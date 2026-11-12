# Bootstrap preflight — 2026-11-12

**Latest recheck: STOP before dispatch, 2026-11-12T15:22:56Z–15:23:10Z.**
[Fresh gate verdicts and sanitized evidence](recheck-20261112T152256Z/preflight.md)
confirm immutable releases enabled, both orphan refs absent, the original tag
protection restored and connector exclusion verified. Current CiCd App Builds
selection and exclusive NuGet/legacy/spike/probe policy and credential disposition
still lack completion proof. The required package-only registry pair and green
exact-source CI pass. External immutable publication `v5.0.1` predates this
assessment and is not adopted as its dispatch or seed. No release was dispatched
or version seed created by this assessment.

The [13:36 UTC stopped recheck](recheck-20261112T133620Z/preflight.md) and the
[approved 14:01 UTC repair evidence](remediation-20261112T140005Z/github-prerequisites.json)
remain preserved as historical observations.

## Earlier stopped assessment — 11:05 UTC

**Verdict: STOP before dispatch.** Read-only observations were captured at
2026-11-12T11:05:14Z–11:07:20Z. Immutable releases remain disabled, the
environment lacks the push-secret names required by the unchanged caller, and
two `v*` tags lack published releases. Current App selections, registry identity
scope, NuGet policy and probe-policy/credential disposition remain unverified.
No maintainer remediation or new attestation was supplied during this execution.
The current source's latest eligible CI run is also still in progress.

No workflow was dispatched, draft published, setting or retained resource
changed, seed written, gitlink moved, or commit created by this execution.
`builds-version` is absent from disk, index and `HEAD`.

## Reconciliation and source

The approved first-compliant-seed scope is the story's 2026-11-12 Spec Change
Log decision: accept the existing pipeline's exact stable version and initial
major after all gates pass. Historical external publications are not this
execution's dispatch and neither is accepted as a seed.

