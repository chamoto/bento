# Bento Auto Order

Googleフォームの回答CSVを読み込み、弁当番号ごとの数量を集計し、Playwrightで注文サイトの数量欄へ自動入力するPythonアプリです。

注文確定ボタンは自動クリックしません。入力後はブラウザを開いたまま停止するので、必ず人間が内容を確認してから手動で確定してください。

Windows / Mac 両対応のGUI入口として `app.py` を用意しています。

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
2. `.env` を編集
3. `start_app_windows.bat` をダブルクリック

詳しくは `WINDOWS_README.md` を見てください。

Mac:

```bash
cd bento_auto_order
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python app.py
```

## .env の作り方

`.env.example` をコピーして `.env` を作成します。

```bash
cp .env.example .env
```

`.env` にログインURL、ログイン情報、4日分の注文ページURLを設定してください。

```env
ORDER_SITE_LOGIN_URL=https://example.com/login
ORDER_SITE_USERNAME=your_username
ORDER_SITE_PASSWORD=your_password
ORDER_SITE_DAY1_URL=https://example.com/order/day1
ORDER_SITE_DAY2_URL=https://example.com/order/day2
ORDER_SITE_DAY3_URL=https://example.com/order/day3
ORDER_SITE_DAY4_URL=https://example.com/order/day4
CSV_PATH=sample_orders.csv
```

`CSV_PATH` を空にした場合は、同じフォルダの `sample_orders.csv` を読み込みます。

## 実行方法

GUIで使う場合:

```bash
python app.py
```

CLIで直接実行する場合:

```bash
python main.py
```

実行すると、まずCSVの集計結果がコンソールに表示されます。その後、ブラウザを表示した状態で注文サイトへログインし、各日付ページの数量欄へ入力します。

## CSVの形式

必須カラムは以下です。

```csv
timestamp,name,day1,day2,day3,day4,note
2026-07-07 10:01,山田太郎,1,2,なし,4,
2026-07-07 10:03,佐藤花子,1,1,3,なし,
2026-07-07 10:05,田中一郎,2,なし,3,4,
```

`day1` から `day4` には弁当番号を入れてください。

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
- 必須カラムがない場合は停止します。
- 空欄、`なし`、`不要`、`未選択` は集計から除外します。
- 数量欄が見つからない弁当番号は警告を表示し、次の入力へ進みます。
- ログイン成功を確認できない場合は停止します。
