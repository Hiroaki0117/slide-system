#!/usr/bin/env python3
"""Recover the editable deck JSON embedded in a slide-system HTML artifact."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DECK_DATA_RE = re.compile(
    r'<script\s+type=["\']application/json["\']\s+id=["\']slide-deck-data["\']\s*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def recover(source: Path) -> dict:
    match = DECK_DATA_RE.search(source.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("Embedded slide-deck-data was not found; inspect and reconstruct this older HTML before editing")
    data = json.loads(match.group(1))
    if not isinstance(data, dict) or not isinstance(data.get("slides"), list):
        raise ValueError("Embedded slide-deck-data is not a valid deck model")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = Path(args.html).resolve()
    output = Path(args.output).resolve()
    try:
        deck = recover(source)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Recovery failed: {exc}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "deck": str(output), "slide_count": len(deck["slides"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
