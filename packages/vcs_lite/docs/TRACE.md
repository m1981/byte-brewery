# vcs-lite — macierz śledzenia powiązań

Plik generowany przez `tests/test_traceability.py` (REQ-VCS-207). Nie edytować ręcznie.

## Wymaganie → projekt, scenariusze, weryfikacja, testy, kod

| REQ | DES | AT | VER | Testy | Moduły |
|---|---|---|---|---|---|
| REQ-VCS-001 | DES-VCS-019 | AT-VCS-001, AT-VCS-018, AT-VCS-022 | VER-VCS-005, VER-VCS-008, VER-VCS-010 | — | — |
| REQ-VCS-002 | DES-VCS-018, DES-VCS-023 | — | VER-VCS-012 | — | — |
| REQ-VCS-003 | DES-VCS-005, DES-VCS-006, DES-VCS-024 | AT-VCS-003, AT-VCS-004, AT-VCS-005 | VER-VCS-001 | — | — |
| REQ-VCS-004 | DES-VCS-005 | AT-VCS-006 | VER-VCS-001 | — | — |
| REQ-VCS-005 | DES-VCS-011, DES-VCS-012, DES-VCS-024 | AT-VCS-008, AT-VCS-009, AT-VCS-029 | VER-VCS-002 | — | — |
| REQ-VCS-006 (zastąpione) | — | — | — | — | — |
| REQ-VCS-007 | DES-VCS-008 | AT-VCS-007 | VER-VCS-001 | — | — |
| REQ-VCS-008 | DES-VCS-001 | — | VER-VCS-001 | — | — |
| REQ-VCS-009 | DES-VCS-013, DES-VCS-026 | AT-VCS-010, AT-VCS-011 | VER-VCS-003 | — | — |
| REQ-VCS-010 | DES-VCS-001, DES-VCS-013 | AT-VCS-012 | VER-VCS-003 | — | — |
| REQ-VCS-011 | DES-VCS-014 | AT-VCS-013 | VER-VCS-004 | — | — |
| REQ-VCS-012 | DES-VCS-014 | AT-VCS-014 | VER-VCS-004 | — | — |
| REQ-VCS-013 | DES-VCS-014 | — | VER-VCS-004 | — | — |
| REQ-VCS-014 | DES-VCS-002, DES-VCS-003, DES-VCS-004 | AT-VCS-015 | VER-VCS-004 | — | — |
| REQ-VCS-015 | DES-VCS-018 | — | VER-VCS-012 | — | — |
| REQ-VCS-016 | DES-VCS-016 | — | VER-VCS-012 | — | — |
| REQ-VCS-017 | DES-VCS-002, DES-VCS-019, DES-VCS-038 | AT-VCS-017, AT-VCS-027 | VER-VCS-007 | — | — |
| REQ-VCS-018 | DES-VCS-023 | AT-VCS-002 | VER-VCS-005 | — | — |
| REQ-VCS-019 | DES-VCS-006 | — | VER-VCS-001 | — | — |
| REQ-VCS-020 | DES-VCS-015 | AT-VCS-020, AT-VCS-021 | VER-VCS-009 | — | — |
| REQ-VCS-021 | DES-VCS-026 | AT-VCS-019 | VER-VCS-008, VER-VCS-012 | — | — |
| REQ-VCS-022 | DES-VCS-021, DES-VCS-026 | AT-VCS-023, AT-VCS-024 | VER-VCS-010 | — | — |
| REQ-VCS-023 | DES-VCS-007, DES-VCS-036, DES-VCS-037, DES-VCS-038, DES-VCS-039 | AT-VCS-004, AT-VCS-025, AT-VCS-026, AT-VCS-027, AT-VCS-028, AT-VCS-029 | VER-VCS-011 | — | — |
| REQ-VCS-100 | DES-VCS-008, DES-VCS-034 | AT-VCS-016 | VER-VCS-006 | — | — |
| REQ-VCS-101 | DES-VCS-017, DES-VCS-035 | — | VER-VCS-006 | — | — |
| REQ-VCS-102 | DES-VCS-034 | — | VER-VCS-006 | — | — |
| REQ-VCS-103 | DES-VCS-028, DES-VCS-029 | — | VER-VCS-013 | — | — |
| REQ-VCS-200 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_200_checker_reports_duplicate_definition, test_req_vcs_200_each_id_defined_once | — |
| REQ-VCS-201 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_201_checker_expands_en_dash_ranges, test_req_vcs_201_checker_rejects_bare_number_lists, test_req_vcs_201_checker_reports_undefined_reference, test_req_vcs_201_references_are_full_and_resolve | — |
| REQ-VCS-202 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_202_checker_accepts_full_coverage, test_req_vcs_202_checker_ignores_withdrawn_design, test_req_vcs_202_checker_reads_status_only_from_description_start, test_req_vcs_202_checker_reports_req_without_design, test_req_vcs_202_forward_req_to_verification_and_design | — |
| REQ-VCS-203 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_203_backward_from_documents, test_req_vcs_203_checker_reports_design_without_link | — |
| REQ-VCS-204 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_204_checker_rejects_test_without_id, test_req_vcs_204_test_names_carry_ids | — |
| REQ-VCS-205 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_205_checker_reports_confirmed_scenario_without_test, test_req_vcs_205_confirmed_scenarios_have_tests | — |
| REQ-VCS-206 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_206_checker_requires_trace_line, test_req_vcs_206_modules_carry_trace | — |
| REQ-VCS-207 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_207_matrix_is_generated | — |

