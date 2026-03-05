from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

try:
    from .constants import (
        APP_TITLE,
        BASE_FONT,
        BUTTON_FONT,
        CATEGORIES,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        ENTRY_TYPES,
        SMALL_FONT,
    )
    from .service import KakeiboService
except ImportError:  # pragma: no cover
    from constants import (
        APP_TITLE,
        BASE_FONT,
        BUTTON_FONT,
        CATEGORIES,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        ENTRY_TYPES,
        SMALL_FONT,
    )
    from service import KakeiboService


class KakeiboApp:
    def __init__(self, root: tk.Tk, service: KakeiboService) -> None:
        self.root = root
        self.service = service

        self.root.title(APP_TITLE)
        self.root.geometry("980x720")
        self.root.minsize(920, 640)
        self.root.configure(padx=16, pady=16)

        self.date_var = tk.StringVar(value=date.today().strftime(DATE_FORMAT))
        self.type_var = tk.StringVar(value=ENTRY_TYPE_EXPENSE)
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.amount_var = tk.StringVar(value="")
        self.memo_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")

        self.income_var = tk.StringVar(value="収入合計: 0円")
        self.expense_var = tk.StringVar(value="支出合計: 0円")
        self.balance_var = tk.StringVar(value="収支: 0円")

        self._configure_style()
        self._build_layout()
        self.refresh_all()
        self._set_status("準備完了")

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.configure("Treeview", font=BASE_FONT, rowheight=30)
        style.configure("Treeview.Heading", font=SMALL_FONT)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        input_frame = tk.LabelFrame(self.root, text="入力フォーム", font=BASE_FONT, padx=10, pady=10)
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        input_frame.columnconfigure(5, weight=1)

        tk.Label(input_frame, text="日付", font=BASE_FONT).grid(row=0, column=0, sticky="w", padx=(0, 8))
        tk.Entry(input_frame, textvariable=self.date_var, font=BASE_FONT, width=12).grid(
            row=0, column=1, sticky="w"
        )

        tk.Label(input_frame, text="区分", font=BASE_FONT).grid(row=0, column=2, sticky="w", padx=(16, 8))
        type_frame = tk.Frame(input_frame)
        type_frame.grid(row=0, column=3, sticky="w")
        for value, label in ENTRY_TYPES:
            tk.Radiobutton(
                type_frame,
                text=label,
                variable=self.type_var,
                value=value,
                font=BASE_FONT,
            ).pack(side="left", padx=(0, 10))

        tk.Label(input_frame, text="カテゴリ", font=BASE_FONT).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(10, 0))
        category_box = ttk.Combobox(
            input_frame,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=BASE_FONT,
            width=12,
        )
        category_box.grid(row=1, column=1, sticky="w", pady=(10, 0))

        tk.Label(input_frame, text="金額(円)", font=BASE_FONT).grid(row=1, column=2, sticky="w", padx=(16, 8), pady=(10, 0))
        tk.Entry(input_frame, textvariable=self.amount_var, font=BUTTON_FONT, width=12).grid(
            row=1, column=3, sticky="w", pady=(10, 0)
        )

        tk.Label(input_frame, text="メモ", font=BASE_FONT).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(10, 0))
        tk.Entry(input_frame, textvariable=self.memo_var, font=BASE_FONT, width=42).grid(
            row=2, column=1, columnspan=3, sticky="ew", pady=(10, 0)
        )

        tk.Button(
            input_frame,
            text="追加",
            font=BUTTON_FONT,
            width=8,
            command=self.on_add,
        ).grid(row=0, column=4, rowspan=3, padx=(16, 0), sticky="ns")

        list_frame = tk.LabelFrame(self.root, text="明細一覧", font=BASE_FONT, padx=10, pady=10)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("date", "type", "category", "amount", "memo")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree.heading("date", text="日付")
        self.tree.heading("type", text="区分")
        self.tree.heading("category", text="カテゴリ")
        self.tree.heading("amount", text="金額")
        self.tree.heading("memo", text="メモ")

        self.tree.column("date", width=130, anchor="center")
        self.tree.column("type", width=90, anchor="center")
        self.tree.column("category", width=120, anchor="center")
        self.tree.column("amount", width=130, anchor="e")
        self.tree.column("memo", width=420, anchor="w")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        list_action_frame = tk.Frame(list_frame)
        list_action_frame.grid(row=1, column=0, sticky="e", pady=(10, 0))
        tk.Button(
            list_action_frame,
            text="選択行を削除",
            font=BASE_FONT,
            command=self.on_delete,
        ).pack(side="left")

        summary_frame = tk.LabelFrame(self.root, text="月次サマリ", font=BASE_FONT, padx=10, pady=10)
        summary_frame.grid(row=2, column=0, sticky="ew")
        summary_frame.columnconfigure(0, weight=1)

        tk.Label(summary_frame, textvariable=self.income_var, font=BASE_FONT).grid(row=0, column=0, sticky="w")
        tk.Label(summary_frame, textvariable=self.expense_var, font=BASE_FONT).grid(row=1, column=0, sticky="w")
        tk.Label(summary_frame, textvariable=self.balance_var, font=BUTTON_FONT).grid(row=2, column=0, sticky="w")

        tk.Button(
            summary_frame,
            text="CSV出力",
            font=BASE_FONT,
            command=self.on_export_csv,
        ).grid(row=0, column=1, rowspan=3, padx=(12, 0), sticky="ns")

        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=SMALL_FONT,
            anchor="w",
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def _set_status(self, message: str, is_error: bool = False) -> None:
        self.status_var.set(message)
        self.status_label.configure(fg="firebrick" if is_error else "darkgreen")

    @staticmethod
    def _format_amount(amount: int, entry_type: str) -> str:
        sign = "+" if entry_type == ENTRY_TYPE_INCOME else "-"
        return f"{sign}{amount:,}円"

    def refresh_all(self) -> None:
        self.refresh_entries()
        self.refresh_summary()

    def refresh_entries(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for row in self.service.list_entries():
            label = "収入" if row["type"] == ENTRY_TYPE_INCOME else "支出"
            amount_text = self._format_amount(row["amount"], row["type"])
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(row["date"], label, row["category"], amount_text, row["memo"]),
            )

    def refresh_summary(self) -> None:
        summary = self.service.monthly_summary()
        self.income_var.set(f"収入合計: {summary['income_total']:,}円")
        self.expense_var.set(f"支出合計: {summary['expense_total']:,}円")
        self.balance_var.set(f"収支: {summary['balance']:,}円")

    def on_add(self) -> None:
        try:
            self.service.create_entry(
                date_text=self.date_var.get(),
                entry_type=self.type_var.get(),
                category=self.category_var.get(),
                amount_text=self.amount_var.get(),
                memo=self.memo_var.get(),
            )
        except ValueError as exc:
            self._set_status(str(exc), is_error=True)
            messagebox.showerror("入力エラー", str(exc))
            return
        except Exception:
            message = "保存に失敗しました"
            self._set_status(message, is_error=True)
            messagebox.showerror("エラー", message)
            return

        self.amount_var.set("")
        self.memo_var.set("")
        self.refresh_all()
        self._set_status("保存しました")

    def on_delete(self) -> None:
        selected = self.tree.selection()
        if not selected:
            self._set_status("削除する行を選択してください", is_error=True)
            return

        if not messagebox.askyesno("確認", "選択した明細を削除しますか？"):
            return

        entry_id = int(selected[0])
        if not self.service.delete_entry(entry_id):
            self._set_status("削除対象が見つかりませんでした", is_error=True)
            return

        self.refresh_all()
        self._set_status("削除しました")

    def on_export_csv(self) -> None:
        default_name = f"kakeibo_export_{date.today().strftime('%Y%m%d')}.csv"
        output_path = filedialog.asksaveasfilename(
            title="CSV保存先を選択",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")],
        )
        if not output_path:
            self._set_status("CSV出力をキャンセルしました")
            return

        try:
            row_count = self.service.export_csv(output_path)
        except Exception:
            message = "CSVの保存に失敗しました"
            self._set_status(message, is_error=True)
            messagebox.showerror("エラー", message)
            return

        self._set_status(f"CSVを出力しました（{row_count}件）")
