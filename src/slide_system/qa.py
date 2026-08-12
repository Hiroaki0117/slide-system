from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .designs import DesignPack
from .runs import now_iso
from .storage import atomic_write_json, read_json
from .validation import validate_document


CRITICAL_CODES = {
    "FONT_LOAD",
    "MISSING_SAFETY_MODEL",
    "MISSING_CURRENT_CONDITION",
    "MISSING_SAFETY_CONDITION",
    "HIGH_STAKES_SOURCE",
    "MISSING_SOURCES_SLIDE",
    "AUTHORITATIVE_SOURCE_REQUIRED",
    "MISSING_CONTENT_CONTRACT",
    "CONTENT_ITEM_UNMAPPED",
    "CONTENT_EVIDENCE_MISSING",
    "CONTENT_SOURCE_MISSING",
    "RESEARCH_SOURCE_MISSING",
    "RESEARCH_SOURCE_UNUSED",
}


def _issue(
    sequence: int,
    *,
    gate: str,
    rule: str,
    requirement: str,
    severity: str,
    message: str,
    slide: int | str | None = None,
    evidence: str | None = None,
    suggested_fix: str | None = None,
) -> dict[str, Any]:
    return {
        "id": f"qa-{sequence:03d}",
        "gate": gate,
        "rule": rule,
        "requirement": requirement,
        "severity": severity,
        "status": "open",
        "slide_id": str(slide) if slide is not None else None,
        "block_id": None,
        "message": message,
        "evidence": evidence,
        "suggested_fix": suggested_fix,
    }


