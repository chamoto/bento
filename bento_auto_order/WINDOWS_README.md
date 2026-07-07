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

`.env.example` は入れてOKです。

## 3. 初回セットアップ

Windowsで `setup_windows.bat` をダブルクリックします。

これで以下を行います。

- 仮想環境 `.venv` を作成
- 必要なPythonパッケージをインストール
- PlaywrightのChromiumをインストール
- `.env` がなければ作成

## 4. .envを編集

`.env` をメモ帳などで開き、注文サイト情報とCSVパスを設定します。

```env
ORDER_SITE_LOGIN_URL=https://example.com/login
ORDER_SITE_USERNAME=your_username
ORDER_SITE_PASSWORD=your_password
ORDER_SITE_DAY1_URL=https://example.com/order/day1
ORDER_SITE_DAY2_URL=https://example.com/order/day2
ORDER_SITE_DAY3_URL=https://example.com/order/day3
ORDER_SITE_DAY4_URL=https://example.com/order/day4
CSV_PATH=ajiya_sample_orders.csv
```

## 5. 起動

`run_windows.bat` をダブルクリックします。

ブラウザが開き、CSVの集計結果を注文ページへ入力します。

注文確定ボタンは自動で押しません。最後は必ず人間が画面を確認して、手動で確定してください。

## CSVだけ開きたい場合

`CSVを開く.bat` をダブルクリックしてください。

`.env` の `CSV_PATH` に設定されたCSVを開きます。未設定の場合は `ajiya_sample_orders.csv` を開きます。

## exe化したい場合

Pythonを入れずに使いたい場合は、PyInstallerで `.exe` 化できます。

ただしPlaywrightのブラウザ同梱やパス調整が少し面倒なので、まずは `.bat` 配布がおすすめです。
