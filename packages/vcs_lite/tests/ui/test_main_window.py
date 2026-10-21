"""Smoke tests of the Tk layer: it builds, draws the model and polls only while work is pending.

Layout and look are verified by hand (docs/MANUAL-UI.md); these tests need a desktop session.
"""

from __future__ import annotations

import time
import tkinter as tk

import pytest
from world import World

from vcs_lite.app.worker import Worker
from vcs_lite.ui.main_window import MainWindow
from vcs_lite.ui.pump import TkPump
from vcs_lite.ui.tkenv import prepare_tk


@pytest.fixture(scope="session")
def tk_root():
    """One Tk per process, like the app."""
    prepare_tk()
    try:
        r = tk.Tk()
    except tk.TclError as exc:  # no display, e.g. over ssh
        pytest.skip(f"Tk unavailable: {exc}")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def root(tk_root):
    """A fresh container per test, so widgets never leak between tests."""
    frame = tk.Frame(tk_root)
    yield frame
    frame.destroy()


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


def test_des_vcs_022_window_has_repo_list_file_area_and_commit_bar(root, world):
    world.repo("alpha").write("new.py", "n\n")
    world.repo("beta")
    window = MainWindow(root, world.start("alpha", "beta"))
    window.pack()
    root.update_idletasks()
    rows = [window.repo_list.item(i, "values") for i in window.repo_list.get_children()]
    assert rows == [("alpha", "main", "1"), ("beta", "main", "0")]
    assert window.file_tree.winfo_exists()
    assert window.commit_button.cget("text") == "Commit"
    assert str(window.commit_button.cget("state")) == "disabled"


def test_des_vcs_023_repo_list_follows_model_changes(root, world):
    a = world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    a.write("one.py", "1\n"); a.write("two.py", "2\n")
    model.refresh_all(); world.worker.settle()
    root.update_idletasks()
    assert window.repo_list.item(window.repo_list.get_children()[0], "values")[2] == "2"


def test_des_vcs_017_pump_polls_only_while_work_is_pending(root):
    pump, delivered = TkPump(root, Worker(), interval_ms=10), []
    assert not pump.polling
    assert pump.submit("alpha", lambda: 42, lambda o: delivered.append(o.value))
    assert pump.polling
    deadline = time.monotonic() + 5
    while (delivered == [] or pump.polling) and time.monotonic() < deadline:
        root.update()
        time.sleep(0.005)
    assert delivered == [42] and not pump.polling
