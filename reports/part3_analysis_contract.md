# Scientific Analysis Contract for Major Revision

**Contract Version:** Part-3A-v1
**Starting Commit:** 459dbfb8bb1361d03c93255d136cc35aca4f897e
**Repository:** abtinasg/springer
**Branch:** major-revision-analysis-v2

## Scientific Positioning

A validation-controlled empirical study of model selection behavior, metric-dependent trade-offs, selection stability, validation-test agreement, post-hoc regret, and soft-ensemble ablation for imbalanced software defect prediction under repeated within-project and cross-project evaluation.

### Key Assertions

- Validation-based selection is standard methodology.
- Soft averaging is standard ensemble methodology.
- Repeated seeds and train/validation/test separation are experimental controls.
- The scientific contribution is empirical characterization and controlled evidence, not the invention of a fundamentally new learning algorithm.
- No result may be framed as universal dominance.
- Conclusions must remain dataset-, metric-, setting-, and protocol-dependent.

## Reviewer Context

### Reviewer 2 Focus

- Methodological decisions require clearer justification.
- Threats to validity require deeper analysis.
- Limitations and future directions must be evidence-based.

### Reviewer 3 Focus

- Validation-based model selection is standard.
- Averaging top models is standard.
- Repeated seeds and leakage control are good practice, not algorithmic novelty.
- The paper should be treated as a careful empirical study rather than a new fundamental algorithm.

## Research Questions

**Total Research Questions:** 4

### Comparative performance

**Exact Intent:** How do the four fixed candidate learners, validation-selected adaptive Top-1 variants, and validation-constructed soft ensembles compare under repeated within-project and cross-project evaluation?

**Requirements:**

- Objective-matched comparisons.
- Run-level outputs.
- Project-level aggregation.
- No post-hoc selection of a favorable comparison only.
- Separate interpretation for within-project and cross-project settings.

### Metric-dependent trade-offs

**Exact Intent:** How do model rankings and conclusions change across discrimination, thresholded classification, early-inspection ranking, and calibration-sensitive metrics?

**Requirements:**

- No single metric defines an overall winner.
- Metric direction must be explicit.
- Ranking metrics, thresholded metrics, and calibration metrics represent different operational goals.
- Brier score is minimized.
- All other retained metrics are maximized.

### Selection behavior and stability

**Exact Intent:** How frequently and how stably are candidates selected across projects and seeds, and how well do validation rankings agree with held-out test rankings?

**Required Analyses:**

- Top-1 selection frequency.
- Top-1 seed stability.
- Soft-top-3 membership and order stability.
- Exact validation-test Top-1 agreement.
- Winner-set overlap.
- Selected-candidate test rank.
- Spearman and Kendall rank agreement.
- Explicit statement that these are descriptive analyses, not proof of superiority.

### Regret, ensemble size, and ablation

**Exact Intent:** What do post-hoc regret and controlled ablation reveal about the value of adaptive Top-1 selection, Soft-top-2, Soft-top-3, and Soft-all-4 relative to fixed candidates and an oracle reference?

**Requirements:**

- Fixed individual candidates.
- Adaptive Top-1.
- Soft-top-2.
- Soft-top-3.
- Soft-all-4.
- Oracle best candidate on test used only as a post-hoc analytical reference.
- Selected-versus-oracle regret.
- Marginal ensemble-size comparisons.
- No use of test information for actual model selection.

## Analysis Domains

### Experiments

- within_project
- cross_project

### Projects

- CM1
- JM1
- KC1
- KC2
- PC1

### Seeds

- 7
- 13
- 29
- 42
- 101

### Fixed Candidate Learners

- LR_std_C0.1
- LR_std_C1
- DT_leaf5
- ET_leaf5

### Existing Adaptive Models

- AQRPE_v2_balanced
- AQRPE_v2_rank
- AQRPE_v2_mcc
- AQRPE_v2_soft_top3

### Planned Additional Ensemble Models

- AQRPE_v2_soft_top2
- AQRPE_v2_soft_all4

### Concept Distinctions

