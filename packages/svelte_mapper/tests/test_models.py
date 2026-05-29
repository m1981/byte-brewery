"""
TDD – Layer 0: Domain models.
Tests validate that Pydantic models accept correct data, reject invalid data,
and serialise cleanly to dict/JSON for renderer consumption.
"""
import pytest
from pydantic import ValidationError

from svelte_mapper.models import (
    PropInfo,
    EventInfo,
    SlotInfo,
    ImportInfo,
    StoreRef,
    ComponentMap,
    StoreMap,
    TypeInfo,
    ProjectMap,
    FileKind,
)


# ---------------------------------------------------------------------------
# PropInfo
# ---------------------------------------------------------------------------

class TestPropInfo:
    def test_minimal_prop(self):
        p = PropInfo(name="label")
        assert p.name == "label"
        assert p.type is None
        assert p.default is None
        assert p.required is True           # no default → required

    def test_prop_with_type_and_default(self):
        p = PropInfo(name="pageSize", type="number", default="10")
        assert p.required is False          # has a default

    def test_prop_boolean_default(self):
        p = PropInfo(name="disabled", type="boolean", default="false")
        assert p.required is False

    def test_prop_name_required(self):
        with pytest.raises(ValidationError):
            PropInfo()                       # name is mandatory


# ---------------------------------------------------------------------------
# EventInfo
# ---------------------------------------------------------------------------

class TestEventInfo:
    def test_event_name_only(self):
        e = EventInfo(name="click")
        assert e.name == "click"
        assert e.payload is None

    def test_event_with_payload(self):
        e = EventInfo(name="rowClick", payload="{ row: Item }")
        assert e.payload == "{ row: Item }"

    def test_event_name_required(self):
        with pytest.raises(ValidationError):
            EventInfo()


# ---------------------------------------------------------------------------
# SlotInfo
# ---------------------------------------------------------------------------

class TestSlotInfo:
    def test_default_slot(self):
        s = SlotInfo(name="default")
        assert s.name == "default"

    def test_named_slot(self):
        s = SlotInfo(name="icon")
        assert s.name == "icon"


# ---------------------------------------------------------------------------
# ImportInfo
# ---------------------------------------------------------------------------

class TestImportInfo:
    def test_relative_import(self):
        i = ImportInfo(source="./Spinner.svelte", names=["Spinner"])
        assert i.is_relative is True
        assert i.is_store is False
        assert i.is_svelte_runtime is False

    def test_store_import(self):
        i = ImportInfo(source="$lib/stores/tableStore", names=["tableStore"])
        assert i.is_store is True
        assert i.is_relative is False

    def test_svelte_runtime_import(self):
        i = ImportInfo(source="svelte", names=["onMount", "onDestroy"])
        assert i.is_svelte_runtime is True

    def test_svelte_store_runtime(self):
        i = ImportInfo(source="svelte/store", names=["writable"])
        assert i.is_svelte_runtime is True

    def test_type_only_import(self):
        i = ImportInfo(source="$lib/types", names=["ButtonVariant"], type_only=True)
        assert i.type_only is True

    def test_names_required(self):
        with pytest.raises(ValidationError):
            ImportInfo(source="svelte")     # names missing


# ---------------------------------------------------------------------------
# StoreRef
# ---------------------------------------------------------------------------

class TestStoreRef:
    def test_store_ref_read(self):
        sr = StoreRef(store_name="tableStore", access="read")
        assert sr.access == "read"

    def test_store_ref_write(self):
        sr = StoreRef(store_name="authStore", access="write")
        assert sr.access == "write"

    def test_invalid_access(self):
        with pytest.raises(ValidationError):
            StoreRef(store_name="x", access="unknown")


# ---------------------------------------------------------------------------
# ComponentMap
# ---------------------------------------------------------------------------

