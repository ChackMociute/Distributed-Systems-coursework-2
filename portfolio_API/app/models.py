from app import db

class Portfolio(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    portfolio = db.Column(db.JSON)