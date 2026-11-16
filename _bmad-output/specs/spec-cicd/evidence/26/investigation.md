# Story 26 investigation — 2026-11-16

This is planning evidence, not implementation, adoption or product verification.
Only read-only remote operations have run. Existing concurrent work on stories
16 and 18 is outside this run's scope.

## Authenticated source and contracts

`source-inventory.json` records identities obtained directly from Git:

- CiCd baseline: `c74b5c8f5787fb33bfd85c1c4430b6de39674198`.
- Freshly fetched Platform main, local HEAD and parent gitlink:
  `c2236a9f95c37d4d2ef8dee3fe2cbfe5e9ab41d2`.
  The story's warning about a stale checkout is no longer true. There is no
  initial gitlink change to make; preparation will create a later product pin.
- Selected Builds `v6.0.6`:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- Platform's historical producer/catalog pin, Builds `v6.0.5`:
  `e2bbbd0893f586e4d447ef8358ff747ea3d34435`.

The canonical SPEC and architecture AD-3/7/12–17/21 govern. Use
`setup/README.md`, `tools/render.py`, `tools/validate.py`, the exact released
Builds schemas/readers, `Github/lib/guard_actions.py` and the shared package
discovery/publishing interfaces. Do not implement a second pipeline in hooks.

## Maintainer preflight

`preflight.json` records sanitized request outcomes from the command-local
maintainer profile `/home/administrator/.config/gh`. Ordinary reads use
`/home/administrator/.config/gh-cicd-agent`. Both authenticated as `jpiquot`;
neither `GH_TOKEN` nor `GITHUB_TOKEN` overrides were present. Repository metadata
reports administrative account access; this does not establish token API scope.

| AD-21 prerequisite | Observed result |
| --- | --- |
| CiCd App repository selection | Unverified. Org installation `179966090` exists. Its selected-repository API returned HTTP 403 requiring an authorized access-token type/`read:user`; this does not prove Platform is absent. Verify selection through the existing interactive installation UI. |
| Stale release/CodeQL state | First release page returned 47 releases and no drafts. Analysis listing returned HTTP 404 `no analysis found`. Recheck complete release/tag inventories and distinguish missing resources from unreadable metadata before cleanup; orphan tags were not assessed. |
| Exact rulesets | Three active rulesets differ from AD-21. Main `24657106` adds reviewed PR/code-owner requirements and a user bypass. Immutable-tags `24657570` applies to all tags. Tag-creation `24657217` adds a separate restriction. Replace with the exact main deletion/non-fast-forward and `v*` update/deletion policy, preserving before/after evidence. |
| Release environment | Only `production` exists, with required review. `hexalith-release` and its Platform-only Zot pair are absent. No existing secret value was read. A secret name alone would not establish its registry ACL. |
| NuGet trusted policy | Unverified; no authenticated NuGet account inspection. Add the scoped `release.yml`/`hexalith-release` policy beside the legacy policy before preparation; retire legacy policy only after adoption. |
| Default CodeQL / security updates | Already not configured / disabled. Secret-scanning push protection is enabled. |
| Central publish switch | `HEXALITH_RELEASE_PUBLISH_ENABLED` absent. Existing extension-specific switch is not a substitute. |
| Retention | 90 days. |
| Shared registry/NuGet grants | Platform absent from the complete three-repository selections returned for both Actions and Dependabot pull secrets and `HEXALITH_NUGET_USER`. |
| Immutable releases | Disabled; enable immediately after successful App adoption. |

No administrative setting, policy, credential, tag or release was modified.

## Product preparation and gate inventory

Paths below are relative to Platform. Preserve SDK `11.0.100`, the
Microsoft.Testing.Platform selection, source-mode product behavior and genuine
assertions, independently of their directory or story-related names.

| Current workflow | Required disposition |
| --- | --- |
| `.github/workflows/tuple-ci.yml` | Delivery retires it. Preserve the actual current42/base42/extensions package-mode Composition suites; current measured inventories are 486/93/9. Replace its restore/build orchestration through shared preparation, not a late rebuilding hook. |
| `.github/workflows/catalog-builder.yml` | Preserve actual CatalogBuilder compatibility against SDK 3.130.0, 3.130.1, 3.130.2, 3.132.1, 4.1.0 and 4.2.0, including signed public/private owner readers. `tests/catalog-builder/verify_*.py` creates and builds isolated consumers and CatalogBuilder is outside the root solution; these are product checks, not disposable CI self-tests. Shared orchestration must supply their finite build cohorts. |
| `.github/workflows/source-release.yml` | Replace workflow-run callbacks/semantic-release with central nightly publication. `release.config.mjs` has `assets: []`: current source releases require no auxiliary asset protocol. Preserve exact-source product qualification; remove coupling to obsolete workflow names. |
| `.github/workflows/test-extension-release.yml` | Move intended `Hexalith.Platform.TestExtension` publication to the shared publisher. Preserve package bodies, signed SDK closure, immutable source/producer documents, qualified native source, archive controls and post-publication signature checks. Explicitly select the package; it is currently `IsPackable=false` and explicitly enabled only by this workflow. |
| `.github/workflows/broker-candidate-qualification.yml` | Human approved retirement of the consumed candidate-02 job through delivery. Preserve qualification tools, assertions, inputs, historical results and unresolved broker work. No replacement dispatch, recurring release gate or production eligibility was approved. |

