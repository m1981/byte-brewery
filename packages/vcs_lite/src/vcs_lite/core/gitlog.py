"""`git log` as the history reader (DES-VCS-065).

`--all` is not used: it also lists the commits of `refs/stash` and `refs/notes` (OBS-VCS-015). HEAD is
named only when it exists, because a fresh repository makes git fail on it (H-04). `--grep` and `--author`
together keep only commits matching both, so the filter runs them apart and joins the results (H-44).

Trace: DES-VCS-079, REQ-VCS-040, DES-VCS-065, DES-VCS-071, REQ-VCS-041, REQ-VCS-037, REQ-VCS-039, REQ-VCS-040, OBS-VCS-015, DEC-VCS-120
"""

from __future__ import annotations

import re
from pathlib import Path

from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.gitdetails import parse_numstat
from vcs_lite.core.log import (FORMAT, Commit, CommitDetails, LogPage, LogQuery, Scope, parse_log,
                               parse_name_status)
from vcs_lite.core.repo import GitError, GitRepo

PAGE = 500                                  # commits read at once (H-06), also the filter's limit (H-44)
PATH_LIMIT = 5000                           # a path's history is read at once, no pages (H-54)
RECORD = "\x1e"                             # starts each commit when names of files follow it
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
        if query.path:
            return self._path_page(repo, query, revisions)
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

    def _path_page(self, repo: Path, query: LogQuery, revisions: list[str]) -> LogPage:
        """A file with its earlier names and its change in each commit, or a folder (H-50, H-51); with
        text, only commits that also match it (H-53)."""
        if query.folder:
            spec, follow = [f":(literal){query.path.rstrip('/')}/"], []
        else:
            spec, follow = [f":(literal){query.path}"], ["--follow", "--name-status"]
        raw = self._read(repo, *LOG[:-1], f"--format={RECORD}{FORMAT}", *follow, f"--max-count={PATH_LIMIT + 1}",
                         *revisions, "--", *spec)
        commits, paths = [], {}
        for record in filter(None, raw.split(RECORD.encode())):
            header, _, names = record.partition(b"\0")
            commit = parse_log(header)[0]
            commits.append(commit)
            changes = parse_name_status(names.lstrip(b"\n"))
            if changes:
                paths[commit.hash] = changes[0]
        if query.filtered:
            # over the whole repository: with --grep git skips the commit of a rename and stops following
            matching = self._matching(repo, query.phrase, revisions)
            commits = [c for c in commits if c.hash in matching or self._hash_matches(c, query.phrase)]
        return LogPage(tuple(commits[:PATH_LIMIT]), False, paths)

    def _matching(self, repo: Path, phrase: str, revisions: list[str]) -> set[str]:
        found = set()
        for pattern in (f"--grep={phrase}", f"--author={phrase}"):
            found |= set(self._read(repo, "log", "--format=%H", "-i", "-F", pattern, *revisions, "--").decode().split())
        return found

    @staticmethod
    def _hash_matches(commit: Commit, phrase: str) -> bool:
        return bool(HASH_PREFIX.fullmatch(phrase)) and commit.hash.startswith(phrase.lower())

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
        try:
            raw = self._read(repo, "diff-tree", "-r", "-z", "-M", "--numstat", "--no-commit-id",
                             "--no-ext-diff", "--no-textconv", *sides, "--")
            lines = parse_numstat(raw)
        except (GitError, ValueError):
            lines = {}  # keep the file list; missing counts are displayed as unknown
        return CommitDetails(commit, body, parse_name_status(files), lines)

    def commit_totals(self, repo: Path, commits: tuple[Commit, ...]) -> dict[str, tuple[int, int]]:
        """One Git process for all commits on a page, compared with the first parent."""
        if not commits:
            return {}
        result = self._git.run(repo, "log", "--no-walk", "--first-parent", "-m", "-z",
                               "--format=%x1e%H", "--numstat", "--no-ext-diff", "--no-textconv",
                               *(c.hash for c in commits), "--", read_only=True)
        if not result.ok:
            return {}
        totals = {}
        for record in result.stdout.split(b"\x1e"):
            hash_, sep, data = record.partition(b"\0")
            if not sep or len(hash_) != 40:
                continue
            try:
                values = parse_numstat(data.lstrip(b"\n"))
            except ValueError:
                continue
            totals[hash_.decode()] = (sum(v.added for v in values.values()),
                                      sum(v.removed for v in values.values()))
        return totals

    def remote_url(self, repo: Path) -> str | None:
        """The remote's address as https, for the commit's address (REQ-VCS-035, H-47); None without one."""
        try:
            return GitRepo(repo, self._git).remote_url()
        except GitError:
            return None
