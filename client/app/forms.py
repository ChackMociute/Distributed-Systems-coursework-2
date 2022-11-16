from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Length

class StockForm(FlaskForm):
    name = StringField('name', validators=[Length(max=100)])
    tickers = TextAreaField('tickers', validators=[DataRequired()])
    number = IntegerField('number', validators=[DataRequired(), NumberRange(min=0)])
    
class OldStockForm(FlaskForm):
    name = StringField('name', validators=[DataRequired(), Length(max=100)])