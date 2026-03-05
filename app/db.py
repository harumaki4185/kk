from __future__ import annotations

import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

try:
    from .constants import DB_DIRECTORY_NAME, DB_FILENAME
except ImportError:  # pragma: no cover
    from constants import DB_DIRECTORY_NAME, DB_FILENAME


def resolve_app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or self.default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def default_db_path() -> Path:
        base_dir = resolve_app_base_dir()
        return base_dir / DB_DIRECTORY_NAME / DB_FILENAME

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_db(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            content_category TEXT DEFAULT '',
            amount INTEGER NOT NULL,
            memo TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
        with self.connect() as conn:
            conn.execute(query)
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(entries);").fetchall()
            }
            if "content_category" not in columns:
                conn.execute(
                    "ALTER TABLE entries ADD COLUMN content_category TEXT DEFAULT '';"
                )

    def insert_entry(
        self,
        date_value: str,
        entry_type: str,
        category: str,
        content_category: str,
        amount: int,
        memo: str,
    ) -> None:
        query = """
        INSERT INTO entries (date, type, category, content_category, amount, memo, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        created_at = datetime.now().isoformat(timespec="seconds")
        with self.connect() as conn:
            conn.execute(
                query,
                (
                    date_value,
                    entry_type,
                    category,
                    content_category,
                    amount,
                    memo,
                    created_at,
                ),
            )

    def update_entry(
        self,
        entry_id: int,
        date_value: str,
        entry_type: str,
        category: str,
        content_category: str,
        amount: int,
        memo: str,
    ) -> bool:
        query = """
        UPDATE entries
        SET date = ?, type = ?, category = ?, content_category = ?, amount = ?, memo = ?
        WHERE id = ?;
        """
        with self.connect() as conn:
            cursor = conn.execute(
                query,
                (
                    date_value,
                    entry_type,
                    category,
                    content_category,
                    amount,
                    memo,
                    entry_id,
                ),
            )
            return cursor.rowcount > 0

    def fetch_entries(
        self,
        date_filter: str | None = None,
        year_month_filter: str | None = None,
    ) -> list[dict]:
        query = """
        SELECT id, date, type, category, content_category, amount, memo, created_at
        FROM entries
        """
        where_clauses: list[str] = []
        params_list: list[str] = []
        if date_filter:
            where_clauses.append("date = ?")
            params_list.append(date_filter)
        if year_month_filter:
            where_clauses.append("substr(date, 1, 7) = ?")
            params_list.append(year_month_filter)

        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses) + "\n"

        params = tuple(params_list)
        query += "ORDER BY date DESC, id DESC;"

        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def delete_entry(self, entry_id: int) -> bool:
        query = "DELETE FROM entries WHERE id = ?;"
        with self.connect() as conn:
            cursor = conn.execute(query, (entry_id,))
            return cursor.rowcount > 0

    def fetch_month_totals(self, year_month: str) -> dict:
        query = """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income_total,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expense_total
        FROM entries
        WHERE substr(date, 1, 7) = ?;
        """
        with self.connect() as conn:
            row = conn.execute(query, (year_month,)).fetchone()
        return {
            "income_total": int(row["income_total"]),
            "expense_total": int(row["expense_total"]),
        }

    def fetch_daily_totals(self, year_month: str) -> list[dict]:
        query = """
        SELECT
            date,
            COUNT(*) AS entry_count,
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income_total,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expense_total
        FROM entries
        WHERE substr(date, 1, 7) = ?
        GROUP BY date
        ORDER BY date ASC;
        """
        with self.connect() as conn:
            rows = conn.execute(query, (year_month,)).fetchall()
        return [dict(row) for row in rows]

    def fetch_all_entries_for_export(self) -> list[dict]:
        query = """
        SELECT id, date, type, category, content_category, amount, memo, created_at
        FROM entries
        ORDER BY date ASC, id ASC;
        """
        with self.connect() as conn:
            rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]
