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
- [x] Builds `schemas/hexalith.ci.v1.json`, `Github/lib/{ci_config,ci_environment,ci_pipeline}.py`, CI/environment/prepare composites and configurations — add default `npmWorkspaces: []`, `dotnetTools: false`; prepare locked tools/npm/browsers once. Cover defaults, strict readers, unsafe/missing inputs and install failures in existing contract/environment/prepare suites; qualify an acceptable release.
- [x] CiCd `tools/{scan,scan_discovery}.py`, `tools/jscpd/`, `.jscpd.json`, `tools/tests/`, `docs/duplicate-scan.md`, SPEC/spine — add static JS/TS/npm/import reachability and document additive contract; test complete scope and fail-closed indirection. Preserve thresholds and cross-module semantics.
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

- The local Projects Story 5.21 worktree had been removed. Recovered its
  29-path backup patch (SHA-256
  `b0693fa0d06f64ae8bd7f0f2e613d4d77c075b17212de64d1344d1184cc86cc9`)
  with a clean three-way apply on freshly fetched Projects main
  `84e29c39460511e34b022b6b5cac1c19e70538e6`, tree
  `8bd46b5b5d83b61d1aa5359b933e7ae068a7af03`. One overlapping Folders
  test change was already on main. The recovered candidate tree was
  `0548e7b7aeecf55a44dce5e4c0f486a7494a9b13`.
- The isolated audit reproduction selected EventStore Gateway v5.6.0
  `295b5a6ba584167f21cfef40787477b8814e32da`, tree
  `32c0e679697bcaaea104e21477b3aec6555b9a73`, with published Contracts,
  DomainService and Aspire 5.6.0. The Contracts archive names the same commit
  and has SHA-256
  `e08f653c0b1ec0b10f283969c8acaf5ab5d4dbf094cfcdb6a033133a1bf660a5`.
  Other checkouts were Builds `deccbc3bcf4ed687ecf4d556ebe356fe57148777`,
  Tenants `d34f353abb59213ac021e81da6885b78ee3231fd`, Folders
  `2791d7a82825238da15a1bfb77c544079a7f7d09` and Platform
  `80a60039b46ea6bdccd9eeac5091551bc59643fa`. Their trees in that order were
  `0285a6dfb4360675021418da2033ffcaf3b4cdf0`,
  `1679d29778073c9527aedccdc919dc18cdc20315`,
  `772b58e3cb751fab352c5b8c4aa6f64b7cbf49a5`, and
  `4b4d0838ccc1bd62fdf71dd7e7ee159d819cdbf5`. Audited restore passed
  (SHA-256 `33b75ca14a8cc6ea9f6f6915d9fe20c32465d0c3a19e5e3193d4abe99302560a`).
  Release build passed with zero warnings and errors (SHA-256
  `f238f55f774289e26a7cc999fd855ff0f54b06e77b9a5c8bc09804f13b349fc0`).
- Five native controls passed through audited inspection. The ordinary-list
  assertion in `WaitForNonDescriptiveControlAsync` failed first with “The
  active audit fault did not recover a Complete non-descriptive control within
  its budget.”
  Attempts 1 and 15 returned HTTP 404, with response SHA-256 values
  `2ca48a99ed739d6e27fcad69dc7420489f8d54729cb3bd2cec8dc114b02fc592` and
  `5c86cb761b0b4dbe0e4e78b64d9a27d95392edf27e9ebf7e182d5be462c3f712`.
  The owned Redis ACL had 82 allowed key patterns and its bounded log showed
  five denial groups, all on new audit keys. The persisted tenant projection
  was enabled at version 2 with one principal and was 358.8 seconds old
  during the fault. Supported reads require current evidence within the
  300-second freshness budget. The native driver exited 1 (runtime SHA-256
  `583a072231296407864f6138c6459b895299d8fdb112025e6a1f3f87b95c99a1`).
  The package AppHost now budgets one hour for ordinary fixture phases, which
  have a 45-minute lifetime, and retains 90 seconds for the stale-access proof.
  The audit ACL and ordinary-read assertions are unchanged.
