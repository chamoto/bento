# Bento Auto Order

Googleフォームの回答CSVを読み込み、弁当番号ごとの数量を集計し、Playwrightで注文サイトの数量欄へ自動入力するPythonアプリです。

注文確定ボタンは自動クリックしません。入力後はブラウザを開いたまま停止するので、必ず人間が内容を確認してから手動で確定してください。

Windows / Mac 両対応のGUI入口として `qt_app.py` を用意しています。

配布用には、Windowsは `.exe`、Macは `.app` として別々にビルドできます。詳しくは `PACKAGING.md` を見てください。

## セットアップ

macOS / Linux:

```bash
cd bento_auto_order
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

Windows:

1. `setup_windows.bat` をダブルクリック
2. `start_app_windows.bat` をダブルクリック
3. アプリ画面でCSV、注文日、ログインID、パスワードを入力

詳しくは `WINDOWS_README.md` を見てください。

Mac:

```bash
cd bento_auto_order
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python qt_app.py
```

## ログイン情報

`.env` は使いません。注文サイトURLはアプリ内に固定しています。

ログインIDとパスワードはアプリ画面で入力します。ログインIDは「IDを記憶」にチェックした場合だけ保存できます。パスワードは保存しません。

## 注文日

注文日はアプリ画面のプルダウンから選びます。候補は4日後から再来月末までです。

入力した日付から以下のURLを自動生成します。

```text
https://reitou.ajiya-lunch.net/daily/?date=2026-07-28
```

注文画面は日付ごとに異なるため、自動入力前に必ず対象日を確認してください。

## 実行方法

GUIで使う場合:

```bash
python qt_app.py
```

GUIの `ログを開く` ボタンから、Windowsでの実行ログを確認できます。

CLIで直接実行する場合:

```bash
python main.py
```

実行すると、まずCSVの集計結果が表示されます。その後、ブラウザを表示した状態で注文サイトへログインし、指定した注文日のページに弁当番号ごとの合計数量を入力します。

集計だけ確認する場合:

```bash
python count_orders.py google_form_sample_orders.csv
```

集計結果をCSVファイルとして保存する場合:

```bash
python count_orders.py google_form_sample_orders.csv --output google_form_count_result.csv
```

出力例:

```csv
弁当番号,数量
123,1
126,1
127,1
128,1
合計,4
```

## CSVの形式

英語カラム、またはGoogleフォーム標準の日本語カラムに対応しています。

```csv
timestamp,name,day1,day2,day3,day4,note
2026-07-07 10:01,山田太郎,1,2,なし,4,
2026-07-07 10:03,佐藤花子,1,1,3,なし,
2026-07-07 10:05,田中一郎,2,なし,3,4,
```

Googleフォームからそのまま出る以下の形式にも対応しています。

```csv
タイムスタンプ,氏名,7/14,7/15,7/16,7/17
2026/07/08 15:11:35,茶本,123大盛：こくうまポーク,126大盛：オリジナルチキン,127大盛：あの時のビーフ,128大盛：メンチカツ
```

`day1` から `day4`、または `7/14`、`7月14日` のような日付列には弁当番号を入れてください。`123大盛：こくうまポーク` のように商品名が付いていても、先頭の `123` だけを弁当番号として集計します。

集計は日付別・氏名別ではありません。全回答者・全日付列をまとめて、弁当番号ごとの発注合計数を出します。注文時はその合計数を1枚の注文ページに一括入力します。

以下の値は注文数に含めません。

- 空欄
- なし
- 不要
- 未選択

## セレクタの調べ方

注文サイトをブラウザで開き、対象の入力欄を右クリックして「検証」を選びます。

数量入力欄が以下のようなHTMLだった場合:

```html
<input name="bento_1">
```

`site_selectors.py` は次のように設定します。

```python
QUANTITY_INPUT_SELECTOR = 'input[name="bento_{bento_no}"]'
```

弁当番号 `1` の場合、実行時に `input[name="bento_1"]` として使われます。

ログイン画面のユーザー名、パスワード、ログインボタンも同じように実サイトのHTMLに合わせて差し替えてください。

```python
USERNAME_INPUT_SELECTOR = 'input[name="username"]'
PASSWORD_INPUT_SELECTOR = 'input[name="password"]'
LOGIN_BUTTON_SELECTOR = 'button[type="submit"]'
LOGIN_SUCCESS_SELECTOR = "body"
```

`LOGIN_SUCCESS_SELECTOR` は、ログイン後の画面にだけ表示される要素に変更するとログイン失敗を検知しやすくなります。

## 注文確定について

このアプリは注文確定ボタンを自動で押しません。

`site_selectors.py` に `NEXT_OR_CONFIRM_BUTTON_SELECTOR` を用意していますが、サンプルでは使っていません。確認画面へ進む処理を追加する場合も、最終的な注文確定ボタンだけは必ず手動で押してください。

## エラー処理

- CSVファイルがない場合は停止します。
- 注文対象の列がない場合は停止します。
- 空欄、`なし`、`不要`、`未選択` は集計から除外します。
- 数量欄が見つからない弁当番号は警告を表示し、次の入力へ進みます。
- ログイン成功を確認できない場合は停止します。
