# ChatGPT Free 実行プロファイル

## 目的

ChatGPT FreeのProjectを使い、iPadとiPhoneだけで初期設定から成果物保存まで完了できるかを確認します。

## 条件

- 新規Projectを作成する
- `dist/release-manifest.json`に記載されたChatGPT Projectパッケージを使用する
- ZIP内の`PROJECT_INSTRUCTIONS.txt`をProject Instructionsへ貼り付ける
- ZIP内の`UPLOAD_TO_PROJECT`にある5ファイルをProjectへ登録する
- 共通仕様パッケージは5ファイル以内とする
- `common/REQUEST.md`の本文を最初のメッセージとして送る
- `common/SOURCE_NOTES.md`だけを利用者資料として添付する
- 共有GPTは使用しない

## 実行

1. iPadでProjectを作成する
2. Project Instructionsと5つの仕様ファイルを登録する
3. 依頼文を送る
4. 最初の質問には`common/CLARIFICATION_ANSWERS.md`の該当部分だけで回答する
5. 構成確認と承認待ちが行われるか記録する
6. 明示的に制作を承認し、HTMLが得られるまで待つ
7. HTML確認後にPDFを依頼する
8. iPhoneで同じProjectを開き、会話と成果物へアクセスできるか確認する

## 追加記録

- ファイル登録上限またはツール上限に到達したか
- 上限到達時に途中成果物と再開方法が残ったか
- Project作成から依頼送信までの操作が初心者にも理解できるか
