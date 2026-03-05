# 家計簿アプリ 全体コードレビュー（第2回）

**対象**: `/Users/admin/Desktop/wk/kk` 全ファイル  
**レビュー日**: 2026-03-05  
**仕様書**: [SPEC.md](file:///Users/admin/Desktop/wk/kk/SPEC.md)

---

## 前回レビュー指摘の対応状況

| # | 内容 | 状態 |
|---|------|------|
| C-1 | 複数行選択バグ | ✅ `selectmode="browse"` で修正済 |
| C-2 | DB例外時ロールバック欠如 | ❌ **未対応** |
| W-1 | 全角数字でクラッシュ | ❌ 未対応 |
| I-2 | `try/except ImportError` パターン | 🟡 `run.py` 導入で改善方向だが各ファイルに残存 |
| I-5 | `Exception` キャッチが広い | 🟡 `main.py` のTkチェックで一部改善 |

---

## 🔴 Critical

### C-1. `connect()` で例外発生時にロールバックされない（前回 C-2 継続）

**ファイル**: [db.py](file:///Users/admin/Desktop/wk/kk/app/db.py) L31-39

```python
@contextmanager
def connect(self):
    connection = sqlite3.connect(self.db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
```

例外時に `rollback()` が呼ばれません。`close()` 時に暗黙ロールバックされますが、明示すべきです。

**修正案**:
```python
try:
    yield connection
    connection.commit()
except Exception:
    connection.rollback()
    raise
finally:
    connection.close()
```

---

## 🟡 Warning

### W-1. 全角数字入力でクラッシュ（前回 W-1 継続）

**ファイル**: [service.py](file:///Users/admin/Desktop/wk/kk/app/service.py) L47-54

`isdigit()` は全角数字 `１２３` に `True` を返しますが、`int()` は変換できずキャッチされない例外が発生します。高齢者はIMEで全角入力しやすいため要注意。

**修正案**: `normalized.isascii() and normalized.isdigit()` に変更。

---

### W-2. `validate_date` が `2026-02-30` 等の不正日付を通す

**ファイル**: [service.py](file:///Users/admin/Desktop/wk/kk/app/service.py) L27-32

```python
def validate_date(date_text: str) -> str:
    parsed = datetime.strptime(date_text, DATE_FORMAT)
    return parsed.strftime(DATE_FORMAT)
```

`strptime` は Python 3.11 時点で `"2026-02-30"` → 例外を出しますが、`"2026-13-01"` のようなケースでの挙動はバージョン依存です。より堅牢にするなら `date.fromisoformat()` を使う方が安全です。

---

### W-3. `ui.py` の SMALL_FONT が未使用

**ファイル**: [ui.py](file:///Users/admin/Desktop/wk/kk/app/ui.py) L34

`SMALL_FONT` をインポートしていますが、使用箇所がありません。不要なインポートです。

---

## 🔵 Improvement

### I-1. `create_entry` の戻り値型がコードとテストで不整合

**ファイル**: [service.py](file:///Users/admin/Desktop/wk/kk/app/service.py) L68-82

```python
def create_entry(...) -> str:    # 戻り値 str と宣言
    ...
    return date_value              # date_value を返す
```

テスト側は戻り値を使っていないため現状問題ありませんが、もともと `-> None` だったものが `-> str` に変更されています。UIでも戻り値は使われていません。設計意図を明確にするか、使わないなら `-> None` に戻す方が良いでしょう。

---

### I-2. `fetch_entries` のフィルタ用SQLが2パターンに分岐

**ファイル**: [db.py](file:///Users/admin/Desktop/wk/kk/app/db.py) L72-91

```python
def fetch_entries(self, date_filter: str | None = None) -> list[dict]:
    if date_filter:
        query = """..."""
        params = (date_filter,)
    else:
        query = """..."""
        params = ()
```

SQL文が2箇所にほぼ同じ内容で書かれています。WHERE句だけ動的に組み立てる方がDRYです：

```python
query = "SELECT ... ORDER BY date DESC, id DESC"
if date_filter:
    query = query.replace("ORDER", "WHERE date = ? ORDER")
    params = (date_filter,)
```

ただしMVP規模なら現状でも許容範囲です。

---

### I-3. `daily_totals` / `fetch_daily_totals` がUIから未使用

**ファイル**: [db.py](file:///Users/admin/Desktop/wk/kk/app/db.py) L114-128, [service.py](file:///Users/admin/Desktop/wk/kk/app/service.py) L106-119

SPEC に「カレンダー表示」があり、テストも存在しますが、`ui.py` からは呼ばれていません。カレンダー機能が未実装の状態でメソッドだけ先に作られています。README には「月カレンダー表示」と記載されているため、**README と実装に乖離**があります。

---

### I-4. `list_entries(date_filter=...)` がUIから未使用

**ファイル**: [service.py](file:///Users/admin/Desktop/wk/kk/app/service.py) L84-85

同様に `date_filter` 機能はテストされていますが、UIからは呼ばれていません。

---

### I-5. テストカバレッジがService層に偏っている

**ファイル**: [test_service.py](file:///Users/admin/Desktop/wk/kk/tests/test_service.py)

5テストに増加（前回3件）しましたが、すべてService層のみです。追加すべきテスト：
- 日付バリデーション（不正形式）
- メモ文字数上限（101文字）
- カテゴリ/区分バリデーション
- DB層の `delete_entry` （存在しないID）

---

### I-6. `activebackground` 等のハードコード色が `constants.py` に未定義

**ファイル**: [ui.py](file:///Users/admin/Desktop/wk/kk/app/ui.py) L217, L277, L323 等

`"#2F8A4C"`, `"#B33030"`, `"#49598A"`, `"#FFFFF0"`, `"#FDECEA"`, `"#E8F5E9"`, `"#B3D4FC"` 等がハードコードされています。`constants.py` に色定数を集約した設計方針と一貫させるなら、これらも定数化するのが良いでしょう。

---

## 📝 Note（軽微 / 参考情報）

### N-1. `run.py` のエントリーポイント分離は良い設計

`run.py` → `app.main.main()` の構成で、PyInstaller ビルドと開発時実行を統一できています。`--noconsole` オプションも追加されており、exe起動時の黒窓が出ない設計になっています。

---

### N-2. `main.py` の Tkinter 可用性チェック

[main.py](file:///Users/admin/Desktop/wk/kk/app/main.py) L26-31 で Tkinter のインポートを `try/except` で包み、ない環境では親切なメッセージを表示しています。良い改善です。

---

### N-3. `.gitignore` に `__pycache__/` があるが、ルートに `__pycache__/` ディレクトリが存在

ルートに `__pycache__/` が残っています。`git clean` で除去するか確認してください。

---

## ✅ 良い点

| 項目 | 評価 |
|------|------|
| **レイヤー分離** | DB → Service → UI が明確 |
| **仕様準拠** | SPEC.md のMVPスコープをほぼカバー |
| **エントリーポイント** | `run.py` で統一、`--noconsole` 対応 |
| **パス解決** | `resolve_app_base_dir()` で frozen 対応 |
| **CSV** | `utf-8-sig` BOM付き（Excel対応）|
| **バリデーション** | 具体的な日本語エラーメッセージ |
| **UI配色** | 暖色系背景、収入/支出色分け、大フォント |
| **単一選択** | `selectmode="browse"` でバグ防止 |
| **テスト** | 5件に増加、`daily_totals` もカバー |
| **Tkチェック** | Tk不在環境でのフォールバック対応 |

---

## 指摘一覧サマリ

| # | 重要度 | 内容 | ファイル |
|---|--------|------|---------|
| C-1 | 🔴 Critical | 例外時のロールバック欠如 | `db.py` |
| W-1 | 🟡 Warning | 全角数字でクラッシュ | `service.py` |
| W-2 | 🟡 Warning | 不正日付のバリデーション | `service.py` |
| W-3 | 🟡 Warning | 未使用インポート `SMALL_FONT` | `ui.py` |
| I-1 | 🔵 Improve | `create_entry` の戻り値型不整合 | `service.py` |
| I-2 | 🔵 Improve | SQLが2パターンに重複 | `db.py` |
| I-3 | 🔵 Improve | `daily_totals` がUI未使用（README乖離）| `db.py`, `service.py` |
| I-4 | 🔵 Improve | `date_filter` がUI未使用 | `service.py` |
| I-5 | 🔵 Improve | テストがService層のみ | `test_service.py` |
| I-6 | 🔵 Improve | UI色のハードコード | `ui.py` |
| N-3 | 📝 Note | ルートに `__pycache__/` 残存 | プロジェクトルート |
