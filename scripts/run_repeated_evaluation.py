#!/usr/bin/env python3
"""
Stage-38 aligned reproduction script for the AQRPE v2 software-quality study.

This script is deliberately aligned with the manuscript, Supplementary Table S1,
and the Stage-27 authoritative repeated-results workbook.  It uses the same
model names, candidate set, threshold grid, validation objectives, repeated
seeds, and output schema described in the paper.

Expected input files in --data_dir: cm1.csv, jm1.csv, kc1.csv, kc2.csv, pc1.csv
Default seeds: 7,13,29,42,101
"""
from __future__ import annotations

import argparse
import json
import math
import warnings
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    matthews_corrcoef,
    average_precision_score,
    roc_auc_score,
    f1_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    brier_score_loss,
)
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

PROJECTS = ["cm1", "jm1", "kc1", "kc2", "pc1"]
SEEDS = [7, 13, 29, 42, 101]
FIXED_GRID = np.linspace(0.03, 0.97, 41)
QUANTILE_GRID = np.linspace(0.03, 0.97, 25)
EPS = 1e-7


def candidate_factories() -> Dict[str, Callable[[int], Pipeline]]:
    """Candidate learners exactly as documented in Supplementary Table S1."""
    return {
        "LR_std_C0.1": lambda seed: Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=0.1,
                penalty="l2",
                solver="lbfgs",
                class_weight="balanced",
                max_iter=600,
                random_state=seed,
            )),
        ]),
        "LR_std_C1": lambda seed: Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=1.0,
                penalty="l2",
                solver="lbfgs",
                class_weight="balanced",
                max_iter=600,
                random_state=seed,
            )),
        ]),
        "DT_leaf5": lambda seed: Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", DecisionTreeClassifier(
                criterion="gini",
                splitter="best",
                min_samples_leaf=5,
                max_depth=None,
                random_state=seed,
            )),
        ]),
        "ET_leaf5": lambda seed: Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", ExtraTreesClassifier(
                n_estimators=50,
                criterion="gini",
                max_depth=None,
                min_samples_leaf=5,
                max_features="sqrt",
                bootstrap=False,
                class_weight="balanced",
                random_state=seed,
                n_jobs=2,
            )),
        ]),
    }


def detect_target(df: pd.DataFrame) -> str:
    lower = {str(c).lower(): c for c in df.columns}
    for key in ["defect", "defects", "bug", "bugs", "problems", "label", "class"]:
        if key in lower:
            return lower[key]
    return df.columns[-1]


def normalize_target(s: pd.Series) -> pd.Series:
    if s.dtype.kind in "biufc":
        return (s.astype(float) > 0).astype(int)
    vals = s.astype(str).str.strip().str.lower()
    yes = {"true", "yes", "y", "1", "defective", "buggy", "problem", "problems"}
    return vals.isin(yes).astype(int)


def load_projects(data_dir: Path, smoke: bool = False) -> Dict[str, Tuple[pd.DataFrame, pd.Series]]:
    out: Dict[str, Tuple[pd.DataFrame, pd.Series]] = {}
    for project in PROJECTS:
        df = pd.read_csv(data_dir / f"{project}.csv")
        df.columns = [str(c).strip().lower() for c in df.columns]
        target = detect_target(df)
        y = normalize_target(df[target]).reset_index(drop=True)
        X = df.drop(columns=[target]).copy()
        for c in list(X.columns):
            X[c] = pd.to_numeric(X[c], errors="coerce")
        X = X.dropna(axis=1, how="all")
        X = X.reset_index(drop=True)
        if smoke:
            rng = np.random.default_rng(7)
            idx_parts = []
            for cls, take_n in [(0, 50), (1, 30)]:
                cls_idx = np.where(y.to_numpy() == cls)[0]
                if len(cls_idx) == 0:
                    continue
                idx_parts.append(rng.choice(cls_idx, size=min(take_n, len(cls_idx)), replace=False))
            idx = np.concatenate(idx_parts)
            rng.shuffle(idx)
            X = X.iloc[idx].reset_index(drop=True)
            y = y.iloc[idx].reset_index(drop=True)
        out[project] = (X, y)

    # Use a common feature schema across projects for within- and cross-project consistency.
    common = None
    for X, _ in out.values():
        cols = set(X.columns)
        common = cols if common is None else common.intersection(cols)
    common_cols = sorted(common)
    return {p: (X.loc[:, common_cols].copy(), y.copy()) for p, (X, y) in out.items()}


