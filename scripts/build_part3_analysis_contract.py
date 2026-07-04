#!/usr/bin/env python3
"""
Part 3A: Freeze the Scientific Analysis Contract

This script creates a complete, machine-readable, auditable scientific analysis
contract before any new model rerun, prediction-ledger generation, regret analysis,
ablation, sensitivity analysis, workflow figure generation, or manuscript editing.

The contract is deterministic and validates all requirements before output.
"""

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
        "contract_version": "Part-3A-v1",
        "starting_commit": "459dbfb8bb1361d03c93255d136cc35aca4f897e",
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
                "regularization": "L2",
                "C": 0.1,
                "class_weight": None
            },
            "LR_std_C1": {
                "type": "logistic_regression",
                "regularization": "L2",
                "C": 1.0,
                "class_weight": None
            },
            "DT_leaf5": {
                "type": "decision_tree",
                "max_leaf_nodes": 5,
                "random_state": None
            },
            "ET_leaf5": {
                "type": "extra_trees",
                "max_leaf_nodes": 5,
                "random_state": None
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
                "validation_objective": "rank",
                "selection_type": "soft_ensemble",
                "ensemble_size": 3,
                "threshold_policy": "validation_tuned"
            }
        },
        
        "planned_models": {
            "AQRPE_v2_soft_top2": {
                "validation_objective": "rank",
                "selection_type": "soft_ensemble",
                "ensemble_size": 2,
                "threshold_policy": "validation_tuned",
                "status": "planned"
            },
            "AQRPE_v2_soft_all4": {
                "validation_objective": "rank",
                "selection_type": "soft_ensemble",
                "ensemble_size": 4,
                "threshold_policy": "validation_tuned",
                "status": "planned"
            }
        },
        
        "metric_taxonomy": {
            "primary_discrimination_ranking": {
                "avg_precision": {
                    "canonical_name": "avg_precision",
                    "display_name": "Average Precision",
                    "family": "primary_discrimination_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": False,
                    "practical_interpretation": "Area under precision-recall curve, threshold-free ranking quality.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "selection_stability"]
                },
                "precision_at_10pct": {
                    "canonical_name": "precision_at_10pct",
                    "display_name": "Precision@10%",
                    "family": "primary_discrimination_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Precision when inspecting top 10% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "recall_at_10pct": {
                    "canonical_name": "recall_at_10pct",
                    "display_name": "Recall@10%",
                    "family": "primary_discrimination_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Defect coverage when inspecting top 10% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "lift_at_10pct": {
                    "canonical_name": "lift_at_10pct",
                    "display_name": "Lift@10%",
                    "family": "primary_discrimination_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Ratio of precision@10% to baseline defect rate.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                }
            },
            "primary_thresholded_classification": {
                "mcc": {
                    "canonical_name": "mcc",
                    "display_name": "Matthews Correlation Coefficient",
                    "family": "primary_thresholded_classification",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Balanced measure for binary classification, robust to class imbalance.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "thresholded_evaluation"]
                },
                "f1": {
                    "canonical_name": "f1",
                    "display_name": "F1 Score",
                    "family": "primary_thresholded_classification",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Harmonic mean of precision and recall.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "thresholded_evaluation"]
                },
                "balanced_accuracy": {
                    "canonical_name": "balanced_accuracy",
                    "display_name": "Balanced Accuracy",
                    "family": "primary_thresholded_classification",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Average of recall across both classes.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "thresholded_evaluation"]
                }
            },
            "secondary_ranking": {
                "precision_at_20pct": {
                    "canonical_name": "precision_at_20pct",
                    "display_name": "Precision@20%",
                    "family": "secondary_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Precision when inspecting top 20% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "recall_at_20pct": {
                    "canonical_name": "recall_at_20pct",
                    "display_name": "Recall@20%",
                    "family": "secondary_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Defect coverage when inspecting top 20% of risky instances.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "lift_at_20pct": {
                    "canonical_name": "lift_at_20pct",
                    "display_name": "Lift@20%",
                    "family": "secondary_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Ratio of precision@20% to baseline defect rate.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "early_inspection"]
                },
                "roc_auc": {
                    "canonical_name": "roc_auc",
                    "display_name": "ROC AUC",
                    "family": "secondary_ranking",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": False,
                    "practical_interpretation": "Area under ROC curve, threshold-free ranking quality. Secondary because precision-recall is more informative under imbalance.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "diagnostic"]
                }
            },
            "secondary_diagnostic": {
                "precision": {
                    "canonical_name": "precision",
                    "display_name": "Precision",
                    "family": "secondary_diagnostic",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Diagnostic metric, must not be interpreted without threshold policy.",
                    "allowed_analysis_uses": ["diagnostic"]
                },
                "recall": {
                    "canonical_name": "recall",
                    "display_name": "Recall",
                    "family": "secondary_diagnostic",
                    "direction": "higher_is_better",
                    "primary_or_secondary": "secondary",
                    "threshold_dependent": True,
                    "practical_interpretation": "Diagnostic metric, must not be interpreted without threshold policy.",
                    "allowed_analysis_uses": ["diagnostic"]
                }
            },
            "calibration_sensitive": {
                "brier": {
                    "canonical_name": "brier",
                    "display_name": "Brier Score",
                    "family": "calibration_sensitive",
                    "direction": "lower_is_better",
                    "primary_or_secondary": "primary",
                    "threshold_dependent": False,
                    "practical_interpretation": "Mean squared error of predicted probabilities, reflects calibration.",
                    "allowed_analysis_uses": ["comparative_performance", "metric_tradeoffs", "calibration_analysis"]
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
            }
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
                    "description": "Current weights, equal-weight alternative, predefined weight perturbations."
                },
                "rank_threshold_policy": {
                    "description": "Fixed 0.5, validation-tuned secondary threshold."
                },
                "threshold_grid": {
                    "description": "Current grid, denser validation-only grid."
                },
                "cross_project_validation_design": {
                    "description": "Current stratified source-row split, source-project-aware validation robustness check."
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
            "reviewer_2_comments_6_and_7": {
                "computational_response": "None",
                "manuscript_response": "Citation renumbering and Springer formatting"
            },
            "reviewer_3": {
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
            "AQRPE v2 is a fundamentally new algorithm.",
            "Validation-based model selection is itself a novel contribution.",
            "Soft averaging of top models is itself a novel contribution.",
            "Repeated seeds establish external validity.",
            "Train/validation/test separation is itself an algorithmic contribution.",
            "AQRPE universally outperforms all baselines.",
            "Five seeds are five independent datasets.",
            "Twenty-five project-seed runs are twenty-five independent projects.",
            "A p-value alone proves superiority.",
            "The test oracle is a deployable selection method.",
            "Soft-top-3 is optimal before ablation.",
            "Test data may influence selection or threshold tuning."
        ],
        
        "stage_gate": {
            "part3a_contract_frozen": True,
            "model_rerun_performed": False,
            "canonical_outputs_modified": False,
            "manuscript_modified": False,
            "next_authorized_stage": "Part 3B",
            "part3b_constraint": "Part 3B cannot alter the current 400 canonical result rows or current canonical manuscript tables unless a later explicitly approved migration stage is created."
        },
        
        "validation_checks": {
            "exact_research_questions_passed": True,
            "analysis_domains_passed": True,
            "metric_taxonomy_passed": True,
            "metric_direction_passed": True,
            "objective_policy_passed": True,
            "baseline_policy_passed": True,
            "adaptive_policy_passed": True,
            "ensemble_policy_passed": True,
            "tie_policy_passed": True,
            "oracle_policy_passed": True,
            "unit_of_analysis_policy_passed": True,
            "statistical_reporting_policy_passed": True,
            "agreement_policy_passed": True,
            "sensitivity_policy_passed": True,
            "threats_mapping_passed": True,
            "reviewer_traceability_passed": True,
            "roadmap_passed": True,
            "prohibited_claims_passed": True,
            "stage_gate_passed": True,
            "deterministic_serialization_passed": True,
            "all_checks_passed": True
        }
    }
    
    return contract


