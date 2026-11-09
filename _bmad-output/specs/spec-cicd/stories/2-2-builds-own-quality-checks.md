---
title: "Builds' own quality checks"
type: feature
created: '2026-11-09'
status: done
baseline_revision: '279c1f1d55c213d71a421189c132df69d7e746fb'
implementation_baseline_revision: '25de7a74d14d099faf7baea5da0cbb0b40264592'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
implementation_repository: references/Hexalith.Builds
---

<intent-contract>

## Intent

**Problem:** Builds' CI lacks the workflow linting, dual-Python script checks and public API removal protection required by CAP-15 and AD-10/11.

**Approach:** Add a quality lane to `builds-ci.yml`, committed lint configuration and pinned tool execution, a shared Python suite runner, and a public API comparator against the last stable release tag reachable from the checked revision. Remove tests that assert workflow text while retaining behavioral execution coverage.

## Boundaries & Constraints

**Always:** Implement in `references/Hexalith.Builds` on `main`, using the CiCd-agent credential. AD-20 freezes every module-executed file, directly or transitively, including all existing non-test `Github/` files and `domain-ci.yml`, `domain-ci-v2.yml`, `domain-release.yml`, `codeql.yml`, `commitlint.yml`, `dependency-review.yml`. This explicitly includes `initialize-dotnet`, `initialize-build`, `create-release`, `verify`. Tests are exempt. New code goes in new files. Retain existing release, G4/G6 qualification, catalog, CodeQL, commitlint and aggregate behavior until the later release rewrite. Third-party actions use full SHAs with version comments. Python logic is >=3.12; workflows invoke scripts, with expressions passed via env. Runtime scripts are stdlib only; CI-only YAML validation may use locked PEP723 PyYAML. Downloaded tools require committed versions and checked SHA256. Npm installs use the lockfile and signature audit. Validate the exact commit message with pinned commitlint; fetch/check divergence before push. Record full revisions from Git.

**Never:** Edit frozen runtime files to satisfy lint; globally disable security audits beyond the spine's `self-repository` exception; use zizmor `--fix` or disable online audits; dispatch a release; advance another story; initialize nested submodules; add tests asserting repository workflow source text. Retain tests exercising extracted script execution and synthetic API fixtures.

## I/O & Edge-Case Matrix

| Scenario | State | Behavior | Failure |
| --- | --- | --- | --- |
| Compatible API | Additive or unchanged surface | Pass against baseline tag | None |
| Removal/rename | Prior public entry disappears | Fail naming removed entries | Nonzero without breaking marker |
| Intentional breaking API | Removal plus Conventional Commit `!` or BREAKING CHANGE/BREAKING-CHANGE footer in baseline..head | Pass with explicit diagnostic | None |
| Baseline selection | Stable v-semver tags plus prerelease/unreachable tags | Select highest reachable stable release tag | Missing history or invalid documents fail clearly; no tags is explicit bootstrap |
| Tool failure | Bad integrity, linter failure, test process failure | Fail quality lane | Never swallow failure |

</intent-contract>

## Code Map

Paths below are relative to Builds.

