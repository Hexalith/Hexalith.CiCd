---
title: 'Delivery: the single write path into modules'
type: feature
created: '2026-11-14'
status: in-progress
baseline_revision: 6d229cab21a30887722e1e1ed58088bb134daad7
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

**Problem:** `deliver.yml` validates desired state but has no writer. Modules need one delivery path that advances accepted state only after their checks pass and repairs their previously accepted state even when the candidate fails validation.

**Approach:** Add the main-only `deliver` job and stdlib controller. Advance each eligible `delivered/<Repo>` ref forward, apply every existing valid ref's committed render through that ref's released Builds perimeter library, and report every result in `hexalith-delivery/delivery.json` (CAP-4, CAP-6, CAP-8; AD-3–7, AD-10).

## Boundaries & Constraints

**Always:** Work in this superproject. Keep exactly the existing `validate` job plus the new `deliver` job. Preserve main push, PR, hourly minute 47 and manual triggers, main concurrency group `deliver` without cancellation, and cancelling `deliver-validate-<ref>` elsewhere. Run delivery only on `refs/heads/main`, after validation regardless of its result, in `cicd-app`. Consume bounded JSON, committed Git objects and anonymous live-main reads. Isolate failures per module and retain accepted refs on skipped updates. Repair accepted state even on failed globals. Use each ref's exact acceptable Builds tag and all perimeter entries. Preserve foreign product content. Upload one report on every entered delivery run, including empty registry and recoverable setup/runtime failures.

**Never:** Retrieve the App private key into this session, a local credential, Builds, a module, fixtures, logs or an artifact. Only the SHA-pinned mint action in the `cicd-app` job receives it. Privileged execution consists of `python3 -I` with stdlib-only CiCd/tagged Builds scripts, Git and SHA-pinned actions. Do not import renderer/validator/global-check modules, parse setup/workflow YAML, execute module code/hooks/filters, recurse submodules, extract downloaded artifacts, run uv/npm/lints/tests, sign App JWTs, or use personal tokens there. Never force-push, rebase a generated commit, deliver an unaccepted render to a skipped module, deliver to Builds, or write a module that has no accepted ref. This story adds infrastructure, not production setup files, onboarding, nightly scheduling, publication or the later instruction/deny policy.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Advance and apply | Global verdict true; anonymous and App checks pass | Create/advance accepted ref to exact candidate; apply complete accepted perimeter to live module main; one `build(cicd): …` commit only if its tree changes | Record accepted and pushed full SHAs |
| Idempotence | Live main already matches accepted perimeter | Preserve module head; no commit or push | `unchanged` |
| Candidate rejected for one module | Anonymous/App check fails | Keep its previous ref and repair from it; healthy siblings advance and deliver | Name skipped check; aggregate run fails |
| Failed/missing/malformed global verdict | `global` is false, or verdict is missing/malformed | No App precondition checks or ref advances; repair every valid existing ref using trusted accepted tools | Aggregate run fails; no rejected candidate tools execute |
| No accepted state | Module has no ref | No files delivered; eligible passing module may first obtain its accepted ref | Report `no-ref` when not accepted; failed checks remain failures |
| Old run or ref race | Candidate does not descend from current ref | Never move backwards or sideways; report `superseded by <full-sha>` and apply current accepted state | Supersession alone is not a failure; other failures still dominate |
| Invalid accepted ref | Target is not ancestral to current CiCd main | Name and exclude that ref from application and trusted-tools selection; continue other modules | Aggregate run fails |
| Concurrent product push | Module main changes between fetch and push | Refetch, rebuild index from new main and reapply; initial attempt plus at most three reapplications | Exhaustion fails this module; no force/rebase; preserve concurrent product commits |
| Unusable Builds release/source | Unacceptable release, missing perimeter capability or clone/tag mismatch | Fail before executing that tag's code or writing its module | Continue siblings; preserve accepted ref |
| App unavailable for one module | Its scoped mint or authenticated operation fails | Record module failure; continue other slots; never broaden token scope | Existing ref remains; no unauthenticated write |
| Nightly freshness | Hourly event; nightly history absent, fresh or older than 26 hours | Valid empty history exempts freshness; age exactly 26 hours passes; older fails while repairs still run | API/authorization/malformed-data errors are failures, not absence |

