#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
  echo "First setup is required."
  echo "Run these commands:"
  echo "python3 -m venv .venv"
  echo "source .venv/bin/activate"
  echo "pip install -r requirements.txt"
  echo "playwright install chromium"
  read -r -p "Press Enter to close..."
  exit 1
fi

source ".venv/bin/activate"
python app.py
