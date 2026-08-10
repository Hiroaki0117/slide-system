from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .runs import find_run, now_iso
from .state import mutate_run
from .storage import atomic_write_text, read_json
from .validation import validate_document


@dataclass(frozen=True)
class Adapter:
    adapter_id: str
    name: str
    version: str
    root: Path
    instructions: Path
    capabilities: dict[str, bool]


def load_adapter(project_root: Path, adapter_id: str) -> Adapter:
    root = project_root / "harness" / "adapters" / adapter_id
    manifest_path = root / "adapter.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"アダプターが見つかりません: {adapter_id}")
    manifest = read_json(manifest_path)
    validate_document(project_root, "adapter", manifest)
    entrypoint = root / manifest["entrypoint"]
    if not entrypoint.is_file():
        raise FileNotFoundError(f"アダプター指示が見つかりません: {entrypoint}")
    return Adapter(manifest["id"], manifest["name"], manifest["version"], root, entrypoint, manifest["capabilities"])


def _resume_action(run: dict[str, Any]) -> tuple[str, list[str]]:
    status = run["status"]
    actions: dict[str, tuple[str, list[str]]] = {
        "created": ("依頼と添付資料を確認し、不足情報だけを質問する", ["まだ制作を開始しない", "質問が不要でも制作内容確認へ進む"]),
        "questions_pending": ("利用者の回答を待ち、回答後に制作条件と構成案をまとめる", ["未回答項目を推測で確定しない"]),
        "confirmation_pending": ("制作条件と構成案への明示的な承認を待つ", ["承認前にHTMLを生成しない"]),
        "approved": ("承認済みBriefからdeck.jsonとAttemptを作成する", ["承認済み範囲を勝手に拡大しない"]),
        "generating": ("最新Attemptのdeck.jsonとStepを確認し、未完了の生成工程から再開する", ["成功済みStepを理由なく再実行しない"]),
        "qa": ("HTMLとQA状況を確認し、PDFの明示的な依頼があればrenderを実行する", ["PDF依頼を推測しない"]),
        "needs_revision": ("qa-report.jsonのopen issueを確認し、新しい修正Attemptを作る", ["直前Attemptを上書きしない"]),
        "ready_for_review": ("HTML/PDFを利用者へ提示し、採用または修正指示を待つ", ["自動QA PASSだけで完了にしない"]),
        "complete": ("完了済み成果物を参照する", ["このRunを変更しない"]),
        "blocked": ("run.jsonのnext_actionにある不足条件を解消する", ["権限や資料不足を推測で回避しない"]),
        "failed": ("最後の失敗Stepとエラーを確認し、安全に再実行できるか判断する", ["原因未確認のまま反復しない"]),
        "cancelled": ("中止済みRunとして参照のみ行う", ["このRunで制作を再開しない"]),
    }
    return actions[status]


def prepare_session(
    project_root: Path,
    config: dict[str, Any],
    run_id: str,
    *,
    adapter_id: str,
    owner: str,
) -> Path:
    adapter = load_adapter(project_root, adapter_id)
    selected = find_run(project_root, config, run_id)
    run_dir = Path(selected["_run_dir"])
    action, prohibitions = _resume_action(selected)
    attempt = int(selected.get("progress", {}).get("current_attempt", 0))
    brief = run_dir / "brief" / "approved-brief.json"
    qa = run_dir / "attempts" / f"{attempt:03d}" / "qa-report.json" if attempt else None
    lines = [
        f"# {selected['display']['title']} - {adapter.name}再開指示",
        "",
        f"- Run: `{run_id}`",
        f"- 状態: `{selected['status']}` ({selected['guidance']['status_label']})",
        f"- 最新Attempt: `{attempt:03d}`" if attempt else "- 最新Attempt: なし",
        f"- 最後の操作: {selected['guidance']['last_action']}",
        f"- 次の操作: {action}",
        "",
        "## 最初に読むファイル",
        "",
        f"1. `{run_dir / 'run.json'}`",
        f"2. `{run_dir / 'input' / 'request.md'}`",
    ]
    if brief.is_file():
        lines.append(f"3. `{brief}`")
    if attempt:
        lines.append(f"4. `{run_dir / 'attempts' / f'{attempt:03d}' / 'deck.json'}`")
    if qa and qa.is_file():
        lines.append(f"5. `{qa}`")
    lines.extend(["", "## このセッションでしないこと", "", *[f"- {item}" for item in prohibitions], "", "## 共通ルール", "", "- 00〜60を正本とする", "- 質問、制作内容、PDF、最終採用の承認ゲートを省略しない", "- チャット履歴ではなくRunファイルを根拠に再開する", ""])
    output = run_dir / ".state" / f"resume-{adapter_id}.md"
    atomic_write_text(output, "\n".join(lines))

    def apply(run: dict[str, Any]) -> dict[str, Any]:
        run["execution"]["adapter"] = adapter_id
        run["sessions"].append({"adapter": adapter_id, "prepared_at": now_iso(), "resume_path": str(output.relative_to(run_dir)).replace("\\", "/")})
        return run

    mutate_run(project_root, config, run_id, owner=owner, event="adapter_session_prepared", mutator=apply, event_details={"adapter": adapter_id})
    return output
