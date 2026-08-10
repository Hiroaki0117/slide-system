from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .hashing import sha256_file
from .runs import find_run, now_iso
from .storage import atomic_write_json, read_json
from .validation import validate_document


BASELINE_FILES = {
    "deck": "deck.json",
    "qa": "qa-report.json",
    "review": "review.json",
    "contact_sheet": "renders/contact-sheet.png",
}


def _baseline_dir(project_root: Path, case_id: str, design_pack: str, design_version: str) -> Path:
    safe_version = design_version.replace(".", "_")
    return project_root / "baselines" / case_id / f"{design_pack}-{safe_version}"


def approve_baseline(
    project_root: Path,
    config: dict[str, Any],
    selector: str,
    *,
    case_id: str,
    approver: str,
    note: str = "",
) -> Path:
    run = find_run(project_root, config, selector)
    if run["status"] != "complete" or run.get("quality", {}).get("human_result") != "accepted":
        raise ValueError("利用者が採用し、完了したRunだけをベースラインにできます")
    attempt_number = int(run["delivery"]["accepted_attempt"])
    run_dir = Path(run["_run_dir"])
    attempt_dir = run_dir / "attempts" / f"{attempt_number:03d}"
    design_pack = str(run["design"]["pack"])
    design_version = str(run["design"].get("version") or "unknown")
    target = _baseline_dir(project_root, case_id, design_pack, design_version)
    if target.exists():
        raise FileExistsError(f"同じベースラインが既にあります: {target}")
    target.mkdir(parents=True)
    artifacts: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for key, relative in BASELINE_FILES.items():
        source = attempt_dir / relative
        if not source.is_file():
            if key in {"deck", "qa", "review"}:
                raise FileNotFoundError(f"ベースライン必須成果物がありません: {source}")
            continue
        destination = target / Path(relative).name
        shutil.copy2(source, destination)
        artifacts[key] = destination.name
        hashes[key] = sha256_file(destination)
    manifest = {
        "schema_version": "1.0",
        "case_id": case_id,
        "design_pack": design_pack,
        "design_version": design_version,
        "source_run_id": run["run_id"],
        "source_attempt": attempt_number,
        "approved_by": approver,
        "approved_at": now_iso(),
        "note": note,
        "artifacts": artifacts,
        "hashes": hashes,
    }
    validate_document(project_root, "baseline", manifest)
    atomic_write_json(target / "baseline.json", manifest)
    return target / "baseline.json"


def compare_baseline(project_root: Path, config: dict[str, Any], selector: str, *, baseline_path: Path) -> dict[str, Any]:
    run = find_run(project_root, config, selector)
    baseline = read_json(baseline_path.resolve())
    validate_document(project_root, "baseline", baseline)
    attempt_number = int(run.get("progress", {}).get("current_attempt", 0))
    attempt_dir = Path(run["_run_dir"]) / "attempts" / f"{attempt_number:03d}"
    comparisons = []
    for key, expected_hash in baseline["hashes"].items():
        relative = BASELINE_FILES[key]
        current = attempt_dir / relative
        current_hash = sha256_file(current) if current.is_file() else None
        comparisons.append({"artifact": key, "result": "MATCH" if current_hash == expected_hash else "CHANGED", "baseline_hash": expected_hash, "current_hash": current_hash})
    result = {
        "schema_version": "1.0",
        "run_id": run["run_id"],
        "attempt": attempt_number,
        "baseline": str(baseline_path.resolve()),
        "result": "MATCH" if all(item["result"] == "MATCH" for item in comparisons) else "CHANGED",
        "comparisons": comparisons,
        "compared_at": now_iso(),
    }
    atomic_write_json(attempt_dir / "baseline-comparison.json", result)
    return result
