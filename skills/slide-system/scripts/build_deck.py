#!/usr/bin/env python3
"""Build a self-contained warm_clean HTML deck from a compact JSON model."""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import sys
from datetime import date
from pathlib import Path


ALLOWED_LAYOUTS = {
    "cover",
    "agenda",
    "section_divider",
    "single_message",
    "text_focus",
    "text_visual",
    "comparison",
    "process",
    "data_focus",
    "bar_chart",
    "table",
    "decision_flow",
    "exercise",
    "summary_action",
    "sources_appendix",
}
ALLOWED_JOBS = {"claim", "explain", "evidence", "compare", "instruction", "question", "exercise", "summary", "transition"}
ALLOWED_VISUAL_ROLES = {"evidence", "explain", "context", "decoration", "none"}
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|LOREM|PLACEHOLDER)\b|仮(?:タイトル|本文|画像)|ここに", re.I)
SOURCE_ID_RE = re.compile(r"\[([A-Za-z][A-Za-z0-9_-]*)\]")
APPROVAL_STATUSES = {"approved", "waived"}
PRODUCTION_PHASES = {"approved", "building", "qa", "revision_approved"}
SESSION_INTENSITIES = {"easy", "recovery", "quality", "long_easy", "other"}
PHASE_TYPES = {"base", "build", "peak", "recovery", "taper", "other"}
BASIS_TYPES = {"user_confirmed", "calculation", "authoritative_source", "effort_only", "inference"}
CONDITION_STATUSES = {"pain_free", "symptomatic", "unknown", "not_applicable"}
LOAD_GUIDE_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:km|キロ|分|時間|mile|miles|mi)", re.I)
VISIBLE_SLIDE_FIELDS = {
    "eyebrow", "title", "subtitle", "date", "headline", "body", "lead", "bullets",
    "callout", "sections", "columns", "steps", "stats", "bars", "note", "headers",
    "rows", "question", "yes_action", "no_action", "prompt", "answer", "actions", "source",
}


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def text_len(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, dict):
        return sum(text_len(v) for v in value.values())
    if isinstance(value, list):
        return sum(text_len(v) for v in value)
    return len(str(value).strip())


def visible_slide_text(slide: object) -> str:
    if not isinstance(slide, dict):
        return ""
    visible = {key: value for key, value in slide.items() if key in VISIBLE_SLIDE_FIELDS}
    return json.dumps(visible, ensure_ascii=False)


def add_issue(issues: list[dict], level: str, code: str, message: str, slide: int | None = None) -> None:
    item = {"level": level, "code": code, "message": message}
    if slide is not None:
        item["slide"] = slide
    issues.append(item)


def validate_approval(work_state: object) -> list[dict]:
    issues: list[dict] = []
    if not isinstance(work_state, dict):
        add_issue(issues, "FAIL", "PRODUCTION_NOT_APPROVED", "work-state must be a JSON object")
        return issues

    phase = str(work_state.get("phase", "")).strip()
    if phase == "revision_approved":
        revision = work_state.get("revision")
        required = ("source_artifact", "scope", "user_reply")
        if not isinstance(revision, dict) or any(not str(revision.get(field, "")).strip() for field in required):
            add_issue(issues, "FAIL", "REVISION_NOT_APPROVED", f"A bounded revision needs {', '.join(required)}")
        return issues
    approval = work_state.get("approval")
    if phase not in PRODUCTION_PHASES or not isinstance(approval, dict):
        add_issue(issues, "FAIL", "PRODUCTION_NOT_APPROVED", "Production phase is not approved")
        return issues

    status = str(approval.get("status", "")).strip()
    user_reply = str(approval.get("user_reply", "")).strip()
    if status not in APPROVAL_STATUSES or not user_reply:
        add_issue(issues, "FAIL", "PRODUCTION_NOT_APPROVED", "Approval needs an approved or waived status and the user's exact reply")
    return issues


