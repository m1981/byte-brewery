#!/usr/bin/env python3
"""
lsproj — Project File Lister
=============================
Lists meaningful project files using a .projlist whitelist and .gitignore rules.

.projlist syntax
----------------
  *.py                   # bare glob  — matches filename anywhere in the tree
  src/*.py               # path glob  — fnmatch against relative path (single level)
  src/**/*.py            # ** glob    — recursive match (proper pathspec semantics)
  !tests/__init__.py     # negation   — exclude this path even if whitelisted
  # comment              # ignored

Key improvements over v1
------------------------
- Real ** / recursive glob support via pathspec (GitWildMatch)
- Negation patterns  (!pattern) in .projlist
- Sorted, deterministic output
- --list-patterns  to inspect effective whitelist
- --no-gitignore   to skip .gitignore filtering
- Graceful fallback when pathspec is missing (back to fnmatch)
- Proper hidden-file handling via .gitignore only (not hard-coded)
"""

import argparse
import os
import sys
import fnmatch
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = ".projlist"

# ---------------------------------------------------------------------------
# pathspec — optional but strongly preferred
# ---------------------------------------------------------------------------
try:
    from pathspec import PathSpec
    from pathspec.patterns import GitWildMatchPattern
    HAS_PATHSPEC = True
except ImportError:
    PathSpec = None  # type: ignore[assignment,misc]
    GitWildMatchPattern = None  # type: ignore[assignment,misc]
    HAS_PATHSPEC = False


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------

def _make_spec(patterns: list[str]) -> "PathSpec | None":
    """Build a PathSpec from a list of gitignore-style patterns."""
    if not HAS_PATHSPEC:
        return None
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


def _fnmatch_any(rel_path_str: str, patterns: list[str]) -> bool:
    """Fallback: match by filename OR full relative path using fnmatch."""
    filename = os.path.basename(rel_path_str)
    for pat in patterns:
        if fnmatch.fnmatch(filename, pat) or fnmatch.fnmatch(rel_path_str, pat):
            return True
    return False


def is_whitelisted(rel_path_str: str,
                   include_spec: "PathSpec | None",
                   exclude_spec: "PathSpec | None",
                   include_patterns: list[str],
                   exclude_patterns: list[str]) -> bool:
    """
    Return True when rel_path_str passes the whitelist and survives negations.
    Strategy:
      1. Must match at least one include pattern.
      2. Must NOT match any negation/exclude pattern.
    """
    if HAS_PATHSPEC and include_spec is not None:
        included = include_spec.match_file(rel_path_str)
        excluded = exclude_spec.match_file(rel_path_str) if exclude_spec else False
    else:
        # fnmatch fallback — no pathspec available
        included = _fnmatch_any(rel_path_str, include_patterns)
        excluded = _fnmatch_any(rel_path_str, exclude_patterns) if exclude_patterns else False

    return included and not excluded


def is_adhoc_excluded(rel_path_str: str,
                      adhoc_spec: "PathSpec | None",
                      adhoc_patterns: list[str]) -> bool:
    """Return True when rel_path_str matches any ad-hoc -e exclusion."""
    if not adhoc_patterns:
        return False
    if HAS_PATHSPEC and adhoc_spec is not None:
        return adhoc_spec.match_file(rel_path_str)
    return _fnmatch_any(rel_path_str, adhoc_patterns)


# ---------------------------------------------------------------------------
# .gitignore handling
# ---------------------------------------------------------------------------

BUILTIN_IGNORES = [
    ".git/",
    ".venv/",
    "venv/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "node_modules/",
    ".svelte-kit/",
    ".next/",
    ".nuxt/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".coverage",
    "build/",
    "dist/",
    "*.egg-info/",
]


def _load_gitignore_patterns(project_root: Path) -> list[str]:
    patterns = list(BUILTIN_IGNORES)
    gi = project_root / ".gitignore"
    if gi.exists():
        for line in gi.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def _make_gitignore_spec(project_root: Path) -> "PathSpec | None":
    if not HAS_PATHSPEC:
        return None
    return _make_spec(_load_gitignore_patterns(project_root))


