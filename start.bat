REM Description: This batch file is used to set up and run the XLTickers application.
@echo off
if not exist "venv" (
    echo No virtual environment detected. Creating one now.
    py -m venv venv
)

echo Checking dependencies
call .\venv\Scripts\activate.bat && python -m pip install -r requirements.txt

echo Starting XLTickers
call .\venv\Scripts\activate.bat && python main.py
