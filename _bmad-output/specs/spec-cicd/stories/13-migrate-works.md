---
title: 'Migrate Works'
type: 'feature'
created: '2026-11-24'
status: blocked
baseline_revision: 0a02af88c7ba4824d7cbc40198c6cded77abaca3
baseline_commit: 0a02af88c7ba4824d7cbc40198c6cded77abaca3
implementation_repository: 'references/Hexalith.Works'
implementation_baseline_revision: '96d231d54bc0a8b33004e828ebdeb1becb3bd15e'
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
- **Scanner proof inputs.** Prove the Platform boundary from the exact committed Platform gitlink by the reviewed bytes of the Platform export implementation that the proof assumes rather than traces, not by a fixed list of Platform commits. Prove the owned Works CI workflow by its reviewed bytes with only the immutable `vX.Y.Z` release tags of its `Hexalith/Hexalith.Builds` references masked. Builds releases are immutable and delivered through CiCd, and their behavior is qualified there. Keep the exact fingerprints of the Works action and materializers. Any other change to a proof input, a missing or non-commit gitlink, an unsafe path or an unresolved descendant still fails discovery with an exact diagnostic.
- **Works candidate publication.** Prepare any new discovery candidate from freshly fetched Works `main`, which already includes the earlier discovery candidate recorded in the checkpoint. Before pushing a discovery candidate through the normal Works PR path, require a report from the normal hosted CiCd scan workflow at the fixed scanner revision and production policy. The report must show a passing Works row with complete discovery for the exact Works `main` base, zero run-level errors and no duplicate involving Works, subject to the scoped prerequisite below. Require complete discovery on the exact local candidate with the same scanner revision and production policy, a passing standalone Builds checker on that candidate, and passing hosted shared CI and Platform parity on the exact Works `main` base and its delivered Builds pin, including after delivery of any Builds correction. Refresh and requalify the candidate after any base change. If a publication prerequisite remains open, preserve the local candidate and record the outstanding prerequisite, its owner and exact evidence.
- **Scoped Works discovery prerequisite.** If the checkpoint establishes that a behavior-preserving Works source change is necessary to clear base discovery failures, allow one dedicated Works PR for that change through the normal Works PR path. For this PR alone, the exact-base hosted report may have a failing Works row due solely to the discovery diagnostics the candidate resolves. Require the exact-base report, zero run-level errors, no duplicate involving Works, both passing exact-base hosted CI jobs, and complete discovery and a passing standalone Builds checker on the exact candidate. After merge, qualify the resulting Works `main` through the normal hosted scan before publishing a further discovery candidate or counting an acceptance Nightly. AD-21 cleanup remains a prerequisite to acceptance Nightly.
- **Handoff after scanner work.** After completing the available scanner work, stop at any unresolved Builds, Platform or maintainer handoff that blocks the next gated step. Hosted requalification of the scanner follows its publication on CiCd `main` through the normal scan workflow. Record the owner and exact missing evidence for Works publication or acceptance Nightly, as applicable.

</intent-contract>

## Code Map

