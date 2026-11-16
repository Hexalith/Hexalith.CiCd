# Shared product-validation support required by Timesheets

Story 25 must not register Timesheets against the current shared contract until
the product checks below have a qualified execution and discovery path. This
document records the prerequisite boundary; it does not claim implementation,
publication or an approved design change.

## Observed inputs

- CiCd base: `66e3a5a3a0e9bb01dd161c19349953594e01a22f`.
- Current `builds-version`: `v6.0.6`, peeled commit
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- Timesheets main and existing CiCd gitlink:
  `bbb91319ee209333d29f07e53bd9b5e4adc40267`.
- Timesheets' own committed Builds gitlink:
  `39973bfccb26ae98a3d25856a8f85950fecdf02a`.

## Package-consumer coverage

Legacy `run-consumer-validation: true` selects
`scripts/pack-release-packages.py`, `validate-nuget-packages.py`, and
`validate-consumer-package-references.py`, with
`tools/release-packages.json` and `release_common.py`.

Retain exactly the six packable product IDs:
`Hexalith.Timesheets.{Contracts,Client,ReadModels,Server,Projections,Testing}`.
The checks require package/symbol pairs, package payload and dependency
boundaries, six independent restores from a private candidate feed, exact local
archive provenance and consumer build/execution. Consumer informational-version
assertions require the version actually compiled by the shared build. Packing
at a fixed substitute version would invalidate this check.

Shared `Github/lib/release_build.py` and `release_publish.py` cover release
identity and publication, but do not supply this full CI consumer contract.
Shared support belongs in Builds, with product-specific IDs, assertions and
consumer sources remaining module-owned. A prospective shared runner must:

- Pack the existing shared Release outputs with `--no-build --no-restore` and
  their evaluated version; do not compile the module again.
- Create/clean isolated package feeds, NuGet caches and consumer workspaces;
  generic feed/process plumbing stays out of the module custom action.
- Preserve independent consumer compilation/execution. These are consumer
  builds, distinct from repeating the main module build.
- Fail on wrong package sets, missing symbols, payload/dependency violations,
  wrong feed bytes, version mismatch and failing consumers.
- Use the existing shared package-mode/security configuration. Never add an
  audit waiver, signature bypass or broad source exemption to make the probes
  pass.

Target implementation boundaries are a shared Builds composite and library,
for example `Github/product-validation/action.yml`,
`Github/lib/product_validation.py`, and its tests under `Github/lib/tests/`.
Assess existing shared work before adding another interface; names above are
proposed locations, not an already published API.

## Complete action discovery

CiCd `tools/scan_discovery.py` statically follows all tracked supported source
literals/imports and fails unresolved execution. `evidence/25/discovery-probe.json`
records the real current scanner against hypothetical action text supplied
only in memory. Existing Timesheets scripts cannot be enabled unchanged:

- Candidate pack/consumer scripts use computed subprocess working directories.
- The configuration-only AppHost check imports the dynamic runtime fixture
  driver, even though its selected mode starts no resources.
- `unittest discover` is an unmodeled runner. Calling the fixture test file
  directly still fails on computed environment/working directory, reflective
  process mocks and dynamic Python execution.
- The selected-index test has complete discovery already.

Resolve the bounded shared execution/discovery model before wiring the action.
Changes to `tools/scan_discovery.py` and `tools/tests/test_scan.py` must model
actual supported targets and enumerate all tracked test sources; arbitrary
computed script targets, imports and path redirection must still fail closed.
Where reflective test machinery cannot be bounded, refactor module tests into
statically discoverable product checks while preserving their assertions.
Do not omit imported files, add scanner exclusions, replace coverage with an
assumed external-command allowlist, or copy generic plumbing into module code.

Qualification needs positive tests for the real intended Timesheets hook and
negative tests proving dynamic tracked-source execution remains rejected,
plus an actual cross-module duplicate scan. The existing Commons hook also
fails current discovery and is not evidence that this interface already works.

## Compatible package catalog

Timesheets pins SDK `11.0.100` but its product and consumers target `net10.0`.
The current shared catalog selects EventStore `5.1.1`. Locally cached Client
and Contracts archives at `5.1.1` contain only `lib/net11.0`; `4.2.0` contains
`lib/net10.0`. The current hosted AppHost build reports 25 missing-type errors
in ReadModels despite its explicit EventStore package references.

Local `dotnet-inspect` API diffs show no removed public Client/Contracts types
between `4.2.0` and `5.1.1`; this is initial compatibility evidence, not a full
graph/build proof. Preserve the module SDK and net10 consumer contract. Assess
a compatible catalog view in Builds `Props/Directory.Packages.props`, following
the existing net10 consumer patterns, and verify the entire module and six
consumers. Do not silently retarget products or add ineffective duplicate
PackageReferences. Catalog data may name products; the shared runtime remains
module-agnostic.

## Completion boundary

Publish required Builds changes through the central release process, select an
acceptable immutable release containing them, and qualify the final product
action against that exact contract. Registration/render/delivery follow only
after these checks. Shared publication identity checks do not replace the six
package-consumer contracts or compiled AppHost/fixture behavior.
