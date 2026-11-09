---
title: 'Stage 4: environment setup and hook points'
type: feature
created: '2026-11-09'
status: done
baseline_revision: f67efd52ca037d5319bdad60d65397cfc30a6148
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4
implementation_upstream_revision: 32d2a0685663b5b47115b2c0972e4819c9a36b70
review_loop_iteration: 0
followup_review_recommended: false
context:
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/AGENTS.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-llm-instructions.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-git-instructions.md
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Shared CI stops after unit tests. Its classified integration projects and enabled hooks never run, and no shared environment setup exists.

**Approach:** Complete stage 4 in the same CI job: one optional environment setup, after-unit-tests hook, ordered integration projects, after-integration-tests hook. Make the environment composite reusable by Linux prepare in story 2-6.

## Boundaries & Constraints

**Always:** Follow CAP-2/5 and AD-9/11/12/13/14/20. Use the strict config loader and workflow-owned scripts/Props. Environment enables Dapr at the existing single runtime/CLI pins (both already 1.19.1), browsers when configured or an integration project name contains E2E, and registry pull login when configured. Use built Playwright tooling at the module's package version. Hook paths are literal workspace-root `.github/actions/<hook>/action.yml`, with no repeated checkout, restore, build or environment setup. Test projects run in ordinal path order with the existing runner selection and complete-project behavior; any failed step stops all successors. Runtime logic is stdlib Python >=3.12; downloaded binaries require integrity verification and third-party actions full SHA pins. Only the explicit pull-only registry pair may enter the CI job. Keep local stages 1–3 and existing Python APIs compatible.

**Never:** Modify frozen runtime files, including initialize-dotnet, initialize-build, create-release and verify; tests are exempt under AD-20. No legacy rewrite, Windows prepare, nightly hook execution, guard implementation, sample module rollout or release dispatch. No workflow text assertions or module-specific conditions. Commit/push only Builds; stage this story and its gitlink in CiCd.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| No solution | solution none | Stage 1 only | No SDK/environment/hook calls |
| Minimal module | All flags false, hooks empty | Integration projects still run; no environment tools | Preserve test exit code |
| Enabled tools | dapr, browsers, registry true | Each tool setup once before first hook; versions from trusted Builds/tooling | Fail before later work on setup error or missing credentials |
| Browser inference | Classified integration E2E project, browsers false | Install built Playwright browser dependencies | Fail clearly if requested tooling absent |
| Hooks | Both hooks enabled; dormant directories also present | Only fixed enabled hooks run, before/after integration respectively | First hook failure prevents integration and second hook |
| Integration failure | First project has passing and failing tests | Finish all tests in that project; later projects/hook never start | Original nonzero status |
| Unit failure | Unit project fails | No environment, hook or integration work | Existing failure behavior |
| Test overrides | Integration override or exclusion to enabled action | Reuse AD-13 classifier; no duplicate project execution | Reject invalid overrides |

</intent-contract>

## Code Map

Paths are Builds-relative.

- `.github/workflows/ci.yml:27,69` — one read-only job currently ends after `$/Github/ci-unit-tests`; append stage 4 and explicit optional workflow_call registry secrets. `builds-ci.yml` dotnet already calls it; pass named secrets there.
- `Github/lib/ci_pipeline.py:331,358,373,389` — executor, classifier/unit stage, outputs and phase CLI. Reuse MTP/VSTest flags and xUnit completion handling; preserve default all as stages 1–3 for future local check. `ci_config.py` remains sole JSON reader.
- `Github/ci-unit-tests/action.yml` — expose validated successful stage outputs for environment/hook gating. New `Github/ci-environment/action.yml`, `Github/ci-integration-tests/action.yml`, `Github/lib/ci_environment.py` provide stage 4 without calling legacy actions.
- `Props/Directory.Packages.props:32-33` — existing 1.19.1 pins; read from executing Builds tree. Already satisfied; keep unchanged.
- `Github/lib/tests/test_ci_pipeline.py` — fake SDK subprocesses and real SDK controls; extend behavioral coverage, using new environment tests as appropriate. `Tools/ci/run_python_tests.py` automatically discovers them on both interpreters.
- `Tools/ci/{lint_workflows,check_public_api,run_python_tests}.py` and locks — pinned real lint/API/shared suites; `Tools/ci/README.md` documents interfaces.
- Story 2-4 deferred Builds Tooling.IntegrationTests coverage is closed by hosted stage-4 execution. Its other deferred module adoption/performance issues remain outside this story. Sample module and Windows coverage belong to 2-8/2-6.

