from app import app, db
from .forms import StockForm
from .models import Portfolio
from flask import render_template, redirect, url_for
from datetime import datetime, timedelta
import time
import requests as req
import pandas as pd

SUMMARY_API = "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}?modules=defaultKeyStatistics,financialData"
HISTORIC_API = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1mo"
HEADERS = {'user-agent': 'curl/7.55.1'}
API_ADDRESS = "http://localhost"
QUALITY_PORT = "1111"
PORTFOLIO_PORT = "2222"


@app.route('/', methods=['GET', 'POST'])
def home():
    form = StockForm()
    if form.validate_on_submit():
        update_db(form)
        return redirect(url_for('stocks', name=form.name.data))
    return render_template('home.html', form=form)

@app.route('/stocks/<name>')
def stocks(name):
    portfolio, stocks = create_portfolio(name)
    return render_template('stocks.html', stocks=stocks.iterrows(), portfolio=portfolio)


def update_db(form):
    name = form.name.data
    tickers = ','.join(list({tick.strip() for tick in form.tickers.data.split(',')}))
    portfolio = Portfolio.query.get(name)
    if portfolio is None:
        db.session.add(Portfolio(name=name, tickers=tickers, n=form.number.data))
    else:
        portfolio.tickers = tickers
        portfolio.n = form.number.data
    db.session.commit()

def create_portfolio(name):
    pf = Portfolio.query.get(name)
    tickers = pf.tickers.split(',')
    summary = create_summary_matrix(tickers)
    historic = create_historic_matrix(tickers)
    common = list(set(summary.index).intersection(historic.columns))
    summary = summary.loc[common]
    historic = historic[common]
    stocks = pd.read_json(req.put(f"{API_ADDRESS}:{QUALITY_PORT}", data={'name': name, 'data': summary.to_json()}).json())
    cov = pd.read_json(req.put(f"{API_ADDRESS}:{QUALITY_PORT}/cov", data={'name': name, 'data': historic.to_json()}).json())
    if len(stocks) == 0: return pd.DataFrame(), stocks.sort_values('score', ascending=False)
    portfolio = pd.read_json(req.put(f"{API_ADDRESS}:{PORTFOLIO_PORT}",
                                      data={'name': name,
                                            'scores': stocks.score.to_json(),
                                            'cov': cov.to_json(),
                                            'n': pf.n}).json(), typ='series').sort_values(ascending=False)
    return portfolio, stocks.sort_values('score', ascending=False)

def create_summary_matrix(tickers):
    df = pd.DataFrame([get_summary_from_ticker(tick) for tick in tickers
                       if tick != '' and get_summary_from_ticker(tick) is not None])
    df.fillna(0, inplace=True)
    return df.set_index('ticker')

def get_summary_from_ticker(tick):
    data = req.get(SUMMARY_API.format(tick), headers=HEADERS).json()['quoteSummary']['result']
    if data is None: return
    data = data[0]
    eps = data['defaultKeyStatistics']['trailingEps']['raw']
    bvps = data['defaultKeyStatistics']['bookValue']['raw']
    price = data['financialData']['currentPrice']['raw']
    return pd.Series({'ticker': tick, 'price': price, 'eps': eps, 'bvps': bvps})

def create_historic_matrix(tickers):
    p1, p2 = int(time.mktime((datetime.now() - 12*timedelta(days=365)).timetuple())), int(time.mktime(datetime.now().timetuple()))
    return pd.DataFrame({tick: get_historic_from_ticker(tick, p1, p2) for tick in tickers
                         if tick != '' and get_historic_from_ticker(tick, p1, p2) is not None}).astype(float).fillna(0)

def get_historic_from_ticker(tick, p1, p2):
    data = req.get(HISTORIC_API.format(tick, p1, p2), headers=HEADERS).text
    data = [i.split(',') for i in data.split('\n')]
    try: df = pd.DataFrame(data[1:], columns=data[0])[['Date', 'Close']]
    except (KeyError, ValueError): return
    df.Close = df.Close.str.replace('null', 'nan', regex=False)
    df.Date = pd.to_datetime(df.Date.squeeze())
    return df.set_index('Date').squeeze()