- candidate learner
- validation selector
- threshold policy
- ensemble construction rule
- post-hoc oracle

## Metric Taxonomy

### Primary Discrimination Ranking

**Average Precision (avg_precision)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: False
- Practical Interpretation: Area under precision-recall curve, threshold-free ranking quality.

**Precision@10% (precision_at_10pct)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: True
- Practical Interpretation: Precision when inspecting top 10% of risky instances.

**Recall@10% (recall_at_10pct)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: True
- Practical Interpretation: Defect coverage when inspecting top 10% of risky instances.

**Lift@10% (lift_at_10pct)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: True
- Practical Interpretation: Ratio of precision@10% to baseline defect rate.

### Primary Thresholded Classification

**Matthews Correlation Coefficient (mcc)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: True
- Practical Interpretation: Balanced measure for binary classification, robust to class imbalance.

**F1 Score (f1)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: True
- Practical Interpretation: Harmonic mean of precision and recall.

**Balanced Accuracy (balanced_accuracy)**

- Direction: higher_is_better
- Primary/Secondary: primary
- Threshold Dependent: True
- Practical Interpretation: Average of recall across both classes.

### Secondary Ranking

**Precision@20% (precision_at_20pct)**

- Direction: higher_is_better
- Primary/Secondary: secondary
- Threshold Dependent: True
- Practical Interpretation: Precision when inspecting top 20% of risky instances.

**Recall@20% (recall_at_20pct)**

- Direction: higher_is_better
- Primary/Secondary: secondary
- Threshold Dependent: True
- Practical Interpretation: Defect coverage when inspecting top 20% of risky instances.

**Lift@20% (lift_at_20pct)**

- Direction: higher_is_better
- Primary/Secondary: secondary
- Threshold Dependent: True
- Practical Interpretation: Ratio of precision@20% to baseline defect rate.

**ROC AUC (roc_auc)**

- Direction: higher_is_better
- Primary/Secondary: secondary
- Threshold Dependent: False
- Practical Interpretation: Area under ROC curve, threshold-free ranking quality. Secondary because precision-recall is more informative under imbalance.

### Secondary Diagnostic

**Precision (precision)**

- Direction: higher_is_better
- Primary/Secondary: secondary
- Threshold Dependent: True
- Practical Interpretation: Diagnostic metric, must not be interpreted without threshold policy.

**Recall (recall)**

- Direction: higher_is_better
- Primary/Secondary: secondary
- Threshold Dependent: True
- Practical Interpretation: Diagnostic metric, must not be interpreted without threshold policy.

### Calibration Sensitive

**Brier Score (brier)**

- Direction: lower_is_better
- Primary/Secondary: primary
- Threshold Dependent: False
- Practical Interpretation: Mean squared error of predicted probabilities, reflects calibration.

## Objective-Matched Comparison Policy

### Balanced Policy

Candidate ranking by balanced validation objective, threshold selected by balanced validation objective.

### Mcc Policy

Candidate ranking by validation MCC objective, threshold selected by validation MCC objective.

### Rank Score Only Policy

Candidate ranking by rank objective, primary interpretation restricted to threshold-free and top-k metrics, thresholded metrics are diagnostic only when threshold is fixed at 0.5.

### Rank Plus Validation Threshold Policy

Candidate ranking by rank objective, after candidate or ensemble selection, threshold is tuned on validation only. This policy is a planned sensitivity analysis and must not replace or silently overwrite the existing score-only rank policy.

## Fixed Baseline Policy

### Individual Fixed Baselines

- LR_std_C0.1
- LR_std_C1
- DT_leaf5
- ET_leaf5

### Best Fixed Baseline

**Selection Rules:**

- Separately for each metric.
- Separately for each experiment.
- From the four fixed candidates only.
- For descriptive summary after all candidate results are available.

**Status:** post-hoc descriptive

**Warning:** Must not be treated as a validation-selected deployment rule unless a separate validation-only baseline-selection mechanism is defined.

## Adaptive Top-1 Policy

### Definition

