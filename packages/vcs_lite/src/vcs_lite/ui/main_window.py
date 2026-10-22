"""Main window E-01 after the reference: toolbar, repositories, files, commit panel, status bar.

Trace: DES-VCS-022, DES-VCS-024, DES-VCS-026, DES-VCS-045, DES-VCS-042, DES-VCS-043, REQ-VCS-002, REQ-VCS-021, REQ-VCS-022, REQ-VCS-025, E-01, E-02
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from vcs_lite.app.model import AppModel
from vcs_lite.ui import theme
from vcs_lite.ui.file_list import FileList
from vcs_lite.ui.settings_dialog import RepoDialog
from vcs_lite.ui.sidebar import RepoSidebar
from vcs_lite.ui.widgets import Pill, Tooltip, kbd

C, S = theme.COLORS, theme.SPACE
PLACEHOLDER = "Opis zmian…   ⌘↩ commit · ⌘⇧↩ commit i push"


def hline(parent: tk.Misc) -> tk.Frame:
    return tk.Frame(parent, height=S["line"], bg=C["line"])


def button(parent: tk.Misc, text: str, parent_bg: str, **options) -> tk.Button:
    """Native aqua button; highlightbackground paints its surroundings in the parent's colour.
    ttk.Button would paint them in the system window colour and leave a visible box (DEC-VCS-047)."""
    return tk.Button(parent, text=text, highlightbackground=parent_bg, **options)


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Misc, model: AppModel):
        super().__init__(master, bg=C["bg"])
        self.model = model
        self._shown_repo: str | None = None
        self.settings_dialog: RepoDialog | None = None
        self._placeholder = False
        self._build()
        model.subscribe(self.render)
        self.render()

    # ---------- layout ----------

    def _build(self) -> None:
        self._build_toolbar().pack(fill=tk.X)
        hline(self).pack(fill=tk.X)
        self._build_status_bar().pack(side=tk.BOTTOM, fill=tk.X)
        hline(self).pack(side=tk.BOTTOM, fill=tk.X)
        self._build_commit_panel().pack(side=tk.BOTTOM, fill=tk.X)
        hline(self).pack(side=tk.BOTTOM, fill=tk.X)
        self._build_middle().pack(fill=tk.BOTH, expand=True)

    def _build_toolbar(self) -> tk.Frame:
        px, py = S["toolbar_pad"]
        bar = tk.Frame(self, bg=C["panel"], padx=px, pady=py)
        self.repo_title = theme.label(bar, "toolbar_repo", bg=C["panel"])
        self.repo_title.pack(side=tk.LEFT)
        self.branch_chip = Pill(bar, role="chip", fill=C["chip_bg"], pad=S["chip_pad"], parent_bg=C["panel"])
        self.branch_chip.pack(side=tk.LEFT, padx=(S["toolbar_gap"], 0))
        self.refresh_button = button(bar, "⟳ Odśwież", C["panel"], command=self.model.refresh_all)
        self.refresh_button.pack(side=tk.RIGHT)
        self.pull_button = button(bar, "⇣ Pull", C["panel"], command=self.model.pull)
        self.pull_button.pack(side=tk.RIGHT, padx=(0, S["toolbar_gap"]))
        self.show_folders = tk.BooleanVar(value=self.model.show_folders)
        self.folders_check = tk.Checkbutton(bar, text="Pokaż foldery", variable=self.show_folders,
                                            command=self.toggle_folders, bg=C["panel"], highlightbackground=C["panel"],
                                            font=theme.font("body"), fg=C["ink"])  # native checkbox (DEC-VCS-055)
        self.folders_check.pack(side=tk.RIGHT, padx=(0, S["toolbar_gap"]))
        Tooltip(self.pull_button, lambda: self.model.pull_disabled_reason)
        return bar

    def _build_middle(self) -> tk.Frame:
        middle = tk.Frame(self, bg=C["bg"])
        sidebar = tk.Frame(middle, bg=C["sidebar"], width=S["sidebar_width"])
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        tk.Frame(middle, width=S["line"], bg=C["line"]).pack(side=tk.LEFT, fill=tk.Y)
        self._build_repo_list(sidebar)
        files = tk.Frame(middle, bg=C["bg"])
        files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_list = FileList(files, on_toggle=self.model.toggle, on_activate=self.model.activate,
                                  on_toggle_folder=self.model.toggle_folder, on_empty_action=self._empty_action)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        return middle

    def _build_repo_list(self, sidebar: tk.Frame) -> None:
        foot = tk.Frame(sidebar, bg=C["sidebar"], padx=S["side_foot_pad"], pady=S["side_foot_pad"])
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        self.settings_button = button(foot, "⚙ Repozytoria…", C["sidebar"], command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT)
        self.sidebar = RepoSidebar(sidebar, on_select=self.model.select)
        self.sidebar.pack(fill=tk.BOTH, expand=True)

    def _build_commit_panel(self) -> tk.Frame:
        px, py = S["commit_pad"]
        gap_x, gap_y = S["commit_gap"]
        panel = tk.Frame(self, bg=C["panel"], padx=px, pady=py)
        box = tk.Frame(panel, bg=C["bg"], highlightthickness=S["line"], highlightbackground=C["control_border"],
                       highlightcolor=C["accent"])
        box.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, gap_x))
        mx, my = S["message_pad"]
        self.message_box = tk.Text(box, height=3, wrap=tk.WORD, undo=True, bd=0, highlightthickness=0,
                                   font=theme.font("message"), fg=C["ink"], bg=C["bg"], padx=mx, pady=my,
                                   insertbackground=C["ink"])
        self.message_box.pack(fill=tk.BOTH, expand=True)
        self.message_box.bind("<FocusIn>", self._message_focus_in)
        self.message_box.bind("<FocusOut>", self._message_focus_out)
        self.message_box.bind("<KeyRelease>", lambda _e: self._sync_message())
        buttons = tk.Frame(panel, bg=C["panel"])
        buttons.grid(row=0, column=1, sticky=tk.N)
        self.commit_button = button(buttons, "Commit", C["panel"], default="active", command=self.model.commit)
        self.commit_button.pack(fill=tk.X)
        self.commit_push_button = button(buttons, "Commit & Push", C["panel"], command=self.model.commit_and_push)
        self.commit_push_button.pack(fill=tk.X, pady=(S["commit_buttons_gap"], 0))
        Tooltip(self.commit_push_button, lambda: self.model.commit_and_push_disabled_reason)
        self.reason = theme.label(panel, "reason", bg=C["panel"], anchor=tk.W)
        self.reason.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(gap_y, 0))
        self.reason.grid_remove()  # shown only while commit is not possible (UI-REFERENCE §4)
        panel.columnconfigure(0, weight=1)
        return panel

    def _build_status_bar(self) -> tk.Frame:
        px, py = S["statusbar_pad"]
        gap = S["statusbar_gap"]
        bar = tk.Frame(self, bg=C["chrome"], padx=px, pady=py)
        self.refreshed = theme.label(bar, "statusbar", bg=C["chrome"])
        self.refreshed.pack(side=tk.LEFT, padx=(0, gap))
        theme.label(bar, "statusbar", "Dwuklik: porównanie w Beyond Compare", bg=C["chrome"]).pack(side=tk.LEFT, padx=(0, gap))
        kbd(bar, "⌘1", C["chrome"]).pack(side=tk.LEFT)
        theme.label(bar, "statusbar", "–", bg=C["chrome"]).pack(side=tk.LEFT)
        kbd(bar, "⌘9", C["chrome"]).pack(side=tk.LEFT)
        theme.label(bar, "statusbar", " wybór repo", bg=C["chrome"]).pack(side=tk.LEFT)
        return bar

    # ---------- the message field ----------

    def _message_text(self) -> str:
        return "" if self._placeholder else self.message_box.get("1.0", "end-1c")

    def _show_placeholder(self) -> None:
        self._placeholder = True
        self.message_box.delete("1.0", tk.END)
        self.message_box.insert("1.0", PLACEHOLDER)
        self.message_box.configure(fg=C["dim"])

    def _hide_placeholder(self) -> None:
        if self._placeholder:
            self._placeholder = False
            self.message_box.delete("1.0", tk.END)
            self.message_box.configure(fg=C["ink"])

    def _message_focus_in(self, _event=None) -> None:
        self._hide_placeholder()

    def _message_focus_out(self, _event=None) -> None:
        if not self._message_text():
            self._show_placeholder()

    def _sync_message(self) -> None:
        if not self._placeholder:
            self.model.message = self._message_text()

    def type_message(self, text: str) -> None:
        """Replace the message as if typed by the user."""
        self._hide_placeholder()
        self.message_box.delete("1.0", tk.END)
        self.message_box.insert("1.0", text)
        self._sync_message()

    def _load_draft(self) -> None:
        if self.model.message:
            self._hide_placeholder()
            self.message_box.delete("1.0", tk.END)
            self.message_box.insert("1.0", self.model.message)
        elif self.focus_get() is not self.message_box:
            self._show_placeholder()

    def toggle_folders(self) -> None:
        self.model.show_folders = self.show_folders.get()

    def open_settings(self) -> RepoDialog:
        if self.settings_dialog is None:
            self.settings_dialog = RepoDialog(self, self.model, on_close=self._settings_closed)
        else:
            self.settings_dialog.lift()
        return self.settings_dialog

    def _settings_closed(self) -> None:
        self.settings_dialog = None

    def _empty_action(self, action: str) -> None:
        if action == "choose_repos":
            self.open_settings()
        elif action == "recheck" and self.model.selected:
            self.model.refresh(self.model.selected)

    # ---------- drawing the model ----------

    def render(self) -> None:
        self.winfo_toplevel().title(self.model.window_title)
        self._render_toolbar()
        self.sidebar.render(self.model)
        self.file_list.render(self.model)
        self._render_commit_panel()
        self.refreshed.configure(text=self.model.refreshed_label)

    def _render_toolbar(self) -> None:
        self.repo_title.configure(text=self.model.selected or "")
        self.branch_chip.set(self.model.branch_summary)
        self.pull_button.configure(state=tk.NORMAL if self.model.can_pull else tk.DISABLED)

    def _render_commit_panel(self) -> None:
        if self._shown_repo != self.model.selected:
            self._shown_repo = self.model.selected
            self._load_draft()
        self.commit_button.configure(text=self.model.commit_label,
                                     state=tk.NORMAL if self.model.can_commit else tk.DISABLED)
        self.commit_push_button.configure(state=tk.NORMAL if self.model.can_commit_and_push else tk.DISABLED)
        reason = self.model.commit_disabled_reason
        self.reason.configure(text=f"ⓘ {reason}" if reason else "")
        if reason:
            self.reason.grid()
        else:
            self.reason.grid_remove()
