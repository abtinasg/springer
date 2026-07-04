# Part 3B Split / Leakage Audit Report

- **Starting commit:** d16e28488aa0936014f020c05466181eff219af6
- **Repository:** abtinasg/springer
- **Branch:** major-revision-analysis-v2
- **Manifest version:** Part-3B-v1

## Dataset Profile

| project | n_rows | n_features | defective | defect_rate |
|---|---|---|---|---|
| CM1 | 498 | 20 | 49 | 0.098393574297188757 |
| JM1 | 13204 | 20 | 2103 | 0.15926991820660405 |
| KC1 | 2109 | 20 | 326 | 0.15457562825983878 |
| KC2 | 522 | 20 | 107 | 0.2049808429118774 |
| PC1 | 1109 | 20 | 77 | 0.06943192064923355 |

- Total rows: 17442
- Total defective: 2662
- Total nondefective: 14780

## Common Feature Schema

- Feature count: 20
- Feature schema SHA-256: ba0553dd1defe6a2da2e183979c58b165c964eef99915505e4d43e02ad47ee89

## Sample Registry Summary

- Rows: 17442
- Unique UIDs: 17442
- Duplicate UIDs: 0

## Event and Split Counts

| event_id | experiment | target_project | seed | n_train | n_validation | n_test | identity_overlap_count | preprocessing_train_only_passed |
|---|---|---|---|---|---|---|---|---|
| within_project__CM1__seed_007 | within_project | CM1 | 7 | 298 | 100 | 100 | 0 | True |
| within_project__JM1__seed_007 | within_project | JM1 | 7 | 7922 | 2641 | 2641 | 0 | True |
| within_project__KC1__seed_007 | within_project | KC1 | 7 | 1265 | 422 | 422 | 0 | True |
| within_project__KC2__seed_007 | within_project | KC2 | 7 | 312 | 105 | 105 | 0 | True |
| within_project__PC1__seed_007 | within_project | PC1 | 7 | 665 | 222 | 222 | 0 | True |
| within_project__CM1__seed_013 | within_project | CM1 | 13 | 298 | 100 | 100 | 0 | True |
| within_project__JM1__seed_013 | within_project | JM1 | 13 | 7922 | 2641 | 2641 | 0 | True |
| within_project__KC1__seed_013 | within_project | KC1 | 13 | 1265 | 422 | 422 | 0 | True |
| within_project__KC2__seed_013 | within_project | KC2 | 13 | 312 | 105 | 105 | 0 | True |
| within_project__PC1__seed_013 | within_project | PC1 | 13 | 665 | 222 | 222 | 0 | True |
| within_project__CM1__seed_029 | within_project | CM1 | 29 | 298 | 100 | 100 | 0 | True |
| within_project__JM1__seed_029 | within_project | JM1 | 29 | 7922 | 2641 | 2641 | 0 | True |
| within_project__KC1__seed_029 | within_project | KC1 | 29 | 1265 | 422 | 422 | 0 | True |
| within_project__KC2__seed_029 | within_project | KC2 | 29 | 312 | 105 | 105 | 0 | True |
| within_project__PC1__seed_029 | within_project | PC1 | 29 | 665 | 222 | 222 | 0 | True |
| within_project__CM1__seed_042 | within_project | CM1 | 42 | 298 | 100 | 100 | 0 | True |
| within_project__JM1__seed_042 | within_project | JM1 | 42 | 7922 | 2641 | 2641 | 0 | True |
| within_project__KC1__seed_042 | within_project | KC1 | 42 | 1265 | 422 | 422 | 0 | True |
| within_project__KC2__seed_042 | within_project | KC2 | 42 | 312 | 105 | 105 | 0 | True |
| within_project__PC1__seed_042 | within_project | PC1 | 42 | 665 | 222 | 222 | 0 | True |
| within_project__CM1__seed_101 | within_project | CM1 | 101 | 298 | 100 | 100 | 0 | True |
| within_project__JM1__seed_101 | within_project | JM1 | 101 | 7922 | 2641 | 2641 | 0 | True |
| within_project__KC1__seed_101 | within_project | KC1 | 101 | 1265 | 422 | 422 | 0 | True |
| within_project__KC2__seed_101 | within_project | KC2 | 101 | 312 | 105 | 105 | 0 | True |
| within_project__PC1__seed_101 | within_project | PC1 | 101 | 665 | 222 | 222 | 0 | True |
| cross_project__CM1__seed_007 | cross_project | CM1 | 7 | 12708 | 4236 | 498 | 0 | True |
| cross_project__JM1__seed_007 | cross_project | JM1 | 7 | 3178 | 1060 | 13204 | 0 | True |
| cross_project__KC1__seed_007 | cross_project | KC1 | 7 | 11499 | 3834 | 2109 | 0 | True |
| cross_project__KC2__seed_007 | cross_project | KC2 | 7 | 12690 | 4230 | 522 | 0 | True |
| cross_project__PC1__seed_007 | cross_project | PC1 | 7 | 12249 | 4084 | 1109 | 0 | True |
| cross_project__CM1__seed_013 | cross_project | CM1 | 13 | 12708 | 4236 | 498 | 0 | True |
| cross_project__JM1__seed_013 | cross_project | JM1 | 13 | 3178 | 1060 | 13204 | 0 | True |
| cross_project__KC1__seed_013 | cross_project | KC1 | 13 | 11499 | 3834 | 2109 | 0 | True |
| cross_project__KC2__seed_013 | cross_project | KC2 | 13 | 12690 | 4230 | 522 | 0 | True |
| cross_project__PC1__seed_013 | cross_project | PC1 | 13 | 12249 | 4084 | 1109 | 0 | True |
| cross_project__CM1__seed_029 | cross_project | CM1 | 29 | 12708 | 4236 | 498 | 0 | True |
| cross_project__JM1__seed_029 | cross_project | JM1 | 29 | 3178 | 1060 | 13204 | 0 | True |
| cross_project__KC1__seed_029 | cross_project | KC1 | 29 | 11499 | 3834 | 2109 | 0 | True |
| cross_project__KC2__seed_029 | cross_project | KC2 | 29 | 12690 | 4230 | 522 | 0 | True |
| cross_project__PC1__seed_029 | cross_project | PC1 | 29 | 12249 | 4084 | 1109 | 0 | True |
| cross_project__CM1__seed_042 | cross_project | CM1 | 42 | 12708 | 4236 | 498 | 0 | True |
| cross_project__JM1__seed_042 | cross_project | JM1 | 42 | 3178 | 1060 | 13204 | 0 | True |
| cross_project__KC1__seed_042 | cross_project | KC1 | 42 | 11499 | 3834 | 2109 | 0 | True |
| cross_project__KC2__seed_042 | cross_project | KC2 | 42 | 12690 | 4230 | 522 | 0 | True |
| cross_project__PC1__seed_042 | cross_project | PC1 | 42 | 12249 | 4084 | 1109 | 0 | True |
| cross_project__CM1__seed_101 | cross_project | CM1 | 101 | 12708 | 4236 | 498 | 0 | True |
| cross_project__JM1__seed_101 | cross_project | JM1 | 101 | 3178 | 1060 | 13204 | 0 | True |
| cross_project__KC1__seed_101 | cross_project | KC1 | 101 | 11499 | 3834 | 2109 | 0 | True |
| cross_project__KC2__seed_101 | cross_project | KC2 | 101 | 12690 | 4230 | 522 | 0 | True |
| cross_project__PC1__seed_101 | cross_project | PC1 | 101 | 12249 | 4084 | 1109 | 0 | True |

