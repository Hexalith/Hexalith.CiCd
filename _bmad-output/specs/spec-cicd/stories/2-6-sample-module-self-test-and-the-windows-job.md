---
title: Sample module self-test and the Windows job
type: feature
created: '2026-11-09'
status: blocked
baseline_revision: 418bb7e97fea73145425c40b881b73b77695df3a
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 5ec1779040606be89306129a7d2b245258c9acd2
review_loop_iteration: 0
followup_review_recommended: true
context:
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/AGENTS.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-llm-instructions.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-git-instructions.md
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Builds tests its own products through shared CI but has no sample consumer proving module MSBuild imports, hooks, or the Windows job contract. Regressions in those surfaces can pass CI.

**Approach:** Add a real sample module, call reusable CI against it, and run a Windows job using validated outputs through a new prepare composite. Provide the delivered-tree fixture for the later guard and reuse existing Linux setup.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds`. Follow CAP-5/15 and AD-2/9/11/12/13/14/19/20. Preserve all frozen runtime bytes, including initialize-dotnet, initialize-build, create-release, verify, legacy workflows and existing Samples templates; tests are not frozen. New runtime logic goes in new files. Preserve legacy CI lanes and stage-1 slot. Runtime Python is stdlib only, >=3.12. Windows prepare performs checkout, SDK setup, direct submodule initialization, restore and Release package build without Python, module JSON reading, tests/hooks or environment setup. Linux prepare uses the sole loader and existing environment composite after one build. Scripts resolve from GITHUB_ACTION_PATH, never the module gitlink. Checkouts have no persisted credentials or recursive initialization. Root sample composites run existing built product tests, never rebuild/setup/call Builds or write evidence. Only sample config enables them. Parent reviews, commits/pushes Builds and verifies exact-SHA hosted CI; stages story plus gitlink in CiCd without superproject commit.

**Never:** Change frozen runtime, dispatch a release, initialize nested submodules, add module conditions to shared runtime, assert workflow text, duplicate a config reader, implement the later guard/perimeter library, or claim its reserved slot exercises enforcement.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Sample | Complete config, central imports, real projects | Build once, units then enabled root hook and integration; Windows-only project runs in its job | Any product failure fails CI |
| Windows prepare | Validated solution, SDK file, direct submodules | Checkout, selective init, exact SDK setup, one restore/build with shared mandatory flags; no environment or Python/JSON | Preserve failure status; no successors |
| Nested paths | Sample prefix, nested solution, spaces | SDK/cwd remain global.json directory; argument arrays preserve paths | Invalid/escaping/non-gitlink inputs fail before product commands |
| Linux prepare | Complete config, optional environment knobs | Same loader/build flags/classifier; one existing environment setup; no tests/hooks | Invalid config/build fails before setup |
| No solution | solution none | No SDK/build/environment/tests/hooks | Linux configuration still validates |
| Regression controls | Failing sample product/hook or prepare command | Failure reaches execution boundary; no successors | Retain nonzero |

</intent-contract>

## Code Map

Paths are Builds-relative. Read-only exploration completed by subagent and parent.

- `.github/workflows/ci.yml:19,42`, `Github/ci-prepare/action.yml`, `Github/lib/ci_pipeline.py:115,416`: validated prefixed solution/submodules/global-json already exist internally. Add workflow global-json output for exact SDK/cwd; preserve existing solution/submodules outputs. prepare_config rejects test-only inputs outside Builds; expected-source currently validates directory existence only.
- `.github/workflows/builds-ci.yml:24,43`: dotnet reusable call and retained aggregator. Add sample call and dependent two-step Windows job; include both verdicts. Own config enables no sample hooks/jobs.
- New `Samples/Hexalith.Sample/`: own global.json, slnx, root build/package wrappers, README, small product and central-versioned xUnit projects for unit/integration/hook/Windows. Import `../../Hexalith.Build.props`, `../../Props/Directory.Packages.props`, and central package props from product; set ProjectRoot after import. Modules import these same files. Do not import existing Samples templates directly (wrong MSBuildThisFileDirectory) or Builds root repository props. No nested Builds checkout.
- New sample expected-source directory laid out as delivered tree: `rendered/Hexalith.Sample/...` and `rendered/Hexalith.Sample.perimeter.json`; supply owned sample config now, reserve perimeter schema integration for owning story. Config requires exact buildsTag and every knob including submodules. tests.exclude delegates hook/Windows projects to enabled actions rather than running twice.
- New `.github/actions/{after-unit-tests,sample-windows}/action.yml`: execute built sample tests with proper MTP semantics, without generic setup or evidence artifacts.
- New `Github/prepare/action.yml` and scripts: Windows solution/submodules/global-json inputs, Linux test-only module-root input as needed; expressions only through env. Actions expressions decode submodule JSON to LF-delimited paths; Windows splits LF and reads no JSON. Valid config paths forbid LF. global-json defaults to global.json; workflow passes validated SDK path instead of guessing from solution directory.
- `Github/lib/ci_pipeline.py` build_flags/prepare_config/restore_and_build/classified_projects; `Github/ci-environment/action.yml` and ci_environment.py provide Linux reuse. Browser inference includes classified E2E.
- `Github/lib/tests/test_ci_environment.py:33` executable CompositeHarness and test_ci_pipeline.py real SDK fixtures; extend/add prepare tests using actual PowerShell execution and command effects. Harness currently assumes bash/skips external actions; supply controls and distinguish them from hosted evidence.
- `Tools/ci/{run_python_tests,lint_workflows,check_public_api}.py`: locked suite discovers Github/*/tests; extend lint to root sample composites. `Tools/ci/README.md` documents interfaces. package.json/lock pin commitlint 21.2.4.

## Tasks & Acceptance

**Execution:**
- [x] `Samples/Hexalith.Sample/**` — runnable consumer, complete config and expected-tree fixture, central imports and product tests.
- [x] `.github/actions/{after-unit-tests,sample-windows}/action.yml` — run built delegated tests under custom-action contract.
- [x] `Github/prepare/**` and relevant new Linux helper — both OS contracts, shared flags/trust, exact SDK/cwd, selective submodules and failure handling.
- [x] `.github/workflows/{ci,builds-ci}.yml` — SDK output, second call, two-step Windows job on sample outputs and aggregate verdicts; preserve legacy lanes.
- [x] `Github/*/tests`, `Tools/ci/lint_workflows.py`, `Tools/ci/README.md` — behavioral matrix coverage, root-action lint coverage and interfaces.
- [ ] Parent Git/spec — independent verification/review, frozen comparison, pinned commitlint, commit/push Builds, exact-SHA hosted sample/Windows evidence; stage CiCd story/gitlink.

**Acceptance Criteria:**
- Given Builds main, when builds-ci.yml runs, then shared CI runs against both Builds and sample, and sample Linux plus dependent Windows jobs pass.
- Given a Builds change breaking sample imports, product tests or hooks, when Builds CI runs, then the run fails at that consumer surface.
- Given a module Windows job, when prepare receives shared CI outputs, then its local action observes restored Release outputs from the same SDK/flags without JSON parsing or environment setup.
- Given the implementation baseline, when final delta is inspected, then every frozen runtime blob remains unchanged, including four named composites.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass

- verdicts: 17 findings — high 0, medium 2, low 9, false 6, maybe-false 0.
- Four context-free layers ran at parent capability. Three launched first; intent launched immediately when a slot freed, before any triage. Review source diff excluded this narrative; only edge received claims.
- findings, in reporting order:
  - `[medium]` `[patch]` Gap G1: Linux prepare's dependency-initialization call has no nonempty-graph coverage — accepted as pre-verified. Reused HTTP Git fixture through the real prepare_linux.py prepare/build entrypoints; every SDK command asserts recorded direct checkout contents and absence of nested/unrequested content.
  - `[low]` `[reject]` Edge E1: macOS prepare returns success after checkout — true, but the caller contract allows Linux and schema-closed Windows jobs only. Unsupported-runner misuse is unlikely in normal use; adding a platform guard introduces an extra branch without an affected supported caller.
  - `[false]` `[reject]` Intent I1: sample imports differ from a managed module's pinned checkout/templates — the requested consumer surface is the same central MSBuild files, which the sample imports from current Builds to detect regressions. Frozen templates and initialization composites must remain unchanged; this story does not require executing the legacy path.
  - `[false]` `[reject]` Intent I2: Windows job is handwritten rather than rendered — AD-19 expressly calls for one job shaped like a rendered one in Builds' handwritten own workflow. Its two-step shape is implemented; renderer production belongs to its separate story.
  - `[false]` `[reject]` Intent I3: local PowerShell doubles do not prove Windows hosting — the tests explicitly identify this evidence boundary and the real windows-latest job asserts OperatingSystem.IsWindows. Parent verifies that actual job after the authorized commit/push; no local-host equivalence is claimed.
  - `[false]` `[reject]` Intent I4: local tests do not execute GitHub workflow output propagation/scheduling — this correctly describes their layer, not a code discrepancy. The real sample-to-Windows dependency uses validated workflow outputs; exact-SHA hosted execution supplies that final evidence.
  - `[false]` `[reject]` Intent I5: delegated command doubles alone do not demonstrate every product regression — no such exhaustive claim is made. Parent additionally executed real sample normal/failing-product controls through the actual shared job/composites, proving failure propagation at the outer sample surface.
  - `[low]` `[reject]` Intent I6: expected-source has an empty reserved perimeter — true and explicitly documented; current preparation validates only the directory. The later guard/perimeter contract must populate it when enforcement lands. No present enforcement is claimed, and inventing a schema here would be more than a direct correction.
  - `[false]` `[reject]` Intent I7: source diff does not prove commit/push/hosted completion — delivery follows review under explicit user authorization and is recorded with Git/run evidence in Auto Run Result. A unified source diff cannot itself contain that subsequent evidence; this identifies no implementation defect.
  - `[low]` `[reject]` Blind B1: LF joining splits a forged submodule entry into two requests — direct invalid input can do so, but every supported caller consumes the sole loader's validated output; ci_config.py rejects all controls, including LF, before publishing. No validated path can trigger it. An additional pre-join validator would duplicate that input contract for an unlikely manual misuse.
  - `[low]` `[patch]` Blind B2: requested submodules can collide case-insensitively on Windows — parent confirmed Select-Object -Unique accepts A/a. Added its direct CaseInsensitive option for requested destinations; regressions reject collisions and retain case-sensitive exact gitlink-name checks.
  - `[medium]` `[patch]` Blind B3: omitted Windows solution silently skips preparation — changed default from none to empty so existing path validation fails; explicit none still skips. Actual composite regression verifies omission fails before SDK or product work; Linux still loads its own config without a solution input.
  - `[low]` `[reject]` Blind B4: unsupported OS silently succeeds — same verified state as E1. Only Linux/Windows are supported, and no macOS caller exists; a new unsupported-platform branch is unnecessary for everyday use.
  - `[low]` `[reject]` Blind B5: no real Windows submodule checkout is exercised — true evidence limit; the sample's Windows graph is empty. Existing real HTTP Git recorded-revision tests plus actual PowerShell command/argument tests cover the implementation locally, and hosted sample verifies Windows build/action execution. No native-Git defect was demonstrated; another hosted dependency graph would require additional workflow/fixture complexity. Retain this coverage limit rather than claiming it was proven.
  - `[low]` `[patch]` Blind B6: duplicated Windows/Python flags can drift — retained independent mandatory-flag assertions and added comparison of captured Windows restore/build arguments with live ci_pipeline.build_flags, so either direction of drift fails.
  - `[low]` `[patch]` Blind B7: action.yaml escapes expanded action lint coverage — scan both metadata filenames under Github and root .github/actions; executable scanner-input test covers all four root/filename combinations.
  - `[low]` `[patch]` Blind B8: checked-overflow product behavior is untested — sample unit project now asserts integer overflow throws, with two real unit tests passing under shared Release/package flags.
- Grouped surviving repairs: six entries, medium 2 and low 4. Six rows patched, eleven rejected, zero deferred; no intent gap or bad-spec loopback. Each low rejection retains its specific evidence/complexity rationale above.

## Design Notes

Story 5-1 owns guard/commitlint and commitlint-caller deletion. The fixture enables that later integration. Preserve solution/submodules API; add SDK-path output/input to avoid guessing module root from solution parent. Actions may decode the validated array; Windows scripts parse no JSON. Sample checks current Builds through central imports, avoiding nested submodules and old released props.

## Verification

Implementer runs focused behavioral tests on Python 3.12 and runner Python, real sample shared stages/delegated tests, prepare PowerShell command-effect/failure controls, pinned actionlint/online zizmor, relevant catalog checks. Leave implementation uncommitted for parent review.

Parent repeats focused tests and full locked `Tools/ci/run_python_tests.py` on both interpreters with tool/token prerequisites; runs `python3 Tools/ci/lint_workflows.py` and locked `Tools/ci/check_public_api.py` (Git-object checker repeated after commit). Run real sample restore/build/classified units/integration and built delegated tests, including failing-product mutation control. Inspect complete staged delta/frozen paths against implementation_baseline_revision, whitespace, exact-message pinned commitlint, fetch/divergence, commit/push and hosted exact-SHA CI. Confirm Windows on windows-latest, not inferred from local pwsh.

## Implementation Notes

- Implementer delivered 30 Builds-relative files, uncommitted for parent review. New sample has five projects and four classified/delegated test lanes; nested solution and current central imports exercise consumer setup. Linux prepare shares existing loader/build/environment APIs; Windows uses PowerShell and validated solution/submodules/SDK inputs.
- Implementer focused evidence: 15 prepare tests on Python 3.12 and 3.14.4, 20 environment tests, 12 linter-helper tests, real sample shared sequence, real local PowerShell prepare, five-project sample authority check, pinned online lint with zero new findings. Local pwsh is not claimed as Windows-runner evidence.
- Parent inspected the complete staged implementation delta and compared all 59 frozen starting blobs: zero changed. Parent pinned online lint passes with 12 exact frozen findings and zero new findings. Precommit Git-object API check passes 2488 entries against v4.46.0; final committed revision will be checked separately.
- Parent disposable real-sample workflow/composite execution passed normal product through units, root hook and integration. Mutating checked addition to subtraction returned unit exit 2 and suppressed hook/integration. The workspace implementation was never mutated. Evidence log: `/tmp/story-2-6-parent-sample.log`.
- The expected-source directory contains sample config and an explicitly reserved perimeter filename. Story 5-1 owns perimeter schema and guard execution; no enforcement claim is made here.

- Parent full locked Python suites passed **20/20 groups on Python 3.12 and 3.14.4**, including all new prepare cases. Logs: `/tmp/story-2-6-parent-python312.log`, `/tmp/story-2-6-parent-runner.log`. Parent root package-authority validation passed 28 projects. Matrix audit: each row has executed passing behavioral coverage; actual Windows-runner confirmation remains the authorized post-push delivery check.

## Auto Run Result

Status: **blocked**. Implementation, review, local verification, commit and push are complete. Actual hosted sample/Windows execution is blocked by a confirmed GitHub Actions outage.

Blocking condition: hosted CI unavailable during GitHub Actions incident tp8cghg7tlc4; both attempts failed before any job started.

- Added a sample consumer of current Builds imports, real unit/integration/delegated hook/Windows tests, a second shared-CI call, SDK output, and a dependent two-step Windows job. New prepare shares Linux loader/build/environment behavior and accepts validated Windows inputs without Python or configuration JSON parsing.
- Review: 17 findings, six repaired entries (medium 2, low 4), eleven rejections recorded individually in Review Triage Log, zero deferred and no loopback. Rejections concern unsupported-runner use, already-validated LF inputs, later guard integration, limits of source-diff/local evidence, and native Windows dependency coverage without a demonstrated defect.
- Follow-up review recommendation: **true**. First pass repaired two medium entries. Specific unverified risk: selective native Git checkout with a nonempty dependency graph has not been exercised on a Windows host; the sample Windows graph is empty. Real HTTP Git plus PowerShell behavior is tested locally, and the actual Windows build/action is checked in hosted CI.
- Parent final verification: full locked suites **20/20 groups on Python 3.12 and 3.14.4**; online actionlint/zizmor **12 exact frozen findings, zero new**; root package authority **28 projects**; real sample shared sequence succeeds; failing arithmetic returns unit exit 2 and suppresses hook/integration. Removing checked arithmetic independently fails the new overflow assertion (one unit passes, one fails). Three review mutations (removed Linux initialization, restored silent no-op default, shared-flag drift) are killed by the new regressions.
- Parent read the complete implementation delta and repair diff. All **59 frozen runtime blobs** match implementation_baseline_revision, including all four named composites. Whitespace checks and exact full candidate pinned commitlint pass. Final Git-object API and hosted evidence follow below.
- Evidence logs: `/tmp/story-2-6-final-{python312,runner,lint,api,sample}.log`, `/tmp/story-2-6-review-mutations.log`, `/tmp/story-2-6-overflow-control.log`, `/tmp/story-2-6-parent-catalog.log`, `/tmp/story-2-6-commitlint.log`.
- Residual boundary: perimeter schema/guard enforcement remains the later owning story; the expected-source filename is explicitly reserved, and the existing first CI step is not claimed as enforcement. Cross-repository consumers still await adoption.

Files changed (Builds-relative):

- `.github/actions/after-unit-tests/action.yml` — Runs the already-built delegated sample test project.
- `.github/actions/sample-windows/action.yml` — Runs the already-built delegated sample test project.
- `.github/workflows/builds-ci.yml` — Calls sample CI and its dependent two-step Windows job; aggregates both verdicts.
- `.github/workflows/ci.yml` — Exposes the validated SDK file along with solution/submodules outputs.
- `Github/lib/tests/test_ci_environment.py` — Executable harness supports PowerShell, action inputs, external controls and working directories.
- `Github/lib/tests/test_ci_pipeline.py` — Reuses real HTTP Git fixture across pipeline and prepare entrypoints.
- `Github/lib/tests/test_ci_prepare.py` — Nineteen executable preparation/delegation tests, including recorded dependency initialization.
- `Github/prepare/action.yml` — Cross-platform prepare interface and OS-specific execution.
- `Github/prepare/prepare_linux.py` — Reuses strict loader, shared build/classifier and environment outputs.
- `Github/prepare/prepare_windows.ps1` — Safe direct gitlinks and one SDK-rooted Release restore/build without Python/config parsing.
- `Samples/Hexalith.Sample/.github/hexalith-ci.json` — Complete sample config with hook and Windows test delegation.
- `Samples/Hexalith.Sample/Directory.Build.props` — Imports current central Builds settings for the sample consumer.
- `Samples/Hexalith.Sample/Directory.Packages.props` — Imports the authoritative central package catalog.
- `Samples/Hexalith.Sample/README.md` — Documents sample layout, preparation interfaces and evidence limits.
- `Samples/Hexalith.Sample/expected-source/rendered/Hexalith.Sample.perimeter.json` — Expected-state fixture for later guard integration.
- `Samples/Hexalith.Sample/expected-source/rendered/Hexalith.Sample/.github/hexalith-ci.json` — Expected-state fixture for later guard integration.
- `Samples/Hexalith.Sample/global.json` — Pins the sample SDK and Microsoft.Testing.Platform.
- `Samples/Hexalith.Sample/solutions/Hexalith.Sample.slnx` — Nested sample solution with five product/test projects.
- `Samples/Hexalith.Sample/src/Hexalith.Sample/Calculator.cs` — Small real product with checked arithmetic.
- `Samples/Hexalith.Sample/src/Hexalith.Sample/Hexalith.Sample.csproj` — Centrally versioned sample library/test project and internal product reference.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.HookTests/CalculatorTests.cs` — Product assertion at the corresponding unit/integration/hook/Windows boundary.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.HookTests/Hexalith.Sample.HookTests.csproj` — Centrally versioned sample library/test project and internal product reference.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.IntegrationTests/CalculatorTests.cs` — Product assertion at the corresponding unit/integration/hook/Windows boundary.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.IntegrationTests/Hexalith.Sample.IntegrationTests.csproj` — Centrally versioned sample library/test project and internal product reference.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.UnitTests/CalculatorTests.cs` — Product assertion at the corresponding unit/integration/hook/Windows boundary.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.UnitTests/Hexalith.Sample.UnitTests.csproj` — Centrally versioned sample library/test project and internal product reference.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.WindowsTests/CalculatorTests.cs` — Product assertion at the corresponding unit/integration/hook/Windows boundary.
- `Samples/Hexalith.Sample/test/Hexalith.Sample.WindowsTests/Hexalith.Sample.WindowsTests.csproj` — Centrally versioned sample library/test project and internal product reference.
- `Tools/ci/README.md` — Documents sample layout, preparation interfaces and evidence limits.
- `Tools/ci/lint_workflows.py` — Scans both action metadata filenames under both action roots.
- `Tools/ci/tests/test_lint_workflows.py` — Verifies complete action-root/filename scan inputs.

