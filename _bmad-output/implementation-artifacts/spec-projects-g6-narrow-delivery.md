---
title: 'Deliver the reviewed Projects G-6 catalog acquisition correction'
type: 'bugfix'
created: '2026-11-16'
status: 'done'
route: 'dispatch'
baseline_commit: 'eba7514e02904c741f6a0a80930d85eb358d385c'
review_loop_iteration: 0
context:
  - /home/administrator/projects/hexalith/cicd/AGENTS.md
  - /home/administrator/projects/hexalith/cicd/docs/projects-g6-catalog-acquisition.md
---

<frozen-after-approval reason="User explicitly authorized implementation, qualification and owner delivery in the invocation">

## Intent

Projects G-6 cannot read the historical Builds catalog selected by its direct Platform source. Acquisition is implemented and tested in CiCd, but the full adoption writer cannot deliver it without registering Projects and changing its perimeter/pins. Add and qualify the smallest CiCd-owned delivery extension, then use it and retain fresh exact-source hosted CI/G-6 evidence or an exact external refusal.

## Boundaries & Constraints

The only module changes are `.github/workflows/ci.yml` plus `.github/actions/prepare-g6-catalog/action.yml` and `prepare.py` from the retained proposal. Acquisition must precede Conversations prepare-build. Reuse the action unchanged and keep the mapper fail-closed/offline. Preserve all product gates, dependency pins, gitlinks, unrelated files, indices and concurrent changes. Do not register/adopt Projects, create an accepted ref, broaden credentials, initialize nested submodules, publish, audit A8, deploy, activate v2 or edit Story 1.17 tracking.

Use `run-with-temp` for disposable repositories/checks. Delivery is explicitly authorized; no new approval checkpoint is needed for this already bounded correction. Work in CiCd only, leaving module working trees untouched. Root will perform remote delivery; implementation agent must not commit, push, dispatch or change other concurrent files.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Exact Projects base and reviewed proposal | Construct exact reviewed result, three paths changed, everything else identical |
| Different live source, proposal, payload or tree | Refuse before push |
| Already delivered exact tree and direct base parent | Idempotent no-op with source receipt |
| Symlink/unexpected mode, extra changed path or missing blob | Refuse |
| Push refused or main advances | Retain bounded failed operation; no force or automatic rebase/reapply |
| Scoped App mint inaccessible | No write; retain GitHub failure |
| Hosted G-6 subsequent failure | Retain logs/artifacts and diagnose separately from acquisition acceptance |

## Owner decision — 2026-11-16

The user replied “fix” to the explicit request to authorize the qualified CiCd reviewed-tree owner gate instead of the adoption-only pinned checker for this exact three-file correction. Record `reviewed-tree-owner-authorized` in the closed manifest and proceed through the existing owner workflow. This exception is limited to Projects base `981ceef13a1abc88219925e73c51a23eb9ac50c2`, unchanged proposal, and result tree `238d933a813d0453e950e1080175d74f12e82975`; all original scope constraints remain in force.

</frozen-after-approval>

## Code Map

- `tools/delivery_runtime.py`: reuse stdlib bounded Git/Transport/Budget, environment isolation and secret sanitization; private bare object store/index; do not change shared runtime behavior.
- `tools/deliver.py:apply_module`: entire accepted perimeter writer, leave unchanged.
- `.github/workflows/deliver.yml`: existing validate/deliver jobs, main-only `cicd-app` and concurrency `deliver`; AD-7 forbids a new secret-bearing job/workflow. Add dispatch choice `projects-g6-catalog` versus default full delivery. Skip all normal writer operations in narrow mode, including report finalization and token minting. Narrow mode must require successful secret-free qualification, use current exact owner source, and mint only Projects Contents/Workflows write through the existing pinned App action. No module code/tests run with secrets.
- `.github/actions/prepare-g6-catalog/` and `tools/tests/test_prepare_g6_catalog.py`: unchanged acquisition and behavioral suite.
- `docs/proposals/projects-g6-catalog.patch`: still applies to Projects `981ceef13a1abc88219925e73c51a23eb9ac50c2`; do not refresh without actual source need.
- Architecture AD-6/7: record a closed pre-adoption exception in task documentation, not the concurrently modified architecture file. No registry/ref or Builds-version resolution.
- `tools/tests/test_delivery_workflow.py`, `delivery_support.py`: existing executable workflow and real-Git boundary harnesses; retain normal behavior.

