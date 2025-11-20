"""
Workspace state and helpers for QMPT Lab IDE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


def repo_root() -> Path:
    """Return repository root assuming this file lives under code/qmpt_ide."""
    return Path(__file__).resolve().parents[2]


@dataclass
class WorkspaceState:
    """Tracks workspace locations and recent documents."""

    notes_dir: Path = field(default_factory=lambda: repo_root() / "lab" / "notes")
    logs_dir: Path = field(default_factory=lambda: repo_root() / "lab" / "logs")
    recent_docs: List[Path] = field(default_factory=list)
    recent_runs: List[Path] = field(default_factory=list)

    def ensure_dirs(self) -> None:
        """Create required directories if they do not exist."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def add_recent(self, path: Path, max_items: int) -> None:
        """Track recently opened documents."""
        path = path.resolve()
        if path in self.recent_docs:
            self.recent_docs.remove(path)
        self.recent_docs.insert(0, path)
        if len(self.recent_docs) > max_items:
            self.recent_docs = self.recent_docs[:max_items]

    def add_run(self, log_path: Path, max_items: int) -> None:
        """Track recently produced simulation logs."""
        log_path = log_path.resolve()
        if log_path in self.recent_runs:
            self.recent_runs.remove(log_path)
        self.recent_runs.insert(0, log_path)
        if len(self.recent_runs) > max_items:
            self.recent_runs = self.recent_runs[:max_items]

    def discover_docs(self, roots: List[str], limit: int = 50) -> List[Path]:
        """Return a list of markdown/text files under provided roots."""
        root_path = repo_root()
        results: List[Path] = []
        for root in roots:
            candidate = (root_path / root).resolve()
            if candidate.is_file() and candidate.suffix.lower() in {".md", ".txt"}:
                results.append(candidate)
            elif candidate.is_dir():
                for path in candidate.rglob("*"):
                    if path.suffix.lower() in {".md", ".txt"}:
                        results.append(path)
                        if len(results) >= limit:
                            return results
        return results

    def new_log_path(self, prefix: str = "sim") -> Path:
        """Return a unique log file path under logs_dir."""
        self.ensure_dirs()
        counter = 0
        while True:
            name = f"{prefix}_{counter:04d}.log"
            candidate = self.logs_dir / name
            if not candidate.exists():
                return candidate
            counter += 1

    def read_log(self, path: Path) -> Optional[str]:
        """Read a log file if it exists."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
