"""Text files in the browser (pattern E-05): the side-by-side diff, and a plain page for reading.

Run as its own process, `python -m vcs_lite.core.textpage <left> <right> <left title> <right title> [--read]
[--line N] [--theme …] [--no-open]`, so the window's memory stays as it is (DES-VCS-059). Lines are aligned
by difflib; inside a changed pair the changed words are underlined like in the Markdown diff (DEC-VCS-087).
A binary side or one over 2 MB gives a message with the sizes instead (REQ-VCS-007).

Trace: DES-VCS-059, DES-VCS-008, DES-VCS-058, REQ-VCS-023, REQ-VCS-007, REQ-VCS-008, REQ-VCS-034, DEC-VCS-103, DEC-VCS-105, DEC-VCS-107, DEC-VCS-108
"""

from __future__ import annotations

import difflib
import html
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from vcs_lite.core import pagekit
from vcs_lite.core.filekind import SNIFF, TEXT_LIMIT
from vcs_lite.core.pagekit import BASE_CSS, SCROLL_TO_HIT

PAGES = pagekit.PAGES
CONTEXT = 3                         # unchanged lines shown around a change; longer runs fold
TOKENS = re.compile(r"\w+|\s+|[^\w\s]")
EMPTY_SIDE = "(pusty)"              # the title of a side that does not exist (a new or deleted file)


@dataclass(frozen=True)
class Row:
    kind: str                       # same, mod, add, del
    left: int | None = None         # line numbers, 1-based
    right: int | None = None
    left_html: str = ""
    right_html: str = ""


def lines_label(n: int) -> str:
    """Polish plural: 1 niezmieniona linia, 2–4 niezmienione linie (but 12–14 …linii), otherwise …linii."""
    if n == 1:
        return "1 niezmieniona linia"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} niezmienione linie"
    return f"{n} niezmienionych linii"


def size_label(n: int) -> str:
    """820 B, 1,3 kB, 1,2 MB: one decimal with a comma."""
    if n < 1024:
        return f"{n} B"
    value, unit = (n / 1024, "kB") if n < 1024 * 1024 else (n / 1024 / 1024, "MB")
    return f"{value:.1f}".replace(".", ",") + f" {unit}"


def side_name(title: str) -> str:
    """'app.py (indeks)' → 'indeks'."""
    return title.rsplit("(", 1)[-1].rstrip(")") if title.endswith(")") else title


def preview_problem(data: bytes) -> str | None:
    if len(data) > TEXT_LIMIT:
        return "Plik większy niż 2 MB: vcs-lite nie pokazuje różnic w jego treści."
    if b"\0" in data[:SNIFF]:
        return "Plik binarny: vcs-lite nie pokazuje różnic w jego treści."
    return None


def render_page(old: bytes, new: bytes, *, file_name: str, left_title: str, right_title: str, theme: str = "system",
                read: bool = False, line: int | None = None) -> str:
    """`read` shows the right side alone, `line` marks and scrolls to that line of it."""
    sides = html.escape(right_title if read else f"{left_title} → {right_title}")
    problem = preview_problem(new) if read else (preview_problem(old) or preview_problem(new))
    badge = stats = ""
    if problem:
        card = _message(problem, [(side_name(left_title), old), (side_name(right_title), new)][1 if read else 0:])
    elif read:
        card = _one_column([Row("same", right=i, right_html=html.escape(t)) for i, t in enumerate(_lines(new), 1)],
                           hit=line)
    elif not old and left_title.endswith(EMPTY_SIDE):
        badge, card = "nowy plik", _one_column([Row("add", right=i, right_html=html.escape(t))
                                                for i, t in enumerate(_lines(new), 1)])
        stats = _stats({"add": len(_lines(new))})
    elif not new and right_title.endswith(EMPTY_SIDE):
        badge, card = "usunięty plik", _one_column([Row("del", left=i, left_html=html.escape(t))
                                                    for i, t in enumerate(_lines(old), 1)], side="left")
        stats = _stats({"del": len(_lines(old))})
    else:
        rows = diff_rows(_lines(old), _lines(new))
        if all(r.kind == "same" for r in rows):
            card = '<p class="nochange">Bez zmian w treści.</p>'
        else:
            card = _two_columns(rows, side_name(left_title), side_name(right_title))
            stats = _stats({kind: sum(r.kind == kind for r in rows) for kind in ("add", "del", "mod")})
    bar = (f'<div class="bar"><span class="f">{html.escape(file_name)}</span><span class="sides">{sides}</span>'
           + (f'<span class="badge">{badge}</span>' if badge else "") + f"{stats}<span class=\"spacer\"></span></div>")
    body = f'{bar}\n<main><div class="card">{card}</div></main>'
    return pagekit.document(title=file_name, theme=theme, css=CSS, body=body, script=SCROLL_TO_HIT)


