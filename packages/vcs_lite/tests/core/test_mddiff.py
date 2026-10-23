"""Markdown split into blocks and compared block by block, then word by word (REQ-VCS-031, DES-VCS-049).

The cases come from the demo shown to the user on 2026-10-23 (22 edge cases).
"""

from __future__ import annotations

from vcs_lite.core.mddiff import DEL_END, DEL_START, INS_END, INS_START, State, diff_blocks, mark_words, parse_blocks


def kinds(text: str) -> list[tuple[str, str]]:
    return [(b.kind, b.src) for b in parse_blocks(text)]


def states(old: str, new: str) -> list[tuple[str, str]]:
    return [(c.state.value, c.block.src) for c in diff_blocks(old, new)]


def readable(marked: str) -> str:
    return marked.replace(INS_START, "{+").replace(INS_END, "+}").replace(DEL_START, "{-").replace(DEL_END, "-}")


# ---------- blocks ----------

def test_des_vcs_049_headings_and_paragraphs_are_blocks_of_inline_markdown():
    blocks = parse_blocks("# Tytuł\n\nPierwszy **akapit**\nw dwóch liniach.\n")
    assert [(b.kind, b.tag, b.src) for b in blocks] == [("heading", "h1", "Tytuł"),
                                                         ("paragraph", "", "Pierwszy **akapit**\nw dwóch liniach.")]


def test_des_vcs_049_list_items_carry_depth_order_and_number_without_their_nested_list():
    blocks = parse_blocks("- a\n  - b\n\n1. c\n2. d\n")
    assert [(b.src, b.depth, b.ordered, b.number) for b in blocks] == [
        ("a", 1, False, ""), ("b", 2, False, ""), ("c", 1, True, "1"), ("d", 1, True, "2")]
    assert {b.kind for b in blocks} == {"item"}


def test_req_vcs_031_task_list_boxes_become_symbols():
    assert kinds("- [ ] napisać testy\n- [x] wdrożyć\n") == [("item", "☐ napisać testy"), ("item", "☑ wdrożyć")]


def test_des_vcs_049_table_rows_are_blocks_of_one_table():
    blocks = parse_blocks("| a | b |\n|---|---|\n| 1 | 2 |\n\ntekst\n\n| c |\n|---|\n| 3 |\n")
    assert [(b.kind, b.cells, b.table) for b in blocks if b.kind in ("header", "row")] == [
        ("header", ("a", "b"), 1), ("row", ("1", "2"), 1), ("header", ("c",), 2), ("row", ("3",), 2)]


def test_des_vcs_049_code_keeps_its_text_and_language():
    [code] = parse_blocks("```python\ndef f():\n    return 1\n```\n")
    assert (code.kind, code.tag, code.src) == ("code", "python", "def f():\n    return 1\n")


def test_des_vcs_049_front_matter_is_one_block():
    blocks = parse_blocks("---\ntitle: Plan\nstatus: draft\n---\n\n# Plan\n")
    assert [(b.kind, b.src) for b in blocks] == [("meta", "title: Plan\nstatus: draft"), ("heading", "Plan")]


def test_des_vcs_049_quoted_paragraphs_know_their_depth():
    [quoted] = parse_blocks("> Uwaga: wersja robocza.\n")
    assert (quoted.kind, quoted.quote) == ("paragraph", 1)


def test_des_vcs_049_raw_html_stays_text_for_the_renderer():
    blocks = parse_blocks("<script>alert('x')</script>\n")
    assert blocks and all(b.kind == "paragraph" for b in blocks)


# ---------- words ----------

def test_req_vcs_031_changed_words_are_marked_in_the_new_text():
    marked = mark_words("zmiany w kilku repozytoriach", "zmiany w wielu repozytoriach naraz")
    assert readable(marked) == "zmiany w {-kilku-} {+wielu+} repozytoriach {+naraz+}"


def test_req_vcs_031_punctuation_stands_apart_from_words():
    assert readable(mark_words("wersja robocza.", "wersja ostateczna.")) == "wersja {-robocza-} {+ostateczna+}."


