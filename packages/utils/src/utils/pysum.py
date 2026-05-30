#!/usr/bin/env python3
"""
pysum — Python Project Structure Generator
==========================================
Parses Python files via AST and emits a compact Markdown summary of every
module's imports, classes (with inheritance and methods), and top-level
functions (with full typed signatures).

Usage
-----
  pysum                          # scan current directory
  pysum /path/to/project         # scan specific directory
  pysum > structure.md           # redirect to file
  find . -name '*.py' | pysum --pipe   # pipe explicit file list
  lsproj | pysum --pipe                # use lsproj whitelist then summarise

Pipe mode
---------
Pass --pipe (or -p) to read newline-separated .py paths from stdin.
Without the flag, pysum always scans the given directory, even when
stdin is not a tty (e.g. inside scripts, CI, or IDE terminals).

Gitignore / pruning
-------------------
Standard .gitignore patterns are respected automatically.  The following
directories are always pruned even without a .gitignore:
  .git  .venv  venv  __pycache__  build  dist  node_modules  .svelte-kit
  .next  .nuxt  .pytest_cache  .mypy_cache  .ruff_cache  *.egg-info
"""

import argparse
import ast
import os
import sys
import fnmatch
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Built-in ignore patterns (no external dependency required)
# ---------------------------------------------------------------------------

_BUILTIN_IGNORES: list[str] = [
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    ".svelte-kit",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    ".idea",
    ".vscode",
]

_BUILTIN_FILE_PATTERNS: list[str] = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
]


def _load_gitignore_patterns(project_dir: Path) -> list[str]:
    """Return merged list of built-in + .gitignore patterns."""
    patterns: list[str] = list(_BUILTIN_IGNORES)
    gi = project_dir / ".gitignore"
    if gi.exists():
        for raw in gi.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                # normalise leading slash (repo-root anchor) → strip it
                if line.startswith("/"):
                    line = line[1:]
                patterns.append(line)
    return patterns


def _should_ignore(path: Path, project_dir: Path, patterns: list[str]) -> bool:
    """
    Return True if *path* should be excluded from analysis.

    Matching strategy (no external deps, pure fnmatch):
      1. Each component of the relative path is tested against every pattern.
      2. The full relative path string is also tested.
      3. File-level glob patterns (*.pyc etc.) are tested against the name only.
    """
    try:
        rel = path.relative_to(project_dir)
    except ValueError:
        return True  # outside project — ignore

    rel_str = str(rel)
    name = path.name

    # Hidden files/dirs (except .gitignore itself)
    if name.startswith(".") and name != ".gitignore":
        return True

    for pattern in patterns:
        norm = pattern.rstrip("/")
        # Match any path component (handles 'node_modules', '__pycache__', …)
        for part in rel.parts:
            if fnmatch.fnmatch(part, norm):
                return True
        # Match full relative path string
        if fnmatch.fnmatch(rel_str, norm):
            return True
        # Match filename against glob patterns like *.pyc
        if fnmatch.fnmatch(name, norm):
            return True

    return False


# ---------------------------------------------------------------------------
# AST parsing helpers
# ---------------------------------------------------------------------------

