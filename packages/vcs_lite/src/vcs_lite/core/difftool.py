"""External diff tool behind a port, so Beyond Compare can be swapped for any CLI tool.

Trace: DES-VCS-036, DES-VCS-037, DES-VCS-038, DES-VCS-039, REQ-VCS-023
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Union

# DES-VCS-037. The -title1/-title2 syntax of BC4 on macOS still has to be checked by hand.
BEYOND_COMPARE = (
    "/Applications/Beyond Compare.app/Contents/MacOS/bcomp",
    "{left}",
    "{right}",
    "-title1={left_title}",
    "-title2={right_title}",
)

# bytes: content from git (HEAD, index or an empty side), shown from a read-only temp file.
# Path: the working-tree file itself, editable in the tool (DEC-VCS-039).
Content = Union[bytes, Path]


_PLACEHOLDER = re.compile(r"\{(?:left|right|left_title|right_title)\}")


class DiffToolError(Exception):
    """The tool could not be started."""


@dataclass(frozen=True)
class DiffResult:
    returncode: int
    stderr: str

    @property
    def failed(self) -> bool:
        # Diff tools exit non-zero when files differ, so only a non-zero code with stderr is an error.
        return self.returncode != 0 and bool(self.stderr.strip())


class RunningDiff(Protocol):
    def wait(self) -> DiffResult: ...


class ExternalDiffTool(Protocol):
    def open(self, left: Path, right: Path, left_title: str, right_title: str) -> RunningDiff: ...


class _Process:
    def __init__(self, proc: subprocess.Popen):
        self._proc = proc

    def wait(self) -> DiffResult:
        _, err = self._proc.communicate()
        return DiffResult(self._proc.returncode, err.decode("utf-8", errors="replace"))


class CommandTemplateDiffTool:
    """Runs a command given as an argument list with {left}, {right}, {left_title}, {right_title}."""

    def __init__(self, argv: Sequence[str] = BEYOND_COMPARE):
        self.argv = list(argv)

    def command(self, left: Path, right: Path, left_title: str, right_title: str) -> list[str]:
        values = {"{left}": str(left), "{right}": str(right), "{left_title}": left_title, "{right_title}": right_title}
        # One pass per argument, so braces inside titles or paths stay literal.
        return [_PLACEHOLDER.sub(lambda m: values[m.group(0)], arg) for arg in self.argv]

    def open(self, left: Path, right: Path, left_title: str, right_title: str) -> RunningDiff:
        argv = self.command(left, right, left_title, right_title)
        try:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as exc:
            raise DiffToolError(f"Nie można uruchomić narzędzia diffu {argv[0]}: {exc.strerror or exc}") from exc
        return _Process(proc)


def _materialize(content: Content, folder: Path, name: str) -> Path:
    if isinstance(content, Path):
        return content
    folder.mkdir()
    path = folder / name
    path.write_bytes(content)
    path.chmod(0o444)
    return path


def compare(tool: ExternalDiffTool, left: Content, right: Content, *, name: str,
            left_title: str, right_title: str) -> DiffResult:
    """Open both sides in the tool, wait until its window closes, then remove the temp files."""
    tmp = Path(tempfile.mkdtemp(prefix="vcs-lite-"))
    try:
        left_path = _materialize(left, tmp / "left", name)
        right_path = _materialize(right, tmp / "right", name)
        return tool.open(left_path, right_path, left_title, right_title).wait()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
