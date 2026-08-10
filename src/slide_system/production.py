from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .attempts import finish_step, start_step
from .designs import DesignPack, load_design_pack
from .hashing import sha256_files
from .legacy import convert_deck_to_legacy
from .runs import STATUS_LABELS, find_run, now_iso
from .state import mutate_run
from .storage import atomic_write_json, read_json
from .validation import validate_document, validate_file


class ProductionError(RuntimeError):
    pass


def _attempt_context(project_root: Path, config: dict[str, Any], run_id: str) -> tuple[dict[str, Any], Path, int, Path]:
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])
    attempt_number = int(selected.get("progress", {}).get("current_attempt", 0))
    if attempt_number < 1:
        raise ProductionError("先に承認済みBriefとAttemptを作成してください")
    attempt_dir = run_dir / "attempts" / f"{attempt_number:03d}"
    deck_path = attempt_dir / "deck.json"
    if not deck_path.is_file():
        raise ProductionError(f"deck.jsonがありません: {deck_path}")
    return selected, run_dir, attempt_number, attempt_dir


def _approved_work_state(run_dir: Path, *, phase: str, pdf_approval: str | None = None) -> dict[str, Any]:
    brief_path = run_dir / "brief" / "approved-brief.json"
    if not brief_path.is_file():
        raise ProductionError("承認済みBriefがありません")
    brief = read_json(brief_path)
    approval_message = str(brief.get("approval_message", "")).strip()
    if not approval_message:
        raise ProductionError("承認時の利用者メッセージが記録されていません")
    state: dict[str, Any] = {
        "phase": phase,
        "delivery_profile": "standard",
        "approval": {"status": "approved", "user_reply": approval_message},
        "revision": {"source_artifact": "", "scope": "", "user_reply": ""},
    }
    if pdf_approval:
        state["pdf_request"] = {"user_reply": pdf_approval}
    return state


def _design_checksum(project_root: Path, pack: DesignPack) -> str:
    paths = [pack.root / "design.json", *pack.entrypoints.values(), pack.template, pack.font]
    return sha256_files(paths, relative_to=project_root)


def _update_attempt_and_run(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    owner: str,
    event: str,
    attempt_status: str,
    run_status: str,
    artifacts: dict[str, str],
    last_action: str,
    next_action: str,
    qa_result: str | None = None,
    design_pack: DesignPack | None = None,
    event_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        number = int(run["progress"]["current_attempt"])
        attempt_path = run_dir / "attempts" / f"{number:03d}" / "attempt.json"
        attempt = read_json(attempt_path)
        attempt["status"] = attempt_status
        attempt["updated_at"] = now_iso()
        attempt.setdefault("artifacts", {}).update(artifacts)
        validate_document(project_root, "attempt", attempt)
        atomic_write_json(attempt_path, attempt)
        run["status"] = run_status
        run["progress"]["current_phase"] = run_status
        run["progress"]["last_step"] = event
        run["guidance"] = {
            "status_label": STATUS_LABELS[run_status],
            "last_action": last_action,
            "next_action": next_action,
        }
        if qa_result is not None:
            run["quality"]["qa_result"] = qa_result
            qa_path = artifacts.get("visual_qa") or artifacts.get("static_qa")
            run["quality"]["latest_qa"] = f"attempts/{number:03d}/{qa_path}" if qa_path else None
        if design_pack:
            run["design"]["version"] = design_pack.version
            run["versions"]["design_pack"] = f"{design_pack.design_id}@{design_pack.version}"
            run_lock_path = run_dir / "run.lock.json"
            run_lock = read_json(run_lock_path)
            run_lock["versions"]["harness"] = __version__
            run_lock["versions"]["design_pack"] = run["versions"]["design_pack"]
            run_lock["checksums"]["design_pack"] = _design_checksum(project_root, design_pack)
            atomic_write_json(run_lock_path, run_lock)
        return run

    return mutate_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event=event,
        mutator=apply,
        event_details=event_details,
    )


