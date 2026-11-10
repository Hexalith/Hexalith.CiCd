---
title: Release gate jobs and the outcome
type: feature
created: '2026-11-10'
status: ready-for-dev
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 8c43e667064d3c8452fc5612e93d822d07114a2d
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: ec97b6be56b46795ffd454067b72dc0ff4b14b3a
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/references/Hexalith.Builds/docs/cicd-3-2-release-gates-plan.md'
warnings: [oversized]
deferred: []
---

# Release gate jobs and the outcome

<intent-contract>

## Intent

**Problem:** Builds has the shared CI and completed publication spike, but no new reusable release gates or machine-readable release outcome. A release must select one source commit, respect its CI and the strict publishing switch, and report security/hook failures even when publishing is disabled.

**Approach:** Add the reusable `release.yml` resolve, CodeQL, nightly-hook and final outcome jobs, backed by trusted stdlib helpers and the versioned outcome schema. This invocation creates and delivers the plan only; implementation is a later dispatch.

## Boundaries & Constraints

**Always:** Follow CAP-12/14 and AD-9/11/14/16/17/18/20. Implement in `references/Hexalith.Builds`. `resolve` runs only trusted stdlib Python >=3.12 and git, with exactly `contents: write` and `actions: read`; no npm, uv, pip, third-party Python, module scripts or publish credentials run there. The existing `ci_config` loader is stdlib and remains the sole CI-config reader. Keep current-dispatch configuration separate from the selected release SHA. Both nightly jobs use `github.sha`, including complete mode and every switch value. `nightly-hook` uses 2-6's existing Linux `$/Github/prepare`, then literal `./.github/actions/nightly`; pass only the named registry pull pair.

New workflows declare `permissions: {}`, per-job permissions and `cache-mode: none`; no expression appears inside `run:`. CodeQL gets `contents: read` and `security-events: write`; nightly-hook gets `contents: read`. Resolve helpers through the workflow's own `$/` composites and `GITHUB_ACTION_PATH`, never through the module's Builds gitlink. Checkouts retain no credentials and initialize no recursive submodules. Concurrency belongs to a top-level caller. Preserve the original-artifact, nested NuGet/login and excluded signed-provenance decisions from 3-1.

**Never:** Implement the 5-1 perimeter/drift check, version/build/draft/publication stages, scheduler, caller migration or environment administration in this story. Preserve frozen module-used runtime files, the legacy `builds-release.yml`, `codeql.yml`, current Builds CI CodeQL call, package/release configuration and existing sample behavior. Their replacements ship in later stories. Do not claim drift protection before 5-1 or release completion before downstream stages exist. Do not add workflow-source assertion tests, publisher secrets, OIDC or attestation permission to these gate jobs.

