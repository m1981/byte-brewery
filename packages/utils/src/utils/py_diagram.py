#!/usr/bin/env python3
"""
py_diagram — Token-Efficient Python Class/Type Diagram Generator
=================================================================

Produces class/type diagrams from Python source or project directories using
**only the standard library** (ast module).  Optional integrations with
``erdantic`` (Pydantic model ER diagrams) degrade gracefully when the library
is not installed.

Four output formats are supported — all are pure-Python text generation,
so no binary tools (Graphviz, PlantUML server, etc.) are required to *produce*
the text output:

  MERMAID   — Mermaid ``classDiagram`` block (renders in GitHub, Obsidian, etc.)
  DOT       — Graphviz DOT language (feed to ``dot -Tpng``)
  PLANTUML  — PlantUML ``@startuml`` / ``@enduml`` (feed to plantuml.jar)
  TOKEN     — Compressed, LLM-optimised structural representation

Design principles
-----------------
  * **Single responsibility** — each class owns one concern.
  * **Open / closed** — new renderers extend ``DiagramRenderer`` ABC.
  * **Dependency inversion** — facade depends on ABC, not concrete renderers.
  * **Testability** — every collaborator is injectable; AST work is isolated.
  * **Zero mandatory deps** — only stdlib + repo's existing deps (pydantic, networkx).

Public API
----------
  DiagramFormat          — Enum of supported output formats
  DiagramConfig          — validated configuration dataclass
  DiagramResult          — result object (diagram text + metadata)
  FieldInfo              — dataclass for a class field
  MethodInfo             — dataclass for a class method
  ClassInfo              — rich dataclass for an extracted class
  RelationshipKind       — Enum (INHERITS, COMPOSES, USES)
  RelationshipInfo       — dataclass for a directed relationship edge
  ASTClassExtractor      — pure-AST class extraction from source/file/directory
  RelationshipEngine     — derives relationships from a set of ClassInfo objects
  MermaidRenderer        — renders Mermaid classDiagram
  DotRenderer            — renders Graphviz DOT
  PlantUMLRenderer       — renders PlantUML
  TokenSerializer        — renders LLM-compressed representation
  ErdanticAdapter        — optional erdantic integration for Pydantic models
  PyDiagramFacade        — high-level façade orchestrating the full pipeline
  build_parser           — CLI argument parser
  main                   — CLI entry point

CLI
---
  py-diagram [root] [--format mermaid|dot|plantuml|token]
             [--output FILE] [--source FILE]
             [--skip DIR ...] [--max-classes N]
             [--include-private] [--include-dunder]

Examples
--------
  py-diagram src/mypackage
  py-diagram src/mypackage --format dot --output docs/classes.dot
  py-diagram --source mymodule.py --format plantuml
  py-diagram src/ --format token --max-classes 40
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DiagramFormat(str, Enum):
    """Supported diagram output formats."""
    MERMAID = "mermaid"
    DOT = "dot"
    PLANTUML = "plantuml"
    TOKEN = "token"


class RelationshipKind(str, Enum):
    """Types of relationships between classes."""
    INHERITS = "inherits"
    COMPOSES = "composes"
    USES = "uses"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class FieldInfo:
    """A class-level annotated field."""
    name: str
    type_hint: str = ""
    default: str = ""
    lineno: int | None = None


@dataclass
class MethodInfo:
    """A class method or function signature."""
    name: str
    params: list[tuple[str, str]] = field(default_factory=list)   # [(param_name, type_hint)]
    return_type: str = ""
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    lineno: int | None = None


@dataclass
class ClassInfo:
    """Rich structural description of a Python class."""
    name: str
    module: str
    bases: list[str] = field(default_factory=list)
    methods: list[MethodInfo] = field(default_factory=list)
    fields: list[FieldInfo] = field(default_factory=list)
    is_dataclass: bool = False
    is_abstract: bool = False
    decorators: list[str] = field(default_factory=list)
    lineno: int | None = None

    def token_repr(self, *, include_dunder: bool = False) -> str:
        """Return a compact, LLM-optimised string for this class.

        Format::

            [CLASS] Dog(Animal) [module=animals] [line 42]
              FIELDS: breed:str
              METHODS: fetch(item:str)->bool
        """
        base_str = f"({', '.join(self.bases)})" if self.bases else ""
        tag = ""
        if self.is_dataclass:
            tag = " @dataclass"
        if self.is_abstract:
            tag += " @abstract"
        lineno_str = f" [line {self.lineno}]" if self.lineno else ""
        header = f"[CLASS] {self.name}{base_str} [module={self.module}]{tag}{lineno_str}"

        parts = [header]

        visible_fields = self.fields
        if visible_fields:
            field_strs = [
                f"{f.name}:{f.type_hint}" if f.type_hint else f.name
                for f in visible_fields
            ]
            parts.append(f"  FIELDS: {', '.join(field_strs)}")

        visible_methods = [
            m for m in self.methods
            if (include_dunder or not m.name.startswith("__"))
        ]
        if visible_methods:
            method_strs = []
            for m in visible_methods:
                param_str = ", ".join(
                    f"{n}:{t}" if t else n
                    for n, t in m.params
                )
                ret = f"->{m.return_type}" if m.return_type else ""
                lineno = f" [line {m.lineno}]" if m.lineno else ""
                method_strs.append(f"{m.name}({param_str}){ret}{lineno}")
            parts.append(f"  METHODS: {', '.join(method_strs)}")

        return "\n".join(parts)


@dataclass
class FunctionInfo:
    """A top-level (module-level) function."""
    name: str
    module: str
    params: list[tuple[str, str]] = field(default_factory=list)
    return_type: str = ""
    is_async: bool = False
    lineno: int | None = None


@dataclass
class ImportInfo:
    """A top-level import statement."""
    module: str
    names: list[str]  # imported names
    source: str  # the 'from X' or 'import X' source
    lineno: int | None = None


@dataclass
class RelationshipInfo:
    """A directed relationship between two classes."""
    source: str
    target: str
    kind: RelationshipKind
    label: str = ""


@dataclass
class DiagramConfig:
    """Validated configuration for a diagram generation run."""
    output_format: DiagramFormat = DiagramFormat.MERMAID
    output_path: Path | None = None
    include_private: bool = False
    include_dunder: bool = False
    max_classes: int | None = None
    skip_dirs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.output_path is not None:
            self.output_path = Path(self.output_path)


@dataclass
class DiagramResult:
    """Result of a diagram generation run."""
    diagram: str
    classes: list[ClassInfo]
    relationships: list[RelationshipInfo]
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)

    @property
    def class_count(self) -> int:
        return len(self.classes)

    @property
    def function_count(self) -> int:
        return len(self.functions)

    @property
    def import_count(self) -> int:
        return len(self.imports)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)


# ---------------------------------------------------------------------------
# Default skip directories
# ---------------------------------------------------------------------------

_DEFAULT_SKIP_DIRS: list[str] = [
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "build", "dist",
]

# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _unparse_annotation(node: ast.AST | None) -> str:
    """Convert an annotation AST node to its string representation."""
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _extract_type_names(type_hint: str) -> set[str]:
    """Extract all identifiers from a composite type hint string."""
    if not type_hint:
        return set()
    # Extract all identifier tokens from type hint (e.g. "List[Animal]" -> {"List", "Animal"})
    return set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", type_hint))


# ---------------------------------------------------------------------------
# ASTClassExtractor
# ---------------------------------------------------------------------------


class ASTClassExtractor:
    """Extracts ClassInfo objects from Python source using the ast module.

    No external dependencies — 100% standard library.
    """

    def extract_from_source(
        self,
        source: str,
        *,
        module_name: str = "",
        include_private: bool = False,
        include_dunder: bool = False,
    ) -> list[ClassInfo]:
        """Parse *source* string and return all ClassInfo objects found."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        return self._extract_classes(
            tree, module_name=module_name,
            include_private=include_private,
            include_dunder=include_dunder,
        )

    def extract_from_file(
        self,
        path: Path,
        *,
        include_private: bool = False,
        include_dunder: bool = False,
    ) -> list[ClassInfo]:
        """Read *path* and return ClassInfo objects."""
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            return []
        module_name = path.stem
        return self.extract_from_source(
            source,
            module_name=module_name,
            include_private=include_private,
            include_dunder=include_dunder,
        )

    def extract_from_directory(
        self,
        root: Path,
        *,
        skip_dirs: list[str] | None = None,
        include_private: bool = False,
        include_dunder: bool = False,
    ) -> list[ClassInfo]:
        """Walk *root* recursively and collect ClassInfo from all .py files."""
        effective_skip = set(_DEFAULT_SKIP_DIRS + (skip_dirs or []))
        all_classes: list[ClassInfo] = []

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune skipped directories in-place
            dirnames[:] = sorted(
                d for d in dirnames if d not in effective_skip
            )
            for filename in sorted(filenames):
                if not filename.endswith(".py"):
                    continue
                file_path = Path(dirpath) / filename
                rel = file_path.relative_to(root)
                # Build dotted module name from relative path
                parts = list(rel.with_suffix("").parts)
                module_name = ".".join(parts)
                classes = self.extract_from_file(
                    file_path,
                    include_private=include_private,
                    include_dunder=include_dunder,
                )
                # Override the module name with the full dotted path
                for cls in classes:
                    cls.module = module_name
                all_classes.extend(classes)

        return all_classes

    def extract_functions_from_source(
        self,
        source: str,
        *,
        module_name: str = "",
    ) -> list[FunctionInfo]:
        """Parse *source* and return all top-level FunctionInfo objects."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        return self._extract_functions(tree, module_name=module_name)

    def extract_functions_from_directory(
        self,
        root: Path,
        *,
        skip_dirs: list[str] | None = None,
    ) -> list[FunctionInfo]:
        """Walk *root* and collect top-level FunctionInfo from all .py files."""
        effective_skip = set(_DEFAULT_SKIP_DIRS + (skip_dirs or []))
        all_functions: list[FunctionInfo] = []

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                d for d in dirnames if d not in effective_skip
            )
            for filename in sorted(filenames):
                if not filename.endswith(".py"):
                    continue
                file_path = Path(dirpath) / filename
                rel = file_path.relative_to(root)
                parts = list(rel.with_suffix("").parts)
                module_name = ".".join(parts)
                try:
                    source = file_path.read_text(encoding="utf-8")
                except OSError:
                    continue
                functions = self.extract_functions_from_source(
                    source, module_name=module_name,
                )
                all_functions.extend(functions)

        return all_functions

    def extract_imports_from_source(
        self,
        source: str,
        *,
        module_name: str = "",
    ) -> list[ImportInfo]:
        """Parse *source* and return all top-level ImportInfo objects."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        return self._extract_imports(tree, module_name=module_name)

    def extract_imports_from_directory(
        self,
        root: Path,
        *,
        skip_dirs: list[str] | None = None,
    ) -> list[ImportInfo]:
        """Walk *root* and collect top-level ImportInfo from all .py files."""
        effective_skip = set(_DEFAULT_SKIP_DIRS + (skip_dirs or []))
        all_imports: list[ImportInfo] = []

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                d for d in dirnames if d not in effective_skip
            )
            for filename in sorted(filenames):
                if not filename.endswith(".py"):
                    continue
                file_path = Path(dirpath) / filename
                rel = file_path.relative_to(root)
                parts = list(rel.with_suffix("").parts)
                module_name = ".".join(parts)
                try:
                    source = file_path.read_text(encoding="utf-8")
                except OSError:
                    continue
                imports = self.extract_imports_from_source(
                    source, module_name=module_name,
                )
                all_imports.extend(imports)

        return all_imports

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_classes(
        self,
        tree: ast.Module,
        *,
        module_name: str,
        include_private: bool,
        include_dunder: bool,
    ) -> list[ClassInfo]:
        classes: list[ClassInfo] = []
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            classes.append(
                self._build_class_info(
                    node,
                    module_name=module_name,
                    include_private=include_private,
                    include_dunder=include_dunder,
                )
            )
        return classes

    def _build_class_info(
        self,
        node: ast.ClassDef,
        *,
        module_name: str,
        include_private: bool,
        include_dunder: bool,
    ) -> ClassInfo:
        bases = [_unparse_annotation(b).split(".")[-1] for b in node.bases]
        decorators = [_unparse_annotation(d).split("(")[0] for d in node.decorator_list]
        is_dataclass = any(
            d in ("dataclass", "dataclasses.dataclass") for d in decorators
        )
        is_abstract = any(
            b in ("ABC", "ABCMeta", "abc.ABC", "abc.ABCMeta") for b in bases
        )

        methods = self._extract_methods(
            node,
            include_private=include_private,
            include_dunder=include_dunder,
        )
        fields = self._extract_fields(node)

        return ClassInfo(
            name=node.name,
            module=module_name,
            bases=bases,
            methods=methods,
            fields=fields,
            is_dataclass=is_dataclass,
            is_abstract=is_abstract,
            decorators=decorators,
            lineno=node.lineno,
        )

    def _extract_methods(
        self,
        node: ast.ClassDef,
        *,
        include_private: bool,
        include_dunder: bool,
    ) -> list[MethodInfo]:
        methods: list[MethodInfo] = []
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            name = child.name
            if not include_dunder and name.startswith("__"):
                continue
            if not include_private and name.startswith("_") and not name.startswith("__"):
                continue
            decorators = [_unparse_annotation(d) for d in child.decorator_list]
            is_classmethod = "classmethod" in decorators
            is_staticmethod = "staticmethod" in decorators

            # Build params list, excluding 'self' and 'cls'
            params: list[tuple[str, str]] = []
            all_args = child.args.args
            for arg in all_args:
                if arg.arg in ("self", "cls"):
                    continue
                type_hint = _unparse_annotation(arg.annotation)
                params.append((arg.arg, type_hint))
            # vararg and kwarg
            if child.args.vararg and child.args.vararg.arg not in ("self", "cls"):
                t = _unparse_annotation(child.args.vararg.annotation)
                params.append((f"*{child.args.vararg.arg}", t))
            if child.args.kwarg and child.args.kwarg.arg not in ("self", "cls"):
                t = _unparse_annotation(child.args.kwarg.annotation)
                params.append((f"**{child.args.kwarg.arg}", t))

            return_type = _unparse_annotation(child.returns)

            methods.append(MethodInfo(
                name=name,
                params=params,
                return_type=return_type,
                is_async=isinstance(child, ast.AsyncFunctionDef),
                is_classmethod=is_classmethod,
                is_staticmethod=is_staticmethod,
                lineno=child.lineno,
            ))
        return methods

    def _extract_fields(self, node: ast.ClassDef) -> list[FieldInfo]:
        fields: list[FieldInfo] = []
        seen: set[str] = set()
        for child in node.body:
            # class-level annotated assignments: name: Type = default
            if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                name = child.target.id
                if name in seen or name.startswith("__"):
                    continue
                seen.add(name)
                type_hint = _unparse_annotation(child.annotation)
                default = _unparse_annotation(child.value) if child.value else ""
                fields.append(FieldInfo(name=name, type_hint=type_hint, default=default, lineno=child.lineno))
            # class-level plain assignments: name = value
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        if target.id not in seen:
                            seen.add(target.id)
                            fields.append(FieldInfo(name=target.id, type_hint=""))
        return fields

    def _extract_functions(
        self,
        tree: ast.Module,
        *,
        module_name: str,
    ) -> list[FunctionInfo]:
        """Extract only top-level functions (not methods inside classes)."""
        functions: list[FunctionInfo] = []
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            params: list[tuple[str, str]] = []
            for arg in node.args.args:
                if arg.arg in ("self", "cls"):
                    continue
                type_hint = _unparse_annotation(arg.annotation)
                params.append((arg.arg, type_hint))
            if node.args.vararg and node.args.vararg.arg not in ("self", "cls"):
                t = _unparse_annotation(node.args.vararg.annotation)
                params.append((f"*{node.args.vararg.arg}", t))
            if node.args.kwarg and node.args.kwarg.arg not in ("self", "cls"):
                t = _unparse_annotation(node.args.kwarg.annotation)
                params.append((f"**{node.args.kwarg.arg}", t))
            return_type = _unparse_annotation(node.returns)
            functions.append(FunctionInfo(
                name=node.name,
                module=module_name,
                params=params,
                return_type=return_type,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                lineno=node.lineno,
            ))
        return functions

    def _extract_imports(
        self,
        tree: ast.Module,
        *,
        module_name: str,
    ) -> list[ImportInfo]:
        """Extract only top-level import statements."""
        imports: list[ImportInfo] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
                source = f"import {', '.join(names)}"
                imports.append(ImportInfo(
                    module=module_name,
                    names=names,
                    source=source,
                    lineno=node.lineno,
                ))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = [alias.name for alias in node.names]
                source = f"from {mod} import {', '.join(names)}"
                imports.append(ImportInfo(
                    module=module_name,
                    names=names,
                    source=source,
                    lineno=node.lineno,
                ))
        return imports


