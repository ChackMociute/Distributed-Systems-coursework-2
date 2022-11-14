from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class StockForm(FlaskForm):
    tickers = TextAreaField('tickers', validators=[DataRequired()])
    number = IntegerField('number', validators=[DataRequired(), NumberRange(min=0)])