#!/usr/bin/env python3
"""Regression check for over-wrapped single-message headlines."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "slide-system"


def run(command: list[str], *, env: dict[str, str] | None = None, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, encoding="utf-8")
    if expect_success and completed.returncode:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}\n{completed.stderr}")
    if not expect_success and completed.returncode == 0:
        raise RuntimeError(f"Command unexpectedly passed: {' '.join(command)}")
    return completed


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="slide-system-message-wrap-") as temporary:
        work = Path(temporary)
        deck = {
            "deck_title": "メッセージ折り返し検査",
            "audience": "スライド制作者",
            "purpose": "過剰な折り返しを視覚QAで検出する",
            "mode": "standalone",
            "high_stakes": False,
            "slides": [
                {
                    "layout": "cover",
                    "title": "メッセージ折り返し検査",
                    "date": "2026-08-10",
                },
                {
                    "layout": "single_message",
                    "job": "claim",
                    "visual_role": "explain",
                    "title": "重要な状態を確認します",
                    "headline": "この計画は現時点では実行不可の暫定案であり開始条件を満たすまで実行できません",
                    "body": "開始条件を別の短い文章で説明します。",
                },
                {
                    "layout": "sources_appendix",
                    "title": "出典",
                    "sources": [
                        {
                            "id": "R1",
                            "title": "視覚QA回帰テスト用入力",
                            "publisher": "slide-system",
                            "url": "https://example.com/visual-qa",
                            "checked": "2026-08-10",
                        }
                    ],
                },
            ],
        }

        deck_path = work / "deck.json"
        state_path = work / "work-state.json"
        html_path = work / "deck.html"
        pdf_path = work / "deck.pdf"
        render_dir = work / "renders"
        static_report = work / "static-qa.json"
        visual_report = work / "visual-qa.json"
        deck_path.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
        state_path.write_text(json.dumps({
            "phase": "approved",
            "delivery_profile": "standard",
            "approval": {"status": "approved", "user_reply": "制作を承認します"},
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        run([
            os.environ.get("SLIDE_SYSTEM_PYTHON", "python"),
            str(SKILL / "scripts" / "build_deck.py"),
            "--input", str(deck_path),
            "--work-state", str(state_path),
            "--template", str(SKILL / "assets" / "deck-template.html"),
            "--output", str(html_path),
            "--report", str(static_report),
        ])
        run([
            os.environ.get("SLIDE_SYSTEM_NODE", "node"),
            str(SKILL / "scripts" / "render_deck.mjs"),
            "--html", str(html_path),
            "--pdf", str(pdf_path),
            "--renders", str(render_dir),
            "--report", str(visual_report),
            "--work-state", str(state_path),
        ], env=os.environ.copy(), expect_success=False)

        report = json.loads(visual_report.read_text(encoding="utf-8"))
        failures = report.get("failures", [])
        assert any(item.get("code") == "SINGLE_MESSAGE_WRAP" for item in failures), failures

    print("PASS: over-wrapped single-message headline is rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
