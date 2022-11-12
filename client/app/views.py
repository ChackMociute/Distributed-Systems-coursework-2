from app import app
from .forms import StockForm
from flask import render_template, redirect, url_for
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
    df = create_dataframe(tickers)
    data = pd.read_json(req.post("http://127.0.0.1:1111", data={'data': df.to_json()}).json())
    return render_template('stocks.html', columns=data.columns, data=data.iterrows())

def create_dataframe(tickers):
    df = pd.DataFrame([get_data_from_ticker(tick) for tick in tickers])
    df.dropna(axis=0, inplace=True)
    return df.set_index('ticker') 

def get_data_from_ticker(tick):
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