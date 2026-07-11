#!/usr/bin/env python3
"""
Part 1 Section 6D: Analyze result ranking stability (tie-aware)
Compares reference results with locked reproduction results to detect drift in rankings.
"""

import pandas as pd
import json
from scipy.stats import spearmanr
from pathlib import Path
import sys

# Base directory for portable paths
BASE_DIR = Path(__file__).resolve().parents[1]

# Configuration
REFERENCE_PATH = BASE_DIR / "results" / "repeated_summary_mean_std.csv"
LOCKED_PATH = BASE_DIR / "results" / "part1_full_reproduction" / "repeated_summary_mean_std.csv"
OUTPUT_JSON = BASE_DIR / "reports" / "part1_result_drift_analysis.json"
OUTPUT_MD = BASE_DIR / "reports" / "part1_result_drift_analysis.md"

SETTINGS = ["within_project", "cross_project"]
METRICS = ["mcc", "avg_precision", "f1", "balanced_accuracy", 
           "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "brier"]

BASELINE_MODELS = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
PROPOSED_MODEL = "AQRPE_v2_soft_top3"
ALL_MODELS = ["AQRPE_v2_balanced", "AQRPE_v2_mcc", "AQRPE_v2_rank", 
              "AQRPE_v2_soft_top3", "DT_leaf5", "ET_leaf5", 
              "LR_std_C0.1", "LR_std_C1"]

TIE_THRESHOLD = 0.0005

# Metrics where lower is better
LOWER_IS_BETTER = {"brier"}


def load_data(path):
    """Load CSV data and create experiment-model keyed dictionary."""
    df = pd.read_csv(path)
    result = {}
    for _, row in df.iterrows():
        key = (row["experiment"], row["model"])
        result[key] = row
    return df, result


def get_metric_value(row, metric):
    """Extract mean value for a metric from a row."""
    return row[f"{metric}_mean"]


def is_better(value1, value2, metric):
    """Determine if value1 is better than value2 for the given metric."""
    if metric in LOWER_IS_BETTER:
        return value1 < value2
    return value1 > value2


def is_tied(value1, value2):
    """Check if two values are tied within threshold."""
    return abs(value1 - value2) < TIE_THRESHOLD


def find_best_models(data, setting, metric, models):
    """Find all best models for a given setting and metric (tie-aware).
    
    Returns:
        best_models: list of models within tie threshold of optimum (sorted by input order)
        best_value: the optimum value
    """
    values = {}
    for model in models:
        key = (setting, model)
        if key not in data:
            continue
        values[model] = get_metric_value(data[key], metric)
    
    if not values:
        return [], None
    
    # Find optimum value
    if metric in LOWER_IS_BETTER:
        best_value = min(values.values())
    else:
        best_value = max(values.values())
    
    # Find all models within tie threshold
    best_models = [model for model, value in values.items() 
                  if abs(value - best_value) < TIE_THRESHOLD]
    
    # Sort by the original model list order to ensure consistency
    best_models = [m for m in models if m in best_models]
    
    return best_models, best_value


def compute_ranks(data, setting, metric, models):
    """Compute tie-aware ranks for all models for a given setting and metric.
    
    Models within 0.0005 of each other are tied and receive the average rank.
    """
    values = {}
    for model in models:
        key = (setting, model)
        if key not in data:
            continue
        values[model] = get_metric_value(data[key], metric)
    
    # Sort models by value (descending for most metrics, ascending for brier)
    if metric in LOWER_IS_BETTER:
        sorted_models = sorted(values.keys(), key=lambda m: values[m])
    else:
        sorted_models = sorted(values.keys(), key=lambda m: values[m], reverse=True)
    
    # Group tied models and assign average ranks
    ranks = {}
    i = 0
    while i < len(sorted_models):
        # Start a new tie group
        group_start = i
        group_value = values[sorted_models[i]]
        
        # Find all models in this tie group
        while i < len(sorted_models) and abs(values[sorted_models[i]] - group_value) < TIE_THRESHOLD:
            i += 1
        
        # Calculate average rank for the group
        group_size = i - group_start
        avg_rank = (group_start + 1 + group_start + group_size) / 2.0
        
        # Assign average rank to all members of the group
        for j in range(group_start, i):
            ranks[sorted_models[j]] = avg_rank
    
    return ranks


def compare_to_baseline(value, baseline_value, metric):
    """Compare a value to baseline value."""
    if is_tied(value, baseline_value):
        return "tied"
    if is_better(value, baseline_value, metric):
        return "better"
    return "worse"


def validate_data(df, data, path):
    """Validate data integrity before analysis."""
    # Check exactly 16 rows
    if len(df) != 16:
        raise ValueError(f"{path} has {len(df)} rows, expected 16")
    
    # Check no duplicate experiment-model keys
    keys = [(row["experiment"], row["model"]) for _, row in df.iterrows()]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{path} has duplicate experiment-model keys")
    
    # Check both settings exist
    experiments = df["experiment"].unique()
    for setting in SETTINGS:
        if setting not in experiments:
            raise ValueError(f"{path} missing setting: {setting}")
    
    # Check all 8 models exist in each setting
    for setting in SETTINGS:
        setting_models = df[df["experiment"] == setting]["model"].unique()
        for model in ALL_MODELS:
            if model not in setting_models:
                raise ValueError(f"{path} missing model {model} in setting {setting}")
    
    # Check no null mean values for required metrics
    for metric in METRICS:
        mean_col = f"{metric}_mean"
        if mean_col not in df.columns:
            raise ValueError(f"{path} missing column {mean_col}")
        if df[mean_col].isnull().any():
            raise ValueError(f"{path} has null values in {mean_col}")


def analyze():
    """Main analysis function."""
    # Load data
    print("Loading data...")
    ref_df, ref_data = load_data(REFERENCE_PATH)
    locked_df, locked_data = load_data(LOCKED_PATH)
    
    # Validate data
    print("Validating data...")
    validate_data(ref_df, ref_data, REFERENCE_PATH)
    validate_data(locked_df, locked_data, LOCKED_PATH)
    
    results = []
    summary = {
        "total_combinations": len(SETTINGS) * len(METRICS),
        "best_overall_winner_set_changes": [],
        "best_overall_disjoint_winner_changes": [],
        "best_baseline_winner_set_changes": [],
        "best_baseline_disjoint_winner_changes": [],
        "soft_top3_outcome_changes": [],
        "combinations_with_any_tie_aware_rank_change": 0,
        "min_tie_aware_spearman_correlation": 1.0,
        "max_absolute_mean_value_change": 0.0,
        "max_absolute_mean_value_change_location": None
    }
    
    for setting in SETTINGS:
        for metric in METRICS:
            # Find best overall models (tie-aware)
            ref_best_overall_models, ref_best_overall_val = find_best_models(
                ref_data, setting, metric, ALL_MODELS
            )
            locked_best_overall_models, locked_best_overall_val = find_best_models(
                locked_data, setting, metric, ALL_MODELS
            )
            
            # Check winner set changes
            ref_set = set(ref_best_overall_models)
            locked_set = set(locked_best_overall_models)
            winner_set_changed = ref_set != locked_set
            winner_sets_overlap = len(ref_set & locked_set) > 0
            disjoint_winner_change = len(ref_set & locked_set) == 0
            
            if winner_set_changed:
                summary["best_overall_winner_set_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_best_models": ref_best_overall_models,
                    "locked_best_models": locked_best_overall_models,
                    "winner_sets_overlap": winner_sets_overlap,
                    "disjoint_winner_change": disjoint_winner_change
                })
            if disjoint_winner_change:
                summary["best_overall_disjoint_winner_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_best_models": ref_best_overall_models,
                    "locked_best_models": locked_best_overall_models
                })
            
            # Find best baseline models (tie-aware)
            ref_best_baseline_models, ref_best_baseline_val = find_best_models(
                ref_data, setting, metric, BASELINE_MODELS
            )
            locked_best_baseline_models, locked_best_baseline_val = find_best_models(
                locked_data, setting, metric, BASELINE_MODELS
            )
            
            # Check baseline winner set changes
            ref_baseline_set = set(ref_best_baseline_models)
            locked_baseline_set = set(locked_best_baseline_models)
            baseline_winner_set_changed = ref_baseline_set != locked_baseline_set
            baseline_winner_sets_overlap = len(ref_baseline_set & locked_baseline_set) > 0
            baseline_disjoint_winner_change = len(ref_baseline_set & locked_baseline_set) == 0
            
            if baseline_winner_set_changed:
                summary["best_baseline_winner_set_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_best_models": ref_best_baseline_models,
                    "locked_best_models": locked_best_baseline_models,
                    "winner_sets_overlap": baseline_winner_sets_overlap,
                    "disjoint_winner_change": baseline_disjoint_winner_change
                })
            if baseline_disjoint_winner_change:
                summary["best_baseline_disjoint_winner_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_best_models": ref_best_baseline_models,
                    "locked_best_models": locked_best_baseline_models
                })
            
            # Get Soft-top-3 values
            ref_soft_val = get_metric_value(ref_data[(setting, PROPOSED_MODEL)], metric)
            locked_soft_val = get_metric_value(locked_data[(setting, PROPOSED_MODEL)], metric)
            
            # Compare Soft-top-3 to best baseline (use the best baseline value)
            ref_comparison = compare_to_baseline(ref_soft_val, ref_best_baseline_val, metric)
            locked_comparison = compare_to_baseline(locked_soft_val, locked_best_baseline_val, metric)
            
            soft_outcome_changed = ref_comparison != locked_comparison
            if soft_outcome_changed:
                summary["soft_top3_outcome_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_outcome": ref_comparison,
                    "locked_outcome": locked_comparison
                })
            
            # Compute ranks
            ref_ranks = compute_ranks(ref_data, setting, metric, ALL_MODELS)
            locked_ranks = compute_ranks(locked_data, setting, metric, ALL_MODELS)
            
            # Count rank changes (tie-aware)
            rank_changes = 0
            max_rank_change = 0.0
            rank_changes_detail = {}
            for model in ALL_MODELS:
                ref_rank = ref_ranks.get(model, None)
                locked_rank = locked_ranks.get(model, None)
                if ref_rank is not None and locked_rank is not None:
                    change = abs(ref_rank - locked_rank)
                    rank_changes_detail[model] = {
                        "reference_rank": ref_rank,
                        "locked_rank": locked_rank,
                        "change": change
                    }
                    if change > 1e-12:  # Only count as changed if significantly different
                        rank_changes += 1
                    if change > max_rank_change:
                        max_rank_change = change
            
            if rank_changes > 0:
                summary["combinations_with_any_tie_aware_rank_change"] += 1
            
            # Spearman correlation (tie-aware)
            ref_rank_list = [ref_ranks.get(m, None) for m in ALL_MODELS]
            locked_rank_list = [locked_ranks.get(m, None) for m in ALL_MODELS]
            # Filter out None values
            valid_pairs = [(r, l) for r, l in zip(ref_rank_list, locked_rank_list) 
                          if r is not None and l is not None]
            if valid_pairs:
                ref_r_valid = [p[0] for p in valid_pairs]
                locked_r_valid = [p[1] for p in valid_pairs]
                corr, _ = spearmanr(ref_r_valid, locked_r_valid)
                if corr < summary["min_tie_aware_spearman_correlation"]:
                    summary["min_tie_aware_spearman_correlation"] = corr
            else:
                corr = None
            
            # Max absolute mean value change with location
            abs_changes = []
            for model in ALL_MODELS:
                ref_val = get_metric_value(ref_data[(setting, model)], metric)
                locked_val = get_metric_value(locked_data[(setting, model)], metric)
                abs_change = abs(ref_val - locked_val)
                abs_changes.append((abs_change, setting, metric, model))
            max_abs_change, max_setting, max_metric, max_model = max(abs_changes, key=lambda x: x[0]) if abs_changes else (0.0, None, None, None)
            if max_abs_change > summary["max_absolute_mean_value_change"]:
                summary["max_absolute_mean_value_change"] = max_abs_change
                summary["max_absolute_mean_value_change_location"] = {
                    "setting": max_setting,
                    "metric": max_metric,
                    "model": max_model
                }
            
            # Store detailed result
            result_entry = {
                "setting": setting,
                "metric": metric,
                "best_overall": {
                    "reference": {
                        "models": ref_best_overall_models,
                        "value": ref_best_overall_val
                    },
                    "locked": {
                        "models": locked_best_overall_models,
                        "value": locked_best_overall_val
                    },
                    "winner_set_changed": winner_set_changed,
                    "winner_sets_overlap": winner_sets_overlap,
                    "disjoint_winner_change": disjoint_winner_change
                },
                "best_baseline": {
                    "reference": {
                        "models": ref_best_baseline_models,
                        "value": ref_best_baseline_val
                    },
                    "locked": {
                        "models": locked_best_baseline_models,
                        "value": locked_best_baseline_val
                    },
                    "winner_set_changed": baseline_winner_set_changed,
                    "winner_sets_overlap": baseline_winner_sets_overlap,
                    "disjoint_winner_change": baseline_disjoint_winner_change
                },
                "soft_top3": {
                    "reference_value": ref_soft_val,
                    "locked_value": locked_soft_val,
                    "reference_vs_baseline": ref_comparison,
                    "locked_vs_baseline": locked_comparison,
                    "outcome_changed": soft_outcome_changed
                },
                "ranks": {
                    "reference": ref_ranks,
                    "locked": locked_ranks,
                    "models_with_changed_rank": rank_changes,
                    "max_rank_change": max_rank_change,
                    "rank_changes_detail": rank_changes_detail
                },
                "tie_aware_spearman_correlation": corr,
                "max_absolute_mean_value_change": max_abs_change
            }
            results.append(result_entry)
    
    return results, summary