## Tasks & Acceptance

**Execution:**
- [x] `Github/lib/ci_pipeline.py`, `Github/ci-unit-tests/action.yml`, new `Github/ci-integration-tests/action.yml` — publish validated stage flags/hook gates and execute classified integration projects with existing runner semantics, retaining stages 1–3 entry points.
- [x] New `Github/ci-environment/action.yml` and `Github/lib/ci_environment.py` — one Linux environment composite; trusted Dapr pins, matching built Playwright tooling, explicit registry pull login; optional flags must perform no disabled work.
- [x] `.github/workflows/{ci,builds-ci}.yml` — append ordered same-job environment/hooks/integration, passing only named pull secrets; keep existing legacy lanes and stage-1 slot.
- [x] `Github/lib/tests/test_ci_pipeline.py`, new environment tests — exercise matrix through subprocesses and actual command effects; prove failure boundaries and no repeated restore/build, without workflow text assertions.
- [x] `Tools/ci/README.md` — document environment contract, hooks, runner behavior and later prepare reuse.
- [x] Builds Git and this spec — implementer runs local checks and leaves changes uncommitted for parent review; parent validates exact commit message, commits/pushes Builds and inspects exact-SHA hosted CI; compare frozen blobs; stage CiCd story plus updated gitlink.

**Acceptance Criteria:**
- Given Builds main, when its push CI runs the shared workflow, then Tooling.IntegrationTests executes successfully after units, restoring CI and release-source evidence coverage.
- Given a module with enabled tools/hooks, when shared CI executes, then its hooks observe the existing Release build and prepared environment in the required order, and failure prevents every successor.
- Given the final delivery, when comparing frozen blobs with implementation_baseline_revision, then all remain byte-identical, and only the authorized new pipeline surfaces change.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass

- verdicts: 19 findings — high 0, medium 8, low 7, false 4, maybe-false 0.
- Four context-free layers ran at parent capability. Three launched first; the fourth launched as soon as a concurrency slot freed, before triage. Claims were withheld from the code diff and supplied only to the edge reviewer.
- findings, in reporting order:
  - `[medium]` `[patch]` Edge E1: a complete Playwright output masks another version's missing script — parent reproduced successful partial installation. Any discovered script/library/package artifact now requires the full contained output; mixed-output regressions cover each missing component.
  - `[medium]` `[patch]` Edge E2: successful output disappears before the secrecy assertion — the harness returned empty strings. It now aggregates stdout/stderr across nested composites; a deliberately printed password is detected.
  - `[medium]` `[patch]` Edge E3: composite GITHUB_PATH effects are lost — copied environments confined the installed CLI path. Harness path effects now propagate across steps; an enabled-Dapr hook executes the installed controlled CLI.
  - `[medium]` `[patch]` Gap G1: registry secrecy assertion discards its evidence — pre-verified password-print mutation survived. Shares E2's output aggregation and deliberate-print regression.
  - `[medium]` `[patch]` Gap G2: removing Dapr forwarding passes the harness — pre-verified missing boundary coverage. A controlled verified archive now traverses the actual workflow/composite and subsequent hook; a dropped-forwarding mutation fails.
  - `[low]` `[patch]` Gap G3: distinct browser versions can collapse undetected — pre-verified single-key mutation survived. Two versions, repeated outputs and inner target frameworks now prove exactly one install per required version.
  - `[false]` `[reject]` Intent I1: old module callers are not exercised — the explicit freeze requires their preservation; additive shared CI is the selected story surface. All 59 frozen blobs were independently compared.
  - `[false]` `[reject]` Intent I2: the harness supplies external checkout/SDK actions — this correctly describes the test layer and alleges no behavioral discrepancy. It is not claimed as hosted-run evidence; actual hosted verification is a separate finalization check.
  - `[low]` `[patch]` Intent I3: optional service tests do not establish live setup — true evidence limit. Parent adds a temporary hosted runtime probe for real Dapr health, browser execution and registry login, removed before final delivery; result recorded below.
  - `[false]` `[reject]` Intent I4: real SDK tests cover executor behavior rather than hosted services — that is their intended layer. They prove runner selection and complete-project behavior; the separate harness and hosted probe cover the other boundaries.
  - `[false]` `[reject]` Intent I5: a content diff cannot establish commit/push/hosted delivery — delivery is explicitly authorized and follows review. Final commit, push, clean-tree, frozen-blob and exact-SHA evidence are recorded in Auto Run Result.
  - `[medium]` `[patch]` Blind B1: a hook can change configuration to solution none and silently bypass integration — parent reproduced a successful job with units only. Internal successful-unit state now binds the validated document, runner and classification; changes fail before integration. Tests cover solution-none, config, runner and project removal.
  - `[low]` `[reject]` Blind B2: Dapr setup lacks legacy partial-install cleanup/port retries — an existing runtime can indeed make init fail, but this stage runs once on a fresh hosted runner. Retrying a preexisting installation is unlikely in normal use and adds recovery/cleanup behavior; clear failure is retained.
  - `[medium]` `[patch]` Blind B3: nested PATH effects differ from GitHub — duplicates E3's verified harness defect and repair.
  - `[medium]` `[patch]` Blind B4: successful logs vanish and hide leaked passwords — duplicates E2/G1's verified defect and repair.
  - `[low]` `[patch]` Blind B5: synthetic Dapr archive does not prove usable live runtime — shares I3's hosted smoke verification rather than claiming synthetic evidence is live.
  - `[low]` `[patch]` Blind B6: browser tests omit distinct versions and cross-targeting — shares G3's expanded version/framework fixtures.
  - `[low]` `[patch]` Blind B7: Dapr, registry and final-hook failure paths are unverified — added actual-action cases preserve each exit status and suppress all applicable successors.
  - `[low]` `[patch]` Blind B8: containment and unknown-digest rejections lack controls — added outside-output, escaping script/library/package symlinks, incomplete tooling and unsupported-pin negatives; no affected tool executes.
