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
    confirmed_conditions = ["現在、脛の内側に軽い違和感がある"]
    confirmed_conditions.extend(
        item["confirmation_quote"]
        for item in brief.get("sessions", [])
        if item.get("current_basis_type") == "user_confirmed" and item.get("confirmation_quote")
    )
    state_path.write_text(
        json.dumps(
            {
                "phase": "approved",
                "delivery_profile": "staged",
                "approval": {"status": "approved", "user_reply": "この内容で制作する"},
                "confirmed_conditions": confirmed_conditions,
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
        assert result["must_return_html"] is True and result["slide_count"] == 13
        assert len(result["user_review_points"]) == 3
        assert report["quality_gate"] == "UNCHANGED_STRICT_VALIDATOR"
        assert report["issues"] == []
        assert report["user_review_points"] == result["user_review_points"]
        assert "検証未完了ドラフト" not in html
        assert "slide-deck-data" in html and "__DRAFT_BANNER__" not in html
        assert ">PDF保存</button>" in html and "PDF保存不可" not in html
        assert '<div class="stat-value">1:51:19</div>' in html
        assert '<div class="stat-label">現在｜ハーフ実績</div>' in html
        assert "提案｜変更" in html and "進め方｜" in html and "理由｜" in html
        assert "SESSION_OVERVIEW_DENSITY" not in json.dumps(report, ensure_ascii=False)

        dense_deck = json.loads(Path(result["deck"]).read_text(encoding="utf-8"))
        assert dense_deck["slides"][6]["layout"] == "comparison"
        assert dense_deck["slides"][6]["title"] == "週3回は目的と強度を分ける"
        assert [slide["title"] for slide in dense_deck["slides"][7:10]] == [item["session_type"] for item in valid["sessions"]]
        assert [item["slide"] for item in dense_deck["safety"]["session_guidance"]] == [8, 9, 10]
        assert dense_deck["slides"][10]["content_role"] == "event_strategy"
        assert dense_deck["slides"][-1]["layout"] == "sources_appendix"

        compact_sessions = json.loads(json.dumps(valid, ensure_ascii=False))
        for item in compact_sessions["sessions"]:
            item["current_method"] = "現行メニュー"
            item["proposed_method"] = "短い提案"
            item["progression"] = "段階調整"
            item["purpose"] = "役割確認"
            item["decision_reason"] = "負荷管理"
            item["adjustment_condition"] = "疲労時短縮"
        result, html, report = run_builder(work, compact_sessions, "compact-sessions")
        assert result["status"] == "PASS" and result["slide_count"] == 10
        compact_deck = json.loads(Path(result["deck"]).read_text(encoding="utf-8"))
        assert compact_deck["slides"][6]["layout"] == "table"
        assert compact_deck["slides"][6]["headers"] == ["種類", "現状", "提案", "目的・理由・調整"]

        compact = json.loads(json.dumps(compact_sessions, ensure_ascii=False))
        compact["phases"] = compact["phases"][1:]
        result, html, report = run_builder(work, compact, "four-phases")
        assert result["status"] == "PASS" and result["slide_count"] == 9
        assert "｜前半" not in html and "｜後半" not in html

        repeated = json.loads(json.dumps(valid, ensure_ascii=False))
        repeated["sessions"][0]["proposed_method"] = repeated["sessions"][0]["current_method"]
        result, html, report = run_builder(work, repeated, "repeated-current")
        assert result["status"] == "DRAFT" and result["complete"] is False
        assert "SESSION_PROPOSAL_REPEATS_CURRENT" in {item["code"] for item in report["issues"]}
        assert "検証未完了ドラフト" in html and "PDF保存不可" in html

        maintained = json.loads(json.dumps(valid, ensure_ascii=False))
        maintained["sessions"][0]["recommendation_decision"] = "maintain"
        maintained["sessions"][0]["proposed_method"] = maintained["sessions"][0]["current_method"]
        maintained["sessions"][0]["decision_reason"] = "現在の負荷を増やさず回復を優先するため"
        result, html, report = run_builder(work, maintained, "maintained-current")
        assert result["status"] == "PASS" and result["complete"] is True
        assert "提案｜維持" in html

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
