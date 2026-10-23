"""The search window E-04 and how the main window opens it (REQ-VCS-033, DES-VCS-057, DEC-VCS-097).

Tk delivers no keys or clicks to the hidden test window, so handlers are called directly and bindings are
checked to exist.
"""

from __future__ import annotations

import pytest
from test_main_window import root, world  # noqa: F401 - shared fixtures

from vcs_lite.app.search import DEBOUNCE_MS
from vcs_lite.core.search import SearchQuery
from vcs_lite.ui import theme
from vcs_lite.ui.keys import DoubleShift
from vcs_lite.ui.main_window import MainWindow

C = theme.COLORS


class Clock:
    def __init__(self):
        self.ms = 0.0

    def __call__(self) -> float:
        return self.ms


@pytest.fixture
def shown(root, world):  # noqa: F811
    r = world.repo("alpha")
    r.write("notatki.md", "Żółw idzie w las\n")
    r.write("src/app.py", "w = 1\n")
    r.write("docs/plan.md", "# Plan\n\nWstęp.\n\nTydzień próbny.\n")
    r.commit("files")
    r.write("src/app.py", "w = 2\n")   # changed, so its name is coloured
    model = world.start("alpha")
    session = world.search_session()
    window = MainWindow(root, model, search=session)
    world.select("alpha")
    return window, session, r


def settle(world):  # noqa: F811
    world.timers.advance(DEBOUNCE_MS)
    world.worker.settle()


def type_into(dialog, world, text):  # noqa: F811
    dialog.phrase.set(text)
    settle(world)


def tap_shift(window, clock, after=50):
    clock.ms += after
    window.key_pressed("Shift_L")
    clock.ms += 30
    window.key_released("Shift_L")


# ---------- opening (AT-VCS-044) ----------

def test_at_vcs_044_double_shift_opens_the_window_but_shift_with_a_letter_or_click_does_not(shown, world):  # noqa: F811
    window, session, _ = shown
    clock = Clock()
    window.double_shift = DoubleShift(window.open_search, clock=clock)
    session.set_query(SearchQuery("w")); settle(world)            # the query of an earlier opening
    tap_shift(window, clock); tap_shift(window, clock)
    dialog = window.search_dialog
    assert dialog is not None and dialog.title() == "Szukaj w plikach — alpha" and dialog.phrase.get() == "w"
    dialog.close()
    assert window.search_dialog is None
    window.key_pressed("Shift_L"); window.key_pressed("A"); window.key_released("A"); window.key_released("Shift_L")
    tap_shift(window, clock)
    assert window.search_dialog is None
    window.key_pressed("Shift_L"); window.pointer_pressed(); window.key_released("Shift_L")
    tap_shift(window, clock)
    assert window.search_dialog is None


def test_des_vcs_057_main_window_listens_to_keys_clicks_and_the_menu(shown):
    window, _, _ = shown
    top = window.winfo_toplevel()
    assert all(top.bind(sequence) for sequence in ("<KeyPress>", "<KeyRelease>", "<ButtonPress>"))
    assert top.bind("<Command-Shift-F>") and top.bind("<Command-Shift-f>")
    assert window.edit_menu.entrycget(0, "label") == "Szukaj w plikach…"
    assert window.edit_menu.entrycget(0, "accelerator") == "Command-Shift-F"


def test_des_vcs_057_nothing_opens_without_a_selected_repository(root, world):  # noqa: F811
    world.repo("alpha")
    window = MainWindow(root, world.start("alpha"), search=world.search_session())
    assert window.open_search() is None


def test_des_vcs_057_opening_again_brings_back_the_same_window(shown):
    window, _, _ = shown
    first = window.open_search()
    assert window.open_search() is first
    first.close()


# ---------- the query ----------

def test_des_vcs_057_phrase_toggles_and_mask_make_the_query(shown, world):  # noqa: F811
    window, session, _ = shown
    dialog = window.open_search()
    dialog.phrase.set("w")
    dialog.word_toggle.click()
    dialog.mask.set("md")
    assert session.query == SearchQuery("w", whole_word=True, mask="md")
    dialog.case_toggle.click()
    assert session.query.case_sensitive and dialog.case_toggle.on
    dialog.close()


def test_des_vcs_057_toggles_have_command_option_shortcuts_that_type_nothing(shown):
    window, session, _ = shown
    dialog = window.open_search()
    for sequence in ("<Command-Option-c>", "<Command-Option-w>"):
        assert dialog.phrase_entry.bind(sequence) and dialog.mask_entry.bind(sequence)
    assert dialog.toggle_case() == "break" and session.query.case_sensitive
    assert dialog.toggle_word() == "break" and session.query.whole_word
    dialog.close()


