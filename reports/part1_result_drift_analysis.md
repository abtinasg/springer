# Part 1 Section 6C: Result Drift Analysis

## Summary

- **Total setting-metric combinations**: 16
- **Best-overall identity changes**: 1
- **Best-baseline identity changes**: 2
- **Soft-top-3 outcome changes**: 0
- **Combinations with any rank change**: 6
- **Minimum Spearman correlation**: 0.8571
- **Maximum absolute mean-value change**: 0.111536

## Best-Overall Identity Changes

- **cross_project / brier**: AQRPE_v2_balanced → AQRPE_v2_mcc

## Best-Baseline Identity Changes

- **within_project / mcc**: LR_std_C0.1 → ET_leaf5
- **within_project / lift_at_10pct**: ET_leaf5 → LR_std_C1

## Detailed Results by Setting-Metric Combination

### within_project / mcc

**Best Overall Model:**
- Reference: AQRPE_v2_rank (0.355922)
- Locked: AQRPE_v2_rank (0.354745)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C0.1 (0.318350)
- Locked: ET_leaf5 (0.320441)
- Identity changed: True

**Soft-Top-3 Performance:**
- Reference value: 0.340068
- Locked value: 0.339156
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 4/8
- Maximum rank change: 1
- Spearman correlation: 0.9524
- Max absolute mean-value change: 0.006169

**Rank Details:**
- AQRPE_v2_balanced: Ref=7, Locked=6, Change=1
- AQRPE_v2_mcc: Ref=5, Locked=5, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=4, Locked=3, Change=1
- LR_std_C0.1: Ref=3, Locked=4, Change=1
- LR_std_C1: Ref=6, Locked=7, Change=1

### within_project / avg_precision

**Best Overall Model:**
- Reference: AQRPE_v2_rank (0.455553)
- Locked: AQRPE_v2_rank (0.454230)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (0.421389)
- Locked: ET_leaf5 (0.420293)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.440253
- Locked value: 0.440429
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.002617

**Rank Details:**
- AQRPE_v2_balanced: Ref=6, Locked=6, Change=0
- AQRPE_v2_mcc: Ref=7, Locked=7, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=3, Locked=3, Change=0
- LR_std_C0.1: Ref=4, Locked=4, Change=0
- LR_std_C1: Ref=5, Locked=5, Change=0

### within_project / f1

**Best Overall Model:**
- Reference: AQRPE_v2_rank (0.448473)
- Locked: AQRPE_v2_rank (0.447602)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (0.406668)
- Locked: ET_leaf5 (0.408831)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.424034
- Locked value: 0.423754
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.002326

**Rank Details:**
- AQRPE_v2_balanced: Ref=4, Locked=4, Change=0
- AQRPE_v2_mcc: Ref=5, Locked=5, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=3, Locked=3, Change=0
- LR_std_C0.1: Ref=6, Locked=6, Change=0
- LR_std_C1: Ref=7, Locked=7, Change=0

### within_project / balanced_accuracy

**Best Overall Model:**
- Reference: AQRPE_v2_rank (0.724039)
- Locked: AQRPE_v2_rank (0.723023)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C1 (0.689859)
- Locked: LR_std_C1 (0.689859)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.694637
- Locked value: 0.694907
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.002792

**Rank Details:**
- AQRPE_v2_balanced: Ref=6, Locked=6, Change=0
- AQRPE_v2_mcc: Ref=7, Locked=7, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=5, Locked=5, Change=0
- LR_std_C0.1: Ref=4, Locked=4, Change=0
- LR_std_C1: Ref=3, Locked=3, Change=0

### within_project / precision_at_10pct

**Best Overall Model:**
- Reference: AQRPE_v2_rank (0.477887)
- Locked: AQRPE_v2_rank (0.473460)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C1 (0.455959)
- Locked: LR_std_C1 (0.455959)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.458026
- Locked value: 0.457398
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 2/8
- Maximum rank change: 1
- Spearman correlation: 0.9762
- Max absolute mean-value change: 0.008312

**Rank Details:**
- AQRPE_v2_balanced: Ref=6, Locked=6, Change=0
- AQRPE_v2_mcc: Ref=7, Locked=7, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=4, Locked=5, Change=1
- LR_std_C0.1: Ref=5, Locked=4, Change=1
- LR_std_C1: Ref=3, Locked=3, Change=0

### within_project / recall_at_10pct

**Best Overall Model:**
- Reference: AQRPE_v2_rank (0.372366)
- Locked: AQRPE_v2_rank (0.369520)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (0.345597)
- Locked: ET_leaf5 (0.341520)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.361307
- Locked value: 0.360881
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.011430

