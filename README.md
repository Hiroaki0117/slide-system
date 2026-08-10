# Slide System

短い依頼と不完全な元資料から、毎回同じ制作ルールで読みやすいスライドを作るための仕様・Claudeスキル・ローカルハーネスです。

現在は`warm_clean`を既定テーマとし、自己完結型HTMLとPDFを中心に検証しています。Claude向け配布ZIPは利用可能です。ローカルハーネスはPhase 2まで完了し、制作履歴、承認済みBrief、Attempt・Step、再開、HTML/PDF生成まで実装しています。

## 最初に選ぶもの

利用方法は3つあります。

| 利用方法 | 向いている人 | 現在の状態 |
|---|---|---|
| Claude無料版スキル | 無料版Claudeの利用枠を節約しながら段階的に作りたい | `v0.2.13`で一区切り |
| Claude有料版スキル | 00〜60を忠実に使い、全ページQAまで実行したい | `v0.1.0`、実機検証待ち |
| ローカルハーネス | CodexまたはClaude Codeで履歴、再開、比較、生成を管理したい | Phase 2完了 |

Claude向けZIPとローカルハーネスは併存します。Claude Webだけで完結したい場合はZIPを使い、制作結果を継続的に保存・比較したい場合はハーネスを使います。

## Claudeスキルを使う

### 配布ファイル

| ファイル | 内容 |
|---|---|
| `dist/slide-system-free-v0.2.13.zip` | 無料版向け。質問、構成確認、HTML先行納品、利用枠を意識した段階制作 |
| `dist/slide-system-paid-v0.1.0.zip` | 有料版向け。00〜60正本、全ページ検査、HTML/PDFの一括制作 |

過去のZIPも`dist/`に残していますが、通常は上記の最新版を使用してください。

### 登録手順

1. GitHubからリポジトリまたは対象ZIPをダウンロードします。
2. Claudeの`Customize > Skills`を開きます。
3. 無料版または有料版のZIPをアップロードします。
4. コード実行とファイル作成が有効であることを確認します。
5. 新しいチャットで対象スキルだけを有効にします。
6. 普段どおりの短い依頼文と、手元にある資料を渡します。

比較テストでは、ZIPと同時に00〜60を別添付しません。二重の指示で挙動が変わるのを防ぐためです。

### 最小の依頼例

```text
添付した記事をもとに、初心者向けのスライドを作ってください。
社内勉強会で使用します。
```

AI向けに完璧な依頼文を準備する必要はありません。不足情報を質問し、制作条件と構成を確認してから進むこと自体がテスト対象です。

### 無料版の納品順

無料版は利用枠を考慮し、原則として次の順番で進みます。

```text
必要な質問
  → 制作内容の確認
  → HTML下書き
  → 利用者の確認
  → 必要な場合だけPDF
```

相談や意見確認だけで制作を始めず、制作内容の明示的な承認を必要とします。

## ローカルハーネスを使う

### 現在できること

- 新しい制作記録（Run）の作成
- タイトル、概要、タグ、利用AIの保存
- 最近の制作一覧
- Run IDだけでなくタイトルの一部による検索
- 最後に使ったRunの確認
- 別セッションでの再開位置表示
- ブラウザで見るローカル管理画面
- `run.json`と`events.jsonl`の安全な保存
- 7種類のJSON Schemaによる実検証
- 制作条件と構成案の承認記録
- AttemptとStepの作成・完了記録
- Run単位の同時編集ロック
- 更新前の`run.json`バックアップ
- 仕様、設定、フォントのハッシュ記録
- 決定的生成物用のローカルキャッシュ
- QA、成果物、利用者承認がない完了操作の拒否
- `warm_clean`デザインパックの読み込みと検証
- ハーネスv1 `deck.json`から既存ビルダー形式への変換
- Attempt単位の自己完結型HTML生成
- 全ページ画像、コンタクトシート、PDFの生成
- HTML確認後だけPDFへ進む明示的な承認ゲート

次は静的QA、全ページ描画結果、PDF比較を1つのQAレポートへ統合し、修正が必要な場合は新しいAttemptへ進むループを実装します。

### 必要な環境

- Python 3.11以上
- Node.js 20以上
- Git
- ChromiumまたはPlaywright管理ブラウザ

PythonはRun管理と生成制御、Node.jsはPlaywrightによる描画とPDF処理に使用します。

### 開発版のセットアップ

PowerShellでリポジトリを開きます。

```powershell
cd "C:\Users\Hiroaki Nishimura\Documents\slide-system"
python -m pip install -e .
npm.cmd install
npx.cmd playwright install chromium
```

PowerShellの設定によって`npm`や`npx`が実行できない場合は、上記のように`npm.cmd`と`npx.cmd`を使用してください。

環境を確認します。

```powershell
slide-system doctor
```

