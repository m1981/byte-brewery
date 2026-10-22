"""Repository sidebar drawn on a canvas after the reference: header, rows with state dot, two lines, badge.

Geometry (UI-REFERENCE §3): sidebar padding 8 × 10, header padding 8 × 6, row padding 8 × 7,
rows 2 apart, dot column 10, gap 8; line heights follow the reference's 1.4 line height.

Trace: DES-VCS-023, DES-VCS-042, DES-VCS-046, REQ-VCS-027, DEC-VCS-068, DEC-VCS-069, REQ-VCS-002, REQ-VCS-016, REQ-VCS-018, DEC-VCS-047, DEC-VCS-049
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import font as tkfont

from vcs_lite.app.model import AppModel, RepoState
from vcs_lite.ui import theme
from vcs_lite.ui.widgets import rounded_rect

C, S = theme.COLORS, theme.SPACE

PAD_X, PAD_Y = S["sidebar_pad"]
HEADER_PAD_X, HEADER_PAD_Y = S["side_header_pad"]
ITEM_PAD_X, ITEM_PAD_Y = S["repo_item_pad"]
NAME_LINE, BRANCH_LINE, HEADER_LINE = 18, 16, 15          # 13, 11.5 and 11 pt at line height 1.4
ITEM_HEIGHT = 2 * ITEM_PAD_Y + NAME_LINE + BRANCH_LINE     # 48
ITEM_STRIDE = ITEM_HEIGHT + S["sidebar_item_gap"]          # 50
FIRST_ITEM_TOP = PAD_Y + 2 * HEADER_PAD_Y + HEADER_LINE    # 37
TEXT_X = PAD_X + ITEM_PAD_X + S["repo_dot_column"] + S["repo_item_gap"]  # 34

DOT_COLORS = {
    RepoState.CHANGES: C["mod"],
    RepoState.CLEAN: C["state_clean"],
    RepoState.CONFLICT: C["conf"],
    RepoState.MERGE: C["mod"],  # P11: never the green "clean" dot
    RepoState.UNAVAILABLE: C["state_off"],
}


@dataclass(frozen=True)
class Row:
    name: str
    shown_name: str
    line: str
    badge: tuple[str, str] | None
    selected: bool
    dot: str
    top: int


def elide(text: str, font: tkfont.Font, width: int) -> str:
    """Shorten text with an ellipsis so it fits the width in pixels."""
    if font.measure(text) <= width:
        return text
    while text and font.measure(text + "…") > width:
        text = text[:-1]
    return text + "…"


class RepoSidebar(tk.Frame):
    def __init__(self, master: tk.Misc, on_select: Callable[[str], None]):
        super().__init__(master, bg=C["sidebar"])
        self._on_select = on_select
        self.canvas = tk.Canvas(self, bg=C["sidebar"], highlightthickness=0, bd=0, width=S["sidebar_width"])
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", lambda event: self.click(event.y))
        self._rows: list[Row] = []
        self.empty_text = ""

    # ---------- reading what was drawn ----------

    def rows(self) -> list[Row]:
        return list(self._rows)

    def name_at(self, y: int) -> str | None:
        for row in self._rows:
            if row.top <= y < row.top + ITEM_HEIGHT:
                return row.name
        return None

    def click(self, y: int) -> None:
        name = self.name_at(y)
        if name:
            self._on_select(name)

    # ---------- drawing ----------

    def render(self, model: AppModel) -> None:
        c = self.canvas
        c.delete("all")
        self._rows = []
        width = S["sidebar_width"]
        c.create_text(PAD_X + HEADER_PAD_X, PAD_Y + HEADER_PAD_Y, anchor=tk.NW, text="REPOZYTORIA",
                      font=theme.font("side_header"), fill=theme.TYPE["side_header"].color)
        self.empty_text = "" if model.repo_names else "Brak"
        if self.empty_text:
            c.create_text(PAD_X + HEADER_PAD_X, FIRST_ITEM_TOP + 4, anchor=tk.NW, text=self.empty_text,
                          font=theme.font("body"), fill=C["dim"])
        for index, name in enumerate(model.repo_names):
            self._rows.append(self._draw_row(model, name, FIRST_ITEM_TOP + index * ITEM_STRIDE, width))

    def _draw_row(self, model: AppModel, name: str, top: int, width: int) -> Row:
        c = self.canvas
        selected = name == model.selected
        state = model.state(name)
        view = model.view(name)
        x1, x2 = PAD_X, width - PAD_X
        middle = top + ITEM_HEIGHT / 2
        if selected:
            rounded_rect(c, x1, top, x2, top + ITEM_HEIGHT, S["repo_item_radius"], fill=C["accent"], outline=C["accent"],
                         tags=("selection",))

        dot = self._dot_color(model, name, state)
        self._draw_dot(x1 + ITEM_PAD_X, middle, dot, selected, state)

        badge = model.badge(name)
        badge_left = self._draw_badge(badge, x2 - ITEM_PAD_X, middle, selected) if badge else x2 - ITEM_PAD_X
        text_width = int(badge_left - S["repo_item_gap"] - TEXT_X)

        name_ink = C["on_accent"] if selected else (C["name_off"] if state is RepoState.UNAVAILABLE else C["ink"])
        shown = elide(name, theme.font("side_name"), text_width)
        c.create_text(TEXT_X, top + ITEM_PAD_Y + NAME_LINE / 2, anchor=tk.W, text=shown,
                      font=theme.font("side_name"), fill=name_ink)
        line = model.sidebar_line(name)
        c.create_text(TEXT_X, top + ITEM_PAD_Y + NAME_LINE + BRANCH_LINE / 2, anchor=tk.W,
                      text=elide(line, theme.font("side_branch"), text_width), font=theme.font("side_branch"),
                      fill=C["branch_on_accent"] if selected else theme.TYPE["side_branch"].color)
        return Row(name, shown, line, badge, selected, dot, top)

    @staticmethod
    def _dot_color(model: AppModel, name: str, state: RepoState) -> str:
        if state is RepoState.BUSY:  # keep the colour the repository had before the operation
            view = model.view(name)
            if not view.status or not (view.status.changes or view.status.merging):
                return C["state_clean"]
            return C["conf"] if view.status.has_conflicts else C["mod"]
        return DOT_COLORS[state]

    def _draw_dot(self, column_left: float, middle: float, color: str, selected: bool, state: RepoState) -> None:
        size = S["state_dot"]
        cx = column_left + S["repo_dot_column"] / 2
        box = (cx - size / 2, middle - size / 2, cx + size / 2, middle + size / 2)
        if selected and state is RepoState.BUSY:       # P4: white dot with a light ring
            self.canvas.create_oval(*box, fill=C["on_accent"], outline=C["busy_ring"], width=2)
        elif selected and state is RepoState.CONFLICT:  # P2: red dot with a white ring
            self.canvas.create_oval(*box, fill=color, outline=C["on_accent"], width=2)
        else:
            self.canvas.create_oval(*box, fill=color, outline=color)

    def _draw_badge(self, badge: tuple[str, str], right: float, middle: float, selected: bool) -> float:
        text, kind = badge
        font = theme.font("badge")
        pad_x, pad_y = S["badge_pad"]
        w = max(S["badge_min_width"], font.measure(text) + 2 * pad_x)
        h = font.metrics("linespace") + 2 * pad_y
        if kind == "conflict":
            fill, ink = (C["on_accent"], C["conf"]) if selected else (C["conf_soft"], C["conf"])
        else:
            fill, ink = (C["badge_on_accent"], C["on_accent"]) if selected else (C["badge_bg"], C["chip_ink"])
        left = right - w
        rounded_rect(self.canvas, left, middle - h / 2, right, middle + h / 2, h / 2, fill=fill, outline=fill)
        self.canvas.create_text(left + w / 2, middle, text=text, font=font, fill=ink)
        return left
