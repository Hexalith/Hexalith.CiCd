---
title: 'Guard drift detection and the release drift check'
type: feature
created: '2026-11-13'
status: done
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 171e764656d8b57d5f06c8f99c2b7c3b9c64650b
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 3d110e06b286acbc6f5aae33fa7eb571e9268b0c
implementation_original_baseline_revision: f01c3ab70f7e7401b3b73217983955f7771a1465
implementation_integration_revision: 05a75b626fb73c6e386d16c41e885f193d3cff16
implementation_original_revision: 0f97426edb6f88ee6e534d95ca9029f7e0b20311
implementation_resume_baseline_revision: 2ecffe8bf5258c3a5b02e58ae8cfad8ab9d77071
implementation_revision: 185e3a4e695f392e114eacffbdecd2a23da32c9b
implementation_evidence_revision: 4dffd595e54699320d483edc1f27aff9b62ed8ca
implementation_review_revision: 7db81f4f19bef5e5337d241abc4bbff98ef62c4c
implementation_followup_integration_revision: cae351e20093634483afad16aca3bfd90845eda8
implementation_final_integration_revision: 9bbe8380c13094ddf41cfd780e3a69289e94b9d4
context:
  - _bmad-output/specs/spec-cicd/SPEC.md
  - _bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md
warnings: [oversized]
deferred:
  - summary: >-
      On create-mode drift, release resolve still emits CodeQL and nightly-hook settings parsed from the drifted dispatch-SHA configuration, so the owned edit can steer the release security jobs.
    evidence: |-
      Follow-up review BH1/IA-D1. release_state.resolve emits dispatch_settings(git, sha, ...) after the completed comparison but before Comparison.require_clean() raises. release.yml gates codeql and nightly-hook only on !cancelled() && config-valid == 'true' (plus codeql != '[]' / nightly-hook == 'true'), not on the resolve result. So an owned edit setting "codeql": [] skips release CodeQL, and adding "nightly" to hooks starts nightly-hook, which runs $/Github/prepare with the registry pull secrets and then ./.github/actions/nightly. test_module_create_matches_accepted_state_and_blocks_drift_before_false_switch asserts codeql == ["ruby"] from the drifted file. This is pre-existing: the baseline emitted dispatch settings unconditionally, before any check. The story's AC and Design Notes explicitly keep these settings available to the existing security jobs, and no publication handoff occurs. Settling it needs a design decision: emit the accepted (expected) configuration's settings on drift, or force nightly-hook=false and the accepted CodeQL languages.
    location: >-
      references/Hexalith.Builds/Github/lib/release_state.py resolve (dispatch_settings emission before require_clean); references/Hexalith.Builds/.github/workflows/release.yml codeql/nightly-hook if conditions
    severity: medium
  - summary: >-
      Release resolve configuration diagnostics still name a random, already-deleted temporary path instead of the committed logical configuration path.
    evidence: |-
      Follow-up review BH3/VG3. release_state.dispatch_settings materializes the dispatch blob into tempfile.TemporaryDirectory(prefix="hexalith-release-config-") and passes it to load_config. Two calls on an invalid configuration printed /tmp/hexalith-release-config-e4hcdqgv/hexalith-ci.json: ... and then /tmp/hexalith-release-config-m4ev6d9i/hexalith-ci.json: .... The guard's expected_state.load_ci maps loader errors to the committed path. dispatch_settings already has this behavior at implementation baseline f01c3ab70f7e7401b3b73217983955f7771a1465, and this story did not change it. Fix: apply the same str(error).replace(str(path), relative) mapping, and assert the logical path and repeat stability in test_release_adapters.
    location: >-
      references/Hexalith.Builds/Github/lib/release_state.py dispatch_settings
    severity: low
  - summary: >-
      Builds main stays red on two baseline failures with no follow-up owner: the package-catalog validator's 14 EventStore 4.2.0-versus-5.0.0 assertions (exit 1) and the 44 failing Evidence.Tests identities (exit 2).
    evidence: |-
      Follow-up review BH14. Both failures reproduce on integration revision 05a75b626fb73c6e386d16c41e885f193d3cff16 (run 43387068103), before this story's source. They come from upstream dependency/catalog changes: Props/Directory.Packages.props moved HexalithEventStoreVersion to 5.0.0 while the catalog assertions still require 4.2.0. The story-5-1 verification exception tolerates them for story verification only. The deferred-work ledger has no entry for either failure. While they persist, Builds' own release green-CI gate cannot pass. Settle by reconciling the catalog validator with the EventStore 5.0.0 pin, and by triaging the 44 Evidence.Tests failures in their owning upstream change.
    location: >-
      references/Hexalith.Builds package catalog contracts job; test/Hexalith.Builds.Evidence.Tests
    severity: medium
  - summary: >-
      Exact-name catalog snapshots accept case-varied consumer names.
    evidence: |-
      Review EC1/BH2: MSBuildProjectName.Equals selectors are case-sensitive, but CatalogVersionMaterializer stores project views with OrdinalIgnoreCase and CompositionDeclarationOptions.ReadRecordedPackageVersion uses OrdinalIgnoreCase. A clean Hexalith.Parties.Tests view selects SDK4.2/OpenAPI2; hexalith.Parties.Tests selects SDK5/OpenAPI3 but can reuse the recorded retained view. Both paths were traced and disposable MSBuild evaluations confirmed the selection difference. This is present in upstream integration cae351e20093634483afad16aca3bfd90845eda8, before the story follow-up commit; fix exact-name materialization/lookup and add a case-varied consumer test in the catalog workstream.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Workspace/CatalogVersionMaterializer.cs:175; Runtime/CompositionDeclarationOptions.cs:183
    severity: medium
  - summary: >-
      The no-snapshot catalog package reader selects conditional EventStore4.2 instead of the default SDK5 view.
    evidence: |-
      Review BH1: CompositionDeclarationOptions.ReadCatalogPackageVersion resolves $(HexalithEventStoreVersion) using the first XML descendant without evaluating its condition. The integrated catalog now declares the retained conditional 4.2.0 before the default 5.0.0, while the first OpenAPI declarations remain 11.0.0/3.11.0. This yields a crossed default tuple through the public no-snapshot overload. The implementation and declaration order are present unchanged in integration cae351e20093634483afad16aca3bfd90845eda8; this story changes neither file. Use an evaluated default view or require the materialized snapshot in that owning catalog change.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionDeclarationOptions.cs:147
    severity: medium
  - summary: >-
      The Python catalog selector reader omits the new Equals-based consumer views from runtime inventory.
    evidence: |-
      Review BH3: Tools/evaluated_catalog.py.conditioned_catalog_project_names recognizes quoted == expressions only. Tools/runtime_toolchain_v2.py.inventory evaluates a consumer-specific catalog only when the project stem is in that returned set. The integrated MSBuildProjectName.Equals selectors are therefore omitted and affected projects receive the default SDK5 inventory. The C# selector reader was updated upstream but this Python reader was not; both the new selectors and this omission already exist in integration cae351e20093634483afad16aca3bfd90845eda8. Extend the Python selector extraction and behavioral inventory tests in that catalog workstream.
    location: >-
      references/Hexalith.Builds/Tools/evaluated_catalog.py:96; Tools/runtime_toolchain_v2.py:186
    severity: medium
  - summary: >-
      Current toolchain defaults and some tests remain coupled to newly frozen v1 runtime pins.
    evidence: |-
      Review BH4/BH9: SupportedPlatformPins now returns immutable v1 literals, but CompositionToolchainPins.DaprRuntimeVersion still delegates to that facade and CompositionPrerequisiteProbe uses it for its documented catalog default. SupportedPlatformPinsCatalogTests also retains current-versus-frozen equality for FrontComposer and Dapr. Values currently agree, so no current hosted failure exists; a future approved current-catalog update would leave the default probe on the frozen runtime and reject the otherwise independent catalog update in tests. This authority split was introduced by the preserved upstream frozen-pin work and is present at integration cae351e20093634483afad16aca3bfd90845eda8. Reconcile the intended current/frozen facade and test authorities in that workstream.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionToolchainPins.cs:34; test/Hexalith.Builds.Module.Tests/SupportedPlatformPinsCatalogTests.cs:29
    severity: low
  - summary: >-
      Active retained compatibility package selections have no current conditional-selection audit records.
    evidence: |-
      Review BH5: The current package audit rows bind EventStore.Gateway5.0.0, ASP.NET OpenAPI11.0.0, OpenAPI3.11.0 and OpenIdConnect11.0.0. The active named views select 4.2.0, 10.0.15, 2.13.0 and 10.0.15, respectively, but any old observations are labeled historical and do not bind the current conditional selections. This leaves current listing/retention provenance incomplete for those consumers. The audit and selectors are unchanged from upstream integration cae351e20093634483afad16aca3bfd90845eda8; extend current view-bound audit evidence in the owning package-audit workstream.
    location: >-
      references/Hexalith.Builds/Tools/package-version-audit.json; Props/Directory.Packages.props
    severity: medium
  - summary: >-
      Automatic response-file isolation lacks a real consumer-authority regression test.
    evidence: |-
      Review VG1, pre-verified: Removing only -noAutoResponse from validate-central-package-versions.ps1 still passed all 23 central-validator scenarios. A disposable ancestor Directory.Build.rsp setting FixtureVersion=9.9.9 under TMPDIR made both actual and expected consumer evaluations use 9.9.9 and validation exit successfully after that mutation; current code correctly rejects 9.9.9 instead of 1.2.3. The consumer-authority suite covers local XML overrides but not this response-file path. The isolation fix and test gap already exist in upstream integration cae351e20093634483afad16aca3bfd90845eda8 and are outside this story-authored patch. Add the demonstrated real-process poisoned-response-file case to the owning consumer-authority suite.
    location: >-
      references/Hexalith.Builds/Tools/validate-central-package-versions.ps1:218; Tools/test-consumer-package-authority-validator.ps1
    severity: medium
