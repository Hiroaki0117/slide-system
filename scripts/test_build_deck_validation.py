#!/usr/bin/env python3
"""Regression checks for slide-system static content validation."""

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
    duration = "88日（約13週間）"
    execution = "痛みなく復帰条件を満たした後に実施"
    phases = [
        ("基礎", "1〜3週", "base", "17〜18kmを上限に維持"),
        ("持久力", "4〜8週", "build", "18〜24kmの条件付き範囲"),
        ("回復", "9〜10週", "recovery", "14〜18kmへ短縮"),
        ("調整", "11〜13週", "taper", "10〜16kmへ段階的に短縮"),
    ]
    phase_items = []
    for name, period, phase_type, load in phases:
        purpose = f"{name}期の目的"
        checkpoint = f"{name}期の確認点"
        progression = f"{name}期を進める条件"
        hold = f"{name}期を維持・後退する条件"
        phase_items.append(
            {
                "name": name,
                "period": period,
                "phase_type": phase_type,
                "long_session_distance_or_time": load,
                "purpose": purpose,
                "checkpoint": checkpoint,
                "progression_condition": progression,
                "hold_or_regress_condition": hold,
                "slide": 3,
                "execution_condition": execution,
            }
        )
    session_items = [
        {
            "session_type": "イージー走",
            "pace_or_effort": "会話できる強度",
            "purpose": "回復と土台",
            "adjustment_condition": "違和感時は休む",
            "intensity_class": "easy",
            "basis": "体感強度を使用",
            "basis_type": "effort_only",
            "source_ids": [],
            "slide": 5,
            "execution_condition": execution,
        },
        {
            "session_type": "質練習",
            "pace_or_effort": "確認済み範囲",
            "purpose": "目標ペースへの適応",
            "adjustment_condition": "疲労時はイージーへ変更",
            "intensity_class": "quality",
            "basis": "利用者確認値",
            "basis_type": "user_confirmed",
            "confirmation_quote": "質練習は確認済み範囲で行っています",
            "source_ids": [],
            "slide": 5,
            "execution_condition": execution,
        },
        {
            "session_type": "ロング走",
            "pace_or_effort": "会話できる強度",
            "purpose": "長時間耐性",
            "adjustment_condition": "痛みや回復遅延時は短縮",
            "intensity_class": "long_easy",
            "basis": "体感強度と現状距離",
            "basis_type": "effort_only",
            "source_ids": [],
            "slide": 5,
            "execution_condition": execution,
        },
    ]
    return {
        "deck_title": "テスト",
        "audience": "初心者ランナー本人",
        "purpose": "条件付きロードマップを判断できる",
        "mode": "standalone",
        "high_stakes": True,
        "dated_roadmap": True,
        "timeline": {
            "current_date": "2026-08-05",
            "target_date": "2026-11-01",
            "duration_text": duration,
            "slide": 2,
        },
        "safety": {
            "progressive_plan": True,
            "novice_or_returning": True,
            "event_preparation": True,
            "current_condition": "軽い違和感あり",
            "condition_status": "symptomatic",
            "plan_status": "provisional",
            "plan_status_text": "この計画は暫定案",
            "clearance_condition": "痛みなく復帰条件を満たしてから開始",
            "status_slide": 2,
            "taper_days": 21,
            "comparable_performance_data": True,
            "limitations": ["医療診断ではない"],
            "progression_conditions": ["痛みなく回復できる"],
            "recovery_conditions": ["3〜4週ごとに負荷を下げる"],
            "regression_conditions": ["違和感が残る場合は前段階へ戻る"],
            "stop_conditions": ["痛みが増す場合は中止"],
            "consultation_conditions": ["改善しない場合は専門家へ相談"],
            "pre_clearance_actions": ["ランニングを再開せず専門家へ相談"],
            "action_slide": 2,
            "phase_guidance": phase_items,
            "session_guidance": session_items,
            "weekly_long_sessions": [
                {
                    "week": week,
                    "period": f"第{week}週",
                    "distance_or_time": f"{16 + (week % 4)}km",
                    "condition": execution,
                    "recovery_week": week in {4, 8},
                    "slide": 4,
                }
                for week in range(1, 14)
            ],
        },
        "claim_evidence": [
            {
                "claim": "公式記録は号砲基準",
                "visible_text": "公式記録はグロスタイム（号砲基準）",
                "slide": 6,
                "basis_type": "authoritative_source",
                "source_ids": ["S1"],
                "support": "大会公式の開催要項が記録基準を示す",
                "evidence_design": "official_rule",
                "claim_strength": "fact",
            },
            {
                "kind": "safety",
                "claim": "症状がある間は走らない",
                "visible_text": "ランニングを再開せず専門家へ相談",
                "slide": 2,
                "basis_type": "authoritative_source",
                "source_ids": ["S2"],
                "support": "復帰前の評価条件を示す",
                "evidence_design": "clinical_guideline",
                "claim_strength": "recommendation",
            },
            *[
                {
                    "kind": "safety",
                    "claim": "復帰条件後に実施",
                    "visible_text": execution,
                    "slide": slide,
                    "basis_type": "authoritative_source",
                    "source_ids": ["S2"],
                    "support": "復帰前の評価条件を示す",
                    "evidence_design": "clinical_guideline",
                    "claim_strength": "recommendation",
                }
                for slide in (3, 4, 5)
            ],
        ],
        "event_facts": {
            "official_event_name": "下関海響マラソン",
            "start_time": "8:30スタート",
            "cutoff": "制限時間6時間",
            "timing_basis": "公式記録はグロスタイム（号砲基準）",
            "course_summary": "後半のアップダウンに備える",
            "strategy_slide": 6,
            "source_ids": ["S1"],
            "goal_basis": "サブ4はグロスタイム4時間未満",
            "pace_buffer_note": "5:41/kmちょうどではスタートロスの余裕がない",
        },
        "event_strategy": {
            "slide": 6,
            "segments": [
                {"label": "0–10km", "approach": "余裕を守る"},
                {"label": "10–30km", "approach": "一定努力で進む"},
                {"label": "30km–", "approach": "状態で調整する"},
            ],
            "fueling": "補給は練習で試した物だけを使う",
            "equipment": "靴と装備は本番前に固定する",
            "rehearsal": "ロング走で補給と装備をリハーサルする",
            "source_ids": ["S1"],
        },
        "current_target_comparison": {
            "current_value": "ハーフ平均5:17/km",
            "target_value": "目標平均5:41/km",
            "meaning": "速度より持久力と故障管理が課題",
            "comparison_basis": "平均ペース同士の比較",
            "slide": 2,
        },
        "slides": [
            {"layout": "cover", "title": "テスト", "date": "2026-08-05"},
            {
                "layout": "data_focus",
                "job": "evidence",
                "visual_role": "evidence",
                "title": "現在地と目標を比べる",
                "lead": f"{duration}・この計画は暫定案・痛みなく復帰条件を満たしてから開始・平均ペース同士の比較・ランニングを再開せず専門家へ相談",
                "stats": [
                    {"value": "ハーフ平均5:17/km", "label": "現在", "note": "実績"},
                    {"value": "目標平均5:41/km", "label": "目標", "note": "速度より持久力と故障管理が課題"},
                ],
                "source": "出典: [S2]",
            },
            {
                "layout": "process",
                "job": "instruction",
                "visual_role": "explain",
                "title": "段階別の負荷を確認する",
                "steps": [
                    {
                        "label": item["name"],
                        "title": item["period"],
                        "body": "・".join(
                            [
                                item["long_session_distance_or_time"],
                                item["purpose"],
                                item["checkpoint"],
                                item["progression_condition"],
                                item["hold_or_regress_condition"],
                                item["execution_condition"],
                            ]
                        ),
                    }
                    for item in phase_items
                ],
                "source": "出典: [S2]（実行条件のみ）",
            },
            {
                "layout": "table",
                "job": "instruction",
                "visual_role": "evidence",
                "title": "毎週のロング走を確認する",
                "headers": ["週", "期間", "距離", "条件"],
                "rows": [[f"第{week}週", f"第{week}週", f"{16 + (week % 4)}km", execution] for week in range(1, 14)],
                "source": "出典: [S2]（実行条件のみ）",
            },
            {
                "layout": "table",
                "job": "instruction",
                "visual_role": "evidence",
                "title": "週3回の役割を分ける",
                "headers": ["種類", "強度", "目的", "調整条件"],
                "rows": [[item["session_type"], f'{item["pace_or_effort"]}・{item["execution_condition"]}', item["purpose"], item["adjustment_condition"]] for item in session_items],
                "source": "出典: [S2]（実行条件のみ）",
            },
            {
                "layout": "process",
                "job": "instruction",
                "visual_role": "explain",
                "content_role": "event_strategy",
                "title": "当日は3区間で組み立てる",
                "lead": "下関海響マラソン・8:30スタート・制限時間6時間・公式記録はグロスタイム（号砲基準）・サブ4はグロスタイム4時間未満・5:41/kmちょうどではスタートロスの余裕がない",
                "steps": [
                    {"label": "0–10km", "title": "抑える", "body": "余裕を守る・後半のアップダウンに備える"},
                    {"label": "10–30km", "title": "整える", "body": "一定努力で進む・補給は練習で試した物だけを使う"},
                    {"label": "30km–", "title": "判断する", "body": "状態で調整する・靴と装備は本番前に固定する・ロング走で補給と装備をリハーサルする"},
                ],
                "source": "出典: [S1]",
            },
            {
                "layout": "sources_appendix",
                "title": "出典",
                "sources": [
                    {
                        "id": "S1",
                        "title": "検証用資料",
                        "publisher": "検証",
                        "url": "https://example.com",
                        "checked": "2026-08-05",
                    },
                    {
                        "id": "S2",
                        "title": "検証用安全資料",
                        "publisher": "検証",
                        "url": "https://example.org",
                        "checked": "2026-08-05",
                    }
                ],
            },
        ],
    }