# ---------------------------------------------------------------------------
# RelationshipEngine
# ---------------------------------------------------------------------------


class RelationshipEngine:
    """Derives RelationshipInfo edges from a set of ClassInfo objects.

    Rules
    -----
    INHERITS  — cls.bases contains a known class name
    COMPOSES  — cls.fields has a type_hint that references a known class name
    USES      — cls.methods have params whose type_hint references a known class name
    """

    def extract(self, classes: list[ClassInfo]) -> list[RelationshipInfo]:
        known_names: set[str] = {c.name for c in classes}
        seen: set[tuple[str, str, RelationshipKind]] = set()
        relationships: list[RelationshipInfo] = []

        def _add(source: str, target: str, kind: RelationshipKind, label: str = "") -> None:
            key = (source, target, kind)
            if key not in seen:
                seen.add(key)
                relationships.append(RelationshipInfo(
                    source=source, target=target, kind=kind, label=label,
                ))

        for cls in classes:
            # INHERITS
            for base in cls.bases:
                if base in known_names:
                    _add(cls.name, base, RelationshipKind.INHERITS)

            # COMPOSES — from field type hints
            for fld in cls.fields:
                for type_name in _extract_type_names(fld.type_hint):
                    if type_name in known_names and type_name != cls.name:
                        _add(cls.name, type_name, RelationshipKind.COMPOSES, label=fld.name)

            # USES — from method parameter type hints
            for method in cls.methods:
                for _param_name, type_hint in method.params:
                    for type_name in _extract_type_names(type_hint):
                        if type_name in known_names and type_name != cls.name:
                            _add(cls.name, type_name, RelationshipKind.USES)

        return relationships


