---
title: 'Fix package fixture owner assembly selection'
type: 'bugfix'
created: '2026-11-16'
status: 'draft'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — user requested fixing blocked publication">

## Intent

Correct the real Projects package/browser qualification failure where owner
assembly loading unifies a selected executable with a different already-loaded
assembly. Preserve the exact-byte identity guard, shared SDK type identity,
package-mode Release builds, source-only production safeguards, complete retained
product tests and all audit rules. Add bounded diagnostics and behavior tests
for identity collisions and mismatches. Use the already approved Projects
pre-adoption substitute; absence of a post-adoption checker is not a blocker.
This fix does not authorize changing historical evidence, frozen product holds,
owned module portions or credential scope. Earlier publication authorization
continues once exact-input qualification succeeds.

</frozen-after-approval>

## Implementation Notes

- Investigated on CiCd `ec481fd50b280e2d41f9baecbd03945c833e4538` with concurrent
  edits preserved. Current upstream already contains PowerShell parser correction
  `65751cd`; do not recreate it or claim that stale 940-diagnostic result is current.
- Projects `tests/Hexalith.Projects.PackageFixtures.AppHost/PackageActualOwnerInfrastructure.cs`
  uses `Assembly.LoadFrom` and compares returned assembly bytes with the selected
  owner's Release artifact. The saved nightly browser result fails that guard.
  Determine the mismatching identity before choosing the correction; do not
  remove the guard or accept merely equal names/versions.
- The fixture AppHost composes real prebuilt resources through EventStore's
  development catalog. Keep SDK interfaces shared; an isolated assembly context
  that duplicates contract types is not sufficient.
- Preserve current pending Projects and Folders fixture/catalog work. Create an
  isolated Projects worktree from freshly fetched module main and overlay the
  exact current tracked/untracked candidate before editing. Use the intended
  module-agent profile for module operations and no credential fallback.
- Reuse `tools/qualification/pre-adoption/projects/local-package-build.py` for
  standalone disposable qualification. All clones/build output go under wrapper
  `TMPDIR`; save useful logs outside. Adapt a private driver for the isolated
  source rather than editing shared drivers or overwriting existing results.
- The newer `push-all-20261116T194845Z/result.json` supersedes old empty-sequence
  and Docker port failures: 2,878 C# tests and other focused lanes passed there.
  Current source differs; run affected loader/fixture tests first, then exact
  complete qualification where prerequisites permit. Record actual refusals.
- Released audit policy separately rejects 12 unchanged historical declarations.
  That independent contradiction is not permission to weaken audit rules. No
  module or CiCd push may be claimed successful without its required proof.

- Reproduction identified `Hexalith.Tenants.Contracts.dll`: selected SHA-256
  `c6875d0851f5aa077155559310e80aca7bcdee16c21d19a1d195908eb94dc968`
  differs from Default's `84ca1ba9b50bb0d03c2e97180c583bc6097ba11337e8da2d6a8ad48df8f74782`.
  The diagnostic, complete audited Release build and nine browser-configuration
  passes are saved in `fix-publication-20261116/owner-diagnostic.log`.
- Concurrent work supplied the initial `PackageOwnerLoadContext`, its tests,
  InternalsVisibleTo and per-resource context reuse. Preserved those changes
  rather than replacing them with a second loader. The initial affected fixture
  qualification passed 43 cases, zero warnings/errors/skips.
- Review corrections retain each loaded path's initial digest, compare actual
  loaded module IDs with PE metadata, keep ordinary dependencies private to the
  selected closure, establish SDK contracts in Default before exact-byte sharing,
  reject file/ancestor links, and make contexts collectible. Added real generated
  assembly regressions for replacement, transitive dependency identity and links.
  The BCL-only exact-source probe passes all four failure/closure scenarios.
- Historical configuration is now preserved as deterministic gzip evidence,
  not an active NuGet input: eight Folders entries and twelve Projects entries
  decompress to the exact original Git blobs. Manifests retain original paths,
  modes, sizes and hashes; original receipts and audit rules are unchanged.
  Released audit lint passes both saved candidate trees. Results are in
  `fix-publication-20261116/{folders,projects}-archive-audit.json`.
- Full Projects qualification ran on the corrected candidate. Folders'
  frozen FR58 hold still prevents claiming its complete hook gate. The human
  has been asked whether to exclude Folders publication or lift that hold;
  no answer or scope change is assumed.
