from pathlib import Path

from code.qmpt_ide.sim_runner import SimulationRunner, BackendType
from code.qmpt_ide.core_runs import RunRegistry
from code.qmpt_ide.state import repo_root


def test_classical_sample_configs(tmp_path: Path) -> None:
    root = repo_root()
    configs = [
        root / "lab" / "configs" / "baseline_layer.json",
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
    cfg = root / "lab" / "configs" / "quantum_stub_example.json"
    registry = RunRegistry(tmp_path / "runs.jsonl")
    runner = SimulationRunner(registry)
    result = runner.run(cfg, BackendType.QUANTUM)
    metrics_path = result.results_path / "metrics.json"
    assert metrics_path.exists()
    content = metrics_path.read_text(encoding="utf-8")
    assert "quantum_stub" in content
    assert "not_implemented" in content
