# Claude Free 実行プロファイル

## 目的

Claude Freeへ無料版Skill ZIPを登録し、iPadとiPhoneだけで成果物を取得できるかを確認します。

## 条件

- `dist/release-manifest.json`に記載された最新の無料版Skill ZIPを使用する
- Code execution and file creationを有効にする
- Skillを有効にした新規チャットで実行する
- `common/REQUEST.md`と`common/SOURCE_NOTES.md`を変更しない
- 別途`00〜60`を添付しない

## 実行

1. iPadでSkill ZIPを登録できるか確認する
2. 登録できない場合は、iPadのブラウザ版でも試し、結果を`environment`として記録する
3. 新規チャットで利用者資料を添付し、依頼文を送る
4. 最初の質問には`common/CLARIFICATION_ANSWERS.md`の該当部分だけで回答する
5. 構成確認と承認待ちが行われるか記録する
6. 明示的に制作を承認し、HTMLが得られるまで待つ
7. HTML確認後、次のターンでPDFを依頼する
8. iPhoneで会話と成果物へアクセスできるか確認する

## 追加記録

- Skill ZIPをモバイルだけで登録できたか
- HTML生成前またはPDF生成前に上限へ到達したか
- 上限到達時に、次のセッションで再開できる情報が残ったか
