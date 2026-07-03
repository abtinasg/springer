#!/usr/bin/env python3
"""
Part 1 Section 6C: Analyze result ranking stability
Compares reference results with locked reproduction results to detect drift in rankings.
"""

import pandas as pd
import json
from scipy.stats import spearmanr
from pathlib import Path

# Configuration
REFERENCE_PATH = "results/repeated_summary_mean_std.csv"
LOCKED_PATH = "results/part1_full_reproduction/repeated_summary_mean_std.csv"
OUTPUT_JSON = "reports/part1_result_drift_analysis.json"
OUTPUT_MD = "reports/part1_result_drift_analysis.md"

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
    return result


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


def find_best_model(data, setting, metric, models):
    """Find the best model for a given setting and metric."""
    best_model = None
    best_value = None
    
    for model in models:
        key = (setting, model)
        if key not in data:
            continue
        value = get_metric_value(data[key], metric)
        
        if best_value is None:
            best_model = model
            best_value = value
        elif is_better(value, best_value, metric):
            best_model = model
            best_value = value
        elif is_tied(value, best_value):
            # In case of tie, keep the first one (or could use alphabetical)
            pass
    
    return best_model, best_value


def compute_ranks(data, setting, metric, models):
    """Compute ranks for all models for a given setting and metric."""
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
    
    # Assign ranks (handle ties)
    ranks = {}
    for i, model in enumerate(sorted_models):
        ranks[model] = i + 1
    
    return ranks


def compare_to_baseline(value, baseline_value, metric):
    """Compare a value to baseline value."""
    if is_tied(value, baseline_value):
        return "tied"
    if is_better(value, baseline_value, metric):
        return "better"
    return "worse"


