#!/usr/bin/env python3
"""Regression check for the free-plan no-tool confirmation gate."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "variants" / "slide-system-free" / "SKILL.md"


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    required = [
        "## Mandatory turn gate — highest priority",
        "Do not call any tool",
        "The next visible assistant response after a blocking answer",
        "Any intervening tool call is a workflow failure",
        "Do not read bundled references before production approval",
        "Allow at most one official-fact lookup",
        "Do not search medical treatment, training methods, tapering, nutrition, formulas",
        "### Stage A tool budget",
        "at most one grouped web-search operation",
        "at most one grouped source-opening operation",
        "Do not research race-prediction formulas",
        "Save the HTML before any optional work",
        "assets/free-roadmap-brief-example.json",
        "scripts/build_free_roadmap.py",
        "Treat the script as an opaque executable",
        "The compact builder must create HTML whether its report says `PASS` or `DRAFT`",
        "Do not inspect builder or validator source code",
        "user_review_points",
        "do not automatically rewrite those content decisions",
        "DRAFT_NOT_APPROVED",
        "keep the lead to 120 characters or fewer",
        "Slide count is the result of fitting one primary message per slide",
        "current_label",
        "the three-row cell total exceeds 180",
    ]
    missing = [item for item in required if item not in text]
    assert not missing, f"Missing free-plan turn-gate contract: {missing}"
    assert text.index("## Mandatory turn gate — highest priority") < text.index("## Free-plan defaults")
    assert text.index("## Mandatory turn gate — highest priority") < text.index("## Workflow")
    print("PASS: free-plan no-tool turn gate contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
