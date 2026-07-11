# Part 2 Section 3D: Soft-Top-3 Seed Stability Analysis

## Canonical Verification

- Manifest validation status: all_checks_passed
- Repeated results SHA-256 verified: True
- Validation log SHA-256 verified: True
- Evaluation script SHA-256 verified: True

## Event Provenance Validation

- **Events checked:** 50
- **Canonical event mismatches:** 0
- **Validation ranking mismatches:** 0
- **Score mismatches:** 0
- **Cutoff gap mismatches:** 0

## Stability Definitions

- **Exact order pairwise agreement:** Proportion of seed pairs with identical selected order
- **Exact membership pairwise agreement:** Proportion of seed pairs with identical membership set
- **Mean pairwise Jaccard:** Mean Jaccard similarity between membership sets across seed pairs
- **Mean full-rank position agreement:** Mean proportion of candidates in same position across seed pairs
- **Mean pairwise Kendall tau:** Mean Kendall tau correlation between full rankings across seed pairs
- **Mean pairwise Kendall similarity:** Mean normalized Kendall similarity (tau+1)/2 across seed pairs

## Order Stability by Project and Setting

| Experiment | Project | Distinct Orders | Modal Order(s) | Modal Count | Modal Prop | Unanimous |
|------------|---------|-----------------|----------------|-------------|------------|-----------|
| cross_project | CM1 | 2 | ET_leaf5|LR_std_C0.1|LR_std_C1 | 3 | 0.600 | False |
| cross_project | JM1 | 3 | ET_leaf5|LR_std_C1|LR_std_C0.1 | 3 | 0.600 | False |
| cross_project | KC1 | 2 | ET_leaf5|LR_std_C0.1|LR_std_C1 | 4 | 0.800 | False |
| cross_project | KC2 | 2 | ET_leaf5|LR_std_C1|LR_std_C0.1 | 4 | 0.800 | False |
| cross_project | PC1 | 2 | ET_leaf5|LR_std_C0.1|LR_std_C1 | 3 | 0.600 | False |
| within_project | CM1 | 4 | ET_leaf5|LR_std_C0.1|LR_std_C1 | 2 | 0.400 | False |
| within_project | JM1 | 2 | ET_leaf5|LR_std_C1|LR_std_C0.1 | 3 | 0.600 | False |
| within_project | KC1 | 5 | LR_std_C1|ET_leaf5|LR_std_C0.1|OR|DT_leaf5|ET_leaf5|LR_std_C1|OR|ET_leaf5|LR_std_C0.1|DT_leaf5|OR|ET_leaf5|LR_std_C1|LR_std_C0.1|OR|ET_leaf5|LR_std_C1|DT_leaf5 | 1 | 0.200 | False |
| within_project | KC2 | 4 | ET_leaf5|LR_std_C1|LR_std_C0.1 | 2 | 0.400 | False |
| within_project | PC1 | 3 | DT_leaf5|ET_leaf5|LR_std_C1|OR|ET_leaf5|LR_std_C0.1|DT_leaf5 | 2 | 0.400 | False |

## Membership Stability by Project and Setting

| Experiment | Project | Distinct Sets | Modal Set(s) | Modal Count | Modal Prop | Modal Excluded Candidate(s) | Unanimous |
|------------|---------|---------------|--------------|-------------|------------|---------------------------|-----------|
| cross_project | CM1 | 1 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 5 | 1.000 | DT_leaf5 | True |
| cross_project | JM1 | 1 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 5 | 1.000 | DT_leaf5 | True |
| cross_project | KC1 | 1 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 5 | 1.000 | DT_leaf5 | True |
| cross_project | KC2 | 1 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 5 | 1.000 | DT_leaf5 | True |
| cross_project | PC1 | 1 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 5 | 1.000 | DT_leaf5 | True |
| within_project | CM1 | 2 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 4 | 0.800 | DT_leaf5 | False |
| within_project | JM1 | 1 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 5 | 1.000 | DT_leaf5 | True |
| within_project | KC1 | 3 | LR_std_C1|DT_leaf5|ET_leaf5|OR|LR_std_C0.1|LR_std_C1|ET_leaf5 | 2 | 0.400 | LR_std_C0.1|OR|DT_leaf5 | False |
| within_project | KC2 | 2 | LR_std_C0.1|LR_std_C1|ET_leaf5 | 4 | 0.800 | DT_leaf5 | False |
| within_project | PC1 | 2 | LR_std_C1|DT_leaf5|ET_leaf5 | 3 | 0.600 | LR_std_C0.1 | False |

## Pairwise Order and Membership Agreement

