"""Operations on one repository: status, diff sides, stage, unstage, commit, push, pull.

Trace: DES-VCS-007, DES-VCS-046, REQ-VCS-027, DES-VCS-048, REQ-VCS-030, DES-VCS-011, DES-VCS-012, DES-VCS-013, DES-VCS-014, DES-VCS-015, DES-VCS-044, DES-VCS-045, REQ-VCS-005, REQ-VCS-024, REQ-VCS-026, REQ-VCS-009, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-017, REQ-VCS-020
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from vcs_lite.core.difftool import Content
from vcs_lite.core.gitcli import GitCli, GitResult
from vcs_lite.core.status import STATUS_ARGS, FileChange, RepoStatus, Side, parse_status


# Lines that only a merge leaves behind. A bare "=======" is not one of them: Markdown uses it to
# underline headings, and a resolved file never keeps "<<<<<<<" or ">>>>>>>" (DES-VCS-044).
CONFLICT_MARKERS = (b"<<<<<<<", b">>>>>>>", b"|||||||")


def ignore_pattern(path: str, *, folder: bool = False) -> str:
    """Anchored at the repository root, so "#" and "!" never start the line; git's wildcards and
    trailing spaces get a backslash (DES-VCS-048)."""
    escaped = "".join("\\" + ch if ch in "\\*?[]" else ch for ch in path)
    kept = escaped.rstrip(" ")
    return "/" + kept + "\\ " * (len(escaped) - len(kept)) + ("/" if folder else "")


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
        status = parse_status(self._read(*STATUS_ARGS).stdout)
        return replace(status, merging=(self.git_dir() / "MERGE_HEAD").exists())

    def git_dir(self) -> Path:
        """The git directory without calling git: `.git` itself, or where a `.git` file points (worktree)."""
        dot_git = self.path / ".git"
        if dot_git.is_file():
            return self.path / dot_git.read_text(encoding="utf-8").partition("gitdir:")[2].strip()
        return dot_git

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

    def ignore(self, files: list[str], folders: dict[str, list[str]]) -> GitResult:
        """Append patterns to the root .gitignore (REQ-VCS-030). `folders` maps a folder to its unversioned
        files: a folder without tracked files is ignored whole (with its subfolders), otherwise file by file."""
        patterns, whole = [], []
        for folder, members in folders.items():
            if self._read("ls-files", "-z", "--", f"{folder}/").stdout:
                patterns += [ignore_pattern(p) for p in members]
            else:
                patterns.append(ignore_pattern(folder, folder=True))
                whole.append(f"{folder}/")
        patterns += [ignore_pattern(f) for f in files if not f.startswith(tuple(whole))]
        path = self.path / ".gitignore"
        old = path.read_bytes() if path.exists() else b""
        newline = b"\r\n" if b"\r\n" in old else b"\n"
        present = {line.rstrip(b"\r") for line in old.split(b"\n")}
        new = [p for p in dict.fromkeys(pattern.encode("utf-8") for pattern in patterns) if p not in present]
        if new:
            lead = newline if old and not old.endswith(b"\n") else b""
            with path.open("ab") as out:  # fails before writing when the file is read-only
                out.write(lead + newline.join(new) + newline)
        return GitResult(("gitignore",), 0, b"", "")

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
