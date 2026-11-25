---
title: 'Migrate Works'
type: 'feature'
created: '2026-11-24'
status: blocked
baseline_revision: eeb0fbffd0ea65d514296529b77519498c56417f
baseline_commit: 117d19c0488bf3855763c0c3bf3270fc04a78fd2
implementation_repository: 'references/Hexalith.Works'
implementation_baseline_revision: '6dc406e07e64e7f4d2b79851b56ba67d25f76300'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

Complete Works adoption under AD-21 and CAP-13. Verify the existing adoption and cleanup against live state, carry forward proof of the product migration and registry entry, and establish passing CI and nightly release evidence for Works.

## Boundaries & Constraints

Check maintainer prerequisites and cleanup first. Use Works' restricted module-agent identity for any product publication, CiCd-agent for central source, and the command-local maintainer profile for repository administration. Preserve owned Works content and foreign settings. Start product work from freshly fetched `main` and pass the adopted standalone Builds checker before any push. Keep shared stages 1–4, the source-identity hook, and the independent 180-minute Platform parity job. Preserve the package audit and all retained tests. Transfer only actual audit waivers, and use a released Builds tag that includes any required transfer. Follow delivery for any change to the perimeter and central nightly for release acceptance.

### Resolution of the adoption blockers

- **Legacy publishing.** Track AD-21 cleanup as a maintainer prerequisite to acceptance Nightly. Use authenticated readbacks to confirm that Works is excluded from all legacy GitHub grants and the legacy automation credentials have lost effective write access to Works. The maintainer must confirm which of EventStore, Memories, Parties and Tenants still depend on the shared legacy Zot key. Qualify scoped replacements that preserve each remaining consumer's required access and deny writes to Works namespaces. Confirm continuity before retiring the identified legacy automation key, then record authenticated proof of retirement and loss of Works write access. Preserve the dedicated Works publisher and unrelated access. For NuGet, Works publishes through trusted publishing only: confirm its scoped policy and its exclusion from the legacy `NUGET_API_KEY` grant. Legacy API keys are obsolete, so their identity and package scope need no readback. Works and CiCd scanner preparation may proceed while the maintainer prerequisites are open.
- **Hosted CI.** Check hosted CI on current Works `main` first. Triage Stage 4 environment setup and integration-test failures by root cause. Route confirmed Works product or test defects through a separate Works PR that preserves the retained tests and their explicit-selection behavior. Route confirmed shared pipeline defects to Builds. The recurring Stage 4 Dapr scheduler bind failure on TCP port `50006` triggers an immediate Builds handoff for diagnosis in the shared environment setup. If the shared producer lookup remains blocked in Stage 2 or the Platform job's Linux preparation, qualify its correction in both entry points. Consume any required Builds correction through an immutable release and normal CiCd delivery. A separately authorized Actions operator may retry a transient failure on the same Works `main` commit. Record any CiCd-agent refusal with its exact result. Require both the shared CI job and the independent Platform parity job to pass against the same exact Works `main` commit and delivered Builds pin before using that commit as the publication base for the discovery candidate.
- **Duplicate scan.** Re-arm story 13 now to complete and qualify the scoped CiCd scanner prerequisite while Builds handles hosted CI recovery and the maintainer handles AD-21 cleanup. Fix discovery errors attributable to the Works-owned Platform parity action and reachable Works-owned scripts using behavior-preserving changes. Preserve all R1–R11 checks, inputs, failure behavior, artifacts, and the independent 180-minute Dapr and Aspire job. Where Works-owned changes cannot express the execution boundary, complete CiCd scanner support for the verified computed Platform checkout, its required scripts, and the sealed export used to execute the gate. Require static discovery from provable committed inputs, including the exact pinned dependency source where traversal is needed. Preserve the existing detection policy, coverage of reachable sources, and explicit failures for unresolved execution or unsafe paths. The shared change must prove positive discovery of the supported boundary and rejection of unproved targets.
- **Scanner checkpoint.** Start from the registered Works actions through the normal CiCd controller. Prove the computed Platform checkout and sealed export against the exact committed Platform gitlink, then follow the source reachable from those execution paths. Continue static proof from committed inputs first. Where proof requires a behavior-preserving source change, record the source revision, file and line, exact diagnostic and owner. Route required Platform changes through the Platform owners and qualify the committed Platform gitlink used by Works. Use the same scanner revision and production policy for the hosted scan of the exact Works `main` publication base and the local scan of the exact candidate. Record complete candidate discovery and the resolved Platform pin. Keep any candidate with unresolved discovery local and hand off its remaining blockers with the same evidence. Complete hosted qualification through the normal CiCd scan workflow before counting an acceptance Nightly.
- **Works candidate publication.** Prepare any new discovery candidate from freshly fetched Works `main`, which already includes the earlier discovery candidate recorded in the checkpoint. Before pushing a discovery candidate through the normal Works PR path, require a report from the normal hosted CiCd scan workflow at the fixed scanner revision and production policy. The report must show a passing Works row with complete discovery for the exact Works `main` base, zero run-level errors and no duplicate involving Works, subject to the scoped prerequisite below. Require complete discovery on the exact local candidate with the same scanner revision and production policy, a passing standalone Builds checker on that candidate, and passing hosted shared CI and Platform parity on the exact Works `main` base and its delivered Builds pin, including after delivery of any Builds correction. Refresh and requalify the candidate after any base change. If a publication prerequisite remains open, preserve the local candidate and record the outstanding prerequisite, its owner and exact evidence.
- **Scoped Works discovery prerequisite.** If the checkpoint establishes that a behavior-preserving Works source change is necessary to clear base discovery failures, allow one dedicated Works PR for that change through the normal Works PR path. For this PR alone, the exact-base hosted report may have a failing Works row due solely to the discovery diagnostics the candidate resolves. Require the exact-base report, zero run-level errors, no duplicate involving Works, both passing exact-base hosted CI jobs, and complete discovery and a passing standalone Builds checker on the exact candidate. After merge, qualify the resulting Works `main` through the normal hosted scan before publishing a further discovery candidate or counting an acceptance Nightly. AD-21 cleanup remains a prerequisite to acceptance Nightly.
- **Handoff after scanner work.** After completing the available scanner work, stop at any unresolved Builds or maintainer handoff that blocks the next gated step. Record the owner and exact missing evidence for Works publication or acceptance Nightly, as applicable.

