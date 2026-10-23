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
from fakes import FakeDiffTool
from world import World

from vcs_lite.app.model import AppModel, RepoState
from vcs_lite.app.worker import Worker
from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.settings import Settings
from vcs_lite.core.repo import GitRepo
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
    a = world.repo("alpha")
    a.write("app.py", "a\n"); a.commit(); a.write("app.py", "b\n")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.CHANGES, "app.py")); world.worker.settle()
    assert world.tool.calls[0]["right"] == world.root / "alpha" / "app.py"
    assert paths(model, Group.CHANGES) == ["app.py"]
    model.toggle(change(model, Group.CHANGES, "app.py")); world.worker.settle()
    assert paths(model, Group.STAGED) == ["app.py"]
    model.toggle(change(model, Group.STAGED, "app.py")); world.worker.settle()
    assert paths(model, Group.STAGED) == [] and paths(model, Group.CHANGES) == ["app.py"]


def test_at_vcs_039_double_click_on_markdown_opens_the_rendered_diff_and_on_text_the_side_by_side_one(world):
    a = world.repo("alpha")
    a.write("README.md", "# Plan\n\nNowy akapit.\n"); a.write("app.py", "x\n")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.CHANGES, "README.md")); world.worker.settle()
    assert [c["right"] for c in world.md_tool.calls] == [a.path / "README.md"] and world.tool.calls == []
    assert world.md_tool.calls[0]["right_title"] == "README.md (kopia robocza)"
    model.activate(change(model, Group.UNVERSIONED, "app.py")); world.worker.settle()
    assert [c["right"].name for c in world.tool.calls] == ["app.py"] and len(world.md_tool.calls) == 1
    assert world.tool.calls[0]["left_title"] == "app.py (pusty)"   # a new file: one column (DES-VCS-059)


def test_req_vcs_031_markdown_is_recognised_by_its_extension():
    from vcs_lite.app.model import is_markdown
    assert [is_markdown(p) for p in ("a.md", "docs/SPEC.MD", "a.markdown", "md", "a.mdx", "a.txt")] == [
        True, True, False, False, False, False]


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
    a.write("app.py", "staged\n"); a.git("add", "app.py")
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.STAGED, "app.py")); world.worker.settle()
    call = world.tool.calls[0]
    assert not call["left"].exists() and not call["right"].exists()
    assert world.worker.history[-1] == "alpha"  # a refresh of the repository ran after the tool closed


def test_at_vcs_028_change_saved_in_the_tool_is_visible_after_closing(world):
    a = world.repo("alpha")
    a.write("app.py", "a\n"); a.commit(); a.write("app.py", "b\n")
    world.external = FakeDiffTool(edit_right=lambda right: right.write_text(right.read_text() + "# poprawka\n"))
    model = world.start("alpha"); world.select("alpha")
    model.activate(change(model, Group.CHANGES, "app.py"), external=True); world.worker.settle()
    assert "# poprawka" in (a.path / "app.py").read_text()
    assert paths(model, Group.CHANGES) == ["app.py"]


def test_at_vcs_025_missing_external_tool_gives_a_message_and_the_app_keeps_working(world, tmp_path):
    world.repo("alpha").write("app.py", "changed\n")
    settings = Settings(rootdir=str(world.root), repos=("alpha",),
                        external_diff_tool=("/nonexistent/inny-diff", "{left}", "{right}"))
    model = AppModel.from_settings(settings, git=world.git, worker=world.worker, confirm=lambda title, message: False)
    model.select("alpha"); world.worker.settle()
    model.activate(change(model, Group.UNVERSIONED, "app.py"), external=True); world.worker.settle()
    assert "/nonexistent/inny-diff" in model.error
    model.toggle(change(model, Group.UNVERSIONED, "app.py")); world.worker.settle()
    assert paths(model, Group.STAGED) == ["app.py"]


