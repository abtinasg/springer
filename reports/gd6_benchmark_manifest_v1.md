# G.D6 Benchmark Manifest

**Stage:** Part 3B.2R.1-G.D6-F0.1
**Benchmark ID:** SEMIT-GD6-BENCHMARK
**Version:** 1.0
**Contract ID:** SEMIT-GD6-ACCEPTANCE-CONTRACT
**Contract version:** 1.0
**Starting commit:** `7dbc206037250b1181aed94bfa7326d79df814fd`

## Benchmark Groups

| Group | Title | Expected Count | Claim IDs |
|-------|-------|----------------|-----------|
| BG-01 | Semantic Policy Tests | 35 | CLAIM-A |
| BG-02 | Historical Fixture Parity | 9 | CLAIM-A |
| BG-03 | Write-Guard Matrix | 240 | CLAIM-C, CLAIM-D |
| BG-04 | Production Entry-Point Guards | 4 | CLAIM-B |
| BG-05 | Restoration Identity Set | 20 | CLAIM-D |
| BG-06 | Forced-Exception Fixture Set | 3 | CLAIM-C, CLAIM-D |
| BG-07 | Transactional Rollback Scenarios | 6 | CLAIM-D |
| BG-08 | Rollback Mutation Set | 7 | CLAIM-D |
| BG-09 | Preservation and Zero-Activity Conditions | 17 | CLAIM-B, CLAIM-C |
| BG-10 | Report Integrity | 9 | CLAIM-E |
| BG-11 | Independent Clean-Environment Execution | 1 | CLAIM-E |

## Expected Counts

- **BG-01:** 35
- **BG-02:** 9
- **BG-03:** 240
- **BG-04:** 4
- **BG-05:** 20
- **BG-06:** 3
- **BG-07:** 6
- **BG-08:** 7
- **BG-09:** 17
- **BG-10:** 9
- **BG-11:** 1

## Exact Sets

### Write-Guard Mechanisms (15)

- builtins_open
- io_open
- path_open
- path_write_text
- path_write_bytes
- path_touch
- path_replace
- path_rename
- os_open
- os_replace
- os_rename
- shutil_copy
- shutil_copy2
- shutil_copyfile
- shutil_move

### Production Entry Points (4)

- build_core_bundle
- fit_event_candidates
- build_prediction_rows
- execute_postbuild_integration

### Restoration Keys (20)

- sys_profile_restored
- builtins_open_restored
- io_open_restored
- path_open_restored
- path_write_text_restored
- path_write_bytes_restored
- path_touch_restored
- path_replace_restored
- path_rename_restored
- os_open_restored
- os_replace_restored
- os_rename_restored
- shutil_copy_restored
- shutil_copy2_restored
- shutil_copyfile_restored
- shutil_move_restored
- build_core_bundle_restored
- fit_event_candidates_restored
- build_prediction_rows_restored
- execute_postbuild_integration_restored

### Forced-Exception Fixture Paths (3)

- reports/part3b_et_policy_implementation.json
- results/part1_full_reproduction/canonical.csv
- results/part3b_prediction_ledger/ledger.csv

### Rollback Scenarios (6)

- before_any_replacement / neither_exist
- before_any_replacement / both_exist
- after_json_before_md / neither_exist
- after_json_before_md / both_exist
- after_md_backup_before_md_replace / neither_exist
- after_md_backup_before_md_replace / both_exist

### Rollback Mutations (7)

- extensionless_temp_leftover
- pubbak_leftover
- unexpected_extra_file
- modified_original_json
- modified_original_markdown
- deleted_original_file
- path_type_change

### Semantic Test IDs (35)

