---
title: 'Fix Folders Server component fixtures for Release qualification'
type: 'bugfix'
created: '2026-11-16'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '92e4e0b0acf0a256078c330419734eafa69b84ed'
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
- [x] Platform `infrastructure/keycloak-workload-binding/{verify_component,component_fixture}.py` — add a bounded fixture scope and complete assembly invocation; prepare the real descriptor, await the child, propagate failure and observe cleanup. Preserve focused modes.
- [x] Platform `infrastructure/keycloak-workload-binding/test_component_fixture.py` — verify startup/child/timeout/cleanup failures, private files, sanitized output and strict executed-test evidence.
- [x] Folders `tests/Hexalith.Folders.Server.Tests/{EnrolledWorkloadSourceBoundaryTests,PackageSdkRuntimeBinding,PackageSdkRuntimeBindingTests}.cs` — retain source assertions; derive package ID/version/runtime entry from restored assets/dependency metadata, verify archive SHA-512 against restore content identity, and compare every currently checked SDK DLL's SHA-256/MVID to its archive payload. Reject missing/ambiguous/tampered inputs.
- [x] Folders `tests/Hexalith.Folders.Server.Tests/Hexalith.Folders.Server.Tests.csproj`, `scripts/prepare-ci-topology-projects.sh` and complete runner — prepare provider once before hooks; record identity inputs; run one complete prebuilt Server suite within the fixture. Preserve other project behavior and strict counters.
- [x] Platform `docs/security/workload-binding-enrollment.md`, Folders `docs/ci.md` and CiCd evidence — document authority/lifecycle boundaries and save revisions, complete results and cleanup proof.

**Acceptance Criteria:**
- Given exact fresh-main inputs, when Server qualification runs, then the complete Release/package suite and all eleven cases pass once without skips or hook builds.
- Given altered SDK payloads/metadata, when identity validation runs, then it fails; Debug/source comparisons remain mandatory in source mode.
- Given fixture success or failure, when execution ends, then cleanup succeeds or blocks publication without exposing credentials.

## Implementation Notes

- 2026-11-17: Resumed bmad-build implementation. Local baseline: CiCd `92e4e0b0acf0a256078c330419734eafa69b84ed`, Platform `c2236a9f95c37d4d2ef8dee3fe2cbfe5e9ab41d2`, Folders `e5760ca105652f4d89c4f240e0ca455723c9a473`. Platform/Folders worktrees are clean; preserve existing unrelated CiCd changes. The implementation phase is sequential and local only: no pushes or remote operations during this phase.
- 2026-11-17: Human approved the spec and requested stopping before implementation. The approved intent is frozen; resume from this file in a fresh bmad-build session.
- Prior publication authorization persists. Publish dependencies/pointers only after applicable checks; retain independent AppHost/FR58 blockers and incomplete migration status.

## Spec Change Log

- 2026-11-17: Signed NuGet packages require the canonical signature-aware content SHA-512 from the pinned SDK NuGet API; raw archive SHA-512 is checked separately against its restored sidecar. Frozen identity and payload requirements are unchanged.

## Review Triage Log

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| BH1 | false | reject | The qualified destination is Folders 3ff01eeab6f6dfe7cff83e4ef3e1ff403c50c245, whose recorded Platform 8ccb479e391564ce982309f106504cf8329c0a43 contains component_fixture.py and --complete-assembly. The old shared source checkout is not the qualified destination; dependency publication and final pointer verification remain explicitly pending. |
| BH2 | medium | defer | SIGTERM bypasses Python context cleanup, but the baseline verifier also had no termination handler around TemporaryDirectory/subprocess.run. This pre-existing cancellation defect can leave private scratch/container resources and needs a separate signal-lifetime correction. |
| BH3 | medium | defer | Capture is unbounded before diagnostic truncation; baseline subprocess.run(capture_output=True,text=True) already had unbounded memory capture. The refactor spools before reading but does not create this pre-existing resource-exhaustion root cause. |
| BH4 | medium | patch | Strict UTF-8 decoding occurs before native child-status handling, so non-UTF-8 failure output can replace the child status. Replacement decoding is a direct internal correction. |
| BH5 | low | patch | The private pathname probe does not disclose credential values or defeat 0700/0600 protection, but the sanitizer docstring overstates private-descriptor coverage. Delete that overstatement rather than add an unsupported pathname-confidentiality rule. |
| BH6 | medium | patch | Parent reproduction accepted XML with an assembly error and a missing errors counter against a zero-error summary. Reject error elements and absent expected counters so contradictory evidence cannot qualify. |
| BH7 | medium | patch | The provider compiles for Java 21, while the preparation command selects no JDK and Ubuntu 24.04 runner documentation identifies Java 17 as default and JAVA_HOME_21_X64 as available. Select/validate the required product compiler before Maven without editing owned workflows. |
| BH8 | medium | patch | clone() applies a source delta to a different destination base but records source file hashes. Current fixed bases share those product bytes, yet the function can attest untested source bytes when destination context differs or concurrent source edits occur; hash the completed destination snapshot. |
| BH9 | medium | patch | Parent invoked the actual job() function with a child that starts an escaped session: timeout killed only the original group and the escaped descendant survived. The probe cleaned/reaped it afterward. Reuse owned process supervision with graceful fixture shutdown and observed descendant cleanup. |
| EC1 | medium | defer | Same verified pre-existing unbounded-capture root cause as BH3; disk spooling and the final full read have no capture cap. Keep this distinct from the new structured-diagnostic bypass fixed under EC3. |
| EC2 | medium | patch | Same strict-decoding root cause as BH4; decoding failure precedes recorded native status. Replace invalid byte sequences and cover the native-status path. |
| EC3 | high | patch | Parent reproduced a registered secret in runtime-binding output and 25,069 emitted characters: record_evidence prints structured data without sanitize(). Sanitize and bound every diagnostic emission, including structured observations. |
| VG1 | medium | patch | Pre-verified broken-verification gap: filtered XML reports eleven cases but the test summary reports twelve, so the earlier consistency guard hides deletion of the complete-project guard. Use matching eleven-case evidence and verify focused acceptance versus complete rejection. |
| VG2 | medium | patch | Pre-verified broken-verification gap: ChildFailure subclasses RuntimeError, so the broad timeout assertion passes when timeout is removed and fake exit code 7 is raised. Require the deadline-specific failure and demonstrate bounded real-child termination/cleanup. |

