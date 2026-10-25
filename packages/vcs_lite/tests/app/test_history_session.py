"""State of the history panel without Tk (DES-VCS-067, rules H-04, H-06, H-10–H-12, H-41–H-44, H-48, H-49)."""

from __future__ import annotations

from datetime import datetime

import pytest
from conftest import Repo
from world import World

from vcs_lite.app.history import DEBOUNCE_MS, HistorySession, commits_label, date_label
from vcs_lite.core import gitlog
from vcs_lite.core.gitcli import GitResult
from vcs_lite.core.log import LogQuery, Scope
from vcs_lite.core.repo import GitError


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


def commit(repo: Repo, message: str, author: str = "Test <t@x>") -> str:
    repo.write(f"{message}.txt", message + "\n")
    repo.git("add", "-A")
    repo.git("commit", "-q", "-m", message, f"--author={author}")
    return repo.git("rev-parse", "HEAD").decode().strip()


def subjects(session: HistorySession) -> list[str]:
    return [c.subject for c in session.commits]


def started(world: World, *names: str, select: str | None = None) -> HistorySession:
    world.start(*names)
    if select:
        world.select(select)
    session = world.history_session()
    world.worker.settle()
    return session


# ---------- reading and reading again (H-41, H-42) ----------

def test_req_vcs_037_the_selected_repository_is_read_with_its_graph_count_and_unpushed(world):
    alpha = world.repo("alpha")
    commit(alpha, "drugi")
    session = started(world, "alpha", select="alpha")
    assert subjects(session) == ["drugi", "init"] and len(session.rows) == 2
    assert session.count == 2 and session.unpushed == set() and session.selected == 0
    assert session.details is not None and session.details.commit.subject == "drugi"


def test_at_vcs_058_a_new_commit_reads_again_and_keeps_the_selection_an_amend_does_not(world):
    alpha = world.repo("alpha")
    commit(alpha, "drugi")
    session = started(world, "alpha", select="alpha")
    session.select(1); world.worker.settle()                    # "init"
    commit(alpha, "trzeci")
    world.model.refresh("alpha"); world.worker.settle()
    assert subjects(session) == ["trzeci", "drugi", "init"] and session.selected_commit.subject == "init"
    session.select(0); world.worker.settle()
    alpha.git("commit", "-q", "--amend", "-m", "trzeci poprawiony")
    world.model.refresh("alpha"); world.worker.settle()
    assert session.selected == 0 and session.selected_commit.subject == "trzeci poprawiony"


def test_at_vcs_058_reading_history_never_holds_the_repository(world):
    world.repo("alpha")
    world.start("alpha"); world.select("alpha")
    session = world.history_session()
    session.set_scope(Scope.CURRENT)
    assert any(key.startswith("history:") for key, _, _ in world.worker.queued)
    assert not world.worker.busy("alpha")                       # commit, pull and stage stay possible (H-43)


def test_des_vcs_067_a_result_for_an_older_selection_is_dropped(world):
    commit(world.repo("alpha"), "z alpha")
    commit(world.repo("beta"), "z beta")
    world.start("alpha", "beta")
    session = world.history_session()
    world.model.select("alpha")
    world.model.select("beta")                                  # before alpha's history came back
    world.worker.settle()
    assert subjects(session) == ["z beta", "init"]


# ---------- states without a list (H-04, H-11, H-12) ----------

def test_at_vcs_058_a_fresh_repository_and_one_that_is_gone(world):
    fresh = Repo(world.root / "fresh"); fresh.path.mkdir(); fresh.git("init", "-q", "-b", "main")
    session = started(world, "fresh", "gone", select="fresh")
    assert session.commits == [] and session.placeholder == "Repo nie ma jeszcze commitów."
    world.select("gone"); world.worker.settle()
    assert session.placeholder == "Repo niedostępne." and session.commits == []


def test_des_vcs_067_a_git_error_replaces_the_list(world):
    world.repo("alpha")
    world.start("alpha"); world.select("alpha")

    class Failing:
        def page(self, repo, query, skip):
            raise GitError(GitResult(("log",), 128, b"", "fatal: zepsute repo"))
    session = HistorySession(Failing(), world.worker, later=world.timers.later, model=world.model)
    world.worker.settle()
    assert session.commits == [] and session.placeholder == "Nie udało się wczytać historii: fatal: zepsute repo"


# ---------- filter, scope and pages (H-03, H-06, H-44) ----------

