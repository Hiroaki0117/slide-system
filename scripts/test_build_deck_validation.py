#!/usr/bin/env python3
"""Regression checks for generic slide-system validation."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "slide-system" / "scripts" / "build_deck.py"
SPEC = importlib.util.spec_from_file_location("slide_system_build_deck", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_deck() -> dict:
    constraint = "個人情報を含む原文は外部ツールへ入力しない"
    return {
        "deck_title": "問い合わせ対応の改善計画",
        "audience": "カスタマーサポート部門の責任者",
        "purpose": "安全な試行条件を確認し、90日間の改善計画を判断する",
        "mode": "standalone",
        "high_stakes": True,
        "dated_roadmap": True,
        "timeline": {
            "current_date": "2026-08-07",
            "target_date": "2026-11-05",
            "duration_text": "残り90日",
            "slide": 3
        },
        "safety": {
            "current_condition": "個人情報を含む問い合わせを扱う",
            "limitations": ["法務確認前は本番データを使わない"],
            "stop_conditions": ["個人情報の外部送信が検知された場合は試行を停止する"],
            "plan_status": "provisional",
            "plan_status_text": "本計画は法務確認前の暫定案",
            "clearance_condition": "法務確認後に本番データで開始する",
            "status_slide": 2,
            "critical_constraints": [
                {"text": constraint, "slide": 4}
            ]
        },
        "claim_evidence": [
            {
                "claim": "現行規程では外部送信を制限する",
                "visible_text": "外部サービスへの送信は事前承認が必要です。",
                "slide": 2,
                "basis_type": "authoritative_source",
                "source_ids": ["S1"],
                "support": "社内規程の事前承認要件",
                "evidence_design": "official_rule",
                "claim_strength": "fact"
            },
            {
                "claim": "個人情報を外部ツールへ入力しない",
                "visible_text": constraint,
                "slide": 4,
                "basis_type": "authoritative_source",
                "source_ids": ["S1"],
                "support": "社内規程の外部送信制限",
                "evidence_design": "official_rule",
                "claim_strength": "recommendation"
            }
        ],
        "slides": [
            {
                "layout": "cover",
                "title": "問い合わせ対応の改善計画",
                "date": "2026-08-07"
            },
            {
                "layout": "text_focus",
                "job": "claim",
                "visual_role": "none",
                "visual_reason": "暫定状態と根拠を短く確認するページ",
                "title": "本番データの利用には事前確認が必要です",
                "lead": "本計画は法務確認前の暫定案",
                "bullets": [
                    "外部サービスへの送信は事前承認が必要です。",
                    "法務確認後に本番データで開始する"
                ],
                "source": "出典: [S1]"
            },
            {
                "layout": "process",
                "job": "explain",
                "visual_role": "explain",
                "title": "残り90日を3段階に分けます",
                "lead": "残り90日",
                "steps": [
                    {"label": "1–30日", "title": "整理", "body": "対象と評価指標を決める"},
                    {"label": "31–60日", "title": "試行", "body": "匿名データで小さく試す"},
                    {"label": "61–90日", "title": "判断", "body": "結果とリスクを確認する"}
                ]
            },
            {
                "layout": "decision_flow",
                "job": "instruction",
                "visual_role": "explain",
                "title": "データ条件を満たしてから試行します",
                "question": constraint,
                "yes_label": "守れる",
                "yes_action": "匿名化したデータで試行を開始する",
                "no_label": "守れない",
                "no_action": "試行を停止し、方法を見直す",
                "source": "出典: [S1]"
            },
            {
                "layout": "sources_appendix",
                "title": "出典",
                "sources": [
                    {
                        "id": "S1",
                        "title": "情報管理規程",
                        "publisher": "依頼者提供",
                        "url": "https://example.com/policy",
                        "checked": "2026-08-07"
                    }
                ]
            }
        ]
    }


def codes(deck: dict) -> set[str]:
    return {issue["code"] for issue in MODULE.validate(deck) if issue["level"] == "FAIL"}


def main() -> int:
    good = valid_deck()
    assert not codes(good), codes(good)

    hidden = copy.deepcopy(good)
    hidden["slides"][3]["question"] = "別の条件"
    assert "CRITICAL_CONSTRAINT_NOT_VISIBLE" in codes(hidden)

    unsupported = copy.deepcopy(good)
    unsupported["claim_evidence"][0]["source_ids"] = []
    assert "MISSING_CLAIM_SOURCE" in codes(unsupported)

    causal = copy.deepcopy(good)
    causal["claim_evidence"][0]["evidence_design"] = "observational"
    causal["claim_evidence"][0]["claim_strength"] = "causal"
    assert "CAUSAL_OVERCLAIM" in codes(causal)

    unrelated = copy.deepcopy(good)
    unrelated["slides"][2]["source"] = "出典: [S1]"
    assert "UNMAPPED_SLIDE_SOURCE" in codes(unrelated)

    wrong_duration = copy.deepcopy(good)
    wrong_duration["timeline"]["duration_text"] = "残り89日"
    wrong_duration["slides"][2]["lead"] = "残り89日"
    assert "TIMELINE_DAY_MISMATCH" in codes(wrong_duration)

    dense_process = copy.deepcopy(good)
    dense_process["slides"][2]["lead"] = "長" * 121
    assert "PROCESS_LEAD_DENSITY" in codes(dense_process)

    duplicate_process = copy.deepcopy(good)
    duplicate_process["slides"][2]["steps"][0]["body"] = duplicate_process["slides"][2]["steps"][0]["title"]
    assert "DUPLICATE_PROCESS_COPY" in codes(duplicate_process)

    dense_comparison = copy.deepcopy(good)
    dense_comparison["slides"].insert(3, {
        "layout": "comparison",
        "job": "compare",
        "visual_role": "evidence",
        "title": "選択肢を比較します",
        "columns": [
            {"heading": "A", "body": "長" * 121},
            {"heading": "B", "body": "短い説明"}
        ]
    })
    assert "COMPARISON_COLUMN_DENSITY" in codes(dense_comparison)

    revision_state = {
        "phase": "revision_approved",
        "revision": {
            "source_artifact": "existing.html",
            "scope": "見出しを1件修正",
            "user_reply": "見出しを修正してください"
        }
    }
    assert not MODULE.validate_approval(revision_state)
    revision_state["revision"]["scope"] = ""
    assert MODULE.validate_approval(revision_state)[0]["code"] == "REVISION_NOT_APPROVED"

    print("PASS: generic build_deck validation regression checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