### Review resolution

All patch findings were fixed and covered by 13 fixture tests plus three driver/JDK probes. See [review resolutions](evidence/fix-folders-component-fixtures-20261117/review-resolutions.json). The two verified pre-existing resource-lifetime root causes were recorded in [deferred work](deferred-work.md); the stale old-base dependency claim was rejected against the actual qualified destination. No frozen intent changed.

## Verification

- Use `run-with-temp`; retain logs outside scratch and await children.
- Run fixture/provenance failure tests, audited Release build, complete Server suite and existing source component lane; record inventories and zero skipped/not-run counts.
- Require real Keycloak 26.6.4, identity/cleanup proof, released audit/action checks, exact commitlint and owned-content preservation before pushes. Resume broader publication checks and report independent failures.

### Implementation qualification, 2026-11-17

- [Mainline qualification](evidence/fix-folders-component-fixtures-20261117/qualification.json) uses Folders destination `3ff01eeab6f6dfe7cff83e4ef3e1ff403c50c245`, source patch base `e5760ca105652f4d89c4f240e0ca455723c9a473`, and recorded Platform `8ccb479e391564ce982309f106504cf8329c0a43` with the exact final product overlay. The report records all dependency revisions and changed-file hashes; parent inspection confirmed those hashes match the working bytes.
- Audited Release/package and Debug/source builds passed with zero warnings/errors. Complete prebuilt Server execution passed 1,462 tests, including all eleven real-issuer cases and 23 provenance controls; errors, failures, skips and not-run counts were zero. The source component lane passed all eleven cases with exact SHA-256/MVID bindings for three SDK assemblies.
- Thirteen final fixture tests and three driver/JDK probes passed; the pre-review broader Python run passed 55 tests, covering every matrix row, including missing provider, malformed evidence, native child failure, timeout, private permissions, sanitization, cleanup refusal, and OS-level cleanup failure. Real Keycloak 26.6.4, independent RSA/TLS verification and natural expiry passed; both component runs observed zero remaining containers and private paths.
- The frozen intent and protected CI/CD paths are preserved. Local verification performs no commits, pushes, or remote Git operations. Publication remains conditional on current remote reconciliation and the approved released-policy/complete-product procedure; independent AppHost, FR58 and migration acceptance remain open.

### Final handoff

- Post-review mainline qualification repeated the audited builds, complete 1,462-test Server run, 13 fixture controls and eleven-case Debug/source lane successfully. All unsuccessful counters and observed remaining-resource counts are zero; final destination-file hashes match the working product bytes.
- [Publication preflight](evidence/fix-folders-component-fixtures-20261117/publication-preflight.json) authenticated immutable Builds `v6.0.6` at `fdda17c0a4538b0f7c99f813c20ca24b49006530` and refreshed both module mains. Folders remains `3ff01eeab6f6dfe7cff83e4ef3e1ff403c50c245`; Platform advanced independently to `3f14b712ab24ca6008e718979e944eef26b695e3` in qualification scripts outside this fixture. Both committed trees remain unadopted. Complete approved preparation qualification, dependency publication and consuming-pointer verification remain outstanding; no publication or migration acceptance is claimed.
- No commit was created. The [shared Git instructions](../../references/Hexalith.AI.Tools/hexalith-git-instructions.md) require publishing all pending submodule commits before creating a superproject commit. Incomplete module preparation qualification prevents that publication, so the dependent superproject commit is stopped. Shared indexes, branches and pre-existing work are preserved.