- valid_roc_auc_row_accepted
- valid_avg_precision_row_accepted
- project_seed_independent_equivalent_row_accepted
- one_ulp_build_mismatch_rejected
- positive_zero_negative_zero_rejected
- build_score_byte_difference_rejected
- missing_candidate_rejected
- unexpected_candidate_rejected
- missing_candidate_field_rejected
- non_et_build1_validation_difference_rejected
- non_et_build2_test_difference_rejected
- et_validation_build_byte_difference_rejected
- et_test_build_byte_difference_rejected
- et_delta_above_tolerance_rejected_independently
- aggregate_maximum_cannot_substitute_for_independent_fields
- metric_build1_delta_above_tolerance_rejected
- metric_build2_delta_above_tolerance_rejected
- brier_rejected
- threshold_sensitive_metric_rejected
- unknown_metric_rejected
- validation_categorical_mismatch_rejected
- validation_numeric_mismatch_rejected
- selected_candidate_difference_rejected
- selection_mode_difference_rejected
- missing_dual_build_context_rejected
- single_build_evidence_cannot_produce_final_approval
- dual_build_all_eligible_classification_no_final_approval
- dual_build_one_ineligible_classification_no_final_approval
- dual_build_unknown_metric_classification_no_final_approval
- dual_build_missing_et_delta_classification_no_final_approval
- validator_single_build_pending_no_final_approval
- policy_specification_sha_mismatch_rejected
- policy_specification_contract_mutation_rejected
- identity_hardcoded_implementation_detector_passes
- frozen_nine_fixture_parity_with_gd5_2

### Write-Guard Target Paths (16)

- scripts/freeze_part3b_et_reconciliation_policy.py
- reports/part3b_et_reconciliation_policy.json
- reports/part3b_et_reconciliation_policy.md
- scripts/audit_part3b_et_canonical_reconciliation.py
- reports/part3b_et_canonical_reconciliation.json
- reports/part3b_et_canonical_reconciliation.md
- results/part3b_prediction_ledger/et_canonical_mismatch_matrix.csv
- results/part3b_prediction_ledger/sample_registry.csv
- results/part3b_prediction_ledger/split_membership_within.csv.gz
- results/part3b_prediction_ledger/canonical_result_reconstruction.csv
- results/part3b_prediction_ledger/ledger_manifest.json
- results/part3b_prediction_ledger/prediction_ledger_within.csv.gz
- results/part3b_prediction_ledger/split_membership_cross.csv.gz
- results/part3b_prediction_ledger/event_manifest.csv
- results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz
- results/part3b_prediction_ledger/validation_reconstruction.csv

### Preservation Conditions (17)

- model_fits_executed = 0
- prediction_calls_executed = 0
- production_model_evaluation_builds_executed = 0
- production_builder_entries = 0
- production_artifact_writes = 0
- canonical_file_writes = 0
- protected_artifacts_changed = 0
- protected_files_added = 0
- protected_files_removed = 0
- protected_files_modified = 0
- production_run_executed = False
- policy_executed_on_production_artifacts = False
- policy_approved = False
- policy_enforced = False
- production_execution_authorized = False
- part3b_complete = False
- part3c_authorized = False

### Report Integrity Conditions (9)

- final_json_parses
- markdown_generated_from_final_json
- render_markdown_equals_final_markdown
- no_self_referential_publication_result_hash_persisted
- no_stale_preliminary_publication_hash_persisted
- repository_relative_paths_only
- no_local_absolute_path
- no_editor_specific_cci_reference
- no_unsupported_scientific_claim

## Future Verifier Requirement

**Verifier path:** `scripts/verify_gd6_frozen_benchmark_v1.py`
**Execution pattern:** `python3 scripts/verify_gd6_frozen_benchmark_v1.py`

Requirements:

- execution_from_clean_clone
- recorded_environment
- exit_code_0
- complete_json_report
- complete_markdown_report
- no_production_action
- execution_by_evaluator_other_than_implementation_author

_At this stage, do not create that future implementation verifier. Record it as a normative future requirement._

## Acceptance Decision Rule

G.D6 Accepted = every mandatory benchmark item passes.

## Provenance

- Starting commit: `7dbc206037250b1181aed94bfa7326d79df814fd`
- Extraction method: runtime_output_and_constant_extraction_from_starting_commit
