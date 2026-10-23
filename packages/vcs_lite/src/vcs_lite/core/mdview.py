"""The rendered Markdown diff as an external diff tool: a short process writes the page and opens the browser.

It plugs into the same port as Beyond Compare (DES-VCS-036), so the sides, their temp files and the clean-up
stay the ones of `difftool.compare`. Images load from the folder of a working-copy file; the temp sides of
HEAD and the index have none (DEC-VCS-081).

Trace: DES-VCS-049, DES-VCS-050, DES-VCS-036, REQ-VCS-031, REQ-VCS-032, DEC-VCS-080, DEC-VCS-081
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from vcs_lite.core.difftool import CommandTemplateDiffTool, is_temporary_side


def open_with_macos(command: list[str]) -> None:
    """`open` and `open -R` (DEC-VCS-090); a refusal becomes an error with macOS's own message."""
    result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or f"{command[0]} zakończył się kodem {result.returncode}")


class MarkdownDiffTool(CommandTemplateDiffTool):
    def __init__(self, python: str = sys.executable, *, open_browser: bool = True, read: bool = False,
                 theme: Callable[[], str] = lambda: "system"):
        """`theme` is read at every opening, so a change in the settings applies to the next page.
        `read` shows a file without changes as a plain document (REQ-VCS-032)."""
        argv = [python, "-m", "vcs_lite.core.mdpage", "{left}", "{right}", "{left_title}", "{right_title}"]
        argv += [] if open_browser else ["--no-open"]
        super().__init__(argv + (["--read"] if read else []))
        self._theme = theme

    def command(self, left: Path, right: Path, left_title: str, right_title: str) -> list[str]:
        argv = super().command(left, right, left_title, right_title)
        if not is_temporary_side(right):
            argv += ["--base", str(right.parent)]
        if (theme := self._theme()) != "system":
            argv += ["--theme", theme]
        return argv
