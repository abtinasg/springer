#!/usr/bin/env python3
"""
Part 1 Section 6E: Build canonical reproduction manifest
Establishes computational provenance and freezes the canonical result set.
"""

import hashlib
import json
from pathlib import Path
import pandas as pd
import openpyxl

# Base directory for portable paths
BASE_DIR = Path(__file__).resolve().parents[1]

# Paths
CANONICAL_RESULT_DIR = BASE_DIR / "results" / "part1_full_reproduction"
CANONICAL_TABLE_DIR = BASE_DIR / "results" / "part1_full_reproduction_tables"
LEGACY_RESULT_DIR = BASE_DIR / "results"
REPORTS_DIR = BASE_DIR / "reports"

# Output files
OUTPUT_JSON = REPORTS_DIR / "part1_canonical_manifest.json"
OUTPUT_MD = REPORTS_DIR / "part1_canonical_manifest.md"

# Input files to verify
INPUT_FILES = {
    "requirements_locked.txt": BASE_DIR / "requirements_locked.txt",
    "run_repeated_evaluation.py": BASE_DIR / "scripts" / "run_repeated_evaluation.py",
    "make_manuscript_tables.py": BASE_DIR / "scripts" / "make_manuscript_tables.py",
}

# Raw datasets
RAW_DATASETS = {
    "cm1.csv": BASE_DIR / "data" / "raw" / "cm1.csv",
    "jm1.csv": BASE_DIR / "data" / "raw" / "jm1.csv",
    "kc1.csv": BASE_DIR / "data" / "raw" / "kc1.csv",
    "kc2.csv": BASE_DIR / "data" / "raw" / "kc2.csv",
    "pc1.csv": BASE_DIR / "data" / "raw" / "pc1.csv",
}

# Canonical output files
CANONICAL_OUTPUTS = {
    "dataset_profile.csv": CANONICAL_RESULT_DIR / "dataset_profile.csv",
    "decision_metadata.json": CANONICAL_RESULT_DIR / "decision_metadata.json",
    "repeated_all_results.csv": CANONICAL_RESULT_DIR / "repeated_all_results.csv",
    "repeated_results_workbook.xlsx": CANONICAL_RESULT_DIR / "repeated_results_workbook.xlsx",
    "repeated_summary_mean_std.csv": CANONICAL_RESULT_DIR / "repeated_summary_mean_std.csv",
    "validation_log.csv": CANONICAL_RESULT_DIR / "validation_log.csv",
}

# Canonical table files
CANONICAL_TABLES = {
    "table_within_project_mean_sd.csv": CANONICAL_TABLE_DIR / "table_within_project_mean_sd.csv",
    "table_cross_project_mean_sd.csv": CANONICAL_TABLE_DIR / "table_cross_project_mean_sd.csv",
    "table_soft_top3_delta_vs_best_baseline.csv": CANONICAL_TABLE_DIR / "table_soft_top3_delta_vs_best_baseline.csv",
}

# Table keys for duplicate checking
TABLE_KEYS = {
    "table_within_project_mean_sd.csv": ["Model"],
    "table_cross_project_mean_sd.csv": ["Model"],
    "table_soft_top3_delta_vs_best_baseline.csv": ["Setting", "Metric"],
}


