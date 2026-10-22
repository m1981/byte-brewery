"""Shared fixtures: throwaway git repositories isolated from the user's git config, and the one Tk root."""

from __future__ import annotations

import os
import subprocess
import tkinter as tk
from pathlib import Path

import pytest

from vcs_lite.ui.tkenv import prepare_tk

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}


class Repo:
    def __init__(self, path: Path):
        self.path = path

    def git(self, *args: str, check: bool = True) -> bytes:
        result = subprocess.run(["git", "-C", str(self.path), *args], env=GIT_ENV, capture_output=True, check=False)
        if check and result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace')}")
        return result.stdout

    def write(self, rel: str, text: str) -> None:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, message: str = "c") -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    r = Repo(tmp_path / "repo")
    r.path.mkdir()
    r.git("init", "-q", "-b", "main")
    return r


@pytest.fixture(scope="session")
def tk_root():
    """One Tk per test session, like the app: fonts cached by ui.theme belong to a single interpreter."""
    prepare_tk()
    try:
        r = tk.Tk()
    except tk.TclError as exc:  # no display, e.g. over ssh
        pytest.skip(f"Tk unavailable: {exc}")
    r.withdraw()
    yield r
    r.destroy()
