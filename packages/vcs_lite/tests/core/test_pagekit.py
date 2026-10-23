"""Parts every browser page shares: template, folder of pages, copies of files (DES-VCS-058)."""

from __future__ import annotations

import os
import time

from vcs_lite.core import pagekit


def test_des_vcs_058_document_has_the_policy_theme_and_one_script():
    page = pagekit.document(title="a<b>.py", theme="dark", css="body{}", body="<p>x</p>", script="1;")
    assert 'data-theme="dark"' in page and "Content-Security-Policy" in page and page.count("<script>") == 1
    assert "<title>a&lt;b&gt;.py · vcs-lite</title>" in page and "<link" not in page
    assert 'data-theme' not in pagekit.document(title="a", theme="system", css="", body="", script="")


def test_des_vcs_058_a_copy_keeps_the_file_name_and_its_bytes(tmp_path):
    copy = pagekit.keep_copy(b"\x89PNG", "ikona.png", folder=tmp_path)
    assert copy.name == "ikona.png" and copy.read_bytes() == b"\x89PNG" and copy.parent.parent == tmp_path
    assert pagekit.keep_copy(b"x", "ikona.png", folder=tmp_path) != copy   # every copy has its own folder


def test_des_vcs_058_pages_and_copies_older_than_a_day_are_removed(tmp_path):
    old_page = pagekit.write_page("<p>stara</p>", "a.md", folder=tmp_path)
    old_copy = pagekit.keep_copy(b"x", "a.png", folder=tmp_path)
    past = time.time() - pagekit.PAGE_LIFETIME - 60
    for path in (old_page, old_copy.parent):
        os.utime(path, (past, past))
    fresh = pagekit.keep_copy(b"y", "b.png", folder=tmp_path)
    assert not old_page.exists() and not old_copy.parent.exists() and fresh.exists()


def test_des_vcs_058_arguments_shared_by_the_page_processes():
    args = pagekit.page_arguments("x").parse_args(["l", "r", "L", "R", "--read", "--line", "7", "--theme", "dark",
                                                   "--no-open"])
    assert (args.read, args.line, args.theme, args.no_open, args.left.name) == (True, 7, "dark", True, "l")
