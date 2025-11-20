"""
Lightweight simulation runner stub for QMPT Lab IDE.

Intended to be replaced by real qmpt.simulation calls once available.
Currently:
- accepts config path, seed, device,
- writes a log with placeholder metrics to lab/logs,
- returns a summary dict.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .state import WorkspaceState


@dataclass
class SimulationRequest:
    config_path: Path
    seed: int
    device: str  # e.g., "cpu", "gpu"


@dataclass
class SimulationResult:
    log_path: Path
    duration_s: float
    metrics: Dict[str, float]
    status: str


def run_simulation(
    req: SimulationRequest,
    workspace: WorkspaceState,
    log_path: Optional[Path] = None,
    steps: int = 3,
    delay_s: float = 0.1,
) -> SimulationResult:
    """
    Run a placeholder simulation and write metrics to a log file.

    This stub should be replaced by a call into qmpt.simulation.* when available.
    """
    workspace.ensure_dirs()
    random.seed(req.seed)
    if log_path is None:
        log_path = workspace.new_log_path(prefix="sim")
    start = time.time()

    # Placeholder metrics: emulate anomaly/reflexivity/stress ranges.
    metrics = {
        "A": round(random.uniform(0.5, 1.2), 3),
        "R_norm": round(random.uniform(0.4, 0.95), 3),
        "sigma_k": round(random.uniform(0.1, 0.9), 3),
        "duration_s": 0.0,
    }
    # Emit step-by-step progress
    progress = []
    for step in range(steps):
        progress.append({"step": step + 1, "total": steps, "status": "running"})
        time.sleep(delay_s)
    duration = time.time() - start
    metrics["duration_s"] = round(duration, 3)

    payload = {
        "config": str(req.config_path),
        "seed": req.seed,
        "device": req.device,
        "status": "ok",
        "metrics": metrics,
        "progress": progress,
    }
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return SimulationResult(
        log_path=log_path,
        duration_s=duration,
        metrics=metrics,
        status="ok",
    )
