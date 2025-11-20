"""
Document browser and viewer.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, List

from .state import AppState, repo_root


class DocBrowser(ttk.Frame):
    def __init__(self, master: tk.Widget, state: AppState, on_select: Callable[[Path], None]):
        super().__init__(master, padding=8)
        self.state = state
        self.on_select = on_select
        self.listbox = tk.Listbox(
            self,
            bg=self.state.config.theme["panel"],
            fg=self.state.config.theme["fg"],
            highlightthickness=1,
            highlightbackground=self.state.config.theme["border"],
            selectbackground=self.state.config.theme["accent"],
            selectforeground=self.state.config.theme["bg"],
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._handle_select)
        self.refresh()

    def refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        docs = self._discover_docs()
        for path in docs:
            rel = path.relative_to(repo_root())
            self.listbox.insert(tk.END, str(rel))
        self.docs = docs

    def _discover_docs(self) -> List[Path]:
        root = repo_root()
        results: List[Path] = []
        for root_name in self.state.config.doc_roots:
            path = (root / root_name).resolve()
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
                results.append(path)
            elif path.is_dir():
                for p in path.rglob("*.md"):
                    results.append(p)
        return results

    def _handle_select(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        path = self.docs[idx]
        self.on_select(path)
