#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.attempts import create_attempt  # noqa: E402
from slide_system.baselines import approve_baseline, compare_baseline  # noqa: E402
from slide_system.runs import create_run, find_run  # noqa: E402
from slide_system.state import mutate_run, transition_run  # noqa: E402
from slide_system.storage import atomic_write_json  # noqa: E402


def config() -> dict:
    return {"defaults": {"language": "ja", "mode": "interactive", "design_pack": "warm_clean", "output_profile": "html_pdf", "aspect_ratio": "16:9"}, "runs": {"directory": "runs", "generate_index": True}, "qa": {"require_human_approval": True}, "cache": {"directory": ".cache"}}


def deck(run_id: str) -> dict:
    return {"schema_version": "1.0", "deck_id": "generic-proposal", "run_id": run_id, "attempt": 1, "metadata": {"title": "問い合わせ改善", "subtitle": None, "date": "2026-08-10", "author": None, "organization": None, "language": "ja"}, "context": {"purpose": "改善案を相談する", "audience": "担当者", "mode": "standalone", "core_message": "小さく試す"}, "slides": [{"id": "slide-01", "role": "cover", "title": "問い合わせ改善", "subtitle": None, "takeaway": None, "layout": {"family": "cover", "variant": None, "density": "low"}, "blocks": [], "visual": {}, "source_refs": []}], "sources": []}


def main() -> None:
    case_root = ROOT / "test-cases" / "harness"
    for name in ("01_internal_training", "02_business_proposal", "03_standalone_explainer"):
        for file_name in ("REQUEST.md", "NOTES.md", "EXPECTED.md"):
            assert (case_root / name / file_name).is_file()
    with tempfile.TemporaryDirectory(prefix="slide-system-phase6-") as temporary:
        root = Path(temporary); shutil.copytree(ROOT / "schemas", root / "schemas")
        run = create_run(root, config(), title="問い合わせ改善", summary="匿名テスト", tags=["改善"], adapter="codex"); run_id = run["run_id"]
        transition_run(root, config(), run_id, new_status="approved", owner="test", last_action="承認", next_action="制作")
        source = root / "deck.json"; atomic_write_json(source, deck(run_id)); create_attempt(root, config(), run_id, owner="test", deck_source=source, reason="承認済み基準")
        run_dir = Path(find_run(root, config(), run_id)["_run_dir"]); attempt_dir = run_dir / "attempts" / "001"
        atomic_write_json(attempt_dir / "qa-report.json", {"schema_version": "1.0", "run_id": run_id, "attempt": 1, "result": "PASS", "summary": {"passed": 4, "failed": 0, "warnings": 0}, "issues": [], "checked_at": "2026-08-10T12:00:00+09:00"})
        atomic_write_json(attempt_dir / "review.json", {"schema_version": "1.0", "run_id": run_id, "attempt": 1, "reviewer": "tester", "result": "accepted", "ratings": {}, "good_points": [], "issues": [], "reviewed_at": "2026-08-10T12:10:00+09:00"})
        def complete(value: dict) -> dict:
            value["status"] = "complete"; value["quality"].update({"qa_result": "PASS", "human_result": "accepted"}); value["delivery"].update({"accepted_attempt": 1, "html": "delivery/final.html", "pdf": "delivery/final.pdf"}); value["design"]["version"] = "1.0.0"; return value
        mutate_run(root, config(), run_id, owner="test", event="test_completed", mutator=complete)
        baseline_path = approve_baseline(root, config(), run_id, case_id="business-proposal", approver="tester", note="匿名テスト")
        manifest = json.loads(baseline_path.read_text(encoding="utf-8")); assert manifest["approved_by"] == "tester"; assert set(manifest["hashes"]) == {"deck", "qa", "review"}
        matched = compare_baseline(root, config(), run_id, baseline_path=baseline_path); assert matched["result"] == "MATCH"
        changed_deck = json.loads((attempt_dir / "deck.json").read_text(encoding="utf-8")); changed_deck["metadata"]["title"] = "変更後"; atomic_write_json(attempt_dir / "deck.json", changed_deck)
        changed = compare_baseline(root, config(), run_id, baseline_path=baseline_path); assert changed["result"] == "CHANGED"; assert next(item for item in changed["comparisons"] if item["artifact"] == "deck")["result"] == "CHANGED"
    print("PASS: harness Phase 6 generic cases and approved baseline comparison")


if __name__ == "__main__": main()
