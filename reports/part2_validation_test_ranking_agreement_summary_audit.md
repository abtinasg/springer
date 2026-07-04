# Part 2 Section 4B.2A: Validation-Test Ranking Agreement Summary Audit

## Input Verification

- Event CSV SHA-256 verified: True
- Event rows: 2100 (expected: 2100)
- Event columns: 28 (expected: 28)
- Duplicate keys: 0
- Missing keys: 0
- Extra keys: 0
- Audit validation checks passed: True

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

## Correlation Undefined Reasons

- Spearman undefined count: 18 (expected: 18)
- Kendall undefined count: 18 (expected: 18)

## Independent Validation

- Summary rows expected: 25
- Summary rows reconstructed: 25
- Complete validation rows: 25
- Incomplete validation rows: 0
- Actual field comparisons: 850
- Mismatch count: 0

## Denominator Identities

- All denominator identities passed: True
- overall: True

- by_experiment: True

- by_mode: True

- by_metric: True

- by_project: True

## Range Checks

- All range checks passed: True
- overall: True

- by_experiment: True

- by_mode: True

- by_metric: True

- by_project: True

## Validation Checks Summary

- input_sha_verified: True
- input_schema_valid: True
- audit_checks_passed: True
- summary_counts_correct: True
- correlation_undefined_counts_correct: True
- independent_validation_passed: True
- denominator_identities_passed: True
- range_checks_passed: True
- all_checks_passed: True

