---
title: 'Nightly releases'
type: 'feature'
created: '2026-11-14'
status: 'done'
baseline_revision: 'a23d2a818806fcbc377f4dfe6ce357d24bd15dcf'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred:
  - summary: >-
      A rerun release run may still list its earlier attempt's same-name outcome artifact, which would make a valid current-attempt outcome non-unique.
    evidence: |-
      `outcome()` requires exactly one `hexalith-release-outcome` artifact before it rejects artifacts created before `run_started_at`. If GitHub's list-run-artifacts endpoint returns earlier attempts' artifacts for a rerun, every rerun target fails closed as an unreadable outcome (medium if true). To settle it, list the artifacts of a hosted rerun release run. If earlier attempts appear, filter by `created_at >= run_started_at` before the uniqueness check.
    location: >-
      tools/nightly.py:338
    severity: medium (unverified)
  - summary: >-
      The delivery barrier's sequential per-status scans can miss a `deliver.yml` run that moves into `waiting` between two status queries.
    evidence: |-
      `delivery_barrier` queries `requested`, `waiting`, `pending`, `queued` and `in_progress` one after another. A run that moves queued→waiting or in_progress→waiting after the `waiting` query and before the later query appears in no inventory, so the barrier can clear while delivery is still active (medium if true). Only deployment protection on the run's environment produces `waiting`. To settle it, check whether `cicd-app` protection rules can hold a main deliver run in `waiting`, or require two consecutive clear scans.
    location: >-
      tools/nightly.py:214
    severity: medium (unverified)
  - summary: >-
      Anonymous trusted-Builds REST acquisition in each nightly job may exhaust the shared unauthenticated rate limit on hosted runners.
    evidence: |-
      Each nightly job acquires the trusted Builds release through delivery's existing anonymous `Transport.builds` reads: about four per job, twelve per night. If hosted runners share egress IPs, the 60/hour unauthenticated quota may already be spent, failing initialization and with it the whole night (medium if true). The same anonymous pattern already runs hourly in delivery and passed story 7's hosted requalification. To settle it, record the X-RateLimit headers from hosted nightly runs. If they show exhaustion, authenticate these public reads with the job token.
    location: >-
      tools/delivery_runtime.py:365 (Transport.builds), reused by tools/nightly_runtime.py Transport
    severity: medium (unverified)
---

<intent-contract>

## Intent

**Problem:** CiCd has delivery and the shared release runtime, but no nightly controller to start releases, wait for their results, complete GitHub publication that needs the App, or report the night's verdicts. CAP-13 and CAP-15 require this unattended release path, including Builds itself.

**Approach:** Add `nightly.yml` at 02:17 UTC with `dispatch → wait → publish-ready`, backed by isolated stdlib Python controllers. Dispatch eligible modules and Builds without waiting between releases; carry exact run identities into bounded polling and authenticated ready-draft publication, then write every verdict and run link.

## Boundaries & Constraints

**Always:** Implement in this superproject. Follow AD-3, AD-7, AD-11, AD-16–19. Enumerate modules from committed `setup/*.yml`; read module live `main` anonymously through private Git object stores. Each App job runs in `cicd-app`, mints its own explicitly scoped tokens through the pinned `actions/create-github-app-token` action, and re-mints through another action step before any token reaches 50 minutes. Track actual mint epochs conservatively and enforce expiry before each authenticated operation. All jobs have explicit timeouts strictly below 360 minutes. App jobs execute only `python3 -I` stdlib scripts, hardened git, and SHA-pinned actions; parse bounded JSON and read artifact ZIP members in memory. Isolate target failures, retain partial results, and finalize reports on failure. Cancelled runs stop new mints, dispatches and publication; report finalization/upload may still run.

**Never:** Modify Builds or a module, adopt a module, change settings/credentials, use a personal token unattended, sign an App JWT in Python, pass tokens between jobs or artifacts, execute module code, import dependency-bearing render/validation code into App jobs, restore caches, rebuild or push packages/images here, move/delete tags, or clean up drafts. Do not implement the bump, delivery-wait, keepalive, CodeQL, hooks, or duplicate scan in this story. Story 9 inserts the secretless scan **after `publish-ready` regardless of its result and before the bump**; the later bump must run regardless of publication/scan failure. No placeholder scan or bump job is needed now.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Normal night | Delivery idle; adopted modules have matching callers and immutable releases | Dispatch module `release.yml` on `main` with exact `delivered-sha`, plus Builds `builds-release.yml`; record exact created run IDs | One target failure does not suppress eligible siblings or Builds |
| No adopted modules | Empty registry, or registered module has no delivered ref | Record registered modules without refs as not adopted; still dispatch Builds | An unreadable ref is an error, never evidence of absence |
| Adoption or caller failure | Delivered ref exists but config is absent, immutable releases are not confirmed enabled, or either caller differs | Do not dispatch that module; record failed eligibility and turn the night red | Preserve diagnostics without running module code or changing its files |
| Delivery busy | Any main `deliver.yml` run is nonterminal, including queued/pending/in progress | Wait up to 30 minutes, then dispatch only after the barrier clears | At deadline or unreadable delivery status, dispatch nothing and report the failed barrier |
| Target outcomes | Correlated run completes with success and `published`, `nothing`, or `disabled` | Pass the target; kill switch is decided by its own release workflow | Any nonsuccess conclusion fails regardless of outcome; success with `failed` also fails |
| Ready draft | Successful run has validated `ready` outcome and authentic original marked draft/artifact | Publish the same draft with the App; create/check the tag last; pass only after all publication checks succeed | Bad draft, producer, digest, ancestry, tag or returned release fails that target before an unauthorized write |
| Incomplete observations | Run unfinished at five-hour deadline; outcome missing/malformed/unreadable; dispatch response uncertain | Preserve run link and diagnostics; final verdict fails | Wait remains successful for target failure/timeout/outcome-read failure; it fails when run statuses cannot be listed/read |
| Partial or cancelled orchestration | Mint, checkout, state download or one target fails; explicit workflow cancellation | Finalizer reports failures and every result it can establish; no guessed runs or silent green | Cancellation prevents further mints, dispatches and publication; missing state fails conservatively |

