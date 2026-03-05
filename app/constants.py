APP_TITLE = "かんたん家計簿"
DATE_FORMAT = "%Y-%m-%d"

ENTRY_TYPE_EXPENSE = "expense"
ENTRY_TYPE_INCOME = "income"
ENTRY_TYPES = (
    (ENTRY_TYPE_EXPENSE, "支出"),
    (ENTRY_TYPE_INCOME, "収入"),
)

CATEGORIES = (
    "食費",
    "日用品",
    "医療",
    "光熱費",
    "交通",
    "その他",
)

MAX_MEMO_LENGTH = 100
DB_DIRECTORY_NAME = "data"
DB_FILENAME = "kakeibo.db"

# ---------- Fonts ----------
FONT_FAMILY = "Yu Gothic UI"
BASE_FONT = (FONT_FAMILY, 16)
HEADING_FONT = (FONT_FAMILY, 18, "bold")
BUTTON_FONT = (FONT_FAMILY, 18, "bold")
AMOUNT_FONT = (FONT_FAMILY, 20, "bold")
SMALL_FONT = (FONT_FAMILY, 14)
SUMMARY_FONT = (FONT_FAMILY, 22, "bold")

# ---------- Colors ----------
# 全体背景 – 温かみのあるクリーム系
BG_MAIN = "#FFF8F0"
BG_FRAME = "#FFF3E6"
BG_INPUT = "#FFFFFF"

# 収入 / 支出の識別色
COLOR_INCOME = "#2678C9"       # 落ち着いた青
COLOR_EXPENSE = "#D94040"      # 落ち着いた赤
COLOR_INCOME_BG = "#E8F2FC"    # 収入行の背景
COLOR_EXPENSE_BG = "#FDEDED"   # 支出行の背景

# ボタン配色
COLOR_ADD_BTN = "#3BA55D"      # 追加 – 安心感のある緑
COLOR_ADD_BTN_FG = "#FFFFFF"
COLOR_DEL_BTN = "#D94040"      # 削除 – 赤
COLOR_DEL_BTN_FG = "#FFFFFF"
COLOR_CSV_BTN = "#5B6EAE"      # CSV出力 – 落ち着いた紫系青
COLOR_CSV_BTN_FG = "#FFFFFF"

# ステータスバー
COLOR_STATUS_OK = "#2E7D32"
COLOR_STATUS_ERR = "#C62828"
