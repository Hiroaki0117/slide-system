#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.designs import load_design_pack  # noqa: E402
from slide_system.legacy import convert_deck_to_legacy  # noqa: E402


def main() -> None:
    deck = {
        "metadata": {"title": "安全計画", "subtitle": None, "date": "2026-08-10", "author": None, "organization": None},
        "context": {
            "purpose": "安全に行動する",
            "audience": "本人",
            "mode": "standalone",
            "high_stakes": True,
            "dated_roadmap": True,
            "timeline": {"current_date": "2026-08-10", "target_date": "2026-11-01", "duration_text": "残り83日", "slide": 2},
            "safety": {"current_condition": "確認済み", "limitations": ["制限"], "stop_conditions": ["中止"]},
            "claim_evidence": [{"claim": "暫定", "visible_text": "暫定", "slide": 2, "basis_type": "source", "source_ids": ["S1"], "support": "根拠", "evidence_design": "guideline", "claim_strength": "recommendation"}],
        },
        "slides": [
            {"id": "s1", "role": "cover", "title": "安全計画", "subtitle": None, "layout": {"family": "cover", "density": "low"}, "blocks": [], "visual": {}, "source_refs": []},
            {"id": "s2", "role": "content", "title": "暫定", "takeaway": "残り83日", "layout": {"family": "table", "density": "medium"}, "blocks": [{"id": "b1", "type": "table", "headers": ["項目"], "rows": [["暫定"]]}], "visual": {"repeat_reason": "週別情報を同じ文法で比較するため"}, "source_refs": ["S1"]},
        ],
        "sources": [{"id": "S1", "title": "資料", "publisher": "発行元", "url": "https://example.com/source", "accessed_at": "2026-08-10", "source_class": "official"}],
    }
    converted = convert_deck_to_legacy(deck, load_design_pack(ROOT, "warm_clean"))
    assert converted["dated_roadmap"] is True
    assert converted["timeline"]["duration_text"] == "残り83日"
    assert converted["claim_evidence"][0]["source_ids"] == ["S1"]
    assert converted["slides"][1]["layout_repeat_reason"] == "週別情報を同じ文法で比較するため"
    print("PASS: high-stakes evidence, dated roadmap, and repeat rationale survive conversion")


if __name__ == "__main__":
    main()