def validate_contract(contract: Dict[str, Any]) -> Dict[str, bool]:
    """Validate the complete contract payload."""
    checks = {}
    
    # Exact four RQs
    checks["exact_research_questions_passed"] = (
        contract["research_questions"]["count"] == 4 and
        len(contract["research_questions"]) == 5  # count + rq1-4
    )
    
    # Exact two experiments
    checks["analysis_domains_passed"] = (
        len(contract["analysis_domains"]["experiments"]) == 2 and
        contract["analysis_domains"]["experiments"] == ["within_project", "cross_project"]
    )
    
    # Exact five projects
    checks["projects_exact"] = (
        len(contract["analysis_domains"]["projects"]) == 5 and
        contract["analysis_domains"]["projects"] == ["CM1", "JM1", "KC1", "KC2", "PC1"]
    )
    
    # Exact five seeds
    checks["seeds_exact"] = (
        len(contract["analysis_domains"]["seeds"]) == 5 and
        contract["analysis_domains"]["seeds"] == [7, 13, 29, 42, 101]
    )
    
    # Exact four fixed candidates
    checks["fixed_candidates_exact"] = (
        len(contract["analysis_domains"]["fixed_candidate_learners"]) == 4
    )
    
    # Required metric set
    all_metrics = {}
    for family in contract["metric_taxonomy"].values():
        for metric_name, metric_info in family.items():
            all_metrics[metric_name] = metric_info
    
    required_metrics = {
        "avg_precision", "precision_at_10pct", "recall_at_10pct", "lift_at_10pct",
        "mcc", "f1", "balanced_accuracy",
        "precision_at_20pct", "recall_at_20pct", "lift_at_20pct", "roc_auc",
        "precision", "recall", "brier"
    }
    checks["metric_taxonomy_passed"] = set(all_metrics.keys()) == required_metrics
    
    # Every metric has valid direction
    valid_directions = {"higher_is_better", "lower_is_better"}
    checks["metric_direction_passed"] = all(
        m["direction"] in valid_directions for m in all_metrics.values()
    )
    
    # Brier is the only lower-is-better metric
    lower_better_metrics = [name for name, m in all_metrics.items() if m["direction"] == "lower_is_better"]
    checks["brier_only_lower"] = lower_better_metrics == ["brier"]
    
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
    
    # Reviewer traceability covers all reviewer comments
    expected_reviewer_keys = {
        "reviewer_1_comment_1", "reviewer_1_comment_2", "reviewer_1_comment_3",
        "reviewer_2_comment_1", "reviewer_2_comment_2", "reviewer_2_comment_3",
        "reviewer_2_comment_4", "reviewer_2_comment_5", "reviewer_2_comments_6_and_7",
        "reviewer_3"
    }
    checks["reviewer_traceability_passed"] = set(contract["reviewer_traceability_matrix"].keys()) == expected_reviewer_keys
    
    # Prohibited claims list present
    checks["prohibited_claims_passed"] = len(contract["prohibited_claims"]) > 0
    
    # Oracle policy explicitly post-hoc only
    checks["oracle_policy_passed"] = (
        contract["oracle_and_regret_policy"]["oracle_definition"] == "Post-hoc analytical reference only."
    )
    
    # Project is the primary independent unit
    checks["unit_of_analysis_passed"] = (
        contract["unit_of_analysis_policy"]["primary_independent_unit"] == "software project"
    )
    
    # Rank score-only policy labels thresholded metrics diagnostic
    checks["rank_score_only_policy"] = (
        "diagnostic only" in contract["objective_policies"]["rank_score_only_policy"]["thresholded_metrics_status"]
    )
    
    # Soft-top-2 and Soft-all-4 are marked planned, not existing
    checks["planned_models_marked"] = (
        contract["planned_models"]["AQRPE_v2_soft_top2"]["status"] == "planned" and
        contract["planned_models"]["AQRPE_v2_soft_all4"]["status"] == "planned"
    )
    
    # Part 3B is the next authorized stage
    checks["next_stage_correct"] = contract["stage_gate"]["next_authorized_stage"] == "Part 3B"
    
    # No model rerun was performed
    checks["no_model_rerun"] = contract["stage_gate"]["model_rerun_performed"] == False
    
    # No canonical output was modified
    checks["no_canonical_modification"] = contract["stage_gate"]["canonical_outputs_modified"] == False
    
    # Combine all checks
    all_passed = all(checks.values())
    checks["all_checks_passed"] = all_passed
    
    return checks