For this invocation, commit and push only the Builds plan document. Stage the canonical story and updated Builds gitlink together in CiCd; do not commit/push CiCd. Leave runtime implementation tasks unchecked and halt at `ready-for-dev`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Wrong ref | `github.ref` other than `refs/heads/main` | No publication authorization | Resolve and final outcome fail |
| Create | No marked draft | Freeze `sha=github.sha`, `mode=create` | More recent pushes never change that SHA |
| Complete | Exactly one valid marked draft | Freeze its SHA and `mode=complete`; expose its identity/version | No CI check or config load from historical draft SHA |
| Invalid drafts | Multiple marked drafts, or invalid bot-authored trailer-bearing draft | Name offending draft(s), touch none | Resolve fails; ordinary unmarked drafts remain untouched |
| Disabled | Switch exactly `false` | Log `publishing disabled`; security/hook still run | `disabled` only if resolve and enabled gates pass |
| Invalid switch | Unset or any string other than `true`/`false` | `HEXALITH_RELEASE_PUBLISH_ENABLED must be exactly true or false` | Failed outcome; valid current-SHA nightly settings remain usable |
| Red CI | Create mode; no exact-source qualifying CI or latest conclusion not success | `main is red, nothing released` | Fail; unfinished run polled every 60 s for at most 30 min |
| CI selection | Several SHAs/events/workflows or older green followed by red | Latest `ci.yml` run for release SHA with event push/manual governs | Reject arbitrary workflow override; only Builds may use `builds-ci.yml` |
| Security | Open high/critical alert, most recent category starts `hexalith-release/` | Block the release after processed analysis | Closed/lower/unrelated alerts do not block; API/analysis errors fail |
| Hook | Enabled nightly hook, including disabled or complete release | One prepare/build/environment sequence at dispatch SHA, then hook | Preparation/hook failure fails run; absent hook setting is dormant |
| Empty languages | Valid `codeql: []` | CodeQL job intentionally skipped | No empty-matrix evaluation failure |
| No publication | Explicit later no-version decision or stale-draft deletion | `nothing`; disabled path is `disabled` | Missing/unexpected job results never imply a successful no-op |
| Publication handoff | Later validated draft authorizes `publish=true` | Reusable reporter does not upload; publisher owns outcome | A failed/cancelled prerequisite must prevent handoff |
| Early error/cancellation | Resolve emits no selected SHA, or a required job cancels | Use dispatch SHA until selected SHA is known; report `failed` when possible | A cancellation preventing upload remains unsuccessful to nightly |
| Intermediate enabled path | Gates pass, but version/build/draft not installed in 3-2 | `publish=false`, failed outcome with explicit incomplete-pipeline diagnostic | Never invent `nothing to release` or a publishable artifact |

</intent-contract>

## Code Map

Paths are Builds-relative unless prefixed with CiCd. Three read-only investigation agents supplied runtime, prepare/CodeQL and architecture maps; the parent checked key reuse surfaces.

- CiCd spine AD-16 (`:365`), AD-17 (`:384`), AD-18 (`:432`, `:462`) and Consistency Conventions (`:591`) define marked drafts, exact-source CI, permission separation, outcomes and nightly execution. `pipeline-stages.md` supplies release order. All prior story Code Maps, Design Notes, change logs, task states and Auto Run Results were loaded. Stories 2-3/2-6 and 3-1 are done; unrelated Windows/CI and spike-credential deferred work remains outside scope.
- `.github/workflows/release.yml` and `schemas/hexalith.release-outcome.v1.json` do not exist at the implementation baseline. Add them; do not adapt frozen `.github/workflows/codeql.yml` or the legacy `.github/workflows/builds-release.yml`.
- `Github/lib/ci_config.py:71,178` — strict `validate_config`/`load_config`, trusted repository context, no reader defaults; vocabulary at `:20`. Read the dispatch-SHA config with this loader before publication gates. Complete mode must not read the old draft's config.
- `Github/prepare/action.yml:19,25,55,64` and `prepare_linux.py:17` — existing event-SHA checkout, direct-submodule preparation, SDK, single restore/build and shared Linux environment. No new prepare input or implementation is required. `Github/ci-environment/action.yml:19` consumes `REGISTRY_PULL_USERNAME`/`REGISTRY_PULL_PASSWORD`.
- `Github/lib/ci_pipeline.py:115,152,421` — config preparation, direct-gitlink initialization and safe output writing. Reuse where applicable; resolve must not invoke build/SDK preparation just to load config.
- `Github/lib/publish_spike.py:115` — tested no-redirect authenticated urllib pattern. Reuse the pattern, not its spike repository/identity constants or spike artifact protocol. Production helpers must be module-agnostic.
- `Github/lib/tests/test_ci_environment.py:33` — executable composite harness; `test_ci_prepare.py:312,448,470` covers prepare effects/failures. Its current stop-on-error behavior does not prove Actions `always()` scheduling; use hosted evidence for the job graph.
- `Tools/ci/run_python_tests.py:20` discovers new `Github/lib/tests` automatically; its lock already supplies CI-only PyYAML/jsonschema. `Tools/ci/lint_workflows.py:111`, `check_public_api.py:65,80` and README provide locked lint, schema/API and dual-interpreter commands. API checks read committed Git objects.
- `package.json`, `package-lock.json`, `commitlint.config.mjs` pin commitlint 21.2.4. `.editorconfig` and `.gitattributes` govern authored bytes. Baselines above were read directly with Git; the review diff must later include both repositories from those respective revisions.
- `docs/cicd-3-2-release-gates-plan.md` — this invocation's Builds-local delivery and implementation companion; the id-keyed CiCd file remains canonical workflow state.

