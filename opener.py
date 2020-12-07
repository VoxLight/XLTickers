from tkinter import filedialog
from common import clear
from menu import menu
import openpyxl
import tkinter



# Get the woorkbook filepath
def _get_wb_fp():
    # Set options for retriving an excel file
    options = {
        "title": "Please select an Excel Workbook...",
        "filetypes": (("Excel Workbook", "*.xlsx"),)
    }
    clear()
    print("Please select the workbook you would like to use.")
    return filedialog.askopenfilename(**options)


# Get the sheet name inside the workbook to act on
def _get_sheet(sheets):
    clear()
    return menu(sheets)


def get_workbook():
    clear()
    print("Getting workbook...")
    
    xlfp = _get_wb_fp()
    
    clear()
    print("Loading the workbook. This might take a while....")
    wb = openpyxl.load_workbook(xlfp)
    
    sheet = _get_sheet(wb.sheetnames)
    clear()
    return wb[sheet]
    
    