---

<intent-contract>

## Intent

**Problem:** Shared CI's first stage is a no-op, and release resolve accepts `delivered-sha` without checking owned content. An edited pipeline or unreadable module configuration can reach parsing before ownership is enforced.

**Approach:** Add a read-only guard that acquires the module's accepted delivered tree, reuses 4-1's loader/comparison engine, and checks enabled action availability after comparison. Reuse that same perimeter comparison in create-mode release resolve, against an ancestry-validated delivered commit. Exercise Builds through its existing sample fixture only.

## Boundaries & Constraints

**Always:** Implement in `references/Hexalith.Builds`, with stdlib Python >=3.12 and workflow-owned `$/` composites / `GITHUB_ACTION_PATH` scripts under `python3 -I`. Use `perimeter_config.load_bytes`, `perimeter.Git`/`Snapshot` and `perimeter.compare`; use `ci_config.load_config` for CI JSON, without another parser/validator. Enumerate actual and expected content from pinned Git trees, including sparse paths, never from working-tree files. The perimeter supplies ownership; do not duplicate its path list or nine-kind semantics. Preserve CAP-8, AD-4/8/9/17/19 and existing public interfaces/permissions.

Normal modules read only `https://github.com/Hexalith/Hexalith.CiCd.git`, branch `delivered/<repository basename>`, through an anonymous shallow sparse clone. Identity comes from trusted workflow repository context, never module JSON. Fetch the branch, not a caller-supplied bare SHA. Missing/unreadable expected state fails closed. Anonymous Git processes receive no token, credential helper/header, inherited URL rewrites or executable module configuration; disable hooks, recursion and smudge/LFS execution. Use a separate trusted Builds Git object repository to peel perimeter gitlink tags, because a downloaded action directory need not contain `.git`.

The fixed failure message is `CI/CD is owned by Hexalith.CiCd. Fix the product code, not the pipeline.` Print deterministic owned-content differences and path/mode/gitlink/partial-entry explanations, with diagnostics escaped against control characters and Actions command injection. Preserve loader-specific fixed messages as supporting diagnostics. CI stops before config parsing and product work on drift or unavailable expected state.

Builds root skips both delivered-state guard and release drift lookup. Only Builds may use fixture inputs; `expected-source` requires `module-root`, and a sample comparison requires both. Under `Samples/Hexalith.Sample`, actual perimeter paths resolve in that subtree and expected paths in its committed `expected-source` delivered-layout tree. Enabled hook/job actions always resolve at workspace-root `.github/actions/<name>/action.yml` (AD-14), without executing or YAML-parsing them. Reject symlink/gitlink action metadata as unavailable. Dormant action lint is outside this story.

**Never:** Implement restore, delivery/ref advancement, local `check.py`, custom-action deny-list/audit/commitlint lint, schema changes, module onboarding, release publication or administration. Keep `commitlint-caller.yml` until commitlint actually migrates; stale earlier attribution does not remove existing coverage. Do not change frozen AD-20 runtime, publisher/original-artifact handling, sample imports/actions/Windows delegation, SDK pins or dependency pins. Do not test workflow source text, run a delivered-ref guard on Builds root, initialize nested submodules or execute module code in release resolve.

**Story-specific verification exception (human-approved 2026-11-13):** For story 5-1 only, the all-green implementation/completion gate permits the two failures reproduced on integration revision `05a75b626fb73c6e386d16c41e885f193d3cff16` ([baseline run 43387068103](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43387068103)) and implementation revision `0f97426edb6f88ee6e534d95ca9029f7e0b20311` ([source run 43389324372](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43389324372)): the package-catalog validator's exit 1 with exactly the same 14 normalized EventStore 4.2.0-versus-5.0.0 assertion messages, and Evidence.Tests' exit 2 with exactly the same 44 failing test identities. Compare and retain the actual signatures against the baseline logs; matching counts alone are insufficient. Missing comparison evidence or any new or changed failure blocks verification. Keep these checks and assertions enabled and retain their failing results explicitly. All other required checks must pass, including both complete local Python lanes and completed exact-source hosted Python, sample Linux, dependent Windows and quality/API jobs. Independent review must still run and pass before completion. This exception governs story verification only; runtime and release green-CI requirements retain their existing semantics.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Accepted module | HEAD matches live accepted perimeter; enabled actions exist | Guard succeeds; normal prepare/build/tests follow | No error |
| Owned drift | Changed/missing whole file, unexpected workflow, gitlink/partial/absence violation; malformed CI JSON or unknown schema | Owned diff plus fixed ownership message before module config parsing | Nonzero; perimeter `drift=true`; no later CI work |
| Expected state unavailable | Missing branch/perimeter/source blob, malformed perimeter, clone or tag-resolution failure | Fail closed with contextual diagnostic and ownership message | Nonzero; no config parsing or repair; do not claim a usable repair target |
| Action unavailable | Matching perimeter; an enabled hook or job lacks regular committed `action.yml` at workspace root | Name the missing action and fixed ownership message | Nonzero; `drift=false`; no later CI work |
| Working tree disagrees | HEAD accepted but worktree/index edited, or sparse worktree omits owned files | Guard judges only the requested pinned Git tree | No false drift from worktree state |
| Builds self-test | Root call versus paired sample fixture inputs | Root performs no expected-state I/O; sample compares its committed fixture and checks root actions | Reject fixture controls outside Builds and incomplete/unsafe pairs |
| Release create | Omitted delivered SHA, live tip, or ancestor of live delivered branch | Use live tip when omitted; otherwise exact requested ancestor; compare frozen release SHA | Deepen/unshallow branch history to prove ancestry; no arbitrary SHA fetch |
| Release invalid source | Bad full-SHA syntax, missing object, sibling/future/unrelated supplied SHA | Reject before switch/green CI/publication | Nonzero; never silently fall back to live tip |
| Release drift / kill switch | Create drift with switch true or false | Drift fails before switch/green CI; a false switch cannot hide it | Fixed ownership error; no publication handoff |
| Release complete | Valid marked historical draft, changed delivered state | No expected-state fetch/comparison, old config load or CI check | Preserve original-artifact completion and dispatch-SHA security settings |
| Implementation verification | Exact-source CI retains only the two baseline-matching failures defined above; every other required check passes | Record the known failures under the approved exception and proceed to independent review | Missing signature evidence or any new/changed failure blocks; review must pass before completion |

