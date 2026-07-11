# G.D6 Acceptance Contract

**Stage:** Part 3B.2R.1-G.D6-F0.1
**Contract ID:** SEMIT-GD6-ACCEPTANCE-CONTRACT
**Version:** 1.0
**Status:** freeze_candidate
**Freeze effective when:** this exact contract package commit is independently accepted
**Starting commit:** `7dbc206037250b1181aed94bfa7326d79df814fd`

## Purpose

Define and freeze the scientific and engineering claims, trusted-computing boundary, acceptance criteria, benchmark cases, stopping rule, reopening rule, and evidence package for G.D6 before any further implementation.

## Scientific Claims

### CLAIM-A — Correct Classification

The frozen policy implementation classifies the defined valid and invalid cases according to the frozen reconciliation policy and benchmark. This claim is bounded to the listed benchmark and invariants. It is not a claim of universal correctness.

Basis:

- **internal_project_evidence** — scripts/build_part3b_prediction_ledger.py: run_et_reconciliation_policy_self_tests() defines the exact test cases for classification
- **external_methodological_source** — MB-01: bounded testing scope

### CLAIM-B — No Unauthorized Approval or Enforcement

G.D6 classification must never independently produce final approval, policy enforcement, production authorization, Part 3B completion, or Part 3C authorization.

Basis:

- **internal_project_evidence** — reports/part3b_et_policy_implementation.json: policy_approved, policy_enforced, production_execution_authorized, part3b_complete, part3c_authorized are all false
- **external_methodological_source** — MB-02: test completion criteria

### CLAIM-C — Artifact Preservation

The G.D6 verification process must not alter canonical Part 1 artifacts, existing Part 3B artifacts, frozen policy evidence, or frozen reconciliation evidence.

Basis:

- **internal_project_evidence** — reports/part3b_et_policy_implementation.json: protected_files_unchanged is true and recursive_snapshot_changed is 0
- **external_methodological_source** — MB-05: versioned development evidence

### CLAIM-D — Recoverability

After an injected exception or transactional-publication failure, patched global objects must be restored, protected files must retain their prior state, temporary and backup files must not remain, and publication state must be restored.

Basis:

- **internal_project_evidence** — reports/part3b_et_policy_implementation.json: forced_exception_test_passed is true and rollback_all_scenarios_passed is true
- **external_methodological_source** — MB-02: planned and documented test processes

### CLAIM-E — Reproducible Verification

An independent evaluator must be able to execute the frozen verifier in a clean environment using the documented command and obtain the same Pass/Fail decision.

Basis:

- **internal_project_evidence** — scripts/audit_part3b_et_policy_implementation.py: existing verifier pattern with documented execution command
- **external_methodological_source** — MB-03: documenting research sufficiently for independent verification
- **external_methodological_source** — MB-04: independent evaluation of computational artifacts

## Trust Boundary

### Trusted Infrastructure

- python_interpreter
- python_standard_library
- operating_system
- filesystem_implementation
- git_implementation
- sha256_implementation
- cpu
- memory_hardware
- github_hosting_infrastructure
- installed_third_party_libraries_at_recorded_versions
- absence_of_deliberate_malicious_tampering_below_repository_level

_These components are trusted assumptions, not verified conclusions._

### In-Scope Components

- frozen_reconciliation_policy_implementation
- integration_points_used_by_gd6
- benchmark_fixtures
- benchmark_expected_outcomes
- write_guards
- production_entry_guards
- restoration_logic
- rollback_logic
- protected_artifact_comparison
- report_generation
- json_markdown_consistency
- frozen_verifier
- environment_and_provenance_records

## Acceptance Rule

**Rule:** G.D6 Accepted = every mandatory contract condition passes.

- No weighted score: True
- No majority vote: True
- No partial acceptance: True
- No discretionary override: True
- No compensation: True
- One failed mandatory condition means not accepted: True
- Contract does not mark G.D6 accepted: True

## Stopping Rule

After Acceptance Contract v1.0 and Benchmark Manifest v1.0 are independently accepted and frozen, no new G.D6 acceptance criterion may be introduced during the same evaluation cycle.

