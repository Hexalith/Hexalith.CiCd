---
title: 'Nightly Builds bump'
type: 'feature'
created: '2026-11-14'
status: 'done'
baseline_revision: '125bf2db35885fd0aaf4cad6a81109604446b099'
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Nightly currently stops after release publication. It does not propagate the newest acceptable Builds release, observe the resulting delivery and module CI, or keep its schedules enabled.

**Approach:** Extend nightly with a secretless bump producer, an independently verifying push job, a bounded delivery/CI observer, and keepalive. Preserve rollbacks through `builds-version` plus `builds-skip` and qualify the spine's GITHUB_TOKEN transport assumption before declaring implementation complete (CAP-6; AD-7, AD-10, AD-18).

## Boundaries & Constraints

**Always:** Work in this superproject. Capture the current tip of CiCd `main`, independently of the nightly run SHA. Select the numerically newest stable `vX.Y.Z` in that pin's major, excluding `builds-skip`; require a published, immutable release by `github-actions[bot]`, matching remote/local peeled tag identity, and ancestry to Builds `main`. Preserve full canonical Git identities. Re-render and run the existing global checks with only a read-only GITHUB_TOKEN. A push must be fast-forward, with the exact validated candidate and subject `build(cicd): bump Builds to vX.Y.Z`. Permit at most one automatic bump per UTC night, including reruns: use the nightly run's creation date as the stable night key and record `hexalith-nightly-bump: YYYY-MM-DD` in the commit body, so reachable automatic bump commits on main remain durable evidence across midnight.

App jobs use `cicd-app`, mint their own explicitly scoped tokens through the pinned action, and re-mint in action steps before 50 minutes; no token crosses jobs. Keep the existing mint-epoch reserve and `skip-token-revoke: true` behavior. All jobs have explicit timeouts below 360 minutes. Privileged controllers run `python3 -I`, stdlib and hardened git only; schemas and handoffs are data. Parse bounded JSON/ZIP members in memory without archive extraction, reject duplicate keys, and keep credentials out of state, artifacts and logs.

**Never:** Change Builds or module repositories directly, adopt a module, auto-adopt a new major, edit setup/templates/skip policy during an automatic bump, force-push, rebase a candidate, execute artifact-supplied source, or run rendering/tests/linting in an App job. Do not implement Story 9's scan: its insertion point is after `publish-ready` and before `bump`, regardless of publication/scan failures. Ordinary prior-stage failures must not suppress bump or keepalive; explicit cancellation stops new mints and writes. Do not alter existing release publication or delivery's accepted-state/repair contracts.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Upgrade | Current v5.1.0; acceptable v5.9.0, v5.10.0 and v6.0.0 | Select v5.10.0, render on captured live main, locally commit, globally validate, then hand off the exact candidate | An unreadable/incomplete release listing or unverifiable tag state fails; never silently choose from partial evidence |
| Rollback/no change | Pin restored to v5.1.0; bad v5.2.0 in skip; no later eligible tag | Keep v5.1.0; explicit successful no-op; no push, delivery dispatch or delivery wait | Invalid skip syntax fails with its line; absent skip is empty for historical parents; no acceptable tag fails |
| Repeated night | A successful automatic bump already exists for this run's UTC night | Successful no-op, even if another release appeared; a later night may bump again | Unreadable history fails verification rather than bypassing the once-per-night limit |
| Validation/race | Global check fails, main advances, a newer eligible release appears, or push is rejected | No stale candidate reaches main; name the tag/file/reason | Fail the night; retry through the next night's fresh plan; do not blindly retry uncertain writes |
| Unsafe candidate | Wrong artifact identity/parent, extra paths, mode changes, or arbitrary rendered edits | Refuse before any push | Failed report; never trust producer-supplied allowed paths/default claims |
| Schema addition | Existing CI JSON plus newly introduced keys at the new schema's defaults | Permit only absent-key additions justified by that exact tagged schema; preserve every existing value except tag/commit substitution | Unsupported or ambiguous default expressions fail closed; no source execution or guessed defaults |
| Delivery | A noncancelled main delivery actually executes on bump or descendant | Select the first qualifying run; authenticate its current-attempt report; inspect every pushed module commit, including repair pushes | Failed delivery/global/module result, missing/invalid report, skipped deliver job or timeout cannot pass |
| Module CI | Main ci.yml on a pushed SHA or proven descendant | The first completed noncancelled qualifying run decides; only success is green | Ignore PR/unrelated/older/cancelled runs; a later green run cannot replace the chosen red result |
| Long wait | Delivery discovery plus module CI takes multiple slices | Poll every 60 seconds within one persisted 90-minute deadline; renew tokens in slices of at most 40 minutes | Failed mint never falls back to an earlier token; collect sibling observations and fail missing results explicitly |
| Keepalive | Schedules active/disabled; main tip younger/older than 50 days | Attempt both enable calls; create an empty keepalive commit only after more than 50 idle days | Attempt the second enable even if the first fails; report HTTP/push failures; never overwrite a racing main |

