---
title: 'Change-scoped validation and delivery'
type: feature
created: '2026-11-22'
status: blocked
baseline_revision: 988ffd197c63e8aa67d08c0631b652a69d59469b
review_loop_iteration: 0
followup_review_recommended: true
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

### 2026-11-23 — Review pass

- Verdicts: 28 findings — high 0, medium 19, low 9, false 0, maybe-false 0.
- Findings:
  - `[low]` `[reject]` Blind 1, classifier authority — the proposed independent code authority would require a new trust model. The approved workflow classifies candidate code, and accepted-ref writes already require the trusted main branch and immutable writer. Shared classifier and rules edits are exercised by the full scope fixtures.
  - `[low]` `[reject]` Blind 2, uv on prose — the existing validator emits the exact verdict using its locked entry point. The approved prose checks exclude Builds, global and module checks and delivery. Removing the runner setup and adding another hosted verdict path would change that interface for a possible setup outage.
  - `[medium]` `[patch]` Blind 3, scope/skip mismatch and repair — the Builds gate and validation now handle missing or failed classifier signals conservatively. Failed validation reaches the existing repair job even when classification said none.
  - `[low]` `[patch]` Blind 4, committed empty trees — explicit empty trees are included in the comparison and a real Git object fixture verifies they select full.
  - `[low]` `[reject]` Blind 5, executable agent paths — D1 explicitly lists the agent tool directories without a content or executable restriction. The repository-input suite still checks executable and shebang-bearing files when it runs. Changing scope for those paths would change the approved classification.
  - `[medium]` `[patch]` Blind 6, empty-output fallback coverage — actual workflow environment expansion and the validator CLI now exercise missing and incomplete classifier outputs.
  - `[low]` `[patch]` Blind 7, schedule fixture — the executable workflow harness now uses a distinct prose candidate and verifies fresh Nightly evidence, ref advancement, actual module repair and accepted render bytes.
  - `[medium]` `[reject]` Blind 8, template receipt — the code path passed. The hosted qualification section records the independently observed outcome.
  - `[medium]` `[reject]` Blind 9, schedule receipt — the hosted qualification section records both observed scheduled runs. The executable fixture proves a repair write and the hosted runs show the in-sync reapply path.
  - `[medium]` `[reject]` Blind 10, prose PR — this is an external credential blocker. The requested GitHub API operation refused Pull requests write under the intended profile.
  - `[medium]` `[reject]` Blind 11, push sample receipt — the measurement section records the independently enumerated Actions API window and class totals.
  - `[medium]` `[reject]` Blind 12, nightly step — there was no hosted Nightly after rollout in the queried window. Measurements of the live production barrier function are labeled separately.
  - `[low]` `[reject]` Blind 13, unrelated gitlinks — the diff includes the intervening sync `4ca71c74269bf7b3374694a72956f37531b8fe10`. The sync is outside this story. The pushes table records the merged tree under its own exact identity.
  - `[low]` `[reject]` Blind 14, temporary Markdown fixture — the earlier fixture entered main through a separate merge and remains useful as the single prose input for the replacement PR qualification branch.
  - `[medium]` `[patch]` Edge 1, missing classifier import — scope normalization in validation is independent of the classifier. A regression test refuses the classifier import and exercises full validation.
  - `[medium]` `[patch]` Edge 2, invalid accepted ref names — reject reserved names and case collisions before fetching. The classifier continues to trust the controlled delivered namespace as approved. Full-history live-main ancestry belongs to the immutable writer.
  - `[medium]` `[patch]` Edge 3, incomplete skip signal — same failure path as Blind 3. Workflow and CLI tests bind the conservative decision to the actual shell argument.
  - `[low]` `[reject]` Edge 4, executable under a prose prefix — same policy decision as Blind 5.
  - `[medium]` `[patch]` Verification 1, locked global CLI scope — the executable fixture proves a failing suite runs for default/unknown and skips for module/none while other errors still affect the exit status.
  - `[medium]` `[patch]` Verification 2, baseline ordering — the fixture places an unreadable baseline after an equivalent one and proves both fetches are attempted.
  - `[medium]` `[patch]` Verification 3, PR baseline wiring — the workflow fixture now uses a divergent delivered baseline and proves the exact PR base is fetched without discovering delivered refs.
  - `[medium]` `[patch]` Verification 4, discovery isolation — the fixture asserts that discovery runs inside the separate initialized bare repository.
  - `[medium]` `[reject]` Intent 1, prose PR — same external authorization blocker as Blind 10.
  - `[medium]` `[reject]` Intent 2, shared-template acceptance — see the resolved hosted evidence for Blind 8.
  - `[medium]` `[reject]` Intent 3, scheduled application — the run records and executable repair fixture address the two surfaces identified in Blind 9.
  - `[low]` `[reject]` Intent 4, push sample — the completed scope sample is measured directly from Actions API metadata and validation logs.
  - `[medium]` `[reject]` Intent 5, hosted Nightly — same missing scheduled Nightly observation as Blind 12.
  - `[medium]` `[patch]` Intent 6, missing classifier — same correction and regression as Edge 1.

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

