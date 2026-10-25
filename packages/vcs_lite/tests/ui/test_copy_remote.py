"""The right button on a repository tile copies its remote address as https, with no menu (REQ-VCS-035, AT-VCS-048)."""

from __future__ import annotations

import tkinter as tk

import pytest
from world import World

from vcs_lite.ui.main_window import MainWindow


@pytest.fixture
def root(tk_root):
    frame = tk.Frame(tk_root)
    yield frame
    frame.destroy()


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


def right_click(window: MainWindow, name: str) -> None:
    """The test window is withdrawn, so Tk delivers no pointer events: the bound handler is called directly."""
    row = next(r for r in window.sidebar.rows() if r.name == name)
    window.sidebar.right_click(row.top + 10)


def test_at_vcs_048_right_button_copies_the_origin_address_and_keeps_the_selection(root, world, monkeypatch):
    world.repo("alpha")
    beta = world.repo("beta")
    beta.git("remote", "add", "upstream", "https://example.com/upstream.git")
    beta.git("remote", "add", "origin", "git@github.com:m1981/beta.git")
    world.repo("gamma")
    model = world.start("alpha", "beta", "gamma")
    world.select("alpha")
    copied, bells = [], []
    window = MainWindow(root, model, clipboard=copied.append)
    monkeypatch.setattr(window, "bell", lambda *args: bells.append(True))
    window.pack()
    root.update_idletasks()
    assert {"<Button-2>", "<Button-3>"} <= set(window.sidebar.canvas.bind())   # right button and two fingers
    right_click(window, "beta")
    world.worker.settle()
    assert copied == ["https://github.com/m1981/beta.git"] and model.selected == "alpha"
    assert [r.selected for r in window.sidebar.rows()] == [True, False, False]
    right_click(window, "gamma")                            # gamma has no remote
    world.worker.settle()
    assert copied == ["https://github.com/m1981/beta.git"] and bells == [True]


def test_des_vcs_063_right_button_outside_the_tiles_does_nothing(root, world):
    world.repo("alpha").git("remote", "add", "origin", "https://github.com/m1981/alpha.git")
    copied = []
    window = MainWindow(root, world.start("alpha"), clipboard=copied.append)
    window.pack()
    root.update_idletasks()
    window.sidebar.right_click(window.sidebar.rows()[-1].top + 200)
    world.worker.settle()
    assert copied == [] and world.worker.queued == []
