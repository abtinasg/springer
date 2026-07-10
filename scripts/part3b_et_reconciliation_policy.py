#!/usr/bin/env python3
"""Part 3B.2R.1-G.D6: Frozen ET reconciliation policy evaluator (fail-closed)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

STAGE = "Part 3B.2R.1-G.D6.1"
POLICY_SPEC_STAGE = "Part 3B.2R.1-G.D5.2"
STARTING_COMMIT = "69f60b84e2e20b3ac3a89aa93e10269a7b6c773c"
POLICY_ID = "et_rank_metric_reconciliation"
POLICY_STATUS = "specified_not_enforced"
FROZEN_POLICY_JSON_PATH = "reports/part3b_et_reconciliation_policy.json"
FROZEN_POLICY_JSON_SHA256 = (
    "6bc043b7c890256fd369eb8747f54dd9f2f1944b03b0dd1c70b5f6d85b8719f5"
)
RECONCILIATION_JSON_SHA256 = (
    "2c483ceea237c97d5c339ba3ceb438f8e6e2e9beae695dc9410aa5b4b825de0a"
)
MATRIX_SHA256 = (
    "25cc88a8785f18668be2e03328a71b80b6e2c66f679a572e1e53656cde4ef908"
)

ET_SCORE_ABSOLUTE_TOLERANCE = 1e-15
METRIC_ABSOLUTE_TOLERANCE = 1e-7
ELIGIBLE_METRIC_ALLOWLIST = ["avg_precision", "roc_auc"]
REQUIRED_CANDIDATES = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
NON_ET_CANDIDATES = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5"]
ET_LEAF5_CANDIDATE = "ET_leaf5"
ET_SCORE_DELTA_FIELDS = [
    "maximum_build1_validation_absolute_score_difference",
    "maximum_build1_test_absolute_score_difference",
    "maximum_build2_validation_absolute_score_difference",
    "maximum_build2_test_absolute_score_difference",
]
NON_ET_BYTE_EQUAL_FIELDS = [
    "build1_validation_score_byte_equal",
    "build1_test_score_byte_equal",
    "build2_validation_score_byte_equal",
    "build2_test_score_byte_equal",
]

HARDCODED_IDENTITY_PATTERNS = [
    re.compile(r"\bJM1\b"),
    re.compile(r"\bseed[_\s-]*0*13\b", re.IGNORECASE),
    re.compile(r"\bseed[_\s-]*0*42\b", re.IGNORECASE),
    re.compile(r"cross_project__JM1"),
    re.compile(r"AQRPE_v2_balanced"),
    re.compile(r"AQRPE_v2_mcc"),
    re.compile(r"AQRPE_v2_rank"),
]

REQUIRED_GLOBAL_FIELDS = [
    "strict_mismatch_count_build1",
    "strict_mismatch_count_build2",
    "build_mismatch_identity_sets_equal",
    "build_result_reconstruction_sha_equal",
    "build_validation_reconstruction_sha_equal",
    "build_prediction_within_sha_equal",
    "build_prediction_cross_sha_equal",
    "validation_categorical_mismatch_count_build1",
    "validation_categorical_mismatch_count_build2",
    "validation_numeric_mismatch_count_build1",
    "validation_numeric_mismatch_count_build2",
    "build1_build2_validation_reconstructions_equal",
    "categorical_mismatch_count",
]

REQUIRED_MATRIX_ROW_FIELDS = [
    "build1_build2_value_equal",
    "absolute_difference_build1",
    "absolute_difference_build2",
    "direct_et_model",
    "selected_candidate_is_et",
    "soft_ensemble_contains_et",
    "et_derived_row",
    "column",
    "threshold_sensitive_metric",
    "calibration_metric",
    "g_r1_build1_value",
    "g_r1_build2_value",
]

INELIGIBLE_METRIC_CATEGORIES = {
    "threshold": "threshold",
    "selection_score": "threshold_sensitive",
    "precision": "threshold_sensitive",
    "recall": "threshold_sensitive",
    "f1": "threshold_sensitive",
    "mcc": "threshold_sensitive",
    "balanced_accuracy": "threshold_sensitive",
    "brier": "calibration",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def float64_bit_equal(a: Any, b: Any) -> bool:
    return np.float64(a).tobytes() == np.float64(b).tobytes()


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if isinstance(value, str) and value == "":
        return True
    return False


def _is_finite(value: Any) -> bool:
    if _is_missing(value):
        return False
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _compare(operator: str, observed: Any, expected: Any) -> bool:
    if operator == "==":
        return observed == expected
    if operator == "!=":
        return observed != expected
    if operator == ">":
        return observed > expected
    if operator == ">=":
        return observed >= expected
    if operator == "<":
        return observed < expected
    if operator == "<=":
        return observed <= expected
    raise ValueError(f"Unsupported operator: {operator}")


def _verify_policy_contract(spec: Dict[str, Any]) -> None:
    required_top_level = {
        "stage": POLICY_SPEC_STAGE,
        "policy_status": POLICY_STATUS,
        "policy_id": POLICY_ID,
        "policy_enforced": False,
        "production_validator_changed": False,
        "canonical_file_changed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
    }
    errors: List[str] = []
    for field, expected in required_top_level.items():
        if spec.get(field) != expected:
            errors.append(f"{field}={spec.get(field)!r} expected {expected!r}")

    constants = spec.get("exact_constants", {})
    if constants.get("et_score_absolute_tolerance") != ET_SCORE_ABSOLUTE_TOLERANCE:
        errors.append("et_score_absolute_tolerance mismatch")
    if constants.get("metric_absolute_tolerance") != METRIC_ABSOLUTE_TOLERANCE:
        errors.append("metric_absolute_tolerance mismatch")
    if constants.get("eligible_metric_allowlist") != ELIGIBLE_METRIC_ALLOWLIST:
        errors.append("eligible_metric_allowlist mismatch")
    if constants.get("exact_build_value_equality") != "float64_bit_exact":
        errors.append("exact_build_value_equality mismatch")
    if constants.get("exact_build_score_equality") != "byte_exact":
        errors.append("exact_build_score_equality mismatch")
    if constants.get("required_candidates") != REQUIRED_CANDIDATES:
        errors.append("required_candidates mismatch")

    counts = spec.get("current_classification_counts", {})
    if counts.get("mechanistically_eligible_rows") != 9:
        errors.append("mechanistically_eligible_rows != 9")
    if counts.get("currently_approved_rows") != 1:
        errors.append("currently_approved_rows != 1")
    if counts.get("currently_unapproved_rows") != 8:
        errors.append("currently_unapproved_rows != 8")

    integrity = spec.get("specification_integrity_checks", {})
    if integrity.get("all_specification_checks_passed") is not True:
        errors.append("all_specification_checks_passed is not true")

    provenance = spec.get("evidence_provenance", [])
    if len(provenance) >= 1:
        if provenance[0].get("sha256") != RECONCILIATION_JSON_SHA256:
            errors.append("reconciliation JSON provenance SHA mismatch")
    if len(provenance) >= 2:
        if provenance[1].get("sha256") != MATRIX_SHA256:
            errors.append("mismatch matrix provenance SHA mismatch")

    if errors:
        raise RuntimeError(
            "Frozen policy specification contract verification failed: " + "; ".join(errors)
        )


def load_and_verify_frozen_policy(
    root: Optional[Path] = None,
    *,
    policy_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load frozen policy JSON, verify SHA-256 and G.D5.2 contract (fail-closed)."""
    base = root if root is not None else repo_root()
    path = policy_path if policy_path is not None else base / FROZEN_POLICY_JSON_PATH
    if not path.is_file():
        raise RuntimeError(f"Frozen policy specification not found: {path}")
    actual_sha = sha256_file(path)
    if actual_sha != FROZEN_POLICY_JSON_SHA256:
        raise RuntimeError(
            f"Frozen policy SHA-256 {actual_sha} != required {FROZEN_POLICY_JSON_SHA256}"
        )
    spec = json.loads(path.read_text(encoding="utf-8"))
    _verify_policy_contract(spec)
    return spec