- Grouped entries: five medium patches (incomplete browser output, harness stdout/stderr, harness PATH, Dapr forwarding coverage, post-unit state), four low patches (browser matrix, live smoke evidence, additional failure boundaries, containment/pin controls). Fourteen finding rows patched; five rows rejected; zero deferred; no intent gap or bad-spec loopback.
- Parent patch verification caught invalid job-level runner.temp context in B1's initial repair. The state path now appears only on the unit/integration steps, where the context is valid; real actionlint and online zizmor pass. No blanket lint suppression was added.

## Design Notes

Environment and hook controls are outputs of successful validated classification, not a second JSON interpretation in YAML. Browser tooling comes from evaluated build outputs so downloads match the module's Playwright version. Hooks always resolve from workspace root even with test-only module-root. The environment composite is independently reusable; Linux prepare can invoke it after its own build. Official Dapr init and Playwright .NET browser documentation confirm versioned init and built `playwright.ps1 install --with-deps` semantics.

## Implementation Notes

- Final-SHA hosted shared CI job 129312688454 succeeded: Evidence 191 passed; Module 2933 passed and 5 existing skips; Tooling.IntegrationTests one passed and 12 existing live-gate skips. Logs show units, environment setup, then integration in the same job; no rebuild occurs between stages. Log: `/tmp/story-2-5-hosted-dotnet.log`.
- Final-SHA hosted Python jobs 129312688769 (3.12.16) and 129312688835 (3.14.4) each report 20/20 groups and all 71 lib tests. Quality job 129312688604 reports 12 exact frozen findings/zero new findings and 2488 compatible API entries at `5ec1779040606be89306129a7d2b245258c9acd2`. Logs: `/tmp/story-2-5-hosted-python312.log`, `/tmp/story-2-5-hosted-python-runner.log`, `/tmp/story-2-5-hosted-quality.log`.

