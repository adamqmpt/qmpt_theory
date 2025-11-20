"""
Entry point for QMPT Lab IDE (v0.9.0 “Quantum Patterns & Examples”).
Wires UI components and shared state.
Run with: python3 -m code.qmpt_ide.app
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from .core_config import IDEConfig, load_config
from .core_runs import RunRegistry
from .sim_runner import SimulationRunner
from .state import AppState, repo_root
from .ui_main import MainWindow
from .theme import init_styles
from . import __version__


def main() -> None:
    root = tk.Tk()
    cfg_path = repo_root() / "config" / "ide_default.json"
    config: IDEConfig = load_config(cfg_path)
    registry = RunRegistry(repo_root() / "lab" / "runs.jsonl")
    sim_runner = SimulationRunner(registry=registry)
    state = AppState(config=config, registry=registry, sim_runner=sim_runner)

    root.title(f"{config.title} v{__version__}")
    root.geometry(f"{config.window.width}x{config.window.height}")
    init_styles(root, config.theme)

    MainWindow(root=root, state=state).pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
