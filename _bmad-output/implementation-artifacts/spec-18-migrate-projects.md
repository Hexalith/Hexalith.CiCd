---
title: '18 — Migrate Projects'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
baseline_commit: 'c74b5c8f5787fb33bfd85c1c4430b6de39674198'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/18/planning.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/18/design.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Projects runs legacy workflows, workflow-policy and historical evidence gates, and lacks Dependabot.

**Approach:** Migrate through AD-21 delivery, retaining genuine product coverage as shared stages or enabled custom actions; accept only green adopted CI and a successful nightly run (CAP-13) after adoption.

## Boundaries & Constraints

**Always:** Wait for the accepted story-11 pilot checkpoint before adoption. Use fresh main, module-agent for product pushes, CiCd-agent for CiCd/Builds, command-local maintainer for administration. Preserve concurrent work. Reuse Release/package outputs; keep all real browser, contract, package and persisted-state assertions. Require the normal Builds checker before module pushes unless a scoped preparation exception is explicitly approved. Use `run-with-temp` for disposable jobs and standalone module clones; initialize no nested submodules.

**Never:** Edit owned module portions, weaken audits/tests, add skips, remove mixed product tests by their story labels, broaden credentials after refusals, dispatch a substitute acceptance night, or revoke legacy access before authenticated adoption. Do not relax the source-only fixture's production safeguard.

**Human decisions (2026-11-16):** Include a distinct Release/package ephemeral browser-fixture path and its required generic Builds support in this migration, preserving all product checks. Approve the Projects-only pre-adoption substitute: released commitlint/audit checks, unchanged owned-tree proof, complete Release/package build/tests and retained product-hook qualification, with recorded source/results. This exception ends at adoption; the normal checker remains mandatory afterward and the exception covers no other module.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Verified prerequisites and qualified product hooks | One App delivery establishes rendered CI/release, Dependabot and perimeter; preserve foreign content. |
| Missing runtime support, refused API or changed main | Record the exact result; stop dependent adoption, refresh and revalidate. |
| Historical evidence/workflow assertion | Retire the gate; preserve separately identified product assertions. |
| No releasable change | Accept authenticated nothing-to-release; never force a version. |

</frozen-after-approval>

## Code Map

- `evidence/18/{planning,design}.md` under the main spec folder — exact observations and complete file/API design; no missing public EventStore API has been established.
- Projects `tests/e2e/`, existing source qualifiers and fixture hosts — reuse product assertions; keep source-only profiles unchanged. Verified Aspire prebuilt metadata suppresses child builds.
- Builds `Github/lib/{ci_config,ci_environment,ci_pipeline}.py` and CI schema — strict contract/preparation extension; published FrontComposer tool replaces source rebuilding.
- CiCd `tools/{render,validate,scan,scan_discovery}.py` — existing delivery and closed reachability model; extend scanner coverage honestly.

## Tasks & Acceptance

**Execution:**

