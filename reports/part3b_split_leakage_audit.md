# Part 3B.2R Split / Leakage Audit Report

- **Version:** Part-3B.2R-v1
- **Repository:** abtinasg/springer
- **Branch:** major-revision-analysis-v2
- **Starting commit:** 653fcb3039804d91c60d19f2e0d3ad5c9bd57013
- **Accepted Part 3A commit:** d16e28488aa0936014f020c05466181eff219af6
- **Timestamp:** 1970-01-01T00:00:00

## Stage Gate

- **part3b_prediction_ledger_complete:** True
- **raw_data_modified:** False
- **canonical_outputs_modified:** False
- **part3a_artifacts_modified:** False
- **identity_leakage_detected:** False
- **preprocessing_leakage_detected:** False
- **selection_test_leakage_detected:** False
- **canonical_validation_reconstruction_passed:** True
- **canonical_result_reconstruction_passed:** True
- **canonical_result_reconstruction_strictly_identical:** False
- **canonical_result_reconstruction_scientifically_reconciled:** True
- **canonical_nondeterminism_exception_detected:** True
- **canonical_nondeterminism_exception_validated:** True
- **semantic_reproducibility_passed:** True
- **next_authorized_stage:** Part 3C
- **part3c_constraint:** Part 3C must consume the frozen Part 3B split and candidate-probability ledgers. It may derive objective-matched candidate, adaptive, and soft-ensemble results, but it must not alter raw data, split assignments, candidate probabilities, the canonical 400 result rows, or the canonical 600 validation rows.

## Audit Checks

- **source_commit_verified:** True
- **imported_pipeline_sha_verified:** True
- **dataset_profile_passed:** True
- **sample_registry_passed:** True
- **feature_schema_passed:** True
- **event_manifest_count_passed:** True
- **within_split_counts_passed:** True
- **cross_split_counts_passed:** True
- **split_membership_totals_passed:** True
- **split_key_uniqueness_passed:** True
- **split_identity_disjointness_passed:** True
- **within_union_coverage_passed:** True
- **cross_target_isolation_passed:** True
- **cross_source_isolation_passed:** True
- **split_determinism_passed:** True
- **class_count_consistency_passed:** True
- **preprocessing_train_only_passed:** True
- **candidate_fit_count_passed:** True
- **prediction_row_counts_passed:** True
- **prediction_key_uniqueness_passed:** True
- **prediction_candidate_schema_passed:** True
- **prediction_scores_finite_passed:** True
- **prediction_scores_range_passed:** True
- **no_train_predictions_passed:** True
- **validation_reconstruction_count_passed:** True
- **validation_categorical_match_passed:** True
- **validation_numeric_match_passed:** True
- **result_reconstruction_count_passed:** True
- **result_categorical_match_passed:** True
- **canonical_nondeterminism_exception_detected:** True
- **canonical_nondeterminism_exception_validated:** True
- **strict_validation_mismatches:** 0
- **strict_result_mismatches_before_exception:** 1
- **approved_nondeterminism_exceptions:** 1
- **unapproved_result_mismatches:** 0
- **result_reconstruction_passed_after_validated_exception:** True
- **result_numeric_match_passed:** True
- **canonical_result_reconstruction_strictly_identical:** False
- **canonical_result_reconstruction_scientifically_reconciled:** True
- **selection_validation_only_passed:** True
- **test_not_used_for_selection_passed:** True
- **tie_policy_passed:** True
- **duplicate_content_audit_completed:** True
- **schema_target_awareness_documented:** True
- **pooled_source_validation_design_documented:** True
- **raw_and_canonical_preservation_passed:** True
- **deterministic_artifacts_passed:** True
- **negative_tests_passed:** True
- **stage_gate_passed:** True
- **all_critical_checks_passed:** True
- **semantic_reproducibility_passed:** True
- **exact_structural_equality:** True
- **identity_columns_exact:** True
- **non_et_score_columns_exact:** True
- **maximum_et_score_difference:** 4.440892098500626e-16
- **number_of_et_cells_differing:** 0
- **selection_decisions_exact:** True
- **thresholds_exact:** True
- **non_exempt_metrics_strictly_equal:** True
- **byte_identical_artifacts:** ['results/part3b_prediction_ledger/event_manifest.csv', 'results/part3b_prediction_ledger/sample_registry.csv', 'results/part3b_prediction_ledger/split_membership_cross.csv.gz', 'results/part3b_prediction_ledger/split_membership_within.csv.gz']
- **artifacts_with_approved_et_roundoff_only:** []
- **unapproved_differing_artifacts:** ['reports/part3b_split_leakage_audit.json', 'reports/part3b_split_leakage_audit.md', 'results/part3b_prediction_ledger/ledger_manifest.json']

