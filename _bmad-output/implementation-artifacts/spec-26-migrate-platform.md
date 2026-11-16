---
title: '26: Migrate Platform'
type: 'chore'
created: '2026-11-16'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/26/investigation.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Platform's tuple, compatibility and publication workflows bypass
shared CI/CD. Adoption must preserve product qualification and signed producer
dependencies without retaining workflow/story gates.

**Approach:** Follow AD-21: provision, prepare product changes, register/render,
adopt through App delivery, then verify green CI and the next central nightly.

**Human decisions, 2026-11-16:**

- Before adoption only, approve Platform preparation pushes after exact-revision
  package-mode builds/tests, compatibility/package checks, policy/commit
  validation and owned byte/mode/gitlink preservation. Save results and rerun
  after changes. The exception ends at adoption; product failures still block.
- Retire the spent broker candidate-02 workflow through delivery. Preserve its
  tools, assertions, inputs, evidence and unresolved failures. No successor
  dispatch, recurring release gate or production eligibility is approved.
- Ship missing shared capabilities separately under
  `prerequisite-26-platform-build-preparation.md`. Reuse story 16 and existing
  build/publication interfaces; add only demonstrated gaps. Adoption waits for
  a qualified acceptable shared release.

## Boundaries & Constraints

**Always:** Preserve SDK 11.0.100, package-mode CI, assertions, six CatalogBuilder
SDK cases and distinct Composition cohorts. Authenticate producer assemblies
before evaluation. Use module-agent for product writes, CiCd-agent for
CiCd/Builds and command-local maintainer access for administration. Preserve
foreign/concurrent work; use run-with-temp for disposable jobs.

**Never:** Directly edit owned Platform content, initialize nested submodules,
invent producer/catalog identities, weaken audits/tests, hide builds/setup in
hooks, publish from hooks, or revoke legacy access before adoption. Retain real
security upgrades. After adoption require the standard checker before pushes.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Missing prerequisite, unavailable shared capability or denied read | Block adoption; distinguish absence from unverified access. |
| Wrong producer, altered archive or changed catalog/cohort | Fail before evaluation; no foreign-source fallback or relabeling. |
| Genuine product failure | Fix product with assertions retained. |
| Adoption and nightly | Verify exact delivery/perimeter; accept authenticated success or nothing-to-release. |

</frozen-after-approval>

## Code Map

- `prerequisite-26-platform-build-preparation.md` beside this spec: separate
  scope, reuse rules and release acceptance required before adoption.
- `evidence/26/{investigation.md,source-inventory.json,preflight.json,package-inventory.json}`
  under `_bmad-output/specs/spec-cicd/`: full identities, gate inventory,
  authenticated settings, exact capability gaps and bootstrap failure.
- Platform `Directory.Build.{props,targets}`, `eng/{builds-tuple.json,prepare_builds_artifacts.py,run_tuple_ci.py}`:
  signed producer assembly preparation; preserve reference refusal and cohorts.
- Platform `Hexalith.Platform.slnx`, `tests/catalog-builder/verify_*.py`,
  `eng/test-extension-release/`, fixture/Identity `.csproj` and
  `eng/HistoricalPackageSecurity.props`: product coverage, package selection,
  payload/signature controls and secure versions. Companion identifies deletions.
- CiCd `setup/README.md`, `tools/{render,validate}.py`, `templates/`, `rendered/`:
  reuse registration/delivery and released Builds schemas/readers.

## Tasks & Acceptance

**Execution:**

- [ ] `evidence/26/` — verify/provision AD-21 prerequisites in order; retain
  sanitized before/after settings and exact access failures. Verify NuGet policy,
  module-only Zot ACL and App selection; inventory legacy cleanup targets.
- [ ] `prerequisite-26-platform-build-preparation.md` — require verified released
  support before dependent preparation/adoption. Record its exact tag/source;
  story 26 consumes that release and does not implement the shared prerequisite.
- [ ] Platform inventory-listed test files, `eng/source-release/`, root npm
  files — remove obsolete CI/story/YAML tooling and split mixed controls to
  retain package/readiness assertions. Preserve owned release configuration for
  delivery's deletion. No tracked husky or active audit waiver was found.
- [ ] Platform solution/projects, product runners and
  `.github/actions/{after-unit-tests,after-integration-tests,nightly}/action.yml`
  as needed — classify tests, route cohorts through shared builds, enable needed
  environment/hooks and preserve source-mode behavior. Keep the spent broker
  qualification outside release gates and retain its open product work.
- [ ] Platform fixture/Identity `.csproj`, archive verifiers and
  `eng/HistoricalPackageSecurity.props` — explicitly enroll only intended
  TestExtension publication, prevent accidental Identity publication, retain
  signed SDK/source/declaration checks and security remediations. Release any
  newly discovered justified waivers in central Builds before adoption.
- [ ] `builds-version`, `setup/Hexalith.Platform.yml`, Platform gitlink and
  `rendered/Hexalith.Platform/` plus its perimeter — after verified preparation
  reaches main, register released prerequisites and render together; validate
  the committed candidate before pushing.
- [ ] `evidence/26/` — authenticate App adoption and foreign-content preservation;
  enable immutable releases and retire verified legacy policies/grants/identities
  immediately. Observe adopted CI, normal checker and next nightly.

**Acceptance Criteria:**

- Given adopted Platform, when shared CI runs, then all retained product cohorts
  pass without workflow/story gates or foreign-source compilation.
- Given a central Builds bump, when Platform prepares, then the active catalog
  and genuine producer/cohort identities remain separately verified.
- Given a releasable Platform revision, when central nightly publishes, then
  only intended packages use qualified original artifacts and public signatures
  are verified; normal pushes do not publish.
- Given successful App adoption, when cleanup and the next scheduled nightly
  finish, then the owned perimeter is correct, CI is green and CAP-16 is met.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

The gitlink already equals fresh main. Source releases need no auxiliary assets.
Released v6.0.6 lacks preparation/cohort support; late hooks cannot fix it.
Settings, pushes, delivery, credential revocation and publication are external
effects; none has run.

## Verification

- Use the approved pre-adoption verification path for exact preparation
  revisions; after adoption run `python3 references/Hexalith.Builds/check.py`.
- Retain package-mode SDK/cohort, native fixture, payload/signature, compatibility
  and genuine product checks; run meaningful shared regressions for new APIs.
- Run `run-with-temp uv run --locked --script tools/render.py --check` and
  committed-candidate `tools/validate.py`; require global and Platform verdicts.
- Inspect authenticated delivery report, accepted/pushed full revisions,
  perimeter/preservation, adopted CI and actual next scheduled nightly outcome.