</intent-contract>

## Code Map

- `.github/workflows/deliver.yml:1` — only `validate` exists. Triggers, cache mode, concurrency and read-only permissions already meet the contract. `jobs.validate.outputs.verdict` forwards `steps.validate.outputs.verdict`; preserve failure-output propagation.
- `tools/validate.py:139` / `emit_verdict:167` — exact handoff is `{"global": boolean, "modules": [sorted passing setup stems]}`. A global failure can coexist with passing module names. This list is not the registry. Invalid/missing output is conservatively global-failed.
- `tools/render.py:326` — registry filename rules and Builds exclusion; reproduce only filename enumeration from committed objects in the stdlib writer. `tools/validate.py:106` already owns anonymous action/submodule checks. Do not rerun or import these dependency-bearing tools in delivery.
- `tools/check_global.py:66,301,355` — perimeter capability preflight, acceptable-tag predicates and automatic discovery of locked `tools/tests/test_*.py`. Read-only design references; import transitively loads Jinja2/PyYAML/jsonschema. New suites automatically join validation.
- `builds-version` — `v5.1.0`. Fresh read-only verification on 2026-11-14 found published immutable bot release `443617691`, tag source `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`, matching remote/local tag and ancestor of live Builds main. That released tree ships the perimeter schema/loader/library: the delivery-start prerequisite is currently satisfied. Recheck at runtime; never infer capability from mutable checkout HEAD.
- **At `v5.1.0`**, Builds `Github/lib/perimeter_config.py:174` — `load_bytes(data, *, source=...)`; schema resolves relative to exported trusted source. Keep `Github/lib/` and `schemas/` layout.
- **At `v5.1.0`**, Builds `Github/lib/perimeter.py:64,99,685,721` — `Git(repository, *, index_file=None)`, `Snapshot(git, ref)`, `compare(document, actual, *, expected, rendered_root, builds, selected=None)`, `apply(document, repository, *, expected, rendered_root, builds, selected=None)`. Apply writes only the index; delivery owns acquisition, commits and pushes. Use every entry, without restore's selection exclusions.
- **At `v5.1.0`**, `perimeter.py:774` constructs a plain internal `Git`, losing an adapter subclass. Sanitize the entire Python process before importing/calling tagged code; hardening only an outer subclass is insufficient.
- Current Builds `Github/lib/restore.py:82,139,254` and `expected_state.py:51` — design references for private Git/index, anonymous acquisition, nonexecuting Git and scoped authenticated push. Current submodule HEAD is `14f87f2dc5dfce9832154b9fd3aa8159fe3ab73c`; its newer code must not substitute for released `v5.1.0`. Do not invoke restore policy or copy its exclusions/CI dispatch into delivery.
- `tools/tests/test_validate.py:51` — disposable Git workspace patterns; Builds `Github/lib/tests/test_restore.py` and `Github/lib/tests/test_expected_state.py` — behavioral isolation/race patterns. Read-only references.
- `setup/README.md` — current render/validation operations, deliberately empty production registry and deferred story-10-2 policy. Extend with delivery/report/bootstrap maintenance instructions; do not create adoption evidence.
- All 21 prior story specs were examined through delegated continuity investigation. They are `done`, with completed execution lists. Relevant decisions are distilled above; their historical unfinished notes do not reopen completed work. The guard and release consume the accepted ref; restore skips workflows and transition-sensitive entries, making full delivery repair necessary. Cross-repository `$/` qualification remains first-adoption work.

## Tasks & Acceptance

**Execution:**

