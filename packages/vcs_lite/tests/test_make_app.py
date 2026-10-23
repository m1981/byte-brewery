"""vcs-lite as a macOS application: icon, bundle and launcher built by tools/make_app.py (REQ-VCS-104, DES-VCS-061)."""

from __future__ import annotations

import importlib.util
import plistlib
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("make_app", TOOLS / "make_app.py")
make_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_app)


def rgb_square(side: int, colour=(10, 200, 30)) -> bytes:
    return bytes(colour) * side * side


def alpha_at(rgba: bytes, canvas: int, x: int, y: int) -> int:
    return rgba[(y * canvas + x) * 4 + 3]


def logo_png(path: Path, side: int = 64) -> Path:
    """A square RGB logo without transparency, like assets/logo.png."""
    rows = b"".join(b"\0" + bytes((200, 40, 40)) * side for _ in range(side))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", side, side, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    return path


# ---------- the icon ----------

def test_des_vcs_061_icon_has_transparent_corners_and_margin_and_the_logo_inside():
    canvas = 128
    side = make_app.body_side(canvas)
    rgba = make_app.shape_icon(rgb_square(side), canvas)
    assert len(rgba) == canvas * canvas * 4 and side == 103
    assert alpha_at(rgba, canvas, 0, 0) == 0 and alpha_at(rgba, canvas, 5, 64) == 0        # margin
    margin = (canvas - side) // 2
    assert alpha_at(rgba, canvas, margin + 1, margin + 1) == 0                            # rounded corner
    centre = (64 * canvas + 64) * 4
    assert rgba[centre:centre + 4] == bytes((10, 200, 30, 255))                           # the logo
    edge = [alpha_at(rgba, canvas, x, 64) for x in range(margin - 1, margin + 2)]
    assert edge[0] == 0 and edge[-1] == 255                                               # a clean straight edge


def test_des_vcs_061_corner_edges_are_smoothed():
    canvas = 256
    rgba = make_app.shape_icon(rgb_square(make_app.body_side(canvas)), canvas)
    alphas = {alpha_at(rgba, canvas, x, y) for x in range(20, 80) for y in range(20, 80)}
    assert any(0 < a < 255 for a in alphas)


def test_des_vcs_061_png_is_rgba_with_its_size():
    png = make_app.png_bytes(bytes(4 * 3 * 2), 3, 2)
    assert png.startswith(b"\x89PNG") and struct.unpack(">IIBB", png[16:26]) == (3, 2, 8, 6)


def test_des_vcs_061_logo_pixels_are_read_by_sips(tmp_path):
    rgb = make_app.read_rgb(logo_png(tmp_path / "logo.png"), 10)
    assert len(rgb) == 10 * 10 * 3 and rgb[:3] == bytes((200, 40, 40))


# ---------- the bundle ----------

def test_des_vcs_061_bundle_metadata_and_launcher():
    info = make_app.info_plist()
    assert (info["CFBundleName"], info["CFBundleIdentifier"], info["CFBundleExecutable"], info["CFBundleIconFile"],
            info["CFBundlePackageType"]) == ("vcs-lite", "io.github.m1981.vcs-lite", "vcs-lite", "vcs-lite.icns", "APPL")
    script = make_app.launcher(Path("/Users/x/PycharmProjects/byte-brewery"))
    assert script.startswith("#!/bin/sh\n")
    assert "cd '/Users/x/PycharmProjects/byte-brewery'" in script
    assert "exec '/Users/x/PycharmProjects/byte-brewery/.venv/bin/python' -m vcs_lite.ui.main \"$@\"" in script
    assert 'logs="$HOME/Library/Logs/vcs-lite"' in script and '2>>"$logs/vcs-lite.log"' in script


def test_at_vcs_047_the_app_is_built_replaced_and_a_foreign_one_is_left_alone(tmp_path):
    logo, repo, dest = logo_png(tmp_path / "logo.png"), tmp_path / "byte-brewery", tmp_path / "Applications"
    dest.mkdir()
    app = make_app.build_app(dest, repo=repo, logo=logo)
    assert app == dest / "vcs-lite.app"
    info = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    assert info["CFBundleName"] == "vcs-lite"
    launcher = app / "Contents" / "MacOS" / "vcs-lite"
    assert launcher.stat().st_mode & 0o111 and str(repo / ".venv" / "bin" / "python") in launcher.read_text()
    icns = app / "Contents" / "Resources" / "vcs-lite.icns"
    assert icns.read_bytes()[:4] == b"icns"
    iconset = tmp_path / "check.iconset"
    subprocess.run(["iconutil", "-c", "iconset", str(icns), "-o", str(iconset)], check=True)
    assert {p.name for p in iconset.iterdir()} >= {"icon_16x16.png", "icon_512x512@2x.png"}
    (app / "Contents" / "Resources" / "stary.txt").write_text("z poprzedniej wersji")
    again = make_app.build_app(dest, repo=repo, logo=logo)
    assert not (again / "Contents" / "Resources" / "stary.txt").exists()          # replaced as a whole
    assert [p.name for p in dest.iterdir()] == ["vcs-lite.app"]                    # no leftovers
    info["CFBundleIdentifier"] = "com.example.inna"
    (again / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info))
    with pytest.raises(make_app.ForeignApp, match="com.example.inna"):
        make_app.build_app(dest, repo=repo, logo=logo)
    assert plistlib.loads((again / "Contents" / "Info.plist").read_bytes())["CFBundleIdentifier"] == "com.example.inna"


def test_des_vcs_061_window_icon_is_a_small_shaped_png(tmp_path):
    target = make_app.write_window_icon(logo_png(tmp_path / "logo.png"), tmp_path / "icon.png")
    data = target.read_bytes()
    assert struct.unpack(">IIBB", data[16:26]) == (256, 256, 8, 6)
