# Part 1 Section 6D: Result Drift Analysis (Tie-Aware)

## Summary

- **Total setting-metric combinations**: 16
- **Best-overall winner-set changes**: 1
- **Best-overall disjoint winner changes**: 0
- **Best-baseline winner-set changes**: 3
- **Best-baseline disjoint winner changes**: 2
- **Soft-top-3 outcome changes**: 0
- **Combinations with any tie-aware rank change**: 9
- **Minimum tie-aware Spearman correlation**: 0.9036
- **Maximum absolute mean-value change**: 0.111536
  - Location: within_project / lift_at_10pct / DT_leaf5

## Best-Overall Winner-Set Changes

- **cross_project / brier**:
  - Reference: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5']
  - Locked: ['AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5']
  - Overlap: True
  - Disjoint: False

## Best-Baseline Winner-Set Changes

- **within_project / mcc**:
  - Reference: ['LR_std_C0.1']
  - Locked: ['ET_leaf5']
  - Overlap: False
  - Disjoint: True
- **within_project / recall_at_10pct**:
  - Reference: ['ET_leaf5']
  - Locked: ['LR_std_C1', 'ET_leaf5']
  - Overlap: True
  - Disjoint: False
- **within_project / lift_at_10pct**:
  - Reference: ['ET_leaf5']
  - Locked: ['LR_std_C1']
  - Overlap: False
  - Disjoint: True

## Detailed Results by Setting-Metric Combination

### within_project / mcc

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (0.355922)
- Locked: ['AQRPE_v2_rank'] (0.354745)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C0.1'] (0.318350)
- Locked: ['ET_leaf5'] (0.320441)
- Winner set changed: True
- Winner sets overlap: False
- Disjoint winner change: True

**Soft-Top-3 Performance:**
- Reference value: 0.340068
- Locked value: 0.339156
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 4/8
- Maximum rank change: 1.00
- Tie-aware Spearman correlation: 0.9524
- Max absolute mean-value change: 0.006169

**Rank Details:**
- AQRPE_v2_balanced: Ref=7.00, Locked=6.00, Change=1.00
- AQRPE_v2_mcc: Ref=5.00, Locked=5.00, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=4.00, Locked=3.00, Change=1.00
- LR_std_C0.1: Ref=3.00, Locked=4.00, Change=1.00
- LR_std_C1: Ref=6.00, Locked=7.00, Change=1.00

### within_project / avg_precision

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (0.455553)
- Locked: ['AQRPE_v2_rank'] (0.454230)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (0.421389)
- Locked: ['ET_leaf5'] (0.420293)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.440253
- Locked value: 0.440429
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.002617

**Rank Details:**
- AQRPE_v2_balanced: Ref=6.50, Locked=6.50, Change=0.00
- AQRPE_v2_mcc: Ref=6.50, Locked=6.50, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=3.00, Locked=3.00, Change=0.00
- LR_std_C0.1: Ref=4.00, Locked=4.00, Change=0.00
- LR_std_C1: Ref=5.00, Locked=5.00, Change=0.00

### within_project / f1

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (0.448473)
- Locked: ['AQRPE_v2_rank'] (0.447602)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (0.406668)
- Locked: ['ET_leaf5'] (0.408831)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.424034
- Locked value: 0.423754
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.002326

**Rank Details:**
- AQRPE_v2_balanced: Ref=4.00, Locked=4.00, Change=0.00
- AQRPE_v2_mcc: Ref=5.00, Locked=5.00, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=3.00, Locked=3.00, Change=0.00
- LR_std_C0.1: Ref=6.00, Locked=6.00, Change=0.00
- LR_std_C1: Ref=7.00, Locked=7.00, Change=0.00

### within_project / balanced_accuracy

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (0.724039)
- Locked: ['AQRPE_v2_rank'] (0.723023)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C1'] (0.689859)
- Locked: ['LR_std_C1'] (0.689859)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.694637
- Locked value: 0.694907
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.002792

