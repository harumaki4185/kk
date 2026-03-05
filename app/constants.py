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

BASE_FONT = ("Yu Gothic UI", 14)
BUTTON_FONT = ("Yu Gothic UI", 16, "bold")
SMALL_FONT = ("Yu Gothic UI", 12)
