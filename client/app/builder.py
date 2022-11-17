from app import db
from .models import Portfolio
from datetime import datetime, timedelta
from tqdm import tqdm
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
    SUMMARY_COLUMNS = ['ticker', 'price', 'eps', 'bvps', 'size', 'current_ratio']
    
    def __init__(self, name):
        # Method to use for communicating with APIs
        self.method = req.put if name is not None else req.post
        self.name = name if name is not None else 'default'
        self.pf = Portfolio.query.get(self.name)
        if self.pf is None:
            self.pf = Portfolio(name=self.name, tickers='', n=0)
            db.session.add(self.pf)
            db.session.commit()
    
    # Method for retrieving an already existing portfolio
    def get_portfolio(self):
        try: stocks = pd.read_json(req.get(f"{self.API_ADDRESS}:{self.QUALITY_PORT}",
                                           data={'name': self.name}).json())
        except ValueError: stocks = self.pf.stocks
        try: portfolio = pd.read_json(req.get(f"{self.API_ADDRESS}:{self.PORTFOLIO_PORT}",
                                              data={'name': self.name}).json(), typ='series')
        except ValueError: portfolio = self.pf.portfolio
        # If requested portfolio doesn't exist in neither API nor local storage, return empty
        if stocks is None or portfolio is None: return pd.Series(), pd.DataFrame()
        return portfolio.sort_values(ascending=False), stocks.sort_values('score', ascending=False)

    # Method for creating a new portfolio
    def create_portfolio(self):
        self.process_financial_data(*self.get_financial_data())
        # Save the financial data under the current portfolio name
        self.pf.portfolio = self.portfolio.to_json()
        self.pf.stocks = self.stocks.to_json()
        db.session.commit()
        return self.portfolio, self.stocks

    def process_financial_data(self, summary, historic):
        print("\n\nPROCESSING DATA: Step 1/2")
        # Evaluate the stocks
        stocks = pd.read_json(self.method(f"{self.API_ADDRESS}:{self.QUALITY_PORT}",
                                          data={'name': self.name, 'data': summary.to_json()}).json())
        # Find the covariance matrix
        cov = pd.read_json(self.method(f"{self.API_ADDRESS}:{self.QUALITY_PORT}/cov",
                                       data={'name': self.name, 'data': historic.to_json()}).json())
        print("\nPROCESSING DATA: Step 2/2")
        # Select stocks and balance the portfolio
        self.portfolio =  pd.read_json(self.method(f"{self.API_ADDRESS}:{self.PORTFOLIO_PORT}",
                                                data={'name': self.name,
                                                      'scores': stocks.score.to_json(),
                                                      'cov': cov.to_json(),
                                                      'n': self.pf.n}).json(),
                                       typ='series').sort_values(ascending=False)
        self.stocks = stocks.sort_values('score', ascending=False)

    def get_financial_data(self):
        tickers = self.pf.tickers.split(',')
        summary = self.create_summary_matrix(tickers)
        historic = self.create_historic_matrix(tickers)
        # Throw out stocks not appearing in either of the matrices
        common = list(set(summary.index).intersection(historic.columns))
        summary = summary.loc[common]
        historic = historic[common]
        return summary, historic

    # Returns matrix of stocks with metrics specified in self.SUMMARY_COLUMNS
    def create_summary_matrix(self, tickers):
        print("RETRIEVING DATA: Step 1/2")
        df = pd.DataFrame([self.current_data for tick in tqdm(tickers)
                           if self.summary_from_ticker(tick) is not None],
                          columns=self.SUMMARY_COLUMNS)
        return df.fillna(0).set_index('ticker')

    def summary_from_ticker(self, tick):
        data = req.get(self.SUMMARY_API.format(tick),
                       headers=self.HEADERS).json()['quoteSummary']['result']
        try:
            data = data[0]
            eps = self.extract_metric(data, 'defaultKeyStatistics', 'trailingEps')
            bvps = self.extract_metric(data, 'defaultKeyStatistics', 'bookValue')
            size = self.extract_metric(data, 'defaultKeyStatistics', 'enterpriseValue')
            price = self.extract_metric(data, 'financialData', 'currentPrice')
            current = self.extract_metric(data, 'financialData', 'currentRatio')
        except (KeyError, ValueError, TypeError, IndexError): return
        self.current_data = pd.Series([tick, price, eps, bvps, size, current],
                                      index=self.SUMMARY_COLUMNS)
        return True
    
    @staticmethod
    def extract_metric(data, key, metric):
        try: return data[key][metric]['raw']
        except KeyError: return 0

    # Returns matrix of historic monthly closing prices for stocks over the last 12 years
    def create_historic_matrix(self, tickers):
        print("\n\nRETRIEVING DATA: Step 2/2")
        # Unix time stamps for querying historic data
        p1 = int(time.mktime((datetime.now() - 12*timedelta(days=365)).timetuple()))
        p2 = int(time.mktime(datetime.now().timetuple()))
        return pd.DataFrame({tick: self.current_data for tick in tqdm(tickers)
                             if self.historic_from_ticker(tick, p1, p2) is not None}
                            ).astype(float).fillna(0)

    # Get the closing prices monthly for specified ticker symbol between p1 and p2
    def historic_from_ticker(self, tick, p1, p2):
        data = req.get(self.HISTORIC_API.format(tick, p1, p2), headers=self.HEADERS).text
        data = [i.split(',') for i in data.split('\n')]
        try: df = pd.DataFrame(data[1:], columns=data[0])[['Date', 'Close']]
        except (KeyError, ValueError, TypeError, IndexError): return
        df.Close = df.Close.str.replace('null', 'nan', regex=False)
        df.Date = pd.to_datetime(df.Date)
        self.current_data = df.set_index('Date').squeeze()
        return True