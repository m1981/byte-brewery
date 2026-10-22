"""theme.py must carry every value of the reference (DES-VCS-042, docs/ui-reference/UI-REFERENCE.md)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vcs_lite.ui import theme

REFERENCE = Path(__file__).resolve().parents[2] / "docs" / "ui-reference" / "UI-REFERENCE.md"
SYSTEM_DRAWN = {"#ff5f57", "#febc2e", "#28c840"}  # window buttons, drawn by macOS


def section(title: str) -> str:
    text = REFERENCE.read_text(encoding="utf-8")
    start = text.index(title)
    end = text.find("\n## ", start + len(title))
    return text[start: end if end != -1 else len(text)]


def test_des_vcs_042_tokens_have_the_reference_values():
    rows = re.findall(r"^\| `([a-z-]+)` \| `(#[0-9a-f]{6})` \|", section("### Tokeny"), re.M)
    assert len(rows) == 14
    for token, value in rows:
        assert theme.COLORS[token.replace("-", "_")] == value, token


def test_des_vcs_042_every_colour_of_the_reference_is_in_the_theme():
    used = set(re.findall(r"#[0-9a-f]{6}\b", REFERENCE.read_text(encoding="utf-8"))) - SYSTEM_DRAWN
    assert used - set(theme.COLORS.values()) == set()


# Rows of the typography table and the theme role that implements each one.
TYPE_ROWS = {
    "tekst bazowy": "body",
    "nazwa repo w pasku narzędzi": "toolbar_repo",
    "chip gałęzi": "chip",
    "nagłówek „REPOZYTORIA”": "side_header",
    "nazwa repo w pasku bocznym": "side_name",
    "gałąź w pasku bocznym": "side_branch",
    "licznik / znacznik": "badge",
    "nagłówek grupy („STAGED”)": "group_header",
    "liczba w nagłówku grupy": "group_count",
    "kwadrat statusu": "status_square",
    "nazwa pliku": "file_name",
    "katalog pliku i „stara → ”": "file_dir",
    "podpowiedź przy wierszu": "hint",
    "klawisz (`kbd`)": "kbd",
    "pole wiadomości": "message",
    "przyczyna nieaktywności": "reason",
    "pasek stanu": "statusbar",
}
NATIVE_ROWS = {"tytuł okna", "przyciski"}  # drawn by macOS and ttk aqua (DEC-VCS-047)


def typography_rows() -> list[list[str]]:
    lines = [line for line in section("## 2. Typografia").splitlines() if line.startswith("| ")]
    return [[cell.strip() for cell in line.strip("|").split("|")] for line in lines[1:] if not line.startswith("|---")]


def resolve(colour_cell: str) -> str:
    value = colour_cell.strip("`")
    return value if value.startswith("#") else theme.COLORS[value.replace("-", "_")]


@pytest.mark.parametrize("row", typography_rows(), ids=lambda r: r[0])
def test_des_vcs_042_typography_follows_the_reference(row):
    label, size, weight, colour = row[0], row[1], row[2], row[3]
    if label in NATIVE_ROWS:
        return
    t = theme.TYPE[TYPE_ROWS[label]]
    points = float(size.split()[0])
    assert t.size == int(points + 0.5), "rozmiar (11.5 → 12, §6)"
    assert t.weight == ("bold" if int(weight) >= 550 else "normal"), "grubość (≥550 → bold, §6)"
    assert t.mono == ("mono" in size)
    assert t.color == resolve(colour)


def test_des_vcs_042_every_typography_row_is_mapped():
    assert {r[0] for r in typography_rows()} == set(TYPE_ROWS) | NATIVE_ROWS
