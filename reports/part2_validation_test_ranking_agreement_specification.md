# Part 2 Section 4A: Validation-Test Ranking Agreement Methodology Specification

**Stage:** Specification and audit design only  
**Base Commit:** b2c1118b832674bf881176bcc5d81cd009a832d2  
**Scope:** This stage defines the methodology only. No ranking computation, analytical CSVs, numeric results, charts, or scientific conclusions are generated.

---

## Purpose

This specification defines the methodology for analyzing agreement between validation-set rankings and test-set rankings across multiple evaluation metrics. The analysis will quantify how well models selected based on validation performance generalize to test performance.

**Important:** This document is a design specification. No results have been computed yet.

---

## Canonical Inputs

- `results/part1_full_reproduction/validation_log.csv` - Validation-set performance rankings
- `results/part1_full_reproduction/repeated_all_results.csv` - Test-set performance results
- `reports/part1_canonical_manifest.json` - SHA-256 verification and provenance

---

## Analysis Unit

The fundamental unit of analysis is:

```
experiment × target_project × seed × mode
```

### Expected Dimensions

- **Experiments:** 2 (within_project, cross_project)
- **Projects:** 5 (CM1, JM1, KC1, KC2, PC1)
- **Seeds:** 5 (7, 13, 29, 42, 101)
- **Modes:** 3 (balanced, rank, mcc)
- **Total Units:** 150

Each analysis unit contains exactly four baseline candidates:

- LR_std_C0.1
- LR_std_C1
- DT_leaf5
- ET_leaf5

---

## Mode Mapping

| Validation Mode | AQRPE Model |
|----------------|--------------|
| balanced | AQRPE_v2_balanced |
| rank | AQRPE_v2_rank |
| mcc | AQRPE_v2_mcc |

The selected candidate for each mode will be verified against both:
1. Validation provenance (validation_log.csv)
2. AQRPE top-1 row (repeated_all_results.csv)

---

## Join Specification

### Composite Join Keys

The join uses the following composite keys:

```
validation_log.experiment == repeated_all_results.experiment
validation_log.target_project == repeated_all_results.target_project
validation_log.seed == repeated_all_results.seed
validation_log.candidate == repeated_all_results.model
```

### Mode Handling

Mode is retained from `validation_log` and is not part of the unique baseline test key.

### Baseline Test Key Uniqueness

The baseline test table is unique on the key:
```
experiment × target_project × seed × model
```

### Validation to Baseline Mapping

Each baseline test row is used in a controlled manner across three validation modes.

### Join Cardinality

- **Validation rows:** 600
- **Unique baseline test rows:** 200
- **Join output:** Exactly 600 rows (no Cartesian expansion)
- **Unexpected many-to-many join:** Forbidden

### Expected Join Rows

The join from 600 validation rows to 200 unique baseline test rows produces exactly 600 rows.

---

## Metrics

Fourteen metrics will be analyzed:

1. avg_precision
2. roc_auc
3. mcc
4. f1
5. balanced_accuracy
6. precision
7. recall
8. brier
9. precision_at_10pct
10. recall_at_10pct
11. lift_at_10pct
12. precision_at_20pct
13. recall_at_20pct
14. lift_at_20pct

### Metric Directions

Each of the 14 metrics is explicitly mapped:

- **avg_precision:** Higher is better
- **roc_auc:** Higher is better
- **mcc:** Higher is better
- **f1:** Higher is better
- **balanced_accuracy:** Higher is better
- **precision:** Higher is better
- **recall:** Higher is better
- **brier:** Lower is better
- **precision_at_10pct:** Higher is better
- **recall_at_10pct:** Higher is better
- **lift_at_10pct:** Higher is better
- **precision_at_20pct:** Higher is better
- **recall_at_20pct:** Higher is better
- **lift_at_20pct:** Higher is better

### Metric Column Mapping

Each metric has explicit validation and test column mappings:

| Metric | Validation Column | Test Column |
|--------|-------------------|-------------|
| avg_precision | val_avg_precision | avg_precision |
| roc_auc | val_roc_auc | roc_auc |
| mcc | val_mcc | mcc |
| f1 | val_f1 | f1 |
| balanced_accuracy | val_balanced_accuracy | balanced_accuracy |
| precision | val_precision | precision |
| recall | val_recall | recall |
| brier | val_brier | brier |
| precision_at_10pct | val_precision_at_10pct | precision_at_10pct |
| recall_at_10pct | val_recall_at_10pct | recall_at_10pct |
| lift_at_10pct | val_lift_at_10pct | lift_at_10pct |
| precision_at_20pct | val_precision_at_20pct | precision_at_20pct |
| recall_at_20pct | val_recall_at_20pct | recall_at_20pct |
| lift_at_20pct | val_lift_at_20pct | lift_at_20pct |

**Audit requirements:**
- `set(metric_column_mapping.keys()) == set(metrics)`
- All validation_column values must exist in validation_log
- All test_column values must exist in baseline test table
- No metric discovery via positional matching or automatic `val_` prefix removal

---

## Tie Policy

Two types of ties are defined:

### Exact Tie
Values are exactly equal.

