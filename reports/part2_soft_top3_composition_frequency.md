# Part 2 Section 3A: Soft-Top-3 Composition Frequency Analysis

## Canonical Verification

- Manifest validation status: all_checks_passed
- SHA-256 verified: True

## Soft-Top-3 Algorithm Provenance

- Uses balanced objective: True
- Selects top-3 candidates: True
- Uses pipe separator: True
- Uses ensemble threshold: True
- Averages probabilities: True

## Selection-Integrity Validation

- **Runs checked:** 50
- **Order mismatches:** 0
- **Membership mismatches:** 0
- **Excluded candidate mismatches:** 0
- **Balanced top-1 consistency mismatches:** 0
- **Selection mode mismatches:** 0
- **Invalid thresholds:** 0
- **Invalid selection scores:** 0

## Tie and Cutoff Diagnostics

- **Exact score-tie runs:** 0
- **Near score-tie runs (within 1e-12):** 0
- **Cutoff near-tie runs (within 1e-12):** 0

## Candidate Membership and Exclusion Frequency

### Overall

| Candidate | Membership Count | Exclusion Count | Denominator | Membership Prop | Exclusion Prop |
|-----------|-----------------|-----------------|------------|----------------|----------------|
| DT_leaf5 | 10 | 40 | 50 | 0.200 | 0.800 |
| ET_leaf5 | 49 | 1 | 50 | 0.980 | 0.020 |
| LR_std_C0.1 | 45 | 5 | 50 | 0.900 | 0.100 |
| LR_std_C1 | 46 | 4 | 50 | 0.920 | 0.080 |

## Position Frequency

### Overall

| Position | Candidate | Count | Denominator | Proportion |
|----------|-----------|-------|------------|------------|
| 1 | DT_leaf5 | 5 | 50 | 0.100 |
| 1 | ET_leaf5 | 40 | 50 | 0.800 |
| 1 | LR_std_C0.1 | 2 | 50 | 0.040 |
| 1 | LR_std_C1 | 3 | 50 | 0.060 |
| 2 | DT_leaf5 | 0 | 50 | 0.000 |
| 2 | ET_leaf5 | 6 | 50 | 0.120 |
| 2 | LR_std_C0.1 | 21 | 50 | 0.420 |
| 2 | LR_std_C1 | 23 | 50 | 0.460 |
| 3 | DT_leaf5 | 5 | 50 | 0.100 |
| 3 | ET_leaf5 | 3 | 50 | 0.060 |
| 3 | LR_std_C0.1 | 22 | 50 | 0.440 |
| 3 | LR_std_C1 | 20 | 50 | 0.400 |

## Ordering Frequency

### Overall

| Order | Count | Denominator | Proportion |
|-------|-------|------------|------------|
| DT_leaf5|ET_leaf5|LR_std_C0.1 | 1 | 50 | 0.020 |
| DT_leaf5|ET_leaf5|LR_std_C1 | 3 | 50 | 0.060 |
| DT_leaf5|LR_std_C1|LR_std_C0.1 | 1 | 50 | 0.020 |
| ET_leaf5|LR_std_C0.1|DT_leaf5 | 3 | 50 | 0.060 |
| ET_leaf5|LR_std_C0.1|LR_std_C1 | 17 | 50 | 0.340 |
| ET_leaf5|LR_std_C1|DT_leaf5 | 2 | 50 | 0.040 |
| ET_leaf5|LR_std_C1|LR_std_C0.1 | 18 | 50 | 0.360 |
| LR_std_C0.1|LR_std_C1|ET_leaf5 | 2 | 50 | 0.040 |
| LR_std_C1|ET_leaf5|LR_std_C0.1 | 2 | 50 | 0.040 |
| LR_std_C1|LR_std_C0.1|ET_leaf5 | 1 | 50 | 0.020 |

## Descriptive Summary

### Overall

- **Unique observed orders:** 10
- **Most frequent order(s):** ET_leaf5|LR_std_C1|LR_std_C0.1
- **Maximum order count:** 18
- **Maximum order proportion:** 0.360
- **Most frequent position-1 candidate(s):** ET_leaf5
- **Most frequently included candidate(s):** ET_leaf5
- **Most frequently excluded candidate(s):** DT_leaf5
- **Minimum cutoff score gap:** 0.000574
- **Median cutoff score gap:** 0.041222
- **Mean cutoff score gap:** 0.053635

### By Setting

**within_project:**
- Unique observed orders: 10
- Most frequent order(s): ET_leaf5|LR_std_C1|LR_std_C0.1
- Maximum order count: 6
- Maximum order proportion: 0.240
- Most frequent position-1 candidate(s): ET_leaf5
- Most frequently included candidate(s): ET_leaf5
- Most frequently excluded candidate(s): DT_leaf5
- Minimum cutoff score gap: 0.000574
- Median cutoff score gap: 0.043925
- Mean cutoff score gap: 0.063345

**cross_project:**
- Unique observed orders: 3
- Most frequent order(s): ET_leaf5|LR_std_C0.1|LR_std_C1, ET_leaf5|LR_std_C1|LR_std_C0.1
- Maximum order count: 12
- Maximum order proportion: 0.480
- Most frequent position-1 candidate(s): ET_leaf5
- Most frequently included candidate(s): ET_leaf5, LR_std_C0.1, LR_std_C1
- Most frequently excluded candidate(s): DT_leaf5
- Minimum cutoff score gap: 0.017964
- Median cutoff score gap: 0.039484
- Mean cutoff score gap: 0.043926

## Reconstruction Limitations

The stored aggregate outputs permit independent verification of selected membership and order from balanced validation scores, but they do not permit independent reconstruction of the ensemble threshold or ensemble validation objective without sample-level validation probabilities.

## Interpretation Limits

These are descriptive frequencies of Soft-top-3 composition across 50 runs.
They do not establish statistical significance, performance superiority, or causal effects.