## Prediction Ledger Summary

- **within_total_rows:** 34900
- **cross_total_rows:** 174430
- **validation_rows:** 104670
- **test_rows:** 104660
- **train_rows:** 0
- **column_count:** 14
- **columns:** event_id, experiment, target_project, seed, split_role, split_position, sample_uid, sample_project, original_row_index, y_true, score__LR_std_C0.1, score__LR_std_C1, score__DT_leaf5, score__ET_leaf5
- **stored_threshold_or_objective_columns:** []
- **stored_aggregate_metric_columns:** []

## Reconstruction Summary

- **Validation rows:** 600
- **Canonical result rows:** 400
- **Canonical results reconstructed exclusively from scores:** True
- **Persisted ledger reconstruction matches in-memory:** True
- **Canonical nondeterminism exception validated:** True
- **Strict validation mismatches:** 0
- **Strict result mismatches before exception:** 1
- **Approved nondeterminism exceptions:** 1
- **Unapproved result mismatches:** 0
- **Canonical result reconstruction strictly identical:** False
- **Canonical result reconstruction scientifically reconciled:** True

### validation_reconstruction_evidence

- **Row count:** 600
- **Categorical match:** True
- **Numeric mismatches:** 0
- **Maximum absolute difference:** 4.440892098500626e-16
- **Maximum relative difference:** 8.608215420122814e-16

| Column | Compared | Mismatches | MaxAbs | MaxRel |
|--------|----------|------------|--------|--------|
| val_threshold | 600 | 0 | 0.0 | 0.0 |
| val_selection_score | 600 | 0 | 8.326672684688674e-17 | 7.536716382249033e-16 |
| val_avg_precision | 600 | 0 | 8.326672684688674e-17 | 5.47310662309119e-16 |
| val_roc_auc | 600 | 0 | 1.1102230246251565e-16 | 1.2126522696215335e-16 |
| val_mcc | 600 | 0 | 8.326672684688674e-17 | 7.536716382249033e-16 |
| val_f1 | 600 | 0 | 8.326672684688674e-17 | 3.955169525227122e-16 |
| val_balanced_accuracy | 600 | 0 | 1.1102230246251565e-16 | 1.2270886061646466e-16 |
| val_precision | 600 | 0 | 8.326672684688674e-17 | 3.88578058618805e-16 |
| val_recall | 600 | 0 | 1.1102230246251565e-16 | 4.22352915693245e-16 |
| val_brier | 600 | 0 | 8.326672684688674e-17 | 8.608215420122814e-16 |
| val_precision_at_10pct | 600 | 0 | 8.326672684688674e-17 | 4.255854927729769e-16 |
| val_recall_at_10pct | 600 | 0 | 8.326672684688674e-17 | 3.4972025275692445e-16 |
| val_lift_at_10pct | 600 | 0 | 4.440892098500626e-16 | 2.023261275388056e-16 |
| val_precision_at_20pct | 600 | 0 | 8.326672684688674e-17 | 4.683753385137381e-16 |
| val_recall_at_20pct | 600 | 0 | 5.551115123125783e-17 | 1.4606371667724719e-16 |
| val_lift_at_20pct | 600 | 0 | 4.440892098500626e-16 | 1.9303579914765497e-16 |

### canonical_result_reconstruction_evidence

- **Row count:** 400
- **Categorical match:** True
- **Numeric mismatches:** 1
- **Maximum absolute difference:** 4.283498544754849e-08
- **Maximum relative difference:** 6.392706981051185e-08

