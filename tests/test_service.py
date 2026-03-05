from __future__ import annotations

import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.db import Database
from app.service import KakeiboService


class KakeiboServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        self.database = Database(db_path)
        self.database.init_db()
        self.service = KakeiboService(self.database)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_entry_and_monthly_summary(self) -> None:
        self.service.create_entry("2026-03-01", "income", "その他", "50000", "年金")
        self.service.create_entry("2026-03-02", "expense", "食費", "1200", "パン")

        summary = self.service.monthly_summary(2026, 3)
        self.assertEqual(summary["income_total"], 50000)
        self.assertEqual(summary["expense_total"], 1200)
        self.assertEqual(summary["balance"], 48800)

    def test_invalid_amount(self) -> None:
        with self.assertRaisesRegex(ValueError, "金額は数字で入力してください"):
            self.service.create_entry("2026-03-01", "expense", "食費", "12a", "")

    def test_fullwidth_amount_is_accepted(self) -> None:
        self.service.create_entry("2026-03-01", "expense", "食費", "１,２３４", "")
        summary = self.service.monthly_summary(2026, 3)
        self.assertEqual(summary["expense_total"], 1234)

    def test_invalid_date_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "日付は YYYY-MM-DD 形式で入力してください"):
            self.service.create_entry("2026/03/01", "expense", "食費", "1200", "")

    def test_invalid_date_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "日付が正しくありません"):
            self.service.create_entry("2026-02-30", "expense", "食費", "1200", "")

    def test_invalid_entry_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "区分の値が不正です"):
            self.service.create_entry("2026-03-01", "transfer", "食費", "1200", "")

    def test_invalid_category(self) -> None:
        with self.assertRaisesRegex(ValueError, "カテゴリを選択してください"):
            self.service.create_entry("2026-03-01", "expense", "娯楽", "1200", "")

    def test_too_long_memo(self) -> None:
        with self.assertRaisesRegex(ValueError, "メモは 100 文字以内で入力してください"):
            self.service.create_entry("2026-03-01", "expense", "食費", "1200", "a" * 101)

    def test_export_csv(self) -> None:
        self.service.create_entry("2026-03-01", "expense", "日用品", "2400", "洗剤")
        output_path = Path(self.temp_dir.name) / "out.csv"

        row_count = self.service.export_csv(output_path)

        self.assertEqual(row_count, 1)
        with output_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            rows = list(csv.reader(csv_file))

        self.assertEqual(rows[0][0], "id")
        self.assertEqual(rows[1][1], "2026-03-01")
        self.assertEqual(rows[1][2], "支出")
        self.assertEqual(rows[1][4], "2400")

    def test_list_entries_with_date_filter(self) -> None:
        self.service.create_entry("2026-03-01", "expense", "食費", "1000", "")
        self.service.create_entry("2026-03-02", "expense", "食費", "2000", "")

        rows = self.service.list_entries(date_filter="2026-03-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date"], "2026-03-01")
        self.assertEqual(rows[0]["amount"], 1000)

    def test_daily_totals(self) -> None:
        self.service.create_entry("2026-03-01", "income", "その他", "5000", "")
        self.service.create_entry("2026-03-01", "expense", "食費", "1500", "")
        self.service.create_entry("2026-03-02", "expense", "日用品", "500", "")

        totals = self.service.daily_totals(2026, 3)
        self.assertEqual(totals["2026-03-01"]["entry_count"], 2)
        self.assertEqual(totals["2026-03-01"]["income_total"], 5000)
        self.assertEqual(totals["2026-03-01"]["expense_total"], 1500)
        self.assertEqual(totals["2026-03-01"]["balance"], 3500)
        self.assertEqual(totals["2026-03-02"]["balance"], -500)

    def test_delete_entry_returns_false_for_missing_id(self) -> None:
        self.assertFalse(self.database.delete_entry(999999))

    def test_connect_rolls_back_on_error(self) -> None:
        with self.assertRaises(sqlite3.OperationalError):
            with self.database.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO entries (date, type, category, amount, memo, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    ("2026-03-05", "expense", "食費", 1200, "", "2026-03-05T10:00:00"),
                )
                conn.execute("INSERT INTO entries (unknown_column) VALUES (1)")

        rows = self.database.fetch_entries(date_filter="2026-03-05")
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
