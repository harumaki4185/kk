from __future__ import annotations

import sqlite3

try:
    from .db import Database
    from .service import KakeiboService
except ImportError:  # pragma: no cover
    from db import Database
    from service import KakeiboService


def _show_error_dialog(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ModuleNotFoundError:
        print(message)
        return

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("エラー", message)
    except tk.TclError:
        print(message)
    finally:
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass


def main() -> int:
    try:
        import tkinter as tk
    except ModuleNotFoundError:
        print("Tkinter が利用できないため、GUIを起動できません。")
        print("Windows向けの配布版（kakeibo.exe）を使用するか、Tk対応のPythonを利用してください。")
        return 1

    try:
        from .ui import KakeiboApp
    except ImportError:  # pragma: no cover
        from ui import KakeiboApp

    database = Database()
    try:
        database.init_db()
    except (sqlite3.Error, OSError):
        _show_error_dialog("データベースの初期化に失敗しました")
        return 1

    service = KakeiboService(database)
    root = tk.Tk()
    KakeiboApp(root, service)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
