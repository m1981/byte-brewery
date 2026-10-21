"""Main window E-01: repository list, file area and commit bar, redrawn whenever AppModel changes.

Trace: DES-VCS-022, DES-VCS-023, DES-VCS-026, REQ-VCS-002, REQ-VCS-021, E-01
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from vcs_lite.app.model import AppModel


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Misc, model: AppModel):
        super().__init__(master, padding=8)
        self.model = model
        self._build()
        model.subscribe(self.render)
        self.render()

    # ---------- layout ----------

    def _build(self) -> None:
        columns = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        columns.pack(fill=tk.BOTH, expand=True)
        columns.add(self._build_repo_column(columns), weight=1)
        columns.add(self._build_file_column(columns), weight=3)
        self._build_commit_bar().pack(fill=tk.X, pady=(8, 0))

    def _build_repo_column(self, parent: tk.Misc) -> ttk.Frame:
        frame = ttk.Frame(parent)
        self.repo_list = ttk.Treeview(frame, columns=("name", "branch", "changes"), show="headings",
                                      selectmode="browse", height=12)
        for column, heading, width in (("name", "Repozytorium", 160), ("branch", "Gałąź", 110), ("changes", "Zmiany", 60)):
            self.repo_list.heading(column, text=heading)
            self.repo_list.column(column, width=width, stretch=column == "name")
        self.repo_list.pack(fill=tk.BOTH, expand=True)
        self.settings_button = ttk.Button(frame, text="Settings", state=tk.DISABLED)  # dialog arrives in UI-2
        self.settings_button.pack(anchor=tk.W, pady=(6, 0))
        return frame

    def _build_file_column(self, parent: tk.Misc) -> ttk.Frame:
        frame = ttk.Frame(parent)
        self.file_tree = ttk.Treeview(frame, show="tree", selectmode="browse")  # groups arrive in UI-3
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        return frame

    def _build_commit_bar(self) -> ttk.Frame:
        bar = ttk.Frame(self)
        self.branch_label = ttk.Label(bar, text="")
        self.branch_label.grid(row=0, column=0, sticky=tk.W)
        self.message_box = tk.Text(bar, height=3, width=60, wrap=tk.WORD, undo=True)
        self.message_box.grid(row=1, column=0, sticky=tk.EW, padx=(0, 8))
        buttons = ttk.Frame(bar)
        buttons.grid(row=1, column=1, sticky=tk.NE)
        self.commit_button = ttk.Button(buttons, text="Commit", state=tk.DISABLED)
        self.commit_push_button = ttk.Button(buttons, text="Commit & Push", state=tk.DISABLED)
        self.pull_button = ttk.Button(buttons, text="Pull", state=tk.DISABLED)
        self.refresh_button = ttk.Button(buttons, text="Refresh", command=self.model.refresh_all)
        for column, button in enumerate((self.commit_button, self.commit_push_button, self.pull_button, self.refresh_button)):
            button.grid(row=0, column=column, padx=2)
        self.reason_label = ttk.Label(bar, text="", foreground="gray")
        self.reason_label.grid(row=2, column=0, columnspan=2, sticky=tk.W)
        bar.columnconfigure(0, weight=1)
        return bar

    # ---------- drawing the model ----------

    def render(self) -> None:
        self._render_repo_list()
        self._render_commit_bar()

    def _render_repo_list(self) -> None:
        self.repo_list.delete(*self.repo_list.get_children())
        for name in self.model.repo_names:
            view = self.model.view(name)
            self.repo_list.insert("", tk.END, iid=name, values=(name, view.branch_label, view.change_count))

    def _render_commit_bar(self) -> None:
        self.commit_button.configure(text=self.model.commit_label,
                                     state=tk.NORMAL if self.model.can_commit else tk.DISABLED)
        self.reason_label.configure(text=self.model.commit_disabled_reason or "")