def model_scores(model: Pipeline, X: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        score = model.predict_proba(X)[:, 1]
    elif hasattr(model, "decision_function"):
        raw = model.decision_function(X)
        score = 1.0 / (1.0 + np.exp(-raw))
    else:
        score = model.predict(X)
    return np.clip(np.asarray(score, dtype=float), EPS, 1 - EPS)


def threshold_grid(scores: np.ndarray) -> np.ndarray:
    s = np.clip(np.asarray(scores, dtype=float), EPS, 1 - EPS)
    q = np.quantile(s, QUANTILE_GRID)
    grid = np.unique(np.round(np.concatenate([FIXED_GRID, q]), 6))
    return grid[(grid > 0) & (grid < 1)]


def topk_metrics(y_true: Iterable[int], y_score: Iterable[float], k_ratio: float) -> Tuple[float, float, float]:
    y = np.asarray(y_true).astype(int)
    s = np.asarray(y_score, dtype=float)
    if len(y) == 0:
        return np.nan, np.nan, np.nan
    k = max(1, int(math.ceil(k_ratio * len(y))))
    idx = np.argsort(-s)[:k]
    selected = y[idx]
    precision = float(selected.mean())
    recall = float(selected.sum() / max(1, y.sum()))
    base_rate = float(y.mean())
    lift = float(precision / base_rate) if base_rate > 0 else np.nan
    return precision, recall, lift


def safe_roc_auc(y_true: Iterable[int], y_score: Iterable[float]) -> float:
    y = np.asarray(y_true).astype(int)
    if len(np.unique(y)) < 2:
        return np.nan
    return float(roc_auc_score(y, y_score))


def metric_row(y_true: Iterable[int], y_score: Iterable[float], threshold: float) -> dict:
    y = np.asarray(y_true).astype(int)
    s = np.clip(np.asarray(y_score, dtype=float), EPS, 1 - EPS)
    pred = (s >= threshold).astype(int)
    p10, r10, l10 = topk_metrics(y, s, 0.10)
    p20, r20, l20 = topk_metrics(y, s, 0.20)
    return {
        "threshold": float(threshold),
        "avg_precision": float(average_precision_score(y, s)) if len(np.unique(y)) > 1 else np.nan,
        "roc_auc": safe_roc_auc(y, s),
        "mcc": float(matthews_corrcoef(y, pred)) if len(np.unique(y)) > 1 else 0.0,
        "f1": float(f1_score(y, pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)) if len(np.unique(y)) > 1 else np.nan,
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "brier": float(brier_score_loss(y, s)),
        "precision_at_10pct": p10,
        "recall_at_10pct": r10,
        "lift_at_10pct": l10,
        "precision_at_20pct": p20,
        "recall_at_20pct": r20,
        "lift_at_20pct": l20,
    }


def objective_value(y_val: Iterable[int], s_val: Iterable[float], threshold: float, mode: str) -> float:
    m = metric_row(y_val, s_val, threshold)
    if mode == "balanced":
        return (
            0.36 * m["mcc"]
            + 0.27 * m["f1"]
            + 0.20 * m["balanced_accuracy"]
            + 0.10 * m["avg_precision"]
            + 0.05 * m["recall_at_10pct"]
            + 0.02 * m["recall_at_20pct"]
            - 0.02 * m["brier"]
        )
    if mode == "rank":
        return 0.60 * m["avg_precision"] + 0.25 * m["recall_at_10pct"] + 0.15 * m["recall_at_20pct"]
    if mode == "mcc":
        return m["mcc"]
    raise ValueError(f"Unknown objective mode: {mode}")


def select_threshold(y_val: Iterable[int], s_val: Iterable[float], mode: str) -> Tuple[float, float]:
    best_t, best_obj = 0.5, -1e18
    for t in threshold_grid(np.asarray(s_val)):
        obj = objective_value(y_val, s_val, float(t), mode)
        if obj > best_obj:
            best_obj, best_t = float(obj), float(t)
    return best_t, best_obj


def fit_candidates(X_train, y_train, X_val, y_val, seed: int):
    fitted = {}
    validation_rows = []
    for name, factory in candidate_factories().items():
        model = factory(seed)
        model.fit(X_train, y_train)
        s_val = model_scores(model, X_val)
        fitted[name] = {"model": model, "validation_scores": s_val}
        for mode in ["balanced", "rank", "mcc"]:
            if mode == "rank":
                # Ranking objective is score-only. Use 0.5 for diagnostic threshold metrics.
                t, obj = 0.5, objective_value(y_val, s_val, 0.5, "rank")
            else:
                t, obj = select_threshold(y_val, s_val, mode)
            row = metric_row(y_val, s_val, t)
            row.update({"candidate": name, "mode": mode, "selection_score": obj})
            validation_rows.append(row)
            fitted[name][f"threshold_{mode}"] = t
            fitted[name][f"objective_{mode}"] = obj
    return fitted, pd.DataFrame(validation_rows)


def evaluate_single(y_test, s_test, threshold: float, model_name: str, selected_candidate: str, mode: str, selection_score: float) -> dict:
    row = metric_row(y_test, s_test, threshold)
    row.update({
        "model": model_name,
        "selected_candidate": selected_candidate,
        "selection_mode": mode,
        "selection_score": float(selection_score),
    })
    return row


def evaluate_bundle(fitted: dict, X_val, y_val, X_test, y_test) -> List[dict]:
    rows: List[dict] = []

    # Candidate baselines are reported using their balanced-objective validation threshold.
    for cand in ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]:
        item = fitted[cand]
        s_test = model_scores(item["model"], X_test)
        rows.append(evaluate_single(
            y_test,
            s_test,
            item["threshold_balanced"],
            cand,
            cand,
            "single_candidate_balanced_threshold",
            item["objective_balanced"],
        ))

    # AQRPE variants.
    # Balanced: select candidate/threshold pair by balanced validation objective.
    bal_cand = max(fitted, key=lambda k: fitted[k]["objective_balanced"])
    rows.append(evaluate_single(
        y_test,
        model_scores(fitted[bal_cand]["model"], X_test),
        fitted[bal_cand]["threshold_balanced"],
        "AQRPE_v2_balanced",
        bal_cand,
        "balanced_objective",
        fitted[bal_cand]["objective_balanced"],
    ))

    # Rank: select candidate by ranking objective; use fixed 0.5 threshold for diagnostic binary metrics.
    rank_cand = max(fitted, key=lambda k: fitted[k]["objective_rank"])
    rows.append(evaluate_single(
        y_test,
        model_scores(fitted[rank_cand]["model"], X_test),
        0.5,
        "AQRPE_v2_rank",
        rank_cand,
        "rank_objective_fixed_threshold",
        fitted[rank_cand]["objective_rank"],
    ))

    # MCC: select candidate/threshold pair by validation MCC.
    mcc_cand = max(fitted, key=lambda k: fitted[k]["objective_mcc"])
    rows.append(evaluate_single(
        y_test,
        model_scores(fitted[mcc_cand]["model"], X_test),
        fitted[mcc_cand]["threshold_mcc"],
        "AQRPE_v2_mcc",
        mcc_cand,
        "mcc_objective",
        fitted[mcc_cand]["objective_mcc"],
    ))

    # Soft-top-3: select top three candidates by balanced validation objective, average validation scores,
    # tune threshold using the balanced objective on validation, and apply the frozen ensemble to test.
    top3 = sorted(fitted, key=lambda k: fitted[k]["objective_balanced"], reverse=True)[:3]
    val_stack = np.mean([fitted[k]["validation_scores"] for k in top3], axis=0)
    t_stack, obj_stack = select_threshold(y_val, val_stack, "balanced")
    test_stack = np.mean([model_scores(fitted[k]["model"], X_test) for k in top3], axis=0)
    row = metric_row(y_test, test_stack, t_stack)
    row.update({
        "model": "AQRPE_v2_soft_top3",
        "selected_candidate": "|".join(top3),
        "selection_mode": "soft_top3_balanced_objective",
        "selection_score": obj_stack,
    })
    rows.append(row)
    return rows


