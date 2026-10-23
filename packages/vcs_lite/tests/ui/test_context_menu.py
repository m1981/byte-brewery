"""Context menu of the file list (DEC-VCS-040, DEC-VCS-073; PROPOZYCJA-gitignore.md, stage 2, G-20, G-21).

tk_popup runs a modal menu loop on macOS, so the tests read the entries prepare_menu() computes and run
their commands; posting the menu is checked by hand.
"""

from __future__ import annotations

import pytest
from test_main_window import conflicted, root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.status import Group
from vcs_lite.ui.main_window import MainWindow

S, C, U = Group.STAGED, Group.CHANGES, Group.UNVERSIONED


@pytest.fixture
def listed(root, world):  # noqa: F811
    """Staged: s1.txt · Changes: c1.txt · Unversioned: u1.txt, u2.txt, u3.txt."""
    r = world.repo("alpha")
    r.write("c1.txt", "1\n"); r.write("s1.txt", "1\n"); r.commit("files")
    r.write("c1.txt", "2\n"); r.write("s1.txt", "2\n"); r.git("add", "s1.txt")
    for name in ("u1.txt", "u2.txt", "u3.txt"):
        r.write(name, "u\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    return window, model


def y(window, key) -> int:
    return next(r.top for r in window.file_list.rows() if r.key == key) + 5


def entries(menu) -> dict:
    return {label: enabled for label, enabled, _ in menu}


def run(menu, label, world):  # noqa: F811
    next(command for text, _, command in menu if text == label)()
    world.worker.settle()


def test_des_vcs_024_right_click_and_two_finger_click_open_the_menu(listed):
    c = listed[0].file_list.canvas
    assert c.bind("<Button-2>") and c.bind("<Button-3>")


def test_des_vcs_024_g20_right_click_outside_the_selection_selects_only_that_row(listed):
    window, _ = listed
    fl = window.file_list
    fl.click(y(window, (U, "u1.txt"))); fl.click(y(window, (U, "u2.txt")), shift=True)
    menu = fl.prepare_menu(y(window, (C, "c1.txt")))
    assert set(fl.selected_keys) == {(C, "c1.txt")}
    assert entries(menu) == {"Stage": True, "Unstage": False, "Oznacz jako rozwiązany": False, "Porównaj": True,
                             "Dodaj do .gitignore": False}


def test_at_vcs_037_g21_right_click_inside_the_selection_acts_on_all_of_it(listed, world):  # noqa: F811
    window, model = listed
    fl = window.file_list
    fl.click(y(window, (U, "u1.txt"))); fl.click(y(window, (U, "u2.txt")), shift=True)
    menu = fl.prepare_menu(y(window, (U, "u2.txt")))
    assert set(fl.selected_keys) == {(U, "u1.txt"), (U, "u2.txt")}
    assert entries(menu) == {"Stage (2)": True, "Unstage (2)": False, "Oznacz jako rozwiązany": False, "Porównaj": False,
                             "Dodaj do .gitignore (2)": True}
    run(menu, "Stage (2)", world)
    assert {"u1.txt", "u2.txt"} <= {c.path for c in model.files(S)}


def test_des_vcs_024_unstage_from_the_menu(listed, world):  # noqa: F811
    window, model = listed
    menu = window.file_list.prepare_menu(y(window, (S, "s1.txt")))
    assert entries(menu)["Unstage"] and not entries(menu)["Stage"]
    run(menu, "Unstage", world)
    assert not model.files(S)


def test_des_vcs_024_rows_of_different_groups_offer_no_stage_or_unstage(listed):
    window, _ = listed
    fl = window.file_list
    fl.click(y(window, (C, "c1.txt"))); fl.click(y(window, (U, "u1.txt")), shift=True)
    menu = fl.prepare_menu(y(window, (U, "u1.txt")))
    assert not any(enabled for _, enabled, _ in menu)


def test_des_vcs_024_compare_from_the_menu_opens_the_file(listed, world):  # noqa: F811
    window, _ = listed
    menu = window.file_list.prepare_menu(y(window, (C, "c1.txt")))
    run(menu, "Porównaj", world)
    assert [call["right"].name for call in world.tool.calls] == ["c1.txt"]


def test_des_vcs_024_conflict_offers_mark_resolved_and_no_compare(root, world):  # noqa: F811
    conflicted(world, "gamma")
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    menu = window.file_list.prepare_menu(y(window, (Group.CONFLICTS, "f.txt")))
    assert entries(menu) == {"Stage": False, "Unstage": False, "Oznacz jako rozwiązany": True, "Porównaj": False,
                             "Dodaj do .gitignore": False}
    run(menu, "Oznacz jako rozwiązany", world)
    assert "linia 1" in model.error  # the markers are still there (REQ-VCS-024)


def test_des_vcs_024_busy_repository_offers_no_operation(listed):
    window, _ = listed
    fl = window.file_list
    fl.select_key((U, "u1.txt")); fl.press_space()  # pending in the manual worker
    menu = fl.prepare_menu(y(window, (U, "u2.txt")))
    assert entries(menu) == {"Stage": False, "Unstage": False, "Oznacz jako rozwiązany": False, "Porównaj": True,
                             "Dodaj do .gitignore": False}


def test_des_vcs_024_right_click_on_empty_space_opens_nothing(listed):
    window, _ = listed
    fl = window.file_list
    fl.select_key((C, "c1.txt"))
    assert fl.prepare_menu(y(window, (U, "u3.txt")) + 200) == []
    assert set(fl.selected_keys) == {(C, "c1.txt")}


# ---------- Dodaj do .gitignore (REQ-VCS-030, stage 3) ----------

def test_at_vcs_038_selected_unversioned_files_go_to_the_gitignore(listed, world):  # noqa: F811
    window, model = listed
    fl = window.file_list
    fl.click(y(window, (U, "u1.txt"))); fl.click(y(window, (U, "u2.txt")), shift=True)
    menu = fl.prepare_menu(y(window, (U, "u2.txt")))
    run(menu, "Dodaj do .gitignore (2)", world)
    root_dir = world.root / "alpha"
    assert (root_dir / ".gitignore").read_text().splitlines() == ["/u1.txt", "/u2.txt"]
    assert [c.path for c in model.files(U)] == [".gitignore", "u3.txt"]
    assert set(fl.selected_keys) == {(U, "u3.txt")}  # REQ-VCS-028


def test_req_vcs_030_g13_count_merges_a_folder_with_its_files(root, world):  # noqa: F811
    r = world.repo("alpha")
    r.write("d/x1.txt", "x\n"); r.write("d/x2.txt", "x\n"); r.write("u1.txt", "u\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.show_folders.set(True)
    window.toggle_folders()
    fl = window.file_list
    fl.click(y(window, (U, "d"))); fl.click(y(window, (U, "u1.txt")), shift=True)  # d, d/x1, d/x2, u1
    menu = fl.prepare_menu(y(window, (U, "u1.txt")))
    assert entries(menu)["Dodaj do .gitignore (2)"]  # /d/ and /u1.txt
    run(menu, "Dodaj do .gitignore (2)", world)
    assert (world.root / "alpha" / ".gitignore").read_text().splitlines() == ["/d/", "/u1.txt"]


def test_req_vcs_030_g16_write_error_shows_the_banner_and_keeps_the_file(listed, world):  # noqa: F811
    window, model = listed
    ignore = world.root / "alpha" / ".gitignore"
    ignore.write_text("*.tmp\n"); ignore.chmod(0o444)
    try:
        model.refresh_all(); world.worker.settle()
        menu = window.file_list.prepare_menu(y(window, (U, "u1.txt")))
        run(menu, "Dodaj do .gitignore", world)
        assert model.error_title == "Dodanie do .gitignore nie powiodło się"
        assert ignore.read_text() == "*.tmp\n"
    finally:
        ignore.chmod(0o644)
