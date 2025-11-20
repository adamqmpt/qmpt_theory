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
from code.qmpt_core import metrics as core_metrics


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


def run_entangled_anomaly_pair(config: Dict, backend: QuantumBackend) -> Tuple[Dict, Dict[str, np.ndarray]]:
    """Two/three-qubit entangled pair with one anomaly-like qubit."""
    qcfg = config.get("quantum", {})
    n_qubits = int(qcfg.get("n_qubits", 2))
    theta = float(qcfg.get("theta", 0.8))
    shots = int(qcfg.get("shots", 512))
    seed = int(config.get("seed", 42))

    if not getattr(backend, "is_available", True):
        summary = {"backend": backend.name, "status": "unavailable"}
        return summary, {"t": np.array([])}

    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n_qubits)
    qc.h(0)
    qc.ry(theta, 1)
    if n_qubits > 2:
        qc.ry(theta / 2, 2)
        qc.cx(0, 2)
    qc.cx(0, 1)
    qres = backend.run_circuit(qc, shots=shots, seed=seed)

    ent = core_metrics.entanglement_entropy(qres.statevector, [0])
    rq = core_metrics.quantum_entropy(qres.statevector)
    anomaly_visibility = float(np.abs(qres.expectations.get("z1", 0.0)))
    timeseries = {
        "t": np.array([0.0]),
        "expectation_mean": np.array([np.mean(list(qres.expectations.values())) if qres.expectations else 0.0]),
        "entanglement": np.array([ent]),
        "entropy": np.array([rq]),
    }
    summary = {
        "backend": backend.name,
        "scenario": "entangled_anomaly_pair",
        "theta": theta,
        "shots": shots,
        "entanglement_entropy": ent,
        "R_quantum": rq,
        "anomaly_visibility": anomaly_visibility,
    }
    return summary, timeseries


def run_quantum_transfer_chain(config: Dict, backend: QuantumBackend) -> Tuple[Dict, Dict[str, np.ndarray]]:
    """Transfer a pattern along a chain with SWAP-like ops and noise."""
    qcfg = config.get("quantum", {})
    n_qubits = int(qcfg.get("n_qubits", 3))
    noise = float(qcfg.get("noise", 0.05))
    shots = int(qcfg.get("shots", 512))
    seed = int(config.get("seed", 42))
    steps = int(config.get("horizon", n_qubits))

    if not getattr(backend, "is_available", True):
        summary = {"backend": backend.name, "status": "unavailable"}
        return summary, {"t": np.array([])}

    from qiskit import QuantumCircuit

    fidelity_arr = []
    ent_arr = []
    t_arr = []
    # initial state |1 0 0 ...>
    qc = QuantumCircuit(n_qubits)
    qc.x(0)
    initial_sv = backend.run_circuit(qc, shots=1, seed=seed).statevector
    current_sv = initial_sv

    for step in range(steps):
        qc_step = QuantumCircuit(n_qubits)
        if step < n_qubits - 1:
            qc_step.swap(step, step + 1)
        # add small noise via random rz
        qc_step.rz(noise, step % n_qubits)
        qres = backend.run_circuit(qc_step, shots=shots, seed=seed + step)
        current_sv = qres.statevector
        fidelity = float(np.abs(np.vdot(initial_sv, current_sv)) ** 2)
        ent = core_metrics.entanglement_entropy(current_sv, [0])
        fidelity_arr.append(fidelity)
        ent_arr.append(ent)
        t_arr.append(step)

    timeseries = {
        "t": np.array(t_arr, dtype=float),
        "fidelity": np.array(fidelity_arr, dtype=float),
        "entanglement": np.array(ent_arr, dtype=float),
    }
    summary = {
        "backend": backend.name,
        "scenario": "quantum_transfer_chain",
        "noise": noise,
        "fidelity_final": float(fidelity_arr[-1]) if fidelity_arr else 0.0,
        "fidelity_min": float(np.min(fidelity_arr)) if fidelity_arr else 0.0,
        "entanglement_mean": float(np.mean(ent_arr)) if ent_arr else 0.0,
    }
    return summary, timeseries


def run_measurement_induced_collapse(config: Dict, backend: QuantumBackend) -> Tuple[Dict, Dict[str, np.ndarray]]:
    """Probe collapse by measuring an anomaly-like superposition."""
    qcfg = config.get("quantum", {})
    theta = float(qcfg.get("theta", 1.1))
    shots = int(qcfg.get("shots", 512))
    seed = int(config.get("seed", 42))

    if not getattr(backend, "is_available", True):
        summary = {"backend": backend.name, "status": "unavailable"}
        return summary, {"t": np.array([])}

    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.ry(theta, 0)
    qc.cx(0, 1)
    pre_res = backend.run_circuit(qc, shots=shots, seed=seed)
    pre_entropy = core_metrics.quantum_entropy(pre_res.statevector)

    # measurement effect: simulate by sampling and building classical distribution entropy
    counts = pre_res.counts
    total = sum(counts.values()) or 1
    probs = np.array(list(counts.values()), dtype=float) / total
    post_entropy = float(-np.sum(probs * np.log2(probs + 1e-12)))

    timeseries = {
        "t": np.array([0.0, 1.0]),
        "entropy": np.array([pre_entropy, post_entropy]),
        "expectation_mean": np.array([
            np.mean(list(pre_res.expectations.values())) if pre_res.expectations else 0.0,
            0.0,
        ]),
    }
    summary = {
        "backend": backend.name,
        "scenario": "measurement_induced_collapse",
        "theta": theta,
        "pre_entropy": pre_entropy,
        "post_entropy": post_entropy,
    }
    return summary, timeseries


def run_quantum_scenario(config: Dict, backend: QuantumBackend, log_path, result_dir) -> Tuple[Dict, Dict[str, np.ndarray]]:
    scenario = config.get("scenario", "layer_stress_probe")
    available = getattr(backend, "is_available", True)
    if scenario == "layer_stress_probe":
        summary, timeseries = run_layer_stress_probe(config, backend)
    elif scenario == "entangled_anomaly_pair":
        summary, timeseries = run_entangled_anomaly_pair(config, backend)
    elif scenario == "quantum_transfer_chain":
        summary, timeseries = run_quantum_transfer_chain(config, backend)
    elif scenario == "measurement_induced_collapse":
        summary, timeseries = run_measurement_induced_collapse(config, backend)
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
