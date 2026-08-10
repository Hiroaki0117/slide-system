from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class RunLockedError(RuntimeError):
    def __init__(self, path: Path, details: dict[str, Any] | None = None) -> None:
        owner = (details or {}).get("owner", "不明")
        locked_at = (details or {}).get("locked_at", "不明")
        super().__init__(f"このRunは別の処理が使用中です: owner={owner}, locked_at={locked_at}, lock={path}")
        self.path = path
        self.details = details or {}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_lock(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"owner": "不明", "locked_at": "不明", "corrupt": True}


class RunLock:
    def __init__(self, run_dir: Path, *, owner: str) -> None:
        self.path = run_dir / ".state" / "run.lock"
        self.owner = owner
        self.token = uuid.uuid4().hex
        self.acquired = False

    def acquire(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        details = {
            "owner": self.owner,
            "process_id": os.getpid(),
            "host": socket.gethostname(),
            "locked_at": _now_iso(),
            "token": self.token,
        }
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RunLockedError(self.path, read_lock(self.path)) from exc
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(details, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            self.path.unlink(missing_ok=True)
            raise
        self.acquired = True
        return self

    def release(self) -> None:
        if not self.acquired:
            return
        details = read_lock(self.path)
        if not details or details.get("token") != self.token:
            raise RuntimeError(f"所有権を確認できないためロックを解除できません: {self.path}")
        self.path.unlink()
        self.acquired = False

    def __enter__(self) -> "RunLock":
        return self.acquire()

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.release()
