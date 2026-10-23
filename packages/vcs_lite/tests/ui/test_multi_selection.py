"""Selecting many rows like Windows Explorer (REQ-VCS-029, DEC-VCS-073; PROPOZYCJA-gitignore.md, S-01–S-20).

Tk does not deliver mouse and key events to the hidden test window, so each test checks that the
event is bound and then runs its handler, as for the shortcuts.
"""

from __future__ import annotations

import time

import pytest
from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.repo import GitRepo
from vcs_lite.core.status import Group
from vcs_lite.ui.main_window import MainWindow

C, U = Group.CHANGES, Group.UNVERSIONED
A, B, CC = (C, "c1.txt"), (C, "c2.txt"), (C, "c3.txt")
D, E, F, G, H, I = ((U, f"u{i}.txt") for i in range(1, 7))  # noqa: E741
ACCENT, ACCENT_SOFT = "#0a66d8", "#e3eefc"


@pytest.fixture
def listed(root, world):  # noqa: F811
    """Changes: c1, c2, c3 (A–C) · Unversioned: u1–u6 (D–I)."""
    r = world.repo("alpha")
    for name in ("c1.txt", "c2.txt", "c3.txt"):
        r.write(name, "1\n")
    r.commit("files")
    for name in ("c1.txt", "c2.txt", "c3.txt"):
        r.write(name, "2\n")
    for i in range(1, 7):
        r.write(f"u{i}.txt", "u\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    return window, model, r


def y(window, key) -> int:
    return next(r.top for r in window.file_list.rows() if r.key == key) + 5


def chosen(window) -> set:
    return set(window.file_list.selected_keys)


def test_req_vcs_029_mouse_and_keys_are_bound(listed):
    c = listed[0].file_list.canvas
    for sequence in ("<Shift-Button-1>", "<Control-Button-1>", "<Command-Button-1>", "<Control-Shift-Button-1>",
                     "<Command-Shift-Button-1>", "<Shift-Up>", "<Shift-Down>", "<Control-Up>", "<Control-Down>",
                     "<Command-Up>", "<Command-Down>", "<Control-space>", "<Command-space>", "<Control-a>",
                     "<Command-a>"):
        assert c.bind(sequence), sequence


def test_req_vcs_029_s01_click_keeps_only_that_row(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, A)); fl.click(y(window, CC), ctrl=True)
    fl.click(y(window, B))
    fl._narrow_now()  # a click on an already selected row narrows after the double-click time
    assert chosen(window) == {B}


def test_req_vcs_029_s02_s03_ctrl_click_adds_and_removes(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, A), ctrl=True); fl.click(y(window, CC), ctrl=True)
    assert chosen(window) == {A, CC}
    fl.click(y(window, A), ctrl=True)
    assert chosen(window) == {CC}


def test_at_vcs_036_s04_s08_shift_click_selects_a_range_across_groups(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, B)); fl.click(y(window, E), shift=True)
    assert chosen(window) == {B, CC, D, E}


def test_req_vcs_029_s05_shift_ranges_start_from_the_same_anchor(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, B)); fl.click(y(window, E), shift=True); fl.click(y(window, CC), shift=True)
    assert chosen(window) == {B, CC}


def test_req_vcs_029_s06_ctrl_shift_click_adds_a_second_range(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, B)); fl.click(y(window, D), shift=True)
    fl.click(y(window, G), ctrl=True); fl.click(y(window, I), ctrl=True, shift=True)
    assert chosen(window) == {B, CC, D, G, H, I}


def test_req_vcs_029_s07_range_upwards(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, E)); fl.click(y(window, B), shift=True)
    assert chosen(window) == {B, CC, D, E}


def test_req_vcs_029_s09_range_takes_a_collapsed_folder_node_but_not_its_files(root, world):  # noqa: F811
    r = world.repo("alpha")
    r.write("README.md", "changed\n")
    r.write("d/x1.txt", "x\n"); r.write("d/x2.txt", "x\n"); r.write("u1.txt", "u\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.set_list_view("folders")
    fl = window.file_list
    fl.select_key((U, "d")); fl.press_left()  # collapse the folder
    fl.click(y(window, (C, "README.md"))); fl.click(y(window, (U, "u1.txt")), shift=True)
    assert chosen(window) == {(C, "README.md"), (U, "d"), (U, "u1.txt")}


def test_req_vcs_029_s10_shift_arrows_grow_and_shrink_the_range(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, CC))
    fl.press_down(extend=True); fl.press_down(extend=True); fl.press_up(extend=True)
    assert chosen(window) == {CC, D}


