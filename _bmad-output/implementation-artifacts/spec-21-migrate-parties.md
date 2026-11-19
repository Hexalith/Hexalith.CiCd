---
title: '21: Migrate Parties'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
route: 'dispatch'
baseline_commit: '94b335c7483ba8fe76ad44de46ee3512017c9a11'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Parties uses domain-ci v2 and obsolete CI-owner, startup and story gates mixed with real product qualification.

**Approach:** Follow AD-21 preparation, registration/render and App adoption. Preserve product coverage and three container identities; completion requires green shared CI and the next central nightly outcome.

## Boundaries & Constraints

**Always:** Module-agent for product writes; CiCd-agent for CiCd/Builds; command-local maintainer for administration. Preserve SDK 11.0.100, package-mode libraries, runtime cleanup and foreign content. Complete maintainer prerequisites and respect pilot acceptance/migration order before adoption.

**Never:** Directly edit Parties' owned perimeter, initialize nested submodules, weaken tests/audits/provenance, add skip markers, switch credentials after refusals, or revoke legacy publishing before adoption. Require the normal checker after adoption.

**Human decisions, 2026-11-16:**

- Approve a Parties-only pre-adoption checker substitute: fresh-main standalone source, package-mode build and retained product tests, released guard audit/action lint, pinned exact-message commitlint and byte/mode/gitlink proof that owned portions are unchanged. Record successful exact-input evidence for every preparation push. This exception ends at App adoption.
- Allow explicitly declared, gitlink-pinned runtime executable/composition source dependencies, including required helpers, while ordinary library dependencies remain packages. Preserve all native scenarios; this is no general source-build permission.
- Preserve publisher-time provenance. Ship generic frozen-created support separately in Builds, as recorded in `prerequisite-21-frozen-release-timestamp.md`; block adoption until it is verified, released and available through the selected Builds pin.

## I/O & Edge-Case Matrix

| State | Behavior |
| --- | --- |
| Preconditions and qualification pass | Register/render; authenticate App adoption |
| Missing prerequisite or refused read | Block dependent work; distinguish absence from unverified access |
| Mixed CI/product test | Remove CI assertions; preserve product behavior |
| No releasable change | Accept authenticated nightly “nothing to release” |

</frozen-after-approval>

## Code Map

- Current preparation and exact-input verification: [implementation handoff](../specs/spec-cicd/evidence/21/implementation-handoff.md), [accepted local verification](../specs/spec-cicd/evidence/21/accepted-local-verification.json), and [dispositions](../specs/spec-cicd/evidence/21/preparation-dispositions.md). Consult these before the earlier planning investigation. [Native build reuse prerequisite](prerequisite-21-native-build-reuse.md) and the owner-emission boundary evidence record the remaining shared interfaces.
- `evidence/21/code-investigation.md`, `planning-preflight.json`, `pre-adoption-check.json` under `_bmad-output/specs/spec-cicd/`: exact revisions, gate inventory, dependencies and observed failures; read for implementation.
- Parties `Hexalith.Parties.Standalone.slnx`, `Directory.Build.{props,targets}`, `Directory.Packages.props`: graph/cohort and container provenance; three native suites currently have obsolete build exclusions.
- Parties `tests/Hexalith.Parties.Ci.Tests/`, `tests/ci-lifecycle/`, `scripts/`: mixed workflow/controller assertions and product runtime/package/asset checks; retain product coverage per inventory.
- Builds `Github/lib/{ci_pipeline,release_build}.py`, `Github/release-build/action.yml`: existing MTP/classifier and source/version release interface; no frozen-created input.
- CiCd `setup/README.md`, `tools/{render,validate}.py`, `templates/`, `rendered/`: existing registration, validation and delivery interfaces.

## Tasks & Acceptance

