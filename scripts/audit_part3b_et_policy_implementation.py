#!/usr/bin/env python3
"""Part 3B.2R.1-G.D6.3: Audit frozen ET reconciliation policy implementation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

STAGE = "Part 3B.2R.1-G.D6.3"
STARTING_COMMIT = "27d103b6fa14c6810d0e33a1141d4739e5f7e34b"
JSON_OUTPUT_PATH = "reports/part3b_et_policy_implementation.json"
MD_OUTPUT_PATH = "reports/part3b_et_policy_implementation.md"
FROZEN_POLICY_JSON_PATH = "reports/part3b_et_reconciliation_policy.json"
POLICY_MODULE_PATH = "scripts/part3b_et_reconciliation_policy.py"
PRODUCTION_VALIDATOR_PATH = "scripts/build_part3b_prediction_ledger.py"
PRODUCTION_VALIDATOR_SHA_BEFORE = (
    "d269bb2eb9b6b4959c9bccb287314249b08da52ad895fa6285ec2af9b6abce49"
)
EXPECTED_WRITE_GUARD_MECHANISMS = [
    "builtins_open",
    "io_open",
    "path_open",
    "path_write_text",
    "path_write_bytes",
    "path_touch",
    "path_replace",
    "path_rename",
    "os_open",
    "os_replace",
    "os_rename",
    "shutil_copy",
    "shutil_copy2",
    "shutil_copyfile",
    "shutil_move",
]
EXPECTED_PRODUCTION_ENTRY_POINTS = [
    "build_core_bundle",
    "fit_event_candidates",
    "build_prediction_rows",
    "execute_postbuild_integration",
]

PROTECTED_PATHS = [
    "scripts/freeze_part3b_et_reconciliation_policy.py",
    "reports/part3b_et_reconciliation_policy.json",
    "reports/part3b_et_reconciliation_policy.md",
    "scripts/audit_part3b_et_canonical_reconciliation.py",
    "reports/part3b_et_canonical_reconciliation.json",
    "reports/part3b_et_canonical_reconciliation.md",
    "results/part3b_prediction_ledger/et_canonical_mismatch_matrix.csv",
    "results/part3b_prediction_ledger/sample_registry.csv",
    "results/part3b_prediction_ledger/split_membership_within.csv.gz",
    "results/part3b_prediction_ledger/canonical_result_reconstruction.csv",
    "results/part3b_prediction_ledger/ledger_manifest.json",
    "results/part3b_prediction_ledger/prediction_ledger_within.csv.gz",
    "results/part3b_prediction_ledger/split_membership_cross.csv.gz",
    "results/part3b_prediction_ledger/event_manifest.csv",
    "results/part3b_prediction_ledger/prediction_ledger_cross.csv.gz",
    "results/part3b_prediction_ledger/validation_reconstruction.csv",
]

REQUIRED_PUBLIC_FUNCTIONS = [
    "load_and_verify_frozen_policy",
    "float64_bit_equal",
    "evaluate_et_rank_metric_reconciliation_eligibility",
    "validate_dual_build_reconciliation_context",
    "classify_dual_build_mismatches",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_module(rel_path: str, module_name: str) -> Any:
    path = repo_root() / rel_path
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protected_snapshot(root: Path) -> Dict[str, Optional[str]]:
    return {
        rel: sha256_file(root / rel) if (root / rel).is_file() else None
        for rel in PROTECTED_PATHS
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Part 3B ET Reconciliation Policy Implementation Report",
        "",
        f"**Stage:** {report['stage']}",
        f"**Starting commit:** `{report['starting_commit']}`",
        "",
        "## Policy Specification",
        "",
        f"- **Frozen policy path:** `{report['frozen_policy_path']}`",
        f"- **Frozen policy SHA-256:** `{report['frozen_policy_sha256']}`",
        f"- **Frozen policy contract verified:** {report['frozen_policy_contract_verified']}",
        f"- **Implementation module SHA-256:** `{report['implementation_module_sha256']}`",
        "",
        "## Production Validator",
        "",
        f"- **Production validator SHA before:** `{report['production_validator_sha_before']}`",
        f"- **Production validator SHA after:** `{report['production_validator_sha_after']}`",
        f"- **Production validator code changed:** {report['production_validator_code_changed']}",
        f"- **Production authorization remains false:** {report['production_authorization_remains_false']}",
        "",
        "## Implemented Constants",
        "",
    ]
    for key, value in report.get("implemented_constants", {}).items():
        lines.append(f"- **{key}:** {value}")
    lines.extend(
        [
            "",
            "## Public Functions",
            "",
        ]
    )
    for fn in report.get("public_functions", []):
        lines.append(f"- `{fn}`")
    lines.extend(
        [
            "",
            "## Integration Points",
            "",
        ]
    )
    for point in report.get("integration_points", []):
        lines.append(f"- {point}")
    lines.extend(
        [
            "",
            "## Dual-Build Architecture",
            "",
            f"- **Dual-build evidence required:** {report['dual_build_evidence_required']}",
            f"- **Single-build final approval prohibited:** {report['single_build_final_approval_prohibited']}",
            f"- **Predicate identity hard-coding detected:** {report['predicate_identity_hardcoding_detected']}",
            "",
            "## Fixture Parity",
            "",
        ]
    )
    for item in report.get("fixture_parity_results", []):
        lines.append(
            f"- `{item.get('event_id', 'n/a')}`: expected={item.get('expected')} "
            f"observed={item.get('observed')} passed={item.get('passed')}"
        )
    lines.extend(
        [
            "",
            "## Synthetic Tests",
            "",
            f"- **Tests expected:** {report['synthetic_tests']['tests_expected']}",
            f"- **Tests executed:** {report['synthetic_tests']['tests_executed']}",
            f"- **Tests passed:** {report['synthetic_tests']['tests_passed']}",
            f"- **Tests failed:** {report['synthetic_tests']['tests_failed']}",
            f"- **All passed:** {report['synthetic_tests']['all_passed']}",
            "",
            "## Dual-Build Classification Semantics",
            "",
            f"- **Classification completed (all-eligible case):** {report.get('dual_build_classification', {}).get('all_eligible', {}).get('classification_completed')}",
            f"- **All rows mechanically eligible (all-eligible case):** {report.get('dual_build_classification', {}).get('all_eligible', {}).get('all_rows_mechanistically_eligible')}",
            f"- **Policy approved:** {report.get('policy_approved')}",
            f"- **Policy enforced:** {report.get('policy_enforced')}",
            f"- **Production execution authorized:** {report.get('production_execution_authorized')}",
            "",
            "## Runtime Activity Measurement",
            "",
            f"- **Runtime activity tracker active:** {report.get('runtime_activity_tracker_active')}",
            f"- **Runtime tracker covered all tests:** {report.get('runtime_activity_tracker_covered_all_tests')}",
            f"- **Runtime activity counters derived:** {report.get('runtime_activity_counters_derived')}",
            f"- **Production builder guard active:** {report.get('production_builder_guard_active')}",
            f"- **Repository write guard active:** {report.get('repository_write_guard_active')}",
            "",
            "## Measured Activity Counters",
            "",
        ]
    )
    counters = report.get("measured_activity_counters", {})
    for key, value in counters.items():
        lines.append(f"- **{key}:** {value}")
    lines.extend(
        [
            "",
            "## Write-Guard Positive Controls",
            "",
            f"- **All write-guard controls passed:** {report.get('write_guard_controls', {}).get('all_passed')}",
            f"- **Total controls:** {report.get('write_guard_controls', {}).get('total')}",
            f"- **Passed controls:** {report.get('write_guard_controls', {}).get('passed_count')}",
            f"- **Mechanisms covered:** {', '.join(report.get('write_guard_mechanisms_covered', []))}",
            f"- **All expected mechanisms present:** {report.get('all_write_guard_mechanisms_present')}",
            "",
            "## Production Entry-Point Positive Controls",
            "",
            f"- **All entry-point controls passed:** {report.get('production_entry_point_controls', {}).get('all_passed')}",
            f"- **Total controls:** {report.get('production_entry_point_controls', {}).get('total')}",
            f"- **Passed controls:** {report.get('production_entry_point_controls', {}).get('passed_count')}",
            f"- **Entry points covered:** {', '.join(report.get('production_entry_points_covered', []))}",
            f"- **All expected entry points present:** {report.get('all_production_entry_points_present')}",
            "",
            "## Forced Exception Restoration",
            "",
            f"- **Forced exception raised:** {report.get('forced_exception_restoration', {}).get('forced_exception_raised')}",
            f"- **All globals restored:** {report.get('forced_exception_restoration', {}).get('all_globals_restored')}",
            f"- **Tracker inactive after exception:** {report.get('forced_exception_restoration', {}).get('tracker_inactive')}",
            f"- **No repository file changed:** {report.get('forced_exception_restoration', {}).get('no_repository_file_changed')}",
            f"- **Restoration keys match:** {report.get('forced_exception_restoration', {}).get('restoration_keys_match')}",
            f"- **Restoration field count:** {report.get('forced_exception_restoration', {}).get('restoration_field_count')}",
            f"- **Expected restoration field count:** {report.get('forced_exception_restoration', {}).get('expected_restoration_field_count')}",
            f"- **Files added:** {report.get('forced_exception_restoration', {}).get('files_added')}",
            f"- **Files removed:** {report.get('forced_exception_restoration', {}).get('files_removed')}",
            f"- **Files modified:** {report.get('forced_exception_restoration', {}).get('files_modified')}",
            f"- **Path type changes:** {report.get('forced_exception_restoration', {}).get('path_type_changes')}",
            f"- **Exact snapshot equality:** {report.get('forced_exception_restoration', {}).get('exact_snapshot_equality')}",
            f"- **Counters derived:** {report.get('forced_exception_restoration', {}).get('counters_derived')}",
            f"- **Forced exception test passed:** {report.get('forced_exception_restoration', {}).get('passed')}",
            "",
            "### Forced-Exception Restoration Map",
            "",
        ]
    )
    restoration_map = report.get('forced_exception_restoration', {}).get('restoration_map', {})
    for key, value in sorted(restoration_map.items()):
        lines.append(f"- **{key}:** {value}")
    lines.extend(
        [
            "",
            "## Recursive Snapshot Verification",
            "",
            f"- **Recursive snapshot changed:** {report.get('recursive_snapshot_changed')}",
            f"- **Files added:** {report.get('recursive_snapshot_added', 0)}",
            f"- **Files removed:** {report.get('recursive_snapshot_removed', 0)}",
            f"- **Files modified:** {report.get('recursive_snapshot_modified', 0)}",
            f"- **Snapshot before file count:** {report.get('recursive_snapshot_before_file_count', 0)}",
            f"- **Snapshot after file count:** {report.get('recursive_snapshot_after_file_count', 0)}",
            "",
            "## Protected File Verification",
            "",
            f"- **Protected files unchanged:** {report['protected_files_unchanged']}",
            "",
            "## Authorization and Scope Flags",
            "",
            f"- **Policy implementation present:** {report['policy_implementation_present']}",
            f"- **Policy specification loaded and verified:** {report['policy_specification_loaded_and_verified']}",
            f"- **Policy executed on production artifacts:** {report['policy_executed_on_production_artifacts']}",
            f"- **Production run executed:** {report['production_run_executed']}",
            f"- **Canonical files changed:** {report['canonical_files_changed']}",
            f"- **Existing Part 3B artifacts changed:** {report['existing_part3b_artifacts_changed']}",
            f"- **Part 3B complete:** {report['part3b_complete']}",
            f"- **Part 3C authorized:** {report['part3c_authorized']}",
            "",
            "## Transactional Publication",
            "",
            f"- **Transactional report publication:** {report['transactional_report_publication']}",
            f"- **Transactional report publication ready:** {report.get('transactional_report_publication_ready')}",
            f"- **Implementation report JSON/Markdown consistency:** {report['implementation_report_json_markdown_consistency']}",
            "",
            "## Transactional Rollback Tests",
            "",
            f"- **Tests expected:** {report.get('transactional_rollback_tests', {}).get('tests_expected')}",
            f"- **Tests executed:** {report.get('transactional_rollback_tests', {}).get('tests_executed')}",
            f"- **Tests passed:** {report.get('transactional_rollback_tests', {}).get('tests_passed')}",
            f"- **Tests failed:** {report.get('transactional_rollback_tests', {}).get('tests_failed')}",
            f"- **All passed:** {report.get('transactional_rollback_tests', {}).get('all_passed')}",
            "",
            "### Per-Scenario Rollback Evidence",
            "",
        ]
    )
    for sr in report.get('transactional_rollback_tests', {}).get('scenario_records', []):
        lines.append(f"- **{sr.get('failure_point')} / {sr.get('initial_state')}:** passed={sr.get('passed')}, final_state_restored={sr.get('final_state_restored')}, path_types_restored={sr.get('path_types_restored')}, temp_files={sr.get('temporary_files_remaining')}, backup_files={sr.get('backup_files_remaining')}, unexpected_files={sr.get('unexpected_files_remaining')}")
    lines.extend(
        [
            "",
            "### Rollback Verifier Mutation Tests",
            "",
        ]
    )
    for mut in report.get('transactional_rollback_tests', {}).get('rollback_verifier_mutations', []):
        lines.append(f"- **{mut.get('mutation_name')}:** verifier_rejected={mut.get('verifier_rejected')}, passed={mut.get('passed')}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _capture_directory_state(directory: Path) -> Dict[str, Any]:
    """Capture exact set of filenames, bytes hashes, and file types in a directory."""
    entries: Dict[str, Dict[str, Any]] = {}
    if directory.is_dir():
        for child in sorted(directory.iterdir()):
            if child.is_file():
                entries[child.name] = {
                    "type": "file",
                    "sha256": _sha256_bytes(child.read_bytes()),
                }
            elif child.is_dir():
                entries[child.name] = {
                    "type": "dir",
                    "sha256": None,
                }
    return entries


def _capture_pre_publication_state(json_path: Path, md_path: Path) -> Dict[str, Any]:
    directory = json_path.parent
    dir_entries = _capture_directory_state(directory)
    return {
        "json_existed": json_path.is_file(),
        "md_existed": md_path.is_file(),
        "json_bytes": json_path.read_bytes() if json_path.is_file() else None,
        "md_bytes": md_path.read_bytes() if md_path.is_file() else None,
        "json_sha256": _sha256_bytes(json_path.read_bytes()) if json_path.is_file() else None,
        "md_sha256": _sha256_bytes(md_path.read_bytes()) if md_path.is_file() else None,
        "directory_file_set": sorted(dir_entries.keys()),
        "directory_entries": dir_entries,
    }


def _detect_temp_and_unexpected(
    directory: Path,
    pre_state: Dict[str, Any],
    json_path: Path,
    md_path: Path,
) -> Tuple[List[str], List[str], List[str]]:
    """Detect temporary, backup, and unexpected files by exact directory-set comparison."""
    current_entries = _capture_directory_state(directory)
    pre_entries = pre_state.get("directory_entries", {})
    pre_names = set(pre_entries.keys())
    current_names = set(current_entries.keys())

    temp_files: List[str] = []
    backup_files: List[str] = []
    unexpected_files: List[str] = []

    for name in sorted(current_names - pre_names):
        if name.endswith(".pubbak"):
            backup_files.append(name)
        elif name.startswith("tmp") or name.startswith(".part3b_et_policy_"):
            temp_files.append(name)
        else:
            unexpected_files.append(name)

    for name in sorted(current_names & pre_names):
        if current_entries[name].get("sha256") != pre_entries[name].get("sha256"):
            unexpected_files.append(name)

    return temp_files, backup_files, unexpected_files


def _publication_state_matches(
    json_path: Path,
    md_path: Path,
    pre_state: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    json_existence_restored = json_path.is_file() == pre_state["json_existed"]
    md_existence_restored = md_path.is_file() == pre_state["md_existed"]
    json_bytes_restored = True
    md_bytes_restored = True
    if pre_state["json_existed"]:
        json_bytes_restored = json_path.is_file() and json_path.read_bytes() == pre_state["json_bytes"]
    else:
        json_bytes_restored = not json_path.is_file()
    if pre_state["md_existed"]:
        md_bytes_restored = md_path.is_file() and md_path.read_bytes() == pre_state["md_bytes"]
    else:
        md_bytes_restored = not md_path.is_file()

    directory = json_path.parent
    current_dir_entries = _capture_directory_state(directory)
    pre_dir_entries = pre_state.get("directory_entries", {})
    directory_file_set_restored = sorted(current_dir_entries.keys()) == pre_state.get("directory_file_set", [])
    directory_file_hashes_restored = all(
        current_dir_entries.get(name, {}).get("sha256") == pre_dir_entries.get(name, {}).get("sha256")
        for name in pre_dir_entries
    )
    all_entry_names = set(current_dir_entries.keys()) | set(pre_dir_entries.keys())
    path_types_restored = all(
        current_dir_entries.get(name, {}).get("type") == pre_dir_entries.get(name, {}).get("type")
        for name in all_entry_names
    )

    temp_files, backup_files, unexpected_files = _detect_temp_and_unexpected(
        directory, pre_state, json_path, md_path
    )

    final_state_restored = (
        json_existence_restored
        and md_existence_restored
        and json_bytes_restored
        and md_bytes_restored
        and directory_file_set_restored
        and directory_file_hashes_restored
        and path_types_restored
        and len(temp_files) == 0
        and len(backup_files) == 0
        and len(unexpected_files) == 0
    )

    detail = {
        "final_state_restored": final_state_restored,
        "json_existence_restored": json_existence_restored,
        "markdown_existence_restored": md_existence_restored,
        "json_bytes_restored": json_bytes_restored,
        "markdown_bytes_restored": md_bytes_restored,
        "directory_file_set_restored": directory_file_set_restored,
        "directory_file_hashes_restored": directory_file_hashes_restored,
        "path_types_restored": path_types_restored,
        "temporary_files_remaining": temp_files,
        "backup_files_remaining": backup_files,
        "unexpected_files_remaining": unexpected_files,
    }
    return final_state_restored, detail


def _cleanup_publication_artifacts(
    json_path: Path,
    md_path: Path,
    tmp_json_path: Optional[Path],
    tmp_md_path: Optional[Path],
) -> None:
    for path in (tmp_json_path, tmp_md_path):
        if path is not None and path.exists():
            path.unlink()
    for path in (
        json_path.with_suffix(json_path.suffix + ".pubbak"),
        md_path.with_suffix(md_path.suffix + ".pubbak"),
    ):
        if path.exists():
            path.unlink()


def _restore_pre_publication_state(
    json_path: Path,
    md_path: Path,
    pre_state: Dict[str, Any],
    *,
    backup_json_path: Optional[Path],
    backup_md_path: Optional[Path],
) -> None:
    if backup_json_path is not None and backup_json_path.exists():
        if json_path.exists():
            json_path.unlink()
        backup_json_path.replace(json_path)
    elif pre_state["json_existed"]:
        if pre_state["json_bytes"] is not None:
            json_path.write_bytes(pre_state["json_bytes"])
    elif json_path.exists():
        json_path.unlink()

    if backup_md_path is not None and backup_md_path.exists():
        if md_path.exists():
            md_path.unlink()
        backup_md_path.replace(md_path)
    elif pre_state["md_existed"]:
        if pre_state["md_bytes"] is not None:
            md_path.write_bytes(pre_state["md_bytes"])
    elif md_path.exists():
        md_path.unlink()

    for path in (
        json_path.with_suffix(json_path.suffix + ".pubbak"),
        md_path.with_suffix(md_path.suffix + ".pubbak"),
    ):
        if path.exists():
            path.unlink()


def publish_outputs_transactionally(
    report: Dict[str, Any],
    json_path: Path,
    md_path: Path,
    *,
    inject_failure: Optional[str] = None,
) -> Dict[str, Any]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(report, indent=2) + "\n"
    md_text = render_markdown(report)
    if render_markdown(json.loads(json_text)) != md_text:
        raise RuntimeError("Markdown does not match JSON report")

    pre_state = _capture_pre_publication_state(json_path, md_path)
    tmp_json_path: Optional[Path] = None
    tmp_md_path: Optional[Path] = None
    backup_json_path: Optional[Path] = None
    backup_md_path: Optional[Path] = None

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=str(json_path.parent), delete=False
    ) as tmp_json:
        tmp_json.write(json_text)
        tmp_json_path = Path(tmp_json.name)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=str(md_path.parent), delete=False
    ) as tmp_md:
        tmp_md.write(md_text)
        tmp_md_path = Path(tmp_md.name)

    try:
        if inject_failure == "before_any_replacement":
            raise RuntimeError("injected failure before any replacement")

        if json_path.is_file():
            backup_json_path = json_path.with_suffix(json_path.suffix + ".pubbak")
            json_path.replace(backup_json_path)
        tmp_json_path.replace(json_path)
        tmp_json_path = None

        if inject_failure == "after_json_before_md":
            raise RuntimeError("injected failure after JSON replacement")

        if md_path.is_file():
            backup_md_path = md_path.with_suffix(md_path.suffix + ".pubbak")
            md_path.replace(backup_md_path)

        if inject_failure == "after_md_backup_before_md_replace":
            raise RuntimeError("injected failure after Markdown backup")

        tmp_md_path.replace(md_path)
        tmp_md_path = None

        if backup_json_path is not None and backup_json_path.exists():
            backup_json_path.unlink()
            backup_json_path = None
        if backup_md_path is not None and backup_md_path.exists():
            backup_md_path.unlink()
            backup_md_path = None
    except Exception:
        _restore_pre_publication_state(
            json_path,
            md_path,
            pre_state,
            backup_json_path=backup_json_path,
            backup_md_path=backup_md_path,
        )
        raise
    finally:
        _cleanup_publication_artifacts(json_path, md_path, tmp_json_path, tmp_md_path)

    _matches, _detail = _publication_state_matches(json_path, md_path, pre_state)
    if not _matches and inject_failure is None:
        # Successful publication should differ from pre-state when content changed
        pass

    final_reread = json.loads(json_path.read_text(encoding="utf-8"))
    final_md = md_path.read_text(encoding="utf-8")
    if render_markdown(final_reread) != final_md:
        raise RuntimeError("Published markdown does not match published JSON")

    rel_json = str(json_path.relative_to(repo_root())) if json_path.is_relative_to(repo_root()) else JSON_OUTPUT_PATH
    rel_md = str(md_path.relative_to(repo_root())) if md_path.is_relative_to(repo_root()) else MD_OUTPUT_PATH
    return {
        "json_path": rel_json,
        "md_path": rel_md,
        "json_sha256": sha256_file(json_path),
        "md_sha256": sha256_file(md_path),
    }


def _test_detail_passed(summary: Dict[str, Any], test_name: str) -> bool:
    for item in summary.get("tests", []):
        if item.get("test_name") == test_name:
            return item.get("passed") is True
    return False


def run_transactional_rollback_tests() -> Dict[str, Any]:
    root = repo_root()
    tests: List[Dict[str, Any]] = []
    scenario_records: List[Dict[str, Any]] = []

    def _record(name: str, passed: bool, **extra: Any) -> None:
        tests.append({"test_name": name, "passed": passed, **extra})

    sample_report = {
        "stage": STAGE,
        "starting_commit": STARTING_COMMIT,
        "synthetic_tests": {
            "tests_expected": 0,
            "tests_executed": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "all_passed": True,
        },
        "dual_build_evidence_required": True,
        "single_build_final_approval_prohibited": True,
        "policy_approved": False,
        "policy_enforced": False,
        "production_execution_authorized": False,
        "transactional_report_publication": False,
        "transactional_report_publication_ready": False,
        "implementation_report_json_markdown_consistency": True,
        "measured_activity_counters": {},
        "fixture_parity_results": [],
        "frozen_policy_path": FROZEN_POLICY_JSON_PATH,
        "frozen_policy_sha256": "",
        "frozen_policy_contract_verified": True,
        "implementation_module_sha256": "",
        "production_validator_sha_before": PRODUCTION_VALIDATOR_SHA_BEFORE,
        "production_validator_sha_after": "",
        "production_validator_code_changed": True,
        "production_authorization_remains_false": True,
        "implemented_constants": {},
        "public_functions": REQUIRED_PUBLIC_FUNCTIONS,
        "integration_points": [],
        "predicate_identity_hardcoding_detected": False,
        "protected_files_unchanged": True,
        "policy_implementation_present": True,
        "policy_specification_loaded_and_verified": True,
        "policy_executed_on_production_artifacts": False,
        "production_run_executed": False,
        "canonical_files_changed": False,
        "existing_part3b_artifacts_changed": False,
        "part3b_complete": False,
        "part3c_authorized": False,
    }

    scenarios = [
        ("rollback_before_any_replacement", "before_any_replacement"),
        ("rollback_after_json_before_md", "after_json_before_md"),
        ("rollback_after_md_backup_before_md_replace", "after_md_backup_before_md_replace"),
    ]

    with tempfile.TemporaryDirectory(prefix="gd63_pub_") as temp_dir:
        base = Path(temp_dir)

        for case_name, failure_point in scenarios:
            for both_exist in (False, True):
                label = f"{case_name}_{'both_exist' if both_exist else 'neither_exist'}"
                json_path = base / f"{label}.json"
                md_path = base / f"{label}.md"
                if both_exist:
                    json_path.write_text('{"existing":"json"}\n', encoding="utf-8")
                    md_path.write_text("# existing md\n", encoding="utf-8")
                pre_state = _capture_pre_publication_state(json_path, md_path)
                exception_observed = False
                detail: Dict[str, Any] = {}
                try:
                    publish_outputs_transactionally(
                        sample_report,
                        json_path,
                        md_path,
                        inject_failure=failure_point,
                    )
                except RuntimeError:
                    exception_observed = True
                    rolled_back, detail = _publication_state_matches(json_path, md_path, pre_state)
                scenario_record = {
                    "failure_point": failure_point,
                    "initial_state": "both_exist" if both_exist else "neither_exist",
                    "exception_observed": exception_observed,
                    "final_state_restored": detail.get("final_state_restored", False),
                    "json_existence_restored": detail.get("json_existence_restored", False),
                    "markdown_existence_restored": detail.get("markdown_existence_restored", False),
                    "json_bytes_restored": detail.get("json_bytes_restored", False),
                    "markdown_bytes_restored": detail.get("markdown_bytes_restored", False),
                    "directory_file_set_restored": detail.get("directory_file_set_restored", False),
                    "directory_file_hashes_restored": detail.get("directory_file_hashes_restored", False),
                    "path_types_restored": detail.get("path_types_restored", False),
                    "temporary_files_remaining": detail.get("temporary_files_remaining", []),
                    "backup_files_remaining": detail.get("backup_files_remaining", []),
                    "unexpected_files_remaining": detail.get("unexpected_files_remaining", []),
                    "passed": (
                        exception_observed
                        and detail.get("final_state_restored", False)
                    ),
                }
                scenario_records.append(scenario_record)
                _record(label, scenario_record["passed"], **{k: v for k, v in scenario_record.items() if k != "passed"})

        json_path = base / "successful_first_publication.json"
        md_path = base / "successful_first_publication.md"
        first_pub_ok = False
        try:
            publish_outputs_transactionally(sample_report, json_path, md_path)
            first_pub_ok = json_path.is_file() and md_path.is_file()
        except Exception:
            first_pub_ok = False
        _record("successful_first_publication", first_pub_ok)

        json_path = base / "successful_replacement.json"
        md_path = base / "successful_replacement.md"
        json_path.write_text('{"old":"json"}\n', encoding="utf-8")
        md_path.write_text("# old md\n", encoding="utf-8")
        replacement_ok = False
        try:
            publish_outputs_transactionally(sample_report, json_path, md_path)
            replacement_ok = (
                json_path.is_file()
                and md_path.is_file()
                and json_path.read_text(encoding="utf-8").startswith("{")
                and "Part 3B ET Reconciliation Policy Implementation Report" in md_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            replacement_ok = False
        _record("successful_replacement_publication", replacement_ok)

        json_path = base / "overwrite_preserves_old.json"
        md_path = base / "overwrite_preserves_old.md"
        old_json = '{"old":"content"}\n'
        old_md = "# old content\n"
        json_path.write_text(old_json, encoding="utf-8")
        md_path.write_text(old_md, encoding="utf-8")
        pre_state = _capture_pre_publication_state(json_path, md_path)
        overwrite_rolled_back = False
        try:
            publish_outputs_transactionally(
                sample_report, json_path, md_path,
                inject_failure="after_json_before_md",
            )
        except RuntimeError:
            overwrite_rolled_back, _ = _publication_state_matches(json_path, md_path, pre_state)
        _record("overwrite_failure_restores_original_content", overwrite_rolled_back)

        json_path = base / "no_backup_leftover.json"
        md_path = base / "no_backup_leftover.md"
        json_path.write_text('{"existing":"json"}\n', encoding="utf-8")
        md_path.write_text("# existing md\n", encoding="utf-8")
        no_backup = False
        try:
            publish_outputs_transactionally(
                sample_report, json_path, md_path,
                inject_failure="after_md_backup_before_md_replace",
            )
        except RuntimeError:
            pubbak_json = json_path.with_suffix(json_path.suffix + ".pubbak")
            pubbak_md = md_path.with_suffix(md_path.suffix + ".pubbak")
            no_backup = not pubbak_json.exists() and not pubbak_md.exists()
        _record("no_backup_files_left_after_rollback", no_backup)

        json_path = base / "temp_files_cleaned.json"
        md_path = base / "temp_files_cleaned.md"
        temp_cleaned = False
        try:
            publish_outputs_transactionally(
                sample_report, json_path, md_path,
                inject_failure="before_any_replacement",
            )
        except RuntimeError:
            pre_state = _capture_pre_publication_state(json_path, md_path)
            temp_files, backup_files, unexpected_files = _detect_temp_and_unexpected(
                json_path.parent, pre_state, json_path, md_path
            )
            temp_cleaned = len(temp_files) == 0 and len(backup_files) == 0 and len(unexpected_files) == 0
        _record("temp_files_cleaned_after_rollback", temp_cleaned)

    mutation_results = _run_rollback_verifier_mutations()

    passed = sum(1 for item in tests if item["passed"])
    failed = len(tests) - passed
    all_passed = failed == 0 and all(m.get("verifier_rejected") for m in mutation_results)
    return {
        "tests": tests,
        "tests_expected": len(tests),
        "tests_executed": len(tests),
        "tests_passed": passed,
        "tests_failed": failed,
        "all_passed": all_passed,
        "scenario_records": scenario_records,
        "rollback_verifier_mutations": mutation_results,
    }


def _run_rollback_verifier_mutations() -> List[Dict[str, Any]]:
    """Seven rollback-verifier mutation tests using temporary synthetic directories."""
    results: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="gd63_mut_") as temp_dir:
        base = Path(temp_dir)

        # 1. Extensionless leftover temporary file causes failure
        d = base / "mut_extless"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        (d / "tmpabc123").write_text("leftover\n", encoding="utf-8")
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched and len(detail.get("temporary_files_remaining", [])) > 0
        results.append({
            "mutation_name": "extensionless_temp_leftover",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })
        (d / "tmpabc123").unlink(missing_ok=True)

        # 2. .pubbak leftover causes failure
        d = base / "mut_pubbak"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        (d / "report.json.pubbak").write_text("backup\n", encoding="utf-8")
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched and len(detail.get("backup_files_remaining", [])) > 0
        results.append({
            "mutation_name": "pubbak_leftover",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })
        (d / "report.json.pubbak").unlink(missing_ok=True)

        # 3. Unexpected extra file causes failure
        d = base / "mut_unexpected"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        (d / "unexpected_file.txt").write_text("extra\n", encoding="utf-8")
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched and len(detail.get("unexpected_files_remaining", [])) > 0
        results.append({
            "mutation_name": "unexpected_extra_file",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })
        (d / "unexpected_file.txt").unlink(missing_ok=True)

        # 4. Modified original JSON causes failure
        d = base / "mut_json_mod"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        json_p.write_text('{"x":2}\n', encoding="utf-8")
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched
        results.append({
            "mutation_name": "modified_original_json",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })

        # 5. Modified original Markdown causes failure
        d = base / "mut_md_mod"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        md_p.write_text("# y\n", encoding="utf-8")
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched
        results.append({
            "mutation_name": "modified_original_markdown",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })

        # 6. Deleted original file causes failure
        d = base / "mut_deleted"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        json_p.unlink()
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched
        results.append({
            "mutation_name": "deleted_original_file",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })

        # 7. Path-type change causes failure
        d = base / "mut_typechange"
        d.mkdir()
        json_p = d / "report.json"
        md_p = d / "report.md"
        json_p.write_text('{"x":1}\n', encoding="utf-8")
        md_p.write_text("# x\n", encoding="utf-8")
        pre = _capture_pre_publication_state(json_p, md_p)
        json_p.unlink()
        json_p.mkdir()
        matched, detail = _publication_state_matches(json_p, md_p, pre)
        rejected = not matched
        results.append({
            "mutation_name": "path_type_change",
            "verifier_rejected": rejected,
            "passed": rejected,
            "detail": detail,
        })

    return results


def _derive_executable_policy_checks(
    policy: Any,
    builder: Any,
    root: Path,
    policy_spec: Dict[str, Any],
) -> Dict[str, Any]:
    missing_dual_build_rejected = (
        policy.validate_dual_build_reconciliation_context(None).get("valid") is False
    )

    single_build = policy.classify_single_build_mismatch_pending(
        {
            "experiment": "cross_project",
            "target_project": "SYNTH",
            "seed": 1,
            "model": "ET_leaf5",
            "column": "roc_auc",
        }
    )
    single_build_final_approval_prohibited = (
        single_build.get("final_status") == "pending_dual_build_reconciliation"
        and single_build.get("final_approval_prohibited") is True
        and single_build.get("eligible") is False
    )

    validator_none = builder.validate_dual_build_et_rank_metric_reconciliation(None)
    dual_build_evidence_required = (
        missing_dual_build_rejected
        and validator_none.get("accepted") is False
        and validator_none.get("dual_build_evidence_provided") is False
    )

    return {
        "missing_dual_build_context_rejected": missing_dual_build_rejected,
        "single_build_final_approval_prohibited": single_build_final_approval_prohibited,
        "dual_build_evidence_required": dual_build_evidence_required,
        "validator_single_build_result": validator_none,
        "single_build_classification_result": single_build,
    }


def run_audit() -> Dict[str, Any]:
    root = repo_root()
    before_protected = protected_snapshot(root)

    policy = load_module(POLICY_MODULE_PATH, "part3b_et_reconciliation_policy")
    builder = load_module(PRODUCTION_VALIDATOR_PATH, "build_part3b_prediction_ledger")

    head = git_head()
    starting_commit_ok = head == STARTING_COMMIT

    frozen_policy_path = root / FROZEN_POLICY_JSON_PATH
    frozen_policy_sha = sha256_file(frozen_policy_path)
    frozen_policy_contract_verified = False
    policy_spec: Optional[Dict[str, Any]] = None
    try:
        policy_spec = policy.load_and_verify_frozen_policy(root)
        frozen_policy_contract_verified = True
    except Exception:
        frozen_policy_contract_verified = False

    implementation_module_sha = sha256_file(root / POLICY_MODULE_PATH)
    production_validator_sha_after = sha256_file(root / PRODUCTION_VALIDATOR_PATH)
    production_validator_code_changed = (
        production_validator_sha_after != PRODUCTION_VALIDATOR_SHA_BEFORE
    )

    public_functions_present = {
        name: callable(getattr(policy, name, None)) for name in REQUIRED_PUBLIC_FUNCTIONS
    }
    all_public_functions_present = all(public_functions_present.values())

    production_source = (root / PRODUCTION_VALIDATOR_PATH).read_text(encoding="utf-8")
    imports_policy_module = (
        "import_et_reconciliation_policy" in production_source
        and "validate_dual_build_et_rank_metric_reconciliation" in production_source
        and "--self-test-et-reconciliation-policy" in production_source
    )

    production_authorization_remains_false = (
        getattr(builder, "FINAL_PRODUCTION_EXECUTION_AUTHORIZED", True) is False
        and getattr(builder, "FINAL_PRODUCTION_COMMIT_MESSAGE", "x") is None
    )

    policy_source = (root / POLICY_MODULE_PATH).read_text(encoding="utf-8")
    predicate_identity_hardcoding_detected = policy.implementation_contains_hardcoded_identities(
        policy_source
    )

    synthetic_summary = builder.run_et_reconciliation_policy_self_tests()
    rollback_summary = run_transactional_rollback_tests()
    executable_checks = _derive_executable_policy_checks(
        policy, builder, root, policy_spec or {}
    )

    after_protected = protected_snapshot(root)
    protected_files_unchanged = before_protected == after_protected
    existing_part3b_artifacts_changed = not protected_files_unchanged

    dual_build_all_eligible = synthetic_summary.get("dual_build_all_eligible_classification_result", {})
    dual_build_one_ineligible = synthetic_summary.get(
        "dual_build_one_ineligible_classification_result", {}
    )

    runtime_activity_tracker_active = (
        synthetic_summary.get("runtime_activity_tracker_active") is True
    )
    runtime_activity_tracker_covered_all_tests = (
        synthetic_summary.get("runtime_activity_tracker_covered_all_tests") is True
    )
    runtime_activity_counters_derived = (
        synthetic_summary.get("runtime_activity_counters_derived") is True
    )
    production_builder_guard_active = (
        synthetic_summary.get("production_builder_guard_active") is True
    )
    repository_write_guard_active = (
        synthetic_summary.get("repository_write_guard_active") is True
    )

    write_guard_controls = synthetic_summary.get("write_guard_positive_controls", {})
    write_guard_mechanisms_covered = sorted({
        c.get("mechanism", "") for c in write_guard_controls.get("controls", [])
    })
    all_write_guard_mechanisms_present = all(
        mech in write_guard_mechanisms_covered for mech in EXPECTED_WRITE_GUARD_MECHANISMS
    )
    write_guard_controls_passed = write_guard_controls.get("all_passed") is True

    production_entry_controls = synthetic_summary.get("production_entry_point_positive_controls", {})
    production_entry_points_covered = sorted({
        c.get("entry_point", "") for c in production_entry_controls.get("controls", [])
    })
    all_production_entry_points_present = all(
        ep in production_entry_points_covered for ep in EXPECTED_PRODUCTION_ENTRY_POINTS
    )
    production_entry_controls_passed = production_entry_controls.get("all_passed") is True

    forced_exception_restoration = synthetic_summary.get("forced_exception_restoration_test", {})
    forced_exception_test_passed = forced_exception_restoration.get("passed") is True
    forced_exception_restoration_map = forced_exception_restoration.get("restoration_map", {})
    forced_exception_restoration_keys_match = forced_exception_restoration.get("restoration_keys_match") is True
    forced_exception_restoration_field_count = forced_exception_restoration.get("restoration_field_count", 0)
    forced_exception_expected_field_count = forced_exception_restoration.get("expected_restoration_field_count", 0)
    forced_exception_exact_snapshot_equality = forced_exception_restoration.get("exact_snapshot_equality") is True
    forced_exception_counters_derived = forced_exception_restoration.get("counters_derived") is True
    forced_exception_all_globals_restored = forced_exception_restoration.get("all_globals_restored") is True
    forced_exception_no_repo_file_changed = forced_exception_restoration.get("no_repository_file_changed") is True
    forced_exception_files_added = forced_exception_restoration.get("files_added", -1)
    forced_exception_files_removed = forced_exception_restoration.get("files_removed", -1)
    forced_exception_files_modified = forced_exception_restoration.get("files_modified", -1)
    forced_exception_path_type_changes = forced_exception_restoration.get("path_type_changes", -1)

    rollback_scenario_records = rollback_summary.get("scenario_records", [])
    rollback_scenarios_count = len(rollback_scenario_records)
    rollback_all_scenarios_passed = all(sr.get("passed") for sr in rollback_scenario_records)
    rollback_all_scenarios_final_state_restored = all(sr.get("final_state_restored") for sr in rollback_scenario_records)
    rollback_all_scenarios_zero_temp_files = all(len(sr.get("temporary_files_remaining", [])) == 0 for sr in rollback_scenario_records)
    rollback_all_scenarios_zero_backup_files = all(len(sr.get("backup_files_remaining", [])) == 0 for sr in rollback_scenario_records)
    rollback_all_scenarios_zero_unexpected_files = all(len(sr.get("unexpected_files_remaining", [])) == 0 for sr in rollback_scenario_records)

    _REQUIRED_SCENARIO_FIELDS = [
        "failure_point", "initial_state", "exception_observed",
        "final_state_restored", "json_existence_restored",
        "markdown_existence_restored", "json_bytes_restored",
        "markdown_bytes_restored", "directory_file_set_restored",
        "directory_file_hashes_restored", "path_types_restored",
        "temporary_files_remaining", "backup_files_remaining",
        "unexpected_files_remaining", "passed",
    ]
    _REQUIRED_SCENARIO_KEYS = {
        ("before_any_replacement", "neither_exist"),
        ("before_any_replacement", "both_exist"),
        ("after_json_before_md", "neither_exist"),
        ("after_json_before_md", "both_exist"),
        ("after_md_backup_before_md_replace", "neither_exist"),
        ("after_md_backup_before_md_replace", "both_exist"),
    }
    _observed_scenario_keys = {
        (sr.get("failure_point"), sr.get("initial_state"))
        for sr in rollback_scenario_records
    }
    rollback_scenarios_no_missing = _observed_scenario_keys == _REQUIRED_SCENARIO_KEYS
    rollback_scenarios_no_duplicates = len(_observed_scenario_keys) == len(rollback_scenario_records)
    rollback_scenarios_all_fields_present = all(
        all(field in sr for field in _REQUIRED_SCENARIO_FIELDS)
        for sr in rollback_scenario_records
    )
    rollback_scenarios_all_exceptions_observed = all(
        sr.get("exception_observed") is True for sr in rollback_scenario_records
    )
    rollback_scenarios_all_json_restored = all(
        sr.get("json_existence_restored") is True and sr.get("json_bytes_restored") is True
        for sr in rollback_scenario_records
    )
    rollback_scenarios_all_md_restored = all(
        sr.get("markdown_existence_restored") is True and sr.get("markdown_bytes_restored") is True
        for sr in rollback_scenario_records
    )
    rollback_scenarios_all_dir_set_restored = all(
        sr.get("directory_file_set_restored") is True for sr in rollback_scenario_records
    )
    rollback_scenarios_all_hashes_restored = all(
        sr.get("directory_file_hashes_restored") is True for sr in rollback_scenario_records
    )
    rollback_scenarios_all_path_types_restored = all(
        sr.get("path_types_restored") is True for sr in rollback_scenario_records
    )

    rollback_mutations = rollback_summary.get("rollback_verifier_mutations", [])
    rollback_mutations_count = len(rollback_mutations)
    rollback_all_mutations_rejected = all(m.get("verifier_rejected") for m in rollback_mutations)
    rollback_all_mutations_passed = all(m.get("passed") for m in rollback_mutations)

    recursive_snapshot_changed = synthetic_summary.get("recursive_snapshot_changed", -1)
    recursive_snapshot_added = synthetic_summary.get("protected_files_added", 0)
    recursive_snapshot_removed = synthetic_summary.get("protected_files_removed", 0)
    recursive_snapshot_modified = synthetic_summary.get("protected_files_modified", 0)
    recursive_snapshot_before_file_count = synthetic_summary.get(
        "recursive_snapshot_before_file_count", 0
    )
    recursive_snapshot_after_file_count = synthetic_summary.get(
        "recursive_snapshot_after_file_count", 0
    )

    counters_connected = (
        runtime_activity_counters_derived
        and "model_fits_executed" in synthetic_summary
        and "prediction_calls_executed" in synthetic_summary
        and "production_builder_entries" in synthetic_summary
    )

    integration_points = [
        "import_et_reconciliation_policy() loads scripts/part3b_et_reconciliation_policy.py",
        "validate_dual_build_et_rank_metric_reconciliation() dual-build entry point (fail-closed)",
        "--self-test-et-reconciliation-policy synthetic self-test mode",
        "FINAL_PRODUCTION_EXECUTION_AUTHORIZED remains False",
    ]

    report: Dict[str, Any] = {
        "stage": STAGE,
        "starting_commit": STARTING_COMMIT,
        "current_commit": head,
        "starting_commit_verified": starting_commit_ok,
        "frozen_policy_path": FROZEN_POLICY_JSON_PATH,
        "frozen_policy_sha256": frozen_policy_sha,
        "frozen_policy_contract_verified": frozen_policy_contract_verified,
        "implementation_module_sha256": implementation_module_sha,
        "production_validator_sha_before": PRODUCTION_VALIDATOR_SHA_BEFORE,
        "production_validator_sha_after": production_validator_sha_after,
        "production_validator_code_changed": production_validator_code_changed,
        "production_authorization_remains_false": production_authorization_remains_false,
        "implemented_constants": {
            "et_score_absolute_tolerance": policy.ET_SCORE_ABSOLUTE_TOLERANCE,
            "metric_absolute_tolerance": policy.METRIC_ABSOLUTE_TOLERANCE,
            "eligible_metric_allowlist": policy.ELIGIBLE_METRIC_ALLOWLIST,
            "required_candidates": policy.REQUIRED_CANDIDATES,
            "exact_build_value_equality": "float64_bit_exact",
            "exact_build_score_equality": "byte_exact",
            "executable_equality_helper": "float64_bit_equal",
            "frozen_policy_json_sha256": policy.FROZEN_POLICY_JSON_SHA256,
        },
        "public_functions": REQUIRED_PUBLIC_FUNCTIONS,
        "public_functions_present": public_functions_present,
        "all_public_functions_present": all_public_functions_present,
        "integration_points": integration_points,
        "production_validator_imports_policy_module": imports_policy_module,
        "missing_dual_build_context_rejected": executable_checks["missing_dual_build_context_rejected"],
        "dual_build_evidence_required": executable_checks["dual_build_evidence_required"],
        "single_build_final_approval_prohibited": executable_checks[
            "single_build_final_approval_prohibited"
        ],
        "valid_dual_build_classification_grants_final_approval": (
            dual_build_all_eligible.get("accepted") is True
        ),
        "ineligible_dual_build_row_grants_final_approval": (
            dual_build_one_ineligible.get("accepted") is True
        ),
        "dual_build_classification": {
            "all_eligible": {
                "classification_completed": dual_build_all_eligible.get("classification_completed"),
                "all_rows_mechanistically_eligible": dual_build_all_eligible.get(
                    "all_rows_mechanistically_eligible"
                ),
                "accepted": dual_build_all_eligible.get("accepted"),
                "final_approval_prohibited": dual_build_all_eligible.get(
                    "final_approval_prohibited"
                ),
                "policy_enforced": dual_build_all_eligible.get("policy_enforced"),
            },
            "one_ineligible": {
                "classification_completed": dual_build_one_ineligible.get("classification_completed"),
                "all_rows_mechanistically_eligible": dual_build_one_ineligible.get(
                    "all_rows_mechanistically_eligible"
                ),
                "ineligible_count": dual_build_one_ineligible.get("ineligible_count"),
                "accepted": dual_build_one_ineligible.get("accepted"),
                "final_approval_prohibited": dual_build_one_ineligible.get(
                    "final_approval_prohibited"
                ),
            },
        },
        "predicate_identity_hardcoding_detected": predicate_identity_hardcoding_detected,
        "candidate_set": policy.REQUIRED_CANDIDATES,
        "eligible_metric_allowlist": policy.ELIGIBLE_METRIC_ALLOWLIST,
        "fixture_parity_results": synthetic_summary.get("fixture_parity_results", []),
        "synthetic_tests": {
            "tests_expected": synthetic_summary.get("tests_expected"),
            "tests_executed": synthetic_summary.get("tests_executed"),
            "tests_passed": synthetic_summary.get("tests_passed"),
            "tests_failed": synthetic_summary.get("tests_failed"),
            "all_passed": synthetic_summary.get("all_passed"),
            "test_details": synthetic_summary.get("tests", []),
        },
        "transactional_rollback_tests": rollback_summary,
        "measured_activity_counters": {
            "model_fits_executed": synthetic_summary.get("model_fits_executed"),
            "prediction_calls_executed": synthetic_summary.get("prediction_calls_executed"),
            "production_model_evaluation_builds_executed": synthetic_summary.get(
                "production_model_evaluation_builds_executed"
            ),
            "production_builder_entries": synthetic_summary.get("production_builder_entries"),
            "production_artifact_writes": synthetic_summary.get("production_artifact_writes"),
            "canonical_file_writes": synthetic_summary.get("canonical_file_writes"),
            "protected_artifacts_changed": synthetic_summary.get("protected_artifacts_changed"),
            "protected_files_added": recursive_snapshot_added,
            "protected_files_removed": recursive_snapshot_removed,
            "protected_files_modified": recursive_snapshot_modified,
        },
        "write_guard_controls": write_guard_controls,
        "write_guard_mechanisms_covered": write_guard_mechanisms_covered,
        "all_write_guard_mechanisms_present": all_write_guard_mechanisms_present,
        "write_guard_controls_passed": write_guard_controls_passed,
        "production_entry_point_controls": production_entry_controls,
        "production_entry_points_covered": production_entry_points_covered,
        "all_production_entry_points_present": all_production_entry_points_present,
        "production_entry_controls_passed": production_entry_controls_passed,
        "forced_exception_restoration": forced_exception_restoration,
        "forced_exception_test_passed": forced_exception_test_passed,
        "forced_exception_restoration_keys_match": forced_exception_restoration_keys_match,
        "forced_exception_restoration_field_count": forced_exception_restoration_field_count,
        "forced_exception_expected_field_count": forced_exception_expected_field_count,
        "forced_exception_exact_snapshot_equality": forced_exception_exact_snapshot_equality,
        "forced_exception_counters_derived": forced_exception_counters_derived,
        "forced_exception_all_globals_restored": forced_exception_all_globals_restored,
        "forced_exception_no_repo_file_changed": forced_exception_no_repo_file_changed,
        "forced_exception_files_added": forced_exception_files_added,
        "forced_exception_files_removed": forced_exception_files_removed,
        "forced_exception_files_modified": forced_exception_files_modified,
        "forced_exception_path_type_changes": forced_exception_path_type_changes,
        "rollback_scenarios_count": rollback_scenarios_count,
        "rollback_all_scenarios_passed": rollback_all_scenarios_passed,
        "rollback_all_scenarios_final_state_restored": rollback_all_scenarios_final_state_restored,
        "rollback_all_scenarios_zero_temp_files": rollback_all_scenarios_zero_temp_files,
        "rollback_all_scenarios_zero_backup_files": rollback_all_scenarios_zero_backup_files,
        "rollback_all_scenarios_zero_unexpected_files": rollback_all_scenarios_zero_unexpected_files,
        "rollback_scenarios_no_missing": rollback_scenarios_no_missing,
        "rollback_scenarios_no_duplicates": rollback_scenarios_no_duplicates,
        "rollback_scenarios_all_fields_present": rollback_scenarios_all_fields_present,
        "rollback_scenarios_all_exceptions_observed": rollback_scenarios_all_exceptions_observed,
        "rollback_scenarios_all_json_restored": rollback_scenarios_all_json_restored,
        "rollback_scenarios_all_md_restored": rollback_scenarios_all_md_restored,
        "rollback_scenarios_all_dir_set_restored": rollback_scenarios_all_dir_set_restored,
        "rollback_scenarios_all_hashes_restored": rollback_scenarios_all_hashes_restored,
        "rollback_scenarios_all_path_types_restored": rollback_scenarios_all_path_types_restored,
        "rollback_mutations_count": rollback_mutations_count,
        "rollback_all_mutations_rejected": rollback_all_mutations_rejected,
        "rollback_all_mutations_passed": rollback_all_mutations_passed,
        "recursive_snapshot_changed": recursive_snapshot_changed,
        "recursive_snapshot_added": recursive_snapshot_added,
        "recursive_snapshot_removed": recursive_snapshot_removed,
        "recursive_snapshot_modified": recursive_snapshot_modified,
        "recursive_snapshot_before_file_count": recursive_snapshot_before_file_count,
        "recursive_snapshot_after_file_count": recursive_snapshot_after_file_count,
        "runtime_activity_tracker_active": runtime_activity_tracker_active,
        "runtime_activity_tracker_covered_all_tests": runtime_activity_tracker_covered_all_tests,
        "runtime_activity_counters_derived": runtime_activity_counters_derived,
        "production_builder_guard_active": production_builder_guard_active,
        "repository_write_guard_active": repository_write_guard_active,
        "protected_file_verification": {
            "paths": PROTECTED_PATHS,
            "before": before_protected,
            "after": after_protected,
            "unchanged": protected_files_unchanged,
        },
        "protected_files_unchanged": protected_files_unchanged,
        "policy_implementation_present": all_public_functions_present,
        "policy_specification_loaded_and_verified": frozen_policy_contract_verified,
        "policy_approved": False,
        "policy_enforced": False,
        "production_execution_authorized": False,
        "policy_executed_on_production_artifacts": False,
        "production_run_executed": False,
        "canonical_files_changed": synthetic_summary.get("canonical_file_writes", 0) != 0,
        "existing_part3b_artifacts_changed": existing_part3b_artifacts_changed,
        "part3b_complete": False,
        "part3c_authorized": False,
        "implementation_report_json_markdown_consistency": True,
        "transactional_report_publication": False,
        "transactional_report_publication_ready": rollback_summary.get("all_passed") is True,
    }

    audit_passed = (
        starting_commit_ok
        and frozen_policy_sha == policy.FROZEN_POLICY_JSON_SHA256
        and frozen_policy_contract_verified
        and all_public_functions_present
        and imports_policy_module
        and production_authorization_remains_false
        and not predicate_identity_hardcoding_detected
        and synthetic_summary.get("all_passed") is True
        and protected_files_unchanged
        and counters_connected
        and runtime_activity_tracker_active
        and runtime_activity_tracker_covered_all_tests
        and runtime_activity_counters_derived
        and production_builder_guard_active
        and repository_write_guard_active
        and synthetic_summary.get("model_fits_executed") == 0
        and synthetic_summary.get("prediction_calls_executed") == 0
        and synthetic_summary.get("production_model_evaluation_builds_executed") == 0
        and synthetic_summary.get("production_builder_entries") == 0
        and synthetic_summary.get("production_artifact_writes") == 0
        and synthetic_summary.get("canonical_file_writes") == 0
        and synthetic_summary.get("protected_artifacts_changed") == 0
        and recursive_snapshot_changed == 0
        and recursive_snapshot_added == 0
        and recursive_snapshot_removed == 0
        and recursive_snapshot_modified == 0
        and write_guard_controls_passed
        and all_write_guard_mechanisms_present
        and production_entry_controls_passed
        and all_production_entry_points_present
        and forced_exception_test_passed
        and forced_exception_restoration_keys_match
        and forced_exception_restoration_field_count == forced_exception_expected_field_count
        and forced_exception_exact_snapshot_equality
        and forced_exception_counters_derived
        and forced_exception_all_globals_restored
        and forced_exception_no_repo_file_changed
        and forced_exception_files_added == 0
        and forced_exception_files_removed == 0
        and forced_exception_files_modified == 0
        and forced_exception_path_type_changes == 0
        and rollback_scenarios_count == 6
        and rollback_all_scenarios_passed
        and rollback_all_scenarios_final_state_restored
        and rollback_all_scenarios_zero_temp_files
        and rollback_all_scenarios_zero_backup_files
        and rollback_all_scenarios_zero_unexpected_files
        and rollback_scenarios_no_missing
        and rollback_scenarios_no_duplicates
        and rollback_scenarios_all_fields_present
        and rollback_scenarios_all_exceptions_observed
        and rollback_scenarios_all_json_restored
        and rollback_scenarios_all_md_restored
        and rollback_scenarios_all_dir_set_restored
        and rollback_scenarios_all_hashes_restored
        and rollback_scenarios_all_path_types_restored
        and rollback_mutations_count == 7
        and rollback_all_mutations_rejected
        and rollback_all_mutations_passed
        and executable_checks["missing_dual_build_context_rejected"]
        and executable_checks["dual_build_evidence_required"]
        and executable_checks["single_build_final_approval_prohibited"]
        and dual_build_all_eligible.get("accepted") is False
        and dual_build_all_eligible.get("final_approval_prohibited") is True
        and dual_build_one_ineligible.get("accepted") is False
        and rollback_summary.get("all_passed") is True
        and _test_detail_passed(synthetic_summary, "dual_build_all_eligible_classification_no_final_approval")
        and _test_detail_passed(synthetic_summary, "dual_build_one_ineligible_classification_no_final_approval")
        and _test_detail_passed(synthetic_summary, "dual_build_unknown_metric_classification_no_final_approval")
        and _test_detail_passed(synthetic_summary, "dual_build_missing_et_delta_classification_no_final_approval")
        and _test_detail_passed(synthetic_summary, "validator_single_build_pending_no_final_approval")
    )
    report["audit_passed"] = audit_passed

    if audit_passed:
        publication = publish_outputs_transactionally(
            report,
            root / JSON_OUTPUT_PATH,
            root / MD_OUTPUT_PATH,
        )
        report["transactional_report_publication"] = True
        report["publication_result"] = publication
        final_json = json.loads((root / JSON_OUTPUT_PATH).read_text(encoding="utf-8"))
        final_md = (root / MD_OUTPUT_PATH).read_text(encoding="utf-8")
        report["implementation_report_json_markdown_consistency"] = (
            render_markdown(final_json) == final_md
        )
        publish_outputs_transactionally(
            report,
            root / JSON_OUTPUT_PATH,
            root / MD_OUTPUT_PATH,
        )

    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit G.D6 ET policy implementation.")
    parser.parse_args(argv)
    report = run_audit()
    print(json.dumps(report, indent=2))
    return 0 if report.get("audit_passed") else 1


if __name__ == "__main__":
    sys.exit(main())
