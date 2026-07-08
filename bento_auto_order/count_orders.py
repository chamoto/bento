from __future__ import annotations

import sys
from pathlib import Path

import main


DEFAULT_CSV_PATH = Path(__file__).resolve().parent / "google_form_sample_orders.csv"


def print_count_csv(orders: dict[str, int]) -> None:
    print("弁当番号,数量")
    total = 0
    for bento_no in sorted(orders, key=main.sort_bento_no):
        quantity = orders[bento_no]
        total += quantity
        print(f"{bento_no},{quantity}")
    print(f"合計,{total}")


def run(csv_path: str | Path = DEFAULT_CSV_PATH) -> None:
    df = main.load_orders(csv_path)
    orders = main.aggregate_total_orders(df)
    print_count_csv(orders)


if __name__ == "__main__":
    try:
        path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV_PATH
        run(path)
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
