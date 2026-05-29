"""
graph.py — Build and query the import/dependency graph of a Svelte project.

Uses networkx DiGraph under the hood.  Every node is identified by its
human-readable name (component stem or store name).  Edges represent
"A imports / uses B".
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import networkx as nx

from svelte_mapper.models import ProjectMap, FileKind


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HotspotInfo:
    name: str
    importer_count: int


@dataclass(frozen=True)
class UnusedInfo:
    name: str
    file: str


# ---------------------------------------------------------------------------
# Route / layout node detection helper
# ---------------------------------------------------------------------------

_ROUTE_KINDS = {FileKind.ROUTE, FileKind.LAYOUT}


def _is_route_node(name: str) -> bool:
    """Heuristic: SvelteKit route files start with '+' ."""
    return name.startswith("+")


# ---------------------------------------------------------------------------
# ImportGraph
# ---------------------------------------------------------------------------

class ImportGraph:
    """
    Directed graph: edge A → B means "A depends on B".
    Nodes are component/store names (strings).
    """

    def __init__(self, g: nx.DiGraph, _meta: dict[str, dict]) -> None:
        self._g = g
        self._meta = _meta  # name → {file, kind}

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def build(cls, project: ProjectMap) -> "ImportGraph":
        g = nx.DiGraph()
        meta: dict[str, dict] = {}

        # ── Register component nodes ──────────────────────────────────
        for comp in project.components:
            g.add_node(comp.name)
            meta[comp.name] = {"file": comp.file, "kind": comp.kind}

        # ── Register store nodes ──────────────────────────────────────
        for store in project.stores:
            g.add_node(store.name)
            meta[store.name] = {"file": store.file, "kind": FileKind.STORE}

        # ── Add edges from component imports ─────────────────────────
        comp_by_stem: dict[str, str] = {c.name: c.name for c in project.components}
        store_by_name: dict[str, str] = {s.name: s.name for s in project.stores}

        for comp in project.components:
            for imp in comp.imports:
                if imp.is_svelte_runtime:
                    continue
                # Resolve imported names to known nodes
                for name in imp.names:
                    target = _resolve(name, imp.source, comp_by_stem, store_by_name)
                    if target:
                        g.add_node(target)   # may be unresolved external
                        g.add_edge(comp.name, target)

            # ── Add store ref edges ────────────────────────────────────
            for ref in comp.store_refs:
                if ref.store_name in store_by_name:
                    g.add_node(ref.store_name)
                    g.add_edge(comp.name, ref.store_name)

        return cls(g, meta)

    # ------------------------------------------------------------------
    # Node / edge inspection
    # ------------------------------------------------------------------

    @property
    def nodes(self) -> set[str]:
        return set(self._g.nodes)

    def has_edge(self, src: str, dst: str) -> bool:
        return self._g.has_edge(src, dst)

    # ------------------------------------------------------------------
    # Dependency queries
    # ------------------------------------------------------------------

    def direct_deps(self, name: str) -> set[str]:
        """Return the set of nodes that *name* directly imports."""
        if name not in self._g:
            return set()
        return set(self._g.successors(name))

    def importers_of(self, name: str) -> set[str]:
        """Return the set of nodes that directly import *name*."""
        if name not in self._g:
            return set()
        return set(self._g.predecessors(name))

    # ------------------------------------------------------------------
    # Store consumer map
    # ------------------------------------------------------------------

    def store_consumers(self, store_name: str) -> set[str]:
        """Return all component names that import or reference *store_name*."""
        return self.importers_of(store_name)

    # ------------------------------------------------------------------
    # Hotspot / dead code analysis
    # ------------------------------------------------------------------

    def hotspots(self, top_n: int = 5) -> list[HotspotInfo]:
        """Return the top-N nodes by incoming-edge count (most imported)."""
        ranked = sorted(
            self._g.nodes,
            key=lambda n: self._g.in_degree(n),
            reverse=True,
        )
        return [
            HotspotInfo(name=n, importer_count=self._g.in_degree(n))
            for n in ranked[:top_n]
            if self._g.in_degree(n) > 0
        ]

    def unused_components(self) -> list[UnusedInfo]:
        """
        Return component nodes with 0 importers that are NOT routes/layouts.
        Nodes not found in _meta are skipped (external/unresolved).
        """
        unused: list[UnusedInfo] = []
        for node in self._g.nodes:
            if _is_route_node(node):
                continue
            if self._g.in_degree(node) > 0:
                continue
            meta = self._meta.get(node)
            if meta is None:
                continue
            if meta.get("kind") in _ROUTE_KINDS:
                continue
            unused.append(UnusedInfo(name=node, file=meta["file"]))
        return unused

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_adjacency_dict(self) -> dict[str, list[str]]:
        """Return adjacency list as a plain dict for rendering."""
        return {node: sorted(self._g.successors(node)) for node in sorted(self._g.nodes)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve(
    imported_name: str,
    source_path: str,
    comp_by_stem: dict[str, str],
    store_by_name: dict[str, str],
) -> Optional[str]:
    """
    Try to map an imported identifier to a known node name.
    Strategy:
      1. Direct match in known component stems.
      2. Direct match in known store names.
      3. Derive from source path stem.
    """
    # Direct name match
    if imported_name in comp_by_stem:
        return imported_name
    if imported_name in store_by_name:
        return imported_name

    # Source path stem (e.g. './Pagination.svelte' → 'Pagination')
    stem = Path(source_path).stem
    if stem in comp_by_stem:
        return stem
    if stem in store_by_name:
        return stem

    # Return the imported name verbatim so external deps are still visible
    return imported_name if imported_name.isidentifier() else None
