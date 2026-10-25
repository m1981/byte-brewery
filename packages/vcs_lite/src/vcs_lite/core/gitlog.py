"""`git log` as the history reader (DES-VCS-065).

`--all` is not used: it also lists the commits of `refs/stash` and `refs/notes` (OBS-VCS-015). HEAD is
named only when it exists, because a fresh repository makes git fail on it (H-04). `--grep` and `--author`
together keep only commits matching both, so the filter runs them apart and joins the results (H-44).

Trace: DES-VCS-065, REQ-VCS-037, REQ-VCS-039, REQ-VCS-040, OBS-VCS-015, DEC-VCS-120
"""

from __future__ import annotations

import re
from pathlib import Path

from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.log import (FORMAT, Commit, CommitDetails, LogPage, LogQuery, Scope, parse_log,
                               parse_name_status)
from vcs_lite.core.repo import GitError, GitRepo

PAGE = 500                                  # commits read at once (H-06), also the filter's limit (H-44)
HASH_PREFIX = re.compile(r"[0-9a-fA-F]{4,40}")
LOG = ("log", "--topo-order", "-z", "--decorate=full", f"--format={FORMAT}")


class GitLog:
    def __init__(self, git: GitCli):
        self._git = git

    def _read(self, repo: Path, *args: str) -> bytes:
        result = self._git.run(repo, *args, read_only=True)
        if not result.ok:
            raise GitError(result)
        return result.stdout

    def _has_head(self, repo: Path) -> bool:
        return self._git.run(repo, "rev-parse", "--verify", "--quiet", "HEAD", read_only=True).ok

    def _revisions(self, repo: Path, scope: Scope) -> list[str]:
        head = ["HEAD"] if self._has_head(repo) else []
        return ["--branches", "--remotes", "--tags", *head] if scope is Scope.ALL else head

    def page(self, repo: Path, query: LogQuery, skip: int) -> LogPage:
        """Up to PAGE commits after `skip`; one more is asked for to know whether others follow."""
        revisions = self._revisions(repo, query.scope)
        if not revisions:
            return LogPage((), False)
        if query.filtered:
            return self._filtered(repo, query.phrase, revisions)
        commits = parse_log(self._read(repo, *LOG, f"--max-count={PAGE + 1}", f"--skip={skip}", *revisions, "--"))
        return LogPage(tuple(commits[:PAGE]), len(commits) > PAGE)

    def _filtered(self, repo: Path, phrase: str, revisions: list[str]) -> LogPage:
        found: dict[str, Commit] = {}
        for pattern in (f"--grep={phrase}", f"--author={phrase}"):
            for commit in parse_log(self._read(repo, *LOG, f"--max-count={PAGE + 1}", "-i", "-F", pattern,
                                               *revisions, "--")):
                found.setdefault(commit.hash, commit)
        if HASH_PREFIX.fullmatch(phrase):
            target = self._git.run(repo, "rev-parse", "--verify", "--quiet", f"{phrase}^{{commit}}", read_only=True)
            if target.ok:
                for commit in parse_log(self._read(repo, *LOG, "--max-count=1", target.stdout.decode().strip(), "--")):
                    found.setdefault(commit.hash, commit)
        commits = sorted(found.values(), key=lambda c: c.time, reverse=True)
        return LogPage(tuple(commits[:PAGE]), len(commits) > PAGE)

    def count(self, repo: Path, query: LogQuery) -> int:
        revisions = self._revisions(repo, query.scope)
        if not revisions:
            return 0
        return int(self._read(repo, "rev-list", "--count", *revisions, "--").decode().strip() or 0)

    def unpushed(self, repo: Path) -> set[str]:
        """Commits of the current branch that its upstream does not have; none without an upstream (H-10)."""
        result = self._git.run(repo, "rev-list", "@{upstream}..HEAD", "--", read_only=True)
        return set(result.stdout.decode().split()) if result.ok else set()

    def details(self, repo: Path, commit: Commit) -> CommitDetails:
        """The whole message and the files: a merge against its first parent, a root as all added (H-45)."""
        message = self._read(repo, "show", "-s", "--format=%B", commit.hash).decode("utf-8", errors="replace")
        body = message.strip().partition("\n")[2].strip()
        sides = [commit.parents[0], commit.hash] if commit.parents else ["--root", commit.hash]
        files = self._read(repo, "diff-tree", "-r", "-z", "-M", "--name-status", "--no-commit-id", *sides, "--")
        return CommitDetails(commit, body, parse_name_status(files))

    def remote_url(self, repo: Path) -> str | None:
        """The remote's address as https, for the commit's address (REQ-VCS-035, H-47); None without one."""
        try:
            return GitRepo(repo, self._git).remote_url()
        except GitError:
            return None
