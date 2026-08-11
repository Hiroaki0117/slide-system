#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=os.environ.copy(), check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run every release gate")
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "dist" / "release-manifest.json").read_text(encoding="utf-8"))
    for item in manifest["skills"].values():
        path = ROOT / "dist" / item["file"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise SystemExit(f"release manifest mismatch: {path}")
    tests = [
        "test_harness_phase0.py", "test_harness_phase1.py", "test_harness_phase2.py", "test_harness_phase3.py",
        "test_harness_phase4.py", "test_harness_phase5.py", "test_harness_phase6.py", "test_harness_phase7.py",
        "test_build_deck_validation.py", "test_artifact_recovery.py", "test_fast_pdf_export.py", "test_free_turn_gate_contract.py",
        "test_cross_platform_mobile_case.py",
    ]
    for name in tests:
        run([sys.executable, str(ROOT / "scripts" / name)])
    run([sys.executable, str(ROOT / "scripts" / "test_free_package_generic.py"), str(ROOT / "dist" / manifest["skills"]["free"]["file"])])
    run([sys.executable, str(ROOT / "scripts" / "test_paid_package_contract.py"), str(ROOT / "dist" / manifest["skills"]["paid"]["file"])])
    run(["node", str(ROOT / "bin" / "slide-system.mjs"), "--project-root", str(ROOT), "doctor"])
    if args.require_clean:
        completed = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True)
        if completed.stdout.strip():
            raise SystemExit("Git working tree is not clean")
    print("PASS: Slide System release checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
