#!/usr/bin/env python3
"""Audit that the current free distribution is generic and complete."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {".md", ".json", ".py", ".mjs", ".html", ".yaml", ".yml"}
FORBIDDEN = re.compile(
    r"\bmarathon\b|\brace\b|\btaper\b|\blong[ -]?run\b|pace prediction|"
    r"マラソン|レース|ロング走|ペース走|脛|weekly_long|session_guidance|"
    r"phase_guidance|free-roadmap|build_free_roadmap",
    re.IGNORECASE,
)
REQUIRED = {
    "SKILL.md",
    "assets/deck-schema-example.json",
    "assets/deck-template.html",
    "assets/fonts/NotoSansJP-Variable.ttf",
    "references/content.md",
    "references/html-pdf.md",
    "references/source-safety.md",
    "scripts/build_deck.py",
    "scripts/export_pdf.mjs",
    "scripts/recover_deck.py",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    path = args.zip_path.resolve()

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names if "/" in name}
        assert len(roots) == 1, f"Expected one root folder, got {sorted(roots)}"
        root = next(iter(roots))
        relative = {name[len(root) + 1:] for name in names if name.startswith(root + "/")}
        missing = sorted(REQUIRED - relative)
        assert not missing, f"Missing package files: {missing}"

        leaked: list[str] = []
        for name in names:
            if Path(name).suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = archive.read(name).decode("utf-8")
            if FORBIDDEN.search(text):
                leaked.append(name)
        assert not leaked, f"Topic-specific production rules leaked into package: {leaked}"

    print(f"PASS: generic package audit ({path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
