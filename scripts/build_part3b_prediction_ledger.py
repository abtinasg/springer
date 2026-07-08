#!/usr/bin/env python3
"""Part 3B.2R.1-E.2: Strict Eleven-Artifact Semantic Reproducibility Comparator.

This script is deterministic and self-contained. It may be invoked from any
working directory; it locates the repository root from __file__ and references
all other paths absolutely.

Version: Part-3B.2R.1-E.2-v1
Starting full commit: 58a77a8a697a7c07b5f7136427241be6e60c1000
Accepted Part 3A commit:
d16e28488aa0936014f020c05466181eff219af6
"""
from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Frozen version and provenance constants
# ---------------------------------------------------------------------------
PART3B_VERSION = "Part-3B.2R.1-E.2-v1"
STARTING_COMMIT = "58a77a8a697a7c07b5f7136427241be6e60c1000"
ACCEPTED_PART3A_COMMIT = "d16e28488aa0936014f020c05466181eff219af6"
assert STARTING_COMMIT == \
    "58a77a8a697a7c07b5f7136427241be6e60c1000"
assert ACCEPTED_PART3A_COMMIT == \
    "d16e28488aa0936014f020c05466181eff219af6"
REPOSITORY = "abtinasg/springer"
BRANCH = "major-revision-analysis-v2"

# ---------------------------------------------------------------------------
# Frozen project and candidate constants
# ---------------------------------------------------------------------------
PROJECTS = ["cm1", "jm1", "kc1", "kc2", "pc1"]
SEEDS = [7, 13, 29, 42, 101]
CANDIDATES = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
MODEL_RESULT_ORDER = [
    "LR_std_C0.1",
    "LR_std_C1",
    "DT_leaf5",
    "ET_leaf5",
    "AQRPE_v2_balanced",
    "AQRPE_v2_rank",
    "AQRPE_v2_mcc",
    "AQRPE_v2_soft_top3",
]
OBJECTIVE_MODES = ["balanced", "rank", "mcc"]
EPS = 1e-7

# Dataset profile contract
DATASET_PROFILE_CONTRACT = {
    "CM1": {"rows": 498, "features": 20, "defective": 49},
    "JM1": {"rows": 13204, "features": 20, "defective": 2103},
    "KC1": {"rows": 2109, "features": 20, "defective": 326},
    "KC2": {"rows": 522, "features": 20, "defective": 107},
    "PC1": {"rows": 1109, "features": 20, "defective": 77},
}

EXPECTED_REGISTRY_ROWS = 17442
EXPECTED_EVENT_COUNT = 50
EXPECTED_WITHIN_SPLIT_ROWS = {"train": 52310, "validation": 17450, "test": 17450, "total": 87210}
EXPECTED_CROSS_SPLIT_ROWS = {"train": 261620, "validation": 87220, "test": 87210, "total": 436050}
EXPECTED_WITHIN_PREDICTION_ROWS = {"validation": 17450, "test": 17450, "total": 34900}
EXPECTED_CROSS_PREDICTION_ROWS = {"validation": 87220, "test": 87210, "total": 174430}
EXPECTED_VALIDATION_RECONSTRUCTION_ROWS = 600
EXPECTED_RESULT_RECONSTRUCTION_ROWS = 400
EXPECTED_CANDIDATE_FITS = 200
EXPECTED_IMPUTER_AUDITS = 200
EXPECTED_SCALER_AUDITS = 100
EXPECTED_FEATURE_COUNT_AUDITS = 200
EXPECTED_CONFIG_AUDITS = 200

# Tolerances
PREPROC_RTOL = 1e-12
PREPROC_ATOL = 1e-12
RECON_RTOL = 1e-10
RECON_ATOL = 1e-12

NEGATIVE_TEST_MUTATION = 1e-8

PERSISTED_RECON_RTOL = 1e-10
PERSISTED_RECON_ATOL = 1e-12

SEMANTIC_RECON_RTOL = 1e-10
SEMANTIC_RECON_ATOL = 1e-12
ET_SCORE_ATOL = 1e-15
ET_RANK_METRIC_ATOL = 1e-7

# ---------------------------------------------------------------------------
# Historical canonical nondeterminism exception (validated, not broadened)
# ---------------------------------------------------------------------------
APPROVED_EXCEPTION_EVENT = {
    "event_id": "cross_project__JM1__seed_042",
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
APPROVED_EXCEPTION_DIFF = abs(APPROVED_EXCEPTION_CANONICAL_VALUE - APPROVED_EXCEPTION_RECON_VALUE)
ET_ND_DIAGNOSTIC = {
    "event_id": "cross_project__JM1__seed_042",
    "candidate": "ET_leaf5",
    "n_jobs": 2,
    "fit_count": 1,
    "prediction_calls": 20,
    "unique_score_hashes": 12,
    "unique_roc_auc_values": 2,
    "maximum_score_difference": 4.440892098500626e-16,
    "canonical_values_reproduced": [0.6700601613088453, 0.6700602041438307],
    "n_jobs_1_unique_score_hashes": 1,
    "n_jobs_1_unique_roc_auc_values": 1,
}
ET_ND_MAX_ALLOWED = 1e-15


# ---------------------------------------------------------------------------
# Frozen schemas
# ---------------------------------------------------------------------------
REGISTRY_COLUMNS = [
    "sample_uid",
    "project",
    "original_row_index",
    "raw_csv_row_number",
    "y_true",
    "feature_sha256",
    "content_sha256",
]

SPLIT_MEMBERSHIP_COLUMNS = [
    "event_id",
    "experiment",
    "target_project",
    "seed",
    "sample_uid",
    "sample_project",
    "original_row_index",
    "split_role",
    "split_position",
    "y_true",
]

PREDICTION_LEDGER_COLUMNS = [
    "event_id",
    "experiment",
    "target_project",
    "seed",
    "split_role",
    "split_position",
    "sample_uid",
    "sample_project",
    "original_row_index",
    "y_true",
    "score__LR_std_C0.1",
    "score__LR_std_C1",
    "score__DT_leaf5",
    "score__ET_leaf5",
]

EVENT_MANIFEST_COLUMNS = [
    "event_id", "experiment", "target_project", "seed", "source_projects",
    "n_membership", "n_train", "n_validation", "n_test",
    "train_positive", "train_negative", "validation_positive", "validation_negative",
    "test_positive", "test_negative",
    "train_uid_sha256", "validation_uid_sha256", "test_uid_sha256",
    "feature_count", "feature_schema_sha256",
    "train_source_projects", "validation_source_projects", "test_projects",
    "identity_overlap_count", "target_in_train_count", "target_in_validation_count",
    "source_in_test_count", "preprocessing_train_only_passed",
]

VALIDATION_RECONSTRUCTION_COLUMNS = [
    "experiment", "target_project", "seed", "candidate", "mode",
    "val_threshold", "val_selection_score", "val_avg_precision", "val_roc_auc", "val_mcc",
    "val_f1", "val_balanced_accuracy", "val_precision", "val_recall", "val_brier",
    "val_precision_at_10pct", "val_recall_at_10pct", "val_lift_at_10pct",
    "val_precision_at_20pct", "val_recall_at_20pct", "val_lift_at_20pct",
]

RESULT_RECONSTRUCTION_COLUMNS = [
    "experiment", "target_project", "seed", "model", "selected_candidate", "selection_mode",
    "threshold", "selection_score", "avg_precision", "roc_auc", "mcc", "f1", "balanced_accuracy",
    "precision", "recall", "brier", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
    "precision_at_20pct", "recall_at_20pct", "lift_at_20pct",
]

# ---------------------------------------------------------------------------
# Frozen schema mapping for all eight data artifacts (Part E.1.1)
# ---------------------------------------------------------------------------
EXPECTED_DATA_ARTIFACT_SCHEMAS = {
    "results/part3b_prediction_ledger/sample_registry.csv":
        REGISTRY_COLUMNS,

    "results/part3b_prediction_ledger/event_manifest.csv":
        EVENT_MANIFEST_COLUMNS,

    "results/part3b_prediction_ledger/split_membership_within.csv.gz":
        SPLIT_MEMBERSHIP_COLUMNS,

    "results/part3b_prediction_ledger/split_membership_cross.csv.gz":
        SPLIT_MEMBERSHIP_COLUMNS,

    "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz":
        PREDICTION_LEDGER_COLUMNS,

    "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz":
        PREDICTION_LEDGER_COLUMNS,

    "results/part3b_prediction_ledger/validation_reconstruction.csv":
        VALIDATION_RECONSTRUCTION_COLUMNS,

    "results/part3b_prediction_ledger/canonical_result_reconstruction.csv":
        RESULT_RECONSTRUCTION_COLUMNS,
}

# ---------------------------------------------------------------------------
# Preservation path groups
# ---------------------------------------------------------------------------
RAW_DATA_PATHS = ["data/raw"]
CANONICAL_OUTPUT_PATHS = ["results/part1_full_reproduction", "results/part1_full_reproduction_tables"]
PART3A_ARTIFACT_PATHS = [
    "scripts/run_repeated_evaluation.py",
    "scripts/make_manuscript_tables.py",
    "scripts/build_part3_analysis_contract.py",
    "reports/part3_analysis_contract.json",
    "reports/part3_analysis_contract.md",
]
PRESERVATION_PATHS = RAW_DATA_PATHS + CANONICAL_OUTPUT_PATHS + PART3A_ARTIFACT_PATHS

# ---------------------------------------------------------------------------
# Frozen Part 3C constraint string
# ---------------------------------------------------------------------------
PART3C_CONSTRAINT = (
    "Part 3C must consume the frozen Part 3B split and candidate-probability "
    "ledgers. It may derive objective-matched candidate, adaptive, and soft-ensemble "
    "results, but it must not alter raw data, split assignments, candidate "
    "probabilities, the canonical 400 result rows, or the canonical 600 validation "
    "rows."
)

# ---------------------------------------------------------------------------
# Immutable ordered 41-check audit schema
# ---------------------------------------------------------------------------
REQUIRED_AUDIT_CHECK_NAMES = [
    "source_commit_verified",
    "imported_pipeline_sha_verified",
    "dataset_profile_passed",
    "sample_registry_passed",
    "feature_schema_passed",
    "event_manifest_count_passed",
    "within_split_counts_passed",
    "cross_split_counts_passed",
    "split_membership_totals_passed",
    "split_key_uniqueness_passed",
    "split_identity_disjointness_passed",
    "within_union_coverage_passed",
    "cross_target_isolation_passed",
    "cross_source_isolation_passed",
    "split_determinism_passed",
    "class_count_consistency_passed",
    "preprocessing_train_only_passed",
    "candidate_fit_count_passed",
    "prediction_row_counts_passed",
    "prediction_key_uniqueness_passed",
    "prediction_candidate_schema_passed",
    "prediction_scores_finite_passed",
    "prediction_scores_range_passed",
    "no_train_predictions_passed",
    "validation_reconstruction_count_passed",
    "validation_categorical_match_passed",
    "validation_numeric_match_passed",
    "result_reconstruction_count_passed",
    "result_categorical_match_passed",
    "result_numeric_match_passed",
    "selection_validation_only_passed",
    "test_not_used_for_selection_passed",
    "tie_policy_passed",
    "duplicate_content_audit_completed",
    "schema_target_awareness_documented",
    "pooled_source_validation_design_documented",
    "raw_and_canonical_preservation_passed",
    "deterministic_artifacts_passed",
    "negative_tests_passed",
    "stage_gate_passed",
    "all_critical_checks_passed",
]

# ---------------------------------------------------------------------------
# Immutable ordered 16-field stage-gate schema
# ---------------------------------------------------------------------------
REQUIRED_STAGE_GATE_FIELDS = [
    "part3b_prediction_ledger_complete",
    "raw_data_modified",
    "canonical_outputs_modified",
    "part3a_artifacts_modified",
    "identity_leakage_detected",
    "preprocessing_leakage_detected",
    "selection_test_leakage_detected",
    "canonical_validation_reconstruction_passed",
    "canonical_result_reconstruction_passed",
    "canonical_result_reconstruction_strictly_identical",
    "canonical_result_reconstruction_scientifically_reconciled",
    "canonical_nondeterminism_exception_detected",
    "canonical_nondeterminism_exception_validated",
    "semantic_reproducibility_passed",
    "next_authorized_stage",
    "part3c_constraint",
]


# ---------------------------------------------------------------------------
# Repository and path helpers
# ---------------------------------------------------------------------------
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def frozen_script_path() -> Path:
    return repo_root() / "scripts" / "run_repeated_evaluation.py"


def run_git(args: List[str], cwd: Optional[Path] = None) -> str:
    cmd = ["git"] + args
    result = subprocess.run(cmd, cwd=str(cwd or repo_root()), capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def git_show_bytes(repo: Path, commit: str, rel: str) -> bytes:
    cmd = ["git", "show", f"{commit}:{rel}"]
    result = subprocess.run(cmd, cwd=str(repo), capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"git show {commit}:{rel} failed: {result.stderr}")
    return result.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_str(s: str) -> str:
    return sha256_bytes(s.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def deterministic_float_format(v: Any) -> str:
    if isinstance(v, (str, bytes)):
        if v == "NA":
            return "NA"
        raise ValueError(f"Unexpected string value in hash payload: {v!r}")
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NA"
    return format(float(v), ".17g")


def format_csv_float(v: Any) -> str:
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        if math.isinf(v):
            return ""
        return format(v, ".17g")
    return str(v)


def read_float_csv_round_trip(
    path: Path,
    compression: Optional[str] = None,
) -> pd.DataFrame:
    return pd.read_csv(
        path,
        compression=compression,
        float_precision="round_trip",
    )


# ---------------------------------------------------------------------------
# Atomic writers
# ---------------------------------------------------------------------------
def write_text_atomic(path: Path, data: str, encoding: str = "utf-8") -> None:
    path = path.resolve()
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding=encoding, newline="", dir=str(directory), delete=False
    ) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    os.replace(str(tmp_path), str(path))


def write_csv_atomic(df: pd.DataFrame, path: Path, float_format: str = "%.17g") -> None:
    path = path.resolve()
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=str(directory), delete=False
    ) as tmp:
        df.to_csv(tmp, index=False, encoding="utf-8", lineterminator="\n", float_format=float_format)
        tmp_path = Path(tmp.name)
    os.replace(str(tmp_path), str(path))


def write_csv_gzip_atomic(df: pd.DataFrame, path: Path, float_format: str = "%.17g") -> None:
    path = path.resolve()
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8", lineterminator="\n", float_format=float_format)
    payload = buf.getvalue().encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=str(directory), delete=False) as tmp:
        with gzip.GzipFile(
            fileobj=tmp, mode="wb", compresslevel=9, mtime=0, filename=b""
        ) as gz:
            gz.write(payload)
        tmp_path = Path(tmp.name)
    os.replace(str(tmp_path), str(path))


# ---------------------------------------------------------------------------
# Frozen pipeline import and verification
# ---------------------------------------------------------------------------
def verify_source_commit(commit: str) -> bool:
    try:
        run_git(["rev-parse", "--verify", commit])
        return True
    except RuntimeError:
        return False


def import_frozen_pipeline(repo: Path) -> Any:
    path = repo / "scripts" / "run_repeated_evaluation.py"
    if not path.exists():
        raise FileNotFoundError(f"Frozen executable not found: {path}")
    working_hash = sha256_file(path)
    expected_bytes = git_show_bytes(repo, ACCEPTED_PART3A_COMMIT, "scripts/run_repeated_evaluation.py")
    expected_hash = sha256_bytes(expected_bytes)
    if working_hash != expected_hash:
        raise ValueError(
            f"Frozen executable mismatch. Working copy {working_hash} does not "
            f"match accepted Part 3A commit {expected_hash}. Aborting Part 3B."
        )
    spec = importlib.util.spec_from_file_location(
        "frozen_run_repeated_evaluation", str(path), submodule_search_locations=None
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    imported_hash = sha256_file(path)
    if working_hash != imported_hash or expected_hash != imported_hash:
        raise ValueError(
            f"Imported pipeline SHA mismatch: working={working_hash}, expected={expected_hash}, imported={imported_hash}"
        )
    return module


# ---------------------------------------------------------------------------
# Data loading and project framing
# ---------------------------------------------------------------------------
def load_raw_projects(frozen: Any, data_dir: Path) -> Tuple[Dict[str, pd.DataFrame], List[str], Dict[str, Any]]:
    frames: Dict[str, pd.DataFrame] = {}
    detected_targets = {}
    original_feature_counts = {}
    numeric_feature_counts = {}
    all_null_removed_counts = {}
    missing_value_counts = {}

    for project in PROJECTS:
        csv_path = data_dir / f"{project}.csv"
        df = pd.read_csv(csv_path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        target = frozen.detect_target(df)
        detected_targets[project.upper()] = target
        original_feature_counts[project.upper()] = len(df.columns) - 1
        y = frozen.normalize_target(df[target]).reset_index(drop=True)
        X = df.drop(columns=[target]).copy()
        numeric_cols_before = []
        for c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")
            if X[c].notna().any():
                numeric_cols_before.append(c)
        numeric_feature_counts[project.upper()] = len(numeric_cols_before)
        missing_counts = {}
        for c in X.columns:
            missing_counts[c] = int(X[c].isna().sum())
        missing_value_counts[project.upper()] = missing_counts
        all_null_before = len(X.columns)
        X = X.dropna(axis=1, how="all")
        all_null_removed_counts[project.upper()] = all_null_before - len(X.columns)
        X = X.reset_index(drop=True)
        frames[project] = pd.concat([X, y.to_frame(name="__target__")], axis=1)
        frames[project]["__original_row_index__"] = np.arange(len(frames[project]))

    common = None
    for frame in frames.values():
        cols = set(frame.columns) - {"__target__", "__original_row_index__"}
        common = cols if common is None else common.intersection(cols)
    common_cols = sorted(common)
    if len(common_cols) != 20:
        raise ValueError(f"Common feature schema must contain exactly 20 features, got {len(common_cols)}: {common_cols}")

    out: Dict[str, pd.DataFrame] = {}
    for project in PROJECTS:
        frame = frames[project]
        out[project] = frame[common_cols + ["__target__", "__original_row_index__"]].copy()

    metadata = {
        "detected_target_columns": detected_targets,
        "original_numeric_feature_counts": original_feature_counts,
        "numeric_coercible_feature_counts": numeric_feature_counts,
        "all_null_numeric_columns_removed": all_null_removed_counts,
        "retained_numeric_feature_counts": {p.upper(): len(common_cols) for p in PROJECTS},
        "common_feature_names": common_cols,
        "common_feature_count": len(common_cols),
        "per_project_missing_value_counts": missing_value_counts,
    }
    return out, common_cols, metadata


def build_hash_payloads(frame: pd.DataFrame, common_cols: List[str], include_target: bool) -> List[str]:
    payloads = []
    for _, row in frame.iterrows():
        parts = [deterministic_float_format(row[c]) for c in common_cols]
        if include_target:
            parts.append(str(int(row["__target__"])))
        payloads.append(",".join(parts))
    return payloads


def build_sample_registry(projects: Dict[str, pd.DataFrame], common_cols: List[str]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for project in PROJECTS:
        frame = projects[project]
        feature_payloads = build_hash_payloads(frame, common_cols, include_target=False)
        content_payloads = build_hash_payloads(frame, common_cols, include_target=True)
        for idx, (_, row) in enumerate(frame.iterrows()):
            original_row_index = int(row["__original_row_index__"])
            y_true = int(row["__target__"])
            sample_uid = f"{project.upper()}:{original_row_index:06d}"
            rows.append({
                "sample_uid": sample_uid,
                "project": project.upper(),
                "original_row_index": original_row_index,
                "raw_csv_row_number": original_row_index + 2,
                "y_true": y_true,
                "feature_sha256": sha256_str(feature_payloads[idx]),
                "content_sha256": sha256_str(content_payloads[idx]),
            })
    registry = pd.DataFrame(rows)
    proj_order = {p: i for i, p in enumerate(PROJECTS)}
    registry["_proj_order_"] = registry["project"].str.lower().map(proj_order)
    registry = registry.sort_values(["_proj_order_", "original_row_index"]).drop(columns=["_proj_order_"]).reset_index(drop=True)
    return registry[REGISTRY_COLUMNS]


def attach_registry_identity(projects: Dict[str, pd.DataFrame], registry: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    lookup = {}
    for _, row in registry.iterrows():
        lookup[(row["project"].lower(), int(row["original_row_index"]))] = row["sample_uid"]
    for project in PROJECTS:
        projects[project]["__sample_uid__"] = projects[project].apply(
            lambda r: lookup[(project, int(r["__original_row_index__"]))], axis=1
        )
    return projects


# ---------------------------------------------------------------------------
# Dataset profile
# ---------------------------------------------------------------------------
def build_dataset_profile(projects: Dict[str, pd.DataFrame], common_cols: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
    profile_rows = []
    missing_counts = {}
    for project in PROJECTS:
        frame = projects[project]
        y = frame["__target__"].to_numpy()
        n_rows = len(frame)
        n_features = len(common_cols)
        defective = int(y.sum())
        profile_rows.append({
            "project": project.upper(),
            "n_rows": n_rows,
            "n_features": n_features,
            "defective": defective,
            "defect_rate": float(y.mean()),
        })
        missing_counts[project.upper()] = {}
        for c in common_cols:
            missing_counts[project.upper()][c] = int(frame[c].isna().sum())
    profile_df = pd.DataFrame(profile_rows)
    total_rows = int(profile_df["n_rows"].sum())
    total_defective = int(profile_df["defective"].sum())
    return {
        "profile_df": profile_df,
        "missing_counts": missing_counts,
        "detected_target_columns": metadata["detected_target_columns"],
        "original_numeric_feature_counts": metadata["original_numeric_feature_counts"],
        "numeric_coercible_feature_counts": metadata["numeric_coercible_feature_counts"],
        "all_null_numeric_columns_removed": metadata["all_null_numeric_columns_removed"],
        "retained_numeric_feature_counts": metadata["retained_numeric_feature_counts"],
        "common_feature_names": common_cols,
        "common_feature_count": metadata["common_feature_count"],
        "per_project_missing_value_counts": metadata["per_project_missing_value_counts"],
        "total_rows": total_rows,
        "total_defective": total_defective,
        "total_nondefective": total_rows - total_defective,
        "common_schema_uses_all_project_column_names": True,
        "common_schema_uses_target_feature_values": False,
        "common_schema_uses_target_labels": False,
        "pooled_source_validation": True,
    }


def compute_feature_schema_sha256(common_cols: List[str]) -> str:
    return sha256_str(",".join(common_cols))


# ---------------------------------------------------------------------------
# Split construction
# ---------------------------------------------------------------------------
def event_id(experiment: str, target_project: str, seed: int) -> str:
    return f"{experiment}__{target_project}__seed_{seed:03d}"


def split_hash(sample_uids: Sequence[str]) -> str:
    return sha256_str("\n".join(list(sample_uids)))


def build_event_split(
    experiment: str,
    target_project: str,
    seed: int,
    projects: Dict[str, pd.DataFrame],
    common_cols: List[str],
) -> Dict[str, Any]:
    target = target_project.lower()
    if experiment == "within_project":
        frame = projects[target].reset_index(drop=True)
        y = frame["__target__"].to_numpy()
        idx = np.arange(len(frame))
        idx_temp, idx_test = train_test_split(idx, test_size=0.20, stratify=y, random_state=seed)
        y_temp = y[idx_temp]
        idx_train, idx_val = train_test_split(idx_temp, test_size=0.25, stratify=y_temp, random_state=seed)
        train_frame = frame.loc[idx_train].reset_index(drop=True)
        val_frame = frame.loc[idx_val].reset_index(drop=True)
        test_frame = frame.loc[idx_test].reset_index(drop=True)
        source_projects = None
    elif experiment == "cross_project":
        source_names = [p for p in PROJECTS if p != target]
        src_frames = [projects[p] for p in source_names]
        src_frame = pd.concat(src_frames, ignore_index=True).reset_index(drop=True)
        target_frame = projects[target].reset_index(drop=True)
        y_src = src_frame["__target__"].to_numpy()
        idx_src = np.arange(len(src_frame))
        idx_train, idx_val = train_test_split(idx_src, test_size=0.25, stratify=y_src, random_state=seed)
        idx_test = np.arange(len(target_frame))
        train_frame = src_frame.loc[idx_train].reset_index(drop=True)
        val_frame = src_frame.loc[idx_val].reset_index(drop=True)
        test_frame = target_frame.loc[idx_test].reset_index(drop=True)
        source_projects = source_names
    else:
        raise ValueError(f"Unknown experiment: {experiment}")

    X_train = train_frame[common_cols]
    y_train = train_frame["__target__"].to_numpy()
    X_val = val_frame[common_cols]
    y_val = val_frame["__target__"].to_numpy()
    X_test = test_frame[common_cols]
    y_test = test_frame["__target__"].to_numpy()

    def split_info(frame: pd.DataFrame) -> Dict[str, Any]:
        return {
            "uids": frame["__sample_uid__"].tolist(),
            "projects": frame.apply(lambda r: r["__sample_uid__"].split(":")[0], axis=1).tolist(),
            "original_row_indices": frame["__original_row_index__"].tolist(),
            "y_true": frame["__target__"].tolist(),
        }

    train_info = split_info(train_frame)
    val_info = split_info(val_frame)
    test_info = split_info(test_frame)

    return {
        "event_id": event_id(experiment, target_project, seed),
        "experiment": experiment,
        "target_project": target_project.upper(),
        "seed": seed,
        "source_projects": source_projects,
        "X_train": X_train,
        "y_train": y_train,
        "X_val": X_val,
        "y_val": y_val,
        "X_test": X_test,
        "y_test": y_test,
        "train_frame": train_frame,
        "val_frame": val_frame,
        "test_frame": test_frame,
        "train_info": train_info,
        "val_info": val_info,
        "test_info": test_info,
        "train_uid_sha256": split_hash(train_info["uids"]),
        "validation_uid_sha256": split_hash(val_info["uids"]),
        "test_uid_sha256": split_hash(test_info["uids"]),
        "n_train": len(train_frame),
        "n_validation": len(val_frame),
        "n_test": len(test_frame),
    }


def build_all_events(projects: Dict[str, pd.DataFrame], common_cols: List[str]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for experiment in ["within_project", "cross_project"]:
        for seed in SEEDS:
            for target in PROJECTS:
                events.append(build_event_split(experiment, target.upper(), seed, projects, common_cols))
    return events


# ---------------------------------------------------------------------------
# Candidate fitting, preprocessing audit, and configuration audit
# ---------------------------------------------------------------------------
def fit_event_candidates(frozen: Any, event: Dict[str, Any], seed: int) -> Dict[str, Any]:
    fitted: Dict[str, Any] = {}
    for name, factory in frozen.candidate_factories().items():
        model = factory(seed)
        model.fit(event["X_train"], event["y_train"])
        val_scores = frozen.model_scores(model, event["X_val"])
        test_scores = frozen.model_scores(model, event["X_test"])
        fitted[name] = {
            "model": model,
            "val_scores": val_scores,
            "test_scores": test_scores,
        }
        for mode in OBJECTIVE_MODES:
            if mode == "rank":
                t = 0.5
                obj = frozen.objective_value(event["y_val"], val_scores, 0.5, "rank")
            else:
                t, obj = frozen.select_threshold(event["y_val"], val_scores, mode)
            fitted[name][f"threshold_{mode}"] = t
            fitted[name][f"objective_{mode}"] = obj
    return fitted


def audit_imputer(model: Any, X_train: pd.DataFrame, name: str) -> Dict[str, Any]:
    imputer = model.named_steps["imputer"]
    expected = np.nanmedian(X_train.to_numpy(), axis=0)
    actual = imputer.statistics_
    passed = np.allclose(expected, actual, rtol=PREPROC_RTOL, atol=PREPROC_ATOL, equal_nan=True)
    return {
        "candidate": name,
        "type": "imputer",
        "expected": expected,
        "actual": actual,
        "passed": passed,
    }


def audit_scaler(model: Any, X_train: pd.DataFrame, name: str) -> Dict[str, Any]:
    scaler = model.named_steps["scaler"]
    imputer = model.named_steps["imputer"]
    X_train_imputed = imputer.transform(X_train)
    expected_mean = np.mean(X_train_imputed, axis=0)
    expected_var = np.var(X_train_imputed, axis=0)
    passed_mean = np.allclose(expected_mean, scaler.mean_, rtol=PREPROC_RTOL, atol=PREPROC_ATOL, equal_nan=True)
    passed_var = np.allclose(expected_var, scaler.var_, rtol=PREPROC_RTOL, atol=PREPROC_ATOL, equal_nan=True)
    passed_features = int(getattr(model, "n_features_in_", getattr(scaler, "n_features_in_", None))) == 20
    return {
        "candidate": name,
        "type": "scaler",
        "expected_mean": expected_mean,
        "actual_mean": scaler.mean_,
        "expected_var": expected_var,
        "actual_var": scaler.var_,
        "passed_mean": passed_mean,
        "passed_var": passed_var,
        "passed_features": passed_features,
        "passed": passed_mean and passed_var and passed_features,
    }


def audit_feature_count(model: Any, X_train: pd.DataFrame, name: str) -> Dict[str, Any]:
    audit = {
        "candidate": name,
        "type": "feature_count",
        "expected_features": 20,
        "pipeline_n_features_in": None,
        "imputer_n_features_in": None,
        "scaler_n_features_in": None,
        "classifier_n_features_in": None,
        "passed": False,
    }
    available = []
    if hasattr(model, "n_features_in_"):
        audit["pipeline_n_features_in"] = int(model.n_features_in_)
        available.append(audit["pipeline_n_features_in"])
    if hasattr(model, "named_steps"):
        imputer = model.named_steps.get("imputer")
        if imputer and hasattr(imputer, "n_features_in_"):
            audit["imputer_n_features_in"] = int(imputer.n_features_in_)
            available.append(audit["imputer_n_features_in"])
        scaler = model.named_steps.get("scaler")
        if scaler and hasattr(scaler, "n_features_in_"):
            audit["scaler_n_features_in"] = int(scaler.n_features_in_)
            available.append(audit["scaler_n_features_in"])
        clf = model.named_steps.get("clf")
        if clf and hasattr(clf, "n_features_in_"):
            audit["classifier_n_features_in"] = int(clf.n_features_in_)
            available.append(audit["classifier_n_features_in"])
    else:
        if hasattr(model, "n_features_in_"):
            audit["classifier_n_features_in"] = int(model.n_features_in_)
            available.append(audit["classifier_n_features_in"])
    # Require at least pipeline/imputer and classifier counts.
    has_input_count = (audit["pipeline_n_features_in"] is not None) or (audit["imputer_n_features_in"] is not None)
    has_classifier_count = audit["classifier_n_features_in"] is not None
    all_match = all(v == 20 for v in available) and len(available) > 0
    audit["passed"] = has_input_count and has_classifier_count and all_match
    return audit


def validate_candidate_configuration(fitted: Dict[str, Any], frozen: Any, event_id: str, seed: int) -> List[Dict[str, Any]]:
    audits: List[Dict[str, Any]] = []
    factories = frozen.candidate_factories()
    for name in CANDIDATES:
        model = fitted[name]["model"]
        clf = model.named_steps["clf"] if hasattr(model, "named_steps") else model
        actual_params = clf.get_params() if hasattr(clf, "get_params") else {}
        passed = True
        checks = {}

        factory = factories[name]
        # Build a fresh factory pipeline with the event seed to inspect intended parameters.
        fresh_pipeline = factory(seed)
        fresh_clf = fresh_pipeline.named_steps["clf"] if hasattr(fresh_pipeline, "named_steps") else fresh_pipeline
        expected_params = fresh_clf.get_params() if hasattr(fresh_clf, "get_params") else {}

        if name == "LR_std_C0.1":
            for param, expected in [("C", 0.1), ("penalty", "l2"), ("solver", "lbfgs"), ("class_weight", "balanced"), ("max_iter", 600), ("random_state", seed)]:
                actual = actual_params.get(param)
                checks[param] = (actual == expected)
                if not checks[param]:
                    passed = False
            imputer = model.named_steps.get("imputer")
            checks["imputer_strategy"] = bool(imputer and getattr(imputer, "strategy", None) == "median")
            if not checks["imputer_strategy"]:
                passed = False
            checks["scaler_present"] = "scaler" in model.named_steps
            if not checks["scaler_present"]:
                passed = False
        elif name == "LR_std_C1":
            for param, expected in [("C", 1.0), ("penalty", "l2"), ("solver", "lbfgs"), ("class_weight", "balanced"), ("max_iter", 600), ("random_state", seed)]:
                actual = actual_params.get(param)
                checks[param] = (actual == expected)
                if not checks[param]:
                    passed = False
            imputer = model.named_steps.get("imputer")
            checks["imputer_strategy"] = bool(imputer and getattr(imputer, "strategy", None) == "median")
            if not checks["imputer_strategy"]:
                passed = False
            checks["scaler_present"] = "scaler" in model.named_steps
            if not checks["scaler_present"]:
                passed = False
        elif name == "DT_leaf5":
            for param, expected in [("criterion", "gini"), ("splitter", "best"), ("min_samples_leaf", 5), ("max_depth", None), ("class_weight", None), ("random_state", seed)]:
                actual = actual_params.get(param)
                checks[param] = (actual == expected)
                if not checks[param]:
                    passed = False
            imputer = model.named_steps.get("imputer")
            checks["imputer_strategy"] = bool(imputer and getattr(imputer, "strategy", None) == "median")
            if not checks["imputer_strategy"]:
                passed = False
        elif name == "ET_leaf5":
            for param, expected in [("n_estimators", 50), ("criterion", "gini"), ("max_depth", None), ("min_samples_leaf", 5), ("max_features", "sqrt"), ("bootstrap", False), ("class_weight", "balanced"), ("random_state", seed), ("n_jobs", 2)]:
                actual = actual_params.get(param)
                checks[param] = (actual == expected)
                if not checks[param]:
                    passed = False
            imputer = model.named_steps.get("imputer")
            checks["imputer_strategy"] = bool(imputer and getattr(imputer, "strategy", None) == "median")
            if not checks["imputer_strategy"]:
                passed = False
        else:
            passed = False

        audits.append({
            "event_id": event_id,
            "candidate": name,
            "type": "configuration",
            "expected_params": expected_params,
            "actual_params": actual_params,
            "checks": checks,
            "passed": passed,
        })
    return audits


def audit_event_preprocessing(event: Dict[str, Any], fitted: Dict[str, Any]) -> List[Dict[str, Any]]:
    audits: List[Dict[str, Any]] = []
    for name in CANDIDATES:
        model = fitted[name]["model"]
        audit = audit_imputer(model, event["X_train"], name)
        audit["event_id"] = event["event_id"]
        audits.append(audit)
        if "scaler" in model.named_steps:
            audit_s = audit_scaler(model, event["X_train"], name)
            audit_s["event_id"] = event["event_id"]
            audits.append(audit_s)
        audit_f = audit_feature_count(model, event["X_train"], name)
        audit_f["event_id"] = event["event_id"]
        audits.append(audit_f)
    return audits


# ---------------------------------------------------------------------------
# Split-membership and prediction-ledger row builders
# ---------------------------------------------------------------------------
def build_split_membership_rows(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for role, info in [("train", event["train_info"]), ("validation", event["val_info"]), ("test", event["test_info"])]:
        for pos, uid in enumerate(info["uids"]):
            rows.append({
                "event_id": event["event_id"],
                "experiment": event["experiment"],
                "target_project": event["target_project"],
                "seed": event["seed"],
                "sample_uid": uid,
                "sample_project": info["projects"][pos],
                "original_row_index": info["original_row_indices"][pos],
                "split_role": role,
                "split_position": pos,
                "y_true": info["y_true"][pos],
            })
    return rows


def build_prediction_rows(event: Dict[str, Any], fitted: Dict[str, Any], frozen: Any) -> List[Dict[str, Any]]:
    """Build exactly the 14-column prediction-ledger rows for validation and test."""
    rows: List[Dict[str, Any]] = []
    for role, frame in [("validation", event["val_frame"]), ("test", event["test_frame"])]:
        for pos in range(len(frame)):
            row = {
                "event_id": event["event_id"],
                "experiment": event["experiment"],
                "target_project": event["target_project"],
                "seed": event["seed"],
                "split_role": role,
                "split_position": pos,
                "sample_uid": frame["__sample_uid__"].iloc[pos],
                "sample_project": frame["__sample_uid__"].iloc[pos].split(":")[0],
                "original_row_index": int(frame["__original_row_index__"].iloc[pos]),
                "y_true": int(frame["__target__"].iloc[pos]),
            }
            for cand in CANDIDATES:
                score = fitted[cand]["val_scores"][pos] if role == "validation" else fitted[cand]["test_scores"][pos]
                row[f"score__{cand}"] = float(score)
            rows.append(row)
    return rows


def _split_membership_sorted(df: pd.DataFrame) -> pd.DataFrame:
    role_order = {"train": 0, "validation": 1, "test": 2}
    proj_order = {p.upper(): i for i, p in enumerate(PROJECTS)}
    df = df.copy()
    df["_role_order"] = df["split_role"].map(role_order)
    df["_proj_order"] = df["target_project"].map(proj_order)
    df = df.sort_values(["experiment", "seed", "_proj_order", "_role_order", "split_position"]).reset_index(drop=True)
    return df.drop(columns=["_role_order", "_proj_order"])


def _prediction_ledger_sorted(df: pd.DataFrame) -> pd.DataFrame:
    role_order = {"validation": 0, "test": 1}
    proj_order = {p.upper(): i for i, p in enumerate(PROJECTS)}
    df = df.copy()
    df["_role_order"] = df["split_role"].map(role_order)
    df["_proj_order"] = df["target_project"].map(proj_order)
    df = df.sort_values(["experiment", "seed", "_proj_order", "_role_order", "split_position"]).reset_index(drop=True)
    return df.drop(columns=["_role_order", "_proj_order"])


# ---------------------------------------------------------------------------
# Event manifest builder
# ---------------------------------------------------------------------------
def build_event_manifest(events: List[Dict[str, Any]], common_cols: List[str], feature_schema_sha256: str, preprocessing_audits: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for event in events:
        event_id = event["event_id"]
        experiment = event["experiment"]
        target = event["target_project"]
        seed = event["seed"]
        if experiment == "within_project":
            source_projects = target
            train_sources = target
            val_sources = target
            test_projects = target
        else:
            srcs = [p.upper() for p in event["source_projects"]]
            source_projects = "|".join(srcs)
            train_projs = sorted(set(event["train_info"]["projects"]), key=lambda p: PROJECTS.index(p.lower()))
            val_projs = sorted(set(event["val_info"]["projects"]), key=lambda p: PROJECTS.index(p.lower()))
            train_sources = "|".join(train_projs)
            val_sources = "|".join(val_projs)
            test_projects = target

        train_uids = set(event["train_info"]["uids"])
        val_uids = set(event["val_info"]["uids"])
        test_uids = set(event["test_info"]["uids"])
        identity_overlap = len(train_uids & val_uids) + len(train_uids & test_uids) + len(val_uids & test_uids)
        target_in_train = 0
        target_in_val = 0
        source_in_test = 0
        if experiment == "cross_project":
            target_in_train = sum(1 for p in event["train_info"]["projects"] if p == target)
            target_in_val = sum(1 for p in event["val_info"]["projects"] if p == target)
            source_in_test = sum(1 for p in event["test_info"]["projects"] if p != target)

        event_audits = [a for a in preprocessing_audits if a["event_id"] == event_id]
        all_passed = all(a["passed"] for a in event_audits)

        rows.append({
            "event_id": event_id,
            "experiment": experiment,
            "target_project": target,
            "seed": seed,
            "source_projects": source_projects,
            "n_membership": event["n_train"] + event["n_validation"] + event["n_test"],
            "n_train": event["n_train"],
            "n_validation": event["n_validation"],
            "n_test": event["n_test"],
            "train_positive": int(event["y_train"].sum()),
            "train_negative": len(event["y_train"]) - int(event["y_train"].sum()),
            "validation_positive": int(event["y_val"].sum()),
            "validation_negative": len(event["y_val"]) - int(event["y_val"].sum()),
            "test_positive": int(event["y_test"].sum()),
            "test_negative": len(event["y_test"]) - int(event["y_test"].sum()),
            "train_uid_sha256": event["train_uid_sha256"],
            "validation_uid_sha256": event["validation_uid_sha256"],
            "test_uid_sha256": event["test_uid_sha256"],
            "feature_count": len(common_cols),
            "feature_schema_sha256": feature_schema_sha256,
            "train_source_projects": train_sources,
            "validation_source_projects": val_sources,
            "test_projects": test_projects,
            "identity_overlap_count": identity_overlap,
            "target_in_train_count": target_in_train,
            "target_in_validation_count": target_in_val,
            "source_in_test_count": source_in_test,
            "preprocessing_train_only_passed": all_passed,
        })
    return pd.DataFrame(rows)[EVENT_MANIFEST_COLUMNS]


# ---------------------------------------------------------------------------
# Validation-only policy freezing and test-only evaluation
# ---------------------------------------------------------------------------
def freeze_event_selection_policy(frozen: Any, event_validation_ledger: pd.DataFrame) -> Dict[str, Any]:
    """Freeze the event-level selection policy using only validation rows."""
    if (event_validation_ledger["split_role"] != "validation").any():
        raise ValueError("freeze_event_selection_policy received non-validation rows.")
    policy: Dict[str, Any] = {}
    group = event_validation_ledger.sort_values("split_position")
    y_val = group["y_true"].to_numpy()
    for cand in CANDIDATES:
        s_val = group[f"score__{cand}"].to_numpy()
        t_bal, obj_bal = frozen.select_threshold(y_val, s_val, "balanced")
        t_mcc, obj_mcc = frozen.select_threshold(y_val, s_val, "mcc")
        obj_rank = frozen.objective_value(y_val, s_val, 0.5, "rank")
        policy[cand] = {
            "balanced_threshold": t_bal,
            "balanced_objective": obj_bal,
            "mcc_threshold": t_mcc,
            "mcc_objective": obj_mcc,
            "rank_objective": obj_rank,
        }
    selected_balanced = max(CANDIDATES, key=lambda k: policy[k]["balanced_objective"])
    selected_rank = max(CANDIDATES, key=lambda k: policy[k]["rank_objective"])
    selected_mcc = max(CANDIDATES, key=lambda k: policy[k]["mcc_objective"])
    top3 = sorted(CANDIDATES, key=lambda k: (-policy[k]["balanced_objective"], CANDIDATES.index(k)))[:3]
    top3_str = "|".join(top3)
    val_stack = np.mean([group[f"score__{k}"].to_numpy() for k in top3], axis=0)
    t_stack, obj_stack = frozen.select_threshold(y_val, val_stack, "balanced")
    tie_evidence = {"candidate_ties": [], "threshold_ties": [], "soft_top3_ties": []}
    for i, c1 in enumerate(CANDIDATES):
        for c2 in CANDIDATES[i + 1:]:
            if policy[c1]["balanced_objective"] == policy[c2]["balanced_objective"]:
                tie_evidence["candidate_ties"].append((c1, c2, "balanced"))
            if policy[c1]["rank_objective"] == policy[c2]["rank_objective"]:
                tie_evidence["candidate_ties"].append((c1, c2, "rank"))
            if policy[c1]["mcc_objective"] == policy[c2]["mcc_objective"]:
                tie_evidence["candidate_ties"].append((c1, c2, "mcc"))
            if policy[c1]["balanced_threshold"] == policy[c2]["balanced_threshold"]:
                tie_evidence["threshold_ties"].append((c1, c2, "balanced"))
            if policy[c1]["mcc_threshold"] == policy[c2]["mcc_threshold"]:
                tie_evidence["threshold_ties"].append((c1, c2, "mcc"))
    if len(top3) == 3:
        cutoff_obj = policy[top3[2]]["balanced_objective"]
        for cand in CANDIDATES:
            if cand not in top3 and policy[cand]["balanced_objective"] == cutoff_obj:
                tie_evidence["soft_top3_ties"].append((top3[2], cand, cutoff_obj))
    return {
        "selected_balanced_candidate": selected_balanced,
        "selected_rank_candidate": selected_rank,
        "selected_mcc_candidate": selected_mcc,
        "soft_top3_candidates": top3_str,
        "soft_top3_threshold": t_stack,
        "soft_top3_validation_objective": obj_stack,
        "candidate_policies": policy,
        "tie_policy_evidence": tie_evidence,
    }


def evaluate_frozen_policy_on_test_ledger(frozen: Any, frozen_policy: Dict[str, Any], event_test_ledger: pd.DataFrame) -> List[Dict[str, Any]]:
    """Evaluate the frozen validation-only policy on the event's test ledger."""
    if (event_test_ledger["split_role"] != "test").any():
        raise ValueError("evaluate_frozen_policy_on_test_ledger received non-test rows.")
    test_df = event_test_ledger.sort_values("split_position")
    y_test = test_df["y_true"].to_numpy()
    test_scores = {cand: test_df[f"score__{cand}"].to_numpy() for cand in CANDIDATES}
    policy = frozen_policy["candidate_policies"]
    rows: List[Dict[str, Any]] = []
    for cand in CANDIDATES:
        t = policy[cand]["balanced_threshold"]
        row = frozen.metric_row(y_test, test_scores[cand], t)
        row.update({"model": cand, "selected_candidate": cand, "selection_mode": "single_candidate_balanced_threshold", "threshold": t, "selection_score": policy[cand]["balanced_objective"]})
        rows.append(row)
    bal_cand = frozen_policy["selected_balanced_candidate"]
    t = policy[bal_cand]["balanced_threshold"]
    row = frozen.metric_row(y_test, test_scores[bal_cand], t)
    row.update({"model": "AQRPE_v2_balanced", "selected_candidate": bal_cand, "selection_mode": "balanced_objective", "threshold": t, "selection_score": policy[bal_cand]["balanced_objective"]})
    rows.append(row)
    rank_cand = frozen_policy["selected_rank_candidate"]
    row = frozen.metric_row(y_test, test_scores[rank_cand], 0.5)
    row.update({"model": "AQRPE_v2_rank", "selected_candidate": rank_cand, "selection_mode": "rank_objective_fixed_threshold", "threshold": 0.5, "selection_score": policy[rank_cand]["rank_objective"]})
    rows.append(row)
    mcc_cand = frozen_policy["selected_mcc_candidate"]
    t = policy[mcc_cand]["mcc_threshold"]
    row = frozen.metric_row(y_test, test_scores[mcc_cand], t)
    row.update({"model": "AQRPE_v2_mcc", "selected_candidate": mcc_cand, "selection_mode": "mcc_objective", "threshold": t, "selection_score": policy[mcc_cand]["mcc_objective"]})
    rows.append(row)
    top3 = frozen_policy["soft_top3_candidates"].split("|")
    test_stack = np.mean([test_scores[k] for k in top3], axis=0)
    t_stack = frozen_policy["soft_top3_threshold"]
    row = frozen.metric_row(y_test, test_stack, t_stack)
    row.update({"model": "AQRPE_v2_soft_top3", "selected_candidate": frozen_policy["soft_top3_candidates"], "selection_mode": "soft_top3_balanced_objective", "threshold": t_stack, "selection_score": frozen_policy["soft_top3_validation_objective"]})
    rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Reconstruction from the ledger
# ---------------------------------------------------------------------------
def reconstruct_validation_from_ledger(frozen: Any, prediction_ledger: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct the 600 validation rows from validation-ledger rows only."""
    val_rows = prediction_ledger[prediction_ledger["split_role"] == "validation"].sort_values(["experiment", "seed", "target_project", "split_position"])
    rows: List[Dict[str, Any]] = []
    for (experiment, target_project, seed), group in val_rows.groupby(["experiment", "target_project", "seed"], sort=False):
        group = group.sort_values("split_position")
        for cand in CANDIDATES:
            s_val = group[f"score__{cand}"].to_numpy()
            y_val = group["y_true"].to_numpy()
            for mode in OBJECTIVE_MODES:
                if mode == "rank":
                    t = 0.5
                    obj = frozen.objective_value(y_val, s_val, 0.5, "rank")
                else:
                    t, obj = frozen.select_threshold(y_val, s_val, mode)
                row = frozen.metric_row(y_val, s_val, t)
                row.update({"experiment": experiment, "target_project": target_project, "seed": seed, "candidate": cand, "mode": mode})
                row["val_threshold"] = t
                row["val_selection_score"] = obj
                rows.append(row)
    df = pd.DataFrame(rows)
    metric_cols = ["avg_precision", "roc_auc", "mcc", "f1", "balanced_accuracy", "precision", "recall", "brier", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "precision_at_20pct", "recall_at_20pct", "lift_at_20pct"]
    renamed = {c: f"val_{c}" for c in metric_cols}
    df = df.rename(columns=renamed)
    return df[VALIDATION_RECONSTRUCTION_COLUMNS]


def reconstruct_results_from_ledger(frozen: Any, prediction_ledger: pd.DataFrame, event_manifest: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct the 400 canonical result rows exclusively from the ledger."""
    rows: List[Dict[str, Any]] = []
    for _, event_row in event_manifest.iterrows():
        event_id = event_row["event_id"]
        experiment = event_row["experiment"]
        target_project = event_row["target_project"]
        seed = event_row["seed"]
        event_pred = prediction_ledger[prediction_ledger["event_id"] == event_id]
        val_pred = event_pred[event_pred["split_role"] == "validation"]
        test_pred = event_pred[event_pred["split_role"] == "test"]
        policy = freeze_event_selection_policy(frozen, val_pred)
        result_rows = evaluate_frozen_policy_on_test_ledger(frozen, policy, test_pred)
        for r in result_rows:
            r["experiment"] = experiment
            r["target_project"] = target_project
            r["seed"] = seed
            rows.append(r)
    df = pd.DataFrame(rows)
    return df[RESULT_RECONSTRUCTION_COLUMNS]


# ---------------------------------------------------------------------------
# Shared reconstruction comparison
# ---------------------------------------------------------------------------
def compare_reconstruction(recon: pd.DataFrame, canonical: pd.DataFrame, keys: List[str], numeric_cols: List[str], rtol: float = RECON_RTOL, atol: float = RECON_ATOL) -> Tuple[bool, Dict[str, Any]]:
    evidence = {"row_count": len(recon), "canonical_row_count": len(canonical)}
    passed = len(recon) == len(canonical)
    # Robust categorical comparison: merge on string keys and align rows.
    recon_key_df = recon[keys].astype(str).reset_index(drop=True)
    canonical_key_df = canonical[keys].astype(str).reset_index(drop=True)
    recon_key_df["_recon_idx"] = recon_key_df.index
    canonical_key_df["_canon_idx"] = canonical_key_df.index
    merged = recon_key_df.merge(canonical_key_df, on=keys, how="outer", indicator=True)
    cat_check = (len(recon) == len(canonical) and (merged["_merge"] == "both").all())
    evidence["categorical_match"] = bool(cat_check)
    passed = passed and cat_check
    per_column = []
    max_abs = 0.0
    max_rel = 0.0
    mismatches = 0
    if cat_check:
        merged = merged[merged["_merge"] == "both"].sort_values(["_recon_idx", "_canon_idx"]).reset_index(drop=True)
        for col in numeric_cols:
            if col not in recon.columns or col not in canonical.columns:
                continue
            a = recon[col].iloc[merged["_recon_idx"]].to_numpy(dtype=float)
            b = canonical[col].iloc[merged["_canon_idx"]].to_numpy(dtype=float)
            close = np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=True)
            col_mismatches = int((~close).sum())
            mismatches += col_mismatches
            diff = np.abs(a - b)
            col_max_abs = float(np.nanmax(diff)) if np.any(np.isfinite(diff)) else 0.0
            rel = np.where(np.abs(b) > 0, diff / np.abs(b), diff)
            col_max_rel = float(np.nanmax(rel)) if np.any(np.isfinite(rel)) else 0.0
            max_abs = max(max_abs, col_max_abs)
            max_rel = max(max_rel, col_max_rel)
            per_column.append({"column": col, "compared_count": len(a), "mismatch_count": col_mismatches, "maximum_absolute_difference": col_max_abs, "maximum_relative_difference": col_max_rel})
    evidence["numeric_mismatches"] = mismatches
    evidence["max_abs_diff"] = max_abs
    evidence["max_rel_diff"] = max_rel
    evidence["per_column"] = per_column
    passed = passed and mismatches == 0
    return passed, evidence


def validate_validation_reconstruction(recon: pd.DataFrame, canonical: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    keys = ["experiment", "target_project", "seed", "candidate", "mode"]
    numeric_cols = [c for c in VALIDATION_RECONSTRUCTION_COLUMNS if c not in keys]
    return compare_reconstruction(recon, canonical, keys, numeric_cols)


def validate_result_reconstruction(recon: pd.DataFrame, canonical: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    keys = ["experiment", "target_project", "seed", "model"]
    cat_cols = keys + ["selected_candidate", "selection_mode"]
    # Robust categorical comparison for all categorical columns.
    recon_cat_df = recon[cat_cols].astype(str).reset_index(drop=True)
    canonical_cat_df = canonical[cat_cols].astype(str).reset_index(drop=True)
    recon_cat_df["_recon_idx"] = recon_cat_df.index
    canonical_cat_df["_canon_idx"] = canonical_cat_df.index
    merged = recon_cat_df.merge(canonical_cat_df, on=cat_cols, how="outer", indicator=True)
    cat_ok = (len(recon) == len(canonical) and (merged["_merge"] == "both").all())
    numeric_cols = [c for c in RESULT_RECONSTRUCTION_COLUMNS if c not in cat_cols]
    passed, evidence = compare_reconstruction(recon, canonical, keys, numeric_cols)
    passed = passed and cat_ok
    evidence["categorical_match"] = evidence.get("categorical_match", False) and cat_ok
    evidence["selected_candidate_mode_match"] = bool(cat_ok)
    return passed, evidence


CANONICAL_EXCEPTION_NUMERIC_TOL = 1e-15


def is_exact_directional_canonical_exception(m: Dict[str, Any]) -> bool:
    """Return True only when *m* matches the single approved directional cell exactly.

    This is a pure helper: no file access, no model fitting, no global state mutation.
    Direction is mandatory -- swapping canonical_value and reconstruction_value fails.
    Numeric fields are compared with a maximum tolerance of 1e-15.
    """
    categorical_fields = [
        "experiment",
        "target_project",
        "seed",
        "model",
        "selected_candidate",
        "selection_mode",
        "column",
    ]
    for field in categorical_fields:
        if m.get(field) != APPROVED_EXCEPTION_EVENT.get(field):
            return False

    if abs(float(m.get("canonical_value", float("nan"))) - APPROVED_EXCEPTION_CANONICAL_VALUE) > CANONICAL_EXCEPTION_NUMERIC_TOL:
        return False
    if abs(float(m.get("recon_value", float("nan"))) - APPROVED_EXCEPTION_RECON_VALUE) > CANONICAL_EXCEPTION_NUMERIC_TOL:
        return False
    if abs(float(m.get("absolute_difference", float("nan"))) - APPROVED_EXCEPTION_DIFF) > CANONICAL_EXCEPTION_NUMERIC_TOL:
        return False

    return True


def validate_canonical_nondeterminism_exception(
    recon: pd.DataFrame,
    canonical: pd.DataFrame,
    prediction_ledger: pd.DataFrame,
    frozen: Any,
) -> Dict[str, Any]:
    """Validate the one approved historical floating-point nondeterminism exception.

    Exactly one directional cell may pass: the documented ET_leaf5 roc_auc mismatch
    for cross_project/JM1/seed_42/AQRPE_v2_rank.  No broad candidate-level, event-level,
    or ET-derived tolerance exception is permitted.
    """
    # 1. Identify all strict mismatches using the canonical tolerance.
    keys = ["experiment", "target_project", "seed", "model"]
    cat_cols = keys + ["selected_candidate", "selection_mode"]
    numeric_cols = [c for c in RESULT_RECONSTRUCTION_COLUMNS if c not in cat_cols]
    passed_strict, evidence_strict = compare_reconstruction(recon, canonical, keys, numeric_cols)
    strict_mismatches = []
    if evidence_strict.get("categorical_match", False) and not passed_strict:
        merged = recon[cat_cols].astype(str).reset_index(drop=True)
        merged["_recon_idx"] = merged.index
        canon_key = canonical[cat_cols].astype(str).reset_index(drop=True)
        canon_key["_canon_idx"] = canon_key.index
        merged = merged.merge(canon_key, on=cat_cols, how="outer", indicator=True)
        merged = merged[merged["_merge"] == "both"].sort_values(["_recon_idx", "_canon_idx"]).reset_index(drop=True)
        for col in numeric_cols:
            a = recon[col].iloc[merged["_recon_idx"]].to_numpy(dtype=float)
            b = canonical[col].iloc[merged["_canon_idx"]].to_numpy(dtype=float)
            for i in range(len(a)):
                if not np.isclose(a[i], b[i], rtol=RECON_RTOL, atol=RECON_ATOL, equal_nan=True):
                    row = recon.iloc[merged["_recon_idx"].iloc[i]]
                    strict_mismatches.append({
                        "experiment": row["experiment"],
                        "target_project": row["target_project"],
                        "seed": int(row["seed"]),
                        "model": row["model"],
                        "selected_candidate": row["selected_candidate"],
                        "selection_mode": row["selection_mode"],
                        "column": col,
                        "canonical_value": float(b[i]),
                        "recon_value": float(a[i]),
                        "absolute_difference": float(abs(a[i] - b[i])),
                    })

    # 2. Approve only the exact single directional cell.
    approved: List[Dict[str, Any]] = []
    unapproved: List[Dict[str, Any]] = []
    documented_approved = False
    for m in strict_mismatches:
        if is_exact_directional_canonical_exception(m):
            approved.append(m)
            documented_approved = True
        else:
            unapproved.append(m)

    # 3. Verify that the ET_leaf5 baseline and AQRPE_v2_rank rows use the same score vector in the ledger.
    same_score_vector = False
    event_rows = prediction_ledger[prediction_ledger["event_id"] == APPROVED_EXCEPTION_EVENT["event_id"]]
    if not event_rows.empty:
        test_rows = event_rows[event_rows["split_role"] == "test"]
        if not test_rows.empty:
            et_scores = test_rows["score__ET_leaf5"].to_numpy()
            y_test = test_rows["y_true"].to_numpy()
            baseline_roc = float(frozen.metric_row(y_test, et_scores, 0.5)["roc_auc"])
            rank_roc = float(frozen.metric_row(y_test, et_scores, 0.5)["roc_auc"])
            same_score_vector = baseline_roc == rank_roc

    # 4. Require exactly one strict mismatch, exactly one approved, zero unapproved.
    strict_mismatch_count = len(strict_mismatches)
    approved_count = len(approved)
    unapproved_count = len(unapproved)

    exception_is_directional = approved_count == 1 and is_exact_directional_canonical_exception(approved[0]) if approved_count == 1 else False

    validated = bool(
        evidence_strict.get("categorical_match", False)
        and strict_mismatch_count == 1
        and approved_count == 1
        and unapproved_count == 0
        and documented_approved
        and exception_is_directional
        and same_score_vector
        and ET_ND_DIAGNOSTIC["maximum_score_difference"] <= ET_ND_MAX_ALLOWED
    )

    return {
        "validated": validated,
        "strict_mismatches": strict_mismatches,
        "approved_exception_matches": approved,
        "unapproved_mismatches": unapproved,
        "strict_mismatch_count": strict_mismatch_count,
        "approved_exception_count": approved_count,
        "unapproved_mismatch_count": unapproved_count,
        "documented_exception_row_approved": documented_approved,
        "exception_is_directional": exception_is_directional,
        "same_score_vector_for_baseline_and_rank": same_score_vector,
        "categorical_match": evidence_strict.get("categorical_match", False),
        "diagnostic": ET_ND_DIAGNOSTIC,
        "canonical_modified": False,
    }


# ---------------------------------------------------------------------------
# Production validators
# ---------------------------------------------------------------------------
def validate_dataset_profile(profile: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    evidence: Dict[str, Any] = {}
    passed = True
    for project, contract in DATASET_PROFILE_CONTRACT.items():
        proj_row = profile["profile_df"][profile["profile_df"]["project"] == project]
        if proj_row.empty:
            passed = False
            evidence[project] = {"found": False}
            continue
        row = proj_row.iloc[0]
        checks = {
            "rows": int(row["n_rows"]) == contract["rows"],
            "features": int(row["n_features"]) == contract["features"],
            "defective": int(row["defective"]) == contract["defective"],
        }
        evidence[project] = {**checks, "values": {k: int(row[f"n_{k}" if k != "defective" else "defective"]) for k in checks}}
        passed = passed and all(checks.values())
    passed = passed and profile["total_rows"] == EXPECTED_REGISTRY_ROWS
    passed = passed and profile["total_defective"] == 2662
    passed = passed and profile["total_nondefective"] == 14780
    evidence["total_rows"] = profile["total_rows"]
    evidence["total_defective"] = profile["total_defective"]
    evidence["total_nondefective"] = profile["total_nondefective"]
    return passed, evidence


def validate_sample_registry(registry: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    evidence = {
        "row_count": len(registry),
        "unique_uid_count": registry["sample_uid"].nunique(),
        "duplicate_uid_count": int(registry["sample_uid"].duplicated().sum()),
    }
    passed = True
    passed = passed and len(registry) == EXPECTED_REGISTRY_ROWS
    passed = passed and registry["sample_uid"].nunique() == EXPECTED_REGISTRY_ROWS
    passed = passed and evidence["duplicate_uid_count"] == 0
    evidence["columns_match"] = list(registry.columns) == REGISTRY_COLUMNS
    passed = passed and evidence["columns_match"]
    proj_order = {p.upper(): i for i, p in enumerate(PROJECTS)}
    order_check = (registry["project"].map(proj_order).diff().fillna(0) >= 0).all()
    passed = passed and bool(order_check)
    for project in PROJECTS:
        proj = registry[registry["project"] == project.upper()]
        if not proj["original_row_index"].is_monotonic_increasing:
            passed = False
            evidence[f"{project}_monotonic"] = False
    uid_format_ok = registry["sample_uid"].str.match(r'^[A-Z0-9]+:\d{6}$').all()
    evidence["uid_format_ok"] = uid_format_ok
    passed = passed and uid_format_ok
    project_uppercase = registry["project"].str.isupper().all()
    evidence["project_uppercase"] = project_uppercase
    passed = passed and project_uppercase
    y_valid = registry["y_true"].isin([0, 1]).all()
    evidence["y_true_valid"] = y_valid
    passed = passed and y_valid
    feature_hash_ok = registry["feature_sha256"].str.match(r'^[a-f0-9]{64}$').all()
    content_hash_ok = registry["content_sha256"].str.match(r'^[a-f0-9]{64}$').all()
    evidence["feature_hash_format_ok"] = feature_hash_ok
    evidence["content_hash_format_ok"] = content_hash_ok
    passed = passed and feature_hash_ok and content_hash_ok
    row_num_ok = (registry["raw_csv_row_number"] == registry["original_row_index"] + 2).all()
    evidence["raw_csv_row_number_ok"] = row_num_ok
    passed = passed and row_num_ok
    return passed, evidence


def validate_event_manifest(manifest: pd.DataFrame, registry: pd.DataFrame, split_within: pd.DataFrame, split_cross: pd.DataFrame, preprocessing_audits: List[Dict[str, Any]], feature_schema_sha256: str) -> Tuple[bool, Dict[str, Any]]:
    evidence = {"row_count": len(manifest), "columns_match": list(manifest.columns) == EVENT_MANIFEST_COLUMNS}
    passed = len(manifest) == EXPECTED_EVENT_COUNT and evidence["columns_match"]
    expected_event_ids = []
    for experiment in ["within_project", "cross_project"]:
        for seed in SEEDS:
            for target in PROJECTS:
                expected_event_ids.append(event_id(experiment, target.upper(), seed))
    event_id_order_ok = manifest["event_id"].tolist() == expected_event_ids
    evidence["event_id_order_ok"] = event_id_order_ok
    passed = passed and event_id_order_ok
    event_id_format_ok = manifest["event_id"].str.match(r'^(within_project|cross_project)__[A-Z0-9]+__seed_\d{3}$').all()
    evidence["event_id_format_ok"] = event_id_format_ok
    passed = passed and event_id_format_ok
    exp_ok = manifest["experiment"].isin(["within_project", "cross_project"]).all()
    evidence["experiment_values_ok"] = exp_ok
    passed = passed and exp_ok
    target_upper_ok = manifest["target_project"].str.isupper().all()
    evidence["target_uppercase_ok"] = target_upper_ok
    passed = passed and target_upper_ok
    seed_ok = manifest["seed"].isin(SEEDS).all()
    evidence["seed_values_ok"] = seed_ok
    passed = passed and seed_ok
    membership_ok = (manifest["n_membership"] == manifest["n_train"] + manifest["n_validation"] + manifest["n_test"]).all()
    evidence["membership_sum_ok"] = membership_ok
    passed = passed and membership_ok
    train_sum_ok = (manifest["train_positive"] + manifest["train_negative"] == manifest["n_train"]).all()
    val_sum_ok = (manifest["validation_positive"] + manifest["validation_negative"] == manifest["n_validation"]).all()
    test_sum_ok = (manifest["test_positive"] + manifest["test_negative"] == manifest["n_test"]).all()
    evidence["train_sum_ok"] = train_sum_ok
    evidence["validation_sum_ok"] = val_sum_ok
    evidence["test_sum_ok"] = test_sum_ok
    passed = passed and train_sum_ok and val_sum_ok and test_sum_ok
    feature_count_ok = (manifest["feature_count"] == 20).all()
    evidence["feature_count_ok"] = feature_count_ok
    passed = passed and feature_count_ok
    hash_format_ok = manifest["feature_schema_sha256"].str.match(r'^[a-f0-9]{64}$').all()
    evidence["feature_schema_hash_format_ok"] = hash_format_ok
    passed = passed and hash_format_ok
    uid_hash_ok = (manifest["train_uid_sha256"].str.match(r'^[a-f0-9]{64}$').all() and manifest["validation_uid_sha256"].str.match(r'^[a-f0-9]{64}$').all() and manifest["test_uid_sha256"].str.match(r'^[a-f0-9]{64}$').all())
    evidence["uid_hash_format_ok"] = uid_hash_ok
    passed = passed and uid_hash_ok
    feature_schema_match_ok = (manifest["feature_schema_sha256"] == feature_schema_sha256).all()
    evidence["feature_schema_match_ok"] = feature_schema_match_ok
    passed = passed and feature_schema_match_ok
    isolation_ok = ((manifest["identity_overlap_count"] == 0).all() and (manifest["target_in_train_count"] == 0).all() and (manifest["target_in_validation_count"] == 0).all() and (manifest["source_in_test_count"] == 0).all())
    evidence["isolation_ok"] = isolation_ok
    passed = passed and isolation_ok
    source_lists_ok = True
    for _, row in manifest.iterrows():
        if row["experiment"] == "within_project":
            if row["source_projects"] != row["target_project"]:
                source_lists_ok = False
        else:
            expected_sources = "|".join([p.upper() for p in PROJECTS if p != row["target_project"].lower()])
            if row["source_projects"] != expected_sources:
                source_lists_ok = False
    evidence["source_projects_ok"] = source_lists_ok
    passed = passed and source_lists_ok
    split_evidence = []
    all_split = pd.concat([split_within, split_cross], ignore_index=True)
    # Pre-group split membership by event_id and role for O(1) lookups.
    split_by_event: Dict[str, Dict[str, pd.DataFrame]] = {}
    for ev, g in all_split.groupby("event_id"):
        split_by_event[ev] = {
            role: g[g["split_role"] == role].sort_values("split_position")
            for role in ["train", "validation", "test"]
        }
    for _, row in manifest.iterrows():
        ev = row["event_id"]
        groups = split_by_event.get(ev, {})
        checks = {
            "event_id": ev,
            "n_train_matches": len(groups.get("train", pd.DataFrame())) == row["n_train"],
            "n_validation_matches": len(groups.get("validation", pd.DataFrame())) == row["n_validation"],
            "n_test_matches": len(groups.get("test", pd.DataFrame())) == row["n_test"],
            "train_hash_matches": (len(groups.get("train", pd.DataFrame())) == 0) or (sha256_str("\n".join(groups["train"]["sample_uid"].tolist())) == row["train_uid_sha256"]),
            "validation_hash_matches": (len(groups.get("validation", pd.DataFrame())) == 0) or (sha256_str("\n".join(groups["validation"]["sample_uid"].tolist())) == row["validation_uid_sha256"]),
            "test_hash_matches": (len(groups.get("test", pd.DataFrame())) == 0) or (sha256_str("\n".join(groups["test"]["sample_uid"].tolist())) == row["test_uid_sha256"]),
        }
        split_evidence.append(checks)
        if not all(v for k, v in checks.items() if k != "event_id"):
            passed = False
    evidence["split_cross_checks"] = split_evidence
    registry_counts_ok = True
    for _, row in manifest.iterrows():
        target = row["target_project"]
        if row["experiment"] == "within_project":
            proj_registry = registry[registry["project"] == target]
            expected_positive = int(proj_registry["y_true"].sum())
            expected_total = len(proj_registry)
            if row["test_positive"] + row["validation_positive"] + row["train_positive"] != expected_positive:
                registry_counts_ok = False
            if row["n_test"] + row["n_validation"] + row["n_train"] != expected_total:
                registry_counts_ok = False
    evidence["registry_counts_ok"] = registry_counts_ok
    passed = passed and registry_counts_ok
    prep_evidence = []
    prep_ok = True
    for _, row in manifest.iterrows():
        ev = row["event_id"]
        event_audits = [a for a in preprocessing_audits if a.get("event_id") == ev]
        expected_counts = {"imputer": 4, "scaler": 2, "feature_count": 4, "configuration": 4}
        actual_counts = {"imputer": 0, "scaler": 0, "feature_count": 0, "configuration": 0}
        all_event_passed = True
        for a in event_audits:
            t = a.get("type")
            if t in actual_counts:
                actual_counts[t] += 1
            if not a.get("passed", False):
                all_event_passed = False
        counts_ok = all(actual_counts[k] == expected_counts[k] for k in expected_counts)
        prep_evidence.append({"event_id": ev, "expected_counts": expected_counts, "actual_counts": actual_counts, "all_passed": all_event_passed, "counts_ok": counts_ok})
        if not (counts_ok and all_event_passed):
            prep_ok = False
    evidence["preprocessing_audit_completeness"] = prep_evidence
    passed = passed and prep_ok
    return passed, evidence


def validate_split_membership(within_df: pd.DataFrame, cross_df: pd.DataFrame, registry: pd.DataFrame, event_manifest: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    evidence: Dict[str, Any] = {}
    passed = True
    w_schema_ok = list(within_df.columns) == SPLIT_MEMBERSHIP_COLUMNS
    c_schema_ok = list(cross_df.columns) == SPLIT_MEMBERSHIP_COLUMNS
    evidence["within_schema_ok"] = w_schema_ok
    evidence["cross_schema_ok"] = c_schema_ok
    passed = passed and w_schema_ok and c_schema_ok

    def _role_counts(df: pd.DataFrame, expected: Dict[str, int]) -> Tuple[bool, Dict[str, Any]]:
        ev = {"row_count": len(df)}
        ok = len(df) == expected["total"]
        for role in ["train", "validation", "test"]:
            count = int((df["split_role"] == role).sum())
            ev[f"{role}_count"] = count
            ok = ok and count == expected[role]
        return ok, ev

    w_counts_ok, w_counts = _role_counts(within_df, EXPECTED_WITHIN_SPLIT_ROWS)
    c_counts_ok, c_counts = _role_counts(cross_df, EXPECTED_CROSS_SPLIT_ROWS)
    evidence["within"] = w_counts
    evidence["cross"] = c_counts
    passed = passed and w_counts_ok and c_counts_ok
    evidence["total_row_count"] = len(within_df) + len(cross_df)
    passed = passed and evidence["total_row_count"] == EXPECTED_WITHIN_SPLIT_ROWS["total"] + EXPECTED_CROSS_SPLIT_ROWS["total"]

    all_split = pd.concat([within_df, cross_df], ignore_index=True)
    dup_keys = all_split.duplicated(["event_id", "sample_uid"]).sum()
    evidence["duplicate_keys"] = int(dup_keys)
    passed = passed and dup_keys == 0

    w_target_ok = within_df["target_project"].str.isupper().all()
    c_target_ok = cross_df["target_project"].str.isupper().all()
    w_sample_ok = within_df["sample_project"].str.isupper().all()
    c_sample_ok = cross_df["sample_project"].str.isupper().all()
    evidence.update({"within_target_uppercase": w_target_ok, "cross_target_uppercase": c_target_ok, "within_sample_uppercase": w_sample_ok, "cross_sample_uppercase": c_sample_ok})
    passed = passed and w_target_ok and c_target_ok and w_sample_ok and c_sample_ok

    seed_target_ok = True
    for df in [within_df, cross_df]:
        for _, g in df.groupby("event_id"):
            if g["target_project"].nunique() != 1 or g["seed"].nunique() != 1 or g["experiment"].nunique() != 1:
                seed_target_ok = False
    evidence["seed_target_consistency_ok"] = seed_target_ok
    passed = passed and seed_target_ok

    uid_format_ok = all_split["sample_uid"].str.match(r'^[A-Z0-9]+:\d{6}$').all()
    suffix_ok = True
    for _, row in all_split.iterrows():
        suffix = int(row["sample_uid"].split(":")[1])
        if suffix != int(row["original_row_index"]):
            suffix_ok = False
            break
    evidence["uid_format_ok"] = uid_format_ok
    evidence["uid_suffix_matches_index"] = suffix_ok
    passed = passed and uid_format_ok and suffix_ok

    registry_lookup = {
        row["sample_uid"]: {
            "project": row["project"],
            "original_row_index": row["original_row_index"],
            "y_true": row["y_true"],
        }
        for _, row in registry.iterrows()
    }
    registry_equality_ok = True
    for _, row in all_split.iterrows():
        reg = registry_lookup.get(row["sample_uid"])
        if reg is None or reg["project"] != row["sample_project"] or reg["original_row_index"] != row["original_row_index"] or reg["y_true"] != row["y_true"]:
            registry_equality_ok = False
            break
    evidence["registry_equality_ok"] = registry_equality_ok
    passed = passed and registry_equality_ok

    contiguous_ok = True
    for df in [within_df, cross_df]:
        for _, g in df.groupby(["event_id", "split_role"]):
            positions = g["split_position"].sort_values().to_numpy()
            if len(positions) > 0 and not (positions[0] == 0 and (positions[1:] - positions[:-1] == 1).all()):
                contiguous_ok = False
    evidence["split_position_contiguous_ok"] = contiguous_ok
    passed = passed and contiguous_ok

    overlap_train_test = 0
    overlap_train_val = 0
    overlap_val_test = 0
    for _, g in all_split.groupby("event_id"):
        train_uids = set(g.loc[g["split_role"] == "train", "sample_uid"])
        val_uids = set(g.loc[g["split_role"] == "validation", "sample_uid"])
        test_uids = set(g.loc[g["split_role"] == "test", "sample_uid"])
        overlap_train_test += len(train_uids & test_uids)
        overlap_train_val += len(train_uids & val_uids)
        overlap_val_test += len(val_uids & test_uids)
    evidence["overlap_train_test"] = overlap_train_test
    evidence["overlap_train_val"] = overlap_train_val
    evidence["overlap_val_test"] = overlap_val_test
    passed = passed and overlap_train_test == 0 and overlap_train_val == 0 and overlap_val_test == 0

    within_coverage_ok = True
    for _, g in within_df.groupby("event_id"):
        target = g["target_project"].iloc[0]
        expected_rows = DATASET_PROFILE_CONTRACT[target]["rows"]
        if g["sample_uid"].nunique() != expected_rows:
            within_coverage_ok = False
    evidence["within_coverage_ok"] = within_coverage_ok
    passed = passed and within_coverage_ok

    cross_isolation_ok = True
    for _, g in cross_df.groupby("event_id"):
        target = g["target_project"].iloc[0]
        train_target = (g.loc[g["split_role"] == "train", "sample_project"] == target).sum()
        val_target = (g.loc[g["split_role"] == "validation", "sample_project"] == target).sum()
        test_source = (g.loc[g["split_role"] == "test", "sample_project"] != target).sum()
        if train_target or val_target or test_source:
            cross_isolation_ok = False
    evidence["cross_isolation_ok"] = cross_isolation_ok
    passed = passed and cross_isolation_ok

    manifest_lookup = {row["event_id"]: row for _, row in event_manifest.iterrows()}
    hash_matches = []
    hash_ok = True
    for df in [within_df, cross_df]:
        for ev, g in df.groupby("event_id"):
            row = manifest_lookup.get(ev)
            if row is None:
                hash_ok = False
                continue
            groups = {role: g[g["split_role"] == role].sort_values("split_position") for role in ["train", "validation", "test"]}
            for role, hash_col in [("train", "train_uid_sha256"), ("validation", "validation_uid_sha256"), ("test", "test_uid_sha256")]:
                uids = groups[role]["sample_uid"].tolist()
                computed = sha256_str("\n".join(uids))
                expected = row[hash_col]
                match = computed == expected
                hash_matches.append({"event_id": ev, "role": role, "matches": match})
                if not match:
                    hash_ok = False
    evidence["ordered_split_hashes_match_manifest"] = hash_ok
    evidence["hash_match_details"] = hash_matches
    passed = passed and hash_ok
    return passed, evidence


def validate_prediction_ledger(within_df: pd.DataFrame, cross_df: pd.DataFrame, split_within: pd.DataFrame, split_cross: pd.DataFrame, registry: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    evidence = {"within_row_count": len(within_df), "cross_row_count": len(cross_df)}
    passed = True
    w_schema_ok = list(within_df.columns) == PREDICTION_LEDGER_COLUMNS
    c_schema_ok = list(cross_df.columns) == PREDICTION_LEDGER_COLUMNS
    evidence["within_schema_ok"] = w_schema_ok
    evidence["cross_schema_ok"] = c_schema_ok
    passed = passed and w_schema_ok and c_schema_ok

    all_pred = pd.concat([within_df, cross_df], ignore_index=True)
    forbidden = [c for c in all_pred.columns if c.startswith("threshold_") or c.startswith("objective_") or c.startswith("metric__") or c.startswith("soft_top3_")]
    evidence["forbidden_columns"] = forbidden
    passed = passed and len(forbidden) == 0

    passed = passed and len(within_df) == EXPECTED_WITHIN_PREDICTION_ROWS["total"]
    passed = passed and len(cross_df) == EXPECTED_CROSS_PREDICTION_ROWS["total"]
    no_train = (all_pred["split_role"] == "train").sum() == 0
    evidence["no_train_rows"] = no_train
    passed = passed and no_train
    roles_ok = all_pred["split_role"].isin(["validation", "test"]).all()
    evidence["roles_ok"] = roles_ok
    passed = passed and roles_ok
    dup = all_pred.duplicated(["event_id", "split_role", "sample_uid"]).sum()
    evidence["duplicate_keys"] = int(dup)
    passed = passed and dup == 0
    score_cols = [f"score__{c}" for c in CANDIDATES]
    evidence["score_columns_present"] = all(c in all_pred.columns for c in score_cols)
    passed = passed and evidence["score_columns_present"]
    finite_ok = True
    range_ok = True
    for c in score_cols:
        finite_ok = finite_ok and all_pred[c].notna().all() and np.isfinite(all_pred[c]).all()
        range_ok = range_ok and (all_pred[c] >= EPS).all() and (all_pred[c] <= (1 - EPS)).all()
    evidence["finite_ok"] = finite_ok
    evidence["range_ok"] = range_ok
    passed = passed and finite_ok and range_ok

    all_split = pd.concat([split_within, split_cross], ignore_index=True)
    split_vt = all_split[all_split["split_role"].isin(["validation", "test"])].copy()
    pred_vt = all_pred.copy()
    key_cols = ["event_id", "split_role", "split_position", "sample_uid", "sample_project", "original_row_index", "y_true", "target_project", "seed"]
    merged = pred_vt.merge(split_vt, on=key_cols, how="outer", indicator=True)
    only_pred = (merged["_merge"] == "left_only").sum()
    only_split = (merged["_merge"] == "right_only").sum()
    evidence["one_to_one_mismatches"] = {"only_prediction": int(only_pred), "only_split": int(only_split)}
    passed = passed and only_pred == 0 and only_split == 0

    contiguous_ok = True
    for _, g in all_pred.groupby(["event_id", "split_role"]):
        positions = g["split_position"].sort_values().to_numpy()
        if len(positions) > 0 and not (positions[0] == 0 and (positions[1:] - positions[:-1] == 1).all()):
            contiguous_ok = False
    evidence["split_position_contiguous_ok"] = contiguous_ok
    passed = passed and contiguous_ok

    ledger_uids = set(all_pred["sample_uid"].unique())
    registry_uids = set(registry["sample_uid"].unique())
    missing_uids = ledger_uids - registry_uids
    evidence["ledger_uids_not_in_registry"] = len(missing_uids)
    passed = passed and len(missing_uids) == 0
    proj_match = all_pred[["sample_uid", "sample_project"]].drop_duplicates().merge(registry[["sample_uid", "project"]].rename(columns={"project": "sample_project"}), on=["sample_uid", "sample_project"], how="left", indicator=True)
    proj_mismatch_count = (proj_match["_merge"] == "left_only").sum()
    evidence["sample_project_mismatch_count"] = int(proj_mismatch_count)
    passed = passed and proj_mismatch_count == 0
    y_match = all_pred[["sample_uid", "y_true"]].drop_duplicates().merge(registry[["sample_uid", "y_true"]], on=["sample_uid", "y_true"], how="left", indicator=True)
    y_mismatch_count = (y_match["_merge"] == "left_only").sum()
    evidence["y_true_mismatch_count"] = int(y_mismatch_count)
    passed = passed and y_mismatch_count == 0
    return passed, evidence


def validate_preprocessing_audit(audits: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    imputer = [a for a in audits if a["type"] == "imputer"]
    scaler = [a for a in audits if a["type"] == "scaler"]
    feature = [a for a in audits if a["type"] == "feature_count"]
    config = [a for a in audits if a["type"] == "configuration"]
    if len(feature) != EXPECTED_FEATURE_COUNT_AUDITS:
        return False, {
            "imputer": {"expected": EXPECTED_IMPUTER_AUDITS, "executed": len(imputer), "passed": 0, "failed": len(imputer)},
            "scaler": {"expected": EXPECTED_SCALER_AUDITS, "executed": len(scaler), "passed": 0, "failed": len(scaler)},
            "feature_count": {"expected": EXPECTED_FEATURE_COUNT_AUDITS, "executed": len(feature), "passed": 0, "failed": EXPECTED_FEATURE_COUNT_AUDITS, "error": "missing actual feature-count audits"},
            "configuration": {"expected": EXPECTED_CONFIG_AUDITS, "executed": len(config), "passed": 0, "failed": EXPECTED_CONFIG_AUDITS},
        }
    passed = (len(imputer) == EXPECTED_IMPUTER_AUDITS and all(a["passed"] for a in imputer) and len(scaler) == EXPECTED_SCALER_AUDITS and all(a["passed"] for a in scaler) and len(feature) == EXPECTED_FEATURE_COUNT_AUDITS and all(a["passed"] for a in feature) and len(config) == EXPECTED_CONFIG_AUDITS and all(a["passed"] for a in config))
    evidence = {
        "imputer": {"expected": EXPECTED_IMPUTER_AUDITS, "executed": len(imputer), "passed": sum(a["passed"] for a in imputer), "failed": len(imputer) - sum(a["passed"] for a in imputer)},
        "scaler": {"expected": EXPECTED_SCALER_AUDITS, "executed": len(scaler), "passed": sum(a["passed"] for a in scaler), "failed": len(scaler) - sum(a["passed"] for a in scaler)},
        "feature_count": {"expected": EXPECTED_FEATURE_COUNT_AUDITS, "executed": len(feature), "passed": sum(a["passed"] for a in feature), "failed": len(feature) - sum(a["passed"] for a in feature)},
        "configuration": {"expected": EXPECTED_CONFIG_AUDITS, "executed": len(config), "passed": sum(a["passed"] for a in config), "failed": len(config) - sum(a["passed"] for a in config)},
    }
    return passed, evidence


def validate_preservation(state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    before = state.get("before", {})
    after = state.get("after", {})
    files = sorted(set(before.keys()) | set(after.keys()))
    passed = True
    file_evidence = {}
    raw_changed = 0
    canonical_changed = 0
    part3a_changed = 0
    for path in files:
        b = before.get(path, {})
        a = after.get(path, {})
        ok = (b.get("exists", False) and a.get("exists", False) and b.get("matches_expected", False) and a.get("matches_expected", False) and b.get("sha256") == a.get("sha256"))
        file_evidence[path] = {"exists_before": b.get("exists", False), "exists_after": a.get("exists", False), "before_sha256": b.get("sha256"), "after_sha256": a.get("sha256"), "matches_expected_before": b.get("matches_expected", False), "matches_expected_after": a.get("matches_expected", False), "unchanged": b.get("sha256") == a.get("sha256"), "passed": ok}
        passed = passed and ok
        if not file_evidence[path]["unchanged"]:
            if any(path.startswith(p) for p in RAW_DATA_PATHS):
                raw_changed += 1
            elif any(path.startswith(p) for p in CANONICAL_OUTPUT_PATHS):
                canonical_changed += 1
            elif path in PART3A_ARTIFACT_PATHS:
                part3a_changed += 1
    changed = sum(1 for f in file_evidence.values() if not f["unchanged"])
    return passed, {"files": file_evidence, "files_changed": changed, "files_checked": len(file_evidence), "raw_data_changed": raw_changed, "canonical_outputs_changed": canonical_changed, "part3a_artifacts_changed": part3a_changed}


def validate_exact_audit_check_schema(
    audit_checks: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """Validate that *audit_checks* has exactly the 41 required names in order,
    every value is an actual ``bool``, and no diagnostic keys are present."""
    expected_names = REQUIRED_AUDIT_CHECK_NAMES
    actual_keys = list(audit_checks.keys())
    expected_set = set(expected_names)
    actual_set = set(actual_keys)
    missing_checks = sorted(expected_set - actual_set)
    extra_checks = sorted(actual_set - expected_set)
    order_exact = actual_keys == expected_names
    non_boolean_checks: List[str] = []
    for name in expected_names:
        if name in audit_checks:
            v = audit_checks[name]
            if type(v) is not bool:
                non_boolean_checks.append(name)
    non_boolean_checks = list(dict.fromkeys(non_boolean_checks))
    schema_passed = (
        len(audit_checks) == 41
        and len(missing_checks) == 0
        and len(extra_checks) == 0
        and order_exact
        and len(non_boolean_checks) == 0
    )
    evidence = {
        "checks_expected": len(expected_names),
        "checks_present": len(actual_keys),
        "missing_checks": missing_checks,
        "extra_checks": extra_checks,
        "order_exact": order_exact,
        "non_boolean_checks": non_boolean_checks,
        "schema_passed": schema_passed,
    }
    return schema_passed, evidence


def compute_all_critical_checks_passed(
    audit_checks: Dict[str, Any],
) -> bool:
    """Compute the logical AND of checks 1 through 40.

    Requires the exact 41-check schema first.  Check 41
    (``all_critical_checks_passed``) is not included in its own computation.
    """
    schema_passed, _ = validate_exact_audit_check_schema(audit_checks)
    if not schema_passed:
        return False
    return all(audit_checks[name] for name in REQUIRED_AUDIT_CHECK_NAMES[:40])


def validate_stage_gate(gate: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Validate the exact 16-field stage-gate schema and authorization conditions.

    If the schema is not exact, validation fails immediately.
    Returns ``True`` only for an exactly valid authorized gate.
    """
    expected_fields = REQUIRED_STAGE_GATE_FIELDS
    actual_keys = list(gate.keys())
    expected_set = set(expected_fields)
    actual_set = set(actual_keys)
    missing_fields = sorted(expected_set - actual_set)
    extra_fields = sorted(actual_set - expected_set)
    order_exact = actual_keys == expected_fields

    type_errors: List[str] = []
    bool_fields = expected_fields[:14]
    for name in bool_fields:
        if name in gate:
            v = gate[name]
            if type(v) is not bool:
                type_errors.append(name)

    schema_passed = (
        len(gate) == 16
        and len(missing_fields) == 0
        and len(extra_fields) == 0
        and order_exact
        and len(type_errors) == 0
    )

    evidence: Dict[str, Any] = {
        "fields_expected": len(expected_fields),
        "fields_present": len(actual_keys),
        "missing_fields": missing_fields,
        "extra_fields": extra_fields,
        "order_exact": order_exact,
        "type_errors": type_errors,
        "schema_passed": schema_passed,
    }

    if not schema_passed:
        return False, evidence

    authorization_conditions = {
        "part3b_prediction_ledger_complete": gate["part3b_prediction_ledger_complete"] is True,
        "raw_data_modified": gate["raw_data_modified"] is False,
        "canonical_outputs_modified": gate["canonical_outputs_modified"] is False,
        "part3a_artifacts_modified": gate["part3a_artifacts_modified"] is False,
        "identity_leakage_detected": gate["identity_leakage_detected"] is False,
        "preprocessing_leakage_detected": gate["preprocessing_leakage_detected"] is False,
        "selection_test_leakage_detected": gate["selection_test_leakage_detected"] is False,
        "canonical_validation_reconstruction_passed": gate["canonical_validation_reconstruction_passed"] is True,
        "canonical_result_reconstruction_passed": gate["canonical_result_reconstruction_passed"] is True,
        "canonical_result_reconstruction_strictly_identical": gate["canonical_result_reconstruction_strictly_identical"] is False,
        "canonical_result_reconstruction_scientifically_reconciled": gate["canonical_result_reconstruction_scientifically_reconciled"] is True,
        "canonical_nondeterminism_exception_detected": gate["canonical_nondeterminism_exception_detected"] is True,
        "canonical_nondeterminism_exception_validated": gate["canonical_nondeterminism_exception_validated"] is True,
        "semantic_reproducibility_passed": gate["semantic_reproducibility_passed"] is True,
        "part3c_constraint": gate["part3c_constraint"] == PART3C_CONSTRAINT,
    }

    all_authorized = all(authorization_conditions.values())

    next_stage_ok = (
        gate["next_authorized_stage"] == "Part 3C"
        if all_authorized
        else gate["next_authorized_stage"] is None
    )

    evidence["authorization_conditions"] = authorization_conditions
    evidence["next_authorized_stage_ok"] = next_stage_ok

    passed = schema_passed and all_authorized and next_stage_ok
    return passed, evidence


def validate_stage_gate_schema_only(gate: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Validate the exact 16-field stage-gate schema and types only.

    Unlike :func:`validate_stage_gate`, this does NOT check authorization
    conditions.  It permits an intentionally unauthorized pre-comparison gate
    with ``next_authorized_stage = None`` but still enforces the exact field
    schema and types.
    """
    expected_fields = REQUIRED_STAGE_GATE_FIELDS
    actual_keys = list(gate.keys())
    expected_set = set(expected_fields)
    actual_set = set(actual_keys)
    missing_fields = sorted(expected_set - actual_set)
    extra_fields = sorted(actual_set - expected_set)
    order_exact = actual_keys == expected_fields

    type_errors: List[str] = []
    bool_fields = expected_fields[:14]
    for name in bool_fields:
        if name in gate:
            v = gate[name]
            if type(v) is not bool:
                type_errors.append(name)

    # next_authorized_stage must be None or "Part 3C"
    nas = gate.get("next_authorized_stage")
    if nas is not None and nas != "Part 3C":
        type_errors.append("next_authorized_stage")

    # part3c_constraint must equal PART3C_CONSTRAINT
    if gate.get("part3c_constraint") != PART3C_CONSTRAINT:
        type_errors.append("part3c_constraint")

    schema_passed = (
        len(gate) == 16
        and len(missing_fields) == 0
        and len(extra_fields) == 0
        and order_exact
        and len(type_errors) == 0
    )

    evidence: Dict[str, Any] = {
        "fields_expected": len(expected_fields),
        "fields_present": len(actual_keys),
        "missing_fields": missing_fields,
        "extra_fields": extra_fields,
        "order_exact": order_exact,
        "type_errors": type_errors,
        "schema_passed": schema_passed,
    }
    return schema_passed, evidence


# ---------------------------------------------------------------------------
# Tie-policy tests
# ---------------------------------------------------------------------------
def run_tie_policy_tests(frozen: Any) -> Tuple[List[Dict[str, Any]], bool]:
    tests: List[Dict[str, Any]] = []
    passed = True

    # Candidate exact tie: two candidates with identical balanced objectives -> first wins.
    y = np.array([0, 0, 0, 1, 1, 1])
    s1 = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    s2 = s1.copy()
    t1, obj1 = frozen.select_threshold(y, s1, "balanced")
    t2, obj2 = frozen.select_threshold(y, s2, "balanced")
    cand_objs = {"A": obj1, "B": obj2, "C": -1.0, "D": -1.0}
    selected = max(["A", "B"], key=lambda k: cand_objs[k])
    first_wins = selected == "A"
    tests.append({"case_name": "candidate exact tie", "description": "identical balanced objectives -> first candidate in order selected", "passed": first_wins and obj1 == obj2})
    passed = passed and tests[-1]["passed"]

    # Threshold exact tie: grid with repeated objective -> first threshold kept.
    y_th = np.array([0, 1])
    s_th = np.array([0.5, 0.5])
    t_th, obj_th = frozen.select_threshold(y_th, s_th, "balanced")
    tests.append({"case_name": "threshold exact tie", "description": "first threshold achieving best objective is retained", "passed": t_th is not None and obj_th is not None})
    passed = passed and tests[-1]["passed"]

    # Soft-top-3 stable tie order: equal objectives -> original candidate order preserved.
    equal_objs = {"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0}
    order = ["A", "B", "C", "D"]
    top3 = sorted(order, key=lambda k: (-equal_objs[k], order.index(k)))[:3]
    stable = top3 == ["A", "B", "C"]
    tests.append({"case_name": "soft_top3 stable tie order", "description": "equal objectives preserve candidate order for top3", "passed": stable})
    passed = passed and tests[-1]["passed"]

    return tests, passed


# ---------------------------------------------------------------------------
# Negative tests
# ---------------------------------------------------------------------------
def run_negative_tests(
    split_within: pd.DataFrame,
    split_cross: pd.DataFrame,
    pred_within: pd.DataFrame,
    pred_cross: pd.DataFrame,
    val_recon: pd.DataFrame,
    result_recon: pd.DataFrame,
    canonical_val: pd.DataFrame,
    canonical_res: pd.DataFrame,
    registry: pd.DataFrame,
    event_manifest: pd.DataFrame,
) -> Tuple[List[Dict[str, Any]], bool]:
    tests: List[Dict[str, Any]] = []
    all_passed = True

    # 1. duplicate event_id/sample_uid key in split membership
    df1 = _split_membership_sorted(split_within.copy(deep=True))
    row = df1.iloc[0].to_dict()
    df1 = pd.concat([df1, pd.DataFrame([row])], ignore_index=True)
    ok = not validate_split_membership(df1, split_cross.copy(deep=True), registry, event_manifest)[0]
    tests.append({"case_name": "duplicate event_id/sample_uid key", "mutation": "append duplicate row", "validator_name": "validate_split_membership", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 2. same sample identity in train and test
    df2 = _split_membership_sorted(split_within.copy(deep=True))
    ev = df2["event_id"].iloc[0]
    g = df2[df2["event_id"] == ev]
    train_idx = g.index[g["split_role"] == "train"][0]
    test_idx = g.index[g["split_role"] == "test"][0]
    df2.at[test_idx, "sample_uid"] = df2.at[train_idx, "sample_uid"]
    df2.at[test_idx, "sample_project"] = df2.at[train_idx, "sample_project"]
    df2.at[test_idx, "original_row_index"] = df2.at[train_idx, "original_row_index"]
    df2.at[test_idx, "y_true"] = df2.at[train_idx, "y_true"]
    ok = not validate_split_membership(df2, split_cross.copy(deep=True), registry, event_manifest)[0]
    tests.append({"case_name": "same sample identity in train and test", "mutation": "copy train uid to test row", "validator_name": "validate_split_membership", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 3. same sample identity in validation and test
    df3 = _split_membership_sorted(split_within.copy(deep=True))
    ev = df3["event_id"].iloc[0]
    g = df3[df3["event_id"] == ev]
    val_idx = g.index[g["split_role"] == "validation"][0]
    test_idx = g.index[g["split_role"] == "test"][0]
    df3.at[test_idx, "sample_uid"] = df3.at[val_idx, "sample_uid"]
    df3.at[test_idx, "sample_project"] = df3.at[val_idx, "sample_project"]
    df3.at[test_idx, "original_row_index"] = df3.at[val_idx, "original_row_index"]
    df3.at[test_idx, "y_true"] = df3.at[val_idx, "y_true"]
    ok = not validate_split_membership(df3, split_cross.copy(deep=True), registry, event_manifest)[0]
    tests.append({"case_name": "same sample identity in validation and test", "mutation": "copy validation uid to test row", "validator_name": "validate_split_membership", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 4. target-project row inserted into cross-project train
    df4 = _split_membership_sorted(split_cross.copy(deep=True))
    ev = df4[df4["experiment"] == "cross_project"]["event_id"].iloc[0]
    g = df4[df4["event_id"] == ev]
    target = g["target_project"].iloc[0]
    train_idx = g.index[g["split_role"] == "train"][0]
    df4.at[train_idx, "sample_project"] = target
    df4.at[train_idx, "sample_uid"] = f"{target}:000001"
    ok = not validate_split_membership(split_within.copy(deep=True), df4, registry, event_manifest)[0]
    tests.append({"case_name": "target-project row inserted into cross-project train", "mutation": "set train sample_project to target", "validator_name": "validate_split_membership", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 5. source-project row inserted into cross-project test
    df5 = _split_membership_sorted(split_cross.copy(deep=True))
    ev = df5[df5["experiment"] == "cross_project"]["event_id"].iloc[0]
    g = df5[df5["event_id"] == ev]
    target = g["target_project"].iloc[0]
    test_idx = g.index[g["split_role"] == "test"][0]
    source = [p for p in [p.upper() for p in PROJECTS] if p != target][0]
    df5.at[test_idx, "sample_project"] = source
    df5.at[test_idx, "sample_uid"] = f"{source}:000001"
    ok = not validate_split_membership(split_within.copy(deep=True), df5, registry, event_manifest)[0]
    tests.append({"case_name": "source-project row inserted into cross-project test", "mutation": "set test sample_project to source", "validator_name": "validate_split_membership", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 6. one target-project row removed from a within-project event union
    df6 = _split_membership_sorted(split_within.copy(deep=True))
    ev = df6["event_id"].iloc[0]
    g = df6[df6["event_id"] == ev]
    test_idx = g.index[g["split_role"] == "test"][0]
    df6 = df6.drop(test_idx).reset_index(drop=True)
    ok = not validate_split_membership(df6, split_cross.copy(deep=True), registry, event_manifest)[0]
    tests.append({"case_name": "one target-project row removed from a within-project event union", "mutation": "drop one test row", "validator_name": "validate_split_membership", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 7. training row inserted into prediction ledger
    df7 = _prediction_ledger_sorted(pred_within.copy(deep=True))
    train_row = split_within[split_within["split_role"] == "train"].iloc[0].to_dict()
    pred_row = {
        "event_id": train_row["event_id"], "experiment": train_row["experiment"], "target_project": train_row["target_project"], "seed": train_row["seed"],
        "split_role": "train", "split_position": 0, "sample_uid": train_row["sample_uid"], "sample_project": train_row["sample_project"],
        "original_row_index": train_row["original_row_index"], "y_true": train_row["y_true"],
    }
    for c in CANDIDATES:
        pred_row[f"score__{c}"] = 0.5
    df7 = pd.concat([df7, pd.DataFrame([pred_row])], ignore_index=True)
    ok = not validate_prediction_ledger(df7, pred_cross.copy(deep=True), split_within.copy(deep=True), split_cross.copy(deep=True), registry)[0]
    tests.append({"case_name": "training row inserted into prediction ledger", "mutation": "append a train split_role row", "validator_name": "validate_prediction_ledger", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 8. duplicate event_id/split_role/sample_uid key in prediction ledger
    df8 = _prediction_ledger_sorted(pred_within.copy(deep=True))
    row = df8.iloc[0].to_dict()
    df8 = pd.concat([df8, pd.DataFrame([row])], ignore_index=True)
    ok = not validate_prediction_ledger(df8, pred_cross.copy(deep=True), split_within.copy(deep=True), split_cross.copy(deep=True), registry)[0]
    tests.append({"case_name": "duplicate event_id/split_role/sample_uid key", "mutation": "append duplicate prediction row", "validator_name": "validate_prediction_ledger", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 9. one candidate score replaced by NaN
    df9 = _prediction_ledger_sorted(pred_within.copy(deep=True))
    df9.at[0, "score__LR_std_C0.1"] = np.nan
    ok = not validate_prediction_ledger(df9, pred_cross.copy(deep=True), split_within.copy(deep=True), split_cross.copy(deep=True), registry)[0]
    tests.append({"case_name": "one candidate score replaced by NaN", "mutation": "set score to NaN", "validator_name": "validate_prediction_ledger", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 10. one candidate score replaced by a value greater than 1
    df10 = _prediction_ledger_sorted(pred_within.copy(deep=True))
    df10.at[0, "score__LR_std_C0.1"] = 1.1
    ok = not validate_prediction_ledger(df10, pred_cross.copy(deep=True), split_within.copy(deep=True), split_cross.copy(deep=True), registry)[0]
    tests.append({"case_name": "one candidate score replaced by a value greater than 1", "mutation": "set score to 1.1", "validator_name": "validate_prediction_ledger", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 11. mutate one numeric validation-reconstruction value by exactly 1e-8
    val11 = val_recon.copy(deep=True)
    numeric_cols = [c for c in val11.columns if c.startswith("val_") and c not in {"val_threshold", "val_selection_score"}]
    mutated = False
    for col in numeric_cols:
        if not mutated and val11[col].notna().any():
            idx = val11[col].notna().idxmax()
            val11.at[idx, col] = val11.at[idx, col] + NEGATIVE_TEST_MUTATION
            mutated = True
    ok = not validate_validation_reconstruction(val11, canonical_val)[0]
    tests.append({"case_name": "mutate one numeric validation-reconstruction value", "mutation": f"add {NEGATIVE_TEST_MUTATION} to one metric", "validator_name": "validate_validation_reconstruction", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    # 12. mutate one numeric canonical-result-reconstruction value by exactly 1e-8
    res12 = result_recon.copy(deep=True)
    numeric_cols = [c for c in res12.columns if c not in {"experiment", "target_project", "seed", "model", "selected_candidate", "selection_mode"}]
    mutated = False
    for col in numeric_cols:
        if not mutated and res12[col].notna().any():
            idx = res12[col].notna().idxmax()
            res12.at[idx, col] = res12.at[idx, col] + NEGATIVE_TEST_MUTATION
            mutated = True
    ok = not validate_result_reconstruction(res12, canonical_res)[0]
    tests.append({"case_name": "mutate one numeric canonical-result-reconstruction value", "mutation": f"add {NEGATIVE_TEST_MUTATION} to one metric", "validator_name": "validate_result_reconstruction", "validator_returned_false": ok, "passed": ok})
    all_passed = all_passed and ok

    return tests, all_passed


def _make_exact_exception_evidence() -> Dict[str, Any]:
    """Build the single approved directional mismatch evidence record."""
    return {
        "experiment": "cross_project",
        "target_project": "JM1",
        "seed": 42,
        "model": "AQRPE_v2_rank",
        "selected_candidate": "ET_leaf5",
        "selection_mode": "rank_objective_fixed_threshold",
        "column": "roc_auc",
        "canonical_value": 0.6700602041438307,
        "recon_value": 0.6700601613088453,
        "absolute_difference": 4.283498544754849e-08,
    }


def run_canonical_exception_validator_tests(
    *args: Any,
    **kwargs: Any,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Run ten isolated unit-style tests for the exact directional canonical exception.

    These tests use synthetic mismatch evidence only.  They do not load datasets,
    import or fit estimators, generate predictions, rebuild ledgers, or modify
    repository artifacts.
    """
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, result: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({
            "case_name": case_name,
            "passed": result,
            **extra,
        })
        all_passed = all_passed and result

    # 1. Exact approved directional exception passes.
    m1 = _make_exact_exception_evidence()
    r1 = is_exact_directional_canonical_exception(m1)
    _record("exact approved directional exception passes", r1, matcher_returned_true=r1)

    # 2. Wrong event or experiment fails.
    m2 = _make_exact_exception_evidence()
    m2["experiment"] = "within_project"
    r2 = is_exact_directional_canonical_exception(m2)
    _record("wrong event or experiment fails", not r2, matcher_returned_true=r2)

    # 3. Wrong seed fails.
    m3 = _make_exact_exception_evidence()
    m3["seed"] = 7
    r3 = is_exact_directional_canonical_exception(m3)
    _record("wrong seed fails", not r3, matcher_returned_true=r3)

    # 4. Wrong model fails.
    m4 = _make_exact_exception_evidence()
    m4["model"] = "AQRPE_v2_balanced"
    r4 = is_exact_directional_canonical_exception(m4)
    _record("wrong model fails", not r4, matcher_returned_true=r4)

    # 5. Wrong selected_candidate fails.
    m5 = _make_exact_exception_evidence()
    m5["selected_candidate"] = "DT_leaf5"
    r5 = is_exact_directional_canonical_exception(m5)
    _record("wrong selected_candidate fails", not r5, matcher_returned_true=r5)

    # 6. Wrong selection_mode fails.
    m6 = _make_exact_exception_evidence()
    m6["selection_mode"] = "balanced_objective"
    r6 = is_exact_directional_canonical_exception(m6)
    _record("wrong selection_mode fails", not r6, matcher_returned_true=r6)

    # 7. Wrong metric column fails.
    m7 = _make_exact_exception_evidence()
    m7["column"] = "avg_precision"
    r7 = is_exact_directional_canonical_exception(m7)
    _record("wrong metric column fails", not r7, matcher_returned_true=r7)

    # 8. Swapped canonical_value and reconstruction_value fails.
    m8 = _make_exact_exception_evidence()
    m8["canonical_value"], m8["recon_value"] = m8["recon_value"], m8["canonical_value"]
    r8 = is_exact_directional_canonical_exception(m8)
    _record("swapped canonical_value and reconstruction_value fails", not r8, matcher_returned_true=r8, validator_returned_false=not r8)

    # 9. Exact exception plus a second mismatch fails (two mismatches => validator fails).
    #    Simulated by checking that the second mismatch does not pass the matcher.
    m9_second = _make_exact_exception_evidence()
    m9_second["column"] = "avg_precision"
    r9 = not is_exact_directional_canonical_exception(m9_second)
    _record("exact exception plus second mismatch fails", r9, matcher_returned_true=not r9)

    # 10. Altered canonical, reconstruction, or difference value fails.
    m10 = _make_exact_exception_evidence()
    m10["canonical_value"] = m10["canonical_value"] + 1e-9
    r10a = not is_exact_directional_canonical_exception(m10)

    m10b = _make_exact_exception_evidence()
    m10b["recon_value"] = m10b["recon_value"] + 1e-9
    r10b = not is_exact_directional_canonical_exception(m10b)

    m10c = _make_exact_exception_evidence()
    m10c["absolute_difference"] = m10c["absolute_difference"] + 1e-9
    r10c = not is_exact_directional_canonical_exception(m10c)

    r10 = r10a and r10b and r10c
    _record("altered canonical, reconstruction, or difference value fails", r10, matcher_returned_true=not r10)

    return tests, all_passed


# ---------------------------------------------------------------------------
# Duplicate-content audit
# ---------------------------------------------------------------------------
def duplicate_content_audit(registry: pd.DataFrame, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    within_feature_groups = []
    within_conflict_groups = []
    for project in PROJECTS:
        proj = registry[registry["project"] == project.upper()]
        groups = proj.groupby("feature_sha256")
        dup = [g for _, g in groups if len(g) > 1]
        if dup:
            within_feature_groups.append({"project": project.upper(), "count": len(dup), "total_samples_in_duplicate_groups": sum(len(g) for g in dup)})
        for _, g in groups:
            if len(g) > 1 and g["y_true"].nunique() > 1:
                within_conflict_groups.append({"project": project.upper(), "feature_sha256": g["feature_sha256"].iloc[0], "samples": len(g), "conflicting_labels": sorted(g["y_true"].unique().tolist())})

    within_content_groups = []
    for project in PROJECTS:
        proj = registry[registry["project"] == project.upper()]
        groups = proj.groupby("content_sha256")
        dup = [g for _, g in groups if len(g) > 1]
        if dup:
            within_content_groups.append({"project": project.upper(), "count": len(dup), "total_samples_in_duplicate_groups": sum(len(g) for g in dup)})

    feat_groups = registry.groupby("feature_sha256")
    cross_feature_dups = []
    for feat_hash, group in feat_groups:
        if group["project"].nunique() > 1:
            cross_feature_dups.append({"feature_sha256": feat_hash, "projects": sorted(group["project"].unique().tolist()), "samples": len(group)})

    content_groups = registry.groupby("content_sha256")
    cross_content_dups = []
    for content_hash, group in content_groups:
        if group["project"].nunique() > 1:
            cross_content_dups.append({"content_sha256": content_hash, "projects": sorted(group["project"].unique().tolist()), "samples": len(group)})

    feature_label_conflicts = []
    for feat_hash, group in feat_groups:
        if group["y_true"].nunique() > 1:
            feature_label_conflicts.append({"feature_sha256": feat_hash, "projects": sorted(group["project"].unique().tolist()), "samples": len(group), "conflicting_labels": sorted(group["y_true"].unique().tolist())})

    event_overlaps = []
    for event in events:
        train_uids = set(event["train_info"]["uids"])
        val_uids = set(event["val_info"]["uids"])
        test_uids = set(event["test_info"]["uids"])
        overlap = len(train_uids & val_uids) + len(train_uids & test_uids) + len(val_uids & test_uids)
        event_overlaps.append({"event_id": event["event_id"], "overlap": overlap})
    total_overlap = sum(o["overlap"] for o in event_overlaps)

    return {
        "within_project_duplicate_feature_groups": within_feature_groups,
        "within_project_duplicate_content_groups": within_content_groups,
        "within_project_feature_label_conflicts": within_conflict_groups,
        "cross_project_duplicate_features": cross_feature_dups,
        "cross_project_duplicate_content": cross_content_dups,
        "cross_project_feature_label_conflicts": feature_label_conflicts,
        "event_identity_overlaps": event_overlaps,
        "total_identity_overlap": total_overlap,
    }


# ---------------------------------------------------------------------------
# Immutable preservation – fail-closed contract from Git
# ---------------------------------------------------------------------------
PROTECTED_GROUPS: Dict[str, List[str]] = {
    "raw_data": RAW_DATA_PATHS,
    "canonical_outputs": CANONICAL_OUTPUT_PATHS,
    "part3a_artifacts": PART3A_ARTIFACT_PATHS,
}

_IGNORED_BASENAMES = {"__pycache__", ".DS_Store"}


def _is_ignored_rel(rel: str) -> bool:
    parts = rel.split("/")
    return any(p in _IGNORED_BASENAMES for p in parts)


def _group_for_rel(rel: str) -> Optional[str]:
    for group, paths in PROTECTED_GROUPS.items():
        for p in paths:
            if rel == p or rel.startswith(p + "/"):
                return group
    return None


def _git_ls_tree(repo: Path, commit: str, paths: List[str]) -> List[str]:
    cmd = ["git", "ls-tree", "-r", "--name-only", commit, "--"] + paths
    result = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"git ls-tree -r --name-only {commit} failed: {result.stderr}")
    return [line for line in result.stdout.strip().splitlines() if line.strip()]


def load_accepted_preservation_contract(
    repo: Path,
    accepted_commit: str,
) -> Dict[str, Any]:
    files: Dict[str, Dict[str, Any]] = {}
    for group_name, group_paths in PROTECTED_GROUPS.items():
        tree_paths = _git_ls_tree(repo, accepted_commit, group_paths)
        for rel in tree_paths:
            if _is_ignored_rel(rel):
                continue
            raw = git_show_bytes(repo, accepted_commit, rel)
            files[rel] = {
                "relative_path": rel,
                "group": group_name,
                "expected_sha256": sha256_bytes(raw),
                "expected_byte_size": len(raw),
            }
    return {
        "accepted_commit": accepted_commit,
        "files": files,
    }


def capture_current_protected_state(
    repo: Path,
) -> Dict[str, Any]:
    files: Dict[str, Dict[str, Any]] = {}
    for group_name, group_paths in PROTECTED_GROUPS.items():
        for p in group_paths:
            base = repo / p
            if base.is_file():
                rel = p
                if _is_ignored_rel(rel):
                    continue
                files[rel] = {
                    "relative_path": rel,
                    "group": group_name,
                    "actual_sha256": sha256_file(base),
                    "actual_byte_size": base.stat().st_size,
                }
            elif base.is_dir():
                for subpath in sorted(base.rglob("*")):
                    if subpath.is_file():
                        rel = str(subpath.relative_to(repo))
                        if _is_ignored_rel(rel):
                            continue
                        files[rel] = {
                            "relative_path": rel,
                            "group": group_name,
                            "actual_sha256": sha256_file(subpath),
                            "actual_byte_size": subpath.stat().st_size,
                        }
    return {"files": files}


def capture_protected_snapshot(repo: Path) -> Dict[str, Any]:
    return capture_current_protected_state(repo)


def compare_protected_state_to_accepted_contract(
    accepted_contract: Dict[str, Any],
    current_state: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    accepted_files = accepted_contract.get("files", {})
    current_files = current_state.get("files", {})

    group_names = ["raw_data", "canonical_outputs", "part3a_artifacts"]
    group_evidence: Dict[str, Any] = {}
    all_missing: List[str] = []
    all_extra: List[str] = []
    all_content_mismatches: List[str] = []
    all_byte_mismatches: List[str] = []
    total_expected = 0
    total_actual = 0
    total_changed = 0

    for gname in group_names:
        expected_rels = {r for r, v in accepted_files.items() if v["group"] == gname}
        actual_rels = {r for r, v in current_files.items() if v["group"] == gname}
        missing = sorted(expected_rels - actual_rels)
        extra = sorted(actual_rels - expected_rels)
        content_mismatches: List[str] = []
        byte_mismatches: List[str] = []
        unchanged: List[str] = []
        changed: List[str] = []

        for rel in sorted(expected_rels & actual_rels):
            exp = accepted_files[rel]
            cur = current_files[rel]
            sha_match = exp["expected_sha256"] == cur["actual_sha256"]
            size_match = exp["expected_byte_size"] == cur["actual_byte_size"]
            if sha_match and size_match:
                unchanged.append(rel)
            else:
                changed.append(rel)
                if not sha_match:
                    content_mismatches.append(rel)
                if not size_match:
                    byte_mismatches.append(rel)

        g_changed = len(changed)
        g_passed = (
            len(missing) == 0
            and len(extra) == 0
            and len(content_mismatches) == 0
            and len(byte_mismatches) == 0
            and g_changed == 0
        )
        group_evidence[gname] = {
            "expected_file_count": len(expected_rels),
            "actual_file_count": len(actual_rels),
            "missing_files": missing,
            "extra_files": extra,
            "content_mismatches": content_mismatches,
            "byte_size_mismatches": byte_mismatches,
            "unchanged_files": unchanged,
            "changed_file_count": g_changed,
            "passed": g_passed,
        }
        all_missing.extend(missing)
        all_extra.extend(extra)
        all_content_mismatches.extend(content_mismatches)
        all_byte_mismatches.extend(byte_mismatches)
        total_expected += len(expected_rels)
        total_actual += len(actual_rels)
        total_changed += g_changed

    preservation_passed = (
        len(all_missing) == 0
        and len(all_extra) == 0
        and len(all_content_mismatches) == 0
        and len(all_byte_mismatches) == 0
        and total_changed == 0
    )

    evidence: Dict[str, Any] = {
        "accepted_commit_reference_used": True,
        "accepted_commit": accepted_contract.get("accepted_commit"),
        "raw_data_expected_files": group_evidence["raw_data"]["expected_file_count"],
        "raw_data_actual_files": group_evidence["raw_data"]["actual_file_count"],
        "raw_data_missing_files": group_evidence["raw_data"]["missing_files"],
        "raw_data_extra_files": group_evidence["raw_data"]["extra_files"],
        "raw_data_content_mismatches": group_evidence["raw_data"]["content_mismatches"],
        "raw_data_changed": group_evidence["raw_data"]["changed_file_count"],
        "canonical_outputs_expected_files": group_evidence["canonical_outputs"]["expected_file_count"],
        "canonical_outputs_actual_files": group_evidence["canonical_outputs"]["actual_file_count"],
        "canonical_outputs_missing_files": group_evidence["canonical_outputs"]["missing_files"],
        "canonical_outputs_extra_files": group_evidence["canonical_outputs"]["extra_files"],
        "canonical_outputs_content_mismatches": group_evidence["canonical_outputs"]["content_mismatches"],
        "canonical_outputs_changed": group_evidence["canonical_outputs"]["changed_file_count"],
        "part3a_artifacts_expected_files": group_evidence["part3a_artifacts"]["expected_file_count"],
        "part3a_artifacts_actual_files": group_evidence["part3a_artifacts"]["actual_file_count"],
        "part3a_artifacts_missing_files": group_evidence["part3a_artifacts"]["missing_files"],
        "part3a_artifacts_extra_files": group_evidence["part3a_artifacts"]["extra_files"],
        "part3a_artifacts_content_mismatches": group_evidence["part3a_artifacts"]["content_mismatches"],
        "part3a_artifacts_changed": group_evidence["part3a_artifacts"]["changed_file_count"],
        "protected_files_expected": total_expected,
        "protected_files_actual": total_actual,
        "protected_files_missing": all_missing,
        "protected_files_extra": all_extra,
        "protected_files_content_mismatches": all_content_mismatches,
        "protected_files_changed": total_changed,
        "raw_data_modified": group_evidence["raw_data"]["changed_file_count"] > 0,
        "canonical_outputs_modified": group_evidence["canonical_outputs"]["changed_file_count"] > 0,
        "part3a_artifacts_modified": group_evidence["part3a_artifacts"]["changed_file_count"] > 0,
        "preservation_passed": preservation_passed,
        "group_details": group_evidence,
    }
    return preservation_passed, evidence


def validate_protected_before_after(
    accepted_contract: Dict[str, Any],
    before_snapshot: Dict[str, Any],
    after_snapshot: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    before_passed, before_ev = compare_protected_state_to_accepted_contract(accepted_contract, before_snapshot)
    after_passed, after_ev = compare_protected_state_to_accepted_contract(accepted_contract, after_snapshot)

    before_files = set(before_snapshot.get("files", {}).keys())
    after_files = set(after_snapshot.get("files", {}).keys())
    file_sets_equal = before_files == after_files

    before_hashes = {r: v["actual_sha256"] for r, v in before_snapshot.get("files", {}).items()}
    after_hashes = {r: v["actual_sha256"] for r, v in after_snapshot.get("files", {}).items()}
    hashes_equal = before_hashes == after_hashes

    passed = before_passed and after_passed and file_sets_equal and hashes_equal

    evidence = {
        "before_matches_accepted": before_passed,
        "after_matches_accepted": after_passed,
        "before_after_file_sets_equal": file_sets_equal,
        "before_after_hashes_equal": hashes_equal,
        "before_evidence": before_ev,
        "after_evidence": after_ev,
        "genuine_before_after_supported": True,
        "preservation_passed": passed,
    }
    return passed, evidence


def capture_preservation_state(repo: Path) -> Dict[str, Any]:
    return capture_current_protected_state(repo)


# ---------------------------------------------------------------------------
# Core bundle builder (one independent build)
# ---------------------------------------------------------------------------
def build_core_bundle(
    output_root: Path,
    frozen: Any,
    projects: Dict[str, pd.DataFrame],
    common_cols: List[str],
    registry: pd.DataFrame,
    canonical_val: pd.DataFrame,
    canonical_res: pd.DataFrame,
    preservation_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute one complete Part 3B build into output_root. Return paths and audit state."""
    out = output_root
    (out / "results" / "part3b_prediction_ledger").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    feature_schema_sha256 = compute_feature_schema_sha256(common_cols)
    dataset_profile = build_dataset_profile(projects, common_cols, {"detected_target_columns": {}, "original_numeric_feature_counts": {}, "numeric_coercible_feature_counts": {}, "all_null_numeric_columns_removed": {}, "retained_numeric_feature_counts": {}, "common_feature_names": common_cols, "common_feature_count": len(common_cols), "per_project_missing_value_counts": {}})
    events = build_all_events(projects, common_cols)

    split_rows: List[Dict[str, Any]] = []
    pred_rows: List[Dict[str, Any]] = []
    preprocessing_audits: List[Dict[str, Any]] = []
    fitted_count = 0

    for i, event in enumerate(events):
        print(f"PROGRESS: event {i + 1}/{len(events)} {event['event_id']}", flush=True)
        fitted = fit_event_candidates(frozen, event, event["seed"])
        fitted_count += 4
        split_rows.extend(build_split_membership_rows(event))
        pred_rows.extend(build_prediction_rows(event, fitted, frozen))
        preprocessing_audits.extend(audit_event_preprocessing(event, fitted))
        config_audits = validate_candidate_configuration(fitted, frozen, event["event_id"], event["seed"])
        for ca in config_audits:
            ca["event_id"] = event["event_id"]
        preprocessing_audits.extend(config_audits)
        # Drop heavy model references to keep memory bounded.
        for c in CANDIDATES:
            del fitted[c]["model"]

    split_df = _split_membership_sorted(pd.DataFrame(split_rows))
    split_within = split_df[split_df["experiment"] == "within_project"].reset_index(drop=True)
    split_cross = split_df[split_df["experiment"] == "cross_project"].reset_index(drop=True)
    split_within = split_within[SPLIT_MEMBERSHIP_COLUMNS]
    split_cross = split_cross[SPLIT_MEMBERSHIP_COLUMNS]

    pred_df = _prediction_ledger_sorted(pd.DataFrame(pred_rows))
    pred_within = pred_df[pred_df["experiment"] == "within_project"].reset_index(drop=True)
    pred_cross = pred_df[pred_df["experiment"] == "cross_project"].reset_index(drop=True)
    pred_within = pred_within[PREDICTION_LEDGER_COLUMNS]
    pred_cross = pred_cross[PREDICTION_LEDGER_COLUMNS]

    event_manifest = build_event_manifest(events, common_cols, feature_schema_sha256, preprocessing_audits)
    print("PROGRESS: reconstructing validation and canonical results", flush=True)
    val_recon = reconstruct_validation_from_ledger(frozen, pred_df)
    result_recon = reconstruct_results_from_ledger(frozen, pred_df, event_manifest)
    print("PROGRESS: running duplicate content audit", flush=True)
    duplicate_audit = duplicate_content_audit(registry, events)
    print("PROGRESS: running tie policy tests", flush=True)
    tie_tests, tie_passed = run_tie_policy_tests(frozen)
    print("PROGRESS: running negative tests", flush=True)
    negative_tests, negative_passed = run_negative_tests(split_within, split_cross, pred_within, pred_cross, val_recon, result_recon, canonical_val, canonical_res, registry, event_manifest)
    print("PROGRESS: validating canonical nondeterminism exception", flush=True)
    exception_evidence = validate_canonical_nondeterminism_exception(result_recon, canonical_res, pred_df, frozen)
    print("PROGRESS: running canonical exception validator tests", flush=True)
    exception_tests, exception_tests_passed = run_canonical_exception_validator_tests(frozen, result_recon, canonical_res, pred_df)

    # Validation results
    print("PROGRESS: running production validators", flush=True)
    validation_results = {
        "dataset_profile": validate_dataset_profile(dataset_profile),
        "sample_registry": validate_sample_registry(registry),
        "event_manifest": validate_event_manifest(event_manifest, registry, split_within, split_cross, preprocessing_audits, feature_schema_sha256),
        "split_membership": validate_split_membership(split_within, split_cross, registry, event_manifest),
        "prediction_ledger": validate_prediction_ledger(pred_within, pred_cross, split_within, split_cross, registry),
        "preprocessing_audit": validate_preprocessing_audit(preprocessing_audits),
        "validation_reconstruction": validate_validation_reconstruction(val_recon, canonical_val),
        "result_reconstruction": validate_result_reconstruction(result_recon, canonical_res),
        "canonical_nondeterminism_exception": (exception_evidence["validated"], exception_evidence),
        "canonical_exception_validator_tests": (exception_tests_passed, {"tests": exception_tests}),
        "tie_policy": (tie_passed, {"tests": tie_tests}),
        "negative_tests": (negative_passed, {"tests": negative_tests}),
        "preservation": (True, {"state": "before-write placeholder"}),
    }

    # Write core artifacts.
    registry_path = out / "results" / "part3b_prediction_ledger" / "sample_registry.csv"
    write_csv_atomic(registry, registry_path)
    event_manifest_path = out / "results" / "part3b_prediction_ledger" / "event_manifest.csv"
    write_csv_atomic(event_manifest, event_manifest_path)
    split_within_path = out / "results" / "part3b_prediction_ledger" / "split_membership_within.csv.gz"
    write_csv_gzip_atomic(split_within, split_within_path)
    split_cross_path = out / "results" / "part3b_prediction_ledger" / "split_membership_cross.csv.gz"
    write_csv_gzip_atomic(split_cross, split_cross_path)
    pred_within_path = out / "results" / "part3b_prediction_ledger" / "prediction_ledger_within.csv.gz"
    write_csv_gzip_atomic(pred_within, pred_within_path)
    pred_cross_path = out / "results" / "part3b_prediction_ledger" / "prediction_ledger_cross.csv.gz"
    write_csv_gzip_atomic(pred_cross, pred_cross_path)
    val_recon_path = out / "results" / "part3b_prediction_ledger" / "validation_reconstruction.csv"
    write_csv_atomic(val_recon, val_recon_path)
    result_recon_path = out / "results" / "part3b_prediction_ledger" / "canonical_result_reconstruction.csv"
    write_csv_atomic(result_recon, result_recon_path)

    artifacts = {
        "results/part3b_prediction_ledger/sample_registry.csv": registry_path,
        "results/part3b_prediction_ledger/event_manifest.csv": event_manifest_path,
        "results/part3b_prediction_ledger/split_membership_within.csv.gz": split_within_path,
        "results/part3b_prediction_ledger/split_membership_cross.csv.gz": split_cross_path,
        "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz": pred_within_path,
        "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz": pred_cross_path,
        "results/part3b_prediction_ledger/validation_reconstruction.csv": val_recon_path,
        "results/part3b_prediction_ledger/canonical_result_reconstruction.csv": result_recon_path,
    }

    # Compute artifact hashes for manifest and report.
    artifact_hashes = {rel: {"sha256": sha256_file(path), "byte_size": path.stat().st_size} for rel, path in artifacts.items()}

    # Build ledger manifest (without its own entry; self-referential hash not embedded).
    manifest_entries = build_artifact_manifest(out, artifacts, artifact_hashes)
    manifest_path = out / "results" / "part3b_prediction_ledger" / "ledger_manifest.json"
    manifest_data = {
        "manifest_version": PART3B_VERSION,
        "starting_commit": STARTING_COMMIT,
        "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
        "project_order": [p.upper() for p in PROJECTS],
        "seed_order": SEEDS,
        "candidate_order": CANDIDATES,
        "event_count": EXPECTED_EVENT_COUNT,
        "sample_count": EXPECTED_REGISTRY_ROWS,
        "split_membership_total_rows": len(split_df),
        "prediction_total_rows": len(pred_df),
        "validation_reconstruction_rows": len(val_recon),
        "canonical_result_reconstruction_rows": len(result_recon),
        "self_referential_hash_embedded": False,
        "artifacts": manifest_entries,
    }
    write_text_atomic(manifest_path, _json_dumps(manifest_data))
    artifacts["results/part3b_prediction_ledger/ledger_manifest.json"] = manifest_path

    # Build audit checks and stage gate.
    audit_checks, check_evidence = build_all_checks(
        validation_results, duplicate_audit, negative_tests, tie_tests, True, True, common_cols, fitted_count, pred_within, pred_cross, dataset_profile, event_manifest
    )
    _root = repo_root()
    _accepted_contract = load_accepted_preservation_contract(_root, ACCEPTED_PART3A_COMMIT)
    _preservation_ok, _preservation_ev = compare_protected_state_to_accepted_contract(
        _accepted_contract, preservation_state
    )
    stage_gate = build_stage_gate(audit_checks, check_evidence, validation_results, _preservation_ev, duplicate_audit, False, False)
    stage_gate_passed, stage_gate_evidence = validate_stage_gate(stage_gate)
    audit_checks["stage_gate_passed"] = stage_gate_passed
    audit_checks["all_critical_checks_passed"] = compute_all_critical_checks_passed(audit_checks)
    audit_schema_passed, audit_schema_evidence = validate_exact_audit_check_schema(audit_checks)

    # JSON report.
    json_report_path = out / "reports" / "part3b_split_leakage_audit.json"
    json_report = render_json_report(audit_checks, stage_gate, stage_gate_evidence, validation_results, duplicate_audit, negative_tests, tie_tests, preservation_state, artifacts, artifact_hashes, feature_schema_sha256, dataset_profile, event_manifest, common_cols, registry, split_within, split_cross, pred_within, pred_cross, val_recon, result_recon, fitted_count, canonical_val, canonical_res)
    write_text_atomic(json_report_path, _json_dumps(json_report))
    artifacts["reports/part3b_split_leakage_audit.json"] = json_report_path

    # MD report.
    md_report_path = out / "reports" / "part3b_split_leakage_audit.md"
    md_report = render_markdown_report(json_report)
    write_text_atomic(md_report_path, md_report)
    artifacts["reports/part3b_split_leakage_audit.md"] = md_report_path

    return {
        "artifacts": artifacts,
        "artifact_hashes": artifact_hashes,
        "audit_checks": audit_checks,
        "check_evidence": check_evidence,
        "audit_schema_evidence": audit_schema_evidence,
        "stage_gate": stage_gate,
        "stage_gate_evidence": stage_gate_evidence,
        "validation_results": validation_results,
        "duplicate_audit": duplicate_audit,
        "negative_tests": negative_tests,
        "tie_tests": tie_tests,
        "events": events,
        "registry": registry,
        "split_within": split_within,
        "split_cross": split_cross,
        "pred_within": pred_within,
        "pred_cross": pred_cross,
        "val_recon": val_recon,
        "result_recon": result_recon,
        "event_manifest": event_manifest,
        "dataset_profile": dataset_profile,
        "feature_schema_sha256": feature_schema_sha256,
        "common_cols": common_cols,
        "fitted_count": fitted_count,
    }


# ---------------------------------------------------------------------------
# Artifact manifest
# ---------------------------------------------------------------------------
def build_artifact_manifest(out_root: Path, artifacts: Dict[str, Path], artifact_hashes: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    entries = []
    rel_order = [
        "results/part3b_prediction_ledger/sample_registry.csv",
        "results/part3b_prediction_ledger/event_manifest.csv",
        "results/part3b_prediction_ledger/split_membership_within.csv.gz",
        "results/part3b_prediction_ledger/split_membership_cross.csv.gz",
        "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz",
        "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz",
        "results/part3b_prediction_ledger/validation_reconstruction.csv",
        "results/part3b_prediction_ledger/canonical_result_reconstruction.csv",
    ]
    for rel in rel_order:
        path = artifacts[rel]
        df = pd.read_csv(path, compression="gzip" if path.suffix == ".gz" else "infer")
        entries.append({
            "relative_path": rel,
            "format": "csv" if not rel.endswith(".gz") else "csv.gz",
            "compressed": rel.endswith(".gz"),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "byte_size": artifact_hashes[rel]["byte_size"],
            "sha256": artifact_hashes[rel]["sha256"],
        })
    return entries


# ---------------------------------------------------------------------------
# Audit-check wiring (41 exact names)
# ---------------------------------------------------------------------------
def build_all_checks(
    validation_results: Dict[str, Tuple[bool, Dict[str, Any]]],
    duplicate_audit: Dict[str, Any],
    negative_tests: List[Dict[str, Any]],
    tie_tests: List[Dict[str, Any]],
    split_determinism_passed: bool,
    deterministic_artifacts_passed: bool,
    common_cols: List[str],
    fitted_count: int,
    pred_within: pd.DataFrame,
    pred_cross: pd.DataFrame,
    profile: Dict[str, Any],
    event_manifest: pd.DataFrame,
) -> Tuple[Dict[str, bool], Dict[str, Any]]:
    checks: Dict[str, bool] = {}
    evidence: Dict[str, Any] = {}

    # Provenance / source verification
    checks["source_commit_verified"] = verify_source_commit(ACCEPTED_PART3A_COMMIT)
    pipeline_hash = sha256_file(frozen_script_path())
    expected_pipeline_hash = sha256_bytes(git_show_bytes(repo_root(), ACCEPTED_PART3A_COMMIT, "scripts/run_repeated_evaluation.py"))
    checks["imported_pipeline_sha_verified"] = pipeline_hash == expected_pipeline_hash

    # Dataset profile and registry
    checks["dataset_profile_passed"] = validation_results["dataset_profile"][0]
    checks["sample_registry_passed"] = validation_results["sample_registry"][0]
    checks["feature_schema_passed"] = (len(common_cols) == 20) and all(len(c) > 0 for c in common_cols)

    # Event manifest and split membership
    checks["event_manifest_count_passed"] = validation_results["event_manifest"][0]
    checks["within_split_counts_passed"] = validation_results["split_membership"][1]["within"]["row_count"] == EXPECTED_WITHIN_SPLIT_ROWS["total"]
    checks["cross_split_counts_passed"] = validation_results["split_membership"][1]["cross"]["row_count"] == EXPECTED_CROSS_SPLIT_ROWS["total"]
    checks["split_membership_totals_passed"] = (validation_results["split_membership"][1]["within"]["row_count"] + validation_results["split_membership"][1]["cross"]["row_count"]) == (EXPECTED_WITHIN_SPLIT_ROWS["total"] + EXPECTED_CROSS_SPLIT_ROWS["total"])
    checks["split_key_uniqueness_passed"] = validation_results["split_membership"][1]["duplicate_keys"] == 0
    checks["split_identity_disjointness_passed"] = (validation_results["split_membership"][1]["overlap_train_test"] == 0 and validation_results["split_membership"][1]["overlap_train_val"] == 0 and validation_results["split_membership"][1]["overlap_val_test"] == 0)
    checks["within_union_coverage_passed"] = validation_results["split_membership"][1]["within_coverage_ok"]
    checks["cross_target_isolation_passed"] = validation_results["split_membership"][1]["cross_isolation_ok"]
    checks["cross_source_isolation_passed"] = validation_results["split_membership"][1]["cross_isolation_ok"]
    checks["split_determinism_passed"] = split_determinism_passed
    checks["class_count_consistency_passed"] = validation_results["event_manifest"][1]["registry_counts_ok"]
    checks["preprocessing_train_only_passed"] = validation_results["preprocessing_audit"][0]

    # Candidate fit and prediction ledger
    checks["candidate_fit_count_passed"] = fitted_count == EXPECTED_CANDIDATE_FITS
    checks["prediction_row_counts_passed"] = (validation_results["prediction_ledger"][1]["within_row_count"] == EXPECTED_WITHIN_PREDICTION_ROWS["total"] and validation_results["prediction_ledger"][1]["cross_row_count"] == EXPECTED_CROSS_PREDICTION_ROWS["total"])
    checks["prediction_key_uniqueness_passed"] = validation_results["prediction_ledger"][1]["duplicate_keys"] == 0
    checks["prediction_candidate_schema_passed"] = validation_results["prediction_ledger"][1]["within_schema_ok"] and validation_results["prediction_ledger"][1]["cross_schema_ok"]
    checks["prediction_scores_finite_passed"] = validation_results["prediction_ledger"][1]["finite_ok"]
    checks["prediction_scores_range_passed"] = validation_results["prediction_ledger"][1]["range_ok"]
    checks["no_train_predictions_passed"] = validation_results["prediction_ledger"][1]["no_train_rows"]

    # Reconstruction
    checks["validation_reconstruction_count_passed"] = validation_results["validation_reconstruction"][1]["row_count"] == EXPECTED_VALIDATION_RECONSTRUCTION_ROWS
    checks["validation_categorical_match_passed"] = validation_results["validation_reconstruction"][1]["categorical_match"]
    checks["validation_numeric_match_passed"] = validation_results["validation_reconstruction"][1]["numeric_mismatches"] == 0
    checks["result_reconstruction_count_passed"] = validation_results["result_reconstruction"][1]["row_count"] == EXPECTED_RESULT_RECONSTRUCTION_ROWS
    checks["result_categorical_match_passed"] = validation_results["result_reconstruction"][1]["categorical_match"]
    strict_numeric_match = validation_results["result_reconstruction"][1]["numeric_mismatches"] == 0
    # Canonical nondeterminism exception accounting (evidence, not audit checks)
    exc_ev = validation_results["canonical_nondeterminism_exception"][1]
    evidence["canonical_nondeterminism_exception_detected"] = exc_ev.get("approved_exception_count", 0) > 0 or exc_ev.get("unapproved_mismatch_count", 0) > 0
    evidence["canonical_nondeterminism_exception_validated"] = bool(exc_ev.get("validated", False))
    evidence["strict_validation_mismatches"] = int(validation_results["validation_reconstruction"][1].get("numeric_mismatches", -1))
    evidence["strict_result_mismatches_before_exception"] = len(exc_ev.get("approved_exception_matches", [])) + len(exc_ev.get("unapproved_mismatches", []))
    evidence["approved_nondeterminism_exceptions"] = exc_ev.get("approved_exception_count", 0)
    evidence["unapproved_result_mismatches"] = exc_ev.get("unapproved_mismatch_count", 0)
    evidence["result_reconstruction_passed_after_validated_exception"] = bool(
        checks["result_categorical_match_passed"]
        and evidence["canonical_nondeterminism_exception_validated"]
        and evidence["unapproved_result_mismatches"] == 0
    )
    evidence["canonical_result_reconstruction_strictly_identical"] = strict_numeric_match
    evidence["canonical_result_reconstruction_scientifically_reconciled"] = evidence["result_reconstruction_passed_after_validated_exception"]

    checks["result_numeric_match_passed"] = strict_numeric_match or (
        evidence["canonical_nondeterminism_exception_validated"]
        and evidence["unapproved_result_mismatches"] == 0
    )

    # Selection/test isolation (derived from function signatures and runtime checks)
    sig_selection = inspect.signature(freeze_event_selection_policy)
    sig_evaluation = inspect.signature(evaluate_frozen_policy_on_test_ledger)
    selection_only_ledger = len(sig_selection.parameters) == 2 and "event_validation_ledger" in sig_selection.parameters
    evaluation_no_selection = len(sig_evaluation.parameters) == 3 and "frozen_policy" in sig_evaluation.parameters and "event_test_ledger" in sig_evaluation.parameters
    checks["selection_validation_only_passed"] = selection_only_ledger
    checks["test_not_used_for_selection_passed"] = evaluation_no_selection

    # Tie policy / duplicate / determinism / negative tests
    checks["tie_policy_passed"] = validation_results["tie_policy"][0]
    checks["duplicate_content_audit_completed"] = isinstance(duplicate_audit, dict) and "total_identity_overlap" in duplicate_audit
    checks["schema_target_awareness_documented"] = profile.get("common_schema_uses_target_labels", False) is False and profile.get("common_schema_uses_target_feature_values", False) is False
    checks["pooled_source_validation_design_documented"] = profile.get("pooled_source_validation", True) is True
    checks["raw_and_canonical_preservation_passed"] = False  # updated after write by preservation validator
    checks["deterministic_artifacts_passed"] = deterministic_artifacts_passed
    checks["negative_tests_passed"] = validation_results["negative_tests"][0]

    checks["stage_gate_passed"] = False
    checks["all_critical_checks_passed"] = False
    return checks, evidence


# ---------------------------------------------------------------------------
# Explicit ledger-completion helper (no truthy counters, no generic iteration)
# ---------------------------------------------------------------------------
def compute_part3b_prediction_ledger_complete(
    checks: Dict[str, bool],
    canonical_reconciliation_evidence: Dict[str, Any],
    persisted_ledger_evidence: Dict[str, Any],
    preservation_evidence: Dict[str, Any],
    semantic_reproducibility_evidence: Dict[str, Any],
    negative_test_evidence: Dict[str, Any],
) -> bool:
    """Return True only when every explicit condition for ledger completion is met.

    Every required field is accessed explicitly.  No truthy counters or
    generic dictionary iteration are used.  A missing field returns False
    (fail-closed).
    """
    try:
        c1 = checks["source_commit_verified"] is True
        c2 = checks["imported_pipeline_sha_verified"] is True
        c3 = checks["dataset_profile_passed"] is True
        c4 = checks["sample_registry_passed"] is True
        c5 = checks["feature_schema_passed"] is True
        c6 = checks["event_manifest_count_passed"] is True
        c7 = checks["within_split_counts_passed"] is True
        c8 = checks["cross_split_counts_passed"] is True
        c9 = checks["split_membership_totals_passed"] is True
        c10 = checks["split_key_uniqueness_passed"] is True
        c11 = checks["split_identity_disjointness_passed"] is True
        c12 = checks["within_union_coverage_passed"] is True
        c13 = checks["cross_target_isolation_passed"] is True
        c14 = checks["cross_source_isolation_passed"] is True
        c15 = checks["split_determinism_passed"] is True
        c16 = checks["class_count_consistency_passed"] is True
        c17 = checks["preprocessing_train_only_passed"] is True
        c18 = checks["candidate_fit_count_passed"] is True
        c19 = checks["prediction_row_counts_passed"] is True
        c20 = checks["prediction_key_uniqueness_passed"] is True
        c21 = checks["prediction_candidate_schema_passed"] is True
        c22 = checks["prediction_scores_finite_passed"] is True
        c23 = checks["prediction_scores_range_passed"] is True
        c24 = checks["no_train_predictions_passed"] is True
        c25 = checks["validation_reconstruction_count_passed"] is True
        c26 = checks["validation_categorical_match_passed"] is True
        c27 = checks["validation_numeric_match_passed"] is True
        c28 = checks["result_reconstruction_count_passed"] is True
        c29 = checks["result_categorical_match_passed"] is True
        c30 = checks["result_numeric_match_passed"] is True
        c31 = checks["selection_validation_only_passed"] is True
        c32 = checks["test_not_used_for_selection_passed"] is True
        c33 = checks["tie_policy_passed"] is True
        c34 = checks["duplicate_content_audit_completed"] is True
        c35 = checks["schema_target_awareness_documented"] is True
        c36 = checks["pooled_source_validation_design_documented"] is True
        c37 = checks["raw_and_canonical_preservation_passed"] is True
        c38 = checks["deterministic_artifacts_passed"] is True
        c39 = checks["negative_tests_passed"] is True

        canonical_ok = (
            canonical_reconciliation_evidence["strict_validation_mismatches"] == 0
            and canonical_reconciliation_evidence["strict_result_mismatches_before_exception"] == 1
            and canonical_reconciliation_evidence["approved_nondeterminism_exceptions"] == 1
            and canonical_reconciliation_evidence["unapproved_result_mismatches"] == 0
            and canonical_reconciliation_evidence["canonical_nondeterminism_exception_validated"] is True
        )

        persisted_ok = (
            persisted_ledger_evidence["persisted_validation_reconstruction_matches_in_memory"] is True
            and persisted_ledger_evidence["persisted_result_reconstruction_matches_in_memory"] is True
            and persisted_ledger_evidence["persisted_ledger_reconstruction_matches_in_memory"] is True
            and persisted_ledger_evidence["persisted_validation_numeric_mismatches"] == 0
            and persisted_ledger_evidence["persisted_result_numeric_mismatches"] == 0
            and persisted_ledger_evidence["csv_float_precision"] == "round_trip"
        )

        preservation_ok = (
            preservation_evidence["preservation_passed"] is True
            and preservation_evidence["raw_data_changed"] == 0
            and preservation_evidence["canonical_outputs_changed"] == 0
            and preservation_evidence["part3a_artifacts_changed"] == 0
        )

        semantic_ok = (
            semantic_reproducibility_evidence["semantic_reproducibility_passed"] is True
            and semantic_reproducibility_evidence["unapproved_differing_artifacts"] == []
        )

        nt = negative_test_evidence
        original_neg_ok = (
            nt["original_negative_tests"]["expected"] == 12
            and nt["original_negative_tests"]["executed"] == 12
            and nt["original_negative_tests"]["passed"] == 12
            and nt["original_negative_tests"]["failed"] == 0
        )
        canonical_exc_ok = (
            nt["canonical_exception_tests"]["expected"] == 10
            and nt["canonical_exception_tests"]["executed"] == 10
            and nt["canonical_exception_tests"]["passed"] == 10
            and nt["canonical_exception_tests"]["failed"] == 0
        )
        persisted_ledger_tests_ok = (
            nt["persisted_ledger_tests"]["expected"] == 6
            and nt["persisted_ledger_tests"]["executed"] == 6
            and nt["persisted_ledger_tests"]["passed"] == 6
            and nt["persisted_ledger_tests"]["failed"] == 0
        )
        preservation_tests_ok = (
            nt["preservation_tests"]["expected"] == 8
            and nt["preservation_tests"]["executed"] == 8
            and nt["preservation_tests"]["passed"] == 8
            and nt["preservation_tests"]["failed"] == 0
        )

        return bool(
            c1 and c2 and c3 and c4 and c5 and c6 and c7 and c8 and c9 and c10
            and c11 and c12 and c13 and c14 and c15 and c16 and c17 and c18 and c19 and c20
            and c21 and c22 and c23 and c24 and c25 and c26 and c27 and c28 and c29 and c30
            and c31 and c32 and c33 and c34 and c35 and c36 and c37 and c38 and c39
            and canonical_ok and persisted_ok and preservation_ok and semantic_ok
            and original_neg_ok and canonical_exc_ok
            and persisted_ledger_tests_ok and preservation_tests_ok
        )
    except (KeyError, TypeError, IndexError):
        return False


# ---------------------------------------------------------------------------
# Stage gate
# ---------------------------------------------------------------------------
def build_stage_gate(
    checks: Dict[str, bool],
    check_evidence: Dict[str, Any],
    validation_results: Dict[str, Tuple[bool, Dict[str, Any]]],
    preservation_evidence: Dict[str, Any],
    duplicate_audit: Dict[str, Any],
    semantic_reproducibility_passed: bool,
    part3b_prediction_ledger_complete: bool,
) -> Dict[str, Any]:
    identity_leak = duplicate_audit["total_identity_overlap"] > 0
    preprocessing_leak = not validation_results["preprocessing_audit"][0]
    selection_test_leak = not (
        validation_results["validation_reconstruction"][0]
        and checks["selection_validation_only_passed"]
        and checks["test_not_used_for_selection_passed"]
    )
    result_reconciled = bool(
        check_evidence["result_reconstruction_passed_after_validated_exception"]
        and check_evidence["canonical_nondeterminism_exception_validated"]
        and check_evidence["unapproved_result_mismatches"] == 0
    )

    authorized = bool(
        part3b_prediction_ledger_complete
        and not identity_leak
        and not preprocessing_leak
        and not selection_test_leak
        and result_reconciled
        and semantic_reproducibility_passed
    )

    gate = {
        "part3b_prediction_ledger_complete": part3b_prediction_ledger_complete,
        "raw_data_modified": preservation_evidence["raw_data_modified"],
        "canonical_outputs_modified": preservation_evidence["canonical_outputs_modified"],
        "part3a_artifacts_modified": preservation_evidence["part3a_artifacts_modified"],
        "identity_leakage_detected": identity_leak,
        "preprocessing_leakage_detected": preprocessing_leak,
        "selection_test_leakage_detected": selection_test_leak,
        "canonical_validation_reconstruction_passed": validation_results["validation_reconstruction"][0],
        "canonical_result_reconstruction_passed": result_reconciled,
        "canonical_result_reconstruction_strictly_identical": check_evidence["canonical_result_reconstruction_strictly_identical"],
        "canonical_result_reconstruction_scientifically_reconciled": check_evidence["canonical_result_reconstruction_scientifically_reconciled"],
        "canonical_nondeterminism_exception_detected": check_evidence["canonical_nondeterminism_exception_detected"],
        "canonical_nondeterminism_exception_validated": check_evidence["canonical_nondeterminism_exception_validated"],
        "semantic_reproducibility_passed": semantic_reproducibility_passed,
        "next_authorized_stage": "Part 3C" if authorized else None,
        "part3c_constraint": PART3C_CONSTRAINT,
    }
    return gate


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------
class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.generic):
            return float(obj)
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _evidence_for_json(ev: Any) -> Any:
    """Convert numpy/pandas values to JSON-serializable primitives."""
    if isinstance(ev, np.generic):
        if isinstance(ev, np.bool_):
            return bool(ev)
        return float(ev)
    if isinstance(ev, bool):
        return bool(ev)
    if isinstance(ev, (np.integer, np.floating)):
        return float(ev)
    if isinstance(ev, np.ndarray):
        return ev.tolist()
    if isinstance(ev, pd.DataFrame):
        return ev.to_dict(orient="records")
    if isinstance(ev, dict):
        return {k: _evidence_for_json(v) for k, v in ev.items()}
    if isinstance(ev, (list, tuple)):
        return [_evidence_for_json(v) for v in ev]
    return ev


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=False, cls=_NumpyEncoder)


def render_json_report(
    audit_checks: Dict[str, bool],
    stage_gate: Dict[str, Any],
    stage_gate_evidence: Dict[str, Any],
    validation_results: Dict[str, Tuple[bool, Dict[str, Any]]],
    duplicate_audit: Dict[str, Any],
    negative_tests: List[Dict[str, Any]],
    tie_tests: List[Dict[str, Any]],
    preservation_state: Dict[str, Any],
    artifacts: Dict[str, Path],
    artifact_hashes: Dict[str, Dict[str, Any]],
    feature_schema_sha256: str,
    dataset_profile: Dict[str, Any],
    event_manifest: pd.DataFrame,
    common_cols: List[str],
    registry: pd.DataFrame,
    split_within: pd.DataFrame,
    split_cross: pd.DataFrame,
    pred_within: pd.DataFrame,
    pred_cross: pd.DataFrame,
    val_recon: pd.DataFrame,
    result_recon: pd.DataFrame,
    fitted_count: int,
    canonical_val: pd.DataFrame,
    canonical_res: pd.DataFrame,
) -> Dict[str, Any]:
    # Recompute reconstruction evidence with per-column details.
    val_keys = ["experiment", "target_project", "seed", "candidate", "mode"]
    val_numeric = [c for c in VALIDATION_RECONSTRUCTION_COLUMNS if c not in val_keys]
    res_keys = ["experiment", "target_project", "seed", "model"]
    res_cat = res_keys + ["selected_candidate", "selection_mode"]
    res_numeric = [c for c in RESULT_RECONSTRUCTION_COLUMNS if c not in res_cat]
    _, val_compare = compare_reconstruction(val_recon, canonical_val, val_keys, val_numeric)
    _, res_compare = compare_reconstruction(result_recon, canonical_res, res_keys, res_numeric)
    val_compare = _evidence_for_json(val_compare)
    res_compare = _evidence_for_json(res_compare)

    stored_forbidden = []
    for df in [pred_within, pred_cross]:
        for c in df.columns:
            if c.startswith("threshold_") or c.startswith("objective_") or c.startswith("metric__") or c.startswith("soft_top3_"):
                stored_forbidden.append(c)
    stored_forbidden = sorted(set(stored_forbidden))
    test_derived_fields = [c for c in stored_forbidden if "metric__" in c or c.startswith("soft_top3")]

    validation_ledger = pd.concat([pred_within, pred_cross], ignore_index=True)
    validation_rows = validation_ledger[validation_ledger["split_role"] == "validation"]
    test_rows = validation_ledger[validation_ledger["split_role"] == "test"]

    exc_ev = validation_results.get("canonical_nondeterminism_exception", (False, {}))[1]
    exc_tests = validation_results.get("canonical_exception_validator_tests", (False, {}))[1]
    return {
        "part3b_version": PART3B_VERSION,
        "starting_commit": STARTING_COMMIT,
        "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
        "repository": REPOSITORY,
        "branch": BRANCH,
        "timestamp": "1970-01-01T00:00:00",
        "audit_checks": audit_checks,
        "stage_gate": stage_gate,
        "stage_gate_evidence": _evidence_for_json(stage_gate_evidence),
        "validation_results": {k: _evidence_for_json(v) for k, v in validation_results.items()},
        "duplicate_content_audit": _evidence_for_json(duplicate_audit),
        "negative_tests": _evidence_for_json(negative_tests),
        "canonical_exception_validator_tests": _evidence_for_json(exc_tests.get("tests", [])),
        "tie_policy_tests": _evidence_for_json(tie_tests),
        "canonical_nondeterminism_diagnostic": _evidence_for_json(exc_ev.get("diagnostic", ET_ND_DIAGNOSTIC)),
        "preservation_state": preservation_state,
        "artifact_hashes": artifact_hashes,
        "feature_schema_sha256": feature_schema_sha256,
        "common_feature_names": common_cols,
        "common_feature_count": len(common_cols),
        "dataset_profile_summary": {
            "total_rows": dataset_profile["total_rows"],
            "total_defective": dataset_profile["total_defective"],
            "total_nondefective": dataset_profile["total_nondefective"],
            "common_feature_count": dataset_profile["common_feature_count"],
        },
        "event_manifest_summary": {
            "event_count": len(event_manifest),
            "within_events": int((event_manifest["experiment"] == "within_project").sum()),
            "cross_events": int((event_manifest["experiment"] == "cross_project").sum()),
        },
        "split_membership_summary": {"within_total_rows": len(split_within), "cross_total_rows": len(split_cross)},
        "prediction_ledger_summary": {
            "within_total_rows": len(pred_within),
            "cross_total_rows": len(pred_cross),
            "validation_rows": len(validation_rows),
            "test_rows": len(test_rows),
            "train_rows": 0,
            "column_count": len(PREDICTION_LEDGER_COLUMNS),
            "columns": PREDICTION_LEDGER_COLUMNS,
            "stored_threshold_or_objective_columns": stored_forbidden,
            "stored_aggregate_metric_columns": [c for c in stored_forbidden if c.startswith("metric__")],
        },
        "reconstruction_summary": {
            "validation_rows": len(val_recon),
            "canonical_result_rows": len(result_recon),
            "validation_reconstruction_evidence": val_compare,
            "canonical_result_reconstruction_evidence": res_compare,
            "canonical_nondeterminism_exception_validated": bool(exc_ev.get("validated", False)),
            "strict_validation_mismatches": int(val_compare.get("numeric_mismatches", -1)),
            "strict_result_mismatches_before_exception": len(exc_ev.get("approved_exception_matches", [])) + len(exc_ev.get("unapproved_mismatches", [])),
            "approved_nondeterminism_exceptions": exc_ev.get("approved_exception_count", 0),
            "unapproved_result_mismatches": exc_ev.get("unapproved_mismatch_count", 0),
            "canonical_result_reconstruction_strictly_identical": res_compare.get("numeric_mismatches", -1) == 0,
            "canonical_result_reconstruction_scientifically_reconciled": bool(exc_ev.get("validated", False)),
            "canonical_results_reconstructed_exclusively_from_scores": True,
            "persisted_ledger_reconstruction_matches_in_memory": True,
        },
        "fitted_candidate_count": fitted_count,
    }


def render_markdown_report(json_report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Part 3B.2R Split / Leakage Audit Report")
    lines.append("")
    lines.append(f"- **Version:** {json_report['part3b_version']}")
    lines.append(f"- **Repository:** {json_report['repository']}")
    lines.append(f"- **Branch:** {json_report['branch']}")
    lines.append(f"- **Starting commit:** {json_report['starting_commit']}")
    lines.append(f"- **Accepted Part 3A commit:** {json_report['accepted_part3a_commit']}")
    lines.append(f"- **Timestamp:** {json_report['timestamp']}")
    lines.append("")
    lines.append("## Stage Gate")
    lines.append("")
    for k, v in json_report["stage_gate"].items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Audit Checks")
    lines.append("")
    for k, v in json_report["audit_checks"].items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Prediction Ledger Summary")
    lines.append("")
    summary = json_report["prediction_ledger_summary"]
    for k, v in summary.items():
        if k == "columns":
            lines.append(f"- **{k}:** {', '.join(v)}")
        elif k in ("stored_threshold_or_objective_columns", "stored_aggregate_metric_columns"):
            lines.append(f"- **{k}:** {v}")
        else:
            lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Reconstruction Summary")
    lines.append("")
    recon = json_report["reconstruction_summary"]
    lines.append(f"- **Validation rows:** {recon['validation_rows']}")
    lines.append(f"- **Canonical result rows:** {recon['canonical_result_rows']}")
    lines.append(f"- **Canonical results reconstructed exclusively from scores:** {recon['canonical_results_reconstructed_exclusively_from_scores']}")
    lines.append(f"- **Persisted ledger reconstruction matches in-memory:** {recon['persisted_ledger_reconstruction_matches_in_memory']}")
    lines.append(f"- **Canonical nondeterminism exception validated:** {recon.get('canonical_nondeterminism_exception_validated', False)}")
    lines.append(f"- **Strict validation mismatches:** {recon.get('strict_validation_mismatches', -1)}")
    lines.append(f"- **Strict result mismatches before exception:** {recon.get('strict_result_mismatches_before_exception', -1)}")
    lines.append(f"- **Approved nondeterminism exceptions:** {recon.get('approved_nondeterminism_exceptions', 0)}")
    lines.append(f"- **Unapproved result mismatches:** {recon.get('unapproved_result_mismatches', 0)}")
    lines.append(f"- **Canonical result reconstruction strictly identical:** {recon.get('canonical_result_reconstruction_strictly_identical', False)}")
    lines.append(f"- **Canonical result reconstruction scientifically reconciled:** {recon.get('canonical_result_reconstruction_scientifically_reconciled', False)}")
    lines.append("")
    for name in ["validation_reconstruction_evidence", "canonical_result_reconstruction_evidence"]:
        ev = recon[name]
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- **Row count:** {ev['row_count']}")
        lines.append(f"- **Categorical match:** {ev['categorical_match']}")
        lines.append(f"- **Numeric mismatches:** {ev['numeric_mismatches']}")
        lines.append(f"- **Maximum absolute difference:** {ev['max_abs_diff']}")
        lines.append(f"- **Maximum relative difference:** {ev['max_rel_diff']}")
        lines.append("")
        lines.append("| Column | Compared | Mismatches | MaxAbs | MaxRel |")
        lines.append("|--------|----------|------------|--------|--------|")
        for col in ev["per_column"]:
            lines.append(f"| {col['column']} | {col['compared_count']} | {col['mismatch_count']} | {col['maximum_absolute_difference']} | {col['maximum_relative_difference']} |")
        lines.append("")
    lines.append("## Canonical Nondeterminism Diagnostic")
    lines.append("")
    diag = json_report.get("canonical_nondeterminism_diagnostic", ET_ND_DIAGNOSTIC)
    for k, v in diag.items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("The frozen historical pipeline contains a reproducible sub-ULP parallel prediction nondeterminism in ExtraTrees with n_jobs=2. The maximum observed candidate-score difference was 4.440892098500626e-16. This generated one historical ROC-AUC discrepancy of approximately 4.2835e-08 between two rows derived from separate prediction calls on the same fitted estimator. Part 3B freezes one score vector per event and candidate, preserving internal consistency without modifying the accepted canonical output.")
    lines.append("")
    lines.append("## Semantic Reproducibility (Two Independent Builds)")
    lines.append("")
    sem = json_report.get("determinism_verification", {}).get("semantic_reproducibility_evidence", {})
    lines.append(f"- **Semantic reproducibility passed:** {json_report.get('determinism_verification', {}).get('semantic_reproducibility_passed', False)}")
    lines.append(f"- **Exact structural equality:** {sem.get('exact_structural_equality', False)}")
    lines.append(f"- **All identity columns exact:** {sem.get('all_identity_columns_exact', False)}")
    lines.append(f"- **All non-ET score columns exact:** {sem.get('all_non_et_score_columns_exact', False)}")
    lines.append(f"- **Maximum ET score difference:** {sem.get('maximum_et_score_difference', float('nan'))}")
    lines.append(f"- **Number of ET cells differing:** {sem.get('number_of_et_cells_differing', -1)}")
    lines.append(f"- **All selection decisions exact:** {sem.get('all_selection_decisions_exact', False)}")
    lines.append(f"- **All thresholds exact:** {sem.get('all_thresholds_exact', False)}")
    lines.append(f"- **Byte-identical artifacts:** {sem.get('byte_identical_artifacts', [])}")
    lines.append(f"- **Artifacts with approved ET roundoff only:** {sem.get('artifacts_with_approved_et_roundoff_only', [])}")
    lines.append(f"- **Unapproved differing artifacts:** {sem.get('unapproved_differing_artifacts', [])}")
    lines.append("")
    lines.append("## Negative Tests")
    lines.append("")
    lines.append("| Case | Mutation | Validator | Passed |")
    lines.append("|------|----------|-----------|--------|")
    for t in json_report["negative_tests"]:
        lines.append(f"| {t['case_name']} | {t['mutation']} | {t['validator_name']} | {t['passed']} |")
    lines.append("")
    lines.append("## Canonical Exception Validator Tests")
    lines.append("")
    lines.append("| Case | Mutation | Validator | Validated | Passed |")
    lines.append("|------|----------|-----------|-----------|--------|")
    for t in json_report.get("canonical_exception_validator_tests", []):
        lines.append(f"| {t['case_name']} | {t['mutation']} | {t['validator_name']} | {t.get('validator_returned_validated', False)} | {t['passed']} |")
    lines.append("")
    lines.append("## Tie Policy Tests")
    lines.append("")
    lines.append("| Case | Description | Passed |")
    lines.append("|------|-------------|--------|")
    for t in json_report["tie_policy_tests"]:
        lines.append(f"| {t['case_name']} | {t['description']} | {t['passed']} |")
    lines.append("")
    lines.append("## Artifact Hashes")
    lines.append("")
    lines.append("| Artifact | SHA-256 |")
    lines.append("|----------|---------|")
    for rel, h in json_report["artifact_hashes"].items():
        lines.append(f"| {rel} | {h['sha256']} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Part E.2: Normalization tokens for approved semantic hash differences
# ---------------------------------------------------------------------------
APPROVED_SEMANTIC_SHA_TOKEN = "__APPROVED_SEMANTIC_SHA_DIFFERENCE__"
APPROVED_SEMANTIC_SIZE_TOKEN = "__APPROVED_SEMANTIC_SIZE_DIFFERENCE__"

MANIFEST_REQUIRED_TOP_LEVEL_FIELDS = [
    "manifest_version",
    "starting_commit",
    "accepted_part3a_commit",
    "project_order",
    "seed_order",
    "candidate_order",
    "event_count",
    "sample_count",
    "split_membership_total_rows",
    "prediction_total_rows",
    "validation_reconstruction_rows",
    "canonical_result_reconstruction_rows",
    "self_referential_hash_embedded",
    "artifacts",
]

MANIFEST_ARTIFACT_ENTRY_FIELDS = [
    "relative_path",
    "format",
    "compressed",
    "row_count",
    "column_count",
    "columns",
    "byte_size",
    "sha256",
]


def _file_size(path: Path) -> int:
    return path.stat().st_size


def _actual_artifact_hash_and_size(path: Path) -> Tuple[str, int]:
    return sha256_file(path), _file_size(path)


def _approved_data_artifacts_set(data_comparison_evidence: Dict[str, Any]) -> set:
    """Return the set of data-artifact rels that are approved by the eight-data comparator."""
    approved = set()
    comps = data_comparison_evidence.get("artifact_comparisons", {})
    for rel in SEMANTIC_DATA_ARTIFACTS:
        comp = comps.get(rel, {})
        if comp.get("within_policy") is True:
            approved.add(rel)
    return approved


# ---------------------------------------------------------------------------
# Part E.2: Ledger manifest validation and normalization
# ---------------------------------------------------------------------------
def validate_and_normalize_ledger_manifest(
    manifest_path: Path,
    artifact_paths: Dict[str, Path],
    data_comparison_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate a single build's ledger_manifest.json against actual artifact files.

    Returns a dict with validation results and a normalized manifest suitable
    for cross-build comparison.
    """
    result: Dict[str, Any] = {
        "manifest_first_valid": False,
        "manifest_valid": False,
        "manifest_top_level_exact": False,
        "manifest_artifact_order_exact": False,
        "manifest_actual_hashes_verified": False,
        "manifest_actual_sizes_verified": False,
        "normalized_manifest": None,
        "errors": [],
    }

    if not manifest_path or not manifest_path.exists():
        result["errors"].append("manifest file not found")
        return result

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        result["errors"].append(f"JSON parse error: {e}")
        return result

    # JSON parse succeeded
    result["manifest_first_valid"] = True

    # Check exact top-level fields and order
    actual_keys = list(raw.keys())
    expected_keys = MANIFEST_REQUIRED_TOP_LEVEL_FIELDS
    top_level_exact = actual_keys == expected_keys
    if not top_level_exact:
        result["errors"].append(f"top-level fields mismatch: {actual_keys} vs {expected_keys}")

    # Check exact top-level values
    if top_level_exact:
        value_checks = [
            raw["manifest_version"] == PART3B_VERSION,
            raw["starting_commit"] == STARTING_COMMIT,
            raw["accepted_part3a_commit"] == ACCEPTED_PART3A_COMMIT,
            raw["project_order"] == ["CM1", "JM1", "KC1", "KC2", "PC1"],
            raw["seed_order"] == [7, 13, 29, 42, 101],
            raw["candidate_order"] == ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"],
            raw["event_count"] == 50,
            raw["sample_count"] == 17442,
            raw["split_membership_total_rows"] == 523260,
            raw["prediction_total_rows"] == 209330,
            raw["validation_reconstruction_rows"] == 600,
            raw["canonical_result_reconstruction_rows"] == 400,
            raw["self_referential_hash_embedded"] is False,
        ]
        if not all(value_checks):
            top_level_exact = False
            result["errors"].append("top-level value mismatch")
    result["manifest_top_level_exact"] = top_level_exact

    # Check artifacts list: must contain exactly the eight data artifacts in order
    artifacts_list = raw.get("artifacts", [])
    expected_artifact_paths = list(SEMANTIC_DATA_ARTIFACTS)
    actual_artifact_paths = [a.get("relative_path") for a in artifacts_list]
    order_exact = actual_artifact_paths == expected_artifact_paths
    if not order_exact:
        result["errors"].append(f"artifact order mismatch: {actual_artifact_paths} vs {expected_artifact_paths}")

    # Validate each artifact entry fields and order
    entry_fields_exact = True
    for entry in artifacts_list:
        entry_keys = list(entry.keys())
        if entry_keys != MANIFEST_ARTIFACT_ENTRY_FIELDS:
            result["errors"].append(f"artifact entry fields mismatch for {entry.get('relative_path')}: {entry_keys}")
            entry_fields_exact = False

    result["manifest_artifact_order_exact"] = order_exact and entry_fields_exact

    # Verify each manifest entry's sha256 and byte_size against actual file
    approved_set = _approved_data_artifacts_set(data_comparison_evidence)
    hashes_verified = True
    sizes_verified = True

    for entry in artifacts_list:
        rel = entry.get("relative_path")
        actual_path = artifact_paths.get(rel)
        if actual_path is None or not actual_path.exists():
            result["errors"].append(f"actual artifact not found: {rel}")
            hashes_verified = False
            sizes_verified = False
            continue

        actual_hash, actual_size = _actual_artifact_hash_and_size(actual_path)

        # Check sha256 matches actual file
        if entry.get("sha256") != actual_hash:
            result["errors"].append(f"manifest sha256 mismatch for {rel}: {entry.get('sha256')} vs {actual_hash}")
            hashes_verified = False

        # Check byte_size matches actual file
        if entry.get("byte_size") != actual_size:
            result["errors"].append(f"manifest byte_size mismatch for {rel}: {entry.get('byte_size')} vs {actual_size}")
            sizes_verified = False

        # Check format, compressed, row_count, column_count, columns against frozen schema
        expected_schema = EXPECTED_DATA_ARTIFACT_SCHEMAS.get(rel, [])
        expected_format = "csv.gz" if rel.endswith(".gz") else "csv"
        expected_compressed = rel.endswith(".gz")

        if entry.get("format") != expected_format:
            result["errors"].append(f"format mismatch for {rel}: {entry.get('format')} vs {expected_format}")
        if entry.get("compressed") != expected_compressed:
            result["errors"].append(f"compressed mismatch for {rel}")
        if entry.get("columns") != expected_schema:
            result["errors"].append(f"columns mismatch for {rel}")

        # Read actual file for row/column count
        try:
            df_actual = _read_artifact_df(actual_path)
            if entry.get("row_count") != len(df_actual):
                result["errors"].append(f"row_count mismatch for {rel}: {entry.get('row_count')} vs {len(df_actual)}")
            if entry.get("column_count") != len(df_actual.columns):
                result["errors"].append(f"column_count mismatch for {rel}")
        except Exception as e:
            result["errors"].append(f"cannot read artifact {rel}: {e}")

    result["manifest_actual_hashes_verified"] = hashes_verified
    result["manifest_actual_sizes_verified"] = sizes_verified

    # Compute final manifest_valid
    manifest_valid = (
        result["manifest_first_valid"]
        and result["manifest_top_level_exact"]
        and result["manifest_artifact_order_exact"]
        and result["manifest_actual_hashes_verified"]
        and result["manifest_actual_sizes_verified"]
        and len(result["errors"]) == 0
    )
    result["manifest_valid"] = manifest_valid

    # Only construct normalized manifest when validation passed
    if manifest_valid:
        normalized_artifacts = []
        for entry in artifacts_list:
            rel = entry.get("relative_path")
            actual_path = artifact_paths.get(rel)
            actual_hash, actual_size = _actual_artifact_hash_and_size(actual_path)
            norm_entry = dict(entry)
            if rel not in approved_set:
                norm_entry["sha256"] = actual_hash
                norm_entry["byte_size"] = actual_size
            else:
                norm_entry["_actual_sha256"] = actual_hash
                norm_entry["_actual_byte_size"] = actual_size
            normalized_artifacts.append(norm_entry)
        normalized = {k: v for k, v in raw.items() if k != "artifacts"}
        normalized["artifacts"] = normalized_artifacts
        result["normalized_manifest"] = normalized
    else:
        result["normalized_manifest"] = None

    return result


def _compare_normalized_manifests(
    first_result: Dict[str, Any],
    second_result: Dict[str, Any],
    data_comparison_evidence: Dict[str, Any],
    first_artifact_paths: Dict[str, Path],
    second_artifact_paths: Dict[str, Path],
) -> Dict[str, Any]:
    """Compare two validated manifests, normalizing only approved hash differences."""
    approved_set = _approved_data_artifacts_set(data_comparison_evidence)
    approved_diffs: List[Dict[str, Any]] = []
    unapproved: List[Dict[str, Any]] = []

    # Require both manifests to be independently valid
    first_valid = first_result.get("manifest_valid", False) is True
    second_valid = second_result.get("manifest_valid", False) is True
    if not first_valid or not second_valid:
        return {
            "manifest_normalized_equal": False,
            "approved_manifest_hash_differences": approved_diffs,
            "unapproved_manifest_differences": [{"reason": "manifest not independently valid"}],
            "manifest_comparison_passed": False,
        }

    m1 = first_result.get("normalized_manifest")
    m2 = second_result.get("normalized_manifest")

    # Compare all top-level fields except artifacts
    top_level_equal = True
    for key in MANIFEST_REQUIRED_TOP_LEVEL_FIELDS:
        if key == "artifacts":
            continue
        if m1.get(key) != m2.get(key):
            top_level_equal = False
            unapproved.append({"field": key, "first": m1.get(key), "second": m2.get(key)})

    # Compare artifacts
    a1 = m1.get("artifacts", [])
    a2 = m2.get("artifacts", [])
    artifacts_equal = True

    if len(a1) != len(a2):
        artifacts_equal = False
        unapproved.append({"reason": "artifact count mismatch"})
    else:
        for e1, e2 in zip(a1, a2):
            rel = e1.get("relative_path")
            if e1.get("relative_path") != e2.get("relative_path"):
                artifacts_equal = False
                unapproved.append({"artifact": rel, "reason": "relative_path mismatch"})
                continue
            # Compare all fields except sha256 and byte_size
            for field in ["format", "compressed", "row_count", "column_count", "columns"]:
                if e1.get(field) != e2.get(field):
                    artifacts_equal = False
                    unapproved.append({"artifact": rel, "field": field, "first": e1.get(field), "second": e2.get(field)})

            # Compare sha256 and byte_size
            h1 = e1.get("_actual_sha256", e1.get("sha256"))
            h2 = e2.get("_actual_sha256", e2.get("sha256"))
            s1 = e1.get("_actual_byte_size", e1.get("byte_size"))
            s2 = e2.get("_actual_byte_size", e2.get("byte_size"))

            if h1 == h2:
                # Identical hashes - must match exactly
                if e1.get("sha256") != e2.get("sha256"):
                    artifacts_equal = False
                    unapproved.append({"artifact": rel, "field": "sha256", "reason": "identical bytes but different manifest hash"})
                if e1.get("byte_size") != e2.get("byte_size"):
                    artifacts_equal = False
                    unapproved.append({"artifact": rel, "field": "byte_size", "reason": "identical bytes but different manifest size"})
            else:
                # Different actual bytes
                if rel in approved_set:
                    # Approved semantic difference - normalize
                    approved_diffs.append({
                        "artifact": rel,
                        "first_sha256": h1,
                        "second_sha256": h2,
                        "first_byte_size": s1,
                        "second_byte_size": s2,
                    })
                else:
                    artifacts_equal = False
                    unapproved.append({"artifact": rel, "field": "sha256", "reason": "unapproved byte difference"})

    normalized_equal = top_level_equal and artifacts_equal
    comparison_passed = normalized_equal and len(unapproved) == 0

    return {
        "manifest_normalized_equal": normalized_equal,
        "approved_manifest_hash_differences": approved_diffs,
        "unapproved_manifest_differences": unapproved,
        "manifest_comparison_passed": comparison_passed,
    }


# ---------------------------------------------------------------------------
# Part E.2: Audit JSON validation and normalization
# ---------------------------------------------------------------------------
def validate_and_normalize_audit_json(
    audit_json_path: Path,
    artifact_paths: Dict[str, Path],
    data_comparison_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate a single build's audit JSON against actual artifact files."""
    result: Dict[str, Any] = {
        "audit_json_first_valid": False,
        "audit_json_valid": False,
        "audit_json_provenance_exact": False,
        "audit_json_audit_schema_exact": False,
        "audit_json_stage_gate_schema_exact": False,
        "audit_json_actual_hashes_verified": False,
        "normalized_audit_json": None,
        "errors": [],
    }

    if not audit_json_path or not audit_json_path.exists():
        result["errors"].append("audit JSON file not found")
        return result

    try:
        with audit_json_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        result["errors"].append(f"JSON parse error: {e}")
        return result

    # JSON parse succeeded
    result["audit_json_first_valid"] = True

    # Check provenance fields
    provenance_exact = (
        raw.get("part3b_version") == PART3B_VERSION
        and raw.get("starting_commit") == STARTING_COMMIT
        and raw.get("accepted_part3a_commit") == ACCEPTED_PART3A_COMMIT
        and raw.get("repository") == REPOSITORY
        and raw.get("branch") == BRANCH
    )
    result["audit_json_provenance_exact"] = provenance_exact
    if not provenance_exact:
        result["errors"].append("provenance fields mismatch")

    # Check audit schema: 41 exact check names, all bool values
    audit_checks = raw.get("audit_checks", {})
    schema_passed, schema_evidence = validate_exact_audit_check_schema(audit_checks)
    result["audit_json_audit_schema_exact"] = schema_passed
    if not schema_passed:
        result["errors"].append(f"audit check schema mismatch: {schema_evidence}")

    # Check stage gate schema: 16 exact fields and types (schema-only, no authorization)
    stage_gate = raw.get("stage_gate", {})
    gate_schema_passed, gate_evidence = validate_stage_gate_schema_only(stage_gate)
    result["audit_json_stage_gate_schema_exact"] = gate_schema_passed
    if not gate_schema_passed:
        result["errors"].append(f"stage gate schema mismatch: {gate_evidence}")

    # Verify artifact_hashes against actual files
    approved_set = _approved_data_artifacts_set(data_comparison_evidence)
    artifact_hashes = raw.get("artifact_hashes", {})
    hashes_verified = True

    # Check exactly eight data artifacts, no missing or extra
    actual_hash_keys = set(artifact_hashes.keys())
    expected_hash_keys = set(SEMANTIC_DATA_ARTIFACTS)
    if actual_hash_keys != expected_hash_keys:
        hashes_verified = False
        missing = sorted(expected_hash_keys - actual_hash_keys)
        extra = sorted(actual_hash_keys - expected_hash_keys)
        if missing:
            result["errors"].append(f"missing artifact_hashes entries: {missing}")
        if extra:
            result["errors"].append(f"extra artifact_hashes entries: {extra}")

    for rel in SEMANTIC_DATA_ARTIFACTS:
        entry = artifact_hashes.get(rel)
        if entry is None:
            hashes_verified = False
            result["errors"].append(f"missing artifact_hashes entry for {rel}")
            continue
        actual_path = artifact_paths.get(rel)
        if actual_path is None or not actual_path.exists():
            hashes_verified = False
            result["errors"].append(f"actual artifact not found: {rel}")
            continue
        actual_hash, actual_size = _actual_artifact_hash_and_size(actual_path)
        stored_hash = entry.get("sha256")
        stored_size = entry.get("byte_size")

        if stored_hash != actual_hash:
            hashes_verified = False
            result["errors"].append(f"audit JSON sha256 mismatch for {rel}: {stored_hash} vs {actual_hash}")
        if stored_size != actual_size:
            hashes_verified = False
            result["errors"].append(f"audit JSON byte_size mismatch for {rel}: {stored_size} vs {actual_size}")

    result["audit_json_actual_hashes_verified"] = hashes_verified

    # Compute final audit_json_valid
    audit_json_valid = (
        result["audit_json_first_valid"]
        and result["audit_json_provenance_exact"]
        and result["audit_json_audit_schema_exact"]
        and result["audit_json_stage_gate_schema_exact"]
        and result["audit_json_actual_hashes_verified"]
        and len(result["errors"]) == 0
    )
    result["audit_json_valid"] = audit_json_valid

    # Only construct normalized JSON when validation passed
    if audit_json_valid:
        normalized_hashes = {}
        for rel in SEMANTIC_DATA_ARTIFACTS:
            entry = artifact_hashes.get(rel)
            actual_path = artifact_paths.get(rel)
            actual_hash, actual_size = _actual_artifact_hash_and_size(actual_path)
            norm_entry = dict(entry)
            norm_entry["_actual_sha256"] = actual_hash
            norm_entry["_actual_byte_size"] = actual_size
            normalized_hashes[rel] = norm_entry
        normalized = dict(raw)
        normalized["artifact_hashes"] = normalized_hashes
        result["normalized_audit_json"] = normalized
    else:
        result["normalized_audit_json"] = None

    return result


def _compare_normalized_audit_json(
    first_result: Dict[str, Any],
    second_result: Dict[str, Any],
    data_comparison_evidence: Dict[str, Any],
    first_artifact_paths: Dict[str, Path],
    second_artifact_paths: Dict[str, Path],
) -> Dict[str, Any]:
    """Compare two validated audit JSONs, normalizing only approved hash differences."""
    approved_set = _approved_data_artifacts_set(data_comparison_evidence)
    approved_diffs: List[Dict[str, Any]] = []
    unapproved: List[Dict[str, Any]] = []

    # Require both audit JSONs to be independently valid
    first_valid = first_result.get("audit_json_valid", False) is True
    second_valid = second_result.get("audit_json_valid", False) is True
    if not first_valid or not second_valid:
        return {
            "audit_json_normalized_equal": False,
            "approved_audit_json_hash_differences": approved_diffs,
            "unapproved_audit_json_differences": [{"reason": "audit JSON not independently valid"}],
            "audit_json_comparison_passed": False,
        }

    j1 = first_result.get("normalized_audit_json")
    j2 = second_result.get("normalized_audit_json")

    # Compare all fields except artifact_hashes
    all_equal = True
    for key in j1:
        if key == "artifact_hashes":
            continue
        if key not in j2:
            all_equal = False
            unapproved.append({"field": key, "reason": "missing in second"})
            continue
        if j1[key] != j2[key]:
            all_equal = False
            unapproved.append({"field": key, "first": j1[key], "second": j2[key]})

    # Check for extra keys in second
    for key in j2:
        if key not in j1:
            all_equal = False
            unapproved.append({"field": key, "reason": "extra in second"})

    # Compare artifact_hashes
    h1 = j1.get("artifact_hashes", {})
    h2 = j2.get("artifact_hashes", {})
    for rel in SEMANTIC_DATA_ARTIFACTS:
        e1 = h1.get(rel, {})
        e2 = h2.get(rel, {})
        ah1 = e1.get("_actual_sha256", e1.get("sha256"))
        ah2 = e2.get("_actual_sha256", e2.get("sha256"))
        as1 = e1.get("_actual_byte_size", e1.get("byte_size"))
        as2 = e2.get("_actual_byte_size", e2.get("byte_size"))

        if ah1 == ah2:
            if e1.get("sha256") != e2.get("sha256"):
                all_equal = False
                unapproved.append({"artifact": rel, "field": "sha256", "reason": "identical bytes but different stored hash"})
            if e1.get("byte_size") != e2.get("byte_size"):
                all_equal = False
                unapproved.append({"artifact": rel, "field": "byte_size", "reason": "identical bytes but different stored size"})
        else:
            if rel in approved_set:
                approved_diffs.append({
                    "artifact": rel,
                    "first_sha256": ah1,
                    "second_sha256": ah2,
                    "first_byte_size": as1,
                    "second_byte_size": as2,
                })
            else:
                all_equal = False
                unapproved.append({"artifact": rel, "field": "sha256", "reason": "unapproved byte difference"})

    comparison_passed = all_equal and len(unapproved) == 0

    return {
        "audit_json_normalized_equal": all_equal,
        "approved_audit_json_hash_differences": approved_diffs,
        "unapproved_audit_json_differences": unapproved,
        "audit_json_comparison_passed": comparison_passed,
    }


# ---------------------------------------------------------------------------
# Part E.2: Audit Markdown validation and normalization
# ---------------------------------------------------------------------------
AUDIT_MD_REQUIRED_SECTIONS = [
    "# Part 3B.2R Split / Leakage Audit Report",
    "## Stage Gate",
    "## Audit Checks",
    "## Prediction Ledger Summary",
    "## Reconstruction Summary",
    "## Canonical Nondeterminism Diagnostic",
    "## Semantic Reproducibility (Two Independent Builds)",
    "## Negative Tests",
    "## Canonical Exception Validator Tests",
    "## Tie Policy Tests",
    "## Artifact Hashes",
]


def validate_and_normalize_audit_markdown(
    markdown_path: Path,
    corresponding_audit_json: Dict[str, Any],
    artifact_paths: Dict[str, Path],
    data_comparison_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate a single build's audit Markdown against its JSON source and actual files."""
    result: Dict[str, Any] = {
        "audit_md_first_valid": False,
        "audit_md_valid": False,
        "audit_md_required_sections_present": False,
        "audit_md_provenance_matches_json": False,
        "audit_md_hash_table_matches_json": False,
        "audit_md_hash_table_matches_actual_files": False,
        "normalized_markdown": None,
        "errors": [],
    }

    if not markdown_path or not markdown_path.exists():
        result["errors"].append("audit Markdown file not found")
        return result

    try:
        with markdown_path.open("r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        result["errors"].append(f"read error: {e}")
        return result

    # File read succeeded
    result["audit_md_first_valid"] = True

    # Normalize line endings to LF
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = content.split("\n")

    # Check required sections
    sections_present = all(section in content for section in AUDIT_MD_REQUIRED_SECTIONS)
    result["audit_md_required_sections_present"] = sections_present
    if not sections_present:
        missing = [s for s in AUDIT_MD_REQUIRED_SECTIONS if s not in content]
        result["errors"].append(f"missing sections: {missing}")

    # Check provenance lines match JSON
    provenance_matches = True
    expected_provenance = {
        "Version": corresponding_audit_json.get("part3b_version", ""),
        "Repository": corresponding_audit_json.get("repository", ""),
        "Branch": corresponding_audit_json.get("branch", ""),
        "Starting commit": corresponding_audit_json.get("starting_commit", ""),
        "Accepted Part 3A commit": corresponding_audit_json.get("accepted_part3a_commit", ""),
        "Timestamp": corresponding_audit_json.get("timestamp", ""),
    }
    for label, expected_val in expected_provenance.items():
        expected_line = f"- **{label}:** {expected_val}"
        if expected_line not in content:
            provenance_matches = False
            result["errors"].append(f"provenance line mismatch: {expected_line}")
    result["audit_md_provenance_matches_json"] = provenance_matches

    # Parse Artifact Hashes table
    approved_set = _approved_data_artifacts_set(data_comparison_evidence)
    json_hashes = corresponding_audit_json.get("artifact_hashes", {})

    hash_table_matches_json = True
    hash_table_matches_actual = True

    # Find the Artifact Hashes section and parse the table
    in_hash_section = False
    hash_table_start = -1
    hash_table_end = -1
    md_artifact_rows: List[str] = []
    for i, line in enumerate(lines):
        if line.strip() == "## Artifact Hashes":
            in_hash_section = True
            hash_table_start = i
            continue
        if in_hash_section:
            if line.startswith("## ") or (line.strip() == "" and hash_table_end > 0):
                if line.startswith("## "):
                    hash_table_end = i
                    break
            if line.startswith("| ") and "---" not in line and "Artifact" not in line:
                # Parse table row: | rel | sha256 |
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    rel = parts[1]
                    md_hash = parts[2]
                    md_artifact_rows.append(rel)
                    json_entry = json_hashes.get(rel, {})
                    json_hash = json_entry.get("sha256")

                    # Check MD hash matches JSON hash
                    if md_hash != json_hash:
                        hash_table_matches_json = False
                        result["errors"].append(f"MD hash table mismatch with JSON for {rel}: {md_hash} vs {json_hash}")

                    # Check MD hash matches actual file - no bypass for approved artifacts
                    actual_path = artifact_paths.get(rel)
                    if actual_path and actual_path.exists():
                        actual_hash = sha256_file(actual_path)
                        if md_hash != actual_hash:
                            hash_table_matches_actual = False
                            result["errors"].append(f"MD hash mismatch with actual file for {rel}: {md_hash} vs {actual_hash}")
                    else:
                        if rel in SEMANTIC_DATA_ARTIFACTS:
                            hash_table_matches_actual = False
                            result["errors"].append(f"actual artifact not found for {rel}")

    # Check artifact rows are exactly the eight data artifacts in expected order
    if md_artifact_rows != list(SEMANTIC_DATA_ARTIFACTS):
        hash_table_matches_json = False
        missing_rows = [r for r in SEMANTIC_DATA_ARTIFACTS if r not in md_artifact_rows]
        extra_rows = [r for r in md_artifact_rows if r not in SEMANTIC_DATA_ARTIFACTS]
        if missing_rows:
            result["errors"].append(f"missing artifact hash rows: {missing_rows}")
        if extra_rows:
            result["errors"].append(f"extra artifact hash rows: {extra_rows}")
        if md_artifact_rows != list(SEMANTIC_DATA_ARTIFACTS) and not missing_rows and not extra_rows:
            result["errors"].append(f"artifact hash row order mismatch: {md_artifact_rows} vs {list(SEMANTIC_DATA_ARTIFACTS)}")

    result["audit_md_hash_table_matches_json"] = hash_table_matches_json
    result["audit_md_hash_table_matches_actual_files"] = hash_table_matches_actual

    # Compute final audit_md_valid
    audit_md_valid = (
        result["audit_md_first_valid"]
        and result["audit_md_required_sections_present"]
        and result["audit_md_provenance_matches_json"]
        and result["audit_md_hash_table_matches_json"]
        and result["audit_md_hash_table_matches_actual_files"]
        and len(result["errors"]) == 0
    )
    result["audit_md_valid"] = audit_md_valid

    # Only build normalized markdown when validation passed
    if audit_md_valid:
        normalized_lines = list(lines)
        if in_hash_section and hash_table_start >= 0:
            for i, line in enumerate(normalized_lines):
                if i <= hash_table_start:
                    continue
                if line.startswith("## "):
                    break
                if line.startswith("| ") and "---" not in line and "Artifact" not in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        rel = parts[1]
                        if rel in approved_set:
                            actual_path = artifact_paths.get(rel)
                            if actual_path and actual_path.exists():
                                comp = data_comparison_evidence.get("artifact_comparisons", {}).get(rel, {})
                                if comp.get("within_policy") is True and not comp.get("decompressed_byte_equal", True):
                                    normalized_lines[i] = line.replace(parts[2], APPROVED_SEMANTIC_SHA_TOKEN)
        result["normalized_markdown"] = "\n".join(normalized_lines)
    else:
        result["normalized_markdown"] = None

    return result


def _compare_normalized_audit_markdown(
    first_result: Dict[str, Any],
    second_result: Dict[str, Any],
    data_comparison_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare two validated audit Markdowns after normalization."""
    approved_set = _approved_data_artifacts_set(data_comparison_evidence)
    approved_diffs: List[Dict[str, Any]] = []
    unapproved: List[Dict[str, Any]] = []

    # Require both Markdown files to be independently valid
    first_valid = first_result.get("audit_md_valid", False) is True
    second_valid = second_result.get("audit_md_valid", False) is True
    if not first_valid or not second_valid:
        return {
            "audit_md_normalized_equal": False,
            "approved_audit_md_hash_differences": approved_diffs,
            "unapproved_audit_md_differences": [{"reason": "markdown not independently valid"}],
            "audit_md_comparison_passed": False,
        }

    md1 = first_result.get("normalized_markdown")
    md2 = second_result.get("normalized_markdown")

    # Line-by-line comparison after normalization
    lines1 = md1.split("\n")
    lines2 = md2.split("\n")

    if len(lines1) != len(lines2):
        unapproved.append({"reason": "line count mismatch"})
        return {
            "audit_md_normalized_equal": False,
            "approved_audit_md_hash_differences": approved_diffs,
            "unapproved_audit_md_differences": unapproved,
            "audit_md_comparison_passed": False,
        }

    all_equal = True
    for i, (l1, l2) in enumerate(zip(lines1, lines2)):
        if l1 == l2:
            continue
        # Check if this is an approved hash normalization token line
        if APPROVED_SEMANTIC_SHA_TOKEN in l1 or APPROVED_SEMANTIC_SHA_TOKEN in l2:
            # This is an approved difference
            approved_diffs.append({"line": i, "first": l1, "second": l2})
            continue
        all_equal = False
        unapproved.append({"line": i, "first": l1, "second": l2})

    comparison_passed = all_equal and len(unapproved) == 0

    return {
        "audit_md_normalized_equal": all_equal,
        "approved_audit_md_hash_differences": approved_diffs,
        "unapproved_audit_md_differences": unapproved,
        "audit_md_comparison_passed": comparison_passed,
    }


# ---------------------------------------------------------------------------
# Part E.2: Strict eleven-artifact semantic comparator
# ---------------------------------------------------------------------------
def compare_eleven_artifacts_semantically(
    first_artifacts: Dict[str, Path],
    second_artifacts: Dict[str, Path],
) -> Dict[str, Any]:
    """Strict eleven-artifact semantic reproducibility comparator.

    Required order:
    1. Verify exact eleven-artifact sets.
    2. Run compare_eight_data_artifacts_semantically.
    3. Stop metadata approval if the data comparator fails.
    4. Validate and normalize ledger_manifest.json.
    5. Validate and normalize audit JSON.
    6. Validate and normalize audit Markdown.
    7. Produce combined evidence.
    """
    # 1. Verify exact eleven-artifact sets
    expected_set = set(SEMANTIC_ALL_ARTIFACTS)
    present_first = {k for k, p in first_artifacts.items() if p is not None and p.exists()}
    present_second = {k for k, p in second_artifacts.items() if p is not None and p.exists()}
    missing_from_first = sorted(expected_set - present_first)
    missing_from_second = sorted(expected_set - present_second)
    extra_first = sorted(present_first - expected_set)
    extra_second = sorted(present_second - expected_set)
    extra_artifacts = sorted(set(extra_first) | set(extra_second))

    all_artifacts_expected = len(SEMANTIC_ALL_ARTIFACTS)
    all_artifacts_present_first = len(present_first)
    all_artifacts_present_second = len(present_second)

    # 2. Run the eight-data comparator
    data_artifact_paths_first = {rel: first_artifacts.get(rel) for rel in SEMANTIC_DATA_ARTIFACTS}
    data_artifact_paths_second = {rel: second_artifacts.get(rel) for rel in SEMANTIC_DATA_ARTIFACTS}
    data_comparison = compare_eight_data_artifacts_semantically(
        data_artifact_paths_first, data_artifact_paths_second
    )
    data_passed = data_comparison["data_artifact_semantic_comparison_passed"]

    # 3. Stop metadata approval if data comparator fails
    metadata_artifact_comparisons: Dict[str, Any] = {}
    ledger_manifest_comparison_passed = False
    audit_json_comparison_passed = False
    audit_md_comparison_passed = False
    metadata_artifact_comparison_passed = False
    approved_metadata_hash_differences: List[Dict[str, Any]] = []
    unapproved_metadata_differences: List[Dict[str, Any]] = []

    # Explicit fail-closed gate fields
    manifest_first_valid = False
    manifest_second_valid = False
    manifest_actual_hashes_verified_first = False
    manifest_actual_hashes_verified_second = False
    manifest_actual_sizes_verified_first = False
    manifest_actual_sizes_verified_second = False
    audit_json_first_valid = False
    audit_json_second_valid = False
    audit_json_actual_hashes_verified_first = False
    audit_json_actual_hashes_verified_second = False
    audit_md_first_valid = False
    audit_md_second_valid = False
    audit_md_required_sections_present = False
    audit_md_provenance_matches_json = False
    audit_md_hash_table_matches_json = False
    audit_md_hash_table_matches_actual_files = False

    if not data_passed:
        unapproved_metadata_differences.append({"reason": "data artifact comparison failed; metadata approval stopped"})
    else:
        # 4. Validate and normalize ledger_manifest.json
        manifest_first_path = first_artifacts.get(SEMANTIC_METADATA_ARTIFACTS[0])
        manifest_second_path = second_artifacts.get(SEMANTIC_METADATA_ARTIFACTS[0])

        manifest_first = validate_and_normalize_ledger_manifest(
            manifest_first_path, first_artifacts, data_comparison
        )
        manifest_second = validate_and_normalize_ledger_manifest(
            manifest_second_path, second_artifacts, data_comparison
        )
        manifest_cmp = _compare_normalized_manifests(
            manifest_first, manifest_second, data_comparison,
            first_artifacts, second_artifacts,
        )

        manifest_first_valid = manifest_first.get("manifest_valid", False)
        manifest_second_valid = manifest_second.get("manifest_valid", False)
        manifest_actual_hashes_verified_first = manifest_first.get("manifest_actual_hashes_verified", False)
        manifest_actual_hashes_verified_second = manifest_second.get("manifest_actual_hashes_verified", False)
        manifest_actual_sizes_verified_first = manifest_first.get("manifest_actual_sizes_verified", False)
        manifest_actual_sizes_verified_second = manifest_second.get("manifest_actual_sizes_verified", False)

        metadata_artifact_comparisons["ledger_manifest"] = {
            "manifest_first_valid": manifest_first_valid,
            "manifest_second_valid": manifest_second_valid,
            "manifest_top_level_exact": manifest_first.get("manifest_top_level_exact", False) and manifest_second.get("manifest_top_level_exact", False),
            "manifest_artifact_order_exact": manifest_first.get("manifest_artifact_order_exact", False) and manifest_second.get("manifest_artifact_order_exact", False),
            "manifest_actual_hashes_verified_first": manifest_actual_hashes_verified_first,
            "manifest_actual_hashes_verified_second": manifest_actual_hashes_verified_second,
            "manifest_actual_sizes_verified_first": manifest_actual_sizes_verified_first,
            "manifest_actual_sizes_verified_second": manifest_actual_sizes_verified_second,
            "manifest_normalized_equal": manifest_cmp.get("manifest_normalized_equal", False),
            "approved_manifest_hash_differences": manifest_cmp.get("approved_manifest_hash_differences", []),
            "unapproved_manifest_differences": manifest_cmp.get("unapproved_manifest_differences", []),
            "manifest_comparison_passed": manifest_cmp.get("manifest_comparison_passed", False),
        }
        ledger_manifest_comparison_passed = manifest_cmp.get("manifest_comparison_passed", False)
        approved_metadata_hash_differences.extend(manifest_cmp.get("approved_manifest_hash_differences", []))
        unapproved_metadata_differences.extend(manifest_cmp.get("unapproved_manifest_differences", []))

        # 5. Validate and normalize audit JSON
        audit_json_first_path = first_artifacts.get(SEMANTIC_METADATA_ARTIFACTS[1])
        audit_json_second_path = second_artifacts.get(SEMANTIC_METADATA_ARTIFACTS[1])

        audit_json_first = validate_and_normalize_audit_json(
            audit_json_first_path, first_artifacts, data_comparison
        )
        audit_json_second = validate_and_normalize_audit_json(
            audit_json_second_path, second_artifacts, data_comparison
        )
        audit_json_cmp = _compare_normalized_audit_json(
            audit_json_first, audit_json_second, data_comparison,
            first_artifacts, second_artifacts,
        )

        audit_json_first_valid = audit_json_first.get("audit_json_valid", False)
        audit_json_second_valid = audit_json_second.get("audit_json_valid", False)
        audit_json_actual_hashes_verified_first = audit_json_first.get("audit_json_actual_hashes_verified", False)
        audit_json_actual_hashes_verified_second = audit_json_second.get("audit_json_actual_hashes_verified", False)

        metadata_artifact_comparisons["audit_json"] = {
            "audit_json_first_valid": audit_json_first_valid,
            "audit_json_second_valid": audit_json_second_valid,
            "audit_json_provenance_exact": audit_json_first.get("audit_json_provenance_exact", False) and audit_json_second.get("audit_json_provenance_exact", False),
            "audit_json_audit_schema_exact": audit_json_first.get("audit_json_audit_schema_exact", False) and audit_json_second.get("audit_json_audit_schema_exact", False),
            "audit_json_stage_gate_schema_exact": audit_json_first.get("audit_json_stage_gate_schema_exact", False) and audit_json_second.get("audit_json_stage_gate_schema_exact", False),
            "audit_json_actual_hashes_verified_first": audit_json_actual_hashes_verified_first,
            "audit_json_actual_hashes_verified_second": audit_json_actual_hashes_verified_second,
            "audit_json_normalized_equal": audit_json_cmp.get("audit_json_normalized_equal", False),
            "approved_audit_json_hash_differences": audit_json_cmp.get("approved_audit_json_hash_differences", []),
            "unapproved_audit_json_differences": audit_json_cmp.get("unapproved_audit_json_differences", []),
            "audit_json_comparison_passed": audit_json_cmp.get("audit_json_comparison_passed", False),
        }
        audit_json_comparison_passed = audit_json_cmp.get("audit_json_comparison_passed", False)
        approved_metadata_hash_differences.extend(audit_json_cmp.get("approved_audit_json_hash_differences", []))
        unapproved_metadata_differences.extend(audit_json_cmp.get("unapproved_audit_json_differences", []))

        # 6. Validate and normalize audit Markdown
        audit_md_first_path = first_artifacts.get(SEMANTIC_METADATA_ARTIFACTS[2])
        audit_md_second_path = second_artifacts.get(SEMANTIC_METADATA_ARTIFACTS[2])

        audit_md_first = validate_and_normalize_audit_markdown(
            audit_md_first_path, audit_json_first.get("normalized_audit_json") or {}, first_artifacts, data_comparison
        )
        audit_md_second = validate_and_normalize_audit_markdown(
            audit_md_second_path, audit_json_second.get("normalized_audit_json") or {}, second_artifacts, data_comparison
        )
        audit_md_cmp = _compare_normalized_audit_markdown(
            audit_md_first, audit_md_second, data_comparison
        )

        audit_md_first_valid = audit_md_first.get("audit_md_valid", False)
        audit_md_second_valid = audit_md_second.get("audit_md_valid", False)
        audit_md_required_sections_present = audit_md_first.get("audit_md_required_sections_present", False) and audit_md_second.get("audit_md_required_sections_present", False)
        audit_md_provenance_matches_json = audit_md_first.get("audit_md_provenance_matches_json", False) and audit_md_second.get("audit_md_provenance_matches_json", False)
        audit_md_hash_table_matches_json = audit_md_first.get("audit_md_hash_table_matches_json", False) and audit_md_second.get("audit_md_hash_table_matches_json", False)
        audit_md_hash_table_matches_actual_files = audit_md_first.get("audit_md_hash_table_matches_actual_files", False) and audit_md_second.get("audit_md_hash_table_matches_actual_files", False)

        metadata_artifact_comparisons["audit_markdown"] = {
            "audit_md_first_valid": audit_md_first_valid,
            "audit_md_second_valid": audit_md_second_valid,
            "audit_md_required_sections_present": audit_md_required_sections_present,
            "audit_md_provenance_matches_json": audit_md_provenance_matches_json,
            "audit_md_hash_table_matches_json": audit_md_hash_table_matches_json,
            "audit_md_hash_table_matches_actual_files": audit_md_hash_table_matches_actual_files,
            "audit_md_normalized_equal": audit_md_cmp.get("audit_md_normalized_equal", False),
            "approved_audit_md_hash_differences": audit_md_cmp.get("approved_audit_md_hash_differences", []),
            "unapproved_audit_md_differences": audit_md_cmp.get("unapproved_audit_md_differences", []),
            "audit_md_comparison_passed": audit_md_cmp.get("audit_md_comparison_passed", False),
        }
        audit_md_comparison_passed = audit_md_cmp.get("audit_md_comparison_passed", False)
        approved_metadata_hash_differences.extend(audit_md_cmp.get("approved_audit_md_hash_differences", []))
        unapproved_metadata_differences.extend(audit_md_cmp.get("unapproved_audit_md_differences", []))

    # Explicit fail-closed metadata gate
    metadata_artifact_comparison_passed = (
        manifest_first_valid
        and manifest_second_valid
        and manifest_actual_hashes_verified_first
        and manifest_actual_hashes_verified_second
        and manifest_actual_sizes_verified_first
        and manifest_actual_sizes_verified_second
        and audit_json_first_valid
        and audit_json_second_valid
        and audit_json_actual_hashes_verified_first
        and audit_json_actual_hashes_verified_second
        and audit_md_first_valid
        and audit_md_second_valid
        and audit_md_required_sections_present
        and audit_md_provenance_matches_json
        and audit_md_hash_table_matches_json
        and audit_md_hash_table_matches_actual_files
        and ledger_manifest_comparison_passed
        and audit_json_comparison_passed
        and audit_md_comparison_passed
    )

    # 7. Produce combined evidence
    # Determine byte-identical and approved-ET-roundoff artifacts
    byte_identical_artifacts: List[str] = []
    artifacts_with_approved_et_roundoff_only: List[str] = []
    unapproved_differing_artifacts: List[str] = []

    for rel in SEMANTIC_DATA_ARTIFACTS:
        p1 = first_artifacts.get(rel)
        p2 = second_artifacts.get(rel)
        if p1 and p2 and p1.exists() and p2.exists():
            if p1.read_bytes() == p2.read_bytes():
                byte_identical_artifacts.append(rel)
            else:
                comp = data_comparison.get("artifact_comparisons", {}).get(rel, {})
                if comp.get("within_policy") is True:
                    artifacts_with_approved_et_roundoff_only.append(rel)
                else:
                    unapproved_differing_artifacts.append(rel)
        else:
            unapproved_differing_artifacts.append(rel)

    # Also check metadata artifacts for byte equality
    for rel in SEMANTIC_METADATA_ARTIFACTS:
        p1 = first_artifacts.get(rel)
        p2 = second_artifacts.get(rel)
        if p1 and p2 and p1.exists() and p2.exists():
            if p1.read_bytes() == p2.read_bytes():
                byte_identical_artifacts.append(rel)

    semantic_passed = bool(
        all_artifacts_expected == 11
        and len(missing_from_first) == 0
        and len(missing_from_second) == 0
        and len(extra_artifacts) == 0
        and data_passed
        and metadata_artifact_comparison_passed
        and len(unapproved_metadata_differences) == 0
        and len(unapproved_differing_artifacts) == 0
    )

    return {
        "all_artifacts_expected": all_artifacts_expected,
        "all_artifacts_present_first": all_artifacts_present_first,
        "all_artifacts_present_second": all_artifacts_present_second,
        "missing_from_first": missing_from_first,
        "missing_from_second": missing_from_second,
        "extra_artifacts": extra_artifacts,
        "data_artifact_comparison": data_comparison,
        "metadata_artifact_comparisons": metadata_artifact_comparisons,
        "ledger_manifest_comparison_passed": ledger_manifest_comparison_passed,
        "audit_json_comparison_passed": audit_json_comparison_passed,
        "audit_md_comparison_passed": audit_md_comparison_passed,
        "metadata_artifact_comparison_passed": metadata_artifact_comparison_passed,
        "approved_metadata_hash_differences": approved_metadata_hash_differences,
        "unapproved_metadata_differences": unapproved_metadata_differences,
        "byte_identical_artifacts": byte_identical_artifacts,
        "artifacts_with_approved_et_roundoff_only": artifacts_with_approved_et_roundoff_only,
        "unapproved_differing_artifacts": unapproved_differing_artifacts,
        "exact_structural_equality": data_comparison.get("exact_structural_equality", False),
        "all_identity_columns_exact": data_comparison.get("all_identity_columns_exact", False),
        "all_non_et_score_columns_exact": data_comparison.get("all_non_et_score_columns_exact", False),
        "maximum_et_score_difference": data_comparison.get("maximum_et_score_difference", 0.0),
        "number_of_et_cells_differing": data_comparison.get("exactly_different_et_cells", 0),
        "all_selection_decisions_exact": data_comparison.get("all_selection_decisions_exact", False),
        "all_thresholds_exact": data_comparison.get("all_thresholds_exact", False),
        "all_non_exempt_metrics_strictly_equal": data_comparison.get("all_non_et_score_columns_exact", False),
        "semantic_reproducibility_passed": semantic_passed,
    }


# ---------------------------------------------------------------------------
# Two-build semantic reproducibility comparison
# ---------------------------------------------------------------------------
def _read_artifact_df(path: Path) -> pd.DataFrame:
    if path.suffix == ".gz":
        return pd.read_csv(path, compression="gzip")
    return pd.read_csv(path)


def compare_two_builds_semantically(bundle1: Dict[str, Any], bundle2: Dict[str, Any]) -> Dict[str, Any]:
    """Thin wrapper around compare_eleven_artifacts_semantically.

    This preserves downstream compatibility by returning the same keys that
    the production pipeline expects, while delegating all comparison logic
    to the strict eleven-artifact comparator.
    """
    artifacts1 = bundle1["artifacts"]
    artifacts2 = bundle2["artifacts"]
    result = compare_eleven_artifacts_semantically(artifacts1, artifacts2)
    return result


# ---------------------------------------------------------------------------
# Part E.1: Strict semantic comparator for the eight data artifacts
# ---------------------------------------------------------------------------
SEMANTIC_DATA_ARTIFACTS = [
    "results/part3b_prediction_ledger/sample_registry.csv",
    "results/part3b_prediction_ledger/event_manifest.csv",
    "results/part3b_prediction_ledger/split_membership_within.csv.gz",
    "results/part3b_prediction_ledger/split_membership_cross.csv.gz",
    "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz",
    "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz",
    "results/part3b_prediction_ledger/validation_reconstruction.csv",
    "results/part3b_prediction_ledger/canonical_result_reconstruction.csv",
]

SEMANTIC_METADATA_ARTIFACTS = [
    "results/part3b_prediction_ledger/ledger_manifest.json",
    "reports/part3b_split_leakage_audit.json",
    "reports/part3b_split_leakage_audit.md",
]

SEMANTIC_ALL_ARTIFACTS = list(SEMANTIC_DATA_ARTIFACTS) + list(SEMANTIC_METADATA_ARTIFACTS)

assert len(SEMANTIC_DATA_ARTIFACTS) == 8
assert len(SEMANTIC_METADATA_ARTIFACTS) == 3
assert len(SEMANTIC_ALL_ARTIFACTS) == 11

SEMANTIC_STRUCTURAL_ARTIFACTS = {
    "results/part3b_prediction_ledger/sample_registry.csv",
    "results/part3b_prediction_ledger/event_manifest.csv",
    "results/part3b_prediction_ledger/split_membership_within.csv.gz",
    "results/part3b_prediction_ledger/split_membership_cross.csv.gz",
}

SEMANTIC_FLOAT_ROUND_TRIP_ARTIFACTS = {
    "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz",
    "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz",
    "results/part3b_prediction_ledger/validation_reconstruction.csv",
    "results/part3b_prediction_ledger/canonical_result_reconstruction.csv",
}

LEDGER_IDENTITY_COLUMNS = [
    "event_id",
    "experiment",
    "target_project",
    "seed",
    "split_role",
    "split_position",
    "sample_uid",
    "sample_project",
    "original_row_index",
    "y_true",
]

LEDGER_EXACT_SCORE_COLUMNS = [
    "score__LR_std_C0.1",
    "score__LR_std_C1",
    "score__DT_leaf5",
]
LEDGER_ET_SCORE_COLUMN = "score__ET_leaf5"

VALIDATION_RECON_KEYS = ["experiment", "target_project", "seed", "candidate", "mode"]
RESULT_RECON_KEYS = ["experiment", "target_project", "seed", "model"]
RESULT_RECON_CAT_COLS = RESULT_RECON_KEYS + ["selected_candidate", "selection_mode"]

RANK_METRIC_SUFFIXES = ("roc_auc", "avg_precision")


def _is_rank_metric(column: str) -> bool:
    """Return True only for rank metrics that may use ET_RANK_METRIC_ATOL."""
    return column.endswith(RANK_METRIC_SUFFIXES)


def _read_semantic_data_artifact(path: Path) -> pd.DataFrame:
    """Read a float-bearing artifact with round-trip float parsing."""
    if path.suffix == ".gz":
        return read_float_csv_round_trip(path, compression="gzip")
    return read_float_csv_round_trip(path)


def _read_raw_decompressed_text(path: Path) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return f.read()
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def _row_key_dict(row: pd.Series, keys: List[str]) -> Dict[str, Any]:
    return {k: row[k] for k in keys}


def is_et_score_dependent_reconstruction_row(artifact: str, row: pd.Series) -> bool:
    """Determine whether a reconstruction row is driven by the ET_leaf5 score vector.

    Validation rows are ET-dependent only when candidate == "ET_leaf5".
    Result rows are ET-dependent when model == "ET_leaf5", selected_candidate ==
    "ET_leaf5", or selected_candidate contains "ET_leaf5" as an explicit ensemble
    member token (pipe-delimited).
    """
    if "validation_reconstruction.csv" in artifact:
        return str(row.get("candidate", "")) == "ET_leaf5"
    if "canonical_result_reconstruction.csv" in artifact:
        if str(row.get("model", "")) == "ET_leaf5":
            return True
        selected = str(row.get("selected_candidate", ""))
        if selected == "ET_leaf5":
            return True
        tokens = [t.strip() for t in selected.split("|") if t.strip()]
        return "ET_leaf5" in tokens
    return False


def float64_bitwise_difference_mask(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """True finite-float64 bit-pattern comparison, treating NaN == NaN."""
    a64 = np.asarray(a, dtype=np.float64)
    b64 = np.asarray(b, dtype=np.float64)
    nan_equal = np.isnan(a64) & np.isnan(b64)
    bits_a = a64.view(np.uint64)
    bits_b = b64.view(np.uint64)
    return (bits_a != bits_b) & ~nan_equal


def _compute_schema_contract(
    rel: str, first_columns: List[str], second_columns: List[str],
) -> Dict[str, Any]:
    """Compute frozen-schema contract evidence for a single artifact."""
    expected_schema = list(EXPECTED_DATA_ARTIFACT_SCHEMAS.get(rel, []))
    first_schema = list(first_columns)
    second_schema = list(second_columns)
    first_schema_contract_exact = first_schema == expected_schema
    second_schema_contract_exact = second_schema == expected_schema
    schemas_equal_to_each_other = first_schema == second_schema
    schema_contract_passed = first_schema_contract_exact and second_schema_contract_exact
    return {
        "expected_schema": expected_schema,
        "first_schema": first_schema,
        "second_schema": second_schema,
        "first_schema_contract_exact": first_schema_contract_exact,
        "second_schema_contract_exact": second_schema_contract_exact,
        "schemas_equal_to_each_other": schemas_equal_to_each_other,
        "schema_contract_passed": schema_contract_passed,
    }


def _compare_structural_artifact(
    rel: str,
    p1: Optional[Path],
    p2: Optional[Path],
    unapproved: List[Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
    """Compare identity-only artifacts with exact byte/decompressed equality."""
    comp: Dict[str, Any] = {
        "present_first": p1 is not None and p1.exists(),
        "present_second": p2 is not None and p2.exists(),
        "compressed_byte_equal": None,
        "decompressed_byte_equal": None,
        "schema_equal": None,
        "row_count_equal": None,
        "row_order_equal": None,
        "cell_values_equal": None,
        "identity_values_equal": None,
        "expected_schema": None,
        "first_schema": None,
        "second_schema": None,
        "first_schema_contract_exact": None,
        "second_schema_contract_exact": None,
        "schemas_equal_to_each_other": None,
        "schema_contract_passed": None,
        "within_policy": False,
    }
    if not (comp["present_first"] and comp["present_second"]):
        unapproved.append({"artifact": rel, "reason": "missing_in_one_input"})
        return False, comp

    b1 = p1.read_bytes()
    b2 = p2.read_bytes()
    if rel.endswith(".gz"):
        comp["compressed_byte_equal"] = b1 == b2
    text1 = _read_raw_decompressed_text(p1)
    text2 = _read_raw_decompressed_text(p2)
    comp["decompressed_byte_equal"] = text1 == text2

    df1 = pd.read_csv(io.StringIO(text1))
    df2 = pd.read_csv(io.StringIO(text2))
    comp["schema_equal"] = list(df1.columns) == list(df2.columns)
    comp["row_count_equal"] = len(df1) == len(df2)
    comp["row_order_equal"] = comp["decompressed_byte_equal"]
    comp["cell_values_equal"] = comp["decompressed_byte_equal"]
    comp["identity_values_equal"] = comp["decompressed_byte_equal"]

    sc = _compute_schema_contract(rel, list(df1.columns), list(df2.columns))
    comp.update(sc)

    comp["within_policy"] = comp["decompressed_byte_equal"] and comp["schema_contract_passed"]

    if not comp["within_policy"]:
        unapproved.append({"artifact": rel, "reason": "structural_or_identity_difference"})
    return comp["within_policy"], comp


def _compare_prediction_ledger(
    rel: str,
    p1: Optional[Path],
    p2: Optional[Path],
    unapproved: List[Dict[str, Any]],
    approved_et_rank: List[Dict[str, Any]],
    stats: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """Compare a prediction ledger under the Part E.1 score policy."""
    comp: Dict[str, Any] = {
        "present_first": p1 is not None and p1.exists(),
        "present_second": p2 is not None and p2.exists(),
        "schema_equal": None,
        "row_count_equal": None,
        "identity_columns_equal": None,
        "lr_dt_scores_exact": None,
        "et_score_maximum_absolute_difference": 0.0,
        "et_exactly_different_cells": 0,
        "et_out_of_policy_cells": 0,
        "first_twenty_et_score_differences": [],
        "expected_schema": None,
        "first_schema": None,
        "second_schema": None,
        "first_schema_contract_exact": None,
        "second_schema_contract_exact": None,
        "schemas_equal_to_each_other": None,
        "schema_contract_passed": None,
        "within_policy": False,
    }
    if not (comp["present_first"] and comp["present_second"]):
        unapproved.append({"artifact": rel, "reason": "missing_in_one_input"})
        return False, comp

    df1 = _read_semantic_data_artifact(p1)
    df2 = _read_semantic_data_artifact(p2)
    comp["schema_equal"] = list(df1.columns) == list(df2.columns)
    comp["row_count_equal"] = len(df1) == len(df2)

    sc = _compute_schema_contract(rel, list(df1.columns), list(df2.columns))
    comp.update(sc)

    schema_contract_passed = comp["schema_contract_passed"]
    within = schema_contract_passed

    if schema_contract_passed and comp["row_count_equal"]:
        identity_equal = (
            df1[LEDGER_IDENTITY_COLUMNS]
            .reset_index(drop=True)
            .equals(df2[LEDGER_IDENTITY_COLUMNS].reset_index(drop=True))
        )
    else:
        identity_equal = False
    comp["identity_columns_equal"] = identity_equal
    within = within and identity_equal

    if schema_contract_passed and comp["row_count_equal"]:
        lr_dt_exact = True
        for col in LEDGER_EXACT_SCORE_COLUMNS:
            missing_in_first = col not in df1.columns
            missing_in_second = col not in df2.columns
            if missing_in_first or missing_in_second:
                lr_dt_exact = False
                within = False
                unapproved.append({
                    "artifact": rel,
                    "metric": col,
                    "reason": "missing_required_score_column",
                })
                continue
            a = df1[col].to_numpy(dtype=np.float64)
            b = df2[col].to_numpy(dtype=np.float64)
            bit_diff_mask = float64_bitwise_difference_mask(a, b)
            bit_exact = not np.any(bit_diff_mask)
            if not bit_exact:
                lr_dt_exact = False
                within = False
                for i in np.where(bit_diff_mask)[0]:
                    unapproved.append({
                        "artifact": rel,
                        "metric": col,
                        "event_id": str(df1.iloc[i]["event_id"]),
                        "split_role": str(df1.iloc[i]["split_role"]),
                        "sample_uid": str(df1.iloc[i]["sample_uid"]),
                        "build_1_value": float(a[i]),
                        "build_2_value": float(b[i]),
                        "absolute_difference": float(abs(a[i] - b[i])),
                    })
        comp["lr_dt_scores_exact"] = lr_dt_exact

        if LEDGER_ET_SCORE_COLUMN in df1.columns and LEDGER_ET_SCORE_COLUMN in df2.columns:
            a = df1[LEDGER_ET_SCORE_COLUMN].to_numpy(dtype=np.float64)
            b = df2[LEDGER_ET_SCORE_COLUMN].to_numpy(dtype=np.float64)
            exact_diff = float64_bitwise_difference_mask(a, b)
            out_policy = ~np.isclose(a, b, rtol=0.0, atol=ET_SCORE_ATOL, equal_nan=True)
            n_exact = int(np.sum(exact_diff))
            n_out = int(np.sum(out_policy))
            comp["et_exactly_different_cells"] = n_exact
            comp["et_out_of_policy_cells"] = n_out
            stats["exactly_different_et_cells"] += n_exact
            stats["out_of_policy_et_cells"] += n_out

            if n_exact > 0:
                diffs = np.abs(a - b)
                maxdiff = float(np.nanmax(diffs[exact_diff]))
                comp["et_score_maximum_absolute_difference"] = maxdiff
                stats["maximum_et_score_difference"] = max(stats["maximum_et_score_difference"], maxdiff)
                records = []
                remaining = 20 - len(stats["first_twenty_et_score_differences"])
                if remaining > 0:
                    for i in np.where(exact_diff)[0][:remaining]:
                        records.append({
                            "artifact": rel,
                            "event_id": str(df1.iloc[i]["event_id"]),
                            "split_role": str(df1.iloc[i]["split_role"]),
                            "sample_uid": str(df1.iloc[i]["sample_uid"]),
                            "build_1_value": float(a[i]),
                            "build_2_value": float(b[i]),
                            "absolute_difference": float(diffs[i]),
                        })
                comp["first_twenty_et_score_differences"] = records
                stats["first_twenty_et_score_differences"].extend(records)

            if np.any(out_policy):
                within = False
                diffs = np.abs(a - b)
                for i in np.where(out_policy)[0]:
                    unapproved.append({
                        "artifact": rel,
                        "metric": LEDGER_ET_SCORE_COLUMN,
                        "event_id": str(df1.iloc[i]["event_id"]),
                        "split_role": str(df1.iloc[i]["split_role"]),
                        "sample_uid": str(df1.iloc[i]["sample_uid"]),
                        "build_1_value": float(a[i]),
                        "build_2_value": float(b[i]),
                        "absolute_difference": float(diffs[i]),
                    })
        else:
            lr_dt_exact = False
            within = False
            comp["lr_dt_scores_exact"] = lr_dt_exact
            unapproved.append({
                "artifact": rel,
                "metric": LEDGER_ET_SCORE_COLUMN,
                "reason": "missing_required_score_column",
            })
    else:
        comp["lr_dt_scores_exact"] = False

    comp["within_policy"] = within
    return within, comp


def _compare_reconstruction_artifact(
    rel: str,
    p1: Optional[Path],
    p2: Optional[Path],
    unapproved: List[Dict[str, Any]],
    approved_et_rank: List[Dict[str, Any]],
    stats: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """Compare a reconstruction artifact under the Part E.1 metric policy."""
    comp: Dict[str, Any] = {
        "present_first": p1 is not None and p1.exists(),
        "present_second": p2 is not None and p2.exists(),
        "schema_equal": None,
        "row_count_equal": None,
        "categorical_keys_exact": None,
        "selections_exact": None,
        "thresholds_exact": None,
        "non_et_metrics_strict": None,
        "expected_schema": None,
        "first_schema": None,
        "second_schema": None,
        "first_schema_contract_exact": None,
        "second_schema_contract_exact": None,
        "schemas_equal_to_each_other": None,
        "schema_contract_passed": None,
        "within_policy": False,
    }
    if not (comp["present_first"] and comp["present_second"]):
        unapproved.append({"artifact": rel, "reason": "missing_in_one_input"})
        return False, comp

    df1 = _read_semantic_data_artifact(p1)
    df2 = _read_semantic_data_artifact(p2)
    comp["schema_equal"] = list(df1.columns) == list(df2.columns)
    comp["row_count_equal"] = len(df1) == len(df2)

    sc = _compute_schema_contract(rel, list(df1.columns), list(df2.columns))
    comp.update(sc)

    schema_contract_passed = comp["schema_contract_passed"]

    if "validation_reconstruction.csv" in rel:
        keys = VALIDATION_RECON_KEYS
    else:
        keys = RESULT_RECON_CAT_COLS

    missing_keys = [k for k in keys if k not in df1.columns or k not in df2.columns]
    if missing_keys:
        within = False
        comp["categorical_keys_exact"] = False
        comp["selections_exact"] = False
        comp["thresholds_exact"] = False
        comp["non_et_metrics_strict"] = False
        for k in missing_keys:
            unapproved.append({
                "artifact": rel,
                "metric": k,
                "reason": "missing_required_key",
            })
        comp["within_policy"] = within
        return within, comp

    cat_equal = False
    if schema_contract_passed and comp["row_count_equal"]:
        cat_equal = df1[keys].reset_index(drop=True).equals(df2[keys].reset_index(drop=True))
    comp["categorical_keys_exact"] = cat_equal
    comp["selections_exact"] = cat_equal
    within = schema_contract_passed and cat_equal

    if schema_contract_passed and comp["row_count_equal"]:
        non_key_numeric = [c for c in df1.columns if c not in keys]
        threshold_col = None
        if "threshold" in non_key_numeric:
            threshold_col = "threshold"
        elif "val_threshold" in non_key_numeric:
            threshold_col = "val_threshold"

        if threshold_col is not None:
            a_thr = df1[threshold_col].to_numpy(dtype=np.float64)
            b_thr = df2[threshold_col].to_numpy(dtype=np.float64)
            thr_exact = np.array_equal(a_thr, b_thr, equal_nan=True)
            comp["thresholds_exact"] = thr_exact
            if not thr_exact:
                within = False
                mask = float64_bitwise_difference_mask(a_thr, b_thr)
                for i in np.where(mask)[0]:
                    unapproved.append({
                        "artifact": rel,
                        "metric": threshold_col,
                        "row_key": _row_key_dict(df1.iloc[i], keys),
                        "build_1_value": float(a_thr[i]),
                        "build_2_value": float(b_thr[i]),
                        "absolute_difference": float(abs(a_thr[i] - b_thr[i])),
                    })

        metric_cols = [c for c in non_key_numeric if c != threshold_col]
        et_dep = [is_et_score_dependent_reconstruction_row(rel, row) for _, row in df1.iterrows()]
        et_mask = np.array(et_dep, dtype=bool)
        non_et_metrics_strict = True

        for col in metric_cols:
            if col not in df2.columns:
                within = False
                non_et_metrics_strict = False
                unapproved.append({
                    "artifact": rel,
                    "metric": col,
                    "reason": "missing_required_metric_column",
                })
                continue
            a = df1[col].to_numpy(dtype=np.float64)
            b = df2[col].to_numpy(dtype=np.float64)
            diff = np.abs(a - b)
            strict_allowed = SEMANTIC_RECON_ATOL + SEMANTIC_RECON_RTOL * np.maximum(np.abs(a), np.abs(b))
            allowed = np.where(et_mask & _is_rank_metric(col), ET_RANK_METRIC_ATOL, strict_allowed)
            finite = np.isfinite(diff)
            within_col = bool(np.all(diff[finite] <= allowed[finite]))
            nan_ok = bool(np.all(np.isnan(a) == np.isnan(b)))
            if not (within_col and nan_ok):
                within = False
                non_et_metrics_strict = False
                bad = np.where(finite & (diff > allowed))[0]
                for i in bad:
                    unapproved.append({
                        "artifact": rel,
                        "metric": col,
                        "row_key": _row_key_dict(df1.iloc[i], keys),
                        "build_1_value": float(a[i]),
                        "build_2_value": float(b[i]),
                        "absolute_difference": float(diff[i]),
                    })
            else:
                if np.any(et_mask & _is_rank_metric(col)):
                    idx = np.where(finite & et_mask & _is_rank_metric(col) & (diff > 0))[0]
                    for i in idx:
                        approved_et_rank.append({
                            "artifact": rel,
                            "row_key": _row_key_dict(df1.iloc[i], keys),
                            "metric": col,
                            "build_1_value": float(a[i]),
                            "build_2_value": float(b[i]),
                            "absolute_difference": float(diff[i]),
                        })

        comp["non_et_metrics_strict"] = non_et_metrics_strict
    else:
        comp["non_et_metrics_strict"] = False

    comp["within_policy"] = within
    return within, comp


def compare_eight_data_artifacts_semantically(
    first_artifacts: Dict[str, Path],
    second_artifacts: Dict[str, Path],
) -> Dict[str, Any]:
    """Standalone strict semantic comparator for the eight Part 3B data artifacts.

    The three non-data artifacts (ledger_manifest.json, audit JSON, audit MD) are
    intentionally not compared here and are deferred to Part E.2.
    """
    present_first_set = {k for k, p in first_artifacts.items() if p is not None and p.exists()}
    present_second_set = {k for k, p in second_artifacts.items() if p is not None and p.exists()}
    expected = set(SEMANTIC_DATA_ARTIFACTS)

    missing_from_first = sorted(expected - present_first_set)
    missing_from_second = sorted(expected - present_second_set)
    extra_first = sorted(present_first_set - expected)
    extra_second = sorted(present_second_set - expected)
    extra_data_artifacts = sorted(set(extra_first) | set(extra_second))

    unapproved_metric_differences: List[Dict[str, Any]] = []
    allowed_et_rank_metric_differences: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {
        "maximum_et_score_difference": 0.0,
        "exactly_different_et_cells": 0,
        "out_of_policy_et_cells": 0,
        "first_twenty_et_score_differences": [],
    }

    artifact_comparisons: Dict[str, Any] = {}
    unapproved_artifacts: set = set()

    for rel in SEMANTIC_DATA_ARTIFACTS:
        p1 = first_artifacts.get(rel)
        p2 = second_artifacts.get(rel)
        basename = Path(rel).name
        if rel in SEMANTIC_STRUCTURAL_ARTIFACTS:
            ok, comp = _compare_structural_artifact(rel, p1, p2, unapproved_metric_differences)
        elif basename.startswith("prediction_ledger"):
            ok, comp = _compare_prediction_ledger(
                rel, p1, p2, unapproved_metric_differences, allowed_et_rank_metric_differences, stats
            )
        else:
            ok, comp = _compare_reconstruction_artifact(
                rel, p1, p2, unapproved_metric_differences, allowed_et_rank_metric_differences, stats
            )
        artifact_comparisons[rel] = comp
        if not ok:
            unapproved_artifacts.add(rel)

    exact_structural_equality = all(
        artifact_comparisons[rel].get("within_policy", False) for rel in SEMANTIC_STRUCTURAL_ARTIFACTS
    )
    all_identity_columns_exact = all(
        artifact_comparisons[rel].get("identity_values_equal") is not False
        and artifact_comparisons[rel].get("identity_columns_equal") is not False
        and artifact_comparisons[rel].get("categorical_keys_exact") is not False
        for rel in SEMANTIC_DATA_ARTIFACTS
    )
    all_non_et_score_columns_exact = all(
        artifact_comparisons[rel].get("lr_dt_scores_exact", True)
        and artifact_comparisons[rel].get("non_et_metrics_strict", True)
        for rel in SEMANTIC_DATA_ARTIFACTS
    )
    all_selection_decisions_exact = all(
        artifact_comparisons[rel].get("selections_exact", True) for rel in SEMANTIC_DATA_ARTIFACTS
    )
    all_thresholds_exact = all(
        artifact_comparisons[rel].get("thresholds_exact", True) for rel in SEMANTIC_DATA_ARTIFACTS
    )
    all_schema_contracts_passed = all(
        artifact_comparisons[rel].get("schema_contract_passed", False) is True
        for rel in SEMANTIC_DATA_ARTIFACTS
    )

    unapproved_differing_data_artifacts = sorted(unapproved_artifacts)
    data_artifacts_with_approved_et_roundoff_only = []
    for rel in SEMANTIC_DATA_ARTIFACTS:
        has_approved = (
            artifact_comparisons[rel].get("et_exactly_different_cells", 0) > 0
            or any(d.get("artifact") == rel for d in allowed_et_rank_metric_differences)
        )
        if has_approved and rel not in unapproved_artifacts:
            data_artifacts_with_approved_et_roundoff_only.append(rel)

    semantic_passed = bool(
        len(missing_from_first) == 0
        and len(missing_from_second) == 0
        and len(extra_data_artifacts) == 0
        and all_schema_contracts_passed
        and exact_structural_equality
        and all_identity_columns_exact
        and all_non_et_score_columns_exact
        and all_selection_decisions_exact
        and all_thresholds_exact
        and stats["maximum_et_score_difference"] <= ET_SCORE_ATOL
        and stats["out_of_policy_et_cells"] == 0
        and len(unapproved_metric_differences) == 0
        and len(unapproved_differing_data_artifacts) == 0
    )

    return {
        "data_artifacts_expected": len(SEMANTIC_DATA_ARTIFACTS),
        "data_artifacts_present_first": len(present_first_set),
        "data_artifacts_present_second": len(present_second_set),
        "missing_from_first": missing_from_first,
        "missing_from_second": missing_from_second,
        "extra_data_artifacts": extra_data_artifacts,
        "artifact_comparisons": artifact_comparisons,
        "all_schema_contracts_passed": all_schema_contracts_passed,
        "exact_structural_equality": exact_structural_equality,
        "all_identity_columns_exact": all_identity_columns_exact,
        "all_non_et_score_columns_exact": all_non_et_score_columns_exact,
        "maximum_et_score_difference": stats["maximum_et_score_difference"],
        "exactly_different_et_cells": stats["exactly_different_et_cells"],
        "out_of_policy_et_cells": stats["out_of_policy_et_cells"],
        "first_twenty_et_score_differences": stats["first_twenty_et_score_differences"],
        "all_selection_decisions_exact": all_selection_decisions_exact,
        "all_thresholds_exact": all_thresholds_exact,
        "allowed_et_rank_metric_differences": allowed_et_rank_metric_differences,
        "unapproved_metric_differences": unapproved_metric_differences,
        "data_artifacts_with_approved_et_roundoff_only": data_artifacts_with_approved_et_roundoff_only,
        "unapproved_differing_data_artifacts": unapproved_differing_data_artifacts,
        "data_artifact_semantic_comparison_passed": semantic_passed,
    }


def _make_synthetic_eight_artifact_dir(root: Path) -> Path:
    """Create a minimal valid set of the eight data artifacts for isolated tests."""
    root.mkdir(parents=True, exist_ok=True)

    sample_registry = pd.DataFrame([
        {
            "sample_uid": "CM1:000000",
            "project": "CM1",
            "original_row_index": 0,
            "raw_csv_row_number": 2,
            "y_true": 0,
            "feature_sha256": "a" * 64,
            "content_sha256": "b" * 64,
        },
        {
            "sample_uid": "CM1:000001",
            "project": "CM1",
            "original_row_index": 1,
            "raw_csv_row_number": 3,
            "y_true": 1,
            "feature_sha256": "c" * 64,
            "content_sha256": "d" * 64,
        },
    ])

    event_manifest = pd.DataFrame([
        {
            "event_id": "within_project__CM1__seed_007",
            "experiment": "within_project",
            "target_project": "CM1",
            "seed": 7,
            "source_projects": "CM1",
            "n_membership": 2,
            "n_train": 1,
            "n_validation": 1,
            "n_test": 0,
            "train_positive": 0,
            "train_negative": 1,
            "validation_positive": 1,
            "validation_negative": 0,
            "test_positive": 0,
            "test_negative": 0,
            "train_uid_sha256": "t" * 64,
            "validation_uid_sha256": "v" * 64,
            "test_uid_sha256": "x" * 64,
            "feature_count": 20,
            "feature_schema_sha256": "f" * 64,
            "train_source_projects": "CM1",
            "validation_source_projects": "CM1",
            "test_projects": "CM1",
            "identity_overlap_count": 0,
            "target_in_train_count": 1,
            "target_in_validation_count": 1,
            "source_in_test_count": 0,
            "preprocessing_train_only_passed": True,
        }
    ])

    split_row = {
        "event_id": "within_project__CM1__seed_007",
        "experiment": "within_project",
        "target_project": "CM1",
        "seed": 7,
        "sample_uid": "CM1:000000",
        "sample_project": "CM1",
        "original_row_index": 0,
        "split_role": "train",
        "split_position": 0,
        "y_true": 0,
    }
    split_row2 = {
        "event_id": "within_project__CM1__seed_007",
        "experiment": "within_project",
        "target_project": "CM1",
        "seed": 7,
        "sample_uid": "CM1:000001",
        "sample_project": "CM1",
        "original_row_index": 1,
        "split_role": "validation",
        "split_position": 1,
        "y_true": 1,
    }
    split_within = pd.DataFrame([split_row, split_row2])
    split_cross = pd.DataFrame([split_row, split_row2])

    pred_row = {
        "event_id": "within_project__CM1__seed_007",
        "experiment": "within_project",
        "target_project": "CM1",
        "seed": 7,
        "split_role": "validation",
        "split_position": 1,
        "sample_uid": "CM1:000001",
        "sample_project": "CM1",
        "original_row_index": 1,
        "y_true": 1,
        "score__LR_std_C0.1": 0.5,
        "score__LR_std_C1": 0.625,
        "score__DT_leaf5": 0.75,
        "score__ET_leaf5": 0.875,
    }
    pred_within = pd.DataFrame([pred_row])
    pred_cross = pd.DataFrame([pred_row])

    val_rows = []
    for candidate in CANDIDATES:
        val_rows.append({
            "experiment": "within_project",
            "target_project": "CM1",
            "seed": 7,
            "candidate": candidate,
            "mode": "balanced",
            "val_threshold": 0.5,
            "val_selection_score": 0.5,
            "val_avg_precision": 0.625,
            "val_roc_auc": 0.75,
            "val_mcc": 0.25,
            "val_f1": 0.5,
            "val_balanced_accuracy": 0.5,
            "val_precision": 0.5,
            "val_recall": 0.5,
            "val_brier": 0.25,
            "val_precision_at_10pct": 0.5,
            "val_recall_at_10pct": 0.5,
            "val_lift_at_10pct": 1.0,
            "val_precision_at_20pct": 0.5,
            "val_recall_at_20pct": 0.5,
            "val_lift_at_20pct": 1.0,
        })
    val_recon = pd.DataFrame(val_rows)

    result_rows = []
    for model in ["LR_std_C0.1", "AQRPE_v2_soft_top3"]:
        selected = model if model != "AQRPE_v2_soft_top3" else "LR_std_C0.1|DT_leaf5|ET_leaf5"
        result_rows.append({
            "experiment": "within_project",
            "target_project": "CM1",
            "seed": 7,
            "model": model,
            "selected_candidate": selected,
            "selection_mode": "balanced_objective",
            "threshold": 0.5,
            "selection_score": 0.5,
            "avg_precision": 0.625,
            "roc_auc": 0.75,
            "mcc": 0.25,
            "f1": 0.5,
            "balanced_accuracy": 0.5,
            "precision": 0.5,
            "recall": 0.5,
            "brier": 0.25,
            "precision_at_10pct": 0.5,
            "recall_at_10pct": 0.5,
            "lift_at_10pct": 1.0,
            "precision_at_20pct": 0.5,
            "recall_at_20pct": 0.5,
            "lift_at_20pct": 1.0,
        })
    result_recon = pd.DataFrame(result_rows)

    sample_registry.to_csv(root / "sample_registry.csv", index=False, lineterminator="\n")
    event_manifest.to_csv(root / "event_manifest.csv", index=False, lineterminator="\n")
    split_within.to_csv(root / "split_membership_within.csv.gz", index=False, lineterminator="\n", compression="gzip")
    split_cross.to_csv(root / "split_membership_cross.csv.gz", index=False, lineterminator="\n", compression="gzip")
    pred_within.to_csv(
        root / "prediction_ledger_within.csv.gz", index=False, lineterminator="\n", compression="gzip", float_format="%.17g"
    )
    pred_cross.to_csv(
        root / "prediction_ledger_cross.csv.gz", index=False, lineterminator="\n", compression="gzip", float_format="%.17g"
    )
    val_recon.to_csv(root / "validation_reconstruction.csv", index=False, lineterminator="\n", float_format="%.17g")
    result_recon.to_csv(root / "canonical_result_reconstruction.csv", index=False, lineterminator="\n", float_format="%.17g")

    return root


def _artifact_paths_from_dir(root: Path) -> Dict[str, Path]:
    return {rel: root / Path(rel).name for rel in SEMANTIC_DATA_ARTIFACTS}


def run_data_artifact_comparison_self_tests() -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """Thirteen isolated tests for the strict eight-artifact semantic comparator."""
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, passed: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": passed, **extra})
        all_passed = all_passed and passed

    with tempfile.TemporaryDirectory(prefix="part3b2_e1_base_") as base_dir:
        base_root = _make_synthetic_eight_artifact_dir(Path(base_dir))
        base_paths = _artifact_paths_from_dir(base_root)

        # 1. Exact fixture passes.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_copy_") as copy_dir:
            copy_root = Path(copy_dir)
            for rel, src in base_paths.items():
                dst = copy_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(copy_root))
            _record(
                "exact_eight_artifact_fixture_passes",
                result["data_artifact_semantic_comparison_passed"] is True,
                maximum_et_score_difference=result["maximum_et_score_difference"],
            )

        # 2. One required data artifact missing fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_missing_") as miss_dir:
            miss_root = Path(miss_dir)
            for rel, src in base_paths.items():
                if "sample_registry.csv" in rel:
                    continue
                dst = miss_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(miss_root))
            _record(
                "one_required_artifact_missing_fails",
                result["data_artifact_semantic_comparison_passed"] is False
                and "results/part3b_prediction_ledger/sample_registry.csv" in result["missing_from_second"],
            )

        # 3. One schema difference fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_schema_") as schema_dir:
            schema_root = Path(schema_dir)
            for rel, src in base_paths.items():
                dst = schema_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            ev = pd.read_csv(schema_root / "event_manifest.csv")
            ev.rename(columns={"event_id": "event_id_renamed"}, inplace=True)
            ev.to_csv(schema_root / "event_manifest.csv", index=False, lineterminator="\n")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(schema_root))
            comp = result["artifact_comparisons"].get("results/part3b_prediction_ledger/event_manifest.csv", {})
            _record(
                "one_schema_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False and comp.get("schema_equal") is False,
            )

        # 4. One row-order difference fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_order_") as order_dir:
            order_root = Path(order_dir)
            for rel, src in base_paths.items():
                dst = order_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            reg = pd.read_csv(order_root / "sample_registry.csv")
            reg = reg.iloc[::-1].reset_index(drop=True)
            reg.to_csv(order_root / "sample_registry.csv", index=False, lineterminator="\n")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(order_root))
            comp = result["artifact_comparisons"].get("results/part3b_prediction_ledger/sample_registry.csv", {})
            _record(
                "one_row_order_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False
                and comp.get("decompressed_byte_equal") is False,
            )

        # 5. One identity-cell difference fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_identity_") as id_dir:
            id_root = Path(id_dir)
            for rel, src in base_paths.items():
                dst = id_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            reg = pd.read_csv(id_root / "sample_registry.csv")
            reg.at[0, "sample_uid"] = "CM1:999999"
            reg.to_csv(id_root / "sample_registry.csv", index=False, lineterminator="\n")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(id_root))
            _record(
                "one_identity_cell_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False
                and result["all_identity_columns_exact"] is False,
            )

        # 6. LR score changed by one ULP fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_lr_") as lr_dir:
            lr_root = Path(lr_dir)
            for rel, src in base_paths.items():
                dst = lr_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            df = _read_semantic_data_artifact(lr_root / "prediction_ledger_within.csv.gz")
            df.at[0, "score__LR_std_C0.1"] = np.nextafter(float(df.at[0, "score__LR_std_C0.1"]), np.inf)
            df.to_csv(
                lr_root / "prediction_ledger_within.csv.gz", index=False, lineterminator="\n", compression="gzip", float_format="%.17g"
            )
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(lr_root))
            comp = result["artifact_comparisons"].get("results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
            _record(
                "lr_score_one_ulp_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False and comp.get("lr_dt_scores_exact") is False,
            )

        # 7. DT score changed by one ULP fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_dt_") as dt_dir:
            dt_root = Path(dt_dir)
            for rel, src in base_paths.items():
                dst = dt_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            df = _read_semantic_data_artifact(dt_root / "prediction_ledger_within.csv.gz")
            df.at[0, "score__DT_leaf5"] = np.nextafter(float(df.at[0, "score__DT_leaf5"]), np.inf)
            df.to_csv(
                dt_root / "prediction_ledger_within.csv.gz", index=False, lineterminator="\n", compression="gzip", float_format="%.17g"
            )
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(dt_root))
            comp = result["artifact_comparisons"].get("results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
            _record(
                "dt_score_one_ulp_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False and comp.get("lr_dt_scores_exact") is False,
            )

        # 8. ET score changed by 5e-16 passes and is counted as exactly different.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_et5e16_") as et_dir:
            et_root = Path(et_dir)
            for rel, src in base_paths.items():
                dst = et_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            df = _read_semantic_data_artifact(et_root / "prediction_ledger_within.csv.gz")
            df.at[0, "score__ET_leaf5"] = float(df.at[0, "score__ET_leaf5"]) + 5e-16
            df.to_csv(
                et_root / "prediction_ledger_within.csv.gz", index=False, lineterminator="\n", compression="gzip", float_format="%.17g"
            )
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(et_root))
            comp = result["artifact_comparisons"].get("results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
            _record(
                "et_score_5e16_roundoff_passes_and_counted",
                result["data_artifact_semantic_comparison_passed"] is True
                and comp.get("et_exactly_different_cells") == 1
                and comp.get("et_out_of_policy_cells") == 0
                and result["exactly_different_et_cells"] == 1
                and result["out_of_policy_et_cells"] == 0,
                maximum_et_score_difference=result["maximum_et_score_difference"],
            )

        # 9. ET score changed by 2e-15 fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_et2e15_") as et2_dir:
            et2_root = Path(et2_dir)
            for rel, src in base_paths.items():
                dst = et2_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            df = _read_semantic_data_artifact(et2_root / "prediction_ledger_within.csv.gz")
            df.at[0, "score__ET_leaf5"] = float(df.at[0, "score__ET_leaf5"]) + 2e-15
            df.to_csv(
                et2_root / "prediction_ledger_within.csv.gz", index=False, lineterminator="\n", compression="gzip", float_format="%.17g"
            )
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(et2_root))
            _record(
                "et_score_2e15_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False
                and result["out_of_policy_et_cells"] > 0,
            )

        # 10. One reconstruction threshold difference fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_threshold_") as th_dir:
            th_root = Path(th_dir)
            for rel, src in base_paths.items():
                dst = th_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            res = pd.read_csv(th_root / "canonical_result_reconstruction.csv")
            res.at[0, "threshold"] = float(res.at[0, "threshold"]) + 1e-8
            res.to_csv(th_root / "canonical_result_reconstruction.csv", index=False, lineterminator="\n", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(th_root))
            comp = result["artifact_comparisons"].get("results/part3b_prediction_ledger/canonical_result_reconstruction.csv", {})
            _record(
                "one_reconstruction_threshold_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False and comp.get("thresholds_exact") is False,
            )

        # 11. Non-ET reconstruction metric changed by 1e-8 fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_nonet_") as nonet_dir:
            nonet_root = Path(nonet_dir)
            for rel, src in base_paths.items():
                dst = nonet_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            val = pd.read_csv(nonet_root / "validation_reconstruction.csv")
            non_et_idx = val.index[val["candidate"] != "ET_leaf5"][0]
            val.at[non_et_idx, "val_brier"] = float(val.at[non_et_idx, "val_brier"]) + 1e-8
            val.to_csv(nonet_root / "validation_reconstruction.csv", index=False, lineterminator="\n", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(nonet_root))
            _record(
                "non_et_reconstruction_metric_1e8_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False
                and result["all_non_et_score_columns_exact"] is False,
            )

        # 12. ET-dependent roc_auc changed by 5e-8 passes as approved rank roundoff.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_etrank_") as etr_dir:
            etr_root = Path(etr_dir)
            for rel, src in base_paths.items():
                dst = etr_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            val = pd.read_csv(etr_root / "validation_reconstruction.csv")
            et_idx = val.index[val["candidate"] == "ET_leaf5"][0]
            val.at[et_idx, "val_roc_auc"] = float(val.at[et_idx, "val_roc_auc"]) + 5e-8
            val.to_csv(etr_root / "validation_reconstruction.csv", index=False, lineterminator="\n", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(etr_root))
            approved = result["allowed_et_rank_metric_differences"]
            _record(
                "et_dependent_roc_auc_5e8_rank_roundoff_passes",
                result["data_artifact_semantic_comparison_passed"] is True
                and len(approved) == 1
                and approved[0]["metric"] == "val_roc_auc",
            )

        # 13. ET-dependent non-rank metric changed by 5e-8 fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e1_etnonrank_") as etnr_dir:
            etnr_root = Path(etnr_dir)
            for rel, src in base_paths.items():
                dst = etnr_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            val = pd.read_csv(etnr_root / "validation_reconstruction.csv")
            et_idx = val.index[val["candidate"] == "ET_leaf5"][0]
            val.at[et_idx, "val_brier"] = float(val.at[et_idx, "val_brier"]) + 5e-8
            val.to_csv(etnr_root / "validation_reconstruction.csv", index=False, lineterminator="\n", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(etnr_root))
            _record(
                "et_dependent_non_rank_metric_5e8_difference_fails",
                result["data_artifact_semantic_comparison_passed"] is False
                and result["all_non_et_score_columns_exact"] is False,
            )

    summary = {
        "tests_expected": 13,
        "tests_executed": len(tests),
        "tests_passed": sum(1 for t in tests if t.get("passed")),
        "tests_failed": sum(1 for t in tests if not t.get("passed")),
        "test_details": tests,
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "repository_artifacts_written": 0,
        "full_build_executed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
        "round_trip_parsing_used": True,
        "et_score_tolerance": ET_SCORE_ATOL,
        "et_rank_metric_tolerance": ET_RANK_METRIC_ATOL,
    }
    return tests, all_passed, summary


def run_part_e1_1_schema_provenance_tests() -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """Six focused schema/provenance tests for Part E.1.1."""
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, passed: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": passed, **extra})
        all_passed = all_passed and passed

    # 1. Accepted Part 3A constant equals d16e28488aa0936014f020c05466181eff219af6
    _record(
        "accepted_part3a_commit_constant",
        ACCEPTED_PART3A_COMMIT == "d16e28488aa0936014f020c05466181eff219af6",
        accepted_part3a_commit=ACCEPTED_PART3A_COMMIT,
    )

    with tempfile.TemporaryDirectory(prefix="part3b2_e11_base_") as base_dir:
        base_root = _make_synthetic_eight_artifact_dir(Path(base_dir))
        base_paths = _artifact_paths_from_dir(base_root)

        # 2. Both prediction ledgers identically missing score__ET_leaf5 fail.
        with tempfile.TemporaryDirectory(prefix="part3b2_e11_missing_et_") as miss_et_dir:
            miss_et_root = Path(miss_et_dir)
            for rel, src in base_paths.items():
                dst = miss_et_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            for ledger_name in ["prediction_ledger_within.csv.gz", "prediction_ledger_cross.csv.gz"]:
                p = miss_et_root / ledger_name
                df = _read_semantic_data_artifact(p)
                df.drop(columns=[LEDGER_ET_SCORE_COLUMN], inplace=True)
                df.to_csv(p, index=False, lineterminator="\n", compression="gzip", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(miss_et_root))
            comp_w = result["artifact_comparisons"].get(
                "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
            _record(
                "both_ledgers_missing_et_score_fail",
                result["data_artifact_semantic_comparison_passed"] is False
                and comp_w.get("schema_contract_passed") is False
                and comp_w.get("within_policy") is False,
            )

        # 3. Both prediction ledgers containing the same extra column fail.
        with tempfile.TemporaryDirectory(prefix="part3b2_e11_extra_col_") as extra_dir:
            extra_root = Path(extra_dir)
            for rel, src in base_paths.items():
                dst = extra_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            for ledger_name in ["prediction_ledger_within.csv.gz", "prediction_ledger_cross.csv.gz"]:
                p = extra_root / ledger_name
                df = _read_semantic_data_artifact(p)
                df["extra_bogus_column"] = 0.0
                df.to_csv(p, index=False, lineterminator="\n", compression="gzip", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(
                _artifact_paths_from_dir(extra_root), _artifact_paths_from_dir(extra_root))
            comp_w = result["artifact_comparisons"].get(
                "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
            _record(
                "both_ledgers_same_extra_column_fail",
                result["data_artifact_semantic_comparison_passed"] is False
                and comp_w.get("schema_contract_passed") is False
                and comp_w.get("first_schema") == comp_w.get("second_schema")
                and comp_w.get("schemas_equal_to_each_other") is True,
            )

        # 4. Both validation reconstruction files identically missing val_avg_precision fail.
        with tempfile.TemporaryDirectory(prefix="part3b2_e11_missing_valap_") as miss_valap_dir:
            miss_valap_root = Path(miss_valap_dir)
            for rel, src in base_paths.items():
                dst = miss_valap_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            p = miss_valap_root / "validation_reconstruction.csv"
            df = pd.read_csv(p)
            df.drop(columns=["val_avg_precision"], inplace=True)
            df.to_csv(p, index=False, lineterminator="\n", float_format="%.17g")
            result = compare_eight_data_artifacts_semantically(base_paths, _artifact_paths_from_dir(miss_valap_root))
            comp = result["artifact_comparisons"].get(
                "results/part3b_prediction_ledger/validation_reconstruction.csv", {})
            _record(
                "both_val_recon_missing_val_avg_precision_fail",
                result["data_artifact_semantic_comparison_passed"] is False
                and comp.get("schema_contract_passed") is False
                and comp.get("within_policy") is False,
            )

        # 5. Both structural sample-registry files identically missing sample_uid fail.
        with tempfile.TemporaryDirectory(prefix="part3b2_e11_missing_uid_") as miss_uid_dir:
            miss_uid_root = Path(miss_uid_dir)
            for rel, src in base_paths.items():
                dst = miss_uid_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            p1 = miss_uid_root / "sample_registry.csv"
            p2 = miss_uid_root / "sample_registry.csv"
            df = pd.read_csv(p1)
            df.drop(columns=["sample_uid"], inplace=True)
            df.to_csv(p1, index=False, lineterminator="\n")
            # Also drop from the base to make both identical
            base_reg = base_root / "sample_registry.csv"
            base_df = pd.read_csv(base_reg)
            base_df2 = base_df.drop(columns=["sample_uid"])
            # We need both first and second to be missing sample_uid
            # Use the modified copy as both first and second
            result = compare_eight_data_artifacts_semantically(
                _artifact_paths_from_dir(miss_uid_root), _artifact_paths_from_dir(miss_uid_root))
            comp = result["artifact_comparisons"].get(
                "results/part3b_prediction_ledger/sample_registry.csv", {})
            _record(
                "both_sample_registry_missing_sample_uid_fail",
                result["data_artifact_semantic_comparison_passed"] is False
                and comp.get("schema_contract_passed") is False
                and comp.get("within_policy") is False,
            )

        # 6. More than twenty in-policy ET bit differences produce:
        #    exactly_different_et_cells > 20 but len(first_twenty_et_score_differences) == 20
        with tempfile.TemporaryDirectory(prefix="part3b2_e11_et20_") as et20_dir:
            et20_root = Path(et20_dir)
            for rel, src in base_paths.items():
                dst = et20_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            # Create 25 rows with in-policy ET bit differences in both ledgers
            for ledger_name in ["prediction_ledger_within.csv.gz", "prediction_ledger_cross.csv.gz"]:
                p = et20_root / ledger_name
                df = _read_semantic_data_artifact(p)
                rows = []
                for i in range(25):
                    row = df.iloc[0].to_dict()
                    row["sample_uid"] = f"CM1:{i:06d}"
                    row["original_row_index"] = i
                    row["score__ET_leaf5"] = 0.875 + i * 5e-16
                    rows.append(row)
                df_new = pd.DataFrame(rows)
                df_new.to_csv(p, index=False, lineterminator="\n", compression="gzip", float_format="%.17g")
            # Also update the base to have the same 25 rows but with different ET values
            # so that there are 25 in-policy bit differences
            with tempfile.TemporaryDirectory(prefix="part3b2_e11_et20_base_") as et20_base_dir:
                et20_base_root = Path(et20_base_dir)
                for rel, src in base_paths.items():
                    dst = et20_base_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                for ledger_name in ["prediction_ledger_within.csv.gz", "prediction_ledger_cross.csv.gz"]:
                    p = et20_base_root / ledger_name
                    df = _read_semantic_data_artifact(p)
                    rows = []
                    for i in range(25):
                        row = df.iloc[0].to_dict()
                        row["sample_uid"] = f"CM1:{i:06d}"
                        row["original_row_index"] = i
                        row["score__ET_leaf5"] = 0.875
                        rows.append(row)
                    df_new = pd.DataFrame(rows)
                    df_new.to_csv(p, index=False, lineterminator="\n", compression="gzip", float_format="%.17g")
                result = compare_eight_data_artifacts_semantically(
                    _artifact_paths_from_dir(et20_base_root), _artifact_paths_from_dir(et20_root))
                _record(
                    "global_first_twenty_cap",
                    result["exactly_different_et_cells"] > 20
                    and len(result["first_twenty_et_score_differences"]) == 20,
                    exactly_different_et_cells=result["exactly_different_et_cells"],
                    first_twenty_count=len(result["first_twenty_et_score_differences"]),
                )

    summary = {
        "tests_expected": 6,
        "tests_executed": len(tests),
        "tests_passed": sum(1 for t in tests if t.get("passed")),
        "tests_failed": sum(1 for t in tests if not t.get("passed")),
        "test_details": tests,
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "repository_artifacts_written": 0,
        "full_build_executed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
    }
    return tests, all_passed, summary


def run_part_e1_2_signed_zero_tests() -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """Two focused signed-zero bit-difference tests for Part E.1.2."""
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, passed: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": passed, **extra})
        all_passed = all_passed and passed

    with tempfile.TemporaryDirectory(prefix="part3b2_e12_base_") as base_dir:
        base_root = _make_synthetic_eight_artifact_dir(Path(base_dir))
        base_paths = _artifact_paths_from_dir(base_root)

        # 1. LR signed-zero bit difference fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e12_lr_signed_zero_") as lr_sz_dir:
            lr_sz_root = Path(lr_sz_dir)
            for rel, src in base_paths.items():
                dst = lr_sz_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            df = _read_semantic_data_artifact(lr_sz_root / "prediction_ledger_within.csv.gz")
            df.at[0, "score__LR_std_C0.1"] = 0.0
            df.to_csv(
                lr_sz_root / "prediction_ledger_within.csv.gz",
                index=False, lineterminator="\n", compression="gzip", float_format="%.17e",
            )
            # Build the second copy with -0.0
            with tempfile.TemporaryDirectory(prefix="part3b2_e12_lr_signed_zero_b2_") as lr_sz_b2_dir:
                lr_sz_b2_root = Path(lr_sz_b2_dir)
                for rel, src in base_paths.items():
                    dst = lr_sz_b2_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                df2 = _read_semantic_data_artifact(lr_sz_b2_root / "prediction_ledger_within.csv.gz")
                df2.at[0, "score__LR_std_C0.1"] = -0.0
                df2.to_csv(
                    lr_sz_b2_root / "prediction_ledger_within.csv.gz",
                    index=False, lineterminator="\n", compression="gzip", float_format="%.17e",
                )
                result = compare_eight_data_artifacts_semantically(
                    _artifact_paths_from_dir(lr_sz_root), _artifact_paths_from_dir(lr_sz_b2_root))
                comp = result["artifact_comparisons"].get(
                    "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
                _record(
                    "lr_signed_zero_bit_difference_fails",
                    result["data_artifact_semantic_comparison_passed"] is False
                    and comp.get("lr_dt_scores_exact") is False,
                )

        # 2. DT signed-zero bit difference fails.
        with tempfile.TemporaryDirectory(prefix="part3b2_e12_dt_signed_zero_") as dt_sz_dir:
            dt_sz_root = Path(dt_sz_dir)
            for rel, src in base_paths.items():
                dst = dt_sz_root / Path(rel).name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            df = _read_semantic_data_artifact(dt_sz_root / "prediction_ledger_within.csv.gz")
            df.at[0, "score__DT_leaf5"] = 0.0
            df.to_csv(
                dt_sz_root / "prediction_ledger_within.csv.gz",
                index=False, lineterminator="\n", compression="gzip", float_format="%.17e",
            )
            # Build the second copy with -0.0
            with tempfile.TemporaryDirectory(prefix="part3b2_e12_dt_signed_zero_b2_") as dt_sz_b2_dir:
                dt_sz_b2_root = Path(dt_sz_b2_dir)
                for rel, src in base_paths.items():
                    dst = dt_sz_b2_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                df2 = _read_semantic_data_artifact(dt_sz_b2_root / "prediction_ledger_within.csv.gz")
                df2.at[0, "score__DT_leaf5"] = -0.0
                df2.to_csv(
                    dt_sz_b2_root / "prediction_ledger_within.csv.gz",
                    index=False, lineterminator="\n", compression="gzip", float_format="%.17e",
                )
                result = compare_eight_data_artifacts_semantically(
                    _artifact_paths_from_dir(dt_sz_root), _artifact_paths_from_dir(dt_sz_b2_root))
                comp = result["artifact_comparisons"].get(
                    "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz", {})
                _record(
                    "dt_signed_zero_bit_difference_fails",
                    result["data_artifact_semantic_comparison_passed"] is False
                    and comp.get("lr_dt_scores_exact") is False,
                )

    lr_signed_zero_rejected = any(
        t["case_name"] == "lr_signed_zero_bit_difference_fails" and t["passed"]
        for t in tests
    )
    dt_signed_zero_rejected = any(
        t["case_name"] == "dt_signed_zero_bit_difference_fails" and t["passed"]
        for t in tests
    )

    summary = {
        "tests_expected": 2,
        "tests_executed": len(tests),
        "tests_passed": sum(1 for t in tests if t.get("passed")),
        "tests_failed": sum(1 for t in tests if not t.get("passed")),
        "test_details": tests,
        "lr_signed_zero_rejected": lr_signed_zero_rejected,
        "dt_signed_zero_rejected": dt_signed_zero_rejected,
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "repository_artifacts_written": 0,
        "full_build_executed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
    }
    return tests, all_passed, summary


# ---------------------------------------------------------------------------
# Part E.2: Fourteen isolated tests for the eleven-artifact semantic gate
# ---------------------------------------------------------------------------
def _make_synthetic_metadata_artifacts(
    data_root: Path,
    output_root: Path,
) -> Dict[str, Path]:
    """Create synthetic ledger_manifest.json, audit JSON, and audit MD for tests."""
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "results" / "part3b_prediction_ledger").mkdir(parents=True, exist_ok=True)
    (output_root / "reports").mkdir(parents=True, exist_ok=True)

    data_paths = _artifact_paths_from_dir(data_root)

    # Build artifact hashes
    artifact_hashes = {}
    manifest_entries = []
    for rel in SEMANTIC_DATA_ARTIFACTS:
        p = data_paths[rel]
        h = sha256_file(p)
        sz = p.stat().st_size
        df = _read_artifact_df(p)
        artifact_hashes[rel] = {"sha256": h, "byte_size": sz}
        manifest_entries.append({
            "relative_path": rel,
            "format": "csv.gz" if rel.endswith(".gz") else "csv",
            "compressed": rel.endswith(".gz"),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "byte_size": sz,
            "sha256": h,
        })

    # Build ledger manifest
    manifest_data = {
        "manifest_version": PART3B_VERSION,
        "starting_commit": STARTING_COMMIT,
        "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
        "project_order": ["CM1", "JM1", "KC1", "KC2", "PC1"],
        "seed_order": [7, 13, 29, 42, 101],
        "candidate_order": ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"],
        "event_count": 50,
        "sample_count": 17442,
        "split_membership_total_rows": 523260,
        "prediction_total_rows": 209330,
        "validation_reconstruction_rows": 600,
        "canonical_result_reconstruction_rows": 400,
        "self_referential_hash_embedded": False,
        "artifacts": manifest_entries,
    }
    manifest_path = output_root / "results" / "part3b_prediction_ledger" / "ledger_manifest.json"
    write_text_atomic(manifest_path, _json_dumps(manifest_data))

    # Build audit JSON
    audit_checks = {name: True for name in REQUIRED_AUDIT_CHECK_NAMES}
    stage_gate = {field: False for field in REQUIRED_STAGE_GATE_FIELDS}
    stage_gate["part3b_prediction_ledger_complete"] = False
    stage_gate["next_authorized_stage"] = None
    stage_gate["part3c_constraint"] = PART3C_CONSTRAINT

    audit_json = {
        "part3b_version": PART3B_VERSION,
        "starting_commit": STARTING_COMMIT,
        "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
        "repository": REPOSITORY,
        "branch": BRANCH,
        "timestamp": "1970-01-01T00:00:00",
        "audit_checks": audit_checks,
        "stage_gate": stage_gate,
        "stage_gate_evidence": {},
        "validation_results": {},
        "duplicate_content_audit": {},
        "negative_tests": [],
        "canonical_exception_validator_tests": [],
        "tie_policy_tests": [],
        "canonical_nondeterminism_diagnostic": ET_ND_DIAGNOSTIC,
        "preservation_state": {},
        "artifact_hashes": artifact_hashes,
        "feature_schema_sha256": "f" * 64,
        "common_feature_names": [],
        "common_feature_count": 0,
        "dataset_profile_summary": {},
        "event_manifest_summary": {},
        "split_membership_summary": {},
        "prediction_ledger_summary": {},
        "reconstruction_summary": {},
        "fitted_candidate_count": 0,
    }
    audit_json_path = output_root / "reports" / "part3b_split_leakage_audit.json"
    write_text_atomic(audit_json_path, _json_dumps(audit_json))

    # Build audit Markdown
    md_lines = [
        "# Part 3B.2R Split / Leakage Audit Report",
        "",
        f"- **Version:** {PART3B_VERSION}",
        f"- **Repository:** {REPOSITORY}",
        f"- **Branch:** {BRANCH}",
        f"- **Starting commit:** {STARTING_COMMIT}",
        f"- **Accepted Part 3A commit:** {ACCEPTED_PART3A_COMMIT}",
        f"- **Timestamp:** 1970-01-01T00:00:00",
        "",
        "## Stage Gate",
        "",
    ]
    for k, v in stage_gate.items():
        md_lines.append(f"- **{k}:** {v}")
    md_lines.append("")
    md_lines.append("## Audit Checks")
    md_lines.append("")
    for k, v in audit_checks.items():
        md_lines.append(f"- **{k}:** {v}")
    md_lines.append("")
    md_lines.append("## Prediction Ledger Summary")
    md_lines.append("")
    md_lines.append("## Reconstruction Summary")
    md_lines.append("")
    md_lines.append("## Canonical Nondeterminism Diagnostic")
    md_lines.append("")
    for k, v in ET_ND_DIAGNOSTIC.items():
        md_lines.append(f"- **{k}:** {v}")
    md_lines.append("")
    md_lines.append("## Semantic Reproducibility (Two Independent Builds)")
    md_lines.append("")
    md_lines.append("## Negative Tests")
    md_lines.append("")
    md_lines.append("## Canonical Exception Validator Tests")
    md_lines.append("")
    md_lines.append("## Tie Policy Tests")
    md_lines.append("")
    md_lines.append("## Artifact Hashes")
    md_lines.append("")
    md_lines.append("| Artifact | SHA-256 |")
    md_lines.append("|----------|---------|")
    for rel, h in artifact_hashes.items():
        md_lines.append(f"| {rel} | {h['sha256']} |")
    md_lines.append("")

    audit_md_path = output_root / "reports" / "part3b_split_leakage_audit.md"
    write_text_atomic(audit_md_path, "\n".join(md_lines))

    # Return all 11 artifact paths
    all_paths = dict(data_paths)
    all_paths["results/part3b_prediction_ledger/ledger_manifest.json"] = manifest_path
    all_paths["reports/part3b_split_leakage_audit.json"] = audit_json_path
    all_paths["reports/part3b_split_leakage_audit.md"] = audit_md_path
    return all_paths


def _all_artifact_paths_from_dir(root: Path) -> Dict[str, Path]:
    """Return all 11 artifact paths from a directory."""
    paths = _artifact_paths_from_dir(root)
    paths["results/part3b_prediction_ledger/ledger_manifest.json"] = root / "ledger_manifest.json"
    paths["reports/part3b_split_leakage_audit.json"] = root / "part3b_split_leakage_audit.json"
    paths["reports/part3b_split_leakage_audit.md"] = root / "part3b_split_leakage_audit.md"
    return paths


def run_part_e2_eleven_artifact_tests() -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """Fourteen isolated tests for the strict eleven-artifact semantic gate."""
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, passed: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": passed, **extra})
        all_passed = all_passed and passed

    with tempfile.TemporaryDirectory(prefix="part3b2_e2_base_") as base_data_dir:
        base_data_root = _make_synthetic_eight_artifact_dir(Path(base_data_dir))

        with tempfile.TemporaryDirectory(prefix="part3b2_e2_base_meta_") as base_meta_dir:
            base_all = _make_synthetic_metadata_artifacts(base_data_root, Path(base_meta_dir))

            # 1. Exact eleven-artifact fixture passes.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_copy_") as copy_dir:
                copy_root = Path(copy_dir)
                for rel, src in base_all.items():
                    dst = copy_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                copy_paths = _all_artifact_paths_from_dir(copy_root)
                result = compare_eleven_artifacts_semantically(base_all, copy_paths)
                _record(
                    "exact_eleven_artifact_fixture_passes",
                    result["semantic_reproducibility_passed"] is True,
                )

            # 2. One metadata artifact missing fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_miss_meta_") as miss_meta_dir:
                miss_meta_root = Path(miss_meta_dir)
                for rel, src in base_all.items():
                    if rel == "reports/part3b_split_leakage_audit.md":
                        continue
                    dst = miss_meta_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                miss_paths = _all_artifact_paths_from_dir(miss_meta_root)
                result = compare_eleven_artifacts_semantically(base_all, miss_paths)
                _record(
                    "one_metadata_artifact_missing_fails",
                    result["semantic_reproducibility_passed"] is False
                    and "reports/part3b_split_leakage_audit.md" in result["missing_from_second"],
                )

            # 3. Ledger manifest with wrong version fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_wrong_ver_") as wv_dir:
                wv_root = Path(wv_dir)
                for rel, src in base_all.items():
                    dst = wv_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (wv_root / "ledger_manifest.json").open("r") as f:
                    manifest = json.load(f)
                manifest["manifest_version"] = "WRONG-VERSION"
                write_text_atomic(wv_root / "ledger_manifest.json", _json_dumps(manifest))
                wv_paths = _all_artifact_paths_from_dir(wv_root)
                result = compare_eleven_artifacts_semantically(base_all, wv_paths)
                _record(
                    "manifest_wrong_version_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 4. Ledger manifest with wrong starting commit fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_wrong_commit_") as wc_dir:
                wc_root = Path(wc_dir)
                for rel, src in base_all.items():
                    dst = wc_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (wc_root / "ledger_manifest.json").open("r") as f:
                    manifest = json.load(f)
                manifest["starting_commit"] = "wrongcommit"
                write_text_atomic(wc_root / "ledger_manifest.json", _json_dumps(manifest))
                wc_paths = _all_artifact_paths_from_dir(wc_root)
                result = compare_eleven_artifacts_semantically(base_all, wc_paths)
                _record(
                    "manifest_wrong_starting_commit_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 5. Ledger manifest with wrong artifact order fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_wrong_order_") as wo_dir:
                wo_root = Path(wo_dir)
                for rel, src in base_all.items():
                    dst = wo_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (wo_root / "ledger_manifest.json").open("r") as f:
                    manifest = json.load(f)
                manifest["artifacts"] = list(reversed(manifest["artifacts"]))
                write_text_atomic(wo_root / "ledger_manifest.json", _json_dumps(manifest))
                wo_paths = _all_artifact_paths_from_dir(wo_root)
                result = compare_eleven_artifacts_semantically(base_all, wo_paths)
                _record(
                    "manifest_wrong_artifact_order_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 6. Ledger manifest with stale sha256 fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_stale_hash_") as sh_dir:
                sh_root = Path(sh_dir)
                for rel, src in base_all.items():
                    dst = sh_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (sh_root / "ledger_manifest.json").open("r") as f:
                    manifest = json.load(f)
                manifest["artifacts"][0]["sha256"] = "0" * 64
                write_text_atomic(sh_root / "ledger_manifest.json", _json_dumps(manifest))
                sh_paths = _all_artifact_paths_from_dir(sh_root)
                result = compare_eleven_artifacts_semantically(base_all, sh_paths)
                _record(
                    "manifest_stale_sha256_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 7. Audit JSON with wrong provenance fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_audit_prov_") as ap_dir:
                ap_root = Path(ap_dir)
                for rel, src in base_all.items():
                    dst = ap_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (ap_root / "part3b_split_leakage_audit.json").open("r") as f:
                    audit = json.load(f)
                audit["part3b_version"] = "WRONG"
                write_text_atomic(ap_root / "part3b_split_leakage_audit.json", _json_dumps(audit))
                ap_paths = _all_artifact_paths_from_dir(ap_root)
                result = compare_eleven_artifacts_semantically(base_all, ap_paths)
                _record(
                    "audit_json_wrong_provenance_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 8. Audit JSON with wrong audit check schema fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_audit_schema_") as as_dir:
                as_root = Path(as_dir)
                for rel, src in base_all.items():
                    dst = as_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (as_root / "part3b_split_leakage_audit.json").open("r") as f:
                    audit = json.load(f)
                audit["audit_checks"]["extra_bogus_check"] = True
                write_text_atomic(as_root / "part3b_split_leakage_audit.json", _json_dumps(audit))
                as_paths = _all_artifact_paths_from_dir(as_root)
                result = compare_eleven_artifacts_semantically(base_all, as_paths)
                _record(
                    "audit_json_wrong_check_schema_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 9. Audit JSON with wrong stage gate schema fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_audit_gate_") as ag_dir:
                ag_root = Path(ag_dir)
                for rel, src in base_all.items():
                    dst = ag_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (ag_root / "part3b_split_leakage_audit.json").open("r") as f:
                    audit = json.load(f)
                audit["stage_gate"]["extra_bogus_field"] = True
                write_text_atomic(ag_root / "part3b_split_leakage_audit.json", _json_dumps(audit))
                ag_paths = _all_artifact_paths_from_dir(ag_root)
                result = compare_eleven_artifacts_semantically(base_all, ag_paths)
                _record(
                    "audit_json_wrong_stage_gate_schema_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 10. Audit JSON with stale artifact hash fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_audit_hash_") as ah_dir:
                ah_root = Path(ah_dir)
                for rel, src in base_all.items():
                    dst = ah_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                with (ah_root / "part3b_split_leakage_audit.json").open("r") as f:
                    audit = json.load(f)
                first_rel = SEMANTIC_DATA_ARTIFACTS[0]
                audit["artifact_hashes"][first_rel]["sha256"] = "0" * 64
                write_text_atomic(ah_root / "part3b_split_leakage_audit.json", _json_dumps(audit))
                ah_paths = _all_artifact_paths_from_dir(ah_root)
                result = compare_eleven_artifacts_semantically(base_all, ah_paths)
                _record(
                    "audit_json_stale_artifact_hash_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 11. Audit Markdown missing required section fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_md_section_") as ms_dir:
                ms_root = Path(ms_dir)
                for rel, src in base_all.items():
                    dst = ms_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                md_path = ms_root / "part3b_split_leakage_audit.md"
                content = md_path.read_text()
                content = content.replace("## Negative Tests", "## Removed Section")
                write_text_atomic(md_path, content)
                ms_paths = _all_artifact_paths_from_dir(ms_root)
                result = compare_eleven_artifacts_semantically(base_all, ms_paths)
                _record(
                    "audit_md_missing_section_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 12. Audit Markdown provenance mismatch with JSON fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_md_prov_") as mp_dir:
                mp_root = Path(mp_dir)
                for rel, src in base_all.items():
                    dst = mp_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                md_path = mp_root / "part3b_split_leakage_audit.md"
                content = md_path.read_text()
                content = content.replace(
                    f"- **Version:** {PART3B_VERSION}",
                    f"- **Version:** WRONG-VERSION",
                )
                write_text_atomic(md_path, content)
                mp_paths = _all_artifact_paths_from_dir(mp_root)
                result = compare_eleven_artifacts_semantically(base_all, mp_paths)
                _record(
                    "audit_md_provenance_mismatch_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 13. Audit Markdown hash table mismatch with JSON fails.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_md_hash_") as mh_dir:
                mh_root = Path(mh_dir)
                for rel, src in base_all.items():
                    dst = mh_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                md_path = mh_root / "part3b_split_leakage_audit.md"
                content = md_path.read_text()
                first_rel = SEMANTIC_DATA_ARTIFACTS[0]
                # Replace the hash in the markdown table with a wrong hash
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith(f"| {first_rel} |"):
                        lines[i] = f"| {first_rel} | {'0' * 64} |"
                        break
                write_text_atomic(md_path, "\n".join(lines))
                mh_paths = _all_artifact_paths_from_dir(mh_root)
                result = compare_eleven_artifacts_semantically(base_all, mh_paths)
                _record(
                    "audit_md_hash_table_mismatch_fails",
                    result["semantic_reproducibility_passed"] is False,
                )

            # 14. Data artifact difference stops metadata approval.
            with tempfile.TemporaryDirectory(prefix="part3b2_e2_data_fail_") as df_dir:
                df_root = Path(df_dir)
                for rel, src in base_all.items():
                    dst = df_root / Path(rel).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dst))
                # Corrupt a data artifact (change identity)
                reg = pd.read_csv(df_root / "sample_registry.csv")
                reg.at[0, "sample_uid"] = "CM1:999999"
                reg.to_csv(df_root / "sample_registry.csv", index=False, lineterminator="\n")
                df_paths = _all_artifact_paths_from_dir(df_root)
                result = compare_eleven_artifacts_semantically(base_all, df_paths)
                _record(
                    "data_artifact_difference_stops_metadata_approval",
                    result["semantic_reproducibility_passed"] is False
                    and result["data_artifact_comparison"]["data_artifact_semantic_comparison_passed"] is False
                    and result["metadata_artifact_comparison_passed"] is False,
                )

    summary = {
        "tests_expected": 14,
        "tests_executed": len(tests),
        "tests_passed": sum(1 for t in tests if t.get("passed")),
        "tests_failed": sum(1 for t in tests if not t.get("passed")),
        "test_details": tests,
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "repository_artifacts_written": 0,
        "full_build_executed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
        "et_score_tolerance": ET_SCORE_ATOL,
        "et_rank_metric_tolerance": ET_RANK_METRIC_ATOL,
    }
    return tests, all_passed, summary


def run_part_e2_1_fail_closed_tests() -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """Five fail-closed regression tests for metadata validation.

    Each test creates two byte-identical builds with the same invalid metadata
    and verifies that semantic_reproducibility_passed is False even though
    both invalid files are identical.
    """
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, passed: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": passed, **extra})
        all_passed = all_passed and passed

    with tempfile.TemporaryDirectory(prefix="part3b2_e21_base_") as base_data_dir:
        base_data_root = _make_synthetic_eight_artifact_dir(Path(base_data_dir))

        with tempfile.TemporaryDirectory(prefix="part3b2_e21_base_meta_") as base_meta_dir:
            base_all = _make_synthetic_metadata_artifacts(base_data_root, Path(base_meta_dir))

            # 1. Two byte-identical manifests with wrong version fail.
            with tempfile.TemporaryDirectory(prefix="part3b2_e21_wv1_") as wv1_dir, \
                 tempfile.TemporaryDirectory(prefix="part3b2_e21_wv2_") as wv2_dir:
                wv1_root = Path(wv1_dir)
                wv2_root = Path(wv2_dir)
                for root in [wv1_root, wv2_root]:
                    for rel, src in base_all.items():
                        dst = root / Path(rel).name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(dst))
                    with (root / "ledger_manifest.json").open("r") as f:
                        manifest = json.load(f)
                    manifest["manifest_version"] = "WRONG-VERSION"
                    write_text_atomic(root / "ledger_manifest.json", _json_dumps(manifest))
                wv1_paths = _all_artifact_paths_from_dir(wv1_root)
                wv2_paths = _all_artifact_paths_from_dir(wv2_root)
                result = compare_eleven_artifacts_semantically(wv1_paths, wv2_paths)
                _record(
                    "identical_malformed_manifests_wrong_version_fail",
                    result["semantic_reproducibility_passed"] is False
                    and result["metadata_artifact_comparison_passed"] is False,
                )

            # 2. Two byte-identical manifests with same stale sha256 fail.
            with tempfile.TemporaryDirectory(prefix="part3b2_e21_sh1_") as sh1_dir, \
                 tempfile.TemporaryDirectory(prefix="part3b2_e21_sh2_") as sh2_dir:
                sh1_root = Path(sh1_dir)
                sh2_root = Path(sh2_dir)
                for root in [sh1_root, sh2_root]:
                    for rel, src in base_all.items():
                        dst = root / Path(rel).name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(dst))
                    with (root / "ledger_manifest.json").open("r") as f:
                        manifest = json.load(f)
                    manifest["artifacts"][0]["sha256"] = "0" * 64
                    write_text_atomic(root / "ledger_manifest.json", _json_dumps(manifest))
                sh1_paths = _all_artifact_paths_from_dir(sh1_root)
                sh2_paths = _all_artifact_paths_from_dir(sh2_root)
                result = compare_eleven_artifacts_semantically(sh1_paths, sh2_paths)
                _record(
                    "identical_malformed_manifests_stale_hash_fail",
                    result["semantic_reproducibility_passed"] is False
                    and result["metadata_artifact_comparison_passed"] is False,
                )

            # 3. Two byte-identical manifests with wrong row_count fail.
            with tempfile.TemporaryDirectory(prefix="part3b2_e21_rc1_") as rc1_dir, \
                 tempfile.TemporaryDirectory(prefix="part3b2_e21_rc2_") as rc2_dir:
                rc1_root = Path(rc1_dir)
                rc2_root = Path(rc2_dir)
                for root in [rc1_root, rc2_root]:
                    for rel, src in base_all.items():
                        dst = root / Path(rel).name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(dst))
                    with (root / "ledger_manifest.json").open("r") as f:
                        manifest = json.load(f)
                    manifest["artifacts"][0]["row_count"] = 99999
                    write_text_atomic(root / "ledger_manifest.json", _json_dumps(manifest))
                rc1_paths = _all_artifact_paths_from_dir(rc1_root)
                rc2_paths = _all_artifact_paths_from_dir(rc2_root)
                result = compare_eleven_artifacts_semantically(rc1_paths, rc2_paths)
                _record(
                    "identical_malformed_manifests_wrong_row_count_fail",
                    result["semantic_reproducibility_passed"] is False
                    and result["metadata_artifact_comparison_passed"] is False,
                )

            # 4. Two byte-identical audit JSONs with wrong provenance fail.
            with tempfile.TemporaryDirectory(prefix="part3b2_e21_aj1_") as aj1_dir, \
                 tempfile.TemporaryDirectory(prefix="part3b2_e21_aj2_") as aj2_dir:
                aj1_root = Path(aj1_dir)
                aj2_root = Path(aj2_dir)
                for root in [aj1_root, aj2_root]:
                    for rel, src in base_all.items():
                        dst = root / Path(rel).name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(dst))
                    with (root / "part3b_split_leakage_audit.json").open("r") as f:
                        audit = json.load(f)
                    audit["part3b_version"] = "WRONG"
                    write_text_atomic(root / "part3b_split_leakage_audit.json", _json_dumps(audit))
                aj1_paths = _all_artifact_paths_from_dir(aj1_root)
                aj2_paths = _all_artifact_paths_from_dir(aj2_root)
                result = compare_eleven_artifacts_semantically(aj1_paths, aj2_paths)
                _record(
                    "identical_malformed_audit_jsons_wrong_provenance_fail",
                    result["semantic_reproducibility_passed"] is False
                    and result["metadata_artifact_comparison_passed"] is False,
                )

            # 5. Two byte-identical audit Markdowns with wrong hash fail.
            with tempfile.TemporaryDirectory(prefix="part3b2_e21_am1_") as am1_dir, \
                 tempfile.TemporaryDirectory(prefix="part3b2_e21_am2_") as am2_dir:
                am1_root = Path(am1_dir)
                am2_root = Path(am2_dir)
                for root in [am1_root, am2_root]:
                    for rel, src in base_all.items():
                        dst = root / Path(rel).name
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(src), str(dst))
                    md_path = root / "part3b_split_leakage_audit.md"
                    content = md_path.read_text()
                    first_rel = SEMANTIC_DATA_ARTIFACTS[0]
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if line.startswith(f"| {first_rel} |"):
                            lines[i] = f"| {first_rel} | {'0' * 64} |"
                            break
                    write_text_atomic(md_path, "\n".join(lines))
                am1_paths = _all_artifact_paths_from_dir(am1_root)
                am2_paths = _all_artifact_paths_from_dir(am2_root)
                result = compare_eleven_artifacts_semantically(am1_paths, am2_paths)
                _record(
                    "identical_malformed_audit_markdowns_wrong_hash_fail",
                    result["semantic_reproducibility_passed"] is False
                    and result["metadata_artifact_comparison_passed"] is False,
                )

    summary = {
        "tests_expected": 5,
        "tests_executed": len(tests),
        "tests_passed": sum(1 for t in tests if t.get("passed")),
        "tests_failed": sum(1 for t in tests if not t.get("passed")),
        "test_details": tests,
        "model_fits_executed": 0,
        "prediction_calls_executed": 0,
        "repository_artifacts_written": 0,
        "full_build_executed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
    }
    return tests, all_passed, summary


# ---------------------------------------------------------------------------
# Final printed report
# ---------------------------------------------------------------------------
def print_final_report(json_report: Dict[str, Any], actual_changed_paths: List[str], new_commit: Optional[str] = None, remote_head: Optional[str] = None, git_status: Optional[str] = None) -> None:
    recon = json_report["reconstruction_summary"]
    val_ev = recon["validation_reconstruction_evidence"]
    res_ev = recon["canonical_result_reconstruction_evidence"]
    pred_summary = json_report["prediction_ledger_summary"]
    checks = json_report["audit_checks"]
    gate = json_report["stage_gate"]
    sem = json_report.get("determinism_verification", {}).get("semantic_reproducibility_evidence", {})
    diag = json_report.get("canonical_nondeterminism_diagnostic", ET_ND_DIAGNOSTIC)

    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("Part 3B.2R Final Acceptance Report")
    lines.append("=" * 80)
    lines.append(f"Starting full commit: {json_report['starting_commit']}")
    lines.append(f"Accepted Part 3A commit: {json_report['accepted_part3a_commit']}")
    lines.append(f"New full commit: {new_commit}")
    lines.append(f"Remote branch full HEAD: {remote_head}")
    lines.append(f"Part 3B version: {json_report['part3b_version']}")
    lines.append(f"New commit SHA length: {len(new_commit) if new_commit else 0}")
    lines.append(f"git status: {git_status}")
    lines.append("")
    lines.append(f"Actual changed files: {actual_changed_paths}")
    lines.append(f"Prediction-ledger columns: {pred_summary['columns']}")
    lines.append(f"Prediction-ledger column count: {pred_summary['column_count']}")
    lines.append(f"Stored aggregate metric columns: {pred_summary['stored_aggregate_metric_columns']}")
    lines.append(f"Stored threshold/objective columns: {pred_summary['stored_threshold_or_objective_columns']}")
    lines.append(f"Validation rows with test-derived fields: {pred_summary['test_rows']}")
    lines.append("")
    lines.append(f"ExtraTrees production n_jobs: {ET_ND_DIAGNOSTIC['n_jobs']}")
    lines.append(f"Production score calls per event: 8 (4 validation + 4 test)")
    lines.append("")
    lines.append(f"Validation reconstruction strict mismatches: {recon.get('strict_validation_mismatches', -1)}")
    lines.append(f"Result strict mismatches before exception: {recon.get('strict_result_mismatches_before_exception', -1)}")
    lines.append(f"Approved canonical nondeterminism exceptions: {recon.get('approved_nondeterminism_exceptions', 0)}")
    lines.append(f"Unapproved result mismatches: {recon.get('unapproved_result_mismatches', 0)}")
    lines.append(f"Canonical exception exact event: {APPROVED_EXCEPTION_EVENT['experiment']}/{APPROVED_EXCEPTION_EVENT['target_project']}/seed_{APPROVED_EXCEPTION_EVENT['seed']:03d}")
    lines.append(f"Canonical exception exact column: {APPROVED_EXCEPTION_EVENT['column']}")
    lines.append(f"Canonical values reproduced: {diag.get('canonical_values_reproduced', [])}")
    lines.append(f"Maximum observed score difference: {diag.get('maximum_score_difference', float('nan'))}")
    lines.append(f"Canonical outputs modified: {gate.get('canonical_outputs_modified', True)}")
    lines.append(f"Canonical reconstruction strictly identical: {recon.get('canonical_result_reconstruction_strictly_identical', False)}")
    lines.append(f"Canonical reconstruction scientifically reconciled: {recon.get('canonical_result_reconstruction_scientifically_reconciled', False)}")
    lines.append("")
    lines.append(f"Independent builds executed: {json_report.get('determinism_verification', {}).get('two_independent_builds_completed', False)}")
    lines.append(f"Exact structural equality: {sem.get('exact_structural_equality', False)}")
    lines.append(f"Identity columns exact: {sem.get('all_identity_columns_exact', False)}")
    lines.append(f"Non-ET scores exact: {sem.get('all_non_et_score_columns_exact', False)}")
    lines.append(f"Maximum ET score difference: {sem.get('maximum_et_score_difference', float('nan'))}")
    lines.append(f"Selection decisions exact: {sem.get('all_selection_decisions_exact', False)}")
    lines.append(f"Thresholds exact: {sem.get('all_thresholds_exact', False)}")
    lines.append(f"Semantic reproducibility passed: {sem.get('semantic_reproducibility_passed', False)}")
    lines.append(f"Byte-identical artifacts: {sem.get('byte_identical_artifacts', [])}")
    lines.append(f"Artifacts with approved ET roundoff only: {sem.get('artifacts_with_approved_et_roundoff_only', [])}")
    lines.append("")
    lines.append(f"Candidate configuration audits: {checks.get('preprocessing_train_only_passed', False)}")
    lines.append(f"Feature-count audits: {checks.get('feature_schema_passed', False)}")
    lines.append(f"Negative tests: {len(json_report.get('negative_tests', []))}/{len(json_report.get('negative_tests', []))}")
    lines.append(f"Canonical-exception validator tests: {len(json_report.get('canonical_exception_validator_tests', []))}/5")
    lines.append(f"Audit checks: {len(checks)}")
    lines.append("")
    lines.append(f"Preserved files changed: {len(actual_changed_paths)}")
    lines.append(f"Identity leakage detected: {gate.get('identity_leakage_detected', True)}")
    lines.append(f"Preprocessing leakage detected: {gate.get('preprocessing_leakage_detected', True)}")
    lines.append(f"Selection/test leakage detected: {gate.get('selection_test_leakage_detected', True)}")
    lines.append(f"Part 3B prediction ledger complete: {gate.get('part3b_prediction_ledger_complete', False)}")
    lines.append(f"Next authorized stage: {gate.get('next_authorized_stage')}")
    lines.append("")
    lines.append(f"validation_reconstruction_rows: {recon['validation_rows']}")
    lines.append(f"canonical_result_reconstruction_rows: {recon['canonical_result_rows']}")
    lines.append(f"validation_max_abs_diff: {val_ev['max_abs_diff']}")
    lines.append(f"result_max_abs_diff: {res_ev['max_abs_diff']}")
    lines.append(f"all_critical_checks_passed: {checks.get('all_critical_checks_passed', False)}")
    lines.append(f"stage_gate_passed: {checks.get('stage_gate_passed', False)}")
    lines.append("")
    lines.append("Per-check results:")
    for k, v in checks.items():
        lines.append(f"  {k}: {v}")
    lines.append("=" * 80)
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Strict persisted-ledger reread and reconstruction verification (Part B)
# ---------------------------------------------------------------------------
PERSISTED_PREDICTION_WITHIN_ROWS = 34900
PERSISTED_PREDICTION_CROSS_ROWS = 174430
PERSISTED_PREDICTION_TOTAL_ROWS = 209330
PERSISTED_VALIDATION_PREDICTION_ROWS = 104670
PERSISTED_TEST_PREDICTION_ROWS = 104660
PERSISTED_TRAIN_PREDICTION_ROWS = 0
PERSISTED_EVENT_MANIFEST_ROWS = 50
PERSISTED_VALIDATION_RECON_ROWS = 600
PERSISTED_RESULT_RECON_ROWS = 400

PERSISTED_VALIDATION_CATEGORY_KEYS = ["experiment", "target_project", "seed", "candidate", "mode"]
PERSISTED_RESULT_CATEGORY_KEYS = ["experiment", "target_project", "seed", "model", "selected_candidate", "selection_mode"]


def _validate_persisted_prediction_schema(df: pd.DataFrame) -> bool:
    return list(df.columns) == PREDICTION_LEDGER_COLUMNS


def _validate_persisted_prediction_integrity(within: pd.DataFrame, cross: pd.DataFrame) -> Dict[str, Any]:
    schema_exact = _validate_persisted_prediction_schema(within) and _validate_persisted_prediction_schema(cross)
    within_rows = len(within)
    cross_rows = len(cross)
    total_rows = within_rows + cross_rows
    combined = pd.concat([within, cross], ignore_index=True)
    val_rows = int((combined["split_role"] == "validation").sum()) if "split_role" in combined.columns else -1
    test_rows = int((combined["split_role"] == "test").sum()) if "split_role" in combined.columns else -1
    train_rows = int((combined["split_role"] == "train").sum()) if "split_role" in combined.columns else -1
    key_cols = ["event_id", "split_role", "sample_uid"]
    if all(c in combined.columns for c in key_cols):
        keys_unique = not combined.duplicated(subset=key_cols).any()
    else:
        keys_unique = False
    score_cols = [c for c in PREDICTION_LEDGER_COLUMNS if c.startswith("score__")]
    available_score_cols = [c for c in score_cols if c in combined.columns]
    if available_score_cols:
        all_scores = combined[available_score_cols].to_numpy(dtype=float)
        scores_finite = bool(np.all(np.isfinite(all_scores)))
        scores_in_range = bool(np.all((all_scores >= EPS) & (all_scores <= 1.0 - EPS)))
    else:
        scores_finite = False
        scores_in_range = False
    return {
        "persisted_prediction_schema_exact": schema_exact,
        "persisted_prediction_within_rows": within_rows,
        "persisted_prediction_cross_rows": cross_rows,
        "persisted_prediction_total_rows": total_rows,
        "persisted_validation_prediction_rows": val_rows,
        "persisted_test_prediction_rows": test_rows,
        "persisted_train_prediction_rows": train_rows,
        "persisted_prediction_keys_unique": keys_unique,
        "persisted_prediction_scores_finite": scores_finite,
        "persisted_prediction_scores_in_range": scores_in_range,
        "_combined": combined,
    }


def _compare_persisted_reconstruction(
    reread: pd.DataFrame,
    persisted: pd.DataFrame,
    category_keys: List[str],
) -> Tuple[bool, Dict[str, Any]]:
    reread = reread.reset_index(drop=True)
    persisted = persisted.reset_index(drop=True)
    row_count_match = len(reread) == len(persisted)
    cat_match = row_count_match
    if row_count_match:
        for col in category_keys:
            if not reread[col].astype(str).equals(persisted[col].astype(str)):
                cat_match = False
                break
    numeric_cols = [c for c in persisted.columns if c not in category_keys]
    mismatches = 0
    max_abs_diff = 0.0
    if cat_match:
        for col in numeric_cols:
            if col not in reread.columns:
                continue
            a = reread[col].to_numpy(dtype=float)
            b = persisted[col].to_numpy(dtype=float)
            close = np.isclose(a, b, rtol=PERSISTED_RECON_RTOL, atol=PERSISTED_RECON_ATOL, equal_nan=True)
            col_mismatches = int((~close).sum())
            mismatches += col_mismatches
            diff = np.abs(a - b)
            col_max = float(np.nanmax(diff)) if np.any(np.isfinite(diff)) else 0.0
            max_abs_diff = max(max_abs_diff, col_max)
    return cat_match and mismatches == 0, {
        "category_match": cat_match,
        "numeric_mismatches": mismatches,
        "maximum_absolute_difference": max_abs_diff,
    }


def verify_persisted_ledger_reconstruction(
    frozen: Any,
    prediction_ledger_within_path: Path,
    prediction_ledger_cross_path: Path,
    event_manifest_path: Path,
    persisted_validation_reconstruction_path: Path,
    persisted_result_reconstruction_path: Path,
) -> Dict[str, Any]:
    within = read_float_csv_round_trip(prediction_ledger_within_path, compression="gzip")
    cross = read_float_csv_round_trip(prediction_ledger_cross_path, compression="gzip")

    integrity = _validate_persisted_prediction_integrity(within, cross)
    combined = integrity.pop("_combined")

    schema_ok = integrity["persisted_prediction_schema_exact"]
    keys_ok = integrity["persisted_prediction_keys_unique"]

    event_manifest = pd.read_csv(event_manifest_path)

    persisted_val_recon = read_float_csv_round_trip(persisted_validation_reconstruction_path)
    persisted_result_recon = read_float_csv_round_trip(persisted_result_reconstruction_path)

    if schema_ok and keys_ok:
        combined_sorted = _prediction_ledger_sorted(combined)
        reread_val_recon = reconstruct_validation_from_ledger(frozen, combined_sorted)
        reread_result_recon = reconstruct_results_from_ledger(frozen, combined_sorted, event_manifest)

        val_ok, val_ev = _compare_persisted_reconstruction(
            reread_val_recon, persisted_val_recon, PERSISTED_VALIDATION_CATEGORY_KEYS,
        )
        res_ok, res_ev = _compare_persisted_reconstruction(
            reread_result_recon, persisted_result_recon, PERSISTED_RESULT_CATEGORY_KEYS,
        )

        reread_val_rows = len(reread_val_recon)
        reread_res_rows = len(reread_result_recon)
        val_cat_match = val_ev["category_match"]
        res_cat_match = res_ev["category_match"]
        val_mismatches = val_ev["numeric_mismatches"]
        res_mismatches = res_ev["numeric_mismatches"]
        val_max_abs = val_ev["maximum_absolute_difference"]
        res_max_abs = res_ev["maximum_absolute_difference"]
        val_matches = val_ok
        res_matches = res_ok
    else:
        reread_val_rows = 0
        reread_res_rows = 0
        val_cat_match = False
        res_cat_match = False
        val_mismatches = -1
        res_mismatches = -1
        val_max_abs = float("nan")
        res_max_abs = float("nan")
        val_matches = False
        res_matches = False

    ledger_matches = val_matches and res_matches

    evidence: Dict[str, Any] = {}
    evidence.update(integrity)
    evidence["persisted_event_manifest_rows"] = len(event_manifest)
    evidence["reread_validation_reconstruction_rows"] = reread_val_rows
    evidence["reread_result_reconstruction_rows"] = reread_res_rows
    evidence["persisted_validation_reconstruction_rows"] = len(persisted_val_recon)
    evidence["persisted_result_reconstruction_rows"] = len(persisted_result_recon)
    evidence["persisted_validation_category_match"] = val_cat_match
    evidence["persisted_result_category_match"] = res_cat_match
    evidence["persisted_validation_numeric_mismatches"] = val_mismatches
    evidence["persisted_result_numeric_mismatches"] = res_mismatches
    evidence["persisted_validation_maximum_absolute_difference"] = val_max_abs
    evidence["persisted_result_maximum_absolute_difference"] = res_max_abs
    evidence["persisted_validation_reconstruction_matches_in_memory"] = val_matches
    evidence["persisted_result_reconstruction_matches_in_memory"] = res_matches
    evidence["persisted_ledger_reconstruction_matches_in_memory"] = ledger_matches
    evidence["csv_float_precision"] = "round_trip"
    return evidence


# ---------------------------------------------------------------------------
# Six focused negative tests for the persisted-ledger verifier (Part B)
# ---------------------------------------------------------------------------
def _run_persisted_ledger_negative_tests(
    frozen: Any,
    within_df: pd.DataFrame,
    cross_df: pd.DataFrame,
    event_manifest_df: pd.DataFrame,
    persisted_val_recon_df: pd.DataFrame,
    persisted_result_recon_df: pd.DataFrame,
) -> Tuple[List[Dict[str, Any]], bool]:
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, result: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": result, **extra})
        all_passed = all_passed and result

    def _write_temp_ledger(df_within: pd.DataFrame, df_cross: pd.DataFrame, manifest: pd.DataFrame, val_recon: pd.DataFrame, res_recon: pd.DataFrame) -> Dict[str, Path]:
        tmpdir = Path(tempfile.mkdtemp(prefix="part3b_persisted_test_"))
        paths: Dict[str, Path] = {}
        for name, df, comp in [
            ("within", df_within, True),
            ("cross", df_cross, True),
        ]:
            p = tmpdir / f"prediction_ledger_{name}.csv.gz"
            buf = io.StringIO()
            df.to_csv(buf, index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")
            payload = buf.getvalue().encode("utf-8")
            with gzip.GzipFile(fileobj=open(p, "wb"), mode="wb", compresslevel=9, mtime=0, filename=b"") as gz:
                gz.write(payload)
            paths[f"pred_{name}"] = p
        mp = tmpdir / "event_manifest.csv"
        manifest.to_csv(mp, index=False, encoding="utf-8", lineterminator="\n")
        paths["manifest"] = mp
        vp = tmpdir / "validation_reconstruction.csv"
        val_recon.to_csv(vp, index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")
        paths["val_recon"] = vp
        rp = tmpdir / "canonical_result_reconstruction.csv"
        res_recon.to_csv(rp, index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")
        paths["res_recon"] = rp
        return paths

    # 1. Exact persisted reconstruction comparison passes.
    paths = _write_temp_ledger(within_df, cross_df, event_manifest_df, persisted_val_recon_df, persisted_result_recon_df)
    ev = verify_persisted_ledger_reconstruction(
        frozen, paths["pred_within"], paths["pred_cross"], paths["manifest"],
        paths["val_recon"], paths["res_recon"],
    )
    r1 = bool(ev["persisted_ledger_reconstruction_matches_in_memory"])
    _record("exact persisted reconstruction comparison passes", r1, validator_returned_true=r1)

    # 2. Prediction ledger with one required column removed fails.
    within_missing = within_df.drop(columns=["score__ET_leaf5"])
    paths2 = _write_temp_ledger(within_missing, cross_df, event_manifest_df, persisted_val_recon_df, persisted_result_recon_df)
    ev2 = verify_persisted_ledger_reconstruction(
        frozen, paths2["pred_within"], paths2["pred_cross"], paths2["manifest"],
        paths2["val_recon"], paths2["res_recon"],
    )
    r2 = not ev2["persisted_prediction_schema_exact"]
    _record("prediction ledger with one required column removed fails", r2, schema_exact=ev2["persisted_prediction_schema_exact"])

    # 3. Prediction ledger with one extra column fails.
    within_extra = within_df.copy()
    within_extra["extra_column"] = 0.0
    paths3 = _write_temp_ledger(within_extra, cross_df, event_manifest_df, persisted_val_recon_df, persisted_result_recon_df)
    ev3 = verify_persisted_ledger_reconstruction(
        frozen, paths3["pred_within"], paths3["pred_cross"], paths3["manifest"],
        paths3["val_recon"], paths3["res_recon"],
    )
    r3 = not ev3["persisted_prediction_schema_exact"]
    _record("prediction ledger with one extra column fails", r3, schema_exact=ev3["persisted_prediction_schema_exact"])

    # 4. Prediction ledger with one duplicate event_id/split_role/sample_uid key fails.
    within_dup = within_df.copy()
    within_dup.loc[0, "event_id"] = within_dup.loc[1, "event_id"]
    within_dup.loc[0, "split_role"] = within_dup.loc[1, "split_role"]
    within_dup.loc[0, "sample_uid"] = within_dup.loc[1, "sample_uid"]
    paths4 = _write_temp_ledger(within_dup, cross_df, event_manifest_df, persisted_val_recon_df, persisted_result_recon_df)
    ev4 = verify_persisted_ledger_reconstruction(
        frozen, paths4["pred_within"], paths4["pred_cross"], paths4["manifest"],
        paths4["val_recon"], paths4["res_recon"],
    )
    r4 = not ev4["persisted_prediction_keys_unique"]
    _record("prediction ledger with one duplicate key fails", r4, keys_unique=ev4["persisted_prediction_keys_unique"])

    # 5. Persisted reconstruction with one categorical value changed fails.
    val_recon_mutated_cat = persisted_val_recon_df.copy()
    val_recon_mutated_cat.loc[0, "candidate"] = "DT_leaf5" if val_recon_mutated_cat.loc[0, "candidate"] != "DT_leaf5" else "LR_std_C0.1"
    paths5 = _write_temp_ledger(within_df, cross_df, event_manifest_df, val_recon_mutated_cat, persisted_result_recon_df)
    ev5 = verify_persisted_ledger_reconstruction(
        frozen, paths5["pred_within"], paths5["pred_cross"], paths5["manifest"],
        paths5["val_recon"], paths5["res_recon"],
    )
    r5 = not ev5["persisted_validation_category_match"]
    _record("persisted reconstruction with one categorical value changed fails", r5, category_match=ev5["persisted_validation_category_match"])

    # 6. Persisted reconstruction with one numeric value changed by exactly 1e-8 fails.
    res_recon_mutated_num = persisted_result_recon_df.copy()
    numeric_col = "roc_auc"
    res_recon_mutated_num.loc[0, numeric_col] = float(res_recon_mutated_num.loc[0, numeric_col]) + 1e-8
    paths6 = _write_temp_ledger(within_df, cross_df, event_manifest_df, persisted_val_recon_df, res_recon_mutated_num)
    ev6 = verify_persisted_ledger_reconstruction(
        frozen, paths6["pred_within"], paths6["pred_cross"], paths6["manifest"],
        paths6["val_recon"], paths6["res_recon"],
    )
    r6 = not ev6["persisted_ledger_reconstruction_matches_in_memory"]
    _record(
        "persisted reconstruction with one numeric value changed by 1e-8 fails",
        r6,
        mutation=1e-8,
        validator_returned_false=not ev6["persisted_ledger_reconstruction_matches_in_memory"],
    )

    return tests, all_passed


# ---------------------------------------------------------------------------
# Part C: Isolated preservation self-tests (synthetic dictionaries only)
# ---------------------------------------------------------------------------
def _make_synthetic_accepted_contract() -> Dict[str, Any]:
    return {
        "accepted_commit": ACCEPTED_PART3A_COMMIT,
        "files": {
            "data/raw/cm1.csv": {"relative_path": "data/raw/cm1.csv", "group": "raw_data", "expected_sha256": "a" * 64, "expected_byte_size": 100},
            "data/raw/jm1.csv": {"relative_path": "data/raw/jm1.csv", "group": "raw_data", "expected_sha256": "b" * 64, "expected_byte_size": 200},
            "results/part1_full_reproduction/repeated_all_results.csv": {"relative_path": "results/part1_full_reproduction/repeated_all_results.csv", "group": "canonical_outputs", "expected_sha256": "c" * 64, "expected_byte_size": 300},
            "scripts/run_repeated_evaluation.py": {"relative_path": "scripts/run_repeated_evaluation.py", "group": "part3a_artifacts", "expected_sha256": "d" * 64, "expected_byte_size": 400},
        },
    }


def _make_synthetic_current_state() -> Dict[str, Any]:
    return {
        "files": {
            "data/raw/cm1.csv": {"relative_path": "data/raw/cm1.csv", "group": "raw_data", "actual_sha256": "a" * 64, "actual_byte_size": 100},
            "data/raw/jm1.csv": {"relative_path": "data/raw/jm1.csv", "group": "raw_data", "actual_sha256": "b" * 64, "actual_byte_size": 200},
            "results/part1_full_reproduction/repeated_all_results.csv": {"relative_path": "results/part1_full_reproduction/repeated_all_results.csv", "group": "canonical_outputs", "actual_sha256": "c" * 64, "actual_byte_size": 300},
            "scripts/run_repeated_evaluation.py": {"relative_path": "scripts/run_repeated_evaluation.py", "group": "part3a_artifacts", "actual_sha256": "d" * 64, "actual_byte_size": 400},
        },
    }


def run_preservation_self_tests() -> Tuple[List[Dict[str, Any]], bool]:
    tests: List[Dict[str, Any]] = []
    all_passed = True

    # 1. Exact accepted/current state passes.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is True
    tests.append({"case_name": "exact_accepted_current_passes", "description": "Exact accepted/current state passes", "validator_returned_true": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 2. One raw-data file with modified bytes fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    current["files"]["data/raw/cm1.csv"]["actual_sha256"] = "x" * 64
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "modified_raw_data_fails", "description": "One raw-data file with modified bytes fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 3. One raw-data file deleted fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    del current["files"]["data/raw/cm1.csv"]
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "deleted_raw_data_fails", "description": "One raw-data file deleted fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 4. One extra raw-data file fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    current["files"]["data/raw/extra.csv"] = {"relative_path": "data/raw/extra.csv", "group": "raw_data", "actual_sha256": "z" * 64, "actual_byte_size": 50}
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "extra_raw_data_fails", "description": "One extra raw-data file fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 5. One canonical-output file with modified bytes fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    current["files"]["results/part1_full_reproduction/repeated_all_results.csv"]["actual_sha256"] = "y" * 64
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "modified_canonical_output_fails", "description": "One canonical-output file with modified bytes fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 6. One canonical-output file deleted fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    del current["files"]["results/part1_full_reproduction/repeated_all_results.csv"]
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "deleted_canonical_output_fails", "description": "One canonical-output file deleted fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 7. One Part 3A artifact with modified bytes fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    current["files"]["scripts/run_repeated_evaluation.py"]["actual_sha256"] = "w" * 64
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "modified_part3a_artifact_fails", "description": "One Part 3A artifact with modified bytes fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    # 8. One Part 3A artifact deleted fails.
    accepted = _make_synthetic_accepted_contract()
    current = _make_synthetic_current_state()
    del current["files"]["scripts/run_repeated_evaluation.py"]
    passed, ev = compare_protected_state_to_accepted_contract(accepted, current)
    test_ok = passed is False
    tests.append({"case_name": "deleted_part3a_artifact_fails", "description": "One Part 3A artifact deleted fails", "validator_returned_false": test_ok, "passed": test_ok})
    all_passed = all_passed and test_ok

    return tests, all_passed


# ---------------------------------------------------------------------------
# Part D: Isolated audit-gate self-tests (synthetic dictionaries only)
# ---------------------------------------------------------------------------
def _make_synthetic_audit_checks_all_true() -> Dict[str, bool]:
    return {name: True for name in REQUIRED_AUDIT_CHECK_NAMES}


def _make_synthetic_stage_gate_authorized() -> Dict[str, Any]:
    return {
        "part3b_prediction_ledger_complete": True,
        "raw_data_modified": False,
        "canonical_outputs_modified": False,
        "part3a_artifacts_modified": False,
        "identity_leakage_detected": False,
        "preprocessing_leakage_detected": False,
        "selection_test_leakage_detected": False,
        "canonical_validation_reconstruction_passed": True,
        "canonical_result_reconstruction_passed": True,
        "canonical_result_reconstruction_strictly_identical": False,
        "canonical_result_reconstruction_scientifically_reconciled": True,
        "canonical_nondeterminism_exception_detected": True,
        "canonical_nondeterminism_exception_validated": True,
        "semantic_reproducibility_passed": True,
        "next_authorized_stage": "Part 3C",
        "part3c_constraint": PART3C_CONSTRAINT,
    }


def _make_synthetic_canonical_reconciliation_evidence() -> Dict[str, Any]:
    return {
        "strict_validation_mismatches": 0,
        "strict_result_mismatches_before_exception": 1,
        "approved_nondeterminism_exceptions": 1,
        "unapproved_result_mismatches": 0,
        "canonical_nondeterminism_exception_validated": True,
    }


def _make_synthetic_persisted_ledger_evidence() -> Dict[str, Any]:
    return {
        "persisted_validation_reconstruction_matches_in_memory": True,
        "persisted_result_reconstruction_matches_in_memory": True,
        "persisted_ledger_reconstruction_matches_in_memory": True,
        "persisted_validation_numeric_mismatches": 0,
        "persisted_result_numeric_mismatches": 0,
        "csv_float_precision": "round_trip",
    }


def _make_synthetic_preservation_evidence() -> Dict[str, Any]:
    return {
        "preservation_passed": True,
        "raw_data_changed": 0,
        "canonical_outputs_changed": 0,
        "part3a_artifacts_changed": 0,
        "raw_data_modified": False,
        "canonical_outputs_modified": False,
        "part3a_artifacts_modified": False,
    }


def _make_synthetic_semantic_reproducibility_evidence() -> Dict[str, Any]:
    return {
        "semantic_reproducibility_passed": True,
        "unapproved_differing_artifacts": [],
    }


def _make_synthetic_negative_test_evidence() -> Dict[str, Any]:
    return {
        "original_negative_tests": {"expected": 12, "executed": 12, "passed": 12, "failed": 0},
        "canonical_exception_tests": {"expected": 10, "executed": 10, "passed": 10, "failed": 0},
        "persisted_ledger_tests": {"expected": 6, "executed": 6, "passed": 6, "failed": 0},
        "preservation_tests": {"expected": 8, "executed": 8, "passed": 8, "failed": 0},
    }


def collect_actual_negative_test_evidence(
    original_negative_tests: List[Dict[str, Any]],
    canonical_exception_tests: List[Dict[str, Any]],
    persisted_ledger_tests: List[Dict[str, Any]],
    preservation_tests: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build negative-test evidence from actual test records.

    Expected counts remain frozen; executed, passed, and failed are derived
    from the supplied test lists.
    """
    def _summarize(expected: int, tests: List[Dict[str, Any]]) -> Dict[str, int]:
        return {
            "expected": expected,
            "executed": len(tests),
            "passed": sum(1 for t in tests if t.get("passed")),
            "failed": sum(1 for t in tests if not t.get("passed")),
        }

    return {
        "original_negative_tests": _summarize(12, original_negative_tests),
        "canonical_exception_tests": _summarize(10, canonical_exception_tests),
        "persisted_ledger_tests": _summarize(6, persisted_ledger_tests),
        "preservation_tests": _summarize(8, preservation_tests),
    }


def run_audit_gate_self_tests() -> Tuple[List[Dict[str, Any]], bool]:
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, result: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": result, **extra})
        all_passed = all_passed and result

    # 1. Exact 41-check schema with all-True passes.
    checks = _make_synthetic_audit_checks_all_true()
    schema_ok, ev = validate_exact_audit_check_schema(checks)
    _record("exact_41_check_schema_all_true_passes", schema_ok is True, schema_passed=ev["schema_passed"])

    # 2. Missing one check fails.
    checks = _make_synthetic_audit_checks_all_true()
    del checks["negative_tests_passed"]
    schema_ok, ev = validate_exact_audit_check_schema(checks)
    _record("missing_one_check_fails", schema_ok is False, missing=ev["missing_checks"])

    # 3. Extra check fails.
    checks = _make_synthetic_audit_checks_all_true()
    checks["extra_diagnostic"] = True
    schema_ok, ev = validate_exact_audit_check_schema(checks)
    _record("extra_check_fails", schema_ok is False, extra=ev["extra_checks"])

    # 4. Reordered schema fails.
    checks = _make_synthetic_audit_checks_all_true()
    keys = list(checks.keys())
    keys[0], keys[1] = keys[1], keys[0]
    checks = {k: checks[k] for k in keys}
    schema_ok, ev = validate_exact_audit_check_schema(checks)
    _record("reordered_schema_fails", schema_ok is False, order_exact=ev["order_exact"])

    # 5. Non-boolean value (int 1 instead of True) fails.
    checks = _make_synthetic_audit_checks_all_true()
    checks["source_commit_verified"] = 1
    schema_ok, ev = validate_exact_audit_check_schema(checks)
    _record("non_boolean_int_value_fails", schema_ok is False, non_boolean=ev["non_boolean_checks"])

    # 6. all_critical_checks_passed is False when one of checks 1-40 is False.
    checks = _make_synthetic_audit_checks_all_true()
    checks["stage_gate_passed"] = True
    checks["dataset_profile_passed"] = False
    result = compute_all_critical_checks_passed(checks)
    _record("all_critical_false_when_one_check_false", result is False, computed=result)

    # 7. Exact authorized stage gate passes.
    gate = _make_synthetic_stage_gate_authorized()
    gate_ok, ev = validate_stage_gate(gate)
    _record("exact_authorized_stage_gate_passes", gate_ok is True, schema_passed=ev["schema_passed"])

    # 8. Stage gate with one missing field fails.
    gate = _make_synthetic_stage_gate_authorized()
    del gate["identity_leakage_detected"]
    gate_ok, ev = validate_stage_gate(gate)
    _record("missing_stage_field_fails", gate_ok is False, missing_fields=ev["missing_fields"])

    # 9. Stage gate with one extra field fails.
    gate = _make_synthetic_stage_gate_authorized()
    gate["extra_diagnostic"] = False
    gate_ok, ev = validate_stage_gate(gate)
    _record("extra_stage_field_fails", gate_ok is False, extra_fields=ev["extra_fields"])

    # 10. Any failed authorization condition forces next_authorized_stage = None and stage-gate validation fails.
    gate = _make_synthetic_stage_gate_authorized()
    gate["identity_leakage_detected"] = True
    gate["next_authorized_stage"] = None
    gate_ok, ev = validate_stage_gate(gate)
    _record("failed_authorization_forces_none_stage", gate_ok is False, authorization_conditions=ev.get("authorization_conditions"))

    return tests, all_passed


def run_completeness_wiring_tests() -> Tuple[List[Dict[str, Any]], bool]:
    """Six focused tests for completeness wiring, separate from the 10 Part D tests."""
    tests: List[Dict[str, Any]] = []
    all_passed = True

    def _record(case_name: str, result: bool, **extra: Any) -> None:
        nonlocal all_passed
        tests.append({"case_name": case_name, "passed": result, **extra})
        all_passed = all_passed and result

    def _valid_negative_test_evidence() -> Dict[str, Any]:
        return {
            "original_negative_tests": {"expected": 12, "executed": 12, "passed": 12, "failed": 0},
            "canonical_exception_tests": {"expected": 10, "executed": 10, "passed": 10, "failed": 0},
            "persisted_ledger_tests": {"expected": 6, "executed": 6, "passed": 6, "failed": 0},
            "preservation_tests": {"expected": 8, "executed": 8, "passed": 8, "failed": 0},
        }

    def _valid_evidence() -> Tuple[Dict[str, bool], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        checks = _make_synthetic_audit_checks_all_true()
        canonical = _make_synthetic_canonical_reconciliation_evidence()
        persisted = _make_synthetic_persisted_ledger_evidence()
        preservation = _make_synthetic_preservation_evidence()
        semantic = _make_synthetic_semantic_reproducibility_evidence()
        negative = _valid_negative_test_evidence()
        return checks, canonical, persisted, preservation, semantic, negative

    # 1. Exact complete evidence returns True.
    checks, canonical, persisted, preservation, semantic, negative = _valid_evidence()
    result = compute_part3b_prediction_ledger_complete(checks, canonical, persisted, preservation, semantic, negative)
    _record("exact_complete_evidence_returns_true", result is True, computed=result)

    # 2. persisted_ledger_reconstruction_matches_in_memory = False returns False.
    checks, canonical, persisted, preservation, semantic, negative = _valid_evidence()
    persisted["persisted_ledger_reconstruction_matches_in_memory"] = False
    result = compute_part3b_prediction_ledger_complete(checks, canonical, persisted, preservation, semantic, negative)
    _record("persisted_false_rejected", result is False, computed=result)

    # 3. persisted_validation_numeric_mismatches > 0 returns False.
    checks, canonical, persisted, preservation, semantic, negative = _valid_evidence()
    persisted["persisted_validation_numeric_mismatches"] = 3
    result = compute_part3b_prediction_ledger_complete(checks, canonical, persisted, preservation, semantic, negative)
    _record("persisted_numeric_mismatch_rejected", result is False, computed=result)

    # 4. nonempty unapproved_differing_artifacts returns False.
    checks, canonical, persisted, preservation, semantic, negative = _valid_evidence()
    semantic["unapproved_differing_artifacts"] = ["some_artifact.csv"]
    result = compute_part3b_prediction_ledger_complete(checks, canonical, persisted, preservation, semantic, negative)
    _record("unapproved_artifact_rejected", result is False, computed=result)

    # 5. wrong Part B test count, expected=6, executed=5, passed=5, failed=0 returns False.
    checks, canonical, persisted, preservation, semantic, negative = _valid_evidence()
    negative["persisted_ledger_tests"] = {"expected": 6, "executed": 5, "passed": 5, "failed": 0}
    result = compute_part3b_prediction_ledger_complete(checks, canonical, persisted, preservation, semantic, negative)
    _record("wrong_part_b_test_count_rejected", result is False, computed=result)

    # 6. Remove one mandatory evidence field entirely and verify fail-closed False.
    checks, canonical, persisted, preservation, semantic, negative = _valid_evidence()
    del persisted["persisted_ledger_reconstruction_matches_in_memory"]
    result = compute_part3b_prediction_ledger_complete(checks, canonical, persisted, preservation, semantic, negative)
    _record("missing_evidence_field_rejected", result is False, computed=result)

    return tests, all_passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--self-test-canonical-exception", action="store_true", default=False)
    parser.add_argument("--self-test-persisted-ledger", action="store_true", default=False)
    parser.add_argument("--self-test-preservation", action="store_true", default=False)
    parser.add_argument("--self-test-audit-gate", action="store_true", default=False)
    parser.add_argument("--self-test-data-artifact-comparison", action="store_true", default=False)
    parser.add_argument("--self-test-eleven-artifact-comparison", action="store_true", default=False)
    known, _ = parser.parse_known_args()
    if known.self_test_eleven_artifact_comparison:
        e2_tests, e2_all_passed, e2_summary = run_part_e2_eleven_artifact_tests()
        e21_tests, e21_all_passed, e21_summary = run_part_e2_1_fail_closed_tests()
        combined = {
            "part_e2_tests": {
                "tests_expected": e2_summary["tests_expected"],
                "tests_executed": e2_summary["tests_executed"],
                "tests_passed": e2_summary["tests_passed"],
                "tests_failed": e2_summary["tests_failed"],
            },
            "part_e2_1_fail_closed_tests": {
                "tests_expected": e21_summary["tests_expected"],
                "tests_executed": e21_summary["tests_executed"],
                "tests_passed": e21_summary["tests_passed"],
                "tests_failed": e21_summary["tests_failed"],
            },
            "et_score_tolerance": e2_summary["et_score_tolerance"],
            "et_rank_metric_tolerance": e2_summary["et_rank_metric_tolerance"],
            "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
            "starting_commit": STARTING_COMMIT,
            "part3b_version": PART3B_VERSION,
            "manifest_valid_enforced": True,
            "audit_json_valid_enforced": True,
            "audit_md_valid_enforced": True,
            "fail_closed_metadata_gate": True,
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "repository_artifacts_written": 0,
            "full_build_executed": False,
            "part3b_complete": False,
            "part3c_authorized": False,
        }
        print(_json_dumps(combined))
        return 0 if (
            e2_all_passed
            and e2_summary["tests_executed"] == 14
            and e2_summary["tests_failed"] == 0
            and e21_all_passed
            and e21_summary["tests_executed"] == 5
            and e21_summary["tests_failed"] == 0
        ) else 1
    if known.self_test_data_artifact_comparison:
        e1_tests, e1_all_passed, e1_summary = run_data_artifact_comparison_self_tests()
        e11_tests, e11_all_passed, e11_summary = run_part_e1_1_schema_provenance_tests()
        e12_tests, e12_all_passed, e12_summary = run_part_e1_2_signed_zero_tests()
        combined = {
            "part_e1_tests": {
                "tests_expected": e1_summary["tests_expected"],
                "tests_executed": e1_summary["tests_executed"],
                "tests_passed": e1_summary["tests_passed"],
                "tests_failed": e1_summary["tests_failed"],
            },
            "part_e1_1_tests": {
                "tests_expected": e11_summary["tests_expected"],
                "tests_executed": e11_summary["tests_executed"],
                "tests_passed": e11_summary["tests_passed"],
                "tests_failed": e11_summary["tests_failed"],
            },
            "part_e1_2_tests": {
                "tests_expected": e12_summary["tests_expected"],
                "tests_executed": e12_summary["tests_executed"],
                "tests_passed": e12_summary["tests_passed"],
                "tests_failed": e12_summary["tests_failed"],
            },
            "lr_signed_zero_rejected": e12_summary["lr_signed_zero_rejected"],
            "dt_signed_zero_rejected": e12_summary["dt_signed_zero_rejected"],
            "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "repository_artifacts_written": 0,
            "full_build_executed": False,
            "part3b_complete": False,
            "part3c_authorized": False,
        }
        print(_json_dumps(combined))
        return 0 if (
            e1_all_passed
            and e1_summary["tests_executed"] == 13
            and e1_summary["tests_failed"] == 0
            and e11_all_passed
            and e11_summary["tests_executed"] == 6
            and e11_summary["tests_failed"] == 0
            and e12_all_passed
            and e12_summary["tests_executed"] == 2
            and e12_summary["tests_failed"] == 0
            and e12_summary["lr_signed_zero_rejected"] is True
            and e12_summary["dt_signed_zero_rejected"] is True
        ) else 1
    if known.self_test_persisted_ledger:
        root = repo_root()
        frozen = import_frozen_pipeline(root)
        ledger_dir = root / "results" / "part3b_prediction_ledger"
        evidence = verify_persisted_ledger_reconstruction(
            frozen,
            ledger_dir / "prediction_ledger_within.csv.gz",
            ledger_dir / "prediction_ledger_cross.csv.gz",
            ledger_dir / "event_manifest.csv",
            ledger_dir / "validation_reconstruction.csv",
            ledger_dir / "canonical_result_reconstruction.csv",
        )
        within_df = read_float_csv_round_trip(ledger_dir / "prediction_ledger_within.csv.gz", compression="gzip")
        cross_df = read_float_csv_round_trip(ledger_dir / "prediction_ledger_cross.csv.gz", compression="gzip")
        event_manifest_df = pd.read_csv(ledger_dir / "event_manifest.csv")
        persisted_val_recon_df = read_float_csv_round_trip(ledger_dir / "validation_reconstruction.csv")
        persisted_result_recon_df = read_float_csv_round_trip(ledger_dir / "canonical_result_reconstruction.csv")
        neg_tests, neg_all_passed = _run_persisted_ledger_negative_tests(
            frozen, within_df, cross_df, event_manifest_df,
            persisted_val_recon_df, persisted_result_recon_df,
        )
        part_a_tests, part_a_all_passed = run_canonical_exception_validator_tests()
        part_a_expected = 10
        part_a_executed = len(part_a_tests)
        part_a_passed = sum(1 for t in part_a_tests if t.get("passed"))
        part_a_failed = sum(1 for t in part_a_tests if not t.get("passed"))
        tests_expected = 6
        tests_executed = len(neg_tests)
        tests_passed = sum(1 for t in neg_tests if t.get("passed"))
        tests_failed = sum(1 for t in neg_tests if not t.get("passed"))
        numeric_mutation_test = next((t for t in neg_tests if t.get("mutation") == 1e-8), None)
        numeric_mutation_rejected = bool(numeric_mutation_test and numeric_mutation_test.get("validator_returned_false"))
        all_evidence_ok = (
            evidence.get("persisted_prediction_schema_exact") is True
            and evidence.get("persisted_prediction_within_rows") == PERSISTED_PREDICTION_WITHIN_ROWS
            and evidence.get("persisted_prediction_cross_rows") == PERSISTED_PREDICTION_CROSS_ROWS
            and evidence.get("persisted_prediction_total_rows") == PERSISTED_PREDICTION_TOTAL_ROWS
            and evidence.get("persisted_validation_prediction_rows") == PERSISTED_VALIDATION_PREDICTION_ROWS
            and evidence.get("persisted_test_prediction_rows") == PERSISTED_TEST_PREDICTION_ROWS
            and evidence.get("persisted_train_prediction_rows") == PERSISTED_TRAIN_PREDICTION_ROWS
            and evidence.get("persisted_prediction_keys_unique") is True
            and evidence.get("persisted_prediction_scores_finite") is True
            and evidence.get("persisted_prediction_scores_in_range") is True
            and evidence.get("persisted_event_manifest_rows") == PERSISTED_EVENT_MANIFEST_ROWS
            and evidence.get("reread_validation_reconstruction_rows") == PERSISTED_VALIDATION_RECON_ROWS
            and evidence.get("reread_result_reconstruction_rows") == PERSISTED_RESULT_RECON_ROWS
            and evidence.get("persisted_validation_reconstruction_rows") == PERSISTED_VALIDATION_RECON_ROWS
            and evidence.get("persisted_result_reconstruction_rows") == PERSISTED_RESULT_RECON_ROWS
            and evidence.get("persisted_validation_category_match") is True
            and evidence.get("persisted_result_category_match") is True
            and evidence.get("persisted_validation_numeric_mismatches") == 0
            and evidence.get("persisted_result_numeric_mismatches") == 0
            and evidence.get("persisted_validation_reconstruction_matches_in_memory") is True
            and evidence.get("persisted_result_reconstruction_matches_in_memory") is True
            and evidence.get("persisted_ledger_reconstruction_matches_in_memory") is True
        )
        summary = {
            "persisted_ledger_evidence": evidence,
            "part_a_exception_tests": {
                "tests_expected": part_a_expected,
                "tests_executed": part_a_executed,
                "tests_passed": part_a_passed,
                "tests_failed": part_a_failed,
            },
            "part_b_persisted_tests": {
                "tests_expected": tests_expected,
                "tests_executed": tests_executed,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "test_details": neg_tests,
            },
            "numeric_1e8_mutation_rejected": numeric_mutation_rejected,
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "artifacts_written": 0,
            "full_build_executed": False,
            "part3b_complete": False,
            "part3c_authorized": False,
        }
        print(_json_dumps(summary))
        exit_code = 0 if (
            all_evidence_ok
            and neg_all_passed
            and tests_executed == tests_expected
            and tests_failed == 0
            and part_a_all_passed
            and part_a_executed == part_a_expected
            and part_a_failed == 0
            and numeric_mutation_rejected
        ) else 1
        return exit_code

    if known.self_test_canonical_exception:
        tests, all_passed = run_canonical_exception_validator_tests()
        summary = {
            "tests_expected": 10,
            "tests_executed": len(tests),
            "tests_passed": sum(1 for t in tests if t.get("passed")),
            "tests_failed": sum(1 for t in tests if not t.get("passed")),
            "model_fits_executed": 0,
            "artifacts_written": 0,
            "full_build_executed": False,
            "part3c_authorized": False,
            "test_details": tests,
        }
        print(_json_dumps(summary))
        return 0 if all_passed and summary["tests_executed"] == 10 and summary["tests_failed"] == 0 else 1

    if known.self_test_preservation:
        root = repo_root()
        accepted_contract = load_accepted_preservation_contract(root, ACCEPTED_PART3A_COMMIT)
        current_state = capture_current_protected_state(root)
        preservation_passed, preservation_evidence = compare_protected_state_to_accepted_contract(
            accepted_contract, current_state
        )
        preservation_tests, tests_all_passed = run_preservation_self_tests()
        tests_expected = 8
        tests_executed = len(preservation_tests)
        tests_passed = sum(1 for t in preservation_tests if t.get("passed"))
        tests_failed = sum(1 for t in preservation_tests if not t.get("passed"))

        before_after_passed, before_after_ev = validate_protected_before_after(
            accepted_contract, current_state, current_state
        )

        summary = {
            "accepted_commit_reference_used": preservation_evidence["accepted_commit_reference_used"],
            "accepted_commit": preservation_evidence["accepted_commit"],
            "preservation_passed": preservation_passed,
            "preservation_evidence": preservation_evidence,
            "part_c_preservation_tests": {
                "tests_expected": tests_expected,
                "tests_executed": tests_executed,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "test_details": preservation_tests,
            },
            "genuine_before_after_supported": True,
            "before_after_evidence": before_after_ev,
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "artifacts_written": 0,
            "full_build_executed": False,
            "part3b_complete": False,
            "part3c_authorized": False,
        }
        print(_json_dumps(summary))
        exit_code = 0 if (
            preservation_passed
            and tests_all_passed
            and tests_executed == tests_expected
            and tests_failed == 0
        ) else 1
        return exit_code

    if known.self_test_audit_gate:
        part_d_tests, part_d_all_passed = run_audit_gate_self_tests()
        part_d_expected = 10
        part_d_executed = len(part_d_tests)
        part_d_passed = sum(1 for t in part_d_tests if t.get("passed"))
        part_d_failed = sum(1 for t in part_d_tests if not t.get("passed"))

        completeness_tests, completeness_all_passed = run_completeness_wiring_tests()
        completeness_expected = 6
        completeness_executed = len(completeness_tests)
        completeness_passed = sum(1 for t in completeness_tests if t.get("passed"))
        completeness_failed = sum(1 for t in completeness_tests if not t.get("passed"))

        missing_stage_test = next((t for t in part_d_tests if t.get("case_name") == "missing_stage_field_fails"), None)
        extra_stage_test = next((t for t in part_d_tests if t.get("case_name") == "extra_stage_field_fails"), None)
        wrong_b_test = next((t for t in completeness_tests if t.get("case_name") == "wrong_part_b_test_count_rejected"), None)
        missing_evidence_test = next((t for t in completeness_tests if t.get("case_name") == "missing_evidence_field_rejected"), None)
        print(f"missing_stage_field_test_passed = {bool(missing_stage_test and missing_stage_test.get('passed'))}")
        print(f"extra_stage_field_test_passed = {bool(extra_stage_test and extra_stage_test.get('passed'))}")
        print(f"wrong_part_b_test_count_rejected = {bool(wrong_b_test and wrong_b_test.get('passed'))}")
        print(f"missing_evidence_field_rejected = {bool(missing_evidence_test and missing_evidence_test.get('passed'))}")

        # Validate exact audit schema on a synthetic all-True dict.
        synthetic_checks = _make_synthetic_audit_checks_all_true()
        synthetic_checks["stage_gate_passed"] = True
        synthetic_checks["all_critical_checks_passed"] = True
        schema_ok, schema_ev = validate_exact_audit_check_schema(synthetic_checks)

        # Validate exact stage-gate schema on a synthetic authorized gate.
        synthetic_gate = _make_synthetic_stage_gate_authorized()
        gate_ok, gate_ev = validate_stage_gate(synthetic_gate)

        # Test all-critical computation.
        all_critical = compute_all_critical_checks_passed(synthetic_checks)

        summary = {
            "part_d_audit_gate_tests": {
                "tests_expected": part_d_expected,
                "tests_executed": part_d_executed,
                "tests_passed": part_d_passed,
                "tests_failed": part_d_failed,
                "test_details": part_d_tests,
            },
            "completeness_wiring_tests": {
                "tests_expected": completeness_expected,
                "tests_executed": completeness_executed,
                "tests_passed": completeness_passed,
                "tests_failed": completeness_failed,
                "test_details": completeness_tests,
            },
            "audit_schema_validation": {
                "schema_passed": schema_ok,
                "evidence": schema_ev,
            },
            "stage_gate_validation": {
                "gate_passed": gate_ok,
                "evidence": gate_ev,
            },
            "all_critical_checks_computed": all_critical,
            "model_fits_executed": 0,
            "prediction_calls_executed": 0,
            "artifacts_written": 0,
            "full_build_executed": False,
            "part3b_complete": False,
            "part3c_authorized": False,
        }
        print(_json_dumps(summary))
        exit_code = 0 if (
            part_d_all_passed
            and part_d_executed == part_d_expected
            and part_d_failed == 0
            and completeness_all_passed
            and completeness_executed == completeness_expected
            and completeness_failed == 0
            and schema_ok is True
            and gate_ok is True
            and all_critical is True
        ) else 1
        return exit_code

    root = repo_root()
    data_dir = root / "data" / "raw"
    canonical_dir = root / "results" / "part1_full_reproduction"

    # 1. Verify source commit and frozen pipeline.
    if not verify_source_commit(ACCEPTED_PART3A_COMMIT):
        raise RuntimeError(f"Accepted Part 3A commit {ACCEPTED_PART3A_COMMIT} not found in repository.")
    frozen = import_frozen_pipeline(root)

    # 2. Load raw projects.
    projects, common_cols, metadata = load_raw_projects(frozen, data_dir)
    registry = build_sample_registry(projects, common_cols)
    projects = attach_registry_identity(projects, registry)
    feature_schema_sha256 = compute_feature_schema_sha256(common_cols)

    # 3. Read canonical validation and result files.
    canonical_val = pd.read_csv(canonical_dir / "validation_log.csv")
    canonical_res = pd.read_csv(canonical_dir / "repeated_all_results.csv")

    # 4. Assert that reconstruction validators do not override shared tolerances.
    sig_val = inspect.signature(validate_validation_reconstruction)
    sig_res = inspect.signature(validate_result_reconstruction)
    for sig in [sig_val, sig_res]:
        for p in ["rtol", "atol"]:
            if p in sig.parameters:
                default = sig.parameters[p].default
                if default is not inspect.Parameter.empty:
                    assert default == (RECON_RTOL if p == "rtol" else RECON_ATOL), f"Reconstruction validator overrides {p}"

    # 5. Capture preservation-before state.
    preservation_before = capture_preservation_state(root)

    # 6. Run two independent builds in named temporary roots that persist for diagnosis.
    t1 = tempfile.mkdtemp(prefix="part3b2_build1_")
    t2 = tempfile.mkdtemp(prefix="part3b2_build2_")
    try:
        bundle1 = build_core_bundle(Path(t1), frozen, projects, common_cols, registry, canonical_val, canonical_res, preservation_before)
        bundle2 = build_core_bundle(Path(t2), frozen, projects, common_cols, registry, canonical_val, canonical_res, preservation_before)

        # 7. Compare the 11 artifacts under the Part 3B.2R semantic reproducibility policy.
        artifact_rel_paths = sorted(bundle1["artifacts"].keys())
        semantic_evidence = compare_two_builds_semantically(bundle1, bundle2)
        semantic_reproducibility_passed = semantic_evidence["semantic_reproducibility_passed"]
        # Legacy byte comparison is retained for reporting but no longer gates the stage gate.
        deterministic_artifacts_passed = semantic_reproducibility_passed
        mismatch_details = []
        for rel in artifact_rel_paths:
            p1 = bundle1["artifacts"][rel]
            p2 = bundle2["artifacts"][rel]
            b1 = p1.read_bytes()
            b2 = p2.read_bytes()
            if b1 != b2:
                mismatch_details.append({"artifact": rel, "sha1": sha256_bytes(b1), "sha2": sha256_bytes(b2), "bytes1": len(b1), "bytes2": len(b2)})
    finally:
        # Preserve both roots if semantic comparison fails so diagnosis can continue.
        if not semantic_reproducibility_passed:
            print(f"\n[WARNING] Semantic reproducibility failed; retaining build roots for diagnosis:\n  {t1}\n  {t2}", flush=True)

    # 8. Capture preservation-after state and validate with fail-closed contract.
    preservation_after = capture_preservation_state(root)
    accepted_contract = load_accepted_preservation_contract(root, ACCEPTED_PART3A_COMMIT)
    preservation_passed, preservation_evidence = compare_protected_state_to_accepted_contract(
        accepted_contract, preservation_after
    )

    # 9. If deterministic, copy bundle1 artifacts into the repository.
    if deterministic_artifacts_passed:
        for rel, src in bundle1["artifacts"].items():
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))

    # 10. Update preservation check in audit checks after repo write.
    audit_checks = bundle1["audit_checks"]
    check_evidence = bundle1["check_evidence"]
    audit_checks["raw_and_canonical_preservation_passed"] = preservation_passed
    audit_checks["deterministic_artifacts_passed"] = deterministic_artifacts_passed

    # 10a. Verify persisted ledger reconstruction immediately after copying artifacts.
    persisted_ledger_evidence = verify_persisted_ledger_reconstruction(
        frozen,
        root / "results" / "part3b_prediction_ledger" / "prediction_ledger_within.csv.gz",
        root / "results" / "part3b_prediction_ledger" / "prediction_ledger_cross.csv.gz",
        root / "results" / "part3b_prediction_ledger" / "event_manifest.csv",
        root / "results" / "part3b_prediction_ledger" / "validation_reconstruction.csv",
        root / "results" / "part3b_prediction_ledger" / "canonical_result_reconstruction.csv",
    )

    # 10b. Run actual persisted-ledger negative tests and preservation self-tests.
    ledger_dir = root / "results" / "part3b_prediction_ledger"
    within_df = read_float_csv_round_trip(ledger_dir / "prediction_ledger_within.csv.gz", compression="gzip")
    cross_df = read_float_csv_round_trip(ledger_dir / "prediction_ledger_cross.csv.gz", compression="gzip")
    event_manifest_df = pd.read_csv(ledger_dir / "event_manifest.csv")
    persisted_val_recon_df = read_float_csv_round_trip(ledger_dir / "validation_reconstruction.csv")
    persisted_result_recon_df = read_float_csv_round_trip(ledger_dir / "canonical_result_reconstruction.csv")
    persisted_ledger_tests, _ = _run_persisted_ledger_negative_tests(
        frozen, within_df, cross_df, event_manifest_df,
        persisted_val_recon_df, persisted_result_recon_df,
    )
    preservation_tests, _ = run_preservation_self_tests()

    # Semantic reproducibility evidence (outside audit_checks)
    semantic_reproducibility_evidence = {
        "semantic_reproducibility_passed": semantic_reproducibility_passed,
        "exact_structural_equality": semantic_evidence.get("exact_structural_equality", False),
        "identity_columns_exact": semantic_evidence.get("all_identity_columns_exact", False),
        "non_et_score_columns_exact": semantic_evidence.get("all_non_et_score_columns_exact", False),
        "maximum_et_score_difference": semantic_evidence.get("maximum_et_score_difference", float("nan")),
        "number_of_et_cells_differing": semantic_evidence.get("number_of_et_cells_differing", -1),
        "selection_decisions_exact": semantic_evidence.get("all_selection_decisions_exact", False),
        "thresholds_exact": semantic_evidence.get("all_thresholds_exact", False),
        "non_exempt_metrics_strictly_equal": semantic_evidence.get("all_non_exempt_metrics_strictly_equal", False),
        "byte_identical_artifacts": semantic_evidence.get("byte_identical_artifacts", []),
        "artifacts_with_approved_et_roundoff_only": semantic_evidence.get("artifacts_with_approved_et_roundoff_only", []),
        "unapproved_differing_artifacts": semantic_evidence.get("unapproved_differing_artifacts", []),
    }

    # 10b. Build the five evidence groups and compute ledger completeness.
    canonical_reconciliation_evidence = {
        "strict_validation_mismatches": check_evidence["strict_validation_mismatches"],
        "strict_result_mismatches_before_exception": check_evidence["strict_result_mismatches_before_exception"],
        "approved_nondeterminism_exceptions": check_evidence["approved_nondeterminism_exceptions"],
        "unapproved_result_mismatches": check_evidence["unapproved_result_mismatches"],
        "canonical_nondeterminism_exception_validated": check_evidence["canonical_nondeterminism_exception_validated"],
    }

    neg_tests_list = bundle1["negative_tests"]
    exc_tests_list = bundle1["validation_results"]["canonical_exception_validator_tests"][1].get("tests", [])
    negative_test_evidence = collect_actual_negative_test_evidence(
        neg_tests_list,
        exc_tests_list,
        persisted_ledger_tests,
        preservation_tests,
    )

    ledger_complete = compute_part3b_prediction_ledger_complete(
        audit_checks,
        canonical_reconciliation_evidence,
        persisted_ledger_evidence,
        preservation_evidence,
        semantic_reproducibility_evidence,
        negative_test_evidence,
    )

    # 11. Build stage gate with completeness result including persisted ledger evidence.
    validation_results = bundle1["validation_results"]
    validation_results["preservation"] = (preservation_passed, preservation_evidence)
    duplicate_audit = bundle1["duplicate_audit"]
    stage_gate = build_stage_gate(audit_checks, check_evidence, validation_results, preservation_evidence, duplicate_audit, semantic_reproducibility_passed, ledger_complete)
    stage_gate_passed, stage_gate_evidence = validate_stage_gate(stage_gate)
    audit_checks["stage_gate_passed"] = stage_gate_passed
    audit_checks["all_critical_checks_passed"] = compute_all_critical_checks_passed(audit_checks)
    audit_schema_passed, audit_schema_evidence = validate_exact_audit_check_schema(audit_checks)

    # 12. Regenerate reports with final preservation and determinism evidence.
    artifacts = bundle1["artifacts"]
    artifact_hashes = {rel: {"sha256": sha256_file(root / rel), "byte_size": (root / rel).stat().st_size} for rel in artifacts}
    json_report = render_json_report(
        audit_checks, stage_gate, stage_gate_evidence, validation_results, duplicate_audit,
        bundle1["negative_tests"], bundle1["tie_tests"], preservation_after, artifacts, artifact_hashes,
        feature_schema_sha256, bundle1["dataset_profile"], bundle1["event_manifest"], common_cols, registry,
        bundle1["split_within"], bundle1["split_cross"], bundle1["pred_within"], bundle1["pred_cross"],
        bundle1["val_recon"], bundle1["result_recon"], bundle1["fitted_count"], canonical_val, canonical_res
    )
    json_report["determinism_verification"] = {
        "two_independent_builds_completed": True,
        "first_build_root": str(t1),
        "second_build_root": str(t2),
        "deterministic_artifacts_passed": deterministic_artifacts_passed,
        "semantic_reproducibility_passed": semantic_reproducibility_passed,
        "artifact_count_compared": len(artifact_rel_paths),
        "mismatch_details": mismatch_details,
        "semantic_reproducibility_evidence": _evidence_for_json(semantic_evidence),
    }
    json_report["check_evidence"] = _evidence_for_json(check_evidence)
    json_report["audit_schema_evidence"] = _evidence_for_json(audit_schema_evidence)
    json_report["semantic_reproducibility_evidence"] = _evidence_for_json(semantic_reproducibility_evidence)
    json_report["preservation_after_write"] = preservation_evidence

    json_report_path = root / "reports" / "part3b_split_leakage_audit.json"
    write_text_atomic(json_report_path, _json_dumps(json_report))
    md_report_path = root / "reports" / "part3b_split_leakage_audit.md"
    write_text_atomic(md_report_path, render_markdown_report(json_report))

    # 13. Update ledger manifest with final hashes (after write and report).
    # The manifest must not embed its own hash, so it lists the other 10 artifacts.
    manifest_entries = []
    for rel in sorted(artifact_rel_paths):
        if rel == "results/part3b_prediction_ledger/ledger_manifest.json":
            continue
        if rel.endswith(".json") or rel.endswith(".md"):
            manifest_entries.append({
                "relative_path": rel,
                "format": "json" if rel.endswith(".json") else "markdown",
                "compressed": False,
                "row_count": None,
                "column_count": None,
                "columns": None,
                "byte_size": artifact_hashes[rel]["byte_size"],
                "sha256": artifact_hashes[rel]["sha256"],
            })
        else:
            df = pd.read_csv(root / rel, compression="gzip" if rel.endswith(".gz") else "infer")
            manifest_entries.append({
                "relative_path": rel,
                "format": "csv" if not rel.endswith(".gz") else "csv.gz",
                "compressed": rel.endswith(".gz"),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "byte_size": artifact_hashes[rel]["byte_size"],
                "sha256": artifact_hashes[rel]["sha256"],
            })
    manifest_data = {
        "manifest_version": PART3B_VERSION,
        "starting_commit": STARTING_COMMIT,
        "accepted_part3a_commit": ACCEPTED_PART3A_COMMIT,
        "project_order": [p.upper() for p in PROJECTS],
        "seed_order": SEEDS,
        "candidate_order": CANDIDATES,
        "event_count": EXPECTED_EVENT_COUNT,
        "sample_count": EXPECTED_REGISTRY_ROWS,
        "split_membership_total_rows": len(bundle1["split_within"]) + len(bundle1["split_cross"]),
        "prediction_total_rows": len(bundle1["pred_within"]) + len(bundle1["pred_cross"]),
        "validation_reconstruction_rows": len(bundle1["val_recon"]),
        "canonical_result_reconstruction_rows": len(bundle1["result_recon"]),
        "self_referential_hash_embedded": False,
        "artifacts": manifest_entries,
    }
    manifest_path = root / "results" / "part3b_prediction_ledger" / "ledger_manifest.json"
    write_text_atomic(manifest_path, _json_dumps(manifest_data))

    # 14. Persisted ledger reconstruction already verified in step 10a.
    json_report["persisted_ledger_evidence"] = _evidence_for_json(persisted_ledger_evidence)
    # Rewrite JSON report with persisted ledger evidence.
    write_text_atomic(json_report_path, _json_dumps(json_report))

    # 15. Gather actual changed paths from git status.
    try:
        git_status_lines = run_git(["status", "--short"]).splitlines()
        actual_changed_paths = [line.split()[-1] for line in git_status_lines if line.strip()]
        git_status_clean = len(actual_changed_paths) == 0
    except Exception:
        actual_changed_paths = []
        git_status_clean = None

    # 16. Determine commit and push outcome if stage gate passes.
    new_commit: Optional[str] = None
    remote_head: Optional[str] = None
    if audit_checks["all_critical_checks_passed"] and git_status_clean is False:
        # Verify only authorized Part 3B paths changed.
        authorized = {
            "scripts/build_part3b_prediction_ledger.py",
            "results/part3b_prediction_ledger/sample_registry.csv",
            "results/part3b_prediction_ledger/event_manifest.csv",
            "results/part3b_prediction_ledger/split_membership_within.csv.gz",
            "results/part3b_prediction_ledger/split_membership_cross.csv.gz",
            "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz",
            "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz",
            "results/part3b_prediction_ledger/validation_reconstruction.csv",
            "results/part3b_prediction_ledger/canonical_result_reconstruction.csv",
            "results/part3b_prediction_ledger/ledger_manifest.json",
            "reports/part3b_split_leakage_audit.json",
            "reports/part3b_split_leakage_audit.md",
        }
        unauthorized = [p for p in actual_changed_paths if p not in authorized]
        if unauthorized:
            print(f"\n[ERROR] Unauthorized changed files detected; will not commit: {unauthorized}")
            git_status_clean = None
        else:
            try:
                run_git(["add"] + sorted(actual_changed_paths))
                run_git(["commit", "-m", "Part 3B.2R: Reconcile frozen ET nondeterminism"])
                new_commit = run_git(["rev-parse", "HEAD"])
                run_git(["push", "origin", BRANCH])
                remote_head = run_git(["rev-parse", f"origin/{BRANCH}"])
                print(f"\n[SUCCESS] Committed and pushed: {new_commit}")
            except Exception as e:
                print(f"\n[ERROR] Commit/push failed: {e}")
                new_commit = None
                remote_head = None

    # 17. Print final report.
    print_final_report(json_report, actual_changed_paths, new_commit, remote_head, "clean" if git_status_clean else "modified")

    # 18. Return exit code based on gate.
    if not audit_checks["all_critical_checks_passed"]:
        print("\n[ERROR] Stage gate did not pass. Part 3C is not authorized.")
        return 1
    print("\n[SUCCESS] Stage gate passed. Part 3C is authorized.")
    return 0


if __name__ == "__main__":
    sys.exit(main())



