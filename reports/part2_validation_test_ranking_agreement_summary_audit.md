# Part 2 Section 4B.2B: Harden Summary Audit, Portability, and Computed Evidence

## Repository-Relative Execution

- Base path: /Users/aliehpourdast/Desktop/springer/springer
- Script path: /Users/aliehpourdast/Desktop/springer/springer/scripts/summarize_validation_test_ranking_agreement.py

## Input Verification

- Event CSV SHA-256 verified: True
- Event rows: 2100 (expected: 2100)
- Event columns: 28 (expected: 28)
- Column order ok: True
- Row count ok: True
- Column count ok: True
- NA state valid: True
- Finite numeric valid: True
- Boolean valid: True
- Duplicate key count: 0
- Actual event key count: 2100
- Missing event key count: 0
- Extra event key count: 0
- Input schema valid: True
- Input key coverage passed: True

## Input Audit Verification

- Input audit check count: 40
- Input audit failed check count: 0
- Input audit missing required check count: 0
- Input audit checks passed: True

## Summary Output Verification

- overall:
  - Expected rows: 1
  - Actual rows: 1

- by_experiment:
  - Expected rows: 2
  - Actual rows: 2

- by_mode:
  - Expected rows: 3
  - Actual rows: 3

- by_metric:
  - Expected rows: 14
  - Actual rows: 14

- by_project:
  - Expected rows: 5
  - Actual rows: 5

## Summary Schema Validation

- Summary schemas passed: True
- overall:
  - Expected columns: 35
  - Actual columns: 35
  - Schema mismatch count: 0
  - Passed: True

- by_experiment:
  - Expected columns: 35
  - Actual columns: 35
  - Schema mismatch count: 0
  - Passed: True

- by_mode:
  - Expected columns: 35
  - Actual columns: 35
  - Schema mismatch count: 0
  - Passed: True

- by_metric:
  - Expected columns: 35
  - Actual columns: 35
  - Schema mismatch count: 0
  - Passed: True

- by_project:
  - Expected columns: 35
  - Actual columns: 35
  - Schema mismatch count: 0
  - Passed: True

- undefined_reasons:
  - Expected columns: 3
  - Actual columns: 3
  - Schema mismatch count: 0
  - Passed: True

## Summary Domain Validation

- Group domain mismatch count: 0
- Group denominator mismatch count: 0
- Summary domains valid: True

## Correlation Undefined Reasons

- Spearman undefined count: 18 (expected: 18)
- Kendall undefined count: 18 (expected: 18)

## Undefined Reasons Validation

- Expected rows: 2
- Actual rows: 2
- Expected Spearman count: 18
- Actual Spearman count: 18
- Expected Kendall count: 18
- Actual Kendall count: 18
- Correlation domain ok: True
- Row count ok: True
- Passed: True

## Independent Validation

- Summary rows expected: 25
- Summary rows reconstructed: 25
- Complete validation rows: 25
- Incomplete validation rows: 0
- Actual field comparisons: 850
- Mismatch count: 0

## Correlation Identity Validation

- Correlation identity rows checked: 25
- Correlation identity failure count: 0
- Passed: True

## Denominator Identities

- All denominator identities passed: True
- overall: True

- by_experiment: True

- by_mode: True

- by_metric: True

- by_project: True

## Range Checks

- All range checks passed: True
- overall:
  - Count range passed: True
  - Rate range passed: True
  - Jaccard range passed: True
  - Correlation range passed: True
  - Selected rank range passed: True
  - Finite numeric values passed: True
  - Passed: True

- by_experiment:
  - Count range passed: True
  - Rate range passed: True
  - Jaccard range passed: True
  - Correlation range passed: True
  - Selected rank range passed: True
  - Finite numeric values passed: True
  - Passed: True

- by_mode:
  - Count range passed: True
  - Rate range passed: True
  - Jaccard range passed: True
  - Correlation range passed: True
  - Selected rank range passed: True
  - Finite numeric values passed: True
  - Passed: True

- by_metric:
  - Count range passed: True
  - Rate range passed: True
  - Jaccard range passed: True
  - Correlation range passed: True
  - Selected rank range passed: True
  - Finite numeric values passed: True
  - Passed: True

- by_project:
  - Count range passed: True
  - Rate range passed: True
  - Jaccard range passed: True
  - Correlation range passed: True
  - Selected rank range passed: True
  - Finite numeric values passed: True
  - Passed: True

## Deterministic Serialization

- Overall CSV identical: True
- Experiment CSV identical: True
- Mode CSV identical: True
- Metric CSV identical: True
- Project CSV identical: True
- Undefined reasons CSV identical: True
- Audit JSON identical: True
- Audit Markdown identical: N/A
- Stable output order passed: True
- Deterministic output serialization passed: False

## Interpretation Limits

- Descriptive summaries only: True
- Seeds are repeated non-independent runs: True
- No p-values: True
- No iid confidence intervals: True
- No significance claim: True
- No causal claim: True
- No superiority claim based only on agreement: True
- Test data used only for post-selection evaluation: True
- Interpretation limits present: True

## Validation Checks Summary

- input_sha_verified: True
- input_schema_valid: True
- input_key_coverage_passed: True
- input_audit_checks_passed: True
- summary_counts_correct: True
- summary_schemas_valid: True
- summary_group_domains_valid: True
- summary_group_denominators_valid: True
- correlation_undefined_counts_correct: True
- correlation_defined_identities_passed: True
- independent_validation_passed: True
- denominator_identities_passed: True
- range_checks_passed: True
- undefined_reasons_validation_passed: True
- interpretation_limits_present: True
- all_checks_passed: True

