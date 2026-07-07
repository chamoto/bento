@echo off
setlocal
cd /d "%~dp0"

echo === Bento Auto Order Windows setup ===

where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON_CMD=py -3
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set PYTHON_CMD=python
  ) else (
    echo Python 3 is not installed.
    echo Install Python 3 from https://www.python.org/downloads/windows/
    echo Make sure to check "Add python.exe to PATH".
    pause
    exit /b 1
  )
)

if not exist ".venv" (
  echo Creating virtual environment...
  %PYTHON_CMD% -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo Installing Python packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Installing Playwright browser...
playwright install chromium

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created .env from .env.example
)

echo.
echo Setup complete.
echo Edit .env, then run run_windows.bat.
pause
