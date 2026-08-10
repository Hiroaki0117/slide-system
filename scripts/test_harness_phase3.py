#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.attempts import create_attempt, create_revision_attempt  # noqa: E402
from slide_system.designs import load_design_pack  # noqa: E402
from slide_system.qa import create_qa_report  # noqa: E402
from slide_system.runs import create_run, find_run  # noqa: E402
from slide_system.state import transition_run  # noqa: E402
from slide_system.storage import atomic_write_json  # noqa: E402


def config() -> dict:
    return {
        "defaults": {"language": "ja", "mode": "interactive", "design_pack": "warm_clean", "output_profile": "html_pdf", "aspect_ratio": "16:9"},
        "runs": {"directory": "runs", "generate_index": True},
        "qa": {"require_human_approval": True},
        "cache": {"directory": ".cache"},
    }


def deck(run_id: str, attempt: int) -> dict:
    return {
        "schema_version": "1.0",
        "deck_id": f"{run_id}-deck",
        "run_id": run_id,
        "attempt": attempt,
        "metadata": {"title": "問い合わせ改善", "subtitle": None, "date": "2026-08-10", "author": None, "organization": None, "language": "ja"},
        "context": {"purpose": "改善案を共有する", "audience": "担当者", "mode": "standalone", "core_message": "小さく試す"},
        "slides": [{"id": "slide-01", "role": "cover", "title": "問い合わせ改善", "subtitle": None, "takeaway": None, "layout": {"family": "cover", "variant": None, "density": "low"}, "blocks": [], "visual": {"strategy": "decorative_shapes"}, "source_refs": []}],
        "sources": [],
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="slide-system-phase3-") as temporary:
        project_root = Path(temporary)
        shutil.copytree(ROOT / "schemas", project_root / "schemas")
        shutil.copytree(ROOT / "designs", project_root / "designs")
        shutil.copytree(ROOT / "skills" / "slide-system", project_root / "skills" / "slide-system")
        run = create_run(project_root, config(), title="問い合わせ改善", summary="QA統合テスト", tags=["改善"], adapter="codex")
        run_id = run["run_id"]
        transition_run(project_root, config(), run_id, new_status="approved", owner="test", last_action="承認", next_action="生成")
        source = project_root / "deck.json"
        atomic_write_json(source, deck(run_id, 1))
        create_attempt(project_root, config(), run_id, owner="test", deck_source=source, reason="初稿")
        attempt_dir = Path(find_run(project_root, config(), run_id)["_run_dir"]) / "attempts" / "001"
        atomic_write_json(attempt_dir / "static-qa-legacy.json", {"status": "PASS", "issues": [{"level": "WARN", "code": "LONG_TITLE", "message": "確認してください", "slide": 1}]})
        atomic_write_json(attempt_dir / "visual-qa-legacy.json", {"status": "FAIL", "slide_count": 1, "detected_pdf_pages": 1, "failures": [{"code": "OVERFLOW", "slide": 1, "details": ["p.body"]}]})
        (attempt_dir / "deck.html").write_text("<style>:root{--bg:#FFF8F4}</style>", encoding="utf-8")
        report = create_qa_report(project_root, run_id=run_id, attempt=1, attempt_dir=attempt_dir, design_pack=load_design_pack(project_root, "warm_clean"))
        assert report["result"] == "FAIL", report
        assert report["summary"]["failed"] == 1
        assert report["summary"]["warnings"] == 1
        assert report["gates"]["pdf_parity"] == "PASS"
        transition_run(project_root, config(), run_id, new_status="needs_revision", owner="test", last_action="QA FAIL", next_action="修正")
        revised = create_revision_attempt(project_root, config(), run_id, owner="test", reason="文字あふれ修正")
        assert revised["attempt"] == 2
        revised_deck = json.loads((attempt_dir.parent / "002" / "deck.json").read_text(encoding="utf-8"))
        assert revised_deck["attempt"] == 2
        assert attempt_dir.joinpath("qa-report.json").is_file()
        assert find_run(project_root, config(), run_id)["progress"]["attempt_count"] == 2
    print("PASS: harness Phase 3 unified QA and revision attempt loop")


if __name__ == "__main__":
    main()
