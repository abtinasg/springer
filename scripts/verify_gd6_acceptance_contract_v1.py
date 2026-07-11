#!/usr/bin/env python3
"""Part 3B.2R.1-G.D6-F0.1: Verify frozen acceptance contract package v1.0."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set

STARTING_COMMIT = "7dbc206037250b1181aed94bfa7326d79df814fd"
CONTRACT_ID = "SEMIT-GD6-ACCEPTANCE-CONTRACT"
CONTRACT_VERSION = "1.0"
BENCHMARK_ID = "SEMIT-GD6-BENCHMARK"
BENCHMARK_VERSION = "1.0"
FREEZE_MANIFEST_ID = "SEMIT-GD6-CONTRACT-FREEZE-MANIFEST"
FREEZE_MANIFEST_VERSION = "1.0"

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

FREEZE_MANIFEST_TARGETS = [f for f in AUTHORIZED_FILES if f != FREEZE_MANIFEST_PATH]

EXPECTED_CLAIM_IDS = ["CLAIM-A", "CLAIM-B", "CLAIM-C", "CLAIM-D", "CLAIM-E"]

EXPECTED_TRUSTED_INFRASTRUCTURE = [
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

EXPECTED_BENCHMARK_GROUP_IDS = [f"BG-{i:02d}" for i in range(1, 12)]

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

EXPECTED_WRITE_GUARD_TARGET_PATHS = [
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

EXPECTED_PRODUCTION_ENTRY_POINTS = [
    "build_core_bundle",
    "fit_event_candidates",
    "build_prediction_rows",
    "execute_postbuild_integration",
]

EXPECTED_RESTORATION_KEYS = [
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

EXPECTED_FORCED_EXCEPTION_FIXTURE_PATHS = [
    "reports/part3b_et_policy_implementation.json",
    "results/part1_full_reproduction/canonical.csv",
    "results/part3b_prediction_ledger/ledger.csv",
]

EXPECTED_ROLLBACK_SCENARIOS = [
    {"failure_point": "before_any_replacement", "initial_state": "neither_exist"},
    {"failure_point": "before_any_replacement", "initial_state": "both_exist"},
    {"failure_point": "after_json_before_md", "initial_state": "neither_exist"},
    {"failure_point": "after_json_before_md", "initial_state": "both_exist"},
    {"failure_point": "after_md_backup_before_md_replace", "initial_state": "neither_exist"},
    {"failure_point": "after_md_backup_before_md_replace", "initial_state": "both_exist"},
]

EXPECTED_ROLLBACK_MUTATIONS = [
    "extensionless_temp_leftover",
    "pubbak_leftover",
    "unexpected_extra_file",
    "modified_original_json",
    "modified_original_markdown",
    "deleted_original_file",
    "path_type_change",
]

EXPECTED_PRESERVATION_CONDITIONS = [
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

EXPECTED_REPORT_INTEGRITY_CONDITIONS = [
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

VALID_CATEGORIES = set(EXPECTED_BENCHMARK_GROUP_IDS)
VALID_EXPECTED_RESULTS = {"pass", "reject", "restore", "unchanged", "zero"}
VALID_EXTRACTION_METHODS = {
    "runtime_output",
    "constant",
    "existing_frozen_artifact",
    "contract_fixed_requirement",
}

PROTECTED_PATHS = EXPECTED_WRITE_GUARD_TARGET_PATHS


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_file_exists_at_commit(root: Path, commit: str, rel_path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{rel_path}"],
        capture_output=True,
        cwd=str(root),
    )
    return result.returncode == 0


class VerificationResult:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks: List[Dict[str, Any]] = []

    def check(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            self.errors.append(f"{name}: {detail}")

    def warn(self, name: str, detail: str) -> None:
        self.warnings.append(f"{name}: {detail}")

    @property
    def all_passed(self) -> bool:
        return len(self.errors) == 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "all_passed": self.all_passed,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": self.checks,
        }


# ---------------------------------------------------------------------------
# 1. File existence
# ---------------------------------------------------------------------------

def verify_all_authorized_files_exist(root: Path, vr: VerificationResult) -> None:
    for rel in AUTHORIZED_FILES:
        p = root / rel
        vr.check(f"file_exists:{rel}", p.is_file(), str(p))


# ---------------------------------------------------------------------------
# 2. Git-scope verification
# ---------------------------------------------------------------------------

def verify_git_scope(root: Path, vr: VerificationResult) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{STARTING_COMMIT}...HEAD"],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    if result.returncode != 0:
        vr.check("git_diff_name_status", False, result.stderr.strip())
        return
    lines = [l for l in result.stdout.strip().split("\n") if l]
    added_files: List[str] = []
    modified_files: List[str] = []
    for line in lines:
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        if status.startswith("A"):
            added_files.append(path)
        elif status.startswith("M"):
            modified_files.append(path)
        elif status.startswith("D"):
            modified_files.append(path)
        elif status.startswith("R"):
            modified_files.append(path)
        else:
            modified_files.append(path)

    added_set = set(added_files)
    authorized_set = set(AUTHORIZED_FILES)
    vr.check(
        "git_scope_only_authorized_added",
        added_set == authorized_set,
        f"added={sorted(added_set)}, expected={sorted(authorized_set)}",
    )
    vr.check(
        "git_scope_no_existing_modified",
        len(modified_files) == 0,
        f"modified={modified_files}",
    )

    result2 = subprocess.run(
        ["git", "diff", "--name-only", f"{STARTING_COMMIT}...HEAD", "--"] + PROTECTED_PATHS,
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    protected_changed = [l for l in result2.stdout.strip().split("\n") if l]
    vr.check(
        "git_scope_protected_paths_unchanged",
        len(protected_changed) == 0,
        f"changed={protected_changed}",
    )


# ---------------------------------------------------------------------------
# 3. JSON parses
# ---------------------------------------------------------------------------

def verify_json_parses(root: Path, vr: VerificationResult) -> None:
    for rel in [CONTRACT_JSON_PATH, BENCHMARK_JSON_PATH, ENV_JSON_PATH, FREEZE_MANIFEST_PATH]:
        p = root / rel
        try:
            load_json(p)
            vr.check(f"json_parses:{rel}", True, "")
        except Exception as exc:
            vr.check(f"json_parses:{rel}", False, str(exc))


# ---------------------------------------------------------------------------
# 4. Contract JSON verification
# ---------------------------------------------------------------------------

def verify_contract_json(root: Path, vr: VerificationResult) -> Dict[str, Any]:
    p = root / CONTRACT_JSON_PATH
    contract = load_json(p)

    vr.check("contract_id", contract.get("contract_id") == CONTRACT_ID, str(contract.get("contract_id")))
    vr.check("contract_version", contract.get("version") == CONTRACT_VERSION, str(contract.get("version")))
    vr.check("contract_starting_commit", contract.get("starting_commit") == STARTING_COMMIT, str(contract.get("starting_commit")))
    vr.check("contract_status", contract.get("status") == "freeze_candidate", str(contract.get("status")))

    claims = contract.get("scientific_claims", [])
    vr.check("exactly_five_claims", len(claims) == 5, f"found {len(claims)}")
    claim_ids = [c.get("claim_id") for c in claims]
    vr.check("claim_ids_exact", claim_ids == EXPECTED_CLAIM_IDS, str(claim_ids))

    for claim in claims:
        cid = claim.get("claim_id", "")
        basis = claim.get("basis", [])
        vr.check(f"claim_{cid}_has_basis", len(basis) > 0, f"basis count={len(basis)}")
        for b in basis:
            sid = b.get("source_id", "")
            btype = b.get("basis_type", "")
            if btype == "external_methodological_source":
                mb_ids = {m.get("source_id") for m in contract.get("methodological_basis", [])}
                vr.check(f"claim_{cid}_basis_{sid}_resolves", sid in mb_ids, f"source_id={sid} not in methodological_basis")
            elif btype == "internal_project_evidence":
                exists = git_file_exists_at_commit(root, STARTING_COMMIT, sid)
                vr.check(f"claim_{cid}_basis_{sid}_exists_at_starting_commit", exists, f"path={sid}")

    tb = contract.get("trust_boundary", {})
    ti = tb.get("trusted_infrastructure", [])
    vr.check("trusted_infrastructure_exact", ti == EXPECTED_TRUSTED_INFRASTRUCTURE, str(ti))

    mb = contract.get("methodological_basis", [])
    mb_ids = [m.get("source_id") for m in mb]
    vr.check("methodological_basis_ids_exact", mb_ids == ["MB-01", "MB-02", "MB-03", "MB-04", "MB-05"], str(mb_ids))

    nc = contract.get("normative_clauses", [])
    vr.check("normative_clauses_count", len(nc) == 11, f"found {len(nc)}")
    for clause in nc:
        basis = clause.get("basis", [])
        vr.check(
            f"normative_clause_{clause.get('clause_id')}_has_basis",
            len(basis) > 0,
            f"basis count: {len(basis)}",
        )
        for b in basis:
            sid = b.get("source_id", "")
            btype = b.get("basis_type", "")
            if btype == "external_methodological_source":
                vr.check(
                    f"clause_{clause['clause_id']}_external_source_in_mb",
                    sid in {m.get("source_id") for m in mb},
                    f"source_id={sid} not in methodological_basis",
                )
            elif btype == "internal_project_evidence":
                exists = git_file_exists_at_commit(root, STARTING_COMMIT, sid)
                vr.check(
                    f"clause_{clause['clause_id']}_internal_source_exists_at_starting_commit",
                    exists,
                    f"path={sid} does not exist at {STARTING_COMMIT}",
                )

    urf = contract.get("unresolved_required_facts", [])
    vr.check("no_unresolved_required_facts", len(urf) == 0, str(urf))

    vr.check("mandatory_benchmark_groups_exact", contract.get("mandatory_benchmark_groups") == EXPECTED_BENCHMARK_GROUP_IDS, str(contract.get("mandatory_benchmark_groups")))

    return contract


# ---------------------------------------------------------------------------
# 5. Benchmark JSON verification
# ---------------------------------------------------------------------------

def verify_benchmark_json(root: Path, vr: VerificationResult) -> Dict[str, Any]:
    p = root / BENCHMARK_JSON_PATH
    benchmark = load_json(p)

    vr.check("benchmark_id", benchmark.get("benchmark_id") == BENCHMARK_ID, str(benchmark.get("benchmark_id")))
    vr.check("benchmark_version", benchmark.get("version") == BENCHMARK_VERSION, str(benchmark.get("version")))
    vr.check("benchmark_contract_id", benchmark.get("contract_id") == CONTRACT_ID, str(benchmark.get("contract_id")))
    vr.check("benchmark_contract_version", benchmark.get("contract_version") == CONTRACT_VERSION, str(benchmark.get("contract_version")))
    vr.check("benchmark_starting_commit", benchmark.get("starting_commit") == STARTING_COMMIT, str(benchmark.get("starting_commit")))

    groups = benchmark.get("benchmark_groups", [])
    group_ids = [g.get("group_id") for g in groups]
    vr.check("benchmark_group_ids_exact", group_ids == EXPECTED_BENCHMARK_GROUP_IDS, str(group_ids))

    es = benchmark.get("exact_sets", {})
    vr.check("exact_sets_write_guard_mechanisms", es.get("write_guard_mechanisms") == EXPECTED_WRITE_GUARD_MECHANISMS, "")
    vr.check("exact_sets_write_guard_target_paths", es.get("write_guard_target_paths") == EXPECTED_WRITE_GUARD_TARGET_PATHS, "")
    vr.check("exact_sets_production_entry_points", es.get("production_entry_points") == EXPECTED_PRODUCTION_ENTRY_POINTS, "")
    vr.check("exact_sets_restoration_keys", es.get("restoration_keys") == EXPECTED_RESTORATION_KEYS, "")
    vr.check("exact_sets_forced_exception_fixture_paths", es.get("forced_exception_fixture_paths") == EXPECTED_FORCED_EXCEPTION_FIXTURE_PATHS, "")
    vr.check("exact_sets_rollback_scenarios", es.get("rollback_scenarios") == EXPECTED_ROLLBACK_SCENARIOS, "")
    vr.check("exact_sets_rollback_mutations", es.get("rollback_mutations") == EXPECTED_ROLLBACK_MUTATIONS, "")
    vr.check("exact_sets_preservation_conditions", es.get("preservation_conditions") == EXPECTED_PRESERVATION_CONDITIONS, "")
    vr.check("exact_sets_report_integrity_conditions", es.get("report_integrity_conditions") == EXPECTED_REPORT_INTEGRITY_CONDITIONS, "")

    items = benchmark.get("benchmark_items", [])
    vr.check("benchmark_items_present", len(items) > 0, f"found {len(items)}")

    seen_ids: Set[str] = set()
    for item in items:
        bid = item.get("benchmark_id", "")
        vr.check(f"item_{bid}_id_nonempty", bool(bid), "")
        vr.check(f"item_{bid}_id_unique", bid not in seen_ids, f"duplicate: {bid}")
        seen_ids.add(bid)
        vr.check(f"item_{bid}_category_valid", item.get("category") in VALID_CATEGORIES, str(item.get("category")))
        vr.check(f"item_{bid}_expected_result_valid", item.get("expected_result") in VALID_EXPECTED_RESULTS, str(item.get("expected_result")))
        vr.check(f"item_{bid}_mandatory_true", item.get("mandatory") is True, str(item.get("mandatory")))
        claim_ids = item.get("claim_ids", [])
        vr.check(f"item_{bid}_claim_ids_nonempty", len(claim_ids) > 0, str(claim_ids))
        for cid in claim_ids:
            vr.check(f"item_{bid}_claim_{cid}_valid", cid in EXPECTED_CLAIM_IDS, f"unknown claim_id={cid}")

        prov = item.get("provenance", {})
        vr.check(f"item_{bid}_provenance_starting_commit", prov.get("starting_commit") == STARTING_COMMIT, str(prov.get("starting_commit")))
        src_file = prov.get("source_file", "")
        vr.check(f"item_{bid}_provenance_source_file_nonempty", bool(src_file), "")
        src_exists = git_file_exists_at_commit(root, STARTING_COMMIT, src_file)
        vr.check(f"item_{bid}_provenance_source_file_exists_at_starting_commit", src_exists, f"file={src_file}")
        vr.check(f"item_{bid}_provenance_extraction_method_valid", prov.get("extraction_method") in VALID_EXTRACTION_METHODS, str(prov.get("extraction_method")))
        src_sym = prov.get("source_symbol", "")
        vr.check(f"item_{bid}_provenance_source_symbol_nonempty", bool(src_sym), "")

    return benchmark


# ---------------------------------------------------------------------------
# 6. Contract and benchmark cross-references
# ---------------------------------------------------------------------------

def verify_cross_references(root: Path, contract: Dict[str, Any], benchmark: Dict[str, Any], vr: VerificationResult) -> None:
    vr.check("xref_contract_id", contract.get("contract_id") == benchmark.get("contract_id"), f"{contract.get('contract_id')} vs {benchmark.get('contract_id')}")
    vr.check("xref_contract_version", contract.get("version") == benchmark.get("contract_version"), f"{contract.get('version')} vs {benchmark.get('contract_version')}")
    vr.check("xref_contract_starting_commit", contract.get("starting_commit") == benchmark.get("starting_commit"), "")
    vr.check("xref_contract_starting_commit_value", contract.get("starting_commit") == STARTING_COMMIT, str(contract.get("starting_commit")))

    manifest = load_json(root / FREEZE_MANIFEST_PATH)
    vr.check("xref_manifest_starting_commit", manifest.get("starting_commit") == STARTING_COMMIT, str(manifest.get("starting_commit")))
    vr.check("xref_manifest_id", manifest.get("manifest_id") == FREEZE_MANIFEST_ID, str(manifest.get("manifest_id")))
    vr.check("xref_manifest_version", manifest.get("version") == FREEZE_MANIFEST_VERSION, str(manifest.get("version")))

    for item in benchmark.get("benchmark_items", []):
        prov = item.get("provenance", {})
        vr.check(
            f"xref_item_{item['benchmark_id']}_provenance_commit",
            prov.get("starting_commit") == STARTING_COMMIT,
            str(prov.get("starting_commit")),
        )


# ---------------------------------------------------------------------------
# 7. Deterministic regeneration
# ---------------------------------------------------------------------------

def verify_deterministic_regeneration(root: Path, vr: VerificationResult) -> None:
    builder_path = root / "scripts/build_gd6_acceptance_contract_v1.py"
    spec = importlib.util.spec_from_file_location("build_gd6_acceptance_contract_v1", str(builder_path))
    if spec is None or spec.loader is None:
        vr.check("regeneration_load_builder", False, "cannot load builder module")
        return
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    with tempfile.TemporaryDirectory(prefix="gd6_verify_") as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(root / "scripts/build_gd6_acceptance_contract_v1.py"), str(tmp_root / "scripts/build_gd6_acceptance_contract_v1.py"))
        shutil.copy2(str(root / "scripts/verify_gd6_acceptance_contract_v1.py"), str(tmp_root / "scripts/verify_gd6_acceptance_contract_v1.py"))
        try:
            builder.main(["--output-root", str(tmp_root)])
        except Exception as exc:
            vr.check("regeneration_builder_run", False, str(exc))
            return
        vr.check("regeneration_builder_run", True, "")

        targets = [
            (CONTRACT_JSON_PATH, "contract_json"),
            (CONTRACT_MD_PATH, "contract_md"),
            (BENCHMARK_JSON_PATH, "benchmark_json"),
            (BENCHMARK_MD_PATH, "benchmark_md"),
            (ENV_JSON_PATH, "env_json"),
            (FREEZE_MANIFEST_PATH, "freeze_manifest"),
        ]
        for rel, label in targets:
            tracked_p = root / rel
            regen_p = tmp_root / rel
            if not tracked_p.is_file() or not regen_p.is_file():
                vr.check(f"regeneration_{label}_exists", False, f"tracked={tracked_p.is_file()}, regen={regen_p.is_file()}")
                continue
            tracked_bytes = tracked_p.read_bytes()
            regen_bytes = regen_p.read_bytes()
            vr.check(
                f"regeneration_{label}_byte_equal",
                tracked_bytes == regen_bytes,
                f"tracked_sha={hashlib.sha256(tracked_bytes).hexdigest()}, regen_sha={hashlib.sha256(regen_bytes).hexdigest()}",
            )


# ---------------------------------------------------------------------------
# 8. JSON/Markdown consistency
# ---------------------------------------------------------------------------

def verify_json_md_consistency(root: Path, vr: VerificationResult) -> None:
    builder_path = root / "scripts/build_gd6_acceptance_contract_v1.py"
    spec = importlib.util.spec_from_file_location("build_gd6_acceptance_contract_v1_consistency", str(builder_path))
    if spec is None or spec.loader is None:
        vr.check("md_consistency_load_builder", False, "cannot load builder module")
        return
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    contract = load_json(root / CONTRACT_JSON_PATH)
    contract_md = (root / CONTRACT_MD_PATH).read_text(encoding="utf-8")
    regen_contract_md = builder.render_contract_markdown(contract)
    vr.check(
        "contract_md_from_json_byte_equal",
        contract_md == regen_contract_md,
        f"tracked_len={len(contract_md)}, regen_len={len(regen_contract_md)}",
    )

    benchmark = load_json(root / BENCHMARK_JSON_PATH)
    benchmark_md = (root / BENCHMARK_MD_PATH).read_text(encoding="utf-8")
    regen_benchmark_md = builder.render_benchmark_markdown(benchmark)
    vr.check(
        "benchmark_md_from_json_byte_equal",
        benchmark_md == regen_benchmark_md,
        f"tracked_len={len(benchmark_md)}, regen_len={len(regen_benchmark_md)}",
    )


# ---------------------------------------------------------------------------
# 9. Content-safety checks
# ---------------------------------------------------------------------------

def verify_content_safety(root: Path, vr: VerificationResult) -> None:
    content_files = [
        CONTRACT_JSON_PATH, CONTRACT_MD_PATH,
        BENCHMARK_JSON_PATH, BENCHMARK_MD_PATH,
        ENV_JSON_PATH, FREEZE_MANIFEST_PATH,
    ]
    all_text = ""
    for rel in content_files:
        p = root / rel
        if p.is_file():
            all_text += p.read_text(encoding="utf-8")

    abs_path_pattern = re.compile(r'(?:/Users|/home|/tmp|/var|/opt|/etc|C:\\)[^\s"\'<>]+')
    abs_matches = abs_path_pattern.findall(all_text)
    vr.check("content_no_absolute_local_paths", len(abs_matches) == 0, f"found: {abs_matches[:5]}")

    username_patterns = re.compile(r'/Users/(\w+)/|/home/(\w+)/')
    username_matches = username_patterns.findall(all_text)
    vr.check("content_no_usernames", len(username_matches) == 0, f"found: {username_matches[:5]}")

    vr.check("content_no_cci_references", "cci:" not in all_text, "")

    unsupported = ["ACM badge", "NIST-certified", "ISO-certified", "IEEE-certified", "security-certified"]
    contract_json = load_json(root / CONTRACT_JSON_PATH)
    mb_stripped = []
    for mb in contract_json.get("methodological_basis", []):
        mb_copy = {k: v for k, v in mb.items() if k != "unsupported_claims"}
        mb_stripped.append(mb_copy)
    contract_json_stripped = {k: v for k, v in contract_json.items() if k != "methodological_basis"}
    contract_json_stripped["methodological_basis"] = mb_stripped
    check_text = json.dumps(contract_json_stripped, ensure_ascii=False, sort_keys=True)
    for rel in [BENCHMARK_JSON_PATH, ENV_JSON_PATH, FREEZE_MANIFEST_PATH]:
        p = root / rel
        if p.is_file():
            check_text += p.read_text(encoding="utf-8")
    for term in unsupported:
        vr.check(f"content_no_unsupported_claim_{term}", term not in check_text, "")

    hostname_pattern = re.compile(r'@(?:\w+\.)+\w{2,}')
    hostname_matches = hostname_pattern.findall(all_text)
    vr.check("content_no_hostnames", len(hostname_matches) == 0, f"found: {hostname_matches[:5]}")


# ---------------------------------------------------------------------------
# 10. Freeze manifest verification
# ---------------------------------------------------------------------------

def verify_freeze_manifest(root: Path, vr: VerificationResult) -> None:
    p = root / FREEZE_MANIFEST_PATH
    manifest = load_json(p)

    vr.check("manifest_id", manifest.get("manifest_id") == FREEZE_MANIFEST_ID, str(manifest.get("manifest_id")))
    vr.check("manifest_version", manifest.get("version") == FREEZE_MANIFEST_VERSION, str(manifest.get("version")))
    vr.check("manifest_hash_algorithm", manifest.get("hash_algorithm") == "SHA-256", "")
    vr.check("manifest_self_hash_excluded", manifest.get("self_hash_included") is False, "")
    vr.check("manifest_starting_commit", manifest.get("starting_commit") == STARTING_COMMIT, str(manifest.get("starting_commit")))

    files = manifest.get("files", {})
    expected_keys = set(FREEZE_MANIFEST_TARGETS)
    actual_keys = set(files.keys())
    vr.check("manifest_files_exact_set", actual_keys == expected_keys, f"missing={expected_keys - actual_keys}, unexpected={actual_keys - expected_keys}")
    vr.check("manifest_no_self_hash", FREEZE_MANIFEST_PATH not in files, "")

    for rel in FREEZE_MANIFEST_TARGETS:
        actual_hash = sha256_file(root / rel)
        manifest_hash = files.get(rel)
        vr.check(f"manifest_hash_match:{rel}", actual_hash == manifest_hash, f"actual={actual_hash}, manifest={manifest_hash}")


# ---------------------------------------------------------------------------
# 11. Environment JSON verification
# ---------------------------------------------------------------------------

def verify_env_json(root: Path, vr: VerificationResult) -> None:
    p = root / ENV_JSON_PATH
    env = load_json(p)
    vr.check("env_starting_commit", env.get("starting_commit") == STARTING_COMMIT, str(env.get("starting_commit")))
    vr.check("env_branch", env.get("branch") == "major-revision-analysis-v2", str(env.get("branch")))
    vr.check("env_python_version", bool(env.get("python_full_version")), "")
    vr.check("env_operating_system", bool(env.get("operating_system_name")), "")
    vr.check("env_installed_packages", isinstance(env.get("installed_packages_directly_imported_by_gd6_scripts"), dict), "")
    vr.check("env_dependency_files", isinstance(env.get("dependency_declaration_files"), dict), "")


# ---------------------------------------------------------------------------
# 12. No production action
# ---------------------------------------------------------------------------

def verify_no_production_action(root: Path, vr: VerificationResult) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{STARTING_COMMIT}...HEAD"],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    changed = [l for l in result.stdout.strip().split("\n") if l]
    production_paths = [
        "results/part1_full_reproduction/",
        "results/part3b_prediction_ledger/",
        "reports/part3b_et_canonical_reconciliation.json",
        "reports/part3b_et_canonical_reconciliation.md",
        "reports/part3b_et_reconciliation_policy.json",
        "reports/part3b_et_reconciliation_policy.md",
        "scripts/build_part3b_prediction_ledger.py",
        "scripts/part3b_et_reconciliation_policy.py",
        "scripts/freeze_part3b_et_reconciliation_policy.py",
        "scripts/audit_part3b_et_canonical_reconciliation.py",
        "scripts/audit_part3b_et_policy_implementation.py",
    ]
    production_changed = [p for p in changed if any(p.startswith(pp) or p == pp for pp in production_paths)]
    vr.check(
        "no_production_artifact_changed",
        len(production_changed) == 0,
        f"changed: {production_changed}" if production_changed else "",
    )


# ---------------------------------------------------------------------------
# 13. No prohibited claims in content
# ---------------------------------------------------------------------------

def verify_no_prohibited_claims(root: Path, contract: Dict[str, Any], benchmark: Dict[str, Any], vr: VerificationResult) -> None:
    prohibited = sorted(set(contract.get("prohibited_claims", [])))
    contract_check = {k: v for k, v in contract.items() if k not in ("prohibited_claims", "limitations")}
    benchmark_check = {k: v for k, v in benchmark.items() if k not in ()}
    contract_text = json.dumps(contract_check, ensure_ascii=False, sort_keys=True)
    benchmark_text = json.dumps(benchmark_check, ensure_ascii=False, sort_keys=True)
    for pc in prohibited:
        in_contract = pc in contract_text
        in_benchmark = pc in benchmark_text
        if in_contract or in_benchmark:
            vr.check(f"no_prohibited_claim_{pc}", False, f"found in {'contract' if in_contract else 'benchmark'}")
        else:
            vr.check(f"no_prohibited_claim_{pc}", True, "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    root = repo_root()
    vr = VerificationResult()

    print("=== G.D6 Acceptance Contract Package Verification ===")
    print(f"Starting commit: {STARTING_COMMIT}")
    print()

    print("[1] Verifying all authorized files exist...")
    verify_all_authorized_files_exist(root, vr)

    print("[2] Verifying git scope...")
    verify_git_scope(root, vr)

    print("[3] Verifying JSON files parse...")
    verify_json_parses(root, vr)

    print("[4] Verifying contract JSON...")
    contract = verify_contract_json(root, vr)

    print("[5] Verifying benchmark JSON...")
    benchmark = verify_benchmark_json(root, vr)

    print("[6] Verifying cross-references...")
    verify_cross_references(root, contract, benchmark, vr)

    print("[7] Verifying deterministic regeneration...")
    verify_deterministic_regeneration(root, vr)

    print("[8] Verifying JSON/Markdown consistency...")
    verify_json_md_consistency(root, vr)

    print("[9] Verifying content safety...")
    verify_content_safety(root, vr)

    print("[10] Verifying freeze manifest...")
    verify_freeze_manifest(root, vr)

    print("[11] Verifying reference environment JSON...")
    verify_env_json(root, vr)

    print("[12] Verifying no prohibited claims in content...")
    verify_no_prohibited_claims(root, contract, benchmark, vr)

    print("[13] Verifying no production action...")
    verify_no_production_action(root, vr)

    report = vr.as_dict()
    report_json = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    print()
    print("=== Verification Report ===")
    print(report_json)

    passed = vr.all_passed
    total_checks = len(vr.checks)
    passed_checks = sum(1 for c in vr.checks if c["passed"])
    failed_checks = total_checks - passed_checks

    print()
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    print(f"Warnings: {len(vr.warnings)}")

    if passed:
        print("\nALL CHECKS PASSED.")
        return 0
    else:
        print(f"\n{len(vr.errors)} ERROR(S).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