</intent-contract>

## Code Map

- `.github/workflows/deliver.yml:64` — existing `cicd-app` job and per-target mint/report pattern. Reuse checkout `3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), App mint `64ab729a6294000f5aa4a4bc0b73d1f32bc45510` (v3.3.0), and upload `cf430e030ddbb5b0abf93d22962f4752f3646cd9` (v7.0.2). Only mint actions receive `vars.HEXALITH_CICD_APP_CLIENT_ID` and `secrets.HEXALITH_CICD_APP_PRIVATE_KEY`. Preserve delivery's immutable bootstrap `03d130f82366dec8ed70a21a14177ae55ea09ca1` and its fixture hashes.
- `tools/delivery_runtime.py:61` — strict JSON; `atomic:89`, `environment:103`, hardened `Git:148`, `Transport.accepted:334`, `Transport.module:355`, `Transport.builds:365`, and `registry:458` are reuse seams. `Budget:133` has a delivery-specific 36-minute deadline and `API:241` is GET-only: do not change their delivery semantics for nightly. `sanitize:124` recognizes only `CICD_TOKEN` and `MODULE_TOKEN`; capture/redact any nightly token names deliberately before clearing the environment. Registry capacity is 17 modules; Builds is a separate fixed target.
- `tools/deliver.py:81` — hourly freshness already discovers `.github/workflows/nightly.yml`; once activated, a last main run older than 26 hours fails delivery. Do not duplicate or change this mechanism.
- `tools/check_global.py:383` — discovers all `tools/tests/test_*.py` and runs their locked scripts; `workflow_paths:400` and `lint_workflows:419` automatically include the new workflow. `run:463` is the shared global-check entrypoint for validation and the later bump.
- `tools/tests/test_delivery_workflow.py:27` — executable workflow-mapping harness with inert actions and real isolated controller processes; adapt its approach, including failure continuation and cancellation. `tools/tests/delivery_support.py:55,186` supplies real disposable Git fixtures and transport-boundary doubles. Do not assert workflow source text.
- Read-only Builds at `references/Hexalith.Builds`, inspected HEAD `0230aefd0502775b034a38c3b037c32c79f20fd7`: `.github/workflows/builds-release.yml` is the rewritten dispatch-only caller with no module inputs; reusable `.github/workflows/release.yml` accepts `delivered-sha`. An outcome's release SHA can intentionally differ from the dispatched run's head SHA in complete mode.
- Read-only Builds `Github/lib/release_outcome.py:29` / `schemas/hexalith.release-outcome.v1.json` — sole strict outcome loader and closed contract. `release_complete.py:selected_draft:19` authenticates the selected live unique marked draft; `release_draft.py:release_trailers:50,artifact_metadata:237` authenticates five original trailers and producer artifact metadata; `release_publish.py:validate_source:69,validate_release:83,version_tag:105,producer:158,finalize_release:234` supplies source, captured-base, original-producer, live-body, tag and final PATCH checks. Use `finalize_release` with the deliberate App path that bypasses only workflow-tree comparison. Do not call publisher `authenticate()`, package/image publication, or complete-mode cleanup.
- `builds-version` currently names `v5.1.0`, source `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`; the listed release helpers exist at that tag. Production must independently validate the pinned acceptable release and acquired tag/source identity, then load its committed `Github/lib` and schema, never execute the mutable submodule checkout. Require the actual release capabilities before import, in addition to existing perimeter acquisition checks.
- Cross-story continuity: every existing story 1 through 7 is `done` with completed execution tasks. Story 7's planning-only Auto Run Result is historical; current implementation and final checklist supersede it. Production setup is intentionally empty. Preserve qualification resources such as Builds draft `441591623`; earlier attended credential/probe exceptions authorize no new exception here. Other release/CI deferrals stay with their owning stories.

## Tasks & Acceptance

**Execution:**

- [x] `tools/nightly_runtime.py` — add the bounded stdlib runtime for job/mint clocks, narrowly allowed REST dispatch/PATCH/artifact operations, trusted Builds acquisition/import, and versioned closed JSON state. Reuse the existing hardened Git/registry/JSON helpers without widening delivery behavior. Bind requests to fixed GitHub endpoints and trusted repo names; bound pagination, calls, response/ZIP sizes and retries. Do not forward authorization to artifact redirect hosts. Keep all temporary stores under the job's scratch root and redact tokens from every diagnostic.
- [x] `tools/nightly_publish.py` — add ready-draft validation/publication and verdict reduction using the authenticated tagged release helpers. Verify original producer and artifact metadata, captured `lastTag`, unchanged live draft and tag before the single publish PATCH, then returned release and peeled tag. Preserve all report rows when one target fails; write summary before returning the final aggregate exit status.
- [x] `tools/nightly.py` — add initialization, eligibility/dispatch, polling-slice, finalization and report CLI phases. Initialize conservative state before fallible work. Enforce the 30-minute delivery barrier, adopted-module checks, exact caller comparison, dispatch-returned run IDs and five-hour aggregate wait. Preserve nondispatched failures and every target observation independently; output only bounded, validated workflow outputs. Define CLI inputs through arguments/env without expression interpolation in shell code.
- [x] `.github/workflows/nightly.yml` — wire schedule `17 2 * * *` and manual dispatch, main-only App jobs, `concurrency: nightly` without cancellation, `cache-mode: none`, top-level `permissions: {}`, explicit per-job grants, pinned actions and no recursive checkouts/persisted credentials. Create `dispatch`, `wait`, `publish-ready` with explicit failure-continuation dependencies. Use action mint steps for every job and every renewal; keep per-target mint failures isolated. Upload token-free state/report artifacts on failure as well as success. Apply the timing and scope contract below.
- [x] `tools/tests/nightly_support.py`, `tools/tests/test_nightly_runtime.py`, `tools/tests/test_nightly.py`, `tools/tests/test_nightly_workflow.py` and the three test scripts' adjacent `.py.lock` files — build real temporary Git snapshots, HTTP/ZIP fixtures, inert mint actions and fake-clock coverage for every matrix row and AC. Execute the actual workflow conditions/env/output mappings and real isolated controllers, substituting external I/O only. Verify all 17 slots plus Builds, mint failure isolation, rollover, failure finalizers, retries and cancellation. Lock PEP 723 test dependencies; production scripts remain stdlib-only.
- [x] `docs/nightly.md`, `README.md` — document and link the schedule, eligibility, artifact/state handoffs, token/job limits, pass/fail meanings, cancellation and rerun behavior, existing 26-hour freshness alert, and the story-9 scan-before-bump integration boundary. Explain how to inspect run links and that target runs retain release details.

**Acceptance Criteria:**

1. Given the committed workflow on main, when its 02:17 UTC schedule or a main manual dispatch starts it, then the real job mappings execute `dispatch → wait → publish-ready` in `cicd-app`; failure of an upstream job still permits result collection/finalization unless the workflow is cancelled, and the schedule has no push/PR trigger.
2. Given mixed registered modules and a running delivery, when dispatch executes, then no release starts before the delivery barrier clears, eligible modules receive their exact delivered commit, excluded modules appear with reasons, and Builds receives exactly its own release dispatch without waiting for module releases to finish.
3. Given a dispatch API reply naming a run, when wait observes results, then only that repository/workflow/main/workflow_dispatch identity is accepted; unrelated/manual runs cannot substitute, and a complete-mode outcome may retain an older release SHA. An uncertain POST is never blindly retried or replaced with the latest run.
4. Given releases spanning multiple token lifetimes, when the actual wait job runs through fake-clock renewal boundaries, then polling remains at 60-second intervals, every token is replaced before 50 minutes, mint failure cannot cause stale-token reuse, no post-job action uses an aged token, and one shared five-hour deadline survives all slices. Each workflow job remains strictly below six hours.
5. Given a successful `ready` result from the target's original release artifact, when publish-ready executes, then it validates marking, original workflow/run/artifact digest, captured base ancestry and tag identity, publishes that same draft without the workflow-tree comparison, and independently checks the returned release and tag; malformed/mismatched inputs produce a failed row with no unsafe publication.
6. Given a mixed night including failed dispatch, failed/cancelled target runs, missing outcomes, timeout, valid disabled/nothing/published results and a publishable ready result, when publish-ready finishes, then its persisted report and Actions summary contain a verdict and available run link for every target; any failed row makes the night red while valid siblings complete.
7. Given hostile JSON, ZIP names, redirect URLs, repo content or token-bearing errors, when the controllers process them, then no module code, dependency-bearing parser, arbitrary URL, archive extraction or credential leak occurs. A cancelled orchestration performs no further mint/dispatch/publication while finalization retains observations.
8. Given only this story is implemented, when its workflow completes, then it stops at publication/reporting; documentation preserves `publish-ready → secretless scan → bump`, with later stages continuing after earlier failures. Builds/module checkouts, pins, delivered refs and delivery bootstrap are unchanged.

## Spec Change Log

## Review Triage Log

### 2026-11-14 — Review pass
- verdicts: 17 findings — high 5, medium 8, low 0, false 4, maybe-false 0
- findings:
  - `[medium]` `[patch]` Verification gap: nonsuccess conclusions are masked by an unverified-ready fixture — the reviewer removed the conclusion guard in memory and all 12 publication tests still passed. Added `test_nonsuccess_conclusions_override_every_otherwise_passing_outcome`, with a passing control and failed row/aggregate assertions for each nonsuccess conclusion.
  - `[medium]` `[patch]` Verification gap: publication mappings for slots 3–18 are unexecuted — mutating slot 18 to slot 17 left all seven workflow tests green because the maximum-capacity fixture returned `nothing`. The maximum-capacity workflow case now publishes all 18 distinct drafts and checks every mint, slot, release ID and result.
  - `[high]` `[patch]` Blind hunter: initial dispatch accepts a changed eligibility head — `run_identity` gates the head comparison on already-dispatched state, then `dispatch_target` replaces the frozen head. Parent reproduction accepted distinct checked/run SHAs. Removed the already-dispatched qualifier from the existing source comparison; the real-controller race regression retains the frozen head and exact created run link.
  - `[high]` `[patch]` Blind hunter: repeated anonymous Builds acquisition exhausts the source-read quota — `Transport._builds` makes at least four anonymous REST reads and publication acquires it 19 times in one job, at least 76 reads within 55 minutes against GitHub's 60/hour limit. Added local reuse of the existing authenticated object store, checking its recorded tag/source, restoring exports from Git with lazy fetching disabled, and making no new REST/fetch acquisition; the 18-target test asserts 12 anonymous acquisition reads across all three jobs.
  - `[medium]` `[patch]` Blind hunter: publication pagination discards the helper deadline — `_ReleaseApi.pages` drops its deadline and `API.pages` does not forward it to page reads. Forwarded the helper deadline through the adapter, pagination, retries and post-response checks; cumulative-page fake-clock and adapter tests cover the bound.
  - `[medium]` `[patch]` Blind hunter: the delivery barrier can report success after its deadline — the deadline is checked only after the busy test, and reads have the wider job budget; the parent's fake-clock idle response cleared at 2,500 seconds. Applied the barrier deadline to the existing budget and every paginated read and checked it before accepting idle; a late-response regression proves no release is dispatched.
  - `[medium]` `[patch]` Blind hunter: a slow dispatch/publication target can consume sibling time — the operations inherit the whole remaining job budget while release inventories, annotated tags and Git operations consume bounded but cumulative time. Bounded each dispatch/publication target to at most 60 seconds and its share of the existing remaining budget, retaining finalization reserve; slow first-slot regressions prove healthy siblings still execute.
  - `[medium]` `[patch]` Blind hunter: a known created run is never observed after its first status-read failure — the exact run ID/link survive but `dispatch=failed` makes `needs_poll` false, confirmed by parent reproduction. Polling now includes every known created run ID and freezes its observed head/attempt; the recovery regression collects its outcome while retaining the original failed dispatch and single POST.
  - `[high]` `[patch]` Blind hunter: reruns during outcome retrieval can leave a stale passing outcome — after reading the ZIP, the completed row becomes terminal without another attempt/status read; only ready publication later rechecks completion. Re-read the exact run after artifact retrieval, retained changed attempt/status observations, suppressed stale outcomes and treated recheck-read failure as a wait failure; tests cover nothing/disabled/published plus read failure.
  - `[medium]` `[patch]` Blind hunter: malformed cross-field state can pass shape validation — parent reproduction accepted a wait handoff with no clock and a completed dispatched row with no head/positive attempt; the reducer accepts otherwise passing outcomes. Enforced a head and positive attempt for dispatched rows and aggregate clocks for observed wait/final states, while accepting unobserved explicit failure seeds; cross-field regressions cover both.
  - `[medium]` `[patch]` Blind hunter: 429 retries ignore server backoff — the response headers are discarded and delays are always one/two seconds, contrary to GitHub's documented Retry-After/reset requirements. Added bounded Retry-After/date and exhausted-primary reset handling, a 60/120-second fallback, and operation/token/job-budget refusal; secondary throttles ignore an unrelated future primary reset.
  - `[false]` `[reject]` Blind hunter: planning-only Auto Run Result is stale — it records the preceding planning invocation, and this workflow explicitly writes the completed implementation/review result during Finalize. Editing this build's spec as a review fix is also expressly rejected by the workflow; finalization will replace the historical terminal status.
  - `[high]` `[patch]` Edge-case hunter: a changed dispatch head bypasses the checked caller snapshot — independently reproduced by that reviewer and the parent; same root cause as the blind-hunter dispatch-head finding, retained as its own row. The shared source-comparison correction and race regression above resolve this duplicate finding.
  - `[high]` `[patch]` Edge-case hunter: delivery can move from queued to in_progress between disjoint status reads — sorted status scans read in_progress first and queued later, so the demonstrated transition is absent from both inventories while delivery remains active. Scans now observe queued work before in_progress; the real-controller transition regression waits for actual completion rather than writing an early cleared marker.
  - `[false]` `[reject]` Intent alignment: broader repository-wide remediation is absent — story 8-1 is the dispatched unit; existing delivery already uses cicd-app with its own mint steps and a 40-minute job, and validation has a 120-minute limit. The diff need not rewrite those compliant jobs or downstream repositories.
  - `[false]` `[reject]` Intent alignment: local tests do not establish hosted execution — the implementation claims local workflow/controller qualification only, and the spec explicitly reserves live installation/schedule evidence for an actual main run. No unsupported hosted-success claim or demonstrated operational defect was identified.
  - `[false]` `[reject]` Intent alignment: scan/bump ordering exists as a future integration boundary — the invocation explicitly assigns the scan to story 9; this story correctly stops at publish-ready and records scan-before-bump with failure continuation. No current executable scan stage was requested.

The two changed-head findings share one patch entry. All other surviving findings have independent root causes. This pass has 12 patch entries (high 4, medium 8), no intent gap, no bad-spec re-derivation, and no deferred entry. Each correction is confined to an existing private validation, budget, acquisition, observation or test boundary; it adds no public interface or unresolved intent.

### 2026-11-14 — Review pass
- verdicts: 36 findings — high 0, medium 4, low 23, false 6, maybe-false 3
- findings:
  - `[low]` `[patch]` Blind hunter: a write reply other than 200 is reported as a definite failure — a 204 or other unexpected status to the dispatch POST raised `unexpected response status` without the uncertain qualifier, even though the service may have created an untracked run. Unexpected write statuses now carry `write result uncertain, not retried`. `test_received_write_reply_is_never_a_definite_failure` covers this, verified by mutation; shares its root cause with the edge-case post-read row.
  - `[low]` `[reject]` Blind hunter: nothing excludes delivery after the barrier clears, so a delivery push can race dispatch — the dispatch API takes a ref and cannot pin a SHA. The frozen-head identity check already rejects any created run whose head moved, failing that row closed, and a stale delivered SHA is still an accepted, ancestral delivered commit. Excluding delivery during nightly is the delivery-wait work this intent excludes, and a pre-POST refetch would only narrow the race. Shares its root cause with the edge-case pre-POST row.
  - `[low]` `[reject]` Blind hunter: `select()` refetches CiCd for every module inside a fixed 20-second target budget — later refetches are incremental. The production registry is empty, so nobody meets this now, and a slow first fetch fails that module's eligibility closed. Restructuring acquisition outside the loop is more than a direct correction.
  - `[low]` `[reject]` Blind hunter: transient poll read failures become permanent — the spec deliberately fails wait when statuses cannot be read and fails a target with an unreadable outcome. Reads already retry 5xx and rate limits, and this pass adds transport-error and artifact rate-limit retries (E3, V2). Retrying until the deadline would need new per-target error state.
  - `[low]` `[reject]` Blind hunter: one failed poll-slice mint consumes a slice and turns the night red — a mint failure is an orchestration failure the night must report. The ninth slice covers one failed mint. Two consecutive failures are rare, and recovering from them needs new backoff state.
  - `[low]` `[patch]` Blind hunter: `docs/nightly.md` lacks operator prerequisites — added the App installation targets, the required installation permissions, the `cicd-app` variable/secret names and the unattended-environment requirement.
  - `[low]` `[patch]` Blind hunter: the rerun guidance is wrong when dispatch itself failed — dispatch finalization is red for any failed target, so re-running failed jobs re-runs dispatch and its dependents. The docs now state that this dispatches a fresh set of exact runs, and that only wait/publish-ready reruns fail closed. Shares its root cause with the edge-case rerun-docs row.
  - `[low]` `[reject]` Blind hunter: verification is claimed but not recorded, the task list omits `nightly_publish_cases.py`, and `review_loop_iteration` is 0 — finalization records the commands and counts under Auto Run Result. The counter tracks only bad_spec loopbacks, of which there were none. The task-list omission is real, but fixing it means editing this build's spec, which triage rejects.
  - `[low]` `[patch]` Blind hunter: the `skip` verdict is undocumented — the docs now say a not-adopted module reports `skip` and never turns the night red.
  - `[low]` `[reject]` Blind hunter: two test names promise symlink/uncertain coverage that is absent — runtime tests already cover lost write responses (`test_retry_get_and_do_not_retry_uncertain_writes`) and malformed run details (`test_exact_dispatch_details_and_inputs`). The controller maps every dispatch exception through the same failed-row path as the tested rejection. The mismatch is in the names only.
  - `[low]` `[reject]` Blind hunter: the helper capability table is duplicated and its copies disagree on async functions — the tagged helpers define no async functions, so the difference has no effect. Deduplicating is refactoring, not a correction.
  - `[low]` `[reject]` Blind hunter: the three inline workflow seeds are duplicated and disagree (`pending` vs `fail`), and no test validates them — each seed holds its phase's own pending/final verdict, and every seed carries a nonempty error, so it fails closed regardless of drift. A seed-validation harness is extra scaffolding for an already fail-closed path.
  - `[false]` `[reject]` Blind hunter: nothing alerts anyone to a red night — a failed row makes publish-ready exit nonzero, so the workflow run fails and GitHub's standard workflow-failure notifications and the Actions UI report it. Nothing in the change suppresses that.
  - `[low]` `[reject]` Blind hunter: Builds is dispatched last and may be starved — `target_budget` keeps a fair share of the remaining budget, plus report reserve, for every later pending target, Builds included. Starvation needs a near-30-minute barrier and a full, slow 17-module registry, while production's registry is empty. Moving Builds changes the fixed slot mapping.
  - `[low]` `[reject]` Blind hunter: `publish_target` relies on `selected_draft` populating artifact keys — a missing key fails that row closed before any write, so only the diagnostic text is opaque. Explicit checks would add branches for a cosmetic gain.
  - `[low]` `[patch]` Edge-case hunter: a received write response is discarded by the post-read budget/deadline check — writes now return their received value without post-read checks, so a created run's exact identity survives. The same regression test covers it, mutation-verified. Shares its root cause with the blind-hunter write-reply row.
  - `[low]` `[reject]` Edge-case hunter: a POST/PATCH can be sent with about one second of budget — this needs a slot to spend nearly all of its ≤60 seconds before the write. The result is already reported as uncertain and fails closed, and a minimum-write guard would add a new branch.
  - `[medium]` `[patch]` Edge-case hunter: a single transient connection reset or timeout on an idempotent GET is not retried — any poll read could turn the night red. GET transport failures now retry twice with 1/2-second backoff inside the remaining operation/token/job budget, and writes still never retry. `test_transport_reset_retries_reads_but_never_writes` covers this, verified by mutation.
  - `[maybe-false]` `[defer]` Edge-case hunter: an earlier attempt's outcome artifact may make a rerun's valid outcome non-unique — whether GitHub lists previous attempts' same-name artifacts under the rerun run is unverified. Medium if true. Recorded in `deferred` with the hosted rerun listing that would settle it.
  - `[maybe-false]` `[defer]` Edge-case hunter: a deliver run moving into `waiting` between status queries escapes the barrier — this depends on whether `cicd-app` deployment protection can hold a main deliver run in `waiting`. Medium if true. Recorded in `deferred` with the settling check.
  - `[low]` `[reject]` Edge-case hunter: module main can advance between select and the dispatch POST — the same inherent ref-dispatch race as the blind-hunter delivery row. The frozen head is enforced on the created run, so the row fails closed.
  - `[maybe-false]` `[defer]` Edge-case hunter: anonymous Builds REST acquisition may exhaust a shared runner IP's unauthenticated quota — it reuses delivery's existing anonymous acquisition, which passed hosted requalification, and hosted IP sharing is unverified. Medium if true. Recorded in `deferred` with the header evidence that would settle it.
  - `[low]` `[patch]` Edge-case hunter: the docs' rerun guidance contradicts dispatch re-running every target — corrected together with the blind-hunter rerun row.
  - `[medium]` `[patch]` Verification gap: the slice-edge polling guards are unverified — added `test_slice_edge_stops_before_the_next_target_without_an_orchestration_error` and `test_slice_edge_recheck_failure_stays_pollable_without_an_orchestration_error`. Reverting either guard now fails its test.
  - `[medium]` `[patch]` Verification gap: artifact downloads ignore the rate-limit handling — `_artifact_payload` now shares `API._limited`, and `artifact_member` waits `_retry_delay`'s service minimum within budget. A 403 without rate-limit headers is still not retried. `test_rate_limited_artifact_downloads_wait_the_service_minimum` covers this, verified by mutation.
  - `[medium]` `[patch]` Verification gap: clearing outcomes after a failed publish-ready initialization is unverified — added `test_failed_publish_ready_initialization_withholds_every_write_slot`, which asserts no slot output, `active=false`, a red finalization and no publication. Removing the clearing loop fails it.
  - `[low]` `[patch]` Verification gap: the publish step's nonzero exit is not asserted — the slow-slot test now asserts exit 1 for the failed slot and exit 0 for the published slot.
  - `[false]` `[reject]` Intent alignment: hosted GitHub behaviour is modelled locally, and the empty production registry leaves the module rows fixture-only — carried: same claim as the earlier "local tests do not establish hosted execution" row, and the change still claims only local qualification.
  - `[false]` `[reject]` Intent alignment: nothing checks that imported Builds helpers are stdlib-only — the tagged v5.1.0 helpers import only stdlib and Builds-internal modules, and the dependency-free locked `test_nightly.py` runs them in isolated `python3 -I` processes, so a third-party import would already fail that suite.
  - `[low]` `[reject]` Intent alignment: wait turns red on inherited dispatch errors or a lost poll mint — the night is already red from the same orchestration error, so only the wait job's colour differs. Failure continuation still runs publish-ready.
  - `[low]` `[reject]` Intent alignment: explicit cancellation leaves no final verdict summary, and a lost `wait.json` drops dispatch run links — the running job's `always()` finalizer persists and uploads its observations with the cancellation error, and the intent says finalization "may" still run. `wait.json` is seeded before checkout and uploaded under `always()`, so it is lost only if the upload itself fails.
  - `[low]` `[reject]` Intent alignment: cancelling a dispatch step mid-POST can leave a created run without a link — this is inherent to runner step termination, and the row fails closed as "did not complete".
  - `[false]` `[reject]` Intent alignment: `skip-token-revoke` leaves unused tokens alive until their normal expiry — the Design Notes mandate this to forbid aged post-job token use, so it is not a divergence.
  - `[false]` `[reject]` Intent alignment: Builds is eligible unconditionally — this matches the intent's fixed Builds target, and the matrix's barrier failure still dispatches nothing.
  - `[false]` `[reject]` Intent alignment: targets are dispatched one slot at a time — "without waiting between releases" forbids waiting for completions, not sequential POSTs.
  - `[low]` `[reject]` Intent alignment: no test pins wait's result on inherited errors or a lost poll mint, or a missing `wait.json` in publish-ready — wait's exit is directly `int(bool(errors))`. Handoff loss runs through the same `handoff()` path that the dispatch-artifact loss cases test, so every untested branch already fails closed.

This pass resumed the follow-up review of the `done` spec. The earlier follow-up session applied and verified working-tree changes but timed out before logging its own triage, so its findings cannot be reconstructed. Those changes were reviewed here as part of the complete diff since `baseline_revision`: concurrency grouping, removal of an unneeded dispatch `actions: read` grant, a ninth poll slice, slice-edge pollability, stricter step exits, rate-limited 403 and bounded artifact retries, documentation and tests. Grouped rows share one patch entry each: write replies, rerun docs, and the reject shared by both ref-dispatch race rows. That leaves 9 patch entries (high 0, medium 4, low 5) and 3 deferred maybe-false entries. There is no intent gap and no bad_spec re-derivation. Each correction stays inside an existing private request, retry, documentation or test boundary.

## Design Notes

**Runtime identities and state.** Keep nightly run ID/attempt, CiCd source SHA, module registry, trusted Builds tag/source, per-target repository/caller path, pinned delivered SHA, observed dispatch head, created run ID/link and dispatch diagnostics in token-free `dispatch.json`. Use a closed versioned document (`schema: hexalith.nightly.v1`) and strict phase-specific fields. `wait.json` adds the single wait start/deadline, last statuses/conclusions, validated outcomes or outcome-read errors. Final `nightly.json` holds per-target eligibility/dispatch/status/outcome/publication/verdict/reason/link and aggregate result. Not-adopted modules are explicit nonfailure skips. Bind handoffs to this nightly run/attempt/source and revalidate repo names against committed setup plus Builds; do not let JSON introduce repositories, code paths or token scopes.

Upload named per-phase artifacts containing only their one JSON file, with names including `github.run_attempt` and IDs passed through job outputs. Consume only artifacts belonging to this current nightly run and expected phase, even during reruns. Read bounded ZIP members in memory, verify archive metadata/digest and exact allowed member, then atomically write parsed state at a controller-chosen path. Missing artifacts/outputs synthesize an explicit orchestration failure, never an empty green night. Always persist available rows and summary before failing. No tokens or keys appear in state.

**Dispatch.** Treat all nonterminal main delivery statuses as busy and paginate boundedly. After it is idle, resolve each delivered ref and confirm its ancestry to current CiCd main. No ref means not adopted. A ref plus missing regular `.github/hexalith-ci.json` means failed adoption. Freeze a fresh live-main commit, compare the bytes and regular-file modes of both callers against `rendered/<Repo>/.github/workflows/{ci,release}.yml` at that delivered commit, and confirm immutable releases are enabled. Authentication/read failures leave settings unverified and fail eligibility; they never prove absence. Dispatch Builds once as the fixed extra target, with no `delivered-sha` input. Do not duplicate release kill-switch/green-CI/security gates in CiCd.

Use the API's returned `workflow_run_id` and URLs with an explicit supported API version and run-details request; validate the returned identity through the run API, including caller path, repo, event and branch. Dispatch POSTs have no blind retries after uncertain delivery. Never select the latest run by time. Current GitHub documents run-ID responses, and its compatibility option is `return_run_details: true`: [workflow endpoint](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event), [run-ID rollout](https://github.blog/changelog/2026-02-19-workflow-dispatch-api-now-returns-run-ids/). Test both definite rejection and lost/malformed response conservatively.

**Timing, minting and permissions.** Use job timeouts of 55 minutes for dispatch, 330 for wait, and 55 for publish-ready, with smaller bounded operations and report reserve. Dispatch's delivery barrier is at most 30 minutes. Wait starts one aggregate 300-minute deadline when the job initializes; alternate pinned action mint steps and poll slices of at most 40 minutes, enough slices to cover that deadline including mint overhead. Later slices skip after completion/deadline. Poll slices never reset the deadline. Token epochs are recorded conservatively at the mint boundary, not reset at each script process; an operation must finish within the remaining token/window/job budget, with safety margin before 50 minutes. No expired token fallback. Shorter dispatch/publication stages mint anew for each target and renew any long-lived scope before reuse.

Set `skip-token-revoke: true` on the new nightly mint steps so their default post-job revocation cannot authenticate with a 50–60-minute-old token; discarded tokens retain GitHub's normal one-hour expiry. The pinned action supports this input and otherwise revokes unexpired tokens at job end: [action inputs](https://github.com/actions/create-github-app-token/blob/64ab729a6294000f5aa4a4bc0b73d1f32bc45510/action.yml), [post-job implementation](https://github.com/actions/create-github-app-token/blob/64ab729a6294000f5aa4a4bc0b73d1f32bc45510/lib/post.js). Cover this lifecycle in the executable mint-action fixture. Do not alter delivery's existing mints.

| App use | Explicit repositories | Token permissions |
|---|---|---|
| Dispatch delivery barrier | CiCd only | Actions read |
| Dispatch one target | That eligible module only; Builds separately | Actions write; Administration read for immutable-setting check where used |
| Wait poll slice | Only successfully dispatched repositories, bounded by committed registry plus Builds | Actions read |
| Publish one ready target | That repository only | Contents write, Workflows write, Actions read |

Every mint explicitly sets owner `Hexalith`, a nonempty repositories list, and `permission-*`; no implicit installation-wide scope. Use per-target action slots for dispatch/publication so an installation/mint error in one module cannot suppress another. Job `GITHUB_TOKEN` has only the read permissions needed for checkout and its own handoff artifacts. The key reaches mint actions only. The immutable-release check is the Administration-read endpoint documented by [GitHub](https://docs.github.com/en/rest/repos/repos#check-if-immutable-releases-are-enabled-for-a-repository); do not generalize a 404/403 into successful eligibility.

**Wait and outcomes.** Persist each successful status read before another target can fail. Continue collecting healthy siblings after a run-list/read failure, then fail wait for that inability. Target conclusions, elapsed deadline, and unreadable outcomes are data for publish-ready rather than reasons for wait to fail. Read only the correlated run's sole unexpired `hexalith-release-outcome` artifact and its exact `outcome.json`; validate ZIP bounds/digest and the tagged outcome loader. Artifact redirects are documented separately from API JSON: [GitHub artifact API](https://docs.github.com/en/rest/actions/artifacts#download-an-artifact). Bind outcomes to the observed current run/attempt and never trust a stale previous-attempt outcome while a rerun is active. Do not require outcome SHA to equal dispatched head SHA.

**Publication and verdicts.** For successful `ready` only, use outcome `sha`, `version`, `draftId`, and captured `lastTag` (including empty tagless base), then authenticate the selected unique bot-marked draft and all five trailers. The artifact named by its trailers must belong to the original workflow_dispatch/main producer at that built SHA, have name `release`, be unexpired, and have the trailer's API digest. That producer may be older than the currently dispatched completion run. Check release SHA/main and base ancestry using trusted Git objects, not a recomputed latest tag or create-only successor rules. Freeze/recheck the complete body and require the version tag to be absent or peel to the built SHA. PATCH only `tag_name`, full `target_commitish`, and `draft: false`; recheck the returned bot-authored release/body and peeled version tag. Keep an already completed phase's verified record when safely resuming; a pre-existing publication alone does not turn an unverified `ready` row green. An uncertain write stays failed unless its exact result can be independently authenticated.

Verdict precedence: conclusion other than `success` fails; success plus `published|nothing|disabled` passes; success plus `ready` passes only after verified publication here; `failed`, unreadable outcome, unresolved dispatch, timed-out run, and eligibility/orchestration errors fail. Summary is pass/fail with run links and short orchestration reasons; release internals stay in target runs.

## Verification

Planning performed read-only source/contract investigation, canonical Git identity checks, tagged-helper existence checks, and API-document verification. Implementation and final verification are complete as recorded below; no hosted dispatch or publication was performed.

**Implementation commands:**

- `uv lock --script tools/tests/test_nightly_runtime.py`, `uv lock --script tools/tests/test_nightly.py`, `uv lock --script tools/tests/test_nightly_workflow.py` — commit reproducible test locks after authoring the suites.
- `run-with-temp uv run --locked --script tools/tests/test_nightly_runtime.py`, `run-with-temp uv run --locked --script tools/tests/test_nightly.py`, `run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py` — expect all behavioral, isolated-process and workflow-mapping cases to pass; disposable repos/artifacts stay below the supplied `TMPDIR`.
- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_nightly_runtime.py`, `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_nightly.py`, `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_nightly_workflow.py` — verify the Python floor as well as the current runner interpreter.
- `run-with-temp uv run --locked --script tools/check_global.py --project-root .` — expect all global checks, existing/new tool suites, actionlint and online zizmor to pass using a privately supplied intended-profile read token; useful logs stay outside `TMPDIR`. Never run tests/lint inside a live App-key job.
- `git diff --check` and `git diff --submodule=log` — expect no whitespace errors, no submodule changes and only story-scoped implementation/documentation changes. Hosted App/schedule wiring can only be claimed from an actual main nightly run; local action doubles establish controller/workflow behavior, not live installation access. Do not invent a module adoption or mutate protected qualification resources to obtain that evidence.