def _should_gitignore(rel_path_str: str,
                      gi_spec: "PathSpec | None",
                      gi_patterns: list[str]) -> bool:
    if HAS_PATHSPEC and gi_spec is not None:
        return gi_spec.match_file(rel_path_str)
    # fnmatch fallback
    name = os.path.basename(rel_path_str)
    for pat in gi_patterns:
        pat = pat.rstrip("/")
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_path_str, pat):
            return True
    return False


# ---------------------------------------------------------------------------
# .projlist loading
# ---------------------------------------------------------------------------

def find_project_root(start: Path) -> Path:
    """Walk up until we find a directory containing .projlist."""
    for p in [start.resolve(), *start.resolve().parents]:
        if (p / CONFIG_FILENAME).exists():
            return p
    return start.resolve()


def load_projlist(config_path: Path) -> tuple[list[str], list[str]]:
    """
    Parse .projlist and return (include_patterns, exclude_patterns).
    Lines starting with '!' are negations (exclude).
    """
    includes: list[str] = []
    excludes: list[str] = []
    if not config_path.exists():
        return includes, excludes

    for raw in config_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            excludes.append(line[1:].strip())
        else:
            includes.append(line)

    return includes, excludes


# ---------------------------------------------------------------------------
# Directory pruning helpers
# ---------------------------------------------------------------------------

