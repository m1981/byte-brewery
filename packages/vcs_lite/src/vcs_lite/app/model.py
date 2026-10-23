"""State and rules of the main window, without Tk: repository list, files, drafts, buttons, operations.

Trace: DES-VCS-016, DES-VCS-046, DES-VCS-055, DES-VCS-056, DES-VCS-060, REQ-VCS-033, REQ-VCS-034, DEC-VCS-095, DEC-VCS-098, DEC-VCS-100, DEC-VCS-106, REQ-VCS-027, REQ-VCS-029, REQ-VCS-030, DES-VCS-048, REQ-VCS-031, DES-VCS-049, REQ-VCS-032, DES-VCS-050, DES-VCS-018, DES-VCS-021, DES-VCS-043, DES-VCS-045, DES-VCS-026, DES-VCS-036, DES-VCS-038, REQ-VCS-002, REQ-VCS-009, REQ-VCS-010, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-015, REQ-VCS-016, REQ-VCS-018, REQ-VCS-019, REQ-VCS-020, REQ-VCS-021, REQ-VCS-022, REQ-VCS-023, REQ-VCS-024, REQ-VCS-025, REQ-VCS-026, REQ-VCS-001, S-VCS-01, E-02
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from pathlib import Path

from vcs_lite.app.worker import Executor, Outcome
from vcs_lite.core import pagekit
from vcs_lite.core.browser import show
from vcs_lite.core.difftool import CommandTemplateDiffTool, ExternalDiffTool, compare
from vcs_lite.core.filekind import Kind, is_text, kind_of
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.pageview import DocumentReader, MarkdownDiffTool, TextDiffTool, open_with_macos
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


def is_markdown(path: str) -> bool:
    """Files opened as a rendered diff by a double click (REQ-VCS-031)."""
    return kind_of(path) is Kind.MARKDOWN


class RepoState(Enum):
    """S-VCS-01."""

    UNAVAILABLE = "niedostępne"
    CLEAN = "czyste"
    CHANGES = "zmiany"
    CONFLICT = "konflikt"
    MERGE = "scalanie"  # merge in progress, no conflicts left (REQ-VCS-027)
    BUSY = "w toku"


@dataclass(frozen=True)
class ProjectFile:
    """A row of the project tree: any tracked or unversioned file, with its change if it has one."""

    path: str
    change: FileChange | None = None


# Which change a file in several groups shows in the project tree: the one of the working copy first.
PROJECT_CHANGE_ORDER = (Group.CONFLICTS, Group.CHANGES, Group.UNVERSIONED, Group.STAGED)


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
    tracked: tuple[str, ...] = ()    # files of the index, read only in the project view (DES-VCS-050)

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
IGNORE = Operation("Dodawanie do .gitignore…", "Dodanie do .gitignore nie powiodło się")
PULL = Operation("Pobieranie zmian…", "Pull nie powiódł się")
COMPARE_FAILED = "Porównanie nie powiodło się"
REFRESH_FAILED = "Odświeżanie nie powiodło się"
OPEN_FAILED = "Otwieranie nie powiodło się"


class AppModel:
    def __init__(self, settings: Settings, *, git: GitCli, worker: Executor, confirm: Callable[[str, str], bool],
                 clock: Callable[[], datetime] = datetime.now,
                 save_settings: Callable[[Settings], None] = lambda settings: None,
                 diff_tool: ExternalDiffTool | None = None, markdown_tool: ExternalDiffTool | None = None,
                 markdown_reader: DocumentReader | None = None, text_reader: DocumentReader | None = None,
                 external_tool: ExternalDiffTool | None = None, browser: Callable[[Path], None] = show,
                 keep_copy: Callable[[bytes, str], Path] = pagekit.keep_copy,
                 opener: Callable[[list[str]], None] = open_with_macos):
        """Pages in the browser by default (DEC-VCS-102): side-by-side diff, Markdown diff, readers of both.
        `external_tool` is the optional command-line plugin (DEC-VCS-106); `browser` shows images and PDFs."""
        self._settings = settings
        self._save_settings = save_settings
        self._clock = clock
        self._git = git
        self._diff_tool = diff_tool or TextDiffTool(theme=self._page_theme)
        self._markdown_tool = markdown_tool or MarkdownDiffTool(theme=self._page_theme)
        self._markdown_reader = markdown_reader or MarkdownDiffTool(read=True, theme=self._page_theme)
        self._text_reader = text_reader or TextDiffTool(read=True, theme=self._page_theme)
        self._external_tool = external_tool
        self._browser, self._keep_copy = browser, keep_copy
        self._opener = opener
        self._worker = worker
        self._confirm = confirm
        self._rootdir = settings.rootdir
        self._repos = {name: RepoView(name, settings.repo_path(name)) for name in settings.repos}
        self._listeners: list[Callable[[], None]] = []
        self.selected: str | None = None

    @classmethod
    def from_settings(cls, settings: Settings, *, git: GitCli, worker: Executor, confirm: Callable[[str, str], bool],
                      save_settings: Callable[[Settings], None] = lambda settings: None) -> AppModel:
        external = CommandTemplateDiffTool(settings.external_diff_tool) if settings.external_diff_tool else None
        return cls(settings, git=git, worker=worker, confirm=confirm, save_settings=save_settings,
                   external_tool=external)

    def _page_theme(self) -> str:
        """Read at every opening, so a change in the menu applies to the next page (DEC-VCS-083)."""
        return self._settings.markdown_theme

    @property
    def has_external_tool(self) -> bool:
        """The command-line diff tool plugin is set in the settings (DEC-VCS-106)."""
        return self._external_tool is not None

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
    def list_view(self) -> str:
        """The View switch: changes, folders or project (REQ-VCS-025, DEC-VCS-091)."""
        return self._settings.list_view

    @list_view.setter
    def list_view(self, value: str) -> None:
        self._settings = replace(self._settings, list_view=value)
        self._save_settings(self._settings)
        if value == "project" and self.selected:
            self.refresh(self.selected)  # the tracked files are read only for this view
        self._changed()

    @property
    def markdown_theme(self) -> str:
        """Colours of the rendered Markdown diff: system, light or dark (REQ-VCS-031)."""
        return self._settings.markdown_theme

    @markdown_theme.setter
    def markdown_theme(self, value: str) -> None:
        self._settings = replace(self._settings, markdown_theme=value)
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
        status = view.status
        if status is not None and status.has_conflicts:
            return RepoState.CONFLICT
        if status is not None and status.merging:
            return RepoState.MERGE
        return RepoState.CHANGES if status is not None and status.changes else RepoState.CLEAN

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
        line = view.branch_label
        if status.upstream and not status.detached:
            line = f"{line} · ↑{status.ahead} ↓{status.behind}"
        return f"{line} · merge" if status.merging else line  # P11

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
        if view.status is not None and not view.status.changes and view.status.merging:  # P11
            return EmptyState("⑂", "Merge gotowy do commita",
                              f"Konflikty w {view.name} są rozwiązane, a wynik jest taki sam jak ostatni commit. "
                              "Wpisz wiadomość i zatwierdź, żeby zakończyć merge.")
        if view.status is not None and not view.status.changes:
            return EmptyState("✓", "Brak zmian", f"Kopia robocza {view.name} jest zgodna z ostatnim commitem.",
                              glyph_color="add")
        return None

    def project_files(self) -> list[ProjectFile]:
        """Tracked and unversioned files of the selected repository, by path (REQ-VCS-032)."""
        view = self._current()
        if self.list_view != "project" or view is None or view.status is None:
            return []
        changes = self._changes_by_path(view)
        return [ProjectFile(path, changes.get(path)) for path in sorted(set(view.tracked) | set(changes))]

    def change_of(self, path: str) -> FileChange | None:
        """The change a file shows outside its group, as in the project tree: a search match's colour."""
        view = self._current()
        return self._changes_by_path(view).get(path) if view and view.status else None

    @staticmethod
    def _changes_by_path(view: RepoView) -> dict[str, FileChange]:
        changes: dict[str, FileChange] = {}
        for group in reversed(PROJECT_CHANGE_ORDER):  # the earlier group wins
            changes.update({c.path: c for c in view.status.group(group)})
        return changes

    @property
    def selected_path(self) -> Path | None:
        """Where „Szukaj w plikach” searches: the selected repository, while it is one (DEC-VCS-094)."""
        view = self._current()
        return view.path if view and view.available else None

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
        if state is not RepoState.MERGE and not self.files(Group.STAGED):  # a merge commits even with nothing staged
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
    def merge_summary(self) -> str:
        """P11: the blue toolbar chip while a merge waits for its commit."""
        view = self._current()
        return "merge gotowy do commita" if view and self.state(view.name) is RepoState.MERGE else ""

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

    def _read_status(self, view: RepoView) -> tuple[RepoStatus, tuple[str, ...]] | None:
        if not (view.path / ".git").exists():
            return None
        repo = self._repo(view)
        tracked = tuple(repo.tracked_files()) if self.list_view == "project" else ()
        return repo.status(), tracked

    def _status_read(self, view: RepoView, outcome: Outcome) -> None:
        if isinstance(outcome.error, GitError):
            view.error, view.error_title = str(outcome.error), REFRESH_FAILED  # keep the previous list, UC-VCS-02 2d
        elif outcome.error is not None:
            raise outcome.error
        else:
            view.available = outcome.value is not None
            view.status, view.tracked = outcome.value or (None, ())
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
        self.toggle_many(group, [c for c in self.files(group) if c.path.rpartition("/")[0] == folder])

    def toggle_many(self, group: Group, changes: list[FileChange]) -> None:
        """Several files of one group in one git call: stage from Changes and Unversioned, unstage from Staged
        (REQ-VCS-026, REQ-VCS-029). Conflicts are marked one by one, each after its own marker check."""
        if not changes or group is Group.CONFLICTS:
            return
        view = self._current()
        repo = self._repo(view)
        operation, kind = (repo.unstage_all, UNSTAGE) if group is Group.STAGED else (repo.stage_all, STAGE)
        self._run(view, kind, lambda: operation(changes))

    def add_to_gitignore(self, files: list[str], folders: list[str]) -> None:
        """Context menu „Dodaj do .gitignore” on unversioned files and folders (REQ-VCS-030)."""
        unversioned = [c.path for c in self.files(Group.UNVERSIONED)]
        members = {folder: [p for p in unversioned if p.startswith(f"{folder}/")] for folder in folders}
        files = [f for f in files if f in unversioned]
        if not files and not members:
            return
        view = self._current()
        repo = self._repo(view)
        self._run(view, IGNORE, lambda: repo.ignore(files, members))

    def activate(self, change: FileChange, *, external: bool = False) -> None:
        """Double click or Enter: the change in the browser, by the kind of file (REQ-VCS-034): Markdown as
        a rendered diff (REQ-VCS-031), an image or PDF as the file itself, anything else side by side
        (REQ-VCS-023). `external` uses the command-line plugin instead (DEC-VCS-106)."""
        view = self._current()
        if change.left is None or change.right is None:
            return
        kind = kind_of(change.path)
        if external:
            if self._external_tool is None:
                return
            tool = self._external_tool
        elif kind.shown_as_file:
            self._show_change(view, change)
            return
        else:
            tool = self._markdown_tool if kind is Kind.MARKDOWN else self._diff_tool
        # Its own key, so the repository stays usable while the diff window is open.
        self._worker.submit(f"{view.name}:diff:{change.group.value}:{change.path}",
                            lambda: self._compare(view, change, tool),
                            lambda outcome: self._compared(view, outcome))

    def open_file(self, path: str, line: int | None = None) -> None:
        """A file without changes, by its kind (REQ-VCS-034): Markdown read as a document, an image or PDF in
        the browser, text as a page with line numbers, anything else (and a folder) in its application. With
        a line, a page scrolls to it (a search match, DES-VCS-056)."""
        view = self._current()
        full, kind = view.path / path, kind_of(path)
        if kind is Kind.MARKDOWN:
            self._read(view, self._markdown_reader, path, line)
        elif kind.shown_as_file:
            self._show(view, path, lambda: full)
        elif is_text(full):
            self._read(view, self._text_reader, path, line)
        else:
            self.open_in_app(path)

    def open_match(self, path: str, line: int) -> None:
        """Enter on a search match opens it like the project tree does, at the line (DEC-VCS-095, DEC-VCS-098)."""
        self.open_file(path, line)

    def _read(self, view: RepoView, reader: DocumentReader, path: str, line: int | None) -> None:
        full, title = view.path / path, f"{path} ({SIDE_LABELS[Side.WORKTREE]})"
        reader = reader if line is None else reader.at_line(line)
        self._worker.submit(f"{view.name}:read:{path}",
                            lambda: compare(reader, full, full, name=full.name, left_title=title, right_title=title),
                            lambda outcome: self._compared(view, outcome))

    def _show_change(self, view: RepoView, change: FileChange) -> None:
        """An image or PDF of a group: the right side of T-VCS-01, or the left one when the file is gone.
        A version that is not on disk is kept as a copy first (DEC-VCS-100)."""
        side, path = change.right, change.path
        if side is Side.EMPTY:  # deleted: its last version
            side = change.left
            path = change.orig_path if side is Side.HEAD and change.orig_path else change.path

        def file() -> Path:
            content = self._repo(view).content(side, path)
            return content if isinstance(content, Path) else self._keep_copy(content, Path(path).name)
        self._show(view, f"{change.group.value}:{change.path}", file)

    def _show(self, view: RepoView, key: str, file: Callable[[], Path]) -> None:
        self._worker.submit(f"{view.name}:show:{key}", lambda: self._browser(file()),
                            lambda outcome: self._opened(view, outcome))

    def open_in_app(self, path: str) -> None:
        """The file or folder in its default macOS application, e.g. to edit it (DEC-VCS-090, DEC-VCS-104)."""
        self._open(["open"], path)

    def reveal(self, path: str) -> None:
        """The file or folder selected in Finder."""
        self._open(["open", "-R"], path)

    def _open(self, command: list[str], path: str) -> None:
        view = self._current()
        argv = [*command, str(view.path / path)]
        key = f"{view.name}:{' '.join(command)}:{path}"  # opening and revealing one file do not block each other
        self._worker.submit(key, lambda: self._opener(argv), lambda outcome: self._opened(view, outcome))

    def _opened(self, view: RepoView, outcome: Outcome) -> None:
        if outcome.error is not None:
            view.error, view.error_title = str(outcome.error), OPEN_FAILED
            self._changed()

    def _compare(self, view: RepoView, change: FileChange, tool: ExternalDiffTool):
        left, right = self._repo(view).sides(change)
        return compare(tool, left, right, name=Path(change.path).name,
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
        self._changed()  # the window shows the emptied message before a question can block it
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
