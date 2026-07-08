from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path.home() / "Documents" / "BentoAutoOrder"
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


BASE_DIR = app_base_dir()
RESOURCE_DIR = resource_dir()
BASE_DIR.mkdir(parents=True, exist_ok=True)

def env_value(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value if value else default


CSV_PATH = ""
LOGIN_URL = ""
ORDER_URL = ""
ORDER_SITE_USERNAME = ""
ORDER_SITE_PASSWORD = ""
DAY_URLS: dict[str, str] = {}
DAILY_URL_TEMPLATE = ""
BROWSER_CHANNEL = "chrome"


def load_settings() -> None:
    global CSV_PATH
    global LOGIN_URL
    global ORDER_URL
    global ORDER_SITE_USERNAME
    global ORDER_SITE_PASSWORD
    global DAY_URLS
    global DAILY_URL_TEMPLATE
    global BROWSER_CHANNEL

    load_dotenv(BASE_DIR / ".env", override=True)

    CSV_PATH = env_value("CSV_PATH", str(BASE_DIR / "ajiya_sample_orders.csv"))
    if not Path(CSV_PATH).is_absolute():
        CSV_PATH = str(BASE_DIR / CSV_PATH)

    LOGIN_URL = env_value("ORDER_SITE_LOGIN_URL")
    ORDER_SITE_USERNAME = env_value("ORDER_SITE_USERNAME")
    ORDER_SITE_PASSWORD = env_value("ORDER_SITE_PASSWORD")

    DAY_URLS = {
        "day1": env_value("ORDER_SITE_DAY1_URL"),
        "day2": env_value("ORDER_SITE_DAY2_URL"),
        "day3": env_value("ORDER_SITE_DAY3_URL"),
        "day4": env_value("ORDER_SITE_DAY4_URL"),
    }
    DAILY_URL_TEMPLATE = env_value("ORDER_SITE_DAILY_URL_TEMPLATE")
    ORDER_URL = env_value("ORDER_SITE_ORDER_URL", DAY_URLS.get("day1") or LOGIN_URL)
    BROWSER_CHANNEL = env_value("ORDER_BROWSER_CHANNEL", "chrome")


load_settings()

LOGIN_TIMEOUT_MS = 10_000
SELECTOR_TIMEOUT_MS = 5_000
