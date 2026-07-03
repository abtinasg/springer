# Part 2 Section 2A: Top-1 Selection Frequency Analysis

## Canonical Verification

- All canonical files verified with SHA-256
- Manifest validation status: all_checks_passed
- Analysis readiness: ready_from_existing_outputs

## Selection-Provenance Validation

- **Runs checked:** 150
- **Selected candidate mismatches:** 0
- **Selection score mismatches:** 0
- **Threshold mismatches:** 0
- **Selection mode mismatches:** 0
- **Validation tie runs:** 0

## Overall Selection Frequency

| Selector | Mode | Candidate | Count | Denominator | Proportion |
|----------|------|-----------|-------|------------|------------|
| AQRPE_v2_balanced | balanced | DT_leaf5 | 5 | 50 | 0.1000 |
| AQRPE_v2_balanced | balanced | ET_leaf5 | 40 | 50 | 0.8000 |
| AQRPE_v2_balanced | balanced | LR_std_C0.1 | 2 | 50 | 0.0400 |
| AQRPE_v2_balanced | balanced | LR_std_C1 | 3 | 50 | 0.0600 |
| AQRPE_v2_mcc | mcc | DT_leaf5 | 5 | 50 | 0.1000 |
| AQRPE_v2_mcc | mcc | ET_leaf5 | 40 | 50 | 0.8000 |
| AQRPE_v2_mcc | mcc | LR_std_C0.1 | 2 | 50 | 0.0400 |
| AQRPE_v2_mcc | mcc | LR_std_C1 | 3 | 50 | 0.0600 |
| AQRPE_v2_rank | rank | DT_leaf5 | 0 | 50 | 0.0000 |
| AQRPE_v2_rank | rank | ET_leaf5 | 41 | 50 | 0.8200 |
| AQRPE_v2_rank | rank | LR_std_C0.1 | 5 | 50 | 0.1000 |
| AQRPE_v2_rank | rank | LR_std_C1 | 4 | 50 | 0.0800 |

## Selection Frequency by Setting

| Selector | Mode | Experiment | Candidate | Count | Denominator | Proportion |
|----------|------|------------|-----------|-------|------------|------------|
| AQRPE_v2_balanced | balanced | cross_project | DT_leaf5 | 0 | 25 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | ET_leaf5 | 24 | 25 | 0.9600 |
| AQRPE_v2_balanced | balanced | cross_project | LR_std_C0.1 | 1 | 25 | 0.0400 |
| AQRPE_v2_balanced | balanced | cross_project | LR_std_C1 | 0 | 25 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | DT_leaf5 | 5 | 25 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | ET_leaf5 | 16 | 25 | 0.6400 |
| AQRPE_v2_balanced | balanced | within_project | LR_std_C0.1 | 1 | 25 | 0.0400 |
| AQRPE_v2_balanced | balanced | within_project | LR_std_C1 | 3 | 25 | 0.1200 |
| AQRPE_v2_mcc | mcc | cross_project | DT_leaf5 | 0 | 25 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | ET_leaf5 | 25 | 25 | 1.0000 |
| AQRPE_v2_mcc | mcc | cross_project | LR_std_C0.1 | 0 | 25 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | LR_std_C1 | 0 | 25 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | DT_leaf5 | 5 | 25 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | ET_leaf5 | 15 | 25 | 0.6000 |
| AQRPE_v2_mcc | mcc | within_project | LR_std_C0.1 | 2 | 25 | 0.0800 |
| AQRPE_v2_mcc | mcc | within_project | LR_std_C1 | 3 | 25 | 0.1200 |
| AQRPE_v2_rank | rank | cross_project | DT_leaf5 | 0 | 25 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | ET_leaf5 | 25 | 25 | 1.0000 |
| AQRPE_v2_rank | rank | cross_project | LR_std_C0.1 | 0 | 25 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | LR_std_C1 | 0 | 25 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | DT_leaf5 | 0 | 25 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | ET_leaf5 | 16 | 25 | 0.6400 |
| AQRPE_v2_rank | rank | within_project | LR_std_C0.1 | 5 | 25 | 0.2000 |
| AQRPE_v2_rank | rank | within_project | LR_std_C1 | 4 | 25 | 0.1600 |

## Selection Frequency by Project

