# Part 2 Section 2C: Top-1 Seed Stability Analysis

## Canonical Verification

- Manifest validation status: all_checks_passed
- SHA-256 verified: True

## Event Provenance Validation

- Events verified against canonical repeated_all_results.csv: True
- All 150 events match canonical values within tolerance

## Stability Definitions

**Modal candidates:** All candidates with the highest count in a group (5 seeds).
**Modal proportion:** modal_count / 5
**Pairwise agreement:** Proportion of agreeing seed pairs (10 possible pairs).
**Shannon entropy:** -sum(p * log(p)) for candidate proportions.
**Normalized entropy:** entropy / log(4), bounded [0, 1].
**Unanimous:** All 5 seeds selected the same candidate.
**At least four of five:** Modal candidate selected by >= 4 seeds.

## Group-Level Stability

| Selector | Mode | Experiment | Project | N Seeds | Distinct | Modal Candidates | Modal Count | Modal Prop | Modal Tie | Unanimous | >=4/5 | Pairwise Agree | Norm Entropy |
|----------|------|------------|---------|---------|----------|-------------------|-------------|------------|-----------|----------|-----------------|--------------|
| AQRPE_v2_balanced | balanced | cross_project | CM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_balanced | balanced | cross_project | JM1 | 5 | 2 | ET_leaf5 | 4 | 0.800 | False | False | True | 0.600 | 0.361 |
| AQRPE_v2_balanced | balanced | cross_project | KC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_balanced | balanced | cross_project | KC2 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_balanced | balanced | cross_project | PC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_balanced | balanced | within_project | CM1 | 5 | 4 | ET_leaf5 | 2 | 0.400 | False | False | False | 0.100 | 0.961 |
| AQRPE_v2_balanced | balanced | within_project | JM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_balanced | balanced | within_project | KC1 | 5 | 3 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.300 | 0.685 |
| AQRPE_v2_balanced | balanced | within_project | KC2 | 5 | 3 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.300 | 0.685 |
| AQRPE_v2_balanced | balanced | within_project | PC1 | 5 | 2 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.400 | 0.485 |
| AQRPE_v2_mcc | mcc | cross_project | CM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_mcc | mcc | cross_project | JM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_mcc | mcc | cross_project | KC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_mcc | mcc | cross_project | KC2 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_mcc | mcc | cross_project | PC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_mcc | mcc | within_project | CM1 | 5 | 4 | ET_leaf5 | 2 | 0.400 | False | False | False | 0.100 | 0.961 |
| AQRPE_v2_mcc | mcc | within_project | JM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_mcc | mcc | within_project | KC1 | 5 | 4 | ET_leaf5 | 2 | 0.400 | False | False | False | 0.100 | 0.961 |
| AQRPE_v2_mcc | mcc | within_project | KC2 | 5 | 3 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.300 | 0.685 |
| AQRPE_v2_mcc | mcc | within_project | PC1 | 5 | 2 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.400 | 0.485 |
| AQRPE_v2_rank | rank | cross_project | CM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_rank | rank | cross_project | JM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_rank | rank | cross_project | KC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_rank | rank | cross_project | KC2 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_rank | rank | cross_project | PC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_rank | rank | within_project | CM1 | 5 | 2 | LR_std_C1 | 3 | 0.600 | False | False | False | 0.400 | 0.485 |
| AQRPE_v2_rank | rank | within_project | JM1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |
| AQRPE_v2_rank | rank | within_project | KC1 | 5 | 3 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.300 | 0.685 |
| AQRPE_v2_rank | rank | within_project | KC2 | 5 | 2 | ET_leaf5 | 3 | 0.600 | False | False | False | 0.400 | 0.485 |
| AQRPE_v2_rank | rank | within_project | PC1 | 5 | 1 | ET_leaf5 | 5 | 1.000 | False | True | True | 1.000 | -0.000 |

## Overall Selector Summaries

