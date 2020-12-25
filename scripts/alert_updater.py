# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel

# local libs
import datetime as dt

# project libs
from libs.common import globals_, CONFIG, _get_valid_input
from libs.toucher import touch_account_rows
from libs.stock_data import get_price, get_date
from scripts.common import _cols, _err


NAME = f"Alert Updater (cols {_cols(CONFIG['ALERT_UPDATER'])})"

def __valid_number_of_days(str_num_of_days):
    if not str_num_of_days.isdigit():
        print("    ERROR: That is not a number, try again.")
        return False
    elif not int(str_num_of_days) > 5:
        print("    ERROR: That is not far enough into the past to get accuarte alert info.")
        return False
    return True

def _get_number_of_days():
    return _get_valid_input(
        "",
        __valid_number_of_days,
        "Please enter the number of days in the past to check: ",
        int
    )

# 1
def _update(ticker, cells):
    alert_price_cell, alert_date_cell = cells
    if _update_alert_price(ticker, alert_price_cell): # pass price cell
        _update_alert_date(ticker, alert_date_cell) # pass date cell
    
# 2  
def _update_alert_price(ticker, cell):
    price = get_price(ticker, days_ago=globals_.days_ago)
    if not price:
        _err(ticker, cell)
        return False
    cell.value = price
    print(f"Setting alert for {cell.coordinate}:{ticker} close={price}")
    return True
    
# 3
def _update_alert_date(ticker, cell):
    cell.value = get_date(ticker)

def run(ws):
    globals_.days_ago = _get_number_of_days()
    
    print("Days ago = ", globals_.days_ago)
    
    price_column = CONFIG["ALERT_UPDATER"]["alert_price_column"]
    date_column = CONFIG["ALERT_UPDATER"]["alert_date_column"]
    
    
    print(f"Updating alert dates of {ws}")
    touch_account_rows(ws, _update, [price_column, date_column])
    
