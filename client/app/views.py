from app import app
from .forms import StockForm
from flask import render_template, redirect, url_for
from datetime import datetime, timedelta
import time
import requests as req
import pandas as pd


@app.route('/', methods=['GET', 'POST'])
def home():
    form = StockForm()
    if form.validate_on_submit():
        return redirect(url_for('stocks', tickers=','.join(list({tick.strip() for tick in form.tickers.data.split(',')}))))
    return render_template('home.html', form=form)


@app.route('/stocks/<tickers>')
def stocks(tickers=[]):
    tickers = tickers.split(',')
    summary = create_summary_matrix(tickers)
    historic = create_historic_matrix(tickers)
    data = pd.read_json(req.post("http://127.0.0.1:1111", data={'data': summary.to_json()}).json())
    cov = pd.read_json(req.post("http://127.0.0.1:1111/cov", data={'data': historic.to_json()}).json())
    print(cov)
    return render_template('stocks.html', columns=data.columns, data=data.iterrows())

def create_summary_matrix(tickers):
    df = pd.DataFrame([get_summary_from_ticker(tick) for tick in tickers])
    df.dropna(axis=0, inplace=True)
    return df.set_index('ticker')

def get_summary_from_ticker(tick):
    data = req.get(f"https://query1.finance.yahoo.com/v11/finance/quoteSummary/{tick}?modules=defaultKeyStatistics,financialData",
                   headers={'user-agent': 'curl/7.55.1'}
                  ).json()['quoteSummary']['result']
    if data is not None:
        data = data[0]
        eps = data['defaultKeyStatistics']['trailingEps']['raw']
        bvps = data['defaultKeyStatistics']['bookValue']['raw']
        price = data['financialData']['currentPrice']['raw']
    else:
        eps, bvps, price = None, None, None
        
    return pd.Series({'ticker': tick, 'price': price, 'eps': eps, 'bvps': bvps})

def create_historic_matrix(tickers):
    p1, p2 = int(time.mktime((datetime.now() - 3*timedelta(days=365)).timetuple())), int(time.mktime(datetime.now().timetuple()))
    return pd.DataFrame({tick: get_historic_from_ticker(tick, p1, p2) for tick in tickers}).astype(float)

def get_historic_from_ticker(tick, p1, p2):
    data = req.get(f"https://query1.finance.yahoo.com/v7/finance/download/{tick}?period1={p1}&period2={p2}&interval=1mo",
                   headers={'user-agent': 'curl/7.55.1'}).text
    data = [i.split(',') for i in data.split('\n')]
    df = pd.DataFrame(data[1:], columns=data[0])[['Date', 'Close']]
    df.Date = pd.to_datetime(df.Date.squeeze())
    return df.set_index('Date').squeeze()