| Selector | Mode | Groups | Unanimous | Unanimous % | >=4/5 | >=4/5 % | Modal Ties | Mean Modal Prop | Median Modal Prop | Mean Pairwise | Median Pairwise | Mean Entropy | Median Entropy |
|----------|------|--------|-----------|-------------|-------|----------|-------------|-----------------|-------------------|---------------|-----------------|---------------|----------------|
| AQRPE_v2_balanced | balanced | 10 | 5 | 0.500 | 6 | 0.600 | 0 | 0.800 | 0.900 | 0.670 | 0.800 | 0.318 | 0.180 |
| AQRPE_v2_mcc | mcc | 10 | 6 | 0.600 | 6 | 0.600 | 0 | 0.800 | 1.000 | 0.690 | 1.000 | 0.309 | 0.000 |
| AQRPE_v2_rank | rank | 10 | 7 | 0.700 | 7 | 0.700 | 0 | 0.880 | 1.000 | 0.810 | 1.000 | 0.166 | 0.000 |

## Selector Summaries by Setting

| Selector | Mode | Experiment | Groups | Unanimous | Unanimous % | >=4/5 | >=4/5 % | Modal Ties | Mean Modal Prop | Median Modal Prop | Mean Pairwise | Median Pairwise | Mean Entropy | Median Entropy |
|----------|------|------------|--------|-----------|-------------|-------|----------|-------------|-----------------|-------------------|---------------|-----------------|---------------|----------------|
| AQRPE_v2_balanced | balanced | cross_project | 5 | 4 | 0.800 | 5 | 1.000 | 0 | 0.960 | 1.000 | 0.920 | 1.000 | 0.072 | 0.000 |
| AQRPE_v2_balanced | balanced | within_project | 5 | 1 | 0.200 | 1 | 0.200 | 0 | 0.640 | 0.600 | 0.420 | 0.300 | 0.563 | 0.685 |
| AQRPE_v2_mcc | mcc | cross_project | 5 | 5 | 1.000 | 5 | 1.000 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| AQRPE_v2_mcc | mcc | within_project | 5 | 1 | 0.200 | 1 | 0.200 | 0 | 0.600 | 0.600 | 0.380 | 0.300 | 0.619 | 0.685 |
| AQRPE_v2_rank | rank | cross_project | 5 | 5 | 1.000 | 5 | 1.000 | 0 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| AQRPE_v2_rank | rank | within_project | 5 | 2 | 0.400 | 2 | 0.400 | 0 | 0.760 | 0.600 | 0.620 | 0.400 | 0.331 | 0.485 |

## Groups with Modal Ties

No groups with modal ties.

## Groups with Unanimous Selection

| Selector | Experiment | Project | Selected Candidate |
|----------|------------|---------|-------------------|
| AQRPE_v2_balanced | cross_project | CM1 | ET_leaf5 |
| AQRPE_v2_balanced | cross_project | KC1 | ET_leaf5 |
| AQRPE_v2_balanced | cross_project | KC2 | ET_leaf5 |
| AQRPE_v2_balanced | cross_project | PC1 | ET_leaf5 |
| AQRPE_v2_balanced | within_project | JM1 | ET_leaf5 |
| AQRPE_v2_mcc | cross_project | CM1 | ET_leaf5 |
| AQRPE_v2_mcc | cross_project | JM1 | ET_leaf5 |
| AQRPE_v2_mcc | cross_project | KC1 | ET_leaf5 |
| AQRPE_v2_mcc | cross_project | KC2 | ET_leaf5 |
| AQRPE_v2_mcc | cross_project | PC1 | ET_leaf5 |
| AQRPE_v2_mcc | within_project | JM1 | ET_leaf5 |
| AQRPE_v2_rank | cross_project | CM1 | ET_leaf5 |
| AQRPE_v2_rank | cross_project | JM1 | ET_leaf5 |
| AQRPE_v2_rank | cross_project | KC1 | ET_leaf5 |
| AQRPE_v2_rank | cross_project | KC2 | ET_leaf5 |
| AQRPE_v2_rank | cross_project | PC1 | ET_leaf5 |
| AQRPE_v2_rank | within_project | JM1 | ET_leaf5 |
| AQRPE_v2_rank | within_project | PC1 | ET_leaf5 |

## Interpretation Limits

These metrics describe categorical agreement of candidate selections across five seeds.
They are not inferential tests and do not establish performance stability, statistical significance, or model superiority.

