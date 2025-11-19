from pathlib import Path

from code.qmpt_ide.sim_runner import SimulationRequest, run_simulation
from code.qmpt_ide.state import WorkspaceState


def test_sim_runner_creates_log(tmp_path: Path) -> None:
    ws = WorkspaceState(
        notes_dir=tmp_path / "notes",
        logs_dir=tmp_path / "logs",
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text("dummy: true", encoding="utf-8")
    req = SimulationRequest(config_path=cfg, seed=1, device="cpu")
    result = run_simulation(req, ws)
    assert result.log_path.is_file()
    payload = result.log_path.read_text(encoding="utf-8")
    assert "dummy" not in payload  # stub writes its own json content
    assert "metrics" in payload
