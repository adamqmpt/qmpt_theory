"""
Main layout combining docs, notes, runs, and plots.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .ui_docs import DocBrowser
from .ui_notes import NotesPanel
from .ui_runs import RunsPanel
from .ui_plots import PlotPanel
from .state import AppState


class MainWindow(ttk.Frame):
    def __init__(self, root: tk.Tk, state: AppState):
        super().__init__(root)
        self.state = state

        # Left: documents
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="Documents").pack(anchor=tk.W, padx=8, pady=4)
        self.browser = DocBrowser(left, state, on_select=self._open_doc)
        self.browser.pack(fill=tk.BOTH, expand=True)
        self.viewer = tk.Text(
            left,
            bg=self.state.config.theme["bg"],
            fg=self.state.config.theme["fg"],
            wrap=tk.WORD,
        )
        self.viewer.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Right: notes + runs + plots
        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        notes = NotesPanel(right, state)
        notes.pack(fill=tk.BOTH, expand=True)

        self.plot_panel = PlotPanel(right, state)
        self.layer_panel = ttk.Frame(right)
        self.layer_panel.pack(fill=tk.BOTH, expand=True)
        from .ui_layer import LayerInspector

        self.layer_inspector = LayerInspector(self.layer_panel, state.config.theme)
        self.layer_inspector.pack(fill=tk.BOTH, expand=True)

        runs = RunsPanel(right, state, on_plot=self._plot_results)
        runs.pack(fill=tk.BOTH, expand=True)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

    def _open_doc(self, path):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            content = f"Failed to read {path}: {exc}"
        self.viewer.delete("1.0", tk.END)
        self.viewer.insert(tk.END, content)

    def _plot_results(self, result_dir):
        self.plot_panel.show(result_dir)
        dsid = getattr(self.state.current_run, "dataset_id", None) if self.state.current_run else None
        self.layer_inspector.load_run(result_dir, dataset_id=dsid)
