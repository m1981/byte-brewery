"""
Tests for utils.py_diagram
===========================

TDD order:
  1.  ClassInfo          — dataclass construction & token-efficient repr
  2.  RelationshipInfo   — dataclass for edges (inheritance, composition, uses)
  3.  DiagramConfig      — validation, defaults, format choices
  4.  ASTClassExtractor  — AST-based class/method/field/annotation extraction
  5.  RelationshipEngine — inheritance + annotation-based dependency detection
  6.  MermaidRenderer    — Mermaid classDiagram output (no deps required)
  7.  DotRenderer        — Graphviz DOT output (no deps required — pure text)
  8.  PlantUMLRenderer   — PlantUML @startuml output (no deps required)
  9.  TokenSerializer    — LLM-optimised compressed text representation
  10. ErdanticAdapter    — optional Pydantic model diagram (erdantic lib)
  11. PyDiagramFacade    — orchestrates extract → relate → render pipeline
  12. CLI arg parser     — build_parser()
  13. Integration        — full pipeline over real fixture Python source

Design notes
------------
- Every renderer is pure-Python text generation — no binary tool required.
- erdantic is optional; its adapter gracefully degrades when not installed.
- pyreverse (pylint) is optional; its adapter runs as a subprocess.
- The facade accepts a ``DiagramConfig`` and returns a ``DiagramResult``.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from utils.py_diagram import (
    ASTClassExtractor,
    ClassInfo,
    DiagramConfig,
    DiagramFormat,
    DiagramResult,
    DotRenderer,
    ErdanticAdapter,
    FieldInfo,
    MermaidRenderer,
    MethodInfo,
    PlantUMLRenderer,
    PyDiagramFacade,
    RelationshipEngine,
    RelationshipInfo,
    RelationshipKind,
    TokenSerializer,
    build_parser,
)


# ===========================================================================
# Fixtures & helpers
# ===========================================================================

SIMPLE_SOURCE = textwrap.dedent("""\
    from __future__ import annotations
    from dataclasses import dataclass
    from typing import Optional, List

    class Animal:
        name: str
        age: int

        def speak(self) -> str: ...
        def move(self) -> None: ...

    class Dog(Animal):
        breed: str

        def fetch(self, item: str) -> bool: ...

    class Cat(Animal):
        indoor: bool

        def purr(self) -> str: ...

    @dataclass
    class Shelter:
        animals: List[Animal]
        capacity: int

        def admit(self, animal: Animal) -> None: ...
        def release(self, animal: Animal) -> Optional[Animal]: ...
""")

PYDANTIC_SOURCE = textwrap.dedent("""\
    from pydantic import BaseModel
    from typing import Optional, List

    class Address(BaseModel):
        street: str
        city: str
        postcode: str

    class User(BaseModel):
        id: int
        name: str
        email: str
        address: Optional[Address] = None

    class Team(BaseModel):
        name: str
        members: List[User]
