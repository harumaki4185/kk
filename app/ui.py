from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

try:
    from .constants import (
        AMOUNT_FONT,
        APP_TITLE,
        BASE_FONT,
        BG_FRAME,
        BG_INPUT,
        BG_MAIN,
        BUTTON_FONT,
        CATEGORIES,
        COLOR_ADD_BTN,
        COLOR_ADD_BTN_FG,
        COLOR_CSV_BTN,
        COLOR_CSV_BTN_FG,
        COLOR_DEL_BTN,
        COLOR_DEL_BTN_FG,
        COLOR_EXPENSE,
        COLOR_EXPENSE_BG,
        COLOR_INCOME,
        COLOR_INCOME_BG,
        COLOR_STATUS_ERR,
        COLOR_STATUS_OK,
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
        BUTTON_FONT,
        CATEGORIES,
        COLOR_ADD_BTN,
        COLOR_ADD_BTN_FG,
        COLOR_CSV_BTN,
        COLOR_CSV_BTN_FG,
        COLOR_DEL_BTN,
        COLOR_DEL_BTN_FG,
        COLOR_EXPENSE,
        COLOR_EXPENSE_BG,
        COLOR_INCOME,
        COLOR_INCOME_BG,
        COLOR_STATUS_ERR,
        COLOR_STATUS_OK,
        DATE_FORMAT,
        ENTRY_TYPE_EXPENSE,
        ENTRY_TYPE_INCOME,
        ENTRY_TYPES,
        HEADING_FONT,
        SMALL_FONT,
        SUMMARY_FONT,
    )
    from service import KakeiboService


