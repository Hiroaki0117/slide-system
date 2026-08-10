#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slide_system.runs import create_run, find_run, list_runs, regenerate_index  # noqa: E402


def config() -> dict:
    return {
        "defaults": {
            "language": "ja",
            "mode": "interactive",
            "design_pack": "warm_clean",
            "output_profile": "html_pdf",
            "aspect_ratio": "16:9",
        },
        "runs": {"directory": "runs", "generate_index": True},
        "qa": {"require_human_approval": True},
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        project_root = Path(temporary)
        request = project_root / "request.md"
        request.write_text("# 依頼\n\n短い依頼です。\n", encoding="utf-8")

        first = create_run(
            project_root,
            config(),
            title="新入社員向けセキュリティ研修",
            summary="社内研修で使用する基礎教材",
            tags=["研修", "セキュリティ"],
            adapter="codex",
            request_source=request,
        )
        second = create_run(
            project_root,
            config(),
            title="問い合わせ対応の改善提案",
            summary="受付後の振り分けを見直す",
            tags=["業務改善"],
            adapter="claude-code",
        )

        assert first["run_id"].endswith("001")
        assert second["run_id"].endswith("002")
        first_dir = project_root / "runs" / first["run_id"]
        assert (first_dir / "run.json").is_file()
        assert (first_dir / "events.jsonl").is_file()
        assert (first_dir / "input/request.md").read_text(encoding="utf-8") == request.read_text(encoding="utf-8")

        loaded = json.loads((first_dir / "run.json").read_text(encoding="utf-8"))
        assert loaded["display"]["title"] == "新入社員向けセキュリティ研修"
        assert loaded["guidance"]["next_action"]
        assert loaded["delivery"]["html"] is None

        all_runs = list_runs(project_root, config())
        assert len(all_runs) == 2
        assert find_run(project_root, config(), "セキュリティ")["run_id"] == first["run_id"]
        assert find_run(project_root, config(), latest=True)["run_id"] == second["run_id"]

        entries = regenerate_index(project_root, config())
        assert len(entries) == 2
        index = json.loads((project_root / "runs/index.json").read_text(encoding="utf-8"))
        assert index["runs"][0]["title"] == "問い合わせ対応の改善提案"
        latest = json.loads((project_root / "runs/latest.json").read_text(encoding="utf-8"))
        assert latest["run_id"] == second["run_id"]
        dashboard = (project_root / "runs/index.html").read_text(encoding="utf-8")
        assert "Slide System" in dashboard
        assert "タイトル・概要・タグで検索" in dashboard

        schema_files = sorted((ROOT / "schemas").glob("*.schema.json"))
        assert len(schema_files) >= 7
        for schema_file in schema_files:
            json.loads(schema_file.read_text(encoding="utf-8"))

    print("PASS: harness Phase 0 run management and dashboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