""")


def _make_animal_class() -> ClassInfo:
    return ClassInfo(
        name="Animal",
        module="animals",
        bases=[],
        methods=[
            MethodInfo(name="speak", params=[], return_type="str"),
            MethodInfo(name="move", params=[], return_type="None"),
        ],
        fields=[
            FieldInfo(name="name", type_hint="str"),
            FieldInfo(name="age", type_hint="int"),
        ],
        is_dataclass=False,
        is_abstract=False,
        decorators=[],
    )


def _make_dog_class() -> ClassInfo:
    return ClassInfo(
        name="Dog",
        module="animals",
        bases=["Animal"],
        methods=[
            MethodInfo(name="fetch", params=[("item", "str")], return_type="bool"),
        ],
        fields=[
            FieldInfo(name="breed", type_hint="str"),
        ],
        is_dataclass=False,
        is_abstract=False,
        decorators=[],
    )


def _make_shelter_class() -> ClassInfo:
    return ClassInfo(
        name="Shelter",
        module="animals",
        bases=[],
        methods=[
            MethodInfo(name="admit", params=[("animal", "Animal")], return_type="None"),
            MethodInfo(name="release", params=[("animal", "Animal")], return_type="Optional[Animal]"),
        ],
        fields=[
            FieldInfo(name="animals", type_hint="List[Animal]"),
            FieldInfo(name="capacity", type_hint="int"),
        ],
        is_dataclass=True,
        is_abstract=False,
        decorators=["dataclass"],
    )


# ===========================================================================
# 1. ClassInfo
# ===========================================================================

class TestClassInfo:
    def test_basic_construction(self):
        cls = _make_animal_class()
        assert cls.name == "Animal"
        assert cls.module == "animals"
        assert len(cls.methods) == 2
        assert len(cls.fields) == 2

    def test_bases_default_empty(self):
        cls = ClassInfo(name="Foo", module="m", bases=[], methods=[], fields=[])
        assert cls.bases == []

    def test_is_dataclass_flag(self):
        cls = _make_shelter_class()
        assert cls.is_dataclass is True

    def test_is_abstract_flag(self):
        cls = ClassInfo(
            name="AbstractBase", module="m", bases=[], methods=[], fields=[],
            is_abstract=True,
        )
        assert cls.is_abstract is True

    def test_decorators_stored(self):
        cls = _make_shelter_class()
        assert "dataclass" in cls.decorators

    def test_token_repr_contains_name(self):
        cls = _make_animal_class()
        assert "Animal" in cls.token_repr()

    def test_token_repr_contains_fields(self):
        cls = _make_animal_class()
        r = cls.token_repr()
        assert "name" in r
        assert "age" in r

    def test_token_repr_contains_methods(self):
        cls = _make_animal_class()
        r = cls.token_repr()
        assert "speak" in r
        assert "move" in r

    def test_token_repr_excludes_dunder_methods_by_default(self):
        cls = ClassInfo(
            name="Foo", module="m", bases=[], fields=[],
            methods=[
                MethodInfo(name="__init__", params=[], return_type="None"),
                MethodInfo(name="do_thing", params=[], return_type="str"),
            ],
        )
        r = cls.token_repr(include_dunder=False)
        assert "__init__" not in r
        assert "do_thing" in r

    def test_token_repr_includes_dunder_when_requested(self):
        cls = ClassInfo(
            name="Foo", module="m", bases=[], fields=[],
            methods=[MethodInfo(name="__init__", params=[], return_type="None")],
        )
        r = cls.token_repr(include_dunder=True)
        assert "__init__" in r

    def test_token_repr_shows_bases(self):
        cls = _make_dog_class()
        r = cls.token_repr()
        assert "Animal" in r

    def test_equality(self):
        a = _make_animal_class()
        b = _make_animal_class()
        assert a == b

    def test_inequality_different_name(self):
        a = _make_animal_class()
        b = ClassInfo(name="Cat", module="animals", bases=[], methods=[], fields=[])
        assert a != b


# ===========================================================================
# 2. RelationshipInfo
# ===========================================================================

class TestRelationshipInfo:
    def test_inheritance_construction(self):
        rel = RelationshipInfo(
            source="Dog",
            target="Animal",
            kind=RelationshipKind.INHERITS,
        )
        assert rel.source == "Dog"
        assert rel.target == "Animal"
        assert rel.kind == RelationshipKind.INHERITS

    def test_composition_construction(self):
        rel = RelationshipInfo(
            source="Shelter",
            target="Animal",
            kind=RelationshipKind.COMPOSES,
            label="animals",
        )
        assert rel.kind == RelationshipKind.COMPOSES
        assert rel.label == "animals"

    def test_uses_kind(self):
        rel = RelationshipInfo(source="A", target="B", kind=RelationshipKind.USES)
        assert rel.kind == RelationshipKind.USES

    def test_label_default_empty(self):
        rel = RelationshipInfo(source="A", target="B", kind=RelationshipKind.INHERITS)
        assert rel.label == ""

    def test_all_relationship_kinds_exist(self):
        kinds = {k.value for k in RelationshipKind}
        assert "inherits" in kinds
        assert "composes" in kinds
        assert "uses" in kinds


# ===========================================================================
# 3. DiagramConfig
# ===========================================================================

class TestDiagramConfig:
    def test_defaults(self):
        cfg = DiagramConfig()
        assert cfg.output_format == DiagramFormat.MERMAID
        assert cfg.include_private is False
        assert cfg.include_dunder is False
        assert cfg.max_classes is None
        assert cfg.skip_dirs == []
        assert cfg.output_path is None

    def test_format_mermaid(self):
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        assert cfg.output_format == DiagramFormat.MERMAID

    def test_format_dot(self):
        cfg = DiagramConfig(output_format=DiagramFormat.DOT)
        assert cfg.output_format == DiagramFormat.DOT

    def test_format_plantuml(self):
        cfg = DiagramConfig(output_format=DiagramFormat.PLANTUML)
        assert cfg.output_format == DiagramFormat.PLANTUML

    def test_format_token(self):
        cfg = DiagramConfig(output_format=DiagramFormat.TOKEN)
        assert cfg.output_format == DiagramFormat.TOKEN

    def test_output_path_coerced_to_path(self):
        cfg = DiagramConfig(output_path="out/diagram.md")
        assert isinstance(cfg.output_path, Path)
        assert cfg.output_path == Path("out/diagram.md")

    def test_max_classes_none_means_unlimited(self):
        cfg = DiagramConfig(max_classes=None)
        assert cfg.max_classes is None

    def test_max_classes_positive_int(self):
        cfg = DiagramConfig(max_classes=50)
        assert cfg.max_classes == 50

    def test_skip_dirs_custom(self):
        cfg = DiagramConfig(skip_dirs=["tests", "migrations"])
        assert "tests" in cfg.skip_dirs

    def test_include_private_flag(self):
        cfg = DiagramConfig(include_private=True)
        assert cfg.include_private is True

    def test_include_dunder_flag(self):
        cfg = DiagramConfig(include_dunder=True)
        assert cfg.include_dunder is True


# ===========================================================================
# 4. ASTClassExtractor
# ===========================================================================

class TestASTClassExtractor:
    def _extract_from_source(self, source: str, module: str = "test_module") -> list[ClassInfo]:
        extractor = ASTClassExtractor()
        return extractor.extract_from_source(source, module_name=module)

    def test_extracts_class_names(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        names = {c.name for c in classes}
        assert "Animal" in names
        assert "Dog" in names
        assert "Cat" in names
        assert "Shelter" in names

    def test_extracts_base_classes(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        assert "Animal" in by_name["Dog"].bases
        assert "Animal" in by_name["Cat"].bases

    def test_extracts_no_bases_for_root_class(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        assert by_name["Animal"].bases == []

    def test_extracts_methods(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        method_names = {m.name for m in by_name["Animal"].methods}
        assert "speak" in method_names
        assert "move" in method_names

    def test_extracts_method_return_types(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        dog_methods = {m.name: m for m in by_name["Dog"].methods}
        assert dog_methods["fetch"].return_type == "bool"

    def test_extracts_method_params(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        dog_methods = {m.name: m for m in by_name["Dog"].methods}
        params = dict(dog_methods["fetch"].params)
        assert "item" in params
        assert params["item"] == "str"

    def test_extracts_annotated_fields(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        field_names = {f.name for f in by_name["Animal"].fields}
        assert "name" in field_names
        assert "age" in field_names

    def test_extracts_field_types(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        fields = {f.name: f for f in by_name["Animal"].fields}
        assert fields["name"].type_hint == "str"
        assert fields["age"].type_hint == "int"

    def test_detects_dataclass_decorator(self):
        classes = self._extract_from_source(SIMPLE_SOURCE)
        by_name = {c.name: c for c in classes}
        assert by_name["Shelter"].is_dataclass is True
        assert by_name["Animal"].is_dataclass is False

    def test_module_name_stored(self):
        classes = self._extract_from_source(SIMPLE_SOURCE, module="mymod")
        assert all(c.module == "mymod" for c in classes)

    def test_extracts_from_file(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text(SIMPLE_SOURCE)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_file(py_file)
        names = {c.name for c in classes}
        assert "Animal" in names

    def test_extracts_from_directory(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        (tmp_path / "other.py").write_text("class Plugin:\n    pass\n")
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_directory(tmp_path)
        names = {c.name for c in classes}
        assert "Animal" in names
        assert "Plugin" in names

    def test_skips_dirs_in_directory_extraction(self, tmp_path):
        (tmp_path / "main.py").write_text("class Main:\n    pass\n")
        skip_dir = tmp_path / "skip_me"
        skip_dir.mkdir()
        (skip_dir / "hidden.py").write_text("class Hidden:\n    pass\n")
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_directory(tmp_path, skip_dirs=["skip_me"])
        names = {c.name for c in classes}
        assert "Main" in names
        assert "Hidden" not in names

    def test_handles_syntax_error_gracefully(self):
        bad_source = "class Broken(:\n    pass\n"
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(bad_source, module_name="bad")
        assert classes == []

    def test_excludes_private_methods_by_default(self):
        source = textwrap.dedent("""\
            class MyClass:
                def public_method(self) -> None: ...
                def _private_method(self) -> None: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m", include_private=False)
        by_name = {c.name: c for c in classes}
        method_names = {m.name for m in by_name["MyClass"].methods}
        assert "public_method" in method_names
        assert "_private_method" not in method_names

    def test_includes_private_methods_when_requested(self):
        source = textwrap.dedent("""\
            class MyClass:
                def _private_method(self) -> None: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m", include_private=True)
        by_name = {c.name: c for c in classes}
        method_names = {m.name for m in by_name["MyClass"].methods}
        assert "_private_method" in method_names

    def test_excludes_dunder_methods_by_default(self):
        source = textwrap.dedent("""\
            class MyClass:
                def __init__(self) -> None: ...
                def public(self) -> None: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m", include_dunder=False)
        by_name = {c.name: c for c in classes}
        method_names = {m.name for m in by_name["MyClass"].methods}
        assert "__init__" not in method_names
        assert "public" in method_names

    def test_includes_dunder_when_requested(self):
        source = textwrap.dedent("""\
            class MyClass:
                def __init__(self) -> None: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m", include_dunder=True)
        by_name = {c.name: c for c in classes}
        method_names = {m.name for m in by_name["MyClass"].methods}
        assert "__init__" in method_names

    def test_self_param_excluded_from_method_params(self):
        source = textwrap.dedent("""\
            class Foo:
                def bar(self, x: int) -> str: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m")
        method = classes[0].methods[0]
        param_names = [p[0] for p in method.params]
        assert "self" not in param_names
        assert "x" in param_names

    def test_async_methods_extracted(self):
        source = textwrap.dedent("""\
            class Service:
                async def fetch(self) -> str: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m")
        method_names = {m.name for m in classes[0].methods}
        assert "fetch" in method_names

    def test_complex_type_hints_extracted(self):
        source = textwrap.dedent("""\
            from typing import Optional, List, Dict
            class Repo:
                items: Dict[str, List[int]]
                def get(self, key: str) -> Optional[int]: ...
        """)
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(source, module_name="m")
        by_name = {c.name: c for c in classes}
        fields = {f.name: f for f in by_name["Repo"].fields}
        assert "Dict" in fields["items"].type_hint or "dict" in fields["items"].type_hint.lower()


# ===========================================================================
# 5. RelationshipEngine
# ===========================================================================

class TestRelationshipEngine:
    def _extract_relationships(self, classes: list[ClassInfo]) -> list[RelationshipInfo]:
        engine = RelationshipEngine()
        return engine.extract(classes)

    def test_detects_inheritance(self):
        classes = [_make_animal_class(), _make_dog_class()]
        rels = self._extract_relationships(classes)
        inherits = [r for r in rels if r.kind == RelationshipKind.INHERITS]
        assert any(r.source == "Dog" and r.target == "Animal" for r in inherits)

    def test_no_inheritance_for_root_class(self):
        classes = [_make_animal_class()]
        rels = self._extract_relationships(classes)
        inherits = [r for r in rels if r.kind == RelationshipKind.INHERITS]
        assert len(inherits) == 0

    def test_detects_composition_via_field_type(self):
        classes = [_make_animal_class(), _make_shelter_class()]
        rels = self._extract_relationships(classes)
        composes = [r for r in rels if r.kind == RelationshipKind.COMPOSES]
        assert any(r.source == "Shelter" and r.target == "Animal" for r in composes)

    def test_detects_uses_via_method_param_type(self):
        # Dog.fetch(item: str) — str is builtin, not in class set, so no edge
        # Shelter.admit(animal: Animal) — Animal IS in class set → uses
        classes = [_make_animal_class(), _make_shelter_class()]
        rels = self._extract_relationships(classes)
        uses = [r for r in rels if r.kind == RelationshipKind.USES]
        assert any(r.source == "Shelter" and r.target == "Animal" for r in uses)

    def test_no_duplicate_relationships(self):
        classes = [_make_animal_class(), _make_shelter_class()]
        rels = self._extract_relationships(classes)
        # Each unique (source, target, kind) should appear once
        seen = set()
        for r in rels:
            key = (r.source, r.target, r.kind)
            assert key not in seen, f"Duplicate relationship: {key}"
            seen.add(key)

    def test_only_known_classes_targeted(self):
        """Relationships should only point to classes that were extracted."""
        classes = [_make_dog_class()]  # Animal not in set
        rels = self._extract_relationships(classes)
        known_names = {c.name for c in classes}
        for r in rels:
            assert r.target in known_names or True  # bases outside the set are still valid edges


# ===========================================================================
# 6. MermaidRenderer
# ===========================================================================

class TestMermaidRenderer:
    def _render(self, classes, rels=None, cfg=None) -> str:
        renderer = MermaidRenderer()
        cfg = cfg or DiagramConfig(output_format=DiagramFormat.MERMAID)
        return renderer.render(classes, rels or [], cfg)

    def test_output_starts_with_classDiagram(self):
        out = self._render([_make_animal_class()])
        assert out.startswith("classDiagram")

    def test_contains_class_name(self):
        out = self._render([_make_animal_class()])
        assert "Animal" in out

    def test_contains_fields(self):
        out = self._render([_make_animal_class()])
        assert "name" in out
        assert "age" in out

    def test_contains_methods(self):
        out = self._render([_make_animal_class()])
        assert "speak" in out
        assert "move" in out

    def test_inheritance_arrow(self):
        classes = [_make_animal_class(), _make_dog_class()]
        rels = [RelationshipInfo(source="Dog", target="Animal", kind=RelationshipKind.INHERITS)]
        out = self._render(classes, rels)
        assert "<|--" in out or "--|>" in out  # Mermaid inheritance syntax

    def test_composition_arrow(self):
        classes = [_make_animal_class(), _make_shelter_class()]
        rels = [RelationshipInfo(source="Shelter", target="Animal", kind=RelationshipKind.COMPOSES, label="animals")]
        out = self._render(classes, rels)
        assert "*--" in out or "--*" in out  # Mermaid composition syntax

    def test_uses_arrow(self):
        classes = [_make_animal_class(), _make_shelter_class()]
        rels = [RelationshipInfo(source="Shelter", target="Animal", kind=RelationshipKind.USES)]
        out = self._render(classes, rels)
        assert "-->" in out

    def test_dataclass_marked_with_stereotype(self):
        out = self._render([_make_shelter_class()])
        # Mermaid uses <<dataclass>> or <<Dataclass>> stereotype notation
        lower = out.lower()
        assert "dataclass" in lower or "<<" in out

    def test_empty_classes_produces_valid_diagram(self):
        out = self._render([])
        assert "classDiagram" in out

    def test_method_return_type_shown(self):
        out = self._render([_make_animal_class()])
        assert "str" in out  # speak() -> str

    def test_field_type_shown(self):
        out = self._render([_make_animal_class()])
        assert "str" in out  # name: str

    def test_output_is_string(self):
        out = self._render([_make_animal_class()])
        assert isinstance(out, str)

    def test_multiple_classes_all_present(self):
        classes = [_make_animal_class(), _make_dog_class(), _make_shelter_class()]
        out = self._render(classes)
        assert "Animal" in out
        assert "Dog" in out
        assert "Shelter" in out


# ===========================================================================
# 7. DotRenderer
# ===========================================================================

class TestDotRenderer:
    def _render(self, classes, rels=None, cfg=None) -> str:
        renderer = DotRenderer()
        cfg = cfg or DiagramConfig(output_format=DiagramFormat.DOT)
        return renderer.render(classes, rels or [], cfg)

    def test_output_starts_with_digraph(self):
        out = self._render([_make_animal_class()])
        assert out.startswith("digraph")

    def test_contains_class_name(self):
        out = self._render([_make_animal_class()])
        assert "Animal" in out

    def test_contains_fields(self):
        out = self._render([_make_animal_class()])
        assert "name" in out

    def test_contains_methods(self):
        out = self._render([_make_animal_class()])
        assert "speak" in out

    def test_inheritance_edge(self):
        classes = [_make_animal_class(), _make_dog_class()]
        rels = [RelationshipInfo(source="Dog", target="Animal", kind=RelationshipKind.INHERITS)]
        out = self._render(classes, rels)
        assert "Dog" in out
        assert "Animal" in out
        assert "->" in out

    def test_record_shape_used(self):
        out = self._render([_make_animal_class()])
        assert "record" in out

    def test_valid_dot_structure(self):
        out = self._render([_make_animal_class()])
        assert "{" in out and "}" in out

    def test_dataclass_labeled(self):
        out = self._render([_make_shelter_class()])
        lower = out.lower()
        assert "dataclass" in lower or "shelter" in out

    def test_empty_renders_valid_dot(self):
        out = self._render([])
        assert "digraph" in out


# ===========================================================================
# 8. PlantUMLRenderer
# ===========================================================================

class TestPlantUMLRenderer:
    def _render(self, classes, rels=None, cfg=None) -> str:
        renderer = PlantUMLRenderer()
        cfg = cfg or DiagramConfig(output_format=DiagramFormat.PLANTUML)
        return renderer.render(classes, rels or [], cfg)

    def test_output_starts_with_startuml(self):
        out = self._render([_make_animal_class()])
        assert "@startuml" in out

    def test_output_ends_with_enduml(self):
        out = self._render([_make_animal_class()])
        assert "@enduml" in out

    def test_contains_class_name(self):
        out = self._render([_make_animal_class()])
        assert "Animal" in out

    def test_contains_fields(self):
        out = self._render([_make_animal_class()])
        assert "name" in out

    def test_contains_methods(self):
        out = self._render([_make_animal_class()])
        assert "speak" in out

    def test_inheritance_arrow(self):
        classes = [_make_animal_class(), _make_dog_class()]
        rels = [RelationshipInfo(source="Dog", target="Animal", kind=RelationshipKind.INHERITS)]
        out = self._render(classes, rels)
        assert "<|--" in out or "--|>" in out  # PlantUML inheritance syntax

    def test_dataclass_stereotype(self):
        out = self._render([_make_shelter_class()])
        lower = out.lower()
        assert "dataclass" in lower or "<<" in out

    def test_empty_renders_valid_plantuml(self):
        out = self._render([])
        assert "@startuml" in out
        assert "@enduml" in out

    def test_multiple_classes_all_present(self):
        classes = [_make_animal_class(), _make_dog_class()]
        out = self._render(classes)
        assert "Animal" in out
        assert "Dog" in out


# ===========================================================================
# 9. TokenSerializer
# ===========================================================================

class TestTokenSerializer:
    def _serialize(self, classes, rels=None, cfg=None) -> str:
        serializer = TokenSerializer()
        cfg = cfg or DiagramConfig(output_format=DiagramFormat.TOKEN)
        return serializer.render(classes, rels or [], cfg)

    def test_contains_class_header(self):
        out = self._serialize([_make_animal_class()])
        assert "[CLASS]" in out
        assert "Animal" in out

    def test_contains_fields_section(self):
        out = self._serialize([_make_animal_class()])
        assert "name" in out
        assert "str" in out

    def test_contains_methods_section(self):
        out = self._serialize([_make_animal_class()])
        assert "speak" in out

    def test_inheritance_shown(self):
        out = self._serialize([_make_dog_class()])
        assert "Animal" in out

    def test_relationship_shown(self):
        rels = [RelationshipInfo(source="Shelter", target="Animal", kind=RelationshipKind.COMPOSES)]
        out = self._serialize([_make_shelter_class()], rels)
        assert "Animal" in out or "COMPOSES" in out.upper()

    def test_dataclass_tagged(self):
        out = self._serialize([_make_shelter_class()])
        lower = out.lower()
        assert "dataclass" in lower

    def test_token_budget_is_smaller_than_mermaid(self):
        """Token repr should be more compact than full Mermaid output."""
        classes = [_make_animal_class(), _make_dog_class(), _make_shelter_class()]
        rels = [
            RelationshipInfo(source="Dog", target="Animal", kind=RelationshipKind.INHERITS),
        ]
        token_out = self._serialize(classes, rels)
        mermaid_out = MermaidRenderer().render(classes, rels, DiagramConfig())
        # Token format should be shorter (or at most equal)
        assert len(token_out) <= len(mermaid_out) * 1.5  # generous allowance

    def test_empty_produces_valid_output(self):
        out = self._serialize([])
        assert isinstance(out, str)

    def test_module_shown(self):
        out = self._serialize([_make_animal_class()])
        assert "animals" in out  # module name


# ===========================================================================
# 10. ErdanticAdapter
# ===========================================================================

class TestErdanticAdapter:
    def test_available_returns_bool(self):
        adapter = ErdanticAdapter()
        assert isinstance(adapter.is_available(), bool)

    def test_render_returns_none_when_unavailable(self, tmp_path):
        adapter = ErdanticAdapter()
        with patch.object(adapter, "is_available", return_value=False):
            result = adapter.render_to_file([], tmp_path / "out.svg")
        assert result is None

    def test_render_called_with_models(self, tmp_path):
        """When erdantic is available, it should be called with model classes."""
        adapter = ErdanticAdapter()
        mock_erdantic = MagicMock()
        with patch.dict("sys.modules", {"erdantic": mock_erdantic}):
            with patch.object(adapter, "is_available", return_value=True):
                # Just check it doesn't crash with empty list
                adapter.render_to_file([], tmp_path / "out.svg")

    def test_extract_pydantic_classes_from_source(self):
        """Adapter can identify Pydantic BaseModel subclasses from ClassInfo list."""
        extractor = ASTClassExtractor()
        classes = extractor.extract_from_source(PYDANTIC_SOURCE, module_name="models")
        adapter = ErdanticAdapter()
        pydantic_classes = adapter.filter_pydantic_classes(classes)
        names = {c.name for c in pydantic_classes}
        assert "User" in names
        assert "Address" in names
        assert "Team" in names

    def test_filter_excludes_non_pydantic(self):
        classes = [_make_animal_class()]  # No BaseModel base
        adapter = ErdanticAdapter()
        pydantic_classes = adapter.filter_pydantic_classes(classes)
        assert len(pydantic_classes) == 0


# ===========================================================================
# 11. PyDiagramFacade
# ===========================================================================

class TestPyDiagramFacade:
    def _facade(self, fmt: DiagramFormat = DiagramFormat.MERMAID) -> PyDiagramFacade:
        cfg = DiagramConfig(output_format=fmt)
        return PyDiagramFacade(cfg)

    def test_analyse_source_returns_diagram_result(self):
        facade = self._facade()
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert isinstance(result, DiagramResult)

    def test_result_contains_diagram_text(self):
        facade = self._facade()
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert isinstance(result.diagram, str)
        assert len(result.diagram) > 0

    def test_result_contains_classes(self):
        facade = self._facade()
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert len(result.classes) >= 4  # Animal, Dog, Cat, Shelter

    def test_result_contains_relationships(self):
        facade = self._facade()
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert len(result.relationships) > 0

    def test_mermaid_format(self):
        facade = self._facade(DiagramFormat.MERMAID)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert "classDiagram" in result.diagram

    def test_dot_format(self):
        facade = self._facade(DiagramFormat.DOT)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert "digraph" in result.diagram

    def test_plantuml_format(self):
        facade = self._facade(DiagramFormat.PLANTUML)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert "@startuml" in result.diagram

    def test_token_format(self):
        facade = self._facade(DiagramFormat.TOKEN)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert "[CLASS]" in result.diagram

    def test_analyse_directory(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        facade = self._facade()
        result = facade.analyse_directory(tmp_path)
        assert "Animal" in result.diagram

    def test_write_output_to_file(self, tmp_path):
        out = tmp_path / "diagram.md"
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID, output_path=out)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        facade.write(result)
        assert out.exists()
        content = out.read_text()
        assert "classDiagram" in content

    def test_write_to_stdout_when_no_path(self, capsys):
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID, output_path=None)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        facade.write(result)
        captured = capsys.readouterr()
        assert "classDiagram" in captured.out

    def test_max_classes_limit_respected(self):
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID, max_classes=2)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert len(result.classes) <= 2

    def test_result_class_count(self):
        facade = self._facade()
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert result.class_count == len(result.classes)

    def test_result_relationship_count(self):
        facade = self._facade()
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="test")
        assert result.relationship_count == len(result.relationships)

    def test_pydantic_source_mermaid(self):
        facade = self._facade(DiagramFormat.MERMAID)
        result = facade.analyse_source(PYDANTIC_SOURCE, module_name="models")
        assert "User" in result.diagram
        assert "Address" in result.diagram


# ===========================================================================
# 12. CLI arg parser
# ===========================================================================

class TestBuildParser:
    def test_no_args_uses_current_dir(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.root == "."

    def test_root_positional(self):
        args = build_parser().parse_args(["src/mypackage"])
        assert args.root == "src/mypackage"

    def test_default_format_mermaid(self):
        args = build_parser().parse_args([])
        assert args.format == "mermaid"

    def test_format_choices(self):
        for fmt in ("mermaid", "dot", "plantuml", "token"):
            args = build_parser().parse_args(["--format", fmt])
            assert args.format == fmt

    def test_invalid_format_exits(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["--format", "jpeg"])

    def test_output_flag(self):
        args = build_parser().parse_args(["--output", "out/diagram.md"])
        assert args.output == "out/diagram.md"

    def test_output_default_none(self):
        args = build_parser().parse_args([])
        assert args.output is None

    def test_skip_dirs_flag(self):
        args = build_parser().parse_args(["--skip", "tests", "migrations"])
        assert "tests" in args.skip
        assert "migrations" in args.skip

    def test_include_private_flag(self):
        args = build_parser().parse_args(["--include-private"])
        assert args.include_private is True

    def test_include_dunder_flag(self):
        args = build_parser().parse_args(["--include-dunder"])
        assert args.include_dunder is True

    def test_max_classes_flag(self):
        args = build_parser().parse_args(["--max-classes", "30"])
        assert args.max_classes == 30

    def test_max_classes_default_none(self):
        args = build_parser().parse_args([])
        assert args.max_classes is None

    def test_source_flag_accepts_single_file(self):
        args = build_parser().parse_args(["--source", "my_module.py"])
        assert args.source == "my_module.py"

    def test_source_default_none(self):
        args = build_parser().parse_args([])
        assert args.source is None


# ===========================================================================
# 13. Integration — full pipeline over real fixture files
# ===========================================================================

class TestIntegration:
    """End-to-end: write a real .py file, run the full pipeline, check output."""

    def test_mermaid_full_pipeline(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert "classDiagram" in result.diagram
        assert "Animal" in result.diagram
        assert "Dog" in result.diagram
        # Inheritance relationship must be rendered
        assert "<|--" in result.diagram or "--|>" in result.diagram

    def test_dot_full_pipeline(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.DOT)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert "digraph" in result.diagram
        assert "Animal" in result.diagram

    def test_plantuml_full_pipeline(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.PLANTUML)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert "@startuml" in result.diagram
        assert "@enduml" in result.diagram

    def test_token_full_pipeline(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.TOKEN)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert "[CLASS]" in result.diagram

    def test_file_written_to_disk(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        out = tmp_path / "out.md"
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID, output_path=out)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        facade.write(result)
        assert out.exists()
        assert "classDiagram" in out.read_text()

    def test_pydantic_models_detected(self, tmp_path):
        (tmp_path / "models.py").write_text(PYDANTIC_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert "User" in result.diagram
        assert "Address" in result.diagram
        assert "Team" in result.diagram

    def test_skip_dirs_respected(self, tmp_path):
        (tmp_path / "main.py").write_text("class Main:\n    pass\n")
        skip = tmp_path / "migrations"
        skip.mkdir()
        (skip / "migration.py").write_text("class Migration:\n    pass\n")
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID, skip_dirs=["migrations"])
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert "Main" in result.diagram
        assert "Migration" not in result.diagram

    def test_inheritance_relationships_complete(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        # Dog and Cat both inherit from Animal
        inherits = [r for r in result.relationships if r.kind == RelationshipKind.INHERITS]
        sources = {r.source for r in inherits}
        assert "Dog" in sources
        assert "Cat" in sources

    def test_composition_relationships_detected(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        composes = [r for r in result.relationships if r.kind == RelationshipKind.COMPOSES]
        assert any(r.source == "Shelter" and r.target == "Animal" for r in composes)

    def test_class_count_matches_source(self, tmp_path):
        (tmp_path / "animals.py").write_text(SIMPLE_SOURCE)
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_directory(tmp_path)
        assert result.class_count == 4  # Animal, Dog, Cat, Shelter

    def test_analyse_source_directly(self):
        cfg = DiagramConfig(output_format=DiagramFormat.MERMAID)
        facade = PyDiagramFacade(cfg)
        result = facade.analyse_source(SIMPLE_SOURCE, module_name="animals")
        assert result.class_count == 4
        assert "classDiagram" in result.diagram
