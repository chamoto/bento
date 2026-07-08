from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

import config
import main


APP_DIR = config.BASE_DIR
RESOURCE_DIR = config.RESOURCE_DIR
ENV_PATH = APP_DIR / ".env"
DEFAULT_CSV_PATH = APP_DIR / "ajiya_sample_orders.csv"


class BentoAutoOrderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bento Auto Order")
        self.root.geometry("760x560")
        self.root.minsize(680, 480)

        self.csv_path_var = tk.StringVar(value=str(Path(config.CSV_PATH)))

        self.build_ui()
        self.refresh_summary()

    def build_ui(self) -> None:
        container = tk.Frame(self.root, padx=16, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(container, text="Bento Auto Order", font=("", 18, "bold"))
        title.pack(anchor="w")

        notice = tk.Label(
            container,
            text="CSVを集計してブラウザに入力します。注文確定ボタンは自動で押しません。",
            fg="#444444",
        )
        notice.pack(anchor="w", pady=(4, 16))

        csv_frame = tk.LabelFrame(container, text="CSV file", padx=10, pady=10)
        csv_frame.pack(fill=tk.X)

        csv_entry = tk.Entry(csv_frame, textvariable=self.csv_path_var)
        csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(csv_frame, text="Choose", command=self.choose_csv).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(csv_frame, text="Open CSV", command=self.open_csv).pack(side=tk.LEFT, padx=(8, 0))

        button_frame = tk.Frame(container)
        button_frame.pack(fill=tk.X, pady=12)

        tk.Button(button_frame, text="Refresh Summary", command=self.refresh_summary).pack(side=tk.LEFT)
        tk.Button(button_frame, text="Edit Settings", command=self.open_env).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(button_frame, text="Run Browser Input", command=self.run_browser_input).pack(side=tk.RIGHT)

        summary_frame = tk.LabelFrame(container, text="Summary", padx=10, pady=10)
        summary_frame.pack(fill=tk.BOTH, expand=True)

        self.output = scrolledtext.ScrolledText(summary_frame, height=18)
        self.output.pack(fill=tk.BOTH, expand=True)

    def choose_csv(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose CSV",
            initialdir=str(APP_DIR),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not selected:
            return

        self.csv_path_var.set(selected)
        self.update_env_value("CSV_PATH", selected)
        self.refresh_summary()

    def open_csv(self) -> None:
        path = Path(self.csv_path_var.get()).expanduser()
        if not path.exists():
            messagebox.showerror("CSV not found", f"CSV file was not found:\n{path}")
            return

        open_file(path)

    def open_env(self) -> None:
        ensure_env_exists()
        open_file(ENV_PATH)

    def refresh_summary(self) -> None:
        self.output.delete("1.0", tk.END)
        try:
            csv_path = Path(self.csv_path_var.get()).expanduser()
            df = main.load_orders(csv_path)
            aggregated = main.aggregate_orders(df)
            self.output.insert(tk.END, format_summary(aggregated))
        except Exception as exc:
            self.output.insert(tk.END, f"Error: {exc}\n")

    def run_browser_input(self) -> None:
        csv_path = Path(self.csv_path_var.get()).expanduser()
        self.update_env_value("CSV_PATH", str(csv_path))
        self.output.insert(tk.END, "\nStarting browser input...\n")
        self.output.see(tk.END)

        thread = threading.Thread(target=self.run_browser_input_worker, daemon=True)
        thread.start()

    def run_browser_input_worker(self) -> None:
        try:
            main.run()
            self.append_output("\nBrowser input finished.\n")
        except Exception as exc:
            self.append_output(f"\nError: {exc}\n")
            messagebox.showerror("Run failed", str(exc))

    def append_output(self, text: str) -> None:
        self.root.after(0, lambda: (self.output.insert(tk.END, text), self.output.see(tk.END)))

    def update_env_value(self, key: str, value: str) -> None:
        ensure_env_exists()
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        updated = False
        next_lines = []

        for line in lines:
            if line.startswith(f"{key}="):
                next_lines.append(f"{key}={value}")
                updated = True
            else:
                next_lines.append(line)

        if not updated:
            next_lines.append(f"{key}={value}")

        ENV_PATH.write_text("\n".join(next_lines) + "\n", encoding="utf-8")


def format_summary(aggregated: dict[str, dict[str, int]]) -> str:
    lines = ["=== Order Summary ==="]
    total = 0

    for day_key, orders in aggregated.items():
        lines.append("")
        lines.append(f"[{day_key}]")
        if not orders:
            lines.append("  No orders")
            continue

        day_total = 0
        for bento_no in sorted(orders, key=main.sort_bento_no):
            quantity = orders[bento_no]
            day_total += quantity
            total += quantity
            lines.append(f"  Bento {bento_no}: {quantity}")
        lines.append(f"  Day total: {day_total}")

    lines.append("")
    lines.append(f"TOTAL: {total}")
    return "\n".join(lines) + "\n"


def ensure_env_exists() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    ensure_default_files_exist()
    if ENV_PATH.exists():
        return
    example_path = RESOURCE_DIR / ".env.example"
    ENV_PATH.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_default_files_exist() -> None:
    for file_name in ["ajiya_sample_orders.csv", "sample_orders.csv", "google_form_sample_orders.csv", "google_form_count_result.csv"]:
        destination = APP_DIR / file_name
        source = RESOURCE_DIR / file_name
        if not destination.exists() and source.exists():
            destination.write_bytes(source.read_bytes())


def open_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def main_app() -> None:
    ensure_env_exists()
    root = tk.Tk()
    BentoAutoOrderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main_app()
