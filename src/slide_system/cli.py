from __future__ import annotations

import argparse
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
    print(f"  ID:   {run.get('run_id')}")
    if run.get("_run_dir"):
        print(f"  場所: {run['_run_dir']}")


def _resolve_run(args: argparse.Namespace, project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    try:
        return find_run(project_root, config, args.selector, latest=args.latest)
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
        except OSError as exc:
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
    return 2
