"""
Configuration loading for QMPT Lab IDE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from . import __version__


@dataclass
class WindowConfig:
    width: int = 1200
    height: int = 800


@dataclass
class IDEConfig:
    title: str = "QMPT Lab IDE"
    version: str = __version__
    window: WindowConfig = field(default_factory=WindowConfig)
    doc_roots: list[str] = field(default_factory=lambda: ["README.md", "lab", "code"])
    theme: Dict[str, str] = field(
        default_factory=lambda: {
            "bg": "#0b0d11",
            "panel": "#121620",
            "accent": "#64ffda",
            "accent_hover": "#52e0c0",
            "fg": "#e6e6e6",
            "muted": "#9ea7ad",
            "border": "#273240",
            "danger": "#ef5350",
        }
    )
    results_dir: str = "lab/results"
    logs_dir: str = "lab/logs"
    notes_dir: str = "lab/notes"
    registry_path: str = "lab/runs.jsonl"
    default_backend: str = "classical"
    default_seed: int = 42
    default_device: str = "cpu"
    matplotlib_enabled: bool = True


def _decode(data: Dict[str, Any]) -> IDEConfig:
    cfg = IDEConfig()
    if "window" in data:
        win = data["window"]
        cfg.window = WindowConfig(
            width=win.get("width", cfg.window.width),
            height=win.get("height", cfg.window.height),
        )
    for key, value in data.items():
        if hasattr(cfg, key) and key != "window":
            setattr(cfg, key, value)
    return cfg


def load_config(path: Path) -> IDEConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return IDEConfig()
    except json.JSONDecodeError:
        return IDEConfig()
    return _decode(payload)


def save_config(config: IDEConfig, path: Path) -> None:
    data = {
        "title": config.title,
        "version": config.version,
        "window": {"width": config.window.width, "height": config.window.height},
        "doc_roots": config.doc_roots,
        "theme": config.theme,
        "results_dir": config.results_dir,
        "logs_dir": config.logs_dir,
        "notes_dir": config.notes_dir,
        "registry_path": config.registry_path,
        "default_backend": config.default_backend,
        "default_seed": config.default_seed,
        "default_device": config.default_device,
        "matplotlib_enabled": config.matplotlib_enabled,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
