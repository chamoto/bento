from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode

BASE_DIR = Path(__file__).resolve().parent

import pandas as pd

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    PlaywrightError = Exception
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None

import config
import site_selectors


BASE_COLUMNS = {
    "timestamp",
    "name",
    "note",
    "email",
    "email address",
    "タイムスタンプ",
    "氏名",
    "名前",
    "メールアドレス",
    "メール",
    "備考",
    "メモ",
}
LEGACY_DAY_KEYS = ["day1", "day2", "day3", "day4"]
SKIP_VALUES = {"", "なし", "不要", "未選択", "nan", "none", "null"}
FULL_WIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def load_orders(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSVファイルが見つかりません: {path}")

    df = read_orders_csv(path)
    get_order_columns(df)
    return df


def read_orders_csv(path: Path) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return pd.read_csv(path, dtype=str, keep_default_na=False, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise RuntimeError(
        f"CSVの文字コードを読み取れませんでした: {path}. UTF-8 または Shift_JIS(CP932) で保存してください。"
    ) from last_error


def get_order_columns(df: pd.DataFrame) -> list[str]:
    order_columns = [column for column in df.columns if column.strip().lstrip("\ufeff") not in BASE_COLUMNS]
    if not order_columns:
        raise ValueError("注文対象の列がありません。day1〜day4、7/14、7月14日 のような日付列を用意してください。")
    return order_columns


def normalize_bento_no(value: object) -> str | None:
    raw_value = str(value).strip()
    if raw_value.lower() in SKIP_VALUES:
        return None

    normalized_value = raw_value.translate(FULL_WIDTH_DIGITS)
    match = re.match(r"^([0-9]+)", normalized_value)
    if match:
        return match.group(1)

    bento_no = normalized_value.strip()
    if bento_no.lower() in SKIP_VALUES:
        return None
    return bento_no


def aggregate_orders(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    order_columns = get_order_columns(df)
    aggregated: dict[str, dict[str, int]] = {order_column: {} for order_column in order_columns}

    for order_column in order_columns:
        for raw_bento_no in df[order_column]:
            bento_no = normalize_bento_no(raw_bento_no)
            if bento_no is None:
                continue
            aggregated[order_column][bento_no] = aggregated[order_column].get(bento_no, 0) + 1

    return aggregated


def aggregate_total_orders(df: pd.DataFrame) -> dict[str, int]:
    order_columns = get_order_columns(df)
    aggregated: dict[str, int] = {}

    for order_column in order_columns:
        for raw_bento_no in df[order_column]:
            bento_no = normalize_bento_no(raw_bento_no)
            if bento_no is None:
                continue
            aggregated[bento_no] = aggregated.get(bento_no, 0) + 1

    return aggregated


def print_summary(aggregated: dict[str, dict[str, int]]) -> None:
    print("=== 弁当注文 集計結果 ===")
    for day_key, orders in aggregated.items():
        print(f"\n[{day_key}]")
        if not orders:
            print("  注文なし")
            continue

        for bento_no in sorted(orders, key=sort_bento_no):
            print(f"  弁当番号 {bento_no}: {orders[bento_no]}個")


def print_total_summary(orders: dict[str, int]) -> None:
    print("=== 弁当注文 一括集計結果 ===")
    if not orders:
        print("注文なし")
        return

    total = 0
    for bento_no in sorted(orders, key=sort_bento_no):
        quantity = orders[bento_no]
        total += quantity
        print(f"弁当番号 {bento_no}: {quantity}個")
    print(f"合計: {total}個")


def sort_bento_no(value: str) -> tuple[int, int | str]:
    if value.isdigit():
        return (0, int(value))
    return (1, value)


def is_gui_mode() -> bool:
    return os.getenv("BENTO_AUTO_ORDER_GUI", "").strip() == "1" or getattr(sys, "frozen", False)


def first_visible_locator(page, selectors: list[str], timeout_ms: int = 2_000):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout_ms)
            return locator, selector
        except PlaywrightTimeoutError:
            continue
    return None, ""


def fill_login_credentials(page) -> None:
    username_selectors = [
        site_selectors.USERNAME_INPUT_SELECTOR,
        'input[name="login_id"]',
        'input[name="loginId"]',
        'input[name="login"]',
        'input[name="user"]',
        'input[name="userid"]',
        'input[name="user_id"]',
        'input[name="email"]',
        'input[type="email"]',
        'input[id*="login" i]',
        'input[id*="user" i]',
        'input[id*="mail" i]',
        'input[name*="login" i]',
        'input[name*="user" i]',
        'input[name*="mail" i]',
        'input[name*="id" i]',
    ]
    password_selectors = [
        site_selectors.PASSWORD_INPUT_SELECTOR,
        'input[type="password"]',
        'input[name="password"]',
        'input[name="passwd"]',
        'input[name="pass"]',
        'input[id*="password" i]',
        'input[id*="passwd" i]',
        'input[id*="pass" i]',
    ]

    password_locator, password_selector = first_visible_locator(page, password_selectors)
    username_locator, username_selector = first_visible_locator(page, username_selectors)

    if password_locator is None:
        raise RuntimeError(
            "ログイン画面のパスワード入力欄が見つかりません。"
            " site_selectors.PASSWORD_INPUT_SELECTOR を実際のHTMLに合わせてください。"
        )

    if username_locator is None:
        username_locator = page.locator(
            "input:not([type='hidden']):not([type='password']):not([type='submit']):not([type='button'])"
        ).first
        try:
            username_locator.wait_for(state="visible", timeout=config.SELECTOR_TIMEOUT_MS)
            username_selector = "first visible non-password input"
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "ログイン画面のID入力欄が見つかりません。"
                " site_selectors.USERNAME_INPUT_SELECTOR を実際のHTMLに合わせてください。"
            ) from exc

    print(f"ログインID入力欄: {username_selector}")
    print(f"パスワード入力欄: {password_selector}")
    username_locator.fill(config.ORDER_SITE_USERNAME)
    password_locator.fill(config.ORDER_SITE_PASSWORD)
    username_value = username_locator.input_value(timeout=config.SELECTOR_TIMEOUT_MS)
    password_value = password_locator.input_value(timeout=config.SELECTOR_TIMEOUT_MS)
    if username_value:
        print("ログインIDを入力しました。")
    if password_value:
        print("パスワードを入力しました。")


def click_login_button(page) -> None:
    button_selectors = [
        site_selectors.LOGIN_BUTTON_SELECTOR,
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("ログイン")',
        'input[value*="ログイン"]',
        'button:has-text("Login")',
        'input[value*="Login"]',
    ]
    button_locator, button_selector = first_visible_locator(page, button_selectors)
    if button_locator is not None:
        print(f"ログインボタン: {button_selector}")
        button_locator.click()
        return

    print("ログインボタンが見つからないため、パスワード欄でEnterを押します。")
    page.keyboard.press("Enter")


def login_form_still_visible(page) -> bool:
    try:
        password_locator = page.locator("input[type='password']").first
        return password_locator.is_visible(timeout=1_000)
    except PlaywrightError:
        return False


def login(page) -> None:
    if not config.LOGIN_URL:
        raise ValueError("ログインURLが未設定です。アプリ内設定を確認してください。")

    page.goto(config.LOGIN_URL, wait_until="domcontentloaded")

    if config.LOGIN_URL.startswith("file://") or Path(config.LOGIN_URL).exists():
        print("\nローカルHTMLを開いているため、ログイン処理をスキップします。")
        return

    if not config.ORDER_SITE_USERNAME or not config.ORDER_SITE_PASSWORD:
        raise RuntimeError("ログインIDまたはパスワードが未入力です。アプリ画面で入力してください。")

    fill_login_credentials(page)
    click_login_button(page)

    try:
        page.wait_for_load_state("domcontentloaded", timeout=config.LOGIN_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass

    if login_form_still_visible(page):
        raise RuntimeError("ログイン後もログイン画面のままです。ログインIDとパスワードを確認してください。")

    try:
        page.wait_for_selector(site_selectors.LOGIN_SUCCESS_SELECTOR, timeout=config.LOGIN_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "ログイン成功を確認できませんでした。"
            " site_selectors.LOGIN_SUCCESS_SELECTOR やログイン情報を確認してください。"
        ) from exc


def build_day_url(day_key: str) -> str:
    if day_key in config.DAY_URLS and config.DAY_URLS[day_key]:
        return config.DAY_URLS[day_key]
    if config.DAILY_URL_TEMPLATE:
        return config.DAILY_URL_TEMPLATE.format(date=day_key, day_key=day_key)
    return ""


def build_order_url() -> str:
    order_url = config.ORDER_URL or config.DAY_URLS.get("day1", "") or config.LOGIN_URL
    if config.ORDER_DATE and order_url:
        separator = "&" if "?" in order_url else "?"
        return f"{order_url}{separator}{urlencode({'date': config.ORDER_DATE})}"
    return order_url


def fill_day_orders(page, day_key: str, orders: dict[str, int]) -> None:
    day_url = build_day_url(day_key)
    if not day_url:
        print(f"警告: {day_key} の注文ページURLが未設定のためスキップします。")
        return

    page.goto(day_url)
    page.wait_for_load_state("networkidle")

    if not orders:
        print(f"{day_key}: 入力する注文がありません。")
        return

    warned_available_numbers = False
    for bento_no, quantity in sorted(orders.items(), key=lambda item: sort_bento_no(item[0])):
        if fill_quantity_by_bento_no(page, bento_no, quantity):
            print(f"{day_key}: 弁当番号 {bento_no} に {quantity} 個を入力しました。")
        else:
            print(f"警告: {day_key} の弁当番号 {bento_no} の数量欄が見つかりません。")
            if not warned_available_numbers:
                print(f"このページで検出できた弁当番号: {', '.join(get_available_bento_numbers(page))}")
                warned_available_numbers = True


def fill_bulk_orders(page, orders: dict[str, int]) -> None:
    order_url = build_order_url()
    if not order_url:
        raise ValueError("注文ページURLが未設定です。アプリ内設定を確認してください。")

    if page.url != order_url:
        page.goto(order_url)
        page.wait_for_load_state("networkidle")

    if not orders:
        print("入力する注文がありません。")
        return

    warned_available_numbers = False
    for bento_no, quantity in sorted(orders.items(), key=lambda item: sort_bento_no(item[0])):
        if fill_quantity_by_bento_no(page, bento_no, quantity):
            print(f"弁当番号 {bento_no} に {quantity} 個を入力しました。")
        else:
            print(f"警告: 弁当番号 {bento_no} の数量欄が見つかりません。")
            if not warned_available_numbers:
                print(f"このページで検出できた弁当番号: {', '.join(get_available_bento_numbers(page))}")
                warned_available_numbers = True


def fill_quantity_by_bento_no(page, bento_no: str, quantity: int) -> bool:
    try:
        page.wait_for_selector(site_selectors.ORDER_TABLE_SELECTOR, timeout=config.SELECTOR_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        return False

    return page.evaluate(
        """
        ({ bentoNo, quantity }) => {
            const rows = Array.from(document.querySelectorAll("#daily-order-table tbody tr"));
            const startsWithBentoNo = new RegExp("^\\\\s*" + String(bentoNo) + "(?!\\\\d)");
            const row = rows.find((tr) => {
                const prodNo = tr.querySelector(".prod-no");
                if (prodNo && prodNo.textContent.trim() === String(bentoNo)) {
                    return true;
                }

                const productCell = tr.querySelector(".prod") || tr.cells?.[0];
                const productText = productCell ? productCell.textContent.trim() : tr.textContent.trim();
                return startsWithBentoNo.test(productText);
            });

            if (!row) return false;

            const input = row.querySelector("input.input-amount, input[type='tel'], input[type='number'], input");
            if (!input) return false;

            input.scrollIntoView({ block: "center", inline: "nearest" });
            input.focus();
            input.value = String(quantity);
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            return true;
        }
        """,
        {"bentoNo": bento_no, "quantity": quantity},
    )


def get_available_bento_numbers(page) -> list[str]:
    return page.evaluate(
        """
        () => {
            const rows = Array.from(document.querySelectorAll("#daily-order-table tbody tr"));
            return rows.map((tr) => {
                const prodNo = tr.querySelector(".prod-no");
                if (prodNo) return prodNo.textContent.trim();

                const productCell = tr.querySelector(".prod") || tr.cells?.[0];
                const text = productCell ? productCell.textContent.trim() : tr.textContent.trim();
                const match = text.match(/^\\s*(\\d+)/);
                return match ? match[1] : "";
            }).filter(Boolean);
        }
        """
    )


def wait_for_human_review(page, browser) -> None:
    print("ブラウザを開いたまま待機します。内容確認後、ブラウザを手動で閉じてください。")
    while True:
        try:
            if not browser.is_connected() or page.is_closed():
                break
            page.wait_for_timeout(1_000)
        except PlaywrightError:
            break
    print("ブラウザが閉じられたため、待機を終了します。")


def launch_visible_browser(playwright):
    channel_candidates: list[str] = []
    if config.BROWSER_CHANNEL:
        channel_candidates.append(config.BROWSER_CHANNEL)
    if sys.platform == "win32" and "msedge" not in channel_candidates:
        channel_candidates.append("msedge")

    last_error: Exception | None = None
    for channel in channel_candidates:
        try:
            print(f"ブラウザ channel={channel} で起動します。")
            return playwright.chromium.launch(headless=False, channel=channel)
        except Exception as exc:
            print(f"ブラウザ channel={channel} を起動できませんでした: {exc}")
            last_error = exc

    if not getattr(sys, "frozen", False):
        try:
            print("Playwright Chromiumで起動します。")
            return playwright.chromium.launch(headless=False)
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "ブラウザを起動できませんでした。Windowsでは Google Chrome または Microsoft Edge をインストールしてください。"
    ) from last_error


def run() -> None:
    current_csv_path = config.CSV_PATH
    current_username = config.ORDER_SITE_USERNAME
    current_password = config.ORDER_SITE_PASSWORD
    current_order_date = config.ORDER_DATE
    config.load_settings()
    if current_csv_path:
        config.CSV_PATH = current_csv_path
    if current_username:
        config.ORDER_SITE_USERNAME = current_username
    if current_password:
        config.ORDER_SITE_PASSWORD = current_password
    if current_order_date:
        config.ORDER_DATE = current_order_date

    if sync_playwright is None:
        raise RuntimeError(
            "Playwright がインストールされていません。"
            " `pip install -r requirements.txt` と `playwright install` を実行してください。"
        )

    aggregated = aggregate_total_orders(load_orders(config.CSV_PATH))
    print_total_summary(aggregated)

    with sync_playwright() as playwright:
        browser = launch_visible_browser(playwright)
        context = browser.new_context()
        page = context.new_page()

        try:
            login(page)
            fill_bulk_orders(page, aggregated)

            print("\n入力が完了しました。注文確定ボタンは自動クリックしていません。")
            print("内容を確認し、必要なら手動で注文確定してください。")
            wait_for_human_review(page, browser)
        finally:
            print("処理を終了します。ブラウザを閉じる場合は手動で閉じてください。")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
