@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo Virtual environment is missing.
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env. Please edit it before running again.
  notepad ".env"
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python app.py
pause
