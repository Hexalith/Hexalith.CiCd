# Projects publication repair — 16 November 2026

The two original failures have local repairs. Publication remains incomplete:
current-main package compilation requires an unpublished EventStore API, and the
retained older runtime graph still has a command-seeding timeout. No push or
release was performed by this repair. Do not treat focused or historical results
as full acceptance of current main.

## Repairs and review

- Each selected owner executable gets one dependency-resolving assembly context.
  Full identity, frozen SHA-256 and loaded module identity checks remain active.
  SDK/JSON contracts share canonical default-context identity only when bytes
  match. Ordinary transitive dependencies stay with their owner.
- Twelve inactive historical XML files are deterministic gzip archives. Their
  manifest preserves original paths, modes, Git blobs, byte counts and hashes.
  Existing historical receipts and all live audit rules stay intact.
- Runtime diagnostics report closed transport statuses and owning method stages
  without raw details. Malformed escaped-surrogate input cannot replace the
  original failure. Removed a duplicate friend-assembly declaration.
- Independent review's ten original findings and the malformed-string follow-up
  were triaged in the repair spec. The unproven native-library loading concern is
  recorded in the deferred ledger; no current factory demonstrated it.

## Evidence boundaries

`focused-final.log` records three Release builds with analyzers and warnings as
errors, then **57 passed, zero failures/skips/unrun cases** covering assembly
identity and transitive binding, real Projects/Tenants/Folders factories,
credentials and diagnostics. These builds deliberately reuse retained product
binaries because current-main product compilation is blocked. Commands and
source hashes are in `verify-focused.py`, `focused-results.json` and
`focused-inputs.json`. This is focused verification, never publication proof.

`archives.json` binds the immutable candidate tree to released Builds validator
`fdda17c0a4538b0f7c99f813c20ca24b49006530`. All twelve originals roundtrip with exact
bytes/modes and match their original Git blobs. Full-tree audit passes; active
NuGet audit-source and arbitrary-extension MSBuild suppression controls are
rejected. The final invocation uses `PYTHONOPTIMIZE=1`; verification checks remain
effective. See `archives-final.log` and `verify-archives.py`.

`product-full.log`, `product-commands.json` and `product-source-snapshot.json`
record the attempted complete proof from fresh Projects main
`7da7e95b670838de3181e946709e1246695a0e72` plus preserved preparation and repairs.
Restore passes. Build stops with fourteen CS0234 errors for
`QueryResultContractAttribute` / `QueryResultContract`. Later checks therefore
cannot qualify this candidate. `sdk-prerequisite.json` and `sdk-api-*.log` confirm
that pinned EventStore 5.1.1 and latest published stable 5.2.0 both lack the API;
it exists in source commit `0be0c922883d4ea61b18e843e24472162261d934`.

`focused.log` and `focused-with-runtime-results.json` preserve the additional
unchanged complete runtime diagnostic. It fails in `SendHumanAsync` →
`CommandAsync` → `SeedAsync` with the original 45-second HTTP timeout. This mixes
retained older product binaries with current fixture inputs. It does not prove
the latest product graph works, and no timeout, assertion or phase was relaxed.
Earlier failed attempts and their distinct source snapshots remain in this
directory rather than being presented as current acceptance.

## Preserved candidates

Projects candidate worktree:
`/home/administrator/projects/hexalith/cicd-projects-publication-fix-20261116T204551Z`
on `fix/projects-publication-checks-20261116T204551Z`, created from freshly fetched
main. Original pending product changes were reapplied without owned changes or
conflicts. `repair-inputs.json` confirms the seven repaired source files also
match the original module checkout. No local commit or push was made by this
repair. `integration.json` retains the preparation identities.

Folders prerequisite worktree:
`/home/administrator/projects/hexalith/cicd-folders-publication-fix-20261116T210543Z`.
Its preparation was preserved on fresh main. Its eleven explicit source/runtime
checks still need genuine matching Platform verifier inputs; previous partial
component results are not complete publication qualification.

Continue with the existing module-scoped pre-adoption procedure only after exact
current inputs pass. Publish prerequisites before consumers and verify their
remote commits before recording parent gitlinks. Use the normal nightly release
process for SDK publication. A new scope decision is pending in the repair spec;
no package release or invented future version is assumed.