def predicate_contains_hardcoded_identities(predicate: Dict[str, Any]) -> bool:
    text = json.dumps(predicate, sort_keys=True)
    return any(pattern.search(text) for pattern in HARDCODED_IDENTITY_PATTERNS)


def _evaluate_et_score_delta_fields(
    event_evidence: Dict[str, Any],
    reason_codes: List[str],
) -> Tuple[bool, List[Dict[str, Any]]]:
    checks: List[Dict[str, Any]] = []
    passed = True
    for field in ET_SCORE_DELTA_FIELDS:
        value = event_evidence.get(field)
        field_pass = True
        if _is_missing(value):
            field_pass = False
            reason_codes.append(f"D_failed:missing_{field}")
        elif not _is_finite(value):
            field_pass = False
            reason_codes.append(f"D_failed:non_finite_{field}")
        elif float(value) > ET_SCORE_ABSOLUTE_TOLERANCE:
            field_pass = False
            reason_codes.append(f"D_failed:{field}_above_tolerance")
        if not field_pass:
            passed = False
        checks.append({"field": field, "passed": field_pass, "observed": value})
    return passed, checks


def _evaluate_candidate_score_evidence(
    event_evidence: Dict[str, Any],
    reason_codes: List[str],
) -> Tuple[bool, List[Dict[str, Any]]]:
    checks: List[Dict[str, Any]] = []
    passed = True
    candidate_map = event_evidence.get("candidate_score_evidence")
    if not isinstance(candidate_map, dict):
        reason_codes.append("D_failed:missing_candidate_score_evidence")
        return False, checks

    present = set(candidate_map.keys())
    expected = set(REQUIRED_CANDIDATES)
    if present != expected:
        passed = False
        missing = sorted(expected - present)
        unexpected = sorted(present - expected)
        if missing:
            reason_codes.append("D_failed:missing_non_et_candidate")
            for cand in missing:
                reason_codes.append(f"D_failed:missing_candidate:{cand}")
        if unexpected:
            reason_codes.append("D_failed:unexpected_candidate")
            for cand in unexpected:
                reason_codes.append(f"D_failed:unexpected_candidate:{cand}")

    for cand in NON_ET_CANDIDATES:
        cand_evidence = candidate_map.get(cand)
        if not isinstance(cand_evidence, dict):
            passed = False
            reason_codes.append(f"D_failed:missing_candidate:{cand}")
            continue
        for field in NON_ET_BYTE_EQUAL_FIELDS:
            value = cand_evidence.get(field)
            if value is None:
                passed = False
                reason_codes.append(f"D_failed:missing_candidate_field:{cand}.{field}")
                checks.append(
                    {"candidate": cand, "field": field, "passed": False, "observed": None}
                )
                continue
            field_pass = bool(value)
            if not field_pass:
                passed = False
                reason_codes.append(f"D_failed:non_et_byte_inequality:{cand}.{field}")
            checks.append(
                {"candidate": cand, "field": field, "passed": field_pass, "observed": value}
            )

    et_evidence = candidate_map.get(ET_LEAF5_CANDIDATE)
    if not isinstance(et_evidence, dict):
        passed = False
        reason_codes.append(f"D_failed:missing_candidate:{ET_LEAF5_CANDIDATE}")
    else:
        for field in (
            "build1_build2_validation_score_byte_equal",
            "build1_build2_test_score_byte_equal",
        ):
            value = et_evidence.get(field)
            if value is None:
                passed = False
                reason_codes.append(f"D_failed:missing_candidate_field:{ET_LEAF5_CANDIDATE}.{field}")
                field_pass = False
            else:
                field_pass = bool(value)
                if not field_pass:
                    passed = False
                    reason_codes.append(f"D_failed:et_candidate_build_byte_inequality:{field}")
            checks.append(
                {
                    "candidate": ET_LEAF5_CANDIDATE,
                    "field": field,
                    "passed": field_pass,
                    "observed": value,
                }
            )
        for field in ET_SCORE_DELTA_FIELDS:
            value = et_evidence.get(field)
            field_pass = True
            if _is_missing(value):
                field_pass = False
                reason_codes.append(
                    f"D_failed:missing_et_build_split_delta_field:{ET_LEAF5_CANDIDATE}.{field}"
                )
            elif not _is_finite(value):
                field_pass = False
                reason_codes.append(
                    f"D_failed:non_finite_et_build_split_delta:{ET_LEAF5_CANDIDATE}.{field}"
                )
            elif float(value) > ET_SCORE_ABSOLUTE_TOLERANCE:
                field_pass = False
                reason_codes.append(
                    f"D_failed:et_build_split_delta_above_tolerance:{ET_LEAF5_CANDIDATE}.{field}"
                )
            if not field_pass:
                passed = False
            checks.append(
                {
                    "candidate": ET_LEAF5_CANDIDATE,
                    "field": field,
                    "passed": field_pass,
                    "observed": value,
                }
            )

    return passed, checks


