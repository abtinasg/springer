#!/usr/bin/env python3
"""
Part 2 Section 2A: Analyze top-1 selection frequency
Computes selection frequency for three top-1 methods without running new models.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

# Base directory for portable paths
BASE_DIR = Path(__file__).resolve().parents[1]

# Paths
CANONICAL_RESULT_DIR = BASE_DIR / "results" / "part1_full_reproduction"
REPORTS_DIR = BASE_DIR / "reports"
OUTPUT_DIR = BASE_DIR / "results" / "part2_candidate_selection"

# Input files
MANIFEST_PATH = REPORTS_DIR / "part1_canonical_manifest.json"
READINESS_PATH = REPORTS_DIR / "part2_analysis_readiness.json"
REPEATED_RESULTS_PATH = CANONICAL_RESULT_DIR / "repeated_all_results.csv"
VALIDATION_LOG_PATH = CANONICAL_RESULT_DIR / "validation_log.csv"

# Output files
OUTPUT_EVENTS = OUTPUT_DIR / "top1_selection_events.csv"
OUTPUT_OVERALL = OUTPUT_DIR / "top1_selection_frequency_overall.csv"
OUTPUT_BY_SETTING = OUTPUT_DIR / "top1_selection_frequency_by_setting.csv"
OUTPUT_BY_PROJECT = OUTPUT_DIR / "top1_selection_frequency_by_project.csv"
OUTPUT_JSON = REPORTS_DIR / "part2_top1_selection_frequency.json"
OUTPUT_MD = REPORTS_DIR / "part2_top1_selection_frequency.md"

# Top-1 selector mappings
SELECTOR_MODELS = ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc"]
SELECTOR_TO_MODE = {
    "AQRPE_v2_balanced": "balanced",
    "AQRPE_v2_rank": "rank",
    "AQRPE_v2_mcc": "mcc",
}
EXPECTED_SELECTION_MODE = {
    "AQRPE_v2_balanced": "balanced_objective",
    "AQRPE_v2_rank": "rank_objective_fixed_threshold",
    "AQRPE_v2_mcc": "mcc_objective",
}
BASELINE_MODELS = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]

# Tolerance for floating point comparisons
TOLERANCE = 1e-12


def load_and_verify_inputs():
    """Load and verify all input files and readiness status."""
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
    
    # Verify final validation
    if readiness["final_validation"]["top_1_models_valid"] != "3/3":
        raise ValueError(f"Top-1 models validation failed: {readiness['final_validation']['top_1_models_valid']}")
    if readiness["final_validation"]["exact_repeated_result_runs"] != "50/50":
        raise ValueError(f"Repeated result runs validation failed: {readiness['final_validation']['exact_repeated_result_runs']}")
    if readiness["final_validation"]["exact_validation_log_runs"] != "50/50":
        raise ValueError(f"Validation log runs validation failed: {readiness['final_validation']['exact_validation_log_runs']}")
    
    # Verify SHA-256
    import hashlib
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
    
    # Load data files
    repeated_df = pd.read_csv(REPEATED_RESULTS_PATH)
    validation_df = pd.read_csv(VALIDATION_LOG_PATH)
    
    print("Inputs verified.")
    return repeated_df, validation_df


def extract_top1_selections(repeated_df):
    """Extract top-1 selection events from repeated_all_results.csv."""
    print("Extracting top-1 selections...")
    
    # Filter to only top-1 selector models
    top1_df = repeated_df[repeated_df["model"].isin(SELECTOR_MODELS)].copy()
    
    # Verify row count
    if len(top1_df) != 150:
        raise ValueError(f"Expected 150 top-1 selection rows, got {len(top1_df)}")
    
    # Verify each selector has exactly 50 rows
    for selector in SELECTOR_MODELS:
        selector_rows = top1_df[top1_df["model"] == selector]
        if len(selector_rows) != 50:
            raise ValueError(f"Expected 50 rows for {selector}, got {len(selector_rows)}")
    
    # Check for duplicate keys
    key_cols = ["experiment", "target_project", "seed", "model"]
    duplicates = top1_df.duplicated(subset=key_cols)
    if duplicates.sum() > 0:
        raise ValueError(f"Found {duplicates.sum()} duplicate keys in top-1 selections")
    
    # Check for null values
    if top1_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in top-1 selections")
    
    # Rename model to selector_model for clarity
    top1_df = top1_df.rename(columns={"model": "selector_model"})
    
    # Add mode column
    top1_df["mode"] = top1_df["selector_model"].map(SELECTOR_TO_MODE)
    
    print("Top-1 selections extracted.")
    return top1_df


def validate_selection_provenance(top1_df, validation_df):
    """Validate that selected candidates match validation winners."""
    print("Validating selection provenance...")
    
    results = {
        "runs_checked": 0,
        "selected_candidate_mismatches": 0,
        "selection_score_mismatches": 0,
        "threshold_mismatches": 0,
        "selection_mode_mismatches": 0,
        "validation_tie_runs": 0,
    }
    
    mismatches = []
    
    for _, row in top1_df.iterrows():
        results["runs_checked"] += 1
        
        experiment = row["experiment"]
        target_project = row["target_project"]
        seed = row["seed"]
        selector_model = row["selector_model"]
        mode = row["mode"]
        selected_candidate = row["selected_candidate"]
        selection_score = row["selection_score"]
        threshold = row["threshold"]
        selection_mode = row["selection_mode"]
        
        # Find corresponding validation rows
        val_subset = validation_df[
            (validation_df["experiment"] == experiment) &
            (validation_df["target_project"] == target_project) &
            (validation_df["seed"] == seed) &
            (validation_df["mode"] == mode)
        ]
        
        if len(val_subset) != 4:
            raise ValueError(f"Expected 4 validation rows for {experiment}/{target_project}/{seed}/{mode}, got {len(val_subset)}")
        
        # Find maximum validation score
        max_val_score = val_subset["val_selection_score"].max()
        
        # Find all candidates within tolerance of max (ties)
        tolerance_mask = (val_subset["val_selection_score"] - max_val_score).abs() <= TOLERANCE
        validation_winners = set(val_subset[tolerance_mask]["candidate"].tolist())
        
        # Check for validation ties
        if len(validation_winners) > 1:
            results["validation_tie_runs"] += 1
        
        # Verify selected candidate is in validation winners
        if selected_candidate not in validation_winners:
            results["selected_candidate_mismatches"] += 1
            mismatches.append({
                "type": "selected_candidate",
                "selector": selector_model,
                "experiment": experiment,
                "target_project": target_project,
                "seed": seed,
                "expected": validation_winners,
                "actual": selected_candidate,
            })
        
        # Verify selection score matches validation score
        val_row = val_subset[val_subset["candidate"] == selected_candidate]
        if len(val_row) == 0:
            results["selection_score_mismatches"] += 1
        else:
            val_score = val_row["val_selection_score"].iloc[0]
            if abs(selection_score - val_score) > TOLERANCE:
                results["selection_score_mismatches"] += 1
                mismatches.append({
                    "type": "selection_score",
                    "selector": selector_model,
                    "experiment": experiment,
                    "target_project": target_project,
                    "seed": seed,
                    "expected": val_score,
                    "actual": selection_score,
                })
        
        # Verify threshold matches validation threshold
        if len(val_row) > 0:
            val_threshold = val_row["val_threshold"].iloc[0]
            if abs(threshold - val_threshold) > TOLERANCE:
                results["threshold_mismatches"] += 1
                mismatches.append({
                    "type": "threshold",
                    "selector": selector_model,
                    "experiment": experiment,
                    "target_project": target_project,
                    "seed": seed,
                    "expected": val_threshold,
                    "actual": threshold,
                })
        
        # Verify selection mode matches expected
        expected_mode = EXPECTED_SELECTION_MODE[selector_model]
        if selection_mode != expected_mode:
            results["selection_mode_mismatches"] += 1
            mismatches.append({
                "type": "selection_mode",
                "selector": selector_model,
                "experiment": experiment,
                "target_project": target_project,
                "seed": seed,
                "expected": expected_mode,
                "actual": selection_mode,
            })
    
    # Check that all mismatches are zero
    if results["selected_candidate_mismatches"] > 0:
        raise ValueError(f"Found {results['selected_candidate_mismatches']} selected candidate mismatches")
    if results["selection_score_mismatches"] > 0:
        raise ValueError(f"Found {results['selection_score_mismatches']} selection score mismatches")
    if results["threshold_mismatches"] > 0:
        raise ValueError(f"Found {results['threshold_mismatches']} threshold mismatches")
    if results["selection_mode_mismatches"] > 0:
        raise ValueError(f"Found {results['selection_mode_mismatches']} selection mode mismatches")
    
    print("Selection provenance validated.")
    return results


def save_selection_events(top1_df):
    """Save selection events to CSV."""
    print("Saving selection events...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Select and order columns
    cols = ["selector_model", "experiment", "target_project", "seed", "mode", 
            "selected_candidate", "threshold", "selection_score"]
    events_df = top1_df[cols].copy()
    
    # Sort
    events_df = events_df.sort_values(["selector_model", "experiment", "target_project", "seed"])
    
    # Verify row count
    if len(events_df) != 150:
        raise ValueError(f"Expected 150 event rows, got {len(events_df)}")
    
    # Check for nulls
    if events_df.isnull().sum().sum() > 0:
        raise ValueError("Found null values in selection events")
    
    # Check for duplicate keys
    key_cols = ["experiment", "target_project", "seed", "selector_model"]
    duplicates = events_df.duplicated(subset=key_cols)
    if duplicates.sum() > 0:
        raise ValueError(f"Found {duplicates.sum()} duplicate keys in selection events")
    
    events_df.to_csv(OUTPUT_EVENTS, index=False)
    
    print("Selection events saved.")
    return events_df


def compute_overall_frequency(top1_df):
    """Compute overall selection frequency by selector and candidate."""
    print("Computing overall frequency...")
    
    # Count selections by selector and candidate
    freq = top1_df.groupby(["selector_model", "mode", "selected_candidate"]).size().reset_index(name="count")
    freq = freq.rename(columns={"selected_candidate": "candidate"})
    
    # Create all combinations
    all_combos = []
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        for candidate in BASELINE_MODELS:
            all_combos.append({"selector_model": selector, "mode": mode, "candidate": candidate})
    
    all_combos_df = pd.DataFrame(all_combos)
    
    # Merge with frequency to include zero counts
    freq = all_combos_df.merge(freq, on=["selector_model", "mode", "candidate"], how="left").fillna(0)
    freq["count"] = freq["count"].astype(int)
    
    # Add denominator and proportion
    freq["denominator"] = 50
    freq["proportion"] = freq["count"] / freq["denominator"]
    
    # Verify row count
    if len(freq) != 12:
        raise ValueError(f"Expected 12 overall frequency rows, got {len(freq)}")
    
    # Verify sums
    for selector in SELECTOR_MODELS:
        selector_sum = freq[freq["selector_model"] == selector]["count"].sum()
        if selector_sum != 50:
            raise ValueError(f"Expected sum 50 for {selector}, got {selector_sum}")
        selector_prop_sum = freq[freq["selector_model"] == selector]["proportion"].sum()
        if abs(selector_prop_sum - 1.0) > TOLERANCE:
            raise ValueError(f"Expected proportion sum 1.0 for {selector}, got {selector_prop_sum}")
    
    # Sort
    freq = freq.sort_values(["selector_model", "mode", "candidate"])
    
    freq.to_csv(OUTPUT_OVERALL, index=False)
    
    print("Overall frequency computed.")
    return freq


def compute_by_setting_frequency(top1_df):
    """Compute selection frequency by selector, experiment, and candidate."""
    print("Computing by-setting frequency...")
    
    # Count selections by selector, experiment, and candidate
    freq = top1_df.groupby(["selector_model", "mode", "experiment", "selected_candidate"]).size().reset_index(name="count")
    freq = freq.rename(columns={"selected_candidate": "candidate"})
    
    # Create all combinations
    all_combos = []
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        for experiment in ["within_project", "cross_project"]:
            for candidate in BASELINE_MODELS:
                all_combos.append({"selector_model": selector, "mode": mode, "experiment": experiment, "candidate": candidate})
    
    all_combos_df = pd.DataFrame(all_combos)
    
    # Merge with frequency to include zero counts
    freq = all_combos_df.merge(freq, on=["selector_model", "mode", "experiment", "candidate"], how="left").fillna(0)
    freq["count"] = freq["count"].astype(int)
    
    # Add denominator and proportion
    freq["denominator"] = 25
    freq["proportion"] = freq["count"] / freq["denominator"]
    
    # Verify row count
    if len(freq) != 24:
        raise ValueError(f"Expected 24 by-setting frequency rows, got {len(freq)}")
    
    # Verify sums
    for selector in SELECTOR_MODELS:
        for experiment in ["within_project", "cross_project"]:
            subset = freq[(freq["selector_model"] == selector) & (freq["experiment"] == experiment)]
            subset_sum = subset["count"].sum()
            if subset_sum != 25:
                raise ValueError(f"Expected sum 25 for {selector}/{experiment}, got {subset_sum}")
            subset_prop_sum = subset["proportion"].sum()
            if abs(subset_prop_sum - 1.0) > TOLERANCE:
                raise ValueError(f"Expected proportion sum 1.0 for {selector}/{experiment}, got {subset_prop_sum}")
    
    # Sort
    freq = freq.sort_values(["selector_model", "mode", "experiment", "candidate"])
    
    freq.to_csv(OUTPUT_BY_SETTING, index=False)
    
    print("By-setting frequency computed.")
    return freq


def compute_by_project_frequency(top1_df):
    """Compute selection frequency by selector, experiment, project, and candidate."""
    print("Computing by-project frequency...")
    
    # Count selections by selector, experiment, project, and candidate
    freq = top1_df.groupby(["selector_model", "mode", "experiment", "target_project", "selected_candidate"]).size().reset_index(name="count")
    freq = freq.rename(columns={"selected_candidate": "candidate"})
    
    # Create all combinations
    all_combos = []
    for selector in SELECTOR_MODELS:
        mode = SELECTOR_TO_MODE[selector]
        for experiment in ["within_project", "cross_project"]:
            for project in ["CM1", "JM1", "KC1", "KC2", "PC1"]:
                for candidate in BASELINE_MODELS:
                    all_combos.append({
                        "selector_model": selector,
                        "mode": mode,
                        "experiment": experiment,
                        "target_project": project,
                        "candidate": candidate
                    })
    
    all_combos_df = pd.DataFrame(all_combos)
    
    # Merge with frequency to include zero counts
    freq = all_combos_df.merge(freq, on=["selector_model", "mode", "experiment", "target_project", "candidate"], how="left").fillna(0)
    freq["count"] = freq["count"].astype(int)
    
    # Add denominator and proportion
    freq["denominator"] = 5
    freq["proportion"] = freq["count"] / freq["denominator"]
    
    # Verify row count
    if len(freq) != 120:
        raise ValueError(f"Expected 120 by-project frequency rows, got {len(freq)}")
    
    # Verify sums
    for selector in SELECTOR_MODELS:
        for experiment in ["within_project", "cross_project"]:
            for project in ["CM1", "JM1", "KC1", "KC2", "PC1"]:
                subset = freq[(freq["selector_model"] == selector) & (freq["experiment"] == experiment) & (freq["target_project"] == project)]
                subset_sum = subset["count"].sum()
                if subset_sum != 5:
                    raise ValueError(f"Expected sum 5 for {selector}/{experiment}/{project}, got {subset_sum}")
                subset_prop_sum = subset["proportion"].sum()
                if abs(subset_prop_sum - 1.0) > TOLERANCE:
                    raise ValueError(f"Expected proportion sum 1.0 for {selector}/{experiment}/{project}, got {subset_prop_sum}")
    
    # Sort
    freq = freq.sort_values(["selector_model", "mode", "experiment", "target_project", "candidate"])
    
    freq.to_csv(OUTPUT_BY_PROJECT, index=False)
    
    print("By-project frequency computed.")
    return freq


def compute_descriptive_maxima(overall_freq, by_setting_freq):
    """Compute descriptive maxima and ties."""
    print("Computing descriptive maxima...")
    
    maxima = {
        "overall": {},
        "by_setting": {},
    }
    
    # Overall maxima by selector
    for selector in SELECTOR_MODELS:
        selector_df = overall_freq[overall_freq["selector_model"] == selector]
        max_count = selector_df["count"].max()
        max_candidates = selector_df[selector_df["count"] == max_count]["candidate"].tolist()
        max_prop = selector_df[selector_df["count"] == max_count]["proportion"].iloc[0]
        
        maxima["overall"][selector] = {
            "most_frequent_candidates": max_candidates,
            "maximum_count": int(max_count),
            "maximum_proportion": float(max_prop),
        }
    
    # By-setting maxima
    for selector in SELECTOR_MODELS:
        for experiment in ["within_project", "cross_project"]:
            selector_df = by_setting_freq[(by_setting_freq["selector_model"] == selector) & (by_setting_freq["experiment"] == experiment)]
            max_count = selector_df["count"].max()
            max_candidates = selector_df[selector_df["count"] == max_count]["candidate"].tolist()
            max_prop = selector_df[selector_df["count"] == max_count]["proportion"].iloc[0]
            
            key = f"{selector}_{experiment}"
            maxima["by_setting"][key] = {
                "most_frequent_candidates": max_candidates,
                "maximum_count": int(max_count),
                "maximum_proportion": float(max_prop),
            }
    
    print("Descriptive maxima computed.")
    return maxima


def save_reports(provenance_results, overall_freq, by_setting_freq, by_project_freq, maxima):
    """Save JSON and Markdown reports."""
    print("Saving reports...")
    
    # Build JSON report
    report = {
        "provenance_validation": provenance_results,
        "overall_frequency": overall_freq.to_dict(orient="records"),
        "by_setting_frequency": by_setting_freq.to_dict(orient="records"),
        "by_project_frequency": by_project_freq.to_dict(orient="records"),
        "descriptive_maxima": maxima,
    }
    
    with open(OUTPUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    
    # Build Markdown report
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 2 Section 2A: Top-1 Selection Frequency Analysis\n\n")
        
        f.write("## Canonical Verification\n\n")
        f.write("- All canonical files verified with SHA-256\n")
        f.write("- Manifest validation status: all_checks_passed\n")
        f.write("- Analysis readiness: ready_from_existing_outputs\n\n")
        
        f.write("## Selection-Provenance Validation\n\n")
        f.write(f"- **Runs checked:** {provenance_results['runs_checked']}\n")
        f.write(f"- **Selected candidate mismatches:** {provenance_results['selected_candidate_mismatches']}\n")
        f.write(f"- **Selection score mismatches:** {provenance_results['selection_score_mismatches']}\n")
        f.write(f"- **Threshold mismatches:** {provenance_results['threshold_mismatches']}\n")
        f.write(f"- **Selection mode mismatches:** {provenance_results['selection_mode_mismatches']}\n")
        f.write(f"- **Validation tie runs:** {provenance_results['validation_tie_runs']}\n\n")
        
        f.write("## Overall Selection Frequency\n\n")
        f.write("| Selector | Mode | Candidate | Count | Denominator | Proportion |\n")
        f.write("|----------|------|-----------|-------|------------|------------|\n")
        for _, row in overall_freq.iterrows():
            f.write(f"| {row['selector_model']} | {row['mode']} | {row['candidate']} | {row['count']} | {row['denominator']} | {row['proportion']:.4f} |\n")
        f.write("\n")
        
        f.write("## Selection Frequency by Setting\n\n")
        f.write("| Selector | Mode | Experiment | Candidate | Count | Denominator | Proportion |\n")
        f.write("|----------|------|------------|-----------|-------|------------|------------|\n")
        for _, row in by_setting_freq.iterrows():
            f.write(f"| {row['selector_model']} | {row['mode']} | {row['experiment']} | {row['candidate']} | {row['count']} | {row['denominator']} | {row['proportion']:.4f} |\n")
        f.write("\n")
        
        f.write("## Selection Frequency by Project\n\n")
        f.write("| Selector | Mode | Experiment | Project | Candidate | Count | Denominator | Proportion |\n")
        f.write("|----------|------|------------|---------|-----------|-------|------------|------------|\n")
        for _, row in by_project_freq.iterrows():
            f.write(f"| {row['selector_model']} | {row['mode']} | {row['experiment']} | {row['target_project']} | {row['candidate']} | {row['count']} | {row['denominator']} | {row['proportion']:.4f} |\n")
        f.write("\n")
        
        f.write("## Descriptive Maxima and Ties\n\n")
        f.write("### Overall Maxima by Selector\n\n")
        for selector in SELECTOR_MODELS:
            data = maxima["overall"][selector]
            f.write(f"**{selector}:**\n")
            f.write(f"- Most frequent candidate(s): {', '.join(data['most_frequent_candidates'])}\n")
            f.write(f"- Maximum count: {data['maximum_count']}\n")
            f.write(f"- Maximum proportion: {data['maximum_proportion']:.4f}\n\n")
        
        f.write("### Maxima by Selector and Setting\n\n")
        for selector in SELECTOR_MODELS:
            for experiment in ["within_project", "cross_project"]:
                key = f"{selector}_{experiment}"
                data = maxima["by_setting"][key]
                f.write(f"**{selector} / {experiment}:**\n")
                f.write(f"- Most frequent candidate(s): {', '.join(data['most_frequent_candidates'])}\n")
                f.write(f"- Maximum count: {data['maximum_count']}\n")
                f.write(f"- Maximum proportion: {data['maximum_proportion']:.4f}\n\n")
        
        f.write("## Interpretation Limits\n\n")
        f.write("These are descriptive selection frequencies from 50 repeated runs per selector.\n")
        f.write("They do not establish statistical significance or superiority.\n")
        f.write("No causal inferences should be drawn from these descriptive statistics.\n\n")
    
    print("Reports saved.")


def main():
    """Main entry point."""
    print("Starting top-1 selection frequency analysis...\n")
    
    # Load and verify inputs
    repeated_df, validation_df = load_and_verify_inputs()
    
    # Extract top-1 selections
    top1_df = extract_top1_selections(repeated_df)
    
    # Validate selection provenance
    provenance_results = validate_selection_provenance(top1_df, validation_df)
    
    # Save selection events
    events_df = save_selection_events(top1_df)
    
    # Compute frequencies
    overall_freq = compute_overall_frequency(top1_df)
    by_setting_freq = compute_by_setting_frequency(top1_df)
    by_project_freq = compute_by_project_frequency(top1_df)
    
    # Compute descriptive maxima
    maxima = compute_descriptive_maxima(overall_freq, by_setting_freq)
    
    # Save reports
    save_reports(provenance_results, overall_freq, by_setting_freq, by_project_freq, maxima)
    
    print("\nTop-1 selection frequency analysis complete!")
    print(f"\nSummary:")
    print(f"  Runs checked: {provenance_results['runs_checked']}")
    print(f"  Selection provenance mismatches: 0")
    print(f"  Validation tie runs: {provenance_results['validation_tie_runs']}")
    print(f"  Event rows: {len(events_df)}")
    print(f"  Overall frequency rows: {len(overall_freq)}")
    print(f"  By-setting rows: {len(by_setting_freq)}")
    print(f"  By-project rows: {len(by_project_freq)}")
    print(f"  Most frequent candidate(s) by selector:")
    for selector in SELECTOR_MODELS:
        data = maxima["overall"][selector]
        print(f"    {selector}: {', '.join(data['most_frequent_candidates'])}")


if __name__ == "__main__":
    main()
