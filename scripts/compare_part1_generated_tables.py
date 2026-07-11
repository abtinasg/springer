#!/usr/bin/env python3
import pandas as pd
import json
import numpy as np
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_mean_std(value: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse a value in format 'mean (std)' into (mean, std)."""
    if pd.isna(value) or value == "":
        return None, None
    
    match = re.match(r'^\s*([+-]?\d*\.?\d+)\s*\(\s*([+-]?\d*\.?\d+)\s*\)\s*$', str(value))
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Try to parse as single number
    try:
        return float(value), None
    except ValueError:
        return None, None

def compare_mean_std_tables(first_path: Path, second_path: Path, key_columns: List[str]) -> Dict[str, Any]:
    """Compare mean/SD tables with detailed parsing."""
    result = {
        "file": first_path.name,
        "exists_in_both": True,
        "first_sha256": "",
        "second_sha256": "",
        "sha256_match": False,
        "first_rows": 0,
        "second_rows": 0,
        "first_cols": 0,
        "second_cols": 0,
        "column_names_match": True,
        "column_order_match": True,
        "key_duplicates": {"first": False, "second": False},
        "missing_keys": [],
        "extra_keys": [],
        "cell_differences": [],
        "null_mismatch_count": 0,
        "max_mean_diff": 0.0,
        "max_std_diff": 0.0,
    }
    
    if not first_path.exists():
        result["exists_in_both"] = False
        result["error"] = "First file not found"
        return result
    
    if not second_path.exists():
        result["exists_in_both"] = False
        result["error"] = "Second file not found"
        return result
    
    result["first_sha256"] = compute_sha256(first_path)
    result["second_sha256"] = compute_sha256(second_path)
    result["sha256_match"] = result["first_sha256"] == result["second_sha256"]
    
    try:
        first_df = pd.read_csv(first_path)
        second_df = pd.read_csv(second_path)
    except Exception as e:
        result["error"] = f"Error reading files: {str(e)}"
        return result
    
    result["first_rows"] = len(first_df)
    result["second_rows"] = len(second_df)
    result["first_cols"] = len(first_df.columns)
    result["second_cols"] = len(second_df.columns)
    
    first_cols = list(first_df.columns)
    second_cols = list(second_df.columns)
    
    if first_cols != second_cols:
        result["column_names_match"] = False
        result["column_names"] = {"first": first_cols, "second": second_cols}
    
    if first_cols == second_cols:
        result["column_order_match"] = True
    else:
        result["column_order_match"] = False
    
    if key_columns:
        first_keys = first_df[key_columns].apply(tuple, axis=1)
        second_keys = second_df[key_columns].apply(tuple, axis=1)
        
        result["key_duplicates"]["first"] = first_keys.duplicated().any()
        result["key_duplicates"]["second"] = second_keys.duplicated().any()
        
        first_key_set = set(first_keys)
        second_key_set = set(second_keys)
        
        result["missing_keys"] = list(first_key_set - second_key_set)
        result["extra_keys"] = list(second_key_set - first_key_set)
    
    if key_columns:
        merged = first_df.merge(second_df, on=key_columns, suffixes=('_first', '_second'), how='outer', indicator=True)
    else:
        merged = first_df.merge(second_df, left_index=True, right_index=True, suffixes=('_first', '_second'), how='outer', indicator=True)
    
    all_mean_diffs = []
    all_std_diffs = []
    
    for col in first_df.columns:
        if col in key_columns:
            continue
        
        if f"{col}_first" in merged.columns and f"{col}_second" in merged.columns:
            first_col = merged[f"{col}_first"]
            second_col = merged[f"{col}_second"]
            
            for idx in merged.index:
                key_values = {k: merged.loc[idx, k] for k in key_columns} if key_columns else {}
                
                first_val = first_col.loc[idx]
                second_val = second_col.loc[idx]
                
                first_null = pd.isna(first_val)
                second_null = pd.isna(second_val)
                
                if first_null != second_null:
                    result["null_mismatch_count"] += 1
                    result["cell_differences"].append({
                        "column": col,
                        "key_values": key_values,
                        "first_value": "NaN" if first_null else str(first_val),
                        "second_value": "NaN" if second_null else str(second_val),
                        "difference_type": "null_mismatch"
                    })
                elif not first_null and not second_null:
                    first_mean, first_std = parse_mean_std(first_val)
                    second_mean, second_std = parse_mean_std(second_val)
                    
                    if first_mean is not None and second_mean is not None:
                        mean_diff = abs(first_mean - second_mean)
                        all_mean_diffs.append(mean_diff)
                        
                        if mean_diff > 1e-12:
                            diff_record = {
                                "column": col,
                                "key_values": key_values,
                                "first_value": str(first_val),
                                "second_value": str(second_val),
                                "reference_mean": first_mean,
                                "new_mean": second_mean,
                                "mean_difference": mean_diff,
                                "difference_type": "mean_difference"
                            }
                            
                            if first_std is not None and second_std is not None:
                                std_diff = abs(first_std - second_std)
                                all_std_diffs.append(std_diff)
                                diff_record["reference_std"] = first_std
                                diff_record["new_std"] = second_std
                                diff_record["std_difference"] = std_diff
                            
                            result["cell_differences"].append(diff_record)
                    elif str(first_val) != str(second_val):
                        result["cell_differences"].append({
                            "column": col,
                            "key_values": key_values,
                            "first_value": str(first_val),
                            "second_value": str(second_val),
                            "difference_type": "text_difference"
                        })
    
    if all_mean_diffs:
        result["max_mean_diff"] = float(max(all_mean_diffs))
    if all_std_diffs:
        result["max_std_diff"] = float(max(all_std_diffs))
    
    return result

def compare_delta_table(first_path: Path, second_path: Path, key_columns: List[str]) -> Dict[str, Any]:
    """Compare delta table with numeric and text column analysis."""
    result = {
        "file": first_path.name,
        "exists_in_both": True,
        "first_sha256": "",
        "second_sha256": "",
        "sha256_match": False,
        "first_rows": 0,
        "second_rows": 0,
        "first_cols": 0,
        "second_cols": 0,
        "column_names_match": True,
        "column_order_match": True,
        "key_duplicates": {"first": False, "second": False},
        "missing_keys": [],
        "extra_keys": [],
        "numeric_differences": [],
        "text_differences": [],
        "null_mismatch_count": 0,
        "max_absolute_diff": 0.0,
    }
    
    if not first_path.exists():
        result["exists_in_both"] = False
        result["error"] = "First file not found"
        return result
    
    if not second_path.exists():
        result["exists_in_both"] = False
        result["error"] = "Second file not found"
        return result
    
    result["first_sha256"] = compute_sha256(first_path)
    result["second_sha256"] = compute_sha256(second_path)
    result["sha256_match"] = result["first_sha256"] == result["second_sha256"]
    
    try:
        first_df = pd.read_csv(first_path)
        second_df = pd.read_csv(second_path)
    except Exception as e:
        result["error"] = f"Error reading files: {str(e)}"
        return result
    
    result["first_rows"] = len(first_df)
    result["second_rows"] = len(second_df)
    result["first_cols"] = len(first_df.columns)
    result["second_cols"] = len(second_df.columns)
    
    first_cols = list(first_df.columns)
    second_cols = list(second_df.columns)
    
    if first_cols != second_cols:
        result["column_names_match"] = False
        result["column_names"] = {"first": first_cols, "second": second_cols}
    
    if first_cols == second_cols:
        result["column_order_match"] = True
    else:
        result["column_order_match"] = False
    
    if key_columns:
        first_keys = first_df[key_columns].apply(tuple, axis=1)
        second_keys = second_df[key_columns].apply(tuple, axis=1)
        
        result["key_duplicates"]["first"] = first_keys.duplicated().any()
        result["key_duplicates"]["second"] = second_keys.duplicated().any()
        
        first_key_set = set(first_keys)
        second_key_set = set(second_keys)
        
        result["missing_keys"] = list(first_key_set - second_key_set)
        result["extra_keys"] = list(second_key_set - first_key_set)
    
    if key_columns:
        merged = first_df.merge(second_df, on=key_columns, suffixes=('_first', '_second'), how='outer', indicator=True)
    else:
        merged = first_df.merge(second_df, left_index=True, right_index=True, suffixes=('_first', '_second'), how='outer', indicator=True)
    
    numeric_columns = ["Soft-top-3 mean", "Best baseline mean", "Delta"]
    text_columns = ["Direction", "Best baseline", "AQRPE outcome"]
    
    all_diffs = []
    
    for col in numeric_columns:
        if col in first_df.columns:
            if f"{col}_first" in merged.columns and f"{col}_second" in merged.columns:
                first_col = merged[f"{col}_first"]
                second_col = merged[f"{col}_second"]
                
                for idx in merged.index:
                    key_values = {k: merged.loc[idx, k] for k in key_columns} if key_columns else {}
                    
                    first_val = first_col.loc[idx]
                    second_val = second_col.loc[idx]
                    
                    first_null = pd.isna(first_val)
                    second_null = pd.isna(second_val)
                    
                    if first_null != second_null:
                        result["null_mismatch_count"] += 1
                        result["numeric_differences"].append({
                            "column": col,
                            "key_values": key_values,
                            "first_value": "NaN" if first_null else str(first_val),
                            "second_value": "NaN" if second_null else str(second_val),
                            "difference_type": "null_mismatch"
                        })
                    elif not first_null and not second_null:
                        try:
                            first_num = float(first_val)
                            second_num = float(second_val)
                            diff = abs(first_num - second_num)
                            all_diffs.append(diff)
                            
                            if diff > 1e-12:
                                result["numeric_differences"].append({
                                    "column": col,
                                    "key_values": key_values,
                                    "first_value": first_num,
                                    "second_value": second_num,
                                    "difference": diff
                                })
                        except (ValueError, TypeError):
                            if str(first_val) != str(second_val):
                                result["numeric_differences"].append({
                                    "column": col,
                                    "key_values": key_values,
                                    "first_value": str(first_val),
                                    "second_value": str(second_val),
                                    "difference_type": "text_difference"
                                })
    
    for col in text_columns:
        if col in first_df.columns:
            if f"{col}_first" in merged.columns and f"{col}_second" in merged.columns:
                first_col = merged[f"{col}_first"]
                second_col = merged[f"{col}_second"]
                
                for idx in merged.index:
                    key_values = {k: merged.loc[idx, k] for k in key_columns} if key_columns else {}
                    
                    first_val = first_col.loc[idx]
                    second_val = second_col.loc[idx]
                    
                    first_null = pd.isna(first_val)
                    second_null = pd.isna(second_val)
                    
                    if first_null != second_null:
                        result["null_mismatch_count"] += 1
                        result["text_differences"].append({
                            "column": col,
                            "key_values": key_values,
                            "first_value": "NaN" if first_null else str(first_val),
                            "second_value": "NaN" if second_null else str(second_val)
                        })
                    elif not first_null and not second_null:
                        if str(first_val) != str(second_val):
                            result["text_differences"].append({
                                "column": col,
                                "key_values": key_values,
                                "first_value": str(first_val),
                                "second_value": str(second_val)
                            })
    
    if all_diffs:
        result["max_absolute_diff"] = float(max(all_diffs))
    
    return result

def main():
    base_dir = Path(__file__).resolve().parents[1]
    first_dir = base_dir / "results"
    second_dir = base_dir / "results/part1_full_reproduction_tables"
    
    files_to_compare = {
        "table_within_project_mean_sd.csv": (["Model"], "mean_std"),
        "table_cross_project_mean_sd.csv": (["Model"], "mean_std"),
        "table_soft_top3_delta_vs_best_baseline.csv": (["Setting", "Metric"], "delta"),
    }
    
    results = {}
    
    for filename, (key_cols, table_type) in files_to_compare.items():
        first_path = first_dir / filename
        second_path = second_dir / filename
        
        if table_type == "mean_std":
            results[filename] = compare_mean_std_tables(first_path, second_path, key_cols)
        else:
            results[filename] = compare_delta_table(first_path, second_path, key_cols)
    
    # Determine overall status
    has_diffs = any(
        not r.get("exists_in_both", True) or
        r.get("column_names_match", True) == False or
        r.get("column_order_match", True) == False or
        r.get("key_duplicates", {}).get("first", False) or
        r.get("key_duplicates", {}).get("second", False) or
        len(r.get("missing_keys", [])) > 0 or
        len(r.get("extra_keys", [])) > 0 or
        len(r.get("cell_differences", [])) > 0 or
        len(r.get("numeric_differences", [])) > 0 or
        len(r.get("text_differences", [])) > 0 or
        r.get("null_mismatch_count", 0) > 0
        for r in results.values()
    )
    
    max_diff = 0.0
    for r in results.values():
        if "max_absolute_diff" in r:
            max_diff = max(max_diff, r["max_absolute_diff"])
        if "max_mean_diff" in r:
            max_diff = max(max_diff, r["max_mean_diff"])
    
    if has_diffs:
        if max_diff > 1e-12:
            overall_status = "materially_different"
        else:
            overall_status = "materially_different"
    else:
        overall_status = "exact_match"
    
    results["overall_status"] = overall_status
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_to_native(obj):
        if isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return convert_to_native(obj.tolist())
        else:
            return obj
    
    results_native = convert_to_native(results)
    
    # Save JSON report
    json_report_path = base_dir / "reports/part1_generated_tables_comparison.json"
    with open(json_report_path, 'w') as f:
        json.dump(results_native, f, indent=2)
    
    # Save Markdown report
    md_report_path = base_dir / "reports/part1_generated_tables_comparison.md"
    with open(md_report_path, 'w') as f:
        f.write("# Part 1 Section 6B: Generated Tables Comparison Report\n\n")
        f.write(f"## Overall Status\n\n")
        f.write(f"**{overall_status}**\n\n")
        f.write(f"## Maximum Numerical Difference\n\n")
        f.write(f"{max_diff:.2e}\n\n")
        
        for filename, result in results.items():
            if filename == "overall_status":
                continue
            
            f.write(f"## {filename}\n\n")
            
            if not result.get("exists_in_both"):
                f.write(f"**Error**: {result.get('error', 'File not found')}\n\n")
                continue
            
            f.write(f"- **SHA-256 match**: {result['sha256_match']}\n")
            f.write(f"- **First SHA-256**: {result['first_sha256']}\n")
            f.write(f"- **Second SHA-256**: {result['second_sha256']}\n")
            f.write(f"- **First rows**: {result['first_rows']}\n")
            f.write(f"- **Second rows**: {result['second_rows']}\n")
            f.write(f"- **First columns**: {result['first_cols']}\n")
            f.write(f"- **Second columns**: {result['second_cols']}\n")
            f.write(f"- **Column names match**: {result['column_names_match']}\n")
            f.write(f"- **Column order match**: {result['column_order_match']}\n")
            
            if "key_duplicates" in result:
                f.write(f"- **Key duplicates (first)**: {result['key_duplicates']['first']}\n")
                f.write(f"- **Key duplicates (second)**: {result['key_duplicates']['second']}\n")
                f.write(f"- **Missing keys**: {len(result['missing_keys'])}\n")
                f.write(f"- **Extra keys**: {len(result['extra_keys'])}\n")
            
            if "cell_differences" in result:
                f.write(f"- **Cell differences**: {len(result['cell_differences'])}\n")
            
            if "numeric_differences" in result:
                f.write(f"- **Numeric differences**: {len(result['numeric_differences'])}\n")
            
            if "text_differences" in result:
                f.write(f"- **Text differences**: {len(result['text_differences'])}\n")
            
            if "null_mismatch_count" in result:
                f.write(f"- **Null mismatches**: {result['null_mismatch_count']}\n")
            
            if "max_mean_diff" in result:
                f.write(f"- **Max mean difference**: {result['max_mean_diff']:.2e}\n")
            
            if "max_std_diff" in result:
                f.write(f"- **Max std difference**: {result['max_std_diff']:.2e}\n")
            
            if "max_absolute_diff" in result:
                f.write(f"- **Max absolute difference**: {result['max_absolute_diff']:.2e}\n")
            
            f.write("\n")
    
    print(f"Comparison complete. Overall status: {overall_status}")
    print(f"JSON report saved to: {json_report_path}")
    print(f"Markdown report saved to: {md_report_path}")

if __name__ == "__main__":
    main()