- Live optional setup is proven by [hosted probe 42660703892](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42660703892), successful at `78682df11bb4491c5995d0f5bc2626993ff7674b`. Logs show CLI/runtime 1.19.1, successful registry login, a healthy real Dapr sidecar, real Chromium DOM output, and both hooks. Log: `/tmp/story-2-5-hosted-probe.log`. This closes I3/B5's live evidence limitation.
- Cleanup commit `5ec1779040606be89306129a7d2b245258c9acd2` removes both temporary probe files and is pushed. Both exact stored commit messages equal their pinned-commitlint-validated files. Final committed API check passes 2488 entries; all 59 frozen blobs still match the preserved upstream. Net story implementation is ten files. Exact-SHA CI 42661065183 and Commitlint 42661064674 both completed successfully.

- Concurrent upstream commit `32d2a0685663b5b47115b2c0972e4819c9a36b70` changed create-release README/action/proxy and its tests while this run was working. Parent inspected the full diff, preserved it and rebased this story without conflicts. The original baseline remains recorded above; the story's own frozen-file delta is measured against this preserved upstream. **All 59 frozen blobs match that upstream**, and this story changes none. The external three runtime-file changes are not attributed to this story or reverted.
- Implementation commit `76b87e3ce055a05302872bd84e10d4ff431b0d8e` rebased to `78682df11bb4491c5995d0f5bc2626993ff7674b`, then pushed successfully. Exact commit message passed pinned commitlint with zero problems/warnings. Rebased online lint passed; committed API has 2488 compatible entries against v4.46.0; upstream create-release's eight tests passed. Probe files are temporary and will be removed by another validated commit.

- Post-review parent checks passed all **71 lib tests on both Python 3.12 and 3.14.4**. The exact step-scoped state-path wiring then passed another focused environment run on both interpreters. Online actionlint/zizmor, including the temporary probe, passes with zero new findings. Tests include mutation controls for dropped Dapr forwarding, successful password output, and premature second-hook execution.

- Parent full locked suites: **20/20 groups passed on Python 3.12 and Python 3.14.4**, including all 64 lib tests and 46 quality-helper tests. Logs: `/tmp/story-2-5-python312-auth.log`, `/tmp/story-2-5-python314.log`. Matrix audit: no-solution, optional tools, inference, hooks/order/failure, integration project completion, unit failure, overrides/exclusions each have executed passing tests. The initially started no-token full run was interrupted and replaced with these authenticated complete runs.

- One new environment composite and stdlib helper read the executing Builds Dapr pins, verify the official CLI archive, locate built Playwright tooling by evaluated output, and pass registry passwords through stdin. Fixed local hooks and integration execution extend the existing read-only CI job. Default local `all` still covers stages 1–3.
- The implementer passed 33 pipeline and 13 environment tests on Python 3.14.4. Parent independently passed all 13 environment tests on Python 3.12 after strengthening the second hook's completed-integration assertion; a reordered-hook mutation was rejected.
- Parent online actionlint/zizmor passed: 12 exact frozen composite findings, zero new findings. All 59 frozen runtime blobs match the starting revision, including initialize-dotnet, initialize-build, create-release and verify. Props are unchanged; both Dapr pins were already 1.19.1.
- GitHub's official Dapr 1.19.1 asset metadata independently confirms SHA256 `6e9a339d261e430e5914909cc4443572573c197c174c3e14504c34116831de3b` for `dapr_linux_amd64.tar.gz`.
- Real local integration stage passed: Tooling.IntegrationTests ran 13 tests, one succeeded and 12 existing opt-in live tests skipped. Those skips are not live Dapr evidence.
- Baseline API check passed against v4.46.0 (`a8a87160f2708322d5520742b9a0c3f93d23db78`), 2480 entries. The final committed revision will be checked separately because this checker reads Git objects.

## Verification

Run focused lib tests on Python 3.12 and runner Python, full locked script suites as warranted, pinned online actionlint/zizmor and API check, and real local Builds integration stage. Use meaningful command doubles for optional setup/failure/secrets and real SDK coverage for per-project execution. Inspect hosted exact-SHA push CI to confirm integration execution. Exercise actual hook/environment action boundaries via a disposable behavioral harness or temporary hosted probe when needed; remove temporary probe surfaces before final delivery. Run whitespace and full frozen-blob comparison, pinned commitlint validation, fetch/inspect divergence and push Builds main. Never dispatch release.

## Auto Run Result

Status: **done**. Implementation is reviewed, committed and pushed; exact-final-revision hosted CI passed.

