"""Drawn shapes must match the reference geometry exactly (UI-REFERENCE §3: pills, radius 7, kbd)."""

from __future__ import annotations

import tkinter as tk

import pytest

from vcs_lite.ui.widgets import rounded_rect


@pytest.fixture(scope="module")
def canvas(tk_root):
    c = tk.Canvas(tk_root)
    yield c
    c.destroy()


def ovals(c: tk.Canvas, tag: str) -> list[tuple[float, ...]]:
    return sorted(tuple(c.coords(i)) for i in c.find_withtag(tag) if c.type(i) == "oval")


def test_des_vcs_042_pill_ends_are_true_semicircles(canvas):
    rounded_rect(canvas, 0, 0, 40, 20, 10, fill="#dfe1e6", tags=("pill",))
    assert ovals(canvas, "pill") == [(0.0, 0.0, 20.0, 20.0), (0.0, 0.0, 20.0, 20.0), (20.0, 0.0, 40.0, 20.0), (20.0, 0.0, 40.0, 20.0)]
    assert all(canvas.type(i) != "polygon" for i in canvas.find_withtag("pill"))


def test_des_vcs_042_corner_radius_is_exact(canvas):
    rounded_rect(canvas, 8, 37, 222, 85, 7, fill="#0a66d8", tags=("selection",))
    assert ovals(canvas, "selection")[0] == (8.0, 37.0, 22.0, 51.0)  # 2 × radius 7 in the top-left corner
    assert {canvas.itemcget(i, "fill") for i in canvas.find_withtag("selection")} == {"#0a66d8"}


def test_des_vcs_042_outline_is_drawn_as_a_one_point_border(canvas):
    rounded_rect(canvas, 0, 0, 30, 18, 4, fill="#f0f0f3", outline="#d5d5da", tags=("kbd",))
    fills = [canvas.itemcget(i, "fill") for i in canvas.find_withtag("kbd")]
    assert fills[0] == "#d5d5da" and fills[-1] == "#f0f0f3"  # border shape first, inner shape on top


# ---------- the View switch (DEC-VCS-092, DES-VCS-051) ----------

OPTIONS = (("changes", "Zmiany"), ("folders", "Foldery"), ("project", "Projekt"))


@pytest.fixture
def switch(tk_root):
    from vcs_lite.ui.widgets import SegmentedControl
    chosen = []
    control = SegmentedControl(tk_root, OPTIONS, "changes", chosen.append, parent_bg="#fafafb")
    yield control, chosen
    control.destroy()


def items(c: tk.Canvas, tag: str) -> list[int]:
    return list(c.find_withtag(tag))


def test_des_vcs_051_the_switch_is_a_grey_capsule_with_a_white_pill_under_the_choice(switch):
    c, _ = switch
    assert int(c.cget("height")) == 24
    track = items(c, "track")
    assert {c.itemcget(i, "fill") for i in track} >= {"#e4e4e9"}
    assert [c.itemcget(i, "text") for i in items(c, "label")] == ["Zmiany", "Foldery", "Projekt"]
    pill = [c.coords(i) for i in items(c, "thumb") if c.type(i) == "oval" and c.itemcget(i, "fill") == "#cfcfd5"]
    assert pill and all(x2 - x1 == 20 for x1, _, x2, _ in pill)  # its edge has radius 10: 20 high inside the 24 pt track
    assert {c.itemcget(i, "fill") for i in items(c, "thumb")} >= {"#ffffff"}
    first = c.coords(items(c, "label")[0])[0]
    assert min(x1 for x1, _, _, _ in pill) < first < max(x2 for _, _, x2, _ in pill)


def test_des_vcs_051_separators_only_between_two_unchosen_options(switch):
    c, _ = switch
    assert len(items(c, "separator")) == 1        # Foldery | Projekt
    c.set("folders")
    assert len(items(c, "separator")) == 0        # both sit next to the pill


def test_des_vcs_051_a_click_chooses_and_reports_once(switch):
    c, chosen = switch
    x = int(c.coords(items(c, "label")[2])[0])
    c.click(x)
    c.click(x)
    assert c.value == "project" and chosen == ["project"]
    labels = items(c, "label")  # the switch redraws itself, so the items are new
    assert c.itemcget(labels[2], "fill") == "#1d1d1f" and c.itemcget(labels[0], "fill") == "#3a3a40"