## Preprocessing Audit

- imputer: expected=200, executed=200, passed=200, failed=0
- scaler: expected=100, executed=100, passed=100, failed=0
- feature_count: expected=200, executed=200, passed=200, failed=0

## Prediction Ledger Counts

- Within rows: 34900
- Cross rows: 174430
- Finite scores: True
- Range OK: True

## Validation Reconstruction

- Rows: 600
- Categorical match: True
- Numeric mismatches: 0
- Max absolute difference: 4.440892098500626e-16
- Max relative difference: 9.689026597918819e-16

## Canonical Result Reconstruction

- Rows: 400
- Categorical match: True
- Numeric mismatches: 0
- Max absolute difference: 4.283498555857079e-08
- Max relative difference: 9.938014047236926e-08

## Selection and Test Isolation

- Candidate fitting uses training rows only (verified by construction).
- Candidate selection uses validation predictions only (verified by reconstruction).
- Threshold selection uses validation labels and predictions only.
- Soft-top-3 membership and threshold use validation data only.
- Test data are not passed to any selection function.

## Schema-Level Target Awareness

- common_schema_uses_all_project_column_names: True
- common_schema_uses_target_feature_values: False
- common_schema_uses_target_labels: False
- classification: schema-level target awareness; not target-value or target-label leakage

## Pooled-Source Validation Design

- pooled_source_validation: True
- source_project_overlap_between_train_and_validation: observed; pooled four-project source split
- classification: current canonical validation design; not target leakage, but a transfer-robustness limitation

## Duplicate Content Analysis

- Cross-project duplicate feature groups: 66
- Cross-project duplicate content groups: 64
- Duplicate feature-label conflict groups: 121
- Requires duplicate sensitivity in Part 3F: True

## Preservation Evidence

- Files checked: 19
- Files changed: 0

## Negative Tests

- Expected: 12
- Passed: 12

