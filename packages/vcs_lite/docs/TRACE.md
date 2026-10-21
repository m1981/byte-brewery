# vcs-lite — macierz śledzenia powiązań

Plik generowany przez `tests/test_traceability.py` (REQ-VCS-207). Nie edytować ręcznie.

## Wymaganie → projekt, scenariusze, weryfikacja, testy, kod

| REQ | DES | AT | VER | Testy | Moduły |
|---|---|---|---|---|---|
| REQ-VCS-001 | DES-VCS-019 | AT-VCS-001, AT-VCS-018, AT-VCS-022 | VER-VCS-005, VER-VCS-008, VER-VCS-010 | test_at_vcs_001_chosen_repositories_survive_a_restart, test_at_vcs_018_only_first_level_repositories_are_listed, test_at_vcs_022_folders_that_are_not_repositories_are_hidden, test_des_vcs_019_corrupt_file_is_reported_not_silently_reset, test_des_vcs_019_defaults_when_no_settings_file_exists, test_des_vcs_019_missing_keys_fall_back_to_defaults, test_des_vcs_019_rootdir_keeps_tilde_and_expands_on_use, test_des_vcs_019_values_of_the_wrong_type_are_reported, test_uc_vcs_01_failed_save_keeps_the_previous_settings, test_uc_vcs_01_missing_rootdir_is_reported_with_its_path | vcs_lite/core/settings.py |
| REQ-VCS-002 | DES-VCS-018, DES-VCS-023 | — | VER-VCS-012 | test_des_vcs_023_repo_list_follows_model_changes, test_req_vcs_002_branch_upstream_and_ahead_behind_headers, test_req_vcs_002_list_shows_branch_and_number_of_changed_files, test_uc_vcs_02_detached_head_allows_commit_but_not_push_or_pull, test_uc_vcs_02_detached_head_has_no_branch | vcs_lite/app/model.py, vcs_lite/core/status.py, vcs_lite/ui/main_window.py |
| REQ-VCS-003 | DES-VCS-005, DES-VCS-006, DES-VCS-024 | AT-VCS-003, AT-VCS-004, AT-VCS-005 | VER-VCS-001 | test_at_vcs_003_modified_file_is_in_changes_and_not_staged, test_at_vcs_004_external_tool_gets_the_sides_of_the_chosen_group, test_at_vcs_005_files_in_a_new_folder_are_listed_one_by_one, test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree | vcs_lite/core/status.py |
| REQ-VCS-004 | DES-VCS-005 | AT-VCS-006 | VER-VCS-001 | test_at_vcs_006_ignored_files_are_not_shown, test_req_vcs_004_ignored_files_are_not_reported, test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree | vcs_lite/core/status.py |
| REQ-VCS-005 | DES-VCS-011, DES-VCS-012, DES-VCS-024 | AT-VCS-008, AT-VCS-009, AT-VCS-029 | VER-VCS-002 | test_at_vcs_008_stage_records_the_whole_file, test_at_vcs_009_unstaging_a_rename_restores_both_paths, test_at_vcs_029_double_click_opens_compare_and_space_stages, test_des_vcs_012_unstage_in_a_repo_without_commits, test_req_vcs_005_stage_adds_an_unversioned_file, test_req_vcs_005_stage_records_a_deletion, test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree | vcs_lite/core/repo.py |
| REQ-VCS-006 (zastąpione) | — | — | — | test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree | — |
| REQ-VCS-007 | DES-VCS-008 | AT-VCS-007 | VER-VCS-001 | — | — |
| REQ-VCS-008 | DES-VCS-001 | — | VER-VCS-001 | test_des_vcs_001_input_goes_to_stdin, test_des_vcs_001_output_is_bytes_and_errors_are_decoded | vcs_lite/core/gitcli.py |
| REQ-VCS-009 | DES-VCS-013, DES-VCS-026 | AT-VCS-010, AT-VCS-011 | VER-VCS-003 | test_at_vcs_010_commit_contains_only_staged_and_clears_the_message, test_at_vcs_011_commit_is_inactive_without_staged_files_or_message, test_req_vcs_009_commit_contains_only_staged_changes | vcs_lite/app/model.py, vcs_lite/core/repo.py, vcs_lite/ui/main_window.py |
| REQ-VCS-010 | DES-VCS-001, DES-VCS-013, DES-VCS-043 | AT-VCS-012 | VER-VCS-003 | test_at_vcs_012_rejected_commit_keeps_message_and_staged_files, test_des_vcs_001_input_goes_to_stdin, test_des_vcs_001_output_is_bytes_and_errors_are_decoded, test_req_vcs_010_hook_rejection_returns_its_output_and_keeps_the_index | vcs_lite/app/model.py, vcs_lite/core/gitcli.py, vcs_lite/core/repo.py |
| REQ-VCS-011 | DES-VCS-014 | AT-VCS-013 | VER-VCS-004 | test_at_vcs_013_commit_and_push_reaches_the_upstream, test_req_vcs_011_commit_and_push_reaches_the_upstream | vcs_lite/app/model.py, vcs_lite/core/repo.py |
| REQ-VCS-012 | DES-VCS-014 | AT-VCS-014 | VER-VCS-004 | test_at_vcs_014_rejected_push_keeps_the_commit_and_does_not_pull | vcs_lite/app/model.py, vcs_lite/core/repo.py |
| REQ-VCS-013 | DES-VCS-014, DES-VCS-026, DES-VCS-043 | — | VER-VCS-004 | test_req_vcs_013_branch_without_upstream_asks_before_pushing, test_req_vcs_013_push_can_set_the_upstream | vcs_lite/app/model.py, vcs_lite/core/repo.py, vcs_lite/ui/main_window.py |
| REQ-VCS-014 | DES-VCS-002, DES-VCS-003, DES-VCS-004 | AT-VCS-015 | VER-VCS-004 | test_at_vcs_015_missing_credentials_end_with_a_message_not_a_hang, test_des_vcs_002_git_never_prompts_in_a_hidden_terminal, test_des_vcs_002_reads_do_not_take_optional_locks, test_des_vcs_003_timeout_ends_with_a_message_instead_of_hanging, test_des_vcs_004_network_calls_use_ssh_batch_mode, test_des_vcs_004_user_core_ssh_command_is_kept, test_des_vcs_004_user_ssh_command_in_env_is_kept | vcs_lite/core/gitcli.py |
| REQ-VCS-015 | DES-VCS-018 | — | VER-VCS-012 | test_req_vcs_015_refresh_all_updates_every_watched_repository, test_uc_vcs_02_detached_head_allows_commit_but_not_push_or_pull, test_uc_vcs_02_detached_head_has_no_branch | vcs_lite/app/model.py |
| REQ-VCS-016 | DES-VCS-016, DES-VCS-043 | — | VER-VCS-012 | test_des_vcs_016_a_failing_job_delivers_its_error, test_des_vcs_016_another_repo_can_run_meanwhile, test_des_vcs_016_on_done_may_schedule_a_follow_up_on_the_same_key, test_des_vcs_016_second_operation_on_a_busy_repo_is_rejected, test_req_vcs_016_no_second_operation_while_one_is_running | vcs_lite/app/model.py, vcs_lite/app/worker.py, vcs_lite/ui/pump.py |
| REQ-VCS-017 | DES-VCS-002, DES-VCS-019, DES-VCS-038 | AT-VCS-017, AT-VCS-027 | VER-VCS-007 | test_at_vcs_017_browsing_does_not_change_the_repository, test_at_vcs_027_temp_files_disappear_and_the_repo_is_refreshed_after_closing, test_des_vcs_002_git_never_prompts_in_a_hidden_terminal, test_des_vcs_002_reads_do_not_take_optional_locks, test_des_vcs_019_corrupt_file_is_reported_not_silently_reset, test_des_vcs_019_defaults_when_no_settings_file_exists, test_des_vcs_019_missing_keys_fall_back_to_defaults, test_des_vcs_019_rootdir_keeps_tilde_and_expands_on_use, test_des_vcs_019_values_of_the_wrong_type_are_reported, test_des_vcs_038_empty_side_is_an_empty_file, test_des_vcs_038_git_sides_are_read_only_temp_files_with_the_file_name, test_des_vcs_038_temp_files_are_removed_after_the_tool_exits, test_des_vcs_038_temp_files_are_removed_when_the_tool_cannot_start, test_req_vcs_017_saving_settings_writes_nothing_into_repositories | vcs_lite/app/model.py, vcs_lite/core/difftool.py, vcs_lite/core/gitcli.py, vcs_lite/core/repo.py, vcs_lite/core/settings.py |
| REQ-VCS-018 | DES-VCS-023 | AT-VCS-002 | VER-VCS-005 | test_at_vcs_002_removed_repository_is_unavailable_and_others_keep_working, test_des_vcs_023_repo_list_follows_model_changes, test_uc_vcs_02_detached_head_allows_commit_but_not_push_or_pull, test_uc_vcs_02_detached_head_has_no_branch | vcs_lite/app/model.py, vcs_lite/ui/main_window.py |
| REQ-VCS-019 | DES-VCS-006, DES-VCS-026 | — | VER-VCS-001 | test_req_vcs_019_conflicts_block_the_commit_with_a_reason, test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree, test_uc_vcs_02_detached_head_allows_commit_but_not_push_or_pull, test_uc_vcs_02_detached_head_has_no_branch | vcs_lite/app/model.py, vcs_lite/core/status.py, vcs_lite/ui/main_window.py |
| REQ-VCS-020 | DES-VCS-015 | AT-VCS-020, AT-VCS-021 | VER-VCS-009 | test_at_vcs_020_pull_fast_forwards_to_the_upstream, test_at_vcs_021_pull_with_diverged_branches_changes_nothing, test_req_vcs_020_pull_fast_forwards_the_selected_repository | vcs_lite/app/model.py, vcs_lite/core/repo.py |
| REQ-VCS-021 | DES-VCS-016, DES-VCS-026 | AT-VCS-019 | VER-VCS-008, VER-VCS-012 | test_at_vcs_019_commit_goes_only_to_the_selected_repository, test_des_vcs_016_a_failing_job_delivers_its_error, test_des_vcs_016_another_repo_can_run_meanwhile, test_des_vcs_016_on_done_may_schedule_a_follow_up_on_the_same_key, test_des_vcs_016_second_operation_on_a_busy_repo_is_rejected, test_req_vcs_021_operation_targets_the_repository_selected_at_click_time | vcs_lite/app/model.py, vcs_lite/app/worker.py, vcs_lite/ui/main_window.py |
| REQ-VCS-022 | DES-VCS-021, DES-VCS-026 | AT-VCS-023, AT-VCS-024 | VER-VCS-010 | test_at_vcs_023_each_repository_keeps_its_own_draft_and_names_the_target, test_at_vcs_024_drafts_are_not_kept_after_a_restart | vcs_lite/app/model.py, vcs_lite/ui/main_window.py |
| REQ-VCS-023 | DES-VCS-007, DES-VCS-036, DES-VCS-037, DES-VCS-038, DES-VCS-039 | AT-VCS-004, AT-VCS-025, AT-VCS-026, AT-VCS-027, AT-VCS-028, AT-VCS-029 | VER-VCS-011 | test_at_vcs_004_external_tool_gets_the_sides_of_the_chosen_group, test_at_vcs_025_missing_diff_tool_gives_a_message_and_the_app_keeps_working, test_at_vcs_026_the_diff_tool_can_be_swapped_in_settings, test_at_vcs_027_temp_files_disappear_and_the_repo_is_refreshed_after_closing, test_at_vcs_028_change_saved_in_the_tool_is_visible_after_closing, test_at_vcs_029_double_click_opens_compare_and_space_stages, test_des_vcs_007_empty_sides_for_new_and_deleted_files, test_des_vcs_007_rename_reads_head_from_original_path, test_des_vcs_007_staged_sides_are_head_and_index, test_des_vcs_036_any_cli_tool_can_be_plugged_in, test_des_vcs_037_default_command_is_beyond_compare, test_des_vcs_037_diff_tool_command_is_stored_in_settings, test_des_vcs_037_template_fills_paths_and_titles, test_des_vcs_037_titles_with_braces_are_inserted_literally, test_des_vcs_038_empty_side_is_an_empty_file, test_des_vcs_038_git_sides_are_read_only_temp_files_with_the_file_name, test_des_vcs_038_temp_files_are_removed_after_the_tool_exits, test_des_vcs_038_temp_files_are_removed_when_the_tool_cannot_start, test_des_vcs_039_exit_code_and_stderr_are_reported, test_des_vcs_039_missing_tool_error_names_the_command, test_des_vcs_039_nonzero_exit_without_stderr_is_not_a_failure, test_req_vcs_023_worktree_side_is_passed_as_the_real_file, test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree | vcs_lite/app/model.py, vcs_lite/core/difftool.py, vcs_lite/core/repo.py, vcs_lite/core/settings.py, vcs_lite/ui/main.py |
| REQ-VCS-024 | DES-VCS-044 | AT-VCS-030, AT-VCS-031 | VER-VCS-002 | test_at_vcs_030_fixed_conflict_is_marked_resolved_with_space, test_at_vcs_031_file_with_markers_stays_in_conflict_with_a_message, test_req_vcs_024_conflict_resolved_by_deleting_the_file_uses_git_rm, test_req_vcs_024_diff3_base_marker_also_blocks, test_req_vcs_024_file_with_markers_is_not_marked_and_names_the_line, test_req_vcs_024_markdown_heading_underline_is_not_a_marker, test_req_vcs_024_resolved_conflict_is_marked_with_git_add, test_t_vcs_01_added_is_staged_empty_vs_index, test_t_vcs_01_conflict_is_listed_without_diff_sides, test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty, test_t_vcs_01_mm_is_in_staged_and_changes, test_t_vcs_01_modified_in_index_is_staged_head_vs_index, test_t_vcs_01_paths_with_spaces_and_polish_letters, test_t_vcs_01_rename_is_staged_with_original_path, test_t_vcs_01_repo_without_commits_stages_against_empty, test_t_vcs_01_untracked_files_are_listed_one_by_one, test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty, test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree | vcs_lite/app/model.py, vcs_lite/core/repo.py |
| REQ-VCS-100 | DES-VCS-008, DES-VCS-034 | AT-VCS-016 | VER-VCS-006 | — | — |
| REQ-VCS-101 | DES-VCS-017, DES-VCS-035 | — | VER-VCS-006 | test_des_vcs_017_nothing_is_pending_while_idle_so_the_ui_stops_polling, test_des_vcs_017_pump_polls_only_while_work_is_pending, test_des_vcs_017_results_are_delivered_only_by_drain_on_the_calling_thread, test_des_vcs_017_the_key_stays_busy_until_drained_and_then_frees, test_des_vcs_035_every_call_is_counted, test_req_vcs_101_the_model_makes_no_git_calls_while_idle | vcs_lite/app/worker.py, vcs_lite/core/gitcli.py, vcs_lite/ui/pump.py |
| REQ-VCS-102 | DES-VCS-034 | — | VER-VCS-006 | — | — |
| REQ-VCS-103 | DES-VCS-028, DES-VCS-029, DES-VCS-041 | — | VER-VCS-013 | test_des_vcs_041_does_nothing_when_the_base_python_has_no_tcl, test_des_vcs_041_keeps_paths_the_user_already_set, test_des_vcs_041_points_tcl_and_tk_at_the_base_python | vcs_lite/ui/main.py, vcs_lite/ui/tkenv.py |
| REQ-VCS-200 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_200_checker_reports_duplicate_definition, test_req_vcs_200_each_id_defined_once | — |
| REQ-VCS-201 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_201_checker_expands_en_dash_ranges, test_req_vcs_201_checker_rejects_bare_number_lists, test_req_vcs_201_checker_reports_undefined_reference, test_req_vcs_201_checker_resolves_ids_cited_in_the_manual_checklist, test_req_vcs_201_references_are_full_and_resolve | — |
| REQ-VCS-202 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_202_checker_accepts_full_coverage, test_req_vcs_202_checker_ignores_withdrawn_design, test_req_vcs_202_checker_reads_status_only_from_description_start, test_req_vcs_202_checker_reports_req_without_design, test_req_vcs_202_forward_req_to_verification_and_design | — |
| REQ-VCS-203 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_203_backward_from_documents, test_req_vcs_203_checker_reports_design_without_link | — |
| REQ-VCS-204 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_204_checker_rejects_test_without_id, test_req_vcs_204_test_names_carry_ids | — |
| REQ-VCS-205 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_205_checker_reports_confirmed_scenario_without_test, test_req_vcs_205_confirmed_scenarios_have_tests | — |
| REQ-VCS-206 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_206_checker_requires_trace_line, test_req_vcs_206_modules_carry_trace | — |
| REQ-VCS-207 | DES-VCS-040 | — | VER-VCS-014 | test_req_vcs_207_matrix_is_generated, test_req_vcs_207_matrix_links_tests_through_referenced_ids | — |

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
| AT-VCS-030 | confirmed | REQ-VCS-024 |
| AT-VCS-031 | confirmed | REQ-VCS-024 |

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
| DES-VCS-016 | REQ-VCS-016, REQ-VCS-021 |
| DES-VCS-017 | REQ-VCS-101 |
| DES-VCS-018 | REQ-VCS-002, REQ-VCS-015 |
| DES-VCS-019 | REQ-VCS-001, REQ-VCS-017 |
| DES-VCS-020 | — |
| DES-VCS-021 | REQ-VCS-022 |
| DES-VCS-022 | — |
| DES-VCS-023 | REQ-VCS-002, REQ-VCS-018 |
| DES-VCS-024 | REQ-VCS-003, REQ-VCS-005 |
| DES-VCS-025 (wycofane) | REQ-VCS-006 |
| DES-VCS-026 | REQ-VCS-009, REQ-VCS-013, REQ-VCS-019, REQ-VCS-021, REQ-VCS-022 |
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
| DES-VCS-041 | REQ-VCS-103 |
| DES-VCS-042 | — |
| DES-VCS-043 | REQ-VCS-010, REQ-VCS-013, REQ-VCS-016 |
| DES-VCS-044 | REQ-VCS-024 |

