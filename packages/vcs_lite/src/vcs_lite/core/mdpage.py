"""The rendered Markdown diff page (pattern E-03): one document with the changes marked, and the source view.

Run as its own process, `python -m vcs_lite.core.mdpage <left> <right> <left title> <right title> [--base DIR]
[--no-open]`, so the window's memory stays as it is (DES-VCS-049). Raw HTML from the file is shown as text and
the page allows no scripts but its own view toggle, so nothing from a repository runs in the browser.

Trace: DES-VCS-049, REQ-VCS-031, DEC-VCS-078, DEC-VCS-079, DEC-VCS-081, DEC-VCS-082, DEC-VCS-084, DEC-VCS-086, DEC-VCS-087, REQ-VCS-032
"""

from __future__ import annotations

import argparse
import difflib
import html
import re
import sys
import tempfile
import time
import webbrowser
from collections.abc import Sequence
from pathlib import Path

from vcs_lite.core.mddiff import (DEL_END, DEL_START, INS_END, INS_START, MARKDOWN, Block, Change, State,
                                  diff_blocks, parse_blocks)

PAGES = Path(tempfile.gettempdir()) / "vcs-lite-md"
PAGE_LIFETIME = 24 * 3600   # older pages are removed when a new one is written
CONTEXT = 1                 # unchanged blocks shown around a change; longer runs fold
IMAGE = re.compile(r'<img src="[^"]*" alt="([^"]*)"[^>]*>')
OLD_IMAGES = re.compile(r"<del>.*?</del>", re.S)


def render_page(old_text: str, new_text: str, *, file_name: str, left_title: str, right_title: str,
                base: Path | None = None, theme: str = "system", read: bool = False) -> str:
    """`theme` light or dark overrides macOS; system follows it. `read` shows the new text as a plain
    document: no marks, no folding, no counts (a file without changes, REQ-VCS-032)."""
    changes = [Change(State.SAME, b) for b in parse_blocks(new_text)] if read else diff_blocks(old_text, new_text)
    counts = {state: sum(c.state is state for c in changes) for state in State}
    stats = "" if read else (f'<span class="stats"><span class="a">+{counts[State.ADD]}</span> '
                             f'<span class="d">−{counts[State.DEL]}</span> <span class="m">~{counts[State.MOD]}</span></span>')
    body = _rendered_view(changes, folding=not read)
    body = _labels_for_old_images(body) if base else IMAGE.sub(_image_label, body)
    base_tag = f'<base href="{html.escape(base.as_uri())}/">' if base else ""
    return TEMPLATE.format(
        theme="" if theme == "system" else f' data-theme="{theme}"',
        title=html.escape(file_name), base=base_tag, css=CSS, script=SCRIPT,
        sides=html.escape(right_title if read else f"{left_title} → {right_title}"), stats=stats,
        body=body, source=_source_view(old_text, new_text))


def write_page(page: str, file_name: str) -> Path:
    """Into one folder of pages; pages older than a day go, so the folder never grows."""
    PAGES.mkdir(parents=True, exist_ok=True)
    now = time.time()
    for stale in PAGES.glob("*.html"):
        if now - stale.stat().st_mtime > PAGE_LIFETIME:
            stale.unlink(missing_ok=True)
    stem = re.sub(r"[^\w.-]", "_", Path(file_name).stem)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=PAGES, prefix=f"{stem}-", suffix=".html",
                                     delete=False) as out:
        out.write(page)
    return Path(out.name)


def blocks_label(n: int) -> str:
    """Polish plural: 1 niezmieniony blok, 2–4 niezmienione bloki (but 12–14 …bloków), otherwise …bloków."""
    if n == 1:
        return "1 niezmieniony blok"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} niezmienione bloki"
    return f"{n} niezmienionych bloków"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vcs-lite-mdpage", description="Wyrenderowany diff Markdown.")
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("left_title")
    parser.add_argument("right_title")
    parser.add_argument("--base", type=Path, help="folder pliku w kopii roboczej, z którego ładują się obrazki")
    parser.add_argument("--no-open", action="store_true", help="tylko zapisz stronę i wypisz jej ścieżkę")
    parser.add_argument("--theme", choices=("system", "light", "dark"), default="system", help="kolory strony")
    parser.add_argument("--read", action="store_true", help="sam dokument z prawej strony, bez porównania")
    args = parser.parse_args(argv)
    page = render_page(_read(args.left), _read(args.right), file_name=args.right_title.split(" (")[0],
                       left_title=args.left_title, right_title=args.right_title, base=args.base, theme=args.theme,
                       read=args.read)
    path = write_page(page, args.right_title)
    print(path)
    if not args.no_open:
        webbrowser.open(path.as_uri())
    return 0


