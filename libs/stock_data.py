import datetime as dt
import pandas_datareader as web
from pandas import to_datetime


storage = {}


def __add_to_storage(ticker, data):
    to_store = {
        "price":__get_df_close(data), # get the closing price
        "date":__get_df_date(data) # get the date
    }
    storage[ticker] = to_store
    
def __get_from_storage(ticker):
    if ticker in storage.keys():
        return storage[ticker]
    return None

def __trunc(num): # truncate a fractional share into a USD amount
    return round(num, 2)

def __get_df_date(data): # Return the DateTime of the DatetimeIndex of a Df
    # RESOURCE: https://pandas.pydata.org/pandas-docs/version/0.18.1/generated/pandas.DatetimeIndex.html
    return data.index.date[0]

def __get_df_close(data): # Return the closing price of a DF in a truncated format
    return __trunc(data["Close"][0])

def __get_price_ago(ticker, days_ago):
    start = dt.datetime.today() - dt.timedelta(days=days_ago)
    data = web.DataReader(ticker, data_source='yahoo', start=start, end=dt.datetime.today()).head(1)
    __add_to_storage(ticker, data)
    
def __get_recent_price(ticker):
    start = dt.datetime.today() - dt.timedelta(days=5)
    data = web.DataReader(ticker, data_source='yahoo', start=start, end=dt.datetime.today()).tail(1)
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
            
    except KeyError:
        print("No price information found for:", ticker, "\n    ln 53")
        return None


    return __get_from_storage(ticker)


def get_price(ticker, **options):
    return _get_ticker_data(ticker, **options)["price"]

def get_date(ticker, **options):
    return _get_ticker_data(ticker, **options)["date"]




if __name__ == "__main__":
    print(get_price("QS", days_ago=365))