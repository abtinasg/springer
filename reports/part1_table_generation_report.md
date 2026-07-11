# Part 1 Section 6A: Table Generation Report

## Execution Command
```bash
python scripts/make_manuscript_tables.py --results_dir results/part1_full_reproduction --out_dir results/part1_full_reproduction_tables
```

## Execution Environment
- **Python path**: .venv/bin/python
- **Python version**: 3.13.5
- **pip check**: No broken requirements found.

## Execution Status
- **Success**: Yes
- **Exit Code**: 0

## Generated Tables

### table_within_project_mean_sd.csv
- **Rows**: 8
- **Columns**: 7
- **Size**: 771 bytes
- **Column names**: ['Model', 'MCC', 'AP', 'F1', 'BA', 'P@10%', 'R@10%']
- **Null counts**: 0 (all columns)

### table_cross_project_mean_sd.csv
- **Rows**: 8
- **Columns**: 7
- **Size**: 771 bytes
- **Column names**: ['Model', 'MCC', 'AP', 'F1', 'BA', 'P@10%', 'R@10%']
- **Null counts**: 0 (all columns)

### table_soft_top3_delta_vs_best_baseline.csv
- **Rows**: 16
- **Columns**: 8
- **Size**: 1423 bytes
- **Column names**: ['Setting', 'Metric', 'Direction', 'Soft-top-3 mean', 'Best baseline', 'Best baseline mean', 'Delta', 'AQRPE outcome']
- **Null counts**: 0 (all columns)

## Warnings/Errors
- None