**Rank Details:**
- AQRPE_v2_balanced: Ref=5, Locked=5, Change=0
- AQRPE_v2_mcc: Ref=6, Locked=6, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=3, Locked=3, Change=0
- LR_std_C0.1: Ref=7, Locked=7, Change=0
- LR_std_C1: Ref=4, Locked=4, Change=0

### within_project / lift_at_10pct

**Best Overall Model:**
- Reference: AQRPE_v2_rank (3.636140)
- Locked: AQRPE_v2_rank (3.607964)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (3.368219)
- Locked: LR_std_C1 (3.336150)
- Identity changed: True

**Soft-Top-3 Performance:**
- Reference value: 3.527434
- Locked value: 3.523288
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 2/8
- Maximum rank change: 1
- Spearman correlation: 0.9762
- Max absolute mean-value change: 0.111536

**Rank Details:**
- AQRPE_v2_balanced: Ref=5, Locked=5, Change=0
- AQRPE_v2_mcc: Ref=6, Locked=6, Change=0
- AQRPE_v2_rank: Ref=1, Locked=1, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=3, Locked=4, Change=1
- LR_std_C0.1: Ref=7, Locked=7, Change=0
- LR_std_C1: Ref=4, Locked=3, Change=1

### within_project / brier

**Best Overall Model:**
- Reference: DT_leaf5 (0.134191)
- Locked: DT_leaf5 (0.133357)
- Identity changed: False

**Best Baseline Model:**
- Reference: DT_leaf5 (0.134191)
- Locked: DT_leaf5 (0.133357)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.148333
- Locked value: 0.146873
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.001460

**Rank Details:**
- AQRPE_v2_balanced: Ref=3, Locked=3, Change=0
- AQRPE_v2_mcc: Ref=4, Locked=4, Change=0
- AQRPE_v2_rank: Ref=5, Locked=5, Change=0
- AQRPE_v2_soft_top3: Ref=2, Locked=2, Change=0
- DT_leaf5: Ref=1, Locked=1, Change=0
- ET_leaf5: Ref=6, Locked=6, Change=0
- LR_std_C0.1: Ref=8, Locked=8, Change=0
- LR_std_C1: Ref=7, Locked=7, Change=0

### cross_project / mcc

**Best Overall Model:**
- Reference: AQRPE_v2_soft_top3 (0.293463)
- Locked: AQRPE_v2_soft_top3 (0.293438)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C0.1 (0.286870)
- Locked: LR_std_C0.1 (0.286870)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.293463
- Locked value: 0.293438
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 5/8
- Maximum rank change: 2
- Spearman correlation: 0.9048
- Max absolute mean-value change: 0.005379

**Rank Details:**
- AQRPE_v2_balanced: Ref=4, Locked=3, Change=1
- AQRPE_v2_mcc: Ref=6, Locked=7, Change=1
- AQRPE_v2_rank: Ref=7, Locked=6, Change=1
- AQRPE_v2_soft_top3: Ref=1, Locked=1, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=5, Locked=4, Change=1
- LR_std_C0.1: Ref=2, Locked=2, Change=0
- LR_std_C1: Ref=3, Locked=5, Change=2

### cross_project / avg_precision

**Best Overall Model:**
- Reference: AQRPE_v2_soft_top3 (0.359273)
- Locked: AQRPE_v2_soft_top3 (0.358844)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C1 (0.356339)
- Locked: LR_std_C1 (0.356312)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.359273
- Locked value: 0.358844
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.000762

**Rank Details:**
- AQRPE_v2_balanced: Ref=4, Locked=4, Change=0
- AQRPE_v2_mcc: Ref=5, Locked=5, Change=0
- AQRPE_v2_rank: Ref=6, Locked=6, Change=0
- AQRPE_v2_soft_top3: Ref=1, Locked=1, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=7, Locked=7, Change=0
- LR_std_C0.1: Ref=3, Locked=3, Change=0
- LR_std_C1: Ref=2, Locked=2, Change=0

### cross_project / f1

**Best Overall Model:**
- Reference: AQRPE_v2_soft_top3 (0.393335)
- Locked: AQRPE_v2_soft_top3 (0.392806)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C0.1 (0.387321)
- Locked: LR_std_C0.1 (0.387321)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.393335
- Locked value: 0.392806
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 3/8
- Maximum rank change: 2
- Spearman correlation: 0.9286
- Max absolute mean-value change: 0.010820

**Rank Details:**
- AQRPE_v2_balanced: Ref=4, Locked=5, Change=1
- AQRPE_v2_mcc: Ref=7, Locked=7, Change=0
- AQRPE_v2_rank: Ref=6, Locked=4, Change=2
- AQRPE_v2_soft_top3: Ref=1, Locked=1, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=5, Locked=6, Change=1
- LR_std_C0.1: Ref=2, Locked=2, Change=0
- LR_std_C1: Ref=3, Locked=3, Change=0

### cross_project / balanced_accuracy

