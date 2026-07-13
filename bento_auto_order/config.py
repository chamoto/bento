from __future__ import annotations

import os
import sys
from pathlib import Path


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "BentoAutoOrder"
        if sys.platform == "win32":
            return Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "BentoAutoOrder"
        return Path.home() / "Documents" / "BentoAutoOrder"
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


BASE_DIR = app_base_dir()
RESOURCE_DIR = resource_dir()
BASE_DIR.mkdir(parents=True, exist_ok=True)


CSV_PATH = ""
LOGIN_URL = "https://reitou.ajiya-lunch.net/login"
ORDER_URL = "https://reitou.ajiya-lunch.net/daily/"
ORDER_DATE = ""
ORDER_SITE_USERNAME = ""
ORDER_SITE_PASSWORD = ""
DAY_URLS: dict[str, str] = {}
DAILY_URL_TEMPLATE = ""
BROWSER_CHANNEL = "chrome"
MANUAL_LOGIN_WAIT_MS = 60_000


def load_settings() -> None:
    global CSV_PATH
    global LOGIN_URL
    global ORDER_URL
    global ORDER_DATE
    global ORDER_SITE_USERNAME
    global ORDER_SITE_PASSWORD
    global DAY_URLS
    global DAILY_URL_TEMPLATE
    global BROWSER_CHANNEL
    global MANUAL_LOGIN_WAIT_MS

    CSV_PATH = str(BASE_DIR / "google_form_sample_orders.csv")
    LOGIN_URL = "https://reitou.ajiya-lunch.net/login"
    ORDER_URL = "https://reitou.ajiya-lunch.net/daily/"
    ORDER_DATE = ""
    ORDER_SITE_USERNAME = ""
    ORDER_SITE_PASSWORD = ""
    DAY_URLS = {}
    DAILY_URL_TEMPLATE = ""
    BROWSER_CHANNEL = "chrome"
    MANUAL_LOGIN_WAIT_MS = 60_000


load_settings()

LOGIN_TIMEOUT_MS = 10_000
SELECTOR_TIMEOUT_MS = 5_000
