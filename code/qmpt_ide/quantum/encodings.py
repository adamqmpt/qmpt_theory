"""
Encodings from QMPT layer states to small quantum circuits.

The goal is to provide a minimal, deterministic mapping that can evolve
into richer QMPT-inspired quantum models later.
"""

from __future__ import annotations

import numpy as np

try:
    from qiskit import QuantumCircuit
except Exception:
    QuantumCircuit = None  # type: ignore


def layer_to_circuit(
    layer_state: dict,
    n_qubits: int = 3,
    depth: int = 1,
    anomaly: float = 0.0,
    seed: int = 0,
):
    """
    Build a shallow circuit encoding layer stress/novelty/anomaly.

    Mapping (toy):
    - stress -> Ry rotations,
    - anomaly -> Rz rotations,
    - novelty -> small Rx perturbations,
    - entanglement ladder per depth.
    """
    if QuantumCircuit is None:
        raise ImportError("qiskit is not available for quantum encodings.")

    stress = float(np.clip(layer_state.get("stress", 0.0), 0.0, 1.0))
    novelty = float(np.clip(layer_state.get("novelty", 0.0), 0.0, 1.0))
    anomaly_val = float(np.clip(anomaly, 0.0, 1.0))

    rng = np.random.default_rng(seed)
    qc = QuantumCircuit(n_qubits)
    ry_angle = stress * np.pi
    rz_angle = anomaly_val * (np.pi / 2.0)
    rx_angle = novelty * (np.pi / 2.0)

    for q in range(n_qubits):
        qc.ry(ry_angle, q)
        qc.rz(rz_angle, q)

    for d in range(depth):
        for q in range(n_qubits - 1):
            qc.cx(q, q + 1)
        # minor randomized phase to avoid total symmetry
        target = d % n_qubits
        qc.rx(rx_angle + rng.normal(0, 0.05), target)
    return qc
