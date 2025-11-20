"""
Theme utilities for QMPT Lab IDE.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict

from .core_config import IDEConfig


def init_styles(root: tk.Tk, theme: Dict[str, str]) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=theme["bg"])
    style.configure("Panel.TFrame", background=theme["panel"])
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
    style.configure("Panel.TLabel", background=theme["panel"], foreground=theme["fg"])
    style.configure(
        "Accent.TButton",
        background=theme["accent"],
        foreground=theme["bg"],
        padding=6,
        borderwidth=0,
    )
    style.map("Accent.TButton", background=[("active", theme["accent_hover"])])
