#!/usr/bin/env python3
"""
Part 2 Section 3A: Analyze soft-top-3 composition frequency
Computes descriptive frequencies for soft-top-3 candidate selections across 50 runs.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import hashlib

# Base directory for portable paths
BASE_DIR = Path(__file__).resolve().parents[1]

# Paths
CANONICAL_RESULT_DIR = BASE_DIR / "results" / "part1_full_reproduction"
REPORTS_DIR = BASE_DIR / "reports"
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "results" / "part2_candidate_selection"

# Input files
MANIFEST_PATH = REPORTS_DIR / "part1_canonical_manifest.json"
READINESS_PATH = REPORTS_DIR / "part2_analysis_readiness.json"
REPEATED_RESULTS_PATH = CANONICAL_RESULT_DIR / "repeated_all_results.csv"
VALIDATION_LOG_PATH = CANONICAL_RESULT_DIR / "validation_log.csv"
EVALUATION_SCRIPT_PATH = SCRIPTS_DIR / "run_repeated_evaluation.py"

# Output files
OUTPUT_EVENTS = OUTPUT_DIR / "soft_top3_selection_events.csv"
OUTPUT_CANDIDATE_FREQ = OUTPUT_DIR / "soft_top3_candidate_frequency.csv"
OUTPUT_POSITION_FREQ = OUTPUT_DIR / "soft_top3_position_frequency.csv"
OUTPUT_ORDERING_FREQ = OUTPUT_DIR / "soft_top3_ordering_frequency.csv"
OUTPUT_JSON = REPORTS_DIR / "part2_soft_top3_composition_frequency.json"
OUTPUT_MD = REPORTS_DIR / "part2_soft_top3_composition_frequency.md"

# Constants
BASELINE_MODELS = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
CANDIDATE_ORDER = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
EXPECTED_EXPERIMENTS = ["within_project", "cross_project"]
EXPECTED_PROJECTS = ["CM1", "JM1", "KC1", "KC2", "PC1"]
EXPECTED_SEEDS = [7, 13, 29, 42, 101]
SOFT_TOP3_MODEL = "AQRPE_v2_soft_top3"
EXPECTED_SELECTION_MODE = "soft_top3_balanced_objective"

# Tolerance for floating point comparisons
TOLERANCE = 1e-12


def load_and_verify_inputs():
    """Load and verify all input files."""
    print("Loading and verifying inputs...")
    
    # Load manifest
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    
    # Load readiness report
    with open(READINESS_PATH, "r") as f:
        readiness = json.load(f)
    
    # Verify manifest status
    if manifest.get("manifest_validation_status") != "all_checks_passed":
        raise ValueError(f"Manifest validation status is '{manifest.get('manifest_validation_status')}', expected 'all_checks_passed'")
    
    # Verify readiness status
    if readiness["analysis_readiness"]["candidate_selection_frequency_and_stability"]["status"] != "ready_from_existing_outputs":
        raise ValueError("Candidate selection frequency analysis not ready")
    
    # Verify soft-top-3 validation
    if not readiness["final_validation"]["soft_top_3_valid"]:
        raise ValueError("Soft-top-3 validation failed")
    
    # Verify run counts
    if readiness["final_validation"]["exact_repeated_result_runs"] != "50/50":
        raise ValueError(f"Repeated result runs validation failed: {readiness['final_validation']['exact_repeated_result_runs']}")
    if readiness["final_validation"]["exact_validation_log_runs"] != "50/50":
        raise ValueError(f"Validation log runs validation failed: {readiness['final_validation']['exact_validation_log_runs']}")
    
    # Verify SHA-256
    def compute_sha256(path):
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    expected_sha = {
        "repeated_all_results.csv": manifest["canonical_reproduction_outputs"]["repeated_all_results.csv"]["sha256"],
        "validation_log.csv": manifest["canonical_reproduction_outputs"]["validation_log.csv"]["sha256"],
    }
    
    actual_sha = {
        "repeated_all_results.csv": compute_sha256(REPEATED_RESULTS_PATH),
        "validation_log.csv": compute_sha256(VALIDATION_LOG_PATH),
    }
    
    for name, expected in expected_sha.items():
        if actual_sha[name] != expected:
            raise ValueError(f"SHA-256 mismatch for {name}")
    
    # Verify evaluation script SHA-256 from environment_and_code_files
    if "run_repeated_evaluation.py" not in manifest.get("environment_and_code_files", {}):
        raise ValueError("run_repeated_evaluation.py not found in manifest environment_and_code_files")
    if not manifest["environment_and_code_files"]["run_repeated_evaluation.py"].get("exists"):
        raise ValueError("run_repeated_evaluation.py does not exist according to manifest")
    expected_script_sha = manifest["environment_and_code_files"]["run_repeated_evaluation.py"]["sha256"]
    actual_script_sha = compute_sha256(EVALUATION_SCRIPT_PATH)
    if actual_script_sha != expected_script_sha:
        raise ValueError(f"SHA-256 mismatch for run_repeated_evaluation.py: expected {expected_script_sha}, got {actual_script_sha}")
    
    # Load data files
    repeated_df = pd.read_csv(REPEATED_RESULTS_PATH)
    validation_df = pd.read_csv(VALIDATION_LOG_PATH)
    
    # Load evaluation script for provenance check
    with open(EVALUATION_SCRIPT_PATH, "r") as f:
        evaluation_script = f.read()
    
    print("Inputs verified.")
    return repeated_df, validation_df, evaluation_script


def verify_algorithm_provenance(evaluation_script):
    """Verify soft-top-3 algorithm provenance from evaluation script with exact code patterns."""
    print("Verifying algorithm provenance...")
    
    # Normalize whitespace for pattern matching
    normalized_script = " ".join(evaluation_script.split())
    
    # Check for exact code patterns
    patterns = {
        "balanced_objective_sort": 'top3 = sorted(fitted, key=lambda k: fitted[k]["objective_balanced"], reverse=True)[:3]',
        "validation_mean": 'val_stack = np.mean([fitted[k]["validation_scores"] for k in top3], axis=0)',
        "balanced_threshold_retuning": 't_stack, obj_stack = select_threshold(y_val, val_stack, "balanced")',
        "test_mean": 'test_stack = np.mean([model_scores(fitted[k]["model"], X_test) for k in top3], axis=0)',
        "pipe_order_storage": '"selected_candidate": "|".join(top3)',
        "selection_mode": '"selection_mode": "soft_top3_balanced_objective"',
    }
    
    provenance = {
        "balanced_objective_sort_verified": patterns["balanced_objective_sort"] in normalized_script,
        "top_three_slice_verified": patterns["balanced_objective_sort"] in normalized_script and "[:3]" in normalized_script,
        "validation_mean_verified": patterns["validation_mean"] in normalized_script,
        "balanced_threshold_retuning_verified": patterns["balanced_threshold_retuning"] in normalized_script,
        "test_mean_verified": patterns["test_mean"] in normalized_script,
        "pipe_order_storage_verified": patterns["pipe_order_storage"] in normalized_script,
        "selection_mode_verified": patterns["selection_mode"] in normalized_script,
    }
    
    # Check all are true
    if not all(provenance.values()):
        missing = [k for k, v in provenance.items() if not v]
        raise ValueError(f"Algorithm provenance verification failed for: {missing}")
    
    print("Algorithm provenance verified.")
    return provenance


def extract_soft_top3_events(repeated_df):
    """Extract soft-top-3 selection events from repeated_all_results.csv."""
    print("Extracting soft-top-3 events...")
    
    # Filter to soft-top-3 model
    soft_top3_df = repeated_df[repeated_df["model"] == SOFT_TOP3_MODEL].copy()
    
    # Verify row count
    if len(soft_top3_df) != 50:
        raise ValueError(f"Expected 50 soft-top-3 rows, got {len(soft_top3_df)}")
    
    # Verify experiments
    experiments = set(soft_top3_df["experiment"].unique())
    if experiments != set(EXPECTED_EXPERIMENTS):
        raise ValueError(f"Experiments mismatch: expected {EXPECTED_EXPERIMENTS}, got {experiments}")
    
    # Verify projects
    projects = set(soft_top3_df["target_project"].unique())
    if projects != set(EXPECTED_PROJECTS):
        raise ValueError(f"Projects mismatch: expected {EXPECTED_PROJECTS}, got {projects}")
    
    # Verify seeds
    seeds = set(soft_top3_df["seed"].unique())
    if seeds != set(EXPECTED_SEEDS):
        raise ValueError(f"Seeds mismatch: expected {EXPECTED_SEEDS}, got {seeds}")
    
    # Check for duplicate keys
    key_cols = ["experiment", "target_project", "seed"]
    duplicates = soft_top3_df.duplicated(subset=key_cols)
    if duplicates.sum() > 0:
        raise ValueError(f"Found {duplicates.sum()} duplicate keys in soft-top-3 events")
    
    # Check for nulls
    if soft_top3_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in soft-top-3 events")
    
    print("Soft-top-3 events extracted.")
    return soft_top3_df


def validate_selection_integrity(soft_top3_df, validation_df, repeated_df):
    """Validate selection integrity against validation log."""
    print("Validating selection integrity...")
    
    results = {
        "runs_checked": 0,
        "order_mismatches": 0,
        "membership_mismatches": 0,
        "excluded_candidate_mismatches": 0,
        "balanced_top1_consistency_mismatches": 0,
        "selection_mode_mismatches": 0,
        "invalid_thresholds": 0,
        "invalid_selection_scores": 0,
        "exact_score_tie_runs": 0,
        "near_score_tie_runs_within_1e-12": 0,
        "cutoff_near_tie_runs_within_1e-12": 0,
    }
    
    for _, row in soft_top3_df.iterrows():
        results["runs_checked"] += 1
        
        experiment = row["experiment"]
        target_project = row["target_project"]
        seed = row["seed"]
        selected_candidate = row["selected_candidate"]
        selection_mode = row["selection_mode"]
        threshold = row["threshold"]
        selection_score = row["selection_score"]
        
        # Parse selected_candidate
        selected_members = selected_candidate.split("|")
        
        # Check exactly 3 members
        if len(selected_members) != 3:
            results["membership_mismatches"] += 1
            continue
        
        # Check no duplicates
        if len(set(selected_members)) != 3:
            results["membership_mismatches"] += 1
            continue
        
        # Check all members are baseline models
        if not all(m in BASELINE_MODELS for m in selected_members):
            results["membership_mismatches"] += 1
            continue
        
        # Check selection mode
        if selection_mode != EXPECTED_SELECTION_MODE:
            results["selection_mode_mismatches"] += 1
        
        # Check threshold is finite and in (0, 1)
        if not (np.isfinite(threshold) and 0 < threshold < 1):
            results["invalid_thresholds"] += 1
        
        # Check selection_score is finite
        if not np.isfinite(selection_score):
            results["invalid_selection_scores"] += 1
        
        # Get validation scores for balanced mode
        val_subset = validation_df[
            (validation_df["experiment"] == experiment) &
            (validation_df["target_project"] == target_project) &
            (validation_df["seed"] == seed) &
            (validation_df["mode"] == "balanced")
        ]
        
        if len(val_subset) != 4:
            raise ValueError(f"Expected 4 validation rows for {experiment}/{target_project}/{seed}, got {len(val_subset)}")
        
        # Build score dictionary
        val_scores = {}
        for _, val_row in val_subset.iterrows():
            val_scores[val_row["candidate"]] = val_row["val_selection_score"]
        
        # Sort candidates by score (descending) and tie-breaking
        sorted_candidates = sorted(
            BASELINE_MODELS,
            key=lambda c: (-val_scores[c], CANDIDATE_ORDER.index(c))
        )
        
        # Expected top-3
        expected_top3 = sorted_candidates[:3]
        expected_excluded = sorted_candidates[3]
        
        # Check order matches
        if selected_members != expected_top3:
            results["order_mismatches"] += 1
        
        # Check excluded candidate - build from actual complement
        actual_excluded_set = set(BASELINE_MODELS) - set(selected_members)
        if len(actual_excluded_set) != 1:
            results["excluded_candidate_mismatches"] += 1
            continue
        actual_excluded = actual_excluded_set.pop()
        
        # Check actual excluded matches expected rank-4
        if actual_excluded != expected_excluded:
            results["excluded_candidate_mismatches"] += 1
        
        # Check consistency with balanced top-1
        balanced_row = repeated_df[
            (repeated_df["experiment"] == experiment) &
            (repeated_df["target_project"] == target_project) &
            (repeated_df["seed"] == seed) &
            (repeated_df["model"] == "AQRPE_v2_balanced")
        ]
        
        if len(balanced_row) == 1:
            balanced_selected = balanced_row["selected_candidate"].iloc[0]
            if balanced_selected != expected_top3[0]:
                results["balanced_top1_consistency_mismatches"] += 1
        
        # Check for exact score ties (actual equality, not rounded)
        from itertools import combinations
        score_values = [val_scores[c] for c in BASELINE_MODELS]
        exact_tie_found = False
        for score_a, score_b in combinations(score_values, 2):
            if score_a == score_b:
                exact_tie_found = True
                break
        if exact_tie_found:
            results["exact_score_tie_runs"] += 1
        
        # Check for near score ties (all 6 pairs)
        near_tie_found = False
        for score_a, score_b in combinations(score_values, 2):
            if abs(score_a - score_b) <= TOLERANCE:
                near_tie_found = True
                break
        if near_tie_found:
            results["near_score_tie_runs_within_1e-12"] += 1
        
        # Check cutoff near tie (position 3 vs position 4)
        cutoff_gap = val_scores[sorted_candidates[2]] - val_scores[sorted_candidates[3]]
        if abs(cutoff_gap) <= TOLERANCE:
            results["cutoff_near_tie_runs_within_1e-12"] += 1
    
    # Check that all critical mismatches are zero
    if results["order_mismatches"] > 0:
        raise ValueError(f"Found {results['order_mismatches']} order mismatches")
    if results["membership_mismatches"] > 0:
        raise ValueError(f"Found {results['membership_mismatches']} membership mismatches")
    if results["excluded_candidate_mismatches"] > 0:
        raise ValueError(f"Found {results['excluded_candidate_mismatches']} excluded candidate mismatches")
    if results["balanced_top1_consistency_mismatches"] > 0:
        raise ValueError(f"Found {results['balanced_top1_consistency_mismatches']} balanced top-1 consistency mismatches")
    if results["selection_mode_mismatches"] > 0:
        raise ValueError(f"Found {results['selection_mode_mismatches']} selection mode mismatches")
    if results["invalid_thresholds"] > 0:
        raise ValueError(f"Found {results['invalid_thresholds']} invalid thresholds")
    if results["invalid_selection_scores"] > 0:
        raise ValueError(f"Found {results['invalid_selection_scores']} invalid selection scores")
    
    print("Selection integrity validated.")
    return results


def save_selection_events(soft_top3_df, validation_df):
    """Save soft-top-3 selection events with detailed columns."""
    print("Saving selection events...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    event_rows = []
    
    for _, row in soft_top3_df.iterrows():
        experiment = row["experiment"]
        target_project = row["target_project"]
        seed = row["seed"]
        selected_candidate = row["selected_candidate"]
        selection_mode = row["selection_mode"]
        threshold = row["threshold"]
        selection_score = row["selection_score"]
        
        # Parse selected order
        selected_members = selected_candidate.split("|")
        
        # Get validation scores
        val_subset = validation_df[
            (validation_df["experiment"] == experiment) &
            (validation_df["target_project"] == target_project) &
            (validation_df["seed"] == seed) &
            (validation_df["mode"] == "balanced")
        ]
        
        val_scores = {}
        for _, val_row in val_subset.iterrows():
            val_scores[val_row["candidate"]] = val_row["val_selection_score"]
        
        # Build actual excluded from complement
        actual_excluded_set = set(BASELINE_MODELS) - set(selected_members)
        actual_excluded = actual_excluded_set.pop()
        
        # Sort candidates for cutoff calculation
        sorted_candidates = sorted(
            BASELINE_MODELS,
            key=lambda c: (-val_scores[c], CANDIDATE_ORDER.index(c))
        )
        
        # Build event row with scores mapped to actual selected/excluded candidates
        event_rows.append({
            "experiment": experiment,
            "target_project": target_project,
            "seed": seed,
            "selected_order": selected_candidate,
            "position_1_candidate": selected_members[0],
            "position_2_candidate": selected_members[1],
            "position_3_candidate": selected_members[2],
            "excluded_candidate": actual_excluded,
            "selection_mode": selection_mode,
            "threshold": threshold,
            "selection_score": selection_score,
            "balanced_score_position_1": val_scores[selected_members[0]],
            "balanced_score_position_2": val_scores[selected_members[1]],
            "balanced_score_position_3": val_scores[selected_members[2]],
            "balanced_score_excluded": val_scores[actual_excluded],
            "cutoff_score_gap": val_scores[sorted_candidates[2]] - val_scores[sorted_candidates[3]],
        })
    
    events_df = pd.DataFrame(event_rows)
    
    # Sort
    events_df = events_df.sort_values(["experiment", "target_project", "seed"])
    
    # Verify row count
    if len(events_df) != 50:
        raise ValueError(f"Expected 50 event rows, got {len(events_df)}")
    
    # Verify column count
    if len(events_df.columns) != 16:
        raise ValueError(f"Expected 16 columns, got {len(events_df.columns)}")
    
    # Check for nulls
    if events_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in events")
    
    # Check for duplicate keys
    key_cols = ["experiment", "target_project", "seed"]
    duplicates = events_df.duplicated(subset=key_cols)
    if duplicates.sum() > 0:
        raise ValueError(f"Found {duplicates.sum()} duplicate keys in events")
    
    events_df.to_csv(OUTPUT_EVENTS, index=False)
    
    print("Selection events saved.")
    return events_df


def compute_candidate_frequency(events_df):
    """Compute candidate membership and exclusion frequency."""
    print("Computing candidate frequency...")
    
    freq_rows = []
    
    # Overall
    for candidate in BASELINE_MODELS:
        membership_count = sum(1 for _, row in events_df.iterrows() if candidate in row["selected_order"].split("|"))
        exclusion_count = sum(1 for _, row in events_df.iterrows() if row["excluded_candidate"] == candidate)
        
        freq_rows.append({
            "scope": "overall",
            "experiment": "all",
            "target_project": "all",
            "candidate": candidate,
            "membership_count": membership_count,
            "exclusion_count": exclusion_count,
            "denominator": 50,
            "membership_proportion": membership_count / 50,
            "exclusion_proportion": exclusion_count / 50,
        })
    
    # By setting
    for experiment in EXPECTED_EXPERIMENTS:
        exp_events = events_df[events_df["experiment"] == experiment]
        for candidate in BASELINE_MODELS:
            membership_count = sum(1 for _, row in exp_events.iterrows() if candidate in row["selected_order"].split("|"))
            exclusion_count = sum(1 for _, row in exp_events.iterrows() if row["excluded_candidate"] == candidate)
            
            freq_rows.append({
                "scope": "by_setting",
                "experiment": experiment,
                "target_project": "all",
                "candidate": candidate,
                "membership_count": membership_count,
                "exclusion_count": exclusion_count,
                "denominator": 25,
                "membership_proportion": membership_count / 25,
                "exclusion_proportion": exclusion_count / 25,
            })
    
    # By project
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            exp_proj_events = events_df[
                (events_df["experiment"] == experiment) &
                (events_df["target_project"] == project)
            ]
            for candidate in BASELINE_MODELS:
                membership_count = sum(1 for _, row in exp_proj_events.iterrows() if candidate in row["selected_order"].split("|"))
                exclusion_count = sum(1 for _, row in exp_proj_events.iterrows() if row["excluded_candidate"] == candidate)
                
                freq_rows.append({
                    "scope": "by_project",
                    "experiment": experiment,
                    "target_project": project,
                    "candidate": candidate,
                    "membership_count": membership_count,
                    "exclusion_count": exclusion_count,
                    "denominator": 5,
                    "membership_proportion": membership_count / 5,
                    "exclusion_proportion": exclusion_count / 5,
                })
    
    freq_df = pd.DataFrame(freq_rows)
    
    # Verify row count
    if len(freq_df) != 52:
        raise ValueError(f"Expected 52 candidate-frequency rows, got {len(freq_df)}")
    
    # Check for nulls
    if freq_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in candidate frequency")
    
    # Check for duplicate keys
    key_cols = ["scope", "experiment", "target_project", "candidate"]
    duplicates = freq_df.duplicated(subset=key_cols)
    if duplicates.sum() > 0:
        raise ValueError(f"Found {duplicates.sum()} duplicate keys in candidate frequency")
    
    # Verify sums for each group
    for scope in ["overall", "by_setting", "by_project"]:
        if scope == "overall":
            groups = [("all", "all")]
        elif scope == "by_setting":
            groups = [(exp, "all") for exp in EXPECTED_EXPERIMENTS]
        else:  # by_project
            groups = [(exp, proj) for exp in EXPECTED_EXPERIMENTS for proj in EXPECTED_PROJECTS]
        
        for experiment, project in groups:
            subset = freq_df[(freq_df["scope"] == scope) & (freq_df["experiment"] == experiment) & (freq_df["target_project"] == project)]
            membership_sum = subset["membership_count"].sum()
            exclusion_sum = subset["exclusion_count"].sum()
            denominator = subset["denominator"].iloc[0]
            
            expected_membership_sum = 3 * denominator
            expected_exclusion_sum = denominator
            
            if membership_sum != expected_membership_sum:
                raise ValueError(f"Expected membership sum {expected_membership_sum} for {scope}/{experiment}/{project}, got {membership_sum}")
            if exclusion_sum != expected_exclusion_sum:
                raise ValueError(f"Expected exclusion sum {expected_exclusion_sum} for {scope}/{experiment}/{project}, got {exclusion_sum}")
    
    # Verify per-candidate sums and proportions
    for _, row in freq_df.iterrows():
        if row["membership_count"] + row["exclusion_count"] != row["denominator"]:
            raise ValueError(f"Membership + exclusion != denominator for {row['scope']}/{row['experiment']}/{row['target_project']}/{row['candidate']}")
        expected_membership_prop = row["membership_count"] / row["denominator"]
        expected_exclusion_prop = row["exclusion_count"] / row["denominator"]
        if abs(row["membership_proportion"] - expected_membership_prop) > TOLERANCE:
            raise ValueError(f"Membership proportion mismatch for {row['scope']}/{row['experiment']}/{row['target_project']}/{row['candidate']}")
        if abs(row["exclusion_proportion"] - expected_exclusion_prop) > TOLERANCE:
            raise ValueError(f"Exclusion proportion mismatch for {row['scope']}/{row['experiment']}/{row['target_project']}/{row['candidate']}")
    
    # Sort
    freq_df = freq_df.sort_values(["scope", "experiment", "target_project", "candidate"])
    
    freq_df.to_csv(OUTPUT_CANDIDATE_FREQ, index=False)
    
    print("Candidate frequency computed.")
    return freq_df


def compute_position_frequency(events_df):
    """Compute position frequency."""
    print("Computing position frequency...")
    
    freq_rows = []
    
    # Generate all combinations
    from itertools import product
    
    # Overall
    for position in [1, 2, 3]:
        for candidate in BASELINE_MODELS:
            count = sum(1 for _, row in events_df.iterrows() 
                       if row[f"position_{position}_candidate"] == candidate)
            
            freq_rows.append({
                "scope": "overall",
                "experiment": "all",
                "position": position,
                "candidate": candidate,
                "count": count,
                "denominator": 50,
                "proportion": count / 50,
            })
    
    # By setting
    for experiment in EXPECTED_EXPERIMENTS:
        exp_events = events_df[events_df["experiment"] == experiment]
        for position in [1, 2, 3]:
            for candidate in BASELINE_MODELS:
                count = sum(1 for _, row in exp_events.iterrows() 
                           if row[f"position_{position}_candidate"] == candidate)
                
                freq_rows.append({
                    "scope": "by_setting",
                    "experiment": experiment,
                    "position": position,
                    "candidate": candidate,
                    "count": count,
                    "denominator": 25,
                    "proportion": count / 25,
                })
    
    freq_df = pd.DataFrame(freq_rows)
    
    # Verify row count
    if len(freq_df) != 36:
        raise ValueError(f"Expected 36 position-frequency rows, got {len(freq_df)}")
    
    # Verify sums
    for scope in ["overall", "by_setting"]:
        for experiment in ["all"] if scope == "overall" else EXPECTED_EXPERIMENTS:
            for position in [1, 2, 3]:
                subset = freq_df[(freq_df["scope"] == scope) & (freq_df["experiment"] == experiment) & (freq_df["position"] == position)]
                subset_sum = subset["count"].sum()
                expected_sum = 50 if scope == "overall" else 25
                if subset_sum != expected_sum:
                    raise ValueError(f"Expected sum {expected_sum} for {scope}/{experiment}/{position}, got {subset_sum}")
                subset_prop_sum = subset["proportion"].sum()
                if abs(subset_prop_sum - 1.0) > TOLERANCE:
                    raise ValueError(f"Expected proportion sum 1.0 for {scope}/{experiment}/{position}, got {subset_prop_sum}")
    
    # Sort
    freq_df = freq_df.sort_values(["scope", "experiment", "position", "candidate"])
    
    freq_df.to_csv(OUTPUT_POSITION_FREQ, index=False)
    
    print("Position frequency computed.")
    return freq_df


def compute_ordering_frequency(events_df):
    """Compute ordering frequency."""
    print("Computing ordering frequency...")
    
    # Generate all possible orderings (4P3 = 24)
    from itertools import permutations
    
    all_orderings = list(permutations(BASELINE_MODELS, 3))
    all_ordering_strs = ["|".join(ordering) for ordering in all_orderings]
    
    freq_rows = []
    
    # Overall
    for ordering in all_ordering_strs:
        count = sum(1 for _, row in events_df.iterrows() if row["selected_order"] == ordering)
        
        freq_rows.append({
            "scope": "overall",
            "experiment": "all",
            "selected_order": ordering,
            "count": count,
            "denominator": 50,
            "proportion": count / 50,
        })
    
    # By setting
    for experiment in EXPECTED_EXPERIMENTS:
        exp_events = events_df[events_df["experiment"] == experiment]
        for ordering in all_ordering_strs:
            count = sum(1 for _, row in exp_events.iterrows() if row["selected_order"] == ordering)
            
            freq_rows.append({
                "scope": "by_setting",
                "experiment": experiment,
                "selected_order": ordering,
                "count": count,
                "denominator": 25,
                "proportion": count / 25,
            })
    
    freq_df = pd.DataFrame(freq_rows)
    
    # Verify row count
    if len(freq_df) != 72:
        raise ValueError(f"Expected 72 ordering-frequency rows, got {len(freq_df)}")
    
    # Verify sums
    for scope in ["overall", "by_setting"]:
        for experiment in ["all"] if scope == "overall" else EXPECTED_EXPERIMENTS:
            subset = freq_df[(freq_df["scope"] == scope) & (freq_df["experiment"] == experiment)]
            subset_sum = subset["count"].sum()
            expected_sum = 50 if scope == "overall" else 25
            if subset_sum != expected_sum:
                raise ValueError(f"Expected sum {expected_sum} for {scope}/{experiment}, got {subset_sum}")
            subset_prop_sum = subset["proportion"].sum()
            if abs(subset_prop_sum - 1.0) > TOLERANCE:
                raise ValueError(f"Expected proportion sum 1.0 for {scope}/{experiment}, got {subset_prop_sum}")
    
    # Sort
    freq_df = freq_df.sort_values(["scope", "experiment", "selected_order"])
    
    freq_df.to_csv(OUTPUT_ORDERING_FREQ, index=False)
    
    print("Ordering frequency computed.")
    return freq_df


def compute_descriptive_summary(events_df, candidate_freq, position_freq, ordering_freq):
    """Compute descriptive summary statistics."""
    print("Computing descriptive summary...")
    
    summary = {
        "overall": {},
        "by_setting": {},
    }
    
    # Overall summary
    overall_events = events_df
    unique_orders = set(overall_events["selected_order"])
    
    # Most frequent order
    overall_ordering = ordering_freq[ordering_freq["scope"] == "overall"]
    max_order_count = overall_ordering["count"].max()
    most_frequent_orders = overall_ordering[overall_ordering["count"] == max_order_count]["selected_order"].tolist()
    
    # Most frequent position 1 candidate
    overall_pos1 = position_freq[(position_freq["scope"] == "overall") & (position_freq["position"] == 1)]
    max_pos1_count = overall_pos1["count"].max()
    most_frequent_pos1 = overall_pos1[overall_pos1["count"] == max_pos1_count]["candidate"].tolist()
    
    # Most frequently included
    overall_candidate = candidate_freq[candidate_freq["scope"] == "overall"]
    max_membership = overall_candidate["membership_count"].max()
    most_frequent_included = overall_candidate[overall_candidate["membership_count"] == max_membership]["candidate"].tolist()
    
    # Most frequently excluded
    max_exclusion = overall_candidate["exclusion_count"].max()
    most_frequent_excluded = overall_candidate[overall_candidate["exclusion_count"] == max_exclusion]["candidate"].tolist()
    
    # Cutoff score gaps
    cutoff_gaps = overall_events["cutoff_score_gap"].values
    
    summary["overall"] = {
        "unique_observed_order_count": len(unique_orders),
        "most_frequent_orders": most_frequent_orders,
        "maximum_order_count": int(max_order_count),
        "maximum_order_proportion": float(max_order_count / 50),
        "most_frequent_position_1_candidates": most_frequent_pos1,
        "most_frequently_included_candidates": most_frequent_included,
        "most_frequently_excluded_candidates": most_frequent_excluded,
        "minimum_cutoff_score_gap": float(cutoff_gaps.min()),
        "median_cutoff_score_gap": float(np.median(cutoff_gaps)),
        "mean_cutoff_score_gap": float(cutoff_gaps.mean()),
    }
    
    # By setting summary
    for experiment in EXPECTED_EXPERIMENTS:
        exp_events = events_df[events_df["experiment"] == experiment]
        unique_orders = set(exp_events["selected_order"])
        
        # Most frequent order
        exp_ordering = ordering_freq[(ordering_freq["scope"] == "by_setting") & (ordering_freq["experiment"] == experiment)]
        max_order_count = exp_ordering["count"].max()
        most_frequent_orders = exp_ordering[exp_ordering["count"] == max_order_count]["selected_order"].tolist()
        
        # Most frequent position 1 candidate
        exp_pos1 = position_freq[(position_freq["scope"] == "by_setting") & (position_freq["experiment"] == experiment) & (position_freq["position"] == 1)]
        max_pos1_count = exp_pos1["count"].max()
        most_frequent_pos1 = exp_pos1[exp_pos1["count"] == max_pos1_count]["candidate"].tolist()
        
        # Most frequently included
        exp_candidate = candidate_freq[(candidate_freq["scope"] == "by_setting") & (candidate_freq["experiment"] == experiment)]
        max_membership = exp_candidate["membership_count"].max()
        most_frequent_included = exp_candidate[exp_candidate["membership_count"] == max_membership]["candidate"].tolist()
        
        # Most frequently excluded
        max_exclusion = exp_candidate["exclusion_count"].max()
        most_frequent_excluded = exp_candidate[exp_candidate["exclusion_count"] == max_exclusion]["candidate"].tolist()
        
        # Cutoff score gaps
        cutoff_gaps = exp_events["cutoff_score_gap"].values
        
        summary["by_setting"][experiment] = {
            "unique_observed_order_count": len(unique_orders),
            "most_frequent_orders": most_frequent_orders,
            "maximum_order_count": int(max_order_count),
            "maximum_order_proportion": float(max_order_count / 25),
            "most_frequent_position_1_candidates": most_frequent_pos1,
            "most_frequently_included_candidates": most_frequent_included,
            "most_frequently_excluded_candidates": most_frequent_excluded,
            "minimum_cutoff_score_gap": float(cutoff_gaps.min()),
            "median_cutoff_score_gap": float(np.median(cutoff_gaps)),
            "mean_cutoff_score_gap": float(cutoff_gaps.mean()),
        }
    
    print("Descriptive summary computed.")
    return summary


def save_reports(provenance, integrity_results, candidate_freq, position_freq, ordering_freq, summary):
    """Save JSON and Markdown reports."""
    print("Saving reports...")
    
    # Build JSON report
    report = {
        "canonical_verification": {
            "manifest_validation_status": "all_checks_passed",
            "repeated_results_sha256_verified": True,
            "validation_log_sha256_verified": True,
            "evaluation_script_sha256_verified": True,
        },
        "algorithm_provenance": provenance,
        "selection_integrity": integrity_results,
        "candidate_frequency": candidate_freq.to_dict(orient="records"),
        "position_frequency": position_freq.to_dict(orient="records"),
        "ordering_frequency": ordering_freq.to_dict(orient="records"),
        "descriptive_summary": summary,
        "validation_checks": {
            "canonical_sha_checks_passed": True,
            "algorithm_provenance_checks_passed": all(provenance.values()),
            "selection_integrity_checks_passed": all(
                integrity_results[k] == 0 for k in [
                    "order_mismatches",
                    "membership_mismatches",
                    "excluded_candidate_mismatches",
                    "balanced_top1_consistency_mismatches",
                    "selection_mode_mismatches",
                    "invalid_thresholds",
                    "invalid_selection_scores",
                ]
            ),
            "candidate_frequency_checks_passed": True,
            "position_frequency_checks_passed": True,
            "ordering_frequency_checks_passed": True,
        },
    }
    
    with open(OUTPUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    
    # Build Markdown report
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 2 Section 3A: Soft-Top-3 Composition Frequency Analysis\n\n")
        
        f.write("## Canonical Verification\n\n")
        f.write("- Manifest validation status: all_checks_passed\n")
        f.write("- Repeated results SHA-256 verified: True\n")
        f.write("- Validation log SHA-256 verified: True\n")
        f.write("- Evaluation script SHA-256 verified: True\n\n")
        
        f.write("## Soft-Top-3 Algorithm Provenance\n\n")
        f.write(f"- Balanced objective sort verified: {provenance['balanced_objective_sort_verified']}\n")
        f.write(f"- Top-three slice verified: {provenance['top_three_slice_verified']}\n")
        f.write(f"- Validation mean verified: {provenance['validation_mean_verified']}\n")
        f.write(f"- Balanced threshold retuning verified: {provenance['balanced_threshold_retuning_verified']}\n")
        f.write(f"- Test mean verified: {provenance['test_mean_verified']}\n")
        f.write(f"- Pipe order storage verified: {provenance['pipe_order_storage_verified']}\n")
        f.write(f"- Selection mode verified: {provenance['selection_mode_verified']}\n\n")
        
        f.write("## Selection-Integrity Validation\n\n")
        f.write(f"- **Runs checked:** {integrity_results['runs_checked']}\n")
        f.write(f"- **Order mismatches:** {integrity_results['order_mismatches']}\n")
        f.write(f"- **Membership mismatches:** {integrity_results['membership_mismatches']}\n")
        f.write(f"- **Excluded candidate mismatches:** {integrity_results['excluded_candidate_mismatches']}\n")
        f.write(f"- **Balanced top-1 consistency mismatches:** {integrity_results['balanced_top1_consistency_mismatches']}\n")
        f.write(f"- **Selection mode mismatches:** {integrity_results['selection_mode_mismatches']}\n")
        f.write(f"- **Invalid thresholds:** {integrity_results['invalid_thresholds']}\n")
        f.write(f"- **Invalid selection scores:** {integrity_results['invalid_selection_scores']}\n\n")
        
        f.write("## Tie and Cutoff Diagnostics\n\n")
        f.write(f"- **Exact score-tie runs:** {integrity_results['exact_score_tie_runs']}\n")
        f.write(f"- **Near score-tie runs (within 1e-12):** {integrity_results['near_score_tie_runs_within_1e-12']}\n")
        f.write(f"- **Cutoff near-tie runs (within 1e-12):** {integrity_results['cutoff_near_tie_runs_within_1e-12']}\n\n")
        
        f.write("## Candidate Membership and Exclusion Frequency\n\n")
        f.write("### Overall\n\n")
        f.write("| Candidate | Membership Count | Exclusion Count | Denominator | Membership Prop | Exclusion Prop |\n")
        f.write("|-----------|-----------------|-----------------|------------|----------------|----------------|\n")
        overall_candidate = candidate_freq[candidate_freq["scope"] == "overall"]
        for _, row in overall_candidate.iterrows():
            f.write(f"| {row['candidate']} | {row['membership_count']} | {row['exclusion_count']} | {row['denominator']} | {row['membership_proportion']:.3f} | {row['exclusion_proportion']:.3f} |\n")
        f.write("\n")
        
        f.write("## Position Frequency\n\n")
        f.write("### Overall\n\n")
        f.write("| Position | Candidate | Count | Denominator | Proportion |\n")
        f.write("|----------|-----------|-------|------------|------------|\n")
        overall_position = position_freq[position_freq["scope"] == "overall"]
        for _, row in overall_position.iterrows():
            f.write(f"| {row['position']} | {row['candidate']} | {row['count']} | {row['denominator']} | {row['proportion']:.3f} |\n")
        f.write("\n")
        
        f.write("## Ordering Frequency\n\n")
        f.write("### Overall\n\n")
        f.write("| Order | Count | Denominator | Proportion |\n")
        f.write("|-------|-------|------------|------------|\n")
        overall_ordering = ordering_freq[ordering_freq["scope"] == "overall"]
        for _, row in overall_ordering.iterrows():
            if row["count"] > 0:
                f.write(f"| {row['selected_order']} | {row['count']} | {row['denominator']} | {row['proportion']:.3f} |\n")
        f.write("\n")
        
        f.write("## Descriptive Summary\n\n")
        f.write("### Overall\n\n")
        f.write(f"- **Unique observed orders:** {summary['overall']['unique_observed_order_count']}\n")
        f.write(f"- **Most frequent order(s):** {', '.join(summary['overall']['most_frequent_orders'])}\n")
        f.write(f"- **Maximum order count:** {summary['overall']['maximum_order_count']}\n")
        f.write(f"- **Maximum order proportion:** {summary['overall']['maximum_order_proportion']:.3f}\n")
        f.write(f"- **Most frequent position-1 candidate(s):** {', '.join(summary['overall']['most_frequent_position_1_candidates'])}\n")
        f.write(f"- **Most frequently included candidate(s):** {', '.join(summary['overall']['most_frequently_included_candidates'])}\n")
        f.write(f"- **Most frequently excluded candidate(s):** {', '.join(summary['overall']['most_frequently_excluded_candidates'])}\n")
        f.write(f"- **Minimum cutoff score gap:** {summary['overall']['minimum_cutoff_score_gap']:.6f}\n")
        f.write(f"- **Median cutoff score gap:** {summary['overall']['median_cutoff_score_gap']:.6f}\n")
        f.write(f"- **Mean cutoff score gap:** {summary['overall']['mean_cutoff_score_gap']:.6f}\n\n")
        
        f.write("### By Setting\n\n")
        for experiment in EXPECTED_EXPERIMENTS:
            data = summary["by_setting"][experiment]
            f.write(f"**{experiment}:**\n")
            f.write(f"- Unique observed orders: {data['unique_observed_order_count']}\n")
            f.write(f"- Most frequent order(s): {', '.join(data['most_frequent_orders'])}\n")
            f.write(f"- Maximum order count: {data['maximum_order_count']}\n")
            f.write(f"- Maximum order proportion: {data['maximum_order_proportion']:.3f}\n")
            f.write(f"- Most frequent position-1 candidate(s): {', '.join(data['most_frequent_position_1_candidates'])}\n")
            f.write(f"- Most frequently included candidate(s): {', '.join(data['most_frequently_included_candidates'])}\n")
            f.write(f"- Most frequently excluded candidate(s): {', '.join(data['most_frequently_excluded_candidates'])}\n")
            f.write(f"- Minimum cutoff score gap: {data['minimum_cutoff_score_gap']:.6f}\n")
            f.write(f"- Median cutoff score gap: {data['median_cutoff_score_gap']:.6f}\n")
            f.write(f"- Mean cutoff score gap: {data['mean_cutoff_score_gap']:.6f}\n\n")
        
        f.write("## Reconstruction Limitations\n\n")
        f.write("The stored aggregate outputs permit independent verification of selected membership and order from balanced validation scores, but they do not permit independent reconstruction of the ensemble threshold or ensemble validation objective without sample-level validation probabilities.\n\n")
        
        f.write("## Interpretation Limits\n\n")
        f.write("These are descriptive frequencies of Soft-top-3 composition across 50 runs.\n")
        f.write("They do not establish statistical significance, performance superiority, or causal effects.\n\n")
    
    print("Reports saved.")


def main():
    """Main entry point."""
    print("Starting soft-top-3 composition frequency analysis...\n")
    
    # Load and verify inputs
    repeated_df, validation_df, evaluation_script = load_and_verify_inputs()
    
    # Verify algorithm provenance
    provenance = verify_algorithm_provenance(evaluation_script)
    
    # Extract soft-top-3 events
    soft_top3_df = extract_soft_top3_events(repeated_df)
    
    # Validate selection integrity
    integrity_results = validate_selection_integrity(soft_top3_df, validation_df, repeated_df)
    
    # Save selection events
    events_df = save_selection_events(soft_top3_df, validation_df)
    
    # Compute frequencies
    candidate_freq = compute_candidate_frequency(events_df)
    position_freq = compute_position_frequency(events_df)
    ordering_freq = compute_ordering_frequency(events_df)
    
    # Compute descriptive summary
    summary = compute_descriptive_summary(events_df, candidate_freq, position_freq, ordering_freq)
    
    # Save reports
    save_reports(provenance, integrity_results, candidate_freq, position_freq, ordering_freq, summary)
    
    # Final validation checks
    print("\nPerforming final validation checks...")
    
    # Verify output row counts
    if len(events_df) != 50:
        raise ValueError(f"Expected 50 event rows, got {len(events_df)}")
    if len(events_df.columns) != 16:
        raise ValueError(f"Expected 16 event columns, got {len(events_df.columns)}")
    if len(candidate_freq) != 52:
        raise ValueError(f"Expected 52 candidate-frequency rows, got {len(candidate_freq)}")
    if len(position_freq) != 36:
        raise ValueError(f"Expected 36 position-frequency rows, got {len(position_freq)}")
    if len(ordering_freq) != 72:
        raise ValueError(f"Expected 72 ordering-frequency rows, got {len(ordering_freq)}")
    
    # Verify selection-integrity mismatches are zero
    if integrity_results["order_mismatches"] != 0:
        raise ValueError(f"Order mismatches: {integrity_results['order_mismatches']}")
    if integrity_results["membership_mismatches"] != 0:
        raise ValueError(f"Membership mismatches: {integrity_results['membership_mismatches']}")
    if integrity_results["excluded_candidate_mismatches"] != 0:
        raise ValueError(f"Excluded candidate mismatches: {integrity_results['excluded_candidate_mismatches']}")
    if integrity_results["balanced_top1_consistency_mismatches"] != 0:
        raise ValueError(f"Balanced top-1 consistency mismatches: {integrity_results['balanced_top1_consistency_mismatches']}")
    if integrity_results["selection_mode_mismatches"] != 0:
        raise ValueError(f"Selection mode mismatches: {integrity_results['selection_mode_mismatches']}")
    if integrity_results["invalid_thresholds"] != 0:
        raise ValueError(f"Invalid thresholds: {integrity_results['invalid_thresholds']}")
    if integrity_results["invalid_selection_scores"] != 0:
        raise ValueError(f"Invalid selection scores: {integrity_results['invalid_selection_scores']}")
    
    # Verify algorithm provenance checks
    if not all(provenance.values()):
        raise ValueError("Algorithm provenance checks failed")
    
    print("Final validation checks passed.")
    
    print("\nSoft-top-3 composition frequency analysis complete!")
    print(f"\nSummary:")
    print(f"  Runs checked: {integrity_results['runs_checked']}")
    print(f"  Selection-integrity mismatches: 0")
    print(f"  Balanced top-1 consistency mismatches: {integrity_results['balanced_top1_consistency_mismatches']}")
    print(f"  Exact score-tie runs: {integrity_results['exact_score_tie_runs']}")
    print(f"  Near score-tie runs: {integrity_results['near_score_tie_runs_within_1e-12']}")
    print(f"  Cutoff near-tie runs: {integrity_results['cutoff_near_tie_runs_within_1e-12']}")
    print(f"  Event rows: {len(events_df)}")
    print(f"  Candidate-frequency rows: {len(candidate_freq)}")
    print(f"  Position-frequency rows: {len(position_freq)}")
    print(f"  Ordering-frequency rows: {len(ordering_freq)}")
    print(f"  Unique observed orders overall: {summary['overall']['unique_observed_order_count']}")
    print(f"  Most frequent order(s) overall: {', '.join(summary['overall']['most_frequent_orders'])}")
    print(f"  Most frequently included candidate(s): {', '.join(summary['overall']['most_frequently_included_candidates'])}")
    print(f"  Most frequently excluded candidate(s): {', '.join(summary['overall']['most_frequently_excluded_candidates'])}")
    print(f"  Minimum cutoff score gap: {summary['overall']['minimum_cutoff_score_gap']:.6f}")


if __name__ == "__main__":
    main()
