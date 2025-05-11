# pypi libs
import openpyxl

# local libs
from tkinter import filedialog

# project libs
from libs.common import clear, globals_
from libs.menu import menu

# Get the woorkbook filepath
def _get_wb_fp():
    print("Getting workbook...")
    
    # Set options for retriving an excel file
    options = {
        "title": "Please select an Excel Workbook...",
        "filetypes": (("Excel Workbook", "*.xlsx"),)
    }
    print("Please select the workbook you would like to use.")
    workbook = filedialog.askopenfilename(**options)
    if not workbook:
        print("No workbook selected.")
        return _get_wb_fp()
    print(f"Workbook selected: {workbook}")
    return workbook

# Get the sheet name inside the workbook to act on
def _get_sheet(sheets):
    print("Please select the sheet name you wish to modify.")
    return menu(sheets)

def get_worksheet():
    clear()
    xlfp = _get_wb_fp()

    print("Loading the workbook. This might take a while....")
    wb = openpyxl.load_workbook(xlfp)  
    clear()  
    sheet = _get_sheet(wb.sheetnames)
    
    clear()
    globals_.workbook_fp = xlfp
    return wb[sheet], wb
    
    