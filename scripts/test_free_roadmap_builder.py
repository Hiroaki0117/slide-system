#!/usr/bin/env python3
"""Regression checks for the free-plan compact roadmap adapter."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "skills" / "slide-system" / "scripts" / "build_free_roadmap.py"
BRIEF = ROOT / "skills" / "slide-system" / "assets" / "free-roadmap-brief-example.json"
TEMPLATE = ROOT / "skills" / "slide-system" / "assets" / "deck-template.html"


def run_builder(work: Path, brief: dict, name: str) -> tuple[dict, str, dict]:
    brief_path = work / f"{name}-brief.json"
    state_path = work / "work-state.json"
    html_path = work / f"{name}.html"
    deck_path = work / f"{name}-deck.json"
    report_path = work / f"{name}-report.json"
    brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    state_path.write_text(
        json.dumps(
            {
                "phase": "approved",
                "delivery_profile": "staged",
                "approval": {"status": "approved", "user_reply": "この内容で制作する"},
                "confirmed_conditions": ["現在、脛の内側に軽い違和感がある"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable, str(BUILDER), "--brief", str(brief_path),
            "--work-state", str(state_path), "--template", str(TEMPLATE),
            "--output", str(html_path), "--deck-output", str(deck_path),
            "--report", str(report_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout), html_path.read_text(encoding="utf-8"), json.loads(report_path.read_text(encoding="utf-8"))


def main() -> int:
    valid = json.loads(BRIEF.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="slide-free-roadmap-") as temporary:
        work = Path(temporary)
        result, html, report = run_builder(work, valid, "valid")
        assert result["status"] == "PASS" and result["complete"] is True
        assert result["must_return_html"] is True and result["slide_count"] == 10
        assert len(result["user_review_points"]) == 3
        assert report["quality_gate"] == "UNCHANGED_STRICT_VALIDATOR"
        assert report["issues"] == []
        assert report["user_review_points"] == result["user_review_points"]
        assert "検証未完了ドラフト" not in html
        assert "slide-deck-data" in html and "__DRAFT_BANNER__" not in html
        assert ">PDF保存</button>" in html and "PDF保存不可" not in html

        compact = json.loads(json.dumps(valid, ensure_ascii=False))
        compact["phases"] = compact["phases"][1:]
        result, html, report = run_builder(work, compact, "four-phases")
        assert result["status"] == "PASS" and result["slide_count"] == 9
        assert "｜前半" not in html and "｜後半" not in html

        invalid = json.loads(json.dumps(valid, ensure_ascii=False))
        invalid["sources"] = [item for item in invalid["sources"] if item["role"] != "nutrition"]
        result, html, report = run_builder(work, invalid, "invalid")
        assert result["status"] == "DRAFT" and result["complete"] is False
        assert result["must_return_html"] is True and Path(result["html"]).exists()
        assert len(result["user_review_points"]) == 1
        assert report["quality_gate"] == "NOT_RUN_INPUT_INCOMPLETE"
        assert "検証未完了ドラフト" in html
        assert "PDF保存不可" in html and "aria-disabled=\"true\"" in html
        assert report["issues"][0]["code"] == "COMPACT_INPUT_ERROR"

    print("PASS: free-plan compact roadmap builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
