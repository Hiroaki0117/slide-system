# ハーネス構成

## 目的

Slide System Harnessは、Claude CodeとCodexが同じ制作データを使い、HTML/PDFの生成、QA、履歴保存、再開を共通化するためのローカル実行基盤です。Claude Web向けの配布ZIPは残し、ハーネスとは別の利用経路として扱います。

## 基本原則

- 00〜60を正規仕様とし、アダプターへ手作業で複製しない。
- `deck.json`を編集可能な内容の正本とし、HTML/PDFは生成物として扱う。
- 内容判断はAI、再現可能な生成と検査はハーネスが担当する。
- 題材固有の知識を共通ハーネスやデザインパックへ入れない。
- 自動QAのPASSだけで完成にせず、人間の承認後に`complete`とする。
- 完了済みRunは変更せず、修正は子Runとして残す。

## 技術境界

```text
Codex / Claude Code / Claude Web bridge
                  ↓
              adapters
                  ↓
        Python control plane
     Run / schema / build / index
                  ↓
       Node.js render worker
 Playwright / screenshots / PDF / visual QA
```

PythonはRun管理、スキーマ、HTML生成、CLI、管理画面を担当します。Node.jsはブラウザが必要な処理だけを担当します。既存のPythonビルダーとNode.jsレンダラーは、互換層を設けながら段階的に移行します。

## 主なディレクトリ

```text
specs相当             00_MASTER.md〜60_QA.md
src/slide_system/     ハーネス制御層
schemas/              共通JSON Schema
designs/              デザインパック（Phase 2で追加）
harness/adapters/     AI別アダプター
runs/                 ローカル制作履歴（Git対象外）
baselines/            承認済み比較基準
skills/               Claudeスキルの共通資産
variants/             Claude無料版・有料版の差分
dist/                 配布ZIP
```

## 現在の移行境界

`skills/slide-system/assets/deck-schema-example.json`は既存ビルダー用の形式です。`schemas/deck.schema.json`はハーネスv1の共通形式です。Phase 2で変換層を追加するまで、両者を同じ形式として扱いません。
