"""The rendered Markdown diff page (REQ-VCS-031, DES-VCS-049, DEC-VCS-078, DEC-VCS-081, pattern E-03)."""

from __future__ import annotations

import os
import re
import time

from vcs_lite.core import mdpage
from vcs_lite.core.mdpage import blocks_label, render_page, write_page


def page(old: str, new: str, **extra) -> str:
    options = {"file_name": "SPEC.md", "left_title": "SPEC.md (HEAD)", "right_title": "SPEC.md (kopia robocza)"}
    return render_page(old, new, **{**options, **extra})


def rendered(html: str) -> str:
    """The rendered view only, without the source view and the template."""
    return html.split('<div class="doc">', 1)[1].split('<div class="source"', 1)[0]


def test_req_vcs_031_changed_words_are_inserted_and_deleted_without_strike_through():
    html = page("Zmiany w kilku repozytoriach.\n", "Zmiany w wielu repozytoriach.\n")
    assert "<del>kilku</del> <ins>wielu</ins>" in rendered(html)
    assert "line-through" not in html  # DEC-VCS-078


def test_req_vcs_031_nothing_from_the_file_runs_in_the_browser():
    html = page("Tekst.\n", "Tekst.\n\n<script>alert('x')</script>\n\n[link](javascript:alert(1))\n")
    body = rendered(html)
    assert "<script" not in body and "&lt;script&gt;" in body
    assert 'href="javascript' not in html
    assert "Content-Security-Policy" in html and html.count("<script>") == 1  # only the page's own toggle


def test_req_vcs_031_task_lists_show_boxes():
    body = rendered(page("- [ ] testy\n", "- [x] testy\n"))
    assert "<del>☐</del> <ins>☑</ins> testy" in body


def test_des_vcs_049_items_make_one_list_with_their_numbers_and_depth():
    body = rendered(page("1. a\n2. b\n", "1. a\n2. nowe\n3. b\n"))
    assert body.count("<ol>") == 1
    assert '<li class="add" value="2"' in body and '<li class="same" value="3"' in body


def test_des_vcs_049_rows_make_one_table_with_its_header():
    body = rendered(page("| ID | S |\n|---|---|\n| A | ok |\n", "| ID | S |\n|---|---|\n| A | ok |\n| B | nowe |\n"))
    assert body.count("<table>") == 1
    assert '<tr class="same"><th>ID</th><th>S</th></tr>' in body and '<tr class="add"><td>B</td>' in body


def test_des_vcs_049_changed_code_is_shown_line_by_line():
    body = rendered(page("```\na = 1\nb = 2\n```\n", "```\na = 1\nb = 3\n```\n"))
    assert '<span class="ln del">b = 2</span>' in body and '<span class="ln add">b = 3</span>' in body


def test_req_vcs_031_long_unchanged_stretches_fold():
    old = "".join(f"## Sekcja {i}\n\nTreść {i}.\n\n" for i in range(1, 13))
    new = old.replace("Treść 7.", "Treść 7 poprawiona.")
    body = rendered(page(old, new))
    assert "⋯ 12 niezmienionych bloków" in body and "⋯ 9 niezmienionych bloków" in body
    assert "Sekcja 7" in body and "Sekcja 1<" not in body


def test_des_vcs_049_polish_plural_of_blocks():
    assert [blocks_label(n) for n in (1, 2, 4, 5, 12, 22)] == [
        "1 niezmieniony blok", "2 niezmienione bloki", "4 niezmienione bloki", "5 niezmienionych bloków",
        "12 niezmienionych bloków", "22 niezmienione bloki"]


def test_req_vcs_031_reflowed_text_says_there_is_no_change():
    assert "Bez zmian w treści" in rendered(page("Jeden\ndwa.\n", "Jeden dwa.\n"))


def test_req_vcs_031_images_of_the_working_copy_load_and_older_ones_become_labels(tmp_path):
    html = page("![schemat](img/v1.png)\n", "![schemat](img/v2.png)\n", base=tmp_path)
    body = rendered(html)
    assert f'<base href="{tmp_path.as_uri()}/">' in html
    assert '<img src="img/v2.png" alt="schemat"' in body
    assert '<del><span class="img-old">🖼 schemat</span></del>' in body


def test_req_vcs_031_without_a_working_copy_every_image_is_a_label():
    body = rendered(page("Tekst.\n", "Tekst.\n\n![schemat](img/v2.png)\n"))
    assert "<img" not in body and '<span class="img-old">🖼 schemat</span>' in body


