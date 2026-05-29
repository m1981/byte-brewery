"""svelte_mapper — compact structural map of Svelte/TS codebases for LLM agents."""

from svelte_mapper.models import (
    PropInfo, EventInfo, SlotInfo, ImportInfo, StoreRef,
    ComponentMap, StoreMap, TypeInfo, ProjectMap, FileKind,
)
from svelte_mapper.extractor import SvelteExtractor, TSExtractor
from svelte_mapper.graph import ImportGraph
from svelte_mapper.renderer import MapRenderer, RendererConfig, OutputLayer
from svelte_mapper.scanner import Scanner

__all__ = [
    "PropInfo", "EventInfo", "SlotInfo", "ImportInfo", "StoreRef",
    "ComponentMap", "StoreMap", "TypeInfo", "ProjectMap", "FileKind",
    "SvelteExtractor", "TSExtractor",
    "ImportGraph",
    "MapRenderer", "RendererConfig", "OutputLayer",
    "Scanner",
]
