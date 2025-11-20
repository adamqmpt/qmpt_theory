import pytest

from code.qmpt_ide.quantum.backends import QISKIT_AVAILABLE, LocalSimulatorBackend, DummyQuantumBackend
from code.qmpt_ide.quantum.encodings import layer_to_circuit
from code.qmpt_ide.quantum.scenarios import run_layer_stress_probe


def test_layer_to_circuit_qubit_count():
    if not QISKIT_AVAILABLE:
        pytest.skip("qiskit not available")
    qc = layer_to_circuit({"stress": 0.5, "novelty": 0.3}, n_qubits=4, depth=2, anomaly=0.2, seed=1)
    assert qc.num_qubits == 4
    assert qc.depth() > 0


def test_run_layer_stress_probe_backend_available():
    backend = LocalSimulatorBackend() if QISKIT_AVAILABLE else DummyQuantumBackend()
    summary, timeseries = run_layer_stress_probe(
        {
            "seed": 7,
            "horizon": 4,
            "dt": 1.0,
            "quantum": {"n_qubits": 2, "circuit_depth": 1, "shots": 64},
        },
        backend,
    )
    assert "expectation_mean" in summary
    assert "t" in timeseries
    assert len(timeseries["t"]) == 4
    if backend.is_available:
        assert summary["backend"] == "quantum_local"
    else:
        assert summary.get("status") in {"unavailable", "not_implemented"}
