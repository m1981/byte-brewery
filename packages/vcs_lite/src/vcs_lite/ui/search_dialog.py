"""The search window E-04 after the reference (section 10, layout A): phrase with "Aa" and "W", file mask,
matches with their file on the right, status line. It only draws the SearchSession and passes events on.

The focus stays in the phrase field: ↑ ↓ move the selection, ↩ opens, Esc closes. ⌥⌘C and ⌥⌘W switch the
options; plain ⌥C would type "ć" on the Polish keyboard (DEC-VCS-109).

Trace: DES-VCS-057, DES-VCS-042, REQ-VCS-033, DEC-VCS-097, DEC-VCS-109, E-04
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from vcs_lite.app.search import SearchSession
from vcs_lite.core.search import Match, SearchQuery
from vcs_lite.ui import theme
from vcs_lite.ui.keys import DoubleShift
from vcs_lite.ui.widgets import Toggle, Tooltip, elide, elide_middle, kbd

C, S = theme.COLORS, theme.SPACE
ROW_HEIGHT = S["row_height"]
SHORTCUT_CASE, SHORTCUT_WORD = "<Command-Option-c>", "<Command-Option-w>"
KEYS = ((("↑", "↓"), " wybór"), (("↩",), " otwórz"), (("esc",), " zamknij"))   # right of the status line


@dataclass(frozen=True)
class ResultRow:
    match: Match
    color: str      # of the file name: its status colour, or ink when unchanged
    top: int

    @property
    def path(self) -> str:
        return self.match.path

    @property
    def line(self) -> int:
        return self.match.line

    @property
    def text(self) -> str:
        return self.match.text


def line_pieces(match: Match) -> list[tuple[str, bool]]:
    """The shown line as (text, is a match), with "…" where it was cut."""
    pieces, at = [("…", False)] if match.cut_start else [], 0
    for start, end in match.spans:
        pieces += [(match.text[at:start], False), (match.text[start:end], True)]
        at = end
    pieces.append((match.text[at:], False))
    if match.cut_end:
        pieces.append(("…", False))
    return [(text, hit) for text, hit in pieces if text]


class ResultList(tk.Frame):
    """Matches on a canvas: 24 pt rows, the matched text on the hit colour, file, folder and line on the right."""

    def __init__(self, master: tk.Misc, session: SearchSession, color_of: Callable[[str], str],
                 on_open: Callable[[], None]):
        super().__init__(master, bg=C["bg"])
        self._session, self._color_of, self._on_open = session, color_of, on_open
        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0, yscrollincrement=2)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._rows: list[ResultRow] = []
        self._shown: dict[int, str] = {}     # row top -> the line text as drawn
        self._placeholder: list[str] = []
        self.hovered = -1
        c = self.canvas
        c.bind("<Button-1>", lambda e: self.click(e.y))
        c.bind("<Double-Button-1>", lambda e: self.double_click(e.y))
        c.bind("<Motion>", lambda e: self.hover(e.y))
        c.bind("<Leave>", lambda e: self.hover(-1))
        c.bind("<MouseWheel>", lambda e: self.scroll(e.delta))
        c.bind("<Configure>", lambda e: self.render())

    # ---------- reading what was drawn ----------

    def rows(self) -> list[ResultRow]:
        return list(self._rows)

    @property
    def selected(self) -> int:
        return self._session.selected

    def hit_count(self) -> int:
        return len(self.canvas.find_withtag("hit"))

    def shown_text(self, row: ResultRow) -> str:
        return self._shown.get(row.top, "")

    def placeholder_texts(self) -> list[str]:
        return list(self._placeholder)

    # ---------- interaction ----------

    def _index_at(self, y: int) -> int:
        y = self.canvas.canvasy(y)
        return next((i for i, r in enumerate(self._rows) if r.top <= y < r.top + ROW_HEIGHT), -1)

    def click(self, y: int) -> None:
        index = self._index_at(y)
        if index >= 0:
            self._session.select(index)

    def double_click(self, y: int) -> None:
        index = self._index_at(y)
        if index >= 0:
            self._session.select(index)
            self._on_open()

    def hover(self, y: int) -> None:
        index = self._index_at(y) if y >= 0 else -1
        if index != self.hovered:
            self.hovered = index
            self.render()

    def scroll(self, delta: int) -> None:
        if self._content_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(-delta, "units")

    def _content_height(self) -> int:
        return S["results_pad_top"] + ROW_HEIGHT * len(self._rows)

    def scroll_to_selected(self) -> None:
        c, index = self.canvas, self._session.selected
        if index < 0 or c.winfo_height() <= 1:
            return
        top, height, total = self._rows[index].top, c.winfo_height(), self._content_height()
        view_top = c.canvasy(0)
        if top < view_top:
            c.yview_moveto(top / total)
        elif top + ROW_HEIGHT > view_top + height:
            c.yview_moveto((top + ROW_HEIGHT - height) / total)

    # ---------- drawing ----------

    def _width(self) -> int:
        width = self.canvas.winfo_width()
        return width if width > 1 else S["search_window"][0]

    def render(self) -> None:
        c, session = self.canvas, self._session
        c.delete("all")
        self._shown, self._placeholder = {}, []
        matches = session.result.matches if session.result else ()
        top = S["results_pad_top"]
        self._rows = [ResultRow(m, self._color_of(m.path), top + i * ROW_HEIGHT) for i, m in enumerate(matches)]
        placeholder = session.placeholder
        if placeholder:
            self._rows = []
            self._draw_placeholder(*placeholder)
        for index, row in enumerate(self._rows):
            self._draw_row(index, row)
        c.configure(scrollregion=(0, 0, self._width(), max(self._content_height(), c.winfo_height())))

    def _draw_placeholder(self, head: str, text: str) -> None:
        c, width = self.canvas, self._width()
        height = max(self.canvas.winfo_height(), 200)
        lines = [("⌕", "empty_glyph"), (head, "empty_head"), (text, "empty_sub")] if head else [(text, "empty_sub")]
        line_height = theme.font("empty_sub").metrics("linespace") + S["empty_gap"]
        y = height / 2 - line_height * (len(lines) - 1) / 2
        for text_, role in lines:
            c.create_text(width / 2, y, text=text_, font=theme.font(role), fill=theme.TYPE[role].color,
                          width=width - 2 * S["empty_pad"][0], justify=tk.CENTER)
            self._placeholder.append(text_)
            y += theme.font(role).metrics("linespace") + S["empty_gap"]

    def _draw_row(self, index: int, row: ResultRow) -> None:
        c, width = self.canvas, self._width()
        fill = C["accent_soft"] if index == self._session.selected else C["row_hover"] if index == self.hovered else C["bg"]
        c.create_rectangle(0, row.top, width, row.top + ROW_HEIGHT, fill=fill, outline="", tags=("row",))
        middle = row.top + ROW_HEIGHT / 2
        where_left = self._draw_where(row, width - S["row_side"], middle, width * S["where_share"])
        self._draw_line(row, S["row_side"], where_left - S["where_gap"], middle)

    def _draw_where(self, row: ResultRow, right: float, middle: float, budget: float) -> float:
        """File name, folder and line number ending at `right`; returns where they start."""
        c = self.canvas
        name_font, dim_font = theme.font("file_name"), theme.font("file_folder")
        folder, _, name = row.path.rpartition("/")
        number = str(row.line)
        number_width = dim_font.measure(number)
        name = elide(name, name_font, int(budget - number_width - S["line_number_gap"]))
        room = budget - name_font.measure(name) - number_width - S["line_number_gap"] - S["suffix_gap"]
        folder = elide_middle(folder, dim_font, int(room)) if folder and room >= dim_font.measure("x…x") else ""
        c.create_text(right, middle, anchor=tk.E, text=number, font=dim_font, fill=C["dim"], tags=("row",))
        right -= number_width + S["line_number_gap"]
        if folder:
            c.create_text(right, middle, anchor=tk.E, text=folder, font=dim_font, fill=C["dim"], tags=("row",))
            right -= dim_font.measure(folder) + S["suffix_gap"]
        c.create_text(right, middle, anchor=tk.E, text=name, font=name_font, fill=row.color, tags=("row",))
        return right - name_font.measure(name)

    def _draw_line(self, row: ResultRow, x: float, right: float, middle: float) -> None:
        """The line left to right; the piece that does not fit ends in "…" and nothing follows it."""
        c, font = self.canvas, theme.font("body")
        ink = C["dim"] if self._session.searching else C["ink"]
        height = font.metrics("linespace")
        shown = ""
        for text, hit in line_pieces(row.match):
            fits = x + font.measure(text) <= right
            text = text if fits else elide(text, font, int(right - x))
            width = font.measure(text)
            if hit:
                c.create_rectangle(x, middle - height / 2, x + width, middle + height / 2, fill=C["hit"], outline="",
                                   tags=("row", "hit"))
            c.create_text(x, middle, anchor=tk.W, text=text, font=font, fill=C["dim"] if text == "…" else ink,
                          tags=("row",))
            shown += text
            x += width
            if not fits:
                break
        self._shown[row.top] = shown


class SearchDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, session: SearchSession, *, repo: str, color_of: Callable[[str], str],
                 on_close: Callable[[], None]):
        super().__init__(master, bg=C["bg"])
        self._session, self._on_close = session, on_close
        self._loading = True    # filling the fields from the session does not send a query back
        self.title(f"Szukaj w plikach — {repo}")
        self.transient(master.winfo_toplevel())
        self.minsize(480, 260)
        self._build(repo, color_of)
        self._load(session.query)
        self._bind_keys()
        session.subscribe(self.render)
        self._loading = False
        self._place_over(master.winfo_toplevel())
        self.after_idle(self._grab)
        session.start()
        self.render()

    # ---------- layout ----------

    def _build(self, repo: str, color_of: Callable[[str], str]) -> None:
        px, py = S["search_bar_pad"]
        bar = tk.Frame(self, bg=C["panel"], padx=px, pady=py)
        bar.pack(fill=tk.X)
        self._build_phrase(bar, repo)
        self._build_mask(bar)
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(fill=tk.X)
        self._build_status()
        tk.Frame(self, height=S["line"], bg=C["line"]).pack(side=tk.BOTTOM, fill=tk.X)
        self.banner = tk.Frame(self, bg=C["conf_soft"])
        tk.Frame(self.banner, width=S["banner_edge"], bg=C["conf"]).pack(side=tk.LEFT, fill=tk.Y)
        texts = tk.Frame(self.banner, bg=C["conf_soft"])
        texts.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(9, 10), pady=8)
        theme.label(texts, "banner_title", "⚠ Wyszukiwanie nie powiodło się", bg=C["conf_soft"], anchor=tk.W).pack(fill=tk.X)
        self.banner_body = theme.label(texts, "banner_body", bg=C["conf_soft"], anchor=tk.W, justify=tk.LEFT,
                                       wraplength=S["search_window"][0] - 60)
        self.banner_body.pack(fill=tk.X, pady=(4, 0))
        self.results = ResultList(self, self._session, color_of, on_open=self.press_return)
        self.results.pack(fill=tk.BOTH, expand=True)

    def _build_phrase(self, bar: tk.Frame, repo: str) -> None:
        """Two frames make the border: grey 1 pt at rest, accent 2 pt while the field has the focus."""
        self._ring = tk.Frame(bar, bg=C["panel"], padx=1, pady=1)
        self._ring.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._field = tk.Frame(self._ring, bg=C["bg"], highlightthickness=1, highlightbackground=C["control_border"])
        self._field.pack(fill=tk.X)
        fx, fy = S["search_field_pad"]
        glass = theme.label(self._field, "placeholder", "⌕", bg=C["bg"])
        glass.configure(fg=C["dim"])
        glass.pack(side=tk.LEFT, padx=(fx, 4))
        self.phrase = tk.StringVar(self)
        self.phrase_entry = tk.Entry(self._field, textvariable=self.phrase, bd=0, highlightthickness=0, bg=C["bg"],
                                     fg=C["ink"], insertbackground=C["ink"], font=theme.font("body"))
        self.phrase_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=fy)
        self._phrase_hint = _hint_over(self.phrase_entry, self.phrase, f"Szukaj w {repo}")
        self.word_toggle = Toggle(self._field, "W", lambda on: self._push(), role="toggle_mono", parent_bg=C["bg"])
        self.word_toggle.pack(side=tk.RIGHT, padx=(2, 4))
        self.case_toggle = Toggle(self._field, "Aa", lambda on: self._push(), parent_bg=C["bg"])
        self.case_toggle.pack(side=tk.RIGHT, padx=2)
        Tooltip(self.case_toggle, lambda: "Wielkość liter (⌥⌘C)")
        Tooltip(self.word_toggle, lambda: "Całe słowo (⌥⌘W)")
        self.phrase_entry.bind("<FocusIn>", lambda e: self._focus_ring(True), add="+")
        self.phrase_entry.bind("<FocusOut>", lambda e: self._focus_ring(False), add="+")

    def _build_mask(self, bar: tk.Frame) -> None:
        box = tk.Frame(bar, bg=C["panel"])
        box.pack(side=tk.LEFT, padx=(S["search_gap"], 0))
        theme.label(box, "dialog_note", "Pliki", bg=C["panel"]).pack(side=tk.LEFT, padx=(0, S["mask_label_gap"]))
        frame = tk.Frame(box, bg=C["bg"], highlightthickness=1, highlightbackground=C["control_border"],
                         width=S["mask_width"])
        frame.pack(side=tk.LEFT)
        self.mask = tk.StringVar(self)
        self.mask_entry = tk.Entry(frame, textvariable=self.mask, bd=0, highlightthickness=0, bg=C["bg"], fg=C["ink"],
                                   insertbackground=C["ink"], font=theme.font("body"), width=14)
        self.mask_entry.pack(padx=6, pady=2)
        self._mask_hint = _hint_over(self.mask_entry, self.mask, "wszystkie")

    def _build_status(self) -> None:
        px, py = S["statusbar_pad"]
        bar = tk.Frame(self, bg=C["chrome"], padx=px, pady=py)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status = theme.label(bar, "statusbar", bg=C["chrome"], anchor=tk.W)
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        keys = tk.Frame(bar, bg=C["chrome"])
        keys.pack(side=tk.RIGHT)
        for index, (glyphs, label) in enumerate(KEYS):
            for position, glyph in enumerate(glyphs):
                gap = S["statusbar_gap"] if index and not position else 0
                kbd(keys, glyph, C["chrome"]).pack(side=tk.LEFT, padx=(gap, 2 if position < len(glyphs) - 1 else 0))
            theme.label(keys, "statusbar", label, bg=C["chrome"]).pack(side=tk.LEFT)

    def _focus_ring(self, focused: bool) -> None:
        self._ring.configure(bg=C["accent"] if focused else C["panel"])
        self._field.configure(highlightbackground=C["accent"] if focused else C["control_border"])

    def _place_over(self, parent: tk.Misc) -> None:
        width, height = S["search_window"]
        self.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - width) // 2)
        self.geometry(f"{width}x{height}+{x}+{parent.winfo_rooty() + 30}")

    def _grab(self) -> None:
        try:
            self.grab_set()
            self.phrase_entry.focus_set()
        except tk.TclError:  # not viewable yet (e.g. while the main window is hidden)
            pass

    # ---------- events ----------

    def _bind_keys(self) -> None:
        for entry in (self.phrase_entry, self.mask_entry):
            entry.bind("<Up>", lambda e: self.press_up())
            entry.bind("<Down>", lambda e: self.press_down())
            entry.bind("<Return>", lambda e: self.press_return())
            entry.bind(SHORTCUT_CASE, lambda e: self.toggle_case())
            entry.bind(SHORTCUT_WORD, lambda e: self.toggle_word())
        self.bind("<Escape>", lambda e: self.press_escape())
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.double_shift = DoubleShift(self.double_shift_pressed)
        self.bind("<KeyPress>", lambda e: self.double_shift.press(e.keysym), add="+")
        self.bind("<KeyRelease>", lambda e: self.double_shift.release(e.keysym), add="+")
        self.bind("<ButtonPress>", lambda e: self.double_shift.other(), add="+")
        for var in (self.phrase, self.mask):
            var.trace_add("write", lambda *_: self._push())

    def _load(self, query: SearchQuery) -> None:
        self.phrase.set(query.text)
        self.mask.set(query.mask)
        self.case_toggle.set(query.case_sensitive)
        self.word_toggle.set(query.whole_word)
        self.phrase_entry.select_range(0, tk.END)

    def _push(self) -> None:
        if not self._loading:
            self._session.set_query(SearchQuery(self.phrase.get(), self.case_toggle.on, self.word_toggle.on,
                                                self.mask.get()))

    def toggle_case(self) -> str:
        self.case_toggle.click()
        return "break"   # nothing is typed into the field

    def toggle_word(self) -> str:
        self.word_toggle.click()
        return "break"

    def press_up(self) -> str:
        self._session.move(-1)
        return "break"

    def press_down(self) -> str:
        self._session.move(+1)
        return "break"

    def press_return(self) -> str:
        if self._session.open():
            self._finish()
        return "break"

    def press_escape(self) -> None:
        self.close()

    def double_shift_pressed(self) -> None:
        self.phrase_entry.focus_set()
        self.phrase_entry.select_range(0, tk.END)
        self.phrase_entry.icursor(tk.END)

    def close(self) -> None:
        self._session.close()
        self._finish()

    def _finish(self) -> None:
        self._session.unsubscribe(self.render)
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        self._on_close()

    # ---------- drawing the session ----------

    def render(self) -> None:
        text, warn = self._session.status
        self.status.configure(text=text, fg=C["mod"] if warn else C["dim"])
        if self._session.error:
            self.banner_body.configure(text=self._session.error)
            if not self.banner.winfo_manager():
                self.banner.pack(fill=tk.X, padx=12, pady=(8, 4), before=self.results)
        elif self.banner.winfo_manager():
            self.banner.pack_forget()
        self.results.render()
        self.results.scroll_to_selected()

    def status_text(self) -> tuple[str, str]:
        return self.status.cget("text"), str(self.status.cget("fg"))

    def placeholder_texts(self) -> list[str]:
        return self.results.placeholder_texts()

    def error_text(self) -> str:
        return self.banner_body.cget("text") if self.banner.winfo_manager() else ""


def _hint_over(entry: tk.Entry, var: tk.StringVar, text: str) -> tk.Label:
    """Grey text over an empty field, also while it has the focus (Tk entries have no placeholder)."""
    hint = theme.label(entry.master, "placeholder", text, bg=str(entry.cget("bg")))
    hint.bind("<Button-1>", lambda e: entry.focus_set())

    def update(*_args) -> None:
        if var.get():
            hint.place_forget()
        else:
            hint.place(in_=entry, x=1, rely=0.5, anchor=tk.W)
    var.trace_add("write", update)
    update()
    return hint
