#!/usr/bin/env python3
"""Regression checks for slide-system static content validation."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "slide-system" / "scripts" / "build_deck.py"
SPEC = importlib.util.spec_from_file_location("slide_system_build_deck", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_deck() -> dict:
    duration = "88日（約13週間）"
    phases = [
        ("基礎", "1〜3週", "base", "17〜18kmを上限に維持"),
        ("持久力", "4〜9週", "build", "18〜24kmの条件付き範囲"),
        ("調整", "10〜13週", "taper", "10〜18kmへ段階的に短縮"),
    ]
    return {
        "deck_title": "テスト",
        "audience": "初心者ランナー本人",
        "purpose": "条件付きロードマップを判断できる",
        "mode": "standalone",
        "high_stakes": True,
        "dated_roadmap": True,
        "timeline": {
            "current_date": "2026-08-05",
            "target_date": "2026-11-01",
            "duration_text": duration,
            "slide": 2,
        },
        "safety": {
            "progressive_plan": True,
            "novice_or_returning": True,
            "event_preparation": True,
            "current_condition": "軽い違和感あり",
            "limitations": ["医療診断ではない"],
            "progression_conditions": ["痛みなく回復できる"],
            "recovery_conditions": ["3〜4週ごとに負荷を下げる"],
            "regression_conditions": ["違和感が残る場合は前段階へ戻る"],
            "stop_conditions": ["痛みが増す場合は中止"],
            "consultation_conditions": ["改善しない場合は専門家へ相談"],
            "phase_guidance": [
                {
                    "name": name,
                    "period": period,
                    "phase_type": phase_type,
                    "long_session_distance_or_time": load,
                    "purpose": "段階の目的",
                    "checkpoint": "痛みと回復を確認",
                    "progression_condition": "痛みなく完了",
                    "hold_or_regress_condition": "違和感時は維持または短縮",
                    "slide": 2,
                }
                for name, period, phase_type, load in phases
            ],
            "session_guidance": [
                {
                    "session_type": "イージー走",
                    "pace_or_effort": "会話できる強度",
                    "purpose": "回復と土台",
                    "adjustment_condition": "違和感時は休む",
                    "intensity_class": "easy",
                    "basis": "体感強度を使用",
                },
                {
                    "session_type": "質練習",
                    "pace_or_effort": "確認済み範囲",
                    "purpose": "目標ペースへの適応",
                    "adjustment_condition": "疲労時はイージーへ変更",
                    "intensity_class": "quality",
                    "basis": "利用者確認値",
                },
                {
                    "session_type": "ロング走",
                    "pace_or_effort": "会話できる強度",
                    "purpose": "長時間耐性",
                    "adjustment_condition": "痛みや回復遅延時は短縮",
                    "intensity_class": "long_easy",
                    "basis": "体感強度と現状距離",
                },
            ],
        },
        "slides": [
            {"layout": "cover", "title": "テスト", "date": "2026-08-05"},
            {
                "layout": "process",
                "job": "instruction",
                "visual_role": "explain",
                "title": "段階別の負荷を確認する",
                "lead": duration,
                "steps": [
                    {"label": name, "title": period, "body": load}
                    for name, period, _, load in phases
                ],
                "source": "出典: [S1]",
            },
            {
                "layout": "table",
                "job": "instruction",
                "visual_role": "evidence",
                "title": "週3回の役割を分ける",
                "headers": ["種類", "強度"],
                "rows": [["イージー", "会話強度"], ["質", "週1回"], ["ロング", "会話強度"]],
                "source": "出典: [S1]",
            },
            {
                "layout": "sources_appendix",
                "title": "出典",
                "sources": [
                    {
                        "id": "S1",
                        "title": "検証用資料",
                        "publisher": "検証",
                        "url": "https://example.com",
                        "checked": "2026-08-05",
                    }
                ],
            },
        ],
    }


def codes(deck: dict) -> set[str]:
    return {issue["code"] for issue in MODULE.validate(deck) if issue["level"] == "FAIL"}


def main() -> int:
    good = valid_deck()
    assert not codes(good), codes(good)

    vague = copy.deepcopy(good)
    vague["safety"]["phase_guidance"][1]["long_session_distance_or_time"] = "少しずつ延ばす"
    assert "NON_NUMERIC_PHASE_LOAD" in codes(vague)

    wrong_rounding = copy.deepcopy(good)
    wrong_rounding["timeline"]["duration_text"] = "88日（約12週間）"
    wrong_rounding["slides"][1]["lead"] = "88日（約12週間）"
    assert "TIMELINE_WEEK_ROUNDING" in codes(wrong_rounding)

    too_hard = copy.deepcopy(good)
    too_hard["safety"]["session_guidance"][0]["intensity_class"] = "quality"
    hard_codes = codes(too_hard)
    assert "MISSING_EASY_SESSION" in hard_codes
    assert "TOO_MANY_QUALITY_SESSIONS" in hard_codes

    hidden = copy.deepcopy(good)
    hidden["slides"][1]["steps"][1]["body"] = "表示から距離を削除"
    assert "PHASE_GUIDANCE_NOT_VISIBLE" in codes(hidden)

    print("PASS: build_deck validation regression checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
