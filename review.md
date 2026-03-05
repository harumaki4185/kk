# 家計簿アプリ 全体コードレビュー（第3回）

**対象**: 全ファイル  
**レビュー日**: 2026-03-06  
**仕様書**: SPEC.md

---

## 前回指摘の対応状況

| # | 内容 | 状態 | 備考 |
|---|------|------|------|
| C-1 | DB例外時のロールバック欠如 | ✅ 修正済 | `except → rollback → raise` 追加 |
| W-1 | 全角数字でクラッシュ | ✅ 修正済 | `_FULLWIDTH_TRANSLATION` で変換、`isascii()` チェック |
| W-2 | 不正日付のバリデーション | ✅ 修正済 | `date.fromisoformat()` + 正規表現で二重チェック |
| W-3 | 未使用インポート `SMALL_FONT` | ✅ 修正済 | ステータスバーで使用 |
| I-1 | `create_entry` 戻り値型不整合 | ✅ 修正済 | `-> None` に戻った |
| I-2 | SQLが2パターンに重複 | ✅ 修正済 | 動的WHERE句に統一 |
| I-3 | `daily_totals` がUI未使用 | ✅ 修正済 | カレンダー機能で使用 |
| I-4 | `date_filter` がUI未使用 | ✅ 修正済 | カレンダー日付選択で使用 |
| I-5 | テストがService層のみ | ✅ 修正済 | 12件に拡充、ロールバックテスト含む |
| I-6 | UI色のハードコード | ✅ 修正済 | 全色を `constants.py` に集約 |
| I-5(旧) | `Exception` キャッチが広い | ✅ 修正済 | `sqlite3.Error, OSError` 等に限定 |

> **前回指摘は全件対応済みです。** 👏

---

## 🟡 Warning（軽微な注意点）

### W-1. カレンダーの `disabledforeground` 未設定

**ファイル**: ui.py L587-594

```python
button.configure(
    text="",
    state="disabled",
    command=lambda: None,
    bg=COLOR_CALENDAR_EMPTY_BG,
    fg=COLOR_TEXT_PRIMARY,
)
```

`state="disabled"` にすると Tkinter はデフォルトの `disabledforeground` を使うため、`fg` 指定が無視されます。空セルなのでテキストがなく実害はありませんが、`disabledforeground` も明示する方がより堅牢です。

---

### W-2. `_show_error_dialog` の `root` がリークする可能性

**ファイル**: main.py L21-27

```python
try:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("エラー", message)
    root.destroy()
except tk.TclError:
    print(message)
```

`showerror` 後に例外が起きた場合、`root.destroy()` がスキップされます。`finally` ブロックで確実に `destroy` する方が安全です。ただし起動失敗時のみなのでリスクは低いです。

---

### W-3. `on_delete` で `sqlite3.Error` がキャッチされない

**ファイル**: ui.py L700-715

`on_add` と `on_export_csv` は `(sqlite3.Error, OSError)` をキャッチしていますが、`on_delete` には DB エラーのキャッチがありません。`service.delete_entry` → `database.delete_entry` で DB アクセスするため、同様のキャッチを入れるべきです。

**修正案**:
```python
def on_delete(self) -> None:
    ...
    try:
        if not self.service.delete_entry(entry_id):
            ...
    except (sqlite3.Error, OSError):
        self._set_status("削除に失敗しました", is_error=True)
        messagebox.showerror("エラー", "削除に失敗しました")
        return
    ...
```

---

## 🔵 Improvement（改善提案）

### I-1. SPEC.md のディレクトリ構成に `run.py` と `tests/` が未記載

**ファイル**: SPEC.md L103-117

```text
.
├─ app/
│  ├─ main.py
│  ├─ ui.py
│  ├─ db.py
│  ├─ service.py
│  └─ constants.py
├─ data/
├─ requirements.txt
├─ README.md
└─ .github/
   └─ workflows/
      └─ build-windows.yml
```

`run.py` と `tests/` がありません。SPEC を最新に保つなら追記が望ましいです。

---

### I-2. `on_select_calendar_date` / `on_clear_date_filter` で `refresh_summary` が呼ばれない

**ファイル**: ui.py L653-664

