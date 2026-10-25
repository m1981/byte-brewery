"""Window layout E-06: the history panel always at the bottom, the commit panel under the file list
(REQ-VCS-036, DES-VCS-069, AT-VCS-049)."""

from __future__ import annotations

import tkinter as tk

import pytest
from world import World

from vcs_lite.ui import history_panel, theme
from vcs_lite.ui.main_window import HISTORY_MIN, TOP_MIN, MainWindow, clamp_history


@pytest.fixture
def root(tk_root):
    frame = tk.Frame(tk_root)
    yield frame
    frame.destroy()


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


def ancestors(widget: tk.Misc) -> list[tk.Misc]:
    out = []
    while widget is not None:
        out.append(widget)
        widget = widget.master
    return out


def test_at_vcs_049_history_is_a_fixed_pane_below_the_files_and_the_commit_panel(root, world):
    world.repo("alpha")
    window = MainWindow(root, world.start("alpha"))
    split = window.split
    assert isinstance(split, tk.PanedWindow) and str(split.cget("orient")) == "vertical"
    top, bottom = split.panes()
    assert str(bottom) == str(window.history) and isinstance(window.history, history_panel.HistoryPanel)
    assert int(split.panecget(top, "minsize")) == TOP_MIN == 220
    assert int(split.panecget(bottom, "minsize")) == HISTORY_MIN == 120
    assert str(split.panecget(bottom, "stretch")) == "never"       # a larger window grows the top part
    assert int(split.panecget(bottom, "height")) == 240
    # the commit panel lives in the file column, next to the full-height sidebar, above the history
    path = [str(w) for w in ancestors(window.commit_button)]
    assert str(top) in path and str(window.file_column) in path
    assert str(window.file_column) not in [str(w) for w in ancestors(window.sidebar)]
    assert str(top) in [str(w) for w in ancestors(window.sidebar)]
    assert not hasattr(window.history, "close_button")              # always visible: nothing closes it


def test_des_vcs_069_the_history_height_comes_from_the_settings_and_is_saved_after_a_drag(root, world):
    world.repo("alpha")
    model = world.start("alpha")
    model.history_height = 300
    window = MainWindow(root, model)
    bottom = window.split.panes()[1]
    assert int(window.split.panecget(bottom, "height")) == 300
    window.history_dragged(410, total=900)   # the test window is not laid out on screen
    assert model.history_height == 410


def test_des_vcs_069_a_drag_is_kept_within_the_limits():
    assert clamp_history(60, total=700) == 120                       # the history keeps 120 pt
    assert clamp_history(600, total=700) == 700 - 220 - 6            # the top keeps 220 pt, the sash 6
    assert clamp_history(300, total=700) == 300
    assert clamp_history(300, total=200) == 120                      # a tiny window: the history wins its minimum


def test_des_vcs_069_the_whole_history_header_drags_the_border(root, world):
    world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    history = window.history
    for handle in history.handles():
        assert str(handle.cget("cursor")) == "sb_v_double_arrow"
    window.history_drag_start(y_root=500, height=240)
    assert window.history_drag_to(y_root=440, total=900) == 300      # up by 60: the history grows by 60
    assert window.history_drag_to(y_root=900, total=900) == 120      # never below its minimum
    window.history_drag_to(y_root=420, total=900)
    window.history_drag_end(total=900)
    assert model.history_height == 320


def test_des_vcs_069_the_grip_lights_up_under_the_pointer(root, world):
    world.repo("alpha")
    window = MainWindow(root, world.start("alpha"))
    history = window.history
    assert history.grip_color == theme.COLORS["seg_thumb_edge"]
    history.highlight(True)
    assert history.grip_color == theme.COLORS["accent"]
    history.highlight(False)
    assert history.grip_color == theme.COLORS["seg_thumb_edge"]
