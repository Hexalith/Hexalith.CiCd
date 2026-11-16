# Local implementation result

This document records the initial local preparation stage. Later publication
of that preparation as work in progress is recorded in
[publication.md](publication.md) and the authoritative
[workspace-publication.json](workspace-publication.json). The
[resumed local assessment](resumed-implementation.md) keeps publication
separate from the still-incomplete implementation and adoption acceptance.

The authorized local preparation stage is complete. Memories is **not
registered or adopted**, and story acceptance remains incomplete. No GitHub
API calls, remote repository operations, pushes, delivery, settings changes or
credential revocation were performed. Public dependency feeds were used for
normal restore and integrity-checked commit validation.

The reviewable product checkout is
`/home/administrator/projects/hexalith/memories-story-22`, branch
`story/22-product-preparation`. The original module and primary CiCd checkouts
were preserved. `local-candidate.json` and the verified 85,653-byte
`memories-product-preparation.bundle` preserve the complete local change.

| Revision | Meaning |
| --- | --- |
| `c64e292a46858058f6764095c8e01c2faa0ff3e0` | Previously fetched Memories main; no newer remote-main claim. |
| `a27d242acf11dbb4cee2f4f9cab92637608b5c0b` | Broadly verified product/code candidate. |
| `74770c1b539d30206403e8549ac5da0aa629f295` | Final code candidate after removing remaining CI/story/formatting gates; affected Server project requalified. |
| `22723f99ed8a3f0abe306a4634836737be7f838d` | Final local revision; only three documentation files differ from the final tested code candidate. |

`documentation-follow-up.json` and its exact gzip-compressed patch prove the final step changes
only `CONTRIBUTING.md`, `tests/README.md` and `docs/dev/release-runbook.md`.
Every local commit passed the pinned shared commitlint before and after commit,
including locked npm installation and signature verification.

## Product preparation

The change extracts the two genuine C# packaging/container guards, removes
module CI/story/agent/YAML gates and obsolete root release tooling, preserves
mixed publishing/recovery/authorization assertions, removes NU1901-NU1904
non-fatal audit overrides while retaining audit mode `all`, and makes Playwright
consume the prepared Release host without rebuilding.

Fast and slow/performance cases now have separate complete projects. The
nightly project links only shared fixture/helper sources and its own scenario
partials. Friend-assembly declarations support its existing internal seams.
DerivedStores owns its source once and has a ninth required unit coverage
report; the 76.5% threshold and production scope are unchanged. Both local
entrypoints route fast, slow, performance, exact integration and benchmark
requests to the correct explicit projects using SDK 11's `--project` form.

`gate-cleanup.md` documents every classification, including the later removal
of IntegrationStubClosureGuardTests, integration-result inventory verification
and formatting-policy qualification. Its mixed operator runbook citation still
names the same retained graph-isolation product scenario.

## Completed local verification

At `a27d242acf11dbb4cee2f4f9cab92637608b5c0b`:

- Full Release/package solution compilation: **0 warnings, 0 errors**. This
  uses the shared CI `NuGetAudit=false` compilation contract.
- Separate Release restore with `NuGetAudit=true`, audit mode `all` and warnings
  as errors: **pass**. CI compilation is not presented as audit evidence.
- All nine complete unit projects: **5,302 total, 5,301 passed, 0 failed,
  1 skipped**. No trait filter or new skip was used.
- Independent Python suites: **449 passed, 0 failed, 0 skipped** — coverage 26,
  dispatch 11, preflight 50, retained publication qualification 24,
  publisher/recovery 176, functional-retention 162.

At final code `74770c1b539d30206403e8549ac5da0aa629f295`, only the affected
complete Server project was repeated after the final policy cleanup:
**3,181 total, 3,180 passed, 0 failed, 1 skipped**, with clean Release/package
compilation and independent enabled release audit. The count decreases by the
12 removed CI/story scanner cases. Unrelated passing suites were not repeated.

The unchanged baseline skip is
`SubmoduleGuardTests.CheckSubmodulesTarget_FailsBuildWhenSubmoduleGitMarkerIsMissing`.
Its existing `RunnableSkippedFact` is disabled by default because it renames a
submodule `.git` marker and invokes MSBuild against a workspace. The existing
opt-in is `HEXALITH_RUN_SKIPPED_TESTS=true/1`; this migration did not add or change
the skip. It grants no complete-matrix acceptance.

Additional independent checks passed:

- All **14** controlled Bash/PowerShell project-routing cases and child-failure
  propagation, with nine report obligations at 76.5% (`local-routing.json`).
- Changed PG2 disposable-source fixture setup, without root Node tooling;
  this is fixture-only evidence and grants no profile/authorization credit.
- Integration source method body/attribute preservation: 478 original source
  methods, one explicitly classified CI trait-selection assertion removed,
  **all 477 product methods unchanged**, including every OpenBao scenario.
- Git-object byte/mode/gitlink equality for owned content, foreign instructions
  and settings, all direct gitlinks, SDK, formatting attributes, ten-package and
  five-image inventories and the browser workspace manifests/lock.
- Local bundle integrity and a clean final product worktree.

The ordinary source-preserving line-ending normalization in the method proof is
explicit; it is not a runtime execution claim. Raw Git objects supply the
ownership/output preservation proof.

## Blocked and unexecuted acceptance

`telemetry-prerequisite.log` reproduces the existing profile refusal:
`FAIL: current-input: deploy/kubernetes/overlays/production/access-telemetry-disabled-patch.yaml`.
`telemetry-prerequisite-blocker.json` proves both baseline and candidate input
bytes have the same SHA-256, differing from the retained approval's hash.
The repeating profile-dependent C1 diagnostic was stopped after diagnosis and
its process group was terminated/waited before cleanup; it is **blocked and
incomplete**, never reported as a passing suite. The complete changed runtime
identity and PG2 capture suites remain unexecuted because of that prerequisite;
only PG2's independent changed fixture setup was separately verified. Approval
hashes and Production overlays remain untouched.

Separate released shared source/composition, npm browser, coverage collection,
SQL and prepared rollout OCI/tool support remain prerequisites. The real fast
and nightly integration projects, all 17 benchmark cases, browser/accessibility
runtime, live SQL contract, real rollout/recovery and complete Debug/source
catalog qualification were not executed without their prepared environment.
The local coverage contract/report ownership was checked; a new measured
76.5% coverage result and the full pre-push package/consumer procedure remain
outstanding. No hook-side setup/rebuild or unsupported registry key was added.

Hook authoring, registration/render with a remotely available product commit,
committed-candidate Memories validation, maintainer preconditions, authenticated
App adoption, foreign-content readback, immediate scoped credential cleanup,
green adopted CI and the next scheduled central nightly outcome are all still
required. `prerequisite-handoff.md` provides the concrete separate handoff and
AD-21 sequence. Unmet story tasks remain unchecked.

All local verification jobs have finished. Disposable checkouts and child work
were cleaned up; the requested logs, proof artifacts and persistent product
checkout remain available for review.
