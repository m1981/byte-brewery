"""
TDD – Layer 2: Import graph builder.
Tests verify that the graph correctly represents component dependencies,
store consumers, and can answer structural queries.
"""
import pytest

from svelte_mapper.graph import ImportGraph
from svelte_mapper.models import ProjectMap, ComponentMap, StoreMap, ImportInfo, StoreRef, PropInfo, EventInfo, SlotInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def small_project() -> ProjectMap:
    """
    ProjectMap mirroring the virtual project in conftest.svelte_project:
      Button  ← imports Spinner
      DataTable ← imports Pagination, SortIcon, tableStore
      Layout  ← imports Header, Sidebar, authStore, themeStore
      +page   ← imports DataTable, authStore
    """
    return ProjectMap(
        root="/fake/root",
        components=[
            ComponentMap(
                name="Button",
                file="src/lib/components/Button.svelte",
                line_count=30,
                imports=[
                    ImportInfo(source="./Spinner.svelte", names=["Spinner"]),
                    ImportInfo(source="$lib/types", names=["ButtonVariant"], type_only=True),
                ],
                store_refs=[],
            ),
            ComponentMap(
                name="Spinner",
                file="src/lib/components/Spinner.svelte",
                line_count=10,
                imports=[
                    ImportInfo(source="svelte/store", names=["writable"]),
                ],
                store_refs=[],
            ),
            ComponentMap(
                name="DataTable",
                file="src/lib/components/DataTable.svelte",
                line_count=55,
                imports=[
                    ImportInfo(source="./Pagination.svelte", names=["Pagination"]),
                    ImportInfo(source="./SortIcon.svelte", names=["SortIcon"]),
                    ImportInfo(source="$lib/stores/tableStore", names=["tableStore"]),
                    ImportInfo(source="svelte", names=["onMount", "onDestroy"]),
                ],
                store_refs=[
                    StoreRef(store_name="tableStore", access="read"),
                    StoreRef(store_name="tableStore", access="write"),
                ],
            ),
            ComponentMap(
                name="+layout",
                file="src/routes/+layout.svelte",
                line_count=22,
                imports=[
                    ImportInfo(source="./Header.svelte", names=["Header"]),
                    ImportInfo(source="./Sidebar.svelte", names=["Sidebar"]),
                    ImportInfo(source="$lib/stores/authStore", names=["authStore"]),
                    ImportInfo(source="$lib/stores/themeStore", names=["themeStore"]),
                ],
                store_refs=[
                    StoreRef(store_name="authStore", access="read"),
                    StoreRef(store_name="themeStore", access="read"),
                ],
            ),
            ComponentMap(
                name="+page",
                file="src/routes/+page.svelte",
                line_count=10,
                imports=[
                    ImportInfo(source="$lib/components/DataTable.svelte", names=["DataTable"]),
                    ImportInfo(source="$lib/stores/authStore", names=["authStore"]),
                ],
                store_refs=[
                    StoreRef(store_name="authStore", access="read"),
                ],
            ),
        ],
        stores=[
            StoreMap(name="tableStore", file="src/lib/stores/tableStore.ts", kind="writable", line_count=12),
            StoreMap(name="authStore", file="src/lib/stores/authStore.ts", kind="writable", line_count=20),
            StoreMap(name="themeStore", file="src/lib/stores/themeStore.ts", kind="writable", line_count=8),
        ],
    )


@pytest.fixture
def graph(small_project) -> ImportGraph:
    return ImportGraph.build(small_project)


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

class TestImportGraphConstruction:
    def test_graph_has_component_nodes(self, graph):
        assert "Button" in graph.nodes
        assert "DataTable" in graph.nodes
        assert "Spinner" in graph.nodes

    def test_graph_has_store_nodes(self, graph):
        assert "tableStore" in graph.nodes
        assert "authStore" in graph.nodes

    def test_button_imports_spinner(self, graph):
        assert graph.has_edge("Button", "Spinner")

    def test_datatable_imports_pagination(self, graph):
        assert graph.has_edge("DataTable", "Pagination")

    def test_datatable_uses_tablestore(self, graph):
        assert graph.has_edge("DataTable", "tableStore")

    def test_layout_uses_authstore(self, graph):
        assert graph.has_edge("+layout", "authStore")

    def test_page_uses_authstore(self, graph):
        assert graph.has_edge("+page", "authStore")

    def test_page_imports_datatable(self, graph):
        assert graph.has_edge("+page", "DataTable")


