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
  -y \
  --clean \
  --name BentoAutoOrder \
  --windowed \
  --onedir \
  --add-data ".env.example:." \
  --add-data "ajiya_sample_orders.csv:." \
  --add-data "sample_orders.csv:." \
  --add-data "google_form_sample_orders.csv:." \
  qt_app.py

APP_BUNDLE="dist/BentoAutoOrder.app"
TMP_SIGN_DIR="/tmp/bento_auto_order_sign"
TMP_APP="$TMP_SIGN_DIR/BentoAutoOrder.app"

rm -rf "$TMP_SIGN_DIR"
mkdir -p "$TMP_SIGN_DIR"
ditto --norsrc "$APP_BUNDLE" "$TMP_APP"
xattr -cr "$TMP_APP" 2>/dev/null || true
codesign --remove-signature "$TMP_APP" 2>/dev/null || true
codesign --force --deep --sign - "$TMP_APP"
rm -rf "$APP_BUNDLE"
ditto --norsrc "$TMP_APP" "$APP_BUNDLE"
xattr -cr "$APP_BUNDLE" 2>/dev/null || true
codesign --force --deep --sign - "$APP_BUNDLE"

echo "Build complete."
echo "Output: dist/BentoAutoOrder.app"