## Tasks & Acceptance

**Execution:**

- [ ] `Github/lib/release_state.py` — add trusted runtime API/Git utilities, one shared highest-reachable stable-tag helper, marked-draft validation and SHA/mode resolution. Handle annotated tags, ancestry, pagination, excluded draft tag and no-tag bootstrap (`1.0.0` only). Ignore unmarked drafts; fail named malformed bot drafts or multiple valid drafts. Read repository objects as data without executing checkout hooks, filters, submodules or module code; keep credentials out of Git/log output.
- [ ] `Github/release-resolve/action.yml` and `Github/lib/release_state.py` — expose validated current-dispatch CodeQL/hook settings before kill-switch/CI failure, then selected `sha`, `mode`, `enabled` and complete-draft metadata. Add `delivered-sha` integration seam for 5-1 and guarded `ci-workflow` input defaulting to `ci.yml`. Order selected SHA, future drift slot, exact switch, create-only CI. Use an injected clock/sleeper for bounded wait tests and fail API errors visibly. No drift-check success claim or placeholder implementation.
- [ ] `Github/lib/release_security.py` and `Github/release-security/action.yml` — add paginated stdlib alert check after successful CodeQL upload/processing. Filter open high/critical security severity by most-recent-instance release category, leaving unrelated configurations nonblocking. Fetch/error handling must fail visibly rather than treat unavailable findings as empty.
- [ ] `schemas/hexalith.release-outcome.v1.json`, `Github/lib/release_outcome.py` and `Github/release-outcome/action.yml` — define and validate the closed draft-2020-12 contract, `$id=https://hexalith.com/schemas/hexalith.release-outcome.v1.json`, required `schema: "hexalith.release-outcome.v1"`, full commit `sha`, and outcome enum `published|ready|nothing|disabled|failed`. Include unprefixed stable `version` whenever known; `ready` requires positive integer `draftId` and `lastTag` (stable `vX.Y.Z`, or empty string when no tag). Add failure-first result reduction, explicit no-op reasons and exclusive publisher handoff. Runtime validation is stdlib; test corpus uses the independent JSON Schema validator.
- [ ] `.github/workflows/release.yml` — wire `workflow_call` resolve, CodeQL matrix, nightly-hook and final outcome jobs, with explicit optional named pull secrets and guarded CI-workflow input. Surface resolved SHA/mode and a string `publish` output, currently `false`. Configure CodeQL v4.39.3 at its verified full upstream commit, `build-mode: none`, `hexalith-release/<language>`, and wait for SARIF processing before checking alerts. Use dispatch SHA for checkout and current config, including when resolve fails after emitting valid settings; use `always()` job scheduling plus intentional-disable conditions, not an ordinary success-only `needs` chain. Nightly invokes existing prepare and the fixed root hook. The final `if: always()` reporter uploads only `outcome.json` as `hexalith-release-outcome`, with `overwrite: true`; ensure upload still happens after a failed outcome decision and the job/run stays failed.
- [ ] `Github/lib/tests/{test_release_state,test_release_security,test_release_outcome}.py` and `Github/lib/tests/fixtures/release-outcome.json` — exercise the matrix using disposable Git histories, paginated local HTTP/API controls and executed adapters; cover redirects/credential boundaries, deadlines, config at dispatch SHA versus draft SHA, schema/stdlib agreement, failure precedence, legitimate skipped jobs and single-writer handoff. No workflow-text assertions.
- [ ] `.github/workflows/release-gates-probe.yml`, `.github/actions/nightly/action.yml` and `Tools/ci/probe_release_gates.py` — create an implementation-time manual Builds-only caller and minimal hook fixture. Reuse `Samples/Hexalith.Sample` through guarded test-only `module-root`; temporarily enable its nightly hook in `Samples/Hexalith.Sample/.github/hexalith-ci.json` and matching expected-source config, then restore both files after the probe. The hook may read a probe dispatch input to exercise intentional failure. Reject fixture inputs outside Builds; keep them outside public module API. Observe the existing repository switch without changing it; prove a real CodeQL matrix/processed-alert query, current-SHA preparation/hook and final reporting after hook failure. Exercise switch variants, red CI and complete-mode selection through executable local controls; claim hosted branch coverage only for branches actually observed. Remove temporary workflow/action/probe scripts after retaining sanitized exact-source evidence in `docs/cicd-3-2-release-gates-results.md`. Do not create live vulnerable findings or publish artifacts to registries.
- [ ] `Tools/ci/README.md` and `docs/cicd-3-2-release-gates-results.md` — document public caller permission union, current/release SHA separation, safe intermediate behavior, later draft/publish/outcome handoff and 5-1 drift slot. Record focused and dual-Python checks, real lint/API checks, frozen-file comparison and hosted evidence; distinguish controls from live observations.
- [ ] Builds Git, this story and CiCd gitlink — on implementation dispatch, review both repository deltas, validate exact messages, commit/push Builds and verify its remote revision; stage the updated gitlink with canonical story. This planning invocation delivers only the companion plan and records its exact commit below.

