from openpyxl.cell.cell import MergedCell
import pandas_datareader as web
from common import trunc, CONFIG, get_ticker_price
import datetime as dt

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

def touch_account_rows(ws, action):
    start, stop = CONFIG["GENERAL"]["start_word"], CONFIG["GENERAL"]["stop_word"]
    
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
            price_column = CONFIG["XL"]["price_column"]
            date_column = CONFIG["XL"]["date_column"]
            
            ticker = cell.value
            price_cell = ws[_format_col_row_2_cell(price_column, cell.row)]
            date_cell = ws[_format_col_row_2_cell(date_column, cell.row)]
            action(ticker, price_cell, date_cell)
        