# ---------- the rendered view ----------

def _rendered_view(changes: list[Change], *, folding: bool = True) -> str:
    """Consecutive rows make one table, consecutive items one list; long unchanged runs fold."""
    if folding and all(c.state is State.SAME for c in changes):
        return '<p class="nochange">Bez zmian w treści (np. tylko inne łamanie linii).</p>'
    shown = _shown(changes) if folding else set(range(len(changes)))
    out: list[str] = []
    group: tuple | None = None   # ("table", id) or ("list", ordered) while one is open
    folded = 0

    def close_group() -> None:
        nonlocal group
        if group:
            out.append("</table>" if group[0] == "table" else "</ol>" if group[1] else "</ul>")
        group = None

    for index, change in enumerate(changes):
        if index not in shown:
            folded += 1
            continue
        if folded:
            close_group()
            out.append(f'<div class="fold">⋯ {blocks_label(folded)}</div>')
            folded = 0
        block, state = change.block, change.state.value
        content = _content(change)
        if block.kind in ("header", "row"):
            if group != ("table", block.table):
                close_group()
                out.append("<table>")
                group = ("table", block.table)
            out.append(content.replace("<tr>", f'<tr class="{state}">', 1))
        elif block.kind == "item":
            if group != ("list", block.ordered):
                close_group()
                out.append("<ol>" if block.ordered else "<ul>")
                group = ("list", block.ordered)
            value = f' value="{html.escape(block.number)}"' if block.ordered and block.number else ""
            out.append(f'<li class="{state}"{value} style="margin-left:{(block.depth - 1) * 22}px">{content}</li>')
        else:
            close_group()
            quote = f' quote" style="margin-left:{block.quote * 14}px' if block.quote else ""
            out.append(f'<div class="blk {state}{quote}">{content}</div>')
    close_group()
    if folded:
        out.append(f'<div class="fold">⋯ {blocks_label(folded)}</div>')
    return "\n".join(out)


def _shown(changes: list[Change]) -> set[int]:
    """Changed blocks with their neighbours, and the header of every table a shown row belongs to."""
    changed = [i for i, c in enumerate(changes) if c.state is not State.SAME]
    shown = {j for i in changed for j in range(i - CONTEXT, i + CONTEXT + 1) if 0 <= j < len(changes)}
    tables = {changes[i].block.table for i in shown if changes[i].block.kind in ("header", "row")}
    return shown | {i for i, c in enumerate(changes) if c.block.kind == "header" and c.block.table in tables}


def _content(change: Change) -> str:
    if change.state is State.MOD and change.marked is None:  # code and front matter: lines, not words
        return _lines(change.old, change.block)
    return _with_marks(_render(change.block, change.marked))


def _render(block: Block, src: str | None = None) -> str:
    src = block.src if src is None else src
    if block.kind == "paragraph":
        return f"<p>{MARKDOWN.renderInline(src)}</p>"
    if block.kind == "item":
        return MARKDOWN.renderInline(src)
    if block.kind == "heading":
        return f"<{block.tag}>{MARKDOWN.renderInline(src)}</{block.tag}>"
    if block.kind in ("header", "row"):
        tag = "th" if block.kind == "header" else "td"
        cells = src.split(" | ") if src != block.src else block.cells
        return "<tr>" + "".join(f"<{tag}>{MARKDOWN.renderInline(c)}</{tag}>" for c in cells) + "</tr>"
    if block.kind == "hr":
        return "<hr>"
    return f'<pre class="{block.kind}">{_language(block)}{html.escape(src)}</pre>'