# ---------------------------------------------------------------------------
# Renderer ABC
# ---------------------------------------------------------------------------


class DiagramRenderer(ABC):
    """Abstract base for all diagram renderers."""

    @abstractmethod
    def render(
        self,
        classes: list[ClassInfo],
        relationships: list[RelationshipInfo],
        config: DiagramConfig,
        *,
        functions: list[FunctionInfo] | None = None,
        imports: list[ImportInfo] | None = None,
    ) -> str:
        """Return the complete diagram as a string."""


# ---------------------------------------------------------------------------
# MermaidRenderer
# ---------------------------------------------------------------------------


class MermaidRenderer(DiagramRenderer):
    """Renders a Mermaid ``classDiagram`` block.

    Output is compatible with GitHub, GitLab, Obsidian, and any Markdown
    renderer that supports Mermaid.
    """

    def render(
        self,
        classes: list[ClassInfo],
        relationships: list[RelationshipInfo],
        config: DiagramConfig,
        *,
        functions: list[FunctionInfo] | None = None,
        imports: list[ImportInfo] | None = None,
    ) -> str:
        lines = ["classDiagram"]

        for cls in classes:
            lines.extend(self._render_class(cls, config))

        lines.append("")  # blank line before relationships

        for rel in relationships:
            lines.append(self._render_relationship(rel))

        if functions:
            lines.append("")
            # Group functions by module
            modules: dict[str, list[FunctionInfo]] = {}
            for fn in functions:
                modules.setdefault(fn.module, []).append(fn)
            for module_name, module_funcs in modules.items():
                safe_name = module_name.replace(".", "_")
                lines.append(f'    class {safe_name}_module {{')
                lines.append(f'        <<module>>')
                for fn in module_funcs:
                    param_str = ", ".join(
                        f"{t} {n}" if t else n
                        for n, t in fn.params
                    )
                    ret = f" {fn.return_type}" if fn.return_type else ""
                    prefix = "async " if fn.is_async else ""
                    lines.append(f'        +{prefix}{fn.name}({param_str}){ret}')
                lines.append('    }')

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _render_class(self, cls: ClassInfo, config: DiagramConfig) -> list[str]:
        lines: list[str] = []

        # Stereotypes / annotations
        if cls.is_dataclass:
            lines.append(f'    class {cls.name} {{')
            lines.append(f'        <<dataclass>>')
        elif cls.is_abstract:
            lines.append(f'    class {cls.name} {{')
            lines.append(f'        <<abstract>>')
        else:
            lines.append(f'    class {cls.name} {{')

        # Fields — UML style: + type fieldName
        for fld in cls.fields:
            type_str = f" {fld.type_hint}" if fld.type_hint else ""
            lines.append(f'        +{type_str} {fld.name}')

        # Methods
        for method in cls.methods:
            if not config.include_dunder and method.name.startswith("__"):
                continue
            if not config.include_private and method.name.startswith("_") and not method.name.startswith("__"):
                continue
            param_str = ", ".join(
                f"{t} {n}" if t else n
                for n, t in method.params
            )
            ret = f" {method.return_type}" if method.return_type else ""
            prefix = "+" if not method.name.startswith("_") else "-"
            lines.append(f'        {prefix}{method.name}({param_str}){ret}')

        lines.append('    }')
        return lines

    def _render_relationship(self, rel: RelationshipInfo) -> str:
        label = f" : {rel.label}" if rel.label else ""
        if rel.kind == RelationshipKind.INHERITS:
            return f"    {rel.target} <|-- {rel.source}"
        elif rel.kind == RelationshipKind.COMPOSES:
            return f"    {rel.source} *-- {rel.target}{label}"
        else:  # USES
            return f"    {rel.source} --> {rel.target}{label}"