- `.github/workflows/builds-ci.yml:272` — existing Python job installs .NET and Node and runs explicit scripts and unittest directory groups; other jobs stay until release rewrite. `build-and-test` currently needs four validation jobs.
- `.github/actionlint.yaml` — existing narrow job.workflow_* ignores. Extend with spine ignores for `$/`, job.workflow_* and cache-mode. Actionlint v1.7.12.
- New `.github/zizmor.yml` and `Tools/ci/` — committed policy and CI-only scripts/locks/tests. Zizmor v1.32.0: ref-pin `Hexalith/*`, hash-pin others, self-repository audit off; scan all workflow YAML and `Github/**/action.yml`, online audits enabled. Frozen workflow findings use specific per-rule ignores.
- Zizmor v1.32 official configuration docs explicitly cannot ignore composite findings through config. If confirmed, use a committed narrowly scoped exact-finding baseline for frozen composite findings outside the files, with rationale and path/rule/location matching; new files/findings still fail. Never alter frozen composites or hide scan failure.
- `Tools/test-*.py`, `Tools/test_*.py`, `Github/*/tests/`, `test/qualification/` — test inputs; use explicit subprocess execution/discovery, not recursive default discovery that loses hyphenated scripts or assertion-based `test_runtime_toolchain_v2.py`. Some cases need .NET and pinned npm tools.
- Workflow-text-only tests: `prepare-module-build/tests/test_prepare_module_build.py` three workflow methods; `governed-provenance/tests/test_candidate_policy.py` three static methods; `split-publication/tests/test_split_publication.py` HostileWorkflowTests static method; `commitlint/tests/test_commitlint_workflow.py` static title-transfer and caller registration; `Tools/test-prepare-domain-release.py:124` static workflow comparison; static methods in `publish-containers/tests/{test_publish_script_contract,test_governed_release_workflow}.py` and provenance closure tests. Preserve behavioral shell/CLI/script cases; inspect remaining test languages too.
- Public API per AD-10: reusable workflow_call inputs/secrets/outputs; composite inputs; schema files; imported `Hexalith.Build.props`, `Hexalith.Package.props`, `Props/Directory.Packages.props`; `PackageVersion` names. Exclude test-only module-root/expected-source. New prepare/publish/ci/release/schema surfaces may not exist yet; additions must pass. Use real YAML, JSON and XML parsing and Git objects, not string assertions or regex YAML parsing.
- Existing release tag `v4.45.1` resolves to starting Builds HEAD `25de7a74d14d099faf7baea5da0cbb0b40264592`. Superproject starting HEAD is `279c1f1d55c213d71a421189c132df69d7e746fb` (re-read when stamping).

## Tasks & Acceptance

**Execution:**
- [x] `.github/actionlint.yaml`, new `.github/zizmor.yml`, `Tools/ci/lint_workflows.py` and pin/baseline support — run pinned lint over required surfaces with committed scoped policies, integrity checks and online audits.
- [x] New `Tools/ci/check_public_api.py` and dependency lock — parse baseline/current public surfaces and commit messages; reject unmarked removals with actionable diagnostics.
- [x] New `Tools/ci/run_python_tests.py` and `Tools/ci/tests/` — run retained script suites, including new meaningful Git/API and tool-failure cases, on both interpreters; remove workflow-source assertions from existing test paths identified above without weakening runtime behavior tests.
- [x] `.github/workflows/builds-ci.yml` — invoke lint/API helpers and identical Python suite on setup-python 3.12 and runner python3 (capture absolute runner interpreter before setup); install required dependencies with pins; include checks in CI verdict; retain existing legacy jobs.
- [x] `Tools/ci/README.md` — document local commands, API baseline/bootstrap behavior, tool pins and temporary frozen ignores.
- [x] Builds repository and this spec — validate freeze and checks, commit/push Builds, record delivery evidence; stage updated superproject gitlink with story per workflow.

**Acceptance Criteria:**
- Given a Builds push/PR, when `builds-ci.yml` runs, then actionlint and online zizmor scan all required files using committed policy and a new unignored finding fails the run.
- Given both Python interpreters, when CI runs the shared suite, then every retained scripted test group runs under 3.12 and the captured runner python3, and failures fail CI.
- Given an API removal, when the checker runs against the last reachable stable release tag, then it fails without a breaking-change commit and succeeds when that marker exists; additive changes pass and diagnostics name baseline and entries.
- Given workflow text assertion tests, when the retained suite is inspected/executed, then source-text assertions are absent and meaningful execution/output tests still pass.
- Given the delivered diff, when compared with the starting Builds revision, then all frozen runtime bytes and legacy release behavior remain unchanged.

## Implementation Notes