</intent-contract>

## Code Map

All paths below are relative to `references/Hexalith.Builds`, unless explicitly identified as CiCd paths. Anchors describe the starting revision above.

- `Github/lib/perimeter.py:57,99,685` — `Git`, `Snapshot`, `compare(document, actual, *, expected, rendered_root, builds, selected=None)`; returns sorted `Drift(path, kind, reason)`. Actual subtree can be a Git tree object; the expected snapshot retains its rendered prefix. `apply` is out of scope. The engine already handles all nine kinds, modes, wildmatch and semantic partials.
- `Github/lib/perimeter_config.py:174` — strict `load_bytes(data, source=...)`; schema identity comes from executing code. `schemas/hexalith.perimeter.v1.json` and `Github/lib/tests/fixtures/perimeter-contract.json` are reusable read-only contract evidence.
- `Github/lib/ci_config.py:178` — sole strict CI loader. Materialize a Git blob into a private temporary file for this API; do not hand it a module working-tree path. Trusted repository/sample context controls `buildsTag` requirements.
- `.github/workflows/ci.yml:54` — reserved no-op precedes checkout. Move executable guard after checkout and before `$/Github/ci-prepare`; checkout is acquisition, not a product stage. `Github/ci-prepare/action.yml` and `Github/lib/ci_pipeline.py:116` currently load JSON and initialize dependencies, so neither may precede the guard.
- `.github/workflows/builds-ci.yml:25,36` — existing Builds-root and sample calls; sample already passes both fixture inputs. No new job is necessary. Existing Windows job consumes validated sample outputs.
- `Samples/Hexalith.Sample/expected-source/rendered/Hexalith.Sample.perimeter.json` — `{}` placeholder. Its sibling `Hexalith.Sample/.github/hexalith-ci.json` already matches sample config. Root `.github/actions/after-unit-tests/action.yml` and `.github/actions/sample-windows/action.yml` are sample action locations.
- `Github/lib/release_state.py:160,295,307` — its independent safe bare `Git`, `dispatch_settings`, `resolve`. Current dispatch settings parse before mode selection, with an explicit drift slot afterward. Adapt the underlying bare repository to perimeter Git snapshots; these two Git classes are not interchangeable.
- `Github/release-resolve/action.yml:7` and `.github/workflows/release.yml:6,84` — `delivered-sha` already forwards to resolver. `module-root` exists, but expected-source plumbing does not. Resolve is stdlib-only with contents write / actions read; keep existing token confined to same-repository API reads.
- `Github/lib/tests/test_release_state.py`, `test_release_adapters.py`, `test_release_outcome.py`, `test_ci_pipeline.py`, `test_ci_prepare.py` — real Git histories, local API endpoints and executable composite harnesses to extend. `Tools/ci/run_python_tests.py` discovers `Github/lib/tests` on both interpreter lanes.
- `Tools/ci/README.md`, `Samples/Hexalith.Sample/README.md` — update integration seams and guard behavior. Existing `docs/cicd-4-1-perimeter-contract-and-library-plan.md` establishes the Builds planning-document convention.
- CiCd stories `1-*`, `2-*`, `3-*`, `4-*` — all loaded through context subagents; all done with execution tasks checked. 4-1 shipped as `v5.1.0`, source `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`. 4-2's instruction/deny placeholders remain opaque perimeter data; 4-3 does not create delivered refs and the production setup registry is empty. Use temporary delivered-branch fixtures rather than assuming live module refs exist.

## Tasks & Acceptance

**Execution:**

- [x] `Github/lib/expected_state.py` (new) — acquire/pin the anonymous delivered branch, validate optional delivered ancestry, resolve trusted Builds tags, load perimeter bytes and invoke the existing comparison engine. Expose read-only comparison/report data shared by guard and release; permit injected transports only in test harnesses, with no production remote override. Keep ownership path policy in the supplied document.
- [x] `Github/lib/guard.py` and `Github/guard/action.yml` (new) — provide CLI and isolated composite entrypoints using existing `CI_REPOSITORY`, `CI_MODULE_ROOT`, `CI_EXPECTED_SOURCE` context. Validate fixture controls before bypass; compare pinned HEAD/subtree first, load matching config through the sole loader, and check every enabled hook/job action in workspace HEAD. Emit internal `drift=true` only for actual perimeter drift, otherwise `false`, before failing; missing expected state and action-only errors must not authorize future restore. Report readable deterministic differences and fixed ownership errors.
- [x] `.github/workflows/ci.yml` — replace the no-op with `$/Github/guard` after nonpersistent, nonrecursive checkout and before prepare. Give the step an id and expose its drift flag as a CI-job output for later restore, without adding a public workflow output or write permission. Correct premature commitlint attribution. Preserve existing stages, call outputs and the separate commitlint caller.
- [x] `Samples/Hexalith.Sample/expected-source/rendered/Hexalith.Sample.perimeter.json` — replace `{}` with v1 `entries: [{"kind":"whole","path":".github/hexalith-ci.json"}]`. This exercises a real nonempty guard with existing expected config, without inventing nested Builds gitlinks or managed workflows in the sample. Keep other entry-kind coverage in disposable real module trees.
- [x] `Github/lib/release_state.py` — select/freeze mode and SHA, then run shared perimeter comparison only in create mode for modules or Builds sample. Validate supplied SHA against the live delivered branch; skip all expected-state operations for complete mode and Builds root. Reorder dispatch settings as described below, fail drift before switch/green CI and keep sole outcome ownership and publication gating.
- [x] `Github/release-resolve/action.yml` and `.github/workflows/release.yml` — add optional test-only `expected-source` forwarding for Builds sample and update delivered-sha descriptions. Reject all fixture controls outside Builds, even complete mode; do not give normal callers a bypass. Keep existing permissions, caches, public inputs/outputs and security job conditions.
- [x] `Github/lib/tests/test_expected_state.py`, `test_guard.py`, `test_guard_adapter.py` (new), plus existing `test_release_state.py`, `test_release_adapters.py`, `test_release_outcome.py` — execute matrix cases through real Git branch histories, CLI/composite entrypoints and release resolver; observe exit status, diagnostics, outputs, API/Git calls and successor commands. Include all nine library entry kinds at the shared integration boundary, missing/corrupt expected sources, tag peeling, shallow ancestry, malformed actual config, root actions versus sample subtree, dirty/sparse checkouts and failed-resolve outcome. Prove no credentials, hooks, module code or repair writes run. Update old seam-only assertions; preserve existing complete-mode/security behavior.
- [x] `Tools/ci/README.md`, `Samples/Hexalith.Sample/README.md` and `docs/cicd-5-1-guard-drift-check-results.md` (new at implementation) — document executable guard, source/ancestry semantics and scope; record later focused/dual-Python/lint/API and exact-source hosted sample/Windows results separately. Planning-only commit contains the plan, not fabricated implementation evidence.


**Acceptance Criteria:**

- Given a normal module checkout, when shared CI runs, then its first executable product-validation stage compares HEAD with its own accepted delivered branch before prepare parses JSON, initializes submodules or invokes SDK/build/tests/hooks; both matching and drifted `solution: none` modules receive the same guard enforcement.
- Given an owned edit or missing/invalid expected state, when the guard CLI/composite runs, then it fails with the fixed ownership message and available differences before any successor stage; malformed/unknown-schema module JSON is reported as drift rather than a parser error.
- Given matching owned state, when an enabled hook or job is absent from committed workspace-root actions, then the guard names it, fails before product work and emits no perimeter-drift repair authorization.
- Given an accepted Git tree with dirty/staged/worktree-only changes or sparse paths, when the guard runs against that tree, then the verdict and differences depend only on Git objects and neither index nor working-tree content changes.
- Given Builds' existing two CI calls, when they run, then root performs no delivered lookup, sample enforces the committed nonempty expected-source perimeter and root actions, and unchanged sample Linux/hooks/integration plus dependent Windows job succeed; changing only sample owned config fails the sample call.
- Given non-Builds repository context or an unsafe/incomplete fixture pair, when either runtime entrypoint receives fixture inputs, then it rejects them without bypassing comparison, including complete mode.
- Given a module create release, when delivered-sha is omitted/equal/ancestor, then resolve compares the frozen release SHA with the exact permitted delivered tree; sibling/future/unavailable commits fail without bare-SHA fetching or fallback.
- Given create drift and any publishing-switch value, when resolve runs, then ownership failure precedes switch/green-CI processing, no publication handoff is emitted, and the release reports failed; valid dispatch security settings emitted after completed comparison remain available to existing security jobs.
- Given a valid marked draft, when resolve selects complete mode, then delivered state and historical draft config/CI are never consulted, while current dispatch settings, original artifact recovery and outcome behavior remain intact.
- Given the implementation revision, when existing quality/API and behavioral suites plus exact-source Builds CI run, then the retained public interfaces and product lanes pass except for the two explicitly approved baseline-matching failures in the intent contract; their actual signatures and failing results are retained, every other required check passes, and independent review passes before completion, without workflow-text assertions, changed frozen files or new write permission.

