# AIアダプター

## 目的

アダプターは、Codex、Claude Code、Claude Webの能力差を共通ハーネスへ伝える薄い接続層です。文章、デザイン、題材固有ルールは持ちません。

## Codex / Claude Code

ローカルのRunとCLIを直接使用します。AIは質問、構成、`deck.json`、内容修正を担当し、ハーネスがHTML/PDFとQAを担当します。

## Claude Web

既存の無料版・有料版ZIPは単体利用として残します。ローカルハーネス連携は、将来`run-bundle.zip`と`result-bundle.zip`を介して`deck.json`だけを往復させます。

## 能力情報

各アダプターは、ファイル操作、シェル、Web検索、ユーザー質問、ブラウザ描画、PDF出力、ZIP入出力の可否を宣言します。機能が不足する場合は制作前に検出し、代替案を提示します。
