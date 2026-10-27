"""The history panel E-06 at the bottom of the window, always visible (DEC-VCS-118).

It only draws HistorySession and passes clicks and keys back. The list of commits draws just the rows in
view, with their piece of the graph (P. Vigier: drawing only the visible part is what keeps long histories
fast). Lanes beyond the eighth are not drawn and their commits get a hollow dot in the eighth column (H-33);
a filtered list has dots only (H-34). The details show the selected commit and its files.

Trace: DES-VCS-079, REQ-VCS-040, DES-VCS-078, REQ-VCS-045, DES-VCS-077, REQ-VCS-044, DES-VCS-075, REQ-VCS-105, DES-VCS-070, DES-VCS-071, REQ-VCS-041, DEC-VCS-124, DEC-VCS-123, DES-VCS-069, REQ-VCS-036, REQ-VCS-037, REQ-VCS-038, REQ-VCS-039, REQ-VCS-040, DEC-VCS-118, DEC-VCS-121, E-06
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import datetime

from vcs_lite.app.history import HistorySession, commits_label, date_label
from vcs_lite.core.graph import Edge, GraphRow
from vcs_lite.core.log import Commit, CommitFile, RefKind, Scope
from vcs_lite.ui.scrolling import ScrollPane
from vcs_lite.ui import theme
from vcs_lite.core.changes import LineStats
from vcs_lite.ui.widgets import draw_line_counts, SegmentedControl, elide, elide_middle, hint_over, rounded_rect

C, S = theme.COLORS, theme.SPACE
GRIP = (36, 3)            # the handle under the sash, width × height (UI-REFERENCE §12)
RESIZE_CURSOR = "sb_v_double_arrow"
ROW = 24                  # a commit or a file
LANE = 16                 # a column of the graph
FIRST_LANE = 12           # the middle of the first column
LANES = 8                 # columns drawn; further ones are clipped (H-33)
AUTHOR_WIDTH, DATE_WIDTH, RIGHT_PAD = 120, 104, 12
MORE_AHEAD = 50           # rows left below the view when the next page is read (H-06)
SCOPES = (("all", "Wszystkie"), ("current", "Bieżąca"))
REF_STYLE = {             # (background, text role)
    "ref_current": ("accent_soft", "ref_chip_strong"),
    "ref_local": ("accent_soft", "ref_chip_strong"),
    "ref_head": ("accent_soft", "ref_chip_strong"),
    "ref_remote": ("chip_bg", "ref_chip"),
    "ref_tag": ("ref_tag", "ref_chip"),
}
FILE_COLORS = {"A": "file_add", "D": "file_del", "M": "file_mod", "T": "file_mod", "R": "file_ren", "C": "file_ren"}


def lane_color(index: int) -> str:
    return C[f"lane_{index % LANES}"]


def graph_width(rows: list[GraphRow]) -> int:
    """Room for the graph: its widest row, at most LANES columns; one column for a filtered list."""
    lanes = min(max((row.width for row in rows), default=1), LANES)
    return lanes * LANE + 20


def dot_style(row: GraphRow | None, commit: Commit) -> tuple[int, str]:
    """Column and kind of a commit's dot: full, merge (hollow) or clipped (hollow in the last column)."""
    if row is None:
        return 0, "merge" if commit.merge else "full"
    if row.column >= LANES:
        return LANES - 1, "clipped"
    return row.column, "merge" if commit.merge else "full"


def title_pieces(commit: Commit, *, unpushed: bool) -> list[tuple[str, str]]:
    """What a row says before the author: ↑ for an unpushed commit, the labels, the subject (H-07, H-09, H-10)."""
    pieces = [("↑", "unpushed")] if unpushed else []
    for ref in commit.refs:
        kind = "ref_current" if ref.current else {RefKind.LOCAL: "ref_local", RefKind.REMOTE: "ref_remote",
                                                  RefKind.TAG: "ref_tag", RefKind.HEAD: "ref_head"}[ref.kind]
        pieces.append((ref.name, kind))
    if not commit.subject:
        pieces.append(("(bez opisu)", "subject_empty"))
    else:
        pieces.append((commit.subject, "subject_out" if unpushed else "subject"))
    return pieces