# ---------------------------------------------------------------------------
# DotRenderer
# ---------------------------------------------------------------------------


class DotRenderer(DiagramRenderer):
    """Renders a Graphviz DOT language class diagram.

    Output can be piped to ``dot -Tpng -o diagram.png``.
    The renderer itself requires no Graphviz installation.
    """

    def render(
        self,
        classes: list[ClassInfo],
        relationships: list[RelationshipInfo],
        config: DiagramConfig,
        *,
        functions: list[FunctionInfo] | None = None,
        imports: list[ImportInfo] | None = None,
    ) -> str:
        lines = [
            "digraph ClassDiagram {",
            "    rankdir=TB;",
            '    node [shape=record fontname=Helvetica fontsize=11];',
            '    edge [fontname=Helvetica fontsize=10];',
            "",
        ]

        for cls in classes:
            lines.append(self._render_node(cls, config))

        lines.append("")

        for rel in relationships:
            lines.append(self._render_edge(rel))

        if functions:
            lines.append("")
            lines.append('    subgraph cluster_functions {')
            lines.append('        label="Functions";')
            lines.append('        style=dashed;')
            modules: dict[str, list[FunctionInfo]] = {}
            for fn in functions:
                modules.setdefault(fn.module, []).append(fn)
            for module_name, module_funcs in modules.items():
                safe_name = module_name.replace(".", "_")
                func_lines = []
                for fn in module_funcs:
                    param_str = ", ".join(
                        f"{n}: {t}" if t else n
                        for n, t in fn.params
                    )
                    ret = f": {fn.return_type}" if fn.return_type else ""
                    prefix = "async " if fn.is_async else ""
                    func_lines.append(f"+ {prefix}{fn.name}({param_str}){ret}")
                label = r"\l".join(func_lines) + r"\l"
                lines.append(f'        "{safe_name}_funcs" [label="{label}" shape=box];')
            lines.append('    }')

        lines.append("}")
        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _render_node(self, cls: ClassInfo, config: DiagramConfig) -> str:
        # Fields section
        field_parts: list[str] = []
        for fld in cls.fields:
            type_str = f": {fld.type_hint}" if fld.type_hint else ""
            field_parts.append(f"- {fld.name}{type_str}")

        # Methods section
        method_parts: list[str] = []
        for method in cls.methods:
            if not config.include_dunder and method.name.startswith("__"):
                continue
            if not config.include_private and method.name.startswith("_") and not method.name.startswith("__"):
                continue
            param_str = ", ".join(
                f"{n}: {t}" if t else n
                for n, t in method.params
            )
            ret = f": {method.return_type}" if method.return_type else ""
            method_parts.append(f"+ {method.name}({param_str}){ret}")

        # Header label
        stereotype = ""
        if cls.is_dataclass:
            stereotype = r"«dataclass»\n"
        elif cls.is_abstract:
            stereotype = r"«abstract»\n"

        header = f"{stereotype}{cls.name}"
        fields_str = r"\l".join(field_parts) + (r"\l" if field_parts else "")
        methods_str = r"\l".join(method_parts) + (r"\l" if method_parts else "")

        # Build record label
        label_parts = [header]
        if field_parts:
            label_parts.append(fields_str)
        if method_parts:
            label_parts.append(methods_str)
        label = "|".join(label_parts)

        return f'    "{cls.name}" [label="{{{label}}}" tooltip="{cls.module}"];'

    def _render_edge(self, rel: RelationshipInfo) -> str:
        label_str = f' [label="{rel.label}"]' if rel.label else ""
        if rel.kind == RelationshipKind.INHERITS:
            return f'    "{rel.source}" -> "{rel.target}" [arrowhead=onormal style=solid];'
        elif rel.kind == RelationshipKind.COMPOSES:
            return f'    "{rel.source}" -> "{rel.target}" [arrowhead=diamond{label_str}];'
        else:  # USES
            return f'    "{rel.source}" -> "{rel.target}" [arrowhead=open style=dashed{label_str}];'


