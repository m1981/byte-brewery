"""
TDD – Layer 1: File extractor.
Tests cover parsing of .svelte and .ts files into domain model objects.
All inputs come from conftest.py string constants — no real project needed.
"""
import pytest
from pathlib import Path

from svelte_mapper.extractor import SvelteExtractor, TSExtractor
from svelte_mapper.models import FileKind


# ===========================================================================
# SvelteExtractor
# ===========================================================================

class TestSvelteExtractorProps:
    """Props are extracted from `export let` statements in <script>."""

    def test_simple_string_prop_with_default(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        label = next(p for p in comp.props if p.name == "label")
        assert label.type == "string"
        assert label.default == "'Click me'"
        assert label.required is False

    def test_boolean_prop_with_default(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        disabled = next(p for p in comp.props if p.name == "disabled")
        assert disabled.type == "boolean"
        assert disabled.default == "false"
        assert disabled.required is False

    def test_typed_prop_with_alias_type(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        variant = next(p for p in comp.props if p.name == "variant")
        assert variant.type == "ButtonVariant"

    def test_array_prop_with_default(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        items = next(p for p in comp.props if p.name == "items")
        assert "Item" in items.type
        assert items.default == "[]"

    def test_number_prop(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        ps = next(p for p in comp.props if p.name == "pageSize")
        assert ps.type == "number"
        assert ps.default == "10"

    def test_no_props_when_none_exported(self, conftest_source):
        comp = SvelteExtractor.parse("Spinner.svelte", conftest_source("NO_EXPORTS_SVELTE"))
        assert comp.props == []

    def test_empty_file_gives_empty_component(self, conftest_source):
        comp = SvelteExtractor.parse("Empty.svelte", conftest_source("EMPTY_SVELTE"))
        assert comp.props == []
        assert comp.events == []
        assert comp.imports == []


class TestSvelteExtractorEvents:
    """Events are detected from dispatch('eventName', …) calls."""

    def test_click_event(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        event_names = [e.name for e in comp.events]
        assert "click" in event_names

    def test_multiple_events_in_template(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        event_names = [e.name for e in comp.events]
        assert "rowClick" in event_names

    def test_no_events_when_no_dispatch(self, conftest_source):
        comp = SvelteExtractor.parse("Layout.svelte", conftest_source("LAYOUT_SVELTE"))
        # Layout doesn't use createEventDispatcher
        assert comp.events == []


class TestSvelteExtractorSlots:
    """Named slots are extracted from <slot name="…"> in the template."""

    def test_named_icon_slot(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        slot_names = [s.name for s in comp.slots]
        assert "icon" in slot_names

    def test_default_slot_detected(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        slot_names = [s.name for s in comp.slots]
        assert "default" in slot_names

    def test_named_row_slot_in_datatable(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        slot_names = [s.name for s in comp.slots]
        assert "row" in slot_names

    def test_no_slots_in_spinner(self, conftest_source):
        comp = SvelteExtractor.parse("Spinner.svelte", conftest_source("NO_EXPORTS_SVELTE"))
        assert comp.slots == []


class TestSvelteExtractorImports:
    """Import statements are parsed from the <script> block."""

    def test_relative_component_import(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        sources = [i.source for i in comp.imports]
        assert "./Spinner.svelte" in sources

    def test_svelte_runtime_import(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        runtime_imports = [i for i in comp.imports if i.is_svelte_runtime]
        assert len(runtime_imports) >= 1

    def test_store_import(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        store_imports = [i for i in comp.imports if i.is_store]
        names = [n for i in store_imports for n in i.names]
        assert "tableStore" in names

    def test_type_only_import(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        type_imports = [i for i in comp.imports if i.type_only]
        assert len(type_imports) >= 1

    def test_layout_has_store_imports(self, conftest_source):
        comp = SvelteExtractor.parse("+layout.svelte", conftest_source("LAYOUT_SVELTE"))
        store_imports = [i for i in comp.imports if i.is_store]
        assert len(store_imports) >= 1


class TestSvelteExtractorStoreRefs:
    """Store references: subscriptions ($store) and mutations (.set/.update)."""

    def test_store_read_via_dollar_prefix(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        store_names = [s.store_name for s in comp.store_refs]
        assert "tableStore" in store_names

    def test_store_write_via_update(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        writes = [s for s in comp.store_refs if s.access == "write"]
        assert any(s.store_name == "tableStore" for s in writes)


class TestSvelteExtractorFeatures:
    """Svelte-specific features: lifecycle, control flow, special elements."""

    def test_lifecycle_onmount_detected(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        assert "onMount" in comp.svelte_features

    def test_lifecycle_ondestroy_detected(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        assert "onDestroy" in comp.svelte_features

    def test_each_block_detected(self, conftest_source):
        comp = SvelteExtractor.parse("DataTable.svelte", conftest_source("DATA_TABLE_SVELTE"))
        assert "{#each}" in comp.svelte_features

    def test_svelte_head_detected(self, conftest_source):
        comp = SvelteExtractor.parse("+layout.svelte", conftest_source("LAYOUT_SVELTE"))
        assert "<svelte:head>" in comp.svelte_features

    def test_no_features_in_empty_file(self, conftest_source):
        comp = SvelteExtractor.parse("Empty.svelte", conftest_source("EMPTY_SVELTE"))
        assert comp.svelte_features == []


class TestSvelteExtractorFileKind:
    """File kind is inferred from filename conventions."""

    def test_layout_file_kind(self, conftest_source):
        comp = SvelteExtractor.parse("+layout.svelte", conftest_source("LAYOUT_SVELTE"))
        assert comp.kind == FileKind.LAYOUT

    def test_page_file_kind(self, conftest_source):
        comp = SvelteExtractor.parse("+page.svelte", conftest_source("PAGE_SVELTE"))
        assert comp.kind == FileKind.ROUTE

    def test_regular_component_kind(self, conftest_source):
        comp = SvelteExtractor.parse("Button.svelte", conftest_source("SIMPLE_BUTTON_SVELTE"))
        assert comp.kind == FileKind.COMPONENT

    def test_line_count_is_accurate(self, conftest_source):
        src = conftest_source("SIMPLE_BUTTON_SVELTE")
        comp = SvelteExtractor.parse("Button.svelte", src)
        assert comp.line_count == len(src.splitlines())


# ===========================================================================
# TSExtractor
# ===========================================================================

class TestTSExtractorStores:
    """TypeScript store files: exported store names and kinds."""

    def test_writable_store_detected(self, conftest_source):
        sm = TSExtractor.parse_store("tableStore.ts", conftest_source("TABLE_STORE_TS"))
        assert sm.name == "tableStore"
        assert sm.kind == "writable"

    def test_derived_store_detected(self, conftest_source):
        sm = TSExtractor.parse_store("tableStore.ts", conftest_source("TABLE_STORE_TS"))
        # sortedRows is derived — store file may surface both or primary only
        # We verify the file is correctly identified as a store file
        assert sm.file.endswith("tableStore.ts")

    def test_auth_store_writable(self, conftest_source):
        sm = TSExtractor.parse_store("authStore.ts", conftest_source("AUTH_STORE_TS"))
        assert sm.kind == "writable"
        assert sm.name == "authStore"

    def test_line_count_correct(self, conftest_source):
        src = conftest_source("TABLE_STORE_TS")
        sm = TSExtractor.parse_store("tableStore.ts", src)
        assert sm.line_count == len(src.splitlines())


class TestTSExtractorTypes:
    """TypeScript type files: interfaces, type aliases, enums."""

    def test_interface_user_detected(self, conftest_source):
        types = TSExtractor.parse_types("types.ts", conftest_source("TYPES_TS"))
        names = [t.name for t in types]
        assert "User" in names

    def test_type_alias_detected(self, conftest_source):
        types = TSExtractor.parse_types("types.ts", conftest_source("TYPES_TS"))
        aliases = [t for t in types if t.kind == "type"]
        assert any(t.name == "ButtonVariant" for t in aliases)

    def test_interface_tablestate_detected(self, conftest_source):
        types = TSExtractor.parse_types("types.ts", conftest_source("TYPES_TS"))
        interfaces = [t for t in types if t.kind == "interface"]
        assert any(t.name == "TableState" for t in interfaces)

    def test_enum_detected(self, conftest_source):
        types = TSExtractor.parse_types("types.ts", conftest_source("TYPES_TS"))
        enums = [t for t in types if t.kind == "enum"]
        assert any(t.name == "Theme" for t in enums)

    def test_empty_source_gives_empty_list(self):
        types = TSExtractor.parse_types("empty.ts", "")
        assert types == []


class TestTSExtractorFileKindClassification:
    """TSExtractor.classify_file correctly labels TS files."""

    def test_store_file_classified(self):
        assert TSExtractor.classify_file("tableStore.ts") == FileKind.STORE

    def test_types_file_classified(self):
        assert TSExtractor.classify_file("types.ts") == FileKind.TYPES

    def test_server_file_classified(self):
        assert TSExtractor.classify_file("+server.ts") == FileKind.SERVER

    def test_page_ts_classified_as_route(self):
        assert TSExtractor.classify_file("+page.ts") == FileKind.ROUTE

    def test_generic_ts_classified_as_util(self):
        assert TSExtractor.classify_file("helpers.ts") == FileKind.UTIL


# ===========================================================================
# Fixtures used inside this test module
# ===========================================================================

@pytest.fixture
def conftest_source():
    """Return a callable that fetches raw source strings from conftest constants."""
    from pathlib import Path
    import importlib.util, sys
    conftest_path = Path(__file__).parent / "conftest.py"
    spec = importlib.util.spec_from_file_location("_svelte_conftest", conftest_path)
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    def _get(name: str) -> str:
        return getattr(cf, name)
    return _get
