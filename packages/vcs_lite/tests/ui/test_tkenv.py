"""Tcl/Tk library paths for uv's Python inside a venv (OBS-VCS-009, DES-VCS-041)."""

from __future__ import annotations

from pathlib import Path

from vcs_lite.ui.tkenv import tcl_tk_paths


def _base(tmp_path: Path) -> Path:
    for folder in ("tcl8.6", "tk8.6"):
        (tmp_path / "lib" / folder).mkdir(parents=True)
    return tmp_path


def test_des_vcs_041_points_tcl_and_tk_at_the_base_python(tmp_path):
    base = _base(tmp_path)
    assert tcl_tk_paths({}, base) == {"TCL_LIBRARY": str(base / "lib" / "tcl8.6"), "TK_LIBRARY": str(base / "lib" / "tk8.6")}


def test_des_vcs_041_keeps_paths_the_user_already_set(tmp_path):
    base = _base(tmp_path)
    assert tcl_tk_paths({"TCL_LIBRARY": "/mine/tcl", "TK_LIBRARY": "/mine/tk"}, base) == {}


def test_des_vcs_041_does_nothing_when_the_base_python_has_no_tcl(tmp_path):
    assert tcl_tk_paths({}, tmp_path) == {}
