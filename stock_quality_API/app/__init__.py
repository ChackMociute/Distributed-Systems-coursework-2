from flask import Flask, request
from flask_restful import Resource, Api
import pandas as pd
import numpy as np

app = Flask(__name__)
api = Api(app)

class StockValuator(Resource):
    def post(self):
        df = pd.read_json(request.form['data'])
        eps, bvps, price = df['eps'], df['bvps'], df['price']
        # Adding a score column using the Graham number
        df['score'] = np.sqrt(22.5 * eps * bvps) - price
        return df.to_json()

api.add_resource(StockValuator, '/')