## Reopening Rule

All required: True

Requirements:

- exact_input_or_fixture
- exact_execution_command
- reproducible_on_frozen_commit
- incorrect_verifier_pass
- claim_relevant_material_effect

Non-reopening:

- hypothetical_concerns_without_executable_evidence
- code_style_preferences
- naming_improvements
- formatting_changes
- speed_optimizations
- additional_defense_in_depth_outside_frozen_claims
- edge_cases_outside_declared_trust_boundary
- defects_that_cannot_affect_a_paper_claim

## Severity Classification

### Critical

**Description:** A reproducible defect that can alter a paper result, grant unauthorized approval, authorize production, enforce policy, modify protected artifacts, or make the frozen verifier incorrectly pass a mandatory mutation.
**Effect:** blocks acceptance; reopens accepted G.D6 if discovered later

### Major

**Description:** A reproducible defect that prevents independent execution, invalidates environment provenance, breaks JSON/Markdown consistency, makes required rollback or restoration evidence incomplete, or makes mandatory benchmark evidence unavailable.
**Effect:** blocks acceptance until corrected

### Minor

**Description:** A defect limited to naming, formatting, refactoring, non-material documentation improvement, performance optimization, or non-claim-relevant cleanup.
**Effect:** recorded but does not block acceptance

## Mandatory Benchmark Groups

- BG-01
- BG-02
- BG-03
- BG-04
- BG-05
- BG-06
- BG-07
- BG-08
- BG-09
- BG-10
- BG-11

## Evidence Requirements

- **all_eight_authorized_files_exist** (mandatory: True)
- **no_existing_tracked_file_changed** (mandatory: True)
- **contract_package_verifier_exits_0** (mandatory: True)
- **contract_json_and_markdown_consistent** (mandatory: True)
- **benchmark_json_and_markdown_consistent** (mandatory: True)
- **exact_benchmark_sets_present** (mandatory: True)
- **every_normative_clause_grounded** (mandatory: True)
- **no_unresolved_required_fact** (mandatory: True)
- **freeze_manifest_hashes_match** (mandatory: True)
- **no_self_referential_hash** (mandatory: True)
- **no_production_action_occurred** (mandatory: True)
- **working_tree_clean_after_commit** (mandatory: True)

## Limitations

- This is a bounded empirical verification contract, not a formal proof.
- No claim of formal verification or mathematical proof of total correctness.
- No claim of absence of all possible defects.
- No ISO, IEEE, ACM, or NIST certification.
- No guarantee of Q2 or Q3 journal acceptance.
- No security against malicious operating systems.
- No verification of Python, Git, SHA-256, CPU, memory, or the operating system.
- No completion of Part 3B.
- No authorization of Part 3C.
- No approval or enforcement of the policy.
- No authorization of production execution.

## Methodological Basis

### MB-01

**Title:** ISO/IEC/IEEE 29119-1:2022 — Software and systems engineering — Software testing — Part 1: General concepts
**Issuer:** ISO/IEC/IEEE
**Version/Year:** 2022
**Authority type:** standard

Supported use:

- terminology for software testing
- explicit test objectives
- test conditions and evidence
- bounded testing scope

Unsupported claims:

- ISO compliance
- ISO certification

### MB-02

**Title:** ISO/IEC/IEEE 29119-2:2021 — Software and systems engineering — Software testing — Part 2: Test processes
**Issuer:** ISO/IEC/IEEE
**Version/Year:** 2021
**Authority type:** standard

Supported use:

- planned and documented test processes
- test monitoring
- test completion criteria
- traceable test work products

Unsupported claims:

- ISO compliance
- ISO certification
- reproduction of inaccessible copyrighted standard text

### MB-03

**Title:** IEEE Author Center — Research Reproducibility
**Issuer:** IEEE
**Version/Year:** current
**Authority type:** official_guidance

Supported use:

- documenting research sufficiently for independent verification
- preserving code, data, and research outputs
- recording execution information

### MB-04

**Title:** ACM Data & Software Artifacts / Artifact Review and Badging, Version 1.1
**Issuer:** ACM
**Version/Year:** 1.1
**Authority type:** official_guidance

