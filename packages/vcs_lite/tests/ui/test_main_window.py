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
    assert [(r.name, r.line, r.badge) for r in window.sidebar.rows()] == [("alpha", "main", ("1", "count")), ("beta", "main", None)]
    assert window.file_list.winfo_exists()
    assert window.commit_button.cget("text") == "Commit"
    assert str(window.commit_button.cget("state")) == "disabled"


def test_des_vcs_023_repo_list_follows_model_changes(root, world):
    a = world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    a.write("one.py", "1\n"); a.write("two.py", "2\n")
    model.refresh_all(); world.worker.settle()
    assert window.sidebar.rows()[0].badge == ("2", "count")


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


def test_des_vcs_042_toolbar_title_and_status_bar_follow_the_selection(root, world):
    world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    root.update_idletasks()
    assert window.repo_title.cget("text") == "alpha"
    assert window.branch_chip.text == "⎇ main → brak upstreamu"
    assert window.winfo_toplevel().title() == "vcs-lite — alpha"
    assert window.refreshed.cget("text").startswith("Odświeżono ")
    assert str(window.pull_button.cget("state")) == "disabled"


def test_des_vcs_042_conflict_chip_follows_the_branch_chip_in_red(root, world):
    r = world.repo("gamma")
    r.write("f.txt", "base\n"); r.commit("base")
    r.git("checkout", "-q", "-b", "other"); r.write("f.txt", "other\n"); r.commit("other")
    r.git("checkout", "-q", "main"); r.write("f.txt", "main\n"); r.commit("main")
    r.git("merge", "-q", "other", check=False)
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    chip = window.conflict_chip
    assert chip.text == "1 plik w konflikcie"
    slaves = chip.master.pack_slaves()
    assert slaves.index(chip) == slaves.index(window.branch_chip) + 1
    texts = [i for i in chip.find_all() if chip.type(i) == "text"]
    assert [chip.itemcget(i, "fill") for i in texts] == ["#c2302a"]
    assert {chip.itemcget(i, "fill") for i in chip.find_all() if chip.type(i) != "text"} == {"#fbe3e1"}
    assert chip.tk.call("font", "actual", chip.itemcget(texts[0], "font"), "-weight") == "bold"
    r.write("f.txt", "main\n"); r.git("add", "f.txt")
    model.refresh_all(); world.worker.settle()
    assert chip.text == "" and not chip.winfo_manager()


def test_des_vcs_042_merge_chip_is_blue_and_takes_the_place_of_the_conflict_chip(root, world):
    r = conflicted(world, "gamma")
    model = world.start("gamma")
    window = MainWindow(root, model)
    world.select("gamma")
    assert window.conflict_chip.winfo_manager() and not window.merge_chip.winfo_manager()
    r.write("f.txt", "main\n"); r.git("add", "f.txt")
    model.refresh_all(); world.worker.settle()
    chip = window.merge_chip
    assert chip.text == "merge gotowy do commita" and not window.conflict_chip.winfo_manager()
    slaves = chip.master.pack_slaves()
    assert slaves.index(chip) == slaves.index(window.branch_chip) + 1
    texts = [i for i in chip.find_all() if chip.type(i) == "text"]
    assert [chip.itemcget(i, "fill") for i in texts] == ["#0a66d8"]
    assert {chip.itemcget(i, "fill") for i in chip.find_all() if chip.type(i) != "text"} == {"#e3eefc"}
    assert chip.tk.call("font", "actual", chip.itemcget(texts[0], "font"), "-weight") == "bold"
    assert [r.dot for r in window.sidebar.rows()] == ["#b4690e"]


def test_des_vcs_042_commit_button_is_the_default_button_only_while_it_can_commit(root, world):
    r = world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    assert window.commit_button.cget("text") == "Commit do alpha"
    assert window.reason.cget("text") == "ⓘ Brak plików w Staged."
    # aqua paints a default button blue in an inactive window even when it is disabled (zrzut 2026-10-22)
    assert str(window.commit_button.cget("default")) == "normal"
    r.write("a.py", "a\n"); r.git("add", "a.py")
    model.refresh_all(); world.worker.settle()
    window.type_message("fix")
    assert str(window.commit_button.cget("state")) == "normal"
    assert str(window.commit_button.cget("default")) == "active"


def test_des_vcs_042_placeholder_is_shown_but_never_becomes_the_message(root, world):
    world.repo("alpha")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    assert window.message_box.get("1.0", "end-1c").startswith("Opis zmian…")
    assert model.message == ""


def test_at_vcs_023_typed_drafts_stay_with_their_repository(root, world):
    world.repo("alpha"); world.repo("beta")
    model = world.start("alpha", "beta")
    window = MainWindow(root, model)
    world.select("alpha")
    window.type_message("wip alpha")
    world.select("beta")
    window.type_message("wip beta")
    world.select("alpha")
    assert window.message_box.get("1.0", "end-1c") == "wip alpha" and model.message == "wip alpha"