- Final source-identical probes pass all five scenarios. The complete audited
  Release build and eight C# projects produce 2,899 passes and one existing
  Dapr persistence case deferred to the live lane. Real owner metadata checks
  pass. The full native lane advances past loading and then cancels in scenario
  `main` with gateway catalog/backend exceptions; the later compatibility case
  is not reached. Owning support/PostgreSQL and tool/browser configuration
  checks pass. All spawned jobs and owned cleanup have finished. See
  [the current result](fix-publication-20261116/README.md). No publication pass
  is claimed while this runtime failure and the scope decision remain open.

## Review Triage Log

- High, patched: disk replacement could hide a cached image. Frozen path digests
  and loaded-module MVID checks reject replacement; the generated v1/v2 probe passes.
- High, patched: an identical intermediate dependency could import Default's
  different leaf. Only explicit SDK/JSON contracts are shared; the selected-leaf
  regression now executes version 2 while Default executes version 1.
- Medium, patched: SDK identity depended on first-load order. Default now resolves
  a contract before exact identity, byte and loaded-module checks accept sharing.
- Medium, patched: lexical containment followed links outside the output. Regular
  file and ancestor checks reject file and directory symlink probes.
- Low, patched: permanently noncollectible contexts retained metadata after
  fixture lifetime. Contexts are collectible when their owning metadata is released.
- Medium, patched: tests omitted a real dependency graph. Generated assembly
  graphs now exercise method execution and closure selection; full real-owner
  fixture qualification remains a separate required result, not inferred from units.
- Medium, patched on recheck: real-owner tests assumed nested module checkouts.
  They now consume MSBuild-normalized selected roots from assembly metadata,
  preserving the supported sibling layout without initializing nested submodules.
- Medium, patched during qualification: the catalog deliberately sanitizes its
  public failure, so an inner SDK diagnostic was not observable through it.
  The test now verifies the precise SDK refusal directly and separately requires
  the catalog's typed public refusal, preserving both identity and redaction.


## Replanning Notes

The loader correction is verified, but complete publication now depends on work
outside the frozen correction: newer Projects annotations require an EventStore
API missing from the pinned published package, the actual native lane still
fails, and Folders' held FR58 prerequisites remain outside migration authority.
Stop further dependent publication and return to scope planning; do not remove
annotations, substitute source-mode Release output, relax deadlines or change
held product gates.

The later main diagnostic passed seven real native cases before the original
folder-service recovery failure. Added actual process lifecycle/identity proof
and bounded recovery observations. Independent recheck found one concrete race:
`StartTime` can throw after a process exits between the prior `HasExited` check
and its read. The associated-process exit exception is now treated as exit;
permission failures still propagate. The final frozen diagnostic's snapshot
predates this last one-line correction and does not qualify it.

A coherent frozen-input follow-up builds in Release/package mode with zero
warnings/errors and passes nine browser configuration cases. It exits 1 during
native main on the unchanged 45-second HTTP timeout, with gateway catalog/Dapr
failures and Folders transport cancellation; no native case or recovery is
proven in that run. Scratch, process cwd and container mount cleanup is verified.
Current complete source separately fails CS0234 on the newer missing SDK API.
Full source hashes, diagnostic limits and failed outcomes remain in the result
packet. Concurrent commits and pending edits are preserved; this session made
no commit or push. No migration acceptance is claimed.

## Code Map

- Projects `PackageFixtures.AppHost/PackageOwnerLoadContext.cs` and
  `PackageActualOwnerInfrastructure.cs`: exact-byte/MVID owner loading and SDK sharing.
- Projects Integration `PackageOwnerLoadContextTests.cs`, `PackageOwnerMetadataTests.cs`:
  generated closure controls and real selected-owner metadata verification.
- Projects Integration `PackageReadFixture.cs`: actual process transition proof,
  unchanged authorized-recovery condition and bounded observations.
- Projects PackageFixtures workers/startup: bounded SDK catalog refusal diagnostics.
- [Result packet](fix-publication-20261116/README.md): exact historical/current
  verification boundaries, missing package API, failure and cleanup receipts.

## Open Questions

- Keep Folders' existing hold and exclude its dependent publication, or explicitly
  expand scope to implement and qualify the held prerequisites? Earlier async
  question remains unanswered; no scope change is assumed.
- Prepare upstream EventStore release readiness in a separately approved scope,
  or await the normal published SDK prerequisite before requalifying Projects?

## Additional Review Triage

- Medium, patched: successful owned process exit could race `StartTime` and
  throw `InvalidOperationException`; handle that specific associated-process exit
  while continuing to surface permission failures. No further privacy issue was
  found in the bounded recovery diagnostics.