def compute_sha256(path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_info(path):
    """Get basic file information."""
    if not path.exists():
        return {
            "exists": False,
            "sha256": None,
            "size": None,
        }
    
    return {
        "exists": True,
        "sha256": compute_sha256(path),
        "size": path.stat().st_size,
    }


def get_csv_info(path):
    """Get detailed CSV information."""
    if not path.exists():
        return {
            "exists": False,
            "sha256": None,
            "size": None,
            "row_count": None,
            "column_count": None,
            "column_names": None,
            "null_count": None,
        }
    
    df = pd.read_csv(path)
    basic_info = get_file_info(path)
    
    return {
        **basic_info,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "column_names": list(df.columns),
        "null_count": int(df.isnull().sum().sum()),
    }


def get_csv_with_duplicates_info(path, key_columns=None):
    """Get detailed CSV information with duplicate checking."""
    if not path.exists():
        return {
            "exists": False,
            "sha256": None,
            "size": None,
            "row_count": None,
            "column_count": None,
            "column_names": None,
            "duplicate_full_rows": None,
            "total_null_count": None,
            "duplicate_key_count": None,
        }
    
    df = pd.read_csv(path)
    basic_info = get_file_info(path)
    
    result = {
        **basic_info,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "column_names": list(df.columns),
        "duplicate_full_rows": int(df.duplicated().sum()),
        "total_null_count": int(df.isnull().sum().sum()),
    }
    
    if key_columns:
        result["duplicate_key_count"] = int(df.duplicated(subset=key_columns).sum())
    
    return result


def get_json_info(path):
    """Get detailed JSON information."""
    if not path.exists():
        return {
            "exists": False,
            "sha256": None,
            "size": None,
            "top_level_fields": None,
        }
    
    with open(path, "r") as f:
        data = json.load(f)
    
    basic_info = get_file_info(path)
    
    result = {
        **basic_info,
        "top_level_fields": list(data.keys()) if isinstance(data, dict) else None,
    }
    
    # Add specific fields for decision_metadata.json
    if "decision_metadata.json" in str(path):
        result["stage"] = data.get("stage")
        result["seeds"] = data.get("seeds")
        result["rows"] = data.get("rows")
    
    return result


def get_excel_info(path):
    """Get detailed Excel information."""
    if not path.exists():
        return {
            "exists": False,
            "sha256": None,
            "size": None,
            "sheet_names": None,
        }
    
    basic_info = get_file_info(path)
    
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    
    sheets_info = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheets_info[sheet_name] = {
            "row_count": int(ws.max_row),
            "column_count": int(ws.max_column),
        }
    
    wb.close()
    
    return {
        **basic_info,
        "sheet_names": list(wb.sheetnames),
        "sheets": sheets_info,
    }


def validate_reports():
    """Validate existing reports before building manifest."""
    print("Validating reports...")
    
    # Check reproduction comparison
    repro_path = REPORTS_DIR / "part1_reproduction_comparison.json"
    if not repro_path.exists():
        raise ValueError(f"Missing report: {repro_path}")
    
    with open(repro_path, "r") as f:
        repro_data = json.load(f)
    
    if repro_data.get("overall_status") != "materially_different":
        raise ValueError(f"part1_reproduction_comparison overall_status is '{repro_data.get('overall_status')}', expected 'materially_different'")
    
    # Check repeatability comparison
    repeat_path = REPORTS_DIR / "part1_repeatability_comparison.json"
    if not repeat_path.exists():
        raise ValueError(f"Missing report: {repeat_path}")
    
    with open(repeat_path, "r") as f:
        repeat_data = json.load(f)
    
    if repeat_data.get("overall_status") != "numerically_equivalent":
        raise ValueError(f"part1_repeatability_comparison overall_status is '{repeat_data.get('overall_status')}', expected 'numerically_equivalent'")
    
    # Check result drift analysis
    drift_path = REPORTS_DIR / "part1_result_drift_analysis.json"
    if not drift_path.exists():
        raise ValueError(f"Missing report: {drift_path}")
    
    with open(drift_path, "r") as f:
        drift_data = json.load(f)
    
    summary = drift_data.get("summary", {})
    if summary.get("total_combinations") != 16:
        raise ValueError(f"part1_result_drift_analysis total_combinations is {summary.get('total_combinations')}, expected 16")
    
    if len(summary.get("soft_top3_outcome_changes", [])) != 0:
        raise ValueError(f"part1_result_drift_analysis has {len(summary.get('soft_top3_outcome_changes', []))} soft_top3_outcome_changes, expected 0")
    
    if len(summary.get("best_overall_disjoint_winner_changes", [])) != 0:
        raise ValueError(f"part1_result_drift_analysis has {len(summary.get('best_overall_disjoint_winner_changes', []))} best_overall_disjoint_winner_changes, expected 0")
    
    # Check provenance audit
    audit_path = REPORTS_DIR / "part1_reference_provenance_audit.md"
    if not audit_path.exists():
        raise ValueError(f"Missing report: {audit_path}")
    
    with open(audit_path, "r") as f:
        audit_content = f.read()
    
    if "The exact executable script that generated the reference results has not yet been identified" not in audit_content:
        raise ValueError("part1_reference_provenance_audit.md does not contain the expected provenance statement")
    
    print("All validation checks passed.")


def validate_manifest_inventory(manifest):
    """Validate the complete manifest inventory with strict checks."""
    print("Validating manifest inventory...")
    
    # Validate environment and code files
    print("  Checking environment and code files...")
    for name, info in manifest["environment_and_code_files"].items():
        if not info["exists"]:
            raise ValueError(f"Environment/code file missing: {name}")
        if not info["sha256"]:
            raise ValueError(f"Environment/code file has no SHA-256: {name}")
        if not info["size"] or info["size"] <= 0:
            raise ValueError(f"Environment/code file has invalid size: {name}")
    
    # Validate raw datasets
    print("  Checking raw datasets...")
    expected_datasets = {
        "cm1.csv": {"rows": 498, "cols": 22},
        "jm1.csv": {"rows": 13204, "cols": 22},
        "kc1.csv": {"rows": 2109, "cols": 22},
        "kc2.csv": {"rows": 522, "cols": 22},
        "pc1.csv": {"rows": 1109, "cols": 22},
    }
    
    for name, info in manifest["raw_datasets"].items():
        if not info["exists"]:
            raise ValueError(f"Raw dataset missing: {name}")
        if not info["sha256"]:
            raise ValueError(f"Raw dataset has no SHA-256: {name}")
        if not info["size"] or info["size"] <= 0:
            raise ValueError(f"Raw dataset has invalid size: {name}")
        if info["null_count"] != 0:
            raise ValueError(f"Raw dataset has null values: {name} (null_count={info['null_count']})")
        
        if name in expected_datasets:
            expected = expected_datasets[name]
            if info["row_count"] != expected["rows"]:
                raise ValueError(f"Raw dataset row count mismatch: {name} (expected {expected['rows']}, got {info['row_count']})")
            if info["column_count"] != expected["cols"]:
                raise ValueError(f"Raw dataset column count mismatch: {name} (expected {expected['cols']}, got {info['column_count']})")
    
    # Validate canonical outputs
    print("  Checking canonical reproduction outputs...")
    
    # dataset_profile.csv
    dp_info = manifest["canonical_reproduction_outputs"]["dataset_profile.csv"]
    if not dp_info["exists"]:
        raise ValueError("dataset_profile.csv missing")
    if not dp_info["sha256"]:
        raise ValueError("dataset_profile.csv has no SHA-256")
    if not dp_info["size"] or dp_info["size"] <= 0:
        raise ValueError("dataset_profile.csv has invalid size")
    if dp_info["row_count"] != 5:
        raise ValueError(f"dataset_profile.csv row count mismatch (expected 5, got {dp_info['row_count']})")
    if dp_info["column_count"] != 5:
        raise ValueError(f"dataset_profile.csv column count mismatch (expected 5, got {dp_info['column_count']})")
    if dp_info["duplicate_full_rows"] != 0:
        raise ValueError(f"dataset_profile.csv has duplicate rows (count={dp_info['duplicate_full_rows']})")
    if dp_info["total_null_count"] != 0:
        raise ValueError(f"dataset_profile.csv has null values (count={dp_info['total_null_count']})")
    
    # repeated_all_results.csv
    rar_info = manifest["canonical_reproduction_outputs"]["repeated_all_results.csv"]
    if not rar_info["exists"]:
        raise ValueError("repeated_all_results.csv missing")
    if not rar_info["sha256"]:
        raise ValueError("repeated_all_results.csv has no SHA-256")
    if not rar_info["size"] or rar_info["size"] <= 0:
        raise ValueError("repeated_all_results.csv has invalid size")
    if rar_info["row_count"] != 400:
        raise ValueError(f"repeated_all_results.csv row count mismatch (expected 400, got {rar_info['row_count']})")
    if rar_info["column_count"] != 22:
        raise ValueError(f"repeated_all_results.csv column count mismatch (expected 22, got {rar_info['column_count']})")
    if rar_info["duplicate_full_rows"] != 0:
        raise ValueError(f"repeated_all_results.csv has duplicate rows (count={rar_info['duplicate_full_rows']})")
    if rar_info["total_null_count"] != 0:
        raise ValueError(f"repeated_all_results.csv has null values (count={rar_info['total_null_count']})")
    
    # repeated_summary_mean_std.csv
    rsms_info = manifest["canonical_reproduction_outputs"]["repeated_summary_mean_std.csv"]
    if not rsms_info["exists"]:
        raise ValueError("repeated_summary_mean_std.csv missing")
    if not rsms_info["sha256"]:
        raise ValueError("repeated_summary_mean_std.csv has no SHA-256")
    if not rsms_info["size"] or rsms_info["size"] <= 0:
        raise ValueError("repeated_summary_mean_std.csv has invalid size")
    if rsms_info["row_count"] != 16:
        raise ValueError(f"repeated_summary_mean_std.csv row count mismatch (expected 16, got {rsms_info['row_count']})")
    if rsms_info["column_count"] != 52:
        raise ValueError(f"repeated_summary_mean_std.csv column count mismatch (expected 52, got {rsms_info['column_count']})")
    if rsms_info["duplicate_full_rows"] != 0:
        raise ValueError(f"repeated_summary_mean_std.csv has duplicate rows (count={rsms_info['duplicate_full_rows']})")
    if rsms_info["total_null_count"] != 0:
        raise ValueError(f"repeated_summary_mean_std.csv has null values (count={rsms_info['total_null_count']})")
    
    # validation_log.csv
    vl_info = manifest["canonical_reproduction_outputs"]["validation_log.csv"]
    if not vl_info["exists"]:
        raise ValueError("validation_log.csv missing")
    if not vl_info["sha256"]:
        raise ValueError("validation_log.csv has no SHA-256")
    if not vl_info["size"] or vl_info["size"] <= 0:
        raise ValueError("validation_log.csv has invalid size")
    if vl_info["row_count"] != 600:
        raise ValueError(f"validation_log.csv row count mismatch (expected 600, got {vl_info['row_count']})")
    if vl_info["column_count"] != 21:
        raise ValueError(f"validation_log.csv column count mismatch (expected 21, got {vl_info['column_count']})")
    if vl_info["duplicate_full_rows"] != 0:
        raise ValueError(f"validation_log.csv has duplicate rows (count={vl_info['duplicate_full_rows']})")
    if vl_info["total_null_count"] != 0:
        raise ValueError(f"validation_log.csv has null values (count={vl_info['total_null_count']})")
    
    # decision_metadata.json
    dm_info = manifest["canonical_reproduction_outputs"]["decision_metadata.json"]
    if not dm_info["exists"]:
        raise ValueError("decision_metadata.json missing")
    if not dm_info["sha256"]:
        raise ValueError("decision_metadata.json has no SHA-256")
    if not dm_info["size"] or dm_info["size"] <= 0:
        raise ValueError("decision_metadata.json has invalid size")
    if dm_info["stage"] != "Stage-43 clean supplementary reproduction script":
        raise ValueError(f"decision_metadata.json stage mismatch (expected 'Stage-43 clean supplementary reproduction script', got '{dm_info['stage']}')")
    if dm_info["seeds"] != [7, 13, 29, 42, 101]:
        raise ValueError(f"decision_metadata.json seeds mismatch (expected [7, 13, 29, 42, 101], got {dm_info['seeds']})")
    if dm_info["rows"] != 400:
        raise ValueError(f"decision_metadata.json rows mismatch (expected 400, got {dm_info['rows']})")
    
    # repeated_results_workbook.xlsx
    wb_info = manifest["canonical_reproduction_outputs"]["repeated_results_workbook.xlsx"]
    if not wb_info["exists"]:
        raise ValueError("repeated_results_workbook.xlsx missing")
    if not wb_info["sha256"]:
        raise ValueError("repeated_results_workbook.xlsx has no SHA-256")
    if not wb_info["size"] or wb_info["size"] <= 0:
        raise ValueError("repeated_results_workbook.xlsx has invalid size")
    
    expected_sheets = ["Dataset_Profile", "All_Results", "Summary_Mean_SD", "Validation_Log"]
    if wb_info["sheet_names"] != expected_sheets:
        raise ValueError(f"repeated_results_workbook.xlsx sheet names mismatch (expected {expected_sheets}, got {wb_info['sheet_names']})")
    
    expected_sheet_dims = {
        "Dataset_Profile": {"rows": 6, "cols": 5},
        "All_Results": {"rows": 401, "cols": 22},
        "Summary_Mean_SD": {"rows": 17, "cols": 52},
        "Validation_Log": {"rows": 601, "cols": 21},
    }
    
    for sheet_name, dims in expected_sheet_dims.items():
        if sheet_name not in wb_info["sheets"]:
            raise ValueError(f"repeated_results_workbook.xlsx missing sheet: {sheet_name}")
        sheet_info = wb_info["sheets"][sheet_name]
        if sheet_info["row_count"] != dims["rows"]:
            raise ValueError(f"repeated_results_workbook.xlsx sheet {sheet_name} row count mismatch (expected {dims['rows']}, got {sheet_info['row_count']})")
        if sheet_info["column_count"] != dims["cols"]:
            raise ValueError(f"repeated_results_workbook.xlsx sheet {sheet_name} column count mismatch (expected {dims['cols']}, got {sheet_info['column_count']})")
    
    # Validate canonical tables
    print("  Checking canonical manuscript tables...")
    
    # table_within_project_mean_sd.csv
    wp_info = manifest["canonical_manuscript_tables"]["table_within_project_mean_sd.csv"]
    if not wp_info["exists"]:
        raise ValueError("table_within_project_mean_sd.csv missing")
    if not wp_info["sha256"]:
        raise ValueError("table_within_project_mean_sd.csv has no SHA-256")
    if not wp_info["size"] or wp_info["size"] <= 0:
        raise ValueError("table_within_project_mean_sd.csv has invalid size")
    if wp_info["row_count"] != 8:
        raise ValueError(f"table_within_project_mean_sd.csv row count mismatch (expected 8, got {wp_info['row_count']})")
    if wp_info["column_count"] != 7:
        raise ValueError(f"table_within_project_mean_sd.csv column count mismatch (expected 7, got {wp_info['column_count']})")
    if wp_info["duplicate_key_count"] != 0:
        raise ValueError(f"table_within_project_mean_sd.csv has duplicate keys (count={wp_info['duplicate_key_count']})")
    if wp_info["total_null_count"] != 0:
        raise ValueError(f"table_within_project_mean_sd.csv has null values (count={wp_info['total_null_count']})")
    
    # table_cross_project_mean_sd.csv
    cp_info = manifest["canonical_manuscript_tables"]["table_cross_project_mean_sd.csv"]
    if not cp_info["exists"]:
        raise ValueError("table_cross_project_mean_sd.csv missing")
    if not cp_info["sha256"]:
        raise ValueError("table_cross_project_mean_sd.csv has no SHA-256")
    if not cp_info["size"] or cp_info["size"] <= 0:
        raise ValueError("table_cross_project_mean_sd.csv has invalid size")
    if cp_info["row_count"] != 8:
        raise ValueError(f"table_cross_project_mean_sd.csv row count mismatch (expected 8, got {cp_info['row_count']})")
    if cp_info["column_count"] != 7:
        raise ValueError(f"table_cross_project_mean_sd.csv column count mismatch (expected 7, got {cp_info['column_count']})")
    if cp_info["duplicate_key_count"] != 0:
        raise ValueError(f"table_cross_project_mean_sd.csv has duplicate keys (count={cp_info['duplicate_key_count']})")
    if cp_info["total_null_count"] != 0:
        raise ValueError(f"table_cross_project_mean_sd.csv has null values (count={cp_info['total_null_count']})")
    
    # table_soft_top3_delta_vs_best_baseline.csv
    st3_info = manifest["canonical_manuscript_tables"]["table_soft_top3_delta_vs_best_baseline.csv"]
    if not st3_info["exists"]:
        raise ValueError("table_soft_top3_delta_vs_best_baseline.csv missing")
    if not st3_info["sha256"]:
        raise ValueError("table_soft_top3_delta_vs_best_baseline.csv has no SHA-256")
    if not st3_info["size"] or st3_info["size"] <= 0:
        raise ValueError("table_soft_top3_delta_vs_best_baseline.csv has invalid size")
    if st3_info["row_count"] != 16:
        raise ValueError(f"table_soft_top3_delta_vs_best_baseline.csv row count mismatch (expected 16, got {st3_info['row_count']})")
    if st3_info["column_count"] != 8:
        raise ValueError(f"table_soft_top3_delta_vs_best_baseline.csv column count mismatch (expected 8, got {st3_info['column_count']})")
    if st3_info["duplicate_key_count"] != 0:
        raise ValueError(f"table_soft_top3_delta_vs_best_baseline.csv has duplicate keys (count={st3_info['duplicate_key_count']})")
    if st3_info["total_null_count"] != 0:
        raise ValueError(f"table_soft_top3_delta_vs_best_baseline.csv has null values (count={st3_info['total_null_count']})")
    
    print("All manifest inventory validation checks passed.")


def build_manifest():
    """Build the canonical manifest."""
    print("Building canonical manifest...")
    
    # Validate reports first
    validate_reports()
    
    manifest = {
        "canonical_policy": {
            "canonical_result_source": "results/part1_full_reproduction",
            "canonical_table_source": "results/part1_full_reproduction_tables",
            "legacy_reference_source": "results",
            "legacy_reference_status": "retained_but_noncanonical",
            "canonical_decision_basis": [
                "The tracked executable does not reproduce the legacy reference results.",
                "The exact executable that generated the legacy reference results is not available in tracked Git history.",
                "Two independent runs in the locked environment are numerically equivalent.",
                "No non-numeric repeatability differences were detected.",
                "Soft-top-3 qualitative outcomes versus the best baseline are unchanged across all 16 setting-metric combinations.",
            ]
        },
        "validation_checks": {
            "part1_reproduction_comparison_overall_status": "materially_different",
            "part1_repeatability_comparison_overall_status": "numerically_equivalent",
            "part1_result_drift_analysis_total_combinations": 16,
            "part1_result_drift_analysis_soft_top3_outcome_changes": 0,
            "part1_result_drift_analysis_best_overall_disjoint_winner_changes": 0,
            "part1_reference_provenance_audit_verified": True,
        },
        "environment_and_code_files": {},
        "raw_datasets": {},
        "canonical_reproduction_outputs": {},
        "canonical_manuscript_tables": {},
    }
    
    # Check input files
    print("Checking environment and code files...")
    for name, path in INPUT_FILES.items():
        manifest["environment_and_code_files"][name] = get_file_info(path)
    
    # Check raw datasets
    print("Checking raw datasets...")
    for name, path in RAW_DATASETS.items():
        manifest["raw_datasets"][name] = get_csv_info(path)
    
    # Check canonical outputs
    print("Checking canonical reproduction outputs...")
    for name, path in CANONICAL_OUTPUTS.items():
        if name.endswith(".csv"):
            manifest["canonical_reproduction_outputs"][name] = get_csv_with_duplicates_info(path)
        elif name.endswith(".json"):
            manifest["canonical_reproduction_outputs"][name] = get_json_info(path)
        elif name.endswith(".xlsx"):
            manifest["canonical_reproduction_outputs"][name] = get_excel_info(path)
        else:
            manifest["canonical_reproduction_outputs"][name] = get_file_info(path)
    
    # Check canonical tables
    print("Checking canonical manuscript tables...")
    for name, path in CANONICAL_TABLES.items():
        key_columns = TABLE_KEYS.get(name)
        manifest["canonical_manuscript_tables"][name] = get_csv_with_duplicates_info(path, key_columns)
    
    return manifest


def save_manifest(manifest):
    """Save manifest to JSON and Markdown files using atomic writes."""
    print("Saving manifest...")
    
    # Ensure output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary files
    temp_json = OUTPUT_JSON.with_suffix('.json.tmp')
    temp_md = OUTPUT_MD.with_suffix('.md.tmp')
    
    # Save JSON to temp file
    with open(temp_json, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Save Markdown to temp file
    with open(temp_md, "w") as f:
        f.write("# Part 1 Section 6F: Canonical Reproduction Manifest\n\n")
        f.write("## Canonical Policy\n\n")
        f.write(f"**Canonical result source:** `{manifest['canonical_policy']['canonical_result_source']}`\n\n")
        f.write(f"**Canonical table source:** `{manifest['canonical_policy']['canonical_table_source']}`\n\n")
        f.write(f"**Legacy reference source:** `{manifest['canonical_policy']['legacy_reference_source']}`\n\n")
        f.write(f"**Legacy reference status:** {manifest['canonical_policy']['legacy_reference_status']}\n\n")
        f.write("**Canonical decision basis:**\n\n")
        for basis in manifest['canonical_policy']['canonical_decision_basis']:
            f.write(f"- {basis}\n")
        f.write("\n")
        
        f.write("## Validation Checks\n\n")
        f.write(f"Manifest inventory validation status: {manifest.get('manifest_validation_status', 'not_checked')}\n\n")
        f.write("The following validation checks were performed before freezing the canonical set:\n\n")
        f.write(f"- part1_reproduction_comparison overall_status: `{manifest['validation_checks']['part1_reproduction_comparison_overall_status']}`\n")
        f.write(f"- part1_repeatability_comparison overall_status: `{manifest['validation_checks']['part1_repeatability_comparison_overall_status']}`\n")
        f.write(f"- part1_result_drift_analysis total_combinations: {manifest['validation_checks']['part1_result_drift_analysis_total_combinations']}\n")
        f.write(f"- part1_result_drift_analysis soft_top3_outcome_changes: {manifest['validation_checks']['part1_result_drift_analysis_soft_top3_outcome_changes']}\n")
        f.write(f"- part1_result_drift_analysis best_overall_disjoint_winner_changes: {manifest['validation_checks']['part1_result_drift_analysis_best_overall_disjoint_winner_changes']}\n")
        f.write(f"- part1_reference_provenance_audit verified: {manifest['validation_checks']['part1_reference_provenance_audit_verified']}\n\n")
        
        f.write("## Environment and Code Files\n\n")
        f.write("| File | Exists | SHA-256 | Size |\n")
        f.write("|------|--------|---------|------|\n")
        for name, info in manifest["environment_and_code_files"].items():
            sha_display = f"{info['sha256'][:16]}..." if info['sha256'] is not None else 'N/A'
            size_display = info['size'] if info['size'] is not None else 'N/A'
            f.write(f"| {name} | {info['exists']} | {sha_display} | {size_display} |\n")
        f.write("\n")
        
        f.write("## Raw Datasets\n\n")
        f.write("| Dataset | Exists | Rows | Columns | Null Count |\n")
        f.write("|---------|--------|-------|---------|------------|\n")
        for name, info in manifest["raw_datasets"].items():
            rows_display = info['row_count'] if info['row_count'] is not None else 'N/A'
            cols_display = info['column_count'] if info['column_count'] is not None else 'N/A'
            nulls_display = info['null_count'] if info['null_count'] is not None else 'N/A'
            f.write(f"| {name} | {info['exists']} | {rows_display} | {cols_display} | {nulls_display} |\n")
        f.write("\n")
        
        f.write("## Canonical Reproduction Outputs\n\n")
        f.write("| File | Exists | SHA-256 | Size | Rows | Columns | Duplicates | Nulls |\n")
        f.write("|------|--------|---------|------|------|---------|------------|-------|\n")
        for name, info in manifest["canonical_reproduction_outputs"].items():
            sha_display = f"{info['sha256'][:16]}..." if info['sha256'] is not None else 'N/A'
            size_display = info['size'] if info['size'] is not None else 'N/A'
            rows_display = info.get('row_count') if info.get('row_count') is not None else 'N/A'
            cols_display = info.get('column_count') if info.get('column_count') is not None else 'N/A'
            dups_display = info.get('duplicate_full_rows') if info.get('duplicate_full_rows') is not None else 'N/A'
            nulls_display = info.get('total_null_count') if info.get('total_null_count') is not None else 'N/A'
            f.write(f"| {name} | {info['exists']} | {sha_display} | {size_display} | {rows_display} | {cols_display} | {dups_display} | {nulls_display} |\n")
        f.write("\n")
        
        f.write("## Canonical Manuscript Tables\n\n")
        f.write("| Table | Exists | SHA-256 | Size | Rows | Columns | Key Duplicates | Nulls |\n")
        f.write("|-------|--------|---------|------|------|---------|-----------------|-------|\n")
        for name, info in manifest["canonical_manuscript_tables"].items():
            sha_display = f"{info['sha256'][:16]}..." if info['sha256'] is not None else 'N/A'
            size_display = info['size'] if info['size'] is not None else 'N/A'
            rows_display = info.get('row_count') if info.get('row_count') is not None else 'N/A'
            cols_display = info.get('column_count') if info.get('column_count') is not None else 'N/A'
            key_dups_display = info.get('duplicate_key_count') if info.get('duplicate_key_count') is not None else 'N/A'
            nulls_display = info.get('total_null_count') if info.get('total_null_count') is not None else 'N/A'
            f.write(f"| {name} | {info['exists']} | {sha_display} | {size_display} | {rows_display} | {cols_display} | {key_dups_display} | {nulls_display} |\n")
        f.write("\n")
        
        f.write("## Legacy-Reference Status\n\n")
        f.write(f"The legacy reference files in `{manifest['canonical_policy']['legacy_reference_source']}` are retained but marked as non-canonical.\n\n")
        f.write("These files are preserved for historical reference and comparison purposes only.\n\n")
        
        f.write("## Scientific Interpretation Limits\n\n")
        f.write("**This manifest establishes computational provenance and repeatability.**\n\n")
        f.write("**It does not establish statistical significance or external validity.**\n\n")
        f.write("The canonical results represent the output of a specific computational pipeline under controlled conditions.\n")
        f.write("Any scientific claims about model performance should be supported by appropriate statistical analysis\n")
        f.write("and validation on independent datasets.\n\n")
    
    # Atomic replace
    temp_json.replace(OUTPUT_JSON)
    temp_md.replace(OUTPUT_MD)
    
    print("Manifest saved atomically.")


def main():
    """Main entry point."""
    manifest = build_manifest()
    
    # Validate manifest inventory before saving
    validate_manifest_inventory(manifest)
    
    # Add validation status to manifest
    manifest["manifest_validation_status"] = "all_checks_passed"
    
    save_manifest(manifest)
    
    print("\nManifest build complete!")
    print(f"\nSummary:")
    print(f"  Canonical result source: {manifest['canonical_policy']['canonical_result_source']}")
    print(f"  Canonical table source: {manifest['canonical_policy']['canonical_table_source']}")
    print(f"  Number of raw datasets verified: {len(manifest['raw_datasets'])}")
    print(f"  Number of canonical outputs verified: {len(manifest['canonical_reproduction_outputs'])}")
    print(f"  Number of canonical tables verified: {len(manifest['canonical_manuscript_tables'])}")
    print(f"  Legacy reference status: {manifest['canonical_policy']['legacy_reference_status']}")
    print(f"  Manifest validation status: {manifest['manifest_validation_status']}")


if __name__ == "__main__":
    main()