### Tolerance-Aware Tie
Absolute difference ≤ 1e-12.

### Winner Set Handling

- Winner sets preserve all tied candidates
- Deterministic candidate ordering is allowed for display only
- Winner sets are never artificially reduced to a single winner
- Tolerance winner set is not built via pairwise chaining or candidate ordering

### Exact Winner Set Definition

All candidates whose metric value is exactly equal to the optimum.

### Tolerance Winner Set Definition

All candidates whose distance from the optimum is at most 1e-12.

For higher-is-better metrics:
```
best_value - candidate_value <= 1e-12
```

For lower-is-better metrics:
```
candidate_value - best_value <= 1e-12
```

---

## Rank Policy

### Canonical Candidate Order

The canonical candidate order is:
```
LR_std_C0.1
LR_std_C1
DT_leaf5
ET_leaf5
```

This order is used **only** for alignment and serialization. It must not be used for tie-breaking.

### Utility Construction

For each metric, a utility value is computed:

- **Higher-is-better metrics:** `utility = metric_value`
- **Lower-is-better metrics (Brier):** `utility = -metric_value`

### Exact Rank Algorithm

1. Compute utility for each candidate based on metric direction
2. Sort candidates by utility in descending order
3. Group candidates with exactly equal utility values
4. Assign rank to each group as the average ordinal positions of its members
5. Rank 1 always represents best performance (highest utility)

### Tolerance-Aware Rank Algorithm

1. Compute utility for each candidate based on metric direction
2. Sort candidates by utility in descending order
3. Start with the best ungrouped candidate as anchor
4. `anchor_utility` is the fixed reference value for the current group
5. Subsequent candidates join the same group only if: `anchor_utility - candidate_utility <= 1e-12`
6. Comparison to the last group member is **forbidden**
7. Pairwise chaining is **forbidden**
8. When the first candidate is outside anchor tolerance, close the group
9. Next candidate becomes anchor for new group
10. Assign rank to each group as the average ordinal positions of its members
11. Candidate order must not be used to extend tie groups

### Synthetic Audit Example

**Utility values:**
- 1.0
- 1.0 - 0.75e-12
- 1.0 - 1.50e-12

**Expected result:**
- First and second candidates in one tolerance group
- Third candidate in next group

**Non-chaining rule:** Even if the distance between the second and third candidates is less than or equal to tolerance, chaining must not group all three together.

### Candidate Vector Alignment

The validation rank vector and test rank vector are aligned with the fixed order:
```
["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
```

This alignment is for coordinate alignment only, not tie-breaking.

**Spearman:** Computed on two tolerance-aware average-rank vectors with fixed alignment order.

**Kendall:** Kendall tau-b computed on the same two tolerance-aware rank vectors with fixed alignment order.

No missing or extra candidates are allowed in rank vectors.

---

## Agreement Measures

For each analysis unit and metric, the following measures will be computed:

### Strict Top-1 Agreement (Exact)
True only when both validation and test winner sets (exact) are single-member and contain the same candidate.

### Strict Top-1 Agreement (Tolerance)
True only when both validation and test winner sets (tolerance) are single-member and contain the same candidate.

### Winner Set Equal (Exact)
Validation winner set (exact) exactly equals test winner set (exact).

### Winner Set Equal (Tolerance)
Validation winner set (tolerance) exactly equals test winner set (tolerance).

### Winner Set Jaccard (Exact)
Jaccard similarity between validation winner set (exact) and test winner set (exact).

### Winner Set Jaccard (Tolerance)
Jaccard similarity between validation winner set (tolerance) and test winner set (tolerance).

### Winner Set Any Overlap (Exact)
Intersection of validation winner set (exact) and test winner set (exact) is non-empty.

### Winner Set Any Overlap (Tolerance)
Intersection of validation winner set (tolerance) and test winner set (tolerance) is non-empty.

### Selected Candidate in Test Winner Set (Exact)
Mode-selected candidate is in test winner set (exact).

### Selected Candidate in Test Winner Set (Tolerance)
Mode-selected candidate is in test winner set (tolerance).

### Spearman Correlation
Correlation on ranks of four candidates, with average ranks for ties.

### Kendall Correlation
Kendall tau-b to support ties.

### Selected Candidate Test Rank
Rank of the mode-selected candidate in the test ranking for the same metric. Average rank is recorded if tied.

**Basis:** `test_tolerance_aware_average_rank`

**Tolerance group handling:** If the candidate is in a multi-member tolerance group, the average rank of that group is recorded.

### Undefined Correlation Policy

Correlation is undefined when the validation rank vector or test rank vector has zero variance (all four candidates have the same rank in one of the vectors).

**Allowed reasons:**
- `validation_rank_vector_constant`
- `test_rank_vector_constant`
- `both_rank_vectors_constant`

**If defined:**
- `defined = true`
- `value = finite number`
- `undefined_reason = null`

**If undefined:**
- `defined = false`
- `value = null`
- `undefined_reason = one of the allowed_reasons values`

Zero must not be substituted for undefined.

---

## Planned Computation Grain

### Event-Level Output

Expected rows: 2,100 (150 units × 14 metrics)

