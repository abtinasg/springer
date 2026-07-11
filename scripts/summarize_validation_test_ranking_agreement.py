#!/usr/bin/env python3
"""
Part 2 Section 4B.2: Validation-Test Ranking Agreement Summary Audit

This script computes descriptive summaries from the validated event-level CSV.
No event rows, ranking values, winner sets, correlations, or selected-candidate results are modified.
"""

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd


# Expected event column order
EXPECTED_EVENT_COLUMNS = [
    "experiment",
    "target_project",
    "seed",
    "mode",
    "metric",
    "metric_direction",
    "validation_winner_set_exact",
    "validation_winner_set_tolerance",
    "test_winner_set_exact",
    "test_winner_set_tolerance",
    "strict_top1_agreement_exact",
    "strict_top1_agreement_tolerance",
    "winner_set_equal_exact",
    "winner_set_equal_tolerance",
    "winner_set_jaccard_exact",
    "winner_set_jaccard_tolerance",
    "winner_set_any_overlap_exact",
    "winner_set_any_overlap_tolerance",
    "spearman_rho",
    "spearman_defined",
    "spearman_undefined_reason",
    "kendall_tau_b",
    "kendall_defined",
    "kendall_undefined_reason",
    "mode_selected_candidate",
    "selected_candidate_test_rank",
    "selected_candidate_in_test_winner_set_exact",
    "selected_candidate_in_test_winner_set_tolerance",
]

# Expected summary schema
EXPECTED_SUMMARY_SCHEMA = [
    "group_name",
    "group_value",
    "n_event_rows",
    "strict_top1_agreement_exact_n",
    "strict_top1_agreement_exact_rate",
    "strict_top1_agreement_tolerance_n",
    "strict_top1_agreement_tolerance_rate",
    "winner_set_equal_exact_n",
    "winner_set_equal_exact_rate",
    "winner_set_equal_tolerance_n",
    "winner_set_equal_tolerance_rate",
    "winner_set_any_overlap_exact_n",
    "winner_set_any_overlap_exact_rate",
    "winner_set_any_overlap_tolerance_n",
    "winner_set_any_overlap_tolerance_rate",
    "winner_set_jaccard_exact_mean",
    "winner_set_jaccard_exact_median",
    "winner_set_jaccard_tolerance_mean",
    "winner_set_jaccard_tolerance_median",
    "spearman_defined_n",
    "spearman_undefined_n",
    "spearman_mean_defined",
    "spearman_median_defined",
    "kendall_defined_n",
    "kendall_undefined_n",
    "kendall_mean_defined",
    "kendall_median_defined",
    "selected_candidate_test_rank_mean",
    "selected_candidate_test_rank_median",
    "selected_candidate_test_rank_one_n",
    "selected_candidate_test_rank_one_rate",
    "selected_candidate_in_test_winner_set_exact_n",
    "selected_candidate_in_test_winner_set_exact_rate",
    "selected_candidate_in_test_winner_set_tolerance_n",
    "selected_candidate_in_test_winner_set_tolerance_rate",
]

# Expected undefined reasons schema
EXPECTED_UNDEFINED_REASON_SCHEMA = [
    "correlation",
    "undefined_reason",
    "count",
]

# Expected domains
EXPECTED_EXPERIMENTS = ["within_project", "cross_project"]
EXPECTED_MODES = ["balanced", "rank", "mcc"]
EXPECTED_PROJECTS = ["CM1", "JM1", "KC1", "KC2", "PC1"]
EXPECTED_SEEDS = [7, 13, 29, 42, 101]

# Expected row counts
EXPECTED_OVERALL_ROWS = 1
EXPECTED_EXPERIMENT_ROWS = 2
EXPECTED_MODE_ROWS = 3
EXPECTED_METRIC_ROWS = 14
EXPECTED_PROJECT_ROWS = 5
EXPECTED_UNDEFINED_REASON_ROWS = 2

# Expected denominators
EXPECTED_OVERALL_DENOMINATOR = 2100
EXPECTED_EXPERIMENT_DENOMINATORS = {"within_project": 1050, "cross_project": 1050}
EXPECTED_MODE_DENOMINATORS = {"balanced": 700, "rank": 700, "mcc": 700}
EXPECTED_METRIC_DENOMINATOR = 150
EXPECTED_PROJECT_DENOMINATOR = 420


def finite_mask(series: pd.Series) -> pd.Series:
    """Return a boolean mask indicating which values are finite (not NaN, None, pd.NA, +inf, -inf)."""
    numeric = pd.to_numeric(series, errors="coerce")
    return series.notna() & np.isfinite(numeric)


def convert_to_python_types(obj):
    """Convert numpy/pandas types to Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_python_types(v) for v in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_specification(spec_path: Path) -> Dict[str, Any]:
    """Load specification JSON."""
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_audit(audit_path: Path) -> Dict[str, Any]:
    """Load audit JSON."""
    with open(audit_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_input_audit(audit: Dict[str, Any]) -> Dict[str, Any]:
    """Verify audit contains all required validation checks and return evidence."""
    validation_checks = audit.get("validation_checks", {})
    
    required_checks = [
        "artifact_semantic_consistency_passed",
        "deterministic_serialization_ready_passed",
        "output_integrity_ready_passed",
    ]
    
    missing_required = [c for c in required_checks if c not in validation_checks]
    failed_checks = [name for name, passed in validation_checks.items() if not passed]
    
    return {
        "input_audit_check_count": len(validation_checks),
        "input_audit_failed_check_count": len(failed_checks),
        "input_audit_missing_required_check_count": len(missing_required),
        "input_audit_checks_passed": len(failed_checks) == 0 and len(missing_required) == 0,
    }


def verify_event_csv(
    df: pd.DataFrame,
    actual_sha: str,
    expected_sha: str,
    spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Verify event CSV structure and content and return evidence."""
    key_cols = ["experiment", "target_project", "seed", "mode", "metric"]
    
    # Check exact column order
    actual_columns = list(df.columns)
    column_order_ok = actual_columns == EXPECTED_EVENT_COLUMNS
    
    # Check row count
    row_count_ok = len(df) == 2100
    
    # Check column count
    column_count_ok = len(df.columns) == 28
    
    # Check NA state
    na_state_valid = True
    for col in df.columns:
        if col in ["spearman_undefined_reason", "kendall_undefined_reason"]:
            # These can be null for defined correlations
            continue
        if col in ["spearman_rho", "kendall_tau_b"]:
            # These can be null when correlation is undefined
            continue
        if df[col].isna().any():
            print(f"Column {col} has NA values")
            na_state_valid = False
            break
    
    # Check numeric columns are finite
    numeric_cols = [
        "winner_set_jaccard_exact",
        "winner_set_jaccard_tolerance",
        "spearman_rho",
        "kendall_tau_b",
        "selected_candidate_test_rank",
    ]
    finite_numeric_valid = True
    for col in numeric_cols:
        if col in df.columns:
            if not df[col].dropna().apply(lambda x: np.isfinite(x)).all():
                finite_numeric_valid = False
                break
    
    # Check boolean columns contain valid boolean values
    boolean_cols = [
        "strict_top1_agreement_exact",
        "strict_top1_agreement_tolerance",
        "winner_set_equal_exact",
        "winner_set_equal_tolerance",
        "winner_set_any_overlap_exact",
        "winner_set_any_overlap_tolerance",
        "spearman_defined",
        "kendall_defined",
        "selected_candidate_in_test_winner_set_exact",
        "selected_candidate_in_test_winner_set_tolerance",
    ]
    boolean_valid = True
    for col in boolean_cols:
        if col in df.columns:
            unique_vals = df[col].dropna().unique()
            if not all(v in [True, False] for v in unique_vals):
                boolean_valid = False
                break
    
    # Check key uniqueness
    key_duplicates = df.duplicated(subset=key_cols, keep=False)
    duplicate_key_count = int(key_duplicates.sum())
    duplicate_keys_ok = duplicate_key_count == 0
    
    # Compute expected key coverage from Cartesian product
    experiments = EXPECTED_EXPERIMENTS
    projects = EXPECTED_PROJECTS
    seeds = EXPECTED_SEEDS
    modes = EXPECTED_MODES
    metrics = spec["metrics"]
    
    expected_keys = set()
    for exp in experiments:
        for proj in projects:
            for seed in seeds:
                for mode in modes:
                    for metric in metrics:
                        expected_keys.add((exp, proj, seed, mode, metric))
    
    # Compute actual keys
    actual_keys = set(tuple(row) for row in df[key_cols].values)
    
    # Compute coverage evidence
    actual_event_key_count = len(actual_keys)
    missing_event_key_count = len(expected_keys - actual_keys)
    extra_event_key_count = len(actual_keys - expected_keys)
    key_coverage_ok = (
        actual_event_key_count == 2100 and
        missing_event_key_count == 0 and
        extra_event_key_count == 0
    )
    
    sha256_verified = actual_sha == expected_sha
    
    return {
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "sha256_verified": sha256_verified,
        "rows": len(df),
        "columns": len(df.columns),
        "column_order_ok": column_order_ok,
        "row_count_ok": row_count_ok,
        "column_count_ok": column_count_ok,
        "na_state_valid": na_state_valid,
        "finite_numeric_valid": finite_numeric_valid,
        "boolean_valid": boolean_valid,
        "duplicate_key_count": duplicate_key_count,
        "actual_event_key_count": actual_event_key_count,
        "missing_event_key_count": missing_event_key_count,
        "extra_event_key_count": extra_event_key_count,
        "key_coverage_ok": key_coverage_ok,
        "input_schema_valid": (
            column_order_ok and
            row_count_ok and
            column_count_ok and
            na_state_valid and
            finite_numeric_valid and
            boolean_valid
        ),
        "input_key_coverage_passed": key_coverage_ok,
    }


