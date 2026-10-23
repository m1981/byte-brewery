"""Main window E-01 after the reference: toolbar, repositories, files, commit panel, status bar.

Trace: DES-VCS-018, REQ-VCS-015, DEC-VCS-059, DES-VCS-022, DES-VCS-024, DES-VCS-026, DES-VCS-045, DES-VCS-042, DES-VCS-043, REQ-VCS-002, REQ-VCS-021, REQ-VCS-022, REQ-VCS-025, REQ-VCS-027, DEC-VCS-064, DEC-VCS-068, E-01, E-02
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from vcs_lite.app.model import AppModel
from vcs_lite.ui import theme
from vcs_lite.ui.file_list import FileList
from vcs_lite.ui.settings_dialog import RepoDialog
from vcs_lite.ui.sidebar import RepoSidebar
from vcs_lite.ui.widgets import Pill, Tooltip, kbd, rounded_rect

C, S = theme.COLORS, theme.SPACE
PLACEHOLDER = "Opis zmian…   ⌘↩ commit · ⌘⇧↩ commit i push"
FOCUS_REFRESH_MS = 300  # several focus events on the way back give one refresh (DES-VCS-018)


def hline(parent: tk.Misc) -> tk.Frame:
    return tk.Frame(parent, height=S["line"], bg=C["line"])


def button(parent: tk.Misc, text: str, parent_bg: str, **options) -> tk.Button:
    """Native aqua button; highlightbackground paints its surroundings in the parent's colour.
    ttk.Button would paint them in the system window colour and leave a visible box (DEC-VCS-047)."""
    return tk.Button(parent, text=text, highlightbackground=parent_bg, **options)


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Misc, model: AppModel, *, reduce_motion: bool = False):
        super().__init__(master, bg=C["bg"])
        self.model = model
        self._reduce_motion = reduce_motion
        self._busy_after: str | None = None   # pending after() of the animation
        self._busy_shown = False
        self._busy_phase = 0
        self._shown_repo: str | None = None
        self.settings_dialog: RepoDialog | None = None
        self._placeholder = False
        self._away = False                     # the focus left the app (DEC-VCS-059)
        self._focus_after: str | None = None   # pending refresh after coming back
        self._build()
        self._bind_shortcuts()
        self._bind_focus_refresh()
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
        self.conflict_chip = Pill(bar, role="conflict_chip", fill=C["conf_soft"], pad=S["chip_pad"], parent_bg=C["panel"])  # P2
        self.merge_chip = Pill(bar, role="merge_chip", fill=C["accent_soft"], pad=S["chip_pad"], parent_bg=C["panel"])  # P11
        self.busy_text = theme.label(bar, "busy_text", bg=C["panel"])  # P4
        self.busy_text.pack(side=tk.LEFT, padx=(S["toolbar_gap"], 0))
        self.busy_bar = tk.Canvas(bar, height=S["busy_bar_height"], bg=C["panel"], highlightthickness=0, bd=0)
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
        self._build_banner(files)
        self.file_list = FileList(files, on_toggle=self.model.toggle, on_activate=self.model.activate,
                                  on_toggle_folder=self.model.toggle_folder, on_empty_action=self._empty_action)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        return middle

    def _build_banner(self, parent: tk.Frame) -> None:
        """P3: the failed operation and git's own message, above the file list; hidden until needed.
        A canvas draws the 8 pt corners and the red left edge (DEC-VCS-064); the content sits on it."""
        self.banner = tk.Canvas(parent, bg=C["bg"], highlightthickness=0, bd=0, height=1)
        content = self._banner_content = tk.Frame(self.banner, bg=C["conf_soft"])
        pad_left, pad_top = S["banner_pad"]
        self.banner.create_window(S["banner_edge"] + pad_left, pad_top, anchor=tk.NW, window=content,
                                  tags=("banner_content",))
        self.banner.bind("<Configure>", lambda _e: self._draw_banner())
        content.bind("<Configure>", lambda _e: self._draw_banner())
        theme.label(content, "banner_title", "⚠", bg=C["conf_soft"]).grid(row=0, column=0, sticky=tk.NW, padx=(0, 10))
        self.banner_title = theme.label(content, "banner_title", bg=C["conf_soft"], anchor=tk.W)
        self.banner_title.grid(row=0, column=1, sticky=tk.W)
        close = theme.label(content, "empty_sub", "×", bg=C["conf_soft"], cursor="hand2")
        close.configure(font=theme.font("folder_act"))
        close.grid(row=0, column=2, sticky=tk.NE)
        close.bind("<Button-1>", lambda e: self.close_banner())
        self.banner_body = tk.Text(content, height=1, wrap=tk.WORD, bd=0, highlightthickness=0, bg=C["conf_soft"],
                                   fg=theme.TYPE["banner_body"].color, font=theme.font("banner_body"))
        self.banner_body.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=(4, 0))
        content.columnconfigure(1, weight=1)

    def _draw_banner(self) -> None:
        c, edge, (pad_left, pad_y) = self.banner, S["banner_edge"], S["banner_pad"]
        width = max(c.winfo_width(), c.winfo_reqwidth())
        height = self._banner_content.winfo_reqheight() + 2 * pad_y
        if int(c.cget("height")) != height:
            c.configure(height=height)
        c.itemconfigure("banner_content", width=max(1, width - edge - pad_left - S["banner_pad_right"]))
        c.delete("banner_edge", "banner_bg")
        rounded_rect(c, 0, 0, width - 1, height - 1, S["banner_radius"], fill=C["conf"], tags=("banner_edge",))
        rounded_rect(c, edge, 0, width - 1, height - 1, S["banner_radius"], fill=C["conf_soft"], tags=("banner_bg",))

    def close_banner(self) -> None:
        self.model.dismiss_error()

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
        self.commit_button = button(buttons, "Commit", C["panel"], command=self.model.commit)
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
        else:
            self.message_box.delete("1.0", tk.END)

    # ---------- refresh on return (DES-VCS-018, DEC-VCS-059) ----------

    def _bind_focus_refresh(self) -> None:
        top = self.winfo_toplevel()
        top.bind("<FocusOut>", lambda _e: self.on_focus_out(), add="+")
        top.bind("<FocusIn>", lambda _e: self.on_focus_in(), add="+")

    def on_focus_out(self) -> None:
        """A widget lost the focus; the app lost it only if none of ours has it once Tk settles."""
        self.after_idle(self._note_focus_left)

    def _note_focus_left(self) -> None:
        if self.focus_get() is None:
            self._away = True

    def on_focus_in(self) -> None:
        """Back from another app: refresh once, 300 ms later. Moving the focus inside the window does nothing."""
        if not self._away:
            return
        self._away = False
        if self._focus_after:
            self.after_cancel(self._focus_after)
        self._focus_after = self.after(FOCUS_REFRESH_MS, self._refresh_on_return)

    def _refresh_on_return(self) -> None:
        self._focus_after = None
        self.model.refresh_all()

    @property
    def focus_refresh_pending(self) -> bool:
        return self._focus_after is not None

    def toggle_folders(self) -> None:
        self.model.show_folders = self.show_folders.get()

    def _bind_shortcuts(self) -> None:
        """⌘↩ commit, ⌘⇧↩ commit and push, ⌘1–⌘9 repository (REQ-VCS-022). The message field gets its own
        bindings so the Text class does not insert a new line first."""
        top = self.winfo_toplevel()
        self.shortcuts = {"<Command-Return>": self._shortcut(self.model.commit),
                          "<Command-Shift-Return>": self._shortcut(self.model.commit_and_push)}
        for sequence, handler in self.shortcuts.items():
            top.bind(sequence, handler)
            self.message_box.bind(sequence, handler)
        for digit in range(1, 10):
            sequence = f"<Command-Key-{digit}>"
            self.shortcuts[sequence] = self._shortcut(lambda index=digit - 1: self._select_index(index))
            top.bind(sequence, self.shortcuts[sequence])

    def _shortcut(self, action):
        def handler(_event=None):
            self._sync_message()
            action()
            return "break"
        return handler

    def _select_index(self, index: int) -> None:
        names = self.model.repo_names
        if index < len(names):
            self.model.select(names[index])

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
        self._render_feedback()
        self.refreshed.configure(text=self.model.refreshed_label)

    # ---------- error banner and operation in progress (P3, P4) ----------

    @property
    def busy_animating(self) -> bool:
        return self._busy_shown

    def _render_feedback(self) -> None:
        error = self.model.error
        if error:
            self.banner_title.configure(text=self.model.error_title or "Operacja nie powiodła się")
            self.banner_body.configure(state=tk.NORMAL)
            self.banner_body.delete("1.0", tk.END)
            self.banner_body.insert("1.0", error)
            lines = int(self.banner_body.count("1.0", tk.END, "displaylines")[0]) if self.banner.winfo_ismapped() else error.count("\n") + 1
            self.banner_body.configure(height=max(1, min(lines, S["banner_lines"])), state=tk.DISABLED)
            if not self.banner.winfo_manager():
                margin_x, margin_top, margin_bottom = S["banner_margin"]
                self.banner.pack(fill=tk.X, padx=margin_x, pady=(margin_top, margin_bottom), before=self.file_list)
            self.after_idle(self._draw_banner)  # once the new text has its size
        elif self.banner.winfo_manager():
            self.banner.pack_forget()

        label = self.model.busy_label
        self.busy_text.configure(text=label or "")
        if label and not self._busy_shown:
            self._busy_shown = True
            self.busy_bar.place(relx=0, rely=1.0, anchor=tk.SW, relwidth=1, height=S["busy_bar_height"])
            self._animate_busy()
        elif not label and self._busy_shown:
            self._busy_shown = False
            self.busy_bar.place_forget()
            if self._busy_after:
                self.after_cancel(self._busy_after)
                self._busy_after = None

    def _animate_busy(self) -> None:
        """A 30 % segment sliding left to right every 1.2 s; runs only while an operation is in progress."""
        c, width = self.busy_bar, max(self.busy_bar.winfo_width(), 1)
        c.delete("all")
        if self._reduce_motion:  # still, full width (P4)
            c.create_rectangle(0, 0, width, S["busy_bar_height"], fill=C["accent"], outline="")
            return
        share, frame_ms = S["busy_bar_share"], 16
        steps = S["busy_bar_period_ms"] // frame_ms
        x = (self._busy_phase / steps) * width * (1 + share) - width * share
        c.create_rectangle(x, 0, x + width * share, S["busy_bar_height"], fill=C["accent"], outline="")
        self._busy_phase = (self._busy_phase + 1) % steps
        self._busy_after = self.after(frame_ms, self._animate_busy)

    def _render_toolbar(self) -> None:
        self.repo_title.configure(text=self.model.selected or "")
        self.branch_chip.set(self.model.branch_summary)
        for chip, text in ((self.conflict_chip, self.model.conflict_summary), (self.merge_chip, self.model.merge_summary)):
            chip.set(text)  # at most one of them has text
            if text and not chip.winfo_manager():
                chip.pack(side=tk.LEFT, padx=(S["toolbar_gap"], 0), after=self.branch_chip)
            elif not text and chip.winfo_manager():
                chip.pack_forget()
        self.pull_button.configure(state=tk.NORMAL if self.model.can_pull else tk.DISABLED)

    def _render_commit_panel(self) -> None:
        if self._shown_repo != self.model.selected or self._message_text() != self.model.message:
            self._shown_repo = self.model.selected  # another repository, or the model cleared the draft after a commit
            self._load_draft()
        can_commit = self.model.can_commit
        # Default (blue) only while it can act: aqua paints a disabled default button blue in an inactive window.
        self.commit_button.configure(text=self.model.commit_label, state=tk.NORMAL if can_commit else tk.DISABLED,
                                     default="active" if can_commit else "normal")
        self.commit_push_button.configure(state=tk.NORMAL if self.model.can_commit_and_push else tk.DISABLED)
        reason = self.model.commit_disabled_reason
        self.reason.configure(text=f"ⓘ {reason}" if reason else "")
        if reason:
            self.reason.grid()
        else:
            self.reason.grid_remove()
