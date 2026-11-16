---
title: 'Fix Folders Server component fixtures for Release qualification'
type: 'bugfix'
created: '2026-11-16'
status: 'draft'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Folders' complete Server hook enables eleven real-Keycloak security cases without their Platform-owned fixture. Their success case also assumes Debug/source SDK binaries, so an injected fixture alone cannot qualify Release/package output.

**Approach:** Run the complete Server project once inside a genuine Platform component lifetime. Retain source identity proof and add strict NuGet payload binding for package mode; then resume publication verification.

## Boundaries & Constraints

**Always:** Keep all eleven behavioral cases and exact Debug/source byte binding in source mode. Package mode proves resolved package identity and payload bytes. Preserve nonempty complete-project execution, native exit and zero error/failure/skip/not-run counters. Build provider/.NET outputs once before hooks. Retain TLS, independent RSA, private credentials, natural expiry, deadlines and observed cleanup. Preserve concurrent work and owned content. Use intended profiles and approved exact-input preparation checks.

**Never:** Invent manifests/hashes, select identity authority by file availability, fall back after identity failure, weaken guards, add skips/exclusions, repeat filtered cases, or claim component proof as protected enrollment. Held FR58 work, AppHost's multiple-cohort lifecycle and migration acceptance remain outside this Server correction.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Prebuilt Server project and provider; valid package bindings | Execute the entire project once with the real issuer; all eleven cases pass. |
| Debug/source input | Require the existing exact source SHA-256 and MVID checks. |
| Missing, ambiguous or altered package/asset metadata | Refuse before claiming security qualification; no source fallback. |
| Missing provider, fixture failure, timeout or child failure | Fail with bounded sanitized diagnostics; clean only owned resources. |
| Empty, filtered, skipped or not-run execution | Fail the complete-project verification. |
| Child exits or fixture preparation fails | Observe container/private-file cleanup; expose cleanup failure. |

</frozen-after-approval>

## Code Map

- Platform `infrastructure/keycloak-workload-binding/verify_component.py:run` owns the real fixture but launches a filtered class. Reuse its provisioning.
- Folders Server `EnrolledWorkloadSourceBoundaryTests.cs` contains all eleven cases and hardcoded Debug comparison; its project already defines `FOLDERS_OWNER_METADATA_SOURCE`. Select identity authority through evaluated build metadata.
- Folders `tests/tools/run-complete-project-tests.ps1` and `.github/actions/after-unit-tests/action.yml` own complete execution. The preparation script and Server project can prepare artifacts before hooks.
- [Failure](push-main-20261116T212849Z/README.md) and [revision evidence](evidence/fix-folders-component-fixtures-20261116/investigation-inputs.json) identify exact inputs.

## Tasks & Acceptance

**Execution:**
- [ ] Platform `infrastructure/keycloak-workload-binding/{verify_component,component_fixture}.py` — add a bounded fixture scope and complete assembly invocation; prepare the real descriptor, await the child, propagate failure and observe cleanup. Preserve focused modes.
- [ ] Platform `infrastructure/keycloak-workload-binding/test_component_fixture.py` — verify startup/child/timeout/cleanup failures, private files, sanitized output and strict executed-test evidence.
- [ ] Folders `tests/Hexalith.Folders.Server.Tests/{EnrolledWorkloadSourceBoundaryTests,PackageSdkRuntimeBinding,PackageSdkRuntimeBindingTests}.cs` — retain source assertions; derive package ID/version/runtime entry from restored assets/dependency metadata, verify archive SHA-512 against restore content identity, and compare every currently checked SDK DLL's SHA-256/MVID to its archive payload. Reject missing/ambiguous/tampered inputs.
- [ ] Folders `tests/Hexalith.Folders.Server.Tests/Hexalith.Folders.Server.Tests.csproj`, `scripts/prepare-ci-topology-projects.sh` and complete runner — prepare provider once before hooks; record identity inputs; run one complete prebuilt Server suite within the fixture. Preserve other project behavior and strict counters.
- [ ] Platform `docs/security/workload-binding-enrollment.md`, Folders `docs/ci.md` and CiCd evidence — document authority/lifecycle boundaries and save revisions, complete results and cleanup proof.

**Acceptance Criteria:**
- Given exact fresh-main inputs, when Server qualification runs, then the complete Release/package suite and all eleven cases pass once without skips or hook builds.
- Given altered SDK payloads/metadata, when identity validation runs, then it fails; Debug/source comparisons remain mandatory in source mode.
- Given fixture success or failure, when execution ends, then cleanup succeeds or blocks publication without exposing credentials.

## Implementation Notes

- Prior publication authorization persists. Publish dependencies/pointers only after applicable checks; retain independent AppHost/FR58 blockers and incomplete migration status.

## Spec Change Log

## Review Triage Log

## Verification

- Use `run-with-temp`; retain logs outside scratch and await children.
- Run fixture/provenance failure tests, audited Release build, complete Server suite and existing source component lane; record inventories and zero skipped/not-run counts.
- Require real Keycloak 26.6.4, identity/cleanup proof, released audit/action checks, exact commitlint and owned-content preservation before pushes. Resume broader publication checks and report independent failures.
