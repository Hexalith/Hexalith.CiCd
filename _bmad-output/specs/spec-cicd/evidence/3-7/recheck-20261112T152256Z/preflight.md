# Bootstrap preflight recheck — 2026-11-12 15:22 UTC

**Verdict: STOP before dispatch.** GitHub and Git observations were captured at
2026-11-12T15:22:56Z–15:23:10Z; connected GitHub selection readback followed at
15:24 UTC. Current CiCd App selection for Builds remains unreadable, and the
required exclusive NuGet production policy and legacy/spike/probe policy and
credential disposition proof remains missing. These are unsatisfied AD-19
prerequisites. This assessment cannot dispatch or seed a release.

The approved earlier repair now passes live readback: immutable releases are
enabled, both removed orphan refs are absent, and the original tag ruleset is
active. The required registry secret pair still matches the approved dedicated
account setup. These observations supersede the corresponding failures in the
13:36 UTC assessment; they do not settle the remaining proof requirements.

## Source and review reconciliation

| Identity | Observation |
| --- | --- |
| CiCd local/remote `main` | `a60a60a08f46a0c02422a6d850b00bbd295ae694` |
| Story-recorded CiCd baseline | `a60a60a08f46a0c02422a6d850b00bbd295ae694` |
| Earlier parent's captured baseline | `0b8123b504f8946371a4c0274998d6e9b17cd28a`; retained as a separate historical identity |
| Pinned Builds checkout and CiCd gitlink | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`; clean and unchanged |
| Current remote Builds `main` | `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7` |
| Story 3-6 | `done`; all seven execution tasks checked; canonical story and review-completion proof hashes unchanged |

[Baselines](baselines.json) records each identity and hashes the unchanged local
caller, CI, release-state, version, draft, publisher, outcome and recovery
references. The read-only compare API shows remote Builds is three commits
ahead of the pinned checkout. Its four changed files are package-catalog/audit,
product runtime and product-test files; the reviewed caller/publisher files are
unchanged. No checkout or gitlink was advanced to follow this external work.

## Authentication and read limits

The effective default remains
`/home/administrator/.config/gh-cicd-agent`; no `GH_TOKEN` or `GITHUB_TOKEN`
override is present. Both intended profiles authenticate as `jpiquot` and target
`Hexalith/Hexalith.Builds`. Administrative metadata GETs use only the command-local
maintainer profile `/home/administrator/.config/gh`.
[Authentication](authentication.json) records the account/repository checks
before setting reads. Account `admin:true` is not token API permission evidence.

The scoped profile's refused setting reads retain their HTTP status and accepted
permission headers in [settings](settings.json). Successful maintainer GETs
supply the corresponding setting observations. CiCd App selected-repository
GET returns HTTP 403; the CLI reports missing `read:user`. The App-authenticated
repository-installation endpoint returns HTTP 401, `A JSON web token could not
be decoded`. The connected GitHub tool independently returns HTTP 403,
`Resource not accessible by integration`, for installation `179966090`.
These responses leave its Builds selection unverified. No credential expansion,
App-key read, credential-file read or App authentication creation was performed.

## Preconditions

| Gate | Verdict | Evidence / required completion |
| --- | --- | --- |
| 3-6 review/tracking | PASS | `done`, seven tasks checked; prior review-completion hashes retained in baselines. |
| Exact kill switch | PASS | Maintainer GET returns `HEXALITH_RELEASE_PUBLISH_ENABLED` exactly `true`. |
| Immutable releases | PASS | Live GET returns `enabled:true`, `enforced_by_owner:false`; earlier approved enablement proof is preserved. |
| Artifact/log retention | PASS | `days:90`, `maximum_allowed_days:90`. |
| Release environment | PASS | `hexalith-release`, one custom deployment branch policy `main`, branch-policy protection only; no reviewer/timer. |
| Required Builds registry pair | PASS for approved package-only scope | Both required secret names retain their 12:58:36Z/12:58:37Z creation/update metadata. The separately hashed provisioning proof records dedicated `hexalith-builds-publish` authentication and zero effective repository/default/group/admin grants. This recheck reads metadata, not credentials, and makes no fresh authentication claim. Any actual container-bearing original artifact stops bootstrap and requires an approved exact repository allowlist before a subsequent container release. |
| Org variable/pull-secret access | PASS for GitHub selection | Complete repository selections include Builds for `HEXALITH_NUGET_USER` and both registry pull secrets in Actions and Dependabot. |
| CiCd App installed on Builds | **UNVERIFIED** | Installation `179966090` exists with expected permissions; current selected-repository readback is refused by the maintainer API and connected tool. Require timestamped maintainer proof that Builds is selected. |
| Other agent Apps exclude Builds/CiCd | PASS for current inspected installations | Complete org inventory has no `claude`, `cursor` or `semgrep-app`. Fresh connected-tool pages for connector `77847816` contain only `Hexalith.EventStore`, then an empty page. It excludes Builds/CiCd. |
| Exclusive NuGet production policy | **UNVERIFIED** | No current proof establishes the exclusive `Hexalith/Hexalith.Builds` / `builds-release.yml` / `hexalith-release` / `Hexalith.Builds*` policy or reconciles the legacy, wildcard spike and probe policies. Historical package publication is not policy-inventory proof. |
| Legacy/spike/probe credential disposition | **UNVERIFIED** | No new maintainer disposition supplies current legacy publication access or spike identity/secret/grant decisions. The existing spike environment secret metadata is retained. Preserve the qualification draft and its artifact/package/image history. |
| Exact AD-21 rulesets | PASS | Only `19196298` (default-branch deletion/non-fast-forward) and `26812219` (`refs/tags/v*` update/deletion) exist, both active, with no bypass actors and tag creation allowed. Live protection content matches the approved repair evidence. |
| Every `v*` tag published | PASS | 204 refs and 204 published releases, no orphans; independent live Git inventory matches the API refs exactly. `v4.46.0` and `v4.47.1` each return 404. |
| Qualification history preserved | PASS for captured metadata | Sole draft `441591623` retains its qualification source marker, body hash and original trailers. Original artifact `13850760915` remains unexpired with the same digest/producer metadata. No production source marker exists on that draft. No package/image or retained resource was mutated by this assessment. |
| Latest exact-source CI | PASS | Run [43237014144](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43237014144), `.github/workflows/builds-ci.yml`, push/main at `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7`, succeeds; all seven jobs succeed. |

[Selections](selections.json), [connected selection readback](connected-selections.json),
[settings](settings.json), [CI readback](ci-readback.json) and
[retained artifact metadata](retained-artifact.json) retain the exact observations.
The existing [NuGet findings](../remediation-20261112T140005Z/nuget-prerequisite-followup.json)
identify the missing maintainer proof. This assessment performs no authenticated
NuGet administration read or policy mutation and supplies no replacement proof.

## Complete inventory and external publication

[Inventory](inventory.json) contains all 205 release records from explicit pages
of 100/100/5: 204 published releases and the qualification draft. The matching-ref
response has 204 entries and no continuation link; independent Git listing
matches all refs and provides tag peeling. Historical release/tag identities and
the protected draft are compared against the approved repair snapshot in
[validation](validation.json).

One release was published externally after the earlier repair snapshot:

| External identity | Current readback |
| --- | --- |
| Version / release | `v5.0.1` / `443097864`; bot-authored, published, stable, `immutable:true` |
| Publication time | `2026-11-12T14:59:06Z` |
| Built / live peeled tag commit | `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7` |
| Historical caller run | [43241459875](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43241459875), main/manual, created `2026-11-12T14:50:56Z`, success |
| Recorded original artifact trailer | `13955511619`, `sha256:4d9a9accaa4d65afb555e2573ec3a0812cdc8fc4c10ffcfa71de870672789861` |

This run predates this invocation's preflight. It is external history, not this
invocation's dispatch or an accepted bootstrap seed. Its empty container trailer
is recorded without claiming authentication of the original artifact's inventory.
It does not supply missing App-selection or exclusive NuGet/disposition proof.
The older `v4.48.3` and `v5.0.0` publications remain mutable historical releases.

## Stop and verification

The preflight task remains unchecked because required completion proof and a
passing immediately-before-dispatch recheck are absent. No dispatch, original
artifact/outcome acceptance, maintainer publication handoff or seed commit is
performed. `builds-version` remains absent from disk, index and `HEAD`.
No `release.md`, `publication.md`, resolution marker, runtime change, settings
mutation, cleanup, checkout advance, gitlink movement or commit is produced.

After timestamped maintainer proof settles the remaining App and NuGet/disposition
gates and the story is re-armed, repeat every AD-19 precondition and the complete
paginated inventory immediately before the single authorized interactive caller
dispatch. This stopped snapshot cannot authorize that dispatch.

Verification parses all JSON, checks page/ref uniqueness and API/Git parity,
preserved historical releases/tags/draft/artifact, restored rulesets, secret
metadata and zero-write provisioning proof, green exact-source CI, unchanged
review references/checkout/gitlink, absent seed and `git diff --check`.
No runtime or workflow-text tests are added for this operational assessment.
The adjacent [SHA-256 manifest](SHA256SUMS) binds the evidence files.
