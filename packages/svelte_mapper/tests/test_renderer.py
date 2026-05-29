"""
TDD – Layer 3: Golden map renderer.
Tests verify YAML and text output shape, token budgets, and layer isolation.
"""
import pytest
import yaml

from svelte_mapper.models import (
    ProjectMap, ComponentMap, StoreMap, TypeInfo,
    PropInfo, EventInfo, SlotInfo, ImportInfo, StoreRef,
)
from svelte_mapper.graph import ImportGraph
from svelte_mapper.renderer import MapRenderer, RendererConfig, OutputLayer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_project() -> ProjectMap:
    return ProjectMap(
        root="/fake/app",
        components=[
            ComponentMap(
                name="Button",
                file="src/lib/components/Button.svelte",
                line_count=30,
                props=[
                    PropInfo(name="label", type="string", default="'Click me'"),
                    PropInfo(name="disabled", type="boolean", default="false"),
                ],
                events=[EventInfo(name="click")],
                slots=[SlotInfo(name="icon"), SlotInfo(name="default")],
                imports=[ImportInfo(source="./Spinner.svelte", names=["Spinner"])],
                store_refs=[],
                svelte_features=[],
            ),
            ComponentMap(
                name="DataTable",
                file="src/lib/components/DataTable.svelte",
                line_count=55,
                props=[
                    PropInfo(name="items", type="Item[]", default="[]"),
                    PropInfo(name="pageSize", type="number", default="10"),
                ],
                events=[EventInfo(name="rowClick"), EventInfo(name="pageChange")],
                slots=[SlotInfo(name="row"), SlotInfo(name="header")],
                imports=[
                    ImportInfo(source="./Pagination.svelte", names=["Pagination"]),
                    ImportInfo(source="$lib/stores/tableStore", names=["tableStore"]),
                ],
                store_refs=[
                    StoreRef(store_name="tableStore", access="read"),
                    StoreRef(store_name="tableStore", access="write"),
                ],
                svelte_features=["onMount", "onDestroy", "{#each}"],
            ),
        ],
        stores=[
            StoreMap(
                name="tableStore",
                file="src/lib/stores/tableStore.ts",
                kind="writable",
                line_count=12,
                readers=["DataTable"],
                writers=["DataTable"],
            ),
            StoreMap(
                name="authStore",
                file="src/lib/stores/authStore.ts",
                kind="writable",
                line_count=20,
                readers=["+layout", "+page"],
                writers=[],
            ),
        ],
        types=[
            TypeInfo(name="User", kind="interface", file="src/lib/types.ts"),
            TypeInfo(name="ButtonVariant", kind="type", file="src/lib/types.ts"),
            TypeInfo(name="Theme", kind="enum", file="src/lib/types.ts"),
        ],
        routes=["src/routes/+page.svelte", "src/routes/+layout.svelte"],
    )


@pytest.fixture
def graph(full_project) -> ImportGraph:
    return ImportGraph.build(full_project)


@pytest.fixture
def renderer(full_project, graph) -> MapRenderer:
    return MapRenderer(project=full_project, graph=graph)


# ---------------------------------------------------------------------------
# RendererConfig
# ---------------------------------------------------------------------------

class TestRendererConfig:
    def test_defaults(self):
        cfg = RendererConfig()
        assert OutputLayer.FILE_TREE in cfg.layers
        assert OutputLayer.IMPORT_GRAPH in cfg.layers
        assert OutputLayer.COMPONENT_SIGNATURES in cfg.layers
        assert OutputLayer.STORE_TOPOLOGY in cfg.layers

    def test_custom_layers(self):
        cfg = RendererConfig(layers=[OutputLayer.FILE_TREE])
        assert len(cfg.layers) == 1

    def test_max_tokens_default_is_positive(self):
        cfg = RendererConfig()
        assert cfg.max_tokens > 0


# ---------------------------------------------------------------------------
# Layer 1: File tree
# ---------------------------------------------------------------------------

class TestFileTreeLayer:
    def test_file_tree_contains_component_files(self, renderer):
        output = renderer.render_file_tree()
        assert "Button.svelte" in output
        assert "DataTable.svelte" in output

    def test_file_tree_contains_store_files(self, renderer):
        output = renderer.render_file_tree()
        assert "tableStore.ts" in output

    def test_file_tree_contains_type_files(self, renderer):
        output = renderer.render_file_tree()
        assert "types.ts" in output

    def test_file_tree_shows_line_counts(self, renderer):
        output = renderer.render_file_tree()
        # e.g. "30 lines" or "(30)"
        assert "30" in output or "55" in output

    def test_file_tree_is_compact(self, renderer):
        output = renderer.render_file_tree()
        lines = [l for l in output.splitlines() if l.strip()]
        # Should be far fewer lines than actual file contents
        assert len(lines) < 30


# ---------------------------------------------------------------------------
# Layer 2: Import graph
# ---------------------------------------------------------------------------

