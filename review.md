# 家計簿アプリ 全体コードレビュー（第4回）

**対象**: 全ファイル（13ファイル, 878+149+158+65+77+128+6+39+50+179+11+2+20行）  
**レビュー日**: 2026-03-06  
**仕様書**: SPEC.md

---

## 前回（第3回）指摘の対応状況

| # | 内容 | 状態 | 備考 |
|---|------|------|------|
| W-1 | `disabledforeground` 未設定 | ✅ 修正済 | L712 で明示 |
| W-2 | `_show_error_dialog` の root リーク | ✅ 修正済 | `finally` + `root = None` イディオム |
| W-3 | `on_delete` に DB エラーキャッチなし | ✅ 修正済 | `(sqlite3.Error, OSError)` で統一 |
| I-1 | SPEC.md に `run.py` / `tests/` 未記載 | ✅ 修正済 | ディレクトリ構成に追記 |
| I-2 | カレンダー選択時に `refresh_summary` 未呼出 | 🟡 設計変更で解消方向 | `on_clear_date_filter` は `refresh_all()` に変更 |
| I-3 | `calendar.firstweekday` 未明示 | ✅ 修正済 | `Calendar(firstweekday=0)` に変更 |
| I-4 | SPEC.md のテスト件数が実態と乖離 | ✅ 修正済 | 「10件以上、現行13件」に更新 |

> **前回指摘は全件対応済みです。** 👏

---

## 新規変更の概要

- **タブ切替UI**: 左パネルでカレンダー/明細一覧を `tkraise()` で切替
- **右パネル**: 入力フォーム（縦レイアウト）+ 月次サマリ（「明細一覧を開く」ボタン付き）
- **`year_month_filter`**: `db.fetch_entries` / `service.list_entries` に月フィルタ追加
- **カレンダー日付トグル**: 同じ日付を再クリックで選択解除
- **追加時の filter 保持**: `previous_filter` を使い、全体表示中は勝手にフィルタしない
- **テスト**: 13件に拡充（`test_list_entries_with_year_month_filter` 追加）

---

## 🟡 Warning

### W-1. `on_select_calendar_date` で `refresh_entries` が二重呼び出し

**ファイル**: ui.py L782-787

```python
self.selected_date_filter = date_text
self.date_var.set(date_text)
self.refresh_calendar()
self.show_view(VIEW_LIST)      # ← 内部で self.refresh_entries() を呼ぶ
self.refresh_entries()          # ← ここでも呼ぶ → 二重呼び出し
```

`show_view(VIEW_LIST)` の L651 で `self.refresh_entries()` が呼ばれ、直後の L786 でも呼ばれます。明細が2回リフレッシュされて無駄なDB問い合わせが発生します。L786 の `self.refresh_entries()` を削除するか、`show_view` 側の呼び出しを条件付きにすべきです。

---

### W-2. `BUTTON_FONT` が未使用

**ファイル**: ui.py L18 (import), constants.py L28

`BUTTON_FONT` をインポートしていますが、現在のコードでは使用されていません。追加ボタンは以前 `BUTTON_FONT` を使っていましたが、L503 を確認すると `BUTTON_FONT` が使われています。

→ 再確認: L503 で使用あり。**この指摘は取り消し**。

---

### W-3. `refresh_all` がリスト非表示時もエントリを更新

**ファイル**: ui.py L684-687

```python
def refresh_all(self) -> None:
    self.refresh_calendar()
    self.refresh_entries()    # ← カレンダー表示中も毎回DBクエリ
    self.refresh_summary()
```

カレンダービュー表示中でも `refresh_entries()` が走り、不可視の Treeview を更新しています。パフォーマンス上は軽微ですが、`show_view(VIEW_LIST)` 切替時に `refresh_entries()` を呼んでいるので、ここでは省略可能です。

**修正案**:
```python
def refresh_all(self) -> None:
    self.refresh_calendar()
    if self.current_view == VIEW_LIST:
        self.refresh_entries()
    self.refresh_summary()
```

ただし、ビュー切替時に `refresh_entries` が呼ばれる設計なので、現状でも大きな問題ではありません。

---

### W-4. `on_select_calendar_date` の解除時に `refresh_entries` が呼ばれない

**ファイル**: ui.py L775-780

```python
if self.selected_date_filter == date_text:
    self.selected_date_filter = None
    self.refresh_calendar()
    self._set_status("日付選択を解除しました")
    return    # ← refresh_entries は呼ばれない
```