- [x] `tools/delivery_runtime.py` — add bounded JSON/HTTP and Git adapters plus exact-tag acquisition. Use canonical fixed GitHub remotes/endpoints, identity checks, pagination/time/size caps and no redirects. Reproduce acceptable-release validation without importing dependency-bearing tools. Before cloning/executing each ref's Builds version, verify published immutable bot release, peel annotated tags, verify ancestry to live Builds main, require released perimeter capability and verify acquired tag object/peeled source. Export regular source/schema blobs from Git objects.
- [x] `tools/delivery_bootstrap.py` — add a minimal stdlib selector, initialized failure report and safe JSON state/output handling. Fetch live CiCd main and all `delivered/*` refs without executing their contents. Verify candidate identity/ancestry and parse the exact verdict with strict types, duplicate-key rejection and limits. Accept advancing names only from candidate committed `setup/*.yml`. Treat missing/malformed verdict as global-failed. Choose candidate tools only for a valid true global verdict; otherwise choose the first valid delivered target encountered in `git rev-list --topo-order main` (newest first). Invalid refs are recorded and excluded. Materialize only regular trusted `tools/` blobs into private storage and invoke selected scripts through `python3 -I`. No valid source, or missing controller at that source, produces a failed report and zero writes, with no candidate fallback.
- [x] `tools/deliver.py` — add initialize/module/finalize operations over private bounded JSON state. Enumerate repair targets from all existing delivered refs, unioned with candidate registry on a passing global verdict; on failed globals use accepted-source registry for discovery and never let rejected setup changes suppress existing repairs. Reject Builds and malformed identities. On passing globals perform exactly the App-readable checks below, intersect with anonymous passing names, and create/advance each eligible ref only forward to the validated full candidate SHA. Re-read after races and before applying; record supersession. Keep rejected modules' refs. Process all valid accepted refs even after sibling/global failures.
- [x] `tools/delivery_runtime.py`, `tools/deliver.py` — implement isolated module transactions with a shallow filtered no-checkout/sparse object acquisition, private bare Git storage and index, no submodule recursion, hooks disabled, LFS smudge disabled and no inherited config/helpers/attributes/credentials. Capture tokens privately, then replace the process environment before loading tagged code. Read committed main into the index, apply/recompare all perimeter entries using that ref's tagged library, compare trees, and `commit-tree` with fresh main as sole parent. Push with a process-local `http.https://github.com/.extraheader`, never argv/URL/files. Retry only genuine non-fast-forward races after a changed main, at most three reapplications; auth/transport failures remain failures. Preserve foreign files/partial content and do not parse malformed whole module files before replacing them.
- [x] `tools/deliver.py` — add hourly nightly-freshness checks and report reduction. For schedule events use the latest main `nightly.yml` run's UTC creation time, regardless of conclusion; valid empty workflow/run history means not activated. If the workflow is missing from a successful inventory read, consult path-matched repository run history before treating it as never run; deleting its file must not hide retained nightly history. Authorization failures cannot exempt freshness. Keep repairing if stale or unreadable. Accumulate all failures; finalize report before returning aggregate nonzero.
- [x] `tools/tests/test_delivery_runtime.py`, `tools/tests/test_deliver.py`, `tools/tests/test_delivery_bootstrap.py` and adjacent locks — test the matrix through executed entrypoints, disposable real Git remotes, bounded HTTP fixtures and fake clocks. Export the actual local `v5.1.0` library/schema blobs for compatibility cases; do not replace them with current HEAD or a fake perimeter engine. Exercise all nine entry kinds, malformed whole/partial content, whole-directory extras and modes, foreign partial preservation, zero-diff second run, invalid refs/tag identities, poisoned Git/Python environment, nonexecuting hooks/clean filters, per-module errors, forward/equal/stale/racing refs, retry parentage/exhaustion and token-age failures. Matrix scenarios must observe final remote refs/trees, absence of marker execution and actual report bytes.
- [x] `tools/delivery_bootstrap.py`, `tools/delivery_runtime.py`, `tools/deliver.py`, `.github/workflows/deliver.yml` — commit the tested bootstrap/runtime/controller sources first in this superproject, obtain their canonical full commit SHA directly with `git rev-parse HEAD`, and make that source remotely fetchable before enabling delivery. Then edit the workflow to check out the bootstrap from that literal immutable source SHA into a dedicated sparse path. Never bind the selector to the candidate or a moving ref. This two-change ordering supplies the concrete trust anchor; no fabricated hash or unbound placeholder may ship.
- [x] `.github/workflows/deliver.yml` — add exactly one main-only `deliver` job with `needs: validate` and an unconditional dependency-result condition. Keep `permissions` minimal, `cache-mode: none`, credentials unpersisted, no nested submodules and a 40-minute hard timeout. Invoke the immutable selector with `python3 -I`; pass expressions through `env`/action inputs. Implement 17 sequential ordinal module slots for the canonical 17-module scope, with repo names supplied exclusively by selector JSON outputs. No second module-name list. Ref/registry union overflow fails before writes and still reports. Empty slots skip minting entirely. Each occupied slot has its own pinned mint action with explicit owner/repository/permissions, followed by selected controller processing; a failed mint or controller must not suppress later slots. A failed CiCd-scoped mint blocks ref writes but still permits independently authenticated repairs. A finalizer reduces failures only after all slots, and an always-run pinned upload publishes exactly `hexalith-delivery` containing `delivery.json`. The immutable bootstrap supplies fallback reporting/finalization when selected tools are unavailable, so a missing source cannot suppress the failure artifact.
- [x] `.github/workflows/deliver.yml`, `tools/delivery_runtime.py` — use a separate CiCd-scoped token for accepted refs and nightly reads, with Contents/Workflows write and Actions read. Per-module tokens hold Contents/Workflows write and Administration read when App checks are needed; repair-only execution omits unnecessary Administration access. Mint only through `actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510` (`# v3.3.0`) with explicit `owner`, nonempty `repositories` and `permission-*`. Only that action receives `HEXALITH_CICD_APP_PRIVATE_KEY` and `HEXALITH_CICD_APP_CLIENT_ID`. Bound all operations by a 36-minute soft deadline, reserve report/upload time, and reject token use beyond 50 minutes from minting using conservative monotonic age accounting. Do not persist token values in JSON state. Use pinned checkout `3d3c42e5aac5ba805825da76410c181273ba90b1` and upload `cf430e030ddbb5b0abf93d22962f4752f3646cd9` with version comments.
- [x] `tools/tests/test_delivery_workflow.py` and its locked PEP 723 dependencies — add an executable no-secret harness that parses the real workflow, evaluates its relevant job/step/output/condition mappings and runs actual script commands with external actions substituted at their invocation boundary. Demonstrate main delivery after success/failure/missing validation, PR exclusion, individual mint failure, controller failure isolation, empty slots, overflow, source pinning and artifact upload after errors. Observe execution and resulting report/ref changes, rather than assert YAML source spelling. Confirm controller imports succeed under `python3 -I` without third-party site packages.
- [ ] `setup/README.md` — document report fields, trusted-source selection, ordinal capacity, bootstrap SHA maintenance, failures, runtime prerequisite and token/key boundaries. Run focused tests on Python 3.12 and runner Python, existing tool suites and global checks outside `cicd-app`. Leave all module and Builds sources unchanged.
- [ ] `_bmad-output/specs/spec-cicd/evidence/7/verification.md` — after the implementation's main push activates the workflow, read back its exact-source run/job conclusions and download/inspect the authenticated `hexalith-delivery` report. Record full source/run/artifact identities and confirm the empty production registry causes no module/ref writes. Keep this hosted integration proof separate from disposable multi-module race/failure tests; do not create setups or retrieve the App key for qualification.

