# Slide System for ChatGPT Projects

ChatGPT Free／PlusのProjectへ、iPadまたはiPhoneだけでSlide Systemを設定するためのパッケージです。FreeとPlusの比較条件を揃えるため、どちらも同じファイルを使用します。

## パッケージの中身

- `PROJECT_INSTRUCTIONS.txt`: Project Instructionsへ貼り付ける文章
- `UPLOAD_TO_PROJECT/`: Projectへ登録する5ファイル
- `PACKAGE_MANIFEST.json`: バージョンと収録ファイルの確認用

`README_MOBILE.md`、`PROJECT_INSTRUCTIONS.txt`、`PACKAGE_MANIFEST.json`はProjectへアップロードしません。

## iPadでの設定

1. GitHubから`slide-system-chatgpt-project-*.zip`をダウンロードします。
2. 「ファイル」アプリでZIPをタップして展開します。
3. `PROJECT_INSTRUCTIONS.txt`を開き、本文をすべてコピーします。
4. ChatGPTで新しいProjectを作成します。
5. Project Instructionsへコピーした文章を貼り付けます。
6. `UPLOAD_TO_PROJECT`内の5ファイルをすべてProjectへ追加します。
7. 新しいチャットで、普段どおりの短い依頼と手元の資料を送ります。

アプリにProject Instructionsの編集項目が見つからない場合は、iPadのSafariでChatGPTを開いて確認します。モバイル画面の名称や位置は更新される可能性があるため、説明書と実画面が違う場合はテスト結果へ記録してください。

## iPhoneでの利用

iPadで作成した同じProjectを開き、会話の続き、HTML/PDFの確認、短い修正依頼に使用します。初回設定をiPhoneだけで完了できるかも比較対象ですが、操作しにくい場合は無理に成功扱いせず記録してください。

## 最初の依頼例

```text
新入社員向けに、社内チャットの基本的な使い方を説明するスライドを作ってください。
詳しい構成は分からないので、必要なことがあれば先に聞いてください。
```

AI向けに出力形式、テーマ、枚数、レイアウトを指定する必要はありません。必要な確認、制作条件、構成案をChatGPTが提示すること自体がパッケージの役割です。

## 基本の納品順

```text
必要な質問
  → 制作条件と構成の確認
  → 明示的な承認
  → HTML下書き
  → 利用者の確認
  → PDF依頼
  → PDFと最終HTML
```

Free／Plusとも、この順序を使用します。Plusだけ一括制作へ変更すると、料金プランと制作方式の差が混ざるためです。

## 困ったとき

- ファイルを5つ登録できない: 古いProjectファイルを削除し、5ファイルをまとめて選び直します。
- 質問なしで制作を始めた: チャットを止め、`01_PROJECT_RULES.md`を読み直すよう伝えます。
- HTMLがコード本文で表示された: コードではなくダウンロード可能な`.html`ファイルとして作成するよう伝えます。
- PDFまで一度に進んだ: 比較テストでは失敗として記録し、新しいチャットで再実行します。
- 利用上限に達した: 新しいProjectや依頼文を作り直さず、同じProjectで上限回復後に再開します。