| Identity | Fresh observation |
| --- | --- |
| CiCd `main`, local and remote | `9ca3f1b0e53d7ffd6d6deea2410098123e50fa68` |
| Builds `main`, local and remote | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0` |
| CiCd committed Builds gitlink | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`; unchanged |
| Builds working tree | Clean |
| Story 3-6 | `done`, seven execution boxes checked, three independent review layers triaged |
| 3-6 reviewed source | `14bb22d9fb2124405ce23c22bd0d38ad55be7836` |
| 3-6 final documentation/evidence delivery | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`; current pinned source |

The story's planning-time statement that 3-6 was `in-review` is historical.
Current canonical 3-6 tracking, its Auto Run Result, Builds' results and
`evidence/cicd-3-6/review-completion.json` agree that review finished. The
four deferred product/tooling follow-ups remain recorded; no untriaged
release-caller fix is identified there. This reconciliation does not establish
that AD-19 settings pass. [Baselines and read-only file hashes](baselines.json)
bind these observations to the exact checkout.

## Authentication and read limits

The effective default is `/home/administrator/.config/gh-cicd-agent`, account
`jpiquot`, target `Hexalith/Hexalith.Builds`. Neither `GH_TOKEN` nor
`GITHUB_TOKEN` overrides is present. The existing maintainer account is also
`jpiquot`; administrative metadata reads used a command-local
`GH_CONFIG_DIR=/home/administrator/.config/gh` only. The default was preserved.
All GitHub requests in this evidence are GETs. No credentials, secret values,
credential files, OIDC exchanges or App private keys were read or recorded.

The scoped profile's eight refused settings reads returned HTTP 403,
`Resource not accessible by personal access token`. Their individual
`X-Accepted-Github-Permissions` headers are retained in [settings.json](settings.json):
`actions_variables=read`, `administration=read`, `environments=read` or
`secrets=read`, as applicable. Those responses leave settings unverified until
the successful maintainer readback supplies the corresponding observation.
Account `admin:true` is not token-permission evidence. [Authentication metadata](authentication.json)
records both intended profiles without credentials.

## Preconditions

| Gate | Verdict | Evidence / required disposition |
| --- | --- | --- |
| 3-6 review and tracking | PASS | Reconciled above; canonical `done` with all execution tasks checked. |
| Exact kill switch | PASS | Maintainer GET returns `HEXALITH_RELEASE_PUBLISH_ENABLED` value exactly `true`; scoped GET is 403. |
| Immutable releases | **FAIL** | Maintainer GET `immutable-releases` returns `enabled:false`, `enforced_by_owner:false`. The maintainer must enable them before another bootstrap preflight. |
| 90-day artifact/log retention | PASS | `days:90`, `maximum_allowed_days:90`. |
| Release environment | PASS | `hexalith-release`, exactly one custom branch policy `main`, only a branch protection rule; no reviewer or timer. |
| Builds-owned push pair required by caller | **FAIL / scope UNVERIFIED** | Environment has exactly `HEXALITH_REGISTRY_PUSH_USERNAME` and `HEXALITH_REGISTRY_PUSH_PASSWORD`. Caller requires `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD`, neither present there or among accessible org secrets. Maintainer must provision the required names and prove the identity pushes only Builds repositories and is distinct from legacy/spike credentials. Names alone cannot establish registry ACLs; no values were inspected. |
| Org variable and pull-secret access | PASS for GitHub selection | Builds can read `HEXALITH_NUGET_USER` and both `HEXALITH_REGISTRY_PULL_USERNAME/PASSWORD`; complete selected-repo lists include Builds for the variable and both Actions and Dependabot secrets. Existing credential semantics are unchanged; this read performs no registry authentication. |
| CiCd App installed on Builds | **UNVERIFIED selection** | Org listing contains active `hexalith-cicd`, installation `179966090`, `selected`, with Actions/Contents/Workflows write and Administration/security-events read. The exact selected-repo GET is 403; installation listing alone does not prove Builds is selected. Latest repository attestation found is 2026-11-09. Require current maintainer selection proof. |
| Other agent Apps exclude Builds | **UNVERIFIED connector selection** | Complete org listing has no `claude`, `cursor` or `semgrep-app` installation. `chatgpt-codex-connector` is `selected`, installation `77847816`, but selected-repo GET is 403. Require current proof it excludes Builds/CiCd; the prior 2026-11-09 attestation is historical. |
| NuGet production policy and legacy/probe policies | **UNVERIFIED** | No current maintainer policy proof is present for repository `Hexalith/Hexalith.Builds`, caller `builds-release.yml`, environment `hexalith-release`, package scope `Hexalith.Builds*`, with legacy/probe policies reconciled. GitHub variable access and successful historical publication do not prove exclusive package scope or policy retirement. No authenticated NuGet administration surface was available in this execution. |
| AD-21 rulesets | PASS | Exactly two active repo rulesets: `19196298`, default-branch deletion/non-fast-forward only; `26812219`, `refs/tags/v*` update/deletion only. No bypass actors; tag creation remains allowed. |
| Every `v*` tag has a published release | **FAIL** | Complete inventory: 205 tags, 203 published releases; orphan `v4.46.0` at `a8a87160f2708322d5520742b9a0c3f93d23db78`, orphan `v4.47.1` at `75e1d4a3809b30684e67c7e9b2c8043720b49c53`. Maintainer disposition/remediation is required. This preflight authorizes no tag deletion, policy change or ruleset disabling. |
| Retained draft and probe-resource disposition | Production marker clear; **UNVERIFIED policy/credential disposition** | Sole draft `441591623`, `v4.47.1`, is qualification-marked and has no `hexalith-release:` source marker. It is not a production marked-draft blocker. It retains original run/artifact/package/image trailers. Preserve it and its resources; no current maintainer proof reconciles its dedicated policy/credentials and the older wildcard spike policy. |
| Latest exact-source green CI | **WAIT / not yet green** | Push run [43203712508](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43203712508), attempt 1, `.github/workflows/builds-ci.yml`, `main`, full source `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`, is `in_progress`, conclusion null at 11:07:19Z. Six retained jobs succeeded; catalog job `131133415231` is running. No dispatch waits on or substitutes an older source. |

The App/connector selection GETs return HTTP 403 with message
`You must authenticate with an access token authorized to a GitHub App, a personal access token, or basic auth in order to list repositories for an installation.`
The CLI additionally reports missing `read:user`. This describes the actual read
failure; it neither proves exclusion/absence nor requests credential expansion.
Current maintainer settings-page proof can settle selection. Complete responses
and successful org selections are in [selections.json](selections.json).

## Complete inventory and preserved history

[Inventory](inventory.json) records every `v*` ref and every release identity.
Explicit release pagination returned 100, 100 and 4 rows. Of the 204 release
records, 203 are published (`draft:false`) and one is a retained draft. The
matching-refs response has 205 entries and no continuation link; independent
`git ls-remote origin 'refs/tags/v*'` exactly matches its complete ref/object
set and supplies annotated-tag peeling. No published release is inferred from
a draft's historical `published_at` field.

| Historical external publication | Release | Live immutable | Full built / peeled tag commit |
| --- | --- | --- | --- |
| `v4.48.3` | `442699245`, bot-authored, published 2026-11-12T09:13:04Z | `false` | `1ecbcd6c6f61629086d019c37557d10d4247b0c3` |
| `v5.0.0` | `442792929`, bot-authored, published 2026-11-12T10:31:01Z | `false` | `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec` |

Neither satisfies AD-10 or supplies this invocation's dispatch. Their release
trailers and all retained draft trailers are preserved in the inventory; no
publication, rebuilding, disposal or version reuse is authorized by recording
them. The existing caller's 12 main/manual runs were inventoried in
[settings.json](settings.json); the latest is historical run `43199661851`.
No run, outcome artifact, original release artifact or publication identity
exists for this stopped execution. [CI readback](ci-readback.json) records the
separate current-source push run and all seven jobs.

## Execution boundary and resume

The first checklist task is complete: approved scope and current 3-6 review
tracking are reconciled and exact baselines captured. Preflight evidence is
complete for this stopped assessment; its task remains unchecked because its
required maintainer dispositions and passing immediately-before-dispatch
recheck are incomplete. Dispatch, outcome authentication, publication handoff
and seed commit tasks remain unexecuted.

After the maintainer resolves the failed/unverified prerequisites, repeat every
AD-19 check and the complete draft/tag/release inventory in an interactive CiCd
session immediately before any one authorized caller dispatch. This snapshot
cannot be reused as a passing preflight. Preserve all historical resources,
the unchanged caller and original-artifact/recovery checks. Only a compliant
pipeline-selected stable tag may seed `builds-version`; `ready` requires
verified AD-18 checks and publication by the maintainer. `nothing` or `disabled`
ends that invocation with no seed and no automatic redispatch.

This execution adds only sanitized evidence and story progress. It adds no
runtime/workflow-text tests. Verification parses all JSON, checks complete
inventory invariants and historical tag identities, compares read-only source
hashes, confirms the absent seed/unchanged gitlink and clean Builds checkout,
and runs `git diff --check`. [SHA-256 manifest](SHA256SUMS) binds the captured
evidence files.