| Experiment | Project | Exact Order | Exact Membership | Jaccard | Position Agreement | Kendall Tau | Kendall Similarity |
|------------|---------|-------------|------------------|---------|-------------------|-------------|-------------------|
| cross_project | CM1 | 0.400 | 1.000 | 1.000 | 0.700 | 0.800 | 0.900 |
| cross_project | JM1 | 0.300 | 1.000 | 1.000 | 0.625 | 0.533 | 0.767 |
| cross_project | KC1 | 0.600 | 1.000 | 1.000 | 0.800 | 0.867 | 0.933 |
| cross_project | KC2 | 0.600 | 1.000 | 1.000 | 0.800 | 0.867 | 0.933 |
| cross_project | PC1 | 0.400 | 1.000 | 1.000 | 0.700 | 0.800 | 0.900 |
| within_project | CM1 | 0.100 | 0.600 | 0.800 | 0.325 | -0.000 | 0.500 |
| within_project | JM1 | 0.400 | 1.000 | 1.000 | 0.700 | 0.800 | 0.900 |
| within_project | KC1 | 0.000 | 0.200 | 0.600 | 0.225 | 0.200 | 0.600 |
| within_project | KC2 | 0.100 | 0.600 | 0.800 | 0.425 | 0.267 | 0.633 |
| within_project | PC1 | 0.200 | 0.400 | 0.700 | 0.350 | 0.267 | 0.633 |

## Overall Summary

- **Groups:** 10
- **Unanimous order groups:** 0 (0.000)
- **Unanimous membership groups:** 6 (0.600)
- **Mean distinct orders:** 2.900
- **Mean distinct membership sets:** 1.500
- **Mean exact order agreement:** 0.310
- **Mean exact membership agreement:** 0.780
- **Mean pairwise Jaccard:** 0.890
- **Mean full-rank position agreement:** 0.565
- **Mean Kendall tau:** 0.540
- **Mean Kendall similarity:** 0.770
- **Minimum cutoff score gap:** 0.000574

## Within-Project Summary

- **Groups:** 5
- **Unanimous order groups:** 0 (0.000)
- **Unanimous membership groups:** 1 (0.200)
- **Mean exact order agreement:** 0.160
- **Mean exact membership agreement:** 0.560
- **Mean pairwise Jaccard:** 0.780
- **Mean Kendall similarity:** 0.653

## Cross-Project Summary

- **Groups:** 5
- **Unanimous order groups:** 0 (0.000)
- **Unanimous membership groups:** 5 (1.000)
- **Mean exact order agreement:** 0.460
- **Mean exact membership agreement:** 1.000
- **Mean pairwise Jaccard:** 1.000
- **Mean Kendall similarity:** 0.887

## Special Stability Groups

### Unanimous Order Groups (0)


### Unanimous Membership but Nonunanimous Order Groups (6)

- cross_project/CM1
- cross_project/JM1
- cross_project/KC1
- cross_project/KC2
- cross_project/PC1
- within_project/JM1

### Order Modal Tie Groups (2)

- within_project/KC1
- within_project/PC1

### Membership Modal Tie Groups (1)

- within_project/KC1

### Minimum Order Agreement Groups (agreement=0.000)

- within_project/KC1

### Minimum Membership Agreement Groups (agreement=0.200)

- within_project/KC1

### Minimum Kendall Similarity Groups (similarity=0.500)

- within_project/CM1

## Final Validation Evidence

### Validation Checks

- **canonical_verification_passed:** True
- **event_provenance_passed:** True
- **modal_order_sorting_passed:** True
- **membership_mapping_passed:** True
- **modal_excluded_mapping_passed:** True
- **pairwise_count_formula_passed:** True
- **jaccard_identity_passed:** True
- **unanimous_bidirectional_checks_passed:** True
- **order_count_structure_passed:** True
- **membership_count_structure_passed:** True
- **group_validation_passed:** True
- **summary_validation_passed:** True
- **validation_evidence_integrity_passed:** True

### Validation Evidence

- **modal_order_groups_checked:** 10
- **modal_membership_groups_checked:** 10
- **pairwise_formula_groups_checked:** 10
- **jaccard_identity_groups_checked:** 10
- **unanimous_groups_checked:** 10
- **order_count_groups_checked:** 10
- **membership_count_groups_checked:** 10
- **group_structure_rows_checked:** 10
- **group_seed_count_rows_checked:** 10
- **group_domain_rows_checked:** 10
- **group_kendall_rows_checked:** 10
- **group_cutoff_rows_checked:** 10
- **summary_rows_reconstructed:** 3
- **summary_fields_checked_per_row:** 20
- **summary_total_field_comparisons:** 60
- **events_checked:** 50
- **order_count_rows:** 240
- **membership_count_rows:** 40
- **group_rows:** 10
- **summary_rows:** 3

## Interpretation Limits

These metrics describe categorical membership and ordering agreement of Soft-top-3 selections across five seeds.

They are descriptive, not inferential, and do not establish predictive-performance stability, statistical significance, or superiority.

Membership stability and ordering stability are distinct: identical candidate membership does not necessarily imply identical candidate ordering.