class TestComponentMap:
    def test_minimal_component(self):
        cm = ComponentMap(
            name="Button",
            file="src/lib/components/Button.svelte",
            line_count=30,
        )
        assert cm.props == []
        assert cm.events == []
        assert cm.slots == []
        assert cm.imports == []
        assert cm.store_refs == []
        assert cm.svelte_features == []

    def test_full_component(self):
        cm = ComponentMap(
            name="DataTable",
            file="src/lib/components/DataTable.svelte",
            line_count=55,
            props=[PropInfo(name="items", type="Item[]", default="[]")],
            events=[EventInfo(name="rowClick")],
            slots=[SlotInfo(name="row")],
            imports=[ImportInfo(source="./Pagination.svelte", names=["Pagination"])],
            store_refs=[StoreRef(store_name="tableStore", access="write")],
            svelte_features=["onMount", "onDestroy", "{#each}"],
        )
        assert len(cm.props) == 1
        assert cm.props[0].name == "items"
        assert "onMount" in cm.svelte_features

    def test_serialisation_roundtrip(self):
        cm = ComponentMap(
            name="Spinner",
            file="src/lib/components/Spinner.svelte",
            line_count=5,
        )
        data = cm.model_dump()
        assert data["name"] == "Spinner"
        assert isinstance(data["props"], list)


# ---------------------------------------------------------------------------
# StoreMap
# ---------------------------------------------------------------------------

class TestStoreMap:
    def test_minimal_store(self):
        sm = StoreMap(
            name="tableStore",
            file="src/lib/stores/tableStore.ts",
            kind="writable",
            line_count=12,
        )
        assert sm.readers == []
        assert sm.writers == []

    def test_store_with_readers_writers(self):
        sm = StoreMap(
            name="authStore",
            file="src/lib/stores/authStore.ts",
            kind="writable",
            line_count=20,
            readers=["Header", "Sidebar"],
            writers=["LoginForm"],
        )
        assert "Header" in sm.readers


# ---------------------------------------------------------------------------
# TypeInfo
# ---------------------------------------------------------------------------

class TestTypeInfo:
    def test_interface(self):
        t = TypeInfo(name="User", kind="interface", file="src/lib/types.ts")
        assert t.kind == "interface"

    def test_type_alias(self):
        t = TypeInfo(name="ButtonVariant", kind="type", file="src/lib/types.ts")
        assert t.kind == "type"

    def test_enum(self):
        t = TypeInfo(name="Theme", kind="enum", file="src/lib/types.ts")
        assert t.kind == "enum"

    def test_invalid_kind(self):
        with pytest.raises(ValidationError):
            TypeInfo(name="X", kind="class", file="f.ts")


# ---------------------------------------------------------------------------
# FileKind
# ---------------------------------------------------------------------------

class TestFileKind:
    def test_all_kinds(self):
        assert FileKind.COMPONENT == "component"
        assert FileKind.STORE == "store"
        assert FileKind.TYPES == "types"
        assert FileKind.ROUTE == "route"
        assert FileKind.LAYOUT == "layout"
        assert FileKind.SERVER == "server"
        assert FileKind.UTIL == "util"


# ---------------------------------------------------------------------------
# ProjectMap
# ---------------------------------------------------------------------------

class TestProjectMap:
    def test_empty_project(self):
        pm = ProjectMap(root=".")
        assert pm.components == []
        assert pm.stores == []
        assert pm.types == []
        assert pm.routes == []

    def test_project_with_data(self):
        pm = ProjectMap(
            root="/home/user/myapp",
            components=[
                ComponentMap(name="Button", file="src/lib/components/Button.svelte", line_count=30),
                ComponentMap(name="DataTable", file="src/lib/components/DataTable.svelte", line_count=55),
            ],
            stores=[
                StoreMap(name="authStore", file="src/lib/stores/authStore.ts", kind="writable", line_count=20),
            ],
        )
        assert len(pm.components) == 2
        assert len(pm.stores) == 1

    def test_component_count(self):
        pm = ProjectMap(
            root=".",
            components=[
                ComponentMap(name=f"Comp{i}", file=f"comp{i}.svelte", line_count=10)
                for i in range(5)
            ],
        )
        assert pm.component_count == 5

    def test_store_count(self):
        pm = ProjectMap(
            root=".",
            stores=[
                StoreMap(name="s1", file="s1.ts", kind="writable", line_count=5),
                StoreMap(name="s2", file="s2.ts", kind="derived", line_count=5),
            ],
        )
        assert pm.store_count == 2

    def test_full_serialisation(self):
        pm = ProjectMap(root=".")
        data = pm.model_dump()
        assert "components" in data
        assert "stores" in data
        assert "types" in data
        assert "routes" in data
