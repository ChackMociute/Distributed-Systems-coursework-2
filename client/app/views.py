from app import app, db
from .forms import StockForm, OldStockForm
from .models import Portfolio
from .builder import PortfolioBuilder
from flask import render_template, redirect, url_for, request


@app.route('/', methods=['GET', 'POST'])
def home():
    form = StockForm()
    form2 = OldStockForm()
    # If form one is submitted, create or update a stock portfolio
    if form.submit1.data and form.validate_on_submit():
        name_provided = form.name.data != ''
        update_db(form, name_provided=name_provided)
        return redirect(url_for('stocks', name=form.name.data))
    # If form two is submitted, merely retrieve the data (if available)
    if form2.submit2.data and form2.validate_on_submit():
        return redirect(url_for('stocks', name=form2.name2.data, get=True))
        
    return render_template('home.html', form=form, form2=form2)

@app.route('/stocks/')
@app.route('/stocks/<name>')
def stocks(name=None):
    get = request.args.get('get')
    if bool(get): portfolio, stocks = PortfolioBuilder(name).get_portfolio()
    else: portfolio, stocks = PortfolioBuilder(name).create_portfolio()
    return render_template('stocks.html', stocks=stocks.iterrows(), portfolio=portfolio)

def update_db(form, name_provided=False):
    if name_provided: name = form.name.data
    else: name = 'default'
    # Reformat the tickers to remove duplicates and get rid of whitespaces
    tickers = ','.join(list({tick.strip() for tick in form.tickers.data.split(',')}))
    portfolio = Portfolio.query.get(name)
    if portfolio is None:
        db.session.add(Portfolio(name=name, tickers=tickers, n=form.number.data))
    else:
        portfolio.tickers = tickers
        portfolio.n = form.number.data
    db.session.commit()