**Acceptance Criteria:**

- Given a manual caller on `main` with disabled publishing, when the reusable workflow executes, then configured CodeQL and nightly jobs run at dispatch SHA, successful gates produce one schema-valid `disabled` outcome artifact, the run succeeds, and logs include `publishing disabled`.
- Given disabled publishing and a failing analysis or hook, when the run finishes, then its conclusion and sole outcome are failed; Given an empty language list or dormant hook, when the run executes, then only that intentionally disabled gate is skipped.
- Given create mode and non-green exact-source CI, when the manual caller executes, then it fails with `main is red, nothing released`, retains a readable failed outcome and never authorizes publication. Given unfinished CI in API controls, when 30 minutes elapse, then it fails without exceeding the bound; qualifying success inside the bound continues.
- Given complete mode selecting an older valid draft, when the workflow runs, then outputs identify that draft's frozen SHA, while CodeQL and the prepared hook observe dispatch SHA; no old-source config, CI check, restore, pack or release build occurs for the draft SHA.
- Given invalid/ambiguous marked drafts or a non-main ref, when resolve executes through its adapter, then the run fails and names the invalid draft where applicable, and no draft/tag is mutated. Given a hand-authored unmarked draft, when resolving, then it neither controls release selection nor gets changed.
- Given processed CodeQL output and paginated alerts, when the gate executes, then qualifying open high/critical release-category findings fail it; unrelated/closed/lower-severity alerts pass, and transport/analysis failure cannot pass as clean.
- Given any failed or cancelled prerequisite, when final reporting executes, then it cannot report `disabled`, `nothing` or publisher handoff. Given explicit no-release/stale-draft-deletion results in downstream integration controls, when reporting runs, then it emits `nothing`; Given an authorized publish handoff, when reporting runs, then it performs zero uploads so the later publisher is the sole writer.
- Given the current gate-only implementation with all gates green and switch true, when a caller attempts release, then it fails with an explicit incomplete-pipeline diagnostic and `publish=false`; production callers stay on their existing workflows until their replacement story.
- Given this planning-only invocation, when delivered changes are inspected, then Builds changes only the plan document, the canonical story is ready-for-dev with implementation tasks unchecked, and no release workflow, probe, security run or publication was dispatched.

## Spec Change Log

## Review Triage Log

## Design Notes

Outcome precedence is failure/cancellation, then authorized publisher handoff, then genuine disabled/no-release reasons. Unknown results or missing downstream publication stages are failures, never inferred `nothing`. Until the downstream stories install version/build/draft, leave production callers unchanged and diagnose the enabled all-green path as `release publication stages are not installed`. This is an incremental integration boundary, not a change to the eventual AD-17 success behavior.

