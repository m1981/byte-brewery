"""State and rules of the main window, without Tk: repository list, files, drafts, buttons, operations.

Trace: DES-VCS-016, DES-VCS-018, DES-VCS-021, DES-VCS-026, DES-VCS-036, DES-VCS-038, REQ-VCS-002, REQ-VCS-009, REQ-VCS-010, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-015, REQ-VCS-016, REQ-VCS-018, REQ-VCS-019, REQ-VCS-020, REQ-VCS-021, REQ-VCS-022, REQ-VCS-023, REQ-VCS-024, S-VCS-01
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from vcs_lite.app.worker import Executor, Outcome
from vcs_lite.core.difftool import CommandTemplateDiffTool, ExternalDiffTool, compare
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.repo import GitError, GitRepo
from vcs_lite.core.settings import Settings
from vcs_lite.core.status import FileChange, Group, RepoStatus, Side

SIDE_LABELS = {Side.HEAD: "HEAD", Side.INDEX: "indeks", Side.WORKTREE: "kopia robocza", Side.EMPTY: "pusty"}


class RepoState(Enum):
    """S-VCS-01."""

    UNAVAILABLE = "niedostępne"
    CLEAN = "czyste"
    CHANGES = "zmiany"
    CONFLICT = "konflikt"
    BUSY = "w toku"


@dataclass
class RepoView:
    name: str
    path: Path
    status: RepoStatus | None = None
    available: bool = True
    error: str | None = None
    draft: str = ""  # DES-VCS-021: kept in memory only

    @property
    def branch_label(self) -> str:
        if self.status is None:
            return ""
        return self.status.branch or (self.status.oid or "")[:7]

    @property
    def change_count(self) -> int:
        return len({c.path for c in self.status.changes}) if self.status else 0


class AppModel:
    def __init__(self, settings: Settings, *, git: GitCli, diff_tool: ExternalDiffTool, worker: Executor,
                 confirm: Callable[[str], bool]):
        self._git = git
        self._diff_tool = diff_tool
        self._worker = worker
        self._confirm = confirm
        self._repos = {name: RepoView(name, settings.repo_path(name)) for name in settings.repos}
        self._listeners: list[Callable[[], None]] = []
        self.selected: str | None = None

    @classmethod
    def from_settings(cls, settings: Settings, *, git: GitCli, worker: Executor,
                      confirm: Callable[[str], bool]) -> AppModel:
        return cls(settings, git=git, diff_tool=CommandTemplateDiffTool(settings.diff_tool), worker=worker,
                   confirm=confirm)

    # ---------- observing ----------

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def _changed(self) -> None:
        for listener in self._listeners:
            listener()

    # ---------- reading state ----------

    @property
    def repo_names(self) -> list[str]:
        return list(self._repos)

    def view(self, name: str) -> RepoView:
        return self._repos[name]

    def state(self, name: str) -> RepoState:
        view = self._repos[name]
        if self._worker.busy(name):
            return RepoState.BUSY
        if not view.available:
            return RepoState.UNAVAILABLE
        if view.status is None or not view.status.changes:
            return RepoState.CLEAN
        return RepoState.CONFLICT if view.status.has_conflicts else RepoState.CHANGES

    def files(self, group: Group) -> list[FileChange]:
        view = self._current()
        return view.status.group(group) if view and view.status else []

    @property
    def error(self) -> str | None:
        view = self._current()
        return view.error if view else None

    @property
    def message(self) -> str:
        view = self._current()
        return view.draft if view else ""

    @message.setter
    def message(self, text: str) -> None:
        view = self._current()
        if view:
            view.draft = text
            self._changed()

    @property
    def commit_label(self) -> str:
        return f"Commit do {self.selected}" if self.selected else "Commit"

    @property
    def commit_disabled_reason(self) -> str | None:
        view = self._current()
        if view is None:
            return "Wybierz repozytorium."
        state = self.state(view.name)
        if state is RepoState.BUSY:
            return "Trwa operacja na tym repozytorium."
        if state is RepoState.UNAVAILABLE:
            return "Repozytorium jest niedostępne."
        if state is RepoState.CONFLICT:
            return "Rozwiąż konflikty przed commitem."
        if not self.files(Group.STAGED):
            return "Brak plików w Staged."
        if not view.draft.strip():
            return "Wpisz wiadomość commita."
        return None

    @property
    def can_commit(self) -> bool:
        return self.commit_disabled_reason is None

    @property
    def can_commit_and_push(self) -> bool:
        view = self._current()
        return self.can_commit and bool(view and view.status and not view.status.detached)

    @property
    def can_pull(self) -> bool:
        view = self._current()
        return bool(view and view.status and not view.status.detached and view.status.upstream
                    and not self._worker.busy(view.name))

    # ---------- selecting and refreshing ----------

    def select(self, name: str) -> None:
        self.selected = name
        self._changed()
        self.refresh(name)

    def refresh_all(self) -> None:
        for name in self._repos:
            self.refresh(name)

    def refresh(self, name: str) -> None:
        view = self._repos[name]
        self._worker.submit(name, lambda: self._read_status(view), lambda outcome: self._status_read(view, outcome))

    def _read_status(self, view: RepoView) -> RepoStatus | None:
        if not (view.path / ".git").exists():
            return None
        return self._repo(view).status()

    def _status_read(self, view: RepoView, outcome: Outcome) -> None:
        if isinstance(outcome.error, GitError):
            view.error = str(outcome.error)  # keep the previous list, UC-VCS-02 2d
        elif outcome.error is not None:
            raise outcome.error
        else:
            view.available = outcome.value is not None
            view.status = outcome.value
        self._changed()

    # ---------- files ----------

    def toggle(self, change: FileChange) -> None:
        """Space: stage from Changes or Unversioned, unstage from Staged (DEC-VCS-040),
        mark as resolved from Conflicts (REQ-VCS-024)."""
        view = self._current()
        repo = self._repo(view)
        operation = {Group.STAGED: repo.unstage, Group.CONFLICTS: repo.mark_resolved}.get(change.group, repo.stage)
        self._run(view, lambda: operation(change))

    def activate(self, change: FileChange) -> None:
        """Double click or Enter: compare the file in the external tool (DEC-VCS-040)."""
        view = self._current()
        if change.left is None or change.right is None:
            return
        # Its own key, so the repository stays usable while the diff window is open.
        self._worker.submit(f"{view.name}:diff:{change.group.value}:{change.path}",
                            lambda: self._compare(view, change),
                            lambda outcome: self._compared(view, outcome))

    def _compare(self, view: RepoView, change: FileChange):
        left, right = self._repo(view).sides(change)
        return compare(self._diff_tool, left, right, name=Path(change.path).name,
                       left_title=f"{change.path} ({SIDE_LABELS[change.left]})",
                       right_title=f"{change.path} ({SIDE_LABELS[change.right]})")

    def _compared(self, view: RepoView, outcome: Outcome) -> None:
        if outcome.error is not None:
            view.error = str(outcome.error)
        elif outcome.value.failed:
            view.error = outcome.value.stderr.strip()
        self.refresh(view.name)

    # ---------- commit, push, pull ----------
    # Each operation captures the repository selected at click time (REQ-VCS-021).

    def commit(self) -> None:
        if not self.can_commit:
            return
        view, message = self._current(), self._current().draft
        self._run(view, lambda: self._repo(view).commit(message), on_success=lambda: self._clear_draft(view))

    def commit_and_push(self) -> None:
        if not self.can_commit_and_push:
            return
        view, message = self._current(), self._current().draft
        self._run(view, lambda: self._repo(view).commit(message), on_success=lambda: self._pushed_after_commit(view))

    def _pushed_after_commit(self, view: RepoView) -> None:
        self._clear_draft(view)
        if view.status.upstream is not None:
            self._run(view, lambda: self._repo(view).push())
        elif self._confirm(f"Gałąź {view.status.branch} nie ma upstreamu. Wypchnąć ją do origin i ustawić upstream?"):
            self._run(view, lambda: self._repo(view).push(set_upstream=True))

    def pull(self) -> None:
        if self.can_pull:
            view = self._current()
            self._run(view, lambda: self._repo(view).pull())

    # ---------- plumbing ----------

    def _current(self) -> RepoView | None:
        return self._repos.get(self.selected) if self.selected else None

    def _repo(self, view: RepoView) -> GitRepo:
        return GitRepo(view.path, self._git)

    @staticmethod
    def _clear_draft(view: RepoView) -> None:
        view.draft = ""

    def _run(self, view: RepoView, operation: Callable[[], GitResult], *,
             on_success: Callable[[], None] | None = None) -> None:
        """Run a repository operation; report git's message on failure, then refresh (DES-VCS-016)."""

        def done(outcome: Outcome) -> None:
            result = outcome.value
            if outcome.error is not None:
                view.error = str(outcome.error)
            elif not result.ok:
                view.error = result.message
            else:
                view.error = None
                if on_success:
                    on_success()  # may chain the next operation (push after commit), which refreshes itself
            self.refresh(view.name)  # rejected while a chained operation holds the repository
            self._changed()

        self._worker.submit(view.name, operation, done)
