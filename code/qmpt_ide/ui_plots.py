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
        series_keys = [k for k in data.files if k != "t"]
        if not series_keys:
            self._write("Timeseries file has no plottable data.")
            return

        t = data["t"] if "t" in data else None
        selected = []
        # Prefer classical keys if present, otherwise take first metrics.
        for pref in ["stress", "protection", "novelty", "expectation_mean", "entropy", "anomaly_proxy"]:
            if pref in series_keys and pref not in selected:
                selected.append(pref)
        for k in series_keys:
            if k not in selected and len(selected) < 3:
                selected.append(k)
        if len(selected) > 3:
            selected = selected[:3]

        fig, ax = plt.subplots(len(selected), 1, figsize=(5, 4 + len(selected)))
        if len(selected) == 1:
            ax = [ax]
        for idx, key in enumerate(selected):
            y = data[key]
            if t is not None and len(t) == len(y):
                ax[idx].plot(t, y, label=key)
                ax[idx].set_xlabel("t")
            else:
                ax[idx].plot(y, label=key)
            ax[idx].set_ylabel(key)
            ax[idx].legend()
        fig.tight_layout()
        img_path = result_dir / "plot.png"
        fig.savefig(img_path)
        plt.close(fig)
        note = f"Plot saved to {img_path}"
        # If run belongs to a dataset, surface ensemble summary
        ds_note = ""
        ds_id = getattr(self.state.current_run, "dataset_id", None)
        if ds_id:
            ds_metrics = result_dir.parents[2] / "datasets" / ds_id / "ensemble_metrics.json"
            if ds_metrics.exists():
                try:
                    import json

                    summary = json.loads(ds_metrics.read_text(encoding="utf-8"))
                    ds_note = f"\nDataset {ds_id}: {summary}"
                except Exception:
                    ds_note = f"\nDataset {ds_id}: (could not read ensemble metrics)"
        self._write(note + ds_note)

    def _write(self, text: str) -> None:
        self.canvas.configure(state="normal")
        self.canvas.delete("1.0", tk.END)
        self.canvas.insert(tk.END, text)
        self.canvas.configure(state="disabled")