| Selector | Mode | Experiment | Project | Candidate | Count | Denominator | Proportion |
|----------|------|------------|---------|-----------|-------|------------|------------|
| AQRPE_v2_balanced | balanced | cross_project | CM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | CM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_balanced | balanced | cross_project | CM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | CM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | JM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | JM1 | ET_leaf5 | 4 | 5 | 0.8000 |
| AQRPE_v2_balanced | balanced | cross_project | JM1 | LR_std_C0.1 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | cross_project | JM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC2 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC2 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC2 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | KC2 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | PC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | PC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_balanced | balanced | cross_project | PC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | cross_project | PC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | CM1 | DT_leaf5 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | CM1 | ET_leaf5 | 2 | 5 | 0.4000 |
| AQRPE_v2_balanced | balanced | within_project | CM1 | LR_std_C0.1 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | CM1 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | JM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | JM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_balanced | balanced | within_project | JM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | JM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | KC1 | DT_leaf5 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | KC1 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_balanced | balanced | within_project | KC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | KC1 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | KC2 | DT_leaf5 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | KC2 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_balanced | balanced | within_project | KC2 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | KC2 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_balanced | balanced | within_project | PC1 | DT_leaf5 | 2 | 5 | 0.4000 |
| AQRPE_v2_balanced | balanced | within_project | PC1 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_balanced | balanced | within_project | PC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_balanced | balanced | within_project | PC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | CM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | CM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_mcc | mcc | cross_project | CM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | CM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | JM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | JM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_mcc | mcc | cross_project | JM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | JM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC2 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC2 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC2 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | KC2 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | PC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | PC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_mcc | mcc | cross_project | PC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | cross_project | PC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | CM1 | DT_leaf5 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | CM1 | ET_leaf5 | 2 | 5 | 0.4000 |
| AQRPE_v2_mcc | mcc | within_project | CM1 | LR_std_C0.1 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | CM1 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | JM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | JM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_mcc | mcc | within_project | JM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | JM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | KC1 | DT_leaf5 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | KC1 | ET_leaf5 | 2 | 5 | 0.4000 |
| AQRPE_v2_mcc | mcc | within_project | KC1 | LR_std_C0.1 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | KC1 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | KC2 | DT_leaf5 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | KC2 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_mcc | mcc | within_project | KC2 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | KC2 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_mcc | mcc | within_project | PC1 | DT_leaf5 | 2 | 5 | 0.4000 |
| AQRPE_v2_mcc | mcc | within_project | PC1 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_mcc | mcc | within_project | PC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_mcc | mcc | within_project | PC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | CM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | CM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | cross_project | CM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | CM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | JM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | JM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | cross_project | JM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | JM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | KC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | KC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | cross_project | KC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | KC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | KC2 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | KC2 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | cross_project | KC2 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | KC2 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | PC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | PC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | cross_project | PC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | cross_project | PC1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | CM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | CM1 | ET_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | CM1 | LR_std_C0.1 | 2 | 5 | 0.4000 |
| AQRPE_v2_rank | rank | within_project | CM1 | LR_std_C1 | 3 | 5 | 0.6000 |
| AQRPE_v2_rank | rank | within_project | JM1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | JM1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | within_project | JM1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | JM1 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | KC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | KC1 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_rank | rank | within_project | KC1 | LR_std_C0.1 | 1 | 5 | 0.2000 |
| AQRPE_v2_rank | rank | within_project | KC1 | LR_std_C1 | 1 | 5 | 0.2000 |
| AQRPE_v2_rank | rank | within_project | KC2 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | KC2 | ET_leaf5 | 3 | 5 | 0.6000 |
| AQRPE_v2_rank | rank | within_project | KC2 | LR_std_C0.1 | 2 | 5 | 0.4000 |
| AQRPE_v2_rank | rank | within_project | KC2 | LR_std_C1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | PC1 | DT_leaf5 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | PC1 | ET_leaf5 | 5 | 5 | 1.0000 |
| AQRPE_v2_rank | rank | within_project | PC1 | LR_std_C0.1 | 0 | 5 | 0.0000 |
| AQRPE_v2_rank | rank | within_project | PC1 | LR_std_C1 | 0 | 5 | 0.0000 |

## Descriptive Maxima and Ties

### Overall Maxima by Selector

**AQRPE_v2_balanced:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 40
- Maximum proportion: 0.8000

**AQRPE_v2_rank:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 41
- Maximum proportion: 0.8200

**AQRPE_v2_mcc:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 40
- Maximum proportion: 0.8000

### Maxima by Selector and Setting

**AQRPE_v2_balanced / within_project:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 16
- Maximum proportion: 0.6400

**AQRPE_v2_balanced / cross_project:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 24
- Maximum proportion: 0.9600

**AQRPE_v2_rank / within_project:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 16
- Maximum proportion: 0.6400

**AQRPE_v2_rank / cross_project:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 25
- Maximum proportion: 1.0000

**AQRPE_v2_mcc / within_project:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 15
- Maximum proportion: 0.6000

**AQRPE_v2_mcc / cross_project:**
- Most frequent candidate(s): ET_leaf5
- Maximum count: 25
- Maximum proportion: 1.0000

## Interpretation Limits

These are descriptive selection frequencies from 50 repeated runs per selector.
They do not establish statistical significance or superiority.
No causal inferences should be drawn from these descriptive statistics.

