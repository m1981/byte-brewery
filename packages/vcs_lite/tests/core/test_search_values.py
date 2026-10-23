"""Search values without I/O: the query, the file mask, word boundaries and clipped lines (DES-VCS-052)."""

from __future__ import annotations

import pytest

from vcs_lite.core.search import CLIP_LEAD, CLIP_LIMIT, Match, SearchQuery, SearchResult, clip_line, match_spans


@pytest.mark.parametrize("mask", ["md, py", "*.md; *.py", ".md .py", "MD,,py", "md py md"])
def test_des_vcs_052_mask_spellings_mean_the_same_extensions(mask):
    assert SearchQuery("x", mask=mask).extensions == ("md", "py")


def test_des_vcs_052_empty_mask_means_every_file():
    assert SearchQuery("x").extensions == ()
    assert SearchQuery("x", mask="  ;, ").pathspecs == ()


def test_des_vcs_052_pathspecs_match_any_folder_and_any_case():
    assert SearchQuery("x", mask="md").pathspecs == (":(glob,icase)**/*.md",)


def test_des_vcs_052_glob_characters_of_the_mask_stay_literal():
    assert SearchQuery("x", mask="a*b, c?[d]").pathspecs == (r":(glob,icase)**/*.a\*b", r":(glob,icase)**/*.c\?\[d]")


def test_des_vcs_052_whole_word_respects_polish_letters():
    query = SearchQuery("w", whole_word=True)
    assert match_spans("Żółw idzie w las, a żółwie zostają.", query) == [(11, 12)]


def test_des_vcs_052_without_whole_word_every_occurrence_counts():
    assert match_spans("Żółw idzie w las", SearchQuery("w")) == [(3, 4), (11, 12)]


def test_des_vcs_052_case_is_ignored_by_default_also_for_polish_letters():
    assert match_spans("ŁÓDŹ i łódź", SearchQuery("łódź")) == [(0, 4), (7, 11)]


def test_des_vcs_052_case_sensitive_matches_exactly():
    assert match_spans("ŁÓDŹ i łódź", SearchQuery("łódź", case_sensitive=True)) == [(7, 11)]


def test_des_vcs_052_whole_word_boundaries_only_where_the_phrase_has_word_characters():
    query = SearchQuery("foo(", whole_word=True)
    assert match_spans("foo(1) xfoo(2) foo(3)", query) == [(0, 4), (15, 19)]


def test_des_vcs_052_regex_characters_of_the_phrase_are_literal():
    assert match_spans("a.b axb a.b", SearchQuery("a.b")) == [(0, 3), (8, 11)]


def test_des_vcs_052_empty_phrase_matches_nothing():
    assert match_spans("anything", SearchQuery("")) == []
    assert not SearchQuery("   ").active


def test_des_vcs_052_short_line_loses_only_its_leading_whitespace():
    assert clip_line("    x = 1", [(4, 5)]) == ("x = 1", [(0, 1)], False, False)


def test_des_vcs_052_long_line_is_cut_around_the_first_match():
    text = "a" * 1000 + "HIT" + "b" * 1000
    shown, spans, cut_start, cut_end = clip_line(text, [(1000, 1003)])
    assert (len(shown), cut_start, cut_end) == (CLIP_LIMIT, True, True)
    assert spans == [(CLIP_LEAD, CLIP_LEAD + 3)] and shown[CLIP_LEAD:CLIP_LEAD + 3] == "HIT"


def test_des_vcs_052_spans_outside_the_clipped_part_are_dropped_or_trimmed():
    text = "HIT" + "x" * 400 + "HIT"
    shown, spans, cut_start, cut_end = clip_line(text, [(0, 3), (403, 406)])
    assert (spans, cut_start, cut_end) == ([(0, 3)], False, True) and len(shown) == CLIP_LIMIT


def test_des_vcs_052_result_counts_files():
    m = [Match("a.md", 1, "x", ((0, 1),)), Match("a.md", 2, "x", ((0, 1),)), Match("b.md", 1, "x", ((0, 1),))]
    assert SearchResult(tuple(m)).file_count == 2
