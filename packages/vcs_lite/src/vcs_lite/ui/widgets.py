"""Small drawn widgets of the reference: rounded pills (chip, badge, kbd) and hover tooltips.

Trace: DES-VCS-042, DEC-VCS-047, DEC-VCS-049, DEC-VCS-071
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tkinter import font as tkfont

from vcs_lite.ui import theme


def elide(text: str, font: tkfont.Font, width: int) -> str:
    """Shorten text with an ellipsis so it fits the width in pixels."""
    if font.measure(text) <= width:
        return text
    while text and font.measure(text + "…") > width:
        text = text[:-1]
    return text + "…"


def elide_middle(text: str, font: tkfont.Font, width: int) -> str:
    """Shorten text by replacing its middle with an ellipsis, so the start and the end stay readable."""
    if font.measure(text) <= width:
        return text
    head, tail = len(text) // 2, len(text) - len(text) // 2
    while head + tail > 0:
        if tail >= head:
            tail -= 1
        else:
            head -= 1
        candidate = text[:head] + "…" + text[len(text) - tail:]
        if font.measure(candidate) <= width:
            return candidate
    return "…"


def _filled_rounded(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, r: float,
                    fill: str, tags: tuple[str, ...]) -> None:
    """Two rectangles and four corner circles: exact radii, so pills get true semicircular ends.
    A smoothed polygon (spline) rounds too little and spikes on narrow shapes."""
    r = max(0.0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    style = {"fill": fill, "outline": "", "tags": tags}
    if r == 0:
        canvas.create_rectangle(x1, y1, x2, y2, **style)
        return
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **style)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **style)
    for cx, cy in ((x1 + r, y1 + r), (x2 - r, y1 + r), (x1 + r, y2 - r), (x2 - r, y2 - r)):
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, **style)


def rounded_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, r: float, *,
                 fill: str, outline: str = "", tags: tuple[str, ...] = ()) -> None:
    """A rectangle with exactly rounded corners; an outline different from the fill is a 1 pt border."""
    if outline and outline != fill:
        _filled_rounded(canvas, x1, y1, x2, y2, r, outline, tags)
        _filled_rounded(canvas, x1 + 1, y1 + 1, x2 - 1, y2 - 1, r - 1, fill, tags)
    else:
        _filled_rounded(canvas, x1, y1, x2, y2, r, fill, tags)


class Pill(tk.Canvas):
    """Text on a rounded background, sized to its text (chip, badge, kbd)."""

    def __init__(self, parent: tk.Misc, *, role: str, fill: str, outline: str = "", ink: str | None = None,
                 pad: tuple[int, int], radius: float | None = None, bottom_edge: int = 0, parent_bg: str):
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0)
        self._font = theme.font(role)
        self._ink = ink or theme.TYPE[role].color
        self._fill, self._outline = fill, outline
        self._pad, self._radius, self._bottom_edge = pad, radius, bottom_edge
        self.text = ""

    def set(self, text: str, *, fill: str | None = None, ink: str | None = None) -> None:
        self.text = text
        fill, ink = fill or self._fill, ink or self._ink
        self.delete("all")
        if not text:
            self.configure(width=0, height=0)
            return
        px, py = self._pad
        w = self._font.measure(text) + 2 * px
        h = self._font.metrics("linespace") + 2 * py + self._bottom_edge
        radius = h / 2 if self._radius is None else self._radius
        self.configure(width=w, height=h)
        if self._bottom_edge:  # kbd: a darker 2 px bottom edge under the key
            rounded_rect(self, 0, self._bottom_edge, w - 1, h - 1, radius, fill=self._outline, outline=self._outline)
        rounded_rect(self, 0, 0, w - 1, h - 1 - self._bottom_edge, radius, fill=fill, outline=self._outline or fill)
        self.create_text(w / 2, (h - self._bottom_edge) / 2, text=text, font=self._font, fill=ink)


def kbd(parent: tk.Misc, text: str, parent_bg: str) -> Pill:
    pill = Pill(parent, role="kbd", fill=theme.COLORS["kbd_bg"], outline=theme.COLORS["kbd_border"],
                pad=theme.SPACE["kbd_pad"], radius=theme.SPACE["kbd_radius"], bottom_edge=1, parent_bg=parent_bg)
    pill.set(text)
    return pill


class Tooltip:
    """Shows text from a callback while the pointer rests on a widget; nothing when the callback returns None."""

    DELAY_MS = 500

    def __init__(self, widget: tk.Widget, text: Callable[[], str | None]):
        self._widget, self._text = widget, text
        self._after: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._after = self._widget.after(self.DELAY_MS, self._show)

    def _show(self) -> None:
        text = self._text()
        if not text:
            return
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        x = self._widget.winfo_rootx()
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=text, font=theme.font("reason"), bg=theme.COLORS["bg"], fg=theme.COLORS["ink"],
                 padx=8, pady=4, highlightthickness=1, highlightbackground=theme.COLORS["control_border"]).pack()

    def _hide(self, _event=None) -> None:
        if self._after:
            self._widget.after_cancel(self._after)
            self._after = None
        if self._tip:
            self._tip.destroy()
            self._tip = None