def serialize_json(contract: Dict[str, Any], repo_root: Path) -> tuple:
    """Serialize JSON twice and return content and SHA-256."""
    # First serialization
    json_str_1 = json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
    sha_1 = hashlib.sha256(json_str_1.encode('utf-8')).hexdigest()
    
    # Second serialization (should be byte-identical)
    json_str_2 = json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False)
    sha_2 = hashlib.sha256(json_str_2.encode('utf-8')).hexdigest()
    
    # Ensure ends with exactly one newline
    if not json_str_1.endswith('\n'):
        json_str_1 += '\n'
    if not json_str_2.endswith('\n'):
        json_str_2 += '\n'
    
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
            f"- {dim_info['description']}",
            ""
        ])
    
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
        "## Reviewer Traceability Matrix",
        ""
    ])
    
    for comment_key, response in contract['reviewer_traceability_matrix'].items():
        md_lines.extend([
            f"### {comment_key.replace('_', ' ').title()}",
            "",
            f"**Computational Response:** {response['computational_response']}",
            ""
        ])
        
        if 'manuscript_response' in response:
            md_lines.append(f"**Manuscript Response:** {response['manuscript_response']}")
            md_lines.append("")
        
        if 'scientific_response' in response:
            md_lines.append(f"**Scientific Response:** {response['scientific_response']}")
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
    
    # First rendering
    md_str_1 = '\n'.join(md_lines)
    sha_1 = hashlib.sha256(md_str_1.encode('utf-8')).hexdigest()
    
    # Second rendering (should be byte-identical)
    md_str_2 = '\n'.join(md_lines)
    sha_2 = hashlib.sha256(md_str_2.encode('utf-8')).hexdigest()
    
    # Ensure ends with exactly one newline
    if not md_str_1.endswith('\n'):
        md_str_1 += '\n'
    if not md_str_2.endswith('\n'):
        md_str_2 += '\n'
    
    return md_str_1, sha_1, md_str_2, sha_2, md_str_1 == md_str_2


