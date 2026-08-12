from __future__ import annotations

import json
from typing import Any


RESOLVED_RESEARCH_STATUSES = {"verified", "user_supplied", "not_applicable"}


class ContentContractError(ValueError):
    """Raised when a brief cannot pass the pre-production content gate."""


def require_content_contract(config: dict[str, Any]) -> bool:
    return bool(config.get("qa", {}).get("require_content_contract", False))


def validate_brief_content_contract(brief: dict[str, Any], config: dict[str, Any]) -> None:
    contract = brief.get("content_contract")
    if not isinstance(contract, dict):
        if require_content_contract(config):
            raise ContentContractError(
                "内容契約がありません。読者の判断、調査項目、重要論点、構成上の掲載先を確認してから承認してください"
            )
        return

    if contract.get("status") != "approved":
        raise ContentContractError("内容契約が利用者承認済みになっていません")

    research_topics = contract.get("research_topics", [])
    if contract.get("research_required"):
        if not research_topics:
            raise ContentContractError("調査が必要な資料にはresearch_topicsが必要です")
        unresolved = [
            str(item.get("id") or item.get("question") or "ID不明")
            for item in research_topics
            if item.get("status") not in RESOLVED_RESEARCH_STATUSES
        ]
        if unresolved:
            raise ContentContractError(f"未解決の調査項目があります: {', '.join(unresolved)}")

    if contract.get("kind") == "comparison":
        subjects = contract.get("comparison_subjects", [])
        axes = contract.get("comparison_axes", [])
        if len(subjects) < 2:
            raise ContentContractError("比較資料には2つ以上の比較対象が必要です")
        if len(axes) < 3:
            raise ContentContractError("比較資料には3つ以上の比較軸が必要です")


def _slide_text(slide: dict[str, Any]) -> str:
    return json.dumps(slide, ensure_ascii=False).casefold()


def evaluate_content_contract(brief: dict[str, Any], deck: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    contract = brief.get("content_contract")
    if not isinstance(contract, dict):
        if require_content_contract(config):
            issues.append(
                {
                    "level": "FAIL",
                    "code": "MISSING_CONTENT_CONTRACT",
                    "message": "承認済みBriefに内容契約がありません",
                }
            )
        return {"status": "FAIL" if issues else "PASS", "issues": issues, "checked_items": 0}

    slides = {str(slide.get("id")): slide for slide in deck.get("slides", [])}
    source_ids = {str(source.get("id")) for source in deck.get("sources", [])}
    used_source_ids = {
        str(source_id)
        for slide in deck.get("slides", [])
        for source_id in slide.get("source_refs", [])
    }
    mappings = {
        str(item.get("item_id")): [str(slide_id) for slide_id in item.get("slide_ids", [])]
        for item in deck.get("context", {}).get("content_coverage", [])
        if isinstance(item, dict)
    }

    for topic in contract.get("research_topics", []):
        if topic.get("status") not in {"verified", "user_supplied"}:
            continue
        for source_id in topic.get("source_ids", []):
            if source_id not in source_ids:
                issues.append(
                    {
                        "level": "FAIL",
                        "code": "RESEARCH_SOURCE_MISSING",
                        "message": f"調査項目{topic.get('id')}の出典{source_id}がdeck.jsonにありません",
                    }
                )
            elif source_id not in used_source_ids:
                issues.append(
                    {
                        "level": "FAIL",
                        "code": "RESEARCH_SOURCE_UNUSED",
                        "message": f"調査項目{topic.get('id')}の出典{source_id}がどのスライドでも参照されていません",
                    }
                )

    required_items = [
        item
        for item in [*contract.get("comparison_axes", []), *contract.get("coverage_items", [])]
        if item.get("requirement", "MUST") == "MUST"
    ]
    for item in required_items:
        item_id = str(item.get("id"))
        mapped_slide_ids = mappings.get(item_id, [])
        if not mapped_slide_ids:
            issues.append(
                {
                    "level": "FAIL",
                    "code": "CONTENT_ITEM_UNMAPPED",
                    "message": f"必須論点「{item.get('label')}」の掲載先がcontent_coverageにありません",
                }
            )
            continue
        missing_slides = [slide_id for slide_id in mapped_slide_ids if slide_id not in slides]
        if missing_slides:
            issues.append(
                {
                    "level": "FAIL",
                    "code": "CONTENT_SLIDE_MISSING",
                    "message": f"必須論点「{item.get('label')}」の掲載先が存在しません: {', '.join(missing_slides)}",
                }
            )
            continue
        combined_text = " ".join(_slide_text(slides[slide_id]) for slide_id in mapped_slide_ids)
        evidence_terms = [str(term).casefold() for term in item.get("evidence_terms", []) if str(term).strip()]
        if evidence_terms and not any(term in combined_text for term in evidence_terms):
            issues.append(
                {
                    "level": "FAIL",
                    "code": "CONTENT_EVIDENCE_MISSING",
                    "message": f"必須論点「{item.get('label')}」を示す語が掲載先にありません: {', '.join(item.get('evidence_terms', []))}",
                    "slide": ",".join(mapped_slide_ids),
                }
            )
        required_sources = {str(source_id) for source_id in item.get("source_ids", [])}
        mapped_sources = {
            str(source_id)
            for slide_id in mapped_slide_ids
            for source_id in slides[slide_id].get("source_refs", [])
        }
        missing_sources = sorted(required_sources - mapped_sources)
        if missing_sources:
            issues.append(
                {
                    "level": "FAIL",
                    "code": "CONTENT_SOURCE_MISSING",
                    "message": f"必須論点「{item.get('label')}」の掲載先に必要な出典がありません: {', '.join(missing_sources)}",
                    "slide": ",".join(mapped_slide_ids),
                }
            )

    return {
        "status": "FAIL" if any(item["level"] == "FAIL" for item in issues) else "PASS",
        "issues": issues,
        "checked_items": len(required_items),
    }