**Rank Details:**
- AQRPE_v2_balanced: Ref=6.00, Locked=6.00, Change=0.00
- AQRPE_v2_mcc: Ref=7.00, Locked=7.00, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=5.00, Locked=5.00, Change=0.00
- LR_std_C0.1: Ref=4.00, Locked=4.00, Change=0.00
- LR_std_C1: Ref=3.00, Locked=3.00, Change=0.00

### within_project / precision_at_10pct

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (0.477887)
- Locked: ['AQRPE_v2_rank'] (0.473460)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C1'] (0.455959)
- Locked: ['LR_std_C1'] (0.455959)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.458026
- Locked value: 0.457398
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 2/8
- Maximum rank change: 1.00
- Tie-aware Spearman correlation: 0.9759
- Max absolute mean-value change: 0.008312

**Rank Details:**
- AQRPE_v2_balanced: Ref=6.50, Locked=6.50, Change=0.00
- AQRPE_v2_mcc: Ref=6.50, Locked=6.50, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=4.00, Locked=5.00, Change=1.00
- LR_std_C0.1: Ref=5.00, Locked=4.00, Change=1.00
- LR_std_C1: Ref=3.00, Locked=3.00, Change=0.00

### within_project / recall_at_10pct

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (0.372366)
- Locked: ['AQRPE_v2_rank'] (0.369520)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (0.345597)
- Locked: ['LR_std_C1', 'ET_leaf5'] (0.341520)
- Winner set changed: True
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.361307
- Locked value: 0.360881
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 2/8
- Maximum rank change: 0.50
- Tie-aware Spearman correlation: 0.9940
- Max absolute mean-value change: 0.011430

**Rank Details:**
- AQRPE_v2_balanced: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_mcc: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=3.00, Locked=3.50, Change=0.50
- LR_std_C0.1: Ref=7.00, Locked=7.00, Change=0.00
- LR_std_C1: Ref=4.00, Locked=3.50, Change=0.50

### within_project / lift_at_10pct

**Best Overall Models:**
- Reference: ['AQRPE_v2_rank'] (3.636140)
- Locked: ['AQRPE_v2_rank'] (3.607964)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (3.368219)
- Locked: ['LR_std_C1'] (3.336150)
- Winner set changed: True
- Winner sets overlap: False
- Disjoint winner change: True

**Soft-Top-3 Performance:**
- Reference value: 3.527434
- Locked value: 3.523288
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 2/8
- Maximum rank change: 1.00
- Tie-aware Spearman correlation: 0.9759
- Max absolute mean-value change: 0.111536

**Rank Details:**
- AQRPE_v2_balanced: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_mcc: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_rank: Ref=1.00, Locked=1.00, Change=0.00
- AQRPE_v2_soft_top3: Ref=2.00, Locked=2.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=3.00, Locked=4.00, Change=1.00
- LR_std_C0.1: Ref=7.00, Locked=7.00, Change=0.00
- LR_std_C1: Ref=4.00, Locked=3.00, Change=1.00

### within_project / brier

**Best Overall Models:**
- Reference: ['DT_leaf5'] (0.134191)
- Locked: ['DT_leaf5'] (0.133357)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['DT_leaf5'] (0.134191)
- Locked: ['DT_leaf5'] (0.133357)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.148333
- Locked value: 0.146873
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 2/8
- Maximum rank change: 1.00
- Tie-aware Spearman correlation: 0.9756
- Max absolute mean-value change: 0.001460

**Rank Details:**
- AQRPE_v2_balanced: Ref=3.00, Locked=3.00, Change=0.00
- AQRPE_v2_mcc: Ref=3.00, Locked=4.00, Change=1.00
- AQRPE_v2_rank: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_soft_top3: Ref=3.00, Locked=2.00, Change=1.00
- DT_leaf5: Ref=1.00, Locked=1.00, Change=0.00
- ET_leaf5: Ref=5.50, Locked=5.50, Change=0.00
- LR_std_C0.1: Ref=8.00, Locked=8.00, Change=0.00
- LR_std_C1: Ref=7.00, Locked=7.00, Change=0.00