def test_req_vcs_031_header_names_the_file_sides_and_counts():
    html = page("Pierwszy akapit.\n\nDrugi akapit.\n",
                "Pierwszy akapit zmieniony.\n\nDrugi akapit poprawiony.\n\nZupełnie nowy tekst na końcu.\n")
    assert "SPEC.md (HEAD) → SPEC.md (kopia robocza)" in html
    assert '<span class="a">+1</span>' in html and '<span class="d">−0</span>' in html
    assert '<span class="m">~2</span>' in html


def test_req_vcs_031_source_view_shows_raw_lines():
    html = page("# A\n\nstare\n", "# A\n\nnowe\n")
    source = html.split('<div class="source"', 1)[1]
    assert '<span class="ln del">- stare</span>' in source and '<span class="ln add">+ nowe</span>' in source


def test_des_vcs_049_file_names_are_escaped():
    assert "a&lt;b&gt;.md" in page("x\n", "y\n", file_name="a<b>.md")


def test_des_vcs_049_pages_are_written_to_one_folder_and_old_ones_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(mdpage, "PAGES", tmp_path / "pages")
    old = write_page("<p>stara</p>", "SPEC.md")
    day_ago = time.time() - 2 * 24 * 3600
    os.utime(old, (day_ago, day_ago))
    fresh = write_page("<p>nowa</p>", "SPEC.md")
    assert fresh.read_text(encoding="utf-8") == "<p>nowa</p>" and fresh.parent == tmp_path / "pages"
    assert not old.exists()


def test_des_vcs_049_main_writes_the_page_and_prints_its_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mdpage, "PAGES", tmp_path / "pages")
    left, right = tmp_path / "left.md", tmp_path / "right.md"
    left.write_bytes(b"Stary tekst \xff.\n")  # not UTF-8: replaced, no crash
    right.write_text("Nowy tekst.\n", encoding="utf-8")
    assert mdpage.main([str(left), str(right), "SPEC.md (HEAD)", "SPEC.md (kopia robocza)", "--no-open"]) == 0
    written = capsys.readouterr().out.strip()
    assert written.endswith(".html") and "Nowy" in open(written, encoding="utf-8").read()


def test_des_vcs_049_marks_never_cross_table_cells_and_none_are_left_over():
    cases = [
        ("| ID | Status |\n|---|---|\n| A | ok |\n| B | ok |\n",
         "| ID | Status | Właściciel |\n|---|---|---|\n| A | ok | Ty |\n| B | ok | agent |\n"),
        ("| a b c | d |\n|---|---|\n| x y | z |\n", "| a c | d e |\n|---|---|\n| x | y z |\n"),
        ("- [ ] a **b** `c` [d](e)\n", "- [x] a *b* `c2` [d](f)\n"),
    ]
    for old, new in cases:
        body = rendered(page(old, new))
        assert not any(ch in body for ch in "")
        for cell in body.split("<t")[1:]:
            assert cell.count("<ins>") == cell.count("</ins>") and cell.count("<del>") == cell.count("</del>"), cell


def test_req_vcs_031_a_chosen_theme_wins_over_the_system_one():
    assert '<html lang="pl" data-theme="dark">' in page("a\n", "b\n", theme="dark")
    assert '<html lang="pl" data-theme="light">' in page("a\n", "b\n", theme="light")
    assert '<html lang="pl">' in page("a\n", "b\n")  # system: follows macOS


def test_req_vcs_031_both_palettes_are_in_the_page_and_links_are_readable():
    html = page("a\n", "[b](c)\n")
    assert ':root:not([data-theme="light"])' in html and ':root[data-theme="dark"]' in html
    assert "--link:#0a5dc2" in html and "--link:#6cb6ff" in html  # contrast 6.3 and 7.7 (2026-10-23)
    assert "a { color:var(--link); }" in html


def test_req_vcs_031_main_takes_the_theme(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mdpage, "PAGES", tmp_path / "pages")
    left = tmp_path / "a.md"
    left.write_text("x\n", encoding="utf-8")
    mdpage.main([str(left), str(left), "a", "b", "--no-open", "--theme", "dark"])
    assert 'data-theme="dark"' in open(capsys.readouterr().out.strip(), encoding="utf-8").read()


