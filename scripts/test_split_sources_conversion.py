from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.designs import load_design_pack  # noqa: E402
from slide_system.legacy import convert_deck_to_legacy  # noqa: E402


def test_sources_pages_only_include_their_references() -> None:
    deck = {
        "metadata": {"title": "test", "date": "2026.8.12"},
        "context": {"purpose": "test", "audience": "test", "mode": "standalone"},
        "slides": [
            {
                "id": "s1",
                "role": "sources",
                "title": "出典A",
                "layout": {"family": "sources", "density": "medium"},
                "blocks": [],
                "visual": {"strategy": "none"},
                "source_refs": ["A"],
            },
            {
                "id": "s2",
                "role": "sources",
                "title": "出典B",
                "layout": {"family": "sources", "density": "medium"},
                "blocks": [],
                "visual": {"strategy": "none"},
                "source_refs": ["B"],
            },
        ],
        "sources": [
            {"id": "A", "title": "A", "publisher": "Pub", "url": "https://example.com/a", "accessed_at": "2026-08-12"},
            {"id": "B", "title": "B", "publisher": "Pub", "url": "https://example.com/b", "accessed_at": "2026-08-12"},
        ],
    }

    converted = convert_deck_to_legacy(deck, load_design_pack(ROOT, "warm_clean"))

    assert [source["id"] for source in converted["slides"][0]["sources"]] == ["A"]
    assert [source["id"] for source in converted["slides"][1]["sources"]] == ["B"]


if __name__ == "__main__":
    test_sources_pages_only_include_their_references()
    print("PASS: split sources conversion")