Wall time was **35 s** (20:05:27–20:06:02); summed job time **12 s / 0.2 runner-minutes**. Validate log SHA-256 `a58a87a5450a11354423b286434cc1b4fdb776f26d129d861ea4b2e0d96058ca` (19,666 bytes). The same unchanged production barrier function, started at 20:05:45 UTC, observed this run queued and cleared in **63.522 s**, with 10 live API reads and one ordinary 60-second poll. This repeats the read-only live experiment; it is not hosted nightly-step evidence.

### Hosted single-module setup — accepted

[Run 45064610266](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45064610266), attempt 1, **passed**, candidate `55d2b3cfd00bb4ca98b6c40e59a11e5af87ed454`, tree `b4ae8dfca8a9c89aa8562f86815066fedf18b09d`. Input was one comment in `setup/Hexalith.Commons.yml` plus prose receipts; parsed configuration and rendered bytes were unchanged. Classifier recorded baseline `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6`, class **module** (20:09:54–20:09:55 UTC). All global checks except tool suites passed, including immutable bootstrap/publication/tag checks and online lints. The verdict remained `global=true` plus all seven registered modules. No suite summaries or tool-suite invocation appeared. Contacted repositories remained CiCd, Builds and all seven modules.

Validate job `137337847305`: **36 s**, 20:09:41–20:10:17. Deliver job `137338739883`: **114 s**, 20:11:13–20:13:07. Run wall time **348 s** from 20:07:20; summed job time **150 s / 2.5 runner-minutes**, with 198 s outside job intervals. All seven accepted refs advanced from `3b171b5f6eb5fb14d4acad36d72b5a11e9ffbce6` to the candidate. Every delivery row was processed and `application=unchanged`, with no module product commit.

[Artifact 14771001798](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45064610266/artifacts/14771001798): artifact digest `sha256:3ac909eca1538b46646edba4cc25a5d1ae3aacbccc9f74fe11ab92497a681dd1`; report SHA-256 `2684d7ea847c0651521827e37d0edd9be16b722aa44a6952431a6a264809ba80`. Report `global=true`, `failed=false`, no failures, tools source equals candidate, freshness `not-scheduled`. Validate log SHA-256 `4c69c29d772fedd499d3533ce6cc64cb640d3bdf2e420c7ea367ec6ec4147631` (56,769 bytes). Raw files remained disposable.

The qualification setup comment is removed in the following shared-template case; its restored blob must equal the original `e88d5d75586650dad2aa96e8fb1badb06e4d9e41`. The shared-template input is a zero-output Jinja comment in `templates/perimeter.json.j2`; global render checks must still prove every rendered byte unchanged.

### Push timing sample method

Repeat the proposal's Actions API method from rollout at **2026-11-22T19:35:39Z**: enumerate completed `deliver.yml` push runs on main in the window, bind each class to its validator log, and report wall time (`run.updated_at - run.created_at`) separately from summed non-skipped job intervals. This includes workflow finalization; the prose and module run envelopes each gain one second beyond their last job completion. At 20:16:26 UTC there were three completed qualification pushes and one pending shared-template case: full 1 (1,675 runner-seconds), none 1 (12), module 1 (150). This small controlled rollout sample is not a five-day population estimate; the historical 13–18 November sample remains 109 completed pushes, 57 prose/receipt/gitlink pushes, 938 runner-minutes and 17.9-minute median for that class. A final refresh below includes subsequent completed pushes.

### Hosted shared template — accepted

[Run 45065364790](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45065364790), attempt 1, passed on `f9a184f44fd1d16c35afca132991b87d0761a106`, tree `ddf1ce1aec1ed8fb81c45cfff147693e3ac98c90`. The classifier chose **full** against `55d2b3cfd00bb4ca98b6c40e59a11e5af87ed454`. The template blob `bc0e2e91dc3f86ac2fe0c0d3692e9321966ce081` adds a zero-output comment and the Commons setup blob returned to `e88d5d75586650dad2aa96e8fb1badb06e4d9e41`. The committed and reproducible render checks passed, alongside all other globals, online lints on 21 workflows and **31 suites / 889 tests**. The verdict was `global=true` with all seven registered modules listed in the full tools push.

