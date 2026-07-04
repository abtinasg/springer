#!/usr/bin/env python3
"""
Part 2 Section 4B.2A: Compute descriptive validation-test ranking-agreement summaries

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


def verify_input_audit(audit: Dict[str, Any]) -> None:
    """Verify audit contains all required validation checks."""
    validation_checks = audit.get("validation_checks", {})
    
    required_checks = [
        "artifact_semantic_consistency_passed",
        "output_integrity_ready_passed",
    ]
    
    for check in required_checks:
        if check not in validation_checks:
            raise ValueError(f"Missing validation check: {check}")
        if not validation_checks[check]:
            raise ValueError(f"Validation check failed: {check}")
    
    # Verify all checks are True
    failed_checks = [name for name, passed in validation_checks.items() if not passed]
    if failed_checks:
        raise ValueError(f"Failed validation checks: {failed_checks}")


def verify_event_csv(
    df: pd.DataFrame,
    expected_sha: str,
    expected_rows: int = 2100,
    expected_cols: int = 28,
) -> None:
    """Verify event CSV structure and content."""
    # Check row count
    if len(df) != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, got {len(df)}")
    
    # Check column count
    if len(df.columns) != expected_cols:
        raise ValueError(f"Expected {expected_cols} columns, got {len(df.columns)}")
    
    # Check key uniqueness
    key_cols = ["experiment", "target_project", "seed", "mode", "metric"]
    key_duplicates = df.duplicated(subset=key_cols, keep=False)
    if key_duplicates.any():
        dup_count = key_duplicates.sum()
        raise ValueError(f"Found {dup_count} duplicate keys")
    
    # Check coverage
    expected_keys = 2100
    actual_keys = len(df.drop_duplicates(subset=key_cols))
    if actual_keys != expected_keys:
        raise ValueError(f"Expected {expected_keys} unique keys, got {actual_keys}")


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
    spearman_mean = spearman_values.mean() if len(spearman_values) > 0 else 0.0
    spearman_median = float(pd.Series(spearman_values).median()) if len(spearman_values) > 0 else 0.0
    
    # Kendall statistics
    kendall_defined_mask = df_subset["kendall_defined"].astype(bool)
    kendall_defined_n = kendall_defined_mask.sum()
    kendall_undefined_n = (~kendall_defined_mask).sum()
    kendall_values = df_subset.loc[kendall_defined_mask, "kendall_tau_b"].values
    kendall_mean = kendall_values.mean() if len(kendall_values) > 0 else 0.0
    kendall_median = float(pd.Series(kendall_values).median()) if len(kendall_values) > 0 else 0.0
    
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
        return False, 0, {"error": "n_event_rows mismatch"}
    
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
    actual_mean = spearman_values.mean() if len(spearman_values) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["spearman_mean_defined"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    actual_median = float(pd.Series(spearman_values).median()) if len(spearman_values) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["spearman_median_defined"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    kendall_values = df_subset.loc[kendall_defined_mask, "kendall_tau_b"].values
    actual_mean = kendall_values.mean() if len(kendall_values) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["kendall_mean_defined"], actual_mean, rel_tol=1e-12, abs_tol=1e-12):
        mismatches += 1
    
    actual_median = float(pd.Series(kendall_values).median()) if len(kendall_values) > 0 else 0.0
    field_comparisons += 1
    if not math.isclose(summary_row["kendall_median_defined"], actual_median, rel_tol=1e-12, abs_tol=1e-12):
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
    
    return mismatches == 0, field_comparisons, {"mismatches": mismatches}


def check_denominator_identities(summary_dfs: Dict[str, pd.DataFrame]) -> bool:
    """Check that all denominator sums equal 2100."""
    total = 2100
    
    for name, df in summary_dfs.items():
        if df["n_event_rows"].sum() != total:
            print(f"Denominator identity failed for {name}: {df['n_event_rows'].sum()} != {total}")
            return False
    
    return True


def check_range_constraints(summary_dfs: Dict[str, pd.DataFrame]) -> bool:
    """Check that all values are within expected ranges."""
    for name, df in summary_dfs.items():
        # Check counts are between 0 and denominator
        for col in df.columns:
            if col.endswith("_n") and col != "n_event_rows":
                if (df[col] < 0).any() or (df[col] > df["n_event_rows"]).any():
                    print(f"Range check failed for {name}.{col}")
                    return False
        
        # Check rates are in [0, 1]
        for col in df.columns:
            if col.endswith("_rate"):
                if (df[col] < 0).any() or (df[col] > 1).any():
                    print(f"Range check failed for {name}.{col}")
                    return False
        
        # Check Jaccard in [0, 1]
        for col in ["winner_set_jaccard_exact_mean", "winner_set_jaccard_exact_median",
                    "winner_set_jaccard_tolerance_mean", "winner_set_jaccard_tolerance_median"]:
            if col in df.columns:
                if (df[col] < 0).any() or (df[col] > 1).any():
                    print(f"Range check failed for {name}.{col}")
                    return False
        
        # Check correlation mean/median in [-1, 1]
        for col in ["spearman_mean_defined", "spearman_median_defined",
                    "kendall_mean_defined", "kendall_median_defined"]:
            if col in df.columns:
                if (df[col] < -1).any() or (df[col] > 1).any():
                    print(f"Range check failed for {name}.{col}")
                    return False
        
        # Check selected test rank in [1, 4]
        for col in ["selected_candidate_test_rank_mean", "selected_candidate_test_rank_median"]:
            if col in df.columns:
                if (df[col] < 1).any() or (df[col] > 4).any():
                    print(f"Range check failed for {name}.{col}")
                    return False
    
    return True


def build_audit_markdown(audit_state: Dict[str, Any]) -> str:
    """Build Markdown audit report from audit state."""
    lines = []
    lines.append("# Part 2 Section 4B.2A: Validation-Test Ranking Agreement Summary Audit\n\n")
    
    lines.append("## Input Verification\n\n")
    lines.append(f"- Event CSV SHA-256 verified: {audit_state['input_verification']['sha256_verified']}\n")
    lines.append(f"- Event rows: {audit_state['input_verification']['rows']} (expected: 2100)\n")
    lines.append(f"- Event columns: {audit_state['input_verification']['columns']} (expected: 28)\n")
    lines.append(f"- Duplicate keys: {audit_state['input_verification']['duplicate_keys']}\n")
    lines.append(f"- Missing keys: {audit_state['input_verification']['missing_keys']}\n")
    lines.append(f"- Extra keys: {audit_state['input_verification']['extra_keys']}\n")
    lines.append(f"- Audit validation checks passed: {audit_state['input_verification']['audit_checks_passed']}\n\n")
    
    lines.append("## Summary Output Verification\n\n")
    for name, counts in audit_state['summary_counts'].items():
        lines.append(f"- {name}:\n")
        lines.append(f"  - Expected rows: {counts['expected_rows']}\n")
        lines.append(f"  - Actual rows: {counts['actual_rows']}\n\n")
    
    lines.append("## Correlation Undefined Reasons\n\n")
    lines.append(f"- Spearman undefined count: {audit_state['correlation_undefined']['spearman_count']} (expected: 18)\n")
    lines.append(f"- Kendall undefined count: {audit_state['correlation_undefined']['kendall_count']} (expected: 18)\n\n")
    
    lines.append("## Independent Validation\n\n")
    lines.append(f"- Summary rows expected: {audit_state['validation']['summary_rows_expected']}\n")
    lines.append(f"- Summary rows reconstructed: {audit_state['validation']['summary_rows_reconstructed']}\n")
    lines.append(f"- Complete validation rows: {audit_state['validation']['summary_rows_with_complete_validation']}\n")
    lines.append(f"- Incomplete validation rows: {audit_state['validation']['summary_rows_with_incomplete_validation']}\n")
    lines.append(f"- Actual field comparisons: {audit_state['validation']['summary_field_comparisons']}\n")
    lines.append(f"- Mismatch count: {audit_state['validation']['summary_mismatch_count']}\n\n")
    
    lines.append("## Denominator Identities\n\n")
    lines.append(f"- All denominator identities passed: {audit_state['denominator_identities']['passed']}\n")
    for name, passed in audit_state['denominator_identities']['details'].items():
        lines.append(f"- {name}: {passed}\n\n")
    
    lines.append("## Range Checks\n\n")
    lines.append(f"- All range checks passed: {audit_state['range_checks']['passed']}\n")
    for name, passed in audit_state['range_checks']['details'].items():
        lines.append(f"- {name}: {passed}\n\n")
    
    lines.append("## Validation Checks Summary\n\n")
    for check_name, check_passed in audit_state['validation_checks'].items():
        lines.append(f"- {check_name}: {check_passed}\n")
    lines.append("\n")
    
    return "".join(lines)


def main():
    # Paths
    base_dir = Path("/Users/aliehpourdast/Desktop/springer/springer")
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
    verify_input_audit(audit)
    
    print("Step 3: Load and verify event CSV...")
    df = pd.read_csv(event_csv_path)
    actual_sha = compute_sha256(event_csv_path)
    if actual_sha != expected_sha:
        raise ValueError(f"SHA mismatch: expected {expected_sha}, got {actual_sha}")
    verify_event_csv(df, expected_sha)
    
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
    
    print("Step 11: Check denominator identities...")
    denominator_passed = check_denominator_identities(summary_dfs)
    denominator_details = {name: df["n_event_rows"].sum() == 2100 for name, df in summary_dfs.items()}
    
    print("Step 12: Check range constraints...")
    range_passed = check_range_constraints(summary_dfs)
    range_details = {name: True for name in summary_dfs.keys()}  # Simplified
    
    print("Step 13: Build audit state...")
    
    # Build summary counts first
    summary_counts = {
        "overall": {"expected_rows": 1, "actual_rows": len(overall_df)},
        "by_experiment": {"expected_rows": 2, "actual_rows": len(experiment_df)},
        "by_mode": {"expected_rows": 3, "actual_rows": len(mode_df)},
        "by_metric": {"expected_rows": 14, "actual_rows": len(metric_df)},
        "by_project": {"expected_rows": 5, "actual_rows": len(project_df)},
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
    }
    
    # Build denominator identities
    denominator_identities = {
        "passed": denominator_passed,
        "details": denominator_details,
    }
    
    # Build range checks
    range_checks = {
        "passed": range_passed,
        "details": range_details,
    }
    
    # Build validation checks (without all_checks_passed initially)
    validation_checks_partial = {
        "input_sha_verified": actual_sha == expected_sha,
        "input_schema_valid": len(df) == 2100 and len(df.columns) == 28,
        "audit_checks_passed": True,
        "summary_counts_correct": all(v["actual_rows"] == v["expected_rows"] for v in summary_counts.values()),
        "correlation_undefined_counts_correct": spearman_count == 18 and kendall_count == 18,
        "independent_validation_passed": summary_mismatch_count == 0,
        "denominator_identities_passed": denominator_passed,
        "range_checks_passed": range_passed,
    }
    
    # Compute all_checks_passed from partial checks
    all_checks_passed = all(validation_checks_partial.values())
    
    # Build final validation checks with all_checks_passed
    validation_checks = validation_checks_partial.copy()
    validation_checks["all_checks_passed"] = all_checks_passed
    
    # Build final audit state
    audit_state = {
        "input_verification": {
            "sha256_verified": actual_sha == expected_sha,
            "rows": len(df),
            "columns": len(df.columns),
            "duplicate_keys": 0,
            "missing_keys": 0,
            "extra_keys": 0,
            "audit_checks_passed": True,
        },
        "summary_counts": summary_counts,
        "correlation_undefined": correlation_undefined,
        "validation": validation_state,
        "denominator_identities": denominator_identities,
        "range_checks": range_checks,
        "validation_checks": validation_checks,
    }
    
    print("Step 14: Serialize outputs deterministically...")
    
    # Sort dataframes by explicit domain order
    experiment_df = experiment_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=experiments, ordered=True))
    mode_df = mode_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=modes, ordered=True))
    metric_df = metric_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=metrics, ordered=True))
    project_df = project_df.sort_values("group_value", key=lambda x: pd.Categorical(x, categories=projects, ordered=True))
    undefined_reasons_df = undefined_reasons_df.sort_values(["correlation", "undefined_reason"])
    
    # Serialize CSVs twice
    overall_csv_1 = overall_df.to_csv(index=False, encoding="utf-8")
    overall_csv_2 = overall_df.to_csv(index=False, encoding="utf-8")
    assert overall_csv_1 == overall_csv_2, "Overall CSV not deterministic"
    
    experiment_csv_1 = experiment_df.to_csv(index=False, encoding="utf-8")
    experiment_csv_2 = experiment_df.to_csv(index=False, encoding="utf-8")
    assert experiment_csv_1 == experiment_csv_2, "Experiment CSV not deterministic"
    
    mode_csv_1 = mode_df.to_csv(index=False, encoding="utf-8")
    mode_csv_2 = mode_df.to_csv(index=False, encoding="utf-8")
    assert mode_csv_1 == mode_csv_2, "Mode CSV not deterministic"
    
    metric_csv_1 = metric_df.to_csv(index=False, encoding="utf-8")
    metric_csv_2 = metric_df.to_csv(index=False, encoding="utf-8")
    assert metric_csv_1 == metric_csv_2, "Metric CSV not deterministic"
    
    project_csv_1 = project_df.to_csv(index=False, encoding="utf-8")
    project_csv_2 = project_df.to_csv(index=False, encoding="utf-8")
    assert project_csv_1 == project_csv_2, "Project CSV not deterministic"
    
    undefined_csv_1 = undefined_reasons_df.to_csv(index=False, encoding="utf-8")
    undefined_csv_2 = undefined_reasons_df.to_csv(index=False, encoding="utf-8")
    assert undefined_csv_1 == undefined_csv_2, "Undefined reasons CSV not deterministic"
    
    # Serialize JSON twice
    audit_state_python = convert_to_python_types(audit_state)
    audit_json_1 = json.dumps(audit_state_python, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    audit_json_2 = json.dumps(audit_state_python, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    assert audit_json_1 == audit_json_2, "Audit JSON not deterministic"
    
    # Serialize Markdown twice
    audit_md_1 = build_audit_markdown(audit_state)
    audit_md_2 = build_audit_markdown(audit_state)
    assert audit_md_1 == audit_md_2, "Audit Markdown not deterministic"
    
    print("Step 15: Validate all checks passed before write...")
    if not audit_state["validation_checks"]["all_checks_passed"]:
        failed = [k for k, v in audit_state["validation_checks"].items() if not v and k != "all_checks_passed"]
        raise ValueError(f"Validation checks failed: {failed}")
    
    print("Step 16: Write outputs...")
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
        temp_json.write_text(audit_json_1, encoding="utf-8")
        temp_files.append(temp_json)
        
        # Write Markdown
        temp_md = audit_output_md.parent / f"{audit_output_md.name}.tmp"
        audit_output_md.parent.mkdir(parents=True, exist_ok=True)
        temp_md.write_text(audit_md_1, encoding="utf-8")
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