# ---------------------------------------------------------------------------
# Dependency queries
# ---------------------------------------------------------------------------

class TestImportGraphDependencies:
    def test_direct_deps_of_button(self, graph):
        deps = graph.direct_deps("Button")
        assert "Spinner" in deps

    def test_direct_deps_of_datatable(self, graph):
        deps = graph.direct_deps("DataTable")
        assert "Pagination" in deps
        assert "SortIcon" in deps
        assert "tableStore" in deps

    def test_importers_of_spinner(self, graph):
        """Spinner is imported by Button → Button is an importer of Spinner."""
        importers = graph.importers_of("Spinner")
        assert "Button" in importers

    def test_importers_of_datatable(self, graph):
        importers = graph.importers_of("DataTable")
        assert "+page" in importers

    def test_importers_of_authstore(self, graph):
        importers = graph.importers_of("authStore")
        assert "+layout" in importers
        assert "+page" in importers

    def test_isolated_node_has_no_deps(self, graph):
        """Spinner has no component-level outgoing edges in our fixture."""
        deps = graph.direct_deps("Spinner")
        # Spinner only imports svelte/store (runtime) — no component/store edges
        assert "Button" not in deps      # Button imports Spinner, not vice-versa

    def test_unknown_node_returns_empty(self, graph):
        assert graph.direct_deps("NonExistent") == set()
        assert graph.importers_of("NonExistent") == set()


# ---------------------------------------------------------------------------
# Store consumer map
# ---------------------------------------------------------------------------

class TestStoreConsumerMap:
    def test_tablestore_has_datatable_as_consumer(self, graph):
        consumers = graph.store_consumers("tableStore")
        assert "DataTable" in consumers

    def test_authstore_has_multiple_consumers(self, graph):
        consumers = graph.store_consumers("authStore")
        assert "+layout" in consumers
        assert "+page" in consumers

    def test_unknown_store_returns_empty(self, graph):
        assert graph.store_consumers("ghostStore") == set()


# ---------------------------------------------------------------------------
# High-impact / hotspot detection
# ---------------------------------------------------------------------------

class TestHotspots:
    def test_most_imported_component(self, graph):
        """authStore is imported by 2 components → should rank high."""
        hotspots = graph.hotspots(top_n=3)
        names = [h.name for h in hotspots]
        assert "authStore" in names

    def test_hotspot_has_importer_count(self, graph):
        hotspots = graph.hotspots(top_n=5)
        auth = next(h for h in hotspots if h.name == "authStore")
        assert auth.importer_count >= 2

    def test_top_n_respected(self, graph):
        hotspots = graph.hotspots(top_n=2)
        assert len(hotspots) <= 2

    def test_unused_components(self, graph):
        """Nodes with 0 importers and that are not routes/layouts."""
        unused = graph.unused_components()
        # Button has 0 importers in our fixture → potentially unused
        names = [u.name for u in unused]
        assert "Button" in names

    def test_routes_not_in_unused(self, graph):
        unused = graph.unused_components()
        names = [u.name for u in unused]
        assert "+page" not in names
        assert "+layout" not in names


# ---------------------------------------------------------------------------
# Adjacency list serialisation
# ---------------------------------------------------------------------------

class TestAdjacencyList:
    def test_to_adjacency_dict_structure(self, graph):
        adj = graph.to_adjacency_dict()
        assert isinstance(adj, dict)
        assert "Button" in adj
        assert isinstance(adj["Button"], list)

    def test_button_adjacency_contains_spinner(self, graph):
        adj = graph.to_adjacency_dict()
        assert "Spinner" in adj["Button"]

    def test_all_nodes_present(self, graph):
        adj = graph.to_adjacency_dict()
        for node in graph.nodes:
            assert node in adj
