#!/usr/bin/env python3
"""
Part 3A: Freeze the Scientific Analysis Contract

This script creates a complete, machine-readable, auditable scientific analysis
contract before any new model rerun, prediction-ledger generation, regret analysis,
ablation, sensitivity analysis, workflow figure generation, or manuscript editing.

The contract is deterministic and validates all requirements before output.
"""

import copy
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List


def get_repository_root() -> Path:
    """Derive repository root from script location."""
    return Path(__file__).resolve().parent.parent


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def build_contract() -> Dict[str, Any]:
    """Build the complete immutable contract payload."""
    
    contract = {
        "contract_title": "Scientific Analysis Contract for Major Revision",
        "contract_version": "Part-3A.3-v1",
        "starting_commit": "ec60c38abae80046fa0d345caa817258b97cdbf1",
        "repository": "abtinasg/springer",
        "branch": "major-revision-analysis-v2",
        
        "scientific_positioning": {
            "positioning_statement": (
                "A validation-controlled empirical study of model selection behavior, "
                "metric-dependent trade-offs, selection stability, validation-test agreement, "
                "post-hoc regret, and soft-ensemble ablation for imbalanced software defect "
                "prediction under repeated within-project and cross-project evaluation."
            ),
            "key_assertions": [
                "Validation-based selection is standard methodology.",
                "Soft averaging is standard ensemble methodology.",
                "Repeated seeds and train/validation/test separation are experimental controls.",
                "The scientific contribution is empirical characterization and controlled evidence, not the invention of a fundamentally new learning algorithm.",
                "No result may be framed as universal dominance.",
                "Conclusions must remain dataset-, metric-, setting-, and protocol-dependent."
            ]
        },
        
        "reviewer_context": {
            "reviewer_1_focus": [
                "Practical explanation of evaluation metrics.",
                "Key findings before detailed result tables.",
                "Reproducible workflow diagram."
            ],
            "reviewer_2_focus": [
                "Methodological decisions require clearer justification.",
                "Threats to validity require deeper analysis.",
                "Limitations and future directions must be evidence-based."
            ],
            "reviewer_3_focus": [
                "Validation-based model selection is standard.",
                "Averaging top models is standard.",
                "Repeated seeds and leakage control are good practice, not algorithmic novelty.",
                "The paper should be treated as a careful empirical study rather than a new fundamental algorithm."
            ]
        },
        
        "research_questions": {
            "count": 4,
            "rq1": {
                "title": "Comparative performance",
                "exact_intent": (
                    "How do the four fixed candidate learners, validation-selected adaptive Top-1 variants, "
                    "and validation-constructed soft ensembles compare under repeated within-project and cross-project evaluation?"
                ),
                "requirements": [
                    "Objective-matched comparisons.",
                    "Run-level outputs.",
                    "Project-level aggregation.",
                    "No post-hoc selection of a favorable comparison only.",
                    "Separate interpretation for within-project and cross-project settings."
                ]
            },
            "rq2": {
                "title": "Metric-dependent trade-offs",
                "exact_intent": (
                    "How do model rankings and conclusions change across discrimination, "
                    "thresholded classification, early-inspection ranking, and calibration-sensitive metrics?"
                ),
                "requirements": [
                    "No single metric defines an overall winner.",
                    "Metric direction must be explicit.",
                    "Ranking metrics, thresholded metrics, and calibration metrics represent different operational goals.",
                    "Brier score is minimized.",
                    "All other retained metrics are maximized."
                ]
            },
            "rq3": {
                "title": "Selection behavior and stability",
                "exact_intent": (
                    "How frequently and how stably are candidates selected across projects and seeds, "
                    "and how well do validation rankings agree with held-out test rankings?"
                ),
                "required_analyses": [
                    "Top-1 selection frequency.",
                    "Top-1 seed stability.",
                    "Soft-top-3 membership and order stability.",
                    "Exact validation-test Top-1 agreement.",
                    "Winner-set overlap.",
                    "Selected-candidate test rank.",
                    "Spearman and Kendall rank agreement.",
                    "Explicit statement that these are descriptive analyses, not proof of superiority."
                ]
            },
            "rq4": {
                "title": "Regret, ensemble size, and ablation",
                "exact_intent": (
                    "What do post-hoc regret and controlled ablation reveal about the value of "
                    "adaptive Top-1 selection, Soft-top-2, Soft-top-3, and Soft-all-4 relative to "
                    "fixed candidates and an oracle reference?"
                ),
                "requirements": [
                    "Fixed individual candidates.",
                    "Adaptive Top-1.",
                    "Soft-top-2.",
                    "Soft-top-3.",
                    "Soft-all-4.",
                    "Oracle best candidate on test used only as a post-hoc analytical reference.",
                    "Selected-versus-oracle regret.",
                    "Marginal ensemble-size comparisons.",
                    "No use of test information for actual model selection."
                ],
                "requires_new_computation": True
            }
        },
        
        "analysis_domains": {
            "experiments": ["within_project", "cross_project"],
            "projects": ["CM1", "JM1", "KC1", "KC2", "PC1"],
            "seeds": [7, 13, 29, 42, 101],
            "fixed_candidate_learners": [
                "LR_std_C0.1",
                "LR_std_C1",
                "DT_leaf5",
                "ET_leaf5"
            ],
            "existing_adaptive_models": [
                "AQRPE_v2_balanced",
                "AQRPE_v2_rank",
                "AQRPE_v2_mcc",
                "AQRPE_v2_soft_top3"
            ],
            "planned_additional_ensemble_models": [
                "AQRPE_v2_soft_top2",
                "AQRPE_v2_soft_all4"
            ],
            "concept_distinctions": [
                "candidate learner",
                "validation selector",
                "threshold policy",
                "ensemble construction rule",
                "post-hoc oracle"
            ]
        },
        
        "candidate_learners": {
            "LR_std_C0.1": {
                "type": "logistic_regression",
                "imputer": "median",
                "scaler": "StandardScaler",
                "C": 0.1,
                "penalty": "l2",
                "solver": "lbfgs",
                "class_weight": "balanced",
                "max_iter": 600,
                "random_state_source": "seed"
            },
            "LR_std_C1": {
                "type": "logistic_regression",
                "imputer": "median",
                "scaler": "StandardScaler",
                "C": 1.0,
                "penalty": "l2",
                "solver": "lbfgs",
                "class_weight": "balanced",
                "max_iter": 600,
                "random_state_source": "seed"
            },
            "DT_leaf5": {
                "type": "decision_tree",
                "imputer": "median",
                "criterion": "gini",
                "splitter": "best",
                "min_samples_leaf": 5,
                "max_depth": None,
                "class_weight": None,
                "random_state_source": "seed"
            },
            "ET_leaf5": {
                "type": "extra_trees",
                "imputer": "median",
                "n_estimators": 50,
                "criterion": "gini",
                "max_depth": None,
                "min_samples_leaf": 5,
                "max_features": "sqrt",
                "bootstrap": False,
                "class_weight": "balanced",
                "random_state_source": "seed",
                "n_jobs": 2
            }
        },
        
        "existing_adaptive_models": {
            "AQRPE_v2_balanced": {
                "validation_objective": "balanced",
                "selection_type": "adaptive_top1",
                "threshold_policy": "validation_tuned"
            },
            "AQRPE_v2_rank": {
                "validation_objective": "rank",
                "selection_type": "adaptive_top1",
                "threshold_policy": "fixed_0.5"
            },
            "AQRPE_v2_mcc": {
                "validation_objective": "mcc",
                "selection_type": "adaptive_top1",
                "threshold_policy": "validation_tuned"
            },
            "AQRPE_v2_soft_top3": {
                "validation_objective": "balanced",
                "membership_ranking_policy": "balanced_objective",
                "threshold_objective": "balanced",
                "ensemble_size": 3,
                "equal_weights": True
            }
        },
        
        "planned_models": {
            "AQRPE_v2_soft_top2": {
                "validation_objective": "balanced",
                "membership_ranking_policy": "balanced_objective",
                "threshold_objective": "balanced",
                "ensemble_size": 2,
                "equal_weights": True,
                "status": "planned"
            },
            "AQRPE_v2_soft_all4": {
                "validation_objective": "balanced",
                "membership_ranking_policy": "not_applicable_all_candidates",
                "threshold_objective": "balanced",
                "ensemble_size": 4,
                "equal_weights": True,
                "status": "planned"
            }
        },
        
        "metric_taxonomy": {
            "threshold_independent_score_ranking": {
                "avg_precision": {
                    "canonical_name": "avg_precision",
                    "display_name": "Average Precision",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": False,
                    "practical_interpretation": "Area under precision-recall curve, threshold-free ranking quality.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "selection_stability"]
                },
                "roc_auc": {
                    "canonical_name": "roc_auc",
                    "display_name": "ROC AUC",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": False,
                    "practical_interpretation": "Area under ROC curve, threshold-free ranking quality. Secondary because precision-recall is more informative under imbalance.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "diagnostic"]
                },
                "precision_at_10pct": {
                    "canonical_name": "precision_at_10pct",
                    "display_name": "Precision@10%",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": True,
                    "practical_interpretation": "Precision when inspecting top 10% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "recall_at_10pct": {
                    "canonical_name": "recall_at_10pct",
                    "display_name": "Recall@10%",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": True,
                    "practical_interpretation": "Defect coverage when inspecting top 10% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "lift_at_10pct": {
                    "canonical_name": "lift_at_10pct",
                    "display_name": "Lift@10%",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": True,
                    "practical_interpretation": "Ratio of precision@10% to baseline defect rate.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "precision_at_20pct": {
                    "canonical_name": "precision_at_20pct",
                    "display_name": "Precision@20%",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": True,
                    "practical_interpretation": "Precision when inspecting top 20% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "recall_at_20pct": {
                    "canonical_name": "recall_at_20pct",
                    "display_name": "Recall@20%",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": True,
                    "practical_interpretation": "Defect coverage when inspecting top 20% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "lift_at_20pct": {
                    "canonical_name": "lift_at_20pct",
                    "display_name": "Lift@20%",
                    "family": "threshold_independent_score_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": True,
                    "practical_interpretation": "Ratio of precision@20% to baseline defect rate.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "brier": {
                    "canonical_name": "brier",
                    "display_name": "Brier Score",
                    "family": "threshold_independent_score_ranking",
                    "direction": "lower_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": False,
                    "inspection_budget_dependent": False,
                    "practical_interpretation": "Proper probability scoring rule measuring squared probabilistic prediction error; it is sensitive to calibration and probability refinement and is not a pure calibration-only measure.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "calibration_analysis"]
                }
            },
            "threshold_dependent": {
                "mcc": {
                    "canonical_name": "mcc",
                    "display_name": "Matthews Correlation Coefficient",
                    "family": "threshold_dependent",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Balanced measure for binary classification, robust to class imbalance.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "thresholded_evaluation"]
                },
                "f1": {
                    "canonical_name": "f1",
                    "display_name": "F1 Score",
                    "family": "threshold_dependent",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Harmonic mean of precision and recall.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "thresholded_evaluation"]
                },
                "balanced_accuracy": {
                    "canonical_name": "balanced_accuracy",
                    "display_name": "Balanced Accuracy",
                    "family": "threshold_dependent",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Average of recall across both classes.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "thresholded_evaluation"]
                },
                "precision": {
                    "canonical_name": "precision",
                    "display_name": "Precision",
                    "family": "threshold_dependent",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Diagnostic metric, must not be interpreted without threshold policy.",
                    "allowed_analysis_uses": ["diagnostic"]
                },
                "recall": {
                    "canonical_name": "recall",
                    "display_name": "Recall",
                    "family": "threshold_dependent",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Diagnostic metric, must not be interpreted without threshold policy.",
                    "allowed_analysis_uses": ["diagnostic"]
                }
            }
        },
        
        "objective_policies": {
            "balanced_policy": {
                "candidate_ranking": "balanced validation objective",
                "threshold_selection": "balanced validation objective",
                "description": "Candidate ranking by balanced validation objective, threshold selected by balanced validation objective."
            },
            "mcc_policy": {
                "candidate_ranking": "validation MCC objective",
                "threshold_selection": "validation MCC objective",
                "description": "Candidate ranking by validation MCC objective, threshold selected by validation MCC objective."
            },
            "rank_score_only_policy": {
                "candidate_ranking": "rank objective",
                "threshold_selection": "fixed at 0.5",
                "primary_interpretation": "Restricted to threshold-free and top-k metrics.",
                "thresholded_metrics_status": "diagnostic only when threshold is fixed at 0.5",
                "description": "Candidate ranking by rank objective, primary interpretation restricted to threshold-free and top-k metrics, thresholded metrics are diagnostic only when threshold is fixed at 0.5."
            },
            "rank_plus_validation_threshold_policy": {
                "candidate_ranking": "rank objective",
                "threshold_selection": "tuned on validation only",
                "status": "planned sensitivity analysis",
                "must_not_replace": "existing score-only rank policy",
                "description": "Candidate ranking by rank objective, after candidate or ensemble selection, threshold is tuned on validation only. This policy is a planned sensitivity analysis and must not replace or silently overwrite the existing score-only rank policy."
            },
            "policy_mismatch_prohibition": [
                "Threshold-dependent method comparisons should use the same candidate-ranking objective and threshold-selection policy whenever scientifically possible.",
                "An MCC-tuned adaptive method must not be compared against a baseline using only a balanced-objective threshold and then interpreted as pure evidence of adaptive-selection benefit.",
                "Policy-mismatched comparisons may appear only as explicitly labeled descriptive legacy comparisons.",
                "Policy-mismatched comparisons cannot support superiority claims."
            ]
        },
        
        "baseline_policy": {
            "individual_fixed_baselines": [
                "LR_std_C0.1",
                "LR_std_C1",
                "DT_leaf5",
                "ET_leaf5"
            ],
            "best_fixed_baseline": {
                "selection_rules": [
                    "Separately for each metric.",
                    "Separately for each experiment.",
                    "From the four fixed candidates only.",
                    "For descriptive summary after all candidate results are available."
                ],
                "status": "post-hoc descriptive",
                "deployment_warning": "Must not be treated as a validation-selected deployment rule unless a separate validation-only baseline-selection mechanism is defined."
            }
        },
        
        "adaptive_top1_policy": {
            "definition": [
                "Train all four candidates on training data.",
                "Score all candidates on validation data.",
                "Select one candidate using the specified validation objective.",
                "Freeze its threshold according to the specified policy.",
                "Evaluate once on held-out test data."
            ],
            "distinguished_components": [
                "Selected candidate identity.",
                "Selection score.",
                "Validation threshold.",
                "Test performance.",
                "Test rank.",
                "Post-hoc regret."
            ],
            "prohibition": "No test label, test score, test metric, or test ranking may influence the selection."
        },
        
        "soft_ensemble_policy": {
            "definition": [
                "Rank candidates using validation scores only.",
                "Select the top k candidates using a deterministic tie policy.",
                "Average their defective-class probabilities with equal weights.",
                "Tune the ensemble threshold using validation data only.",
                "Freeze selected membership, order, weights, and threshold.",
                "Evaluate once on test data."
            ],
            "planned_k_values": [2, 3, 4],
            "soft_all_4_note": "Soft-all-4 includes all four candidates and therefore does not involve membership selection, but its threshold must still be tuned on validation only.",
            "key_assertions": [
                "Equal weighting is the primary ensemble rule.",
                "Learned weights are outside the current study scope.",
                "Soft-top-3 must not be treated as privileged before the ablation is complete.",
                "If Soft-top-3 does not outperform Soft-all-4 or Soft-top-2 consistently, the manuscript must report that result directly."
            ]
        },
        
        "tie_policy": {
            "validation_candidate_ranking": [
                "Use exact validation score ordering.",
                "Use a tolerance of 1e-12 only for reporting near ties.",
                "Do not merge non-transitive chains of near-equal values.",
                "If exact scores are equal, use the following deterministic candidate order: LR_std_C0.1, LR_std_C1, DT_leaf5, ET_leaf5."
            ],
            "distinguished_concepts": [
                "Exact tie.",
                "Near tie.",
                "Winner set.",
                "Deterministic operational choice."
            ],
            "scientific_analysis_rule": "For scientific analysis, all exact tied winners must be preserved in the winner set even if one deterministic candidate is used operationally."
        },
        
        "oracle_and_regret_policy": {
            "oracle_definition": "Post-hoc analytical reference only.",
            "oracle_computation": {
                "higher_is_better": "oracle_value = maximum test value among the four fixed candidates",
                "lower_is_better": "oracle_value = minimum test value among the four fixed candidates"
            },
            "absolute_regret": {
                "higher_is_better": "oracle_value - selected_value",
                "lower_is_better": "selected_value - oracle_value"
            },
            "regret_property": "Regret must always be non-negative up to floating-point tolerance.",
            "normalized_regret_formula": "absolute_regret / max(abs(oracle_value), 1e-12)",
            "separate_records": [
                "Exact winner.",
                "Tolerance winner using 1e-12.",
                "Selected candidate test rank.",
                "Selected candidate in oracle winner set.",
                "Absolute regret.",
                "Normalized regret."
            ],
            "key_assertions": [
                "Oracle is not a deployable model.",
                "Oracle uses test information only for retrospective analysis.",
                "Oracle values must never feed candidate selection, threshold selection, ensemble construction, or model fitting."
            ]
        },
        
        "unit_of_analysis_policy": {
            "primary_independent_unit": "software project",
            "repeated_seed": {
                "definition": "Within-project replication nested inside a project.",
                "not": [
                    "An independent project.",
                    "A valid substitute for additional datasets."
                ]
            },
            "run_level_observations_may_be_used_for": [
                "Descriptive distributions.",
                "Stability analysis.",
                "Event-level regret.",
                "Debugging and provenance."
            ],
            "run_level_observations_must_not_be_used_for": [
                "Fully independent observations for significance claims."
            ],
            "project_level_paired_summaries": [
                "First aggregate the five seeds within each project.",
                "Then compare methods across the five projects."
            ],
            "prohibitions": [
                "Treating 25 project-seed runs as 25 fully independent projects.",
                "Using seed-level p-values as primary superiority evidence.",
                "Claiming general population-level significance from five projects."
            ]
        },
        
        "statistical_reporting_policy": {
            "required_descriptive_reporting": [
                "Mean.",
                "Standard deviation.",
                "Median.",
                "Interquartile range.",
                "Minimum.",
                "Maximum.",
                "Positive / negative / tied project counts.",
                "Five raw project-level paired differences when space permits."
            ],
            "permitted_exploratory_inference": [
                "Exact Wilcoxon signed-rank test at project level only.",
                "Only when the assumptions and zero-difference handling are explicitly stated.",
                "Labeled exploratory.",
                "No binary accept/reject conclusion based only on p-values."
            ],
            "effect_reporting": [
                "Median paired project-level difference.",
                "Rank-biserial effect size or another predeclared paired effect size.",
                "Explicit warning that n_projects = 5."
            ],
            "key_assertions": [
                "No multiple-comparison-adjusted confirmatory family is claimed.",
                "No inferential superiority claim is authorized.",
                "Conclusions must emphasize direction, magnitude, consistency, and limitations."
            ]
        },
        
        "validation_test_agreement_policy": {
            "required_agreement_analyses": [
                "Strict Top-1 exact agreement.",
                "Tolerance-aware Top-1 agreement.",
                "Exact winner-set equality.",
                "Tolerance-aware winner-set equality.",
                "Winner-set overlap.",
                "Jaccard similarity.",
                "Spearman correlation.",
                "Kendall tau-b.",
                "Selected candidate test rank.",
                "Selected candidate in test winner set."
            ],
            "explicit_statements": [
                "Agreement is descriptive.",
                "Low agreement does not by itself prove the validation procedure is invalid.",
                "High agreement does not prove predictive superiority.",
                "Undefined rank correlations must remain missing, never substituted with zero.",
                "All test-based agreement is retrospective analysis only."
            ]
        },
        
        "sensitivity_analysis_policy": {
            "required_dimensions": {
                "balanced_objective_weights": {
                    "current": {
                        "mcc": 0.36,
                        "f1": 0.27,
                        "balanced_accuracy": 0.20,
                        "avg_precision": 0.10,
                        "recall_at_10pct": 0.05,
                        "recall_at_20pct": 0.02,
                        "brier_penalty": 0.02
                    },
                    "equal_positive_weights": {
                        "mcc": 0.16666666666666666,
                        "f1": 0.16666666666666666,
                        "balanced_accuracy": 0.16666666666666666,
                        "avg_precision": 0.16666666666666666,
                        "recall_at_10pct": 0.16666666666666666,
                        "recall_at_20pct": 0.16666666666666666,
                        "brier_penalty": 0.02
                    },
                    "mcc_emphasis": {
                        "mcc": 0.50,
                        "f1": 0.20,
                        "balanced_accuracy": 0.15,
                        "avg_precision": 0.08,
                        "recall_at_10pct": 0.05,
                        "recall_at_20pct": 0.02,
                        "brier_penalty": 0.02
                    },
                    "ranking_emphasis": {
                        "mcc": 0.20,
                        "f1": 0.15,
                        "balanced_accuracy": 0.15,
                        "avg_precision": 0.30,
                        "recall_at_10pct": 0.15,
                        "recall_at_20pct": 0.05,
                        "brier_penalty": 0.02
                    },
                    "constraints": [
                        "Positive metric weights must sum to 1 within 1e-12.",
                        "The Brier term must be subtracted.",
                        "The profile must be predeclared, not selected after observing test results."
                    ]
                },
                "rank_threshold_policy": {
                    "description": "Fixed 0.5, validation-tuned secondary threshold."
                },
                "threshold_grid": {
                    "current": {
                        "fixed": "linspace(0.03, 0.97, 41)",
                        "quantile_probabilities": "linspace(0.03, 0.97, 25)",
                        "combination": "unique(round(concat(fixed, validation-score quantiles), 6))",
                        "filter": "0 < threshold < 1"
                    },
                    "dense_sensitivity": {
                        "fixed": "linspace(0.01, 0.99, 99)",
                        "quantile_probabilities": "linspace(0.01, 0.99, 99)",
                        "combination": "unique(round(concat(fixed, validation-score quantiles), 6))",
                        "filter": "0 < threshold < 1"
                    },
                    "constraint": "Both grids must use validation scores only."
                },
                "cross_project_validation_design": {
                    "source_project_aware_protocol": [
                        "For each held-out target project and seed:",
                        "Use the other four projects as source projects.",
                        "Perform four leave-one-source-project-out validation folds.",
                        "In each fold, train on three source projects and validate on the fourth.",
                        "Generate out-of-fold validation probabilities for every source project.",
                        "Concatenate the four out-of-fold validation predictions.",
                        "Rank candidates using the aggregated out-of-fold validation objective.",
                        "Select candidate or ensemble membership from aggregated source-only validation evidence.",
                        "Select the threshold using only aggregated source-only out-of-fold validation predictions.",
                        "Refit frozen selected candidate(s) on all four source projects.",
                        "Evaluate once on the held-out target project.",
                        "Never use the target project for candidate selection, membership selection, threshold selection, or sensitivity choice."
                    ]
                }
            },
            "optional_after_required": [
                "More seeds.",
                "Additional learners.",
                "Broader hyperparameter search."
            ],
            "dataset_change_policy": "Changing the five benchmark projects is outside the current computational revision unless new verified datasets are introduced under a separate protocol."
        },
        
        "threats_to_validity": {
            "internal_validity": [
                {
                    "threat": "Leakage",
                    "possible_impact": "Inflated performance due to test information contaminating training.",
                    "current_mitigation": "Strict train/validation/test splits, leakage audit in Part 3B.",
                    "remaining_limitation": "Complex preprocessing pipelines may have subtle leakage.",
                    "planned_computational_response": "Comprehensive leakage audit in Part 3B."
                },
                {
                    "threat": "Preprocessing fitted outside training",
                    "possible_impact": "Data leakage through preprocessing parameters.",
                    "current_mitigation": "Preprocessing fitted on training fold only.",
                    "remaining_limitation": "Need to verify all preprocessing steps.",
                    "planned_computational_response": "Audit preprocessing pipeline in Part 3B."
                },
                {
                    "threat": "Nondeterminism",
                    "possible_impact": "Inconsistent results across runs.",
                    "current_mitigation": "Fixed random seeds, deterministic algorithms.",
                    "remaining_limitation": "Some library components may have nondeterministic behavior.",
                    "planned_computational_response": "Verify seed stability in Part 3C."
                },
                {
                    "threat": "Tie handling",
                    "possible_impact": "Selection instability when scores are equal.",
                    "current_mitigation": "Deterministic tie-breaking order.",
                    "remaining_limitation": "Near ties may still cause instability.",
                    "planned_computational_response": "Report tie frequency and impact in Part 3C."
                },
                {
                    "threat": "Threshold-selection mismatch",
                    "possible_impact": "Unfair comparisons using different threshold policies.",
                    "current_mitigation": "Objective-matched comparison policy.",
                    "remaining_limitation": "Policy mismatches may still occur in exploratory analyses.",
                    "planned_computational_response": "Explicit policy labeling in Part 3C."
                },
                {
                    "threat": "Post-hoc analytical choices",
                    "possible_impact": "Cherry-picking favorable analyses.",
                    "current_mitigation": "Pre-specified analysis contract.",
                    "remaining_limitation": "Exploratory analyses may still be selective.",
                    "planned_computational_response": "Distinguish pre-specified from exploratory in reporting."
                }
            ],
            "construct_validity": [
                {
                    "threat": "Metric disagreement",
                    "possible_impact": "Different metrics may rank models differently.",
                    "current_mitigation": "Comprehensive metric taxonomy, metric-dependent analysis.",
                    "remaining_limitation": "No single metric captures all operational goals.",
                    "planned_computational_response": "RQ2 analysis of metric trade-offs."
                },
                {
                    "threat": "Threshold dependence",
                    "possible_impact": "Thresholded metrics sensitive to threshold choice.",
                    "current_mitigation": "Validation-tuned thresholds, fixed 0.5 baseline.",
                    "remaining_limitation": "Threshold policy may favor certain methods.",
                    "planned_computational_response": "Sensitivity analysis on threshold policy in Part 3F."
                },
                {
                    "threat": "Top-k budget dependence",
                    "possible_impact": "Precision@k and recall@k depend on inspection budget.",
                    "current_mitigation": "Multiple k values (10%, 20%).",
                    "remaining_limitation": "Results may not generalize to other budgets.",
                    "planned_computational_response": "Report results for multiple k values."
                },
                {
                    "threat": "Calibration versus discrimination",
                    "possible_impact": "Models may excel at one but not the other.",
                    "current_mitigation": "Separate calibration metric (Brier score).",
                    "remaining_limitation": "Trade-off between calibration and discrimination.",
                    "planned_computational_response": "Analyze calibration-discrimination trade-off in RQ2."
                },
                {
                    "threat": "Oracle interpretation",
                    "possible_impact": "Oracle may be misinterpreted as achievable target.",
                    "current_mitigation": "Explicit post-hoc-only labeling.",
                    "remaining_limitation": "Oracle is not a deployable method.",
                    "planned_computational_response": "Clear oracle framing in all reporting."
                }
            ],
            "external_validity": [
                {
                    "threat": "Only five NASA/PROMISE projects",
                    "possible_impact": "Results may not generalize to other datasets.",
                    "current_mitigation": "Diverse project characteristics.",
                    "remaining_limitation": "Small number of datasets, all from same domain.",
                    "planned_computational_response": "Explicit limitation statement, no universal claims."
                },
                {
                    "threat": "Static metrics only",
                    "possible_impact": "Results may not apply to process or change metrics.",
                    "current_mitigation": "Clear scope definition.",
                    "remaining_limitation": "Static metrics may not capture dynamic defect patterns.",
                    "planned_computational_response": "Limitation statement on metric type."
                },
                {
                    "threat": "Older public benchmark data",
                    "possible_impact": "Data may not reflect modern software development.",
                    "current_mitigation": "Use of established benchmark.",
                    "remaining_limitation": "Data age and collection methodology.",
                    "planned_computational_response": "Limitation statement on data vintage."
                },
                {
                    "threat": "Compact learner pool",
                    "possible_impact": "Results may not extend to other learner types.",
                    "current_mitigation": "Diverse learner families (LR, DT, ET).",
                    "remaining_limitation": "Limited hyperparameter search, no deep learning.",
                    "planned_computational_response": "Limitation statement on learner scope."
                },
                {
                    "threat": "No industrial deployment evaluation",
                    "possible_impact": "Practical utility unverified.",
                    "current_mitigation": "Clear empirical study framing.",
                    "remaining_limitation": "No real-world deployment validation.",
                    "planned_computational_response": "Limitation statement on deployment gap."
                }
            ],
            "conclusion_validity": [
                {
                    "threat": "Five independent projects",
                    "possible_impact": "Low statistical power.",
                    "current_mitigation": "Project-level paired analysis, descriptive focus.",
                    "remaining_limitation": "N=5 is small for strong inference.",
                    "planned_computational_response": "Emphasize descriptive over inferential, report effect sizes."
                },
                {
                    "threat": "Repeated seeds are nested",
                    "possible_impact": "Pseudo-replication if treated as independent.",
                    "current_mitigation": "Project as primary unit, seed as nested replication.",
                    "remaining_limitation": "Limited independent observations.",
                    "planned_computational_response": "Strict unit-of-analysis policy, no seed-level inference."
                },
                {
                    "threat": "Low power",
                    "possible_impact": "Type II errors, missed real differences.",
                    "current_mitigation": "Descriptive emphasis, effect size reporting.",
                    "remaining_limitation": "Small N limits detection of small effects.",
                    "planned_computational_response": "Power limitation in discussion."
                },
                {
                    "threat": "Multiple metrics",
                    "possible_impact": "Multiple comparisons, inconsistent conclusions.",
                    "current_mitigation": "Metric taxonomy, family grouping.",
                    "remaining_limitation": "No unified metric family-wise error control.",
                    "planned_computational_response": "Metric-by-metric interpretation, no global superiority claim."
                },
                {
                    "threat": "Descriptive versus inferential distinction",
                    "possible_impact": "Over-interpretation of descriptive patterns.",
                    "current_mitigation": "Clear labeling of descriptive vs exploratory inference.",
                    "remaining_limitation": "Exploratory tests may be misinterpreted.",
                    "planned_computational_response": "Explicit framing, no binary accept/reject."
                },
                {
                    "threat": "Sensitivity to objective weights and validation design",
                    "possible_impact": "Results may change under different validation schemes.",
                    "current_mitigation": "Pre-specified validation design.",
                    "remaining_limitation": "Many possible validation alternatives.",
                    "planned_computational_response": "Sensitivity analysis in Part 3F."
                }
            ]
        },
        
        "reviewer_traceability_matrix": {
            "reviewer_1_comment_1": {
                "computational_response": "Metric dictionary in later Part 3H",
                "manuscript_response": "Brief practical metric explanation"
            },
            "reviewer_1_comment_2": {
                "computational_response": "None",
                "manuscript_response": "Key finding paragraph before every results table"
            },
            "reviewer_1_comment_3": {
                "computational_response": "Deterministic workflow figure in later Part 3H",
                "manuscript_response": "Include figure and description"
            },
            "reviewer_2_comment_1": {
                "computational_response": "None",
                "manuscript_response": "Rewrite abstract to 150-250 words"
            },
            "reviewer_2_comment_2": {
                "computational_response": "None",
                "manuscript_response": "Verified 2025-2026 literature update"
            },
            "reviewer_2_comment_3": {
                "computational_response": [
                    "Objective-matched comparisons.",
                    "Prediction ledger.",
                    "Regret.",
                    "Ablation.",
                    "Sensitivity.",
                    "Project-level effects"
                ],
                "manuscript_response": "Not applicable (computational focus)"
            },
            "reviewer_2_comment_4": {
                "computational_response": [
                    "Leakage audit.",
                    "Robustness analyses.",
                    "Dependency-aware statistical policy"
                ],
                "manuscript_response": "Not applicable (computational focus)"
            },
            "reviewer_2_comment_5": {
                "computational_response": "Final limitations grounded in completed analyses",
                "manuscript_response": "Not applicable (computational focus)"
            },
            "reviewer_2_comment_6": {
                "computational_response": "None",
                "manuscript_response": "Citation renumbering and Springer formatting"
            },
            "reviewer_2_comment_7": {
                "computational_response": "None",
                "manuscript_response": "Citation renumbering and Springer formatting"
            },
            "reviewer_3_novelty_concern": {
                "computational_response": [
                    "Selection frequency.",
                    "Seed stability.",
                    "Validation-test agreement.",
                    "Post-hoc regret.",
                    "Ensemble-size ablation.",
                    "Sensitivity analysis.",
                    "Objective-matched comparison"
                ],
                "scientific_response": "Reposition the study as a controlled empirical evaluation rather than a fundamentally novel algorithm."
            }
        },
        
        "remaining_stage_roadmap": [
            "Part 3A: Scientific analysis contract",
            "Part 3B: Prediction ledger and split/leakage audit",
            "Part 3C: Objective-matched candidate and adaptive evaluation",
            "Part 3D: Post-hoc regret and oracle-gap analysis",
            "Part 3E: Ensemble-size and component ablation",
            "Part 3F: Methodological sensitivity analyses",
            "Part 3G: Project-level paired effects and uncertainty",
            "Part 3H: Workflow diagram and metric dictionary",
            "Part 4: Final full rerun, deterministic artifact freeze, package rebuild, and canonical manifest"
        ],
        
        "prohibited_claims": [
            "No method universally dominates all others across all metrics, projects, and settings.",
            "Validation-based selection guarantees superior test performance.",
            "Soft ensembles always outperform fixed candidates.",
            "Adaptive Top-1 selection is always better than fixed baselines.",
            "The oracle reference is a deployable model.",
            "The five projects are a representative sample of all software projects.",
            "The results generalize to industrial deployment without further validation.",
            "Statistical significance tests with n=5 projects provide definitive population-level evidence.",
            "Metric choice is arbitrary and does not affect conclusions.",
            "Threshold policy choice is arbitrary and does not affect conclusions.",
            "Validation-test agreement is a proof of validity.",
            "Post-hoc regret analysis is a validation procedure."
        ],
        
        "stage_gate": {
            "part3a_contract_frozen": False,
            "model_rerun_performed": False,
            "canonical_outputs_modified": False,
            "manuscript_modified": False,
            "next_authorized_stage": "Part 3B",
            "part3b_constraint": "Part 3B cannot alter the current 400 canonical result rows or current canonical manuscript tables unless a later explicitly approved migration stage is created."
        },
        
        "reviewer_coverage_evidence": {
            "reviewer_1_comment_count": 3,
            "reviewer_2_comment_count": 7,
            "reviewer_3_concern_count": 1,
            "covered_comment_count": 11,
            "coverage_identifiers": [
                "reviewer_1_comment_1",
                "reviewer_1_comment_2",
                "reviewer_1_comment_3",
                "reviewer_2_comment_1",
                "reviewer_2_comment_2",
                "reviewer_2_comment_3",
                "reviewer_2_comment_4",
                "reviewer_2_comment_5",
                "reviewer_2_comment_6",
                "reviewer_2_comment_7",
                "reviewer_3_novelty_concern"
            ]
        }
    }
    
    return contract