def codes(deck: dict) -> set[str]:
    return {issue["code"] for issue in MODULE.validate(deck) if issue["level"] == "FAIL"}


def main() -> int:
    good = valid_deck()
    assert not codes(good), codes(good)

    vague = copy.deepcopy(good)
    vague["safety"]["phase_guidance"][1]["long_session_distance_or_time"] = "少しずつ延ばす"
    assert "NON_NUMERIC_PHASE_LOAD" in codes(vague)

    wrong_rounding = copy.deepcopy(good)
    wrong_rounding["timeline"]["duration_text"] = "88日（約12週間）"
    wrong_rounding["slides"][1]["lead"] = "88日（約12週間）"
    assert "TIMELINE_WEEK_ROUNDING" in codes(wrong_rounding)

    too_hard = copy.deepcopy(good)
    too_hard["safety"]["session_guidance"][0]["intensity_class"] = "quality"
    hard_codes = codes(too_hard)
    assert "MISSING_EASY_SESSION" in hard_codes
    assert "TOO_MANY_QUALITY_SESSIONS" in hard_codes

    hidden = copy.deepcopy(good)
    hidden["slides"][2]["steps"][1]["body"] = "表示から距離を削除"
    assert "PHASE_GUIDANCE_NOT_VISIBLE" in codes(hidden)

    unsupported = copy.deepcopy(good)
    unsupported["claim_evidence"][0]["source_ids"] = []
    assert "MISSING_CLAIM_SOURCE" in codes(unsupported)

    unrelated = copy.deepcopy(good)
    unrelated["slides"][2]["source"] = "出典: [S1]"
    assert "UNMAPPED_SLIDE_SOURCE" in codes(unrelated)

    calculated = copy.deepcopy(good)
    calculated["safety"]["session_guidance"][0]["basis_type"] = "calculation"
    assert "CALCULATION_ONLY_PRESCRIPTION" in codes(calculated)

    no_week = copy.deepcopy(good)
    no_week["safety"]["weekly_long_sessions"].pop()
    assert "INCOMPLETE_WEEKLY_LONG_PLAN" in codes(no_week)

    no_recovery = copy.deepcopy(good)
    for item in no_recovery["safety"]["weekly_long_sessions"]:
        item["recovery_week"] = False
    assert "MISSING_WEEKLY_RECOVERY" in codes(no_recovery)

    no_strategy = copy.deepcopy(good)
    del no_strategy["event_strategy"]
    assert "MISSING_EVENT_STRATEGY" in codes(no_strategy)

    causal = copy.deepcopy(good)
    causal["claim_evidence"][0]["evidence_design"] = "observational"
    causal["claim_evidence"][0]["claim_strength"] = "causal"
    assert "CAUSAL_OVERCLAIM" in codes(causal)

    receipt_state = {"confirmed_conditions": ["質練習は確認済み範囲で行っています"]}
    assert not MODULE.validate_confirmation_receipts(good, receipt_state)
    assert "UNVERIFIED_USER_CONFIRMATION" in {item["code"] for item in MODULE.validate_confirmation_receipts(good, {"confirmed_conditions": []})}

    weak_strategy = copy.deepcopy(good)
    weak_strategy["slides"][5]["layout"] = "text_focus"
    assert "WEAK_EVENT_STRATEGY_VISUAL" in codes(weak_strategy)

    dense_process = copy.deepcopy(good)
    dense_process["slides"][5]["lead"] = "長" * 121
    assert "PROCESS_LEAD_DENSITY" in codes(dense_process)

    duplicate_process = copy.deepcopy(good)
    duplicate_process["slides"][5]["steps"][0]["body"] = duplicate_process["slides"][5]["steps"][0]["title"]
    assert "DUPLICATE_PROCESS_COPY" in codes(duplicate_process)

    dense_data_focus = copy.deepcopy(good)
    dense_data_focus["slides"][1]["lead"] = "長" * 81
    assert "DATA_FOCUS_LEAD_DENSITY" in codes(dense_data_focus)

    dense_stat = copy.deepcopy(good)
    dense_stat["slides"][1]["stats"][0]["value"] = "長" * 19
    assert "DATA_FOCUS_VALUE_DENSITY" in codes(dense_stat)

    dense_comparison = copy.deepcopy(good)
    dense_comparison["slides"].insert(2, {
        "layout": "comparison", "job": "compare", "visual_role": "evidence",
        "title": "比較する", "columns": [
            {"heading": "A", "body": "長" * 121},
            {"heading": "B", "body": "短い"},
        ],
    })
    assert "COMPARISON_COLUMN_DENSITY" in codes(dense_comparison)

    dense_event_title = copy.deepcopy(good)
    dense_event_title["slides"][5]["steps"][0]["title"] = "長" * 47
    assert "PROCESS_TITLE_DENSITY" in codes(dense_event_title)

    revision_state = {
        "phase": "revision_approved",
        "revision": {
            "source_artifact": "existing.html",
            "scope": "7ページ目を3区間の図へ修正",
            "user_reply": "7ページ目を修正してください",
        },
    }
    assert not MODULE.validate_approval(revision_state)
    revision_state["revision"]["scope"] = ""
    assert MODULE.validate_approval(revision_state)[0]["code"] == "REVISION_NOT_APPROVED"

    print("PASS: build_deck validation regression checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
