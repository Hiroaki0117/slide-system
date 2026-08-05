#!/usr/bin/env python3
"""End-to-end regression check for embedded deck recovery."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_valid_deck() -> dict:
    module_path = ROOT / "scripts" / "test_build_deck_validation.py"
    spec = importlib.util.spec_from_file_location("slide_system_validation_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.valid_deck()


def main() -> int:
    deck = load_valid_deck()
    deck["deck_title"] = "復元テスト </script> &quot;"
    with tempfile.TemporaryDirectory(prefix="slide-recovery-test-") as temporary:
        work = Path(temporary)
        source = work / "deck.json"
        state = work / "work-state.json"
        output = work / "deck.html"
        report = work / "static-qa.json"
        recovered = work / "recovered.json"
        source.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
        state.write_text(
            json.dumps(
                {
                    "phase": "approved",
                    "delivery_profile": "staged",
                    "approval": {"status": "approved", "user_reply": "その内容でお願いします"},
                    "confirmed_conditions": ["質練習は確認済み範囲で行っています"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "skills" / "slide-system" / "scripts" / "build_deck.py"),
                "--input", str(source),
                "--work-state", str(state),
                "--template", str(ROOT / "skills" / "slide-system" / "assets" / "deck-template.html"),
                "--output", str(output),
                "--report", str(report),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "skills" / "slide-system" / "scripts" / "recover_deck.py"),
                "--html", str(output),
                "--output", str(recovered),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(recovered.read_text(encoding="utf-8")) == deck
        assert "__DECK_DATA__" not in output.read_text(encoding="utf-8")
    print("PASS: embedded HTML deck recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
