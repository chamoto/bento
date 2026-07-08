from __future__ import annotations

import os
import subprocess
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import config
import main


APP_DIR = config.BASE_DIR
RESOURCE_DIR = config.RESOURCE_DIR
ENV_PATH = APP_DIR / ".env"
DEFAULT_CSV_PATH = APP_DIR / "ajiya_sample_orders.csv"
LOG_PATH = APP_DIR / "app.log"


def ensure_app_files() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    for file_name in ["ajiya_sample_orders.csv", "sample_orders.csv", "google_form_sample_orders.csv", "google_form_count_result.csv"]:
        source = RESOURCE_DIR / file_name
        destination = APP_DIR / file_name
        if not destination.exists() and source.exists():
            destination.write_bytes(source.read_bytes())

    if not ENV_PATH.exists():
        source = RESOURCE_DIR / ".env.example"
        if source.exists():
            ENV_PATH.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            ENV_PATH.write_text("", encoding="utf-8")


def open_file(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
        return
    subprocess.run(["xdg-open", str(path)], check=False)


def update_env_value(key: str, value: str) -> None:
    ensure_app_files()
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    updated = False
    next_lines: list[str] = []

    for line in lines:
        if line.startswith(f"{key}="):
            next_lines.append(f"{key}={value}")
            updated = True
        else:
            next_lines.append(line)

    if not updated:
        next_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(next_lines) + "\n", encoding="utf-8")


def append_log_file(message: str) -> None:
    ensure_app_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def format_summary(orders: dict[str, int], csv_path: Path) -> str:
    lines = ["=== 発注合計数 ===", f"CSV: {csv_path}", ""]
    if not orders:
        lines.append("注文なし")
        return "\n".join(lines)

    total = 0
    for bento_no in sorted(orders, key=main.sort_bento_no):
        quantity = orders[bento_no]
        total += quantity
        lines.append(f"弁当番号 {bento_no}: {quantity}個")
    lines.append("")
    lines.append(f"合計: {total}個")
    return "\n".join(lines)


class SignalTextWriter:
    def __init__(self, emit) -> None:
        self.emit = emit
        self.buffer = ""

    def write(self, text: str) -> int:
        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.strip():
                self.emit(line)
        return len(text)

    def flush(self) -> None:
        if self.buffer.strip():
            self.emit(self.buffer.strip())
        self.buffer = ""


class BrowserInputWorker(QObject):
    finished = Signal()
    failed = Signal(str)
    message = Signal(str)

    def __init__(self, csv_path: Path) -> None:
        super().__init__()
        self.csv_path = csv_path

    def run(self) -> None:
        try:
            writer = SignalTextWriter(self.message.emit)
            with redirect_stdout(writer), redirect_stderr(writer):
                config.CSV_PATH = str(self.csv_path)
                os.environ["CSV_PATH"] = str(self.csv_path)
                os.environ["BENTO_AUTO_ORDER_GUI"] = "1"
                self.message.emit("ブラウザ入力を開始しました。")
                self.message.emit("一括注文として、注文ページ1枚に合計数量を入力します。")
                self.message.emit("注文サイト操作用のブラウザが開きます。注文確定は自動で押しません。")
                main.run()
                writer.flush()
                self.message.emit("ブラウザ入力が終了しました。")
            self.finished.emit()
        except Exception as exc:
            self.message.emit(traceback.format_exc())
            self.failed.emit(str(exc))
            self.finished.emit()


class BentoAutoOrderWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ensure_app_files()

        self.worker_thread: QThread | None = None
        self.worker: BrowserInputWorker | None = None

        self.setWindowTitle("Bento Auto Order")
        self.resize(820, 620)
        self.setMinimumSize(720, 520)

        self.csv_path_input = QLineEdit(str(Path(config.CSV_PATH)))
        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.run_button = QPushButton("自動入力")

        self.build_ui()
        self.refresh_summary()

    def build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Bento Auto Order")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        notice = QLabel("日付や氏名に関係なく、弁当番号ごとの発注合計数を集計します。注文確定ボタンは自動で押しません。")
        notice.setStyleSheet("color: #444;")
        layout.addWidget(notice)

        csv_box = self.make_panel("CSV")
        csv_layout = QHBoxLayout(csv_box)
        csv_layout.addWidget(self.csv_path_input, 1)

        choose_button = QPushButton("CSVを選ぶ")
        choose_button.clicked.connect(self.choose_csv)
        csv_layout.addWidget(choose_button)

        open_csv_button = QPushButton("CSVを開く")
        open_csv_button.clicked.connect(self.open_csv)
        csv_layout.addWidget(open_csv_button)
        layout.addWidget(csv_box)

        utility_row = QHBoxLayout()
        utility_row.addStretch(1)

        settings_button = QPushButton("設定を開く")
        settings_button.clicked.connect(self.open_settings)
        utility_row.addWidget(settings_button)

        log_button = QPushButton("ログを開く")
        log_button.clicked.connect(self.open_log)
        utility_row.addWidget(log_button)
        layout.addLayout(utility_row)

        action_row = QHBoxLayout()
        action_row.addStretch(1)

        refresh_button = QPushButton("集計")
        refresh_button.clicked.connect(self.refresh_summary)
        refresh_button.setMinimumWidth(140)
        refresh_button.setStyleSheet("font-weight: 700; padding: 8px 14px;")
        action_row.addWidget(refresh_button)

        self.run_button.setText("自動入力")
        self.run_button.clicked.connect(self.run_browser_input)
        self.run_button.setMinimumWidth(140)
        self.run_button.setStyleSheet("font-weight: 700; padding: 8px 14px;")
        action_row.addWidget(self.run_button)

        action_row.addStretch(1)
        layout.addLayout(action_row)

        summary_label = QLabel("集計")
        summary_label.setStyleSheet("font-weight: 700;")
        layout.addWidget(summary_label)
        layout.addWidget(self.summary_output, 3)

        status_label = QLabel("実行ログ")
        status_label.setStyleSheet("font-weight: 700;")
        layout.addWidget(status_label)
        layout.addWidget(self.status_output, 1)

    def make_panel(self, title: str) -> QFrame:
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setProperty("title", title)
        panel.setStyleSheet("QFrame { background: #fff; border: 1px solid #d8dee4; border-radius: 6px; padding: 8px; }")
        return panel

    def choose_csv(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "CSVを選択",
            str(APP_DIR),
            "CSV files (*.csv);;All files (*.*)",
        )
        if not selected:
            return

        self.csv_path_input.setText(selected)
        update_env_value("CSV_PATH", selected)
        config.CSV_PATH = selected
        self.refresh_summary()

    def open_csv(self) -> None:
        path = Path(self.csv_path_input.text()).expanduser()
        if not path.exists():
            QMessageBox.critical(self, "CSVが見つかりません", f"CSVファイルが見つかりません:\n{path}")
            return
        open_file(path)

    def open_settings(self) -> None:
        ensure_app_files()
        open_file(ENV_PATH)

    def open_log(self) -> None:
        ensure_app_files()
        if not LOG_PATH.exists():
            LOG_PATH.write_text("", encoding="utf-8")
        open_file(LOG_PATH)

    def refresh_summary(self) -> None:
        csv_path = Path(self.csv_path_input.text()).expanduser()
        try:
            df = main.load_orders(csv_path)
            aggregated = main.aggregate_total_orders(df)
            self.summary_output.setPlainText(format_summary(aggregated, csv_path))
            self.status("集計しました。")
        except Exception as exc:
            self.summary_output.setPlainText(f"エラー: {exc}")

    def run_browser_input(self) -> None:
        csv_path = Path(self.csv_path_input.text()).expanduser()
        if not csv_path.exists():
            QMessageBox.critical(self, "CSVが見つかりません", f"CSVファイルが見つかりません:\n{csv_path}")
            return

        update_env_value("CSV_PATH", str(csv_path))
        config.CSV_PATH = str(csv_path)
        self.run_button.setEnabled(False)

        self.worker_thread = QThread()
        self.worker = BrowserInputWorker(csv_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.message.connect(self.status)
        self.worker.failed.connect(self.show_worker_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.on_worker_thread_finished)
        self.worker_thread.start()

    def on_worker_thread_finished(self) -> None:
        self.run_button.setEnabled(True)
        self.worker_thread = None
        self.worker = None

    def show_worker_error(self, message: str) -> None:
        self.status(f"エラー: {message}")
        QMessageBox.critical(self, "実行エラー", message)

    def status(self, message: str) -> None:
        self.status_output.append(message)
        append_log_file(message)
        self.status_output.verticalScrollBar().setValue(self.status_output.verticalScrollBar().maximum())

    def closeEvent(self, event) -> None:
        if self.worker_thread is not None and self.worker_thread.isRunning():
            QMessageBox.information(
                self,
                "自動入力中",
                "自動入力の確認待ちです。先にブラウザを閉じてから、もう一度アプリを閉じてください。",
            )
            event.ignore()
            return
        super().closeEvent(event)


def main_app() -> None:
    QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
    app = QApplication(sys.argv)
    window = BentoAutoOrderWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_app()