- New `Tools/ci/` helpers provide verified actionlint 1.7.12, zizmor 1.32.0 and uv 0.13.7; locked PyYAML 6.0.3; Git-object API comparison; exact frozen-composite findings; runner interpreter capture; and one explicit Python group runner. Setup-python 7.1.0 and other third-party actions are SHA-pinned. The own workflow has job-level read permissions, a quality job and a Python 3.12/runner matrix, all feeding the retained aggregate verdict.
- Zizmor 1.32 cannot suppress composite findings through YAML config. The external baseline records 12 preexisting findings with rule/path/ranges/feature hashes and rationale. Frozen workflows have per-rule location ignores. Online audits remain enabled. The parent independently confirmed a real temporary unpinned workflow fails through the production policy, and the final full online scan reports zero new findings across 24 inputs.
- Removed source-text assertions from Python and PowerShell tests; preserved extracted-script execution/output coverage. Newly included `Tools/test_g6_current.py` depended on ambient EventStore source/evidence in the umbrella checkout; its test inputs are now generated hermetically with real Git material mutation and retained receipt/count/source/scope negatives. No runtime implementation changed for this portability repair.
- Parent verification caught and fixed an installer `ETXTBSY` error while uv was running: verified archives/executables now publish by atomic replacement. A real running-ELF reinstall test proves the old process survives and the replacement executes. Parent also required spine-aligned tool pins, global narrow job.workflow_* ignores, explicit job permissions and exclusion of test-only workflow inputs from API comparison.
- Parent independently passed both changed PowerShell suites (312 legacy and 206 v2 assertions), npm signatures (318 verified signatures, 58 verified attestations), the API baseline check (v4.45.1, 2,430 compatible entries), and staged whitespace checks. The exact candidate in `/tmp/hexalith-story-2-2-commit-message.txt` passed the owning pinned commitlint CLI with zero problems/warnings; evidence is `/tmp/story-2-2-commitlint.log`.
- Parent independently compared all 58 frozen blobs with `implementation_baseline_revision`, including the four named composites; every blob is unchanged. Legacy release is absent from the diff. The two full independent suite runs are recorded in `/tmp/story-2-2-parent-python312.log` and `/tmp/story-2-2-parent-python314.log`; both completed successfully with **18/18 groups passed**, including all 39 new helper tests, on Python 3.12.13 and 3.14.4. The original uv process was started with the earlier verified bootstrap; the final pinned uv 0.13.7 also passed locked helper/API runs. The final online lint retry passed while both runners were alive, proving the atomic replacement repair in actual use.

- Matrix audit: additive/unchanged API, removal/rename, all four breaking-marker forms, semantic tag ordering/ancestry, shallow/invalid/bootstrap histories, tampered tool archives, failed linters and failed test processes each have covering synthetic behavior tests in `Tools/ci/tests/`; all ran and passed in both complete suite outputs. New-finding failure was additionally exercised with real pinned linters and production policy.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass

