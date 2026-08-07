#!/usr/bin/env python3
"""Audit the paid package against the canonical 00-60 specifications."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SPECS = (
    "00_MASTER.md",
    "10_CONTENT.md",
    "20_DESIGN.md",
    "30_LAYOUTS.md",
    "40_VISUALS.md",
    "50_OUTPUTS.md",
    "60_QA.md",
)
REQUIRED_FILES = {
    "SKILL.md",
    "agents/openai.yaml",
    "assets/deck-schema-example.json",
    "assets/deck-template.html",
    "assets/fonts/NotoSansJP-Variable.ttf",
    "references/html-pdf.md",
    "references/pptx.md",
    "scripts/build_deck.py",
    "scripts/recover_deck.py",
    "scripts/render_deck.mjs",
    "scripts/export_pdf.mjs",
}
REQUIRED_SKILL_TEXT = (
    "Treat the bundled 00-60 specifications as the canonical contract",
    "Non-negotiable approval gate",
    "Do not mix a missing-information question with production approval",
    "Do not use the staged `export_pdf.mjs` path",
    "every HTML slide at readable size",
    "every PDF page after conversion",
    "Repeat without a fixed iteration limit",
    "every applicable canonical `MUST` is `PASS` or justified `N/A`",
)
FORBIDDEN_PAID_TEXT = (
    "one grouped search with up to four precise queries",
    "Limit external visual search and download to at most three",
    "HTML is the first deliverable. PDF is created in a later turn",
    'delivery_profile: "staged"',
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    zip_path = args.zip_path.resolve()

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names if "/" in name}
        assert roots == {"slide-system-paid"}, f"Unexpected package root: {sorted(roots)}"
        prefix = "slide-system-paid/"
        relative = {name[len(prefix):] for name in names if name.startswith(prefix)}
        missing = sorted(REQUIRED_FILES - relative)
        assert not missing, f"Missing paid package files: {missing}"

        for filename in CANONICAL_SPECS:
            packaged_name = f"{prefix}references/{filename}"
            assert packaged_name in names, f"Missing canonical specification: {filename}"
            packaged = archive.read(packaged_name)
            canonical = (ROOT / filename).read_bytes()
            assert packaged == canonical, f"Canonical specification drifted: {filename}"

        skill = archive.read(f"{prefix}SKILL.md").decode("utf-8")
        missing_contract = [text for text in REQUIRED_SKILL_TEXT if text not in skill]
        assert not missing_contract, f"Missing paid workflow contract: {missing_contract}"
        leaked_limits = [text for text in FORBIDDEN_PAID_TEXT if text in skill]
        assert not leaked_limits, f"Free-plan limits leaked into paid skill: {leaked_limits}"

    print(f"PASS: paid package canonical contract ({zip_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
