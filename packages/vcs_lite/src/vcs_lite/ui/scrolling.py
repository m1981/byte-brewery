"""Native vertical scrolling with a reserved gutter and inset track.

Trace: DES-VCS-078, REQ-VCS-045
"""
from collections.abc import Callable
import tkinter as tk
from tkinter import ttk


class ScrollPane(tk.Frame):
    """Own geometry and scroll wiring only; the client owns content and selection."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, takefocus=False)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS, pady=6)
        self._view = None

    def attach(self, widget: tk.Canvas | tk.Text, *, on_view: Callable | None = None) -> None:
        """Compose viewport painting with Tk's two-way scrollbar protocol."""
        def changed(first: str, last: str) -> None:
            self.scrollbar.set(first, last)
            view = (first, last, widget.winfo_width(), widget.winfo_height())
            if view != self._view:
                self._view = view  # set before repainting, which may configure the region again
                if on_view:
                    on_view(first, last)

        self.scrollbar.configure(command=widget.yview)
        widget.configure(yscrollcommand=changed)
        widget.grid(row=0, column=0, sticky=tk.NSEW)
