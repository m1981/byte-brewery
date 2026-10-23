"""`git grep` as the text searcher: git picks candidate lines, `match_spans` decides (DEC-VCS-093).

git knows which files are tracked, skips binary ones and searches the whole repository in hundredths of a
second, so there is no index to keep fresh. `-w` is never passed: git treats Polish letters as word
separators. Records of `-z -n` are `path NUL line NUL text`, so paths with ":" or spaces stay intact.

Trace: DES-VCS-054, REQ-VCS-033, DEC-VCS-093
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.repo import GitError
from vcs_lite.core.search import Match, SearchQuery, SearchResult, clip_line, match_spans

NO_MATCH = 1  # git grep's exit code when nothing matched


class GitGrepSearcher:
    def __init__(self, git: GitCli):
        self._git = git

    @staticmethod
    def arguments(query: SearchQuery) -> list[str]:
        case = [] if query.case_sensitive else ["-i"]
        return ["grep", "-I", "-z", "-n", "--no-color", "-F", *case, "-e", query.text, "--", *query.pathspecs]

    def search(self, repo: Path, query: SearchQuery, *, limit: int,
               cancelled: Callable[[], bool]) -> SearchResult:
        matches: list[Match] = []
        truncated = False
        with self._git.stream(repo, *self.arguments(query)) as out:
            for record in out:
                if cancelled():
                    break
                match = self._verified(record, query)
                if match is None:
                    continue
                if len(matches) == limit:
                    truncated = True
                    break
                matches.append(match)
        result = out.result
        if not result.ok and not result.stopped and result.returncode != NO_MATCH:
            raise GitError(result)
        return SearchResult(tuple(matches), truncated)

    @staticmethod
    def _verified(record: bytes, query: SearchQuery) -> Match | None:
        """A match only where match_spans agrees: git's -i and -F choose candidates, Python decides."""
        path, _, rest = record.partition(b"\0")
        number, _, raw = rest.partition(b"\0")
        text = raw.decode("utf-8", errors="replace")
        spans = match_spans(text, query)
        if not spans:
            return None
        shown, shown_spans, cut_start, cut_end = clip_line(text, spans)
        return Match(path.decode("utf-8", errors="surrogateescape"), int(number), shown, tuple(shown_spans),
                     cut_start, cut_end)
