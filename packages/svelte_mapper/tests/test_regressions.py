"""
test_regressions.py — Regression tests for bugs discovered during the
real kitchen-agent run.

Each class documents exactly which bug it guards against, the original
symptom, and the fix.  No test here should ever silently re-break.

Bugs covered
------------
BUG-1  Named import starting with 't' was mangled (tableStore → ableStore)
       Root cause: `lstrip("type")` strips individual chars, not the word "type"
       Fix: re.sub(r"^type\\s+", "", tok) on each comma-separated token

BUG-2  dispatch() in template-only inline handler was missed
       Root cause: event guard required `createEventDispatcher` in script
       Fix: also surface events when dispatch() call is found anywhere in source

BUG-3  Svelte 5 rune stores (*.svelte.ts) produced empty store topology
       Root cause A: classify_file only knew writable/derived/readable patterns
       Fix A: detect $state/$derived and return kind="rune ($state)"
       Root cause B: *.svelte.ts suffix confusingly has suffix='.ts' but was
                     not being picked up as FileKind.STORE when the stem
                     ("notes") contains no "store" keyword
       Fix B: check all path parts (parent dirs) for "store", not just stem

BUG-4  Scanner passed bare filename to classify_file losing directory context
       Root cause: `kind = TSExtractor.classify_file(fname)` — fname has no dir
       Fix: `kind = TSExtractor.classify_file(rel)` — rel has full relative path
"""
import importlib.util
from pathlib import Path

import pytest

from svelte_mapper.extractor import TSExtractor, _parse_imports
from svelte_mapper.models import FileKind
from svelte_mapper.scanner import Scanner


# ---------------------------------------------------------------------------
# Helper: load conftest constants without package import
# ---------------------------------------------------------------------------

