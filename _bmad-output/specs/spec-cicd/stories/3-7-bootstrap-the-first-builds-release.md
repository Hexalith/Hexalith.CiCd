---
title: 'Bootstrap the first Builds release'
type: chore
created: '2026-11-12'
status: blocked
blocking_condition: intent gap
baseline_revision: 34ff3463ab49b53c7965745b3b293c2718035ec8
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 14bb22d9fb2124405ce23c22bd0d38ad55be7836
observed_remote_builds_revision: 9f5d751f7ab0b7a621dcd18b589bf061fabac6ec
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred: []
---

# Bootstrap the first Builds release

<intent-contract>

## Intent

**Problem:** Story 3-7 must establish the first AD-10-acceptable seed from the rewritten Builds pipeline and commit its exact tag as this repository's `builds-version`. The recorded external publications `v4.48.3` and `v5.0.0` are historical releases, both non-immutable at investigation time; neither qualifies as the seed. This story does not claim the historically first dispatch.

**Approach:** After re-arm, all AD-19 prerequisites and story 3-6's review requirements must pass before one subsequent interactive dispatch of the existing caller is authorized. Accept the exact stable version and initial major selected by the existing pipeline, without a version override or major-5 restriction. Preserve the preflight, maintainer publication of any `ready` draft, and verified version-seeding sequence below. A `nothing` or `disabled` outcome leaves `builds-version` absent and stops execution without automatic redispatch. This resolution session changes the spec only; it does not execute the release.

## Boundaries & Constraints

**Always:** Apply CAP-15 and AD-7/10/16/17/18/19. The authorized subsequent dispatch comes from an interactive CiCd session using the configured CiCd-agent profile, on Builds `main`, through `builds-release.yml`. Repeat every AD-19 precondition immediately before dispatch. Record exact full source revisions, correlated run identity, original artifact ID/digest, sole outcome, release identity and peeled tag. A `ready` outcome leaves publication to the maintainer by hand after AD-18's publish-ready checks. Commit `builds-version` in Hexalith.CiCd only after its tag is published, immutable, bot-authored and points to the built commit, an ancestor of Builds `main`.

Treat unreadable settings as unverified. Use command-local maintainer-profile overrides only for authorized administration, preserving the default profile. Maintainer remediation and proof must precede dispatch; this story's recheck is not authorization to delete resources, change policy or disable rulesets. Reconcile story 3-6's current review/tracking before production execution. Preserve its implementation and stories 3-1 through 3-5's authenticated-original-artifact and conservative recovery behavior.

**Never:** Dispatch or publish during planning or resolution; seed a mutable release or infer acceptability from a green run; move/delete a tag, reuse a published version with different content, rebuild an existing draft, weaken caller/producer checks, expose credentials, or edit frozen runtime/module files. No unattended dispatch or automatic redispatch, new scheduler, new release controller, version override, API-key fallback or artificial releasable commit. Preserve the two external publications as history; do not republish either to manufacture a seed. `nothing` and `disabled` do not supply a bootstrap tag. The agent does not publish a `ready` draft for the maintainer.

</intent-contract>

## Code Map

- `builds-version` — future CiCd-root output; currently absent from both disk and `git ls-tree HEAD`. Write one exact stable tag including `v`, UTF-8/LF with a final newline, after acceptance. The user's instruction establishes its destination and required commit; no existing value is assumed.
- `references/Hexalith.Builds/.github/workflows/builds-release.yml:1` — existing dispatch-only caller, no inputs, serialized `release` concurrency, shared Builds rules and `builds-ci.yml`. Publisher at line 26 owns `hexalith-release`; lines 49–50 consume `HEXALITH_REGISTRY_USERNAME/PASSWORD`. Read-only for this operational story.
- `references/Hexalith.Builds/Github/lib/release_state.py:207` (`select_release`), `:251` (CI check), `:307` (`resolve`) — marked draft versus create mode, exact switch, main-only dispatch and latest eligible exact-source push/manual CI. `release_version.py` already owns version selection; do not invent a bootstrap version.
- `references/Hexalith.Builds/Github/lib/release_outcome.py:29` (`validate_outcome`), `schemas/hexalith.release-outcome.v1.json` — validate the sole `hexalith-release-outcome/outcome.json`; `ready` carries `version`, `draftId`, `lastTag`. Workflow success alone is insufficient.
- `references/Hexalith.Builds/Github/lib/release_draft.py:50,237` — five trailers and original artifact metadata checks. `release_publish.py:69,83,105,146` — source/base ancestry, bot release identity/trailers, peeled tag, producer workflow/event/main/source identity. Reuse as read-only validation references; runtime phase commands also perform writes and are not a manual preflight command.
- `references/Hexalith.Builds/Github/publish/README.md`, `Github/lib/release_complete.py` — original-byte retries, tag-last publication and retained package-bearing draft on unavailable original artifact. No rebuild or package/image cleanup is part of bootstrap.
- `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md:280,444,512` — acceptable tag, publish-ready checks and AD-19 preconditions/bootstrap respectively. CiCd has no implemented `publish-ready`, `nightly.yml`, renderer or global-check command yet; execute the specified manual checks without depending on future stories.
- `_bmad-output/specs/spec-cicd/stories/3-6-rewrite-builds-release-yml-onto-the-shared-release.md` and `references/Hexalith.Builds/docs/cicd-3-6-builds-shared-release-results.md` — canonical status is `in-review`, seven execution boxes unchecked, despite physical implementation/results. Historical Auto Run Result says planning-ready and is not current completion evidence. Every other existing story is `done`; all thirteen stories' continuity sections were loaded.