- duplicate event_id/sample_uid key: validate_split_membership returned false = True (passed=True)
- same sample identity in train and test: validate_split_membership returned false = True (passed=True)
- same sample identity in validation and test: validate_split_membership returned false = True (passed=True)
- target-project row inserted into cross-project train: validate_split_membership returned false = True (passed=True)
- source-project row inserted into cross-project test: validate_split_membership returned false = True (passed=True)
- one target-project row removed from a within-project event union: validate_split_membership returned false = True (passed=True)
- training row inserted into prediction ledger: validate_prediction_ledger returned false = True (passed=True)
- duplicate event_id/split_role/sample_uid key: validate_prediction_ledger returned false = True (passed=True)
- one candidate score replaced by NaN: validate_prediction_ledger returned false = True (passed=True)
- one candidate score replaced by a value greater than 1: validate_prediction_ledger returned false = True (passed=True)
- mutate one numeric validation-reconstruction value: validate_validation_reconstruction returned false = True (passed=True)
- mutate one numeric canonical-result-reconstruction value: validate_result_reconstruction returned false = True (passed=True)

## Audit Checks

- source_commit_verified: True
- imported_pipeline_sha_verified: True
- dataset_profile_passed: True
- sample_registry_passed: True
- feature_schema_passed: True
- event_manifest_count_passed: True
- within_split_counts_passed: True
- cross_split_counts_passed: True
- split_membership_totals_passed: True
- split_key_uniqueness_passed: True
- split_identity_disjointness_passed: True
- within_union_coverage_passed: True
- cross_target_isolation_passed: True
- cross_source_isolation_passed: True
- split_determinism_passed: True
- class_count_consistency_passed: True
- preprocessing_train_only_passed: True
- candidate_fit_count_passed: True
- prediction_row_counts_passed: True
- prediction_key_uniqueness_passed: True
- prediction_candidate_schema_passed: True
- prediction_scores_finite_passed: True
- prediction_scores_range_passed: True
- no_train_predictions_passed: True
- validation_reconstruction_count_passed: True
- validation_categorical_match_passed: True
- validation_numeric_match_passed: True
- result_reconstruction_count_passed: True
- result_categorical_match_passed: True
- result_numeric_match_passed: True
- selection_validation_only_passed: True
- test_not_used_for_selection_passed: True
- tie_policy_passed: True
- duplicate_content_audit_completed: True
- schema_target_awareness_documented: True
- pooled_source_validation_design_documented: True
- raw_and_canonical_preservation_passed: True
- deterministic_artifacts_passed: True
- negative_tests_passed: True
- stage_gate_passed: True
- all_critical_checks_passed: True

## Stage Gate

- part3b_prediction_ledger_complete: True
- raw_data_modified: False
- canonical_outputs_modified: False
- part3a_artifacts_modified: False
- identity_leakage_detected: False
- preprocessing_leakage_detected: False
- selection_test_leakage_detected: False
- canonical_validation_reconstruction_passed: True
- canonical_result_reconstruction_passed: True
- next_authorized_stage: Part 3C
- part3c_constraint: Part 3C must consume the frozen Part 3B split and candidate-probability ledgers. It may derive objective-matched candidate, adaptive, and soft-ensemble results, but it must not alter raw data, split assignments, candidate probabilities, the canonical 400 result rows, or the canonical 600 validation rows.

## Artifact Hashes

- results/part3b_prediction_ledger/sample_registry.csv: c877c8e2589e895ffca9ca953e6309cc07105c9b142edfd8d103de8b9dbf44fd (2735784 bytes)
- results/part3b_prediction_ledger/event_manifest.csv: 89f80b9045bae96b75a074caa5d2ccc4ad0cae59f72a4c84079ceae2e7a76431 (20749 bytes)
- results/part3b_prediction_ledger/split_membership_within.csv.gz: cc9e8c99a79a7c8b880531a50419fdc6c460089cd5e5d684cd7ef4c8f77ed01d (768767 bytes)
- results/part3b_prediction_ledger/split_membership_cross.csv.gz: 1478568991c0b9661fdbc80e7b7731cc984b1e418ca9bdba07910f41e8a869ad (3904404 bytes)
- results/part3b_prediction_ledger/prediction_ledger_within.csv.gz: 52724f5194969ee5a44b9761f80508c5ef095f6f5df05eeaf1c0745f6ed8a071 (1356761 bytes)
- results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz: 1726f756c014ea2c75c023070679dd4d0b3b9ec50e7403879f29224ccbf780b5 (6587556 bytes)
- results/part3b_prediction_ledger/validation_reconstruction.csv: afc1c57c1e68cfd23b98bd20f2255e5984b187854aa883f27e8a986f6ab8a54f (202733 bytes)
- results/part3b_prediction_ledger/canonical_result_reconstruction.csv: 35e295d1b7b6b830c032a0924878cfd86e95926768c49b06b9f1e5b8ff59bd1e (153640 bytes)
