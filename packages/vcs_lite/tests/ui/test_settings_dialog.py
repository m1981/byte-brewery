"""Repository dialog E-02 after the reference (UI-REFERENCE §8, P8)."""

from __future__ import annotations

from conftest import Repo
from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.app.model import AppModel
from vcs_lite.core.settings import Settings
from vcs_lite.ui.main_window import MainWindow


def rootdir_with_repos(world):  # noqa: F811
    for name in ("gamma", "alpha", "beta"):
        world.repo(name)
    (world.root / "zdjecia").mkdir()
    hidden = Repo(world.root / ".ukryte")
    hidden.path.mkdir()
    (hidden.path / ".git").mkdir()


def test_at_vcs_022_dialog_lists_repositories_with_current_choice(root, world):  # noqa: F811
    rootdir_with_repos(world)
    window = MainWindow(root, world.start("alpha"))
    dialog = window.open_settings()
    assert dialog.title() == "Repozytoria do obserwowania"
    assert dialog.path_text == str(world.root)
    assert [(name, var.get()) for name, var in dialog.checks] == [("alpha", True), ("beta", False), ("gamma", False)]
    assert dialog.count.cget("text") == "Zaznaczono 1 z 3"
    dialog.cancel()


def test_des_vcs_043_count_follows_the_checkboxes(root, world):  # noqa: F811
    rootdir_with_repos(world)
    window = MainWindow(root, world.start("alpha"))
    dialog = window.open_settings()
    dict(dialog.checks)["gamma"].set(True)
    dialog.update_count()
    assert dialog.count.cget("text") == "Zaznaczono 2 z 3"
    dialog.cancel()


def test_at_vcs_001_save_applies_the_choice_and_closes(root, world):  # noqa: F811
    rootdir_with_repos(world)
    model = world.start("alpha")
    window = MainWindow(root, model)
    dialog = window.open_settings()
    checks = dict(dialog.checks)
    checks["alpha"].set(False); checks["beta"].set(True); checks["gamma"].set(True)
    dialog.save()
    world.worker.settle()
    assert model.repo_names == ["beta", "gamma"]
    assert not dialog.winfo_exists()
    assert [r.name for r in window.sidebar.rows()] == ["beta", "gamma"]


def test_uc_vcs_01_cancel_changes_nothing(root, world):  # noqa: F811
    rootdir_with_repos(world)
    model = world.start("alpha")
    window = MainWindow(root, model)
    dialog = window.open_settings()
    dict(dialog.checks)["beta"].set(True)
    dialog.cancel()
    assert model.repo_names == ["alpha"] and not dialog.winfo_exists()


def test_req_vcs_018_missing_repository_is_listed_greyed_and_can_be_removed(root, world):  # noqa: F811
    rootdir_with_repos(world)
    model = world.start("alpha", "delta")
    window = MainWindow(root, model)
    dialog = window.open_settings()
    assert dialog.checks[-1][0] == "delta" and dialog.checks[-1][1].get() is True
    assert "niedostępne" in dialog.notes["delta"]
    dict(dialog.checks)["delta"].set(False)
    dialog.save()
    assert model.repo_names == ["alpha"]


def test_uc_vcs_01_missing_rootdir_shows_the_error_and_blocks_saving(root, world, tmp_path):  # noqa: F811
    model = AppModel(Settings(rootdir=str(tmp_path / "nope")), git=world.git, diff_tool=world.tool,
                     worker=world.worker, confirm=lambda title, message: True)
    window = MainWindow(root, model)
    dialog = window.open_settings()
    assert "Katalog z repozytoriami nie istnieje" in dialog.error_text
    assert str(dialog.save_button.cget("state")) == "disabled"
    dialog.cancel()


def test_des_vcs_043_both_buttons_open_the_dialog(root, world):  # noqa: F811
    window = MainWindow(root, world.start())
    assert str(window.settings_button.cget("state")) == "normal"
    assert window.file_list.empty_action_enabled()
    window.file_list.run_empty_action()
    assert window.settings_dialog is not None and window.settings_dialog.winfo_exists()
    window.settings_dialog.cancel()


def test_des_vcs_042_long_folder_path_is_shortened_in_the_middle_to_keep_420(root, world, tmp_path):  # noqa: F811
    deep = tmp_path / ("very-long-folder-name-" * 6) / "PycharmProjects"
    deep.mkdir(parents=True)
    model = AppModel(Settings(rootdir=str(deep)), git=world.git, diff_tool=world.tool,
                     worker=world.worker, confirm=lambda title, message: True)
    window = MainWindow(root, model)
    dialog = window.open_settings()
    assert "…" in dialog.path_shown and dialog.path_shown.endswith("PycharmProjects")
    assert dialog.winfo_reqwidth() <= 420 + 2
    dialog.cancel()


def test_des_vcs_042_short_folder_path_is_shown_whole(tk_root):  # noqa: F811
    from vcs_lite.ui import theme
    from vcs_lite.ui.widgets import elide_middle
    font = theme.font("path")
    assert elide_middle("~/PycharmProjects", font, 300) == "~/PycharmProjects"
    shortened = elide_middle("/a/very/long/path/to/the/folder/PycharmProjects", font, 150)
    assert shortened.startswith("/a/") and shortened.endswith("Projects") and font.measure(shortened) <= 150


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def test_des_vcs_042_wheel_scrolls_the_list_over_the_names_too(root, world):  # noqa: F811
    for i in range(20):
        world.repo(f"repo{i:02}")
    window = MainWindow(root, world.start("repo00"))
    dialog = window.open_settings()
    canvas = dialog.list_canvas
    dialog.update_idletasks()
    check = next(w for w in descendants(canvas) if w.winfo_class() == "Checkbutton")
    check.event_generate("<MouseWheel>", delta=-3)
    assert canvas.yview()[0] > 0
    [rows] = canvas.find_all()
    assert float(canvas.itemcget(rows, "width")) == canvas.winfo_reqwidth()  # rows span the whole list
    dialog.cancel()
