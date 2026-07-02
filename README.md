# Anonymous Supplementary Package

This clean supplementary package supports the manuscript tables for the AQRPE v2 software-quality prediction study. It is intentionally limited to the files needed to reproduce the current manuscript tables. Prior audit reports, smoke-test outputs, cache files, and previous-stage archives are excluded.

## Directory structure

```text
supplementary_package/
├── README.md
├── requirements.txt
├── data/raw/
│   ├── cm1.csv
│   ├── jm1.csv
│   ├── kc1.csv
│   ├── kc2.csv
│   └── pc1.csv
├── scripts/
│   ├── run_repeated_evaluation.py
│   └── make_manuscript_tables.py
├── results/
│   ├── repeated_all_results.csv
│   ├── repeated_summary_mean_std.csv
│   ├── repeated_results_workbook.xlsx
│   ├── validation_log.csv
│   ├── dataset_profile.csv
│   ├── decision_metadata.json
│   ├── table_within_project_mean_sd.csv
│   ├── table_cross_project_mean_sd.csv
│   └── table_soft_top3_delta_vs_best_baseline.csv
├── docs/
│   └── reproducibility_table_S1.docx
└── inventory/
    └── package_inventory.csv
```

## Reproduction commands

From the `supplementary_package/` directory:

```bash
pip install -r requirements.txt
python scripts/run_repeated_evaluation.py --data_dir data/raw --out_dir results
python scripts/make_manuscript_tables.py --results_dir results --out_dir results
```

The first command regenerates row-level repeated evaluation results, mean/standard-deviation summaries, validation logs, dataset profile, decision metadata, and the workbook under `results/`. The second command regenerates the manuscript table CSV files directly under `results/`.

## Manuscript-table mapping

| Manuscript item | File path |
|---|---|
| Within-project repeated results table | `results/table_within_project_mean_sd.csv` |
| Cross-project repeated results table | `results/table_cross_project_mean_sd.csv` |
| Soft-top-3 versus best-baseline delta table | `results/table_soft_top3_delta_vs_best_baseline.csv` |
| Full row-level repeated results | `results/repeated_all_results.csv` |
| Mean/SD summary | `results/repeated_summary_mean_std.csv` |
| Full workbook | `results/repeated_results_workbook.xlsx` |
| Candidate/threshold validation log | `results/validation_log.csv` |

## Notes

- The five public NASA/PROMISE CSV files are included under `data/raw/`.
- The repeated seeds are `7, 13, 29, 42, 101` by default.
- Test partitions are used only for final evaluation. Candidate selection, ensemble construction, and threshold selection use validation data.
- Old stage folders, previous audit reports, smoke-test outputs, `__pycache__` folders, and `.pyc` files are intentionally not included.
