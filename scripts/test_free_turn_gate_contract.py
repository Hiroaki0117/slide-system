#!/usr/bin/env python3
"""Regression check for the free-plan staged workflow contract."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "variants" / "slide-system-free" / "SKILL.md"


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    required = [
        "## Non-negotiable turn gate",
        "use no tools",
        "An answer to a question",
        "Before approval, do not open bundled references",
        "## Resource budget",
        "one grouped search with up to four precise queries",
        "Save HTML before optional work",
        "assets/deck-schema-example.json",
        "scripts/build_deck.py",
        "Do not inspect builder source code",
        "story order and key conclusions",
        "current state and the proposed decision",
        "material revision",
        "cross-axis table",
        "Name a table or diagram for its actual scope",
        "Do not embed rules for a single sample domain",
        "Do not hardcode domain prescriptions into the skill",
        "source_requirement: \"standard\"",
        "claim-level",
        "layout_repeat_reason",
        "at most three necessary assets",
        "HTML is the first deliverable",
        "PDF is created in a later turn",
    ]
    missing = [item for item in required if item not in text]
    assert not missing, f"Missing free-plan contract: {missing}"
    assert text.index("## Non-negotiable turn gate") < text.index("## Defaults")
    assert text.index("## Non-negotiable turn gate") < text.index("## Workflow")

    forbidden = [
        "marathon", "race", "taper", "long run", "pace prediction",
        "マラソン", "レース", "ロング走", "ペース走", "脛",
        "free-roadmap-brief-example.json", "build_free_roadmap.py",
    ]
    leaked = [item for item in forbidden if item.lower() in text.lower()]
    assert not leaked, f"Domain-specific production rules leaked into free skill: {leaked}"

    print("PASS: generic free-plan staged workflow contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
