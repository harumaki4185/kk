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
VIEW_CALENDAR = "calendar"
VIEW_LIST = "list"


class KakeiboApp:
    def __init__(self, root: tk.Tk, service: KakeiboService) -> None:
        self.root = root
        self.service = service

        today = date.today()
        self.calendar_year = today.year
        self.calendar_month = today.month
        self.selected_date_filter: str | None = None
        self.current_view = VIEW_CALENDAR

        self.root.title(APP_TITLE)
        self.root.geometry("1450x920")
        self.root.minsize(1120, 760)
        self.root.configure(bg=BG_MAIN, padx=20, pady=20)
        self._set_default_window_state()

        self.date_var = tk.StringVar(value=today.strftime(DATE_FORMAT))
        self.type_var = tk.StringVar(value=ENTRY_TYPE_EXPENSE)
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.content_category_var = tk.StringVar(value="")
        self.amount_var = tk.StringVar(value="")
        self.memo_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")
        self.calendar_title_var = tk.StringVar(value="")
        self.list_title_var = tk.StringVar(value="明細一覧")

        self.income_var = tk.StringVar(value="収入合計: 0 円")
        self.expense_var = tk.StringVar(value="支出合計: 0 円")
        self.balance_var = tk.StringVar(value="収支: 0 円")

        self.calendar_buttons: list[tk.Button] = []
        self.entries_by_id: dict[int, dict] = {}
        self.current_entry_id: int | None = None

        self._configure_style()
        self._build_layout()
        self.refresh_all()
        self.show_view(VIEW_CALENDAR)
        self._set_status("準備できました。入力してみてください。")

    def _set_default_window_state(self) -> None:
        try:
            self.root.state("zoomed")
            return
        except tk.TclError:
            pass
        try:
            self.root.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass
        self.root.geometry(
            f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0"
        )

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
        self.root.columnconfigure(0, weight=3, minsize=680)
        self.root.columnconfigure(1, weight=2, minsize=420)
        self.root.rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()
        self._build_status_bar()

    def _build_left_panel(self) -> None:
        left_panel = tk.Frame(self.root, bg=BG_MAIN)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)

        switch_frame = tk.Frame(left_panel, bg=BG_MAIN)
        switch_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        switch_frame.columnconfigure(0, weight=1)
        switch_frame.columnconfigure(1, weight=1)

        self.calendar_view_btn = tk.Button(
            switch_frame,
            text="カレンダー",
            font=HEADING_FONT,
            bg=COLOR_CSV_BTN,
            fg=COLOR_CSV_BTN_FG,
            activebackground=COLOR_CSV_BTN_ACTIVE,
            activeforeground=COLOR_CSV_BTN_FG,
            cursor="hand2",
            command=lambda: self.show_view(VIEW_CALENDAR),
        )
        self.calendar_view_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.list_view_btn = tk.Button(
            switch_frame,
            text="明細一覧",
            font=HEADING_FONT,
            bg=BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_TREE_SELECTED_BG,
            activeforeground=COLOR_TEXT_PRIMARY,
            cursor="hand2",
            command=lambda: self.show_view(VIEW_LIST),
        )
        self.list_view_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.left_content = tk.Frame(left_panel, bg=BG_MAIN)
        self.left_content.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.left_content.rowconfigure(0, weight=1)
        self.left_content.columnconfigure(0, weight=1)

        self._build_calendar_page()
        self._build_list_page()

    def _build_calendar_page(self) -> None:
        frame = tk.LabelFrame(
            self.left_content,
            text="カレンダー（日別収支）",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=14,
            pady=10,
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        self.calendar_page = frame

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
            text="選択解除",
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
                    width=9,
                    height=3,
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

        tk.Label(
            frame,
            text="※ 日付をクリックすると明細一覧に切り替わります",
            font=SMALL_FONT,
            bg=BG_FRAME,
            fg=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def _build_list_page(self) -> None:
        frame = tk.LabelFrame(
            self.left_content,
            text="明細一覧",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=14,
            pady=10,
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        self.list_page = frame

        header = tk.Frame(frame, bg=BG_FRAME)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)

        tk.Label(
            header,
            textvariable=self.list_title_var,
            font=BASE_FONT,
            bg=BG_FRAME,
            fg=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        tk.Button(
            header,
            text="月全体表示",
            font=SMALL_FONT,
            bg=BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_TREE_SELECTED_BG,
            activeforeground=COLOR_TEXT_PRIMARY,
            cursor="hand2",
            command=self.on_clear_date_filter,
        ).grid(row=0, column=1, sticky="e")

        columns = ("date", "type", "category", "content_category", "amount", "memo")
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_entry)

        self.tree.heading("date", text="日付")
        self.tree.heading("type", text="区分")
        self.tree.heading("category", text="カテゴリ")
        self.tree.heading("content_category", text="内容カテゴリ")
        self.tree.heading("amount", text="金額")
        self.tree.heading("memo", text="メモ")

        self.tree.column("date", width=120, minwidth=110, stretch=False, anchor="center")
        self.tree.column("type", width=88, minwidth=80, stretch=False, anchor="center")
        self.tree.column("category", width=100, minwidth=90, stretch=False, anchor="center")
        self.tree.column(
            "content_category",
            width=130,
            minwidth=110,
            stretch=False,
            anchor="w",
        )
        self.tree.column("amount", width=120, minwidth=100, stretch=False, anchor="e")
        self.tree.column("memo", width=260, minwidth=180, stretch=True, anchor="w")

        self.tree.tag_configure("income", background=COLOR_INCOME_BG, foreground=COLOR_INCOME)
        self.tree.tag_configure("expense", background=COLOR_EXPENSE_BG, foreground=COLOR_EXPENSE)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        action_frame = tk.Frame(frame, bg=BG_FRAME)
        action_frame.grid(row=2, column=0, sticky="e", pady=(10, 0))
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

    def _build_right_panel(self) -> None:
        right_panel = tk.Frame(self.root, bg=BG_MAIN)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=4)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=3)
        right_panel.rowconfigure(1, weight=2)
        self.right_panel = right_panel

        self._build_input_frame()
        self._build_summary_frame()

    def _build_input_frame(self) -> None:
        frame = tk.LabelFrame(
            self.right_panel,
            text="入力フォーム",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=18,
            pady=14,
        )
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        tk.Label(frame, text="日付", font=BASE_FONT, bg=BG_FRAME).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6
        )
        tk.Entry(
            frame,
            textvariable=self.date_var,
            font=BASE_FONT,
            width=13,
            bg=BG_INPUT,
            relief="solid",
            bd=1,
        ).grid(row=0, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="区分", font=BASE_FONT, bg=BG_FRAME).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6
        )
        type_frame = tk.Frame(frame, bg=BG_FRAME)
        type_frame.grid(row=1, column=1, sticky="w", pady=6)
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

        tk.Label(frame, text="内容カテゴリ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=6
        )
        tk.Entry(
            frame,
            textvariable=self.content_category_var,
            font=BASE_FONT,
            bg=BG_INPUT,
            relief="solid",
            bd=1,
        ).grid(row=2, column=1, columnspan=3, sticky="ew", pady=6)

        tk.Label(frame, text="カテゴリ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=6
        )
        ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=BASE_FONT,
            width=12,
        ).grid(row=3, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="金額（円）", font=BASE_FONT, bg=BG_FRAME).grid(
            row=4, column=0, sticky="w", padx=(0, 8), pady=6
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
        ).grid(row=4, column=1, sticky="ew", pady=6)

        tk.Label(frame, text="メモ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=5, column=0, sticky="w", padx=(0, 8), pady=6
        )
        tk.Entry(
            frame,
            textvariable=self.memo_var,
            font=BASE_FONT,
            bg=BG_INPUT,
            relief="solid",
            bd=1,
        ).grid(row=5, column=1, columnspan=3, sticky="ew", pady=6)

        self.submit_button = tk.Button(
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
        )
        self.submit_button.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        self.cancel_edit_button = tk.Button(
            frame,
            text="編集をやめる",
            font=BASE_FONT,
            bg=BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_TREE_SELECTED_BG,
            activeforeground=COLOR_TEXT_PRIMARY,
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.on_cancel_edit,
            state="disabled",
        )
        self.cancel_edit_button.grid(row=6, column=2, columnspan=2, sticky="ew", pady=(14, 0), padx=(8, 0))

    def _build_summary_frame(self) -> None:
        frame = tk.LabelFrame(
            self.right_panel,
            text="月次サマリ",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=18,
            pady=14,
        )
        frame.grid(row=1, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        tk.Label(
            frame,
            textvariable=self.income_var,
            font=HEADING_FONT,
            bg=BG_FRAME,
            fg=COLOR_INCOME,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=4)

        tk.Label(
            frame,
            textvariable=self.expense_var,
            font=HEADING_FONT,
            bg=BG_FRAME,
            fg=COLOR_EXPENSE,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=4)

        tk.Label(
            frame,
            textvariable=self.balance_var,
            font=SUMMARY_FONT,
            bg=BG_FRAME,
            fg=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(8, 10))

        action_frame = tk.Frame(frame, bg=BG_FRAME)
        action_frame.grid(row=3, column=0, sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        tk.Button(
            action_frame,
            text="明細一覧を開く",
            font=BASE_FONT,
            bg=BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_TREE_SELECTED_BG,
            activeforeground=COLOR_TEXT_PRIMARY,
            cursor="hand2",
            command=lambda: self.show_view(VIEW_LIST),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        tk.Button(
            action_frame,
            text="CSV出力",
            font=BASE_FONT,
            bg=COLOR_CSV_BTN,
            fg=COLOR_CSV_BTN_FG,
            activebackground=COLOR_CSV_BTN_ACTIVE,
            activeforeground=COLOR_CSV_BTN_FG,
            cursor="hand2",
            command=self.on_export_csv,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

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

    def _month_key(self) -> str:
        return f"{self.calendar_year:04d}-{self.calendar_month:02d}"

    def _set_edit_mode(self, entry_id: int | None) -> None:
        self.current_entry_id = entry_id
        if entry_id is None:
            self.submit_button.configure(text="追加する")
            self.cancel_edit_button.configure(state="disabled")
        else:
            self.submit_button.configure(text="更新する")
            self.cancel_edit_button.configure(state="normal")

    def _clear_input_values(self) -> None:
        self.content_category_var.set("")
        self.amount_var.set("")
        self.memo_var.set("")

    def _populate_form_for_edit(self, row: dict) -> None:
        self.date_var.set(row["date"])
        self.type_var.set(row["type"])
        self.category_var.set(row["category"])
        self.content_category_var.set(row.get("content_category", ""))
        self.amount_var.set(str(row["amount"]))
        self.memo_var.set(row["memo"])
        self._set_edit_mode(int(row["id"]))

    def _update_view_buttons(self) -> None:
        active = self.calendar_view_btn if self.current_view == VIEW_CALENDAR else self.list_view_btn
        inactive = self.list_view_btn if self.current_view == VIEW_CALENDAR else self.calendar_view_btn
        active.configure(bg=COLOR_CSV_BTN, fg=COLOR_CSV_BTN_FG, relief="sunken")
        inactive.configure(bg=BG_INPUT, fg=COLOR_TEXT_PRIMARY, relief="raised")

    def show_view(self, view_name: str) -> None:
        self.current_view = view_name
        if view_name == VIEW_CALENDAR:
            self.calendar_page.tkraise()
        else:
            self.list_page.tkraise()
            self.refresh_entries()
        self._update_view_buttons()

    def _change_month(self, diff: int) -> None:
        self.calendar_year, self.calendar_month = self._change_year_month(
            self.calendar_year,
            self.calendar_month,
            diff,
        )
        if self.selected_date_filter and not self.selected_date_filter.startswith(self._month_key()):
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
        if self.current_view == VIEW_LIST:
            self.refresh_entries()
        self.refresh_summary()

    def refresh_calendar(self) -> None:
        self.calendar_title_var.set(self._month_title(self.calendar_year, self.calendar_month))

        month_key = self._month_key()
        totals = self.service.daily_totals(self.calendar_year, self.calendar_month)
        month_days = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self.calendar_year,
            self.calendar_month,
        )
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
                    disabledforeground=COLOR_TEXT_PRIMARY,
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
        self.entries_by_id = {}

        if self.selected_date_filter:
            self.list_title_var.set(f"明細一覧（{self.selected_date_filter}）")
            rows = self.service.list_entries(date_filter=self.selected_date_filter)
        else:
            month_key = self._month_key()
            self.list_title_var.set(f"明細一覧（{month_key} 全件）")
            rows = self.service.list_entries(year_month_filter=month_key)

        for row in rows:
            self.entries_by_id[int(row["id"])] = row
            label = "収入" if row["type"] == ENTRY_TYPE_INCOME else "支出"
            amount_text = self._format_amount(row["amount"], row["type"])
            tag = "income" if row["type"] == ENTRY_TYPE_INCOME else "expense"
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    row["date"],
                    label,
                    row["category"],
                    row.get("content_category", ""),
                    amount_text,
                    row["memo"],
                ),
                tags=(tag,),
            )

        if self.current_entry_id is not None and self.current_entry_id not in self.entries_by_id:
            self._set_edit_mode(None)

    def refresh_summary(self) -> None:
        summary = self.service.monthly_summary(self.calendar_year, self.calendar_month)
        title = self._month_title(summary["year"], summary["month"])
        self.income_var.set(f"{title} 収入合計: {summary['income_total']:,} 円")
        self.expense_var.set(f"{title} 支出合計: {summary['expense_total']:,} 円")
        self.balance_var.set(f"{title} 収支: {summary['balance']:,} 円")

    def on_select_calendar_date(self, date_text: str) -> None:
        if self.selected_date_filter == date_text:
            self.selected_date_filter = None
            self.refresh_calendar()
            if self.current_view == VIEW_LIST:
                self.refresh_entries()
            self._set_status("日付選択を解除しました")
            return

        self.selected_date_filter = date_text
        self.date_var.set(date_text)
        self.refresh_calendar()
        self.show_view(VIEW_LIST)
        self._set_status(f"{date_text} の明細を表示しています")

    def on_clear_date_filter(self) -> None:
        self.selected_date_filter = None
        self.refresh_all()
        self._set_status("日付選択を解除しました")

    def on_select_entry(self, _event: tk.Event | None = None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        entry_id = int(selected[0])
        row = self.entries_by_id.get(entry_id)
        if row is None:
            return
        self._populate_form_for_edit(row)
        self._set_status(f"{row['date']} の明細を編集中です")

    def on_cancel_edit(self) -> None:
        self._set_edit_mode(None)
        self.tree.selection_remove(*self.tree.selection())
        self._clear_input_values()
        self._set_status("編集を解除しました")

    def on_add(self) -> None:
        input_date = self.date_var.get()
        previous_filter = self.selected_date_filter
        is_update = self.current_entry_id is not None
        try:
            if is_update:
                updated = self.service.update_entry(
                    entry_id=self.current_entry_id,
                    date_text=input_date,
                    entry_type=self.type_var.get(),
                    category=self.category_var.get(),
                    content_category=self.content_category_var.get(),
                    amount_text=self.amount_var.get(),
                    memo=self.memo_var.get(),
                )
                if not updated:
                    self._set_edit_mode(None)
                    self._set_status("更新対象が見つかりませんでした", is_error=True)
                    return
            else:
                self.service.create_entry(
                    date_text=input_date,
                    entry_type=self.type_var.get(),
                    category=self.category_var.get(),
                    content_category=self.content_category_var.get(),
                    amount_text=self.amount_var.get(),
                    memo=self.memo_var.get(),
                )
        except ValueError as exc:
            self._set_status(str(exc), is_error=True)
            messagebox.showerror("入力エラー", str(exc))
            return
        except (sqlite3.Error, OSError):
            message = "更新に失敗しました" if is_update else "保存に失敗しました"
            self._set_status(message, is_error=True)
            messagebox.showerror("エラー", message)
            return

        try:
            created = datetime.strptime(input_date.strip(), DATE_FORMAT)
            created_date = created.strftime(DATE_FORMAT)
            self.calendar_year = created.year
            self.calendar_month = created.month
            if previous_filter is not None:
                self.selected_date_filter = created_date
            else:
                self.selected_date_filter = None
        except ValueError:
            self.selected_date_filter = previous_filter

        if is_update:
            self._set_edit_mode(None)
            self.tree.selection_remove(*self.tree.selection())
        else:
            self._clear_input_values()
        self.refresh_all()
        self._set_status("更新しました" if is_update else "保存しました")

    def on_delete(self) -> None:
        selected = self.tree.selection()
        if not selected:
            self._set_status("削除したい行を選択してください", is_error=True)
            return

        if not messagebox.askyesno("確認", "選択した明細を削除しますか？"):
            return

        entry_id = int(selected[0])
        try:
            deleted = self.service.delete_entry(entry_id)
        except (sqlite3.Error, OSError):
            message = "削除に失敗しました"
            self._set_status(message, is_error=True)
            messagebox.showerror("エラー", message)
            return

        if not deleted:
            self._set_status("削除対象が見つかりませんでした", is_error=True)
            return

        if self.current_entry_id == entry_id:
            self._set_edit_mode(None)
            self._clear_input_values()
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