```python
def on_select_calendar_date(self, date_text: str) -> None:
    ...
    self.refresh_calendar()
    self.refresh_entries()     # ← refresh_summary なし

def on_clear_date_filter(self) -> None:
    ...
    self.refresh_calendar()
    self.refresh_entries()     # ← refresh_summary なし
```

月を変えるときは `refresh_all()` でサマリも更新されますが、カレンダー日付のクリック / 全期間表示ボタンでは呼ばれません。現状はサマリが月単位なので実害はありませんが、将来的に選択日付とサマリが連動する場合に漏れが出ます。意図的なら問題ありません。

---

### I-3. `calendar` モジュールの `firstweekday` 未指定

**ファイル**: ui.py L579

```python
month_days = calendar.monthcalendar(self.calendar_year, self.calendar_month)
```

Python の `calendar` デフォルトは月曜始まり（`firstweekday=0`）で、`WEEKDAY_LABELS` も `("月", "火", ... "日")` になっているため整合しています。ただし、ロケール依存で変わる可能性があるため、明示的に `calendar.setfirstweekday(0)` するか `Calendar(firstweekday=0).monthcalendar(...)` を使う方が安全です。

---

### I-4. SPEC.md のテスト方針に「2〜3件」とあるが12件に増加

**ファイル**: SPEC.md L152-153

```
- 自動テスト（可能なら）
  - `service.py` の集計関数ユニットテスト 2〜3件
```

実際には12件のテストが実装されています。SPEC.md を実態に合わせて更新するのが良いでしょう。

---

## ✅ 良い点

| 項目 | 評価 |
|------|------|
| **レイヤー分離** | DB → Service → UI が明確で、テストしやすい |
| **仕様準拠** | SPEC.md の全機能（カレンダー含む）を実装 |
| **2カラムレイアウト** | 左カレンダー / 右入力+明細+サマリの直感的レイアウト |
| **全角数字対応** | `_FULLWIDTH_TRANSLATION` で自然な変換 |
| **日付バリデーション** | 正規表現 + `fromisoformat()` の二重チェック |
| **DB ロールバック** | `connect()` で例外時に明示的 `rollback()` |
| **例外の絞り込み** | `sqlite3.Error, OSError` に限定（デバッグしやすい）|
| **Tkinter 可用性チェック** | `main.py` で `ModuleNotFoundError` / `TclError` 対応 |
| **エントリーポイント** | `run.py` で開発/ビルドを統一 |
| **テスト充実** | 12件（バリデーション全パターン + ロールバック + 日次集計）|
| **色定数集約** | 全色が `constants.py` に定義、ハードコードなし |
| **CI** | テスト実行 → ビルド → アップロードの完全ワークフロー |
| **CSV** | `utf-8-sig` BOM付き、日本語ヘッダー |
| **README** | トラブルシュート含む実用的なドキュメント |

---

## 指摘一覧サマリ

| # | 重要度 | 内容 | ファイル |
|---|--------|------|---------|
| W-1 | 🟡 Warning | `disabledforeground` 未設定 | `ui.py` |
| W-2 | 🟡 Warning | `_show_error_dialog` の root リーク | `main.py` |
| W-3 | 🟡 Warning | `on_delete` に DB エラーキャッチなし | `ui.py` |
| I-1 | 🔵 Improve | SPEC.md に `run.py` / `tests/` 未記載 | `SPEC.md` |
| I-2 | 🔵 Improve | カレンダー選択時に `refresh_summary` 未呼出 | `ui.py` |
| I-3 | 🔵 Improve | `calendar.firstweekday` 未明示 | `ui.py` |
| I-4 | 🔵 Improve | SPEC.md のテスト件数が実態と乖離 | `SPEC.md` |

**🔴 Critical: 0件** — 前回の Critical 指摘はすべて解消されています。

---

## 総合評価

前回レビューの **全11件の指摘が対応済み** です。特に以下が大きな改善です：

- 全角数字変換（`_FULLWIDTH_TRANSLATION`）は高齢者向けとして秀逸
- `date.fromisoformat()` + 正規表現の二重バリデーションは堅牢
- ロールバックテスト（`test_connect_rolls_back_on_error`）でDB整合性を検証
- 2カラムレイアウトでカレンダーと入力が同時に見える

残りの指摘は Warning/Improvement のみで、**MVPとしては十分な品質**です。
