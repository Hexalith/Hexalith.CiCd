---
title: 'Nightly Builds bump'
type: 'feature'
created: '2026-11-14'
status: 'in-progress'
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

- [ ] `builds-skip`, `tools/bump_runtime.py` — add the empty skip policy and stdlib stable-tag/skip/acceptability selection primitives, preserving the existing predicates and bounded pagination. Define the versioned JSON handoff before its consumers. Both producer and writer select from their own fresh observations; inability to complete verification is an error. Check the stable UTC night key against reachable automatic bump subjects and body markers on main before producing/pushing another bump.
- [ ] `tools/nightly_runtime.py` — add narrowly scoped release-enumeration, delivery-dispatch, CI-run, attempt-jobs and enable endpoints/queries, plus the new exact JSON member readers. Handle enable's empty HTTP 204 explicitly; preserve redirect, origin, retry, size, redaction and uncertain-write restrictions. Do not widen the existing release state validator.
- [ ] `tools/bump.py`, `tools/bump.py.lock` — add the locked secretless producer. Fetch live CiCd main and needed Builds objects into a disposable workspace; read policy/render causes there; select the tag; render; create a single-parent local candidate with the exact subject and night marker; then invoke `tools/check_global.py` unchanged as the shared global gate. A successful no-op is explicit. A failed check exposes no usable candidate artifact ID.
- [ ] `tools/bump_runtime.py`, `tools/bump_push.py` — define a versioned token-free bounded JSON candidate handoff carrying nightly run/attempt/controller source, full base/candidate and old/new Builds tag/commit identities, and Git object bytes sufficient to reconstruct the exact candidate. Bind artifact ID/name/digest to its producer run/attempt, recompute object identities and reconstruct without checkout/execution of candidate source. Writer independently fetches main/tag/schema data and verifies the exact subject/night marker and that one parent equals the captured base and still-live main. Only `builds-version` and existing regular `rendered/` files may differ: rendered bytes equal parent bytes after old-tag/peeled-commit substitution, with only the schema-default JSON addition exception. Reject additions outside that exception, removals, renames, symlinks, mode changes and unrelated field edits. Read the schema as data; verify property-local defaults and supported references/conditions conservatively, without introducing a competing rendering default policy.
- [ ] `tools/bump_push.py`, `.github/workflows/nightly.yml` — push only after all checks and fresh tag selection, with GITHUB_TOKEN Contents/Actions write; explicitly dispatch `deliver.yml` on main after confirmed push. Add a main-only manual qualification path using that job token on an isolated disposable probe ref: its child commit changes only an inert `rendered/Hexalith.Probe/.github/workflows/probe.yml`; it must not push main, dispatch releases/delivery, or touch modules. Record actual remote SHA/tree and run evidence and remove temporary probe refs/workflows. A definite nested-path workflow-permission rejection selects the specified App fallback: `bump-push` in `cicd-app`, freshly minted CiCd-only Contents/Workflows write, same verifier, and no explicit delivery dispatch. An unrelated auth/transport failure leaves qualification incomplete and cannot be reported as a rejection or success.
- [ ] `tools/nightly_delivery_wait.py` — add stdlib delivery/report/CI observation with one aggregate 90-minute deadline and persistent failure/observation state. Qualify delivery by main, workflow identity, bump ancestry and an actually started `deliver` job in that attempt. Order eligible deliveries by creation time, then run ID; for module CI order completed eligible runs by completion time, then run ID. Bind the unique report to run/attempt/candidate; recheck attempt identity after reading it, rejecting stale/duplicate rerun artifacts. Authorize target repositories using the bumped-main registry and independently verified delivered refs, capped at 17 modules and excluding Builds, never report JSON or the earlier dispatch registry alone. Observe every pushed row, preserve diagnostics across failed siblings, and require successful delivery and qualifying module CI. No-change skips these operations successfully.
- [ ] `tools/nightly_keepalive.py` — add stdlib independent enable calls for exactly nightly.yml/deliver.yml and a fresh-main committer-timestamp check in UTC. If older than 50 days, create and fast-forward push only an empty `build(cicd): keepalive` commit. Use the job's GITHUB_TOKEN Contents/Actions write and preserve failure/cancellation semantics.
- [ ] `.github/workflows/nightly.yml` — wire `bump → bump-push → delivery-wait → keepalive` after publish-ready. Use explicit failed-prerequisite continuation and successful-candidate/push conditions; never mistake missing outputs for no-change. Leave Story 9's insertion boundary documented. Set new timeouts to 55/55/105/15 minutes; preserve existing 55/330/55 limits. Delivery-wait is an App job with its own scoped mints, at least three possible ≤40-minute mint/poll slices against one 90-minute deadline, plus finalization reserve. Do not run tests/render/lint or execute handoff code in App jobs. Surface reports and links even after earlier failures, without making any failed job green.
- [ ] `tools/tests/test_bump.py`, `tools/tests/test_bump_push.py`, `tools/tests/test_nightly_delivery_wait.py`, `tools/tests/test_nightly_keepalive.py`, their adjacent `.py.lock` files, `tools/tests/test_nightly_runtime.py`, `tools/tests/test_nightly_workflow.py`, `tools/tests/nightly_support.py` — cover the matrix through real isolated controllers/Git and behavioral workflow execution. Include nested default additions and wrong defaults, tag/commit substitutions, arbitrary path/mode mutations, new-main/new-release races, same-night reruns and next-night eligibility, artifact corruption/run/attempt swaps, removed-setup repair pushes, red/descendant/cancelled CI, first-result selection, partial mint failure, token boundary reserves, aggregate timeout, enable 204/error and idle-day thresholds. Stub global suite discovery in tests that invoke the global runner to prevent recursive test execution.
- [ ] `docs/nightly.md`, `setup/README.md`, `docs/nightly-bump-qualification.md` — document rollback and one-tag-per-line skip policy, no-op/failure behavior, stage order, token/job limits and the qualified transport with full revisions/run links and cleanup evidence. Preserve the distinction between fixture validation and hosted acceptance; use fixture modules without production adoption.

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

