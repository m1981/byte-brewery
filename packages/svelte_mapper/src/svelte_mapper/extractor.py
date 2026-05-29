"""
extractor.py — Parse .svelte and .ts files into domain model objects.

Strategy: pure regex / string scanning.
- Zero Node.js dependency, zero tree-sitter install pain.
- Covers the high-signal surface area: props, events, slots, imports,
  store refs, TS types.  False-negative rate on pathological code is
  acceptable; false-positives are kept low by anchoring patterns.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from svelte_mapper.models import (
    ComponentMap, StoreMap, TypeInfo,
    PropInfo, EventInfo, SlotInfo, ImportInfo, StoreRef,
    FileKind,
)


# ---------------------------------------------------------------------------
# Shared regex helpers
# ---------------------------------------------------------------------------

# Matches: import [type] { A, B } from 'source'
#          import [type] Foo from './Foo.svelte'
_RE_IMPORT = re.compile(
    r"import\s+(?P<type_kw>type\s+)?"
    r"(?:"
    r"\{(?P<named>[^}]*)\}"      # named imports { A, B }
    r"|(?P<default>\w+)"         # default import Foo
    r")"
    r"\s+from\s+['\"](?P<src>[^'\"]+)['\"]",
    re.MULTILINE,
)

# Matches: export let foo: Type = default
_RE_EXPORT_LET = re.compile(
    r"export\s+let\s+(?P<name>\w+)"
    r"(?:\s*:\s*(?P<type>[^=;\n]+?))?"
    r"(?:\s*=\s*(?P<default>[^;{\n]+?))?(?:\s*;|\s*\n)",
    re.MULTILINE,
)

# Matches dispatch('eventName', …)
_RE_DISPATCH = re.compile(r"dispatch\(\s*['\"](?P<event>[^'\"]+)['\"]")

# Matches <slot name="foo">  or  <slot name='foo'>  or plain <slot>
_RE_SLOT_NAMED = re.compile(r'<slot\s+name=["\'](?P<name>[^"\']+)["\']')
_RE_SLOT_DEFAULT = re.compile(r'<slot(?:\s*/?>|\s*>)')

# Store subscriptions: $storeName  (in template or script)
_RE_STORE_READ = re.compile(r'\$(?P<name>[a-zA-Z_]\w+)')

# Store mutations: storeName.set(  storeName.update(  storeName.subscribe(
_RE_STORE_WRITE = re.compile(r'(?P<name>[a-zA-Z_]\w+)\.(set|update)\s*\(')

# Svelte lifecycle / control-flow markers
_LIFECYCLE_HOOKS = {"onMount", "onDestroy", "beforeUpdate", "afterUpdate", "tick"}
_CONTROL_FLOW = {
    "{#if}": re.compile(r'\{#if\b'),
    "{#each}": re.compile(r'\{#each\b'),
    "{#await}": re.compile(r'\{#await\b'),
    "{#key}": re.compile(r'\{#key\b'),
}
_SPECIAL_ELEMENTS = {
    "<svelte:head>": re.compile(r'<svelte:head\b'),
    "<svelte:self>": re.compile(r'<svelte:self\b'),
    "<svelte:component>": re.compile(r'<svelte:component\b'),
    "<svelte:window>": re.compile(r'<svelte:window\b'),
    "<svelte:body>": re.compile(r'<svelte:body\b'),
}

# TypeScript type declarations
_RE_INTERFACE = re.compile(r'^export\s+interface\s+(?P<name>\w+)', re.MULTILINE)
_RE_TYPE_ALIAS = re.compile(r'^export\s+type\s+(?P<name>\w+)\s*=', re.MULTILINE)
_RE_ENUM = re.compile(r'^export\s+enum\s+(?P<name>\w+)', re.MULTILINE)

# Store declarations in .ts files — classic writable/derived/readable
_RE_STORE_DECL = re.compile(
    r'export\s+const\s+(?P<name>\w+)\s*=\s*(?P<kind>writable|derived|readable)\s*[<(]',
    re.MULTILINE,
)

# Svelte 5 rune-based store: exported const from a factory function
# e.g. export const notesStore = createNotesStore();
_RE_RUNE_STORE_EXPORT = re.compile(
    r'^export\s+const\s+(?P<name>\w+)\s*=',
    re.MULTILINE,
)

# Detect $state / $derived usage = rune-based reactive
_RE_RUNE_STATE = re.compile(r'\$state\s*[<(]|\$derived\s*[<(]')


# ---------------------------------------------------------------------------
# Script block extraction
# ---------------------------------------------------------------------------

def _extract_script_block(source: str) -> str:
    """Return only the content inside the first <script …>…</script> block."""
    m = re.search(r'<script[^>]*>(.*?)</script>', source, re.DOTALL)
    return m.group(1) if m else ""


def _extract_template_block(source: str) -> str:
    """Return source with all <script> blocks stripped (the template portion)."""
    return re.sub(r'<script[^>]*>.*?</script>', '', source, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Import parser (shared by Svelte and TS)
# ---------------------------------------------------------------------------

def _parse_imports(source: str) -> list[ImportInfo]:
    imports: list[ImportInfo] = []
    for m in _RE_IMPORT.finditer(source):
        type_only = bool(m.group("type_kw"))
        src = m.group("src")
        named = m.group("named")
        default = m.group("default")
        names: list[str] = []
        if named:
            # Each token may be prefixed with `type ` keyword (re-export style)
            names = []
            for tok in named.split(","):
                tok = tok.strip()
                # Remove leading `type ` keyword if present
                tok = re.sub(r'^type\s+', '', tok)
                if tok:
                    names.append(tok)
        elif default:
            names = [default.strip()]
        if names:
            imports.append(ImportInfo(source=src, names=names, type_only=type_only))
    return imports


# ---------------------------------------------------------------------------
# SvelteExtractor
# ---------------------------------------------------------------------------

class SvelteExtractor:
    """Parse a single .svelte file into a ComponentMap."""

    @staticmethod
    def parse(filename: str, source: str) -> ComponentMap:
        script = _extract_script_block(source)
        template = _extract_template_block(source)
        full = source  # some patterns need the whole file

        props = SvelteExtractor._extract_props(script)
        events = SvelteExtractor._extract_events(script, template)
        slots = SvelteExtractor._extract_slots(template)
        imports = _parse_imports(script)
        store_refs = SvelteExtractor._extract_store_refs(script, template, imports)
        features = SvelteExtractor._extract_features(script, template)
        kind = SvelteExtractor._infer_kind(filename)

        return ComponentMap(
            name=Path(filename).stem,
            file=filename,
            line_count=len(source.splitlines()),
            kind=kind,
            props=props,
            events=events,
            slots=slots,
            imports=imports,
            store_refs=store_refs,
            svelte_features=features,
        )

    # ---- props -------------------------------------------------------

    @staticmethod
    def _extract_props(script: str) -> list[PropInfo]:
        props: list[PropInfo] = []
        for m in _RE_EXPORT_LET.finditer(script):
            name = m.group("name")
            raw_type = (m.group("type") or "").strip()
            raw_default = (m.group("default") or "").strip()
            props.append(PropInfo(
                name=name,
                type=raw_type or None,
                default=raw_default or None,
            ))
        return props

    # ---- events -------------------------------------------------------

    @staticmethod
    def _extract_events(script: str, template: str) -> list[EventInfo]:
        # Surface events when createEventDispatcher is imported OR when dispatch()
        # is called directly in the template (inline arrow-function handlers).
        full_text = script + "\n" + template
        has_dispatcher = "createEventDispatcher" in script
        has_dispatch_call = bool(_RE_DISPATCH.search(full_text))
        if not has_dispatcher and not has_dispatch_call:
            return []
        seen: set[str] = set()
        events: list[EventInfo] = []
        for m in _RE_DISPATCH.finditer(full_text):
            name = m.group("event")
            if name not in seen:
                seen.add(name)
                events.append(EventInfo(name=name))
        return events

    # ---- slots --------------------------------------------------------

    @staticmethod
    def _extract_slots(template: str) -> list[SlotInfo]:
        slots: list[SlotInfo] = []
        seen: set[str] = set()

        for m in _RE_SLOT_NAMED.finditer(template):
            name = m.group("name")
            if name not in seen:
                seen.add(name)
                slots.append(SlotInfo(name=name))

        # Check for bare <slot> (default slot) — only if not already captured
        if _RE_SLOT_DEFAULT.search(template) and "default" not in seen:
            slots.append(SlotInfo(name="default"))

        return slots

    # ---- store refs ---------------------------------------------------

    @staticmethod
    def _extract_store_refs(script: str, template: str, imports: list[ImportInfo]) -> list[StoreRef]:
        """
        Correlate $name usages and .set/.update calls against known store imports.
        """
        # Collect names that are actually imported stores
        imported_stores: set[str] = {
            n for imp in imports if imp.is_store for n in imp.names
        }
        if not imported_stores:
            return []

        full_text = script + template
        refs: list[StoreRef] = []
        seen: set[tuple[str, str]] = set()

        # Reads: $storeName
        for m in _RE_STORE_READ.finditer(full_text):
            name = m.group("name")
            if name in imported_stores and (name, "read") not in seen:
                seen.add((name, "read"))
                refs.append(StoreRef(store_name=name, access="read"))

        # Writes: storeName.set(…) / storeName.update(…)
        for m in _RE_STORE_WRITE.finditer(full_text):
            name = m.group("name")
            if name in imported_stores and (name, "write") not in seen:
                seen.add((name, "write"))
                refs.append(StoreRef(store_name=name, access="write"))

        return refs

    # ---- svelte features ---------------------------------------------

    @staticmethod
    def _extract_features(script: str, template: str) -> list[str]:
        features: list[str] = []
        full = script + template

        # Lifecycle hooks (imported from 'svelte')
        for hook in _LIFECYCLE_HOOKS:
            if re.search(rf'\b{hook}\s*\(', full):
                features.append(hook)

        # Control flow
        for label, pattern in _CONTROL_FLOW.items():
            if pattern.search(template):
                features.append(label)

        # Special elements
        for label, pattern in _SPECIAL_ELEMENTS.items():
            if pattern.search(full):
                features.append(label)

        return features

    # ---- file kind ---------------------------------------------------

    @staticmethod
    def _infer_kind(filename: str) -> FileKind:
        stem = Path(filename).name
        if stem.startswith("+layout"):
            return FileKind.LAYOUT
        if stem.startswith("+page") or stem.startswith("+error"):
            return FileKind.ROUTE
        return FileKind.COMPONENT


# ---------------------------------------------------------------------------
# TSExtractor
# ---------------------------------------------------------------------------

class TSExtractor:
    """Parse .ts files into StoreMap or TypeInfo objects."""

    @staticmethod
    def parse_store(filename: str, source: str) -> StoreMap:
        """
        Extract the primary exported store from a store .ts file.
        Handles:
          - Classic: export const x = writable/derived/readable(...)
          - Svelte 5 rune-based: $state / $derived inside a factory function
        Falls back to filename stem when nothing else matches.
        """
        # 1. Classic Svelte store
        m = _RE_STORE_DECL.search(source)
        if m:
            name = m.group("name")
            kind = m.group("kind")
            return StoreMap(
                name=name,
                file=filename,
                kind=kind,
                line_count=len(source.splitlines()),
            )

        # 2. Svelte 5 rune store — look for $state/$derived usage + top-level export
        if _RE_RUNE_STATE.search(source):
            # Find the exported singleton name (last `export const X = …`)
            exports = _RE_RUNE_STORE_EXPORT.findall(source)
            name = exports[-1].strip() if exports else Path(filename).stem
            # Clean stem: remove .svelte suffix if file is *.svelte.ts
            stem = Path(filename).stem  # e.g. "notes.svelte"
            if stem.endswith(".svelte"):
                stem = Path(stem).stem   # strip inner .svelte → "notes"
            if not name or not name.replace('_','').isalnum():
                name = stem
            return StoreMap(
                name=name,
                file=filename,
                kind="rune ($state)",
                line_count=len(source.splitlines()),
            )

        # 3. Fallback
        stem = Path(filename).stem
        if stem.endswith(".svelte"):
            stem = Path(stem).stem
        return StoreMap(
            name=stem,
            file=filename,
            kind="custom",
            line_count=len(source.splitlines()),
        )

    @staticmethod
    def parse_types(filename: str, source: str) -> list[TypeInfo]:
        """Extract all exported interface / type alias / enum declarations."""
        types: list[TypeInfo] = []
        for m in _RE_INTERFACE.finditer(source):
            types.append(TypeInfo(name=m.group("name"), kind="interface", file=filename))
        for m in _RE_TYPE_ALIAS.finditer(source):
            types.append(TypeInfo(name=m.group("name"), kind="type", file=filename))
        for m in _RE_ENUM.finditer(source):
            types.append(TypeInfo(name=m.group("name"), kind="enum", file=filename))
        return types

    @staticmethod
    def classify_file(filename: str) -> FileKind:
        """Classify a .ts file by its role in the project."""
        p = Path(filename)
        name = p.name           # e.g. "notes.svelte.ts" or "+server.ts"
        # All path parts give directory-level context (e.g. 'stores')
        all_parts = " ".join(p.parts).lower()

        # Normalise stem: strip .ts then optionally inner .svelte
        stem = name
        if stem.endswith(".ts"):
            stem = stem[:-3]                # "notes.svelte" or "+server"
        if stem.endswith(".svelte"):
            stem = stem[:-7]               # "notes" or "sidebar-resize"
        stem_lower = stem.lower()

        if name.startswith("+server"):
            return FileKind.SERVER
        if name.startswith("+page") or name.startswith("+layout") or name.startswith("+error"):
            return FileKind.ROUTE
        # Match stem OR any parent directory named store/stores
        if "store" in stem_lower or "store" in all_parts:
            return FileKind.STORE
        if stem_lower in ("types", "type", "interfaces", "models", "schema"):
            return FileKind.TYPES
        return FileKind.UTIL
