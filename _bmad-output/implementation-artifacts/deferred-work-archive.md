### DW-2: Builds' own CI no longer runs Hexalith.Builds.Tooling.IntegrationTests until stage 4 executes integration projects.
origin: spec-deferred b8b8df1d842a
location: .github/workflows/builds-ci.yml dotnet job; test/Hexalith.Builds.Tooling.IntegrationTests
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
reason: The replaced inline dotnet job ran the project explicitly. AD-13 now classifies it as integration (hosted run 42622137434 lists it under "integration"), and this story's intent forbids stage 4 execution. Its only ungated test, ToolAssembliesHaveIndependentEntryPoints, is unrun meanwhile; live tests skip without LiveGate. Story 2-5 implements integration execution and should confirm this project runs there.
status: done 2026-11-23
archived: 2026-11-23
resolution: Builds main push `5ec1779040606be89306129a7d2b245258c9acd2` ran `builds-ci.yml` and its local reusable `ci.yml`. Stage 4 ran Hexalith.Builds.Tooling.IntegrationTests after the unit tests and environment setup in the same job. Its ungated `ToolAssembliesHaveIndependentEntryPoints` passed and 12 opt-in live cases skipped. The run completed successfully. [Story 2-5](../specs/spec-cicd/stories/2-5-stage-4-environment-setup-and-hook-points.md) · [CI 42661065183, job 129312688454](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42661065183/job/129312688454)

