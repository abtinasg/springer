# Part 3B ExtraTrees Reconciliation Policy Specification

**Stage:** Part 3B.2R.1-G.D5
**Starting commit:** `429eb3f6df0173457b2b8cece69c6f01cbaeaa25`
**Policy ID:** et_rank_metric_reconciliation
**Policy version:** 1.0.0

## Purpose and Non-Enforcement Warning

This document freezes the exact mechanistic predicate `et_rank_metric_reconciliation_eligible` as a **specified, not enforced** policy.
The production validator is **unchanged**. Production authorization is **false**.
Mechanistic eligibility does **not** change current approval status.

- **Policy status:** specified_not_enforced
- **Production validator status:** unchanged
- **Production authorization:** False
- **Policy enforced:** False
- **Part 3B complete:** False
- **Part 3C authorized:** False
- **Canonical files changed:** False

## Evidence Inputs

| Path | SHA-256 | Rows | Columns | Role |
| --- | --- | --- | --- | --- |
| reports/part3b_et_canonical_reconciliation.json | `2c483ceea237c97d5c339ba3ceb438f8e6e2e9beae695dc9410aa5b4b825de0a` | None | None | G.D4 reconciliation audit report with score-level mechanism evidence |
| results/part3b_prediction_ledger/et_canonical_mismatch_matrix.csv | `25cc88a8785f18668be2e03328a71b80b6e2c66f679a572e1e53656cde4ef908` | 9 | 28 | Nine-row ET canonical mismatch matrix with current approval flags |

## Exact Constants

- **ET score absolute tolerance:** 1e-15
- **Metric absolute tolerance:** 1e-07
- **Eligible metric allowlist:** avg_precision, roc_auc
- **Exact build-value equality:** float64_bit_exact
- **Exact build-score equality:** byte_exact

## Predicate: et_rank_metric_reconciliation_eligible

A mismatch row is eligible only when every section below passes.

### A. Evidence Completeness
- Mismatch exists in both deterministic builds.
- Build 1 and Build 2 mismatch identity sets are exactly equal.
- No required source role or evidence field is missing.
- All G.D4 audit-integrity checks are true.

### B. Exact Deterministic Equality
- Build 1 and Build 2 mismatch values are float64 bit-exact.
- Build 1 and Build 2 result/validation/prediction SHA-256 values are equal.
- Build 1 and Build 2 score arrays are byte-identical.
- Tolerance-based equality must not substitute for any requirement here.

### C. ET Mechanism
- Direct model is `ET_leaf5`, or selected candidate is `ET_leaf5`, or a soft ensemble explicitly contains `ET_leaf5`.

### D. Accepted-Output Comparison
- Non-ET validation and test score arrays are byte-identical to accepted tracked arrays.
- Maximum ET validation/test score absolute difference is at most 1e-15.
- Missing score evidence causes rejection.

### E. Metric Classification
- Eligible metrics: avg_precision, roc_auc.
- Threshold-sensitive, calibration, and unknown metrics are ineligible.

### F. Metric Delta
- Absolute metric difference from canonical is at most 1e-07 for both builds.
- Relative difference is reported but does not replace the absolute threshold.
- No rounding, quantization, truncation, post-hoc replacement, averaging, or output copying.

### G. Validation and Categorical Invariants
- Validation categorical and numeric mismatch counts are zero for both builds.
- Validation reconstructions are exactly equal across builds.
- Result-row categorical identity, selected candidate, and selection mode are unchanged.
- No validation/test role mixing; no test-set use in model selection.

### H. Fail-Closed Behavior
- Any missing field, null/NaN, unknown metric, build disagreement, score mismatch, validation mismatch, or non-ET-derived row rejects eligibility.

## Decision Table

| Concept | Meaning | Changes approval? |
| --- | --- | --- |
| mechanistically_eligible_under_frozen_policy | Predicate passes all sections | No |
| currently_approved_exception | Historical approval in mismatch matrix | No (unchanged) |
| currently_unapproved_mismatch | Not currently approved | No (unchanged) |

## Metric Classification Table

| Metric | Classification | Eligible |
| --- | --- | --- |
| avg_precision | eligible | True |
| roc_auc | eligible | True |
| threshold | threshold | False |
| selection_score | threshold_sensitive | False |
| precision | threshold_sensitive | False |
| recall | threshold_sensitive | False |
| f1 | threshold_sensitive | False |
| mcc | threshold_sensitive | False |
| balanced_accuracy | threshold_sensitive | False |
| brier | calibration | False |
| any_unknown_metric | unknown | False |
| any_calibration_metric | calibration | False |
| any_threshold_sensitive_metric | threshold_sensitive | False |

## Tolerance vs Exact Equality

- **Exact equality** applies to Build 1/Build 2 mismatch values (float64 bit-exact) and score arrays (byte-exact).
- **Tolerance** applies only to ET score deltas (≤ 1e-15) and metric deltas (≤ 1e-07).
- Relative metric differences are reported for transparency but never substitute for the absolute threshold.

## Fail-Closed Conditions

- missing_field
- null_or_nan_required_field
- unknown_metric
- build_identity_disagreement
- one_ulp_build_value_difference
- score_array_byte_difference_between_builds
- non_et_score_difference_from_accepted_output
- et_score_delta_above_1e-15
- metric_delta_above_1e-07
- threshold_sensitive_metric
- calibration_metric
- validation_mismatch
- selected_candidate_difference
- selection_mode_difference
- non_et_derived_row

## Prohibited Operations

- implement_policy_in_production_validator
- enforce_unapproved_mismatches
- rerun_production
- fit_models
- call_prediction_methods
- generate_new_prediction_ledgers
- modify_canonical_part1_files
- modify_g_d4_reconciliation_evidence
- rounding
- quantization
- truncation
- post_hoc_replacement
- averaging
- output_copying
- tolerance_substitution_for_exact_equality

## Current Classification

- **Mechanistically eligible rows:** 9
- **Currently approved rows:** 1
- **Currently unapproved rows:** 8

## Regression Fixtures (Nine Rows)

| Seed | Model | Metric | Mechanistically eligible | Currently approved | Currently unapproved | Reason codes |
| --- | --- | --- | --- | --- | --- | --- |
| 13 | AQRPE_v2_balanced | avg_precision | True | False | True | none |
| 13 | AQRPE_v2_balanced | roc_auc | True | False | True | none |
| 13 | AQRPE_v2_mcc | avg_precision | True | False | True | none |
| 13 | AQRPE_v2_mcc | roc_auc | True | False | True | none |
| 13 | AQRPE_v2_rank | avg_precision | True | False | True | none |
| 13 | AQRPE_v2_rank | roc_auc | True | False | True | none |
| 13 | ET_leaf5 | avg_precision | True | False | True | none |
| 13 | ET_leaf5 | roc_auc | True | False | True | none |
| 42 | AQRPE_v2_rank | roc_auc | True | True | False | none |

## Production and Authorization Status

- **Model fits executed:** 0
- **Prediction calls executed:** 0
- **Production builds executed:** 0
- **Repository production artifacts published:** 0
- **Production authorization:** False
- **Policy enforced:** False
- **Production validator changed:** False
- **Canonical file changed:** False
- **Part 3B complete:** False
- **Part 3C authorized:** False