def evaluate_et_rank_metric_reconciliation_eligibility(
    row: Dict[str, Any],
    global_ctx: Dict[str, Any],
    event_evidence: Optional[Dict[str, Any]],
    *,
    selected_candidate_differs: bool = False,
    selection_mode_differs: bool = False,
) -> Dict[str, Any]:
    """Evaluate mechanistic eligibility from explicit evidence (no identity allowlists)."""
    reason_codes: List[str] = []
    sections: Dict[str, Any] = {}

    a_checks: List[Dict[str, Any]] = []
    a_pass = True
    for field in [
        ("strict_mismatch_count_build1", ">", 0),
        ("strict_mismatch_count_build2", ">", 0),
        ("build_mismatch_identity_sets_equal", "==", True),
    ]:
        key, op, val = field
        value = global_ctx.get(key)
        passed = not _is_missing(value) and _compare(op, value, val)
        if not passed:
            a_pass = False
            reason_codes.append(f"A_failed:global.{key}")
        a_checks.append({"field": f"global.{key}", "passed": passed, "observed": value})
    integrity = global_ctx.get("audit_integrity_checks", {})
    for key in ("exact_source_role_set_passed", "all_audit_integrity_checks_passed"):
        value = integrity.get(key)
        passed = value is True
        if not passed:
            a_pass = False
            reason_codes.append(f"A_failed:global.audit_integrity_checks.{key}")
        a_checks.append(
            {
                "field": f"global.audit_integrity_checks.{key}",
                "passed": passed,
                "observed": value,
            }
        )
    sections["A_evidence_completeness"] = {"passed": a_pass, "checks": a_checks}

    b_checks: List[Dict[str, Any]] = []
    b_pass = True
    b1 = row.get("g_r1_build1_value")
    b2 = row.get("g_r1_build2_value")
    if _is_missing(b1) or _is_missing(b2):
        b_pass = False
        reason_codes.append("B_failed:missing_build_value")
    else:
        if not float64_bit_equal(b1, b2):
            b_pass = False
            if float(b1) == float(b2) and not float64_bit_equal(b1, b2):
                reason_codes.append("B_failed:positive_zero_negative_zero_build_value_difference")
            elif np.float64(b1) != np.float64(b2):
                reason_codes.append("B_failed:one_ulp_build_value_difference")
            else:
                reason_codes.append("B_failed:float64_byte_representation_difference")
        b_checks.append(
            {
                "field": "g_r1_build1_value_vs_g_r1_build2_value",
                "passed": float64_bit_equal(b1, b2),
                "equality_helper": "float64_bit_equal",
            }
        )
    if not bool(row.get("build1_build2_value_equal")):
        b_pass = False
        if "B_failed:one_ulp_build_value_difference" not in reason_codes:
            reason_codes.append("B_failed:build1_build2_value_equal_flag_false")
    for key in [
        "build_result_reconstruction_sha_equal",
        "build_validation_reconstruction_sha_equal",
        "build_prediction_within_sha_equal",
        "build_prediction_cross_sha_equal",
    ]:
        passed = bool(global_ctx.get(key))
        if not passed:
            b_pass = False
            reason_codes.append(f"B_failed:{key}")
        b_checks.append({"field": key, "passed": passed})
    bit_exact = bool(integrity.get("build_mismatch_values_bit_exact"))
    if not bit_exact:
        b_pass = False
        reason_codes.append("B_failed:build_mismatch_values_bit_exact")
    b_checks.append({"field": "build_mismatch_values_bit_exact", "passed": bit_exact})
    if event_evidence is None:
        b_pass = False
        reason_codes.append("B_failed:missing_score_evidence")
        score_byte_exact = False
    else:
        score_byte_exact = bool(event_evidence.get("build_score_arrays_byte_exact"))
        if not score_byte_exact:
            b_pass = False
            reason_codes.append("B_failed:build_score_arrays_byte_exact")
    b_checks.append({"field": "build_score_arrays_byte_exact", "passed": score_byte_exact})
    sections["B_exact_deterministic_equality"] = {"passed": b_pass, "checks": b_checks}

    et_mechanism = bool(
        row.get("direct_et_model")
        or row.get("selected_candidate_is_et")
        or row.get("soft_ensemble_contains_et")
    )
    if not et_mechanism:
        reason_codes.append("C_failed:non_et_mechanism")
    sections["C_et_mechanism"] = {
        "passed": et_mechanism,
        "direct_et_model": bool(row.get("direct_et_model")),
        "selected_candidate_is_et": bool(row.get("selected_candidate_is_et")),
        "soft_ensemble_contains_et": bool(row.get("soft_ensemble_contains_et")),
    }

    d_pass = True
    d_checks: List[Dict[str, Any]] = []
    if event_evidence is None:
        d_pass = False
        reason_codes.append("D_failed:missing_score_evidence")
    else:
        delta_pass, delta_checks = _evaluate_et_score_delta_fields(event_evidence, reason_codes)
        d_checks.extend(delta_checks)
        if not delta_pass:
            d_pass = False
        candidate_pass, candidate_checks = _evaluate_candidate_score_evidence(
            event_evidence, reason_codes
        )
        d_checks.extend(candidate_checks)
        if not candidate_pass:
            d_pass = False
        aggregate_max = event_evidence.get("maximum_et_score_absolute_difference")
        derived_max = None
        if all(not _is_missing(event_evidence.get(field)) for field in ET_SCORE_DELTA_FIELDS):
            derived_max = max(float(event_evidence[field]) for field in ET_SCORE_DELTA_FIELDS)
        d_checks.append(
            {
                "field": "maximum_et_score_absolute_difference",
                "passed": True,
                "observed": aggregate_max,
                "derived_from_independent_fields": derived_max,
                "reporting_only": True,
            }
        )
    sections["D_accepted_output_comparison"] = {"passed": d_pass, "checks": d_checks}

    metric = row.get("column")
    e_pass = True
    if metric not in ELIGIBLE_METRIC_ALLOWLIST:
        e_pass = False
        reason_codes.append("E_failed:unknown_or_ineligible_metric")
    if bool(row.get("threshold_sensitive_metric")):
        e_pass = False
        reason_codes.append("E_failed:threshold_sensitive_metric")
    if bool(row.get("calibration_metric")):
        e_pass = False
        reason_codes.append("E_failed:calibration_metric")
    sections["E_metric_classification"] = {
        "passed": e_pass,
        "metric": metric,
        "eligible_metric_allowlist": ELIGIBLE_METRIC_ALLOWLIST,
    }

    f_pass = True
    for field in ["absolute_difference_build1", "absolute_difference_build2"]:
        value = row.get(field)
        if _is_missing(value):
            f_pass = False
            reason_codes.append(f"F_failed:missing_{field}")
            continue
        if float(value) > METRIC_ABSOLUTE_TOLERANCE:
            f_pass = False
            reason_codes.append(f"F_failed:{field}_above_tolerance")
    sections["F_metric_delta"] = {
        "passed": f_pass,
        "absolute_difference_build1": row.get("absolute_difference_build1"),
        "absolute_difference_build2": row.get("absolute_difference_build2"),
        "relative_difference_build1": row.get("relative_difference_build1"),
        "relative_difference_build2": row.get("relative_difference_build2"),
        "metric_absolute_tolerance": METRIC_ABSOLUTE_TOLERANCE,
    }

    g_pass = True
    g_checks: List[Dict[str, Any]] = []
    for key, expected in [
        ("validation_categorical_mismatch_count_build1", 0),
        ("validation_categorical_mismatch_count_build2", 0),
        ("validation_numeric_mismatch_count_build1", 0),
        ("validation_numeric_mismatch_count_build2", 0),
        ("categorical_mismatch_count", 0),
    ]:
        observed = global_ctx.get(key)
        passed = observed == expected
        if not passed:
            g_pass = False
            reason_codes.append(f"G_failed:{key}")
        g_checks.append({"field": key, "passed": passed, "observed": observed})
    if not bool(global_ctx.get("build1_build2_validation_reconstructions_equal")):
        g_pass = False
        reason_codes.append("G_failed:validation_reconstructions_unequal")
    if not bool(row.get("et_derived_row")):
        g_pass = False
        reason_codes.append("G_failed:non_et_derived_row")
    if selected_candidate_differs:
        g_pass = False
        reason_codes.append("G_failed:selected_candidate_difference")
    if selection_mode_differs:
        g_pass = False
        reason_codes.append("G_failed:selection_mode_difference")
    sections["G_validation_and_categorical_invariants"] = {"passed": g_pass, "checks": g_checks}

    eligible = all(
        sections[section]["passed"]
        for section in [
            "A_evidence_completeness",
            "B_exact_deterministic_equality",
            "C_et_mechanism",
            "D_accepted_output_comparison",
            "E_metric_classification",
            "F_metric_delta",
            "G_validation_and_categorical_invariants",
        ]
    )
    sections["H_fail_closed"] = {"passed": eligible, "reason_codes": reason_codes}

    return {
        "eligible": eligible,
        "reason_codes": reason_codes,
        "predicate_results": sections,
    }