class TestImportGraphLayer:
    def test_graph_output_shows_edges(self, renderer):
        output = renderer.render_import_graph()
        assert "DataTable" in output
        assert "tableStore" in output

    def test_button_to_spinner_edge_present(self, renderer):
        output = renderer.render_import_graph()
        assert "Button" in output
        assert "Spinner" in output

    def test_graph_is_adjacency_style(self, renderer):
        output = renderer.render_import_graph()
        # Expect "→" or "->" or ":" separating node from its deps
        assert ("→" in output) or ("->" in output) or (":" in output)

    def test_graph_output_is_compact(self, renderer):
        output = renderer.render_import_graph()
        lines = [l for l in output.splitlines() if l.strip()]
        assert len(lines) < 20


# ---------------------------------------------------------------------------
# Layer 3: Component signatures
# ---------------------------------------------------------------------------

class TestComponentSignaturesLayer:
    def test_button_signature_present(self, renderer):
        output = renderer.render_component_signatures()
        assert "Button" in output

    def test_props_section_present(self, renderer):
        output = renderer.render_component_signatures()
        assert "label" in output
        assert "disabled" in output

    def test_events_section_present(self, renderer):
        output = renderer.render_component_signatures()
        assert "click" in output
        assert "rowClick" in output

    def test_slots_section_present(self, renderer):
        output = renderer.render_component_signatures()
        assert "icon" in output
        assert "row" in output

    def test_svelte_features_present(self, renderer):
        output = renderer.render_component_signatures()
        assert "onMount" in output

    def test_output_is_valid_yaml(self, renderer):
        output = renderer.render_component_signatures()
        parsed = yaml.safe_load(output)
        assert parsed is not None

    def test_yaml_has_component_names_as_keys(self, renderer):
        output = renderer.render_component_signatures()
        parsed = yaml.safe_load(output)
        assert "Button" in parsed
        assert "DataTable" in parsed


# ---------------------------------------------------------------------------
# Layer 4: Store topology
# ---------------------------------------------------------------------------

class TestStoreTopologyLayer:
    def test_store_names_present(self, renderer):
        output = renderer.render_store_topology()
        assert "tableStore" in output
        assert "authStore" in output

    def test_store_kind_shown(self, renderer):
        output = renderer.render_store_topology()
        assert "writable" in output

    def test_readers_shown(self, renderer):
        output = renderer.render_store_topology()
        assert "DataTable" in output

    def test_output_is_valid_yaml(self, renderer):
        output = renderer.render_store_topology()
        parsed = yaml.safe_load(output)
        assert parsed is not None


# ---------------------------------------------------------------------------
# Full golden map (all layers combined)
# ---------------------------------------------------------------------------

class TestFullGoldenMap:
    def test_render_all_layers(self, renderer):
        output = renderer.render()
        assert "Button" in output
        assert "tableStore" in output
        assert "writable" in output

    def test_each_layer_has_header(self, renderer):
        output = renderer.render()
        assert "FILE TREE" in output.upper() or "file_tree" in output.lower()
        assert "IMPORT" in output.upper()
        assert "COMPONENT" in output.upper() or "signature" in output.lower()
        assert "STORE" in output.upper()

    def test_selective_layers(self, full_project, graph):
        renderer = MapRenderer(
            project=full_project,
            graph=graph,
            config=RendererConfig(layers=[OutputLayer.STORE_TOPOLOGY]),
        )
        output = renderer.render()
        assert "tableStore" in output
        # Component signatures should NOT appear
        assert "props:" not in output

    def test_render_to_dict(self, renderer):
        result = renderer.render_to_dict()
        assert isinstance(result, dict)
        assert "file_tree" in result or "components" in result or "stores" in result

    def test_hotspots_section_present(self, renderer):
        output = renderer.render()
        # Hotspots / high-impact nodes should surface somewhere
        assert "authStore" in output or "tableStore" in output

    def test_total_line_count_compact(self, renderer):
        """Golden map should be dramatically shorter than raw source."""
        output = renderer.render()
        total_source_lines = sum(c.line_count for c in renderer.project.components)
        map_lines = len([l for l in output.splitlines() if l.strip()])
        assert map_lines < total_source_lines


# ---------------------------------------------------------------------------
# Scanner integration (filesystem → ProjectMap)
# ---------------------------------------------------------------------------

class TestScanner:
    """Test the filesystem scanner that builds a ProjectMap from a real directory."""

    def test_scanner_finds_svelte_files(self, svelte_project):
        from svelte_mapper.scanner import Scanner
        pm = Scanner.scan(svelte_project)
        names = [c.name for c in pm.components]
        assert "Button" in names
        assert "DataTable" in names

    def test_scanner_finds_stores(self, svelte_project):
        from svelte_mapper.scanner import Scanner
        pm = Scanner.scan(svelte_project)
        store_names = [s.name for s in pm.stores]
        assert "tableStore" in store_names
        assert "authStore" in store_names

    def test_scanner_finds_types(self, svelte_project):
        from svelte_mapper.scanner import Scanner
        pm = Scanner.scan(svelte_project)
        type_names = [t.name for t in pm.types]
        assert "User" in type_names

    def test_scanner_identifies_routes(self, svelte_project):
        from svelte_mapper.scanner import Scanner
        pm = Scanner.scan(svelte_project)
        # Routes list should contain SvelteKit route files
        assert any("+page" in r for r in pm.routes)
        assert any("+layout" in r for r in pm.routes)

    def test_scanner_sets_root(self, svelte_project):
        from svelte_mapper.scanner import Scanner
        pm = Scanner.scan(svelte_project)
        assert str(svelte_project) in pm.root