## Wstecz: scenariusz → wymagania

| AT | Status | REQ |
|---|---|---|
| AT-VCS-001 | confirmed | REQ-VCS-001 |
| AT-VCS-002 | confirmed | REQ-VCS-018 |
| AT-VCS-003 | confirmed | REQ-VCS-003 |
| AT-VCS-004 | confirmed | REQ-VCS-003, REQ-VCS-023 |
| AT-VCS-005 | confirmed | REQ-VCS-003 |
| AT-VCS-006 | confirmed | REQ-VCS-004 |
| AT-VCS-007 | dormant | REQ-VCS-007 |
| AT-VCS-008 | confirmed | REQ-VCS-005 |
| AT-VCS-009 | confirmed | REQ-VCS-005 |
| AT-VCS-010 | confirmed | REQ-VCS-009 |
| AT-VCS-011 | confirmed | REQ-VCS-009 |
| AT-VCS-012 | confirmed | REQ-VCS-010 |
| AT-VCS-013 | confirmed | REQ-VCS-011 |
| AT-VCS-014 | confirmed | REQ-VCS-012 |
| AT-VCS-015 | confirmed | REQ-VCS-014 |
| AT-VCS-016 | confirmed | REQ-VCS-100 |
| AT-VCS-017 | confirmed | REQ-VCS-017 |
| AT-VCS-018 | confirmed | REQ-VCS-001 |
| AT-VCS-019 | confirmed | REQ-VCS-021 |
| AT-VCS-020 | confirmed | REQ-VCS-020 |
| AT-VCS-021 | confirmed | REQ-VCS-020 |
| AT-VCS-022 | confirmed | REQ-VCS-001 |
| AT-VCS-023 | confirmed | REQ-VCS-022 |
| AT-VCS-024 | confirmed | REQ-VCS-022 |
| AT-VCS-025 | confirmed | REQ-VCS-023 |
| AT-VCS-026 | confirmed | REQ-VCS-023 |
| AT-VCS-027 | confirmed | REQ-VCS-017, REQ-VCS-023 |
| AT-VCS-028 | confirmed | REQ-VCS-023 |
| AT-VCS-029 | confirmed | REQ-VCS-005, REQ-VCS-023 |

## Wstecz: decyzja projektowa → wymagania

| DES | REQ |
|---|---|
| DES-VCS-001 | REQ-VCS-008, REQ-VCS-010 |
| DES-VCS-002 | REQ-VCS-014, REQ-VCS-017 |
| DES-VCS-003 | REQ-VCS-014 |
| DES-VCS-004 | REQ-VCS-014 |
| DES-VCS-005 | REQ-VCS-003, REQ-VCS-004 |
| DES-VCS-006 | REQ-VCS-003, REQ-VCS-019 |
| DES-VCS-007 | REQ-VCS-023 |
| DES-VCS-008 | REQ-VCS-007, REQ-VCS-100 |
| DES-VCS-009 (wycofane) | REQ-VCS-006 |
| DES-VCS-010 (wycofane) | REQ-VCS-006 |
| DES-VCS-011 | REQ-VCS-005 |
| DES-VCS-012 | REQ-VCS-005 |
| DES-VCS-013 | REQ-VCS-009, REQ-VCS-010 |
| DES-VCS-014 | REQ-VCS-011, REQ-VCS-012, REQ-VCS-013 |
| DES-VCS-015 | REQ-VCS-020 |
| DES-VCS-016 | REQ-VCS-016 |
| DES-VCS-017 | REQ-VCS-101 |
| DES-VCS-018 | REQ-VCS-002, REQ-VCS-015 |
| DES-VCS-019 | REQ-VCS-001, REQ-VCS-017 |
| DES-VCS-020 | — |
| DES-VCS-021 | REQ-VCS-022 |
| DES-VCS-022 | — |
| DES-VCS-023 | REQ-VCS-002, REQ-VCS-018 |
| DES-VCS-024 | REQ-VCS-003, REQ-VCS-005 |
| DES-VCS-025 (wycofane) | REQ-VCS-006 |
| DES-VCS-026 | REQ-VCS-009, REQ-VCS-021, REQ-VCS-022 |
| DES-VCS-027 (wycofane) | — |
| DES-VCS-028 | REQ-VCS-103 |
| DES-VCS-029 | REQ-VCS-103 |
| DES-VCS-030 | — |
| DES-VCS-031 | — |
| DES-VCS-032 | — |
| DES-VCS-033 | — |
| DES-VCS-034 | REQ-VCS-100, REQ-VCS-102 |
| DES-VCS-035 | REQ-VCS-101 |
| DES-VCS-036 | REQ-VCS-023 |
| DES-VCS-037 | REQ-VCS-023 |
| DES-VCS-038 | REQ-VCS-017, REQ-VCS-023 |
| DES-VCS-039 | REQ-VCS-023 |
| DES-VCS-040 | REQ-VCS-200, REQ-VCS-201, REQ-VCS-202, REQ-VCS-203, REQ-VCS-204, REQ-VCS-205, REQ-VCS-206, REQ-VCS-207 |

