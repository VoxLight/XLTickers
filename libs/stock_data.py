import datetime as dt
import pandas_datareader as web
from pandas import to_datetime


storage = {}


def __add_to_storage(ticker, data):
    storage[ticker] = data
    
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

def _get_ticker_data(ticker, days_ago=None):
    data = __get_from_storage(ticker)
    if data:
        return data
    
    if not days_ago:
        start = dt.datetime.today() - dt.timedelta(days=5)
        data = web.DataReader(ticker, data_source='yahoo', start=start).head(1)
    else:
        start = dt.datetime.today() - dt.timedelta(days=5)
        end = start + dt.timedelta(days=5)
        data = web.DataReader(ticker, data_source='yahoo', start=start).tail(1)

    
    to_store = (
        __get_df_close(data), # get the closing price
        __get_df_date(data) # get the date
    )
    __add_to_storage(ticker, to_store)
    return __get_from_storage(ticker)


def get_price(ticker, **options):
    return _get_ticker_data(ticker, **options)[0]

def get_date(ticker, **options):
    return _get_ticker_data(ticker, **options)[1]




if __name__ == "__main__":
    print(get_date("AMD", days_ago=333))