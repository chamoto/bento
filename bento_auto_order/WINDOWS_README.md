# Windowsで使う手順

## 1. Pythonを入れる

WindowsにPython 3をインストールしてください。

https://www.python.org/downloads/windows/

インストール画面では `Add python.exe to PATH` にチェックを入れてください。

## 2. フォルダを配布する

この `bento_auto_order` フォルダをWindows PCへコピーします。

配布時は以下を入れないでください。

- `.venv`
- `.env`

## 3. 初回セットアップ

Windowsで `setup_windows.bat` をダブルクリックします。

これで以下を行います。

- 仮想環境 `.venv` を作成
- 必要なPythonパッケージをインストール
- PlaywrightのChromiumをインストール

## 4. 起動

`start_app_windows.bat` をダブルクリックします。

GUIアプリが開きます。

注文サイトURLはアプリ内に固定されています。注文日はアプリ画面のプルダウンから選び、ログインIDとパスワードはアプリ画面で入力してください。ログインIDは「IDを記憶」にチェックした場合だけ保存できます。パスワードは保存しません。注文日の候補は4日後から再来月末までです。

注文日は以下のURLの `date=` 部分として使います。

```text
https://reitou.ajiya-lunch.net/daily/?date=2026-07-28
```

Chromeを起動できない場合は、Microsoft Edgeへ自動で切り替えます。

- `CSVを開く`: CSVをExcelなどで開く
- `CSVを選ぶ`: 別のCSVを選ぶ
- `注文日`: 自動入力する注文ページの日付をプルダウンから選ぶ
- `集計`: 集計を確認する
- `ログを開く`: 実行ログを開く
- `自動入力`: ブラウザを開いて注文ページへ入力する

注文確定ボタンは自動で押しません。最後は必ず人間が画面を確認して、手動で確定してください。

## CSVだけ開きたい場合

GUIの `CSVを開く` を押してください。

選択中のCSVを開きます。初期状態ではサンプルCSVを開きます。

CSVはWindows Excelで文字化けしにくい `UTF-8 BOM付き` で保存しています。
読み込みは `UTF-8 BOM付き`、`UTF-8`、`Shift_JIS(CP932)` に対応しています。

## exe化したい場合

Pythonを入れずに使いたい場合は、PyInstallerで `.exe` 化できます。

Windows版はDLL込みの1ファイルexeとして作ります。

```bat
build_windows_exe.bat
```

出力:

```text
dist\BentoAutoOrder.exe
```

Google Chrome自体は同梱しません。Chromeが無い場合はMicrosoft Edgeを使います。