</intent-contract>

## Code Map

This map records the planning baseline. The completed execution checklist, verification record and as-built notes below describe the resulting implementation.

- `.github/workflows/nightly.yml` — existing `dispatch`, `wait`, `publish-ready` jobs, timeouts 55/330/55 minutes. Preserve main-only gating, cancellation, cache policy, pinned actions, nonpersistent checkout credentials, failure seeding and final reports. There is no bump/scan placeholder.
- `tools/nightly.py` — `SECONDS`, `permit`, `poll`, `finalize` provide persisted budgets and failure isolation. `tools/nightly_runtime.py` — `Budget`, `API._path`, `_request`, `artifact_member`, `validate_state` provide strict transport and handoff patterns. Existing state is closed to the three release phases; add a separate bump/report contract.
- `tools/check_global.py` — `run`, `check_committed_render`, `check_committed_inputs` require candidate HEAD to contain both inputs and rendered bytes/modes. `check_release` is the existing acceptable-tag reference; `run_tool_tests` discovers every `tools/tests/test_*.py`. It imports third-party dependencies and must remain outside privileged jobs.
- `tools/render.py` — `pinned_contract` requires fetched exact Builds tag objects; `defaults` materializes schema defaults through nested properties, local references and conditionals; `desired_tree` produces callers, CI JSON and sibling perimeter files. Preserve this behavior; do not import the renderer into the writer.
- `tools/delivery_runtime.py` — `Git`, `environment`, `json_read`, `atomic`, `registry` are reusable stdlib boundaries. `tools/delivery_bootstrap.py:row/select` define actual `hexalith.delivery.v1` data; `tools/deliver.py:apply_module` writes `pushed_sha` only for real pushes.
- `.github/workflows/deliver.yml` — fixed `hexalith-delivery` artifact contains only `delivery.json`. Report identity fields `run_id`/`run_attempt` are strings; it also carries `candidate_sha`, `tools_source_sha`, `global`, `failed`, `failures`, `freshness`, and module rows with `accepted_sha`, `advancement`, `application`, `pushed_sha`, `retries`, `reasons`, `processed`. Delivery targets include valid existing delivered refs after setup removal, not only the registry. Consume this contract without changing the writer or bootstrap pin.
- `tools/tests/nightly_support.py`, `delivery_support.py`, `test_render.py:Workspace`, `test_validate.py:Workspace` — real disposable Git remotes, clocks, API/artifact fixtures and tagged schemas. `test_nightly_workflow.py:Workflow` executes actual workflow mappings/conditions/controllers; it currently assumes three phases and needs deliberate extension, not text-only assertions.
- `builds-version` is v5.1.0; `builds-skip` does not yet exist. Production `setup/` is intentionally empty. All 23 predecessor stories are done with completed execution checklists; 4-2/4-3/7/8-1 establish the interfaces above. No predecessor establishes the nested-workflow push result. Existing unrelated deferrals stay with their owning stories.

## Tasks & Acceptance

**Execution:**