def validate_high_stakes_semantics(deck: dict, slides: list[dict]) -> list[dict]:
    """Require visible, traceable support for high-stakes instructions."""
    issues: list[dict] = []
    if deck.get("high_stakes") is not True:
        return issues
    safety = deck.get("safety")
    if not isinstance(safety, dict):
        return issues

    appendix_ids: set[str] = set()
    for slide in slides:
        if isinstance(slide, dict) and slide.get("layout") == "sources_appendix":
            for source in slide.get("sources", []):
                if isinstance(source, dict) and str(source.get("id", "")).strip():
                    appendix_ids.add(str(source["id"]).strip())
    evidence_source_ids: set[str] = set()

    condition_status = str(safety.get("condition_status", "")).strip()
    if condition_status not in CONDITION_STATUSES:
        add_issue(issues, "FAIL", "MISSING_CONDITION_STATUS", f"condition_status must be one of {', '.join(sorted(CONDITION_STATUSES))}")

    if safety.get("progressive_plan") is True:
        plan_status = str(safety.get("plan_status", "")).strip()
        if plan_status not in {"executable", "provisional"}:
            add_issue(issues, "FAIL", "MISSING_PLAN_STATUS", "A progressive plan needs plan_status: executable or provisional")
        if condition_status in {"symptomatic", "unknown"} and plan_status != "provisional":
            add_issue(issues, "FAIL", "UNSAFE_PLAN_STATUS", "A symptomatic or unknown current condition must keep the plan provisional")
        if plan_status == "provisional":
            required_status = ("plan_status_text", "clearance_condition", "status_slide")
            if any(not str(safety.get(field, "")).strip() for field in required_status):
                add_issue(issues, "FAIL", "INCOMPLETE_PROVISIONAL_STATUS", f"A provisional plan needs {', '.join(required_status)}")
            else:
                status_slide = safety.get("status_slide")
                if not isinstance(status_slide, int) or not 1 <= status_slide <= len(slides):
                    add_issue(issues, "FAIL", "INVALID_STATUS_SLIDE", "status_slide must identify a valid slide")
                else:
                    shown = visible_slide_text(slides[status_slide - 1])
                    for field in ("plan_status_text", "clearance_condition"):
                        if str(safety[field]).strip() not in shown:
                            add_issue(issues, "FAIL", "PROVISIONAL_STATUS_NOT_VISIBLE", f"{field} must be visible on status_slide")

        phases = safety.get("phase_guidance", [])
        phase_types = {str(item.get("phase_type", "")).strip() for item in phases if isinstance(item, dict)}
        for phase_index, phase in enumerate(phases if isinstance(phases, list) else [], 1):
            if not isinstance(phase, dict):
                continue
            phase_slide = phase.get("slide")
            if not isinstance(phase_slide, int) or not 1 <= phase_slide <= len(slides):
                continue
            shown = visible_slide_text(slides[phase_slide - 1])
            visible_fields = ("period", "long_session_distance_or_time", "purpose", "checkpoint", "progression_condition", "hold_or_regress_condition")
            missing = [field for field in visible_fields if str(phase.get(field, "")).strip() not in shown]
            if missing:
                add_issue(issues, "FAIL", "PHASE_GUIDANCE_NOT_VISIBLE", f"Phase guidance {phase_index} must visibly show: {', '.join(missing)}")

        sessions = safety.get("session_guidance", [])
        for session_index, session in enumerate(sessions if isinstance(sessions, list) else [], 1):
            if not isinstance(session, dict):
                continue
            basis_type = str(session.get("basis_type", "")).strip()
            if basis_type not in BASIS_TYPES:
                add_issue(issues, "FAIL", "INVALID_SESSION_BASIS", f"Session guidance {session_index} needs a supported basis_type")
            source_ids = session.get("source_ids", [])
            if not isinstance(source_ids, list):
                add_issue(issues, "FAIL", "INVALID_SESSION_SOURCES", f"Session guidance {session_index} source_ids must be an array")
            else:
                evidence_source_ids.update(str(item).strip() for item in source_ids if str(item).strip())
                if basis_type == "authoritative_source" and not source_ids:
                    add_issue(issues, "FAIL", "MISSING_SESSION_SOURCE", f"Session guidance {session_index} needs source_ids")
            session_slide = session.get("slide")
            if not isinstance(session_slide, int) or not 1 <= session_slide <= len(slides):
                add_issue(issues, "FAIL", "SESSION_GUIDANCE_SLIDE", f"Session guidance {session_index} must identify a valid slide")
            else:
                shown = visible_slide_text(slides[session_slide - 1])
                for field in ("session_type", "pace_or_effort", "purpose", "adjustment_condition"):
                    if str(session.get(field, "")).strip() not in shown:
                        add_issue(issues, "FAIL", "SESSION_GUIDANCE_NOT_VISIBLE", f"Session guidance {session_index} must visibly show {field}")

        if safety.get("event_preparation") is True:
            if "recovery" not in phase_types:
                add_issue(issues, "FAIL", "MISSING_EVENT_RECOVERY_PHASE", "Event preparation needs an explicit recovery phase before taper")
            if "taper" not in phase_types:
                add_issue(issues, "FAIL", "MISSING_TAPER_PHASE", "Event preparation needs an explicit taper phase")
            taper_days = safety.get("taper_days")
            if not isinstance(taper_days, int) or not 14 <= taper_days <= 21:
                add_issue(issues, "FAIL", "INVALID_TAPER_LENGTH", "Event preparation needs taper_days between 14 and 21")

    claim_evidence = deck.get("claim_evidence")
    if not isinstance(claim_evidence, list) or not claim_evidence:
        add_issue(issues, "FAIL", "MISSING_CLAIM_EVIDENCE", "A high-stakes deck needs explicit claim_evidence records")
    else:
        for evidence_index, evidence in enumerate(claim_evidence, 1):
            required = ("claim", "visible_text", "slide", "basis_type", "support")
            if not isinstance(evidence, dict) or any(not str(evidence.get(field, "")).strip() for field in required):
                add_issue(issues, "FAIL", "INCOMPLETE_CLAIM_EVIDENCE", f"Claim evidence {evidence_index} needs {', '.join(required)}")
                continue
            basis_type = str(evidence.get("basis_type", "")).strip()
            if basis_type not in BASIS_TYPES:
                add_issue(issues, "FAIL", "INVALID_CLAIM_BASIS", f"Claim evidence {evidence_index} has unsupported basis_type")
            source_ids = evidence.get("source_ids", [])
            if not isinstance(source_ids, list):
                add_issue(issues, "FAIL", "INVALID_CLAIM_SOURCES", f"Claim evidence {evidence_index} source_ids must be an array")
            else:
                evidence_source_ids.update(str(item).strip() for item in source_ids if str(item).strip())
                if basis_type == "authoritative_source" and not source_ids:
                    add_issue(issues, "FAIL", "MISSING_CLAIM_SOURCE", f"Claim evidence {evidence_index} needs at least one source ID")
            evidence_slide = evidence.get("slide")
            if not isinstance(evidence_slide, int) or not 1 <= evidence_slide <= len(slides):
                add_issue(issues, "FAIL", "CLAIM_EVIDENCE_SLIDE", f"Claim evidence {evidence_index} must identify a valid slide")
            elif str(evidence.get("visible_text", "")).strip() not in visible_slide_text(slides[evidence_slide - 1]):
                add_issue(issues, "FAIL", "CLAIM_NOT_VISIBLE", f"Claim evidence {evidence_index} visible_text is not shown on its slide")

    if safety.get("event_preparation") is True:
        event_facts = deck.get("event_facts")
        required_event = ("official_event_name", "start_time", "cutoff", "timing_basis", "course_summary", "strategy_slide", "source_ids")
        if not isinstance(event_facts, dict) or any(not event_facts.get(field) for field in required_event):
            add_issue(issues, "FAIL", "INCOMPLETE_EVENT_FACTS", f"Event preparation needs event_facts with {', '.join(required_event)}")
        else:
            source_ids = event_facts.get("source_ids", [])
            if isinstance(source_ids, list):
                evidence_source_ids.update(str(item).strip() for item in source_ids if str(item).strip())
            strategy_slide = event_facts.get("strategy_slide")
            if not isinstance(strategy_slide, int) or not 1 <= strategy_slide <= len(slides):
                add_issue(issues, "FAIL", "INVALID_EVENT_STRATEGY_SLIDE", "event_facts.strategy_slide must identify a valid slide")
            else:
                strategy = slides[strategy_slide - 1]
                shown = visible_slide_text(strategy)
                for field in ("official_event_name", "start_time", "cutoff", "timing_basis", "course_summary"):
                    if str(event_facts.get(field, "")).strip() not in shown:
                        add_issue(issues, "FAIL", "EVENT_FACT_NOT_VISIBLE", f"event_facts.{field} must be visible on strategy_slide")
                if strategy.get("layout") in {"text_focus", "single_message"} or strategy.get("visual_role") in {"none", "decoration"}:
                    add_issue(issues, "FAIL", "WEAK_EVENT_STRATEGY_VISUAL", "The event strategy slide needs a meaningful process, comparison, table, chart, or decision visual")

    if safety.get("comparable_performance_data") is True:
        comparison = deck.get("current_target_comparison")
        required = ("current_value", "target_value", "meaning", "slide")
        if not isinstance(comparison, dict) or any(not str(comparison.get(field, "")).strip() for field in required):
            add_issue(issues, "FAIL", "MISSING_CURRENT_TARGET_COMPARISON", f"Comparable performance data needs {', '.join(required)}")
        else:
            comparison_slide = comparison.get("slide")
            if not isinstance(comparison_slide, int) or not 1 <= comparison_slide <= len(slides):
                add_issue(issues, "FAIL", "INVALID_COMPARISON_SLIDE", "current_target_comparison.slide must identify a valid slide")
            else:
                shown = visible_slide_text(slides[comparison_slide - 1])
                for field in ("current_value", "target_value", "meaning"):
                    if str(comparison.get(field, "")).strip() not in shown:
                        add_issue(issues, "FAIL", "COMPARISON_NOT_VISIBLE", f"current_target_comparison.{field} must be visible on its slide")

    missing_sources = evidence_source_ids - appendix_ids
    if missing_sources:
        add_issue(issues, "FAIL", "UNRESOLVED_EVIDENCE_SOURCE", f"Evidence records are missing appendix entries: {', '.join(sorted(missing_sources))}")
    return issues


