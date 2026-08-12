# Mobile Cross-Platform Test 01 — Internal Training

PCを持たず、iPadとiPhoneだけを使うAI初心者が、短い依頼と走り書きから研修スライドを完成できるかを比較するテストです。

## 比較対象

- ChatGPT Free
- ChatGPT Plus
- Claude Free
- Claude Pro

4環境には同じ`common/REQUEST.md`と`common/SOURCE_NOTES.md`を渡します。仕様・依頼・期待条件は共通にし、生成物と実行記録だけを環境別に保存します。

## 現在の実行準備

| 環境 | 使用物 | 状態 |
|---|---|---|
| ChatGPT Free | `dist/release-manifest.json`記載のChatGPT Projectパッケージ | 実行可能 |
| ChatGPT Plus | Freeと同じChatGPT Projectパッケージ | 実行可能 |
| Claude Free | `dist/release-manifest.json`記載の無料版Skill ZIP | 実行可能 |
| Claude Pro | `dist/release-manifest.json`記載の有料版Skill ZIP | 実行可能 |

ChatGPT Free／Plusでは同じProjectパッケージを使用します。00〜60を個別にアップロードして代用すると、モバイル導入とファイル数の比較条件が変わるため行いません。

## 比較の原則

- AIへ送る依頼文を環境ごとに改善しない
- 最初の成果物が出るまで、追加のデザイン指示を送らない
- 不足確認への回答は、4環境で同じ内容にする
- HTMLとPDFは環境ごとに別ファイルとして保存する
- iPadを主制作端末、iPhoneを再開・確認端末とする
- PCやローカルコマンドを利用者の操作手順へ含めない
- ハーネスによるQAは評価者側で実施し、利用者には要求しない

## 実行順

順番による評価の甘辛を抑えるため、推奨順は次のとおりです。

1. ChatGPT Free
2. Claude Free
3. ChatGPT Plus
4. Claude Pro

各環境では`profiles/`の手順だけを参照し、他環境の成果物を見せません。

## 保存先

成果物は次の名前で`results/`配下へ保存します。

```text
results/
├─ chatgpt-free/
├─ chatgpt-plus/
├─ claude-free/
└─ claude-pro/
```

各フォルダにはHTML、PDF、会話記録、`RESULT.md`を保存します。評価方法は`EVALUATION.md`、記録形式は`results/RESULT_TEMPLATE.md`を使用します。