### DW-5: Builds releases also stop exercising Hexalith.Builds.Tooling.IntegrationTests until stage 4 runs integration projects.
origin: spec-deferred 6b2e087c4a3b
location: .github/workflows/builds-release.yml; Tools/G4PackageQualification.functions.ps1
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
reason: builds-release.yml passes HEXALITH_G4_SOURCE_CI_RUN_ID. Get-VerifiedSourceCiRun (Tools/G4PackageQualification.functions.ps1) accepts the exact-SHA push run of builds-ci.yml as the source-test evidence. Since this story, that run classifies Tooling.IntegrationTests as integration and does not execute it. This is the same root cause as the deferred Builds CI coverage item. Story 2-5 should confirm the project runs in stage 4 for both CI and release evidence.
status: done 2026-11-23
archived: 2026-11-23
resolution: At Builds `5ec1779040606be89306129a7d2b245258c9acd2`, the hosted Release job logged `HEXALITH_G4_SOURCE_CI_RUN_ID=42661065183`. That main push CI ran the DW-2 integration project (1 passed, 12 live cases skipped). At this revision, `builds-release.yml` checks the live branch tip before and after approval. `verify-g4-release-source.sh` selects the highest successful run ID among completed `builds-ci.yml` pushes for the exact branch and SHA. The workflow passes `approved_source.outputs.ci-run-id` to the release step. In the verifier source, `Get-VerifiedSourceCiRun` checks the ID, repository, workflow, branch, SHA, event, status, conclusion and URL and requires a positive attempt number. Qualification rechecks the recorded attempt before publication. The published v4.47.0 evidence ZIP (SHA-256 `16e379d3e1d2312a9c998d633c2311e627dd195711b7ae26a4e1a514e52e22fa`) contains `g4-tool-package-inventory.json`. Its `qualification.sourceValidation.ciRun` records run `42661065183`, attempt 1, workflow `.github/workflows/builds-ci.yml` and branch `main`. [Qualification evidence ZIP](https://github.com/Hexalith/Hexalith.Builds/releases/download/v4.47.0/g4-tool-qualification-evidence.zip) · [Release 42664680297, job 129325132481](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42664680297/job/129325132481) · [CI job 129312688454](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42661065183/job/129312688454) · [Source selector](https://github.com/Hexalith/Hexalith.Builds/blob/5ec1779040606be89306129a7d2b245258c9acd2/Tools/verify-g4-release-source.sh) · [Verifier](https://github.com/Hexalith/Hexalith.Builds/blob/5ec1779040606be89306129a7d2b245258c9acd2/Tools/G4PackageQualification.functions.ps1)

### DW-6: Cross-repository resolution of $/ in the reusable ci.yml has not been exercised by any hosted run.
origin: spec-deferred 04af84c349a0
location: .github/workflows/ci.yml:54
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: medium
reason: The hosted probe (run 42615634829) and Builds' own calls are same-repository, so the caller and workflow commits coincide. Whether a module's cross-repository workflow_call resolves $/Github/ci-* to Hexalith.Builds at job.workflow_sha is documented but unverified. If it does not, every consumer's CI fails at preparation. Settle with the first module's hosted call of Hexalith/Hexalith.Builds/.github/workflows/ci.yml; if it fails, apply AD-9's pinned own-code checkout. (declared severity: medium (unverified))
status: done 2026-11-23
archived: 2026-11-23
resolution: The Commons main push at `5169f6b6165482d4b1499ccc5958eb897101be4f` called `Hexalith/Hexalith.Builds/.github/workflows/ci.yml@v6.0.6`. Its `ci / Build and tests` job succeeded. The called tag peels to `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Its workflow used `$/Github/guard`, `ci-prepare`, `ci-build`, `ci-unit-tests`, `ci-environment` and `ci-integration-tests` under the same `$/Github/` prefix. All six action manifests exist there. The Commons caller tree has no root `Github/` directory. Its package consumer hook ran from the module checkout, and the separate restore job skipped. [Caller](https://github.com/Hexalith/Hexalith.Commons/blob/5169f6b6165482d4b1499ccc5958eb897101be4f/.github/workflows/ci.yml) · [Called workflow](https://github.com/Hexalith/Hexalith.Builds/blob/fdda17c0a4538b0f7c99f813c20ca24b49006530/.github/workflows/ci.yml) · [Run 43864267698, job 133288671894](https://github.com/Hexalith/Hexalith.Commons/actions/runs/43864267698/job/133288671894) · [Story 11 receipt](../specs/spec-cicd/evidence/11/adopted-main-ci-proof.json)

### DW-34: The delivery barrier's sequential per-status scans can miss a `deliver.yml` run that moves into `waiting` between two status queries.
origin: spec-deferred fda010c8a0b1
location: tools/nightly.py:214
source_spec: `8-1-nightly-releases.md`
severity: medium
reason: `delivery_barrier` queries `requested`, `waiting`, `pending`, `queued` and `in_progress` one after another. A run that moves queued→waiting or in_progress→waiting after the `waiting` query and before the later query appears in no inventory, so the barrier can clear while delivery is still active (medium if true). Only deployment protection on the run's environment produces `waiting`. To settle it, check whether `cicd-app` protection rules can hold a main deliver run in `waiting`, or require two consecutive clear scans. (declared severity: medium (unverified))
status: done 2026-11-23
archived: 2026-11-23
resolution: Dispatch requires two complete idle scans separated by the existing 60-second poll. An active run, short page or changing page total resets the count. Both observations must finish inside the 30-minute limit and dispatch reserve. Controlled-clock tests cover queued and in-progress runs moving to waiting mid-scan, recovery after page drift, a busy run between idle scans, a late response and insufficient time for confirmation. The nightly controller suite passed 48 tests and the workflow suite passed 30.

### DW-38: Complete current App selected-repository membership remains unverified.
origin: spec-deferred 4ec62ad298c1
location: docs/cicd-app-inventory.md
source_spec: `30-1-verify-the-cicd-app-workflow-inventory.md`
severity: medium
reason: Read-only maintainer GET user/installations/179966090/repositories returned HTTP 403 with request identity and response digest retained in evidence/30-1/hosted-readback-20261122.json. Installation grants and the environment client-ID binding were readable; neither proves the full selected-repository set. A reader authorized for installation repository enumeration is needed. Preserve story 11's accepted open Hexalith.Docs exception.
status: done 2026-11-22
archived: 2026-11-23
resolution: Story 30-3 verified `repository_selection: all` on the active installation and records the approved AD-7 change. The historical selected-list refusal and story 11's earlier Hexalith.Docs exception remain in their receipts. [Story 30-3](../specs/spec-cicd/stories/30-3-reconcile-organization-wide-cicd-app-access.md)

### DW-41: The relocated EventStore verifier suite is not discovered by the CiCd tool-suite gate.
origin: spec-deferred 20f3d4904c68
location: tools/check_global.py:401
source_spec: `28-3-executable-fixtures-out-of-evidence.md`
severity: medium
reason: check_global.run_tool_tests globs only tools/tests/test_*.py, so tools/qualification/pre-adoption/eventstore/test_pre_adoption_verify.py (17 tests) runs only when invoked by hand. Pre-existing: the suite was equally undiscovered under evidence/20. It needs jsonschema and Builds release fdda17c0a4538b0f7c99f813c20ca24b49006530 objects at references/Hexalith.Builds, so gate wiring needs a prerequisite decision.
status: done 2026-11-23
archived: 2026-11-23
resolution: Full validation runs the relocated suite once with the gate’s locked Python environment. All 17 tests passed against the original loader and schema blobs from fdda17c0a4538b0f7c99f813c20ca24b49006530 with a replacement ref, signing configuration and inherited repository/index settings in disposable repositories. The 77 validation tests passed, including a real suite run that failed the gate when the selected Builds repository lacked the release.

### DW-43: The Parties publication runner's exact-input checks are bare asserts that python3 -O removes.
origin: spec-deferred ef40bb6bea8b
location: tools/qualification/pre-adoption/parties/qualify-push.py:32
source_spec: `28-3-executable-fixtures-out-of-evidence.md`
severity: medium
reason: tools/qualification/pre-adoption/parties/qualify-push.py checks HEAD and origin, patch identity, dependency pins, untracked source bytes and modes and the expected tree with assert; under -O they vanish and the record reports result pass. Pre-existing and unchanged by the path-only relocation, which forbids logic changes; other repository procedures use run-with-temp python3 -O -B, so the pattern can be copied.
status: done 2026-11-23
archived: 2026-11-23
resolution: The Parties qualifier enforces each source, patch, pin, hash, mode, tree and commit-message check under both Python modes. The two relocation tests passed. Normal Python and python -O raised the expected refusal and wrote matching failed receipts for each mismatched source, dependency pin, staged tree and owning commitlint rejection. Both modes passed the controlled preparation with both commit messages verified.
