# Harness Test Result — Sub4 Roadmap

## 実施情報

- 実施日: 2026-08-10
- Run ID: `run_20260810_001`
- 題材: 下関海響マラソン2026 サブ4ロードマップ
- 入力: `REQUEST.md`の短い依頼文と、`source/RUNNING_NOTES.md`の粗い利用者メモ
- テスト条件: 現在の脛の状態は「軽い違和感がある程度」と回答した再現用シナリオ
- 最終Attempt: `006`
- 最終状態: `complete`

このテストはハーネスの再現性確認用です。記録した症状はテスト条件であり、利用者の現在の医学的状態を示すものではありません。

## 確認できたフロー

1. 短い依頼文と粗いメモをRunへ登録
2. 脛の状態をブロッキング質問として記録
3. 制作条件と14枚の構成を提示
4. 承認済みBriefを保存
5. HTMLを生成
6. PDF生成の承認文を記録
7. 全ページ画像、コンタクトシート、PDF、統合QAを生成
8. 自動QA後に人の目で確認
9. 修正前Attemptを残したまま新しいAttemptを作成
10. 採用したHTML/PDFを`delivery/final.*`へ保存

## Attempt履歴

| Attempt | 結果 | 発見・対応 |
|---|---|---|
| 001 | 静的QA FAIL | v1から旧形式への変換で`claim_evidence`、`dated_roadmap`、`timeline`が欠落していた。変換処理を修正 |
| 002 | 静的QA FAIL | 根拠マッピングの表示文と実スライド文に助詞1文字の差があった。完全一致へ修正 |
| 003 | 自動QA PASS／人の確認 NG | 3枚目の巨大メッセージが細かく折り返され、視覚階層が崩れていた |
| 004 | 描画失敗 | 実行シェルからPlaywright依存先が見えなかった。Codex付属依存先を明示 |
| 005 | QA PASS・警告1 | 3枚目を「現在／開始条件」の2列へ変更。比較レイアウトの反復理由が一部未記録 |
| 006 | QA PASS・警告0 | 全比較ページに反復理由を記録し、最終採用 |

## 最終QA

- static: PASS
- visual: PASS
- pdf_parity: PASS
- theme: PASS
- warning: 0
- ページ数: 14
- Attempt 005と006の全14ページ画像ハッシュ: 完全一致
- 人の目による全ページ確認: 文字切れ、重なり、不自然な折り返しなし

## ハーネスへ反映した改善

### 高ステークス情報の変換保持

`src/slide_system/legacy.py`で次を旧形式へ引き継ぐよう修正した。

- `claim_evidence`
- `dated_roadmap`
- `timeline`
- `visual.repeat_reason`

回帰テスト: `scripts/test_high_stakes_conversion.py`

### 巨大メッセージの折り返し検出

自動QAが3枚目の見た目の悪さを見逃したため、`single_message`の大見出しが4行以上になる場合を`SINGLE_MESSAGE_WRAP`として失敗させるようにした。

回帰テスト: `scripts/test_single_message_visual_qa.py`

## 最終成果物

- HTML: `runs/run_20260810_001/delivery/final.html`
- PDF: `runs/run_20260810_001/delivery/final.pdf`
- QA: `runs/run_20260810_001/attempts/006/qa-report.json`
- 人のレビュー: `runs/run_20260810_001/attempts/006/review.json`

`runs/`は利用者固有の制作履歴を含むためGit管理対象外。テスト結果と回帰テストだけをリポジトリへ残す。