### cross_project / mcc

**Best Overall Models:**
- Reference: ['AQRPE_v2_soft_top3'] (0.293463)
- Locked: ['AQRPE_v2_soft_top3'] (0.293438)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C0.1'] (0.286870)
- Locked: ['LR_std_C0.1'] (0.286870)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.293463
- Locked value: 0.293438
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 5/8
- Maximum rank change: 2.00
- Tie-aware Spearman correlation: 0.9036
- Max absolute mean-value change: 0.005379

**Rank Details:**
- AQRPE_v2_balanced: Ref=4.50, Locked=3.50, Change=1.00
- AQRPE_v2_mcc: Ref=6.00, Locked=7.00, Change=1.00
- AQRPE_v2_rank: Ref=7.00, Locked=6.00, Change=1.00
- AQRPE_v2_soft_top3: Ref=1.00, Locked=1.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=4.50, Locked=3.50, Change=1.00
- LR_std_C0.1: Ref=2.00, Locked=2.00, Change=0.00
- LR_std_C1: Ref=3.00, Locked=5.00, Change=2.00

### cross_project / avg_precision

**Best Overall Models:**
- Reference: ['AQRPE_v2_soft_top3'] (0.359273)
- Locked: ['AQRPE_v2_soft_top3'] (0.358844)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C1'] (0.356339)
- Locked: ['LR_std_C1'] (0.356312)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.359273
- Locked value: 0.358844
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.000762

**Rank Details:**
- AQRPE_v2_balanced: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_mcc: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_rank: Ref=5.50, Locked=5.50, Change=0.00
- AQRPE_v2_soft_top3: Ref=1.00, Locked=1.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=5.50, Locked=5.50, Change=0.00
- LR_std_C0.1: Ref=3.00, Locked=3.00, Change=0.00
- LR_std_C1: Ref=2.00, Locked=2.00, Change=0.00

### cross_project / f1

**Best Overall Models:**
- Reference: ['AQRPE_v2_soft_top3'] (0.393335)
- Locked: ['AQRPE_v2_soft_top3'] (0.392806)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C0.1'] (0.387321)
- Locked: ['LR_std_C0.1'] (0.387321)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.393335
- Locked value: 0.392806
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 3/8
- Maximum rank change: 2.00
- Tie-aware Spearman correlation: 0.9222
- Max absolute mean-value change: 0.010820

**Rank Details:**
- AQRPE_v2_balanced: Ref=4.50, Locked=5.00, Change=0.50
- AQRPE_v2_mcc: Ref=7.00, Locked=7.00, Change=0.00
- AQRPE_v2_rank: Ref=6.00, Locked=4.00, Change=2.00
- AQRPE_v2_soft_top3: Ref=1.00, Locked=1.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=4.50, Locked=6.00, Change=1.50
- LR_std_C0.1: Ref=2.00, Locked=2.00, Change=0.00
- LR_std_C1: Ref=3.00, Locked=3.00, Change=0.00

### cross_project / balanced_accuracy

**Best Overall Models:**
- Reference: ['AQRPE_v2_soft_top3'] (0.685915)
- Locked: ['AQRPE_v2_soft_top3'] (0.685664)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['LR_std_C1'] (0.674898)
- Locked: ['LR_std_C1'] (0.674898)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.685915
- Locked value: 0.685664
- Reference vs best baseline: better
- Locked vs best baseline: better
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 3/8
- Maximum rank change: 1.00
- Tie-aware Spearman correlation: 0.9818
- Max absolute mean-value change: 0.005132

**Rank Details:**
- AQRPE_v2_balanced: Ref=5.00, Locked=4.00, Change=1.00
- AQRPE_v2_mcc: Ref=7.00, Locked=7.00, Change=0.00
- AQRPE_v2_rank: Ref=5.00, Locked=5.50, Change=0.50
- AQRPE_v2_soft_top3: Ref=1.00, Locked=1.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=5.00, Locked=5.50, Change=0.50
- LR_std_C0.1: Ref=3.00, Locked=3.00, Change=0.00
- LR_std_C1: Ref=2.00, Locked=2.00, Change=0.00