## Tasks & Acceptance

**Execution, after re-arm and prerequisite remediation:**

- [ ] `_bmad-output/specs/spec-cicd/stories/3-7-bootstrap-the-first-builds-release.md` — apply the approved first-compliant-seed scope recorded in Spec Change Log, reconcile 3-6 review/completion evidence, and capture fresh local/remote baselines. Do not turn another session's publication into this invocation's dispatch claim.
- [ ] `_bmad-output/specs/spec-cicd/evidence/3-7/preflight.md` — create sanitized timestamped evidence for every precondition in Design Notes. Obtain maintainer disposition/proof for failing or unverified items; re-read the settings and complete paginated draft/tag/release inventory immediately before any dispatch. Any remaining failure stops execution without creating `builds-version`.
- [ ] `references/Hexalith.Builds/.github/workflows/builds-release.yml` and `_bmad-output/specs/spec-cicd/evidence/3-7/release.md` — after a freshly passing preflight, invoke the existing caller once, with no inputs, from the interactive CiCd session. Correlate the run against pre-dispatch inventory, time, path, event, branch and actual full head SHA. Record exact-source green CI and resulting jobs, authenticated original artifact and schema-valid sole outcome. The pipeline selects the exact version and initial major. Do not change the caller. Poll with bounded waits; inspect failures without automatic redispatch.
- [ ] `_bmad-output/specs/spec-cicd/evidence/3-7/publication.md` — for `published`, verify live release/tag; for successful `ready`, record all AD-18 checks and hand the exact draft to the maintainer. After the maintainer's publication, independently verify the resulting published immutable release and tag at the original built SHA. Retain the original `ready` outcome unchanged as historical evidence. Failed, missing, malformed, cancelled, disabled or nothing outcomes leave the version seed absent.
- [ ] `builds-version` and `_bmad-output/specs/spec-cicd/stories/3-7-bootstrap-the-first-builds-release.md` — only after final acceptance, write the exact accepted tag, record all publication/source identities and completed acceptance evidence, and commit the seed with its story/evidence in CiCd using a conventional `build(cicd)` message. Re-read the committed blob and independently resolve its tag. No Builds source commit or gitlink movement is required by an operational release; preserve the pinned submodule unless separately authorized. Do not fabricate rendering or delivery before those capabilities exist.

**Acceptance Criteria:**

- Given any unmet/unverified AD-19 prerequisite or unmet story 3-6 review requirement, when the operator assesses readiness, then no workflow is dispatched and no version seed is committed; the evidence identifies each exact stop without treating 403 as absence.
- Given this approved reconciliation and a freshly passing preflight, when the interactive CiCd session invokes Builds' caller on main, then one correlated actual Actions run uses the captured source and latest eligible green CI, the shared release rules/security/audit gates, and authenticated original artifact; no replacement build is introduced for retry.
- Given the historical mutable publications and a subsequent compliant release, when selecting the initial seed, then the historical publications remain preserved and the exact stable tag selected by the pipeline is accepted regardless of its major only after all AD-10 checks pass; no version override or republication of an earlier release is used.
- Given no releasable changes or a `nothing` or `disabled` outcome, when bootstrap execution stops, then `builds-version` remains absent, the evidence records the stop, and no artificial releasable commit or automatic redispatch is performed.
- Given a successful run with `ready`, when publish-ready's draft/source/base/artifact-digest/tag checks pass and the maintainer publishes by hand, then independent API readback confirms bot authorship, published immutable state and the final peeled tag at the original built SHA. A failed check leaves the draft unpublished by this agent and the seed absent.
- Given either verified direct publication or the verified maintainer handoff, when the CiCd seed commit is inspected, then its `builds-version` blob contains exactly that acceptable tag plus newline, with evidence linking run, outcome, original artifact, release and full source revision; `nothing`, `disabled` and mutable releases cannot pass.

## Spec Change Log

