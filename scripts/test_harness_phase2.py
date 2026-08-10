#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from slide_system.attempts import create_attempt  # noqa: E402
from slide_system.briefs import approve_brief  # noqa: E402
from slide_system.designs import load_design_pack, load_layout_registry  # noqa: E402
from slide_system.production import build_html, render_pdf  # noqa: E402
from slide_system.runs import create_run, find_run, regenerate_index  # noqa: E402
from slide_system.state import transition_run  # noqa: E402


def config() -> dict:
    return {
        "defaults": {
            "language": "ja",
            "mode": "interactive",
            "design_pack": "warm_clean",
            "output_profile": "html_pdf",
            "aspect_ratio": "16:9",
        },
        "runs": {"directory": "runs", "generate_index": True, "generate_thumbnails": True},
        "qa": {"require_human_approval": True},
        "cache": {"directory": ".cache"},
    }


def copy_runtime(project_root: Path) -> None:
    shutil.copytree(ROOT / "schemas", project_root / "schemas")
    shutil.copytree(ROOT / "designs", project_root / "designs")
    source = ROOT / "skills/slide-system"
    target = project_root / "skills/slide-system"
    (target / "scripts").mkdir(parents=True)
    (target / "assets/fonts").mkdir(parents=True)
    for name in ("build_deck.py", "render_deck.mjs"):
        shutil.copy2(source / "scripts" / name, target / "scripts" / name)
    shutil.copy2(source / "assets/deck-template.html", target / "assets/deck-template.html")
    shutil.copy2(source / "assets/fonts/NotoSansJP-Variable.ttf", target / "assets/fonts/NotoSansJP-Variable.ttf")


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        project_root = Path(temporary)
        copy_runtime(project_root)
        pack = load_design_pack(project_root, "warm_clean")
        assert pack.version == "1.0.0"
        registry = load_layout_registry(pack)
        assert {"cover", "comparison", "summary", "sources"}.issubset(registry)

        run = create_run(
            project_root,
            config(),
            title="問い合わせ対応の改善提案",
            summary="受付後の振り分けを見直す",
            adapter="codex",
        )
        run_id = run["run_id"]
        transition_run(
            project_root,
            config(),
            run_id,
            new_status="confirmation_pending",
            owner="test",
            last_action="制作条件を提示しました",
            next_action="内容を確認してください",
        )
        approved_at = datetime.now().astimezone().isoformat(timespec="seconds")
        brief = {
            "schema_version": "1.0",
            "run_id": run_id,
            "status": "approved",
            "purpose": "問い合わせ対応の改善方針を決める",
            "audience": "カスタマーサポート部門",
            "cover": {"title": "問い合わせ対応の改善提案", "date": "2026-08-10", "subtitle": None, "author": None, "organization": None},
            "outline": ["現状", "比較", "次の行動"],
            "output": {"profile": "html_pdf"},
            "approved_at": approved_at,
            "approval_message": "この内容で制作する",
        }
        brief_path = project_root / "approved-brief.json"
        brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        approve_brief(project_root, config(), run_id, brief_source=brief_path, owner="test")

        deck = {
            "schema_version": "1.0",
            "deck_id": "deck-phase2",
            "run_id": run_id,
            "attempt": 1,
            "metadata": {
                "title": "問い合わせ対応の改善提案",
                "subtitle": "現状・選択肢・次の行動",
                "date": "2026-08-10",
                "author": None,
                "organization": None,
                "language": "ja",
            },
            "context": {
                "purpose": "問い合わせ対応の改善方針を決める",
                "audience": "カスタマーサポート部門",
                "mode": "standalone",
                "core_message": "受付後の振り分けから改善する",
            },
            "narrative": {"opening": "課題", "development": "比較", "closing": "行動"},
            "slides": [
                {
                    "id": "slide-01",
                    "role": "cover",
                    "title": "問い合わせ対応の改善提案",
                    "subtitle": "現状・選択肢・次の行動",
                    "takeaway": None,
                    "layout": {"family": "cover", "variant": "standard", "density": "low"},
                    "blocks": [],
                    "visual": {"strategy": "decorative_shapes", "eyebrow": "SERVICE × IMPROVEMENT"},
                    "source_refs": [],
                },
                {
                    "id": "slide-02",
                    "role": "content",
                    "title": "3つの改善案を比較します",
                    "subtitle": None,
                    "takeaway": "入力、振り分け、回答の順で見直します",
                    "layout": {"family": "comparison", "variant": "three_column", "density": "medium"},
                    "blocks": [
                        {
                            "id": "block-01",
                            "type": "comparison",
                            "items": [
                                {"heading": "入力項目", "body": "不足情報を減らします。"},
                                {"heading": "自動振り分け", "body": "適切な担当へ届けます。", "tone": "mint"},
                                {"heading": "回答テンプレート", "body": "品質と速度を揃えます。", "tone": "neutral"}
                            ],
                            "source_refs": []
                        }
                    ],
                    "visual": {"strategy": "comparison_graphic"},
                    "source_refs": [],
                },
                {
                    "id": "slide-03",
                    "role": "summary",
                    "title": "今週は試行条件を決めます",
                    "subtitle": None,
                    "takeaway": "まず1チームで検証する",
                    "layout": {"family": "summary", "variant": "actions", "density": "medium"},
                    "blocks": [
                        {
                            "id": "block-02",
                            "type": "bullets",
                            "items": ["対象分類を3つ選ぶ", "判断指標を決める", "責任者と確認日を決める"],
                            "source_refs": []
                        }
                    ],
                    "visual": {"strategy": "explain"},
                    "source_refs": [],
                }
            ],
            "sources": [],
        }
        deck_path = project_root / "deck.json"
        deck_path.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
        create_attempt(project_root, config(), run_id, owner="test", deck_source=deck_path, reason="Phase 2初稿")

        built = build_html(project_root, config(), run_id, owner="test")
        assert built["html"].is_file()
        assert built["report"].is_file()
        static_report = json.loads(built["report"].read_text(encoding="utf-8"))
        assert static_report["status"] == "PASS"
        html = built["html"].read_text(encoding="utf-8")
        assert "問い合わせ対応の改善提案" in html
        assert "Slide Noto Sans JP" in html

        rendered = render_pdf(project_root, config(), run_id, owner="test", pdf_approval="PDFもお願いします")
        assert rendered["pdf"].is_file()
        assert rendered["pdf"].stat().st_size > 4000
        qa_report = json.loads(rendered["report"].read_text(encoding="utf-8"))
        assert qa_report["result"] == "PASS", qa_report
        assert qa_report["gates"] == {"static": "PASS", "visual": "PASS", "pdf_parity": "PASS", "theme": "PASS"}
        visual_report = json.loads((Path(rendered["report"]).parent / "visual-qa-legacy.json").read_text(encoding="utf-8"))
        assert visual_report["slide_count"] == 3
        assert (rendered["renders"] / "contact-sheet.png").is_file()

        completed_run = find_run(project_root, config(), run_id)
        assert completed_run["status"] == "ready_for_review"
        assert completed_run["quality"]["qa_result"] == "PASS"
        assert completed_run["design"]["version"] == "1.0.0"
        lock = json.loads((project_root / "runs" / run_id / "run.lock.json").read_text(encoding="utf-8"))
        assert lock["checksums"]["design_pack"].startswith("sha256:")

        entries = regenerate_index(project_root, config())
        current = next(item for item in entries if item["run_id"] == run_id)
        assert current["html"].endswith("/attempts/001/deck.html")
        assert current["pdf"].endswith("/attempts/001/deck.pdf")
        assert current["thumbnail"].endswith("/attempts/001/renders/slide-01.png")
        contact_sheet_copy = os.environ.get("SLIDE_SYSTEM_PHASE2_CONTACT_SHEET")
        if contact_sheet_copy:
            destination = Path(contact_sheet_copy)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(rendered["renders"] / "contact-sheet.png", destination)

    print("PASS: harness Phase 2 design pack, HTML build, visual QA, and PDF render")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
