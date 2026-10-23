"""Build vcs-lite.app, so vcs-lite opens from Finder, Launchpad and Spotlight with its own icon (REQ-VCS-104).

Usage: python tools/make_app.py [--dest /Applications]

The app is a small bundle (DES-VCS-061): Info.plist, a shell launcher that runs the code and the .venv of this
repository, and an icon made from assets/logo.png in the macOS shape: the logo 824 × 824 inside a rounded
square on a transparent 1024 canvas. Code changes need no rebuild; a new logo or a moved repository does.
Only the standard library, plus `sips` and `iconutil` that come with macOS. It also writes the small window
icon src/vcs_lite/ui/icon.png used when vcs-lite starts from a terminal (DES-VCS-062).
"""

from __future__ import annotations

import argparse
import os
import plistlib
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[1]
LOGO = PACKAGE / "assets" / "logo.png"
WINDOW_ICON = PACKAGE / "src" / "vcs_lite" / "ui" / "icon.png"
APP = "vcs-lite.app"
BUNDLE_ID = "io.github.m1981.vcs-lite"
CANVAS = 1024
BODY, RADIUS = 824 / 1024, 185.4 / 1024    # share of the canvas: the rounded square and its corner radius
SAMPLES = 4                                 # per side of a pixel on the rounded corners
ICONSET = [(size, scale) for size in (16, 32, 128, 256, 512) for scale in (1, 2)]


class ForeignApp(Exception):
    """A vcs-lite.app that this script did not build; it is never replaced."""


# ---------- the icon ----------

def body_side(canvas: int) -> int:
    return round(canvas * BODY)


def shape_icon(rgb: bytes, canvas: int) -> bytes:
    """RGBA rows of the canvas: the logo (`rgb`, body_side × body_side) in a rounded square, transparent
    around it; the rounded corners are smoothed by sampling each of their pixels SAMPLES × SAMPLES times."""
    side, radius = body_side(canvas), canvas * RADIUS
    margin = (canvas - side) // 2
    out = bytearray(canvas * canvas * 4)
    for y in range(side):
        for x in range(side):
            alpha = _coverage(x, y, side, radius)
            if alpha:
                source, target = (y * side + x) * 3, ((y + margin) * canvas + x + margin) * 4
                out[target:target + 4] = rgb[source:source + 3] + bytes((alpha,))
    return bytes(out)


def _coverage(x: int, y: int, side: int, radius: float) -> int:
    """How much of the pixel lies inside the rounded square, 0–255."""
    in_corner_column = x < radius or x >= side - radius
    in_corner_row = y < radius or y >= side - radius
    if not (in_corner_column and in_corner_row):
        return 255
    inside = 0
    for i in range(SAMPLES):
        for j in range(SAMPLES):
            px, py = x + (i + 0.5) / SAMPLES, y + (j + 0.5) / SAMPLES
            cx, cy = min(max(px, radius), side - radius), min(max(py, radius), side - radius)
            inside += (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2
    return round(255 * inside / SAMPLES ** 2)


def png_bytes(rgba: bytes, width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    rows = b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")


def read_rgb(image: Path, size: int) -> bytes:
    """The image scaled to size × size by sips, as RGB rows from the top."""
    with tempfile.TemporaryDirectory() as tmp:
        bmp = Path(tmp) / "logo.bmp"
        subprocess.run(["sips", "-s", "format", "bmp", "-z", str(size), str(size), str(image), "--out", str(bmp)],
                       check=True, capture_output=True)
        data = bmp.read_bytes()
    offset, = struct.unpack_from("<I", data, 10)
    width, height = struct.unpack_from("<ii", data, 18)
    step = struct.unpack_from("<H", data, 28)[0] // 8
    stride = (width * step + 3) & ~3
    rows = []
    for y in range(abs(height)):
        start = offset + (y if height < 0 else abs(height) - 1 - y) * stride   # positive height: bottom row first
        row = data[start:start + width * step]
        rows.append(b"".join(bytes((row[i + 2], row[i + 1], row[i])) for i in range(0, len(row), step)))  # BGR → RGB
    return b"".join(rows)


def icon_png(logo: Path, canvas: int) -> bytes:
    return png_bytes(shape_icon(read_rgb(logo, body_side(canvas)), canvas), canvas, canvas)


def make_icns(png: Path, icns: Path) -> None:
    iconset = icns.with_suffix(".iconset")
    iconset.mkdir()
    for size, scale in ICONSET:
        name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
        pixels = str(size * scale)
        subprocess.run(["sips", "-z", pixels, pixels, str(png), "--out", str(iconset / name)], check=True,
                       capture_output=True)
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)], check=True, capture_output=True)
    shutil.rmtree(iconset)


