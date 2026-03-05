from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

try:
    from .constants import (
        CATEGORIES,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        MAX_MEMO_LENGTH,
    )
    from .db import Database
except ImportError:  # pragma: no cover
    from constants import (
        CATEGORIES,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        MAX_MEMO_LENGTH,
    )
    from db import Database


def validate_date(date_text: str) -> str:
    try:
        parsed = datetime.strptime(date_text, DATE_FORMAT)
    except ValueError as exc:
        raise ValueError("日付は YYYY-MM-DD 形式で入力してください") from exc
    return parsed.strftime(DATE_FORMAT)


def validate_entry_type(entry_type: str) -> str:
    if entry_type not in {ENTRY_TYPE_INCOME, ENTRY_TYPE_EXPENSE}:
        raise ValueError("区分の値が不正です")
    return entry_type


def validate_category(category: str) -> str:
    if category not in CATEGORIES:
        raise ValueError("カテゴリを選択してください")
    return category


def validate_amount(amount_text: str) -> int:
    normalized = amount_text.replace(",", "").strip()
    if not normalized.isdigit():
        raise ValueError("金額は数字で入力してください")
    amount = int(normalized)
    if amount < 1:
        raise ValueError("金額は1円以上で入力してください")
    return amount


def validate_memo(memo: str) -> str:
    text = memo.strip()
    if len(text) > MAX_MEMO_LENGTH:
        raise ValueError(f"メモは {MAX_MEMO_LENGTH} 文字以内で入力してください")
    return text


class KakeiboService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_entry(
        self,
        date_text: str,
        entry_type: str,
        category: str,
        amount_text: str,
        memo: str,
    ) -> str:
        date_value = validate_date(date_text)
        type_value = validate_entry_type(entry_type)
        category_value = validate_category(category)
        amount_value = validate_amount(amount_text)
        memo_value = validate_memo(memo)
        self.database.insert_entry(date_value, type_value, category_value, amount_value, memo_value)
        return date_value

    def list_entries(self, date_filter: str | None = None) -> list[dict]:
        return self.database.fetch_entries(date_filter=date_filter)

    def delete_entry(self, entry_id: int) -> bool:
        return self.database.delete_entry(entry_id)

    def monthly_summary(self, year: int | None = None, month: int | None = None) -> dict:
        today = date.today()
        summary_year = year or today.year
        summary_month = month or today.month
        year_month = f"{summary_year:04d}-{summary_month:02d}"
        totals = self.database.fetch_month_totals(year_month)
        income_total = totals["income_total"]
        expense_total = totals["expense_total"]
        return {
            "year": summary_year,
            "month": summary_month,
            "income_total": income_total,
            "expense_total": expense_total,
            "balance": income_total - expense_total,
        }

    def daily_totals(self, year: int, month: int) -> dict[str, dict]:
        year_month = f"{year:04d}-{month:02d}"
        rows = self.database.fetch_daily_totals(year_month)
        results: dict[str, dict] = {}
        for row in rows:
            income_total = int(row["income_total"])
            expense_total = int(row["expense_total"])
            results[row["date"]] = {
                "entry_count": int(row["entry_count"]),
                "income_total": income_total,
                "expense_total": expense_total,
                "balance": income_total - expense_total,
            }
        return results

    def export_csv(self, output_path: str | Path) -> int:
        rows = self.database.fetch_all_entries_for_export()
        path = Path(output_path)
        with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["id", "日付", "区分", "カテゴリ", "金額", "メモ", "作成日時"])
            for row in rows:
                writer.writerow(
                    [
                        row["id"],
                        row["date"],
                        "収入" if row["type"] == ENTRY_TYPE_INCOME else "支出",
                        row["category"],
                        row["amount"],
                        row["memo"],
                        row["created_at"],
                    ]
                )
        return len(rows)
