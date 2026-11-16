# Publication fixes, 2026-11-16

The wrong post-adoption checker gate has been corrected. Folders, Parties and
Projects already have approved, module-specific preparation substitutes; their
missing nested checker is not a substantive pre-adoption refusal.

Local fixes now preserve inactive historical configuration as deterministic gzip
evidence: eight Folders files and twelve Projects files decompress to their exact
original Git blobs. Manifests retain paths, modes, lengths and hashes. Original
receipts and audit rules are unchanged. The released audit validator passes both
saved candidate trees, and owned module content is unchanged.

The actual loader collision was `Hexalith.Tenants.Contracts.dll`: the selected
executable's bytes differed from the package already loaded in Default. Owner
assemblies now use one isolated context per owner. Only explicit SDK/JSON
contracts share Default's exact bytes and actual loaded module identity; ordinary
dependencies keep their selected closure. Cached-path replacement and file or
directory links are rejected. Contexts are collectible.

Review corrections include generated assembly regressions, real selected-owner
metadata checks, MSBuild-selected nested/sibling roots, and separate checks of
the loader's SDK refusal and the catalog API's sanitized public failure.

| Qualification | Result |
| --- | --- |
| CiCd renderer tests | 43 passed |
| CiCd validator tests | 52 passed |
| Production render check | Passed |
| Exact-source loader probes | 5 passed |
| Complete Projects Release/package build | Passed, zero warnings/errors |
| Eight complete Projects test projects | 2,899 passed; one existing Dapr case deferred |
| Owning support and PostgreSQL checks | 33 + 1 passed |
| Package/tool/browser configuration checks | Passed; 20 tool and 9 browser configuration cases |
| Complete package/native/browser lane | Failed in actual-owner native scenario `main` |

The complete run above advances past the assembly collision, then cancels while
the gateway reports `RouteCatalogUnavailableException`, `DaprException` and
`RpcException`. A later diagnostic completed seven actual-owner main cases and
then failed the unchanged 90-second folder-service authorized-recovery check.
The fixture now verifies actual old-process exit, a distinct healthy replacement
with the selected binary identity, and refreshed endpoints for both owners.
Review also found and corrected an exit race while reading `Process.StartTime`.
Recovery diagnostics retain only bounded status/count/boolean/enum observations.

Newer concurrent Projects work uses `QueryResultContractAttribute`, absent from
its pinned EventStore Contracts 5.1.1. Current-source package compilation fails
CS0234; those annotations remain untouched. The separate SDK prerequisite record
also checks published 5.2.0 and records the missing API. Releasing dependencies
remains governed by the central nightly process.

To inspect recovery without changing that newer work, a separate diagnostic
froze the original source trees and overlaid the listed fixture corrections.
Its Release/package build passed with zero warnings/errors, as did all nine
browser configuration cases. Native `main` then failed on the unchanged
45-second HTTP timeout; gateway catalog/Dapr exceptions and Folders transport
failures were observed before any native case completed. This does not establish
a root cause or prove recovery. The final one-line process-exit race correction
was added after that snapshot and is explicitly outside its verification.

The deferred Server persistence case belongs to a later compatibility phase,
which was not reached. No frozen diagnostic, earlier pass, or selected subset
qualifies the complete newer current tree or replaces retained hook coverage.

[The result record](result.json) binds source revisions/digests, current fix
hashes, counts and actual failed outcomes. Raw command output remains beside it.
The wrapper workspace, its child processes and mounted containers are gone; all
three owned G-6 containers were removed. No commit or remote push was made by this fix session. Concurrent sessions
committed preparation while this work ran; their content and pending edits are
preserved. Both follow-up wrapper workspaces are removed, with no process cwd
or running container mount beneath them; see [cleanup](followup-cleanup.json).

Folders' independent frozen FR58 prerequisites remain held. The required scope
question is pending: exclude held Folders and publish only independently
qualified work, or lift that hold and implement the prerequisite stories. No
answer is assumed and no test, audit or source-only guard was bypassed.


The publication barrier remains in [the approved procedure](../../../docs/pre-adoption-publication.md):
failed module checks stop the superproject commit. Earlier CiCd merge checks are
saved evidence for their exact candidate, not a qualification of subsequent
concurrent commits. No branch, credential, audit, timeout or product assertion
was weakened to publish these inputs.
