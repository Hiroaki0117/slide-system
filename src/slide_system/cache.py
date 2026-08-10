from __future__ import annotations

from pathlib import Path
from typing import Any

from .hashing import sha256_json
from .storage import atomic_write_json, atomic_write_text


def cache_key(namespace: str, inputs: dict[str, Any]) -> str:
    return sha256_json({"namespace": namespace, "inputs": inputs}).split(":", 1)[1]


class CacheStore:
    def __init__(self, project_root: Path, config: dict[str, Any]) -> None:
        directory = config.get("cache", {}).get("directory", ".cache")
        self.root = project_root / directory

    def artifact_path(self, namespace: str, key: str, extension: str) -> Path:
        safe_namespace = "".join(character for character in namespace if character.isalnum() or character in "-_")
        safe_extension = extension.lstrip(".")
        if not safe_namespace or not safe_extension or len(key) != 64 or any(character not in "0123456789abcdef" for character in key):
            raise ValueError("不正なキャッシュ識別子です")
        return self.root / safe_namespace / key[:2] / f"{key}.{safe_extension}"

    def get(self, namespace: str, key: str, extension: str) -> Path | None:
        path = self.artifact_path(namespace, key, extension)
        return path if path.is_file() else None

    def put_text(
        self,
        namespace: str,
        key: str,
        extension: str,
        content: str,
        *,
        metadata: dict[str, Any],
    ) -> Path:
        path = self.artifact_path(namespace, key, extension)
        atomic_write_text(path, content)
        atomic_write_json(path.with_suffix(path.suffix + ".meta.json"), metadata)
        return path
