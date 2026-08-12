# Claude Code adapter

このファイルはClaude Code固有の薄い入口です。制作判断は00〜60、Run状態、承認済みBrief、最新Attemptに従います。

- 作業前に`slide-system adapter prepare <Run> --adapter claude-code`の出力を読む。
- 質問・制作内容確認・PDF生成・最終採用の各承認ゲートを省略しない。
- 制作内容確認では、目的に必要な調査項目、重要論点、比較軸、掲載予定セクション、主要出典を`content_contract`として提示する。
- 承認後の`deck.json`には`context.content_coverage`を記録し、必須論点を掲載したスライドIDと結び付ける。
- `deck.json`を内容の正本とし、HTML/PDFを直接修正しない。
- QA FAIL時は既存Attemptを上書きせず`attempt revise`で新しいAttemptを作る。
- 完了済みRunは変更せず、必要なら子Runとして扱う。
