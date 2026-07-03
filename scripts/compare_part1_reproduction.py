#!/usr/bin/env python3
import pandas as pd
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

def compare_files(ref_path: Path, new_path: Path, key_columns: List[str]) -> Dict[str, Any]:
    """Compare two CSV files with detailed analysis."""
    result = {
        "file": str(new_path.name),
        "exists_in_both": True,
        "ref_rows": 0,
        "new_rows": 0,
        "ref_cols": 0,
        "new_cols": 0,
        "column_names_match": True,
        "column_order_match": True,
        "key_duplicates": {"ref": False, "new": False},
        "missing_keys": [],
        "extra_keys": [],
        "text_columns_match": True,
        "text_differences": [],
        "numerical_analysis": {},
        "max_absolute_diff": 0.0,
        "mean_absolute_diff": 0.0,
        "diff_gt_1e12": 0,
        "diff_gt_1e9": 0,
    }
    
    # Check file existence
    if not ref_path.exists():
        result["exists_in_both"] = False
        result["error"] = "Reference file not found"
        return result
    
    if not new_path.exists():
        result["exists_in_both"] = False
        result["error"] = "New file not found"
        return result
    
    # Read files
    try:
        ref_df = pd.read_csv(ref_path)
        new_df = pd.read_csv(new_path)
    except Exception as e:
        result["error"] = f"Error reading files: {str(e)}"
        return result
    
    result["ref_rows"] = len(ref_df)
    result["new_rows"] = len(new_df)
    result["ref_cols"] = len(ref_df.columns)
    result["new_cols"] = len(new_df.columns)
    
    # Column names and order
    ref_cols = list(ref_df.columns)
    new_cols = list(new_df.columns)
    
    if ref_cols != new_cols:
        result["column_names_match"] = False
        result["column_names"] = {"ref": ref_cols, "new": new_cols}
    
    if ref_cols == new_cols:
        result["column_order_match"] = True
    else:
        result["column_order_match"] = False
    
    # Key duplicates
    if key_columns:
        ref_keys = ref_df[key_columns].apply(tuple, axis=1)
        new_keys = new_df[key_columns].apply(tuple, axis=1)
        
        result["key_duplicates"]["ref"] = ref_keys.duplicated().any()
        result["key_duplicates"]["new"] = new_keys.duplicated().any()
        
        # Missing/extra keys
        ref_key_set = set(ref_keys)
        new_key_set = set(new_keys)
        
        result["missing_keys"] = list(ref_key_set - new_key_set)
        result["extra_keys"] = list(new_key_set - ref_key_set)
    
    # Merge on keys for comparison
    if key_columns:
        merged = ref_df.merge(new_df, on=key_columns, suffixes=('_ref', '_new'), how='outer', indicator=True)
    else:
        # If no keys, compare by index
        merged = ref_df.merge(new_df, left_index=True, right_index=True, suffixes=('_ref', '_new'), how='outer', indicator=True)
    
    # Text column comparison
    text_cols = ref_df.select_dtypes(include=['object']).columns
    for col in text_cols:
        if f"{col}_ref" in merged.columns and f"{col}_new" in merged.columns:
            ref_col = merged[f"{col}_ref"]
            new_col = merged[f"{col}_new"]
            
            # Compare non-null values
            mask = ref_col.notna() & new_col.notna()
            if not (ref_col[mask] == new_col[mask]).all():
                result["text_columns_match"] = False
                diff_mask = mask & (ref_col != new_col)
                for idx in merged[diff_mask].index:
                    result["text_differences"].append({
                        "column": col,
                        "index": idx,
                        "ref_value": str(ref_col.loc[idx]),
                        "new_value": str(new_col.loc[idx])
                    })
    
    # Numerical column comparison
    num_cols = ref_df.select_dtypes(include=[np.number]).columns
    all_diffs = []
    
    for col in num_cols:
        if f"{col}_ref" in merged.columns and f"{col}_new" in merged.columns:
            ref_col = merged[f"{col}_ref"]
            new_col = merged[f"{col}_new"]
            
            # Handle NaN
            mask = ref_col.notna() & new_col.notna()
            if mask.sum() > 0:
                diff = np.abs(ref_col[mask] - new_col[mask])
                all_diffs.extend(diff.tolist())
                
                col_max_diff = diff.max() if len(diff) > 0 else 0.0
                col_mean_diff = diff.mean() if len(diff) > 0 else 0.0
                
                result["numerical_analysis"][col] = {
                    "max_diff": float(col_max_diff),
                    "mean_diff": float(col_mean_diff),
                    "diff_gt_1e12": int((diff > 1e-12).sum()),
                    "diff_gt_1e9": int((diff > 1e-9).sum())
                }
    
    if all_diffs:
        result["max_absolute_diff"] = float(max(all_diffs))
        result["mean_absolute_diff"] = float(np.mean(all_diffs))
        result["diff_gt_1e12"] = sum(1 for d in all_diffs if d > 1e-12)
        result["diff_gt_1e9"] = sum(1 for d in all_diffs if d > 1e-9)
    
    return result