- [x] `evidence/18/` — refresh revisions and verify/provision AD-21 in order: App selection, stale analyses/drafts/orphans, rulesets, main-only environment, scoped Zot/NuGet, disabled scans, publish switch, retention and grants. Adopt only after pilot acceptance.
- [ ] Projects `tests/Hexalith.Projects.PackageFixtures{,.AppHost}/`, `Hexalith.Projects.CI.slnx` — add nonpackable prebuilt fixture/driver; seed through authenticated product commands, verify independent durable state and complete browser phases. Test readiness/output/cleanup failures and production isolation.
- [ ] Folders `src/Hexalith.Folders.Server/{Hexalith.Folders.Server.csproj,FolderServerCatalogAdapterSource.cs}`, shared `src/Hexalith.Folders.EventStore/{FoldersCatalogAdapterSource,FoldersCatalogAdapters}.cs`, and `tests/Hexalith.Folders.Server.Tests/` — expose the actual owner's existing compiled command policies through the public SDK catalog seam from one module implementation; retain all Debug guards. Qualify exact declarations and all 36 retained canonical-intent cases, owner/server/gateway product suites and available required checks. Require the independently qualified corrected remote owner commit before delivered gitlinks or Projects adoption; this nonpackable executable repair needs no new Folder adapter NuGet package/version. Normal Folder checker/push prerequisites apply; no Folder push/publication is authorized by the Projects preparation exception.
- [ ] Projects `src/Hexalith.Projects.UI.Contracts/*.csproj`, `tests/tools/run-*-gate.ps1`, `scripts/`, `.config/dotnet-tools.json`, `.github/actions/{after-unit-tests,nightly}/action.yml`, `tests/e2e/package.json` — retain generator output, use inspector 6.0.0 and no-rebuild package checks; run browser driver nightly. Preserve C# suites, OpenAPI assertions and owning cross-module tests. Delete workflow assertions and tool-only root npm files.
- [ ] Builds `schemas/hexalith.ci.v1.json`, `Github/lib/{ci_config,ci_environment,ci_pipeline}.py`, CI/environment/prepare composites and configurations — add default `npmWorkspaces: []`, `dotnetTools: false`; prepare locked tools/npm/browsers once. Cover defaults, strict readers, unsafe/missing inputs and install failures in existing contract/environment/prepare suites; qualify an acceptable release.
- [ ] CiCd `tools/{scan,scan_discovery}.py`, `tools/jscpd/`, `.jscpd.json`, `tools/tests/`, `docs/duplicate-scan.md`, SPEC/spine — add static JS/TS/npm/import reachability and document additive contract; test complete scope and fail-closed indirection. Preserve thresholds and cross-module semantics.
- [ ] `setup/Hexalith.Projects.yml`, `rendered/`, `references/Hexalith.Projects`, `builds-version` — register the CI solution, four direct dependencies from the design, Dapr/browsers, tools/npm and two hooks. Commit prepared remote main plus cause/render together; fully validate before push.
- [ ] `evidence/18/` — authenticate accepted ref/report/App commit and tree preservation; immediately enable immutability and remove only Projects' legacy scopes. Before the first post-adoption nightly scan, delete `.github/actions/prepare-g6-catalog/` in a module-agent Projects commit that passes the normal checker (gate rule; no scanner exclusion). Verify normal checker, green CI and genuine next-night outcomes.

**Acceptance Criteria:**

- Given accepted pilots and verified prerequisites, when delivery adopts Projects, then rendered shared workflows replace legacy gates and add Dependabot without losing product coverage or foreign content.
- Given qualified package-mode hooks, when shared CI/checker run, then build/unit stages and enabled product checks succeed without repeated generic setup, source-mode substitution or workflow assertions.
- Given adopted green main, when a nightly run (CAP-13) after adoption finishes, then authentic successful release or nothing-to-release, scan and delivery outcomes establish CAP-16 completion.

## Implementation Notes

- 2026-11-17: Local implementation and reconciliation are recorded in
  [the implementation evidence](../specs/spec-cicd/evidence/18/implementation.md).
  The immutable combined six-module qualification restored successfully but
  failed its unchanged Release/package build with fourteen CS0234 errors:
  current Projects query declarations require `QueryResultContractAttribute`,
  absent from the selected published SDK. No dependent product tests, hooks or
  runtime phases ran, and the private workspace was removed. The exact source
  trees and command results are in
  [the qualification manifest](../specs/spec-cicd/evidence/18/matrix-reconciled-qualification.json).
- Scanner parent audit rejected an opaque Git regex shortcut. Computed operands
  now refuse until native value provenance is proved; the delivered G6 action
  remains unchanged and included. Historical green discovery from the rejected
  shortcut is not acceptance evidence. Full scanner results and the remaining
  candidate diagnostic are tracked in the implementation evidence.
  Full scanner suites passed 121 tests on both interpreters before the final
  narrow hardening; all eight affected groups passed on the final source on both.
  [Final verification](../specs/spec-cicd/evidence/18/matrix-final-verification.json)
  preserves those boundaries and the remaining candidate refusal.
