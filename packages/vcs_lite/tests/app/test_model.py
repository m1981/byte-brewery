"""AppModel: the window's state and rules without Tk (DES-VCS-032).

Acceptance scenarios that describe buttons, the message field and the repository list are
checked here: the Tk layer only draws this state and forwards clicks and keys.
"""

from __future__ import annotations

import http.server
import json
import shutil
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest
from conftest import GIT_ENV, Repo
from world import World

from vcs_lite.app.model import AppModel, RepoState
from vcs_lite.app.worker import Worker
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.settings import Settings
from vcs_lite.core.status import Group


# ---------- fixtures ----------

@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


def paths(model: AppModel, group: Group) -> list[str]:
    return [c.path for c in model.files(group)]


def change(model: AppModel, group: Group, path: str):
    return next(c for c in model.files(group) if c.path == path)


def commit_count(repo: Repo) -> int:
    return int(repo.git("rev-list", "--count", "HEAD"))


# ---------- repository list and refreshing ----------

def test_req_vcs_002_list_shows_branch_and_number_of_changed_files(world):
    a = world.repo("alpha")
    a.write("one.py", "1\n"); a.write("two.py", "2\n")
    model = world.start("alpha")
    view = model.view("alpha")
    assert (view.branch_label, view.change_count, model.state("alpha")) == ("main", 2, RepoState.CHANGES)


def test_at_vcs_002_removed_repository_is_unavailable_and_others_keep_working(world):
    world.repo("alpha").write("a.py", "a\n")
    world.repo("beta")
    model = world.start("alpha", "beta")
    shutil.rmtree(world.root / "beta")
    model.refresh_all(); world.worker.settle()
    assert model.state("beta") is RepoState.UNAVAILABLE
    assert model.state("alpha") is RepoState.CHANGES and model.view("alpha").error is None


def test_req_vcs_015_refresh_all_updates_every_watched_repository(world):
    a, b = world.repo("alpha"), world.repo("beta")
    model = world.start("alpha", "beta")
    a.write("new.py", "n\n"); b.write("new.py", "n\n")
    model.refresh_all(); world.worker.settle()
    assert model.view("alpha").change_count == model.view("beta").change_count == 1


def test_at_vcs_003_modified_file_is_in_changes_and_not_staged(world):
    world.repo("alpha").write("README.md", "changed\n")
    model = world.start("alpha"); world.select("alpha")
    assert paths(model, Group.CHANGES) == ["README.md"] and paths(model, Group.STAGED) == []


def test_at_vcs_005_files_in_a_new_folder_are_listed_one_by_one(world):
    a = world.repo("alpha")
    a.write("new/a.txt", "1\n"); a.write("new/b.txt", "2\n")
    model = world.start("alpha"); world.select("alpha")
    assert paths(model, Group.UNVERSIONED) == ["new/a.txt", "new/b.txt"]


def test_at_vcs_006_ignored_files_are_not_shown(world):
    a = world.repo("alpha")
    a.write(".gitignore", "*.log\n"); a.commit("ignore"); a.write("debug.log", "x\n")
    model = world.start("alpha"); world.select("alpha")
    assert all("debug.log" not in paths(model, g) for g in Group)


def test_req_vcs_101_the_model_makes_no_git_calls_while_idle(world):
    world.repo("alpha")
    world.start("alpha"); world.select("alpha")
    calls = world.git.call_count
    time.sleep(0.2)
    assert world.git.call_count == calls and world.worker.queued == []


# ---------- stage, unstage, compare ----------

def test_at_vcs_029_double_click_opens_compare_and_space_stages(world):
    world.repo("alpha").write("README.md", "changed\n")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.CHANGES, "README.md")); world.worker.settle()
    assert world.tool.calls[0]["right"] == world.root / "alpha" / "README.md"
    assert paths(model, Group.CHANGES) == ["README.md"]
    model.toggle(change(model, Group.CHANGES, "README.md")); world.worker.settle()
    assert paths(model, Group.STAGED) == ["README.md"]
    model.toggle(change(model, Group.STAGED, "README.md")); world.worker.settle()
    assert paths(model, Group.STAGED) == [] and paths(model, Group.CHANGES) == ["README.md"]


