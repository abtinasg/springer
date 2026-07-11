#!/usr/bin/env python3
"""Part 3B.2R.1-G.D6-F0: Verify acceptance contract package v1.0."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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

CONTRACT_ID = "SEMIT-GD6-ACCEPTANCE-CONTRACT"
BENCHMARK_ID = "SEMIT-GD6-BENCHMARK"
FREEZE_MANIFEST_ID = "SEMIT-GD6-CONTRACT-FREEZE-MANIFEST"


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


def verify_all_authorized_files_exist(root: Path, vr: VerificationResult) -> None:
    for rel in AUTHORIZED_FILES:
        p = root / rel
        vr.check(f"file_exists:{rel}", p.is_file(), str(p))


def verify_no_existing_tracked_file_changed(root: Path, vr: VerificationResult) -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    lines = [l for l in result.stdout.strip().split("\n") if l]
    changed_existing = []
    new_authorized = []
    for line in lines:
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if "__pycache__" in path or path.endswith(".pyc"):
            continue
        if path in AUTHORIZED_FILES:
            new_authorized.append(path)
        else:
            changed_existing.append({"path": path, "status": status})
    vr.check(
        "no_existing_tracked_file_changed",
        len(changed_existing) == 0,
        f"changed files: {changed_existing}" if changed_existing else "",
    )


def verify_contract_json(root: Path, vr: VerificationResult) -> Dict[str, Any]:
    p = root / CONTRACT_JSON_PATH
    contract = load_json(p)
    vr.check("contract_id", contract.get("contract_id") == CONTRACT_ID, str(contract.get("contract_id")))
    vr.check("contract_version", contract.get("version") == "1.0", str(contract.get("version")))
    vr.check("contract_status", contract.get("status") == "freeze_candidate", str(contract.get("status")))

    claims = contract.get("scientific_claims", [])
    vr.check("exactly_five_claims", len(claims) == 5, f"found {len(claims)}")
    claim_ids = [c.get("claim_id") for c in claims]
    expected_ids = ["CLAIM-A", "CLAIM-B", "CLAIM-C", "CLAIM-D", "CLAIM-E"]
    vr.check("claim_ids_exact", claim_ids == expected_ids, str(claim_ids))

    tb = contract.get("trust_boundary", {})
    vr.check("trusted_infrastructure_present", len(tb.get("trusted_infrastructure", [])) > 0, "")
    vr.check("in_scope_components_present", len(tb.get("in_scope_components", [])) > 0, "")

    ar = contract.get("acceptance_rule", {})
    vr.check("acceptance_no_weighted_score", ar.get("no_weighted_score") is True, "")
    vr.check("acceptance_no_partial", ar.get("no_partial_acceptance") is True, "")
    vr.check("acceptance_one_fail_rejects", ar.get("one_failed_mandatory_condition_means_not_accepted") is True, "")

    rr = contract.get("reopening_rule", {})
    vr.check("reopening_all_required", rr.get("all_required") is True, "")
    vr.check("reopening_five_requirements", len(rr.get("requirements", [])) == 5, str(len(rr.get("requirements", []))))

    sr = contract.get("stopping_rule", {})
    vr.check("stopping_rule_present", "statement" in sr, "")

    sc = contract.get("severity_classification", {})
    for level in ["critical", "major", "minor"]:
        vr.check(f"severity_{level}", level in sc, "")

    vr.check("mandatory_benchmark_groups_count", len(contract.get("mandatory_benchmark_groups", [])) == 11, "")

    mb = contract.get("methodological_basis", [])
    vr.check("methodological_basis_count", len(mb) == 5, f"found {len(mb)}")
    mb_ids = [m.get("source_id") for m in mb]
    vr.check("methodological_basis_ids", mb_ids == ["MB-01", "MB-02", "MB-03", "MB-04", "MB-05"], str(mb_ids))

    pc = contract.get("prohibited_claims", [])
    vr.check("prohibited_claims_present", len(pc) > 0, "")

    nc = contract.get("normative_clauses", [])
    vr.check("normative_clauses_present", len(nc) > 0, f"found {len(nc)}")
    for clause in nc:
        basis = clause.get("basis", [])
        has_external = any(b.get("basis_type") == "external_methodological_source" for b in basis)
        has_internal = any(b.get("basis_type") == "internal_project_evidence" for b in basis)
        vr.check(
            f"normative_clause_{clause.get('clause_id')}_has_basis",
            len(basis) > 0,
            f"basis count: {len(basis)}",
        )

    return contract


def verify_benchmark_json(root: Path, vr: VerificationResult) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    p = root / BENCHMARK_JSON_PATH
    benchmark = load_json(p)
    vr.check("benchmark_id", benchmark.get("benchmark_id") == BENCHMARK_ID, str(benchmark.get("benchmark_id")))
    vr.check("benchmark_version", benchmark.get("version") == "1.0", str(benchmark.get("version")))

    groups = benchmark.get("benchmark_groups", [])
    vr.check("benchmark_groups_count", len(groups) == 11, f"found {len(groups)}")
    group_ids = [g.get("group_id") for g in groups]
    expected_gids = [f"BG-{i:02d}" for i in range(1, 12)]
    vr.check("benchmark_group_ids", group_ids == expected_gids, str(group_ids))

    ec = benchmark.get("expected_counts", {})
    vr.check("expected_counts_has_all_groups", set(ec.keys()) == set(expected_gids), str(sorted(ec.keys())))

    items = benchmark.get("benchmark_items", [])
    vr.check("benchmark_items_present", len(items) > 0, f"found {len(items)}")

    for item in items:
        vr.check(
            f"benchmark_item_{item['benchmark_id']}_has_provenance",
            "provenance" in item,
            "",
        )

    es = benchmark.get("exact_sets", {})
    vr.check("exact_sets_write_guard_mechanisms", len(es.get("write_guard_mechanisms", [])) == 15, "")
    vr.check("exact_sets_production_entry_points", len(es.get("production_entry_points", [])) == 4, "")
    vr.check("exact_sets_restoration_keys", len(es.get("restoration_keys", [])) == 20, "")
    vr.check("exact_sets_forced_exception_paths", len(es.get("forced_exception_fixture_paths", [])) == 3, "")
    vr.check("exact_sets_rollback_scenarios", len(es.get("rollback_scenarios", [])) == 6, "")
    vr.check("exact_sets_rollback_mutations", len(es.get("rollback_mutations", [])) == 7, "")

    fv = benchmark.get("future_verifier_requirement", {})
    vr.check("future_verifier_path", fv.get("verifier_path") == "scripts/verify_gd6_frozen_benchmark_v1.py", "")
    vr.check("future_verifier_execution_pattern", fv.get("execution_pattern") == "python3 scripts/verify_gd6_frozen_benchmark_v1.py", "")

    return benchmark, es


def verify_contract_md(root: Path, contract: Dict[str, Any], vr: VerificationResult) -> None:
    p = root / CONTRACT_MD_PATH
    md = p.read_text(encoding="utf-8")
    vr.check("contract_md_starts_with_title", md.startswith("# G.D6 Acceptance Contract"), md[:80])
    vr.check("contract_md_has_contract_id", CONTRACT_ID in md, "")
    for claim in contract.get("scientific_claims", []):
        vr.check(f"contract_md_has_{claim['claim_id']}", claim["claim_id"] in md, "")
    for mb in contract.get("methodological_basis", []):
        vr.check(f"contract_md_has_{mb['source_id']}", mb["source_id"] in md, "")


def verify_benchmark_md(root: Path, benchmark: Dict[str, Any], vr: VerificationResult) -> None:
    p = root / BENCHMARK_MD_PATH
    md = p.read_text(encoding="utf-8")
    vr.check("benchmark_md_starts_with_title", md.startswith("# G.D6 Benchmark Manifest"), md[:80])
    vr.check("benchmark_md_has_benchmark_id", BENCHMARK_ID in md, "")
    for g in benchmark.get("benchmark_groups", []):
        vr.check(f"benchmark_md_has_{g['group_id']}", g["group_id"] in md, "")


def verify_env_json(root: Path, vr: VerificationResult) -> None:
    p = root / ENV_JSON_PATH
    env = load_json(p)
    vr.check("env_python_version", bool(env.get("python_full_version")), "")
    vr.check("env_operating_system", bool(env.get("operating_system_name")), "")
    vr.check("env_installed_packages", isinstance(env.get("installed_packages_directly_imported_by_gd6_scripts"), dict), "")
    vr.check("env_dependency_files", isinstance(env.get("dependency_declaration_files"), dict), "")
    vr.check("env_starting_commit", bool(env.get("starting_commit")), "")
    vr.check("env_branch", env.get("branch") == "major-revision-analysis-v2", "")


def verify_freeze_manifest(root: Path, vr: VerificationResult) -> None:
    p = root / FREEZE_MANIFEST_PATH
    manifest = load_json(p)
    vr.check("manifest_id", manifest.get("manifest_id") == FREEZE_MANIFEST_ID, str(manifest.get("manifest_id")))
    vr.check("manifest_hash_algorithm", manifest.get("hash_algorithm") == "SHA-256", "")
    vr.check("manifest_self_hash_excluded", manifest.get("self_hash_included") is False, "")

    files = manifest.get("files", {})
    expected_files = [f for f in AUTHORIZED_FILES if f != FREEZE_MANIFEST_PATH]
    vr.check("manifest_files_count", len(files) == len(expected_files), f"expected {len(expected_files)}, got {len(files)}")

    for rel in expected_files:
        actual_hash = sha256_file(root / rel)
        manifest_hash = files.get(rel)
        vr.check(f"manifest_hash_match:{rel}", actual_hash == manifest_hash, f"actual={actual_hash}, manifest={manifest_hash}")

    vr.check("manifest_no_self_hash", FREEZE_MANIFEST_PATH not in files, "")


def verify_no_prohibited_sources(root: Path, contract: Dict[str, Any], vr: VerificationResult) -> None:
    mb = contract.get("methodological_basis", [])
    valid_ids = {m["source_id"] for m in mb}
    for clause in contract.get("normative_clauses", []):
        for basis in clause.get("basis", []):
            sid = basis.get("source_id", "")
            is_external = basis.get("basis_type") == "external_methodological_source"
            is_internal = basis.get("basis_type") == "internal_project_evidence"
            if is_external:
                vr.check(
                    f"clause_{clause['clause_id']}_external_source_in_mb",
                    sid in valid_ids,
                    f"source_id={sid} not in methodological_basis",
                )
            if is_internal:
                p = root / sid
                vr.check(
                    f"clause_{clause['clause_id']}_internal_source_exists",
                    p.exists(),
                    f"path {sid} does not exist",
                )


def verify_no_prohibited_claims(root: Path, contract: Dict[str, Any], benchmark: Dict[str, Any], vr: VerificationResult) -> None:
    prohibited = set(contract.get("prohibited_claims", []))
    contract_check = {k: v for k, v in contract.items() if k not in ("prohibited_claims", "limitations")}
    benchmark_check = {k: v for k, v in benchmark.items() if k not in ("prohibited_claims", "limitations")}
    contract_text = json.dumps(contract_check, ensure_ascii=False, sort_keys=True)
    benchmark_text = json.dumps(benchmark_check, ensure_ascii=False, sort_keys=True)
    for pc in prohibited:
        in_contract = pc in contract_text
        in_benchmark = pc in benchmark_text
        if in_contract or in_benchmark:
            vr.check(f"no_prohibited_claim_{pc}", False, f"found in {'contract' if in_contract else 'benchmark'}")
        else:
            vr.check(f"no_prohibited_claim_{pc}", True, "")


def verify_json_parses(root: Path, vr: VerificationResult) -> None:
    for rel in [CONTRACT_JSON_PATH, BENCHMARK_JSON_PATH, ENV_JSON_PATH, FREEZE_MANIFEST_PATH]:
        p = root / rel
        try:
            load_json(p)
            vr.check(f"json_parses:{rel}", True, "")
        except Exception as exc:
            vr.check(f"json_parses:{rel}", False, str(exc))


def verify_no_production_action(root: Path, vr: VerificationResult) -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
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


def main() -> int:
    root = repo_root()
    vr = VerificationResult()

    print("Verifying all authorized files exist...")
    verify_all_authorized_files_exist(root, vr)

    print("Verifying no existing tracked file changed...")
    verify_no_existing_tracked_file_changed(root, vr)

    print("Verifying JSON files parse...")
    verify_json_parses(root, vr)

    print("Verifying contract JSON...")
    contract = verify_contract_json(root, vr)

    print("Verifying benchmark JSON...")
    benchmark, es = verify_benchmark_json(root, vr)

    print("Verifying contract Markdown...")
    verify_contract_md(root, contract, vr)

    print("Verifying benchmark Markdown...")
    verify_benchmark_md(root, benchmark, vr)

    print("Verifying reference environment JSON...")
    verify_env_json(root, vr)

    print("Verifying freeze manifest...")
    verify_freeze_manifest(root, vr)

    print("Verifying no prohibited sources...")
    verify_no_prohibited_sources(root, contract, vr)

    print("Verifying no prohibited claims...")
    verify_no_prohibited_claims(root, contract, benchmark, vr)

    print("Verifying no production action...")
    verify_no_production_action(root, vr)

    report = vr.as_dict()
    report_json = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    print("\n" + report_json)

    if vr.all_passed:
        print("\nALL CHECKS PASSED.")
        return 0
    else:
        print(f"\n{len(vr.errors)} ERROR(S).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
