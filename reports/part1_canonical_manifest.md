# Part 1 Section 6F: Canonical Reproduction Manifest

## Canonical Policy

**Canonical result source:** `results/part1_full_reproduction`

**Canonical table source:** `results/part1_full_reproduction_tables`

**Legacy reference source:** `results`

**Legacy reference status:** retained_but_noncanonical

**Canonical decision basis:**

- The tracked executable does not reproduce the legacy reference results.
- The exact executable that generated the legacy reference results is not available in tracked Git history.
- Two independent runs in the locked environment are numerically equivalent.
- No non-numeric repeatability differences were detected.
- Soft-top-3 qualitative outcomes versus the best baseline are unchanged across all 16 setting-metric combinations.

## Validation Checks

Manifest inventory validation status: all_checks_passed

The following validation checks were performed before freezing the canonical set:

- part1_reproduction_comparison overall_status: `materially_different`
- part1_repeatability_comparison overall_status: `numerically_equivalent`
- part1_result_drift_analysis total_combinations: 16
- part1_result_drift_analysis soft_top3_outcome_changes: 0
- part1_result_drift_analysis best_overall_disjoint_winner_changes: 0
- part1_reference_provenance_audit verified: True

## Environment and Code Files

| File | Exists | SHA-256 | Size |
|------|--------|---------|------|
| requirements_locked.txt | True | 1d7cdfba46d87a52... | 93 |
| run_repeated_evaluation.py | True | d385b6ecef2427c8... | 20162 |
| make_manuscript_tables.py | True | 152f4568025420bf... | 3729 |

## Raw Datasets

| Dataset | Exists | Rows | Columns | Null Count |
|---------|--------|-------|---------|------------|
| cm1.csv | True | 498 | 22 | 0 |
| jm1.csv | True | 13204 | 22 | 0 |
| kc1.csv | True | 2109 | 22 | 0 |
| kc2.csv | True | 522 | 22 | 0 |
| pc1.csv | True | 1109 | 22 | 0 |

## Canonical Reproduction Outputs

| File | Exists | SHA-256 | Size | Rows | Columns | Duplicates | Nulls |
|------|--------|---------|------|------|---------|------------|-------|
| dataset_profile.csv | True | 486b6c38749a8d0a... | 225 | 5 | 5 | 0 | 0 |
| decision_metadata.json | True | bd446ccbb5571bfe... | 600 | N/A | N/A | N/A | N/A |
| repeated_all_results.csv | True | 76b430031a944708... | 141632 | 400 | 22 | 0 | 0 |
| repeated_results_workbook.xlsx | True | 0674e0a290d716b0... | 161846 | N/A | N/A | N/A | N/A |
| repeated_summary_mean_std.csv | True | b6f27ee32e350e23... | 11273 | 16 | 52 | 0 | 0 |
| validation_log.csv | True | d18dbb6b7a71f356... | 187902 | 600 | 21 | 0 | 0 |

## Canonical Manuscript Tables

| Table | Exists | SHA-256 | Size | Rows | Columns | Key Duplicates | Nulls |
|-------|--------|---------|------|------|---------|-----------------|-------|
| table_within_project_mean_sd.csv | True | cccaeb1553ac942d... | 771 | 8 | 7 | 0 | 0 |
| table_cross_project_mean_sd.csv | True | 1753444c5b8a0c3a... | 771 | 8 | 7 | 0 | 0 |
| table_soft_top3_delta_vs_best_baseline.csv | True | bf5cac180bf97012... | 1423 | 16 | 8 | 0 | 0 |

## Legacy-Reference Status

The legacy reference files in `results` are retained but marked as non-canonical.

These files are preserved for historical reference and comparison purposes only.

## Scientific Interpretation Limits

**This manifest establishes computational provenance and repeatability.**

**It does not establish statistical significance or external validity.**

The canonical results represent the output of a specific computational pipeline under controlled conditions.
Any scientific claims about model performance should be supported by appropriate statistical analysis
and validation on independent datasets.