- All tasks remain unchecked because each still has a qualification or adoption
  requirement outstanding. The normal published SDK prerequisite must be met
  before rerunning the complete combined product lane. The implementation step's
  repository/hosted-operation restriction also leaves AD-21 administration,
  authenticated adoption, required owner/release prerequisites, normal checker,
  adopted CI and the genuine next scheduled night unperformed. Status remains
  `in-progress`; no completion or CAP-16 acceptance is claimed.
- 2026-11-18: The public NuGet index now lists EventStore Contracts 5.3.0 and
  5.3.1. Their tags (`05e4f6d40d4731f7acf435f3c678959efc672269`,
  `3371f29fd7df1469a2c71f185292b2bd0592ae0e`) contain
  `src/Hexalith.EventStore.Contracts/Queries/QueryResultContractAttribute.cs`;
  v5.2.0 does not. Projects `Directory.Packages.props` still defaults
  `HexalithEventStoreVersion` to 5.1.1. Confirm the published package, then
  rerun the combined qualification on fresh inputs.
- 2026-11-18 (later): The published 5.3.x packages were confirmed. The unpushed
  Projects branch `story/18-eventstore-query-contracts` (`038f2f40`) adopts
  EventStore 5.3.1, Tenants 8.0.2 and explicit AppHost package references.
  Released v6.3.2 policy checks and the audited restore pass. The Release build
  now stops on five Conversations query symbols that are absent from the
  published 2.0.0 package. They come from unreleased Conversations main
  `f1a2b3da`, and today's Conversations releases failed. Story 11 is still
  unaccepted, the AD-21 state is unchanged and the G-6 action scanner refusal
  remains. Nothing was pushed, provisioned or adopted. See
  [the refresh evidence](../specs/spec-cicd/evidence/18/refresh-20261118.json).
- 2026-11-18: Parked by human decision. Resume with a fresh-input rerun once
  both hold: a published Conversations package contains the five symbols from
  `f1a2b3da468760d4188f604045deb098af8ead52`, and story 11 is accepted. Keep
  Projects branch `story/18-eventstore-query-contracts`
  (`038f2f4088415c6371b4ac0aad8cff7fd9438d62`) unpushed in its separate
  worktree until the Projects-only pre-adoption checks pass on it.
- 2026-11-19: Human decision: the Projects product push no longer waits for story 11. Story 11 still gates adoption, as the Always rule says.
  - **Trigger:** a published Conversations package contains the five symbols.
  - **Steps:**
    1. Rebase `038f2f40` onto freshly fetched Projects main.
    2. Select that Conversations version. The Builds catalog still defaults to 2.0.0, so set `HexalithConversationsVersion` as a dependency minimum until the catalog moves.
    3. Pass the Projects-only pre-adoption checks with exact inputs, then push with module-agent.
  - **Why:** the ChatBot latest-dependencies story needs a Projects main that builds in package mode.
  - **Conversations status:** its release is blocked because main CI is red. On `298eb57e8c3580e81d50bfc5fc7579cb6a0fa789`, the Windows prepare job fails in Builds v6.3.1 with "hosted Windows checkout requires the job token". The 2026-11-19 release reported "main is red, nothing released".
  - **Fix path:** Builds `73acaceb` and `a8e2ae292a45070e95646bf6db8a7f7a8704c1d3` fix it after v6.3.3. The fix reaches Conversations through the next Builds release, the nightly bump and delivery.
  - **Evidence:** [main readback](../specs/spec-cicd/evidence/19/latest-dependencies/main-readback-20261119.json).
