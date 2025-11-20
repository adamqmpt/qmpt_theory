"""
Run registry and metadata management.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Any


@dataclass
class RunRecord:
    run_id: str
    timestamp: float
    config_path: str
    backend: str
    status: str
    log_path: str
    results_path: str
    metrics: Dict[str, Any]
    git_commit: Optional[str] = None
    config_hash: Optional[str] = None
    dataset_id: Optional[str] = None


class RunRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, record: RunRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def list(self) -> List[RunRecord]:
        if not self.path.exists():
            return []
        records: List[RunRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                data = json.loads(line)
                records.append(RunRecord(**data))
            except Exception:
                continue
        return records

    def latest(self, n: int = 20) -> List[RunRecord]:
        recs = self.list()
        recs.sort(key=lambda r: r.timestamp, reverse=True)
        return recs[:n]