def _cf():
    spec = importlib.util.spec_from_file_location(
        "_svelte_conftest", Path(__file__).parent / "conftest.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cf = _cf()


# ===========================================================================
# BUG-1 — Named import mangling (tableStore → ableStore)
# ===========================================================================

class TestBug1NamedImportMangling:
    """
    lstrip("type") was used to strip the 'type' keyword from named imports.
    lstrip strips a *set of characters*, so any token starting with t, y, p,
    or e lost its leading character.  tableStore became ableStore.
    """

    def test_tablestore_import_name_is_intact(self):
        imports = _parse_imports(cf.STORE_IMPORT_STARTS_WITH_T)
        names = [n for imp in imports for n in imp.names]
        assert "tableStore" in names, f"tableStore was mangled; got names={names}"

    def test_themestore_import_name_is_intact(self):
        imports = _parse_imports(cf.STORE_IMPORT_STARTS_WITH_T)
        names = [n for imp in imports for n in imp.names]
        assert "themeStore" in names, f"themeStore was mangled; got names={names}"

    def test_token_service_import_intact(self):
        """tokenService also starts with 't' — another victim of the old bug."""
        imports = _parse_imports(cf.STORE_IMPORT_STARTS_WITH_T)
        names = [n for imp in imports for n in imp.names]
        assert "tokenService" in names, f"tokenService mangled; got names={names}"

    def test_no_stray_stripped_names(self):
        """None of the parsed names should be missing their first character."""
        imports = _parse_imports(cf.STORE_IMPORT_STARTS_WITH_T)
        names = [n for imp in imports for n in imp.names]
        for name in names:
            # Every import name here begins with a known letter; none should
            # be a substring that's missing the leading 't'
            for bad in ("ableStore", "hemeStore", "okenService"):
                assert bad not in names, f"Mangled name '{bad}' found in {names}"

    def test_type_keyword_prefix_still_stripped(self):
        """'import type { Foo }' — the word 'type' IS a keyword and must be removed."""
        src = "import type { Foo, Bar } from './types';"
        imports = _parse_imports(src)
        names = [n for imp in imports for n in imp.names]
        assert "Foo" in names
        assert "Bar" in names
        # "type" keyword itself must NOT appear as a name
        assert "type" not in names

    def test_inline_type_keyword_in_named_import(self):
        """'import { type Foo, Bar }' — per-item type keyword must be stripped."""
        src = "import { type Foo, Bar } from './types';"
        imports = _parse_imports(src)
        names = [n for imp in imports for n in imp.names]
        assert "Foo" in names
        assert "Bar" in names
        assert "type" not in names


# ===========================================================================
# BUG-2 — dispatch() in template-only inline handler was silently dropped
# ===========================================================================

class TestBug2TemplateOnlyDispatch:
    """
    DataTable dispatched 'rowClick' via an inline arrow in the template:
      <tr on:click={() => dispatch('rowClick', row)}>
    but the component did NOT import createEventDispatcher.
    The original guard `if "createEventDispatcher" not in script: return []`
    caused all such events to be invisible.
    """

    def test_event_found_when_dispatch_only_in_template(self):
        from svelte_mapper.extractor import SvelteExtractor
        comp = SvelteExtractor.parse("InlineDispatch.svelte", cf.DISPATCH_IN_TEMPLATE_ONLY)
        event_names = [e.name for e in comp.events]
        assert "select" in event_names, (
            f"'select' event missing; got {event_names}. "
            "dispatch() in template-only handler must be detected."
        )

    def test_no_false_events_without_any_dispatch(self):
        """Components with no dispatch() at all must yield no events."""
        from svelte_mapper.extractor import SvelteExtractor
        comp = SvelteExtractor.parse("NoDispatch.svelte", cf.NO_EXPORTS_SVELTE)
        assert comp.events == []

    def test_event_from_script_still_found(self):
        """Events dispatched inside the script block continue to work."""
        from svelte_mapper.extractor import SvelteExtractor
        comp = SvelteExtractor.parse("Button.svelte", cf.SIMPLE_BUTTON_SVELTE)
        event_names = [e.name for e in comp.events]
        assert "click" in event_names

    def test_event_from_template_in_data_table(self):
        """The original kitchen-agent case: rowClick dispatched in template."""
        from svelte_mapper.extractor import SvelteExtractor
        comp = SvelteExtractor.parse("DataTable.svelte", cf.DATA_TABLE_SVELTE)
        event_names = [e.name for e in comp.events]
        assert "rowClick" in event_names, (
            f"rowClick missing; got {event_names}. "
            "This is the exact regression from the kitchen-agent run."
        )

    def test_no_duplicate_events(self):
        """If dispatch() appears twice with same name, only one EventInfo emitted."""
        from svelte_mapper.extractor import SvelteExtractor
        src = """\
<script lang="ts">
  function a() { dispatch('save'); }
</script>
<button on:click={() => dispatch('save')}>Save</button>
"""
        comp = SvelteExtractor.parse("Dup.svelte", src)
        save_events = [e for e in comp.events if e.name == "save"]
        assert len(save_events) == 1, f"Duplicate events; got {comp.events}"


# ===========================================================================
# BUG-3a — Svelte 5 rune store parse_store returns wrong kind / name
# ===========================================================================

class TestBug3aRuneStoreParsing:
    """
    parse_store only matched writable/derived/readable.
    Svelte 5 stores use $state/$derived inside a factory function.
    """

    def test_rune_store_kind_is_labelled(self):
        sm = TSExtractor.parse_store("lib/stores/notes.svelte.ts", cf.RUNE_NOTES_STORE_TS)
        assert "rune" in sm.kind.lower(), (
            f"Expected rune kind, got '{sm.kind}'. "
            "Svelte 5 $state stores must be labelled as rune."
        )

    def test_rune_store_name_extracted(self):
        sm = TSExtractor.parse_store("lib/stores/notes.svelte.ts", cf.RUNE_NOTES_STORE_TS)
        assert sm.name == "notesStore", (
            f"Expected 'notesStore', got '{sm.name}'. "
            "The exported singleton name must be the store name."
        )

    def test_rune_session_store_name(self):
        sm = TSExtractor.parse_store("lib/stores/sessions.svelte.ts", cf.RUNE_SESSION_STORE_TS)
        assert sm.name == "sessionStore"

    def test_rune_session_store_kind(self):
        sm = TSExtractor.parse_store("lib/stores/sessions.svelte.ts", cf.RUNE_SESSION_STORE_TS)
        assert "rune" in sm.kind.lower()

    def test_rune_store_line_count(self):
        sm = TSExtractor.parse_store("lib/stores/notes.svelte.ts", cf.RUNE_NOTES_STORE_TS)
        assert sm.line_count == len(cf.RUNE_NOTES_STORE_TS.splitlines())

    def test_classic_store_still_detected_as_writable(self):
        """Rune detection must not break classic store detection."""
        sm = TSExtractor.parse_store("tableStore.ts", cf.TABLE_STORE_TS)
        assert sm.kind == "writable"
        assert sm.name == "tableStore"

    def test_derived_store_still_detected(self):
        src = "export const myStore = derived(base, $b => $b * 2);"
        sm = TSExtractor.parse_store("derived.ts", src)
        assert sm.kind == "derived"

    def test_store_without_state_falls_back_to_custom(self):
        """A .ts file with no $state and no writable() gets kind='custom'."""
        src = "export const helper = { doThing() {} };"
        sm = TSExtractor.parse_store("lib/stores/helper.ts", src)
        assert sm.kind == "custom"

    def test_svelte_stem_stripped_from_fallback_name(self):
        """When falling back to filename stem, '.svelte' infix is removed."""
        src = "export const helper = { doThing() {} };"
        sm = TSExtractor.parse_store("lib/stores/helper.svelte.ts", src)
        # stem of "helper.svelte.ts" → "helper.svelte" → strip ".svelte" → "helper"
        assert ".svelte" not in sm.name


# ===========================================================================
# BUG-3b — classify_file must use full path parts, not just filename stem
# ===========================================================================

class TestBug3bClassifyFileWithPath:
    """
    When the filename has no 'store' in its stem (e.g. 'notes.svelte.ts')
    but lives inside a 'stores/' directory, classify_file must still return
    FileKind.STORE.  The old code only checked the stem.
    """

    # -- Cases that MUST be STORE ----------------------------------------

    def test_svelte_ts_in_stores_dir_is_store(self):
        assert TSExtractor.classify_file(cf.STORE_REL_PATH_SVELTE_TS) == FileKind.STORE, (
            f"'{cf.STORE_REL_PATH_SVELTE_TS}' must be STORE — lives in stores/ dir."
        )

    def test_plain_ts_in_stores_dir_is_store(self):
        assert TSExtractor.classify_file(cf.STORE_REL_PATH_PLAIN_TS) == FileKind.STORE

    def test_filename_with_store_in_stem_is_store(self):
        assert TSExtractor.classify_file("tableStore.ts") == FileKind.STORE

    def test_nested_stores_dir_is_store(self):
        """Deeply nested: src/app/feature/stores/counter.svelte.ts"""
        assert TSExtractor.classify_file(
            "src/app/feature/stores/counter.svelte.ts"
        ) == FileKind.STORE

    # -- Cases that must NOT be misclassified as STORE -------------------

    def test_sidebar_resize_svelte_ts_is_util(self):
        """sidebar-resize.svelte.ts has no 'store' anywhere — must be UTIL."""
        assert TSExtractor.classify_file(cf.NON_STORE_REL_PATH) == FileKind.UTIL

    def test_bare_notes_filename_without_path_is_util(self):
        """
        The OLD broken form: bare filename passed without directory context.
        'notes.svelte.ts' has no 'store' in stem and no path parts.
        This was the original bug: scanner used fname instead of rel.
        We document it here so we know the bare form is NOT reliable.
        """
        result = TSExtractor.classify_file(cf.NON_STORE_BARE_FILENAME)
        # Without directory context the classifier CANNOT know it's a store.
        # It returns UTIL — that is the correct/expected behaviour for bare names.
        assert result == FileKind.UTIL, (
            "Bare filename without path correctly returns UTIL — "
            "the scanner must always pass the relative path, not just fname."
        )

    def test_server_file_not_store(self):
        assert TSExtractor.classify_file("+server.ts") == FileKind.SERVER

    def test_types_file_not_store(self):
        assert TSExtractor.classify_file("types.ts") == FileKind.TYPES


# ===========================================================================
# BUG-4 — Scanner must pass rel (full relative path) to classify_file
# ===========================================================================

class TestBug4ScannerPassesRelPath:
    """
    The scanner previously called TSExtractor.classify_file(fname) where
    fname is just the bare filename ('notes.svelte.ts').  Without the
    'stores/' prefix in the path the classifier returned UTIL and the
    file was silently skipped — producing an empty store topology.

    Fix: scanner now calls classify_file(rel) where rel is the full
    relative path from the project root.
    """

    def test_rune_stores_appear_in_project_map(self, rune_store_project):
        """Notes and session stores must be discovered when scanner uses rel."""
        pm = Scanner.scan(rune_store_project)
        store_names = [s.name for s in pm.stores]
        assert "notesStore" in store_names, (
            f"notesStore missing from {store_names}. "
            "Scanner must pass rel path so stores/ dir is detected."
        )
        assert "sessionStore" in store_names, (
            f"sessionStore missing from {store_names}."
        )

    def test_rune_store_kind_in_project_map(self, rune_store_project):
        pm = Scanner.scan(rune_store_project)
        kinds = {s.name: s.kind for s in pm.stores}
        assert "rune" in kinds["notesStore"].lower()
        assert "rune" in kinds["sessionStore"].lower()

    def test_store_topology_not_empty(self, rune_store_project):
        """The store topology must not be an empty dict for a rune-only project."""
        pm = Scanner.scan(rune_store_project)
        assert len(pm.stores) >= 2, (
            "Store topology is empty — scanner dropped .svelte.ts files. "
            "This is the exact symptom of BUG-4."
        )

    def test_classic_and_rune_stores_coexist(self, svelte_project):
        """
        The updated svelte_project fixture has both classic (.ts) and rune
        (.svelte.ts) stores.  Both must appear in the project map.
        """
        pm = Scanner.scan(svelte_project)
        store_names = [s.name for s in pm.stores]
        # Classic stores
        assert "tableStore" in store_names
        assert "authStore" in store_names
        # Rune stores (*.svelte.ts)
        assert "notesStore" in store_names
        assert "sessionStore" in store_names

    def test_svelte_ts_not_treated_as_svelte_component(self, rune_store_project):
        """
        *.svelte.ts files must NOT be parsed as Svelte components —
        they have .ts suffix and must go through the TS path.
        """
        pm = Scanner.scan(rune_store_project)
        comp_names = [c.name for c in pm.components]
        # store files must not end up as components
        assert "notes" not in comp_names, (
            "notes.svelte.ts was incorrectly parsed as a Svelte component."
        )
        assert "sessions" not in comp_names

    def test_rel_path_preserved_in_store_file_field(self, rune_store_project):
        """The store's .file field must contain the full relative path."""
        pm = Scanner.scan(rune_store_project)
        notes = next(s for s in pm.stores if s.name == "notesStore")
        assert "stores" in notes.file, (
            f"Store file path '{notes.file}' must include the 'stores' directory."
        )
        assert notes.file.endswith("notes.svelte.ts")
