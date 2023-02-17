@echo off
if not exist "venv" (
    echo No virtual environment detected, creating one.
    py -m venv venv
    echo Installing requirements.
    call .\venv\Scripts\activate.bat && python -m pip install -r requirements.txt
)

echo Starting XLTickers
call .\venv\Scripts\activate.bat && python main.py
pause