def build_html(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    owner: str,
) -> dict[str, Any]:
    run, run_dir, attempt_number, attempt_dir = _attempt_context(project_root, config, run_id)
    if run["status"] != "generating":
        raise ProductionError(f"HTMLを生成できる状態ではありません: {run['status']}")
    deck_path = attempt_dir / "deck.json"
    deck = validate_file(project_root, "deck", deck_path)
    design_id = str(run.get("design", {}).get("pack") or config.get("defaults", {}).get("design_pack", "warm_clean"))
    pack = load_design_pack(project_root, design_id)
    legacy = convert_deck_to_legacy(deck, pack, asset_base=deck_path.parent)
    build_dir = attempt_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    legacy_path = build_dir / "legacy-deck.json"
    work_state_path = build_dir / "work-state.json"
    html_path = attempt_dir / "deck.html"
    report_path = attempt_dir / "static-qa-legacy.json"
    atomic_write_json(legacy_path, legacy)
    atomic_write_json(work_state_path, _approved_work_state(run_dir, phase="building"))

    step = start_step(
        project_root,
        config,
        run_id,
        name="build_html",
        owner=owner,
        input_data={"deck": "deck.json", "design_pack": f"{pack.design_id}@{pack.version}"},
    )
    builder = project_root / "skills/slide-system/scripts/build_deck.py"
    command = [
        sys.executable,
        str(builder),
        "--input",
        str(legacy_path),
        "--work-state",
        str(work_state_path),
        "--template",
        str(pack.template),
        "--output",
        str(html_path),
        "--report",
        str(report_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        finish_step(
            project_root,
            config,
            run_id,
            step_id=step["step_id"],
            owner=owner,
            success=False,
            error={"message": completed.stderr.strip() or completed.stdout.strip() or "HTML生成に失敗しました"},
        )
        report = read_json(report_path) if report_path.is_file() else {}
        run_status = "needs_revision" if report.get("status") == "FAIL" else "failed"
        _update_attempt_and_run(
            project_root,
            config,
            run_id,
            owner=owner,
            event="html_build_failed",
            attempt_status="needs_revision" if run_status == "needs_revision" else "failed",
            run_status=run_status,
            artifacts={"legacy_deck": "build/legacy-deck.json", "static_qa": "static-qa-legacy.json"},
            last_action="HTML生成または静的QAに失敗しました",
            next_action="QAレポートを確認し、新しいAttemptで修正してください",
            qa_result="FAIL",
            design_pack=pack,
        )
        raise ProductionError(completed.stderr.strip() or completed.stdout.strip() or "HTML生成に失敗しました")

    finish_step(
        project_root,
        config,
        run_id,
        step_id=step["step_id"],
        owner=owner,
        success=True,
        output_data={"html": "deck.html", "static_qa": "static-qa-legacy.json"},
    )
    updated = _update_attempt_and_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="html_built",
        attempt_status="qa",
        run_status="qa",
        artifacts={
            "html": "deck.html",
            "legacy_deck": "build/legacy-deck.json",
            "work_state": "build/work-state.json",
            "static_qa": "static-qa-legacy.json",
        },
        last_action=f"Attempt {attempt_number:03d}のHTMLを生成しました",
        next_action="HTMLの全ページを描画し、視覚QAを実行してください",
        design_pack=pack,
    )
    return {"run": updated, "html": html_path, "report": report_path, "attempt": attempt_number}


def _node_executable() -> str:
    node = shutil.which("node")
    if not node:
        raise ProductionError("Node.jsが見つかりません。slide-system doctorを実行してください")
    return node


def _browser_path() -> str | None:
    candidates = [
        os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def render_pdf(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    owner: str,
    pdf_approval: str,
) -> dict[str, Any]:
    if not pdf_approval.strip():
        raise ProductionError("PDF生成には利用者の明示的な依頼文が必要です")
    run, run_dir, attempt_number, attempt_dir = _attempt_context(project_root, config, run_id)
    if run["status"] != "qa":
        raise ProductionError(f"視覚QAとPDF生成を実行できる状態ではありません: {run['status']}")
    html_path = attempt_dir / "deck.html"
    if not html_path.is_file():
        raise ProductionError(f"HTMLがありません: {html_path}")
    build_dir = attempt_dir / "build"
    work_state_path = build_dir / "render-work-state.json"
    atomic_write_json(work_state_path, _approved_work_state(run_dir, phase="qa", pdf_approval=pdf_approval))
    pdf_path = attempt_dir / "deck.pdf"
    render_dir = attempt_dir / "renders"
    report_path = attempt_dir / "visual-qa-legacy.json"
    step = start_step(
        project_root,
        config,
        run_id,
        name="render_pdf",
        owner=owner,
        input_data={"html": "deck.html", "pdf_approval": pdf_approval},
    )
    command = [
        _node_executable(),
        str(project_root / "skills/slide-system/scripts/render_deck.mjs"),
        "--html",
        str(html_path),
        "--pdf",
        str(pdf_path),
        "--renders",
        str(render_dir),
        "--report",
        str(report_path),
        "--work-state",
        str(work_state_path),
    ]
    browser = _browser_path()
    if browser:
        command.extend(["--browser", browser])
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    success = completed.returncode == 0
    finish_step(
        project_root,
        config,
        run_id,
        step_id=step["step_id"],
        owner=owner,
        success=success,
        output_data={"pdf": "deck.pdf", "visual_qa": "visual-qa-legacy.json"} if success else {},
        error=None if success else {"message": completed.stderr.strip() or completed.stdout.strip() or "視覚QAに失敗しました"},
    )
    artifacts = {
        "pdf": "deck.pdf",
        "visual_qa": "visual-qa-legacy.json",
        "renders": "renders",
        "contact_sheet": "renders/contact-sheet.png",
        "render_work_state": "build/render-work-state.json",
    }
    updated = _update_attempt_and_run(
        project_root,
        config,
        run_id,
        owner=owner,
        event="visual_qa_passed" if success else "visual_qa_failed",
        attempt_status="ready_for_review" if success else "needs_revision",
        run_status="ready_for_review" if success else "needs_revision",
        artifacts=artifacts,
        last_action="HTML/PDFの全ページQAが完了しました" if success else "視覚QAで問題が見つかりました",
        next_action="HTMLとPDFを確認してください" if success else "QAレポートを確認し、新しいAttemptで修正してください",
        qa_result="PASS" if success else "FAIL",
        event_details={"pdf_approval": pdf_approval},
    )
    if not success:
        raise ProductionError(completed.stderr.strip() or completed.stdout.strip() or "視覚QAに失敗しました")
    return {
        "run": updated,
        "html": html_path,
        "pdf": pdf_path,
        "report": report_path,
        "renders": render_dir,
        "attempt": attempt_number,
    }
