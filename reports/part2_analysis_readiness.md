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

| Mode | Validation Rows | Matched Rows | Unmatched Validation | Duplicate Matches |
|------|-----------------|--------------|----------------------|-------------------|
| balanced | 200 | 200 | 0 | 0 |
| rank | 200 | 200 | 0 | 0 |
| mcc | 200 | 200 | 0 | 0 |

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
- Valid: False
- Total rows: 50
- Invalid length count: 0
- Duplicate count: 0
- Invalid member count: 0
- Unique orderings count: 10

## Analysis Readiness Matrix

### Candidate Selection Frequency and Stability

**Status:** ready_from_existing_outputs
**Reason:** All required fields are present in repeated_all_results.csv: selected_candidate, experiment, target_project, seed, model

### Validation-Test Ranking Agreement

**Status:** ready_from_existing_outputs
**Reason:** Validation metrics are in validation_log.csv and test metrics are in repeated_all_results.csv. Join keys are available.

### Post-Hoc Regret

**Status:** ready_from_existing_outputs
**Reason:** Selected top-1 candidate is in repeated_all_results.csv. Test performance of all four baselines is available.

### Ablation

**fixed_individual_baselines:**
- Status: ready_from_existing_outputs
- Reason: All four baseline models have complete results in repeated_all_results.csv

**adaptive_top_1:**
- Status: ready_from_existing_outputs
- Reason: Top-1 AQRPE models (balanced, rank, mcc) have selected_candidate field in repeated_all_results.csv

**soft_top_3:**
- Status: ready_from_existing_outputs
- Reason: AQRPE_v2_soft_top3 has selected_candidate field with pipe-separated candidates in repeated_all_results.csv

**soft_all_4:**
- Status: requires_new_computation
- Reason: Sample-level probabilities for all four candidates are not stored in canonical outputs. Would require re-running models with probability output.

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