## Auto Run Result

Status: done

This story adds the 02:17 UTC nightly release controller to this superproject. It dispatches adopted modules and Builds, polls the exact created runs against one five-hour deadline, uses the App to publish authenticated ready drafts, and reports a token-free verdict and summary for every target. All three App jobs run in `cicd-app` and have explicit limits of 55, 330 and 55 minutes. Each job mints its own narrowly scoped tokens, and renewals happen in action steps before 50 minutes. The workflow stops at `publish-ready`; story 9 keeps `publish-ready → secretless scan → bump`, with failure continuation.

**This run:** a resumed follow-up review pass (`followup_pass` = true). The implementation session committed `88fa0f6db4e7ed52e015fd449f322115263cbc36` as `done`. A follow-up review session then reopened the spec, applied and verified working-tree corrections, and timed out before logging its triage. This session reviewed the complete diff since `baseline_revision`, including those unlogged corrections, with four fresh layers. It triaged 36 findings, applied the surviving patches and finalized.

**Files changed:**

- `.github/workflows/nightly.yml` — three main-only App jobs; scoped per-target and per-slice mint/renewal slots, including a ninth poll slice; failure seeds, handoffs and reports; main-only concurrency grouping.
- `tools/nightly_runtime.py` — bounded clocks; the REST/ZIP/state validation boundary; GET retries for transport errors, 5xx and rate limits; uncertain-write reporting; rate-limit-aware artifact downloads; trusted-helper acquisition and reuse.
- `tools/nightly.py` — initialization, eligibility, delivery barrier, dispatch, slice-bounded polling, publication and finalization phases.
- `tools/nightly_publish.py` — original-draft authentication, final publication checks and failure-first verdict reduction.
- `tools/tests/nightly_support.py` — disposable real Git snapshots, HTTP/ZIP boundaries and fake clocks.
- `tools/tests/nightly_publish_cases.py` — producer, draft, artifact and tag checks, plus conclusion-precedence cases.
- `tools/tests/test_nightly_runtime.py` — 26 runtime, hostile-input, deadline, retry/backoff and authenticated-cache tests.
- `tools/tests/test_nightly.py` — 39 controller/publication tests, including race, slice-edge, recovery and failed-initialization regressions.
- `tools/tests/test_nightly_workflow.py` — nine executable workflow-mapping tests, including all 18 publication slots and later-job cancellation.
- `tools/tests/test_nightly_runtime.py.lock`, `tools/tests/test_nightly.py.lock`, `tools/tests/test_nightly_workflow.py.lock` — reproducible test environments; only the workflow harness pins PyYAML.
- `docs/nightly.md` — the operating contract: App prerequisites, the `skip` verdict, handoffs, timing, verdicts, cancellation and rerun behaviour, and the story-9 boundary.
- `README.md` — link to the nightly operating documentation.
- This story spec — tasks, both review triage passes, deferred items and this result.

