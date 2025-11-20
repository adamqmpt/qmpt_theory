"""
QMPT scenarios for classical simulations.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Tuple

from .models import Pattern, Layer, LayerState
from .metrics import estimate_anomaly, estimate_reflexivity, estimate_self_operator


def _build_patterns(layer_id: str, scenario: str, seed: int) -> list[Pattern]:
    rng = np.random.default_rng(seed)
    patterns: list[Pattern] = []
    # Base population
    for i in range(10):
        features = rng.normal(0, 0.5, size=4)
        patterns.append(Pattern(pattern_id=f"p{i}", layer_id=layer_id, features=features))

    if scenario in {"single_anomaly_injection", "self_aware_anomaly"}:
        features = rng.normal(3.0, 0.2, size=4)  # far from mean
        metadata = {"impact": 0.8}
        if scenario == "self_aware_anomaly":
            metadata["meta_consistency"] = 0.9
        patterns.append(Pattern(pattern_id="anom", layer_id=layer_id, features=features, metadata=metadata))
    return patterns


def _update_layer_state(prev: LayerState, anomaly_mean: float, rng: np.random.Generator, dt: float) -> LayerState:
    stress = max(0.0, min(1.0, prev.stress + rng.normal(0, 0.05) + 0.1 * anomaly_mean))
    protection = max(0.0, min(1.0, prev.protection - 0.05 * anomaly_mean + rng.normal(0, 0.02)))
    novelty = max(0.0, min(1.0, prev.novelty + rng.normal(0, 0.05) + 0.05 * anomaly_mean))
    macro = {"regime": "upgrade" if anomaly_mean > 0.6 else "stable"}
    return LayerState(t=prev.t + dt, stress=stress, protection=protection, novelty=novelty, macro=macro)


def run_scenario(config: Dict) -> Tuple[Layer, Dict]:
    layer_id = config.get("layer_id", "Lk")
    scenario = config.get("scenario", "baseline_layer")
    seed = int(config.get("seed", 42))
    horizon = int(config.get("horizon", 50))
    dt = float(config.get("dt", 1.0))
    rng = np.random.default_rng(seed)

    patterns = _build_patterns(layer_id, scenario, seed)
    estimate_anomaly(patterns)
    estimate_reflexivity(patterns)
    estimate_self_operator(patterns)

    layer = Layer(layer_id=layer_id, description=scenario, patterns=patterns)
    state0 = LayerState(t=0.0, stress=0.2, protection=0.8, novelty=0.1, macro={"regime": "stable"})
    layer.trajectory.append(state0)

    for _ in range(horizon):
        anomaly_mean = float(np.mean([p.anomaly_score or 0.0 for p in patterns]))
        next_state = _update_layer_state(layer.trajectory[-1], anomaly_mean, rng, dt)
        layer.trajectory.append(next_state)

    summary = {
        "scenario": scenario,
        "seed": seed,
        "stress_max": max(s.stress for s in layer.trajectory),
        "protection_min": min(s.protection for s in layer.trajectory),
        "anomaly_mean": float(np.mean([p.anomaly_score or 0.0 for p in patterns])),
    }
    return layer, summary
