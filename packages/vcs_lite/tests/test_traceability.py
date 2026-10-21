"""Traceability tests: the real documents (REQ-VCS-200..207) and the checker itself."""

from __future__ import annotations

from pathlib import Path

import pytest

import traceability as tr

ROOT = Path(__file__).resolve().parents[1]
DOCS, SRC, TESTS = ROOT / "docs", ROOT / "src" / "vcs_lite", ROOT / "tests"

# DEC-VCS-037: before TDD a confirmed AT without a test is only a warning.
# Flip to True when TDD starts; from then on a missing test fails.
TDD_STARTED = True


@pytest.fixture(scope="module")
def corpus() -> tr.Corpus:
    return tr.load_corpus(DOCS, SRC, TESTS)


def _ok(errors: list[str]) -> None:
    assert not errors, "\n" + "\n".join(errors)


# ---------- rules on the real documents ----------

def test_req_vcs_200_each_id_defined_once(corpus):
    _ok(tr.check_200(corpus))


def test_req_vcs_201_references_are_full_and_resolve(corpus):
    _ok(tr.check_201(corpus))


def test_req_vcs_202_forward_req_to_verification_and_design(corpus):
    _ok(tr.check_202(corpus))


def test_req_vcs_203_backward_from_documents(corpus):
    _ok(tr.check_203(corpus))


def test_req_vcs_204_test_names_carry_ids(corpus):
    _ok(tr.check_204(corpus))


def test_req_vcs_205_confirmed_scenarios_have_tests(corpus):
    missing = tr.check_205(corpus)
    if TDD_STARTED:
        _ok(missing)


def test_req_vcs_206_modules_carry_trace(corpus):
    _ok(tr.check_206(corpus))


def test_req_vcs_207_matrix_is_generated(corpus):
    warnings = [] if TDD_STARTED else tr.check_205(corpus)
    text = tr.render_matrix(corpus, warnings)
    target = DOCS / "TRACE.md"
    if not target.exists() or target.read_text(encoding="utf-8") != text:
        target.write_text(text, encoding="utf-8")
    assert "| REQ-VCS-001 |" in target.read_text(encoding="utf-8")


# ---------- the checker on small synthetic documents ----------

SPEC = """\
| REQ-VCS-001 | Stage. | Potwierdzone | DEC-VCS-001 |
| REQ-VCS-002 | Commit. | Potwierdzone | DEC-VCS-001 |
| DEC-VCS-001 | Decyzja. | Źródło |
| VER-VCS-001 | REQ-VCS-002 | test | — |
"""
DESIGN = "| DES-VCS-001 | Moduł. | REQ-VCS-001–002 |\n"
FEATURE = "  @AT_VCS_001 @confirmed @REQ_VCS_001\n  Scenario: Stage\n    Given x\n"


def _corpus(tmp_path, spec=SPEC, design=DESIGN, feature=FEATURE, tests=None, modules=None):
    docs, src, tst = tmp_path / "docs", tmp_path / "src" / "vcs_lite", tmp_path / "tests"
    for d in (docs, src, tst):
        d.mkdir(parents=True)
    (docs / "SPEC.md").write_text(spec, encoding="utf-8")
    (docs / "DESIGN.md").write_text(design, encoding="utf-8")
    (docs / "ACCEPTANCE.feature").write_text(feature, encoding="utf-8")
    for name, body in (tests or {}).items():
        (tst / name).write_text(body, encoding="utf-8")
    for name, body in (modules or {}).items():
        (src / name).write_text(body, encoding="utf-8")
    return tr.load_corpus(docs, src, tst)


def test_req_vcs_201_checker_expands_en_dash_ranges():
    assert tr.expand_refs("REQ-VCS-005–007") == ["REQ-VCS-005", "REQ-VCS-006", "REQ-VCS-007"]


def test_req_vcs_201_checker_rejects_bare_number_lists(tmp_path):
    c = _corpus(tmp_path, design="| DES-VCS-001 | Moduł. | REQ-VCS-001, 002 |\n")
    assert any("skrót niedozwolony" in e for e in tr.check_201(c))


def test_req_vcs_201_checker_reports_undefined_reference(tmp_path):
    c = _corpus(tmp_path, design="| DES-VCS-001 | Moduł. | REQ-VCS-009 |\n")
    assert "odwołanie do niezdefiniowanego REQ-VCS-009 w DESIGN.md" in tr.check_201(c)