## Tasks & Acceptance

- [x] `tools/deliver_g6_catalog.py` and `docs/proposals/projects-g6-catalog.json`: closed manifest/controller bound to full base commit/tree, patch SHA256, expected workflow/action blobs and complete output tree. Apply in isolated bare Git/index only. Require exact main and reread after non-forced push; include owner source, actual delivered SHA/tree and exact failed operation in JSON. No configurable remote or module path.
- [x] `tools/tests/test_deliver_g6_catalog.py`: real Git behavioral tests for the matrix, preservation and token isolation; fixture transport substitution only at network boundary, no module commands.
- [x] `.github/workflows/deliver.yml`: narrow dispatch branch within existing job; secret-free qualification tests and pinned-source plan output bind validation to writer. Normal delivery stays unchanged for all existing triggers/default.
- [x] `docs/projects-g6-catalog-acquisition.md`: document narrow contract and exact dispatch; distinguish local qualification, actual delivery, hosted acceptance.
- [x] Run existing acquisition tests, narrow tests, normal delivery workflow tests and relevant lint/security checks. Resolve regressions. Retain useful logs outside TMPDIR.
- [ ] Root: publish only task-owned CiCd changes through scoped CiCd profile, dispatch owner path, inspect exact Projects result and collect new hosted CI/G-6 or precise external blocker.

Acceptance: Given current reviewed Projects source, when narrow owner delivery succeeds, then precisely the proposal is committed with unchanged pins/gates and a fresh CI/G-6 run binds that SHA. Given unexpected source or unauthorized transport, delivery fails without modifying module source. Local tests never stand in for hosted acceptance.

## Implementation Notes

The user authorized preserving concurrent changes; isolation supersedes the skill's generic dirty-tree confirmation. Origin/main CiCd advanced to `94b335c7483ba8fe76ad44de46ee3512017c9a11` through unrelated documentation. The root will publish a task-only commit based on freshly fetched main using a private index/checkout. Original workspace indices remain untouched.

## Spec Change Log

## Review Triage Log

## Verification

`run-with-temp python3 -B tools/tests/test_prepare_g6_catalog.py` and the new behavioral suite; locked existing workflow suite; narrow source/proposal qualification; actionlint/zizmor where available. Run the exact pinned Builds checker before any module push and retain a pre-adoption prerequisite failure without suppressing it. Do not execute module code with an App token.

### Review pass 1 triage

| Finding | Verdict | Evidence and route |
| --- | --- | --- |
| Blind 1: missing pre-push enforcement | high | Production source could mint/push despite recorded checker exit 1. Keep the closed manifest disarmed pending explicit owner decision; no module write while pending. |
| Blind 2: ambiguous push loses accepted write | medium | Reviewer pushed to a real fixture then returned 128; receipt lost delivered identity. Patch candidate retention and remote reconciliation without retries. |
| Blind 3: push stderr discarded | medium | Shared runtime returns stdout only; actual permission/hook diagnostics go to discarded stderr. Patch narrow diagnostic capture without changing shared behavior. |
| Blind 4: stale no-op receipt | medium | Real fixture advanced main during proposal construction; successful unchanged SHA differed from actual main. Patch final rereads. |
| Blind 5: wrong failed operation | low | Missing token retained construct-proposal stage. Patch explicit verification/token stages. |
| Blind 6: missing receipt for test failure | low | Default step success condition skips plan generation after suite failure; upload warns. Patch failed qualification receipt, with no plan/mint. |
| Blind 7: full Builds history for narrow fixtures | low | Unchanged checkout pulls all history/tags, needed only by normal-suite v5.1.0 fixture. Patch narrow checkout to one exact released fixture tag/object. |
| Blind 8: whitelist test stops too early | medium | Existing extra-path case fails complete-tree guard before whitelist. Patch matching mutated tree so the whitelist itself is tested. |
| Blind 9: final reread races untested | medium | Current tests advance before initial verification or rely on final push rejection. Patch owner/module final-reread race cases and assert no write attempt. |
| Blind 10: workflow model omits implicit success | medium | Explicit input-only conditions run through failed/cancelled states in the harness, unlike Actions. Patch the test model and cover failure/cancellation. |
| Edge 1: stale unchanged receipt | medium | Independently reproduced advancing main after initial fetch. Same no-op freshness patch as Blind 4. |
| Edge 2: no-op after mint refusal | low | Empty token returns unchanged on an already delivered tree, contrary to documented failed-mint receipt. Require token on deliver, including no-op. |
| Verification 1: output publication untested | medium | Renaming plan= to wrong_output= leaves 13 controller and 3 workflow cases green. Patch real qualification entrypoint/output-to-workflow coverage. |

