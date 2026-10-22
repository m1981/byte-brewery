"""Keyboard shortcuts of the commit bar and the repository list (REQ-VCS-022).

Tk does not deliver generated key events to the hidden test window, so each test checks that the
shortcut is bound and then runs its handler; the real keys are checked by hand (MANUAL-UI.md, steps 8–9).
"""

from __future__ import annotations

from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.ui.main_window import PLACEHOLDER, MainWindow


def staged(world, name):  # noqa: F811
    r = world.repo(name)
    r.write("a.py", "a\n"); r.commit()
    r.write("a.py", "a2\n"); r.git("add", "a.py")
    return r


def test_req_vcs_022_cmd_return_in_the_message_commits_without_a_new_line(root, world):  # noqa: F811
    r = staged(world, "alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.type_message("fix a")
    press(window, "<Command-Return>", in_message=True)
    world.worker.settle()
    assert r.git("log", "-1", "--format=%s").strip() == b"fix a"
    assert model.message == "" and "\n" not in window.message_box.get("1.0", "end-1c")


def test_req_vcs_009_message_field_is_emptied_after_a_commit(root, world):  # noqa: F811
    staged(world, "alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.type_message("fix a")
    window.message_box.focus_set()
    model.commit(); world.worker.settle()
    assert window.message_box.get("1.0", "end-1c") in ("", PLACEHOLDER)


def test_req_vcs_022_cmd_return_anywhere_in_the_window_commits(root, world):  # noqa: F811
    r = staged(world, "alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.type_message("fix a")
    press(window, "<Command-Return>")
    world.worker.settle()
    assert r.git("log", "-1", "--format=%s").strip() == b"fix a"


def test_req_vcs_022_cmd_return_does_nothing_when_commit_is_not_possible(root, world):  # noqa: F811
    r = staged(world, "alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    before = r.git("rev-parse", "HEAD")
    press(window, "<Command-Return>")  # empty message
    world.worker.settle()
    assert r.git("rev-parse", "HEAD") == before


def test_req_vcs_022_cmd_shift_return_commits_and_pushes(root, world, tmp_path):  # noqa: F811
    from conftest import Repo
    bare = tmp_path / "origin.git"
    Repo(tmp_path).git("init", "-q", "--bare", "-b", "main", str(bare))
    r = staged(world, "alpha")
    r.git("remote", "add", "origin", str(bare)); r.git("push", "-q", "-u", "origin", "main")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.type_message("fix a")
    press(window, "<Command-Shift-Return>", in_message=True)
    world.worker.settle()
    assert Repo(bare).git("log", "-1", "--format=%s", "main").strip() == b"fix a"


def test_req_vcs_022_cmd_digit_selects_that_repository(root, world):  # noqa: F811
    world.repo("alpha"); world.repo("beta")
    model = world.start("alpha", "beta")
    window = MainWindow(root, model)
    press(window, "<Command-Key-2>")
    world.worker.settle()
    assert model.selected == "beta"
    press(window, "<Command-Key-9>")  # no ninth repository: nothing happens
    assert model.selected == "beta"


def press(window, sequence: str, *, in_message: bool = False) -> None:
    widget = window.message_box if in_message else window.winfo_toplevel()
    assert widget.bind(sequence), f"{sequence} is not bound"  # Tk stores it as <Mod1-Key-…>
    assert window.shortcuts[sequence]() == "break"
