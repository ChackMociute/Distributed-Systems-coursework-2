from app import db

class Portfolio(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    tickers = db.Column(db.String())
    n = db.Column(db.Integer())
    stocks = db.Column(db.JSON)
    portfolio = db.Column(db.JSON)