All findings were verified before grouping. The owner-gate choice is pending with the user; production delivery will be disarmed meanwhile. Remaining corrections preserve the established design and are being applied by the original implementation agent. No finding is deferred and no unrelated source is reverted.

### Review-derived implementation constraints

Add a closed `pre_push_gate` manifest field (`pending-owner-decision` or `reviewed-tree-owner-authorized`) and keep the production manifest pending until a user decision authorizes this specific alternative. Bind it through the manifest digest in the qualification plan and refuse qualification/mint while pending. An authorization may cover only this exact reviewed base/proposal/result; it never changes normal checker, adoption or module product gates.

Always retain the candidate identity before a push and reconcile remote state after failure/ambiguity without retrying a write. Successful no-op receipts require fresh owner/module rereads and an available scoped token. Preserve explicit failure stages and bounded sanitized Git diagnostics. Exercise actual qualification output publication and failure receipt generation, including the workflow's real condition semantics.

### Review pass 1 corrections and confirmation

All 13 findings are addressed. Follow-up edge review confirmed the original no-op/token boundaries fail closed, ambiguous push identity survives, reconciliation never retries writes, and diagnostic output is bounded and credential-redacted. Follow-up verification review confirmed real qualification output feeds the workflow, failed suites emit failed receipts with no plan/mint, the whitelist is reached, and final reread races attempt no push. No unresolved material finding or deferred correction remains.

The production manifest remains `pending-owner-decision`; a source-bound choice prevents qualification and minting, so the known pinned-check failure cannot be bypassed by dispatch. A separate async question requests the owner's explicit decision on the reviewed-tree alternative. No answer has been assumed.

Final locked Python 3.12 controller qualification: 20 tests passed. Pinned actionlint 1.7.12 and online zizmor 1.32.0 passed the final owner workflow hash `118dde04b95074f04666c855172125284d8d035cca1ecafe10c9c8bc63b6dae0`. The full normal/narrow workflow regression is still being awaited by root; its result will be recorded separately.

Final full locked Python 3.12 workflow regression: all 15 tests passed in 413.228 seconds, including the 17-slot existing path and five narrow-path cases. Root awaited the complete child; no regression run remains active. Local qualification is complete. Owner delivery and fresh Projects CI/G-6 remain pending the source-bound pre-push decision.

### Authorized delivery continuation — 2026-11-16

The user’s “fix” resolves the pending source-bound gate decision. Current remote CiCd is `b836159cea272e5211333296936106cf82833a27`; Projects remains at the reviewed base. Only the manifest decision and explanatory owner documentation/spec are being updated. The acquisition helper, mapper, proposal, workflow mechanism and all normal product gates are unchanged.

The first authorized-manifest rerun failed only because the production-state assertion still required pending-owner-decision. The pending-gate CLI refusal test remains unchanged in behavior; the production-state assertion now belongs with the production manifest/payload check and requires the authorized state. No controller behavior or scope guard changed.

