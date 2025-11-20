"""
Quantum utilities for QMPT Lab IDE.

Provides:
- backend abstractions for quantum engines (local simulator, dummy fallback),
- encodings from QMPT layer states to small quantum circuits,
- quantum scenarios mapping QMPT parameters to circuit runs.
"""

from .backends import (
    QuantumBackend,
    LocalSimulatorBackend,
    DummyQuantumBackend,
    QuantumResult,
    QISKIT_AVAILABLE,
)
from . import encodings, scenarios

__all__ = [
    "QuantumBackend",
    "LocalSimulatorBackend",
    "DummyQuantumBackend",
    "QuantumResult",
    "encodings",
    "scenarios",
    "QISKIT_AVAILABLE",
]
