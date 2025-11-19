"""
Tkinter-based dark-theme IDE for QMPT lab usage (v0.1).
Features:
- document browser for core markdown files,
- read-only viewer,
- note editor saved under lab/notes,
- status/log pane.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from .config import IDEConfig, load_config
from .state import WorkspaceState, repo_root
from .theme import DARK_THEME, FONT_BASE, FONT_MONO, FONT_TITLE
from . import __version__
from .sim_runner import SimulationRequest, run_simulation


class IdeApp:
    def __init__(self, config: Optional[IDEConfig] = None, state: Optional[WorkspaceState] = None):
        self.config = config or load_config()
        self.state = state or WorkspaceState()
        self.state.ensure_dirs()
        self.root = tk.Tk()
        self.root.title(f"{self.config.title} v{self.config.version}")
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.configure(bg=self.config.theme["bg"])

        self._build_styles()
        self._build_layout()
        self._populate_docs()
        if self.config.enable_simulation_stub:
            self._populate_simulation_stub()

    def _build_styles(self) -> None:
        """Create ttk styles aligned with the dark theme."""
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "TFrame",
            background=self.config.theme["bg"],
            bordercolor=self.config.theme["border"],
        )
        style.configure(
            "Sidebar.TFrame",
            background=self.config.theme["panel"],
            bordercolor=self.config.theme["border"],
        )
        style.configure(
            "TLabel",
            background=self.config.theme["bg"],
            foreground=self.config.theme["fg"],
            font=FONT_BASE,
        )
        style.configure(
            "Sidebar.TLabel",
            background=self.config.theme["panel"],
            foreground=self.config.theme["fg"],
            font=FONT_TITLE,
        )
        style.configure(
            "Accent.TButton",
            background=self.config.theme["accent"],
            foreground=self.config.theme["bg"],
            font=FONT_BASE,
            borderwidth=0,
            padding=6,
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.config.theme["accent_hover"])],
        )

    def _build_layout(self) -> None:
        """Construct main frames and widgets."""
        # Sidebar frame
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", width=260, padding=8)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        lbl_docs = ttk.Label(sidebar, text="Documents", style="Sidebar.TLabel")
        lbl_docs.pack(anchor=tk.W, pady=(0, 6))

        self.doc_list = tk.Listbox(
            sidebar,
            bg=self.config.theme["panel"],
            fg=self.config.theme["fg"],
            selectbackground=self.config.theme["accent"],
            selectforeground=self.config.theme["bg"],
            activestyle="none",
            highlightthickness=1,
            highlightcolor=self.config.theme["border"],
            highlightbackground=self.config.theme["border"],
        )
        self.doc_list.pack(fill=tk.BOTH, expand=True)
        self.doc_list.bind("<<ListboxSelect>>", self._on_doc_select)

        btn_refresh = ttk.Button(
            sidebar,
            text="Refresh",
            style="Accent.TButton",
            command=self._populate_docs,
        )
        btn_refresh.pack(fill=tk.X, pady=(10, 4))

        btn_open = ttk.Button(
            sidebar,
            text="Open file...",
            style="Accent.TButton",
            command=self._open_external,
        )
        btn_open.pack(fill=tk.X)

        # Main content frame
        main = ttk.Frame(self.root, style="TFrame", padding=10)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title_wrapper = ttk.Frame(main, style="TFrame")
        title_wrapper.pack(fill=tk.X)
        self.title_label = ttk.Label(
            title_wrapper, text="Select a document to view", font=FONT_TITLE
        )
        self.title_label.pack(side=tk.LEFT, anchor=tk.W)

        viewer_frame = ttk.Frame(main, style="TFrame")
        viewer_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        self.viewer = tk.Text(
            viewer_frame,
            wrap=tk.WORD,
            bg=self.config.theme["bg"],
            fg=self.config.theme["fg"],
            font=FONT_MONO,
            insertbackground=self.config.theme["fg"],
            highlightthickness=0,
            borderwidth=1,
            relief=tk.FLAT,
        )
        self.viewer.configure(state="disabled")
        scrollbar = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL, command=self.viewer.yview)
        self.viewer.configure(yscrollcommand=scrollbar.set)
        self.viewer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Notes panel
        notes_frame = ttk.Frame(main, style="TFrame")
        notes_frame.pack(fill=tk.X, pady=(4, 8))

        ttk.Label(notes_frame, text="Note name:", font=FONT_BASE).pack(side=tk.LEFT)
        self.note_name_var = tk.StringVar(value="session_notes")
        self.note_entry = ttk.Entry(notes_frame, textvariable=self.note_name_var, width=30)
        self.note_entry.pack(side=tk.LEFT, padx=(6, 12))

        save_btn = ttk.Button(
            notes_frame, text="Save note", style="Accent.TButton", command=self._save_note
        )
        save_btn.pack(side=tk.LEFT)

        template_btn = ttk.Button(
            notes_frame, text="Insert template", style="Accent.TButton", command=self._insert_template
        )
        template_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.note_editor = tk.Text(
            main,
            wrap=tk.WORD,
            bg=self.config.theme["panel"],
            fg=self.config.theme["fg"],
            font=FONT_MONO,
            insertbackground=self.config.theme["fg"],
            height=10,
            highlightthickness=1,
            highlightbackground=self.config.theme["border"],
        )
        self.note_editor.pack(fill=tk.BOTH, expand=False)
        self.note_editor.bind("<<Modified>>", self._on_note_changed)

        # Note preview
        ttk.Label(main, text="Preview", font=FONT_TITLE).pack(anchor=tk.W)
        self.note_preview = tk.Text(
            main,
            wrap=tk.WORD,
            bg=self.config.theme["bg"],
            fg=self.config.theme["fg"],
            font=FONT_MONO,
            insertbackground=self.config.theme["fg"],
            height=10,
            highlightthickness=1,
            highlightbackground=self.config.theme["border"],
            state="disabled",
        )
        self.note_preview.pack(fill=tk.BOTH, expand=False, pady=(4, 8))

        # Simulation panel
        self.sim_frame = ttk.Frame(main, style="TFrame")
        self.sim_frame.pack(fill=tk.X, pady=(8, 4))
        ttk.Label(self.sim_frame, text="Simulation launcher", font=FONT_TITLE).pack(
            anchor=tk.W
        )

        sim_controls = ttk.Frame(self.sim_frame, style="TFrame")
        sim_controls.pack(fill=tk.X, pady=(4, 4))

        ttk.Label(sim_controls, text="Config:", font=FONT_BASE).grid(row=0, column=0, sticky="w")
        self.sim_config_var = tk.StringVar()
        self.sim_config_combo = ttk.Combobox(
            sim_controls, textvariable=self.sim_config_var, state="readonly", width=40
        )
        self.sim_config_combo.grid(row=0, column=1, padx=6, pady=2, sticky="w")

        ttk.Label(sim_controls, text="Seed:", font=FONT_BASE).grid(row=1, column=0, sticky="w")
        self.seed_var = tk.StringVar(value=str(self.config.default_seed))
        ttk.Entry(sim_controls, textvariable=self.seed_var, width=10).grid(
            row=1, column=1, sticky="w", padx=6, pady=2
        )

        ttk.Label(sim_controls, text="Device:", font=FONT_BASE).grid(row=2, column=0, sticky="w")
        self.device_var = tk.StringVar(value=self.config.default_device)
        ttk.Combobox(
            sim_controls,
            textvariable=self.device_var,
            values=["cpu", "gpu"],
            width=10,
            state="readonly",
        ).grid(row=2, column=1, sticky="w", padx=6, pady=2)

        run_btn = ttk.Button(
            sim_controls, text="Run simulation", style="Accent.TButton", command=self._run_simulation
        )
        run_btn.grid(row=0, column=2, rowspan=3, padx=8, pady=2)

        scan_btn = ttk.Button(
            sim_controls, text="Rescan configs", style="Accent.TButton", command=self._populate_configs
        )
        scan_btn.grid(row=0, column=3, rowspan=3, padx=8, pady=2)

        self.sim_status = tk.StringVar(value="Ready")
        ttk.Label(self.sim_frame, textvariable=self.sim_status, font=FONT_BASE).pack(
            anchor=tk.W
        )

        # Status/log
        status_frame = ttk.Frame(main, style="TFrame")
        status_frame.pack(fill=tk.X, pady=(6, 0))
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_var, font=FONT_BASE
        )
        self.status_label.pack(side=tk.LEFT)

        version_label = ttk.Label(
            status_frame,
            text=f"v{__version__}",
            font=FONT_BASE,
            foreground=self.config.theme["muted"],
        )
        version_label.pack(side=tk.RIGHT)

    def _populate_docs(self, *_args) -> None:
        """Refresh document list from configured roots."""
        self.doc_list.delete(0, tk.END)
        docs = self.state.discover_docs(self.config.doc_roots, limit=self.config.max_recent_docs)
        self.docs = docs
        for path in docs:
            rel = path.relative_to(repo_root())
            self.doc_list.insert(tk.END, str(rel))
        self.status_var.set(f"Loaded {len(docs)} documents")

    def _populate_simulation_stub(self) -> None:
        """Placeholder for future simulation launcher."""
        try:
            cfg_dir = repo_root() / "config"
            available = sorted(p.name for p in cfg_dir.glob("*.yaml")) + sorted(
                p.name for p in cfg_dir.glob("*.json")
            )
            if available:
                self.sim_status.set(
                    f"Configs detected ({len(available)}): " + ", ".join(available[:5]) +
                    (" ..." if len(available) > 5 else "")
                )
            else:
                self.sim_status.set("No simulation configs found in config/.")
        except Exception:
            self.sim_status.set("Simulation stub could not scan configs.")

    def _on_doc_select(self, _event=None) -> None:
        """Load the selected document into the viewer."""
        if not hasattr(self, "docs"):
            return
        selection = self.doc_list.curselection()
        if not selection:
            return
        idx = selection[0]
        path = self.docs[idx]
        self._load_doc(path)

    def _open_external(self) -> None:
        """Open a file chooser and load a document."""
        filename = filedialog.askopenfilename(
            title="Open Markdown or text file",
            initialdir=repo_root(),
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self._load_doc(Path(filename))

    def _load_doc(self, path: Path) -> None:
        """Read and display a document in the viewer."""
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Could not read {path.name}: {exc}")
            return
        self.viewer.configure(state="normal")
        self.viewer.delete("1.0", tk.END)
        self.viewer.insert(tk.END, content)
        self.viewer.configure(state="disabled")
        self.title_label.configure(text=str(path.relative_to(repo_root())))
        self.status_var.set(f"Viewing {path.name}")
        self.state.add_recent(path, self.config.max_recent_docs)

    def _save_note(self) -> None:
        """Persist note content under lab/notes."""
        name = self.note_name_var.get().strip() or "note"
        safe_name = name.replace(" ", "_")
        target = self.state.notes_dir / f"{safe_name}.md"
        try:
            target.write_text(self.note_editor.get("1.0", tk.END).strip() + "\n", encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Could not save note: {exc}")
            return
        self.status_var.set(f"Saved note to {target.relative_to(repo_root())}")

    def _insert_template(self) -> None:
        """Insert experiment template with current config/seed/device."""
        template = self.config.note_template
        templated = template.format(
            config=self.sim_config_var.get() or "<config>",
            seed=self.seed_var.get(),
            device=self.device_var.get(),
        )
        self.note_editor.insert("1.0", templated)

    def _on_note_changed(self, _event=None) -> None:
        """Render markdown-like preview of the note editor."""
        self.note_editor.edit_modified(0)
        content = self.note_editor.get("1.0", tk.END)
        self._render_preview(content)

    def _render_preview(self, content: str) -> None:
        """Very lightweight markdown/math preview."""
        self.note_preview.configure(state="normal")
        self.note_preview.delete("1.0", tk.END)
        self.note_preview.insert(tk.END, content)

        # Configure tags
        h1_font = tkfont.Font(self.note_preview, self.note_preview.cget("font"))
        h1_font.configure(size=13, weight="bold")
        h2_font = tkfont.Font(self.note_preview, self.note_preview.cget("font"))
        h2_font.configure(size=12, weight="bold")
        math_font = tkfont.Font(self.note_preview, self.note_preview.cget("font"))
        math_font.configure(slant="italic")

        self.note_preview.tag_configure("h1", font=h1_font)
        self.note_preview.tag_configure("h2", font=h2_font)
        self.note_preview.tag_configure("math", font=math_font, foreground=self.config.theme["accent"])

        # Apply heading tags
        idx = "1.0"
        while True:
            line_start = f"{idx.split('.')[0]}.0"
            line = self.note_preview.get(line_start, f"{line_start} lineend")
            if not line:
                break
            if line.startswith("# "):
                self.note_preview.tag_add("h1", line_start, f"{line_start} lineend")
            elif line.startswith("## "):
                self.note_preview.tag_add("h2", line_start, f"{line_start} lineend")
            # Next line
            next_line_num = int(line_start.split(".")[0]) + 1
            if next_line_num > int(float(self.note_preview.index(tk.END))):
                break
            idx = f"{next_line_num}.0"

        # Apply math tag for $...$
        import re

        for match in re.finditer(r"\$(.+?)\$", content, re.DOTALL):
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            self.note_preview.tag_add("math", start_idx, end_idx)

        self.note_preview.configure(state="disabled")

    def _populate_configs(self) -> None:
        """Scan available simulation config files."""
        configs = []
        for pattern in self.config.simulation_config_globs:
            configs.extend(Path(repo_root()).glob(pattern))
        configs = [p for p in configs if p.is_file()]
        configs = sorted(set(configs))
        self.sim_configs = configs
        self.sim_config_combo["values"] = [str(p.relative_to(repo_root())) for p in configs]
        if configs:
            self.sim_config_combo.current(0)
            self.sim_status.set(f"Configs ready ({len(configs)} found).")
        else:
            self.sim_status.set("No configs found in config/.")

    def _run_simulation(self) -> None:
        """Run placeholder simulation and log results."""
        if not hasattr(self, "sim_configs") or not self.sim_configs:
            self.sim_status.set("No configs to run.")
            return
        selected = self.sim_config_combo.get()
        if not selected:
            self.sim_status.set("Select a config first.")
            return
        config_path = repo_root() / selected
        try:
            seed = int(self.seed_var.get())
        except ValueError:
            self.sim_status.set("Seed must be an integer.")
            return
        req = SimulationRequest(
            config_path=config_path,
            seed=seed,
            device=self.device_var.get() or "cpu",
        )
        try:
            result = run_simulation(req, self.state)
        except Exception as exc:  # noqa: BLE001
            self.sim_status.set(f"Run failed: {exc}")
            return
        self.sim_status.set(
            f"Run ok: {result.metrics} (log {result.log_path.relative_to(repo_root())})"
        )

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = IdeApp()
    app._populate_configs()
    app.run()


if __name__ == "__main__":
    main()