**Acceptance Criteria:**

- Given a passing candidate and multiple modules with mixed checks, when the real main delivery path runs, then only eligible accepted refs advance, rejected refs stay fixed, every valid existing ref is reapplied, foreign module content remains, each changed module gets one `build(cicd)` commit pushed with its scoped App token and the artifact exposes both successful repairs and failures.
- Given a failed or absent global verdict and drift in accepted modules, when the same workflow runs, then it uses an immutable selector and newest accepted tools, executes no rejected-candidate tools/App checks/ref advances, repairs all valid accepted renders and uploads a report while failing the run.
- Given invalid/nonancestor accepted refs or a rejected/unavailable Builds tag, when delivery runs, then those sources execute no code and write no module; valid siblings continue, and the report names every rejected identity.
- Given PR, main push, hourly and main manual events, when the executable workflow harness dispatches them, then PR performs validation only, all main events reach the post-validation App job, main delivery is not cancelled by validation runs, and every entered delivery execution attempts the single report upload.
- Given repeated delivery and concurrent product/ref updates, when the controller applies accepted state, then unchanged modules receive no commit, accepted refs never retreat, race retries preserve the newer product parent, and exhausted or non-race write failures leave an explicit failed result.
- Given the selected release lacks the perimeter schema/library, or a scoped mint fails, or untrusted configuration attempts command execution, when delivery proceeds, then the affected writes fail closed, other eligible modules continue, and the App key/tokens never appear in module trees, state, artifacts or diagnostics.
- Given an hourly run before nightly history exists, at exactly 26 hours and beyond 26 hours after a recorded run, when freshness is evaluated, then only the last case is stale; failed/cancelled nightly runs count as runs, API failures are reported separately, and repair still executes.
- Given the implementation is active on main with the current empty production registry, when its exact-source hosted delivery finishes, then its actual Actions artifact contains the final report, the job conclusion agrees with that report, and no module or accepted ref has been written.