- Train all four candidates on training data.
- Score all candidates on validation data.
- Select one candidate using the specified validation objective.
- Freeze its threshold according to the specified policy.
- Evaluate once on held-out test data.

### Distinguished Components

- Selected candidate identity.
- Selection score.
- Validation threshold.
- Test performance.
- Test rank.
- Post-hoc regret.

**Prohibition:** No test label, test score, test metric, or test ranking may influence the selection.

## Soft Ensemble Policy

### Definition

- Rank candidates using validation scores only.
- Select the top k candidates using a deterministic tie policy.
- Average their defective-class probabilities with equal weights.
- Tune the ensemble threshold using validation data only.
- Freeze selected membership, order, weights, and threshold.
- Evaluate once on test data.

**Planned k Values:** [2, 3, 4]

**Note:** Soft-all-4 includes all four candidates and therefore does not involve membership selection, but its threshold must still be tuned on validation only.

### Key Assertions

- Equal weighting is the primary ensemble rule.
- Learned weights are outside the current study scope.
- Soft-top-3 must not be treated as privileged before the ablation is complete.
- If Soft-top-3 does not outperform Soft-all-4 or Soft-top-2 consistently, the manuscript must report that result directly.

## Tie Policy

### Validation Candidate Ranking

- Use exact validation score ordering.
- Use a tolerance of 1e-12 only for reporting near ties.
- Do not merge non-transitive chains of near-equal values.
- If exact scores are equal, use the following deterministic candidate order: LR_std_C0.1, LR_std_C1, DT_leaf5, ET_leaf5.

### Distinguished Concepts

- Exact tie.
- Near tie.
- Winner set.
- Deterministic operational choice.

**Scientific Analysis Rule:** For scientific analysis, all exact tied winners must be preserved in the winner set even if one deterministic candidate is used operationally.

## Oracle and Regret Policy

**Oracle Definition:** Post-hoc analytical reference only.

### Oracle Computation

- higher_is_better: oracle_value = maximum test value among the four fixed candidates
- lower_is_better: oracle_value = minimum test value among the four fixed candidates

### Absolute Regret

- higher_is_better: oracle_value - selected_value
- lower_is_better: selected_value - oracle_value

**Property:** Regret must always be non-negative up to floating-point tolerance.

**Normalized Regret Formula:** absolute_regret / max(abs(oracle_value), 1e-12)

### Separate Records

- Exact winner.
- Tolerance winner using 1e-12.
- Selected candidate test rank.
- Selected candidate in oracle winner set.
- Absolute regret.
- Normalized regret.

### Key Assertions

- Oracle is not a deployable model.
- Oracle uses test information only for retrospective analysis.
- Oracle values must never feed candidate selection, threshold selection, ensemble construction, or model fitting.

## Unit of Analysis

**Primary Independent Unit:** software project

### Repeated Seed

- Definition: Within-project replication nested inside a project.
- Not:
  - An independent project.
  - A valid substitute for additional datasets.

### Run-Level Observations May Be Used For

- Descriptive distributions.
- Stability analysis.
- Event-level regret.
- Debugging and provenance.

### Run-Level Observations Must Not Be Used For

- Fully independent observations for significance claims.

### Project-Level Paired Summaries

- First aggregate the five seeds within each project.
- Then compare methods across the five projects.

### Prohibitions

- Treating 25 project-seed runs as 25 fully independent projects.
- Using seed-level p-values as primary superiority evidence.
- Claiming general population-level significance from five projects.

## Statistical Reporting

### Required Descriptive Reporting

- Mean.
- Standard deviation.
- Median.
- Interquartile range.
- Minimum.
- Maximum.
- Positive / negative / tied project counts.
- Five raw project-level paired differences when space permits.

### Permitted Exploratory Inference

- Exact Wilcoxon signed-rank test at project level only.
- Only when the assumptions and zero-difference handling are explicitly stated.
- Labeled exploratory.
- No binary accept/reject conclusion based only on p-values.

### Effect Reporting