def test_des_vcs_042_reason_line_disappears_when_commit_is_possible(root, world):
    r = world.repo("alpha")
    r.write("README.md", "changed\n"); r.git("add", "README.md")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    root.update_idletasks()
    assert window.reason.winfo_manager() == "grid"
    window.type_message("fix")
    root.update_idletasks()
    assert window.reason.winfo_manager() == ""


def test_des_vcs_042_buttons_blend_into_their_panel(root, world):
    world.repo("alpha")
    window = MainWindow(root, world.start("alpha"))
    for b in (window.pull_button, window.refresh_button, window.commit_button, window.commit_push_button):
        assert b.cget("highlightbackground") == "#fafafb"
    assert window.settings_button.cget("highlightbackground") == "#f2f2f5"


# ---------- sidebar (UI-REFERENCE §4, P2, P4, P5, P6) ----------

def conflicted(world, name):
    r = world.repo(name)
    r.write("f.txt", "base\n"); r.commit("base")
    r.git("checkout", "-q", "-b", "other"); r.write("f.txt", "other\n"); r.commit("other")
    r.git("checkout", "-q", "main"); r.write("f.txt", "main\n"); r.commit("main")
    r.git("merge", "-q", "other", check=False)
    return r


def test_des_vcs_023_sidebar_draws_state_line_badge_and_selection(root, world):
    world.repo("alpha").write("a.py", "a\n")
    world.repo("beta")
    conflicted(world, "gamma")
    model = world.start("alpha", "beta", "gamma", "delta")
    window = MainWindow(root, model)
    world.select("alpha")
    rows = window.sidebar.rows()
    assert [(r.name, r.line, r.badge, r.selected) for r in rows] == [
        ("alpha", "main", ("1", "count"), True),
        ("beta", "main", None, False),
        ("gamma", "main · merge", ("konflikt", "conflict"), False),
        ("delta", "niedostępne", None, False),
    ]
    assert [r.dot for r in rows] == ["#b4690e", "#9fd3ad", "#c2302a", "#c7c7cc"]
    canvas = window.sidebar.canvas
    selection = canvas.find_withtag("selection")
    assert selection and {canvas.itemcget(i, "fill") for i in selection} == {"#0a66d8"}
    top = min(canvas.coords(i)[1] for i in selection)
    assert top == rows[0].top  # one selection shape, on the selected row


def test_des_vcs_023_sidebar_scrolls_when_repositories_do_not_fit(root, world):
    names = [f"repo{i:02}" for i in range(15)]
    for name in names:
        world.repo(name)
    model = world.start(*names)
    window = MainWindow(root, model)
    c = window.sidebar.canvas
    rows = window.sidebar.rows()
    assert float(c.cget("scrollregion").split()[3]) >= rows[-1].top + 48  # the last row is inside the region
    assert c.bind("<MouseWheel>")  # Tk delivers no events to the hidden test window: bound, then run
    window.sidebar.scroll(-5)
    shift = c.canvasy(0)
    assert shift > 0
    last = rows[-1]
    window.sidebar.click(int(last.top - shift + 5))  # a click is read in canvas coordinates
    assert model.selected == last.name


def test_des_vcs_023_clicking_a_row_selects_that_repository(root, world):
    world.repo("alpha"); world.repo("beta")
    model = world.start("alpha", "beta")
    window = MainWindow(root, model)
    beta = window.sidebar.rows()[1]
    window.sidebar.click(beta.top + 10)
    world.worker.settle()
    assert model.selected == "beta"
    assert window.sidebar.name_at(beta.top - 1) is None  # the 2 pt gap between rows selects nothing


def test_des_vcs_023_empty_sidebar_says_none(root, world):
    window = MainWindow(root, world.start())
    assert window.sidebar.rows() == [] and window.sidebar.empty_text == "Brak"


def test_des_vcs_023_long_names_are_shortened_to_fit(root, world):
    world.repo("a-very-long-repository-name-that-does-not-fit")
    window = MainWindow(root, world.start("a-very-long-repository-name-that-does-not-fit"))
    shown = window.sidebar.rows()[0].shown_name
    assert shown.endswith("…") and len(shown) < 40


def test_des_vcs_023_short_lists_do_not_scroll(root, world, monkeypatch):
    """Zrzut 2026-10-22: the wheel moved a list shorter than its window down into empty space."""
    world.repo("alpha").write("a.py", "a\n")
    model = world.start("alpha")
    window = MainWindow(root, model)
    world.select("alpha")
    for canvas, scroll in ((window.file_list.canvas, window.file_list.scroll), (window.sidebar.canvas, window.sidebar.scroll)):
        monkeypatch.setattr(canvas, "winfo_height", lambda: 600)  # a tall window; the hidden test one has no height
        for delta in (-5, +5):
            scroll(delta)
            assert canvas.canvasy(0) == 0