def validate(deck: dict) -> list[dict]:
    issues: list[dict] = []
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        add_issue(issues, "FAIL", "NO_SLIDES", "slides must be a non-empty array")
        return issues

    if len(slides) < 3:
        add_issue(issues, "WARN", "SHORT_DECK", "A deck normally needs at least three slides")
    if len(slides) > 20:
        add_issue(issues, "WARN", "LONG_DECK", "More than 20 slides may exceed a resource-constrained session")

    mode = deck.get("mode", "standalone")
    if not str(deck.get("audience", "")).strip():
        add_issue(issues, "FAIL", "MISSING_AUDIENCE", "Deck metadata needs an intended audience")
    if not str(deck.get("purpose", "")).strip():
        add_issue(issues, "FAIL", "MISSING_PURPOSE", "Deck metadata needs a concrete audience outcome")
    high_stakes = deck.get("high_stakes") is True
    if deck.get("dated_roadmap") is True:
        timeline = deck.get("timeline")
        if not isinstance(timeline, dict):
            add_issue(issues, "FAIL", "MISSING_TIMELINE", "A dated roadmap needs a timeline object")
        else:
            required_timeline = ("current_date", "target_date", "duration_text", "slide")
            if any(not str(timeline.get(field, "")).strip() for field in required_timeline):
                add_issue(issues, "FAIL", "INCOMPLETE_TIMELINE", f"A dated roadmap needs {', '.join(required_timeline)}")
            else:
                try:
                    current = date.fromisoformat(str(timeline["current_date"]))
                    target = date.fromisoformat(str(timeline["target_date"]))
                    remaining_days = (target - current).days
                    if remaining_days < 0:
                        raise ValueError("target_date precedes current_date")
                    duration_text = str(timeline["duration_text"])
                    if str(remaining_days) not in duration_text:
                        add_issue(issues, "FAIL", "TIMELINE_DAY_MISMATCH", f"duration_text must visibly include the exact {remaining_days} remaining days")
                    rounded_match = re.search(r"約\s*(\d+)\s*週間", duration_text)
                    if rounded_match and int(rounded_match.group(1)) != round(remaining_days / 7):
                        add_issue(issues, "FAIL", "TIMELINE_WEEK_ROUNDING", f"{remaining_days} days rounds naturally to about {round(remaining_days / 7)} weeks")
                    timeline_slide = timeline.get("slide")
                    if not isinstance(timeline_slide, int) or not 1 <= timeline_slide <= len(slides):
                        add_issue(issues, "FAIL", "TIMELINE_SLIDE", "timeline.slide must identify a valid slide")
                    elif duration_text not in visible_slide_text(slides[timeline_slide - 1]):
                        add_issue(issues, "FAIL", "TIMELINE_NOT_VISIBLE", "The exact duration_text must be visible on timeline.slide")
                except (TypeError, ValueError) as exc:
                    add_issue(issues, "FAIL", "INVALID_TIMELINE_DATE", f"Timeline dates must be valid ISO dates: {exc}")
    if high_stakes:
        safety = deck.get("safety")
        if not isinstance(safety, dict):
            add_issue(issues, "FAIL", "MISSING_SAFETY_MODEL", "A high-stakes deck needs a safety object")
        else:
            if not str(safety.get("current_condition", "")).strip():
                add_issue(issues, "FAIL", "MISSING_CURRENT_CONDITION", "A high-stakes deck needs the confirmed current condition or an explicit unknown status")
            for field in ("limitations", "stop_conditions"):
                value = safety.get(field)
                if not isinstance(value, list) or not any(str(item).strip() for item in value):
                    add_issue(issues, "FAIL", "MISSING_SAFETY_CONDITION", f"A high-stakes deck needs non-empty {field}")
            if safety.get("progressive_plan") is True:
                for field in ("progression_conditions", "recovery_conditions", "regression_conditions", "consultation_conditions"):
                    value = safety.get(field)
                    if not isinstance(value, list) or not any(str(item).strip() for item in value):
                        add_issue(issues, "FAIL", "MISSING_PROGRESSIVE_PLAN_CONDITION", f"A progressive high-stakes plan needs non-empty {field}")
                phase_guidance = safety.get("phase_guidance")
                if not isinstance(phase_guidance, list) or len(phase_guidance) < 2:
                    add_issue(issues, "FAIL", "MISSING_PHASE_GUIDANCE", "A progressive exercise plan needs at least two phases with visible load guidance")
                else:
                    phase_types: set[str] = set()
                    required_phase = ("name", "period", "phase_type", "long_session_distance_or_time", "purpose", "checkpoint", "progression_condition", "hold_or_regress_condition", "slide")
                    for phase_index, phase in enumerate(phase_guidance, 1):
                        if not isinstance(phase, dict) or any(not str(phase.get(field, "")).strip() for field in required_phase):
                            add_issue(issues, "FAIL", "INCOMPLETE_PHASE_GUIDANCE", f"Phase guidance {phase_index} needs {', '.join(required_phase)}")
                            continue
                        phase_type = str(phase.get("phase_type", "")).strip()
                        phase_types.add(phase_type)
                        if phase_type not in PHASE_TYPES:
                            add_issue(issues, "FAIL", "INVALID_PHASE_TYPE", f"Phase guidance {phase_index} has unsupported phase_type: {phase_type}")
                        load_guide = str(phase.get("long_session_distance_or_time", "")).strip()
                        if not LOAD_GUIDE_RE.search(load_guide):
                            add_issue(issues, "FAIL", "NON_NUMERIC_PHASE_LOAD", f"Phase guidance {phase_index} needs a numeric distance or time guide, not only a vague progression phrase")
                        phase_slide = phase.get("slide")
                        if not isinstance(phase_slide, int) or not 1 <= phase_slide <= len(slides):
                            add_issue(issues, "FAIL", "PHASE_GUIDANCE_SLIDE", f"Phase guidance {phase_index} must identify a valid slide")
                        else:
                            shown = visible_slide_text(slides[phase_slide - 1])
                            if str(phase.get("period")) not in shown or load_guide not in shown:
                                add_issue(issues, "FAIL", "PHASE_GUIDANCE_NOT_VISIBLE", f"Phase guidance {phase_index} period and load guide must be visible on slide {phase_slide}")
                    if safety.get("event_preparation") is True and not phase_types.intersection({"recovery", "taper"}):
                        add_issue(issues, "FAIL", "MISSING_EVENT_RECOVERY_PHASE", "Event preparation needs a recovery or taper phase")

                session_guidance = safety.get("session_guidance")
                if not isinstance(session_guidance, list) or not session_guidance:
                    add_issue(issues, "FAIL", "MISSING_SESSION_GUIDANCE", "A progressive exercise plan needs session guidance with pace or effort, purpose, and adjustment conditions")
                else:
                    required = ("session_type", "pace_or_effort", "purpose", "adjustment_condition", "intensity_class", "basis")
                    intensities: list[str] = []
                    for session_index, session in enumerate(session_guidance, 1):
                        if not isinstance(session, dict) or any(not str(session.get(field, "")).strip() for field in required):
                            add_issue(issues, "FAIL", "INCOMPLETE_SESSION_GUIDANCE", f"Session guidance {session_index} needs {', '.join(required)}")
                            continue
                        intensity = str(session.get("intensity_class", "")).strip()
                        intensities.append(intensity)
                        if intensity not in SESSION_INTENSITIES:
                            add_issue(issues, "FAIL", "INVALID_SESSION_INTENSITY", f"Session guidance {session_index} has unsupported intensity_class: {intensity}")
                    if safety.get("novice_or_returning") is True:
                        if not any(item in {"easy", "recovery"} for item in intensities):
                            add_issue(issues, "FAIL", "MISSING_EASY_SESSION", "A beginner or return-from-injury plan needs an explicit easy or recovery session")
                        if intensities.count("quality") > 1:
                            add_issue(issues, "FAIL", "TOO_MANY_QUALITY_SESSIONS", "A beginner or return-from-injury plan should not prescribe more than one recurring quality session")
    issues.extend(validate_high_stakes_semantics(deck, slides))
    body_limit = 120 if mode == "presented" else 220
    saw_source_marker = False
    saw_sources_slide = False
    consecutive_text_only = 0
    meaningful_visuals = 0
    content_slide_count = 0
    referenced_source_ids: set[str] = set()
    appendix_source_ids: set[str] = set()

    for index, slide in enumerate(slides, 1):
        if not isinstance(slide, dict):
            add_issue(issues, "FAIL", "INVALID_SLIDE", "Each slide must be an object", index)
            continue
        layout = slide.get("layout")
        title = str(slide.get("title", "")).strip()
        if layout not in ALLOWED_LAYOUTS:
            add_issue(issues, "FAIL", "INVALID_LAYOUT", f"Unsupported layout: {layout}", index)
        if layout != "cover" and not title:
            add_issue(issues, "FAIL", "MISSING_TITLE", "A non-cover slide needs a title", index)
        if title and len(title) > 34:
            add_issue(issues, "WARN", "LONG_TITLE", "Title may wrap; shorten or verify at full size", index)
        if PLACEHOLDER_RE.search(json.dumps(slide, ensure_ascii=False)):
            add_issue(issues, "FAIL", "PLACEHOLDER", "Unresolved placeholder text remains", index)

        if layout == "cover":
            if index != 1:
                add_issue(issues, "WARN", "COVER_POSITION", "Cover is normally the first slide", index)
            if not title:
                add_issue(issues, "FAIL", "COVER_TITLE", "Cover needs a title", index)
            if not str(slide.get("date", "")).strip():
                add_issue(issues, "FAIL", "COVER_DATE", "Cover needs a date", index)

        if layout not in {"cover", "sources_appendix"}:
            content_slide_count += 1
            job = str(slide.get("job", "")).strip()
            visual_role = str(slide.get("visual_role", "")).strip()
            if job not in ALLOWED_JOBS:
                add_issue(issues, "FAIL", "MISSING_JOB", "Each content slide needs one supported narrative job", index)
            if visual_role not in ALLOWED_VISUAL_ROLES:
                add_issue(issues, "FAIL", "MISSING_VISUAL_ROLE", "Each content slide needs a visual_role", index)
            if visual_role == "none" and not str(slide.get("visual_reason", "")).strip():
                add_issue(issues, "FAIL", "MISSING_VISUAL_REASON", "A text-only slide needs a content-based reason", index)
            if visual_role in {"none", "decoration"}:
                consecutive_text_only += 1
                if consecutive_text_only >= 4:
                    add_issue(issues, "FAIL", "VISUAL_CADENCE", "Four text-only or decoration-only slides appear consecutively", index)
            else:
                meaningful_visuals += 1
                consecutive_text_only = 0
            source_marker = str(slide.get("source", "")).strip()
            if high_stakes and job in {"claim", "instruction"} and not source_marker:
                add_issue(issues, "FAIL", "HIGH_STAKES_SOURCE", "High-stakes claim and instruction slides need a short source marker", index)
            if source_marker:
                marker_ids = set(SOURCE_ID_RE.findall(source_marker))
                referenced_source_ids.update(marker_ids)
                if high_stakes and not marker_ids:
                    add_issue(issues, "FAIL", "UNSTRUCTURED_SOURCE_MARKER", "High-stakes source markers must cite appendix IDs such as [S1]", index)

        bullets = slide.get("bullets", [])
        if isinstance(bullets, list) and len(bullets) > 4:
            add_issue(issues, "WARN", "TOO_MANY_BULLETS", "Use four or fewer bullets or split the slide", index)
        if text_len(slide.get("body")) + text_len(bullets) > body_limit:
            add_issue(issues, "WARN", "TEXT_DENSITY", "Body content exceeds the normal density guide", index)

        if layout == "agenda":
            sections = slide.get("sections", [])
            if not isinstance(sections, list) or not 3 <= len(sections) <= 5:
                add_issue(issues, "FAIL", "AGENDA_SECTIONS", "Agenda needs three to five sections", index)
        elif layout == "section_divider":
            if not str(slide.get("section", "")).strip():
                add_issue(issues, "FAIL", "SECTION_LABEL", "Section divider needs a section label", index)
        elif layout in {"text_focus", "text_visual"}:
            if layout == "text_visual" and not str(slide.get("image", "")).strip():
                add_issue(issues, "FAIL", "TEXT_VISUAL_IMAGE", "Text visual layout needs a local image", index)
            if slide.get("visual_role") in {"explain", "context"} and not slide.get("image") and not slide.get("callout"):
                add_issue(issues, "FAIL", "UNREALIZED_VISUAL_ROLE", "Explain/context role needs an image or meaningful callout composition", index)
        elif layout == "comparison":
            columns = slide.get("columns", [])
            if not isinstance(columns, list) or len(columns) not in (2, 3):
                add_issue(issues, "FAIL", "COMPARISON_COLUMNS", "Comparison needs two or three columns", index)
        elif layout == "process":
            steps = slide.get("steps", [])
            if not isinstance(steps, list) or not 3 <= len(steps) <= 6:
                add_issue(issues, "FAIL", "PROCESS_STEPS", "Process needs three to six steps", index)
        elif layout == "data_focus":
            stats = slide.get("stats", [])
            if not isinstance(stats, list) or not 1 <= len(stats) <= 4:
                add_issue(issues, "FAIL", "STAT_COUNT", "Data focus needs one to four stats", index)
        elif layout == "bar_chart":
            bars = slide.get("bars", [])
            maximum = slide.get("max_value")
            if not isinstance(bars, list) or not 3 <= len(bars) <= 8:
                add_issue(issues, "FAIL", "BAR_COUNT", "Bar chart needs three to eight bars", index)
            if not isinstance(maximum, (int, float)) or maximum <= 0:
                add_issue(issues, "FAIL", "BAR_MAX", "Bar chart needs a positive max_value", index)
            for bar in bars if isinstance(bars, list) else []:
                if not isinstance(bar.get("value"), (int, float)) or bar.get("value", 0) < 0:
                    add_issue(issues, "FAIL", "BAR_VALUE", "Each bar needs a non-negative numeric value", index)
        elif layout == "table":
            headers, rows = slide.get("headers", []), slide.get("rows", [])
            if not isinstance(headers, list) or not headers:
                add_issue(issues, "FAIL", "TABLE_HEADERS", "Table needs headers", index)
            if not isinstance(rows, list) or not rows:
                add_issue(issues, "FAIL", "TABLE_ROWS", "Table needs rows", index)
            if isinstance(headers, list) and len(headers) > 4:
                add_issue(issues, "WARN", "TABLE_COLUMNS", "More than four columns may be unreadable", index)
            if isinstance(rows, list) and len(rows) > 8:
                add_issue(issues, "WARN", "TABLE_LENGTH", "More than eight rows may overflow", index)
            if isinstance(headers, list) and isinstance(rows, list):
                for row in rows:
                    if not isinstance(row, list) or len(row) != len(headers):
                        add_issue(issues, "FAIL", "TABLE_SHAPE", "Each row must match the header count", index)
        elif layout == "decision_flow":
            for field in ("question", "yes_action", "no_action"):
                if not str(slide.get(field, "")).strip():
                    add_issue(issues, "FAIL", "DECISION_FLOW_FIELD", f"Decision flow needs {field}", index)
        elif layout == "sources_appendix":
            saw_sources_slide = True
            sources = slide.get("sources", [])
            if not isinstance(sources, list) or not sources:
                add_issue(issues, "FAIL", "EMPTY_SOURCES", "Sources slide needs at least one source", index)
            else:
                for source in sources:
                    if not isinstance(source, dict):
                        add_issue(issues, "FAIL", "INVALID_SOURCE", "Each source must be an object", index)
                        continue
                    source_id = str(source.get("id", "")).strip()
                    if not source_id:
                        add_issue(issues, "FAIL", "MISSING_SOURCE_ID", "Each source needs an ID", index)
                        continue
                    if source_id in appendix_source_ids:
                        add_issue(issues, "FAIL", "DUPLICATE_SOURCE_ID", f"Duplicate source ID: {source_id}", index)
                    appendix_source_ids.add(source_id)
                    for field in ("title", "publisher", "checked"):
                        if not str(source.get(field, "")).strip():
                            add_issue(issues, "FAIL", "INCOMPLETE_SOURCE", f"Source {source_id} needs {field}", index)
                    if source_id.upper().startswith("S") and not str(source.get("url", "")).strip():
                        add_issue(issues, "FAIL", "MISSING_SOURCE_URL", f"External source {source_id} needs a URL", index)
        elif layout == "exercise":
            if not str(slide.get("prompt", "")).strip():
                add_issue(issues, "FAIL", "EXERCISE_PROMPT", "Exercise layout needs a learner-facing prompt", index)

        if str(slide.get("source", "")).strip():
            saw_source_marker = True

    if saw_source_marker and not saw_sources_slide:
        add_issue(issues, "FAIL", "MISSING_SOURCES_SLIDE", "Short source markers exist but no sources appendix exists")
    if high_stakes and not saw_sources_slide:
        add_issue(issues, "FAIL", "MISSING_SOURCES_SLIDE", "A high-stakes deck needs a sources appendix")
    if saw_sources_slide and slides[-1].get("layout") != "sources_appendix":
        add_issue(issues, "WARN", "SOURCES_POSITION", "Sources appendix is normally the final slide")
    missing_source_ids = sorted(referenced_source_ids - appendix_source_ids)
    if missing_source_ids:
        add_issue(issues, "FAIL", "UNRESOLVED_SOURCE_ID", f"Source markers are missing from the appendix: {', '.join(missing_source_ids)}")
    unused_source_ids = sorted(appendix_source_ids - referenced_source_ids)
    if unused_source_ids and referenced_source_ids:
        add_issue(issues, "WARN", "UNUSED_SOURCE_ID", f"Appendix sources are not cited on a slide: {', '.join(unused_source_ids)}")
    if content_slide_count >= 6 and meaningful_visuals < max(2, round(content_slide_count * 0.35)):
        add_issue(issues, "WARN", "LOW_VISUAL_COVERAGE", "Too few content slides use evidence, explanation, or context visuals")
    return issues


