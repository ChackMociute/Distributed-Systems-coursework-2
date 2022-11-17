from app import api, db
from .models import Portfolio
from flask import request
from flask_restful import Resource
import pandas as pd
import numpy as np
from scipy.optimize import minimize


class PortfolioBuilder(Resource):
    # ---------------------RESTFUL METHODS---------------------
    def get(self):
        pf = Portfolio.query.get(request.form['name'])
        if pf is None: return
        return pf.portfolio
    
    def post(self):
        self.update_db('default', self.build().to_json())
        return Portfolio.query.get('default').portfolio
    
    def put(self):
        self.update_db(request.form['name'], self.build().to_json())
        return Portfolio.query.get(request.form['name']).portfolio
    
    def delete(self):
        if Portfolio.query.get(request.form['name']) is None: return
        Portfolio.query.filter(Portfolio.name == request.form['name']).delete()
        db.session.commit()
    
    # ---------------------UTILITY METHODS---------------------
    @staticmethod
    def update_db(name, data):
        pf = Portfolio.query.get(name)
        if pf is None:
            db.session.add(Portfolio(name=name, portfolio=data))
        else:
            pf.portfolio = data
        db.session.commit()
    
    def build(self):
        scores = pd.read_json(request.form['scores'], typ='series')
        cov = pd.read_json(request.form['cov'])
        n = int(request.form['n'])
        weights, scores = self.balance(scores, cov, n)
        return pd.Series(weights, index=scores.index)
    
    def balance(self, scores, cov, n):
        if len(scores) == 0: return [], scores
        if n is None: n = len(scores)
        x = self.minimize(cov, scores)
        
        # Drop stocks and recalculate weights until number of stocks equals n
        while(len(scores) > n):
            # Drop 20% of remaining unwanted stocks rounded up at a time
            for _ in range(int(np.ceil((len(scores)-n)/5))):
                i = scores.index[np.argmin(x)]
                x = np.delete(x, np.argmin(x))
                cov = cov.drop(i)
                cov = cov.drop(columns=i)
                scores = scores.drop(i)
            x = self.minimize(cov, scores)
        return x, scores
            
    def minimize(self, cov, scores):
        # Insure weights add up to 1
        constraints = ({'type': 'eq', 'fun': lambda x: 1 - sum(x)})
        # Set boundaries for weights in [x; 1] where x is 20% of an equal share
        bounds = tuple((0.2/len(scores), 1) for _ in scores)
        
        return minimize(self.weights, np.ones(len(scores))/len(scores),
                        args=(cov, scores),
                        bounds=bounds,
                        constraints=constraints).x
    
    @staticmethod
    def weights(x, cov, scores):
        # Function to minimize takes into account variance, quality, and weight heterogeneity
        return np.sqrt(x.dot(cov).dot(x)) - x.dot(scores) + x.dot(x) * 5 * len(x)

api.add_resource(PortfolioBuilder, '/')