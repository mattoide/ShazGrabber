@echo off
cd /d "%~dp0"
echo Installazione dipendenze...
pip install -r requirements.txt -q
echo.
echo Avvio ShazGrabber...
echo Apri il browser su: http://localhost:5000
echo.
python app.py
pause