## Spec Change Log

## Review Triage Log

## Design Notes

**App-readable checks are deliberately closed.** With each module's scoped token verify installation accessibility, exactly active AD-21 `main` branch and `v*` tag ruleset targets/conditions/rules, code-scanning default setup `not-configured`, Dependabot security updates disabled, and artifact/log retention exactly 90 days. Enumerate inherited rulesets and details, comparing semantic sets rather than names/IDs/order. Main has deletion/non-fast-forward rules; `v*` has update/deletion rules. Ignore hidden `bypass_actors`; all other onboarding preconditions remain manual. Do not add environment, immutable-release, credential or nuget.org checks to delivery.

**Token isolation within two jobs.** One mint naming every setup repo can fail collectively if one installation entry is missing. Seventeen ordinal slots avoid this and keep a single final report without introducing extra jobs or parsing YAML in the App job. Never invoke the mint action with owner plus empty repositories: that widens scope to the installation. Per-slot errors are accumulated; finalization is the only ordinary aggregate-failure exit. A scope/mint failure cannot authorize advancing that module's ref.

The validator job can fail because one module failed while still emitting `global: true`. Use the well-formed global field to select advancement versus replay; a failed job conclusion alone must not suppress eligible siblings. Missing or malformed output always selects replay.

**Report contract.** Write JSON atomically from bootstrap onward. Include run ID/attempt/event, full candidate SHA, tools-source SHA (nullable when unavailable), global verdict, overall failure reasons, freshness result, and a deterministic row per discovered module. Each row includes repository, accepted ref SHA (nullable), advancement result (`advanced`, `unchanged`, `superseded`, `skipped`, `failed`), application result (`pushed`, `unchanged`, `no-ref`, `failed`), pushed module SHA when any, retry count and sanitized check/error reasons. Separate advancement from application: a skipped/superseded module can still receive a repair, and nightly must be able to identify every pushed commit. Failed global/module checks or a failed push make the run fail even when repairs succeed. Supersession and a legitimate empty registry alone do not.

**Endpoint-specific absence.** The Dependabot security-updates check documents HTTP 404 for disabled. Accept that response only alongside successful scoped installation and Administration-protected metadata reads; never reinterpret generic 403/404 authorization failures as compliant configuration. Cap JSON bodies/pagination, reject redirects, redact tokens and escape diagnostic controls. Existing session auth was verified as the CiCd-agent profile with no token overrides; no maintainer profile or App key was used.

