"""
Workspace state and helpers for QMPT Lab IDE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def repo_root() -> Path:
    """Return repository root assuming this file lives under code/qmpt_ide."""
    return Path(__file__).resolve().parents[2]


@dataclass
class WorkspaceState:
    """Tracks workspace locations and recent documents."""

    notes_dir: Path = field(default_factory=lambda: repo_root() / "lab" / "notes")
    logs_dir: Path = field(default_factory=lambda: repo_root() / "lab" / "logs")
    recent_docs: List[Path] = field(default_factory=list)

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