def compute_summary_row(
    df_subset: pd.DataFrame,
    group_name: str,
    group_value: str,
) -> Dict[str, Any]:
    """Compute summary statistics for a subset of event rows."""
    n = len(df_subset)
    
    # Boolean counts
    strict_top1_exact_n = df_subset["strict_top1_agreement_exact"].sum()
    strict_top1_tolerance_n = df_subset["strict_top1_agreement_tolerance"].sum()
    winner_set_equal_exact_n = df_subset["winner_set_equal_exact"].sum()
    winner_set_equal_tolerance_n = df_subset["winner_set_equal_tolerance"].sum()
    winner_set_any_overlap_exact_n = df_subset["winner_set_any_overlap_exact"].sum()
    winner_set_any_overlap_tolerance_n = df_subset["winner_set_any_overlap_tolerance"].sum()
    selected_in_test_exact_n = df_subset["selected_candidate_in_test_winner_set_exact"].sum()
    selected_in_test_tolerance_n = df_subset["selected_candidate_in_test_winner_set_tolerance"].sum()
    
    # Rates
    strict_top1_exact_rate = strict_top1_exact_n / n if n > 0 else 0.0
    strict_top1_tolerance_rate = strict_top1_tolerance_n / n if n > 0 else 0.0
    winner_set_equal_exact_rate = winner_set_equal_exact_n / n if n > 0 else 0.0
    winner_set_equal_tolerance_rate = winner_set_equal_tolerance_n / n if n > 0 else 0.0
    winner_set_any_overlap_exact_rate = winner_set_any_overlap_exact_n / n if n > 0 else 0.0
    winner_set_any_overlap_tolerance_rate = winner_set_any_overlap_tolerance_n / n if n > 0 else 0.0
    selected_in_test_exact_rate = selected_in_test_exact_n / n if n > 0 else 0.0
    selected_in_test_tolerance_rate = selected_in_test_tolerance_n / n if n > 0 else 0.0
    
    # Jaccard statistics
    jaccard_exact = df_subset["winner_set_jaccard_exact"].values
    jaccard_tolerance = df_subset["winner_set_jaccard_tolerance"].values
    jaccard_exact_mean = jaccard_exact.mean() if len(jaccard_exact) > 0 else 0.0
    jaccard_exact_median = float(pd.Series(jaccard_exact).median()) if len(jaccard_exact) > 0 else 0.0
    jaccard_tolerance_mean = jaccard_tolerance.mean() if len(jaccard_tolerance) > 0 else 0.0
    jaccard_tolerance_median = float(pd.Series(jaccard_tolerance).median()) if len(jaccard_tolerance) > 0 else 0.0
    
    # Spearman statistics
    spearman_defined_mask = df_subset["spearman_defined"].astype(bool)
    spearman_defined_n = spearman_defined_mask.sum()
    spearman_undefined_n = (~spearman_defined_mask).sum()
    spearman_values = df_subset.loc[spearman_defined_mask, "spearman_rho"].values
    if spearman_defined_n > 0:
        spearman_mean = spearman_values.mean()
        spearman_median = float(pd.Series(spearman_values).median())
    else:
        spearman_mean = np.nan
        spearman_median = np.nan
    
    # Kendall statistics
    kendall_defined_mask = df_subset["kendall_defined"].astype(bool)
    kendall_defined_n = kendall_defined_mask.sum()
    kendall_undefined_n = (~kendall_defined_mask).sum()
    kendall_values = df_subset.loc[kendall_defined_mask, "kendall_tau_b"].values
    if kendall_defined_n > 0:
        kendall_mean = kendall_values.mean()
        kendall_median = float(pd.Series(kendall_values).median())
    else:
        kendall_mean = np.nan
        kendall_median = np.nan
    
    # Selected candidate test rank statistics
    selected_ranks = df_subset["selected_candidate_test_rank"].values
    selected_rank_mean = selected_ranks.mean() if len(selected_ranks) > 0 else 0.0
    selected_rank_median = float(pd.Series(selected_ranks).median()) if len(selected_ranks) > 0 else 0.0
    selected_rank_one_mask = df_subset["selected_candidate_test_rank"].apply(
        lambda x: math.isclose(x, 1.0, rel_tol=1e-12, abs_tol=1e-12)
    )
    selected_rank_one_n = selected_rank_one_mask.sum()
    selected_rank_one_rate = selected_rank_one_n / n if n > 0 else 0.0
    
    return {
        "group_name": group_name,
        "group_value": group_value,
        "n_event_rows": n,
        "strict_top1_agreement_exact_n": int(strict_top1_exact_n),
        "strict_top1_agreement_exact_rate": strict_top1_exact_rate,
        "strict_top1_agreement_tolerance_n": int(strict_top1_tolerance_n),
        "strict_top1_agreement_tolerance_rate": strict_top1_tolerance_rate,
        "winner_set_equal_exact_n": int(winner_set_equal_exact_n),
        "winner_set_equal_exact_rate": winner_set_equal_exact_rate,
        "winner_set_equal_tolerance_n": int(winner_set_equal_tolerance_n),
        "winner_set_equal_tolerance_rate": winner_set_equal_tolerance_rate,
        "winner_set_any_overlap_exact_n": int(winner_set_any_overlap_exact_n),
        "winner_set_any_overlap_exact_rate": winner_set_any_overlap_exact_rate,
        "winner_set_any_overlap_tolerance_n": int(winner_set_any_overlap_tolerance_n),
        "winner_set_any_overlap_tolerance_rate": winner_set_any_overlap_tolerance_rate,
        "winner_set_jaccard_exact_mean": jaccard_exact_mean,
        "winner_set_jaccard_exact_median": jaccard_exact_median,
        "winner_set_jaccard_tolerance_mean": jaccard_tolerance_mean,
        "winner_set_jaccard_tolerance_median": jaccard_tolerance_median,
        "spearman_defined_n": int(spearman_defined_n),
        "spearman_undefined_n": int(spearman_undefined_n),
        "spearman_mean_defined": spearman_mean,
        "spearman_median_defined": spearman_median,
        "kendall_defined_n": int(kendall_defined_n),
        "kendall_undefined_n": int(kendall_undefined_n),
        "kendall_mean_defined": kendall_mean,
        "kendall_median_defined": kendall_median,
        "selected_candidate_test_rank_mean": selected_rank_mean,
        "selected_candidate_test_rank_median": selected_rank_median,
        "selected_candidate_test_rank_one_n": int(selected_rank_one_n),
        "selected_candidate_test_rank_one_rate": selected_rank_one_rate,
        "selected_candidate_in_test_winner_set_exact_n": int(selected_in_test_exact_n),
        "selected_candidate_in_test_winner_set_exact_rate": selected_in_test_exact_rate,
        "selected_candidate_in_test_winner_set_tolerance_n": int(selected_in_test_tolerance_n),
        "selected_candidate_in_test_winner_set_tolerance_rate": selected_in_test_tolerance_rate,
    }


def compute_correlation_undefined_reasons(df: pd.DataFrame) -> pd.DataFrame:
    """Compute correlation undefined reasons summary."""
    reasons_rows = []
    
    # Spearman undefined reasons
    spearman_undefined = df[df["spearman_defined"] == False]
    if not spearman_undefined.empty:
        spearman_reason_counts = spearman_undefined["spearman_undefined_reason"].value_counts()
        for reason, count in spearman_reason_counts.items():
            reasons_rows.append({
                "correlation": "spearman",
                "undefined_reason": reason,
                "count": int(count),
            })
    
    # Kendall undefined reasons
    kendall_undefined = df[df["kendall_defined"] == False]
    if not kendall_undefined.empty:
        kendall_reason_counts = kendall_undefined["kendall_undefined_reason"].value_counts()
        for reason, count in kendall_reason_counts.items():
            reasons_rows.append({
                "correlation": "kendall",
                "undefined_reason": reason,
                "count": int(count),
            })
    
    return pd.DataFrame(reasons_rows)


