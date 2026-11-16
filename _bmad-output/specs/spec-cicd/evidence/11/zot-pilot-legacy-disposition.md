# Pilot-specific legacy Zot disposition

The human cannot identify or attest to the existing administrators' global key
usage. Read-only investigation instead establishes the scope relevant to AD-21:
neither package-only pilot has a legacy Zot publishing path or legacy credential
grant to retire. Root independently accepted this bounded no-op on 2026-11-16;
it supersedes the overly broad human-attestation blocker. Global API-key
identity/scope mapping remains unverified. No administrator, key or other
module's grant was changed.

## Pilot automation scope

`zot-pilot-automation-scope.json` records exact mains matching the fresh
authenticated GitHub refs: Commons `ab5e92faa3bab1fa43b8ecadd423432dfe652bb2`
and Poly `476cfccac3c5ba694a8e0ef11b1157728b9ec093`.

| Observation | Commons | PolymorphicSerializations |
| --- | --- | --- |
| Complete, non-shallow main ancestry | 448 commits | 190 commits |
| Unique historical workflow blobs inspected case-insensitively | 71 | 19 |
| Zot/registry host, credential-name or Docker login/push reference | None | None |
| Secret inheritance or dynamic secret indexing | None | None |
| Current workflow secret references | `GITHUB_TOKEN` only | `GITHUB_TOKEN` only |
| Current or historical Dockerfile/Compose/container project files | None | None |
| Current project inventory | 20 `Microsoft.NET.Sdk` projects, no container properties | 4 `Microsoft.NET.Sdk` projects, no container properties |

The static container inventory describes tracked inputs, not an invented live
release artifact. The local adopted configuration also has `registry: false`.
Both complete package-mode product verification sets remain independently saved.

Fresh complete org-secret metadata/selected-repository lists show the pilots
receive only the new pull pair. The legacy Zot pair selects exactly EventStore,
Memories, Parties and Tenants; neither pilot is selected. Both pilots' repository
Actions/Dependabot and legacy `production` environment secret inventories are
empty. `zot-pilot-org-secret-access.json` and
`zot-identity-github-selection.json` retain these successful authenticated reads.
The new dedicated `hexalith-release` pairs remain correctly scoped and retained.

## Other-module access and key mapping limits

`zot-identity-auth-metadata.json` confirms both administrator names are absent
from Basic-auth usernames. OIDC and API-key authentication are enabled. This
does not establish absence of administrator-owned API keys.

Bounded current-pod logs positively show `jpiquot@itaneo.com` making authenticated
containerd HEAD/GET pulls for Memories repositories. They show no administrator
pilot requests or writes in that retained window. These observations establish
other-module pull use; they do not identify a GitHub publisher, a key UUID or
its scope. Raw logs, authorization values and credential hashes were discarded.
See `zot-admin-usage-metadata.json` and `zot-identity-log-observation.json`.

The intended maintainer GitHub audit-log request returns authenticated HTTP 404
after account/profile/repository/scope checks. It leaves audit access unverified.
Zot's [documented key metadata GET](https://zotregistry.dev/v2.1.11/developer-guide/api-user-guide/#listing-your-current-api-keys)
lists a logged-in user's keys without retrieving key values. The normal browser
GET initially reached `/login`; a bounded subsequent attempt found no reachable
registry/issuer metadata or SSO control. `ordinary_sso_invoked` is false. Later
inspection of that exact endpoint's browser window identified a native
username/password authentication dialog obscuring the document; its password
control's `IsPassword` flag establishes a human credential prompt. Cancelled it
without reading/entering values. `zot-identity-sso-attempt.json` and
`zot-identity-api-auth-prompt.json` preserve both observations. No browser-cookie/
storage extraction, key creation or key revocation occurred. No global key
inventory or identity/scope mapping is claimed.

## AD-21 application

AD-21 requires revoking “the legacy Zot identity's push on its repositories”
after adoption. The relevant identity is legacy module publishing automation;
the clause does not classify every maintainer administrator or another module's
active client as that pilot's publisher. These package-only pilots have no
tracked container publishing path, no legacy Zot credential availability and no
identified legacy per-pilot push identity. Their revocation operation therefore
has no target and is explicitly a no-op. Removing a global administrator would
also affect the positively observed Memories access and violate the requirement
to preserve unrelated access.

At actual cleanup, recheck exact current module scope and legacy secret
exclusion. Record the no-op only while those facts remain true. If a new pilot
container path or legacy grant appears, reassess its concrete identity/scope
before claiming cleanup. Preserve both global administrators, all four remaining
legacy-selected modules, existing maintainer keys, pull identities, the
qualification identity and each new dedicated pilot identity. No frozen spec
exception, global-key guarantee or broad revocation is needed for this bounded
disposition.