def test_at_vcs_004_external_tool_gets_the_sides_of_the_chosen_group(world):
    a = world.repo("alpha")
    a.write("app.py", "return x * 2\n"); a.commit()
    a.write("app.py", "return x * 3\n"); a.git("add", "app.py"); a.write("app.py", "return x * 3\n# todo\n")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.STAGED, "app.py")); world.worker.settle()
    model.activate(change(model, Group.CHANGES, "app.py")); world.worker.settle()
    staged, changes = world.tool.calls
    assert (staged["left_bytes"], staged["right_bytes"]) == (b"return x * 2\n", b"return x * 3\n")
    assert (changes["left_bytes"], changes["right_bytes"]) == (b"return x * 3\n", b"return x * 3\n# todo\n")
    assert changes["right"] == a.path / "app.py"
    assert (staged["left_title"], changes["right_title"]) == ("app.py (HEAD)", "app.py (kopia robocza)")


def test_at_vcs_027_temp_files_disappear_and_the_repo_is_refreshed_after_closing(world):
    a = world.repo("alpha")
    a.write("README.md", "staged\n"); a.git("add", "README.md")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.STAGED, "README.md")); world.worker.settle()
    call = world.tool.calls[0]
    assert not call["left"].exists() and not call["right"].exists()
    assert world.worker.history[-1] == "alpha"  # a refresh of the repository ran after the tool closed


def test_at_vcs_028_change_saved_in_the_tool_is_visible_after_closing(world):
    a = world.repo("alpha")
    a.write("app.py", "a\n"); a.commit(); a.write("app.py", "b\n")
    world.tool.edit_right = lambda right: right.write_text(right.read_text() + "# poprawka\n")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.CHANGES, "app.py")); world.worker.settle()
    assert "# poprawka" in (a.path / "app.py").read_text()
    assert paths(model, Group.CHANGES) == ["app.py"]


def test_at_vcs_025_missing_diff_tool_gives_a_message_and_the_app_keeps_working(world, tmp_path):
    world.repo("alpha").write("README.md", "changed\n")
    settings = Settings(rootdir=str(world.root), repos=("alpha",), diff_tool=("/nonexistent/inny-diff", "{left}", "{right}"))
    model = AppModel.from_settings(settings, git=world.git, worker=world.worker, confirm=lambda q: False)
    model.select("alpha"); world.worker.settle()
    model.activate(change(model, Group.CHANGES, "README.md")); world.worker.settle()
    assert "/nonexistent/inny-diff" in model.error
    model.toggle(change(model, Group.CHANGES, "README.md")); world.worker.settle()
    assert paths(model, Group.STAGED) == ["README.md"]


def test_at_vcs_026_the_diff_tool_can_be_swapped_in_settings(world, tmp_path):
    out = tmp_path / "args.json"
    script = tmp_path / "inny_diff.py"
    script.write_text(textwrap.dedent(f"""
        import json, sys
        json.dump(sys.argv[1:], open({str(out)!r}, "w"))
    """))
    world.repo("alpha").write("README.md", "changed\n")
    settings = Settings(rootdir=str(world.root), repos=("alpha",), diff_tool=(sys.executable, str(script), "{left}", "{right}"))
    model = AppModel.from_settings(settings, git=world.git, worker=world.worker, confirm=lambda q: False)
    model.select("alpha"); world.worker.settle()
    model.activate(change(model, Group.CHANGES, "README.md")); world.worker.settle()
    left, right = json.loads(out.read_text())
    assert Path(left).name == "README.md" and right == str(world.root / "alpha" / "README.md")


# ---------- commit ----------

def staged_repo(world: World, name: str = "alpha") -> Repo:
    r = world.repo(name)
    r.write("a.py", "a\n"); r.write("b.py", "b\n"); r.commit()
    r.write("a.py", "a2\n"); r.git("add", "a.py"); r.write("b.py", "b2\n")
    return r


def test_at_vcs_010_commit_contains_only_staged_and_clears_the_message(world):
    r = staged_repo(world)
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix a"
    model.commit(); world.worker.settle()
    assert r.git("log", "-1", "--format=%s").strip() == b"fix a"
    assert r.git("show", "--name-only", "--format=", "HEAD").split() == [b"a.py"]
    assert model.message == "" and paths(model, Group.CHANGES) == ["b.py"]


@pytest.mark.parametrize("stage_something, message", [(False, "fix"), (True, ""), (True, "   ")])
def test_at_vcs_011_commit_is_inactive_without_staged_files_or_message(world, stage_something, message):
    r = world.repo("alpha")
    r.write("README.md", "changed\n")
    if stage_something:
        r.git("add", "README.md")
    model = world.start("alpha"); world.select("alpha")
    model.message = message
    assert not model.can_commit and model.commit_disabled_reason


