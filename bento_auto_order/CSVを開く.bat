@echo off
setlocal
cd /d "%~dp0"

set CSV_FILE=ajiya_sample_orders.csv

if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="CSV_PATH" (
      if not "%%B"=="" set CSV_FILE=%%B
    )
  )
)

if not exist "%CSV_FILE%" (
  echo CSV file was not found: %CSV_FILE%
  echo Check CSV_PATH in .env.
  pause
  exit /b 1
)

start "" "%CSV_FILE%"
