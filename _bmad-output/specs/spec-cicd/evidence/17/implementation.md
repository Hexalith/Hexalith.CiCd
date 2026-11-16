# Story 17 local implementation handoff

> Publication update: after this local handoff, the human requested `push all changes`.
> The Folders candidate is now on its story branch; see [publication details](publication.md).
> Verification remains blocked and production adoption is still pending.

Status: **in progress; local candidate prepared; adoption blocked**. This handoff
performed no remote Git operation, external provisioning, publication, delivery,
credential retirement, or release dispatch. The original workspace and owned
module portions are preserved. Production setup/render and the CiCd gitlink are
unchanged.

The final module candidate, exact changed paths, tree and commit identities,
released policy results, and complete Client result are in
[`final-candidate.json`](final-candidate.json). The local verification commit is
portable in [`folders-product-candidate.bundle`](folders-product-candidate.bundle)
and [`folders-product-candidate.patch`](folders-product-candidate.patch). It is
not a protected-token publication or a remotely available gitlink.

## Prepared product changes

- Retired the npm tooling manifests, module audit waiver, pure CI/tooling/story
  assertion files, and redundant scheduled policy/NFR orchestration. The
  [per-method inventory](gate-classification.json) records 20 removed files,
  60 individually removed methods, retained product methods, and mixed safety
  channel changes. These counts are observations, not deletion targets.
- Retained complete contract/generated-client/browser/security suites, source
  whitespace/analyzer operations, five package archive/inventory checks,
  measured capacity smoke/calibration, provider classification/redaction, and
  the real two-version Forgejo Alpine TLS smoke. Product diagnostic negative
  controls remain present after removing CI/tooling channel assertions.
- Kept global SDK11 and published targets. The unpublished generator/shared
  projects and both NSwag runtime selections now use .NET11. Roll-forward is
  scoped to the NSwag processes; nested generator execution receives the
  calling build/package/audit settings. Both Client fixture runtime lookups
  now match those tool outputs. The Alpine image matches net11.0.
- Regenerated through the released tools. The principal generated client is
  byte-identical. Helper output changes only its canonical configuration digest
  and dependent self-hash. Native-client output changes only stale generator
  version metadata, from the prior stored 14.7.1/11.6.1 to the already pinned
  14.8.0/11.6.2. Public signatures and method bodies are unchanged; exact diffs
  and hashes are in [`runtime-regeneration.json`](runtime-regeneration.json).

## Complete-project ownership

| Hook | Complete delegated projects |
| --- | --- |
| `after-unit-tests` | Contracts, Client, core Folders, Server |
| `after-integration-tests` | AppHost, UI.E2E including accessibility |
| `nightly` | Distinct provider classification/redaction/report and actual Forgejo Alpine smoke |

The initial three-project mapping could leave shared runners green after
zero-exit results with skipped or Not Run cases. The final nonfrozen mapping
therefore delegates all six complete projects to the same strict runner,
enables explicit cases, and rejects empty, ambiguous, failed, skipped, and Not
Run summaries. AppHost remains in stage 4; other IntegrationTests retain released
automatic classification. No per-case exclusion, allow-not-runnable list, or
second overlapping accessibility/contract test run was introduced.

The runner's [nine boundary checks](complete-project-runner-qualification.json)
verify all-counter failure behavior, complete explicit selection, and native
exit-code propagation. Focused selectors in the local investigation are absent
from delivered hooks.

The proposed setup, reproducible render, hashes and activation prerequisites
are in [`registration-candidate.json`](registration-candidate.json) and
[`registration-candidate/`](registration-candidate/). Both candidate render/check
and the unchanged production render check passed. Registration remains a review
artifact because prerequisite proof and protected publication have not passed.

## Verification and actual blockers

[`attempt-3/product-verification.json`](attempt-3/product-verification.json)
records the full audited package-mode Release restore/build, fresh helper and
native generation under a private host containing only .NET11 runtimes,
whitespace/analyzer checks, all **493 Contracts cases** with zero unsuccessful
counters, capacity smoke/calibration, nightly classification/redaction, and
actual Alpine TLS smoke against Forgejo **16.0.3 and 15.0.7**. Those operations
passed. The final complete Client suite passes all **392 cases** with zero unsuccessful
counters, recorded in `final-candidate.json` and `final-client-complete.log`.

Unchanged suite evidence retains its original source identity and strict
counters. This includes **854 IntegrationTests** and the complete **63-case UI
E2E/accessibility suite** with no failed/skipped/Not Run cases. Earlier failed
attempts are preserved under [`attempt-1/`](attempt-1/) and
[`attempt-2/`](attempt-2/). Their harness/runtime failures are explicitly
identified; contaminated missing-generated-file results do not establish
product failures.

The preparation proof remains failed:

1. Released audit lint rejects eight unchanged historical evidence NuGet config
   blobs containing `auditSources`. Their exact diagnostics are saved in
   `final-candidate.json`. No historical bytes were rewritten or renamed, and
   no central suppression was invented. Audited compilation found no need for
   a vulnerability waiver.
2. Current CiCd discovery rejects ordinary PowerShell parameter/assignment and
   control-flow syntax. [`action-discovery-minimal.json`](action-discovery-minimal.json)
   proves the issue with a three-line script having one literal action callee
   and no child execution. Full final diagnostics are saved once in
   `action-discovery.json`. The extracted Python checks have no remaining
   discovery errors; their import/subprocess boundary was repaired by sharing
   the real package-output validator with the packer. Its CLI still rejects
   repository-root output.
3. Retained real controls remain incomplete. The default Server result was
   1,437 total with 11 Not Run; AppHost was 193 total with 10 skipped and 6 Not
   Run before removing its separate story-blocker self-assertion; core Folders
   was 2,489 total with two provider skips. These zero exits are **not passes**.
   [Focused actual executions](focused-product-prerequisites.json) ran the 11
   explicit Server controls, six explicit AppHost controls, and opted-in FR58
   proof: all fail on real missing component/frozen product prerequisites.
   Server needs the real Keycloak component manifest and source-bound Debug
   EventStore proof binaries; AppHost needs its real component/run-owned
   manifests. FR58 has an unconditional frozen prerequisite failure. Nine
   additional full-topology proofs need genuine Aspire/Dapr product setup.
   The operator provider-evidence lane remains unrun; the separate real
   Alpine smoke is not substituted for that evidence. Strict complete-project
   hooks remain red until the required proofs actually pass.
4. Predecessor acceptance, ordered AD-21 administration, protected publication,
   authenticated sole-parent adoption/tree preservation, normal post-adoption
   checker, green delivered CI, immediate credential retirement and the next
   genuine scheduled release remain outstanding. Full live validation would
   perform remote Git operations and was not run within this local-only boundary.

All recorded task-owned verification roots/processes and unique smoke
containers/networks are absent in [`cleanup-readback.json`](cleanup-readback.json). Existing
workspace services and shared caches are preserved. No story acceptance or
CAP-16 completion is claimed.
