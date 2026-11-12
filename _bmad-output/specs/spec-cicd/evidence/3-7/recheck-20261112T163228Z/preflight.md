# Builds bootstrap preflight — 2026-11-12

**PASS before one interactive dispatch.** This snapshot completed at 2026-11-12T16:45:24.674262Z.
Current authenticated manual readbacks and all AD-19 preconditions passed.
API setting reads used the command-local maintainer profile; the authorized caller
must use the default CiCd-agent profile. Inaccessible API surfaces remain recorded
as inaccessible; independent authenticated UI evidence satisfies the manual App
check without inferring additional token permissions.

| Identity | Value |
| --- | --- |
| CiCd parent-captured/current local HEAD | `44adaab81c554e405dd941615819f3ce38b6ca9a` |
| CiCd observed remote main | `44adaab81c554e405dd941615819f3ce38b6ca9a` |
| Builds clean pinned checkout and gitlink | `adfbf21896ef982ae9d1c3ee1db247e87bda22c0` |
| Builds current remote main / intended dispatch source | `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7` |
| Exact-source CI | [43237014144](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43237014144), success, all seven jobs green |
| App UI readback | 2026-11-12T16:44:29.6406232Z |
| Complete NuGet UI inventory | 2026-11-12T16:44:55.2291506Z |
| Expired legacy API key UI readback | 2026-11-12T16:45:06.4946163Z |

Earlier CiCd baselines remain separate historical identities in baselines.json.
Story 3-6 is done, all seven execution tasks checked, with unchanged canonical
story and review-completion hashes. Builds remote main has three external product
commits beyond the pin; reviewed caller/publisher references remain unchanged.
No checkout or gitlink is advanced for this operational release.

| Precondition | Current result |
| --- | --- |
| Exact kill switch | `true` |
| Immutable releases | Enabled |
| Artifact/log retention | 90 days |
| Environment | `hexalith-release`, custom branch `main`, no reviewers or timer |
| Registry secrets/account | Both required `HEXALITH_REGISTRY_USERNAME/PASSWORD` metadata records equal the dedicated account provisioning proof. Separate original authentication/zero-effective-ACL evidence is bound in baselines.json; current full ACL is unchanged. No fresh authentication claim is inferred from package publication. |
| Package-only scope | Dedicated `hexalith-builds-publish` has zero grants, including default/group/admin; a container-bearing authenticated original artifact stops bootstrap and needs an explicitly approved exact repository allowlist before another container release. |
| Required org access | Builds is selected for NuGet user variable and both pull secrets in Actions and Dependabot. |
| App | Installation `179966090` is active. Fresh authenticated manual UI selects exactly Builds/CiCd and shows the expected permissions. API 403/401 observations remain unverified API paths. |
| Other agent Apps | Complete org inventory excludes claude/cursor/semgrep-app. Complete connector pagination selects only EventStore and excludes Builds/CiCd. |
| Exclusive NuGet policy | Complete signed-in inventory has 17 unchanged approved cards: sole Builds policy `26029`, owner/repository `Hexalith` (`80614290`) / `Hexalith.Builds` (`952945989`), `builds-release.yml`, `hexalith-release`, `Hexalith.Builds*`, new packages/versions push only. Four obsolete policies remain absent; 16 other repository policies are preserved. |
| Legacy/probe disposition | Sole publisher key `Github Hexalith` remains expired. Complete legacy Actions secret selections exclude Builds/CiCd; Dependabot has no legacy families. No credential mapping is inferred. Qualification secrets/variables and exact read/create/update registry scope are retained. |
| Rulesets | Exactly the active default-branch deletion/force-push and v* tag update/deletion rulesets, tag creation allowed, no bypass actors; independent comparison equals approved repair proof. |
| Tags/releases | Complete pages 100/100/5, 204 published releases and one retained qualification draft; all 204 v* refs match independent Git inventory and have published releases. Both removed orphan refs return 404. |
| Qualification resources | Draft `441591623` body/trailers and original artifact `13850760915` identity/digest/producer/expiry unchanged. No production source marker; no fresh package/image byte authentication claimed. |
| Workflow/correlation | Existing dispatch-only input-free caller unchanged; pre-dispatch workflow-run inventory captured in settings.json. |

The external immutable `v5.0.1` release at the current source remains history,
not this invocation's dispatch or seed. A `nothing` or `disabled` outcome stops
with `builds-version` absent and no automatic redispatch. A `ready` outcome
requires all AD-18 checks and the maintainer's manual publication; this agent
cannot publish that draft. Only a published immutable bot-authored exact-source
tag ancestral to Builds main can be committed as the seed.

[Machine validation](preflight-validation.json) records 30 passing
checks. Authentication, complete inventory, current settings/selections, manual
UI readbacks, registry ACL and preservation evidence are retained alongside it.
The SHA-256 manifest binds the sanitized evidence. No credentials are included.