- verdicts: 19 findings — high 0, medium 6, low 5, false 8, maybe-false 0. Four context-free layers completed; the fourth was launched as soon as the three-slot concurrency limit freed a slot, before triage. The review diff included the implementation repository and other superproject changes; this narrative was withheld from the blind/gap/intent layers and supplied only through the edge layer's claims path.
- findings, in reporting order:
  - `[medium]` `[patch]` Blind: schema annotation values are interpreted as schema rules — parent reproduced a valid examples array containing an instance enum string failing validation. Traversal now follows only schema-bearing keywords; examples/default/const and unknown vocabulary data remain opaque. Git regressions cover additive and removed annotations.
  - `[medium]` `[patch]` Blind: slash-delimited schema names collide with nested property paths — parent reproduced removal of literal foo/properties/bar passing. Named path components now escape slash/tilde according to JSON Pointer; independent slash/tilde removal fixtures reject the loss.
  - `[low]` `[reject]` Blind: composite outputs are not compared — AD-10's explicit API-check list names composite inputs, while reusable workflow outputs are compared. No current public prepare/publish composite exists yet. Expanding the explicit check list is outside this invocation's AD-10 algorithm; no runtime output changed here.
  - `[low]` `[reject]` Blind: action.yaml is not scanned/protected — the invoked spine's Builds surface is explicitly Github/**/action.yml and the fixed action contract uses action.yml. Every existing Builds action uses that filename. Supporting a second metadata convention adds discovery/API rules outside the named surface.
  - `[low]` `[reject]` Blind: workflow per-rule ignores do not bind source bytes — true, and intentionally distinct from the external composite workaround. AD-20 explicitly requires frozen workflow per-rule ignores and the user forbids changing those files. All 58 frozen blobs were independently compared; broadening the workaround to protect a prohibited future frozen-file edit is unnecessary for this change.
  - `[low]` `[patch]` Blind: the cache-mode action-input ignore masks unsupported inputs — removed that ignore. The parent also reproduced the actual missing native workflow-key exception (recorded below). Real actionlint regressions accept native workflow cache-mode and reject the unsupported checkout input. This shares the native-key policy repair entry.
  - `[low]` `[reject]` Blind: deleted/empty test directories can produce successful group counts — existing groups are nonempty and all 18 run with their tests reported. Deleting a directory removes its test files from the suite; a separate required-inventory/zero-test framework would add guards and duplicate the glob registry for an unlikely everyday state. No present test is silently skipped.
  - `[false]` `[reject]` Blind: a breaking marker inside fenced prose should not authorize removals — the owning pinned conventional-commits-parser also recognizes that exact line as a breaking note, as parent demonstrated locally. This checker matches the release toolchain's marker semantics; the proposed exclusion would introduce disagreement.
  - `[false]` `[reject]` Blind: deleted publication-condition text assertions need parsed replacements — these asserted workflow arrangement and predicates, which CAP-15 expressly removes. Frozen production predicates are unchanged, retained gate bodies still execute in behavioral tests, and generic lint runs against those workflows. Reintroducing equivalent parsed workflow assertions would contradict the intent.
  - `[false]` `[reject]` Blind: deleted hostile-workflow authority checks need replacements — the removed test asserted YAML permissions, steps and pins. Those frozen bytes are unchanged and real security lint now scans them. The synthetic candidate/workspace/authority execution tests remain; no authority path changed in this story.
  - `[medium]` `[patch]` Verification gap: committed third-party pinning policy lacked a real-tool regression — accepted as pre-verified. New tests verify installed binaries against pinned archives and run real online zizmor with the committed config; a tag fails unpinned-uses and the verified SHA passes. Shared CI passes its read-only token explicitly.
  - `[false]` `[reject]` Intent: helper tests alone do not establish hosted matrix/delivery — correct as a limit of unit evidence, not a code defect. The user-authorized commit/push and exact-SHA hosted run are final delivery steps; their evidence is recorded in Auto Run Result rather than fabricated by tests.
  - `[false]` `[reject]` Intent: broader compatibility differs from removal checking — the auditor confirms the removal-only surface matches the story and AD-10's explicit criteria. Types/defaults/constraint semantics are documented limits, not missing promised checks.
  - `[false]` `[reject]` Intent: some removed real-workflow closure checks assert evaluator output — those expected the precise action/helper graph of real workflow files. The retained synthetic collector diamond/helper/hash/identity tests still exercise evaluator behavior without prescribing workflow structure. Frozen graph bytes are unchanged.
  - `[false]` `[reject]` Intent: hermetic fixtures no longer revalidate one ambient historical packet — that packet is not available to a standalone Builds checkout. The repaired tests retain receipt/hash/count/source/scope rejection behavior and real material mutation; no historical packet or validator implementation was rewritten, and synthetic receipts are labeled as such.
  - `[medium]` `[patch]` Edge: annotation instance values create false API entries/failures — independently duplicates the verified annotation traversal defect. It shares that repair entry and its real Git regression evidence.
  - `[false]` `[reject]` Edge claim: action source assertions remain in prepare-domain-release tests — the cited ACTION is composite metadata, not a workflow file. CAP-15's workflow-source assertions were removed; metadata-bound action behavior and output tests are retained. The claim does not identify a remaining assertion against a real workflow's text.
  - `[medium]` `[patch]` Parent: native workflow cache-mode is still rejected by actionlint — the real binary reported unexpected key cache-mode for workflow section; the prior ignore targeted an action input instead. Replaced it with the narrow native-key diagnostic prefix and kept unrelated input errors active. Shares the blind cache-mode repair entry.
  - `[medium]` `[patch]` Parent repair verification: indexed unordered schema alternatives falsely remove names when a branch is prepended/reordered — parent reproduced additive anyOf failure in a temporary Git repository. allOf/anyOf/oneOf/extends alternatives now have position-independent entries; tuple prefixItems/legacy items retain positions. Git fixtures cover both positive alternative changes and negative tuple-position changes.