def save_results(results, summary):
    """Save results to JSON and Markdown files."""
    # Ensure output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump({
            "summary": summary,
            "detailed_results": results
        }, f, indent=2)
    
    # Save Markdown
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 1 Section 6D: Result Drift Analysis (Tie-Aware)\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total setting-metric combinations**: {summary['total_combinations']}\n")
        f.write(f"- **Best-overall winner-set changes**: {len(summary['best_overall_winner_set_changes'])}\n")
        f.write(f"- **Best-overall disjoint winner changes**: {len(summary['best_overall_disjoint_winner_changes'])}\n")
        f.write(f"- **Best-baseline winner-set changes**: {len(summary['best_baseline_winner_set_changes'])}\n")
        f.write(f"- **Best-baseline disjoint winner changes**: {len(summary['best_baseline_disjoint_winner_changes'])}\n")
        f.write(f"- **Soft-top-3 outcome changes**: {len(summary['soft_top3_outcome_changes'])}\n")
        f.write(f"- **Combinations with any tie-aware rank change**: {summary['combinations_with_any_tie_aware_rank_change']}\n")
        f.write(f"- **Minimum tie-aware Spearman correlation**: {summary['min_tie_aware_spearman_correlation']:.4f}\n")
        f.write(f"- **Maximum absolute mean-value change**: {summary['max_absolute_mean_value_change']:.6f}\n")
        loc = summary['max_absolute_mean_value_change_location']
        if loc:
            f.write(f"  - Location: {loc['setting']} / {loc['metric']} / {loc['model']}\n")
        f.write("\n")
        
        if summary['best_overall_winner_set_changes']:
            f.write("## Best-Overall Winner-Set Changes\n\n")
            for change in summary['best_overall_winner_set_changes']:
                f.write(f"- **{change['setting']} / {change['metric']}**:\n")
                f.write(f"  - Reference: {change['reference_best_models']}\n")
                f.write(f"  - Locked: {change['locked_best_models']}\n")
                f.write(f"  - Overlap: {change['winner_sets_overlap']}\n")
                f.write(f"  - Disjoint: {change['disjoint_winner_change']}\n")
            f.write("\n")
        
        if summary['best_baseline_winner_set_changes']:
            f.write("## Best-Baseline Winner-Set Changes\n\n")
            for change in summary['best_baseline_winner_set_changes']:
                f.write(f"- **{change['setting']} / {change['metric']}**:\n")
                f.write(f"  - Reference: {change['reference_best_models']}\n")
                f.write(f"  - Locked: {change['locked_best_models']}\n")
                f.write(f"  - Overlap: {change['winner_sets_overlap']}\n")
                f.write(f"  - Disjoint: {change['disjoint_winner_change']}\n")
            f.write("\n")
        
        if summary['soft_top3_outcome_changes']:
            f.write("## Soft-Top-3 Outcome Changes\n\n")
            for change in summary['soft_top3_outcome_changes']:
                f.write(f"- **{change['setting']} / {change['metric']}**: {change['reference_outcome']} → {change['locked_outcome']}\n")
            f.write("\n")
        
        f.write("## Detailed Results by Setting-Metric Combination\n\n")
        for entry in results:
            f.write(f"### {entry['setting']} / {entry['metric']}\n\n")
            f.write(f"**Best Overall Models:**\n")
            f.write(f"- Reference: {entry['best_overall']['reference']['models']} ({entry['best_overall']['reference']['value']:.6f})\n")
            f.write(f"- Locked: {entry['best_overall']['locked']['models']} ({entry['best_overall']['locked']['value']:.6f})\n")
            f.write(f"- Winner set changed: {entry['best_overall']['winner_set_changed']}\n")
            f.write(f"- Winner sets overlap: {entry['best_overall']['winner_sets_overlap']}\n")
            f.write(f"- Disjoint winner change: {entry['best_overall']['disjoint_winner_change']}\n\n")
            
            f.write(f"**Best Baseline Models:**\n")
            f.write(f"- Reference: {entry['best_baseline']['reference']['models']} ({entry['best_baseline']['reference']['value']:.6f})\n")
            f.write(f"- Locked: {entry['best_baseline']['locked']['models']} ({entry['best_baseline']['locked']['value']:.6f})\n")
            f.write(f"- Winner set changed: {entry['best_baseline']['winner_set_changed']}\n")
            f.write(f"- Winner sets overlap: {entry['best_baseline']['winner_sets_overlap']}\n")
            f.write(f"- Disjoint winner change: {entry['best_baseline']['disjoint_winner_change']}\n\n")
            
            f.write(f"**Soft-Top-3 Performance:**\n")
            f.write(f"- Reference value: {entry['soft_top3']['reference_value']:.6f}\n")
            f.write(f"- Locked value: {entry['soft_top3']['locked_value']:.6f}\n")
            f.write(f"- Reference vs best baseline: {entry['soft_top3']['reference_vs_baseline']}\n")
            f.write(f"- Locked vs best baseline: {entry['soft_top3']['locked_vs_baseline']}\n")
            f.write(f"- Outcome changed: {entry['soft_top3']['outcome_changed']}\n\n")
            
            f.write(f"**Rank Stability (Tie-Aware):**\n")
            f.write(f"- Models with changed rank: {entry['ranks']['models_with_changed_rank']}/8\n")
            f.write(f"- Maximum rank change: {entry['ranks']['max_rank_change']:.2f}\n")
            f.write(f"- Tie-aware Spearman correlation: {entry['tie_aware_spearman_correlation']:.4f}\n")
            f.write(f"- Max absolute mean-value change: {entry['max_absolute_mean_value_change']:.6f}\n\n")
            
            f.write(f"**Rank Details:**\n")
            for model in ALL_MODELS:
                detail = entry['ranks']['rank_changes_detail'].get(model, {})
                if detail:
                    f.write(f"- {model}: Ref={detail['reference_rank']:.2f}, Locked={detail['locked_rank']:.2f}, Change={detail['change']:.2f}\n")
            f.write("\n")


