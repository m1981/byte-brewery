"""Files shown in the default browser that macOS names (DES-VCS-060, DEC-VCS-101, OBS-VCS-013)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vcs_lite.core.browser import default_browser, show


class Runner:
    """Records commands and answers like subprocess.run."""

    def __init__(self, stdout: str = "", returncode: int = 0, stderr: str = ""):
        self.calls: list[list[str]] = []
        self.answer = (stdout, returncode, stderr)

    def __call__(self, argv, **_options):
        self.calls.append(list(argv))
        stdout, code, stderr = self.answer
        return subprocess.CompletedProcess(argv, code, stdout, stderr)


def test_des_vcs_060_default_browser_is_asked_from_macos():
    run = Runner("/Applications/Google Chrome.app\n")
    assert default_browser(run) == "/Applications/Google Chrome.app"
    assert run.calls[0][:3] == ["osascript", "-l", "JavaScript"] and "URLForApplicationToOpenURL" in run.calls[0][-1]


def test_des_vcs_060_no_answer_means_no_browser():
    assert default_browser(Runner("", 1, "error")) is None
    assert default_browser(Runner("\n")) is None


def test_des_vcs_060_show_opens_the_file_in_that_browser():
    run = Runner()
    show(Path("/r/logo.png"), browser=lambda: "/Applications/Safari.app", run=run)
    assert run.calls == [["open", "-a", "/Applications/Safari.app", "/r/logo.png"]]


def test_des_vcs_060_without_a_browser_the_default_application_opens_it():
    run = Runner()
    show(Path("/r/opis.pdf"), browser=lambda: None, run=run)
    assert run.calls == [["open", "/r/opis.pdf"]]


def test_des_vcs_060_a_refusal_is_an_error_with_the_message():
    with pytest.raises(OSError, match="nie istnieje"):
        show(Path("/r/x.png"), browser=lambda: None, run=Runner("", 1, "plik nie istnieje"))
