# Part 2 Section 4A: Validation-Test Ranking Agreement Methodology Specification

**Stage:** Specification and audit design only  
**Base Commit:** 1600bc2f3c6e7af70415042133170139ce173550  
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

### Keys

**Validation Log Key:**
- experiment
- target_project
- seed
- mode
- candidate

**Baseline Test Results Key:**
- experiment
- target_project
- seed
- model

### Join Condition

```
validation_log.candidate == repeated_all_results.model
```

### Join Characteristics

- **Type:** Controlled many-to-one from validation to baseline test row
- **Filter:** Only four baseline models included in join
- **Expected Cardinalities:**
  - Validation rows: 600
  - Baseline repeated-result rows: 200
  - Joined candidate rows: 600
- **Coverage:** Exactly four candidates per analysis unit

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

- **brier:** Lower is better
- **All other metrics:** Higher is better

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

---

## Agreement Measures

For each analysis unit and metric, the following measures will be computed:

### Strict Top-1 Exact Agreement
True only when both validation and test winner sets are single-member and contain the same candidate.

### Winner Set Exact Agreement
Validation winner set exactly equals test winner set.

### Tie-Aware Winner Set Overlap
Jaccard similarity between validation winner set and test winner set.

### Winner Set Any Overlap
Intersection of two winner sets is non-empty.

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
- strict_top1_exact_agreement
- winner_set_exact_agreement
- winner_set_jaccard
- winner_set_any_overlap
- spearman_rho
- spearman_defined
- kendall_tau_b
- kendall_defined
- mode_selected_candidate
- selected_candidate_test_rank
- selected_candidate_in_test_winner_set

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

Seeds are **not** treated as independent observations for inference. They are considered repeated measurements within analysis units.

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
13. Selected-candidate provenance agreement validation
14. Tie-policy consistency validation
15. No test information used for candidate selection validation

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
