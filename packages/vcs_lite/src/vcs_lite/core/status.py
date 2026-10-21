"""Parse `git status --porcelain=v2 -z --branch` into the groups of T-VCS-01.

Trace: DES-VCS-005, DES-VCS-006, REQ-VCS-002, REQ-VCS-003, REQ-VCS-004, REQ-VCS-019, T-VCS-01
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# No --ignored, so ignored files never appear (REQ-VCS-004); untracked files one by one (DEC-VCS-006).
STATUS_ARGS = ("status", "--porcelain=v2", "-z", "--branch", "--untracked-files=all")


class Group(Enum):
    STAGED = "Staged"
    CHANGES = "Changes"
    UNVERSIONED = "Unversioned"
    CONFLICTS = "Conflicts"


class Side(Enum):
    HEAD = "HEAD"
    INDEX = "index"
    WORKTREE = "worktree"
    EMPTY = "empty"


@dataclass(frozen=True)
class FileChange:
    path: str
    group: Group
    code: str
    left: Side | None
    right: Side | None
    orig_path: str | None = None  # renames and copies: the HEAD side is read from this path


@dataclass(frozen=True)
class RepoStatus:
    oid: str | None  # None before the first commit
    branch: str | None  # None when HEAD is detached
    upstream: str | None
    ahead: int
    behind: int
    changes: tuple[FileChange, ...]

    @property
    def detached(self) -> bool:
        return self.branch is None

    @property
    def has_conflicts(self) -> bool:
        return any(c.group is Group.CONFLICTS for c in self.changes)

    def group(self, group: Group) -> list[FileChange]:
        return [c for c in self.changes if c.group is group]


def _staged_sides(x: str, initial: bool) -> tuple[Side, Side]:
    if initial or x == "A":
        return Side.EMPTY, Side.INDEX
    if x == "D":
        return Side.HEAD, Side.EMPTY
    return Side.HEAD, Side.INDEX  # M, T, R, C


def _changes_sides(y: str) -> tuple[Side, Side]:
    if y == "D":
        return Side.INDEX, Side.EMPTY
    if y == "A":  # intent-to-add (git add -N): nothing in the index yet
        return Side.EMPTY, Side.WORKTREE
    return Side.INDEX, Side.WORKTREE  # M, T


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="surrogateescape")


def parse_status(raw: bytes) -> RepoStatus:
    records = [_decode(r) for r in raw.split(b"\0")]
    oid = branch = upstream = None
    ahead = behind = 0
    initial = False
    changes: list[FileChange] = []
    i = 0
    while i < len(records):
        rec = records[i]
        i += 1
        if not rec:
            continue
        if rec.startswith("# "):
            key, _, value = rec[2:].partition(" ")
            if key == "branch.oid":
                initial = value == "(initial)"
                oid = None if initial else value
            elif key == "branch.head":
                branch = None if value == "(detached)" else value
            elif key == "branch.upstream":
                upstream = value
            elif key == "branch.ab":
                a, b = value.split()
                ahead, behind = int(a), -int(b)
            continue
        kind = rec[0]
        if kind == "?":
            changes.append(FileChange(rec[2:], Group.UNVERSIONED, "?", Side.EMPTY, Side.WORKTREE))
        elif kind == "u":
            parts = rec.split(" ", 10)
            changes.append(FileChange(parts[10], Group.CONFLICTS, parts[1], None, None))
        elif kind in "12":
            parts = rec.split(" ", 8 if kind == "1" else 9)
            x, y = parts[1][0], parts[1][1]
            path = parts[-1]
            orig = None
            if kind == "2":
                orig = records[i]
                i += 1
            if x != ".":
                left, right = _staged_sides(x, initial)
                changes.append(FileChange(path, Group.STAGED, x, left, right, orig))
            if y != ".":
                left, right = _changes_sides(y)
                changes.append(FileChange(path, Group.CHANGES, y, left, right))
        # "!" (ignored) is never requested, see STATUS_ARGS
    return RepoStatus(oid, branch, upstream, ahead, behind, tuple(changes))
