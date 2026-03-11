from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SessionNode:
    id: str
    name: str
    parent_id: str | None
    created_at: str
    updated_at: str
    notes: str = ""
    last_build_log: str | None = None
    changed_files: list[str] = field(default_factory=list)
    reference_map: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, parent_id: str | None = None) -> "SessionNode":
        timestamp = now_iso()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            created_at=timestamp,
            updated_at=timestamp,
        )


class SessionStore:
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: SessionNode) -> None:
        session.updated_at = now_iso()
        path = self.session_dir / f"{session.id}.json"
        path.write_text(json.dumps(asdict(session), ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, session_id: str) -> SessionNode:
        path = self.session_dir / f"{session_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionNode(**data)

    def list_all(self) -> list[SessionNode]:
        result: list[SessionNode] = []
        for file in sorted(self.session_dir.glob("*.json")):
            data: dict[str, Any] = json.loads(file.read_text(encoding="utf-8"))
            result.append(SessionNode(**data))
        return result
