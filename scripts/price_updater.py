# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel

# local libs
import datetime as dt

# project libs
from libs.common import globals_, get_ticker_price
from libs.toucher import touch_account_rows



price_storage = {}

# 1
def _update(ticker, price_cell, date_cell):
    if _update_price(ticker, price_cell):
        _update_date(date_cell)
    
# 2  
def _update_price(ticker, cell):
    # Update the price
    
    # Check if we have gotten the price before
    if ticker in price_storage.keys():
        # If we have, retrieve it from storage.
        price = price_storage[ticker]
    else:
        # If we have not, then find the price and store it
        price = get_ticker_price(ticker)
        price_storage[ticker] = price
        
    if not price:
        globals_.add_error(ticker, cell.coordinate)
        return False
    print(f"Setting {cell.coordinate}:{ticker} close={price}")
    cell.value = price
    return True
    
# 3
def _update_date(cell):
    cell.value = date_to_excel(dt.datetime.today())


def update_prices(ws):
    print(f"Updating the prices of {ws}.")
    touch_account_rows(ws, _update)