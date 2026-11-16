# Prerequisite for story 21: frozen release timestamp

On 2026-11-16 the human selected “apply recommendations,” including generic
frozen publisher-created support released in Builds before Parties adoption.
This is a separate prerequisite; story 21 consumes the capability after it is
implemented, verified, released and available through CiCd's selected Builds
pin. This document does not claim the capability has shipped.

## Goal and boundaries

Give the original audited release build one publisher-owned UTC creation
instant, reused across every project, image and runtime identifier. Preserve
Parties' existing publisher-time semantics, exact source/version binding,
calendar validation and three container identities. Commit timestamps and
independent per-project clocks do not satisfy this decision.

Keep the shared runtime module-agnostic. Supply a generic build property that
product metadata can consume; do not hardcode Parties property names or
introduce a new scheduler, publishing path, restore/build in a hook, or a new
module secret. Existing consumers that do not use this property must retain
their current behavior. Preserve release complete-mode's original-artifact
semantics: reruns finish from the stored payload rather than rebuilding it.

## Current source

- Builds `v6.0.6` resolves to
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- `Github/lib/release_build.py:release_flags` passes `Version`,
  `PackageVersion`, `SourceRevisionId` and `RepositoryCommit`, but no common
  created-time authority. The build phase discovers projects, restores/builds
  the selected solution, packs packages and publishes each container RID.
- `Github/release-build/action.yml` supplies the frozen SHA and version to the
  original build phase. A common instant can be captured inside that phase;
  no new caller configuration or workflow input is inherently required.
- Parties `Directory.Build.targets` requires
  `ContainerProvenanceCreated` as one exact, real UTC RFC3339 second. Its labels
  include both image-created and artifact-created. It already requires exact
  SHA/version and equal container version tags. Keep these validations.
- Parties product adapters must additionally map the shared source/version
  properties and enroll all three hosts with `HexalithPublishContainer`.

## Work to implement separately

1. Builds `Github/lib/release_build.py`: capture the publisher instant once at
   the start of the original build phase. Carry the same validated value into
   project discovery, audited restore/build, package creation and each RID's
   container publication through a documented generic MSBuild property.
   Choose one unambiguous property name and retain full source/version binding.
2. Builds `Github/lib/tests/test_release_build.py` and the applicable existing
   release/OCI tests: verify that multiple projects and RIDs receive the same
   instant, including executions spanning a clock tick; reject malformed or
   impossible dates at the appropriate interface. Verify package-only/no-
   solution consumers and original-artifact completion remain correct.
   Use controlled clocks and fixture archives, not real-time sleeps or
   publication fixtures.
3. Builds documentation for the shared release interface: document the property,
   its time authority, exact format and scope. Only update the release composite
   or workflow interface if the implementation actually needs an added input.
   Reuse existing artifact transfer and complete-mode behavior.
4. Publish the capability through the authorized central release process.
   Confirm the acceptable immutable release contains it; advance CiCd's
   `builds-version` and render together using the existing version policy.
   Run committed-candidate validation before it can reach registered modules.
5. In story 21, map the released generic property to Parties' existing
   `ContainerProvenanceCreated` in product-owned metadata. Qualify the actual
   OCI archives for `parties`, `parties-mcp` and `parties-ui` across all selected
   platforms. Keep image/archive identity, source/version and both created labels.

## Acceptance

- Given a release containing multiple images and RIDs, when the original build
  produces its payload, then all created labels carry one publisher instant
  even if publication spans multiple clock seconds.
- Given malformed, inconsistent or impossible created metadata, when the
  product provenance boundary validates it, then publication fails without
  weakening existing validation or using an alternate timestamp authority.
- Given a stored original artifact, when complete-mode finishes publication,
  then it uses the original payload and timestamp without rebuilding.
- Given a consumer that does not use the new property, when its existing
  release runs, then no additional setup/configuration is required.
- Given the capability's verified acceptable release and updated CiCd pin,
  when Parties registration is prepared, then story 21 can consume it.
  Actual Parties adoption and nightly acceptance remain story 21 obligations.
