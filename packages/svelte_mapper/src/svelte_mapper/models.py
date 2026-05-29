"""
Domain models for the Svelte codebase map.

Design goals:
- Pydantic v2 throughout (model_dump, model_validate, computed_field)
- All fields optional with sensible defaults to keep construction ergonomic
- Serialises cleanly to dict/JSON for renderer consumption
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator, computed_field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FileKind(str, Enum):
    COMPONENT = "component"
    STORE = "store"
    TYPES = "types"
    ROUTE = "route"
    LAYOUT = "layout"
    SERVER = "server"
    UTIL = "util"


# ---------------------------------------------------------------------------
# Leaf models
# ---------------------------------------------------------------------------

class PropInfo(BaseModel):
    """A single `export let` prop declaration."""
    name: str
    type: Optional[str] = None
    default: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def required(self) -> bool:
        return self.default is None


class EventInfo(BaseModel):
    """A dispatched custom event."""
    name: str
    payload: Optional[str] = None


class SlotInfo(BaseModel):
    """A <slot> element (named or default)."""
    name: str = "default"


class ImportInfo(BaseModel):
    """A single import statement parsed from a <script> block or .ts file."""
    source: str
    names: list[str]
    type_only: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_relative(self) -> bool:
        return self.source.startswith("./") or self.source.startswith("../")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_svelte_runtime(self) -> bool:
        return self.source == "svelte" or self.source.startswith("svelte/")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_store(self) -> bool:
        """True when the import path smells like a project store reference."""
        if self.is_svelte_runtime:
            return False
        low = self.source.lower()
        return "store" in low or "stores" in low


class StoreRef(BaseModel):
    """A reference to a Svelte store within a component (read or write)."""
    store_name: str
    access: Literal["read", "write"]


# ---------------------------------------------------------------------------
# File-level models
# ---------------------------------------------------------------------------

class ComponentMap(BaseModel):
    """Full extracted signature of one .svelte file."""
    name: str
    file: str
    line_count: int
    kind: FileKind = FileKind.COMPONENT
    props: list[PropInfo] = Field(default_factory=list)
    events: list[EventInfo] = Field(default_factory=list)
    slots: list[SlotInfo] = Field(default_factory=list)
    imports: list[ImportInfo] = Field(default_factory=list)
    store_refs: list[StoreRef] = Field(default_factory=list)
    svelte_features: list[str] = Field(default_factory=list)


class StoreMap(BaseModel):
    """Metadata about a Svelte store exported from a .ts file."""
    name: str
    file: str
    kind: str                           # writable | derived | readable | custom
    line_count: int
    readers: list[str] = Field(default_factory=list)   # component names that read it
    writers: list[str] = Field(default_factory=list)   # component names that write it


class TypeInfo(BaseModel):
    """A TypeScript type declaration (interface / type alias / enum)."""
    name: str
    kind: Literal["interface", "type", "enum"]
    file: str


# ---------------------------------------------------------------------------
# Project-level aggregate
# ---------------------------------------------------------------------------

class ProjectMap(BaseModel):
    """The full structural map of a Svelte/SvelteKit project."""
    root: str
    components: list[ComponentMap] = Field(default_factory=list)
    stores: list[StoreMap] = Field(default_factory=list)
    types: list[TypeInfo] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def component_count(self) -> int:
        return len(self.components)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def store_count(self) -> int:
        return len(self.stores)
