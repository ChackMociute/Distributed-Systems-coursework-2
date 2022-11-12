from app import app
from flask import render_template
import requests as req
import pandas as pd
    

@app.route('/')
def home():
    s = get_data_from_ticker('MSFT')
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    df = create_dataframe(tickers)
    data = pd.read_json(req.post("http://127.0.0.1:1111", data={'data': df.to_json()}).json())
    return render_template('index.html', columns=data.columns, data=data.iterrows())

def create_dataframe(tickers):
    df = pd.DataFrame([get_data_from_ticker(tick) for tick in tickers])
    return df.set_index('ticker') 

def get_data_from_ticker(tick):
    data = req.get(f"https://query1.finance.yahoo.com/v11/finance/quoteSummary/{tick}?modules=defaultKeyStatistics,financialData",
                   headers={'user-agent': 'curl/7.55.1'}
                  ).json()['quoteSummary']['result'][0]
    eps = data['defaultKeyStatistics']['trailingEps']['raw']
    bvps = data['defaultKeyStatistics']['bookValue']['raw']
    price = data['financialData']['currentPrice']['raw']
    return pd.Series({'ticker': tick, 'price': price, 'eps': eps, 'bvps': bvps})