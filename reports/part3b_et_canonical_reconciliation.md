# Part 3B ExtraTrees Canonical Reconciliation Audit

**Stage:** Part 3B.2R.1-G.D4.1.1
**Starting commit:** `3b87873e851fb84f361a88736c0188b106f7f2c2`

## Summary

- **Strict mismatch count Build 1:** 9
- **Strict mismatch count Build 2:** 9
- **Approved existing exception count:** 1
- **Unapproved systematic difference count:** 8
- **Build mismatch identity sets equal:** True
- **Build mismatch values equal:** True
- **Build mismatch values bit-exact:** True
- **Categorical mismatches:** 0
- **Validation numeric mismatches:** 0
- **Maximum metric absolute difference:** 4.283498555857079e-08
- **Maximum metric relative difference:** 9.938014065509184e-08
- **Maximum ET score absolute difference:** 4.440892098500626e-16
- **Non-ET scores byte-identical:** True
- **Build score arrays byte-exact:** True
- **All unapproved rows ET-derived:** True
- **All unapproved rows rank-sensitive:** True
- **All unapproved rows within 1e-7:** True
- **Policy enforced:** False
- **Production validator changed:** False
- **Canonical file changed:** False
- **All validation checks passed:** True

## Build Source Equality

- **Build result reconstruction SHA equal:** True
- **Build validation reconstruction SHA equal:** True
- **Build prediction-within SHA equal:** True
- **Build prediction-cross SHA equal:** True

## Affected Scope

- **Affected events:** cross_project__JM1__seed_013, cross_project__JM1__seed_042
- **Affected models:** AQRPE_v2_balanced, AQRPE_v2_mcc, AQRPE_v2_rank, ET_leaf5
- **Affected columns:** avg_precision, roc_auc

## Validation Reconstruction

- **Build 1 and Build 2 validation reconstructions equal:** True
- **Build 1 validation categorical mismatches:** 0
- **Build 2 validation categorical mismatches:** 0
- **Build 1 validation numeric mismatches:** 0
- **Build 2 validation numeric mismatches:** 0
- **Validation builds exactly equal:** True

## Audit Integrity

- **Source-role contract passed:** True
- **Matrix/JSON consistency passed:** True
- **Markdown/JSON consistency passed:** True
- **Transactional publication validation passed:** True
- **Audit-integrity checks passed:** True

## Score-Level Mechanism

### cross_project__JM1__seed_013

- Maximum ET score absolute difference: 3.3306690738754696e-16
- Non-ET scores byte-identical: True
- Build score arrays byte-exact: True

| Candidate | B1 val byte | B1 test byte | B2 val byte | B2 test byte | B1/B2 val byte | B1/B2 test byte | Max B1 val diff | Max B1 test diff | Max B2 val diff | Max B2 test diff | Max B1/B2 diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR_std_C0.1 | True | True | True | True | True | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| LR_std_C1 | True | True | True | True | True | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| DT_leaf5 | True | True | True | True | True | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ET_leaf5 | False | False | False | False | True | True | 2.220446049250313e-16 | 3.3306690738754696e-16 | 2.220446049250313e-16 | 3.3306690738754696e-16 | 0.0 |

### cross_project__JM1__seed_042

- Maximum ET score absolute difference: 4.440892098500626e-16
- Non-ET scores byte-identical: True
- Build score arrays byte-exact: True

| Candidate | B1 val byte | B1 test byte | B2 val byte | B2 test byte | B1/B2 val byte | B1/B2 test byte | Max B1 val diff | Max B1 test diff | Max B2 val diff | Max B2 test diff | Max B1/B2 diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR_std_C0.1 | True | True | True | True | True | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| LR_std_C1 | True | True | True | True | True | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| DT_leaf5 | True | True | True | True | True | True | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ET_leaf5 | False | False | False | False | True | True | 2.220446049250313e-16 | 4.440892098500626e-16 | 2.220446049250313e-16 | 4.440892098500626e-16 | 0.0 |

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
