#!/usr/bin/env python3
"""Build a complete skill ZIP by overlaying a small variant on a shared base."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


EXCLUDED_PARTS = {"__pycache__", ".git"}
CANONICAL_SPEC_FILES = (
    "00_MASTER.md",
    "10_CONTENT.md",
    "20_DESIGN.md",
    "30_LAYOUTS.md",
    "40_VISUALS.md",
    "50_OUTPUTS.md",
    "60_QA.md",
)


def copy_overlay(source: Path, destination: Path) -> None:
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            copy_overlay(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def package(
    base: Path,
    variant: Path,
    output: Path,
    root_name: str,
    replace: bool = False,
    canonical_spec_root: Path | None = None,
) -> dict[str, object]:
    if output.exists() and not replace:
        raise FileExistsError(f"Output already exists: {output}")
    if output.exists():
        if output.suffix.lower() != ".zip" or output.parent.name != "dist":
            raise ValueError(f"Refusing to replace unexpected output: {output}")
        output.unlink()
    if not (base / "SKILL.md").is_file():
        raise FileNotFoundError(f"Base SKILL.md not found: {base}")
    if not (variant / "SKILL.md").is_file():
        raise FileNotFoundError(f"Variant SKILL.md not found: {variant}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="slide-skill-package-") as temporary:
        staged = Path(temporary) / root_name
        shutil.copytree(base, staged)
        copy_overlay(variant, staged)
        spec_count = 0
        if canonical_spec_root is not None:
            reference_dir = staged / "references"
            reference_dir.mkdir(parents=True, exist_ok=True)
            for filename in CANONICAL_SPEC_FILES:
                source = canonical_spec_root / filename
                if not source.is_file():
                    raise FileNotFoundError(f"Canonical specification not found: {source}")
                shutil.copy2(source, reference_dir / filename)
                spec_count += 1

        files = [
            path
            for path in sorted(staged.rglob("*"))
            if path.is_file()
            and not any(part in EXCLUDED_PARTS for part in path.parts)
            and path.suffix != ".pyc"
        ]
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                archive.write(path, Path(root_name) / path.relative_to(staged))

    return {
        "status": "PASS",
        "output": str(output),
        "root": root_name,
        "file_count": len(files),
        "canonical_spec_count": spec_count,
        "size_bytes": output.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--variant", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root-name", required=True)
    parser.add_argument("--canonical-spec-root", type=Path)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    result = package(
        args.base.resolve(),
        args.variant.resolve(),
        args.output.resolve(),
        args.root_name.strip(),
        args.replace,
        args.canonical_spec_root.resolve() if args.canonical_spec_root else None,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