class _ASTParser:
    """Extracts imports, classes, and top-level functions from a Python AST."""

    # ── public ──────────────────────────────────────────────────────────────

    def parse_file(self, file_path: str) -> dict[str, Any] | None:
        try:
            source = Path(file_path).read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError) as exc:
            print(f"Warning: skipping {file_path}: {exc}", file=sys.stderr)
            return None

        imports = self._extract_imports(tree)
        classes = self._extract_classes(tree)
        functions = self._extract_functions(tree)

        if not (imports or classes or functions):
            return None

        return {"imports": imports, "classes": classes, "functions": functions}

    # ── imports ─────────────────────────────────────────────────────────────

    def _extract_imports(self, tree: ast.Module) -> list[str]:
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join(a.name for a in node.names)
                imports.append(f"from {module} import {names}")
        return imports

    # ── classes ─────────────────────────────────────────────────────────────

    def _extract_classes(self, tree: ast.Module) -> list[dict[str, Any]]:
        classes: list[dict[str, Any]] = []
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            info: dict[str, Any] = {"name": node.name, "methods": []}
            bases = [self._name(b) for b in node.bases if self._name(b)]
            if bases:
                info["bases"] = bases
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    info["methods"].append(self._func_info(child))
            classes.append(info)
        return classes

    # ── top-level functions ─────────────────────────────────────────────────

    def _extract_functions(self, tree: ast.Module) -> list[dict[str, str]]:
        return [
            self._func_info(node)
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    # ── shared helpers ───────────────────────────────────────────────────────

    def _func_info(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, str]:
        args: list[str] = []

        for arg in node.args.args:
            s = arg.arg
            if arg.annotation:
                s += f": {self._annotation(arg.annotation)}"
            args.append(s)

        # Map defaults to the tail of the positional args list
        n_defaults = len(node.args.defaults)
        if n_defaults:
            offset = len(args) - n_defaults
            for i, default in enumerate(node.args.defaults):
                args[offset + i] += f"={self._default(default)}"

        if node.args.vararg:
            ann = (
                f": {self._annotation(node.args.vararg.annotation)}"
                if node.args.vararg.annotation
                else ""
            )
            args.append(f"*{node.args.vararg.arg}{ann}")
        if node.args.kwarg:
            ann = (
                f": {self._annotation(node.args.kwarg.annotation)}"
                if node.args.kwarg.annotation
                else ""
            )
            args.append(f"**{node.args.kwarg.arg}{ann}")

        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        sig = f"{prefix} {node.name}({', '.join(args)})"
        if node.returns:
            sig += f" -> {self._annotation(node.returns)}"

        return {"name": node.name, "signature": sig}

    def _annotation(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._name(node)
        if isinstance(node, ast.Subscript):
            val = self._annotation(node.value)
            slc = self._annotation(node.slice)
            return f"{val}[{slc}]"
        if isinstance(node, ast.Tuple):
            return ", ".join(self._annotation(e) for e in node.elts)
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Python 3.10+ X | Y union syntax
            return f"{self._annotation(node.left)} | {self._annotation(node.right)}"
        return "Any"

    def _name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            owner = self._name(node.value)
            return f"{owner}.{node.attr}" if owner else node.attr
        return ""

    def _default(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.List):
            return "[]"
        if isinstance(node, ast.Dict):
            return "{}"
        if isinstance(node, ast.Tuple):
            return "()"
        if isinstance(node, ast.Set):
            return "set()"
        if isinstance(node, ast.Call):
            func = self._name(node.func) if hasattr(node, "func") else ""
            return f"{func}()" if func else "..."
        return "..."


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

class _MarkdownWriter:
    """Converts parsed file structures into Markdown text."""

    def write(self, file_structures: dict[str, dict[str, Any]]) -> None:
        print("# Project Structure\n")
        for file_path, structure in file_structures.items():
            self._write_file(file_path, structure)

    def _write_file(self, file_path: str, structure: dict[str, Any]) -> None:
        print(f"## {file_path}")
        print("```python")

        if structure["imports"]:
            for imp in structure["imports"]:
                print(imp)
            print()

        for cls in structure["classes"]:
            header = cls["name"]
            if "bases" in cls:
                header += f"({', '.join(cls['bases'])})"
            print(f"class {header}")
            if cls["methods"]:
                for method in cls["methods"]:
                    print(f"    {method['signature']}")
            else:
                print("    pass")
            print()

        funcs = structure["functions"]
        for i, func in enumerate(funcs):
            print(func["signature"])
            if i < len(funcs) - 1:
                print()

        print("```\n")


# ---------------------------------------------------------------------------
# Core orchestration
# ---------------------------------------------------------------------------

class ProjectStructureGenerator:
    """Discovers Python files and drives parse + render."""

    def __init__(self, project_dir: str) -> None:
        self.project_dir = Path(project_dir).resolve()
        self._parser = _ASTParser()
        self._writer = _MarkdownWriter()
        self._ignore_patterns = _load_gitignore_patterns(self.project_dir)

    # ── public API ──────────────────────────────────────────────────────────

    def generate(self) -> None:
        """Scan project_dir, parse, and print Markdown."""
        files = self._find_python_files()
        self._render(files)

    def generate_from_files(self, python_files: list[str]) -> None:
        """Parse an explicit list of files (e.g. from stdin pipe)."""
        # Still honour gitignore for piped files
        filtered = [
            f for f in python_files
            if not _should_ignore(Path(f).resolve(), self.project_dir, self._ignore_patterns)
        ]
        self._render(filtered)

    def should_ignore(self, path: Path) -> bool:
        """Expose ignore check so callers can pre-filter."""
        return _should_ignore(path, self.project_dir, self._ignore_patterns)

    # ── internals ───────────────────────────────────────────────────────────

    def _find_python_files(self) -> list[str]:
        found: list[str] = []
        for root, dirs, files in os.walk(self.project_dir):
            root_path = Path(root)
            # Prune ignored dirs in-place (topdown=True default)
            dirs[:] = sorted(
                d for d in dirs
                if not _should_ignore(root_path / d, self.project_dir, self._ignore_patterns)
            )
            for fname in sorted(files):
                if not fname.endswith(".py"):
                    continue
                abs_f = root_path / fname
                if not _should_ignore(abs_f, self.project_dir, self._ignore_patterns):
                    found.append(str(abs_f))
        return found

    def _render(self, file_paths: list[str]) -> None:
        structures: dict[str, dict[str, Any]] = {}
        for fp in file_paths:
            rel = os.path.relpath(fp, self.project_dir)
            parsed = self._parser.parse_file(fp)
            if parsed:
                structures[rel] = parsed
        self._writer.write(structures)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pysum",
        description="Generate a compact Markdown summary of a Python project's structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pysum                                                 scan current directory
  pysum /path/to/project                                scan specific directory
  pysum > structure.md                                  save to file
  find . -name '*.py' | pysum --pipe                    pipe explicit file list
  find . -name '*.py' -not -path '*/tests/*' | pysum -p skip test files
  lsproj | pysum --pipe                                 lsproj whitelist then summarise
        """,
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory to analyse (default: current directory).",
    )
    parser.add_argument(
        "-p", "--pipe",
        action="store_true",
        help=(
            "Read newline-separated .py file paths from stdin instead of "
            "scanning project_dir.  Use this when piping from find/lsproj."
        ),
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Error: '{project_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    generator = ProjectStructureGenerator(str(project_dir))

    if args.pipe:
        # Explicit pipe mode: read .py paths from stdin
        piped: list[str] = []
        for line in sys.stdin:
            fp = line.strip()
            if fp.endswith(".py") and os.path.isfile(fp):
                piped.append(os.path.abspath(fp))
        if not piped:
            print("Error: no valid .py files received from stdin.", file=sys.stderr)
            sys.exit(1)
        generator.generate_from_files(piped)
    else:
        # Directory scan mode — always the default, even when stdin is not a tty
        generator.generate()


if __name__ == "__main__":
    main()