- Delivery commit: `93c9db2e2892be80ab8595052b91cbda5b7d158f` on Builds main, pushed successfully after fetch showed one local and zero remote-only commits. Stored full commit message exactly equals the pinned-commitlint-validated candidate; the owning working tree is clean.
- Committed API check passes against v4.47.0 (`5ec1779040606be89306129a7d2b245258c9acd2`): **2494 entries, no removals**. Log: `/tmp/story-2-6-committed-api.log`.
- Exact-source push runs: [CI 42672353669](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42672353669), [Commitlint 42672354063](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42672354063). Hosted outcome will be appended when complete.

- Hosted CI attempt 1 failed before any job started: GitHub run annotation says **Internal server error**, correlation ID `5a4ec4b3-aab5-4741-b7d7-ef69c3da2353`. REST jobs/check-runs were empty. Commitlint completed/success. Parent reran the same CI run at the same commit; no code was changed for this infrastructure failure.

- Final hosted state: CI run 42672353669 **attempts 1 and 2 failed before creating any jobs**. Attempt 2 correlation ID is `5ba17e68-2a98-450a-bc2e-980287369a07`; its log archive is empty. Commitlint run 42672354063 completed/success at the exact implementation revision. This is not a passing hosted CI claim.
- Confirmed external blocker: GitHub's live [official status API](https://www.githubstatus.com/api/v2/summary.json) reports Actions **major_outage**, incident `tp8cghg7tlc4`, started `2026-11-09T18:12:37.232Z`, before the push run at `18:14:56Z`. Latest captured update says Actions is experiencing degraded availability and GitHub is investigating. Earlier cached status/unresolved endpoints returned stale operational state; the live summary and independent diagnostic confirmed the outage. Snapshot: `/tmp/story-2-6-github-status.json`.
- Read-only diagnostic found no concrete workflow syntax defect. No diagnostic branch, source workaround or extra commit was created in response to the outage. Resume verification after GitHub recovers by rerunning CI 42672353669 at the same pushed commit, then inspect actual sample, Windows, quality and both Python jobs. Native Windows execution remains unverified until that succeeds.
- Final Git state: Builds HEAD and origin/main both equal `93c9db2e2892be80ab8595052b91cbda5b7d158f`; owning working tree is clean. All 31 implementation files are committed and all 59 frozen runtime blobs match their starting IDs. CiCd stages only this story record and updated Builds gitlink; no CiCd commit/push or release dispatch was made.
