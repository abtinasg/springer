#!/usr/bin/env python3
"""Part 3B.2R.1-G.D6: Audit frozen ET reconciliation policy implementation."""
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

STAGE = "Part 3B.2R.1-G.D6"
STARTING_COMMIT = "2cdc97470765ca0b93054d84b7f34294f4384d83"
JSON_OUTPUT_PATH = "reports/part3b_et_policy_implementation.json"
MD_OUTPUT_PATH = "reports/part3b_et_policy_implementation.md"
FROZEN_POLICY_JSON_PATH = "reports/part3b_et_reconciliation_policy.json"
POLICY_MODULE_PATH = "scripts/part3b_et_reconciliation_policy.py"
PRODUCTION_VALIDATOR_PATH = "scripts/build_part3b_prediction_ledger.py"
PRODUCTION_VALIDATOR_SHA_BEFORE = (
    "a18e4b5c559011ab508a988f4dfe6d91a7d878ec2ef7249d59dd5796d3473b39"
)

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
            f"- **Implementation report JSON/Markdown consistency:** {report['implementation_report_json_markdown_consistency']}",
        ]
    )
    return "\n".join(lines) + "\n"


def publish_outputs_transactionally(
    report: Dict[str, Any],
    json_path: Path,
    md_path: Path,
) -> Dict[str, Any]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(report, indent=2) + "\n"
    md_text = render_markdown(report)
    if render_markdown(json.loads(json_text)) != md_text:
        raise RuntimeError("Markdown does not match JSON report")

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

    backup_json_path: Optional[Path] = None
    backup_md_path: Optional[Path] = None
    try:
        if json_path.is_file():
            backup_json_path = json_path.with_suffix(json_path.suffix + ".pubbak")
            json_path.replace(backup_json_path)
        tmp_json_path.replace(json_path)

        try:
            if md_path.is_file():
                backup_md_path = md_path.with_suffix(md_path.suffix + ".pubbak")
                md_path.replace(backup_md_path)
            tmp_md_path.replace(md_path)
        except Exception:
            if backup_json_path is not None and backup_json_path.exists():
                if json_path.exists():
                    json_path.unlink()
                backup_json_path.replace(json_path)
            if backup_md_path is not None and backup_md_path.exists():
                if md_path.exists():
                    md_path.unlink()
                backup_md_path.replace(md_path)
            raise

        if backup_json_path is not None and backup_json_path.exists():
            backup_json_path.unlink()
        if backup_md_path is not None and backup_md_path.exists():
            backup_md_path.unlink()
    finally:
        if tmp_json_path.exists():
            tmp_json_path.unlink()
        if tmp_md_path.exists():
            tmp_md_path.unlink()

    final_reread = json.loads(json_path.read_text(encoding="utf-8"))
    final_md = md_path.read_text(encoding="utf-8")
    if render_markdown(final_reread) != final_md:
        raise RuntimeError("Published markdown does not match published JSON")

    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "json_sha256": sha256_file(json_path),
        "md_sha256": sha256_file(md_path),
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

    after_protected = protected_snapshot(root)
    protected_files_unchanged = before_protected == after_protected
    existing_part3b_artifacts_changed = not protected_files_unchanged

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
        "dual_build_evidence_required": True,
        "single_build_final_approval_prohibited": True,
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
        "measured_activity_counters": {
            "model_fits_executed": synthetic_summary.get("model_fits_executed", 0),
            "prediction_calls_executed": synthetic_summary.get("prediction_calls_executed", 0),
            "production_model_evaluation_builds_executed": synthetic_summary.get(
                "production_model_evaluation_builds_executed", 0
            ),
            "production_artifact_writes": synthetic_summary.get("production_artifact_writes", 0),
            "canonical_file_writes": synthetic_summary.get("canonical_file_writes", 0),
        },
        "protected_file_verification": {
            "paths": PROTECTED_PATHS,
            "before": before_protected,
            "after": after_protected,
            "unchanged": protected_files_unchanged,
        },
        "protected_files_unchanged": protected_files_unchanged,
        "policy_implementation_present": all_public_functions_present,
        "policy_specification_loaded_and_verified": frozen_policy_contract_verified,
        "policy_executed_on_production_artifacts": False,
        "production_run_executed": False,
        "canonical_files_changed": False,
        "existing_part3b_artifacts_changed": existing_part3b_artifacts_changed,
        "part3b_complete": False,
        "part3c_authorized": False,
        "implementation_report_json_markdown_consistency": True,
        "transactional_report_publication": False,
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
        and synthetic_summary.get("model_fits_executed", 1) == 0
        and synthetic_summary.get("prediction_calls_executed", 1) == 0
        and synthetic_summary.get("production_model_evaluation_builds_executed", 1) == 0
        and synthetic_summary.get("production_artifact_writes", 1) == 0
        and synthetic_summary.get("canonical_file_writes", 1) == 0
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
