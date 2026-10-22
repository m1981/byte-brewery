"""A rootdir with throwaway repositories and an AppModel wired to test doubles."""

from __future__ import annotations

from pathlib import Path

from conftest import GIT_ENV, Repo
from fakes import FakeDiffTool, ManualWorker

from vcs_lite.app.model import AppModel
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.settings import Settings


class World:
    """A rootdir with repositories, plus the model wired to fakes."""

    def __init__(self, tmp_path: Path):
        self.root = tmp_path / "PycharmProjects"
        self.root.mkdir()
        self.git = GitCli(env=GIT_ENV)
        self.worker = ManualWorker()
        self.tool = FakeDiffTool()
        self.questions: list[str] = []
        self.answer = True
        self.model: AppModel | None = None
        self.clock = None  # None: the model uses the real clock
        self.save_settings = None  # None: settings are not saved

    def repo(self, name: str) -> Repo:
        r = Repo(self.root / name)
        r.path.mkdir()
        r.git("init", "-q", "-b", "main")
        r.write("README.md", "x\n")
        r.commit("init")
        return r

    def start(self, *names: str) -> AppModel:
        settings = Settings(rootdir=str(self.root), repos=names)
        extra = {"clock": self.clock} if self.clock else {}
        if self.save_settings:
            extra["save_settings"] = self.save_settings
        self.model = AppModel(settings, git=self.git, diff_tool=self.tool, worker=self.worker, confirm=self._confirm, **extra)
        self.model.refresh_all()
        self.worker.settle()
        return self.model

    def _confirm(self, title: str, message: str) -> bool:
        self.questions.append((title, message))
        return self.answer

    def select(self, name: str) -> AppModel:
        self.model.select(name)
        self.worker.settle()
        return self.model
