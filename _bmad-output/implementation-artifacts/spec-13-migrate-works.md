---
title: '13 — Migrate Works'
type: 'feature'
created: '2026-11-17'
status: 'ready-for-dev'
baseline_commit: '9ffce320a27501a643c40996ffca490d68f620d9'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-13-context.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/gate-classification.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Works still runs legacy domain-ci, a 180-minute Platform parity job, and mixed lint/source-identity gates. Sampled CI was 56/56 red; product tests ran only after setup and policy failures.

**Approach:** Follow AD-21 to adopt Works through App delivery. Keep product compilation, tests, scans, commitlint and publishing. Replace the two failing setup steps with shared stages. Classify the three unnamed Works gates with the keep/delete rule and enable only kept product checks as custom actions.

## Boundaries & Constraints

**Always:** Follow AD-21 in order. Use module-agent for `references/Hexalith.Works` product writes, CiCd-agent for CiCd and Builds, command-local maintainer for App/rulesets/environment/legacy cleanup. Start product branches from freshly fetched current `main`. After adoption, require standalone `python3 references/Hexalith.Builds/check.py`. Preserve `global.json` 11.0.100, foreign instructions/settings, Builds catalog Works conditions, and `commitlint.config.mjs` bytes until delivery deletes that absent-glob. Shared CI checks out `references/Hexalith.Platform` and `references/Hexalith.Parties`, enables `dapr` and `additionalSdkVersion: '10.0.404'`, and CodeQL `csharp`/`python`. Host Platform R1–R11 as an extra Linux `jobs` entry (`timeoutMinutes: 180`, own Dapr); that action may init the extra gitlinks it already uses. Save evidence under `evidence/13/` outside `run-with-temp`.

**Never:** Edit owned module files. Initialize nested submodules. Weaken audits, skip test projects, add skip markers, or port `allowed-not-runnable-tests`. Import owned CI/CD through PR Update branch. Obtain the App key. Count a `qualify-bump` run or another module's row as a nightly outcome. Register or deliver Works before story 11's nightly checkpoint is accepted. Put R1–R11 on the shared CI job or the nightly hook. Run Explicit Platform-lane facts in stage 4. Revoke legacy publishing before authenticated adoption. Extend another module's checker exception to Works.

**Human decisions, 2026-11-17 ("apply recommended"):** (1) Works-only preparation proof before module-agent pushes: package-mode Release build; UnitTests, PropertyTests, ArchitectureTests; IntegrationTests that stage 4 actually executes (not Explicit Platform-lane facts); consumer validation; released commitlint/audit; exact owned-byte/mode/gitlink preservation vs freshly fetched `main`; save revisions/results. After delivery, normal `check.py`. This proof does not run R1–R11. (2) Run AD-21 and product prep now; add setup/render/gitlink and let delivery adopt only after story 11's nightly checkpoint is accepted (amended 2026-11-18, on-demand nightly). (3) Keep R1–R11 as a parallel extra Linux `jobs` product action, 180-minute timeout, own Dapr — the existing long-job knob, not a second OS. (4) Leave the nine allowlisted facts as Explicit Platform-lane tests in `IntegrationTests`; do not port the skip list; R1–R11 remains their proof. If adopted stage 4 still selects them, add a test-project trait/filter, not a CI skip.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing AD-21 prerequisite, refused API, or concurrent main change | Record the exact result; stop the dependent write; refresh and revalidate. |
| Unadopted tree without `hexalith-ci.json` | Use only the approved Works preparation proof on that exact candidate; after adoption, `check.py` is mandatory. |
| Story 11 night not yet accepted | Product prep and AD-21 may proceed; setup/render/gitlink and delivery wait. |
| Product test or scan failure | Fix the product; do not skip projects, weaken audits, or edit owned files. |
| Explicit Platform-lane facts in `IntegrationTests` | Stage 4 does not select them; R1–R11 remains the proof. |
| Platform R1–R11 or source-identity failure | Fail that product action; keep artifacts. Shared stages 1–4 may still pass. |
| Adopted green main with drifted callers, failed adoption push, or immutable releases off | Do not release; the nightly run is red. |
| Releasable history vs nothing to release | Authenticate the real nightly outcome; never force a version. |

</frozen-after-approval>

## Code Map

