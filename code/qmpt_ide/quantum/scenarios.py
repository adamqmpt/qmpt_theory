"""
Quantum scenarios for QMPT Lab IDE.

These are toy mappings from QMPT layer parameters to quantum circuits and
observable proxies. They are intentionally lightweight and deterministic.
"""

from __future__ import annotations

import json
from typing import Dict, Tuple

import numpy as np

from .encodings import layer_to_circuit
from .backends import QuantumBackend, QuantumResult


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _entropy_from_counts(counts: Dict[str, int]) -> float:
    total = sum(counts.values()) or 1
    probs = np.array([c / total for c in counts.values()], dtype=float)
    return float(-np.sum(probs * np.log2(probs + 1e-12)))


def run_layer_stress_probe(config: Dict, backend: QuantumBackend) -> Tuple[Dict, Dict[str, np.ndarray]]:
    qcfg = config.get("quantum", {})
    n_qubits = int(qcfg.get("n_qubits", 3))
    depth = int(qcfg.get("circuit_depth", 1))
    shots = int(qcfg.get("shots", 512))
    seed = int(config.get("seed", 42))
    horizon = int(config.get("horizon", 20))
    dt = float(config.get("dt", 1.0))

    rng = np.random.default_rng(seed)
    t_arr = []
    stress_arr = []
    novelty_arr = []
    expectation_arr = []
    entropy_arr = []
    anomaly_proxy_arr = []

    for step in range(horizon):
        t = step * dt
        base_stress = 0.35 + 0.25 * np.sin(0.15 * t)
        stress = _clip01(base_stress + rng.normal(0, 0.05))
        novelty = _clip01(0.2 + 0.3 * rng.random())
        anomaly = _clip01(0.4 + 0.2 * rng.normal())
        layer_state = {"stress": stress, "novelty": novelty}

        if getattr(backend, "is_available", True):
            circuit = layer_to_circuit(layer_state, n_qubits=n_qubits, depth=depth, anomaly=anomaly, seed=seed + step)
            qresult: QuantumResult = backend.run_circuit(circuit, shots=shots, seed=seed + step)
            expectations = qresult.expectations
            mean_z = float(np.mean(list(expectations.values()))) if expectations else 0.0
            entropy_meas = _entropy_from_counts(qresult.counts) if qresult.counts else qresult.entropy
        else:
            mean_z = 0.0
            entropy_meas = 0.0
        anomaly_proxy = _clip01(0.5 * (1.0 - mean_z) + 0.5 * entropy_meas / max(np.log2(max(1, n_qubits)), 1))

        t_arr.append(t)
        stress_arr.append(stress)
        novelty_arr.append(novelty)
        expectation_arr.append(mean_z)
        entropy_arr.append(entropy_meas)
        anomaly_proxy_arr.append(anomaly_proxy)

    summary = {
        "backend": backend.name,
        "scenario": "layer_stress_probe",
        "seed": seed,
        "shots": shots,
        "n_qubits": n_qubits,
        "circuit_depth": depth,
        "expectation_mean": float(np.mean(expectation_arr)),
        "entropy_mean": float(np.mean(entropy_arr)),
        "anomaly_proxy_mean": float(np.mean(anomaly_proxy_arr)),
    }
    timeseries = {
        "t": np.array(t_arr, dtype=float),
        "stress": np.array(stress_arr, dtype=float),
        "novelty": np.array(novelty_arr, dtype=float),
        "expectation_mean": np.array(expectation_arr, dtype=float),
        "entropy": np.array(entropy_arr, dtype=float),
        "anomaly_proxy": np.array(anomaly_proxy_arr, dtype=float),
    }
    return summary, timeseries


def run_quantum_scenario(config: Dict, backend: QuantumBackend, log_path, result_dir) -> Tuple[Dict, Dict[str, np.ndarray]]:
    scenario = config.get("scenario", "layer_stress_probe")
    available = getattr(backend, "is_available", True)
    if scenario == "layer_stress_probe":
        summary, timeseries = run_layer_stress_probe(config, backend)
    else:
        summary = {"backend": backend.name, "status": "error", "reason": f"Unknown scenario {scenario}"}
        timeseries = {"t": np.array([])}
    if not available and "status" not in summary:
        summary["status"] = "unavailable"
    # basic log
    try:
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write(f"backend={backend.name}\n")
            logf.write(f"scenario={scenario}\n")
            logf.write(f"seed={config.get('seed', 42)}\n")
            logf.write(f"summary={json.dumps(summary)}\n")
    except Exception:
        pass
    return summary, timeseries