- Completed stage 4 in the existing CI job: one optional Dapr/browser/registry setup, after-unit-tests hook, ordinal integration projects, after-integration-tests hook. Unit and integration failures finish the failing project and stop successors. Configuration, runner and classification changes after units fail before integration. Default local `all` remains stages 1–3.
- Net changed files (Builds-relative):
  - `.github/workflows/ci.yml`: ordered stage 4, explicit optional pull secrets, internal per-stage state path.
  - `.github/workflows/builds-ci.yml`: passes the named org pull secrets to shared CI.
  - `Github/ci-environment/action.yml`: reusable Linux environment interface.
  - `Github/ci-integration-tests/action.yml`: integration entrypoint.
  - `Github/ci-unit-tests/action.yml`: successful validated environment/hook outputs.
  - `Github/lib/ci_environment.py`: trusted pin/integrity checks, built Playwright version selection and pull-only login.
  - `Github/lib/ci_pipeline.py`: shared executor, integration phase and post-unit input/state comparison.
  - `Github/lib/tests/test_ci_environment.py`: executable workflow/composite harness, optional-tool effects, ordering, failure and negative controls.
  - `Github/lib/tests/test_ci_pipeline.py`: integration ordering/completion, stage outputs and real MTP/VSTest controls.
  - `Tools/ci/README.md`: runtime interfaces, guarantees and verification.
- Delivery commits on Builds main: `78682df11bb4491c5995d0f5bc2626993ff7674b` (implementation and temporary live probe), `5ec1779040606be89306129a7d2b245258c9acd2` (remove successful probe). Both exact full messages passed pinned commitlint. Both probe files are absent from the final tree. No release was dispatched.
- Review: 19 findings, 14 patched rows across five medium and four low entries; five rejected rows; zero deferred. Rejected: four descriptive intent/evidence-layer observations do not identify code deviations, and preexisting Dapr installation recovery is unlikely on the fresh single-setup runner and would add cleanup/retry complexity. Individual evidence/refutations are in Review Triage Log.
- Follow-up review recommendation: false. Five medium entries were repaired, but no specific unverified implementation risk remains after both-interpreter behavioral/mutation controls, the real optional-runtime probe and final hosted validation. The live probe closes the risk the unit doubles could not settle.
- Parent verification: initial full locked Python suites **20/20 groups on both interpreters**; post-review **71/71 lib tests on 3.12 and 3.14.4**, then **20/20 environment tests on each** after final step-scoped state wiring; real local integration project **one passed, twelve existing opt-in live tests skipped**; online actionlint/zizmor **zero new findings**; final committed API **2488 entries, no removals**; whitespace checks pass. The concurrent upstream release tests also passed 8/8.
- Real hosted optional setup: [probe 42660703892](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42660703892) succeeded, with Dapr CLI/runtime 1.19.1, healthy sidecar, Chromium DOM execution, registry login and both hooks. This is live evidence; the synthetic archive and command-double controls are not claimed as live services.
- Frozen-file evidence: this story's commits change no frozen runtime blob; all 59 match preserved upstream `32d2a0685663b5b47115b2c0972e4819c9a36b70`, including all four named composites. That concurrent commit changed create-release's README/action/proxy and tests relative to the original starting revision; it was preserved and inspected, never reverted or attributed to this story. Raw original-baseline differences include those three external runtime files, so a blanket original-tree byte-identity claim would be inaccurate.
- Residual limits: existing opt-in G-4 live tests retain their own skips unless their separate live gate is enabled. Module adoption and cross-repository `$/` consumer verification remain later-story work, unchanged from story 2-4. No known stage-4 defect or deferred work remains.

- Final hosted result: [CI 42661065183](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42661065183) **completed/success**, all eight jobs successful, at `5ec1779040606be89306129a7d2b245258c9acd2`. [Commitlint 42661064674](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42661064674) also completed/success at the same revision. Machine-readable evidence: `/tmp/story-2-5-hosted-final.json`, `/tmp/story-2-5-hosted-commitlint.json`.
- Final repository check: Builds HEAD and fetched origin/main both equal `5ec1779040606be89306129a7d2b245258c9acd2`; the owning working copy and both whitespace checks are clean. All reviewed implementation files are committed, temporary probe files are absent, and no required work remains. CiCd stages only this story record and the updated Builds gitlink, following the submodule-story rule; no CiCd commit or push was made.