- [x] `builds-skip`, `tools/bump_runtime.py` — add the empty skip policy and stdlib stable-tag/skip/acceptability selection primitives, preserving the existing predicates and bounded pagination. Define the versioned JSON handoff before its consumers. Both producer and writer select from their own fresh observations; inability to complete verification is an error. Check the stable UTC night key against reachable automatic bump subjects and body markers on main before producing/pushing another bump.
- [x] `tools/nightly_runtime.py` — add narrowly scoped release-enumeration, delivery-dispatch, CI-run, attempt-jobs and enable endpoints/queries, plus the new exact JSON member readers. Handle enable's empty HTTP 204 explicitly; preserve redirect, origin, retry, size, redaction and uncertain-write restrictions. Do not widen the existing release state validator.
- [x] `tools/bump.py`, `tools/bump.py.lock` — add the locked secretless producer. Fetch live CiCd main and needed Builds objects into a disposable workspace; read policy/render causes there; select the tag; render; create a single-parent local candidate with the exact subject and night marker; then invoke `tools/check_global.py` unchanged as the shared global gate. A successful no-op is explicit. A failed check exposes no usable candidate artifact ID.
- [x] `tools/bump_runtime.py`, `tools/bump_push.py` — define a versioned token-free bounded JSON candidate handoff carrying nightly run/attempt/controller source, full base/candidate and old/new Builds tag/commit identities, and Git object bytes sufficient to reconstruct the exact candidate. Bind artifact ID/name/digest to its producer run/attempt, recompute object identities and reconstruct without checkout/execution of candidate source. Writer independently fetches main/tag/schema data and verifies the exact subject/night marker and that one parent equals the captured base and still-live main. Only `builds-version` and existing regular `rendered/` files may differ: rendered bytes equal parent bytes after old-tag/peeled-commit substitution, with only the schema-default JSON addition exception. Reject additions outside that exception, removals, renames, symlinks, mode changes and unrelated field edits. Read the schema as data; verify property-local defaults and supported references/conditions conservatively, without introducing a competing rendering default policy.
- [x] `tools/bump_push.py`, `.github/workflows/nightly.yml` — push only after all checks and fresh tag selection, with GITHUB_TOKEN Contents/Actions write; explicitly dispatch `deliver.yml` on main after confirmed push. Add a main-only manual qualification path using that job token on an isolated disposable probe ref: its child commit changes only an inert `rendered/Hexalith.Probe/.github/workflows/probe.yml`; it must not push main, dispatch releases/delivery, or touch modules. Record actual remote SHA/tree and run evidence and remove temporary probe refs/workflows. A definite nested-path workflow-permission rejection selects the specified App fallback: `bump-push` in `cicd-app`, freshly minted CiCd-only Contents/Workflows write, same verifier, and no explicit delivery dispatch. An unrelated auth/transport failure leaves qualification incomplete and cannot be reported as a rejection or success.
- [x] `tools/nightly_delivery_wait.py` — add stdlib delivery/report/CI observation with one aggregate 90-minute deadline and persistent failure/observation state. Qualify delivery by main, workflow identity, bump ancestry and an actually started `deliver` job in that attempt. Order eligible deliveries by creation time, then run ID; for module CI order completed eligible runs by completion time, then run ID. Bind the unique report to run/attempt/candidate; recheck attempt identity after reading it, rejecting stale/duplicate rerun artifacts. Authorize target repositories using the bumped-main registry and independently verified delivered refs, capped at 17 modules and excluding Builds, never report JSON or the earlier dispatch registry alone. Observe every pushed row, preserve diagnostics across failed siblings, and require successful delivery and qualifying module CI. No-change skips these operations successfully.
- [x] `tools/nightly_keepalive.py` — add stdlib independent enable calls for exactly nightly.yml/deliver.yml and a fresh-main committer-timestamp check in UTC. If older than 50 days, create and fast-forward push only an empty `build(cicd): keepalive` commit. Use the job's GITHUB_TOKEN Contents/Actions write and preserve failure/cancellation semantics.
- [x] `.github/workflows/nightly.yml` — wire `bump → bump-push → delivery-wait → keepalive` after publish-ready. Use explicit failed-prerequisite continuation and successful-candidate/push conditions; never mistake missing outputs for no-change. Leave Story 9's insertion boundary documented. Set new timeouts to 55/55/105/15 minutes; preserve existing 55/330/55 limits. Delivery-wait is an App job with its own scoped mints, at least three possible ≤40-minute mint/poll slices against one 90-minute deadline, plus finalization reserve. Do not run tests/render/lint or execute handoff code in App jobs. Surface reports and links even after earlier failures, without making any failed job green.
- [x] `tools/tests/test_bump.py`, `tools/tests/test_bump_push.py`, `tools/tests/test_nightly_delivery_wait.py`, `tools/tests/test_nightly_keepalive.py`, their adjacent `.py.lock` files, `tools/tests/test_nightly_runtime.py`, `tools/tests/test_nightly_workflow.py`, `tools/tests/nightly_support.py` — cover the matrix through real isolated controllers/Git and behavioral workflow execution. Include nested default additions and wrong defaults, tag/commit substitutions, arbitrary path/mode mutations, new-main/new-release races, same-night reruns and next-night eligibility, artifact corruption/run/attempt swaps, removed-setup repair pushes, red/descendant/cancelled CI, first-result selection, partial mint failure, token boundary reserves, aggregate timeout, enable 204/error and idle-day thresholds. Stub global suite discovery in tests that invoke the global runner to prevent recursive test execution.
- [x] `docs/nightly.md`, `setup/README.md`, `docs/nightly-bump-qualification.md` — document rollback and one-tag-per-line skip policy, no-op/failure behavior, stage order, token/job limits and the qualified transport with full revisions/run links and cleanup evidence. Preserve the distinction between fixture validation and hosted acceptance; use fixture modules without production adoption.

