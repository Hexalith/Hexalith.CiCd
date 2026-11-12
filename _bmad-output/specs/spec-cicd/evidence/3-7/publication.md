# Builds bootstrap seed acceptance — 2026-11-12

**Accepted `v5.0.1` at 2026-11-12T19:34:53.303685Z.** The [current readiness record](adoption-20261112T192604Z/readiness-validation.json)
passes all 34 checks. [Final independent readbacks](adoption-20261112T192604Z/acceptance.json) repeat
the live release, tag, main, producer, artifacts and key settings immediately
before writing exactly `v5.0.1` plus LF to CiCd's root `builds-version`.

The approved one-time exception accepts this external release's earlier
prerequisite state and missing complete producer-time AD-19 checklist. It was
published before the 16:23 NuGet cleanup and 16:24 authenticated App proof.
These current readbacks establish current readiness; they do not certify
retroactive producer-time compliance. The exception applies only to this seed.

| Accepted identity | Independently authenticated value |
| --- | --- |
| External producer | [43241459875](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43241459875), attempt 1, success |
| Producer workflow/event/branch | `.github/workflows/builds-release.yml`, `workflow_dispatch`, `main` |
| Full built source | `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7` |
| Sole original outcome | `published`, version `5.0.1`, same full source; no `draftId` or `lastTag` field |
| Outcome artifact | `13955866607`, API/download digest `sha256:ed1fc3dc8b14b10d2959e4df55906689eff570a0d408b149697a72a62a0fa5cb` |
| Original release artifact | `13955511619`, available and unexpired through `2027-02-10T14:50:57Z` |
| Original ZIP API/trailer/download digest | `sha256:4d9a9accaa4d65afb555e2573ec3a0812cdc8fc4c10ffcfa71de870672789861` |
| Published release | [443097864 / v5.0.1](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v5.0.1), published `2026-11-12T14:59:06Z` |
| Release author/state | `github-actions[bot]` (`41898282`), published, immutable, stable |
| Peeled tag and current Builds main | Both `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7`; live REST and independent Git agree |
| Base ancestry | `v5.0.0` at `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec` is an ancestor of the built source |

[Producer and artifact verification](adoption-20261112T192604Z/candidate-verification.json) records
complete artifact pagination, the sole outcome's ZIP digest and exact member
`outcome.json`, shared `validate_outcome` and JSON Schema validation, and the
producer's successful jobs. Both original artifacts' API identities, repository,
source, availability and expiry are authenticated independently of the release
trailers. The original `release` ZIP was downloaded and inspected in memory.
The shared `artifact_metadata`, `artifact_inventory`, `package_identity`,
`producer_identity`, `release_trailers` and `validate_release` validators passed;
no runtime phase or publication command was invoked.
The [supplemental schema validation record](adoption-20261112T192604Z/schema-validation-supplement.json)
retains the interpreter, validator version, schema identity/digest and reproducible
invocation for a separately timestamped repeat check.

The [authenticated original manifest](adoption-20261112T192604Z/original-release-manifest.json)
contains exactly `Hexalith.Builds.Evidence.Cli` and `Hexalith.Builds.Module.Cli`
packages at `5.0.1`, both with repository commit `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7`, and an empty
container inventory. The ZIP has exactly the manifest and those two packages;
member sizes and SHA-256 hashes are recorded. Its actual contents, rather than
its empty trailer alone, satisfy the approved package-only registry scope.
Original payload bytes were validated without executing or rebuilding them.
Separately timestamped supplemental nuspec readback in the candidate record retains
each original package's ID, version, repository URL/commit and member hashes from
the same digest-authenticated original ZIP. An independent current NuGet feed
availability check was not performed and is not claimed by this seed acceptance.

Current AD-19 and story 3-6 evidence is retained in the adjacent directory:

- Story 3-6 remains `done`, all seven execution tasks checked, with unchanged
  canonical story and three-layer accepted review proof hashes. The reviewed
  caller/publisher references remain unchanged at the external source.
- The kill switch is exactly `true`, immutable releases are enabled, retention
  is 90 days, and `hexalith-release` permits only custom branch `main` with no
  reviewer or timer. Both required registry-secret metadata records match the
  dedicated account setup. The configured ACL readback is unchanged, and separate
  provisioning proof retains prior successful authentication and zero effective
  grants. [Supplemental running registry metadata](adoption-20261112T192604Z/registry-acl-current.json)
  links the ConfigMap through the deployment/ReplicaSet to the ready Zot pod and
  its read-only `/etc/zot/config.json` mount. This is configured-ACL and mount/health
  evidence; it claims neither a comparison of mounted runtime bytes nor fresh
  credential authentication. The original ACL observation time is preserved.
- Fresh authenticated App UI at 2026-11-12T19:34:05.6059837Z selects exactly
  Builds/CiCd with expected permissions. The API's 403/401 paths remain
  explicitly unreadable. Complete connected selection pagination includes only
  EventStore; forbidden agent Apps are absent from the complete org inventory.
- Fresh NuGet inventory at 2026-11-12T19:34:28.7287931Z contains exactly the sole
  approved Builds policy `26029`: `Hexalith` (`80614290`) /
  `Hexalith.Builds` (`952945989`), `builds-release.yml`, `hexalith-release`,
  `Hexalith.Builds*`, push new packages/versions only. Four obsolete policies
  are absent and all 16 other repository policies match the approved inventory.
  At 2026-11-12T19:34:51.5587173Z, the sole `Github Hexalith` publisher key remains expired.
- Complete legacy secret selections exclude Builds/CiCd, Actions/Dependabot
  pull-secret and NuGet-user selections include Builds, and qualification secret
  and variable metadata and exact isolated registry grants are preserved.
- Both exact rulesets remain active with no bypass actors. Complete 100/100/5
  release pages contain 204 published releases and one unchanged qualification
  draft `441591623`; all 204 tags match independent Git and have publications.
  Both removed orphan refs remain absent. Protected artifact `13850760915` is
  unchanged, available and unexpired; its package/image history is preserved
  without claiming newly authenticated historical package/image bytes.
- Latest eligible exact-source CI
  [43237014144](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43237014144)
  is successful with all seven jobs green.

The completed interactive [no-op run 43262148178](release.md), its original
`nothing` outcome, passing preflight and original evidence remain unchanged.
It produced no payload or seed and is separate from external producer
`43241459875`. This acceptance performed zero dispatches, publications,
rebuilds, setting/credential/resource changes or Builds source changes.

CiCd baseline is `af8e2bcc3391fe842b895815fee7ec403a165051`. The clean pinned
Builds checkout and gitlink remain `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`.
The seed, this story and sanitized acceptance evidence were committed together as
`bc1fcf61304b144729589b6deb2ba2ce1a99a62c` with a `build(cicd)` message. The
[archived original post-commit result](adoption-20261112T192604Z/post-commit-verification.json),
observed at `2026-11-12T19:35:35.295665+00:00`, records committed seed blob
`4bccc27e8978a926aa4d0b464a2cfe3196754729`, exact bytes `76352e302e310a`,
verification of that commit's 21 evidence blobs, and independent live tag
resolution to the accepted full source. Supplemental review-time metadata is
separately timestamped and does not replace that historical result or the
original acceptance timestamps. Rendering and delivery await their implementation stories.
The adjacent SHA-256 manifest binds every JSON evidence file.
