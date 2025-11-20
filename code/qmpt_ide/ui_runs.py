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

from .sim_runner import BackendType, RunResult
from .state import AppState, repo_root
from .core_runs import RunRecord


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

        # Ensemble controls
        ensemble_frame = ttk.Frame(self)
        ensemble_frame.pack(fill=tk.X, pady=(6, 0))
        self.ensemble_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ensemble_frame, text="Ensemble mode", variable=self.ensemble_var).grid(row=0, column=0, sticky="w")
        ttk.Label(ensemble_frame, text="n_runs").grid(row=0, column=1, padx=4)
        self.n_runs_entry = ttk.Entry(ensemble_frame, width=6)
        self.n_runs_entry.insert(0, "4")
        self.n_runs_entry.grid(row=0, column=2)
        ttk.Label(ensemble_frame, text="Dataset note").grid(row=0, column=3, padx=4)
        self.dataset_desc = ttk.Entry(ensemble_frame, width=25)
        self.dataset_desc.grid(row=0, column=4, padx=2, sticky="w")

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
        badge = {"classical": "C", "quantum": "Q", "hybrid": "H"}
        for rec in self.state.registry.latest():
            ts = datetime.fromtimestamp(rec.timestamp).isoformat(timespec="seconds")
            tag = badge.get(rec.backend, "?")
            ds = f" ds={rec.dataset_id}" if getattr(rec, "dataset_id", None) else ""
            self.history.insert(
                tk.END, f"{rec.run_id} [{tag}:{rec.backend} {rec.status}]{ds} {ts}"
            )
        self.state.current_run = None

    def _run_thread(self, config_path: Path, backend: BackendType) -> None:
        result = self.state.sim_runner.run(config_path, backend)
        self._record_run(result, config_path)
        self._refresh_history()
        self._show_log(result.log_path)
        if self.on_plot:
            self.on_plot(result.results_path)

    def _ensemble_thread(self, config_path: Path, backend: BackendType, overrides: dict) -> None:
        dataset_id, results = self.state.sim_runner.run_ensemble(config_path, backend, overrides)
        for res in results:
            res.dataset_id = dataset_id or res.dataset_id
            self._record_run(res, config_path)
        if results:
            self._refresh_history()
            self._show_log(results[-1].log_path)
            if self.on_plot:
                self.on_plot(results[-1].results_path)

    def _record_run(self, result: RunResult, config_path: Path) -> None:
        record = RunRecord(
            run_id=result.run_id,
            timestamp=datetime.utcnow().timestamp(),
            config_path=str(config_path),
            backend=result.backend.value,
            status=result.status,
            log_path=str(result.log_path),
            results_path=str(result.results_path),
            metrics=result.metrics,
            git_commit=result.git_commit,
            config_hash=result.config_hash,
            dataset_id=result.dataset_id,
        )
        self.state.registry.add(record)

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
        if self.ensemble_var.get():
            try:
                n_runs = int(self.n_runs_entry.get())
            except Exception:
                n_runs = 1
            desc = self.dataset_desc.get().strip()
            overrides = {"enabled": True, "n_runs": n_runs, "description": desc}
            threading.Thread(
                target=self._ensemble_thread, args=(config_path, backend, overrides), daemon=True
            ).start()
        else:
            threading.Thread(
                target=self._run_thread, args=(config_path, backend), daemon=True
            ).start()
