"""File list drawn on a canvas after the reference: groups, status squares, split paths, hints, keys, empty states.

Geometry (UI-REFERENCE §3): top padding 6; group header 10 + 15 + 4; rows 5 + 18 + 5 with square
column 22, gap 10 and side padding 16; the hint is right-aligned at the same padding.

Trace: DES-VCS-024, DES-VCS-042, DES-VCS-043, REQ-VCS-003, REQ-VCS-005, REQ-VCS-023, REQ-VCS-024, DEC-VCS-040, DEC-VCS-049, DEC-VCS-050, T-VCS-01
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field

from vcs_lite.app.model import AppModel, EmptyState
from vcs_lite.core.status import FileChange, Group
from vcs_lite.ui import theme
from vcs_lite.ui.widgets import rounded_rect

C, S = theme.COLORS, theme.SPACE

GROUP_ORDER = (Group.CONFLICTS, Group.STAGED, Group.CHANGES, Group.UNVERSIONED)  # P1: conflicts first
SIDE, ROW_PAD = S["row_pad"]
G_SIDE, G_TOP, G_BOTTOM = S["group_pad"]
HEADER_LINE = 15                                     # 11 pt at line height 1.4
HEADER_HEIGHT = G_TOP + HEADER_LINE + G_BOTTOM       # 29
ROW_HEIGHT = 2 * ROW_PAD + S["status_square"]        # 28
TEXT_X = SIDE + S["row_square_column"] + S["row_gap"]  # 48

LETTERS = {"M": ("M", "mod"), "T": ("M", "mod"), "A": ("A", "add"), "D": ("D", "del"),
           "R": ("R", "ren"), "C": ("C", "ren"), "?": ("?", "unv")}

KBD = "kbd"
HINTS = {
    Group.CONFLICTS: [("rozwiąż w edytorze · ", None), ("spacja", KBD), (" oznacz jako rozwiązany", None)],
    Group.STAGED: [("spacja", KBD), (" unstage · ", None), ("dwuklik", KBD), (" porównaj", None)],  # DEC-VCS-051
    Group.CHANGES: [("spacja", KBD), (" stage · ", None), ("dwuklik", KBD), (" porównaj", None)],
    Group.UNVERSIONED: [("spacja", KBD), (" stage · ", None), ("dwuklik", KBD), (" porównaj", None)],  # P7
}

Key = tuple[Group, str]


@dataclass(frozen=True)
class FileRow:
    group: Group
    path: str
    letter: str
    color: str
    pieces: list[tuple[str, str]] = field(compare=False)
    top: int = 0
    height: int = ROW_HEIGHT
    change: FileChange | None = field(default=None, compare=False)

    @property
    def key(self) -> Key:
        return self.group, self.path


def square(change: FileChange) -> tuple[str, str]:
    if change.group is Group.CONFLICTS:
        return "!", C["conf"]
    letter, color = LETTERS.get(change.code, (change.code[:1], "unv"))
    return letter, C[color]


def path_pieces(change: FileChange) -> list[tuple[str, str]]:
    """Directory and the old name of a rename in the dim style, the file name in bold."""
    pieces = [(f"{change.orig_path} → ", "file_dir")] if change.orig_path and change.group is Group.STAGED else []
    folder, _, name = change.path.rpartition("/")
    if folder:
        pieces.append((f"{folder}/", "file_dir"))
    pieces.append((name, "file_name"))
    return pieces


class FileList(tk.Frame):
    def __init__(self, master: tk.Misc, *, on_toggle: Callable[[FileChange], None],
                 on_activate: Callable[[FileChange], None], on_empty_action: Callable[[str], None]):
        super().__init__(master, bg=C["bg"])
        self._on_toggle, self._on_activate, self._on_empty_action = on_toggle, on_activate, on_empty_action
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0, yscrollincrement=2, takefocus=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._rows: list[FileRow] = []
        self._headers: list[tuple[str, int]] = []
        self._empty: list[str] = []
        self.selected_key: Key | None = None
        self.hovered_key: Key | None = None
        self._follow: Key | None = None  # file moved by space: follow it until it shows up in another group
        self._model: AppModel | None = None
        self._bind()

    def _bind(self) -> None:
        c = self.canvas
        c.bind("<Button-1>", lambda e: (c.focus_set(), self.click(e.y)))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.y))
        c.bind("<Motion>", lambda e: self.hover(e.y))
        c.bind("<Leave>", lambda e: self.hover(-1))
        c.bind("<Up>", lambda e: self.press_up())
        c.bind("<Down>", lambda e: self.press_down())
        c.bind("<space>", lambda e: self.press_space())
        c.bind("<Return>", lambda e: self.press_return())
        c.bind("<MouseWheel>", lambda e: c.yview_scroll(-e.delta, "units"))
        c.bind("<Configure>", lambda e: self._model and self.render(self._model))

    # ---------- reading what was drawn ----------

    def rows(self) -> list[FileRow]:
        return list(self._rows)

    def headers(self) -> list[tuple[str, int]]:
        return list(self._headers)

    def empty_texts(self) -> list[str]:
        return list(self._empty)

    def hint_texts(self) -> list[str]:
        return ["".join(text for text, _ in HINTS[row.group]) for row in self._rows if row.key in self._hint_keys()]

    # ---------- interaction ----------

    def _row_at(self, y: int) -> FileRow | None:
        y = self.canvas.canvasy(y)
        return next((r for r in self._rows if r.top <= y < r.top + r.height), None)

    def select_key(self, key: Key | None) -> None:
        self._follow = None
        self.selected_key = key
        self._redraw_rows()
        self._scroll_into_view()

    def click(self, y: int) -> None:
        row = self._row_at(y)
        if row:
            self.select_key(row.key)

    def hover(self, y: int) -> None:
        row = self._row_at(y) if y >= 0 else None
        key = row.key if row else None
        if key != self.hovered_key:
            self.hovered_key = key
            self._redraw_rows()

    def double_click(self, y: int) -> None:
        row = self._row_at(y)
        if row:
            self.select_key(row.key)
            self._on_activate(row.change)

    def press_return(self) -> None:
        row = self._selected_row()
        if row:
            self._on_activate(row.change)

    def press_space(self) -> None:
        row = self._selected_row()
        if row:
            self._on_toggle(row.change)
            self._follow = row.key

    def press_down(self) -> None:
        self._move(+1)

    def press_up(self) -> None:
        self._move(-1)

    def _move(self, step: int) -> None:
        if not self._rows:
            return
        keys = [r.key for r in self._rows]
        index = keys.index(self.selected_key) + step if self.selected_key in keys else (0 if step > 0 else len(keys) - 1)
        self.select_key(keys[max(0, min(index, len(keys) - 1))])

    def _selected_row(self) -> FileRow | None:
        return next((r for r in self._rows if r.key == self.selected_key), None)

    def _scroll_into_view(self) -> None:
        row = self._selected_row()
        if not row:
            return
        c = self.canvas
        view_top, view_height = c.canvasy(0), c.winfo_height()
        if view_height <= 1:
            return
        if row.top < view_top:
            c.yview_moveto(row.top / self._content_height)
        elif row.top + row.height > view_top + view_height:
            c.yview_moveto((row.top + row.height - view_height) / self._content_height)

    # ---------- drawing ----------

    def render(self, model: AppModel) -> None:
        self._model = model
        self._rows, self._headers, self._header_tops, self._empty = [], [], [], []
        y = S["files_pad_top"]
        for group in GROUP_ORDER:
            changes = model.files(group)
            if not changes:
                continue
            self._headers.append((group.value.upper(), len(changes)))
            self._header_tops.append(y)
            y += HEADER_HEIGHT
            for change in changes:
                letter, color = square(change)
                self._rows.append(FileRow(group, change.path, letter, color, path_pieces(change), y, ROW_HEIGHT, change))
                y += ROW_HEIGHT
        self._content_height = max(y, 1)
        self._keep_selection()
        self._redraw_all(model)

    def _keep_selection(self) -> None:
        keys = {r.key for r in self._rows}
        if self._follow is not None:
            old_group, path = self._follow
            moved = next((r.key for r in self._rows if r.path == path and r.group is not old_group), None)
            if moved or self._follow not in keys:  # arrived in its new group, or gone altogether
                self.selected_key, self._follow = moved, None
        if self.selected_key not in keys:
            self.selected_key = None
        if self.hovered_key not in keys:
            self.hovered_key = None

    def _width(self) -> int:
        w = self.canvas.winfo_width()
        return w if w > 1 else 700

    def _redraw_all(self, model: AppModel) -> None:
        c = self.canvas
        c.delete("all")
        empty = model.empty_state
        if empty and not self._rows:
            self._draw_empty(empty)
            c.configure(scrollregion=(0, 0, self._width(), c.winfo_height()))
            return
        for (title, count), top in zip(self._headers, self._header_tops):
            self._draw_header(title, count, top)
        self._redraw_rows()
        c.configure(scrollregion=(0, 0, self._width(), self._content_height))

    def _draw_header(self, title: str, count: int, top: int) -> None:
        color = C["conf"] if title == Group.CONFLICTS.value.upper() else theme.TYPE["group_header"].color
        y = top + G_TOP + HEADER_LINE / 2
        self.canvas.create_text(G_SIDE, y, anchor=tk.W, text=title, font=theme.font("group_header"), fill=color)
        x = G_SIDE + theme.font("group_header").measure(title) + S["group_count_gap"]
        self.canvas.create_text(x, y, anchor=tk.W, text=str(count), font=theme.font("group_count"),
                                fill=theme.TYPE["group_count"].color)

    def _hint_keys(self) -> set[Key]:
        return {k for k in (self.selected_key, self.hovered_key) if k is not None}

    def _redraw_rows(self) -> None:
        c = self.canvas
        c.delete("row")
        width = self._width()
        hinted = self._hint_keys()
        for row in self._rows:
            fill = C["accent_soft"] if row.key == self.selected_key else (
                C["row_hover"] if row.key == self.hovered_key else C["bg"])
            c.create_rectangle(0, row.top, width, row.top + row.height, fill=fill, outline="", tags=("row",))
            self._draw_square(row)
            x = TEXT_X
            middle = row.top + row.height / 2
            for text, role in row.pieces:
                c.create_text(x, middle, anchor=tk.W, text=text, font=theme.font(role),
                              fill=theme.TYPE[role].color, tags=("row",))
                x += theme.font(role).measure(text)
            if row.key in hinted:
                self._draw_hint(row, width - SIDE, middle)

    def _draw_square(self, row: FileRow) -> None:
        size = S["status_square"]
        x1, y1 = SIDE, row.top + ROW_PAD
        rounded_rect(self.canvas, x1, y1, x1 + size, y1 + size, S["status_square_radius"], fill=row.color, tags=("row",))
        self.canvas.create_text(x1 + size / 2, y1 + size / 2, text=row.letter, font=theme.font("status_square"),
                                fill=theme.TYPE["status_square"].color, tags=("row",))

    def _draw_hint(self, row: FileRow, right: float, middle: float) -> None:
        c = self.canvas
        pad_x, _ = S["kbd_pad"]
        kbd_font, hint_font = theme.font("kbd"), theme.font("hint")
        for text, kind in reversed(HINTS[row.group]):
            if kind == KBD:
                w = kbd_font.measure(text) + 2 * pad_x
                h = kbd_font.metrics("linespace") + 2
                rounded_rect(c, right - w, middle - h / 2, right, middle + h / 2, S["kbd_radius"],
                             fill=C["kbd_bg"], outline=C["kbd_border"], tags=("row",))
                c.create_text(right - w / 2, middle, text=text, font=kbd_font, fill=theme.TYPE["kbd"].color, tags=("row",))
            else:
                w = hint_font.measure(text)
                c.create_text(right, middle, anchor=tk.E, text=text, font=hint_font,
                              fill=theme.TYPE["hint"].color, tags=("row",))
            right -= w

    def _draw_empty(self, empty: EmptyState) -> None:
        c = self.canvas
        width, height = self._width(), max(c.winfo_height(), 300)
        gap = S["empty_gap"]
        lines: list[tuple[str, str, str]] = [
            (empty.glyph, "empty_glyph", C[empty.glyph_color] if empty.glyph_color else theme.TYPE["empty_glyph"].color),
            (empty.head, "empty_head", theme.TYPE["empty_head"].color),
            (empty.sub, "empty_sub", theme.TYPE["empty_sub"].color),
        ]
        if empty.path:
            lines.append((empty.path, "path", theme.TYPE["path"].color))
        heights = [theme.font(role).metrics("linespace") for _, role, _ in lines]
        button_height = 28 if empty.action else 0
        total = sum(heights) + gap * (len(lines) - 1) + (gap + button_height if empty.action else 0)
        y = (height - total) / 2
        for (text, role, color), h in zip(lines, heights):
            c.create_text(width / 2, y + h / 2, text=text, font=theme.font(role), fill=color, justify=tk.CENTER)
            self._empty.append(text)
            y += h + gap
        if empty.action:
            label = "⚙ Wybierz repozytoria…" if empty.action == "choose_repos" else "⟳ Sprawdź ponownie"
            button = tk.Button(c, text=label, highlightbackground=C["bg"], command=lambda: self._on_empty_action(empty.action),
                               default="active" if empty.action == "choose_repos" else "normal",
                               state=tk.DISABLED if empty.action == "choose_repos" else tk.NORMAL)  # Settings dialog: UI-2
            c.create_window(width / 2, y + button_height / 2, window=button)
