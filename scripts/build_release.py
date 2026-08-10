#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_skill_package import package


ROOT = Path(__file__).resolve().parents[1]
FREE_VERSION = "0.2.14"
PAID_VERSION = "0.1.1"


def sha256(path: Path) -> str:
    import hashlib

    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude skills and release manifest builder")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    dist = ROOT / "dist"
    free = dist / f"slide-system-free-v{FREE_VERSION}.zip"
    paid = dist / f"slide-system-paid-v{PAID_VERSION}.zip"
    package(ROOT / "skills/slide-system", ROOT / "variants/slide-system-free", free, "slide-system-free", args.replace)
    package(ROOT / "skills/slide-system", ROOT / "variants/slide-system-paid", paid, "slide-system-paid", args.replace, ROOT)
    manifest = {
        "schema_version": "1.0",
        "harness_version": "0.9.0",
        "skills": {
            "free": {"version": FREE_VERSION, "file": free.name, "sha256": sha256(free)},
            "paid": {"version": PAID_VERSION, "file": paid.name, "sha256": sha256(paid)},
        },
    }
    (dist / "release-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
