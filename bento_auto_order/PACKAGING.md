# Packaging

Windows and Mac need separate builds.

- Windows: `BentoAutoOrder.exe`
- Mac: `BentoAutoOrder.app`

There is no reliable single executable that runs on both Windows and Mac.

## Browser policy

This app uses Playwright, but the packaged app defaults to installed Google Chrome:

```env
ORDER_BROWSER_CHANNEL=chrome
```

This avoids bundling Chromium into the app and keeps the package smaller.

If Chrome is not installed, install Chrome or remove `ORDER_BROWSER_CHANNEL=chrome` and install Playwright Chromium separately.

## Build on Windows

Run:

```bat
setup_windows.bat
build_windows_exe.bat
```

Output:

```text
dist\BentoAutoOrder.exe
```

This is a one-file build. PyInstaller bundles Python and DLLs into `BentoAutoOrder.exe`.
Chrome itself is not bundled; the user's Windows PC should have Google Chrome installed.

## Build Windows App on GitHub

This repo includes a GitHub Actions workflow:

```text
.github/workflows/build-windows.yml
```

After pushing to `main`, open GitHub Actions and download the artifact:

```text
BentoAutoOrder-windows
```

Unzip the downloaded artifact and run:

```text
BentoAutoOrder.exe
```

## Build on Mac

Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./build_mac_app.command
```

Output:

```text
dist/BentoAutoOrder.app
```

Mac apps may need Gatekeeper approval if distributed outside the App Store.
