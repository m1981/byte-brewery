"""State of the history panel without Tk: what is read, from which repository, and what is selected.

Shaped like SearchSession (DES-VCS-055): it knows the HistoryReader port, an executor, a timer and the
model. It watches the model and reads the history again when the selected repository changes or one of
its refreshes finishes (H-41), so it reads exactly when the status is read and never on its own. Every
read carries a number; a result with an older number is dropped (H-43). Jobs run under their own keys, so
the repository stays free for commit, pull and stage.

Trace: DES-VCS-067, DEC-VCS-123, REQ-VCS-037, REQ-VCS-039, REQ-VCS-101, DEC-VCS-116, DEC-VCS-120
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from vcs_lite.app.worker import Executor, Outcome
from vcs_lite.core.graph import Edge, GraphLayout, GraphRow
from vcs_lite.core.log import Commit, CommitDetails, HistoryReader, LogQuery, Scope
from vcs_lite.core.repo import GitError

DEBOUNCE_MS = 250   # the filter reads after a pause this long in typing (H-44)

Later = Callable[[int, Callable[[], None]], Callable[[], None]]


class Watched(Protocol):
    """What the session needs of AppModel."""

    selected: str | None

    @property
    def selected_path(self) -> Path | None: ...

    def view(self, name: str): ...

    def subscribe(self, listener: Callable[[], None]) -> None: ...


def commits_label(n: int) -> str:
    """Polish plural with a space between thousands: 1 commit, 2–4 commity (but 12–14 commitów), commitów."""
    number = f"{n:,}".replace(",", " ")
    if n == 1:
        return "1 commit"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{number} commity"
    return f"{number} commitów"


def commit_web_url(remote: str | None, commit_hash: str) -> str | None:
    """The commit's page on GitHub, GitLab or Bitbucket (also self-hosted with that name), from the remote
    address as https (REQ-VCS-035); None for other hosts and for paths on disk (H-47)."""
    parts = urlsplit(remote or "")
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("https", "http") or not any(name in host for name in ("github", "gitlab", "bitbucket")):
        return None
    path = parts.path.rstrip("/").removesuffix(".git")
    port = f":{parts.port}" if parts.port else ""
    return f"{parts.scheme}://{host}{port}{path}/{'commits' if 'bitbucket' in host else 'commit'}/{commit_hash}"


def date_label(timestamp: float, now: datetime) -> str:
    """dziś 14:05, wczoraj 18:22, otherwise 24.10.2026, in local time (H-48)."""
    when = datetime.fromtimestamp(timestamp)
    if when.date() == now.date():
        return f"dziś {when:%H:%M}"
    if when.date() == (now - timedelta(days=1)).date():
        return f"wczoraj {when:%H:%M}"
    return f"{when:%d.%m.%Y}"


class HistorySession:
    def __init__(self, reader: HistoryReader, executor: Executor, *, later: Later, model: Watched):
        self._reader, self._executor, self._later, self._model = reader, executor, later, model
        self.query = LogQuery()
        self.commits: list[Commit] = []
        self.rows: list[GraphRow] = []          # empty while filtering: no lines then (H-34)
        self.more = False
        self.count = 0
        self.unpushed: set[str] = set()
        self.selected = -1
        self.details: CommitDetails | None = None
        self.loading = False
        self.error: str | None = None
        self._remote: str | None = None
        self._layout = GraphLayout()
        self._repo: Path | None = None
        self._seen: tuple[str | None, int] | None = None
        self._generation = 0
        self._loading_more = False
        self._cancel_timer: Callable[[], None] | None = None
        self._listeners: list[Callable[[], None]] = []
        model.subscribe(self._model_changed)
        self._model_changed()

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def _changed(self) -> None:
        for listener in self._listeners:
            listener()

    # ---------- what the panel shows ----------

    @property
    def selected_commit(self) -> Commit | None:
        return self.commits[self.selected] if 0 <= self.selected < len(self.commits) else None

    @property
    def edges(self) -> list[Edge]:
        """The graph's lines: finished ones and those still waiting for a parent below (DEC-VCS-123)."""
        return [*self._layout.edges, *self._layout.open_edges()] if self.rows else []

    def commit_url(self, commit: Commit) -> str | None:
        return commit_web_url(self._remote, commit.hash)

    @property
    def placeholder(self) -> str | None:
        """The text instead of the list, or None when there is a list or it is still being read."""
        if self.error:
            return f"Nie udało się wczytać historii: {self.error}"
        if self._model.selected is None:
            return ""
        if self._repo is None:
            return "Repo niedostępne."
        if self.loading or self.commits:
            return None
        if self.query.filtered:
            return f"Brak commitów pasujących do „{self.query.phrase}”."
        return "Repo nie ma jeszcze commitów."

    # ---------- what the panel asks for ----------

    def set_text(self, text: str) -> None:
        """The filter: read once typing pauses (H-44)."""
        if self._cancel_timer:
            self._cancel_timer()
        self._cancel_timer = self._later(DEBOUNCE_MS, lambda: self._set_query(LogQuery(self.query.scope, text)))

    def set_scope(self, scope: Scope) -> None:
        self._set_query(LogQuery(scope, self.query.text))

    def select(self, index: int) -> None:
        if not 0 <= index < len(self.commits) or index == self.selected and self.details:
            return
        self.selected, self.details = index, None
        commit, repo, generation = self.commits[index], self._repo, self._generation
        self._executor.submit(f"history:{generation}:details:{commit.hash}",
                              lambda: self._reader.details(repo, commit),
                              lambda outcome: self._details_read(generation, commit, outcome))
        self._changed()

    def move(self, step: int) -> None:
        if self.commits:
            self.select(max(0, min(self.selected + step, len(self.commits) - 1)))

    def load_more(self) -> None:
        """The next page, when the list is scrolled near its end (H-06, H-32)."""
        if not self.more or self._loading_more or self._repo is None:
            return
        self._loading_more = True
        repo, query, generation, skip = self._repo, self.query, self._generation, len(self.commits)
        self._executor.submit(f"history:{generation}:more:{skip}", lambda: self._reader.page(repo, query, skip),
                              lambda outcome: self._more_read(generation, outcome))

    # ---------- reading ----------

    def _model_changed(self) -> None:
        name = self._model.selected
        seen = (name, self._model.view(name).refreshes if name else 0)
        if seen != self._seen:
            self._seen = seen
            self._read()

    def _set_query(self, query: LogQuery) -> None:
        self._cancel_timer = None
        if query != self.query:
            self.query = query
            self._read()

    def _read(self) -> None:
        self._generation += 1
        self._repo, self.error, self._loading_more = self._model.selected_path, None, False
        if self._repo is None:
            self.commits, self.rows, self.more, self.count, self.selected, self.details = [], [], False, 0, -1, None
            self.loading = False
            self._changed()
            return
        repo, query, generation = self._repo, self.query, self._generation
        self.loading = True
        self._executor.submit(f"history:{generation}", lambda: self._read_all(repo, query),
                              lambda outcome: self._read_done(generation, outcome))
        self._changed()

    def _read_all(self, repo: Path, query: LogQuery):
        page = self._reader.page(repo, query, 0)
        count = len(page.commits) if query.filtered else self._reader.count(repo, query)
        return page, count, self._reader.unpushed(repo), self._reader.remote_url(repo)

    def _read_done(self, generation: int, outcome: Outcome) -> None:
        if generation != self._generation:
            return
        self.loading = False
        keep = self.selected_commit.hash if self.selected_commit else None
        if isinstance(outcome.error, GitError):
            self.error = str(outcome.error)
            self.commits, self.rows, self.more, self.count, self.selected, self.details = [], [], False, 0, -1, None
        elif outcome.error is not None:
            raise outcome.error
        else:
            page, self.count, self.unpushed, self._remote = outcome.value
            self.commits, self.more = list(page.commits), page.more
            self._layout = GraphLayout()
            self.rows = [] if self.query.filtered else self._layout.extend(self.commits)
            index = next((i for i, c in enumerate(self.commits) if c.hash == keep), 0 if self.commits else -1)
            self.selected, self.details = -1, None
            if index >= 0:
                self.select(index)
        self._changed()

    def _more_read(self, generation: int, outcome: Outcome) -> None:
        if generation != self._generation:
            return
        self._loading_more = False
        if isinstance(outcome.error, GitError):
            self.error = str(outcome.error)
        elif outcome.error is not None:
            raise outcome.error
        else:
            page = outcome.value
            self.commits.extend(page.commits)
            self.more = page.more
            if not self.query.filtered:
                self.rows.extend(self._layout.extend(page.commits))
        self._changed()

    def _details_read(self, generation: int, commit: Commit, outcome: Outcome) -> None:
        if generation != self._generation or self.selected_commit != commit:
            return
        if isinstance(outcome.error, GitError):
            self.error = str(outcome.error)
        elif outcome.error is not None:
            raise outcome.error
        else:
            self.details = outcome.value
        self._changed()