- The full driver on candidate tree `ec6ffb862f7a607644c9e79ebe0a820c5669efa1`
  passed the audit-storage row. Both ordinary list and open returned Complete
  HTTP 200 on the first attempt before the inspected refusals, and authorized
  recovery returned HTTP 200 after restoration. The row result SHA-256 is
  `df64987fc6e88ac4b179e332958b7980a00195dd5ae2e818792041fa0268b09a`.
  The next persisted-state row reached a Complete retained cursor before the
  real `RevokeFolderAccess` command returned HTTP 500 (response SHA-256
  `82dfd5e55a2e35dba8e464059c03f69f78f3bcdd877eedf90b7a4361a66a9aed`).
  Duplicate delivery passed. Full replay reached the rebuilt read-truth
  comparison and a positive open returned HTTP 404. The unchanged 90-second
  recovery configuration also exposed a seed-time HTTP 500 on `SetProjectFolder`
  in the full run (response SHA-256
  `3a26c10ee955c1120cf8a19c6454fe48541964ec751b25e7aaf95c62f0f695e7`).
  The follow-up gives the disposable Folders host the same one-hour freshness
  window and retains the Projects recovery deadline.
  The full driver ran all six named phases and exited 1 (runtime SHA-256
  `5204b3f3d0a54863e0f8b31e3f0f63cb07de203c1bae310a9def0d04cb1d728e`).
- The recovery fixture now uses the retained v1 read's required
  `inspectDescriptiveMetadata=true` opt-in with its existing scoped OIDC
  credential. The Chromium name-only lifecycle test checks the persisted Active
  result through authorized quarantine inspection, checks Pending Folder and
  ordinary-read refusal, and still requires the ordinary Archived read after
  archive. Cleanup can observe the same quarantined project before archiving.
- The package build of candidate tree `a25acecc015da85712deb02427a21ee7dbaecde3`
  passed with zero warnings and errors (SHA-256
  `1eceaf57036373ec0ac65a4ee48f8c0aab5dab9fa59e085925c64211fbc5fab3`).
  Eight C# suites recorded 3,315 passes, zero failures, and one skipped Dapr-gated
  restart case (SHA-256
  `574420733d24e8f511c5d55a7dec6059b83f5846f8d6fa689c30d303e56aa150`).
  That case passed separately in the live compatibility fixture. All 46 package
  tooling tests passed (SHA-256
  `b403e4ab476ab612dfe6d48965133ad2b3c1aa3b6369d4cf8095af6c84684d63`).
  FrontComposer 6.0.1 inspection passed (SHA-256
  `a20b6d929d735029327274d9e4169a44c971fdde73fa024983dc397eabebe661`), as did
  all six isolated consumers (SHA-256
  `202ea75a70c9f6034608a59a445247d62e85dfe811482f12674f274afc79db27`).
  TypeScript caught the local helper's missing `references` type before the
  driver could start. With the existing reference summary type added, the
  locked `tsc --noEmit` passed (SHA-256
  `7c9d1fd4106c42b1dc2d3fe817493910eb1bf28e39e82213b1901e2a440861e9`).
- The initial Chromium smoke collected eight tests and passed seven with zero
  skips. `renders protected Project data through server-side token relay only`
  failed during seed convergence after HTTP 202. Shared active-project seeds
  now wait for the quarantined projection, bind the owned sibling Folder
  through the supported command, and wait for the ordinary active read.
- The diagnostic run on tree `9e2ca21271f72adddd4b6e045ff5fa950a98e60f`
  passed the complete stale-access recovery phase. Pre-recovery HTTP 404 was
  observed at 104.4 seconds against the unchanged projection and the configured
  90-second budget. The same scoped token, both independent refresh writes,
  unchanged membership and roles, and source/projection watermarks passed.
  The four-line result SHA-256 is
  `6523cbd7ac69a37f6287d7edd8399dc69a498117cbc939efec0e1e78062d8054`.
