"""File list drawn on a canvas after the reference §9: names in PyCharm colours, 24 pt rows, optional folder view.

Flat view: files from 28, the parent folder in grey after the name. Folder view: one node per directory
(chevron 28, icon 46, name 68) with a hover button that stages or unstages the whole folder; files inside
a folder from 68, files at the repository root from 46.

Trace: DES-VCS-024, DES-VCS-042, DES-VCS-043, DES-VCS-045, REQ-VCS-003, REQ-VCS-005, REQ-VCS-023, REQ-VCS-024, REQ-VCS-025, REQ-VCS-026, DEC-VCS-040, DEC-VCS-049, DEC-VCS-050, DEC-VCS-051, DEC-VCS-057, DEC-VCS-071, DEC-VCS-072, DEC-VCS-073, REQ-VCS-028, REQ-VCS-029, REQ-VCS-030, REQ-VCS-031, REQ-VCS-032, REQ-VCS-034, DEC-VCS-076, DEC-VCS-089, DEC-VCS-090, DEC-VCS-100, DEC-VCS-104, DEC-VCS-106, DES-VCS-060, T-VCS-01
"""

from __future__ import annotations

import tkinter as tk
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from vcs_lite.app.model import AppModel, EmptyState, RepoState, files_label, is_markdown
from vcs_lite.core.filekind import kind_of
from vcs_lite.core.status import FileChange, Group
from vcs_lite.ui import theme
from vcs_lite.ui.widgets import elide, elide_middle, rounded_rect

C, S = theme.COLORS, theme.SPACE

GROUP_ORDER = (Group.CONFLICTS, Group.STAGED, Group.CHANGES, Group.UNVERSIONED)  # P1: conflicts first
H_TOP, H_LINE, H_BOTTOM = S["group_header"]
HEADER_HEIGHT = H_TOP + H_LINE + H_BOTTOM   # 24
ROW_HEIGHT = S["row_height"]                # 24

STATUS_COLORS = {"M": "file_mod", "T": "file_mod", "A": "file_add", "D": "file_del", "R": "file_ren", "C": "file_ren",
                 "?": "file_unv"}

KBD = "kbd"
EMPTY_STAGED = [("pusto · ", None), ("spacja", KBD), (" na pliku dodaje go do commita", None)]  # P13b
HINTS = {
    Group.CONFLICTS: [("rozwiąż w edytorze · ", None), ("spacja", KBD), (" oznacz jako rozwiązany", None)],
    Group.STAGED: [("spacja", KBD), (" unstage · ", None), ("dwuklik", KBD), (" porównaj", None)],  # DEC-VCS-051
    Group.CHANGES: [("spacja", KBD), (" stage · ", None), ("dwuklik", KBD), (" porównaj", None)],
    Group.UNVERSIONED: [("spacja", KBD), (" stage · ", None), ("dwuklik", KBD), (" porównaj", None)],  # P7
}
SHOW_HINT = {group: [*hint[:-1], (" pokaż", None)] for group, hint in HINTS.items() if hint[-1][1] is None}
# images and PDFs: the browser shows the file itself, there is nothing to compare (DEC-VCS-100)
FOLDER_ACTIONS = {Group.STAGED: "−", Group.CHANGES: "+", Group.UNVERSIONED: "+"}  # none for conflicts (DEC-VCS-057)
PROJECT = "projekt"         # the group of the project tree rows (REQ-VCS-032)
DIRS = ("folder", "pdir")
PROJECT_INDENT = 18         # one level deeper in the project tree   # folder nodes of the change groups and of the project tree
READ_HINT = [("dwuklik", KBD), (" czytaj", None)]   # a Markdown file without changes
OPEN_HINT = [("dwuklik", KBD), (" otwórz", None)]   # any other file without changes

Key = tuple["Group | str", str]


@dataclass(frozen=True)
class ListRow:
    kind: str                       # "file", "folder", or in the project tree "pfile" and "pdir"
    group: Group | str              # a status group, or PROJECT
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


