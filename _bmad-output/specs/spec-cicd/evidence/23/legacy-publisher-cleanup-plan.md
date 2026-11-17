# Tenants legacy publisher cleanup checkpoint

This is a prepared plan, not an executed cleanup or an adoption approval.
Tenants remains unadopted. Preserve its old publishing path until actual App
adoption has been authenticated, then perform the verified cleanup immediately.

## Established targets

| Target | Evidence and required action after adoption |
| --- | --- |
| Tenants repository | ID `1174267565`, `Hexalith/Hexalith.Tenants`; enable immutable releases and verify the authenticated setting. |
| Legacy Trusted Publishing policy | Remove only policy `18796`, after rechecking owner/repository, `release.yml` and environment `production`. Preserve new Active policy `27252`, environment `hexalith-release`, glob `Hexalith.Tenants*`, and every other repository's policy. |
| Legacy org secret membership | Fresh complete `legacy-publisher-org-selection.json` shows both `HEXALITH_ZOT_USERNAME` and `HEXALITH_ZOT_API_KEY` select EventStore, Memories, Parties and Tenants. Remove only Tenants' ID from each selection. Re-inventory every other legacy family and remove any exact Tenants membership while preserving all other selections and secret values. |
| Repository and old environment secrets | Complete `legacy-credential-input-inventory.json` shows no Actions, Dependabot or `production` secrets. Recheck immediately before cleanup; preserve the foreign environment itself and the new `hexalith-release` pair. |
| Registry publisher to retain | `hexalith-tenants-publish`, read/create/update on `tenants`, `tenants/**`, `tenants-api`, `tenants-api/**`; real foreign upload attempts returned 403. Preserve it and the read-only shared identities. |
| Legacy NuGet API key | Recheck the account's visible key metadata and any active key's Tenants scope. Prior pilot evidence found only expired key `954800`; that historical observation is not a fresh Tenants scope readback or a mapping to an encrypted GitHub secret. |

The legacy module release source at product base
`0e0e85fd646da904c5528854e271b71a2b0b9066` passes the organization Zot pair to
Semantic Release and artifact verification in `production`. There is no
repository/environment secret overriding that pair. Tenants publishes both
`tenants` and `tenants-api`, so the package-only pilots' no-target disposition
does not apply.

## Registry revocation dependency

`legacy-registry-key-metadata.json` is an authenticated metadata-only read for
`jpiquot@itaneo.com`. It lists three active keys with no API-key scope:

| UUID | Label | Disposition |
| --- | --- | --- |
| `9eba6461-9d15-40d1-addf-2be14bc76ad8` | `JPIQ PC` | Preserve the existing local/maintainer credential. |
| `099585e7-fd9e-4aac-9042-56426c1add7b` | `Github Actions Hexalith` | Candidate legacy automation key; label and usage timestamp alone do not establish the encrypted org-secret mapping or its complete consumer set. |
| `d122a9d6-90c8-4f5f-afa5-cf8866cb6391` | `GITHUB` | Preserve until its actual consumers and role are established. |

