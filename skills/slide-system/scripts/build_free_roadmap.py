#!/usr/bin/env python3
"""Expand a compact dated-exercise brief and build a validated HTML deck."""

from __future__ import annotations

import argparse
import json
from datetime import date
from math import ceil
from pathlib import Path

import build_deck as engine


DRAFT_NOTICE = "検証未完了ドラフト｜実行用ではありません。内容と安全条件の確認が必要です。"


def text(value: object, fallback: str = "未設定") -> str:
    value = str(value or "").strip()
    return value or fallback


def source_map(brief: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in brief.get("sources", []):
        if isinstance(item, dict) and text(item.get("role"), ""):
            result[text(item["role"], "")] = item
    return result


def evidence(source: dict, visible_text: str, slide: int, claim: str, kind: str = "fact") -> dict:
    return {
        "kind": kind,
        "claim": claim,
        "visible_text": visible_text,
        "slide": slide,
        "basis_type": "authoritative_source",
        "source_ids": [text(source.get("id"))],
        "support": text(source.get("support")),
        "evidence_design": text(source.get("evidence_design")),
        "claim_strength": text(source.get("claim_strength")),
    }


def expand(brief: dict) -> dict:
    sources_by_role = source_map(brief)
    missing_roles = [role for role in ("event", "safety", "taper", "nutrition") if role not in sources_by_role]
    if missing_roles:
        raise ValueError(f"sources needs roles: {', '.join(missing_roles)}")
    event_source = sources_by_role["event"]
    safety_source = sources_by_role["safety"]
    taper_source = sources_by_role["taper"]
    nutrition_source = sources_by_role["nutrition"]

    current = date.fromisoformat(text(brief.get("current_date"), ""))
    target = date.fromisoformat(text(brief.get("target_date"), ""))
    remaining_days = (target - current).days
    if remaining_days <= 0:
        raise ValueError("target_date must be after current_date")
    expected_weeks = ceil(remaining_days / 7)
    duration = f"{remaining_days}日（約{round(remaining_days / 7)}週間）"

    condition = brief.get("condition", {})
    comparison = brief.get("comparison", {})
    event = brief.get("event", {})
    phases = brief.get("phases", [])
    weeks = brief.get("weekly_long_sessions", [])
    sessions = brief.get("sessions", [])
    segments = event.get("segments", [])
    if len(phases) < 4:
        raise ValueError("phases needs at least four entries")
    if len(weeks) != expected_weeks:
        raise ValueError(f"weekly_long_sessions needs exactly {expected_weeks} entries")
    if len(sessions) < 3:
        raise ValueError("sessions needs at least three entries")
    if len(segments) < 3:
        raise ValueError("event.segments needs at least three entries")

    execution = text(condition.get("execution_condition"))
    plan_status_text = text(condition.get("plan_status_text"))
    clearance = text(condition.get("clearance_condition"))
    pre_clearance_action = text(condition.get("pre_clearance_action"))
    stop_condition = text(condition.get("stop_condition"))
    consultation = text(condition.get("consultation_condition"))

    phase_guidance = []
    phase_rows = []
    taper_visible_text = ""
    for item in phases:
        phase = {
            "name": text(item.get("name")),
            "period": text(item.get("period")),
            "phase_type": text(item.get("phase_type")),
            "long_session_distance_or_time": text(item.get("long_session_distance_or_time")),
            "purpose": text(item.get("purpose")),
            "checkpoint": text(item.get("checkpoint")),
            "progression_condition": text(item.get("progression_condition")),
            "hold_or_regress_condition": text(item.get("hold_or_regress_condition")),
            "execution_condition": execution,
            "slide": 3,
        }
        phase_guidance.append(phase)
        phase_rows.append([
            f'{phase["name"]}｜{phase["period"]}',
            f'{phase["long_session_distance_or_time"]}｜{phase["purpose"]}',
            f'{phase["checkpoint"]}｜{phase["progression_condition"]}',
            phase["hold_or_regress_condition"],
        ])
        if phase["phase_type"] == "taper":
            taper_visible_text = phase["purpose"]

    weekly_guidance = []
    week_rows_first = []
    week_rows_second = []
    split_at = ceil(expected_weeks / 2)
    for item in weeks:
        week_number = item.get("week")
        slide_number = 4 if isinstance(week_number, int) and week_number <= split_at else 5
        weekly = {
            "week": week_number,
            "period": text(item.get("period")),
            "distance_or_time": text(item.get("distance_or_time")),
            "condition": execution,
            "recovery_week": item.get("recovery_week") is True,
            "slide": slide_number,
        }
        weekly_guidance.append(weekly)
        label = f"第{week_number}週" + ("・回復" if weekly["recovery_week"] else "")
        row = [label, weekly["period"], weekly["distance_or_time"]]
        (week_rows_first if slide_number == 4 else week_rows_second).append(row)

    session_guidance = []
    session_rows = []
    for item in sessions:
        session = {
            "session_type": text(item.get("session_type")),
            "pace_or_effort": text(item.get("pace_or_effort")),
            "purpose": text(item.get("purpose")),
            "adjustment_condition": text(item.get("adjustment_condition")),
            "intensity_class": text(item.get("intensity_class")),
            "basis": text(item.get("basis")),
            "basis_type": text(item.get("basis_type")),
            "source_ids": item.get("source_ids", []),
            "slide": 6,
            "execution_condition": execution,
        }
        if session["basis_type"] == "user_confirmed":
            session["confirmation_quote"] = text(item.get("confirmation_quote"))
        session_guidance.append(session)
        session_rows.append([
            session["session_type"], f'{session["pace_or_effort"]}・{execution}',
            session["purpose"], session["adjustment_condition"],
        ])

    event_facts = {
        "official_event_name": text(event.get("official_event_name")),
        "start_time": text(event.get("start_time")),
        "cutoff": text(event.get("cutoff")),
        "timing_basis": text(event.get("timing_basis")),
        "course_summary": text(event.get("course_summary")),
        "goal_basis": text(event.get("goal_basis")),
        "pace_buffer_note": text(event.get("pace_buffer_note")),
        "strategy_slide": 7,
        "source_ids": [text(event_source.get("id"))],
    }
    event_strategy = {
        "slide": 7,
        "segments": [
            {"label": text(item.get("label")), "approach": text(item.get("approach"))}
            for item in segments
        ],
        "fueling": text(event.get("fueling")),
        "equipment": text(event.get("equipment")),
        "rehearsal": text(event.get("rehearsal")),
        "source_ids": [text(event_source.get("id")), text(nutrition_source.get("id"))],
    }
    event_lead = "・".join([
        event_facts["official_event_name"], event_facts["start_time"], event_facts["cutoff"],
        event_facts["timing_basis"], event_facts["course_summary"], event_facts["goal_basis"],
        event_facts["pace_buffer_note"], event_strategy["fueling"], event_strategy["equipment"],
        event_strategy["rehearsal"],
    ])

    safety_id = text(safety_source.get("id"))
    taper_id = text(taper_source.get("id"))
    event_id = text(event_source.get("id"))
    nutrition_id = text(nutrition_source.get("id"))
    claim_evidence = [
        evidence(safety_source, clearance, 2, "実行前の復帰条件", "safety"),
        evidence(safety_source, execution, 3, "段階計画の実行条件", "safety"),
        evidence(safety_source, execution, 4, "週別計画前半の実行条件", "safety"),
        evidence(safety_source, execution, 5, "週別計画後半の実行条件", "safety"),
        evidence(safety_source, execution, 6, "定例練習の実行条件", "safety"),
        evidence(safety_source, pre_clearance_action, 8, "復帰前の行動", "safety"),
        evidence(event_source, event_facts["timing_basis"], 7, "公式記録基準"),
        evidence(nutrition_source, event_strategy["fueling"], 7, "補給の準備", "instruction"),
    ]
    if taper_visible_text:
        claim_evidence.append(evidence(taper_source, taper_visible_text, 3, "調整期の考え方", "instruction"))

    comparison_model = {
        "current_value": text(comparison.get("current_value")),
        "target_value": text(comparison.get("target_value")),
        "meaning": text(comparison.get("meaning")),
        "comparison_basis": text(comparison.get("comparison_basis")),
        "slide": 2,
    }
    comparison_lead = "・".join([
        duration, plan_status_text, clearance, comparison_model["comparison_basis"], comparison_model["meaning"],
    ])

    slides = [
        {
            "layout": "cover", "eyebrow": text(brief.get("eyebrow"), "ROADMAP"),
            "title": text(brief.get("deck_title")), "subtitle": text(brief.get("subtitle"), ""),
            "date": text(brief.get("date")),
        },
        {
            "layout": "data_focus", "job": "evidence", "visual_role": "evidence",
            "title": "現在地と目標を同じ単位で比べる", "lead": comparison_lead,
            "stats": [
                {"value": comparison_model["current_value"], "label": "現在", "note": "確認済み実績"},
                {"value": comparison_model["target_value"], "label": "目標", "note": comparison_model["meaning"]},
            ],
            "source": f"出典: [{safety_id}]（復帰条件のみ）",
        },
        {
            "layout": "table", "job": "instruction", "visual_role": "evidence",
            "title": "段階ごとの目的と進行条件", "lead": execution,
            "headers": ["段階・期間", "距離・目的", "確認・進行", "維持・後退"],
            "rows": phase_rows,
            "source": f"出典: [{safety_id}]（実行条件） [{taper_id}]（調整期）",
        },
        {
            "layout": "table", "job": "instruction", "visual_role": "evidence",
            "title": f"第1〜{split_at}週のロング走", "lead": execution,
            "headers": ["週", "期間", "距離・時間"],
            "rows": week_rows_first, "source": f"出典: [{safety_id}]（実行条件のみ）",
        },
        {
            "layout": "table", "job": "instruction", "visual_role": "evidence",
            "title": f"第{split_at + 1}〜{expected_weeks}週のロング走", "lead": execution,
            "headers": ["週", "期間", "距離・時間"],
            "rows": week_rows_second, "source": f"出典: [{safety_id}]（実行条件のみ）",
        },
        {
            "layout": "table", "job": "instruction", "visual_role": "evidence",
            "title": "週3回の役割と強度を分ける", "headers": ["種類", "強度", "目的", "調整条件"],
            "rows": session_rows, "source": f"出典: [{safety_id}]（実行条件のみ）",
        },
        {
            "layout": "process", "job": "instruction", "visual_role": "explain",
            "title": "当日は3区間以上で組み立てる", "lead": event_lead,
            "steps": [
                {"label": item["label"], "title": item["approach"], "body": item["approach"]}
                for item in event_strategy["segments"]
            ],
            "source": f"出典: [{event_id}] [{nutrition_id}]",
        },
        {
            "layout": "summary_action", "job": "instruction", "visual_role": "explain",
            "title": "違和感がある今は復帰判断を優先する", "lead": plan_status_text,
            "actions": [pre_clearance_action, stop_condition, consultation],
            "source": f"出典: [{safety_id}]",
        },
        {
            "layout": "sources_appendix", "title": "出典",
            "sources": [
                {key: item[key] for key in ("id", "title", "publisher", "url", "checked")}
                for item in brief.get("sources", [])
            ],
        },
    ]

    return {
        "deck_title": text(brief.get("deck_title")),
        "audience": text(brief.get("audience")),
        "purpose": text(brief.get("purpose")),
        "mode": "standalone",
        "high_stakes": True,
        "dated_roadmap": True,
        "timeline": {
            "current_date": current.isoformat(), "target_date": target.isoformat(),
            "duration_text": duration, "slide": 2,
        },
        "safety": {
            "progressive_plan": True, "novice_or_returning": True, "event_preparation": True,
            "current_condition": text(condition.get("current_condition")),
            "condition_status": text(condition.get("condition_status")),
            "plan_status": text(condition.get("plan_status")),
            "plan_status_text": plan_status_text, "clearance_condition": clearance, "status_slide": 2,
            "taper_days": condition.get("taper_days"), "comparable_performance_data": True,
            "limitations": [text(condition.get("limitation"))],
            "progression_conditions": [text(condition.get("progression_condition"))],
            "recovery_conditions": [text(condition.get("recovery_condition"))],
            "regression_conditions": [text(condition.get("regression_condition"))],
            "stop_conditions": [stop_condition], "consultation_conditions": [consultation],
            "pre_clearance_actions": [pre_clearance_action], "action_slide": 8,
            "phase_guidance": phase_guidance, "session_guidance": session_guidance,
            "weekly_long_sessions": weekly_guidance,
        },
        "claim_evidence": claim_evidence,
        "event_facts": event_facts,
        "event_strategy": event_strategy,
        "current_target_comparison": comparison_model,
        "slides": slides,
    }


def minimal_draft(brief: object, message: str) -> dict:
    data = brief if isinstance(brief, dict) else {}
    return {
        "deck_title": text(data.get("deck_title"), "スライド下書き"),
        "audience": text(data.get("audience"), "依頼者"),
        "purpose": "不足項目を確認して制作を再開する",
        "mode": "standalone", "high_stakes": False,
        "slides": [
            {"layout": "cover", "title": text(data.get("deck_title"), "スライド下書き"), "date": text(data.get("date"), date.today().isoformat())},
            {
                "layout": "text_focus", "job": "summary", "visual_role": "none",
                "visual_reason": "検証結果と再開条件を明確に伝えるため", "title": "検証未完了",
                "lead": "このファイルは実行用ではありません。入力を修正して再構築してください。",
                "bullets": [message[:180]],
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True)
    parser.add_argument("--work-state", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--deck-output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    brief_path = Path(args.brief).resolve()
    state_path = Path(args.work_state).resolve()
    template_path = Path(args.template).resolve()
    output_path = Path(args.output).resolve()
    deck_path = Path(args.deck_output).resolve()
    report_path = Path(args.report).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    brief: object = {}
    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        work_state = json.loads(state_path.read_text(encoding="utf-8"))
        approval_issues = engine.validate_approval(work_state)
        if approval_issues:
            raise ValueError(approval_issues[0]["message"])
        deck = expand(brief)
        issues = engine.validate(deck)
        issues.extend(engine.validate_confirmation_receipts(deck, work_state))
        failures = [item for item in issues if item["level"] == "FAIL"]
        report = {
            "status": "DRAFT" if failures else "PASS", "slide_count": len(deck["slides"]),
            "warning_count": sum(item["level"] == "WARN" for item in issues), "issues": issues,
            "quality_gate": "UNCHANGED_STRICT_VALIDATOR",
        }
        notice = DRAFT_NOTICE if failures else ""
    except Exception as exc:
        deck = minimal_draft(brief, str(exc))
        report = {
            "status": "DRAFT", "slide_count": len(deck["slides"]), "warning_count": 0,
            "issues": [{"level": "FAIL", "code": "COMPACT_INPUT_ERROR", "message": str(exc)}],
            "quality_gate": "NOT_RUN_INPUT_INCOMPLETE",
        }
        notice = DRAFT_NOTICE

    deck_path.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html = engine.build_html_document(deck, deck_path, template_path, notice)
    output_path.write_text(html, encoding="utf-8", newline="\n")
    print(json.dumps({
        "status": report["status"], "html": str(output_path), "deck": str(deck_path),
        "report": str(report_path), "slide_count": report["slide_count"],
        "complete": report["status"] == "PASS", "must_return_html": True,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
