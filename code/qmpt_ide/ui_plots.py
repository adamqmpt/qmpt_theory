"""
Plotting helpers using matplotlib if available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk


try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

import numpy as np

from .state import AppState


class PlotPanel(ttk.Frame):
    def __init__(self, master: tk.Widget, state: AppState):
        super().__init__(master, padding=8)
        self.state = state
        self.label = ttk.Label(self, text="Plots (matplotlib required)")
        self.label.pack(anchor=tk.W)
        self.canvas = tk.Text(
            self,
            bg=self.state.config.theme["bg"],
            fg=self.state.config.theme["muted"],
            height=8,
            state="disabled",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def show(self, result_dir: Path) -> None:
        if plt is None or not self.state.config.matplotlib_enabled:
            self._write("Plotting disabled (matplotlib not available).")
            return
        npz_path = result_dir / "timeseries.npz"
        if not npz_path.exists():
            self._write("No timeseries available to plot.")
            return
        data = np.load(npz_path)
        t = data["t"]
        fig, ax = plt.subplots(3, 1, figsize=(5, 5))
        ax[0].plot(t, data["stress"], label="stress")
        ax[0].set_ylabel("σ_k")
        ax[1].plot(t, data["protection"], label="protection", color="orange")
        ax[1].set_ylabel("P_k")
        ax[2].plot(t, data["novelty"], label="novelty", color="green")
        ax[2].set_ylabel("novelty")
        ax[2].set_xlabel("t")
        fig.tight_layout()
        img_path = result_dir / "plot.png"
        fig.savefig(img_path)
        plt.close(fig)
        self._write(f"Plot saved to {img_path}")

    def _write(self, text: str) -> None:
        self.canvas.configure(state="normal")
        self.canvas.delete("1.0", tk.END)
        self.canvas.insert(tk.END, text)
        self.canvas.configure(state="disabled")