Delete the YAML assertions in `tests/source-release/{tuple-workflow,
broker-candidate-workflow,fixture-workflow}.test.mjs`. Retire
`tests/source-release/source-release.test.mjs`, `eng/source-release/` and the
old workflow-identity/publication gate assertions when their orchestration is
removed. Split mixed controls: retain the product archive/readiness/inventory
assertions in `eng/test-extension-release/{verify-package.py,verify-published.py,
qualify-host.py,test_package.py,test_controls.py,test_host_entry.py}`. Refusal
tests of the deleted publisher are not a reason to delete package validation.

Delete tool-only root `package.json` and `package-lock.json` after retiring their
release/commitlint/js-yaml consumers. No tracked `.husky/` exists. Delivery owns
removing release/commitlint configuration; product preparation must preserve
those files and every other owned entry exactly.

No active NuGet audit waivers were found. `eng/HistoricalPackageSecurity.props`
contains real secure package-version upgrades, including Aspire 13.6.5 and
SignalR 10.0.15. Preserve or deliberately centralize those remediations; do not
delete them as waivers. If fresh investigation finds a waiver, centralize its
justified equivalent in a released Builds `Props/` before adoption.

`source-inventory.json` lists 31 root-solution projects and 56 total projects.
After valid preparation, evaluate `IsTestProject` and classify every actual
retained project and external compatibility consumer. Do not blindly add all
fixture projects to the root solution or treat every helper project as a test.

`src/Hexalith.Platform.Identity/Hexalith.Platform.Identity.csproj` is implicitly
packable but the old source publisher publishes no packages. Avoid introducing
an Identity package merely through central discovery. Preserve the existing
explicit TestExtension publication intent and make other project packability
explicit. Anonymous NuGet flat-container reads in `package-inventory.json`
returned 404 for both names: neither an existing published archive nor a new
package-publication success was established.

## Blocking shared capability

`Directory.Build.props` maps `HexalithBuildsPublishedToolRoot` to
`BuildsToolingAssemblyPath` and `BuildsEventStoreHostAssemblyPath`.
Composition and Composition.Tests otherwise fall back to foreign Builds source
projects. `Directory.Build.targets::ValidatePlatformCiReferences` refuses those
references and missing assemblies under CI. Preserve that product boundary.

Before evaluation, `eng/run_tuple_ci.py` calls
`eng/prepare_builds_artifacts.py` to verify `eng/builds-tuple.json`, official
release handoff, signed CLI archive and extracted assembly identities. A normal
shared build needs equivalent authenticated preparation before restore. The
current released schema/runtime does not supply it. Story 16's proposed generic
managed preparation is unshipped and its module-manifest behavior alone does
not provide Platform's required assembly paths.

The producer's signed catalog defaults to SDK 5.1. Composition's measured
regression cohort deliberately selects SDK 4.2.0, Tenants 7.0.7, Memories 3.0.27,
Parties 3.1.1 and McpCli 2.0.1. Preserve distinct cohort identities and do not
relabel the historical producer or default catalog. First reuse existing
test/project and shared preparation support to preserve the six CatalogBuilder
SDK cases and fixture build. Add shared build support only for demonstrated
gaps; no speculative general compatibility framework is approved. Keep actual
build orchestration in the shared path rather than hiding builds inside hooks.

Extend/reuse shared authenticated preparation and package discovery/release
interfaces; retain the existing release build-once and immutable original
artifact rules. Product verification that requires the built package must run
against that original payload at an appropriate shared stage; `nightly` must
not repack or publish. The existing `verify-published.py` intent needs equivalent
public-package verification. Reuse `Github/lib/release_publish.py::verify_packages`,
which already checks published package identity, version and source revision;
add only missing payload/signature checks. A general module-code callback in the
privileged publisher is not justified. Hooks remain read-only, reuse the
environment/build and write no result
or story-evidence files. Keep module names out of generic runtime logic.

The proposed prerequisite must concretely define and qualify those inputs,
stages and failure modes, document any required architecture amendment, and
publish an acceptable Builds/CLI release before story 26 can adopt. No new
auxiliary source-release archive format is justified by current product needs.

## Preparation checker conflict and approved decisions

The required normal command was attempted from the Platform root through
`run-with-temp`; it exited 2 because the nested Builds checker is unavailable.
No nested submodule was initialized and no prospective owned state was overlaid.
Even making the executable available would not supply an accepted Platform
render or the missing preparation contract. This is not a passing check.

On 2026-11-16 the human approved the recommendations after reviewing their
mechanism, alternatives, benefits and costs:

1. A Platform-only preparation exception requires exact-revision package-mode
   builds/tests, retained compatibility/package checks, policy/commit validation
   and byte/mode/gitlink preservation of owned content. Save results for each
   exact candidate and rerun after changes. It ends at App adoption; standard
   `check.py` is then mandatory. Product failures and missing shared preparation
   remain blocking conditions.
2. Retire the spent broker candidate-02 workflow through delivery, retaining
   its product tools, assertions, inputs, history and open failures. The source
   `docs/implementation/story-4-17-broker-candidate-02-hosted-attempt-1.md`
   records a consumed attempt with verified integrity, credited cleanup and
   technical FAIL 20/24. `sprint-status.yaml` keeps Platform 4.17 in progress;
   its next step is offline remediation with no accepted successor dispatch.
   Removing the workflow removes its one-click hosted route; this does not
   resolve qualification, select a broker or grant production eligibility.
3. Record a separate blocking prerequisite in
   `prerequisite-26-platform-build-preparation.md`, reusing story 16's work and
   existing build/release interfaces. Add only verified missing capabilities,
   qualify them and consume an acceptable shared release before adoption.

This approval settles the three intent choices. It does not establish a
successful product check, shared release, remote setting change or adoption.
