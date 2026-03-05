from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

try:
    from .db import Database
    from .service import KakeiboService
    from .ui import KakeiboApp
except ImportError:  # pragma: no cover
    from db import Database
    from service import KakeiboService
    from ui import KakeiboApp


def main() -> None:
    database = Database()
    try:
        database.init_db()
    except Exception:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("エラー", "データベースの初期化に失敗しました")
        root.destroy()
        return

    service = KakeiboService(database)
    root = tk.Tk()
    KakeiboApp(root, service)
    root.mainloop()


if __name__ == "__main__":
    main()