- 2026-11-12 interactive resolution: the maintainer selected "First compliant release; accept the pipeline-selected major (Recommended)". Story 3-7 establishes the first compliant seed after prerequisite remediation, with one subsequent interactive caller dispatch authorized after re-arm. Preserve the external publications as history, retain AD-10/AD-19 acceptance, and accept the pipeline-selected initial major without forcing a version. `nothing` and `disabled` leave the seed absent without automatic redispatch. This decision resolves the bootstrap intent gap; it does not establish that the operational prerequisites pass or authorize settings/resource changes. The original planning Auto Run Result below remains historical; the orchestrator owns re-arming the status.

## Review Triage Log

## Design Notes

Two investigation subagents completed read-only code/continuity and live-setting investigations. Snapshot time: **2026-11-12T10:32:25Z**. Remote Builds main had advanced beyond the clean local/pinned baseline during planning. External activity is evidence, not an action performed by this workflow.

| External shared-caller publication | Full built/tag commit | Run / release | Published UTC | Immutable |
| --- | --- | --- | --- | --- |
| `v4.48.3` | `1ecbcd6c6f61629086d019c37557d10d4247b0c3` | [43186506314](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43186506314), attempt 2 / `442699245` | `2026-11-12T09:13:04Z` | `false` |
| `v5.0.0` | `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec` | [43199661851](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43199661851), attempt 1 / `442792929` | `2026-11-12T10:31:01Z` | `false` |

Both runs are successful `workflow_dispatch` runs of `.github/workflows/builds-release.yml` on main; both bot-authored releases have matching `published` outcomes and matching tag commits. Exact-source push CI [43196500590](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43196500590) passed at the remote main above. The `v5.0.0` original `release` artifact is `13934373426`, digest `sha256:dd60825984323fe85d7d3441221da9a58ecc2f35295bb9525daf4f5fda4fd12a`, expiry `2027-02-10T10:21:39Z`; outcome artifact `13933909745` records that same source/version and `published`. Its trailers list `Hexalith.Builds.Evidence.Cli,Hexalith.Builds.Module.Cli` and no containers. Package publication does not prove the required registry credential configuration.

| AD-19 recheck | Current evidence / execution condition |
| --- | --- |
| Kill switch | Repository variable exactly `true`; `false` legitimately disables publication but cannot satisfy this story's seed acceptance. Any other value fails. |
| Immutable releases | **Fails:** repository API explicitly returns `enabled:false`, `enforced_by_owner:false`, including after `v5.0.0`. Both candidates above are explicitly non-immutable. |
| Retention | Pass: 90 days, maximum allowed 90. Recheck immediately before dispatch. |
| Environment | Pass: `hexalith-release`, exactly custom branch policy `main`, no reviewer or timer. |
| Environment push pair | **Fails:** only `HEXALITH_REGISTRY_PUSH_USERNAME/PASSWORD` exist; both local and current remote caller require `HEXALITH_REGISTRY_USERNAME/PASSWORD`. Maintainer must establish the required Builds-owned, registry-scoped pair; do not weaken the caller or expose values. |
| Org access | Builds has access to `HEXALITH_NUGET_USER` and both `HEXALITH_REGISTRY_PULL_USERNAME/PASSWORD`. Verify Actions/Dependabot selections and actual Builds-scoped push identity without reading/logging secret values. |
| App | `hexalith-cicd`, installation `179966090`, selected repositories and expected AD-7 permissions exist. Exact current selection including Builds remains unverified: latest available attestation is 2026-11-09; selection API access refused. |
| NuGet policy | **Unverified:** require maintainer evidence for `builds-release.yml`, environment `hexalith-release`, package scope `Hexalith.Builds*`, with legacy/probe policies reconciled. Successful publication does not prove exclusive/scoped policy configuration. |
| Rulesets | Active `19196298`: default-branch deletion/non-fast-forward only. Active `26812219`: `refs/tags/v*` update/deletion only, creation allowed; no bypass actors. |
| All `v*` tags published | **Fails:** 205 tags, 203 published releases. Orphans `v4.46.0` at `a8a87160f2708322d5520742b9a0c3f93d23db78` and `v4.47.1` at `75e1d4a3809b30684e67c7e9b2c8043720b49c53`. Maintainer disposition is required; no automatic deletion or ruleset disabling. |
| Draft/probe history | One retained qualification draft `441591623` was externally archived by changing its source marker to `hexalith-qualification-source:`. It is currently unmarked for production selection; do not retain the stale claim that it is a production marked-draft blocker. Its original artifact/package/image history remains protected; archival authorizes no deletion, publication or version reuse. Re-inventory before execution and verify probe policy/credential disposition. |

