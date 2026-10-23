"""The View switch set to Projekt: every tracked file in a tree under the change groups (REQ-VCS-032, DEC-VCS-089)."""

from __future__ import annotations

import pytest
from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.status import Group
from vcs_lite.ui.file_list import PROJECT
from vcs_lite.ui.main_window import MainWindow

INK, FILE_MOD = "#1d1d1f", "#002daa"


@pytest.fixture
def shown(root, world):  # noqa: F811
    """README.md changed; docs/plan.md, src/app.py and src/util/io.py unchanged."""
    r = world.repo("alpha")
    r.write("docs/plan.md", "# Plan\n"); r.write("src/app.py", "x\n"); r.write("src/util/io.py", "y\n"); r.commit("files")
    r.write("README.md", "zmiana\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.set_list_view("project"); world.worker.settle()
    return window, model, r


def project_rows(window):
    return [(r.kind, r.path) for r in window.file_list.rows() if r.group == PROJECT]


def row(window, path):
    return next(r for r in window.file_list.rows() if r.group == PROJECT and r.path == path)


def test_at_vcs_040_project_view_shows_unchanged_files_and_opens_them(shown, world):  # noqa: F811
    window, model, r = shown
    fl = window.file_list
    assert fl.headers() == [("STAGED", 0), ("CHANGES", 1), ("PROJEKT", 4)]
    assert project_rows(window) == [("pdir", "docs"), ("pdir", "src"), ("pfile", "README.md")]  # folders first, collapsed
    assert row(window, "README.md").color == FILE_MOD
    fl.double_click(row(window, "docs").top + 5)
    assert ("pfile", "docs/plan.md") in project_rows(window) and row(window, "docs/plan.md").color == INK
    fl.double_click(row(window, "docs/plan.md").top + 5); world.worker.settle()
    assert world.md_reader.calls[0]["right"] == r.path / "docs" / "plan.md"
    fl.double_click(row(window, "src").top + 5)
    fl.double_click(row(window, "src/app.py").top + 5); world.worker.settle()
    assert world.opened == [["open", str(r.path / "src" / "app.py")]]


def test_req_vcs_032_tree_is_nested_and_indented(shown):
    window, _, _ = shown
    fl = window.file_list
    fl.double_click(row(window, "src").top + 5)
    fl.double_click(row(window, "src/util").top + 5)
    assert [(p, row(window, p).x) for p in ("src", "src/util", "src/util/io.py", "src/app.py", "README.md")] == [
        ("src", 28), ("src/util", 46), ("src/util/io.py", 82), ("src/app.py", 64), ("README.md", 46)]
    assert row(window, "src/util").pieces[0] == ("util", "folder_name")


def test_req_vcs_032_a_collapsed_folder_counts_the_changes_inside(shown, world):
    window, model, r = shown
    r.write("src/util/io.py", "zmiana\n"); r.write("src/new.py", "n\n")
    model.refresh_all(); world.worker.settle()
    assert row(window, "src").pieces == [("src", "folder_name"), ("2 zmiany", "folder_changes")]
    window.file_list.double_click(row(window, "src").top + 5)
    assert row(window, "src").pieces == [("src", "folder_name")]  # open: the files show their colours themselves


def test_req_vcs_032_arrows_fold_and_unfold_a_folder(shown):
    window, _, _ = shown
    fl = window.file_list
    fl.select_key((PROJECT, "docs"))
    fl.press_right()
    assert ("pfile", "docs/plan.md") in project_rows(window)
    fl.press_left()
    assert ("pfile", "docs/plan.md") not in project_rows(window)


def test_req_vcs_032_space_stages_a_changed_file_and_keeps_the_row(shown, world):
    window, model, _ = shown
    fl = window.file_list
    fl.select_key((PROJECT, "README.md")); fl.press_space(); world.worker.settle()
    assert [c.path for c in model.files(Group.STAGED)] == ["README.md"]
    assert fl.selected_key == (PROJECT, "README.md")
    fl.double_click(row(window, "docs").top + 5)
    fl.select_key((PROJECT, "docs/plan.md")); fl.press_space(); world.worker.settle()
    assert [c.path for c in model.files(Group.STAGED)] == ["README.md"]  # unchanged: nothing


def test_req_vcs_032_hints_say_read_or_open(shown):
    window, _, _ = shown
    fl = window.file_list
    fl.double_click(row(window, "docs").top + 5)
    fl.hover(row(window, "docs/plan.md").top + 5)
    assert fl.hint_texts() == ["dwuklik czytaj"]
    fl.double_click(row(window, "src").top + 5)
    fl.hover(row(window, "src/app.py").top + 5)
    assert fl.hint_texts() == ["dwuklik otwórz"]
    fl.hover(row(window, "README.md").top + 5)
    assert fl.hint_texts() == ["spacja stage · dwuklik porównaj"]


def test_req_vcs_032_menu_opens_reveals_and_compares(shown, world):
    window, _, r = shown
    fl = window.file_list
    menu = fl.prepare_menu(row(window, "src").top + 5)
    assert [(label, enabled) for label, enabled, _ in menu] == [("Otwórz", True), ("Pokaż w Finderze", True)]
    next(command for label, _, command in menu if label == "Pokaż w Finderze")(); world.worker.settle()
    assert world.opened == [["open", "-R", str(r.path / "src")]]
    menu = fl.prepare_menu(row(window, "README.md").top + 5)
    assert [label for label, _, _ in menu] == ["Otwórz", "Pokaż w Finderze", "Porównaj", "Porównaj źródło"]


def test_req_vcs_032_change_groups_stay_a_flat_list(shown):
    window, _, _ = shown
    assert [(r.kind, r.path) for r in window.file_list.rows() if r.group is Group.CHANGES] == [("file", "README.md")]
