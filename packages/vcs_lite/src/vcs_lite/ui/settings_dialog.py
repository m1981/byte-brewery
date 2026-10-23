"""Repository dialog E-02 after the reference (UI-REFERENCE §8, P8): modal, folder shown, native checkboxes.

Trace: DES-VCS-019, DES-VCS-042, REQ-VCS-001, REQ-VCS-018, DEC-VCS-007, DEC-VCS-016, DEC-VCS-027, DEC-VCS-049, E-02
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from vcs_lite.app.model import AppModel
from vcs_lite.ui import theme
from vcs_lite.ui.widgets import Pill, elide_middle

C, S = theme.COLORS, theme.SPACE
PAD_X = 18
NOTE = "Pokazane są repozytoria z pierwszego poziomu folderu. Zwykłe i ukryte foldery są pominięte."


class RepoDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, model: AppModel, on_close: Callable[[], None]):
        super().__init__(master, bg=C["bg"])
        self._model, self._on_close = model, on_close
        self.title("Repozytoria do obserwowania")
        self.transient(master.winfo_toplevel())
        self.resizable(False, False)
        self.checks: list[tuple[str, tk.BooleanVar]] = []
        self.notes: dict[str, str] = {}
        self.error_text = ""
        self.path_text = model.rootdir
        choices, error = model.repo_choices()
        self._build(choices, error)
        self.update_count()
        self.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self._place_over(master.winfo_toplevel())
        self.after_idle(self._grab)

    # ---------- layout ----------

    def _build(self, choices, error: str | None) -> None:
        theme.label(self, "dialog_title", "Repozytoria do obserwowania", anchor=tk.W).pack(fill=tk.X, padx=PAD_X, pady=(16, 4))
        sub = tk.Frame(self, bg=C["bg"])
        sub.pack(fill=tk.X, padx=PAD_X, pady=(0, 10))
        prefix = theme.label(sub, "empty_sub", "z folderu")
        prefix.pack(side=tk.LEFT)
        chip_pad, gap = 6, 6
        room = S["dialog_width"] - 2 * PAD_X - theme.font("empty_sub").measure("z folderu") - gap - 2 * chip_pad
        self.path_shown = elide_middle(self.path_text, theme.font("path"), room)  # keeps the dialog 420 wide
        chip = Pill(sub, role="path", fill=C["chip_bg"], ink=C["ink"], pad=(chip_pad, 1), radius=5, parent_bg=C["bg"])
        chip.set(self.path_shown)
        chip.pack(side=tk.LEFT, padx=(gap, 0))
        if error:
            self._build_error(error)
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(fill=tk.X)
        self._build_list(choices)
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(fill=tk.X)
        theme.label(self, "dialog_note", NOTE, anchor=tk.W, justify=tk.LEFT,
                    wraplength=S["dialog_width"] - 2 * PAD_X).pack(fill=tk.X, padx=PAD_X, pady=8)
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(fill=tk.X)
        self._build_footer(error is None)

    def _build_error(self, error: str) -> None:
        self.error_text = error
        banner = tk.Frame(self, bg=C["conf_soft"], highlightthickness=0)
        banner.pack(fill=tk.X, padx=PAD_X, pady=(0, 10))
        tk.Frame(banner, width=S["banner_edge"], bg=C["conf"]).pack(side=tk.LEFT, fill=tk.Y)
        theme.label(banner, "banner_title", f"⚠ {error}", bg=C["conf_soft"], anchor=tk.W, justify=tk.LEFT,
                    wraplength=S["dialog_width"] - 2 * PAD_X - 24).pack(side=tk.LEFT, padx=(9, 10), pady=8)

    def _build_list(self, choices) -> None:
        holder = tk.Frame(self, bg=C["bg"], width=S["dialog_width"])
        holder.pack(fill=tk.X)
        canvas = self.list_canvas = tk.Canvas(holder, bg=C["bg"], highlightthickness=0, bd=0, width=S["dialog_width"])
        inner = tk.Frame(canvas, bg=C["bg"])
        canvas.create_window(0, 0, window=inner, anchor=tk.NW, width=S["dialog_width"])  # rows span the list
        for choice in choices:
            var = tk.BooleanVar(value=choice.chosen)
            row = tk.Frame(inner, bg=C["bg"])
            row.pack(fill=tk.X, padx=PAD_X - 4, pady=1)
            tk.Checkbutton(row, text=choice.name, variable=var, command=self.update_count, bg=C["bg"],
                           highlightbackground=C["bg"], font=theme.font("body"),
                           fg=C["name_off"] if choice.missing else C["ink"], anchor=tk.W).pack(side=tk.LEFT)
            if choice.missing:
                self.notes[choice.name] = "niedostępne"
                theme.label(row, "dialog_note", "niedostępne").pack(side=tk.RIGHT)
            self.checks.append((choice.name, var))
        inner.update_idletasks()
        needed = inner.winfo_reqheight() + 8
        canvas.configure(height=min(needed, S["dialog_list_height"]), scrollregion=(0, 0, S["dialog_width"], needed))
        canvas.pack(fill=tk.X, pady=4)
        # Tk sends the wheel to the widget under the pointer, not to its parent: every row widget scrolls.
        scroll = lambda e: canvas.yview_scroll(-e.delta, "units")  # noqa: E731
        pending = [canvas]
        while pending:
            widget = pending.pop()
            widget.bind("<MouseWheel>", scroll)
            pending.extend(widget.winfo_children())

    def _build_footer(self, can_save: bool) -> None:
        foot = tk.Frame(self, bg=C["panel"], padx=PAD_X, pady=12)
        foot.pack(fill=tk.X)
        self.count = theme.label(foot, "dialog_note", bg=C["panel"])
        self.count.pack(side=tk.LEFT)
        self.save_button = tk.Button(foot, text="Zapisz", default="active", command=self.save,
                                     highlightbackground=C["panel"], state=tk.NORMAL if can_save else tk.DISABLED)
        self.save_button.pack(side=tk.RIGHT)
        tk.Button(foot, text="Anuluj", command=self.cancel, highlightbackground=C["panel"]).pack(side=tk.RIGHT, padx=(0, 8))

    def _place_over(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_reqwidth()) // 2)
        y = parent.winfo_rooty() + 30
        self.geometry(f"+{x}+{y}")

    def _grab(self) -> None:
        try:
            self.grab_set()
        except tk.TclError:  # not viewable yet (e.g. while the main window is hidden)
            pass

    # ---------- actions ----------

    def update_count(self) -> None:
        chosen = sum(var.get() for _, var in self.checks)
        self.count.configure(text=f"Zaznaczono {chosen} z {len(self.checks)}")

    def save(self) -> None:
        if str(self.save_button.cget("state")) == tk.DISABLED:
            return
        self._model.set_repos([name for name, var in self.checks if var.get()])
        self._close()

    def cancel(self) -> None:
        self._close()

    def _close(self) -> None:
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        self._on_close()
