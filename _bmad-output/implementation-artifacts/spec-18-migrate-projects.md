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

- [ ] `evidence/18/` — refresh revisions and verify/provision AD-21 in order: App selection, stale analyses/drafts/orphans, rulesets, main-only environment, scoped Zot/NuGet, disabled scans, publish switch, retention and grants. Adopt only after pilot acceptance.
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

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines, including frozen ones; no other constraint changed.
- 2026-11-18 — Human chose how to clear the scanner refusal at `.github/actions/prepare-g6-catalog/prepare.py:47`: delete that legacy G-6 action in a module-agent Projects commit after adoption, before the first post-adoption nightly scan, instead of extending the scanner to prove the computed call. The legacy `ci.yml` uses it until adoption. Added this to the last execution task. The scanner stays fail-closed and no exclusion is added. No other constraint changed.
- 2026-11-19 — Human split the 2026-11-18 resume condition. The Projects product push waits only for a Conversations release with the five symbols; story 11 acceptance still gates adoption. No other constraint changed.

## Review Triage Log

## Verification

- `run-with-temp uv run --locked --script tools/render.py --check` — reproducible render.
- `run-with-temp uv run --locked --script tools/validate.py` — committed global/live-module verdict; authenticate privately using the intended profile.
- `run-with-temp python3 references/Hexalith.Builds/check.py` — successful normal post-adoption checker from a standalone Projects root.
- Run every preserved C# suite/product hook and the complete browser/persisted-state lane; verify exact App settings, artifact identities, tree preservation and actual scheduled-night results.
