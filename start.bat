if [ ! -d "./venv"]; then
    echo "No virtual environment detected, creating one."
    py -m venv ./venv
    echo "Installing requirements."
    .\venv\Scripts\python.exe -m pip install -r requirements.txt

echo "Starting XLTickers"
.\venv\Scripts\python.exe main.py
pause