Authentication: default `/home/administrator/.config/gh-cicd-agent`, no `GH_TOKEN` or `GITHUB_TOKEN` overrides, account `jpiquot`, target `Hexalith/Hexalith.Builds`. The scoped switch read returned HTTP 403, `Resource not accessible by personal access token`, advertised `actions_variables=read`. Command-local `GH_CONFIG_DIR=/home/administrator/.config/gh` read-only administration verified the settings above without changing the default. The installation selection request returned HTTP 403 with CLI reporting missing `read:user`; `/repos/Hexalith/Hexalith.Builds/installation` returned HTTP 401 requiring App authentication. Neither failure proves installation absence; do not infer token permissions from account `admin:true` or automatically request broader credentials.

## Verification

All commands below are for later execution; the dispatch command was **not run** in this planning invocation.

- `GH_CONFIG_DIR=/home/administrator/.config/gh-cicd-agent gh workflow run builds-release.yml --repo Hexalith/Hexalith.Builds --ref main` — only after reconciliation and passing preflight; no inputs. A dispatch response does not identify its run reliably. Correlate using inventory/timestamp/path/event/main/source; concurrent runs must not be adopted accidentally.
- `gh run list --repo Hexalith/Hexalith.Builds --workflow builds-release.yml --branch main --event workflow_dispatch --limit 20 --json databaseId,headSha,status,conclusion,createdAt,url` — capture the dispatch inventory and correlate the actual run; use its numeric database ID for run metadata and artifact reads. Read `hexalith-release-outcome` through that run's artifact listing/download and validate with `validate_outcome`; authenticate the original artifact against its producer and digest.
- Read-only API surfaces: repository `actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED`, `immutable-releases`, `actions/permissions/artifact-and-log-retention`, `environments/hexalith-release` plus `deployment-branch-policies`/`secrets`, `actions/organization-secrets`, `actions/organization-variables`, rulesets `19196298`/`26812219`, all `git/matching-refs/tags/v`, and every `releases?per_page=100&page=N` page. Use intended-profile metadata reads; record inaccessible settings as unverified. Installed `gh api` has no `--slurp`; explicitly iterate release pages.
- For a `ready` handoff, inspect the outcome's exact `draftId`, unchanged bot-authored marked draft/trailers and captured `lastTag`; check original producer path/manual-main/source, unexpired original artifact and API digest equal to the trailer, source/base ancestry, and absent or matching peeled version tag. The maintainer publishes with `tag_name`, full `target_commitish`, `draft:false` in one request, omitting the workflow-tree-equality requirement as AD-18 specifies. Independently read back the published immutable release and exact peeled tag before accepting the seed.
- `git diff --check` and `git ls-tree HEAD builds-version` — before/after the eventual CiCd commit, verify whitespace and a tracked version file; inspect the committed blob against the verified exact tag. Planning-only validation checks the spec/frontmatter/full baselines/unchecked tasks and local diff. No runtime or workflow-text tests are added for this operational story.

## Bootstrap Reconciliation

**Original intent gap, resolved 2026-11-12:** External shared-caller publications had already happened, while both recorded results failed immutable-release acceptance. The original plan lacked authority for a subsequent dispatch and a rule for the initial seed's major.

**Approved decision:** Establish the first compliant seed using one subsequent interactive dispatch after all AD-19 prerequisites and story 3-6 review requirements pass. Accept the existing pipeline's exact stable version and initial major; preserve the historical releases and the immutable-release contract. If the pipeline yields `nothing` or `disabled`, stop with no seed and no automatic redispatch. Failed/unverified preconditions and story 3-6 review state remain execution gates, not an unresolved bootstrap-scope choice. The snapshot above is historical evidence and must be refreshed before execution.

## Auto Run Result

Status: blocked
Blocking condition: intent gap

Halted after planning as requested. Two investigation subagents completed and returned their results before the planning decision. The skill launcher ran exactly once and its rendered planning instructions were followed. Five execution tasks remain unchecked; no implementation, workflow dispatch, publication, administration/resource/credential mutation, version seed, gitlink movement or commit was performed by this invocation. The only workspace change is this story spec.

Self-review found actionable file-anchored tasks, dependency ordering, Given/When/Then acceptance criteria and checks at the actual Actions/release/tag/committed-file surfaces. The spec cannot meet the sufficient/coherent readiness criteria until the explicit bootstrap scope decision is resolved: the first rewritten release already happened externally, neither observed seed is immutable, and an additional dispatch/major selection is not determined by the original intent. Known AD-19 failures and unverified policy/installation evidence are recorded above, together with the current 3-6 review dependency. No repair to implementation detail can resolve that intent decision; the plan is not marked ready-for-dev.

Planning validation: parseable frontmatter; full canonical superproject and implementation baseline identifiers verified against Git; unique story-id path; all five tasks unchecked; no template comments or unfinished template markers; UTF-8/LF with final newline and no trailing whitespace. Runtime suites were not run for this planning-only operational artifact.
