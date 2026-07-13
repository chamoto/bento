@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo Virtual environment is missing.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python qt_app.py
pause