def test_at_vcs_012_rejected_commit_keeps_message_and_staged_files(world):
    r = staged_repo(world)
    hook = r.path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'lint failed' >&2\nexit 1\n"); hook.chmod(0o755)
    before = commit_count(r)
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix a"
    model.commit(); world.worker.settle()
    assert "lint failed" in model.error
    assert model.message == "fix a" and paths(model, Group.STAGED) == ["a.py"]
    assert commit_count(r) == before


def test_at_vcs_019_commit_goes_only_to_the_selected_repository(world):
    a, b = staged_repo(world, "alpha"), staged_repo(world, "beta")
    model = world.start("alpha", "beta"); world.select("alpha")
    beta_before = commit_count(b)
    model.message = "fix"
    model.commit(); world.worker.settle()
    assert a.git("log", "-1", "--format=%s").strip() == b"fix"
    assert commit_count(b) == beta_before
    world.select("beta")
    assert paths(model, Group.STAGED) == ["a.py"]


def test_at_vcs_023_each_repository_keeps_its_own_draft_and_names_the_target(world):
    world.repo("alpha"); world.repo("beta")
    model = world.start("alpha", "beta")
    world.select("alpha"); model.message = "wip alpha"
    world.select("beta"); model.message = "wip beta"
    world.select("alpha")
    assert model.message == "wip alpha" and model.commit_label == "Commit do alpha"


def test_at_vcs_024_drafts_are_not_kept_after_a_restart(world):
    world.repo("alpha")
    model = world.start("alpha"); world.select("alpha"); model.message = "wip alpha"
    restarted = world.start("alpha"); world.select("alpha")
    assert restarted.message == ""


def test_req_vcs_016_no_second_operation_while_one_is_running(world):
    staged_repo(world)
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix a"
    model.commit()
    assert model.state("alpha") is RepoState.BUSY and not model.can_commit
    model.commit()
    assert len(world.worker.queued) == 1


def test_req_vcs_019_conflicts_block_the_commit_with_a_reason(world):
    r = world.repo("alpha")
    r.write("f.txt", "base\n"); r.commit()
    r.git("checkout", "-q", "-b", "other"); r.write("f.txt", "other\n"); r.commit()
    r.git("checkout", "-q", "main"); r.write("f.txt", "main\n"); r.commit()
    r.git("merge", "-q", "other", check=False)
    r.write("g.txt", "g\n"); r.git("add", "g.txt")
    model = world.start("alpha"); world.select("alpha")
    model.message = "merge"
    assert model.state("alpha") is RepoState.CONFLICT
    assert not model.can_commit and "konflikt" in model.commit_disabled_reason.lower()


def test_uc_vcs_02_detached_head_allows_commit_but_not_push_or_pull(world):
    r = world.repo("alpha")
    r.git("checkout", "-q", "--detach"); r.write("README.md", "y\n"); r.git("add", "README.md")
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix"
    assert model.view("alpha").branch_label == r.git("rev-parse", "--short=7", "HEAD").decode().strip()
    assert model.can_commit and not model.can_commit_and_push and not model.can_pull


# ---------- push and pull ----------

@pytest.fixture
def tracked(world, tmp_path):
    bare = tmp_path / "origin.git"
    Repo(tmp_path).git("init", "-q", "--bare", "-b", "main", str(bare))
    r = staged_repo(world)
    r.git("remote", "add", "origin", str(bare))
    r.git("push", "-q", "-u", "origin", "main")
    return r, bare


def test_req_vcs_011_commit_and_push_reaches_the_upstream(world, tracked):
    r, bare = tracked
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix a"
    model.commit_and_push(); world.worker.settle()
    assert Repo(bare).git("log", "-1", "--format=%s", "main").strip() == b"fix a"
    assert model.error is None and model.view("alpha").status.ahead == 0


@pytest.mark.parametrize("answer", [True, False])
def test_req_vcs_013_branch_without_upstream_asks_before_pushing(world, tracked, answer):
    r, bare = tracked
    r.git("checkout", "-q", "-b", "feature"); r.write("f.txt", "f\n"); r.git("add", "f.txt")
    world.answer = answer
    model = world.start("alpha"); world.select("alpha")
    model.message = "feat"
    model.commit_and_push(); world.worker.settle()
    assert len(world.questions) == 1 and "origin" in world.questions[0]
    assert r.git("log", "-1", "--format=%s").strip() == b"feat"  # the commit happens either way
    assert (model.view("alpha").status.upstream == "origin/feature") is answer