## Spec Change Log

- 2026-11-13: Independent review completed all four layers. Applied six direct correction groups for filtered history, snapshot lifetime, logical diagnostics, branch-race coverage and CI/release caller verification. The intent contract and frozen/pin boundaries remain unchanged. Reviewed source e2bdaca58c95c52e05cb6db77d91ab7ae22ee4a0 passed both complete 822-case local lanes and every required hosted job except the two exact approved baseline matches; no re-derivation or review loopback was required.

- 2026-11-13: Human approved a story-5-1-only verification exception for the baseline-matching 14 catalog assertions and 44 Evidence.Tests failures. All other checks, completed hosted Python lanes and independent review remain mandatory; new/changed failures or missing signature evidence still block. This resolves the all-green gate conflict without changing implementation scope or runtime/release behavior.

- 2026-11-13: Preserved concurrent upstream package-catalog updates by rebasing the implementation onto `05a75b626fb73c6e386d16c41e885f193d3cff16`. Those dependency edits belong to upstream; story code does not edit pins. Implementation commit `0f97426edb6f88ee6e534d95ca9029f7e0b20311` is pushed and its committed-object API check reports 2,581 entries with no removals.

- 2026-11-13: Resumed implementation by explicit user dispatch. The implementation baseline now records the already-pushed planning revision; the earlier integration and planning history remain documented below. The previous planning-only terminal instruction was fulfilled by that run and does not apply to this implementation run.

## Review Triage Log

### 2026-11-13 — Review pass

- verdicts: 17 findings — high 0, medium 4, low 6, false 7, maybe-false 0
- findings:
  - `[medium]` `[patch]` V1: Shared CI enforcement can be removed without the shared-job tests failing. — The verification reviewer removed the guard through an in-memory workflow mutation and all 20 CompositeHarness tests still passed. Add committed sample drift at the real job boundary and assert ownership failure before prepare/build/hooks. Applied: Added committed sample drift through the actual shared workflow and assertions that prepare/build/hooks do not run.
  - `[medium]` `[patch]` V2: Release adapter tests bypass actual delivered-sha and expected-source environment mappings. — The verification reviewer removed both composite mappings and all 12 adapter tests still passed because they injected RELEASE_* variables directly. Evaluate metadata defaults/mappings and execute paired sample and ancestor cases. Applied: The release adapter now evaluates real composite defaults/environment mappings and executes paired-sample and exact-ancestor cases.
  - `[false]` `[reject]` I1: Committed-tree and execution-workspace surfaces differ. — The intent contract explicitly requires pinned Git objects and dirty/staged/sparse independence. Comparing committed state is the requested behavior, and checkout precedes guard in the deployed job.
  - `[false]` `[reject]` I2: Hosted sample coverage has one owned file rather than all nine perimeter kinds. — The story explicitly defines a one-whole-entry sample perimeter and assigns nine-kind coverage to disposable real repositories. Both surfaces are exercised as requested.
  - `[false]` `[reject]` I3: Fixture adapters do not prove an adopted module's live delivered branch. — The dispatched story excludes module onboarding and production release. Actual composites plus hosted Builds/sample verification satisfy its stated integration surface; adoption is not claimed.
  - `[false]` `[reject]` I4: Aggregate diff includes unrelated package pins and superproject gitlinks. — The two package changes are already present in integration revision 05a75b626fb73c6e386d16c41e885f193d3cff16 and unchanged by source 0f97426edb6f88ee6e534d95ca9029f7e0b20311. A concurrent superproject /pushall advanced the other gitlinks; this run did not author them.
  - `[false]` `[reject]` I5: The review diff alone cannot establish current remote delivery or final completion. — Pushed implementation/evidence are verified by Git remote reads and the completed exact-source GitHub run. The review handoff correctly does not claim completion; finalization follows triage and validation.
  - `[medium]` `[patch]` B1: Deepening through the raw remote loses the blob filter. — A filtering-enabled local Git reproduction fetched the unrelated historical blob with unfiltered --unshallow; adding --filter=blob:none kept that blob absent. Retain filtering on deepening. Applied: Deepening now retains --filter=blob:none.
  - `[low]` `[patch]` B2: Comparison.expected exposes a snapshot after its temporary repository has been removed. — Reading an uncached expected blob after compare_repository returned raised ExpectedStateError. No production caller uses this field; delete the unused field/argument and retain durable actual/workspace snapshots plus materialized diagnostics. Applied: Deleted the unused expected snapshot field and constructor argument.
  - `[low]` `[reject]` B3: Multiple partial entries at one path can have indistinguishable explanations. — Two legal absent-line patterns produced the same path/kind/partial diagnostic. The fixed ownership error and violated path remain correct; entry disambiguation would add matching/association logic for an uncommon diagnostic case, so the cosmetic extension is rejected.
  - `[low]` `[reject]` B4: Whole-file symlink drift omits the two target strings. — A real Git symlink mismatch reports the owned path and content reason correctly. The module perimeter uses ordinary managed configuration/workflow files; extra symlink-specific report branches are not justified for this rare cosmetic case.
  - `[low]` `[reject]` B5: Individual Git subprocesses do not have a separate deadline. — Git.run does not set a subprocess timeout; hosted CI/release jobs already have 30/40-minute bounds and fail closed. An additional timeout policy and exception branches for the rare transport stall would add complexity beyond a direct correction.
  - `[low]` `[patch]` B6: Configuration diagnostics expose a random temporary materialization path. — A matching unsupported-schema fixture emitted /tmp/hexalith-guard-config-<random>/hexalith-ci.json. Preserve loader wording while reporting the committed logical path and verify repeated failures are identical. Applied: Loader diagnostics now name .github/hexalith-ci.json; repeated malformed/unknown-schema runs assert stable wording.
  - `[false]` `[reject]` B7: Repository-local URL/header config can steer production anonymous acquisition. — The demonstrated settings remain active only in an existing repository. Production accepted-state and Builds-tag acquisition use fresh private repositories with fixed remotes and stripped global/environment configuration. Actions checkout supplies an unfiltered module tree with persist-credentials=false; no actual-workspace lazy-fetch path carrying those settings is used by these callers.
  - `[medium]` `[patch]` B8: Existing transports do not exercise genuine filtered clone/lazy blob retrieval. — LocalTransport omits filtering and the adapter's file transport has filtering disabled by default. Add a filtering-enabled executed transport regression covering owned lazy reads, deepening and continued absence of unrelated historical blobs; this accompanies B1. Applied: Added a filtering-enabled Git transport regression proving lazy owned reads and absence of unrelated historical blobs.
  - `[low]` `[patch]` B9: Pinned delivered-tip behavior during branch advancement lacks a controlled race regression. — The code freezes tip before deepening and enumerates its ancestors, but existing tests never advance the branch between those operations. Add a direct branch-advance control asserting comparison remains tied to the original tip. Applied: Added a controlled delivered-branch advance during deepening, testing both the pinned ancestor and rejection of the newly advanced commit.
  - `[false]` `[reject]` B10: Early invalid source selection should still recover ordinary-module dispatch security settings. — The spec prohibits parsing ordinary-module config before a completed create comparison, and prohibits expected-state acquisition in complete mode. Ambiguous/invalid draft selection establishes neither mode safely, so fail-closed output suppression is intentional. Builds root alone has no comparison prerequisite and retains its prior recovery.

