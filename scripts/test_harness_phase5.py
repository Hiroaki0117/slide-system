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
from slide_system.reviews import record_review  # noqa: E402
from slide_system.runs import create_run, find_run, regenerate_index  # noqa: E402
from slide_system.state import transition_run  # noqa: E402
from slide_system.storage import atomic_write_json  # noqa: E402


def config() -> dict:
    return {"defaults": {"language": "ja", "mode": "interactive", "design_pack": "warm_clean", "output_profile": "html_pdf", "aspect_ratio": "16:9"}, "runs": {"directory": "runs", "generate_index": True}, "qa": {"require_human_approval": True}, "cache": {"directory": ".cache"}}


def deck(run_id: str) -> dict:
    return {"schema_version": "1.0", "deck_id": f"{run_id}-deck", "run_id": run_id, "attempt": 1, "metadata": {"title": "研修資料", "subtitle": None, "date": "2026-08-10", "author": None, "organization": None, "language": "ja"}, "context": {"purpose": "研修", "audience": "新人", "mode": "training", "core_message": "基本を理解する"}, "slides": [{"id": "slide-01", "role": "cover", "title": "研修資料", "subtitle": None, "takeaway": None, "layout": {"family": "cover", "variant": None, "density": "low"}, "blocks": [], "visual": {}, "source_refs": []}], "sources": []}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="slide-system-phase5-") as temporary:
        root = Path(temporary)
        shutil.copytree(ROOT / "schemas", root / "schemas")
        run = create_run(root, config(), title="新人研修", summary="管理画面と採用確認", tags=["研修"], adapter="codex")
        run_id = run["run_id"]
        transition_run(root, config(), run_id, new_status="approved", owner="test", last_action="承認", next_action="制作")
        source = root / "deck.json"; atomic_write_json(source, deck(run_id)); create_attempt(root, config(), run_id, owner="test", deck_source=source, reason="初稿")
        transition_run(root, config(), run_id, new_status="qa", owner="test", last_action="生成", next_action="QA")
        transition_run(root, config(), run_id, new_status="ready_for_review", owner="test", last_action="QA PASS", next_action="確認")
        run_dir = Path(find_run(root, config(), run_id)["_run_dir"]); attempt_dir = run_dir / "attempts" / "001"
        (attempt_dir / "deck.html").write_text("<html>final</html>", encoding="utf-8"); (attempt_dir / "deck.pdf").write_bytes(b"%PDF-final")
        atomic_write_json(attempt_dir / "qa-report.json", {"schema_version": "1.0", "run_id": run_id, "attempt": 1, "result": "PASS", "summary": {"passed": 4, "failed": 0, "warnings": 0}, "issues": [], "checked_at": "2026-08-10T12:00:00+09:00"})
        def quality(value: dict) -> dict:
            value["quality"]["qa_result"] = "PASS"; value["quality"]["latest_qa"] = "attempts/001/qa-report.json"; return value
        from slide_system.state import mutate_run
        mutate_run(root, config(), run_id, owner="test", event="qa_test_ready", mutator=quality)
        review_path = root / "review.json"; atomic_write_json(review_path, {"schema_version": "1.0", "run_id": run_id, "attempt": 1, "reviewer": "user", "result": "accepted", "ratings": {}, "good_points": ["読みやすい"], "issues": [], "reviewed_at": "2026-08-10T12:10:00+09:00"})
        completed = record_review(root, config(), run_id, review_source=review_path, owner="test")
        assert completed["status"] == "complete"; assert (run_dir / "delivery" / "final.html").is_file(); assert (run_dir / "delivery" / "final.pdf").is_file()
        regenerate_index(root, config())
        detail = (run_dir / "index.html").read_text(encoding="utf-8")
        assert "制作案の履歴" in detail and "Attempt" in detail and "QAレポート" in detail
        index = json.loads((root / "runs" / "index.json").read_text(encoding="utf-8"))
        assert index["runs"][0]["detail"].endswith("/index.html")
    print("PASS: harness Phase 5 run detail comparison and human review delivery")


if __name__ == "__main__": main()