def bullet_list(items: object) -> str:
    if not isinstance(items, list) or not items:
        return ""
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def image_uri(value: object, base_dir: Path) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("data:"):
        return raw
    if raw.startswith(("http://", "https://")):
        raise ValueError("Remote image URLs are not self-contained; download the approved asset and reference the local file")
    path = Path(raw)
    if not path.is_absolute():
        path = base_dir / path
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def render_body(slide: dict, base_dir: Path) -> str:
    layout = slide["layout"]
    if layout == "cover":
        eyebrow = f'<div class="eyebrow">{esc(slide.get("eyebrow"))}</div>' if slide.get("eyebrow") else ""
        subtitle = f'<p class="subtitle">{esc(slide.get("subtitle"))}</p>' if slide.get("subtitle") else ""
        return f'{eyebrow}<h1>{esc(slide.get("title"))}</h1>{subtitle}<div class="accent-line"></div><div class="date">{esc(slide.get("date"))}</div>'

    title = f'<h2>{esc(slide.get("title"))}</h2>'
    lead = f'<p class="lead">{esc(slide.get("lead"))}</p>' if slide.get("lead") else ""

    if layout == "agenda":
        sections = "".join(
            f'<article class="agenda-item"><div class="agenda-number">{i:02d}</div><h3>{esc(item.get("title"))}</h3><p>{esc(item.get("body"))}</p></article>'
            for i, item in enumerate(slide.get("sections", []), 1)
        )
        return f'{title}{lead}<div class="agenda-list" style="--section-count:{len(slide.get("sections", []))}">{sections}</div>'

    if layout == "section_divider":
        copy = f'<p class="section-copy">{esc(slide.get("body"))}</p>' if slide.get("body") else ""
        return f'<div class="section-kicker">{esc(slide.get("section"))}</div><h2>{esc(slide.get("title"))}</h2>{copy}'

    if layout == "single_message":
        support = f'<p class="headline-support">{esc(slide.get("body"))}</p>' if slide.get("body") else ""
        return f'{title}<div class="message-stage"><div class="message-value">{esc(slide.get("headline"))}</div><div class="message-copy">{support}</div></div>'

    if layout in {"text_focus", "text_visual"}:
        body = f'<p>{esc(slide.get("body"))}</p>' if slide.get("body") else ""
        callout = f'<div class="callout">{esc(slide.get("callout"))}</div>' if slide.get("callout") else ""
        text_block = f'<div class="text-focus-main">{lead}{body}{bullet_list(slide.get("bullets"))}</div>'
        if slide.get("image"):
            uri = esc(image_uri(slide.get("image"), base_dir))
            image = f'<div class="image-frame"><img src="{uri}" alt="{esc(slide.get("image_alt", ""))}"></div>'
            reverse = " reverse" if slide.get("image_position") == "left" else ""
            parts = image + text_block if reverse else text_block + image
            return f'{title}<div class="image-layout{reverse}">{parts}</div>'
        if callout:
            return f'{title}<div class="text-focus-grid">{text_block}{callout}</div>'
        return f'{title}{lead}{body}{bullet_list(slide.get("bullets"))}'

    if layout == "comparison":
        columns = slide.get("columns", [])
        count_class = "three" if len(columns) == 3 else "two"
        panels = []
        for column in columns:
            tone = str(column.get("tone", "")).strip()
            tone_class = f" {tone}" if tone in {"mint", "neutral"} else ""
            paragraph = f'<p>{esc(column.get("body"))}</p>' if column.get("body") else ""
            heading = column.get("heading") or column.get("title")
            panels.append(f'<article class="panel{tone_class}"><h3>{esc(heading)}</h3>{paragraph}{bullet_list(column.get("bullets"))}</article>')
        return f'{title}{lead}<div class="columns {count_class}">{"".join(panels)}</div>'

    if layout == "process":
        steps = slide.get("steps", [])
        cards = "".join(
            f'<article class="step"><div class="step-label">{esc(step.get("label"))}</div><h3>{esc(step.get("title"))}</h3><p>{esc(step.get("body"))}</p></article>'
            for step in steps
        )
        return f'{title}{lead}<div class="process-grid" style="--step-count:{len(steps)}">{cards}</div>'

    if layout == "data_focus":
        stats = slide.get("stats", [])
        cards = "".join(
            f'<article class="stat"><div class="stat-value">{esc(stat.get("value"))}</div><div class="stat-label">{esc(stat.get("label"))}</div><div class="stat-note">{esc(stat.get("note"))}</div></article>'
            for stat in stats
        )
        return f'{title}{lead}<div class="stats" style="--stat-count:{len(stats)}">{cards}</div>{bullet_list(slide.get("bullets"))}'

    if layout == "bar_chart":
        maximum = float(slide.get("max_value", 1))
        rows = []
        for bar in slide.get("bars", []):
            width = min(100, max(0, float(bar.get("value", 0)) / maximum * 100))
            display = bar.get("display") or bar.get("value")
            rows.append(f'<div class="bar-row"><div class="bar-label">{esc(bar.get("label"))}</div><div class="bar-track"><div class="bar-fill" style="width:{width:.2f}%"></div></div><div class="bar-display">{esc(display)}</div></div>')
        note = f'<p class="note">{esc(slide.get("note"))}</p>' if slide.get("note") else ""
        return f'{title}{lead}<div class="bar-chart">{"".join(rows)}</div>{note}'

    if layout == "table":
        headers = "".join(f"<th>{esc(value)}</th>" for value in slide.get("headers", []))
        rows = "".join("<tr>" + "".join(f"<td>{esc(value)}</td>" for value in row) + "</tr>" for row in slide.get("rows", []))
        note = f'<p class="note">{esc(slide.get("note"))}</p>' if slide.get("note") else ""
        return f'{title}{lead}<div class="table-wrap"><table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>{note}'

    if layout == "decision_flow":
        footer = f'<div class="decision-footer">{esc(slide.get("footer"))}</div>' if slide.get("footer") else ""
        return (
            f'{title}{lead}<div class="decision-flow">'
            f'<div class="decision-question">{esc(slide.get("question"))}</div>'
            f'<div class="decision-branches">'
            f'<article class="decision-branch stop"><div class="decision-label">{esc(slide.get("yes_label", "はい"))}</div><h3>{esc(slide.get("yes_action"))}</h3></article>'
            f'<article class="decision-branch go"><div class="decision-label">{esc(slide.get("no_label", "いいえ"))}</div><h3>{esc(slide.get("no_action"))}</h3></article>'
            f'</div>{footer}</div>'
        )

    if layout == "summary_action":
        actions = "".join(f'<div class="action"><span class="action-number">{i:02d}</span><span>{esc(item)}</span></div>' for i, item in enumerate(slide.get("actions", []), 1))
        note = f'<p class="note">{esc(slide.get("note"))}</p>' if slide.get("note") else ""
        return f'{title}<div class="headline" style="margin-top:20px;text-align:left;font-size:48px">{esc(slide.get("headline"))}</div><div class="actions">{actions}</div>{note}'

    if layout == "exercise":
        checks = bullet_list(slide.get("checks"))
        return f'{title}{lead}<div class="exercise-box"><div class="exercise-prompt">{esc(slide.get("prompt"))}</div><div class="exercise-check"><h3>{esc(slide.get("check_title", "確認"))}</h3>{checks}</div></div>'

    if layout == "sources_appendix":
        items = []
        for source in slide.get("sources", []):
            meta = " / ".join(filter(None, [str(source.get("publisher", "")).strip(), str(source.get("url", "")).strip(), f'確認日 {source.get("checked")}' if source.get("checked") else ""]))
            items.append(f'<div class="source-item"><div class="source-id">[{esc(source.get("id"))}]</div><div><div class="source-main">{esc(source.get("title"))}</div><div class="source-meta">{esc(meta)}</div></div></div>')
        return f'{title}<div class="sources-list">{"".join(items)}</div>'

    raise ValueError(f"Unsupported layout: {layout}")