### 2026-11-13 — Review pass

- verdicts: 38 findings — high 0, medium 5, low 18, false 15, maybe-false 0
- findings:
  - `[medium]` `[defer]` BH1: A create-mode drift still emits CodeQL/nightly-hook settings parsed from the drifted dispatch configuration, and release.yml's security jobs consume them. — Real: `resolve` emits `dispatch_settings` before `require_clean()`, and `codeql`/`nightly-hook` gate only on `config-valid`. Pre-existing: the baseline emitted these settings unconditionally before any check. The AC/Design Notes deliberately keep them for the security jobs, and no publication handoff occurs. Deferred with the needed design decision.
  - `[low]` `[patch]` BH2: delivered-sha syntax validation moved after mode selection and became create-only. — Real: a malformed delivered-sha was silently ignored in complete mode, although the baseline rejected it in every mode and the invalid-source row requires rejection before switch/publication. Applied: `resolve` validates syntax again before `select_release`, inside the Builds-root settings-recovery block. `test_resolve_requires_full_dispatch_and_delivered_commit_identities` now asserts rejection with no API request in both create and marked-draft states.
  - `[low]` `[defer]` BH3: Release `dispatch_settings` diagnostics still leak the random `hexalith-release-config-*` temp path that B6 removed from guard. — Real and reproduced. `dispatch_settings` materializes into the same temp-path pattern at baseline f01c3ab70f7e7401b3b73217983955f7771a1465, and this story did not change it, so it is pre-existing. Deferred.
  - `[low]` `[reject]` BH4: No shared-job test exercises the normal-module guard branch. — Real: `CompositeHarness` fixes `github.repository` to Builds. The module branch is covered at the composite boundary (`test_guard_adapter`, which reads `CI_REPOSITORY`) and the library boundary. The job-level mapping `CI_REPOSITORY: ${{ github.repository }}` is pre-existing and shared with prepare. A regression there is unlikely in everyday use, and closing the gap needs new harness parameters and a delivered-remote shim, which is more than a direct correction.
  - `[false]` `[reject]` BH5: The trust anchor that stops a module re-pinning its caller to a pre-guard Builds is undocumented. — The architecture spine gates nightly release dispatch on live `ci.yml`/`release.yml` equality with `delivered/<Repo>`, and places rulesets in administration. The intent excludes administration and restore. No defect exists at this story's surface.
  - `[false]` `[reject]` BH6: CI is coupled to the live delivered tip, with no pinning or transition story. — The intent requires comparison against the live `delivered/<Repo>` branch. The architecture defines the ordering: advance the ref, then restore modules from it. Delivery and restore are excluded by the intent.
  - `[low]` `[reject]` BH7: Whole-file drift diffs are unbounded, and Unicode format characters such as U+202E pass through `escaped()`. — Real but cosmetic. Owned whole files are small configuration/workflow files, control characters and Actions command prefixes are already escaped, and paths are JSON-escaped. Truncation logic and a new Cf-category guard add complexity for a rare case.
  - `[low]` `[reject]` BH8: A missing delivered branch, an unreachable remote and an outage produce the same acquisition diagnostic. — Real but low. The diagnostic already names the exact `delivered/<Repo>` branch and fails closed. Telling them apart needs an extra remote query plus new branches, while stderr must stay suppressed.
  - `[false]` `[reject]` BH9: The results doc status and revision keys contradict the canonical story. — The results front matter labels `implementation_revision` (0f97426…) and `review_implementation_revision` (e2bdaca…) separately and records the terminal `done`. The story's `in-review` is this follow-up pass's transient status.
  - `[low]` `[patch]` BH10: The results doc's focused test counts (12/16/20/199) are stale and unlabeled. — Real: they are the pre-review counts at 0f97426 but read as current. Applied: the section now names source 0f97426edb6f88ee6e534d95ca9029f7e0b20311 and says these are pre-review counts, with post-review totals in later sections.
  - `[low]` `[patch]` BH11: Committed evidence says local transcripts "remain at" `/tmp` paths that no later reader can obtain. — Real wording defect. Applied: the results doc and JSON normalization rule now call those transcripts session-local and uncommitted, and name the committed arrays/fingerprints and hosted job logs as the durable evidence.
  - `[low]` `[reject]` BH12: Post-review job evidence lacks log fingerprints, and its fingerprint definitions conflict. — Partly false: the post-review catalog and Evidence.Tests failure records carry `logSha256` plus full signature arrays under `postReview.allowedFailures`, and passing jobs need only results. The `decodedLogSha256` name versus the "downloaded bytes" note is a real cosmetic inconsistency. Correcting it would mean re-downloading and re-hashing the historical logs, which is more than a direct correction.
  - `[false]` `[reject]` BH13: The gate exception has no audit trail. — The approval is recorded in the canonical story's intent contract ("human-approved 2026-11-13") and its Spec Change Log, and the JSON records the approval date. Adding more would mean editing this build's spec.
  - `[medium]` `[defer]` BH14: The two baseline failures that keep Builds main red have no follow-up. — Real: the deferred-work ledger has no entry for the 14 EventStore 4.2.0-versus-5.0.0 catalog assertions or the 44 Evidence.Tests failures, and both block Builds' own green-CI release gate. They are pre-existing on integration revision 05a75b626fb73c6e386d16c41e885f193d3cff16, so they are deferred for upstream reconciliation.
  - `[low]` `[reject]` BH15: `test_release_outcome` hand-instantiates `ResolveAdapterTests` and calls `setUp`/`doCleanups`. — Real coupling to fixture internals. It works, since unittest permits the default `runTest` name, and it passes in both lanes. A shared fixture/mixin refactor is not a direct correction for a developer-only risk.
  - `[low]` `[reject]` BH16: Output/diagnostic inconsistencies: a silent guard output without `GITHUB_OUTPUT`, a duplicate `drift` write, and a `guard:` prefix in release diagnostics. — The silent CLI output is intended for local CLI use. The duplicate write is safe because the runner applies `GITHUB_OUTPUT` entries in order and later values overwrite earlier ones. The `guard:` prefix in release resolve is real but cosmetic beside the fixed ownership message, and changing it would add parameterization.
  - `[false]` `[reject]` BH17: The anonymous-Git environment whitelist omits proxy variables, and its Windows entries contradict a POSIX askpass. — Every guard and resolve job is fixed to `runs-on: ubuntu-latest` GitHub-hosted runners with direct egress, with no runner input. The guard never runs in the Windows job, so neither failure occurs on a deployed surface.
  - `[false]` `[reject]` BH18: The Samples README reflow leaves a ragged line. — Lines 13–14 are a soft Markdown line break with no trailing hard-break spaces, so the paragraph renders unchanged.
  - `[low]` `[reject]` EC1: An owned path replaced by a directory, or with a symlinked parent, raises `PerimeterError` in compare and is reported as "comparison unavailable" with `drift=false`. — Real (perimeter `_Plan` raises on unrepairable file/directory conflicts). CI still fails closed with the fixed ownership message and the engine's specific conflict text. `drift=false` correctly claims no usable repair target, because the same conflict blocks `perimeter.apply`. Rewording needs a separate exception branch for a rare case.
  - `[false]` `[reject]` EC2: Ancestry via `rev-list tip` without `--first-parent` admits merged side-branch commits. — The intent and AD define the accepted input as the live `delivered/<Repo>` commit "or one of its ancestors". The delivered ref advances along CiCd `main`, so first-parent would neither match that contract nor exclude unvalidated first-parent commits.
  - `[false]` `[reject]` EC3: The proxy and SSL variables missing from the anonymous whitelist break proxied runners. — The same root and refutation as BH17: the deployed jobs run only on `ubuntu-latest` hosted runners.
  - `[low]` `[reject]` EC4: Git subprocesses have no individual timeout. — carried B5: `Git.run` still has no subprocess timeout, and the hosted 30/40-minute job bounds fail closed. A timeout policy plus exception branches is beyond a direct correction.
  - `[false]` `[reject]` EC5: An enabled action committed as `action.yaml` is reported missing. — The intent explicitly fixes enabled actions at workspace-root `.github/actions/<name>/action.yml` (AD-14). Requiring that exact file is the specified behavior.
  - `[low]` `[patch]` EC6: Builds sample configuration diagnostics name root `.github/hexalith-ci.json` instead of the sample path. — Real: `load_ci` reported the snapshot-relative path. Applied: `load_ci` prefixes `module_root` for both the unavailable and loader-error messages. `test_sample_config_diagnostics_name_the_sample_logical_path` asserts `Samples/Hexalith.Sample/.github/hexalith-ci.json:` and the absence of temp paths.
  - `[low]` `[patch]` EC7: The pre-selection delivered-sha format check was removed. — The same defect as BH2, and the same fix applied.
  - `[low]` `[reject]` EC8: A compare-raised conflict for an owned path keeps `drift=false` instead of reporting drift. — The same root as EC1, with the same verdict and refutation: an unrepairable conflict must not authorize restore, and the guard fails closed with the ownership message.
  - `[medium]` `[patch]` VG1: release.yml's resolve-step forwarding of `delivered-sha`/`expected-source` was never evaluated. Pre-verified: deleting both `with:` lines left all 200 release tests green. Applied: `ResolveAdapterTests.release_inputs` maps workflow inputs through release.yml's real resolve `with:`, with omitted mappings falling back to composite defaults. `test_release_workflow_forwards_delivered_sha_and_sample_pair_to_resolve` executes the sample pair, the exact accepted ancestor and live-tip drift. Mutations removing either line now fail by assertion.
  - `[medium]` `[patch]` VG2: Reverting the resolver to the old prefix-stripped `Git` environment failed no test. Pre-verified mutation. Applied: the adapter Git shim now requires `HOME == os.devnull` and `SSH_ASKPASS == /bin/false`, and the absence of a planted `CI_CUSTOM_TOKEN`. `invoke` plants that token and a poison askpass, and pre-creates the ledger. Reverting `ResolverGit.fetch` to `Git.fetch` now fails by assertion with "Git object operation failed: init".
  - `[low]` `[defer]` VG3: Release resolve still reports the random temp config path. — The same pre-existing defect as BH3, deferred together. The layer's `patch` disposition was weighed, but `dispatch_settings` is unchanged baseline code.
  - `[medium]` `[defer]` IA-D1: Release drift reaches downstream security jobs through settings from the drifted config. — The same root as BH1, deferred together.
  - `[false]` `[reject]` IA-D2: No real or hosted execution of the ordinary-module anonymous clone or create-mode release comparison. — carried I3: the dispatched story excludes module onboarding and production release, and the code and tests still use local transports, shims and the sample fixture as described.
  - `[low]` `[reject]` IA-D3: The shared-job surface covers only root and sample. — The same root as BH4, with the same verdict and reasoning.
  - `[false]` `[reject]` IA-D4: Hosted evidence covers only the matching case, and the duplicate `drift` output is unobserved. — Drift, unavailable-state and missing-action cases run through the actual shared workflow and composite harnesses. Hosted negative cases would require committing drift to Builds main. Runner `GITHUB_OUTPUT` handling is last-value-wins.
  - `[false]` `[reject]` IA-D5: Ordinary-module early resolve failures no longer emit dispatch security settings. — carried B10: suppressing ordinary-module settings before a completed comparison is the specified fail-closed behavior, and the Builds root keeps recovery.
  - `[low]` `[patch]` IA-D6: Complete mode no longer rejects a malformed `delivered-sha`. — The same defect as BH2, and the same fix applied.
  - `[false]` `[reject]` IA-D7: The sample's no-network property depends on its perimeter having no gitlink entries. — The intent requires trusted Builds tag objects for any gitlink entry. The committed sample perimeter has exactly one whole entry by design, so the sample performs no CiCd acquisition.
  - `[false]` `[reject]` IA-D8: The exception names 0f97426, the docs-only head 3d110e0 has no run of its own, and completion preceded this review. — The exception names the revisions where the failures were reproduced. The exact-source signature comparison was repeated at code revision e2bdaca, and 3d110e0 changes only two evidence documents. Independent review ran and passed before completion. This follow-up pass repeats verification for any new code.
  - `[false]` `[reject]` IA-D9: The change surface includes unrelated pins and gitlinks. — carried I4: the pin edits are in integration revision 05a75b626fb73c6e386d16c41e885f193d3cff16, and the other gitlinks come from concurrent superproject synchronization.

