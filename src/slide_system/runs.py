from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from . import __version__
from .dashboard import write_dashboard
from .hashing import sha256_file, sha256_files, sha256_json
from .storage import append_jsonl, atomic_write_json, atomic_write_text, read_json
from .validation import validate_document


STATUS_LABELS = {
    "created": "準備中",
    "questions_pending": "質問への回答待ち",
    "confirmation_pending": "制作内容の確認待ち",
    "approved": "制作開始待ち",
    "generating": "制作中",
    "qa": "品質検査中",
    "needs_revision": "修正が必要",
    "ready_for_review": "HTML確認待ち",
    "complete": "完了",
    "blocked": "対応待ち",
    "failed": "エラー",
    "cancelled": "中止",
}


class RunNotFoundError(LookupError):
    pass


class AmbiguousRunError(LookupError):
    def __init__(self, selector: str, candidates: list[dict[str, Any]]) -> None:
        super().__init__(selector)
        self.selector = selector
        self.candidates = candidates


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def runs_root(project_root: Path, config: dict[str, Any]) -> Path:
    return project_root / config.get("runs", {}).get("directory", "runs")


def _allocate_run_directory(root: Path) -> tuple[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    date_key = datetime.now().astimezone().strftime("%Y%m%d")
    for sequence in range(1, 1000):
        run_id = f"run_{date_key}_{sequence:03d}"
        candidate = root / run_id
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return run_id, candidate
    raise RuntimeError(f"Run IDを確保できませんでした: {date_key}")


def create_run(
    project_root: Path,
    config: dict[str, Any],
    *,
    title: str,
    summary: str = "",
    tags: list[str] | None = None,
    adapter: str = "manual",
    request_source: Path | None = None,
) -> dict[str, Any]:
    root = runs_root(project_root, config)
    run_id, run_dir = _allocate_run_directory(root)
    for name in ("input/attachments", "brief", "attempts", "delivery", ".state/backups"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    request_path = run_dir / "input" / "request.md"
    if request_source:
        source = request_source.resolve()
        if not source.is_file():
            raise FileNotFoundError(f"依頼ファイルが見つかりません: {source}")
        shutil.copy2(source, request_path)
    else:
        atomic_write_text(request_path, "# 依頼\n\n（依頼内容はまだ登録されていません）\n")

    timestamp = now_iso()
    defaults = config.get("defaults", {})
    run = {
        "schema_version": "1.0",
        "run_id": run_id,
        "status": "created",
        "display": {
            "title": title.strip(),
            "summary": summary.strip(),
            "tags": [item.strip() for item in (tags or []) if item.strip()],
            "thumbnail": None,
        },
        "timestamps": {"created_at": timestamp, "updated_at": timestamp, "completed_at": None},
        "lineage": {"parent_run_id": None, "relation": None, "reason": None},
        "input": {
            "request_path": "input/request.md",
            "attachments_path": "input/attachments",
            "approved_brief_path": None,
        },
        "execution": {"adapter": adapter, "provider": None, "model": None, "effort": None},
        "versions": {
            "harness": __version__,
            "specification": "prototype-00-60",
            "run_schema": "1.0",
            "deck_schema": "1.0",
            "qa_schema": "1.0",
        },
        "design": {
            "pack": defaults.get("design_pack", "warm_clean"),
            "version": None,
            "brand_overlay": None,
            "overrides": {},
        },
        "output": {
            "profile": defaults.get("output_profile", "html_pdf"),
            "aspect_ratio": defaults.get("aspect_ratio", "16:9"),
            "language": defaults.get("language", "ja"),
        },
        "progress": {
            "current_attempt": 0,
            "attempt_count": 0,
            "current_phase": "preflight",
            "last_step": "run_created",
        },
        "quality": {
            "latest_qa": None,
            "qa_result": None,
            "latest_review": None,
            "human_result": "pending",
        },
        "delivery": {"accepted_attempt": None, "html": None, "pdf": None},
        "guidance": {
            "status_label": STATUS_LABELS["created"],
            "last_action": "制作記録を作成しました",
            "next_action": "依頼内容と添付資料を確認してください",
        },
        "sessions": [],
        "resolved_config": {
            "mode": defaults.get("mode", "interactive"),
            "design_pack": defaults.get("design_pack", "warm_clean"),
            "output_profile": defaults.get("output_profile", "html_pdf"),
            "aspect_ratio": defaults.get("aspect_ratio", "16:9"),
            "require_human_approval": config.get("qa", {}).get("require_human_approval", True),
        },
    }
    validate_document(project_root, "run", run)
    atomic_write_json(run_dir / "run.json", run)
    specification_files = [
        project_root / "PROJECT_INSTRUCTIONS.md",
        *(project_root / f"{number}_{name}.md" for number, name in (
            ("00", "MASTER"),
            ("10", "CONTENT"),
            ("20", "DESIGN"),
            ("30", "LAYOUTS"),
            ("40", "VISUALS"),
            ("50", "OUTPUTS"),
            ("60", "QA"),
        )),
    ]
    existing_specification_files = [path for path in specification_files if path.is_file()]
    font_path = project_root / "skills/slide-system/assets/fonts/NotoSansJP-Variable.ttf"
    run_lock = {
        "schema_version": "1.0",
        "run_id": run_id,
        "created_at": timestamp,
        "versions": run["versions"],
        "resolved_config": run["resolved_config"],
        "checksums": {
            "specification": sha256_files(existing_specification_files, relative_to=project_root),
            "configuration": sha256_json(config),
            "font_bundle": sha256_file(font_path) if font_path.is_file() else None,
        },
    }
    atomic_write_json(run_dir / "run.lock.json", run_lock)
    append_jsonl(
        run_dir / "events.jsonl",
        {"event": "run_created", "at": timestamp, "run_id": run_id, "adapter": adapter},
    )
    regenerate_index(project_root, config)
    return run


def list_runs(project_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    root = runs_root(project_root, config)
    if not root.exists():
        return []
    results: list[dict[str, Any]] = []
    for path in root.glob("run_*/run.json"):
        try:
            value = read_json(path)
        except (OSError, ValueError):
            continue
        value["_run_dir"] = str(path.parent)
        results.append(value)
    return sorted(
        results,
        key=lambda item: (
            item.get("timestamps", {}).get("updated_at", ""),
            item.get("run_id", ""),
        ),
        reverse=True,
    )


def find_run(
    project_root: Path,
    config: dict[str, Any],
    selector: str | None = None,
    *,
    latest: bool = False,
) -> dict[str, Any]:
    runs = list_runs(project_root, config)
    if latest:
        if not runs:
            raise RunNotFoundError("最近の制作はありません")
        return runs[0]
    if not selector:
        raise RunNotFoundError("Run ID、タイトルの一部、または--latestを指定してください")
    root = runs_root(project_root, config)
    exact_path = root / selector / "run.json"
    if exact_path.is_file():
        value = read_json(exact_path)
        value["_run_dir"] = str(exact_path.parent)
        return value
    query = selector.casefold()
    matches = []
    for run in runs:
        display = run.get("display", {})
        haystack = " ".join(
            [display.get("title", ""), display.get("summary", ""), *display.get("tags", [])]
        ).casefold()
        if query in haystack:
            matches.append(run)
    if not matches:
        raise RunNotFoundError(f"該当する制作がありません: {selector}")
    if len(matches) > 1:
        raise AmbiguousRunError(selector, matches)
    return matches[0]


def _relative_artifact(run: dict[str, Any], key: str) -> str | None:
    path = run.get("delivery", {}).get(key)
    return f"./{run['run_id']}/{path}" if path else None


def _index_entry(run: dict[str, Any]) -> dict[str, Any]:
    display = run.get("display", {})
    guidance = run.get("guidance", {})
    updated = run.get("timestamps", {}).get("updated_at", "")
    updated_label = updated.replace("T", " ")[:16] if updated else "不明"
    thumbnail = display.get("thumbnail")
    if thumbnail:
        thumbnail = f"./{run['run_id']}/{thumbnail}"
    title = display.get("title") or "無題の制作"
    summary = display.get("summary") or ""
    tags = display.get("tags") or []
    return {
        "run_id": run["run_id"],
        "title": title,
        "summary": summary,
        "tags": tags,
        "thumbnail": thumbnail,
        "status": run.get("status", "created"),
        "status_label": guidance.get("status_label") or STATUS_LABELS.get(run.get("status"), "状態不明"),
        "updated_at": updated,
        "updated_label": updated_label,
        "adapter": run.get("execution", {}).get("adapter"),
        "design_pack": run.get("design", {}).get("pack"),
        "next_action": guidance.get("next_action"),
        "html": _relative_artifact(run, "html"),
        "pdf": _relative_artifact(run, "pdf"),
        "search_text": " ".join([title, summary, *tags]).casefold(),
    }


def regenerate_index(project_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    root = runs_root(project_root, config)
    root.mkdir(parents=True, exist_ok=True)
    entries = [_index_entry(run) for run in list_runs(project_root, config)]
    atomic_write_json(root / "index.json", {"schema_version": "1.0", "runs": entries})
    latest = {"run_id": entries[0]["run_id"] if entries else None, "updated_at": now_iso()}
    atomic_write_json(root / "latest.json", latest)
    if config.get("runs", {}).get("generate_index", True):
        write_dashboard(root / "index.html", entries)
    return entries
