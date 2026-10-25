"""Where a file opens, by its kind: pages in the browser, the file itself, or its macOS application.

Taken out of AppModel before the history panel (DEC-VCS-119), so a change of a group and, later, a file of
a commit open the same way. The opener knows a repository only by its name and path; what goes wrong is
reported back through `on_error`, and a finished comparison through `on_compared`.

Trace: DES-VCS-068, REQ-VCS-040, DES-VCS-060, DES-VCS-036, REQ-VCS-023, REQ-VCS-031, REQ-VCS-034, DEC-VCS-098, DEC-VCS-100, DEC-VCS-104, DEC-VCS-106
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from vcs_lite.app.worker import Executor, Outcome
from vcs_lite.core.difftool import ExternalDiffTool, compare
from vcs_lite.core.filekind import Kind, is_text, kind_of
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.log import Commit, CommitFile
from vcs_lite.core.pageview import DocumentReader
from vcs_lite.core.repo import GitRepo
from vcs_lite.core.status import FileChange, Side

SIDE_LABELS = {Side.HEAD: "HEAD", Side.INDEX: "indeks", Side.WORKTREE: "kopia robocza", Side.EMPTY: "pusty"}
COMPARE_FAILED = "Porównanie nie powiodło się"
OPEN_FAILED = "Otwieranie nie powiodło się"


class Place(Protocol):
    """A repository as the opener needs it; RepoView is one."""

    name: str
    path: Path


class PageOpener:
    def __init__(self, *, git: GitCli, worker: Executor, diff_tool: ExternalDiffTool,
                 markdown_tool: ExternalDiffTool, markdown_reader: DocumentReader, text_reader: DocumentReader,
                 external_tool: ExternalDiffTool | None, browser: Callable[[Path], None],
                 keep_copy: Callable[[bytes, str], Path], opener: Callable[[list[str]], None],
                 on_error: Callable[[Place, str, str], None], on_compared: Callable[[Place], None]):
        self._git, self._worker = git, worker
        self._diff_tool, self._markdown_tool = diff_tool, markdown_tool
        self._markdown_reader, self._text_reader = markdown_reader, text_reader
        self.external_tool = external_tool
        self._browser, self._keep_copy, self._opener = browser, keep_copy, opener
        self._on_error, self._on_compared = on_error, on_compared

    def change(self, place: Place, change: FileChange, *, external: bool = False) -> None:
        """A change of a group in the browser, by the kind of file (REQ-VCS-034): Markdown as a rendered diff
        (REQ-VCS-031), an image or PDF as the file itself, anything else side by side (REQ-VCS-023).
        `external` uses the command-line plugin instead (DEC-VCS-106)."""
        if change.left is None or change.right is None:
            return
        kind = kind_of(change.path)
        if external:
            if self.external_tool is None:
                return
            tool = self.external_tool
        elif kind.shown_as_file:
            self._show_change(place, change)
            return
        else:
            tool = self._markdown_tool if kind is Kind.MARKDOWN else self._diff_tool
        # Its own key, so the repository stays usable while the diff window is open.
        self._worker.submit(f"{place.name}:diff:{change.group.value}:{change.path}",
                            lambda: self._compare(place, change, tool),
                            lambda outcome: self._compared(place, outcome))

    def file(self, place: Place, path: str, line: int | None = None) -> None:
        """A file without changes, by its kind (REQ-VCS-034): Markdown read as a document, an image or PDF in
        the browser, text as a page with line numbers, anything else (and a folder) in its application. With
        a line, a page scrolls to it (a search match, DES-VCS-056)."""
        full, kind = place.path / path, kind_of(path)
        if kind is Kind.MARKDOWN:
            self._read(place, self._markdown_reader, path, line)
        elif kind.shown_as_file:
            self._show(place, path, lambda: full)
        elif is_text(full):
            self._read(place, self._text_reader, path, line)
        else:
            self.in_app(place, path)

    def commit_file(self, place: Place, commit: Commit, file: CommitFile) -> None:
        """A file of a commit: its first parent against the commit, by the kind of file (H-46). An added file
        has an empty left side, a deleted one an empty right side; nothing is refreshed afterwards."""
        parent = commit.parents[0] if commit.parents else None
        left = None if file.status == "A" or parent is None else (parent, file.old_path or file.path)
        right = None if file.status == "D" else (commit.hash, file.path)
        repo, kind = GitRepo(place.path, self._git), kind_of(file.path)

        def side(version: tuple[str, str] | None) -> bytes:
            return repo.blob(*version) if version else b""

        def title(version: tuple[str, str] | None) -> str:
            return f"{file.path} ({version[0][:7] if version else SIDE_LABELS[Side.EMPTY]})"

        key = f"{place.name}:commit:{commit.hash}:{file.path}"
        if kind.shown_as_file:
            version = right or left
            self._show(place, key, lambda: self._keep_copy(side(version), Path(file.path).name))
            return
        tool = self._markdown_tool if kind is Kind.MARKDOWN else self._diff_tool
        self._worker.submit(key, lambda: compare(tool, side(left), side(right), name=Path(file.path).name,
                                                 left_title=title(left), right_title=title(right)),
                            lambda outcome: self._compared(place, outcome, refresh=False))

    def in_app(self, place: Place, path: str) -> None:
        """The file or folder in its default macOS application, e.g. to edit it (DEC-VCS-090, DEC-VCS-104)."""
        self._open(place, ["open"], path)

    def reveal(self, place: Place, path: str) -> None:
        """The file or folder selected in Finder."""
        self._open(place, ["open", "-R"], path)

    # ---------- the ways of opening ----------

    def _read(self, place: Place, reader: DocumentReader, path: str, line: int | None) -> None:
        full, title = place.path / path, f"{path} ({SIDE_LABELS[Side.WORKTREE]})"
        reader = reader if line is None else reader.at_line(line)
        self._worker.submit(f"{place.name}:read:{path}",
                            lambda: compare(reader, full, full, name=full.name, left_title=title, right_title=title),
                            lambda outcome: self._compared(place, outcome))

    def _show_change(self, place: Place, change: FileChange) -> None:
        """An image or PDF of a group: the right side of T-VCS-01, or the left one when the file is gone.
        A version that is not on disk is kept as a copy first (DEC-VCS-100)."""
        side, path = change.right, change.path
        if side is Side.EMPTY:  # deleted: its last version
            side = change.left
            path = change.orig_path if side is Side.HEAD and change.orig_path else change.path

        def file() -> Path:
            content = GitRepo(place.path, self._git).content(side, path)
            return content if isinstance(content, Path) else self._keep_copy(content, Path(path).name)
        self._show(place, f"{change.group.value}:{change.path}", file)

    def _show(self, place: Place, key: str, file: Callable[[], Path]) -> None:
        self._worker.submit(f"{place.name}:show:{key}", lambda: self._browser(file()),
                            lambda outcome: self._opened(place, outcome))

    def _open(self, place: Place, command: list[str], path: str) -> None:
        argv = [*command, str(place.path / path)]
        key = f"{place.name}:{' '.join(command)}:{path}"  # opening and revealing one file do not block each other
        self._worker.submit(key, lambda: self._opener(argv), lambda outcome: self._opened(place, outcome))

    def _compare(self, place: Place, change: FileChange, tool: ExternalDiffTool):
        left, right = GitRepo(place.path, self._git).sides(change)
        return compare(tool, left, right, name=Path(change.path).name,
                       left_title=f"{change.path} ({SIDE_LABELS[change.left]})",
                       right_title=f"{change.path} ({SIDE_LABELS[change.right]})")

    # ---------- results ----------

    def _opened(self, place: Place, outcome: Outcome) -> None:
        if outcome.error is not None:
            self._on_error(place, str(outcome.error), OPEN_FAILED)

    def _compared(self, place: Place, outcome: Outcome, *, refresh: bool = True) -> None:
        """After a diff of the working copy the repository is read again: the page may have been used to
        look before editing; a file of a commit cannot change, so it is not."""
        if outcome.error is not None:
            self._on_error(place, str(outcome.error), COMPARE_FAILED)
        elif outcome.value.failed:
            self._on_error(place, outcome.value.stderr.strip(), COMPARE_FAILED)
        if refresh:
            self._on_compared(place)
