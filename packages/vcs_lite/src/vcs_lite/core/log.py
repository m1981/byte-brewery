"""Values of the history panel and the parsers of git's output, without any I/O (DES-VCS-064).

The reader is a port, like TextSearcher for the search window, so the session and the panel never depend
on git directly. Records of `git log -z` are separated by NUL and their fields by US (0x1f), which no
name, label or subject contains.

Trace: DES-VCS-079, REQ-VCS-040, DES-VCS-064, DES-VCS-071, REQ-VCS-041, REQ-VCS-037, REQ-VCS-040, DEC-VCS-116, DEC-VCS-120
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol

from vcs_lite.core.changes import LineStats

FIELD = "\x1f"
FORMAT = FIELD.join(["%H", "%P", "%an", "%ae", "%at", "%D", "%s"])   # hash, parents, author, e-mail, time, labels, subject


class RefKind(Enum):
    LOCAL = "local"
    REMOTE = "remote"
    TAG = "tag"
    HEAD = "head"          # a detached HEAD


@dataclass(frozen=True)
class Ref:
    kind: RefKind
    name: str
    current: bool = False  # the branch HEAD points to


@dataclass(frozen=True)
class Commit:
    hash: str
    parents: tuple[str, ...]
    author: str
    email: str
    time: int              # author time, seconds since the epoch
    refs: tuple[Ref, ...]
    subject: str

    @property
    def short(self) -> str:
        return self.hash[:7]

    @property
    def merge(self) -> bool:
        return len(self.parents) > 1


@dataclass(frozen=True)
class CommitFile:
    status: str            # A, M, D, R, T (git's letter without the similarity score)
    path: str
    old_path: str | None = None


@dataclass(frozen=True)
class CommitDetails:
    commit: Commit
    body: str              # the message without its subject line
    files: tuple[CommitFile, ...]
    lines: dict[str, LineStats] = field(default_factory=dict)


class Scope(Enum):
    ALL = "all"            # branches, remote branches, tags and HEAD (H-02)
    CURRENT = "current"    # what HEAD reaches (H-03)


@dataclass(frozen=True)
class LogQuery:
    scope: Scope = Scope.ALL
    text: str = ""
    path: str = ""          # „Pokaż historię”: one file or folder (DEC-VCS-124)
    folder: bool = False

    @property
    def phrase(self) -> str:
        return self.text.strip()

    @property
    def filtered(self) -> bool:
        return bool(self.phrase)

    @property
    def flat(self) -> bool:
        """Commits are left out, so the graph has no lines (H-34, H-53)."""
        return self.filtered or bool(self.path)


@dataclass(frozen=True)
class LogPage:
    commits: tuple[Commit, ...]
    more: bool             # git has more commits after these
    paths: dict[str, CommitFile] = field(default_factory=dict)   # a file's history: its change in each commit


class HistoryReader(Protocol):
    def page(self, repo: Path, query: LogQuery, skip: int) -> LogPage: ...

    def count(self, repo: Path, query: LogQuery) -> int: ...

    def unpushed(self, repo: Path) -> set[str]: ...

    def details(self, repo: Path, commit: Commit) -> CommitDetails: ...

    def remote_url(self, repo: Path) -> str | None: ...


# ---------- parsers ----------

def _text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def parse_refs(text: str) -> tuple[Ref, ...]:
    """Labels of `%D` with `--decorate=full` (H-07): the kind comes from the full ref name, so a local
    branch called "origin/x" stays local; remote HEADs, `grafted` and other refs are not labels."""
    refs = []
    for item in filter(None, (part.strip() for part in text.split(", "))):
        current = item.startswith("HEAD -> ")
        item = item.removeprefix("HEAD -> ")
        if item == "HEAD":
            refs.append(Ref(RefKind.HEAD, "HEAD"))
        elif item.startswith("tag: refs/tags/"):
            refs.append(Ref(RefKind.TAG, item.removeprefix("tag: refs/tags/")))
        elif item.startswith("refs/heads/"):
            refs.append(Ref(RefKind.LOCAL, item.removeprefix("refs/heads/"), current=current))
        elif item.startswith("refs/remotes/") and not item.endswith("/HEAD"):
            refs.append(Ref(RefKind.REMOTE, item.removeprefix("refs/remotes/")))
    return tuple(refs)


def parse_log(raw: bytes) -> list[Commit]:
    commits = []
    for record in filter(None, raw.split(b"\0")):
        hash_, parents, author, email, time, refs, subject = _text(record.strip(b"\n")).split(FIELD, 6)
        commits.append(Commit(hash_, tuple(dict.fromkeys(parents.split())), author, email, int(time),
                              parse_refs(refs), subject))
    return commits


def parse_name_status(raw: bytes) -> tuple[CommitFile, ...]:
    """`--name-status -z`: a status and a path, or for a rename or copy a status and two paths."""
    fields = [_text(f) for f in raw.split(b"\0")]
    files, i = [], 0
    while i < len(fields) and fields[i]:
        status = fields[i][0]
        if status in "RC":
            files.append(CommitFile(status, fields[i + 2], fields[i + 1]))
            i += 3
        else:
            files.append(CommitFile(status, fields[i + 1]))
            i += 2
    return tuple(files)
