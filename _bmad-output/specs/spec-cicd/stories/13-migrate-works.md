---
title: 'Migrate Works'
type: 'feature'
created: '2026-11-24'
status: ready-for-dev
baseline_revision: 'eba76b2d4680eab1a02b7a88df6021a5f4cb3b5f'
implementation_repository: 'references/Hexalith.Works'
implementation_baseline_revision: 'd55cda77c2a42bc523aa3664647cdafb87c87be5'
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

- **Legacy publishing.** Track AD-21 cleanup as a maintainer prerequisite to acceptance Nightly. Use authenticated readbacks to confirm that Works is excluded from all legacy GitHub grants and the legacy automation credentials have lost effective write access to Works. The maintainer must confirm which of EventStore, Memories, Parties and Tenants still depend on the shared legacy Zot key. Qualify scoped replacements that preserve each remaining consumer's required access and deny writes to Works namespaces. Confirm continuity before retiring the identified legacy automation key, then record authenticated proof of retirement and loss of Works write access. Preserve the dedicated Works publisher and unrelated access. For NuGet, identify the credential behind the historical `NUGET_API_KEY` grant and confirm that its Works package scope was removed or that the credential can no longer publish those IDs. The expired key with an unverified secret mapping leaves this check open. Works and CiCd scanner preparation may proceed while the maintainer prerequisites are open.
- **Hosted CI.** Check hosted CI on current Works `main` first. Triage Stage 4 environment setup and integration-test failures by root cause. Route confirmed Works product or test defects through a separate Works PR that preserves the retained tests and their explicit-selection behavior. Route confirmed shared pipeline defects to Builds. The recurring Stage 4 Dapr scheduler bind failure on TCP port `50006` triggers an immediate Builds handoff for diagnosis in the shared environment setup. If the shared producer lookup remains blocked in Stage 2 or the Platform job's Linux preparation, qualify its correction in both entry points. Consume any required Builds correction through an immutable release and normal CiCd delivery. A separately authorized Actions operator may retry a transient failure on the same Works `main` commit. Record any CiCd-agent refusal with its exact result. Require both the shared CI job and the independent Platform parity job to pass against the same exact Works `main` commit and delivered Builds pin before using that commit as the publication base for the discovery candidate.
- **Duplicate scan.** Re-arm story 13 now to complete and qualify the scoped CiCd scanner prerequisite while Builds handles hosted CI recovery and the maintainer handles AD-21 cleanup. Fix discovery errors attributable to the Works-owned Platform parity action and reachable Works-owned scripts using behavior-preserving changes. Preserve all R1–R11 checks, inputs, failure behavior, artifacts, and the independent 180-minute Dapr and Aspire job. Where Works-owned changes cannot express the execution boundary, complete CiCd scanner support for the verified computed Platform checkout, its required scripts, and the sealed export used to execute the gate. Require static discovery from provable committed inputs, including the exact pinned dependency source where traversal is needed. Preserve the existing detection policy, coverage of reachable sources, and explicit failures for unresolved execution or unsafe paths. The shared change must prove positive discovery of the supported boundary and rejection of unproved targets. Qualification must cover the committed execution paths on the exact Works `main` publication base and the paths in the exact local candidate. Record each remaining blocker with its exact source and diagnostic. Qualify the completed scanner change through the normal CiCd scan workflow before counting an acceptance Nightly.
- **Works candidate publication.** Keep the candidate local while CiCd scanner qualification, hosted CI recovery and AD-21 cleanup proceed in parallel. Before pushing the candidate for a normal Works PR, require a report from the normal hosted CiCd scan workflow at the fixed scanner revision and production policy. The report must show a passing Works row with complete discovery for the exact Works `main` commit from which the candidate is prepared, zero run-level errors and no duplicate involving Works. Separately prove complete discovery on the exact local candidate with the same scanner revision and production policy. Require passing hosted shared CI and Platform parity on that same Works `main` base and delivered Builds pin, including after delivery of any Builds correction. Refresh the product candidate from freshly fetched Works `main` after any base change and bind discovery and the standalone Builds checker result to the exact candidate to be pushed. If a publication prerequisite remains open, preserve the local candidate and record the outstanding prerequisite, its owner and exact evidence. AD-21 cleanup remains a prerequisite to acceptance Nightly.
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

- [ ] `../evidence/13/` Track and reconcile the maintainer prerequisites against authenticated precondition and cutover readbacks. Record qualified Zot replacements and continuity for the remaining consumers, old key retirement and loss of legacy Works write access, the legacy NuGet credential disposition, and the retained scoped publishing and immutable release settings.
- [x] `references/Hexalith.Works`, `setup/Hexalith.Works.yml`, and `rendered/Hexalith.Works*` Verify historical preparation and delivery, exact current configuration, and the disposition of product gates and audit waivers. Reuse the existing adoption.
- [ ] `tools/scan_discovery.py`, `references/Hexalith.Works/.github/actions/platform-parity/` and its reachable Works-owned scripts. Complete and qualify the scoped CiCd scanner support for the verified Platform execution boundary. Resolve Works-owned discovery errors while preserving Platform parity behavior. Record the scanner qualification evidence and run the standalone Builds checker on the exact candidate before any module push.
- [ ] `../evidence/13/` Route the recurring Stage 4 Dapr scheduler bind failure to Builds and record its triage and any immutable Builds correction and delivery. Record any separate Works product fix. Before publishing the discovery candidate through its normal Works PR path, record passing hosted shared CI and Platform parity on the exact Works `main` base and Builds pin, and the clean Works `main` row from the hosted CiCd scan. Record run and attempt identities, the scan artifact identity and digest, the Works commit, the scanner revision and policy digest, and the exact local candidate discovery and standalone-checker results.
- [ ] `references/Hexalith.Works/references/Hexalith.Builds/check.py` and `tools/nightly_acceptance.py` Verify the current adopted source and obtain passing exact-source hosted CI and an eligible central Nightly result. Record any shared pipeline failure or access refusal with exact evidence.