def test_at_vcs_026_an_external_tool_plugs_in_through_the_settings(world, tmp_path):
    out = tmp_path / "args.json"
    script = tmp_path / "inny_diff.py"
    script.write_text(textwrap.dedent(f"""
        import json, sys
        json.dump(sys.argv[1:], open({str(out)!r}, "w"))
    """))
    world.repo("alpha").write("app.py", "changed\n")
    plain = AppModel.from_settings(Settings(rootdir=str(world.root), repos=("alpha",)), git=world.git,
                                   worker=world.worker, confirm=lambda title, message: False)
    assert not plain.has_external_tool
    settings = Settings(rootdir=str(world.root), repos=("alpha",),
                        external_diff_tool=(sys.executable, str(script), "{left}", "{right}"))
    model = AppModel.from_settings(settings, git=world.git, worker=world.worker, confirm=lambda title, message: False)
    assert model.has_external_tool
    model.select("alpha"); world.worker.settle()
    model.activate(change(model, Group.UNVERSIONED, "app.py"), external=True); world.worker.settle()
    left, right = json.loads(out.read_text())
    assert Path(left).name == "app.py" and right == str(world.root / "alpha" / "app.py")


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
    assert world.questions == [("Gałąź feature nie ma upstreamu",
                                "Commit został zapisany. Wypchnąć gałąź do origin i ustawić upstream?")]  # P9
    assert r.git("log", "-1", "--format=%s").strip() == b"feat"  # the commit happens either way
    assert (model.view("alpha").status.upstream == "origin/feature") is answer


def test_req_vcs_009_the_window_shows_the_emptied_message_before_the_upstream_question(world, tracked):
    """Zrzut 2026-10-22: during question P9 the message field still showed the saved commit's text."""
    r, _ = tracked
    r.git("checkout", "-q", "-b", "feature"); r.write("f.txt", "f\n"); r.git("add", "f.txt")
    world.answer = False
    model = world.start("alpha"); world.select("alpha")
    events = world.questions  # the question lands in the same list, after whatever the window was told
    model.subscribe(lambda: events.append(("render", model.message)))
    model.message = "feat"
    model.commit_and_push(); world.worker.settle()
    asked = next(i for i, e in enumerate(events) if e[0] == "Gałąź feature nie ma upstreamu")
    assert ("render", "") in events[:asked]


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
                         diff_tool=world.tool, worker=worker, confirm=lambda title, message: False)
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


def test_at_vcs_034_merge_resolved_to_head_can_be_concluded_with_a_commit(world):
    r = conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    r.write("f.txt", "main\n")
    model.toggle(change(model, Group.CONFLICTS, "f.txt")); world.worker.settle()
    assert model.state("gamma") is RepoState.MERGE
    assert model.sidebar_line("gamma") == "main · merge"
    assert model.merge_summary == "merge gotowy do commita" and model.conflict_summary == ""
    assert model.empty_state.head == "Merge gotowy do commita"
    assert model.commit_disabled_reason == "Wpisz wiadomość commita."
    model.message = "Merge branch 'other'"
    assert model.can_commit and paths(model, Group.STAGED) == []
    model.commit(); world.worker.settle()
    assert len(r.git("log", "-1", "--format=%P").split()) == 2
    assert model.state("gamma") is RepoState.CLEAN and model.merge_summary == ""


def test_req_vcs_027_conflicts_during_a_merge_say_merge_in_the_sidebar(world):
    conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    assert model.state("gamma") is RepoState.CONFLICT
    assert model.sidebar_line("gamma") == "main · merge"
    assert model.merge_summary == ""


def test_req_vcs_027_merge_with_a_staged_result_keeps_the_list_and_the_upstream_line(world, tracked):
    r, _ = tracked
    r.git("commit", "-q", "-m", "staged")
    r.git("checkout", "-q", "-b", "other"); r.write("o.txt", "o\n"); r.git("add", "o.txt"); r.git("commit", "-q", "-m", "o")
    r.git("checkout", "-q", "main"); r.git("merge", "-q", "--no-ff", "--no-commit", "other")
    model = world.start("alpha"); world.select("alpha")
    assert model.state("alpha") is RepoState.MERGE
    assert paths(model, Group.STAGED) == ["o.txt"]
    assert model.sidebar_line("alpha") == "main · ↑1 ↓0 · merge"
    assert model.empty_state is None


# ---------- toolbar, title and status bar (DES-VCS-043, P10) ----------

def test_des_vcs_043_branch_summary_names_the_upstream(world, tracked):
    model = world.start("alpha"); world.select("alpha")
    assert model.branch_summary == "⎇ main → origin/main"


def test_des_vcs_043_conflict_chip_counts_the_files_in_conflict(world):
    r = conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    assert model.conflict_summary == "1 plik w konflikcie"
    r.write("f.txt", "main\n"); r.git("add", "f.txt")
    model.refresh_all(); world.worker.settle()
    assert model.conflict_summary == ""


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



