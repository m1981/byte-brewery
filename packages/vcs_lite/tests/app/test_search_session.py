"""The search window's state without Tk: delay, stale results, opening matches (REQ-VCS-033, DES-VCS-055)."""

from __future__ import annotations

import pytest
from world import World

from vcs_lite.app.search import DEBOUNCE_MS, LIMIT, SearchSession
from vcs_lite.core.search import Match, SearchQuery, SearchResult


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


@pytest.fixture
def alpha(world):
    r = world.repo("alpha")
    r.write("notatki.md", "Żółw idzie w las\n")
    r.write("src/app.py", "w = 1\n")
    r.write("docs/plan.md", "# Plan\n\nWstęp.\n\nTydzień próbny.\n")
    r.commit("files")
    world.start("alpha")
    world.select("alpha")
    return r


def typed(world, session, text, **options):
    """The user types a query and stops for longer than the delay."""
    session.set_query(SearchQuery(text, **options))
    world.timers.advance(DEBOUNCE_MS)
    world.worker.settle()


def hits(session):
    return [(m.path, m.line) for m in session.result.matches]


class ScriptedSearcher:
    """Answers each query with the result given for its text, and remembers what it was asked."""

    def __init__(self, answers: dict[str, SearchResult] | None = None):
        self.answers = answers or {}
        self.asked: list[str] = []
        self.cancel_flags = []

    def search(self, repo, query, *, limit, cancelled):
        self.asked.append(query.text)
        self.cancel_flags.append(cancelled)
        return self.answers.get(query.text, SearchResult())


def result(*paths: str, truncated: bool = False) -> SearchResult:
    return SearchResult(tuple(Match(p, 1, "x", ((0, 1),)) for p in paths), truncated)


# ---------- scenarios ----------

def test_at_vcs_041_whole_word_with_polish_letters_and_file_mask(world, alpha):
    session = world.search_session()
    typed(world, session, "w", whole_word=True, mask="md")
    assert hits(session) == [("notatki.md", 1)] and session.result.matches[0].spans == ((11, 12),)
    typed(world, session, "w", whole_word=True)
    assert hits(session) == [("notatki.md", 1), ("src/app.py", 1)]
    typed(world, session, "ŻÓŁW", case_sensitive=True)
    assert hits(session) == []


def test_at_vcs_042_enter_opens_markdown_and_text_at_the_line(world, alpha):
    session = world.search_session()
    typed(world, session, "próbny")
    assert session.selected_match.path == "docs/plan.md"
    assert session.open() is True
    world.worker.settle()
    [call] = world.md_reader.calls
    assert call["right"] == alpha.path / "docs" / "plan.md" and call["line"] == 5
    typed(world, session, "w = 1")
    session.open()
    world.worker.settle()
    [text] = world.text_reader.calls
    assert text["right"] == alpha.path / "src" / "app.py" and text["line"] == 1 and world.opened == []


def test_at_vcs_043_search_waits_for_a_pause_and_drops_stale_results(world, alpha):
    searcher = ScriptedSearcher({"tyd": result("old.md"), "tydzień": result("new.md")})
    session = world.search_session(searcher)
    session.set_query(SearchQuery("tyd"))
    world.timers.advance(100)
    session.set_query(SearchQuery("tydzień"))
    world.timers.advance(DEBOUNCE_MS - 1)
    assert world.worker.queued == [] and session.searching
    world.timers.advance(1)
    world.worker.settle()
    assert searcher.asked == ["tydzień"]
    assert hits(session) == [("new.md", 1)] and not session.searching


def test_at_vcs_043_a_result_arriving_after_a_newer_query_is_ignored(world, alpha):
    searcher = ScriptedSearcher({"tyd": result("old.md"), "tydzień": result("new.md")})
    session = world.search_session(searcher)
    session.set_query(SearchQuery("tyd")); world.timers.advance(DEBOUNCE_MS)            # running …
    session.set_query(SearchQuery("tydzień")); world.timers.advance(DEBOUNCE_MS)        # … when a newer one starts
    world.worker.step()    # the result of "tyd" arrives first
    assert session.result is None and session.searching
    world.worker.step()
    assert hits(session) == [("new.md", 1)] and not session.searching


def test_at_vcs_043_more_than_the_limit_shows_the_first_ones_and_a_warning(world, alpha):
    alpha.write("many.txt", "hit\n" * (LIMIT + 5)); alpha.commit("many")
    session = world.search_session()
    typed(world, session, "hit")
    assert len(session.result.matches) == LIMIT and session.result.truncated


# ---------- the session in detail ----------

def test_des_vcs_055_a_newer_search_cancels_the_running_one(world, alpha):
    searcher = ScriptedSearcher()
    session = world.search_session(searcher)
    session.set_query(SearchQuery("a")); world.timers.advance(DEBOUNCE_MS)
    session.set_query(SearchQuery("ab")); world.timers.advance(DEBOUNCE_MS)
    world.worker.settle()
    first, second = searcher.cancel_flags
    assert first() and not second()


def test_des_vcs_055_closing_cancels_the_pending_and_the_running_search(world, alpha):
    searcher = ScriptedSearcher()
    session = world.search_session(searcher)
    session.set_query(SearchQuery("a")); world.timers.advance(DEBOUNCE_MS)
    session.set_query(SearchQuery("ab"))
    session.close()
    assert world.timers.pending == 0 and not session.searching
    world.worker.settle()
    assert searcher.cancel_flags[0]() and session.result is None
    world.timers.advance(10 * DEBOUNCE_MS)
    assert searcher.asked == ["a"]   # nothing runs in the background after closing (REQ-VCS-101)