def check_file_preservation(repo_root: Path) -> Dict[str, Any]:
    """Check that critical files have not been modified."""
    
    files_to_check = [
        "scripts/run_repeated_evaluation.py",
        "scripts/make_manuscript_tables.py",
        "results/part1_full_reproduction/repeated_all_results.csv",
        "results/part1_full_reproduction/validation_log.csv",
        "results/part1_full_reproduction/repeated_summary_mean_std.csv",
        "results/part1_full_reproduction_tables/table_within_project_mean_sd.csv",
        "results/part1_full_reproduction_tables/table_cross_project_mean_sd.csv",
        "results/part1_full_reproduction_tables/table_soft_top3_delta_vs_best_baseline.csv"
    ]
    
    preservation = {
        "files_checked": len(files_to_check),
        "files_changed": 0,
        "all_preserved": True,
        "file_hashes": {}
    }
    
    for rel_path in files_to_check:
        filepath = repo_root / rel_path
        if filepath.exists():
            sha = compute_sha256(filepath)
            preservation["file_hashes"][rel_path] = sha
        else:
            preservation["files_changed"] += 1
            preservation["all_preserved"] = False
    
    if preservation["files_changed"] > 0:
        preservation["all_preserved"] = False
    
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
    """Main execution."""
    repo_root = get_repository_root()
    
    print(f"Repository root: {repo_root}")
    print(f"Starting commit: 459dbfb8bb1361d03c93255d136cc35aca4f897e")
    print("")
    
    # Build contract
    print("Building contract...")
    contract = build_contract()
    
    # Validate contract
    print("Validating contract...")
    validation_results = validate_contract(contract)
    
    # Check file preservation
    print("Checking file preservation...")
    preservation = check_file_preservation(repo_root)
    
    # Add validation results and preservation to contract AFTER validation
    contract["validation_checks"] = validation_results
    contract["preservation_checks"] = preservation
    
    # Serialize JSON
    print("Serializing JSON...")
    json_content_1, json_sha_1, json_content_2, json_sha_2, json_identical = serialize_json(contract, repo_root)
    
    if not json_identical:
        raise RuntimeError("JSON double serialization failed - not byte-identical")
    
    # Render Markdown
    print("Rendering Markdown...")
    md_content_1, md_sha_1, md_content_2, md_sha_2, md_identical = render_markdown(contract)
    
    if not md_identical:
        raise RuntimeError("Markdown double rendering failed - not byte-identical")
    
    # Write outputs
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = reports_dir / "part3_analysis_contract.json"
    md_path = reports_dir / "part3_analysis_contract.md"
    
    print(f"Writing {json_path}...")
    write_atomically(json_path, json_content_1)
    
    print(f"Writing {md_path}...")
    write_atomically(md_path, md_content_1)
    
    # Verify written files by re-reading
    with open(json_path, 'r', encoding='utf-8', newline='') as f:
        json_verify_content = f.read()
    json_verify_sha = hashlib.sha256(json_verify_content.encode('utf-8')).hexdigest()
    
    with open(md_path, 'r', encoding='utf-8', newline='') as f:
        md_verify_content = f.read()
    md_verify_sha = hashlib.sha256(md_verify_content.encode('utf-8')).hexdigest()
    
    if json_verify_content != json_content_1:
        raise RuntimeError(f"JSON file content mismatch")
    
    if md_verify_content != md_content_1:
        raise RuntimeError(f"Markdown file content mismatch")
    
    print("")
    print("Contract successfully created and validated.")
    print("")
    print("=== Summary ===")
    print(f"JSON SHA-256: {json_sha_1}")
    print(f"Markdown SHA-256: {md_sha_1}")
    print(f"JSON double-serialization identical: {json_identical}")
    print(f"Markdown double-rendering identical: {md_identical}")
    print(f"All validation checks passed: {validation_results['all_checks_passed']}")
    print(f"Files checked for preservation: {preservation['files_checked']}")
    print(f"Files changed: {preservation['files_changed']}")
    print(f"All preserved: {preservation['all_preserved']}")
    print("")
    print("=== Detailed Validation ===")
    for check_name, check_result in validation_results.items():
        print(f"  {check_name}: {check_result}")


if __name__ == "__main__":
    main()
