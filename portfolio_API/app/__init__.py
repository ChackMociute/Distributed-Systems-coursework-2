from flask import Flask, request
from flask_restful import Resource, Api
import pandas as pd
import numpy as np
from scipy.optimize import minimize

app = Flask(__name__)
api = Api(app)

class PortfolioBuilder(Resource):
    def post(self):
        scores = pd.read_json(request.form['scores'])
        cov = pd.read_json(request.form['cov'])
        w, scores = self.balance(scores, cov, n=3)
        return {'w': list(w), 'scores': scores.to_json()}
    
    def balance(self, scores, cov, n=None):
        if n is None: n = len(scores)
        x = self.minimize(cov, scores)
        
        while(len(scores) > n):
            i = np.argmin(x)
            cov = cov.drop(i)
            cov = cov.drop(columns=i)
            scores = scores.drop(i)
            x = self.minimize(cov, scores)
        
        return x, scores
            
    def minimize(self, cov, scores):
        constraints = ({'type': 'eq', 'fun': lambda x: 1 - sum(x)})
        bounds = tuple((0, 1) for _ in scores)
        
        return minimize(self.weights, np.ones(len(scores))/len(scores),
                        args=(cov, scores),
                        bounds=bounds,
                        constraints=constraints).x
    
    @staticmethod
    def weights(x, cov, scores):
        return x.T.dot(cov).dot(x)/x.T.dot(scores)

api.add_resource(PortfolioBuilder, '/')