# ---------------------------------------------------------------------------
# PlantUMLRenderer
# ---------------------------------------------------------------------------


class PlantUMLRenderer(DiagramRenderer):
    """Renders a PlantUML class diagram.

    Output can be fed to ``plantuml diagram.puml`` or rendered online at
    https://www.plantuml.com/plantuml
    """

    def render(
        self,
        classes: list[ClassInfo],
        relationships: list[RelationshipInfo],
        config: DiagramConfig,
        *,
        functions: list[FunctionInfo] | None = None,
        imports: list[ImportInfo] | None = None,
    ) -> str:
        lines = ["@startuml", ""]

        for cls in classes:
            lines.extend(self._render_class(cls, config))
            lines.append("")

        for rel in relationships:
            lines.append(self._render_relationship(rel))

        if functions:
            lines.append("")
            modules: dict[str, list[FunctionInfo]] = {}
            for fn in functions:
                modules.setdefault(fn.module, []).append(fn)
            for module_name, module_funcs in modules.items():
                safe_name = module_name.replace(".", "_")
                lines.append(f'package "{module_name}" {{')
                for fn in module_funcs:
                    param_str = ", ".join(
                        f"{n}: {t}" if t else n
                        for n, t in fn.params
                    )
                    ret = f": {fn.return_type}" if fn.return_type else ""
                    prefix = "async " if fn.is_async else ""
                    lines.append(f'    +{prefix}{fn.name}({param_str}){ret}')
                lines.append('}')

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _render_class(self, cls: ClassInfo, config: DiagramConfig) -> list[str]:
        lines: list[str] = []

        keyword = "abstract class" if cls.is_abstract else "class"
        stereotype = ""
        if cls.is_dataclass:
            stereotype = " <<dataclass>>"
        elif cls.is_abstract:
            stereotype = " <<abstract>>"

        lines.append(f"{keyword} {cls.name}{stereotype} {{")

        for fld in cls.fields:
            type_str = f"{fld.type_hint} " if fld.type_hint else ""
            lines.append(f"    +{type_str}{fld.name}")

        lines.append("    --")

        for method in cls.methods:
            if not config.include_dunder and method.name.startswith("__"):
                continue
            if not config.include_private and method.name.startswith("_") and not method.name.startswith("__"):
                continue
            param_str = ", ".join(
                f"{n}: {t}" if t else n
                for n, t in method.params
            )
            ret = f": {method.return_type}" if method.return_type else ""
            prefix = "+" if not method.name.startswith("_") else "-"
            lines.append(f"    {prefix}{method.name}({param_str}){ret}")

        lines.append("}")
        return lines

    def _render_relationship(self, rel: RelationshipInfo) -> str:
        label = f" : {rel.label}" if rel.label else ""
        if rel.kind == RelationshipKind.INHERITS:
            return f"{rel.target} <|-- {rel.source}"
        elif rel.kind == RelationshipKind.COMPOSES:
            return f"{rel.source} *-- {rel.target}{label}"
        else:  # USES
            return f"{rel.source} --> {rel.target}{label}"