def _static_issues(report: dict[str, Any], start: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for offset, item in enumerate(report.get("issues", []), start):
        level = str(item.get("level", "FAIL")).upper()
        code = str(item.get("code", "STATIC_QA"))
        requirement = "MUST" if level == "FAIL" else "SHOULD"
        severity = "critical" if code in CRITICAL_CODES else ("major" if level == "FAIL" else "minor")
        normalized.append(
            _issue(
                offset,
                gate="static",
                rule=code,
                requirement=requirement,
                severity=severity,
                message=str(item.get("message", code)),
                slide=item.get("slide"),
                evidence="static-qa-legacy.json",
                suggested_fix="deck.jsonの該当内容を修正し、新しいAttemptを作成してください",
            )
        )
    return normalized


def _content_issues(report: dict[str, Any], start: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for offset, item in enumerate(report.get("issues", []), start):
        level = str(item.get("level", "FAIL")).upper()
        code = str(item.get("code", "CONTENT_QA"))
        normalized.append(
            _issue(
                offset,
                gate="content",
                rule=code,
                requirement="MUST" if level == "FAIL" else "SHOULD",
                severity="critical" if level == "FAIL" else "minor",
                message=str(item.get("message", code)),
                slide=item.get("slide"),
                evidence="content-qa.json",
                suggested_fix="承認済み内容契約とdeck.jsonの掲載内容・出典・掲載先を一致させてください",
            )
        )
    return normalized


def _visual_issues(report: dict[str, Any], start: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for offset, item in enumerate(report.get("failures", []), start):
        code = str(item.get("code", "VISUAL_QA"))
        normalized.append(
            _issue(
                offset,
                gate="visual" if not code.startswith("PDF_") else "pdf",
                rule=code,
                requirement="MUST",
                severity="critical" if code in {"FONT_LOAD", "PDF_PAGE_COUNT"} else "major",
                message=str(item.get("message") or code),
                slide=item.get("slide"),
                evidence=str(item.get("details") or "visual-qa-legacy.json"),
                suggested_fix="レンダリング結果を確認し、レイアウトまたは文字量を修正してください",
            )
        )
    return normalized


def _theme_issues(html_path: Path, design_pack: DesignPack, start: int) -> tuple[list[dict[str, Any]], int]:
    html = html_path.read_text(encoding="utf-8").casefold() if html_path.is_file() else ""
    issues: list[dict[str, Any]] = []
    passed = 0
    sequence = start
    if re.search(r"(?:linear|radial|conic)-gradient\s*\(", html):
        issues.append(
            _issue(
                sequence,
                gate="theme",
                rule="warm-clean-no-gradient",
                requirement="MUST",
                severity="major",
                message="warm_cleanではグラデーションを使用できません",
                evidence="deck.html内にgradient指定があります",
                suggested_fix="単色の背景または図形へ置き換えてください",
            )
        )
        sequence += 1
    else:
        passed += 1
    colors = read_json(design_pack.entrypoints["colors"])
    background_token = colors.get("background", "#fff8f4")
    if isinstance(background_token, dict):
        background_token = background_token.get("primary", "#fff8f4")
    expected_background = str(background_token).casefold()
    if expected_background not in html:
        issues.append(
            _issue(
                sequence,
                gate="theme",
                rule="warm-clean-background",
                requirement="MUST",
                severity="major",
                message=f"既定背景色{expected_background.upper()}を確認できません",
                evidence="deck.html",
                suggested_fix="デザインパックの背景トークンを適用してください",
            )
        )
    else:
        passed += 1
    return issues, passed


def create_qa_report(
    project_root: Path,
    *,
    run_id: str,
    attempt: int,
    attempt_dir: Path,
    design_pack: DesignPack,
) -> dict[str, Any]:
    static_path = attempt_dir / "static-qa-legacy.json"
    visual_path = attempt_dir / "visual-qa-legacy.json"
    content_path = attempt_dir / "content-qa.json"
    html_path = attempt_dir / "deck.html"
    static = read_json(static_path) if static_path.is_file() else {"status": "FAIL", "issues": [{"level": "FAIL", "code": "STATIC_REPORT_MISSING", "message": "静的QAレポートがありません"}]}
    visual = read_json(visual_path) if visual_path.is_file() else {"status": "FAIL", "failures": [{"code": "VISUAL_REPORT_MISSING", "message": "視覚QAレポートがありません"}]}
    content = read_json(content_path) if content_path.is_file() else {"status": "PASS", "issues": []}
    issues = _content_issues(content, 1)
    if content.get("status") == "FAIL":
        must_failures = sum(1 for item in issues if item["requirement"] == "MUST" and item["status"] == "open")
        report = {
            "schema_version": "1.0",
            "run_id": run_id,
            "attempt": attempt,
            "result": "FAIL",
            "summary": {"passed": 0, "failed": must_failures, "warnings": 0},
            "issues": issues,
            "gates": {"content": "FAIL", "static": "NOT_RUN", "visual": "NOT_RUN", "pdf_parity": "NOT_RUN", "theme": "NOT_RUN"},
            "legacy_reports": {"content": "content-qa.json"},
            "checked_at": now_iso(),
        }
        validate_document(project_root, "qa-report", report)
        atomic_write_json(attempt_dir / "qa-report.json", report)
        return report
    issues.extend(_static_issues(static, len(issues) + 1))
    issues.extend(_visual_issues(visual, len(issues) + 1))
    theme_issues, theme_passed = _theme_issues(html_path, design_pack, len(issues) + 1)
    issues.extend(theme_issues)
    must_failures = sum(1 for item in issues if item["requirement"] == "MUST" and item["status"] == "open")
    warnings = sum(1 for item in issues if item["requirement"] != "MUST" and item["status"] == "open")
    passed_gates = int(content.get("status") == "PASS") + int(static.get("status") == "PASS") + int(visual.get("status") == "PASS") + theme_passed
    report = {
        "schema_version": "1.0",
        "run_id": run_id,
        "attempt": attempt,
        "result": "FAIL" if must_failures else "PASS",
        "summary": {"passed": passed_gates, "failed": must_failures, "warnings": warnings},
        "issues": issues,
        "gates": {
            "content": content.get("status", "FAIL"),
            "static": static.get("status", "FAIL"),
            "visual": visual.get("status", "FAIL"),
            "pdf_parity": "PASS" if visual.get("detected_pdf_pages") == visual.get("slide_count") else "FAIL",
            "theme": "FAIL" if theme_issues else "PASS",
        },
        "legacy_reports": {"content": "content-qa.json", "static": "static-qa-legacy.json", "visual": "visual-qa-legacy.json"},
        "checked_at": now_iso(),
    }
    validate_document(project_root, "qa-report", report)
    atomic_write_json(attempt_dir / "qa-report.json", report)
    return report