**Best Overall Model:**
- Reference: AQRPE_v2_soft_top3 (0.685915)
- Locked: AQRPE_v2_soft_top3 (0.685664)
- Identity changed: False

**Best Baseline Model:**
- Reference: LR_std_C1 (0.674898)
- Locked: LR_std_C1 (0.674898)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.685915
- Locked value: 0.685664
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.005132

**Rank Details:**
- AQRPE_v2_balanced: Ref=4, Locked=4, Change=0
- AQRPE_v2_mcc: Ref=7, Locked=7, Change=0
- AQRPE_v2_rank: Ref=6, Locked=6, Change=0
- AQRPE_v2_soft_top3: Ref=1, Locked=1, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=5, Locked=5, Change=0
- LR_std_C0.1: Ref=3, Locked=3, Change=0
- LR_std_C1: Ref=2, Locked=2, Change=0

### cross_project / precision_at_10pct

**Best Overall Model:**
- Reference: AQRPE_v2_balanced (0.414298)
- Locked: AQRPE_v2_balanced (0.413764)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (0.414298)
- Locked: ET_leaf5 (0.413764)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.400087
- Locked value: 0.400436
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.003380

**Rank Details:**
- AQRPE_v2_balanced: Ref=1, Locked=1, Change=0
- AQRPE_v2_mcc: Ref=2, Locked=2, Change=0
- AQRPE_v2_rank: Ref=3, Locked=3, Change=0
- AQRPE_v2_soft_top3: Ref=6, Locked=6, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=4, Locked=4, Change=0
- LR_std_C0.1: Ref=5, Locked=5, Change=0
- LR_std_C1: Ref=7, Locked=7, Change=0

### cross_project / recall_at_10pct

**Best Overall Model:**
- Reference: AQRPE_v2_balanced (0.304315)
- Locked: AQRPE_v2_balanced (0.306049)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (0.304315)
- Locked: ET_leaf5 (0.306049)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.283987
- Locked value: 0.284368
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.003994

**Rank Details:**
- AQRPE_v2_balanced: Ref=1, Locked=1, Change=0
- AQRPE_v2_mcc: Ref=2, Locked=2, Change=0
- AQRPE_v2_rank: Ref=3, Locked=3, Change=0
- AQRPE_v2_soft_top3: Ref=5, Locked=5, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=4, Locked=4, Change=0
- LR_std_C0.1: Ref=6, Locked=6, Change=0
- LR_std_C1: Ref=7, Locked=7, Change=0

### cross_project / lift_at_10pct

**Best Overall Model:**
- Reference: AQRPE_v2_balanced (3.028701)
- Locked: AQRPE_v2_balanced (3.046156)
- Identity changed: False

**Best Baseline Model:**
- Reference: ET_leaf5 (3.028701)
- Locked: ET_leaf5 (3.046156)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 2.825839
- Locked value: 2.829612
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 0/8
- Maximum rank change: 0
- Spearman correlation: 1.0000
- Max absolute mean-value change: 0.039746

**Rank Details:**
- AQRPE_v2_balanced: Ref=1, Locked=1, Change=0
- AQRPE_v2_mcc: Ref=2, Locked=2, Change=0
- AQRPE_v2_rank: Ref=3, Locked=3, Change=0
- AQRPE_v2_soft_top3: Ref=5, Locked=5, Change=0
- DT_leaf5: Ref=8, Locked=8, Change=0
- ET_leaf5: Ref=4, Locked=4, Change=0
- LR_std_C0.1: Ref=6, Locked=6, Change=0
- LR_std_C1: Ref=7, Locked=7, Change=0

### cross_project / brier

**Best Overall Model:**
- Reference: AQRPE_v2_balanced (0.162478)
- Locked: AQRPE_v2_mcc (0.161972)
- Identity changed: True

**Best Baseline Model:**
- Reference: ET_leaf5 (0.162478)
- Locked: ET_leaf5 (0.161972)
- Identity changed: False

**Soft-Top-3 Performance:**
- Reference value: 0.181151
- Locked value: 0.180948
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability:**
- Models with changed rank: 4/8
- Maximum rank change: 3
- Spearman correlation: 0.8571
- Max absolute mean-value change: 0.001071

**Rank Details:**
- AQRPE_v2_balanced: Ref=1, Locked=4, Change=3
- AQRPE_v2_mcc: Ref=2, Locked=1, Change=1
- AQRPE_v2_rank: Ref=3, Locked=2, Change=1
- AQRPE_v2_soft_top3: Ref=6, Locked=6, Change=0
- DT_leaf5: Ref=5, Locked=5, Change=0
- ET_leaf5: Ref=4, Locked=3, Change=1
- LR_std_C0.1: Ref=7, Locked=7, Change=0
- LR_std_C1: Ref=8, Locked=8, Change=0