# ---------------------------------------------------------------------------
# TokenSerializer
# ---------------------------------------------------------------------------


class TokenSerializer(DiagramRenderer):
    """Produces a compact, LLM-optimised structural representation.

    Token-efficient format designed to convey maximum structural information
    in minimum tokens for use as context in LLM prompts.

    Example output::

        [MODULE] animals
          [CLASS] Animal [module=animals]
            FIELDS: name:str, age:int
            METHODS: speak()->str, move()->None
          [CLASS] Dog(Animal) [module=animals]
            FIELDS: breed:str
            METHODS: fetch(item:str)->bool
        [RELATIONSHIPS]
          Dog --inherits--> Animal
          Shelter --composes--> Animal (animals)
    """

    def render(
        self,
        classes: list[ClassInfo],
        relationships: list[RelationshipInfo],
        config: DiagramConfig,
        *,
        functions: list[FunctionInfo] | None = None,
        imports: list[ImportInfo] | None = None,
    ) -> str:
        lines: list[str] = []

        # Group imports by module
        import_modules: dict[str, list[ImportInfo]] = {}
        if imports:
            for imp in imports:
                import_modules.setdefault(imp.module, []).append(imp)

        # Group classes by module
        modules: dict[str, list[ClassInfo]] = {}
        for cls in classes:
            modules.setdefault(cls.module, []).append(cls)

        # Group functions by module
        func_modules: dict[str, list[FunctionInfo]] = {}
        if functions:
            for fn in functions:
                func_modules.setdefault(fn.module, []).append(fn)

        # Collect all modules in order
        all_modules = list(dict.fromkeys(list(modules.keys()) + list(func_modules.keys()) + list(import_modules.keys())))

        # Detect duplicate class names for disambiguation
        name_counts: dict[str, int] = {}
        for cls in classes:
            name_counts[cls.name] = name_counts.get(cls.name, 0) + 1
        duplicate_names = {name for name, count in name_counts.items() if count > 1}

        for module_name in all_modules:
            lines.append(f"[MODULE] {module_name}")
            module_imports = import_modules.get(module_name, [])
            if module_imports:
                for imp in module_imports:
                    lines.append(f"  [IMPORT] {imp.source}")
            for cls in modules.get(module_name, []):
                repr_text = cls.token_repr(include_dunder=config.include_dunder)
                if cls.name in duplicate_names:
                    # Disambiguate by replacing [CLASS] Name with [CLASS] module.Name
                    qualified = f"{cls.module}.{cls.name}"
                    repr_text = repr_text.replace(f"[CLASS] {cls.name}", f"[CLASS] {qualified}", 1)
                lines.append(
                    repr_text
                    .replace("\n", "\n  ")  # indent under [MODULE]
                )
            module_funcs = func_modules.get(module_name, [])
            if module_funcs:
                lines.append("  [FUNCTIONS]")
                for fn in module_funcs:
                    param_str = ", ".join(
                        f"{n}:{t}" if t else n
                        for n, t in fn.params
                    )
                    ret = f"->{fn.return_type}" if fn.return_type else ""
                    async_tag = "async " if fn.is_async else ""
                    lineno = f" [line {fn.lineno}]" if fn.lineno else ""
                    lines.append(f"    {async_tag}{fn.name}({param_str}){ret}{lineno}")
            lines.append("")

        if relationships:
            lines.append("[RELATIONSHIPS]")
            for rel in relationships:
                label = f" ({rel.label})" if rel.label else ""
                lines.append(f"  {rel.source} --{rel.kind.value}--> {rel.target}{label}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# ErdanticAdapter
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# PyDiagramFacade
# ---------------------------------------------------------------------------

_RENDERERS: dict[DiagramFormat, type[DiagramRenderer]] = {
    DiagramFormat.MERMAID: MermaidRenderer,
    DiagramFormat.DOT: DotRenderer,
    DiagramFormat.PLANTUML: PlantUMLRenderer,
    DiagramFormat.TOKEN: TokenSerializer,
}


class PyDiagramFacade:
    """High-level façade orchestrating the full extract → relate → render pipeline.

    Usage::

        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)

        # From a directory:
        result = facade.analyse_directory(Path("src/mypackage"))

        # From a single source string:
        result = facade.analyse_source(source_code, module_name="mymod")

        facade.write(result)   # writes to file or stdout
    """

    def __init__(
        self,
        config: DiagramConfig,
        *,
        extractor: ASTClassExtractor | None = None,
        engine: RelationshipEngine | None = None,
    ) -> None:
        self._config = config
        self._extractor = extractor or ASTClassExtractor()
        self._engine = engine or RelationshipEngine()
        self._renderer: DiagramRenderer = _RENDERERS[config.output_format]()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse_source(self, source: str, *, module_name: str = "") -> DiagramResult:
        """Extract, relate, and render from a raw source string."""
        classes = self._extractor.extract_from_source(
            source,
            module_name=module_name,
            include_private=self._config.include_private,
            include_dunder=self._config.include_dunder,
        )
        functions = self._extractor.extract_functions_from_source(
            source, module_name=module_name,
        )
        imports = self._extractor.extract_imports_from_source(
            source, module_name=module_name,
        )
        return self._build_result(classes, functions=functions, imports=imports)

    def analyse_directory(self, root: Path) -> DiagramResult:
        """Extract, relate, and render from all .py files under *root*."""
        classes = self._extractor.extract_from_directory(
            root,
            skip_dirs=self._config.skip_dirs,
            include_private=self._config.include_private,
            include_dunder=self._config.include_dunder,
        )
        functions = self._extractor.extract_functions_from_directory(
            root, skip_dirs=self._config.skip_dirs,
        )
        imports = self._extractor.extract_imports_from_directory(
            root, skip_dirs=self._config.skip_dirs,
        )
        return self._build_result(classes, functions=functions, imports=imports)

    def analyse_file(self, path: Path) -> DiagramResult:
        """Extract, relate, and render from a single .py file."""
        classes = self._extractor.extract_from_file(
            path,
            include_private=self._config.include_private,
            include_dunder=self._config.include_dunder,
        )
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            source = ""
        module_name = path.stem
        functions = self._extractor.extract_functions_from_source(
            source, module_name=module_name,
        )
        imports = self._extractor.extract_imports_from_source(
            source, module_name=module_name,
        )
        return self._build_result(classes, functions=functions, imports=imports)

    def write(self, result: DiagramResult) -> None:
        """Write *result.diagram* to the configured output path, or stdout."""
        if self._config.output_path:
            self._config.output_path.parent.mkdir(parents=True, exist_ok=True)
            self._config.output_path.write_text(result.diagram, encoding="utf-8")
            print(f"[py-diagram] Written → {self._config.output_path}", file=sys.stderr)
        else:
            print(result.diagram)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_result(self, classes: list[ClassInfo], *, functions: list[FunctionInfo] | None = None, imports: list[ImportInfo] | None = None) -> DiagramResult:
        # Apply max_classes limit (take first N by occurrence order)
        if self._config.max_classes is not None:
            classes = classes[: self._config.max_classes]

        functions = functions or []
        imports = imports or []
        relationships = self._engine.extract(classes)
        diagram = self._renderer.render(classes, relationships, self._config, functions=functions, imports=imports)
        return DiagramResult(
            diagram=diagram,
            classes=classes,
            relationships=relationships,
            functions=functions,
            imports=imports,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="py-diagram",
        description=(
            "Generate token-efficient class/type diagrams from Python source.\n\n"
            "Supports Mermaid, Graphviz DOT, PlantUML, and LLM token formats."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py-diagram src/mypackage
  py-diagram src/ --format dot --output docs/classes.dot
  py-diagram --source mymodule.py --format plantuml
  py-diagram src/ --format token --max-classes 40 --skip tests migrations
  py-diagram src/ --format mermaid --include-private --include-dunder
        """,
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Project root to scan (default: current directory)",
    )
    parser.add_argument(
        "--source", "-s",
        default=None,
        metavar="FILE",
        help="Analyse a single .py file instead of scanning root",
    )
    parser.add_argument(
        "--format", "-f",
        default="mermaid",
        choices=[f.value for f in DiagramFormat],
        help="Output diagram format (default: mermaid)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help="Write diagram to FILE (default: stdout)",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=[],
        metavar="DIR",
        help="Additional directory names to skip",
    )
    parser.add_argument(
        "--max-classes",
        type=int,
        default=None,
        metavar="N",
        help="Limit diagram to first N classes",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include single-underscore private members",
    )
    parser.add_argument(
        "--include-dunder",
        action="store_true",
        help="Include double-underscore dunder members",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    cfg = DiagramConfig(
        output_format=DiagramFormat(args.format),
        output_path=Path(args.output) if args.output else None,
        include_private=args.include_private,
        include_dunder=args.include_dunder,
        max_classes=args.max_classes,
        skip_dirs=args.skip or [],
    )

    facade = PyDiagramFacade(cfg)

    if args.source:
        source_path = Path(args.source)
        if not source_path.exists():
            print(f"Error: '{source_path}' not found.", file=sys.stderr)
            sys.exit(1)
        result = facade.analyse_file(source_path)
    else:
        root = Path(args.root).resolve()
        if not root.exists():
            print(f"Error: '{root}' not found.", file=sys.stderr)
            sys.exit(1)
        result = facade.analyse_directory(root)

    facade.write(result)

    # Summary to stderr so it doesn't pollute stdout redirects
    print(
        f"[py-diagram] {result.class_count} classes, "
        f"{result.relationship_count} relationships — format: {cfg.output_format.value}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