Primary API references checked during planning: [pinned mint interface](https://github.com/actions/create-github-app-token/blob/64ab729a6294000f5aa4a4bc0b73d1f32bc45510/action.yml), [installation repository access](https://docs.github.com/en/rest/apps/installations#list-repositories-accessible-to-the-app-installation), [ruleset detail](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset), [CodeQL default setup](https://docs.github.com/en/rest/code-scanning/code-scanning#get-a-code-scanning-default-setup-configuration), [Dependabot status](https://docs.github.com/en/rest/repos/repos#check-if-dependabot-security-updates-are-enabled-for-a-repository), [retention](https://docs.github.com/en/rest/actions/permissions#get-artifact-and-log-retention-settings-for-a-repository).

## Verification

**Commands for implementation:**

- `uv run --locked --script tools/tests/test_delivery_bootstrap.py`, `uv run --locked --script tools/tests/test_delivery_runtime.py`, `uv run --locked --script tools/tests/test_deliver.py`, `uv run --locked --script tools/tests/test_delivery_workflow.py` — all behavioral suites pass offline after dependencies are installed; repeat each with `--python 3.12` and runner Python. Commit adjacent locks.
- `uv run --locked --script tools/tests/test_render.py` and `uv run --locked --script tools/tests/test_validate.py` — existing render/verdict behavior remains green.
- `uv run --locked --script tools/check_global.py` — committed inputs/render, exact release/interfaces, all automatically discovered suites and pinned online workflow lints pass with a read-only token outside privileged delivery.
- `git diff --check` and `git status --short` — clean formatting; only planned superproject files change, no module/Builds gitlink change.

Planning validation does not claim these future implementation tests ran. Qualification uses disposable remotes and inert token sentinels; no production adoption, workflow dispatch, App secret read or administrative mutation is required to complete this plan.

## Auto Run Result

Status: ready-for-dev

Halted after planning as explicitly requested. The ready-for-development gate passed: tasks have concrete paths/actions and dependency order; acceptance criteria observe workflow/report and remote Git behavior using Given/When/Then; trust, credential, release prerequisite and failure/retry decisions are resolved. The spec exceeds the template's size target and carries `warnings: [oversized]`.

Planning used three subagents for all prior-story continuity and focused source/API investigation. The superproject was clean on `main` at baseline `6d229cab21a30887722e1e1ed58088bb134daad7`. Only this story spec was created; implementation tasks remain unchecked. No source implementation, commit, push, workflow dispatch, module/Builds edit, administrative mutation or App-key access occurred.

The current pin `v5.1.0` satisfies the perimeter prerequisite: release `443617691` is published, immutable and authored by `github-actions[bot]`; released source `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4` matches the tag, is ancestral to live Builds main, and contains the perimeter schema/library/loader. Runtime must repeat those checks for each accepted ref. Read-only checks used the intended CiCd-agent profile, with no GH_TOKEN/GITHUB_TOKEN overrides; the App private key stayed in `cicd-app`.

Verification for this planning run: canonical Git revisions and clean initial metadata/tree checked; rendered workflow/template and all canonical companions loaded; all 21 prior stories incorporated; tagged library and current integration interfaces inspected; official action/API contracts checked; final specification re-read against the gate and whitespace checked. Implementation tests and hosted delivery qualification remain tasks for the next run.


## Implementation Progress

The source-only changes were committed and pushed before workflow activation:
`8844abd40ab72c3d5547d37d803aec3fbc35c45c` introduced the tested writer,
then `03d130f82366dec8ed70a21a14177ae55ea09ca1` added the tested mint-time
budget gate. The workflow's immutable sparse bootstrap checkout uses the latter
literal full SHA. No module or Builds source/gitlink changed.

The executable suites exercise the real v5.1.0 perimeter engine and disposable
Git remotes. Bootstrap (9), runtime (6), controller (12, including the final
expired-state check) and workflow harness (7 scenarios) cover selection,
advancement, repair, failures, races, credentials and report bytes. The extra
expired-state test exposed and corrected a fixture clock that had not used the
private state's start time; the corrected case passes on Python 3.12 and 3.14.
The existing render (32) and validate (49) suites pass. Online actionlint and
zizmor pass after correcting job-level context availability. Full final global
checks and exact-source hosted artifact qualification are in progress.

The shared root filesystem reached capacity during qualification. Only this
task's generated bytecode was removed; subsequent temporary fixtures and a
private uv cache use `/dev/shm`. No unrelated workspaces or caches were deleted.