**Acceptance Criteria:**

- Given an eligible newer Builds release and a live CiCd main newer than the scheduler SHA, when nightly completes its bump stages, then main contains exactly the validated tag/render bump based on that live tip, and the nightly report links its delivery and each pushed module's qualifying CI result.
- Given a rollback to an older tag with the bad newer tag skipped, when the next bump executes, then its remote main remains on the rollback unless a different newer acceptable unskipped tag exists.
- Given a successful automatic bump for a UTC night, when the nightly is rerun or another run from that night sees another release, then no second automatic bump commit reaches main; a following night can select the new release.
- Given release publication failure, when nightly continues, then bump and keepalive still execute and the overall night remains failed; given Story 9 later inserts its scan, when that scan fails, then the same continuation applies after scan completes.
- Given a candidate failing validation, substitution, ancestry, artifact identity or fresh-main/tag checks, when bump-push executes, then no candidate commit is pushed and the failed report names the cause.
- Given a confirmed bump push, when delivery or any required module CI is failed, missing or outside the shared 90-minute deadline, then the nightly Actions run fails with available run links instead of reporting successful propagation.
- Given a delivery wait spanning token slices, when an authenticated operation is attempted, then its token was minted in that job with sufficient reserve before 50 minutes, and each job's configured timeout remains below six hours.
- Given the hosted nested-path probe, when GITHUB_TOKEN succeeds, then the production path uses it and dispatches delivery explicitly; when GitHub definitively rejects that path for workflow permission, then the documented App fallback passes the same checks and relies on its push trigger without duplicate dispatch.
- Given active or disabled schedules and an idle repository, when keepalive runs, then both enable calls are attempted and only a tip older than 50 days gains the exact keepalive commit; failures remain visible in the nightly verdict.

## Spec Change Log

- 2026-11-14 — Hosted verification corrected all seven artifact directories to canonical nonhidden sibling paths and corrected delivery dispatch to authenticate the pinned API's HTTP 200 run-details response. Enable remains exact empty HTTP 204. These are protocol/transport fixes; the intent contract and stage policy are unchanged.

## Review Triage Log

Review 1 (2026-11-15), baseline `125bf2db35885fd0aaf4cad6a81109604446b099`. Layers: blind-hunter (B), verification-gap (V), edge-case-hunter (E). No intent_gap or bad_spec entries; no loopback.