@dataclass(frozen=True)
class Advance:
    """Where the selection goes once a space operation has finished (REQ-VCS-028)."""

    repo: str
    group: Group
    leaving: frozenset[str]   # paths that space takes out of the group
    after: tuple[Key, ...]    # files of the group below the row, nearest first
    before: tuple[Key, ...]   # files of the group above the row, nearest first


DOUBLE_CLICK_MS = 500  # a click inside a multiple selection narrows it only if no double click follows
STAY = object()        # the planned move found nothing to do: the selection stays as it is


def fit_pieces(pieces: list[tuple[str, str]], room: float) -> list[tuple[str, str]]:
    """P12: the name stays whole while it fits on its own, else it ends in "…" and nothing follows;
    the folder or old name after it is shortened in the middle, so its first and last parts stay."""
    (name, role), *rest = pieces
    name_width = theme.font(role).measure(name)
    if name_width > room:
        return [(elide(name, theme.font(role), int(room)), role)]
    fitted, room = [(name, role)], room - name_width
    for text, suffix_role in rest:
        room -= S["suffix_gap"]
        font = theme.font(suffix_role)
        if room < font.measure("x…x"):
            break
        short = elide_middle(text, font, int(room))
        fitted.append((short, suffix_role))
        room -= font.measure(short)
    return fitted