- A follow-up recovery diagnostic on tree `b116721a08f0eaacd6effdeabd3f03d803f236d8`
  reached the stale denial at 90.0 seconds against the unchanged projection
  and then failed a recovery assertion. A follow-up with only Tenant membership
  and no initialized Project list returned an unexpected status before staleness
  on tree `2b4ea8f4a6ee92426a2ed8b2c40de2dd3b0a9f5d` (runtime SHA-256
  `e92b89381e3570e7d3872cc314df2c00091499de70aab7252cf6fb15df4e306f`).
  The recovery seed includes both genuine Tenant memberships and one bound
  primary Project to initialize the list. It keeps the existing status and
  persisted-authority assertions. The exact list contents, ordinary open and
  replay assertions run in their respective phases.
- The same diagnostic tree passed all nine native main controls with zero
  skips after the Folders fixture received the ordinary freshness window.
  This includes the audit-storage fault, the real Folder revocation and old
  cursor refusal, the Folder outage, and authenticated projection compatibility.
  The ten main case and scenario result lines have SHA-256
  `a966060fdd6b8d67ac0d75b224bb5acabcc205ebf4066812bb5a82c4df3ea920`.
  Full replay also passed with zero skips, including both tenants' rebuilt
  list/open truth and the invalidated pre-rebuild cursor. The two passes and
  the recovery retry's assertion failure are in the same diagnostic runtime
  SHA-256 `b115f94a09c950870ff5f758af729884d671f701c35661cbafd292c15bd63205`.
  Audited restore and Release build SHA-256 were
  `5ba34d83fc0521868bd5c244b000906451eec1e5821dc4bd64eb16410ab470b0` and
  `cb6147efa857a4b2681ee3fd4cbf9a65cc99ed3b04b75aece21f327d88303a6c`.
- The browser-fix candidate tree before the separate package checkout was
  `a93fe8c3b9e641c271acd4375599f6704e77c1d3` on the same refreshed Projects main.
  Audited restore SHA-256 is
  `a36ce3fbdceb6f08f32fdf6b9bbe110d9f77a735159c1bb0c1294357d5d2147b`.
  Release build passed with zero warnings and errors (SHA-256
  `a171030ceb573cf51c079f93f57534aaa65a6052ef4a082bfdaa15b1edcdc701`).
  The live stale-access diagnostic passed 1/1 with zero skips. The unchanged
  OIDC token progressed from HTTP 404 at a projection age of 90.67 seconds
  against the 90-second limit to HTTP 200. Eight retries produced one refresh
  and a distinct operation produced the second refresh. The persisted source,
  projection and snapshot watermarks all reached 5. The runtime and the two
  receipts generated inside that run's private fixture have SHA-256 values
  `8f652f4c759b99482f98bb1344bd65a582608aabf37bddc61d20b4a5e37f4f6a`,
  `379d8e29e538d3d45eb004c4e47a8002f3bb55622453fd584b7aee1298a79535`
  (observations) and
  `0d113515b61782bcd7b41d408261ab7c8bcea29e0db6a65dfd5c7a3cfb41219c`
  (result). An earlier receipt read from a tracked historical file is excluded
  from these run results.
- On browser candidate tree `ec6ffb862f7a607644c9e79ebe0a820c5669efa1`, the
  Chromium minimal-create control passed with zero skips, including Pending,
  ordinary refusal and Archived convergence (SHA-256
  `38900a2d6a51c02a44949b754f352ea5a4d45f975d44771f58a2bba1309f9912`). The
  compatibility smoke again passed seven of eight. Its seeded Project now
  converges and is archived successfully. The actual browser then shows
  `Project reads are unavailable` at `/projects/{id}` and cannot find
  `project-detail-name` (browser observation SHA-256
  `d90299b6e7c626ac8a19205a1e534ad9708641ee4b017cd335cbb5ace29361d3`).
  Compatibility exercises the retained UI, whose `LegacyRollback` selection
  requires exact-source Story 6.7 v4 evidence for all seven retained routes,
  verified native receipts and Projects maintainer/Test Architect acceptance.
  The previous local acceptance candidate was based on Projects `928f66f5`
  and its owner acceptance is pending. The product selector remains guarded.
  A diagnostic driver ran each compatibility browser phase after smoke failure.
  Full Chromium collected 146 cases, with 102 passes, 44 failures and zero
  skips. Repeat passed 14/14 and the expected-failure retry control passed 2/2
  with zero skips. Runtime SHA-256
  `d899c5c022e28d7beaac96e8ad2ba6f133bd436d08ece34e6839d7b5e2f9d62d`.
