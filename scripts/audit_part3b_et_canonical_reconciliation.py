#!/usr/bin/env python3
"""Part 3B.2R.1-G.D4.1: Exact fail-closed ExtraTrees canonical-reconciliation audit."""
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

STARTING_COMMIT = "b62af5623b571cd3e683c767e55ede1691d65fca"
STAGE = "Part 3B.2R.1-G.D4.1"
MATRIX_SHA256 = (
    "25cc88a8785f18668be2e03328a71b80b6e2c66f679a572e1e53656cde4ef908"
)

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

EXPECTED_SOURCE_ROLES = [
    "g_r1_build1_result_reconstruction",
    "g_r1_build2_result_reconstruction",
    "g_r1_build1_validation_reconstruction",
    "g_r1_build2_validation_reconstruction",
    "g_r1_build1_prediction_within",
    "g_r1_build1_prediction_cross",
    "g_r1_build2_prediction_within",
    "g_r1_build2_prediction_cross",
    "accepted_tracked_result_reconstruction",
    "accepted_tracked_prediction_within",
    "accepted_tracked_prediction_cross",
    "canonical_repeated_all_results",
    "canonical_validation_log",
]

EXPECTED_SOURCE_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "g_r1_build1_result_reconstruction": {
        "sha256": "35e295d1b7b6b830c032a0924878cfd86e95926768c49b06b9f1e5b8ff59bd1e",
        "row_count": 400,
        "column_count": 22,
        "size_bytes": 153640,
    },
    "g_r1_build2_result_reconstruction": {
        "sha256": "35e295d1b7b6b830c032a0924878cfd86e95926768c49b06b9f1e5b8ff59bd1e",
        "row_count": 400,
        "column_count": 22,
        "size_bytes": 153640,
    },
    "g_r1_build1_validation_reconstruction": {
        "sha256": "c619c2650d8aace5311da2ca7d009ef68da9fc3e4330707fb37f2675e5071c44",
        "row_count": 600,
        "column_count": 21,
        "size_bytes": 202733,
    },
    "g_r1_build2_validation_reconstruction": {
        "sha256": "c619c2650d8aace5311da2ca7d009ef68da9fc3e4330707fb37f2675e5071c44",
        "row_count": 600,
        "column_count": 21,
        "size_bytes": 202733,
    },
    "g_r1_build1_prediction_within": {
        "sha256": "52724f5194969ee5a44b9761f80508c5ef095f6f5df05eeaf1c0745f6ed8a071",
        "row_count": 34900,
        "column_count": 14,
        "size_bytes": 1356761,
    },
    "g_r1_build1_prediction_cross": {
        "sha256": "1726f756c014ea2c75c023070679dd4d0b3b9ec50e7403879f29224ccbf780b5",
        "row_count": 174430,
        "column_count": 14,
        "size_bytes": 6587556,
    },
    "g_r1_build2_prediction_within": {
        "sha256": "52724f5194969ee5a44b9761f80508c5ef095f6f5df05eeaf1c0745f6ed8a071",
        "row_count": 34900,
        "column_count": 14,
        "size_bytes": 1356761,
    },
    "g_r1_build2_prediction_cross": {
        "sha256": "1726f756c014ea2c75c023070679dd4d0b3b9ec50e7403879f29224ccbf780b5",
        "row_count": 174430,
        "column_count": 14,
        "size_bytes": 6587556,
    },
    "accepted_tracked_result_reconstruction": {
        "sha256": "bcd1ec1e1ff3ec1e80775201d26633ff84b15a1025837d1658f1fb9d120fb045",
        "row_count": 400,
        "column_count": 22,
        "size_bytes": 153648,
    },
    "accepted_tracked_prediction_within": {
        "sha256": "03079b85039a934b2783b4473045fcdd273abdb326f163193370f2bdef6ce5f1",
        "row_count": 34900,
        "column_count": 14,
        "size_bytes": 1356915,
    },
    "accepted_tracked_prediction_cross": {
        "sha256": "d17de9576bdc9ce7d9e4332631e87496af5856796b36c16d3b60ae472fd0618e",
        "row_count": 174430,
        "column_count": 14,
        "size_bytes": 6587717,
    },
    "canonical_repeated_all_results": {
        "sha256": "76b430031a944708af661bee1a1355619d1e0e6f49b932d462cea421aeb01160",
        "row_count": 400,
        "column_count": 22,
        "size_bytes": 141632,
    },
    "canonical_validation_log": {
        "sha256": "d18dbb6b7a71f356203aa34fe41ab7d531daa1f8499fc06d06ab643b088f0272",
        "row_count": 600,
        "column_count": 21,
        "size_bytes": 187902,
    },
}

