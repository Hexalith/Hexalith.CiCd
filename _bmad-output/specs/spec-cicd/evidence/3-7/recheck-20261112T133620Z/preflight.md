# Bootstrap preflight recheck — 2026-11-12 13:36 UTC

**Verdict: STOP before dispatch.** Read-only evidence captured at
2026-11-12T13:36:20Z–13:36:30Z confirms immutable releases are disabled and
orphan tags `v4.46.0` and `v4.47.1` still exist. Current App/connector repository
selections and NuGet/legacy/probe policy and credential disposition remain
unverified. Selecting the maintainer's remediation path is not its completion.

The dedicated package-only registry prerequisite has improved since the earlier
assessment: the required environment secret pair now exists, and the approved
12:58:33Z–12:59:11Z provisioning proof records separate authentication and
zero-effective-write-ACL checks. The latest exact-source CI also now succeeds.
Those observations do not satisfy the remaining release gates.

No workflow was dispatched, draft published, setting or retained resource
changed, seed written, gitlink moved, or commit created by this recheck. All
GitHub requests are GETs. No credentials, secret values, App private key,
credential files or OIDC exchanges were read or recorded.

## Source and authorization

| Identity | Observation |
| --- | --- |
| CiCd observed local and remote `main` | `a60a60a08f46a0c02422a6d850b00bbd295ae694` |
| Parent's separately captured pre-implementation baseline | `0b8123b504f8946371a4c0274998d6e9b17cd28a`; the intervening commit is preserved |
| Builds local and remote `main` | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0` |
| CiCd committed Builds gitlink | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`; unchanged |
| Builds working tree | Clean |
| Story 3-6 | Canonical `done`, seven checked execution tasks, no unchecked tasks; reviewed delivery unchanged |
| Seed | Absent from disk, index and `HEAD` |

[Baselines](baselines.json) record the full observed revisions, source-file
hashes, 3-6 review/story hashes and the sanitized registry prerequisite proof.
The observed CiCd HEAD does not replace the parent's earlier captured baseline.
The existing caller and publisher remain unchanged. The pipeline alone owns
version/initial-major selection; historical releases are not adopted as this
invocation's dispatch or seed.

The effective default remains `/home/administrator/.config/gh-cicd-agent`,
account `jpiquot`, target `Hexalith/Hexalith.Builds`. Neither `GH_TOKEN` nor
`GITHUB_TOKEN` is present. Both intended profiles' account, repository and
read-only permission metadata were checked before interpreting authorization
failures. Administrative readback used command-local
`GH_CONFIG_DIR=/home/administrator/.config/gh`; the default was preserved.
[Authentication metadata](authentication.json) contains no credentials.

## Gate verdicts

