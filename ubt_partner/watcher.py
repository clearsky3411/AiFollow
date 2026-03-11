from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_SCAN_EXTENSIONS


def scan_file_state(repo_root: Path) -> dict[str, float]:
    state: dict[str, float] = {}
    for p in repo_root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in DEFAULT_SCAN_EXTENSIONS:
            continue
        rel = p.relative_to(repo_root).as_posix()
        state[rel] = p.stat().st_mtime
    return state


def diff_states(old: dict[str, float], new: dict[str, float]) -> list[str]:
    changed: list[str] = []
    all_keys = set(old) | set(new)
    for key in sorted(all_keys):
        if old.get(key) != new.get(key):
            changed.append(key)
    return changed
