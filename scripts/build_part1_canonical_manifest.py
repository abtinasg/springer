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
    """Save manifest to JSON and Markdown files."""
    print("Saving manifest...")
    
    # Ensure output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Save Markdown
    with open(OUTPUT_MD, "w") as f:
        f.write("# Part 1 Section 6E: Canonical Reproduction Manifest\n\n")
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
            f.write(f"| {name} | {info['exists']} | {info['sha256'][:16] if info['sha256'] else 'N/A'}... | {info['size'] if info['size'] else 'N/A'} |\n")
        f.write("\n")
        
        f.write("## Raw Datasets\n\n")
        f.write("| Dataset | Exists | Rows | Columns | Null Count |\n")
        f.write("|---------|--------|-------|---------|------------|\n")
        for name, info in manifest["raw_datasets"].items():
            f.write(f"| {name} | {info['exists']} | {info['row_count'] if info['row_count'] else 'N/A'} | {info['column_count'] if info['column_count'] else 'N/A'} | {info['null_count'] if info['null_count'] else 'N/A'} |\n")
        f.write("\n")
        
        f.write("## Canonical Reproduction Outputs\n\n")
        f.write("| File | Exists | SHA-256 | Size | Rows | Columns | Duplicates | Nulls |\n")
        f.write("|------|--------|---------|------|------|---------|------------|-------|\n")
        for name, info in manifest["canonical_reproduction_outputs"].items():
            rows = info.get('row_count', 'N/A')
            cols = info.get('column_count', 'N/A')
            dups = info.get('duplicate_full_rows', 'N/A')
            nulls = info.get('total_null_count', 'N/A')
            f.write(f"| {name} | {info['exists']} | {info['sha256'][:16] if info['sha256'] else 'N/A'}... | {info['size'] if info['size'] else 'N/A'} | {rows} | {cols} | {dups} | {nulls} |\n")
        f.write("\n")
        
        f.write("## Canonical Manuscript Tables\n\n")
        f.write("| Table | Exists | SHA-256 | Size | Rows | Columns | Key Duplicates | Nulls |\n")
        f.write("|-------|--------|---------|------|------|---------|-----------------|-------|\n")
        for name, info in manifest["canonical_manuscript_tables"].items():
            rows = info.get('row_count', 'N/A')
            cols = info.get('column_count', 'N/A')
            key_dups = info.get('duplicate_key_count', 'N/A')
            nulls = info.get('total_null_count', 'N/A')
            f.write(f"| {name} | {info['exists']} | {info['sha256'][:16] if info['sha256'] else 'N/A'}... | {info['size'] if info['size'] else 'N/A'} | {rows} | {cols} | {key_dups} | {nulls} |\n")
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


def main():
    """Main entry point."""
    manifest = build_manifest()
    save_manifest(manifest)
    
    print("\nManifest build complete!")
    print(f"\nSummary:")
    print(f"  Canonical result source: {manifest['canonical_policy']['canonical_result_source']}")
    print(f"  Canonical table source: {manifest['canonical_policy']['canonical_table_source']}")
    print(f"  Number of raw datasets verified: {len(manifest['raw_datasets'])}")
    print(f"  Number of canonical outputs verified: {len(manifest['canonical_reproduction_outputs'])}")
    print(f"  Number of canonical tables verified: {len(manifest['canonical_manuscript_tables'])}")
    print(f"  Legacy reference status: {manifest['canonical_policy']['legacy_reference_status']}")


if __name__ == "__main__":
    main()
