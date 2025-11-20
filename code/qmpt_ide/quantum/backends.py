"""
Quantum backend abstractions for QMPT Lab IDE.

LocalSimulatorBackend uses qiskit (Statevector) if available to compute
probabilities and simple observables; DummyQuantumBackend provides a safe
fallback when qiskit is not installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector

    QISKIT_AVAILABLE = True
except Exception:
    QuantumCircuit = None  # type: ignore
    Statevector = None  # type: ignore
    QISKIT_AVAILABLE = False


@dataclass
class QuantumResult:
    counts: Dict[str, int]
    expectations: Dict[str, float]
    entropy: float
    metadata: Dict[str, Any]
    statevector: Any = None


class QuantumBackend:
    name: str = "abstract"

    def run_circuit(self, circuit, shots: int, seed: int) -> QuantumResult:
        raise NotImplementedError

    @property
    def is_available(self) -> bool:
        return True


class LocalSimulatorBackend(QuantumBackend):
    """
    Lightweight simulator based on qiskit Statevector.
    Uses numpy sampling for counts; does not require Aer.
    """

    name = "quantum_local"

    def __init__(self) -> None:
        self.available = QISKIT_AVAILABLE and QuantumCircuit is not None and Statevector is not None

    @property
    def is_available(self) -> bool:
        return self.available

    def run_circuit(self, circuit, shots: int, seed: int) -> QuantumResult:
        if not self.available:
            raise RuntimeError("qiskit is not available; cannot run quantum simulator")
        sv = Statevector.from_instruction(circuit)
        probs = sv.probabilities_dict()
        keys = list(probs.keys())
        pvals = np.array([probs[k] for k in keys], dtype=float)
        rng = np.random.default_rng(seed)
        samples = rng.choice(keys, size=shots, p=pvals)
        counts: Dict[str, int] = {}
        for s in samples:
            counts[s] = counts.get(s, 0) + 1

        # Expectation of Z on each qubit computed from probabilities
        num_qubits = circuit.num_qubits
        expectations: Dict[str, float] = {}
        for qi in range(num_qubits):
            exp = 0.0
            for bitstring, prob in probs.items():
                bit = bitstring[::-1][qi]  # qiskit bit order (little endian)
                exp += prob * (1.0 if bit == "0" else -1.0)
            expectations[f"z{qi}"] = float(exp)

        entropy = float(-np.sum(pvals * np.log2(pvals + 1e-12)))
        metadata = {"shots": shots, "backend": self.name, "seed": seed}
        return QuantumResult(counts=counts, expectations=expectations, entropy=entropy, metadata=metadata, statevector=np.array(sv.data))


class DummyQuantumBackend(QuantumBackend):
    """Fallback backend when qiskit is missing."""

    name = "quantum_dummy"

    @property
    def is_available(self) -> bool:
        return False

    def run_circuit(self, circuit, shots: int, seed: int) -> QuantumResult:  # type: ignore[override]
        return QuantumResult(
            counts={},
            expectations={},
            entropy=0.0,
            metadata={
                "backend": self.name,
                "status": "unavailable",
                "reason": "qiskit not installed",
                "shots": shots,
                "seed": seed,
            },
        )
