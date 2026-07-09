#!/usr/bin/env python3
"""Part 3B.2R.1-G.D4: Persist and audit ExtraTrees canonical-reconciliation evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

STARTING_COMMIT = "82d284f606ba4b06b4ee6ef46ab279d914028eef"

RECON_RTOL = 1e-10
RECON_ATOL = 1e-12
ET_SCORE_ATOL = 1e-15
ET_RANK_METRIC_ATOL = 1e-7

CANDIDATES = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]

RESULT_IDENTITY = [
    "experiment",
    "target_project",
    "seed",
    "model",
    "selected_candidate",
    "selection_mode",
]
VALIDATION_IDENTITY = ["experiment", "target_project", "seed", "candidate", "mode"]

RESULT_RECONSTRUCTION_COLUMNS = [
    "experiment",
    "target_project",
    "seed",
    "model",
    "selected_candidate",
    "selection_mode",
    "threshold",
    "selection_score",
    "avg_precision",
    "roc_auc",
    "mcc",
    "f1",
    "balanced_accuracy",
    "precision",
    "recall",
    "brier",
    "precision_at_10pct",
    "recall_at_10pct",
    "lift_at_10pct",
    "precision_at_20pct",
    "recall_at_20pct",
    "lift_at_20pct",
]

VALIDATION_RECONSTRUCTION_COLUMNS = [
    "experiment",
    "target_project",
    "seed",
    "candidate",
    "mode",
    "val_threshold",
    "val_selection_score",
    "val_avg_precision",
    "val_roc_auc",
    "val_mcc",
    "val_f1",
    "val_balanced_accuracy",
    "val_precision",
    "val_recall",
    "val_brier",
    "val_precision_at_10pct",
    "val_recall_at_10pct",
    "val_lift_at_10pct",
    "val_precision_at_20pct",
    "val_recall_at_20pct",
    "val_lift_at_20pct",
]

RANK_SENSITIVE_METRICS = {
    "roc_auc",
    "avg_precision",
    "precision_at_10pct",
    "recall_at_10pct",
    "lift_at_10pct",
    "precision_at_20pct",
    "recall_at_20pct",
    "lift_at_20pct",
}
THRESHOLD_SENSITIVE_METRICS = {
    "threshold",
    "selection_score",
    "precision",
    "recall",
    "f1",
    "mcc",
    "balanced_accuracy",
}
CALIBRATION_METRICS = {"brier"}

APPROVED_EXCEPTION_EVENT = {
    "experiment": "cross_project",
    "target_project": "JM1",
    "seed": 42,
    "model": "AQRPE_v2_rank",
    "selected_candidate": "ET_leaf5",
    "selection_mode": "rank_objective_fixed_threshold",
    "column": "roc_auc",
}
APPROVED_EXCEPTION_CANONICAL_VALUE = 0.6700602041438307
APPROVED_EXCEPTION_RECON_VALUE = 0.6700601613088453

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


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv_round_trip(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip")


def read_gz_round_trip(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, compression="gzip", float_precision="round_trip")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataframe_shape(path: Path, compression: Optional[str] = None) -> Tuple[int, int]:
    df = pd.read_csv(path, compression=compression, float_precision="round_trip")
    return int(len(df)), int(len(df.columns))


def source_record(role: str, path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing source for role {role}: {path}")
    compression = "gzip" if path.suffix == ".gz" else None
    rows, cols = dataframe_shape(path, compression=compression)
    root = repo_root()
    try:
        rel = str(path.resolve().relative_to(root.resolve()))
        stored_path = rel
    except ValueError:
        stored_path = str(path.resolve())
    return {
        "source_role": role,
        "absolute_or_repository_path": stored_path,
        "size_bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
        "row_count": rows,
        "column_count": cols,
    }


def align_rows(df: pd.DataFrame, identity: Sequence[str]) -> pd.DataFrame:
    out = df.copy()
    for col in identity:
        out[col] = out[col].astype(str)
    return out.sort_values(list(identity)).reset_index(drop=True)


def numeric_columns_result() -> List[str]:
    cat = set(RESULT_IDENTITY)
    return [c for c in RESULT_RECONSTRUCTION_COLUMNS if c not in cat]


def numeric_columns_validation() -> List[str]:
    cat = set(VALIDATION_IDENTITY)
    return [c for c in VALIDATION_RECONSTRUCTION_COLUMNS if c not in cat]


def et_flags(row: pd.Series) -> Tuple[bool, bool, bool, bool]:
    direct_et = str(row["model"]) == "ET_leaf5"
    selected_et = str(row["selected_candidate"]) == "ET_leaf5"
    soft_contains = False
    if str(row["model"]) == "AQRPE_v2_soft_top3":
        soft_contains = "ET_leaf5" in str(row["selected_candidate"]).split("|")
    et_derived = direct_et or selected_et or soft_contains
    return direct_et, selected_et, soft_contains, et_derived


def is_approved_exception_row(
    row: Dict[str, Any],
    col: str,
    canon_val: float,
    recon_val: float,
) -> bool:
    if col != APPROVED_EXCEPTION_EVENT["column"]:
        return False
    for key in ("experiment", "target_project", "model", "selected_candidate", "selection_mode"):
        if str(row[key]) != str(APPROVED_EXCEPTION_EVENT[key]):
            return False
    if int(row["seed"]) != int(APPROVED_EXCEPTION_EVENT["seed"]):
        return False
    return (
        abs(float(canon_val) - APPROVED_EXCEPTION_CANONICAL_VALUE) <= 1e-15
        and abs(float(recon_val) - APPROVED_EXCEPTION_RECON_VALUE) <= 1e-15
    )


def mismatch_identity(m: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        m["experiment"],
        m["target_project"],
        int(m["seed"]),
        m["model"],
        m["selected_candidate"],
        m["selection_mode"],
        m["column"],
    )


def find_strict_mismatches(
    recon: pd.DataFrame,
    canonical: pd.DataFrame,
    build_label: str,
) -> List[Dict[str, Any]]:
    recon_a = align_rows(recon[RESULT_RECONSTRUCTION_COLUMNS], RESULT_IDENTITY)
    canon_a = align_rows(canonical[RESULT_RECONSTRUCTION_COLUMNS], RESULT_IDENTITY)
    merged = recon_a.merge(
        canon_a,
        on=RESULT_IDENTITY,
        how="outer",
        indicator=True,
        suffixes=("_recon", "_canon"),
    )
    if not (merged["_merge"] == "both").all():
        raise RuntimeError(f"{build_label}: categorical alignment failure")

    mismatches: List[Dict[str, Any]] = []
    for _, mrow in merged.iterrows():
        row_dict = {k: mrow[k] for k in RESULT_IDENTITY}
        direct_et, selected_et, soft_contains, et_derived = et_flags(mrow)
        for col in numeric_columns_result():
            recon_val = float(mrow[f"{col}_recon"])
            canon_val = float(mrow[f"{col}_canon"])
            if np.isclose(recon_val, canon_val, rtol=RECON_RTOL, atol=RECON_ATOL, equal_nan=True):
                continue
            abs_diff = abs(recon_val - canon_val)
            rel_diff = abs_diff / abs(canon_val) if canon_val != 0 else abs_diff
            mismatches.append(
                {
                    "experiment": row_dict["experiment"],
                    "target_project": row_dict["target_project"],
                    "seed": int(mrow["seed"]),
                    "model": row_dict["model"],
                    "selected_candidate": row_dict["selected_candidate"],
                    "selection_mode": row_dict["selection_mode"],
                    "column": col,
                    "canonical_value": canon_val,
                    f"{build_label}_value": recon_val,
                    "absolute_difference": abs_diff,
                    "relative_difference": rel_diff,
                    "within_1e_7": abs_diff <= ET_RANK_METRIC_ATOL,
                    "direct_et_model": direct_et,
                    "selected_candidate_is_et": selected_et,
                    "soft_ensemble_contains_et": soft_contains,
                    "et_derived_row": et_derived,
                    "rank_sensitive_metric": col in RANK_SENSITIVE_METRICS,
                    "threshold_sensitive_metric": col in THRESHOLD_SENSITIVE_METRICS,
                    "calibration_metric": col in CALIBRATION_METRICS,
                }
            )
    return mismatches


def lookup_accepted_value(
    accepted_recon: pd.DataFrame,
    identity: Dict[str, Any],
    column: str,
) -> float:
    mask = pd.Series(True, index=accepted_recon.index)
    for key in RESULT_IDENTITY:
        if key == "seed":
            mask &= accepted_recon[key].astype(int) == int(identity[key])
        else:
            mask &= accepted_recon[key].astype(str) == str(identity[key])
    rows = accepted_recon.loc[mask]
    if len(rows) != 1:
        raise RuntimeError(f"Accepted reconstruction lookup failed for {identity}")
    return float(rows.iloc[0][column])


def compare_validation(
    recon: pd.DataFrame,
    canonical: pd.DataFrame,
) -> Dict[str, Any]:
    recon_a = align_rows(recon[VALIDATION_RECONSTRUCTION_COLUMNS], VALIDATION_IDENTITY)
    canon_a = align_rows(canonical[VALIDATION_RECONSTRUCTION_COLUMNS], VALIDATION_IDENTITY)
    merged = recon_a.merge(
        canon_a,
        on=VALIDATION_IDENTITY,
        how="outer",
        indicator=True,
        suffixes=("_recon", "_canon"),
    )
    cat_mismatches = int((merged["_merge"] != "both").sum())
    numeric_mismatches = 0
    if cat_mismatches == 0:
        merged = merged[merged["_merge"] == "both"].reset_index(drop=True)
        for col in numeric_columns_validation():
            a = merged[f"{col}_recon"].to_numpy(dtype=float)
            b = merged[f"{col}_canon"].to_numpy(dtype=float)
            close = np.isclose(a, b, rtol=RECON_RTOL, atol=RECON_ATOL, equal_nan=True)
            numeric_mismatches += int((~close).sum())
    return {
        "validation_categorical_mismatch_count": cat_mismatches,
        "validation_numeric_mismatch_count": numeric_mismatches,
    }


def event_id_for(experiment: str, target_project: str, seed: int) -> str:
    return f"{experiment}__{target_project}__seed_{seed:03d}"


def compare_prediction_scores(
    g_r1_pred: pd.DataFrame,
    accepted_pred: pd.DataFrame,
    event_id: str,
) -> Dict[str, Any]:
    sort_cols = ["split_role", "split_position", "sample_uid"]
    g_event = g_r1_pred[g_r1_pred["event_id"] == event_id].sort_values(sort_cols).reset_index(drop=True)
    a_event = accepted_pred[g_r1_pred.columns.intersection(accepted_pred.columns)]
    a_event = accepted_pred[accepted_pred["event_id"] == event_id].sort_values(sort_cols).reset_index(drop=True)
    if len(g_event) != len(a_event):
        raise RuntimeError(f"Prediction ledger row count mismatch for {event_id}")

    candidate_evidence: Dict[str, Any] = {}
    max_val_diff = 0.0
    max_test_diff = 0.0
    non_et_byte_identical = True
    max_et_diff = 0.0

    for cand in CANDIDATES:
        col = f"score__{cand}"
        g_val = g_event.loc[g_event["split_role"] == "validation", col].to_numpy(dtype=float)
        a_val = a_event.loc[a_event["split_role"] == "validation", col].to_numpy(dtype=float)
        g_test = g_event.loc[g_event["split_role"] == "test", col].to_numpy(dtype=float)
        a_test = a_event.loc[a_event["split_role"] == "test", col].to_numpy(dtype=float)

        val_byte_equal = bool(g_val.tobytes() == a_val.tobytes())
        test_byte_equal = bool(g_test.tobytes() == a_test.tobytes())
        val_abs_diff = float(np.max(np.abs(g_val - a_val))) if len(g_val) else 0.0
        test_abs_diff = float(np.max(np.abs(g_test - a_test))) if len(g_test) else 0.0

        candidate_evidence[cand] = {
            "validation_score_byte_equal": val_byte_equal,
            "test_score_byte_equal": test_byte_equal,
            "maximum_validation_absolute_score_difference": val_abs_diff,
            "maximum_test_absolute_score_difference": test_abs_diff,
        }

        max_val_diff = max(max_val_diff, val_abs_diff)
        max_test_diff = max(max_test_diff, test_abs_diff)
        if cand == "ET_leaf5":
            max_et_diff = max(max_et_diff, val_abs_diff, test_abs_diff)
        elif not (val_byte_equal and test_byte_equal):
            non_et_byte_identical = False

    return {
        "event_id": event_id,
        "candidate_score_evidence": candidate_evidence,
        "maximum_validation_absolute_score_difference": max_val_diff,
        "maximum_test_absolute_score_difference": max_test_diff,
        "maximum_et_score_absolute_difference": max_et_diff,
        "non_et_scores_byte_identical": non_et_byte_identical,
    }


def build_mismatch_matrix(
    b1_mismatches: List[Dict[str, Any]],
    b2_mismatches: List[Dict[str, Any]],
    accepted_recon: pd.DataFrame,
) -> pd.DataFrame:
    b2_by_identity = {mismatch_identity(m): m for m in b2_mismatches}
    rows: List[Dict[str, Any]] = []
    for m1 in b1_mismatches:
        ident = mismatch_identity(m1)
        m2 = b2_by_identity[ident]
        identity = {k: m1[k] for k in RESULT_IDENTITY}
        accepted_val = lookup_accepted_value(accepted_recon, identity, m1["column"])
        build_equal = bool(
            np.isclose(
                m1["build1_value"],
                m2["build2_value"],
                rtol=RECON_RTOL,
                atol=RECON_ATOL,
                equal_nan=True,
            )
        )
        approved = is_approved_exception_row(
            identity,
            m1["column"],
            m1["canonical_value"],
            m1["build1_value"],
        )
        status = "approved_existing_exception" if approved else "unapproved_systematic_et_difference"
        g_r1_vs_accepted = abs(float(m1["build1_value"]) - accepted_val)
        rows.append(
            {
                "mismatch_status": status,
                "experiment": m1["experiment"],
                "target_project": m1["target_project"],
                "seed": int(m1["seed"]),
                "model": m1["model"],
                "selected_candidate": m1["selected_candidate"],
                "selection_mode": m1["selection_mode"],
                "column": m1["column"],
                "canonical_value": m1["canonical_value"],
                "g_r1_build1_value": m1["build1_value"],
                "g_r1_build2_value": m2["build2_value"],
                "accepted_tracked_part3b_value": accepted_val,
                "build1_build2_value_equal": build_equal,
                "absolute_difference_build1": m1["absolute_difference"],
                "absolute_difference_build2": m2["absolute_difference"],
                "relative_difference_build1": m1["relative_difference"],
                "relative_difference_build2": m2["relative_difference"],
                "g_r1_vs_accepted_absolute_difference": g_r1_vs_accepted,
                "direct_et_model": m1["direct_et_model"],
                "selected_candidate_is_et": m1["selected_candidate_is_et"],
                "soft_ensemble_contains_et": m1["soft_ensemble_contains_et"],
                "et_derived_row": m1["et_derived_row"],
                "rank_sensitive_metric": m1["rank_sensitive_metric"],
                "threshold_sensitive_metric": m1["threshold_sensitive_metric"],
                "calibration_metric": m1["calibration_metric"],
                "within_1e_7": m1["within_1e_7"],
                "currently_approved_exception": approved,
                "currently_unapproved_mismatch": not approved,
            }
        )
    return pd.DataFrame(rows)[MATRIX_COLUMNS]


def row_meets_proposed_policy(
    matrix_row: Dict[str, Any],
    score_evidence: Dict[str, Any],
    validation_exact: bool,
) -> bool:
    et_scores = score_evidence["candidate_score_evidence"]["ET_leaf5"]
    max_et_score_diff = max(
        et_scores["maximum_validation_absolute_score_difference"],
        et_scores["maximum_test_absolute_score_difference"],
    )
    return bool(
        matrix_row["build1_build2_value_equal"]
        and matrix_row["et_derived_row"]
        and max_et_score_diff <= ET_SCORE_ATOL
        and score_evidence["non_et_scores_byte_identical"]
        and matrix_row["rank_sensitive_metric"]
        and not matrix_row["threshold_sensitive_metric"]
        and not matrix_row["calibration_metric"]
        and matrix_row["absolute_difference_build1"] <= ET_RANK_METRIC_ATOL
        and validation_exact
    )


def write_text_atomic(path: Path, data: str) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=str(path.parent),
        delete=False,
    ) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def write_csv_atomic(df: pd.DataFrame, path: Path) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=str(path.parent),
        delete=False,
    ) as tmp:
        df.to_csv(tmp, index=False, encoding="utf-8", lineterminator="\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2, cls=NumpyEncoder) + "\n")


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Part 3B ExtraTrees Canonical Reconciliation Audit",
        "",
        f"**Stage:** Part 3B.2R.1-G.D4",
        f"**Starting commit:** `{report['starting_commit']}`",
        "",
        "## Summary",
        "",
        f"- **Strict mismatch count Build 1:** {report['strict_mismatch_count_build1']}",
        f"- **Strict mismatch count Build 2:** {report['strict_mismatch_count_build2']}",
        f"- **Approved existing exception count:** {report['approved_existing_exception_count']}",
        f"- **Unapproved systematic difference count:** {report['unapproved_systematic_difference_count']}",
        f"- **Build mismatch identity sets equal:** {report['build_mismatch_identity_sets_equal']}",
        f"- **Build mismatch values equal:** {report['build_mismatch_values_equal']}",
        f"- **Categorical mismatches:** {report['categorical_mismatch_count']}",
        f"- **Validation numeric mismatches:** {report['validation_numeric_mismatch_count']}",
        f"- **Maximum metric absolute difference:** {report['maximum_metric_absolute_difference']}",
        f"- **Maximum metric relative difference:** {report['maximum_metric_relative_difference']}",
        f"- **Maximum ET score absolute difference:** {report['maximum_et_score_absolute_difference']}",
        f"- **Non-ET scores byte-identical:** {report['non_et_scores_byte_identical']}",
        f"- **All unapproved rows ET-derived:** {report['all_unapproved_rows_et_derived']}",
        f"- **All unapproved rows rank-sensitive:** {report['all_unapproved_rows_rank_sensitive']}",
        f"- **All unapproved rows within 1e-7:** {report['all_unapproved_rows_within_1e_7']}",
        f"- **Policy enforced:** {report['policy_enforced']}",
        f"- **Production validator changed:** {report['production_validator_changed']}",
        f"- **Canonical file changed:** {report['canonical_file_changed']}",
        f"- **All validation checks passed:** {report['all_validation_checks_passed']}",
        "",
        "## Affected Scope",
        "",
        f"- **Affected events:** {', '.join(report['affected_events'])}",
        f"- **Affected models:** {', '.join(report['affected_models'])}",
        f"- **Affected columns:** {', '.join(report['affected_columns'])}",
        "",
        "## Validation Reconstruction",
        "",
        f"- **Build 1 and Build 2 validation reconstructions equal:** {report['build1_build2_validation_reconstructions_equal']}",
        f"- **Validation categorical mismatches:** {report['validation_categorical_mismatch_count_build1']}",
        f"- **Validation numeric mismatches:** {report['validation_numeric_mismatch_count']}",
        "",
        "## Score-Level Mechanism",
        "",
    ]
    for event in report["score_level_evidence"]:
        lines.append(f"### {event['event_id']}")
        lines.append("")
        lines.append(
            f"- Maximum ET score absolute difference: {event['maximum_et_score_absolute_difference']}"
        )
        lines.append(f"- Non-ET scores byte-identical: {event['non_et_scores_byte_identical']}")
        lines.append("")
        lines.append("| Candidate | Validation byte equal | Test byte equal | Max val diff | Max test diff |")
        lines.append("| --- | --- | --- | --- | --- |")
        for cand, evidence in event["candidate_score_evidence"].items():
            lines.append(
                "| {cand} | {vb} | {tb} | {vd} | {td} |".format(
                    cand=cand,
                    vb=evidence["validation_score_byte_equal"],
                    tb=evidence["test_score_byte_equal"],
                    vd=evidence["maximum_validation_absolute_score_difference"],
                    td=evidence["maximum_test_absolute_score_difference"],
                )
            )
        lines.append("")

    policy = report["proposed_et_rank_metric_reconciliation_policy"]
    lines.extend(
        [
            "## Proposed ET Rank Metric Reconciliation Policy",
            "",
            f"- **policy_enforced:** {policy['policy_enforced']}",
            f"- **production_validator_changed:** {policy['production_validator_changed']}",
            f"- **canonical_file_changed:** {policy['canonical_file_changed']}",
            "",
            "### Classification",
            "",
            f"- **Mechanistically explainable:** {len(policy['mechanistically_explainable'])} row(s)",
            f"- **Currently approved:** {len(policy['currently_approved'])} row(s)",
            f"- **Currently unapproved:** {len(policy['currently_unapproved'])} row(s)",
            "",
            "## Production Activity",
            "",
            f"- **Model fits executed:** {report['model_fits_executed']}",
            f"- **Prediction calls executed:** {report['prediction_calls_executed']}",
            f"- **Build core bundle calls:** {report['build_core_bundle_calls']}",
            f"- **Repository production artifacts published:** {report['repository_production_artifacts_published']}",
            f"- **Part 3B complete:** {report['part3b_complete']}",
            f"- **Part 3C authorized:** {report['part3c_authorized']}",
            "",
        ]
    )
    return "\n".join(lines)


def validate_results(
    matrix_df: pd.DataFrame,
    b1_mismatches: List[Dict[str, Any]],
    b2_mismatches: List[Dict[str, Any]],
    categorical_mismatch_count: int,
    validation_numeric_mismatch_count: int,
    score_evidence: List[Dict[str, Any]],
    report: Dict[str, Any],
) -> None:
    errors: List[str] = []

    if len(b1_mismatches) != 9:
        errors.append(f"Build 1 strict mismatch count {len(b1_mismatches)} != 9")
    if len(b2_mismatches) != 9:
        errors.append(f"Build 2 strict mismatch count {len(b2_mismatches)} != 9")

    approved_count = int(matrix_df["currently_approved_exception"].sum())
    unapproved_count = int(matrix_df["currently_unapproved_mismatch"].sum())
    if approved_count != 1:
        errors.append(f"Approved count {approved_count} != 1")
    if unapproved_count != 8:
        errors.append(f"Unapproved count {unapproved_count} != 8")
    if len(matrix_df) != 9:
        errors.append(f"Matrix row count {len(matrix_df)} != 9")

    b1_identities = {mismatch_identity(m) for m in b1_mismatches}
    b2_identities = {mismatch_identity(m) for m in b2_mismatches}
    if b1_identities != b2_identities:
        errors.append("Build 1 and Build 2 mismatch identity sets differ")

    for m1, m2 in zip(
        sorted(b1_mismatches, key=lambda m: mismatch_identity(m)),
        sorted(b2_mismatches, key=lambda m: mismatch_identity(m)),
    ):
        if not np.isclose(
            m1["build1_value"],
            m2["build2_value"],
            rtol=RECON_RTOL,
            atol=RECON_ATOL,
            equal_nan=True,
        ):
            errors.append(f"Build values differ for {mismatch_identity(m1)}")

    if categorical_mismatch_count != 0:
        errors.append(f"Categorical mismatches {categorical_mismatch_count} != 0")
    if validation_numeric_mismatch_count != 0:
        errors.append(f"Validation numeric mismatches {validation_numeric_mismatch_count} != 0")

    for _, row in matrix_df.iterrows():
        if not row["et_derived_row"]:
            errors.append(f"Non-ET-derived mismatch: {row['model']} seed {row['seed']}")
        if not row["within_1e_7"]:
            errors.append(f"Mismatch exceeds 1e-7: {row['model']} {row['column']}")
        if row["currently_unapproved_mismatch"]:
            if not (
                row["experiment"] == "cross_project"
                and row["target_project"] == "JM1"
                and int(row["seed"]) == 13
            ):
                errors.append(f"Unapproved mismatch outside seed 13 JM1 cross-project: {dict(row)}")

    approved_rows = matrix_df[matrix_df["currently_approved_exception"]]
    if len(approved_rows) != 1:
        errors.append("Expected exactly one approved row")
    else:
        approved = approved_rows.iloc[0]
        if not (
            approved["experiment"] == "cross_project"
            and approved["target_project"] == "JM1"
            and int(approved["seed"]) == 42
            and approved["model"] == "AQRPE_v2_rank"
            and approved["column"] == "roc_auc"
        ):
            errors.append("Approved mismatch identity does not match required exception")

    max_et = max(ev["maximum_et_score_absolute_difference"] for ev in score_evidence)
    if max_et > ET_SCORE_ATOL:
        errors.append(f"Maximum ET score difference {max_et} > {ET_SCORE_ATOL}")
    if not all(ev["non_et_scores_byte_identical"] for ev in score_evidence):
        errors.append("Non-ET scores are not byte-identical for all affected events")

    if report["strict_mismatch_count"] != 9:
        errors.append("Report strict_mismatch_count != 9")
    if report["approved_existing_exception_count"] != approved_count:
        errors.append("JSON approved count disagrees with matrix")
    if report["unapproved_systematic_difference_count"] != unapproved_count:
        errors.append("JSON unapproved count disagrees with matrix")

    if errors:
        raise RuntimeError("Audit validation failed:\n- " + "\n- ".join(errors))


def verify_starting_commit() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if head != STARTING_COMMIT:
        raise RuntimeError(f"HEAD {head} != required starting commit {STARTING_COMMIT}")


def run_audit(build1_root: Path, build2_root: Path) -> Dict[str, Any]:
    verify_starting_commit()
    root = repo_root()

    canonical_results_path = root / "results/part1_full_reproduction/repeated_all_results.csv"
    canonical_validation_path = root / "results/part1_full_reproduction/validation_log.csv"
    accepted_recon_path = root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv"
    accepted_pred_within_path = root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz"
    accepted_pred_cross_path = root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz"

    source_specs = [
        ("g_r1_build1_result_reconstruction", build1_root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv"),
        ("g_r1_build2_result_reconstruction", build2_root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv"),
        ("g_r1_build1_validation_reconstruction", build1_root / "results/part3b_prediction_ledger/validation_reconstruction.csv"),
        ("g_r1_build2_validation_reconstruction", build2_root / "results/part3b_prediction_ledger/validation_reconstruction.csv"),
        ("g_r1_build1_prediction_within", build1_root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz"),
        ("g_r1_build1_prediction_cross", build1_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz"),
        ("g_r1_build2_prediction_within", build2_root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz"),
        ("g_r1_build2_prediction_cross", build2_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz"),
        ("accepted_tracked_result_reconstruction", accepted_recon_path),
        ("accepted_tracked_prediction_within", accepted_pred_within_path),
        ("accepted_tracked_prediction_cross", accepted_pred_cross_path),
        ("canonical_repeated_all_results", canonical_results_path),
        ("canonical_validation_log", canonical_validation_path),
    ]
    source_provenance = [source_record(role, path) for role, path in source_specs]
    source_hashes = {item["source_role"]: item["sha256"] for item in source_provenance}

    canonical_results = read_csv_round_trip(canonical_results_path)
    canonical_validation = read_csv_round_trip(canonical_validation_path)
    build1_recon = read_csv_round_trip(build1_root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv")
    build2_recon = read_csv_round_trip(build2_root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv")
    build1_val = read_csv_round_trip(build1_root / "results/part3b_prediction_ledger/validation_reconstruction.csv")
    build2_val = read_csv_round_trip(build2_root / "results/part3b_prediction_ledger/validation_reconstruction.csv")
    accepted_recon = read_csv_round_trip(accepted_recon_path)
    g_r1_pred_cross = read_gz_round_trip(build1_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz")
    accepted_pred_cross = read_gz_round_trip(accepted_pred_cross_path)

    b1_mismatches = find_strict_mismatches(build1_recon, canonical_results, "build1")
    b2_mismatches = find_strict_mismatches(build2_recon, canonical_results, "build2")
    matrix_df = build_mismatch_matrix(b1_mismatches, b2_mismatches, accepted_recon)

    cat_cols = RESULT_IDENTITY
    cat_merged = align_rows(build1_recon[cat_cols], cat_cols).merge(
        align_rows(canonical_results[cat_cols], cat_cols),
        on=cat_cols,
        how="outer",
        indicator=True,
    )
    categorical_mismatch_count = int((cat_merged["_merge"] != "both").sum())

    val1 = compare_validation(build1_val, canonical_validation)
    val2 = compare_validation(build2_val, canonical_validation)
    validation_numeric_mismatch_count = max(
        val1["validation_numeric_mismatch_count"],
        val2["validation_numeric_mismatch_count"],
    )
    validation_categorical_mismatch_count = max(
        val1["validation_categorical_mismatch_count"],
        val2["validation_categorical_mismatch_count"],
    )
    build1_build2_validation_equal = bool(
        build1_val[VALIDATION_RECONSTRUCTION_COLUMNS].equals(
            build2_val[VALIDATION_RECONSTRUCTION_COLUMNS]
        )
    )

    affected_events = sorted(
        {
            event_id_for(row["experiment"], row["target_project"], int(row["seed"]))
            for row in matrix_df.to_dict(orient="records")
        }
    )
    score_level_evidence = [
        compare_prediction_scores(g_r1_pred_cross, accepted_pred_cross, event_id)
        for event_id in affected_events
    ]

    validation_exact = (
        validation_categorical_mismatch_count == 0
        and validation_numeric_mismatch_count == 0
        and build1_build2_validation_equal
    )

    mechanistically_explainable: List[Dict[str, Any]] = []
    currently_approved: List[Dict[str, Any]] = []
    currently_unapproved: List[Dict[str, Any]] = []
    score_by_event = {item["event_id"]: item for item in score_level_evidence}

    for row in matrix_df.to_dict(orient="records"):
        event_id = event_id_for(row["experiment"], row["target_project"], int(row["seed"]))
        row_summary = {
            "experiment": row["experiment"],
            "target_project": row["target_project"],
            "seed": int(row["seed"]),
            "model": row["model"],
            "column": row["column"],
        }
        if row["currently_approved_exception"]:
            currently_approved.append(row_summary)
        if row["currently_unapproved_mismatch"]:
            currently_unapproved.append(row_summary)
        if row_meets_proposed_policy(row, score_by_event[event_id], validation_exact):
            mechanistically_explainable.append(row_summary)

    b1_identities = {mismatch_identity(m) for m in b1_mismatches}
    b2_identities = {mismatch_identity(m) for m in b2_mismatches}
    build_values_equal = bool(matrix_df["build1_build2_value_equal"].all())

    unapproved_rows = matrix_df[matrix_df["currently_unapproved_mismatch"]]
    report: Dict[str, Any] = {
        "stage": "Part 3B.2R.1-G.D4",
        "starting_commit": STARTING_COMMIT,
        "source_provenance": source_provenance,
        "source_hashes": source_hashes,
        "strict_mismatch_count": len(b1_mismatches),
        "strict_mismatch_count_build1": len(b1_mismatches),
        "strict_mismatch_count_build2": len(b2_mismatches),
        "approved_existing_exception_count": int(matrix_df["currently_approved_exception"].sum()),
        "unapproved_systematic_difference_count": int(matrix_df["currently_unapproved_mismatch"].sum()),
        "build_mismatch_identity_sets_equal": b1_identities == b2_identities,
        "build_mismatch_values_equal": build_values_equal,
        "categorical_mismatch_count": categorical_mismatch_count,
        "validation_numeric_mismatch_count": validation_numeric_mismatch_count,
        "validation_categorical_mismatch_count_build1": val1["validation_categorical_mismatch_count"],
        "validation_categorical_mismatch_count_build2": val2["validation_categorical_mismatch_count"],
        "build1_build2_validation_reconstructions_equal": build1_build2_validation_equal,
        "maximum_metric_absolute_difference": float(matrix_df["absolute_difference_build1"].max()),
        "maximum_metric_relative_difference": float(matrix_df["relative_difference_build1"].max()),
        "maximum_et_score_absolute_difference": float(
            max(item["maximum_et_score_absolute_difference"] for item in score_level_evidence)
        ),
        "non_et_scores_byte_identical": bool(
            all(item["non_et_scores_byte_identical"] for item in score_level_evidence)
        ),
        "affected_events": affected_events,
        "affected_models": sorted(matrix_df["model"].unique().tolist()),
        "affected_columns": sorted(matrix_df["column"].unique().tolist()),
        "all_unapproved_rows_et_derived": bool(unapproved_rows["et_derived_row"].all()),
        "all_unapproved_rows_rank_sensitive": bool(unapproved_rows["rank_sensitive_metric"].all()),
        "all_unapproved_rows_within_1e_7": bool(unapproved_rows["within_1e_7"].all()),
        "score_level_evidence": score_level_evidence,
        "proposed_et_rank_metric_reconciliation_policy": {
            "policy_enforced": False,
            "production_validator_changed": False,
            "canonical_file_changed": False,
            "criteria": [
                "categorical row identity is exact",
                "Build 1 and Build 2 deterministic values are identical",
                "row is ET-derived",
                "relevant deterministic versus accepted ET score difference is at most 1e-15",
                "all non-ET score vectors are byte-identical",
                "metric is explicitly rank-sensitive",
                "no threshold-sensitive metric is accepted",
                "no calibration metric such as Brier is accepted",
                "metric absolute difference is at most 1e-7",
                "validation reconstruction remains exact",
                "no categorical selection or selection-mode difference exists",
            ],
            "mechanistically_explainable": mechanistically_explainable,
            "currently_approved": currently_approved,
            "currently_unapproved": currently_unapproved,
        },
        "policy_enforced": False,
        "production_validator_changed": False,
        "canonical_file_changed": False,
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "build_core_bundle_calls": 0,
        "repository_production_artifacts_published": 0,
        "part3b_complete": False,
        "part3c_authorized": False,
        "all_validation_checks_passed": False,
        "g_r1_build1_root": str(build1_root.resolve()),
        "g_r1_build2_root": str(build2_root.resolve()),
    }

    validate_results(
        matrix_df,
        b1_mismatches,
        b2_mismatches,
        categorical_mismatch_count,
        validation_numeric_mismatch_count,
        score_level_evidence,
        report,
    )
    report["all_validation_checks_passed"] = True

    matrix_path = root / "results/part3b_prediction_ledger/et_canonical_mismatch_matrix.csv"
    json_path = root / "reports/part3b_et_canonical_reconciliation.json"
    md_path = root / "reports/part3b_et_canonical_reconciliation.md"

    write_csv_atomic(matrix_df, matrix_path)
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_markdown(report))

    loaded_matrix = read_csv_round_trip(matrix_path)
    if len(loaded_matrix) != len(matrix_df):
        raise RuntimeError("Persisted matrix row count disagrees with in-memory matrix")
    if int(loaded_matrix["currently_approved_exception"].sum()) != report["approved_existing_exception_count"]:
        raise RuntimeError("Persisted matrix approved count disagrees with JSON report")

    return report


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Persist and audit ExtraTrees canonical-reconciliation evidence."
    )
    parser.add_argument(
        "--build1-root",
        type=Path,
        required=True,
        help="Absolute path to preserved G.R1 Build 1 root directory.",
    )
    parser.add_argument(
        "--build2-root",
        type=Path,
        required=True,
        help="Absolute path to preserved G.R1 Build 2 root directory.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    build1_root = args.build1_root.resolve()
    build2_root = args.build2_root.resolve()
    if not build1_root.is_dir():
        raise FileNotFoundError(f"Build 1 root not found: {build1_root}")
    if not build2_root.is_dir():
        raise FileNotFoundError(f"Build 2 root not found: {build2_root}")

    report = run_audit(build1_root, build2_root)
    print(
        json.dumps(
            {
                "audit_checks_passed": report["all_validation_checks_passed"],
                "strict_mismatch_count_build1": report["strict_mismatch_count_build1"],
                "strict_mismatch_count_build2": report["strict_mismatch_count_build2"],
                "approved_existing_exception_count": report["approved_existing_exception_count"],
                "unapproved_systematic_difference_count": report["unapproved_systematic_difference_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