def main():
    """Main entry point."""
    results, summary = analyze()
    
    print("Saving results...")
    save_results(results, summary)
    
    print("Analysis complete!")
    print(f"\nSummary:")
    print(f"  Total combinations: {summary['total_combinations']}")
    print(f"  Best-overall winner-set changes: {len(summary['best_overall_winner_set_changes'])}")
    print(f"  Best-overall disjoint winner changes: {len(summary['best_overall_disjoint_winner_changes'])}")
    print(f"  Best-baseline winner-set changes: {len(summary['best_baseline_winner_set_changes'])}")
    print(f"  Best-baseline disjoint winner changes: {len(summary['best_baseline_disjoint_winner_changes'])}")
    print(f"  Soft-top-3 outcome changes: {len(summary['soft_top3_outcome_changes'])}")
    print(f"  Combinations with any tie-aware rank change: {summary['combinations_with_any_tie_aware_rank_change']}")
    print(f"  Minimum tie-aware Spearman correlation: {summary['min_tie_aware_spearman_correlation']:.4f}")
    print(f"  Maximum absolute mean-value change: {summary['max_absolute_mean_value_change']:.6f}")
    loc = summary['max_absolute_mean_value_change_location']
    if loc:
        print(f"    Location: {loc['setting']} / {loc['metric']} / {loc['model']}")


if __name__ == "__main__":
    main()
