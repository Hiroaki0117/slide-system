from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "src" / "slide_system" / "attempts.py"


def test_empty_orphan_steps_directory_is_recoverable() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert 'existing_items[0].name == "steps"' in text
    assert '(attempt_dir / "steps").mkdir(exist_ok=True)' in text


if __name__ == "__main__":
    test_empty_orphan_steps_directory_is_recoverable()
    print("PASS: orphan attempt recovery")
