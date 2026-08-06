#!/usr/bin/env python3
"""Integration check for the free-plan HTML-to-PDF fast path."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from test_build_deck_validation import valid_deck


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "slide-system"


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}\n{completed.stderr}")


def run_failure(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, encoding="utf-8")
    assert completed.returncode != 0, f"Command unexpectedly passed: {' '.join(command)}"
    return completed


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="slide-system-fast-pdf-") as temporary:
        work = Path(temporary)
        deck_path = work / "deck.json"
        state_path = work / "work-state.json"
        html_path = work / "deck.html"
        pdf_path = work / "deck.pdf"
        static_report = work / "static-qa.json"
        pdf_report = work / "pdf-qa.json"

        deck_path.write_text(json.dumps(valid_deck(), ensure_ascii=False, indent=2), encoding="utf-8")
        state = {
            "phase": "approved",
            "delivery_profile": "staged",
            "approval": {"status": "approved", "user_reply": "その内容でお願いします"},
            "confirmed_conditions": ["質練習は確認済み範囲で行っています"],
        }
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        run([
            os.environ.get("SLIDE_SYSTEM_PYTHON", "python"),
            str(SKILL / "scripts" / "build_deck.py"),
            "--input", str(deck_path),
            "--work-state", str(state_path),
            "--template", str(SKILL / "assets" / "deck-template.html"),
            "--output", str(html_path),
            "--report", str(static_report),
        ])

        state["phase"] = "pdf_requested"
        state["pdf_request"] = {"user_reply": "PDFもお願いします"}
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        env = os.environ.copy()
        run([
            os.environ.get("SLIDE_SYSTEM_NODE", "node"),
            str(SKILL / "scripts" / "export_pdf.mjs"),
            "--html", str(html_path),
            "--pdf", str(pdf_path),
            "--report", str(pdf_report),
            "--work-state", str(state_path),
        ], env=env)

        report = json.loads(pdf_report.read_text(encoding="utf-8"))
        assert report["status"] == "PASS", report
        assert report["slide_count"] == report["pdf_pages"], report
        assert report["font"]["loaded"] is True, report
        assert report["controls_hidden"] is True, report
        assert report["aspect_16_9"] is True, report
        assert pdf_path.stat().st_size > 10_000, pdf_path.stat().st_size

        draft_html = work / "draft.html"
        draft_pdf = work / "draft.pdf"
        draft_report = work / "draft-pdf-qa.json"
        draft_html.write_text(
            html_path.read_text(encoding="utf-8").replace(
                "<body>", '<body><div class="draft-banner">検証未完了ドラフト</div>', 1
            ),
            encoding="utf-8",
        )
        failed = run_failure([
            os.environ.get("SLIDE_SYSTEM_NODE", "node"),
            str(SKILL / "scripts" / "export_pdf.mjs"),
            "--html", str(draft_html),
            "--pdf", str(draft_pdf),
            "--report", str(draft_report),
            "--work-state", str(state_path),
        ], env=env)
        assert "DRAFT_NOT_APPROVED" in failed.stderr
        assert not draft_pdf.exists()

    print("PASS: fast PDF export integration check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
