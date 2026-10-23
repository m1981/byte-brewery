"""The default browser that macOS names, and files shown in it (DES-VCS-060, DEC-VCS-101).

Images and PDFs open as the files themselves (DEC-VCS-100); vcs-lite never names a browser on its own, so a
change of the default in macOS applies at once. macOS answers in about 0.05 s (OBS-VCS-013).

Trace: DES-VCS-060, REQ-VCS-034, DEC-VCS-100, DEC-VCS-101
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

ASK_MACOS = ('ObjC.import("AppKit"); '
             '$.NSWorkspace.sharedWorkspace.URLForApplicationToOpenURL($.NSURL.URLWithString("https://example.invalid"))'
             '.path.js')

Run = Callable[..., subprocess.CompletedProcess]


def default_browser(run: Run = subprocess.run) -> str | None:
    """The application macOS opens web pages with, or None when it cannot say."""
    try:
        result = run(["osascript", "-l", "JavaScript", "-e", ASK_MACOS], capture_output=True, text=True, timeout=5,
                     check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (result.stdout.strip() or None) if result.returncode == 0 else None


def show(path: Path, *, browser: Callable[[], str | None] = default_browser, run: Run = subprocess.run) -> None:
    """The file in the default browser; without one, in its default application."""
    app = browser()
    argv = ["open", "-a", app, str(path)] if app else ["open", str(path)]
    result = run(argv, capture_output=True, text=True, timeout=10, check=False)
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or f"open zakończył się kodem {result.returncode}")
