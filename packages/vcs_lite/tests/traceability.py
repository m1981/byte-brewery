"""Bidirectional traceability check for vcs-lite.

Reads docs/SPEC.md, docs/DESIGN.md, docs/ACCEPTANCE.feature, the test files and
the modules in src/vcs_lite, checks the rules REQ-VCS-200..207 and renders the
matrix written to docs/TRACE.md. Design: DES-VCS-040.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

PREFIXES = "NEED|REQ|DEC|UC|AT|VER|DES|Q|OBS|T|S"
ID_RE = re.compile(rf"\b(?:{PREFIXES})-VCS-\d+[a-z]?\b")
RANGE_RE = re.compile(rf"\b({PREFIXES})-VCS-(\d+)–(\d+)\b")
# A full ID (optionally a range) followed by bare numbers: "REQ-VCS-003, 004" or "Q-VCS-001–004 i 006".
SHORTHAND_RE = re.compile(rf"\b(?:{PREFIXES})-VCS-\d+[a-z]?(?:–\d+)?(?:,\s*\d{{2,3}}\b|\s+i\s+\d{{2,3}}\b)")
ROW_DEF_RE = re.compile(rf"^\| ((?:{PREFIXES})-VCS-\d+[a-z]?) \|", re.M)
HEADING_DEF_RE = re.compile(rf"^#{{2,4}} ((?:{PREFIXES})-VCS-\d+[a-z]?)\b", re.M)
TEST_NAME_RE = re.compile(r"^test_(at|req|des|ver|uc|t|s)_vcs_(\d+)_")
TRACE_LINE_RE = re.compile(r"^Trace:\s*(.+)$", re.M)


@dataclass
class Definition:
    id: str
    source: str
    text: str


@dataclass
class Scenario:
    at: str
    tags: list[str]
    confirmed: bool


@dataclass
class Corpus:
    definitions: dict[str, list[Definition]] = field(default_factory=lambda: defaultdict(list))
    references: list[tuple[str, str]] = field(default_factory=list)  # (id, source)
    shorthands: list[tuple[str, str]] = field(default_factory=list)  # (text, source)
    scenarios: list[Scenario] = field(default_factory=list)
    tests: list[tuple[str, str]] = field(default_factory=list)  # (function name, file)
    modules: dict[str, list[str] | None] = field(default_factory=dict)  # module -> ids or None


def expand_refs(text: str) -> list[str]:
    """Return every ID mentioned in text, with en dash ranges expanded."""
    ids = ID_RE.findall(text)
    for prefix, start, end in RANGE_RE.findall(text):
        width = len(start)
        ids += [f"{prefix}-VCS-{n:0{width}d}" for n in range(int(start), int(end) + 1)]
    return list(dict.fromkeys(ids))


def _sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into (defined id, body) for table rows and ID headings."""
    out = [(m.group(1), text[m.start(): text.find("\n", m.start())]) for m in ROW_DEF_RE.finditer(text)]
    heads = list(HEADING_DEF_RE.finditer(text))
    for i, m in enumerate(heads):
        nxt = text.find("\n#", m.end())
        out.append((m.group(1), text[m.start(): nxt if nxt != -1 else len(text)]))
    return out


