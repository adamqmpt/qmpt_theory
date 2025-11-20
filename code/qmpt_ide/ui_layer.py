"""
Layer / pattern inspector for QMPT results.
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import numpy as np


class LayerInspector(ttk.Frame):
    def __init__(self, master: tk.Widget, theme: dict):
        super().__init__(master, padding=8)
        self.theme = theme
        ttk.Label(self, text="Layer / Pattern Inspector").pack(anchor=tk.W)

        self.summary = tk.Text(
            self,
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            height=8,
            state="disabled",
            wrap=tk.WORD,
        )
        self.summary.pack(fill=tk.BOTH, expand=True)

        self.patterns = tk.Text(
            self,
            bg=self.theme["panel"],
            fg=self.theme["fg"],
            height=8,
            state="disabled",
            wrap=tk.WORD,
        )
        self.patterns.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

    def load_run(self, result_dir: Path) -> None:
        self._set_text(self.summary, "No data")
        self._set_text(self.patterns, "")
        metrics_path = result_dir / "metrics.json"
        patterns_path = result_dir / "patterns.json"
        timeseries_path = result_dir / "timeseries.npz"
        lines = []
        if metrics_path.exists():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                for k, v in metrics.items():
                    lines.append(f"{k}: {v}")
            except Exception:
                lines.append("Could not parse metrics.json")
        if timeseries_path.exists():
            try:
                data = np.load(timeseries_path)
                stress_max = float(np.max(data["stress"]))
                protection_min = float(np.min(data["protection"]))
                lines.append(f"stress_max: {stress_max:.3f}")
                lines.append(f"protection_min: {protection_min:.3f}")
            except Exception:
                lines.append("Could not parse timeseries.npz")
        self._set_text(self.summary, "\n".join(lines))

        if patterns_path.exists():
            try:
                pats = json.loads(patterns_path.read_text(encoding="utf-8"))
                pat_lines = []
                for p in pats:
                    pat_lines.append(
                        f"{p.get('pattern_id')}  A={p.get('anomaly_score')}  R={p.get('reflexivity')}  O_self={p.get('self_operator')}"
                    )
                self._set_text(self.patterns, "\n".join(pat_lines))
            except Exception:
                self._set_text(self.patterns, "Could not parse patterns.json")

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state="disabled")
