from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def env_value(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    return value if value else default


CSV_PATH = env_value("CSV_PATH", str(BASE_DIR / "sample_orders.csv"))
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

LOGIN_TIMEOUT_MS = 10_000
SELECTOR_TIMEOUT_MS = 5_000