トグルで日付選択を解除したとき、リスト側のタイトルやデータがフィルタ状態のままになります。リストビューに切り替えたとき `show_view` 内で `refresh_entries()` が呼ばれるため直ちに問題にはなりませんが、すでにリストビューが表示中だった場合は古い状態が残ります。

---

## 🔵 Improvement

### I-1. `_update_view_buttons` の冗長なコード

**ファイル**: ui.py L621-643

カレンダー / リストの2ビューに対して if/else で完全に対称的なコードがあります。ヘルパーで簡潔にできます:

```python
def _update_view_buttons(self) -> None:
    active = self.calendar_view_btn if self.current_view == VIEW_CALENDAR else self.list_view_btn
    inactive = self.list_view_btn if self.current_view == VIEW_CALENDAR else self.calendar_view_btn
    active.configure(bg=COLOR_CSV_BTN, fg=COLOR_CSV_BTN_FG, relief="sunken")
    inactive.configure(bg=BG_INPUT, fg=COLOR_TEXT_PRIMARY, relief="raised")
```

---

### I-2. `on_select_calendar_date` から `show_view(VIEW_LIST)` を呼ぶのが少し驚き

日付をクリックするとカレンダーからリストビューに自動切替する動作は、直感的かもしれないし、混乱するかもしれません。設計判断としては理解できますが、ユーザーテストで「勝手に切り替わった」と感じられる場合は要検討です。

---

### I-3. SPEC.md の「5.1 メイン画面」が実態と乖離

**ファイル**: SPEC.md L50-63

```
- 上部: 「入力フォーム」
- 中央: 「明細一覧」
- 下部: 「月次サマリ」
```

実際は2カラム + タブ切替UIです。5.1 を実態に合わせて更新するのが望ましいです。

---

### I-4. テストに `year_month_filter` + `date_filter` 併用ケースがない

`fetch_entries` は `date_filter` と `year_month_filter` を同時に受け取れる設計（WHERE句を AND で結合）ですが、UIで同時使用することはありません。テストでも併用ケースはありません。同時指定を禁止するか、テストを追加するか、どちらかが明確になります。

---

## ✅ 良い点

| 項目 | 評価 |
|------|------|
| **タブ切替** | `tkraise()` でスタック切替。画面遷移なしのSPA風 |
| **前回指摘全件対応** | W-1〜W-3, I-1〜I-4 すべて修正済 |
| **DB フィルタ設計** | `date_filter` / `year_month_filter` を WHERE 動的構築 |
| **カレンダー日付トグル** | 同じ日付再クリックで解除、直感的 |
| **追加時の filter 保持** | `previous_filter` パターンで自然なUX |
| **`_show_error_dialog`** | `finally` + `root = None` で安全 |
| **`on_delete` エラーキャッチ** | `sqlite3.Error, OSError` で統一 |
| **テスト 13件** | バリデーション全パターン、ロールバック、月フィルタ |
| **色定数完全集約** | ハードコード色ゼロ |
| **`Calendar(firstweekday=0)`** | ロケール依存なし |
| **`disabledforeground`** | 無効セルの表示が明示的 |
| **SPEC.md 更新** | ディレクトリ構成 / テスト件数を反映済 |

---

## 指摘一覧サマリ

| # | 重要度 | 内容 | ファイル |
|---|--------|------|---------|
| W-1 | 🟡 Warning | `refresh_entries` 二重呼び出し | `ui.py` L782-787 |
| W-3 | 🟡 Warning | リスト非表示時もDB問い合わせ | `ui.py` L684-687 |
| W-4 | 🟡 Warning | トグル解除時にリスト未更新 | `ui.py` L775-780 |
| I-1 | 🔵 Improve | `_update_view_buttons` 冗長 | `ui.py` L621-643 |
| I-2 | 🔵 Improve | カレンダークリックで自動ビュー切替 | `ui.py` L785 |
| I-3 | 🔵 Improve | SPEC.md 画面仕様が実態と乖離 | `SPEC.md` L50-63 |
| I-4 | 🔵 Improve | フィルタ併用のテスト不在 | `test_service.py` |

**🔴 Critical: 0件**

---

## 総合評価

前回の指摘 **全7件が対応済み**。新たなタブ切替UIも適切に実装されています。

残りの指摘は **Warning 3件（うち2件はパフォーマンス微小）**、**Improvement 4件（設計判断レベル）** のみで、**プロダクション投入可能な品質** です。
