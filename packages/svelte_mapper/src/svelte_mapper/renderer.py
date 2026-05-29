"""
renderer.py — Produce the "golden map" for LLM agent consumption.

Three output modes:
  render()          → single string (all layers concatenated with headers)
  render_to_dict()  → dict keyed by layer name (for JSON/API usage)
  render_*(…)       → individual layer strings (for selective rendering)

Output is YAML-structured where parseable, plain text for the file tree
and import graph.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

from svelte_mapper.models import ProjectMap
from svelte_mapper.graph import ImportGraph


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class OutputLayer(str, Enum):
    FILE_TREE = "file_tree"
    IMPORT_GRAPH = "import_graph"
    COMPONENT_SIGNATURES = "component_signatures"
    STORE_TOPOLOGY = "store_topology"


_ALL_LAYERS = [
    OutputLayer.FILE_TREE,
    OutputLayer.IMPORT_GRAPH,
    OutputLayer.COMPONENT_SIGNATURES,
    OutputLayer.STORE_TOPOLOGY,
]


class RendererConfig:
    def __init__(
        self,
        layers: Optional[list[OutputLayer]] = None,
        max_tokens: int = 4096,
    ) -> None:
        self.layers: list[OutputLayer] = layers if layers is not None else list(_ALL_LAYERS)
        self.max_tokens: int = max_tokens


# ---------------------------------------------------------------------------
# MapRenderer
# ---------------------------------------------------------------------------

class MapRenderer:
    def __init__(
        self,
        project: ProjectMap,
        graph: ImportGraph,
        config: Optional[RendererConfig] = None,
    ) -> None:
        self.project = project
        self.graph = graph
        self.config = config or RendererConfig()

    # ------------------------------------------------------------------
    # Layer 1: File tree
    # ------------------------------------------------------------------

    def render_file_tree(self) -> str:
        """Annotated directory listing with file counts."""
        lines: list[str] = [f"root: {self.project.root}"]

        # Group by directory
        by_dir: dict[str, list[str]] = {}
        all_files = (
            [(c.file, f"{c.name}.svelte ({c.line_count} lines)") for c in self.project.components]
            + [(s.file, f"{s.name}.ts  ({s.line_count} lines) [store]") for s in self.project.stores]
            + [(t.file, f"{Path(t.file).name}  [{t.kind}: {t.name}]") for t in self.project.types]
        )
        for file_path, label in all_files:
            directory = str(Path(file_path).parent)
            by_dir.setdefault(directory, []).append(label)

        for directory in sorted(by_dir):
            lines.append(f"\n  {directory}/")
            for label in sorted(by_dir[directory]):
                lines.append(f"    {label}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Layer 2: Import graph
    # ------------------------------------------------------------------

    def render_import_graph(self) -> str:
        """Compact adjacency list: 'Node → dep1, dep2'."""
        adj = self.graph.to_adjacency_dict()
        lines: list[str] = []
        for node in sorted(adj):
            deps = adj[node]
            if deps:
                lines.append(f"  {node} → {', '.join(deps)}")
            else:
                lines.append(f"  {node}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Layer 3: Component signatures
    # ------------------------------------------------------------------

    def render_component_signatures(self) -> str:
        """YAML block: per-component props / events / slots / features."""
        data: dict = {}
        for comp in self.project.components:
            entry: dict = {}

            if comp.props:
                entry["props"] = [
                    {
                        "name": p.name,
                        **({"type": p.type} if p.type else {}),
                        **({"default": p.default} if p.default is not None else {}),
                        "required": p.required,
                    }
                    for p in comp.props
                ]

            if comp.events:
                entry["events"] = [
                    e.name if e.payload is None else {e.name: e.payload}
                    for e in comp.events
                ]

            if comp.slots:
                entry["slots"] = [s.name for s in comp.slots]

            if comp.svelte_features:
                entry["features"] = comp.svelte_features

            if comp.store_refs:
                reads = sorted({r.store_name for r in comp.store_refs if r.access == "read"})
                writes = sorted({r.store_name for r in comp.store_refs if r.access == "write"})
                stores_entry: dict = {}
                if reads:
                    stores_entry["reads"] = reads
                if writes:
                    stores_entry["writes"] = writes
                if stores_entry:
                    entry["stores"] = stores_entry

            entry["file"] = comp.file
            entry["lines"] = comp.line_count
            data[comp.name] = entry

        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # ------------------------------------------------------------------
    # Layer 4: Store topology
    # ------------------------------------------------------------------

    def render_store_topology(self) -> str:
        """YAML block: store names, kinds, readers, writers."""
        data: dict = {}
        for store in self.project.stores:
            entry: dict = {"kind": store.kind, "file": store.file}
            if store.readers:
                entry["readers"] = store.readers
            if store.writers:
                entry["writers"] = store.writers
            # Augment with graph data
            graph_consumers = sorted(self.graph.store_consumers(store.name))
            if graph_consumers and not store.readers:
                entry["readers"] = graph_consumers
            data[store.name] = entry
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # ------------------------------------------------------------------
    # Full render
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Render all configured layers into one string with section headers."""
        sections: list[str] = []

        layer_renderers = {
            OutputLayer.FILE_TREE: ("═══ FILE TREE ═══", self.render_file_tree),
            OutputLayer.IMPORT_GRAPH: ("═══ IMPORT GRAPH ═══", self.render_import_graph),
            OutputLayer.COMPONENT_SIGNATURES: ("═══ COMPONENT SIGNATURES ═══", self.render_component_signatures),
            OutputLayer.STORE_TOPOLOGY: ("═══ STORE TOPOLOGY ═══", self.render_store_topology),
        }

        for layer in self.config.layers:
            header, fn = layer_renderers[layer]
            sections.append(f"\n{header}\n{fn()}")

        # Append hotspot summary
        if self.project.stores or self.project.components:
            hotspots = self.graph.hotspots(top_n=5)
            if hotspots:
                hs_lines = ["═══ HOTSPOTS (most imported) ═══"]
                for h in hotspots:
                    hs_lines.append(f"  {h.name}  ({h.importer_count} importers)")
                sections.append("\n" + "\n".join(hs_lines))

        return "\n".join(sections)

    def render_to_dict(self) -> dict:
        """Return each layer as a dict value for structured consumption."""
        result: dict = {}

        if OutputLayer.FILE_TREE in self.config.layers:
            result["file_tree"] = self.render_file_tree()
        if OutputLayer.IMPORT_GRAPH in self.config.layers:
            result["import_graph"] = self.render_import_graph()
        if OutputLayer.COMPONENT_SIGNATURES in self.config.layers:
            result["components"] = self.render_component_signatures()
        if OutputLayer.STORE_TOPOLOGY in self.config.layers:
            result["stores"] = self.render_store_topology()

        return result
