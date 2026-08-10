# 生成パイプライン

## 標準フロー

```text
依頼と添付資料
  → 事前検査
  → 必要な質問
  → 制作条件・構成案の承認
  → deck.json
  → 構造QA
  → HTML
  → 全ページ視覚QA
  → HTML確認
  → PDF
  → 最終QA
  → 人間の承認
  → delivery
```

既定は`interactive`です。HTML確認後にPDFを生成し、不要な再変換を避けます。`autonomous`、`html_only`、`review_only`は後続Phaseで追加します。

## 再開

再開時はチャット履歴に依存せず、`run.json`、承認済みBrief、最新Attempt、QA、レビュー、最後の成功Stepを読みます。入力ハッシュが同じ生成物は再利用し、`deck.json`が変わった場合は新しいAttemptを作ります。

## 既存成果物

- `deck.json`: 共通形式なら続きから再生成する。
- ハーネス生成HTML: 埋め込みデータから復元する。
- 一般HTML: 新しいRunへ取り込み、変換結果を人間が確認する。
- PDFのみ: 参考・検査用途とし、完全復元を保証しない。