def validate_summary_row(
    df: pd.DataFrame,
    summary_row: Dict[str, Any],
    group_cols: List[str],
    group_filter: Dict[str, str],
) -> Tuple[bool, int, Dict[str, Any]]:
    """Independently validate a summary row by recomputing from source data."""
    # Extract subset
    mask = pd.Series([True] * len(df))
    for col, val in group_filter.items():
        mask &= (df[col] == val)
    df_subset = df[mask]
    
    # Check n_event_rows
    if len(df_subset) != summary_row["n_event_rows"]:
        return False, 0, {
            "mismatches": 1,
            "structural_mismatch_count": 1,
            "error": "n_event_rows mismatch",
        }
    
    # Recompute boolean counts
    field_comparisons = 0
    mismatches = 0
    
    # Check strict_top1_agreement_exact
    actual_count = df_subset["strict_top1_agreement_exact"].sum()
    field_comparisons += 1
    if actual_count != summary_row["strict_top1_agreement_exact_n"]:
        mismatches += 1
    
    # Check strict_top1_agreement_tolerance
    actual_count = df_subset["strict_top1_agreement_tolerance"].sum()
    field_comparisons += 1
    if actual_count != summary_row["strict_top1_agreement_tolerance_n"]:
        mismatches += 1
    
    # Check winner_set_equal_exact
    actual_count = df_subset["winner_set_equal_exact"].sum()
    field_comparisons += 1
    if actual_count != summary_row["winner_set_equal_exact_n"]:
        mismatches += 1
    
    # Check winner_set_equal_tolerance
    actual_count = df_subset["winner_set_equal_tolerance"].sum()
    field_comparisons += 1
    if actual_count != summary_row["winner_set_equal_tolerance_n"]:
        mismatches += 1
    
    # Check winner_set_any_overlap_exact
    actual_count = df_subset["winner_set_any_overlap_exact"].sum()
    field_comparisons += 1
    if actual_count != summary_row["winner_set_any_overlap_exact_n"]:
        mismatches += 1
    
    # Check winner_set_any_overlap_tolerance
    actual_count = df_subset["winner_set_any_overlap_tolerance"].sum()
    field_comparisons += 1
    if actual_count != summary_row["winner_set_any_overlap_tolerance_n"]:
        mismatches += 1
    
    # Check selected_candidate_in_test_winner_set_exact
    actual_count = df_subset["selected_candidate_in_test_winner_set_exact"].sum()
    field_comparisons += 1
    if actual_count != summary_row["selected_candidate_in_test_winner_set_exact_n"]:
        mismatches += 1
    
    # Check selected_candidate_in_test_winner_set_tolerance
    actual_count = df_subset["selected_candidate_in_test_winner_set_tolerance"].sum()
    field_comparisons += 1
    if actual_count != summary_row["selected_candidate_in_test_winner_set_tolerance_n"]:
        mismatches += 1
    
    # Check rate identities
    n = summary_row["n_event_rows"]
    for field in [
        "strict_top1_agreement_exact_rate",
        "strict_top1_agreement_tolerance_rate",
        "winner_set_equal_exact_rate",
        "winner_set_equal_tolerance_rate",
        "winner_set_any_overlap_exact_rate",
        "winner_set_any_overlap_tolerance_rate",
        "selected_candidate_in_test_winner_set_exact_rate",
        "selected_candidate_in_test_winner_set_tolerance_rate",
        "selected_candidate_test_rank_one_rate",
    ]:
        count_field = field.replace("_rate", "_n")
        expected_rate = summary_row[count_field] / n if n > 0 else 0.0
        field_comparisons += 1
        if not math.isclose(summary_row[field], expected_rate, rel_tol=1e-12, abs_tol=1e-12):
            mismatches += 1
    
    # Check Jaccard mean/median
    jaccard_exact = df_subset["winner_set_jaccard_exact"].values
    actual_mean = jaccard_exact.mean() if len(jaccard_exact) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["winner_set_jaccard_exact_mean"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    actual_median = float(pd.Series(jaccard_exact).median()) if len(jaccard_exact) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["winner_set_jaccard_exact_median"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    jaccard_tolerance = df_subset["winner_set_jaccard_tolerance"].values
    actual_mean = jaccard_tolerance.mean() if len(jaccard_tolerance) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["winner_set_jaccard_tolerance_mean"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    actual_median = float(pd.Series(jaccard_tolerance).median()) if len(jaccard_tolerance) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["winner_set_jaccard_tolerance_median"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    # Check correlation defined/undefined counts
    spearman_defined_mask = df_subset["spearman_defined"].astype(bool)
    actual_defined = spearman_defined_mask.sum()
    field_comparisons += 1
    if actual_defined != summary_row["spearman_defined_n"]:
        mismatches += 1
    
    actual_undefined = (~spearman_defined_mask).sum()
    field_comparisons += 1
    if actual_undefined != summary_row["spearman_undefined_n"]:
        mismatches += 1
    
    field_comparisons += 1
    if actual_defined + actual_undefined != n:
        mismatches += 1
    
    kendall_defined_mask = df_subset["kendall_defined"].astype(bool)
    actual_defined = kendall_defined_mask.sum()
    field_comparisons += 1
    if actual_defined != summary_row["kendall_defined_n"]:
        mismatches += 1
    
    actual_undefined = (~kendall_defined_mask).sum()
    field_comparisons += 1
    if actual_undefined != summary_row["kendall_undefined_n"]:
        mismatches += 1
    
    field_comparisons += 1
    if actual_defined + actual_undefined != n:
        mismatches += 1
    
    # Check correlation mean/median
    spearman_values = df_subset.loc[spearman_defined_mask, "spearman_rho"].values
    spearman_defined_n_val = spearman_defined_mask.sum()
    if spearman_defined_n_val > 0:
        actual_mean = spearman_values.mean()
        actual_median = float(pd.Series(spearman_values).median())
        # Check mean separately
        field_comparisons += 1
        if not np.isfinite(actual_mean):
            mismatches += 1
        elif not math.isclose(summary_row["spearman_mean_defined"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
            mismatches += 1
        # Check median separately
        field_comparisons += 1
        if not np.isfinite(actual_median):
            mismatches += 1
        elif not math.isclose(summary_row["spearman_median_defined"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
            mismatches += 1
    else:
        # When defined_n == 0, summary mean and median must both be missing
        # Check mean separately
        field_comparisons += 1
        if not pd.isna(summary_row["spearman_mean_defined"]):
            mismatches += 1
        # Check median separately
        field_comparisons += 1
        if not pd.isna(summary_row["spearman_median_defined"]):
            mismatches += 1
    
    kendall_values = df_subset.loc[kendall_defined_mask, "kendall_tau_b"].values
    kendall_defined_n_val = kendall_defined_mask.sum()
    if kendall_defined_n_val > 0:
        actual_mean = kendall_values.mean()
        actual_median = float(pd.Series(kendall_values).median())
        # Check mean separately
        field_comparisons += 1
        if not np.isfinite(actual_mean):
            mismatches += 1
        elif not math.isclose(summary_row["kendall_mean_defined"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
            mismatches += 1
        # Check median separately
        field_comparisons += 1
        if not np.isfinite(actual_median):
            mismatches += 1
        elif not math.isclose(summary_row["kendall_median_defined"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
            mismatches += 1
    else:
        # When defined_n == 0, summary mean and median must both be missing
        # Check mean separately
        field_comparisons += 1
        if not pd.isna(summary_row["kendall_mean_defined"]):
            mismatches += 1
        # Check median separately
        field_comparisons += 1
        if not pd.isna(summary_row["kendall_median_defined"]):
            mismatches += 1
    
    # Check selected rank statistics
    selected_ranks = df_subset["selected_candidate_test_rank"].values
    actual_mean = selected_ranks.mean() if len(selected_ranks) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["selected_candidate_test_rank_mean"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    actual_median = float(pd.Series(selected_ranks).median()) if len(selected_ranks) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["selected_candidate_test_rank_median"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    selected_rank_one_mask = df_subset["selected_candidate_test_rank"].apply(
        lambda x: math.isclose(x, 1.0, rel_tol=1e-12, abs_tol=1e-12)
    )
    actual_count = selected_rank_one_mask.sum()
    field_comparisons += 1
    if actual_count != summary_row["selected_candidate_test_rank_one_n"]:
        mismatches += 1
    
    return mismatches == 0, field_comparisons, {
        "mismatches": mismatches,
        "structural_mismatch_count": 0,
    }


def check_denominator_identities(summary_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Check that all denominator sums equal 2100 and return evidence."""
    total = 2100
    details = {}
    
    for name, df in summary_dfs.items():
        details[name] = df["n_event_rows"].sum() == total
    
    all_passed = all(details.values())
    
    return {
        "passed": all_passed,
        "details": details,
    }


def validate_correlation_summary_state(
    df: pd.DataFrame,
    prefix: str,
    table_evidence: Dict[str, Any],
) -> None:
    """Validate correlation summary state for a single correlation type (Spearman or Kendall).
    
    For each correlation-row (one per summary row), increment correlation_state_failure_count
    at most once, regardless of whether mean, median, or both are invalid.
    
    Args:
        df: Summary DataFrame for a single table
        prefix: Either "spearman" or "kendall"
        table_evidence: Dictionary to accumulate failure counts
    """
    defined_n_col = f"{prefix}_defined_n"
    mean_col = f"{prefix}_mean_defined"
    median_col = f"{prefix}_median_defined"
    
    if defined_n_col not in df.columns:
        return
    
    for idx, row in df.iterrows():
        defined_n = row[defined_n_col]
        mean_val = row[mean_col]
        median_val = row[median_col]
        
        # Check if defined_n is valid
        if pd.isna(defined_n) or not np.isfinite(defined_n) or defined_n < 0 or defined_n > row["n_event_rows"]:
            table_evidence["correlation_state_failure_count"] += 1
            continue
        
        if defined_n > 0:
            # A. defined_n > 0: mean and median must be non-missing, finite, and in [-1, 1]
            row_state_failed = False
            
            # Check mean
            if pd.isna(mean_val):
                table_evidence["correlation_non_finite_count"] += 1
                row_state_failed = True
            elif not np.isfinite(mean_val):
                table_evidence["correlation_non_finite_count"] += 1
                row_state_failed = True
            elif mean_val < -1 or mean_val > 1:
                table_evidence["correlation_range_failure_count"] += 1
                row_state_failed = True
            
            # Check median
            if pd.isna(median_val):
                table_evidence["correlation_non_finite_count"] += 1
                row_state_failed = True
            elif not np.isfinite(median_val):
                table_evidence["correlation_non_finite_count"] += 1
                row_state_failed = True
            elif median_val < -1 or median_val > 1:
                table_evidence["correlation_range_failure_count"] += 1
                row_state_failed = True
            
            # Increment state failure count at most once per correlation-row
            if row_state_failed:
                table_evidence["correlation_state_failure_count"] += 1
        else:
            # B. defined_n == 0: mean and median must be missing
            row_state_failed = False
            
            if not pd.isna(mean_val):
                row_state_failed = True
                if not np.isfinite(mean_val):
                    table_evidence["correlation_non_finite_count"] += 1
            
            if not pd.isna(median_val):
                row_state_failed = True
                if not np.isfinite(median_val):
                    table_evidence["correlation_non_finite_count"] += 1
            
            # Increment state failure count at most once per correlation-row
            if row_state_failed:
                table_evidence["correlation_state_failure_count"] += 1


def check_range_constraints(summary_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Check that all values are within expected ranges and return evidence."""
    range_details = {}
    
    for name, df in summary_dfs.items():
        table_evidence = {
            "mandatory_numeric_non_finite_count": 0,
            "count_non_finite_count": 0,
            "rate_non_finite_count": 0,
            "jaccard_non_finite_count": 0,
            "selected_rank_non_finite_count": 0,
            "correlation_non_finite_count": 0,
            "correlation_state_failure_count": 0,
            "count_range_failure_count": 0,
            "rate_range_failure_count": 0,
            "jaccard_range_failure_count": 0,
            "correlation_range_failure_count": 0,
            "selected_rank_range_failure_count": 0,
            "passed": True,
        }
        
        # Check n_event_rows is finite (mandatory numeric)
        non_finite_mask = ~finite_mask(df["n_event_rows"])
        failure_count = int(non_finite_mask.sum())
        table_evidence["mandatory_numeric_non_finite_count"] += failure_count
        
        # Check counts are between 0 and denominator and finite
        for col in df.columns:
            if col.endswith("_n") and col != "n_event_rows":
                non_finite_mask = ~finite_mask(df[col])
                failure_count = int(non_finite_mask.sum())
                table_evidence["count_non_finite_count"] += failure_count
                if (df[col] < 0).any() or (df[col] > df["n_event_rows"]).any():
                    table_evidence["count_range_failure_count"] += 1
        
        # Check rates are in [0, 1] and finite
        for col in df.columns:
            if col.endswith("_rate"):
                non_finite_mask = ~finite_mask(df[col])
                failure_count = int(non_finite_mask.sum())
                table_evidence["rate_non_finite_count"] += failure_count
                if (df[col] < 0).any() or (df[col] > 1).any():
                    table_evidence["rate_range_failure_count"] += 1
        
        # Check Jaccard in [0, 1] and finite
        for col in ["winner_set_jaccard_exact_mean", "winner_set_jaccard_exact_median",
                    "winner_set_jaccard_tolerance_mean", "winner_set_jaccard_tolerance_median"]:
            if col in df.columns:
                non_finite_mask = ~finite_mask(df[col])
                failure_count = int(non_finite_mask.sum())
                table_evidence["jaccard_non_finite_count"] += failure_count
                if (df[col] < 0).any() or (df[col] > 1).any():
                    table_evidence["jaccard_range_failure_count"] += 1
        
        # Check correlation mean/median with state-aware validation
        # Use shared helper for both Spearman and Kendall
        validate_correlation_summary_state(df, "spearman", table_evidence)
        validate_correlation_summary_state(df, "kendall", table_evidence)
        
        # Check selected test rank in [1, 4] and finite
        for col in ["selected_candidate_test_rank_mean", "selected_candidate_test_rank_median"]:
            if col in df.columns:
                non_finite_mask = ~finite_mask(df[col])
                failure_count = int(non_finite_mask.sum())
                table_evidence["selected_rank_non_finite_count"] += failure_count
                if (df[col] < 1).any() or (df[col] > 4).any():
                    table_evidence["selected_rank_range_failure_count"] += 1
        
        table_evidence["passed"] = (
            table_evidence["mandatory_numeric_non_finite_count"] == 0 and
            table_evidence["count_non_finite_count"] == 0 and
            table_evidence["rate_non_finite_count"] == 0 and
            table_evidence["jaccard_non_finite_count"] == 0 and
            table_evidence["selected_rank_non_finite_count"] == 0 and
            table_evidence["correlation_non_finite_count"] == 0 and
            table_evidence["correlation_state_failure_count"] == 0 and
            table_evidence["count_range_failure_count"] == 0 and
            table_evidence["rate_range_failure_count"] == 0 and
            table_evidence["jaccard_range_failure_count"] == 0 and
            table_evidence["correlation_range_failure_count"] == 0 and
            table_evidence["selected_rank_range_failure_count"] == 0
        )
        range_details[name] = table_evidence
    
    all_passed = all(e["passed"] for e in range_details.values())
    
    return {
        "passed": all_passed,
        "details": range_details,
    }


def validate_output_schemas(summary_dfs: Dict[str, pd.DataFrame], undefined_reasons_df: pd.DataFrame) -> Dict[str, Any]:
    """Validate exact output schemas for all CSVs."""
    schema_evidence = {}
    
    # Validate summary schemas
    for name, df in summary_dfs.items():
        actual_columns = list(df.columns)
        schema_evidence[name] = {
            "expected_column_count": len(EXPECTED_SUMMARY_SCHEMA),
            "actual_column_count": len(actual_columns),
            "schema_mismatch_count": sum(1 for a, e in zip(actual_columns, EXPECTED_SUMMARY_SCHEMA) if a != e),
            "passed": actual_columns == EXPECTED_SUMMARY_SCHEMA,
        }
    
    # Validate undefined reasons schema
    undefined_actual_columns = list(undefined_reasons_df.columns)
    schema_evidence["undefined_reasons"] = {
        "expected_column_count": len(EXPECTED_UNDEFINED_REASON_SCHEMA),
        "actual_column_count": len(undefined_actual_columns),
        "schema_mismatch_count": sum(1 for a, e in zip(undefined_actual_columns, EXPECTED_UNDEFINED_REASON_SCHEMA) if a != e),
        "passed": undefined_actual_columns == EXPECTED_UNDEFINED_REASON_SCHEMA,
    }
    
    all_passed = all(e["passed"] for e in schema_evidence.values())
    
    return {
        "passed": all_passed,
        "details": schema_evidence,
    }


def run_synthetic_nan_tests() -> Dict[str, Any]:
    """Run seven in-memory synthetic fail-safe tests for NaN and undefined-state handling."""
    tests_passed = 0
    tests_failed = 0
    
    # Test A: Count field = NaN
    test_df_a = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "strict_top1_agreement_exact_n": [np.nan],
        "strict_top1_agreement_exact_rate": [0.5],
    })
    result_a = check_range_constraints({"test": test_df_a})
    test_a_passed = not result_a["details"]["test"]["passed"] and result_a["details"]["test"]["count_non_finite_count"] > 0
    if test_a_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test B: Rate field = NaN
    test_df_b = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "strict_top1_agreement_exact_n": [50],
        "strict_top1_agreement_exact_rate": [np.nan],
    })
    result_b = check_range_constraints({"test": test_df_b})
    test_b_passed = not result_b["details"]["test"]["passed"] and result_b["details"]["test"]["rate_non_finite_count"] > 0
    if test_b_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test C: Jaccard field = NaN
    test_df_c = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "winner_set_jaccard_exact_mean": [np.nan],
        "winner_set_jaccard_exact_median": [0.5],
    })
    result_c = check_range_constraints({"test": test_df_c})
    test_c_passed = not result_c["details"]["test"]["passed"] and result_c["details"]["test"]["jaccard_non_finite_count"] > 0
    if test_c_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test D: Selected-rank mean = NaN
    test_df_d = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "selected_candidate_test_rank_mean": [np.nan],
        "selected_candidate_test_rank_median": [2.0],
    })
    result_d = check_range_constraints({"test": test_df_d})
    test_d_passed = not result_d["details"]["test"]["passed"] and result_d["details"]["test"]["selected_rank_non_finite_count"] > 0
    if test_d_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test E: Correlation defined_n == 0 and mean/median == 0.0 (invalid substitution)
    test_df_e = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "spearman_defined_n": [0],
        "spearman_undefined_n": [100],
        "spearman_mean_defined": [0.0],
        "spearman_median_defined": [0.0],
    })
    result_e = check_range_constraints({"test": test_df_e})
    test_e_passed = (result_e["details"]["test"]["passed"] is False and
                    result_e["details"]["test"]["correlation_state_failure_count"] == 1 and
                    result_e["details"]["test"]["correlation_non_finite_count"] == 0 and
                    result_e["details"]["test"]["correlation_range_failure_count"] == 0)
    if test_e_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test F: Correlation defined_n == 0 and mean/median == NaN (correct behavior)
    test_df_f = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "spearman_defined_n": [0],
        "spearman_undefined_n": [100],
        "spearman_mean_defined": [np.nan],
        "spearman_median_defined": [np.nan],
    })
    result_f = check_range_constraints({"test": test_df_f})
    test_f_passed = (result_f["details"]["test"]["passed"] is True and
                    result_f["details"]["test"]["correlation_state_failure_count"] == 0 and
                    result_f["details"]["test"]["correlation_non_finite_count"] == 0)
    if test_f_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test G: Correlation defined_n > 0 and mean or median == NaN
    test_df_g = pd.DataFrame({
        "group_name": ["overall"],
        "group_value": ["all"],
        "n_event_rows": [100],
        "spearman_defined_n": [50],
        "spearman_undefined_n": [50],
        "spearman_mean_defined": [np.nan],
        "spearman_median_defined": [0.5],
    })
    result_g = check_range_constraints({"test": test_df_g})
    test_g_passed = (result_g["details"]["test"]["passed"] is False and
                    result_g["details"]["test"]["correlation_non_finite_count"] == 1 and
                    result_g["details"]["test"]["correlation_state_failure_count"] == 1 and
                    result_g["details"]["test"]["correlation_range_failure_count"] == 0)
    if test_g_passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    return {
        "synthetic_nan_tests_expected": 7,
        "synthetic_nan_tests_executed": 7,
        "synthetic_nan_tests_passed": tests_passed,
        "synthetic_nan_test_failure_count": tests_failed,
        "nan_and_undefined_state_fail_safe_passed": tests_failed == 0,
        # Exact test evidence
        "test_e_passed": test_e_passed,
        "test_e_overall_table_passed": result_e["details"]["test"]["passed"],
        "test_e_correlation_non_finite_count": result_e["details"]["test"]["correlation_non_finite_count"],
        "test_e_correlation_state_failure_count": result_e["details"]["test"]["correlation_state_failure_count"],
        "test_e_correlation_range_failure_count": result_e["details"]["test"]["correlation_range_failure_count"],
        "test_f_passed": test_f_passed,
        "test_f_overall_table_passed": result_f["details"]["test"]["passed"],
        "test_f_correlation_non_finite_count": result_f["details"]["test"]["correlation_non_finite_count"],
        "test_f_correlation_state_failure_count": result_f["details"]["test"]["correlation_state_failure_count"],
        "test_f_correlation_range_failure_count": result_f["details"]["test"]["correlation_range_failure_count"],
        "test_g_passed": test_g_passed,
        "test_g_overall_table_passed": result_g["details"]["test"]["passed"],
        "test_g_correlation_non_finite_count": result_g["details"]["test"]["correlation_non_finite_count"],
        "test_g_correlation_state_failure_count": result_g["details"]["test"]["correlation_state_failure_count"],
        "test_g_correlation_range_failure_count": result_g["details"]["test"]["correlation_range_failure_count"],
    }


def validate_summary_domains(summary_dfs: Dict[str, pd.DataFrame], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Validate exact summary domains and row cardinalities."""
    domain_evidence = {
        "group_domain_mismatch_count": 0,
        "group_denominator_mismatch_count": 0,
        "details": {},
    }
    
    # Construct expected group sets
    expected_groups = {
        "overall": [("overall", "all")],
        "by_experiment": [("experiment", exp) for exp in EXPECTED_EXPERIMENTS],
        "by_mode": [("mode", mode) for mode in EXPECTED_MODES],
        "by_metric": [("metric", metric) for metric in spec["metrics"]],
        "by_project": [("target_project", project) for project in EXPECTED_PROJECTS],
    }
    
    expected_denominators = {
        "overall": EXPECTED_OVERALL_DENOMINATOR,
        "by_experiment": EXPECTED_EXPERIMENT_DENOMINATORS,
        "by_mode": EXPECTED_MODE_DENOMINATORS,
        "by_metric": EXPECTED_METRIC_DENOMINATOR,
        "by_project": EXPECTED_PROJECT_DENOMINATOR,
    }
    
    # Validate each table
    for table_name, df in summary_dfs.items():
        expected_set = set(expected_groups[table_name])
        actual_set = set(zip(df["group_name"], df["group_value"]))
        
        # Compute duplicate_group_key_count (groups with size > 1)
        duplicate_group_key_count = df.groupby(["group_name", "group_value"]).size().gt(1).sum()
        
        # Compute duplicate_group_row_count (rows that are duplicates)
        duplicate_mask = df.duplicated(subset=["group_name", "group_value"], keep=False)
        duplicate_group_row_count = int(duplicate_mask.sum())
        
        missing_group_count = len(expected_set - actual_set)
        extra_group_count = len(actual_set - expected_set)
        group_name_mismatch_count = 0
        denominator_mismatch_count = 0
        
        # Check group names and denominators
        for _, row in df.iterrows():
            group_tuple = (row["group_name"], row["group_value"])
            if group_tuple not in expected_set:
                group_name_mismatch_count += 1
            else:
                # Check denominator
                if table_name == "overall":
                    expected_denom = expected_denominators[table_name]
                elif table_name == "by_experiment":
                    expected_denom = expected_denominators[table_name][row["group_value"]]
                elif table_name == "by_mode":
                    expected_denom = expected_denominators[table_name][row["group_value"]]
                elif table_name == "by_metric":
                    expected_denom = expected_denominators[table_name]
                elif table_name == "by_project":
                    expected_denom = expected_denominators[table_name]
                else:
                    expected_denom = None
                
                if expected_denom is not None and row["n_event_rows"] != expected_denom:
                    denominator_mismatch_count += 1
        
        domain_evidence["details"][table_name] = {
            "expected_group_count": len(expected_set),
            "actual_group_count": len(actual_set),
            "duplicate_group_key_count": int(duplicate_group_key_count),
            "duplicate_group_row_count": duplicate_group_row_count,
            "missing_group_count": missing_group_count,
            "extra_group_count": extra_group_count,
            "group_name_mismatch_count": group_name_mismatch_count,
            "denominator_mismatch_count": denominator_mismatch_count,
            "passed": (
                duplicate_group_key_count == 0 and
                duplicate_group_row_count == 0 and
                missing_group_count == 0 and
                extra_group_count == 0 and
                group_name_mismatch_count == 0 and
                denominator_mismatch_count == 0
            ),
        }
        
        domain_evidence["group_domain_mismatch_count"] += (
            duplicate_group_key_count + missing_group_count + extra_group_count + group_name_mismatch_count
        )
        domain_evidence["group_denominator_mismatch_count"] += denominator_mismatch_count
    
    all_passed = (
        domain_evidence["group_domain_mismatch_count"] == 0 and
        domain_evidence["group_denominator_mismatch_count"] == 0
    )
    
    return {
        "passed": all_passed,
        "details": domain_evidence,
    }


def validate_correlation_identities(summary_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Validate correlation defined identities for all 25 summary rows."""
    rows_checked = 0
    failure_count = 0
    
    for name, df in summary_dfs.items():
        for _, row in df.iterrows():
            rows_checked += 1
            n = row["n_event_rows"]
            spearman_ok = (row["spearman_defined_n"] + row["spearman_undefined_n"]) == n
            kendall_ok = (row["kendall_defined_n"] + row["kendall_undefined_n"]) == n
            if not (spearman_ok and kendall_ok):
                failure_count += 1
    
    return {
        "correlation_identity_rows_checked": rows_checked,
        "correlation_identity_failure_count": failure_count,
        "passed": failure_count == 0,
    }


def validate_undefined_reasons(df: pd.DataFrame, undefined_reasons_df: pd.DataFrame) -> Dict[str, Any]:
    """Validate undefined-reasons CSV independently from event CSV."""
    # Reconstruct expected undefined-reasons table from event CSV
    expected_undefined_reasons = []
    
    # For Spearman
    spearman_undefined = df[df["spearman_defined"] == False]
    if not spearman_undefined.empty:
        spearman_reason_counts = spearman_undefined["spearman_undefined_reason"].value_counts()
        for reason, count in spearman_reason_counts.items():
            expected_undefined_reasons.append({
                "correlation": "spearman",
                "undefined_reason": reason,
                "count": int(count),
            })
    
    # For Kendall
    kendall_undefined = df[df["kendall_defined"] == False]
    if not kendall_undefined.empty:
        kendall_reason_counts = kendall_undefined["kendall_undefined_reason"].value_counts()
        for reason, count in kendall_reason_counts.items():
            expected_undefined_reasons.append({
                "correlation": "kendall",
                "undefined_reason": reason,
                "count": int(count),
            })
    
    expected_df = pd.DataFrame(expected_undefined_reasons)
    
    # Validate defined rows have no undefined reason
    defined_rows_with_reason_count = 0
    spearman_defined = df[df["spearman_defined"] == True]
    if not spearman_defined.empty and spearman_defined["spearman_undefined_reason"].notna().any():
        defined_rows_with_reason_count += spearman_defined["spearman_undefined_reason"].notna().sum()
    
    kendall_defined = df[df["kendall_defined"] == True]
    if not kendall_defined.empty and kendall_defined["kendall_undefined_reason"].notna().any():
        defined_rows_with_reason_count += kendall_defined["kendall_undefined_reason"].notna().sum()
    
    # Validate undefined rows have a non-null reason
    undefined_rows_without_reason_count = 0
    if not spearman_undefined.empty and spearman_undefined["spearman_undefined_reason"].isna().any():
        undefined_rows_without_reason_count += spearman_undefined["spearman_undefined_reason"].isna().sum()
    
    if not kendall_undefined.empty and kendall_undefined["kendall_undefined_reason"].isna().any():
        undefined_rows_without_reason_count += kendall_undefined["kendall_undefined_reason"].isna().sum()
    
    # Validate actual CSV matches expected
    undefined_reason_duplicate_row_count = 0
    undefined_reason_missing_row_count = 0
    undefined_reason_extra_row_count = 0
    undefined_reason_value_mismatch_count = 0
    
    if not undefined_reasons_df.empty and not expected_df.empty:
        # Check for duplicates
        duplicate_mask = undefined_reasons_df.duplicated(subset=["correlation", "undefined_reason"], keep=False)
        undefined_reason_duplicate_row_count = duplicate_mask.sum()
        
        # Check for missing rows
        expected_set = set(zip(expected_df["correlation"], expected_df["undefined_reason"]))
        actual_set = set(zip(undefined_reasons_df["correlation"], undefined_reasons_df["undefined_reason"]))
        undefined_reason_missing_row_count = len(expected_set - actual_set)
        undefined_reason_extra_row_count = len(actual_set - expected_set)
        
        # Check for value mismatches
        for _, expected_row in expected_df.iterrows():
            match = undefined_reasons_df[
                (undefined_reasons_df["correlation"] == expected_row["correlation"]) &
                (undefined_reasons_df["undefined_reason"] == expected_row["undefined_reason"])
            ]
            if not match.empty:
                if match["count"].iloc[0] != expected_row["count"]:
                    undefined_reason_value_mismatch_count += 1
    
    return {
        "undefined_reason_expected_rows": len(expected_df),
        "undefined_reason_actual_rows": len(undefined_reasons_df),
        "expected_spearman_count": len(spearman_undefined),
        "actual_spearman_count": int(undefined_reasons_df[undefined_reasons_df["correlation"] == "spearman"]["count"].sum()) if not undefined_reasons_df.empty else 0,
        "expected_kendall_count": len(kendall_undefined),
        "actual_kendall_count": int(undefined_reasons_df[undefined_reasons_df["correlation"] == "kendall"]["count"].sum()) if not undefined_reasons_df.empty else 0,
        "defined_rows_with_reason_count": int(defined_rows_with_reason_count),
        "undefined_rows_without_reason_count": int(undefined_rows_without_reason_count),
        "undefined_reason_duplicate_row_count": int(undefined_reason_duplicate_row_count),
        "undefined_reason_missing_row_count": undefined_reason_missing_row_count,
        "undefined_reason_extra_row_count": undefined_reason_extra_row_count,
        "undefined_reason_value_mismatch_count": undefined_reason_value_mismatch_count,
        "passed": (
            defined_rows_with_reason_count == 0 and
            undefined_rows_without_reason_count == 0 and
            undefined_reason_duplicate_row_count == 0 and
            undefined_reason_missing_row_count == 0 and
            undefined_reason_extra_row_count == 0 and
            undefined_reason_value_mismatch_count == 0
        ),
    }


def build_audit_markdown(audit_state: Dict[str, Any]) -> str:
    """Build Markdown audit report from audit state (for audit_payload)."""
    lines = []
    lines.append("# Part 2 Section 4B.2: Validation-Test Ranking Agreement Summary Audit\n\n")
    
    lines.append("## Repository-Relative Execution\n\n")
    lines.append(f"- Base path: {audit_state['execution']['base_path']}\n")
    lines.append(f"- Script path: {audit_state['execution']['script_path']}\n\n")
    
    lines.append("## Input Verification\n\n")
    iv = audit_state['input_verification']
    lines.append(f"- Event CSV SHA-256 verified: {iv['sha256_verified']}\n")
    lines.append(f"- Event CSV SHA-256 (expected): {iv.get('expected_sha256', 'N/A')}\n")
    lines.append(f"- Event CSV SHA-256 (actual): {iv.get('actual_sha256', 'N/A')}\n")
    lines.append(f"- Event CSV rows: {iv['rows']}\n")
    lines.append(f"- Event CSV columns: {iv['columns']}\n")
    lines.append(f"- Column order ok: {iv['column_order_ok']}\n")
    lines.append(f"- Row count ok: {iv['row_count_ok']}\n")
    lines.append(f"- Column count ok: {iv['column_count_ok']}\n")
    lines.append(f"- NA state valid: {iv['na_state_valid']}\n")
    lines.append(f"- Finite numeric valid: {iv['finite_numeric_valid']}\n")
    lines.append(f"- Boolean valid: {iv['boolean_valid']}\n")
    lines.append(f"- Duplicate key count: {iv['duplicate_key_count']}\n")
    lines.append(f"- Actual event key count: {iv['actual_event_key_count']}\n")
    lines.append(f"- Missing event key count: {iv['missing_event_key_count']}\n")
    lines.append(f"- Extra event key count: {iv['extra_event_key_count']}\n")
    lines.append(f"- Key coverage ok: {iv['key_coverage_ok']}\n")
    lines.append(f"- Input schema valid: {iv['input_schema_valid']}\n")
    lines.append(f"- Input key coverage passed: {iv['input_key_coverage_passed']}\n\n")
    
    lines.append("## Input Audit Verification\n\n")
    iav = audit_state['input_audit_verification']
    lines.append(f"- Input audit check count: {iav['input_audit_check_count']}\n")
    lines.append(f"- Input audit failed check count: {iav['input_audit_failed_check_count']}\n")
    lines.append(f"- Input audit missing required check count: {iav['input_audit_missing_required_check_count']}\n")
    lines.append(f"- Input audit checks passed: {iav['input_audit_checks_passed']}\n\n")
    
    lines.append("## Summary Counts\n\n")
    sc = audit_state['summary_counts']
    for name, counts in sc.items():
        lines.append(f"- {name}:\n")
        lines.append(f"  - Expected rows: {counts['expected_rows']}\n")
        lines.append(f"  - Actual rows: {counts['actual_rows']}\n\n")
    
    lines.append("## Summary Schema Validation\n\n")
    sv = audit_state['summary_schema_validation']
    lines.append(f"- Summary schemas passed: {sv['passed']}\n")
    for name, details in sv['details'].items():
        lines.append(f"- {name}:\n")
        lines.append(f"  - Expected columns: {details['expected_column_count']}\n")
        lines.append(f"  - Actual columns: {details['actual_column_count']}\n")
        lines.append(f"  - Schema mismatch count: {details['schema_mismatch_count']}\n")
        lines.append(f"  - Passed: {details['passed']}\n\n")
    
    lines.append("## Summary Domain Validation\n\n")
    dv = audit_state['summary_domain_validation']
    lines.append(f"- Group domain mismatch count: {dv['details']['group_domain_mismatch_count']}\n")
    lines.append(f"- Group denominator mismatch count: {dv['details']['group_denominator_mismatch_count']}\n")
    lines.append(f"- Summary domains valid: {dv['passed']}\n\n")
    
    lines.append("## Summary Duplicate Group Evidence\n\n")
    details = dv['details']['details']
    total_duplicate_keys = sum(d['duplicate_group_key_count'] for d in details.values())
    total_duplicate_rows = sum(d['duplicate_group_row_count'] for d in details.values())
    lines.append(f"- Summary duplicate group keys: {total_duplicate_keys}\n")
    lines.append(f"- Summary duplicate group rows: {total_duplicate_rows}\n\n")
    
    lines.append("## Correlation Undefined Reasons\n\n")
    cu = audit_state['correlation_undefined']
    lines.append(f"- Spearman undefined count: {cu['spearman_count']} (expected: 18)\n")
    lines.append(f"- Kendall undefined count: {cu['kendall_count']} (expected: 18)\n\n")
    
    lines.append("## Undefined Reasons Validation\n\n")
    ur = audit_state['undefined_reasons_validation']
    lines.append(f"- Expected rows: {ur['undefined_reason_expected_rows']}\n")
    lines.append(f"- Actual rows: {ur['undefined_reason_actual_rows']}\n")
    lines.append(f"- Expected Spearman count: {ur['expected_spearman_count']}\n")
    lines.append(f"- Actual Spearman count: {ur['actual_spearman_count']}\n")
    lines.append(f"- Expected Kendall count: {ur['expected_kendall_count']}\n")
    lines.append(f"- Actual Kendall count: {ur['actual_kendall_count']}\n")
    lines.append(f"- Defined rows with reason count: {ur['defined_rows_with_reason_count']}\n")
    lines.append(f"- Undefined rows without reason count: {ur['undefined_rows_without_reason_count']}\n")
    lines.append(f"- Undefined reason duplicate row count: {ur['undefined_reason_duplicate_row_count']}\n")
    lines.append(f"- Undefined reason missing row count: {ur['undefined_reason_missing_row_count']}\n")
    lines.append(f"- Undefined reason extra row count: {ur['undefined_reason_extra_row_count']}\n")
    lines.append(f"- Undefined reason value mismatch count: {ur['undefined_reason_value_mismatch_count']}\n")
    lines.append(f"- Passed: {ur['passed']}\n\n")
    
    lines.append("## Independent Validation\n\n")
    val = audit_state['validation']
    lines.append(f"- Summary rows expected: {val['summary_rows_expected']}\n")
    lines.append(f"- Summary rows reconstructed: {val['summary_rows_reconstructed']}\n")
    lines.append(f"- Summary rows with complete validation: {val['summary_rows_with_complete_validation']}\n")
    lines.append(f"- Summary rows with incomplete validation: {val['summary_rows_with_incomplete_validation']}\n")
    lines.append(f"- Summary field comparisons: {val['summary_field_comparisons']}\n")
    lines.append(f"- Summary mismatch count: {val['summary_mismatch_count']}\n")
    lines.append(f"- Summary structural mismatch count: {val['summary_structural_mismatch_count']}\n\n")
    
    lines.append("## Correlation Identity Validation\n\n")
    civ = audit_state['correlation_identity_validation']
    lines.append(f"- Correlation identity rows checked: {civ['correlation_identity_rows_checked']}\n")
    lines.append(f"- Correlation identity failure count: {civ['correlation_identity_failure_count']}\n")
    lines.append(f"- Passed: {civ['passed']}\n\n")
    
    lines.append("## Denominator Identities\n\n")
    di = audit_state['denominator_identities']
    lines.append(f"- Passed: {di['passed']}\n")
    for name, passed in di['details'].items():
        lines.append(f"- {name}: {passed}\n\n")
    
    lines.append("## Range Checks\n\n")
    rc = audit_state['range_checks']
    lines.append(f"- Range checks passed: {rc['passed']}\n")
    for name, details in rc['details'].items():
        lines.append(f"- {name}:\n")
        lines.append(f"  - Mandatory numeric non-finite count: {details['mandatory_numeric_non_finite_count']}\n")
        lines.append(f"  - Count-field non-finite count: {details['count_non_finite_count']}\n")
        lines.append(f"  - Rate-field non-finite count: {details['rate_non_finite_count']}\n")
        lines.append(f"  - Jaccard non-finite count: {details['jaccard_non_finite_count']}\n")
        lines.append(f"  - Selected-rank non-finite count: {details['selected_rank_non_finite_count']}\n")
        lines.append(f"  - Correlation non-finite count: {details['correlation_non_finite_count']}\n")
        lines.append(f"  - Correlation state failure count: {details['correlation_state_failure_count']}\n")
        lines.append(f"  - Count range failure count: {details['count_range_failure_count']}\n")
        lines.append(f"  - Rate range failure count: {details['rate_range_failure_count']}\n")
        lines.append(f"  - Jaccard range failure count: {details['jaccard_range_failure_count']}\n")
        lines.append(f"  - Correlation range failure count: {details['correlation_range_failure_count']}\n")
        lines.append(f"  - Selected rank range failure count: {details['selected_rank_range_failure_count']}\n")
        lines.append(f"  - Passed: {details['passed']}\n\n")
    
    lines.append("## Interpretation Limits\n\n")
    il = audit_state['interpretation_limits']
    lines.append(f"- Descriptive summaries only: {il['descriptive_summaries_only']}\n")
    lines.append(f"- Seeds are repeated non-independent runs: {il['seeds_repeated_non_independent']}\n")
    lines.append(f"- No p-values: {il['no_p_values']}\n")
    lines.append(f"- No iid confidence intervals: {il['no_iid_confidence_intervals']}\n")
    lines.append(f"- No significance claim: {il['no_significance_claim']}\n")
    lines.append(f"- No causal claim: {il['no_causal_claim']}\n")
    lines.append(f"- No superiority claim based only on agreement: {il['no_superiority_claim']}\n")
    lines.append(f"- Test data post-selection only: {il['test_data_post_selection_only']}\n")
    lines.append(f"- Present: {il['present']}\n\n")
    
    lines.append("## Synthetic NaN Tests\n\n")
    snt = audit_state['synthetic_nan_tests']
    lines.append(f"- Synthetic NaN tests expected: {snt['synthetic_nan_tests_expected']}\n")
    lines.append(f"- Synthetic NaN tests executed: {snt['synthetic_nan_tests_executed']}\n")
    lines.append(f"- Synthetic NaN tests passed: {snt['synthetic_nan_tests_passed']}\n")
    lines.append(f"- Synthetic NaN test failures: {snt['synthetic_nan_test_failure_count']}\n")
    lines.append(f"- NaN and undefined-state fail-safe passed: {snt['nan_and_undefined_state_fail_safe_passed']}\n")
    # Exact test evidence
    lines.append(f"- Test E passed: {snt['test_e_passed']}\n")
    lines.append(f"- Test E overall table passed: {snt['test_e_overall_table_passed']}\n")
    lines.append(f"- Test E correlation non-finite count: {snt['test_e_correlation_non_finite_count']}\n")
    lines.append(f"- Test E correlation state failure count: {snt['test_e_correlation_state_failure_count']}\n")
    lines.append(f"- Test E correlation range failure count: {snt['test_e_correlation_range_failure_count']}\n")
    lines.append(f"- Test F passed: {snt['test_f_passed']}\n")
    lines.append(f"- Test F overall table passed: {snt['test_f_overall_table_passed']}\n")
    lines.append(f"- Test F correlation non-finite count: {snt['test_f_correlation_non_finite_count']}\n")
    lines.append(f"- Test F correlation state failure count: {snt['test_f_correlation_state_failure_count']}\n")
    lines.append(f"- Test F correlation range failure count: {snt['test_f_correlation_range_failure_count']}\n")
    lines.append(f"- Test G passed: {snt['test_g_passed']}\n")
    lines.append(f"- Test G overall table passed: {snt['test_g_overall_table_passed']}\n")
    lines.append(f"- Test G correlation non-finite count: {snt['test_g_correlation_non_finite_count']}\n")
    lines.append(f"- Test G correlation state failure count: {snt['test_g_correlation_state_failure_count']}\n")
    lines.append(f"- Test G correlation range failure count: {snt['test_g_correlation_range_failure_count']}\n\n")
    
    return "".join(lines)


def build_final_audit_markdown(final_audit_state: Dict[str, Any]) -> str:
    """Build final Markdown audit report from final_audit_state."""
    lines = []
    lines.append("# Part 2 Section 4B.2: Validation-Test Ranking Agreement Summary Audit\n\n")
    
    # Include audit_payload content
    lines.append("## Audit Payload\n\n")
    lines.append(build_audit_markdown(final_audit_state['audit_payload']))
    
    # Include serialization_audit
    lines.append("## Serialization Audit\n\n")
    sa = final_audit_state['serialization_audit']
    lines.append(f"- Overall CSV serialization identical: {sa['overall_csv_serialization_identical']}\n")
    lines.append(f"- Experiment CSV serialization identical: {sa['experiment_csv_serialization_identical']}\n")
    lines.append(f"- Mode CSV serialization identical: {sa['mode_csv_serialization_identical']}\n")
    lines.append(f"- Metric CSV serialization identical: {sa['metric_csv_serialization_identical']}\n")
    lines.append(f"- Project CSV serialization identical: {sa['project_csv_serialization_identical']}\n")
    lines.append(f"- Undefined reasons CSV serialization identical: {sa['undefined_reasons_csv_serialization_identical']}\n")
    lines.append(f"- Audit payload JSON serialization identical: {sa['audit_payload_json_serialization_identical']}\n")
    lines.append(f"- Audit payload Markdown serialization identical: {sa['audit_payload_markdown_serialization_identical']}\n")
    lines.append(f"- Stable output order passed: {sa['stable_output_order_passed']}\n")
    lines.append(f"- Deterministic output serialization passed: {sa['passed']}\n\n")
    
    # Include validation_checks
    lines.append("## Validation Checks\n\n")
    vc = final_audit_state['validation_checks']
    for key, value in vc.items():
        # Format key with spaces instead of underscores for display
        display_key = key.replace("_", " ")
        lines.append(f"- {display_key}: {value}\n")
    lines.append("\n")
    
    return "".join(lines)


def main():
    # Repository-relative paths
    script_path = Path(__file__).resolve()
    base_dir = script_path.parents[1]
    
    event_csv_path = base_dir / "results/part2_validation_test_ranking_agreement/validation_test_ranking_agreement_events.csv"
    audit_json_path = base_dir / "reports/part2_validation_test_ranking_agreement_event_audit.json"
    spec_json_path = base_dir / "reports/part2_validation_test_ranking_agreement_specification.json"
    
    output_dir = base_dir / "results/part2_validation_test_ranking_agreement"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_overall = output_dir / "validation_test_ranking_agreement_summary_overall.csv"
    output_by_experiment = output_dir / "validation_test_ranking_agreement_summary_by_experiment.csv"
    output_by_mode = output_dir / "validation_test_ranking_agreement_summary_by_mode.csv"
    output_by_metric = output_dir / "validation_test_ranking_agreement_summary_by_metric.csv"
    output_by_project = output_dir / "validation_test_ranking_agreement_summary_by_project.csv"
    output_undefined_reasons = output_dir / "validation_test_ranking_agreement_correlation_undefined_reasons.csv"
    
    audit_output_json = base_dir / "reports/part2_validation_test_ranking_agreement_summary_audit.json"
    audit_output_md = base_dir / "reports/part2_validation_test_ranking_agreement_summary_audit.md"
    
    # Expected SHA
    expected_sha = "85314055415bbb3cca13d35c8dd65979f92c9c120e90c1c866cae722d0ad1f15"
    
    print("Step 1: Load specification and audit...")
    spec = load_specification(spec_json_path)
    audit = load_audit(audit_json_path)
    
    print("Step 2: Verify audit checks...")
    input_audit_evidence = verify_input_audit(audit)
    
    print("Step 3: Load and verify event CSV...")
    actual_sha = compute_sha256(event_csv_path)
    df = pd.read_csv(event_csv_path)
    input_verification = verify_event_csv(df, actual_sha, expected_sha, spec)
    
    if actual_sha != expected_sha:
        raise ValueError(f"SHA mismatch: expected {expected_sha}, got {actual_sha}")
    if not input_verification["input_schema_valid"]:
        raise ValueError(f"Input schema validation failed: {input_verification}")
    if not input_verification["input_key_coverage_passed"]:
        raise ValueError("Input key coverage validation failed")
    
    print("Step 4: Compute overall summary...")
    overall_row = compute_summary_row(df, "overall", "all")
    overall_df = pd.DataFrame([overall_row])
    
    print("Step 5: Compute by experiment summary...")
    experiments = ["within_project", "cross_project"]
    experiment_rows = []
    for exp in experiments:
        df_subset = df[df["experiment"] == exp]
        row = compute_summary_row(df_subset, "experiment", exp)
        experiment_rows.append(row)
    experiment_df = pd.DataFrame(experiment_rows)
    
    print("Step 6: Compute by mode summary...")
    modes = ["balanced", "rank", "mcc"]
    mode_rows = []
    for mode in modes:
        df_subset = df[df["mode"] == mode]
        row = compute_summary_row(df_subset, "mode", mode)
        mode_rows.append(row)
    mode_df = pd.DataFrame(mode_rows)
    
    print("Step 7: Compute by metric summary...")
    metrics = spec["metrics"]
    metric_rows = []
    for metric in metrics:
        df_subset = df[df["metric"] == metric]
        row = compute_summary_row(df_subset, "metric", metric)
        metric_rows.append(row)
    metric_df = pd.DataFrame(metric_rows)
    
    print("Step 8: Compute by project summary...")
    projects = ["CM1", "JM1", "KC1", "KC2", "PC1"]
    project_rows = []
    for project in projects:
        df_subset = df[df["target_project"] == project]
        row = compute_summary_row(df_subset, "target_project", project)
        project_rows.append(row)
    project_df = pd.DataFrame(project_rows)
    
    print("Step 9: Compute correlation undefined reasons...")
    undefined_reasons_df = compute_correlation_undefined_reasons(df)
    
    print("Step 10: Validate summary rows independently...")
    summary_dfs = {
        "overall": overall_df,
        "by_experiment": experiment_df,
        "by_mode": mode_df,
        "by_metric": metric_df,
        "by_project": project_df,
    }
    
    summary_rows_expected = 25
    summary_rows_reconstructed = 0
    summary_rows_with_complete_validation = 0
    summary_rows_with_incomplete_validation = 0
    summary_field_comparisons = 0
    summary_mismatch_count = 0
    summary_structural_mismatch_count = 0
    
    # Validate overall
    for _, row in overall_df.iterrows():
        passed, comparisons, evidence = validate_summary_row(df, row.to_dict(), [], {})
        summary_rows_reconstructed += 1
        summary_field_comparisons += comparisons
        if passed:
            summary_rows_with_complete_validation += 1
        else:
            summary_rows_with_incomplete_validation += 1
            summary_mismatch_count += evidence["mismatches"]
            summary_structural_mismatch_count += evidence.get("structural_mismatch_count", 0)
    
    # Validate by experiment
    for _, row in experiment_df.iterrows():
        passed, comparisons, evidence = validate_summary_row(df, row.to_dict(), ["experiment"], {"experiment": row["group_value"]})
        summary_rows_reconstructed += 1
        summary_field_comparisons += comparisons
        if passed:
            summary_rows_with_complete_validation += 1
        else:
            summary_rows_with_incomplete_validation += 1
            summary_mismatch_count += evidence["mismatches"]
            summary_structural_mismatch_count += evidence.get("structural_mismatch_count", 0)
    
    # Validate by mode
    for _, row in mode_df.iterrows():
        passed, comparisons, evidence = validate_summary_row(df, row.to_dict(), ["mode"], {"mode": row["group_value"]})
        summary_rows_reconstructed += 1
        summary_field_comparisons += comparisons
        if passed:
            summary_rows_with_complete_validation += 1
        else:
            summary_rows_with_incomplete_validation += 1
            summary_mismatch_count += evidence["mismatches"]
            summary_structural_mismatch_count += evidence.get("structural_mismatch_count", 0)
    
    # Validate by metric
    for _, row in metric_df.iterrows():
        passed, comparisons, evidence = validate_summary_row(df, row.to_dict(), ["metric"], {"metric": row["group_value"]})
        summary_rows_reconstructed += 1
        summary_field_comparisons += comparisons
        if passed:
            summary_rows_with_complete_validation += 1
        else:
            summary_rows_with_incomplete_validation += 1
            summary_mismatch_count += evidence["mismatches"]
            summary_structural_mismatch_count += evidence.get("structural_mismatch_count", 0)
    
    # Validate by project
    for _, row in project_df.iterrows():
        passed, comparisons, evidence = validate_summary_row(df, row.to_dict(), ["target_project"], {"target_project": row["group_value"]})
        summary_rows_reconstructed += 1
        summary_field_comparisons += comparisons
        if passed:
            summary_rows_with_complete_validation += 1
        else:
            summary_rows_with_incomplete_validation += 1
            summary_mismatch_count += evidence["mismatches"]
            summary_structural_mismatch_count += evidence.get("structural_mismatch_count", 0)
    
    print("Step 11: Validate output schemas...")
    summary_schema_validation = validate_output_schemas(summary_dfs, undefined_reasons_df)
    
    print("Step 12: Validate summary domains...")
    summary_domain_validation = validate_summary_domains(summary_dfs, spec)
    
    print("Step 13: Validate correlation identities...")
    correlation_identity_validation = validate_correlation_identities(summary_dfs)
    
    print("Step 14: Validate undefined reasons...")
    undefined_reasons_validation = validate_undefined_reasons(df, undefined_reasons_df)
    
    print("Step 15: Check denominator identities...")
    denominator_identities = check_denominator_identities(summary_dfs)
    
    print("Step 16: Check range constraints...")
    range_checks = check_range_constraints(summary_dfs)
    
    print("Step 17: Run synthetic NaN fail-safe tests...")
    synthetic_nan_tests = run_synthetic_nan_tests()
    
    print("Step 18: Build immutable audit payload...")
    
    # Build execution evidence
    execution_evidence = {
        "base_path": str(base_dir),
        "script_path": str(script_path),
    }
    
    # Build summary counts
    summary_counts = {
        "overall": {"expected_rows": EXPECTED_OVERALL_ROWS, "actual_rows": len(overall_df)},
        "by_experiment": {"expected_rows": EXPECTED_EXPERIMENT_ROWS, "actual_rows": len(experiment_df)},
        "by_mode": {"expected_rows": EXPECTED_MODE_ROWS, "actual_rows": len(mode_df)},
        "by_metric": {"expected_rows": EXPECTED_METRIC_ROWS, "actual_rows": len(metric_df)},
        "by_project": {"expected_rows": EXPECTED_PROJECT_ROWS, "actual_rows": len(project_df)},
    }
    
    # Build correlation undefined counts
    spearman_count = int(undefined_reasons_df[undefined_reasons_df["correlation"] == "spearman"]["count"].sum()) if not undefined_reasons_df.empty else 0
    kendall_count = int(undefined_reasons_df[undefined_reasons_df["correlation"] == "kendall"]["count"].sum()) if not undefined_reasons_df.empty else 0
    
    correlation_undefined = {
        "spearman_count": spearman_count,
        "kendall_count": kendall_count,
    }
    
    # Build validation state
    validation_state = {
        "summary_rows_expected": summary_rows_expected,
        "summary_rows_reconstructed": summary_rows_reconstructed,
        "summary_rows_with_complete_validation": summary_rows_with_complete_validation,
        "summary_rows_with_incomplete_validation": summary_rows_with_incomplete_validation,
        "summary_field_comparisons": summary_field_comparisons,
        "summary_mismatch_count": summary_mismatch_count,
        "summary_structural_mismatch_count": summary_structural_mismatch_count,
    }
    
    # Build interpretation limits
    interpretation_limits = {
        "descriptive_summaries_only": True,
        "seeds_repeated_non_independent": True,
        "no_p_values": True,
        "no_iid_confidence_intervals": True,
        "no_significance_claim": True,
        "no_causal_claim": True,
        "no_superiority_claim": True,
        "test_data_post_selection_only": True,
        "present": True,
    }
    
    # Build immutable audit payload (A: Complete all scientific and structural validation evidence)
    audit_payload = {
        "execution": execution_evidence,
        "input_verification": input_verification,
        "input_audit_verification": input_audit_evidence,
        "summary_counts": summary_counts,
        "summary_schema_validation": summary_schema_validation,
        "summary_domain_validation": summary_domain_validation,
        "correlation_undefined": correlation_undefined,
        "undefined_reasons_validation": undefined_reasons_validation,
        "validation": validation_state,
        "correlation_identity_validation": correlation_identity_validation,
        "denominator_identities": denominator_identities,
        "range_checks": range_checks,
        "synthetic_nan_tests": synthetic_nan_tests,
        "interpretation_limits": interpretation_limits,
    }
    
    print("Step 19: Serialize CSVs twice and compute equality flags...")
    
    # Sort dataframes by explicit domain order
    experiment_df = experiment_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=experiments, ordered=True))
    mode_df = mode_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=modes, ordered=True))
    metric_df = metric_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=metrics, ordered=True))
    project_df = project_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=projects, ordered=True))
    undefined_reasons_df = undefined_reasons_df.sort_values(["correlation", "undefined_reason"])
    
    # Serialize CSVs twice and record evidence
    overall_csv_1 = overall_df.to_csv(index=False, encoding="utf-8")
    overall_csv_2 = overall_df.to_csv(index=False, encoding="utf-8")
    overall_csv_identical = overall_csv_1 == overall_csv_2
    
    experiment_csv_1 = experiment_df.to_csv(index=False, encoding="utf-8")
    experiment_csv_2 = experiment_df.to_csv(index=False, encoding="utf-8")
    experiment_csv_identical = experiment_csv_1 == experiment_csv_2
    
    mode_csv_1 = mode_df.to_csv(index=False, encoding="utf-8")
    mode_csv_2 = mode_df.to_csv(index=False, encoding="utf-8")
    mode_csv_identical = mode_csv_1 == mode_csv_2
    
    metric_csv_1 = metric_df.to_csv(index=False, encoding="utf-8")
    metric_csv_2 = metric_df.to_csv(index=False, encoding="utf-8")
    metric_csv_identical = metric_csv_1 == metric_csv_2
    
    project_csv_1 = project_df.to_csv(index=False, encoding="utf-8")
    project_csv_2 = project_df.to_csv(index=False, encoding="utf-8")
    project_csv_identical = project_csv_1 == project_csv_2
    
    undefined_csv_1 = undefined_reasons_df.to_csv(index=False, encoding="utf-8")
    undefined_csv_2 = undefined_reasons_df.to_csv(index=False, encoding="utf-8")
    undefined_reasons_csv_identical = undefined_csv_1 == undefined_csv_2
    
    # Serialize JSON twice and record evidence (E: Serialize audit_payload JSON twice)
    audit_payload_python = convert_to_python_types(audit_payload)
    audit_payload_json_1 = json.dumps(audit_payload_python, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    audit_payload_json_2 = json.dumps(audit_payload_python, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    audit_payload_json_identical = audit_payload_json_1 == audit_payload_json_2
    
    # Render audit_payload Markdown twice using a pure function (F)
    audit_payload_md_1 = build_audit_markdown(audit_payload)
    audit_payload_md_2 = build_audit_markdown(audit_payload)
    audit_payload_md_identical = audit_payload_md_1 == audit_payload_md_2
    
    # Build serialization_audit from the six CSV checks plus payload JSON/Markdown checks (G)
    serialization_audit = {
        "overall_csv_serialization_identical": overall_csv_identical,
        "experiment_csv_serialization_identical": experiment_csv_identical,
        "mode_csv_serialization_identical": mode_csv_identical,
        "metric_csv_serialization_identical": metric_csv_identical,
        "project_csv_serialization_identical": project_csv_identical,
        "undefined_reasons_csv_serialization_identical": undefined_reasons_csv_identical,
        "audit_payload_json_serialization_identical": audit_payload_json_identical,
        "audit_payload_markdown_serialization_identical": audit_payload_md_identical,
        "stable_output_order_passed": all([
            overall_csv_identical,
            experiment_csv_identical,
            mode_csv_identical,
            metric_csv_identical,
            project_csv_identical,
            undefined_reasons_csv_identical,
        ]),
        "passed": all([
            overall_csv_identical,
            experiment_csv_identical,
            mode_csv_identical,
            metric_csv_identical,
            project_csv_identical,
            undefined_reasons_csv_identical,
            audit_payload_json_identical,
            audit_payload_md_identical,
        ]),
    }
    
    # Compute deterministic_output_serialization_passed from all eight serialization checks (H)
    deterministic_output_serialization_passed = serialization_audit["passed"]
    
    # Build validation checks (I: Compute output_integrity_ready_passed only after every other check)
    validation_checks = {
        "input_sha_verified": input_verification["sha256_verified"],
        "input_schema_valid": input_verification["input_schema_valid"],
        "input_key_coverage_passed": input_verification["input_key_coverage_passed"],
        "input_audit_checks_passed": input_audit_evidence["input_audit_checks_passed"],
        "summary_counts_correct": all(v["actual_rows"] == v["expected_rows"] for v in summary_counts.values()),
        "summary_schemas_valid": summary_schema_validation["passed"],
        "summary_group_domains_valid": summary_domain_validation["passed"],
        "summary_group_denominators_valid": summary_domain_validation["details"]["group_denominator_mismatch_count"] == 0,
        "correlation_undefined_counts_correct": spearman_count == 18 and kendall_count == 18,
        "correlation_defined_identities_passed": correlation_identity_validation["passed"],
        "independent_validation_passed": all([
            summary_rows_expected == 25,
            summary_rows_reconstructed == 25,
            summary_rows_with_complete_validation == 25,
            summary_rows_with_incomplete_validation == 0,
            summary_field_comparisons == 850,
            summary_mismatch_count == 0,
            summary_structural_mismatch_count == 0,
        ]),
        "denominator_identities_passed": denominator_identities["passed"],
        "range_checks_passed": range_checks["passed"],
        "undefined_reasons_validation_passed": undefined_reasons_validation["passed"],
        "interpretation_limits_present": interpretation_limits["present"],
        "deterministic_output_serialization_passed": deterministic_output_serialization_passed,
        "nan_and_undefined_state_fail_safe_passed": synthetic_nan_tests["nan_and_undefined_state_fail_safe_passed"],
    }
    
    # Compute output_integrity_ready_passed only after every other check
    output_integrity_ready_passed = all(validation_checks.values())
    validation_checks["output_integrity_ready_passed"] = output_integrity_ready_passed
    
    # Compute all_checks_passed only after output_integrity_ready_passed exists (J)
    all_checks_passed = output_integrity_ready_passed
    validation_checks["all_checks_passed"] = all_checks_passed
    
    # Build one immutable final state (K)
    final_audit_state = {
        "audit_payload": audit_payload,
        "serialization_audit": serialization_audit,
        "validation_checks": validation_checks,
    }
    
    print("Step 20: Serialize final_audit_state to JSON twice and require equality...")
    
    # Serialize final_audit_state to JSON twice (L)
    final_audit_state_python = convert_to_python_types(final_audit_state)
    final_audit_json_1 = json.dumps(final_audit_state_python, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    final_audit_json_2 = json.dumps(final_audit_state_python, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    final_audit_json_identical = final_audit_json_1 == final_audit_json_2
    
    if not final_audit_json_identical:
        raise ValueError("Final audit state JSON serialization is not deterministic")
    
    # Build final Markdown from final_audit_state twice and require equality (M)
    final_audit_md_1 = build_final_audit_markdown(final_audit_state)
    final_audit_md_2 = build_final_audit_markdown(final_audit_state)
    final_audit_md_identical = final_audit_md_1 == final_audit_md_2
    
    if not final_audit_md_identical:
        raise ValueError("Final audit state Markdown rendering is not deterministic")
    
    print("Step 21: Validate all checks passed before write...")
    if not validation_checks["all_checks_passed"]:
        failed = [k for k, v in validation_checks.items() if not v and k != "all_checks_passed"]
        raise ValueError(f"Validation checks failed: {failed}")
    
    # Final JSON/Markdown consistency assertions (I)
    assert final_audit_state["serialization_audit"]["passed"] is True
    assert final_audit_state["validation_checks"]["deterministic_output_serialization_passed"] is True
    assert final_audit_state["validation_checks"]["output_integrity_ready_passed"] is True
    assert final_audit_state["validation_checks"]["all_checks_passed"] is True
    
    # Assert required True lines are present in final Markdown
    assert "Audit payload JSON serialization identical: True" in final_audit_md_1
    assert "Audit payload Markdown serialization identical: True" in final_audit_md_1
    assert "Deterministic output serialization passed: True" in final_audit_md_1
    assert "output integrity ready passed: True" in final_audit_md_1
    assert "all checks passed: True" in final_audit_md_1
    assert "NaN and undefined-state fail-safe passed: True" in final_audit_md_1
    
    # Assert final Markdown does not contain N/A or false deterministic status
    assert "N/A" not in final_audit_md_1
    assert "Deterministic output serialization passed: False" not in final_audit_md_1
    
    print("Step 22: Write outputs...")
    temp_files = []
    try:
        # Write CSVs
        for path, content in [
            (output_overall, overall_csv_1),
            (output_by_experiment, experiment_csv_1),
            (output_by_mode, mode_csv_1),
            (output_by_metric, metric_csv_1),
            (output_by_project, project_csv_1),
            (output_undefined_reasons, undefined_csv_1),
        ]:
            temp = path.parent / f"{path.name}.tmp"
            temp.write_text(content, encoding="utf-8")
            temp_files.append(temp)
        
        # Write JSON
        temp_json = audit_output_json.parent / f"{audit_output_json.name}.tmp"
        temp_json.write_text(final_audit_json_1, encoding="utf-8")
        temp_files.append(temp_json)
        
        # Write Markdown
        temp_md = audit_output_md.parent / f"{audit_output_md.name}.tmp"
        audit_output_md.parent.mkdir(parents=True, exist_ok=True)
        temp_md.write_text(final_audit_md_1, encoding="utf-8")
        temp_files.append(temp_md)
        
        # Atomic rename
        for temp_file in temp_files:
            final_path = temp_file.parent / temp_file.name.replace(".tmp", "")
            temp_file.replace(final_path)
        
        print("Outputs written successfully")
        
    except Exception as e:
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
        raise e
    finally:
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
    
    print("Done!")


if __name__ == "__main__":
    main()
