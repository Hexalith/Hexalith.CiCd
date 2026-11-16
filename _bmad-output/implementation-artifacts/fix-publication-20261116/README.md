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

The final live lane advances past the assembly collision, then cancels while the
gateway reports `RouteCatalogUnavailableException`, `DaprException` and
`RpcException`. The bounded diagnostics do not establish its root cause. The
deferred Server persistence case belongs to a later compatibility phase, which
was not reached. This is not complete hook coverage or a publication pass.

[The result record](result.json) binds source revisions/digests, current fix
hashes, counts and actual failed outcomes. Raw command output remains beside it.
The wrapper workspace, its child processes and mounted containers are gone; all
three owned G-6 containers were removed. No new commit or remote push was made
in this fix attempt.

Folders' independent frozen FR58 prerequisites remain held. The required scope
question is pending: exclude held Folders and publish only independently
qualified work, or lift that hold and implement the prerequisite stories. No
answer is assumed and no test, audit or source-only guard was bypassed.