def _should_prune_dir(rel_dir_str: str,
                      gi_spec: "PathSpec | None",
                      gi_patterns: list[str]) -> bool:
    """
    Decide if an entire directory subtree can be skipped.
    We check both 'dir/' and 'dir' forms so gitignore dir patterns work.
    """
    as_dir = rel_dir_str.rstrip("/") + "/"
    return (
        _should_gitignore(rel_dir_str, gi_spec, gi_patterns)
        or _should_gitignore(as_dir, gi_spec, gi_patterns)
    )


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def collect_files(
    scan_dir: Path,
    project_root: Path,
    include_spec: "PathSpec | None",
    exclude_spec: "PathSpec | None",
    include_patterns: list[str],
    exclude_patterns: list[str],
    adhoc_spec: "PathSpec | None",
    adhoc_patterns: list[str],
    use_gitignore: bool,
    gi_spec: "PathSpec | None",
    gi_patterns: list[str],
    debug: bool,
) -> list[Path]:
    results: list[Path] = []

    for root, dirs, files in os.walk(scan_dir, topdown=True):
        root_path = Path(root)

        # Prune ignored directories in-place (topdown=True lets us modify dirs)
        if use_gitignore:
            pruned: list[str] = []
            for d in dirs:
                abs_d = root_path / d
                try:
                    rel_d = str(abs_d.relative_to(project_root))
                except ValueError:
                    rel_d = d
                if _should_prune_dir(rel_d, gi_spec, gi_patterns):
                    if debug:
                        print(f"DEBUG: prune dir  {rel_d}", file=sys.stderr)
                else:
                    pruned.append(d)
            dirs[:] = sorted(pruned)
        else:
            dirs[:] = sorted(dirs)

        for fname in sorted(files):
            abs_f = root_path / fname
            try:
                rel_f = abs_f.relative_to(project_root)
            except ValueError:
                continue
            rel_str = str(rel_f)

            # A. gitignore
            if use_gitignore and _should_gitignore(rel_str, gi_spec, gi_patterns):
                if debug:
                    print(f"DEBUG: gitignore  {rel_str}", file=sys.stderr)
                continue

            # B. whitelist + negations
            if not is_whitelisted(rel_str, include_spec, exclude_spec,
                                  include_patterns, exclude_patterns):
                continue

            # C. ad-hoc -e excludes
            if is_adhoc_excluded(rel_str, adhoc_spec, adhoc_patterns):
                if debug:
                    print(f"DEBUG: ad-hoc excl {rel_str}", file=sys.stderr)
                continue

            results.append(abs_f)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lsproj",
        description=(
            "List meaningful project files using a .projlist whitelist "
            "and .gitignore rules.\n\n"
            ".projlist syntax:\n"
            "  *.py                 match by filename anywhere\n"
            "  src/**/*.py          recursive glob (** supported)\n"
            "  !tests/__init__.py   negation — exclude even if whitelisted\n"
            "  # comment            ignored"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "scan_dir", nargs="?", default=".",
        help="Directory to scan (default: current directory)."
    )
    p.add_argument(
        "-o", "--output", metavar="FILE",
        help="Write output to FILE instead of stdout."
    )
    p.add_argument(
        "-e", "--exclude", action="append", default=[], metavar="PATTERN",
        help="Ad-hoc exclusion pattern (repeatable). E.g. -e '*.md' -e 'tests/*'."
    )
    p.add_argument(
        "--no-gitignore", action="store_true",
        help="Disable .gitignore / built-in ignore rules."
    )
    p.add_argument(
        "--list-patterns", action="store_true",
        help="Print effective whitelist patterns and exit."
    )
    p.add_argument(
        "--debug", action="store_true",
        help="Print debug info to stderr."
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Paths ────────────────────────────────────────────────────────────────
    scan_dir = Path(args.scan_dir).resolve()
    if not scan_dir.exists():
        print(f"Error: '{scan_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    project_root = find_project_root(scan_dir)
    config_file = project_root / CONFIG_FILENAME

    if args.debug:
        backend = "pathspec (GitWildMatch)" if HAS_PATHSPEC else "fnmatch (fallback)"
        print(f"DEBUG: scan_dir     = {scan_dir}", file=sys.stderr)
        print(f"DEBUG: project_root = {project_root}", file=sys.stderr)
        print(f"DEBUG: config_file  = {config_file}", file=sys.stderr)
        print(f"DEBUG: match backend= {backend}", file=sys.stderr)

    # ── Load .projlist ────────────────────────────────────────────────────────
    include_patterns, exclude_patterns = load_projlist(config_file)

    if not include_patterns:
        print(f"Error: no include patterns found in {config_file}", file=sys.stderr)
        print(f"Create {CONFIG_FILENAME} with lines like '*.py' or 'src/**/*.py'.",
              file=sys.stderr)
        sys.exit(1)

    if args.list_patterns:
        print(f"# .projlist — {config_file}")
        print(f"# match backend: {'pathspec' if HAS_PATHSPEC else 'fnmatch'}")
        print("\n# include:")
        for p in include_patterns:
            print(f"  {p}")
        if exclude_patterns:
            print("\n# negations (!…):")
            for p in exclude_patterns:
                print(f"  !{p}")
        if args.exclude:
            print("\n# ad-hoc -e:")
            for p in args.exclude:
                print(f"  -e {p}")
        sys.exit(0)

    # ── Build specs ───────────────────────────────────────────────────────────
    include_spec = _make_spec(include_patterns)
    exclude_spec = _make_spec(exclude_patterns) if exclude_patterns else None
    adhoc_spec   = _make_spec(args.exclude) if args.exclude else None

    use_gitignore = not args.no_gitignore
    gi_patterns   = _load_gitignore_patterns(project_root) if use_gitignore else []
    gi_spec       = _make_gitignore_spec(project_root) if use_gitignore else None

    # ── Collect ───────────────────────────────────────────────────────────────
    found = collect_files(
        scan_dir=scan_dir,
        project_root=project_root,
        include_spec=include_spec,
        exclude_spec=exclude_spec,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        adhoc_spec=adhoc_spec,
        adhoc_patterns=args.exclude,
        use_gitignore=use_gitignore,
        gi_spec=gi_spec,
        gi_patterns=gi_patterns,
        debug=args.debug,
    )

    # ── Output ────────────────────────────────────────────────────────────────
    cwd = Path.cwd()
    lines: list[str] = []
    for abs_f in found:
        try:
            lines.append(str(abs_f.relative_to(cwd)))
        except ValueError:
            lines.append(str(abs_f))

    output = "\n".join(lines)

    if args.output:
        try:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        except IOError as e:
            print(f"Error writing to '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if output:
            print(output)


if __name__ == "__main__":
    main()
