from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

from . import __version__
from .runs import AmbiguousRunError, RunNotFoundError, create_run, find_run, list_runs, regenerate_index, runs_root
from .storage import read_json
from .validation import validate_file


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "slide-system.config.json").is_file():
            return candidate
    raise FileNotFoundError("slide-system.config.jsonが見つかりません。--project-rootで指定してください。")


def load_config(project_root: Path) -> dict[str, Any]:
    return read_json(project_root / "slide-system.config.json")


def _version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    completed = subprocess.run([executable, "--version"], capture_output=True, text=True, check=False)
    return (completed.stdout or completed.stderr).strip() or None


def _node_dependencies() -> tuple[bool, str]:
    executable = shutil.which("node")
    if not executable:
        return False, "Node.jsが見つかりません"
    completed = subprocess.run(
        [executable, "-e", "require('playwright');require('pdf-lib');process.stdout.write('playwright, pdf-lib')"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return True, completed.stdout.strip()
    return False, "npm.cmd installを実行してください"


def _browser_path() -> Path | None:
    candidates = [
        os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    executable = shutil.which("node")
    if executable:
        completed = subprocess.run(
            [executable, "-e", "process.stdout.write(require('playwright').chromium.executablePath())"],
            capture_output=True,
            text=True,
            check=False,
        )
        managed = Path(completed.stdout.strip()) if completed.returncode == 0 and completed.stdout.strip() else None
        if managed and managed.is_file():
            return managed
    return None


def doctor(project_root: Path, config: dict[str, Any]) -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python", sys.version_info >= (3, 11), sys.version.split()[0]))
    jsonschema_available = importlib.util.find_spec("jsonschema") is not None
    checks.append(("Python依存", jsonschema_available, "jsonschema" if jsonschema_available else "python -m pip install -e . を実行してください"))
    node_version = _version("node")
    checks.append(("Node.js", node_version is not None, node_version or "見つかりません"))
    node_modules_ok, node_modules_detail = _node_dependencies()
    checks.append(("Node.js依存", node_modules_ok, node_modules_detail))
    browser = _browser_path()
    checks.append(("描画ブラウザ", browser is not None, str(browser) if browser else "Chrome、Edge、またはPlaywright Chromiumが必要です"))
    checks.append(("設定", True, str(project_root / "slide-system.config.json")))
    required = [
        project_root / "skills/slide-system/scripts/build_deck.py",
        project_root / "skills/slide-system/scripts/render_deck.mjs",
        project_root / "skills/slide-system/assets/deck-template.html",
        project_root / "skills/slide-system/assets/fonts/NotoSansJP-Variable.ttf",
    ]
    for path in required:
        checks.append((path.name, path.is_file(), str(path)))
    schema_dir = project_root / "schemas"
    schema_files = sorted(schema_dir.glob("*.schema.json")) if schema_dir.exists() else []
    schema_ok = bool(schema_files)
    for path in schema_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            schema_ok = False
            break
    checks.append(("JSON Schema", schema_ok, f"{len(schema_files)}ファイル"))
    print(f"Slide System Harness {__version__}")
    print(f"Project: {project_root}")
    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    return 0 if all(item[1] for item in checks) else 2


def _print_run(run: dict[str, Any]) -> None:
    display = run.get("display", {})
    guidance = run.get("guidance", {})
    print(f"{display.get('title') or '無題の制作'}")
    print(f"  状態: {guidance.get('status_label') or run.get('status')}")
    print(f"  更新: {run.get('timestamps', {}).get('updated_at', '不明')}")
    print(f"  次:   {guidance.get('next_action') or '未設定'}")
    attempt = run.get("progress", {}).get("current_attempt", 0)
    if attempt:
        print(f"  案:   Attempt {attempt:03d}")
    last_step = run.get("progress", {}).get("last_step")
    if last_step:
        print(f"  工程: {last_step}")
    print(f"  ID:   {run.get('run_id')}")
    if run.get("_run_dir"):
        print(f"  場所: {run['_run_dir']}")


def _resolve_run(args: argparse.Namespace, project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    return _resolve_selector(project_root, config, args.selector, latest=args.latest)


def _resolve_selector(
    project_root: Path,
    config: dict[str, Any],
    selector: str | None,
    *,
    latest: bool = False,
) -> dict[str, Any]:
    try:
        return find_run(project_root, config, selector, latest=latest)
    except AmbiguousRunError as exc:
        print(f"「{exc.selector}」に該当する制作が複数あります:", file=sys.stderr)
        for run in exc.candidates:
            print(f"- {run['run_id']}: {run.get('display', {}).get('title', '無題')}", file=sys.stderr)
        raise SystemExit(2) from exc
    except RunNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slide-system", description="Slide System local harness")
    parser.add_argument("--project-root", type=Path, help="slide-systemリポジトリの場所")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="実行環境を確認する")
    open_parser = subparsers.add_parser("open", help="ローカル管理画面を開く")
    open_parser.add_argument("--no-browser", action="store_true", help="管理画面を生成するだけにする")

    validate_parser = subparsers.add_parser("validate", help="JSONファイルを共通スキーマで検証する")
    validate_parser.add_argument("schema", choices=["run", "deck", "approved-brief", "attempt", "step", "qa-report", "review", "design-pack", "adapter", "baseline"])
    validate_parser.add_argument("path", type=Path)

    run_parser = subparsers.add_parser("run", help="制作記録を管理する")
    run_subparsers = run_parser.add_subparsers(dest="run_command", required=True)
    new_parser = run_subparsers.add_parser("new", help="新しい制作記録を作る")
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--summary", default="")
    new_parser.add_argument("--tag", action="append", default=[])
    new_parser.add_argument("--adapter", default="manual", choices=["manual", "codex", "claude-code", "claude-web"])
    new_parser.add_argument("--request", type=Path)
    run_subparsers.add_parser("list", help="制作一覧を表示する")
    for command in ("status", "resume"):
        item = run_subparsers.add_parser(command, help="制作の状態を確認する" if command == "status" else "制作の再開位置を確認する")
        item.add_argument("selector", nargs="?")
        item.add_argument("--latest", action="store_true")
    transition_parser = run_subparsers.add_parser("transition", help="Runの状態を変更する")
    transition_parser.add_argument("selector")
    transition_parser.add_argument("--status", required=True)
    transition_parser.add_argument("--last-action", required=True)
    transition_parser.add_argument("--next-action", required=True)
    transition_parser.add_argument("--phase")
    transition_parser.add_argument("--last-step")
    transition_parser.add_argument("--owner", default="manual")

    brief_parser = subparsers.add_parser("brief", help="制作条件の承認を記録する")
    brief_subparsers = brief_parser.add_subparsers(dest="brief_command", required=True)
    brief_approve = brief_subparsers.add_parser("approve", help="承認済みBriefを登録する")
    brief_approve.add_argument("selector")
    brief_approve.add_argument("--file", required=True, type=Path)
    brief_approve.add_argument("--owner", default="manual")

    attempt_parser = subparsers.add_parser("attempt", help="制作候補を管理する")
    attempt_subparsers = attempt_parser.add_subparsers(dest="attempt_command", required=True)
    attempt_new = attempt_subparsers.add_parser("new", help="新しいAttemptを作る")
    attempt_new.add_argument("selector")
    attempt_new.add_argument("--deck", type=Path)
    attempt_new.add_argument("--reason", default="")
    attempt_new.add_argument("--owner", default="manual")
    attempt_revise = attempt_subparsers.add_parser("revise", help="QA FAILから新しい修正Attemptを作る")
    attempt_revise.add_argument("selector")
    attempt_revise.add_argument("--deck", type=Path, help="省略時は直前Attemptのdeck.jsonを複製する")
    attempt_revise.add_argument("--reason", default="")
    attempt_revise.add_argument("--owner", default="manual")

    step_parser = subparsers.add_parser("step", help="Attempt内の工程を管理する")
    step_subparsers = step_parser.add_subparsers(dest="step_command", required=True)
    step_start = step_subparsers.add_parser("start", help="Stepを開始する")
    step_start.add_argument("selector")
    step_start.add_argument("--name", required=True)
    step_start.add_argument("--owner", default="manual")
    step_finish = step_subparsers.add_parser("finish", help="Stepを完了または失敗として記録する")
    step_finish.add_argument("selector")
    step_finish.add_argument("--step-id", required=True)
    step_finish.add_argument("--failed", action="store_true")
    step_finish.add_argument("--message", default="")
    step_finish.add_argument("--owner", default="manual")

    build_command_parser = subparsers.add_parser("build", help="最新AttemptからHTMLを生成する")
    build_command_parser.add_argument("selector")
    build_command_parser.add_argument("--owner", default="manual")
    render_parser = subparsers.add_parser("render", help="全ページ視覚QAとPDF生成を実行する")
    render_parser.add_argument("selector")
    render_parser.add_argument("--pdf-approval", required=True, help="PDF生成を依頼した利用者のメッセージ")
    render_parser.add_argument("--owner", default="manual")
    adapter_parser = subparsers.add_parser("adapter", help="AI別の再開指示を作る")
    adapter_subparsers = adapter_parser.add_subparsers(dest="adapter_command", required=True)
    adapter_prepare = adapter_subparsers.add_parser("prepare", help="現在のRun状態から再開指示を生成する")
    adapter_prepare.add_argument("selector")
    adapter_prepare.add_argument("--adapter", required=True, choices=["codex", "claude-code"])
    adapter_prepare.add_argument("--owner", default="manual")
    review_parser = subparsers.add_parser("review", help="利用者レビューを記録する")
    review_subparsers = review_parser.add_subparsers(dest="review_command", required=True)
    review_record = review_subparsers.add_parser("record", help="レビューJSONを記録し、採用時はdeliveryへ保存する")
    review_record.add_argument("selector")
    review_record.add_argument("--file", required=True, type=Path)
    review_record.add_argument("--owner", default="manual")
    baseline_parser = subparsers.add_parser("baseline", help="承認済み比較基準を管理する")
    baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_command", required=True)
    baseline_approve = baseline_subparsers.add_parser("approve", help="完了Runを新しいベースラインとして保存する")
    baseline_approve.add_argument("selector")
    baseline_approve.add_argument("--case-id", required=True)
    baseline_approve.add_argument("--approver", required=True)
    baseline_approve.add_argument("--note", default="")
    baseline_compare = baseline_subparsers.add_parser("compare", help="最新Attemptをベースラインと比較する")
    baseline_compare.add_argument("selector")
    baseline_compare.add_argument("--baseline", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        project_root = args.project_root.resolve() if args.project_root else find_project_root(Path.cwd())
        config = load_config(project_root)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.command == "doctor":
        return doctor(project_root, config)
    if args.command == "validate":
        try:
            validate_file(project_root, args.schema, args.path.resolve())
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"PASS: {args.path} ({args.schema})")
        return 0
    if args.command == "open":
        regenerate_index(project_root, config)
        dashboard = runs_root(project_root, config) / "index.html"
        print(f"管理画面: {dashboard}")
        if not args.no_browser:
            webbrowser.open(dashboard.resolve().as_uri())
        return 0
    if args.command == "run" and args.run_command == "new":
        try:
            run = create_run(
                project_root,
                config,
                title=args.title,
                summary=args.summary,
                tags=args.tag,
                adapter=args.adapter,
                request_source=args.request,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        run["_run_dir"] = str(runs_root(project_root, config) / run["run_id"])
        _print_run(run)
        return 0
    if args.command == "run" and args.run_command == "list":
        runs = list_runs(project_root, config)
        if not runs:
            print("制作記録はまだありません。")
            return 0
        for index, run in enumerate(runs):
            if index:
                print()
            _print_run(run)
        return 0
    if args.command == "run" and args.run_command in {"status", "resume"}:
        run = _resolve_run(args, project_root, config)
        _print_run(run)
        return 0
    if args.command == "run" and args.run_command == "transition":
        from .state import transition_run

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            run = transition_run(
                project_root,
                config,
                selected["run_id"],
                new_status=args.status,
                owner=args.owner,
                last_action=args.last_action,
                next_action=args.next_action,
                phase=args.phase,
                last_step=args.last_step,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        _print_run(run)
        return 0
    if args.command == "brief" and args.brief_command == "approve":
        from .briefs import approve_brief

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            run = approve_brief(
                project_root,
                config,
                selected["run_id"],
                brief_source=args.file,
                owner=args.owner,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        _print_run(run)
        return 0
    if args.command == "attempt" and args.attempt_command == "new":
        from .attempts import create_attempt

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            attempt = create_attempt(
                project_root,
                config,
                selected["run_id"],
                owner=args.owner,
                deck_source=args.deck,
                reason=args.reason,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"Attempt {attempt['attempt']:03d}を作成しました")
        return 0
    if args.command == "attempt" and args.attempt_command == "revise":
        from .attempts import create_revision_attempt

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            attempt = create_revision_attempt(
                project_root,
                config,
                selected["run_id"],
                owner=args.owner,
                deck_source=args.deck,
                reason=args.reason,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"修正Attempt {attempt['attempt']:03d}を作成しました。直前Attemptは保持されています")
        return 0
    if args.command == "step" and args.step_command == "start":
        from .attempts import start_step

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            step = start_step(project_root, config, selected["run_id"], name=args.name, owner=args.owner)
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"{step['step_id']}を開始しました: {step['name']}")
        return 0
    if args.command == "step" and args.step_command == "finish":
        from .attempts import finish_step

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            step = finish_step(
                project_root,
                config,
                selected["run_id"],
                step_id=args.step_id,
                owner=args.owner,
                success=not args.failed,
                error={"message": args.message or "詳細なし"} if args.failed else None,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"{step['step_id']}: {step['status']}")
        return 0
    if args.command == "build":
        from .production import build_html

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            result = build_html(project_root, config, selected["run_id"], owner=args.owner)
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"HTML: {result['html']}")
        print(f"静的QA: {result['report']}")
        return 0
    if args.command == "render":
        from .production import render_pdf

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            result = render_pdf(
                project_root,
                config,
                selected["run_id"],
                owner=args.owner,
                pdf_approval=args.pdf_approval,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"HTML: {result['html']}")
        print(f"PDF: {result['pdf']}")
        print(f"視覚QA: {result['report']}")
        return 0
    if args.command == "adapter" and args.adapter_command == "prepare":
        from .adapters import prepare_session

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            output = prepare_session(project_root, config, selected["run_id"], adapter_id=args.adapter, owner=args.owner)
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(f"再開指示: {output}")
        return 0
    if args.command == "review" and args.review_command == "record":
        from .reviews import record_review

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            run = record_review(project_root, config, selected["run_id"], review_source=args.file, owner=args.owner)
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        _print_run(run)
        return 0
    if args.command == "baseline":
        from .baselines import approve_baseline, compare_baseline

        selected = _resolve_selector(project_root, config, args.selector)
        try:
            if args.baseline_command == "approve":
                path = approve_baseline(project_root, config, selected["run_id"], case_id=args.case_id, approver=args.approver, note=args.note)
                print(f"ベースライン: {path}")
            else:
                result = compare_baseline(project_root, config, selected["run_id"], baseline_path=args.baseline)
                print(f"比較結果: {result['result']}")
                for item in result["comparisons"]:
                    print(f"- {item['artifact']}: {item['result']}")
        except (OSError, ValueError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0
    return 2
