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
        self._days_ago = 0
    
    @property
    def days_ago(self):
        return self._days_ago
    
    @days_ago.setter
    def days_ago(self, days):
        self._days_ago = days
        
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

def clear():
    os.system('cls')
    
def print_errors():
    for k, v in globals_.errors.items():
        print(f"Ticker {k} errored on row(s): {str(v)}")
        
def trunc(num):
    return round(num, int(CONFIG["DATA"]["rounding"]))
 

def _get_valid_input(err_msg, is_valid_condition, ask_txt, return_type=None):
    while not is_valid_condition(txt := input(ask_txt)):
        print(err_msg)
        
    if return_type:
        return return_type(txt)
    
    return txt
