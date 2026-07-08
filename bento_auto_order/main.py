from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

import pandas as pd

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    PlaywrightTimeoutError = TimeoutError
    sync_playwright = None

import config
import site_selectors


BASE_COLUMNS = {"timestamp", "name", "note"}
LEGACY_DAY_KEYS = ["day1", "day2", "day3", "day4"]
SKIP_VALUES = {"", "なし", "不要", "未選択", "nan", "none", "null"}


def load_orders(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSVファイルが見つかりません: {path}")

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing_columns = [column for column in ["timestamp", "name"] if column not in df.columns]
    if missing_columns:
        raise ValueError(f"CSVに必須カラムがありません: {', '.join(missing_columns)}")

    return df


def get_order_columns(df: pd.DataFrame) -> list[str]:
    order_columns = [column for column in df.columns if column not in BASE_COLUMNS]
    if not order_columns:
        raise ValueError("注文対象の列がありません。day1〜day4 または YYYY-MM-DD の日付列を用意してください。")
    return order_columns


def normalize_bento_no(value: object) -> str | None:
    bento_no = str(value).strip()
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


def print_summary(aggregated: dict[str, dict[str, int]]) -> None:
    print("=== 弁当注文 集計結果 ===")
    for day_key, orders in aggregated.items():
        print(f"\n[{day_key}]")
        if not orders:
            print("  注文なし")
            continue

        for bento_no in sorted(orders, key=sort_bento_no):
            print(f"  弁当番号 {bento_no}: {orders[bento_no]}個")


def sort_bento_no(value: str) -> tuple[int, int | str]:
    if value.isdigit():
        return (0, int(value))
    return (1, value)


def login(page) -> None:
    if not config.LOGIN_URL:
        raise ValueError("ORDER_SITE_LOGIN_URL が未設定です。.env を確認してください。")

    page.goto(config.LOGIN_URL)
    page.wait_for_load_state("networkidle")

    if config.LOGIN_URL.startswith("file://") or Path(config.LOGIN_URL).exists():
        print("\nローカルHTMLを開いているため、ログイン処理をスキップします。")
        return

    if not config.ORDER_SITE_USERNAME or not config.ORDER_SITE_PASSWORD:
        print("\nORDER_SITE_USERNAME または ORDER_SITE_PASSWORD が空です。")
        print("ブラウザで手動ログインしてください。ログイン後、ターミナルで Enter を押すと続行します。")
        input("手動ログインが終わったら Enter: ")
        return

    page.fill(site_selectors.USERNAME_INPUT_SELECTOR, config.ORDER_SITE_USERNAME)
    page.fill(site_selectors.PASSWORD_INPUT_SELECTOR, config.ORDER_SITE_PASSWORD)
    page.click(site_selectors.LOGIN_BUTTON_SELECTOR)

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


def run() -> None:
    if sync_playwright is None:
        raise RuntimeError(
            "Playwright がインストールされていません。"
            " `pip install -r requirements.txt` と `playwright install` を実行してください。"
        )

    aggregated = aggregate_orders(load_orders(config.CSV_PATH))
    print_summary(aggregated)

    with sync_playwright() as playwright:
        launch_options = {"headless": False}
        if config.BROWSER_CHANNEL:
            launch_options["channel"] = config.BROWSER_CHANNEL

        try:
            browser = playwright.chromium.launch(**launch_options)
        except Exception:
            if not config.BROWSER_CHANNEL:
                raise
            print(f"Chrome channel '{config.BROWSER_CHANNEL}' が使えないため、Playwright Chromiumで再試行します。")
            browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            login(page)
            for day_key, orders in aggregated.items():
                fill_day_orders(page, day_key, orders)

            print("\n入力が完了しました。注文確定ボタンは自動クリックしていません。")
            print("ブラウザを開いたまま停止します。内容を確認し、必要なら手動で注文確定してください。")
            page.pause()
        finally:
            print("処理を終了します。ブラウザを閉じる場合は手動で閉じてください。")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