**Acceptance criteria**

- Given the initial adoption receipts and current maintainer readbacks, when AD-21 is reconciled, then Works retains its scoped publish identity and policy, immutable releases are enabled, Works receives no legacy GitHub grants, and the retired Zot key and legacy NuGet credential cannot publish Works repositories or packages. The other Zot consumers retain their required access.
- Given the product candidate and first delivery, when their exact trees and live successors are compared, then Works retains the two registered product actions and authorized tests, lacks the obsolete tooling and gates, and matches the rendered CI/CD perimeter at the delivered Builds pin.
- Given the verified Platform execution boundary, when story 13 qualifies its scanner change in CiCd, then the scanner follows the supported pinned execution targets through the computed checkout and sealed export and discovers their reachable source without executing module code. An unresolved target or unsafe path still fails discovery. Use the same scanner revision and production policy to prove complete discovery on the exact Works `main` publication base and the exact local candidate.
- Given the prepared Works candidate, when publication is evaluated, then it stays local until the normal hosted CiCd scan shows complete discovery for the Works `main` commit used as its base, zero run-level errors and no duplicate involving Works. The exact local candidate must separately show complete discovery with the same scanner revision and production policy and pass the standalone Builds checker. Both hosted jobs, shared CI and independent Platform parity, must pass on the same exact Works `main` base and its delivered Builds pin. Publish through the normal Works PR path once those conditions are met.
- Given completed AD-21 cleanup and green shared stages 1–4, source identity and Platform R1–R11 on the adopted Works `main` commit, when a scheduled or eligible dispatched central Nightly with `qualify-bump` disabled processes that commit, then `tools/nightly_acceptance.py --run <run-id> --module Hexalith.Works` exits 0. Require Works' release or nothing-to-release outcome and both CodeQL jobs for the dispatch commit, plus any required post-bump delivery result. The deciding scan must cover that dispatch commit with full Works discovery, no run-level errors and no duplicate involving Works.

## Spec Change Log

- 2026-11-24 — Human resolution for run `20261124-144406-c3cd`. Keep AD-21 and exact-source hosted acceptance mandatory. Allow a behavior-preserving Works-owned fix for duplicate-scan discovery and route persistent shared Stage 2 failure through released Builds and normal delivery.
- 2026-11-24 — Human decision for the current pause of run `20261124-144406-c3cd`. Track the verified Platform execution boundary as a separately scoped CiCd scanner prerequisite alongside Works-owned fixes. Keep authenticated AD-21 credential disposition and full exact-source hosted and Nightly proof mandatory.
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Hold Works candidate publication until the scanner qualifies, exact candidate discovery passes and the shared CI path is verified. Continue AD-21 cleanup in parallel and require it before acceptance Nightly.
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Require clean hosted Works discovery on the exact Works `main` base before candidate publication, and verify the exact local candidate with the same scanner revision and production policy.
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Triage Stage 4 by root cause, route confirmed Works defects through a separate Works PR and confirmed shared defects through Builds, and require both hosted jobs to pass on the exact Works `main` publication base. On `7bd9b18c02985ea5fc320735d16bd6ee0d2f6019`, Dapr setup passed, `WorksAppHostSelectionTests.LiveFactsRequireExplicitSelection` failed, and Platform parity was skipped. [Hosted CI jobs](https://github.com/Hexalith/Hexalith.Works/actions/runs/45480464147)
- 2026-11-24 — Human decision for run `20261124-144406-c3cd`. Route the recurring Stage 4 Dapr scheduler bind failure to Builds immediately. In parallel, qualify CiCd discovery for both the Works `main` publication base and the local candidate. [Exact verification and owner handoffs](../evidence/13/hosted-ci-triage-20261124.md)
- 2026-11-25 — Human decision for run `20261124-144406-c3cd`. Re-arm story 13 to complete and qualify the scoped CiCd scanner prerequisite while Builds and the maintainer handle their respective prerequisites. Apply the existing Works publication and Nightly acceptance gates.

## Review Triage Log

## Verification

- [Current AD-21 and exact-tree reconciliation](../evidence/13/reconciliation-20261124.md)
- [Follow-up AD-21 and hosted acceptance readbacks](../evidence/13/auto-run-20261124.md#follow-up-verification)
- [Live AD-21 readback, hosted CI triage and refreshed candidate](../evidence/13/hosted-ci-triage-20261124.md)
- [Exact Works candidate and shared scanner prerequisite](../evidence/13/platform-scanner-prerequisite.md)
- `run-with-temp uv run --locked --script tools/render.py --check` from CiCd.
- `run-with-temp python3 references/Hexalith.Builds/check.py` from a standalone exact Works checkout with the declared direct submodules.
- `python3 tools/nightly_acceptance.py --run <run-id> --module Hexalith.Works` against an actual scheduled or eligible dispatched Nightly run.

