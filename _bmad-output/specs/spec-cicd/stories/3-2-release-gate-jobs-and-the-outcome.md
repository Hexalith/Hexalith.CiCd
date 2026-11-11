---
title: Release gate jobs and the outcome
type: feature
created: '2026-11-10'
status: done
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 112538e7be21d574b37a21e5d55daf90dbd0f2d2
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 11f8534fc89a2c4a18a984307e927abb6d6c7ff3
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/references/Hexalith.Builds/docs/cicd-3-2-release-gates-plan.md'
warnings: [oversized]
deferred:
  - summary: >-
      Verify Kotlin coverage with the pinned CodeQL no-build analyzer before adopting java-kotlin in a managed module.
    evidence: |-
      Current GitHub documentation says no-build java-kotlin analyzes Java and omits Kotlin with a warning. The review did not execute a mixed Kotlin/Java fixture with pinned v4.39.3, so that pinned behavior remains unverified. A pinned mixed-language analysis and an architecture decision on the mandated no-build policy would settle it; current hosted evidence covers csharp only. Primary reference: https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/codeql-for-compiled-languages
    location: >-
      references/Hexalith.Builds/.github/workflows/release.yml:94
    severity: medium (unverified)
  - summary: >-
      Confirm the release alert gate cannot miss a release-category alert whose most recent instance on main moves to a non-release analysis.
    evidence: |-
      The gate implements AD-18's predicate exactly: open high/critical alerts whose most_recent_instance carries a hexalith-release/ category. An alert shared with another analysis configuration on main (for example the frozen codeql.yml default /language:<lang> category) could carry that other category, and pass unblocked, if that analysis finishes processing between this run's SARIF processing and the alert read. Whether GitHub orders most_recent_instance by processing time across categories was not verified. The scoped agent token cannot read code scanning (HTTP 403), and no concurrent two-category experiment ran. A controlled two-category experiment on main, or authoritative GitHub documentation, would settle it. A fix would judge the release-category instance from /code-scanning/alerts/{number}/instances and needs an AD-18 predicate decision.
    location: >-
      references/Hexalith.Builds/Github/lib/release_security.py:64
    severity: medium (unverified)
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