class KakeiboApp:
    def __init__(self, root: tk.Tk, service: KakeiboService) -> None:
        self.root = root
        self.service = service

        self.root.title(APP_TITLE)
        self.root.geometry("1100x850")
        self.root.minsize(1000, 750)
        self.root.configure(bg=BG_MAIN, padx=20, pady=20)

        # ---------- Variables ----------
        self.date_var = tk.StringVar(value=date.today().strftime(DATE_FORMAT))
        self.type_var = tk.StringVar(value=ENTRY_TYPE_EXPENSE)
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.amount_var = tk.StringVar(value="")
        self.memo_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")

        self.income_var = tk.StringVar(value="収入合計:  0 円")
        self.expense_var = tk.StringVar(value="支出合計:  0 円")
        self.balance_var = tk.StringVar(value="収支:  0 円")

        self._configure_style()
        self._build_layout()
        self.refresh_all()
        self._set_status("✅ 準備できました。さっそく入力してみましょう！")

    # --------------------------------------------------------
    # Style
    # --------------------------------------------------------
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
            background=[("selected", "#B3D4FC")],
            foreground=[("selected", "#000000")],
        )

        # Combobox
        style.configure("TCombobox", padding=6)

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------
    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_input_frame()
        self._build_list_frame()
        self._build_summary_frame()
        self._build_status_bar()

    # --- Input Frame ---
    def _build_input_frame(self) -> None:
        frame = tk.LabelFrame(
            self.root,
            text="📝 入力フォーム",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=18,
            pady=14,
        )
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        frame.columnconfigure(5, weight=1)

        # --- Row 0: 日付 & 区分 ---
        tk.Label(frame, text="📅 日付", font=BASE_FONT, bg=BG_FRAME).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4,
        )
        date_entry = tk.Entry(
            frame, textvariable=self.date_var, font=BASE_FONT,
            width=13, bg=BG_INPUT, relief="solid", bd=1,
        )
        date_entry.grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(frame, text="区分", font=BASE_FONT, bg=BG_FRAME).grid(
            row=0, column=2, sticky="w", padx=(24, 8), pady=4,
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

        # --- Row 1: カテゴリ & 金額 ---
        tk.Label(frame, text="🏷 カテゴリ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=8,
        )
        category_box = ttk.Combobox(
            frame,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            font=BASE_FONT,
            width=10,
        )
        category_box.grid(row=1, column=1, sticky="w", pady=8)

        tk.Label(frame, text="💰 金額（円）", font=BASE_FONT, bg=BG_FRAME).grid(
            row=1, column=2, sticky="w", padx=(24, 8), pady=8,
        )
        amount_entry = tk.Entry(
            frame, textvariable=self.amount_var, font=AMOUNT_FONT,
            width=12, bg="#FFFFF0", relief="solid", bd=2,
            fg="#333333",
        )
        amount_entry.grid(row=1, column=3, sticky="w", pady=8)

        # --- Row 2: メモ ---
        tk.Label(frame, text="📝 メモ", font=BASE_FONT, bg=BG_FRAME).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=8,
        )
        tk.Entry(
            frame, textvariable=self.memo_var, font=BASE_FONT,
            width=38, bg=BG_INPUT, relief="solid", bd=1,
        ).grid(row=2, column=1, columnspan=3, sticky="ew", pady=8)

        # --- Add button ---
        add_btn = tk.Button(
            frame,
            text="✏️ 追加する",
            font=BUTTON_FONT,
            bg=COLOR_ADD_BTN,
            fg=COLOR_ADD_BTN_FG,
            activebackground="#2F8A4C",
            activeforeground="#FFFFFF",
            relief="raised",
            bd=2,
            width=10,
            cursor="hand2",
            command=self.on_add,
        )
        add_btn.grid(row=0, column=4, rowspan=3, padx=(20, 0), sticky="ns")

    # --- List Frame ---
    def _build_list_frame(self) -> None:
        frame = tk.LabelFrame(
            self.root,
            text="📋 明細いちらん",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=14,
            pady=10,
        )
        frame.grid(row=1, column=0, sticky="nsew", pady=(0, 14))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        columns = ("date", "type", "category", "amount", "memo")
        self.tree = ttk.Treeview(
            frame, columns=columns, show="headings",
            selectmode="browse",  # 単一選択のみ
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

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

        # Tag colors for row striping
        self.tree.tag_configure("income", background=COLOR_INCOME_BG, foreground=COLOR_INCOME)
        self.tree.tag_configure("expense", background=COLOR_EXPENSE_BG, foreground=COLOR_EXPENSE)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Delete button
        action_frame = tk.Frame(frame, bg=BG_FRAME)
        action_frame.grid(row=1, column=0, sticky="e", pady=(12, 0))
        tk.Button(
            action_frame,
            text="🗑 選択行を削除",
            font=BASE_FONT,
            bg=COLOR_DEL_BTN,
            fg=COLOR_DEL_BTN_FG,
            activebackground="#B33030",
            activeforeground="#FFFFFF",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=self.on_delete,
        ).pack(side="left")

    # --- Summary Frame ---
    def _build_summary_frame(self) -> None:
        frame = tk.LabelFrame(
            self.root,
            text="📊 今月のまとめ",
            font=HEADING_FONT,
            bg=BG_FRAME,
            padx=18,
            pady=14,
        )
        frame.grid(row=2, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)

        # Income
        tk.Label(
            frame, textvariable=self.income_var, font=HEADING_FONT,
            bg=BG_FRAME, fg=COLOR_INCOME, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=2)

        # Expense
        tk.Label(
            frame, textvariable=self.expense_var, font=HEADING_FONT,
            bg=BG_FRAME, fg=COLOR_EXPENSE, anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=2)

        # Balance – extra large
        tk.Label(
            frame, textvariable=self.balance_var, font=SUMMARY_FONT,
            bg=BG_FRAME, fg="#333333", anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(6, 2))

        # CSV button
        tk.Button(
            frame,
            text="📁 CSV出力",
            font=BUTTON_FONT,
            bg=COLOR_CSV_BTN,
            fg=COLOR_CSV_BTN_FG,
            activebackground="#49598A",
            activeforeground="#FFFFFF",
            relief="raised",
            bd=2,
            width=12,
            cursor="hand2",
            command=self.on_export_csv,
        ).grid(row=0, column=1, rowspan=3, padx=(20, 0), sticky="ns")

    # --- Status Bar ---
    def _build_status_bar(self) -> None:
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=BASE_FONT,
            bg=BG_MAIN,
            anchor="w",
            pady=6,
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def _set_status(self, message: str, is_error: bool = False) -> None:
        self.status_var.set(message)
        if is_error:
            self.status_label.configure(fg=COLOR_STATUS_ERR, bg="#FDECEA")
        else:
            self.status_label.configure(fg=COLOR_STATUS_OK, bg="#E8F5E9")

    @staticmethod
    def _format_amount(amount: int, entry_type: str) -> str:
        sign = "＋" if entry_type == ENTRY_TYPE_INCOME else "－"
        return f"{sign}{amount:,} 円"

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_entries()
        self.refresh_summary()

    def refresh_entries(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for row in self.service.list_entries():
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
        summary = self.service.monthly_summary()
        self.income_var.set(f"🔵 収入合計:  {summary['income_total']:,} 円")
        self.expense_var.set(f"🔴 支出合計:  {summary['expense_total']:,} 円")
        bal = summary["balance"]
        mark = "🟢" if bal >= 0 else "🔻"
        self.balance_var.set(f"{mark} 収支:  {bal:,} 円")

    # --------------------------------------------------------
    # Event handlers
    # --------------------------------------------------------
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
            self._set_status(f"⚠️ {exc}", is_error=True)
            messagebox.showerror("入力エラー", str(exc))
            return
        except Exception:
            message = "保存に失敗しました"
            self._set_status(f"❌ {message}", is_error=True)
            messagebox.showerror("エラー", message)
            return

        self.amount_var.set("")
        self.memo_var.set("")
        self.refresh_all()
        self._set_status("✅ 保存しました！")

    def on_delete(self) -> None:
        selected = self.tree.selection()
        if not selected:
            self._set_status("⚠️ 削除したい行をクリックして選んでください", is_error=True)
            return

        if not messagebox.askyesno("確認", "選んだ明細を削除しますか？"):
            return

        entry_id = int(selected[0])
        if not self.service.delete_entry(entry_id):
            self._set_status("⚠️ 削除する明細が見つかりませんでした", is_error=True)
            return

        self.refresh_all()
        self._set_status("✅ 削除しました")

    def on_export_csv(self) -> None:
        default_name = f"kakeibo_export_{date.today().strftime('%Y%m%d')}.csv"
        output_path = filedialog.asksaveasfilename(
            title="CSVの保存先をえらんでください",
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
            self._set_status(f"❌ {message}", is_error=True)
            messagebox.showerror("エラー", message)
            return

        self._set_status(f"✅ CSVを出力しました（{row_count}件）")
