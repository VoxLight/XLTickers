# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel

# local libs
import datetime as dt

# project libs
from libs.toucher import touch_account_rows
from libs.common import globals_, CONFIG, _get_valid_input
from scripts.common import _get_price, _cols, _get_date


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
    
days_ago = 0

# 1
def _update(ticker, cells):
    alert_price_cell, alert_date_cell = cells
    if _update_alert_price(ticker, alert_price_cell):
        _update_alert_date(ticker, alert_date_cell)
    
# 2  
def _update_alert_price(ticker, cell):
    # get the price
    price = _get_price(ticker, days_ago, False)
        
    if not price:
        globals_.add_error(ticker, cell.coordinate)
        return False
    
    print(f"Setting Alert {cell.coordinate}:{ticker} close={price}")
    cell.value = price
    return True
    
# 3
def _update_alert_date(ticker, cell):
    cell.value = date_to_excel(_get_date(ticker, days_ago))

def run(ws):
    alert_price_column = CONFIG["ALERT_UPDATER"]["alert_price_column"]
    alert_date_column = CONFIG["ALERT_UPDATER"]["alert_date_column"]
    
    days_ago = _get_number_of_days()
    
    print(days_ago)
    print(type(days_ago))
    
    
    print(f"Updating the Alerts of {ws}.")
    # Touch all account rows in ws
    # each row has _update applied to every cell in columns
    touch_account_rows(ws, _update, [
        alert_price_column, 
        alert_date_column
    ])