Validate job [137340193962](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45065364790/job/137340193962) took **1,539 s** and deliver job [137348344602](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45065364790/job/137348344602) took **188 s**. Wall time was **1,857 s**, 20:15:10–20:46:07 UTC, and combined job time was **1,727 s / 28.7833 runner-minutes**. The run contacted CiCd, Builds and all seven registered modules. All seven refs advanced from the module qualification commit to the template candidate. All seven applications were processed and unchanged, with no module commit written. Anonymous ref readback on 23 November confirmed all seven refs still named the template candidate.

[Delivery artifact 14771804652](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45065364790/artifacts/14771804652) digest `sha256:c540bc6919163305781286ede8ce6d6e3124ece053446089aad86435aff87234`. The report SHA-256 is `2e0356d3bf738929aead61af1a8078d3f12d89f9e78c6b8ca2fbfb10ac78ff97`. The validator job log SHA-256 is `f0d364bd31cc2c509efa9bf54439968161e3ef251c02b3120b5ee2a457407a7d`.

### Hosted scheduled repair — accepted

Both schedule attempts used the template candidate `f9a184f44fd1d16c35afca132991b87d0761a106` as candidate, tools source and the single distinct accepted baseline. Both classified **none**, checked out Builds, passed all globals except suites, passed all seven module checks and emitted `global=true` with all seven modules. The acceptable Builds publication and online actionlint and zizmor checks on 21 workflows passed. Each deliver job ran all seven module slots and processed the accepted perimeter. Every row reported `advancement=unchanged`, `application=unchanged`, and no module commit. The hosted repos were CiCd, Builds and the seven registered modules. Both reports show the existing 26-hour gate found Nightly run `45009181227` fresh at the ages below. The scheduled runs encountered no drift that required a write.

| Scheduled run, attempt 1 | Validate / deliver job, seconds | Wall / job seconds | Freshness age |
|---|---|---:|---:|
| [45079935706](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45079935706), 22:50:24–22:53:14 UTC | `137385573990` 34 / `137385745801` 128 | 170 / 162 | 47,094.606 s |
| [45109480349](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45109480349), 04:02:58–04:06:02 UTC | `137478302532` 30 / `137478481853` 144 | 184 / 174 | 65,849.363 s |

- [Artifact 14777126404](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45079935706/artifacts/14777126404), SHA-256 `2dc2e1eb189023d398e688fad7c9b95444ee27eaff678c5ec39ad2098c1955a5`. Report `13f1f4760f4375d7254a5ae6a93e99e05a2fa6294b636ba5dfe3f7bd88693d97`, validator log `2bb5ebdda9499ad76351994c62f7cfdb2379d3da8ebabdd38d7168d4029db2ef`.
- [Artifact 14788424985](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45109480349/artifacts/14788424985), SHA-256 `d46abd8df106144c44686e05c39a6ba9b94eb6bbd421aad5b1c7e239459c2490`. Report `0d914879aaae7a27f3a3c9ef74fd6f6c3b4206e4c54a4bd6d530a5dc9b0f32f3`, validator log `c42cef25b720a649086ddd000c783079a7dd9e588816b6598e1fff1ab26c0880`.

### Post-rollout push sample and barrier

The completed main-push sample at **2026-11-23T06:46:30Z** includes all six Actions API records from rollout. In addition to the four qualification pushes above, two receipt/gitlink pushes classified **none** against `f9a184f44fd1d16c35afca132991b87d0761a106`. Both had the empty passing verdict, skipped the Builds checkout and writer, emitted no delivery artifact and contacted only CiCd.

| Additional none push, attempt 1 | Candidate / tree | Wall / job seconds |
|---|---|---:|
| [45125263451](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45125263451) | `ebf9f4f1d697745f1df2c71971f6016b78ec6308` / `79ff30394a512e85186523de4d2137682d230b10` | 16 / 12 |
| [45126032405](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45126032405) | `df5803634b98af3ad2f24c8d133289637136f24d` / `4f04aa45e76acb525d9a71be356d923a92036642` | 15 / 11 |

| Scope | Passed pushes | Total runner-minutes | Median job / wall seconds |
|---|---:|---:|---:|
| none | 3 | 0.5833 | 12 / 16 |
| module | 1 | 2.5000 | 150 / 348 |
| full | 2 | 56.7000 | 1,701 / 1,783 |

Total was **59.7833 runner-minutes** across six pushes, with 3 of 6 in the prose/receipt/gitlink class. That class used **35 runner-seconds** here and **938 runner-minutes** across 57 historical pushes. The median job time was **12 s** here and **17.9 min** in the historical sample. The sample covers the actual rollout window and includes the shared implementation and template qualification runs.

