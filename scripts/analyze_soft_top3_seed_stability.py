#!/usr/bin/env python3
"""
Part 2 Section 3D: Analyze soft-top-3 seed stability
Computes descriptive stability metrics for soft-top-3 candidate selections across five seeds.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import hashlib
from itertools import permutations, combinations

# Base directory for portable paths
BASE_DIR = Path(__file__).resolve().parents[1]

# Paths
CANONICAL_RESULT_DIR = BASE_DIR / "results" / "part1_full_reproduction"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_DIR = BASE_DIR / "results" / "part2_candidate_selection"

# Input files
MANIFEST_PATH = REPORTS_DIR / "part1_canonical_manifest.json"
COMPOSITION_FREQ_JSON = REPORTS_DIR / "part2_soft_top3_composition_frequency.json"
EVENTS_PATH = OUTPUT_DIR / "soft_top3_selection_events.csv"
REPEATED_RESULTS_PATH = CANONICAL_RESULT_DIR / "repeated_all_results.csv"
VALIDATION_LOG_PATH = CANONICAL_RESULT_DIR / "validation_log.csv"

# Output files
OUTPUT_ORDER_COUNTS = OUTPUT_DIR / "soft_top3_seed_stability_order_counts.csv"
OUTPUT_MEMBERSHIP_COUNTS = OUTPUT_DIR / "soft_top3_seed_stability_membership_counts.csv"
OUTPUT_GROUP_STABILITY = OUTPUT_DIR / "soft_top3_seed_stability_by_group.csv"
OUTPUT_SUMMARY = OUTPUT_DIR / "soft_top3_seed_stability_summary.csv"
OUTPUT_JSON = REPORTS_DIR / "part2_soft_top3_seed_stability.json"
OUTPUT_MD = REPORTS_DIR / "part2_soft_top3_seed_stability.md"

# Constants
BASELINE_MODELS = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
CANDIDATE_ORDER = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
EXPECTED_EXPERIMENTS = ["within_project", "cross_project"]
EXPECTED_PROJECTS = ["CM1", "JM1", "KC1", "KC2", "PC1"]
EXPECTED_SEEDS = [7, 13, 29, 42, 101]
SOFT_TOP3_MODEL = "AQRPE_v2_soft_top3"
EXPECTED_SELECTION_MODE = "soft_top3_balanced_objective"

# Reference orderings
ALL_SELECTED_ORDERS = [
    "|".join(order)
    for order in permutations(CANDIDATE_ORDER, 3)
]

MEMBERSHIP_OPTIONS = []

for excluded_candidate in CANDIDATE_ORDER:
    members = [
        candidate
        for candidate in CANDIDATE_ORDER
        if candidate != excluded_candidate
    ]

    membership_set = "|".join(members)

    MEMBERSHIP_OPTIONS.append({
        "membership_set": membership_set,
        "excluded_candidate": excluded_candidate,
    })

MEMBERSHIP_ORDER = [
    item["membership_set"]
    for item in MEMBERSHIP_OPTIONS
]

MEMBERSHIP_TO_EXCLUDED = {
    item["membership_set"]: item["excluded_candidate"]
    for item in MEMBERSHIP_OPTIONS
}

# Tolerance for floating point comparisons
TOLERANCE = 1e-12


def compute_sha256(file_path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_and_verify_inputs():
    """Load and verify all input files."""
    print("Loading and verifying inputs...")
    
    # Load manifest
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    
    # Load composition frequency report
    with open(COMPOSITION_FREQ_JSON, "r") as f:
        composition_report = json.load(f)
    
    # Verify manifest status
    if manifest.get("manifest_validation_status") != "all_checks_passed":
        raise ValueError(f"Manifest validation status is '{manifest.get('manifest_validation_status')}', expected 'all_checks_passed'")
    
    # Verify canonical verification from composition report
    canonical_verification = composition_report["canonical_verification"]
    if not canonical_verification["repeated_results_sha256_verified"]:
        raise ValueError("Repeated results SHA-256 not verified")
    if not canonical_verification["validation_log_sha256_verified"]:
        raise ValueError("Validation log SHA-256 not verified")
    if not canonical_verification["evaluation_script_sha256_verified"]:
        raise ValueError("Evaluation script SHA-256 not verified")
    
    # Verify selection integrity from composition report
    selection_integrity = composition_report["selection_integrity"]
    if selection_integrity["runs_checked"] != 50:
        raise ValueError(f"Expected 50 runs checked, got {selection_integrity['runs_checked']}")
    if selection_integrity["order_mismatches"] != 0:
        raise ValueError(f"Order mismatches: {selection_integrity['order_mismatches']}")
    if selection_integrity["membership_mismatches"] != 0:
        raise ValueError(f"Membership mismatches: {selection_integrity['membership_mismatches']}")
    if selection_integrity["excluded_candidate_mismatches"] != 0:
        raise ValueError(f"Excluded candidate mismatches: {selection_integrity['excluded_candidate_mismatches']}")
    if selection_integrity["balanced_top1_consistency_mismatches"] != 0:
        raise ValueError(f"Balanced top-1 consistency mismatches: {selection_integrity['balanced_top1_consistency_mismatches']}")
    if selection_integrity["selection_mode_mismatches"] != 0:
        raise ValueError(f"Selection mode mismatches: {selection_integrity['selection_mode_mismatches']}")
    if selection_integrity["invalid_thresholds"] != 0:
        raise ValueError(f"Invalid thresholds: {selection_integrity['invalid_thresholds']}")
    if selection_integrity["invalid_selection_scores"] != 0:
        raise ValueError(f"Invalid selection scores: {selection_integrity['invalid_selection_scores']}")
    
    # Verify validation checks from composition report
    validation_checks = composition_report["validation_checks"]
    if not validation_checks["canonical_sha_checks_passed"]:
        raise ValueError("Canonical SHA checks not passed")
    if not validation_checks["algorithm_provenance_checks_passed"]:
        raise ValueError("Algorithm provenance checks not passed")
    if not validation_checks["selection_integrity_checks_passed"]:
        raise ValueError("Selection integrity checks not passed")
    if not validation_checks["candidate_frequency_checks_passed"]:
        raise ValueError("Candidate frequency checks not passed")
    if not validation_checks["position_frequency_checks_passed"]:
        raise ValueError("Position frequency checks not passed")
    if not validation_checks["ordering_frequency_checks_passed"]:
        raise ValueError("Ordering frequency checks not passed")
    
    # Load data files
    events_df = pd.read_csv(EVENTS_PATH)
    repeated_df = pd.read_csv(REPEATED_RESULTS_PATH)
    validation_df = pd.read_csv(VALIDATION_LOG_PATH)
    
    # Direct SHA verification of input files
    expected_repeated_sha = manifest["canonical_reproduction_outputs"]["repeated_all_results.csv"]["sha256"]
    actual_repeated_sha = compute_sha256(REPEATED_RESULTS_PATH)
    repeated_results_sha256_verified = (expected_repeated_sha == actual_repeated_sha)
    
    expected_validation_sha = manifest["canonical_reproduction_outputs"]["validation_log.csv"]["sha256"]
    actual_validation_sha = compute_sha256(VALIDATION_LOG_PATH)
    validation_log_sha256_verified = (expected_validation_sha == actual_validation_sha)
    
    expected_eval_script_sha = manifest["environment_and_code_files"]["run_repeated_evaluation.py"]["sha256"]
    actual_eval_script_sha = compute_sha256(BASE_DIR / "scripts" / "run_repeated_evaluation.py")
    evaluation_script_sha256_verified = (expected_eval_script_sha == actual_eval_script_sha)
    
    if not repeated_results_sha256_verified:
        raise ValueError(f"Repeated results SHA-256 mismatch: expected {expected_repeated_sha}, got {actual_repeated_sha}")
    if not validation_log_sha256_verified:
        raise ValueError(f"Validation log SHA-256 mismatch: expected {expected_validation_sha}, got {actual_validation_sha}")
    if not evaluation_script_sha256_verified:
        raise ValueError(f"Evaluation script SHA-256 mismatch: expected {expected_eval_script_sha}, got {actual_eval_script_sha}")
    
    canonical_verification = {
        "manifest_validation_status": manifest.get("manifest_validation_status"),
        "repeated_results_sha256_verified": repeated_results_sha256_verified,
        "validation_log_sha256_verified": validation_log_sha256_verified,
        "evaluation_script_sha256_verified": evaluation_script_sha256_verified,
    }
    
    print("Inputs verified.")
    return events_df, repeated_df, validation_df, canonical_verification


def verify_event_schema(events_df):
    """Verify event file schema and content."""
    print("Verifying event schema...")
    
    # Expected columns
    expected_columns = [
        "experiment", "target_project", "seed", "selected_order",
        "position_1_candidate", "position_2_candidate", "position_3_candidate",
        "excluded_candidate", "selection_mode", "threshold", "selection_score",
        "balanced_score_position_1", "balanced_score_position_2",
        "balanced_score_position_3", "balanced_score_excluded", "cutoff_score_gap"
    ]
    
    if list(events_df.columns) != expected_columns:
        raise ValueError(f"Column mismatch: expected {expected_columns}, got {list(events_df.columns)}")
    
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
    
    # Verify experiments
    experiments = set(events_df["experiment"].unique())
    if experiments != set(EXPECTED_EXPERIMENTS):
        raise ValueError(f"Experiments mismatch: expected {EXPECTED_EXPERIMENTS}, got {experiments}")
    
    # Verify projects
    projects = set(events_df["target_project"].unique())
    if projects != set(EXPECTED_PROJECTS):
        raise ValueError(f"Projects mismatch: expected {EXPECTED_PROJECTS}, got {projects}")
    
    # Verify seeds
    seeds = set(events_df["seed"].unique())
    if seeds != set(EXPECTED_SEEDS):
        raise ValueError(f"Seeds mismatch: expected {EXPECTED_SEEDS}, got {seeds}")
    
    # Verify each row
    for _, row in events_df.iterrows():
        selected_order = row["selected_order"]
        position_1 = row["position_1_candidate"]
        position_2 = row["position_2_candidate"]
        position_3 = row["position_3_candidate"]
        excluded = row["excluded_candidate"]
        
        # Check selected_order matches positions
        expected_order = f"{position_1}|{position_2}|{position_3}"
        if selected_order != expected_order:
            raise ValueError(f"Selected order mismatch: {selected_order} vs {expected_order}")
        
        # Check positions are distinct
        positions = [position_1, position_2, position_3]
        if len(set(positions)) != 3:
            raise ValueError(f"Positions not distinct: {positions}")
        
        # Check all positions are baseline models
        if not all(p in BASELINE_MODELS for p in positions):
            raise ValueError(f"Invalid position candidates: {positions}")
        
        # Check excluded is baseline model
        if excluded not in BASELINE_MODELS:
            raise ValueError(f"Invalid excluded candidate: {excluded}")
        
        # Check all four candidates are covered
        all_candidates = set(positions + [excluded])
        if all_candidates != set(CANDIDATE_ORDER):
            raise ValueError(f"Candidate set mismatch: {all_candidates} vs {set(CANDIDATE_ORDER)}")
        
        # Check score ordering
        score_1 = row["balanced_score_position_1"]
        score_2 = row["balanced_score_position_2"]
        score_3 = row["balanced_score_position_3"]
        score_excluded = row["balanced_score_excluded"]
        
        if not (score_1 > score_2 > score_3 > score_excluded):
            raise ValueError(f"Score ordering violation: {score_1} > {score_2} > {score_3} > {score_excluded}")
        
        # Check cutoff gap
        expected_gap = score_3 - score_excluded
        actual_gap = row["cutoff_score_gap"]
        if abs(actual_gap - expected_gap) > TOLERANCE:
            raise ValueError(f"Cutoff gap mismatch: {actual_gap} vs {expected_gap}")
    
    print("Event schema verified.")
    return events_df


def verify_event_provenance(events_df, repeated_df, validation_df):
    """Verify events against canonical results and validation rankings."""
    print("Verifying event provenance...")
    
    results = {
        "events_checked": 0,
        "canonical_event_mismatches": 0,
        "validation_ranking_mismatches": 0,
        "score_mismatches": 0,
        "cutoff_gap_mismatches": 0,
    }
    
    for _, event_row in events_df.iterrows():
        results["events_checked"] += 1
        
        experiment = event_row["experiment"]
        target_project = event_row["target_project"]
        seed = event_row["seed"]
        selected_order = event_row["selected_order"]
        selection_mode = event_row["selection_mode"]
        threshold = event_row["threshold"]
        selection_score = event_row["selection_score"]
        
        # Verify against canonical repeated results
        canonical_row = repeated_df[
            (repeated_df["experiment"] == experiment) &
            (repeated_df["target_project"] == target_project) &
            (repeated_df["seed"] == seed) &
            (repeated_df["model"] == SOFT_TOP3_MODEL)
        ]
        
        if len(canonical_row) != 1:
            raise ValueError(f"Expected 1 canonical row for {experiment}/{target_project}/{seed}, got {len(canonical_row)}")
        
        canonical = canonical_row.iloc[0]
        
        if canonical["selected_candidate"] != selected_order:
            results["canonical_event_mismatches"] += 1
        
        if canonical["selection_mode"] != selection_mode:
            results["canonical_event_mismatches"] += 1
        
        if abs(canonical["threshold"] - threshold) > TOLERANCE:
            results["canonical_event_mismatches"] += 1
        
        if abs(canonical["selection_score"] - selection_score) > TOLERANCE:
            results["canonical_event_mismatches"] += 1
        
        # Verify against validation rankings
        val_subset = validation_df[
            (validation_df["experiment"] == experiment) &
            (validation_df["target_project"] == target_project) &
            (validation_df["seed"] == seed) &
            (validation_df["mode"] == "balanced")
        ]
        
        if len(val_subset) != 4:
            raise ValueError(f"Expected 4 validation rows for {experiment}/{target_project}/{seed}, got {len(val_subset)}")
        
        val_scores = {}
        for _, val_row in val_subset.iterrows():
            val_scores[val_row["candidate"]] = val_row["val_selection_score"]
        
        # Reconstruct ranking
        sorted_candidates = sorted(
            BASELINE_MODELS,
            key=lambda c: (-val_scores[c], CANDIDATE_ORDER.index(c))
        )
        
        # Verify positions and scores
        position_1 = event_row["position_1_candidate"]
        position_2 = event_row["position_2_candidate"]
        position_3 = event_row["position_3_candidate"]
        excluded = event_row["excluded_candidate"]
        
        if sorted_candidates[:3] != [position_1, position_2, position_3]:
            results["validation_ranking_mismatches"] += 1
        
        if sorted_candidates[3] != excluded:
            results["validation_ranking_mismatches"] += 1
        
        # Verify scores
        if abs(val_scores[position_1] - event_row["balanced_score_position_1"]) > TOLERANCE:
            results["score_mismatches"] += 1
        if abs(val_scores[position_2] - event_row["balanced_score_position_2"]) > TOLERANCE:
            results["score_mismatches"] += 1
        if abs(val_scores[position_3] - event_row["balanced_score_position_3"]) > TOLERANCE:
            results["score_mismatches"] += 1
        if abs(val_scores[excluded] - event_row["balanced_score_excluded"]) > TOLERANCE:
            results["score_mismatches"] += 1
        
        # Verify cutoff gap
        expected_gap = val_scores[sorted_candidates[2]] - val_scores[sorted_candidates[3]]
        if abs(expected_gap - event_row["cutoff_score_gap"]) > TOLERANCE:
            results["cutoff_gap_mismatches"] += 1
    
    # Check all mismatches are zero
    if results["canonical_event_mismatches"] > 0:
        raise ValueError(f"Canonical event mismatches: {results['canonical_event_mismatches']}")
    if results["validation_ranking_mismatches"] > 0:
        raise ValueError(f"Validation ranking mismatches: {results['validation_ranking_mismatches']}")
    if results["score_mismatches"] > 0:
        raise ValueError(f"Score mismatches: {results['score_mismatches']}")
    if results["cutoff_gap_mismatches"] > 0:
        raise ValueError(f"Cutoff gap mismatches: {results['cutoff_gap_mismatches']}")
    
    print("Event provenance verified.")
    return results


def compute_order_counts(events_df):
    """Compute order counts for each group."""
    print("Computing order counts...")
    
    # Generate all possible orders (4P3 = 24)
    all_orderings = list(permutations(BASELINE_MODELS, 3))
    all_ordering_strs = ["|".join(ordering) for ordering in all_orderings]
    
    order_rows = []
    
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            group_events = events_df[
                (events_df["experiment"] == experiment) &
                (events_df["target_project"] == project)
            ]
            
            if len(group_events) != 5:
                raise ValueError(f"Expected 5 events for {experiment}/{project}, got {len(group_events)}")
            
            for ordering in all_ordering_strs:
                count = sum(1 for _, row in group_events.iterrows() if row["selected_order"] == ordering)
                
                order_rows.append({
                    "experiment": experiment,
                    "target_project": project,
                    "selected_order": ordering,
                    "count": count,
                    "denominator": 5,
                    "proportion": count / 5,
                })
    
    order_counts_df = pd.DataFrame(order_rows)
    
    # Verify row count
    if len(order_counts_df) != 240:
        raise ValueError(f"Expected 240 order-count rows, got {len(order_counts_df)}")
    
    # Verify sums for each group
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            subset = order_counts_df[
                (order_counts_df["experiment"] == experiment) &
                (order_counts_df["target_project"] == project)
            ]
            subset_sum = subset["count"].sum()
            if subset_sum != 5:
                raise ValueError(f"Expected sum 5 for {experiment}/{project}, got {subset_sum}")
            subset_prop_sum = subset["proportion"].sum()
            if abs(subset_prop_sum - 1.0) > TOLERANCE:
                raise ValueError(f"Expected proportion sum 1.0 for {experiment}/{project}, got {subset_prop_sum}")
    
    # Sort
    order_counts_df = order_counts_df.sort_values(["experiment", "target_project", "selected_order"])
    
    print("Order counts computed.")
    return order_counts_df


def compute_membership_counts(events_df):
    """Compute membership counts for each group."""
    print("Computing membership counts...")
    
    # Generate all possible membership sets (4 choose 3 = 4)
    membership_rows = []
    
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            group_events = events_df[
                (events_df["experiment"] == experiment) &
                (events_df["target_project"] == project)
            ]
            
            if len(group_events) != 5:
                raise ValueError(f"Expected 5 events for {experiment}/{project}, got {len(group_events)}")
            
            for excluded_candidate in BASELINE_MODELS:
                # Build membership set (all candidates except excluded)
                membership_set = [c for c in CANDIDATE_ORDER if c != excluded_candidate]
                membership_set_str = "|".join(membership_set)
                
                count = sum(1 for _, row in group_events.iterrows() if row["excluded_candidate"] == excluded_candidate)
                
                membership_rows.append({
                    "experiment": experiment,
                    "target_project": project,
                    "membership_set": membership_set_str,
                    "excluded_candidate": excluded_candidate,
                    "count": count,
                    "denominator": 5,
                    "proportion": count / 5,
                })
    
    membership_counts_df = pd.DataFrame(membership_rows)
    
    # Verify row count
    if len(membership_counts_df) != 40:
        raise ValueError(f"Expected 40 membership-count rows, got {len(membership_counts_df)}")
    
    # Verify sums for each group
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            subset = membership_counts_df[
                (membership_counts_df["experiment"] == experiment) &
                (membership_counts_df["target_project"] == project)
            ]
            subset_sum = subset["count"].sum()
            if subset_sum != 5:
                raise ValueError(f"Expected sum 5 for {experiment}/{project}, got {subset_sum}")
            subset_prop_sum = subset["proportion"].sum()
            if abs(subset_prop_sum - 1.0) > TOLERANCE:
                raise ValueError(f"Expected proportion sum 1.0 for {experiment}/{project}, got {subset_prop_sum}")
    
    # Sort
    membership_counts_df = membership_counts_df.sort_values(["experiment", "target_project", "membership_set"])
    
    # Validate membership mapping
    for _, row in membership_counts_df.iterrows():
        membership_set = row["membership_set"]
        excluded_candidate = row["excluded_candidate"]
        
        members = membership_set.split("|")
        
        if set(members) | {excluded_candidate} != set(CANDIDATE_ORDER):
            raise ValueError(f"Membership set + excluded != all candidates for {membership_set}/{excluded_candidate}")
        if set(members) & {excluded_candidate}:
            raise ValueError(f"Membership set intersects with excluded for {membership_set}/{excluded_candidate}")
        if len(members) != 3:
            raise ValueError(f"Membership set has wrong size: {len(members)}")
        if len(set(members)) != 3:
            raise ValueError(f"Membership set has duplicates: {members}")
        if MEMBERSHIP_TO_EXCLUDED[membership_set] != excluded_candidate:
            raise ValueError(f"Membership mapping mismatch for {membership_set}/{excluded_candidate}")
    
    print("Membership counts computed.")
    return membership_counts_df


def compute_pairwise_metrics(group_events):
    """Compute pairwise stability metrics for a group of 5 seeds."""
    # Extract selected orders and membership sets
    selected_orders = group_events["selected_order"].tolist()
    excluded_candidates = group_events["excluded_candidate"].tolist()
    
    # Build membership sets
    membership_sets = []
    for excluded in excluded_candidates:
        membership = [c for c in CANDIDATE_ORDER if c != excluded]
        membership_sets.append("|".join(membership))
    
    # Build full orders (4 candidates)
    full_orders = []
    for _, row in group_events.iterrows():
        full_order = f"{row['position_1_candidate']}|{row['position_2_candidate']}|{row['position_3_candidate']}|{row['excluded_candidate']}"
        full_orders.append(full_order)
    
    # Exact order agreement
    exact_order_agreements = []
    for i in range(5):
        for j in range(i + 1, 5):
            exact_order_agreements.append(1 if selected_orders[i] == selected_orders[j] else 0)
    exact_order_pairwise_agreement = sum(exact_order_agreements) / 10
    
    # Exact membership agreement
    exact_membership_agreements = []
    for i in range(5):
        for j in range(i + 1, 5):
            exact_membership_agreements.append(1 if membership_sets[i] == membership_sets[j] else 0)
    exact_membership_pairwise_agreement = sum(exact_membership_agreements) / 10
    
    # Jaccard similarity
    jaccard_similarities = []
    for i in range(5):
        for j in range(i + 1, 5):
            set_i = set(membership_sets[i].split("|"))
            set_j = set(membership_sets[j].split("|"))
            intersection = len(set_i & set_j)
            union = len(set_i | set_j)
            jaccard = intersection / union
            jaccard_similarities.append(jaccard)
    mean_pairwise_jaccard = sum(jaccard_similarities) / 10
    
    # Full-rank position agreement
    position_agreements = []
    for i in range(5):
        for j in range(i + 1, 5):
            order_i = full_orders[i].split("|")
            order_j = full_orders[j].split("|")
            same_position = sum(1 for k in range(4) if order_i[k] == order_j[k])
            position_agreements.append(same_position / 4)
    mean_full_rank_position_agreement = sum(position_agreements) / 10
    
    # Kendall tau for full ranking
    kendall_taus = []
    for i in range(5):
        for j in range(i + 1, 5):
            order_i = full_orders[i].split("|")
            order_j = full_orders[j].split("|")
            
            # Build rank dictionaries
            rank_i = {candidate: idx for idx, candidate in enumerate(order_i)}
            rank_j = {candidate: idx for idx, candidate in enumerate(order_j)}
            
            # Count concordant and discordant pairs
            concordant = 0
            discordant = 0
            for a, b in combinations(BASELINE_MODELS, 2):
                order_a_b_i = rank_i[a] < rank_i[b]
                order_a_b_j = rank_j[a] < rank_j[b]
                if order_a_b_i == order_a_b_j:
                    concordant += 1
                else:
                    discordant += 1
            
            kendall_tau = (concordant - discordant) / 6
            kendall_taus.append(kendall_tau)
    
    mean_pairwise_kendall_tau = sum(kendall_taus) / 10
    mean_pairwise_kendall_similarity = (mean_pairwise_kendall_tau + 1) / 2
    
    return {
        "exact_order_pairwise_agreement": exact_order_pairwise_agreement,
        "exact_membership_pairwise_agreement": exact_membership_pairwise_agreement,
        "mean_pairwise_jaccard": mean_pairwise_jaccard,
        "mean_full_rank_position_agreement": mean_full_rank_position_agreement,
        "mean_pairwise_kendall_tau": mean_pairwise_kendall_tau,
        "mean_pairwise_kendall_similarity": mean_pairwise_kendall_similarity,
    }


def compute_group_stability(events_df):
    """Compute group-level stability metrics."""
    print("Computing group stability...")
    
    group_rows = []
    
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            group_events = events_df[
                (events_df["experiment"] == experiment) &
                (events_df["target_project"] == project)
            ]
            
            if len(group_events) != 5:
                raise ValueError(f"Expected 5 events for {experiment}/{project}, got {len(group_events)}")
            
            # Distinct orders
            distinct_orders = set(group_events["selected_order"].tolist())
            
            # Modal orders
            order_counts = {}
            for order in group_events["selected_order"]:
                order_counts[order] = order_counts.get(order, 0) + 1
            max_order_count = max(order_counts.values())
            modal_orders = [order for order, count in order_counts.items() if count == max_order_count]
            modal_orders_sorted = sorted(modal_orders, key=ALL_SELECTED_ORDERS.index)
            
            # Distinct membership sets
            membership_sets = []
            for excluded in group_events["excluded_candidate"]:
                membership = [c for c in CANDIDATE_ORDER if c != excluded]
                membership_sets.append("|".join(membership))
            distinct_membership_sets = set(membership_sets)
            
            # Modal membership sets
            membership_counts = {}
            for ms in membership_sets:
                membership_counts[ms] = membership_counts.get(ms, 0) + 1
            max_membership_count = max(membership_counts.values())
            modal_membership_sets = [ms for ms, count in membership_counts.items() if count == max_membership_count]
            modal_membership_sets_sorted = sorted(modal_membership_sets, key=MEMBERSHIP_ORDER.index)
            modal_excluded_candidates = [
                MEMBERSHIP_TO_EXCLUDED[membership_set]
                for membership_set in modal_membership_sets_sorted
            ]
            modal_excluded_candidates = sorted(
                modal_excluded_candidates,
                key=CANDIDATE_ORDER.index,
            )
            
            # Cutoff score gaps
            cutoff_gaps = group_events["cutoff_score_gap"].values
            
            # Compute pairwise metrics
            pairwise_metrics = compute_pairwise_metrics(group_events)
            
            # Validate pairwise count formulas
            observed_order_counts_list = list(order_counts.values())
            expected_exact_order_agreement = sum(c * (c - 1) / 2 for c in observed_order_counts_list) / 10
            if abs(pairwise_metrics["exact_order_pairwise_agreement"] - expected_exact_order_agreement) > TOLERANCE:
                raise ValueError(f"Exact order agreement formula violation for {experiment}/{project}")
            
            observed_membership_counts_list = list(membership_counts.values())
            expected_exact_membership_agreement = sum(c * (c - 1) / 2 for c in observed_membership_counts_list) / 10
            if abs(pairwise_metrics["exact_membership_pairwise_agreement"] - expected_exact_membership_agreement) > TOLERANCE:
                raise ValueError(f"Exact membership agreement formula violation for {experiment}/{project}")
            
            # Build group row
            group_rows.append({
                "experiment": experiment,
                "target_project": project,
                "n_seeds": 5,
                "distinct_orders": len(distinct_orders),
                "modal_orders": "|OR|".join(modal_orders_sorted),
                "modal_order_count": max_order_count,
                "modal_order_proportion": max_order_count / 5,
                "order_modal_tie": len(modal_orders) > 1,
                "unanimous_order": max_order_count == 5,
                "distinct_membership_sets": len(distinct_membership_sets),
                "modal_membership_sets": "|OR|".join(modal_membership_sets_sorted),
                "modal_excluded_candidates": "|OR|".join(modal_excluded_candidates),
                "modal_membership_count": max_membership_count,
                "modal_membership_proportion": max_membership_count / 5,
                "membership_modal_tie": len(modal_membership_sets) > 1,
                "unanimous_membership": max_membership_count == 5,
                **pairwise_metrics,
                "minimum_cutoff_score_gap": float(cutoff_gaps.min()),
                "median_cutoff_score_gap": float(np.median(cutoff_gaps)),
                "mean_cutoff_score_gap": float(cutoff_gaps.mean()),
            })
    
    group_stability_df = pd.DataFrame(group_rows)
    
    # Verify row count
    if len(group_stability_df) != 10:
        raise ValueError(f"Expected 10 group-stability rows, got {len(group_stability_df)}")
    
    # Logical validation
    for _, row in group_stability_df.iterrows():
        if row["n_seeds"] != 5:
            raise ValueError(f"n_seeds != 5 for {row['experiment']}/{row['target_project']}")
        if not (1 <= row["distinct_orders"] <= 5):
            raise ValueError(f"distinct_orders out of range: {row['distinct_orders']}")
        if not (1 <= row["distinct_membership_sets"] <= 4):
            raise ValueError(f"distinct_membership_sets out of range: {row['distinct_membership_sets']}")
        if not (1 <= row["modal_order_count"] <= 5):
            raise ValueError(f"modal_order_count out of range: {row['modal_order_count']}")
        if not (1 <= row["modal_membership_count"] <= 5):
            raise ValueError(f"modal_membership_count out of range: {row['modal_membership_count']}")
        if not (0 <= row["exact_order_pairwise_agreement"] <= 1):
            raise ValueError(f"exact_order_pairwise_agreement out of range: {row['exact_order_pairwise_agreement']}")
        if not (0 <= row["exact_membership_pairwise_agreement"] <= 1):
            raise ValueError(f"exact_membership_pairwise_agreement out of range: {row['exact_membership_pairwise_agreement']}")
        if not (0.5 <= row["mean_pairwise_jaccard"] <= 1):
            raise ValueError(f"mean_pairwise_jaccard out of range: {row['mean_pairwise_jaccard']}")
        if not (0 <= row["mean_full_rank_position_agreement"] <= 1):
            raise ValueError(f"mean_full_rank_position_agreement out of range: {row['mean_full_rank_position_agreement']}")
        if not (-1 <= row["mean_pairwise_kendall_tau"] <= 1):
            raise ValueError(f"mean_pairwise_kendall_tau out of range: {row['mean_pairwise_kendall_tau']}")
        if not (0 <= row["mean_pairwise_kendall_similarity"] <= 1):
            raise ValueError(f"mean_pairwise_kendall_similarity out of range: {row['mean_pairwise_kendall_similarity']}")
        if row["minimum_cutoff_score_gap"] <= 0:
            raise ValueError(f"minimum_cutoff_score_gap <= 0: {row['minimum_cutoff_score_gap']}")
        
        # Check equivalence conditions
        if row["unanimous_order"]:
            if row["distinct_orders"] != 1:
                raise ValueError(f"unanimous_order but distinct_orders != 1")
            if row["modal_order_count"] != 5:
                raise ValueError(f"unanimous_order but modal_order_count != 5")
            if abs(row["exact_order_pairwise_agreement"] - 1.0) > TOLERANCE:
                raise ValueError(f"unanimous_order but exact_order_pairwise_agreement != 1")
        
        if row["unanimous_membership"]:
            if row["distinct_membership_sets"] != 1:
                raise ValueError(f"unanimous_membership but distinct_membership_sets != 1")
            if row["modal_membership_count"] != 5:
                raise ValueError(f"unanimous_membership but modal_membership_count != 5")
            if abs(row["exact_membership_pairwise_agreement"] - 1.0) > TOLERANCE:
                raise ValueError(f"unanimous_membership but exact_membership_pairwise_agreement != 1")
            if abs(row["mean_pairwise_jaccard"] - 1.0) > TOLERANCE:
                raise ValueError(f"unanimous_membership but mean_pairwise_jaccard != 1")
        
        # Check Kendall similarity formula
        expected_kendall_similarity = (row["mean_pairwise_kendall_tau"] + 1) / 2
        if abs(row["mean_pairwise_kendall_similarity"] - expected_kendall_similarity) > TOLERANCE:
            raise ValueError(f"Kendall similarity formula violation")
        
        # Check modal membership set and excluded candidate mapping
        modal_membership_sets_list = row["modal_membership_sets"].split("|OR|")
        modal_excluded_candidates_list = row["modal_excluded_candidates"].split("|OR|")
        
        if len(modal_membership_sets_list) != len(modal_excluded_candidates_list):
            raise ValueError(f"Modal membership sets and excluded candidates count mismatch for {row['experiment']}/{row['target_project']}")
        
        for ms, exc in zip(modal_membership_sets_list, modal_excluded_candidates_list):
            if MEMBERSHIP_TO_EXCLUDED[ms] != exc:
                raise ValueError(f"Modal membership mapping mismatch for {ms}/{exc} in {row['experiment']}/{row['target_project']}")
        
        # Check Jaccard identity
        expected_jaccard = 0.5 + 0.5 * row["exact_membership_pairwise_agreement"]
        if abs(row["mean_pairwise_jaccard"] - expected_jaccard) > TOLERANCE:
            raise ValueError(f"Jaccard identity violation for {row['experiment']}/{row['target_project']}")
        
        # Check bidirectional unanimous conditions
        expected_unanimous_order = (
            row["distinct_orders"] == 1
            and row["modal_order_count"] == 5
            and abs(row["exact_order_pairwise_agreement"] - 1.0) <= TOLERANCE
        )
        if row["unanimous_order"] != expected_unanimous_order:
            raise ValueError(f"Unanimous order bidirectional check failed for {row['experiment']}/{row['target_project']}")
        
        expected_unanimous_membership = (
            row["distinct_membership_sets"] == 1
            and row["modal_membership_count"] == 5
            and abs(row["exact_membership_pairwise_agreement"] - 1.0) <= TOLERANCE
            and abs(row["mean_pairwise_jaccard"] - 1.0) <= TOLERANCE
        )
        if row["unanimous_membership"] != expected_unanimous_membership:
            raise ValueError(f"Unanimous membership bidirectional check failed for {row['experiment']}/{row['target_project']}")
        
        # Check modal tie flags
        num_modal_orders = len(row["modal_orders"].split("|OR|"))
        if row["order_modal_tie"] != (num_modal_orders > 1):
            raise ValueError(f"Order modal tie flag mismatch for {row['experiment']}/{row['target_project']}")
        
        num_modal_membership_sets = len(row["modal_membership_sets"].split("|OR|"))
        if row["membership_modal_tie"] != (num_modal_membership_sets > 1):
            raise ValueError(f"Membership modal tie flag mismatch for {row['experiment']}/{row['target_project']}")
    
    # Sort
    group_stability_df = group_stability_df.sort_values(["experiment", "target_project"])
    
    print("Group stability computed.")
    return group_stability_df


def compute_summary(group_stability_df):
    """Compute summary statistics."""
    print("Computing summary...")
    
    summary_rows = []
    
    # Overall summary
    overall = {
        "scope": "overall",
        "experiment": "all",
        "group_count": 10,
        "unanimous_order_group_count": int(group_stability_df["unanimous_order"].sum()),
        "unanimous_order_group_proportion": group_stability_df["unanimous_order"].sum() / 10,
        "unanimous_membership_group_count": int(group_stability_df["unanimous_membership"].sum()),
        "unanimous_membership_group_proportion": group_stability_df["unanimous_membership"].sum() / 10,
        "order_modal_tie_group_count": int(group_stability_df["order_modal_tie"].sum()),
        "membership_modal_tie_group_count": int(group_stability_df["membership_modal_tie"].sum()),
        "mean_distinct_orders": group_stability_df["distinct_orders"].mean(),
        "mean_distinct_membership_sets": group_stability_df["distinct_membership_sets"].mean(),
        "mean_modal_order_proportion": group_stability_df["modal_order_proportion"].mean(),
        "mean_modal_membership_proportion": group_stability_df["modal_membership_proportion"].mean(),
        "mean_exact_order_pairwise_agreement": group_stability_df["exact_order_pairwise_agreement"].mean(),
        "mean_exact_membership_pairwise_agreement": group_stability_df["exact_membership_pairwise_agreement"].mean(),
        "mean_pairwise_jaccard": group_stability_df["mean_pairwise_jaccard"].mean(),
        "mean_full_rank_position_agreement": group_stability_df["mean_full_rank_position_agreement"].mean(),
        "mean_pairwise_kendall_tau": group_stability_df["mean_pairwise_kendall_tau"].mean(),
        "mean_pairwise_kendall_similarity": group_stability_df["mean_pairwise_kendall_similarity"].mean(),
        "minimum_group_cutoff_score_gap": group_stability_df["minimum_cutoff_score_gap"].min(),
        "median_group_minimum_cutoff_score_gap": group_stability_df["minimum_cutoff_score_gap"].median(),
        "mean_group_minimum_cutoff_score_gap": group_stability_df["minimum_cutoff_score_gap"].mean(),
    }
    summary_rows.append(overall)
    
    # By setting summary
    for experiment in EXPECTED_EXPERIMENTS:
        subset = group_stability_df[group_stability_df["experiment"] == experiment]
        summary_rows.append({
            "scope": "by_setting",
            "experiment": experiment,
            "group_count": 5,
            "unanimous_order_group_count": int(subset["unanimous_order"].sum()),
            "unanimous_order_group_proportion": subset["unanimous_order"].sum() / 5,
            "unanimous_membership_group_count": int(subset["unanimous_membership"].sum()),
            "unanimous_membership_group_proportion": subset["unanimous_membership"].sum() / 5,
            "order_modal_tie_group_count": int(subset["order_modal_tie"].sum()),
            "membership_modal_tie_group_count": int(subset["membership_modal_tie"].sum()),
            "mean_distinct_orders": subset["distinct_orders"].mean(),
            "mean_distinct_membership_sets": subset["distinct_membership_sets"].mean(),
            "mean_modal_order_proportion": subset["modal_order_proportion"].mean(),
            "mean_modal_membership_proportion": subset["modal_membership_proportion"].mean(),
            "mean_exact_order_pairwise_agreement": subset["exact_order_pairwise_agreement"].mean(),
            "mean_exact_membership_pairwise_agreement": subset["exact_membership_pairwise_agreement"].mean(),
            "mean_pairwise_jaccard": subset["mean_pairwise_jaccard"].mean(),
            "mean_full_rank_position_agreement": subset["mean_full_rank_position_agreement"].mean(),
            "mean_pairwise_kendall_tau": subset["mean_pairwise_kendall_tau"].mean(),
            "mean_pairwise_kendall_similarity": subset["mean_pairwise_kendall_similarity"].mean(),
            "minimum_group_cutoff_score_gap": subset["minimum_cutoff_score_gap"].min(),
            "median_group_minimum_cutoff_score_gap": subset["minimum_cutoff_score_gap"].median(),
            "mean_group_minimum_cutoff_score_gap": subset["minimum_cutoff_score_gap"].mean(),
        })
    
    summary_df = pd.DataFrame(summary_rows)
    
    # Verify row count
    if len(summary_df) != 3:
        raise ValueError(f"Expected 3 summary rows, got {len(summary_df)}")
    
    # Check for nulls
    if summary_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in summary")
    
    # Sort
    summary_df = summary_df.sort_values(["scope", "experiment"])
    
    print("Summary computed.")
    return summary_df


def reconstruct_expected_summary(group_stability_df):
    """Reconstruct expected summary from group_stability_df independently."""
    # Overall: all 10 groups
    overall_df = group_stability_df
    overall_row = {
        "scope": "overall",
        "experiment": "all",
        "group_count": len(overall_df),
        "unanimous_order_group_count": int(overall_df["unanimous_order"].sum()),
        "unanimous_order_group_proportion": overall_df["unanimous_order"].sum() / len(overall_df),
        "unanimous_membership_group_count": int(overall_df["unanimous_membership"].sum()),
        "unanimous_membership_group_proportion": overall_df["unanimous_membership"].sum() / len(overall_df),
        "order_modal_tie_group_count": int(overall_df["order_modal_tie"].sum()),
        "membership_modal_tie_group_count": int(overall_df["membership_modal_tie"].sum()),
        "mean_distinct_orders": overall_df["distinct_orders"].mean(),
        "mean_distinct_membership_sets": overall_df["distinct_membership_sets"].mean(),
        "mean_modal_order_proportion": overall_df["modal_order_proportion"].mean(),
        "mean_modal_membership_proportion": overall_df["modal_membership_proportion"].mean(),
        "mean_exact_order_pairwise_agreement": overall_df["exact_order_pairwise_agreement"].mean(),
        "mean_exact_membership_pairwise_agreement": overall_df["exact_membership_pairwise_agreement"].mean(),
        "mean_pairwise_jaccard": overall_df["mean_pairwise_jaccard"].mean(),
        "mean_full_rank_position_agreement": overall_df["mean_full_rank_position_agreement"].mean(),
        "mean_pairwise_kendall_tau": overall_df["mean_pairwise_kendall_tau"].mean(),
        "mean_pairwise_kendall_similarity": overall_df["mean_pairwise_kendall_similarity"].mean(),
        "minimum_group_cutoff_score_gap": overall_df["minimum_cutoff_score_gap"].min(),
        "median_group_minimum_cutoff_score_gap": overall_df["minimum_cutoff_score_gap"].median(),
        "mean_group_minimum_cutoff_score_gap": overall_df["minimum_cutoff_score_gap"].mean(),
    }
    
    # Within-project: 5 groups
    wp_df = overall_df[overall_df["experiment"] == "within_project"]
    wp_row = {
        "scope": "by_setting",
        "experiment": "within_project",
        "group_count": len(wp_df),
        "unanimous_order_group_count": int(wp_df["unanimous_order"].sum()),
        "unanimous_order_group_proportion": wp_df["unanimous_order"].sum() / len(wp_df),
        "unanimous_membership_group_count": int(wp_df["unanimous_membership"].sum()),
        "unanimous_membership_group_proportion": wp_df["unanimous_membership"].sum() / len(wp_df),
        "order_modal_tie_group_count": int(wp_df["order_modal_tie"].sum()),
        "membership_modal_tie_group_count": int(wp_df["membership_modal_tie"].sum()),
        "mean_distinct_orders": wp_df["distinct_orders"].mean(),
        "mean_distinct_membership_sets": wp_df["distinct_membership_sets"].mean(),
        "mean_modal_order_proportion": wp_df["modal_order_proportion"].mean(),
        "mean_modal_membership_proportion": wp_df["modal_membership_proportion"].mean(),
        "mean_exact_order_pairwise_agreement": wp_df["exact_order_pairwise_agreement"].mean(),
        "mean_exact_membership_pairwise_agreement": wp_df["exact_membership_pairwise_agreement"].mean(),
        "mean_pairwise_jaccard": wp_df["mean_pairwise_jaccard"].mean(),
        "mean_full_rank_position_agreement": wp_df["mean_full_rank_position_agreement"].mean(),
        "mean_pairwise_kendall_tau": wp_df["mean_pairwise_kendall_tau"].mean(),
        "mean_pairwise_kendall_similarity": wp_df["mean_pairwise_kendall_similarity"].mean(),
        "minimum_group_cutoff_score_gap": wp_df["minimum_cutoff_score_gap"].min(),
        "median_group_minimum_cutoff_score_gap": wp_df["minimum_cutoff_score_gap"].median(),
        "mean_group_minimum_cutoff_score_gap": wp_df["minimum_cutoff_score_gap"].mean(),
    }
    
    # Cross-project: 5 groups
    cp_df = overall_df[overall_df["experiment"] == "cross_project"]
    cp_row = {
        "scope": "by_setting",
        "experiment": "cross_project",
        "group_count": len(cp_df),
        "unanimous_order_group_count": int(cp_df["unanimous_order"].sum()),
        "unanimous_order_group_proportion": cp_df["unanimous_order"].sum() / len(cp_df),
        "unanimous_membership_group_count": int(cp_df["unanimous_membership"].sum()),
        "unanimous_membership_group_proportion": cp_df["unanimous_membership"].sum() / len(cp_df),
        "order_modal_tie_group_count": int(cp_df["order_modal_tie"].sum()),
        "membership_modal_tie_group_count": int(cp_df["membership_modal_tie"].sum()),
        "mean_distinct_orders": cp_df["distinct_orders"].mean(),
        "mean_distinct_membership_sets": cp_df["distinct_membership_sets"].mean(),
        "mean_modal_order_proportion": cp_df["modal_order_proportion"].mean(),
        "mean_modal_membership_proportion": cp_df["modal_membership_proportion"].mean(),
        "mean_exact_order_pairwise_agreement": cp_df["exact_order_pairwise_agreement"].mean(),
        "mean_exact_membership_pairwise_agreement": cp_df["exact_membership_pairwise_agreement"].mean(),
        "mean_pairwise_jaccard": cp_df["mean_pairwise_jaccard"].mean(),
        "mean_full_rank_position_agreement": cp_df["mean_full_rank_position_agreement"].mean(),
        "mean_pairwise_kendall_tau": cp_df["mean_pairwise_kendall_tau"].mean(),
        "mean_pairwise_kendall_similarity": cp_df["mean_pairwise_kendall_similarity"].mean(),
        "minimum_group_cutoff_score_gap": cp_df["minimum_cutoff_score_gap"].min(),
        "median_group_minimum_cutoff_score_gap": cp_df["minimum_cutoff_score_gap"].median(),
        "mean_group_minimum_cutoff_score_gap": cp_df["minimum_cutoff_score_gap"].mean(),
    }
    
    return [overall_row, wp_row, cp_row]


def validate_final_outputs(order_counts_df, membership_counts_df, group_stability_df, summary_df, event_provenance_results, canonical_verification):
    """Validate all outputs and return validation checks and evidence."""
    print("Validating final outputs...")
    
    validation_checks = {}
    validation_evidence = {}
    
    # 1. Canonical verification passed
    canonical_verification_passed = (
        canonical_verification["manifest_validation_status"] == "all_checks_passed"
        and canonical_verification["repeated_results_sha256_verified"]
        and canonical_verification["validation_log_sha256_verified"]
        and canonical_verification["evaluation_script_sha256_verified"]
    )
    validation_checks["canonical_verification_passed"] = canonical_verification_passed
    
    # 2. Event provenance passed
    event_provenance_passed = (
        event_provenance_results["events_checked"] == 50
        and all(
            event_provenance_results[key] == 0
            for key in [
                "canonical_event_mismatches",
                "validation_ranking_mismatches",
                "score_mismatches",
                "cutoff_gap_mismatches",
            ]
        )
    )
    validation_checks["event_provenance_passed"] = event_provenance_passed
    
    # 3. Modal order sorting passed
    modal_order_groups_checked = 0
    modal_order_sorting_passed = True
    for _, row in group_stability_df.iterrows():
        modal_order_groups_checked += 1
        modal_orders = row["modal_orders"].split("|OR|")
        
        # Check all modal orders are in ALL_SELECTED_ORDERS
        for order in modal_orders:
            if order not in ALL_SELECTED_ORDERS:
                modal_order_sorting_passed = False
                break
        
        # Check sorting
        expected_sorted = sorted(modal_orders, key=ALL_SELECTED_ORDERS.index)
        if modal_orders != expected_sorted:
            modal_order_sorting_passed = False
        
        # Check count matches order_counts_df
        experiment = row["experiment"]
        project = row["target_project"]
        modal_order_count = row["modal_order_count"]
        
        for order in modal_orders:
            order_count = order_counts_df[
                (order_counts_df["experiment"] == experiment) &
                (order_counts_df["target_project"] == project) &
                (order_counts_df["selected_order"] == order)
            ]["count"].iloc[0]
            if order_count != modal_order_count:
                modal_order_sorting_passed = False
                break
        
        # Check no other order has higher count
        group_order_counts = order_counts_df[
            (order_counts_df["experiment"] == experiment) &
            (order_counts_df["target_project"] == project)
        ]
        for _, oc_row in group_order_counts.iterrows():
            if oc_row["selected_order"] not in modal_orders and oc_row["count"] >= modal_order_count:
                modal_order_sorting_passed = False
                break
        
        if not modal_order_sorting_passed:
            break
    
    validation_checks["modal_order_sorting_passed"] = modal_order_sorting_passed
    validation_evidence["modal_order_groups_checked"] = modal_order_groups_checked
    
    # 4. Membership mapping passed
    membership_mapping_passed = True
    for _, row in membership_counts_df.iterrows():
        membership_set = row["membership_set"]
        excluded_candidate = row["excluded_candidate"]
        
        members = membership_set.split("|")
        
        if len(members) != 3:
            membership_mapping_passed = False
            break
        if len(set(members)) != 3:
            membership_mapping_passed = False
            break
        if set(members) | {excluded_candidate} != set(CANDIDATE_ORDER):
            membership_mapping_passed = False
            break
        if set(members) & {excluded_candidate}:
            membership_mapping_passed = False
            break
        if MEMBERSHIP_TO_EXCLUDED[membership_set] != excluded_candidate:
            membership_mapping_passed = False
            break
    
    # Check membership_counts_df structure
    if len(membership_counts_df) != 40:
        membership_mapping_passed = False
    if len(membership_counts_df.columns) != 7:
        membership_mapping_passed = False
    if membership_counts_df.isnull().sum().sum() > 0:
        membership_mapping_passed = False
    
    key_cols = ["experiment", "target_project", "membership_set"]
    if membership_counts_df.duplicated(subset=key_cols).sum() > 0:
        membership_mapping_passed = False
    
    validation_checks["membership_mapping_passed"] = membership_mapping_passed
    
    # 5. Modal excluded mapping passed
    modal_membership_groups_checked = 0
    modal_excluded_mapping_passed = True
    for _, row in group_stability_df.iterrows():
        modal_membership_groups_checked += 1
        modal_sets = row["modal_membership_sets"].split("|OR|")
        actual_excluded = row["modal_excluded_candidates"].split("|OR|")
        
        expected_excluded = [
            MEMBERSHIP_TO_EXCLUDED[membership_set]
            for membership_set in modal_sets
        ]
        expected_excluded = sorted(expected_excluded, key=CANDIDATE_ORDER.index)
        
        if actual_excluded != expected_excluded:
            modal_excluded_mapping_passed = False
            break
        
        # Check count matches membership_counts_df
        experiment = row["experiment"]
        project = row["target_project"]
        modal_membership_count = row["modal_membership_count"]
        
        for ms in modal_sets:
            membership_count = membership_counts_df[
                (membership_counts_df["experiment"] == experiment) &
                (membership_counts_df["target_project"] == project) &
                (membership_counts_df["membership_set"] == ms)
            ]["count"].iloc[0]
            if membership_count != modal_membership_count:
                modal_excluded_mapping_passed = False
                break
        
        # Check no other membership set has higher count
        group_membership_counts = membership_counts_df[
            (membership_counts_df["experiment"] == experiment) &
            (membership_counts_df["target_project"] == project)
        ]
        for _, mc_row in group_membership_counts.iterrows():
            if mc_row["membership_set"] not in modal_sets and mc_row["count"] >= modal_membership_count:
                modal_excluded_mapping_passed = False
                break
        
        if not modal_excluded_mapping_passed:
            break
    
    validation_checks["modal_excluded_mapping_passed"] = modal_excluded_mapping_passed
    validation_evidence["modal_membership_groups_checked"] = modal_membership_groups_checked
    
    # 6. Pairwise count formula passed
    pairwise_formula_groups_checked = 0
    pairwise_count_formula_passed = True
    for _, row in group_stability_df.iterrows():
        pairwise_formula_groups_checked += 1
        experiment = row["experiment"]
        project = row["target_project"]
        
        # Check order agreement formula
        group_order_counts = order_counts_df[
            (order_counts_df["experiment"] == experiment) &
            (order_counts_df["target_project"] == project)
        ]["count"].values
        expected_order_agreement = sum(c * (c - 1) / 2 for c in group_order_counts) / 10
        if abs(row["exact_order_pairwise_agreement"] - expected_order_agreement) > TOLERANCE:
            pairwise_count_formula_passed = False
            break
        
        # Check membership agreement formula
        group_membership_counts = membership_counts_df[
            (membership_counts_df["experiment"] == experiment) &
            (membership_counts_df["target_project"] == project)
        ]["count"].values
        expected_membership_agreement = sum(c * (c - 1) / 2 for c in group_membership_counts) / 10
        if abs(row["exact_membership_pairwise_agreement"] - expected_membership_agreement) > TOLERANCE:
            pairwise_count_formula_passed = False
            break
    
    validation_checks["pairwise_count_formula_passed"] = pairwise_count_formula_passed
    validation_evidence["pairwise_formula_groups_checked"] = pairwise_formula_groups_checked
    
    # 7. Jaccard identity passed
    jaccard_identity_groups_checked = 0
    jaccard_identity_passed = True
    for _, row in group_stability_df.iterrows():
        jaccard_identity_groups_checked += 1
        expected_jaccard = 0.5 + 0.5 * row["exact_membership_pairwise_agreement"]
        if abs(row["mean_pairwise_jaccard"] - expected_jaccard) > TOLERANCE:
            jaccard_identity_passed = False
            break
    
    validation_checks["jaccard_identity_passed"] = jaccard_identity_passed
    validation_evidence["jaccard_identity_groups_checked"] = jaccard_identity_groups_checked
    
    # 8. Unanimous bidirectional checks passed
    unanimous_groups_checked = 0
    unanimous_bidirectional_checks_passed = True
    for _, row in group_stability_df.iterrows():
        unanimous_groups_checked += 1
        
        # Check unanimous order
        expected_unanimous_order = (
            row["distinct_orders"] == 1
            and row["modal_order_count"] == 5
            and abs(row["exact_order_pairwise_agreement"] - 1.0) <= TOLERANCE
        )
        if row["unanimous_order"] != expected_unanimous_order:
            unanimous_bidirectional_checks_passed = False
            break
        
        # Check unanimous membership
        expected_unanimous_membership = (
            row["distinct_membership_sets"] == 1
            and row["modal_membership_count"] == 5
            and abs(row["exact_membership_pairwise_agreement"] - 1.0) <= TOLERANCE
            and abs(row["mean_pairwise_jaccard"] - 1.0) <= TOLERANCE
        )
        if row["unanimous_membership"] != expected_unanimous_membership:
            unanimous_bidirectional_checks_passed = False
            break
        
        # Check modal tie flags
        num_modal_orders = len(row["modal_orders"].split("|OR|"))
        if row["order_modal_tie"] != (num_modal_orders > 1):
            unanimous_bidirectional_checks_passed = False
            break
        
        num_modal_membership_sets = len(row["modal_membership_sets"].split("|OR|"))
        if row["membership_modal_tie"] != (num_modal_membership_sets > 1):
            unanimous_bidirectional_checks_passed = False
            break
    
    validation_checks["unanimous_bidirectional_checks_passed"] = unanimous_bidirectional_checks_passed
    validation_evidence["unanimous_groups_checked"] = unanimous_groups_checked
    
    # 9. Order count structure passed
    order_count_structure_passed = True
    if len(order_counts_df) != 240:
        order_count_structure_passed = False
    if len(order_counts_df.columns) != 6:
        order_count_structure_passed = False
    if order_counts_df.isnull().sum().sum() > 0:
        order_count_structure_passed = False
    
    key_cols = ["experiment", "target_project", "selected_order"]
    if order_counts_df.duplicated(subset=key_cols).sum() > 0:
        order_count_structure_passed = False
    
    order_count_groups_checked = 0
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            order_count_groups_checked += 1
            group_counts = order_counts_df[
                (order_counts_df["experiment"] == experiment) &
                (order_counts_df["target_project"] == project)
            ]
            if len(group_counts) != 24:
                order_count_structure_passed = False
            if group_counts["count"].sum() != 5:
                order_count_structure_passed = False
            if abs(group_counts["proportion"].sum() - 1.0) > TOLERANCE:
                order_count_structure_passed = False
            if (group_counts["denominator"] != 5).any():
                order_count_structure_passed = False
    
    validation_checks["order_count_structure_passed"] = order_count_structure_passed
    validation_evidence["order_count_groups_checked"] = order_count_groups_checked
    
    # 10. Membership count structure passed
    membership_count_structure_passed = True
    if len(membership_counts_df) != 40:
        membership_count_structure_passed = False
    if len(membership_counts_df.columns) != 7:
        membership_count_structure_passed = False
    if membership_counts_df.isnull().sum().sum() > 0:
        membership_count_structure_passed = False
    
    key_cols = ["experiment", "target_project", "membership_set"]
    if membership_counts_df.duplicated(subset=key_cols).sum() > 0:
        membership_count_structure_passed = False
    
    membership_count_groups_checked = 0
    for experiment in EXPECTED_EXPERIMENTS:
        for project in EXPECTED_PROJECTS:
            membership_count_groups_checked += 1
            group_counts = membership_counts_df[
                (membership_counts_df["experiment"] == experiment) &
                (membership_counts_df["target_project"] == project)
            ]
            if len(group_counts) != 4:
                membership_count_structure_passed = False
            if group_counts["count"].sum() != 5:
                membership_count_structure_passed = False
            if abs(group_counts["proportion"].sum() - 1.0) > TOLERANCE:
                membership_count_structure_passed = False
            if (group_counts["denominator"] != 5).any():
                membership_count_structure_passed = False
    
    validation_checks["membership_count_structure_passed"] = membership_count_structure_passed
    validation_evidence["membership_count_groups_checked"] = membership_count_groups_checked
    
    # 11. Group validation passed (structure + domain + existing checks)
    group_structure_passed = True
    if len(group_stability_df) != 10:
        group_structure_passed = False
    if len(group_stability_df.columns) != 25:
        group_structure_passed = False
    if group_stability_df.isnull().sum().sum() > 0:
        group_structure_passed = False
    if group_stability_df.duplicated(subset=["experiment", "target_project"]).sum() > 0:
        group_structure_passed = False
    
    expected_group_keys = {
        (experiment, project)
        for experiment in EXPECTED_EXPERIMENTS
        for project in EXPECTED_PROJECTS
    }
    actual_group_keys = set(
        (row["experiment"], row["target_project"])
        for _, row in group_stability_df.iterrows()
    )
    if actual_group_keys != expected_group_keys:
        group_structure_passed = False
    
    group_domain_rows_checked = 0
    group_kendall_rows_checked = 0
    group_cutoff_rows_checked = 0
    group_seed_count_rows_checked = 0
    group_domain_passed = True
    
    for _, row in group_stability_df.iterrows():
        group_domain_rows_checked += 1
        group_seed_count_rows_checked += 1
        
        # Explicit n_seeds check
        if row["n_seeds"] != 5:
            group_domain_passed = False
        
        # Domain checks
        if not (1 <= row["distinct_orders"] <= 5):
            group_domain_passed = False
        if not (1 <= row["distinct_membership_sets"] <= 4):
            group_domain_passed = False
        if not (1 <= row["modal_order_count"] <= 5):
            group_domain_passed = False
        if not (1 <= row["modal_membership_count"] <= 5):
            group_domain_passed = False
        if abs(row["modal_order_proportion"] - row["modal_order_count"] / 5) > TOLERANCE:
            group_domain_passed = False
        if abs(row["modal_membership_proportion"] - row["modal_membership_count"] / 5) > TOLERANCE:
            group_domain_passed = False
        if not (0 <= row["exact_order_pairwise_agreement"] <= 1):
            group_domain_passed = False
        if not (0 <= row["exact_membership_pairwise_agreement"] <= 1):
            group_domain_passed = False
        if not (0.5 <= row["mean_pairwise_jaccard"] <= 1):
            group_domain_passed = False
        if not (0 <= row["mean_full_rank_position_agreement"] <= 1):
            group_domain_passed = False
        
        # Kendall checks
        group_kendall_rows_checked += 1
        if not (-1 <= row["mean_pairwise_kendall_tau"] <= 1):
            group_domain_passed = False
        if not (0 <= row["mean_pairwise_kendall_similarity"] <= 1):
            group_domain_passed = False
        if abs(row["mean_pairwise_kendall_similarity"] - (row["mean_pairwise_kendall_tau"] + 1) / 2) > TOLERANCE:
            group_domain_passed = False
        
        # Cutoff checks
        group_cutoff_rows_checked += 1
        if row["minimum_cutoff_score_gap"] <= 0:
            group_domain_passed = False
        if row["minimum_cutoff_score_gap"] > row["median_cutoff_score_gap"]:
            group_domain_passed = False
        if row["minimum_cutoff_score_gap"] > row["mean_cutoff_score_gap"]:
            group_domain_passed = False
    
    group_structure_rows_checked = len(group_stability_df)
    validation_evidence["group_structure_rows_checked"] = group_structure_rows_checked
    validation_evidence["group_seed_count_rows_checked"] = group_seed_count_rows_checked
    validation_evidence["group_domain_rows_checked"] = group_domain_rows_checked
    validation_evidence["group_kendall_rows_checked"] = group_kendall_rows_checked
    validation_evidence["group_cutoff_rows_checked"] = group_cutoff_rows_checked
    
    group_validation_passed = (
        group_structure_passed
        and group_structure_rows_checked == 10
        and group_domain_passed
        and modal_order_sorting_passed
        and membership_mapping_passed
        and modal_excluded_mapping_passed
        and pairwise_count_formula_passed
        and jaccard_identity_passed
        and unanimous_bidirectional_checks_passed
    )
    validation_checks["group_validation_passed"] = group_validation_passed
    
    # 12. Summary validation passed (schema + reconstruction)
    summary_schema_passed = True
    if len(summary_df) != 3:
        summary_schema_passed = False
    if len(summary_df.columns) != 22:
        summary_schema_passed = False
    if summary_df.isnull().sum().sum() > 0:
        summary_schema_passed = False
    
    key_cols = ["scope", "experiment"]
    if summary_df.duplicated(subset=key_cols).sum() > 0:
        summary_schema_passed = False
    
    expected_summary_keys = {
        ("overall", "all"),
        ("by_setting", "within_project"),
        ("by_setting", "cross_project"),
    }
    actual_summary_keys = set(
        (row["scope"], row["experiment"])
        for _, row in summary_df.iterrows()
    )
    if actual_summary_keys != expected_summary_keys:
        summary_schema_passed = False
    
    expected_summary_columns = {
        "scope", "experiment", "group_count",
        "unanimous_order_group_count", "unanimous_order_group_proportion",
        "unanimous_membership_group_count", "unanimous_membership_group_proportion",
        "order_modal_tie_group_count", "membership_modal_tie_group_count",
        "mean_distinct_orders", "mean_distinct_membership_sets",
        "mean_modal_order_proportion", "mean_modal_membership_proportion",
        "mean_exact_order_pairwise_agreement", "mean_exact_membership_pairwise_agreement",
        "mean_pairwise_jaccard", "mean_full_rank_position_agreement",
        "mean_pairwise_kendall_tau", "mean_pairwise_kendall_similarity",
        "minimum_group_cutoff_score_gap", "median_group_minimum_cutoff_score_gap",
        "mean_group_minimum_cutoff_score_gap",
    }
    actual_summary_columns = set(summary_df.columns)
    if actual_summary_columns != expected_summary_columns:
        summary_schema_passed = False
    
    # Reconstruct expected summary independently
    expected_summary_rows = reconstruct_expected_summary(group_stability_df)
    
    # Compare all 3 rows and 20 non-key fields
    summary_field_counts_by_row = []
    summary_total_field_comparisons = 0
    summary_reconstruction_passed = True
    
    for expected_row in expected_summary_rows:
        actual_row = summary_df[
            (summary_df["scope"] == expected_row["scope"]) &
            (summary_df["experiment"] == expected_row["experiment"])
        ].iloc[0]
        
        # Check scope and experiment match exactly
        if actual_row["scope"] != expected_row["scope"]:
            summary_reconstruction_passed = False
        if actual_row["experiment"] != expected_row["experiment"]:
            summary_reconstruction_passed = False
        
        # Check all non-key fields
        non_key_fields = [k for k in expected_row.keys() if k not in ["scope", "experiment"]]
        summary_field_counts_by_row.append(len(non_key_fields))
        
        for field in non_key_fields:
            summary_total_field_comparisons += 1
            expected_val = expected_row[field]
            actual_val = actual_row[field]
            
            if field.endswith("_count"):
                if actual_val != expected_val:
                    summary_reconstruction_passed = False
            else:
                if abs(actual_val - expected_val) > TOLERANCE:
                    summary_reconstruction_passed = False
    
    # Validate summary field counts
    summary_fields_consistent = (
        len(summary_field_counts_by_row) == 3
        and all(count == 20 for count in summary_field_counts_by_row)
    )
    if not summary_fields_consistent:
        summary_reconstruction_passed = False
    
    summary_rows_reconstructed = len(expected_summary_rows)
    summary_fields_checked_per_row = (
        summary_field_counts_by_row[0]
        if summary_fields_consistent
        else None
    )
    
    validation_evidence["summary_rows_reconstructed"] = summary_rows_reconstructed
    validation_evidence["summary_fields_checked_per_row"] = summary_fields_checked_per_row
    validation_evidence["summary_total_field_comparisons"] = summary_total_field_comparisons
    
    summary_validation_passed = (
        summary_schema_passed
        and summary_reconstruction_passed
        and summary_rows_reconstructed == 3
    )
    validation_checks["summary_validation_passed"] = summary_validation_passed
    
    # 13. Validation evidence integrity passed
    validation_evidence_integrity_passed = (
        validation_evidence["group_structure_rows_checked"] == len(group_stability_df) == 10
        and validation_evidence["group_seed_count_rows_checked"] == len(group_stability_df) == 10
        and validation_evidence["summary_rows_reconstructed"] == len(expected_summary_rows) == 3
        and validation_evidence["summary_fields_checked_per_row"] == 20
        and validation_evidence["summary_total_field_comparisons"] == 60
    )
    validation_checks["validation_evidence_integrity_passed"] = validation_evidence_integrity_passed
    
    # Add evidence
    validation_evidence["events_checked"] = event_provenance_results["events_checked"]
    validation_evidence["order_count_rows"] = len(order_counts_df)
    validation_evidence["membership_count_rows"] = len(membership_counts_df)
    validation_evidence["group_rows"] = len(group_stability_df)
    validation_evidence["summary_rows"] = len(summary_df)
    
    print("Final validation complete.")
    return validation_checks, validation_evidence


def save_all_outputs(order_counts_df, membership_counts_df, group_stability_df, summary_df, event_provenance_results, validation_checks, validation_evidence, canonical_verification):
    """Save all output files after validation passes."""
    print("Saving all outputs...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build all outputs in memory
    order_csv_text = order_counts_df.to_csv(index=False)
    membership_csv_text = membership_counts_df.to_csv(index=False)
    group_csv_text = group_stability_df.to_csv(index=False)
    summary_csv_text = summary_df.to_csv(index=False)
    
    # Build reports in memory
    report_dict = build_report_dict(event_provenance_results, group_stability_df, summary_df, validation_checks, validation_evidence, canonical_verification)
    json_text = json.dumps(report_dict, indent=2, ensure_ascii=False) + "\n"
    
    markdown_text = build_markdown_report(event_provenance_results, group_stability_df, summary_df, validation_checks, validation_evidence, canonical_verification)
    
    # Save using same-directory temp files for atomic writes
    temp_files = []
    
    try:
        # Save order counts
        tmp_order = OUTPUT_ORDER_COUNTS.with_name(OUTPUT_ORDER_COUNTS.name + ".tmp")
        tmp_order.write_text(order_csv_text, encoding="utf-8")
        temp_files.append(tmp_order)
        
        # Save membership counts
        tmp_membership = OUTPUT_MEMBERSHIP_COUNTS.with_name(OUTPUT_MEMBERSHIP_COUNTS.name + ".tmp")
        tmp_membership.write_text(membership_csv_text, encoding="utf-8")
        temp_files.append(tmp_membership)
        
        # Save group stability
        tmp_group = OUTPUT_GROUP_STABILITY.with_name(OUTPUT_GROUP_STABILITY.name + ".tmp")
        tmp_group.write_text(group_csv_text, encoding="utf-8")
        temp_files.append(tmp_group)
        
        # Save summary
        tmp_summary = OUTPUT_SUMMARY.with_name(OUTPUT_SUMMARY.name + ".tmp")
        tmp_summary.write_text(summary_csv_text, encoding="utf-8")
        temp_files.append(tmp_summary)
        
        # Save JSON
        tmp_json = OUTPUT_JSON.with_name(OUTPUT_JSON.name + ".tmp")
        tmp_json.write_text(json_text, encoding="utf-8")
        temp_files.append(tmp_json)
        
        # Save Markdown
        tmp_md = OUTPUT_MD.with_name(OUTPUT_MD.name + ".tmp")
        tmp_md.write_text(markdown_text, encoding="utf-8")
        temp_files.append(tmp_md)
        
        # Atomic replacement
        tmp_order.replace(OUTPUT_ORDER_COUNTS)
        tmp_membership.replace(OUTPUT_MEMBERSHIP_COUNTS)
        tmp_group.replace(OUTPUT_GROUP_STABILITY)
        tmp_summary.replace(OUTPUT_SUMMARY)
        tmp_json.replace(OUTPUT_JSON)
        tmp_md.replace(OUTPUT_MD)
        
        # Clear temp files list after successful replacement
        temp_files = []
        
    finally:
        # Clean up any remaining temp files
        for tmp_path in temp_files:
            if tmp_path.exists():
                tmp_path.unlink()
    
    print("All outputs saved.")


def build_report_dict(event_provenance_results, group_stability_df, summary_df, validation_checks, validation_evidence, canonical_verification):
    """Build the report dictionary for JSON output."""
    
    # Identify special groups
    unanimous_order_groups = group_stability_df[group_stability_df["unanimous_order"]][["experiment", "target_project"]].to_dict(orient="records")
    unanimous_membership_but_nonunanimous_order_groups = group_stability_df[
        (group_stability_df["unanimous_membership"]) & (~group_stability_df["unanimous_order"])
    ][["experiment", "target_project"]].to_dict(orient="records")
    order_modal_tie_groups = group_stability_df[group_stability_df["order_modal_tie"]][["experiment", "target_project"]].to_dict(orient="records")
    membership_modal_tie_groups = group_stability_df[group_stability_df["membership_modal_tie"]][["experiment", "target_project"]].to_dict(orient="records")
    
    # Groups with minimum agreement
    min_order_agreement = group_stability_df["exact_order_pairwise_agreement"].min()
    minimum_order_agreement_groups = group_stability_df[
        group_stability_df["exact_order_pairwise_agreement"] == min_order_agreement
    ][["experiment", "target_project"]].to_dict(orient="records")
    
    min_membership_agreement = group_stability_df["exact_membership_pairwise_agreement"].min()
    minimum_membership_agreement_groups = group_stability_df[
        group_stability_df["exact_membership_pairwise_agreement"] == min_membership_agreement
    ][["experiment", "target_project"]].to_dict(orient="records")
    
    min_kendall_similarity = group_stability_df["mean_pairwise_kendall_similarity"].min()
    minimum_kendall_similarity_groups = group_stability_df[
        group_stability_df["mean_pairwise_kendall_similarity"] == min_kendall_similarity
    ][["experiment", "target_project"]].to_dict(orient="records")
    
    return {
        "canonical_verification": {
            "manifest_validation_status": canonical_verification["manifest_validation_status"],
            "repeated_results_sha256_verified": canonical_verification["repeated_results_sha256_verified"],
            "validation_log_sha256_verified": canonical_verification["validation_log_sha256_verified"],
            "evaluation_script_sha256_verified": canonical_verification["evaluation_script_sha256_verified"],
        },
        "event_provenance_validation": event_provenance_results,
        "metric_definitions": {
            "exact_order_pairwise_agreement": "Proportion of seed pairs with identical selected order",
            "exact_membership_pairwise_agreement": "Proportion of seed pairs with identical membership set",
            "mean_pairwise_jaccard": "Mean Jaccard similarity between membership sets across seed pairs",
            "mean_full_rank_position_agreement": "Mean proportion of candidates in same position across seed pairs",
            "mean_pairwise_kendall_tau": "Mean Kendall tau correlation between full rankings across seed pairs",
            "mean_pairwise_kendall_similarity": "Mean normalized Kendall similarity (tau+1)/2 across seed pairs",
        },
        "group_level_stability": group_stability_df.to_dict(orient="records"),
        "summary_overall": summary_df[summary_df["scope"] == "overall"].iloc[0].to_dict(),
        "summary_by_setting": {
            exp: summary_df[(summary_df["scope"] == "by_setting") & (summary_df["experiment"] == exp)].iloc[0].to_dict()
            for exp in EXPECTED_EXPERIMENTS
        },
        "special_groups": {
            "unanimous_order_groups": unanimous_order_groups,
            "unanimous_membership_but_nonunanimous_order_groups": unanimous_membership_but_nonunanimous_order_groups,
            "order_modal_tie_groups": order_modal_tie_groups,
            "membership_modal_tie_groups": membership_modal_tie_groups,
            "minimum_order_agreement_groups": minimum_order_agreement_groups,
            "minimum_membership_agreement_groups": minimum_membership_agreement_groups,
            "minimum_kendall_similarity_groups": minimum_kendall_similarity_groups,
        },
        "validation_checks": validation_checks,
        "validation_evidence": validation_evidence,
    }


def build_markdown_report(event_provenance_results, group_stability_df, summary_df, validation_checks, validation_evidence, canonical_verification):
    """Build the Markdown report as a string."""
    
    # Identify special groups
    unanimous_order_groups = group_stability_df[group_stability_df["unanimous_order"]][["experiment", "target_project"]].to_dict(orient="records")
    unanimous_membership_but_nonunanimous_order_groups = group_stability_df[
        (group_stability_df["unanimous_membership"]) & (~group_stability_df["unanimous_order"])
    ][["experiment", "target_project"]].to_dict(orient="records")
    order_modal_tie_groups = group_stability_df[group_stability_df["order_modal_tie"]][["experiment", "target_project"]].to_dict(orient="records")
    membership_modal_tie_groups = group_stability_df[group_stability_df["membership_modal_tie"]][["experiment", "target_project"]].to_dict(orient="records")
    
    # Groups with minimum agreement
    min_order_agreement = group_stability_df["exact_order_pairwise_agreement"].min()
    minimum_order_agreement_groups = group_stability_df[
        group_stability_df["exact_order_pairwise_agreement"] == min_order_agreement
    ][["experiment", "target_project"]].to_dict(orient="records")
    
    min_membership_agreement = group_stability_df["exact_membership_pairwise_agreement"].min()
    minimum_membership_agreement_groups = group_stability_df[
        group_stability_df["exact_membership_pairwise_agreement"] == min_membership_agreement
    ][["experiment", "target_project"]].to_dict(orient="records")
    
    min_kendall_similarity = group_stability_df["mean_pairwise_kendall_similarity"].min()
    minimum_kendall_similarity_groups = group_stability_df[
        group_stability_df["mean_pairwise_kendall_similarity"] == min_kendall_similarity
    ][["experiment", "target_project"]].to_dict(orient="records")
    
    lines = []
    lines.append("# Part 2 Section 3D: Soft-Top-3 Seed Stability Analysis\n\n")
    
    lines.append("## Canonical Verification\n\n")
    lines.append(f"- Manifest validation status: {canonical_verification['manifest_validation_status']}\n")
    lines.append(f"- Repeated results SHA-256 verified: {canonical_verification['repeated_results_sha256_verified']}\n")
    lines.append(f"- Validation log SHA-256 verified: {canonical_verification['validation_log_sha256_verified']}\n")
    lines.append(f"- Evaluation script SHA-256 verified: {canonical_verification['evaluation_script_sha256_verified']}\n\n")
    
    lines.append("## Event Provenance Validation\n\n")
    lines.append(f"- **Events checked:** {event_provenance_results['events_checked']}\n")
    lines.append(f"- **Canonical event mismatches:** {event_provenance_results['canonical_event_mismatches']}\n")
    lines.append(f"- **Validation ranking mismatches:** {event_provenance_results['validation_ranking_mismatches']}\n")
    lines.append(f"- **Score mismatches:** {event_provenance_results['score_mismatches']}\n")
    lines.append(f"- **Cutoff gap mismatches:** {event_provenance_results['cutoff_gap_mismatches']}\n\n")
    
    lines.append("## Stability Definitions\n\n")
    lines.append("- **Exact order pairwise agreement:** Proportion of seed pairs with identical selected order\n")
    lines.append("- **Exact membership pairwise agreement:** Proportion of seed pairs with identical membership set\n")
    lines.append("- **Mean pairwise Jaccard:** Mean Jaccard similarity between membership sets across seed pairs\n")
    lines.append("- **Mean full-rank position agreement:** Mean proportion of candidates in same position across seed pairs\n")
    lines.append("- **Mean pairwise Kendall tau:** Mean Kendall tau correlation between full rankings across seed pairs\n")
    lines.append("- **Mean pairwise Kendall similarity:** Mean normalized Kendall similarity (tau+1)/2 across seed pairs\n\n")
    
    lines.append("## Order Stability by Project and Setting\n\n")
    lines.append("| Experiment | Project | Distinct Orders | Modal Order(s) | Modal Count | Modal Prop | Unanimous |\n")
    lines.append("|------------|---------|-----------------|----------------|-------------|------------|-----------|\n")
    for _, row in group_stability_df.iterrows():
        lines.append(f"| {row['experiment']} | {row['target_project']} | {row['distinct_orders']} | {row['modal_orders']} | {row['modal_order_count']} | {row['modal_order_proportion']:.3f} | {row['unanimous_order']} |\n")
    lines.append("\n")
    
    lines.append("## Membership Stability by Project and Setting\n\n")
    lines.append("| Experiment | Project | Distinct Sets | Modal Set(s) | Modal Count | Modal Prop | Modal Excluded Candidate(s) | Unanimous |\n")
    lines.append("|------------|---------|---------------|--------------|-------------|------------|---------------------------|-----------|\n")
    for _, row in group_stability_df.iterrows():
        lines.append(f"| {row['experiment']} | {row['target_project']} | {row['distinct_membership_sets']} | {row['modal_membership_sets']} | {row['modal_membership_count']} | {row['modal_membership_proportion']:.3f} | {row['modal_excluded_candidates']} | {row['unanimous_membership']} |\n")
    lines.append("\n")
    
    lines.append("## Pairwise Order and Membership Agreement\n\n")
    lines.append("| Experiment | Project | Exact Order | Exact Membership | Jaccard | Position Agreement | Kendall Tau | Kendall Similarity |\n")
    lines.append("|------------|---------|-------------|------------------|---------|-------------------|-------------|-------------------|\n")
    for _, row in group_stability_df.iterrows():
        lines.append(f"| {row['experiment']} | {row['target_project']} | {row['exact_order_pairwise_agreement']:.3f} | {row['exact_membership_pairwise_agreement']:.3f} | {row['mean_pairwise_jaccard']:.3f} | {row['mean_full_rank_position_agreement']:.3f} | {row['mean_pairwise_kendall_tau']:.3f} | {row['mean_pairwise_kendall_similarity']:.3f} |\n")
    lines.append("\n")
    
    lines.append("## Overall Summary\n\n")
    overall = summary_df[summary_df["scope"] == "overall"].iloc[0]
    lines.append(f"- **Groups:** {overall['group_count']}\n")
    lines.append(f"- **Unanimous order groups:** {overall['unanimous_order_group_count']} ({overall['unanimous_order_group_proportion']:.3f})\n")
    lines.append(f"- **Unanimous membership groups:** {overall['unanimous_membership_group_count']} ({overall['unanimous_membership_group_proportion']:.3f})\n")
    lines.append(f"- **Mean distinct orders:** {overall['mean_distinct_orders']:.3f}\n")
    lines.append(f"- **Mean distinct membership sets:** {overall['mean_distinct_membership_sets']:.3f}\n")
    lines.append(f"- **Mean exact order agreement:** {overall['mean_exact_order_pairwise_agreement']:.3f}\n")
    lines.append(f"- **Mean exact membership agreement:** {overall['mean_exact_membership_pairwise_agreement']:.3f}\n")
    lines.append(f"- **Mean pairwise Jaccard:** {overall['mean_pairwise_jaccard']:.3f}\n")
    lines.append(f"- **Mean full-rank position agreement:** {overall['mean_full_rank_position_agreement']:.3f}\n")
    lines.append(f"- **Mean Kendall tau:** {overall['mean_pairwise_kendall_tau']:.3f}\n")
    lines.append(f"- **Mean Kendall similarity:** {overall['mean_pairwise_kendall_similarity']:.3f}\n")
    lines.append(f"- **Minimum cutoff score gap:** {overall['minimum_group_cutoff_score_gap']:.6f}\n\n")
    
    lines.append("## Within-Project Summary\n\n")
    wp = summary_df[(summary_df["scope"] == "by_setting") & (summary_df["experiment"] == "within_project")].iloc[0]
    lines.append(f"- **Groups:** {wp['group_count']}\n")
    lines.append(f"- **Unanimous order groups:** {wp['unanimous_order_group_count']} ({wp['unanimous_order_group_proportion']:.3f})\n")
    lines.append(f"- **Unanimous membership groups:** {wp['unanimous_membership_group_count']} ({wp['unanimous_membership_group_proportion']:.3f})\n")
    lines.append(f"- **Mean exact order agreement:** {wp['mean_exact_order_pairwise_agreement']:.3f}\n")
    lines.append(f"- **Mean exact membership agreement:** {wp['mean_exact_membership_pairwise_agreement']:.3f}\n")
    lines.append(f"- **Mean pairwise Jaccard:** {wp['mean_pairwise_jaccard']:.3f}\n")
    lines.append(f"- **Mean Kendall similarity:** {wp['mean_pairwise_kendall_similarity']:.3f}\n\n")
    
    lines.append("## Cross-Project Summary\n\n")
    cp = summary_df[(summary_df["scope"] == "by_setting") & (summary_df["experiment"] == "cross_project")].iloc[0]
    lines.append(f"- **Groups:** {cp['group_count']}\n")
    lines.append(f"- **Unanimous order groups:** {cp['unanimous_order_group_count']} ({cp['unanimous_order_group_proportion']:.3f})\n")
    lines.append(f"- **Unanimous membership groups:** {cp['unanimous_membership_group_count']} ({cp['unanimous_membership_group_proportion']:.3f})\n")
    lines.append(f"- **Mean exact order agreement:** {cp['mean_exact_order_pairwise_agreement']:.3f}\n")
    lines.append(f"- **Mean exact membership agreement:** {cp['mean_exact_membership_pairwise_agreement']:.3f}\n")
    lines.append(f"- **Mean pairwise Jaccard:** {cp['mean_pairwise_jaccard']:.3f}\n")
    lines.append(f"- **Mean Kendall similarity:** {cp['mean_pairwise_kendall_similarity']:.3f}\n\n")
    
    lines.append("## Special Stability Groups\n\n")
    lines.append(f"### Unanimous Order Groups ({len(unanimous_order_groups)})\n\n")
    for group in unanimous_order_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append(f"### Unanimous Membership but Nonunanimous Order Groups ({len(unanimous_membership_but_nonunanimous_order_groups)})\n\n")
    for group in unanimous_membership_but_nonunanimous_order_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append(f"### Order Modal Tie Groups ({len(order_modal_tie_groups)})\n\n")
    for group in order_modal_tie_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append(f"### Membership Modal Tie Groups ({len(membership_modal_tie_groups)})\n\n")
    for group in membership_modal_tie_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append(f"### Minimum Order Agreement Groups (agreement={min_order_agreement:.3f})\n\n")
    for group in minimum_order_agreement_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append(f"### Minimum Membership Agreement Groups (agreement={min_membership_agreement:.3f})\n\n")
    for group in minimum_membership_agreement_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append(f"### Minimum Kendall Similarity Groups (similarity={min_kendall_similarity:.3f})\n\n")
    for group in minimum_kendall_similarity_groups:
        lines.append(f"- {group['experiment']}/{group['target_project']}\n")
    lines.append("\n")
    
    lines.append("## Final Validation Evidence\n\n")
    lines.append("### Validation Checks\n\n")
    for check_name, passed in validation_checks.items():
        lines.append(f"- **{check_name}:** {passed}\n")
    lines.append("\n")
    
    lines.append("### Validation Evidence\n\n")
    for evidence_name, value in validation_evidence.items():
        lines.append(f"- **{evidence_name}:** {value}\n")
    lines.append("\n")
    
    lines.append("## Interpretation Limits\n\n")
    lines.append("These metrics describe categorical membership and ordering agreement of Soft-top-3 selections across five seeds.\n\n")
    lines.append("They are descriptive, not inferential, and do not establish predictive-performance stability, statistical significance, or superiority.\n\n")
    lines.append("Membership stability and ordering stability are distinct: identical candidate membership does not necessarily imply identical candidate ordering.\n")
    
    return "".join(lines)


def main():
    """Main entry point."""
    print("Starting soft-top-3 seed stability analysis...\n")
    
    # Load and verify inputs
    events_df, repeated_df, validation_df, canonical_verification = load_and_verify_inputs()
    
    # Verify event schema
    events_df = verify_event_schema(events_df)
    
    # Verify event provenance
    event_provenance_results = verify_event_provenance(events_df, repeated_df, validation_df)
    
    # Compute order counts
    order_counts_df = compute_order_counts(events_df)
    
    # Compute membership counts
    membership_counts_df = compute_membership_counts(events_df)
    
    # Compute group stability
    group_stability_df = compute_group_stability(events_df)
    
    # Compute summary
    summary_df = compute_summary(group_stability_df)
    
    # Validate final outputs
    validation_checks, validation_evidence = validate_final_outputs(
        order_counts_df,
        membership_counts_df,
        group_stability_df,
        summary_df,
        event_provenance_results,
        canonical_verification,
    )
    
    # Check for failed validations before writing
    failed_checks = [name for name, passed in validation_checks.items() if not passed]
    if failed_checks:
        raise ValueError(f"Final validation failed: {failed_checks}")
    
    # Save all outputs after validation passes
    save_all_outputs(
        order_counts_df,
        membership_counts_df,
        group_stability_df,
        summary_df,
        event_provenance_results,
        validation_checks,
        validation_evidence,
        canonical_verification,
    )
    
    print("\nSoft-top-3 seed stability analysis complete!")
    print(f"\nSummary:")
    print(f"  Events verified against canonical results: {event_provenance_results['events_checked']}")
    print(f"  Events verified against validation rankings: {event_provenance_results['events_checked']}")
    print(f"  Groups analyzed: {len(group_stability_df)}")
    print(f"  Order-count rows: {len(order_counts_df)}")
    print(f"  Membership-count rows: {len(membership_counts_df)}")
    print(f"  Group-stability rows: {len(group_stability_df)}")
    print(f"  Summary rows: {len(summary_df)}")
    print(f"  Unanimous-order groups: {int(group_stability_df['unanimous_order'].sum())}")
    print(f"  Unanimous-membership groups: {int(group_stability_df['unanimous_membership'].sum())}")
    print(f"  Order-modal-tie groups: {int(group_stability_df['order_modal_tie'].sum())}")
    print(f"  Membership-modal-tie groups: {int(group_stability_df['membership_modal_tie'].sum())}")
    print(f"  Mean exact-order agreement overall: {group_stability_df['exact_order_pairwise_agreement'].mean():.3f}")
    print(f"  Mean exact-membership agreement overall: {group_stability_df['exact_membership_pairwise_agreement'].mean():.3f}")
    print(f"  Mean pairwise Jaccard overall: {group_stability_df['mean_pairwise_jaccard'].mean():.3f}")
    print(f"  Mean full-rank position agreement overall: {group_stability_df['mean_full_rank_position_agreement'].mean():.3f}")
    print(f"  Mean Kendall similarity overall: {group_stability_df['mean_pairwise_kendall_similarity'].mean():.3f}")
    print(f"  Minimum cutoff score gap: {group_stability_df['minimum_cutoff_score_gap'].min():.6f}")


if __name__ == "__main__":
    main()