## Review Triage Log

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

Status: ready-for-dev

Halted after planning as requested. Resolved story 8-2 from the supplied spec folder, loaded the canonical companions and all predecessor-story continuity, and completed three read-only investigation subagents. The on-disk specification passed the ready-for-development gate after one repair pass for dependency ordering and the once-per-night behavior.

The plan preserves `cicd-app`, per-job action-minted tokens renewed before 50 minutes, job limits below six hours, and Story 9's scan between publish-ready and bump. The GITHUB_TOKEN hosted probe and its deterministic App fallback are future implementation acceptance work. No blocking intent gaps remain. Warning: oversized.

Only this story specification was created. No implementation, tests, hosted probe, commit or push was performed.


### Implementation verification — 2026-11-14

Implementation is present for the producer, independently verifying writer, delivery observer, keepalive, workflow, locked suites and operating documentation. The read-only intent contract is unchanged. No Builds or module repository changes or production registration were made.

The parent reran all six requested suites through `run-with-temp` with verbose output: producer 9, writer 17, observer 20, keepalive 9, runtime 28 and workflow 19 tests; all 102 passed. Each of the ten I/O matrix rows has a named passing test in those outputs. The producer lock is byte-identical to the renderer lock; `tools/check_global.py` is unchanged. The implementation agent's global pass covered 13 suites/271 tests and both online workflow linters; the parent global run against the final hardened writer completed successfully: 13 suites/272 tests, all global gates, actionlint 1.7.12 and online zizmor 1.32.0 passed.

Hosted qualification remains pending. The configured ordinary CiCd-agent profile is in use, with no GH_TOKEN/GITHUB_TOKEN overrides; its repository reads identify Hexalith/Hexalith.CiCd. Remote main is an ancestor of the local baseline and does not yet contain nightly.yml. There are no production setup files or delivered refs. No hosted write has occurred at this checkpoint, and no transport qualification or final acceptance is claimed.
