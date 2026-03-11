from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path

    @property
    def workspace(self) -> Path:
        return self.root / ".ubt_partner"

    @property
    def logs(self) -> Path:
        return self.workspace / "logs"

    @property
    def sessions(self) -> Path:
        return self.workspace / "sessions"

    @property
    def config(self) -> Path:
        return self.workspace / "config"

    @property
    def providers(self) -> Path:
        return self.config / "providers.json"


DEFAULT_SCAN_EXTENSIONS = {
    ".h",
    ".hpp",
    ".cpp",
    ".c",
    ".cs",
    ".py",
    ".uproject",
    ".uplugin",
    ".ini",
}
