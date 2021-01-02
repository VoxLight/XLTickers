# pypi libs
from openpyxl.utils.datetime import to_excel as date_to_excel
from pandas import rolling

# local libs
import datetime as dt

# project libs
from libs.common import globals_, CONFIG, _get_valid_input
from libs.toucher import touch_account_rows
from libs.stock_data import get_price, get_date
from scripts.common import _cols, _err


NAME = f"52 Week High"

# 1
def _update(ticker, cells):
    pass
    
# 2  
def _get_high(ticker, cell):
    pass


def run(ws):
    print("Getting 52 week highs")
    touch_account_rows(ws, _update, [price_column, date_column])
    