- Grouped repairs: five medium entries (schema annotation traversal, escaped names, cache-mode policy, effective pinning-policy tests, unordered alternatives); seven finding rows patched. Rejected rows: twelve. Deferred entries: zero. No intent gap or bad-spec loopback.


## Verification

Run new API/tool tests and the shared Python suite with Python 3.12 and runner python3. Run pinned actionlint and online zizmor through the new helper; run API comparison against v4.45.1. Use negative temporary fixtures for unmarked removal, breaking markers, tag ancestry, new lint findings and integrity/process failure. Inspect staged diff and compare frozen blobs against implementation_baseline_revision. Run `git diff --check` and pinned commitlint on exact candidate; fetch/inspect/push Builds main, then inspect exact-SHA hosted CI without dispatching a release. Record any unrelated existing CI blockers separately.

## Auto Run Result

Status: done. Implementation committed and pushed to Builds main under the invocation's explicit delivery authorization.

- Implemented Builds-own lint/API checks and identical script suites on Python 3.12 and runner python3; removed real-workflow text assertions while preserving behavioral cases. The API check reads Git objects and protects the AD-10 removal surface against the latest reachable stable tag, with Conventional Commit breaking markers for intentional removals.
- Changed files (Builds-relative):
  - `.github/workflows/builds-ci.yml` — quality lane, dual-Python matrix, SHA pins, scoped permissions and aggregate verdict.
  - `.github/actionlint.yaml` — narrow self-repository, workflow identity and native cache-mode exceptions.
  - `.github/zizmor.yml` — third-party hash policy, Hexalith ref policy and frozen workflow locations.
  - `Tools/ci/tools.json` — versions, HTTPS archives and SHA256 digests for actionlint 1.7.12, zizmor 1.32.0 and uv 0.13.7.
  - `Tools/ci/lint_workflows.py` — integrity-checked atomic installation, complete lint inputs, online audits and exact frozen composite matching.
  - `Tools/ci/frozen-composite-findings.json` — twelve exact legacy findings with hashes, locations, revision and rationale.
  - `Tools/ci/check_public_api.py` — parsed API projection, tag ancestry/order, marker checks and diagnostics.
  - `Tools/ci/check_public_api.py.lock` — pinned and hashed CI-only PyYAML dependency.
  - `Tools/ci/run_python_tests.py` — explicit script/discovery processes with one selected interpreter and propagated failures.
  - `Tools/ci/run_python_tests.py.lock` — identical locked dependency environment for all test groups.
  - `Tools/ci/capture_python.py` — capture runner interpreter before setup-python changes PATH.
  - `Tools/ci/tests/test_public_api.py` — temporary-Git compatibility, marker, schema, import and history controls.
  - `Tools/ci/tests/test_lint_workflows.py` — integrity/process/finding controls, running-binary replacement and real production-policy tests.
  - `Tools/ci/tests/test_python_runner.py` — group discovery, exact interpreter and failure propagation controls.
  - `Tools/ci/README.md` — commands, prerequisites, frozen exceptions and removal-only limitations.
  - `Tools/test_g6_current.py` — hermetic source/evidence fixtures and real Git material mutation.
  - `Tools/test-domain-workflow-test-platforms.ps1` — remove YAML text assertions; retain shell behavior and invocation/output checks.
  - `Tools/test-prepare-domain-release.py` — remove workflow comparison assertions; retain action execution checks.
  - `Github/commitlint/tests/test_commitlint_workflow.py` — remove caller/workflow source assertions; retain injection and CLI checks.
  - `Github/governed-provenance/tests/test_candidate_policy.py` — remove workflow structure assertions; retain policy behavior.
  - `Github/governed-provenance/tests/test_governed_provenance.py` — remove real-workflow graph expectations; retain synthetic collector/identity behavior.
  - `Github/prepare-module-build/tests/test_prepare_module_build.py` — remove static workflow layout/input assertions.
  - `Github/publish-containers/tests/test_governed_release_workflow.py` — remove frozen workflow spelling/order/pin assertions; retain execution/output cases.
  - `Github/publish-containers/tests/test_publish_script_contract.py` — remove action/workflow text-only checks; retain publisher and source-guard behavior.
  - `Github/split-publication/tests/test_split_publication.py` — remove hostile-workflow YAML assertions; retain authority/workspace behavior.