- The retained File Reference tests now opt in to descriptive inspection. The
  no-Folder-replacement case uses its own Pending Project and explicit
  quarantine view, preserving the before/after Folder assertion. All five
  Chromium File Reference tests passed with zero skips on tree
  `c39f49d551e01c6e8e24a3575105471fd47a0730` (runtime SHA-256
  `8f6c7167317e332d880488fa9b19d5fe3a467bd9975d2eb9dc52ed1d1ea02b2e`).
- The actual-owner browser control timed out at advisory seed readiness. Ten
  sampled real responses were HTTP 200 with incomplete observations and zero
  candidates, while the independent Project index, both details, both linked
  Folders and owner projections were present. A representative timing sample
  ranged from 3.79 to 4.07 seconds alongside a 168-second Tenant projection
  age, inside the existing 300-second Folder budget. Partial diagnostic
  observations SHA-256
  `30d4cde45c85d37b0ff46a3f80abcd480ee3ee2d9869971a9004c3fd091f3ff8`.
  A disposable trace of the aligned Gateway/SDK showed Accepted Folder owner
  calls taking 1,050–1,372 ms, followed by `TaskCanceledException` in the
  advisory executor. Two serial observations already exceed the unchanged
  two-second dependency budget. The instrumented runtime SHA-256 is
  `a84a385e37eb47a2ddb40460aa16c9913eacf6f3121b9b7a56b4df9f504bc326`.
  The complete positive advisory assertion still requires a transport that
  fits the existing budget with the initial and final owner checks intact.
  The above timing used the installed Dapr 1.19.1 sidecar. The diagnostic
  configured for the hosted Builds pin, 1.19.2, stopped at the bootstrap
  authority check before it could measure advisory (runtime SHA-256
  `696f7eec414c81f3db206c06bc16f493e588adbe069336e19581e3176b6a20e3`).
- The user approved a separate package-mode Gateway checkout pinned to
  EventStore v5.6.0 `295b5a6ba584167f21cfef40787477b8814e32da` and the published
  SDK 5.6.0. The source-mode gitlink remains
  `df6a96ab2a5bae24fe5951eee5429bda223cc675`. The source-mode Gateway's command
  contract uses `SubmitCommandResponse.ResultPayloadOmissionReason` from
  `360ed041d530d22f5c1f0fc8cd6bd9e8f3964a58`, which is absent from the public SDK
  5.6.0 (Contracts index SHA-256
  `628abeccc17a67457b6721471ecfec1bc141c39d463780a326696c4d7b3030c7`).
  The approval covers the source selection. The browser acceptance gates still
  apply before CiCd registration and Projects V2 publication.
