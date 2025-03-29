import datetime as dt
import yfinance as yf
import logging
import traceback
from libs.common import trunc


storage = {}

# everything helper/puts data
def __add_to_storage(ticker, data):
    to_store = {
        "price":__get_df_close(data), # get the closing price
        "date":__get_df_date(data) # get the date
    }
    storage[ticker] = to_store
    
def __no_price_info(ticker):
    storage[ticker] = {"price": None, "date": None}
    
# everything helper/retrieves data
def __get_from_storage(ticker):
    if ticker in storage.keys():
        return storage[ticker]
    return None

# everything helper/parses data
def __get_df_date(data): # Return the DateTime of the DatetimeIndex of a Df
    # RESOURCE: https://pandas.pydata.org/pandas-docs/version/0.18.1/generated/pandas.DatetimeIndex.html
    return data.index.date[0]

# everything helper/parses data
def __get_df_close(data): # Return the closing price of a DF in a truncated format
    return trunc(data["Close"].iloc[0])  # Use .iloc[0] to avoid FutureWarning


# everything helper   
def __get_data(ticker, days_ago=7):
    start = dt.datetime.today() - dt.timedelta(days=days_ago)
    ticker_data = yf.Ticker(ticker)
    data = ticker_data.history(start=start, end=dt.datetime.today())
    
    # Add logging to see the fetched data
    if data.empty:
        logging.warning(f"No data fetched for ticker: {ticker}")
    else:
        logging.info(f"Fetched data for ticker: {ticker}\n{data}")
    
    return data

# _get_ticker_data helper
def __get_price_ago(ticker, days_ago):
    data = __get_data(ticker, days_ago).head(1)
    __add_to_storage(ticker, data)

# _get_ticker_data helper   
def __get_recent_price(ticker):
    data = __get_data(ticker).tail(1)
    __add_to_storage(ticker, data)  

def _get_ticker_data(ticker, days_ago=None):
    # See if we already have stock info on this ticker
    data = __get_from_storage(ticker) 
    if data:
        # If we do, return it
        return data
    
    
    try:
        if days_ago:
            __get_price_ago(ticker, days_ago)
        else:
            __get_recent_price(ticker)
            
    except Exception as e:
        print("No price information found for:", ticker)
        __no_price_info(ticker)
        logging.getLogger(__name__)
        logging.debug("################################################################")
        logging.exception(e)
        

    return __get_from_storage(ticker)


def get_price(ticker, **options):
    return _get_ticker_data(ticker, **options)["price"]

def get_date(ticker, **options):
    return _get_ticker_data(ticker, **options)["date"]


### Calculations

def get_x_week(ticker, days):
    data = __get_data(ticker, days)
    print(data)
    
    print(data["High"])




if __name__ == "__main__":
    print( get_x_week("TSLA", 52*7) )

