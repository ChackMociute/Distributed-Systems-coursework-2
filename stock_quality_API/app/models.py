from app import db

class Stocks(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    stocks = db.Column(db.JSON)
    cov = db.Column(db.JSON)