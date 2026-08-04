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


def add_issue(issues: list[dict], level: str, code: str, message: str, slide: int | None = None) -> None:
    item = {"level": level, "code": code, "message": message}
    if slide is not None:
        item["slide"] = slide
    issues.append(item)


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
    body_limit = 120 if mode == "presented" else 220
    saw_source_marker = False
    saw_sources_slide = False
    consecutive_text_only = 0
    meaningful_visuals = 0
    content_slide_count = 0

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
        elif layout == "exercise":
            if not str(slide.get("prompt", "")).strip():
                add_issue(issues, "FAIL", "EXERCISE_PROMPT", "Exercise layout needs a learner-facing prompt", index)

        if str(slide.get("source", "")).strip():
            saw_source_marker = True

    if saw_source_marker and not saw_sources_slide:
        add_issue(issues, "FAIL", "MISSING_SOURCES_SLIDE", "Short source markers exist but no sources appendix exists")
    if saw_sources_slide and slides[-1].get("layout") != "sources_appendix":
        add_issue(issues, "WARN", "SOURCES_POSITION", "Sources appendix is normally the final slide")
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
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    template_path = Path(args.template).resolve()
    output_path = Path(args.output).resolve()
    report_path = Path(args.report).resolve()

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
    if "__DECK_TITLE__" not in template or "__SLIDES__" not in template or "__FONT_DATA__" not in template:
        print("Template markers are missing", file=sys.stderr)
        return 2
    font_path = template_path.parent / "fonts" / "NotoSansJP-Variable.ttf"
    if not font_path.is_file():
        print(f"Bundled font is missing: {font_path}", file=sys.stderr)
        return 2
    font_data = base64.b64encode(font_path.read_bytes()).decode("ascii")
    slides_html = "\n".join(render_slide(slide, i, len(deck["slides"]), input_path.parent) for i, slide in enumerate(deck["slides"], 1))
    result = template.replace("__DECK_TITLE__", esc(deck.get("deck_title", "Slide Deck"))).replace("__FONT_DATA__", font_data).replace("__SLIDES__", slides_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "html": str(output_path), "report": str(report_path), "slide_count": len(deck["slides"]), "warnings": report["warning_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
