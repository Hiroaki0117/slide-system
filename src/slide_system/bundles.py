from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from .attempts import create_attempt
from .runs import find_run, now_iso
from .storage import atomic_write_json, read_json
from .validation import validate_document


MAX_FILES = 50
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
RESULT_ALLOWED = {"bundle.json", "deck.json", "deck.html", "deck.pdf", "qa-report.json", "contact-sheet.png", "RESULT_NOTES.md"}


class BundleError(ValueError):
    pass


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return bool(name) and not path.is_absolute() and ".." not in path.parts and not (path.parts and ":" in path.parts[0])


def _validate_zip(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = [item for item in archive.infolist() if not item.is_dir()]
    if not members or len(members) > MAX_FILES:
        raise BundleError(f"Bundleのファイル数が不正です: {len(members)}")
    total = 0
    for member in members:
        if not _safe_member(member.filename):
            raise BundleError(f"危険なZIPパスです: {member.filename}")
        if member.file_size > MAX_FILE_BYTES:
            raise BundleError(f"Bundle内ファイルが大きすぎます: {member.filename}")
        total += member.file_size
        unix_mode = member.external_attr >> 16
        if unix_mode and (unix_mode & 0o170000) == 0o120000:
            raise BundleError(f"シンボリックリンクは取り込めません: {member.filename}")
    if total > MAX_TOTAL_BYTES:
        raise BundleError("Bundleの合計サイズが上限を超えています")
    return members


def export_run_bundle(project_root: Path, config: dict[str, Any], selector: str, *, output: Path) -> Path:
    run = find_run(project_root, config, selector)
    run_dir = Path(run["_run_dir"])
    files: dict[str, Path | str] = {
        "request.md": run_dir / "input" / "request.md",
        "BUNDLE_INSTRUCTIONS.md": "# Claude Webへの依頼\n\nslide-systemスキルを有効にし、依頼・添付・承認済みBrief・deck.jsonを確認してください。制作条件が未承認なら確認を先に行い、承認済みならその範囲だけで制作してください。結果はdeck.jsonを必須とするResult Bundleで返してください。HTML/PDFを返してもローカルで再検証します。\n",
    }
    brief = run_dir / "brief" / "approved-brief.json"
    if brief.is_file():
        files["approved-brief.json"] = brief
    attempt_number = int(run.get("progress", {}).get("current_attempt", 0))
    if attempt_number:
        deck = run_dir / "attempts" / f"{attempt_number:03d}" / "deck.json"
        if deck.is_file():
            files["deck.json"] = deck
    attachments = run_dir / "input" / "attachments"
    if attachments.is_dir():
        for path in sorted(item for item in attachments.rglob("*") if item.is_file()):
            relative = path.relative_to(attachments).as_posix()
            if not _safe_member(relative):
                raise BundleError(f"添付ファイル名をBundleへ保存できません: {relative}")
            files[f"attachments/{relative}"] = path
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.0",
        "bundle_type": "run_bundle",
        "bundle_id": f"{run['run_id']}_export",
        "run_id": run["run_id"],
        "created_at": now_iso(),
        "source_bundle_id": None,
        "files": ["bundle.json", *files.keys()],
    }
    validate_document(project_root, "bundle-manifest", manifest)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("bundle.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for name, source in files.items():
            if isinstance(source, str):
                archive.writestr(name, source)
            elif source.is_file():
                archive.write(source, name)
    return output


def import_result_bundle(
    project_root: Path,
    config: dict[str, Any],
    selector: str,
    *,
    bundle_path: Path,
    owner: str,
) -> dict[str, Any]:
    run = find_run(project_root, config, selector)
    with zipfile.ZipFile(bundle_path.resolve(), "r") as archive:
        members = _validate_zip(archive)
        names = {item.filename.replace("\\", "/") for item in members}
        unexpected = names - RESULT_ALLOWED
        if unexpected:
            raise BundleError(f"Result Bundleに許可されていないファイルがあります: {', '.join(sorted(unexpected))}")
        if "bundle.json" not in names or "deck.json" not in names:
            raise BundleError("Result Bundleにはbundle.jsonとdeck.jsonが必要です")
        manifest = json.loads(archive.read("bundle.json").decode("utf-8"))
        validate_document(project_root, "bundle-manifest", manifest)
        if manifest["bundle_type"] != "result_bundle" or manifest["run_id"] != run["run_id"]:
            raise BundleError("Result Bundleの種類またはRun IDが一致しません")
        if set(manifest["files"]) != names:
            raise BundleError("bundle.jsonのファイル一覧とZIP内容が一致しません")
        with tempfile.TemporaryDirectory(prefix="slide-system-result-bundle-") as temporary:
            temporary_root = Path(temporary)
            for member in members:
                destination = temporary_root / member.filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
            deck = read_json(temporary_root / "deck.json")
            next_attempt = int(run.get("progress", {}).get("attempt_count", 0)) + 1
            deck["run_id"] = run["run_id"]
            deck["attempt"] = next_attempt
            validate_document(project_root, "deck", deck)
            normalized = temporary_root / "normalized-deck.json"
            atomic_write_json(normalized, deck)
            attempt = create_attempt(project_root, config, run["run_id"], owner=owner, deck_source=normalized, reason="Claude Web Result Bundle取り込み")
            run_dir = Path(find_run(project_root, config, run["run_id"])["_run_dir"])
            imported_dir = run_dir / "attempts" / f"{attempt['attempt']:03d}" / "imported"
            imported_dir.mkdir()
            for name in names - {"bundle.json", "deck.json"}:
                shutil.copy2(temporary_root / name, imported_dir / Path(name).name)
            atomic_write_json(imported_dir / "bundle.json", manifest)
    return {"attempt": attempt["attempt"], "run_id": run["run_id"], "imported": imported_dir, "next_action": "ローカルのbuildとQAを実行してください"}