- The Projects candidate uses a distinct direct gitlink at
  `references/Hexalith.EventStore.PackageMode` for the approved release. The
  public v5.6.0 tag and the initialized checkout both resolved to the approved
  commit. Both AppHosts resolved the new checkout in Release and the existing
  gitlink in Debug source mode. With the package checkout withheld, Release
  resolved no EventStore root. Mapping results SHA-256
  `bea3934035d1ffa74620e65077227a29a1b42b4a7940c82cb5c7efd5f8e85e7a`.
  Projects base `84e29c39460511e34b022b6b5cac1c19e70538e6`, candidate tree
  `4b6269ecebd4b3711f58a92f85a6bfb1aa47e3c6`. Audited Release restore passed
  (SHA-256 `ee5e4e6e0f0d21be3e12db2e6e31bc42275aaef902c2a2650ba6d9dd57ff70eb`).
  The restore assets confirm published EventStore Aspire and Contracts 5.6.0
  (SHA-256 `995823d106791ae2460475c77cf895a82f1722962d2b0b39b63fda34ad189a84`).
  The first live run found a fixed source-checkout path in the writer-protocol
  setup and stopped with `FileNotFoundException` (runtime SHA-256
  `110a271c7775c891fb5c7590aee63055b3800ad40bf09eaf1e941bdf7dfc3dcb`). The
  fixture now reads the Server assembly's source commit from the prebuilt
  output directory of the Gateway resource it actually starts.
  Candidate tree `375403ea5e74a5e915b764039b2e86aa54a784c6` passed audited
  Release restore and build with zero warnings and errors (SHA-256
  `c0e8f344a74249b75a31e124c0fef0110dba62e0f409355dc6b1e1da6dc5b5a1` and
  `b9fc5c45ca276c913370ee37e01b378025988ee5d6c52af348d3e680f03cd6f6`).
  The focused live recovery passed 1/1 with zero skips. The running Gateway's
  prebuilt Server assembly reported the approved `295b5a6b` source and the
  intended stale HTTP 404 occurred at 90.1 seconds. The complete recovery
  assertions passed (runtime SHA-256
  `35a1a9f74f75e266ebaed9941aaf4b4946fd46f67a65864a04a3c82ae91be93d`).
  Projects main advanced during the run to `ce6fff0b8d27347eef989643c8ec4b64961e1976`,
  tree `e3624bef60933897c009f05b60cd8da3f20a4260`, with a Story 7.1
  documentation change. The local candidate was carried forward byte-for-byte
  to that base. Its tree is `77f2628aa9f6c66607be06e41e92bdda7c2ba1ff` and its
  patch SHA-256 is `1de84eaa222f34a58f260f69d8cea20be452e69ad3e2c6c45ee9e1e7a7cb518b`.
  The run results above refer to the tested tree before the documentation update.
  The eventual CiCd setup will select this explicit package-mode gitlink for
  the dependency checkout after qualification.

### Local qualification on Projects `2067b57d`

- The detached `projects-story-18-candidate` worktree holds staged tree
  `6b5066ae7b1b6eaf267a6d22476b1d59362c83fd` on cached main
  `2067b57d8c72af9f83a404eefd80d33033d51268`. The recovered package-mode and
  Projects V2 changes were carried forward together for qualification. The
  existing Story 5.21 worktree was preserved. Package-mode checkouts used the
  following exact commits and trees.

  | Checkout | Commit | Tree |
  | --- | --- | --- |
  | Builds v6.8.5 | `deccbc3bcf4ed687ecf4d556ebe356fe57148777` | `0285a6dfb4360675021418da2033ffcaf3b4cdf0` |
  | EventStore.PackageMode v5.6.0 | `295b5a6ba584167f21cfef40787477b8814e32da` | `32c0e679697bcaaea104e21477b3aec6555b9a73` |
  | Tenants | `d34f353abb59213ac021e81da6885b78ee3231fd` | `1679d29778073c9527aedccdc919dc18cdc20315` |
  | Folders | `2791d7a82825238da15a1bfb77c544079a7f7d09` | `772b58e3cb751fab352c5b8c4aa6f64b7cbf49a5` |
  | Platform | `80a60039b46ea6bdccd9eeac5091551bc59643fa` | `4b4d0838ccc1bd62fdf71dd7e7ee159d819cdbf5` |

- Restore passed with NuGet audit enabled and the released trust configuration
  (`6de945a18de26a7509d0b293b4eb1bd5f65896d2d42e2fcdacb6bb1aa8adafc1`).
  The Release build passed without warnings or errors
  (`8591aa7e93743e4ac76402f5fa3ad2116e918ba9ffd6bc4b25885a65f2563441`).
  Eight C# suites recorded 3,315 passes, zero failures and one Dapr-gated skip
  (`a9f9d726990c9b0d5e20ea794ccd0374a49f45875a5e1cc09858421c2820dc2c`).
  That restart check passed in the live compatibility fixture. All 46 package
  tooling tests and all six isolated consumers passed (consumer SHA-256
  `2fb5abc51b47174cc91e0c86a4442d740a3b3b62c27faf657fecc90bbb1cb38f`).
  FrontComposer 6.0.1 inspection passed
  (`a20b6d929d735029327274d9e4169a44c971fdde73fa024983dc397eabebe661`).
  Locked npm install, signature verification and TypeScript checking passed.
