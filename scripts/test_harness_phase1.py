#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slide_system.attempts import create_attempt, finish_step, start_step  # noqa: E402
from slide_system.briefs import approve_brief  # noqa: E402
from slide_system.cache import CacheStore, cache_key  # noqa: E402
from slide_system.locking import RunLock, RunLockedError  # noqa: E402
from slide_system.runs import create_run, find_run  # noqa: E402
from slide_system.state import CompletedRunError, InvalidTransitionError, mutate_run, transition_run  # noqa: E402
from slide_system.validation import DocumentValidationError, validate_document  # noqa: E402


def config() -> dict:
    return {
        "defaults": {
            "language": "ja",
            "mode": "interactive",
            "design_pack": "warm_clean",
            "output_profile": "html_pdf",
            "aspect_ratio": "16:9",
        },
        "runs": {"directory": "runs", "generate_index": True},
        "qa": {"require_human_approval": True},
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        project_root = Path(temporary)
        shutil.copytree(ROOT / "schemas", project_root / "schemas")
        run = create_run(
            project_root,
            config(),
            title="Phase 1検証資料",
            summary="状態遷移と再開情報の検証",
            adapter="codex",
        )
        run_id = run["run_id"]
        run_dir = project_root / "runs" / run_id
        assert (run_dir / "run.lock.json").is_file()
        lock_data = json.loads((run_dir / "run.lock.json").read_text(encoding="utf-8"))
        assert lock_data["checksums"]["configuration"].startswith("sha256:")
        cache = CacheStore(project_root, {**config(), "cache": {"directory": ".cache"}})
        key = cache_key("html", {"deck": "sha256:test", "design": "warm_clean@1.0.0"})
        cached_path = cache.put_text("html", key, "html", "<!doctype html>", metadata={"test": True})
        assert cache.get("html", key, "html") == cached_path

        with RunLock(run_dir, owner="first"):
            try:
                RunLock(run_dir, owner="second").acquire()
            except RunLockedError as exc:
                assert exc.details["owner"] == "first"
            else:
                raise AssertionError("Concurrent Run lock was not rejected")
        assert not (run_dir / ".state/run.lock").exists()

        try:
            transition_run(
                project_root,
                config(),
                run_id,
                new_status="qa",
                owner="test",
                last_action="不正な遷移",
                next_action="停止",
            )
        except InvalidTransitionError:
            pass
        else:
            raise AssertionError("Invalid state transition was accepted")

        transition_run(
            project_root,
            config(),
            run_id,
            new_status="confirmation_pending",
            owner="test",
            last_action="制作条件を提示しました",
            next_action="内容を確認してください",
            phase="confirmation",
            last_step="brief_presented",
        )
        assert list((run_dir / ".state/backups").glob("run.*.json"))

        approved_at = datetime.now().astimezone().isoformat(timespec="seconds")
        brief_path = project_root / "approved-brief.json"
        brief_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "run_id": run_id,
                    "status": "approved",
                    "purpose": "Phase 1を検証する",
                    "audience": "開発者",
                    "cover": {"title": "Phase 1検証資料", "date": "2026-08-10", "subtitle": None, "author": None, "organization": None},
                    "outline": ["状態遷移", "Attempt", "Step"],
                    "output": {"profile": "html_pdf"},
                    "approved_at": approved_at,
                    "approval_message": "この内容で制作する",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        approve_brief(project_root, config(), run_id, brief_source=brief_path, owner="test")
        approved_run = find_run(project_root, config(), run_id)
        assert approved_run["status"] == "approved"
        assert (run_dir / "brief/approved-brief.json").is_file()

        deck_path = project_root / "deck.json"
        deck_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "deck_id": "deck-phase1",
                    "run_id": run_id,
                    "attempt": 1,
                    "metadata": {"title": "Phase 1検証資料", "subtitle": None, "date": "2026-08-10", "author": None, "organization": None, "language": "ja"},
                    "context": {"purpose": "Phase 1を検証する", "audience": "開発者", "mode": "standalone", "core_message": "中断しても安全に再開できる"},
                    "narrative": {},
                    "slides": [
                        {
                            "id": "slide-01",
                            "role": "cover",
                            "title": "Phase 1検証資料",
                            "subtitle": None,
                            "takeaway": None,
                            "layout": {"family": "cover", "variant": "standard", "density": "low"},
                            "blocks": [],
                            "visual": {"strategy": "decorative_shapes"},
                            "source_refs": [],
                        }
                    ],
                    "sources": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        attempt = create_attempt(project_root, config(), run_id, owner="test", deck_source=deck_path, reason="初稿")
        assert attempt["attempt"] == 1
        assert attempt["input_hash"].startswith("sha256:")
        assert (run_dir / "attempts/001/deck.json").is_file()

        step = start_step(project_root, config(), run_id, name="validate_deck", owner="test")
        assert step["status"] == "running"
        completed = finish_step(
            project_root,
            config(),
            run_id,
            step_id=step["step_id"],
            owner="test",
            success=True,
            output_data={"result": "PASS"},
        )
        assert completed["status"] == "completed"
        assert completed["execution"]["duration_ms"] >= 0

        transition_run(project_root, config(), run_id, new_status="qa", owner="test", last_action="HTML生成完了", next_action="全ページを検査してください")
        transition_run(project_root, config(), run_id, new_status="ready_for_review", owner="test", last_action="自動QAがPASSしました", next_action="HTMLを確認してください")
        try:
            transition_run(project_root, config(), run_id, new_status="complete", owner="test", last_action="未承認", next_action="なし")
        except InvalidTransitionError:
            pass
        else:
            raise AssertionError("Run completed without QA, delivery, and human approval")

        (run_dir / "delivery/final.html").write_text("<!doctype html>", encoding="utf-8")
        (run_dir / "delivery/final.pdf").write_bytes(b"%PDF-test")

        def accept_artifacts(value: dict) -> dict:
            value["quality"].update({"qa_result": "PASS", "human_result": "accepted", "latest_review": "attempts/001/review.json"})
            value["delivery"].update({"accepted_attempt": 1, "html": "delivery/final.html", "pdf": "delivery/final.pdf"})
            return value

        mutate_run(project_root, config(), run_id, owner="test", event="test_artifacts_accepted", mutator=accept_artifacts)
        transition_run(project_root, config(), run_id, new_status="complete", owner="test", last_action="利用者が承認しました", next_action="完了")
        completed_run = find_run(project_root, config(), run_id)
        assert completed_run["timestamps"]["completed_at"]

        try:
            transition_run(project_root, config(), run_id, new_status="complete", owner="test", last_action="再変更", next_action="なし")
        except CompletedRunError:
            pass
        else:
            raise AssertionError("Completed Run was mutated")

        invalid = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        invalid["display"]["title"] = ""
        try:
            validate_document(project_root, "run", invalid)
        except DocumentValidationError:
            pass
        else:
            raise AssertionError("Invalid run document passed schema validation")

        events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        transition_event = next(item for item in events if item["event"] == "status_changed")
        assert transition_event["from"] == "created"
        assert transition_event["to"] == "confirmation_pending"
        assert any(item["event"] == "brief_approved" for item in events)
        assert any(item["event"] == "attempt_created" for item in events)
        assert any(item["event"] == "step_completed" for item in events)

    print("PASS: harness Phase 1 validation, transitions, locks, attempts, and steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