def write_window_icon(logo: Path = LOGO, target: Path = WINDOW_ICON) -> Path:
    """256 px is enough for the Dock and keeps the window's memory low (DES-VCS-062, REQ-VCS-100)."""
    target.write_bytes(icon_png(logo, 256))
    return target


# ---------- the bundle ----------

def info_plist() -> dict:
    return {"CFBundleName": "vcs-lite", "CFBundleDisplayName": "vcs-lite", "CFBundleIdentifier": BUNDLE_ID,
            "CFBundleExecutable": "vcs-lite", "CFBundleIconFile": "vcs-lite.icns", "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": "0.1", "LSMinimumSystemVersion": "12.0", "NSHighResolutionCapable": True}


def _quote(text: str) -> str:
    return "'" + text.replace("'", "'\\''") + "'"


def launcher(repo: Path) -> str:
    """Runs the code and the .venv of the repository, so a code change needs no rebuild; start-up errors go to
    a log, because an app opened from Finder has no terminal."""
    python = repo / ".venv" / "bin" / "python"
    return ("#!/bin/sh\n"
            'logs="$HOME/Library/Logs/vcs-lite"\n'
            'mkdir -p "$logs"\n'
            f"cd {_quote(str(repo))} || exit 1\n"
            f'exec {_quote(str(python))} -m vcs_lite.ui.main "$@" 2>>"$logs/vcs-lite.log"\n')


def _bundle_id(app: Path) -> str | None:
    try:
        return plistlib.loads((app / "Contents" / "Info.plist").read_bytes()).get("CFBundleIdentifier")
    except (OSError, plistlib.InvalidFileException):
        return None


def build_app(dest: Path, *, repo: Path = REPO, logo: Path = LOGO) -> Path:
    """Build next to the target, then swap: an existing vcs-lite.app is replaced only when it is ours."""
    target = dest / APP
    if target.exists() and (found := _bundle_id(target)) != BUNDLE_ID:
        raise ForeignApp(f"{target} należy do innej aplikacji ({found}); nie zastępuję jej.")
    work = Path(tempfile.mkdtemp(prefix=".vcs-lite-", dir=dest))
    try:
        app = work / APP
        (app / "Contents" / "MacOS").mkdir(parents=True)
        (app / "Contents" / "Resources").mkdir()
        (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info_plist()))
        program = app / "Contents" / "MacOS" / "vcs-lite"
        program.write_text(launcher(repo))
        program.chmod(0o755)
        png = work / "icon-1024.png"
        png.write_bytes(icon_png(logo, CANVAS))
        make_icns(png, app / "Contents" / "Resources" / "vcs-lite.icns")
        if target.exists():
            target.rename(work / "old.app")
        app.rename(target)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    os.utime(target)   # Finder and the Dock notice the new icon
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", type=Path, default=Path("/Applications"), help="folder aplikacji")
    args = parser.parse_args()
    print(f"Aplikacja: {build_app(args.dest)}")
    print(f"Ikona okna: {write_window_icon()}")


if __name__ == "__main__":
    main()
