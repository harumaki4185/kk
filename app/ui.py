from __future__ import annotations

import calendar
import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

try:
    from .constants import (
        AMOUNT_FONT,
        APP_TITLE,
        BASE_FONT,
        BG_FRAME,
        BG_INPUT,
        BG_MAIN,
        BG_SOFT_YELLOW,
        BUTTON_FONT,
        CATEGORIES,
        COLOR_ADD_BTN,
        COLOR_ADD_BTN_ACTIVE,
        COLOR_ADD_BTN_FG,
        COLOR_CALENDAR_ACTIVE_BG,
        COLOR_CALENDAR_CELL_BG,
        COLOR_CALENDAR_EMPTY_BG,
        COLOR_CALENDAR_NEGATIVE_BG,
        COLOR_CALENDAR_POSITIVE_BG,
        COLOR_CALENDAR_SAT_BG,
        COLOR_CALENDAR_SELECTED_BG,
        COLOR_CALENDAR_SUN_BG,
        COLOR_CSV_BTN,
        COLOR_CSV_BTN_ACTIVE,
        COLOR_CSV_BTN_FG,
        COLOR_DEL_BTN,
        COLOR_DEL_BTN_ACTIVE,
        COLOR_DEL_BTN_FG,
        COLOR_EXPENSE,
        COLOR_EXPENSE_BG,
        COLOR_INCOME,
        COLOR_INCOME_BG,
        COLOR_STATUS_ERR,
        COLOR_STATUS_ERR_BG,
        COLOR_STATUS_OK,
        COLOR_STATUS_OK_BG,
        COLOR_TEXT_PRIMARY,
        COLOR_TREE_SELECTED_BG,
        COLOR_TREE_SELECTED_FG,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        ENTRY_TYPES,
        HEADING_FONT,
        SMALL_FONT,
        SUMMARY_FONT,
    )
    from .service import KakeiboService
except ImportError:  # pragma: no cover
    from constants import (
        AMOUNT_FONT,
        APP_TITLE,
        BASE_FONT,
        BG_FRAME,
        BG_INPUT,
        BG_MAIN,
        BG_SOFT_YELLOW,
        BUTTON_FONT,
        CATEGORIES,
        COLOR_ADD_BTN,
        COLOR_ADD_BTN_ACTIVE,
        COLOR_ADD_BTN_FG,
        COLOR_CALENDAR_ACTIVE_BG,
        COLOR_CALENDAR_CELL_BG,
        COLOR_CALENDAR_EMPTY_BG,
        COLOR_CALENDAR_NEGATIVE_BG,
        COLOR_CALENDAR_POSITIVE_BG,
        COLOR_CALENDAR_SAT_BG,
        COLOR_CALENDAR_SELECTED_BG,
        COLOR_CALENDAR_SUN_BG,
        COLOR_CSV_BTN,
        COLOR_CSV_BTN_ACTIVE,
        COLOR_CSV_BTN_FG,
        COLOR_DEL_BTN,
        COLOR_DEL_BTN_ACTIVE,
        COLOR_DEL_BTN_FG,
        COLOR_EXPENSE,
        COLOR_EXPENSE_BG,
        COLOR_INCOME,
        COLOR_INCOME_BG,
        COLOR_STATUS_ERR,
        COLOR_STATUS_ERR_BG,
        COLOR_STATUS_OK,
        COLOR_STATUS_OK_BG,
        COLOR_TEXT_PRIMARY,
        COLOR_TREE_SELECTED_BG,
        COLOR_TREE_SELECTED_FG,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        ENTRY_TYPES,
        HEADING_FONT,
        SMALL_FONT,
        SUMMARY_FONT,
    )
    from service import KakeiboService


WEEKDAY_LABELS = ("月", "火", "水", "木", "金", "土", "日")