# ---------- folders (REQ-VCS-025, REQ-VCS-026) ----------

def folders_repo(world):
    r = world.repo("alpha")
    r.write("spec/a.json", "1\n"); r.write("spec/b.json", "2\n"); r.write("top.txt", "t\n")
    return r


def test_at_vcs_033_folder_button_stages_every_file_of_the_folder(world):
    folders_repo(world)
    model = world.start("alpha"); world.select("alpha")
    model.toggle_folder(Group.UNVERSIONED, "spec"); world.worker.settle()
    assert paths(model, Group.STAGED) == ["spec/a.json", "spec/b.json"]
    assert paths(model, Group.UNVERSIONED) == ["top.txt"]


def test_req_vcs_026_minus_in_staged_unstages_the_folder(world):
    r = folders_repo(world)
    r.git("add", "spec")
    model = world.start("alpha"); world.select("alpha")
    model.toggle_folder(Group.STAGED, "spec"); world.worker.settle()
    assert paths(model, Group.STAGED) == []


def test_req_vcs_026_folder_in_conflicts_does_nothing(world):
    conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    queued = len(world.worker.queued)
    model.toggle_folder(Group.CONFLICTS, "")
    assert len(world.worker.queued) == queued


def test_req_vcs_025_folder_view_choice_is_saved(world):
    world.repo("alpha")
    saved = []
    settings = Settings(rootdir=str(world.root), repos=("alpha",))
    model = AppModel(settings, git=world.git, diff_tool=world.tool, worker=world.worker,
                     confirm=lambda title, message: True, save_settings=saved.append)
    assert model.list_view == "changes"
    model.list_view = "folders"
    assert model.list_view == "folders" and saved[-1].list_view == "folders" and saved[-1].repos == ("alpha",)


# ---------- choosing repositories (E-02, P8, REQ-VCS-001) ----------

def make_rootdir_contents(world):
    for name in ("gamma", "alpha", "beta"):
        world.repo(name)
    (world.root / "zdjecia").mkdir()
    Repo(world.root / ".ukryte").path.mkdir()
    (world.root / ".ukryte" / ".git").mkdir()


def test_at_vcs_001_choices_list_first_level_repositories_with_the_current_choice(world):
    make_rootdir_contents(world)
    model = world.start("alpha")
    choices, error = model.repo_choices()
    assert error is None
    assert [(c.name, c.chosen, c.missing) for c in choices] == [("alpha", True, False), ("beta", False, False), ("gamma", False, False)]


def test_req_vcs_018_chosen_repository_missing_from_disk_stays_listed(world):
    make_rootdir_contents(world)
    model = world.start("alpha", "delta")
    choices, _ = model.repo_choices()
    assert (choices[-1].name, choices[-1].chosen, choices[-1].missing) == ("delta", True, True)


def test_uc_vcs_01_missing_rootdir_is_reported(world, tmp_path):
    model = AppModel(Settings(rootdir=str(tmp_path / "nope")), git=world.git, diff_tool=world.tool,
                     worker=world.worker, confirm=lambda title, message: True)
    choices, error = model.repo_choices()
    assert choices == [] and str(tmp_path / "nope") in error


def test_at_vcs_001_saving_the_choice_updates_the_list_and_settings(world):
    make_rootdir_contents(world)
    saved = []
    world.save_settings = saved.append
    model = world.start("alpha")
    world.select("alpha")
    model.set_repos(["beta", "gamma"]); world.worker.settle()
    assert model.repo_names == ["beta", "gamma"]
    assert model.selected is None
    assert saved[-1].repos == ("beta", "gamma")
    assert model.view("beta").status is not None  # newly chosen repositories are refreshed



# ---------- error banner and operation in progress (P3, P4, DES-VCS-043) ----------

def test_des_vcs_043_failed_commit_names_the_operation(world):
    r = staged_repo(world)
    hook = r.path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'lint failed' >&2\nexit 1\n"); hook.chmod(0o755)
    model = world.start("alpha"); world.select("alpha")
    model.message = "fix"
    model.commit(); world.worker.settle()
    assert model.error_title == "Commit nie powiódł się" and "lint failed" in model.error


def test_des_vcs_043_unresolved_conflict_names_the_operation(world):
    conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    model.toggle(change(model, Group.CONFLICTS, "f.txt")); world.worker.settle()
    assert model.error_title == "Oznaczenie jako rozwiązany nie powiodło się"


