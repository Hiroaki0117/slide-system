from __future__ import annotations

from pathlib import Path
from typing import Any

from .designs import DesignPack, load_layout_registry


class DeckConversionError(ValueError):
    pass


def _blocks(slide: dict[str, Any], block_type: str) -> list[dict[str, Any]]:
    return [block for block in slide.get("blocks", []) if block.get("type") == block_type]


def _first_text(blocks: list[dict[str, Any]], *fields: str) -> str:
    for block in blocks:
        for field in fields:
            value = str(block.get(field, "")).strip()
            if value:
                return value
    return ""


def _bullet_items(slide: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for block in _blocks(slide, "bullets"):
        values = block.get("items", [])
        if isinstance(values, list):
            items.extend(str(item).strip() for item in values if str(item).strip())
    return items


def _source_marker(slide: dict[str, Any], source_ids: set[str]) -> str:
    refs = slide.get("source_refs", [])
    missing = [source_id for source_id in refs if source_id not in source_ids]
    if missing:
        raise DeckConversionError(f"未定義の出典IDがあります: {', '.join(missing)}")
    return " ".join(f"[{source_id}]" for source_id in refs)


def _visual_role(slide: dict[str, Any], legacy_layout: str) -> tuple[str, str | None]:
    visual = slide.get("visual", {})
    strategy = str(visual.get("strategy", "")).strip().casefold()
    if legacy_layout in {"data_focus", "bar_chart", "table"}:
        return "evidence", None
    if legacy_layout in {"comparison", "process", "decision_flow", "exercise"}:
        return "explain", None
    if legacy_layout == "text_visual":
        return "context", None
    if strategy in {"none", "text_only"}:
        reason = str(visual.get("reason", "")).strip() or "文章の理解を優先するページのため"
        return "none", reason
    if strategy in {"decorative_shapes", "decoration"}:
        return "decoration", None
    if strategy in {"image", "photo", "illustration"}:
        return "context", None
    if strategy in {"chart", "data", "evidence"}:
        return "evidence", None
    if strategy in {"diagram", "comparison_graphic", "process", "explain"}:
        return "explain", None
    return "decoration", None


def _job(legacy_layout: str, role: str) -> str:
    if legacy_layout == "comparison":
        return "compare"
    if legacy_layout in {"data_focus", "bar_chart", "table"}:
        return "evidence"
    if legacy_layout in {"decision_flow"}:
        return "instruction"
    if legacy_layout == "exercise":
        return "exercise"
    if legacy_layout == "summary_action" or role == "summary":
        return "summary"
    if legacy_layout in {"agenda", "section_divider"}:
        return "transition"
    if legacy_layout == "single_message":
        return "claim"
    return "explain"


def _comparison_columns(slide: dict[str, Any]) -> list[dict[str, Any]]:
    columns: list[dict[str, Any]] = []
    for block in _blocks(slide, "comparison"):
        candidates = block.get("items") or block.get("columns")
        if isinstance(candidates, list):
            columns.extend(item for item in candidates if isinstance(item, dict))
        else:
            columns.append(block)
    return [
        {
            "heading": item.get("heading") or item.get("title") or item.get("label"),
            "body": item.get("body") or item.get("text") or "",
            "bullets": item.get("bullets") or [],
            **({"tone": item["tone"]} if item.get("tone") else {}),
        }
        for item in columns
    ]


def _process_steps(slide: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for block_type in ("process", "timeline"):
        for block in _blocks(slide, block_type):
            candidates = block.get("items") or block.get("steps")
            if isinstance(candidates, list):
                steps.extend(item for item in candidates if isinstance(item, dict))
    return [
        {
            "label": item.get("label") or str(index),
            "title": item.get("title") or item.get("heading") or "",
            "body": item.get("body") or item.get("text") or "",
        }
        for index, item in enumerate(steps, 1)
    ]


def _legacy_sources(deck: dict[str, Any], source_refs: list[str] | None = None) -> list[dict[str, Any]]:
    selected_ids = set(source_refs or [])
    result = []
    for source in deck.get("sources", []):
        source_id = str(source.get("id", "")).strip()
        if selected_ids and source_id not in selected_ids:
            continue
        title = str(source.get("title", "")).strip()
        publisher = str(source.get("publisher") or "").strip()
        checked = str(source.get("accessed_at") or "").strip()
        url = str(source.get("url") or "").strip()
        source_class = str(source.get("source_class") or ("secondary" if url else "user_supplied")).strip()
        missing = [name for name, value in (("id", source_id), ("title", title), ("publisher", publisher), ("accessed_at", checked)) if not value]
        if missing:
            raise DeckConversionError(f"出典に必要な項目がありません ({source_id or 'ID不明'}): {', '.join(missing)}")
        if source_class != "user_supplied" and not url:
            raise DeckConversionError(f"外部出典にはURLが必要です: {source_id}")
        result.append(
            {
                "id": source_id,
                "title": title,
                "publisher": publisher,
                "url": url,
                "checked": checked,
                "source_class": source_class,
            }
        )
    return result


def convert_deck_to_legacy(
    deck: dict[str, Any],
    pack: DesignPack,
    *,
    asset_base: Path | None = None,
) -> dict[str, Any]:
    if pack.manifest["renderer"]["adapter"] != "legacy_warm_clean":
        raise DeckConversionError(f"未対応のレンダラーです: {pack.manifest['renderer']['adapter']}")
    registry = load_layout_registry(pack)
    metadata = deck["metadata"]
    context = deck["context"]
    source_ids = {str(source.get("id", "")) for source in deck.get("sources", [])}
    legacy_slides: list[dict[str, Any]] = []
    has_sources_slide = False

    for slide in deck["slides"]:
        family = str(slide["layout"]["family"])
        definition = registry.get(family)
        if not definition:
            fallback = pack.manifest["fallback_layout"]
            definition = registry.get(fallback)
            if not definition:
                raise DeckConversionError(f"レイアウトとフォールバックがありません: {family}")
        legacy_layout = str(definition["legacy_layout"])
        role = str(slide.get("role", "content"))
        title = str(slide.get("title", "")).strip()
        visual_role, visual_reason = _visual_role(slide, legacy_layout)
        converted: dict[str, Any] = {
            "layout": legacy_layout,
            "title": title,
        }
        repeat_reason = str(slide.get("visual", {}).get("repeat_reason", "")).strip()
        if repeat_reason:
            converted["layout_repeat_reason"] = repeat_reason
        if legacy_layout not in {"cover", "sources_appendix"}:
            converted.update(
                {
                    "job": _job(legacy_layout, role),
                    "visual_role": visual_role,
                    "source": _source_marker(slide, source_ids),
                    "source_requirement": "standard" if slide.get("source_refs") else "none",
                }
            )
            if visual_reason:
                converted["visual_reason"] = visual_reason

        paragraphs = _blocks(slide, "paragraph")
        callouts = _blocks(slide, "callout") + _blocks(slide, "quote")
        bullets = _bullet_items(slide)
        lead = str(slide.get("takeaway") or "").strip()

        if legacy_layout == "cover":
            author_line = " / ".join(filter(None, [metadata.get("author"), metadata.get("organization")]))
            subtitle_parts = [slide.get("subtitle") or metadata.get("subtitle"), author_line]
            converted.update(
                {
                    "title": title or metadata["title"],
                    "subtitle": "\n".join(str(item) for item in subtitle_parts if item),
                    "date": metadata["date"],
                    "eyebrow": slide.get("visual", {}).get("eyebrow", ""),
                }
            )
        elif legacy_layout == "agenda":
            sections = _process_steps(slide)
            if not sections:
                sections = [{"title": item, "body": ""} for item in bullets]
            converted.update({"lead": lead, "sections": sections})
        elif legacy_layout == "section_divider":
            converted.update(
                {
                    "section": slide.get("visual", {}).get("section") or slide.get("subtitle") or "SECTION",
                    "body": _first_text(paragraphs, "text", "body") or lead,
                }
            )
        elif legacy_layout == "single_message":
            metrics = _blocks(slide, "metric")
            headline = _first_text(metrics, "value") or lead or _first_text(callouts, "heading", "body", "text")
            body = _first_text(paragraphs, "text", "body") or _first_text(callouts, "body", "text")
            converted.update({"headline": headline, "body": body})
        elif legacy_layout in {"text_focus", "text_visual"}:
            converted.update(
                {
                    "lead": lead,
                    "body": _first_text(paragraphs, "text", "body"),
                    "bullets": bullets,
                    "callout": _first_text(callouts, "body", "text", "heading"),
                }
            )
            images = _blocks(slide, "image")
            if legacy_layout == "text_visual":
                if not images:
                    raise DeckConversionError(f"画像レイアウトにimageブロックがありません: {slide['id']}")
                image = images[0]
                image_path = image.get("path") or image.get("asset_ref")
                if image_path and asset_base and not Path(str(image_path)).is_absolute():
                    image_path = str((asset_base / str(image_path)).resolve())
                converted.update(
                    {
                        "image": image_path,
                        "image_alt": image.get("alt") or "",
                        "image_position": image.get("position") or "right",
                    }
                )
        elif legacy_layout == "comparison":
            converted.update({"lead": lead, "columns": _comparison_columns(slide)})
        elif legacy_layout == "process":
            converted.update({"lead": lead, "steps": _process_steps(slide)})
        elif legacy_layout == "data_focus":
            stats = [
                {"value": block.get("value"), "label": block.get("label"), "note": block.get("note", "")}
                for block in _blocks(slide, "metric")
            ]
            converted.update({"lead": lead, "stats": stats, "bullets": bullets})
        elif legacy_layout == "bar_chart":
            charts = _blocks(slide, "chart")
            chart = charts[0] if charts else {}
            bars = chart.get("items") or chart.get("bars") or []
            maximum = chart.get("max_value") or max((float(item.get("value", 0)) for item in bars), default=0)
            converted.update({"lead": lead, "bars": bars, "max_value": maximum, "note": chart.get("note", "")})
        elif legacy_layout == "table":
            tables = _blocks(slide, "table")
            table = tables[0] if tables else {}
            converted.update({"lead": lead, "headers": table.get("headers", []), "rows": table.get("rows", []), "note": table.get("note", "")})
        elif legacy_layout == "decision_flow":
            decision = callouts[0] if callouts else {}
            converted.update(
                {
                    "lead": lead,
                    "question": decision.get("question", ""),
                    "yes_label": decision.get("yes_label", "はい"),
                    "yes_action": decision.get("yes_action", ""),
                    "no_label": decision.get("no_label", "いいえ"),
                    "no_action": decision.get("no_action", ""),
                    "footer": decision.get("footer", ""),
                }
            )
        elif legacy_layout == "summary_action":
            converted.update({"headline": lead or title, "actions": bullets, "note": _first_text(paragraphs, "text", "body")})
        elif legacy_layout == "exercise":
            converted.update(
                {
                    "lead": lead,
                    "prompt": _first_text(paragraphs, "text", "body"),
                    "checks": bullets,
                    "check_title": slide.get("subtitle") or "確認",
                }
            )
        elif legacy_layout == "sources_appendix":
            converted["sources"] = _legacy_sources(deck, slide.get("source_refs", []))
            has_sources_slide = True
        legacy_slides.append(converted)

    if deck.get("sources") and not has_sources_slide:
        legacy_slides.append({"layout": "sources_appendix", "title": "出典", "sources": _legacy_sources(deck)})

    mode = "presented" if context.get("mode") == "presented" else "standalone"
    result: dict[str, Any] = {
        "deck_title": metadata["title"],
        "audience": context["audience"],
        "purpose": context["purpose"],
        "mode": mode,
        "high_stakes": bool(context.get("high_stakes", False)),
        "slides": legacy_slides,
    }
    if result["high_stakes"]:
        safety = context.get("safety")
        if not isinstance(safety, dict):
            raise DeckConversionError("high_stakes資料にはcontext.safetyが必要です")
        result["safety"] = safety
        claim_evidence = context.get("claim_evidence")
        if isinstance(claim_evidence, list):
            result["claim_evidence"] = claim_evidence
    if context.get("dated_roadmap") is True:
        result["dated_roadmap"] = True
        timeline = context.get("timeline")
        if isinstance(timeline, dict):
            result["timeline"] = timeline
    return result