def test_des_vcs_055_blank_phrase_clears_the_result_without_searching(world, alpha):
    searcher = ScriptedSearcher({"a": result("x.md")})
    session = world.search_session(searcher)
    typed(world, session, "a")
    typed(world, session, "  ")
    assert session.result is None and not session.searching and searcher.asked == ["a"]


def test_des_vcs_055_reopening_searches_the_remembered_query_at_once_in_the_selected_repo(world, alpha):
    searcher = ScriptedSearcher({"a": result("x.md")})
    session = world.search_session(searcher)
    typed(world, session, "a")
    session.close()
    session.start()
    world.worker.settle()
    assert searcher.asked == ["a", "a"] and session.query == SearchQuery("a") and hits(session) == [("x.md", 1)]


def test_des_vcs_055_search_does_not_occupy_the_repository(world, alpha):
    searcher = ScriptedSearcher()
    session = world.search_session(searcher)
    session.set_query(SearchQuery("a")); world.timers.advance(DEBOUNCE_MS)
    assert not world.worker.busy("alpha")


def test_des_vcs_055_selection_moves_within_the_results_and_starts_at_the_first(world, alpha):
    session = world.search_session(ScriptedSearcher({"a": result("1.md", "2.md", "3.md")}))
    typed(world, session, "a")
    assert session.selected == 0
    session.move(-1); assert session.selected == 0
    session.move(+5); assert session.selected == 2
    session.select(1); assert session.selected_match.path == "2.md"


def test_des_vcs_055_nothing_to_open_without_a_match(world, alpha):
    session = world.search_session(ScriptedSearcher())
    typed(world, session, "a")
    assert session.selected_match is None and session.open() is False


def test_des_vcs_055_git_error_is_shown_and_clears_on_the_next_search(world, alpha):
    class Failing:
        def search(self, repo, query, *, limit, cancelled):
            from vcs_lite.core.gitcli import GitResult
            from vcs_lite.core.repo import GitError
            raise GitError(GitResult(("grep",), 128, b"", "fatal: zepsute"))
    session = world.search_session(Failing())
    typed(world, session, "a")
    assert session.error == "fatal: zepsute" and not session.searching


def test_des_vcs_055_listeners_hear_every_change(world, alpha):
    session = world.search_session(ScriptedSearcher())
    heard = []
    session.subscribe(lambda: heard.append(session.searching))
    typed(world, session, "a")
    assert heard[0] is True and heard[-1] is False


def test_des_vcs_055_no_selected_repository_means_no_search(world, alpha):
    searcher = ScriptedSearcher()
    session = SearchSession(searcher, world.worker, later=world.timers.later, repo=lambda: None,
                            open_match=lambda path, line: None)
    typed(world, session, "a")
    assert searcher.asked == [] and session.result is None and not session.searching


# ---------- the model's part (DES-VCS-055) ----------

def test_des_vcs_055_model_gives_the_change_of_a_path_for_its_colour(world, alpha):
    alpha.write("notatki.md", "zmiana\n")
    world.model.refresh("alpha"); world.worker.settle()
    assert world.model.change_of("notatki.md").code == "M" and world.model.change_of("src/app.py") is None
    assert world.model.selected_path == alpha.path


# ---------- what the window shows (DES-VCS-055) ----------

@pytest.mark.parametrize("matches, files, text", [
    (1, 1, "1 trafienie w 1 pliku"), (3, 1, "3 trafienia w 1 pliku"), (5, 2, "5 trafień w 2 plikach"),
    (12, 3, "12 trafień w 3 plikach"), (22, 4, "22 trafienia w 4 plikach")])
def test_des_vcs_055_status_counts_matches_and_files_in_polish(world, alpha, matches, files, text):
    paths = [f"{i % files}.md" for i in range(matches)]
    session = world.search_session(ScriptedSearcher({"a": result(*paths)}))
    typed(world, session, "a")
    assert session.status == (text, False)


def test_des_vcs_055_status_while_searching_and_when_truncated(world, alpha):
    session = world.search_session(ScriptedSearcher({"a": result("x.md", truncated=True)}))
    session.set_query(SearchQuery("a"))
    assert session.status == ("Szukam…", False)
    world.timers.advance(DEBOUNCE_MS); world.worker.settle()
    assert session.status == ("Pokazano pierwsze 500 trafień · zawęź frazę albo maskę plików", True)


def test_des_vcs_055_centre_text_for_an_empty_phrase_and_for_no_matches(world, alpha):
    session = world.search_session(ScriptedSearcher())
    assert session.placeholder == ("", "Wpisz frazę. Szukam w plikach śledzonych przez git, w ich obecnej postaci na dysku.")
    typed(world, session, "zażółć", case_sensitive=True, whole_word=True, mask="md, py")
    assert session.placeholder == ("Brak trafień",
                                   "„zażółć” w plikach *.md, *.py, z rozróżnianiem wielkości liter, całe słowo.")
    typed(world, session, "zażółć")
    assert session.placeholder == ("Brak trafień", "„zażółć” we wszystkich plikach.")
    assert session.status == ("0 trafień", False)


def test_des_vcs_055_a_closed_window_stops_listening(world, alpha):
    session = world.search_session(ScriptedSearcher())
    heard = []
    listener = lambda: heard.append(1)  # noqa: E731
    session.subscribe(listener)
    session.unsubscribe(listener)
    typed(world, session, "a")
    assert heard == []
