"""Drawn shapes must match the reference geometry exactly (UI-REFERENCE §3: pills, radius 7, kbd)."""

from __future__ import annotations

import tkinter as tk

import pytest

from vcs_lite.ui.tkenv import prepare_tk
from vcs_lite.ui.widgets import rounded_rect


@pytest.fixture(scope="module")
def canvas():
    prepare_tk()
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")
    root.withdraw()
    c = tk.Canvas(root)
    yield c
    root.destroy()


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
