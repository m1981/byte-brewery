"""Reviewing a group file by file: where the selection goes after space (REQ-VCS-028, DEC-VCS-072)."""

from __future__ import annotations

import pytest
from test_main_window import conflicted, root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.status import Group
from vcs_lite.ui.main_window import MainWindow

U, C, S = Group.UNVERSIONED, Group.CHANGES, Group.STAGED


@pytest.fixture
def review(root, world):  # noqa: F811
    """Staged: a_m.txt · Changes: a_m.txt, c1.txt, c2.txt · Unversioned: u1.txt, u2.txt, u3.txt."""
    r = world.repo("alpha")
    for name in ("a_m.txt", "c1.txt", "c2.txt"):
        r.write(name, "1\n")
    r.commit("init")
    r.write("a_m.txt", "2\n"); r.git("add", "a_m.txt"); r.write("a_m.txt", "3\n")
    r.write("c1.txt", "2\n"); r.write("c2.txt", "2\n")
    for name in ("u1.txt", "u2.txt", "u3.txt"):
        r.write(name, "u\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    return window, model, r


def space_on(window, world, key):  # noqa: F811
    window.file_list.select_key(key)
    window.file_list.press_space()
    world.worker.settle()


def test_at_vcs_035_space_moves_to_the_next_file_of_the_group_after_the_result(review, world):  # noqa: F811
    window, model, _ = review
    fl = window.file_list
    fl.select_key((U, "u1.txt"))
    fl.press_space()
    assert fl.selected_key == (U, "u1.txt")  # D2: nothing moves before the result
    world.worker.settle()
    assert "u1.txt" in [c.path for c in model.files(S)]
    assert fl.selected_key == (U, "u2.txt")
    fl.press_space(); world.worker.settle()
    assert fl.selected_key == (U, "u3.txt")


def test_req_vcs_028_last_file_of_the_group_moves_to_the_previous(review, world):  # noqa: F811
    window, _, _ = review
    space_on(window, world, (U, "u3.txt"))
    assert window.file_list.selected_key == (U, "u2.txt")


def test_req_vcs_028_emptied_group_moves_to_the_first_file_below(review, world):  # noqa: F811
    window, model, _ = review
    space_on(window, world, (S, "a_m.txt"))  # unstage the only staged file: Staged disappears
    assert not model.files(S)
    assert window.file_list.selected_key == (C, "a_m.txt")


def test_req_vcs_028_emptied_last_group_leaves_nothing_selected(review, world):  # noqa: F811
    window, _, _ = review
    for path in ("u1.txt", "u2.txt", "u3.txt"):
        space_on(window, world, (U, path))
    assert window.file_list.selected_key is None


def test_req_vcs_028_file_in_both_groups_staged_from_changes_moves_on_in_changes(review, world):  # noqa: F811
    window, model, _ = review
    space_on(window, world, (C, "a_m.txt"))
    assert "a_m.txt" not in [c.path for c in model.files(C)]
    assert window.file_list.selected_key == (C, "c1.txt")


def test_req_vcs_028_failed_operation_keeps_the_selection(review, world):  # noqa: F811
    window, model, r = review
    (r.path / ".git" / "index.lock").write_text("")
    space_on(window, world, (U, "u1.txt"))
    assert model.error and window.file_list.selected_key == (U, "u1.txt")


def test_req_vcs_028_file_with_conflict_markers_keeps_the_selection(root, world):  # noqa: F811
    conflicted(world, "gamma")
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    space_on(window, world, (Group.CONFLICTS, "f.txt"))
    assert "linia 1" in model.error and window.file_list.selected_key == (Group.CONFLICTS, "f.txt")


def test_req_vcs_028_space_during_an_operation_does_nothing(review, world):  # noqa: F811
    window, model, _ = review
    fl = window.file_list
    fl.select_key((U, "u1.txt"))
    fl.press_space()
    fl.press_space()  # the repository is busy: ignored
    world.worker.settle()
    assert [c.path for c in model.files(U)] == ["u2.txt", "u3.txt"]
    assert fl.selected_key == (U, "u2.txt")


def test_req_vcs_028_next_file_gone_meanwhile_takes_the_one_after(review, world):  # noqa: F811
    window, _, r = review
    fl = window.file_list
    fl.select_key((U, "u1.txt"))
    fl.press_space()
    (r.path / "u2.txt").unlink()  # changed outside before the refresh
    world.worker.settle()
    assert fl.selected_key == (U, "u3.txt")


def test_req_vcs_028_choosing_another_row_meanwhile_wins(review, world):  # noqa: F811
    window, _, _ = review
    fl = window.file_list
    fl.select_key((U, "u1.txt"))
    fl.press_space()
    fl.select_key((C, "c2.txt"))
    world.worker.settle()
    assert fl.selected_key == (C, "c2.txt")


@pytest.fixture
def folders(root, world):  # noqa: F811
    """Folder view, Unversioned: node d (d/x1.txt, d/x2.txt), then root file u1.txt."""
    r = world.repo("alpha")
    r.write("keep.txt", "k\n"); r.commit("init")
    r.write("d/x1.txt", "x\n"); r.write("d/x2.txt", "x\n"); r.write("u1.txt", "u\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.set_list_view("folders")
    return window


def test_req_vcs_028_folder_view_moves_to_the_next_visible_file(folders, world):  # noqa: F811
    space_on(folders, world, (U, "d/x1.txt"))
    assert folders.file_list.selected_key == (U, "d/x2.txt")


def test_req_vcs_028_space_on_a_folder_moves_to_the_first_file_after_it(folders, world):  # noqa: F811
    space_on(folders, world, (U, "d"))
    assert folders.file_list.selected_key == (U, "u1.txt")
