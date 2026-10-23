"""File list drawn on a canvas after the reference §9: names in PyCharm colours, 24 pt rows, optional folder view.

Flat view: files from 28, the parent folder in grey after the name. Folder view: one node per directory
(chevron 28, icon 46, name 68) with a hover button that stages or unstages the whole folder; files inside
a folder from 68, files at the repository root from 46.

Trace: DES-VCS-024, DES-VCS-042, DES-VCS-043, DES-VCS-045, REQ-VCS-003, REQ-VCS-005, REQ-VCS-023, REQ-VCS-024, REQ-VCS-025, REQ-VCS-026, DEC-VCS-040, DEC-VCS-049, DEC-VCS-050, DEC-VCS-051, DEC-VCS-057, T-VCS-01
"""

from __future__ import annotations

import tkinter as tk
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from vcs_lite.app.model import AppModel, EmptyState, files_label
from vcs_lite.core.status import FileChange, Group
from vcs_lite.ui import theme
from vcs_lite.ui.widgets import rounded_rect

C, S = theme.COLORS, theme.SPACE

GROUP_ORDER = (Group.CONFLICTS, Group.STAGED, Group.CHANGES, Group.UNVERSIONED)  # P1: conflicts first
H_TOP, H_LINE, H_BOTTOM = S["group_header"]
HEADER_HEIGHT = H_TOP + H_LINE + H_BOTTOM   # 24
ROW_HEIGHT = S["row_height"]                # 24

STATUS_COLORS = {"M": "file_mod", "T": "file_mod", "A": "file_add", "D": "file_del", "R": "file_ren", "C": "file_ren",
                 "?": "file_unv"}

KBD = "kbd"
HINTS = {
    Group.CONFLICTS: [("rozwiąż w edytorze · ", None), ("spacja", KBD), (" oznacz jako rozwiązany", None)],
    Group.STAGED: [("spacja", KBD), (" unstage · ", None), ("dwuklik", KBD), (" porównaj", None)],  # DEC-VCS-051
    Group.CHANGES: [("spacja", KBD), (" stage · ", None), ("dwuklik", KBD), (" porównaj", None)],
    Group.UNVERSIONED: [("spacja", KBD), (" stage · ", None), ("dwuklik", KBD), (" porównaj", None)],  # P7
}
FOLDER_ACTIONS = {Group.STAGED: "−", Group.CHANGES: "+", Group.UNVERSIONED: "+"}  # none for conflicts (DEC-VCS-057)

Key = tuple[Group, str]


@dataclass(frozen=True)
class ListRow:
    kind: str                       # "file" or "folder"
    group: Group
    path: str                       # file path, or the directory of a folder node
    color: str
    pieces: list[tuple[str, str]] = field(compare=False)
    top: int = 0
    x: int = S["indent_flat"]
    height: int = ROW_HEIGHT
    change: FileChange | None = field(default=None, compare=False)
    collapsed: bool = False

    @property
    def key(self) -> Key:
        return self.group, self.path


def file_color(change: FileChange) -> str:
    if change.group is Group.CONFLICTS:
        return C["conf"]
    return C[STATUS_COLORS.get(change.code, "file_unv")]


def file_pieces(change: FileChange, *, folder_suffix: bool) -> list[tuple[str, str]]:
    """Name first; after it the old name of a rename, or the parent folder in the flat view (K4)."""
    folder, _, name = change.path.rpartition("/")
    pieces = [(name, "file_name_del" if change.code == "D" and change.group is not Group.CONFLICTS else "file_name")]
    if change.orig_path and change.group is Group.STAGED:
        pieces.append((f"← {change.orig_path}", "file_folder"))
    elif folder and folder_suffix:
        pieces.append((folder, "file_folder"))
    return pieces