インストールせずに開発中のコードを試す場合は、次の形式でも実行できます。

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m slide_system doctor
```

### 新しい制作記録を作る

```powershell
slide-system run new `
  --title "新入社員向けセキュリティ研修" `
  --summary "社内研修で使用する基礎教材" `
  --tag "研修" `
  --tag "セキュリティ" `
  --adapter codex
```

依頼文をMarkdownで用意している場合は、`--request`で登録できます。

```powershell
slide-system run new `
  --title "問い合わせ対応の改善提案" `
  --request ".\request.md" `
  --adapter claude-code
```

### 過去の制作を探す

```powershell
slide-system run list
```

タイトルの一部でも探せます。

```powershell
slide-system run status "セキュリティ"
```

一番最近の制作はRun IDを覚えなくても確認できます。

```powershell
slide-system run resume --latest
```

候補が複数ある場合は、勝手に選ばず候補のタイトルとRun IDを表示します。

### ローカル管理画面

```powershell
slide-system open
```

ブラウザに次を表示します。

- 制作タイトル
- 概要
- 更新日時
- 現在の状態
- 使用したAI
- デザイン
- 次に必要な操作
- HTML/PDFへのリンク（生成後）
- 表紙サムネイル（生成後）

Run IDは内部管理用です。普段はタイトル、サムネイル、更新日時、状態から探します。

ブラウザを自動で開かず、管理画面だけを更新する場合は次を使います。

```powershell
slide-system open --no-browser
```

生成された管理画面は`runs/index.html`です。`runs/`は個人の制作履歴を含むため、既定ではGit管理しません。

### エージェント・開発者向けの状態管理

通常、以下のコマンドはCodexまたはClaude Codeが実行します。初心者が状態名やAttempt番号を覚える必要はありません。

JSONを共通スキーマで検証します。

```powershell
slide-system validate run ".\runs\run_20260810_001\run.json"
```

承認済みBriefを登録します。

```powershell
slide-system brief approve run_20260810_001 `
  --file ".\approved-brief.json" `
  --owner codex
```

新しい制作候補を作ります。

```powershell
slide-system attempt new run_20260810_001 `
  --deck ".\deck.json" `
  --reason "初稿" `
  --owner codex
```

承認済みBriefとAttemptを作成した後、HTMLを生成します。

```powershell
slide-system build run_20260810_001 --owner codex
```

HTMLを確認してPDFも必要と判断した場合だけ、承認文を明示して描画します。

```powershell
slide-system render run_20260810_001 `
  --owner codex `
  --pdf-approval "HTML確認済み。PDF生成を承認します"
```

`render`は全ページ画像、コンタクトシート、PDFを最新Attemptへ保存します。承認文がない場合はPDFを生成しません。

個別工程を記録します。

```powershell
slide-system step start run_20260810_001 --name validate_deck --owner codex
slide-system step finish run_20260810_001 --step-id step-001 --owner codex
```

状態変更は定義済みの順序だけを許可します。完了済みRunは変更できません。

## ハーネスの完成形

標準フローは次のとおりです。

```text
依頼・添付資料
  → 事前検査と質問
  → 制作条件・構成案の承認
  → deck.json
  → 構造QA
  → HTML
  → 全ページ視覚QA
  → HTML確認
  → PDF
  → 最終QA
  → 人間の承認
  → 保存・比較
```

自動QAがPASSしても完成にはしません。利用者が内容と見た目を承認した後にRunを`complete`とします。

## 制作履歴

1件の制作はRunとして保存します。

```text
runs/
└─ run_YYYYMMDD_NNN/
   ├─ run.json
   ├─ events.jsonl
   ├─ input/
   ├─ brief/
   ├─ attempts/
   └─ delivery/
```

- Run: 目的と実行条件が固定された制作単位
- Attempt: 内容やデザインを修正した候補
- Step: HTML生成、描画、PDF生成、QAなどの個別処理

チャット履歴ではなくRunのファイルを読むため、CodexやClaude Codeの別セッションから再開できます。

## 00〜60の正規仕様

| ファイル | 役割 |
|---|---|
| `PROJECT_INSTRUCTIONS.md` | Claudeプロジェクトで毎回行う動作 |
| `00_MASTER.md` | 制作工程、優先順位、既定値 |
| `10_CONTENT.md` | 構成、文章、情報量 |
| `20_DESIGN.md` | 色、文字、余白、トンマナ |
| `30_LAYOUTS.md` | レイアウトタイプと選択条件 |
| `40_VISUALS.md` | 写真、イラスト、図解、グラフ、表 |
| `50_OUTPUTS.md` | HTML、PPTX、PDFの出力ルール |
| `60_QA.md` | 制作前確認、検査、修正、完成判定 |

