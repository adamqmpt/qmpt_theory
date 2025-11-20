"""
Run control panel, history, and log viewer.
"""

from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Optional

from .sim_runner import BackendType
from .state import AppState, repo_root


class RunsPanel(ttk.Frame):
    def __init__(self, master: tk.Widget, state: AppState, on_plot: Optional[callable] = None):
        super().__init__(master, padding=8)
        self.state = state
        self.on_plot = on_plot

        controls = ttk.Frame(self)
        controls.pack(fill=tk.X)
        ttk.Label(controls, text="Config:").grid(row=0, column=0, sticky="w")
        self.config_entry = ttk.Entry(controls, width=40)
        self.config_entry.grid(row=0, column=1, padx=4, pady=2, sticky="w")
        ttk.Label(controls, text="Backend:").grid(row=1, column=0, sticky="w")
        self.backend_var = tk.StringVar(value=self.state.config.default_backend)
        ttk.Combobox(
            controls,
            textvariable=self.backend_var,
            values=[b.value for b in BackendType],
            state="readonly",
            width=12,
        ).grid(row=1, column=1, padx=4, pady=2, sticky="w")
        ttk.Button(
            controls, text="Run", style="Accent.TButton", command=self._start_run
        ).grid(row=0, column=2, rowspan=2, padx=6)

        ttk.Label(self, text="Run history").pack(anchor=tk.W, pady=(8, 2))
        self.history = tk.Listbox(
            self,
            bg=self.state.config.theme["panel"],
            fg=self.state.config.theme["fg"],
            height=6,
            selectbackground=self.state.config.theme["accent"],
            selectforeground=self.state.config.theme["bg"],
        )
        self.history.pack(fill=tk.X)
        self.history.bind("<<ListboxSelect>>", self._select_history)

        ttk.Label(self, text="Log").pack(anchor=tk.W, pady=(8, 2))
        self.log_view = tk.Text(
            self,
            bg=self.state.config.theme["bg"],
            fg=self.state.config.theme["fg"],
            height=10,
            state="disabled",
            wrap=tk.WORD,
        )
        self.log_view.pack(fill=tk.BOTH, expand=True)

        self._refresh_history()

    def _refresh_history(self) -> None:
        self.history.delete(0, tk.END)
        for rec in self.state.registry.latest():
            ts = datetime.fromtimestamp(rec.timestamp).isoformat(timespec="seconds")
            self.history.insert(
                tk.END, f"{rec.run_id} [{rec.backend} {rec.status}] {ts}"
            )
        self.state.current_run = None

    def _start_run(self) -> None:
        config_rel = self.config_entry.get().strip()
        if not config_rel:
            messagebox.showerror("Error", "Select a config path")
            return
        backend = BackendType(self.backend_var.get())
        config_path = (repo_root() / config_rel).resolve()
        if not config_path.exists():
            messagebox.showerror("Error", f"Config not found: {config_path}")
            return
        threading.Thread(
            target=self._run_thread, args=(config_path, backend), daemon=True
        ).start()

    def _run_thread(self, config_path: Path, backend: BackendType) -> None:
        result = self.state.sim_runner.run(config_path, backend)
        self.state.registry.add(
            self.state.registry.__class__.__annotations__["RunRecord"](  # type: ignore
                run_id=result.run_id,
                timestamp=datetime.utcnow().timestamp(),
                config_path=str(config_path),
                backend=result.backend.value,
                status=result.status,
                log_path=str(result.log_path),
                results_path=str(result.results_path),
                metrics=result.metrics,
                git_commit=None,
                config_hash=None,
            )
        )
        self._refresh_history()
        self._show_log(result.log_path)
        if self.on_plot:
            self.on_plot(result.results_path)

    def _select_history(self, _event=None) -> None:
        idxs = self.history.curselection()
        if not idxs:
            return
        recs = self.state.registry.latest()
        try:
            rec = recs[idxs[0]]
        except IndexError:
            return
        self.state.current_run = rec
        self._show_log(Path(rec.log_path))
        if self.on_plot:
            self.on_plot(Path(rec.results_path))

    def _show_log(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            content = f"Cannot read log: {path}"
        self.log_view.configure(state="normal")
        self.log_view.delete("1.0", tk.END)
        self.log_view.insert(tk.END, content)
        self.log_view.configure(state="disabled")