def run_within(projects: dict, seeds: List[int]):
    all_rows, val_rows = [], []
    for seed in seeds:
        for project, (X, y) in projects.items():
            X_temp, X_test, y_temp, y_test = train_test_split(
                X, y, test_size=0.20, stratify=y, random_state=seed
            )
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=0.25, stratify=y_temp, random_state=seed
            )
            fitted, vdf = fit_candidates(X_train, y_train, X_val, y_val, seed)
            for row in evaluate_bundle(fitted, X_val, y_val, X_test, y_test):
                row.update({"experiment": "within_project", "target_project": project.upper(), "seed": seed})
                all_rows.append(row)
            vdf.insert(0, "experiment", "within_project")
            vdf.insert(1, "target_project", project.upper())
            vdf.insert(2, "seed", seed)
            val_rows.append(vdf)
    return pd.DataFrame(all_rows), pd.concat(val_rows, ignore_index=True)


def run_cross(projects: dict, seeds: List[int]):
    all_rows, val_rows = [], []
    names = list(projects.keys())
    for seed in seeds:
        for target in names:
            sources = [p for p in names if p != target]
            X_src = pd.concat([projects[p][0] for p in sources], ignore_index=True)
            y_src = pd.concat([projects[p][1] for p in sources], ignore_index=True)
            X_test, y_test = projects[target]
            X_train, X_val, y_train, y_val = train_test_split(
                X_src, y_src, test_size=0.25, stratify=y_src, random_state=seed
            )
            fitted, vdf = fit_candidates(X_train, y_train, X_val, y_val, seed)
            for row in evaluate_bundle(fitted, X_val, y_val, X_test, y_test):
                row.update({"experiment": "cross_project", "target_project": target.upper(), "seed": seed})
                all_rows.append(row)
            vdf.insert(0, "experiment", "cross_project")
            vdf.insert(1, "target_project", target.upper())
            vdf.insert(2, "seed", seed)
            val_rows.append(vdf)
    return pd.DataFrame(all_rows), pd.concat(val_rows, ignore_index=True)


