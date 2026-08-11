#!/usr/bin/env python3
"""Audit the mobile ChatGPT Project package and its canonical snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = "slide-system-chatgpt-project/"
CANONICAL_SPECS = (
    "00_MASTER.md",
    "10_CONTENT.md",
    "20_DESIGN.md",
    "30_LAYOUTS.md",
    "40_VISUALS.md",
    "50_OUTPUTS.md",
    "60_QA.md",
)
UPLOAD_FILES = {
    "UPLOAD_TO_PROJECT/01_PROJECT_RULES.md",
    "UPLOAD_TO_PROJECT/02_CANONICAL_SPEC.md",
    "UPLOAD_TO_PROJECT/03_DECK_TEMPLATE.html",
    "UPLOAD_TO_PROJECT/04_DECK_SCHEMA.json",
    "UPLOAD_TO_PROJECT/05_MOBILE_RUNTIME.md",
}
ROOT_FILES = {"README_MOBILE.md", "PROJECT_INSTRUCTIONS.txt", "PACKAGE_MANIFEST.json"}


def sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    zip_path = args.zip_path.resolve()

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        roots = {name.split("/", 1)[0] for name in names if "/" in name}
        assert roots == {PACKAGE_ROOT.rstrip("/")}, roots
        relative = {name[len(PACKAGE_ROOT):] for name in names if name.startswith(PACKAGE_ROOT)}
        assert relative == ROOT_FILES | UPLOAD_FILES, sorted(relative)

        manifest = json.loads(archive.read(f"{PACKAGE_ROOT}PACKAGE_MANIFEST.json"))
        assert manifest["package"] == "slide-system-chatgpt-project"
        assert manifest["target"] == ["ChatGPT Free", "ChatGPT Plus"]
        assert manifest["target_devices"] == ["iPad", "iPhone"]
        assert manifest["upload_file_count"] == 5
        assert {item["file"] for item in manifest["upload_files"]} == UPLOAD_FILES
        for item in manifest["upload_files"]:
            data = archive.read(f"{PACKAGE_ROOT}{item['file']}")
            assert item["sha256"] == sha256(data), item["file"]
            assert item["size_bytes"] == len(data), item["file"]

        canonical = archive.read(f"{PACKAGE_ROOT}UPLOAD_TO_PROJECT/02_CANONICAL_SPEC.md").decode("utf-8")
        canonical_manifest = {item["file"]: item["sha256"] for item in manifest["canonical_sources"]}
        assert set(canonical_manifest) == set(CANONICAL_SPECS)
        for filename in CANONICAL_SPECS:
            source = (ROOT / filename).read_bytes()
            assert canonical_manifest[filename] == sha256(source), filename
            assert source.decode("utf-8").replace("\r\n", "\n").rstrip() in canonical, filename

        template = archive.read(f"{PACKAGE_ROOT}UPLOAD_TO_PROJECT/03_DECK_TEMPLATE.html").decode("utf-8")
        assert "__FONT_DATA__" not in template
        assert "Slide Noto Sans JP" not in template
        for marker in ("__DECK_TITLE__", "__SLIDES__", "__DECK_DATA__", "__DRAFT_BANNER__", "__PRINT_DISABLED__", "__PRINT_LABEL__"):
            assert marker in template, marker
        assert '"Hiragino Sans"' in template

        project_instructions = archive.read(f"{PACKAGE_ROOT}PROJECT_INSTRUCTIONS.txt").decode("utf-8")
        for required in ("01_PROJECT_RULES.md", "明示的な承認", "HTML下書き", "PDFはHTML確認後"):
            assert required in project_instructions, required
        mobile = archive.read(f"{PACKAGE_ROOT}README_MOBILE.md").decode("utf-8")
        assert "iPad" in mobile and "iPhone" in mobile
        assert "5ファイル" in mobile

    with tempfile.TemporaryDirectory(prefix="slide-system-chatgpt-repro-") as temporary:
        first = Path(temporary) / "first.zip"
        second = Path(temporary) / "second.zip"
        command = [
            os.environ.get("SLIDE_SYSTEM_PYTHON", "python"),
            str(ROOT / "scripts" / "build_chatgpt_project_package.py"),
            "--version", manifest["version"],
        ]
        subprocess.run(command + ["--output", str(first)], cwd=ROOT, check=True, capture_output=True)
        subprocess.run(command + ["--output", str(second)], cwd=ROOT, check=True, capture_output=True)
        assert first.read_bytes() == second.read_bytes(), "ChatGPT package build is not deterministic"
        assert first.read_bytes() == zip_path.read_bytes(), "Distributed ZIP differs from deterministic build"

    print(f"PASS: ChatGPT Project package contract ({zip_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