**Review findings (this pass):** 36 findings (high 0, medium 4, low 23, false 6, maybe-false 3).

- **Patches applied:** 9 entries.
  - Medium (4):
    - GET transport-error retry.
    - Rate-limit handling for artifact downloads.
    - Slice-edge polling regressions.
    - A failed publish-ready initialization withholds write slots.
  - Low (5):
    - Write replies are never treated as definite failures or discarded by post-read checks.
    - App prerequisites in the docs.
    - Corrected rerun guidance.
    - `skip` verdict in the docs.
    - Exit codes asserted on the publish step.
- **Deferred:** 3 entries, all maybe-false, each recorded as `medium (unverified)` in `deferred` along with what would settle it:
  - Rerun outcome-artifact uniqueness.
  - A barrier transition into `waiting`.
  - The anonymous Builds REST quota on hosted runners.
- **Rejected:** each with the reason recorded in the triage log.
  - Ref-dispatch races after the barrier, or before the POST: inherent to ref-based dispatch, fail closed on the frozen head, and the delivery-wait fix is excluded by the intent.
  - Per-module CiCd refetch: no production modules yet; fails closed.
  - Transient poll failures: the spec fails these deliberately, and this pass adds transport/artifact retries.
  - Failed slice mint: an orchestration failure the night must report.
  - Verification record, task list and loop counter: finalization records the evidence, and spec-only fixes are rejected.
  - Test-name mismatch: names only; the behaviour is already covered.
  - Duplicated helper contract: no async helpers exist.
  - Seed duplication: every seed fails closed.
  - Red-night alerting: false, because standard workflow-failure notifications apply.
  - Builds slot order: fair-share budgets apply.
  - `selected_draft` side effect: fails closed before any write.
  - Near-zero write timeout: already reported as uncertain and fails closed.
  - Local-versus-hosted surface: carried from the earlier pass.
  - Helper stdlib imports: false, as the dependency-free suite proves.
  - Wait colour on inherited errors: the night is already red.
  - Cancellation summary and `wait.json` loss: the `always()` finalizers persist, and the intent's "may" allows this.
  - Mid-step cancellation: inherent, and fails closed.
  - `skip-token-revoke`, Builds eligibility and sequential slots: false, since they match the spec and intent.
  - Untested fail-closed branches: they share already-tested paths.