def test_des_vcs_043_error_can_be_dismissed(world):
    conflicted_repo(world)
    model = world.start("gamma"); world.select("gamma")
    model.toggle(change(model, Group.CONFLICTS, "f.txt")); world.worker.settle()
    model.dismiss_error()
    assert model.error is None and model.error_title is None


def test_des_vcs_043_busy_label_names_the_running_operation(world, tracked):
    model = world.start("alpha"); world.select("alpha")
    assert model.busy_label is None
    model.message = "fix a"
    model.commit_and_push()
    assert model.busy_label == "Zapisywanie commita…"
    world.worker.step()          # the commit; the push is chained right after it
    assert model.busy_label == "Wypychanie do origin…"
    world.worker.settle()
    assert model.busy_label is None


def test_req_vcs_029_toggle_many_stages_or_unstages_files_of_one_group(world):
    r = world.repo("alpha")
    for name in ("u1.txt", "u2.txt"):
        r.write(name, "u\n")
    model = world.start("alpha"); world.select("alpha")
    model.toggle_many(Group.UNVERSIONED, model.files(Group.UNVERSIONED)); world.worker.settle()
    assert paths(model, Group.STAGED) == ["u1.txt", "u2.txt"]
    model.toggle_many(Group.STAGED, model.files(Group.STAGED)); world.worker.settle()
    assert paths(model, Group.UNVERSIONED) == ["u1.txt", "u2.txt"]


def test_req_vcs_031_markdown_theme_is_kept_in_the_settings(world):
    saved = []
    world.save_settings = saved.append
    world.repo("alpha")
    model = world.start("alpha")
    assert model.markdown_theme == "system"
    model.markdown_theme = "light"
    assert model.markdown_theme == "light" and saved[-1].markdown_theme == "light"


# ---------- project view (REQ-VCS-032, DES-VCS-050) ----------

@pytest.fixture
def project(world):
    r = world.repo("alpha")  # README.md committed by the world
    r.write("docs/plan.md", "# Plan\n"); r.write("src/app.py", "x\n"); r.write("both.py", "1\n"); r.commit("files")
    r.write("README.md", "zmiana\n")
    r.write("both.py", "2\n"); r.git("add", "both.py"); r.write("both.py", "3\n")
    r.write("u.txt", "u\n")
    model = world.start("alpha"); world.select("alpha")
    return model


def test_req_vcs_032_project_files_join_tracked_and_unversioned_with_their_change(project, world):
    model = project
    model.list_view = "project"; world.worker.settle()
    files = [(f.path, f.change.group.value if f.change else None) for f in model.project_files()]
    assert files == [("README.md", "Changes"), ("both.py", "Changes"), ("docs/plan.md", None), ("src/app.py", None),
                     ("u.txt", "Unversioned")]  # a file in Staged and Changes shows its working-copy change


def test_req_vcs_032_tracked_files_are_read_only_in_the_project_view(project, world, monkeypatch):
    model = project
    calls = []
    real = GitRepo.tracked_files
    monkeypatch.setattr(GitRepo, "tracked_files", lambda self: calls.append(self.path.name) or real(self))
    model.refresh_all(); world.worker.settle()
    assert calls == [] and model.project_files() == []
    model.list_view = "project"; world.worker.settle()  # switching to the view reads them at once
    assert calls == ["alpha"] and model.project_files()


def test_req_vcs_032_reading_opening_and_revealing_project_files(project, world):
    model = project
    root = world.root / "alpha"
    model.open_file("docs/plan.md"); world.worker.settle()
    assert world.md_reader.calls[0]["right"] == root / "docs" / "plan.md"
    assert world.md_reader.calls[0]["right_title"] == "docs/plan.md (kopia robocza)"
    model.open_file("src/app.py"); world.worker.settle()
    assert world.text_reader.calls[0]["right"] == root / "src" / "app.py"   # text in the browser (REQ-VCS-034)
    model.open_in_app("src/app.py"); model.reveal("src/app.py"); world.worker.settle()
    assert world.opened == [["open", str(root / "src" / "app.py")], ["open", "-R", str(root / "src" / "app.py")]]


def test_req_vcs_032_a_failing_open_shows_the_error(project, world):
    model = project
    def refuse(command):
        raise OSError("brak aplikacji do otwarcia")
    model._opener = refuse
    model.open_in_app("src/app.py"); world.worker.settle()
    assert model.error_title == "Otwieranie nie powiodło się" and "brak aplikacji" in model.error


