"""Which way a file opens is decided in one place, by its type (REQ-VCS-034, DES-VCS-060)."""

from __future__ import annotations

import pytest

from vcs_lite.core.filekind import TEXT_LIMIT, Kind, is_text, kind_of


@pytest.mark.parametrize("path, kind", [
    ("README.md", Kind.MARKDOWN), ("docs/SPEC.MD", Kind.MARKDOWN), ("logo.png", Kind.IMAGE), ("a/b.JPEG", Kind.IMAGE),
    ("ikona.svg", Kind.IMAGE), ("x.webp", Kind.IMAGE), ("opis.pdf", Kind.PDF), ("Opis.PDF", Kind.PDF),
    ("app.py", Kind.OTHER), ("archiwum.zip", Kind.OTHER), ("Makefile", Kind.OTHER), ("a.markdown", Kind.OTHER)])
def test_des_vcs_060_kind_comes_from_the_extension_in_any_case(path, kind):
    assert kind_of(path) is kind


def test_des_vcs_060_shown_kinds_open_as_the_file_itself():
    assert Kind.IMAGE.shown_as_file and Kind.PDF.shown_as_file and not Kind.MARKDOWN.shown_as_file


def test_des_vcs_060_text_has_no_nul_in_its_first_8000_bytes(tmp_path):
    text, binary, late_nul = tmp_path / "a.txt", tmp_path / "b.bin", tmp_path / "c.txt"
    text.write_text("zażółć\n" * 10, encoding="utf-8")
    binary.write_bytes(b"abc\0def")
    late_nul.write_bytes(b"x" * 8000 + b"\0")
    assert is_text(text) and not is_text(binary) and is_text(late_nul)


def test_des_vcs_060_large_files_folders_and_missing_files_are_not_text(tmp_path):
    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * (TEXT_LIMIT + 1))
    assert not is_text(big) and not is_text(tmp_path) and not is_text(tmp_path / "brak.txt")