有料版Claudeスキルには00〜60の正本をそのまま同梱します。無料版は利用枠に合わせて手順を圧縮しますが、題材固有の知識は固定しません。

## 設計文書

ハーネスの詳しい設計は`docs/harness/`にあります。

- `ARCHITECTURE.md`: 技術境界と責任分担
- `DATA_MODEL.md`: Run、Attempt、Step
- `PIPELINE.md`: 質問から納品までの流れ
- `QA.md`: PASS/FAILの考え方
- `ADAPTERS.md`: Codex、Claude Code、Claude Web
- `ROADMAP.md`: 実装順序

共通JSON Schemaは`schemas/`に置きます。

## リポジトリ構成

```text
slide-system/
├─ 00_MASTER.md〜60_QA.md     正規仕様
├─ PROJECT_INSTRUCTIONS.md    Claudeプロジェクト指示
├─ src/slide_system/          ローカルハーネス
├─ schemas/                   共通JSON Schema
├─ docs/harness/              ハーネス設計
├─ skills/slide-system/       Claudeスキル共通資産
├─ variants/                  無料版・有料版の差分
├─ scripts/                   ZIP生成と回帰テスト
├─ test-cases/                実利用に近い検証
├─ dist/                      配布ZIP
└─ runs/                      ローカル制作履歴（Git対象外）
```

## デザインの拡張

初期テーマは`warm_clean`です。背景`#FFF8F4`を中心とした、温かく清潔感のあるデザインです。

ハーネスでは、内容、レイアウト、デザインテーマ、レンダラーを分離します。将来のテーマ追加では既存テーマを直接コピーして題材固有ルールを加えるのではなく、共通のデザインパック契約に従います。

第2テーマは、`warm_clean`のデザインパック化と拡張テンプレートが完成してから追加します。資料の題材だけでテーマを自動変更しません。

## テスト

主テストは、AIに詳しくない利用者の使い方を再現します。1〜2文の自然な依頼と、走り書き程度の添付資料を使用し、完璧なプロンプトを入力しません。

現在の回帰テストは次のように実行できます。

```powershell
python scripts/test_build_deck_validation.py
python scripts/test_artifact_recovery.py
python scripts/test_fast_pdf_export.py
python scripts/test_free_turn_gate_contract.py
python scripts/test_free_package_generic.py dist/slide-system-free-v0.2.13.zip
python scripts/test_paid_package_contract.py dist/slide-system-paid-v0.1.0.zip
python scripts/test_harness_phase0.py
python scripts/test_harness_phase1.py
python scripts/test_harness_phase2.py
```

Node.jsモジュールが通常とは異なる場所にある環境では、`NODE_PATH`の指定が必要になる場合があります。

## 配布ZIPの再生成

無料版の例です。

```powershell
python scripts/build_skill_package.py `
  --base skills/slide-system `
  --variant variants/slide-system-free `
  --output dist/slide-system-free-v0.2.13.zip `
  --root-name slide-system-free `
  --replace
```

有料版では`--canonical-spec-root .`を追加し、00〜60の正本を同梱します。生成後は必ず対応するパッケージ契約テストを実行してください。

## Gitとプライバシー

GitHubで管理するもの：

- 00〜60
- ハーネスとスキーマ
- Claudeスキル
- 匿名化したテストケース
- 承認済みベースライン
- QA・比較形式

原則としてGitHubへ入れないもの：

- 個人の依頼文
- 未加工の添付資料
- すべての途中HTML/PDF
- 全スクリーンショット
- キャッシュ
- APIキーや認証情報

`runs/`、`.cache/`、`.state/`は`.gitignore`に含まれます。

## トラブルシューティング

### `slide-system`が見つからない

```powershell
python -m pip install -e .
```

または次を使用します。

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m slide_system doctor
```

### Node.jsが見つからない

Node.js 20以上をインストールし、PowerShellを開き直してから確認します。

```powershell
node --version
```

### Playwrightのブラウザがない

```powershell
npx.cmd playwright install chromium
```

### 前回の制作が分からない

```powershell
slide-system open
```

または次を使います。

```powershell
slide-system run resume --latest
```

### PDFだけを修正したい

PDFは編集データの正本ではありません。`deck.json`またはハーネス生成HTMLがあればそこから再開します。PDFしかない場合は、完全復元ではなく新しいRunでの再構築になります。

## ロードマップ

1. Run、Attempt、Stepと再開処理（基本機能完了）
2. `warm_clean`デザインパック（完了）
3. ハーネスv1 `deck.json`からHTML/PDF生成（完了）
4. 自動QAと修正ループ
5. Codex・Claude Codeアダプター
6. ローカル管理画面の成果物・比較機能
7. 複数題材のテストケースとベースライン
8. Claude WebとのBundle連携
9. npm配布ラッパーとリリース自動化

詳細は`docs/harness/ROADMAP.md`を参照してください。
