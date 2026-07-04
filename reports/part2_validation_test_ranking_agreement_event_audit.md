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
- Domain validation passed: True
- Key uniqueness passed: True

## Baseline Extraction

- Baseline rows: 200 (expected: 200)
- Baseline extraction passed: True

## Controlled Join

- Joined rows: 600 (expected: 600)
- Join validation passed: True

## Metric Mapping

- Metrics count: 14
- Metric mapping passed: True

## Selected-Candidate Provenance

- AQRPE rows checked: 150
- Selected candidate rows checked: 150
- Provenance validation passed: True
- Error count: 0

## Synthetic Non-Chaining Test

- Utilities: [1.0, 0.99999999999925, 0.9999999999985]
- Ranks: [1.5, 1.5, 3.0]
- First two in same group: True
- Third in different group: True
- Not all three same group: True
- Synthetic test passed: True

## Event Computation

- Analysis units checked: 150
- Metric rows computed: 2100
- Winner sets checked: 2100
- Rank vectors checked: 2100
- Spearman defined: 2073
- Spearman undefined: 27
- Kendall defined: 2073
- Kendall undefined: 27

## Event Validation

- Event rows: 2100 (expected: 2100)
- Event columns: 28 (expected: 28)
- Event validation passed: True
- Key duplicates: False
- Rank range OK: True
- Spearman range OK: True
- Kendall range OK: True

## Validation Checks Summary

- canonical_verification_passed: True
- input_schema_passed: True
- input_domain_passed: True
- validation_key_uniqueness_passed: True
- baseline_key_uniqueness_passed: True
- controlled_join_passed: True
- metric_mapping_passed: True
- selected_candidate_AQRPE_uniqueness_passed: True
- selected_candidate_selection_mode_passed: True
- selected_candidate_score_match_passed: True
- selected_candidate_threshold_match_passed: True
- selected_candidate_objective_membership_passed: True
- selected_candidate_no_test_leakage_passed: True
- synthetic_non_chaining_test_passed: True
- event_schema_passed: True
- event_row_count_passed: True
- event_key_uniqueness_passed: True
- winner_set_integrity_passed: True
- rank_integrity_passed: True
- agreement_identity_checks_passed: True
- correlation_state_consistency_passed: True
- correlation_range_passed: True
- input_cardinality_passed: True
- four_candidate_coverage_passed: True

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
- spearman_rows_defined: 2073
- spearman_rows_undefined: 27
- kendall_rows_defined: 2073
- kendall_rows_undefined: 27
- synthetic_tests_checked: 1
- event_rows_validated: 2100

## Interpretation Limits

Event-level analysis unit includes seed: experiment × target_project × seed × mode. For descriptive aggregation, the five seeds are repeated, non-independent runs nested within experiment × target_project × mode × metric. Seeds are not treated as iid observations for inferential testing.

Excluded inferences:
- p-value
- iid seed-based confidence interval
- significance claim
- superiority claim
- causal claim

