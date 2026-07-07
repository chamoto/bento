USERNAME_INPUT_SELECTOR = 'input[name="username"]'
PASSWORD_INPUT_SELECTOR = 'input[name="password"]'
LOGIN_BUTTON_SELECTOR = 'button[type="submit"]'

# ログイン後の画面にだけ出る要素へ差し替えてください。
LOGIN_SUCCESS_SELECTOR = "body"

# bento_no に弁当番号が入ります。例: input[name="bento_1"]
QUANTITY_INPUT_SELECTOR = 'input[name="bento_{bento_no}"]'

# あじやの日別注文ページ用。弁当番号の入った行から数量欄を探します。
ORDER_TABLE_SELECTOR = "#daily-order-table"
PRODUCT_NO_SELECTOR = ".prod-no"
ROW_QUANTITY_INPUT_SELECTOR = "input.input-amount"

# サイトによって確認画面へ進むボタンが必要な場合だけ使ってください。
# 注文確定ボタンは絶対に自動クリックしないでください。
NEXT_OR_CONFIRM_BUTTON_SELECTOR = 'button[name="confirm"]'
