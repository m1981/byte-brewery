"""Operations on one repository: status, diff sides, stage, unstage, commit, push, pull.

Trace: DES-VCS-007, DES-VCS-011, DES-VCS-012, DES-VCS-013, DES-VCS-014, DES-VCS-015, REQ-VCS-005, REQ-VCS-009, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-017, REQ-VCS-020
"""

from __future__ import annotations

from pathlib import Path

from vcs_lite.core.difftool import Content
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.status import STATUS_ARGS, FileChange, RepoStatus, Side, parse_status


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
        return self.git.run(self.path, "add", "--", change.path)  # also records deletions

    def unstage(self, change: FileChange) -> GitResult:
        paths = [p for p in (change.orig_path, change.path) if p]
        if self.status().oid is None:  # no HEAD to restore from
            return self.git.run(self.path, "rm", "-q", "--cached", "--", *paths)
        return self.git.run(self.path, "restore", "--staged", "--", *paths)

    def commit(self, message: str) -> GitResult:
        return self.git.run(self.path, "commit", "-F", "-", input=message.encode("utf-8"))

    def push(self, *, set_upstream: bool = False) -> GitResult:
        args = ("push", "-u", "origin", "HEAD") if set_upstream else ("push",)
        return self.git.run(self.path, *args, network=True)

    def pull(self) -> GitResult:
        return self.git.run(self.path, "pull", "--ff-only", network=True)
