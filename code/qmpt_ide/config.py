"""
Configuration utilities for the QMPT Lab IDE.
Prefer standard library only; loads JSON configs when available.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List

from . import __version__
from .theme import DARK_THEME


@dataclass
class IDEConfig:
    """UI and workspace configuration for the IDE."""

    window_width: int = 1200
    window_height: int = 800
    max_recent_docs: int = 40
    doc_roots: List[str] = field(
        default_factory=lambda: ["README.md", ".", "lab"]
    )
    theme: Dict[str, str] = field(default_factory=lambda: DARK_THEME.copy())
    title: str = field(
        default="QMPT Lab IDE"
    )
    version: str = field(default_factory=lambda: __version__)

    @classmethod
    def load(cls, path: Path | None) -> "IDEConfig":
        """
        Load configuration from JSON; fall back to defaults if file is missing.
        """
        if path is None:
            return cls()
        try:
            payload: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError:
            return cls()

        base = cls()
        for key, value in payload.items():
            if hasattr(base, key):
                setattr(base, key, value)
        # Ensure theme keys exist; merge with defaults
        merged_theme = DARK_THEME.copy()
        merged_theme.update(base.theme or {})
        base.theme = merged_theme
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary representation."""
        return asdict(self)


def default_config_path() -> Path:
    """Return the default config path relative to repo root."""
    return Path(__file__).resolve().parents[2] / "config" / "ide_default.json"


def load_config(path: Path | None = None) -> IDEConfig:
    """Convenience wrapper loading IDEConfig, using default path if not provided."""
    cfg_path = path if path is not None else default_config_path()
    return IDEConfig.load(cfg_path)