def test_req_vcs_020_pull_fast_forwards_the_selected_repository(world, tracked, tmp_path):
    r, bare = tracked
    other = Repo(tmp_path / "other")
    Repo(tmp_path).git("clone", "-q", str(bare), str(other.path))
    other.write("c.txt", "c\n"); other.commit("remote fix"); other.git("push", "-q")
    model = world.start("alpha"); world.select("alpha")
    assert model.can_pull
    model.pull(); world.worker.settle()
    assert r.git("log", "-1", "--format=%s").strip() == b"remote fix" and model.error is None


class _AuthRequired(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - http.server API
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="git"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_POST = do_GET

    def log_message(self, *args):
        pass


def test_at_vcs_015_missing_credentials_end_with_a_message_not_a_hang(world, tmp_path):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _AuthRequired)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        r = staged_repo(world)
        r.git("remote", "add", "origin", f"http://127.0.0.1:{server.server_port}/repo.git")
        r.git("config", "branch.main.remote", "origin"); r.git("config", "branch.main.merge", "refs/heads/main")
        worker = Worker()
        model = AppModel(Settings(rootdir=str(world.root), repos=("alpha",)), git=world.git,
                         diff_tool=world.tool, worker=worker, confirm=lambda q: False)
        model.select("alpha")
        _drain_until(worker, lambda: model.view("alpha").status is not None)
        model.message = "fix a"
        started = time.monotonic()
        model.commit_and_push()
        assert time.monotonic() - started < 0.5  # the UI thread is not blocked
        _drain_until(worker, lambda: model.error is not None, timeout=30)
        assert "prompts disabled" in model.error or "Authentication" in model.error
    finally:
        server.shutdown()


