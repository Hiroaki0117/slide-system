#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.bundles import BundleError, export_run_bundle, import_result_bundle  # noqa: E402
from slide_system.runs import create_run, find_run  # noqa: E402
from slide_system.state import transition_run  # noqa: E402


def config() -> dict:
    return {"defaults": {"language": "ja", "mode": "interactive", "design_pack": "warm_clean", "output_profile": "html_pdf", "aspect_ratio": "16:9"}, "runs": {"directory": "runs", "generate_index": True}, "qa": {"require_human_approval": True}, "cache": {"directory": ".cache"}}


def deck(run_id: str) -> dict:
    return {"schema_version": "1.0", "deck_id": "web-result", "run_id": run_id, "attempt": 99, "metadata": {"title": "研修資料", "subtitle": None, "date": "2026-08-10", "author": None, "organization": None, "language": "ja"}, "context": {"purpose": "研修", "audience": "新人", "mode": "training", "core_message": "基本を知る"}, "slides": [{"id": "slide-01", "role": "cover", "title": "研修資料", "subtitle": None, "takeaway": None, "layout": {"family": "cover", "variant": None, "density": "low"}, "blocks": [], "visual": {}, "source_refs": []}], "sources": []}


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="slide-system-phase7-") as temporary:
        root = Path(temporary); shutil.copytree(ROOT / "schemas", root / "schemas")
        request = root / "request.md"; request.write_text("研修資料を作ってください", encoding="utf-8")
        run = create_run(root, config(), title="新人研修", summary="Bundleテスト", tags=["研修"], adapter="claude-web", request_source=request); run_id = run["run_id"]
        transition_run(root, config(), run_id, new_status="approved", owner="test", last_action="承認", next_action="制作")
        export_path = root / "out" / "run-bundle.zip"; export_run_bundle(root, config(), run_id, output=export_path)
        with zipfile.ZipFile(export_path) as archive:
            assert {"bundle.json", "request.md", "BUNDLE_INSTRUCTIONS.md"}.issubset(archive.namelist())
        malicious = root / "malicious.zip"
        with zipfile.ZipFile(malicious, "w") as archive:
            archive.writestr("../outside.txt", "bad"); archive.writestr("bundle.json", "{}"); archive.writestr("deck.json", "{}")
        try:
            import_result_bundle(root, config(), run_id, bundle_path=malicious, owner="test")
            raise AssertionError("path traversal bundle was accepted")
        except BundleError:
            pass
        result_path = root / "result.zip"
        manifest = {"schema_version": "1.0", "bundle_type": "result_bundle", "bundle_id": "result_001", "run_id": run_id, "created_at": "2026-08-10T12:00:00+09:00", "source_bundle_id": f"{run_id}_export", "files": ["bundle.json", "deck.json", "deck.html", "RESULT_NOTES.md"]}
        with zipfile.ZipFile(result_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("bundle.json", json.dumps(manifest, ensure_ascii=False)); archive.writestr("deck.json", json.dumps(deck(run_id), ensure_ascii=False)); archive.writestr("deck.html", "<html>untrusted preview</html>"); archive.writestr("RESULT_NOTES.md", "Claude Web result")
        imported = import_result_bundle(root, config(), run_id, bundle_path=result_path, owner="test")
        assert imported["attempt"] == 1
        run_dir = Path(find_run(root, config(), run_id)["_run_dir"]); attempt_dir = run_dir / "attempts" / "001"
        normalized = json.loads((attempt_dir / "deck.json").read_text(encoding="utf-8")); assert normalized["attempt"] == 1
        assert not (attempt_dir / "deck.html").exists(); assert (attempt_dir / "imported" / "deck.html").is_file()
        assert find_run(root, config(), run_id)["status"] == "generating"
    print("PASS: harness Phase 7 safe Claude Web run and result bundles")


if __name__ == "__main__": main()
