"""File list after the reference §9 (DEC-VCS-052–057): colour names, 24 pt rows, folder view, folder stage."""

from __future__ import annotations

import pytest
from test_main_window import conflicted, root, world  # noqa: F401 - shared fixtures

from vcs_lite.core.settings import SettingsStore
from vcs_lite.core.status import Group
from vcs_lite.ui import theme
from vcs_lite.ui.main_window import MainWindow

FILE_MOD, FILE_ADD, FILE_UNV, FILE_REN, FILE_DEL = "#002daa", "#0c7216", "#a92c3e", "#002daa", "#6e6e73"


def alpha_like(world):
    """Staged, changed, both, renamed, deleted, unversioned in folders, ignored."""
    a = world.repo("alpha")
    a.write("staged.py", "1\n"); a.write("both.py", "1\n"); a.write("old_name.py", "x\n" * 10)
    a.write("gone.py", "g\n"); a.write(".gitignore", "*.log\n"); a.commit("init")
    a.write("README.md", "changed\n")
    a.write("staged.py", "2\n"); a.git("add", "staged.py")
    a.write("both.py", "2\n"); a.git("add", "both.py"); a.write("both.py", "3\n")
    a.git("mv", "old_name.py", "renamed.py"); a.git("rm", "-q", "gone.py")
    a.write("new/a.txt", "a\n"); a.write("new/b.txt", "b\n"); a.write("debug.log", "x\n")
    return a


@pytest.fixture
def shown(root, world):  # noqa: F811
    alpha_like(world)
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    return window, model


def by_path(window, group, path):
    return next(r for r in window.file_list.rows() if r.group is group and r.path == path)


# ---------- flat view ----------

def test_des_vcs_045_groups_in_order_with_counts(shown):
    window, _ = shown
    assert window.file_list.headers() == [("STAGED", 4), ("CHANGES", 2), ("UNVERSIONED", 2)]


def test_des_vcs_045_names_are_coloured_by_status_without_squares(shown):
    window, _ = shown
    assert by_path(window, Group.STAGED, "staged.py").color == FILE_MOD
    assert by_path(window, Group.STAGED, "gone.py").color == FILE_DEL
    assert by_path(window, Group.UNVERSIONED, "new/a.txt").color == FILE_UNV
    assert all(r.kind == "file" for r in window.file_list.rows())


def test_des_vcs_045_name_first_then_folder_or_old_name(shown):
    window, _ = shown
    assert by_path(window, Group.UNVERSIONED, "new/a.txt").pieces == [("a.txt", "file_name"), ("new", "file_folder")]
    assert by_path(window, Group.STAGED, "renamed.py").pieces == [("renamed.py", "file_name"), ("← old_name.py", "file_folder")]
    assert by_path(window, Group.STAGED, "gone.py").pieces == [("gone.py", "file_name_del")]


def test_des_vcs_045_rows_are_24_points_from_x_28(shown):
    window, _ = shown
    first = window.file_list.rows()[0]
    assert (first.top, first.height, first.x) == (6 + 24, 24, 28)


def test_des_vcs_024_hint_shows_only_on_the_selected_row(shown):
    window, _ = shown
    assert window.file_list.hint_texts() == []
    window.file_list.select_key((Group.CHANGES, "README.md"))
    assert window.file_list.hint_texts() == ["spacja stage · dwuklik porównaj"]
    window.file_list.select_key((Group.STAGED, "staged.py"))
    assert window.file_list.hint_texts() == ["spacja unstage · dwuklik porównaj"]


def test_des_vcs_024_hover_highlights_and_shows_the_hint(shown):
    window, _ = shown
    row = window.file_list.rows()[0]
    window.file_list.hover(row.top + 5)
    assert window.file_list.hovered_key == row.key
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
    readme = by_path(window, Group.CHANGES, "README.md")
    window.file_list.double_click(readme.top + 5)
    world.worker.settle()
    window.file_list.press_return()
    world.worker.settle()
    assert len(world.tool.calls) == 2 and world.tool.calls[0]["right"].name == "README.md"


def test_des_vcs_024_arrow_keys_move_the_selection(shown):
    window, _ = shown
    window.file_list.press_down()
    assert window.file_list.selected_key == (Group.STAGED, "both.py")
    window.file_list.press_up()
    assert window.file_list.selected_key == (Group.STAGED, "both.py")


def test_des_vcs_045_conflicts_come_first_in_red(root, world):  # noqa: F811
    conflicted(world, "gamma")
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    assert window.file_list.headers()[0] == ("CONFLICTS", 1)
    assert window.file_list.rows()[0].color == "#c2302a"
    window.file_list.select_key((Group.CONFLICTS, "f.txt"))
    assert window.file_list.hint_texts() == ["rozwiąż w edytorze · spacja oznacz jako rozwiązany"]


