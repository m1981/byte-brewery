#!/usr/bin/env python3
"""
repo_map.py — print a compressed structural map of a Python project.

Usage:
    repo-map                          # full map, skips .venv/tests/data
    repo-map --skip tests data        # skip extra prefixes
    repo-map --only src/game src/quiz # only these prefixes
    repo-map --show-imports           # include import lines
    repo-map --all                    # include everything
"""

import argparse
import ast
import os
import subprocess
from pathlib import Path

try:
    from pathspec import PathSpec
    from pathspec.patterns import GitWildMatchPattern

    HAS_PATHSPEC = True
except ImportError:
    PathSpec = None
    GitWildMatchPattern = None
    HAS_PATHSPEC = False


DEFAULT_SKIP = [
    "data",
    ".venv",
    ".git",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
]

MEANINGFUL_NODES = (
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Import,
    ast.ImportFrom,
    ast.Assign,
    ast.AnnAssign,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a structural map of a Python project."
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        metavar="PREFIX",
        help="Additional path prefixes to skip (e.g. tests data)",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        metavar="PREFIX",
        help="Only include files under these prefixes (e.g. src/game src/quiz/domain)",
    )
    parser.add_argument(
        "--show-imports", action="store_true", help="Include import lines in output"
    )
    parser.add_argument(
        "--all", action="store_true", help="Disable all default skips — show everything"
    )
    parser.add_argument(
        "--root", default=".", help="Root directory to scan (default: current dir)"
    )
    return parser


def get_gitignore_spec(root: str) -> "PathSpec | set[str] | None":
    """Return ignore rules from git or .gitignore when available."""
    try:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "--directory",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        ignored_dirs = {
            line.rstrip("/") for line in result.stdout.splitlines() if line.strip()
        }
        if ignored_dirs:
            return ignored_dirs
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if HAS_PATHSPEC:
        gitignore = Path(root) / ".gitignore"
        if gitignore.exists():
            lines = gitignore.read_text(encoding="utf-8").splitlines()
            return PathSpec.from_lines(GitWildMatchPattern, lines)

    return None


def _format_args(args_node: ast.arguments) -> str:
    parts = []
    all_args = args_node.posonlyargs + args_node.args
    defaults_offset = len(all_args) - len(args_node.defaults)
    for i, arg in enumerate(all_args):
        di = i - defaults_offset
        if di >= 0:
            try:
                parts.append(f"{arg.arg}={ast.unparse(args_node.defaults[di])}")
            except Exception:
                parts.append(arg.arg)
        else:
            ann = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
            parts.append(f"{arg.arg}{ann}")
    if args_node.vararg:
        parts.append(f"*{args_node.vararg.arg}")
    if args_node.kwarg:
        parts.append(f"**{args_node.kwarg.arg}")
    return ", ".join(parts)


def _print_node(node: ast.AST, indent: int = 0) -> None:
    pad = "  " * indent

    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(b) for b in node.bases]
        base_str = f"({', '.join(bases)})" if bases else ""
        print(f"{pad}class {node.name}{base_str}  [line {node.lineno}]")
        for child in node.body:
            _print_node(child, indent + 1)

    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        args_str = _format_args(node.args)
        for dec in node.decorator_list:
            print(f"{pad}  @{ast.unparse(dec)}")
        print(f"{pad}  {prefix} {node.name}({args_str})  [line {node.lineno}]")

    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                print(f"{pad}  = {target.id}")

    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            ann = ast.unparse(node.annotation)
            print(f"{pad}  = {node.target.id}: {ann}")


def has_meaningful_content(tree: ast.Module) -> bool:
    """Return False for empty files or files with only docstrings/comments."""
    return any(isinstance(node, MEANINGFUL_NODES) for node in ast.walk(tree))


def summarize_file(path: str, show_imports: bool = False) -> None:
    rel = os.path.relpath(path)
    try:
        source = Path(path).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"\n⚠️  {rel} — SyntaxError: {e}")
        return
    except Exception as e:
        print(f"\n⚠️  {rel} — {e}")
        return

    if not has_meaningful_content(tree):
        return

    print(f"\n{'━' * 60}")
    print(f"📄 {rel}")
    print("━" * 60)

    if show_imports:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.asname or a.name for a in node.names]
                print(f"  import  {', '.join(names)}")
            elif isinstance(node, ast.ImportFrom):
                names = [a.asname or a.name for a in node.names]
                mod = node.module or ""
                print(f"  from    {mod} → {', '.join(names)}")

    for node in tree.body:
        _print_node(node, indent=0)


def make_gitignore_checker(root: str):
    gitignore = get_gitignore_spec(root)
    git_dirs: set[str] = gitignore if isinstance(gitignore, set) else set()
    git_spec = gitignore if HAS_PATHSPEC and not isinstance(gitignore, set) else None

    def is_gitignored(rel_path: str) -> bool:
        if rel_path in git_dirs:
            return True
        if any(rel_path.startswith(d + "/") for d in git_dirs):
            return True
        if git_spec and git_spec.match_file(rel_path):
            return True
        return False

    return is_gitignored


def iter_python_files(root: str, skip_prefixes: list[str], only_prefixes: list[str]):
    is_gitignored = make_gitignore_checker(root)

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        dirnames[:] = sorted(
            d
            for d in dirnames
            if not d.startswith(".") and d not in ("__pycache__", "node_modules")
        )

        if rel_dir and (
            any(
                rel_dir == p or rel_dir.startswith(p.rstrip("/") + "/")
                for p in skip_prefixes
            )
            or is_gitignored(rel_dir)
        ):
            dirnames.clear()
            continue

        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue

            rel_file = os.path.join(rel_dir, filename) if rel_dir else filename

            if any(
                rel_file == p or rel_file.startswith(p.rstrip("/") + "/")
                for p in skip_prefixes
            ) or is_gitignored(rel_file):
                continue

            if only_prefixes and not any(
                rel_file == p or rel_file.startswith(p.rstrip("/") + "/")
                for p in only_prefixes
            ):
                continue

            yield os.path.join(dirpath, filename)


def main() -> None:
    args = build_parser().parse_args()
    root = os.path.abspath(args.root)
    skip_prefixes = [] if args.all else DEFAULT_SKIP + args.skip

    for path in iter_python_files(root, skip_prefixes, args.only):
        summarize_file(path, show_imports=args.show_imports)


if __name__ == "__main__":
    main()