## Wstecz: test → ID

| Test | Plik | ID |
|---|---|---|
| `test_req_vcs_200_checker_reports_duplicate_definition` | test_traceability.py | REQ-VCS-200 |
| `test_req_vcs_200_each_id_defined_once` | test_traceability.py | REQ-VCS-200 |
| `test_req_vcs_201_checker_expands_en_dash_ranges` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_201_checker_rejects_bare_number_lists` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_201_checker_reports_undefined_reference` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_201_references_are_full_and_resolve` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_202_checker_accepts_full_coverage` | test_traceability.py | REQ-VCS-202 |
| `test_req_vcs_202_checker_ignores_withdrawn_design` | test_traceability.py | REQ-VCS-202 |
| `test_req_vcs_202_checker_reads_status_only_from_description_start` | test_traceability.py | REQ-VCS-202 |
| `test_req_vcs_202_checker_reports_req_without_design` | test_traceability.py | REQ-VCS-202 |
| `test_req_vcs_202_forward_req_to_verification_and_design` | test_traceability.py | REQ-VCS-202 |
| `test_req_vcs_203_backward_from_documents` | test_traceability.py | REQ-VCS-203 |
| `test_req_vcs_203_checker_reports_design_without_link` | test_traceability.py | REQ-VCS-203 |
| `test_req_vcs_204_checker_rejects_test_without_id` | test_traceability.py | REQ-VCS-204 |
| `test_req_vcs_204_test_names_carry_ids` | test_traceability.py | REQ-VCS-204 |
| `test_req_vcs_205_checker_reports_confirmed_scenario_without_test` | test_traceability.py | REQ-VCS-205 |
| `test_req_vcs_205_confirmed_scenarios_have_tests` | test_traceability.py | REQ-VCS-205 |
| `test_req_vcs_206_checker_requires_trace_line` | test_traceability.py | REQ-VCS-206 |
| `test_req_vcs_206_modules_carry_trace` | test_traceability.py | REQ-VCS-206 |
| `test_req_vcs_207_matrix_is_generated` | test_traceability.py | REQ-VCS-207 |

## Wstecz: moduł → ID

| Moduł | Trace |
|---|---|
| `vcs_lite/__init__.py` | DEC-VCS-038, DES-VCS-030 |

## Ostrzeżenia

- AT-VCS-001 (@confirmed) nie ma testu test_at_vcs_001_…
- AT-VCS-002 (@confirmed) nie ma testu test_at_vcs_002_…
- AT-VCS-003 (@confirmed) nie ma testu test_at_vcs_003_…
- AT-VCS-004 (@confirmed) nie ma testu test_at_vcs_004_…
- AT-VCS-005 (@confirmed) nie ma testu test_at_vcs_005_…
- AT-VCS-006 (@confirmed) nie ma testu test_at_vcs_006_…
- AT-VCS-008 (@confirmed) nie ma testu test_at_vcs_008_…
- AT-VCS-009 (@confirmed) nie ma testu test_at_vcs_009_…
- AT-VCS-010 (@confirmed) nie ma testu test_at_vcs_010_…
- AT-VCS-011 (@confirmed) nie ma testu test_at_vcs_011_…
- AT-VCS-012 (@confirmed) nie ma testu test_at_vcs_012_…
- AT-VCS-013 (@confirmed) nie ma testu test_at_vcs_013_…
- AT-VCS-014 (@confirmed) nie ma testu test_at_vcs_014_…
- AT-VCS-015 (@confirmed) nie ma testu test_at_vcs_015_…
- AT-VCS-016 (@confirmed) nie ma testu test_at_vcs_016_…
- AT-VCS-017 (@confirmed) nie ma testu test_at_vcs_017_…
- AT-VCS-018 (@confirmed) nie ma testu test_at_vcs_018_…
- AT-VCS-019 (@confirmed) nie ma testu test_at_vcs_019_…
- AT-VCS-020 (@confirmed) nie ma testu test_at_vcs_020_…
- AT-VCS-021 (@confirmed) nie ma testu test_at_vcs_021_…
- AT-VCS-022 (@confirmed) nie ma testu test_at_vcs_022_…
- AT-VCS-023 (@confirmed) nie ma testu test_at_vcs_023_…
- AT-VCS-024 (@confirmed) nie ma testu test_at_vcs_024_…
- AT-VCS-025 (@confirmed) nie ma testu test_at_vcs_025_…
- AT-VCS-026 (@confirmed) nie ma testu test_at_vcs_026_…
- AT-VCS-027 (@confirmed) nie ma testu test_at_vcs_027_…
- AT-VCS-028 (@confirmed) nie ma testu test_at_vcs_028_…
- AT-VCS-029 (@confirmed) nie ma testu test_at_vcs_029_…