class KakeiboApp:
    def __init__(self, root: tk.Tk, service: KakeiboService) -> None:
        self.root = root
        self.service = service

        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        self.selected_date_filter: str | None = None

        self.root.title(APP_TITLE)
        self.root.geometry("1400x900")
        self.root.minsize(1200, 780)
        self.root.configure(bg=BG_MAIN, padx=20, pady=20)

        self.date_var = tk.StringVar(value=today.strftime(DATE_FORMAT))
        self.type_var = tk.StringVar(value=ENTRY_TYPE_EXPENSE)
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.amount_var = tk.StringVar(value="")
        self.memo_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.calendar_title_var = tk.StringVar(value="")
        self.list_title_var = tk.StringVar(value="明細一覧（全期間）")

        self.income_var = tk.StringVar(value="収入合計: 0 円")
        self.expense_var = tk.StringVar(value="支出合計: 0 円")
        self.balance_var = tk.StringVar(value="収支: 0 円")

        self.calendar_buttons: list[tk.Button] = []

        self._configure_style()
        self._build_layout()
        self.refresh_all()
        self._set_status("準備できました。入力してみてください。")

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            font=BASE_FONT,
            rowheight=42,
            background=BG_INPUT,
            fieldbackground=BG_INPUT,
        )
        style.configure("Treeview.Heading", font=HEADING_FONT, padding=6)
        style.map(
            "Treeview",
            background=[("selected", COLOR_TREE_SELECTED_BG)],
            foreground=[("selected", COLOR_TREE_SELECTED_FG)],
        )
        style.configure("TCombobox", padding=6)

    def _build_layout(self) -> None:
        # Two-column layout: calendar (left) | input+list+summary (right)
        self.root.columnconfigure(0, weight=0)  # calendar column - fixed
        self.root.columnconfigure(1, weight=1)  # right column - expandable
        self.root.rowconfigure(0, weight=1)      # main content row

        # --- Left column: Calendar ---
        self._build_calendar_frame()

        # --- Right column: stacked frames ---
        right_frame = tk.Frame(self.root, bg=BG_MAIN)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)  # list frame expands
        self.right_frame = right_frame

        self._build_input_frame()
        self._build_list_frame()
        self._build_summary_frame()
        self._build_status_bar()

    def _build_input_frame(self) -> None:
        frame = tk.LabelFrame(
            self.right_frame,
            text="入力フォーム",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=18,
            pady=14,
        )
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        frame.columnconfigure(5, weight=1)

        tk.Label(frame, text="日付", font=BASE_FONT, bg=BG_FRAME).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )
        tk.Entry(
            frame,
            textvariable=self.date_var,
            font=BASE_FONT,
            width=13,
            bg=BG_INPUT,
            relief="solid",
            bd=1,
        ).grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(frame, text="区分", font=BASE_FONT, bg=BG_FRAME).grid(
            row=0, column=2, sticky="w", padx=(24, 8), pady=4
        )
        type_frame = tk.Frame(frame, bg=BG_FRAME)
        type_frame.grid(row=0, column=3, sticky="w", pady=4)
        for value, label in ENTRY_TYPES:
            color = COLOR_EXPENSE if value == ENTRY_TYPE_EXPENSE else COLOR_INCOME
            tk.Radiobutton(
                type_frame,
                text=label,
                variable=self.type_var,
                value=value,
                font=HEADING_FONT,
                fg=color,
                bg=BG_FRAME,
                activebackground=BG_FRAME,
                selectcolor=BG_FRAME,
                indicatoron=True,
            ).pack(side="left", padx=(0, 16))

        tk.Label(frame, text="カテゴリ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=8
        )
        ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=BASE_FONT,
            width=10,
        ).grid(row=1, column=1, sticky="w", pady=8)

        tk.Label(frame, text="金額（円）", font=BASE_FONT, bg=BG_FRAME).grid(
            row=1, column=2, sticky="w", padx=(24, 8), pady=8
        )
        tk.Entry(
            frame,
            textvariable=self.amount_var,
            font=AMOUNT_FONT,
            width=12,
            bg=BG_SOFT_YELLOW,
            relief="solid",
            bd=2,
            fg=COLOR_TEXT_PRIMARY,
        ).grid(row=1, column=3, sticky="w", pady=8)

        tk.Label(frame, text="メモ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=8
        )
        tk.Entry(
            frame,
            textvariable=self.memo_var,
            font=BASE_FONT,
            width=38,
            bg=BG_INPUT,
            relief="solid",
            bd=1,
        ).grid(row=2, column=1, columnspan=3, sticky="ew", pady=8)

        tk.Button(
            frame,
            text="追加する",
            font=BUTTON_FONT,
            bg=COLOR_ADD_BTN,
            fg=COLOR_ADD_BTN_FG,
            activebackground=COLOR_ADD_BTN_ACTIVE,
            activeforeground=COLOR_ADD_BTN_FG,
            relief="raised",
            bd=2,
            width=10,
            cursor="hand2",
            command=self.on_add,
        ).grid(row=0, column=4, rowspan=3, padx=(20, 0), sticky="ns")

    def _build_calendar_frame(self) -> None:
        frame = tk.LabelFrame(
            self.root,
            text="カレンダー（日別収支）",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=14,
            pady=10,
        )
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)  # calendar grid expands vertically

        header_frame = tk.Frame(frame, bg=BG_FRAME)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header_frame.columnconfigure(1, weight=1)

        tk.Button(
            header_frame,
            text="前月",
            font=BASE_FONT,
            bg=COLOR_CSV_BTN,
            fg=COLOR_CSV_BTN_FG,
            activebackground=COLOR_CSV_BTN_ACTIVE,
            activeforeground=COLOR_CSV_BTN_FG,
            cursor="hand2",
            command=lambda: self._change_month(-1),
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            header_frame,
            textvariable=self.calendar_title_var,
            font=HEADING_FONT,
            bg=BG_FRAME,
            fg=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="n")

        tk.Button(
            header_frame,
            text="次月",
            font=BASE_FONT,
            bg=COLOR_CSV_BTN,
            fg=COLOR_CSV_BTN_FG,
            activebackground=COLOR_CSV_BTN_ACTIVE,
            activeforeground=COLOR_CSV_BTN_FG,
            cursor="hand2",
            command=lambda: self._change_month(1),
        ).grid(row=0, column=2, sticky="e", padx=(8, 0))

        tk.Button(
            header_frame,
            text="全期間表示",
            font=SMALL_FONT,
            bg=BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_TREE_SELECTED_BG,
            activeforeground=COLOR_TEXT_PRIMARY,
            cursor="hand2",
            command=self.on_clear_date_filter,
        ).grid(row=0, column=3, sticky="e", padx=(8, 0))

        weekday_frame = tk.Frame(frame, bg=BG_FRAME)
        weekday_frame.grid(row=1, column=0, sticky="ew")
        for col, weekday in enumerate(WEEKDAY_LABELS):
            weekday_color = COLOR_TEXT_PRIMARY
            if col == 5:
                weekday_color = COLOR_INCOME
            if col == 6:
                weekday_color = COLOR_EXPENSE
            tk.Label(
                weekday_frame,
                text=weekday,
                font=BASE_FONT,
                bg=BG_FRAME,
                fg=weekday_color,
            ).grid(row=0, column=col, sticky="nsew")
            weekday_frame.columnconfigure(col, weight=1)

        self.calendar_grid_frame = tk.Frame(frame, bg=BG_FRAME)
        self.calendar_grid_frame.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        for row in range(6):
            self.calendar_grid_frame.rowconfigure(row, weight=1)
            for col in range(7):
                self.calendar_grid_frame.columnconfigure(col, weight=1)
                button = tk.Button(
                    self.calendar_grid_frame,
                    text="",
                    font=SMALL_FONT,
                    width=8,
                    height=2,
                    justify="center",
                    relief="groove",
                    bg=COLOR_CALENDAR_CELL_BG,
                    fg=COLOR_TEXT_PRIMARY,
                    activebackground=COLOR_CALENDAR_ACTIVE_BG,
                    activeforeground=COLOR_TEXT_PRIMARY,
                    cursor="hand2",
                )
                button.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
                self.calendar_buttons.append(button)

    def _build_list_frame(self) -> None:
        frame = tk.LabelFrame(
            self.right_frame,
            text="明細一覧",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=14,
            pady=10,
        )
        frame.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        tk.Label(
            frame,
            textvariable=self.list_title_var,
            font=BASE_FONT,
            bg=BG_FRAME,
            fg=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        columns = ("date", "type", "category", "amount", "memo")
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=1, column=0, sticky="nsew")

        self.tree.heading("date", text="日付")
        self.tree.heading("type", text="区分")
        self.tree.heading("category", text="カテゴリ")
        self.tree.heading("amount", text="金額")
        self.tree.heading("memo", text="メモ")

        self.tree.column("date", width=140, anchor="center")
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("category", width=130, anchor="center")
        self.tree.column("amount", width=150, anchor="e")
        self.tree.column("memo", width=400, anchor="w")

        self.tree.tag_configure("income", background=COLOR_INCOME_BG, foreground=COLOR_INCOME)
        self.tree.tag_configure("expense", background=COLOR_EXPENSE_BG, foreground=COLOR_EXPENSE)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        action_frame = tk.Frame(frame, bg=BG_FRAME)
        action_frame.grid(row=2, column=0, sticky="e", pady=(12, 0))
        tk.Button(
            action_frame,
            text="選択行を削除",
            font=BASE_FONT,
            bg=COLOR_DEL_BTN,
            fg=COLOR_DEL_BTN_FG,
            activebackground=COLOR_DEL_BTN_ACTIVE,
            activeforeground=COLOR_DEL_BTN_FG,
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.on_delete,
        ).pack(side="left")

    def _build_summary_frame(self) -> None:
        frame = tk.LabelFrame(
            self.right_frame,
            text="月次サマリ",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=18,
            pady=14,
        )
        frame.grid(row=2, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)

        tk.Label(
            frame,
            textvariable=self.income_var,
            font=HEADING_FONT,
            bg=BG_FRAME,
            fg=COLOR_INCOME,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=2)

        tk.Label(
            frame,
            textvariable=self.expense_var,
            font=HEADING_FONT,
            bg=BG_FRAME,
            fg=COLOR_EXPENSE,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=2)

        tk.Label(
            frame,
            textvariable=self.balance_var,
            font=SUMMARY_FONT,
            bg=BG_FRAME,
            fg=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(6, 2))

        tk.Button(
            frame,
            text="CSV出力",
            font=BUTTON_FONT,
            bg=COLOR_CSV_BTN,
            fg=COLOR_CSV_BTN_FG,
            activebackground=COLOR_CSV_BTN_ACTIVE,
            activeforeground=COLOR_CSV_BTN_FG,
            relief="raised",
            bd=2,
            width=12,
            cursor="hand2",
            command=self.on_export_csv,
        ).grid(row=0, column=1, rowspan=3, padx=(20, 0), sticky="ns")

    def _build_status_bar(self) -> None:
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=SMALL_FONT,
            bg=BG_MAIN,
            anchor="w",
            pady=6,
        )
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _set_status(self, message: str, is_error: bool = False) -> None:
        self.status_var.set(message)
        if is_error:
            self.status_label.configure(fg=COLOR_STATUS_ERR, bg=COLOR_STATUS_ERR_BG)
        else:
            self.status_label.configure(fg=COLOR_STATUS_OK, bg=COLOR_STATUS_OK_BG)

    @staticmethod
    def _format_amount(amount: int, entry_type: str) -> str:
        sign = "＋" if entry_type == ENTRY_TYPE_INCOME else "－"
        return f"{sign}{amount:,} 円"

    @staticmethod
    def _month_title(year: int, month: int) -> str:
        return f"{year}年{month}月"

    @staticmethod
    def _change_year_month(year: int, month: int, diff: int) -> tuple[int, int]:
        month_index = year * 12 + (month - 1) + diff
        next_year = month_index // 12
        next_month = month_index % 12 + 1
        return next_year, next_month

    def _change_month(self, diff: int) -> None:
        self.calendar_year, self.calendar_month = self._change_year_month(
            self.calendar_year,
            self.calendar_month,
            diff,
        )
        if self.selected_date_filter and not self.selected_date_filter.startswith(
            f"{self.calendar_year:04d}-{self.calendar_month:02d}"
        ):
            self.selected_date_filter = None
        self.refresh_all()
        self._set_status(f"{self._month_title(self.calendar_year, self.calendar_month)}を表示しています")

    def _calendar_cell_style(
        self,
        col: int,
        selected: bool,
        has_data: bool,
        balance: int,
    ) -> tuple[str, str]:
        if selected:
            return COLOR_CALENDAR_SELECTED_BG, COLOR_TEXT_PRIMARY
        if col == 6:
            return COLOR_CALENDAR_SUN_BG, COLOR_EXPENSE
        if col == 5:
            return COLOR_CALENDAR_SAT_BG, COLOR_INCOME
        if has_data and balance > 0:
            return COLOR_CALENDAR_POSITIVE_BG, COLOR_STATUS_OK
        if has_data and balance < 0:
            return COLOR_CALENDAR_NEGATIVE_BG, COLOR_STATUS_ERR
        return COLOR_CALENDAR_CELL_BG, COLOR_TEXT_PRIMARY

    def refresh_all(self) -> None:
        self.refresh_calendar()
        self.refresh_entries()
        self.refresh_summary()

    def refresh_calendar(self) -> None:
        self.calendar_title_var.set(self._month_title(self.calendar_year, self.calendar_month))

        month_key = f"{self.calendar_year:04d}-{self.calendar_month:02d}"
        totals = self.service.daily_totals(self.calendar_year, self.calendar_month)
        month_days = calendar.monthcalendar(self.calendar_year, self.calendar_month)
        flat_days = [day for week in month_days for day in week]
        while len(flat_days) < len(self.calendar_buttons):
            flat_days.append(0)

        for idx, day in enumerate(flat_days[: len(self.calendar_buttons)]):
            button = self.calendar_buttons[idx]
            col = idx % 7
            if day == 0:
                button.configure(
                    text="",
                    state="disabled",
                    command=lambda: None,
                    bg=COLOR_CALENDAR_EMPTY_BG,
                    fg=COLOR_TEXT_PRIMARY,
                )
                continue

            date_text = f"{month_key}-{day:02d}"
            daily = totals.get(date_text)
            if daily:
                balance = int(daily["balance"])
                count = int(daily["entry_count"])
                sign = "+" if balance >= 0 else "-"
                amount_text = f"{sign}{abs(balance):,}"
                cell_text = f"{day}\n{amount_text}円 ({count})"
            else:
                balance = 0
                cell_text = f"{day}\n-"

            bg, fg = self._calendar_cell_style(
                col=col,
                selected=self.selected_date_filter == date_text,
                has_data=daily is not None,
                balance=balance,
            )
            button.configure(
                text=cell_text,
                state="normal",
                command=lambda d=date_text: self.on_select_calendar_date(d),
                bg=bg,
                fg=fg,
                activebackground=COLOR_CALENDAR_ACTIVE_BG,
                activeforeground=COLOR_TEXT_PRIMARY,
            )

    def refresh_entries(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        if self.selected_date_filter:
            self.list_title_var.set(f"明細一覧（{self.selected_date_filter}）")
        else:
            self.list_title_var.set("明細一覧（全期間）")

        for row in self.service.list_entries(date_filter=self.selected_date_filter):
            label = "収入" if row["type"] == ENTRY_TYPE_INCOME else "支出"
            amount_text = self._format_amount(row["amount"], row["type"])
            tag = "income" if row["type"] == ENTRY_TYPE_INCOME else "expense"
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(row["date"], label, row["category"], amount_text, row["memo"]),
                tags=(tag,),
            )

    def refresh_summary(self) -> None:
        summary = self.service.monthly_summary(self.calendar_year, self.calendar_month)
        title = self._month_title(summary["year"], summary["month"])
        self.income_var.set(f"{title} 収入合計: {summary['income_total']:,} 円")
        self.expense_var.set(f"{title} 支出合計: {summary['expense_total']:,} 円")
        self.balance_var.set(f"{title} 収支: {summary['balance']:,} 円")

    def on_select_calendar_date(self, date_text: str) -> None:
        self.selected_date_filter = date_text
        self.date_var.set(date_text)
        self.refresh_calendar()
        self.refresh_entries()
        self._set_status(f"{date_text} の明細を表示しています")

    def on_clear_date_filter(self) -> None:
        self.selected_date_filter = None
        self.refresh_calendar()
        self.refresh_entries()
        self._set_status("全期間の明細を表示しています")

    def on_add(self) -> None:
        input_date = self.date_var.get()
        try:
            self.service.create_entry(
                date_text=input_date,
                entry_type=self.type_var.get(),
                category=self.category_var.get(),
                amount_text=self.amount_var.get(),
                memo=self.memo_var.get(),
            )
        except ValueError as exc:
            self._set_status(str(exc), is_error=True)
            messagebox.showerror("入力エラー", str(exc))
            return
        except (sqlite3.Error, OSError):
            message = "保存に失敗しました"
            self._set_status(message, is_error=True)
            messagebox.showerror("エラー", message)
            return

        try:
            created = datetime.strptime(input_date.strip(), DATE_FORMAT)
            created_date = created.strftime(DATE_FORMAT)
            self.calendar_year = created.year
            self.calendar_month = created.month
            self.selected_date_filter = created_date
        except ValueError:
            self.selected_date_filter = None

        self.amount_var.set("")
        self.memo_var.set("")
        self.refresh_all()
        self._set_status("保存しました")

    def on_delete(self) -> None:
        selected = self.tree.selection()
        if not selected:
            self._set_status("削除したい行を選択してください", is_error=True)
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
        except (sqlite3.Error, OSError):
            message = "CSVの保存に失敗しました"
            self._set_status(message, is_error=True)
            messagebox.showerror("エラー", message)
            return

        self._set_status(f"CSVを出力しました（{row_count}件）")
