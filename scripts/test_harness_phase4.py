#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slide_system.adapters import load_adapter, prepare_session  # noqa: E402
from slide_system.runs import create_run, find_run  # noqa: E402
from slide_system.state import transition_run  # noqa: E402


def config() -> dict:
    return {
        "defaults": {"language": "ja", "mode": "interactive", "design_pack": "warm_clean", "output_profile": "html_pdf", "aspect_ratio": "16:9"},
        "runs": {"directory": "runs", "generate_index": True},
        "qa": {"require_human_approval": True},
        "cache": {"directory": ".cache"},
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="slide-system-phase4-") as temporary:
        project_root = Path(temporary)
        shutil.copytree(ROOT / "schemas", project_root / "schemas")
        shutil.copytree(ROOT / "harness", project_root / "harness")
        run = create_run(project_root, config(), title="新人研修", summary="アダプター検証", tags=["研修"], adapter="manual")
        run_id = run["run_id"]
        codex = load_adapter(project_root, "codex")
        claude = load_adapter(project_root, "claude-code")
        assert codex.capabilities == claude.capabilities
        created_context = prepare_session(project_root, config(), run_id, adapter_id="codex", owner="test")
        text = created_context.read_text(encoding="utf-8")
        assert "まだ制作を開始しない" in text
        assert "質問、制作内容、PDF、最終採用" in text
        transition_run(project_root, config(), run_id, new_status="confirmation_pending", owner="test", last_action="構成案提示", next_action="承認待ち")
        pending_context = prepare_session(project_root, config(), run_id, adapter_id="claude-code", owner="test")
        assert "承認前にHTMLを生成しない" in pending_context.read_text(encoding="utf-8")
        current = find_run(project_root, config(), run_id)
        assert current["execution"]["adapter"] == "claude-code"
        assert len(current["sessions"]) == 2
    print("PASS: harness Phase 4 Codex and Claude Code adapter resume contract")


if __name__ == "__main__":
    main()
