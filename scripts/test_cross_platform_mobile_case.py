#!/usr/bin/env python3
"""Validate the mobile ChatGPT/Claude comparison test contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "test-cases" / "cross-platform" / "01_mobile_internal_training"
EXPECTED_PROFILES = {
    "chatgpt-free": ("chatgpt", "free", "project"),
    "chatgpt-plus": ("chatgpt", "plus", "project"),
    "claude-free": ("claude", "free", "custom-skill"),
    "claude-pro": ("claude", "pro", "custom-skill"),
}


def main() -> int:
    matrix = json.loads((CASE / "TEST_MATRIX.json").read_text(encoding="utf-8"))
    assert matrix["schema_version"] == "1.0"
    assert matrix["target_user"] == {
        "pc_available": False,
        "primary_device": "ipad",
        "secondary_device": "iphone",
        "ai_literacy": "beginner",
    }

    common = matrix["common_inputs"]
    assert set(common) == {"request", "source", "acceptance"}
    for relative in common.values():
        assert (CASE / relative).is_file(), relative
    assert common["acceptance"] not in {common["request"], common["source"]}

    request = (CASE / common["request"]).read_text(encoding="utf-8")
    source = (CASE / common["source"]).read_text(encoding="utf-8")
    combined_input = f"{request}\n{source}"
    forbidden = ["warm_clean", "html_pdf", "layout", "00_MASTER", "60_QA"]
    assert all(token not in combined_input for token in forbidden), combined_input
    assert len(request) <= 180, "The user request should stay short and realistic"

    profiles = {item["id"]: item for item in matrix["profiles"]}
    assert set(profiles) == set(EXPECTED_PROFILES)
    for profile_id, (provider, plan, setup_mode) in EXPECTED_PROFILES.items():
        profile = profiles[profile_id]
        assert (profile["provider"], profile["plan"], profile["setup_mode"]) == (provider, plan, setup_mode)
        instructions = CASE / profile["instructions"]
        assert instructions.is_file(), instructions
        text = instructions.read_text(encoding="utf-8")
        assert "iPad" in text and "iPhone" in text, instructions
        assert "common/REQUEST.md" in text and "common/SOURCE_NOTES.md" in text, instructions

    rules = matrix["rules"]
    assert rules["same_request"] is True
    assert rules["same_source"] is True
    assert rules["same_clarification_answers"] is True
    assert rules["no_improvement_prompt_before_first_artifact"] is True
    assert rules["separate_outputs_by_profile"] is True
    assert rules["common_reference_file_budget"] <= 5
    assert matrix["required_outputs"] == ["html", "pdf"]
    assert (CASE / matrix["evaluation"]).is_file()
    assert (CASE / matrix["result_template"]).is_file()

    print("PASS: mobile cross-platform comparison case contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

