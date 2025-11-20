from pathlib import Path

from code.qmpt_ide.sim_runner import SimulationRunner, BackendType
from code.qmpt_ide.core_runs import RunRegistry
from code.qmpt_ide.state import repo_root
from code.qmpt_ide.quantum.backends import QISKIT_AVAILABLE


def test_classical_sample_configs(tmp_path: Path) -> None:
    root = repo_root()
    configs = [
        root / "lab" / "configs" / "classical_layer_dynamics.json",
        root / "lab" / "configs" / "single_anomaly_injection.json",
        root / "lab" / "configs" / "self_aware_anomaly.json",
    ]
    registry = RunRegistry(tmp_path / "runs.jsonl")
    runner = SimulationRunner(registry)
    for cfg in configs:
        result = runner.run(cfg, BackendType.CLASSICAL)
        assert result.log_path.exists()
        assert (result.results_path / "metrics.json").exists()
        assert (result.results_path / "timeseries.npz").exists()


def test_quantum_stub_config(tmp_path: Path) -> None:
    root = repo_root()
    cfg = root / "lab" / "configs" / "quantum_layer_stress_probe.json"
    registry = RunRegistry(tmp_path / "runs.jsonl")
    runner = SimulationRunner(registry)
    result = runner.run(cfg, BackendType.QUANTUM)
    metrics_path = result.results_path / "metrics.json"
    assert metrics_path.exists()
    content = metrics_path.read_text(encoding="utf-8")
    if QISKIT_AVAILABLE:
        assert "layer_stress_probe" in content
    else:
        assert "unavailable" in content or "quantum_dummy" in content


def test_hybrid_config(tmp_path: Path) -> None:
    root = repo_root()
    cfg = root / "lab" / "configs" / "hybrid_layer_cycle.json"
    registry = RunRegistry(tmp_path / "runs.jsonl")
    runner = SimulationRunner(registry)
    result = runner.run(cfg, BackendType.HYBRID)
    assert (result.results_path / "metrics.json").exists()
    assert (result.results_path / "timeseries.npz").exists()


def test_classical_ensemble(tmp_path: Path) -> None:
    root = repo_root()
    cfg = root / "lab" / "configs" / "classical_ensemble.json"
    registry = RunRegistry(tmp_path / "runs.jsonl")
    runner = SimulationRunner(registry)
    dataset_id, results = runner.run_ensemble(cfg, BackendType.CLASSICAL)
    assert len(results) >= 2
    ds_manifest = root / "lab" / "datasets" / dataset_id / "dataset_manifest.json"
    assert ds_manifest.exists()


def test_new_scenarios_run(tmp_path: Path) -> None:
    # Anomaly injection
    cfg_anom = {
        "backend": "classical",
        "scenario": "anomaly_injection",
        "horizon": 10,
        "dt": 1.0,
        "inject_step": 3,
    }
    registry = RunRegistry(tmp_path / "runs.jsonl")
    runner = SimulationRunner(registry)
    res1 = runner.run_config(cfg_anom, BackendType.CLASSICAL)
    assert (res1.results_path / "metrics.json").exists()

    # Collapse recovery
    cfg_collapse = {
        "backend": "classical",
        "scenario": "collapse_recovery",
        "horizon": 8,
    }
    res2 = runner.run_config(cfg_collapse, BackendType.CLASSICAL)
    assert (res2.results_path / "metrics.json").exists()

    # Transfer cycle
    cfg_transfer = {
        "backend": "classical",
        "scenario": "transfer_cycle",
        "substrates": ["S1", "S2"],
        "substrate_noise": [0.1, 0.15],
    }
    res3 = runner.run_config(cfg_transfer, BackendType.CLASSICAL)
    assert (res3.results_path / "metrics.json").exists()
