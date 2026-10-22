"""State and rules of the main window, without Tk: repository list, files, drafts, buttons, operations.

Trace: DES-VCS-016, DES-VCS-018, DES-VCS-021, DES-VCS-043, DES-VCS-045, DES-VCS-026, DES-VCS-036, DES-VCS-038, REQ-VCS-002, REQ-VCS-009, REQ-VCS-010, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-015, REQ-VCS-016, REQ-VCS-018, REQ-VCS-019, REQ-VCS-020, REQ-VCS-021, REQ-VCS-022, REQ-VCS-023, REQ-VCS-024, REQ-VCS-025, REQ-VCS-026, REQ-VCS-001, S-VCS-01, E-02
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path

from vcs_lite.app.worker import Executor, Outcome
from vcs_lite.core.difftool import CommandTemplateDiffTool, ExternalDiffTool, compare
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.repo import GitError, GitRepo
from vcs_lite.core.settings import Settings, SettingsError, scan_rootdir
from vcs_lite.core.status import FileChange, Group, RepoStatus, Side

SIDE_LABELS = {Side.HEAD: "HEAD", Side.INDEX: "indeks", Side.WORKTREE: "kopia robocza", Side.EMPTY: "pusty"}


def files_label(n: int) -> str:
    """Polish plural: 1 plik, 2–4 pliki (but 12–14 plików), otherwise plików."""
    if n == 1:
        return "1 plik"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} pliki"
    return f"{n} plików"


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
    error_title: str | None = None   # P3: "<operation> nie powiódł się"
    busy_label: str | None = None    # P4: the operation running now
    draft: str = ""  # DES-VCS-021: kept in memory only
    refreshed_at: datetime | None = None

    @property
    def branch_label(self) -> str:
        if self.status is None:
            return ""
        return self.status.branch or (self.status.oid or "")[:7]

    @property
    def change_count(self) -> int:
        return len({c.path for c in self.status.changes}) if self.status else 0


@dataclass(frozen=True)
class RepoChoice:
    """One line of the repository dialog (E-02)."""

    name: str
    chosen: bool
    missing: bool = False  # chosen earlier but no longer a repository on disk


@dataclass(frozen=True)
class EmptyState:
    """What the file area shows instead of a list (P5)."""

    glyph: str
    head: str
    sub: str
    path: str | None = None
    action: str | None = None        # "choose_repos" or "recheck"
    glyph_color: str | None = None   # theme colour name; None means the default glyph colour


@dataclass(frozen=True)
class Operation:
    """What the window says while an operation runs (P4) and when it fails (P3)."""

    busy: str
    failed: str


STAGE = Operation("Dodawanie do Staged…", "Stage nie powiódł się")
UNSTAGE = Operation("Wycofywanie ze Staged…", "Unstage nie powiódł się")
MARK_RESOLVED = Operation("Oznaczanie jako rozwiązany…", "Oznaczenie jako rozwiązany nie powiodło się")
COMMIT = Operation("Zapisywanie commita…", "Commit nie powiódł się")
PUSH = Operation("Wypychanie do origin…", "Push nie powiódł się")
PULL = Operation("Pobieranie zmian…", "Pull nie powiódł się")
COMPARE_FAILED = "Porównanie nie powiodło się"
REFRESH_FAILED = "Odświeżanie nie powiodło się"


class AppModel:
    def __init__(self, settings: Settings, *, git: GitCli, diff_tool: ExternalDiffTool, worker: Executor,
                 confirm: Callable[[str, str], bool], clock: Callable[[], datetime] = datetime.now,
                 save_settings: Callable[[Settings], None] = lambda settings: None):
        self._settings = settings
        self._save_settings = save_settings
        self._clock = clock
        self._git = git
        self._diff_tool = diff_tool
        self._worker = worker
        self._confirm = confirm
        self._rootdir = settings.rootdir
        self._repos = {name: RepoView(name, settings.repo_path(name)) for name in settings.repos}
        self._listeners: list[Callable[[], None]] = []
        self.selected: str | None = None

    @classmethod
    def from_settings(cls, settings: Settings, *, git: GitCli, worker: Executor, confirm: Callable[[str, str], bool],
                      save_settings: Callable[[Settings], None] = lambda settings: None) -> AppModel:
        return cls(settings, git=git, diff_tool=CommandTemplateDiffTool(settings.diff_tool), worker=worker,
                   confirm=confirm, save_settings=save_settings)

    # ---------- choosing repositories (E-02, REQ-VCS-001) ----------

    @property
    def rootdir(self) -> str:
        return self._settings.rootdir

    def repo_choices(self) -> tuple[list[RepoChoice], str | None]:
        """First-level repositories of rootdir, then chosen ones that disappeared; or the error to show."""
        try:
            found = scan_rootdir(self._settings.root_path)
        except SettingsError as exc:
            return [], str(exc)
        chosen = set(self._settings.repos)
        choices = [RepoChoice(name, name in chosen) for name in found]
        choices += [RepoChoice(name, True, missing=True) for name in self._settings.repos if name not in found]
        return choices, None

    def set_repos(self, names: list[str]) -> None:
        """Save the chosen repositories; keep the state of the ones that stay, refresh the new ones."""
        self._settings = replace(self._settings, repos=tuple(names))
        self._save_settings(self._settings)
        old = self._repos
        self._repos = {name: old.get(name) or RepoView(name, self._settings.repo_path(name)) for name in names}
        if self.selected not in self._repos:
            self.selected = None
        self._changed()
        for name in names:
            if name not in old:
                self.refresh(name)

    # ---------- folder view (REQ-VCS-025) ----------

    @property
    def show_folders(self) -> bool:
        return self._settings.show_folders

    @show_folders.setter
    def show_folders(self, value: bool) -> None:
        self._settings = replace(self._settings, show_folders=value)
        self._save_settings(self._settings)
        self._changed()

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

    def sidebar_line(self, name: str) -> str:
        """Second line of a repository in the sidebar (UI-REFERENCE §4, P4)."""
        view = self._repos[name]
        if self._worker.busy(name):
            return "w toku…"
        if not view.available:
            return "niedostępne"
        if view.status is None:
            return ""
        status = view.status
        if status.upstream and not status.detached:
            return f"{view.branch_label} · ↑{status.ahead} ↓{status.behind}"
        return view.branch_label

    def badge(self, name: str) -> tuple[str, str] | None:
        """(text, kind) at the right of a sidebar row: change count or conflict; none when clean (P6)."""
        view = self._repos[name]
        if not view.available or view.status is None:
            return None
        if view.status.has_conflicts:
            return "konflikt", "conflict"
        return (str(view.change_count), "count") if view.change_count else None

    @property
    def empty_state(self) -> EmptyState | None:
        if not self._repos:
            return EmptyState("▣", "Wybierz repozytoria", "vcs-lite pokazuje repozytoria z folderu",
                              path=self._rootdir, action="choose_repos")
        view = self._current()
        if view is None:
            return EmptyState("←", "Wybierz repozytorium", "Kliknij je po lewej albo naciśnij ⌘1.")
        if not view.available:
            return EmptyState("⊘", "Repozytorium niedostępne", "Folder nie istnieje albo nie jest repozytorium gita.",
                              path=f"{self._rootdir}/{view.name}", action="recheck")
        if view.status is not None and not view.status.changes:
            return EmptyState("✓", "Brak zmian", f"Kopia robocza {view.name} jest zgodna z ostatnim commitem.",
                              glyph_color="add")
        return None

    def files(self, group: Group) -> list[FileChange]:
        view = self._current()
        return view.status.group(group) if view and view.status else []

    @property
    def error(self) -> str | None:
        view = self._current()
        return view.error if view else None

    @property
    def error_title(self) -> str | None:
        view = self._current()
        return view.error_title if view else None

    @property
    def busy_label(self) -> str | None:
        view = self._current()
        return view.busy_label if view else None

    def dismiss_error(self) -> None:
        view = self._current()
        if view:
            view.error = view.error_title = None
            self._changed()

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
    def commit_and_push_disabled_reason(self) -> str | None:
        reason = self.commit_disabled_reason
        if reason is None and self._current().status.detached:
            return "Odłączony HEAD: brak gałęzi do wypchnięcia"
        return reason

    @property
    def can_commit_and_push(self) -> bool:
        return self.commit_and_push_disabled_reason is None

    @property
    def pull_disabled_reason(self) -> str | None:
        view = self._current()
        if view is None:
            return "Wybierz repozytorium."
        if self._worker.busy(view.name):
            return "Trwa operacja na tym repozytorium."
        if not view.available or view.status is None:
            return "Repozytorium jest niedostępne."
        if view.status.detached:
            return "Odłączony HEAD: brak gałęzi do pull"
        if not view.status.upstream:
            return "Gałąź nie ma upstreamu"
        return None

    @property
    def can_pull(self) -> bool:
        return self.pull_disabled_reason is None

    # ---------- window chrome (DES-VCS-043) ----------

    @property
    def window_title(self) -> str:
        return f"vcs-lite — {self.selected}" if self.selected else "vcs-lite"

    @property
    def branch_summary(self) -> str:
        view = self._current()
        if view is None or view.status is None:
            return ""
        status = view.status
        if status.detached:
            return f"⎇ odłączony HEAD · {(status.oid or '')[:7]}"
        return f"⎇ {status.branch} → {status.upstream or 'brak upstreamu'}"

    @property
    def conflict_summary(self) -> str:
        """P2: the red toolbar chip; empty without conflicts."""
        count = len(self.files(Group.CONFLICTS))
        return f"{files_label(count)} w konflikcie" if count else ""

    @property
    def refreshed_label(self) -> str:
        view = self._current()
        return f"Odświeżono {view.refreshed_at:%H:%M}" if view and view.refreshed_at else ""

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
            view.error, view.error_title = str(outcome.error), REFRESH_FAILED  # keep the previous list, UC-VCS-02 2d
        elif outcome.error is not None:
            raise outcome.error
        else:
            view.available = outcome.value is not None
            view.status = outcome.value
            view.refreshed_at = self._clock()
        self._changed()

    # ---------- files ----------

    def toggle(self, change: FileChange) -> None:
        """Space: stage from Changes or Unversioned, unstage from Staged (DEC-VCS-040),
        mark as resolved from Conflicts (REQ-VCS-024)."""
        view = self._current()
        repo = self._repo(view)
        operation, kind = {Group.STAGED: (repo.unstage, UNSTAGE),
                           Group.CONFLICTS: (repo.mark_resolved, MARK_RESOLVED)}.get(change.group, (repo.stage, STAGE))
        self._run(view, kind, lambda: operation(change))

    def toggle_folder(self, group: Group, folder: str) -> None:
        """Folder button or space on a folder: stage from Changes and Unversioned, unstage from Staged
        (REQ-VCS-026); conflicts stay per file (REQ-VCS-024)."""
        changes = [c for c in self.files(group) if c.path.rpartition("/")[0] == folder]
        if not changes or group is Group.CONFLICTS:
            return
        view = self._current()
        repo = self._repo(view)
        operation, kind = (repo.unstage_all, UNSTAGE) if group is Group.STAGED else (repo.stage_all, STAGE)
        self._run(view, kind, lambda: operation(changes))

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
            view.error, view.error_title = str(outcome.error), COMPARE_FAILED
        elif outcome.value.failed:
            view.error, view.error_title = outcome.value.stderr.strip(), COMPARE_FAILED
        self.refresh(view.name)

    # ---------- commit, push, pull ----------
    # Each operation captures the repository selected at click time (REQ-VCS-021).

    def commit(self) -> None:
        if not self.can_commit:
            return
        view, message = self._current(), self._current().draft
        self._run(view, COMMIT, lambda: self._repo(view).commit(message), on_success=lambda: self._clear_draft(view))

    def commit_and_push(self) -> None:
        if not self.can_commit_and_push:
            return
        view, message = self._current(), self._current().draft
        self._run(view, COMMIT, lambda: self._repo(view).commit(message), on_success=lambda: self._pushed_after_commit(view))

    def _pushed_after_commit(self, view: RepoView) -> None:
        self._clear_draft(view)
        if view.status.upstream is not None:
            self._run(view, PUSH, lambda: self._repo(view).push())
        elif self._confirm(f"Gałąź {view.status.branch} nie ma upstreamu",  # P9
                           "Commit został zapisany. Wypchnąć gałąź do origin i ustawić upstream?"):
            self._run(view, PUSH, lambda: self._repo(view).push(set_upstream=True))

    def pull(self) -> None:
        if self.can_pull:
            view = self._current()
            self._run(view, PULL, lambda: self._repo(view).pull())

    # ---------- plumbing ----------

    def _current(self) -> RepoView | None:
        return self._repos.get(self.selected) if self.selected else None

    def _repo(self, view: RepoView) -> GitRepo:
        return GitRepo(view.path, self._git)

    @staticmethod
    def _clear_draft(view: RepoView) -> None:
        view.draft = ""

    def _run(self, view: RepoView, kind: Operation, operation: Callable[[], GitResult], *,
             on_success: Callable[[], None] | None = None) -> None:
        """Run a repository operation; report git's message on failure, then refresh (DES-VCS-016, DES-VCS-043)."""

        def done(outcome: Outcome) -> None:
            view.busy_label = None  # cleared first, so a chained operation can set its own
            result = outcome.value
            if outcome.error is not None:
                view.error, view.error_title = str(outcome.error), kind.failed
            elif not result.ok:
                view.error, view.error_title = result.message, kind.failed
            else:
                view.error = view.error_title = None
                if on_success:
                    on_success()  # may chain the next operation (push after commit), which refreshes itself
            self.refresh(view.name)  # rejected while a chained operation holds the repository
            self._changed()

        if self._worker.submit(view.name, operation, done):
            view.busy_label = kind.busy
            self._changed()