The live production barrier function cleared in **1.690 s** at 06:48:44 UTC with five Actions API reads and no sleep. The exact nightly controller and runtime blobs match the two earlier read-only measurements above. This measures an idle delivery queue. Hosted Nightly's most recent barrier is still the pre-rollout 1,350 s step on run `45009181227`. The Actions API returned zero Nightly runs created from rollout through this observation, so the post-rollout hosted nightly step is unmeasured.

### Prose PR qualification branch — authorization blocked

The earlier branch merged independently through `df5803634b98af3ad2f24c8d133289637136f24d`. A fresh candidate on that exact main base changes only `docs/28-4-scope-qualification.md`. The remote branch `qualify/28-4-prose-pr` names commit `e338ede595fc3ca47e9202e5775f3192f30a6306`, tree `02ef17dd67013dbb7fea52e5482be2d39fc489f3`. [Open the draft PR from this branch](https://github.com/Hexalith/Hexalith.CiCd/compare/main...qualify/28-4-prose-pr?expand=1).

The intended CiCd-agent profile at `/home/administrator/.config/gh-cicd-agent` authenticated as `jpiquot` for `Hexalith/Hexalith.CiCd`, with both token overrides absent. The REST create-PR request returned **HTTP 403**, `Resource not accessible by personal access token`, with `X-Accepted-GitHub-Permissions: pull_requests=write`, request `C866:A5B75:B13EAD:146AC0C:6B03E305`. The read-only PR inventory returned no matching PR. Completing this case requires a PR opened by an authorized actor or Pull requests write under the intended profile.

## Auto Run Result

**Status: blocked.** The implemented rollout passed hosted tools, prose push, single-module setup, shared-template and scheduled repair qualification. The prose PR has a prepared branch and requires Pull requests write. The next normal hosted Nightly must supply the post-rollout barrier step timing. The last Actions API check found zero hosted Nightly runs since rollout, and the read-only barrier measurements are recorded with their own timing and context.

The review applied seven medium and two low correction groups. Validator startup and full fallback can operate without importing the classifier. The workflow skips Builds and the writer only on the expected successful classification and validation signals. The classifier treats explicit empty trees, reserved accepted ref names and collisions conservatively. Workflow tests now exercise incomplete scope outputs, divergent PR and delivery baselines, and freshness and accepted-render repair on a distinct scheduled candidate. All 16 rejected findings and their reasons are in the review log. No findings were deferred. Follow-up review is recommended for the repaired gate expressions on the hosted workflow after deployment. The hosted matrix above identifies the already deployed source, and the corrections have local verification.

| Updated input | Change | Git blob |
|---|---|---|
| `tools/change_scope.py` | Include explicit empty trees and reject ambiguous accepted-ref names | `5404369d5f2710fb1956528500e668a22f23cbed` |
| `tools/validate.py` | Keep validation independent of classifier imports | `f69476ee4b6c1f9b566bec17bdee8fd1689b1579` |
| `tools/check_global.py` | Share validator scope normalization | `d5ce30c98c9a27020f9aac6cb403f16312344b2a` |
| `.github/workflows/deliver.yml` | Preserve full validation and repair on missing or failed scope signals | `b6dabfb1dedf3e3c53c163d40d1f358cf5a0aa9b` |
| `tools/tests/test_validate.py` | Verify CLI scope, real Git edges and classifier-independent fallback | `69689bfb69b9fdb8af220974b9657a654342bcef` |
| `tools/tests/test_delivery_workflow.py` | Exercise exact PR and schedule inputs and failed validation repair | `26eeee229f554f85991eb2f2442d666f31a04bbd` |
| `tools/app-workflow-policy.json` | Renew only the validate digest and writer condition | `bbf0e8b8914a5893b86e848202cbe272b6583fb3` |

All five local verification commands passed after correction. Actionlint 1.7.12 passed for the updated Delivery workflow and `git diff --check` passed.

| Local verification | Result / seconds | Combined output SHA-256 |
|---|---:|---|
| Validator | 76 passed / 33.096 | `6fc7db534820e2a528cad5c57b494ff9f2fcecdd600794aa497113b86ead4ee9` |
| Workflow harness | 24 passed / 132.988 | `cc85c636063188614edb7cd00da44ea673371e82a6bef4b9b1970c2a1b0fcc6a` |
| Repository-input guard | 33 passed / 61.359 | `473e00b3fd2055c6b55a30f1cfae3e4bd49cedc25df4aafb9b1f903a3014a673` |
| App inventory | 19 passed / 18.795 | `d545bc4dd29e9dffc11459c104f652b1a68518da638d9a6b320538ed6a62c784` |
| Locked render comparison | passed | `54d515b7b2ab8e70f73a100b4c13cff8e0b62d8e72fb04c9d6818671c73a26d1` |
