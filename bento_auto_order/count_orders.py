from __future__ import annotations

import sys
from pathlib import Path

import main


DEFAULT_CSV_PATH = Path(__file__).resolve().parent / "google_form_sample_orders.csv"


def build_count_csv_lines(orders: dict[str, int]) -> list[str]:
    lines = ["弁当番号,数量"]
    total = 0
    for bento_no in sorted(orders, key=main.sort_bento_no):
        quantity = orders[bento_no]
        total += quantity
        lines.append(f"{bento_no},{quantity}")
    lines.append(f"合計,{total}")
    return lines


def print_count_csv(orders: dict[str, int]) -> None:
    for line in build_count_csv_lines(orders):
        print(line)


def run(csv_path: str | Path = DEFAULT_CSV_PATH, output_path: str | Path | None = None) -> None:
    df = main.load_orders(csv_path)
    orders = main.aggregate_total_orders(df)
    lines = build_count_csv_lines(orders)
    for line in lines:
        print(line)

    if output_path:
        Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        output: Path | None = None
        if "--output" in args:
            output_index = args.index("--output")
            if output_index + 1 >= len(args):
                raise ValueError("--output の後に出力CSVパスを指定してください。")
            output = Path(args[output_index + 1])
            del args[output_index : output_index + 2]
        if "-o" in args:
            output_index = args.index("-o")
            if output_index + 1 >= len(args):
                raise ValueError("-o の後に出力CSVパスを指定してください。")
            output = Path(args[output_index + 1])
            del args[output_index : output_index + 2]

        path = Path(args[0]) if args else DEFAULT_CSV_PATH
        run(path, output)
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
