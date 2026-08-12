# データモデル

## Run / Attempt / Step

- Run: 制作目的と実行条件が固定された1回の制作単位。
- Attempt: `deck.json`が変わるたびに作る候補。
- Step: 検証、HTML生成、描画、PDF生成などの個別処理。

技術的な再試行で入力が変わらない場合は、Attemptを増やしません。

## Runの主なファイル

```text
runs/run_YYYYMMDD_NNN/
├─ run.json
├─ run.lock.json              将来追加
├─ events.jsonl
├─ input/
│  ├─ request.md
│  └─ attachments/
├─ brief/
│  └─ approved-brief.json
├─ attempts/
│  └─ 001/
│     ├─ attempt.json
│     ├─ deck.json
│     ├─ steps/
│     ├─ deck.html
│     ├─ content-qa.json
│     ├─ qa-report.json
│     ├─ review.json
│     └─ screenshots/
└─ delivery/
   ├─ final.html
   └─ final.pdf
```

`run.json`は現在状態とファイル位置を示す索引です。履歴は`events.jsonl`へ追記し、HTML/PDFの内容を`run.json`へ埋め込みません。

`approved-brief.json`の`content_contract`は、読者が得る判断・理解、必要な調査項目、必須論点、比較軸、掲載予定セクション、主要出典を保持します。`deck.json`の`context.content_coverage`は、その必須論点を実際のスライドIDへ結び付けます。`content-qa.json`は両者を照合した結果です。

## 状態

```text
created
questions_pending
confirmation_pending
approved
generating
qa
needs_revision
ready_for_review
complete
blocked
failed
cancelled
```

`complete`は人間が成果物を承認した後だけ設定します。

## 人間向けの識別

Run IDは内部識別子です。管理画面ではタイトル、概要、表紙サムネイル、更新日時、状態、次の操作を優先して表示します。`runs/index.json`、`runs/index.html`、`runs/latest.json`はRunから再生成可能な索引です。
