---
title: 'Guard drift detection and the release drift check'
type: feature
created: '2026-11-13'
status: in-progress
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: db053a530db7c8b69f73e742b6e76d7b13b92f44
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: f01c3ab70f7e7401b3b73217983955f7771a1465
implementation_integration_revision: 05a75b626fb73c6e386d16c41e885f193d3cff16
implementation_revision: 0f97426edb6f88ee6e534d95ca9029f7e0b20311
implementation_evidence_revision: 2ecffe8bf5258c3a5b02e58ae8cfad8ab9d77071
context:
  - _bmad-output/specs/spec-cicd/SPEC.md
  - _bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md
warnings: [oversized]
deferred: []
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

- 2026-11-13: Human approved a story-5-1-only verification exception for the baseline-matching 14 catalog assertions and 44 Evidence.Tests failures. All other checks, completed hosted Python lanes and independent review remain mandatory; new/changed failures or missing signature evidence still block. This resolves the all-green gate conflict without changing implementation scope or runtime/release behavior.

- 2026-11-13: Preserved concurrent upstream package-catalog updates by rebasing the implementation onto `05a75b626fb73c6e386d16c41e885f193d3cff16`. Those dependency edits belong to upstream; story code does not edit pins. Implementation commit `0f97426edb6f88ee6e534d95ca9029f7e0b20311` is pushed and its committed-object API check reports 2,581 entries with no removals.

- 2026-11-13: Resumed implementation by explicit user dispatch. The implementation baseline now records the already-pushed planning revision; the earlier integration and planning history remain documented below. The previous planning-only terminal instruction was fulfilled by that run and does not apply to this implementation run.

## Review Triage Log

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

All ten runtime intent-matrix rows have executed, passing behavioral coverage in the focused Python 3.14.4 transcripts. These tests inspect Git objects, actual CLI/composite execution, API/Git calls and downstream execution, not workflow source text. Both complete interpreter lanes subsequently passed all 14 groups and 817 tests each without skips. Hosted guarded sample and Windows verification passed; independent upstream product failures prevented the overall verification gate from passing at the implementation halt. The implementation-verification row added during resolution requires the signature comparison and completed job evidence described above; this resolution claims no new test execution or completed review.

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

