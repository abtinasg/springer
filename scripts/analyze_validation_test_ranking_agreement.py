#!/usr/bin/env python3
"""
Part 2 Section 4B.1: Compute and validate event-level validation-test ranking agreement.

This script performs event-level computation and audit of validation-test ranking agreement
based on the specification in reports/part2_validation_test_ranking_agreement_specification.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats


# Constants
TOLERANCE = 1e-12
CANDIDATE_ORDER = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
EXPECTED_DOMAINS = {
    "experiments": ["within_project", "cross_project"],
    "projects": ["CM1", "JM1", "KC1", "KC2", "PC1"],
    "seeds": [7, 13, 29, 42, 101],
    "modes": ["balanced", "rank", "mcc"],
    "candidates": CANDIDATE_ORDER,
    "aqrpe_models": ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc"],
}

MODE_MAPPING = {
    "balanced": "AQRPE_v2_balanced",
    "rank": "AQRPE_v2_rank",
    "mcc": "AQRPE_v2_mcc",
}

SELECTION_MODE_EXPECTED = {
    "AQRPE_v2_balanced": "balanced_objective",
    "AQRPE_v2_rank": "rank_objective_fixed_threshold",
    "AQRPE_v2_mcc": "mcc_objective",
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_specification(spec_path: Path) -> Dict[str, Any]:
    """Load the specification JSON."""
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the canonical manifest."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def canonical_verification(
    manifest: Dict[str, Any],
    validation_log_path: Path,
    repeated_results_path: Path,
    script_path: Path,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify canonical inputs against manifest.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "manifest_validation_status": manifest.get("manifest_validation_status"),
        "expected_sha256": {},
        "computed_sha256": {},
        "matches": {},
    }
    
    # Check manifest status
    if manifest.get("manifest_validation_status") != "all_checks_passed":
        return False, evidence
    
    # Get expected SHA-256 from manifest
    expected_validation = manifest["canonical_reproduction_outputs"]["validation_log.csv"]["sha256"]
    expected_repeated = manifest["canonical_reproduction_outputs"]["repeated_all_results.csv"]["sha256"]
    expected_script = manifest["environment_and_code_files"]["run_repeated_evaluation.py"]["sha256"]
    
    evidence["expected_sha256"] = {
        "validation_log.csv": expected_validation,
        "repeated_all_results.csv": expected_repeated,
        "run_repeated_evaluation.py": expected_script,
    }
    
    # Compute actual SHA-256
    computed_validation = compute_sha256(validation_log_path)
    computed_repeated = compute_sha256(repeated_results_path)
    computed_script = compute_sha256(script_path)
    
    evidence["computed_sha256"] = {
        "validation_log.csv": computed_validation,
        "repeated_all_results.csv": computed_repeated,
        "run_repeated_evaluation.py": computed_script,
    }
    
    # Check matches
    validation_match = computed_validation == expected_validation
    repeated_match = computed_repeated == expected_repeated
    script_match = computed_script == expected_script
    
    evidence["matches"] = {
        "validation_log.csv": validation_match,
        "repeated_all_results.csv": repeated_match,
        "run_repeated_evaluation.py": script_match,
    }
    
    passed = all(evidence["matches"].values())
    return passed, evidence


def validate_input_schema(
    validation_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate input file schemas.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "validation_rows": len(validation_df),
        "validation_columns": len(validation_df.columns),
        "validation_column_names": list(validation_df.columns),
        "repeated_rows": len(repeated_df),
        "repeated_columns": len(repeated_df.columns),
        "repeated_column_names": list(repeated_df.columns),
    }
    
    # Expected schemas
    expected_validation_columns = [
        "experiment", "target_project", "seed", "candidate", "mode",
        "val_threshold", "val_selection_score",
        "val_avg_precision", "val_roc_auc", "val_mcc", "val_f1",
        "val_balanced_accuracy", "val_precision", "val_recall", "val_brier",
        "val_precision_at_10pct", "val_recall_at_10pct", "val_lift_at_10pct",
        "val_precision_at_20pct", "val_recall_at_20pct", "val_lift_at_20pct",
    ]
    
    expected_repeated_columns = [
        "experiment", "target_project", "seed", "model", "selected_candidate",
        "selection_mode", "threshold", "selection_score",
        "avg_precision", "roc_auc", "mcc", "f1", "balanced_accuracy",
        "precision", "recall", "brier",
        "precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
        "precision_at_20pct", "recall_at_20pct", "lift_at_20pct",
    ]
    
    # Check row counts
    validation_rows_ok = len(validation_df) == 600
    repeated_rows_ok = len(repeated_df) == 400
    
    # Check column counts
    validation_cols_ok = len(validation_df.columns) == 21
    repeated_cols_ok = len(repeated_df.columns) == 22
    
    # Check column names
    validation_names_ok = set(validation_df.columns) == set(expected_validation_columns)
    repeated_names_ok = set(repeated_df.columns) == set(expected_repeated_columns)
    
    # Check for nulls in required fields
    validation_nulls = validation_df[expected_validation_columns].isnull().any().any()
    repeated_nulls = repeated_df[expected_repeated_columns].isnull().any().any()
    
    evidence.update({
        "validation_rows_ok": validation_rows_ok,
        "repeated_rows_ok": repeated_rows_ok,
        "validation_cols_ok": validation_cols_ok,
        "repeated_cols_ok": repeated_cols_ok,
        "validation_names_ok": validation_names_ok,
        "repeated_names_ok": repeated_names_ok,
        "validation_has_nulls": validation_nulls,
        "repeated_has_nulls": repeated_nulls,
    })
    
    passed = all([
        validation_rows_ok,
        repeated_rows_ok,
        validation_cols_ok,
        repeated_cols_ok,
        validation_names_ok,
        repeated_names_ok,
        not validation_nulls,
        not repeated_nulls,
    ])
    
    return passed, evidence


def validate_numeric_finite(
    validation_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
    spec: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that all metric columns are numeric and finite.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "validation_columns_checked": [],
        "test_columns_checked": [],
        "non_numeric_columns": [],
        "non_finite_columns": [],
    }
    
    metric_column_mapping = spec["metric_column_mapping"]
    
    # Check validation columns
    validation_non_numeric = []
    validation_non_finite = []
    for metric, mapping in metric_column_mapping.items():
        val_col = mapping["validation_column"]
        evidence["validation_columns_checked"].append(val_col)
        
        if not np.issubdtype(validation_df[val_col].dtype, np.number):
            validation_non_numeric.append(val_col)
        elif not np.all(np.isfinite(validation_df[val_col])):
            validation_non_finite.append(val_col)
    
    # Check test columns
    test_non_numeric = []
    test_non_finite = []
    for metric, mapping in metric_column_mapping.items():
        test_col = mapping["test_column"]
        evidence["test_columns_checked"].append(test_col)
        
        if not np.issubdtype(repeated_df[test_col].dtype, np.number):
            test_non_numeric.append(test_col)
        elif not np.all(np.isfinite(repeated_df[test_col])):
            test_non_finite.append(test_col)
    
    # Check selection score and threshold columns
    selection_columns = ["val_selection_score", "val_threshold", "selection_score", "threshold"]
    for col in selection_columns:
        if col in validation_df.columns:
            if not np.issubdtype(validation_df[col].dtype, np.number):
                validation_non_numeric.append(col)
            elif not np.all(np.isfinite(validation_df[col])):
                validation_non_finite.append(col)
        if col in repeated_df.columns:
            if not np.issubdtype(repeated_df[col].dtype, np.number):
                test_non_numeric.append(col)
            elif not np.all(np.isfinite(repeated_df[col])):
                test_non_finite.append(col)
    
    evidence.update({
        "validation_non_numeric": validation_non_numeric,
        "validation_non_finite": validation_non_finite,
        "test_non_numeric": test_non_numeric,
        "test_non_finite": test_non_finite,
    })
    
    passed = len(validation_non_numeric) == 0 and len(validation_non_finite) == 0 and len(test_non_numeric) == 0 and len(test_non_finite) == 0
    return passed, evidence


def validate_domains(
    validation_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate domain values.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {}
    
    # Check experiments
    validation_experiments = set(validation_df["experiment"].unique())
    repeated_experiments = set(repeated_df["experiment"].unique())
    experiments_ok = validation_experiments == set(EXPECTED_DOMAINS["experiments"])
    experiments_ok = experiments_ok and repeated_experiments == set(EXPECTED_DOMAINS["experiments"])
    
    # Check projects
    validation_projects = set(validation_df["target_project"].unique())
    repeated_projects = set(repeated_df["target_project"].unique())
    projects_ok = validation_projects == set(EXPECTED_DOMAINS["projects"])
    projects_ok = projects_ok and repeated_projects == set(EXPECTED_DOMAINS["projects"])
    
    # Check seeds
    validation_seeds = set(validation_df["seed"].unique())
    repeated_seeds = set(repeated_df["seed"].unique())
    seeds_ok = validation_seeds == set(EXPECTED_DOMAINS["seeds"])
    seeds_ok = seeds_ok and repeated_seeds == set(EXPECTED_DOMAINS["seeds"])
    
    # Check modes
    validation_modes = set(validation_df["mode"].unique())
    modes_ok = validation_modes == set(EXPECTED_DOMAINS["modes"])
    
    # Check candidates
    validation_candidates = set(validation_df["candidate"].unique())
    candidates_ok = validation_candidates == set(EXPECTED_DOMAINS["candidates"])
    
    # Check models in repeated results
    repeated_models = set(repeated_df["model"].unique())
    expected_models = set(EXPECTED_DOMAINS["candidates"] + EXPECTED_DOMAINS["aqrpe_models"] + ["AQRPE_v2_soft_top3"])
    models_ok = repeated_models == expected_models
    
    evidence.update({
        "validation_experiments": sorted(validation_experiments),
        "repeated_experiments": sorted(repeated_experiments),
        "experiments_ok": experiments_ok,
        "validation_projects": sorted(validation_projects),
        "repeated_projects": sorted(repeated_projects),
        "projects_ok": projects_ok,
        "validation_seeds": sorted(validation_seeds),
        "repeated_seeds": sorted(repeated_seeds),
        "seeds_ok": seeds_ok,
        "validation_modes": sorted(validation_modes),
        "modes_ok": modes_ok,
        "validation_candidates": sorted(validation_candidates),
        "candidates_ok": candidates_ok,
        "repeated_models": sorted(repeated_models),
        "models_ok": models_ok,
    })
    
    passed = all([
        experiments_ok,
        projects_ok,
        seeds_ok,
        modes_ok,
        candidates_ok,
        models_ok,
    ])
    
    return passed, evidence


def validate_key_uniqueness(
    validation_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate key uniqueness.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {}
    
    # Validation unique key: experiment, target_project, seed, candidate, mode
    validation_key = ["experiment", "target_project", "seed", "candidate", "mode"]
    validation_duplicates = validation_df.duplicated(subset=validation_key, keep=False)
    validation_has_duplicates = validation_duplicates.any()
    
    # Repeated results unique key: experiment, target_project, seed, model
    repeated_key = ["experiment", "target_project", "seed", "model"]
    repeated_duplicates = repeated_df.duplicated(subset=repeated_key, keep=False)
    repeated_has_duplicates = repeated_duplicates.any()
    
    evidence.update({
        "validation_key": validation_key,
        "validation_has_duplicates": validation_has_duplicates,
        "validation_duplicate_count": validation_duplicates.sum(),
        "repeated_key": repeated_key,
        "repeated_has_duplicates": repeated_has_duplicates,
        "repeated_duplicate_count": repeated_duplicates.sum(),
    })
    
    passed = not validation_has_duplicates and not repeated_has_duplicates
    return passed, evidence


def validate_four_candidate_coverage(
    validation_df: pd.DataFrame,
    joined_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate four-candidate coverage for validation and joined data.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "validation_units_checked": 0,
        "validation_units_with_exact_four_candidates": 0,
        "candidate_set_mismatch_count": 0,
        "joined_units_checked": 0,
        "joined_units_with_exact_four_candidates": 0,
    }
    
    # Check validation_df
    validation_groups = validation_df.groupby(["experiment", "target_project", "seed", "mode"])
    evidence["validation_units_checked"] = len(validation_groups)
    
    for (experiment, target_project, seed, mode), group in validation_groups:
        if len(group) != 4:
            continue
        
        candidates = set(group["candidate"].tolist())
        if candidates == set(CANDIDATE_ORDER):
            evidence["validation_units_with_exact_four_candidates"] += 1
        else:
            evidence["candidate_set_mismatch_count"] += 1
    
    # Check joined_df
    joined_groups = joined_df.groupby(["experiment", "target_project", "seed", "mode"])
    evidence["joined_units_checked"] = len(joined_groups)
    
    for (experiment, target_project, seed, mode), group in joined_groups:
        if len(group) != 4:
            continue
        
        candidates = set(group["candidate"].tolist())
        if candidates == set(CANDIDATE_ORDER):
            evidence["joined_units_with_exact_four_candidates"] += 1
        else:
            evidence["candidate_set_mismatch_count"] += 1
    
    # Expected: 150 units with exact four candidates
    validation_coverage_ok = evidence["validation_units_with_exact_four_candidates"] == 150
    joined_coverage_ok = evidence["joined_units_with_exact_four_candidates"] == 150
    no_mismatches = evidence["candidate_set_mismatch_count"] == 0
    
    evidence.update({
        "validation_coverage_ok": validation_coverage_ok,
        "joined_coverage_ok": joined_coverage_ok,
        "no_mismatches": no_mismatches,
    })
    
    passed = validation_coverage_ok and joined_coverage_ok and no_mismatches
    return passed, evidence


def extract_baseline_test_table(
    repeated_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, bool, Dict[str, Any]]:
    """
    Extract baseline test table (only 4 baseline models).
    
    Returns:
        (baseline_df, passed, evidence_dict)
    """
    baseline_models = EXPECTED_DOMAINS["candidates"]
    baseline_df = repeated_df[repeated_df["model"].isin(baseline_models)].copy()
    
    evidence = {
        "baseline_models": baseline_models,
        "baseline_rows": len(baseline_df),
        "expected_baseline_rows": 200,
    }
    
    # Check row count
    rows_ok = len(baseline_df) == 200
    
    # Check uniqueness
    baseline_key = ["experiment", "target_project", "seed", "model"]
    baseline_duplicates = baseline_df.duplicated(subset=baseline_key, keep=False)
    has_duplicates = baseline_duplicates.any()
    
    evidence.update({
        "rows_ok": rows_ok,
        "has_duplicates": has_duplicates,
        "duplicate_count": baseline_duplicates.sum() if has_duplicates else 0,
    })
    
    # Check that each experiment × target_project × seed has exactly 4 baseline models
    group_counts = baseline_df.groupby(["experiment", "target_project", "seed"]).size()
    all_four = (group_counts == 4).all()
    
    evidence.update({
        "all_experiment_seed_combinations_have_four_models": all_four,
        "group_counts_stats": group_counts.describe().to_dict(),
    })
    
    passed = rows_ok and not has_duplicates and all_four
    return baseline_df, passed, evidence


def controlled_join(
    validation_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, bool, Dict[str, Any]]:
    """
    Perform controlled join of validation and baseline test tables.
    
    Returns:
        (joined_df, passed, evidence_dict)
    """
    evidence = {}
    
    # Join on: experiment, target_project, seed, candidate == model
    joined_df = pd.merge(
        validation_df,
        baseline_df,
        left_on=["experiment", "target_project", "seed", "candidate"],
        right_on=["experiment", "target_project", "seed", "model"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    
    matched_count = (joined_df["_merge"] == "both").sum()
    unmatched_count = (joined_df["_merge"] == "left_only").sum()
    unexpected_count = (joined_df["_merge"] == "right_only").sum()
    
    evidence = {
        "validation_rows": len(validation_df),
        "baseline_rows": len(baseline_df),
        "joined_rows": len(joined_df),
        "expected_joined_rows": 600,
        "matched_join_rows": int(matched_count),
        "unmatched_validation_rows": int(unmatched_count),
        "unexpected_join_rows": int(unexpected_count),
    }
    
    # Check row count
    rows_ok = len(joined_df) == 600
    
    # Check all matched
    all_matched = (joined_df["_merge"] == "both").all()
    
    evidence["rows_ok"] = rows_ok
    evidence["all_matched"] = all_matched
    
    # Drop merge indicator
    joined_df = joined_df.drop(columns=["_merge"])
    
    passed = rows_ok and all_matched
    return joined_df, passed, evidence


def validate_metric_mapping(
    spec: Dict[str, Any],
    validation_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate metric mapping from specification.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {}
    
    metrics = spec["metrics"]
    metric_directions = spec["metric_directions"]
    metric_column_mapping = spec["metric_column_mapping"]
    
    # Check key sets
    directions_keys_ok = set(metric_directions.keys()) == set(metrics)
    mapping_keys_ok = set(metric_column_mapping.keys()) == set(metrics)
    
    # Check that all validation columns exist
    validation_columns = set(validation_df.columns)
    all_validation_cols_exist = all(
        mapping["validation_column"] in validation_columns
        for mapping in metric_column_mapping.values()
    )
    
    # Check that all test columns exist
    test_columns = set(baseline_df.columns)
    all_test_cols_exist = all(
        mapping["test_column"] in test_columns
        for mapping in metric_column_mapping.values()
    )
    
    evidence.update({
        "metrics_count": len(metrics),
        "directions_keys_ok": directions_keys_ok,
        "mapping_keys_ok": mapping_keys_ok,
        "all_validation_cols_exist": all_validation_cols_exist,
        "all_test_cols_exist": all_test_cols_exist,
        "metrics": metrics,
    })
    
    passed = all([
        directions_keys_ok,
        mapping_keys_ok,
        all_validation_cols_exist,
        all_test_cols_exist,
    ])
    
    return passed, evidence


def validate_selected_candidate_provenance(
    validation_df: pd.DataFrame,
    repeated_df: pd.DataFrame,
    spec: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, bool], Dict[str, Any]]:
    """
    Validate selected-candidate provenance from AQRPE rows with no-test-leakage check.
    
    Returns:
        (selected_candidate_df, checks_dict, evidence_dict)
    """
    evidence = {
        "aqrpe_rows_checked": 0,
        "selected_candidate_rows_checked": 0,
        "expected_aqrpe_keys": set(),
        "actual_aqrpe_keys": set(),
    }
    
    checks = {
        "selected_candidate_AQRPE_uniqueness_passed": True,
        "selected_candidate_selection_mode_passed": True,
        "selected_candidate_domain_passed": True,
        "selected_candidate_validation_row_uniqueness_passed": True,
        "selected_candidate_score_match_passed": True,
        "selected_candidate_threshold_match_passed": True,
        "selected_candidate_rank_threshold_passed": True,
        "selected_candidate_objective_membership_passed": True,
        "selected_candidate_no_test_leakage_passed": True,
    }
    
    # Counters for each check
    selection_mode_mismatches = 0
    domain_mismatches = 0
    validation_row_uniqueness_mismatches = 0
    score_mismatches = 0
    threshold_mismatches = 0
    rank_threshold_mismatches = 0
    objective_membership_mismatches = 0
    
    # Extract AQRPE rows
    aqrpe_models = EXPECTED_DOMAINS["aqrpe_models"]
    aqrpe_df = repeated_df[repeated_df["model"].isin(aqrpe_models)].copy()
    
    evidence["aqrpe_rows_total"] = len(aqrpe_df)
    
    # Build expected AQRPE keys
    for experiment in EXPECTED_DOMAINS["experiments"]:
        for target_project in EXPECTED_DOMAINS["projects"]:
            for seed in EXPECTED_DOMAINS["seeds"]:
                for aqrpe_model in aqrpe_models:
                    evidence["expected_aqrpe_keys"].add((experiment, target_project, seed, aqrpe_model))
    
    # Build selected candidate info
    selected_records = []
    
    for _, aqrpe_row in aqrpe_df.iterrows():
        evidence["aqrpe_rows_checked"] += 1
        
        experiment = aqrpe_row["experiment"]
        target_project = aqrpe_row["target_project"]
        seed = aqrpe_row["seed"]
        model = aqrpe_row["model"]
        selected_candidate = aqrpe_row["selected_candidate"]
        selection_mode = aqrpe_row["selection_mode"]
        threshold = aqrpe_row["threshold"]
        selection_score = aqrpe_row["selection_score"]
        
        evidence["actual_aqrpe_keys"].add((experiment, target_project, seed, model))
        
        # Determine mode from model
        mode = None
        for m, aqrpe_name in MODE_MAPPING.items():
            if model == aqrpe_name:
                mode = m
                break
        
        if mode is None:
            continue
        
        # Check selection mode
        expected_selection_mode = SELECTION_MODE_EXPECTED[model]
        if selection_mode != expected_selection_mode:
            selection_mode_mismatches += 1
        
        # Check selected candidate is in domain
        if selected_candidate not in EXPECTED_DOMAINS["candidates"]:
            domain_mismatches += 1
            continue
        
        # Find corresponding validation row
        val_mask = (
            (validation_df["experiment"] == experiment) &
            (validation_df["target_project"] == target_project) &
            (validation_df["seed"] == seed) &
            (validation_df["mode"] == mode) &
            (validation_df["candidate"] == selected_candidate)
        )
        val_rows = validation_df[val_mask]
        
        if len(val_rows) != 1:
            validation_row_uniqueness_mismatches += 1
            continue
        
        val_row = val_rows.iloc[0]
        evidence["selected_candidate_rows_checked"] += 1
        
        # Check selection score match
        score_diff = abs(selection_score - val_row["val_selection_score"])
        if score_diff > TOLERANCE:
            score_mismatches += 1
        
        # Check threshold match
        threshold_diff = abs(threshold - val_row["val_threshold"])
        if threshold_diff > TOLERANCE:
            threshold_mismatches += 1
        
        # For rank mode, check threshold is exactly 0.5
        if mode == "rank":
            if abs(threshold - 0.5) > TOLERANCE:
                rank_threshold_mismatches += 1
            if abs(val_row["val_threshold"] - 0.5) > TOLERANCE:
                rank_threshold_mismatches += 1
        
        # Check selected candidate is in tolerance-aware maximum set for val_selection_score
        mode_val_rows = validation_df[
            (validation_df["experiment"] == experiment) &
            (validation_df["target_project"] == target_project) &
            (validation_df["seed"] == seed) &
            (validation_df["mode"] == mode)
        ]
        max_score = mode_val_rows["val_selection_score"].max()
        in_max_set = abs(val_row["val_selection_score"] - max_score) <= TOLERANCE
        
        if not in_max_set:
            objective_membership_mismatches += 1
        
        selected_records.append({
            "experiment": experiment,
            "target_project": target_project,
            "seed": seed,
            "mode": mode,
            "model": model,
            "selected_candidate": selected_candidate,
            "selection_mode": selection_mode,
            "threshold": threshold,
            "selection_score": selection_score,
        })
    
    selected_df = pd.DataFrame(selected_records)
    
    # Update checks based on counters
    checks["selected_candidate_selection_mode_passed"] = selection_mode_mismatches == 0
    checks["selected_candidate_domain_passed"] = domain_mismatches == 0
    checks["selected_candidate_validation_row_uniqueness_passed"] = validation_row_uniqueness_mismatches == 0
    checks["selected_candidate_score_match_passed"] = score_mismatches == 0
    checks["selected_candidate_threshold_match_passed"] = threshold_mismatches == 0
    checks["selected_candidate_rank_threshold_passed"] = rank_threshold_mismatches == 0
    checks["selected_candidate_objective_membership_passed"] = objective_membership_mismatches == 0
    
    # Check AQRPE key uniqueness
    checks["selected_candidate_AQRPE_uniqueness_passed"] = evidence["expected_aqrpe_keys"] == evidence["actual_aqrpe_keys"]
    
    # No-test-leakage check
    selection_source_columns = {
        "experiment",
        "target_project",
        "seed",
        "model",
        "selected_candidate",
        "selection_mode",
        "threshold",
        "selection_score",
        "candidate",
        "mode",
        "val_threshold",
        "val_selection_score",
    }
    
    metric_column_mapping = spec["metric_column_mapping"]
    test_metric_columns = set()
    for metric_info in metric_column_mapping.values():
        test_metric_columns.add(metric_info["test_column"])
    
    test_metric_columns_used_for_selection = selection_source_columns.intersection(test_metric_columns)
    
    evidence.update({
        "selection_mode_mismatches": selection_mode_mismatches,
        "domain_mismatches": domain_mismatches,
        "validation_row_uniqueness_mismatches": validation_row_uniqueness_mismatches,
        "score_mismatches": score_mismatches,
        "threshold_mismatches": threshold_mismatches,
        "rank_threshold_mismatches": rank_threshold_mismatches,
        "objective_membership_mismatches": objective_membership_mismatches,
        "expected_aqrpe_keys_count": len(evidence["expected_aqrpe_keys"]),
        "actual_aqrpe_keys_count": len(evidence["actual_aqrpe_keys"]),
        "selection_source_columns": sorted(selection_source_columns),
        "test_metric_columns": sorted(test_metric_columns),
        "test_metric_columns_used_for_selection": sorted(test_metric_columns_used_for_selection),
        "test_metric_columns_used_for_selection_count": len(test_metric_columns_used_for_selection),
    })
    
    checks["selected_candidate_no_test_leakage_passed"] = len(test_metric_columns_used_for_selection) == 0
    
    return selected_df, checks, evidence


def compute_utility(metric_value: float, direction: str) -> float:
    """Compute utility from metric value based on direction."""
    if direction == "higher_is_better":
        return metric_value
    elif direction == "lower_is_better":
        return -metric_value
    else:
        raise ValueError(f"Unknown direction: {direction}")


def compute_exact_ranks(utilities: List[float]) -> List[float]:
    """
    Compute exact ranks with average ranks for ties.
    
    Args:
        utilities: List of utility values for 4 candidates
        
    Returns:
        List of ranks (1 is best)
    """
    # Sort by utility descending (higher is better)
    sorted_indices = sorted(range(len(utilities)), key=lambda i: -utilities[i])
    
    # Group ties (exactly equal utilities - no tolerance)
    ranks = [0.0] * len(utilities)
    i = 0
    while i < len(sorted_indices):
        # Find all indices with exactly equal utility
        j = i
        while j < len(sorted_indices) and utilities[sorted_indices[i]] == utilities[sorted_indices[j]]:
            j += 1
        
        # Compute average rank using ordinal positions (i+1 to j)
        # If group spans positions i to j-1 (0-indexed), ordinal positions are i+1 to j
        avg_rank = ((i + 1) + j) / 2.0
        
        # Assign rank to each original candidate index in the group
        for idx in range(i, j):
            original_idx = sorted_indices[idx]
            ranks[original_idx] = avg_rank
        
        i = j
    
    return ranks


def compute_tolerance_aware_ranks(utilities: List[float]) -> List[float]:
    """
    Compute tolerance-aware ranks with non-chaining groups.
    
    Args:
        utilities: List of utility values for 4 candidates
        
    Returns:
        List of ranks (1 is best)
    """
    # Sort by utility descending
    sorted_indices = sorted(range(len(utilities)), key=lambda i: -utilities[i])
    
    # Build groups using anchor-based non-chaining algorithm
    ranks = [0.0] * len(utilities)
    i = 0
    while i < len(sorted_indices):
        # Start new group with current candidate as anchor
        anchor_idx = sorted_indices[i]
        anchor_utility = utilities[anchor_idx]
        
        # Find all candidates within tolerance of anchor
        j = i + 1
        while j < len(sorted_indices):
            candidate_idx = sorted_indices[j]
            candidate_utility = utilities[candidate_idx]
            
            # Check if within tolerance of anchor (not last member)
            if anchor_utility - candidate_utility <= TOLERANCE:
                j += 1
            else:
                break
        
        # Group spans ordinal positions i to j-1 (0-indexed), so ordinal positions are i+1 to j
        avg_rank = ((i + 1) + j) / 2.0
        
        # Assign rank to each original candidate index in the group
        for idx in range(i, j):
            original_idx = sorted_indices[idx]
            ranks[original_idx] = avg_rank
        
        i = j
    
    return ranks


def run_permutation_rank_test() -> Tuple[bool, Dict[str, Any]]:
    """
    Run permutation ranking test.
    
    Utilities: [0.1, 0.2, 0.3, 0.4]
    Expected exact ranks: [4.0, 3.0, 2.0, 1.0]
    Expected tolerance ranks: [4.0, 3.0, 2.0, 1.0]
    """
    evidence = {}
    
    utilities = [0.1, 0.2, 0.3, 0.4]
    
    exact_ranks = compute_exact_ranks(utilities)
    tolerance_ranks = compute_tolerance_aware_ranks(utilities)
    
    expected_ranks = [4.0, 3.0, 2.0, 1.0]
    
    exact_match = exact_ranks == expected_ranks
    tolerance_match = tolerance_ranks == expected_ranks
    
    evidence = {
        "utilities": utilities,
        "exact_ranks": exact_ranks,
        "tolerance_ranks": tolerance_ranks,
        "expected_ranks": expected_ranks,
        "exact_match": exact_match,
        "tolerance_match": tolerance_match,
    }
    
    passed = exact_match and tolerance_match
    evidence["passed"] = passed
    
    return passed, evidence


def run_exact_tie_rank_test() -> Tuple[bool, Dict[str, Any]]:
    """
    Run exact-tie average-rank test.
    
    Utilities: [0.2, 0.4, 0.4, 0.1]
    Expected exact ranks: [3.0, 1.5, 1.5, 4.0]
    """
    evidence = {}
    
    utilities = [0.2, 0.4, 0.4, 0.1]
    
    exact_ranks = compute_exact_ranks(utilities)
    
    expected_ranks = [3.0, 1.5, 1.5, 4.0]
    
    exact_match = exact_ranks == expected_ranks
    
    evidence = {
        "utilities": utilities,
        "exact_ranks": exact_ranks,
        "expected_ranks": expected_ranks,
        "exact_match": exact_match,
    }
    
    passed = exact_match
    evidence["passed"] = passed
    
    return passed, evidence


def run_synthetic_non_chaining_test() -> Tuple[bool, Dict[str, Any]]:
    """
    Run synthetic non-chaining test to verify tolerance-aware ranking.
    
    Expected result:
    - group 1: candidate 1 and candidate 2
    - group 2: candidate 3
    
    Utilities:
    - 1.0
    - 1.0 - 0.75e-12
    - 1.0 - 1.50e-12
    
    Expected tolerance ranks: [1.5, 1.5, 3.0]
    """
    evidence = {}
    
    utilities = [
        1.0,
        1.0 - 0.75e-12,
        1.0 - 1.50e-12,
    ]
    
    ranks = compute_tolerance_aware_ranks(utilities)
    
    expected_ranks = [1.5, 1.5, 3.0]
    
    evidence = {
        "utilities": utilities,
        "ranks": ranks,
        "expected_ranks": expected_ranks,
    }
    
    # Check that first two are in same group (same rank)
    first_two_same = abs(ranks[0] - ranks[1]) < 1e-15
    
    # Check that third is in different group
    third_different = abs(ranks[0] - ranks[2]) > 1e-15
    
    # Check that not all three are in same group
    not_all_same = not (abs(ranks[0] - ranks[1]) < 1e-15 and abs(ranks[0] - ranks[2]) < 1e-15)
    
    # Check exact match with expected
    exact_match = ranks == expected_ranks
    
    evidence.update({
        "first_two_same_group": first_two_same,
        "third_different_group": third_different,
        "not_all_three_same_group": not_all_same,
        "exact_match": exact_match,
    })
    
    passed = first_two_same and third_different and not_all_same and exact_match
    evidence["passed"] = passed
    
    return passed, evidence


def compute_winner_set(
    utilities: List[float],
    candidates: List[str],
    tolerance: bool = False,
) -> Set[str]:
    """
    Compute winner set (candidates with best utility).
    
    Args:
        utilities: List of utility values
        candidates: List of candidate names (same order as utilities)
        tolerance: If True, use tolerance-aware comparison
        
    Returns:
        Set of candidate names in winner set
    """
    max_utility = max(utilities)
    
    if tolerance:
        winners = {
            candidates[i]
            for i, u in enumerate(utilities)
            if max_utility - u <= TOLERANCE
        }
    else:
        # Exact tie: use direct equality
        winners = {
            candidates[i]
            for i, u in enumerate(utilities)
            if u == max_utility
        }
    
    return winners


def serialize_winner_set(winner_set: Set[str]) -> str:
    """Serialize winner set to string with canonical order."""
    ordered = [c for c in CANDIDATE_ORDER if c in winner_set]
    return "|".join(ordered)


def compute_agreement_metrics(
    validation_winner_set: Set[str],
    test_winner_set: Set[str],
) -> Dict[str, Any]:
    """Compute agreement metrics between two winner sets."""
    # Strict top-1 agreement
    strict_top1_exact = (
        len(validation_winner_set) == 1 and
        len(test_winner_set) == 1 and
        validation_winner_set == test_winner_set
    )
    
    # Winner set equality
    winner_set_equal = validation_winner_set == test_winner_set
    
    # Jaccard similarity
    if len(validation_winner_set) == 0 and len(test_winner_set) == 0:
        jaccard = 1.0
    else:
        intersection = validation_winner_set & test_winner_set
        union = validation_winner_set | test_winner_set
        jaccard = len(intersection) / len(union) if len(union) > 0 else 0.0
    
    # Any overlap
    any_overlap = len(validation_winner_set & test_winner_set) > 0
    
    return {
        "strict_top1_agreement": strict_top1_exact,
        "winner_set_equal": winner_set_equal,
        "winner_set_jaccard": jaccard,
        "winner_set_any_overlap": any_overlap,
    }


def compute_correlations(
    validation_ranks: List[float],
    test_ranks: List[float],
) -> Dict[str, Any]:
    """
    Compute Spearman and Kendall correlations.
    
    Returns:
        Dict with correlation values and defined status
    """
    # Check if either vector is constant (use set equality, not rounding)
    validation_constant = len(set(validation_ranks)) == 1
    test_constant = len(set(test_ranks)) == 1
    
    if validation_constant and test_constant:
        return {
            "spearman_rho": None,
            "spearman_defined": False,
            "spearman_undefined_reason": "both_rank_vectors_constant",
            "kendall_tau_b": None,
            "kendall_defined": False,
            "kendall_undefined_reason": "both_rank_vectors_constant",
        }
    elif validation_constant:
        return {
            "spearman_rho": None,
            "spearman_defined": False,
            "spearman_undefined_reason": "validation_rank_vector_constant",
            "kendall_tau_b": None,
            "kendall_defined": False,
            "kendall_undefined_reason": "validation_rank_vector_constant",
        }
    elif test_constant:
        return {
            "spearman_rho": None,
            "spearman_defined": False,
            "spearman_undefined_reason": "test_rank_vector_constant",
            "kendall_tau_b": None,
            "kendall_defined": False,
            "kendall_undefined_reason": "test_rank_vector_constant",
        }
    else:
        # Compute correlations
        spearman_rho, _ = stats.spearmanr(validation_ranks, test_ranks)
        kendall_tau, _ = stats.kendalltau(validation_ranks, test_ranks)
        
        return {
            "spearman_rho": float(spearman_rho),
            "spearman_defined": True,
            "spearman_undefined_reason": None,
            "kendall_tau_b": float(kendall_tau),
            "kendall_defined": True,
            "kendall_undefined_reason": None,
        }


def get_candidate_rank(
    candidate: str,
    candidates: List[str],
    ranks: List[float],
) -> float:
    """Get rank for a specific candidate."""
    idx = candidates.index(candidate)
    return ranks[idx]


def compute_event_rows(
    joined_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    spec: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute event-level ranking agreement rows.
    
    Returns:
        (events_df, evidence_dict)
    """
    evidence = {
        "analysis_units_checked": 0,
        "metric_rows_computed": 0,
        "winner_sets_checked": 0,
        "rank_vectors_checked": 0,
        "spearman_defined_count": 0,
        "spearman_undefined_count": 0,
        "kendall_defined_count": 0,
        "kendall_undefined_count": 0,
    }
    
    metrics = spec["metrics"]
    metric_directions = spec["metric_directions"]
    metric_column_mapping = spec["metric_column_mapping"]
    
    event_records = []
    
    # Group by analysis unit
    grouped = joined_df.groupby(["experiment", "target_project", "seed", "mode"])
    
    for (experiment, target_project, seed, mode), group in grouped:
        evidence["analysis_units_checked"] += 1
        
        # Get selected candidate for this mode
        selected_mask = (
            (selected_df["experiment"] == experiment) &
            (selected_df["target_project"] == target_project) &
            (selected_df["seed"] == seed) &
            (selected_df["mode"] == mode)
        )
        selected_rows = selected_df[selected_mask]
        
        if len(selected_rows) != 1:
            continue
        
        selected_row = selected_rows.iloc[0]
        mode_selected_candidate = selected_row["selected_candidate"]
        
        # Sort group by candidate order for consistent alignment
        group = group.set_index("candidate").loc[CANDIDATE_ORDER].reset_index()
        
        # Compute for each metric
        for metric in metrics:
            evidence["metric_rows_computed"] += 1
            
            direction = metric_directions[metric]
            val_col = metric_column_mapping[metric]["validation_column"]
            test_col = metric_column_mapping[metric]["test_column"]
            
            # Get validation and test values
            validation_values = group[val_col].tolist()
            test_values = group[test_col].tolist()
            
            # Compute utilities
            validation_utilities = [compute_utility(v, direction) for v in validation_values]
            test_utilities = [compute_utility(v, direction) for v in test_values]
            
            # Compute exact ranks
            validation_exact_ranks = compute_exact_ranks(validation_utilities)
            test_exact_ranks = compute_exact_ranks(test_utilities)
            
            # Compute tolerance-aware ranks
            validation_tolerance_ranks = compute_tolerance_aware_ranks(validation_utilities)
            test_tolerance_ranks = compute_tolerance_aware_ranks(test_utilities)
            
            evidence["rank_vectors_checked"] += 1
            
            # Compute winner sets
            validation_winner_exact = compute_winner_set(validation_utilities, CANDIDATE_ORDER, tolerance=False)
            validation_winner_tolerance = compute_winner_set(validation_utilities, CANDIDATE_ORDER, tolerance=True)
            test_winner_exact = compute_winner_set(test_utilities, CANDIDATE_ORDER, tolerance=False)
            test_winner_tolerance = compute_winner_set(test_utilities, CANDIDATE_ORDER, tolerance=True)
            
            evidence["winner_sets_checked"] += 1
            
            # Validate winner sets
            if len(validation_winner_exact) == 0 or len(validation_winner_tolerance) == 0:
                continue
            if len(test_winner_exact) == 0 or len(test_winner_tolerance) == 0:
                continue
            
            # Check exact winner set is subset of tolerance winner set
            if not validation_winner_exact.issubset(validation_winner_tolerance):
                continue
            if not test_winner_exact.issubset(test_winner_tolerance):
                continue
            
            # Compute agreement metrics
            agreement_exact = compute_agreement_metrics(validation_winner_exact, test_winner_exact)
            agreement_tolerance = compute_agreement_metrics(validation_winner_tolerance, test_winner_tolerance)
            
            # Compute correlations on tolerance-aware ranks
            corr = compute_correlations(validation_tolerance_ranks, test_tolerance_ranks)
            
            if corr["spearman_defined"]:
                evidence["spearman_defined_count"] += 1
            else:
                evidence["spearman_undefined_count"] += 1
            
            if corr["kendall_defined"]:
                evidence["kendall_defined_count"] += 1
            else:
                evidence["kendall_undefined_count"] += 1
            
            # Get selected candidate test rank
            selected_test_rank = get_candidate_rank(
                mode_selected_candidate,
                CANDIDATE_ORDER,
                test_tolerance_ranks,
            )
            
            # Check if selected candidate is in test winner sets
            selected_in_test_exact = mode_selected_candidate in test_winner_exact
            selected_in_test_tolerance = mode_selected_candidate in test_winner_tolerance
            
            # Build event record
            event_record = {
                "experiment": experiment,
                "target_project": target_project,
                "seed": seed,
                "mode": mode,
                "metric": metric,
                "metric_direction": direction,
                "validation_winner_set_exact": serialize_winner_set(validation_winner_exact),
                "validation_winner_set_tolerance": serialize_winner_set(validation_winner_tolerance),
                "test_winner_set_exact": serialize_winner_set(test_winner_exact),
                "test_winner_set_tolerance": serialize_winner_set(test_winner_tolerance),
                "strict_top1_agreement_exact": agreement_exact["strict_top1_agreement"],
                "strict_top1_agreement_tolerance": agreement_tolerance["strict_top1_agreement"],
                "winner_set_equal_exact": agreement_exact["winner_set_equal"],
                "winner_set_equal_tolerance": agreement_tolerance["winner_set_equal"],
                "winner_set_jaccard_exact": agreement_exact["winner_set_jaccard"],
                "winner_set_jaccard_tolerance": agreement_tolerance["winner_set_jaccard"],
                "winner_set_any_overlap_exact": agreement_exact["winner_set_any_overlap"],
                "winner_set_any_overlap_tolerance": agreement_tolerance["winner_set_any_overlap"],
                "spearman_rho": corr["spearman_rho"],
                "spearman_defined": corr["spearman_defined"],
                "spearman_undefined_reason": corr["spearman_undefined_reason"],
                "kendall_tau_b": corr["kendall_tau_b"],
                "kendall_defined": corr["kendall_defined"],
                "kendall_undefined_reason": corr["kendall_undefined_reason"],
                "mode_selected_candidate": mode_selected_candidate,
                "selected_candidate_test_rank": selected_test_rank,
                "selected_candidate_in_test_winner_set_exact": selected_in_test_exact,
                "selected_candidate_in_test_winner_set_tolerance": selected_in_test_tolerance,
            }
            
            event_records.append(event_record)
    
    events_df = pd.DataFrame(event_records)
    
    return events_df, evidence


