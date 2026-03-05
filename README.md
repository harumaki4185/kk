# かんたん家計簿

Windows向けのシンプルな家計簿アプリです。  
高齢者でも使いやすいように、1画面で入力・一覧・月次集計・CSV出力を行えます。

## 機能
- 収支入力（収入/支出、カテゴリ、金額、メモ）
- 明細一覧表示（最新順）
- 選択行削除
- 当月の収入・支出・収支集計
- CSV出力（UTF-8 BOM付き）

## ローカル実行（開発時）
```bash
python run.py
```

## テスト
```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Windowsビルド（ローカル）
```bash
pip install -r requirements.txt
pyinstaller --onefile --name kakeibo run.py
```

ビルド成果物:
- `dist/kakeibo.exe`

## GitHub Actionsビルド
- ワークフロー: `.github/workflows/build-windows.yml`
- トリガー:
  - `main` ブランチへの push
  - `workflow_dispatch`（手動実行）
- 成果物:
  - Artifact 名: `kakeibo-windows`
  - ファイル: `dist/kakeibo.exe`
  - 保持期間: 14日

## トラブルシュート
- `No module named '_tkinter'` が出る場合:
  - そのPython環境はGUIライブラリ（Tk）なしです。
  - Windowsでは Actions 生成の `kakeibo.exe` を使うか、Tk対応のPythonをインストールしてください。
