"""Parts every page vcs-lite opens in the browser shares: palette, template, policy, folder of pages, copies.

Pages are written by short processes (`mdpage`, `textpage`), so the window's memory stays as it is. Nothing
from a repository runs in the browser: the policy allows only the page's own script and local images. Pages
and copies of files live in one folder and go after a day, so it never grows.

Trace: DES-VCS-058, DES-VCS-049, DES-VCS-059, REQ-VCS-023, REQ-VCS-031, REQ-VCS-034, DEC-VCS-082, DEC-VCS-084
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import tempfile
import time
import webbrowser
from pathlib import Path

PAGES = Path(tempfile.gettempdir()) / "vcs-lite-md"
PAGE_LIFETIME = 24 * 3600   # older pages and copies are removed when a new one is written

# Colours checked for contrast on 2026-10-23: text at least 4.5:1 on every background it sits on, change
# bars and word underlines at least 3:1 against the page. Dark lines of added and removed blocks stand
# 1.44:1 off the card and about 1.3:1 off code (they had 1.03–1.15).
LIGHT = ("--bg:#ffffff; --page:#f4f4f6; --line:#dedee3; --ink:#1d1d1f; --dim:#5f5f66; --link:#0a5dc2; "
         "--accent:#0a66d8; --code-bg:#f2f3f5; --add:#1a7f37; --add-soft:#ecf7ef; "
         "--del:#cf222e; --del-soft:#fdeeec; --mod:#b26a00; --hit:#fde68a; "
         "--gutter:#f6f6f8; --filler:#f0f0f3; color-scheme:light;")
DARK = ("--bg:#1e1e21; --page:#121214; --line:#3a3a40; --ink:#e8e8ec; --dim:#a3a3ab; --link:#6cb6ff; "
        "--accent:#3d8bfd; --code-bg:#26272b; --add:#3fb950; --add-soft:#1f4029; "
        "--del:#f85149; --del-soft:#5f2828; --mod:#e3a33b; --hit:#5c4a12; "
        "--gutter:#232327; --filler:#26262a; color-scheme:dark;")

BASE_CSS = f"""
:root {{ {LIGHT} --font:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,monospace; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ {DARK} }} }}
:root[data-theme="dark"] {{ {DARK} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--page); color:var(--ink); font:15px/1.55 var(--font); }}
a {{ color:var(--link); }}
.bar {{ position:sticky; top:0; z-index:1; display:flex; flex-wrap:wrap; gap:12px; align-items:center; padding:10px 20px;
  background:var(--bg); border-bottom:1px solid var(--line); font-size:13px; }}
.bar .f {{ font-weight:650; }} .bar .sides {{ color:var(--dim); }} .spacer {{ flex:1; }}
.badge {{ font-size:12px; color:var(--dim); border:1px solid var(--line); border-radius:999px; padding:0 8px; }}
.stats {{ font:12px var(--mono); }} .stats .a {{ color:var(--add); }} .stats .d {{ color:var(--del); }} .stats .m {{ color:var(--mod); }}
.seg {{ display:inline-flex; border:1px solid var(--line); border-radius:6px; overflow:hidden; }}
.seg button {{ font:inherit; border:0; background:none; color:inherit; padding:3px 10px; cursor:pointer; }}
.seg button.on {{ background:var(--accent); color:#fff; }}
main {{ max-width:1200px; margin:0 auto; padding:16px; }}
.card {{ background:var(--bg); border-radius:10px; box-shadow:0 0 0 1px var(--line); overflow:hidden; }}
ins {{ background:none; text-decoration:underline solid var(--add) 2px; text-underline-offset:3px; }}
del {{ background:none; text-decoration:underline dotted var(--del) 2px; text-underline-offset:3px; color:var(--dim); }}
.nochange {{ color:var(--dim); }}
[hidden] {{ display:none !important; }}
.hit {{ animation:hit 2s ease-out; }} @keyframes hit {{ from {{ background:var(--hit); }} }}
"""

SCROLL_TO_HIT = """
const hit = document.getElementById('hit');
if (hit) hit.scrollIntoView({block: 'center'});
"""

POLICY = ("default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
          "font-src https://fonts.gstatic.com; script-src 'unsafe-inline'; img-src file: data:")
FONTS = ('<link rel="stylesheet" '
         'href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;1,400&display=swap">')

TEMPLATE = """<!doctype html>
<html lang="pl"{theme}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{policy}">
{fonts}
{base}
<title>{title} · vcs-lite</title>
<style>{css}</style>
</head>
<body>
{body}
<script>{script}</script>
</body>
</html>
"""


def document(*, title: str, theme: str, css: str, body: str, script: str, base: str = "", fonts: bool = False) -> str:
    """A whole page; `theme` light or dark overrides macOS, system follows it. `title` is escaped here."""
    return TEMPLATE.format(theme="" if theme == "system" else f' data-theme="{theme}"', policy=POLICY,
                           fonts=FONTS if fonts else "", base=base, title=html.escape(title), css=css, body=body,
                           script=script)


def _clean(folder: Path) -> None:
    now = time.time()
    for stale in folder.iterdir():
        if now - stale.stat().st_mtime <= PAGE_LIFETIME:
            continue
        if stale.is_dir():
            shutil.rmtree(stale, ignore_errors=True)
        else:
            stale.unlink(missing_ok=True)


def write_page(page: str, file_name: str, folder: Path = PAGES) -> Path:
    """Into the folder of pages, after removing what is older than a day."""
    folder.mkdir(parents=True, exist_ok=True)
    _clean(folder)
    stem = re.sub(r"[^\w.-]", "_", Path(file_name).stem)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=folder, prefix=f"{stem}-", suffix=".html",
                                     delete=False) as out:
        out.write(page)
    return Path(out.name)


def keep_copy(content: bytes, name: str, folder: Path = PAGES) -> Path:
    """A version that is not on disk (index, last commit) as a file the browser can open later (DES-VCS-060).
    Each copy has its own subfolder, so the name stays the file's own and the browser knows its type."""
    folder.mkdir(parents=True, exist_ok=True)
    _clean(folder)
    target = Path(tempfile.mkdtemp(prefix="copy-", dir=folder)) / Path(name).name
    target.write_bytes(content)
    return target


def page_arguments(description: str) -> argparse.ArgumentParser:
    """Arguments every page process takes: both sides, their titles, and how to show the page."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("left_title")
    parser.add_argument("right_title")
    parser.add_argument("--no-open", action="store_true", help="tylko zapisz stronę i wypisz jej ścieżkę")
    parser.add_argument("--theme", choices=("system", "light", "dark"), default="system", help="kolory strony")
    parser.add_argument("--read", action="store_true", help="sam dokument z prawej strony, bez porównania")
    parser.add_argument("--line", type=int, help="w trybie czytania: przewiń do tej linii pliku")
    return parser


def publish(page: str, title: str, *, no_open: bool, folder: Path = PAGES) -> Path:
    """Write the page, print where, and show it in the default browser unless asked not to."""
    path = write_page(page, title, folder)
    print(path)
    if not no_open:
        webbrowser.open(path.as_uri())
    return path


def read_text(path: Path) -> str:
    """UTF-8 with replacement characters for anything else (REQ-VCS-008)."""
    return path.read_bytes().decode("utf-8", errors="replace")