def _lines(old: Block, new: Block) -> str:
    rows = []
    for line in difflib.ndiff(old.src.splitlines(), new.src.splitlines()):
        mark, text = line[:2], html.escape(line[2:]) or " "
        if mark != "? ":
            rows.append(f'<span class="ln {_LINE_CLASS.get(mark, "")}">{text}</span>')
    return f'<pre class="{new.kind}">{_language(new)}' + "".join(rows) + "</pre>"


def _language(block: Block) -> str:
    return f'<span class="lang">{html.escape(block.tag)}</span>' if block.kind == "code" and block.tag else ""


def _with_marks(fragment: str) -> str:
    return (fragment.replace(INS_START, "<ins>").replace(INS_END, "</ins>")
            .replace(DEL_START, "<del>").replace(DEL_END, "</del>"))


def _image_label(match: re.Match) -> str:
    return f'<span class="img-old">🖼 {match[1]}</span>'


def _labels_for_old_images(body: str) -> str:
    """Images of the earlier version are not on disk: the removed ones become their descriptions."""
    body = OLD_IMAGES.sub(lambda m: IMAGE.sub(_image_label, m[0]), body)
    return re.sub(r'(<(?:div|li|tr) class="(?:blk )?del[^"]*"[^>]*>)(.*?)(?=</(?:div|li|tr)>)',
                  lambda m: m[1] + IMAGE.sub(_image_label, m[2]), body, flags=re.S)


# ---------- the source view ----------

_LINE_CLASS = {"+ ": "add", "- ": "del"}


def _source_view(old_text: str, new_text: str) -> str:
    rows = []
    for line in difflib.ndiff(old_text.splitlines(), new_text.splitlines()):
        mark = line[:2]
        if mark != "? ":
            rows.append(f'<span class="ln {_LINE_CLASS.get(mark, "")}">{html.escape(mark + line[2:])}</span>')
    return '<pre class="raw">' + "\n".join(rows) + "</pre>"


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


# ---------- page template ----------

# Colours checked for contrast on 2026-10-23: text at least 4.5:1 on every background it sits on, change
# bars and word underlines at least 3:1 against the page. Dark lines of added and removed blocks stand
# 1.44:1 off the card and about 1.3:1 off code (they had 1.03–1.15).
LIGHT = ("--bg:#ffffff; --page:#f4f4f6; --line:#dedee3; --ink:#1d1d1f; --dim:#5f5f66; --link:#0a5dc2; "
         "--accent:#0a66d8; --code-bg:#f2f3f5; --add:#1a7f37; --add-soft:#ecf7ef; "
         "--del:#cf222e; --del-soft:#fdeeec; --mod:#b26a00; color-scheme:light;")
DARK = ("--bg:#1e1e21; --page:#121214; --line:#3a3a40; --ink:#e8e8ec; --dim:#a3a3ab; --link:#6cb6ff; "
        "--accent:#3d8bfd; --code-bg:#26272b; --add:#3fb950; --add-soft:#1f4029; "
        "--del:#f85149; --del-soft:#5f2828; --mod:#e3a33b; color-scheme:dark;")

