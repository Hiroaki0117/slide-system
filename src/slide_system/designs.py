from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .storage import read_json
from .validation import validate_document


@dataclass(frozen=True)
class DesignPack:
    root: Path
    manifest: dict[str, Any]
    entrypoints: dict[str, Path]
    template: Path
    font: Path

    @property
    def design_id(self) -> str:
        return str(self.manifest["id"])

    @property
    def version(self) -> str:
        return str(self.manifest["version"])


def _resolve_inside_project(project_root: Path, base: Path, relative: str) -> Path:
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(f"デザインパックの参照がプロジェクト外です: {relative}") from exc
    if not resolved.is_file():
        raise FileNotFoundError(f"デザインパックの参照先がありません: {resolved}")
    return resolved


def load_design_pack(project_root: Path, design_id: str) -> DesignPack:
    root = (project_root / "designs" / design_id).resolve()
    manifest_path = root / "design.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"デザインパックが見つかりません: {design_id}")
    manifest = read_json(manifest_path)
    validate_document(project_root, "design-pack", manifest)
    if manifest["id"] != design_id:
        raise ValueError(f"デザインIDがフォルダ名と一致しません: {manifest['id']} != {design_id}")
    entrypoints = {
        name: _resolve_inside_project(project_root, root, relative)
        for name, relative in manifest["entrypoints"].items()
    }
    renderer = manifest["renderer"]
    template = _resolve_inside_project(project_root, root, renderer["template"])
    font = _resolve_inside_project(project_root, root, renderer["font"])
    return DesignPack(root=root, manifest=manifest, entrypoints=entrypoints, template=template, font=font)


def load_layout_registry(pack: DesignPack) -> dict[str, dict[str, Any]]:
    document = read_json(pack.entrypoints["layouts"])
    layouts = document.get("layouts")
    if not isinstance(layouts, list) or not layouts:
        raise ValueError(f"レイアウト定義がありません: {pack.entrypoints['layouts']}")
    registry: dict[str, dict[str, Any]] = {}
    for layout in layouts:
        if not isinstance(layout, dict) or not str(layout.get("id", "")).strip():
            raise ValueError("各レイアウトにはidが必要です")
        layout_id = str(layout["id"])
        if layout_id in registry:
            raise ValueError(f"レイアウトIDが重複しています: {layout_id}")
        registry[layout_id] = layout
    return registry
