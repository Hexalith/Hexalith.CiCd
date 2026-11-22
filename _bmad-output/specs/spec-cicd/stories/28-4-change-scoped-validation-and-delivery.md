---
title: 'Change-scoped validation and delivery'
type: feature
created: '2026-11-22'
status: in-review
baseline_revision: 988ffd197c63e8aa67d08c0631b652a69d59469b
review_loop_iteration: 0
followup_review_recommended: false
context:
  - AGENTS.md
  - _bmad-output/specs/spec-cicd/enforcement.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-18.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Every push runs the expensive tool suites and delivery, including prose and receipt changes. These unrelated runs delay nightly release behind the delivery barrier.

**Approach:** Classify committed candidate changes as `none`, `module` or `full` using the approved classes and accepted baseline. Skip only checks excluded by that class, preserving delivery's existing per-module verdict and repair behavior.

## Boundaries & Constraints

**Always:** Use [enforcement](../enforcement.md#what-a-change-runs), [approved criteria](../../../planning-artifacts/sprint-change-proposal-2026-11-18.md#41-storiesyaml-insert-after-story-11-through-a-bmad-spec-update), and [added qualification](../../../planning-artifacts/sprint-change-proposal-2026-11-19.md#backlog-edits-and-acceptance). Classifier is standard-library Python and reads CiCd only, without authentication. PR comparison uses the exact PR base; push/schedule discovers every distinct accepted `delivered/*` commit by anonymous `ls-remote` and blobless depth-1 CiCd fetch, then takes the narrowest classification. Missing, malformed, unknown or unreadable inputs mean full. Compare committed bytes and modes with rename-safe path handling. Existing direct gitlink value changes alone are prose only when `.gitmodules` is unchanged. New/deleted gitlinks, unknown paths and `.gitmodules` changes are shared. Every module-scoped or scheduled validation still performs all global checks except suites, and all per-module checks. Scope is separate from the exact `{global,modules}` verdict. Default existing direct callers to full. Preserve 26-hour freshness, release identity/acceptability and online audit checks.

**Never:** Use push `before` as acceptance; hide a cancelled/red tools change behind a later prose push; narrow delivery or module checks to just affected modules; alter the immutable bootstrap, nightly barrier, token permissions or repository selections; read module checkouts to classify; weaken audits, skip tests or switch credentials. No raw output or new evidence bundle under the spec; record hosted links and identities in this story. Work stays in this superproject.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Prose | PR/push differs from accepted base only in approved prose/receipt paths | `none`; green validate without Builds, module clones or suites; push has no writer/token mint/ref move | Missing base is full |
| Failed predecessor | Red or cancelled tools change followed by prose, accepted state predates tools | `full`; all checks | Never trust previous push |
| Module | Setup plus render/execution/perimeter changes for registered modules | `module`; all globals except suites, all module checks, unchanged delivery | Unknown/ambiguous path full |
| Shared | Pin, template, tools, nested docs/proposals, unknown path, `.gitmodules`, submodule add/delete/mode change | `full`; all checks | Conservative fallback |
| Gitlink | Only value of an existing direct `references/*` mode-160000 entry changes | `none` | `.gitmodules` change full |
| Schedule | Accepted baseline differs only in prose or is identical | `none` classification; all globals except suites, all modules and repair | Freshness/tag/lints preserved |
| Manual/default | workflow_dispatch, no accepted commit, unreadable baseline, missing/unknown/malformed scope | `full`; all checks | No silent narrowing |
| Multiple baselines | Candidate has different classifications against accepted commits | Narrowest sound class across every readable baseline | Any unreadable baseline full |

</intent-contract>

## Code Map

- `tools/change_scope.py` (new): stdlib classification, anonymous Git discovery/fetch, CLI and Actions scope output before any Builds checkout.
- `tools/validate.py:29,162,207`: global child invocation, module loop, CLI; preserve independent global/module failure and JSON verdict, early return on PR/push none.
- `tools/check_global.py` (`run`): every global check remains; only tool suites depend on normalized scope.
- `.github/workflows/deliver.yml:25`: validate checkout/uv/Builds ordering and outputs; classify first, gate Builds/validation, skip writer only on explicit push none. Missing scope keeps repair on failures. Existing narrow Projects manual route remains full and functional.
- `tools/tests/test_validate.py`: real committed Git fixtures and external doubles; extend with scope and check-selection tests rather than a new suite/lock.
- `tools/tests/test_delivery_workflow.py`: executable workflow harness, exact verdict and failure-repair tests; adapt minimally if needed to cover job gating and preserve its existing cases.
- `tools/app-workflow-policy.json`: reviewed delivery job boundary and validate dependency semantic digest must track this authorized scope change. Renew these specific entries after reviewing the diff; preserve every token target, permission and trusted controller identity. `tools/check_app_inventory.py` remains unchanged.
- `tools/repository_inputs.py`: existing prose classification constants and no-live-evidence dependency guard; reuse its PROSE_FILES, PROSE_DIRECTORIES and EVIDENCE_ROOT instead of duplicating their list; preserve prior story 28-3's consumer migration. Do not introduce literal active evidence dependency strings merely to classify filenames.
- `tools/delivery_bootstrap.py:39`: read-only exact verdict shape. Omitting unaffected registered modules falsely reports failure; narrowing module work is explicitly deferred.

## Tasks & Acceptance

**Execution:**
- [x] Implement conservative Git classification and output in `tools/change_scope.py`.
- [x] Thread normalized scope through `validate.py`, `check_global.py` and `deliver.yml`; retain all existing default/full callers and error-repair semantics.
- [x] Extend `test_validate.py` with real Git baselines and external-call assertions covering every matrix row, additions/deletions, renames/modes, distinct baselines and failed fetch/discovery. Adapt the workflow harness only as necessary; renew the specific App inventory boundary/digest.
- [ ] Qualify hosted matrix and timings; record only compact identities, links, verdicts and durations here.

**Acceptance Criteria:**
- Given a prose PR or push equivalent to an accepted commit, when Delivery runs, then validate completes green without Builds checkout, module reads or suites, and a push skips the privileged job and leaves delivered refs unchanged.
- Given module inputs, when validation runs, then render, schemas, immutable bootstrap/publication proofs, caller interfaces, online workflow audits and every per-module check run, tool suites do not, and the existing `{global,modules}` contract still drives delivery.
- Given a shared/tools change or an unknown/unreadable baseline, when Delivery runs, then every check runs even if the previous push failed or was cancelled.
- Given scheduled repair with none scope, when Delivery runs, then only tool suites are skipped and accepted renders are reapplied with freshness, acceptable-tag and lint checks intact.
- Given deployed changes, when hosted qualification completes, then this story records jobs/verdicts/accepted refs/durations/contacted repositories for prose PR, prose push, module setup push, tools push, shared-template run and scheduled repair, plus post-rollout push sample runner-minutes and nightly barrier measurements using the proposal's method. Unexecuted or refused evidence stays explicitly unproven.

## Spec Change Log

## Review Triage Log

### 2026-11-22 — Review pass

- verdicts: 14 findings — high 0, medium 10, low 3, false 1, maybe-false 0
- findings:
  - `[medium]` `[patch]` Blind 1: GitHub case-insensitive comparisons could treat malformed `NONE` as `none` — replaced string-based gates with Python's exact validated numeric skip decision; harness now models case-insensitive equality and tests malformed scope.
  - `[medium]` `[patch]` Blind 2: substituted boundaries hid workflow environment propagation failures — real classifier-main/validator-CLI boundary cases now expand actual workflow env and shell arguments, with only external I/O replaced.
  - `[low]` `[patch]` Blind 3: nested project roots inherited the enclosing Git repository — require the requested root to equal Git's toplevel; real nested/nonrepository fixtures take full without baseline reads.
  - `[low]` `[reject]` Blind 4: serial baseline timeouts have no aggregate deadline — each operation already has a finite 180-second timeout; an aggregate timing policy is not an approved acceptance limit (one minute is an estimate). No ordinary slow-baseline failure was demonstrated, and another timing policy would add state and branching. Hosted classification timing is measured separately.
  - `[low]` `[patch]` Blind 5: prose logs omitted the identity justifying skipped checks — stderr now records exact candidate/baseline IDs and each class, with bounded fixed fallback reasons and no raw exception strings.
  - `[false]` `[reject]` Blind 6: classifier source lacks a selector-source digest — its output can suppress the existing writer but cannot select a token target or broaden permissions. The unchanged immutable bootstrap and reviewed token mappings retain those boundaries; a new source digest does not address the claimed token-selection exposure. Actual suppression correctness is covered by the new boundary/gating tests.
  - `[medium]` `[patch]` Blind 7: hosted scope matrix was absent at review — retained as required execution work; local fixtures do not establish hosted acceptance. Outcomes are recorded below as qualification proceeds.
  - `[medium]` `[patch]` Blind 8: post-rollout push/barrier measurements were absent — retained as required execution work; local test durations are not operational evidence.
  - `[medium]` `[patch]` Gap 1: empty `CICD_CHANGE_SCOPE` mapping escaped the workflow matrix — same root cause and fix as Blind 2; real CLI boundary assertions check verdict, full/narrow child selection and module reads.
  - `[medium]` `[patch]` Gap 2: combined module changes masked a perimeter-only `none` regression — each setup, render, execution and perimeter path is now independently changed against a reset accepted baseline.
  - `[medium]` `[patch]` Intent 1: actual prose job/token/ref behavior was unproven — same hosted execution work as Blind 7, with run/job and accepted-ref identities required below.
  - `[medium]` `[patch]` Intent 2: scheduled repair/freshness/tag/lint behavior was unproven — same hosted matrix work; manual dispatch does not stand in for schedule.
  - `[medium]` `[patch]` Intent 3: local durations did not measure runner-minutes or nightly barrier wait — same operational measurement work as Blind 8.
  - `[medium]` `[patch]` Intent 4: the story contained absence-of-evidence text instead of hosted links — append hosted receipts directly to this story; create no evidence bundle.

Edge-case hunter reported no findings. The four layers were all completed; the platform's three available worker slots required starting the intent layer after the edge layer returned. Five code/test corrections were applied in the existing implementation agent. No findings were deferred.

## Design Notes

Baseline at planning is local main `988ffd197c63e8aa67d08c0631b652a69d59469b`, tree `b529aa8e27910131b63bd4d3883bd62e2ead883a`. Freshly fetched hosted main is `307405aba85e587982b69d6ce5847ab2c06000a3`; local main is three commits ahead and contains 28-3,30-2,30-1 prerequisites. Preserve them. Accepted refs currently all name that hosted main. The first shared implementation push must still take full validation; later prose only becomes none once an accepted ref covers the shared changes. Hosted outcomes are not established by local fixtures.

## Verification

**Commands:**
- `run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_validate.py -v` — all scope and existing verdict/global tests pass.
- `run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_delivery_workflow.py -v` — workflow writer isolation, fallback repair and narrow Projects route pass.
- `run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_repository_inputs.py -v` — no executable evidence or live registry dependency regression.
- `run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_app_inventory.py -v` — inventory checks and adversarial cases pass.
- `run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/render.py --check` — unchanged committed render.
- `git diff --check` — no whitespace errors. Hosted full validation must run online with existing credentials; refusals and independent product failures remain failures.

### Local implementation qualification — 22 November 2026

The committed-source baseline remains `988ffd197c63e8aa67d08c0631b652a69d59469b`,
tree `b529aa8e27910131b63bd4d3883bd62e2ead883a`. All listed local commands
passed: validator **71 tests / 31.439 s**, workflow harness **22 tests /
126.040 s**, repository-input guard **33 tests / 58.372 s**, App inventory
**19 tests / 19.378 s**, locked render comparison and whitespace check.
After the final anonymous-discovery isolation and disposable-fixture changes,
the scope cases passed again (**17 tests / 1.540 s**) and the changed
classifier/Builds-failure workflow case passed (**1 test / 1.482 s**).

Classification compares committed tree entries, including modes and both
sides of renamed paths. Anonymous discovery and baseline acquisition both run
in a private CiCd-only bare repository; the candidate's refs and shallow
boundary are untouched. Tests preserve complete module verdicts, online-proof
and lint selection, default full validation, failed-validation repair and the
existing narrow Projects manual route. The App policy renewal changes only
the delivery job condition and validate dependency digest; the checker,
trusted controllers, token targets and permission entries remain unchanged.

| Qualified candidate input | Git blob identity |
|---|---|
| `tools/change_scope.py` | `8693ab30068583253e08da22f49a8f5a55c85f9a` |
| `tools/validate.py` | `68728488c724a0ba594cdd0baf10b490f36b1fee` |
| `tools/check_global.py` | `f59cd076e06338b860332392661149084edf011e` |
| `.github/workflows/deliver.yml` | `167fec5df03547fa25eac450564cb64810c4b89a` |
| `tools/tests/test_validate.py` | `cff68085253ce3d5a6203951f3017d316928fb8d` |
| `tools/tests/test_delivery_workflow.py` | `e32323547a29ef489851b09d98b15c0844d8a67e` |
| `tools/app-workflow-policy.json` | `f1c566ee4983d140954f8354862f0047fd6057bf` |

**Hosted acceptance remains unproven:** no implementation deployment, hosted
prose PR/push, module setup push, tools push, shared-template run or scheduled
repair was performed by this local qualification. No hosted jobs, accepted-ref
moves, contacted-repository measurements, post-rollout runner-minute sample or
nightly-barrier timings are claimed. The first shared deployment must validate
in full before a later prose change can be equivalent to an accepted commit.

### Refreshed hosted baseline — 22 November 2026

All seven accepted `delivered/*` refs named `307405aba85e587982b69d6ce5847ab2c06000a3` before rollout: AI.Tools, Agents, Commons, Conversations, McpCli, PolymorphicSerializations and Works. The configured CiCd-agent profile (`GH_CONFIG_DIR=/home/administrator/.config/gh-cicd-agent`, account `jpiquot`, no token overrides) can read run/job metadata. A read of repository Actions administration settings returned HTTP 403 (`Resource not accessible by personal access token`); those settings remain unverified. No credential switch was made, and account `admin:true` was not treated as token API authority.

| Baseline observation | Exact source | Result / duration |
|---|---|---|
| [Scheduled delivery 45049397859](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45049397859), attempt 1 | `307405aba85e587982b69d6ce5847ab2c06000a3` | Success; validate 1,312 s, deliver 142 s; 17:25:49–17:50:13 UTC |
| [Push delivery 45042807806](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45042807806), attempt 1 | `307405aba85e587982b69d6ce5847ab2c06000a3` | Success; validate 1,028 s, deliver 136 s; 16:15:31–16:35:03 UTC |
| [Nightly 45009181227](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45009181227), attempt 1 | `705ef75404763c3ba495d2baf06cb6fcd53e7f6a` | Nightly failed; barrier step succeeded in 1,350 s, 09:47:00–10:09:30 UTC. The four preceding barriers took 1, 2, 2 and 3 s. |

These runs predate this implementation. They are baseline observations, not evidence of scoped hosted behavior. The user's explicit request to qualify the hosted matrix requires publishing the reviewed candidate; it supersedes the generic build-auto finalization instruction not to push for that qualification only. Existing profile and enforcement remain in force.

### Post-review local verification

All required commands passed after correction: validator **74 / 32.385 s**, workflow **24 / 135.501 s**, repository-input guard **33 / 61.805 s**, App inventory **19 / 20.029 s**, locked render and whitespace. Combined-output SHA-256 digests (raw output remained disposable): validator `87c4dd71ac56bbfbc51f861382b253a1355074322e6940855a53ff13403ac0c1`; workflow `2f68cc136509c22f3ba9a0d75f30402a4149bd0e43ce0d8aa0cd887eff73ac7f`; repository inputs `95196da06e9d22ddac5f7d461506df9f9e09415e88064b4ffa3323607b46e0b3`; inventory `45c7f8431be1ea58e968e385bfc5a22056c222dbcf076dcc21fd3bc0d4e722b6`; render `1291aa3e9b362345269ae9beeafe32b4c0fd661af64abd60f37f7068e3cc193f`.

The matrix audit maps prose/failed predecessor/module/shared/gitlink/multiple baseline rows to `ScopeTests`; schedule/manual/default selection to `ScopeSelectionTests`; writer/token/ref behavior to `WorkflowTests`; and real environment propagation through six classifier-main/validator-CLI scenarios to `WorkflowBoundaryTests`. Every covering test ran without skips.

Corrected candidate source identities supersede the earlier local candidate table:

| Input | Git blob |
|---|---|
| `tools/change_scope.py` | `8e00471165287f1236a85b0b7c92cad5a1dce3fe` |
| `tools/validate.py` | `68728488c724a0ba594cdd0baf10b490f36b1fee` |
| `tools/check_global.py` | `f59cd076e06338b860332392661149084edf011e` |
| `.github/workflows/deliver.yml` | `ba2c774d1eb6ad0cf8f195b00b3bbce9dd2cb357` |
| `tools/tests/test_validate.py` | `bd3221a06ffcfc0fd2b6166403012ed35a228af9` |
| `tools/tests/test_delivery_workflow.py` | `3b91203f18b32b25568f30957512064309f64314` |
| `tools/app-workflow-policy.json` | `10eab971509c733baf2b7ce75e63400179f1e0be` |

### Hosted rollout and PR refusal

Reviewed candidate `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6`, tree `e2e46d6221f18b6b1b8897b4826a776d58efd5c3`, was pushed with the configured CiCd-agent profile. [Full tools/implementation push 45061641542](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45061641542) started at 19:35:39 UTC; its outcome is pending in this entry. This push also published the three preserved prerequisite commits.

The temporary prose branch candidate is `4e92de6bfdd8e327629bb8936f2d1118ab106d3a`. Both GraphQL `createPullRequest` and REST `POST /repos/Hexalith/Hexalith.CiCd/pulls` refused draft PR creation. REST returned **HTTP 403**, `Resource not accessible by personal access token`, `X-Accepted-GitHub-Permissions: pull_requests=write`, request ID `D284:E8514:144437BD:1E9766B6:6B034458`. Immediately before the REST attempt, effective profile was `/home/administrator/.config/gh-cicd-agent`, account `jpiquot`, target `Hexalith/Hexalith.CiCd`, and both token overrides were absent. Account permissions were readable but did not establish token API authority. A prose PR remains unproven; completing it requires Pull requests write on this repository for the intended profile, or an externally created PR for the qualified branch. No credential switch or grant change was made.

### Hosted full path — accepted

[Run 45061641542](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45061641542), attempt 1, **passed**. Classifier log binds candidate `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6` to baseline `307405aba85e587982b69d6ce5847ab2c06000a3`, class **full** (classification 19:35:49–19:35:50 UTC). All global checks passed, including immutable bootstrap/publication/tag proofs, online lints and **31 suite summaries / 889 tests**. The exact verdict was `{"global":true,"modules":["Hexalith.AI.Tools","Hexalith.Agents","Hexalith.Commons","Hexalith.Conversations","Hexalith.McpCli","Hexalith.PolymorphicSerializations","Hexalith.Works"]}`.

Validate job `137328652129` took **1,548 s** (19:35:42–20:01:30); deliver job `137336083729` took **127 s** (20:02:01–20:04:08). Run wall time was **1,709 s**; summed job time **1,675 s / 27.9167 runner-minutes**. CiCd, Builds and all seven registered module repositories were contacted. Every module row was processed, advanced to the candidate, and applied its accepted perimeter with `application=unchanged`; no module product commit was written. Anonymous `ls-remote` after completion confirmed all seven accepted refs equal `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6`.

[Delivery artifact 14769749145](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45061641542/artifacts/14769749145), `hexalith-delivery`: artifact digest `sha256:3be9a244aa31a9604914e12d610dc4c0b0da52a04fde78c4bb2a431ce8188cc8`; extracted `delivery.json` SHA-256 `1aee33ac8caac2da8e0319fe501af3d9aab654546af8df73c2708a5d2d840bee`; `global=true`, `failed=false`, no failures, tools source equals candidate, freshness `not-scheduled`. Validate log SHA-256 `432dce2a497820f6402e6985f7f7557baba1a380297fa8427d2e850beb00893f` (101,971 bytes). Raw downloads and logs stayed disposable.

**Live read-only barrier experiment:** starting 19:41:39 UTC, the unchanged production `delivery_barrier` function observed this run and cleared in **1,360.633 s**, after 115 live API reads. It used the intended profile's existing read credential and never dispatched releases. Source blobs: `tools/nightly.py` `39545a595d4f7adcc85de5ca6e3fee9b0ed5f7cb`, `tools/nightly_runtime.py` `3e18a8b916e6e029a64f3c891279ccf882cf0537`. This is a measured function call against live Actions state, not a new hosted nightly step; post-rollout hosted nightly timing remains unproven. No new scheduled Delivery has appeared since the pre-rollout run at 17:25:49 UTC.

### Hosted prose push — accepted

[Run 45064426893](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45064426893), attempt 1, **passed**, candidate `b041e24ab85daa132caf13392d0ab48a07e29c5b`, tree `f9d926188962221d5ce38a49d9f35e70ff0614a9`. Only this story receipt changed. Classifier recorded accepted baseline `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6`, class **none** (20:05:57–20:05:58 UTC). Validate job `137337282880` passed in **12 s** (20:05:49–20:06:01), exact verdict `{"global":true,"modules":[]}`. Builds checkout was **skipped**; there were no module checks, global child or suites. Deliver job `137337448682` was **skipped with zero steps**, so no App token mint, accepted-ref write or module write ran. Artifact count was zero. All seven accepted refs remained `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6` after completion. Contacted repository: **CiCd only**.

Wall time was **34 s** (20:05:27–20:06:01); summed job time **12 s / 0.2 runner-minutes**. Validate log SHA-256 `a58a87a5450a11354423b286434cc1b4fdb776f26d129d861ea4b2e0d96058ca` (19,666 bytes). The same unchanged production barrier function, started at 20:05:45 UTC, observed this run queued and cleared in **63.522 s**, with 10 live API reads and one ordinary 60-second poll. This repeats the read-only live experiment; it is not hosted nightly-step evidence.
