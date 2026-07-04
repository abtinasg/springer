# Part 2 Section 4B.1: Event-Level Validation-Test Ranking Agreement Audit

## Canonical Verification

- Manifest validation status: all_checks_passed
- Validation log SHA-256 match: True
- Repeated results SHA-256 match: True
- Script SHA-256 match: True

## Input Validation

- Validation rows: 600 (expected: 600)
- Validation columns: 21 (expected: 21)
- Repeated results rows: 400 (expected: 400)
- Repeated results columns: 22 (expected: 22)
- Schema validation passed: True
- Numeric/finite validation passed: True
- Domain validation passed: True
- Key uniqueness passed: True

## Baseline Extraction

- Baseline rows: 200 (expected: 200)
- Baseline extraction passed: True

## Controlled Join

- Joined rows: 600 (expected: 600)
- Matched join rows: 600
- Join validation passed: True

## Four-Candidate Coverage

- Validation units with exact four candidates: 150 (expected: 150)
- Joined units with exact four candidates: 150 (expected: 150)
- Candidate set mismatches: 0
- Coverage validation passed: True

## Metric Mapping

- Metrics count: 14
- Metric mapping passed: True

## Selected-Candidate Provenance

- AQRPE rows checked: 150
- Selected candidate rows checked: 150
- Selection mode mismatches: 0
- Domain mismatches: 0
- Score mismatches: 0
- Threshold mismatches: 0
- Rank threshold mismatches: 0
- Objective membership mismatches: 0
- Test metric columns used for selection: 0
- Provenance validation passed: True

## Ranking Algorithm Tests

### Permutation Rank Test
- Utilities: [0.1, 0.2, 0.3, 0.4]
- Exact ranks: [4.0, 3.0, 2.0, 1.0]
- Tolerance ranks: [4.0, 3.0, 2.0, 1.0]
- Expected ranks: [4.0, 3.0, 2.0, 1.0]
- Passed: True

### Exact Tie Rank Test
- Utilities: [0.2, 0.4, 0.4, 0.1]
- Exact ranks: [3.0, 1.5, 1.5, 4.0]
- Expected ranks: [3.0, 1.5, 1.5, 4.0]
- Passed: True

### Synthetic Non-Chaining Test
- Utilities: [1.0, 0.99999999999925, 0.9999999999985]
- Ranks: [1.5, 1.5, 3.0]
- Expected ranks: [1.5, 1.5, 3.0]
- First two same group: True
- Third different group: True
- Not all three same group: True
- Test passed: True

## Event Computation

- Analysis units checked: 150
- Metric rows computed: 2100
- Winner sets checked: 2100
- Rank vectors checked: 2100
- Spearman defined: 2082
- Spearman undefined: 18
- Kendall defined: 2082
- Kendall undefined: 18

## Event Validation

- Event rows: 2100 (expected: 2100)
- Event columns: 28 (expected: 28)
- Column order ok: True
- Event validation passed: True
- Key duplicates: False
- Rank range OK: True
- Spearman range OK: True
- Kendall range OK: True

## Event Key Coverage

- Expected event key count: 2100
- Actual event key count: 2100
- Duplicate event key count: 0
- Missing event key count: 0
- Extra event key count: 0
- Event key coverage passed: True

## Winner Set Integrity

- Rows checked: 2100
- Empty sets: 0
- Unknown candidates: []
- Duplicate members: 0
- Serialization order violations: 0
- Exact not subset tolerance: 0
- Winner set integrity passed: True

## Correlation State Consistency

- Rows checked: 2100
- Defined without value: 0
- Undefined with value: 0
- Undefined without reason: 0
- Undefined invalid reason: 0
- Defined with reason: 0
- Non-finite defined value: 0
- Value out of range: 0
- Correlation state consistency passed: True

## Event Row Reconstruction

- Event rows reconstructed: 2100
- Event rows with exact 23 comparisons: 2100
- Event rows with incomplete comparisons: 0
- Fields checked per row: 23
- Total field comparisons: 48300
- Reconstruction mismatch count: 0
- Structural reconstruction failures: 0
- String mismatches: 0
- Boolean mismatches: 0
- Missing state mismatches: 0
- Exact value mismatches: 0
- Tolerance value mismatches: 0
- Candidate alignments checked: 2100
- Candidate alignment failures: 0
- Event reconstruction passed: True

## Agreement Identity Validation

- Agreement rows checked: 2100
- Agreement fields checked: 21000
- Agreement identity mismatch count: 0
- Agreement identity checks passed: True

## Rank Identity Validation