### 2026-11-13 — Follow-up delivery review

- verdicts: 18 findings — high 0, medium 7, low 7, false 4, maybe-false 0
- findings (review-layer completion order):
  - `[medium]` `[defer]` EC1: Case-varied consumer names reuse exact-name catalog views. — Confirmed: catalog `.Equals` selection is case-sensitive, while snapshot storage and `ReadRecordedPackageVersion` use OrdinalIgnoreCase. The reviewer evaluated canonical/lowercase names and observed SDK4.2 versus SDK5. Already present in upstream integration `cae351e20093634483afad16aca3bfd90845eda8`; grouped with BH2 for the owning catalog workstream.
  - `[medium]` `[defer]` BH1: No-snapshot package lookup chooses the first conditional SDK4.2 declaration. — Confirmed `ReadCatalogPackageVersion` uses `Descendants(property).FirstOrDefault()`, and the first SDK declaration is conditional 4.2.0 while default OpenAPI declarations are 11/3. This predates the story-authored follow-up at the upstream integration; recorded separately.
  - `[medium]` `[defer]` BH2: Case-insensitive snapshot lookup disagrees with new exact-case selectors. — Confirmed the same bad outcome as EC1 from snapshot construction through the public lookup; grouped with EC1. This is an upstream catalog issue and neither file is changed by source `185e3a4e695f392e114eacffbdecd2a23da32c9b`.
  - `[medium]` `[defer]` BH3: Python catalog selector discovery does not recognize `.Equals`. — Confirmed the regex accepts quoted equality only and `runtime_toolchain_v2.inventory` uses default versions when a name is omitted. The C# reader alone was updated upstream. Recorded for that existing inventory workstream.
  - `[low]` `[defer]` BH4: Current runtime facade now follows a frozen literal. — Confirmed `CompositionToolchainPins.DaprRuntimeVersion` delegates to `SupportedPlatformPins` and the prerequisite probe documents a current catalog default. Current values agree; a future approved runtime bump would expose the mismatch. This upstream authority-coupling issue is grouped with BH9.
  - `[medium]` `[defer]` BH5: Active compatibility versions lack current conditional-selection audit records. — Confirmed current audit rows bind default SDK5/OpenAPI11/3/OpenIdConnect11 selections, while retained selections only have historical observations where present. The missing current view-bound provenance predates this authored follow-up and belongs to upstream package auditing.
  - `[low]` `[reject]` BH6: The independent host verifier checks thirteen SDK-prefixed rows rather than exact identities. — Real hardening opportunity, but replacing an identity is not an everyday consumer path; enforcement would introduce a separate canonical identity set and new mutation controls. No source identity is changed by this story, so the extra verifier policy is not warranted here.
  - `[low]` `[reject]` BH7: Positive/negative catalog probes do not assert the entire non-host selector allowlist. — Real future verification limitation. Current named views are checked, and enforcing every possible added name needs new selector-validation policy and branches. Such an unrecorded selector edit is unlikely in everyday use; no change is justified for this low-severity case.
  - `[low]` `[reject]` BH8: Clean catalog probes inherit explicitly poisoned version/MSBuild environment variables. — Confirmed this helper launches `dotnet` directly, unlike the separately isolated packaged-host verifier. Hosted checks pass with ordinary environments; adding a new process/environment abstraction for this uncommon developer-test setup is more than a direct correction.
  - `[low]` `[defer]` BH9: Some frozen-pin tests still require equality with the moving catalog. — Confirmed the three Dapr/FrontComposer current/frozen equality assertions. They currently pass but would reject an approved independent current-catalog update. Grouped with BH4 as incomplete upstream separation of current/frozen authorities.
  - `[low]` `[reject]` BH10: Transcript fingerprints become unverifiable after local/hosted log expiry. — Real long-term archival limitation. The committed text correctly labels local logs session-local and retains source identities, results and fingerprints; no current retrievability promise is false. Durable archival infrastructure adds retention/artifact policy for a rare later replay need, so it is not added.
  - `[false]` `[reject]` IA1: Ordinary-module expectations are exercised through local adapters rather than a live adopted module. — carried I3: onboarding and production adoption are explicitly excluded. Disposable real Git histories, executed composites and hosted sample verification are the specified surfaces.
  - `[false]` `[reject]` IA2: Reusable release forwarding is simulated rather than run through the hosted scheduler. — The new test evaluates the real `with:` mappings and executes the real composite; removing either forwarding entry fails the behavior check. Production release dispatch and downstream scheduling are excluded, so their absence is not a missing story acceptance surface.
  - `[false]` `[reject]` IA3: Hosted sample owns one configuration file while all nine kinds run locally. — carried I2: that exact nonempty sample perimeter and disposable nine-kind library integration split are required by the intent; both passed.
  - `[low]` `[defer]` IA4: Release configuration errors still expose temporary paths. — carried BH3/VG3: unchanged baseline `dispatch_settings` behavior, already deferred. No duplicate deferred entry or patch is added.
  - `[medium]` `[defer]` IA5: Drift blocks publication while dispatch settings can still steer security jobs. — carried BH1/IA-D1: the recorded design explicitly preserves current dispatch settings after comparison. The pre-existing security-job policy decision remains deferred without duplication.
  - `[false]` `[reject]` IA6: Aggregate diff changes pins/frozen facades/publisher behavior despite story exclusions. — carried I4: commit history proves those changes are separate upstream integration; the authored `cae351e20093634483afad16aca3bfd90845eda8..185e3a4e695f392e114eacffbdecd2a23da32c9b` diff is the seven recorded files and changes no excluded surface.
  - `[medium]` `[defer]` VG1: Automatic response-file isolation lacks a consumer-authority regression. — Pre-verified: removing `-noAutoResponse` passes all 23 central-validator scenarios, and a poisoned ancestor response file then makes actual/expected consumer maps agree on 9.9.9 instead of 1.2.3. The filed patch disposition is appropriate to the owning catalog change; this isolation fix and gap already exist in upstream integration, so this story records the separate follow-up.