The live ACL in `legacy-publisher-acl-assessment.json` gives global admin access
to `jpiquot` and `jpiquot@itaneo.com`. The only legacy write grant on the default
and Tenants namespaces belongs to those administrators. Zot's documented
[admin policy](https://zotregistry.dev/v2.1.11/articles/authn-authz/) overrides
repository policies. Removing an administrator from only the Tenants namespace
therefore does not revoke a global administrator-owned key's Tenants push.

Fresh live-main workflow reads in
`legacy-other-publisher-source-assessment.json` positively confirm that all three
other selected modules still reference the legacy pair. EventStore declares
`eventstore`; Parties declares `parties`, `parties-mcp`, and `parties-ui`.
Memories routes publishing through scripts and its complete namespace set is
not established by that workflow packet. The initial block-only extraction missed
EventStore's inline value and is not evidence of absence; the subsequent
assessment captures it. The `.releaserc.json` request returned 404 and remains
unverified, rather than a reason to change credentials or claim there is no
Memories publisher. These reads do not establish an API-key UUID or complete
external consumer mapping.

The subsequent complete root/tools tree reads and exact manifest blob
`67faba0fb459148fb11b32607fbfd85e48f5b61a`, at Memories source
`341ae091bc9a94bfab0c7741314419713188ae8d`, establish its five declared
repositories: `memories`, `memories-mcp`, `memories-access-telemetry`,
`memories-access-telemetry-clock`, and `memories-domain-service`.
See `legacy-memories-container-manifest.json`. Together these are nine known
non-Tenants publishing repositories, each with its own possible nested paths.
Any assessed replacement must preserve their required reads and writes, and
preserve needed cross-module pulls while refusing Tenants writes. Recheck live
sources/selections before an actual rotation; these declarations do not establish
that the API key has no additional consumers. The complete root tree also
resolves the earlier `.releaserc.json` 404 as no such root file at that exact
commit, without changing the preserved raw request classification.

The documented [API-key endpoints](https://zotregistry.dev/v2.1.11/developer-guide/api-reference/)
offer create, metadata list and delete, with no in-place scope-edit operation.
The installed registry is identified by immutable digest in
`registry-version-readback.json`; that packet does not establish a matching
version tag, so any replacement-key scope behavior requires actual qualification
on the installed instance before use.

To complete revocation while preserving the other legacy publishers, establish
the exact old key UUID and its consumers, replace the other still-authorized
consumers with credentials that cannot write Tenants, verify those credentials,
and delete the assessed old automation key at the registry. This is a wider
credential rotation than removing Tenants from GitHub's selected repositories.
Do not infer permission to rotate unrelated consumers or delete a key from its
label. Do not remove either global administrator, revoke personal access, or
claim that removing GitHub secret selection revokes the registry key.

Adoption stays gated until this concrete mapping/rotation boundary is resolved.
No old key, administrator, org-secret value or remaining module's selection has
been changed by this investigation.

## Shared release dependency

`shared-release-product-phase-complete.json` contains a complete 216-release
inventory and the latest-release endpoint readback: `v6.0.6`, immutable,
published, authored by `github-actions[bot]`, target
`fdda17c0a4538b0f7c99f813c20ca24b49006530`. It lacks the new shared contract.
The first product-phase packet retains a deliberately incomplete inventory
because GitHub changed the pagination route to the numeric repository alias;
the subsequent packet starts from the metadata-verified numeric repository
route and completes without changing the strict Tenants preflight reader.
Use the central release process and verify/pin a compatible published tag before
registration; unreleased Builds source is not a released prerequisite.

On 2026-11-17 this shared release dependency was satisfied independently:
`shared-v610-publication-verification.json` authenticates immutable published
Builds `v6.1.0` at `a1e0c310b1f1a50d78e6132890fae6bcba769f6d` with the required
receipt/timeout and TLS fixes. Complete unchanged CiCd validation03 passed all
global and three registered-module verdicts on
`f56dcbfb167b4701de5b1fc0a130971e6bca8e30`; ordinary fast-forward publication
and authenticated main/pin readback are in `cicd-v610-publication.json`.
The earlier v6.0.6 inventories remain historical evidence. This resolves the
shared release/pin prerequisite, not the registry mapping/consumer boundary,
Tenants product qualification or adoption/legacy cleanup.

## Fresh attended and Kubernetes reads, 2026-11-17

The human confirmed the App form was saved and NuGet signed in. A separate
new App settings tab reads20 saved selected repositories, including Tenants,
with Save disabled; foreign selections (now including Docs) were preserved.
`app-selection-fresh-verification.json` binds the fresh server read.

`nuget-legacy-key-fresh-verification.json` binds the fresh authenticated API Keys
page with Manage expanded and actual loaded key row954800, label Github Hexalith,
Expired, ownerHexalith/globHexalith.*. No active key rows were observed; no key
was deleted/regenerated and this is not a mapping to an encrypted GitHub secret.
The first signed-in read without expanding Manage returned no visible key rows;
that read was incomplete and is retained without treating it as absence.
A separate fresh Trusted Publishing read retains Active27252 with exact
Hexalith.Tenants* push-new-packages/versions scope and old18796. Recovery policy
18797 also remains and must be assessed against its actual workflow/environment
before cleanup; preserve foreign policies. See attended-policy-refresh-01.json.

The human directed investigation through192.168.1.30 Kubernetes access. Intended
context jpiquot@local resolves https://192.168.1.30:6443 and reads registry
configuration/pod metadata and credential references without configuration changes.
The195-secret reference inventory finds no direct HEXALITH_ZOT key-name match.
Memories' actual pull secret registry-credentials is distinct from the existing
personal API key and is not in zak_ format; preserve it. Registry authenticated
public key metadata still lists the same three UUIDs/labels. Neither Kubernetes
metadata nor these public key records establish which UUID backs GitHub's
encrypted organization secret or every external consumer. No credential values
were printed or persisted, and no key was revoked. Exact reads are retained in
kubernetes-legacy-key-reference-inventory.json and
kubernetes-registry-credential-assessment.json. The attempted fixed binary
version read at /usr/local/bin/zot failed; the immutable image digest remains
known but an exact version tag is still unverified.
