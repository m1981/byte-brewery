"""git grep behind the TextSearcher port, on throwaway repositories (DES-VCS-054)."""

from __future__ import annotations

import pytest
from conftest import GIT_ENV

from vcs_lite.core.gitcli import GitCli
from vcs_lite.core.gitgrep import GitGrepSearcher
from vcs_lite.core.repo import GitError
from vcs_lite.core.search import Match, SearchQuery


def search(repo, text, *, limit=500, cancelled=lambda: False, **options):
    return GitGrepSearcher(GitCli(env=GIT_ENV)).search(repo.path, SearchQuery(text, **options), limit=limit,
                                                       cancelled=cancelled)


def hits(result):
    return [(m.path, m.line) for m in result.matches]


@pytest.fixture
def notes(repo):
    repo.write("notatki.md", "Żółw idzie w las\nŁÓDŹ\n")
    repo.write("src/app.py", "w = 1\n")
    repo.git("add", ".")
    return repo


def test_des_vcs_054_whole_word_with_polish_letters_and_mask(notes):
    result = search(notes, "w", whole_word=True, mask="md")
    assert result.matches == (Match("notatki.md", 1, "Żółw idzie w las", ((11, 12),)),)
    assert hits(search(notes, "w", whole_word=True)) == [("notatki.md", 1), ("src/app.py", 1)]


def test_des_vcs_054_case_is_ignored_unless_asked(notes):
    assert hits(search(notes, "łódź")) == [("notatki.md", 2)]
    assert hits(search(notes, "łódź", case_sensitive=True)) == []


def test_des_vcs_054_no_match_is_an_empty_result(notes):
    result = search(notes, "nic takiego")
    assert result.matches == () and not result.truncated


def test_des_vcs_054_working_copy_is_searched_but_not_untracked_or_binary_files(notes):
    notes.write("notatki.md", "teraz inaczej\n")          # tracked, changed on disk
    notes.write("nowy.md", "teraz\n")                     # untracked
    (notes.path / "bin.dat").write_bytes(b"teraz\0\1")
    notes.git("add", "bin.dat")
    assert hits(search(notes, "teraz")) == [("notatki.md", 1)]


def test_des_vcs_054_files_deleted_from_disk_are_skipped(notes):
    (notes.path / "notatki.md").unlink()
    assert hits(search(notes, "w")) == [("src/app.py", 1)]


def test_des_vcs_054_odd_paths_and_a_phrase_starting_with_a_dash(repo):
    repo.write("a b:c.md", "--force tu\n")
    repo.git("add", ".")
    assert hits(search(repo, "--force")) == [("a b:c.md", 1)]


def test_des_vcs_054_mask_ignores_the_case_of_the_extension(repo):
    repo.write("d/README.MD", "x\n"); repo.write("x.py", "x\n")
    repo.git("add", ".")
    assert hits(search(repo, "x", mask="*.md")) == [("d/README.MD", 1)]


def test_des_vcs_054_stops_at_the_limit(repo):
    repo.write("many.txt", "hit\n" * 50)
    repo.git("add", ".")
    result = search(repo, "hit", limit=10)
    assert len(result.matches) == 10 and result.truncated


def test_des_vcs_054_exactly_the_limit_is_not_truncated(repo):
    repo.write("many.txt", "hit\n" * 10)
    repo.git("add", ".")
    assert not search(repo, "hit", limit=10).truncated


def test_des_vcs_054_cancelled_search_stops_reading(repo):
    repo.write("many.txt", "hit\n" * 50)
    repo.git("add", ".")
    seen = []
    result = search(repo, "hit", cancelled=lambda: seen.append(1) or len(seen) > 3)
    assert len(result.matches) == 3 and not result.truncated


def test_des_vcs_054_long_lines_are_clipped_around_the_match(repo):
    repo.write("min.js", "a" * 5000 + "HIT" + "b" * 5000 + "\n")
    repo.git("add", ".")
    [m] = search(repo, "hit").matches
    assert m.cut_start and m.cut_end and len(m.text) == 300 and m.text[m.spans[0][0]:m.spans[0][1]] == "HIT"


def test_des_vcs_054_git_failure_is_an_error(tmp_path):
    class NotARepo:
        path = tmp_path
    with pytest.raises(GitError, match="not a git repository"):
        search(NotARepo, "x")