BUILD_SOURCE_HASH_PAIRS = [
    ("g_r1_build1_result_reconstruction", "g_r1_build2_result_reconstruction"),
    ("g_r1_build1_validation_reconstruction", "g_r1_build2_validation_reconstruction"),
    ("g_r1_build1_prediction_within", "g_r1_build2_prediction_within"),
    ("g_r1_build1_prediction_cross", "g_r1_build2_prediction_cross"),
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


def float64_bit_equal(a: Any, b: Any) -> bool:
    return np.float64(a).tobytes() == np.float64(b).tobytes()


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


def sha256_text(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def is_valid_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


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


def compare_prediction_scores_dual(
    build1_pred: pd.DataFrame,
    build2_pred: pd.DataFrame,
    accepted_pred: pd.DataFrame,
    event_id: str,
) -> Dict[str, Any]:
    sort_cols = ["split_role", "split_position", "sample_uid"]
    b1_event = build1_pred[build1_pred["event_id"] == event_id].sort_values(sort_cols).reset_index(drop=True)
    b2_event = build2_pred[build2_pred["event_id"] == event_id].sort_values(sort_cols).reset_index(drop=True)
    a_event = accepted_pred[accepted_pred["event_id"] == event_id].sort_values(sort_cols).reset_index(drop=True)
    if not (len(b1_event) == len(b2_event) == len(a_event)):
        raise RuntimeError(f"Prediction ledger row count mismatch for {event_id}")

    candidate_evidence: Dict[str, Any] = {}
    max_b1_val_diff = 0.0
    max_b1_test_diff = 0.0
    max_b2_val_diff = 0.0
    max_b2_test_diff = 0.0
    max_b1_b2_diff = 0.0
    non_et_byte_identical_b1 = True
    non_et_byte_identical_b2 = True
    max_et_diff = 0.0
    build_score_arrays_byte_exact = True

    for cand in CANDIDATES:
        col = f"score__{cand}"
        b1_val = b1_event.loc[b1_event["split_role"] == "validation", col].to_numpy(dtype=np.float64)
        b1_test = b1_event.loc[b1_event["split_role"] == "test", col].to_numpy(dtype=np.float64)
        b2_val = b2_event.loc[b2_event["split_role"] == "validation", col].to_numpy(dtype=np.float64)
        b2_test = b2_event.loc[b2_event["split_role"] == "test", col].to_numpy(dtype=np.float64)
        a_val = a_event.loc[a_event["split_role"] == "validation", col].to_numpy(dtype=np.float64)
        a_test = a_event.loc[a_event["split_role"] == "test", col].to_numpy(dtype=np.float64)

        b1_val_byte = bool(b1_val.tobytes() == a_val.tobytes())
        b1_test_byte = bool(b1_test.tobytes() == a_test.tobytes())
        b2_val_byte = bool(b2_val.tobytes() == a_val.tobytes())
        b2_test_byte = bool(b2_test.tobytes() == a_test.tobytes())
        b1_b2_val_byte = bool(b1_val.tobytes() == b2_val.tobytes())
        b1_b2_test_byte = bool(b1_test.tobytes() == b2_test.tobytes())

        b1_val_diff = float(np.max(np.abs(b1_val - a_val))) if len(b1_val) else 0.0
        b1_test_diff = float(np.max(np.abs(b1_test - a_test))) if len(b1_test) else 0.0
        b2_val_diff = float(np.max(np.abs(b2_val - a_val))) if len(b2_val) else 0.0
        b2_test_diff = float(np.max(np.abs(b2_test - a_test))) if len(b2_test) else 0.0
        b1_b2_diff = float(
            max(
                np.max(np.abs(b1_val - b2_val)) if len(b1_val) else 0.0,
                np.max(np.abs(b1_test - b2_test)) if len(b1_test) else 0.0,
            )
        )

        candidate_evidence[cand] = {
            "build1_validation_score_byte_equal": b1_val_byte,
            "build1_test_score_byte_equal": b1_test_byte,
            "build2_validation_score_byte_equal": b2_val_byte,
            "build2_test_score_byte_equal": b2_test_byte,
            "build1_build2_validation_score_byte_equal": b1_b2_val_byte,
            "build1_build2_test_score_byte_equal": b1_b2_test_byte,
            "validation_score_byte_equal": b1_val_byte,
            "test_score_byte_equal": b1_test_byte,
            "maximum_build1_validation_absolute_score_difference": b1_val_diff,
            "maximum_build1_test_absolute_score_difference": b1_test_diff,
            "maximum_build2_validation_absolute_score_difference": b2_val_diff,
            "maximum_build2_test_absolute_score_difference": b2_test_diff,
            "maximum_build1_build2_absolute_score_difference": b1_b2_diff,
            "maximum_validation_absolute_score_difference": b1_val_diff,
            "maximum_test_absolute_score_difference": b1_test_diff,
        }

        max_b1_val_diff = max(max_b1_val_diff, b1_val_diff)
        max_b1_test_diff = max(max_b1_test_diff, b1_test_diff)
        max_b2_val_diff = max(max_b2_val_diff, b2_val_diff)
        max_b2_test_diff = max(max_b2_test_diff, b2_test_diff)
        max_b1_b2_diff = max(max_b1_b2_diff, b1_b2_diff)

        if cand == "ET_leaf5":
            max_et_diff = max(max_et_diff, b1_val_diff, b1_test_diff, b2_val_diff, b2_test_diff)
        else:
            if not (b1_val_byte and b1_test_byte):
                non_et_byte_identical_b1 = False
            if not (b2_val_byte and b2_test_byte):
                non_et_byte_identical_b2 = False
        if not (b1_b2_val_byte and b1_b2_test_byte):
            build_score_arrays_byte_exact = False

    return {
        "event_id": event_id,
        "candidate_score_evidence": candidate_evidence,
        "maximum_build1_validation_absolute_score_difference": max_b1_val_diff,
        "maximum_build1_test_absolute_score_difference": max_b1_test_diff,
        "maximum_build2_validation_absolute_score_difference": max_b2_val_diff,
        "maximum_build2_test_absolute_score_difference": max_b2_test_diff,
        "maximum_build1_build2_absolute_score_difference": max_b1_b2_diff,
        "maximum_validation_absolute_score_difference": max_b1_val_diff,
        "maximum_test_absolute_score_difference": max_b1_test_diff,
        "maximum_et_score_absolute_difference": max_et_diff,
        "non_et_scores_byte_identical": non_et_byte_identical_b1 and non_et_byte_identical_b2,
        "build1_non_et_scores_byte_identical": non_et_byte_identical_b1,
        "build2_non_et_scores_byte_identical": non_et_byte_identical_b2,
        "build_score_arrays_byte_exact": build_score_arrays_byte_exact,
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
        build_equal = float64_bit_equal(m1["build1_value"], m2["build2_value"])
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
        et_scores["maximum_build1_validation_absolute_score_difference"],
        et_scores["maximum_build1_test_absolute_score_difference"],
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


def matrix_to_csv_text(matrix_df: pd.DataFrame) -> str:
    from io import StringIO

    buf = StringIO()
    matrix_df.to_csv(buf, index=False, encoding="utf-8", lineterminator="\n")
    return buf.getvalue()


def recompute_matrix_summaries(matrix_df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "strict_mismatch_count": int(len(matrix_df)),
        "strict_mismatch_count_build1": int(len(matrix_df)),
        "strict_mismatch_count_build2": int(len(matrix_df)),
        "approved_existing_exception_count": int(matrix_df["currently_approved_exception"].sum()),
        "unapproved_systematic_difference_count": int(matrix_df["currently_unapproved_mismatch"].sum()),
        "build_mismatch_values_equal": bool(matrix_df["build1_build2_value_equal"].all()),
        "maximum_metric_absolute_difference": float(matrix_df["absolute_difference_build1"].max()),
        "maximum_metric_relative_difference": float(matrix_df["relative_difference_build1"].max()),
    }


def validate_source_role_contract(source_provenance: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[str] = []
    roles = [item["source_role"] for item in source_provenance]
    if roles != EXPECTED_SOURCE_ROLES:
        if set(roles) != set(EXPECTED_SOURCE_ROLES):
            errors.append("source role set mismatch")
        if len(roles) != len(set(roles)):
            errors.append("duplicate source roles detected")
        if len(roles) != len(EXPECTED_SOURCE_ROLES):
            errors.append("unexpected source role count")

    for item in source_provenance:
        role = item["source_role"]
        expected = EXPECTED_SOURCE_PROVENANCE.get(role)
        if expected is None:
            errors.append(f"unknown source role {role}")
            continue
        if not is_valid_sha256(item["sha256"]):
            errors.append(f"invalid sha256 for role {role}")
        for field in ("sha256", "row_count", "column_count", "size_bytes"):
            if item[field] != expected[field]:
                errors.append(
                    f"{role} {field} {item[field]!r} != expected {expected[field]!r}"
                )

    pair_equal = True
    source_hashes = {item["source_role"]: item["sha256"] for item in source_provenance}
    for left, right in BUILD_SOURCE_HASH_PAIRS:
        if source_hashes.get(left) != source_hashes.get(right):
            pair_equal = False
            errors.append(f"build hash pair mismatch for {left} vs {right}")

    return {
        "exact_source_role_set_passed": roles == EXPECTED_SOURCE_ROLES and not errors,
        "build_source_hash_pairs_equal": pair_equal,
        "errors": errors,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    integrity = report["audit_integrity_checks"]
    lines = [
        "# Part 3B ExtraTrees Canonical Reconciliation Audit",
        "",
        f"**Stage:** {report['stage']}",
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
        f"- **Build mismatch values bit-exact:** {integrity['build_mismatch_values_bit_exact']}",
        f"- **Categorical mismatches:** {report['categorical_mismatch_count']}",
        f"- **Validation numeric mismatches:** {report['validation_numeric_mismatch_count']}",
        f"- **Maximum metric absolute difference:** {report['maximum_metric_absolute_difference']}",
        f"- **Maximum metric relative difference:** {report['maximum_metric_relative_difference']}",
        f"- **Maximum ET score absolute difference:** {report['maximum_et_score_absolute_difference']}",
        f"- **Non-ET scores byte-identical:** {report['non_et_scores_byte_identical']}",
        f"- **Build score arrays byte-exact:** {integrity['build_score_arrays_byte_exact']}",
        f"- **All unapproved rows ET-derived:** {report['all_unapproved_rows_et_derived']}",
        f"- **All unapproved rows rank-sensitive:** {report['all_unapproved_rows_rank_sensitive']}",
        f"- **All unapproved rows within 1e-7:** {report['all_unapproved_rows_within_1e_7']}",
        f"- **Policy enforced:** {report['policy_enforced']}",
        f"- **Production validator changed:** {report['production_validator_changed']}",
        f"- **Canonical file changed:** {report['canonical_file_changed']}",
        f"- **All validation checks passed:** {report['all_validation_checks_passed']}",
        "",
        "## Build Source Equality",
        "",
        f"- **Build result reconstruction SHA equal:** {report['build_result_reconstruction_sha_equal']}",
        f"- **Build validation reconstruction SHA equal:** {report['build_validation_reconstruction_sha_equal']}",
        f"- **Build prediction-within SHA equal:** {report['build_prediction_within_sha_equal']}",
        f"- **Build prediction-cross SHA equal:** {report['build_prediction_cross_sha_equal']}",
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
        f"- **Build 1 validation categorical mismatches:** {report['validation_categorical_mismatch_count_build1']}",
        f"- **Build 2 validation categorical mismatches:** {report['validation_categorical_mismatch_count_build2']}",
        f"- **Build 1 validation numeric mismatches:** {report['validation_numeric_mismatch_count_build1']}",
        f"- **Build 2 validation numeric mismatches:** {report['validation_numeric_mismatch_count_build2']}",
        f"- **Validation builds exactly equal:** {integrity['validation_builds_exactly_equal']}",
        "",
        "## Audit Integrity",
        "",
        f"- **Source-role contract passed:** {integrity['exact_source_role_set_passed']}",
        f"- **Matrix/JSON consistency passed:** {integrity['json_matches_matrix']}",
        f"- **Markdown/JSON consistency passed:** {integrity['markdown_matches_json']}",
        f"- **Atomic publication validation passed:** {integrity['atomic_publication_ready']}",
        f"- **Audit-integrity checks passed:** {integrity['all_audit_integrity_checks_passed']}",
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
        lines.append(
            f"- Build score arrays byte-exact: {event['build_score_arrays_byte_exact']}"
        )
        lines.append("")
        lines.append(
            "| Candidate | B1 val byte | B1 test byte | B2 val byte | B2 test byte | "
            "B1/B2 val byte | B1/B2 test byte | Max B1 val diff | Max B1 test diff | "
            "Max B2 val diff | Max B2 test diff | Max B1/B2 diff |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for cand, evidence in event["candidate_score_evidence"].items():
            lines.append(
                "| {cand} | {b1v} | {b1t} | {b2v} | {b2t} | {b12v} | {b12t} | {d1v} | {d1t} | {d2v} | {d2t} | {d12} |".format(
                    cand=cand,
                    b1v=evidence["build1_validation_score_byte_equal"],
                    b1t=evidence["build1_test_score_byte_equal"],
                    b2v=evidence["build2_validation_score_byte_equal"],
                    b2t=evidence["build2_test_score_byte_equal"],
                    b12v=evidence["build1_build2_validation_score_byte_equal"],
                    b12t=evidence["build1_build2_test_score_byte_equal"],
                    d1v=evidence["maximum_build1_validation_absolute_score_difference"],
                    d1t=evidence["maximum_build1_test_absolute_score_difference"],
                    d2v=evidence["maximum_build2_validation_absolute_score_difference"],
                    d2t=evidence["maximum_build2_test_absolute_score_difference"],
                    d12=evidence["maximum_build1_build2_absolute_score_difference"],
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
    val1: Dict[str, Any],
    val2: Dict[str, Any],
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
        if not float64_bit_equal(m1["build1_value"], m2["build2_value"]):
            errors.append(f"Build values not bit-equal for {mismatch_identity(m1)}")

    if categorical_mismatch_count != 0:
        errors.append(f"Categorical mismatches {categorical_mismatch_count} != 0")
    if val1["validation_categorical_mismatch_count"] != 0:
        errors.append(
            f"Build 1 validation categorical mismatches "
            f"{val1['validation_categorical_mismatch_count']} != 0"
        )
    if val2["validation_categorical_mismatch_count"] != 0:
        errors.append(
            f"Build 2 validation categorical mismatches "
            f"{val2['validation_categorical_mismatch_count']} != 0"
        )
    if val1["validation_numeric_mismatch_count"] != 0:
        errors.append(
            f"Build 1 validation numeric mismatches "
            f"{val1['validation_numeric_mismatch_count']} != 0"
        )
    if val2["validation_numeric_mismatch_count"] != 0:
        errors.append(
            f"Build 2 validation numeric mismatches "
            f"{val2['validation_numeric_mismatch_count']} != 0"
        )

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
    if not all(ev["build_score_arrays_byte_exact"] for ev in score_evidence):
        errors.append("Build 1 and Build 2 score arrays are not byte-identical")

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


def publish_outputs_fail_closed(
    matrix_df: pd.DataFrame,
    report: Dict[str, Any],
    matrix_path: Path,
    json_path: Path,
    md_path: Path,
) -> Dict[str, bool]:
    existing_matrix_bytes = matrix_path.read_bytes()
    if sha256_file(matrix_path) != MATRIX_SHA256:
        raise RuntimeError("Existing mismatch matrix SHA-256 changed before publication")

    matrix_csv = matrix_to_csv_text(matrix_df)
    if existing_matrix_bytes != matrix_csv.encode("utf-8"):
        raise RuntimeError("In-memory mismatch matrix differs from persisted matrix bytes")

    json_text = json.dumps(report, indent=2, cls=NumpyEncoder) + "\n"
    md_text = render_markdown(report)

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=str(matrix_path.parent), delete=False
    ) as tmp_csv:
        tmp_csv.write(matrix_csv)
        tmp_csv_path = Path(tmp_csv.name)
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

    try:
        reread_csv_df = read_csv_round_trip(tmp_csv_path)
        if not matrix_df.equals(reread_csv_df):
            raise RuntimeError("Temporary CSV does not equal in-memory matrix")

        reread_json = json.loads(tmp_json_path.read_text(encoding="utf-8"))
        expected_md = render_markdown(reread_json)
        actual_md = tmp_md_path.read_text(encoding="utf-8")
        if actual_md != expected_md:
            raise RuntimeError("Temporary Markdown does not match Markdown regenerated from JSON")

        recomputed = recompute_matrix_summaries(reread_csv_df)
        summary_fields = [
            "strict_mismatch_count",
            "strict_mismatch_count_build1",
            "strict_mismatch_count_build2",
            "approved_existing_exception_count",
            "unapproved_systematic_difference_count",
            "build_mismatch_values_equal",
            "maximum_metric_absolute_difference",
            "maximum_metric_relative_difference",
        ]
        for field in summary_fields:
            if reread_json.get(field) != recomputed[field]:
                raise RuntimeError(
                    f"JSON field {field}={reread_json.get(field)!r} "
                    f"!= recomputed {recomputed[field]!r}"
                )

        md_checks = {
            "strict_mismatch_count_build1": str(reread_json["strict_mismatch_count_build1"]),
            "approved_existing_exception_count": str(
                reread_json["approved_existing_exception_count"]
            ),
            "all_validation_checks_passed": str(reread_json["all_validation_checks_passed"]),
        }
        for label, value in md_checks.items():
            if value not in actual_md:
                raise RuntimeError(f"Markdown missing JSON-backed value for {label}")

        checks = {
            "matrix_matches_in_memory": matrix_df.equals(reread_csv_df),
            "json_matches_matrix": all(
                reread_json.get(field) == recomputed[field] for field in summary_fields
            ),
            "markdown_matches_json": actual_md == expected_md,
            "atomic_publication_ready": True,
        }
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_json_path.replace(json_path)
        tmp_md_path.replace(md_path)
        tmp_csv_path.unlink()
        return checks
    except Exception:
        for path in (tmp_csv_path, tmp_json_path, tmp_md_path):
            if path.exists():
                path.unlink()
        raise


def run_audit(build1_root: Path, build2_root: Path, *, verify_commit: bool = True) -> Dict[str, Any]:
    if verify_commit:
        verify_starting_commit()
    root = repo_root()

    canonical_results_path = root / "results/part1_full_reproduction/repeated_all_results.csv"
    canonical_validation_path = root / "results/part1_full_reproduction/validation_log.csv"
    accepted_recon_path = root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv"
    accepted_pred_within_path = root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz"
    accepted_pred_cross_path = root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz"
    matrix_path = root / "results/part3b_prediction_ledger/et_canonical_mismatch_matrix.csv"

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
    source_contract = validate_source_role_contract(source_provenance)
    if source_contract["errors"]:
        raise RuntimeError(
            "Source-role contract failed:\n- " + "\n- ".join(source_contract["errors"])
        )

    canonical_results = read_csv_round_trip(canonical_results_path)
    canonical_validation = read_csv_round_trip(canonical_validation_path)
    build1_recon = read_csv_round_trip(build1_root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv")
    build2_recon = read_csv_round_trip(build2_root / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv")
    build1_val = read_csv_round_trip(build1_root / "results/part3b_prediction_ledger/validation_reconstruction.csv")
    build2_val = read_csv_round_trip(build2_root / "results/part3b_prediction_ledger/validation_reconstruction.csv")
    accepted_recon = read_csv_round_trip(accepted_recon_path)
    b1_pred_within = read_gz_round_trip(build1_root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz")
    b1_pred_cross = read_gz_round_trip(build1_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz")
    b2_pred_within = read_gz_round_trip(build2_root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz")
    b2_pred_cross = read_gz_round_trip(build2_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz")
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
    validation_build1_exact = (
        val1["validation_categorical_mismatch_count"] == 0
        and val1["validation_numeric_mismatch_count"] == 0
    )
    validation_build2_exact = (
        val2["validation_categorical_mismatch_count"] == 0
        and val2["validation_numeric_mismatch_count"] == 0
    )

    affected_events = sorted(
        {
            event_id_for(row["experiment"], row["target_project"], int(row["seed"]))
            for row in matrix_df.to_dict(orient="records")
        }
    )
    score_level_evidence = [
        compare_prediction_scores_dual(
            b1_pred_cross,
            b2_pred_cross,
            accepted_pred_cross,
            event_id,
        )
        for event_id in affected_events
    ]

    validation_exact = (
        validation_build1_exact
        and validation_build2_exact
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
    build_mismatch_values_bit_exact = bool(matrix_df["build1_build2_value_equal"].all())

    within_byte_exact = (
        sha256_file(build1_root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz")
        == sha256_file(build2_root / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz")
        and b1_pred_within.equals(b2_pred_within)
    )
    cross_byte_exact = (
        sha256_file(build1_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz")
        == sha256_file(build2_root / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz")
        and b1_pred_cross.equals(b2_pred_cross)
    )
    build_score_arrays_byte_exact = (
        within_byte_exact
        and cross_byte_exact
        and all(item["build_score_arrays_byte_exact"] for item in score_level_evidence)
    )

    unapproved_rows = matrix_df[matrix_df["currently_unapproved_mismatch"]]
    report: Dict[str, Any] = {
        "stage": STAGE,
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
        "build_result_reconstruction_sha_equal": (
            source_hashes["g_r1_build1_result_reconstruction"]
            == source_hashes["g_r1_build2_result_reconstruction"]
        ),
        "build_validation_reconstruction_sha_equal": (
            source_hashes["g_r1_build1_validation_reconstruction"]
            == source_hashes["g_r1_build2_validation_reconstruction"]
        ),
        "build_prediction_within_sha_equal": (
            source_hashes["g_r1_build1_prediction_within"]
            == source_hashes["g_r1_build2_prediction_within"]
        ),
        "build_prediction_cross_sha_equal": (
            source_hashes["g_r1_build1_prediction_cross"]
            == source_hashes["g_r1_build2_prediction_cross"]
        ),
        "categorical_mismatch_count": categorical_mismatch_count,
        "validation_numeric_mismatch_count": validation_numeric_mismatch_count,
        "validation_numeric_mismatch_count_build1": val1["validation_numeric_mismatch_count"],
        "validation_numeric_mismatch_count_build2": val2["validation_numeric_mismatch_count"],
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
        val1,
        val2,
        score_level_evidence,
        report,
    )

    audit_integrity_checks = {
        "exact_source_role_set_passed": source_contract["exact_source_role_set_passed"],
        "build_source_hash_pairs_equal": source_contract["build_source_hash_pairs_equal"],
        "build_mismatch_values_bit_exact": build_mismatch_values_bit_exact,
        "build_score_arrays_byte_exact": build_score_arrays_byte_exact,
        "validation_build1_exact": validation_build1_exact,
        "validation_build2_exact": validation_build2_exact,
        "validation_builds_exactly_equal": build1_build2_validation_equal,
        "matrix_matches_in_memory": False,
        "json_matches_matrix": False,
        "markdown_matches_json": False,
        "atomic_publication_ready": False,
        "all_audit_integrity_checks_passed": False,
    }
    report["audit_integrity_checks"] = audit_integrity_checks

    publication_checks = publish_outputs_fail_closed(
        matrix_df,
        report,
        matrix_path,
        root / "reports/part3b_et_canonical_reconciliation.json",
        root / "reports/part3b_et_canonical_reconciliation.md",
    )
    audit_integrity_checks.update(publication_checks)
    audit_integrity_checks["all_audit_integrity_checks_passed"] = all(
        audit_integrity_checks[key]
        for key in (
            "exact_source_role_set_passed",
            "build_source_hash_pairs_equal",
            "build_mismatch_values_bit_exact",
            "build_score_arrays_byte_exact",
            "validation_build1_exact",
            "validation_build2_exact",
            "validation_builds_exactly_equal",
            "matrix_matches_in_memory",
            "json_matches_matrix",
            "markdown_matches_json",
            "atomic_publication_ready",
        )
    )
    report["audit_integrity_checks"] = audit_integrity_checks
    report["all_validation_checks_passed"] = audit_integrity_checks["all_audit_integrity_checks_passed"]

    if not report["all_validation_checks_passed"]:
        raise RuntimeError("Audit integrity checks failed")

    final_publication = publish_outputs_fail_closed(
        matrix_df,
        report,
        matrix_path,
        root / "reports/part3b_et_canonical_reconciliation.json",
        root / "reports/part3b_et_canonical_reconciliation.md",
    )
    if not all(final_publication.values()):
        raise RuntimeError("Final publication consistency checks failed")

    return report


def _self_test_one_ulp_build_value_difference_rejected() -> bool:
    b1 = {"build1_value": 1.0}
    b2 = {"build2_value": np.nextafter(np.float64(1.0), np.float64(2.0))}
    return not float64_bit_equal(b1["build1_value"], b2["build2_value"])


def _self_test_build2_score_difference_rejected() -> bool:
    a = np.array([0.1, 0.2], dtype=np.float64)
    b = a.copy()
    b[0] = np.nextafter(b[0], np.float64(1.0))
    return a.tobytes() != b.tobytes()


def _self_test_validation_categorical_difference_rejected() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_synthetic_bundle(root)
        canon_val = root / "canonical/validation_log.csv"
        build_val = root / "build1/results/part3b_prediction_ledger/validation_reconstruction.csv"
        df = read_csv_round_trip(build_val)
        df.loc[0, "candidate"] = "MUTATED"
        df.to_csv(build_val, index=False, lineterminator="\n")
        val = compare_validation(read_csv_round_trip(build_val), read_csv_round_trip(canon_val))
        return val["validation_categorical_mismatch_count"] > 0


def _self_test_missing_source_role_rejected() -> bool:
    provenance = [
        {
            "source_role": role,
            "sha256": EXPECTED_SOURCE_PROVENANCE[role]["sha256"],
            "row_count": EXPECTED_SOURCE_PROVENANCE[role]["row_count"],
            "column_count": EXPECTED_SOURCE_PROVENANCE[role]["column_count"],
            "size_bytes": EXPECTED_SOURCE_PROVENANCE[role]["size_bytes"],
        }
        for role in EXPECTED_SOURCE_ROLES[:-1]
    ]
    contract = validate_source_role_contract(provenance)
    return not contract["exact_source_role_set_passed"]


def _self_test_markdown_json_disagreement_rejected() -> bool:
    report = {
        "stage": STAGE,
        "starting_commit": STARTING_COMMIT,
        "strict_mismatch_count_build1": 9,
        "strict_mismatch_count_build2": 9,
        "approved_existing_exception_count": 1,
        "unapproved_systematic_difference_count": 8,
        "build_mismatch_identity_sets_equal": True,
        "build_mismatch_values_equal": True,
        "categorical_mismatch_count": 0,
        "validation_numeric_mismatch_count": 0,
        "maximum_metric_absolute_difference": 0.0,
        "maximum_metric_relative_difference": 0.0,
        "maximum_et_score_absolute_difference": 0.0,
        "non_et_scores_byte_identical": True,
        "all_unapproved_rows_et_derived": True,
        "all_unapproved_rows_rank_sensitive": True,
        "all_unapproved_rows_within_1e_7": True,
        "policy_enforced": False,
        "production_validator_changed": False,
        "canonical_file_changed": False,
        "all_validation_checks_passed": True,
        "affected_events": [],
        "affected_models": [],
        "affected_columns": [],
        "build1_build2_validation_reconstructions_equal": True,
        "validation_categorical_mismatch_count_build1": 0,
        "validation_categorical_mismatch_count_build2": 0,
        "validation_numeric_mismatch_count_build1": 0,
        "validation_numeric_mismatch_count_build2": 0,
        "build_result_reconstruction_sha_equal": True,
        "build_validation_reconstruction_sha_equal": True,
        "build_prediction_within_sha_equal": True,
        "build_prediction_cross_sha_equal": True,
        "score_level_evidence": [],
        "proposed_et_rank_metric_reconciliation_policy": {
            "policy_enforced": False,
            "production_validator_changed": False,
            "canonical_file_changed": False,
            "mechanistically_explainable": [],
            "currently_approved": [],
            "currently_unapproved": [],
        },
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "build_core_bundle_calls": 0,
        "repository_production_artifacts_published": 0,
        "part3b_complete": False,
        "part3c_authorized": False,
        "audit_integrity_checks": {
            "exact_source_role_set_passed": True,
            "build_source_hash_pairs_equal": True,
            "build_mismatch_values_bit_exact": True,
            "build_score_arrays_byte_exact": True,
            "validation_build1_exact": True,
            "validation_build2_exact": True,
            "validation_builds_exactly_equal": True,
            "matrix_matches_in_memory": True,
            "json_matches_matrix": True,
            "markdown_matches_json": True,
            "atomic_publication_ready": True,
            "all_audit_integrity_checks_passed": True,
        },
    }
    md = render_markdown(report)
    report["strict_mismatch_count_build1"] = 8
    return md != render_markdown(report)


def _write_synthetic_bundle(root: Path) -> Tuple[Path, Path]:
    build1 = root / "build1"
    build2 = root / "build2"
    canon = root / "canonical"
    for path in (
        build1 / "results/part3b_prediction_ledger",
        build2 / "results/part3b_prediction_ledger",
        canon,
    ):
        path.mkdir(parents=True, exist_ok=True)

    canon_res = pd.DataFrame(
        [
            {
                "experiment": "cross_project",
                "target_project": "JM1",
                "seed": 13,
                "model": "ET_leaf5",
                "selected_candidate": "ET_leaf5",
                "selection_mode": "single_candidate_balanced_threshold",
                "threshold": 0.5,
                "selection_score": 0.1,
                "avg_precision": 0.30380013771863795,
                "roc_auc": 0.6693121125388155,
                "mcc": 0.0,
                "f1": 0.0,
                "balanced_accuracy": 0.5,
                "precision": 0.0,
                "recall": 0.0,
                "brier": 0.1,
                "precision_at_10pct": 0.0,
                "recall_at_10pct": 0.0,
                "lift_at_10pct": 0.0,
                "precision_at_20pct": 0.0,
                "recall_at_20pct": 0.0,
                "lift_at_20pct": 0.0,
            }
        ]
    )
    recon = canon_res.copy()
    recon.loc[0, "avg_precision"] = 0.30380010752693754
    recon.loc[0, "roc_auc"] = 0.66931206970383
    val = pd.DataFrame(
        [
            {
                "experiment": "cross_project",
                "target_project": "JM1",
                "seed": 13,
                "candidate": "ET_leaf5",
                "mode": "balanced",
                "val_threshold": 0.5,
                "val_selection_score": 0.1,
                "val_avg_precision": 0.1,
                "val_roc_auc": 0.2,
                "val_mcc": 0.0,
                "val_f1": 0.0,
                "val_balanced_accuracy": 0.5,
                "val_precision": 0.0,
                "val_recall": 0.0,
                "val_brier": 0.1,
                "val_precision_at_10pct": 0.0,
                "val_recall_at_10pct": 0.0,
                "val_lift_at_10pct": 0.0,
                "val_precision_at_20pct": 0.0,
                "val_recall_at_20pct": 0.0,
                "val_lift_at_20pct": 0.0,
            }
        ]
    )
    pred = pd.DataFrame(
        [
            {
                "event_id": "cross_project__JM1__seed_013",
                "experiment": "cross_project",
                "target_project": "JM1",
                "seed": 13,
                "split_role": "validation",
                "split_position": 0,
                "sample_uid": "s0",
                "y_true": 0,
                "score__LR_std_C0.1": 0.1,
                "score__LR_std_C1": 0.2,
                "score__DT_leaf5": 0.3,
                "score__ET_leaf5": 0.4,
            },
            {
                "event_id": "cross_project__JM1__seed_013",
                "experiment": "cross_project",
                "target_project": "JM1",
                "seed": 13,
                "split_role": "test",
                "split_position": 0,
                "sample_uid": "s1",
                "y_true": 1,
                "score__LR_std_C0.1": 0.1,
                "score__LR_std_C1": 0.2,
                "score__DT_leaf5": 0.3,
                "score__ET_leaf5": 0.4,
            },
        ]
    )
    canon_res.to_csv(canon / "repeated_all_results.csv", index=False, lineterminator="\n")
    val.to_csv(canon / "validation_log.csv", index=False, lineterminator="\n")
    for build in (build1, build2):
        recon.to_csv(
            build / "results/part3b_prediction_ledger/canonical_result_reconstruction.csv",
            index=False,
            lineterminator="\n",
        )
        val.to_csv(
            build / "results/part3b_prediction_ledger/validation_reconstruction.csv",
            index=False,
            lineterminator="\n",
        )
        pred.to_csv(
            build / "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz",
            index=False,
            compression="gzip",
            lineterminator="\n",
        )
        pred.to_csv(
            build / "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz",
            index=False,
            compression="gzip",
            lineterminator="\n",
        )
    return build1, build2


def run_self_tests() -> Dict[str, Any]:
    tests = [
        ("one_ulp_build_value_difference_rejected", _self_test_one_ulp_build_value_difference_rejected),
        ("build2_score_difference_rejected", _self_test_build2_score_difference_rejected),
        ("validation_categorical_difference_rejected", _self_test_validation_categorical_difference_rejected),
        ("missing_source_role_rejected", _self_test_missing_source_role_rejected),
        ("markdown_json_disagreement_rejected", _self_test_markdown_json_disagreement_rejected),
    ]
    results: List[Dict[str, Any]] = []
    for name, fn in tests:
        passed = bool(fn())
        results.append({"test_name": name, "passed": passed})
    passed_count = sum(1 for item in results if item["passed"])
    failed_count = len(results) - passed_count
    return {
        "tests": results,
        "passed": passed_count,
        "failed": failed_count,
        "total": len(results),
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "repository_production_artifacts_published": 0,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exact fail-closed audit for ExtraTrees canonical-reconciliation evidence."
    )
    parser.add_argument(
        "--build1-root",
        type=Path,
        help="Absolute path to preserved G.R1 Build 1 root directory.",
    )
    parser.add_argument(
        "--build2-root",
        type=Path,
        help="Absolute path to preserved G.R1 Build 2 root directory.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run synthetic no-fit mutation self-tests only.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        summary = run_self_tests()
        print(
            json.dumps(
                {
                    "self_tests": f"{summary['passed']} / {summary['total']} / {summary['total']} / {summary['failed']}",
                    "model_fits_executed": summary["model_fits_executed"],
                    "prediction_calls_executed": summary["prediction_calls_executed"],
                    "repository_production_artifacts_published": summary[
                        "repository_production_artifacts_published"
                    ],
                    "tests": summary["tests"],
                },
                indent=2,
            )
        )
        return 0 if summary["failed"] == 0 and summary["passed"] == summary["total"] else 1

    if args.build1_root is None or args.build2_root is None:
        raise SystemExit("--build1-root and --build2-root are required unless --self-test is set")

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
                "audit_integrity_checks": report["audit_integrity_checks"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
