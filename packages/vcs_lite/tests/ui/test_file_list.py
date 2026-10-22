"""File list drawn after the reference (UI-REFERENCE §4, P1, P5, P7): groups, squares, paths, hints, keys."""

from __future__ import annotations

import pytest
from test_main_window import conflicted, root, tk_root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.status import Group
from vcs_lite.ui.main_window import MainWindow


def alpha_like(world):
    """The demo repository of the reference: staged, changed, both, renamed, unversioned, ignored."""
    a = world.repo("alpha")
    a.write("staged.py", "1\n"); a.write("both.py", "1\n"); a.write("old_name.py", "x\n" * 10)
    a.write(".gitignore", "*.log\n"); a.commit("init")
    a.write("README.md", "changed\n")
    a.write("staged.py", "2\n"); a.git("add", "staged.py")
    a.write("both.py", "2\n"); a.git("add", "both.py"); a.write("both.py", "3\n")
    a.git("mv", "old_name.py", "renamed.py")
    a.write("new/a.txt", "a\n"); a.write("debug.log", "x\n")
    return a


@pytest.fixture
def shown(root, world):  # noqa: F811
    alpha_like(world)
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    return window, model


def test_des_vcs_024_groups_in_order_with_counts(shown):
    window, _ = shown
    assert window.file_list.headers() == [("STAGED", 3), ("CHANGES", 2), ("UNVERSIONED", 1)]


def test_des_vcs_024_rows_have_status_squares_and_split_paths(shown):
    window, _ = shown
    rows = {(r.group, r.path): r for r in window.file_list.rows()}
    assert (rows[(Group.STAGED, "staged.py")].letter, rows[(Group.STAGED, "staged.py")].color) == ("M", "#b4690e")
    renamed = rows[(Group.STAGED, "renamed.py")]
    assert (renamed.letter, renamed.color, renamed.pieces) == ("R", "#2a5fb0", [("old_name.py → ", "file_dir"), ("renamed.py", "file_name")])
    new = rows[(Group.UNVERSIONED, "new/a.txt")]
    assert (new.letter, new.color, new.pieces) == ("?", "#7a7a80", [("new/", "file_dir"), ("a.txt", "file_name")])
    assert all("debug.log" not in r.path for r in rows.values())


def test_des_vcs_024_row_geometry_follows_the_reference(shown):
    window, _ = shown
    first = window.file_list.rows()[0]
    assert first.top == 6 + 29 and first.height == 28  # padding 6, header 10 + 15 + 4, row 5 + 18 + 5


def test_des_vcs_024_hint_shows_only_on_the_selected_row(shown):
    window, _ = shown
    assert window.file_list.hint_texts() == []
    window.file_list.select_key((Group.CHANGES, "README.md"))
    assert window.file_list.hint_texts() == ["spacja stage · dwuklik porównaj"]
    window.file_list.select_key((Group.STAGED, "staged.py"))
    assert window.file_list.hint_texts() == ["spacja unstage · dwuklik porównaj"]
    window.file_list.select_key((Group.UNVERSIONED, "new/a.txt"))
    assert window.file_list.hint_texts() == ["spacja stage · dwuklik porównaj"]  # P7


def test_des_vcs_024_hover_highlights_and_shows_the_hint(shown):
    window, _ = shown
    row = window.file_list.rows()[0]
    window.file_list.hover(row.top + 5)
    assert window.file_list.hovered_key == (row.group, row.path)
    assert window.file_list.hint_texts() == ["spacja unstage · dwuklik porównaj"]
    window.file_list.hover(-100)
    assert window.file_list.hovered_key is None


def test_at_vcs_029_space_stages_and_selection_follows_the_file(shown, world):
    window, model = shown
    window.file_list.select_key((Group.CHANGES, "README.md"))
    window.file_list.press_space()
    world.worker.settle()
    assert "README.md" in [c.path for c in model.files(Group.STAGED)]
    assert window.file_list.selected_key == (Group.STAGED, "README.md")


def test_at_vcs_029_double_click_and_enter_open_the_compare(shown, world):
    window, _ = shown
    readme = next(r for r in window.file_list.rows() if r.path == "README.md")
    window.file_list.double_click(readme.top + 5)
    world.worker.settle()
    window.file_list.press_return()
    world.worker.settle()
    assert len(world.tool.calls) == 2 and world.tool.calls[0]["right"].name == "README.md"


def test_des_vcs_024_arrow_keys_move_the_selection(shown):
    window, _ = shown
    window.file_list.press_down()
    assert window.file_list.selected_key == (Group.STAGED, "both.py")
    window.file_list.press_down(); window.file_list.press_down(); window.file_list.press_down()
    assert window.file_list.selected_key == (Group.CHANGES, "README.md")
    window.file_list.press_up()
    assert window.file_list.selected_key == (Group.STAGED, "staged.py")


def test_des_vcs_024_conflicts_come_first_in_red(root, world):  # noqa: F811
    conflicted(world, "gamma")
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    assert window.file_list.headers()[0] == ("CONFLICTS", 1)
    row = window.file_list.rows()[0]
    assert (row.letter, row.color) == ("!", "#c2302a")
    window.file_list.select_key((Group.CONFLICTS, "f.txt"))
    assert window.file_list.hint_texts() == ["rozwiąż w edytorze · spacja oznacz jako rozwiązany"]


def test_des_vcs_043_empty_state_is_drawn_in_the_file_area(root, world):  # noqa: F811
    world.repo("beta")
    model = world.start("beta")
    window = MainWindow(root, model)
    world.select("beta")
    assert window.file_list.rows() == []
    assert window.file_list.empty_texts() == ["✓", "Brak zmian", "Kopia robocza beta jest zgodna z ostatnim commitem."]
