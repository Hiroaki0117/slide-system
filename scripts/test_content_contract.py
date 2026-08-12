#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.briefs import approve_brief  # noqa: E402
from slide_system.content_contract import ContentContractError, evaluate_content_contract  # noqa: E402
from slide_system.runs import create_run  # noqa: E402
from slide_system.state import transition_run  # noqa: E402


def config() -> dict:
    return {
        "defaults": {"design_pack": "warm_clean"},
        "runs": {"directory": "runs", "generate_index": False},
        "qa": {"require_content_contract": True, "require_human_approval": True},
    }


def item(item_id: str, label: str, term: str, source_id: str = "S1") -> dict:
    return {
        "id": item_id,
        "label": label,
        "requirement": "MUST",
        "planned_section": label,
        "evidence_terms": [term],
        "source_ids": [source_id],
    }


def approved_brief(run_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "status": "approved",
        "purpose": "モバイル利用者が有料化を判断する",
        "audience": "PCを持たないAI初心者",
        "cover": {"title": "AIプラン比較", "date": "2026-08-12", "subtitle": None, "author": None, "organization": None},
        "outline": ["無料版", "有料版", "選び方"],
        "content_contract": {
            "status": "approved",
            "kind": "comparison",
            "decision_or_learning_outcome": "無料版と有料版を自分の用途で選べる",
            "research_required": True,
            "research_topics": [
                {"id": "R1", "question": "完成物を作る作業モードは何か", "status": "verified", "source_ids": ["S1"]}
            ],
            "comparison_subjects": ["Free", "Plus"],
            "comparison_axes": [
                item("axis-model", "モデルの違い", "高度な推論"),
                item("axis-work", "作業モード", "Work"),
                item("axis-research", "調査機能", "Deep Research"),
            ],
            "coverage_items": [item("feature-deliverable", "完成物の制作", "プレゼン")],
        },
        "output": {"profile": "html_pdf"},
        "approved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "approval_message": "この内容契約と構成で制作する",
    }


def deck(run_id: str) -> dict:
    slide = {
        "id": "slide-02",
        "role": "content",
        "title": "Plusで制作の幅が広がる",
        "takeaway": "高度な推論、Work、Deep Researchを使い、プレゼンまで作る",
        "layout": {"family": "text", "density": "medium"},
        "blocks": [{"id": "b1", "type": "paragraph", "text": "Workで調査からプレゼン作成まで進める", "source_refs": ["S1"]}],
        "visual": {"strategy": "explain"},
        "source_refs": ["S1"],
    }
    return {
        "schema_version": "1.0",
        "deck_id": "comparison",
        "run_id": run_id,
        "attempt": 1,
        "metadata": {"title": "AIプラン比較", "date": "2026-08-12", "language": "ja", "subtitle": None, "author": None, "organization": None},
        "context": {
            "purpose": "有料化を判断する",
            "audience": "AI初心者",
            "mode": "standalone",
            "core_message": "用途で選ぶ",
            "content_coverage": [
                {"item_id": "axis-model", "slide_ids": ["slide-02"]},
                {"item_id": "axis-work", "slide_ids": ["slide-02"]},
                {"item_id": "axis-research", "slide_ids": ["slide-02"]},
                {"item_id": "feature-deliverable", "slide_ids": ["slide-02"]},
            ],
        },
        "slides": [slide],
        "sources": [{"id": "S1", "title": "Official product documentation", "publisher": "Vendor", "url": "https://example.com", "accessed_at": "2026-08-12"}],
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="slide-system-content-contract-") as temporary:
        root = Path(temporary)
        shutil.copytree(ROOT / "schemas", root / "schemas")
        run = create_run(root, config(), title="AIプラン比較", summary="内容QA", adapter="codex")
        run_id = run["run_id"]
        transition_run(root, config(), run_id, new_status="confirmation_pending", owner="test", last_action="構成提示", next_action="承認")

        missing = approved_brief(run_id)
        missing.pop("content_contract")
        missing_path = root / "missing.json"
        missing_path.write_text(json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            approve_brief(root, config(), run_id, brief_source=missing_path, owner="test")
        except ContentContractError:
            pass
        else:
            raise AssertionError("内容契約のないBriefが承認された")

        unresolved = approved_brief(run_id)
        unresolved["content_contract"]["research_topics"][0]["status"] = "unresolved"
        unresolved_path = root / "unresolved.json"
        unresolved_path.write_text(json.dumps(unresolved, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            approve_brief(root, config(), run_id, brief_source=unresolved_path, owner="test")
        except ContentContractError:
            pass
        else:
            raise AssertionError("未解決調査を含むBriefが承認された")

        brief = approved_brief(run_id)
        brief_path = root / "approved.json"
        brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        approve_brief(root, config(), run_id, brief_source=brief_path, owner="test")

        good = deck(run_id)
        assert evaluate_content_contract(brief, good, config())["status"] == "PASS"

        no_work = copy.deepcopy(good)
        no_work["slides"][0]["title"] = "Plusで制作量が広がる"
        no_work["slides"][0]["takeaway"] = "高度な推論とDeep Researchでプレゼンを作る"
        no_work["slides"][0]["blocks"][0]["text"] = "調査からプレゼン作成まで進める"
        report = evaluate_content_contract(brief, no_work, config())
        assert "CONTENT_EVIDENCE_MISSING" in {issue["code"] for issue in report["issues"]}

        unmapped = copy.deepcopy(good)
        unmapped["context"]["content_coverage"] = [
            item for item in unmapped["context"]["content_coverage"] if item["item_id"] != "axis-work"
        ]
        report = evaluate_content_contract(brief, unmapped, config())
        assert "CONTENT_ITEM_UNMAPPED" in {issue["code"] for issue in report["issues"]}

        unused_source = copy.deepcopy(good)
        unused_source["slides"][0]["source_refs"] = []
        unused_source["slides"][0]["blocks"][0]["source_refs"] = []
        report = evaluate_content_contract(brief, unused_source, config())
        codes = {issue["code"] for issue in report["issues"]}
        assert {"RESEARCH_SOURCE_UNUSED", "CONTENT_SOURCE_MISSING"}.issubset(codes)

    print("PASS: content contract approval and deck coverage gates")


if __name__ == "__main__":
    main()
