from app import db
from .models import Portfolio
from datetime import datetime, timedelta
import time
import requests as req
import pandas as pd

class PortfolioBuilder():
    SUMMARY_API = "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}?modules=defaultKeyStatistics,financialData"
    HISTORIC_API = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1mo"
    HEADERS = {'user-agent': 'curl/7.55.1'}
    API_ADDRESS = "http://localhost"
    QUALITY_PORT = "1111"
    PORTFOLIO_PORT = "2222"
    
    def __init__(self, name):
        self.method = req.put if name is not None else req.post
        self.name = name if name is not None else 'default'
        self.pf = Portfolio.query.get(self.name)
        if self.pf is None:
            self.pf = Portfolio(name=self.name, tickers='', n=0)
            db.session.add(self.pf)
            db.session.commit()
    
    def get_portfolio(self):
        try: stocks = pd.read_json(req.get(f"{self.API_ADDRESS}:{self.QUALITY_PORT}",
                                           data={'name': self.name}).json())
        except ValueError: stocks = self.pf.stocks
        try: portfolio = pd.read_json(req.get(f"{self.API_ADDRESS}:{self.PORTFOLIO_PORT}",
                                              data={'name': self.name}).json(), typ='series')
        except ValueError: portfolio = self.pf.portfolio
        if stocks is None or portfolio is None: return pd.Series(), pd.DataFrame()
        return portfolio, stocks

    def create_portfolio(self):
        self.process_financial_data(*self.get_financial_data())
        self.pf.portfolio = self.portfolio.to_json()
        self.pf.stocks = self.stocks.to_json()
        db.session.commit()
        return self.portfolio, self.stocks

    def get_financial_data(self):
        tickers = self.pf.tickers.split(',')
        summary = self.create_summary_matrix(tickers)
        historic = self.create_historic_matrix(tickers)
        common = list(set(summary.index).intersection(historic.columns))
        summary = summary.loc[common]
        historic = historic[common]
        return summary, historic

    def create_summary_matrix(self, tickers):
        df = pd.DataFrame([self.get_summary_from_ticker(tick) for tick in tickers
                           if tick != '' and self.get_summary_from_ticker(tick) is not None],
                          columns=['ticker', 'price', 'eps', 'bvps'])
        df.fillna(0, inplace=True)
        return df.set_index('ticker')

    def get_summary_from_ticker(self, tick):
        data = req.get(self.SUMMARY_API.format(tick), headers=self.HEADERS).json()['quoteSummary']['result']
        try:
            data = data[0]
            eps = data['defaultKeyStatistics']['trailingEps']['raw']
            bvps = data['defaultKeyStatistics']['bookValue']['raw']
            price = data['financialData']['currentPrice']['raw']
        except (KeyError, ValueError, TypeError): return
        return pd.Series({'ticker': tick, 'price': price, 'eps': eps, 'bvps': bvps})

    def create_historic_matrix(self, tickers):
        p1, p2 = int(time.mktime((datetime.now() - 12*timedelta(days=365)).timetuple())), int(time.mktime(datetime.now().timetuple()))
        return pd.DataFrame({tick: self.get_historic_from_ticker(tick, p1, p2) for tick in tickers
                             if tick != '' and self.get_historic_from_ticker(tick, p1, p2) is not None}).astype(float).fillna(0)

    def get_historic_from_ticker(self, tick, p1, p2):
        data = req.get(self.HISTORIC_API.format(tick, p1, p2), headers=self.HEADERS).text
        data = [i.split(',') for i in data.split('\n')]
        try: df = pd.DataFrame(data[1:], columns=data[0])[['Date', 'Close']]
        except (KeyError, ValueError): return
        df.Close = df.Close.str.replace('null', 'nan', regex=False)
        df.Date = pd.to_datetime(df.Date.squeeze())
        return df.set_index('Date').squeeze()

    def process_financial_data(self, summary, historic):
        stocks = pd.read_json(self.method(f"{self.API_ADDRESS}:{self.QUALITY_PORT}",
                                          data={'name': self.name, 'data': summary.to_json()}).json())
        cov = pd.read_json(self.method(f"{self.API_ADDRESS}:{self.QUALITY_PORT}/cov",
                                       data={'name': self.name, 'data': historic.to_json()}).json())
        self.portfolio =  pd.read_json(self.method(f"{self.API_ADDRESS}:{self.PORTFOLIO_PORT}",
                                                data={'name': self.name,
                                                      'scores': stocks.score.to_json(),
                                                      'cov': cov.to_json(),
                                                      'n': self.pf.n}).json(),
                                       typ='series').sort_values(ascending=False)
        self.stocks = stocks.sort_values('score', ascending=False)