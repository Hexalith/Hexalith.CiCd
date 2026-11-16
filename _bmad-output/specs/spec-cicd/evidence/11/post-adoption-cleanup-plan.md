# Concrete pilot cleanup targets

The prepared scope below was executed after authenticating both actual App
adoption commits/refs/report. Completed results are in
`post-adoption-github-cleanup.json`, `nuget-cleanup-verify-cleanup.json` and
`post-adoption-legacy-codeql-cleanup.json`; every planned target is verified,
including explicit credential no-ops. The bounded
pilot-specific Zot no-op in `zot-pilot-legacy-disposition.md` supersedes the
earlier broad administrator-attestation blocker; global key mapping is still
unverified and no shared administrator is altered.

| Operation immediately after adoption | Commons | PolymorphicSerializations | Safety boundary |
| --- | --- | --- | --- |
| Enable immutable releases | `PUT repos/Hexalith/Hexalith.Commons/immutable-releases` | `PUT repos/Hexalith/Hexalith.PolymorphicSerializations/immutable-releases` | Empty body; require HTTP 204 then authenticated `enabled: true` readback. Use only the command-local maintainer profile. |
| Remove legacy Trusted Publishing policy | Policy `20233`, name `Hexalith.Commons`, production environment | Policy `20232`, name `Hexalith.PolymorphicSerializations`, production environment | Recheck exact repository IDs `952960148`/`957156862`, owner `Hexalith#80614290`, `release.yml`, and `production` before invoking the matching card's Delete control. Keep new policies `27048`/`27049`, with `hexalith-release` and their existing package-prefix scopes. Fresh inventory must still match the assessed targets; do not delete another repository's policy or guess a changed ID. |
| Remove legacy org-secret selection | Already absent | Already absent | Complete Actions/Dependabot inventories show neither pilot in any legacy family (`NUGET_API_KEY`, `HEXALITH_ZOT_*`, `AZURE_*`, `SONAR_TOKEN`). Recheck after adoption. If a verified legacy selected-secret membership appears, remove only the exact pilot repository ID, retaining all other selections and the secret value. Keep the new Actions/Dependabot pull-pair selections and `HEXALITH_NUGET_USER`. |
| Remove legacy repo/environment secrets and deploy keys | Already absent | Already absent | Both repository secret inventories, both `production` secret inventories and both deploy-key inventories are empty. Retain each new `hexalith-release` pair. Recheck; preserve the empty foreign `production` environment itself. |
| Legacy NuGet API key | Sole visible key `Github Hexalith`, ID `954800`, already Expired | Same shared account observation | Preserve the prior explicit expired-key disposition without regeneration/replacement. Its `Hexalith.*` display is not proof of a mapping to the GitHub org secret. Do not delete another module's key or claim a secret-value mapping. |
| Legacy Zot push access | **Pilot-specific no-op** | **Pilot-specific no-op** | Complete workflow/container scope and current secret inventories identify no legacy pilot publisher path or credential grant. Recheck those facts at cleanup. Preserve both global administrators, existing keys, the four legacy-selected modules, new own identities and the qualification identity; global key mapping remains unverified. |

GitHub documents the
[immutable-release enable operation](https://docs.github.com/en/rest/repos/repos#enable-immutable-releases).
The concrete settings and successful intended-profile reads are retained in
`cleanup-github-inventory.json`, with every selected org-secret repository list,
both repository/environment secret inventories and deploy-key inventories.
`nuget-policy-verification.json` and the final reloaded UI snapshot identify the
policies to retain and their unchanged legacy siblings. The expired key's
visible metadata is in `legacy-nuget-key-metadata.json`; story 3-7 records the
prior explicit disposition without asserting a secret/principal mapping.

The registry question is substantive. The current ConfigMap ACL snapshot is in
`cleanup-registry-acl.json`, resourceVersion `46533286`. Zot's
[authorization documentation](https://zotregistry.dev/v2.0.0/articles/authn-authz/)
states that `adminPolicy` overrides repository policies. Removing an existing
admin's grant from only the four pilot namespace patterns would therefore not
revoke that admin's access. Removing a global administrator without establishing
its automation role could affect shared access outside these pilots. The
earlier request for a global administrator-role attestation was broader than
the pilot cleanup needs. The human cannot attest to that mapping. The complete
pilot-specific source and credential evidence instead supports an explicit
no-op, accepted by root; see `zot-pilot-legacy-disposition.md`. Existing admin
pulls for Memories are positively observed and preserved. Neither a global key
inventory nor absence of administrator automation is asserted.

After every actual cleanup, preserve exact before/after settings and policy IDs,
including no-op results where access was already absent. A no-op inventory may
prove absence of a selected GitHub grant; it does not prove an unverified Zot
principal mapping or revoke a global administrator.
