#!/usr/bin/env python3
"""Part 3B.2R.1-G.D5: Freeze exact ET reconciliation policy as non-enforced specification."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

STARTING_COMMIT = "429eb3f6df0173457b2b8cece69c6f01cbaeaa25"
STAGE = "Part 3B.2R.1-G.D5"
POLICY_ID = "et_rank_metric_reconciliation"
POLICY_VERSION = "1.0.0"
POLICY_STATUS = "specified_not_enforced"

MATRIX_SHA256 = (
    "25cc88a8785f18668be2e03328a71b80b6e2c66f679a572e1e53656cde4ef908"
)
RECONCILIATION_JSON_PATH = "reports/part3b_et_canonical_reconciliation.json"
MATRIX_PATH = "results/part3b_prediction_ledger/et_canonical_mismatch_matrix.csv"
JSON_OUTPUT_PATH = "reports/part3b_et_reconciliation_policy.json"
MD_OUTPUT_PATH = "reports/part3b_et_reconciliation_policy.md"

ET_SCORE_ABSOLUTE_TOLERANCE = 1e-15
METRIC_ABSOLUTE_TOLERANCE = 1e-7
ELIGIBLE_METRIC_ALLOWLIST = ["avg_precision", "roc_auc"]
ET_LEAF5_CANDIDATE = "ET_leaf5"

MATRIX_COLUMNS = [
    "mismatch_status",
    "experiment",
    "target_project",
    "seed",
    "model",
    "selected_candidate",
    "selection_mode",
    "column",
    "canonical_value",
    "g_r1_build1_value",
    "g_r1_build2_value",
    "accepted_tracked_part3b_value",
    "build1_build2_value_equal",
    "absolute_difference_build1",
    "absolute_difference_build2",
    "relative_difference_build1",
    "relative_difference_build2",
    "g_r1_vs_accepted_absolute_difference",
    "direct_et_model",
    "selected_candidate_is_et",
    "soft_ensemble_contains_et",
    "et_derived_row",
    "rank_sensitive_metric",
    "threshold_sensitive_metric",
    "calibration_metric",
    "within_1e_7",
    "currently_approved_exception",
    "currently_unapproved_mismatch",
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

HARDCODED_IDENTITY_PATTERNS = [
    re.compile(r"\bJM1\b"),
    re.compile(r"\bseed[_\s-]*0*13\b", re.IGNORECASE),
    re.compile(r"\bseed[_\s-]*0*42\b", re.IGNORECASE),
    re.compile(r"cross_project__JM1"),
    re.compile(r"AQRPE_v2_balanced"),
    re.compile(r"AQRPE_v2_mcc"),
    re.compile(r"AQRPE_v2_rank"),
]


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_starting_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def event_id_from_row(row: Dict[str, Any]) -> str:
    seed = int(row["seed"])
    return f"{row['experiment']}__{row['target_project']}__seed_{seed:03d}"


def row_identity(row: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        row["experiment"],
        row["target_project"],
        int(row["seed"]),
        row["model"],
        row["column"],
    )


def build_predicate_definition() -> Dict[str, Any]:
    return {
        "predicate_name": "et_rank_metric_reconciliation_eligible",
        "A_evidence_completeness": {
            "description": "Mismatch exists in both deterministic builds with complete evidence.",
            "requirements": [
                {
                    "field": "global.strict_mismatch_count_build1",
                    "operator": ">",
                    "value": 0,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.strict_mismatch_count_build2",
                    "operator": ">",
                    "value": 0,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.build_mismatch_identity_sets_equal",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.audit_integrity_checks.exact_source_role_set_passed",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.audit_integrity_checks.all_audit_integrity_checks_passed",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
            ],
        },
        "B_exact_deterministic_equality": {
            "description": "Build 1 and Build 2 mismatch values and artifacts are exactly equal.",
            "requirements": [
                {
                    "field": "row.build1_build2_value_equal",
                    "operator": "==",
                    "value": True,
                    "equality_mode": "float64_bit_exact",
                    "source": "matrix_row",
                },
                {
                    "field": "global.build_result_reconstruction_sha_equal",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.build_validation_reconstruction_sha_equal",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.build_prediction_within_sha_equal",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.build_prediction_cross_sha_equal",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "global.audit_integrity_checks.build_mismatch_values_bit_exact",
                    "operator": "==",
                    "value": True,
                    "source": "reconciliation_json",
                },
                {
                    "field": "event.build_score_arrays_byte_exact",
                    "operator": "==",
                    "value": True,
                    "equality_mode": "byte_exact",
                    "source": "score_evidence",
                },
            ],
            "exact_build_value_equality": "float64_bit_exact",
            "exact_build_score_equality": "byte_exact",
            "tolerance_substitution_prohibited": True,
        },
        "C_et_mechanism": {
            "description": "Row is ET-derived through direct model, selected candidate, or soft ensemble.",
            "any_of": [
                {"field": "row.direct_et_model", "operator": "==", "value": True},
                {"field": "row.selected_candidate_is_et", "operator": "==", "value": True},
                {"field": "row.soft_ensemble_contains_et", "operator": "==", "value": True},
            ],
            "et_candidate_literal": ET_LEAF5_CANDIDATE,
            "identity_hardcoding_prohibited": True,
        },
        "D_accepted_output_comparison": {
            "description": "Non-ET scores byte-identical; ET scores within absolute tolerance.",
            "requirements": [
                {
                    "field": "event.non_et_scores_byte_identical",
                    "operator": "==",
                    "value": True,
                    "source": "score_evidence",
                },
                {
                    "field": "event.build1_non_et_scores_byte_identical",
                    "operator": "==",
                    "value": True,
                    "source": "score_evidence",
                },
                {
                    "field": "event.build2_non_et_scores_byte_identical",
                    "operator": "==",
                    "value": True,
                    "source": "score_evidence",
                },
                {
                    "field": "event.maximum_et_score_absolute_difference",
                    "operator": "<=",
                    "value": ET_SCORE_ABSOLUTE_TOLERANCE,
                    "source": "score_evidence",
                },
            ],
            "et_score_absolute_tolerance": ET_SCORE_ABSOLUTE_TOLERANCE,
            "missing_score_evidence_rejects": True,
        },
        "E_metric_classification": {
            "description": "Metric must be on the exact allowlist.",
            "eligible_metric_allowlist": ELIGIBLE_METRIC_ALLOWLIST,
            "ineligible_categories": {
                "threshold_sensitive": [
                    "threshold",
                    "selection_score",
                    "precision",
                    "recall",
                    "f1",
                    "mcc",
                    "balanced_accuracy",
                ],
                "calibration": ["brier"],
                "threshold_sensitive_metrics_flag": "row.threshold_sensitive_metric",
                "calibration_metrics_flag": "row.calibration_metric",
            },
            "unknown_metric_rejects": True,
        },
        "F_metric_delta": {
            "description": "Absolute metric delta from canonical must be within tolerance.",
            "requirements": [
                {
                    "field": "row.absolute_difference_build1",
                    "operator": "<=",
                    "value": METRIC_ABSOLUTE_TOLERANCE,
                },
                {
                    "field": "row.absolute_difference_build2",
                    "operator": "<=",
                    "value": METRIC_ABSOLUTE_TOLERANCE,
                },
            ],
            "metric_absolute_tolerance": METRIC_ABSOLUTE_TOLERANCE,
            "relative_difference_reported_not_substituted": True,
            "prohibited_operations": [
                "rounding",
                "quantization",
                "truncation",
                "post_hoc_replacement",
                "averaging",
                "output_copying",
            ],
        },
        "G_validation_and_categorical_invariants": {
            "description": "Validation reconstructions exact with unchanged categorical identity.",
            "requirements": [
                {
                    "field": "global.validation_categorical_mismatch_count_build1",
                    "operator": "==",
                    "value": 0,
                },
                {
                    "field": "global.validation_categorical_mismatch_count_build2",
                    "operator": "==",
                    "value": 0,
                },
                {
                    "field": "global.validation_numeric_mismatch_count_build1",
                    "operator": "==",
                    "value": 0,
                },
                {
                    "field": "global.validation_numeric_mismatch_count_build2",
                    "operator": "==",
                    "value": 0,
                },
                {
                    "field": "global.build1_build2_validation_reconstructions_equal",
                    "operator": "==",
                    "value": True,
                },
                {"field": "row.et_derived_row", "operator": "==", "value": True},
                {
                    "field": "global.categorical_mismatch_count",
                    "operator": "==",
                    "value": 0,
                },
            ],
            "invariants": [
                "result_row_categorical_identity_unchanged",
                "selected_candidate_unchanged",
                "selection_mode_unchanged",
                "no_validation_test_role_mixing",
                "no_test_set_use_in_model_selection",
            ],
        },
        "H_fail_closed": {
            "description": "Any missing, null, NaN, or disagreement rejects eligibility.",
            "rejection_conditions": [
                "missing_field",
                "null_or_nan_required_field",
                "unknown_metric",
                "build_identity_disagreement",
                "one_ulp_build_value_difference",
                "score_array_byte_difference_between_builds",
                "non_et_score_difference_from_accepted_output",
                "et_score_delta_above_tolerance",
                "metric_delta_above_tolerance",
                "threshold_sensitive_metric",
                "calibration_metric",
                "validation_mismatch",
                "selected_candidate_difference",
                "selection_mode_difference",
                "non_et_derived_row",
            ],
        },
    }


def build_ordered_evaluation_steps() -> List[Dict[str, Any]]:
    return [
        {"step": 1, "section": "A_evidence_completeness", "action": "verify_global_and_row_presence"},
        {"step": 2, "section": "B_exact_deterministic_equality", "action": "verify_bit_and_byte_exact"},
        {"step": 3, "section": "C_et_mechanism", "action": "verify_et_derivation"},
        {"step": 4, "section": "D_accepted_output_comparison", "action": "verify_score_evidence"},
        {"step": 5, "section": "E_metric_classification", "action": "verify_metric_allowlist"},
        {"step": 6, "section": "F_metric_delta", "action": "verify_metric_delta"},
        {"step": 7, "section": "G_validation_and_categorical_invariants", "action": "verify_validation_invariants"},
        {"step": 8, "section": "H_fail_closed", "action": "aggregate_fail_closed"},
    ]


def build_fail_closed_rules() -> List[str]:
    return [
        "missing_field",
        "null_or_nan_required_field",
        "unknown_metric",
        "build_identity_disagreement",
        "one_ulp_build_value_difference",
        "score_array_byte_difference_between_builds",
        "non_et_score_difference_from_accepted_output",
        f"et_score_delta_above_{ET_SCORE_ABSOLUTE_TOLERANCE}",
        f"metric_delta_above_{METRIC_ABSOLUTE_TOLERANCE}",
        "threshold_sensitive_metric",
        "calibration_metric",
        "validation_mismatch",
        "selected_candidate_difference",
        "selection_mode_difference",
        "non_et_derived_row",
    ]


def build_prohibited_operations() -> List[str]:
    return [
        "implement_policy_in_production_validator",
        "enforce_unapproved_mismatches",
        "rerun_production",
        "fit_models",
        "call_prediction_methods",
        "generate_new_prediction_ledgers",
        "modify_canonical_part1_files",
        "modify_g_d4_reconciliation_evidence",
        "rounding",
        "quantization",
        "truncation",
        "post_hoc_replacement",
        "averaging",
        "output_copying",
        "tolerance_substitution_for_exact_equality",
    ]


def build_metric_classification_table() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for metric in ELIGIBLE_METRIC_ALLOWLIST:
        rows.append(
            {
                "metric": metric,
                "classification": "eligible",
                "eligible_under_policy": True,
            }
        )
    for metric, category in INELIGIBLE_METRIC_CATEGORIES.items():
        rows.append(
            {
                "metric": metric,
                "classification": category,
                "eligible_under_policy": False,
            }
        )
    rows.extend(
        [
            {
                "metric": "any_unknown_metric",
                "classification": "unknown",
                "eligible_under_policy": False,
            },
            {
                "metric": "any_calibration_metric",
                "classification": "calibration",
                "eligible_under_policy": False,
            },
            {
                "metric": "any_threshold_sensitive_metric",
                "classification": "threshold_sensitive",
                "eligible_under_policy": False,
            },
        ]
    )
    return rows


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if isinstance(value, str) and value == "":
        return True
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


def evaluate_predicate(
    row: Dict[str, Any],
    global_ctx: Dict[str, Any],
    event_evidence: Optional[Dict[str, Any]],
    *,
    selected_candidate_differs: bool = False,
    selection_mode_differs: bool = False,
) -> Dict[str, Any]:
    reason_codes: List[str] = []
    sections: Dict[str, Any] = {}

  # Section A
    a_checks: List[Dict[str, Any]] = []
    a_pass = True
    for req in build_predicate_definition()["A_evidence_completeness"]["requirements"]:
        field = req["field"]
        if field.startswith("global."):
            value = global_ctx
            for part in field.split(".")[1:]:
                value = value[part]
        else:
            value = row.get(field.replace("row.", ""))
        passed = _compare(req["operator"], value, req["value"])
        if not passed:
            a_pass = False
            reason_codes.append(f"A_failed:{field}")
        a_checks.append({"field": field, "passed": passed, "observed": value})
    sections["A_evidence_completeness"] = {"passed": a_pass, "checks": a_checks}

  # Section B
    b_checks: List[Dict[str, Any]] = []
    b_pass = True
    if not bool(row.get("build1_build2_value_equal")):
        b_pass = False
        reason_codes.append("B_failed:one_ulp_build_value_difference")
    b1 = row.get("g_r1_build1_value")
    b2 = row.get("g_r1_build2_value")
    if not _is_missing(b1) and not _is_missing(b2):
        if not np.float64(b1) == np.float64(b2):
            b_pass = False
            reason_codes.append("B_failed:float64_bit_inequality")
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
    bit_exact = bool(
        global_ctx.get("audit_integrity_checks", {}).get("build_mismatch_values_bit_exact")
    )
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

  # Section C
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

  # Section D
    d_pass = True
    d_checks: List[Dict[str, Any]] = []
    if event_evidence is None:
        d_pass = False
        reason_codes.append("D_failed:missing_score_evidence")
    else:
        for key in [
            "non_et_scores_byte_identical",
            "build1_non_et_scores_byte_identical",
            "build2_non_et_scores_byte_identical",
        ]:
            passed = bool(event_evidence.get(key))
            if not passed:
                d_pass = False
                reason_codes.append(f"D_failed:{key}")
            d_checks.append({"field": key, "passed": passed})
        max_et = event_evidence.get("maximum_et_score_absolute_difference")
        if _is_missing(max_et):
            d_pass = False
            reason_codes.append("D_failed:missing_et_score_delta")
        else:
            passed = float(max_et) <= ET_SCORE_ABSOLUTE_TOLERANCE
            if not passed:
                d_pass = False
                reason_codes.append("D_failed:et_score_delta_above_tolerance")
            d_checks.append(
                {
                    "field": "maximum_et_score_absolute_difference",
                    "passed": passed,
                    "observed": max_et,
                }
            )
    sections["D_accepted_output_comparison"] = {"passed": d_pass, "checks": d_checks}

  # Section E
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

  # Section F
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

  # Section G
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

  # Section H aggregate
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


def validate_reconciliation_json(report: Dict[str, Any]) -> None:
    required = {
        "all_validation_checks_passed": True,
        "policy_enforced": False,
        "production_validator_changed": False,
        "canonical_file_changed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
    }
    errors: List[str] = []
    for field, expected in required.items():
        if report.get(field) != expected:
            errors.append(f"{field}={report.get(field)!r} expected {expected!r}")
    integrity = report.get("audit_integrity_checks", {})
    if integrity.get("all_audit_integrity_checks_passed") is not True:
        errors.append("all_audit_integrity_checks_passed is not true")
    if errors:
        raise RuntimeError("G.D4 reconciliation evidence failed closed: " + "; ".join(errors))


def load_evidence(root: Path) -> Tuple[Dict[str, Any], pd.DataFrame, Dict[str, Dict[str, Any]]]:
    json_path = root / RECONCILIATION_JSON_PATH
    matrix_path = root / MATRIX_PATH

    json_sha = sha256_file(json_path)
    matrix_sha = sha256_file(matrix_path)
    if matrix_sha != MATRIX_SHA256:
        raise RuntimeError(
            f"Mismatch matrix SHA-256 {matrix_sha} != required {MATRIX_SHA256}"
        )

    report = json.loads(json_path.read_text(encoding="utf-8"))
    validate_reconciliation_json(report)

    matrix_df = pd.read_csv(matrix_path)
    if list(matrix_df.columns) != MATRIX_COLUMNS:
        raise RuntimeError("Mismatch matrix columns do not match required schema")
    if len(matrix_df) != 9:
        raise RuntimeError(f"Mismatch matrix row count {len(matrix_df)} != 9")

    event_map = {item["event_id"]: item for item in report.get("score_level_evidence", [])}
    return report, matrix_df, event_map


def build_evidence_provenance(
    root: Path, report: Dict[str, Any], matrix_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    json_path = root / RECONCILIATION_JSON_PATH
    matrix_path = root / MATRIX_PATH
    return [
        {
            "repository_relative_path": RECONCILIATION_JSON_PATH,
            "sha256": sha256_file(json_path),
            "row_count": None,
            "column_count": None,
            "role_in_policy_derivation": "G.D4 reconciliation audit report with score-level mechanism evidence",
            "required_fields_verified": {
                "all_validation_checks_passed": report["all_validation_checks_passed"],
                "all_audit_integrity_checks_passed": report["audit_integrity_checks"][
                    "all_audit_integrity_checks_passed"
                ],
                "policy_enforced": report["policy_enforced"],
                "production_validator_changed": report["production_validator_changed"],
                "canonical_file_changed": report["canonical_file_changed"],
                "part3b_complete": report["part3b_complete"],
                "part3c_authorized": report["part3c_authorized"],
            },
        },
        {
            "repository_relative_path": MATRIX_PATH,
            "sha256": sha256_file(matrix_path),
            "row_count": len(matrix_df),
            "column_count": len(matrix_df.columns),
            "role_in_policy_derivation": "Nine-row ET canonical mismatch matrix with current approval flags",
        },
    ]


def build_regression_fixtures(
    matrix_df: pd.DataFrame,
    report: Dict[str, Any],
    event_map: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    fixtures: List[Dict[str, Any]] = []
    for _, series in matrix_df.iterrows():
        row = series.to_dict()
        event_id = event_id_from_row(row)
        evaluation = evaluate_predicate(row, report, event_map.get(event_id))
        fixtures.append(
            {
                "fixture_role": "regression_fixture_only",
                "experiment": row["experiment"],
                "target_project": row["target_project"],
                "seed": int(row["seed"]),
                "model": row["model"],
                "selected_candidate": row["selected_candidate"],
                "selection_mode": row["selection_mode"],
                "column": row["column"],
                "event_id": event_id,
                "mechanistically_eligible_under_frozen_policy": evaluation["eligible"],
                "currently_approved_exception": bool(row["currently_approved_exception"]),
                "currently_unapproved_mismatch": bool(row["currently_unapproved_mismatch"]),
                "reason_codes": evaluation["reason_codes"],
                "predicate_results": evaluation["predicate_results"],
            }
        )
    return fixtures


def predicate_contains_hardcoded_identities(predicate: Dict[str, Any]) -> bool:
    text = json.dumps(predicate, sort_keys=True)
    return any(pattern.search(text) for pattern in HARDCODED_IDENTITY_PATTERNS)


def build_policy_specification(
    root: Path,
    starting_commit: str,
    report: Dict[str, Any],
    matrix_df: pd.DataFrame,
    event_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    fixtures = build_regression_fixtures(matrix_df, report, event_map)
    mechanistically_eligible = sum(
        1 for item in fixtures if item["mechanistically_eligible_under_frozen_policy"]
    )
    currently_approved = int(matrix_df["currently_approved_exception"].sum())
    currently_unapproved = int(matrix_df["currently_unapproved_mismatch"].sum())

    predicate = build_predicate_definition()
    if predicate_contains_hardcoded_identities(predicate):
        raise RuntimeError("Policy predicate contains prohibited project/seed/event hard-coding")

    spec: Dict[str, Any] = {
        "stage": STAGE,
        "starting_commit": starting_commit,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "policy_status": POLICY_STATUS,
        "production_validator_status": "unchanged",
        "production_authorization": False,
        "part3b_complete": False,
        "part3c_authorized": False,
        "canonical_files_changed": False,
        "policy_enforced": False,
        "production_validator_changed": False,
        "canonical_file_changed": False,
        "evidence_provenance": build_evidence_provenance(root, report, matrix_df),
        "exact_constants": {
            "et_score_absolute_tolerance": ET_SCORE_ABSOLUTE_TOLERANCE,
            "metric_absolute_tolerance": METRIC_ABSOLUTE_TOLERANCE,
            "eligible_metric_allowlist": ELIGIBLE_METRIC_ALLOWLIST,
            "exact_build_value_equality": "float64_bit_exact",
            "exact_build_score_equality": "byte_exact",
            "et_leaf5_candidate_literal": ET_LEAF5_CANDIDATE,
        },
        "metric_classifications": build_metric_classification_table(),
        "required_fields": {
            "matrix_row": [
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
                "currently_approved_exception",
                "currently_unapproved_mismatch",
            ],
            "reconciliation_json_global": [
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
            ],
            "score_evidence_event": [
                "non_et_scores_byte_identical",
                "build1_non_et_scores_byte_identical",
                "build2_non_et_scores_byte_identical",
                "maximum_et_score_absolute_difference",
                "build_score_arrays_byte_exact",
            ],
        },
        "predicate_definition": predicate,
        "ordered_evaluation_steps": build_ordered_evaluation_steps(),
        "fail_closed_rules": build_fail_closed_rules(),
        "prohibited_operations": build_prohibited_operations(),
        "concept_separation": {
            "mechanistically_eligible_under_frozen_policy": (
                "Predicate et_rank_metric_reconciliation_eligible returns true; "
                "does not change approval status."
            ),
            "currently_approved_exception": (
                "Historical approval recorded in mismatch matrix; unchanged by G.D5."
            ),
            "currently_unapproved_mismatch": (
                "Rows not currently approved; remain unapproved after G.D5."
            ),
        },
        "regression_fixtures": fixtures,
        "current_classification_counts": {
            "mechanistically_eligible_rows": mechanistically_eligible,
            "currently_approved_rows": currently_approved,
            "currently_unapproved_rows": currently_unapproved,
            "matrix_row_count": len(matrix_df),
        },
        "production_activity_counters": {
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "production_builds_executed": 0,
            "repository_production_artifacts_published": 0,
        },
        "authorization_flags": {
            "production_authorization": False,
            "part3b_complete": False,
            "part3c_authorized": False,
            "policy_enforced": False,
            "production_validator_changed": False,
            "canonical_file_changed": False,
        },
        "specification_integrity_checks": {},
    }
    return spec


def validate_specification(
    spec: Dict[str, Any],
    matrix_df: Optional[pd.DataFrame] = None,
    markdown_text: Optional[str] = None,
) -> Dict[str, bool]:
    checks: Dict[str, bool] = {}
    provenance = spec.get("evidence_provenance", [])
    checks["source_evidence_hashes_verified"] = (
        len(provenance) >= 2 and provenance[1].get("sha256") == MATRIX_SHA256
    )
    if matrix_df is not None and not matrix_df.empty:
        checks["source_evidence_schema_verified"] = list(matrix_df.columns) == MATRIX_COLUMNS
        checks["matrix_row_count_is_9"] = len(matrix_df) == 9
        checks["approved_count_is_1"] = int(matrix_df["currently_approved_exception"].sum()) == 1
        checks["unapproved_count_is_8"] = int(matrix_df["currently_unapproved_mismatch"].sum()) == 8
    else:
        checks["source_evidence_schema_verified"] = True
        checks["matrix_row_count_is_9"] = (
            spec.get("current_classification_counts", {}).get("matrix_row_count") == 9
        )
        checks["approved_count_is_1"] = (
            spec.get("current_classification_counts", {}).get("currently_approved_rows") == 1
        )
        checks["unapproved_count_is_8"] = (
            spec.get("current_classification_counts", {}).get("currently_unapproved_rows") == 8
        )
    checks["eligible_metric_allowlist_exact"] = (
        spec["exact_constants"]["eligible_metric_allowlist"] == ELIGIBLE_METRIC_ALLOWLIST
    )
    checks["exact_equality_rules_present"] = (
        spec["exact_constants"]["exact_build_value_equality"] == "float64_bit_exact"
        and spec["exact_constants"]["exact_build_score_equality"] == "byte_exact"
    )
    checks["fail_closed_rules_present"] = len(spec["fail_closed_rules"]) >= 10
    checks["predicate_free_of_identity_hardcoding"] = not predicate_contains_hardcoded_identities(
        spec["predicate_definition"]
    )
    checks["regression_fixtures_separated_from_predicate"] = all(
        item.get("fixture_role") == "regression_fixture_only"
        for item in spec["regression_fixtures"]
    )
    checks["all_nine_rows_mechanistically_eligible"] = all(
        item["mechanistically_eligible_under_frozen_policy"] for item in spec["regression_fixtures"]
    )
    checks["approval_status_unchanged"] = (
        spec["current_classification_counts"]["currently_approved_rows"] == 1
        and spec["current_classification_counts"]["currently_unapproved_rows"] == 8
    )
    checks["policy_remains_unenforced"] = spec["policy_enforced"] is False
    checks["production_flags_remain_false"] = (
        spec["production_validator_changed"] is False
        and spec["canonical_file_changed"] is False
        and spec["part3b_complete"] is False
        and spec["part3c_authorized"] is False
    )
    if markdown_text is not None:
        expected_md = render_markdown(spec)
        checks["json_markdown_consistency"] = markdown_text == expected_md
    else:
        checks["json_markdown_consistency"] = True
    checks["all_specification_checks_passed"] = all(checks.values())
    return checks


def validate_publication_candidates(
    spec: Dict[str, Any],
    json_text: str,
    md_text: str,
) -> None:
    reread_spec = json.loads(json_text)
    if md_text != render_markdown(reread_spec):
        raise RuntimeError("Markdown does not match JSON specification")
    integrity = validate_specification(reread_spec, markdown_text=md_text)
    if not integrity["all_specification_checks_passed"]:
        failed = [key for key, value in integrity.items() if not value]
        raise RuntimeError(f"Publication candidate validation failed: {failed}")


def render_markdown(spec: Dict[str, Any]) -> str:
    constants = spec["exact_constants"]
    counts = spec["current_classification_counts"]
    lines = [
        "# Part 3B ExtraTrees Reconciliation Policy Specification",
        "",
        f"**Stage:** {spec['stage']}",
        f"**Starting commit:** `{spec['starting_commit']}`",
        f"**Policy ID:** {spec['policy_id']}",
        f"**Policy version:** {spec['policy_version']}",
        "",
        "## Purpose and Non-Enforcement Warning",
        "",
        "This document freezes the exact mechanistic predicate "
        "`et_rank_metric_reconciliation_eligible` as a **specified, not enforced** policy.",
        "The production validator is **unchanged**. Production authorization is **false**.",
        "Mechanistic eligibility does **not** change current approval status.",
        "",
        f"- **Policy status:** {spec['policy_status']}",
        f"- **Production validator status:** {spec['production_validator_status']}",
        f"- **Production authorization:** {spec['production_authorization']}",
        f"- **Policy enforced:** {spec['policy_enforced']}",
        f"- **Part 3B complete:** {spec['part3b_complete']}",
        f"- **Part 3C authorized:** {spec['part3c_authorized']}",
        f"- **Canonical files changed:** {spec['canonical_files_changed']}",
        "",
        "## Evidence Inputs",
        "",
        "| Path | SHA-256 | Rows | Columns | Role |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in spec["evidence_provenance"]:
        lines.append(
            "| {path} | `{sha}` | {rows} | {cols} | {role} |".format(
                path=item["repository_relative_path"],
                sha=item["sha256"],
                rows=item.get("row_count", "n/a"),
                cols=item.get("column_count", "n/a"),
                role=item["role_in_policy_derivation"],
            )
        )
    lines.extend(
        [
            "",
            "## Exact Constants",
            "",
            f"- **ET score absolute tolerance:** {constants['et_score_absolute_tolerance']}",
            f"- **Metric absolute tolerance:** {constants['metric_absolute_tolerance']}",
            f"- **Eligible metric allowlist:** {', '.join(constants['eligible_metric_allowlist'])}",
            f"- **Exact build-value equality:** {constants['exact_build_value_equality']}",
            f"- **Exact build-score equality:** {constants['exact_build_score_equality']}",
            "",
            "## Predicate: et_rank_metric_reconciliation_eligible",
            "",
            "A mismatch row is eligible only when every section below passes.",
            "",
            "### A. Evidence Completeness",
            "- Mismatch exists in both deterministic builds.",
            "- Build 1 and Build 2 mismatch identity sets are exactly equal.",
            "- No required source role or evidence field is missing.",
            "- All G.D4 audit-integrity checks are true.",
            "",
            "### B. Exact Deterministic Equality",
            "- Build 1 and Build 2 mismatch values are float64 bit-exact.",
            "- Build 1 and Build 2 result/validation/prediction SHA-256 values are equal.",
            "- Build 1 and Build 2 score arrays are byte-identical.",
            "- Tolerance-based equality must not substitute for any requirement here.",
            "",
            "### C. ET Mechanism",
            f"- Direct model is `{ET_LEAF5_CANDIDATE}`, or selected candidate is `{ET_LEAF5_CANDIDATE}`, "
            f"or a soft ensemble explicitly contains `{ET_LEAF5_CANDIDATE}`.",
            "",
            "### D. Accepted-Output Comparison",
            f"- Non-ET validation and test score arrays are byte-identical to accepted tracked arrays.",
            f"- Maximum ET validation/test score absolute difference is at most {ET_SCORE_ABSOLUTE_TOLERANCE}.",
            "- Missing score evidence causes rejection.",
            "",
            "### E. Metric Classification",
            f"- Eligible metrics: {', '.join(ELIGIBLE_METRIC_ALLOWLIST)}.",
            "- Threshold-sensitive, calibration, and unknown metrics are ineligible.",
            "",
            "### F. Metric Delta",
            f"- Absolute metric difference from canonical is at most {METRIC_ABSOLUTE_TOLERANCE} for both builds.",
            "- Relative difference is reported but does not replace the absolute threshold.",
            "- No rounding, quantization, truncation, post-hoc replacement, averaging, or output copying.",
            "",
            "### G. Validation and Categorical Invariants",
            "- Validation categorical and numeric mismatch counts are zero for both builds.",
            "- Validation reconstructions are exactly equal across builds.",
            "- Result-row categorical identity, selected candidate, and selection mode are unchanged.",
            "- No validation/test role mixing; no test-set use in model selection.",
            "",
            "### H. Fail-Closed Behavior",
            "- Any missing field, null/NaN, unknown metric, build disagreement, score mismatch, "
            "validation mismatch, or non-ET-derived row rejects eligibility.",
            "",
            "## Decision Table",
            "",
            "| Concept | Meaning | Changes approval? |",
            "| --- | --- | --- |",
            "| mechanistically_eligible_under_frozen_policy | Predicate passes all sections | No |",
            "| currently_approved_exception | Historical approval in mismatch matrix | No (unchanged) |",
            "| currently_unapproved_mismatch | Not currently approved | No (unchanged) |",
            "",
            "## Metric Classification Table",
            "",
            "| Metric | Classification | Eligible |",
            "| --- | --- | --- |",
        ]
    )
    for item in spec["metric_classifications"]:
        lines.append(
            f"| {item['metric']} | {item['classification']} | {item['eligible_under_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Tolerance vs Exact Equality",
            "",
            "- **Exact equality** applies to Build 1/Build 2 mismatch values (float64 bit-exact) "
            "and score arrays (byte-exact).",
            f"- **Tolerance** applies only to ET score deltas (≤ {ET_SCORE_ABSOLUTE_TOLERANCE}) "
            f"and metric deltas (≤ {METRIC_ABSOLUTE_TOLERANCE}).",
            "- Relative metric differences are reported for transparency but never substitute "
            "for the absolute threshold.",
            "",
            "## Fail-Closed Conditions",
            "",
        ]
    )
    for rule in spec["fail_closed_rules"]:
        lines.append(f"- {rule}")
    lines.extend(["", "## Prohibited Operations", ""])
    for op in spec["prohibited_operations"]:
        lines.append(f"- {op}")
    lines.extend(
        [
            "",
            "## Current Classification",
            "",
            f"- **Mechanistically eligible rows:** {counts['mechanistically_eligible_rows']}",
            f"- **Currently approved rows:** {counts['currently_approved_rows']}",
            f"- **Currently unapproved rows:** {counts['currently_unapproved_rows']}",
            "",
            "## Regression Fixtures (Nine Rows)",
            "",
            "| Seed | Model | Metric | Mechanistically eligible | Currently approved | "
            "Currently unapproved | Reason codes |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for fixture in spec["regression_fixtures"]:
        lines.append(
            "| {seed} | {model} | {metric} | {eligible} | {approved} | {unapproved} | {reasons} |".format(
                seed=fixture["seed"],
                model=fixture["model"],
                metric=fixture["column"],
                eligible=fixture["mechanistically_eligible_under_frozen_policy"],
                approved=fixture["currently_approved_exception"],
                unapproved=fixture["currently_unapproved_mismatch"],
                reasons=", ".join(fixture["reason_codes"]) if fixture["reason_codes"] else "none",
            )
        )
    lines.extend(
        [
            "",
            "## Production and Authorization Status",
            "",
            f"- **Model fits executed:** {spec['production_activity_counters']['model_fits_executed']}",
            f"- **Prediction calls executed:** {spec['production_activity_counters']['prediction_calls_executed']}",
            f"- **Production builds executed:** {spec['production_activity_counters']['production_builds_executed']}",
            "- **Repository production artifacts published:** "
            f"{spec['production_activity_counters']['repository_production_artifacts_published']}",
            f"- **Production authorization:** {spec['authorization_flags']['production_authorization']}",
            f"- **Policy enforced:** {spec['authorization_flags']['policy_enforced']}",
            f"- **Production validator changed:** {spec['authorization_flags']['production_validator_changed']}",
            f"- **Canonical file changed:** {spec['authorization_flags']['canonical_file_changed']}",
            f"- **Part 3B complete:** {spec['authorization_flags']['part3b_complete']}",
            f"- **Part 3C authorized:** {spec['authorization_flags']['part3c_authorized']}",
            "",
        ]
    )
    return "\n".join(lines)


def _cleanup_publication_artifacts(*paths: Optional[Path]) -> None:
    for path in paths:
        if path is not None and path.exists():
            path.unlink()


def publish_outputs_transactionally(
    spec: Dict[str, Any],
    json_path: Path,
    md_path: Path,
) -> Dict[str, bool]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    existing_json_bytes = json_path.read_bytes() if json_path.is_file() else b""
    existing_md_bytes = md_path.read_bytes() if md_path.is_file() else b""

    json_text = json.dumps(spec, indent=2, cls=NumpyEncoder) + "\n"
    md_text = render_markdown(spec)

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=str(json_path.parent), delete=False
    ) as tmp_json:
        tmp_json.write(json_text)
        tmp_json_path = Path(tmp_json.name)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=str(md_path.parent), delete=False
    ) as tmp_md:
        tmp_md.write(md_text)
        tmp_md_path = Path(tmp_md.name)

    backup_json_path: Optional[Path] = None
    backup_md_path: Optional[Path] = None
    replaced_json = False
    replaced_md = False

    try:
        validate_publication_candidates(spec, json_text, md_text)

        if json_path.is_file():
            backup_json_path = json_path.with_suffix(json_path.suffix + ".pubbak")
            json_path.replace(backup_json_path)
        tmp_json_path.replace(json_path)
        replaced_json = True
        tmp_json_path = None

        try:
            if md_path.is_file():
                backup_md_path = md_path.with_suffix(md_path.suffix + ".pubbak")
                md_path.replace(backup_md_path)
            tmp_md_path.replace(md_path)
            replaced_md = True
            tmp_md_path = None
        except Exception:
            if backup_json_path is not None and backup_json_path.exists():
                if json_path.exists():
                    json_path.unlink()
                backup_json_path.replace(json_path)
                replaced_json = False
            if backup_md_path is not None and backup_md_path.exists():
                if md_path.exists():
                    md_path.unlink()
                backup_md_path.replace(md_path)
            raise

        if backup_json_path is not None and backup_json_path.exists():
            backup_json_path.unlink()
        if backup_md_path is not None and backup_md_path.exists():
            backup_md_path.unlink()

        return {
            "json_published": True,
            "markdown_published": True,
            "transactional_publication_passed": True,
        }
    except Exception:
        if replaced_json and backup_json_path is not None and backup_json_path.exists():
            if json_path.exists():
                json_path.unlink()
            backup_json_path.replace(json_path)
        elif replaced_json and json_path.exists():
            json_path.unlink()
            if existing_json_bytes:
                json_path.write_bytes(existing_json_bytes)

        if replaced_md and backup_md_path is not None and backup_md_path.exists():
            if md_path.exists():
                md_path.unlink()
            backup_md_path.replace(md_path)
        elif replaced_md and md_path.exists():
            md_path.unlink()
            if existing_md_bytes:
                md_path.write_bytes(existing_md_bytes)
        elif backup_md_path is not None and backup_md_path.exists() and not md_path.exists():
            backup_md_path.replace(md_path)

        _cleanup_publication_artifacts(tmp_json_path, tmp_md_path)
        for backup in (backup_json_path, backup_md_path):
            if backup is not None and backup.exists():
                backup.unlink()
        raise


def generate_policy(root: Optional[Path] = None) -> Dict[str, Any]:
    root = root or repo_root()
    starting_commit = git_starting_commit()
    report, matrix_df, event_map = load_evidence(root)
    spec = build_policy_specification(root, starting_commit, report, matrix_df, event_map)
    md_text = render_markdown(spec)
    integrity = validate_specification(spec, matrix_df, md_text)
    spec["specification_integrity_checks"] = integrity
    if not integrity["all_specification_checks_passed"]:
        failed = [key for key, value in integrity.items() if not value]
        raise RuntimeError(f"Pre-publication validation failed: {failed}")

    json_path = root / JSON_OUTPUT_PATH
    md_path = root / MD_OUTPUT_PATH
    publication = publish_outputs_transactionally(spec, json_path, md_path)
    spec["specification_integrity_checks"]["transactional_publication_passed"] = publication[
        "transactional_publication_passed"
    ]
    return spec


# ---------------------------------------------------------------------------
# Self-tests (synthetic data only; no repository evidence)
# ---------------------------------------------------------------------------


def _synthetic_global_ctx(**overrides: Any) -> Dict[str, Any]:
    base = {
        "strict_mismatch_count_build1": 9,
        "strict_mismatch_count_build2": 9,
        "build_mismatch_identity_sets_equal": True,
        "build_result_reconstruction_sha_equal": True,
        "build_validation_reconstruction_sha_equal": True,
        "build_prediction_within_sha_equal": True,
        "build_prediction_cross_sha_equal": True,
        "validation_categorical_mismatch_count_build1": 0,
        "validation_categorical_mismatch_count_build2": 0,
        "validation_numeric_mismatch_count_build1": 0,
        "validation_numeric_mismatch_count_build2": 0,
        "build1_build2_validation_reconstructions_equal": True,
        "categorical_mismatch_count": 0,
        "audit_integrity_checks": {
            "exact_source_role_set_passed": True,
            "all_audit_integrity_checks_passed": True,
            "build_mismatch_values_bit_exact": True,
        },
    }
    base.update(overrides)
    return base


def _synthetic_event_evidence(**overrides: Any) -> Dict[str, Any]:
    base = {
        "non_et_scores_byte_identical": True,
        "build1_non_et_scores_byte_identical": True,
        "build2_non_et_scores_byte_identical": True,
        "maximum_et_score_absolute_difference": 4.440892098500626e-16,
        "build_score_arrays_byte_exact": True,
    }
    base.update(overrides)
    return base


def _synthetic_row(**overrides: Any) -> Dict[str, Any]:
    base = {
        "experiment": "cross_project",
        "target_project": "SYNTH",
        "seed": 99,
        "model": "ET_leaf5",
        "selected_candidate": "ET_leaf5",
        "selection_mode": "single_candidate_balanced_threshold",
        "column": "roc_auc",
        "g_r1_build1_value": 0.5,
        "g_r1_build2_value": 0.5,
        "build1_build2_value_equal": True,
        "absolute_difference_build1": 1e-8,
        "absolute_difference_build2": 1e-8,
        "relative_difference_build1": 1e-8,
        "relative_difference_build2": 1e-8,
        "direct_et_model": True,
        "selected_candidate_is_et": True,
        "soft_ensemble_contains_et": False,
        "et_derived_row": True,
        "threshold_sensitive_metric": False,
        "calibration_metric": False,
    }
    base.update(overrides)
    return base


def _self_test_valid_et_roc_auc_accepted() -> bool:
    result = evaluate_predicate(
        _synthetic_row(column="roc_auc"),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is True


def _self_test_valid_et_avg_precision_accepted() -> bool:
    result = evaluate_predicate(
        _synthetic_row(column="avg_precision"),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is True


def _self_test_one_ulp_build_value_difference_rejected() -> bool:
    value = np.float64(0.5)
    ulp = float(np.nextafter(value, np.float64(1.0)))
    result = evaluate_predicate(
        _synthetic_row(
            g_r1_build1_value=float(value),
            g_r1_build2_value=ulp,
            build1_build2_value_equal=False,
        ),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_build_score_array_difference_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(build_score_arrays_byte_exact=False),
    )
    return result["eligible"] is False


def _self_test_non_et_accepted_score_difference_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(non_et_scores_byte_identical=False),
    )
    return result["eligible"] is False


def _self_test_et_score_delta_above_tolerance_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(maximum_et_score_absolute_difference=2e-15),
    )
    return result["eligible"] is False


def _self_test_metric_delta_above_tolerance_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(
            absolute_difference_build1=2e-7,
            absolute_difference_build2=1e-8,
        ),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_brier_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(column="brier", calibration_metric=True),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_threshold_sensitive_metric_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(column="f1", threshold_sensitive_metric=True),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_unknown_metric_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(column="unknown_metric"),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_missing_required_field_rejected() -> bool:
    row = _synthetic_row()
    del row["absolute_difference_build1"]
    result = evaluate_predicate(row, _synthetic_global_ctx(), _synthetic_event_evidence())
    return result["eligible"] is False


def _self_test_selected_candidate_difference_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
        selected_candidate_differs=True,
    )
    return result["eligible"] is False


def _self_test_selection_mode_difference_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
        selection_mode_differs=True,
    )
    return result["eligible"] is False


def _self_test_validation_mismatch_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(),
        _synthetic_global_ctx(validation_numeric_mismatch_count_build1=1),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_non_et_derived_row_rejected() -> bool:
    result = evaluate_predicate(
        _synthetic_row(
            direct_et_model=False,
            selected_candidate_is_et=False,
            soft_ensemble_contains_et=False,
            et_derived_row=False,
        ),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is False


def _self_test_project_seed_independent_equivalent_row_accepted() -> bool:
    result = evaluate_predicate(
        _synthetic_row(
            target_project="OTHER",
            seed=7,
            model="AQRPE_v2_synth",
            selected_candidate="ET_leaf5",
            direct_et_model=False,
            selected_candidate_is_et=True,
        ),
        _synthetic_global_ctx(),
        _synthetic_event_evidence(),
    )
    return result["eligible"] is True


def _synthetic_minimal_publish_spec() -> Dict[str, Any]:
    fixtures = [
        {
            "fixture_role": "regression_fixture_only",
            "experiment": "cross_project",
            "target_project": "SYNTH",
            "seed": 99,
            "model": "ET_leaf5",
            "selected_candidate": "ET_leaf5",
            "selection_mode": "single_candidate_balanced_threshold",
            "column": "roc_auc",
            "event_id": "cross_project__SYNTH__seed_099",
            "mechanistically_eligible_under_frozen_policy": True,
            "currently_approved_exception": False,
            "currently_unapproved_mismatch": True,
            "reason_codes": [],
            "predicate_results": {},
        }
    ]
    for index in range(8):
        fixtures.append(
            {
                **fixtures[0],
                "seed": 100 + index,
                "event_id": f"cross_project__SYNTH__seed_{100 + index:03d}",
            }
        )
    fixtures.append(
        {
            **fixtures[0],
            "seed": 42,
            "currently_approved_exception": True,
            "currently_unapproved_mismatch": False,
            "event_id": "cross_project__SYNTH__seed_042",
        }
    )
    return {
        "stage": STAGE,
        "starting_commit": STARTING_COMMIT,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "policy_status": POLICY_STATUS,
        "production_validator_status": "unchanged",
        "production_authorization": False,
        "part3b_complete": False,
        "part3c_authorized": False,
        "canonical_files_changed": False,
        "policy_enforced": False,
        "production_validator_changed": False,
        "canonical_file_changed": False,
        "evidence_provenance": [
            {
                "repository_relative_path": RECONCILIATION_JSON_PATH,
                "sha256": "0" * 64,
                "row_count": None,
                "column_count": None,
                "role_in_policy_derivation": "synthetic",
            },
            {
                "repository_relative_path": MATRIX_PATH,
                "sha256": MATRIX_SHA256,
                "row_count": 9,
                "column_count": len(MATRIX_COLUMNS),
                "role_in_policy_derivation": "synthetic",
            },
        ],
        "exact_constants": {
            "et_score_absolute_tolerance": ET_SCORE_ABSOLUTE_TOLERANCE,
            "metric_absolute_tolerance": METRIC_ABSOLUTE_TOLERANCE,
            "eligible_metric_allowlist": ELIGIBLE_METRIC_ALLOWLIST,
            "exact_build_value_equality": "float64_bit_exact",
            "exact_build_score_equality": "byte_exact",
            "et_leaf5_candidate_literal": ET_LEAF5_CANDIDATE,
        },
        "metric_classifications": build_metric_classification_table(),
        "required_fields": {},
        "predicate_definition": build_predicate_definition(),
        "ordered_evaluation_steps": build_ordered_evaluation_steps(),
        "fail_closed_rules": build_fail_closed_rules(),
        "prohibited_operations": build_prohibited_operations(),
        "concept_separation": {},
        "regression_fixtures": fixtures,
        "current_classification_counts": {
            "mechanistically_eligible_rows": 9,
            "currently_approved_rows": 1,
            "currently_unapproved_rows": 8,
            "matrix_row_count": 9,
        },
        "production_activity_counters": {
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "production_builds_executed": 0,
            "repository_production_artifacts_published": 0,
        },
        "authorization_flags": {
            "production_authorization": False,
            "part3b_complete": False,
            "part3c_authorized": False,
            "policy_enforced": False,
            "production_validator_changed": False,
            "canonical_file_changed": False,
        },
        "specification_integrity_checks": {},
    }


def _self_test_markdown_json_disagreement_rejected() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        json_path = tmp_dir / "policy.json"
        md_path = tmp_dir / "policy.md"
        json_path.write_text("{}\n", encoding="utf-8")
        md_path.write_text("# existing\n", encoding="utf-8")
        before_json = json_path.read_bytes()
        before_md = md_path.read_bytes()
        spec = _synthetic_minimal_publish_spec()
        json_text = json.dumps(spec, indent=2, cls=NumpyEncoder) + "\n"
        md_text = render_markdown(spec) + "\nDISAGREE\n"
        try:
            validate_publication_candidates(spec, json_text, md_text)
            return False
        except RuntimeError:
            pass
        return json_path.read_bytes() == before_json and md_path.read_bytes() == before_md


def _self_test_partial_publication_failure_rolls_back() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        json_path = tmp_dir / "policy.json"
        md_path = tmp_dir / "policy.md"
        json_path.write_text('{"existing": true}\n', encoding="utf-8")
        md_path.write_text("# existing\n", encoding="utf-8")
        before_json = json_path.read_bytes()
        before_md = md_path.read_bytes()
        spec = _synthetic_minimal_publish_spec()
        original_replace = Path.replace

        def failing_md_replace(self: Path, target: Path) -> Path:
            if target == md_path and not self.name.endswith(".pubbak"):
                raise OSError("simulated md replace failure")
            return original_replace(self, target)

        Path.replace = failing_md_replace  # type: ignore[method-assign]
        try:
            try:
                publish_outputs_transactionally(spec, json_path, md_path)
                return False
            except OSError:
                pass
        finally:
            Path.replace = original_replace  # type: ignore[method-assign]
        return json_path.read_bytes() == before_json and md_path.read_bytes() == before_md


def run_self_tests() -> Dict[str, Any]:
    tests = [
        ("valid_et_roc_auc_row_accepted", _self_test_valid_et_roc_auc_accepted),
        ("valid_et_avg_precision_row_accepted", _self_test_valid_et_avg_precision_accepted),
        ("one_ulp_build_value_difference_rejected", _self_test_one_ulp_build_value_difference_rejected),
        ("build_score_array_difference_rejected", _self_test_build_score_array_difference_rejected),
        ("non_et_accepted_score_difference_rejected", _self_test_non_et_accepted_score_difference_rejected),
        ("et_score_delta_above_tolerance_rejected", _self_test_et_score_delta_above_tolerance_rejected),
        ("metric_delta_above_tolerance_rejected", _self_test_metric_delta_above_tolerance_rejected),
        ("brier_rejected", _self_test_brier_rejected),
        ("threshold_sensitive_metric_rejected", _self_test_threshold_sensitive_metric_rejected),
        ("unknown_metric_rejected", _self_test_unknown_metric_rejected),
        ("missing_required_field_rejected", _self_test_missing_required_field_rejected),
        ("selected_candidate_difference_rejected", _self_test_selected_candidate_difference_rejected),
        ("selection_mode_difference_rejected", _self_test_selection_mode_difference_rejected),
        ("validation_mismatch_rejected", _self_test_validation_mismatch_rejected),
        ("non_et_derived_row_rejected", _self_test_non_et_derived_row_rejected),
        ("project_seed_independent_equivalent_row_accepted", _self_test_project_seed_independent_equivalent_row_accepted),
        ("markdown_json_disagreement_rejected", _self_test_markdown_json_disagreement_rejected),
        ("partial_publication_failure_rolls_back", _self_test_partial_publication_failure_rolls_back),
    ]
    results = [{"test_name": name, "passed": bool(fn())} for name, fn in tests]
    passed = sum(1 for item in results if item["passed"])
    return {
        "tests": results,
        "passed": passed,
        "expected": len(tests),
        "failed": len(tests) - passed,
        "total": len(tests),
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "production_builds_executed": 0,
        "repository_production_artifacts_published": 0,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze exact ET reconciliation policy as non-enforced specification."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run synthetic no-fit self-tests only.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        summary = run_self_tests()
        print(
            json.dumps(
                {
                    "self_tests": (
                        f"{summary['passed']} / {summary['expected']} / "
                        f"{summary['total']} / {summary['failed']}"
                    ),
                    "model_fits_executed": summary["model_fits_executed"],
                    "prediction_calls_executed": summary["prediction_calls_executed"],
                    "production_builds_executed": summary["production_builds_executed"],
                    "repository_production_artifacts_published": summary[
                        "repository_production_artifacts_published"
                    ],
                    "tests": summary["tests"],
                },
                indent=2,
            )
        )
        return 0 if summary["failed"] == 0 else 1

    spec = generate_policy()
    print(
        json.dumps(
            {
                "stage": spec["stage"],
                "policy_status": spec["policy_status"],
                "mechanistically_eligible_rows": spec["current_classification_counts"][
                    "mechanistically_eligible_rows"
                ],
                "currently_approved_rows": spec["current_classification_counts"][
                    "currently_approved_rows"
                ],
                "currently_unapproved_rows": spec["current_classification_counts"][
                    "currently_unapproved_rows"
                ],
                "all_specification_checks_passed": spec["specification_integrity_checks"][
                    "all_specification_checks_passed"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