def summarize(allres: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "avg_precision", "roc_auc", "mcc", "f1", "balanced_accuracy", "precision", "recall", "brier",
        "precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
        "precision_at_20pct", "recall_at_20pct", "lift_at_20pct",
    ]
    summary = allres.groupby(["experiment", "model"])[metrics].agg(["mean", "std", "count"]).reset_index()
    summary.columns = ["_".join([str(x) for x in col if str(x)]) for col in summary.columns]
    # Add metric ranks by experiment; lower is better only for Brier.
    for metric in ["mcc", "avg_precision", "f1", "balanced_accuracy", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "brier"]:
        col = f"{metric}_mean"
        rank_col = f"rank_{metric}_mean"
        ascending = metric == "brier"
        summary[rank_col] = summary.groupby("experiment")[col].rank(method="min", ascending=ascending)
    return summary


def write_outputs(projects: dict, allres: pd.DataFrame, vallog: pd.DataFrame, out_dir: Path):
    profile = []
    for project, (X, y) in projects.items():
        profile.append({
            "project": project.upper(),
            "n_rows": len(y),
            "n_features": X.shape[1],
            "defective": int(y.sum()),
            "defect_rate": float(y.mean()),
        })
    profile_df = pd.DataFrame(profile)
    summary = summarize(allres)
    cols = [
        "experiment", "target_project", "seed", "model", "selected_candidate", "selection_mode",
        "threshold", "selection_score", "avg_precision", "roc_auc", "mcc", "f1", "balanced_accuracy",
        "precision", "recall", "brier", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
        "precision_at_20pct", "recall_at_20pct", "lift_at_20pct",
    ]
    allres = allres.loc[:, cols]
    val_cols = [
        "experiment", "target_project", "seed", "candidate", "mode", "threshold", "selection_score",
        "avg_precision", "roc_auc", "mcc", "f1", "balanced_accuracy", "precision", "recall", "brier",
        "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "precision_at_20pct", "recall_at_20pct", "lift_at_20pct",
    ]
    vallog = vallog.loc[:, val_cols].rename(columns={c: f"val_{c}" for c in val_cols if c not in ["experiment", "target_project", "seed", "candidate", "mode"]})

    out_dir.mkdir(parents=True, exist_ok=True)
    profile_df.to_csv(out_dir / "dataset_profile.csv", index=False)
    allres.to_csv(out_dir / "repeated_all_results.csv", index=False)
    vallog.to_csv(out_dir / "validation_log.csv", index=False)
    summary.to_csv(out_dir / "repeated_summary_mean_std.csv", index=False)
    with pd.ExcelWriter(out_dir / "repeated_results_workbook.xlsx") as writer:
        profile_df.to_excel(writer, "Dataset_Profile", index=False)
        allres.to_excel(writer, "All_Results", index=False)
        summary.to_excel(writer, "Summary_Mean_SD", index=False)
        vallog.to_excel(writer, "Validation_Log", index=False)

    decision = {
        "stage": "Stage-43 clean supplementary reproduction script",
        "seeds": SEEDS,
        "candidate_pool": ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"],
        "aqrpe_variants": ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc", "AQRPE_v2_soft_top3"],
        "threshold_grid": "unique(concat(linspace(0.03, 0.97, 41), quantile(validation_scores, linspace(0.03, 0.97, 25))))",
        "integrity_control": "Training fits models; validation selects candidates/thresholds/soft-top-3; test is final evaluation only.",
        "rows": int(len(allres)),
    }
    (out_dir / "decision_metadata.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", default="data/raw")
    ap.add_argument("--out_dir", default="results")
    ap.add_argument("--seeds", default=",".join(map(str, SEEDS)))
    ap.add_argument("--smoke", action="store_true", help="Run a small stratified sample and first two seeds for quick package verification.")
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    projects = load_projects(Path(args.data_dir), smoke=args.smoke)
    if args.smoke:
        seeds = seeds[:2]
        keep = ["cm1", "jm1"]
        projects = {k: projects[k] for k in keep if k in projects}

    wres, wval = run_within(projects, seeds)
    cres, cval = run_cross(projects, seeds)
    allres = pd.concat([wres, cres], ignore_index=True)
    vallog = pd.concat([wval, cval], ignore_index=True)
    write_outputs(projects, allres, vallog, Path(args.out_dir))
    print(json.dumps({"status": "ok", "out_dir": args.out_dir, "rows": len(allres), "smoke": bool(args.smoke)}, indent=2))


if __name__ == "__main__":
    main()
