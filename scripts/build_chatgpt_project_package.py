#!/usr/bin/env python3
"""Build the five-file ChatGPT Project distribution for mobile users."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "variants" / "chatgpt-project"
PACKAGE_ROOT = "slide-system-chatgpt-project"
CANONICAL_SPECS = (
    "00_MASTER.md",
    "10_CONTENT.md",
    "20_DESIGN.md",
    "30_LAYOUTS.md",
    "40_VISUALS.md",
    "50_OUTPUTS.md",
    "60_QA.md",
)
UPLOAD_FILES = (
    "01_PROJECT_RULES.md",
    "02_CANONICAL_SPEC.md",
    "03_DECK_TEMPLATE.html",
    "04_DECK_SCHEMA.json",
    "05_MOBILE_RUNTIME.md",
)
FONT_FACE = '''    @font-face {
      font-family: "Slide Noto Sans JP";
      src: url("data:font/ttf;base64,__FONT_DATA__") format("truetype");
      font-style: normal;
      font-weight: 100 900;
      font-display: block;
    }
'''


def sha256(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n").rstrip() + "\n", encoding="utf-8", newline="\n")


def canonical_bundle() -> tuple[str, list[dict[str, str]]]:
    sections = [
        "# Slide System Canonical Specification\n",
        "このファイルはリポジトリの00〜60正本を省略せず結合した配布用スナップショットです。",
        "競合時は`00_MASTER.md`に記載された優先順位を使用します。",
        "ChatGPT固有の実行方法は`01_PROJECT_RULES.md`と`05_MOBILE_RUNTIME.md`を参照してください。\n",
    ]
    sources: list[dict[str, str]] = []
    for filename in CANONICAL_SPECS:
        path = ROOT / filename
        if not path.is_file():
            raise FileNotFoundError(f"Canonical specification not found: {path}")
        data = path.read_bytes()
        text = data.decode("utf-8").replace("\r\n", "\n").rstrip()
        sections.extend((f"\n---\n\n## FILE: {filename}\n", text, ""))
        sources.append({"file": filename, "sha256": sha256(data)})
    return "\n".join(sections).rstrip() + "\n", sources


def project_template() -> str:
    source = ROOT / "skills" / "slide-system" / "assets" / "deck-template.html"
    template = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    if FONT_FACE not in template:
        raise ValueError("Expected bundled-font block was not found in deck-template.html")
    template = template.replace(FONT_FACE, "")
    template = template.replace(
        '--font: "Slide Noto Sans JP", "Noto Sans JP", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;',
        '--font: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;',
    )
    if "__FONT_DATA__" in template:
        raise ValueError("Font placeholder remains in ChatGPT Project template")
    return template.rstrip() + "\n"


def add_deterministic_file(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output: Path, version: str, *, replace: bool = False) -> dict[str, object]:
    output = output.resolve()
    if output.exists() and not replace:
        raise FileExistsError(f"Output already exists: {output}")
    if output.exists():
        if output.parent != (ROOT / "dist").resolve() or output.suffix.lower() != ".zip":
            raise ValueError(f"Refusing to replace unexpected output: {output}")
        output.unlink()

    canonical, canonical_sources = canonical_bundle()
    with tempfile.TemporaryDirectory(prefix="slide-system-chatgpt-project-") as temporary:
        staged = Path(temporary) / PACKAGE_ROOT
        upload = staged / "UPLOAD_TO_PROJECT"
        write_text(staged / "README_MOBILE.md", (SOURCE / "README_MOBILE.md").read_text(encoding="utf-8"))
        write_text(staged / "PROJECT_INSTRUCTIONS.txt", (SOURCE / "PROJECT_INSTRUCTIONS.txt").read_text(encoding="utf-8"))
        write_text(upload / "01_PROJECT_RULES.md", (SOURCE / "upload" / "01_PROJECT_RULES.md").read_text(encoding="utf-8"))
        write_text(upload / "02_CANONICAL_SPEC.md", canonical)
        write_text(upload / "03_DECK_TEMPLATE.html", project_template())
        schema = ROOT / "skills" / "slide-system" / "assets" / "deck-schema-example.json"
        write_text(upload / "04_DECK_SCHEMA.json", schema.read_text(encoding="utf-8"))
        write_text(upload / "05_MOBILE_RUNTIME.md", (SOURCE / "upload" / "05_MOBILE_RUNTIME.md").read_text(encoding="utf-8"))

        upload_manifest = []
        for filename in UPLOAD_FILES:
            path = upload / filename
            data = path.read_bytes()
            upload_manifest.append({"file": f"UPLOAD_TO_PROJECT/{filename}", "sha256": sha256(data), "size_bytes": len(data)})
        manifest = {
            "schema_version": "1.0",
            "package": "slide-system-chatgpt-project",
            "version": version,
            "target": ["ChatGPT Free", "ChatGPT Plus"],
            "target_devices": ["iPad", "iPhone"],
            "upload_file_count": len(upload_manifest),
            "upload_files": upload_manifest,
            "canonical_sources": canonical_sources,
        }
        write_text(staged / "PACKAGE_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w") as archive:
            for path in sorted(staged.rglob("*")):
                if path.is_file():
                    relative = Path(PACKAGE_ROOT) / path.relative_to(staged)
                    add_deterministic_file(archive, relative.as_posix(), path.read_bytes())

    return {
        "status": "PASS",
        "output": str(output),
        "version": version,
        "upload_file_count": len(UPLOAD_FILES),
        "size_bytes": output.stat().st_size,
        "sha256": sha256(output.read_bytes()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the ChatGPT Project package")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.version.strip(), replace=args.replace), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
