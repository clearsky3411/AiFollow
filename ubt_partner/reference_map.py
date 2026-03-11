from __future__ import annotations

import re
from pathlib import Path

INCLUDE_RE = re.compile(r'^\s*#include\s+["<]([^">]+)[">]')
PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))")


TARGET_SUFFIXES = {".h", ".hpp", ".cpp", ".c", ".py", ".cs"}


def build_reference_map(repo_root: Path) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}

    for p in repo_root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TARGET_SUFFIXES:
            continue

        rel = p.relative_to(repo_root).as_posix()
        refs: set[str] = set()

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            graph[rel] = []
            continue

        for line in content.splitlines():
            include_match = INCLUDE_RE.search(line)
            if include_match:
                refs.add(include_match.group(1))

            import_match = PY_IMPORT_RE.search(line)
            if import_match:
                refs.add(import_match.group(1) or import_match.group(2) or "")

        graph[rel] = sorted(r for r in refs if r)

    return graph
