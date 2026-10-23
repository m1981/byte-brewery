"""A rootdir with throwaway repositories and an AppModel wired to test doubles."""

from __future__ import annotations

from pathlib import Path

from conftest import GIT_ENV, Repo
from fakes import FakeDiffTool, FakeTimers, ManualWorker

from vcs_lite.app.model import AppModel
from vcs_lite.app.search import SearchSession
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.gitgrep import GitGrepSearcher
from vcs_lite.core import pagekit
from vcs_lite.core.settings import Settings


class World:
    """A rootdir with repositories, plus the model wired to fakes."""

    def __init__(self, tmp_path: Path):
        self.root = tmp_path / "PycharmProjects"
        self.root.mkdir()
        self.git = GitCli(env=GIT_ENV)
        self.worker = ManualWorker()
        self.tool = FakeDiffTool()  # the side-by-side diff page (REQ-VCS-023)
        self.md_tool = FakeDiffTool()  # the rendered Markdown diff (REQ-VCS-031)
        self.md_reader = FakeDiffTool()  # a Markdown file read without changes (REQ-VCS-032)
        self.text_reader = FakeDiffTool()  # a text file read without changes (REQ-VCS-034)
        self.external: FakeDiffTool | None = None  # the diff tool plugin, off unless a test sets it (DEC-VCS-106)
        self.browsed: list[Path] = []  # files shown in the default browser (REQ-VCS-034)
        self.copies = tmp_path / "copies"  # versions that are not on disk, kept for the browser
        self.opened: list[list[str]] = []  # commands of the macOS opener (REQ-VCS-032)
        self.questions: list[str] = []
        self.answer = True
        self.model: AppModel | None = None
        self.clock = None  # None: the model uses the real clock
        self.save_settings = None  # None: settings are not saved
        self.timers = FakeTimers()  # after() of the search window (REQ-VCS-033)

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
        self.model = AppModel(settings, git=self.git, diff_tool=self.tool, markdown_tool=self.md_tool,
                              markdown_reader=self.md_reader, text_reader=self.text_reader,
                              external_tool=self.external, browser=self.browsed.append,
                              keep_copy=lambda content, name: pagekit.keep_copy(content, name, folder=self.copies),
                              opener=self.opened.append, worker=self.worker, confirm=self._confirm, **extra)
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

    def search_session(self, searcher=None) -> SearchSession:
        """The search window's state on the selected repository, with git grep unless another searcher is given."""
        return SearchSession(searcher or GitGrepSearcher(self.git), self.worker, later=self.timers.later,
                             repo=lambda: self.model.selected_path, open_match=self.model.open_match)