CSS = f"""
:root {{ {LIGHT} --font:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,monospace; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ {DARK} }} }}
:root[data-theme="dark"] {{ {DARK} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--page); color:var(--ink); font:17px/1.6 var(--font); }}
a {{ color:var(--link); }}
.bar {{ position:sticky; top:0; display:flex; flex-wrap:wrap; gap:12px; align-items:center; padding:10px 20px;
  background:var(--bg); border-bottom:1px solid var(--line); font-size:13px; }}
.bar .f {{ font-weight:650; }} .bar .sides {{ color:var(--dim); }} .spacer {{ flex:1; }}
.stats {{ font:12px var(--mono); }} .stats .a {{ color:var(--add); }} .stats .d {{ color:var(--del); }} .stats .m {{ color:var(--mod); }}
.seg {{ display:inline-flex; border:1px solid var(--line); border-radius:6px; overflow:hidden; }}
.seg button {{ font:inherit; border:0; background:none; color:inherit; padding:3px 10px; cursor:pointer; }}
.seg button.on {{ background:var(--accent); color:#fff; }}
main {{ max-width:1200px; margin:0 auto; padding:16px; }}
.doc, .source {{ background:var(--bg); border-radius:10px; box-shadow:0 0 0 1px var(--line); }}
.doc {{ padding:18px 32px 24px; }}
.doc {{ font-family:"Open Sans",var(--font); font-synthesis:none; }}
.doc strong, .doc b, .doc th, .doc h1, .doc h2, .doc h3, .doc h4 {{ font-weight:600; }}
.doc h1 {{ font-size:26px; }} .doc h2 {{ font-size:21px; }} .doc h3 {{ font-size:18px; }}
.doc h1, .doc h2, .doc h3, .doc h4 {{ margin:14px 0 6px; }} .doc p, .doc ul, .doc ol, .doc pre {{ margin:0 0 8px; }}
.doc ul, .doc ol {{ padding-left:22px; }} .doc table {{ border-collapse:collapse; font-size:16px; margin:0 0 8px; }}
.doc td, .doc th {{ border:1px solid var(--line); padding:4px 10px; text-align:left; }}
.doc pre {{ font:15px/1.5 var(--mono); background:var(--code-bg); border-radius:6px; padding:8px 10px; overflow-x:auto; }}
.doc :not(pre) > code {{ font:0.9em var(--mono); background:var(--code-bg); border-radius:4px; padding:0 4px; }}
.doc pre.meta {{ color:var(--dim); background:none; border:1px dashed var(--line); }}
.doc pre .lang {{ float:right; color:var(--dim); font-size:13px; }}
.blk {{ padding:2px 0 2px 12px; margin-left:-15px; border-left:3px solid transparent; }}
.blk > :last-child {{ margin-bottom:2px; }}
.blk.add {{ border-left-color:var(--add); background:var(--add-soft); }}
.blk.del {{ border-left-color:var(--del); background:var(--del-soft); }}
.blk.mod {{ border-left-color:var(--mod); }}
.blk.quote {{ color:var(--dim); }}
li.add {{ background:var(--add-soft); box-shadow:-15px 0 0 -12px var(--add); }}
li.del {{ background:var(--del-soft); box-shadow:-15px 0 0 -12px var(--del); }}
li.mod {{ box-shadow:-15px 0 0 -12px var(--mod); }}
tr.add td, tr.add th {{ background:var(--add-soft); }} tr.del td, tr.del th {{ background:var(--del-soft); }}
ins {{ background:none; text-decoration:underline solid var(--add) 2px; text-underline-offset:3px; }}
del {{ background:none; text-decoration:underline dotted var(--del) 2px; text-underline-offset:3px; color:var(--dim); }}
ins code {{ box-shadow:0 0 0 1.5px var(--add); }} del code {{ box-shadow:0 0 0 1.5px var(--del); }}
ins a, del a {{ text-decoration:none; }}
.img-old {{ color:var(--dim); font-size:15px; }}
.doc img {{ max-width:100%; }}
.ln {{ display:block; }} .ln.add {{ background:var(--add-soft); }} .ln.del {{ background:var(--del-soft); }}
.fold {{ color:var(--dim); font-size:14px; border-top:1px dashed var(--line); border-bottom:1px dashed var(--line);
  padding:3px 0; margin:8px 0; }}
.nochange {{ color:var(--dim); }}
.source pre {{ margin:0; padding:14px 18px; font:15px/1.5 var(--mono); overflow-x:auto; }}
[hidden] {{ display:none !important; }}
"""

SCRIPT = """
document.querySelectorAll('.seg button').forEach(b => b.onclick = () => {
  document.querySelectorAll('.seg button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelector('.doc').hidden = b.dataset.view !== 'doc';
  document.querySelector('.source').hidden = b.dataset.view !== 'source';
});
"""

TEMPLATE = """<!doctype html>
<html lang="pl"{theme}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'unsafe-inline'; img-src file: data:">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,400;0,600;1,400&display=swap">
{base}
<title>{title} · vcs-lite</title>
<style>{css}</style>
</head>
<body>
<div class="bar"><span class="f">{title}</span><span class="sides">{sides}</span>
{stats}
<span class="spacer"></span>
<span class="seg"><button class="on" data-view="doc">Wyrenderowany</button><button data-view="source">Źródło</button></span></div>
<main><div class="doc">{body}</div><div class="source" hidden>{source}</div></main>
<script>{script}</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
