# Part 2 Section 4B.2: Validation-Test Ranking Agreement Summary Audit

## Audit Payload

# Part 2 Section 4B.2: Validation-Test Ranking Agreement Summary Audit

## Repository-Relative Execution

- Base path: /Users/aliehpourdast/Desktop/springer/springer
- Script path: /Users/aliehpourdast/Desktop/springer/springer/scripts/summarize_validation_test_ranking_agreement.py

## Input Verification

- Event CSV SHA-256 verified: True
- Event CSV SHA-256 (expected): 85314055415bbb3cca13d35c8dd65979f92c9c120e90c1c866cae722d0ad1f15
- Event CSV SHA-256 (actual): 85314055415bbb3cca13d35c8dd65979f92c9c120e90c1c866cae722d0ad1f15
- Event CSV rows: 2100
- Event CSV columns: 28
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
- Key coverage ok: True
- Input schema valid: True
- Input key coverage passed: True

## Input Audit Verification

- Input audit check count: 40
- Input audit failed check count: 0
- Input audit missing required check count: 0
- Input audit checks passed: True

## Summary Counts

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

## Summary Duplicate Group Evidence

- Summary duplicate group keys: 0
- Summary duplicate group rows: 0

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
- Defined rows with reason count: 0
- Undefined rows without reason count: 0
- Undefined reason duplicate row count: 0
- Undefined reason missing row count: 0
- Undefined reason extra row count: 0
- Undefined reason value mismatch count: 0
- Passed: True

## Independent Validation

- Summary rows expected: 25
- Summary rows reconstructed: 25
- Summary rows with complete validation: 25
- Summary rows with incomplete validation: 0
- Summary field comparisons: 850
- Summary mismatch count: 0
- Summary structural mismatch count: 0

## Correlation Identity Validation

- Correlation identity rows checked: 25
- Correlation identity failure count: 0
- Passed: True

## Denominator Identities

- Passed: True
- overall: True

- by_experiment: True

- by_mode: True

- by_metric: True

- by_project: True

## Range Checks

- Range checks passed: True
- overall:
  - Mandatory numeric non-finite count: 0
  - Count-field non-finite count: 0
  - Rate-field non-finite count: 0
  - Jaccard non-finite count: 0
  - Selected-rank non-finite count: 0
  - Correlation non-finite count: 0
  - Correlation state failure count: 0
  - Count range failure count: 0
  - Rate range failure count: 0
  - Jaccard range failure count: 0
  - Correlation range failure count: 0
  - Selected rank range failure count: 0
  - Passed: True

- by_experiment:
  - Mandatory numeric non-finite count: 0
  - Count-field non-finite count: 0
  - Rate-field non-finite count: 0
  - Jaccard non-finite count: 0
  - Selected-rank non-finite count: 0
  - Correlation non-finite count: 0
  - Correlation state failure count: 0
  - Count range failure count: 0
  - Rate range failure count: 0
  - Jaccard range failure count: 0
  - Correlation range failure count: 0
  - Selected rank range failure count: 0
  - Passed: True

- by_mode:
  - Mandatory numeric non-finite count: 0
  - Count-field non-finite count: 0
  - Rate-field non-finite count: 0
  - Jaccard non-finite count: 0
  - Selected-rank non-finite count: 0
  - Correlation non-finite count: 0
  - Correlation state failure count: 0
  - Count range failure count: 0
  - Rate range failure count: 0
  - Jaccard range failure count: 0
  - Correlation range failure count: 0
  - Selected rank range failure count: 0
  - Passed: True

- by_metric:
  - Mandatory numeric non-finite count: 0
  - Count-field non-finite count: 0
  - Rate-field non-finite count: 0
  - Jaccard non-finite count: 0
  - Selected-rank non-finite count: 0
  - Correlation non-finite count: 0
  - Correlation state failure count: 0
  - Count range failure count: 0
  - Rate range failure count: 0
  - Jaccard range failure count: 0
  - Correlation range failure count: 0
  - Selected rank range failure count: 0
  - Passed: True

- by_project:
  - Mandatory numeric non-finite count: 0
  - Count-field non-finite count: 0
  - Rate-field non-finite count: 0
  - Jaccard non-finite count: 0
  - Selected-rank non-finite count: 0
  - Correlation non-finite count: 0
  - Correlation state failure count: 0
  - Count range failure count: 0
  - Rate range failure count: 0
  - Jaccard range failure count: 0
  - Correlation range failure count: 0
  - Selected rank range failure count: 0
  - Passed: True

## Interpretation Limits

- Descriptive summaries only: True
- Seeds are repeated non-independent runs: True
- No p-values: True
- No iid confidence intervals: True
- No significance claim: True
- No causal claim: True
- No superiority claim based only on agreement: True
- Test data post-selection only: True
- Present: True

## Synthetic NaN Tests

- Synthetic NaN tests expected: 7
- Synthetic NaN tests executed: 7
- Synthetic NaN tests passed: 7
- Synthetic NaN test failures: 0
- NaN and undefined-state fail-safe passed: True

## Serialization Audit

- Overall CSV serialization identical: True
- Experiment CSV serialization identical: True
- Mode CSV serialization identical: True
- Metric CSV serialization identical: True
- Project CSV serialization identical: True
- Undefined reasons CSV serialization identical: True
- Audit payload JSON serialization identical: True
- Audit payload Markdown serialization identical: True
- Stable output order passed: True
- Deterministic output serialization passed: True

## Validation Checks

- input sha verified: True
- input schema valid: True
- input key coverage passed: True
- input audit checks passed: True
- summary counts correct: True
- summary schemas valid: True
- summary group domains valid: True
- summary group denominators valid: True
- correlation undefined counts correct: True
- correlation defined identities passed: True
- independent validation passed: True
- denominator identities passed: True
- range checks passed: True
- undefined reasons validation passed: True
- interpretation limits present: True
- deterministic output serialization passed: True
- nan and undefined state fail safe passed: True
- output integrity ready passed: True
- all checks passed: True

