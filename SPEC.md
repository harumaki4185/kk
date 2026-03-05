# 家計簿アプリ仕様書（Windows向け・短時間開発版）

## 1. 目的
- 祖母世代でも迷わず使える、シンプルな家計簿アプリを提供する。
- Windows PC 上で動作する単体実行ファイル（`.exe`）を配布できるようにする。
- 実装は「数時間（目安 4〜6 時間）」で完了可能な MVP に限定する。

## 2. 前提と制約
- 対象OS: Windows 10 / 11
- 開発言語: Python 3.11
- UI: Tkinter（標準ライブラリ）
- データ保存: SQLite（ローカルファイル）
- ビルド: GitHub Actions（Windows Runner）+ PyInstaller
- オフライン利用を前提（ネット接続不要）

## 3. ユーザー像
- PCの基本操作（起動、クリック、文字入力）は可能
- 複雑な設定や多機能は不要
- 1日ごとの支出入力と月次の合計確認が主目的

## 4. MVPスコープ
### 4.1 必須機能
- 収支入力
  - 日付（初期値: 今日）
  - 区分（`支出` / `収入`）
  - カテゴリ（固定: 食費, 日用品, 医療, 光熱費, 交通, その他）
  - 金額（整数円）
  - メモ（任意）
- 一覧表示
  - 最新順表示
  - 行選択で削除
- 月次集計
  - 当月の収入合計
  - 当月の支出合計
  - 当月の収支（収入 - 支出）
- CSVエクスポート
  - 全データを `kakeibo_export_YYYYMMDD.csv` で保存

### 4.2 非対象（MVP外）
- ユーザーアカウント
- クラウド同期
- 複数通貨対応
- グラフ描画
- レシートOCR

## 5. 画面仕様
### 5.1 メイン画面（単一画面）
- 上部: 「入力フォーム」
  - 日付入力（YYYY-MM-DD）
  - 区分選択（ラジオボタン）
  - カテゴリ選択（ドロップダウン）
  - 金額入力（大きめフォント）
  - メモ入力
  - `追加` ボタン
- 中央: 「明細一覧」
  - 列: 日付, 区分, カテゴリ, 金額, メモ
  - `選択行を削除` ボタン
- 下部: 「月次サマリ」
  - 収入合計、支出合計、収支
  - `CSV出力` ボタン

### 5.2 UI/UX要件（高齢者向け）
- 基本文字サイズ 14pt 以上、主要ボタン 16pt
- 1画面完結（画面遷移なし）
- ボタン文言は動詞で明確化（例: `追加`, `削除`, `CSV出力`）
- エラー時は短文で具体的に表示（例: `金額は数字で入力してください`）

## 6. データ仕様
### 6.1 SQLiteファイル
- ファイル名: `kakeibo.db`
- 配置: 実行ファイル同階層の `data/` ディレクトリ

### 6.2 テーブル定義
```sql
CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,         -- YYYY-MM-DD
  type TEXT NOT NULL,         -- income / expense
  category TEXT NOT NULL,
  amount INTEGER NOT NULL,    -- 円
  memo TEXT DEFAULT '',
  created_at TEXT NOT NULL    -- ISO8601
);
```

### 6.3 入力バリデーション
- 日付: `YYYY-MM-DD` 形式かつ妥当日付
- 区分: `income` または `expense`
- 金額: 1 以上の整数
- メモ: 100文字以内（超過時はエラー）

## 7. 例外処理・メッセージ
- DB初期化失敗: `データベースの初期化に失敗しました`
- 入力不正: `入力内容を確認してください`
- CSV出力失敗: `CSVの保存に失敗しました`
- 成功時: `保存しました`, `削除しました`, `CSVを出力しました`

## 8. 技術構成
### 8.1 ディレクトリ構成（想定）
```text
.
├─ app/
│  ├─ main.py
│  ├─ ui.py
│  ├─ db.py
│  ├─ service.py
│  └─ constants.py
├─ data/                 # 実行時作成
├─ requirements.txt
├─ README.md
└─ .github/
   └─ workflows/
      └─ build-windows.yml
```

### 8.2 依存ライブラリ
- 必須:
  - `pyinstaller`
- 任意:
  - `pytest`（最小テスト用）

## 9. GitHub Actions ビルド仕様
### 9.1 トリガー
- `push`（`main` ブランチ）
- `workflow_dispatch`（手動実行）

### 9.2 ビルド環境
- `runs-on: windows-latest`
- Python 3.11 セットアップ
- `pip install -r requirements.txt`
- `python -m unittest discover -s tests -p "test_*.py"`
- `pyinstaller --onefile --name kakeibo run.py`

### 9.3 成果物
- `dist/kakeibo.exe` を Artifact としてアップロード
- Artifact 名: `kakeibo-windows`
- 保持期間: 14日

### 9.4 将来拡張（任意）
- タグ (`v*`) で GitHub Release を自動作成
- `.exe` を Release Assets に添付

## 10. テスト方針（短時間版）
- 手動確認（必須）
  - 追加 → 一覧反映
  - 削除 → 一覧から消える
  - 月次合計が正しい
  - CSV出力できる
- 自動テスト（可能なら）
  - `service.py` の集計関数ユニットテスト 2〜3件

## 11. 完了条件（受け入れ基準）
- Windowsで `kakeibo.exe` が起動する
- 収支の追加・削除・月次集計・CSV出力が動く
- 異常入力時にエラーメッセージが出る
- GitHub Actions で `.exe` Artifact が生成される

## 12. 実装スケジュール（4〜6時間想定）
1. 0:00-0:40 プロジェクト雛形・DB層実装
2. 0:40-2:20 UI実装（入力/一覧/削除）
3. 2:20-3:10 月次集計・CSV出力
4. 3:10-3:50 バリデーション・エラーメッセージ
5. 3:50-4:30 GitHub Actions設定・ビルド確認
6. 4:30-6:00 バグ修正・最低限テスト・README整備

## 13. リスクと対策
- 日本語パスで実行時に文字化けする可能性
  - 対策: UTF-8 固定、CSV出力時 `utf-8-sig` を使用
- PyInstallerで実行時DBパスがずれる可能性
  - 対策: 実行ファイル基準の絶対パス解決関数を実装
- 高齢者には入力が細かすぎる可能性
  - 対策: カテゴリ固定、入力項目最小化、フォント拡大