def compare_json_files(ref_path: Path, new_path: Path) -> Dict[str, Any]:
    """Compare two JSON files field by field."""
    result = {
        "file": new_path.name,
        "exists_in_both": True,
        "fields_match": True,
        "differences": []
    }
    
    if not ref_path.exists():
        result["exists_in_both"] = False
        result["error"] = "Reference file not found"
        return result
    
    if not new_path.exists():
        result["exists_in_both"] = False
        result["error"] = "New file not found"
        return result
    
    try:
        with open(ref_path, 'r') as f:
            ref_data = json.load(f)
        with open(new_path, 'r') as f:
            new_data = json.load(f)
    except Exception as e:
        result["error"] = f"Error reading files: {str(e)}"
        return result
    
    # Compare field by field
    all_keys = set(ref_data.keys()) | set(new_data.keys())
    
    for key in all_keys:
        ref_val = ref_data.get(key)
        new_val = new_data.get(key)
        
        if ref_val != new_val:
            result["fields_match"] = False
            result["differences"].append({
                "field": key,
                "ref_value": str(ref_val),
                "new_value": str(new_val)
            })
    
    return result

def main():
    base_dir = Path("/Users/aliehpourdast/Desktop/springer/springer")
    ref_dir = base_dir / "results"
    new_dir = base_dir / "results/part1_full_reproduction"
    
    # Define files to compare with their key columns
    files_to_compare = {
        "dataset_profile.csv": ["project"],
        "repeated_all_results.csv": ["experiment", "target_project", "seed", "model"],
        "validation_log.csv": ["experiment", "target_project", "seed", "candidate", "mode"],
        "repeated_summary_mean_std.csv": ["experiment", "model"],
    }
    
    results = {}
    
    # Compare CSV files
    for filename, key_cols in files_to_compare.items():
        ref_path = ref_dir / filename
        new_path = new_dir / filename
        results[filename] = compare_files(ref_path, new_path, key_cols)
    
    # Compare JSON file
    json_result = compare_json_files(ref_dir / "decision_metadata.json", new_dir / "decision_metadata.json")
    results["decision_metadata.json"] = json_result
    
    # Determine overall status
    has_text_diffs = any(
        r.get("text_columns_match") == False or 
        r.get("fields_match") == False or
        len(r.get("text_differences", [])) > 0 or
        len(r.get("differences", [])) > 0 or
        len(r.get("missing_keys", [])) > 0 or
        len(r.get("extra_keys", [])) > 0
        for r in results.values()
    )
    
    max_diff = max(r.get("max_absolute_diff", 0.0) for r in results.values())
    
    if has_text_diffs:
        overall_status = "materially_different"
    elif max_diff > 1e-9:
        overall_status = "materially_different"
    elif max_diff > 1e-12:
        overall_status = "numerically_equivalent"
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
    json_report_path = base_dir / "reports/part1_reproduction_comparison.json"
    with open(json_report_path, 'w') as f:
        json.dump(results_native, f, indent=2)
    
    # Save Markdown report
    md_report_path = base_dir / "reports/part1_reproduction_comparison.md"
    with open(md_report_path, 'w') as f:
        f.write("# Part 1 Section 5B: Reproduction Comparison Report\n\n")
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
            
            f.write(f"- **Exists in both**: {result['exists_in_both']}\n")
            f.write(f"- **Reference rows**: {result.get('ref_rows', 'N/A')}\n")
            f.write(f"- **New rows**: {result.get('new_rows', 'N/A')}\n")
            f.write(f"- **Reference columns**: {result.get('ref_cols', 'N/A')}\n")
            f.write(f"- **New columns**: {result.get('new_cols', 'N/A')}\n")
            f.write(f"- **Column names match**: {result.get('column_names_match', 'N/A')}\n")
            f.write(f"- **Column order match**: {result.get('column_order_match', 'N/A')}\n")
            
            if "key_duplicates" in result:
                f.write(f"- **Key duplicates (ref)**: {result['key_duplicates']['ref']}\n")
                f.write(f"- **Key duplicates (new)**: {result['key_duplicates']['new']}\n")
                f.write(f"- **Missing keys**: {len(result['missing_keys'])}\n")
                f.write(f"- **Extra keys**: {len(result['extra_keys'])}\n")
            
            if "text_columns_match" in result:
                f.write(f"- **Text columns match**: {result['text_columns_match']}\n")
                if result['text_differences']:
                    f.write(f"- **Text differences**: {len(result['text_differences'])}\n")
            
            if "fields_match" in result:
                f.write(f"- **Fields match**: {result['fields_match']}\n")
                if result['differences']:
                    f.write(f"- **Field differences**: {len(result['differences'])}\n")
            
            if "max_absolute_diff" in result:
                f.write(f"- **Max absolute difference**: {result['max_absolute_diff']:.2e}\n")
                f.write(f"- **Mean absolute difference**: {result['mean_absolute_diff']:.2e}\n")
                f.write(f"- **Differences > 1e-12**: {result['diff_gt_1e12']}\n")
                f.write(f"- **Differences > 1e-9**: {result['diff_gt_1e9']}\n")
            
            f.write("\n")
    
    print(f"Comparison complete. Overall status: {overall_status}")
    print(f"JSON report saved to: {json_report_path}")
    print(f"Markdown report saved to: {md_report_path}")

if __name__ == "__main__":
    main()