def event_id_from_row(row: Dict[str, Any]) -> str:
    seed = int(row["seed"])
    return f"{row['experiment']}__{row['target_project']}__seed_{seed:03d}"


def _extract_global_context(reconciliation_json: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "strict_mismatch_count_build1": reconciliation_json.get("strict_mismatch_count_build1"),
        "strict_mismatch_count_build2": reconciliation_json.get("strict_mismatch_count_build2"),
        "build_mismatch_identity_sets_equal": reconciliation_json.get(
            "build_mismatch_identity_sets_equal"
        ),
        "build_result_reconstruction_sha_equal": reconciliation_json.get(
            "build_result_reconstruction_sha_equal"
        ),
        "build_validation_reconstruction_sha_equal": reconciliation_json.get(
            "build_validation_reconstruction_sha_equal"
        ),
        "build_prediction_within_sha_equal": reconciliation_json.get(
            "build_prediction_within_sha_equal"
        ),
        "build_prediction_cross_sha_equal": reconciliation_json.get(
            "build_prediction_cross_sha_equal"
        ),
        "validation_categorical_mismatch_count_build1": reconciliation_json.get(
            "validation_categorical_mismatch_count_build1"
        ),
        "validation_categorical_mismatch_count_build2": reconciliation_json.get(
            "validation_categorical_mismatch_count_build2"
        ),
        "validation_numeric_mismatch_count_build1": reconciliation_json.get(
            "validation_numeric_mismatch_count_build1"
        ),
        "validation_numeric_mismatch_count_build2": reconciliation_json.get(
            "validation_numeric_mismatch_count_build2"
        ),
        "build1_build2_validation_reconstructions_equal": reconciliation_json.get(
            "build1_build2_validation_reconstructions_equal"
        ),
        "categorical_mismatch_count": reconciliation_json.get("categorical_mismatch_count"),
        "audit_integrity_checks": reconciliation_json.get("audit_integrity_checks", {}),
    }