def changes_label(n: int) -> str:
    """Polish plural: 1 zmiana, 2–4 zmiany (but 12–14 zmian), otherwise zmian."""
    if n == 1:
        return "1 zmiana"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} zmiany"
    return f"{n} zmian"


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
                 on_empty_action: Callable[[str], None],
                 on_toggle_many: Callable[[Group, list[FileChange]], None] = lambda group, changes: None,
                 on_ignore: Callable[[list[str], list[str]], None] = lambda files, folders: None,
                 on_compare_external: Callable[[FileChange], None] | None = None,
                 on_open: Callable[[str], None] = lambda path: None,
                 on_open_in_app: Callable[[str], None] = lambda path: None,
                 on_reveal: Callable[[str], None] = lambda path: None):
        """`on_compare_external` is set only when the diff tool plugin is (DEC-VCS-106)."""
        super().__init__(master, bg=C["bg"])
        self._on_toggle, self._on_activate = on_toggle, on_activate
        self._on_toggle_folder, self._on_empty_action = on_toggle_folder, on_empty_action
        self._on_toggle_many, self._on_ignore = on_toggle_many, on_ignore
        self._on_compare_external = on_compare_external
        self._on_open, self._on_open_in_app, self._on_reveal = on_open, on_open_in_app, on_reveal
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0, yscrollincrement=2, takefocus=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._rows: list[ListRow] = []
        self._headers: list[tuple[str, int, int]] = []   # title, count, top
        self._placeholder_top: int | None = None          # the grey hint of an empty Staged group (P13b)
        self._empty: list[str] = []
        self._collapsed: set[Key] = set()    # folders of the change groups, open by default
        self._expanded: set[str] = set()     # folders of the project tree, closed by default
        self._content_height = 1
        self.selected_key: Key | None = None     # the current row: arrows and Enter act on it
        self.selected_keys: set[Key] = set()     # the selection (REQ-VCS-029)
        self.anchor_key: Key | None = None       # where Shift ranges start
        self.hovered_key: Key | None = None
        self._narrow_after: str | None = None
        self._shown_repo: str | None = None
        self._advance: Advance | None = None  # planned by space, carried out once the operation is over
        self._model: AppModel | None = None
        self._empty_button: tk.Button | None = None
        self._bind()

    def _bind(self) -> None:
        c = self.canvas
        c.bind("<Button-1>", lambda e: (c.focus_set(), self.click(e.y, e.x)))
        for sequence, ctrl, shift in (("<Shift-Button-1>", False, True), ("<Control-Button-1>", True, False),
                                      ("<Command-Button-1>", True, False), ("<Control-Shift-Button-1>", True, True),
                                      ("<Command-Shift-Button-1>", True, True)):  # Ctrl and ⌘ alike (DEC-VCS-073)
            c.bind(sequence, lambda e, a=ctrl, b=shift: (c.focus_set(), self.click(e.y, e.x, ctrl=a, shift=b)))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.y))
        c.bind("<Motion>", lambda e: self.hover(e.y))
        c.bind("<Leave>", lambda e: self.hover(-1))
        for key, action in (("<Up>", self.press_up), ("<Down>", self.press_down), ("<Left>", self.press_left),
                            ("<Right>", self.press_right), ("<space>", self.press_space), ("<Return>", self.press_return),
                            ("<Shift-Up>", lambda: self.press_up(extend=True)),
                            ("<Shift-Down>", lambda: self.press_down(extend=True)),
                            ("<Control-Up>", lambda: self.move_current(-1)), ("<Command-Up>", lambda: self.move_current(-1)),
                            ("<Control-Down>", lambda: self.move_current(+1)),
                            ("<Command-Down>", lambda: self.move_current(+1)),
                            ("<Control-space>", self.toggle_current), ("<Command-space>", self.toggle_current),
                            ("<Control-a>", self.select_all), ("<Command-a>", self.select_all)):
            c.bind(key, lambda e, a=action: a())
        c.bind("<MouseWheel>", lambda e: self.scroll(e.delta))
        for sequence in ("<Button-2>", "<Button-3>"):  # right button and two-finger click (DEC-VCS-073)
            c.bind(sequence, lambda e: self.open_menu(e.y, e.x_root, e.y_root))
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

    def staged_placeholder(self) -> str | None:
        return "".join(text for text, _ in EMPTY_STAGED) if self._placeholder_top is not None else None

    def hint_texts(self) -> list[str]:
        return ["".join(t for t, _ in self._hints(r)) for r in self._rows
                if r.kind in ("file", "pfile") and r.key == self.hovered_key]

    @staticmethod
    def _hints(row: ListRow) -> list[tuple[str, str | None]]:
        if row.change is not None:
            shown = kind_of(row.path).shown_as_file and row.change.group in SHOW_HINT
            return SHOW_HINT[row.change.group] if shown else HINTS[row.change.group]
        return READ_HINT if is_markdown(row.path) else OPEN_HINT

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
        """Only this row: selected, current and anchor."""
        self._cancel_narrow()
        self._advance = None  # choosing a row by hand wins over a pending move
        self.selected_key = self.anchor_key = key
        self.selected_keys = {key} if key is not None else set()
        self._redraw_rows()
        self._scroll_into_view()

    def click(self, y: int, x: int = 0, *, ctrl: bool = False, shift: bool = False) -> None:
        """Explorer rules (REQ-VCS-029): click, Ctrl-click, Shift-click, Ctrl+Shift-click; empty space clears."""
        row = self._row_at(y)
        if not row:
            if not ctrl and not shift:
                self.select_key(None)
            return
        if ctrl or shift:
            self._cancel_narrow()
            self._advance = None
            if shift:
                anchor = self.anchor_key if self._row(self.anchor_key) else row.key
                span = self._span(anchor, row.key)
                self.selected_keys = self.selected_keys | span if ctrl else span
                self.anchor_key = anchor
            else:
                self.selected_keys ^= {row.key}
                self.anchor_key = row.key
            self.selected_key = row.key
            self._redraw_rows()
        elif row.kind == "folder" and x >= self._action_left() and FOLDER_ACTIONS.get(row.group):
            self.select_key(row.key)
            self.click_action()
        elif row.kind in DIRS and row.x <= x < row.x + S["chevron_width"]:
            self._toggle_collapsed(row)
        elif row.key in self.selected_keys and len(self.selected_keys) > 1:
            self._narrow_later(row.key)
        else:
            self.select_key(row.key)

    def _narrow_later(self, key: Key) -> None:
        """A click inside a multiple selection: narrow to the row unless a double click follows (S-16)."""
        self._cancel_narrow()
        self.selected_key = self.anchor_key = key
        self._narrow_after = self.after(DOUBLE_CLICK_MS, lambda: self.select_key(key))
        self._redraw_rows()

    def _narrow_now(self) -> None:
        if self._narrow_after:
            key = self.selected_key
            self._cancel_narrow()
            self.select_key(key)

    def _cancel_narrow(self) -> None:
        if self._narrow_after:
            self.after_cancel(self._narrow_after)
            self._narrow_after = None

    def _span(self, first: Key, last: Key) -> set[Key]:
        keys = [r.key for r in self._rows]
        a, b = sorted((keys.index(first), keys.index(last)))
        return set(keys[a:b + 1])

    def move_current(self, step: int) -> None:
        """Ctrl+↑/↓: move the current row without changing the selection."""
        key = self._step_key(step)
        if key is not None:
            self.selected_key = key
            self._redraw_rows()
            self._scroll_into_view()

    def toggle_current(self) -> None:
        """Ctrl+space: add the current row to the selection or take it out."""
        if self.selected_key is not None:
            self.selected_keys ^= {self.selected_key}
            self.anchor_key = self.selected_key
            self._redraw_rows()

    def select_all(self) -> None:
        self.selected_keys = {r.key for r in self._rows}
        self._redraw_rows()

    def click_action(self) -> None:
        row = self._action_row()
        if row and FOLDER_ACTIONS.get(row.group) and not self._busy():
            self._plan_advance(row, self._folder_paths(row))
            self._on_toggle_folder(row.group, row.path)

    def hover(self, y: int) -> None:
        row = self._row_at(y) if y >= 0 else None
        key = row.key if row else None
        if key != self.hovered_key:
            self.hovered_key = key
            self._redraw_rows()

    def double_click(self, y: int) -> None:
        """Compare only the clicked file; a multiple selection stays (S-16)."""
        row = self._row_at(y)
        if not row:
            return
        self._cancel_narrow()
        if row.key in self.selected_keys:
            self.selected_key = row.key
        else:
            self.select_key(row.key)
        self._open_row(row)

    def press_return(self) -> None:
        row = self._row(self.selected_key)
        if row:
            self._open_row(row)

    def _open_row(self, row: ListRow) -> None:
        """Double click and Enter: fold a folder; compare a changed file; open one without changes by its kind."""
        if row.kind in DIRS:
            self._toggle_collapsed(row)
        elif row.change is not None:
            self._on_activate(row.change)
        else:
            self._on_open(row.path)

    def press_space(self) -> None:
        rows = [r for r in self._rows if r.key in self.selected_keys]
        if not rows or self._busy():  # one operation per repository at a time (REQ-VCS-016)
            return
        if len(rows) > 1:
            self._toggle_selection(rows)
            return
        row = rows[0]
        if row.group == PROJECT:  # the tree keeps its rows: only a changed file has something to do
            if row.kind == "pfile" and row.change is not None:
                self._on_toggle(row.change)
            return
        if row.kind == "folder":
            if FOLDER_ACTIONS.get(row.group):
                self._plan_advance(row, self._folder_paths(row))
                self._on_toggle_folder(row.group, row.path)
            return
        self._plan_advance(row, {row.path})
        self._on_toggle(row.change)

    # ---------- review file by file (REQ-VCS-028) ----------

    # ---------- context menu (DEC-VCS-040) ----------

    def prepare_menu(self, y: int) -> list[tuple[str, bool, Callable[[], None]]]:
        """Select as Explorer does (a row outside the selection becomes the only one) and list the entries:
        label, enabled, command. The commands are space and Enter, so their rules apply (REQ-VCS-028)."""
        row = self._row_at(y)
        if not row:
            return []
        self._cancel_narrow()
        if row.key in self.selected_keys:
            self.selected_key = row.key
            self._redraw_rows()
        else:
            self.select_key(row.key)
        rows = [r for r in self._rows if r.key in self.selected_keys]
        if row.group == PROJECT:
            return self._project_menu(row, single=len(rows) == 1)
        groups = {r.group for r in rows}
        group = rows[0].group if len(groups) == 1 else None
        free = not self._busy()
        paths: set[str] = set()
        for r in rows:
            paths |= self._folder_paths(r) if r.kind == "folder" else {r.path}
        count = f" ({len(paths)})" if len(paths) > 1 else ""
        single_file = len(rows) == 1 and rows[0].kind == "file"
        compare_ok = single_file and group is not Group.CONFLICTS
        entries = [
            (f"Stage{count}", free and group in (Group.CHANGES, Group.UNVERSIONED), self.press_space),
            (f"Unstage{count}", free and group is Group.STAGED, self.press_space),
            ("Oznacz jako rozwiązany", free and group is Group.CONFLICTS and single_file, self.press_space),
            ("Porównaj", compare_ok, self.press_return),
            *self._external_entry(rows[0].change, compare_ok),
            ("Otwórz w aplikacji", single_file and self._on_disk(rows[0].path),
             lambda: self._on_open_in_app(rows[0].path)),
        ]
        entries.append((f"Dodaj do .gitignore{self._ignore_count(rows)}", free and group is Group.UNVERSIONED,
                        lambda: self._ignore_selection(rows)))
        return entries

    def _project_menu(self, row: ListRow, *, single: bool) -> list[tuple[str, bool, Callable[[], None]]]:
        """A row of the project tree: open it by its kind or in its application, show it in Finder, and
        compare it when it changed (REQ-VCS-032, REQ-VCS-034)."""
        entries = [("Otwórz", single, lambda: self._on_open(row.path)),
                   ("Otwórz w aplikacji", single, lambda: self._on_open_in_app(row.path)),
                   ("Pokaż w Finderze", single, lambda: self._on_reveal(row.path))]
        change = row.change
        if single and change is not None and change.group is not Group.CONFLICTS:
            entries.append(("Porównaj", True, lambda: self._on_activate(change)))
            entries += self._external_entry(change, True)
        return entries

    def _external_entry(self, change: FileChange | None, enabled: bool) -> list[tuple[str, bool, Callable[[], None]]]:
        """„Porównaj w narzędziu zewnętrznym”, only while the plugin is set (DEC-VCS-106)."""
        if self._on_compare_external is None or change is None:
            return []
        compare = self._on_compare_external
        return [("Porównaj w narzędziu zewnętrznym", enabled, lambda: compare(change))]

    def _on_disk(self, path: str) -> bool:
        """The working copy exists, so there is something to open in an application (DEC-VCS-104)."""
        repo = self._model.selected_path if self._model else None
        return repo is not None and (repo / path).exists()

    @staticmethod
    def _ignore_count(rows: list[ListRow]) -> str:
        """Entries after merging: a selected folder covers the files below it (counted without git)."""
        folders = [f"{r.path}/" for r in rows if r.kind == "folder"]
        entries = len(folders) + sum(1 for r in rows if r.kind == "file" and not r.path.startswith(tuple(folders)))
        return f" ({entries})" if entries > 1 else ""

    def _ignore_selection(self, rows: list[ListRow]) -> None:
        files = [r.path for r in rows if r.kind == "file"]
        folders = [r.path for r in rows if r.kind == "folder"]
        leaving = set(files)
        for r in rows:
            if r.kind == "folder":
                leaving |= {c.path for c in self._model.files(r.group) if c.path.startswith(f"{r.path}/")}
        self._plan_advance(rows[-1], leaving)
        self._on_ignore(files, folders)

    def open_menu(self, y: int, x_root: int, y_root: int) -> None:
        entries = self.prepare_menu(y)
        if not entries:
            return
        menu = tk.Menu(self, tearoff=0)
        for label, enabled, command in entries:
            if label.startswith("Dodaj do .gitignore"):
                menu.add_separator()
            menu.add_command(label=label, command=command, state=tk.NORMAL if enabled else tk.DISABLED)
        menu.tk_popup(x_root, y_root)

    def _toggle_selection(self, rows: list[ListRow]) -> None:
        """Space on several rows of one group: one operation for all; other groups or conflicts: nothing."""
        group = rows[0].group
        if any(r.group is not group for r in rows) or group in (Group.CONFLICTS, PROJECT):
            return
        paths: set[str] = set()
        for r in rows:
            paths |= self._folder_paths(r) if r.kind == "folder" else {r.path}
        self._plan_advance(rows[-1], paths)
        self._on_toggle_many(group, [c for c in self._model.files(group) if c.path in paths])

    def _busy(self) -> bool:
        model = self._model
        return bool(model and model.selected and model.state(model.selected) is RepoState.BUSY)

    def _folder_paths(self, row: ListRow) -> set[str]:
        return {c.path for c in self._model.files(row.group) if c.path.rpartition("/")[0] == row.path}

    def _plan_advance(self, row: ListRow, leaving: set[str]) -> None:
        """Remember the visible files of the group around the row; set before the operation starts."""
        index = self._rows.index(row)
        files = [(i, r.key) for i, r in enumerate(self._rows)
                 if r.group is row.group and r.kind == "file" and r.path not in leaving]
        self._advance = Advance(self._model.selected, row.group, frozenset(leaving),
                                tuple(key for i, key in files if i > index),
                                tuple(key for i, key in reversed(files) if i < index))

    def _advanced_key(self, keys: set[Key]):
        plan = self._advance
        if plan.leaving <= {c.path for c in self._model.files(plan.group)}:
            return STAY  # nothing left the group: the operation failed or changed nothing
        found = next((key for key in (*plan.after, *plan.before) if key in keys), None)
        if found:
            return found
        below = GROUP_ORDER[GROUP_ORDER.index(plan.group) + 1:]
        return next((r.key for group in below for r in self._rows if r.group is group and r.kind == "file"), None)

    def press_left(self) -> None:
        row = self._row(self.selected_key)
        if row and row.kind in DIRS and not row.collapsed:
            self._toggle_collapsed(row)

    def press_right(self) -> None:
        row = self._row(self.selected_key)
        if row and row.kind in DIRS and row.collapsed:
            self._toggle_collapsed(row)

    def press_down(self, extend: bool = False) -> None:
        self._move(+1, extend)

    def press_up(self, extend: bool = False) -> None:
        self._move(-1, extend)

    def _step_key(self, step: int) -> Key | None:
        if not self._rows:
            return None
        keys = [r.key for r in self._rows]
        index = keys.index(self.selected_key) + step if self.selected_key in keys else (0 if step > 0 else len(keys) - 1)
        return keys[max(0, min(index, len(keys) - 1))]

    def _move(self, step: int, extend: bool = False) -> None:
        """↑/↓ select the next row only; Shift+↑/↓ select from the anchor to it (REQ-VCS-029)."""
        key = self._step_key(step)
        if key is None:
            return
        if not extend:
            self.select_key(key)
            return
        anchor = self.anchor_key if self._row(self.anchor_key) else self.selected_key or key
        self._cancel_narrow()
        self._advance = None
        self.selected_key, self.anchor_key, self.selected_keys = key, anchor, self._span(anchor, key)
        self._redraw_rows()
        self._scroll_into_view()

    def _toggle_collapsed(self, row: ListRow) -> None:
        if row.kind == "pdir":
            self._expanded.symmetric_difference_update({row.path})
        else:
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
        self._rows, self._headers, self._empty, self._placeholder_top = [], [], [], None
        y = S["files_pad_top"]
        anything = any(model.files(group) for group in GROUP_ORDER)
        for group in GROUP_ORDER:
            changes = model.files(group)
            if not changes and group is Group.STAGED and anything:  # P13b: what the commit takes stays in view
                self._headers.append((group.value.upper(), 0, y))
                self._placeholder_top = y + HEADER_HEIGHT
                y += HEADER_HEIGHT + ROW_HEIGHT
                continue
            if not changes:
                continue
            self._headers.append((group.value.upper(), len(changes), y))
            y += HEADER_HEIGHT
            y = self._add_folder_rows(group, changes, y) if model.list_view == "folders" else self._add_flat_rows(changes, y)
        if model.list_view == "project":
            files = model.project_files()
            self._headers.append(("PROJEKT", len(files), y))
            y = self._add_project_rows(files, y + HEADER_HEIGHT)
        self._content_height = max(y, 1)
        moved = self._keep_selection()
        self._redraw_all(model)
        if moved:
            self._scroll_into_view()

    def _add_project_rows(self, files: list, y: int) -> int:
        """Nested folders (closed until opened), then files, by name; a closed folder counts its changes."""
        tree: dict = {}
        for file in files:
            *folders, name = file.path.split("/")
            node = tree
            for folder in folders:
                node = node.setdefault(folder + "/", {})
            node[name] = file

        def changed(node: dict) -> int:
            return sum(changed(v) if isinstance(v, dict) else v.change is not None for v in node.values())

        def add(node: dict, prefix: str, depth: int) -> None:
            nonlocal y
            for key in sorted(k for k in node if k.endswith("/")):
                path, open_ = prefix + key[:-1], prefix + key[:-1] in self._expanded
                count = 0 if open_ else changed(node[key])
                pieces = [(key[:-1], "folder_name")] + ([(changes_label(count), "folder_changes")] if count else [])
                self._rows.append(ListRow("pdir", PROJECT, path, C["ink"], pieces, y, S["indent_flat"] + depth * PROJECT_INDENT,
                                          collapsed=not open_))
                y += ROW_HEIGHT
                if open_:
                    add(node[key], path + "/", depth + 1)
            for key in sorted(k for k in node if not k.endswith("/")):
                file = node[key]
                pieces = file_pieces(file.change, folder_suffix=False) if file.change else [(key, "file_name")]
                self._rows.append(ListRow("pfile", PROJECT, file.path, file_color(file.change) if file.change else C["ink"],
                                          pieces, y, S["indent_icon"] + depth * PROJECT_INDENT, change=file.change))
                y += ROW_HEIGHT

        add(tree, "", 0)
        return y

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

    def _keep_selection(self) -> bool:
        """Drop keys that are gone; carry out a planned move once the repository is free. True if it moved."""
        keys = {r.key for r in self._rows}
        moved = False
        if self._model.selected != self._shown_repo:  # another repository: nothing of the old one stays chosen
            self._shown_repo = self._model.selected
            self._cancel_narrow()
            self.selected_key = self.anchor_key = self._advance = None
            self.selected_keys = set()
        if self._advance is not None and not self._busy():
            target, self._advance = self._advanced_key(keys), None
            if target is not STAY:
                self.selected_key = self.anchor_key = target
                self.selected_keys = {target} if target is not None else set()
                moved = True
        self.selected_keys &= keys
        if self.selected_key not in keys:
            self.selected_key = None
        if self.anchor_key not in keys:
            self.anchor_key = self.selected_key
        if self.hovered_key not in keys:
            self.hovered_key = None
        return moved

    # ---------- drawing ----------

    def _width(self) -> int:
        w = self.canvas.winfo_width()
        return w if w > 1 else 700

    def _action_left(self) -> int:
        return self._width() - S["row_side"] - S["folder_act"]

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
        if self._placeholder_top is not None:
            self._draw_staged_placeholder(self._placeholder_top + ROW_HEIGHT / 2)
        self._redraw_rows()
        c.configure(scrollregion=(0, 0, self._width(), max(self._content_height, c.winfo_height())))

    def _draw_header(self, title: str, count: int, top: int) -> None:
        color = C["conf"] if title == Group.CONFLICTS.value.upper() else theme.TYPE["group_header"].color
        y = top + H_TOP + H_LINE / 2
        side = S["group_side"]
        self.canvas.create_text(side, y, anchor=tk.W, text=title, font=theme.font("group_header"), fill=color)
        x = side + theme.font("group_header").measure(title) + S["group_count_gap"]
        label = files_label(count) if title == "PROJEKT" else str(count)
        self.canvas.create_text(x, y, anchor=tk.W, text=label, font=theme.font("group_count"),
                                fill=theme.TYPE["group_count"].color)

    def _redraw_rows(self) -> None:
        c = self.canvas
        c.delete("row")
        width, action_row = self._width(), self._action_row()
        for row in self._rows:
            fill = C["accent_soft"] if row.key in self.selected_keys else (
                C["row_hover"] if row.key == self.hovered_key else C["bg"])
            c.create_rectangle(0, row.top, width, row.top + row.height, fill=fill, outline="", tags=("row",))
            if row.key == self.selected_key and row.key not in self.selected_keys:  # current, not selected
                c.create_rectangle(0.5, row.top + 0.5, width - 0.5, row.top + row.height - 0.5, outline=C["accent"],
                                   tags=("row", "current_ring"))
            middle = row.top + row.height / 2
            if row.kind in DIRS:
                self._draw_folder(row, middle)
                if row is action_row and FOLDER_ACTIONS.get(row.group):
                    self._draw_action(FOLDER_ACTIONS[row.group], middle)
            else:
                right = width - S["row_side"]
                if row.key == self.hovered_key:  # P12: one hint, only on the row under the pointer
                    right = self._draw_hint(row, right, middle) - S["hint_gap"]
                self._draw_pieces(row, row.x, middle, right)

    def _draw_pieces(self, row: ListRow, x: float, middle: float, right: float | None = None) -> None:
        pieces = row.pieces if right is None else fit_pieces(row.pieces, right - x)
        for index, (text, role) in enumerate(pieces):
            if index:
                x += S["suffix_gap"]
            color = row.color if role in ("file_name", "file_name_del") else theme.TYPE[role].color
            self.canvas.create_text(x, middle, anchor=tk.W, text=text, font=theme.font(role), fill=color, tags=("row",))
            x += theme.font(role).measure(text)

    def _draw_staged_placeholder(self, middle: float) -> None:
        """Not a row: selection, hover and keys never reach it."""
        c, x = self.canvas, S["indent_flat"]
        pad_x, _ = S["kbd_pad"]
        kbd_font, hint_font = theme.font("kbd"), theme.font("hint")
        tags = ("staged_placeholder",)
        for text, kind in EMPTY_STAGED:
            if kind == KBD:
                w, h = kbd_font.measure(text) + 2 * pad_x, kbd_font.metrics("linespace") + 2
                rounded_rect(c, x, middle - h / 2, x + w, middle + h / 2, S["kbd_radius"],
                             fill=C["kbd_bg"], outline=C["kbd_border"], tags=tags)
                c.create_text(x + w / 2, middle, text=text, font=kbd_font, fill=theme.TYPE["kbd"].color, tags=tags)
            else:
                w = hint_font.measure(text)
                c.create_text(x, middle, anchor=tk.W, text=text, font=hint_font, fill=theme.TYPE["hint"].color, tags=tags)
            x += w

    def _draw_folder(self, row: ListRow, middle: float) -> None:
        c = self.canvas
        c.create_text(row.x + S["chevron_width"] / 2, middle, text="▸" if row.collapsed else "▾",
                      font=theme.font("folder_count"), fill=C["dim"], tags=("row",))
        w, h = S["folder_icon"]
        left, top = row.x + S["indent_icon"] - S["indent_chevron"], middle - h / 2   # 18 after the chevron
        rounded_rect(c, left, top, left + w * 0.45, top + 3, 1.5, fill=C["folder_icon"], tags=("row",))   # tab
        rounded_rect(c, left, top + 2, left + w, top + h, 2, fill=C["folder_icon"], tags=("row",))        # body
        self._draw_pieces(row, row.x + S["indent_child"] - S["indent_chevron"], middle)

    def _draw_action(self, glyph: str, middle: float) -> None:
        size, left = S["folder_act"], self._action_left()
        rounded_rect(self.canvas, left, middle - size / 2, left + size, middle + size / 2, S["folder_act_radius"],
                     fill=C["folder_act_hover"], tags=("row",))
        self.canvas.create_text(left + size / 2, middle, text=glyph, font=theme.font("folder_act"),
                                fill=theme.TYPE["folder_act"].color, tags=("row",))

    def _draw_hint(self, row: ListRow, right: float, middle: float) -> float:
        """Draw the hint ending at `right`; return where it starts."""
        c = self.canvas
        pad_x, _ = S["kbd_pad"]
        kbd_font, hint_font = theme.font("kbd"), theme.font("hint")
        for text, kind in reversed(self._hints(row)):
            if kind == KBD:
                w = kbd_font.measure(text) + 2 * pad_x
                h = kbd_font.metrics("linespace") + 2
                rounded_rect(c, right - w, middle - h / 2, right, middle + h / 2, S["kbd_radius"],
                             fill=C["kbd_bg"], outline=C["kbd_border"], tags=("row", "hint"))
                c.create_text(right - w / 2, middle, text=text, font=kbd_font, fill=theme.TYPE["kbd"].color,
                              tags=("row", "hint"))
            else:
                w = hint_font.measure(text)
                c.create_text(right, middle, anchor=tk.E, text=text, font=hint_font,
                              fill=theme.TYPE["hint"].color, tags=("row", "hint"))
            right -= w
        return right

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