- 2026-11-19 08:53 UTC: The [public NuGet index](https://api.nuget.org/v3-flatcontainer/hexalith.conversations.contracts/index.json)
  still ends at 2.0.0 (index SHA-256
  `43506685628fa6a300cbcd145fd5b36fb6a28abe0074652b403e094dc3d3cbea`). The published
  package SHA-256 is `bba5483dbaea023b08f66c163516cd142086eb93c2306d79979dbb9de10e74bd`.
  Assembly inspection confirmed that `GetConversationQuery` lacks `AdvisoryMetadataOnly`,
  `NativeMembershipOnly`, `QueryType` and `NativeMembershipPurpose`, and
  `ConversationDetailResult` lacks `ReadPurpose` (inspection output SHA-256
  `92ef06d85b9fea329684de6546ea6e5893ae9f8dee594e4ce60d0e851199439c`).
  Projects preparation remains at commit `038f2f4088415c6371b4ac0aad8cff7fd9438d62`,
  tree `c6b30c0eb626c2f7c0ad9c351ed6e381131372ec`, with a clean worktree. The
  package prerequisite still blocks the rebase, qualification and push. The
  [story 11 record](spec-11-pilot-migration-commons-and-polymorphicserializations.md)
  still shows `in-progress`, so adoption remains gated separately.
- 2026-11-19: [Local Folders owner qualification](../specs/spec-cicd/evidence/18/folder-owner-local-20261119.json)
  on cached main `4d371566dff0f1fc0ac1dbaf606a1eaf6c92c9fc` passed the audited
  Release build, both adapter controls covering 18 declarations and 36 canonical
  intent cases, all 124 gateway tests, and 1,451 Server tests. Eleven explicit
  Keycloak component cases and authenticated remote and hosted check evidence
  remain outstanding for the owner prerequisite.
- 2026-11-26: Resumed adoption for [CiCd issue #9](https://github.com/Hexalith/Hexalith.CiCd/issues/9).
  Story 11 passed in [nightly run 44566082537](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44566082537).
  Projects main `46568b4509d896372129b51f5c8719dfd493d3e8`, tree
  `5146e66b7499c362a94d09b0d2be094585b6885b`, passed its
  [legacy CI run](https://github.com/Hexalith/Hexalith.Projects/actions/runs/45838436409).
  Both product actions and their lockfiles are on main. The G-6 deterministic
  support and PostgreSQL replay assertions already run in their EventStore owner
  suites. The Projects catalog preparation action remains until delivery
  replaces the legacy caller.
- The maintainer readback confirms CiCd App installation `179966090` covers all
  repositories. Projects has no rulesets or `hexalith-release` environment.
  Default CodeQL and Dependabot security updates are off, push protection is
  enabled, retention is 90 days, and the publish switch is `true`. There are
  seven published releases, zero drafts, and 414 analyses from the legacy
  CodeQL caller. The sorted analysis ID list SHA-256 is
  `9678dca7adfac1851c38eb61bf67e785c7cf47fc567c2383bbd29d4194a4bd32`.
  Tag `v1.1.0` points to `66b7e1bd12eade0f43b464744d3ddc588d858f19`
  and is reachable from later release tags. GitHub returns 404 for its release,
  and nuget.org returns 404 for the corresponding five package IDs in its
  release manifest. The selected Actions and Dependabot pull grants and
  `HEXALITH_NUGET_USER` initially excluded Projects. NuGet Trusted Publishing
  required an interactive package-owner sign-in before policy readback.
- The approved cleanup removed all 414 legacy analyses and `v1.1.0` through
  the maintainer profile. The first six analysis deletions succeeded. GitHub
  returned no continuation URLs, so a verified remaining inventory was
  processed by ref in reverse creation order. The final 408-request ledger has
  SHA-256 `c5d55bb50a214206f9319b58c5fd0bda32cebaf5c6e46ee57f86692058004ee0`.
  Readback shows an empty CodeQL analysis inventory and HTTP 404 for the old
  tag ref and release.
- The maintainer created and verified `Protect main` ruleset `28175414` and
  `v tags` ruleset `28175416`, with their precise branch/tag conditions and
  empty bypass lists. Environment `hexalith-release` (`28663748343`) has the
  single `main` deployment branch policy `68387800`. The legacy `production`
  environment remains present under ID `22314003854` through cutover.
- The approved Zot restart at 16:06 UTC moved `distribution-registry` to
  generation 27 with one ready replica. ConfigMap `51624342` (configuration
  SHA-256 `ddfa2175a59b741ccd41facf2cc372d2a687ee4eb1486f51554d9be6fbe78527`)
  grants the Projects publisher read/create/update on `projects` and
  `projects/**`. Registry authentication returned HTTP 200 and a foreign
  repository read returned HTTP 403. The Projects release environment now
  contains the two scoped registry secret names. The deployed Zot binary
  verified the proposed configuration, and readback preserved all previous
  registry ACL entries and authentication rows.
- After the package-owner sign-in, NuGet created active policy `29361` for
  owner `Hexalith`, organization ID `80614290`, and Projects repository ID
  `871087402`. The policy permits new packages and versions matching
  `Hexalith.Projects*` through `release.yml` in `hexalith-release`. Reloaded
  readback confirmed the scoped policy and all 23 prior policies, including
  the `production` policy `20857`. Projected readback SHA-256
  `6e7caa73da12969da804be08618bd64ef2d5e7e162b46416a720ac2f554d1174`.
- The maintainer added Projects to the Actions and Dependabot registry pull
  grants and to the `HEXALITH_NUGET_USER` Actions variable. Each selected
  repository list grew from nine to ten and preserved every prior entry.
  Maintainer readback also confirmed default CodeQL off, Dependabot security
  updates off, 90-day retention, push protection enabled, `main`-only
  deployment and publish switch `true`. Receipt SHA-256
  `ea700f3080822e836fdeb25518228353f672afed67d91b28cdc7da6d4297347e`.
- The registration preview combines the original four direct checkouts and
  hooks with `aspire: true` for the Aspire 17 package fixture. The disposable
  CiCd tree `caa60de49dc62ed6ed739079ad9acc6429f41097` at Builds `v6.8.5`
  passed render and render check. All eight per-module validation checks passed.
  Global validation returned false after `tools/tests/test_scan.py` hit the
  existing 600-second suite limit (log SHA-256
  `c425089912436046635ce8401d56e7712937e46376b1ee3ee887d63ffc3016ec`). An
  isolated rerun of the committed scanner suite with a 1,800-second diagnostic
  deadline also timed out in the final `ScanTests` cases. The local PowerShell
  tool took 20.79 seconds for a simple startup probe. Diagnostic SHA-256
  `0a55329aa9e1636f6e3ecb5bb2c66f4f893d75cf019578bed587b800e8aa76b1`.
  The Folders pin `c00bad4d364dc25800cf9dc41220c1eba512fed9`
  has [failed hosted CI](https://github.com/Hexalith/Hexalith.Folders/actions/runs/45826937192).
  Folders successor `2791d7a82825238da15a1bfb77c544079a7f7d09` passed its
  [contract-spine run](https://github.com/Hexalith/Hexalith.Folders/actions/runs/45844093834)
  and [hosted CI](https://github.com/Hexalith/Hexalith.Folders/actions/runs/45844094422).
  The Projects fixture still needs qualification against the successor pin.
- The committed CiCd scanner selected 54 Projects files after the planned
  removal of the legacy G-6 action. It still refused the package hook's direct
  computed assembly invocation at `scripts/_consumer_packages.py:161`
  (scope and error digest `ac53ecdbe07f2607b9ef52da9f45c996620b70fccd91b692ace578fc66a27fc9`).
  A disposable probe launched the same prebuilt consumer using the SDK's
  `Run` target and the installed package manifest. It opened the manifest from
  a private path containing spaces and propagated the failure of an invalid
  manifest. The committed scanner then traced the same 54 files with no
  Projects diagnostics. The revised package tooling passed all 46 tests
  (SHA-256 `fa3b0ef7c7f275c23f9df52377312d40fe5c53e143b3c604ae40fd19f330b6db`).
  The retained hook ran all six API consumers, including the actual package
  extension's healthy readiness and wrong-major refusal (SHA-256
  `08973f749d7d2e790ca4fe6d259497b666ea52a63b66b9a407055f0171737a01`).
- The full audited Release build against the four-checkout projection and
  Folders `2791d7a8` passed. All eight suites ran and passed 3,315 cases. The
  standalone Server suite skipped one Dapr-gated restart control that the
  retained nightly compatibility phase explicitly exercises. Aggregate SHA-256
  `81498c28966bbac2ec00b0a640e8bdb98e1e437202f28f316744f6e57e412a78`.
  The real browser fixture initially enrolled `Folders.Server.dll` as both
  owner and adapter. It now uses the Folders Contracts and EventStoreExtensions
  assemblies from the selected executable's Release directory, which passes
  catalog construction. The actual Gateway at EventStore `df6a96ab` refuses 45
  command operation digests at activation because its `SubmitCommandResponse`
  includes `ResultPayloadOmissionReason`, absent from the published `5.6.0`
  Contracts used by the AppHost. All query and projection operation digests
  match (diagnostic SHA-256
  `4d45b865ebc619f7a78f60039d2de95a53038801963e0c942a6cc2c08e0f1980`).
  The disposable tree `914d27541e16f94a077b465bcd413b47f8df3b43` selects the
  released EventStore source `295b5a6ba584167f21cfef40787477b8814e32da` and
  Folders `2791d7a8`. Audited restore/build, all eight C# suites, FrontComposer
  inspection and all six package consumers passed. Six actual owners and
  workers committed the catalog. Duplicate delivery, full replay and the
  compatibility SDK host/store restart passed. The full browser hook failed
  the audit-storage ordinary-read control, the stale tenant-access assertion,
  Chromium creation read-model convergence, and the final actual-owner browser
  phase. The bounded output records an `InvalidOperationException` for the
  last phase. Full native log SHA-256
  `36b081ac91148cc6f8e6b45d246c7f8b6eb864a784d3fac0587bb5afd56c01e3`.
- Projects main advanced to `8faccc8d87f60abd47b1eed0b45b80418b6a0455`, tree
  `34962406848424e06095191f2332369a01d3d62b`, with a documentation-only commit
  recording the approved durable-task source-mode tuple at EventStore
  `df6a96ab`. The `5.6.0` Gateway alignment belongs to the disposable package
  rehearsal. The published SDK still ends at `5.6.0`. Adoption remains pending
  a compatible package-mode source selection and successful retained
  qualification.
- [Legacy CI for the new Projects main](https://github.com/Hexalith/Hexalith.Projects/actions/runs/45855546456)
  succeeded. A refreshed CiCd registration preview selecting that revision
  passed render check and authenticated `tools/validate.py --scope module` on
  preview commit `fa8ebd2fc3398a704603fcfd92837436c048fba7`, tree
  `3ac566088b9cf0ad5cb2271345fa4f4b65387982`. All eight module checks and the
  online audits for 25 workflows passed. The scoped run excludes the full
  scanner test suite. Validation SHA-256
  `ff83b256f90ec8e88e16d752252b18a630158c84a5ffc11ec7e5833471a0cff4`.

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines, including frozen ones; no other constraint changed.
- 2026-11-18 — Human chose how to clear the scanner refusal at `.github/actions/prepare-g6-catalog/prepare.py:47`: delete that legacy G-6 action in a module-agent Projects commit after adoption, before the first post-adoption nightly scan, instead of extending the scanner to prove the computed call. The legacy `ci.yml` uses it until adoption. Added this to the last execution task. The scanner stays fail-closed and no exclusion is added. No other constraint changed.
- 2026-11-19 — Human split the 2026-11-18 resume condition. The Projects product push waits only for a Conversations release with the five symbols; story 11 acceptance still gates adoption. No other constraint changed.
- 2026-11-26 — The user approved resuming this adoption alongside the package release and V2 qualification required by CiCd issue #9. Existing acceptance conditions apply.
- 2026-11-26 — The user approved removing the 414 identified legacy CodeQL analyses and the orphan Projects tag `v1.1.0` after the GitHub and NuGet release checks.
- 2026-11-26 — The user approved the shared Zot restart to establish the Projects-specific publishing scope. The rollout targets the existing deployment and the `projects` and `projects/**` policies.

## Review Triage Log

## Verification

- `run-with-temp uv run --locked --script tools/render.py --check` — reproducible render.
- `run-with-temp uv run --locked --script tools/validate.py` — committed global/live-module verdict; authenticate privately using the intended profile.
- `run-with-temp python3 references/Hexalith.Builds/check.py` — successful normal post-adoption checker from a standalone Projects root.
- Run every preserved C# suite/product hook and the complete browser/persisted-state lane; verify exact App settings, artifact identities, tree preservation and actual scheduled-night results.
