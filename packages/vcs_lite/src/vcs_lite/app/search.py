"""State of the search window without Tk: the query, the delay while typing, stale results, opening a match.

The session knows only the TextSearcher port, an executor, a timer and two callbacks, so the engine, the
worker and the window can each be replaced without touching it (DES-VCS-055). It lives as long as the app,
so the window finds its last query when it opens again (DEC-VCS-097).

Trace: DES-VCS-055, REQ-VCS-033, REQ-VCS-101, DEC-VCS-094, DEC-VCS-095, DEC-VCS-097
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from vcs_lite.app.worker import Executor, Outcome
from vcs_lite.core.repo import GitError
from vcs_lite.core.search import Match, SearchQuery, SearchResult, TextSearcher

DEBOUNCE_MS = 250   # searching starts after a pause this long in typing
LIMIT = 500         # matches shown; more give a warning

Later = Callable[[int, Callable[[], None]], Callable[[], None]]   # schedule a callback, get its cancel
HINT = "Wpisz frazę. Szukam w plikach śledzonych przez git, w ich obecnej postaci na dysku."
TRUNCATED = f"Pokazano pierwsze {LIMIT} trafień · zawęź frazę albo maskę plików"


def matches_label(n: int) -> str:
    """Polish plural: 1 trafienie, 2–4 trafienia (but 12–14 trafień), otherwise trafień."""
    if n == 1:
        return "1 trafienie"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} trafienia"
    return f"{n} trafień"


def in_files_label(n: int) -> str:
    return "w 1 pliku" if n == 1 else f"w {n} plikach"


class SearchSession:
    def __init__(self, searcher: TextSearcher, executor: Executor, *, later: Later,
                 repo: Callable[[], Path | None], open_match: Callable[[str, int], None]):
        self._searcher, self._executor, self._later = searcher, executor, later
        self._repo, self._open_match = repo, open_match
        self.query = SearchQuery("")
        self.result: SearchResult | None = None
        self.searching = False
        self.error: str | None = None
        self.selected = -1
        self._generation = 0                          # results of older numbers are dropped
        self._cancel_timer: Callable[[], None] | None = None
        self._running: threading.Event | None = None  # set to stop the search in progress
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[], None]) -> None:
        """A closed window stops listening; the session outlives it."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _changed(self) -> None:
        for listener in self._listeners:
            listener()

    # ---------- what the window asks for ----------

    def start(self) -> None:
        """The window opened: search the remembered query at once, in the repository selected now."""
        if self.query.active:
            self._search()

    def set_query(self, query: SearchQuery) -> None:
        """A new phrase or option: search once typing pauses; a blank phrase only clears the list."""
        if query == self.query and (self.searching or self.result is not None):
            return
        self.query = query
        self._stop()
        if query.active and self._repo() is not None:
            self.searching = True
            self._cancel_timer = self._later(DEBOUNCE_MS, self._search)
        else:
            self.result, self.error, self.selected = None, None, -1
        self._changed()

    def close(self) -> None:
        """The window closed: nothing keeps searching in the background (REQ-VCS-101)."""
        self._stop()
        self._changed()

    @property
    def status(self) -> tuple[str, bool]:
        """The status line and whether it is a warning (E-04)."""
        if self.searching:
            return "Szukam…", False
        if self.result is None:
            return "", False
        if self.result.truncated:
            return TRUNCATED, True
        count = len(self.result.matches)
        return (f"{matches_label(count)} {in_files_label(self.result.file_count)}" if count else matches_label(0)), False

    @property
    def placeholder(self) -> tuple[str, str] | None:
        """(head, text) shown instead of the list: the hint for a blank phrase, or why nothing matched."""
        if not self.query.active:
            return "", HINT
        if self.searching or self.result is None or self.result.matches:
            return None
        q = self.query
        where = f"w plikach {', '.join('*.' + ext for ext in q.extensions)}" if q.extensions else "we wszystkich plikach"
        options = ""
        if q.case_sensitive:
            options += ", z rozróżnianiem wielkości liter"
        if q.whole_word:
            options += ", całe słowo"
        return "Brak trafień", f"„{q.text}” {where}{options}."

    @property
    def selected_match(self) -> Match | None:
        matches = self.result.matches if self.result else ()
        return matches[self.selected] if 0 <= self.selected < len(matches) else None

    def select(self, index: int) -> None:
        if self.result and 0 <= index < len(self.result.matches):
            self.selected = index
            self._changed()

    def move(self, step: int) -> None:
        if self.result and self.result.matches:
            self.select(max(0, min(self.selected + step, len(self.result.matches) - 1)))

    def open(self) -> bool:
        """Enter or a double click: open the selected match and finish; False when there is none."""
        match = self.selected_match
        if match is None:
            return False
        self.close()
        self._open_match(match.path, match.line)
        return True

    # ---------- searching ----------

    def _stop(self) -> None:
        """Cancel the planned search and stop the running one; whatever it still returns is dropped."""
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None
        if self._running:
            self._running.set()
            self._running = None
        self._generation += 1
        self.searching = False

    def _search(self) -> None:
        self._stop()
        repo, query = self._repo(), self.query
        if repo is None:
            self._changed()
            return
        generation, stop = self._generation, threading.Event()
        self._running, self.searching = stop, True
        self._executor.submit(f"search:{generation}",   # its own key: the repository stays usable
                              lambda: self._searcher.search(repo, query, limit=LIMIT, cancelled=stop.is_set),
                              lambda outcome: self._found(generation, outcome))
        self._changed()

    def _found(self, generation: int, outcome: Outcome) -> None:
        if generation != self._generation:
            return  # a newer query or a closed window
        self._running, self.searching = None, False
        if isinstance(outcome.error, GitError):
            self.error = str(outcome.error)
        elif outcome.error is not None:
            raise outcome.error
        else:
            self.result, self.error = outcome.value, None
            self.selected = 0 if self.result.matches else -1
        self._changed()