**Execution:**
- [ ] `evidence/21/` — verify/provision AD-21 App selection, stale CodeQL/release state, exact rulesets, main-only release environment, Parties-only Zot identity, scoped NuGet policy and org grants. Keep exact-true switch/90-day retention; assess unmatched `v1.2.0` before cleanup. Resolve unreadable installation selection through maintainer UI/readback.
- [ ] Parties `tests/Hexalith.Parties.Ci.Tests/`, `tests/ci-lifecycle/`, obsolete controller scripts, root `package.json`/lock and active docs — remove CI/agent/story/YAML gates and tool-only manifests; preserve mixed product assertions and `tests/e2e` tooling. Delivery alone replaces all eight legacy workflows. Record both owner-gate dispositions; historical eleven-test count is stale.
- [ ] Parties standalone solution, native test projects, Admin UI test host and `scripts/{prepare-aspire-runtime-hosts,prepare-ci-package-dependencies,verify-catalog-runtime,verify-public-package-integration}.*` — implement approved graph boundary; build declared runtime owners once, reuse outputs, preserve native/authentication/persistence/cleanup and compatibility cohorts. Include published Aspire assets in the graph. Qualify EventStore 5.1.1, 5.3.0 and 5.3.1, shipping 5.3.x early (see the 2026-11-19 note); remove obsolete build exclusions and old CI receipts.
- [ ] Parties `.github/actions/{after-unit-tests,after-integration-tests}/action.yml` and retained test projects — route all product suites exactly once; explicitly classify lifecycle tests as integration and separate environment-sensitive general tests. Preserve browser/accessibility, declaration, package and native checks with shared Dapr/browser/registry setup.
- [ ] Parties `Directory.Build.targets`, `src/Hexalith.Parties{,.Mcp,.UI}/*.csproj` — enroll all existing container identities and adapt shared source/version/created metadata with strict provenance. Require `prerequisite-21-frozen-release-timestamp.md` to ship separately before adoption. No audit waiver was found; transfer none without evidence.
- [ ] `setup/Hexalith.Parties.yml`, `references/Hexalith.Parties`, `rendered/Hexalith.Parties/`, `rendered/Hexalith.Parties.perimeter.json` — register the verified remote product revision, standalone solution, hooks, environment and direct dependencies; commit registration/render together only after prerequisites.
- [ ] `evidence/21/` — verify candidate/App adoption and foreign-content preservation; immediately enable immutable releases and remove only scoped legacy policies/credential grants. Authenticate green CI, normal local checker and next nightly publication or valid no-release result.

**Acceptance Criteria:**
- Given adopted Parties, when shared CI runs, then every retained product suite executes successfully without CI/story/YAML gates or repeated hook builds.
- Given a releasable revision, when central nightly publishes, then packages and all three images retain exact source/version and the approved common timestamp.
- Given adoption, when cleanup and a nightly run (CAP-13) after adoption finish, then scoped publishing and green CI satisfy CAP-16.

## Implementation Notes

