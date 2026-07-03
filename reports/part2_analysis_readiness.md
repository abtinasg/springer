# Part 2 Section 1A: Analysis Readiness Audit

## Canonical Verification

- **Manifest validation status:** `all_checks_passed`
- **Canonical result source:** `results/part1_full_reproduction`
- **SHA-256 verified:** True

## Canonical Result Coverage

- **Row count:** 400
- **Column count:** 22
- **Null count:** 0
- **Key duplicates:** 0
- **Experiments:** within_project, cross_project
- **Projects:** CM1, JM1, KC1, KC2, PC1
- **Seeds:** 7, 13, 29, 42, 101
- **Models:** LR_std_C0.1, LR_std_C1, DT_leaf5, ET_leaf5, AQRPE_v2_balanced, AQRPE_v2_rank, AQRPE_v2_mcc, AQRPE_v2_soft_top3

## Validation-Log Coverage

- **Row count:** 600
- **Column count:** 21
- **Null count:** 0
- **Key duplicates:** 0
- **Modes:** balanced, rank, mcc
- **Candidates:** LR_std_C0.1, LR_std_C1, DT_leaf5, ET_leaf5

## Join Coverage

| Mode | Validation Rows | Baseline Rows | Matched Rows | Unmatched Validation | Duplicate Validation Keys | Duplicate Baseline Keys |
|------|-----------------|---------------|--------------|----------------------|-------------------------|------------------------|
| balanced | 200 | 200 | 200 | 0 | 0 | 0 |
| rank | 200 | 200 | 200 | 0 | 0 | 0 |
| mcc | 200 | 200 | 200 | 0 | 0 | 0 |

## Selected-Candidate Integrity

### Top-1 Models

**AQRPE_v2_balanced:**
- Has field: True
- Valid: True
- Total rows: 50
- Invalid count: 0

**AQRPE_v2_rank:**
- Has field: True
- Valid: True
- Total rows: 50
- Invalid count: 0

**AQRPE_v2_mcc:**
- Has field: True
- Valid: True
- Total rows: 50
- Invalid count: 0

### Soft-Top-3

- Has field: True
- Valid: True
- Total rows: 50
- Invalid length count: 0
- Duplicate count: 0
- Invalid member count: 0
- Unique orderings count: 10

## Metric Verification

- **Validation metrics present:** 14/14
- **Test metrics present:** 14/14

## Soft-All-4 Availability

- **Existing soft-all-4 output:** False
- **Sample-level probabilities available:** False
- **Reconstructable without model rerun:** False

**Evidence:**

- No AQRPE_v2_soft_all4 model found in repeated_all_results.csv
- No probability columns found in data files
- Evaluation script contains probability-related code

## Final Validation

- **Top-1 models valid:** 3/3
- **Soft-top-3 valid:** True
- **Exact repeated-result runs:** 50/50
- **Exact validation-log runs:** 50/50
- **Join modes passed:** 3/3
- **Validation metrics present:** 14/14
- **Test metrics present:** 14/14

## Analysis Readiness Matrix

### Candidate Selection Frequency and Stability

**Status:** ready_from_existing_outputs
**Reason:** All top-1 models have valid selected_candidate fields and soft-top-3 is valid.

### Validation-Test Ranking Agreement

**Status:** ready_from_existing_outputs
**Reason:** All 14 validation metrics and 14 test metrics are present. Join coverage is complete for all modes.

### Post-Hoc Regret

**Status:** ready_from_existing_outputs
**Reason:** All four baselines are present in all 50 runs and top-1 selections are valid.

### Ablation

**fixed_individual_baselines:**
- Status: ready_from_existing_outputs
- Reason: All four baseline models have complete results in repeated_all_results.csv

**adaptive_top_1:**
- Status: ready_from_existing_outputs
- Reason: Top-1 AQRPE models have valid selected_candidate fields

**soft_top_3:**
- Status: ready_from_existing_outputs
- Reason: AQRPE_v2_soft_top3 has valid selected_candidate field

**soft_all_4:**
- Status: requires_new_computation
- Reason: ['No AQRPE_v2_soft_all4 model found in repeated_all_results.csv', 'No probability columns found in data files', 'Evaluation script contains probability-related code']

## Missing Artifacts

The following artifacts are NOT stored in canonical outputs:

- sample_level_true_labels
- sample_level_predicted_probabilities
- validation_sample_indices
- test_sample_indices
- trained_model_objects

## Next-Computation Implications

Based on the current audit:

- **Candidate selection analysis:** Can proceed immediately with existing outputs.
- **Validation-test agreement:** Can proceed immediately with existing outputs.
- **Post-hoc regret:** Can proceed immediately with existing outputs.
- **Ablation (fixed baselines, adaptive top-1, soft-top-3):** Can proceed immediately with existing outputs.
- **Ablation (soft-all-4):** Requires new computation to obtain sample-level probabilities for all four candidates.

No algorithm changes are proposed at this stage. This audit only assesses data availability.

