"""
scanner.py — Walk a Svelte/SvelteKit project directory and build a ProjectMap.

Respects:
  - .gitignore patterns (via pathspec when available)
  - Hard-coded skip dirs: node_modules, .svelte-kit, .git, dist, build, .venv
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from svelte_mapper.extractor import SvelteExtractor, TSExtractor
from svelte_mapper.models import (
    ProjectMap, ComponentMap, StoreMap, TypeInfo, FileKind,
)

try:
    from pathspec import PathSpec
    from pathspec.patterns import GitWildMatchPattern
    _HAS_PATHSPEC = True
except ImportError:
    _HAS_PATHSPEC = False

_SKIP_DIRS = {
    "node_modules", ".svelte-kit", ".git", ".venv", "venv",
    "dist", "build", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".next", ".nuxt",
}


# ---------------------------------------------------------------------------
# .gitignore helper
# ---------------------------------------------------------------------------

def _load_gitignore(root: Path) -> Optional["PathSpec"]:
    if not _HAS_PATHSPEC:
        return None
    gi = root / ".gitignore"
    if not gi.exists():
        return None
    lines = gi.read_text(encoding="utf-8").splitlines()
    return PathSpec.from_lines(GitWildMatchPattern, lines)


def _is_ignored(rel: str, gi: Optional["PathSpec"]) -> bool:
    if gi is None:
        return False
    return gi.match_file(rel)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class Scanner:
    """Walk a project root and produce a ProjectMap."""

    @classmethod
    def scan(cls, root: Path) -> ProjectMap:
        root = Path(root).resolve()
        gi = _load_gitignore(root)

        components: list[ComponentMap] = []
        stores: list[StoreMap] = []
        all_types: list[TypeInfo] = []
        routes: list[str] = []

        for dirpath, dirnames, filenames in os.walk(root):
            cur = Path(dirpath)

            # Prune skip dirs in-place
            dirnames[:] = sorted(
                d for d in dirnames
                if d not in _SKIP_DIRS and not d.startswith(".")
            )

            for fname in sorted(filenames):
                abs_f = cur / fname
                try:
                    rel = str(abs_f.relative_to(root))
                except ValueError:
                    rel = str(abs_f)

                if _is_ignored(rel, gi):
                    continue

                suffix = abs_f.suffix.lower()

                if suffix == ".svelte":
                    source = _safe_read(abs_f)
                    if source is None:
                        continue
                    comp = SvelteExtractor.parse(rel, source)
                    components.append(comp)
                    if comp.kind in (FileKind.ROUTE, FileKind.LAYOUT):
                        routes.append(rel)

                elif suffix == ".ts":
                    source = _safe_read(abs_f)
                    if source is None:
                        continue
                    kind = TSExtractor.classify_file(fname)

                    if kind == FileKind.STORE:
                        sm = TSExtractor.parse_store(rel, source)
                        stores.append(sm)

                    elif kind == FileKind.TYPES:
                        types = TSExtractor.parse_types(rel, source)
                        all_types.extend(types)

                    elif kind == FileKind.SERVER:
                        # Surface as a route entry
                        routes.append(rel)

                    # UTIL / ROUTE .ts files are currently skipped for
                    # deep parsing but could be added later.

        # ── Enrich store readers/writers from component store_refs ───
        stores = _enrich_stores(stores, components)

        return ProjectMap(
            root=str(root),
            components=components,
            stores=stores,
            types=all_types,
            routes=sorted(routes),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _enrich_stores(
    stores: list[StoreMap],
    components: list[ComponentMap],
) -> list[StoreMap]:
    """Populate readers/writers on each StoreMap from component StoreRefs."""
    readers: dict[str, list[str]] = {s.name: [] for s in stores}
    writers: dict[str, list[str]] = {s.name: [] for s in stores}

    for comp in components:
        for ref in comp.store_refs:
            if ref.store_name in readers:
                if ref.access == "read":
                    readers[ref.store_name].append(comp.name)
                else:
                    writers[ref.store_name].append(comp.name)

    enriched: list[StoreMap] = []
    for s in stores:
        enriched.append(StoreMap(
            name=s.name,
            file=s.file,
            kind=s.kind,
            line_count=s.line_count,
            readers=sorted(set(readers[s.name])),
            writers=sorted(set(writers[s.name])),
        ))
    return enriched
