"""Pages in the browser as diff tools: a short process writes the page and opens the default browser.

They plug into the same port as any other diff tool (DES-VCS-036), so the sides, their temp files and the
clean-up stay the ones of `difftool.compare`. `MarkdownDiffTool` runs `mdpage` (images load from the folder of
a working-copy file, DEC-VCS-081); `TextDiffTool` runs `textpage`, the side-by-side diff (DEC-VCS-103).
`read=True` makes either a reader of a file without changes, and `at_line` scrolls its page to a line.

Trace: DES-VCS-049, DES-VCS-050, DES-VCS-056, DES-VCS-059, DES-VCS-036, REQ-VCS-023, REQ-VCS-031, REQ-VCS-032, REQ-VCS-033, REQ-VCS-034, DEC-VCS-080, DEC-VCS-081, DEC-VCS-102
"""

from __future__ import annotations

import copy
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from vcs_lite.core.difftool import CommandTemplateDiffTool, ExternalDiffTool, is_temporary_side


class DocumentReader(ExternalDiffTool, Protocol):
    """Shows one document; `at_line` gives the same reader scrolling to a line of the file (DES-VCS-056)."""

    def at_line(self, line: int) -> ExternalDiffTool: ...


def open_with_macos(command: list[str]) -> None:
    """`open` and `open -R` (DEC-VCS-090); a refusal becomes an error with macOS's own message."""
    result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or f"{command[0]} zakończył się kodem {result.returncode}")


class PageTool(CommandTemplateDiffTool):
    """`python -m <module> <left> <right> <titles>` with the options every page process takes (DES-VCS-058)."""

    MODULE = ""

    def __init__(self, python: str = sys.executable, *, open_browser: bool = True, read: bool = False,
                 theme: Callable[[], str] = lambda: "system"):
        """`theme` is read at every opening, so a change in the settings applies to the next page."""
        argv = [python, "-m", self.MODULE, "{left}", "{right}", "{left_title}", "{right_title}"]
        argv += [] if open_browser else ["--no-open"]
        super().__init__(argv + (["--read"] if read else []))
        self._theme = theme
        self._line: int | None = None

    def at_line(self, line: int) -> PageTool:
        """The same reader, scrolling its page to a line of the file (a search match, DES-VCS-056)."""
        reader = copy.copy(self)
        reader._line = line
        return reader

    def command(self, left: Path, right: Path, left_title: str, right_title: str) -> list[str]:
        argv = super().command(left, right, left_title, right_title) + self._options(left, right)
        if (theme := self._theme()) != "system":
            argv += ["--theme", theme]
        if self._line is not None:
            argv += ["--line", str(self._line)]
        return argv

    def _options(self, left: Path, right: Path) -> list[str]:
        """Options of one page module; none by default."""
        return []


class MarkdownDiffTool(PageTool):
    MODULE = "vcs_lite.core.mdpage"

    def _options(self, left: Path, right: Path) -> list[str]:
        """Images of a working-copy file load from its folder; temp sides from git have none."""
        return [] if is_temporary_side(right) else ["--base", str(right.parent)]


class TextDiffTool(PageTool):
    MODULE = "vcs_lite.core.textpage"
