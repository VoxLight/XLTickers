# pypi libs
import pandas_datareader as web

# local libs
from collections import defaultdict as DD
import datetime as dt
import configparser
import os

# project libs


class Globals:
    def __init__(self):
        self._errors = DD(list)
        self._workbook_fp = None
        
    @property
    def workbook_fp(self):
        return self._workbook_fp
    
    @workbook_fp.setter
    def workbook_fp(self, val):
        self._workbook_fp = val
        
    @property
    def errors(self):
        return self._errors
    
    def add_error(self, ticker, loc):
        self._errors[ticker].append(loc)
        
globals_ = Globals()
        

CONFIG_PATH = "./config.ini"
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)


def trunc(num):
    return round(num, 2)


def clear():
    os.system('cls')
    
def print_errors():
    for k, v in globals_.errors.items():
        print(f"Ticker {k} errored at: {', '.join(v)}")
 
    
def get_ticker_price(ticker, days_prior=5, head=True):
    position = -1 if head else 0
    now = dt.datetime.today()
    past_point = now - dt.timedelta(days=days_prior)
    try:
        return trunc(web.DataReader(ticker, data_source='yahoo', start=past_point, end=now)["Close"][position])
    except Exception as e:
        print(f"Attempting to set {ticker} caused an error: ")
        print(str(e))
        return False


def _get_valid_input(err_msg, is_valid_condition, ask_txt, return_type=None):
    while not is_valid_condition(txt := input(ask_txt)):
        print(err_msg)
        
    if return_type:
        return return_type(txt)
    
    return txt