</intent-contract>

## Code Map

- [Approved Works migration](../../../implementation-artifacts/spec-13-migrate-works.md) preserves the historical approval and acceptance conditions. [AD-21](../../../planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-21--onboarding-sequence) governs ordering. [Gate classification](../gate-classification.md#works-classification-story-13) maps removed workflow/evidence gates and retained product checks.
- `references/Hexalith.Works/.github/actions/{after-unit-tests,platform-parity}/action.yml` runs the reviewed source/package bindings and Platform R1–R11. The product preparation commit removed the tool-only npm files and retired tests. `.husky/` and `NuGetAuditSuppress` were absent at preparation. The historical `NU19xx` warning-severity setting was explicitly excluded from waiver transfer.
- `setup/Hexalith.Works.yml`, `rendered/Hexalith.Works/`, `rendered/Hexalith.Works.perimeter.json` and the Works gitlink comprise registration. Works `.github/hexalith-ci.json` and the live workflow blobs identify the delivered configuration. `builds-version` selects immutable `v6.8.1` at `bf8a28b4bbcec619e8d9764d335f786f2bafb69e`.
- `eng/published-builds.json` in Works binds the reviewed producer handoff. Tagged Builds `Github/lib/published_builds.py` reads that publication in shared Stage 2. `tools/nightly_acceptance.py` judges Works' release, duplicate scan and delivery results against authenticated run artifacts.
- `../evidence/13/` holds the original readbacks, including `provision-registry.json`, `nuget-policy-verification.json`, `nuget-cleanup-verify-cleanup.json`, `legacy-org-secret-cleanup.json` and `authenticated-adoption.json`. Use those as historical evidence. Store only compact current results and digests. Executable historical evidence stays archived.
- Works live `main` was `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf` at planning. [CI run 45397690202](https://github.com/Hexalith/Hexalith.Works/actions/runs/45397690202) hit an HTTP 403 rate limit in the shared producer lookup. [Nightly run 45394054346](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346) also records Works' duplicate scan failure at the Platform parity action's shell command substitution. Distinguish pipeline or permission failures from product failures and report shared defects under the repository guidance.

## Tasks & Acceptance

**Execution**

- [ ] `../evidence/13/` Track and reconcile the maintainer prerequisites against authenticated precondition and cutover readbacks. Record qualified Zot replacements and continuity for the remaining consumers, old key retirement and loss of legacy Works write access, Works' exclusion from the legacy `NUGET_API_KEY` grant, and the retained scoped publishing and immutable release settings.
- [x] `references/Hexalith.Works`, `setup/Hexalith.Works.yml`, and `rendered/Hexalith.Works*` Verify historical preparation and delivery, exact current configuration, and the disposition of product gates and audit waivers. Reuse the existing adoption.
- [ ] `tools/scan_discovery.py`, `references/Hexalith.Works/.github/actions/platform-parity/` and its reachable Works-owned scripts. Complete the scanner checkpoint and resolve Works-owned discovery errors while preserving Platform parity behavior. Record exact-base and exact-candidate qualification evidence or the outstanding path diagnostics and owners. Run the standalone Builds checker on the exact candidate before any module push.
- [ ] `../evidence/13/` Route the recurring Stage 4 Dapr scheduler bind failure to Builds and record its triage and any immutable Builds correction and delivery. Record any separate Works product fix. Before publishing through the normal Works PR path, record passing hosted shared CI and Platform parity on the exact Works `main` base and Builds pin, the hosted CiCd scan of that base, and the exact local candidate discovery and standalone-checker results. Record run and attempt identities, the scan artifact identity and digest, the Works commits, the scanner revision and policy digest. If the scoped prerequisite applies, record why a Works source change is necessary, which base diagnostics it clears, and the clean hosted Works row on the resulting `main` after merge.
- [ ] `references/Hexalith.Works/references/Hexalith.Builds/check.py` and `tools/nightly_acceptance.py` Verify the current adopted source and obtain passing exact-source hosted CI and an eligible central Nightly result. Record any shared pipeline failure or access refusal with exact evidence.

**Acceptance criteria**

- Given the initial adoption receipts and current maintainer readbacks, when AD-21 is reconciled, then Works retains its scoped publish identity and policy, immutable releases are enabled, Works receives no legacy GitHub grants, including `NUGET_API_KEY`, and the retired Zot key cannot publish Works repositories. The other Zot consumers retain their required access.
- Given the product candidate and first delivery, when their exact trees and live successors are compared, then Works retains the two registered product actions and authorized tests, lacks the obsolete tooling and gates, and matches the rendered CI/CD perimeter at the delivered Builds pin.
- Given the registered Works actions and the verified Platform execution boundary, when the normal controller scans the exact Works `main` publication base and the exact local candidate with the same scanner revision and production policy, then both scans record their committed Platform gitlink revision and follow reachable source through the computed checkout and sealed export without executing module code. An unresolved target or unsafe path remains a discovery failure and requires an exact diagnostic and owner handoff. Require complete discovery on the exact candidate.
- Given a Works discovery candidate prepared from current `main`, when publication is evaluated, then it stays local until the normal hosted CiCd scan of the exact base shows zero run-level errors and no duplicate involving Works, the exact local candidate shows complete discovery with the same scanner revision and production policy and passes the standalone Builds checker, and hosted shared CI and independent Platform parity both pass on the exact base and its delivered Builds pin. Require complete discovery on the hosted base except for one dedicated, behavior-preserving Works prerequisite PR whose exact candidate clears the base discovery failures and whose necessity is recorded in the checkpoint. Require a clean hosted Works row on the resulting `main` after that PR merges and before publishing a further discovery candidate or counting an acceptance Nightly.
- Given completed AD-21 cleanup and green shared stages 1–4, source identity and Platform R1–R11 on the adopted Works `main` commit, when a scheduled or eligible dispatched central Nightly with `qualify-bump` disabled processes that commit, then `tools/nightly_acceptance.py --run <run-id> --module Hexalith.Works` exits 0. Require Works' release or nothing-to-release outcome and both CodeQL jobs for the dispatch commit, plus any required post-bump delivery result. The deciding scan must cover that dispatch commit with full Works discovery, no run-level errors and no duplicate involving Works.

## Spec Change Log

- 2026-11-24 — Human resolution for run `20261124-144406-c3cd`. Keep AD-21 and exact-source hosted acceptance mandatory. Allow a behavior-preserving Works-owned fix for duplicate-scan discovery and route persistent shared Stage 2 failure through released Builds and normal delivery.
- 2026-11-24 — Human decision for the current pause of run `20261124-144406-c3cd`. Track the verified Platform execution boundary as a separately scoped CiCd scanner prerequisite alongside Works-owned fixes. Keep authenticated AD-21 credential disposition and full exact-source hosted and Nightly proof mandatory.
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Hold Works candidate publication until the scanner qualifies, exact candidate discovery passes and the shared CI path is verified. Continue AD-21 cleanup in parallel and require it before acceptance Nightly.
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Require clean hosted Works discovery on the exact Works `main` base before candidate publication, and verify the exact local candidate with the same scanner revision and production policy.
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Triage Stage 4 by root cause, route confirmed Works defects through a separate Works PR and confirmed shared defects through Builds, and require both hosted jobs to pass on the exact Works `main` publication base. On `7bd9b18c02985ea5fc320735d16bd6ee0d2f6019`, Dapr setup passed, `WorksAppHostSelectionTests.LiveFactsRequireExplicitSelection` failed, and Platform parity was skipped. [Hosted CI jobs](https://github.com/Hexalith/Hexalith.Works/actions/runs/45480464147)
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Route the recurring Stage 4 Dapr scheduler bind failure to Builds immediately. In parallel, qualify CiCd discovery for both the Works `main` publication base and the local candidate. [Exact verification and owner handoffs](../evidence/13/hosted-ci-triage-20261124.md)
- 2026-11-25 — Human decision for run `20261124-144406-c3cd`. Re-arm story 13 to complete and qualify the scoped CiCd scanner prerequisite while Builds and the maintainer handle their respective prerequisites. Apply the existing Works publication and Nightly acceptance gates.
- 2026-11-25 — Human decision for run `20261124-144406-c3cd`. Re-arm with a scanner checkpoint that requires end-to-end discovery from the registered Works actions through the pinned Platform checkout and sealed export. Qualify the exact hosted base and local candidate, or stop and hand off the precise remaining diagnostics to their owners.
- 2026-11-25 — Human decision for run `20261124-144406-c3cd`. Continue static proof first. Allow one dedicated Works prerequisite PR if a behavior-preserving Works source change is required to clear base discovery failures. Keep exact candidate qualification and exact-base hosted CI mandatory, and require clean hosted discovery on the resulting Works `main` and AD-21 cleanup before acceptance Nightly. [Discovery checkpoint](../evidence/13/computed-platform-checkpoint-20261125.md)
- 2026-11-25 — Human decision. NuGet API keys are obsolete and Works publishes through trusted publishing only. Drop the readback of the legacy NuGet key's identity and package scope. The scoped Works policy and the verified exclusion of Works from the legacy `NUGET_API_KEY` grant cover NuGet under AD-21. The story stays blocked until the Platform owner corrects the Builds tag-to-gitlink pairing and the maintainer completes the legacy Zot cleanup.

## Review Triage Log

## Verification

- [Current AD-21 and exact-tree reconciliation](../evidence/13/reconciliation-20261124.md)
- [Follow-up AD-21 and hosted acceptance readbacks](../evidence/13/auto-run-20261124.md#follow-up-verification)
- [Live AD-21 readback, hosted CI triage and refreshed candidate](../evidence/13/hosted-ci-triage-20261124.md)
- [Exact Works candidate and shared scanner prerequisite](../evidence/13/platform-scanner-prerequisite.md)
- [Pinned source discovery and current hosted CI evidence](../evidence/13/scanner-increment-20261125.md)
- [Computed Platform discovery checkpoint and owner handoffs](../evidence/13/computed-platform-checkpoint-20261125.md)
- [Latest AD-21, adopted perimeter and hosted verification](../evidence/13/ad21-and-hosted-readback-20261125.md)
- [Latest exact base and candidate discovery with owner diagnostics](../evidence/13/platform-boundary-qualification-20261125.md)
- `run-with-temp uv run --locked --script tools/render.py --check` from CiCd.
- `run-with-temp python3 references/Hexalith.Builds/check.py` from a standalone exact Works checkout with the declared direct submodules.
- `python3 tools/nightly_acceptance.py --run <run-id> --module Hexalith.Works` against an actual scheduled or eligible dispatched Nightly run.

## Auto Run Result

**Status** `blocked`

**Blocking condition** Implementation verification failed. Works
`f934f53682fb6f8250370289103a19df65e9480e` failed Stage 3 on drift in the
source records. The separately scoped pin restoration
`4c96591bf94f2345f4d2b7fa8f5077001182054e` passed the source-identity
preflight, standalone Builds checker and shared hosted CI. Its Platform
parity failed because the pinned Platform source pairs Builds tag `v6.7.0`
with a different Builds gitlink. Works `main` independently reconciled its
source records at `0f7963233e721cd758e56000c1bff4da76706756`, superseding
the pin restoration. The Works module-agent opened and then closed PR 26.
Shared CI passed on the successor, and its independent Platform parity
reproduced the tag-to-gitlink failure before the canonical gate. The
Platform owner still needs a qualified correction to that pairing.
[Works PR 26](https://github.com/Hexalith/Hexalith.Works/pull/26) ·
[Successor CI](https://github.com/Hexalith/Hexalith.Works/actions/runs/45592491388)

The local scanner traced the computed checkout and sealed export at Platform
`616e27789f935ebb7f7f33406150ecf2dc9913a2`, clearing 13 Works parity
materializer diagnostics. Exact initial base, candidate and successor scans
each selected 43 files with zero run-level errors and zero Works duplicates.
All failed on 128 pinned Platform diagnostics and two Works source-identity
diagnostics. The normal hosted scan used the prior scanner and also failed.
The scoped Works-only prerequisite cannot clear the Platform failures.
Renderer, focused scanner regression and App inventory checks passed locally.
The broader local validation passed seven module readbacks and timed out in
its global suite. CiCd `main` published the exact scanner source blobs
at `98f9430be01b50985ef5adb8466989548f2f479c`.
[Scanner results and owner handoff](../evidence/13/platform-boundary-qualification-20261125.md)

The AD-21 readback confirmed existing adoption, immutable releases, the
dedicated Works Zot publisher, scoped NuGet policy and all eight legacy
GitHub secret exclusions. No module audit waivers required transfer. The
maintainer handoff remains open for legacy Zot replacement continuity and
retirement.
The acceptance reader exited 1 on scheduled Nightly `45394054346`, which
used an older Works commit. Acceptance still requires eligible exact-source
CI, duplicate discovery, cleanup and Nightly results.
[AD-21 and hosted evidence](../evidence/13/ad21-and-hosted-readback-20261125.md)