| Column | Compared | Mismatches | MaxAbs | MaxRel |
|--------|----------|------------|--------|--------|
| threshold | 400 | 0 | 0.0 | 0.0 |
| selection_score | 400 | 0 | 5.551115123125783e-17 | 1.911127746855028e-16 |
| avg_precision | 400 | 0 | 8.326672684688674e-17 | 7.099676344916416e-16 |
| roc_auc | 400 | 1 | 4.283498544754849e-08 | 6.392706981051185e-08 |
| mcc | 400 | 0 | 8.326672684688674e-17 | 1.9251244442694982e-15 |
| f1 | 400 | 0 | 8.326672684688674e-17 | 6.18332545659289e-16 |
| balanced_accuracy | 400 | 0 | 5.551115123125783e-17 | 1.3147377923192647e-16 |
| precision | 400 | 0 | 8.326672684688674e-17 | 1.2212453270876738e-15 |
| recall | 400 | 0 | 1.1102230246251565e-16 | 4.308722690807157e-16 |
| brier | 400 | 0 | 8.326672684688674e-17 | 1.0744788691998048e-15 |
| precision_at_10pct | 400 | 0 | 1.1102230246251565e-16 | 5.134781488891351e-16 |
| recall_at_10pct | 400 | 0 | 8.326672684688674e-17 | 1.0200174038743638e-15 |
| lift_at_10pct | 400 | 0 | 4.440892098500626e-16 | 1.8213333111646333e-16 |
| precision_at_20pct | 400 | 0 | 8.326672684688674e-17 | 9.242606680004437e-16 |
| recall_at_20pct | 400 | 0 | 5.551115123125783e-17 | 1.827942959736369e-16 |
| lift_at_20pct | 400 | 0 | 4.440892098500626e-16 | 1.9303579914765497e-16 |

## Canonical Nondeterminism Diagnostic

- **event_id:** cross_project__JM1__seed_042
- **candidate:** ET_leaf5
- **n_jobs:** 2
- **fit_count:** 1
- **prediction_calls:** 20
- **unique_score_hashes:** 12
- **unique_roc_auc_values:** 2
- **maximum_score_difference:** 4.440892098500626e-16
- **canonical_values_reproduced:** [0.6700601613088453, 0.6700602041438307]
- **n_jobs_1_unique_score_hashes:** 1
- **n_jobs_1_unique_roc_auc_values:** 1

The frozen historical pipeline contains a reproducible sub-ULP parallel prediction nondeterminism in ExtraTrees with n_jobs=2. The maximum observed candidate-score difference was 4.440892098500626e-16. This generated one historical ROC-AUC discrepancy of approximately 4.2835e-08 between two rows derived from separate prediction calls on the same fitted estimator. Part 3B freezes one score vector per event and candidate, preserving internal consistency without modifying the accepted canonical output.

## Semantic Reproducibility (Two Independent Builds)

- **Semantic reproducibility passed:** True
- **Exact structural equality:** True
- **All identity columns exact:** True
- **All non-ET score columns exact:** True
- **Maximum ET score difference:** 4.440892098500626e-16
- **Number of ET cells differing:** 0
- **All selection decisions exact:** True
- **All thresholds exact:** True
- **Byte-identical artifacts:** ['results/part3b_prediction_ledger/event_manifest.csv', 'results/part3b_prediction_ledger/sample_registry.csv', 'results/part3b_prediction_ledger/split_membership_cross.csv.gz', 'results/part3b_prediction_ledger/split_membership_within.csv.gz']
- **Artifacts with approved ET roundoff only:** []
- **Unapproved differing artifacts:** ['reports/part3b_split_leakage_audit.json', 'reports/part3b_split_leakage_audit.md', 'results/part3b_prediction_ledger/ledger_manifest.json']

## Negative Tests

