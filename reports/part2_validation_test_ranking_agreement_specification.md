# Part 2 Section 4A: Validation-Test Ranking Agreement Methodology Specification

**Stage:** Specification and audit design only  
**Base Commit:** 26f638598f77cbae56c3ea4fb92c58736f56ca2a  
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

### Rank Direction

- **Rank 1** always represents best performance
- **Brier score:** Ascending rank (lower value = better rank)
- **All other metrics:** Descending rank (higher value = better rank)

### Tie Handling

Ties are managed with average ranks.

### Correlation Computation

- **Spearman:** Computed on two rank vectors of four candidates
- **Kendall:** Uses tau-b to support ties

### Correlation Tie Policy

- Main correlations are based on tolerance-aware ranks
- Tolerance groups are built by comparison to ordered performance levels
- No deterministic candidate order should break real ties

If tolerance-aware full ranking implementation in 4B requires a distinct algorithm, that algorithm will be specified in the stage 4B specification.

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

### Undefined Correlation Policy

If correlation is undefined due to constant ranking:
- Record NA
- Record reason for undefined
- Do not fabricate a zero value

**Rules:**
- If defined: reason must be null
- If undefined: correlation value must be null and reason must be non-null
- Zero must not be substituted for undefined

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
14. Selected-candidate provenance agreement validation
15. Tie-policy consistency validation
16. No test information used for candidate selection validation

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
