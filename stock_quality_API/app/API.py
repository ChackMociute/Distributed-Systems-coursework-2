from app import api, db
from flask import request
from flask_restful import Resource
from .models import Stocks
import pandas as pd
import numpy as np


class StockValuator(Resource):
    # ---------------------RESTFUL METHODS---------------------
    def get(self):
        stocks = Stocks.query.get(request.form['name'])
        if stocks is None: return
        return stocks.stocks
    
    def post(self):
        self.update_db('default', self.evaluate().to_json())
        return Stocks.query.get('default').stocks
    
    def put(self):
        self.update_db(request.form['name'], self.evaluate().to_json())
        return Stocks.query.get(request.form['name']).stocks
    
    def delete(self):
        if Stocks.query.get(request.form['name']) is None: return
        Stocks.query.filter(Stocks.name == request.form['name']).delete()
        db.session.commit()
    
    # ---------------------UTILITY METHODS---------------------
    @staticmethod
    def update_db(name, data):
        stocks = Stocks.query.get(name)
        if stocks is None:
            db.session.add(Stocks(name=name, stocks=data))
        else:
            stocks.stocks = data
        db.session.commit()
    
    @staticmethod
    def evaluate():
        df = pd.read_json(request.form['data'])
        eps, bvps = np.clip(df['eps'], 0, None), np.clip(df['bvps'], 0, None)
        
        size_score = 100/(1 + np.power(0.98, (df['size']/1e9)-200))
        cr_score = 100*np.power(4, -1*np.power(df['current_ratio']-2.25, 2))
        graham_score = 100/(1 + np.power(0.99, np.sqrt(22.5 * eps * bvps) - df['price']))
        df['score'] = (size_score + cr_score + 2*graham_score)/4
        return df


class CovarianceCalculator(Resource):
    # ---------------------RESTFUL METHODS---------------------
    def get(self):
        stocks = Stocks.query.get(request.form['name'])
        if stocks is None: return
        return stocks.cov
    
    def post(self):
        self.update_db('default', self.covariance().to_json())
        return Stocks.query.get('default').cov
    
    def put(self):
        self.update_db(request.form['name'], self.covariance().to_json())
        return Stocks.query.get(request.form['name']).cov
    
    def delete(self):
        if Stocks.query.get(request.form['name']) is None: return
        Stocks.query.filter(Stocks.name == request.form['name']).delete()
        db.session.commit()
    
    # ---------------------UTILITY METHODS---------------------
    @staticmethod
    def update_db(name, cov):
        stocks = Stocks.query.get(name)
        if stocks is None:
            db.session.add(Stocks(name=name, cov=cov))
        else:
            stocks.cov = cov
        db.session.commit()
    
    @staticmethod
    def covariance():
        df = pd.read_json(request.form['data'])
        # The following lines create a covariance matrix.
        # df.cov() would be simpler but I pretend it doesn't
        # exist to give the appearance of usefulness to this method.
        df = df.apply(lambda x: x-x.mean())
        if len(df) == 0: return df.T.dot(df)
        return df.T.dot(df)/len(df)
        

api.add_resource(StockValuator, '/')
api.add_resource(CovarianceCalculator, '/cov')