Authorized continuation qualification: all 20 controller tests pass on locked Python 3.12, with the pending refusal behavior retained. The previously published owner source also completed hosted validation and delivery successfully in CiCd run `43920301403`. No workflow/controller runtime change is needed for activation.

### Real-source continuation findings — 2026-11-16

The authorized production read-only probe qualified exact source `61c558fc4a9b02fbfef262bebce76c2c15370194` and the unchanged Projects base/result. Its partial-clone `write-tree` spent roughly a minute checking/fetching untouched object contents. Tree construction must use Git's `--missing-ok` behavior so unchanged promised blobs remain absent, while retaining the exact full input/output tree and three-path comparisons. Add a real filtered-clone behavioral case that proves an unrelated promised blob remains missing after successful construction. No source acquisition, module pin, gate or payload change is authorized by this fix.

The queued narrow dispatches `43924772253` and `43925666921` were cancelled by subsequent push-triggered runs sharing the main delivery concurrency group. Neither executed a delivery job. Concurrent owner commits `61c558fc4a9b02fbfef262bebce76c2c15370194` and `2adf156b24e0a8053de42d7d4bf9b7c15a8b82e4` contain only Memories/Folders documentation/evidence and are preserved. The smallest supported scheduling correction must let the closed pre-adoption path qualify and deliver without cancelling concurrent normal owner work or permitting a second full writer for Projects. Existing normal delivery semantics and all original scope constraints remain required.

### Scoped scheduling decision and acceptance — 2026-11-16

Use a separate `deliver-projects-g6-catalog` concurrency group only for main + workflow_dispatch + projects-g6-catalog. Keep the existing main/default group `deliver`, non-main validation group and cancel behavior unchanged. Keep the same deliver job, cicd-app environment and Projects-only App token. This isolates the one-off pre-adoption operation without cancelling concurrent normal owner work.

The controller must prove Projects is excluded from both full-writer selectors: no case-insensitive Projects entry in the committed setup registry, and no live case-insensitive delivered/Projects accepted ref. Inspect only committed tree metadata and a bounded ls-remote of delivered heads; do not initialize dependencies or fetch accepted histories. Fail closed during qualification and again after final source rereads immediately before push or a successful no-op. Record the phase and absence proof. Existing exact owner/module source and complete tree checks, payload limits, non-forced push and reconciliation remain required.

Qualify registry/ref refusal and their appearance at the final write/no-op boundary with zero push attempts. Exercise the narrow/default/PR group selections in the existing executable workflow harness; preserve all normal cases. Narrow workflow fixtures must represent a genuinely unregistered target. GitHub queue:max would require changing/suppressing the pinned actionlint gate and would still wait behind unrelated normal validation, so it is not used. This scheduling correction changes no module-owned file, pin, gate, credential or tracking.

### Scheduling correction review triage — 2026-11-16

| Finding | Verdict | Evidence and correction |
| --- | --- | --- |
| Blind 1: stale registry/source during ref advertisement | high | A real-Git callback advanced owner main to register Projects during the last ls-remote; the old source passed. Advertise owner main and accepted heads together and require the advertised main to equal the reviewed source. Coordinate all owner write jobs with a shared job-level mutex. |
| Blind 2: stale no-op after ref read | medium | Advancing Projects main inside the new network read returned unchanged for a stale SHA. Recheck the module source after the exclusion probe before a successful no-op/write. |
| Blind 3: nonempty unrelated selectors untested | medium | Added success fixtures had empty registries/refs. Add unrelated entries/refs to successful qualification/delivery/no-op and workflow cases to prove coexistence. |
| Blind 4: unavailable/malformed inventory untested | medium | Existing tests arrange only successful inventories. Add I/O failure, timeout, malformed/invalid/duplicate advertisement cases at qualification and final boundaries; no plan/write/no-op success may result. |
| Blind 5: missing-blob wording | low | Missing unrelated promised content is intentionally allowed; required reviewed payload blobs are verified. Clarify that distinction in the owner document. |
| Edge 1: overlapping full and narrow write phases | medium | Distinct validation groups must not introduce two uncoordinated write phases. Add a shared job-level owner-write concurrency group, retaining independent validation scheduling. |
| Verification 1: inventory failure gap | medium | Pre-verified regression gap: catching inventory errors and treating them as empty could pass the checked tests. Same I/O-boundary tests as Blind 4; retain failed receipts and no plan. |

