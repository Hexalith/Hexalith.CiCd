---
title: '26 prerequisite: authenticated Platform build preparation'
type: 'feature'
created: '2026-11-16'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '9c2a65cbf1d523609000fffb525fba5cf5e8b4b3'
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/26/shared-support.md'
  - '{project-root}/_bmad-output/implementation-artifacts/prerequisite-26-platform-build-preparation.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 26 cannot consume shared CI/release because its signed producer
assemblies and finite compatibility consumers lack shared orchestration, and
public package verification omits signature and exact payload checks.

**Approach:** Implement the separately approved prerequisite using story 16's
preparation lifetime and existing build/publication paths. Add only demonstrated
missing support and qualify a concrete local source candidate for central release.
The 2026-11-16 human approval and subsequent `fix` instruction authorize this
work separately from Platform adoption.

## Boundaries & Constraints

**Always:** Preserve assertions, active catalog versus historical producer
identities, original artifacts, audited release settings and unchanged opt-out
behavior. Follow shared-support.md's closed interfaces. Preserve concurrent
work and use run-with-temp for disposable jobs. Author Builds policy in Builds
and module delivery policy in CiCd. Record architecture additions first.

**Never:** Edit Platform owned files, initialize nested submodules, create
another publisher/scheduler, execute module callbacks during privileged
publication, build/setup in hooks, introduce module-name branches, weaken
security/tests, fabricate qualification or pin untagged source. Source work does
not grant adoption/CAP-16. This implementation step performs no remote operations.

## I/O & Edge-Case Matrix

| State | Required result |
| --- | --- |
| Options absent/null | Existing shared behavior and legacy manifest shape unchanged. |
| Valid historical producer and different active catalog | Authenticated assemblies exist before first evaluation; both identities retained. |
| Wrong/unsigned/changed/unavailable producer | Fail before evaluation; export nothing and remove owned scratch. |
| Declared compatibility projects | Isolated per-case outputs, exact selected versions, shared package-mode restore/build. |
| Unsafe or policy-changing project input | Reject; no hidden build, test omission or foreign-source fallback. |
| Case build failure | Stop before successor/hooks; retain failure and release audits. |
| Enrolled public package | Signature verifies and all original nonsignature members match. |
| Public body change or failed signature | Fail before finalization; no module code or credential leakage. |

</frozen-after-approval>

## Code Map

All Builds paths below are relative to `references/Hexalith.Builds/`.

- `Github/lib/module_preparation.py`, `ci_pipeline.py`, `local_check.py`,
  `release_build.py`: reuse one preparation lifetime, exact-input validation,
  shared flags/evaluation and fail-fast orchestration.
- `schemas/hexalith.ci.v1.json`, `Github/lib/ci_config.py`: add nullable
  `publishedBuilds` and bounded `buildProjects` with defaults; no new reader.
- Platform `eng/{builds-tuple.json,builds_publication.py,prepare_builds_artifacts.py}`:
  existing producer handoff/parser reference; port controls into shared code,
  never call these module scripts or conflate their old catalog with active Builds.
- `Props/Directory.Packages.props`: existing Composition versions already suffice;
  preserve catalog data and existing managed producer behavior.
- `Github/lib/{release_build,release_draft,release_publish}.py`: evaluated project
  opt-in, authenticated manifest and strict public archive verification.
- `Github/lib/tests/`, `setup/README.md`, CiCd renderer/validator fixtures and
  architecture spine: qualification and synchronized additive contracts.

## Tasks & Acceptance

**Execution:**

- [ ] `shared-support.md`, architecture spine and `setup/README.md` — record
  reused interfaces and actual additive source contract before runtime edits.
- [ ] Builds CI schema/reader and tests — add closed defaults, paths, mutually
  exclusive preparation, finite catalog selections and unsupported-input refusals.
- [ ] Builds preparation, CI/local/release entry points and tests — authenticate
  historical assemblies before evaluation; reuse/revalidate one producer lifetime.
- [ ] Builds shared project orchestration and tests — build declared committed
  non-test consumers with isolated artifacts and publish read-only output mapping;
  keep these projects outside package discovery.
- [ ] Builds release discovery/artifact reader/publisher and tests — carry
  evaluated `HexalithVerifyPublishedPackage` policy only when enabled; verify
  public signatures and unchanged original payload without module callbacks.
- [ ] Builds docs and CiCd renderer/validator fixtures — qualify new inputs,
  meaningful failure cases, defaults and regression paths; save exact evidence.

**Acceptance Criteria:**

- Given opt-in producer preparation, when CI/local/release evaluate projects,
  then the same verified historical assemblies exist first and the accepted
  catalog remains independently authenticated.
- Given six declared SDK cases, when shared build orchestration runs, then
  each has its selected versions and disjoint outputs with normal strict flags.
- Given an authenticated original enrolled package, when public verification
  runs, then signature and every nonsignature body pass or publication fails.
- Given existing unconfigured modules, when the changed shared paths run, then
  existing behavior and artifact formats remain compatible.

## Implementation Notes

The separate prerequisite scope was approved before this session. No new intent
choices or irreversible local operations are required. Publication through the
existing central process, acceptable immutable tag/source and genuine Platform
product qualification remain dependencies after this source candidate. Keep
production builds-version, setup registrations and rendered modules unchanged
until that release is qualified. Record outstanding external work explicitly.

## Spec Change Log

## Review Triage Log

## Design Notes

Reuse the existing finite Composition catalog views. `publishedBuilds` reuses the
historical signed handoff and exports the existing published tool root without
requiring Platform to reference itself. `buildProjects` supports only explicit
non-test consumers and finite named catalog versions. Product archive assertions
can run read-only in ordinary unprivileged Pack targets; the publisher receives
only authenticated policy and bytes, never a module callback.

## Verification

Run relevant schema/preparation/pipeline/local/release tests and renderer/validator
regressions using run-with-temp. Include real SDK output-isolation qualification
and six exact selections. Exercise altered/unsigned producer and public-package
inputs, strict-policy round trips, unchanged defaults, audit preservation and
credential isolation. Record actual commands/results separately from unexecuted
Platform qualification or central publication.