def render_slide(slide: dict, index: int, total: int, base_dir: Path) -> str:
    layout = slide["layout"]
    source = str(slide.get("source", "")).strip()
    source_html = f'<div class="slide-source">{esc(source)}</div>' if source else ""
    active = " active" if index == 1 else ""
    no_decor = " no-decor" if slide.get("no_decor") else ""
    visual_role = esc(slide.get("visual_role", "special"))
    job = esc(slide.get("job", "special"))
    return (
        f'    <section class="slide {esc(layout)}{active}{no_decor}" data-slide="{index}" data-job="{job}" data-visual-role="{visual_role}" aria-label="{index} / {total}">\n'
        f'      <div class="content">{render_body(slide, base_dir)}</div>\n'
        f'      {source_html}<div class="page-number">{index:02d}</div>\n'
        f'    </section>'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--work-state", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    work_state_path = Path(args.work_state).resolve()
    template_path = Path(args.template).resolve()
    output_path = Path(args.output).resolve()
    report_path = Path(args.report).resolve()

    try:
        work_state = json.loads(work_state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues = [{"level": "FAIL", "code": "PRODUCTION_NOT_APPROVED", "message": f"Approval record is unavailable: {exc}"}]
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "FAIL", "issues": issues}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "FAIL", "issues": issues}, ensure_ascii=False))
        return 2

    approval_issues = validate_approval(work_state)
    if approval_issues:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "FAIL", "issues": approval_issues}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "FAIL", "issues": approval_issues}, ensure_ascii=False))
        return 2

    try:
        deck = json.loads(input_path.read_text(encoding="utf-8"))
        issues = validate(deck)
    except Exception as exc:
        issues = [{"level": "FAIL", "code": "INPUT_ERROR", "message": str(exc)}]
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"status": "FAIL", "issues": issues}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"status": "FAIL", "issues": issues}, ensure_ascii=False))
        return 2

    failures = [item for item in issues if item["level"] == "FAIL"]
    report = {
        "status": "FAIL" if failures else "PASS",
        "slide_count": len(deck["slides"]),
        "warning_count": sum(item["level"] == "WARN" for item in issues),
        "issues": issues,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures:
        print(json.dumps(report, ensure_ascii=False))
        return 2

    template = template_path.read_text(encoding="utf-8")
    if any(marker not in template for marker in ("__DECK_TITLE__", "__SLIDES__", "__FONT_DATA__", "__DECK_DATA__")):
        print("Template markers are missing", file=sys.stderr)
        return 2
    font_path = template_path.parent / "fonts" / "NotoSansJP-Variable.ttf"
    if not font_path.is_file():
        print(f"Bundled font is missing: {font_path}", file=sys.stderr)
        return 2
    font_data = base64.b64encode(font_path.read_bytes()).decode("ascii")
    slides_html = "\n".join(render_slide(slide, i, len(deck["slides"]), input_path.parent) for i, slide in enumerate(deck["slides"], 1))
    deck_data = json.dumps(deck, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    result = template.replace("__DECK_TITLE__", esc(deck.get("deck_title", "Slide Deck"))).replace("__FONT_DATA__", font_data).replace("__SLIDES__", slides_html).replace("__DECK_DATA__", deck_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "html": str(output_path), "report": str(report_path), "slide_count": len(deck["slides"]), "warnings": report["warning_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