- Median paired project-level difference.
- Rank-biserial effect size or another predeclared paired effect size.
- Explicit warning that n_projects = 5.

### Key Assertions

- No multiple-comparison-adjusted confirmatory family is claimed.
- No inferential superiority claim is authorized.
- Conclusions must emphasize direction, magnitude, consistency, and limitations.

## Validation-Test Agreement

### Required Agreement Analyses

- Strict Top-1 exact agreement.
- Tolerance-aware Top-1 agreement.
- Exact winner-set equality.
- Tolerance-aware winner-set equality.
- Winner-set overlap.
- Jaccard similarity.
- Spearman correlation.
- Kendall tau-b.
- Selected candidate test rank.
- Selected candidate in test winner set.

### Explicit Statements

- Agreement is descriptive.
- Low agreement does not by itself prove the validation procedure is invalid.
- High agreement does not prove predictive superiority.
- Undefined rank correlations must remain missing, never substituted with zero.
- All test-based agreement is retrospective analysis only.

## Sensitivity Analyses

### Required Dimensions

**Balanced Objective Weights**
- Current weights, equal-weight alternative, predefined weight perturbations.

**Rank Threshold Policy**
- Fixed 0.5, validation-tuned secondary threshold.

**Threshold Grid**
- Current grid, denser validation-only grid.

**Cross Project Validation Design**
- Current stratified source-row split, source-project-aware validation robustness check.

### Optional After Required

- More seeds.
- Additional learners.
- Broader hyperparameter search.

**Dataset Change Policy:** Changing the five benchmark projects is outside the current computational revision unless new verified datasets are introduced under a separate protocol.

## Threats to Validity

### Internal Validity

**Threat:** Leakage

- Possible Impact: Inflated performance due to test information contaminating training.
- Current Mitigation: Strict train/validation/test splits, leakage audit in Part 3B.
- Remaining Limitation: Complex preprocessing pipelines may have subtle leakage.
- Planned Computational Response: Comprehensive leakage audit in Part 3B.

**Threat:** Preprocessing fitted outside training

- Possible Impact: Data leakage through preprocessing parameters.
- Current Mitigation: Preprocessing fitted on training fold only.
- Remaining Limitation: Need to verify all preprocessing steps.
- Planned Computational Response: Audit preprocessing pipeline in Part 3B.

**Threat:** Nondeterminism

- Possible Impact: Inconsistent results across runs.
- Current Mitigation: Fixed random seeds, deterministic algorithms.
- Remaining Limitation: Some library components may have nondeterministic behavior.
- Planned Computational Response: Verify seed stability in Part 3C.

**Threat:** Tie handling

- Possible Impact: Selection instability when scores are equal.
- Current Mitigation: Deterministic tie-breaking order.
- Remaining Limitation: Near ties may still cause instability.
- Planned Computational Response: Report tie frequency and impact in Part 3C.

**Threat:** Threshold-selection mismatch

- Possible Impact: Unfair comparisons using different threshold policies.
- Current Mitigation: Objective-matched comparison policy.
- Remaining Limitation: Policy mismatches may still occur in exploratory analyses.
- Planned Computational Response: Explicit policy labeling in Part 3C.

**Threat:** Post-hoc analytical choices

- Possible Impact: Cherry-picking favorable analyses.
- Current Mitigation: Pre-specified analysis contract.
- Remaining Limitation: Exploratory analyses may still be selective.
- Planned Computational Response: Distinguish pre-specified from exploratory in reporting.

### Construct Validity

**Threat:** Metric disagreement

- Possible Impact: Different metrics may rank models differently.
- Current Mitigation: Comprehensive metric taxonomy, metric-dependent analysis.
- Remaining Limitation: No single metric captures all operational goals.
- Planned Computational Response: RQ2 analysis of metric trade-offs.

**Threat:** Threshold dependence

- Possible Impact: Thresholded metrics sensitive to threshold choice.
- Current Mitigation: Validation-tuned thresholds, fixed 0.5 baseline.
- Remaining Limitation: Threshold policy may favor certain methods.
- Planned Computational Response: Sensitivity analysis on threshold policy in Part 3F.

