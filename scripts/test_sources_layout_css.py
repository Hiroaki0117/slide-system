from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "skills" / "slide-system" / "assets" / "deck-template.html"


def test_sources_layout_has_room_for_long_ids_and_urls() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "grid-template-columns: 110px minmax(0,1fr)" in text
    assert ".source-meta { min-width: 0;" in text
    assert "overflow-wrap: anywhere;" in text


if __name__ == "__main__":
    test_sources_layout_has_room_for_long_ids_and_urls()
    print("PASS: sources layout CSS")
