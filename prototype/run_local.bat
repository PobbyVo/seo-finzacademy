@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Could not install Python requirements. Check Python and pip.
  pause
  exit /b 1
)
py server.py 5173
pause