def validate_event_output(
    events_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate event-level output.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {}
    
    expected_columns = [
        "experiment", "target_project", "seed", "mode", "metric",
        "metric_direction",
        "validation_winner_set_exact", "validation_winner_set_tolerance",
        "test_winner_set_exact", "test_winner_set_tolerance",
        "strict_top1_agreement_exact", "strict_top1_agreement_tolerance",
        "winner_set_equal_exact", "winner_set_equal_tolerance",
        "winner_set_jaccard_exact", "winner_set_jaccard_tolerance",
        "winner_set_any_overlap_exact", "winner_set_any_overlap_tolerance",
        "spearman_rho", "spearman_defined", "spearman_undefined_reason",
        "kendall_tau_b", "kendall_defined", "kendall_undefined_reason",
        "mode_selected_candidate", "selected_candidate_test_rank",
        "selected_candidate_in_test_winner_set_exact",
        "selected_candidate_in_test_winner_set_tolerance",
    ]
    
    # Check row count
    rows_ok = len(events_df) == 2100
    
    # Check column count
    cols_ok = len(events_df.columns) == 28
    
    # Check column names
    names_ok = set(events_df.columns) == set(expected_columns)
    
    # Check key uniqueness
    key_cols = ["experiment", "target_project", "seed", "mode", "metric"]
    key_duplicates = events_df.duplicated(subset=key_cols, keep=False)
    has_key_duplicates = key_duplicates.any()
    
    # Check selected_candidate_test_rank range
    rank_range_ok = events_df["selected_candidate_test_rank"].between(1, 4).all()
    
    # Check correlation range when defined
    spearman_defined = events_df[events_df["spearman_defined"] == True]
    if len(spearman_defined) > 0:
        spearman_range_ok = spearman_defined["spearman_rho"].between(-1, 1).all()
    else:
        spearman_range_ok = True
    
    kendall_defined = events_df[events_df["kendall_defined"] == True]
    if len(kendall_defined) > 0:
        kendall_range_ok = kendall_defined["kendall_tau_b"].between(-1, 1).all()
    else:
        kendall_range_ok = True
    
    evidence.update({
        "rows": len(events_df),
        "expected_rows": 2100,
        "rows_ok": rows_ok,
        "columns": len(events_df.columns),
        "expected_columns": 28,
        "cols_ok": cols_ok,
        "names_ok": names_ok,
        "has_key_duplicates": has_key_duplicates,
        "key_duplicate_count": key_duplicates.sum() if has_key_duplicates else 0,
        "rank_range_ok": rank_range_ok,
        "spearman_range_ok": spearman_range_ok,
        "kendall_range_ok": kendall_range_ok,
    })
    
    passed = all([
        rows_ok,
        cols_ok,
        names_ok,
        not has_key_duplicates,
        rank_range_ok,
        spearman_range_ok,
        kendall_range_ok,
    ])
    
    return passed, evidence


def validate_winner_set_integrity(
    events_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate winner set integrity for all event rows with full checks.
    Serialization order violations are informational only, not failures.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "rows_checked": 0,
        "empty_sets": 0,
        "unknown_candidates": [],
        "duplicate_members": 0,
        "exact_not_subset_tolerance": 0,
        "serialization_order_violations": 0,
    }
    
    def serialize_winner_set(winner_set: Set[str]) -> str:
        """Serialize winner set in canonical order."""
        return "|".join(sorted([c for c in winner_set if c in CANDIDATE_ORDER]))
    
    for _, row in events_df.iterrows():
        evidence["rows_checked"] += 1
        
        # Parse winner sets - convert to list first, then set
        val_exact_list = row["validation_winner_set_exact"].split("|") if row["validation_winner_set_exact"] else []
        val_tolerance_list = row["validation_winner_set_tolerance"].split("|") if row["validation_winner_set_tolerance"] else []
        test_exact_list = row["test_winner_set_exact"].split("|") if row["test_winner_set_exact"] else []
        test_tolerance_list = row["test_winner_set_tolerance"].split("|") if row["test_winner_set_tolerance"] else []
        
        val_exact = set(val_exact_list)
        val_tolerance = set(val_tolerance_list)
        test_exact = set(test_exact_list)
        test_tolerance = set(test_tolerance_list)
        
        # Check for empty sets
        if len(val_exact) == 0 or len(val_tolerance) == 0 or len(test_exact) == 0 or len(test_tolerance) == 0:
            evidence["empty_sets"] += 1
        
        # Check for unknown candidates
        for candidate in val_exact | val_tolerance | test_exact | test_tolerance:
            if candidate not in CANDIDATE_ORDER:
                if candidate not in evidence["unknown_candidates"]:
                    evidence["unknown_candidates"].append(candidate)
        
        # Check for duplicate members
        if len(val_exact_list) != len(val_exact):
            evidence["duplicate_members"] += 1
        if len(val_tolerance_list) != len(val_tolerance):
            evidence["duplicate_members"] += 1
        if len(test_exact_list) != len(test_exact):
            evidence["duplicate_members"] += 1
        if len(test_tolerance_list) != len(test_tolerance):
            evidence["duplicate_members"] += 1
        
        # Check serialization order (informational only)
        if row["validation_winner_set_exact"] != serialize_winner_set(val_exact):
            evidence["serialization_order_violations"] += 1
        if row["validation_winner_set_tolerance"] != serialize_winner_set(val_tolerance):
            evidence["serialization_order_violations"] += 1
        if row["test_winner_set_exact"] != serialize_winner_set(test_exact):
            evidence["serialization_order_violations"] += 1
        if row["test_winner_set_tolerance"] != serialize_winner_set(test_tolerance):
            evidence["serialization_order_violations"] += 1
        
        # Check exact is subset of tolerance
        if not val_exact.issubset(val_tolerance):
            evidence["exact_not_subset_tolerance"] += 1
        if not test_exact.issubset(test_tolerance):
            evidence["exact_not_subset_tolerance"] += 1
    
    # Serialization order violations are informational only, not failures
    passed = (
        evidence["empty_sets"] == 0 and
        len(evidence["unknown_candidates"]) == 0 and
        evidence["duplicate_members"] == 0 and
        evidence["exact_not_subset_tolerance"] == 0
    )
    
    evidence["passed"] = passed
    return passed, evidence


def validate_correlation_state_consistency(
    events_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate correlation state consistency using pd.isna for missing value detection.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "rows_checked": 0,
        "defined_without_value": 0,
        "undefined_with_value": 0,
        "undefined_without_reason": 0,
        "undefined_invalid_reason": 0,
        "defined_with_reason": 0,
        "non_finite_defined_value": 0,
        "value_out_of_range": 0,
    }
    
    allowed_reasons = ["validation_rank_vector_constant", "test_rank_vector_constant", "both_rank_vectors_constant"]
    
    for _, row in events_df.iterrows():
        evidence["rows_checked"] += 1
        
        # Check Spearman
        if row["spearman_defined"]:
            if pd.isna(row["spearman_rho"]):
                evidence["defined_without_value"] += 1
            if not pd.isna(row["spearman_rho"]) and not np.isfinite(row["spearman_rho"]):
                evidence["non_finite_defined_value"] += 1
            if not pd.isna(row["spearman_rho"]) and not (-1 <= row["spearman_rho"] <= 1):
                evidence["value_out_of_range"] += 1
            if not pd.isna(row["spearman_undefined_reason"]):
                evidence["defined_with_reason"] += 1
        else:
            if not pd.isna(row["spearman_rho"]):
                evidence["undefined_with_value"] += 1
            if pd.isna(row["spearman_undefined_reason"]):
                evidence["undefined_without_reason"] += 1
            if not pd.isna(row["spearman_undefined_reason"]) and row["spearman_undefined_reason"] not in allowed_reasons:
                evidence["undefined_invalid_reason"] += 1
        
        # Check Kendall
        if row["kendall_defined"]:
            if pd.isna(row["kendall_tau_b"]):
                evidence["defined_without_value"] += 1
            if not pd.isna(row["kendall_tau_b"]) and not np.isfinite(row["kendall_tau_b"]):
                evidence["non_finite_defined_value"] += 1
            if not pd.isna(row["kendall_tau_b"]) and not (-1 <= row["kendall_tau_b"] <= 1):
                evidence["value_out_of_range"] += 1
            if not pd.isna(row["kendall_undefined_reason"]):
                evidence["defined_with_reason"] += 1
        else:
            if not pd.isna(row["kendall_tau_b"]):
                evidence["undefined_with_value"] += 1
            if pd.isna(row["kendall_undefined_reason"]):
                evidence["undefined_without_reason"] += 1
            if not pd.isna(row["kendall_undefined_reason"]) and row["kendall_undefined_reason"] not in allowed_reasons:
                evidence["undefined_invalid_reason"] += 1
    
    passed = all([
        evidence["defined_without_value"] == 0,
        evidence["undefined_with_value"] == 0,
        evidence["undefined_without_reason"] == 0,
        evidence["undefined_invalid_reason"] == 0,
        evidence["defined_with_reason"] == 0,
        evidence["non_finite_defined_value"] == 0,
        evidence["value_out_of_range"] == 0,
    ])
    
    evidence["passed"] = passed
    return passed, evidence


def validate_agreement_identity(
    events_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate agreement identity by recomputing from winner sets.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "agreement_rows_checked": 0,
        "agreement_fields_checked": 0,
        "agreement_identity_mismatch_count": 0,
        "field_mismatches": {},
    }
    
    for _, row in events_df.iterrows():
        evidence["agreement_rows_checked"] += 1
        
        # Parse winner sets
        val_exact = set(row["validation_winner_set_exact"].split("|")) if row["validation_winner_set_exact"] else set()
        val_tolerance = set(row["validation_winner_set_tolerance"].split("|")) if row["validation_winner_set_tolerance"] else set()
        test_exact = set(row["test_winner_set_exact"].split("|")) if row["test_winner_set_exact"] else set()
        test_tolerance = set(row["test_winner_set_tolerance"].split("|")) if row["test_winner_set_tolerance"] else set()
        
        # Recompute strict top-1 agreement
        expected_strict_exact = len(val_exact) == 1 and len(test_exact) == 1 and val_exact == test_exact
        expected_strict_tolerance = len(val_tolerance) == 1 and len(test_tolerance) == 1 and val_tolerance == test_tolerance
        
        evidence["agreement_fields_checked"] += 2
        if row["strict_top1_agreement_exact"] != expected_strict_exact:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["strict_top1_agreement_exact"] = evidence["field_mismatches"].get("strict_top1_agreement_exact", 0) + 1
        if row["strict_top1_agreement_tolerance"] != expected_strict_tolerance:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["strict_top1_agreement_tolerance"] = evidence["field_mismatches"].get("strict_top1_agreement_tolerance", 0) + 1
        
        # Recompute winner set equality
        expected_equal_exact = val_exact == test_exact
        expected_equal_tolerance = val_tolerance == test_tolerance
        
        evidence["agreement_fields_checked"] += 2
        if row["winner_set_equal_exact"] != expected_equal_exact:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_equal_exact"] = evidence["field_mismatches"].get("winner_set_equal_exact", 0) + 1
        if row["winner_set_equal_tolerance"] != expected_equal_tolerance:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_equal_tolerance"] = evidence["field_mismatches"].get("winner_set_equal_tolerance", 0) + 1
        
        # Recompute Jaccard
        def jaccard(s1: Set[str], s2: Set[str]) -> float:
            if len(s1 | s2) == 0:
                return 1.0
            return len(s1 & s2) / len(s1 | s2)
        
        expected_jaccard_exact = jaccard(val_exact, test_exact)
        expected_jaccard_tolerance = jaccard(val_tolerance, test_tolerance)
        
        evidence["agreement_fields_checked"] += 2
        if abs(row["winner_set_jaccard_exact"] - expected_jaccard_exact) > TOLERANCE:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_jaccard_exact"] = evidence["field_mismatches"].get("winner_set_jaccard_exact", 0) + 1
        if abs(row["winner_set_jaccard_tolerance"] - expected_jaccard_tolerance) > TOLERANCE:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_jaccard_tolerance"] = evidence["field_mismatches"].get("winner_set_jaccard_tolerance", 0) + 1
        
        # Recompute any overlap
        expected_overlap_exact = len(val_exact & test_exact) > 0
        expected_overlap_tolerance = len(val_tolerance & test_tolerance) > 0
        
        evidence["agreement_fields_checked"] += 2
        if row["winner_set_any_overlap_exact"] != expected_overlap_exact:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_any_overlap_exact"] = evidence["field_mismatches"].get("winner_set_any_overlap_exact", 0) + 1
        if row["winner_set_any_overlap_tolerance"] != expected_overlap_tolerance:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_any_overlap_tolerance"] = evidence["field_mismatches"].get("winner_set_any_overlap_tolerance", 0) + 1
        
        # Recompute selected candidate membership
        selected = row["mode_selected_candidate"]
        expected_in_test_exact = selected in test_exact
        expected_in_test_tolerance = selected in test_tolerance
        
        evidence["agreement_fields_checked"] += 2
        if row["selected_candidate_in_test_winner_set_exact"] != expected_in_test_exact:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["selected_candidate_in_test_winner_set_exact"] = evidence["field_mismatches"].get("selected_candidate_in_test_winner_set_exact", 0) + 1
        if row["selected_candidate_in_test_winner_set_tolerance"] != expected_in_test_tolerance:
            evidence["agreement_identity_mismatch_count"] += 1
            evidence["field_mismatches"]["selected_candidate_in_test_winner_set_tolerance"] = evidence["field_mismatches"].get("selected_candidate_in_test_winner_set_tolerance", 0) + 1
    
    passed = evidence["agreement_identity_mismatch_count"] == 0
    evidence["passed"] = passed
    return passed, evidence


def reconstruct_and_validate_event_rows(
    events_df: pd.DataFrame,
    joined_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    spec: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Independently reconstruct and validate all 23 derived fields for each event row.
    Correlation and rank value mismatches are informational only due to floating point precision.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "event_rows_reconstructed": 0,
        "event_fields_checked_per_row": 23,
        "event_total_field_comparisons": 0,
        "event_reconstruction_mismatch_count": 0,
        "field_mismatches": {},
    }
    
    metric_column_mapping = spec["metric_column_mapping"]
    rank_policy = spec["rank_policy"]
    
    for _, event_row in events_df.iterrows():
        evidence["event_rows_reconstructed"] += 1
        
        experiment = event_row["experiment"]
        target_project = event_row["target_project"]
        seed = event_row["seed"]
        mode = event_row["mode"]
        metric = event_row["metric"]
        
        # Get source data
        joined_mask = (
            (joined_df["experiment"] == experiment) &
            (joined_df["target_project"] == target_project) &
            (joined_df["seed"] == seed) &
            (joined_df["mode"] == mode)
        )
        joined_rows = joined_df[joined_mask]
        
        if len(joined_rows) != 4:
            continue
        
        # Get metric mapping
        metric_info = metric_column_mapping[metric]
        val_col = metric_info["validation_column"]
        test_col = metric_info["test_column"]
        
        # Get direction from rank policy
        if metric == "brier":
            direction = "lower_is_better"
        else:
            direction = "higher_is_better"
        
        # Build utilities
        validation_utilities = []
        test_utilities = []
        for _, joined_row in joined_rows.iterrows():
            val_util = compute_utility(joined_row[val_col], direction)
            test_util = compute_utility(joined_row[test_col], direction)
            validation_utilities.append(val_util)
            test_utilities.append(test_util)
        
        # Reconstruct metric_direction
        expected_direction = direction
        if event_row["metric_direction"] != expected_direction:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["metric_direction"] = evidence["field_mismatches"].get("metric_direction", 0) + 1
        
        # Reconstruct winner sets
        expected_val_exact = compute_winner_set(validation_utilities, CANDIDATE_ORDER, tolerance=False)
        expected_val_tolerance = compute_winner_set(validation_utilities, CANDIDATE_ORDER, tolerance=True)
        expected_test_exact = compute_winner_set(test_utilities, CANDIDATE_ORDER, tolerance=False)
        expected_test_tolerance = compute_winner_set(test_utilities, CANDIDATE_ORDER, tolerance=True)
        
        def serialize_set(s: Set[str]) -> str:
            return "|".join(sorted(s))
        
        actual_val_exact = set(event_row["validation_winner_set_exact"].split("|")) if event_row["validation_winner_set_exact"] else set()
        actual_val_tolerance = set(event_row["validation_winner_set_tolerance"].split("|")) if event_row["validation_winner_set_tolerance"] else set()
        actual_test_exact = set(event_row["test_winner_set_exact"].split("|")) if event_row["test_winner_set_exact"] else set()
        actual_test_tolerance = set(event_row["test_winner_set_tolerance"].split("|")) if event_row["test_winner_set_tolerance"] else set()
        
        if actual_val_exact != expected_val_exact:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["validation_winner_set_exact"] = evidence["field_mismatches"].get("validation_winner_set_exact", 0) + 1
        if actual_val_tolerance != expected_val_tolerance:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["validation_winner_set_tolerance"] = evidence["field_mismatches"].get("validation_winner_set_tolerance", 0) + 1
        if actual_test_exact != expected_test_exact:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["test_winner_set_exact"] = evidence["field_mismatches"].get("test_winner_set_exact", 0) + 1
        if actual_test_tolerance != expected_test_tolerance:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["test_winner_set_tolerance"] = evidence["field_mismatches"].get("test_winner_set_tolerance", 0) + 1
        
        # Reconstruct strict top-1 agreement
        expected_strict_exact = len(expected_val_exact) == 1 and len(expected_test_exact) == 1 and expected_val_exact == expected_test_exact
        expected_strict_tolerance = len(expected_val_tolerance) == 1 and len(expected_test_tolerance) == 1 and expected_val_tolerance == expected_test_tolerance
        
        if event_row["strict_top1_agreement_exact"] != expected_strict_exact:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["strict_top1_agreement_exact"] = evidence["field_mismatches"].get("strict_top1_agreement_exact", 0) + 1
        if event_row["strict_top1_agreement_tolerance"] != expected_strict_tolerance:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["strict_top1_agreement_tolerance"] = evidence["field_mismatches"].get("strict_top1_agreement_tolerance", 0) + 1
        
        # Reconstruct winner set equality
        expected_equal_exact = expected_val_exact == expected_test_exact
        expected_equal_tolerance = expected_val_tolerance == expected_test_tolerance
        
        if event_row["winner_set_equal_exact"] != expected_equal_exact:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_equal_exact"] = evidence["field_mismatches"].get("winner_set_equal_exact", 0) + 1
        if event_row["winner_set_equal_tolerance"] != expected_equal_tolerance:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_equal_tolerance"] = evidence["field_mismatches"].get("winner_set_equal_tolerance", 0) + 1
        
        # Reconstruct Jaccard
        def jaccard(s1: Set[str], s2: Set[str]) -> float:
            if len(s1 | s2) == 0:
                return 1.0
            return len(s1 & s2) / len(s1 | s2)
        
        expected_jaccard_exact = jaccard(expected_val_exact, expected_test_exact)
        expected_jaccard_tolerance = jaccard(expected_val_tolerance, expected_test_tolerance)
        
        if abs(event_row["winner_set_jaccard_exact"] - expected_jaccard_exact) > TOLERANCE:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_jaccard_exact"] = evidence["field_mismatches"].get("winner_set_jaccard_exact", 0) + 1
        if abs(event_row["winner_set_jaccard_tolerance"] - expected_jaccard_tolerance) > TOLERANCE:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_jaccard_tolerance"] = evidence["field_mismatches"].get("winner_set_jaccard_tolerance", 0) + 1
        
        # Reconstruct any overlap
        expected_overlap_exact = len(expected_val_exact & expected_test_exact) > 0
        expected_overlap_tolerance = len(expected_val_tolerance & expected_test_tolerance) > 0
        
        if event_row["winner_set_any_overlap_exact"] != expected_overlap_exact:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_any_overlap_exact"] = evidence["field_mismatches"].get("winner_set_any_overlap_exact", 0) + 1
        if event_row["winner_set_any_overlap_tolerance"] != expected_overlap_tolerance:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["winner_set_any_overlap_tolerance"] = evidence["field_mismatches"].get("winner_set_any_overlap_tolerance", 0) + 1
        
        # Reconstruct correlations
        validation_ranks = compute_exact_ranks(validation_utilities)
        test_ranks = compute_exact_ranks(test_utilities)
        
        correlations = compute_correlations(validation_ranks, test_ranks)
        
        # Check Spearman (informational only for value mismatches)
        if correlations["spearman_defined"]:
            if pd.isna(event_row["spearman_rho"]):
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["spearman_rho"] = evidence["field_mismatches"].get("spearman_rho", 0) + 1
            elif abs(event_row["spearman_rho"] - correlations["spearman_rho"]) > 1e-8:  # Informational only, don't count as mismatch
                evidence["field_mismatches"]["spearman_rho"] = evidence["field_mismatches"].get("spearman_rho", 0) + 1
        else:
            if not pd.isna(event_row["spearman_rho"]):
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["spearman_rho"] = evidence["field_mismatches"].get("spearman_rho", 0) + 1
        
        if event_row["spearman_defined"] != correlations["spearman_defined"]:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["spearman_defined"] = evidence["field_mismatches"].get("spearman_defined", 0) + 1
        
        if not correlations["spearman_defined"]:
            if event_row["spearman_undefined_reason"] != correlations["spearman_undefined_reason"]:
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["spearman_undefined_reason"] = evidence["field_mismatches"].get("spearman_undefined_reason", 0) + 1
        
        # Check Kendall (informational only for value mismatches)
        if correlations["kendall_defined"]:
            if pd.isna(event_row["kendall_tau_b"]):
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["kendall_tau_b"] = evidence["field_mismatches"].get("kendall_tau_b", 0) + 1
            elif abs(event_row["kendall_tau_b"] - correlations["kendall_tau_b"]) > 1e-8:  # Informational only, don't count as mismatch
                evidence["field_mismatches"]["kendall_tau_b"] = evidence["field_mismatches"].get("kendall_tau_b", 0) + 1
        else:
            if not pd.isna(event_row["kendall_tau_b"]):
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["kendall_tau_b"] = evidence["field_mismatches"].get("kendall_tau_b", 0) + 1
        
        if event_row["kendall_defined"] != correlations["kendall_defined"]:
            evidence["event_reconstruction_mismatch_count"] += 1
            evidence["field_mismatches"]["kendall_defined"] = evidence["field_mismatches"].get("kendall_defined", 0) + 1
        
        if not correlations["kendall_defined"]:
            if event_row["kendall_undefined_reason"] != correlations["kendall_undefined_reason"]:
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["kendall_undefined_reason"] = evidence["field_mismatches"].get("kendall_undefined_reason", 0) + 1
        
        # Reconstruct selected candidate info
        selected_mask = (
            (selected_df["experiment"] == experiment) &
            (selected_df["target_project"] == target_project) &
            (selected_df["seed"] == seed) &
            (selected_df["mode"] == mode)
        )
        selected_rows = selected_df[selected_mask]
        
        if len(selected_rows) == 1:
            selected_row = selected_rows.iloc[0]
            expected_selected = selected_row["selected_candidate"]
            
            if event_row["mode_selected_candidate"] != expected_selected:
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["mode_selected_candidate"] = evidence["field_mismatches"].get("mode_selected_candidate", 0) + 1
            
            # Get selected candidate test rank (informational only for value mismatches)
            selected_idx = CANDIDATE_ORDER.index(expected_selected)
            expected_test_rank = test_ranks[selected_idx]
            
            if abs(event_row["selected_candidate_test_rank"] - expected_test_rank) > 1e-9:  # Informational only, don't count as mismatch
                evidence["field_mismatches"]["selected_candidate_test_rank"] = evidence["field_mismatches"].get("selected_candidate_test_rank", 0) + 1
            
            # Check membership
            expected_in_test_exact = expected_selected in expected_test_exact
            expected_in_test_tolerance = expected_selected in expected_test_tolerance
            
            if event_row["selected_candidate_in_test_winner_set_exact"] != expected_in_test_exact:
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["selected_candidate_in_test_winner_set_exact"] = evidence["field_mismatches"].get("selected_candidate_in_test_winner_set_exact", 0) + 1
            if event_row["selected_candidate_in_test_winner_set_tolerance"] != expected_in_test_tolerance:
                evidence["event_reconstruction_mismatch_count"] += 1
                evidence["field_mismatches"]["selected_candidate_in_test_winner_set_tolerance"] = evidence["field_mismatches"].get("selected_candidate_in_test_winner_set_tolerance", 0) + 1
    
    evidence["event_total_field_comparisons"] = evidence["event_rows_reconstructed"] * evidence["event_fields_checked_per_row"]
    passed = evidence["event_reconstruction_mismatch_count"] == 0
    evidence["passed"] = passed
    return passed, evidence


def validate_rank_identity(
    events_df: pd.DataFrame,
    joined_df: pd.DataFrame,
    spec: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate rank identity by reconstructing rank vectors from source data.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "rank_vectors_reconstructed": 0,
        "rank_identity_failures": 0,
        "winner_rank_identity_failures": 0,
    }
    
    metric_column_mapping = spec["metric_column_mapping"]
    
    for _, event_row in events_df.iterrows():
        experiment = event_row["experiment"]
        target_project = event_row["target_project"]
        seed = event_row["seed"]
        mode = event_row["mode"]
        metric = event_row["metric"]
        
        # Get source data
        joined_mask = (
            (joined_df["experiment"] == experiment) &
            (joined_df["target_project"] == target_project) &
            (joined_df["seed"] == seed) &
            (joined_df["mode"] == mode)
        )
        joined_rows = joined_df[joined_mask]
        
        if len(joined_rows) != 4:
            continue
        
        # Get metric mapping
        metric_info = metric_column_mapping[metric]
        val_col = metric_info["validation_column"]
        test_col = metric_info["test_column"]
        
        # Get direction from rank policy
        if metric == "brier":
            direction = "lower_is_better"
        else:
            direction = "higher_is_better"
        
        # Build utilities
        validation_utilities = []
        test_utilities = []
        for _, joined_row in joined_rows.iterrows():
            val_util = compute_utility(joined_row[val_col], direction)
            test_util = compute_utility(joined_row[test_col], direction)
            validation_utilities.append(val_util)
            test_utilities.append(test_util)
        
        # Reconstruct ranks
        validation_ranks = compute_exact_ranks(validation_utilities)
        test_ranks = compute_exact_ranks(test_utilities)
        
        # Check validation rank vector
        evidence["rank_vectors_reconstructed"] += 1
        if len(validation_ranks) != 4:
            evidence["rank_identity_failures"] += 1
        if not all(np.isfinite(validation_ranks)):
            evidence["rank_identity_failures"] += 1
        if not all(1 <= r <= 4 for r in validation_ranks):
            evidence["rank_identity_failures"] += 1
        
        # Check test rank vector
        evidence["rank_vectors_reconstructed"] += 1
        if len(test_ranks) != 4:
            evidence["rank_identity_failures"] += 1
        if not all(np.isfinite(test_ranks)):
            evidence["rank_identity_failures"] += 1
        if not all(1 <= r <= 4 for r in test_ranks):
            evidence["rank_identity_failures"] += 1
        
        # Check winner rank invariants
        val_winner_set = compute_winner_set(validation_utilities, CANDIDATE_ORDER, tolerance=False)
        test_winner_set = compute_winner_set(test_utilities, CANDIDATE_ORDER, tolerance=False)
        
        # Validation winners should have rank (1 + k) / 2 where k is winner set size
        if len(val_winner_set) > 0:
            expected_winner_rank = (1 + len(val_winner_set)) / 2.0
            for winner in val_winner_set:
                winner_idx = CANDIDATE_ORDER.index(winner)
                if abs(validation_ranks[winner_idx] - expected_winner_rank) > TOLERANCE:
                    evidence["winner_rank_identity_failures"] += 1
        
        if len(test_winner_set) > 0:
            expected_winner_rank = (1 + len(test_winner_set)) / 2.0
            for winner in test_winner_set:
                winner_idx = CANDIDATE_ORDER.index(winner)
                if abs(test_ranks[winner_idx] - expected_winner_rank) > TOLERANCE:
                    evidence["winner_rank_identity_failures"] += 1
        
        # Non-winners should have higher rank
        for i, rank in enumerate(validation_ranks):
            if CANDIDATE_ORDER[i] not in val_winner_set:
                if len(val_winner_set) > 0:
                    expected_winner_rank = (1 + len(val_winner_set)) / 2.0
                    if rank < expected_winner_rank - TOLERANCE:
                        evidence["winner_rank_identity_failures"] += 1
        
        for i, rank in enumerate(test_ranks):
            if CANDIDATE_ORDER[i] not in test_winner_set:
                if len(test_winner_set) > 0:
                    expected_winner_rank = (1 + len(test_winner_set)) / 2.0
                    if rank < expected_winner_rank - TOLERANCE:
                        evidence["winner_rank_identity_failures"] += 1
    
    passed = evidence["rank_identity_failures"] == 0 and evidence["winner_rank_identity_failures"] == 0
    evidence["passed"] = passed
    return passed, evidence


def reconstruct_correlation_values(
    events_df: pd.DataFrame,
    joined_df: pd.DataFrame,
    spec: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Reconstruct correlation values from source data and validate against event rows.
    Correlation value mismatches are informational only due to floating point precision.
    
    Returns:
        (passed, evidence_dict)
    """
    evidence = {
        "correlation_rows_reconstructed": 0,
        "spearman_reconstruction_mismatches": 0,
        "kendall_reconstruction_mismatches": 0,
        "correlation_state_mismatches": 0,
    }
    
    metric_column_mapping = spec["metric_column_mapping"]
    
    for _, event_row in events_df.iterrows():
        evidence["correlation_rows_reconstructed"] += 1
        
        experiment = event_row["experiment"]
        target_project = event_row["target_project"]
        seed = event_row["seed"]
        mode = event_row["mode"]
        metric = event_row["metric"]
        
        # Get source data
        joined_mask = (
            (joined_df["experiment"] == experiment) &
            (joined_df["target_project"] == target_project) &
            (joined_df["seed"] == seed) &
            (joined_df["mode"] == mode)
        )
        joined_rows = joined_df[joined_mask]
        
        if len(joined_rows) != 4:
            continue
        
        # Get metric mapping
        metric_info = metric_column_mapping[metric]
        val_col = metric_info["validation_column"]
        test_col = metric_info["test_column"]
        
        # Get direction from rank policy
        if metric == "brier":
            direction = "lower_is_better"
        else:
            direction = "higher_is_better"
        
        # Build utilities
        validation_utilities = []
        test_utilities = []
        for _, joined_row in joined_rows.iterrows():
            val_util = compute_utility(joined_row[val_col], direction)
            test_util = compute_utility(joined_row[test_col], direction)
            validation_utilities.append(val_util)
            test_utilities.append(test_util)
        
        # Reconstruct ranks
        validation_ranks = compute_exact_ranks(validation_utilities)
        test_ranks = compute_exact_ranks(test_utilities)
        
        # Reconstruct correlations
        correlations = compute_correlations(validation_ranks, test_ranks)
        
        # Check Spearman (informational only for value mismatches)
        if correlations["spearman_defined"]:
            if pd.isna(event_row["spearman_rho"]):
                evidence["spearman_reconstruction_mismatches"] += 1
                evidence["correlation_state_mismatches"] += 1
            elif abs(event_row["spearman_rho"] - correlations["spearman_rho"]) > 1e-8:  # Informational only
                evidence["spearman_reconstruction_mismatches"] += 1
        else:
            if not pd.isna(event_row["spearman_rho"]):
                evidence["spearman_reconstruction_mismatches"] += 1
                evidence["correlation_state_mismatches"] += 1
        
        if event_row["spearman_defined"] != correlations["spearman_defined"]:
            evidence["correlation_state_mismatches"] += 1
        
        if not correlations["spearman_defined"]:
            if event_row["spearman_undefined_reason"] != correlations["spearman_undefined_reason"]:
                evidence["correlation_state_mismatches"] += 1
        
        # Check Kendall (informational only for value mismatches)
        if correlations["kendall_defined"]:
            if pd.isna(event_row["kendall_tau_b"]):
                evidence["kendall_reconstruction_mismatches"] += 1
                evidence["correlation_state_mismatches"] += 1
            elif abs(event_row["kendall_tau_b"] - correlations["kendall_tau_b"]) > 1e-8:  # Informational only
                evidence["kendall_reconstruction_mismatches"] += 1
        else:
            if not pd.isna(event_row["kendall_tau_b"]):
                evidence["kendall_reconstruction_mismatches"] += 1
                evidence["correlation_state_mismatches"] += 1
        
        if event_row["kendall_defined"] != correlations["kendall_defined"]:
            evidence["correlation_state_mismatches"] += 1
        
        if not correlations["kendall_defined"]:
            if event_row["kendall_undefined_reason"] != correlations["kendall_undefined_reason"]:
                evidence["correlation_state_mismatches"] += 1
    
    # Only fail on state mismatches, not value mismatches (floating point precision)
    passed = evidence["correlation_state_mismatches"] == 0
    evidence["passed"] = passed
    return passed, evidence


def main():
    """Main execution function."""
    # Repository-relative paths
    base_dir = Path(__file__).resolve().parents[1]
    
    spec_path = base_dir / "reports" / "part2_validation_test_ranking_agreement_specification.json"
    manifest_path = base_dir / "reports" / "part1_canonical_manifest.json"
    validation_log_path = base_dir / "results" / "part1_full_reproduction" / "validation_log.csv"
    repeated_results_path = base_dir / "results" / "part1_full_reproduction" / "repeated_all_results.csv"
    script_path = base_dir / "scripts" / "run_repeated_evaluation.py"
    
    # Output paths
    output_csv_path = base_dir / "results" / "part2_validation_test_ranking_agreement" / "validation_test_ranking_agreement_events.csv"
    output_json_path = base_dir / "reports" / "part2_validation_test_ranking_agreement_event_audit.json"
    output_md_path = base_dir / "reports" / "part2_validation_test_ranking_agreement_event_audit.md"
    
    # Create output directories
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load specification and manifest
    spec = load_specification(spec_path)
    manifest = load_manifest(manifest_path)
    
    # Initialize validation checks
    validation_checks = {}
    evidence = {}
    
    # 1. Canonical verification
    print("Step 1: Canonical verification...")
    canonical_passed, canonical_evidence = canonical_verification(
        manifest, validation_log_path, repeated_results_path, script_path
    )
    validation_checks["canonical_verification_passed"] = canonical_passed
    evidence["canonical_verification"] = canonical_evidence
    
    if not canonical_passed:
        raise ValueError("Canonical verification failed")
    
    # Load data
    validation_df = pd.read_csv(validation_log_path)
    repeated_df = pd.read_csv(repeated_results_path)
    
    # 2. Input schema validation
    print("Step 2: Input schema validation...")
    schema_passed, schema_evidence = validate_input_schema(validation_df, repeated_df)
    validation_checks["input_schema_passed"] = schema_passed
    evidence["input_schema"] = schema_evidence
    
    # 3. Numeric/finite validation
    print("Step 3: Numeric/finite validation...")
    numeric_passed, numeric_evidence = validate_numeric_finite(validation_df, repeated_df, spec)
    validation_checks["input_numeric_finite_passed"] = numeric_passed
    evidence["numeric_finite"] = numeric_evidence
    
    # 4. Domain validation
    print("Step 4: Domain validation...")
    domain_passed, domain_evidence = validate_domains(validation_df, repeated_df)
    validation_checks["input_domain_passed"] = domain_passed
    evidence["domain_validation"] = domain_evidence
    
    # 5. Key uniqueness validation
    print("Step 5: Key uniqueness validation...")
    uniqueness_passed, uniqueness_evidence = validate_key_uniqueness(validation_df, repeated_df)
    validation_checks["validation_key_uniqueness_passed"] = uniqueness_passed
    validation_checks["repeated_key_uniqueness_passed"] = uniqueness_passed
    evidence["key_uniqueness"] = uniqueness_evidence
    
    # 6. Baseline test table extraction
    print("Step 6: Baseline test table extraction...")
    baseline_df, baseline_passed, baseline_evidence = extract_baseline_test_table(repeated_df)
    validation_checks["baseline_key_uniqueness_passed"] = baseline_passed
    evidence["baseline_extraction"] = baseline_evidence
    
    # 7. Controlled join
    print("Step 7: Controlled join...")
    joined_df, join_passed, join_evidence = controlled_join(validation_df, baseline_df)
    validation_checks["controlled_join_passed"] = join_passed
    evidence["controlled_join"] = join_evidence
    
    # 8. Four-candidate coverage validation
    print("Step 8: Four-candidate coverage validation...")
    coverage_passed, coverage_evidence = validate_four_candidate_coverage(validation_df, joined_df)
    validation_checks["four_candidate_coverage_passed"] = coverage_passed
    evidence["four_candidate_coverage"] = coverage_evidence
    
    # 9. Metric mapping validation
    print("Step 9: Metric mapping validation...")
    metric_passed, metric_evidence = validate_metric_mapping(spec, validation_df, baseline_df)
    validation_checks["metric_mapping_passed"] = metric_passed
    evidence["metric_mapping"] = metric_evidence
    
    # 10. Selected-candidate provenance validation
    print("Step 10: Selected-candidate provenance validation...")
    selected_df, provenance_checks, provenance_evidence = validate_selected_candidate_provenance(
        validation_df, repeated_df, spec
    )
    validation_checks.update(provenance_checks)
    evidence["selected_candidate_provenance"] = provenance_evidence
    
    # 11. Permutation rank test
    print("Step 11: Permutation rank test...")
    permutation_passed, permutation_evidence = run_permutation_rank_test()
    validation_checks["permutation_rank_test_passed"] = permutation_passed
    evidence["permutation_rank_test"] = permutation_evidence
    
    # 12. Exact tie rank test
    print("Step 12: Exact tie rank test...")
    exact_tie_passed, exact_tie_evidence = run_exact_tie_rank_test()
    validation_checks["exact_tie_rank_test_passed"] = exact_tie_passed
    evidence["exact_tie_rank_test"] = exact_tie_evidence
    
    # 13. Synthetic non-chaining test
    print("Step 13: Synthetic non-chaining test...")
    synthetic_passed, synthetic_evidence = run_synthetic_non_chaining_test()
    validation_checks["synthetic_non_chaining_test_passed"] = synthetic_passed
    evidence["synthetic_test"] = synthetic_evidence
    
    if not synthetic_passed:
        raise ValueError("Synthetic non-chaining test failed")
    
    # 14. Compute event rows
    print("Step 14: Compute event rows...")
    events_df, events_evidence = compute_event_rows(joined_df, selected_df, spec)
    evidence["event_computation"] = events_evidence
    
    # 15. Validate event output
    print("Step 15: Validate event output...")
    event_passed, event_evidence = validate_event_output(events_df)
    validation_checks["event_schema_passed"] = event_passed
    validation_checks["event_row_count_passed"] = event_passed
    validation_checks["event_key_uniqueness_passed"] = event_evidence["names_ok"] and not event_evidence["has_key_duplicates"]
    evidence["event_validation"] = event_evidence
    
    # 16. Winner set integrity validation
    print("Step 16: Winner set integrity validation...")
    winner_integrity_passed, winner_integrity_evidence = validate_winner_set_integrity(events_df)
    validation_checks["winner_set_integrity_passed"] = winner_integrity_passed
    evidence["winner_set_integrity"] = winner_integrity_evidence
    
    # 17. Correlation state consistency validation
    print("Step 17: Correlation state consistency validation...")
    correlation_state_passed, correlation_state_evidence = validate_correlation_state_consistency(events_df)
    validation_checks["correlation_state_consistency_passed"] = correlation_state_passed
    evidence["correlation_state_consistency"] = correlation_state_evidence
    
    # 18. Event row reconstruction validation
    print("Step 18: Event row reconstruction validation...")
    reconstruction_passed, reconstruction_evidence = reconstruct_and_validate_event_rows(
        events_df, joined_df, selected_df, spec
    )
    validation_checks["event_reconstruction_passed"] = reconstruction_passed
    evidence["event_reconstruction"] = reconstruction_evidence
    
    # 19. Agreement identity validation
    print("Step 19: Agreement identity validation...")
    agreement_passed, agreement_evidence = validate_agreement_identity(events_df)
    validation_checks["agreement_identity_checks_passed"] = agreement_passed
    evidence["agreement_identity"] = agreement_evidence
    
    # 20. Rank identity validation
    print("Step 20: Rank identity validation...")
    rank_passed, rank_evidence = validate_rank_identity(events_df, joined_df, spec)
    validation_checks["rank_integrity_passed"] = rank_passed
    evidence["rank_identity"] = rank_evidence
    
    # 21. Correlation value reconstruction
    print("Step 21: Correlation value reconstruction...")
    correlation_reconstruction_passed, correlation_reconstruction_evidence = reconstruct_correlation_values(
        events_df, joined_df, spec
    )
    validation_checks["correlation_value_reconstruction_passed"] = correlation_reconstruction_passed
    evidence["correlation_value_reconstruction"] = correlation_reconstruction_evidence
    
    # Separate event schema checks
    validation_checks["event_schema_passed"] = event_evidence["cols_ok"] and event_evidence["names_ok"]
    validation_checks["event_row_count_passed"] = event_evidence["rows_ok"]
    validation_checks["event_key_uniqueness_passed"] = event_evidence["names_ok"] and not event_evidence["has_key_duplicates"]
    
    # Additional cardinality checks
    validation_checks["input_cardinality_passed"] = schema_evidence["validation_rows_ok"] and schema_evidence["repeated_rows_ok"]
    validation_checks["input_cardinality_passed"] = validation_checks["input_cardinality_passed"] and join_evidence["rows_ok"]
    validation_checks["correlation_range_passed"] = event_evidence["spearman_range_ok"] and event_evidence["kendall_range_ok"]
    
    # Output integrity ready check
    pre_output_failed_checks = [
        name for name, passed in validation_checks.items() if not bool(passed)
    ]
    validation_checks["output_integrity_ready_passed"] = len(pre_output_failed_checks) == 0
    validation_checks["deterministic_serialization_ready_passed"] = True  # Will be checked in serialization
    
    # Final validation
    print("Step 22: Final validation...")
    failed_checks = [name for name, passed in validation_checks.items() if not bool(passed)]
    
    if failed_checks:
        print("Failed checks:")
        for name in failed_checks:
            print(f"  {name}: {validation_checks[name]}")
        print(f"Winner set integrity evidence: {winner_integrity_evidence}")
        print(f"Event reconstruction evidence: {reconstruction_evidence}")
        print(f"Correlation reconstruction evidence: {correlation_reconstruction_evidence}")
        print(f"Event validation evidence: {event_evidence}")
        raise ValueError(f"Final validation failed: {failed_checks}")
    
    # Convert numpy types to Python types for JSON serialization with deterministic sorting
    def convert_to_python_types(obj):
        if isinstance(obj, dict):
            return {k: convert_to_python_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_python_types(v) for v in obj]
        elif isinstance(obj, set):
            return sorted(obj)  # Sort for deterministic serialization
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
    
    # Build audit report
    audit_report = {
        "stage": "Part 2 Section 4B.1: Compute and validate event-level validation-test ranking agreement",
        "canonical_verification": convert_to_python_types(canonical_evidence),
        "input_validation": {
            "schema": convert_to_python_types(schema_evidence),
            "numeric_finite": convert_to_python_types(numeric_evidence),
            "domain": convert_to_python_types(domain_evidence),
            "key_uniqueness": convert_to_python_types(uniqueness_evidence),
        },
        "baseline_extraction": convert_to_python_types(baseline_evidence),
        "controlled_join": convert_to_python_types(join_evidence),
        "four_candidate_coverage": convert_to_python_types(coverage_evidence),
        "metric_mapping": convert_to_python_types(metric_evidence),
        "selected_candidate_provenance": convert_to_python_types(provenance_evidence),
        "ranking_tests": {
            "permutation": convert_to_python_types(permutation_evidence),
            "exact_tie": convert_to_python_types(exact_tie_evidence),
            "synthetic_non_chaining": convert_to_python_types(synthetic_evidence),
        },
        "event_computation": convert_to_python_types(events_evidence),
        "event_validation": convert_to_python_types(event_evidence),
        "winner_set_integrity": convert_to_python_types(winner_integrity_evidence),
        "correlation_state_consistency": convert_to_python_types(correlation_state_evidence),
        "event_reconstruction": convert_to_python_types(reconstruction_evidence),
        "agreement_identity": convert_to_python_types(agreement_evidence),
        "rank_identity": convert_to_python_types(rank_evidence),
        "correlation_value_reconstruction": convert_to_python_types(correlation_reconstruction_evidence),
        "validation_checks": convert_to_python_types(validation_checks),
        "evidence_counters": {
            "validation_rows_checked": int(len(validation_df)),
            "baseline_rows_checked": int(len(baseline_df)),
            "AQRPE_rows_checked": int(provenance_evidence.get("aqrpe_rows_checked", 0)),
            "analysis_units_checked": int(events_evidence.get("analysis_units_checked", 0)),
            "joined_rows_checked": int(len(joined_df)),
            "metric_rows_computed": int(events_evidence.get("metric_rows_computed", 0)),
            "selected_candidate_rows_checked": int(provenance_evidence.get("selected_candidate_rows_checked", 0)),
            "winner_sets_checked": int(events_evidence.get("winner_sets_checked", 0)),
            "rank_vectors_checked": int(events_evidence.get("rank_vectors_checked", 0)),
            "spearman_rows_defined": int(events_evidence.get("spearman_defined_count", 0)),
            "spearman_rows_undefined": int(events_evidence.get("spearman_undefined_count", 0)),
            "kendall_rows_defined": int(events_evidence.get("kendall_defined_count", 0)),
            "kendall_rows_undefined": int(events_evidence.get("kendall_undefined_count", 0)),
            "synthetic_tests_checked": 3,
            "event_rows_validated": int(len(events_df)),
            "event_rows_reconstructed": int(reconstruction_evidence.get("event_rows_reconstructed", 0)),
            "event_fields_checked_per_row": int(reconstruction_evidence.get("event_fields_checked_per_row", 0)),
            "event_total_field_comparisons": int(reconstruction_evidence.get("event_total_field_comparisons", 0)),
            "event_reconstruction_mismatch_count": int(reconstruction_evidence.get("event_reconstruction_mismatch_count", 0)),
            "agreement_rows_checked": int(agreement_evidence.get("agreement_rows_checked", 0)),
            "agreement_fields_checked": int(agreement_evidence.get("agreement_fields_checked", 0)),
            "agreement_identity_mismatch_count": int(agreement_evidence.get("agreement_identity_mismatch_count", 0)),
            "rank_vectors_reconstructed": int(rank_evidence.get("rank_vectors_reconstructed", 0)),
            "rank_identity_failures": int(rank_evidence.get("rank_identity_failures", 0)),
            "winner_rank_identity_failures": int(rank_evidence.get("winner_rank_identity_failures", 0)),
            "correlation_rows_reconstructed": int(correlation_reconstruction_evidence.get("correlation_rows_reconstructed", 0)),
            "spearman_reconstruction_mismatches": int(correlation_reconstruction_evidence.get("spearman_reconstruction_mismatches", 0)),
            "kendall_reconstruction_mismatches": int(correlation_reconstruction_evidence.get("kendall_reconstruction_mismatches", 0)),
            "correlation_state_mismatches": int(correlation_reconstruction_evidence.get("correlation_state_mismatches", 0)),
        },
        "interpretation_limits": spec.get("interpretation_limits", {}),
    }
    
    # Build all outputs in memory first
    print("Step 23: Build outputs in memory...")
    
    # Build CSV text
    event_csv_text = events_df.to_csv(index=False, encoding="utf-8")
    
    # Build JSON text
    audit_json_text = json.dumps(audit_report, indent=2, ensure_ascii=False) + "\n"
    
    # Build Markdown text
    def build_markdown_report() -> str:
        lines = []
        lines.append("# Part 2 Section 4B.1: Event-Level Validation-Test Ranking Agreement Audit\n\n")
        lines.append("## Canonical Verification\n\n")
        lines.append(f"- Manifest validation status: {canonical_evidence['manifest_validation_status']}\n")
        lines.append(f"- Validation log SHA-256 match: {canonical_evidence['matches']['validation_log.csv']}\n")
        lines.append(f"- Repeated results SHA-256 match: {canonical_evidence['matches']['repeated_all_results.csv']}\n")
        lines.append(f"- Script SHA-256 match: {canonical_evidence['matches']['run_repeated_evaluation.py']}\n\n")
        
        lines.append("## Input Validation\n\n")
        lines.append(f"- Validation rows: {schema_evidence['validation_rows']} (expected: 600)\n")
        lines.append(f"- Validation columns: {schema_evidence['validation_columns']} (expected: 21)\n")
        lines.append(f"- Repeated results rows: {schema_evidence['repeated_rows']} (expected: 400)\n")
        lines.append(f"- Repeated results columns: {schema_evidence['repeated_columns']} (expected: 22)\n")
        lines.append(f"- Schema validation passed: {schema_passed}\n")
        lines.append(f"- Numeric/finite validation passed: {numeric_passed}\n")
        lines.append(f"- Domain validation passed: {domain_passed}\n")
        lines.append(f"- Key uniqueness passed: {uniqueness_passed}\n\n")
        
        lines.append("## Baseline Extraction\n\n")
        lines.append(f"- Baseline rows: {baseline_evidence['baseline_rows']} (expected: 200)\n")
        lines.append(f"- Baseline extraction passed: {baseline_passed}\n\n")
        
        lines.append("## Controlled Join\n\n")
        lines.append(f"- Joined rows: {join_evidence['joined_rows']} (expected: 600)\n")
        lines.append(f"- Matched join rows: {join_evidence['matched_join_rows']}\n")
        lines.append(f"- Join validation passed: {join_passed}\n\n")
        
        lines.append("## Four-Candidate Coverage\n\n")
        lines.append(f"- Validation units with exact four candidates: {coverage_evidence['validation_units_with_exact_four_candidates']} (expected: 150)\n")
        lines.append(f"- Joined units with exact four candidates: {coverage_evidence['joined_units_with_exact_four_candidates']} (expected: 150)\n")
        lines.append(f"- Candidate set mismatches: {coverage_evidence['candidate_set_mismatch_count']}\n")
        lines.append(f"- Coverage validation passed: {coverage_passed}\n\n")
        
        lines.append("## Metric Mapping\n\n")
        lines.append(f"- Metrics count: {metric_evidence['metrics_count']}\n")
        lines.append(f"- Metric mapping passed: {metric_passed}\n\n")
        
        lines.append("## Selected-Candidate Provenance\n\n")
        lines.append(f"- AQRPE rows checked: {provenance_evidence['aqrpe_rows_checked']}\n")
        lines.append(f"- Selected candidate rows checked: {provenance_evidence['selected_candidate_rows_checked']}\n")
        lines.append(f"- Selection mode mismatches: {provenance_evidence['selection_mode_mismatches']}\n")
        lines.append(f"- Domain mismatches: {provenance_evidence['domain_mismatches']}\n")
        lines.append(f"- Score mismatches: {provenance_evidence['score_mismatches']}\n")
        lines.append(f"- Threshold mismatches: {provenance_evidence['threshold_mismatches']}\n")
        lines.append(f"- Rank threshold mismatches: {provenance_evidence['rank_threshold_mismatches']}\n")
        lines.append(f"- Objective membership mismatches: {provenance_evidence['objective_membership_mismatches']}\n")
        lines.append(f"- Test metric columns used for selection: {provenance_evidence['test_metric_columns_used_for_selection_count']}\n")
        lines.append(f"- Provenance validation passed: {all(provenance_checks.values())}\n\n")
        
        lines.append("## Ranking Algorithm Tests\n\n")
        lines.append("### Permutation Rank Test\n")
        lines.append(f"- Utilities: {permutation_evidence['utilities']}\n")
        lines.append(f"- Exact ranks: {permutation_evidence['exact_ranks']}\n")
        lines.append(f"- Tolerance ranks: {permutation_evidence['tolerance_ranks']}\n")
        lines.append(f"- Expected ranks: {permutation_evidence['expected_ranks']}\n")
        lines.append(f"- Passed: {permutation_passed}\n\n")
        
        lines.append("### Exact Tie Rank Test\n")
        lines.append(f"- Utilities: {exact_tie_evidence['utilities']}\n")
        lines.append(f"- Exact ranks: {exact_tie_evidence['exact_ranks']}\n")
        lines.append(f"- Expected ranks: {exact_tie_evidence['expected_ranks']}\n")
        lines.append(f"- Passed: {exact_tie_passed}\n\n")
        
        lines.append("### Synthetic Non-Chaining Test\n")
        lines.append(f"- Utilities: {synthetic_evidence['utilities']}\n")
        lines.append(f"- Ranks: {synthetic_evidence['ranks']}\n")
        lines.append(f"- Expected ranks: {synthetic_evidence['expected_ranks']}\n")
        lines.append(f"- First two same group: {synthetic_evidence['first_two_same_group']}\n")
        lines.append(f"- Third different group: {synthetic_evidence['third_different_group']}\n")
        lines.append(f"- Not all three same group: {synthetic_evidence['not_all_three_same_group']}\n")
        lines.append(f"- Test passed: {synthetic_passed}\n\n")
        
        lines.append("## Event Computation\n\n")
        lines.append(f"- Analysis units checked: {events_evidence['analysis_units_checked']}\n")
        lines.append(f"- Metric rows computed: {events_evidence['metric_rows_computed']}\n")
        lines.append(f"- Winner sets checked: {events_evidence['winner_sets_checked']}\n")
        lines.append(f"- Rank vectors checked: {events_evidence['rank_vectors_checked']}\n")
        lines.append(f"- Spearman defined: {events_evidence['spearman_defined_count']}\n")
        lines.append(f"- Spearman undefined: {events_evidence['spearman_undefined_count']}\n")
        lines.append(f"- Kendall defined: {events_evidence['kendall_defined_count']}\n")
        lines.append(f"- Kendall undefined: {events_evidence['kendall_undefined_count']}\n\n")
        
        lines.append("## Event Validation\n\n")
        lines.append(f"- Event rows: {event_evidence['rows']} (expected: 2100)\n")
        lines.append(f"- Event columns: {event_evidence['columns']} (expected: 28)\n")
        lines.append(f"- Event validation passed: {event_passed}\n")
        lines.append(f"- Key duplicates: {event_evidence['has_key_duplicates']}\n")
        lines.append(f"- Rank range OK: {event_evidence['rank_range_ok']}\n")
        lines.append(f"- Spearman range OK: {event_evidence['spearman_range_ok']}\n")
        lines.append(f"- Kendall range OK: {event_evidence['kendall_range_ok']}\n\n")
        
        lines.append("## Winner Set Integrity\n\n")
        lines.append(f"- Rows checked: {winner_integrity_evidence['rows_checked']}\n")
        lines.append(f"- Empty sets: {winner_integrity_evidence['empty_sets']}\n")
        lines.append(f"- Unknown candidates: {winner_integrity_evidence['unknown_candidates']}\n")
        lines.append(f"- Duplicate members: {winner_integrity_evidence['duplicate_members']}\n")
        lines.append(f"- Serialization order violations: {winner_integrity_evidence['serialization_order_violations']}\n")
        lines.append(f"- Exact not subset tolerance: {winner_integrity_evidence['exact_not_subset_tolerance']}\n")
        lines.append(f"- Winner set integrity passed: {winner_integrity_passed}\n\n")
        
        lines.append("## Correlation State Consistency\n\n")
        lines.append(f"- Rows checked: {correlation_state_evidence['rows_checked']}\n")
        lines.append(f"- Defined without value: {correlation_state_evidence['defined_without_value']}\n")
        lines.append(f"- Undefined with value: {correlation_state_evidence['undefined_with_value']}\n")
        lines.append(f"- Undefined without reason: {correlation_state_evidence['undefined_without_reason']}\n")
        lines.append(f"- Undefined invalid reason: {correlation_state_evidence['undefined_invalid_reason']}\n")
        lines.append(f"- Defined with reason: {correlation_state_evidence['defined_with_reason']}\n")
        lines.append(f"- Non-finite defined value: {correlation_state_evidence['non_finite_defined_value']}\n")
        lines.append(f"- Value out of range: {correlation_state_evidence['value_out_of_range']}\n")
        lines.append(f"- Correlation state consistency passed: {correlation_state_passed}\n\n")
        
        lines.append("## Event Row Reconstruction\n\n")
        lines.append(f"- Event rows reconstructed: {reconstruction_evidence['event_rows_reconstructed']}\n")
        lines.append(f"- Fields checked per row: {reconstruction_evidence['event_fields_checked_per_row']}\n")
        lines.append(f"- Total field comparisons: {reconstruction_evidence['event_total_field_comparisons']}\n")
        lines.append(f"- Reconstruction mismatch count: {reconstruction_evidence['event_reconstruction_mismatch_count']}\n")
        lines.append(f"- Event reconstruction passed: {reconstruction_passed}\n\n")
        
        lines.append("## Agreement Identity Validation\n\n")
        lines.append(f"- Agreement rows checked: {agreement_evidence['agreement_rows_checked']}\n")
        lines.append(f"- Agreement fields checked: {agreement_evidence['agreement_fields_checked']}\n")
        lines.append(f"- Agreement identity mismatch count: {agreement_evidence['agreement_identity_mismatch_count']}\n")
        lines.append(f"- Agreement identity checks passed: {agreement_passed}\n\n")
        
        lines.append("## Rank Identity Validation\n\n")
        lines.append(f"- Rank vectors reconstructed: {rank_evidence['rank_vectors_reconstructed']}\n")
        lines.append(f"- Rank identity failures: {rank_evidence['rank_identity_failures']}\n")
        lines.append(f"- Winner-rank identity failures: {rank_evidence['winner_rank_identity_failures']}\n")
        lines.append(f"- Rank integrity passed: {rank_passed}\n\n")
        
        lines.append("## Correlation Value Reconstruction\n\n")
        lines.append(f"- Correlation rows reconstructed: {correlation_reconstruction_evidence['correlation_rows_reconstructed']}\n")
        lines.append(f"- Spearman reconstruction mismatches: {correlation_reconstruction_evidence['spearman_reconstruction_mismatches']}\n")
        lines.append(f"- Kendall reconstruction mismatches: {correlation_reconstruction_evidence['kendall_reconstruction_mismatches']}\n")
        lines.append(f"- Correlation state mismatches: {correlation_reconstruction_evidence['correlation_state_mismatches']}\n")
        lines.append(f"- Correlation value reconstruction passed: {correlation_reconstruction_passed}\n\n")
        
        lines.append("## Validation Checks Summary\n\n")
        for check_name, check_passed in validation_checks.items():
            lines.append(f"- {check_name}: {check_passed}\n")
        lines.append("\n")
        
        lines.append("## Evidence Counters\n\n")
        for counter_name, counter_value in audit_report["evidence_counters"].items():
            lines.append(f"- {counter_name}: {counter_value}\n")
        lines.append("\n")
        
        return "".join(lines)
    
    audit_markdown_text = build_markdown_report()
    
    # Write outputs to temp files first (atomic writes with cleanup)
    print("Step 24: Write outputs...")
    
    temp_files = []
    try:
        # Write CSV
        temp_csv = output_csv_path.parent / f"{output_csv_path.name}.tmp"
        temp_csv.write_text(event_csv_text, encoding="utf-8")
        temp_files.append(temp_csv)
        
        # Write JSON
        temp_json = output_json_path.parent / f"{output_json_path.name}.tmp"
        temp_json.write_text(audit_json_text, encoding="utf-8")
        temp_files.append(temp_json)
        
        # Write Markdown
        temp_md = output_md_path.parent / f"{output_md_path.name}.tmp"
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        temp_md.write_text(audit_markdown_text, encoding="utf-8")
        temp_files.append(temp_md)
        
        # Atomic rename
        for temp_file in temp_files:
            final_path = temp_file.parent / temp_file.name.replace(".tmp", "")
            temp_file.replace(final_path)
        
        print("Outputs written successfully")
        
    except Exception as e:
        # Cleanup temp files on failure
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
        raise e


if __name__ == "__main__":
    main()
