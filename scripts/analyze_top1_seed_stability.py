#!/usr/bin/env python3
"""
Part 2 Section 2C: Analyze top-1 seed stability
Computes descriptive stability metrics for candidate selections across five seeds.
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
OUTPUT_DIR = BASE_DIR / "results" / "part2_candidate_selection"

# Input files
MANIFEST_PATH = REPORTS_DIR / "part1_canonical_manifest.json"
READINESS_PATH = REPORTS_DIR / "part2_analysis_readiness.json"
FREQUENCY_PATH = REPORTS_DIR / "part2_top1_selection_frequency.json"
EVENTS_PATH = OUTPUT_DIR / "top1_selection_events.csv"
REPEATED_RESULTS_PATH = CANONICAL_RESULT_DIR / "repeated_all_results.csv"

# Output files
OUTPUT_CANDIDATE_COUNTS = OUTPUT_DIR / "top1_seed_stability_candidate_counts.csv"
OUTPUT_BY_GROUP = OUTPUT_DIR / "top1_seed_stability_by_group.csv"
OUTPUT_SUMMARY = OUTPUT_DIR / "top1_seed_stability_summary.csv"
OUTPUT_JSON = REPORTS_DIR / "part2_top1_seed_stability.json"
OUTPUT_MD = REPORTS_DIR / "part2_top1_seed_stability.md"

# Constants
SELECTOR_MODELS = ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc"]
SELECTOR_TO_MODE = {
    "AQRPE_v2_balanced": "balanced",
    "AQRPE_v2_rank": "rank",
    "AQRPE_v2_mcc": "mcc",
}
BASELINE_MODELS = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
EXPECTED_EXPERIMENTS = ["within_project", "cross_project"]
EXPECTED_PROJECTS = ["CM1", "JM1", "KC1", "KC2", "PC1"]
EXPECTED_SEEDS = [7, 13, 29, 42, 101]
CANDIDATE_ORDER = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]

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
    
    # Load frequency report
    with open(FREQUENCY_PATH, "r") as f:
        frequency = json.load(f)
    
    # Verify manifest status
    if manifest.get("manifest_validation_status") != "all_checks_passed":
        raise ValueError(f"Manifest validation status is '{manifest.get('manifest_validation_status')}', expected 'all_checks_passed'")
    
    # Verify readiness final validation
    if readiness["final_validation"]["top_1_models_valid"] != "3/3":
        raise ValueError(f"Top-1 models validation failed: {readiness['final_validation']['top_1_models_valid']}")
    
    # Verify provenance validation
    if frequency["provenance_validation"]["runs_checked"] != 150:
        raise ValueError(f"Expected 150 runs checked, got {frequency['provenance_validation']['runs_checked']}")
    if frequency["provenance_validation"]["selected_candidate_mismatches"] != 0:
        raise ValueError(f"Selected candidate mismatches: {frequency['provenance_validation']['selected_candidate_mismatches']}")
    if frequency["provenance_validation"]["selection_score_mismatches"] != 0:
        raise ValueError(f"Selection score mismatches: {frequency['provenance_validation']['selection_score_mismatches']}")
    if frequency["provenance_validation"]["threshold_mismatches"] != 0:
        raise ValueError(f"Threshold mismatches: {frequency['provenance_validation']['threshold_mismatches']}")
    if frequency["provenance_validation"]["selection_mode_mismatches"] != 0:
        raise ValueError(f"Selection mode mismatches: {frequency['provenance_validation']['selection_mode_mismatches']}")
    
    # Verify SHA-256
    def compute_sha256(path):
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    expected_sha = {
        "repeated_all_results.csv": manifest["canonical_reproduction_outputs"]["repeated_all_results.csv"]["sha256"],
    }
    
    actual_sha = {
        "repeated_all_results.csv": compute_sha256(REPEATED_RESULTS_PATH),
    }
    
    for name, expected in expected_sha.items():
        if actual_sha[name] != expected:
            raise ValueError(f"SHA-256 mismatch for {name}")
    
    # Load data files
    events_df = pd.read_csv(EVENTS_PATH)
    repeated_df = pd.read_csv(REPEATED_RESULTS_PATH)
    
    print("Inputs verified.")
    return events_df, repeated_df


def verify_events_schema(events_df):
    """Verify events file schema and content."""
    print("Verifying events schema...")
    
    # Verify column order
    expected_cols = ["experiment", "target_project", "seed", "selector_model", "mode", 
                     "selected_candidate", "threshold", "selection_score"]
    if list(events_df.columns) != expected_cols:
        raise ValueError(f"Column mismatch: expected {expected_cols}, got {list(events_df.columns)}")
    
    # Verify row count
    if len(events_df) != 150:
        raise ValueError(f"Expected 150 event rows, got {len(events_df)}")
    
    # Verify column count
    if len(events_df.columns) != 8:
        raise ValueError(f"Expected 8 columns, got {len(events_df.columns)}")
    
    # Check for nulls
    if events_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in events")
    
    # Check for duplicate keys
    key_cols = ["experiment", "target_project", "seed", "selector_model"]
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
    
    # Verify selectors
    selectors = set(events_df["selector_model"].unique())
    if selectors != set(SELECTOR_MODELS):
        raise ValueError(f"Selectors mismatch: expected {SELECTOR_MODELS}, got {selectors}")
    
    # Verify candidates
    candidates = set(events_df["selected_candidate"].unique())
    if candidates != set(BASELINE_MODELS):
        raise ValueError(f"Candidates mismatch: expected {BASELINE_MODELS}, got {candidates}")
    
    # Verify each selector × experiment × project has exactly 5 seeds
    for selector in SELECTOR_MODELS:
        for experiment in EXPECTED_EXPERIMENTS:
            for project in EXPECTED_PROJECTS:
                subset = events_df[
                    (events_df["selector_model"] == selector) &
                    (events_df["experiment"] == experiment) &
                    (events_df["target_project"] == project)
                ]
                if len(subset) != 5:
                    raise ValueError(f"Expected 5 seeds for {selector}/{experiment}/{project}, got {len(subset)}")
    
    # Verify group count
    group_count = len(SELECTOR_MODELS) * len(EXPECTED_EXPERIMENTS) * len(EXPECTED_PROJECTS)
    if group_count != 30:
        raise ValueError(f"Expected 30 groups, got {group_count}")
    
    print("Events schema verified.")
    return events_df


def verify_events_against_canonical(events_df, repeated_df):
    """Verify events match canonical repeated_all_results.csv."""
    print("Verifying events against canonical results...")
    
    mismatches = {
        "selected_candidate": 0,
        "threshold": 0,
        "selection_score": 0,
    }
    
    for _, event_row in events_df.iterrows():
        experiment = event_row["experiment"]
        target_project = event_row["target_project"]
        seed = event_row["seed"]
        selector_model = event_row["selector_model"]
        
        # Find corresponding row in repeated_all_results
        canonical_row = repeated_df[
            (repeated_df["experiment"] == experiment) &
            (repeated_df["target_project"] == target_project) &
            (repeated_df["seed"] == seed) &
            (repeated_df["model"] == selector_model)
        ]
        
        if len(canonical_row) != 1:
            raise ValueError(f"Expected 1 canonical row for {experiment}/{target_project}/{seed}/{selector_model}, got {len(canonical_row)}")
        
        # Verify selected_candidate
        if event_row["selected_candidate"] != canonical_row["selected_candidate"].iloc[0]:
            mismatches["selected_candidate"] += 1
        
        # Verify threshold
        if abs(event_row["threshold"] - canonical_row["threshold"].iloc[0]) > TOLERANCE:
            mismatches["threshold"] += 1
        
        # Verify selection_score
        if abs(event_row["selection_score"] - canonical_row["selection_score"].iloc[0]) > TOLERANCE:
            mismatches["selection_score"] += 1
    
    if mismatches["selected_candidate"] > 0:
        raise ValueError(f"Selected candidate mismatches: {mismatches['selected_candidate']}")
    if mismatches["threshold"] > 0:
        raise ValueError(f"Threshold mismatches: {mismatches['threshold']}")
    if mismatches["selection_score"] > 0:
        raise ValueError(f"Selection score mismatches: {mismatches['selection_score']}")
    
    print("Events verified against canonical results.")
    return True


def compute_candidate_counts(events_df):
    """Compute candidate counts for each group."""
    print("Computing candidate counts...")
    
    # Count selections by group and candidate
    counts = events_df.groupby(
        ["selector_model", "mode", "experiment", "target_project", "selected_candidate"]
    ).size().reset_index(name="count")
    counts = counts.rename(columns={"selected_candidate": "candidate"})
    
    # Create all combinations
    all_combos = []
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        for experiment in EXPECTED_EXPERIMENTS:
            for project in EXPECTED_PROJECTS:
                for candidate in BASELINE_MODELS:
                    all_combos.append({
                        "selector_model": selector,
                        "mode": mode,
                        "experiment": experiment,
                        "target_project": project,
                        "candidate": candidate,
                    })
    
    all_combos_df = pd.DataFrame(all_combos)
    
    # Merge with counts to include zero counts
    counts = all_combos_df.merge(counts, on=["selector_model", "mode", "experiment", "target_project", "candidate"], how="left").fillna(0)
    counts["count"] = counts["count"].astype(int)
    
    # Add denominator and proportion
    counts["denominator"] = 5
    counts["proportion"] = counts["count"] / counts["denominator"]
    
    # Verify row count
    if len(counts) != 120:
        raise ValueError(f"Expected 120 candidate-count rows, got {len(counts)}")
    
    # Verify sums
    for selector in SELECTOR_MODELS:
        for experiment in EXPECTED_EXPERIMENTS:
            for project in EXPECTED_PROJECTS:
                subset = counts[
                    (counts["selector_model"] == selector) &
                    (counts["experiment"] == experiment) &
                    (counts["target_project"] == project)
                ]
                subset_sum = subset["count"].sum()
                if subset_sum != 5:
                    raise ValueError(f"Expected sum 5 for {selector}/{experiment}/{project}, got {subset_sum}")
                subset_prop_sum = subset["proportion"].sum()
                if abs(subset_prop_sum - 1.0) > TOLERANCE:
                    raise ValueError(f"Expected proportion sum 1.0 for {selector}/{experiment}/{project}, got {subset_prop_sum}")
    
    # Sort
    counts = counts.sort_values(["selector_model", "mode", "experiment", "target_project", "candidate"])
    
    counts.to_csv(OUTPUT_CANDIDATE_COUNTS, index=False)
    
    print("Candidate counts computed.")
    return counts


def compute_group_stability(events_df, candidate_counts):
    """Compute stability metrics for each group."""
    print("Computing group stability...")
    
    stability_rows = []
    
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        for experiment in EXPECTED_EXPERIMENTS:
            for project in EXPECTED_PROJECTS:
                # Get candidate counts for this group
                group_counts = candidate_counts[
                    (candidate_counts["selector_model"] == selector) &
                    (candidate_counts["experiment"] == experiment) &
                    (candidate_counts["target_project"] == project)
                ].copy()
                
                n_seeds = 5
                distinct_candidates = int((group_counts["count"] > 0).sum())
                
                # Find modal candidates
                max_count = group_counts["count"].max()
                modal_candidates_df = group_counts[group_counts["count"] == max_count]
                modal_candidates = sorted(modal_candidates_df["candidate"].tolist(), key=lambda x: CANDIDATE_ORDER.index(x))
                modal_candidates_str = "|".join(modal_candidates)
                modal_count = int(max_count)
                modal_proportion = modal_count / 5
                modal_tie = len(modal_candidates) > 1
                
                # Unanimous
                unanimous = modal_count == 5
                
                # At least four of five
                at_least_four_of_five = modal_count >= 4
                
                # Pairwise agreement
                pairwise_agreement = sum(
                    count * (count - 1) / 2 for count in group_counts["count"]
                ) / 10
                
                # Shannon entropy
                proportions = group_counts["proportion"].values
                proportions = proportions[proportions > 0]
                shannon_entropy = -np.sum(proportions * np.log(proportions))
                
                # Normalized entropy
                normalized_entropy = shannon_entropy / np.log(4)
                
                stability_rows.append({
                    "selector_model": selector,
                    "mode": mode,
                    "experiment": experiment,
                    "target_project": project,
                    "n_seeds": n_seeds,
                    "distinct_candidates": distinct_candidates,
                    "modal_candidates": modal_candidates_str,
                    "modal_count": modal_count,
                    "modal_proportion": modal_proportion,
                    "modal_tie": modal_tie,
                    "unanimous": unanimous,
                    "at_least_four_of_five": at_least_four_of_five,
                    "pairwise_agreement": pairwise_agreement,
                    "shannon_entropy_nats": shannon_entropy,
                    "normalized_entropy": normalized_entropy,
                })
    
    stability_df = pd.DataFrame(stability_rows)
    
    # Verify row count
    if len(stability_df) != 30:
        raise ValueError(f"Expected 30 stability rows, got {len(stability_df)}")
    
    # Sort
    stability_df = stability_df.sort_values(["selector_model", "mode", "experiment", "target_project"])
    
    stability_df.to_csv(OUTPUT_BY_GROUP, index=False)
    
    print("Group stability computed.")
    return stability_df


def compute_summary(stability_df):
    """Compute summary statistics."""
    print("Computing summary statistics...")
    
    summary_rows = []
    
    # Overall summaries for each selector
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        selector_subset = stability_df[stability_df["selector_model"] == selector]
        
        summary_rows.append({
            "scope": "overall",
            "selector_model": selector,
            "mode": mode,
            "experiment": "all",
            "group_count": 10,
            "unanimous_group_count": int(selector_subset["unanimous"].sum()),
            "unanimous_group_proportion": selector_subset["unanimous"].mean(),
            "at_least_four_group_count": int(selector_subset["at_least_four_of_five"].sum()),
            "at_least_four_group_proportion": selector_subset["at_least_four_of_five"].mean(),
            "modal_tie_group_count": int(selector_subset["modal_tie"].sum()),
            "mean_modal_proportion": selector_subset["modal_proportion"].mean(),
            "median_modal_proportion": selector_subset["modal_proportion"].median(),
            "min_modal_proportion": selector_subset["modal_proportion"].min(),
            "max_modal_proportion": selector_subset["modal_proportion"].max(),
            "mean_pairwise_agreement": selector_subset["pairwise_agreement"].mean(),
            "median_pairwise_agreement": selector_subset["pairwise_agreement"].median(),
            "min_pairwise_agreement": selector_subset["pairwise_agreement"].min(),
            "max_pairwise_agreement": selector_subset["pairwise_agreement"].max(),
            "mean_normalized_entropy": selector_subset["normalized_entropy"].mean(),
            "median_normalized_entropy": selector_subset["normalized_entropy"].median(),
            "min_normalized_entropy": selector_subset["normalized_entropy"].min(),
            "max_normalized_entropy": selector_subset["normalized_entropy"].max(),
        })
    
    # By-setting summaries
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        for experiment in EXPECTED_EXPERIMENTS:
            subset = stability_df[
                (stability_df["selector_model"] == selector) &
                (stability_df["experiment"] == experiment)
            ]
            
            summary_rows.append({
                "scope": "by_setting",
                "selector_model": selector,
                "mode": mode,
                "experiment": experiment,
                "group_count": 5,
                "unanimous_group_count": int(subset["unanimous"].sum()),
                "unanimous_group_proportion": subset["unanimous"].mean(),
                "at_least_four_group_count": int(subset["at_least_four_of_five"].sum()),
                "at_least_four_group_proportion": subset["at_least_four_of_five"].mean(),
                "modal_tie_group_count": int(subset["modal_tie"].sum()),
                "mean_modal_proportion": subset["modal_proportion"].mean(),
                "median_modal_proportion": subset["modal_proportion"].median(),
                "min_modal_proportion": subset["modal_proportion"].min(),
                "max_modal_proportion": subset["modal_proportion"].max(),
                "mean_pairwise_agreement": subset["pairwise_agreement"].mean(),
                "median_pairwise_agreement": subset["pairwise_agreement"].median(),
                "min_pairwise_agreement": subset["pairwise_agreement"].min(),
                "max_pairwise_agreement": subset["pairwise_agreement"].max(),
                "mean_normalized_entropy": subset["normalized_entropy"].mean(),
                "median_normalized_entropy": subset["normalized_entropy"].median(),
                "min_normalized_entropy": subset["normalized_entropy"].min(),
                "max_normalized_entropy": subset["normalized_entropy"].max(),
            })
    
    summary_df = pd.DataFrame(summary_rows)
    
    # Verify row count
    if len(summary_df) != 9:
        raise ValueError(f"Expected 9 summary rows, got {len(summary_df)}")
    
    # Check for nulls
    if summary_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in summary")
    
    # Sort
    summary_df = summary_df.sort_values(["scope", "selector_model", "experiment"])
    
    summary_df.to_csv(OUTPUT_SUMMARY, index=False)
    
    print("Summary statistics computed.")
    return summary_df


def perform_validation_checks(stability_df):
    """Perform logical validation checks."""
    print("Performing validation checks...")
    
    validation_results = {
        "n_seeds_check": True,
        "distinct_candidates_check": True,
        "modal_count_check": True,
        "modal_proportion_check": True,
        "pairwise_agreement_range_check": True,
        "normalized_entropy_range_check": True,
        "unanimous_consistency_check": True,
        "errors": [],
    }
    
    for _, row in stability_df.iterrows():
        # Check n_seeds
        if row["n_seeds"] != 5:
            validation_results["n_seeds_check"] = False
            validation_results["errors"].append(f"n_seeds != 5 for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
        
        # Check distinct_candidates range
        if not (1 <= row["distinct_candidates"] <= 4):
            validation_results["distinct_candidates_check"] = False
            validation_results["errors"].append(f"distinct_candidates out of range for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
        
        # Check modal_count range
        if not (1 <= row["modal_count"] <= 5):
            validation_results["modal_count_check"] = False
            validation_results["errors"].append(f"modal_count out of range for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
        
        # Check modal_proportion
        expected_modal_proportion = row["modal_count"] / 5
        if abs(row["modal_proportion"] - expected_modal_proportion) > TOLERANCE:
            validation_results["modal_proportion_check"] = False
            validation_results["errors"].append(f"modal_proportion mismatch for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
        
        # Check pairwise_agreement range
        if not (0 <= row["pairwise_agreement"] <= 1):
            validation_results["pairwise_agreement_range_check"] = False
            validation_results["errors"].append(f"pairwise_agreement out of range for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
        
        # Check normalized_entropy range
        if not (0 <= row["normalized_entropy"] <= 1):
            validation_results["normalized_entropy_range_check"] = False
            validation_results["errors"].append(f"normalized_entropy out of range for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
        
        # Check unanimous consistency
        if row["unanimous"]:
            if not (
                row["distinct_candidates"] == 1 and
                row["modal_count"] == 5 and
                abs(row["pairwise_agreement"] - 1.0) <= TOLERANCE and
                abs(row["normalized_entropy"] - 0.0) <= TOLERANCE
            ):
                validation_results["unanimous_consistency_check"] = False
                validation_results["errors"].append(f"unanimous consistency failed for {row['selector_model']}/{row['experiment']}/{row['target_project']}")
    
    if validation_results["errors"]:
        raise ValueError(f"Validation errors: {validation_results['errors']}")
    
    print("Validation checks passed.")
    return validation_results


def save_reports(stability_df, summary_df, validation_results):
    """Save JSON and Markdown reports."""
    print("Saving reports...")
    
    # Build JSON report
    report = {
        "canonical_verification": {
            "manifest_validation_status": "all_checks_passed",
            "sha256_verified": True,
        },
        "event_provenance_validation": {
            "events_verified_against_canonical": True,
        },
        "group_level_stability": stability_df.to_dict(orient="records"),
        "summary_overall": summary_df[summary_df["scope"] == "overall"].to_dict(orient="records"),
        "summary_by_setting": summary_df[summary_df["scope"] == "by_setting"].to_dict(orient="records"),
        "validation_checks": validation_results,
    }
    
    with open(OUTPUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    
    # Build Markdown report
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 2 Section 2C: Top-1 Seed Stability Analysis\n\n")
        
        f.write("## Canonical Verification\n\n")
        f.write("- Manifest validation status: all_checks_passed\n")
        f.write("- SHA-256 verified: True\n\n")
        
        f.write("## Event Provenance Validation\n\n")
        f.write("- Events verified against canonical repeated_all_results.csv: True\n")
        f.write("- All 150 events match canonical values within tolerance\n\n")
        
        f.write("## Stability Definitions\n\n")
        f.write("**Modal candidates:** All candidates with the highest count in a group (5 seeds).\n")
        f.write("**Modal proportion:** modal_count / 5\n")
        f.write("**Pairwise agreement:** Proportion of agreeing seed pairs (10 possible pairs).\n")
        f.write("**Shannon entropy:** -sum(p * log(p)) for candidate proportions.\n")
        f.write("**Normalized entropy:** entropy / log(4), bounded [0, 1].\n")
        f.write("**Unanimous:** All 5 seeds selected the same candidate.\n")
        f.write("**At least four of five:** Modal candidate selected by >= 4 seeds.\n\n")
        
        f.write("## Group-Level Stability\n\n")
        f.write("| Selector | Mode | Experiment | Project | N Seeds | Distinct | Modal Candidates | Modal Count | Modal Prop | Modal Tie | Unanimous | >=4/5 | Pairwise Agree | Norm Entropy |\n")
        f.write("|----------|------|------------|---------|---------|----------|-------------------|-------------|------------|-----------|----------|-----------------|--------------|\n")
        for _, row in stability_df.iterrows():
            f.write(f"| {row['selector_model']} | {row['mode']} | {row['experiment']} | {row['target_project']} | {row['n_seeds']} | {row['distinct_candidates']} | {row['modal_candidates']} | {row['modal_count']} | {row['modal_proportion']:.3f} | {row['modal_tie']} | {row['unanimous']} | {row['at_least_four_of_five']} | {row['pairwise_agreement']:.3f} | {row['normalized_entropy']:.3f} |\n")
        f.write("\n")
        
        f.write("## Overall Selector Summaries\n\n")
        f.write("| Selector | Mode | Groups | Unanimous | Unanimous % | >=4/5 | >=4/5 % | Modal Ties | Mean Modal Prop | Median Modal Prop | Mean Pairwise | Median Pairwise | Mean Entropy | Median Entropy |\n")
        f.write("|----------|------|--------|-----------|-------------|-------|----------|-------------|-----------------|-------------------|---------------|-----------------|---------------|----------------|\n")
        overall_df = summary_df[summary_df["scope"] == "overall"]
        for _, row in overall_df.iterrows():
            f.write(f"| {row['selector_model']} | {row['mode']} | {row['group_count']} | {row['unanimous_group_count']} | {row['unanimous_group_proportion']:.3f} | {row['at_least_four_group_count']} | {row['at_least_four_group_proportion']:.3f} | {row['modal_tie_group_count']} | {row['mean_modal_proportion']:.3f} | {row['median_modal_proportion']:.3f} | {row['mean_pairwise_agreement']:.3f} | {row['median_pairwise_agreement']:.3f} | {row['mean_normalized_entropy']:.3f} | {row['median_normalized_entropy']:.3f} |\n")
        f.write("\n")
        
        f.write("## Selector Summaries by Setting\n\n")
        f.write("| Selector | Mode | Experiment | Groups | Unanimous | Unanimous % | >=4/5 | >=4/5 % | Modal Ties | Mean Modal Prop | Median Modal Prop | Mean Pairwise | Median Pairwise | Mean Entropy | Median Entropy |\n")
        f.write("|----------|------|------------|--------|-----------|-------------|-------|----------|-------------|-----------------|-------------------|---------------|-----------------|---------------|----------------|\n")
        by_setting_df = summary_df[summary_df["scope"] == "by_setting"]
        for _, row in by_setting_df.iterrows():
            f.write(f"| {row['selector_model']} | {row['mode']} | {row['experiment']} | {row['group_count']} | {row['unanimous_group_count']} | {row['unanimous_group_proportion']:.3f} | {row['at_least_four_group_count']} | {row['at_least_four_group_proportion']:.3f} | {row['modal_tie_group_count']} | {row['mean_modal_proportion']:.3f} | {row['median_modal_proportion']:.3f} | {row['mean_pairwise_agreement']:.3f} | {row['median_pairwise_agreement']:.3f} | {row['mean_normalized_entropy']:.3f} | {row['median_normalized_entropy']:.3f} |\n")
        f.write("\n")
        
        f.write("## Groups with Modal Ties\n\n")
        tie_groups = stability_df[stability_df["modal_tie"]]
        if len(tie_groups) > 0:
            f.write("| Selector | Experiment | Project | Modal Candidates | Modal Count |\n")
            f.write("|----------|------------|---------|------------------|-------------|\n")
            for _, row in tie_groups.iterrows():
                f.write(f"| {row['selector_model']} | {row['experiment']} | {row['target_project']} | {row['modal_candidates']} | {row['modal_count']} |\n")
        else:
            f.write("No groups with modal ties.\n")
        f.write("\n")
        
        f.write("## Groups with Unanimous Selection\n\n")
        unanimous_groups = stability_df[stability_df["unanimous"]]
        if len(unanimous_groups) > 0:
            f.write("| Selector | Experiment | Project | Selected Candidate |\n")
            f.write("|----------|------------|---------|-------------------|\n")
            for _, row in unanimous_groups.iterrows():
                f.write(f"| {row['selector_model']} | {row['experiment']} | {row['target_project']} | {row['modal_candidates']} |\n")
        else:
            f.write("No groups with unanimous selection.\n")
        f.write("\n")
        
        f.write("## Interpretation Limits\n\n")
        f.write("These metrics describe categorical agreement of candidate selections across five seeds.\n")
        f.write("They are not inferential tests and do not establish performance stability, statistical significance, or model superiority.\n\n")
    
    print("Reports saved.")


def main():
    """Main entry point."""
    print("Starting top-1 seed stability analysis...\n")
    
    # Load and verify inputs
    events_df, repeated_df = load_and_verify_inputs()
    
    # Verify events schema
    events_df = verify_events_schema(events_df)
    
    # Verify events against canonical
    verify_events_against_canonical(events_df, repeated_df)
    
    # Compute candidate counts
    candidate_counts = compute_candidate_counts(events_df)
    
    # Compute group stability
    stability_df = compute_group_stability(events_df, candidate_counts)
    
    # Compute summary
    summary_df = compute_summary(stability_df)
    
    # Perform validation checks
    validation_results = perform_validation_checks(stability_df)
    
    # Save reports
    save_reports(stability_df, summary_df, validation_results)
    
    print("\nTop-1 seed stability analysis complete!")
    print(f"\nSummary:")
    print(f"  Events verified against canonical results: True")
    print(f"  Groups analyzed: {len(stability_df)}")
    print(f"  Candidate-count rows: {len(candidate_counts)}")
    print(f"  Group-stability rows: {len(stability_df)}")
    print(f"  Summary rows: {len(summary_df)}")
    print(f"  Unanimous groups: {int(stability_df['unanimous'].sum())}")
    print(f"  At-least-four-of-five groups: {int(stability_df['at_least_four_of_five'].sum())}")
    print(f"  Modal-tie groups: {int(stability_df['modal_tie'].sum())}")
    print(f"  Mean pairwise agreement by selector:")
    for selector in SELECTOR_MODELS:
        selector_df = stability_df[stability_df["selector_model"] == selector]
        print(f"    {selector}: {selector_df['pairwise_agreement'].mean():.3f}")
    print(f"  Mean normalized entropy by selector:")
    for selector in SELECTOR_MODELS:
        selector_df = stability_df[stability_df["selector_model"] == selector]
        print(f"    {selector}: {selector_df['normalized_entropy'].mean():.3f}")


if __name__ == "__main__":
    main()