def test_at_vcs_059_the_filter_waits_for_a_pause_and_shows_a_flat_list(world):
    alpha = world.repo("alpha")
    commit(alpha, "fix parser", "Ola <o@x>"); commit(alpha, "docs", "Ola <o@x>"); commit(alpha, "fix ui", "Michal <m@x>")
    session = started(world, "alpha", select="alpha")
    session.set_text("ola")
    world.worker.settle()
    assert len(session.commits) == 4                            # nothing yet: typing goes on
    world.timers.advance(DEBOUNCE_MS); world.worker.settle()
    assert subjects(session) == ["docs", "fix parser"] and session.query.filtered
    assert session.rows == []                                    # no lines while filtering (H-34)
    session.set_text("brak takiego")
    world.timers.advance(DEBOUNCE_MS); world.worker.settle()
    assert session.placeholder == "Brak commitów pasujących do „brak takiego”."
    session.set_text("")
    world.timers.advance(DEBOUNCE_MS); world.worker.settle()
    assert len(session.commits) == 4 and len(session.rows) == 4


def test_req_vcs_039_the_scope_reads_again_at_once(world):
    alpha = world.repo("alpha")
    alpha.git("checkout", "-q", "-b", "feature"); commit(alpha, "na feature")
    alpha.git("checkout", "-q", "main")
    session = started(world, "alpha", select="alpha")
    assert "na feature" in subjects(session)
    session.set_scope(Scope.CURRENT); world.worker.settle()
    assert subjects(session) == ["init"] and session.query == LogQuery(scope=Scope.CURRENT)


def test_at_vcs_055_more_reads_the_next_page_and_extends_the_graph(world, monkeypatch):
    alpha = world.repo("alpha")
    for i in range(5):
        commit(alpha, f"c{i}")
    monkeypatch.setattr(gitlog, "PAGE", 4)
    session = started(world, "alpha", select="alpha")
    assert len(session.commits) == 4 and session.more
    first_rows = list(session.rows)
    session.load_more(); session.load_more()                     # a second call while reading does nothing
    world.worker.settle()
    assert len(session.commits) == 6 and not session.more and session.rows[:4] == first_rows
    assert session.count == 6


# ---------- labels (H-48, H-49) ----------

def test_des_vcs_067_dates_and_counts_in_polish():
    now = datetime(2026, 10, 25, 22, 0)
    assert date_label(datetime(2026, 10, 25, 14, 5).timestamp(), now) == "dziś 14:05"
    assert date_label(datetime(2026, 10, 24, 18, 22).timestamp(), now) == "wczoraj 18:22"
    assert date_label(datetime(2026, 10, 23, 9, 0).timestamp(), now) == "23.10.2026"
    assert [commits_label(n) for n in (1, 3, 5, 12, 22, 1248)] == [
        "1 commit", "3 commity", "5 commitów", "12 commitów", "22 commity", "1\u00a0248 commitów"]


# ---------- the commit's address (H-47) ----------

def test_des_vcs_067_the_commit_address_on_github_gitlab_and_bitbucket():
    from vcs_lite.app.history import commit_web_url
    h = "a" * 40
    assert commit_web_url("https://github.com/m1981/app.git", h) == f"https://github.com/m1981/app/commit/{h}"
    assert commit_web_url("https://gitlab.firma.pl/zespol/app", h) == f"https://gitlab.firma.pl/zespol/app/commit/{h}"
    assert commit_web_url("https://bitbucket.org/zespol/app.git", h) == f"https://bitbucket.org/zespol/app/commits/{h}"
    assert commit_web_url("https://git.example.com/app.git", h) is None
    assert commit_web_url("/Users/x/remotes/app.git", h) is None and commit_web_url(None, h) is None


def test_at_vcs_060_the_session_knows_the_commit_address_from_the_remote(world):
    alpha = world.repo("alpha")
    alpha.git("remote", "add", "origin", "git@github.com:m1981/app.git")
    session = started(world, "alpha", select="alpha")
    commit_ = session.selected_commit
    assert session.commit_url(commit_) == f"https://github.com/m1981/app/commit/{commit_.hash}"


# ---------- the history of a path (H-50–H-56) ----------

def test_at_vcs_061_show_path_narrows_the_list_and_clearing_brings_the_graph_back(world):
    alpha = world.repo("alpha")
    commit(alpha, "jeden"); commit(alpha, "dwa")
    session = started(world, "alpha", select="alpha")
    session.show_path("jeden.txt", folder=False); world.worker.settle()
    assert subjects(session) == ["jeden"] and session.rows == [] and session.query.path == "jeden.txt"
    assert session.path_change(session.commits[0]).path == "jeden.txt"
    session.show_path("brak.txt", folder=False); world.worker.settle()
    assert session.placeholder == "Brak commitów dla brak.txt."
    session.clear_path(); world.worker.settle()
    assert len(session.commits) == 3 and len(session.rows) == 3


def test_at_vcs_062_another_repository_drops_the_path_and_a_folder_opens_no_diff(world):
    alpha = world.repo("alpha")
    alpha.write("docs/a.md", "a\n"); alpha.commit("docs")
    world.repo("beta")
    session = started(world, "alpha", "beta", select="alpha")
    session.show_path("docs", folder=True); world.worker.settle()
    assert subjects(session) == ["docs"] and session.path_change(session.commits[0]) is None
    world.select("beta"); world.worker.settle()
    assert session.query.path == "" and subjects(session) == ["init"]