- 2026-11-16: A concurrent local-only build run started from CiCd `ec481fd50b280e2d41f9baecbd03945c833e4538` and Parties `a575021fc97a8eda664711089270b60f5e570ded`. It later discovered the separate published preparation recorded below. Its [older candidate and verification](../specs/spec-cicd/evidence/21/preparation-a575-session-report.md) are retained separately. The checkout is clean at the published preparation, with the older changes preserved in a patch and named stash; see [preservation proof](../specs/spec-cicd/evidence/21/preparation-a575-checkout-preservation.json). The canonical baseline above is preserved and full story acceptance remains incomplete.
- 2026-11-16: This bmad-build execution is local only: no push or remote operations, per the implementation workflow. Preserve pre-existing staged, unstaged and submodule changes. Remote freshness, administration, publication and adoption remain incomplete until an authorized execution can verify them. Shared frozen-created support remains a separate prerequisite.
- 2026-11-16: The human approved the complete spec and requested stopping before implementation. The approved intent is frozen; shared timestamp support remains a separate adoption prerequisite.
- 2026-11-16: Resumed in `/home/administrator/projects/hexalith/cicd-build-21` from freshly fetched main. The implementation phase permits local edits and verification only, with no pushes or remote operations. Complete independent product preparation while keeping prerequisite, delivery and nightly acceptance explicitly pending. Parties is on `build/21-product-preparation` at freshly fetched `a575021fc97a8eda664711089270b60f5e570ded`; only direct CiCd submodules are initialized.
- 2026-11-16: Local preparation removes obsolete gates, retains product observation checks, declares runtime artifacts, separates five live-runtime classes, and adapts container source/version identity. The complete Release build and thirteen prebuilt preparation records pass. Complete retained Ci.Tests passes 421 cases serially; complete general unit tests pass 2,800 cases; both report zero errors/failures/skips. Exact inputs, layered verification and earlier failures are preserved in the linked handoff. No commit, push, registration or adoption occurred.
- 2026-11-19: Human decision: qualify EventStore 5.3.0 and 5.3.1 now, as an early standalone preparation push.
  - **Why:** ChatBot runs all owner children on one EventStore version, and Tenants requires 5.3.0 or 5.3.1. Parties `Directory.Build.targets` enables its catalog API, query selectors, catalog hosts and cancellable projections only through 5.1.1. The lists are at lines 6, 11, 15 and 35 of main `e88937fb6bc6d6ceaf66996abcf1f753102abf71`, blob `3b8f26b17d9f0d14b34c8b03978b957e246de3aa`. On 5.3.x, Parties compiles without owner declarations, and ChatBot's loader refuses it.
  - **How:**
    - Start from freshly fetched Parties main.
    - Add 5.3.0 and 5.3.1 to those four lists.
    - Run the retained suites in package mode on 5.3.1.
    - Push only this change with module-agent, under the approved Parties pre-adoption substitute and with exact-input evidence.
    - It does not wait for the other story-21 prerequisites.
    - Leave Parties' own default selection unchanged, including Builds' `HexalithPartiesSdk42CatalogView`.
  - **Compile probe, 2026-11-19, tests not run:**
    - Owner project: 0 warnings and 0 errors, with all catalog constants enabled.
    - Standalone solution: 38 projects built with no C# errors. The one failure was the native Admin UI prebuild prerequisite, which the probe skipped.
    - Evidence: [main readback](../specs/spec-cicd/evidence/19/latest-dependencies/main-readback-20261119.json).
- Completion remains blocked on shared native test/model reuse, owner composition package routing, released frozen-created support and the live AD-21/adoption/nightly prerequisites. All execution checkboxes remain open because their full obligations are unsatisfied. Keep status `in-progress`; implementation has not reached the workflow review checkpoint.

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines; no other constraint changed.
- 2026-11-19 — Human approved qualifying EventStore 5.3.0 and 5.3.1 in this story and shipping it as an early standalone preparation push, so that ChatBot can host the Parties owner beside Tenants. Extended the EventStore task and added an implementation note. No other constraint changed.

## Review Triage Log

## Design Notes

External effects include settings, product pushes, delivery, credential revocation and publication. The footprint is Parties tests/graph/scripts/actions/metadata and CiCd registration/render/evidence. Shared timestamp support ships separately. API inspection establishes published fixture availability, not a successful build or live run.

## Verification

- Use `run-with-temp` for disposable work; preserve exact-input results in `evidence/21/`.
- Before product pushes require the approved substitute and pinned exact-message commitlint; after adoption require the normal checker from a standalone module clone.
- Run `uv run --locked --script tools/render.py --check`, then committed-candidate `tools/validate.py`; require global/Parties lint, schema, perimeter and live-action verdicts.
- Verify actual native/browser execution, container provenance/OCI identity, hosted CI, App delivery and scheduled-night outcomes; no mock or unavailable permission proves acceptance.

## Preparation Publication

The human requested publication to main. Product preparation is published in
Parties commit `0f261ccd3b461102dcac35da2e074d15a195ebb4`; the corresponding CiCd
record preserves `in-progress`. See [publication proof](../specs/spec-cicd/evidence/21/publication/publication.json)
and [pre-push qualification](../specs/spec-cicd/evidence/21/publication/pre-push-qualification.json).
Registration/adoption and full acceptance remain pending their documented prerequisites.