def edge_paths(edge: Edge, *, bottom: float) -> list[tuple[list[float], bool]]:
    """Points of an edge in the canvas, each piece with whether it is a Bézier curve (DEC-VCS-123): a change
    of column takes one whole row and leaves and enters vertically; the rest is straight down the lane. An
    open edge runs to `bottom`. A lane beyond the last drawn column is not drawn (H-33)."""
    if edge.lane >= LANES:
        return []

    def x(column: int) -> float:
        return FIRST_LANE + min(column, LANES - 1) * LANE

    def y(row: int) -> float:
        return row * ROW + ROW / 2

    def curve(x1: float, y1: float, x2: float, y2: float) -> tuple[list[float], bool]:
        middle = (y1 + y2) / 2
        return [x1, y1, x1, middle, x2, middle, x2, y2], True

    start_x, lane_x, top = x(edge.from_col), x(edge.lane), y(edge.from_row)
    if edge.to_row is None:
        end_x, end = lane_x, bottom
    else:
        end_x, end = x(edge.to_col), y(edge.to_row)
    leaves, enters = start_x != lane_x, end_x != lane_x
    if leaves and enters and edge.to_row == edge.from_row + 1:
        return [curve(start_x, top, end_x, end)]
    pieces = []
    if leaves:
        pieces.append(curve(start_x, top, lane_x, top + ROW))
        top += ROW
    bend = end - ROW if enters else end
    if bend > top:
        pieces.append(([lane_x, top, lane_x, bend], False))
    if enters:
        pieces.append(curve(lane_x, bend, end_x, end))
    return pieces


def full_date(timestamp: int) -> str:
    return f"{datetime.fromtimestamp(timestamp):%d.%m.%Y %H:%M}"


class HistoryPanel(tk.Frame):
    def __init__(self, master: tk.Misc, session: HistorySession | None = None, *,
                 on_open_file: Callable[[Commit, CommitFile], None] = lambda commit, file: None,
                 clipboard: Callable[[str], None] = lambda text: None,
                 open_url: Callable[[str], None] = lambda url: None):
        super().__init__(master, bg=C["bg"], cursor="arrow")
        self.session = session
        self.grip_color = C["seg_thumb_edge"]
        self._grip = tk.Canvas(self, height=GRIP[1] + 2, bg=C["panel"], highlightthickness=0, bd=0)
        self._grip.pack(fill=tk.X)
        self._grip.bind("<Configure>", lambda _e: self._draw_grip())
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(side=tk.TOP, fill=tk.X)
        self._build_header()
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(fill=tk.X)
        body = tk.Frame(self, bg=C["line"])
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(side=tk.BOTTOM, fill=tk.X)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(0, weight=62, uniform="split")
        body.columnconfigure(1, weight=38, uniform="split")
        body.rowconfigure(0, weight=1)
        self.commit_list = CommitList(body, session, clipboard=clipboard, open_url=open_url, on_open_file=on_open_file)
        self.commit_list.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, S["line"]))
        self.details = CommitView(body, session, on_open_file=on_open_file,
                                  on_show_history=lambda path: session.show_path(path, folder=False))
        self.details.grid(row=0, column=1, sticky=tk.NSEW)
        if session:
            session.subscribe(self.render)
        self.render()

    def _build_header(self) -> None:
        header = self._header = tk.Frame(self, bg=C["panel"], padx=14, pady=5)
        header.pack(fill=tk.X)
        self.title = theme.label(header, "history_title", "Historia", bg=C["panel"])
        self.title.pack(side=tk.LEFT)
        for handle in self.handles():
            handle.configure(cursor=RESIZE_CURSOR)
        if self.session is None:
            self.filter, self.scope, self._count, self._path = tk.StringVar(self), None, None, None
            return
        field = tk.Frame(header, bg=C["bg"], cursor="arrow", highlightthickness=1, highlightbackground=C["control_border"])
        field.pack(side=tk.LEFT, padx=(10, 0))
        theme.label(field, "placeholder", "⌕", bg=C["bg"]).pack(side=tk.LEFT, padx=(6, 4))
        self.filter = tk.StringVar(self)
        entry = tk.Entry(field, textvariable=self.filter, bd=0, highlightthickness=0, bg=C["bg"], fg=C["ink"],
                         insertbackground=C["ink"], font=theme.font("body"), width=30)
        entry.pack(side=tk.LEFT, pady=2, padx=(0, 6))
        hint_over(entry, self.filter, "Filtr: wiadomość, hash albo autor")
        self.filter.trace_add("write", lambda *_a: self.session.set_text(self.filter.get()))
        theme.label(header, "history_meta", "Gałęzie", bg=C["panel"], cursor="arrow").pack(side=tk.LEFT, padx=(10, S["seg_label_gap"]))
        self.scope = SegmentedControl(header, SCOPES, self.session.query.scope.value,
                                      lambda value: self.session.set_scope(Scope(value)), parent_bg=C["panel"])
        self.scope.configure(cursor="arrow")
        self.scope.pack(side=tk.LEFT)
        self._path = tk.Label(header, text="", font=theme.font("history_meta"), bg=C["accent_soft"],
                              fg=C["ref_local_ink"], padx=8, pady=1, cursor="hand2")   # „Plik: … ✕” (DEC-VCS-124)
        self._path.bind("<Button-1>", lambda _e: self.clear_path())
        self._count = theme.label(header, "history_meta", "", bg=C["panel"], cursor="arrow")
        self._count.pack(side=tk.RIGHT)

    def handles(self) -> list[tk.Misc]:
        """What drags the border besides the border itself: the grip and the free part of the header,
        not its controls (DEC-VCS-121)."""
        return [self._grip, self._header, self.title]

    def highlight(self, on: bool) -> None:
        """The grip in accent while the pointer is over the border or the header (DEC-VCS-121)."""
        color = C["accent"] if on else C["seg_thumb_edge"]
        if color != self.grip_color:
            self.grip_color = color
            self._draw_grip()

    def _draw_grip(self) -> None:
        canvas = self._grip
        canvas.delete("all")
        w, h = GRIP
        left = (canvas.winfo_width() - w) / 2
        canvas.create_rectangle(left, 1, left + w, 1 + h, fill=self.grip_color, outline=self.grip_color)

    @property
    def path_text(self) -> str:
        return self._path.cget("text") if self._path and self._path.winfo_manager() else ""

    def clear_path(self) -> None:
        self.session.clear_path()

    @property
    def count_text(self) -> str:
        return self._count.cget("text") if self._count else ""

    def render(self) -> None:
        session = self.session
        if session and self._count:
            self._count.configure(text=commits_label(session.count) if session.commits else "")
            query = session.query
            if query.path:
                self._path.configure(text=f"{'Folder' if query.folder else 'Plik'}: {query.path} ✕")
                self._path.pack(side=tk.LEFT, padx=(10, 0))
            else:
                self._path.pack_forget()
        self.commit_list.render()
        self.details.render()