**Threat:** Top-k budget dependence

- Possible Impact: Precision@k and recall@k depend on inspection budget.
- Current Mitigation: Multiple k values (10%, 20%).
- Remaining Limitation: Results may not generalize to other budgets.
- Planned Computational Response: Report results for multiple k values.

**Threat:** Calibration versus discrimination

- Possible Impact: Models may excel at one but not the other.
- Current Mitigation: Separate calibration metric (Brier score).
- Remaining Limitation: Trade-off between calibration and discrimination.
- Planned Computational Response: Analyze calibration-discrimination trade-off in RQ2.

**Threat:** Oracle interpretation

- Possible Impact: Oracle may be misinterpreted as achievable target.
- Current Mitigation: Explicit post-hoc-only labeling.
- Remaining Limitation: Oracle is not a deployable method.
- Planned Computational Response: Clear oracle framing in all reporting.

### External Validity

**Threat:** Only five NASA/PROMISE projects

- Possible Impact: Results may not generalize to other datasets.
- Current Mitigation: Diverse project characteristics.
- Remaining Limitation: Small number of datasets, all from same domain.
- Planned Computational Response: Explicit limitation statement, no universal claims.

**Threat:** Static metrics only

- Possible Impact: Results may not apply to process or change metrics.
- Current Mitigation: Clear scope definition.
- Remaining Limitation: Static metrics may not capture dynamic defect patterns.
- Planned Computational Response: Limitation statement on metric type.

**Threat:** Older public benchmark data

- Possible Impact: Data may not reflect modern software development.
- Current Mitigation: Use of established benchmark.
- Remaining Limitation: Data age and collection methodology.
- Planned Computational Response: Limitation statement on data vintage.

**Threat:** Compact learner pool

- Possible Impact: Results may not extend to other learner types.
- Current Mitigation: Diverse learner families (LR, DT, ET).
- Remaining Limitation: Limited hyperparameter search, no deep learning.
- Planned Computational Response: Limitation statement on learner scope.

**Threat:** No industrial deployment evaluation

- Possible Impact: Practical utility unverified.
- Current Mitigation: Clear empirical study framing.
- Remaining Limitation: No real-world deployment validation.
- Planned Computational Response: Limitation statement on deployment gap.

### Conclusion Validity

**Threat:** Five independent projects

- Possible Impact: Low statistical power.
- Current Mitigation: Project-level paired analysis, descriptive focus.
- Remaining Limitation: N=5 is small for strong inference.
- Planned Computational Response: Emphasize descriptive over inferential, report effect sizes.

**Threat:** Repeated seeds are nested

- Possible Impact: Pseudo-replication if treated as independent.
- Current Mitigation: Project as primary unit, seed as nested replication.
- Remaining Limitation: Limited independent observations.
- Planned Computational Response: Strict unit-of-analysis policy, no seed-level inference.

**Threat:** Low power

- Possible Impact: Type II errors, missed real differences.
- Current Mitigation: Descriptive emphasis, effect size reporting.
- Remaining Limitation: Small N limits detection of small effects.
- Planned Computational Response: Power limitation in discussion.

**Threat:** Multiple metrics

- Possible Impact: Multiple comparisons, inconsistent conclusions.
- Current Mitigation: Metric taxonomy, family grouping.
- Remaining Limitation: No unified metric family-wise error control.
- Planned Computational Response: Metric-by-metric interpretation, no global superiority claim.

**Threat:** Descriptive versus inferential distinction

- Possible Impact: Over-interpretation of descriptive patterns.
- Current Mitigation: Clear labeling of descriptive vs exploratory inference.
- Remaining Limitation: Exploratory tests may be misinterpreted.
- Planned Computational Response: Explicit framing, no binary accept/reject.

**Threat:** Sensitivity to objective weights and validation design

- Possible Impact: Results may change under different validation schemes.
- Current Mitigation: Pre-specified validation design.
- Remaining Limitation: Many possible validation alternatives.
- Planned Computational Response: Sensitivity analysis in Part 3F.

