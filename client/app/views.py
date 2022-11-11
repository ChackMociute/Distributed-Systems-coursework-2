from app import app
import requests as req
import json

def get_data_from_ticker(tick):
    data = json.loads(req.get(
        f"https://query1.finance.yahoo.com/v11/finance/quoteSummary/{tick}?modules=defaultKeyStatistics,financialData",
        headers={'user-agent': 'curl/7.55.1'}
        ).text)['quoteSummary']['result'][0]
    book = data['defaultKeyStatistics']['bookValue']['raw']
    eps = data['defaultKeyStatistics']['trailingEps']['raw']
    price = data['financialData']['currentPrice']['raw']
    pe = price/eps
    return pe, book
    

@app.route('/')
def hello():
    pe, book = get_data_from_ticker('MSFT')
    return f"Book: {book}, PE ratio: {pe}"