def contrast(a: str, b: str) -> float:
    def lum(colour: str) -> float:
        rgb = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    high, low = sorted((lum(a), lum(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def palette(tokens: str) -> dict[str, str]:
    return dict(re.findall(r"--([\w-]+):(#[0-9a-f]{6})", tokens))


def test_req_vcs_031_changed_lines_stand_out_and_their_text_stays_readable():
    """Zrzut 2026-10-23: in the dark theme the lines of added and removed blocks merged with the background."""
    for tokens in (mdpage.LIGHT, mdpage.DARK):
        colours = palette(tokens)
        for line in ("add-soft", "del-soft"):
            for text in ("ink", "dim", "link"):
                assert contrast(colours[text], colours[line]) >= 4.5, (text, line)
    dark = palette(mdpage.DARK)
    assert min(contrast(dark[line], dark["bg"]) for line in ("add-soft", "del-soft")) >= 1.4
    assert min(contrast(dark[line], dark["code-bg"]) for line in ("add-soft", "del-soft")) >= 1.25


def test_req_vcs_031_document_text_uses_real_open_sans_faces_from_google_fonts():
    """Zrzut 2026-10-23: bold text was blurry, because only weight 400 was loaded and the browser faked bold."""
    html = page("a\n", "b\n")
    family = "family=Open+Sans:ital,wght@0,400;0,600;1,400&display=swap"
    assert f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{family}">' in html
    assert "style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com" in html
    assert '.doc { font-family:"Open Sans",var(--font); font-synthesis:none; }' in html  # never a faked face
    assert ".doc strong, .doc b, .doc th, .doc h1, .doc h2, .doc h3, .doc h4 { font-weight:600; }" in html


def test_req_vcs_031_wide_page_and_document_text_two_points_larger():
    """User 2026-10-23: „Potrzebuję szerszej canvy i czcionka większa o 2 punkty”."""
    css = mdpage.CSS
    assert "main { max-width:1200px;" in css
    for rule in ("body { margin:0; background:var(--page); color:var(--ink); font:17px/1.6",
                 ".doc h1 { font-size:26px; } .doc h2 { font-size:21px; } .doc h3 { font-size:18px; }",
                 "border-collapse:collapse; font-size:16px;", ".doc pre { font:15px/1.5", ".source pre { margin:0; padding:14px 18px; font:15px/1.5"):
        assert rule in css, rule
    assert "border-bottom:1px solid var(--line); font-size:13px; }" in css  # the bar stays as it was


def test_req_vcs_031_changed_words_are_underlined_not_filled():
    """DEC-VCS-087 (wariant U2): colour, line style and tone tell added from removed, also for red-green blindness."""
    css = mdpage.CSS
    assert ("ins { background:none; text-decoration:underline solid var(--add) 2px; text-underline-offset:3px; }"
            in css)
    assert ("del { background:none; text-decoration:underline dotted var(--del) 2px; text-underline-offset:3px; "
            "color:var(--dim); }" in css)
    assert "ins code { box-shadow:0 0 0 1.5px var(--add); } del code { box-shadow:0 0 0 1.5px var(--del); }" in css
    assert "ins a, del a { text-decoration:none; }" in css  # the change line stands in for the link underline
    assert "--add-word" not in css and "--del-word" not in css  # no word fill any more


# ---------- <br> (DEC-VCS-088) ----------

def test_req_vcs_031_br_breaks_a_line_in_tables_and_text():
    body = rendered(page("x\n", "| Treść |\n|---|\n| linia 1<br>linia 2 |\n\ntekst<br/>dalej<BR />koniec\n"))
    assert "linia 1<br />" in body and "linia 2" in body and "&lt;br" not in body.split("<pre")[0]
    assert "tekst<br />" in body and "dalej<br />" in body


def test_req_vcs_031_br_stays_literal_in_code_and_other_tags_stay_text():
    body = rendered(page("x\n", "W kodzie `a<br>b`.\n\n```\nc<br>d\n```\n\n<b>gruby</b> i <br onclick=\"x\">\n"))
    assert "<code>a&lt;br&gt;b</code>" in body and "c&lt;br&gt;d" in body
    assert "&lt;b&gt;gruby&lt;/b&gt;" in body and "&lt;br onclick=" in body and "onclick=\"x\">" not in body


def test_req_vcs_031_br_lines_are_compared_like_words():
    body = rendered(page("| A |\n|---|\n| D1. stara<br>D2. bez zmian |\n", "| A |\n|---|\n| D1. nowa<br>D2. bez zmian |\n"))
    assert "<del>stara</del>" in body and "<ins>nowa</ins>" in body and "<br />" in body
    assert not any(ch in body for ch in "\ue000\ue001\ue002\ue003")


# ---------- reading mode (REQ-VCS-032) ----------

def test_req_vcs_032_reading_mode_shows_the_whole_document_without_marks():
    text = "".join(f"## Sekcja {i}\n\nTreść {i}.\n\n" for i in range(1, 13))
    html = page(text, text, read=True, right_title="plan.md (kopia robocza)")
    body = rendered(html)
    assert "Sekcja 1<" in body and "Sekcja 12<" in body and 'class="fold"' not in body
    assert "Bez zmian" not in body and '<span class="stats">' not in html
    assert '<span class="sides">plan.md (kopia robocza)</span>' in html
