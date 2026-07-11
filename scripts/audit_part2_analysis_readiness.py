#!/usr/bin/env python3
"""
Part 2 Section 1A: Audit analysis readiness for supplementary analyses
Checks data coverage and structure for planned Part 2 analyses without running new models.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Base directory for portable paths
BASE_DIR = Path(__file__).resolve().parents[1]

# Paths
CANONICAL_RESULT_DIR = BASE_DIR / "results" / "part1_full_reproduction"
REPORTS_DIR = BASE_DIR / "reports"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Input files
MANIFEST_PATH = REPORTS_DIR / "part1_canonical_manifest.json"
REPEATED_RESULTS_PATH = CANONICAL_RESULT_DIR / "repeated_all_results.csv"
VALIDATION_LOG_PATH = CANONICAL_RESULT_DIR / "validation_log.csv"
DECISION_METADATA_PATH = CANONICAL_RESULT_DIR / "decision_metadata.json"
EVALUATION_SCRIPT_PATH = SCRIPTS_DIR / "run_repeated_evaluation.py"

# Output files
OUTPUT_JSON = REPORTS_DIR / "part2_analysis_readiness.json"
OUTPUT_MD = REPORTS_DIR / "part2_analysis_readiness.md"

# Expected values
EXPECTED_EXPERIMENTS = ["within_project", "cross_project"]
EXPECTED_PROJECTS = ["CM1", "JM1", "KC1", "KC2", "PC1"]
EXPECTED_SEEDS = [7, 13, 29, 42, 101]
BASELINE_MODELS = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
AQRPE_MODELS = ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc", "AQRPE_v2_soft_top3"]
ALL_MODELS = BASELINE_MODELS + AQRPE_MODELS
EXPECTED_MODES = ["balanced", "rank", "mcc"]

# Hard-coded metric lists
VALIDATION_METRICS = [
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

TEST_METRICS = [
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

# Expected field lists
SELECTION_FIELDS = ["selected_candidate", "selection_mode", "selection_score", "mode", "val_selection_score"]
CANDIDATE_IDENTIFIER_FIELDS = ["model", "candidate", "selected_candidate"]
RUN_IDENTIFIER_FIELDS = ["experiment", "target_project", "seed"]


def load_manifest():
    """Load and verify canonical manifest."""
    print("Loading canonical manifest...")
    
    if not MANIFEST_PATH.exists():
        raise ValueError(f"Manifest not found: {MANIFEST_PATH}")
    
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    
    return manifest


def verify_canonical_status(manifest):
    """Verify canonical manifest status."""
    print("Verifying canonical status...")
    
    # Check manifest validation status
    if manifest.get("manifest_validation_status") != "all_checks_passed":
        raise ValueError(f"Manifest validation status is '{manifest.get('manifest_validation_status')}', expected 'all_checks_passed'")
    
    # Check canonical result source
    if manifest["canonical_policy"]["canonical_result_source"] != "results/part1_full_reproduction":
        raise ValueError(f"Canonical result source is '{manifest['canonical_policy']['canonical_result_source']}', expected 'results/part1_full_reproduction'")
    
    # Get expected SHA-256 from manifest
    expected_sha = {
        "repeated_all_results.csv": manifest["canonical_reproduction_outputs"]["repeated_all_results.csv"]["sha256"],
        "validation_log.csv": manifest["canonical_reproduction_outputs"]["validation_log.csv"]["sha256"],
        "decision_metadata.json": manifest["canonical_reproduction_outputs"]["decision_metadata.json"]["sha256"],
    }
    
    # Verify file existence and compute SHA-256
    import hashlib
    
    def compute_sha256(path):
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    actual_sha = {
        "repeated_all_results.csv": compute_sha256(REPEATED_RESULTS_PATH),
        "validation_log.csv": compute_sha256(VALIDATION_LOG_PATH),
        "decision_metadata.json": compute_sha256(DECISION_METADATA_PATH),
    }
    
    for name, expected in expected_sha.items():
        if actual_sha[name] != expected:
            raise ValueError(f"SHA-256 mismatch for {name}: expected {expected[:16]}..., got {actual_sha[name][:16]}...")
    
    print("Canonical verification passed.")
    return expected_sha


def load_repeated_results():
    """Load and analyze repeated_all_results.csv."""
    print("Loading repeated_all_results.csv...")
    
    df = pd.read_csv(REPEATED_RESULTS_PATH)
    
    result = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "column_names": list(df.columns),
        "null_count": int(df.isnull().sum().sum()),
    }
    
    # Check structure
    if result["row_count"] != 400:
        raise ValueError(f"Expected 400 rows, got {result['row_count']}")
    
    if result["column_count"] != 22:
        raise ValueError(f"Expected 22 columns, got {result['column_count']}")
    
    if result["null_count"] != 0:
        raise ValueError(f"Expected 0 null values, got {result['null_count']}")
    
    # Check unique key
    key_cols = ["experiment", "target_project", "seed", "model"]
    key_duplicates = df.duplicated(subset=key_cols).sum()
    if key_duplicates > 0:
        raise ValueError(f"Found {key_duplicates} duplicate keys in repeated_all_results.csv")
    
    # Check experiments
    experiments = df["experiment"].unique()
    for exp in EXPECTED_EXPERIMENTS:
        if exp not in experiments:
            raise ValueError(f"Missing experiment: {exp}")
    
    # Check projects
    projects = df["target_project"].unique()
    for proj in EXPECTED_PROJECTS:
        if proj not in projects:
            raise ValueError(f"Missing project: {proj}")
    
    # Check seeds
    seeds = df["seed"].unique()
    for seed in EXPECTED_SEEDS:
        if seed not in seeds:
            raise ValueError(f"Missing seed: {seed}")
    
    # Check models
    models = df["model"].unique()
    for model in ALL_MODELS:
        if model not in models:
            raise ValueError(f"Missing model: {model}")
    
    # Check that each experiment × project × seed has exactly the expected 8 models
    for exp in EXPECTED_EXPERIMENTS:
        for proj in EXPECTED_PROJECTS:
            for seed in EXPECTED_SEEDS:
                subset = df[(df["experiment"] == exp) & (df["target_project"] == proj) & (df["seed"] == seed)]
                if len(subset) != 8:
                    raise ValueError(f"Expected 8 models for {exp}/{proj}/{seed}, got {len(subset)}")
                actual_models = set(subset["model"].unique())
                expected_models = set(ALL_MODELS)
                if actual_models != expected_models:
                    raise ValueError(f"Model set mismatch for {exp}/{proj}/{seed}: expected {expected_models}, got {actual_models}")
    
    result["experiments"] = list(experiments)
    result["projects"] = list(projects)
    result["seeds"] = list(sorted(seeds))
    result["models"] = list(models)
    result["key_duplicates"] = int(key_duplicates)
    
    print("Repeated results structure verified.")
    return df, result


def load_validation_log():
    """Load and analyze validation_log.csv."""
    print("Loading validation_log.csv...")
    
    df = pd.read_csv(VALIDATION_LOG_PATH)
    
    result = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "column_names": list(df.columns),
        "null_count": int(df.isnull().sum().sum()),
    }
    
    # Check structure
    if result["row_count"] != 600:
        raise ValueError(f"Expected 600 rows, got {result['row_count']}")
    
    if result["column_count"] != 21:
        raise ValueError(f"Expected 21 columns, got {result['column_count']}")
    
    if result["null_count"] != 0:
        raise ValueError(f"Expected 0 null values, got {result['null_count']}")
    
    # Check unique key
    key_cols = ["experiment", "target_project", "seed", "candidate", "mode"]
    key_duplicates = df.duplicated(subset=key_cols).sum()
    if key_duplicates > 0:
        raise ValueError(f"Found {key_duplicates} duplicate keys in validation_log.csv")
    
    # Check that each experiment × project × seed has exactly 4 candidates × 3 modes = 12 unique rows
    for exp in EXPECTED_EXPERIMENTS:
        for proj in EXPECTED_PROJECTS:
            for seed in EXPECTED_SEEDS:
                subset = df[(df["experiment"] == exp) & (df["target_project"] == proj) & (df["seed"] == seed)]
                if len(subset) != 12:
                    raise ValueError(f"Expected 12 rows for {exp}/{proj}/{seed}, got {len(subset)}")
                
                # Check exact candidates
                actual_candidates = set(subset["candidate"].unique())
                expected_candidates = set(BASELINE_MODELS)
                if actual_candidates != expected_candidates:
                    raise ValueError(f"Candidate set mismatch for {exp}/{proj}/{seed}: expected {expected_candidates}, got {actual_candidates}")
                
                # Check exact modes for each candidate
                for cand in BASELINE_MODELS:
                    cand_subset = subset[subset["candidate"] == cand]
                    actual_modes = set(cand_subset["mode"].unique())
                    expected_modes = set(EXPECTED_MODES)
                    if actual_modes != expected_modes:
                        raise ValueError(f"Mode set mismatch for {exp}/{proj}/{seed}/{cand}: expected {expected_modes}, got {actual_modes}")
    
    # Check modes
    modes = df["mode"].unique()
    for mode in EXPECTED_MODES:
        if mode not in modes:
            raise ValueError(f"Missing mode: {mode}")
    
    # Check that each mode has exactly 200 rows
    for mode in EXPECTED_MODES:
        mode_subset = df[df["mode"] == mode]
        if len(mode_subset) != 200:
            raise ValueError(f"Expected 200 rows for mode {mode}, got {len(mode_subset)}")
    
    # Check candidates
    candidates = df["candidate"].unique()
    for cand in BASELINE_MODELS:
        if cand not in candidates:
            raise ValueError(f"Missing candidate: {cand}")
    
    result["modes"] = list(modes)
    result["candidates"] = list(candidates)
    result["key_duplicates"] = int(key_duplicates)
    
    print("Validation log structure verified.")
    return df, result


def check_join_coverage(repeated_df, validation_df):
    """Check join coverage between validation_log and repeated_all_results for baseline models using pandas merge."""
    print("Checking join coverage...")
    
    # Filter repeated results to only baseline models
    baseline_df = repeated_df[repeated_df["model"].isin(BASELINE_MODELS)].copy()
    
    # Rename model to candidate for merge
    baseline_df = baseline_df.rename(columns={"model": "candidate"})
    
    join_results = {}
    
    for mode in EXPECTED_MODES:
        mode_validation = validation_df[validation_df["mode"] == mode].copy()
        
        # Check for duplicate keys in validation
        val_key_cols = ["experiment", "target_project", "seed", "candidate"]
        val_dup_keys = mode_validation.duplicated(subset=val_key_cols, keep=False)
        duplicate_validation_keys = int(val_dup_keys.sum())
        
        # Check for duplicate keys in baseline
        base_dup_keys = baseline_df.duplicated(subset=val_key_cols, keep=False)
        duplicate_baseline_keys = int(base_dup_keys.sum())
        
        # Perform merge
        merged = pd.merge(
            mode_validation,
            baseline_df,
            on=val_key_cols,
            how="left",
            indicator=True,
            validate="one_to_one"
        )
        
        # Count matches
        matched_rows = int((merged["_merge"] == "both").sum())
        unmatched_validation_rows = int((merged["_merge"] == "left_only").sum())
        
        join_results[mode] = {
            "validation_rows": int(len(mode_validation)),
            "baseline_rows": int(len(baseline_df)),
            "matched_rows": matched_rows,
            "unmatched_validation_rows": unmatched_validation_rows,
            "duplicate_validation_keys": duplicate_validation_keys,
            "duplicate_baseline_keys": duplicate_baseline_keys,
        }
        
        # Verify expectations
        if join_results[mode]["validation_rows"] != 200:
            raise ValueError(f"Mode {mode}: expected 200 validation rows, got {join_results[mode]['validation_rows']}")
        if join_results[mode]["baseline_rows"] != 200:
            raise ValueError(f"Mode {mode}: expected 200 baseline rows, got {join_results[mode]['baseline_rows']}")
        if join_results[mode]["matched_rows"] != 200:
            raise ValueError(f"Mode {mode}: expected 200 matched rows, got {join_results[mode]['matched_rows']}")
        if join_results[mode]["unmatched_validation_rows"] != 0:
            raise ValueError(f"Mode {mode}: expected 0 unmatched validation rows, got {join_results[mode]['unmatched_validation_rows']}")
        if join_results[mode]["duplicate_validation_keys"] != 0:
            raise ValueError(f"Mode {mode}: expected 0 duplicate validation keys, got {join_results[mode]['duplicate_validation_keys']}")
        if join_results[mode]["duplicate_baseline_keys"] != 0:
            raise ValueError(f"Mode {mode}: expected 0 duplicate baseline keys, got {join_results[mode]['duplicate_baseline_keys']}")
    
    print("Join coverage verified.")
    return join_results


def check_selected_candidate_integrity(repeated_df):
    """Check selected_candidate field integrity for AQRPE models."""
    print("Checking selected_candidate integrity...")
    
    result = {
        "top_1_models": {},
        "soft_top_3": {},
    }
    
    # Check top-1 models
    for model in ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc"]:
        model_df = repeated_df[repeated_df["model"] == model]
        
        if "selected_candidate" not in model_df.columns:
            result["top_1_models"][model] = {
                "has_field": False,
                "valid": False,
                "error": "selected_candidate column not found"
            }
            continue
        
        selected = model_df["selected_candidate"]
        
        # Check that all selected candidates are in baseline models
        invalid = selected[~selected.isin(BASELINE_MODELS)]
        
        result["top_1_models"][model] = {
            "has_field": True,
            "valid": len(invalid) == 0,
            "total_rows": int(len(model_df)),
            "invalid_count": int(len(invalid)),
            "invalid_values": list(invalid.unique()) if len(invalid) > 0 else [],
        }
    
    # Check soft-top-3
    soft_top3_df = repeated_df[repeated_df["model"] == "AQRPE_v2_soft_top3"]
    
    if "selected_candidate" not in soft_top3_df.columns:
        result["soft_top_3"] = {
            "has_field": False,
            "valid": False,
            "error": "selected_candidate column not found"
        }
    else:
        selected = soft_top3_df["selected_candidate"]
        
        # Parse pipe-separated values
        parsed = selected.apply(lambda x: str(x).split("|") if pd.notna(x) else [])
        
        # Check that each has exactly 3 candidates
        length_check = parsed.apply(len) == 3
        invalid_length = ~length_check
        
        # Check for duplicates within each selection
        duplicate_check = parsed.apply(lambda x: len(x) == len(set(x)))
        has_duplicates = ~duplicate_check
        
        # Check that all members are baseline models
        all_baseline = parsed.apply(lambda x: all(c in BASELINE_MODELS for c in x))
        invalid_members = ~all_baseline
        
        # Count unique orderings
        unique_orderings = set(tuple(x) for x in parsed)
        
        invalid_length_count = int(invalid_length.sum())
        duplicate_count = int(has_duplicates.sum())
        invalid_member_count = int(invalid_members.sum())
        
        valid = (
            invalid_length_count == 0
            and duplicate_count == 0
            and invalid_member_count == 0
            and len(soft_top3_df) == 50
        )
        
        if not valid:
            raise ValueError(f"Soft-top-3 validation failed: invalid_length={invalid_length_count}, duplicates={duplicate_count}, invalid_members={invalid_member_count}, rows={len(soft_top3_df)}")
        
        result["soft_top_3"] = {
            "has_field": True,
            "valid": valid,
            "total_rows": int(len(soft_top3_df)),
            "invalid_length_count": invalid_length_count,
            "duplicate_count": duplicate_count,
            "invalid_member_count": invalid_member_count,
            "unique_orderings_count": int(len(unique_orderings)),
            "unique_orderings": [list(o) for o in sorted(unique_orderings)],
        }
    
    print("Selected candidate integrity checked.")
    return result


def assess_analysis_readiness(repeated_df, validation_df, repeated_info, validation_info, selected_candidate_integrity, join_coverage, soft_all_4_check):
    """Assess readiness for each planned analysis based on validation checks."""
    print("Assessing analysis readiness...")
    
    readiness = {
        "candidate_selection_frequency_and_stability": {},
        "validation_test_ranking_agreement": {},
        "post_hoc_regret": {},
        "ablation": {},
    }
    
    # Check if all top-1 models are valid
    top_1_valid = all(
        selected_candidate_integrity["top_1_models"][model]["valid"] 
        for model in ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc"]
    )
    
    # Check if soft-top-3 is valid
    soft_top_3_valid = selected_candidate_integrity["soft_top_3"].get("valid", False)
    
    # Check if all join modes passed
    join_passed = all(
        join_coverage[mode]["matched_rows"] == 200 and
        join_coverage[mode]["unmatched_validation_rows"] == 0
        for mode in EXPECTED_MODES
    )
    
    # Check if all metrics are present
    validation_metrics_present = all(m in validation_info["column_names"] for m in VALIDATION_METRICS)
    test_metrics_present = all(m in repeated_info["column_names"] for m in TEST_METRICS)
    
    # A. Candidate selection frequency and stability
    if top_1_valid and soft_top_3_valid:
        readiness["candidate_selection_frequency_and_stability"] = {
            "status": "ready_from_existing_outputs",
            "reason": "All top-1 models have valid selected_candidate fields and soft-top-3 is valid.",
            "available_fields": {
                "top_1_selected_candidate": "selected_candidate column exists and valid for top-1 models",
                "soft_top_3_membership": "selected_candidate column exists and valid for soft-top-3 (pipe-separated)",
                "soft_top_3_order": "selected_candidate column preserves order for soft-top-3",
                "experiment": "experiment column exists",
                "target_project": "target_project column exists",
                "seed": "seed column exists",
            }
        }
    else:
        readiness["candidate_selection_frequency_and_stability"] = {
            "status": "not_determinable",
            "reason": f"Top-1 valid: {top_1_valid}, Soft-top-3 valid: {soft_top_3_valid}",
        }
    
    # B. Validation-test ranking agreement
    if validation_metrics_present and test_metrics_present and join_passed:
        readiness["validation_test_ranking_agreement"] = {
            "status": "ready_from_existing_outputs",
            "reason": "All 14 validation metrics and 14 test metrics are present. Join coverage is complete for all modes.",
            "available_fields": {
                "validation_metrics": f"{len(VALIDATION_METRICS)}/14 validation metrics present",
                "test_metrics": f"{len(TEST_METRICS)}/14 test metrics present",
                "join_keys": "experiment, target_project, seed, candidate↔model",
            }
        }
    else:
        readiness["validation_test_ranking_agreement"] = {
            "status": "not_determinable",
            "reason": f"Validation metrics present: {validation_metrics_present}, Test metrics present: {test_metrics_present}, Join passed: {join_passed}",
        }
    
    # C. Post-hoc regret
    if top_1_valid:
        readiness["post_hoc_regret"] = {
            "status": "ready_from_existing_outputs",
            "reason": "All four baselines are present in all 50 runs and top-1 selections are valid.",
            "available_fields": {
                "selected_top_1_candidate": "selected_candidate column exists and valid for top-1 models",
                "test_performance_all_candidates": "All four baseline models have test metrics in repeated_all_results.csv",
            }
        }
    else:
        readiness["post_hoc_regret"] = {
            "status": "not_determinable",
            "reason": f"Top-1 valid: {top_1_valid}",
        }
    
    # D. Ablation
    readiness["ablation"] = {
        "fixed_individual_baselines": {
            "status": "ready_from_existing_outputs",
            "reason": "All four baseline models have complete results in repeated_all_results.csv",
        },
        "adaptive_top_1": {
            "status": "ready_from_existing_outputs" if top_1_valid else "not_determinable",
            "reason": "Top-1 AQRPE models have valid selected_candidate fields" if top_1_valid else "Top-1 selections not valid",
        },
        "soft_top_3": {
            "status": "ready_from_existing_outputs" if soft_top_3_valid else "not_determinable",
            "reason": "AQRPE_v2_soft_top3 has valid selected_candidate field" if soft_top_3_valid else "Soft-top-3 not valid",
        },
        "soft_all_4": {
            "status": "requires_new_computation" if (
                not soft_all_4_check["existing_soft_all4_output"] and
                not soft_all_4_check["sample_level_candidate_probabilities_available"] and
                not soft_all_4_check["reconstructable_without_model_rerun"]
            ) else "ready_from_existing_outputs",
            "reason": soft_all_4_check["evidence"],
            "details": soft_all_4_check,
        }
    }
    
    print("Analysis readiness assessed.")
    return readiness


def verify_metrics(validation_info, repeated_info):
    """Verify that all expected metrics are present in the data files."""
    print("Verifying metrics...")
    
    # Check validation metrics
    missing_validation = []
    for metric in VALIDATION_METRICS:
        if metric not in validation_info["column_names"]:
            missing_validation.append(metric)
    
    if missing_validation:
        raise ValueError(f"Missing validation metrics: {missing_validation}")
    
    # Check test metrics
    missing_test = []
    for metric in TEST_METRICS:
        if metric not in repeated_info["column_names"]:
            missing_test.append(metric)
    
    if missing_test:
        raise ValueError(f"Missing test metrics: {missing_test}")
    
    print("All metrics verified.")
    return {
        "validation_metrics_present": len(VALIDATION_METRICS),
        "test_metrics_present": len(TEST_METRICS),
    }


def check_soft_all_4_availability(repeated_info, validation_info):
    """Check if soft-all-4 output is available by examining files and code."""
    print("Checking soft-all-4 availability...")
    
    result = {
        "existing_soft_all4_output": False,
        "sample_level_candidate_probabilities_available": False,
        "reconstructable_without_model_rerun": False,
        "evidence": [],
    }
    
    # Check for soft-all-4 in model names
    if "AQRPE_v2_soft_all4" in repeated_info.get("models", []):
        result["existing_soft_all4_output"] = True
        result["evidence"].append("Found AQRPE_v2_soft_all4 in repeated_all_results.csv models")
    else:
        result["evidence"].append("No AQRPE_v2_soft_all4 model found in repeated_all_results.csv")
    
    # Check for probability columns in both files
    all_cols = repeated_info["column_names"] + validation_info["column_names"]
    prob_cols = [col for col in all_cols if "prob" in col.lower() or "probability" in col.lower()]
    if prob_cols:
        result["sample_level_candidate_probabilities_available"] = True
        result["evidence"].append(f"Found probability columns: {prob_cols}")
    else:
        result["evidence"].append("No probability columns found in data files")
    
    # Check evaluation script for probability output
    if EVALUATION_SCRIPT_PATH.exists():
        with open(EVALUATION_SCRIPT_PATH, "r") as f:
            script_content = f.read()
        
        if "predict_proba" in script_content or "probability" in script_content.lower():
            result["evidence"].append("Evaluation script contains probability-related code")
        else:
            result["evidence"].append("Evaluation script does not contain predict_proba calls")
    else:
        result["evidence"].append("Evaluation script not found")
    
    # Check canonical directory for probability files
    canonical_files = list(CANONICAL_RESULT_DIR.glob("*"))
    prob_files = [f for f in canonical_files if "prob" in f.name.lower() or "prediction" in f.name.lower()]
    if prob_files:
        result["sample_level_candidate_probabilities_available"] = True
        result["evidence"].append(f"Found probability/prediction files in canonical directory: {[f.name for f in prob_files]}")
    
    # Determine reconstructability
    if result["existing_soft_all4_output"] and result["sample_level_candidate_probabilities_available"]:
        result["reconstructable_without_model_rerun"] = True
        result["evidence"].append("Soft-all-4 appears reconstructable from existing outputs")
    
    print("Soft-all-4 availability checked.")
    return result


def report_column_inventory(repeated_info, validation_info):
    """Report available columns and artifacts using hard-coded lists."""
    print("Reporting column inventory...")
    
    inventory = {
        "selection_fields": [],
        "validation_metric_fields": [],
        "test_metric_fields": [],
        "threshold_fields": [],
        "candidate_identifiers": [],
        "run_identifiers": [],
        "stored_artifacts": {},
    }
    
    # Check selection fields
    for field in SELECTION_FIELDS:
        if field in repeated_info["column_names"] or field in validation_info["column_names"]:
            inventory["selection_fields"].append(field)
    
    # Check validation metrics
    for metric in VALIDATION_METRICS:
        if metric in validation_info["column_names"]:
            inventory["validation_metric_fields"].append(metric)
    
    # Check test metrics
    for metric in TEST_METRICS:
        if metric in repeated_info["column_names"]:
            inventory["test_metric_fields"].append(metric)
    
    # Check candidate identifiers
    for field in CANDIDATE_IDENTIFIER_FIELDS:
        if field in repeated_info["column_names"] or field in validation_info["column_names"]:
            inventory["candidate_identifiers"].append(field)
    
    # Check run identifiers
    for field in RUN_IDENTIFIER_FIELDS:
        if field in repeated_info["column_names"] or field in validation_info["column_names"]:
            inventory["run_identifiers"].append(field)
    
    # Check for threshold fields
    all_cols = repeated_info["column_names"] + validation_info["column_names"]
    for col in all_cols:
        if "threshold" in col.lower():
            inventory["threshold_fields"].append(col)
    
    # Remove duplicates
    for key in ["selection_fields", "validation_metric_fields", "test_metric_fields", 
                "candidate_identifiers", "run_identifiers", "threshold_fields"]:
        inventory[key] = list(set(inventory[key]))
    
    # Check for stored artifacts
    inventory["stored_artifacts"] = {
        "sample_level_true_labels": False,
        "sample_level_predicted_probabilities": False,
        "validation_sample_indices": False,
        "test_sample_indices": False,
        "trained_model_objects": False,
    }
    
    # Check column names for evidence of these artifacts
    if any("true_label" in col.lower() or "y_true" in col.lower() for col in all_cols):
        inventory["stored_artifacts"]["sample_level_true_labels"] = True
    if any("prob" in col.lower() or "probability" in col.lower() for col in all_cols):
        inventory["stored_artifacts"]["sample_level_predicted_probabilities"] = True
    if any("validation_index" in col.lower() or "val_idx" in col.lower() for col in all_cols):
        inventory["stored_artifacts"]["validation_sample_indices"] = True
    if any("test_index" in col.lower() or "test_idx" in col.lower() for col in all_cols):
        inventory["stored_artifacts"]["test_sample_indices"] = True
    
    print("Column inventory reported.")
    return inventory


def build_report():
    """Build the complete analysis readiness report."""
    print("Building analysis readiness report...")
    
    # Load and verify manifest
    manifest = load_manifest()
    sha_values = verify_canonical_status(manifest)
    
    # Load data files
    repeated_df, repeated_info = load_repeated_results()
    validation_df, validation_info = load_validation_log()
    
    # Perform analyses
    join_coverage = check_join_coverage(repeated_df, validation_df)
    selected_candidate_integrity = check_selected_candidate_integrity(repeated_df)
    metric_verification = verify_metrics(validation_info, repeated_info)
    soft_all_4_check = check_soft_all_4_availability(repeated_info, validation_info)
    analysis_readiness = assess_analysis_readiness(
        repeated_df, validation_df, repeated_info, validation_info, 
        selected_candidate_integrity, join_coverage, soft_all_4_check
    )
    column_inventory = report_column_inventory(repeated_info, validation_info)
    
    # Final validation before save
    print("Performing final validation...")
    
    # Check top-1 models valid
    top_1_valid_count = sum(
        1 for model in ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc"]
        if selected_candidate_integrity["top_1_models"][model]["valid"]
    )
    if top_1_valid_count != 3:
        raise ValueError(f"Expected 3/3 top-1 models valid, got {top_1_valid_count}/3")
    
    # Check soft-top-3 valid
    if not selected_candidate_integrity["soft_top_3"].get("valid", False):
        raise ValueError("Soft-top-3 validation failed")
    
    # Check exact run coverage (50 runs = 2 experiments × 5 projects × 5 seeds)
    expected_runs = len(EXPECTED_EXPERIMENTS) * len(EXPECTED_PROJECTS) * len(EXPECTED_SEEDS)
    if expected_runs != 50:
        raise ValueError(f"Expected 50 runs, got {expected_runs}")
    
    # Check join modes passed
    join_modes_passed = sum(
        1 for mode in EXPECTED_MODES
        if join_coverage[mode]["matched_rows"] == 200 and
        join_coverage[mode]["unmatched_validation_rows"] == 0
    )
    if join_modes_passed != 3:
        raise ValueError(f"Expected 3/3 join modes passed, got {join_modes_passed}/3")
    
    # Check metrics present
    if metric_verification["validation_metrics_present"] != 14:
        raise ValueError(f"Expected 14 validation metrics, got {metric_verification['validation_metrics_present']}")
    if metric_verification["test_metrics_present"] != 14:
        raise ValueError(f"Expected 14 test metrics, got {metric_verification['test_metrics_present']}")
    
    print("Final validation passed.")
    
    # Build report
    report = {
        "canonical_verification": {
            "manifest_validation_status": manifest.get("manifest_validation_status"),
            "canonical_result_source": manifest["canonical_policy"]["canonical_result_source"],
            "sha256_verified": True,
            "sha256_values": sha_values,
        },
        "canonical_result_coverage": repeated_info,
        "validation_log_coverage": validation_info,
        "join_coverage": join_coverage,
        "selected_candidate_integrity": selected_candidate_integrity,
        "metric_verification": metric_verification,
        "soft_all_4_check": soft_all_4_check,
        "analysis_readiness": analysis_readiness,
        "column_inventory": column_inventory,
        "final_validation": {
            "top_1_models_valid": f"{top_1_valid_count}/3",
            "soft_top_3_valid": selected_candidate_integrity["soft_top_3"].get("valid", False),
            "exact_repeated_result_runs": f"{expected_runs}/50",
            "exact_validation_log_runs": f"{expected_runs}/50",
            "join_modes_passed": f"{join_modes_passed}/3",
            "validation_metrics_present": f"{metric_verification['validation_metrics_present']}/14",
            "test_metrics_present": f"{metric_verification['test_metrics_present']}/14",
        },
    }
    
    return report


def save_report(report):
    """Save report to JSON and Markdown files."""
    print("Saving report...")
    
    # Ensure output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump(report, f, indent=2, cls=NumpyEncoder)
    
    # Save Markdown
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 2 Section 1A: Analysis Readiness Audit\n\n")
        
        f.write("## Canonical Verification\n\n")
        f.write(f"- **Manifest validation status:** `{report['canonical_verification']['manifest_validation_status']}`\n")
        f.write(f"- **Canonical result source:** `{report['canonical_verification']['canonical_result_source']}`\n")
        f.write(f"- **SHA-256 verified:** {report['canonical_verification']['sha256_verified']}\n\n")
        
        f.write("## Canonical Result Coverage\n\n")
        f.write(f"- **Row count:** {report['canonical_result_coverage']['row_count']}\n")
        f.write(f"- **Column count:** {report['canonical_result_coverage']['column_count']}\n")
        f.write(f"- **Null count:** {report['canonical_result_coverage']['null_count']}\n")
        f.write(f"- **Key duplicates:** {report['canonical_result_coverage']['key_duplicates']}\n")
        f.write(f"- **Experiments:** {', '.join(report['canonical_result_coverage']['experiments'])}\n")
        f.write(f"- **Projects:** {', '.join(report['canonical_result_coverage']['projects'])}\n")
        f.write(f"- **Seeds:** {', '.join(map(str, report['canonical_result_coverage']['seeds']))}\n")
        f.write(f"- **Models:** {', '.join(report['canonical_result_coverage']['models'])}\n\n")
        
        f.write("## Validation-Log Coverage\n\n")
        f.write(f"- **Row count:** {report['validation_log_coverage']['row_count']}\n")
        f.write(f"- **Column count:** {report['validation_log_coverage']['column_count']}\n")
        f.write(f"- **Null count:** {report['validation_log_coverage']['null_count']}\n")
        f.write(f"- **Key duplicates:** {report['validation_log_coverage']['key_duplicates']}\n")
        f.write(f"- **Modes:** {', '.join(report['validation_log_coverage']['modes'])}\n")
        f.write(f"- **Candidates:** {', '.join(report['validation_log_coverage']['candidates'])}\n\n")
        
        f.write("## Join Coverage\n\n")
        f.write("| Mode | Validation Rows | Baseline Rows | Matched Rows | Unmatched Validation | Duplicate Validation Keys | Duplicate Baseline Keys |\n")
        f.write("|------|-----------------|---------------|--------------|----------------------|-------------------------|------------------------|\n")
        for mode, data in report['join_coverage'].items():
            f.write(f"| {mode} | {data['validation_rows']} | {data['baseline_rows']} | {data['matched_rows']} | {data['unmatched_validation_rows']} | {data['duplicate_validation_keys']} | {data['duplicate_baseline_keys']} |\n")
        f.write("\n")
        
        f.write("## Selected-Candidate Integrity\n\n")
        f.write("### Top-1 Models\n\n")
        for model, data in report['selected_candidate_integrity']['top_1_models'].items():
            f.write(f"**{model}:**\n")
            f.write(f"- Has field: {data['has_field']}\n")
            f.write(f"- Valid: {data['valid']}\n")
            if data['has_field']:
                f.write(f"- Total rows: {data['total_rows']}\n")
                f.write(f"- Invalid count: {data['invalid_count']}\n")
            f.write("\n")
        
        f.write("### Soft-Top-3\n\n")
        st3 = report['selected_candidate_integrity']['soft_top_3']
        f.write(f"- Has field: {st3['has_field']}\n")
        f.write(f"- Valid: {st3['valid']}\n")
        if st3['has_field']:
            f.write(f"- Total rows: {st3['total_rows']}\n")
            f.write(f"- Invalid length count: {st3['invalid_length_count']}\n")
            f.write(f"- Duplicate count: {st3['duplicate_count']}\n")
            f.write(f"- Invalid member count: {st3['invalid_member_count']}\n")
            f.write(f"- Unique orderings count: {st3['unique_orderings_count']}\n")
        f.write("\n")
        
        f.write("## Metric Verification\n\n")
        f.write(f"- **Validation metrics present:** {report['metric_verification']['validation_metrics_present']}/14\n")
        f.write(f"- **Test metrics present:** {report['metric_verification']['test_metrics_present']}/14\n\n")
        
        f.write("## Soft-All-4 Availability\n\n")
        f.write(f"- **Existing soft-all-4 output:** {report['soft_all_4_check']['existing_soft_all4_output']}\n")
        f.write(f"- **Sample-level probabilities available:** {report['soft_all_4_check']['sample_level_candidate_probabilities_available']}\n")
        f.write(f"- **Reconstructable without model rerun:** {report['soft_all_4_check']['reconstructable_without_model_rerun']}\n\n")
        f.write("**Evidence:**\n\n")
        for evidence in report['soft_all_4_check']['evidence']:
            f.write(f"- {evidence}\n")
        f.write("\n")
        
        f.write("## Final Validation\n\n")
        f.write(f"- **Top-1 models valid:** {report['final_validation']['top_1_models_valid']}\n")
        f.write(f"- **Soft-top-3 valid:** {report['final_validation']['soft_top_3_valid']}\n")
        f.write(f"- **Exact repeated-result runs:** {report['final_validation']['exact_repeated_result_runs']}\n")
        f.write(f"- **Exact validation-log runs:** {report['final_validation']['exact_validation_log_runs']}\n")
        f.write(f"- **Join modes passed:** {report['final_validation']['join_modes_passed']}\n")
        f.write(f"- **Validation metrics present:** {report['final_validation']['validation_metrics_present']}\n")
        f.write(f"- **Test metrics present:** {report['final_validation']['test_metrics_present']}\n\n")
        
        f.write("## Analysis Readiness Matrix\n\n")
        f.write("### Candidate Selection Frequency and Stability\n\n")
        f.write(f"**Status:** {report['analysis_readiness']['candidate_selection_frequency_and_stability']['status']}\n")
        f.write(f"**Reason:** {report['analysis_readiness']['candidate_selection_frequency_and_stability']['reason']}\n\n")
        
        f.write("### Validation-Test Ranking Agreement\n\n")
        f.write(f"**Status:** {report['analysis_readiness']['validation_test_ranking_agreement']['status']}\n")
        f.write(f"**Reason:** {report['analysis_readiness']['validation_test_ranking_agreement']['reason']}\n\n")
        
        f.write("### Post-Hoc Regret\n\n")
        f.write(f"**Status:** {report['analysis_readiness']['post_hoc_regret']['status']}\n")
        f.write(f"**Reason:** {report['analysis_readiness']['post_hoc_regret']['reason']}\n\n")
        
        f.write("### Ablation\n\n")
        for ablation_type, data in report['analysis_readiness']['ablation'].items():
            f.write(f"**{ablation_type}:**\n")
            f.write(f"- Status: {data['status']}\n")
            f.write(f"- Reason: {data['reason']}\n\n")
        
        f.write("## Missing Artifacts\n\n")
        f.write("The following artifacts are NOT stored in canonical outputs:\n\n")
        for artifact, stored in report['column_inventory']['stored_artifacts'].items():
            if not stored:
                f.write(f"- {artifact}\n")
        f.write("\n")
        
        f.write("## Next-Computation Implications\n\n")
        f.write("Based on the current audit:\n\n")
        f.write("- **Candidate selection analysis:** Can proceed immediately with existing outputs.\n")
        f.write("- **Validation-test agreement:** Can proceed immediately with existing outputs.\n")
        f.write("- **Post-hoc regret:** Can proceed immediately with existing outputs.\n")
        f.write("- **Ablation (fixed baselines, adaptive top-1, soft-top-3):** Can proceed immediately with existing outputs.\n")
        f.write("- **Ablation (soft-all-4):** Requires new computation to obtain sample-level probabilities for all four candidates.\n\n")
        f.write("No algorithm changes are proposed at this stage. This audit only assesses data availability.\n\n")
    
    print("Report saved.")


def main():
    """Main entry point."""
    report = build_report()
    save_report(report)
    
    print("\nAnalysis readiness audit complete!")
    print(f"\nSummary:")
    print(f"  Canonical verification: {report['canonical_verification']['manifest_validation_status']}")
    print(f"  Repeated-results coverage: {report['canonical_result_coverage']['row_count']} rows, {report['canonical_result_coverage']['column_count']} columns")
    print(f"  Validation-log coverage: {report['validation_log_coverage']['row_count']} rows, {report['validation_log_coverage']['column_count']} columns")
    print(f"  Join coverage: All modes have 200/200 matches")
    print(f"  Top-1 selected-candidate integrity: Checked")
    print(f"  Soft-top-3 integrity: Checked")
    print(f"  Candidate-selection analysis readiness: {report['analysis_readiness']['candidate_selection_frequency_and_stability']['status']}")
    print(f"  Validation-test agreement readiness: {report['analysis_readiness']['validation_test_ranking_agreement']['status']}")
    print(f"  Post-hoc regret readiness: {report['analysis_readiness']['post_hoc_regret']['status']}")
    print(f"  Ablation readiness: Mixed (see report)")
    print(f"  Soft-all-4 status: {report['analysis_readiness']['ablation']['soft_all_4']['status']}")


if __name__ == "__main__":
    main()
