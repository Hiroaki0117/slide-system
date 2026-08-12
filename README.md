# Slide System

短い依頼と不完全な元資料から、毎回同じ制作ルールで読みやすいスライドを作るための仕様・ChatGPT Projectパッケージ・Claudeスキル・ローカルハーネスです。

現在は`warm_clean`を既定テーマとし、自己完結型HTMLとPDFを中心に検証しています。ChatGPT Free／Plus向けProject ZIPとClaude向けSkill ZIPを配布しています。ローカルハーネスはPhase 0〜8の実装を完了し、制作履歴、生成、QA、比較、AI間連携、配布検査まで一通り実行できます。

## 最初に選ぶもの

利用方法は4つあります。

| 利用方法 | 向いている人 | 現在の状態 |
|---|---|---|
| ChatGPT Project | PCを使わず、ChatGPT Free／PlusのProjectで作りたい | `v0.1.1`、モバイル表示QA対応 |
| Claude無料版スキル | 無料版Claudeの利用枠を節約しながら段階的に作りたい | `v0.2.16` |
| Claude有料版スキル | 00〜60を忠実に使い、全ページQAまで実行したい | `v0.1.3`、実機検証待ち |
| ローカルハーネス | CodexまたはClaude Codeで履歴、再開、比較、生成を管理したい | Phase 0〜8完了 |

ChatGPT／Claude向けZIPとローカルハーネスは併存します。AIのWeb／モバイル画面だけで完結したい場合は配布ZIPを使い、制作結果を継続的に保存・比較したい場合はハーネスを使います。

## ChatGPT Projectパッケージを使う

### 配布ファイル

`dist/slide-system-chatgpt-project-v0.1.1.zip`をChatGPT Free／Plusで共通利用します。パッケージには、Projectへ登録する5ファイル、Project Instructionsへ貼り付ける文章、iPad／iPhone向け説明書が入っています。

### iPadでの登録

1. ZIPをダウンロードし、「ファイル」アプリで展開します。
2. `PROJECT_INSTRUCTIONS.txt`をProject Instructionsへ貼り付けます。
3. `UPLOAD_TO_PROJECT/`内の5ファイルを同じProjectへ追加します。
4. 新しいチャットで短い依頼と手元の資料を送ります。
5. HTMLを確認した後、次のメッセージでPDFを依頼します。

Free／Plusの比較では同じProjectパッケージと段階納品を使用します。Plusだけ共有GPTや追加機能を使うと、料金プラン以外の条件が変わるためです。

## Claudeスキルを使う

### 配布ファイル

| ファイル | 内容 |
|---|---|
| `dist/slide-system-free-v0.2.16.zip` | 無料版向け。質問、構成確認、HTML先行納品、利用枠を意識した段階制作 |
| `dist/slide-system-paid-v0.1.3.zip` | 有料版向け。00〜60正本、全ページ検査、HTML/PDFの一括制作 |

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
- 静的・全ページ視覚・PDF・テーマQAの統合レポート
- QA FAIL時に直前Attemptを保持したまま修正Attemptを作成
- Codex・Claude Code向けの状態別再開指示を自動生成
- Run詳細画面でAttemptごとのHTML・PDF・QA・レビューを比較
- 利用者レビューを記録し、採用成果物だけを`delivery/`へ保存
- 研修・業務提案・自己完結型解説の汎用テストケース
- 利用者が採用した匿名Runだけをベースライン化し、成果物ハッシュを比較
- Claude Webへ渡すRun Bundleと、結果Bundleの安全な取り込み

Phase 0〜8は完了しています。今後は実案件でのRun蓄積、利用者が承認したベースライン、追加テーマ、有料版Claudeでの実機検証を反復します。

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

npm経由でも同じPythonハーネスを起動できます。別実装ではなく薄いコマンドラッパーです。

```powershell
npm.cmd run doctor
npx.cmd slide-system --project-root . run list
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
- Runごとの制作案履歴と比較リンク
- AttemptごとのQA・レビュー結果

Run IDは内部管理用です。普段はタイトル、サムネイル、更新日時、状態から探します。

ブラウザを自動で開かず、管理画面だけを更新する場合は次を使います。

```powershell
slide-system open --no-browser
```

生成された管理画面は`runs/index.html`です。`runs/`は個人の制作履歴を含むため、既定ではGit管理しません。

### 利用者レビューと最終保存

HTML/PDF確認後、`schemas/review.schema.json`に沿ったレビューJSONを記録します。

```powershell
slide-system review record run_20260810_001 `
  --file ".\review.json" `
  --owner codex
