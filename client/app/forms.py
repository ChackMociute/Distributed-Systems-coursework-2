from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class StockForm(FlaskForm):
    name = StringField('name', validators=[Length(max=100)])
    tickers = TextAreaField('tickers', validators=[DataRequired()])
    number = IntegerField('number', validators=[DataRequired(), NumberRange(min=0)])
    submit1 = SubmitField('submit')

# Form for retrieving saved data by name
class OldStockForm(FlaskForm):
    name2 = StringField('name', validators=[DataRequired(), Length(max=100)])
    submit2 = SubmitField('submit')