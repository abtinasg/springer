#!/usr/bin/env python3
"""Generate manuscript-style summary tables from an aligned AQRPE reproduction run."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

MODEL_DISPLAY = {
    "LR_std_C0.1": "LR-C0.1",
    "LR_std_C1": "LR-C1",
    "DT_leaf5": "DT-L5",
    "ET_leaf5": "ET-L5",
    "AQRPE_v2_balanced": "AQRPE-bal",
    "AQRPE_v2_rank": "AQRPE-rank",
    "AQRPE_v2_mcc": "AQRPE-MCC",
    "AQRPE_v2_soft_top3": "Soft-top-3",
}
METRICS = ["mcc", "avg_precision", "f1", "balanced_accuracy", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "brier"]


def fmt(mean, std):
    if pd.isna(std):
        return f"{mean:.3f}"
    val = 0.0 if abs(mean) < 0.0005 else mean
    return f"{val:.3f} ({std:.3f})"


def table_for_setting(summary, setting):
    sdf = summary[summary["experiment"] == setting].copy()
    rows = []
    for _, r in sdf.iterrows():
        rows.append({
            "Model": MODEL_DISPLAY.get(r["model"], r["model"]),
            "MCC": fmt(r["mcc_mean"], r["mcc_std"]),
            "AP": fmt(r["avg_precision_mean"], r["avg_precision_std"]),
            "F1": fmt(r["f1_mean"], r["f1_std"]),
            "BA": fmt(r["balanced_accuracy_mean"], r["balanced_accuracy_std"]),
            "P@10%": fmt(r["precision_at_10pct_mean"], r["precision_at_10pct_std"]),
            "R@10%": fmt(r["recall_at_10pct_mean"], r["recall_at_10pct_std"]),
        })
    return pd.DataFrame(rows)


def delta_table(summary):
    rows = []
    for setting in sorted(summary["experiment"].unique()):
        sdf = summary[summary["experiment"] == setting].set_index("model")
        baselines = [m for m in sdf.index if not m.startswith("AQRPE")]
        if "AQRPE_v2_soft_top3" not in sdf.index:
            continue
        for metric in METRICS:
            mean_col = f"{metric}_mean"
            higher_is_better = metric != "brier"
            best_baseline_name = sdf.loc[baselines, mean_col].idxmax() if higher_is_better else sdf.loc[baselines, mean_col].idxmin()
            best_baseline = float(sdf.loc[best_baseline_name, mean_col])
            proposed = float(sdf.loc["AQRPE_v2_soft_top3", mean_col])
            delta = proposed - best_baseline
            if abs(delta) < 0.0005:
                outcome = "tied"
                delta = 0.0
            else:
                outcome = "better" if ((delta > 0 and higher_is_better) or (delta < 0 and not higher_is_better)) else "worse"
            rows.append({
                "Setting": setting,
                "Metric": metric,
                "Direction": "higher is better" if higher_is_better else "lower is better",
                "Soft-top-3 mean": round(proposed, 6),
                "Best baseline": MODEL_DISPLAY.get(best_baseline_name, best_baseline_name),
                "Best baseline mean": round(best_baseline, 6),
                "Delta": round(delta, 6),
                "AQRPE outcome": outcome,
            })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results_dir", default="results")
    ap.add_argument("--out_dir", default="results")
    args = ap.parse_args()
    r = Path(args.results_dir)
    o = Path(args.out_dir)
    o.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(r / "repeated_summary_mean_std.csv")
    table_for_setting(summary, "within_project").to_csv(o / "table_within_project_mean_sd.csv", index=False)
    table_for_setting(summary, "cross_project").to_csv(o / "table_cross_project_mean_sd.csv", index=False)
    delta_table(summary).to_csv(o / "table_soft_top3_delta_vs_best_baseline.csv", index=False)
    print({"status": "ok", "out_dir": str(o)})


if __name__ == "__main__":
    main()
