#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
  echo "Create .venv first."
  echo "python3 -m venv .venv"
  exit 1
fi

source ".venv/bin/activate"
pip install -r requirements-build.txt

pyinstaller \
  --name BentoAutoOrder \
  --windowed \
  --onedir \
  --add-data ".env.example:." \
  --add-data "ajiya_sample_orders.csv:." \
  --add-data "sample_orders.csv:." \
  app.py

echo "Build complete."
echo "Output: dist/BentoAutoOrder.app"