| ID | Finding | Verdict | Route | Evidence |
|----|---------|---------|-------|----------|
| E1 | Producer Builds store lacks tags the global gate's suites read | high | patch P1 | `delivery_support.py:20,79`, `nightly_support.py:154`, `nightly_publish_cases.py:30` fetch/read `v5.1.0` from `ROOT/references/Hexalith.Builds`; the producer fetches only main, tried candidates and the current pin (`bump.py:70-76`). Builds already has v5.2.2, so once the pin leaves v5.1.0 every later gate fails. |
| V5 | Same producer-workspace tag gap (other finding) | high | patch P1 | Same root cause as E1; validate uses `fetch-depth: 0` and `fetch-tags: true` (`deliver.yml`). |
| B2 | Builds and run-identity reads sent without a token | medium | patch P2 | `Transport.select/tag` call `api.get/pages` without a token, so `_headers(None)` sends no Authorization and a rate-limit 403 whose reset exceeds the budget fails the night. Patch covers the producer/writer Builds reads; the observer's single per-night `bind_creation` read stays unauthenticated (low; a token there needs new mint-epoch plumbing in the App job). Delivery's shared anonymous `Transport.builds` reads remain open as DW-35; this patch applies DW-35's suggested remedy only to the new bump reads. |
| E11 | Unauthenticated Builds release/tag/main reads | medium | patch P2 | Same root cause as B2. |
| V6 | Unauthenticated Builds reads (other finding) | medium | patch P2 | Same root cause as B2. |
| V1 | Producer `run_script` exit/timeout/redaction path has no test | medium | patch P3 | Pre-verified gap: every producer test injects `check`; no test reaches `run_script`. |
| B8 | Real render/check path never exercised | medium | patch P3 | Same gap as V1; hosted run executed only qualify mode. |
| V2 | "Report omits authorized target" rule untested | medium | patch P4 | Pre-verified gap at `nightly_delivery_wait.py:304-305`. |
| V3 | Skip-with-newer, draft, author and ancestry selection rules untested | medium | patch P5 | Pre-verified gap at `bump_runtime.py:159-192`; the writer reuses the same selection. |
| V4 | New jobs' timeouts not checked against controller budgets | medium | patch P6 | Pre-verified gap: the existing invariant skips phases outside `controller.SECONDS`. |
| B15 | New jobs excluded from the timeout invariant | medium | patch P6 | Same gap as V4. |
| E2 | `builds-version` without trailing newline blocks every bump | low | patch P7 | `policy()`, render and `check_global` strip one newline, but `verify_diff` requires an exact `tag\n` parent; a hand-restored pin then fails nightly with "parent tag mismatch". Direct comparison correction. |
| B14 | One non-UTF-8 commit body permanently breaks the night guard | low | patch P8 | Strict decode at `bump_runtime.py:123`; current 101-commit history has none. The subject and marker are ASCII, so replacement decoding is a direct correction. |
| E13 | Non-UTF-8 historical commit | low | patch P8 | Same root cause as B14. |
| B3 | Absent `builds-skip` is empty on live main; docs claim "only historical parents" | low | patch P9 | `policy()` and `test_historical_missing_skip_is_empty` treat absence as empty at any base; `docs/nightly.md:126-127` says otherwise. Doc correction. |
| E14 | `builds-skip` deleted from live main is silently empty | low | patch P9 | Same root cause as B3. |
| E15 | Whitespace-only skip line rejected while docs say blank lines are ignored | low | patch P10 | `if not tag` skips only empty lines; whitespace-only lines fail with their line number (NightlyError is a ValueError). Doc correction in `docs/nightly.md` and `setup/README.md`. |
| B1 | GITHUB_TOKEN push to protected main never qualified | maybe-false | defer (medium, unverified) | Ruleset 26812262 has only `deletion` and `non_fast_forward`, so fast-forwards are allowed; classic branch protection was unreadable with the available token. |
| B9 | Writer default logic has no parity test against the renderer on a real schema | maybe-false | defer (medium, unverified) | v5.1.0 and v5.2.2 CI schemas are identical, so `add_defaults` is not yet reached. Parity on a schema that adds defaults is unproven. |
| B4 | Prerelease flag not rejected | low | reject | Every Builds release is `prerelease: false`, and `check_release` uses the same predicates. A new predicate guards an undemonstrated state. |
| B5 | Keepalive re-enables a manually disabled `deliver.yml` | low | reject | The intent matrix requires attempting both enable calls for active or disabled schedules. |
| B6 | Dispatched delivery run id discarded | false | reject | The observer selects the first qualifying delivery by design (also for the App fallback) and `finalize` writes its link to the summary. |
| B7 | A `rejected` qualification exits 0 | low | reject | Manual one-off path; the summary and artifact state the result; qualification already concluded `qualified`. |
| B10 | Two CI schemas break schema lookup | false | reject | `render.pinned_contract` itself requires exactly one `hexalith.ci.v*.json` (`render.py:255-260`). |
| B11 | Candidate author/committer/dates unchecked | low | reject | Needs a compromised producer; identity/date guards add complexity. |
| B12 | Rerunning failed jobs cannot recover the bump chain, undocumented | false | reject | `docs/nightly.md:92-97` documents that rerunning only failed jobs is unsupported for attempt-bound handoffs. |
| B13 | A qualification dispatch can replace a pending scheduled run | low | reject | Requires a scheduled run pending behind a running qualification plus a second dispatch. |
| B16 | `bump.py` dependencies not kept in sync with the scripts it runs | low | reject | Pins currently match `render.py` and `check_global.py`; no automated updater; a sync test is beyond a direct correction. |
| B17 | Seed and controller report vocabularies differ | false | reject | No code reads these report fields; job outputs come only from the controllers. |
| B18 | Delivery dispatch relies on default run details | false | reject | Under the pinned API version, hosted proof 43643836917 returned HTTP 200 run details. |
| B19 | Observer token lacks `contents: read` for compare | false | reject | CiCd, Builds and the sampled module repositories are public. |
| B20 | Missing checkout guards, dead env fallbacks, unpassed `NIGHTLY_CANCELLED` | low | reject | A failed checkout already fails the job, and `!cancelled()` stops bump and keepalive steps; the fallbacks have no effect. |
| B21 | Double blank line, probe sentence, blank-line note | low | reject | Renders identically or is cosmetic; the blank-line note is handled by P10. |
| E3 | Substring tag substitution falsely rejects a valid render | low | reject | Templates contain no literal versions; the tag reaches rendered files only through `builds_tag`/`@tag`. A collision needs setup text containing the old tag, and fails closed. |
| E4 | `add_defaults` sees schema/buildsTag that `render.defaults` does not | false | reject | The only `if` in the real CI schemas tests `solution` (`#/allOf/0`); those keys cannot change the branch. |
| E5 | Nonzero push exit after the remote applied it | low | reject | The intent forbids retrying uncertain writes; the night fails loudly. |
| E6 | Report persistence raises after a confirmed push | low | reject | Needs a local atomic write failure right after an identical successful write at `bump_push.py:97`. |
| E7 | Empty artifact outputs silently skip bump-push | false | reject | A failed upload fails the bump job (no `continue-on-error`); a successful upload sets both outputs. |
| E8 | A transient discovery error stays sticky in the verdict | low | reject | The observer is fail-closed by design; discovery spans a few polls after explicit dispatch, and GETs already retry three times. |
| E9 | Descendant registry differs from the bump commit | low | reject | The intent prescribes the bumped-main registry plus delivered refs; the explicit dispatch runs at the bump tip; a race fails closed. |
| E10 | Repeated compares exhaust MAX_CALLS | low | reject | Needs several completed non-descendant main CI runs per module across 17 modules for a whole slice; caching adds persisted state. |
| E12 | History batch exceeds the 16 MiB Git output bound | low | reject | Current history is 101 commits / 36 KB, roughly 46k commits before the bound. |
| E16 | Producer timeout kills only the direct child | low | reject | Only on the 40-minute timeout; no candidate is uploaded after the error and the runner reaps orphans at job end. |