def test_des_vcs_043_empty_state_is_drawn_in_the_file_area(root, world):  # noqa: F811
    world.repo("beta")
    model = world.start("beta")
    window = MainWindow(root, model)
    world.select("beta")
    assert window.file_list.rows() == []
    assert window.file_list.empty_texts() == ["✓", "Brak zmian", "Kopia robocza beta jest zgodna z ostatnim commitem."]


def test_des_vcs_043_empty_state_description_wraps_at_46_characters(root, world):  # noqa: F811
    r = conflicted(world, "gamma")
    r.write("f.txt", "main\n"); r.git("add", "f.txt")
    model = world.start("gamma")
    window = MainWindow(root, model)
    window.pack()
    world.select("gamma")
    root.update_idletasks()
    c = window.file_list.canvas
    item = next(i for i in c.find_all() if c.type(i) == "text" and c.itemcget(i, "text").startswith("Konflikty w gamma"))
    limit = theme.font("empty_sub").measure("0") * 46
    x1, y1, x2, y2 = c.bbox(item)
    assert float(c.itemcget(item, "width")) == limit and x2 - x1 <= limit + 2
    assert y2 - y1 > 1.5 * theme.font("empty_sub").metrics("linespace")  # wrapped onto more lines


# ---------- folder view ----------

@pytest.fixture
def folders(shown):
    window, model = shown
    window.show_folders.set(True)
    window.toggle_folders()
    return window, model


def test_at_vcs_032_folder_view_groups_files_and_is_remembered(root, world, tmp_path):  # noqa: F811
    alpha_like(world)
    store = SettingsStore(tmp_path / "settings.json")
    world.save_settings = store.save
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    window.show_folders.set(True)
    window.toggle_folders()
    unversioned = [r for r in window.file_list.rows() if r.group is Group.UNVERSIONED]
    assert [(r.kind, r.path, r.x) for r in unversioned] == [("folder", "new", 28), ("file", "new/a.txt", 68), ("file", "new/b.txt", 68)]
    assert unversioned[0].pieces == [("new", "folder_name"), ("2 pliki", "folder_count")]
    readme = by_path(window, Group.CHANGES, "README.md")
    assert (readme.x, readme.pieces) == (46, [("README.md", "file_name")])
    assert store.load().show_folders is True


def test_des_vcs_045_folders_come_before_root_files(folders):
    window, _ = folders
    staged = [(r.kind, r.path) for r in window.file_list.rows() if r.group is Group.UNVERSIONED]
    assert staged[0] == ("folder", "new")


def test_at_vcs_033_plus_on_a_hovered_folder_stages_all_its_files(folders, world):
    window, model = folders
    node = by_path(window, Group.UNVERSIONED, "new")
    window.file_list.hover(node.top + 5)
    assert window.file_list.action_glyph() == "+"
    window.file_list.click_action()
    world.worker.settle()
    assert [c.path for c in model.files(Group.STAGED) if c.path.startswith("new/")] == ["new/a.txt", "new/b.txt"]
    assert model.files(Group.UNVERSIONED) == []


def test_des_vcs_045_minus_in_staged_and_space_on_a_folder(folders, world):
    window, model = folders
    window.file_list.select_key((Group.UNVERSIONED, "new"))
    window.file_list.press_space()
    world.worker.settle()
    window.file_list.select_key((Group.STAGED, "new"))
    assert window.file_list.action_glyph() == "−"
    window.file_list.press_space()
    world.worker.settle()
    assert [c.path for c in model.files(Group.UNVERSIONED)] == ["new/a.txt", "new/b.txt"]


def test_des_vcs_045_double_click_and_arrows_collapse_a_folder(folders):
    window, _ = folders
    node = by_path(window, Group.UNVERSIONED, "new")
    window.file_list.double_click(node.top + 5)
    assert [r.path for r in window.file_list.rows() if r.group is Group.UNVERSIONED] == ["new"]
    assert by_path(window, Group.UNVERSIONED, "new").collapsed
    window.file_list.select_key(node.key)
    window.file_list.press_right()
    assert len([r for r in window.file_list.rows() if r.group is Group.UNVERSIONED]) == 3
    window.file_list.press_left()
    assert len([r for r in window.file_list.rows() if r.group is Group.UNVERSIONED]) == 1


def test_des_vcs_045_polish_plural_of_files():
    from vcs_lite.ui.file_list import files_label
    assert [files_label(n) for n in (1, 2, 4, 5, 12, 22, 25)] == ["1 plik", "2 pliki", "4 pliki", "5 plików", "12 plików", "22 pliki", "25 plików"]
