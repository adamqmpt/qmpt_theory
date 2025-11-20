"""
Shared application state for QMPT Lab IDE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from .core_config import IDEConfig
from .core_runs import RunRegistry, RunRecord
from .sim_runner import SimulationRunner


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass
class AppState:
    """Aggregates config, registry, and runtime selections."""

    config: IDEConfig
    registry: RunRegistry
    sim_runner: SimulationRunner

    current_doc: Optional[Path] = None
    current_note: Optional[Path] = None
    current_run: Optional[RunRecord] = None
    recent_docs: List[Path] = field(default_factory=list)

    def add_recent_doc(self, path: Path, max_items: int = 40) -> None:
        path = path.resolve()
        if path in self.recent_docs:
            self.recent_docs.remove(path)
        self.recent_docs.insert(0, path)
        self.recent_docs = self.recent_docs[:max_items]
