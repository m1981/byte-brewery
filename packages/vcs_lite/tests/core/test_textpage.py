"""The side-by-side diff page in the browser and the plain text page (pattern E-05, DES-VCS-059)."""

from __future__ import annotations

import re

from vcs_lite.core import textpage
from vcs_lite.core.filekind import TEXT_LIMIT
from vcs_lite.core.textpage import lines_label, render_page, size_label


def page(old: bytes, new: bytes, **extra) -> str:
    titles = {"file_name": "app.py", "left_title": "app.py (indeks)", "right_title": "app.py (kopia robocza)"}
    return render_page(old, new, **{**titles, **extra})


def rows(html: str) -> list[str]:
    """Each table row's class and its cells as text, e.g. 'mod|2|return x * 2|2|return x * 3'."""
    out = []
    for cls, cells in re.findall(r'<tr class="([^"]*)"[^>]*>(.*?)</tr>', html, re.S):
        texts = [re.sub(r"<[^>]+>", "", c) for c in re.findall(r"<td[^>]*>(.*?)</td>", cells, re.S)]
        out.append("|".join([cls, *texts]))
    return out


def numbered(n: int, changes: dict[int, str | None] | None = None) -> bytes:
    lines = [f"linia {i}" for i in range(1, n + 1)]
    for number, text in (changes or {}).items():
        lines[number - 1] = text
    return ("\n".join(line for line in lines if line is not None) + "\n").encode()


# ---------- side by side ----------

def test_at_vcs_046_changed_lines_side_by_side_with_marks_filler_and_folding():
    old = numbered(60, {2: "return x * 2"})
    new = numbered(60, {2: "return x * 3", 30: None})
    html = page(old, new)
    table = rows(html)
    assert "mod|2|return x * 2|2|return x * 3" in table
    assert re.search(r'<td class="c l">return x \* <del>2</del></td>', html)
    assert re.search(r'<td class="c r">return x \* <ins>3</ins></td>', html)
    assert "del|30|linia 30||" in table                     # the right side is the filler
    assert table[0] == "same|1|linia 1|1|linia 1"
    folds = [r for r in table if r.startswith("fold")]
    assert folds == ["fold|⋯ 21 niezmienionych linii", "fold|⋯ 27 niezmienionych linii"]   # lines 6–26 and 34–60
    assert '<th class="side" colspan="2">indeks</th><th class="side" colspan="2">kopia robocza</th>' in html
    assert '<span class="a">+0</span> <span class="d">−1</span> <span class="m">~1</span>' in html


def test_des_vcs_059_added_lines_have_the_filler_on_the_left():
    table = rows(page(b"a\nc\n", b"a\nb\nc\n"))
    assert table == ["same|1|a|1|a", "add|||2|b", "same|2|c|3|c"]


def test_des_vcs_059_a_changed_stretch_pairs_lines_then_adds_the_rest():
    table = rows(page(b"x = 1\nkoniec\n", b"x = 2\ny = 3\nkoniec\n"))
    assert table == ["mod|1|x = 1|1|x = 2", "add|||2|y = 3", "same|2|koniec|3|koniec"]


def test_des_vcs_059_everything_from_the_file_is_escaped():
    html = page(b"<script>alert(1)</script>\nok\n", b"ok\n<b>x</b>\n")
    body = html.split("<table", 1)[1]
    assert "<script>alert" not in body and "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "<b>x</b>" not in body and "&lt;b&gt;x&lt;/b&gt;" in body
    assert "Content-Security-Policy" in html and html.count("<script>") == 1


def test_des_vcs_059_other_encodings_show_replacement_characters():
    assert "�" in page(b"za\xbf\n", b"za\xbf\xf3\n")


def test_des_vcs_059_same_text_says_there_is_no_change():
    assert "Bez zmian w treści" in page(b"a\r\n", b"a\r\n")


# ---------- one column ----------

def test_des_vcs_059_new_file_is_one_green_column_with_a_badge():
    html = page(b"", b"pierwsza\ndruga\n", left_title="app.py (pusty)")
    assert rows(html) == ["add|1|pierwsza", "add|2|druga"] and '<span class="badge">nowy plik</span>' in html


def test_des_vcs_059_deleted_file_is_one_red_column_with_a_badge():
    html = page(b"stara\n", b"", right_title="app.py (pusty)")
    assert rows(html) == ["del|1|stara"] and '<span class="badge">usunięty plik</span>' in html


def test_des_vcs_059_reading_marks_the_line_and_scrolls_to_it():
    html = page(b"", numbered(40), read=True, line=25, right_title="app.py (kopia robocza)")
    assert rows(html)[24] == "same hit|25|linia 25" and html.count('id="hit"') == 1
    assert "scrollIntoView" in html and "fold" not in "".join(rows(html))


# ---------- no preview (REQ-VCS-007) ----------

def test_req_vcs_007_binary_side_gives_a_message_with_both_sizes():
    html = page(b"x" * 1300, b"\0" * 2048)
    assert "Brak podglądu zmian" in html and "Plik binarny" in html and "<table class=\"diff" not in html
    assert "<td>indeks</td><td>1,3 kB</td>" in html and "<td>kopia robocza</td><td>2,0 kB</td>" in html


def test_req_vcs_007_too_large_side_gives_a_message():
    html = page(b"a\n", b"a\n" * (TEXT_LIMIT // 2 + 1))
    assert "Brak podglądu zmian" in html and "większy niż 2 MB" in html


# ---------- labels and the process ----------

def test_des_vcs_059_polish_labels():
    assert [lines_label(n) for n in (1, 3, 5, 12, 22)] == [
        "1 niezmieniona linia", "3 niezmienione linie", "5 niezmienionych linii", "12 niezmienionych linii",
        "22 niezmienione linie"]
    assert [size_label(n) for n in (820, 1300, 1_258_291)] == ["820 B", "1,3 kB", "1,2 MB"]


def test_des_vcs_059_the_process_writes_the_page(tmp_path, monkeypatch):
    left, right = tmp_path / "l.py", tmp_path / "r.py"
    left.write_text("a\n"); right.write_text("b\n")
    monkeypatch.setattr(textpage, "PAGES", tmp_path / "pages")
    textpage.main([str(left), str(right), "app.py (indeks)", "app.py (kopia robocza)", "--no-open", "--theme", "dark"])
    [written] = (tmp_path / "pages").glob("*.html")
    text = written.read_text(encoding="utf-8")
    assert 'data-theme="dark"' in text and "mod|1|a|1|b" in rows(text)