| Gate | Verdict | Evidence / required completion |
| --- | --- | --- |
| Story 3-6 review/tracking | PASS | Canonical `done`, seven checked tasks, recorded review completion and unchanged reviewed delivery. |
| Exact kill switch | PASS | Maintainer readback returns `HEXALITH_RELEASE_PUBLISH_ENABLED` exactly `true`. |
| Immutable releases | **FAIL** | `enabled:false`, `enforced_by_owner:false`. Maintainer enablement/proof is still required. |
| Artifact/log retention | PASS | 90 days, maximum allowed 90. |
| Release environment | PASS | `hexalith-release`, one custom branch policy `main`, no reviewer or wait timer. |
| Required registry secret pair | PASS for approved package-only prerequisite | `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD` exist, created at 12:58:36Z and 12:58:37Z. The previous `HEXALITH_REGISTRY_PUSH_*` metadata remains present. No values were read. |
| Dedicated registry account/authentication/ACL | Recorded prerequisite proof verified | Account `hexalith-builds-publish`, distinct from legacy/spike/pull identities; proof records authenticated 200, incorrect/anonymous 401, denied repository creates and zero effective actions for both ACL patterns, with no admin/default/group grants. This is the approved provisioning proof, not a new live registry authentication. Any future original artifact must have an empty container inventory. |
| Org variable and pull-secret access | PASS for selection | Builds is selected for `HEXALITH_NUGET_USER` and both registry pull secrets in Actions and Dependabot; returned counts match the complete lists. |
| CiCd App installed on Builds | **UNVERIFIED selection** | Org listing contains active `hexalith-cicd`, installation `179966090`, selected repositories, with expected Actions/Contents/Workflows write and Administration/security-events read. Its selected-repository GET remains HTTP 403. Require current maintainer selection proof. |
| Other agent Apps exclude Builds/CiCd | **UNVERIFIED connector selection** | Complete six-installation org listing has no `claude`, `cursor` or `semgrep-app`. `chatgpt-codex-connector` installation `77847816` remains selected; its repository-selection GET is HTTP 403. Require current exclusion proof. |
| NuGet and legacy/probe policy/credential disposition | **UNVERIFIED** | No new maintainer completion proof establishes exclusive `builds-release.yml` / `hexalith-release` / `Hexalith.Builds*` policy scope or reconciled legacy/probe policies and credentials. Historical package success does not establish those settings. |
| AD-21 rulesets | PASS for current configuration | `19196298` is active default-branch deletion/non-fast-forward only. `26812219` is active for `refs/tags/v*` update/deletion only, creation allowed, no bypass actors. |
| Chosen maintainer orphan-tag remedy | **INCOMPLETE / FAIL** | Both `refs/tags/v4.46.0` and `refs/tags/v4.47.1` remain. The existing active ruleset does not prove the chosen cleanup completed. This recheck authorizes no cleanup or ruleset mutation. |
| Qualification draft/resources | Draft intact; policy/credential completion unverified | Sole retained draft `441591623`, `v4.47.1`, remains qualification-marked at source `75e1d4a3809b30684e67c7e9b2c8043720b49c53`, with original run/artifact/package/image trailers unchanged. It is not a production marked-draft blocker. No resources were modified or original artifact republished/rebuilt. |
| Latest eligible exact-source CI | PASS | Push run [43203712508](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43203712508), attempt 1, `builds-ci.yml`, main, source `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`: `success`, all seven jobs successful. |

[Settings](settings.json) retain exact response dates and permission headers.
Six scoped administrative reads returned HTTP 403,
`Resource not accessible by personal access token`, advertising
`actions_variables=read`, `administration=read`, `environments=read` or
`secrets=read` as applicable. Successful maintainer readback supplies the
corresponding settings; account `admin:true` does not establish token scope.

Both repository-selection failures return HTTP 403:
`You must authenticate with an access token authorized to a GitHub App, a personal access token, or basic auth in order to list repositories for an installation.`
The CLI additionally reports missing `read:user`. These failures leave selection
unverified; they do not prove absence/exclusion and no credential expansion was
requested. [Selection metadata](selections.json) retains those exact failures.

## Inventory and stop boundary

[Complete inventory](inventory.json) contains 205 `v*` refs, independently matched
against `git ls-remote`, and every release from explicit pages of 100, 100 and
4 rows: 203 published releases and one retained draft. The orphan refs still
resolve to `a8a87160f2708322d5520742b9a0c3f93d23db78` (`v4.46.0`) and
`75e1d4a3809b30684e67c7e9b2c8043720b49c53` (`v4.47.1`). The draft's
historical `published_at` value is not treated as publication while `draft:true`.

Historical bot publications `v4.48.3` / release `442699245` and `v5.0.0` /
release `442792929` remain non-immutable and preserve their original source/tag
identities. Neither supplies an acceptable AD-10 seed. The existing caller's
12 main/manual runs remain historical; no new run was created or adopted.
[Current CI readback](ci-readback.json) is separate from those release runs.

The preflight checklist task remains incomplete because maintainer completion
proof and a passing immediately-before-dispatch recheck are still required.
Dispatch, original-artifact/outcome authentication, publication/handoff and seed
commit tasks remain unexecuted. No `release.md` or `publication.md` is fabricated
for this stopped assessment. After prerequisite completion, repeat all AD-19
checks and complete inventory before the one authorized interactive dispatch.
A future container-bearing artifact stops this package-only bootstrap; a
future `nothing` or `disabled` outcome leaves the seed absent without redispatch.

Verification checks evidence JSON, pagination/count invariants, tag/API parity,
unchanged source hashes/gitlink, absent seed, clean Builds checkout, and
`git diff --check`. No runtime or workflow-text tests apply to these evidence
changes. [SHA-256 manifest](SHA256SUMS) binds this snapshot.
