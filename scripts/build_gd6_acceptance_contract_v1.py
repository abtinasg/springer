#!/usr/bin/env python3
"""Part 3B.2R.1-G.D6-F0: Build acceptance contract and benchmark v1.0."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


STARTING_COMMIT = "7dbc206037250b1181aed94bfa7326d79df814fd"
CONTRACT_ID = "SEMIT-GD6-ACCEPTANCE-CONTRACT"
CONTRACT_VERSION = "1.0"
BENCHMARK_ID = "SEMIT-GD6-BENCHMARK"
BENCHMARK_VERSION = "1.0"
FREEZE_MANIFEST_ID = "SEMIT-GD6-CONTRACT-FREEZE-MANIFEST"
FREEZE_MANIFEST_VERSION = "1.0"
STAGE = "Part 3B.2R.1-G.D6-F0.2"

CONTRACT_JSON_PATH = "reports/gd6_acceptance_contract_v1.json"
CONTRACT_MD_PATH = "reports/gd6_acceptance_contract_v1.md"
BENCHMARK_JSON_PATH = "reports/gd6_benchmark_manifest_v1.json"
BENCHMARK_MD_PATH = "reports/gd6_benchmark_manifest_v1.md"
ENV_JSON_PATH = "reports/gd6_reference_environment_v1.json"
FREEZE_MANIFEST_PATH = "reports/gd6_contract_freeze_manifest_v1.json"

AUTHORIZED_FILES = [
    "scripts/build_gd6_acceptance_contract_v1.py",
    "scripts/verify_gd6_acceptance_contract_v1.py",
    "reports/gd6_acceptance_contract_v1.json",
    "reports/gd6_acceptance_contract_v1.md",
    "reports/gd6_benchmark_manifest_v1.json",
    "reports/gd6_benchmark_manifest_v1.md",
    "reports/gd6_reference_environment_v1.json",
    "reports/gd6_contract_freeze_manifest_v1.json",
]

# --- Exact sets extracted from starting-commit repository ---

WRITE_GUARD_MECHANISMS = [
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

WRITE_GUARD_CONTROL_TARGETS = [
    "results/part1_full_reproduction/canonical.csv",
    "results/part3b_prediction_ledger/ledger.csv",
    "reports/part3b_et_policy_implementation.json",
]

PROTECTED_ARTIFACT_PATHS = [
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

PRODUCTION_ENTRY_POINTS = [
    "build_core_bundle",
    "fit_event_candidates",
    "build_prediction_rows",
    "execute_postbuild_integration",
]

RESTORATION_KEYS = [
    "sys_profile_restored",
    "builtins_open_restored",
    "io_open_restored",
    "path_open_restored",
    "path_write_text_restored",
    "path_write_bytes_restored",
    "path_touch_restored",
    "path_replace_restored",
    "path_rename_restored",
    "os_open_restored",
    "os_replace_restored",
    "os_rename_restored",
    "shutil_copy_restored",
    "shutil_copy2_restored",
    "shutil_copyfile_restored",
    "shutil_move_restored",
    "build_core_bundle_restored",
    "fit_event_candidates_restored",
    "build_prediction_rows_restored",
    "execute_postbuild_integration_restored",
]

FORCED_EXCEPTION_FIXTURE_PATHS = [
    "reports/part3b_et_policy_implementation.json",
    "results/part1_full_reproduction/canonical.csv",
    "results/part3b_prediction_ledger/ledger.csv",
]

ROLLBACK_SCENARIOS = [
    {"failure_point": "before_any_replacement", "initial_state": "neither_exist"},
    {"failure_point": "before_any_replacement", "initial_state": "both_exist"},
    {"failure_point": "after_json_before_md", "initial_state": "neither_exist"},
    {"failure_point": "after_json_before_md", "initial_state": "both_exist"},
    {"failure_point": "after_md_backup_before_md_replace", "initial_state": "neither_exist"},
    {"failure_point": "after_md_backup_before_md_replace", "initial_state": "both_exist"},
]

ROLLBACK_MUTATIONS = [
    "extensionless_temp_leftover",
    "pubbak_leftover",
    "unexpected_extra_file",
    "modified_original_json",
    "modified_original_markdown",
    "deleted_original_file",
    "path_type_change",
]

PRESERVATION_CONDITIONS = [
    {"condition": "model_fits_executed", "expected": 0},
    {"condition": "prediction_calls_executed", "expected": 0},
    {"condition": "production_model_evaluation_builds_executed", "expected": 0},
    {"condition": "production_builder_entries", "expected": 0},
    {"condition": "production_artifact_writes", "expected": 0},
    {"condition": "canonical_file_writes", "expected": 0},
    {"condition": "protected_artifacts_changed", "expected": 0},
    {"condition": "protected_files_added", "expected": 0},
    {"condition": "protected_files_removed", "expected": 0},
    {"condition": "protected_files_modified", "expected": 0},
    {"condition": "production_run_executed", "expected": False},
    {"condition": "policy_executed_on_production_artifacts", "expected": False},
    {"condition": "policy_approved", "expected": False},
    {"condition": "policy_enforced", "expected": False},
    {"condition": "production_execution_authorized", "expected": False},
    {"condition": "part3b_complete", "expected": False},
    {"condition": "part3c_authorized", "expected": False},
]

REPORT_INTEGRITY_CONDITIONS = [
    "final_json_parses",
    "markdown_generated_from_final_json",
    "render_markdown_equals_final_markdown",
    "no_self_referential_publication_result_hash_persisted",
    "no_stale_preliminary_publication_hash_persisted",
    "repository_relative_paths_only",
    "no_local_absolute_path",
    "no_editor_specific_cci_reference",
    "no_unsupported_scientific_claim",
]

TRUSTED_INFRASTRUCTURE = [
    "python_interpreter",
    "python_standard_library",
    "operating_system",
    "filesystem_implementation",
    "git_implementation",
    "sha256_implementation",
    "cpu",
    "memory_hardware",
    "github_hosting_infrastructure",
    "installed_third_party_libraries_at_recorded_versions",
    "absence_of_deliberate_malicious_tampering_below_repository_level",
]

IN_SCOPE_COMPONENTS = [
    "frozen_reconciliation_policy_implementation",
    "integration_points_used_by_gd6",
    "benchmark_fixtures",
    "benchmark_expected_outcomes",
    "write_guards",
    "production_entry_guards",
    "restoration_logic",
    "rollback_logic",
    "protected_artifact_comparison",
    "report_generation",
    "json_markdown_consistency",
    "frozen_verifier",
    "environment_and_provenance_records",
]

SCIENTIFIC_CLAIMS = [
    {
        "claim_id": "CLAIM-A",
        "title": "Correct Classification",
        "statement": "The frozen policy implementation classifies the defined valid and invalid cases according to the frozen reconciliation policy and benchmark. This claim is bounded to the listed benchmark and invariants. It is not a claim of universal correctness.",
        "basis": [
            {
                "basis_type": "internal_project_evidence",
                "source_id": "scripts/build_part3b_prediction_ledger.py",
                "supported_proposition": "run_et_reconciliation_policy_self_tests() defines the exact test cases for classification",
            },
            {
                "basis_type": "external_methodological_source",
                "source_id": "MB-01",
                "supported_proposition": "bounded testing scope",
            },
        ],
    },
    {
        "claim_id": "CLAIM-B",
        "title": "No Unauthorized Approval or Enforcement",
        "statement": "G.D6 classification must never independently produce final approval, policy enforcement, production authorization, Part 3B completion, or Part 3C authorization.",
        "basis": [
            {
                "basis_type": "internal_project_evidence",
                "source_id": "reports/part3b_et_policy_implementation.json",
                "supported_proposition": "policy_approved, policy_enforced, production_execution_authorized, part3b_complete, part3c_authorized are all false",
            },
            {
                "basis_type": "external_methodological_source",
                "source_id": "MB-02",
                "supported_proposition": "test completion criteria",
            },
        ],
    },
    {
        "claim_id": "CLAIM-C",
        "title": "Artifact Preservation",
        "statement": "The G.D6 verification process must not alter canonical Part 1 artifacts, existing Part 3B artifacts, frozen policy evidence, or frozen reconciliation evidence.",
        "basis": [
            {
                "basis_type": "internal_project_evidence",
                "source_id": "reports/part3b_et_policy_implementation.json",
                "supported_proposition": "protected_files_unchanged is true and recursive_snapshot_changed is 0",
            },
            {
                "basis_type": "external_methodological_source",
                "source_id": "MB-05",
                "supported_proposition": "versioned development evidence",
            },
        ],
    },
    {
        "claim_id": "CLAIM-D",
        "title": "Recoverability",
        "statement": "After an injected exception or transactional-publication failure, patched global objects must be restored, protected files must retain their prior state, temporary and backup files must not remain, and publication state must be restored.",
        "basis": [
            {
                "basis_type": "internal_project_evidence",
                "source_id": "reports/part3b_et_policy_implementation.json",
                "supported_proposition": "forced_exception_test_passed is true and rollback_all_scenarios_passed is true",
            },
            {
                "basis_type": "external_methodological_source",
                "source_id": "MB-02",
                "supported_proposition": "planned and documented test processes",
            },
        ],
    },
    {
        "claim_id": "CLAIM-E",
        "title": "Reproducible Verification",
        "statement": "An independent evaluator must be able to execute the frozen verifier in a clean environment using the documented command and obtain the same Pass/Fail decision.",
        "basis": [
            {
                "basis_type": "internal_project_evidence",
                "source_id": "scripts/audit_part3b_et_policy_implementation.py",
                "supported_proposition": "existing verifier pattern with documented execution command",
            },
            {
                "basis_type": "external_methodological_source",
                "source_id": "MB-03",
                "supported_proposition": "documenting research sufficiently for independent verification",
            },
            {
                "basis_type": "external_methodological_source",
                "source_id": "MB-04",
                "supported_proposition": "independent evaluation of computational artifacts",
            },
        ],
    },
]

METHODOLOGICAL_BASIS = [
    {
        "source_id": "MB-01",
        "title": "ISO/IEC/IEEE 29119-1:2022 — Software and systems engineering — Software testing — Part 1: General concepts",
        "issuer": "ISO/IEC/IEEE",
        "version_or_year": "2022",
        "authority_type": "standard",
        "supported_use": [
            "terminology for software testing",
            "explicit test objectives",
            "test conditions and evidence",
            "bounded testing scope",
        ],
        "unsupported_claims": [
            "ISO compliance",
            "ISO certification",
        ],
    },
    {
        "source_id": "MB-02",
        "title": "ISO/IEC/IEEE 29119-2:2021 — Software and systems engineering — Software testing — Part 2: Test processes",
        "issuer": "ISO/IEC/IEEE",
        "version_or_year": "2021",
        "authority_type": "standard",
        "supported_use": [
            "planned and documented test processes",
            "test monitoring",
            "test completion criteria",
            "traceable test work products",
        ],
        "unsupported_claims": [
            "ISO compliance",
            "ISO certification",
            "reproduction of inaccessible copyrighted standard text",
        ],
    },
    {
        "source_id": "MB-03",
        "title": "IEEE Author Center — Research Reproducibility",
        "issuer": "IEEE",
        "version_or_year": "current",
        "authority_type": "official_guidance",
        "supported_use": [
            "documenting research sufficiently for independent verification",
            "preserving code, data, and research outputs",
            "recording execution information",
        ],
        "unsupported_claims": [],
    },
    {
        "source_id": "MB-04",
        "title": "ACM Data & Software Artifacts / Artifact Review and Badging, Version 1.1",
        "issuer": "ACM",
        "version_or_year": "1.1",
        "authority_type": "official_guidance",
        "supported_use": [
            "artifact completeness",
            "artifact usability",
            "relationship between artifacts and paper claims",
            "independent evaluation of computational artifacts",
        ],
        "unsupported_claims": [
            "ACM badge has been awarded",
        ],
    },
    {
        "source_id": "MB-05",
        "title": "NIST SP 800-218, Secure Software Development Framework, Version 1.1",
        "issuer": "NIST",
        "version_or_year": "1.1",
        "authority_type": "standard",
        "supported_use": [
            "versioned development evidence",
            "provenance",
            "verification practices",
            "documented software-development controls",
        ],
        "unsupported_claims": [
            "NIST-certified",
            "security-certified",
        ],
    },
]

PROHIBITED_CLAIMS = [
    "formal_verification",
    "mathematical_proof_of_total_correctness",
    "absence_of_all_possible_defects",
    "ISO_certification",
    "IEEE_certification",
    "ACM_certification",
    "NIST_certification",
    "guaranteed_Q2_or_Q3_journal_acceptance",
    "security_against_malicious_operating_systems",
    "verification_of_python_git_sha256_cpu_memory_or_operating_system",
    "completion_of_Part_3B",
    "authorization_of_Part_3C",
    "approval_of_the_policy",
    "enforcement_of_the_policy",
    "authorization_of_production_execution",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_module(rel_path: str, module_name: str) -> Any:
    path = repo_root() / rel_path
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module_from_path(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def worktree_at_commit(commit: str):
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="gd6_worktree_") as wt_dir:
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", wt_dir, commit],
            capture_output=True, text=True, cwd=str(root),
        )
        if result.returncode != 0:
            raise RuntimeError(f"git worktree add failed: {result.stderr}")
        try:
            yield Path(wt_dir)
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", wt_dir],
                capture_output=True, text=True, cwd=str(root),
            )


def extract_write_guard_controls_from_worktree() -> Dict[str, Any]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        builder = load_module_from_path(
            wt / "scripts/build_part3b_prediction_ledger.py",
            "build_part3b_prediction_ledger_wt",
        )
        result = builder._gd6_run_write_guard_positive_controls()
        controls = result.get("controls", [])
        mechanisms = sorted({c["mechanism"] for c in controls})
        targets = sorted({c["target"] for c in controls})
        pairs = sorted([(c["mechanism"], c["target"]) for c in controls])
        return {
            "mechanisms": mechanisms,
            "targets": targets,
            "pairs": pairs,
            "control_count": len(controls),
            "unique_pair_count": len(pairs),
            "all_passed": result.get("all_passed"),
        }


def extract_production_entry_points_from_worktree() -> List[str]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        builder = load_module_from_path(
            wt / "scripts/build_part3b_prediction_ledger.py",
            "build_part3b_prediction_ledger_wt",
        )
        return list(builder._GD6_PRODUCTION_ENTRY_POINTS)


def extract_restoration_keys_from_worktree() -> List[str]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        builder = load_module_from_path(
            wt / "scripts/build_part3b_prediction_ledger.py",
            "build_part3b_prediction_ledger_wt",
        )
        return list(builder._GD6_FORCED_EXCEPTION_RESTORATION_KEYS)


def extract_forced_exception_fixture_paths_from_worktree() -> List[str]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        builder = load_module_from_path(
            wt / "scripts/build_part3b_prediction_ledger.py",
            "build_part3b_prediction_ledger_wt",
        )
        return list(builder._GD6_FORCED_EXCEPTION_FIXTURE_PATHS)


def extract_rollback_scenarios_from_worktree() -> List[Dict[str, str]]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        auditor = load_module_from_path(
            wt / "scripts/audit_part3b_et_policy_implementation.py",
            "audit_part3b_et_policy_implementation_wt",
        )
        result = auditor.run_transactional_rollback_tests()
        records = result.get("scenario_records", [])
        scenarios = [
            {"failure_point": r["failure_point"], "initial_state": r["initial_state"]}
            for r in records
        ]
        return scenarios


def extract_rollback_mutations_from_worktree() -> List[str]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        auditor = load_module_from_path(
            wt / "scripts/audit_part3b_et_policy_implementation.py",
            "audit_part3b_et_policy_implementation_wt",
        )
        return sorted(auditor.REQUIRED_ROLLBACK_MUTATIONS)


def extract_protected_artifact_paths_from_worktree() -> List[str]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        builder = load_module_from_path(
            wt / "scripts/build_part3b_prediction_ledger.py",
            "build_part3b_prediction_ledger_wt",
        )
        return list(builder.GD6_PROTECTED_ARTIFACT_PATHS)


def extract_semantic_test_ids_from_worktree() -> Dict[str, Any]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        builder = load_module_from_path(
            wt / "scripts/build_part3b_prediction_ledger.py",
            "build_part3b_prediction_ledger_wt",
        )
        summary = builder.run_et_reconciliation_policy_self_tests()
        tests = summary.get("tests", [])
        test_ids = [t["test_name"] for t in tests]
        return {
            "test_count": len(tests),
            "test_ids": test_ids,
            "tests_expected": summary.get("tests_expected"),
            "all_passed": summary.get("all_passed"),
        }


def extract_fixture_parity_records_from_worktree() -> List[Dict[str, Any]]:
    with worktree_at_commit(STARTING_COMMIT) as wt:
        policy = load_module_from_path(
            wt / "scripts/part3b_et_reconciliation_policy.py",
            "part3b_et_reconciliation_policy_wt",
        )
        spec = policy.load_and_verify_frozen_policy(wt)
        fixtures = spec.get("regression_fixtures", [])
        records = []
        for fx in fixtures:
            records.append({
                "event_id": fx.get("event_id"),
                "experiment": fx.get("experiment"),
                "target_project": fx.get("target_project"),
                "seed": fx.get("seed"),
                "model": fx.get("model"),
                "selected_candidate": fx.get("selected_candidate"),
                "selection_mode": fx.get("selection_mode"),
                "column": fx.get("column"),
                "expected_result": "pass" if fx.get("mechanistically_eligible_under_frozen_policy") else "reject",
                "currently_approved_exception": fx.get("currently_approved_exception"),
                "source_artifact": "reports/part3b_et_reconciliation_policy.json",
            })
        return records


def deterministic_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def extract_semantic_test_ids() -> Dict[str, Any]:
    builder = load_module(
        "scripts/build_part3b_prediction_ledger.py",
        "build_part3b_prediction_ledger",
    )
    summary = builder.run_et_reconciliation_policy_self_tests()
    tests = summary.get("tests", [])
    test_ids = [t["test_name"] for t in tests]
    return {
        "test_count": len(tests),
        "test_ids": test_ids,
        "tests_expected": summary.get("tests_expected"),
        "all_passed": summary.get("all_passed"),
    }


def extract_fixture_parity_records() -> List[Dict[str, Any]]:
    policy = load_module(
        "scripts/part3b_et_reconciliation_policy.py",
        "part3b_et_reconciliation_policy",
    )
    root = repo_root()
    spec = policy.load_and_verify_frozen_policy(root)
    fixtures = spec.get("regression_fixtures", [])
    records = []
    for fx in fixtures:
        records.append({
            "event_id": fx.get("event_id"),
            "experiment": fx.get("experiment"),
            "target_project": fx.get("target_project"),
            "seed": fx.get("seed"),
            "model": fx.get("model"),
            "selected_candidate": fx.get("selected_candidate"),
            "selection_mode": fx.get("selection_mode"),
            "column": fx.get("column"),
            "expected_result": "pass" if fx.get("mechanistically_eligible_under_frozen_policy") else "reject",
            "currently_approved_exception": fx.get("currently_approved_exception"),
            "source_artifact": "reports/part3b_et_reconciliation_policy.json",
        })
    return records


def build_reference_environment() -> Dict[str, Any]:
    root = repo_root()
    dep_files: Dict[str, Any] = {}
    for rel in ["requirements.txt", "requirements_locked.txt"]:
        p = root / rel
        if p.is_file():
            dep_files[rel] = {
                "present": True,
                "sha256": sha256_file(p),
            }
        else:
            dep_files[rel] = {"present": False}

    import numpy
    import pandas
    import sklearn
    import scipy
    import openpyxl

    installed_packages = {
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scikit-learn": sklearn.__version__,
        "scipy": scipy.__version__,
        "openpyxl": openpyxl.__version__,
    }

    git_version = subprocess.run(
        ["git", "--version"], capture_output=True, text=True
    ).stdout.strip()

    return {
        "python_full_version": platform.python_version(),
        "implementation_name": platform.python_implementation(),
        "operating_system_name": platform.system(),
        "operating_system_version": platform.release(),
        "machine_architecture": platform.machine(),
        "dependency_declaration_files": dep_files,
        "installed_packages_directly_imported_by_gd6_scripts": installed_packages,
        "git_version": git_version,
        "starting_commit": STARTING_COMMIT,
        "branch": "major-revision-analysis-v2",
    }


def build_normative_clauses() -> List[Dict[str, Any]]:
    clauses = [
        {
            "clause_id": "NC-01",
            "statement": "G.D6 Accepted = every mandatory contract condition passes.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-02",
                    "supported_proposition": "test completion criteria",
                },
            ],
        },
        {
            "clause_id": "NC-02",
            "statement": "No weighted score, no majority vote, no partial acceptance, no discretionary override, no compensation between failed and passed conditions. One failed mandatory condition means G.D6 is not accepted.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-02",
                    "supported_proposition": "test completion criteria",
                },
            ],
        },
        {
            "clause_id": "NC-03",
            "statement": "The contract itself must not mark G.D6 as accepted. It only defines the future decision rule.",
            "basis": [
                {
                    "basis_type": "internal_project_evidence",
                    "source_id": "reports/part3b_et_reconciliation_policy.json",
                    "supported_proposition": "policy_status is specified_not_enforced",
                },
            ],
        },
        {
            "clause_id": "NC-04",
            "statement": "After Acceptance Contract v1.0 and Benchmark Manifest v1.0 are independently accepted and frozen, no new G.D6 acceptance criterion may be introduced during the same evaluation cycle.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-02",
                    "supported_proposition": "test completion criteria",
                },
            ],
        },
        {
            "clause_id": "NC-05",
            "statement": "If the frozen verifier passes every mandatory benchmark item, G.D6 must be accepted under Contract v1.0.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-02",
                    "supported_proposition": "test completion criteria",
                },
            ],
        },
        {
            "clause_id": "NC-06",
            "statement": "The contract may be reopened only after presentation of a Reproducible Material Counterexample satisfying all five conditions: exact input or fixture, exact execution command, reproducible on frozen commit, incorrect verifier pass, and claim-relevant material effect.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-01",
                    "supported_proposition": "bounded testing scope",
                },
            ],
        },
        {
            "clause_id": "NC-07",
            "statement": "Hypothetical concerns without executable evidence, code-style preferences, naming improvements, formatting changes, speed optimizations, additional defense-in-depth outside frozen claims, edge cases outside declared trust boundary, and defects that cannot affect a paper claim do not reopen G.D6.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-01",
                    "supported_proposition": "bounded testing scope",
                },
            ],
        },
        {
            "clause_id": "NC-08",
            "statement": "The framework is a bounded empirical verification contract, not a formal proof.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-01",
                    "supported_proposition": "terminology for software testing",
                },
            ],
        },
        {
            "clause_id": "NC-09",
            "statement": "Trusted infrastructure components are trusted assumptions, not verified conclusions.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-01",
                    "supported_proposition": "bounded testing scope",
                },
            ],
        },
        {
            "clause_id": "NC-10",
            "statement": "The future frozen verifier path is scripts/verify_gd6_frozen_benchmark_v1.py and the execution pattern is python3 scripts/verify_gd6_frozen_benchmark_v1.py.",
            "basis": [
                {
                    "basis_type": "internal_project_evidence",
                    "source_id": "scripts/audit_part3b_et_policy_implementation.py",
                    "supported_proposition": "existing verifier pattern at scripts/audit_part3b_et_policy_implementation.py",
                },
            ],
        },
        {
            "clause_id": "NC-11",
            "statement": "Final acceptance later requires execution from a clean clone, recorded environment, exit code 0, complete JSON report, complete Markdown report, no production action, and execution by an evaluator other than the implementation author.",
            "basis": [
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-03",
                    "supported_proposition": "documenting research sufficiently for independent verification",
                },
                {
                    "basis_type": "external_methodological_source",
                    "source_id": "MB-04",
                    "supported_proposition": "independent evaluation of computational artifacts",
                },
            ],
        },
    ]
    return clauses


def build_severity_classification() -> Dict[str, Any]:
    return {
        "critical": {
            "description": "A reproducible defect that can alter a paper result, grant unauthorized approval, authorize production, enforce policy, modify protected artifacts, or make the frozen verifier incorrectly pass a mandatory mutation.",
            "effect": "blocks acceptance; reopens accepted G.D6 if discovered later",
        },
        "major": {
            "description": "A reproducible defect that prevents independent execution, invalidates environment provenance, breaks JSON/Markdown consistency, makes required rollback or restoration evidence incomplete, or makes mandatory benchmark evidence unavailable.",
            "effect": "blocks acceptance until corrected",
        },
        "minor": {
            "description": "A defect limited to naming, formatting, refactoring, non-material documentation improvement, performance optimization, or non-claim-relevant cleanup.",
            "effect": "recorded but does not block acceptance",
        },
    }


def build_reopening_rule() -> Dict[str, Any]:
    return {
        "all_required": True,
        "requirements": [
            "exact_input_or_fixture",
            "exact_execution_command",
            "reproducible_on_frozen_commit",
            "incorrect_verifier_pass",
            "claim_relevant_material_effect",
        ],
        "non_reopening": [
            "hypothetical_concerns_without_executable_evidence",
            "code_style_preferences",
            "naming_improvements",
            "formatting_changes",
            "speed_optimizations",
            "additional_defense_in_depth_outside_frozen_claims",
            "edge_cases_outside_declared_trust_boundary",
            "defects_that_cannot_affect_a_paper_claim",
        ],
    }


def build_acceptance_rule() -> Dict[str, Any]:
    return {
        "rule": "G.D6 Accepted = every mandatory contract condition passes.",
        "no_weighted_score": True,
        "no_majority_vote": True,
        "no_partial_acceptance": True,
        "no_discretionary_override": True,
        "no_compensation_between_failed_and_passed_conditions": True,
        "one_failed_mandatory_condition_means_not_accepted": True,
        "contract_does_not_mark_gd6_accepted": True,
    }


def build_stopping_rule() -> Dict[str, Any]:
    return {
        "statement": "After Acceptance Contract v1.0 and Benchmark Manifest v1.0 are independently accepted and frozen, no new G.D6 acceptance criterion may be introduced during the same evaluation cycle.",
        "if_frozen_verifier_passes_all_mandatory_benchmark_items_then_gd6_must_be_accepted": True,
        "do_not_add_further_requirements_merely_because_another_hypothetical_edge_case_can_be_imagined": True,
    }


def build_trust_boundary() -> Dict[str, Any]:
    return {
        "trusted_infrastructure": TRUSTED_INFRASTRUCTURE,
        "trusted_infrastructure_note": "These components are trusted assumptions, not verified conclusions.",
        "in_scope_components": IN_SCOPE_COMPONENTS,
    }


def build_limitations() -> List[str]:
    return [
        "This is a bounded empirical verification contract, not a formal proof.",
        "No claim of formal verification or mathematical proof of total correctness.",
        "No claim of absence of all possible defects.",
        "No ISO, IEEE, ACM, or NIST certification.",
        "No guarantee of Q2 or Q3 journal acceptance.",
        "No security against malicious operating systems.",
        "No verification of Python, Git, SHA-256, CPU, memory, or the operating system.",
        "No completion of Part 3B.",
        "No authorization of Part 3C.",
        "No approval or enforcement of the policy.",
        "No authorization of production execution.",
    ]


def build_evidence_requirements() -> List[Dict[str, Any]]:
    return [
        {"requirement": "all_eight_authorized_files_exist", "mandatory": True},
        {"requirement": "no_existing_tracked_file_changed", "mandatory": True},
        {"requirement": "contract_package_verifier_exits_0", "mandatory": True},
        {"requirement": "contract_json_and_markdown_consistent", "mandatory": True},
        {"requirement": "benchmark_json_and_markdown_consistent", "mandatory": True},
        {"requirement": "exact_benchmark_sets_present", "mandatory": True},
        {"requirement": "every_normative_clause_grounded", "mandatory": True},
        {"requirement": "no_unresolved_required_fact", "mandatory": True},
        {"requirement": "freeze_manifest_hashes_match", "mandatory": True},
        {"requirement": "no_self_referential_hash", "mandatory": True},
        {"requirement": "no_production_action_occurred", "mandatory": True},
        {"requirement": "working_tree_clean_after_commit", "mandatory": True},
    ]


def build_provenance() -> Dict[str, Any]:
    return {
        "starting_commit": STARTING_COMMIT,
        "branch": "major-revision-analysis-v2",
        "repository": "abtinasg/springer",
        "extraction_method": "runtime_output_and_constant_extraction_from_starting_commit",
    }


def build_contract(semantic_test_info: Dict[str, Any], fixture_parity_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "stage": STAGE,
        "contract_id": CONTRACT_ID,
        "version": CONTRACT_VERSION,
        "title": "G.D6 Acceptance Contract",
        "purpose": "Define and freeze the scientific and engineering claims, trusted-computing boundary, acceptance criteria, benchmark cases, stopping rule, reopening rule, and evidence package for G.D6 before any further implementation.",
        "status": "freeze_candidate",
        "freeze_effective_when": "this exact contract package commit is independently accepted",
        "starting_commit": STARTING_COMMIT,
        "scientific_claims": SCIENTIFIC_CLAIMS,
        "trust_boundary": build_trust_boundary(),
        "acceptance_rule": build_acceptance_rule(),
        "stopping_rule": build_stopping_rule(),
        "reopening_rule": build_reopening_rule(),
        "severity_classification": build_severity_classification(),
        "mandatory_benchmark_groups": ["BG-01", "BG-02", "BG-03", "BG-04", "BG-05", "BG-06", "BG-07", "BG-08", "BG-09", "BG-10", "BG-11"],
        "evidence_requirements": build_evidence_requirements(),
        "limitations": build_limitations(),
        "methodological_basis": METHODOLOGICAL_BASIS,
        "prohibited_claims": PROHIBITED_CLAIMS,
        "unresolved_required_facts": [],
        "normative_clauses": build_normative_clauses(),
        "provenance": build_provenance(),
    }


def build_benchmark_items(semantic_test_info: Dict[str, Any], fixture_parity_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    # BG-01: Semantic Policy Tests
    for tid in semantic_test_info["test_ids"]:
        items.append({
            "benchmark_id": f"BG-01-{tid}",
            "category": "BG-01",
            "expected_result": "pass",
            "claim_ids": ["CLAIM-A"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/build_part3b_prediction_ledger.py",
                "source_symbol": f"run_et_reconciliation_policy_self_tests().tests[{tid}]",
                "extraction_method": "runtime_output",
            },
        })

    # BG-02: Historical Fixture Parity
    for i, rec in enumerate(fixture_parity_records):
        items.append({
            "benchmark_id": f"BG-02-{i:03d}-{rec['event_id']}-{rec['model']}-{rec['column']}",
            "category": "BG-02",
            "expected_result": rec["expected_result"],
            "claim_ids": ["CLAIM-A"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "reports/part3b_et_reconciliation_policy.json",
                "source_symbol": f"regression_fixtures[{i}]",
                "extraction_method": "existing_frozen_artifact",
            },
        })

    # BG-03: Write-Guard Matrix
    for mech in WRITE_GUARD_MECHANISMS:
        for tgt in WRITE_GUARD_CONTROL_TARGETS:
            items.append({
                "benchmark_id": f"BG-03-{mech}-{tgt}",
                "category": "BG-03",
                "expected_result": "reject",
                "claim_ids": ["CLAIM-C", "CLAIM-D"],
                "mandatory": True,
                "provenance": {
                    "starting_commit": STARTING_COMMIT,
                    "source_file": "scripts/build_part3b_prediction_ledger.py",
                    "source_symbol": f"_gd6_run_write_guard_positive_controls().controls[mechanism={mech},target={tgt}]",
                    "extraction_method": "runtime_output",
                },
            })

    # BG-04: Production Entry-Point Guards
    for ep in PRODUCTION_ENTRY_POINTS:
        items.append({
            "benchmark_id": f"BG-04-{ep}",
            "category": "BG-04",
            "expected_result": "reject",
            "claim_ids": ["CLAIM-B"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/build_part3b_prediction_ledger.py",
                "source_symbol": f"_GD6_PRODUCTION_ENTRY_POINTS[{ep}]",
                "extraction_method": "constant",
            },
        })

    # BG-05: Restoration Identity Set
    for rk in RESTORATION_KEYS:
        items.append({
            "benchmark_id": f"BG-05-{rk}",
            "category": "BG-05",
            "expected_result": "restore",
            "claim_ids": ["CLAIM-D"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/build_part3b_prediction_ledger.py",
                "source_symbol": f"_GD6_FORCED_EXCEPTION_RESTORATION_KEYS[{rk}]",
                "extraction_method": "constant",
            },
        })

    # BG-06: Forced-Exception Fixture Set
    for fp in FORCED_EXCEPTION_FIXTURE_PATHS:
        items.append({
            "benchmark_id": f"BG-06-{fp}",
            "category": "BG-06",
            "expected_result": "unchanged",
            "claim_ids": ["CLAIM-C", "CLAIM-D"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/build_part3b_prediction_ledger.py",
                "source_symbol": f"_GD6_FORCED_EXCEPTION_FIXTURE_PATHS[{fp}]",
                "extraction_method": "constant",
            },
        })

    # BG-07: Transactional Rollback Scenarios
    for sc in ROLLBACK_SCENARIOS:
        items.append({
            "benchmark_id": f"BG-07-{sc['failure_point']}-{sc['initial_state']}",
            "category": "BG-07",
            "expected_result": "restore",
            "claim_ids": ["CLAIM-D"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/audit_part3b_et_policy_implementation.py",
                "source_symbol": f"run_transactional_rollback_tests().scenario_records[failure_point={sc['failure_point']},initial_state={sc['initial_state']}]",
                "extraction_method": "runtime_output",
            },
        })

    # BG-08: Rollback Mutation Set
    for mut in ROLLBACK_MUTATIONS:
        items.append({
            "benchmark_id": f"BG-08-{mut}",
            "category": "BG-08",
            "expected_result": "reject",
            "claim_ids": ["CLAIM-D"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/audit_part3b_et_policy_implementation.py",
                "source_symbol": f"REQUIRED_ROLLBACK_MUTATIONS[{mut}]",
                "extraction_method": "constant",
            },
        })

    # BG-09: Preservation and Zero-Activity Conditions
    for cond in PRESERVATION_CONDITIONS:
        items.append({
            "benchmark_id": f"BG-09-{cond['condition']}",
            "category": "BG-09",
            "expected_result": "zero",
            "claim_ids": ["CLAIM-B", "CLAIM-C"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/audit_part3b_et_policy_implementation.py",
                "source_symbol": f"run_audit().measured_activity_counters[{cond['condition']}]",
                "extraction_method": "contract_fixed_requirement",
            },
        })

    # BG-10: Report Integrity
    for cond in REPORT_INTEGRITY_CONDITIONS:
        items.append({
            "benchmark_id": f"BG-10-{cond}",
            "category": "BG-10",
            "expected_result": "pass",
            "claim_ids": ["CLAIM-E"],
            "mandatory": True,
            "provenance": {
                "starting_commit": STARTING_COMMIT,
                "source_file": "scripts/audit_part3b_et_policy_implementation.py",
                "source_symbol": f"run_audit().report[{cond}]",
                "extraction_method": "contract_fixed_requirement",
            },
        })

    # BG-11: Independent Clean-Environment Execution
    items.append({
        "benchmark_id": "BG-11-clean-environment-execution",
        "category": "BG-11",
        "expected_result": "pass",
        "claim_ids": ["CLAIM-E"],
        "mandatory": True,
        "provenance": {
            "starting_commit": STARTING_COMMIT,
            "source_file": "scripts/audit_part3b_et_policy_implementation.py",
            "source_symbol": "run_audit() verifier pattern",
            "extraction_method": "contract_fixed_requirement",
        },
    })

    return items


def build_benchmark(semantic_test_info: Dict[str, Any], fixture_parity_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    items = build_benchmark_items(semantic_test_info, fixture_parity_records)

    benchmark_groups = [
        {
            "group_id": "BG-01",
            "title": "Semantic Policy Tests",
            "expected_count": semantic_test_info["test_count"],
            "claim_ids": ["CLAIM-A"],
            "extraction_entry_point": "run_et_reconciliation_policy_self_tests()",
        },
        {
            "group_id": "BG-02",
            "title": "Historical Fixture Parity",
            "expected_count": len(fixture_parity_records),
            "claim_ids": ["CLAIM-A"],
        },
        {
            "group_id": "BG-03",
            "title": "Write-Guard Matrix",
            "expected_count": len(WRITE_GUARD_MECHANISMS) * len(WRITE_GUARD_CONTROL_TARGETS),
            "mechanism_count": len(WRITE_GUARD_MECHANISMS),
            "target_count": len(WRITE_GUARD_CONTROL_TARGETS),
            "claim_ids": ["CLAIM-C", "CLAIM-D"],
        },
        {
            "group_id": "BG-04",
            "title": "Production Entry-Point Guards",
            "expected_count": len(PRODUCTION_ENTRY_POINTS),
            "claim_ids": ["CLAIM-B"],
        },
        {
            "group_id": "BG-05",
            "title": "Restoration Identity Set",
            "expected_count": len(RESTORATION_KEYS),
            "claim_ids": ["CLAIM-D"],
        },
        {
            "group_id": "BG-06",
            "title": "Forced-Exception Fixture Set",
            "expected_count": len(FORCED_EXCEPTION_FIXTURE_PATHS),
            "claim_ids": ["CLAIM-C", "CLAIM-D"],
        },
        {
            "group_id": "BG-07",
            "title": "Transactional Rollback Scenarios",
            "expected_count": len(ROLLBACK_SCENARIOS),
            "claim_ids": ["CLAIM-D"],
        },
        {
            "group_id": "BG-08",
            "title": "Rollback Mutation Set",
            "expected_count": len(ROLLBACK_MUTATIONS),
            "claim_ids": ["CLAIM-D"],
        },
        {
            "group_id": "BG-09",
            "title": "Preservation and Zero-Activity Conditions",
            "expected_count": len(PRESERVATION_CONDITIONS),
            "claim_ids": ["CLAIM-B", "CLAIM-C"],
        },
        {
            "group_id": "BG-10",
            "title": "Report Integrity",
            "expected_count": len(REPORT_INTEGRITY_CONDITIONS),
            "claim_ids": ["CLAIM-E"],
        },
        {
            "group_id": "BG-11",
            "title": "Independent Clean-Environment Execution",
            "expected_count": 1,
            "claim_ids": ["CLAIM-E"],
        },
    ]

    return {
        "stage": STAGE,
        "benchmark_id": BENCHMARK_ID,
        "version": BENCHMARK_VERSION,
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "starting_commit": STARTING_COMMIT,
        "benchmark_groups": benchmark_groups,
        "expected_counts": {
            "BG-01": semantic_test_info["test_count"],
            "BG-02": len(fixture_parity_records),
            "BG-03": len(WRITE_GUARD_MECHANISMS) * len(WRITE_GUARD_CONTROL_TARGETS),
            "BG-04": len(PRODUCTION_ENTRY_POINTS),
            "BG-05": len(RESTORATION_KEYS),
            "BG-06": len(FORCED_EXCEPTION_FIXTURE_PATHS),
            "BG-07": len(ROLLBACK_SCENARIOS),
            "BG-08": len(ROLLBACK_MUTATIONS),
            "BG-09": len(PRESERVATION_CONDITIONS),
            "BG-10": len(REPORT_INTEGRITY_CONDITIONS),
            "BG-11": 1,
        },
        "exact_sets": {
            "write_guard_mechanisms": WRITE_GUARD_MECHANISMS,
            "write_guard_control_targets": WRITE_GUARD_CONTROL_TARGETS,
            "protected_artifact_paths": PROTECTED_ARTIFACT_PATHS,
            "production_entry_points": PRODUCTION_ENTRY_POINTS,
            "restoration_keys": RESTORATION_KEYS,
            "forced_exception_fixture_paths": FORCED_EXCEPTION_FIXTURE_PATHS,
            "rollback_scenarios": ROLLBACK_SCENARIOS,
            "rollback_mutations": ROLLBACK_MUTATIONS,
            "semantic_test_ids": semantic_test_info["test_ids"],
            "preservation_conditions": PRESERVATION_CONDITIONS,
            "report_integrity_conditions": REPORT_INTEGRITY_CONDITIONS,
        },
        "benchmark_items": items,
        "future_verifier_requirement": {
            "verifier_path": "scripts/verify_gd6_frozen_benchmark_v1.py",
            "execution_pattern": "python3 scripts/verify_gd6_frozen_benchmark_v1.py",
            "requirements": [
                "execution_from_clean_clone",
                "recorded_environment",
                "exit_code_0",
                "complete_json_report",
                "complete_markdown_report",
                "no_production_action",
                "execution_by_evaluator_other_than_implementation_author",
            ],
            "note": "At this stage, do not create that future implementation verifier. Record it as a normative future requirement.",
        },
        "acceptance_decision_rule": "G.D6 Accepted = every mandatory benchmark item passes.",
        "reopening_rule_reference": "See gd6_acceptance_contract_v1.json reopening_rule",
        "provenance": {
            "starting_commit": STARTING_COMMIT,
            "extraction_method": "runtime_output_and_constant_extraction_from_starting_commit",
        },
    }


def render_contract_markdown(contract: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# {contract['title']}")
    lines.append("")
    lines.append(f"**Stage:** {contract.get('stage', '')}")
    lines.append(f"**Contract ID:** {contract['contract_id']}")
    lines.append(f"**Version:** {contract['version']}")
    lines.append(f"**Status:** {contract['status']}")
    lines.append(f"**Freeze effective when:** {contract['freeze_effective_when']}")
    lines.append(f"**Starting commit:** `{contract['starting_commit']}`")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(contract["purpose"])
    lines.append("")
    lines.append("## Scientific Claims")
    lines.append("")
    for claim in contract["scientific_claims"]:
        lines.append(f"### {claim['claim_id']} — {claim['title']}")
        lines.append("")
        lines.append(claim["statement"])
        lines.append("")
        if "basis" in claim:
            lines.append("Basis:")
            lines.append("")
            for b in claim["basis"]:
                lines.append(f"- **{b['basis_type']}** — {b['source_id']}: {b['supported_proposition']}")
            lines.append("")
    lines.append("## Trust Boundary")
    lines.append("")
    lines.append("### Trusted Infrastructure")
    lines.append("")
    for item in contract["trust_boundary"]["trusted_infrastructure"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(f"_{contract['trust_boundary']['trusted_infrastructure_note']}_")
    lines.append("")
    lines.append("### In-Scope Components")
    lines.append("")
    for item in contract["trust_boundary"]["in_scope_components"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Acceptance Rule")
    lines.append("")
    ar = contract["acceptance_rule"]
    lines.append(f"**Rule:** {ar['rule']}")
    lines.append("")
    lines.append(f"- No weighted score: {ar['no_weighted_score']}")
    lines.append(f"- No majority vote: {ar['no_majority_vote']}")
    lines.append(f"- No partial acceptance: {ar['no_partial_acceptance']}")
    lines.append(f"- No discretionary override: {ar['no_discretionary_override']}")
    lines.append(f"- No compensation: {ar['no_compensation_between_failed_and_passed_conditions']}")
    lines.append(f"- One failed mandatory condition means not accepted: {ar['one_failed_mandatory_condition_means_not_accepted']}")
    lines.append(f"- Contract does not mark G.D6 accepted: {ar['contract_does_not_mark_gd6_accepted']}")
    lines.append("")
    lines.append("## Stopping Rule")
    lines.append("")
    sr = contract["stopping_rule"]
    lines.append(sr["statement"])
    lines.append("")
    lines.append("## Reopening Rule")
    lines.append("")
    rr = contract["reopening_rule"]
    lines.append(f"All required: {rr['all_required']}")
    lines.append("")
    lines.append("Requirements:")
    lines.append("")
    for req in rr["requirements"]:
        lines.append(f"- {req}")
    lines.append("")
    lines.append("Non-reopening:")
    lines.append("")
    for nr in rr["non_reopening"]:
        lines.append(f"- {nr}")
    lines.append("")
    lines.append("## Severity Classification")
    lines.append("")
    sc = contract["severity_classification"]
    for level in ["critical", "major", "minor"]:
        lines.append(f"### {level.title()}")
        lines.append("")
        lines.append(f"**Description:** {sc[level]['description']}")
        lines.append(f"**Effect:** {sc[level]['effect']}")
        lines.append("")
    lines.append("## Mandatory Benchmark Groups")
    lines.append("")
    for bg in contract["mandatory_benchmark_groups"]:
        lines.append(f"- {bg}")
    lines.append("")
    lines.append("## Evidence Requirements")
    lines.append("")
    for er in contract["evidence_requirements"]:
        lines.append(f"- **{er['requirement']}** (mandatory: {er['mandatory']})")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    for lim in contract["limitations"]:
        lines.append(f"- {lim}")
    lines.append("")
    lines.append("## Methodological Basis")
    lines.append("")
    for mb in contract["methodological_basis"]:
        lines.append(f"### {mb['source_id']}")
        lines.append("")
        lines.append(f"**Title:** {mb['title']}")
        lines.append(f"**Issuer:** {mb['issuer']}")
        lines.append(f"**Version/Year:** {mb['version_or_year']}")
        lines.append(f"**Authority type:** {mb['authority_type']}")
        lines.append("")
        lines.append("Supported use:")
        lines.append("")
        for su in mb["supported_use"]:
            lines.append(f"- {su}")
        lines.append("")
        if mb["unsupported_claims"]:
            lines.append("Unsupported claims:")
            lines.append("")
            for uc in mb["unsupported_claims"]:
                lines.append(f"- {uc}")
            lines.append("")
    lines.append("## Prohibited Claims")
    lines.append("")
    for pc in contract["prohibited_claims"]:
        lines.append(f"- {pc}")
    lines.append("")
    lines.append("## Normative Clauses")
    lines.append("")
    for nc in contract["normative_clauses"]:
        lines.append(f"### {nc['clause_id']}")
        lines.append("")
        lines.append(nc["statement"])
        lines.append("")
        lines.append("Basis:")
        lines.append("")
        for b in nc["basis"]:
            lines.append(f"- **{b['basis_type']}** — {b['source_id']}: {b['supported_proposition']}")
        lines.append("")
    lines.append("## Provenance")
    lines.append("")
    pv = contract["provenance"]
    lines.append(f"- Starting commit: `{pv['starting_commit']}`")
    lines.append(f"- Branch: {pv['branch']}")
    lines.append(f"- Repository: {pv['repository']}")
    lines.append(f"- Extraction method: {pv['extraction_method']}")
    lines.append("")
    return "\n".join(lines)


def render_benchmark_markdown(benchmark: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# G.D6 Benchmark Manifest")
    lines.append("")
    lines.append(f"**Stage:** {benchmark.get('stage', '')}")
    lines.append(f"**Benchmark ID:** {benchmark['benchmark_id']}")
    lines.append(f"**Version:** {benchmark['version']}")
    lines.append(f"**Contract ID:** {benchmark['contract_id']}")
    lines.append(f"**Contract version:** {benchmark['contract_version']}")
    lines.append(f"**Starting commit:** `{benchmark['starting_commit']}`")
    lines.append("")
    lines.append("## Benchmark Groups")
    lines.append("")
    lines.append("| Group | Title | Expected Count | Claim IDs |")
    lines.append("|-------|-------|----------------|-----------|")
    for bg in benchmark["benchmark_groups"]:
        lines.append(f"| {bg['group_id']} | {bg['title']} | {bg['expected_count']} | {', '.join(bg['claim_ids'])} |")
    lines.append("")
    lines.append("## Expected Counts")
    lines.append("")
    for k, v in benchmark["expected_counts"].items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Exact Sets")
    lines.append("")
    es = benchmark["exact_sets"]
    lines.append(f"### Write-Guard Mechanisms ({len(es['write_guard_mechanisms'])})")
    lines.append("")
    for m in es["write_guard_mechanisms"]:
        lines.append(f"- {m}")
    lines.append("")
    lines.append(f"### Production Entry Points ({len(es['production_entry_points'])})")
    lines.append("")
    for ep in es["production_entry_points"]:
        lines.append(f"- {ep}")
    lines.append("")
    lines.append(f"### Restoration Keys ({len(es['restoration_keys'])})")
    lines.append("")
    for rk in es["restoration_keys"]:
        lines.append(f"- {rk}")
    lines.append("")
    lines.append(f"### Forced-Exception Fixture Paths ({len(es['forced_exception_fixture_paths'])})")
    lines.append("")
    for fp in es["forced_exception_fixture_paths"]:
        lines.append(f"- {fp}")
    lines.append("")
    lines.append(f"### Rollback Scenarios ({len(es['rollback_scenarios'])})")
    lines.append("")
    for sc in es["rollback_scenarios"]:
        lines.append(f"- {sc['failure_point']} / {sc['initial_state']}")
    lines.append("")
    lines.append(f"### Rollback Mutations ({len(es['rollback_mutations'])})")
    lines.append("")
    for mut in es["rollback_mutations"]:
        lines.append(f"- {mut}")
    lines.append("")
    lines.append(f"### Semantic Test IDs ({len(es['semantic_test_ids'])})")
    lines.append("")
    for tid in es["semantic_test_ids"]:
        lines.append(f"- {tid}")
    lines.append("")
    lines.append(f"### Write-Guard Control Targets ({len(es['write_guard_control_targets'])})")
    lines.append("")
    for tp in es["write_guard_control_targets"]:
        lines.append(f"- {tp}")
    lines.append("")
    lines.append(f"### Protected Artifact Paths ({len(es['protected_artifact_paths'])})")
    lines.append("")
    for tp in es["protected_artifact_paths"]:
        lines.append(f"- {tp}")
    lines.append("")
    lines.append(f"### Preservation Conditions ({len(es['preservation_conditions'])})")
    lines.append("")
    for pc in es["preservation_conditions"]:
        lines.append(f"- {pc['condition']} = {pc['expected']}")
    lines.append("")
    lines.append(f"### Report Integrity Conditions ({len(es['report_integrity_conditions'])})")
    lines.append("")
    for ric in es["report_integrity_conditions"]:
        lines.append(f"- {ric}")
    lines.append("")
    lines.append("## Future Verifier Requirement")
    lines.append("")
    fv = benchmark["future_verifier_requirement"]
    lines.append(f"**Verifier path:** `{fv['verifier_path']}`")
    lines.append(f"**Execution pattern:** `{fv['execution_pattern']}`")
    lines.append("")
    lines.append("Requirements:")
    lines.append("")
    for req in fv["requirements"]:
        lines.append(f"- {req}")
    lines.append("")
    lines.append(f"_{fv['note']}_")
    lines.append("")
    lines.append("## Acceptance Decision Rule")
    lines.append("")
    lines.append(benchmark["acceptance_decision_rule"])
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    pv = benchmark["provenance"]
    lines.append(f"- Starting commit: `{pv['starting_commit']}`")
    lines.append(f"- Extraction method: {pv['extraction_method']}")
    lines.append("")
    return "\n".join(lines)


def build_freeze_manifest(root: Path) -> Dict[str, Any]:
    files: Dict[str, str] = {}
    for rel in AUTHORIZED_FILES:
        if rel == FREEZE_MANIFEST_PATH:
            continue
        p = root / rel
        if p.is_file():
            files[rel] = sha256_file(p)
    return {
        "manifest_id": FREEZE_MANIFEST_ID,
        "version": FREEZE_MANIFEST_VERSION,
        "starting_commit": STARTING_COMMIT,
        "hash_algorithm": "SHA-256",
        "files": files,
        "self_hash_included": False,
    }


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build G.D6 acceptance contract and benchmark v1.0"
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Alternative output root directory. Defaults to repository root.",
    )
    args = parser.parse_args(argv)

    root = Path(args.output_root) if args.output_root else repo_root()

    print("Extracting semantic test IDs from worktree...")
    semantic_test_info = extract_semantic_test_ids_from_worktree()
    print(f"  Test count: {semantic_test_info['test_count']}")
    print(f"  Tests expected: {semantic_test_info['tests_expected']}")

    print("Extracting fixture parity records from worktree...")
    fixture_parity_records = extract_fixture_parity_records_from_worktree()
    print(f"  Fixture parity count: {len(fixture_parity_records)}")

    print("Extracting write-guard controls from worktree...")
    wg_info = extract_write_guard_controls_from_worktree()
    print(f"  Mechanism count: {len(wg_info['mechanisms'])}")
    print(f"  Target count: {len(wg_info['targets'])}")
    print(f"  Control count: {wg_info['control_count']}")
    print(f"  Unique pair count: {wg_info['unique_pair_count']}")

    print("Extracting production entry points from worktree...")
    prod_eps = extract_production_entry_points_from_worktree()
    print(f"  Entry point count: {len(prod_eps)}")

    print("Extracting restoration keys from worktree...")
    rest_keys = extract_restoration_keys_from_worktree()
    print(f"  Restoration key count: {len(rest_keys)}")

    print("Extracting forced-exception fixture paths from worktree...")
    fe_paths = extract_forced_exception_fixture_paths_from_worktree()
    print(f"  Fixture path count: {len(fe_paths)}")

    print("Extracting rollback scenarios from worktree...")
    rb_scenarios = extract_rollback_scenarios_from_worktree()
    print(f"  Scenario count: {len(rb_scenarios)}")

    print("Extracting rollback mutations from worktree...")
    rb_mutations = extract_rollback_mutations_from_worktree()
    print(f"  Mutation count: {len(rb_mutations)}")

    print("Extracting protected artifact paths from worktree...")
    pa_paths = extract_protected_artifact_paths_from_worktree()
    print(f"  Protected artifact count: {len(pa_paths)}")

    print("Building reference environment...")
    env = build_reference_environment()

    print("Building contract...")
    contract = build_contract(semantic_test_info, fixture_parity_records)

    print("Building benchmark...")
    benchmark = build_benchmark(semantic_test_info, fixture_parity_records)

    print("Rendering Markdown...")
    contract_md = render_contract_markdown(contract)
    benchmark_md = render_benchmark_markdown(benchmark)

    print("Writing files...")
    (root / CONTRACT_JSON_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / CONTRACT_MD_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / BENCHMARK_JSON_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / BENCHMARK_MD_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / ENV_JSON_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / FREEZE_MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)

    (root / CONTRACT_JSON_PATH).write_text(deterministic_json(contract), encoding="utf-8")
    (root / CONTRACT_MD_PATH).write_text(contract_md, encoding="utf-8")
    (root / BENCHMARK_JSON_PATH).write_text(deterministic_json(benchmark), encoding="utf-8")
    (root / BENCHMARK_MD_PATH).write_text(benchmark_md, encoding="utf-8")
    (root / ENV_JSON_PATH).write_text(deterministic_json(env), encoding="utf-8")

    print("Building freeze manifest...")
    freeze_manifest = build_freeze_manifest(root)
    (root / FREEZE_MANIFEST_PATH).write_text(deterministic_json(freeze_manifest), encoding="utf-8")

    print("Done.")
    print(f"  Contract JSON: {CONTRACT_JSON_PATH}")
    print(f"  Contract MD: {CONTRACT_MD_PATH}")
    print(f"  Benchmark JSON: {BENCHMARK_JSON_PATH}")
    print(f"  Benchmark MD: {BENCHMARK_MD_PATH}")
    print(f"  Environment JSON: {ENV_JSON_PATH}")
    print(f"  Freeze manifest: {FREEZE_MANIFEST_PATH}")


if __name__ == "__main__":
    main()
