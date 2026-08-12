from __future__ import annotations

from datetime import datetime
import tempfile
from pathlib import Path
from typing import Any

from .hashing import sha256_file
from .runs import STATUS_LABELS, find_run, now_iso
from .state import mutate_run
from .storage import atomic_write_json, read_json
from .validation import validate_document, validate_file


ATTEMPT_ALLOWED_STATES = {"approved", "generating", "qa", "needs_revision", "ready_for_review"}


def create_attempt(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    owner: str,
    deck_source: Path | None = None,
    reason: str = "",
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])
    details: dict[str, Any] = {"attempt": None, "reason": reason}
    result: dict[str, Any] = {}

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        if run["status"] not in ATTEMPT_ALLOWED_STATES:
            raise ValueError(f"この状態ではAttemptを作成できません: {run['status']}")
        number = int(run["progress"].get("attempt_count", 0)) + 1
        attempt_dir = run_dir / "attempts" / f"{number:03d}"
        if attempt_dir.exists():
            existing_items = list(attempt_dir.iterdir())
            if existing_items and not (
                len(existing_items) == 1
                and existing_items[0].name == "steps"
                and existing_items[0].is_dir()
                and not any(existing_items[0].iterdir())
            ):
                raise FileExistsError(f"Attemptフォルダが既にあります: {attempt_dir}")
        attempt_dir.mkdir(parents=True, exist_ok=True)
        (attempt_dir / "steps").mkdir(exist_ok=True)

        input_hash = None
        artifacts: dict[str, Any] = {}
        if deck_source:
            deck = validate_file(project_root, "deck", deck_source.resolve())
            if deck.get("run_id") != run_id:
                raise ValueError(f"deck.jsonのrun_idが一致しません: {deck.get('run_id')} != {run_id}")
            if deck.get("attempt") != number:
                raise ValueError(f"deck.jsonのattemptは{number}である必要があります: {deck.get('attempt')}")
            atomic_write_json(attempt_dir / "deck.json", deck)
            input_hash = sha256_file(attempt_dir / "deck.json")
            artifacts["deck"] = "deck.json"

        timestamp = now_iso()
        attempt = {
            "schema_version": "1.0",
            "run_id": run_id,
            "attempt": number,
            "status": "created",
            "created_at": timestamp,
            "updated_at": timestamp,
            "input_hash": input_hash,
            "artifacts": artifacts,
            "reason": reason,
        }
        validate_document(project_root, "attempt", attempt)
        atomic_write_json(attempt_dir / "attempt.json", attempt)
        run["status"] = "generating"
        run["progress"]["current_attempt"] = number
        run["progress"]["attempt_count"] = number
        run["progress"]["current_phase"] = "generating"
        run["progress"]["last_step"] = "attempt_created"
        run["guidance"] = {
            "status_label": STATUS_LABELS["generating"],
            "last_action": f"Attempt {number:03d}を作成しました",
            "next_action": "deck.jsonを検証し、HTML生成へ進んでください",
        }
        details["attempt"] = number
        result.update(attempt)
        return run

    mutate_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="attempt_created",
        mutator=apply,
        event_details=details,
    )
    return result


def create_revision_attempt(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    owner: str,
    deck_source: Path | None = None,
    reason: str,
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    if selected["status"] != "needs_revision":
        raise ValueError(f"修正Attemptを作成できる状態ではありません: {selected['status']}")
    run_dir = Path(selected["_run_dir"])
    current_number = int(selected["progress"].get("current_attempt", 0))
    source = deck_source.resolve() if deck_source else run_dir / "attempts" / f"{current_number:03d}" / "deck.json"
    if not source.is_file():
        raise FileNotFoundError(f"修正元deck.jsonがありません: {source}")
    deck = read_json(source)
    deck["run_id"] = run_id
    deck["attempt"] = current_number + 1
    validate_document(project_root, "deck", deck)
    with tempfile.TemporaryDirectory(prefix="slide-system-revision-") as temporary:
        normalized = Path(temporary) / "deck.json"
        atomic_write_json(normalized, deck)
        return create_attempt(
            project_root,
            config,
            run_id,
            owner=owner,
            deck_source=normalized,
            reason=reason or f"Attempt {current_number:03d}のQA修正",
        )


def start_step(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    name: str,
    owner: str,
    input_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])
    details: dict[str, Any] = {"attempt": None, "step_id": None, "name": name}
    result: dict[str, Any] = {}

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        number = int(run["progress"].get("current_attempt", 0))
        if number < 1:
            raise ValueError("先にAttemptを作成してください")
        steps_dir = run_dir / "attempts" / f"{number:03d}" / "steps"
        existing = sorted(steps_dir.glob("[0-9][0-9][0-9]-*.json"))
        sequence = len(existing) + 1
        step_id = f"step-{sequence:03d}"
        safe_name = "".join(character if character.isalnum() or character in "-_" else "-" for character in name).strip("-") or "step"
        path = steps_dir / f"{sequence:03d}-{safe_name}.json"
        if path.exists():
            raise FileExistsError(f"Stepが既にあります: {path}")
        step = {
            "schema_version": "1.0",
            "step_id": step_id,
            "name": name,
            "status": "running",
            "input": input_data or {},
            "output": {},
            "execution": {
                "started_at": now_iso(),
                "completed_at": None,
                "duration_ms": None,
                "retry_count": 0,
            },
            "error": None,
        }
        validate_document(project_root, "step", step)
        atomic_write_json(path, step)
        run["progress"]["last_step"] = name
        details.update({"attempt": number, "step_id": step_id, "path": str(path.relative_to(run_dir)).replace("\\", "/")})
        result.update(step)
        result["_path"] = str(path)
        return run

    mutate_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="step_started",
        mutator=apply,
        event_details=details,
    )
    return result


def finish_step(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    step_id: str,
    owner: str,
    success: bool,
    output_data: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])
    details: dict[str, Any] = {"step_id": step_id, "success": success}
    result: dict[str, Any] = {}

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        number = int(run["progress"].get("current_attempt", 0))
        steps_dir = run_dir / "attempts" / f"{number:03d}" / "steps"
        matches = [path for path in steps_dir.glob("*.json") if read_json(path).get("step_id") == step_id]
        if len(matches) != 1:
            raise FileNotFoundError(f"Stepを一意に特定できません: {step_id}")
        path = matches[0]
        step = read_json(path)
        if step["status"] != "running":
            raise ValueError(f"実行中ではないStepです: {step_id} ({step['status']})")
        completed_at = now_iso()
        started = datetime.fromisoformat(step["execution"]["started_at"])
        completed = datetime.fromisoformat(completed_at)
        step["status"] = "completed" if success else "failed"
        step["output"] = output_data or {}
        step["error"] = None if success else (error or {"message": "詳細なし"})
        step["execution"]["completed_at"] = completed_at
        step["execution"]["duration_ms"] = max(0, round((completed - started).total_seconds() * 1000))
        validate_document(project_root, "step", step)
        atomic_write_json(path, step)
        result.update(step)
        result["_path"] = str(path)
        return run

    mutate_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="step_completed" if success else "step_failed",
        mutator=apply,
        event_details=details,
    )
    return result