- Works `151ffb945a7017143010136fedc5762b5b67a18e` `main`: `.github/workflows/{ci,release,codeql,commitlint,dependency-review}.yml` — legacy callers pin Builds `3641d622`; delete with delivery.
- Works `.github/workflows/ci.yml` jobs `platform-parity`, `scripts-lint`, `ci` — classify: keep R1–R11 and `scripts/verify-source-debug.py`; delete actionlint, YAML-asserting `scripts/tests/test_release_{builds_compatibility,hook_permissions}.py`, `tests/Hexalith.Works.ArchitectureTests/FitnessTests/CiCdConfigurationTests.cs`, `PlanningEvidenceDocumentationTests`.
- Works `scripts/{prepare-platform-builds.sh,verify-platform-parity-ci.sh,verify-source-debug.py}` and `references/Hexalith.Platform/eng/works_toolchain.py` — product proofs; enable as custom actions, never from owned workflows.
- Works `package.json`, `package-lock.json`, `.releaserc.json` — tool-only; delete in product prep. No `.husky/`. No `NuGetAuditSuppress`. `Directory.Build.props` `WarningsNotAsErrors` NU1901–NU1904 is not a Props waiver; do not treat it as one.
- Works tests: stage 3 `UnitTests`, `PropertyTests`, `ArchitectureTests`; stage 4 `IntegrationTests` excluding `[Fact(Explicit = true)]` Platform-lane proofs; `Hexalith.Works.Testing` is packable helper. Packages: Contracts, Server, Projections, Reactor, Testing.
- `setup/Hexalith.PolymorphicSerializations.yml` — closest plain .NET registration; add Works knobs plus a Linux `jobs` entry for R1–R11. `setup/Hexalith.Works.yml` is absent.
- `tools/{render,validate,check_global}.py`, `templates/`, `builds-version` (`v6.2.0`) — reuse; commit setup + `rendered/Hexalith.Works/**` + perimeter + gitlink together.
- `_bmad-output/specs/spec-cicd/{gate-classification.md,module-inventory.md,adoption-execution.md}` and `docs/pre-adoption-publication.md` — record Works verdicts; do not extend other modules' checker exceptions.

## Tasks & Acceptance

**Execution:**

- [x] `_bmad-output/specs/spec-cicd/evidence/13/` — provision AD-21 in order for Hexalith.Works (App selection, stale drafts/tags/CodeQL, exact `main`/`v*` rulesets, main-only `hexalith-release` with this module's Zot identity, additive nuget.org policy for the five package IDs, scans off, exact publish switch, 90-day retention, org grants). Record live readbacks.
- [x] `_bmad-output/specs/spec-cicd/gate-classification.md` — record the three Works verdicts: delete CI/YAML/story lint; keep source-identity and R1–R11 as product actions.
- [x] Works product tree — add `.github/actions/` for source-identity and R1–R11; delete YAML/story/workflow-text tests and tool-only npm/releaserc; leave Explicit Platform-lane facts in `IntegrationTests`; do not edit owned files. Apply the approved preparation proof before any module-agent push.
- [ ] `setup/Hexalith.Works.yml`, `rendered/Hexalith.Works/`, `rendered/Hexalith.Works.perimeter.json`, `references/Hexalith.Works` gitlink — after story 11 night acceptance, register `Hexalith.Works.slnx`, Platform/Parties submodules, dapr, extra SDK, CodeQL csharp/python, source-identity hook, and the 180-minute Linux R1–R11 job; validate; commit cause and render together; delivery adopts.
- [ ] `evidence/13/` — authenticate adoption, enable immutable releases, remove other nuget.org policies and legacy secrets/NUGET_API_KEY/Zot; prove green adopted CI, standalone `check.py`, and a nightly run (CAP-13) after adoption (release or nothing-to-release).

**Acceptance Criteria:**

- Given AD-21 and the approved publication rule, when module-agent pushes product prep, then owned bytes/modes/gitlink match freshly fetched main and the approved checks passed on that exact candidate.
- Given story 11's nightly checkpoint is accepted and registration is valid, when App delivery adopts Works, then one forward `build(cicd): apply … from Hexalith.CiCd` commit matches the accepted perimeter, keeps foreign content and `.github/actions/**`, and removes legacy workflows plus absent-globs.
- Given adopted main, when CI runs, then shared stages 1–4 pass without Explicit Platform-lane facts, the parallel R1–R11 job and source-identity action are green, the two legacy setup failures are gone, and no workflow-YAML or story-evidence tests remain.
- Given adopted green main, when a nightly run (CAP-13) after adoption finishes, then authenticated CodeQL, release-or-nothing-to-release, scan and delivery results exist, and legacy publishing access is already gone.

## Implementation Notes

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines, including frozen ones; no other constraint changed. The story 11 night prohibition became a ban on counting `qualify-bump` runs or another module's row; human decision (2) now waits for story 11's nightly checkpoint.

## Review Triage Log

## Design Notes

Apply the gate rule; do not invent a fourth category.

- **Lint release tooling:** delete actionlint and tests that parse workflow YAML or story evidence. Keep `verify-source-debug.py` (reviewed EventStore/PolymorphicSerializations source↔package identity) as a product action.
- **Preserve source identity checks:** keep; same product action as `verify-source-debug.py`.
- **Platform R1–R11 parity and rollback:** keep as a parallel extra Linux `jobs` action (`timeoutMinutes: 180`, own Dapr). Shared CI submodule list stays Platform + Parties; the action keeps initializing the gitlinks it needs.
- Shared stage 3 replaces late "Fail on blocking test failures". Shared package-mode build replaces the two failing setup steps except published Builds artifacts still needed inside the R1–R11 action.

## Verification

**Commands:**

- `run-with-temp python3 references/Hexalith.Builds/check.py` from a standalone Works clone with Builds as a direct dependency after adoption — expected: exit 0 on the adopted tree.
- `run-with-temp uv run --locked --script tools/render.py --check` — expected: `rendered/Hexalith.Works` matches generation.
- `run-with-temp uv run --locked --script tools/validate.py` — expected: global true and Works live-main actions exist.

**Manual checks:**

- Authenticated GitHub readbacks for AD-21, adoption SHA, immutable releases, legacy-grant absence, hosted CI, and the next scheduled nightly verdict.
