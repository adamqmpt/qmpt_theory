from pathlib import Path

from code.qmpt_ide.state import WorkspaceState


def test_add_run_limits(tmp_path: Path) -> None:
    ws = WorkspaceState(
        notes_dir=tmp_path / "notes",
        logs_dir=tmp_path / "logs",
    )
    ws.ensure_dirs()
    for i in range(5):
        path = ws.logs_dir / f"log_{i}.log"
        path.write_text("x", encoding="utf-8")
        ws.add_run(path, max_items=3)
    assert len(ws.recent_runs) == 3
    # most recent first
    assert ws.recent_runs[0].name == "log_4.log"
    assert ws.recent_runs[-1].name == "log_2.log"
