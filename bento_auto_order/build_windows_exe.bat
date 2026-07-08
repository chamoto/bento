@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
pip install -r requirements-build.txt

pyinstaller ^
  --name BentoAutoOrder ^
  --windowed ^
  --onedir ^
  --add-data ".env.example;." ^
  --add-data "ajiya_sample_orders.csv;." ^
  --add-data "sample_orders.csv;." ^
  app.py

echo.
echo Build complete.
echo Output: dist\BentoAutoOrder\BentoAutoOrder.exe
pause