## Design Notes

The candidate must be committed locally before global checks because those checks compare against HEAD. This commit is still unprivileged until the separate writer has authenticated its objects and constrained its diff. Use a single bounded JSON Git-object envelope rather than archive extraction or a producer-supplied patch executed in the writer.

The observer uses delivery's actual pushed commits, including repair commits after skipped advancement. A later successful run cannot hide the first qualifying failure. The release summary's existing schema remains intact; bump/delivery/keepalive reports supplement it and job failures determine the overall workflow conclusion.

GitHub documents that GITHUB_TOKEN pushes suppress push-triggered workflows while explicit workflow_dispatch creates a run: [token event behavior](https://docs.github.com/en/actions/concepts/security/github_token). The [workflow API](https://docs.github.com/en/rest/actions/workflows#enable-a-workflow) defines enable as PUT with empty 204, and the [attempt-jobs API](https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run-attempt) supplies evidence that delivery actually ran. These sources do not establish the nested rendered-path push result; hosted qualification is an implementation acceptance task, not a planning claim.

## Verification

**Commands, during implementation:**

- `run-with-temp uv run --locked tools/tests/test_bump.py` and the equivalent commands for `test_bump_push.py`, `test_nightly_delivery_wait.py`, `test_nightly_keepalive.py`, `test_nightly_runtime.py`, `test_nightly_workflow.py` — expected: matrix and behavioral workflow scenarios pass, with no credentials or live writes in fixtures.
- `run-with-temp uv run --locked tools/check_global.py` — expected: existing global checks, all discovered tool suites, actionlint and online zizmor pass on committed render inputs/output. Keep useful logs outside TMPDIR.
- Execute the isolated hosted probe and save its exact result in `docs/nightly-bump-qualification.md`; fixture success cannot substitute for the real job token. Validate the chosen route's delivery dispatch/trigger behavior before recording implementation complete. No production module adoption is part of this story.

The earlier planning invocation ended at ready-for-development. This implementation invocation requires every local and hosted check above before completion.

## Auto Run Result

Status: done

Implemented the secretless producer, bounded Git-object envelope, independent stdlib verifier/writer, delivery/report/module-CI observer, schedule keepalive, workflow wiring, skip policy, locked regression suites and operating documentation. The intent contract is unchanged. No Builds/module repository or production registration changed.

The parent verification passed all six initial requested suites (102 tests), every edge-case matrix row, and the unchanged global gate (13 suites/272 tests plus actionlint 1.7.12 and online zizmor 1.32.0). Hosted qualification then exposed and resolved artifact paths containing `..` and the dispatch API's current HTTP 200 response. The corrected workflow passed 21 tests; the dispatch fix passed 114 tests across runtime, writer, release controllers, observer and keepalive. Final parent verification after both hosted fixes passed the unchanged global gate: 13 suites/275 tests, all global checks, actionlint 1.7.12 and online zizmor 1.32.0. Every matrix-covering test is registered, enabled and passing. Mandatory independent review follows.

The [hosted qualification record](../../../../docs/nightly-bump-qualification.md) binds successful nested-path probe 43643834124 and delivery-dispatch proof 43643836917 to source revision `6a7b287b7f2b40614970f10e3479c109f114d863`. The probe artifact was authenticated and its ref cleanup independently confirmed. The separate job-token proof returned actual delivery run 43643848734. That transport uses GITHUB_TOKEN and explicit delivery dispatch; the App fallback was not selected. Temporary workflow cleanup is complete at revision `f5b6389b9363bdf062ada1fed9dc48b028dea462`: its Actions definition is disabled, its file is absent from remote main, and all probe refs are absent. The earlier hosted empty-registry delivery completed successfully, and the authenticated corrected-dispatch delivery has started.

Review 1 (three layers, 43 findings) produced ten patches, two deferrals and no loopback. The serious fix was that the producer now fetches every Builds tag before the shared gate, whose suites read `v5.1.0` from that reference. Without it, every bump after the first would have failed. The other patches authenticate the producer and writer Builds reads with the job token, accept a parent pin with no trailing newline, decode legacy commit bodies leniently, and correct the `builds-skip` docs. They also add regression tests for the shared-gate exit code and redaction, the selection rules, report target omission and the new jobs' timeout budgets. Each defect test failed on the unpatched code, and mutation checks confirmed that the gap tests catch their regressions. The six requested suites passed, and the unchanged global gate passed: 13 suites/283 tests, all eight global checks, actionlint 1.7.12 and online zizmor 1.32.0. The production producer path still has no hosted run, so the first eligible scheduled night is its first live execution.