def test_req_vcs_031_links_and_code_spans_stay_whole():
    marked = readable(mark_words("Zobacz [spec](docs/SPEC.md) i `uv run`.", "Zobacz [spec](docs/SPEC-v2.md) i `uv sync`."))
    assert marked == "Zobacz {-[spec](docs/SPEC.md)-} {+[spec](docs/SPEC-v2.md)+} i {-`uv run`-} {+`uv sync`+}."


def test_req_vcs_031_polish_letters_and_emoji():
    assert readable(mark_words("Zażółć gęślą jaźń 🙂", "Zażółć żółtą gęślą jaźń 🚀")) == "Zażółć {+żółtą+} gęślą jaźń {-🙂-} {+🚀+}"


# ---------- blocks compared ----------

def test_req_vcs_031_reflowed_text_is_not_a_change():
    assert all(c.state is State.SAME for c in diff_blocks("To jest akapit\nzawinięty.\n", "To jest\nakapit zawinięty.\n"))


def test_req_vcs_031_a_changed_paragraph_is_one_modified_block():
    [change] = diff_blocks("Pierwszy akapit.\n", "Pierwszy poprawiony akapit.\n")
    assert change.state is State.MOD and change.old.src == "Pierwszy akapit."
    assert readable(change.marked) == "Pierwszy {+poprawiony+} akapit."


def test_req_vcs_031_similar_items_are_paired_and_the_rest_added_or_removed():
    old = "- Stage całych plików\n- Diff tylko do odczytu\n- Pull\n  - tylko fast-forward\n"
    new = "- Stage całych plików i folderów\n- Pull\n  - tylko fast-forward, bez rebase\n- Menu kontekstowe\n"
    assert states(old, new) == [("mod", "Stage całych plików i folderów"), ("del", "Diff tylko do odczytu"),
                                ("same", "Pull"), ("mod", "tylko fast-forward, bez rebase"), ("add", "Menu kontekstowe")]


def test_req_vcs_031_renumbering_a_list_only_adds_the_new_item():
    assert states("1. pierwszy\n2. drugi\n", "1. pierwszy\n2. nowy drugi\n3. drugi\n") == [
        ("same", "pierwszy"), ("add", "nowy drugi"), ("same", "drugi")]


def test_req_vcs_031_new_and_deleted_files_are_all_added_or_removed():
    assert {c.state for c in diff_blocks("", "# Nowy\n\nTekst.\n")} == {State.ADD}
    assert {c.state for c in diff_blocks("# Stary\n\nTekst.\n", "")} == {State.DEL}


def test_req_vcs_031_a_moved_section_shows_as_removed_and_added():
    old, new = "## A\n\nTreść A.\n\n## B\n\nTreść B.\n", "## B\n\nTreść B.\n\n## A\n\nTreść A.\n"
    assert [c.state.value for c in diff_blocks(old, new)] == ["add", "add", "same", "same", "del", "del"]


def test_des_vcs_049_a_changed_code_block_is_modified_line_by_line():
    [change] = diff_blocks("```\na = 1\nb = 2\n```\n", "```\na = 1\nb = 3\n```\n")
    assert change.state is State.MOD and change.block.kind == "code" and change.marked is None


def test_des_vcs_049_huge_rewrites_skip_pairing():
    old = "".join(f"- stary punkt {i}\n" for i in range(100))
    new = "".join(f"- nowy punkt {i}\n" for i in range(100))
    assert {c.state for c in diff_blocks(old, new)} == {State.DEL, State.ADD}


# ---------- source lines of blocks (DES-VCS-056) ----------

def test_des_vcs_056_blocks_know_their_first_and_last_line_in_the_file():
    text = "---\ntytul: x\n---\n\n# Plan\n\nAkapit\nw dwóch.\n\n- punkt\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```py\nx\n```\n"
    assert [(b.kind, b.line, b.end) for b in parse_blocks(text)] == [
        ("meta", 1, 3), ("heading", 5, 5), ("paragraph", 7, 8), ("item", 10, 10), ("header", 12, 12),
        ("row", 14, 14), ("code", 16, 18)]


def test_des_vcs_056_lines_do_not_change_how_blocks_compare():
    assert states("Akapit.\n", "\n\n\nAkapit.\n") == [("same", "Akapit.")]