def test_req_vcs_029_s11_ctrl_arrows_move_without_selecting_then_ctrl_space_toggles(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, CC))
    fl.move_current(+1); fl.move_current(+1)
    assert chosen(window) == {CC} and fl.selected_key == E
    c = fl.canvas
    ring = [i for i in c.find_withtag("current_ring")]
    assert ring and {c.itemcget(i, "outline") for i in ring} == {ACCENT}
    fl.toggle_current()
    assert chosen(window) == {CC, E} and fl.selected_key == E


def test_req_vcs_029_s12_ctrl_a_selects_every_visible_row(listed):
    window, _, _ = listed
    window.file_list.select_all()
    assert chosen(window) == {A, B, CC, D, E, F, G, H, I}


def test_req_vcs_029_s13_click_on_empty_space_clears_the_selection(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, A)); fl.click(y(window, CC), ctrl=True)
    fl.click(y(window, I) + 200)
    assert chosen(window) == set() and fl.selected_key is None


def test_at_vcs_036_s14_space_stages_the_selection_with_one_git_add(listed, world, monkeypatch):
    window, model, _ = listed
    calls = []
    real = GitRepo.stage_all
    monkeypatch.setattr(GitRepo, "stage_all", lambda self, changes: calls.append([c.path for c in changes]) or real(self, changes))
    fl = window.file_list
    fl.click(y(window, D)); fl.click(y(window, F), shift=True); fl.click(y(window, E), ctrl=True)
    assert chosen(window) == {D, F}
    fl.press_space(); world.worker.settle()
    assert calls == [["u1.txt", "u3.txt"]]
    assert {"u1.txt", "u3.txt"} <= {c.path for c in model.files(Group.STAGED)}
    assert chosen(window) == {G} and fl.selected_key == G  # REQ-VCS-028: after the last of them


def test_req_vcs_029_s15_space_on_rows_of_different_groups_does_nothing(listed, world):
    window, model, _ = listed
    fl = window.file_list
    fl.click(y(window, CC)); fl.click(y(window, D), shift=True)
    fl.press_space(); world.worker.settle()
    assert not model.files(Group.STAGED) and chosen(window) == {CC, D}


def test_req_vcs_029_s16_double_click_compares_only_that_file_and_keeps_the_selection(listed, world):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, D)); fl.click(y(window, F), shift=True)
    fl.click(y(window, E)); fl.double_click(y(window, E))
    world.worker.settle()
    assert [call["right"].name for call in world.tool.calls] == ["u2.txt"]
    assert chosen(window) == {D, E, F}


def test_req_vcs_029_single_click_in_a_selection_narrows_after_the_double_click_time(listed, root):  # noqa: F811
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, D)); fl.click(y(window, F), shift=True)
    fl.click(y(window, E))
    assert chosen(window) == {D, E, F}
    deadline = time.monotonic() + 0.8
    while time.monotonic() < deadline:
        root.update(); time.sleep(0.01)
    assert chosen(window) == {E}


def test_req_vcs_029_s17_s18_refresh_keeps_existing_rows_and_falls_back_to_the_current_row(listed, world):
    window, model, r = listed
    fl = window.file_list
    fl.click(y(window, D)); fl.click(y(window, G), shift=True)  # anchor u1
    fl.move_current(-1)  # current u3, anchor still u1
    (r.path / "u1.txt").unlink(); (r.path / "u2.txt").unlink()
    model.refresh_all(); world.worker.settle()
    assert chosen(window) == {F, G}
    fl.click(y(window, H), shift=True)  # the anchor is gone: the range starts at the current row u3
    assert chosen(window) == {F, G, H}


def test_req_vcs_029_s19_switching_repositories_clears_the_selection(root, world):  # noqa: F811
    for name in ("alpha", "beta"):
        r = world.repo(name)
        r.write("README.md", "changed\n")
    model = world.start("alpha", "beta")
    window = MainWindow(root, model)
    world.select("alpha")
    fl = window.file_list
    fl.select_key((C, "README.md"))
    world.select("beta")
    assert chosen(window) == set() and fl.selected_key is None


def test_req_vcs_029_s20_every_selected_row_is_tinted_and_only_the_hovered_has_a_hint(listed):
    window, _, _ = listed
    fl = window.file_list
    fl.click(y(window, A)); fl.click(y(window, CC), ctrl=True)
    fl.hover(y(window, E))
    c = fl.canvas
    tops = {r.key: r.top for r in fl.rows()}
    fills = {key: next(c.itemcget(i, "fill") for i in c.find_withtag("row")
                       if c.type(i) == "rectangle" and c.coords(i)[1] == top) for key, top in tops.items()}
    assert fills[A] == fills[CC] == ACCENT_SOFT and fills[B] != ACCENT_SOFT
    assert fl.hint_texts() == ["spacja stage · dwuklik porównaj"]
