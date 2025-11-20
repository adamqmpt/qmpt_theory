"""
IO helpers for QMPT simulation results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional
import numpy as np

from .models import Layer
from .metrics import compute_run_metrics


def save_run_results(run_id: str, layer: Layer, summary: Dict, base_dir: Path, config: Optional[Dict] = None) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = base_dir / "metrics.json"
    timeseries_path = base_dir / "timeseries.npz"
    patterns_path = base_dir / "patterns.json"

    t = np.array([s.t for s in layer.trajectory])
    stress = np.array([s.stress for s in layer.trajectory])
    protection = np.array([s.protection for s in layer.trajectory])
    novelty = np.array([s.novelty for s in layer.trajectory])
    np.savez(timeseries_path, t=t, stress=stress, protection=protection, novelty=novelty)

    timeseries_payload = {"t": t, "stress": stress, "protection": protection, "novelty": novelty}
    if config is None:
        config = {}
    derived = compute_run_metrics(timeseries_payload, config)
    merged_metrics = {**summary, **derived}
    metrics_path.write_text(json.dumps(merged_metrics, indent=2), encoding="utf-8")

    patterns = [
        {
            "pattern_id": p.pattern_id,
            "layer_id": p.layer_id,
            "anomaly_score": p.anomaly_score,
            "reflexivity": p.reflexivity,
            "self_operator": p.self_operator,
        }
        for p in layer.patterns
    ]
    patterns_path.write_text(json.dumps(patterns, indent=2), encoding="utf-8")