def test_req_vcs_200_checker_reports_duplicate_definition(tmp_path):
    c = _corpus(tmp_path, spec=SPEC + "| REQ-VCS-001 | Drugi raz. | x |\n")
    assert tr.check_200(c) == ["REQ-VCS-001 zdefiniowane 2 razy: SPEC.md, SPEC.md"]


def test_req_vcs_202_checker_accepts_full_coverage(tmp_path):
    assert tr.check_202(_corpus(tmp_path)) == []


def test_req_vcs_202_checker_reports_req_without_design(tmp_path):
    c = _corpus(tmp_path, design="| DES-VCS-001 | Moduł. | REQ-VCS-001 |\n")
    assert tr.check_202(c) == ["REQ-VCS-002 nie ma DES (ani wyjątku „bez DES: <powód>”)"]


def test_req_vcs_202_checker_ignores_withdrawn_design(tmp_path):
    c = _corpus(tmp_path, design="| DES-VCS-001 | WYCOFANE. | REQ-VCS-001–002 |\n")
    assert len(tr.check_202(c)) == 2


def test_req_vcs_203_checker_reports_design_without_link(tmp_path):
    c = _corpus(tmp_path, design=DESIGN + "| DES-VCS-002 | Bez powiązań. | sekcja |\n")
    assert tr.check_203(c) == ["DES-VCS-002 nie wskazuje żadnego REQ ani DEC"]


def test_req_vcs_204_checker_rejects_test_without_id(tmp_path):
    c = _corpus(tmp_path, tests={"test_x.py": "def test_something():\n    pass\n"})
    assert tr.check_204(c) == ["test_x.py::test_something nie zaczyna się od ID (np. test_req_vcs_005_…)"]


def test_req_vcs_205_checker_reports_confirmed_scenario_without_test(tmp_path):
    assert tr.check_205(_corpus(tmp_path)) == ["AT-VCS-001 (@confirmed) nie ma testu test_at_vcs_001_…"]
    c = _corpus(tmp_path / "b", tests={"test_a.py": "def test_at_vcs_001_stage():\n    pass\n"})
    assert tr.check_205(c) == []


def test_req_vcs_206_checker_requires_trace_line(tmp_path):
    c = _corpus(tmp_path, modules={"a.py": '"""No trace."""\n', "b.py": '"""Ok.\n\nTrace: DES-VCS-001\n"""\n'})
    assert tr.check_206(c) == ["vcs_lite/a.py: docstring modułu nie ma linii „Trace: …”"]


def test_req_vcs_202_checker_reads_status_only_from_description_start(tmp_path):
    design = "| DES-VCS-001 | Opis wspomina słowo WYCOFANE w środku. | REQ-VCS-001–002 |\n"
    spec = SPEC.replace("| REQ-VCS-002 | Commit. |", "| REQ-VCS-002 | Reguła o wyjątku „bez DES: <powód>”. |")
    assert tr.check_202(_corpus(tmp_path, spec=spec, design=design)) == []
    c = _corpus(tmp_path / "b", spec=spec, design="| DES-VCS-001 | Moduł. | REQ-VCS-001 |\n")
    assert tr.check_202(c) == ["REQ-VCS-002 nie ma DES (ani wyjątku „bez DES: <powód>”)"]


def test_req_vcs_207_matrix_links_tests_through_referenced_ids(tmp_path):
    spec = SPEC.replace("| REQ-VCS-001 | Stage. |", "| REQ-VCS-001 | Stage według T-VCS-01. |") + "## T-VCS-01 — tabela\n\n| a | b |\n"
    c = _corpus(tmp_path, spec=spec, tests={"test_s.py": "def test_t_vcs_01_row():\n    pass\n"})
    assert tr.req_to_tests(c)["REQ-VCS-001"] == {"test_t_vcs_01_row"}


def test_req_vcs_201_checker_resolves_ids_cited_in_the_manual_checklist(tmp_path):
    c = _corpus(tmp_path)
    (tmp_path / "docs" / "MANUAL-UI.md").write_text("| 1 | Krok. | REQ-VCS-001, AT-VCS-009 |\n", encoding="utf-8")
    c = tr.load_corpus(tmp_path / "docs", tmp_path / "src" / "vcs_lite", tmp_path / "tests")
    assert "odwołanie do niezdefiniowanego AT-VCS-009 w MANUAL-UI.md" in tr.check_201(c)
