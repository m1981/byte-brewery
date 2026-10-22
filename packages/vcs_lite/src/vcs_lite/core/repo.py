"""Operations on one repository: status, diff sides, stage, unstage, commit, push, pull.

Trace: DES-VCS-007, DES-VCS-011, DES-VCS-012, DES-VCS-013, DES-VCS-014, DES-VCS-015, DES-VCS-044, DES-VCS-045, REQ-VCS-005, REQ-VCS-024, REQ-VCS-026, REQ-VCS-009, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-017, REQ-VCS-020
"""

from __future__ import annotations

from pathlib import Path

from vcs_lite.core.difftool import Content
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.status import STATUS_ARGS, FileChange, RepoStatus, Side, parse_status


# Lines that only a merge leaves behind. A bare "=======" is not one of them: Markdown uses it to
# underline headings, and a resolved file never keeps "<<<<<<<" or ">>>>>>>" (DES-VCS-044).
CONFLICT_MARKERS = (b"<<<<<<<", b">>>>>>>", b"|||||||")


class UnresolvedConflict(Exception):
    def __init__(self, path: str, line: int):
        super().__init__(f"{path}: plik nadal zawiera znaczniki konfliktu (linia {line}).")
        self.path = path
        self.line = line


def first_conflict_marker(path: Path) -> int | None:
    """1-based number of the first line that starts with a conflict marker, or None."""
    for number, line in enumerate(path.read_bytes().splitlines(), start=1):
        if line.startswith(CONFLICT_MARKERS):
            return number
    return None


class GitError(Exception):
    def __init__(self, result: GitResult):
        super().__init__(result.message)
        self.result = result


class GitRepo:
    def __init__(self, path: Path, git: GitCli):
        self.path = path
        self.git = git

    def _read(self, *args: str) -> GitResult:
        result = self.git.run(self.path, *args, read_only=True)
        if not result.ok:
            raise GitError(result)
        return result

    def status(self) -> RepoStatus:
        return parse_status(self._read(*STATUS_ARGS).stdout)

    def content(self, side: Side, path: str) -> Content:
        if side is Side.EMPTY:
            return b""
        if side is Side.WORKTREE:
            return self.path / path
        rev = f"HEAD:{path}" if side is Side.HEAD else f":{path}"
        return self._read("cat-file", "blob", rev).stdout

    def sides(self, change: FileChange) -> tuple[Content, Content]:
        if change.left is None or change.right is None:
            raise ValueError(f"{change.path}: brak stron diffu dla grupy {change.group.value}")
        left_path = change.orig_path if change.left is Side.HEAD and change.orig_path else change.path
        return self.content(change.left, left_path), self.content(change.right, change.path)

    def stage(self, change: FileChange) -> GitResult:
        return self.stage_all([change])

    def stage_all(self, changes: list[FileChange]) -> GitResult:
        """One `git add` for all files; it also records deletions (REQ-VCS-026)."""
        return self.git.run(self.path, "add", "--", *(c.path for c in changes))

    def unstage(self, change: FileChange) -> GitResult:
        return self.unstage_all([change])

    def unstage_all(self, changes: list[FileChange]) -> GitResult:
        paths = [p for c in changes for p in (c.orig_path, c.path) if p]
        if self.status().oid is None:  # no HEAD to restore from
            return self.git.run(self.path, "rm", "-q", "--cached", "--", *paths)
        return self.git.run(self.path, "restore", "--staged", "--", *paths)

    def mark_resolved(self, change: FileChange) -> GitResult:
        """Stage a conflicted file once its markers are gone; a deleted file is staged as a deletion."""
        worktree_file = self.path / change.path
        if not worktree_file.exists():
            return self.git.run(self.path, "rm", "-q", "--", change.path)
        line = first_conflict_marker(worktree_file)
        if line is not None:
            raise UnresolvedConflict(change.path, line)
        return self.git.run(self.path, "add", "--", change.path)

    def commit(self, message: str) -> GitResult:
        return self.git.run(self.path, "commit", "-F", "-", input=message.encode("utf-8"))

    def push(self, *, set_upstream: bool = False) -> GitResult:
        args = ("push", "-u", "origin", "HEAD") if set_upstream else ("push",)
        return self.git.run(self.path, *args, network=True)

    def pull(self) -> GitResult:
        return self.git.run(self.path, "pull", "--ff-only", network=True)