- Exact rank vectors reconstructed: 4200
- Tolerance rank vectors reconstructed: 4200
- Total rank vectors reconstructed: 8400
- Exact rank vectors independently checked: 4200
- Exact rank-group mismatches: 2288
- Exact rank identity failures: 0
- Tolerance rank identity failures: 0
- Exact winner-rank identity failures: 0
- Tolerance winner-rank identity failures: 0
- Non-chaining vectors checked: 4200
- Non-chaining identity failures: 0
- Rank structural failures: 0
- Candidate alignments checked: 2100
- Candidate alignment failures: 0
- Rank integrity passed: True

## Correlation Value Reconstruction

- Correlation rows reconstructed: 2100
- Correlation rows fully checked: 2100
- Correlation structural failures: 0
- Spearman reconstruction mismatches: 0
- Kendall reconstruction mismatches: 0
- Correlation state mismatches: 0
- Candidate alignments checked: 2100
- Candidate alignment failures: 0
- Correlation value reconstruction passed: True

## Selected Candidate Test Rank Validation

- Selected-rank rows seen: 2100
- Selected test ranks checked: 2100
- Selected-rank structural failures: 0
- Selected-rank alignment failures: 0
- Selected test rank mismatches: 0
- Selected candidate test rank passed: True

## Deterministic Serialization

- Stable event ordering rows checked: 2100
- Stable event ordering passed: True
- CSV serialization identical: True
- JSON serialization identical: True
- Deterministic serialization ready passed: True

## Validation Checks Summary

- canonical_verification_passed: True
- input_schema_passed: True
- input_numeric_finite_passed: True
- input_domain_passed: True
- validation_key_uniqueness_passed: True
- repeated_key_uniqueness_passed: True
- baseline_key_uniqueness_passed: True
- controlled_join_passed: True
- four_candidate_coverage_passed: True
- metric_mapping_passed: True
- selected_candidate_AQRPE_uniqueness_passed: True
- selected_candidate_selection_mode_passed: True
- selected_candidate_domain_passed: True
- selected_candidate_validation_row_uniqueness_passed: True
- selected_candidate_score_match_passed: True
- selected_candidate_threshold_match_passed: True
- selected_candidate_rank_threshold_passed: True
- selected_candidate_objective_membership_passed: True
- selected_candidate_no_test_leakage_passed: True
- permutation_rank_test_passed: True
- exact_tie_rank_test_passed: True
- synthetic_non_chaining_test_passed: True
- event_schema_passed: True
- event_row_count_passed: True
- event_key_uniqueness_passed: True
- winner_set_integrity_passed: True
- correlation_state_consistency_passed: True
- event_reconstruction_passed: True
- agreement_identity_checks_passed: True
- rank_integrity_passed: True
- correlation_value_reconstruction_passed: True
- selected_candidate_test_rank_passed: True
- input_cardinality_passed: True
- correlation_range_passed: True
- deterministic_serialization_ready_passed: True
- output_integrity_ready_passed: True

## Evidence Counters

- validation_rows_checked: 600
- baseline_rows_checked: 200
- AQRPE_rows_checked: 150
- analysis_units_checked: 150
- joined_rows_checked: 600
- metric_rows_computed: 2100
- selected_candidate_rows_checked: 150
- winner_sets_checked: 2100
- rank_vectors_checked: 2100
- spearman_rows_defined: 2082
- spearman_rows_undefined: 18
- kendall_rows_defined: 2082
- kendall_rows_undefined: 18
- synthetic_tests_checked: 3
- event_rows_validated: 2100
- event_rows_reconstructed: 2100
- event_rows_with_exact_23_comparisons: 2100
- event_rows_with_incomplete_comparisons: 0
- event_fields_checked_per_row: 23
- event_total_field_comparisons: 48300
- event_reconstruction_mismatch_count: 0
- structural_reconstruction_failure: 0
- string_mismatches: 0
- boolean_mismatches: 0
- missing_state_mismatches: 0
- exact_value_mismatches: 0
- tolerance_value_mismatches: 0
- reconstruction_candidate_alignments_checked: 2100
- reconstruction_candidate_alignment_failures: 0
- agreement_rows_checked: 2100
- agreement_fields_checked: 21000
- agreement_identity_mismatch_count: 0
- exact_rank_vectors_reconstructed: 4200
- tolerance_rank_vectors_reconstructed: 4200
- total_rank_vectors_reconstructed: 8400
- exact_rank_identity_failures: 0
- tolerance_rank_identity_failures: 0
- exact_winner_rank_identity_failures: 0
- tolerance_winner_rank_identity_failures: 0
- non_chaining_identity_failures: 0
- rank_candidate_alignments_checked: 2100
- rank_candidate_alignment_failures: 0
- correlation_rows_reconstructed: 2100
- spearman_reconstruction_mismatches: 0
- kendall_reconstruction_mismatches: 0
- correlation_state_mismatches: 0
- correlation_candidate_alignments_checked: 2100
- correlation_candidate_alignment_failures: 0
- selected_test_ranks_checked: 2100
- selected_test_rank_mismatches: 0