All findings are addressed within the existing owner job and exact three-file correction. Default/full validation groups and gates remain unchanged. Add `deliver` job-level `concurrency` with a distinct shared key (different from the workflow-level `deliver` key to avoid self-deadlock) and cancellation disabled, applying identically to full and narrow runs. The existing per-mode workflow groups allow at most one active full and one active narrow run; their write jobs serialize without queueing narrow validation behind full validation. Keep the selector checks and post-advertisement module freshness guard in addition to that mutex. No credentials, registry, accepted refs, module files, pins or tracking are changed by this correction.

### Final current-source and hosted result — 2026-11-16

The original request requires source rechecks before delivery. Concurrent product preparation advanced Projects to `4511105bb1f00b8cf762097523de74acc828a001`; independent filtered-Git requalification bound input tree `24c52776922ecca9eca63720347f32ecee64694c` and corrected tree `c5425f42f16a8fe328ae5ec9f7c3d3ad81bd0047` without changing the patch or any output blob, unrelated entry, pin or gitlink. This is the same authorized three-file correction on the reviewed current source. The source guard rejected earlier stale inputs; no automatic module rebase or direct workflow patch was used.

Fresh hosted CiCd run `43933951553` at `6fe837f2fafa0952d21e1690c61cef7a11e6eeab` passed acquisition (17), controller (28), and workflow (17) cases plus production qualification. Actual delivery is externally blocked: the configured App lookup `GET /repos/Hexalith/Hexalith.Projects/installation` returned 404. Its controller receipt fails at require-scoped-token, with no minted token, push attempt, candidate or delivered SHA. Required prerequisite: accessible configured App installation covering Projects under the existing Contents/Workflows request. Credentials, installation settings and tracking were not broadened or changed. No corrected Projects CI/G-6 evidence exists. Implementation/review is complete; actual delivery and hosted runtime acceptance remain pending that external prerequisite.

### Delivered outcome and subsequent-failure diagnosis — 2026-11-16

The authorized App access prerequisite is resolved. Fresh owner run 43939511545
at `2a1128e0106baed22999c4687d7d15e7639f22cf` passed 17 acquisition, 28 controller
and 17 workflow cases, qualified the exact current source, minted the existing
scoped Projects token and successfully delivered
`146d0f7e9964c82da23d31b51e6ab62efdcfdda6`. Its sole parent is the reviewed base;
its complete tree equals `c5425f42f16a8fe328ae5ec9f7c3d3ad81bd0047`. Independent
untruncated hosted-tree comparison proves exactly the three reviewed output
paths and all other entries, pins and gitlinks preserved. No owner source or
proposal rebinding was needed on this continuation.

Fresh Projects CI 43940159468 binds that delivered source, fails at the unchanged
shared-skill fixture import (`@dataclass` decorates `_write_text`, a function),
and skips G-6 behind the existing workflow-gates dependency. Commitlint
43940159230 fails before message validation: its unchanged caller resolves
Builds workflow `6db97d4e9da392ef691ed3f367e73f1b7d2ef318`, whose `npm ci`
requires a lockfile absent from the reviewed Projects source. Both exact logs,
metadata and source diagnoses are retained in the accepted-resume evidence
packet. These are subsequent failures, not successful hosted acquisition/G-6
acceptance. Separate owner fixes and a fresh exact-source run remain required
for runtime acceptance. No existing gate was removed or weakened.

The narrow implementation, review, delivery and requested subsequent-failure
diagnosis are complete. This task-spec status does not change Story 1.17 or
sprint tracking, does not accept runtime G-6, and does not repeat historical
publication/audit/A8 work, deploy or activate v2.