def analyze():
    """Main analysis function."""
    # Load data
    ref_data = load_data(REFERENCE_PATH)
    locked_data = load_data(LOCKED_PATH)
    
    results = []
    summary = {
        "total_combinations": len(SETTINGS) * len(METRICS),
        "best_overall_identity_changes": [],
        "best_baseline_identity_changes": [],
        "soft_top3_outcome_changes": [],
        "combinations_with_any_rank_change": 0,
        "min_spearman_correlation": 1.0,
        "max_absolute_mean_value_change": 0.0
    }
    
    for setting in SETTINGS:
        for metric in METRICS:
            # Find best overall model
            ref_best_overall, ref_best_overall_val = find_best_model(
                ref_data, setting, metric, ALL_MODELS
            )
            locked_best_overall, locked_best_overall_val = find_best_model(
                locked_data, setting, metric, ALL_MODELS
            )
            
            best_overall_changed = ref_best_overall != locked_best_overall
            if best_overall_changed:
                summary["best_overall_identity_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_best": ref_best_overall,
                    "locked_best": locked_best_overall
                })
            
            # Find best baseline
            ref_best_baseline, ref_best_baseline_val = find_best_model(
                ref_data, setting, metric, BASELINE_MODELS
            )
            locked_best_baseline, locked_best_baseline_val = find_best_model(
                locked_data, setting, metric, BASELINE_MODELS
            )
            
            best_baseline_changed = ref_best_baseline != locked_best_baseline
            if best_baseline_changed:
                summary["best_baseline_identity_changes"].append({
                    "setting": setting,
                    "metric": metric,
                    "reference_best": ref_best_baseline,
                    "locked_best": locked_best_baseline
                })
            
            # Get Soft-top-3 values
            ref_soft_val = get_metric_value(ref_data[(setting, PROPOSED_MODEL)], metric)
            locked_soft_val = get_metric_value(locked_data[(setting, PROPOSED_MODEL)], metric)
            
            # Compare Soft-top-3 to best baseline
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
            
            # Count rank changes
            rank_changes = 0
            max_rank_change = 0
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
                    if change > 0:
                        rank_changes += 1
                    if change > max_rank_change:
                        max_rank_change = change
            
            if rank_changes > 0:
                summary["combinations_with_any_rank_change"] += 1
            
            # Spearman correlation
            ref_rank_list = [ref_ranks.get(m, None) for m in ALL_MODELS]
            locked_rank_list = [locked_ranks.get(m, None) for m in ALL_MODELS]
            # Filter out None values
            valid_pairs = [(r, l) for r, l in zip(ref_rank_list, locked_rank_list) 
                          if r is not None and l is not None]
            if valid_pairs:
                ref_r_valid = [p[0] for p in valid_pairs]
                locked_r_valid = [p[1] for p in valid_pairs]
                corr, _ = spearmanr(ref_r_valid, locked_r_valid)
                if corr < summary["min_spearman_correlation"]:
                    summary["min_spearman_correlation"] = corr
            else:
                corr = None
            
            # Max absolute mean value change
            abs_changes = []
            for model in ALL_MODELS:
                ref_val = get_metric_value(ref_data[(setting, model)], metric)
                locked_val = get_metric_value(locked_data[(setting, model)], metric)
                abs_changes.append(abs(ref_val - locked_val))
            max_abs_change = max(abs_changes) if abs_changes else 0.0
            if max_abs_change > summary["max_absolute_mean_value_change"]:
                summary["max_absolute_mean_value_change"] = max_abs_change
            
            # Store detailed result
            result_entry = {
                "setting": setting,
                "metric": metric,
                "best_overall": {
                    "reference": {
                        "model": ref_best_overall,
                        "value": ref_best_overall_val
                    },
                    "locked": {
                        "model": locked_best_overall,
                        "value": locked_best_overall_val
                    },
                    "identity_changed": best_overall_changed
                },
                "best_baseline": {
                    "reference": {
                        "model": ref_best_baseline,
                        "value": ref_best_baseline_val
                    },
                    "locked": {
                        "model": locked_best_baseline,
                        "value": locked_best_baseline_val
                    },
                    "identity_changed": best_baseline_changed
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
                "spearman_correlation": corr,
                "max_absolute_mean_value_change": max_abs_change
            }
            results.append(result_entry)
    
    return results, summary


def save_results(results, summary):
    """Save results to JSON and Markdown files."""
    # Ensure output directory exists
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_MD).parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump({
            "summary": summary,
            "detailed_results": results
        }, f, indent=2)
    
    # Save Markdown
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 1 Section 6C: Result Drift Analysis\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total setting-metric combinations**: {summary['total_combinations']}\n")
        f.write(f"- **Best-overall identity changes**: {len(summary['best_overall_identity_changes'])}\n")
        f.write(f"- **Best-baseline identity changes**: {len(summary['best_baseline_identity_changes'])}\n")
        f.write(f"- **Soft-top-3 outcome changes**: {len(summary['soft_top3_outcome_changes'])}\n")
        f.write(f"- **Combinations with any rank change**: {summary['combinations_with_any_rank_change']}\n")
        f.write(f"- **Minimum Spearman correlation**: {summary['min_spearman_correlation']:.4f}\n")
        f.write(f"- **Maximum absolute mean-value change**: {summary['max_absolute_mean_value_change']:.6f}\n\n")
        
        if summary['best_overall_identity_changes']:
            f.write("## Best-Overall Identity Changes\n\n")
            for change in summary['best_overall_identity_changes']:
                f.write(f"- **{change['setting']} / {change['metric']}**: {change['reference_best']} → {change['locked_best']}\n")
            f.write("\n")
        
        if summary['best_baseline_identity_changes']:
            f.write("## Best-Baseline Identity Changes\n\n")
            for change in summary['best_baseline_identity_changes']:
                f.write(f"- **{change['setting']} / {change['metric']}**: {change['reference_best']} → {change['locked_best']}\n")
            f.write("\n")
        
        if summary['soft_top3_outcome_changes']:
            f.write("## Soft-Top-3 Outcome Changes\n\n")
            for change in summary['soft_top3_outcome_changes']:
                f.write(f"- **{change['setting']} / {change['metric']}**: {change['reference_outcome']} → {change['locked_outcome']}\n")
            f.write("\n")
        
        f.write("## Detailed Results by Setting-Metric Combination\n\n")
        for entry in results:
            f.write(f"### {entry['setting']} / {entry['metric']}\n\n")
            f.write(f"**Best Overall Model:**\n")
            f.write(f"- Reference: {entry['best_overall']['reference']['model']} ({entry['best_overall']['reference']['value']:.6f})\n")
            f.write(f"- Locked: {entry['best_overall']['locked']['model']} ({entry['best_overall']['locked']['value']:.6f})\n")
            f.write(f"- Identity changed: {entry['best_overall']['identity_changed']}\n\n")
            
            f.write(f"**Best Baseline Model:**\n")
            f.write(f"- Reference: {entry['best_baseline']['reference']['model']} ({entry['best_baseline']['reference']['value']:.6f})\n")
            f.write(f"- Locked: {entry['best_baseline']['locked']['model']} ({entry['best_baseline']['locked']['value']:.6f})\n")
            f.write(f"- Identity changed: {entry['best_baseline']['identity_changed']}\n\n")
            
            f.write(f"**Soft-Top-3 Performance:**\n")
            f.write(f"- Reference value: {entry['soft_top3']['reference_value']:.6f}\n")
            f.write(f"- Locked value: {entry['soft_top3']['locked_value']:.6f}\n")
            f.write(f"- Reference vs best baseline: {entry['soft_top3']['reference_vs_baseline']}\n")
            f.write(f"- Locked vs best baseline: {entry['soft_top3']['locked_vs_baseline']}\n")
            f.write(f"- Outcome changed: {entry['soft_top3']['outcome_changed']}\n\n")
            
            f.write(f"**Rank Stability:**\n")
            f.write(f"- Models with changed rank: {entry['ranks']['models_with_changed_rank']}/8\n")
            f.write(f"- Maximum rank change: {entry['ranks']['max_rank_change']}\n")
            f.write(f"- Spearman correlation: {entry['spearman_correlation']:.4f}\n")
            f.write(f"- Max absolute mean-value change: {entry['max_absolute_mean_value_change']:.6f}\n\n")
            
            f.write(f"**Rank Details:**\n")
            for model in ALL_MODELS:
                detail = entry['ranks']['rank_changes_detail'].get(model, {})
                if detail:
                    f.write(f"- {model}: Ref={detail['reference_rank']}, Locked={detail['locked_rank']}, Change={detail['change']}\n")
            f.write("\n")


def main():
    """Main entry point."""
    print("Loading data...")
    results, summary = analyze()
    
    print("Saving results...")
    save_results(results, summary)
    
    print("Analysis complete!")
    print(f"\nSummary:")
    print(f"  Total combinations: {summary['total_combinations']}")
    print(f"  Best-overall identity changes: {len(summary['best_overall_identity_changes'])}")
    print(f"  Best-baseline identity changes: {len(summary['best_baseline_identity_changes'])}")
    print(f"  Soft-top-3 outcome changes: {len(summary['soft_top3_outcome_changes'])}")
    print(f"  Combinations with any rank change: {summary['combinations_with_any_rank_change']}")
    print(f"  Minimum Spearman correlation: {summary['min_spearman_correlation']:.4f}")
    print(f"  Maximum absolute mean-value change: {summary['max_absolute_mean_value_change']:.6f}")


if __name__ == "__main__":
    main()