# ---------- aligning lines ----------

def diff_rows(old: list[str], new: list[str]) -> list[Row]:
    rows: list[Row] = []
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            rows += [Row("same", i + 1, j + 1, html.escape(old[i]), html.escape(new[j]))
                     for i, j in zip(range(i1, i2), range(j1, j2))]
            continue
        pairs = min(i2 - i1, j2 - j1) if op == "replace" else 0
        for k in range(pairs):
            left, right = mark_words(old[i1 + k], new[j1 + k])
            rows.append(Row("mod", i1 + k + 1, j1 + k + 1, left, right))
        rows += [Row("del", left=i + 1, left_html=html.escape(old[i])) for i in range(i1 + pairs, i2)]
        rows += [Row("add", right=j + 1, right_html=html.escape(new[j])) for j in range(j1 + pairs, j2)]
    return rows


def mark_words(old: str, new: str) -> tuple[str, str]:
    """Both lines escaped, with the changed words in <del> on the left and <ins> on the right."""
    a, b = TOKENS.findall(old), TOKENS.findall(new)
    left, right = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        old_part, new_part = html.escape("".join(a[i1:i2])), html.escape("".join(b[j1:j2]))
        if op == "equal":
            left.append(old_part)
            right.append(new_part)
            continue
        if old_part:
            left.append(f"<del>{old_part}</del>")
        if new_part:
            right.append(f"<ins>{new_part}</ins>")
    return "".join(left), "".join(right)


def _shown(rows: list[Row]) -> set[int]:
    changed = [i for i, r in enumerate(rows) if r.kind != "same"]
    return {j for i in changed for j in range(i - CONTEXT, i + CONTEXT + 1) if 0 <= j < len(rows)}


# ---------- drawing ----------

def _lines(data: bytes) -> list[str]:
    return data.decode("utf-8", errors="replace").splitlines()


def _number(n: int | None) -> str:
    return "" if n is None else str(n)


def _two_columns(rows: list[Row], left_name: str, right_name: str) -> str:
    shown, out, folded = _shown(rows), [], 0
    for index, row in enumerate(rows):
        if index not in shown:
            folded += 1
            continue
        if folded:
            out.append(f'<tr class="fold"><td colspan="4">⋯ {lines_label(folded)}</td></tr>')
            folded = 0
        out.append(f'<tr class="{row.kind}"><td class="n l">{_number(row.left)}</td><td class="c l">{row.left_html}</td>'
                   f'<td class="n r">{_number(row.right)}</td><td class="c r">{row.right_html}</td></tr>')
    if folded:
        out.append(f'<tr class="fold"><td colspan="4">⋯ {lines_label(folded)}</td></tr>')
    head = (f'<tr><th class="side" colspan="2">{html.escape(left_name)}</th>'
            f'<th class="side" colspan="2">{html.escape(right_name)}</th></tr>')
    return ('<table class="diff"><colgroup><col class="n"><col class="c"><col class="n"><col class="c"></colgroup>'
            + head + "".join(out) + "</table>")


