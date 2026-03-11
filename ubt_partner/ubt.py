from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ERROR_PATTERNS = [
    re.compile(r"\berror\b", re.IGNORECASE),
    re.compile(r"\bfatal\b", re.IGNORECASE),
    re.compile(r"\bexception\b", re.IGNORECASE),
]


@dataclass
class BuildResult:
    command: str
    return_code: int
    log_path: Path
    error_lines: list[str]


class UBTExecutor:
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def run(self, command: str, cwd: Path) -> BuildResult:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self.logs_dir / f"ubt_{ts}.log"

        process = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        full_output = (process.stdout or "") + "\n" + (process.stderr or "")
        log_path.write_text(full_output, encoding="utf-8", errors="replace")

        error_lines: list[str] = []
        for line in full_output.splitlines():
            if any(pattern.search(line) for pattern in ERROR_PATTERNS):
                error_lines.append(line.strip())

        return BuildResult(
            command=command,
            return_code=process.returncode,
            log_path=log_path,
            error_lines=error_lines[:200],
        )