# ---------- where a file opens (REQ-VCS-034, DES-VCS-060) ----------

PNG = b"\x89PNG\r\n\x1a\nobraz"


@pytest.fixture
def typed(world):
    """Changed logo.png, a new ikona.png staged then changed again, unversioned opis.pdf and dane.bin,
    unchanged notatki.txt, archiwum.zip and stare.png (deleted in Changes)."""
    r = world.repo("alpha")
    for name in ("logo.png", "stare.png"):
        (r.path / name).write_bytes(PNG + b"1")
    r.write("notatki.txt", "notatki\n"); (r.path / "archiwum.zip").write_bytes(b"PK\3\4\0\0")
    r.commit("files")
    (r.path / "logo.png").write_bytes(PNG + b"2")
    (r.path / "ikona.png").write_bytes(PNG + b"indeks"); r.git("add", "ikona.png")
    (r.path / "ikona.png").write_bytes(PNG + b"dysk")
    (r.path / "opis.pdf").write_bytes(b"%PDF-1.4\n"); (r.path / "dane.bin").write_bytes(b"\0\1\2")
    (r.path / "stare.png").unlink()
    model = world.start("alpha"); world.select("alpha")
    return model, r


def test_at_vcs_045_the_kind_of_file_decides_where_it_opens(typed, world):
    model, r = typed
    model.activate(change(model, Group.CHANGES, "logo.png")); world.worker.settle()
    assert world.browsed == [r.path / "logo.png"]
    model.activate(change(model, Group.STAGED, "ikona.png")); world.worker.settle()
    copy = world.browsed[-1]
    assert copy.name == "ikona.png" and copy.read_bytes() == PNG + b"indeks" and world.copies in copy.parents
    model.activate(change(model, Group.UNVERSIONED, "opis.pdf")); world.worker.settle()
    assert world.browsed[-1] == r.path / "opis.pdf"
    model.open_file("notatki.txt"); model.open_file("archiwum.zip"); world.worker.settle()
    assert world.text_reader.calls[0]["right"] == r.path / "notatki.txt"
    assert world.opened == [["open", str(r.path / "archiwum.zip")]]
    model.open_in_app("logo.png"); world.worker.settle()
    assert world.opened[-1] == ["open", str(r.path / "logo.png")]
    assert world.tool.calls == [] and world.md_tool.calls == []   # no page of differences for any of them


def test_des_vcs_060_a_deleted_image_shows_its_last_version(typed, world):
    model, r = typed
    model.activate(change(model, Group.CHANGES, "stare.png")); world.worker.settle()
    assert world.browsed[-1].read_bytes() == PNG + b"1"


def test_des_vcs_060_images_and_pdfs_open_in_the_browser_also_unchanged(typed, world):
    model, r = typed
    (r.path / "logo.png").write_bytes(PNG + b"1")   # back as committed
    model.open_file("logo.png"); world.worker.settle()
    assert world.browsed == [r.path / "logo.png"]


def test_des_vcs_060_a_failing_browser_shows_the_error(typed, world):
    model, _ = typed
    def refuse(path):
        raise OSError("brak przeglądarki")
    model._browser = refuse
    model.activate(change(model, Group.CHANGES, "logo.png")); world.worker.settle()
    assert model.error_title == "Otwieranie nie powiodło się" and "brak przeglądarki" in model.error


def test_at_vcs_007_binary_file_has_no_diff_but_can_be_staged(typed, world):
    from vcs_lite.core.textpage import render_page
    model, r = typed
    model.activate(change(model, Group.UNVERSIONED, "dane.bin")); world.worker.settle()
    [call] = world.tool.calls
    page = render_page(call["left_bytes"], call["right_bytes"], file_name="dane.bin", left_title=call["left_title"],
                       right_title=call["right_title"])
    assert "Brak podglądu zmian" in page and "3 B" in page
    model.toggle(change(model, Group.UNVERSIONED, "dane.bin")); world.worker.settle()
    assert "dane.bin" in paths(model, Group.STAGED)


def test_des_vcs_060_text_search_match_opens_the_text_page_at_its_line(typed, world):
    model, r = typed
    model.open_match("notatki.txt", 1); world.worker.settle()
    assert world.text_reader.calls[0]["line"] == 1
