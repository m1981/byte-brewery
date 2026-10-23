"""Searching in files, as values without I/O: the query, its file mask, matches in a line, clipped lines, results.

`match_spans` is the one place that decides whether a line matches and where, so filtering and highlighting
never disagree. Word boundaries are Unicode-aware: `git grep -w` treats Polish letters as separators and finds
"w" inside "żółw" (DEC-VCS-093). The port `TextSearcher` lets another engine (e.g. an index) replace git grep.

Trace: DES-VCS-052, REQ-VCS-033, DEC-VCS-093
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Protocol

Span = tuple[int, int]

CLIP_LIMIT = 300   # characters kept of a long line (e.g. minified code), so 500 matches stay small
CLIP_LEAD = 40     # characters kept before the first match of a clipped line
MASK_SEPARATORS = re.compile(r"[,;\s]+")
GLOB_SPECIAL = re.compile(r"([*?\[\\])")


@dataclass(frozen=True)
class SearchQuery:
    text: str
    case_sensitive: bool = False
    whole_word: bool = False
    mask: str = ""   # extensions as typed: "md, py", "*.md; *.py" or ".md"

    @property
    def active(self) -> bool:
        """A phrase worth searching for; blank text shows the hint instead."""
        return bool(self.text.strip())

    @cached_property
    def extensions(self) -> tuple[str, ...]:
        tokens = (token.lstrip("*.").lower() for token in MASK_SEPARATORS.split(self.mask))
        return tuple(dict.fromkeys(token for token in tokens if token))

    @property
    def pathspecs(self) -> tuple[str, ...]:
        """git pathspecs of the mask: in every folder, the case of the extension ignored (README.MD counts)."""
        return tuple(":(glob,icase)**/*." + GLOB_SPECIAL.sub(r"\\\1", ext) for ext in self.extensions)

    @cached_property
    def pattern(self) -> re.Pattern[str]:
        body = re.escape(self.text)
        if self.whole_word and self.text:
            # A boundary only on a side where the phrase has a word character, like PyCharm: "foo(" still works.
            body = ("(?<!\\w)" if re.match(r"\w", self.text) else "") + body
            body += "(?!\\w)" if re.search(r"\w$", self.text) else ""
        return re.compile(body, 0 if self.case_sensitive else re.IGNORECASE)


def match_spans(text: str, query: SearchQuery) -> list[Span]:
    """Where the query matches in one line; empty when it does not."""
    if not query.text:
        return []
    return [m.span() for m in query.pattern.finditer(text)]


def clip_line(text: str, spans: list[Span]) -> tuple[str, list[Span], bool, bool]:
    """The part of a line worth showing: without its indentation and, when long, around the first match.
    Returns the text, the spans inside it, and whether the start and the end were cut."""
    indent = len(text) - len(text.lstrip())
    text, spans = text[indent:], [(a - indent, b - indent) for a, b in spans if b > indent]
    if len(text) <= CLIP_LIMIT:
        return text, spans, False, False
    first = spans[0][0] if spans else 0
    start = max(0, min(first - CLIP_LEAD, len(text) - CLIP_LIMIT))
    end = start + CLIP_LIMIT
    inside = [(max(a, start) - start, min(b, end) - start) for a, b in spans if a < end and b > start]
    return text[start:end], inside, start > 0, end < len(text)


@dataclass(frozen=True)
class Match:
    path: str                     # relative to the repository root
    line: int                     # 1-based
    text: str                     # the shown part of the line (clip_line)
    spans: tuple[Span, ...]
    cut_start: bool = False
    cut_end: bool = False


@dataclass(frozen=True)
class SearchResult:
    matches: tuple[Match, ...] = ()
    truncated: bool = False       # the limit was reached; more matches exist

    @property
    def file_count(self) -> int:
        return len({m.path for m in self.matches})


class TextSearcher(Protocol):
    def search(self, repo: Path, query: SearchQuery, *, limit: int,
               cancelled: Callable[[], bool]) -> SearchResult: ...