### cross_project / precision_at_10pct

**Best Overall Models:**
- Reference: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (0.414298)
- Locked: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (0.413764)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (0.414298)
- Locked: ['ET_leaf5'] (0.413764)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.400087
- Locked value: 0.400436
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.003380

**Rank Details:**
- AQRPE_v2_balanced: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_mcc: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_rank: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_soft_top3: Ref=6.50, Locked=6.50, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=2.50, Locked=2.50, Change=0.00
- LR_std_C0.1: Ref=5.00, Locked=5.00, Change=0.00
- LR_std_C1: Ref=6.50, Locked=6.50, Change=0.00

### cross_project / recall_at_10pct

**Best Overall Models:**
- Reference: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (0.304315)
- Locked: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (0.306049)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (0.304315)
- Locked: ['ET_leaf5'] (0.306049)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.283987
- Locked value: 0.284368
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.003994

**Rank Details:**
- AQRPE_v2_balanced: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_mcc: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_rank: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_soft_top3: Ref=5.00, Locked=5.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=2.50, Locked=2.50, Change=0.00
- LR_std_C0.1: Ref=6.00, Locked=6.00, Change=0.00
- LR_std_C1: Ref=7.00, Locked=7.00, Change=0.00

### cross_project / lift_at_10pct

**Best Overall Models:**
- Reference: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (3.028701)
- Locked: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (3.046156)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (3.028701)
- Locked: ['ET_leaf5'] (3.046156)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 2.825839
- Locked value: 2.829612
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 0/8
- Maximum rank change: 0.00
- Tie-aware Spearman correlation: 1.0000
- Max absolute mean-value change: 0.039746

**Rank Details:**
- AQRPE_v2_balanced: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_mcc: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_rank: Ref=2.50, Locked=2.50, Change=0.00
- AQRPE_v2_soft_top3: Ref=5.00, Locked=5.00, Change=0.00
- DT_leaf5: Ref=8.00, Locked=8.00, Change=0.00
- ET_leaf5: Ref=2.50, Locked=2.50, Change=0.00
- LR_std_C0.1: Ref=6.00, Locked=6.00, Change=0.00
- LR_std_C1: Ref=7.00, Locked=7.00, Change=0.00

### cross_project / brier

**Best Overall Models:**
- Reference: ['AQRPE_v2_balanced', 'AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (0.162478)
- Locked: ['AQRPE_v2_mcc', 'AQRPE_v2_rank', 'ET_leaf5'] (0.161972)
- Winner set changed: True
- Winner sets overlap: True
- Disjoint winner change: False

**Best Baseline Models:**
- Reference: ['ET_leaf5'] (0.162478)
- Locked: ['ET_leaf5'] (0.161972)
- Winner set changed: False
- Winner sets overlap: True
- Disjoint winner change: False

**Soft-Top-3 Performance:**
- Reference value: 0.181151
- Locked value: 0.180948
- Reference vs best baseline: worse
- Locked vs best baseline: worse
- Outcome changed: False

**Rank Stability (Tie-Aware):**
- Models with changed rank: 4/8
- Maximum rank change: 1.50
- Tie-aware Spearman correlation: 0.9618
- Max absolute mean-value change: 0.001071

**Rank Details:**
- AQRPE_v2_balanced: Ref=2.50, Locked=4.00, Change=1.50
- AQRPE_v2_mcc: Ref=2.50, Locked=2.00, Change=0.50
- AQRPE_v2_rank: Ref=2.50, Locked=2.00, Change=0.50
- AQRPE_v2_soft_top3: Ref=6.00, Locked=6.00, Change=0.00
- DT_leaf5: Ref=5.00, Locked=5.00, Change=0.00
- ET_leaf5: Ref=2.50, Locked=2.00, Change=0.50
- LR_std_C0.1: Ref=7.00, Locked=7.00, Change=0.00
- LR_std_C1: Ref=8.00, Locked=8.00, Change=0.00