- [x] `Github/lib/release_state.py` — add trusted runtime API/Git utilities, one shared highest-reachable stable-tag helper, marked-draft validation and SHA/mode resolution. Handle annotated tags, ancestry, pagination, excluded draft tag and no-tag bootstrap (`1.0.0` only). Ignore unmarked drafts; fail named malformed bot drafts or multiple valid drafts. Read repository objects as data without executing checkout hooks, filters, submodules or module code; keep credentials out of Git/log output.
- [x] `Github/release-resolve/action.yml` and `Github/lib/release_state.py` — expose validated current-dispatch CodeQL/hook settings before kill-switch/CI failure, then selected `sha`, `mode`, `enabled` and complete-draft metadata. Add `delivered-sha` integration seam for 5-1 and guarded `ci-workflow` input defaulting to `ci.yml`. Order selected SHA, future drift slot, exact switch, create-only CI. Use an injected clock/sleeper for bounded wait tests and fail API errors visibly. No drift-check success claim or placeholder implementation.
- [x] `Github/lib/release_security.py` and `Github/release-security/action.yml` — add paginated stdlib alert check after successful CodeQL upload/processing. Filter open high/critical security severity by most-recent-instance release category, leaving unrelated configurations nonblocking. Fetch/error handling must fail visibly rather than treat unavailable findings as empty.
- [x] `schemas/hexalith.release-outcome.v1.json`, `Github/lib/release_outcome.py` and `Github/release-outcome/action.yml` — define and validate the closed draft-2020-12 contract, `$id=https://hexalith.com/schemas/hexalith.release-outcome.v1.json`, required `schema: "hexalith.release-outcome.v1"`, full commit `sha`, and outcome enum `published|ready|nothing|disabled|failed`. Include unprefixed stable `version` whenever known; `ready` requires positive integer `draftId` and `lastTag` (stable `vX.Y.Z`, or empty string when no tag). Add failure-first result reduction, explicit no-op reasons and exclusive publisher handoff. Runtime validation is stdlib; test corpus uses the independent JSON Schema validator.
- [x] `.github/workflows/release.yml` — wire `workflow_call` resolve, CodeQL matrix, nightly-hook and final outcome jobs, with explicit optional named pull secrets and guarded CI-workflow input. Surface resolved SHA/mode and a string `publish` output, currently `false`. Configure CodeQL v4.39.3 at its verified full upstream commit, `build-mode: none`, `hexalith-release/<language>`, and wait for SARIF processing before checking alerts. Use dispatch SHA for checkout and current config, including when resolve fails after emitting valid settings; use `always()` job scheduling plus intentional-disable conditions, not an ordinary success-only `needs` chain. Nightly invokes existing prepare and the fixed root hook. The final `if: always()` reporter uploads only `outcome.json` as `hexalith-release-outcome`, with `overwrite: true`; ensure upload still happens after a failed outcome decision and the job/run stays failed.
- [x] `Github/lib/tests/{test_release_state,test_release_security,test_release_outcome}.py` and `Github/lib/tests/fixtures/release-outcome.json` — exercise the matrix using disposable Git histories, paginated local HTTP/API controls and executed adapters; cover redirects/credential boundaries, deadlines, config at dispatch SHA versus draft SHA, schema/stdlib agreement, failure precedence, legitimate skipped jobs and single-writer handoff. No workflow-text assertions.
- [x] `.github/workflows/release-gates-probe.yml`, `.github/actions/nightly/action.yml` and `Tools/ci/probe_release_gates.py` — create an implementation-time manual Builds-only caller and minimal hook fixture. Reuse `Samples/Hexalith.Sample` through guarded test-only `module-root`; temporarily enable its nightly hook in `Samples/Hexalith.Sample/.github/hexalith-ci.json` and matching expected-source config, then restore both files after the probe. The hook may read a probe dispatch input to exercise intentional failure. Reject fixture inputs outside Builds; keep them outside public module API. Observe the existing repository switch without changing it; prove a real CodeQL matrix/processed-alert query, current-SHA preparation/hook and final reporting after hook failure. Exercise switch variants, red CI and complete-mode selection through executable local controls; claim hosted branch coverage only for branches actually observed. Remove temporary workflow/action/probe scripts after retaining sanitized exact-source evidence in `docs/cicd-3-2-release-gates-results.md`. Do not create live vulnerable findings or publish artifacts to registries.
- [x] `Tools/ci/README.md` and `docs/cicd-3-2-release-gates-results.md` — document public caller permission union, current/release SHA separation, safe intermediate behavior, later draft/publish/outcome handoff and 5-1 drift slot. Record focused and dual-Python checks, real lint/API checks, frozen-file comparison and hosted evidence; distinguish controls from live observations.
- [x] Builds Git, this story and CiCd gitlink — on implementation dispatch, review both repository deltas, validate exact messages, commit/push Builds and verify its remote revision; stage the updated gitlink with canonical story. This planning invocation delivers only the companion plan and records its exact commit below.

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