Emit selected SHA as soon as resolution succeeds, retaining it even if the CI gate later fails. Before selection, the known dispatch SHA provides failure identity. A disabled or invalid switch must not suppress validated current-SHA security jobs. Configuration failure remains failed without fabricating settings. `overwrite: true` handles reruns; it does not substitute for exclusive writer ownership. Cancellation can prevent any reporter from running, which nightly already treats as failed.

No change to prepare is planned. It already supplies event-SHA checkout, SDK/build and environment; the nightly action receives its existing workspace guarantee without unit/integration reruns. The known limitation of the local composite harness requires a hosted job-graph check.

## Verification

**Planning delivery:** validate YAML frontmatter, full baselines against Git, canonical slug, local links, unchecked runtime tasks and a documentation-only Builds diff; run `git diff --check` and pinned exact-message commitlint. Fetch/inspect divergence before push and read back remote HEAD. Runtime tests are not run for this documentation-only change.

**Implementation commands (from Builds, later dispatch):**

- `python3 -m unittest discover -s Github/lib/tests -p 'test_release_*.py' -v` — behavioral matrix passes; repeat in the locked Python 3.12 environment.
- `/tmp/hexalith-builds-ci-tools/uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and the same with the captured runner interpreter — every discovered group passes on both.
- `python3 Tools/ci/lint_workflows.py` — pinned actionlint/online zizmor, no new finding; supply read-only authentication command-locally without logging tokens.
- `/tmp/hexalith-builds-ci-tools/uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` — committed-revision API additions pass; compare frozen runtime blobs to `implementation_baseline_revision` and inspect both repository diffs.
- Implementation-time `gh workflow run release-gates-probe.yml --ref main`, then inspect run/jobs/logs and download `hexalith-release-outcome` — verify the real job graph under the existing repository switch, repeat with the intentional-failure hook input, record exact source/run/attempt and artifact, then remove the probe and restore sample config. Other state/decision variants use executable controls; do not label them hosted observations. No publishing or production release dispatch.

## Auto Run Result

Status: **ready-for-dev**. Halt after planning, as requested.

- Planned exactly story 3-2 from its title/description and canonical epic companions. Three read-only investigation subagents completed before plan generation. No implementation or code-review step was entered.
- User constraints are explicit: resolve is stdlib only with `contents: write` and `actions: read`; nightly-hook reuses 2-6's Linux prepare; 5-1 owns drift comparison. The plan also records the unique outcome writer and the truthful intermediate failure until downstream publication stages are installed.
- Builds delivery: `docs/cicd-3-2-release-gates-plan.md` only, committed and pushed on `main` as `11f8534fc89a2c4a18a984307e927abb6d6c7ff3`. `git ls-remote origin refs/heads/main` returned that exact full revision, and Builds is clean with HEAD equal to origin/main.
- Planning checks passed: both documents' YAML frontmatter, date, full starting revisions, local links and content hygiene; unique id-keyed story filename; all implementation tasks unchecked; exact documentation-only staged/committed scope; `git diff --check`. Commitlint 21.2.4 is both installed and lock-pinned and accepted the exact full stored message with zero problems/warnings. Validation evidence: `/tmp/cicd-3-2-planning-commitlint.log`.
- No runtime file changed, so the frozen runtime and legacy workflows remain unchanged. No runtime tests, probe, security run, release dispatch, publishing or repository administration was performed. Hosted CI may start normally from the documentation push; it is not claimed as implementation acceptance.
- CiCd write-back consists of this canonical ready-for-dev story and the updated Builds gitlink staged together. No CiCd commit or push is authorized by this invocation. Baselines retain the original full revisions above for the later implementation/review delta.
- Remaining work: every unchecked implementation task, its runtime/hosted verification and later downstream integration. These are planned future work, not a completed implementation claim. The ready-for-development gate found no unresolved intent gap.
