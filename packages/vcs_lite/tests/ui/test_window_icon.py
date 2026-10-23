"""The logo in the Dock also when vcs-lite starts from a terminal (REQ-VCS-104, DES-VCS-062, DEC-VCS-112)."""

from __future__ import annotations

import struct

from vcs_lite.ui.main import WINDOW_ICON, set_window_icon


def test_des_vcs_062_the_window_icon_ships_with_the_package_small_and_shaped():
    data = WINDOW_ICON.read_bytes()
    assert data.startswith(b"\x89PNG") and struct.unpack(">IIBB", data[16:26]) == (256, 256, 8, 6)


def test_des_vcs_062_the_icon_is_set_on_the_window(tk_root):
    assert set_window_icon(tk_root, WINDOW_ICON) is True


def test_des_vcs_062_a_missing_or_broken_icon_never_stops_the_start(tk_root, tmp_path):
    broken = tmp_path / "icon.png"
    broken.write_bytes(b"nie obrazek")
    assert set_window_icon(tk_root, tmp_path / "brak.png") is False
    assert set_window_icon(tk_root, broken) is False