### 2026-11-10 — Review pass
- verdicts: 16 findings — high 0, medium 4, low 4, false 7, maybe-false 1
- findings (report order; verification-gap returned no findings):
  - `[medium]` `[patch]` Edge: streaming API responses exceed the absolute CI deadline — the former json.load used an inactivity timeout only; a daemon operation with deadline-bound waiting now covers acquisition, headers and body. Real streaming/header and blocked-acquisition controls pass. Grouped with Blind 4.
  - `[false]` `[reject]` Intent: historical planning-only text differs from runtime implementation — the current user dispatch explicitly authorizes implementing the ready-for-dev story and committing/pushing Builds; historical text is preserved and the current dispatch is explained outside the immutable contract.
  - `[false]` `[reject]` Intent: helper/composite tests differ from the GitHub scheduler surface — hosted probes additionally executed scheduling, actual preparation, processed CodeQL and outcome upload; local controls are explicitly identified, with no claim that they reproduce the scheduler.
  - `[false]` `[reject]` Intent: hosted switch/state coverage is narrower than the complete local matrix — the spec expressly requires observing the unchanged switch and allows deterministic controls for other switch/draft/CI states. The unset switch and resulting failed hosted conclusions are recorded accurately.
  - `[false]` `[reject]` Intent: production adoption is absent — the user selected gate story 3-2, whose publication stages and caller migration are separate work; the reusable gates and temporary exact-source caller are the required surfaces, and production callers remain preserved.
  - `[false]` `[reject]` Intent: a patch cannot independently prove the push — parent read-back and the implementation's remote verification establish Builds remote main at the committed implementation revision; delivery is verified outside the patch as required.
  - `[false]` `[reject]` Blind 1: an existing draft tag may point at another commit — AD-16's marked-draft predicate requires version/ancestry and excludes the draft's own tag, not tag-target equality. AD-17 deliberately gives the later publisher preflight responsibility to reject conflicting existing tags before any publication; this gate-only workflow cannot authorize publication.
  - `[low]` `[reject]` Blind 2: go/swift cannot use the prescribed no-build Ubuntu path — these are upstream analyzer capability limits, and unsupported analysis fails the job/run as required. No affected managed module or false-clean result was shown. Alternate OS/build-mode branches add complexity beyond a direct correction for a non-everyday configuration; no runtime mode is changed.
  - `[maybe-false]` `[defer]` Blind 3: no-build java-kotlin may pass with Kotlin omitted — current upstream docs describe this limitation, but no mixed-language fixture ran against the pinned v4.39.3 analyzer. Recorded as medium if true, unverified; a pinned fixture plus a no-build policy decision would settle it. No broad language-coverage claim is made from the csharp hosted evidence.
  - `[medium]` `[patch]` Blind 4: absolute CI deadline does not cover streaming JSON — same demonstrated root cause as Edge; fixed by the bounded complete API operation and tested with real dribbling body/headers and delayed response acquisition.
  - `[medium]` `[patch]` Blind 5: implicit alert ref can inspect a non-main default branch — GitHub documents most_recent_instance as default-branch scoped unless ref is supplied. The endpoint now explicitly requests refs/heads/main, verified in executed HTTP controls.
  - `[false]` `[reject]` Blind 6: successful exact-SHA push/manual CI on another ref qualifies — AD-16 explicitly defines the qualifying source by workflow, SHA and push/manual event, with no head_branch condition. The implementation follows that exact predicate; imposing another branch predicate would change the specified release gate.
  - `[medium]` `[patch]` Blind 7: handoff accepts mismatched draft identity — reducer previously checked success and publish=true only. It now requires draft output SHA/version equality to the selected identity, with missing/mismatched create/complete controls; no public surface was added.
  - `[low]` `[patch]` Blind 8: empty-matrix evidence overstates local execution — narrowed the results to reducer skip semantics and expressly records that matrix expansion was not exercised locally or hosted. The earlier story implementation evidence is narrowed in this write-back as well.
  - `[low]` `[patch]` Blind 9: HTTP errors hide the prerequisite endpoint — HTTP diagnostics now include only the sanitized repository-relative endpoint path and status; executed controls prove that queries, tokens and response bodies are absent.
  - `[low]` `[reject]` Blind 10: implementation record says in-progress after review advances status — that record describes the implementation handoff before parent review. Final state is recorded separately; the requested fix edits this build's spec and is rejected under the review rule.