Each row will include:

- experiment
- target_project
- seed
- mode
- metric
- metric_direction
- validation_winner_set_exact
- validation_winner_set_tolerance
- test_winner_set_exact
- test_winner_set_tolerance
- strict_top1_agreement_exact
- strict_top1_agreement_tolerance
- winner_set_equal_exact
- winner_set_equal_tolerance
- winner_set_jaccard_exact
- winner_set_jaccard_tolerance
- winner_set_any_overlap_exact
- winner_set_any_overlap_tolerance
- spearman_rho
- spearman_defined
- spearman_undefined_reason
- kendall_tau_b
- kendall_defined
- kendall_undefined_reason
- mode_selected_candidate
- selected_candidate_test_rank
- selected_candidate_in_test_winner_set_exact
- selected_candidate_in_test_winner_set_tolerance

**Note:** This schema is defined for future computation. No event-level file is created in this stage.

---

## Summary Design

Future summaries will be descriptive at the following scopes:

- overall
- by experiment
- by mode
- by metric
- by target_project

### Seed Assumption

The event-level analysis unit includes seed:
```
experiment × target_project × seed × mode
```

For descriptive aggregation, the five seeds are repeated, non-independent runs nested within:
```
experiment × target_project × mode × metric
```

Seeds are not treated as iid observations for inferential testing.

**Consequences:**
- Event rows include seed
- Summary may perform descriptive aggregation across seeds
- No p-value or iid confidence interval will be produced

### Excluded Inferences

The following will **not** be proposed or computed:

- p-values
- Confidence intervals based on iid seeds
- Significance claims
- Superiority claims
- Causal claims

---

## Selected Candidate Provenance

### Source

The scalar selected candidate is sourced from the AQRPE row corresponding to the mode in `repeated_all_results.csv`.

### Mode Mapping

| Validation Mode | AQRPE Model |
|----------------|--------------|
| balanced | AQRPE_v2_balanced |
| rank | AQRPE_v2_rank |
| mcc | AQRPE_v2_mcc |

### AQRPE Unique Key

The unique key for an AQRPE row is:
```
experiment × target_project × seed × model
```

**Expected uniqueness:** Exactly one AQRPE row must exist for each analysis unit and mapped model.

### Mode Selected Candidate Source

The `mode_selected_candidate` is taken from the `selected_candidate` column of the AQRPE row.

### Validation Verification

The selected candidate is verified against `validation_log.csv`:

1. **Candidate domain check:** `selected_candidate` must be in the candidate domain
2. **Validation row existence:** Exactly one validation row must exist for the same `experiment`, `target_project`, `seed`, `mode`, and `selected_candidate`
3. **Selection score match:** `abs(repeated_AQRPE.selection_score - validation_row.val_selection_score) <= 1e-12`
4. **Objective direction:** `val_selection_score` is treated as a higher-is-better objective for all three modes
5. **Winner set membership:** Selected candidate must be a member of the tolerance-aware maximum set for `val_selection_score` of the same mode
6. **Multi-member winner set handling:** If the objective winner set has multiple members, the scalar selected candidate must be one of them
7. **Tie-break exclusion:** The tie-break scalar from the canonical AQRPE row must not be used for winner sets of the 14 metrics

### Test Leakage Prohibition

No test metric is used to extract or validate candidate selection.

---

## Pre-Computation Audit Design

Before computation in stage 4B, the following checks will be performed:

1. Canonical manifest status verification
2. Direct SHA-256 verification of input files
3. Exact input schema validation
4. Exact input row count validation
5. Null value checks
6. Duplicate key checks
7. Expected experiment/project/seed/mode/candidate domain validation
8. Exact four-candidate coverage per unit validation
9. One-to-one baseline test key coverage validation
10. 600-row joined candidate coverage validation
11. Metric presence and numeric type validation
12. Metric-direction mapping completeness validation
13. Metric-direction key set validation (set(metric_directions.keys()) == set(metrics))
14. Metric column mapping key set validation (set(metric_column_mapping.keys()) == set(metrics))
15. Validation metric column presence validation
16. Test metric column presence validation
17. Candidate vector alignment validation
18. Tolerance rank anchor algorithm validation
19. Tolerance rank non-chaining synthetic test
20. Selected candidate unique AQRPE row validation
21. Selected candidate selection score match validation
22. Selected candidate objective winner membership validation
23. Selected candidate no test leakage validation
24. Selected-candidate provenance agreement validation
25. Tie-policy consistency validation
26. No test information used for candidate selection validation

---

## Interpretation Limits

### Test Data Usage

Test data will **only** be used for post-selection evaluation. No test information will influence candidate selection.

### Tie Preservation

Ties are preserved in winner sets. No artificial tie-breaking is performed for analysis.

### Brier Score Direction

Brier score has reverse direction (lower is better) compared to all other metrics (higher is better).

### Scope of Conclusions

This analysis describes agreement between validation and test rankings. It does not establish:
- Predictive performance stability
- Statistical significance
- Model superiority
- Causal relationships

---

## Computation Status

**Computation Performed:** false

This specification defines the methodology for future implementation in stage 4B. No results have been generated.