- The browser driver on Dapr 1.19.1 passed the native main, duplicate-delivery,
  full-replay and tenant-access recovery phases without skips. Compatibility
  smoke passed seven of eight. The actual protected detail route remained
  unavailable because the package AppHost has no `Projects:Reads` selection
  and the local record has no Story 6.7 v4 acceptance for this source. The
  selector requires seven validated security slices and hash-bound native
  receipts for `LegacyRollback`. Full compatibility Chromium, repeat and retry
  phases were not reached. The separate actual-owner phase stopped before
  Chromium in `PackageReadAdvisoryReadiness.WaitAsync`. Projects `DW-80`
  records the owner-path performance work required to fit the existing deadline
  with all authorization observations intact. The driver exited 1 (SHA-256
  `5fd78548be715e1b72905e5d1e4bf5b4bd678167a5c040a3fa8e2c6211d5350e`).
  Hosted Dapr 1.19.2 parity remains open.
- Builds v6.8.5 passed 22 focused contract, environment, pipeline and Linux
  prepare tests (SHA-256
  `1281a208b3446f366cd2d49b7589a36a739e2765fd6ff2b7f26e5acbb0aab697`).
  Four npm and JavaScript reachability tests passed on CiCd
  `b74d2e80b46896a51f72c32387b45163954afb1f` (SHA-256
  `0256e7c2df542f507c389696f3bbe8853706cf6df6f014480b8b503d87771bdb`).
  The post-adoption scanner rehearsal selected 54 Projects sources without
  diagnostics after removing the legacy G-6 action in a private index.
  Full global validation remains pending.
- The [registration preview](../specs/spec-cicd/evidence/18/setup-candidate.yml)
  selects the explicit package-mode checkout and passed render reproducibility
  (rendered CI configuration SHA-256
  `d15f3a39c071dde7e342d1ac37313df149fa1dd8d3a306f6c3244baca5ceb103`).
  Projects still needs complete browser qualification before active registration,
  App delivery and post-adoption CI/nightly acceptance.

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines, including frozen ones; no other constraint changed.
- 2026-11-18 — Human chose how to clear the scanner refusal at `.github/actions/prepare-g6-catalog/prepare.py:47`: delete that legacy G-6 action in a module-agent Projects commit after adoption, before the first post-adoption nightly scan, instead of extending the scanner to prove the computed call. The legacy `ci.yml` uses it until adoption. Added this to the last execution task. The scanner stays fail-closed and no exclusion is added. No other constraint changed.
- 2026-11-19 — Human split the 2026-11-18 resume condition. The Projects product push waits only for a Conversations release with the five symbols; story 11 acceptance still gates adoption. No other constraint changed.
- 2026-11-26 — The user approved resuming this adoption alongside the package release and V2 qualification required by CiCd issue #9. Existing acceptance conditions apply.
- 2026-11-26 — The user approved removing the 414 identified legacy CodeQL analyses and the orphan Projects tag `v1.1.0` after the GitHub and NuGet release checks.
- 2026-11-26 — The user approved the shared Zot restart to establish the Projects-specific publishing scope. The rollout targets the existing deployment and the `projects` and `projects/**` policies.
- 2026-11-26 — The user approved the separate v5.6.0 Gateway pin for package mode and retained the existing EventStore source-mode pin.

## Review Triage Log

## Verification

- `run-with-temp uv run --locked --script tools/render.py --check` — reproducible render.
- `run-with-temp uv run --locked --script tools/validate.py` — committed global/live-module verdict; authenticate privately using the intended profile.
- `run-with-temp python3 references/Hexalith.Builds/check.py` — successful normal post-adoption checker from a standalone Projects root.
- Run every preserved C# suite/product hook and the complete browser/persisted-state lane; verify exact App settings, artifact identities, tree preservation and actual scheduled-night results.