```

`accepted`なら採用AttemptのHTML/PDFを`delivery/final.*`へコピーし、Runを完了します。`needs_revision`なら既存Attemptを残したまま修正状態へ戻します。

### 承認済みベースライン

完了Runを比較基準として保存します。未承認の試作は登録できません。

```powershell
slide-system baseline approve run_20260810_001 `
  --case-id business-proposal `
  --approver "Hiroaki"
```

別のRunまたはAttemptと比較します。

```powershell
slide-system baseline compare run_20260810_002 `
  --baseline ".\baselines\business-proposal\warm_clean-1_0_0\baseline.json"
```

画像ハッシュの変化は自動的に品質低下とは断定しません。`CHANGED`として提示し、コンタクトシートを人が確認します。

### Claude Web Bundle

Claude Webへ依頼・添付・承認済みBrief・最新deckを渡すZIPを作ります。

```powershell
slide-system bundle export run_20260810_001 `
  --output ".\exports\run-bundle.zip"
```

Claude Webから返されたResult Bundleは新しいAttemptへ取り込みます。

```powershell
slide-system bundle import run_20260810_001 `
  --file ".\downloads\result-bundle.zip" `
  --owner codex
```

取り込んだHTML/PDFは`imported/`へ参考保存され、最終成果物としては扱いません。`deck.json`からローカルでHTML/PDFを再生成し、統合QAを通します。ZIP内の危険なパス、シンボリックリンク、未許可ファイル、過大なファイルは拒否します。

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

QAがFAILした場合は、直前の成果物を上書きせず修正Attemptを作ります。

```powershell
slide-system attempt revise run_20260810_001 `
  --reason "QAで見つかった文字あふれを修正" `
  --owner codex
```

`--deck`を省略すると直前の`deck.json`を複製し、Attempt番号だけ安全に更新します。

### Codex・Claude Codeで再開する

別セッションの開始時には、現在のRun状態に合う再開指示を生成します。

```powershell
slide-system adapter prepare run_20260810_001 --adapter codex
slide-system adapter prepare run_20260810_001 --adapter claude-code
```

生成先は各Runの`.state/resume-codex.md`または`.state/resume-claude-code.md`です。チャット履歴ではなく、`run.json`、承認済みBrief、最新Attempt、QAレポートを読む順番と、現在省略してはいけない承認ゲートが記載されます。

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
python scripts/test_free_package_generic.py dist/slide-system-free-v0.2.16.zip
python scripts/test_paid_package_contract.py dist/slide-system-paid-v0.1.3.zip
python scripts/test_chatgpt_project_package.py dist/slide-system-chatgpt-project-v0.1.1.zip
python scripts/test_harness_phase0.py
python scripts/test_harness_phase1.py
python scripts/test_harness_phase2.py
python scripts/test_harness_phase3.py
python scripts/test_harness_phase4.py
python scripts/test_harness_phase5.py
python scripts/test_harness_phase6.py
python scripts/test_harness_phase7.py
```

リリース前の全検査は1コマンドで実行できます。

```powershell
python scripts/release_check.py
```

Node.jsモジュールが通常とは異なる場所にある環境では、`NODE_PATH`の指定が必要になる場合があります。

## 配布ZIPの再生成

ChatGPT Project、Claude無料版、Claude有料版をまとめて再生成し、SHA-256付きマニフェストを更新します。

```powershell
python scripts/build_release.py --replace
```

生成物とハッシュは`dist/release-manifest.json`で確認できます。生成後は`python scripts/release_check.py`を実行してください。

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
4. 自動QAと修正ループ（完了）
5. Codex・Claude Codeアダプター（完了）
6. ローカル管理画面の成果物・比較機能（完了）
7. 複数題材のテストケースとベースライン（完了）
8. Claude WebとのBundle連携（完了）
9. npm配布ラッパーとリリース自動化（完了）

詳細は`docs/harness/ROADMAP.md`を参照してください。
