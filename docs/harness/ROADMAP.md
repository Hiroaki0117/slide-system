# ハーネス実装ロードマップ

## Phase 0: 基盤（完了）

- 技術境界と設計文書
- PythonパッケージとNode.js依存宣言
- 基本JSON Schema
- Run作成・一覧・検索・再開位置表示
- 静的HTML管理画面
- 初心者向けREADME

## Phase 1: Run管理（基本機能完了）

- Attempt / Step
- 状態遷移
- 承認済みBrief
- ロック、バックアップ、ハッシュ、キャッシュ
- スキーマの実検証
- 完了時のQA・成果物・人間承認ゲート

スキーマ移行コマンドは、v2形式が必要になった時点で追加します。完成済みRunはその場で書き換えず、子Runとして再生成します。

## Phase 2: デザインと生成（完了）

- `warm_clean`デザインパック
- ハーネスv1 `deck.json`からHTML生成
- 既存ビルダーとの変換層
- PDF生成

## Phase 3: QA（完了）

- 静的QA
- 全ページ描画
- PDF比較
- QAレポート統合
- PASSまでのAttemptループ

## Phase 4: アダプター（次）

- Codex
- Claude Code
- 承認ゲートと再開指示

## Phase 5: 管理画面

- サムネイルと成果物リンク
- 状態変更とレビュー導線
- 比較画面

## Phase 6以降

- 複数題材のテストケースとベースライン
- Claude WebのBundle連携
- リリース自動化
- npm配布ラッパー