- [Approved Works migration](../../../implementation-artifacts/spec-13-migrate-works.md) preserves the historical approval and acceptance conditions. [AD-21](../../../planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-21--onboarding-sequence) governs ordering. [Gate classification](../gate-classification.md#works-classification-story-13) maps removed workflow/evidence gates and retained product checks.
- `references/Hexalith.Works/.github/actions/{after-unit-tests,platform-parity}/action.yml` runs the reviewed source/package bindings and Platform R1–R11. The product preparation commit removed the tool-only npm files and retired tests. `.husky/` and `NuGetAuditSuppress` were absent at preparation. The historical `NU19xx` warning-severity setting was explicitly excluded from waiver transfer.
- `setup/Hexalith.Works.yml`, `rendered/Hexalith.Works/`, `rendered/Hexalith.Works.perimeter.json` and the Works gitlink comprise registration. Works `.github/hexalith-ci.json` and the live workflow blobs identify the delivered configuration. `builds-version` selects immutable `v6.8.1` at `bf8a28b4bbcec619e8d9764d335f786f2bafb69e`.
- `eng/published-builds.json` in Works binds the reviewed producer handoff. Tagged Builds `Github/lib/published_builds.py` reads that publication in shared Stage 2. `tools/nightly_acceptance.py` judges Works' release, duplicate scan and delivery results against authenticated run artifacts.
- `tools/scan_discovery.py:113-145` and `Discovery.discover_works_platform` hold the Works boundary proof. `WORKS_PLATFORM_PINS` accepts only Platform `99a17baa…` and `616e2778…`. `WORKS_PLATFORM_INPUTS` fixes `.github/workflows/ci.yml` at SHA-256 `489af315…`, which is its Builds `v6.8.1` rendering. `tools/tests/test_scan.py:1731` `test_works_platform_boundary_follows_only_the_reviewed_inputs` patches both constants. Scheduled hosted scan [45615203576](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45615203576), at controller `0a02af88c7ba4824d7cbc40198c6cded77abaca3`, failed Works `dfa1c7d2f200ac425ebd044719c40c775adbe14f` (Platform `4de0bfff31b849986f6f1ea200a3585eb76c9938`) with six files and 16 diagnostics, led by `unproved Platform gitlink`. It had zero run-level errors. Current Works `main` `96d231d54bc0a8b33004e828ebdeb1becb3bd15e` pins Platform `3bcac63c6fe20b46687b6e0bb7a333ea8c66fb4d`. It carries the delivered `v6.8.3` `ci.yml` at SHA-256 `dacc0de5…`, which differs from `v6.8.1` only in its two Builds tags. Its action and materializer blobs are unchanged. Platform `eng/works_host_snapshot.py` is blob `52dfe0ea4b6357a3ed04a330211ff4f162885925` at `616e2778`, `4de0bfff` and `3bcac63c`, and it imports only the standard library. Platform `main` `3bcac63c` names tuple `v6.8.3` with Builds gitlink `62876129eaa035e78bd0324419231f07d43a07b8`, which is the `v6.8.3` tag commit.
- `../evidence/13/` holds the original readbacks, including `provision-registry.json`, `nuget-policy-verification.json`, `nuget-cleanup-verify-cleanup.json`, `legacy-org-secret-cleanup.json` and `authenticated-adoption.json`. Use those as historical evidence. Store only compact current results and digests. Executable historical evidence stays archived.
- Works live `main` was `ae9dbe8eccd58ff1e9c0276cc17ed0a2e70d03bf` at planning. [CI run 45397690202](https://github.com/Hexalith/Hexalith.Works/actions/runs/45397690202) hit an HTTP 403 rate limit in the shared producer lookup. [Nightly run 45394054346](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45394054346) also records Works' duplicate scan failure at the Platform parity action's shell command substitution. Distinguish pipeline or permission failures from product failures and report shared defects under the repository guidance.

## Tasks & Acceptance

**Execution**

- [x] `tools/scan_discovery.py` and `tools/tests/test_scan.py` Replace the Platform commit allowlist with reviewed-byte proof of the Platform export implementation read from the exact committed gitlink. Mask only immutable Builds release tags in the Works workflow fingerprint. Keep a missing or non-commit gitlink failing as `unproved Platform gitlink` and report a changed reviewed Platform source with its path. Extend the boundary test with positive and negative cases. Pass the focused test, the locked scanner suite and the renderer check. Locally scan current Works `main` with the normal controller and production policy, and record its Platform pin, selected files, diagnostics and digests in `../evidence/13/`.
- [x] `../evidence/13/` Read back whether hosted shared CI and independent Platform parity on the current Works `main` show the Platform tag-to-gitlink pairing as resolved. Record the run, job and attempt identities, or the exact remaining failure and its owner.
- [ ] `../evidence/13/` Track and reconcile the maintainer prerequisites against authenticated precondition and cutover readbacks. Record qualified Zot replacements and continuity for the remaining consumers, old key retirement and loss of legacy Works write access, Works' exclusion from the legacy `NUGET_API_KEY` grant, and the retained scoped publishing and immutable release settings.
- [x] `references/Hexalith.Works`, `setup/Hexalith.Works.yml`, and `rendered/Hexalith.Works*` Verify historical preparation and delivery, exact current configuration, and the disposition of product gates and audit waivers. Reuse the existing adoption.
- [ ] `tools/scan_discovery.py`, `references/Hexalith.Works/.github/actions/platform-parity/` and its reachable Works-owned scripts. Complete the scanner checkpoint and resolve Works-owned discovery errors while preserving Platform parity behavior. Record exact-base and exact-candidate qualification evidence or the outstanding path diagnostics and owners. Run the standalone Builds checker on the exact candidate before any module push.
- [ ] `../evidence/13/` Route the recurring Stage 4 Dapr scheduler bind failure to Builds and record its triage and any immutable Builds correction and delivery. Record any separate Works product fix. Before publishing through the normal Works PR path, record passing hosted shared CI and Platform parity on the exact Works `main` base and Builds pin, the hosted CiCd scan of that base, and the exact local candidate discovery and standalone-checker results. Record run and attempt identities, the scan artifact identity and digest, the Works commits, the scanner revision and policy digest. If the scoped prerequisite applies, record why a Works source change is necessary, which base diagnostics it clears, and the clean hosted Works row on the resulting `main` after merge.
- [ ] `references/Hexalith.Works/references/Hexalith.Builds/check.py` and `tools/nightly_acceptance.py` Verify the current adopted source and obtain passing exact-source hosted CI and an eligible central Nightly result. Record any shared pipeline failure or access refusal with exact evidence.

**Acceptance criteria**

- Given the initial adoption receipts and current maintainer readbacks, when AD-21 is reconciled, then Works retains its scoped publish identity and policy, immutable releases are enabled, Works receives no legacy GitHub grants, including `NUGET_API_KEY`, and the retired Zot key cannot publish Works repositories. The other Zot consumers retain their required access.
- Given the product candidate and first delivery, when their exact trees and live successors are compared, then Works retains the two registered product actions and authorized tests, lacks the obsolete tooling and gates, and matches the rendered CI/CD perimeter at the delivered Builds pin.
- Given a Works revision whose committed Platform gitlink is any commit, when that commit's tree holds the reviewed Platform export implementation bytes and the Works workflow differs from its reviewed bytes only in immutable Builds release tags, then the normal controller proves the computed checkout and export, records the gitlink in `pinnedSources`, and traces the four entry targets by ordinary discovery. When the export implementation, the workflow outside those tags, the action or a materializer differs, or the gitlink is missing or not a commit, then Works discovery fails with the exact `unproved` diagnostic.
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
- 2026-11-25 — Human decision (option A). Re-arm story 13 for a scanner increment. Scheduled scan `45615203576` showed that the Platform commit allowlist and the exact `ci.yml` fingerprint fail Works after every Platform update and every Builds release. Prove the Platform boundary by the reviewed export implementation bytes at the exact committed gitlink, and mask only immutable Builds tags in the workflow fingerprint. Read back the Platform pairing on current Works `main`. Then stop at the remaining Platform, Works source-identity and maintainer handoffs.

## Review Triage Log

### 2026-11-25 — Review pass (scanner proof inputs)

- Verdicts cover 21 findings — high 0, medium 3, low 7, false 5, maybe-false 1, rejected as edits to this spec 5.
- The six patch findings were applied. The two focused tests, the 137-test locked scanner suite and the renderer check passed afterwards. Nothing was deferred.
- Findings
  - `[medium]` `[patch]` No test binds the production workflow fingerprint to the rendered Works `ci.yml` (verification gap). A renderer or Builds-contract change outside the two tags would fail every hosted Works scan with no CiCd check flagging it first.
  - `[medium]` `[patch]` Nothing ties the hand-copied workflow digest to the renderer. Same root cause as the row above.
  - `[medium]` `[patch]` A committed bytecode cache beside the export implementation runs instead of the reviewed source. Demonstrated: `spec_from_file_location` executed an unchecked-hash `eng/__pycache__/works_host_snapshot.*.pyc` built from substituted source, and the proof reads only the `.py` blob. Fixed commit pins excluded this before the change.
  - `[low]` `[patch]` The `BUILDS_RELEASE` owner lookbehind is untested. Removing it would mask lookalike-owner references without failing the boundary test.
  - `[low]` `[patch]` The export path appears in both `WORKS_PLATFORM_ENTRIES` and `WORKS_PLATFORM_EXPORT`, and nothing checks that the bound file is the module the coordinator loads.
  - `[low]` `[patch]` The evidence gives test digests without the documented command, and gives the Python version two ways.
  - `[low]` `[reject]` The masked tags are not tied to each other or to the delivered Builds tag (verification gap). The digest still binds every byte outside the tags, and delivery restores the owned workflow. The tag does not change which Works or Platform source the parity action runs, and the guard would add branches for a case not met in normal use.
  - `[low]` `[reject]` Same claim from the blind review: mixed or downgraded tags pass. Rejected for the same reason.
  - `[low]` `[reject]` Same claim from the edge-case review, tied to the Builds gitlink. Rejected for the same reason.
  - `[low]` `[reject]` An unfetchable gitlink commit fails with a generic fetch error instead of `unproved Platform gitlink`. Discovery still fails loudly at the action, the acceptance criterion covers only a missing or non-commit gitlink, and mapping the error adds branches.
  - `[low]` `[reject]` Platform `99a17baa` is no longer proved. No scan targets it: hosted scans fetch live Works `main`, which pins `3bcac63c`. The suggested fix edits this spec.
  - `[false]` `[reject]` Removing the allowlist drops a check that the pin descends from Platform `main`. The allowlist never checked ancestry. The scanner traces the exact bytes at the committed SHA, and `tools/scan.py:287` still requires the committed `.gitmodules` declaration.
  - `[false]` `[reject]` `.gitattributes` transforms could change the executed export bytes (blind review). At `3bcac63c` no `ident`, filter or encoding attribute applies to `eng/works_host_snapshot.py`, and the file has no `$Id$`. An LFS pointer would fail the blob digest.
  - `[false]` `[reject]` The same claim from the edge-case review, extended to `.gitmodules` and LFS smudge. Refuted by the same readback, and the `.gitmodules` declaration check remains.
  - `[false]` `[reject]` `pinnedSources` on a failed export row could be read as proof. Its only writer is `tools/scan.py:352`, nothing consumes it as proof, and rows failing on an unresolved descendant already carried it before this change.
  - `[false]` `[reject]` The Builds lookahead cases do not test the trailing lookahead. Any leftover suffix changes the digest, so the lookahead cannot weaken the proof and no fix is needed.
  - `[maybe-false]` `[reject]` Calling `MintToken` a Works test defect is unconfirmed. Settling it would need a read of `WorksAppHostSmokeHarness.cs:1018` at `96d231d5`. If true, it is only low: handoff wording that already routes the exception to the Works owners.
  - `[reject]` The Code Map bullet describes the pre-change constants (verification gap). The fix edits this spec, and the bullet records the state at re-arm.
  - `[reject]` The Context section is stale, including the `v6.8.1` `builds-version` bullet (blind review). The fix edits this spec.
  - `[reject]` The Code Map cites the removed constant and the superseded digest (edge-case review). The fix edits this spec.
  - `[reject]` The frontmatter status and Auto Run Result disagree, and the run summary says the hosted run passed when only the shared job did. The fix edits this spec, the status is transient review state, and the evidence names job `139251312243`.

## Verification

- [Current AD-21 and exact-tree reconciliation](../evidence/13/reconciliation-20261124.md)
- [Follow-up AD-21 and hosted acceptance readbacks](../evidence/13/auto-run-20261124.md#follow-up-verification)
- [Live AD-21 readback, hosted CI triage and refreshed candidate](../evidence/13/hosted-ci-triage-20261124.md)
- [Exact Works candidate and shared scanner prerequisite](../evidence/13/platform-scanner-prerequisite.md)
- [Pinned source discovery and current hosted CI evidence](../evidence/13/scanner-increment-20261125.md)
- [Computed Platform discovery checkpoint and owner handoffs](../evidence/13/computed-platform-checkpoint-20261125.md)
- [Latest AD-21, adopted perimeter and hosted verification](../evidence/13/ad21-and-hosted-readback-20261125.md)
- [Latest exact base and candidate discovery with owner diagnostics](../evidence/13/platform-boundary-qualification-20261125.md)
- [Export-byte Platform proof, current pairing and AD-21 readback](../evidence/13/export-byte-proof-20261125.md)
- `run-with-temp uv run --locked --script tools/render.py --check` from CiCd.
- `run-with-temp python3 references/Hexalith.Builds/check.py` from a standalone exact Works checkout with the declared direct submodules.
- `python3 tools/nightly_acceptance.py --run <run-id> --module Hexalith.Works` against an actual scheduled or eligible dispatched Nightly run.

## Auto Run Result

**Status** `blocked`

**Blocking condition** The scanner increment is complete locally. Platform
parity, scanner publication and AD-21 cleanup belong to other owners.

The scanner now proves the Works Platform boundary at any committed gitlink
whose tree holds the reviewed `eng/works_host_snapshot.py` bytes. The Works
workflow fingerprint masks only immutable Builds `vX.Y.Z` tags. A missing or
non-commit gitlink, or any other proof-input change, still fails with the
exact `unproved` diagnostic, and so does a bytecode cache beside the export
implementation. A new test binds the production workflow digest to the
rendered Works `ci.yml`. After the review patches, both focused tests, all
137 tests in the locked scanner suite and the renderer check passed.

On Works `main` `96d231d54bc0a8b33004e828ebdeb1becb3bd15e`, the normal
production controller now records Platform
`3bcac63c6fe20b46687b6e0bb7a333ea8c66fb4d` in `pinnedSources`. It selects
43 files, with zero run-level errors and no Works duplicates. The unmodified
controller stopped at 6 files. Works discovery still fails on 128 Platform
diagnostics and the two Works source-identity diagnostics. Their compact
diagnostic array is unchanged from Platform `616e2778`.
Hosted requalification needs the scanner published on CiCd `main`.

Shared CI job `139251312243` passed in run `45627444691`, attempt 1. Its Platform parity
job resolved the Builds tag-to-gitlink pairing and reached the canonical gate.
The gate failed the `platform-recovery` lane with an
`ObjectDisposedException` for `RSAOpenSsl` in Works
`WorksAppHostSmokeHarness.MintToken` at line 1018. Works commit
`1ce938a4` introduced that code. This is a Works test defect for a separate
Works PR.

The AD-21 readback found Works excluded from all eight legacy grants,
including `NUGET_API_KEY`. It also confirmed immutable releases and the
scoped release environment. The legacy Zot owner and pair are unchanged, so
the maintainer cleanup remains open. Nightly `45603058797` fails Works
acceptance.
[Increment evidence and owner handoffs](../evidence/13/export-byte-proof-20261125.md)