| Case | Mutation | Validator | Passed |
|------|----------|-----------|--------|
| duplicate event_id/sample_uid key | append duplicate row | validate_split_membership | True |
| same sample identity in train and test | copy train uid to test row | validate_split_membership | True |
| same sample identity in validation and test | copy validation uid to test row | validate_split_membership | True |
| target-project row inserted into cross-project train | set train sample_project to target | validate_split_membership | True |
| source-project row inserted into cross-project test | set test sample_project to source | validate_split_membership | True |
| one target-project row removed from a within-project event union | drop one test row | validate_split_membership | True |
| training row inserted into prediction ledger | append a train split_role row | validate_prediction_ledger | True |
| duplicate event_id/split_role/sample_uid key | append duplicate prediction row | validate_prediction_ledger | True |
| one candidate score replaced by NaN | set score to NaN | validate_prediction_ledger | True |
| one candidate score replaced by a value greater than 1 | set score to 1.1 | validate_prediction_ledger | True |
| mutate one numeric validation-reconstruction value | add 1e-08 to one metric | validate_validation_reconstruction | True |
| mutate one numeric canonical-result-reconstruction value | add 1e-08 to one metric | validate_result_reconstruction | True |

## Canonical Exception Validator Tests

| Case | Mutation | Validator | Validated | Passed |
|------|----------|-----------|-----------|--------|
| exact approved exception passes | none | validate_canonical_nondeterminism_exception | True | True |
| changed event key fails | canonical target_project JM1 -> KC1 | validate_canonical_nondeterminism_exception | False | True |
| non-approved ET-derived deviation fails | documented roc_auc given recon + 1e-7 (exceeds approved tolerance) | validate_canonical_nondeterminism_exception | False | True |
| larger score deviation fails | canonical roc_auc increased by 1e-7 | validate_canonical_nondeterminism_exception | False | True |
| second mismatch fails | add a second 1e-8 mismatch in another row | validate_canonical_nondeterminism_exception | False | True |

## Tie Policy Tests

| Case | Description | Passed |
|------|-------------|--------|
| candidate exact tie | identical balanced objectives -> first candidate in order selected | True |
| threshold exact tie | first threshold achieving best objective is retained | True |
| soft_top3 stable tie order | equal objectives preserve candidate order for top3 | True |

## Artifact Hashes

| Artifact | SHA-256 |
|----------|---------|
| results/part3b_prediction_ledger/sample_registry.csv | c877c8e2589e895ffca9ca953e6309cc07105c9b142edfd8d103de8b9dbf44fd |
| results/part3b_prediction_ledger/event_manifest.csv | 89f80b9045bae96b75a074caa5d2ccc4ad0cae59f72a4c84079ceae2e7a76431 |
| results/part3b_prediction_ledger/split_membership_within.csv.gz | cc9e8c99a79a7c8b880531a50419fdc6c460089cd5e5d684cd7ef4c8f77ed01d |
| results/part3b_prediction_ledger/split_membership_cross.csv.gz | 1478568991c0b9661fdbc80e7b7731cc984b1e418ca9bdba07910f41e8a869ad |
| results/part3b_prediction_ledger/prediction_ledger_within.csv.gz | 03079b85039a934b2783b4473045fcdd273abdb326f163193370f2bdef6ce5f1 |
| results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz | d17de9576bdc9ce7d9e4332631e87496af5856796b36c16d3b60ae472fd0618e |
| results/part3b_prediction_ledger/validation_reconstruction.csv | f15958ccbcb5368b869e91965de82ef4332f11ed2960878ed9b630b58603d77a |
| results/part3b_prediction_ledger/canonical_result_reconstruction.csv | bcd1ec1e1ff3ec1e80775201d26633ff84b15a1025837d1658f1fb9d120fb045 |
| results/part3b_prediction_ledger/ledger_manifest.json | fce71edf53563817725f93eccd6193aa20c708c04ac6b3019fba062fbd3b7329 |
| reports/part3b_split_leakage_audit.json | 6bd7d25488f4899071e5b9b75b596d299f18b2ca5bdaa6197a8162b605a21500 |
| reports/part3b_split_leakage_audit.md | 0664217604926e7f7e2140131f615fb5dc70d16343053409b4e8bfb44ada5c58 |