## Reviewer Traceability Matrix

### Reviewer 1 Comment 1

**Computational Response:** Metric dictionary in later Part 3H

**Manuscript Response:** Brief practical metric explanation

### Reviewer 1 Comment 2

**Computational Response:** None

**Manuscript Response:** Key finding paragraph before every results table

### Reviewer 1 Comment 3

**Computational Response:** Deterministic workflow figure in later Part 3H

**Manuscript Response:** Include figure and description

### Reviewer 2 Comment 1

**Computational Response:** None

**Manuscript Response:** Rewrite abstract to 150-250 words

### Reviewer 2 Comment 2

**Computational Response:** None

**Manuscript Response:** Verified 2025-2026 literature update

### Reviewer 2 Comment 3

**Computational Response:** ['Objective-matched comparisons.', 'Prediction ledger.', 'Regret.', 'Ablation.', 'Sensitivity.', 'Project-level effects']

**Manuscript Response:** Not applicable (computational focus)

### Reviewer 2 Comment 4

**Computational Response:** ['Leakage audit.', 'Robustness analyses.', 'Dependency-aware statistical policy']

**Manuscript Response:** Not applicable (computational focus)

### Reviewer 2 Comment 5

**Computational Response:** Final limitations grounded in completed analyses

**Manuscript Response:** Not applicable (computational focus)

### Reviewer 2 Comments 6 And 7

**Computational Response:** None

**Manuscript Response:** Citation renumbering and Springer formatting

### Reviewer 3

**Computational Response:** ['Selection frequency.', 'Seed stability.', 'Validation-test agreement.', 'Post-hoc regret.', 'Ensemble-size ablation.', 'Sensitivity analysis.', 'Objective-matched comparison']

**Scientific Response:** Reposition the study as a controlled empirical evaluation rather than a fundamentally novel algorithm.

## Remaining Computational Roadmap

- Part 3A: Scientific analysis contract
- Part 3B: Prediction ledger and split/leakage audit
- Part 3C: Objective-matched candidate and adaptive evaluation
- Part 3D: Post-hoc regret and oracle-gap analysis
- Part 3E: Ensemble-size and component ablation
- Part 3F: Methodological sensitivity analyses
- Part 3G: Project-level paired effects and uncertainty
- Part 3H: Workflow diagram and metric dictionary
- Part 4: Final full rerun, deterministic artifact freeze, package rebuild, and canonical manifest

## Prohibited Claims

- AQRPE v2 is a fundamentally new algorithm.
- Validation-based model selection is itself a novel contribution.
- Soft averaging of top models is itself a novel contribution.
- Repeated seeds establish external validity.
- Train/validation/test separation is itself an algorithmic contribution.
- AQRPE universally outperforms all baselines.
- Five seeds are five independent datasets.
- Twenty-five project-seed runs are twenty-five independent projects.
- A p-value alone proves superiority.
- The test oracle is a deployable selection method.
- Soft-top-3 is optimal before ablation.
- Test data may influence selection or threshold tuning.

## Stage Gate

- Part 3A Contract Frozen: True
- Model Rerun Performed: False
- Canonical Outputs Modified: False
- Manuscript Modified: False
- Next Authorized Stage: Part 3B

**Part 3B Constraint:** Part 3B cannot alter the current 400 canonical result rows or current canonical manuscript tables unless a later explicitly approved migration stage is created.

## Validation Checks

- exact_research_questions_passed: True
- analysis_domains_passed: True
- projects_exact: True
- seeds_exact: True
- fixed_candidates_exact: True
- metric_taxonomy_passed: True
- metric_direction_passed: True
- brier_only_lower: True
- roadmap_passed: True
- reviewer_traceability_passed: True
- prohibited_claims_passed: True
- oracle_policy_passed: True
- unit_of_analysis_passed: True
- rank_score_only_policy: True
- planned_models_marked: True
- next_stage_correct: True
- no_model_rerun: True
- no_canonical_modification: True
- all_checks_passed: True
