# Part 3B ExtraTrees Canonical Reconciliation Audit

**Stage:** Part 3B.2R.1-G.D4
**Starting commit:** `82d284f606ba4b06b4ee6ef46ab279d914028eef`

## Summary

- **Strict mismatch count Build 1:** 9
- **Strict mismatch count Build 2:** 9
- **Approved existing exception count:** 1
- **Unapproved systematic difference count:** 8
- **Build mismatch identity sets equal:** True
- **Build mismatch values equal:** True
- **Categorical mismatches:** 0
- **Validation numeric mismatches:** 0
- **Maximum metric absolute difference:** 4.283498555857079e-08
- **Maximum metric relative difference:** 9.938014065509184e-08
- **Maximum ET score absolute difference:** 4.440892098500626e-16
- **Non-ET scores byte-identical:** True
- **All unapproved rows ET-derived:** True
- **All unapproved rows rank-sensitive:** True
- **All unapproved rows within 1e-7:** True
- **Policy enforced:** False
- **Production validator changed:** False
- **Canonical file changed:** False
- **All validation checks passed:** True

## Affected Scope

- **Affected events:** cross_project__JM1__seed_013, cross_project__JM1__seed_042
- **Affected models:** AQRPE_v2_balanced, AQRPE_v2_mcc, AQRPE_v2_rank, ET_leaf5
- **Affected columns:** avg_precision, roc_auc

## Validation Reconstruction

- **Build 1 and Build 2 validation reconstructions equal:** True
- **Validation categorical mismatches:** 0
- **Validation numeric mismatches:** 0

## Score-Level Mechanism

### cross_project__JM1__seed_013

- Maximum ET score absolute difference: 3.3306690738754696e-16
- Non-ET scores byte-identical: True

| Candidate | Validation byte equal | Test byte equal | Max val diff | Max test diff |
| --- | --- | --- | --- | --- |
| LR_std_C0.1 | True | True | 0.0 | 0.0 |
| LR_std_C1 | True | True | 0.0 | 0.0 |
| DT_leaf5 | True | True | 0.0 | 0.0 |
| ET_leaf5 | False | False | 2.220446049250313e-16 | 3.3306690738754696e-16 |

### cross_project__JM1__seed_042

- Maximum ET score absolute difference: 4.440892098500626e-16
- Non-ET scores byte-identical: True

| Candidate | Validation byte equal | Test byte equal | Max val diff | Max test diff |
| --- | --- | --- | --- | --- |
| LR_std_C0.1 | True | True | 0.0 | 0.0 |
| LR_std_C1 | True | True | 0.0 | 0.0 |
| DT_leaf5 | True | True | 0.0 | 0.0 |
| ET_leaf5 | False | False | 2.220446049250313e-16 | 4.440892098500626e-16 |

## Proposed ET Rank Metric Reconciliation Policy

- **policy_enforced:** False
- **production_validator_changed:** False
- **canonical_file_changed:** False

### Classification

- **Mechanistically explainable:** 9 row(s)
- **Currently approved:** 1 row(s)
- **Currently unapproved:** 8 row(s)

## Production Activity

- **Model fits executed:** 0
- **Prediction calls executed:** 0
- **Build core bundle calls:** 0
- **Repository production artifacts published:** 0
- **Part 3B complete:** False
- **Part 3C authorized:** False