## Wstecz: test → ID

| Test | Plik | ID |
|---|---|---|
| `test_at_vcs_001_chosen_repositories_survive_a_restart` | test_settings.py | AT-VCS-001 |
| `test_at_vcs_002_removed_repository_is_unavailable_and_others_keep_working` | test_model.py | AT-VCS-002 |
| `test_at_vcs_003_modified_file_is_in_changes_and_not_staged` | test_model.py | AT-VCS-003 |
| `test_at_vcs_004_external_tool_gets_the_sides_of_the_chosen_group` | test_model.py | AT-VCS-004 |
| `test_at_vcs_005_files_in_a_new_folder_are_listed_one_by_one` | test_model.py | AT-VCS-005 |
| `test_at_vcs_006_ignored_files_are_not_shown` | test_model.py | AT-VCS-006 |
| `test_at_vcs_008_stage_records_the_whole_file` | test_repo.py | AT-VCS-008 |
| `test_at_vcs_009_unstaging_a_rename_restores_both_paths` | test_repo.py | AT-VCS-009 |
| `test_at_vcs_010_commit_contains_only_staged_and_clears_the_message` | test_model.py | AT-VCS-010 |
| `test_at_vcs_011_commit_is_inactive_without_staged_files_or_message` | test_model.py | AT-VCS-011 |
| `test_at_vcs_012_rejected_commit_keeps_message_and_staged_files` | test_model.py | AT-VCS-012 |
| `test_at_vcs_013_commit_and_push_reaches_the_upstream` | test_repo.py | AT-VCS-013 |
| `test_at_vcs_014_rejected_push_keeps_the_commit_and_does_not_pull` | test_repo.py | AT-VCS-014 |
| `test_at_vcs_015_missing_credentials_end_with_a_message_not_a_hang` | test_model.py | AT-VCS-015 |
| `test_at_vcs_017_browsing_does_not_change_the_repository` | test_repo.py | AT-VCS-017 |
| `test_at_vcs_018_only_first_level_repositories_are_listed` | test_settings.py | AT-VCS-018 |
| `test_at_vcs_019_commit_goes_only_to_the_selected_repository` | test_model.py | AT-VCS-019 |
| `test_at_vcs_020_pull_fast_forwards_to_the_upstream` | test_repo.py | AT-VCS-020 |
| `test_at_vcs_021_pull_with_diverged_branches_changes_nothing` | test_repo.py | AT-VCS-021 |
| `test_at_vcs_022_folders_that_are_not_repositories_are_hidden` | test_settings.py | AT-VCS-022 |
| `test_at_vcs_023_each_repository_keeps_its_own_draft_and_names_the_target` | test_model.py | AT-VCS-023 |
| `test_at_vcs_024_drafts_are_not_kept_after_a_restart` | test_model.py | AT-VCS-024 |
| `test_at_vcs_025_missing_diff_tool_gives_a_message_and_the_app_keeps_working` | test_model.py | AT-VCS-025 |
| `test_at_vcs_026_the_diff_tool_can_be_swapped_in_settings` | test_model.py | AT-VCS-026 |
| `test_at_vcs_027_temp_files_disappear_and_the_repo_is_refreshed_after_closing` | test_model.py | AT-VCS-027 |
| `test_at_vcs_028_change_saved_in_the_tool_is_visible_after_closing` | test_model.py | AT-VCS-028 |
| `test_at_vcs_029_double_click_opens_compare_and_space_stages` | test_model.py | AT-VCS-029 |
| `test_at_vcs_030_fixed_conflict_is_marked_resolved_with_space` | test_model.py | AT-VCS-030 |
| `test_at_vcs_031_file_with_markers_stays_in_conflict_with_a_message` | test_model.py | AT-VCS-031 |
| `test_des_vcs_001_input_goes_to_stdin` | test_gitcli.py | DES-VCS-001 |
| `test_des_vcs_001_output_is_bytes_and_errors_are_decoded` | test_gitcli.py | DES-VCS-001 |
| `test_des_vcs_002_git_never_prompts_in_a_hidden_terminal` | test_gitcli.py | DES-VCS-002 |
| `test_des_vcs_002_reads_do_not_take_optional_locks` | test_gitcli.py | DES-VCS-002 |
| `test_des_vcs_003_timeout_ends_with_a_message_instead_of_hanging` | test_gitcli.py | DES-VCS-003 |
| `test_des_vcs_004_network_calls_use_ssh_batch_mode` | test_gitcli.py | DES-VCS-004 |
| `test_des_vcs_004_user_core_ssh_command_is_kept` | test_gitcli.py | DES-VCS-004 |
| `test_des_vcs_004_user_ssh_command_in_env_is_kept` | test_gitcli.py | DES-VCS-004 |
| `test_des_vcs_007_empty_sides_for_new_and_deleted_files` | test_repo.py | DES-VCS-007 |
| `test_des_vcs_007_rename_reads_head_from_original_path` | test_repo.py | DES-VCS-007 |
| `test_des_vcs_007_staged_sides_are_head_and_index` | test_repo.py | DES-VCS-007 |
| `test_des_vcs_012_unstage_in_a_repo_without_commits` | test_repo.py | DES-VCS-012 |
| `test_des_vcs_016_a_failing_job_delivers_its_error` | test_worker.py | DES-VCS-016 |
| `test_des_vcs_016_another_repo_can_run_meanwhile` | test_worker.py | DES-VCS-016 |
| `test_des_vcs_016_on_done_may_schedule_a_follow_up_on_the_same_key` | test_worker.py | DES-VCS-016 |
| `test_des_vcs_016_second_operation_on_a_busy_repo_is_rejected` | test_worker.py | DES-VCS-016 |
| `test_des_vcs_017_nothing_is_pending_while_idle_so_the_ui_stops_polling` | test_worker.py | DES-VCS-017 |
| `test_des_vcs_017_pump_polls_only_while_work_is_pending` | test_main_window.py | DES-VCS-017 |
| `test_des_vcs_017_results_are_delivered_only_by_drain_on_the_calling_thread` | test_worker.py | DES-VCS-017 |
| `test_des_vcs_017_the_key_stays_busy_until_drained_and_then_frees` | test_worker.py | DES-VCS-017 |
| `test_des_vcs_019_corrupt_file_is_reported_not_silently_reset` | test_settings.py | DES-VCS-019 |
| `test_des_vcs_019_defaults_when_no_settings_file_exists` | test_settings.py | DES-VCS-019 |
| `test_des_vcs_019_missing_keys_fall_back_to_defaults` | test_settings.py | DES-VCS-019 |
| `test_des_vcs_019_rootdir_keeps_tilde_and_expands_on_use` | test_settings.py | DES-VCS-019 |
| `test_des_vcs_019_values_of_the_wrong_type_are_reported` | test_settings.py | DES-VCS-019 |
| `test_des_vcs_020_hidden_folders_are_skipped` | test_settings.py | DES-VCS-020 |
| `test_des_vcs_020_plain_files_are_ignored_and_names_are_sorted` | test_settings.py | DES-VCS-020 |
| `test_des_vcs_020_worktree_with_git_file_counts_as_repository` | test_settings.py | DES-VCS-020 |
| `test_des_vcs_022_window_has_repo_list_file_area_and_commit_bar` | test_main_window.py | DES-VCS-022 |
| `test_des_vcs_023_repo_list_follows_model_changes` | test_main_window.py | DES-VCS-023 |
| `test_des_vcs_035_every_call_is_counted` | test_gitcli.py | DES-VCS-035 |
| `test_des_vcs_036_any_cli_tool_can_be_plugged_in` | test_difftool.py | DES-VCS-036 |
| `test_des_vcs_037_default_command_is_beyond_compare` | test_difftool.py | DES-VCS-037 |
| `test_des_vcs_037_diff_tool_command_is_stored_in_settings` | test_settings.py | DES-VCS-037 |
| `test_des_vcs_037_template_fills_paths_and_titles` | test_difftool.py | DES-VCS-037 |
| `test_des_vcs_037_titles_with_braces_are_inserted_literally` | test_difftool.py | DES-VCS-037 |
| `test_des_vcs_038_empty_side_is_an_empty_file` | test_difftool.py | DES-VCS-038 |
| `test_des_vcs_038_git_sides_are_read_only_temp_files_with_the_file_name` | test_difftool.py | DES-VCS-038 |
| `test_des_vcs_038_temp_files_are_removed_after_the_tool_exits` | test_difftool.py | DES-VCS-038 |
| `test_des_vcs_038_temp_files_are_removed_when_the_tool_cannot_start` | test_difftool.py | DES-VCS-038 |
| `test_des_vcs_039_exit_code_and_stderr_are_reported` | test_difftool.py | DES-VCS-039 |
| `test_des_vcs_039_missing_tool_error_names_the_command` | test_difftool.py | DES-VCS-039 |
| `test_des_vcs_039_nonzero_exit_without_stderr_is_not_a_failure` | test_difftool.py | DES-VCS-039 |
| `test_des_vcs_041_does_nothing_when_the_base_python_has_no_tcl` | test_tkenv.py | DES-VCS-041 |
| `test_des_vcs_041_keeps_paths_the_user_already_set` | test_tkenv.py | DES-VCS-041 |
| `test_des_vcs_041_points_tcl_and_tk_at_the_base_python` | test_tkenv.py | DES-VCS-041 |
| `test_req_vcs_002_branch_upstream_and_ahead_behind_headers` | test_status.py | REQ-VCS-002 |
| `test_req_vcs_002_list_shows_branch_and_number_of_changed_files` | test_model.py | REQ-VCS-002 |
| `test_req_vcs_004_ignored_files_are_not_reported` | test_status.py | REQ-VCS-004 |
| `test_req_vcs_005_stage_adds_an_unversioned_file` | test_repo.py | REQ-VCS-005 |
| `test_req_vcs_005_stage_records_a_deletion` | test_repo.py | REQ-VCS-005 |
| `test_req_vcs_009_commit_contains_only_staged_changes` | test_repo.py | REQ-VCS-009 |
| `test_req_vcs_010_hook_rejection_returns_its_output_and_keeps_the_index` | test_repo.py | REQ-VCS-010 |
| `test_req_vcs_011_commit_and_push_reaches_the_upstream` | test_model.py | REQ-VCS-011 |
| `test_req_vcs_013_branch_without_upstream_asks_before_pushing` | test_model.py | REQ-VCS-013 |
| `test_req_vcs_013_push_can_set_the_upstream` | test_repo.py | REQ-VCS-013 |
| `test_req_vcs_015_refresh_all_updates_every_watched_repository` | test_model.py | REQ-VCS-015 |
| `test_req_vcs_016_no_second_operation_while_one_is_running` | test_model.py | REQ-VCS-016 |
| `test_req_vcs_017_saving_settings_writes_nothing_into_repositories` | test_settings.py | REQ-VCS-017 |
| `test_req_vcs_019_conflicts_block_the_commit_with_a_reason` | test_model.py | REQ-VCS-019 |
| `test_req_vcs_020_pull_fast_forwards_the_selected_repository` | test_model.py | REQ-VCS-020 |
| `test_req_vcs_021_operation_targets_the_repository_selected_at_click_time` | test_model.py | REQ-VCS-021 |
| `test_req_vcs_023_worktree_side_is_passed_as_the_real_file` | test_difftool.py | REQ-VCS-023 |
| `test_req_vcs_024_conflict_resolved_by_deleting_the_file_uses_git_rm` | test_repo.py | REQ-VCS-024 |
| `test_req_vcs_024_diff3_base_marker_also_blocks` | test_repo.py | REQ-VCS-024 |
| `test_req_vcs_024_file_with_markers_is_not_marked_and_names_the_line` | test_repo.py | REQ-VCS-024 |
| `test_req_vcs_024_markdown_heading_underline_is_not_a_marker` | test_repo.py | REQ-VCS-024 |
| `test_req_vcs_024_resolved_conflict_is_marked_with_git_add` | test_repo.py | REQ-VCS-024 |
| `test_req_vcs_101_the_model_makes_no_git_calls_while_idle` | test_model.py | REQ-VCS-101 |
| `test_req_vcs_200_checker_reports_duplicate_definition` | test_traceability.py | REQ-VCS-200 |
| `test_req_vcs_200_each_id_defined_once` | test_traceability.py | REQ-VCS-200 |
| `test_req_vcs_201_checker_expands_en_dash_ranges` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_201_checker_rejects_bare_number_lists` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_201_checker_reports_undefined_reference` | test_traceability.py | REQ-VCS-201 |
| `test_req_vcs_201_checker_resolves_ids_cited_in_the_manual_checklist` | test_traceability.py | REQ-VCS-201 |
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
| `test_req_vcs_207_matrix_links_tests_through_referenced_ids` | test_traceability.py | REQ-VCS-207 |
| `test_t_vcs_01_added_is_staged_empty_vs_index` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_conflict_is_listed_without_diff_sides` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_deleted_in_index_is_staged_head_vs_empty` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_mm_is_in_staged_and_changes` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_modified_in_index_is_staged_head_vs_index` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_paths_with_spaces_and_polish_letters` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_rename_is_staged_with_original_path` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_repo_without_commits_stages_against_empty` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_untracked_files_are_listed_one_by_one` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_worktree_deleted_is_changes_index_vs_empty` | test_status.py | T-VCS-01 |
| `test_t_vcs_01_worktree_modified_is_changes_index_vs_worktree` | test_status.py | T-VCS-01 |
| `test_uc_vcs_01_failed_save_keeps_the_previous_settings` | test_settings.py | UC-VCS-01 |
| `test_uc_vcs_01_missing_rootdir_is_reported_with_its_path` | test_settings.py | UC-VCS-01 |
| `test_uc_vcs_02_detached_head_allows_commit_but_not_push_or_pull` | test_model.py | UC-VCS-02 |
| `test_uc_vcs_02_detached_head_has_no_branch` | test_status.py | UC-VCS-02 |

## Wstecz: moduł → ID

| Moduł | Trace |
|---|---|
| `vcs_lite/__init__.py` | DEC-VCS-038, DES-VCS-030 |
| `vcs_lite/app/__init__.py` | DEC-VCS-030, DES-VCS-032 |
| `vcs_lite/app/model.py` | DES-VCS-016, DES-VCS-018, DES-VCS-021, DES-VCS-026, DES-VCS-036, DES-VCS-038, REQ-VCS-002, REQ-VCS-009, REQ-VCS-010, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-015, REQ-VCS-016, REQ-VCS-018, REQ-VCS-019, REQ-VCS-020, REQ-VCS-021, REQ-VCS-022, REQ-VCS-023, REQ-VCS-024, S-VCS-01 |
| `vcs_lite/app/worker.py` | DES-VCS-016, DES-VCS-017, REQ-VCS-016, REQ-VCS-101 |
| `vcs_lite/core/__init__.py` | DEC-VCS-030, DES-VCS-030 |
| `vcs_lite/core/difftool.py` | DES-VCS-036, DES-VCS-037, DES-VCS-038, DES-VCS-039, REQ-VCS-023 |
| `vcs_lite/core/gitcli.py` | DES-VCS-001, DES-VCS-002, DES-VCS-003, DES-VCS-004, DES-VCS-035, REQ-VCS-010, REQ-VCS-014, REQ-VCS-017 |
| `vcs_lite/core/repo.py` | DES-VCS-007, DES-VCS-011, DES-VCS-012, DES-VCS-013, DES-VCS-014, DES-VCS-015, DES-VCS-044, REQ-VCS-005, REQ-VCS-009, REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-017, REQ-VCS-020, REQ-VCS-024 |
| `vcs_lite/core/settings.py` | DEC-VCS-007, DEC-VCS-016, DEC-VCS-027, DES-VCS-019, DES-VCS-020, DES-VCS-037, REQ-VCS-001, REQ-VCS-017 |
| `vcs_lite/core/status.py` | DES-VCS-005, DES-VCS-006, REQ-VCS-002, REQ-VCS-003, REQ-VCS-004, REQ-VCS-019, T-VCS-01 |
| `vcs_lite/ui/__init__.py` | DEC-VCS-030, DES-VCS-022 |
| `vcs_lite/ui/main.py` | DES-VCS-028, DES-VCS-029, DES-VCS-036, DES-VCS-041, REQ-VCS-103 |
| `vcs_lite/ui/main_window.py` | DES-VCS-022, DES-VCS-023, DES-VCS-026, REQ-VCS-002, REQ-VCS-021 |
| `vcs_lite/ui/pump.py` | DES-VCS-017, REQ-VCS-016, REQ-VCS-101 |
| `vcs_lite/ui/tkenv.py` | DES-VCS-041, OBS-VCS-009, REQ-VCS-103 |

## Ostrzeżenia

- brak
