# Prerequisite for story 26: Platform build preparation

The human approved this separate prerequisite on 2026-11-16 after considering
the alternatives. Story 26 consumes its verified shared release; it does not
implement this shared work. This record defines scope and release acceptance,
not a shipped capability or a fully designed new shared API.

## Goal and boundaries

Supply Platform's authenticated producer assemblies before evaluation and
preserve its compatibility/package checks through the shared build/release
paths. Reuse story 16's producer preparation and existing project/publication
interfaces. First establish what the released support already provides, then
add only demonstrated missing capabilities. Existing modules keep their current
behavior unless they enable new support.

Keep shared restore/build/environment orchestration in Builds. Preserve product
assertions, genuine producer/catalog identities and original release artifacts.
No general compatibility framework, arbitrary module-code callbacks in privileged
publishing, second publisher/scheduler, module-name conditions in generic runtime
code or auxiliary source-release archive format is approved.

## Evidence and dependency

- Initial Builds contract inspected: `v6.0.6`, source
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Recheck the exact released
  contract when implementing; concurrent uncommitted code is not a release.
- Platform source inspected:
  `c2236a9f95c37d4d2ef8dee3fe2cbfe5e9ab41d2`.
- Platform's `eng/builds-tuple.json` binds historical Builds `v6.0.5`, source
  `e2bbbd0893f586e4d447ef8358ff747ea3d34435`.
  `eng/prepare_builds_artifacts.py` verifies its official release handoff,
  signed CLI archive, extracted Tooling assembly and executable identity.
- `Directory.Build.props` consumes `HexalithBuildsPublishedToolRoot` to supply
  Tooling and EventStoreHost assembly paths. Composition otherwise falls back to
  foreign Builds source projects, which `ValidatePlatformCiReferences` rejects
  under CI. A hook after the build cannot supply this preparation.
- Composition's measured cohorts differ deliberately from the producer catalog
  default. CatalogBuilder also checks six SDK versions: 3.130.0, 3.130.1,
  3.130.2, 3.132.1, 4.1.0 and 4.2.0. Its product verifiers compile isolated
  consumers; invoking those scripts from a hook does not move their build
  orchestration into the shared path.
- `Github/lib/release_publish.py::verify_packages` already downloads public
  packages and checks their identity/version/source revision. Reuse it; determine
  only the missing payload/signature checks needed to preserve Platform's
  `eng/test-extension-release/verify-published.py` behavior.
- Source releases carry no auxiliary assets. Intended NuGet publication is
  TestExtension; implicitly packable Identity does not authorize another package.
  The broker candidate job does not publish OCI images.

Read [the investigation](../specs/spec-cicd/evidence/26/investigation.md) for
source inventories, historical administrative reads and the bootstrap failure.
Story 16's in-progress preparation work is a dependency to reuse, not duplicate.

## Separate implementation work

1. `_bmad-output/specs/spec-cicd/evidence/26/shared-support.md` — compare the
   qualified story-16 release with Platform's requirements. Record exact reusable
   interfaces, remaining changes, project/cohort routing, failure probes and
   release dependency. Establish existing sufficiency before adding settings.
2. Builds `Github/lib/module_preparation.py`, `Github/lib/ci_pipeline.py`,
   `Github/prepare/` and story 16's producer/CLI interface — supply authenticated
   published assemblies before restore/evaluation in CI, local checking and
   release builds. Keep genuine historical producer identity separate from the
   active accepted catalog. Reject wrong, missing, changed or unsigned inputs
   and retain the refusal to compile foreign source projects.
3. Builds `Github/lib/ci_pipeline.py`, `Github/lib/ci_config.py`,
   `schemas/hexalith.ci.v1.json` and existing tests, only if existing interfaces
   are insufficient — support declared project/version builds for the retained
   compatibility cases. Isolate outputs/catalog selections, preserve fail-fast
   behavior and reuse setup. Record any required architecture amendment before
   implementation; do not hide restoration/builds in module actions.
4. Builds `Github/lib/release_build.py`, `Github/lib/release_publish.py` and
   their tests — reuse discovery, original versioned payloads and public-package
   verification; add only missing product-equivalent payload/signature checks.
   Keep module-specific assertions in ordinary product validation with read-only
   inputs. Publication preserves its credential boundary and authenticated
   original-artifact handoff, with no rebuilding or execution of module callbacks.
5. CiCd architecture spine, `setup/README.md`, `templates/` and renderer/
   validator tests — document/export only actual new validated inputs. Qualify
   existing defaults and Platform success/failure cases. Tagged schemas,
   readers, consumers and rendered inputs must agree.
6. Publish through the authorized central release process. Record the exact
   acceptable tag/source and successful preparation, compatibility and package
   qualification. Move CiCd `builds-version` with its render when appropriate;
   story 26 consumes the capability only after qualification and release.

## Acceptance

- Given verified producer inputs, when Platform restores/builds in CI, local
  verification or release, then required assemblies exist before evaluation
  and no foreign Builds source projects are compiled.
- Given a wrong producer, changed/unsigned archive or unavailable authority,
  when preparation runs, then it fails before evaluation with the actual cause.
- Given the accepted catalog and measured compatibility cases, when checks run,
  then all cases retain their genuine SDK/package identities, isolated outputs
  and product assertions.
- Given a TestExtension release, when validation/publication runs, then the
  original package retains its required source/declaration/native payloads and
  its signed public package is verified without rebuilding during publication.
- Given an existing module with no new support enabled, when shared paths run,
  then its defaults and existing behavior remain unchanged.
- Given an acceptable released Builds contract containing the required support,
  when story 26 resumes, then adoption can use it. Prerequisite fixture results
  do not establish Platform adoption or CAP-16 completion.


## Source implementation status, 2026-11-16

The separate [source implementation spec](spec-26-platform-shared-build-preparation.md)
is complete after independent review and passing shared CI/local/release,
renderer and validator qualification. See the
[final verification packet](../specs/spec-cicd/evidence/26/final-verification/results.json).
It supplies historical published producer preparation, finite shared compatibility
builds and strict public archive verification. Original catalog views and legacy
defaults remain intact.

This is a reviewed source candidate. Central publication, an acceptable exact
immutable bot release and genuine Platform producer/cohort/package qualification
remain outstanding. Do not consume untagged source or mark story 26 adopted.