class CommitList(tk.Frame):
    def __init__(self, master: tk.Misc, session: HistorySession | None, *, clipboard: Callable[[str], None],
                 open_url: Callable[[str], None], on_open_file: Callable[[Commit, CommitFile], None]):
        super().__init__(master, bg=C["bg"])
        self.session, self._clipboard, self._open_url = session, clipboard, open_url
        self._on_open_file = on_open_file
        self.scroller = ScrollPane(self, bg=C["bg"])
        self.scroller.pack(fill=tk.BOTH, expand=True)
        self.canvas = c = tk.Canvas(self.scroller, bg=C["bg"], highlightthickness=0, bd=0, takefocus=True)
        self.scroller.attach(c, on_view=lambda *_: self.render())
        self.drawn: list[int] = []
        self.placeholder_text = ""
        self._hover = -1
        c.bind("<Configure>", lambda _e: self.render())
        c.bind("<MouseWheel>", lambda e: self.scroll(e.delta))
        c.bind("<Button-1>", lambda e: (c.focus_set(), self.click(e.y)))
        c.bind("<Motion>", lambda e: self._set_hover(self.index_at(e.y)))
        c.bind("<Leave>", lambda _e: self._set_hover(-1))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.y))
        c.bind("<Return>", lambda _e: self.open_selected())
        c.bind("<Up>", lambda _e: self.press_up())
        c.bind("<Down>", lambda _e: self.press_down())
        for sequence in ("<Button-2>", "<Button-3>"):  # right button and two-finger click
            c.bind(sequence, lambda e: self.open_menu(e.y, e.x_root, e.y_root))

    # ---------- reading what is drawn ----------

    def _view_height(self) -> int:
        c = self.canvas
        return c.winfo_height() if c.winfo_ismapped() else c.winfo_reqheight()

    def _view_width(self) -> int:
        c = self.canvas
        return c.winfo_width() if c.winfo_ismapped() else max(c.winfo_reqwidth(), 600)

    def index_at(self, y: int) -> int:
        """`y` in window coordinates; -1 below the last commit."""
        index = int(self.canvas.canvasy(y) // ROW)
        return index if self.session and 0 <= index < len(self.session.commits) else -1

    # ---------- events ----------

    def click(self, y: int) -> None:
        index = self.index_at(y)
        if index >= 0:
            self.session.select(index)

    def double_click(self, y: int) -> None:
        index = self.index_at(y)
        if index >= 0:
            self.session.select(index)
            self.open_selected()

    def open_selected(self) -> None:
        """In a file's history: the file's diff in the selected commit, under its name there (H-55)."""
        commit = self.session.selected_commit if self.session else None
        change = self.session.path_change(commit) if commit else None
        if change:
            self._on_open_file(commit, change)

    def press_up(self) -> None:
        if self.session:
            self.session.move(-1)
            self._keep_in_view()

    def press_down(self) -> None:
        if self.session:
            self.session.move(+1)
            self._keep_in_view()

    def scroll(self, delta: int) -> None:
        c = self.canvas
        if self.session and len(self.session.commits) * ROW > self._view_height():
            c.yview_scroll(-delta, "units")
        self.render()

    def scroll_to_end(self) -> None:
        self.canvas.yview_moveto(1.0)
        self.render()

    def _keep_in_view(self) -> None:
        c, index = self.canvas, self.session.selected
        top, height = c.canvasy(0), self._view_height()
        total = max(len(self.session.commits) * ROW, 1)
        if index * ROW < top:
            c.yview_moveto(index * ROW / total)
        elif (index + 1) * ROW > top + height:
            c.yview_moveto(((index + 1) * ROW - height) / total)
        self.render()

    def _set_hover(self, index: int) -> None:
        if index != self._hover:
            self._hover = index
            self.render()

    def prepare_menu(self, index: int) -> list[tuple[str, bool, Callable[[], None]]]:
        """The commit's menu (H-47); only reading, nothing that changes the repository."""
        commit = self.session.commits[index]
        url = self.session.commit_url(commit)
        return [("Kopiuj hash", True, lambda: self._clipboard(commit.hash)),
                ("Kopiuj adres commita", url is not None, lambda: self._clipboard(url)),
                ("Otwórz w przeglądarce", url is not None, lambda: self._open_url(url))]

    def open_menu(self, y: int, x_root: int, y_root: int) -> None:
        index = self.index_at(y)
        if index < 0:
            return
        self.session.select(index)
        menu = tk.Menu(self, tearoff=0)
        for label, enabled, command in self.prepare_menu(index):
            menu.add_command(label=label, command=command, state=tk.NORMAL if enabled else tk.DISABLED)
        menu.tk_popup(x_root, y_root)

    # ---------- drawing ----------

    def render(self) -> None:
        c, session = self.canvas, self.session
        c.delete("all")
        self.drawn = []
        width, height = self._view_width(), self._view_height()
        self.placeholder_text = (session.placeholder or "") if session else ""
        if not session or not session.commits:
            c.configure(scrollregion=(0, 0, width, height))
            c.yview_moveto(0)
            if self.placeholder_text:
                c.create_text(width / 2, height / 2, text=self.placeholder_text, font=theme.font("hint"),
                              fill=C["dim"], width=width - 40, justify=tk.CENTER)
            return
        total = len(session.commits) * ROW
        c.configure(scrollregion=(0, 0, width, max(total, height)))
        top = int(c.canvasy(0))
        first, last = max(0, top // ROW), min(len(session.commits), (top + height) // ROW + 1)
        text_x = graph_width(session.rows)
        for index in range(first, last):
            self._draw_background(index, width)
        self._draw_edges(first, last, max(total, height))
        for index in range(first, last):
            self._draw_row(index, width, text_x)
            self.drawn.append(index)
        if last >= len(session.commits) - MORE_AHEAD:
            session.load_more()

    def _draw_background(self, index: int, width: int) -> None:
        top, bottom = index * ROW, (index + 1) * ROW
        if index == self.session.selected:
            self.canvas.create_rectangle(0, top, width, bottom, fill=C["accent_soft"], outline="")
        elif index == self._hover:
            self.canvas.create_rectangle(0, top, width, bottom, fill=C["row_hover"], outline="")

    def _draw_edges(self, first: int, last: int, bottom: float) -> None:
        """Every edge crossing the view, whole, so lines run smooth across rows (DEC-VCS-123)."""
        for edge in self.session.edges:
            if edge.from_row <= last and (edge.to_row is None or edge.to_row >= first):
                for points, curved in edge_paths(edge, bottom=bottom):
                    self.canvas.create_line(*points, fill=lane_color(edge.color), width=2, capstyle=tk.ROUND,
                                            smooth="raw" if curved else False, splinesteps=24)

    def _draw_row(self, index: int, width: int, text_x: int) -> None:
        c, session = self.canvas, self.session
        commit = session.commits[index]
        row = session.rows[index] if session.rows else None
        middle = index * ROW + ROW / 2
        self._draw_dot(row, commit, middle, selected=index == session.selected)
        right = width - RIGHT_PAD - DATE_WIDTH - AUTHOR_WIDTH
        self._draw_title(commit, text_x, middle, right - 12, unpushed=commit.hash in session.unpushed)
        author_font = theme.font("history_meta")
        c.create_text(right, middle, anchor=tk.W, text=elide(commit.author, author_font, AUTHOR_WIDTH - 8),
                      font=author_font, fill=C["dim"])
        c.create_text(width - RIGHT_PAD - DATE_WIDTH, middle, anchor=tk.W, font=author_font, fill=C["dim"],
                      text=date_label(commit.time, datetime.now()))

    def _draw_dot(self, row: GraphRow | None, commit: Commit, middle: float, *, selected: bool) -> None:
        column, style = dot_style(row, commit)
        color = lane_color(row.color if row else 0)
        r = 5 if selected else 4
        cx = FIRST_LANE + column * LANE
        if style == "full":
            self.canvas.create_oval(cx - r, middle - r, cx + r, middle + r, fill=color, outline=color)
        else:
            self.canvas.create_oval(cx - r, middle - r, cx + r, middle + r, fill=C["bg"], outline=color, width=2)

    def _draw_title(self, commit: Commit, x: float, middle: float, right: float, *, unpushed: bool) -> None:
        c = self.canvas
        for text, role in title_pieces(commit, unpushed=unpushed):
            if x >= right:
                return
            if role in REF_STYLE:
                fill, text_role = REF_STYLE[role]
                font = theme.font(text_role)
                label = elide(text, font, int(right - x - 12))
                w = font.measure(label) + 12
                rounded_rect(c, x, middle - 8, x + w, middle + 8, 4, fill=C[fill])
                c.create_text(x + w / 2, middle, text=label, font=font, fill=theme.TYPE[text_role].color)
                x += w + 6
            else:
                font = theme.font(role)
                label = elide(text, font, int(right - x))
                c.create_text(x, middle, anchor=tk.W, text=label, font=font, fill=theme.TYPE[role].color)
                x += font.measure(label) + 6


class CommitView(tk.Frame):
    """Details of the selected commit and its files (H-45); a double click on a file opens its diff (H-46)."""

    PAD_X, PAD_Y = 14, 10

    def __init__(self, master: tk.Misc, session: HistorySession | None, *,
                 on_open_file: Callable[[Commit, CommitFile], None], on_show_history: Callable[[str], None]):
        super().__init__(master, bg=C["bg"])
        self.session, self._on_open_file, self._on_show_history = session, on_open_file, on_show_history
        self.scroller = ScrollPane(self, bg=C["bg"])
        self.scroller.pack(fill=tk.BOTH, expand=True)
        self.canvas = c = tk.Canvas(self.scroller, bg=C["bg"], highlightthickness=0, bd=0)
        self.title_text = ""
        self.selected_path: str | None = None
        self._shown_context: tuple | None = None
        self._files: list[tuple[CommitFile, int]] = []
        self._parents: list[tuple[str, tuple[int, int, int, int]]] = []
        self._hover = -1
        self._painted_top: float | None = None
        self.scroller.attach(c, on_view=self._viewport_changed)
        c.bind("<Configure>", lambda _e: self.render())
        c.bind("<MouseWheel>", lambda e: (c.yview_scroll(-e.delta, "units"), self.render()))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.y))
        c.bind("<Button-1>", lambda e: self.click(e.x, e.y))
        c.bind("<Motion>", lambda e: self._set_hover(self.file_index_at(e.y)))
        c.bind("<Leave>", lambda _e: self._set_hover(-1))
        for sequence in ("<Button-2>", "<Button-3>"):  # right button and two-finger click
            c.bind(sequence, lambda e: self.open_file_menu(e.y, e.x_root, e.y_root))

    def prepare_file_menu(self, y: int) -> list[tuple[str, bool, Callable[[], None]]]:
        """A file of the commit: its diff, or its own history (DEC-VCS-124)."""
        index = self.file_index_at(y)
        commit = self.session.selected_commit if self.session else None
        if index < 0 or commit is None:
            return []
        file = self._files[index][0]
        return [("Porównaj", True, lambda: self._on_open_file(commit, file)),
                ("Pokaż historię", True, lambda: self._on_show_history(file.path))]

    def open_file_menu(self, y: int, x_root: int, y_root: int) -> None:
        self._select_file(self.file_index_at(y))
        entries = self.prepare_file_menu(y)
        if not entries:
            return
        menu = tk.Menu(self, tearoff=0)
        for label, enabled, command in entries:
            menu.add_command(label=label, command=command, state=tk.NORMAL if enabled else tk.DISABLED)
        menu.tk_popup(x_root, y_root)

    def file_rows(self) -> list[tuple[CommitFile, int]]:
        return list(self._files)

    def file_index_at(self, y: int) -> int:
        y = self.canvas.canvasy(y)
        return next((i for i, (_, top) in enumerate(self._files) if top <= y < top + ROW), -1)

    def double_click(self, y: int) -> None:
        index = self.file_index_at(y)
        commit = self.session.selected_commit if self.session else None
        if index >= 0 and commit:
            self._select_file(index)
            self._on_open_file(commit, self._files[index][0])

    def _select_file(self, index: int) -> None:
        if 0 <= index < len(self._files):
            self.selected_path = self._files[index][0].path
            self.render()

    def click(self, x: int, y: int) -> None:
        """A parent's hash goes to that commit when it is in the list."""
        index = self.file_index_at(y)
        if index >= 0:
            self._select_file(index)
            return
        x, y = self.canvas.canvasx(x), self.canvas.canvasy(y)
        for parent, (x1, y1, x2, y2) in self._parents:
            if x1 <= x <= x2 and y1 <= y <= y2:
                index = next((i for i, c in enumerate(self.session.commits) if c.hash == parent), -1)
                if index >= 0:
                    self.session.select(index)
                return

    def _set_hover(self, index: int) -> None:
        if index != self._hover:
            self._hover = index
            self.render()

    def _viewport_changed(self, *_fractions) -> None:
        if self.canvas.canvasy(0) != self._painted_top:
            self._hover = -1
            self.render()

    def render(self) -> None:
        c, session = self.canvas, self.session
        commit = session.selected_commit if session else None
        context = (session.repo_path, commit.hash) if commit else None
        if context != self._shown_context:
            self._shown_context = context
            self.selected_path, self._hover = None, -1
            c.yview_moveto(0)
        self._painted_top = c.canvasy(0)
        c.delete("all")
        self._files, self._parents = [], []
        self.title_text = commit.subject if commit else ""
        width = c.winfo_width() if c.winfo_ismapped() else max(c.winfo_reqwidth(), 400)
        if commit is None:
            c.configure(scrollregion=(0, 0, width, c.winfo_height()))
            return
        x, room = self.PAD_X, width - 2 * self.PAD_X
        y = self.PAD_Y
        title = c.create_text(x, y, anchor=tk.NW, text=commit.subject or "(bez opisu)", width=room,
                              font=theme.font("details_title"), fill=C["ink"] if commit.subject else C["dim"])
        y = c.bbox(title)[3] + 4
        y = self._draw_meta(commit, x, y, room) + 4
        details = session.details if session.details and session.details.commit == commit else None
        if details and details.body:
            body = c.create_text(x, y, anchor=tk.NW, text=details.body, width=room, font=theme.font("details_body"),
                                 fill=theme.TYPE["details_body"].color)
            y = c.bbox(body)[3] + 8
        if details:
            y = self._draw_files(details.files, x, y + 4, width, details.lines)
        c.configure(scrollregion=(0, 0, width, max(y + self.PAD_Y, c.winfo_height())))

    def _draw_meta(self, commit: Commit, x: float, y: float, room: float) -> float:
        c = self.canvas
        pieces = [(commit.short, "hash", None), (f"{commit.author} <{commit.email}>", "history_meta", None),
                  (full_date(commit.time), "history_meta", None)]
        if commit.parents:
            pieces.append(("rodzic" if len(commit.parents) == 1 else "rodzice", "history_meta", None))
            pieces += [(p[:7], "link", p) for p in commit.parents]
        right, line_height = x + room, theme.font("history_meta").metrics("linespace")
        for text, role, parent in pieces:
            font = theme.font(role)
            w = font.measure(text)
            if x + w > right and x > self.PAD_X:
                x, y = self.PAD_X, y + line_height + 2
            item = c.create_text(x, y, anchor=tk.NW, text=text, font=font, fill=theme.TYPE[role].color or C["ink"])
            if parent:
                self._parents.append((parent, c.bbox(item)))
            x += w + 10
        return y + line_height

    def _draw_files(self, files: tuple[CommitFile, ...], x: float, y: float, width: int,
                    lines: dict[str, LineStats]) -> float:
        c = self.canvas
        header_font = theme.font("group_header")
        c.create_text(x, y, anchor=tk.NW, text="PLIKI", font=header_font, fill=theme.TYPE["group_header"].color)
        c.create_text(x + header_font.measure("PLIKI") + 8, y, anchor=tk.NW, text=str(len(files)),
                      font=theme.font("group_count"), fill=theme.TYPE["group_count"].color)
        known = [lines.get(file.path, LineStats(kind="unknown")) for file in files]
        if all(line.kind in {"text", "binary"} for line in known):
            added = sum(line.added for line in known)
            removed = sum(line.removed for line in known)
            summary = f"+{added:,} −{removed:,}".replace(",", "\u202f")
        else:
            summary = "—"
        c.create_text(width - self.PAD_X, y, anchor=tk.NE, text=summary,
                      font=theme.font("group_count"), fill=C["dim"], tags=("commit_line_totals",))
        y += header_font.metrics("linespace") + 6
        name_font, folder_font = theme.font("file_name"), theme.font("file_folder")
        self._files = [(file, int(y + index * ROW)) for index, file in enumerate(files)]
        height = c.winfo_height() if c.winfo_ismapped() else c.winfo_reqheight()
        view_top = c.canvasy(0)
        first = max(0, int((view_top - y) // ROW) - 1)
        last = min(len(files), int((view_top + height - y) // ROW) + 2)
        for index in range(first, last):
            file, top = self._files[index]
            middle = top + ROW / 2
            selected = file.path == self.selected_path
            if selected or index == self._hover:
                c.create_rectangle(0, top, width, top + ROW,
                                   fill=C["accent_soft"] if selected else C["row_hover"], outline="",
                                   tags=("selected_commit_file",) if selected else ())
            right = width - self.PAD_X
            draw_line_counts(c, lines.get(file.path, LineStats(kind="unknown")), right, middle)
            right -= S["line_counts_width"] + S["hint_gap"]
            show_hint = index == self._hover and width >= S["inline_hint_min_width"]
            if show_hint:
                c.create_text(right, middle, anchor=tk.E, text="dwuklik porównaj",
                              font=theme.font("hint"), fill=C["dim"])
            folder, _, name = file.path.rpartition("/")
            role = "file_name_del" if file.status == "D" else "file_name"
            room = max(0, right - x - (110 if show_hint else 0))
            shown = elide(name, theme.font(role), int(room))
            c.create_text(x, middle, anchor=tk.W, text=shown, font=theme.font(role), fill=C[FILE_COLORS.get(file.status, "file_mod")])
            after = name_font.measure(shown) + 8
            extra = f"← {file.old_path}" if file.old_path else folder
            if extra and room - after > folder_font.measure("x…x"):
                c.create_text(x + after, middle, anchor=tk.W, text=elide_middle(extra, folder_font, int(room - after)),
                              font=folder_font, fill=C["dim"])
        return y + len(files) * ROW