class FileList(tk.Frame):
    def __init__(self, master: tk.Misc, *, on_toggle: Callable[[FileChange], None],
                 on_activate: Callable[[FileChange], None], on_toggle_folder: Callable[[Group, str], None],
                 on_empty_action: Callable[[str], None]):
        super().__init__(master, bg=C["bg"])
        self._on_toggle, self._on_activate = on_toggle, on_activate
        self._on_toggle_folder, self._on_empty_action = on_toggle_folder, on_empty_action
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0, yscrollincrement=2, takefocus=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._rows: list[ListRow] = []
        self._headers: list[tuple[str, int, int]] = []   # title, count, top
        self._empty: list[str] = []
        self._collapsed: set[Key] = set()
        self._content_height = 1
        self.selected_key: Key | None = None
        self.hovered_key: Key | None = None
        self._follow: Key | None = None  # row moved by space: follow it until it shows up in another group
        self._model: AppModel | None = None
        self._empty_button: tk.Button | None = None
        self._bind()

    def _bind(self) -> None:
        c = self.canvas
        c.bind("<Button-1>", lambda e: (c.focus_set(), self.click(e.y, e.x)))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.y))
        c.bind("<Motion>", lambda e: self.hover(e.y))
        c.bind("<Leave>", lambda e: self.hover(-1))
        for key, action in (("<Up>", self.press_up), ("<Down>", self.press_down), ("<Left>", self.press_left),
                            ("<Right>", self.press_right), ("<space>", self.press_space), ("<Return>", self.press_return)):
            c.bind(key, lambda e, a=action: a())
        c.bind("<MouseWheel>", lambda e: self.scroll(e.delta))
        c.bind("<Configure>", lambda e: self._model and self.render(self._model))

    def scroll(self, delta: int) -> None:
        """Mouse wheel; a list that fits its window stays put (Tk would move a short region into empty space)."""
        c = self.canvas
        if self._content_height <= c.winfo_height():
            c.yview_moveto(0)
            return
        c.yview_scroll(-delta, "units")

    # ---------- reading what was drawn ----------

    def rows(self) -> list[ListRow]:
        return list(self._rows)

    def headers(self) -> list[tuple[str, int]]:
        return [(title, count) for title, count, _ in self._headers]

    def empty_texts(self) -> list[str]:
        return list(self._empty)

    def hint_texts(self) -> list[str]:
        shown = self._marked_keys()
        return ["".join(t for t, _ in HINTS[r.group]) for r in self._rows if r.kind == "file" and r.key in shown]

    def empty_action_enabled(self) -> bool:
        return self._empty_button is not None and str(self._empty_button.cget("state")) == tk.NORMAL

    def run_empty_action(self) -> None:
        if self._empty_button is not None:
            self._empty_button.invoke()

    def action_glyph(self) -> str | None:
        row = self._action_row()
        return FOLDER_ACTIONS.get(row.group) if row else None

    # ---------- interaction ----------

    def _row_at(self, y: int) -> ListRow | None:
        y = self.canvas.canvasy(y)
        return next((r for r in self._rows if r.top <= y < r.top + r.height), None)

    def _row(self, key: Key | None) -> ListRow | None:
        return next((r for r in self._rows if r.key == key), None)

    def select_key(self, key: Key | None) -> None:
        self._follow = None
        self.selected_key = key
        self._redraw_rows()
        self._scroll_into_view()

    def click(self, y: int, x: int = 0) -> None:
        row = self._row_at(y)
        if not row:
            return
        if row.kind == "folder" and x >= self._action_left() and FOLDER_ACTIONS.get(row.group):
            self.select_key(row.key)
            self.click_action()
        elif row.kind == "folder" and row.x <= x < row.x + S["chevron_width"]:
            self._toggle_collapsed(row)
        else:
            self.select_key(row.key)

    def click_action(self) -> None:
        row = self._action_row()
        if row and FOLDER_ACTIONS.get(row.group):
            self._on_toggle_folder(row.group, row.path)
            self._follow = row.key

    def hover(self, y: int) -> None:
        row = self._row_at(y) if y >= 0 else None
        key = row.key if row else None
        if key != self.hovered_key:
            self.hovered_key = key
            self._redraw_rows()

    def double_click(self, y: int) -> None:
        row = self._row_at(y)
        if not row:
            return
        self.select_key(row.key)
        if row.kind == "folder":
            self._toggle_collapsed(row)
        else:
            self._on_activate(row.change)

    def press_return(self) -> None:
        row = self._row(self.selected_key)
        if row and row.kind == "folder":
            self._toggle_collapsed(row)
        elif row:
            self._on_activate(row.change)

    def press_space(self) -> None:
        row = self._row(self.selected_key)
        if not row:
            return
        if row.kind == "folder":
            if FOLDER_ACTIONS.get(row.group):
                self._on_toggle_folder(row.group, row.path)
                self._follow = row.key
            return
        self._on_toggle(row.change)
        self._follow = row.key

    def press_left(self) -> None:
        row = self._row(self.selected_key)
        if row and row.kind == "folder" and not row.collapsed:
            self._toggle_collapsed(row)

    def press_right(self) -> None:
        row = self._row(self.selected_key)
        if row and row.kind == "folder" and row.collapsed:
            self._toggle_collapsed(row)

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

    def _toggle_collapsed(self, row: ListRow) -> None:
        self._collapsed.symmetric_difference_update({row.key})
        if self._model:
            self.render(self._model)

    def _action_row(self) -> ListRow | None:
        """The folder row whose button is visible: the hovered one first, else the selected one."""
        for key in (self.hovered_key, self.selected_key):
            row = self._row(key)
            if row and row.kind == "folder":
                return row
        return None

    def _scroll_into_view(self) -> None:
        row = self._row(self.selected_key)
        c = self.canvas
        if not row or c.winfo_height() <= 1:
            return
        view_top, view_height = c.canvasy(0), c.winfo_height()
        if row.top < view_top:
            c.yview_moveto(row.top / self._content_height)
        elif row.top + row.height > view_top + view_height:
            c.yview_moveto((row.top + row.height - view_height) / self._content_height)

    # ---------- building rows ----------

    def render(self, model: AppModel) -> None:
        self._model = model
        self._rows, self._headers, self._empty = [], [], []
        y = S["files_pad_top"]
        for group in GROUP_ORDER:
            changes = model.files(group)
            if not changes:
                continue
            self._headers.append((group.value.upper(), len(changes), y))
            y += HEADER_HEIGHT
            y = self._add_folder_rows(group, changes, y) if model.show_folders else self._add_flat_rows(changes, y)
        self._content_height = max(y, 1)
        self._keep_selection()
        self._redraw_all(model)

    def _add_flat_rows(self, changes: list[FileChange], y: int) -> int:
        for change in changes:
            self._rows.append(ListRow("file", change.group, change.path, file_color(change),
                                      file_pieces(change, folder_suffix=True), y, S["indent_flat"], change=change))
            y += ROW_HEIGHT
        return y

    def _add_folder_rows(self, group: Group, changes: list[FileChange], y: int) -> int:
        by_folder: dict[str, list[FileChange]] = defaultdict(list)
        for change in changes:
            by_folder[change.path.rpartition("/")[0]].append(change)
        for folder in sorted(f for f in by_folder if f):  # folders first, alphabetically
            members = by_folder[folder]
            collapsed = (group, folder) in self._collapsed
            self._rows.append(ListRow("folder", group, folder, C["ink"],
                                      [(folder, "folder_name"), (files_label(len(members)), "folder_count")],
                                      y, S["indent_chevron"], collapsed=collapsed))
            y += ROW_HEIGHT
            if not collapsed:
                for change in members:
                    self._rows.append(ListRow("file", group, change.path, file_color(change),
                                              file_pieces(change, folder_suffix=False), y, S["indent_child"], change=change))
                    y += ROW_HEIGHT
        for change in by_folder.get("", []):  # then files at the repository root
            self._rows.append(ListRow("file", group, change.path, file_color(change),
                                      file_pieces(change, folder_suffix=False), y, S["indent_icon"], change=change))
            y += ROW_HEIGHT
        return y

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

    # ---------- drawing ----------

    def _width(self) -> int:
        w = self.canvas.winfo_width()
        return w if w > 1 else 700

    def _action_left(self) -> int:
        return self._width() - S["row_side"] - S["folder_act"]

    def _marked_keys(self) -> set[Key]:
        return {k for k in (self.selected_key, self.hovered_key) if k is not None}

    def _redraw_all(self, model: AppModel) -> None:
        c = self.canvas
        c.delete("all")
        self._empty_button = None
        empty = model.empty_state
        if empty and not self._rows:
            self._draw_empty(empty)
            c.configure(scrollregion=(0, 0, self._width(), c.winfo_height()))
            return
        for title, count, top in self._headers:
            self._draw_header(title, count, top)
        self._redraw_rows()
        c.configure(scrollregion=(0, 0, self._width(), max(self._content_height, c.winfo_height())))

    def _draw_header(self, title: str, count: int, top: int) -> None:
        color = C["conf"] if title == Group.CONFLICTS.value.upper() else theme.TYPE["group_header"].color
        y = top + H_TOP + H_LINE / 2
        side = S["group_side"]
        self.canvas.create_text(side, y, anchor=tk.W, text=title, font=theme.font("group_header"), fill=color)
        x = side + theme.font("group_header").measure(title) + S["group_count_gap"]
        self.canvas.create_text(x, y, anchor=tk.W, text=str(count), font=theme.font("group_count"),
                                fill=theme.TYPE["group_count"].color)

    def _redraw_rows(self) -> None:
        c = self.canvas
        c.delete("row")
        width, marked, action_row = self._width(), self._marked_keys(), self._action_row()
        for row in self._rows:
            fill = C["accent_soft"] if row.key == self.selected_key else (
                C["row_hover"] if row.key == self.hovered_key else C["bg"])
            c.create_rectangle(0, row.top, width, row.top + row.height, fill=fill, outline="", tags=("row",))
            middle = row.top + row.height / 2
            if row.kind == "folder":
                self._draw_folder(row, middle)
                if row is action_row and FOLDER_ACTIONS.get(row.group):
                    self._draw_action(FOLDER_ACTIONS[row.group], middle)
            else:
                self._draw_pieces(row, row.x, middle)
                if row.key in marked:
                    self._draw_hint(row, width - S["row_side"], middle)

    def _draw_pieces(self, row: ListRow, x: float, middle: float) -> None:
        for index, (text, role) in enumerate(row.pieces):
            if index:
                x += S["suffix_gap"]
            color = row.color if role in ("file_name", "file_name_del") else theme.TYPE[role].color
            self.canvas.create_text(x, middle, anchor=tk.W, text=text, font=theme.font(role), fill=color, tags=("row",))
            x += theme.font(role).measure(text)

    def _draw_folder(self, row: ListRow, middle: float) -> None:
        c = self.canvas
        c.create_text(row.x + S["chevron_width"] / 2, middle, text="▸" if row.collapsed else "▾",
                      font=theme.font("folder_count"), fill=C["dim"], tags=("row",))
        w, h = S["folder_icon"]
        left, top = S["indent_icon"], middle - h / 2
        rounded_rect(c, left, top, left + w * 0.45, top + 3, 1.5, fill=C["folder_icon"], tags=("row",))   # tab
        rounded_rect(c, left, top + 2, left + w, top + h, 2, fill=C["folder_icon"], tags=("row",))        # body
        self._draw_pieces(row, S["indent_child"], middle)

    def _draw_action(self, glyph: str, middle: float) -> None:
        size, left = S["folder_act"], self._action_left()
        rounded_rect(self.canvas, left, middle - size / 2, left + size, middle + size / 2, S["folder_act_radius"],
                     fill=C["folder_act_hover"], tags=("row",))
        self.canvas.create_text(left + size / 2, middle, text=glyph, font=theme.font("folder_act"),
                                fill=theme.TYPE["folder_act"].color, tags=("row",))

    def _draw_hint(self, row: ListRow, right: float, middle: float) -> None:
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
        items = []
        for text, role, color in lines:  # the description wraps at 46 characters (P5)
            wrap = theme.font(role).measure("0") * S["empty_text_width"] if role == "empty_sub" else 0
            items.append(c.create_text(width / 2, 0, text=text, font=theme.font(role), fill=color, justify=tk.CENTER,
                                       anchor=tk.N, width=wrap))
            self._empty.append(text)
        heights = [max(c.bbox(i)[3] - c.bbox(i)[1], theme.font(role).metrics("linespace"))
                   for i, (_, role, _) in zip(items, lines)]
        button_height = 28 if empty.action else 0
        total = sum(heights) + gap * (len(lines) - 1) + (gap + button_height if empty.action else 0)
        y = (height - total) / 2
        for item, h in zip(items, heights):
            c.move(item, 0, y)
            y += h + gap
        if empty.action:
            label = "⚙ Wybierz repozytoria…" if empty.action == "choose_repos" else "⟳ Sprawdź ponownie"
            button = tk.Button(c, text=label, highlightbackground=C["bg"], command=lambda: self._on_empty_action(empty.action),
                               default="active" if empty.action == "choose_repos" else "normal")
            c.create_window(width / 2, y + button_height / 2, window=button)
            self._empty_button = button