**Follow-up review recommendation:** false. On a follow-up pass a new recommendation needs a patched `high`. This pass patched high 0, medium 4 and low 5.

**Verification performed:**

- **Mutation checks:** each new regression test fails when its fix is reverted. This held for both slice-edge guards, the GET transport retry, the write-reply post-check, the artifact rate-limit delay and the failed-initialization outcome clearing. Every mutated file was restored byte-for-byte.
- **Locks:** all three `uv lock --script` commands passed with the committed locks unchanged.
- **Locked nightly suites, current interpreter and Python 3.12:** runtime 26, controller/publication 39, workflow 9, which is 74 tests per interpreter, all passing with no skips.
  - The first current-interpreter workflow run hit `ModuleNotFoundError: yaml`. Two concurrent `uv` installs of the same script environment had raced. Run again alone, the suite passed.
- **`git diff --check`:** passed once the spec's trailing blank line was removed.
- **Logs:** `_bmad-output/implementation-artifacts/story-8-1-followup2-*.log`, which are gitignored.
- **Global check:** `run-with-temp uv run --locked --script tools/check_global.py --project-root .`, run with the intended CiCd-agent profile supplied privately. It exited 0. These all passed: committed render inputs and render, the immutable delivery bootstrap, render reproducibility, schemas and caller interfaces, acceptable Builds publication, and actionlint 1.7.12 plus online zizmor 1.32.0 over both workflows. All nine tool suites passed, 205 tests in total.

**Residual risks:**

- Hosted behaviour remains unqualified until an actual main nightly run. This covers App installation scopes, service timing of the 60-second target budget, run-attempt and artifact visibility during reruns, and the deferred items.
- Production's registry is empty, so a first hosted night exercises only the Builds target.
- The interrupted session's own findings could not be reconstructed. Its changes were re-reviewed here as part of the complete diff.
- No GitHub settings, credentials, modules, releases or qualification resources were changed. Builds and module pointers, `builds-version`, delivered refs and the delivery bootstrap are unchanged. The change is committed locally without a push.