No finding routes to intent_gap, bad_spec or patch. Six new upstream deferred root causes are recorded above; two release findings retain their earlier deferred decisions. This pass applied zero high, medium or low patches. No new story runtime verification is needed because the reviewed guard/release source remains byte-identical to the fully verified source.

## Design Notes

Comparison and action availability are separate: release uses the drift comparison only; guard adds action checks after a match. Keep the public perimeter engine unchanged. A downloaded `$/` action has trusted source files but is not necessarily a Git clone, so acquire tag objects from the fixed Builds remote independently of module gitlink/worktree state. Expected branch data is read through Git objects even when sparse checkout omits it.

Release ordering is deliberately precise: select mode/source; in create mode complete the perimeter comparison before parsing dispatch JSON; retain any drift verdict; load and emit valid **dispatch-SHA** security settings; reject drift; then evaluate switch and create-mode green CI. If drift and config decoding both fail, the ownership diagnostic wins. If missing/invalid expected state prevents comparison, fail immediately before parsing and do not fabricate security settings. Complete mode parses dispatch settings only, never historical draft settings. Preserve existing dispatch-security outputs on other resolver failures where possible, without making a pre-comparison config read.

Historical 2-6 prose and the CI placeholder attributed commitlint migration to 5-1, but the dispatched entry explicitly scopes this story to perimeter/action existence and release drift. Keep independent commitlint coverage until its replacement actually runs. Other continuity limitations remain separate: cross-repository `$/` observation awaits first adoption; the sample cannot validate a normal module's live delivered ref; writers' older-Git attribute compatibility is irrelevant to this read-only story. No new production release or adoption is required for validation.

Before planning delivery, Builds fast-forwarded to the recorded integration revision, which adds unrelated attached-lifecycle test coverage and README clarification. Its guard/perimeter/CI/release surfaces are unchanged. Preserve those already-pushed upstream changes and distinguish them from this story's authored diff when comparing against the original implementation baseline.

## Verification

Run from the Builds root during implementation, using its locked test dependencies and existing read-only online-audit credentials:

- `python3 -m unittest discover -s Github/lib/tests -p 'test_perimeter*.py' -v` — existing nine-kind engine/loader behavior remains green.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and the same command with the captured runner Python path — both complete suites, including executed guard/release adapter regressions, pass.
- `python3 Tools/ci/lint_workflows.py` — pinned actionlint/zizmor and online audits pass without widened exceptions.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` — API additions preserve the existing surface; run against committed implementation Git objects.
- `git diff --check` and an explicit diff against `implementation_baseline_revision` — no whitespace faults, frozen runtime changes or unrelated scope.
- Observe the implementation commit's normal `builds-ci.yml` push run at its full SHA, including guarded sample and dependent Windows success. Record its run link and actual job results in the implementation results file; do not substitute workflow-text checks. This planning run does not dispatch, publish or claim those future checks passed.
- Apply the human-approved exception in the intent contract only after retaining the baseline/current signature comparison and the final results of all other required jobs, including both hosted Python lanes. Preserve the two known failures as failures in the evidence; proceed through independent review only when every other verification requirement is satisfied.

Implementation delivery: implement and verify the tasks above, commit/push in Builds after exact-message pinned commitlint validation, and record exact-source hosted validation. Stage the canonical CiCd story and updated Builds gitlink together; leave the superproject commit/push to the caller. The prior planning delivery is preserved below as history.

## Matrix Test Audit

All ten runtime matrix rows and the implementation-verification row are satisfied at source `185e3a4e695f392e114eacffbdecd2a23da32c9b`. Both exact-source local lanes and both hosted lanes passed 14/14 groups and 824 test cases with no skips. The parent independently checked the source/transcript/hosted-log fingerprints and the successful execution of all 22 named matrix/follow-up regressions in each local transcript. All seven hosted jobs passed; no historical failure exception was needed. Four independent review layers completed with no required story patch. Historical 817/822-case runs and baseline-failure signatures remain preserved below and in the evidence JSON.

| Matrix row | Passing tests |
|---|---|
| Accepted module | `test_guard_adapter.GuardAdapterTests.test_matching_none_module_executes_successor_through_anonymous_branch_clone` |
| Owned drift | `test_guard.GuardTests.test_owned_malformed_or_unknown_schema_fails_before_ci_loader_and_emits_drift`; `test_expected_state.ExpectedStateTests.test_all_nine_kinds_use_the_existing_perimeter_contract_and_tag_repository` |
| Expected state unavailable | `test_expected_state.ExpectedStateTests.test_missing_branch_manifest_blob_and_invalid_manifest_fail_closed`; `test_expected_state.ExpectedStateTests.test_corrupt_manifest_bytes_and_missing_expected_blob_fail_closed`; `test_guard.GuardTests.test_missing_expected_state_never_parses_config_or_authorizes_restore` |
| Action unavailable | `test_guard_adapter.GuardAdapterTests.test_symlink_and_gitlink_action_metadata_are_unavailable_without_execution` |
| Working tree disagrees | `test_expected_state.ExpectedStateTests.test_pinned_head_ignores_dirty_staged_and_sparse_worktree_content`; `test_guard_adapter.GuardAdapterTests.test_head_verdict_ignores_staged_dirty_and_omitted_worktree_files` |
| Builds self-test | `test_guard_adapter.GuardAdapterTests.test_builds_root_does_no_expected_acquisition_and_sample_reads_root_actions`; `test_guard.GuardTests.test_sample_compares_committed_subtrees_and_resolves_actions_from_workspace_root` |
| Release create | `test_release_state.ReleaseStateTests.test_explicit_delivered_ancestor_uses_exact_tree_and_deepens_by_branch`; `test_release_adapters.ResolveAdapterTests.test_module_explicit_ancestor_is_compared_exactly_after_branch_history_acquisition` |
| Release invalid source | `test_expected_state.ExpectedStateTests.test_sibling_and_future_commits_are_rejected_using_only_delivered_branch_history`; `test_release_state.ReleaseStateTests.test_missing_or_unrelated_delivered_sha_never_falls_back_to_tip` |
| Release drift / kill switch | `test_release_state.ReleaseStateTests.test_create_drift_fails_before_switch_or_ci_with_dispatch_security_settings`; `test_release_outcome.OutcomeAdapterTests.test_real_drifted_resolve_retains_reporter_ownership_and_reports_failed` |
| Release complete | `test_release_state.ReleaseStateTests.test_complete_mode_never_acquires_expected_state_even_with_changed_accepted_branch`; `test_release_adapters.ResolveAdapterTests.test_module_complete_uses_current_security_settings_without_delivered_lookup` |
| Implementation verification | [Exact-source verification evidence](../../../../references/Hexalith.Builds/docs/cicd-5-1-guard-drift-check-verification.json): all seven hosted jobs and both complete local lanes passed at `185e3a4e695f392e114eacffbdecd2a23da32c9b`; historical exception signatures retained, unused |

## Historical implementation verification handoff

The implementation remains the already-pushed Builds commit `0f97426edb6f88ee6e534d95ca9029f7e0b20311`; the resumed handoff required evidence updates only. The [exact-source run](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43389324372) completed with five successful jobs and the two explicitly retained failures. Hosted Python 3.12.16 and runner Python 3.14.4 each passed all 14 groups. The runner job completed at 08:22:27 UTC on 2026-11-13. Sample guard/build/units/root hook/integration, dependent Windows and workflow/API verification passed.

Re-fetched baseline/current logs establish exact equality of the full 14 catalog assertions and all 44 Evidence.Tests identities, including parameterized cases, and preserve exits 1 and 2. The committed JSON record retains both arrays, normalization rules, log fingerprints and completed job/step results. The overall hosted conclusion remains `failure`; the approved exception applies only to story verification and does not alter release green-CI requirements. The authored source diff changes neither failing validator, its catalog nor Evidence.Tests. No runtime, assertion, dependency pin or frozen file was changed in this resumed handoff.

Both original complete local Python transcripts, the 58-test perimeter result, authenticated lint, committed-object 2,581-entry API result and exact-message pinned commitlint evidence remain retained and fingerprinted. The [updated Builds results](../../../../references/Hexalith.Builds/docs/cicd-5-1-guard-drift-check-results.md) record this historical pre-review handoff; the final reviewed result follows below.

## Follow-up implementation verification handoff

The recorded follow-up corrections were preserved and delivered as Builds source
`185e3a4e695f392e114eacffbdecd2a23da32c9b`, over the separately authored upstream
integration `cae351e20093634483afad16aca3bfd90845eda8`. The seven-file authored
diff restores early delivered-SHA syntax validation in every release mode,
reports sample configuration diagnostics with their committed logical path,
executes release-workflow input forwarding, and asserts the strict anonymous
resolver Git environment. Historical count and transcript descriptions were
clarified. Frozen runtime, schemas, dependency pins, publisher behavior and
sample imports/actions/Windows delegation were unchanged by this follow-up.

Both complete local Python lanes were repeated at the committed source and
passed 14/14 groups with 824 test cases each and no skips (Python 3.12.13 and
runner 3.14.4). The 58 perimeter tests, authenticated pinned workflow lint,
registry signature audit, exact-message pinned commitlint, whitespace/scope
checks and committed-object public API check passed. The API result is 2,589
entries with no removals against `v5.2.1`.

The normal [exact-source push run](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467144)
completed successfully with all seven jobs passing: both complete Python lanes
(3.12.16 and 3.14.4; 824 cases each), guarded sample Linux, dependent sample
Windows, workflow lint/API, catalog contracts and Builds .NET tests. The latter
passed Evidence 191, Module 3,086 and Tooling integration 13 tests with zero
failures. The separate [Commitlint run](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467014)
also passed. The earlier catalog/Evidence failure signatures remain historical
evidence; those failures are absent at this source, and no verification
exception was used.

Evidence-only Builds commit `4dffd595e54699320d483edc1f27aff9b62ed8ca` retains the
completed job/step records, all seven hosted-log fingerprints, repeated local
lane fingerprints and source identities in the existing results/verification
documents. Local transcript paths describe session-local, uncommitted files.
The required independent review of this follow-up remains pending; this
implementation handoff does not claim that review has run or mark the story
complete. The two previously deferred release behaviors remain unchanged.

## Auto Run Result

Status: done

Completed story 5-1 in Builds using the existing 4-1 perimeter engine and loader. Shared CI guards pinned committed ownership before configuration/product stages, checks enabled root actions after comparison, and exercises Builds through `Samples/Hexalith.Sample/`. Create-mode release resolve uses the same read-only comparison against the exact accepted delivered commit; complete mode keeps its existing bypass/recovery behavior.

This resumed run preserved the original implementation and delivered the recorded review corrections as source `185e3a4e695f392e114eacffbdecd2a23da32c9b`, integrated over separately authored upstream `cae351e20093634483afad16aca3bfd90845eda8`. The starting Builds revision was `3d110e06b286acbc6f5aae33fa7eb571e9268b0c`. The complete combined diff was retained and reviewed, with source authorship established from Git history.

Changed files in this follow-up (Builds-relative):

- `Github/lib/expected_state.py` — report sample loader failures using the committed logical path.
- `Github/lib/release_state.py` — reject malformed delivered SHA syntax before mode selection in every mode.
- `Github/lib/tests/test_guard.py` — execute the sample logical-diagnostic regression.
- `Github/lib/tests/test_release_adapters.py` — execute actual workflow input mappings and assert strict anonymous Git environments.
- `Github/lib/tests/test_release_state.py` — verify malformed identities fail before API/source selection in create and complete states.
- `docs/cicd-5-1-guard-drift-check-results.md` — retain correction, verification and independent-review results.
- `docs/cicd-5-1-guard-drift-check-verification.json` — retain full source/job identities, test results and log fingerprints.

All four independent review layers ran. Their 18 findings were individually triaged above: 10 deferred finding rows (six new upstream root causes and two carried release issues), eight rejected rows, zero patches. Each rejected reason is retained in the triage log. No intent gap or bad specification remains. Follow-up review recommended: false; patched counts high 0, medium 0, low 0; no unverified story-specific risk was identified.

Verification passed: both complete local locked Python lanes at the committed source (824 cases each, 14/14 groups, no skips), 58 perimeter tests, authenticated pinned actionlint/zizmor/online audits, registry signatures, exact-message pinned commitlint, committed-object public API (2,589 entries, no removals against `v5.2.1`), whitespace and authored-scope inspection, and all seven jobs of [exact-source Builds CI](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467144). The separate [Commitlint workflow](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467014) passed. The parent independently matched retained source/log fingerprints, checked successful matrix regression lines, and confirmed the run's completed success/full SHA through GitHub. No story-owned guard/release runtime changed after that verification.

Residual risks are the two previously deferred release behaviors and the separately recorded upstream catalog follow-ups. Historical BH14 (red catalog/Evidence CI) is resolved by the preserved upstream fixes: current catalog and all 191 Evidence.Tests pass. The earlier failure arrays remain historical; the story-specific exception was not used.

Builds source and verification evidence are committed and pushed. Final review metadata is delivered in documentation-only Builds commit `7db81f4f19bef5e5337d241abc4bbff98ef62c4c`. The canonical story and updated Builds pointer are staged together in CiCd; superproject commit/push remains with the caller as the implementation-delivery instruction specifies.

The final divergence check also preserved independently authored upstream catalog commit `9bbe8380c13094ddf41cfd780e3a69289e94b9d4`. It changes no guard/release source, shared CI/release workflow or sample file. Exact-source story verification remains bound to `185e3a4e695f392e114eacffbdecd2a23da32c9b`; the late upstream C# work is outside that claim.
