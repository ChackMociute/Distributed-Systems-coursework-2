# Stock portfolio builder
## Coursework 2 for course Distributed Systems

### Description
The client provides an interface to interact with the two APIs. The stock quality API, used to evaluate stocks, and the portfolio API, used to create and balance a diversified portfolio. The user enters the ticker symbols of his chosen stocks, how many stocks they wish to have in the portfolio, and optionally the name of the portfolio. Yahoo! Finance is then queried for the selected stocks and the needed data is extracted. Next, the stock data is sent to the first API to be evaluated and for a covariance matrix to be created. Following that, the evaluated stocks and the covarianve matrix is sent to the second API which finds the best weights taking into account portfolio variance, stock quality, and heterogeneity of the weights. Finally, the client shows the stock information as well as the recommended portfolio.

### Set up
1. Create a virtual environment by typing `python -m venv venv`
2. Activate the virtual environment
    1. On Windows type `venv\Source\activate`
    2. On Linux type `source venv/bin/activate`
3. Install the needed packages by typing `pip install -r requirements.txt`
4. Start the program
    1. On Windows by running `run.bat`
    2. On Linux:
        1. Run the client by typing `flask --app client/app --debug run`
        2. Open a new terminal and run the first API by typing `flask --app stock_quality_API/app --debug run -p 1111`
        3. Open a new terminal and run the second API by typing `flask --app portfolio/app --debug run -p 2222`
5. Open the client terminal and copy the link into your internet browser

You may choose other ports but then make sure to update `client/app/builder.py` appropriately.

### Disclaimer
This web application should not be used for actual investing because I am not a financial analyst and both the evaluation of stocks and the creation of a portfolio are likely to be suboptimal. While I did employ some ideas from Benjamin Graham's "The Intelligent Investor", they are by no means extensive and they are mixed with my own ideas which are neither backed up by theory nor by historic success. Ultimately, you should not be building your own portfolios in any case. Just invest in a global index fund. 