def validate_contract(contract: Dict[str, Any]) -> Dict[str, bool]:
    """Validate the complete contract payload."""
    checks = {}
    
    # Exact Research Questions - validate complete exact structure
    rq = contract["research_questions"]
    checks["exact_research_questions_passed"] = (
        rq["count"] == 4 and
        set(rq.keys()) == {"count", "rq1", "rq2", "rq3", "rq4"} and
        rq["rq1"]["title"] == "Comparative performance" and
        rq["rq1"]["exact_intent"] == "How do the four fixed candidate learners, validation-selected adaptive Top-1 variants, and validation-constructed soft ensembles compare under repeated within-project and cross-project evaluation?" and
        rq["rq1"]["requirements"] == [
            "Objective-matched comparisons.",
            "Run-level outputs.",
            "Project-level aggregation.",
            "No post-hoc selection of a favorable comparison only.",
            "Separate interpretation for within-project and cross-project settings."
        ] and
        rq["rq2"]["title"] == "Metric-dependent trade-offs" and
        rq["rq2"]["exact_intent"] == "How do model rankings and conclusions change across discrimination, thresholded classification, early-inspection ranking, and calibration-sensitive metrics?" and
        rq["rq2"]["requirements"] == [
            "No single metric defines an overall winner.",
            "Metric direction must be explicit.",
            "Ranking metrics, thresholded metrics, and calibration metrics represent different operational goals.",
            "Brier score is minimized.",
            "All other retained metrics are maximized."
        ] and
        rq["rq3"]["title"] == "Selection behavior and stability" and
        rq["rq3"]["exact_intent"] == "How frequently and how stably are candidates selected across projects and seeds, and how well do validation rankings agree with held-out test rankings?" and
        rq["rq3"]["required_analyses"] == [
            "Top-1 selection frequency.",
            "Top-1 seed stability.",
            "Soft-top-3 membership and order stability.",
            "Exact validation-test Top-1 agreement.",
            "Winner-set overlap.",
            "Selected-candidate test rank.",
            "Spearman and Kendall rank agreement.",
            "Explicit statement that these are descriptive analyses, not proof of superiority."
        ] and
        rq["rq4"]["title"] == "Regret, ensemble size, and ablation" and
        rq["rq4"]["exact_intent"] == "What do post-hoc regret and controlled ablation reveal about the value of adaptive Top-1 selection, Soft-top-2, Soft-top-3, and Soft-all-4 relative to fixed candidates and an oracle reference?" and
        rq["rq4"]["requirements"] == [
            "Fixed individual candidates.",
            "Adaptive Top-1.",
            "Soft-top-2.",
            "Soft-top-3.",
            "Soft-all-4.",
            "Oracle best candidate on test used only as a post-hoc analytical reference.",
            "Selected-versus-oracle regret.",
            "Marginal ensemble-size comparisons.",
            "No use of test information for actual model selection."
        ] and
        rq["rq4"]["requires_new_computation"] == True
    )
    
    # Exact analysis domains - validate complete exact dictionary
    ad = contract["analysis_domains"]
    checks["analysis_domains_passed"] = (
        set(ad.keys()) == {"experiments", "projects", "seeds", "fixed_candidate_learners", "existing_adaptive_models", "planned_additional_ensemble_models", "concept_distinctions"} and
        ad["experiments"] == ["within_project", "cross_project"] and
        ad["projects"] == ["CM1", "JM1", "KC1", "KC2", "PC1"] and
        ad["seeds"] == [7, 13, 29, 42, 101] and
        ad["fixed_candidate_learners"] == ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"] and
        ad["existing_adaptive_models"] == ["AQRPE_v2_balanced", "AQRPE_v2_rank", "AQRPE_v2_mcc", "AQRPE_v2_soft_top3"] and
        ad["planned_additional_ensemble_models"] == ["AQRPE_v2_soft_top2", "AQRPE_v2_soft_all4"] and
        ad["concept_distinctions"] == ["candidate learner", "validation selector", "threshold policy", "ensemble construction rule", "post-hoc oracle"]
    )
    
    # Candidate metadata matches current pipeline - enforce exact field sets
    lr_c01 = contract["candidate_learners"]["LR_std_C0.1"]
    lr_c1 = contract["candidate_learners"]["LR_std_C1"]
    dt = contract["candidate_learners"]["DT_leaf5"]
    et = contract["candidate_learners"]["ET_leaf5"]
    
    lr_exact_keys = {"type", "imputer", "scaler", "C", "penalty", "solver", "class_weight", "max_iter", "random_state_source"}
    dt_exact_keys = {"type", "imputer", "criterion", "splitter", "min_samples_leaf", "max_depth", "class_weight", "random_state_source"}
    et_exact_keys = {"type", "imputer", "n_estimators", "criterion", "max_depth", "min_samples_leaf", "max_features", "bootstrap", "class_weight", "random_state_source", "n_jobs"}
    
    checks["candidate_metadata_matches_current_pipeline"] = (
        set(lr_c01.keys()) == lr_exact_keys and
        set(lr_c1.keys()) == lr_exact_keys and
        set(dt.keys()) == dt_exact_keys and
        set(et.keys()) == et_exact_keys and
        lr_c01["type"] == "logistic_regression" and
        lr_c01["imputer"] == "median" and
        lr_c01["scaler"] == "StandardScaler" and
        lr_c01["C"] == 0.1 and
        lr_c01["penalty"] == "l2" and
        lr_c01["solver"] == "lbfgs" and
        lr_c01["class_weight"] == "balanced" and
        lr_c01["max_iter"] == 600 and
        lr_c01["random_state_source"] == "seed" and
        lr_c1["type"] == "logistic_regression" and
        lr_c1["imputer"] == "median" and
        lr_c1["scaler"] == "StandardScaler" and
        lr_c1["C"] == 1.0 and
        lr_c1["penalty"] == "l2" and
        lr_c1["solver"] == "lbfgs" and
        lr_c1["class_weight"] == "balanced" and
        lr_c1["max_iter"] == 600 and
        lr_c1["random_state_source"] == "seed" and
        dt["type"] == "decision_tree" and
        dt["imputer"] == "median" and
        dt["criterion"] == "gini" and
        dt["splitter"] == "best" and
        dt["min_samples_leaf"] == 5 and
        dt["max_depth"] is None and
        dt["class_weight"] is None and
        dt["random_state_source"] == "seed" and
        et["type"] == "extra_trees" and
        et["imputer"] == "median" and
        et["n_estimators"] == 50 and
        et["criterion"] == "gini" and
        et["max_depth"] is None and
        et["min_samples_leaf"] == 5 and
        et["max_features"] == "sqrt" and
        et["bootstrap"] is False and
        et["class_weight"] == "balanced" and
        et["random_state_source"] == "seed" and
        et["n_jobs"] == 2
    )
    
    # Required metric set - validate exact taxonomy families and field sets
    all_metrics = {}
    for family in contract["metric_taxonomy"].values():
        for metric_name, metric_info in family.items():
            all_metrics[metric_name] = metric_info
    
    required_metrics = {
        "avg_precision", "roc_auc", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
        "precision_at_20pct", "recall_at_20pct", "lift_at_20pct", "brier",
        "mcc", "f1", "balanced_accuracy", "precision", "recall"
    }
    
    # Validate exact taxonomy families
    taxonomy_families = set(contract["metric_taxonomy"].keys())
    exact_families = {"threshold_independent_score_ranking", "threshold_dependent"}
    
    # Validate exact nine threshold-independent metrics
    ti_metrics = set(contract["metric_taxonomy"]["threshold_independent_score_ranking"].keys())
    exact_ti = {"avg_precision", "roc_auc", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "precision_at_20pct", "recall_at_20pct", "lift_at_20pct", "brier"}
    
    # Validate exact five threshold-dependent metrics
    td_metrics = set(contract["metric_taxonomy"]["threshold_dependent"].keys())
    exact_td = {"mcc", "f1", "balanced_accuracy", "precision", "recall"}
    
    # Validate exact field sets for every metric
    common_fields = {"canonical_name", "display_name", "family", "direction", "primary_or_secondary", "threshold_dependent", "practical_interpretation", "allowed_analysis_uses"}
    ti_extra_field = {"inspection_budget_dependent"}
    
    all_fields_correct = True
    for metric_name, metric_info in all_metrics.items():
        expected_fields = common_fields.copy()
        if metric_name in ti_metrics:
            expected_fields.add("inspection_budget_dependent")
        if set(metric_info.keys()) != expected_fields:
            all_fields_correct = False
            break
    
    checks["metric_taxonomy_passed"] = (
        set(all_metrics.keys()) == required_metrics and
        taxonomy_families == exact_families and
        ti_metrics == exact_ti and
        td_metrics == exact_td and
        all_fields_correct
    )
    
    # Metric count is 14
    checks["metric_count_is_14"] = len(all_metrics) == 14
    
    # Every metric has valid direction - brier must be lower_is_better, all others higher_is_better
    checks["metric_direction_passed"] = (
        all_metrics["brier"]["direction"] == "lower_is_better" and
        all(all_metrics[m]["direction"] == "higher_is_better" for m in all_metrics if m != "brier")
    )
    
    # Metric threshold dependency
    threshold_independent = {"avg_precision", "roc_auc", "precision_at_10pct", "recall_at_10pct", 
                           "lift_at_10pct", "precision_at_20pct", "recall_at_20pct", "lift_at_20pct", "brier"}
    threshold_dependent = {"mcc", "f1", "balanced_accuracy", "precision", "recall"}
    checks["metric_threshold_dependency_passed"] = (
        all(all_metrics[m]["threshold_dependent"] == False for m in threshold_independent) and
        all(all_metrics[m]["threshold_dependent"] == True for m in threshold_dependent)
    )
    
    # Metric inspection budget dependency
    inspection_budget_dependent = {"precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
                                   "precision_at_20pct", "recall_at_20pct", "lift_at_20pct"}
    inspection_budget_independent = {"avg_precision", "roc_auc", "brier"}
    checks["metric_inspection_budget_dependency_passed"] = (
        all(all_metrics[m].get("inspection_budget_dependent", False) == True for m in inspection_budget_dependent) and
        all(all_metrics[m].get("inspection_budget_dependent", False) == False for m in inspection_budget_independent)
    )
    
    # Brier marked secondary - verify complete frozen primary and secondary classification
    primary_metrics = {"avg_precision", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct", "mcc", "f1", "balanced_accuracy"}
    secondary_metrics = {"roc_auc", "precision_at_20pct", "recall_at_20pct", "lift_at_20pct", "brier", "precision", "recall"}
    
    checks["metric_primary_secondary_passed"] = (
        all(all_metrics[m]["primary_or_secondary"] == "primary" for m in primary_metrics) and
        all(all_metrics[m]["primary_or_secondary"] == "secondary" for m in secondary_metrics)
    )
    
    # Objective policy passed - validate exact key set and ordered prohibitions
    obj_policies = contract["objective_policies"]
    exact_obj_keys = {"balanced_policy", "mcc_policy", "rank_score_only_policy", "rank_plus_validation_threshold_policy", "policy_mismatch_prohibition"}
    exact_prohibitions = [
        "Threshold-dependent method comparisons should use the same candidate-ranking objective and threshold-selection policy whenever scientifically possible.",
        "An MCC-tuned adaptive method must not be compared against a baseline using only a balanced-objective threshold and then interpreted as pure evidence of adaptive-selection benefit.",
        "Policy-mismatched comparisons may appear only as explicitly labeled descriptive legacy comparisons.",
        "Policy-mismatched comparisons cannot support superiority claims."
    ]
    checks["objective_policy_passed"] = (
        set(obj_policies.keys()) == exact_obj_keys and
        obj_policies["policy_mismatch_prohibition"] == exact_prohibitions and
        obj_policies["balanced_policy"]["candidate_ranking"] == "balanced validation objective" and
        obj_policies["balanced_policy"]["threshold_selection"] == "balanced validation objective" and
        obj_policies["mcc_policy"]["candidate_ranking"] == "validation MCC objective" and
        obj_policies["mcc_policy"]["threshold_selection"] == "validation MCC objective" and
        obj_policies["rank_score_only_policy"]["candidate_ranking"] == "rank objective" and
        obj_policies["rank_score_only_policy"]["threshold_selection"] == "fixed at 0.5" and
        obj_policies["rank_plus_validation_threshold_policy"]["candidate_ranking"] == "rank objective" and
        obj_policies["rank_plus_validation_threshold_policy"]["threshold_selection"] == "tuned on validation only" and
        obj_policies["rank_plus_validation_threshold_policy"]["status"] == "planned sensitivity analysis"
    )
    
    # Existing Soft-top-3 objective - require exact key set and values
    soft_top3 = contract["existing_adaptive_models"]["AQRPE_v2_soft_top3"]
    exact_soft_top3_keys = {"validation_objective", "membership_ranking_policy", "threshold_objective", "ensemble_size", "equal_weights"}
    checks["existing_soft_top3_policy_passed"] = (
        set(soft_top3.keys()) == exact_soft_top3_keys and
        soft_top3["validation_objective"] == "balanced" and
        soft_top3["membership_ranking_policy"] == "balanced_objective" and
        soft_top3["threshold_objective"] == "balanced" and
        soft_top3["ensemble_size"] == 3 and
        soft_top3["equal_weights"] == True
    )
    
    # Baseline policy passed - validate exact key set and content
    baseline = contract["baseline_policy"]
    exact_baseline_keys = {"individual_fixed_baselines", "best_fixed_baseline"}
    exact_baselines = ["LR_std_C0.1", "LR_std_C1", "DT_leaf5", "ET_leaf5"]
    exact_selection_rules = [
        "Separately for each metric.",
        "Separately for each experiment.",
        "From the four fixed candidates only.",
        "For descriptive summary after all candidate results are available."
    ]
    checks["baseline_policy_passed"] = (
        set(baseline.keys()) == exact_baseline_keys and
        baseline["individual_fixed_baselines"] == exact_baselines and
        baseline["best_fixed_baseline"]["selection_rules"] == exact_selection_rules and
        baseline["best_fixed_baseline"]["status"] == "post-hoc descriptive" and
        baseline["best_fixed_baseline"]["deployment_warning"] == "Must not be treated as a validation-selected deployment rule unless a separate validation-only baseline-selection mechanism is defined."
    )
    
    # Adaptive policy passed - validate exact key set and content
    adaptive = contract["adaptive_top1_policy"]
    exact_adaptive_keys = {"definition", "distinguished_components", "prohibition"}
    exact_definition = [
        "Train all four candidates on training data.",
        "Score all candidates on validation data.",
        "Select one candidate using the specified validation objective.",
        "Freeze its threshold according to the specified policy.",
        "Evaluate once on held-out test data."
    ]
    exact_components = [
        "Selected candidate identity.",
        "Selection score.",
        "Validation threshold.",
        "Test performance.",
        "Test rank.",
        "Post-hoc regret."
    ]
    checks["adaptive_policy_passed"] = (
        set(adaptive.keys()) == exact_adaptive_keys and
        adaptive["definition"] == exact_definition and
        adaptive["distinguished_components"] == exact_components and
        adaptive["prohibition"] == "No test label, test score, test metric, or test ranking may influence the selection."
    )
    
    # Ensemble policy passed - validate exact key sets and values
    soft_top2 = contract["planned_models"]["AQRPE_v2_soft_top2"]
    soft_all4 = contract["planned_models"]["AQRPE_v2_soft_all4"]
    exact_soft_top2_keys = {"validation_objective", "membership_ranking_policy", "threshold_objective", "ensemble_size", "equal_weights", "status"}
    exact_soft_all4_keys = {"validation_objective", "membership_ranking_policy", "threshold_objective", "ensemble_size", "equal_weights", "status"}
    checks["ensemble_policy_passed"] = (
        contract["soft_ensemble_policy"]["planned_k_values"] == [2, 3, 4] and
        contract["existing_adaptive_models"]["AQRPE_v2_soft_top3"]["equal_weights"] == True and
        set(soft_top2.keys()) == exact_soft_top2_keys and
        soft_top2["validation_objective"] == "balanced" and
        soft_top2["membership_ranking_policy"] == "balanced_objective" and
        soft_top2["threshold_objective"] == "balanced" and
        soft_top2["ensemble_size"] == 2 and
        soft_top2["equal_weights"] == True and
        soft_top2["status"] == "planned" and
        set(soft_all4.keys()) == exact_soft_all4_keys and
        soft_all4["validation_objective"] == "balanced" and
        soft_all4["membership_ranking_policy"] == "not_applicable_all_candidates" and
        soft_all4["threshold_objective"] == "balanced" and
        soft_all4["ensemble_size"] == 4 and
        soft_all4["equal_weights"] == True and
        soft_all4["status"] == "planned"
    )
    
    # Tie policy passed - verify exact ordered rules
    tie_rules = contract["tie_policy"]["validation_candidate_ranking"]
    expected_tie_rules = [
        "Use exact validation score ordering.",
        "Use a tolerance of 1e-12 only for reporting near ties.",
        "Do not merge non-transitive chains of near-equal values.",
        "If exact scores are equal, use the following deterministic candidate order: LR_std_C0.1, LR_std_C1, DT_leaf5, ET_leaf5."
    ]
    checks["tie_policy_passed"] = tie_rules == expected_tie_rules
    
    # Oracle policy passed
    checks["oracle_policy_passed"] = (
        contract["oracle_and_regret_policy"]["oracle_definition"] == "Post-hoc analytical reference only."
    )
    
    # Unit of analysis policy passed
    checks["unit_of_analysis_policy_passed"] = (
        contract["unit_of_analysis_policy"]["primary_independent_unit"] == "software project"
    )
    
    # Statistical reporting policy passed - validate exact key set and ordered contents
    stat = contract["statistical_reporting_policy"]
    exact_stat_keys = {"required_descriptive_reporting", "permitted_exploratory_inference", "effect_reporting", "key_assertions"}
    exact_descriptive = [
        "Mean.",
        "Standard deviation.",
        "Median.",
        "Interquartile range.",
        "Minimum.",
        "Maximum.",
        "Positive / negative / tied project counts.",
        "Five raw project-level paired differences when space permits."
    ]
    exact_exploratory = [
        "Exact Wilcoxon signed-rank test at project level only.",
        "Only when the assumptions and zero-difference handling are explicitly stated.",
        "Labeled exploratory.",
        "No binary accept/reject conclusion based only on p-values."
    ]
    exact_effect = [
        "Median paired project-level difference.",
        "Rank-biserial effect size or another predeclared paired effect size.",
        "Explicit warning that n_projects = 5."
    ]
    exact_key_assertions = [
        "No multiple-comparison-adjusted confirmatory family is claimed.",
        "No inferential superiority claim is authorized.",
        "Conclusions must emphasize direction, magnitude, consistency, and limitations."
    ]
    checks["statistical_reporting_policy_passed"] = (
        set(stat.keys()) == exact_stat_keys and
        stat["required_descriptive_reporting"] == exact_descriptive and
        stat["permitted_exploratory_inference"] == exact_exploratory and
        stat["effect_reporting"] == exact_effect and
        stat["key_assertions"] == exact_key_assertions
    )
    
    # Agreement policy passed - validate exact key set and ordered contents
    agreement = contract["validation_test_agreement_policy"]
    exact_agreement_keys = {"required_agreement_analyses", "explicit_statements"}
    exact_analyses = [
        "Strict Top-1 exact agreement.",
        "Tolerance-aware Top-1 agreement.",
        "Exact winner-set equality.",
        "Tolerance-aware winner-set equality.",
        "Winner-set overlap.",
        "Jaccard similarity.",
        "Spearman correlation.",
        "Kendall tau-b.",
        "Selected candidate test rank.",
        "Selected candidate in test winner set."
    ]
    exact_statements = [
        "Agreement is descriptive.",
        "Low agreement does not by itself prove the validation procedure is invalid.",
        "High agreement does not prove predictive superiority.",
        "Undefined rank correlations must remain missing, never substituted with zero.",
        "All test-based agreement is retrospective analysis only."
    ]
    checks["agreement_policy_passed"] = (
        set(agreement.keys()) == exact_agreement_keys and
        agreement["required_agreement_analyses"] == exact_analyses and
        agreement["explicit_statements"] == exact_statements
    )
    
    # Balanced weight sensitivity frozen - verify exact dictionaries and reject extra fields
    weights = contract["sensitivity_analysis_policy"]["required_dimensions"]["balanced_objective_weights"]
    exact_profile_keys = {"mcc", "f1", "balanced_accuracy", "avg_precision", "recall_at_10pct", "recall_at_20pct", "brier_penalty"}
    current_profile = weights["current"]
    equal_profile = weights["equal_positive_weights"]
    mcc_profile = weights["mcc_emphasis"]
    ranking_profile = weights["ranking_emphasis"]
    
    # Verify exact current profile
    current_exact = (
        set(current_profile.keys()) == exact_profile_keys and
        abs(current_profile["mcc"] - 0.36) < 1e-12 and
        abs(current_profile["f1"] - 0.27) < 1e-12 and
        abs(current_profile["balanced_accuracy"] - 0.20) < 1e-12 and
        abs(current_profile["avg_precision"] - 0.10) < 1e-12 and
        abs(current_profile["recall_at_10pct"] - 0.05) < 1e-12 and
        abs(current_profile["recall_at_20pct"] - 0.02) < 1e-12 and
        abs(current_profile["brier_penalty"] - 0.02) < 1e-12
    )
    
    # Verify exact equal positive weights profile
    equal_exact = (
        set(equal_profile.keys()) == exact_profile_keys and
        abs(equal_profile["mcc"] - 1/6) < 1e-12 and
        abs(equal_profile["f1"] - 1/6) < 1e-12 and
        abs(equal_profile["balanced_accuracy"] - 1/6) < 1e-12 and
        abs(equal_profile["avg_precision"] - 1/6) < 1e-12 and
        abs(equal_profile["recall_at_10pct"] - 1/6) < 1e-12 and
        abs(equal_profile["recall_at_20pct"] - 1/6) < 1e-12 and
        abs(equal_profile["brier_penalty"] - 0.02) < 1e-12
    )
    
    # Verify exact MCC emphasis profile
    mcc_exact = (
        set(mcc_profile.keys()) == exact_profile_keys and
        abs(mcc_profile["mcc"] - 0.50) < 1e-12 and
        abs(mcc_profile["f1"] - 0.20) < 1e-12 and
        abs(mcc_profile["balanced_accuracy"] - 0.15) < 1e-12 and
        abs(mcc_profile["avg_precision"] - 0.08) < 1e-12 and
        abs(mcc_profile["recall_at_10pct"] - 0.05) < 1e-12 and
        abs(mcc_profile["recall_at_20pct"] - 0.02) < 1e-12 and
        abs(mcc_profile["brier_penalty"] - 0.02) < 1e-12
    )
    
    # Verify exact ranking emphasis profile
    ranking_exact = (
        set(ranking_profile.keys()) == exact_profile_keys and
        abs(ranking_profile["mcc"] - 0.20) < 1e-12 and
        abs(ranking_profile["f1"] - 0.15) < 1e-12 and
        abs(ranking_profile["balanced_accuracy"] - 0.15) < 1e-12 and
        abs(ranking_profile["avg_precision"] - 0.30) < 1e-12 and
        abs(ranking_profile["recall_at_10pct"] - 0.15) < 1e-12 and
        abs(ranking_profile["recall_at_20pct"] - 0.05) < 1e-12 and
        abs(ranking_profile["brier_penalty"] - 0.02) < 1e-12
    )
    
    # Verify positive weight sums equal 1.0
    def sum_positive_weights(profile):
        return profile["mcc"] + profile["f1"] + profile["balanced_accuracy"] + profile["avg_precision"] + profile["recall_at_10pct"] + profile["recall_at_20pct"]
    
    current_sum_ok = abs(sum_positive_weights(current_profile) - 1.0) <= 1e-12
    equal_sum_ok = abs(sum_positive_weights(equal_profile) - 1.0) <= 1e-12
    mcc_sum_ok = abs(sum_positive_weights(mcc_profile) - 1.0) <= 1e-12
    ranking_sum_ok = abs(sum_positive_weights(ranking_profile) - 1.0) <= 1e-12
    
    # Verify Brier penalty is 0.02 for all profiles
    brier_ok = (
        abs(current_profile["brier_penalty"] - 0.02) < 1e-12 and
        abs(equal_profile["brier_penalty"] - 0.02) < 1e-12 and
        abs(mcc_profile["brier_penalty"] - 0.02) < 1e-12 and
        abs(ranking_profile["brier_penalty"] - 0.02) < 1e-12
    )
    
    checks["balanced_weight_sensitivity_frozen"] = (
        current_exact and equal_exact and mcc_exact and ranking_exact and
        current_sum_ok and equal_sum_ok and mcc_sum_ok and ranking_sum_ok and brier_ok
    )
    
    # Threshold grid sensitivity frozen - verify exact dictionaries and reject extra fields
    grid = contract["sensitivity_analysis_policy"]["required_dimensions"]["threshold_grid"]
    exact_grid_keys = {"current", "dense_sensitivity", "constraint"}
    exact_grid_fields = {"fixed", "quantile_probabilities", "combination", "filter"}
    current_grid = grid["current"]
    dense_grid = grid["dense_sensitivity"]
    
    # Verify exact current grid
    current_grid_exact = (
        set(current_grid.keys()) == exact_grid_fields and
        current_grid["fixed"] == "linspace(0.03, 0.97, 41)" and
        current_grid["quantile_probabilities"] == "linspace(0.03, 0.97, 25)" and
        current_grid["combination"] == "unique(round(concat(fixed, validation-score quantiles), 6))" and
        current_grid["filter"] == "0 < threshold < 1"
    )
    
    # Verify exact dense sensitivity grid
    dense_grid_exact = (
        set(dense_grid.keys()) == exact_grid_fields and
        dense_grid["fixed"] == "linspace(0.01, 0.99, 99)" and
        dense_grid["quantile_probabilities"] == "linspace(0.01, 0.99, 99)" and
        dense_grid["combination"] == "unique(round(concat(fixed, validation-score quantiles), 6))" and
        dense_grid["filter"] == "0 < threshold < 1"
    )
    
    # Verify constraint is present and exact
    constraint_ok = grid.get("constraint") == "Both grids must use validation scores only."
    
    checks["threshold_grid_sensitivity_frozen"] = (
        set(grid.keys()) == exact_grid_keys and
        current_grid_exact and dense_grid_exact and constraint_ok
    )
    
    # Source-project-aware protocol frozen - verify exact ordered list
    protocol = contract["sensitivity_analysis_policy"]["required_dimensions"]["cross_project_validation_design"]["source_project_aware_protocol"]
    expected_protocol = [
        "For each held-out target project and seed:",
        "Use the other four projects as source projects.",
        "Perform four leave-one-source-project-out validation folds.",
        "In each fold, train on three source projects and validate on the fourth.",
        "Generate out-of-fold validation probabilities for every source project.",
        "Concatenate the four out-of-fold validation predictions.",
        "Rank candidates using the aggregated out-of-fold validation objective.",
        "Select candidate or ensemble membership from aggregated source-only validation evidence.",
        "Select the threshold using only aggregated source-only out-of-fold validation predictions.",
        "Refit frozen selected candidate(s) on all four source projects.",
        "Evaluate once on the held-out target project.",
        "Never use the target project for candidate selection, membership selection, threshold selection, or sensitivity choice."
    ]
    checks["source_project_aware_protocol_frozen"] = protocol == expected_protocol
    
    # Sensitivity policy passed
    checks["sensitivity_policy_passed"] = (
        checks["balanced_weight_sensitivity_frozen"] and
        checks["threshold_grid_sensitivity_frozen"] and
        checks["source_project_aware_protocol_frozen"]
    )
    
    # Threats mapping passed - require exact four validity categories, exact threat names, exact record counts, and non-empty fields
    threats = contract["threats_to_validity"]
    exact_categories = {"internal_validity", "construct_validity", "external_validity", "conclusion_validity"}
    exact_threat_keys = {"threat", "possible_impact", "current_mitigation", "remaining_limitation", "planned_computational_response"}
    
    internal_threats = {t["threat"] for t in threats["internal_validity"]}
    construct_threats = {t["threat"] for t in threats["construct_validity"]}
    external_threats = {t["threat"] for t in threats["external_validity"]}
    conclusion_threats = {t["threat"] for t in threats["conclusion_validity"]}
    
    required_internal = {"Leakage", "Preprocessing fitted outside training", "Nondeterminism", "Tie handling", "Threshold-selection mismatch", "Post-hoc analytical choices"}
    required_construct = {"Metric disagreement", "Threshold dependence", "Top-k budget dependence", "Calibration versus discrimination", "Oracle interpretation"}
    required_external = {"Only five NASA/PROMISE projects", "Static metrics only", "Older public benchmark data", "Compact learner pool", "No industrial deployment evaluation"}
    required_conclusion = {"Five independent projects", "Repeated seeds are nested", "Low power", "Multiple metrics", "Descriptive versus inferential distinction", "Sensitivity to objective weights and validation design"}
    
    # Verify exact record counts
    exact_counts = (
        len(threats["internal_validity"]) == 6 and
        len(threats["construct_validity"]) == 5 and
        len(threats["external_validity"]) == 5 and
        len(threats["conclusion_validity"]) == 6
    )
    
    # Verify all threats have exact key set and non-empty string values
    all_threats_complete = True
    for category in ["internal_validity", "construct_validity", "external_validity", "conclusion_validity"]:
        for threat in threats[category]:
            if set(threat.keys()) != exact_threat_keys:
                all_threats_complete = False
                break
            for key in exact_threat_keys:
                if not threat.get(key) or not str(threat[key]).strip():
                    all_threats_complete = False
                    break
        if not all_threats_complete:
            break
    
    # Reject duplicate threat names
    all_unique = (
        len(internal_threats) == 6 and
        len(construct_threats) == 5 and
        len(external_threats) == 5 and
        len(conclusion_threats) == 6
    )
    
    checks["threats_mapping_passed"] = (
        set(threats.keys()) == exact_categories and
        internal_threats == required_internal and
        construct_threats == required_construct and
        external_threats == required_external and
        conclusion_threats == required_conclusion and
        exact_counts and
        all_threats_complete and
        all_unique
    )
    
    # Reviewer context complete - validate exact three reviewer-context arrays
    rc = contract["reviewer_context"]
    exact_reviewer_1_focus = [
        "Practical explanation of evaluation metrics.",
        "Key findings before detailed result tables.",
        "Reproducible workflow diagram."
    ]
    exact_reviewer_2_focus = [
        "Methodological decisions require clearer justification.",
        "Threats to validity require deeper analysis.",
        "Limitations and future directions must be evidence-based."
    ]
    exact_reviewer_3_focus = [
        "Validation-based model selection is standard.",
        "Averaging top models is standard.",
        "Repeated seeds and leakage control are good practice, not algorithmic novelty.",
        "The paper should be treated as a careful empirical study rather than a new fundamental algorithm."
    ]
    checks["reviewer_context_complete"] = (
        set(rc.keys()) == {"reviewer_1_focus", "reviewer_2_focus", "reviewer_3_focus"} and
        rc["reviewer_1_focus"] == exact_reviewer_1_focus and
        rc["reviewer_2_focus"] == exact_reviewer_2_focus and
        rc["reviewer_3_focus"] == exact_reviewer_3_focus
    )
    
    # Reviewer traceability passed - validate reviewer_coverage_evidence itself
    expected_reviewer_keys = {
        "reviewer_1_comment_1", "reviewer_1_comment_2", "reviewer_1_comment_3",
        "reviewer_2_comment_1", "reviewer_2_comment_2", "reviewer_2_comment_3",
        "reviewer_2_comment_4", "reviewer_2_comment_5", "reviewer_2_comment_6",
        "reviewer_2_comment_7", "reviewer_3_novelty_concern"
    }
    actual_keys = set(contract["reviewer_traceability_matrix"].keys())
    
    # Validate reviewer_coverage_evidence exact key set and values
    rce = contract["reviewer_coverage_evidence"]
    exact_rce_keys = {"reviewer_1_comment_count", "reviewer_2_comment_count", "reviewer_3_concern_count", "covered_comment_count", "coverage_identifiers"}
    exact_identifiers = [
        "reviewer_1_comment_1", "reviewer_1_comment_2", "reviewer_1_comment_3",
        "reviewer_2_comment_1", "reviewer_2_comment_2", "reviewer_2_comment_3",
        "reviewer_2_comment_4", "reviewer_2_comment_5", "reviewer_2_comment_6",
        "reviewer_2_comment_7", "reviewer_3_novelty_concern"
    ]
    
    # Verify each covered item has a non-empty response
    all_responses_nonempty = True
    for key in expected_reviewer_keys:
        if key in contract["reviewer_traceability_matrix"]:
            response = contract["reviewer_traceability_matrix"][key]
            comp_resp = response.get("computational_response")
            manus_resp = response.get("manuscript_response")
            sci_resp = response.get("scientific_response")
            if not comp_resp and not manus_resp and not sci_resp:
                all_responses_nonempty = False
                break
    
    checks["reviewer_traceability_passed"] = (
        set(rce.keys()) == exact_rce_keys and
        rce["reviewer_1_comment_count"] == 3 and
        rce["reviewer_2_comment_count"] == 7 and
        rce["reviewer_3_concern_count"] == 1 and
        rce["covered_comment_count"] == 11 and
        rce["coverage_identifiers"] == exact_identifiers and
        actual_keys == expected_reviewer_keys and
        len(actual_keys) == 11 and
        all_responses_nonempty
    )
    
    # Exact roadmap stages
    expected_roadmap = [
        "Part 3A: Scientific analysis contract",
        "Part 3B: Prediction ledger and split/leakage audit",
        "Part 3C: Objective-matched candidate and adaptive evaluation",
        "Part 3D: Post-hoc regret and oracle-gap analysis",
        "Part 3E: Ensemble-size and component ablation",
        "Part 3F: Methodological sensitivity analyses",
        "Part 3G: Project-level paired effects and uncertainty",
        "Part 3H: Workflow diagram and metric dictionary",
        "Part 4: Final full rerun, deterministic artifact freeze, package rebuild, and canonical manifest"
    ]
    checks["roadmap_passed"] = contract["remaining_stage_roadmap"] == expected_roadmap
    
    # Prohibited claims list present - validate exact ordered list of twelve claims
    exact_prohibited_claims = [
        "No method universally dominates all others across all metrics, projects, and settings.",
        "Validation-based selection guarantees superior test performance.",
        "Soft ensembles always outperform fixed candidates.",
        "Adaptive Top-1 selection is always better than fixed baselines.",
        "The oracle reference is a deployable model.",
        "The five projects are a representative sample of all software projects.",
        "The results generalize to industrial deployment without further validation.",
        "Statistical significance tests with n=5 projects provide definitive population-level evidence.",
        "Metric choice is arbitrary and does not affect conclusions.",
        "Threshold policy choice is arbitrary and does not affect conclusions.",
        "Validation-test agreement is a proof of validity.",
        "Post-hoc regret analysis is a validation procedure."
    ]
    checks["prohibited_claims_passed"] = contract["prohibited_claims"] == exact_prohibited_claims
    
    # Stage gate passed - validate exact key set, exact values, and exact constraint
    stage_gate = contract["stage_gate"]
    exact_stage_gate_keys = {"part3a_contract_frozen", "model_rerun_performed", "canonical_outputs_modified", "manuscript_modified", "next_authorized_stage", "part3b_constraint"}
    exact_constraint = "Part 3B cannot alter the current 400 canonical result rows or current canonical manuscript tables unless a later explicitly approved migration stage is created."
    checks["stage_gate_passed"] = (
        set(stage_gate.keys()) == exact_stage_gate_keys and
        stage_gate["next_authorized_stage"] == "Part 3B" and
        stage_gate["model_rerun_performed"] == False and
        stage_gate["canonical_outputs_modified"] == False and
        stage_gate["manuscript_modified"] == False and
        stage_gate["part3b_constraint"] == exact_constraint
    )
    
    # Combine all checks except all_checks_passed itself - exactly 32 required checks
    required_checks = [
        "exact_research_questions_passed", "analysis_domains_passed", "candidate_metadata_matches_current_pipeline",
        "metric_taxonomy_passed", "metric_direction_passed", "metric_count_is_14",
        "metric_threshold_dependency_passed", "metric_inspection_budget_dependency_passed",
        "metric_primary_secondary_passed", "objective_policy_passed", "existing_soft_top3_policy_passed",
        "baseline_policy_passed", "adaptive_policy_passed", "ensemble_policy_passed",
        "tie_policy_passed", "oracle_policy_passed", "unit_of_analysis_policy_passed",
        "statistical_reporting_policy_passed", "agreement_policy_passed", "balanced_weight_sensitivity_frozen",
        "threshold_grid_sensitivity_frozen", "source_project_aware_protocol_frozen",
        "sensitivity_policy_passed", "threats_mapping_passed", "reviewer_context_complete",
        "reviewer_traceability_passed", "roadmap_passed", "prohibited_claims_passed", "stage_gate_passed",
        "preservation_checks_passed", "deterministic_serialization_passed"
    ]
    
    # Note: preservation_checks_passed and deterministic_serialization_passed will be set after serialization
    # They are initialized to False here and updated later
    checks["preservation_checks_passed"] = False
    checks["deterministic_serialization_passed"] = False
    
    all_passed = all(checks[check] for check in required_checks if check in checks)
    checks["all_checks_passed"] = all_passed
    
    return checks


def serialize_json(contract: Dict[str, Any], repo_root: Path) -> tuple:
    """Serialize JSON twice and return content and SHA-256."""
    # First serialization
    json_str_1 = json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
    json_str_1 = json_str_1.rstrip('\n') + '\n'
    sha_1 = hashlib.sha256(json_str_1.encode('utf-8')).hexdigest()
    
    # Second serialization (should be byte-identical)
    json_str_2 = json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
    json_str_2 = json_str_2.rstrip('\n') + '\n'
    sha_2 = hashlib.sha256(json_str_2.encode('utf-8')).hexdigest()
    
    return json_str_1, sha_1, json_str_2, sha_2, json_str_1 == json_str_2


def render_markdown(contract: Dict[str, Any]) -> tuple:
    """Render Markdown twice and return content and SHA-256."""
    
    md_lines = [
        "# Scientific Analysis Contract for Major Revision",
        "",
        f"**Contract Version:** {contract['contract_version']}",
        f"**Starting Commit:** {contract['starting_commit']}",
        f"**Repository:** {contract['repository']}",
        f"**Branch:** {contract['branch']}",
        "",
        "## Scientific Positioning",
        "",
        contract['scientific_positioning']['positioning_statement'],
        "",
        "### Key Assertions",
        ""
    ]
    
    for assertion in contract['scientific_positioning']['key_assertions']:
        md_lines.append(f"- {assertion}")
    
    md_lines.extend([
        "",
        "## Reviewer Context",
        "",
        "### Reviewer 1 Focus",
        ""
    ])
    
    for focus in contract['reviewer_context']['reviewer_1_focus']:
        md_lines.append(f"- {focus}")
    
    md_lines.extend([
        "",
        "### Reviewer 2 Focus",
        ""
    ])
    
    for focus in contract['reviewer_context']['reviewer_2_focus']:
        md_lines.append(f"- {focus}")
    
    md_lines.extend([
        "",
        "### Reviewer 3 Focus",
        ""
    ])
    
    for focus in contract['reviewer_context']['reviewer_3_focus']:
        md_lines.append(f"- {focus}")
    
    md_lines.extend([
        "",
        "## Research Questions",
        "",
        f"**Total Research Questions:** {contract['research_questions']['count']}",
        ""
    ])
    
    for rq_key in ['rq1', 'rq2', 'rq3', 'rq4']:
        rq = contract['research_questions'][rq_key]
        md_lines.extend([
            f"### {rq['title']}",
            "",
            f"**Exact Intent:** {rq['exact_intent']}",
            ""
        ])
        
        if 'requirements' in rq:
            md_lines.append("**Requirements:**")
            md_lines.append("")
            for req in rq['requirements']:
                md_lines.append(f"- {req}")
        
        if 'required_analyses' in rq:
            md_lines.append("**Required Analyses:**")
            md_lines.append("")
            for analysis in rq['required_analyses']:
                md_lines.append(f"- {analysis}")
        
        md_lines.append("")
    
    md_lines.extend([
        "## Analysis Domains",
        "",
        "### Experiments",
        ""
    ])
    
    for exp in contract['analysis_domains']['experiments']:
        md_lines.append(f"- {exp}")
    
    md_lines.extend([
        "",
        "### Projects",
        ""
    ])
    
    for proj in contract['analysis_domains']['projects']:
        md_lines.append(f"- {proj}")
    
    md_lines.extend([
        "",
        "### Seeds",
        ""
    ])
    
    for seed in contract['analysis_domains']['seeds']:
        md_lines.append(f"- {seed}")
    
    md_lines.extend([
        "",
        "### Fixed Candidate Learners",
        ""
    ])
    
    for learner in contract['analysis_domains']['fixed_candidate_learners']:
        md_lines.append(f"- {learner}")
    
    md_lines.extend([
        "",
        "### Existing Adaptive Models",
        ""
    ])
    
    for model in contract['analysis_domains']['existing_adaptive_models']:
        md_lines.append(f"- {model}")
    
    md_lines.extend([
        "",
        "### Planned Additional Ensemble Models",
        ""
    ])
    
    for model in contract['analysis_domains']['planned_additional_ensemble_models']:
        md_lines.append(f"- {model}")
    
    md_lines.extend([
        "",
        "### Concept Distinctions",
        ""
    ])
    
    for distinction in contract['analysis_domains']['concept_distinctions']:
        md_lines.append(f"- {distinction}")
    
    md_lines.extend([
        "",
        "## Candidate Learner Configuration",
        ""
    ])
    
    for learner_name, learner_config in contract['candidate_learners'].items():
        md_lines.extend([
            f"### {learner_name}",
            ""
        ])
        for key, value in learner_config.items():
            md_lines.append(f"- {key}: {value}")
        md_lines.append("")
    
    md_lines.extend([
        "",
        "## Existing Adaptive-Model Policies",
        ""
    ])
    
    for model_name, model_config in contract['existing_adaptive_models'].items():
        md_lines.extend([
            f"### {model_name}",
            ""
        ])
        for key, value in model_config.items():
            md_lines.append(f"- {key}: {value}")
        md_lines.append("")
    
    md_lines.extend([
        "",
        "## Planned Ensemble Policies",
        ""
    ])
    
    for model_name, model_config in contract['planned_models'].items():
        md_lines.extend([
            f"### {model_name}",
            ""
        ])
        for key, value in model_config.items():
            md_lines.append(f"- {key}: {value}")
        md_lines.append("")
    
    md_lines.extend([
        "",
        "## Metric Taxonomy",
        ""
    ])
    
    for family_name, family in contract['metric_taxonomy'].items():
        md_lines.extend([
            f"### {family_name.replace('_', ' ').title()}",
            ""
        ])
        
        for metric_name, metric_info in family.items():
            md_lines.extend([
                f"**{metric_info['display_name']} ({metric_name})**",
                "",
                f"- Direction: {metric_info['direction']}",
                f"- Primary/Secondary: {metric_info['primary_or_secondary']}",
                f"- Threshold Dependent: {metric_info['threshold_dependent']}",
                f"- Practical Interpretation: {metric_info['practical_interpretation']}",
                ""
            ])
    
    md_lines.extend([
        "## Objective-Matched Comparison Policy",
        ""
    ])
    
    for policy_name, policy in contract['objective_policies'].items():
        if policy_name == "policy_mismatch_prohibition":
            md_lines.extend([
                "### Policy-Mismatch Prohibition",
                ""
            ])
            for prohibition in policy:
                md_lines.append(f"- {prohibition}")
            md_lines.append("")
        else:
            md_lines.extend([
                f"### {policy_name.replace('_', ' ').title()}",
                "",
                f"{policy.get('description', '')}",
                ""
            ])
    
    md_lines.extend([
        "## Fixed Baseline Policy",
        "",
        "### Individual Fixed Baselines",
        ""
    ])
    
    for baseline in contract['baseline_policy']['individual_fixed_baselines']:
        md_lines.append(f"- {baseline}")
    
    md_lines.extend([
        "",
        "### Best Fixed Baseline",
        "",
        "**Selection Rules:**",
        ""
    ])
    
    for rule in contract['baseline_policy']['best_fixed_baseline']['selection_rules']:
        md_lines.append(f"- {rule}")
    
    md_lines.extend([
        "",
        f"**Status:** {contract['baseline_policy']['best_fixed_baseline']['status']}",
        "",
        f"**Warning:** {contract['baseline_policy']['best_fixed_baseline']['deployment_warning']}",
        ""
    ])
    
    md_lines.extend([
        "## Adaptive Top-1 Policy",
        "",
        "### Definition",
        ""
    ])
    
    for step in contract['adaptive_top1_policy']['definition']:
        md_lines.append(f"- {step}")
    
    md_lines.extend([
        "",
        "### Distinguished Components",
        ""
    ])
    
    for component in contract['adaptive_top1_policy']['distinguished_components']:
        md_lines.append(f"- {component}")
    
    md_lines.extend([
        "",
        f"**Prohibition:** {contract['adaptive_top1_policy']['prohibition']}",
        ""
    ])
    
    md_lines.extend([
        "## Soft Ensemble Policy",
        "",
        "### Definition",
        ""
    ])
    
    for step in contract['soft_ensemble_policy']['definition']:
        md_lines.append(f"- {step}")
    
    md_lines.extend([
        "",
        f"**Planned k Values:** {contract['soft_ensemble_policy']['planned_k_values']}",
        "",
        f"**Note:** {contract['soft_ensemble_policy']['soft_all_4_note']}",
        "",
        "### Key Assertions",
        ""
    ])
    
    for assertion in contract['soft_ensemble_policy']['key_assertions']:
        md_lines.append(f"- {assertion}")
    
    md_lines.extend([
        "",
        "## Tie Policy",
        "",
        "### Validation Candidate Ranking",
        ""
    ])
    
    for rule in contract['tie_policy']['validation_candidate_ranking']:
        md_lines.append(f"- {rule}")
    
    md_lines.extend([
        "",
        "### Distinguished Concepts",
        ""
    ])
    
    for concept in contract['tie_policy']['distinguished_concepts']:
        md_lines.append(f"- {concept}")
    
    md_lines.extend([
        "",
        f"**Scientific Analysis Rule:** {contract['tie_policy']['scientific_analysis_rule']}",
        ""
    ])
    
    md_lines.extend([
        "## Oracle and Regret Policy",
        "",
        f"**Oracle Definition:** {contract['oracle_and_regret_policy']['oracle_definition']}",
        "",
        "### Oracle Computation",
        ""
    ])
    
    for metric_type, formula in contract['oracle_and_regret_policy']['oracle_computation'].items():
        md_lines.append(f"- {metric_type}: {formula}")
    
    md_lines.extend([
        "",
        "### Absolute Regret",
        ""
    ])
    
    for metric_type, formula in contract['oracle_and_regret_policy']['absolute_regret'].items():
        md_lines.append(f"- {metric_type}: {formula}")
    
    md_lines.extend([
        "",
        f"**Property:** {contract['oracle_and_regret_policy']['regret_property']}",
        "",
        f"**Normalized Regret Formula:** {contract['oracle_and_regret_policy']['normalized_regret_formula']}",
        "",
        "### Separate Records",
        ""
    ])
    
    for record in contract['oracle_and_regret_policy']['separate_records']:
        md_lines.append(f"- {record}")
    
    md_lines.extend([
        "",
        "### Key Assertions",
        ""
    ])
    
    for assertion in contract['oracle_and_regret_policy']['key_assertions']:
        md_lines.append(f"- {assertion}")
    
    md_lines.extend([
        "",
        "## Unit of Analysis",
        "",
        f"**Primary Independent Unit:** {contract['unit_of_analysis_policy']['primary_independent_unit']}",
        "",
        "### Repeated Seed",
        ""
    ])
    
    md_lines.append(f"- Definition: {contract['unit_of_analysis_policy']['repeated_seed']['definition']}")
    md_lines.append("- Not:")
    
    for not_item in contract['unit_of_analysis_policy']['repeated_seed']['not']:
        md_lines.append(f"  - {not_item}")
    
    md_lines.extend([
        "",
        "### Run-Level Observations May Be Used For",
        ""
    ])
    
    for use in contract['unit_of_analysis_policy']['run_level_observations_may_be_used_for']:
        md_lines.append(f"- {use}")
    
    md_lines.extend([
        "",
        "### Run-Level Observations Must Not Be Used For",
        ""
    ])
    
    for not_use in contract['unit_of_analysis_policy']['run_level_observations_must_not_be_used_for']:
        md_lines.append(f"- {not_use}")
    
    md_lines.extend([
        "",
        "### Project-Level Paired Summaries",
        ""
    ])
    
    for step in contract['unit_of_analysis_policy']['project_level_paired_summaries']:
        md_lines.append(f"- {step}")
    
    md_lines.extend([
        "",
        "### Prohibitions",
        ""
    ])
    
    for prohibition in contract['unit_of_analysis_policy']['prohibitions']:
        md_lines.append(f"- {prohibition}")
    
    md_lines.extend([
        "",
        "## Statistical Reporting",
        "",
        "### Required Descriptive Reporting",
        ""
    ])
    
    for item in contract['statistical_reporting_policy']['required_descriptive_reporting']:
        md_lines.append(f"- {item}")
    
    md_lines.extend([
        "",
        "### Permitted Exploratory Inference",
        ""
    ])
    
    for item in contract['statistical_reporting_policy']['permitted_exploratory_inference']:
        md_lines.append(f"- {item}")
    
    md_lines.extend([
        "",
        "### Effect Reporting",
        ""
    ])
    
    for item in contract['statistical_reporting_policy']['effect_reporting']:
        md_lines.append(f"- {item}")
    
    md_lines.extend([
        "",
        "### Key Assertions",
        ""
    ])
    
    for assertion in contract['statistical_reporting_policy']['key_assertions']:
        md_lines.append(f"- {assertion}")
    
    md_lines.extend([
        "",
        "## Validation-Test Agreement",
        "",
        "### Required Agreement Analyses",
        ""
    ])
    
    for analysis in contract['validation_test_agreement_policy']['required_agreement_analyses']:
        md_lines.append(f"- {analysis}")
    
    md_lines.extend([
        "",
        "### Explicit Statements",
        ""
    ])
    
    for statement in contract['validation_test_agreement_policy']['explicit_statements']:
        md_lines.append(f"- {statement}")
    
    md_lines.extend([
        "",
        "## Sensitivity Analyses",
        "",
        "### Required Dimensions",
        ""
    ])
    
    for dim_name, dim_info in contract['sensitivity_analysis_policy']['required_dimensions'].items():
        md_lines.extend([
            f"**{dim_name.replace('_', ' ').title()}**",
            ""
        ])
        if dim_name == "balanced_objective_weights":
            for profile_name, profile_weights in dim_info.items():
                if profile_name != "constraints":
                    md_lines.extend([
                        f"### {profile_name.replace('_', ' ').title()}",
                        ""
                    ])
                    for metric, weight in profile_weights.items():
                        md_lines.append(f"- {metric}: {weight}")
                    md_lines.append("")
            if "constraints" in dim_info:
                md_lines.extend([
                    "### Constraints",
                    ""
                ])
                for constraint in dim_info["constraints"]:
                    md_lines.append(f"- {constraint}")
                md_lines.append("")
        elif dim_name == "threshold_grid":
            for grid_name, grid_config in dim_info.items():
                if grid_name != "constraint":
                    md_lines.extend([
                        f"### {grid_name.replace('_', ' ').title()}",
                        ""
                    ])
                    for key, value in grid_config.items():
                        md_lines.append(f"- {key}: {value}")
                    md_lines.append("")
            if "constraint" in dim_info:
                md_lines.append(f"- Constraint: {dim_info['constraint']}")
                md_lines.append("")
        elif dim_name == "cross_project_validation_design":
            if "source_project_aware_protocol" in dim_info:
                md_lines.extend([
                    "### Source-Project-Aware Protocol",
                    ""
                ])
                for step in dim_info["source_project_aware_protocol"]:
                    md_lines.append(f"- {step}")
                md_lines.append("")
        else:
            md_lines.append(f"- {dim_info.get('description', '')}")
            md_lines.append("")
    
    md_lines.extend([
        "### Optional After Required",
        ""
    ])
    
    for optional in contract['sensitivity_analysis_policy']['optional_after_required']:
        md_lines.append(f"- {optional}")
    
    md_lines.extend([
        "",
        f"**Dataset Change Policy:** {contract['sensitivity_analysis_policy']['dataset_change_policy']}",
        ""
    ])
    
    md_lines.extend([
        "## Threats to Validity",
        ""
    ])
    
    for validity_type, threats in contract['threats_to_validity'].items():
        md_lines.extend([
            f"### {validity_type.replace('_', ' ').title()}",
            ""
        ])
        
        for threat in threats:
            md_lines.extend([
                f"**Threat:** {threat['threat']}",
                "",
                f"- Possible Impact: {threat['possible_impact']}",
                f"- Current Mitigation: {threat['current_mitigation']}",
                f"- Remaining Limitation: {threat['remaining_limitation']}",
                f"- Planned Computational Response: {threat['planned_computational_response']}",
                ""
            ])
    
    md_lines.extend([
        "## Reviewer Coverage Evidence",
        ""
    ])
    
    if 'reviewer_coverage_evidence' in contract:
        rce = contract['reviewer_coverage_evidence']
        md_lines.append(f"- Reviewer 1 Comment Count: {rce['reviewer_1_comment_count']}")
        md_lines.append(f"- Reviewer 2 Comment Count: {rce['reviewer_2_comment_count']}")
        md_lines.append(f"- Reviewer 3 Concern Count: {rce['reviewer_3_concern_count']}")
        md_lines.append(f"- Covered Comment Count: {rce['covered_comment_count']}")
        md_lines.append("")
        md_lines.append("**Coverage Identifiers:**")
        md_lines.append("")
        for identifier in rce['coverage_identifiers']:
            md_lines.append(f"- {identifier}")
        md_lines.append("")
    
    md_lines.extend([
        "## Reviewer Traceability Matrix",
        ""
    ])
    
    for comment_key, response in contract['reviewer_traceability_matrix'].items():
        md_lines.extend([
            f"### {comment_key.replace('_', ' ').title()}",
            "",
            "**Computational Response:**",
            ""
        ])
        
        comp_response = response['computational_response']
        if isinstance(comp_response, list):
            for item in comp_response:
                md_lines.append(f"- {item}")
        else:
            md_lines.append(f"- {comp_response}")
        md_lines.append("")
        
        if 'manuscript_response' in response:
            md_lines.append("**Manuscript Response:**")
            md_lines.append("")
            md_lines.append(f"- {response['manuscript_response']}")
            md_lines.append("")
        
        if 'scientific_response' in response:
            md_lines.append("**Scientific Response:**")
            md_lines.append("")
            md_lines.append(f"- {response['scientific_response']}")
            md_lines.append("")
    
    md_lines.extend([
        "## Remaining Computational Roadmap",
        ""
    ])
    
    for stage in contract['remaining_stage_roadmap']:
        md_lines.append(f"- {stage}")
    
    md_lines.extend([
        "",
        "## Prohibited Claims",
        ""
    ])
    
    for claim in contract['prohibited_claims']:
        md_lines.append(f"- {claim}")
    
    md_lines.extend([
        "",
        "## Stage Gate",
        "",
        f"- Part 3A Contract Frozen: {contract['stage_gate']['part3a_contract_frozen']}",
        f"- Model Rerun Performed: {contract['stage_gate']['model_rerun_performed']}",
        f"- Canonical Outputs Modified: {contract['stage_gate']['canonical_outputs_modified']}",
        f"- Manuscript Modified: {contract['stage_gate']['manuscript_modified']}",
        f"- Next Authorized Stage: {contract['stage_gate']['next_authorized_stage']}",
        "",
        f"**Part 3B Constraint:** {contract['stage_gate']['part3b_constraint']}",
        ""
    ])
    
    md_lines.extend([
        "## Validation Checks",
        ""
    ])
    
    for check_name, check_result in contract['validation_checks'].items():
        md_lines.append(f"- {check_name}: {check_result}")
    
    md_lines.append("")
    
    md_lines.extend([
        "## Preservation Checks",
        ""
    ])
    
    md_lines.append(f"- Files Checked: {contract['preservation_checks']['files_checked']}")
    md_lines.append(f"- Files Changed: {contract['preservation_checks']['files_changed']}")
    md_lines.append(f"- All Preserved: {contract['preservation_checks']['all_preserved']}")
    md_lines.append(f"- Preservation Checks Passed: {contract['preservation_checks']['preservation_checks_passed']}")
    md_lines.append("")
    
    md_lines.extend([
        "### File Evidence",
        ""
    ])
    
    for file_path, evidence in contract['preservation_checks']['file_evidence'].items():
        md_lines.extend([
            f"**{file_path}**",
            ""
        ])
        md_lines.append(f"- Expected SHA-256: {evidence['expected_sha256']}")
        md_lines.append(f"- Before SHA-256: {evidence['before_sha256']}")
        md_lines.append(f"- After SHA-256: {evidence['after_sha256']}")
        md_lines.append(f"- Exists Before: {evidence['exists_before']}")
        md_lines.append(f"- Exists After: {evidence['exists_after']}")
        md_lines.append(f"- Matches Expected Before: {evidence['matches_expected_before']}")
        md_lines.append(f"- Matches Expected After: {evidence['matches_expected_after']}")
        md_lines.append(f"- Unchanged During Execution: {evidence['unchanged_during_execution']}")
        md_lines.append("")
    
    md_lines.extend([
        "## Serialization Validation",
        ""
    ])
    
    if 'serialization_evidence' in contract:
        se = contract['serialization_evidence']
        md_lines.append(f"- JSON Double Render Required: {se['json_double_render_required']}")
        md_lines.append(f"- Markdown Double Render Required: {se['markdown_double_render_required']}")
        md_lines.append(f"- Exact Written Byte Verification Required: {se['exact_written_byte_verification_required']}")
        md_lines.append(f"- Written SHA-256 Reported Externally: {se['written_sha256_reported_externally']}")
        md_lines.append(f"- Self-Referential Hashes Embedded: {se['self_referential_hashes_embedded']}")
        md_lines.append("")
    
    md_lines.append("")
    
    # First rendering
    md_str_1 = '\n'.join(md_lines)
    md_str_1 = md_str_1.rstrip('\n') + '\n'
    sha_1 = hashlib.sha256(md_str_1.encode('utf-8')).hexdigest()
    
    # Second rendering (should be byte-identical)
    md_str_2 = '\n'.join(md_lines)
    md_str_2 = md_str_2.rstrip('\n') + '\n'
    sha_2 = hashlib.sha256(md_str_2.encode('utf-8')).hexdigest()
    
    return md_str_1, sha_1, md_str_2, sha_2, md_str_1 == md_str_2


def snapshot_preserved_files(repo_root: Path) -> Dict[str, Any]:
    """Perform one independent filesystem snapshot of preserved files."""
    
    expected_hashes = {
        "scripts/run_repeated_evaluation.py": "d385b6ecef2427c85299dcbc50cfff919fa8546b31829fa3ce0e5fdb307c4856",
        "scripts/make_manuscript_tables.py": "152f4568025420bf8aff780e2f9c104abb6e00a4373635277d14483e67dcdbb2",
        "results/part1_full_reproduction/repeated_all_results.csv": "76b430031a944708af661bee1a1355619d1e0e6f49b932d462cea421aeb01160",
        "results/part1_full_reproduction/validation_log.csv": "d18dbb6b7a71f356203aa34fe41ab7d531daa1f8499fc06d06ab643b088f0272",
        "results/part1_full_reproduction/repeated_summary_mean_std.csv": "b6f27ee32e350e23899d451fe4ab0758a76944633873f018bdac9ce16b94ae5b",
        "results/part1_full_reproduction_tables/table_within_project_mean_sd.csv": "cccaeb1553ac942dbe26f33673a3683ea181f06a4cf4ceb2466f0c3556086160",
        "results/part1_full_reproduction_tables/table_cross_project_mean_sd.csv": "1753444c5b8a0c3a34179c644f6998cc663a3eb1da80e81b8fcf6d285e53731c",
        "results/part1_full_reproduction_tables/table_soft_top3_delta_vs_best_baseline.csv": "bf5cac180bf9701299dfd1c1b410224d34b8f32269b49fb8203df7567ff7a60b"
    }
    
    snapshot = {}
    
    for rel_path, expected_sha in expected_hashes.items():
        filepath = repo_root / rel_path
        if filepath.exists():
            actual_sha = compute_sha256(filepath)
            snapshot[rel_path] = {
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "exists": True,
                "matches_expected": (actual_sha == expected_sha)
            }
        else:
            snapshot[rel_path] = {
                "expected_sha256": expected_sha,
                "actual_sha256": None,
                "exists": False,
                "matches_expected": False
            }
    
    return snapshot


def compare_preservation_snapshots(before_snapshot: Dict[str, Any], after_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two independent preservation snapshots."""
    
    preservation = {
        "files_checked": len(before_snapshot),
        "files_changed": 0,
        "all_preserved": True,
        "file_evidence": {}
    }
    
    for rel_path in before_snapshot.keys():
        before = before_snapshot[rel_path]
        after = after_snapshot[rel_path]
        
        evidence = {
            "expected_sha256": before["expected_sha256"],
            "before_sha256": before["actual_sha256"],
            "after_sha256": after["actual_sha256"],
            "exists_before": before["exists"],
            "exists_after": after["exists"],
            "matches_expected_before": before["matches_expected"],
            "matches_expected_after": after["matches_expected"],
            "unchanged_during_execution": (before["actual_sha256"] == after["actual_sha256"])
        }
        
        # Count as changed if any condition is true
        changed = (
            not evidence["exists_before"] or
            not evidence["exists_after"] or
            not evidence["matches_expected_before"] or
            not evidence["matches_expected_after"] or
            not evidence["unchanged_during_execution"]
        )
        
        if changed:
            preservation["files_changed"] += 1
            preservation["all_preserved"] = False
        
        preservation["file_evidence"][rel_path] = evidence
    
    preservation["preservation_checks_passed"] = preservation["all_preserved"]
    
    return preservation


def write_atomically(filepath: Path, content: str) -> None:
    """Write file atomically using temporary file."""
    fd, temp_path = tempfile.mkstemp(dir=filepath.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        os.replace(temp_path, filepath)
    except:
        try:
            os.unlink(temp_path)
        except:
            pass
        raise


def main():
    """Main execution with immutable final state design."""
    repo_root = get_repository_root()
    
    print(f"Repository root: {repo_root}")
    print(f"Starting commit: ec60c38abae80046fa0d345caa817258b97cdbf1")
    print("")
    
    # A. Capture genuine before preservation snapshot
    print("Capturing before preservation snapshot...")
    before_snapshot = snapshot_preserved_files(repo_root)
    
    # B. Build the core scientific contract
    print("Building contract...")
    contract = build_contract()
    
    # C. Capture after preservation snapshot immediately before final-state construction
    print("Capturing after preservation snapshot...")
    after_snapshot = snapshot_preserved_files(repo_root)
    
    # D. Build preservation evidence by comparing independent snapshots
    print("Building preservation evidence...")
    preservation_evidence = compare_preservation_snapshots(before_snapshot, after_snapshot)
    
    # E. Compute every semantic check except deterministic_serialization_passed and stage_gate_passed
    print("Validating contract...")
    validation_results = validate_contract(contract)
    
    # F. Build the scientific core with part3a_contract_frozen initially false
    # G. Capture and compare preservation snapshots (already done)
    # H. Compute preservation_checks_passed
    validation_results["preservation_checks_passed"] = preservation_evidence["preservation_checks_passed"]
    
    # I. Determine pre_gate_passed = logical AND of every required semantic and preservation check except: stage_gate_passed, deterministic_serialization_passed, all_checks_passed
    pre_gate_checks = [
        "exact_research_questions_passed", "analysis_domains_passed", "candidate_metadata_matches_current_pipeline",
        "metric_taxonomy_passed", "metric_direction_passed", "metric_count_is_14",
        "metric_threshold_dependency_passed", "metric_inspection_budget_dependency_passed",
        "metric_primary_secondary_passed", "objective_policy_passed", "existing_soft_top3_policy_passed",
        "baseline_policy_passed", "adaptive_policy_passed", "ensemble_policy_passed",
        "tie_policy_passed", "oracle_policy_passed", "unit_of_analysis_policy_passed",
        "statistical_reporting_policy_passed", "agreement_policy_passed", "balanced_weight_sensitivity_frozen",
        "threshold_grid_sensitivity_frozen", "source_project_aware_protocol_frozen",
        "sensitivity_policy_passed", "threats_mapping_passed", "reviewer_context_complete",
        "reviewer_traceability_passed", "roadmap_passed", "prohibited_claims_passed", "preservation_checks_passed"
    ]
    pre_gate_passed = all(validation_results[check] for check in pre_gate_checks)
    
    # J. Create a deep copy of the core contract using copy.deepcopy
    prospective_final_state = copy.deepcopy(contract)
    prospective_final_state["preservation_checks"] = preservation_evidence
    prospective_final_state["validation_checks"] = validation_results
    
    # K. Set prospective_final_state.stage_gate.part3a_contract_frozen = pre_gate_passed
    prospective_final_state["stage_gate"]["part3a_contract_frozen"] = pre_gate_passed
    
    # L. Compute stage_gate_passed by validating the complete final gate, including part3a_contract_frozen == true and the exact constraint
    # Re-validate stage gate with the updated part3a_contract_frozen value
    exact_stage_gate_keys = {"part3a_contract_frozen", "model_rerun_performed", "canonical_outputs_modified", "manuscript_modified", "next_authorized_stage", "part3b_constraint"}
    exact_constraint = "Part 3B cannot alter the current 400 canonical result rows or current canonical manuscript tables unless a later explicitly approved migration stage is created."
    stage_gate = prospective_final_state["stage_gate"]
    validation_results["stage_gate_passed"] = (
        set(stage_gate.keys()) == exact_stage_gate_keys and
        stage_gate["next_authorized_stage"] == "Part 3B" and
        stage_gate["model_rerun_performed"] == False and
        stage_gate["canonical_outputs_modified"] == False and
        stage_gate["manuscript_modified"] == False and
        stage_gate["part3b_constraint"] == exact_constraint and
        stage_gate["part3a_contract_frozen"] == True
    )
    
    # M. Add deterministic_serialization_passed = true prospectively
    validation_results["deterministic_serialization_passed"] = True
    
    # N. Compute all_checks_passed as the logical AND of checks 1 through 31
    all_validation_checks = [
        "exact_research_questions_passed", "analysis_domains_passed", "candidate_metadata_matches_current_pipeline",
        "metric_taxonomy_passed", "metric_direction_passed", "metric_count_is_14",
        "metric_threshold_dependency_passed", "metric_inspection_budget_dependency_passed",
        "metric_primary_secondary_passed", "objective_policy_passed", "existing_soft_top3_policy_passed",
        "baseline_policy_passed", "adaptive_policy_passed", "ensemble_policy_passed",
        "tie_policy_passed", "oracle_policy_passed", "unit_of_analysis_policy_passed",
        "statistical_reporting_policy_passed", "agreement_policy_passed", "balanced_weight_sensitivity_frozen",
        "threshold_grid_sensitivity_frozen", "source_project_aware_protocol_frozen",
        "sensitivity_policy_passed", "threats_mapping_passed", "reviewer_context_complete",
        "reviewer_traceability_passed", "roadmap_passed", "prohibited_claims_passed", "stage_gate_passed",
        "preservation_checks_passed", "deterministic_serialization_passed"
    ]
    validation_results["all_checks_passed"] = all(validation_results[check] for check in all_validation_checks)
    
    # O. Assert the exact 32-key validation schema before serialization
    exact_required_set = set(all_validation_checks + ["all_checks_passed"])
    assert len(validation_results) == 32, f"Expected 32 validation keys, got {len(validation_results)}"
    assert set(validation_results.keys()) == exact_required_set, f"Validation keys do not match required set"
    assert validation_results["all_checks_passed"] == all(validation_results[check] for check in all_validation_checks), "all_checks_passed does not match logical AND of all checks"
    
    # Update validation_checks in prospective_final_state with final values (BEFORE rendering)
    prospective_final_state["validation_checks"] = validation_results
    
    # Add non-self-referential serialization evidence (before rendering)
    prospective_final_state["serialization_evidence"] = {
        "json_double_render_required": True,
        "markdown_double_render_required": True,
        "exact_written_byte_verification_required": True,
        "written_sha256_reported_externally": True,
        "self_referential_hashes_embedded": False
    }
    
    # P. Render the exact prospective final state twice
    print("Testing JSON double serialization...")
    json_content_1, json_sha_1, json_content_2, json_sha_2, json_identical = serialize_json(prospective_final_state, repo_root)
    
    if not json_identical:
        raise RuntimeError("JSON double serialization failed - not byte-identical")
    
    print("Testing Markdown double rendering...")
    md_content_1, md_sha_1, md_content_2, md_sha_2, md_identical = render_markdown(prospective_final_state)
    
    if not md_identical:
        raise RuntimeError("Markdown double rendering failed - not byte-identical")
    
    # Q. Abort before writing if either double rendering differs (already verified above)
    # R. Treat the successfully double-rendered state as immutable final_state
    
    # K. Write the exact already-compared strings
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = reports_dir / "part3_analysis_contract.json"
    md_path = reports_dir / "part3_analysis_contract.md"
    
    print(f"Writing {json_path}...")
    write_atomically(json_path, json_content_1)
    
    print(f"Writing {md_path}...")
    write_atomically(md_path, md_content_1)
    
    # L. Reread the written bytes and verify their SHA-256 against the rendered bytes
    with open(json_path, 'rb') as f:
        json_verify_bytes = f.read()
    json_verify_sha = hashlib.sha256(json_verify_bytes).hexdigest()
    
    with open(md_path, 'rb') as f:
        md_verify_bytes = f.read()
    md_verify_sha = hashlib.sha256(md_verify_bytes).hexdigest()
    
    if json_verify_sha != json_sha_1:
        raise RuntimeError(f"JSON written-file SHA mismatch: expected {json_sha_1}, got {json_verify_sha}")
    
    if md_verify_sha != md_sha_1:
        raise RuntimeError(f"Markdown written-file SHA mismatch: expected {md_sha_1}, got {md_verify_sha}")
    
    # M. Do not mutate final_state afterward (no further mutations)
    
    print("")
    print("Contract successfully created and validated.")
    print("")
    print("=== Summary ===")
    print(f"JSON SHA-256: {json_sha_1}")
    print(f"Markdown SHA-256: {md_sha_1}")
    print(f"JSON double-serialization identical: {json_identical}")
    print(f"Markdown double-rendering identical: {md_identical}")
    print(f"All validation checks passed: {validation_results['all_checks_passed']}")
    print(f"Files checked for preservation: {preservation_evidence['files_checked']}")
    print(f"Files changed: {preservation_evidence['files_changed']}")
    print(f"All preserved: {preservation_evidence['all_preserved']}")
    print("")
    print("=== Detailed Validation ===")
    for check_name, check_result in validation_results.items():
        print(f"  {check_name}: {check_result}")


if __name__ == "__main__":
    main()
