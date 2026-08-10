from __future__ import annotations

import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .locking import RunLock
from .runs import STATUS_LABELS, find_run, now_iso, regenerate_index
from .storage import append_jsonl, atomic_write_json, read_json
from .validation import validate_document


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "created": {"questions_pending", "confirmation_pending", "approved", "blocked", "failed", "cancelled"},
    "questions_pending": {"confirmation_pending", "blocked", "cancelled"},
    "confirmation_pending": {"questions_pending", "approved", "blocked", "cancelled"},
    "approved": {"generating", "blocked", "failed", "cancelled"},
    "generating": {"qa", "needs_revision", "blocked", "failed", "cancelled"},
    "qa": {"needs_revision", "ready_for_review", "blocked", "failed", "cancelled"},
    "needs_revision": {"generating", "blocked", "failed", "cancelled"},
    "ready_for_review": {"needs_revision", "complete", "blocked", "cancelled"},
    "complete": set(),
    "blocked": {"questions_pending", "confirmation_pending", "approved", "generating", "needs_revision", "cancelled"},
    "failed": {"generating", "cancelled"},
    "cancelled": set(),
}


class InvalidTransitionError(ValueError):
    pass


class CompletedRunError(ValueError):
    pass


def _backup_name() -> str:
    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%f")
    return f"run.{stamp}.json"


def mutate_run(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    owner: str,
    event: str,
    mutator: Callable[[dict[str, Any]], dict[str, Any]],
    event_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])
    with RunLock(run_dir, owner=owner):
        current = read_json(run_dir / "run.json")
        if current.get("status") == "complete":
            raise CompletedRunError("完了済みRunは変更できません。子Runを作成してください。")
        updated = mutator(copy.deepcopy(current))
        updated["timestamps"]["updated_at"] = now_iso()
        validate_document(project_root, "run", updated)
        backup_path = run_dir / ".state" / "backups" / _backup_name()
        atomic_write_json(backup_path, current)
        atomic_write_json(run_dir / "run.json", updated)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "event": event,
                "at": updated["timestamps"]["updated_at"],
                "run_id": run_id,
                "owner": owner,
                **(event_details or {}),
            },
        )
    regenerate_index(project_root, config)
    updated["_run_dir"] = str(run_dir)
    return updated


def transition_run(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    new_status: str,
    owner: str,
    last_action: str,
    next_action: str,
    phase: str | None = None,
    last_step: str | None = None,
) -> dict[str, Any]:
    if new_status not in ALLOWED_TRANSITIONS:
        raise InvalidTransitionError(f"未定義の状態です: {new_status}")

    transition_details: dict[str, Any] = {"from": None, "to": new_status}

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        previous_status = run["status"]
        transition_details["from"] = previous_status
        if new_status != previous_status and new_status not in ALLOWED_TRANSITIONS.get(previous_status, set()):
            raise InvalidTransitionError(f"状態を変更できません: {previous_status} -> {new_status}")
        run["status"] = new_status
        run["guidance"] = {
            "status_label": STATUS_LABELS[new_status],
            "last_action": last_action,
            "next_action": next_action,
        }
        if phase is not None:
            run["progress"]["current_phase"] = phase
        if last_step is not None:
            run["progress"]["last_step"] = last_step
        if new_status == "complete":
            quality = run.get("quality", {})
            delivery = run.get("delivery", {})
            if quality.get("qa_result") != "PASS":
                raise InvalidTransitionError("自動QAがPASSするまでRunを完了できません")
            if quality.get("human_result") != "accepted":
                raise InvalidTransitionError("利用者が成果物を承認するまでRunを完了できません")
            if not delivery.get("accepted_attempt") or not delivery.get("html"):
                raise InvalidTransitionError("採用Attemptと最終HTMLが記録されるまでRunを完了できません")
            if run.get("output", {}).get("profile") == "html_pdf" and not delivery.get("pdf"):
                raise InvalidTransitionError("最終PDFが記録されるまでRunを完了できません")
            run["timestamps"]["completed_at"] = now_iso()
        return run

    return mutate_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="status_changed",
        mutator=apply,
        event_details=transition_details,
    )
