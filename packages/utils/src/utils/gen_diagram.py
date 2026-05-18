#!/usr/bin/env python3
"""Generate a Graphviz DOT class diagram for a Python project."""

import argparse
import ast
import os
from pathlib import Path


DEFAULT_SKIP = [".venv", ".git", "__pycache__", "node_modules"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Graphviz DOT class diagram for a Python project."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to scan (default: current directory)",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        metavar="PREFIX",
        help="Additional path prefixes to skip",
    )
    return parser


def _base_name(node: ast.expr) -> str:
    return ast.unparse(node).split(".")[-1]


def collect_classes(root: Path, skip_prefixes: list[str]) -> dict[str, dict[str, object]]:
    classes: dict[str, dict[str, object]] = {}

    for dirpath, dirnames, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        dirnames[:] = sorted(
            d
            for d in dirnames
            if not d.startswith(".") and d not in ("__pycache__", "node_modules")
        )

        if rel_dir and any(
            rel_dir == prefix or rel_dir.startswith(prefix.rstrip("/") + "/")
            for prefix in skip_prefixes
        ):
            dirnames.clear()
            continue

        for filename in sorted(files):
            if not filename.endswith(".py"):
                continue

            path = Path(dirpath) / filename
            rel_file = os.path.relpath(path, root)
            if any(
                rel_file == prefix or rel_file.startswith(prefix.rstrip("/") + "/")
                for prefix in skip_prefixes
            ):
                continue

            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue

                methods = []
                attrs = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(child.name)
                    elif isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                attrs.append(target.id)

                classes[node.name] = {
                    "bases": [_base_name(base) for base in node.bases],
                    "methods": methods,
                    "attrs": attrs,
                    "file": rel_file,
                }

    return classes


def emit_dot(classes: dict[str, dict[str, object]]) -> None:
    print("digraph Architecture {")
    print("  rankdir=TB;")
    print("  node [shape=record fontname=Helvetica];")
    print()

    for name, info in classes.items():
        methods = info["methods"]
        attrs = info["attrs"]
        methods_str = r"\l".join(
            f"+ {method}()" for method in methods if not method.startswith("__")
        )
        attrs_str = r"\l".join(f"- {attr}" for attr in attrs)
        module = str(info["file"]).replace("/", ".").replace(".py", "")
        label = (
            f"{name}|"
            f"{attrs_str + r'\\l' if attrs_str else ''}"
            f"{methods_str + r'\\l' if methods_str else ''}"
        )
        print(f'  "{name}" [label="{{{label}}}" tooltip="{module}"];')

    print()
    for name, info in classes.items():
        for base in info["bases"]:
            if base in classes:
                print(f'  "{base}" -> "{name}" [arrowhead=onormal];')
    print()
    print("}")


def main() -> None:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    skip_prefixes = DEFAULT_SKIP + args.skip
    emit_dot(collect_classes(root, skip_prefixes))


if __name__ == "__main__":
    main()
