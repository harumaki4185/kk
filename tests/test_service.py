from __future__ import annotations

import csv
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


if __name__ == "__main__":
    unittest.main()