def _one_column(rows: list[Row], *, side: str = "right", hit: int | None = None) -> str:
    out = []
    for row in rows:
        number, text = (row.left, row.left_html) if side == "left" else (row.right, row.right_html)
        marked = ' id="hit"' if number == hit else ""
        kind = f"{row.kind} hit" if marked else row.kind
        out.append(f'<tr class="{kind}"{marked}><td class="n">{_number(number)}</td><td class="c">{text}</td></tr>')
    return '<table class="diff one"><colgroup><col class="n"><col class="c"></colgroup>' + "".join(out) + "</table>"


def _message(problem: str, sides: list[tuple[str, bytes]]) -> str:
    sizes = "".join(f"<tr><td>{html.escape(name)}</td><td>{size_label(len(data))}</td></tr>" for name, data in sides)
    return (f'<div class="msg"><span class="sym">⊘</span><span class="h">Brak podglądu zmian</span>'
            f'<span class="d">{html.escape(problem)}</span><table>{sizes}</table></div>')


def _stats(counts: dict[str, int]) -> str:
    return (f'<span class="stats"><span class="a">+{counts.get("add", 0)}</span> '
            f'<span class="d">−{counts.get("del", 0)}</span> <span class="m">~{counts.get("mod", 0)}</span></span>')


def main(argv: Sequence[str] | None = None) -> int:
    args = pagekit.page_arguments("Diff lewo–prawo pliku tekstowego.").parse_args(argv)
    page = render_page(args.left.read_bytes(), args.right.read_bytes(), file_name=args.right_title.split(" (")[0],
                       left_title=args.left_title, right_title=args.right_title, theme=args.theme, read=args.read,
                       line=args.line)
    pagekit.publish(page, args.right_title, no_open=args.no_open, folder=PAGES)
    return 0


CSS = BASE_CSS + """
table.diff { width:100%; border-collapse:collapse; table-layout:fixed; font:13px/1.55 var(--mono); }
.diff col.n { width:52px; } .diff col.c { width:calc(50% - 52px); } .one col.c { width:calc(100% - 52px); }
.diff th.side { font:12px var(--font); color:var(--dim); text-align:left; padding:6px 12px; border-bottom:1px solid var(--line); }
.diff td { padding:0 12px; vertical-align:top; white-space:pre-wrap; overflow-wrap:anywhere; }
.diff td.n { padding:0 8px; text-align:right; color:var(--dim); background:var(--gutter); user-select:none; font-size:12px; }
.diff td.c + td.n { border-left:1px solid var(--line); }
.diff tr.del td.c.l, .diff tr.mod td.c.l { background:var(--del-soft); }
.diff tr.add td.c.r, .diff tr.mod td.c.r { background:var(--add-soft); }
.diff tr.del td.c.r, .diff tr.add td.c.l { background:repeating-linear-gradient(135deg, var(--filler) 0 6px, transparent 6px 12px); }
.diff tr.del td.n.l, .diff tr.mod td.n.l { color:var(--del); } .diff tr.add td.n.r, .diff tr.mod td.n.r { color:var(--add); }
.one tr.add td.c { background:var(--add-soft); } .one tr.add td.n { color:var(--add); }
.one tr.del td.c { background:var(--del-soft); } .one tr.del td.n { color:var(--del); }
.diff tr.fold td { font:12px var(--font); color:var(--dim); background:var(--gutter); border-top:1px dashed var(--line);
  border-bottom:1px dashed var(--line); padding:3px 12px; text-align:center; }
.nochange { padding:18px 24px; margin:0; }
.msg { padding:40px 24px; text-align:center; display:grid; gap:6px; justify-items:center; }
.msg .sym { font-size:26px; color:#b9bac0; } .msg .h { font-size:15px; font-weight:600; } .msg .d { color:var(--dim); }
.msg table { border-collapse:collapse; margin-top:8px; font-size:13px; }
.msg td { padding:3px 12px; border-bottom:1px solid var(--line); text-align:left; } .msg td + td { font-family:var(--mono); text-align:right; }
@media (max-width:700px) { .diff col.n { width:36px; } .diff td { padding:0 6px; } }
"""


if __name__ == "__main__":
    sys.exit(main())