def _drain_until(worker: Worker, predicate, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "timed out"
        worker.drain()
        time.sleep(0.02)


def test_req_vcs_021_operation_targets_the_repository_selected_at_click_time(world):
    a, b = staged_repo(world, "alpha"), staged_repo(world, "beta")
    model = world.start("alpha", "beta")
    world.select("beta"); model.message = "wip beta"
    world.select("alpha"); model.message = "fix alpha"
    beta_before = commit_count(b)
    model.commit()
    model.select("beta")  # the user switches before the commit has run
    world.worker.settle()
    assert a.git("log", "-1", "--format=%s").strip() == b"fix alpha"
    assert commit_count(b) == beta_before
    assert model.view("alpha").draft == "" and model.view("beta").draft == "wip beta"


# ---------- conflicts (REQ-VCS-024) ----------

def conflicted_repo(world: World, name: str = "gamma") -> Repo:
    r = world.repo(name)
    r.write("f.txt", "base\n"); r.commit("base")
    r.git("checkout", "-q", "-b", "other"); r.write("f.txt", "other\n"); r.commit("other")
    r.git("checkout", "-q", "main"); r.write("f.txt", "main\n"); r.commit("main")
    r.git("merge", "-q", "other", check=False)
    return r


def test_at_vcs_030_fixed_conflict_is_marked_resolved_with_space(world):
    r = conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    r.write("f.txt", "main and other\n")
    model.toggle(change(model, Group.CONFLICTS, "f.txt")); world.worker.settle()
    assert paths(model, Group.CONFLICTS) == [] and paths(model, Group.STAGED) == ["f.txt"]
    model.message = "Merge branch 'other'"
    assert model.can_commit


def test_at_vcs_031_file_with_markers_stays_in_conflict_with_a_message(world):
    conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    model.toggle(change(model, Group.CONFLICTS, "f.txt")); world.worker.settle()
    assert "f.txt" in model.error and "linia 1" in model.error
    assert paths(model, Group.CONFLICTS) == ["f.txt"]
    model.message = "merge"
    assert not model.can_commit


# ---------- toolbar, title and status bar (DES-VCS-043, P10) ----------

def test_des_vcs_043_branch_summary_names_the_upstream(world, tracked):
    model = world.start("alpha"); world.select("alpha")
    assert model.branch_summary == "⎇ main → origin/main"


def test_req_vcs_020_without_upstream_pull_is_off_with_a_reason(world):
    world.repo("alpha")
    model = world.start("alpha"); world.select("alpha")
    assert model.branch_summary == "⎇ main → brak upstreamu"
    assert not model.can_pull and model.pull_disabled_reason == "Gałąź nie ma upstreamu"


def test_uc_vcs_02_detached_head_shows_the_commit_and_explains_why(world):
    r = world.repo("alpha")
    r.git("checkout", "-q", "--detach"); r.write("README.md", "y\n"); r.git("add", "README.md")
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix"
    short = r.git("rev-parse", "--short=7", "HEAD").decode().strip()
    assert model.branch_summary == f"⎇ odłączony HEAD · {short}"
    assert model.pull_disabled_reason == "Odłączony HEAD: brak gałęzi do pull"
    assert model.commit_and_push_disabled_reason == "Odłączony HEAD: brak gałęzi do wypchnięcia"
    assert model.can_commit


def test_req_vcs_021_window_title_names_the_selected_repository(world):
    world.repo("alpha")
    model = world.start("alpha")
    assert model.window_title == "vcs-lite"
    world.select("alpha")
    assert model.window_title == "vcs-lite — alpha"


def test_des_vcs_043_status_bar_shows_when_the_selected_repo_was_refreshed(world):
    from datetime import datetime
    world.repo("alpha")
    world.clock = lambda: datetime(2026, 10, 22, 12, 4)
    model = world.start("alpha")
    assert model.refreshed_label == ""
    world.select("alpha")
    assert model.refreshed_label == "Odświeżono 12:04"


# ---------- sidebar rows (UI-REFERENCE §4, P2, P4, P6) ----------

def test_req_vcs_002_sidebar_line_shows_branch_and_ahead_behind_with_upstream(world, tracked):
    world.repo("plain")
    model = world.start("alpha", "plain")
    assert model.sidebar_line("alpha") == "main · ↑0 ↓0"
    assert model.sidebar_line("plain") == "main"


def test_des_vcs_043_badges_count_changes_skip_clean_and_name_conflicts(world):
    world.repo("alpha").write("a.py", "a\n")
    world.repo("beta")
    conflicted_repo(world, "gamma")
    model = world.start("alpha", "beta", "gamma")
    assert model.badge("alpha") == ("1", "count")
    assert model.badge("beta") is None
    assert model.badge("gamma") == ("konflikt", "conflict")


def test_req_vcs_018_unavailable_repo_has_its_own_line_and_no_badge(world):
    world.repo("alpha")
    model = world.start("alpha", "ghost")
    assert (model.sidebar_line("ghost"), model.badge("ghost")) == ("niedostępne", None)


def test_req_vcs_016_busy_repo_says_so_in_the_sidebar(world):
    staged_repo(world)
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix"
    model.commit()
    assert model.sidebar_line("alpha") == "w toku…"


# ---------- empty states of the file area (P5) ----------

def test_des_vcs_043_empty_state_without_chosen_repositories(world):
    model = world.start()
    e = model.empty_state
    assert (e.glyph, e.head, e.sub, e.action) == ("▣", "Wybierz repozytoria", "vcs-lite pokazuje repozytoria z folderu", "choose_repos")
    assert e.path == str(world.root)


def test_des_vcs_043_empty_state_without_a_selection(world):
    world.repo("alpha")
    e = world.start("alpha").empty_state
    assert (e.glyph, e.head, e.sub, e.action) == ("←", "Wybierz repozytorium", "Kliknij je po lewej albo naciśnij ⌘1.", None)


def test_des_vcs_043_empty_state_for_a_clean_repository(world):
    world.repo("beta")
    model = world.start("beta"); world.select("beta")
    e = model.empty_state
    assert (e.glyph, e.head, e.sub, e.glyph_color) == ("✓", "Brak zmian", "Kopia robocza beta jest zgodna z ostatnim commitem.", "add")


def test_req_vcs_018_empty_state_for_an_unavailable_repository(world):
    world.repo("alpha")
    model = world.start("alpha", "delta"); world.select("delta")
    e = model.empty_state
    assert (e.glyph, e.head, e.sub, e.action) == ("⊘", "Repozytorium niedostępne", "Folder nie istnieje albo nie jest repozytorium gita.", "recheck")
    assert e.path == str(world.root / "delta")


def test_des_vcs_043_no_empty_state_when_there_are_changes(world):
    world.repo("alpha").write("a.py", "a\n")
    model = world.start("alpha"); world.select("alpha")
    assert model.empty_state is None