- Review: nineteen finding rows, five grouped repairs (medium 5, high 0, low 0 at grouped-entry verdict), twelve rejected rows, zero deferred. The seven patched rows and every rejection/refutation are recorded individually in Review Triage Log. Rejections concern surfaces outside the explicit AD-10/action.yml check list, intended frozen exceptions, a rare empty-group inventory proposal, release-parser-consistent marker semantics, required workflow assertion removal, and descriptive evidence limitations already handled by delivery/fixtures.
- Parent verification: final full locked suite **18/18 groups passed on both interpreters**, including **46 helper/policy tests**. Logs: `/tmp/story-2-2-final-python312.log` and `/tmp/story-2-2-final-python314.log`. Both changed PowerShell suites passed (312 legacy, 206 v2 assertions); npm signature audit passed (318 signatures, 58 attestations). Final online actionlint/zizmor passed across 24 inputs with 12 exact frozen findings and zero new findings. A real temporary unpinned workflow was rejected. The final API extractor passed v4.45.1 with 2,430 entries. Staged/unstaged whitespace checks and exact pinned commitlint validation passed.
- All 58 frozen runtime blobs, including initialize-dotnet, initialize-build, create-release and verify, are byte-identical to the implementation baseline. Legacy release/runtime files and package/release configuration are unchanged. No release was dispatched.
- Follow-up recommendation: false. Five medium repair entries ordinarily trigger a recommendation, but the named unverified risk was hosted interpreter/token behavior and is now closed by the exact-SHA quality and both matrix jobs. Their logs confirm the complete suites and real online policy regressions under GitHub-hosted read-only tokens. No specific unverified implementation risk remains after parent inspection and the recorded regressions.
- Residual limits: the API checker detects removals/renames, not every semantic compatibility change. Frozen lint exceptions are temporary until AD-20 migration completes. Historical validator tests use labeled hermetic inputs, not an ambient live qualification packet.

- Delivery commit: `459c1f2fe347ebcdf125c514dd3e08439d3324a5`, subject validated by pinned commitlint. Fetch before push showed one local commit and no remote-only commit; push fast-forwarded main successfully. Full HEAD and origin/main match that revision and the Builds working copy is clean. All 25 reviewed implementation files are included in that commit. The committed-revision API check again passed v4.45.1 (2,430 entries).
- Exact-SHA hosted runs: [Builds CI 42604909419](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42604909419) and [Commitlint 42604909420](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42604909420). Both started on push; no workflow or release was dispatched manually. Both completed successfully at the delivery revision.
- CiCd records the story and updated Builds gitlink together in its index, as required for submodule stories. The implementation repository is clean; these superproject records are intentionally staged for the caller rather than pushed as an unrelated CiCd delivery.

- Hosted new checks passed: quality job 129118282627 confirms v4.45.1 against the delivery revision and 12 exact frozen findings/zero new findings. Python jobs 129118282704 (3.12.16) and 129118282526 (captured runner /usr/bin/python3.14, 3.14.4) each report 18/18 groups and 46 helper tests, including both real-tool regressions. Logs are `/tmp/story-2-2-hosted-quality.log`, `/tmp/story-2-2-hosted-python312.log` and `/tmp/story-2-2-hosted-python-runner.log`. All eight CI jobs, including retained .NET tests, package qualification and the aggregate verdict, passed. Commitlint also passed.

- Final hosted result: **CI 42604909419 completed/success**, all eight jobs successful, including the aggregate Build and test; Commitlint 42604909420 completed/success. Both use delivery revision `459c1f2fe347ebcdf125c514dd3e08439d3324a5`. API job logs and both interpreter logs were read directly from GitHub. Machine-readable run/job evidence is `/tmp/story-2-2-hosted-results.json`.
- Final repository checks: Builds is clean on main, the committed message equals the exact validated candidate, and all 58 committed frozen blobs match the starting revision. Only the story spec and Builds gitlink are staged in CiCd. No implementation, verification, delivery or deferred task remains.