def load_corpus(docs: Path, src: Path, tests: Path) -> Corpus:
    c = Corpus()
    for name in ("SPEC.md", "DESIGN.md"):
        text = (docs / name).read_text(encoding="utf-8")
        for id_, body in _sections(text):
            c.definitions[id_].append(Definition(id_, name, body))
        c.references += [(i, name) for i in expand_refs(text)]
        c.shorthands += [(m.group(0), name) for m in SHORTHAND_RE.finditer(text)]

    feature = (docs / "ACCEPTANCE.feature").read_text(encoding="utf-8")
    lines = feature.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(("Scenario", "Scenario Outline")) and i > 0 and lines[i - 1].strip().startswith("@"):
            tags = lines[i - 1].split()
            ats = [t for t in tags if t.startswith("@AT_VCS_")]
            if not ats:
                continue
            at = "AT-VCS-" + ats[0].removeprefix("@AT_VCS_")
            block_end = next((j for j in range(i + 1, len(lines)) if lines[j].strip().startswith("@")), len(lines))
            c.definitions[at].append(Definition(at, "ACCEPTANCE.feature", "\n".join(lines[i - 1: block_end])))
            c.scenarios.append(Scenario(at, tags, "@confirmed" in tags))
    for tag in re.findall(r"@((?:REQ|DEC|UC|VER)_VCS_\d+)", feature):
        prefix, _, num = tag.split("_")
        c.references.append((f"{prefix}-VCS-{num}", "ACCEPTANCE.feature"))
    c.shorthands += [(m.group(0), "ACCEPTANCE.feature") for m in SHORTHAND_RE.finditer(feature)]

    for path in sorted(tests.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                c.tests.append((node.name, path.name))

    for path in sorted(src.rglob("*.py")):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        m = TRACE_LINE_RE.search(doc)
        c.modules[str(path.relative_to(src.parent))] = expand_refs(m.group(1)) if m else None
    return c


def test_id(name: str) -> str | None:
    m = TEST_NAME_RE.match(name)
    return f"{m.group(1).upper()}-VCS-{m.group(2)}" if m else None


# ---------- relations ----------

def _rows(c: Corpus, prefix: str) -> dict[str, Definition]:
    return {k: v[0] for k, v in c.definitions.items() if k.startswith(prefix + "-")}


def cells(d: Definition) -> list[str]:
    return [x.strip() for x in d.text.strip().strip("|").split(" | ")]


def superseded(d: Definition) -> bool:
    """Status word must open the description cell; a mention elsewhere does not count."""
    return cells(d)[1].startswith("ZASTĄPIONE")


def withdrawn(d: Definition) -> bool:
    return cells(d)[1].startswith("WYCOFANE")


def des_exception(d: Definition) -> bool:
    """„bez DES: <powód>” counts only outside the description cell."""
    return any("bez DES:" in x for x in cells(d)[2:])


def links(d: Definition, prefix: str) -> set[str]:
    return {i for i in expand_refs(d.text) if i.startswith(prefix + "-") and i != d.id}


def req_to_at(c: Corpus) -> dict[str, set[str]]:
    out = defaultdict(set)
    for s in c.scenarios:
        for t in s.tags:
            if t.startswith("@REQ_VCS_"):
                out["REQ-VCS-" + t.removeprefix("@REQ_VCS_")].add(s.at)
    return out


def req_to(c: Corpus, prefix: str) -> dict[str, set[str]]:
    out = defaultdict(set)
    for id_, d in _rows(c, prefix).items():
        if prefix == "DES" and withdrawn(d):
            continue
        for r in links(d, "REQ"):
            out[r].add(id_)
    return out


def module_ids(c: Corpus) -> dict[str, set[str]]:
    """REQ -> modules, directly or through a DES the module traces to."""
    des_req = {k: links(v, "REQ") for k, v in _rows(c, "DES").items()}
    out = defaultdict(set)
    for mod, ids in c.modules.items():
        for i in ids or []:
            for r in ({i} if i.startswith("REQ-") else des_req.get(i, set())):
                out[r].add(mod)
    return out


def req_to_tests(c: Corpus) -> dict[str, set[str]]:
    at_req = {s.at: {"REQ-VCS-" + t.removeprefix("@REQ_VCS_") for t in s.tags if t.startswith("@REQ_VCS_")} for s in c.scenarios}
    out = defaultdict(set)
    for name, _ in c.tests:
        tid = test_id(name)
        for r in ({tid} if tid and tid.startswith("REQ-") else at_req.get(tid, set())):
            out[r].add(name)
    return out


# ---------- rules ----------

def check_200(c: Corpus) -> list[str]:
    return [f"{k} zdefiniowane {len(v)} razy: {', '.join(d.source for d in v)}" for k, v in sorted(c.definitions.items()) if len(v) > 1]


def check_201(c: Corpus) -> list[str]:
    errors = [f"skrót niedozwolony w {src}: „{txt}”" for txt, src in c.shorthands]
    errors += sorted({f"odwołanie do niezdefiniowanego {i} w {src}" for i, src in c.references if i not in c.definitions})
    return errors


def check_202(c: Corpus) -> list[str]:
    errors = []
    at, ver, des = req_to_at(c), req_to(c, "VER"), req_to(c, "DES")
    for r, d in sorted(_rows(c, "REQ").items()):
        if superseded(d):
            continue
        if not at[r] and not ver[r]:
            errors.append(f"{r} nie ma AT ani VER")
        if not des[r] and not des_exception(d):
            errors.append(f"{r} nie ma DES (ani wyjątku „bez DES: <powód>”)")
    return errors


def check_203(c: Corpus) -> list[str]:
    errors = [f"{s.at} nie ma tagu REQ" for s in c.scenarios if not any(t.startswith("@REQ_VCS_") for t in s.tags)]
    for prefix in ("VER", "DES"):
        for k, d in sorted(_rows(c, prefix).items()):
            if not (links(d, "REQ") | links(d, "DEC")):
                errors.append(f"{k} nie wskazuje żadnego REQ ani DEC")
    return errors


def check_204(c: Corpus) -> list[str]:
    errors = []
    for name, file in c.tests:
        tid = test_id(name)
        if tid is None:
            errors.append(f"{file}::{name} nie zaczyna się od ID (np. test_req_vcs_005_…)")
        elif tid not in c.definitions:
            errors.append(f"{file}::{name} wskazuje niezdefiniowane {tid}")
    return errors


def check_205(c: Corpus) -> list[str]:
    tested = {test_id(n) for n, _ in c.tests}
    return [f"{s.at} (@confirmed) nie ma testu test_{s.at.lower().replace('-', '_')}_…" for s in c.scenarios if s.confirmed and s.at not in tested]


def check_206(c: Corpus) -> list[str]:
    errors = []
    for mod, ids in sorted(c.modules.items()):
        if ids is None:
            errors.append(f"{mod}: docstring modułu nie ma linii „Trace: …”")
        elif not ids:
            errors.append(f"{mod}: linia „Trace:” nie zawiera żadnego ID")
        else:
            errors += [f"{mod}: Trace wskazuje niezdefiniowane {i}" for i in ids if i not in c.definitions]
    return errors


# ---------- matrix (REQ-VCS-207) ----------

def render_matrix(c: Corpus, warnings: list[str]) -> str:
    at, ver, des = req_to_at(c), req_to(c, "VER"), req_to(c, "DES")
    tests, mods = req_to_tests(c), module_ids(c)
    j = lambda s: ", ".join(sorted(s)) or "—"
    out = ["# vcs-lite — macierz śledzenia powiązań", "",
           "Plik generowany przez `tests/test_traceability.py` (REQ-VCS-207). Nie edytować ręcznie.", "",
           "## Wymaganie → projekt, scenariusze, weryfikacja, testy, kod", "",
           "| REQ | DES | AT | VER | Testy | Moduły |", "|---|---|---|---|---|---|"]
    for r, d in sorted(_rows(c, "REQ").items()):
        label = f"{r} (zastąpione)" if superseded(d) else r
        out.append(f"| {label} | {j(des[r])} | {j(at[r])} | {j(ver[r])} | {j(tests[r])} | {j(mods[r])} |")
    out += ["", "## Wstecz: scenariusz → wymagania", "", "| AT | Status | REQ |", "|---|---|---|"]
    for s in sorted(c.scenarios, key=lambda s: s.at):
        status = "confirmed" if s.confirmed else next((t[1:] for t in s.tags if t in ("@proposal", "@decision_pending", "@dormant")), "?")
        out.append(f"| {s.at} | {status} | {j('REQ-VCS-' + t.removeprefix('@REQ_VCS_') for t in s.tags if t.startswith('@REQ_VCS_'))} |")
    out += ["", "## Wstecz: decyzja projektowa → wymagania", "", "| DES | REQ |", "|---|---|"]
    for k, d in sorted(_rows(c, "DES").items()):
        out.append(f"| {k}{' (wycofane)' if withdrawn(d) else ''} | {j(links(d, 'REQ'))} |")
    out += ["", "## Wstecz: test → ID", "", "| Test | Plik | ID |", "|---|---|---|"]
    out += [f"| `{n}` | {f} | {test_id(n) or '—'} |" for n, f in sorted(c.tests)] or ["| — | — | — |"]
    out += ["", "## Wstecz: moduł → ID", "", "| Moduł | Trace |", "|---|---|"]
    out += [f"| `{m}` | {j(ids or [])} |" for m, ids in sorted(c.modules.items())] or ["| — | — |"]
    out += ["", "## Ostrzeżenia", ""] + ([f"- {w}" for w in warnings] or ["- brak"])
    return "\n".join(out) + "\n"
