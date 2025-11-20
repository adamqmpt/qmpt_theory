"""
QMPT scenarios for classical simulations.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Tuple, Any

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

    if scenario == "anomaly_injection":
        return _run_anomaly_injection(config, layer_id, seed, horizon, dt, rng)
    if scenario == "collapse_recovery":
        return _run_collapse_recovery(config, layer_id, seed, horizon, dt, rng)
    if scenario == "transfer_cycle":
        return _run_transfer_cycle(config, layer_id, seed, horizon, dt, rng)

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


def _run_anomaly_injection(config: Dict, layer_id: str, seed: int, horizon: int, dt: float, rng) -> Tuple[Layer, Dict[str, Any]]:
    inject_step = int(config.get("inject_step", horizon // 3))
    anomaly_level = float(config.get("anomaly_level", 0.8))
    threshold = float(config.get("anomaly_threshold", 0.5))
    layer = Layer(layer_id=layer_id, description="anomaly_injection")
    state0 = LayerState(t=0.0, stress=0.2, protection=0.8, novelty=0.1, macro={"regime": "stable"})
    layer.trajectory.append(state0)
    anomaly_gt = []
    anomaly_est = []
    for step in range(horizon):
        current = layer.trajectory[-1]
        stress = current.stress + rng.normal(0, 0.03)
        protection = current.protection + rng.normal(0, 0.02)
        novelty = current.novelty + rng.normal(0, 0.02)
        is_anom = step >= inject_step
        anomaly_gt.append(1.0 if is_anom else 0.0)
        if is_anom:
            stress += anomaly_level * 0.2
            protection -= anomaly_level * 0.1
            novelty += anomaly_level * 0.05
        stress = float(np.clip(stress, 0.0, 1.0))
        protection = float(np.clip(protection, 0.0, 1.0))
        novelty = float(np.clip(novelty, 0.0, 1.0))
        est = float(np.clip(0.3 * stress + 0.4 * (1 - protection) + 0.3 * novelty, 0.0, 1.0))
        anomaly_est.append(est)
        layer.trajectory.append(LayerState(t=(step + 1) * dt, stress=stress, protection=protection, novelty=novelty, macro={"regime": "upgrade" if is_anom else "stable"}))

    anomaly_est_arr = np.array(anomaly_est)
    gt_arr = np.array(anomaly_gt)
    det_mask = anomaly_est_arr >= threshold
    detection_latency = -1
    if np.any(det_mask & (gt_arr > 0)):
        detection_latency = int(np.argmax(det_mask & (gt_arr > 0)) * dt)
    summary = {
        "scenario": "anomaly_injection",
        "seed": seed,
        "inject_step": inject_step,
        "anomaly_level": anomaly_level,
        "detection_latency": detection_latency,
        "false_positives": int(np.sum(det_mask & (gt_arr == 0))),
        "false_negatives": int(np.sum((~det_mask) & (gt_arr == 1))),
        "anomaly_threshold": threshold,
        "timeseries": {"anomaly_ground_truth": gt_arr, "anomaly_proxy": anomaly_est_arr},
    }
    return layer, summary


def _run_collapse_recovery(config: Dict, layer_id: str, seed: int, horizon: int, dt: float, rng) -> Tuple[Layer, Dict[str, Any]]:
    recovery = bool(config.get("recovery", True))
    anomaly_boost = float(config.get("anomaly_boost", 0.2))
    layer = Layer(layer_id=layer_id, description="collapse_recovery")
    state0 = LayerState(t=0.0, stress=0.5, protection=0.6, novelty=0.2, macro={"regime": "stable"})
    layer.trajectory.append(state0)
    collapse_time = None
    recovery_time = None
    capacity = 1.0
    capacity_traj = []
    for step in range(horizon):
        current = layer.trajectory[-1]
        stress = float(np.clip(current.stress + 0.08 + rng.normal(0, 0.02), 0.0, 1.2))
        capacity = float(np.clip(capacity - 0.06 + rng.normal(0, 0.02), 0.0, 1.0))
        if stress > 0.9 and collapse_time is None:
            collapse_time = (step + 1) * dt
        if recovery and stress > 0.8:
            stress -= anomaly_boost * 0.2
            capacity += anomaly_boost * 0.1
        if recovery and capacity < 0.5:
            capacity += 0.05
            stress -= 0.05
        if recovery_time is None and collapse_time and capacity > 0.8:
            recovery_time = (step + 1) * dt

        protection = float(np.clip(current.protection - 0.05 + capacity * 0.1 + rng.normal(0, 0.02), 0.0, 1.0))
        novelty = float(np.clip(current.novelty + rng.normal(0, 0.02), 0.0, 1.0))
        layer.trajectory.append(LayerState(t=(step + 1) * dt, stress=stress, protection=protection, novelty=novelty, macro={"regime": "collapse" if stress > 0.9 else "stable"}))
        capacity_traj.append(capacity)
    summary = {
        "scenario": "collapse_recovery",
        "seed": seed,
        "collapse_time": collapse_time if collapse_time is not None else -1,
        "recovery_time": recovery_time if recovery_time is not None else -1,
        "capacity_min": float(min(capacity_traj)) if capacity_traj else 0.0,
        "timeseries": {"capacity": np.array(capacity_traj)},
    }
    return layer, summary


def _run_transfer_cycle(config: Dict, layer_id: str, seed: int, horizon: int, dt: float, rng) -> Tuple[Layer, Dict[str, Any]]:
    substrates = config.get("substrates", ["S1", "S2"])
    noise = config.get("substrate_noise", [0.05 for _ in substrates])
    continuity = []
    layer = Layer(layer_id=layer_id, description="transfer_cycle")
    state0 = LayerState(t=0.0, stress=0.3, protection=0.7, novelty=0.2, macro={"regime": "stable"})
    layer.trajectory.append(state0)
    pattern_fidelity = 1.0
    for step in range(len(substrates)):
        n = float(noise[step] if step < len(noise) else noise[-1])
        pattern_fidelity = float(np.clip(pattern_fidelity - n + rng.normal(0, 0.01), 0.0, 1.0))
        continuity.append(pattern_fidelity)
        stress = float(np.clip(layer.trajectory[-1].stress + n, 0.0, 1.0))
        protection = float(np.clip(layer.trajectory[-1].protection - n * 0.5, 0.0, 1.0))
        novelty = float(np.clip(layer.trajectory[-1].novelty + n * 0.2, 0.0, 1.0))
        layer.trajectory.append(LayerState(t=(step + 1) * dt, stress=stress, protection=protection, novelty=novelty, macro={"substrate": substrates[step]}))
    summary = {
        "scenario": "transfer_cycle",
        "seed": seed,
        "substrates": substrates,
        "continuity_min": float(min(continuity)),
        "continuity_mean": float(np.mean(continuity)),
        "identity_loss_prob": float(np.mean(np.array(continuity) < 0.7)),
        "timeseries": {"continuity": np.array(continuity)},
    }
    return layer, summary
