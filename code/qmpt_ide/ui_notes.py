"""
Note editor with simple Markdown preview.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk
from typing import Optional

from .state import AppState
from .state import repo_root


class NotesPanel(ttk.Frame):
    def __init__(self, master: tk.Widget, state: AppState):
        super().__init__(master, padding=8)
        self.state = state

        control = ttk.Frame(self)
        control.pack(fill=tk.X)
        ttk.Label(control, text="Note name:").pack(side=tk.LEFT)
        self.note_name = tk.StringVar(value="note")
        ttk.Entry(control, textvariable=self.note_name, width=28).pack(side=tk.LEFT, padx=6)
        ttk.Button(control, text="Save", command=self._save).pack(side=tk.LEFT, padx=4)

        self.editor = tk.Text(
            self,
            wrap=tk.WORD,
            bg=self.state.config.theme["panel"],
            fg=self.state.config.theme["fg"],
            insertbackground=self.state.config.theme["fg"],
            height=10,
        )
        self.editor.pack(fill=tk.BOTH, expand=True, pady=6)
        self.editor.bind("<<Modified>>", self._on_change)

        ttk.Label(self, text="Preview").pack(anchor=tk.W)
        self.preview = tk.Text(
            self,
            wrap=tk.WORD,
            bg=self.state.config.theme["bg"],
            fg=self.state.config.theme["fg"],
            state="disabled",
            height=8,
        )
        self.preview.pack(fill=tk.BOTH, expand=True)

    def _save(self) -> None:
        name = self.note_name.get().strip() or "note"
        safe_name = name.replace(" ", "_")
        notes_dir = repo_root() / self.state.config.notes_dir
        notes_dir.mkdir(parents=True, exist_ok=True)
        target = notes_dir / f"{safe_name}.md"
        target.write_text(self.editor.get("1.0", tk.END), encoding="utf-8")

    def _on_change(self, _event=None) -> None:
        self.editor.edit_modified(0)
        content = self.editor.get("1.0", tk.END)
        self._render_preview(content)

    def _render_preview(self, content: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", tk.END)
        self.preview.insert(tk.END, content)
        h1_font = tkfont.Font(self.preview, self.preview.cget("font"))
        h1_font.configure(size=13, weight="bold")
        self.preview.tag_configure("h1", font=h1_font)
        lines = content.splitlines()
        pos = 1
        for line in lines:
            if line.startswith("# "):
                self.preview.tag_add("h1", f"{pos}.0", f"{pos}.end")
            pos += 1
        self.preview.configure(state="disabled")