# ---------- results ----------

def test_at_vcs_041_window_lists_whole_word_matches_with_marks(shown, world):  # noqa: F811
    window, _, _ = shown
    dialog = window.open_search()
    dialog.word_toggle.click()
    dialog.mask.set("md")
    type_into(dialog, world, "w")
    rows = dialog.results.rows()
    assert [(r.path, r.line, r.text) for r in rows] == [("notatki.md", 1, "Żółw idzie w las")]
    assert dialog.results.hit_count() == 1
    assert dialog.status_text() == ("1 trafienie w 1 pliku", C["dim"])
    dialog.close()


def test_des_vcs_057_file_names_take_their_status_colour(shown, world):  # noqa: F811
    window, _, _ = shown
    dialog = window.open_search()
    type_into(dialog, world, "w")
    colours = {r.path: r.color for r in dialog.results.rows()}
    assert colours["src/app.py"] == C["file_mod"] and colours["notatki.md"] == C["ink"]
    dialog.close()


def test_des_vcs_057_arrows_move_the_selection_and_enter_opens_and_closes(shown, world):  # noqa: F811
    window, session, r = shown
    dialog = window.open_search()
    type_into(dialog, world, "w")
    assert dialog.results.selected == 0
    dialog.press_down()
    assert dialog.results.selected == 1 == session.selected
    dialog.press_up()
    dialog.press_return()
    world.worker.settle()
    [call] = world.md_reader.calls          # docs/plan.md comes first: "Wstęp" matches without whole word
    assert window.search_dialog is None and call["right"] == r.path / "docs" / "plan.md" and call["line"] == 3


def test_des_vcs_057_double_click_on_a_row_opens_it(shown, world):  # noqa: F811
    window, _, r = shown
    dialog = window.open_search()
    type_into(dialog, world, "w = 2")
    dialog.results.double_click(dialog.results.rows()[0].top + 5)
    world.worker.settle()
    assert world.text_reader.calls[0]["right"] == r.path / "src" / "app.py" and window.search_dialog is None


def test_des_vcs_057_escape_closes_and_stops_searching(shown, world):  # noqa: F811
    window, session, _ = shown
    dialog = window.open_search()
    dialog.phrase.set("w")
    dialog.press_escape()
    assert window.search_dialog is None and not session.searching and world.timers.pending == 0
    session.set_query(SearchQuery("x")); settle(world)   # the closed window no longer listens


def test_des_vcs_057_hint_no_matches_and_warning_texts(shown, world):  # noqa: F811
    window, session, _ = shown
    dialog = window.open_search()
    assert dialog.placeholder_texts() == ["Wpisz frazę. Szukam w plikach śledzonych przez git, w ich obecnej postaci na dysku."]
    type_into(dialog, world, "nie ma takiego")
    assert dialog.placeholder_texts() == ["⌕", "Brak trafień", "„nie ma takiego” we wszystkich plikach."]
    dialog.phrase.set("w")
    assert dialog.status_text() == ("Szukam…", C["dim"])
    dialog.close()


def test_des_vcs_057_git_error_shows_the_banner(shown, world):  # noqa: F811
    window, session, r = shown
    dialog = window.open_search()
    (r.path / ".git").rename(r.path / ".git-gone")
    type_into(dialog, world, "w")
    assert dialog.error_text().startswith("fatal:") and "not a git repository" in dialog.error_text()
    (r.path / ".git-gone").rename(r.path / ".git")
    dialog.close()


def test_des_vcs_057_double_shift_inside_selects_the_phrase(shown, world):  # noqa: F811
    window, _, _ = shown
    dialog = window.open_search()
    dialog.phrase.set("tydzień")
    dialog.double_shift_pressed()
    assert dialog.phrase_entry.selection_present()
    dialog.close()


def test_des_vcs_057_long_lines_are_shortened_to_the_row(shown, world):  # noqa: F811
    window, _, r = shown
    r.write("long.txt", "w" + " słowo" * 300 + "\n"); r.commit("long")
    dialog = window.open_search()
    dialog.word_toggle.click()
    type_into(dialog, world, "w")
    long_row = next(row for row in dialog.results.rows() if row.path == "long.txt")
    assert dialog.results.shown_text(long_row).endswith("…")
    dialog.close()