Supported use:

- artifact completeness
- artifact usability
- relationship between artifacts and paper claims
- independent evaluation of computational artifacts

Unsupported claims:

- ACM badge has been awarded

### MB-05

**Title:** NIST SP 800-218, Secure Software Development Framework, Version 1.1
**Issuer:** NIST
**Version/Year:** 1.1
**Authority type:** standard

Supported use:

- versioned development evidence
- provenance
- verification practices
- documented software-development controls

Unsupported claims:

- NIST-certified
- security-certified

## Prohibited Claims

- formal_verification
- mathematical_proof_of_total_correctness
- absence_of_all_possible_defects
- ISO_certification
- IEEE_certification
- ACM_certification
- NIST_certification
- guaranteed_Q2_or_Q3_journal_acceptance
- security_against_malicious_operating_systems
- verification_of_python_git_sha256_cpu_memory_or_operating_system
- completion_of_Part_3B
- authorization_of_Part_3C
- approval_of_the_policy
- enforcement_of_the_policy
- authorization_of_production_execution

## Normative Clauses

### NC-01

G.D6 Accepted = every mandatory contract condition passes.

Basis:

- **external_methodological_source** — MB-02: test completion criteria

### NC-02

No weighted score, no majority vote, no partial acceptance, no discretionary override, no compensation between failed and passed conditions. One failed mandatory condition means G.D6 is not accepted.

Basis:

- **external_methodological_source** — MB-02: test completion criteria

### NC-03

The contract itself must not mark G.D6 as accepted. It only defines the future decision rule.

Basis:

- **internal_project_evidence** — reports/part3b_et_reconciliation_policy.json: policy_status is specified_not_enforced

### NC-04

After Acceptance Contract v1.0 and Benchmark Manifest v1.0 are independently accepted and frozen, no new G.D6 acceptance criterion may be introduced during the same evaluation cycle.

Basis:

- **external_methodological_source** — MB-02: test completion criteria

### NC-05

If the frozen verifier passes every mandatory benchmark item, G.D6 must be accepted under Contract v1.0.

Basis:

- **external_methodological_source** — MB-02: test completion criteria

### NC-06

The contract may be reopened only after presentation of a Reproducible Material Counterexample satisfying all five conditions: exact input or fixture, exact execution command, reproducible on frozen commit, incorrect verifier pass, and claim-relevant material effect.

Basis:

- **external_methodological_source** — MB-01: bounded testing scope

### NC-07

Hypothetical concerns without executable evidence, code-style preferences, naming improvements, formatting changes, speed optimizations, additional defense-in-depth outside frozen claims, edge cases outside declared trust boundary, and defects that cannot affect a paper claim do not reopen G.D6.

Basis:

- **external_methodological_source** — MB-01: bounded testing scope

### NC-08

The framework is a bounded empirical verification contract, not a formal proof.

Basis:

- **external_methodological_source** — MB-01: terminology for software testing

### NC-09

Trusted infrastructure components are trusted assumptions, not verified conclusions.

Basis:

- **external_methodological_source** — MB-01: bounded testing scope

### NC-10

The future frozen verifier path is scripts/verify_gd6_frozen_benchmark_v1.py and the execution pattern is python3 scripts/verify_gd6_frozen_benchmark_v1.py.

Basis:

- **internal_project_evidence** — scripts/audit_part3b_et_policy_implementation.py: existing verifier pattern at scripts/audit_part3b_et_policy_implementation.py

### NC-11

Final acceptance later requires execution from a clean clone, recorded environment, exit code 0, complete JSON report, complete Markdown report, no production action, and execution by an evaluator other than the implementation author.

Basis:

- **external_methodological_source** — MB-03: documenting research sufficiently for independent verification
- **external_methodological_source** — MB-04: independent evaluation of computational artifacts

## Provenance

- Starting commit: `7dbc206037250b1181aed94bfa7326d79df814fd`
- Branch: major-revision-analysis-v2
- Repository: abtinasg/springer
- Extraction method: runtime_output_and_constant_extraction_from_starting_commit