### 2026-11-10 — Review pass
- verdicts: 50 findings — high 0, medium 3, low 23, false 22, maybe-false 2
- findings (follow-up pass; layer order Blind 17, Edge 12, Verification-gap 6, Intent 15):
  - `[maybe-false]` `[defer]` Blind 1: release gate can miss an alert whose most recent instance is a non-release category — the gate follows AD-18's literal most-recent-instance predicate. An older routine analysis cannot become most recent, so only a non-release analysis processed between this run's SARIF processing and the alert read could cause this, and that ordering was not verified (scoped token returns HTTP 403 on code scanning). Deferred as medium (unverified): a two-category experiment or authoritative docs would settle it; the fix needs an AD-18 predicate decision. Grouped with Edge 5.
  - `[low]` `[reject]` Blind 2: every matrix leg checks all hexalith-release/* categories (removed-language stale alerts; sibling leg not yet processed) — this matches AD-18/intent's "most recent category starts hexalith-release/". Both effects fail closed: the run names alert numbers and is fixed by dismissing alerts, deleting the stale configuration, or rerunning. Removing a language or fixing a sibling's alert between runs is not everyday use, and the fix adds a per-language parameter. Grouped with Edge 4.
  - `[medium]` `[patch]` Blind 3: `always()` gate jobs keep running after run cancellation — GitHub documents that jobs whose condition re-evaluates true are not cancelled, and `always()` is true even when cancelled. Fixed: codeql and nightly-hook now use `${{ !cancelled() && … }}`, which still schedules them after a resolve failure. The reporter keeps AD-17's `if: always()`. Grouped with Edge 1.
  - `[low]` `[reject]` Blind 4: wrong-ref dispatch of a commit not on main fails with `Git object operation failed: cat-file` instead of the ref diagnostic — resolve and the outcome still fail, as the Wrong ref row requires. Only the message differs, and only for a manual mis-dispatch from an unmerged branch. The smallest fix either reorders against deliberately tested gate-on-wrong-ref behavior or adds a branch. Grouped with Edge 6 and Intent 6.
  - `[false]` `[reject]` Blind 5: draft ancestry is checked against the main tip instead of the dispatch SHA — AD-16 defines a marked draft as "that SHA is an ancestor of `main`", and complete-mode gates intentionally run at github.sha whatever the draft SHA. The implementation follows that exact predicate.
  - `[false]` `[reject]` Blind 6: an existing same-name tag is not checked, and higher descendant tags are ignored — carried: tag identity is the logged Blind 1 claim (AD-17 publisher preflight owns conflicting tags). For ordering, AD-16 defines the bound as the highest tag reachable from the draft SHA, and any marked draft forces complete mode, so the pipeline cannot create a higher descendant tag while one exists.
  - `[false]` `[reject]` Blind 7: fetch is hard-coded to anonymous github.com, so it breaks on GHES/private repos and fetches full history — every managed repository (all 18 root submodules) is public on github.com, read back via the API. No reachable module hits this path, and an unsupported repository would fail loudly. Hosted resolve completed the full fetch within its bound. Grouped with Edge 7 and Intent 14.
  - `[false]` `[reject]` Blind 8: a caller granting less than contents write would silently hide drafts — a reusable-workflow job cannot request more permission than its caller grants, so GitHub rejects the run at startup ("is requesting 'contents: write', but is only allowed …"). Resolve never runs with draft listing silently reduced.
  - `[low]` `[patch]` Blind 9: empty resolve outputs make the reporter print a JSON decode error instead of the failed prerequisite — confirmed: workflow expressions render absent outputs as "", and `json.loads("")` raised before failure-first reduction. Fixed: empty RELEASE_CODEQL/RELEASE_NEEDS are treated as missing. An executed adapter control now asserts `release prerequisite 'resolve' failure` and a dispatch-SHA failed outcome.
  - `[false]` `[reject]` Blind 10: empty dispatch SHA, Python < 3.12 or a write error leave no artifact — RELEASE_DISPATCH_SHA is always `github.sha` and ubuntu-latest supplies Python ≥ 3.12. A write failure fails the job loudly, and AD-18 nightly treats "no readable outcome" as failed, so a missing artifact never reads as success. Grouped with Edge 9.
  - `[false]` `[reject]` Blind 11: no qualifying CI run fails immediately without grace — AD-16 and the Red CI row prescribe exactly "Anything else, or no run: fail with 'main is red, nothing released'"; only an in-progress run waits.
  - `[low]` `[patch]` Blind 12: release_outcome duplicates the ci_config LANGUAGES vocabulary — a future ci_config language would make every outcome for such modules fail as "settings were not validated". Fixed: release_outcome imports LANGUAGES from ci_config, and an identity control asserts the shared object.
  - `[low]` `[reject]` Blind 13: go/swift cannot use no-build Ubuntu analysis — carried: same location and claim as the logged Blind 2 rejection (upstream capability limit; unsupported analysis fails the job). The Kotlin coverage question stays deferred from the prior pass. Grouped with Edge 3 and Intent 9.
  - `[low]` `[patch]` Blind 14: README focused command omits PyYAML/jsonschema/node prerequisites — confirmed: a bare interpreter fails on import. Fixed: README names the locked runner's PyYAML/jsonschema and node on PATH, and points to the locked full command. Grouped with Edge 10.
  - `[low]` `[reject]` Blind 15: README has no example caller or concurrency snippet — the required permission union, secrets, cache mode and caller-owned concurrency are documented. Production callers are intentionally unmigrated and caller rendering belongs to the caller-migration story. A new snippet is more than a direct correction, with no current adopter.
  - `[false]` `[reject]` Blind 16: results evidence lives in /tmp, post-review claims name no commit, and no hosted run covers the final source — the results doc labels /tmp logs as workspace-local and hosted links as the durable evidence. It states explicitly that the hosted probes predate the review patches, and the story records the committed revision (a commit cannot embed its own hash). Grouped with Intent 3.
  - `[low]` `[patch]` Blind 17: tests miss delivered-sha/dispatch-SHA validation and non-string schema/null outcome corpus cases (workflow-wiring part carried as the logged scheduler-surface rejection) — fixed: resolve controls for malformed dispatch/delivered SHAs, plus corpus cases `schema-not-string` and `outcome-null` agreeing across the stdlib and jsonschema validators. Grouped with Verification-gap 4.
  - `[medium]` `[patch]` Edge 1: always() gate jobs ignore cancellation — same defect as Blind 3; fixed by `!cancelled()`.
  - `[low]` `[patch]` Edge 2: '[]' never uses the matrix fallback, so the intentional skip relied on condition-before-matrix evaluation, and the comment misdescribed it — confirmed in the expression (non-empty string is truthy). This is an everyday path: `solution: "none"` defaults to `codeql: []`. Fixed: `fromJSON(codeql != '[]' && codeql || '["csharp"]')` with an accurate comment, so neither '[]' nor a missing output can evaluate an empty matrix. Grouped with Intent 5 and Verification-gap 6.
  - `[low]` `[reject]` Edge 3: go/swift build-mode none — carried, as Blind 13.
  - `[low]` `[reject]` Edge 4: language-agnostic category filter blocks on stale/sibling categories — same as Blind 2.
  - `[maybe-false]` `[defer]` Edge 5: a non-release analysis processed between release processing and the alert read moves most_recent_instance — same unverified ordering as Blind 1; deferred together.
  - `[low]` `[reject]` Edge 6: dispatch SHA unreachable from fetched main/tags masks the wrong-ref diagnostic — same as Blind 4.
  - `[false]` `[reject]` Edge 7: private repository or GHES fetch — same refutation as Blind 7 (all managed repositories are public on github.com).
  - `[low]` `[patch]` Edge 8: truncated bodies and other protocol errors escape as non-ReleaseError tracebacks — reproduced: a short Content-Length body raised `http.client.IncompleteRead` on both deadline and non-deadline paths. Fixed: `_request` maps `http.client.HTTPException` to the sanitized transport failure, with a loopback control for both paths. The malformed-Link-URL part was not patched: GitHub does not emit malformed Link URLs.
  - `[false]` `[reject]` Edge 9: Python < 3.12 or output-directory OSError leaves no outcome artifact — same refutation as Blind 10.
  - `[low]` `[patch]` Edge 10: missing `node` raises FileNotFoundError in the schema-pattern control — same root cause as Blind 14 (the test prerequisite was undocumented). Fixed by the README prerequisite note. The error already names `node`, so no runtime guard was added.
  - `[medium]` `[patch]` Edge 11: analyze's processing wait is best-effort, so the gate could read pre-processing alerts and pass clean — verified in pinned v4.39.3 `src/upload-lib.ts`: five backoff polls (about 155 s) or a status-read error only log a warning and the step succeeds. This violates "after processed analysis" and "analysis errors fail". Fixed: analyze has `id: analyze`, its `sarif-id` reaches the gate as RELEASE_SARIF_ID, and `require_processed` fails closed unless the SARIF status is `complete` before any alert read. Executed loopback and adapter controls cover complete, pending, failed, unknown, HTTP 404 and invalid/absent IDs.
  - `[false]` `[reject]` Edge 12: a non-text bot draft body fails without the draft identity — GitHub's API returns `body` as string or null, and null is normalized to "". A non-string body is unreachable from the real API and still fails loudly.
  - `[low]` `[patch]` Verification-gap 1: deadline-bound worker errors on the CI path are untested — pre-verified (mutation survived). Fixed: a real-Api loopback control drives `require_green_ci` against 403/500 and asserts the exact sanitized endpoint diagnostic. The filed mutation is now killed.
  - `[low]` `[patch]` Verification-gap 2: API deadline translation to the red-CI message is untested — pre-verified. Fixed: a shared offset clock pushes an in-flight real-Api request past the deadline and asserts `main is red, nothing released (CI wait exceeded 30 minutes)`. Mutation killed.
  - `[low]` `[patch]` Verification-gap 3: resolve's ci-workflow guard is untested in disabled and complete modes — pre-verified. Fixed: resolve controls for arbitrary.yml and non-Builds builds-ci.yml under switch false, and arbitrary.yml in complete mode, all failing before any API read. Mutation killed.
  - `[low]` `[patch]` Verification-gap 4: delivered-sha validation is untested — pre-verified; fixed by the Blind 17 identity controls. Mutation killed.
  - `[low]` `[patch]` Verification-gap 5: pagination cycle and duplicate rel="next" guards are untested — pre-verified. Fixed: loopback controls for a self-referencing Link and a doubled next link, each failing after one request. Mutations killed; a removed cycle guard made the control hang, which is the unbounded-request consequence.
  - `[low]` `[patch]` Verification-gap 6: the empty-language workflow skip never ran — filed as a defer for a hosted probe. Grouped with Edge 2: the placeholder now makes an empty matrix structurally impossible whatever the evaluation order, and the reducer skip is executed locally. A hosted `codeql: []` observation is still absent and is recorded as residual risk.
  - `[false]` `[reject]` Intent 1: literal plan-only reading versus the runtime implementation — carried: same claim as the logged Intent "historical planning-only text" rejection.
  - `[false]` `[reject]` Intent 2: the story is not ready-for-dev, staged and working copies differ, and CiCd has an unpushed ledger commit — this follow-up review sets in-review then done per the workflow. The staged/working differences are pipeline write-back. `b4b3ce1` is the orchestrator-owned deferred-work bookkeeping commit, outside this story's change.
  - `[false]` `[reject]` Intent 3: tests exercise helpers rather than the scheduler, and post-review changes were never hosted — carried for the scheduler-surface claim. The post-review hosted gap is explicitly disclosed, and the spec allows local controls. The alerts `ref` query parameter is documented by GitHub; its live read was refused by the scoped token, so it is not claimed as observed.
  - `[false]` `[reject]` Intent 4: hosted switch coverage is only the invalid switch — carried: same claim as the logged hosted switch/state coverage rejection.
  - `[low]` `[patch]` Intent 5: the matrix fallback never fires for '[]' despite its comment — same defect as Edge 2; fixed there.
  - `[low]` `[reject]` Intent 6: the wrong-ref control uses a main-reachable SHA — same as Blind 4.
  - `[false]` `[reject]` Intent 7: disabled publishing skips CI (fork a) — AD-17 orders kill switch step 3 ("exactly false ends the run with 'publishing disabled'") before create-mode CI step 4, and the Problem statement keeps security/hook reporting under disabled publishing.
  - `[false]` `[reject]` Intent 8: draft-id/last-tag do not reach the reusable workflow outputs — the spec requires resolve to expose complete-draft metadata (it does, as job outputs) and the workflow to surface SHA/mode/publish. In-workflow downstream stages consume draft metadata, and AD-17 has the publisher take last-tag from draft.
  - `[low]` `[reject]` Intent 9: build-mode none for go/swift/java-kotlin — carried, as Blind 13; the Kotlin part remains the prior deferred item.
  - `[false]` `[reject]` Intent 10: no-op and handoff branches are unreachable from the workflow and the draft output interface is invented — the spec task requires "explicit no-op reasons and exclusive publisher handoff" verified by downstream integration controls. `RELEASE_PUBLISH: 'false'` is the specified intermediate output, and later stories wire their jobs to this seam.
  - `[false]` `[reject]` Intent 11: the intermediate enabled path was never consumed hosted — carried, as the logged hosted coverage rejection; reducer and adapter controls cover it.
  - `[false]` `[reject]` Intent 12: invalid-switch diagnostic appears only in the resolve log — the closed v1 outcome schema has no diagnostic field. Resolve emits the exact message, and the outcome is failed as the matrix requires.
  - `[false]` `[reject]` Intent 13: red CI, CI selection and cancellation were never hosted — carried: deterministic controls are explicitly sanctioned for those states.
  - `[false]` `[reject]` Intent 14: anonymous fetch does not address private repositories — same refutation as Blind 7.
  - `[false]` `[reject]` Intent 15: test_release_adapters.py is not named in the task list — the task requires "executed adapters"; a separate adapter test module implements that requirement without changing scope.


## Design Notes

**Current implementation dispatch (2026-11-10):** The user now requests bmad-build-auto implementation of this ready-for-dev story, using subagents as needed, committing and pushing in `references/Hexalith.Builds`. The prior planning-only invocation is complete; references to "this planning-only invocation" and "later dispatch" in the preserved contract and companion describe that prior delivery. Execute the implementation tasks and runtime/hosted verification now. Preserve the prior planning record as history, then append the implementation result. Resolve remains stdlib only with exactly `contents: write` and `actions: read` (AD-16/17); nightly-hook uses 2-6 prepare. Commit/push Builds and stage the canonical story/gitlink in CiCd, with no CiCd commit/push.

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

### Planning delivery — 2026-11-10

Status at planning delivery: **ready-for-dev**. Halt after planning, as requested.

- Planned exactly story 3-2 from its title/description and canonical epic companions. Three read-only investigation subagents completed before plan generation. No implementation or code-review step was entered.
- User constraints are explicit: resolve is stdlib only with `contents: write` and `actions: read`; nightly-hook reuses 2-6's Linux prepare; 5-1 owns drift comparison. The plan also records the unique outcome writer and the truthful intermediate failure until downstream publication stages are installed.
- Builds delivery: `docs/cicd-3-2-release-gates-plan.md` only, committed and pushed on `main` as `11f8534fc89a2c4a18a984307e927abb6d6c7ff3`. `git ls-remote origin refs/heads/main` returned that exact full revision, and Builds is clean with HEAD equal to origin/main.
- Planning checks passed: both documents' YAML frontmatter, date, full starting revisions, local links and content hygiene; unique id-keyed story filename; all implementation tasks unchecked; exact documentation-only staged/committed scope; `git diff --check`. Commitlint 21.2.4 is both installed and lock-pinned and accepted the exact full stored message with zero problems/warnings. Validation evidence: `/tmp/cicd-3-2-planning-commitlint.log`.
- No runtime file changed, so the frozen runtime and legacy workflows remain unchanged. No runtime tests, probe, security run, release dispatch, publishing or repository administration was performed. Hosted CI may start normally from the documentation push; it is not claimed as implementation acceptance.
- CiCd write-back consists of this canonical ready-for-dev story and the updated Builds gitlink staged together. No CiCd commit or push is authorized by this invocation. Baselines retain the original full revisions above for the later implementation/review delta.
- Remaining work: every unchecked implementation task, its runtime/hosted verification and later downstream integration. These are planned future work, not a completed implementation claim. The ready-for-development gate found no unresolved intent gap.

### Follow-up review result — 2026-11-10

Status: **done**. Story 3-2's reusable release gates are implemented,
reviewed twice and verified. Builds `main` is committed and pushed at
`fa5f48734ca44ce63b55fc645f53c9c6bdccaa1c`. Remote `refs/heads/main` was read
back at that exact full revision, and Builds is clean.

**Implemented change.** Builds' reusable `release.yml` adds:

- a stdlib-only resolve job (exactly contents write and actions read) that reads dispatch-SHA settings through `ci_config`, freezes the marked-draft or dispatch release SHA, applies the strict switch and checks create-mode exact-source CI within a fixed 30-minute deadline;
- a current-SHA CodeQL matrix gated on processed release alerts;
- 2-6 prepare followed by the fixed nightly hook;
- an always-scheduled reporter that writes the closed v1 `outcome.json` with failure-first precedence and an identity-bound future publisher handoff.

Production callers, legacy workflows, frozen runtime files and the publishing switch are unchanged. Enabled all-green gate-only runs deliberately fail with `release publication stages are not installed` and `publish=false`. Story 5-1 owns drift protection; downstream stories own version/build/draft/publication.

**Files changed (Builds-relative; all story additions except the README):**

- `.github/workflows/release.yml` — reusable gate workflow. This pass: `!cancelled()` gate scheduling, empty/missing-list matrix placeholder, and analyze `sarif-id` passed to the gate.
- `Github/lib/release_state.py`, `Github/release-resolve/action.yml` — resolve, marked drafts, stable tags, exact-source CI and bounded API transport. This pass: `http.client` protocol errors are sanitized.
- `Github/lib/release_security.py`, `Github/release-security/action.yml` — processed-alert gate. This pass: SARIF `complete` processing is required before alerts are read.
- `Github/lib/release_outcome.py`, `Github/release-outcome/action.yml`, `schemas/hexalith.release-outcome.v1.json` — outcome contract and reporter. This pass: empty outputs are treated as missing, and the vocabulary is shared from ci_config.
- `Github/lib/tests/test_release_{state,security,outcome,adapters}.py`, `Github/lib/tests/fixtures/release-outcome.json` — executed Git, loopback HTTP, adapter and schema controls. This pass: 10 new mutation-checked controls and 2 corpus cases.
- `Tools/ci/README.md`, `docs/cicd-3-2-release-gates-results.md` — interfaces, ownership and evidence. This pass: scheduling/SARIF notes, test prerequisites and a follow-up hardening section.

**Review findings (this pass): 50 findings — high 0, medium 3, low 23, false 22, maybe-false 2.** They are recorded row by row in the triage log above.

- Patches applied, 12 entries (2 medium, 10 low):
  1. Cancellation-aware gate scheduling (Blind 3 / Edge 1, medium).
  2. Fail-closed SARIF processing check (Edge 11, medium).
  3. Empty-list matrix placeholder (Edge 2 / Intent 5 / Verification-gap 6).
  4. Empty-output prerequisite naming (Blind 9).
  5. Shared language vocabulary (Blind 12).
  6. Documented test prerequisites (Blind 14 / Edge 10).
  7. Sanitized HTTP protocol errors (Edge 8).
  8. New controls for Verification-gap 1, 2, 3 and 5, and for Verification-gap 4 / Blind 17 (identity validation plus corpus cases).
- Deferred, 1 entry, appended to the frontmatter list (the prior Kotlin item is preserved unchanged): the most-recent-instance race (Blind 1 / Edge 5), medium (unverified).
- Rejected low findings, with their reasons:
  - Blind 2 / Edge 4: language-agnostic category filter. It is the intent's predicate, fails closed, and the fix needs a parameter.
  - Blind 4 / Edge 6 / Intent 6: wrong-ref diagnostic. The run still fails as required; this is a rare manual mis-dispatch, and the fix reorders tested behavior or adds a branch.
  - Blind 13 / Edge 3 / Intent 9: go/swift build mode. Carried from the prior pass.
  - Blind 15: example caller. It belongs to the caller-migration story.
- Rejected false findings:
  - Blind 5, 6, 7, 8, 10, 11 and 16;
  - Edge 7, 9 and 12;
  - Intent 1, 2, 3, 4, 7, 8, 10, 11, 12, 13, 14 and 15.

  Each refutation is in its triage row. Carried rows reuse the first pass's verdicts unchanged.

**Follow-up review recommendation: `false`.** This follow-up pass patched 0 high, 2 medium and 10 low entries. Only a patched high justifies another pass, so the work has converged.

**Verification performed (Builds, after patches):**

- Focused release suite: 70/70 pass (previously 60).
- A targeted mutation check confirmed each new control kills its guard's removal: worker error sanitizing, deadline translation, resolve workflow and delivered guards, pagination cycle and ambiguity guards, protocol-error mapping, SARIF processing check, empty-output handling and the shared vocabulary. Every mutated file was restored.
- Locked Python 3.12 and runner Python 3.14.4 `Tools/ci/run_python_tests.py`: 20/20 groups each, including 178 shared-library tests.
- Pinned online actionlint/zizmor (read-only token supplied command-locally): 12 exact frozen findings, 0 new findings.
- Committed-source public API check at `fa5f48734ca44ce63b55fc645f53c9c6bdccaa1c`: 2521 entries, no removals against v4.47.0.
- Against `implementation_baseline_revision`: 14 added paths plus the README; no frozen runtime, legacy workflow, sample or package file changed. `git diff --check` passes. Document-reading tool tests pass.
- Upstream evidence: pinned `github/codeql-action@33d7b85da1a04171e211befe2c739303b9a4c066` `src/upload-lib.ts` (timeout and status-error warnings), and its analyze `sarif-id` output.
- Commit delivery:
  - The exact Builds message passed pinned commitlint 21.2.4 with 0 problems and 0 warnings. Fetch showed no divergence before the push, which used the scoped CiCd agent profile.
  - The CiCd commit message was validated with the same pinned Builds commitlint; CiCd has no commitlint configuration of its own.
  - Per the workflow, the CiCd commit is local only.
  - Evidence logs (workspace-local): `followup-python312.log`, `followup-python314.log`, `followup-lint.log`, `followup-api.log` and `followup-builds-commitlint.log` in this session's scratchpad.

**Residual risks:**

- The changed job conditions, matrix placeholder and SARIF status read have local controls and pass lint, but no hosted run has observed them. Hosted probes 42867966372 and 42868589774 predate both review passes, and the scoped token cannot read code scanning.
- The `codeql: []` skip has not been observed in a hosted run.
- Two deferred questions remain open: Kotlin coverage under no-build mode, and the most-recent-instance race.
- A slow-processing analysis now fails the run rather than passing unverified. That is fail-closed and remedied by a rerun.
- Production adoption, publication stages and drift protection remain later stories.
