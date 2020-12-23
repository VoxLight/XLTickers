# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel

# local libs
import datetime as dt

# project libs
from libs.stock_data import get_price, get_date
from libs.toucher import touch_account_rows
from libs.common import globals_, CONFIG
from scripts.common import _cols



NAME = f"Price Updater (cols {_cols(CONFIG['PRICE_UPDATER'])})"

# 1
def _update(ticker, cells):
    price_cell, date_cell = cells
    if _update_price(ticker, price_cell):
        _update_date(date_cell)
    
# 2  
def _update_price(ticker, cell):

    # get the price
    price = get_price(ticker)
        
    if not price:
        globals_.add_error(ticker, cell.coordinate)
        return False
    
    print(f"Setting {cell.coordinate}:{ticker} close={price}")
    cell.value = price
    return True
    
# 3
def _update_date(cell):
    cell.value = date_to_excel(dt.datetime.today())


def run(ws):
    price_column = CONFIG["PRICE_UPDATER"]["price_column"]
    date_column = CONFIG["PRICE_UPDATER"]["date_column"]
    
    
    print(f"Updating the prices of {ws}.")
    touch_account_rows(ws, _update, [price_column, date_column])