# pypi libs
from openpyxl.cell.cell import MergedCell
import pandas_datareader as web

# local libs
import datetime as dt

# project libs
from libs.common import trunc, CONFIG



def _valid_row(cell):
    if type(cell) == MergedCell:
        return False
    
    val = cell.value
    if type(val) != str:
        return False
    
    if len(val) == 0:
        return False
    
    if val == " ":
        return False
    
    return True


def _format_col_row_2_cell(column_let, row_num):
    return column_let + str(row_num)

def touch_account_rows(ws, action, cols):
    start, stop = CONFIG["XL"]["start_word"], CONFIG["XL"]["stop_word"]
    
    account_num = 0
    
    ticker_column = CONFIG["XL"]["ticker_column"]
    touch = False
    for cell in ws[ticker_column]:
        if cell.value == start:
            account_num += 1
            print(f"Account {account_num}:\n")
            touch = True
            continue
        elif cell.value == stop:
            touch = False
            continue
            
        if touch and _valid_row(cell):
            
            ticker = cell.value
            cells = [
                ws[_format_col_row_2_cell(col, cell.row)] for col in cols
            ]
            action(ticker, cells)
        