def validate_dual_build_reconciliation_context(
    context: Optional[Dict[str, Any]],
    policy_spec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate dual-build reconciliation context; fail closed on missing evidence."""
    if context is None:
        return {
            "valid": False,
            "dual_build_evidence_provided": False,
            "reason_codes": ["missing_dual_build_context"],
        }

    if policy_spec is None:
        policy_spec = load_and_verify_frozen_policy()

    reason_codes: List[str] = []
    if context.get("dual_build_evidence_complete") is not True:
        reason_codes.append("dual_build_evidence_incomplete")
    if context.get("build1_present") is not True:
        reason_codes.append("build1_evidence_missing")
    if context.get("build2_present") is not True:
        reason_codes.append("build2_evidence_missing")

    reconciliation_json = context.get("reconciliation_json")
    matrix_rows = context.get("matrix_rows")
    event_evidence_map = context.get("event_evidence_by_id")

    if not isinstance(reconciliation_json, dict):
        reason_codes.append("missing_reconciliation_json")
    if not isinstance(matrix_rows, list) or not matrix_rows:
        reason_codes.append("missing_matrix_rows")
    if not isinstance(event_evidence_map, dict):
        reason_codes.append("missing_event_evidence_map")

    if isinstance(reconciliation_json, dict):
        global_ctx = _extract_global_context(reconciliation_json)
        for field in REQUIRED_GLOBAL_FIELDS:
            value = global_ctx.get(field)
            if _is_missing(value):
                reason_codes.append(f"missing_global_field:{field}")
        integrity = global_ctx.get("audit_integrity_checks", {})
        for key in ("exact_source_role_set_passed", "all_audit_integrity_checks_passed"):
            if integrity.get(key) is not True:
                reason_codes.append(f"audit_integrity_failed:{key}")

    if isinstance(matrix_rows, list):
        for index, row in enumerate(matrix_rows):
            if not isinstance(row, dict):
                reason_codes.append(f"matrix_row_not_dict:{index}")
                continue
            for field in REQUIRED_MATRIX_ROW_FIELDS:
                if field not in row or _is_missing(row.get(field)):
                    reason_codes.append(f"missing_matrix_field:{field}")

    valid = len(reason_codes) == 0
    return {
        "valid": valid,
        "dual_build_evidence_provided": valid,
        "reason_codes": reason_codes,
        "policy_id": policy_spec.get("policy_id"),
        "policy_status": policy_spec.get("policy_status"),
    }


def classify_dual_build_mismatches(
    context: Dict[str, Any],
    policy_spec: Optional[Dict[str, Any]] = None,
    *,
    selected_candidate_differs_by_event: Optional[Dict[str, bool]] = None,
    selection_mode_differs_by_event: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """Final policy classification using dual-build evidence only."""
    if policy_spec is None:
        policy_spec = load_and_verify_frozen_policy()

    ctx_validation = validate_dual_build_reconciliation_context(context, policy_spec)
    if not ctx_validation["valid"]:
        return {
            "classification_completed": False,
            "accepted": False,
            "dual_build_context_valid": False,
            "final_approval_prohibited": True,
            "classifications": [],
            "reason_codes": ctx_validation["reason_codes"],
            "policy_enforced": False,
        }

    reconciliation_json = context["reconciliation_json"]
    matrix_rows = context["matrix_rows"]
    event_evidence_map = context["event_evidence_by_id"]
    global_ctx = _extract_global_context(reconciliation_json)

    selected_candidate_differs_by_event = selected_candidate_differs_by_event or {}
    selection_mode_differs_by_event = selection_mode_differs_by_event or {}

    classifications: List[Dict[str, Any]] = []
    eligible_count = 0
    for row in matrix_rows:
        event_id = event_id_from_row(row)
        evaluation = evaluate_et_rank_metric_reconciliation_eligibility(
            row,
            global_ctx,
            event_evidence_map.get(event_id),
            selected_candidate_differs=selected_candidate_differs_by_event.get(event_id, False),
            selection_mode_differs=selection_mode_differs_by_event.get(event_id, False),
        )
        if evaluation["eligible"]:
            eligible_count += 1
            final_status = "mechanistically_eligible"
        else:
            final_status = "ineligible"
        classifications.append(
            {
                "event_id": event_id,
                "experiment": row.get("experiment"),
                "target_project": row.get("target_project"),
                "seed": row.get("seed"),
                "model": row.get("model"),
                "column": row.get("column"),
                "final_status": final_status,
                "eligible": evaluation["eligible"],
                "reason_codes": evaluation["reason_codes"],
                "predicate_results": evaluation["predicate_results"],
            }
        )

    row_count = len(classifications)
    return {
        "classification_completed": True,
        "dual_build_context_valid": True,
        "all_rows_mechanistically_eligible": eligible_count == row_count,
        "eligible_count": eligible_count,
        "ineligible_count": row_count - eligible_count,
        "row_count": row_count,
        "classifications": classifications,
        "accepted": False,
        "final_approval_prohibited": True,
        "policy_id": policy_spec.get("policy_id"),
        "policy_status": policy_spec.get("policy_status"),
        "policy_enforced": False,
    }


def classify_single_build_mismatch_pending(
    row: Dict[str, Any],
    partial_global_ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Single-build path may only mark rows pending_dual_build_reconciliation."""
    return {
        "event_id": event_id_from_row(row) if "seed" in row and "experiment" in row else None,
        "final_status": "pending_dual_build_reconciliation",
        "eligible": False,
        "final_approval_prohibited": True,
        "reason_codes": ["single_build_cannot_produce_final_approval"],
        "partial_global_ctx_present": partial_global_ctx is not None,
    }


def implementation_contains_hardcoded_identities(source_text: str) -> bool:
    """Detect project/seed/event-specific logic in executable policy source."""
    executable_lines: List[str] = []
    for line in source_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "HARDCODED_IDENTITY_PATTERNS" in stripped:
            continue
        if stripped.startswith("re.compile"):
            continue
        executable_lines.append(line)
    text = "\n".join(executable_lines)
    return any(pattern.search(text) for pattern in HARDCODED_IDENTITY_PATTERNS)
