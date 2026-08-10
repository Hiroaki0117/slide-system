from __future__ import annotations

from pathlib import Path
from typing import Any

from .runs import STATUS_LABELS, find_run
from .state import ALLOWED_TRANSITIONS, InvalidTransitionError, mutate_run
from .storage import atomic_write_json
from .validation import validate_file


def approve_brief(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    brief_source: Path,
    owner: str,
) -> dict[str, Any]:
    brief = validate_file(project_root, "approved-brief", brief_source.resolve())
    if brief.get("run_id") != run_id:
        raise ValueError(f"Briefのrun_idが一致しません: {brief.get('run_id')} != {run_id}")
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        current = run["status"]
        if current != "approved" and "approved" not in ALLOWED_TRANSITIONS.get(current, set()):
            raise InvalidTransitionError(f"この状態ではBriefを承認できません: {current}")
        run["status"] = "approved"
        run["input"]["approved_brief_path"] = "brief/approved-brief.json"
        run["progress"]["current_phase"] = "approved"
        run["progress"]["last_step"] = "brief_approved"
        run["guidance"] = {
            "status_label": STATUS_LABELS["approved"],
            "last_action": "制作条件と構成案が承認されました",
            "next_action": "最初のdeck.json候補を作成してください",
        }
        atomic_write_json(run_dir / "brief" / "approved-brief.json", brief)
        return run

    return mutate_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="brief_approved",
        mutator=apply,
        event_details={"brief": "brief/approved-brief.json"},
    )
