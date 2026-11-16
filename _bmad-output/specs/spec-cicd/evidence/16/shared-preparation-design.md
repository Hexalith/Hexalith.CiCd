# Story 16 shared preparation design

Planning evidence, 2026-11-16. No production implementation or external
configuration mutation is represented here. Builds was fetched read-only at
`fdda17c0a4538b0f7c99f813c20ca24b49006530`. The source and NuGet observations
below establish the prerequisite design; successful execution remains required.

## Existing implementation and actual producer

- `Github/lib/ci_pipeline.py`: `prepare_config` strictly loads configuration,
  initializes explicit direct dependencies through `initialize_submodules`, and
  shares build flags, evaluated project discovery, test classification and test
  execution with the local checker. Its separate build/unit/integration process
  invocations currently have no producer preparation.
- `Github/lib/local_check.py:run`: verifies committed/checked-out Builds and the
  exact tag, all required clean direct dependencies, and the ownership guard
  before product commands. It must continue to fetch/initialize nothing in caller
  checkouts. Its existing `revalidate` checks must surround new preparation too.
- `Github/lib/release_build.py:build_release`: initializes dependencies, then
  evaluates publication identities before audited restore/build. Producer imports
  must exist before that discovery, not only before restore. Its release
  configuration overrides audit/version flags and installs shared release targets.
- `Github/prepare/{action.yml,prepare_linux.py,prepare_windows.ps1}`: Linux uses
  shared Python functions; Windows intentionally consumes validated CI outputs
  rather than reparsing module configuration. Windows builds one solution and
  provisions no browser, Dapr or registry environment.
- Frozen `Github/prepare-module-build/prepare_module_build.py` already validates
  an exact local tool pin, invokes `prepare-build --mode package`, checks the
  producer's successful runtime-free result and validates seven environment
  values. Do not edit it or its composite. Its pure `read_json`, `real_path` and
  `verified_environment` functions can be reused by a workflow-owned new helper;
  its orchestration cannot be reused unmodified for the local checker because it
  fetches Platform tags and writes directly to `GITHUB_ENV`.

The actual public NuGet package `Hexalith.Builds.Module.Cli` **6.0.3** was read
in memory from the official flat-container URL. It is 41,042,724 bytes; its
nuspec repository commit is `99f7c86072ca7b35e3fbbaee4606a559a847805a`, equal to
tag `v6.0.3`. Runtime metadata selects `net11.0` and
`Microsoft.NETCore.App` `11.0.0`. That revision contains the real
`prepare-build` command. Conversations' SDK `11.0.100` supplies the producer's
required runtime; SDK 10 is not required merely to run this producer. This does
not qualify any other product-specific older-framework dependency.

`ModuleCommandApplication.CreatePrepareBuildCommand` accepts only manifest,
workspace, source/package mode and output format. There is no no-initialization
option. `WorkspaceRootResolver.ResolveAsync` climbs actual superprojects, checks
all direct declarations, can initialize Builds/Platform identity dependencies,
and in package mode can initialize an active module reference. The new helper
must preflight a standalone module Git root and exact initialized identity
checkouts so the producer cannot mutate a parent or initialize a dependency.
Use standalone temporary repository roots for preparation qualification; leave
the original CiCd umbrella and its nested module paths untouched.

## Why a preparation shim alone cannot work

Current Conversations main records:

| Input | Actual committed value |
| --- | --- |
| Builds gitlink | `39973bfccb26ae98a3d25856a8f85950fecdf02a` |
| Platform gitlink | `ddb1c0b141372a66d4a9d9c231d0041afbb7cd0c` |
| Module CLI pin | `6.0.3` |
| That Platform's tool range | `[6.0.5, 7.0.0-0)` |
| That Platform's Builds catalog | `e2bbbd0893f586e4d447ef8358ff747ea3d34435` (`v6.0.5`) |

Published Platform tags `v2.1.8`, `v2.1.9`, and latest `v2.1.10` all retain that
same tool range and Builds catalog. Latest `v2.1.10` resolves to
`215ae18c972e6ea8ccb27032dfc11a57b098f047` and was published on 2026-11-16.
A legitimate, qualified module-side update can select this existing released
Platform identity instead of untagged
`ddb1c0b141372a66d4a9d9c231d0041afbb7cd0c`. No Platform repository write or
early Platform migration is needed. The module CLI pin must also be updated.

Existing `PlatformIdentityResolver.ResolveAsync` emits `HXW009` unless the
module's staged Builds gitlink, clean checkout and Platform's CatalogCommit are
equal. It also rejects producer versions outside the truthful Platform range.
Consequently simply updating Platform or the CLI pin cannot support AD-6/AD-10's
independent future central Builds bumps. Altering an index/gitlink to impersonate
the old catalog, substituting a false identity, or dropping `HXW009` from the
existing package/source modes is not a solution.

The canonical AD precedence and the approved generic shared support require a
new explicit **managed-build authority**. The active package catalog comes from
the delivered exact Builds tag. The real Platform record and its historical
catalog pin remain separately represented and verified. This is a new producer
contract, not an assertion that the old tuple check passed.

## Generic opt-in interface

Add optional `moduleManifest` to `schemas/hexalith.ci.v1.json` and the stdlib
loader, default `null`. A non-null value is a safe repository-relative regular
JSON file path; reject it with `solution: none`. Keep old complete documents
without the new field valid: it is optional to the loader, while the renderer
materializes its pinned schema default. No module name or version is embedded in
the shared implementation. Coordinate the separate optional `windowsCheckout`
field with `windows-and-fixture-design.md`.

Emit `module-manifest` through `ci_pipeline.write_outputs`, `Github/ci-prepare`
and reusable `ci.yml` job/workflow outputs. Prefix it with test-only module-root
exactly as solution/global-json are prefixed; encode disabled as an empty output.
Pass the output to remote `Github/prepare` in the rendered Windows caller. The
Windows path validates and consumes this trusted output; it does not load the CI
document or discover whether preparation should run.

## New producer command and authority representation

Add `prepare-managed-build` to the CLI, backed by a new typed service/context in
`Hexalith.Builds.Tooling/Workspace/`. Keep `WorkspaceMode.Package` and
`EnrolledReferenceMode=package`; do not add a third mode that existing callers
would accidentally interpret as source mode. Existing `prepare-build` and
source/package APIs retain their exact tuple checks and behavior.

The managed context binds repository, frozen module revision, exact Builds tag
and commit, accepted CiCd delivered revision, and the real Platform identity and
its catalog commit. Acquire its authority through the existing fixed anonymous
CiCd delivered-state transport and successful ownership comparison; configuration
alone cannot assert acceptance. The Python guard can retain the secret-free
validated receipt from `Comparison.delivered_sha`, its perimeter document, exact
actual tree and the verified Builds tag rather than repeating independent
network comparisons. Local uses its successful `guard.run` result; release
uses its already accepted delivered-sha/drift result. Windows consumes the
validated, revision-bound CI receipt in addition to the existing path outputs.
Validate the receipt and current checkout/tag/configuration identities again
before executing the producer; never trust a module-authored context file as an
authority grant. Builds' own sample keeps an explicitly test-only fixture source.

Introduce an optional managed authority property on `SourceMapping`, omitted
from JSON and the legacy hash payload when absent. Its new hash payload includes
the complete managed authority, active catalog commit and truthful Platform
identity, so changing either invalidates the mapping. Preserve the original
`PlatformIdentity.CatalogCommit` value; add a single effective catalog selection
accessor that returns the authenticated managed Builds commit only in the new
context and otherwise returns the existing Platform pin. Mark that computed
accessor `JsonIgnore` so its mere addition does not change old serialized data.

Update `CatalogVersionMaterializer` to materialize and validate its snapshot
against that effective catalog accessor, including its per-project evaluations
and import closure. `CatalogVersionSnapshot.CatalogCommit` remains the actual
catalog used. `SourceMappingMaterializer` and final validation must bind the
managed authority and effective catalog alongside the unchanged source/package
selection checks. `CatalogVersionValidationTask` must continue to reject
package and restored-assets drift from the selected catalog. Nothing changes
existing runtime composition authority implicitly: only the new runtime-free
build preparation entrypoint creates managed authority.

Managed validation replaces the equality-to-Platform requirement with explicit
new checks, never an ignored finding: root HEAD/index gitlink, clean direct
Builds checkout, local exact tag and accepted delivered tag/commit all agree;
the actual Platform checkout still equals its committed identity, has a real
release tag and clean contents, supplies its real pin and accepts the actual
new CLI version. Missing, changed, unaccepted, differently scoped or malformed
authority fails before project evaluation. No tool-created Git initialization
or checkout retargeting is permitted.

The existing published 6.0.3 command is adequate only for its old contract. This
new command requires a minor Builds/CLI release within the existing Platform
`<7` tool range. Qualify it first
through existing source CLI command tests/local isolated package qualification,
then publish the shared release and update the module's exact tool pin. Do not
invent a published version or add a production fallback that builds arbitrary
source CLI projects from module input.

## Honest pre-adoption qualification

The human-approved Conversations-only pre-adoption verifier cannot supply an
accepted delivered receipt before actual adoption. It must not reuse an accepted
managed context with invented fields. Add a separate runtime-free
`prepare-qualified-build` command and Python qualification entrypoint that share
the managed service's safe path, tool, mapping and catalog machinery but require
an explicit `candidate-qualification` authority. Its purpose is exact-input local
product qualification only. Production CI, the normal checker, Windows prepare
and release accept only `accepted-delivery` authority and reject qualification
contexts before SDK/product execution. No module configuration knob can enable
qualification, and no qualification artifact makes adoption or publication pass.

The qualification context records these concrete, checked fields:

| Field | Meaning and required evidence |
| --- | --- |
| `schema`, `kind` | A closed versioned context schema and literal `candidate-qualification`. |
| `repository`, `moduleRoot` | The exact Conversations origin and a real standalone temporary Git root; no enclosing superproject. |
| `baselineHead`, `productHead` | Freshly fetched remote main and the exact clean committed local product revision being tested. Recheck both around the run and immediately before a push. |
| `originalBuildsGitlink` | The actual mode/OID in both baseline and product HEAD/index. They must agree; this is deliberately independent of the qualified execution/catalog checkout. |
| `ownedBaselineDigest`, `ownedProductDigest` | Equal byte/mode/gitlink inventories of the existing owned perimeter, plus an explicit allowed product-diff inventory and ordinary action/audit/commit-policy results. The mask comes from canonical ownership rules, not from a module-authored allowlist. |
| `cicdCandidate`, `candidateTree` | Canonical local CiCd commit/tree containing registration, pinned version and reproducible render, independently validated as candidate content. Its Conversations gitlink names the remotely available baseline, not the unpushed product head. |
| `renderedConfigPath`, `renderedConfigBlob`, `renderedConfigDigest` | Exact candidate rendered CI document. Read it from Git into memory; never write it into the unadopted module's owned paths. Validate through the released schema/loader. |
| `qualifiedBuildsTag`, `qualifiedBuildsCommit`, `qualifiedBuildsRoot` | A separate real clean Git checkout of the acceptable published immutable Builds release, exact tag/commit and ancestor evidence. It is outside the module root and differs truthfully from the original owned gitlink when necessary. |
| `producerPin`, `producerSourceCommit` | The exact module tool-manifest version restored through trusted NuGet configuration and its released package provenance, not a source-built substitute. |
| `platformIdentity`, `platformCatalogCommit` | The actual qualified Platform checkout/tag/gitlink and its real record; a permitted product-side Platform update is recorded as such. Its historical catalog is not relabelled as the active qualified catalog. |
| `activeCatalogCommit`, `configurationDigest` | The qualified Builds release's actual catalog selection and the exact validated prospective configuration. Both participate in the producer mapping hash. |

The new qualification orchestration reads actual Git objects/checkouts for these
identities, verifies the candidate's tagged contract/render and product ownership
equivalence, and validates the separately selected released catalog. Reuse the
Python renderer, schema loader and perimeter code for those checks; do not build
a second renderer or ownership parser in .NET. The producer's typed service
independently binds the supplied context to actual source, tag, catalog and
Platform identities and hashes the checked authority. It must not report that
the module's original Builds gitlink equals this external checkout.
Its generated mapping explicitly carries both the original recorded pin and the
external qualified catalog root/commit under the qualification authority. Its
catalog reader and generated `HexalithBuildsRoot` selection consume that real
external root only for this explicit context. They never retarget the original
gitlink, index or checkout, and the producer supplies all generated imports,
mapping metadata and validation targets normally. Existing source/package
commands remain unchanged and can still reject the legacy tuple.

The verifier creates a standalone module checkout at `productHead` beneath
`TMPDIR`, a separate exact released Builds checkout and the necessary direct
identity dependencies, and restores the exact newly published tool. It constructs
`PreparedConfig` in memory from the committed candidate render and uses the same
shared flags, build, evaluated classifier, all applicable product checks and
strict result verification. No `.github/hexalith-ci.json` overlay, fake delivered
ref, replacement Git index, changed owned file or source-tool fallback is created.
The original CiCd/module workspaces are not qualification workspaces.

This proves candidate-content and product results, not full live adoption
validation: live action availability can remain false until the protected module
push publishes the tested actions. After qualification succeeds, recheck the
fresh baseline and exact tested head, then push only the product commit with the
protected module credential under the approved exception. Only afterward update
the CiCd module gitlink to that now-published head, commit the final adoption
candidate and rerun the required exact committed/global/live checks. Do not commit
a superproject gitlink pointing to an unpushed product revision.

Each qualification context is single-run, source/release/candidate bound and
cannot resume against changed inputs. Keep its JSON receipt, inventory hashes,
exact revisions and useful logs outside scratch; never save credentials. Remove
producer outputs, tools, package caches, checkouts and any worktree registrations
when the wrapped verifier and all children finish, including failure. After real
App adoption the exception expires: use only accepted-delivery contexts and the
normal required checker. Tests must prove that missing/mismatched identities,
owned drift, stale baseline and attempts to submit a qualification receipt to
normal CI/checker/release all fail, and that successful qualification changes no
owned bytes/index/gitlinks or external state.

## New shared helper and lifecycle

Create workflow-owned `Github/lib/module_preparation.py` with a small typed API:

```python
prepare_environment(prepared, authority, temporary_root, *, fetch_tags=False)
    -> BuildEnvironment
verify_environment(prepared, authority, environment) -> None
```

`BuildEnvironment` records the private producer workspace, exact seven exported
values and verified input/output hashes. Disabled configuration returns an empty
environment without SDK/tool/network work. Read duplicate-safe JSON; reject
symlinks/reparse points, traversal/control characters, unavailable declared
identities, dirty/mismatched gitlinks, floating tool versions, roll-forward,
version mismatches, source mode, runtime/run IDs, unknown environment keys,
missing/escaping imports, hash mismatches and non-Release preparation. Restore
the exact manifest through the trusted NuGet configuration; invoke the real new
command without a shell. Export only after every check succeeds. Never evaluate
producer text or construct mapping metadata in Python.

Preserve a single producer workspace through all project evaluations, restore,
build, unit tests, integration tests and product hooks of a job. Independent
Actions processes consume a validated private state/receipt and exported seven
values; validate original identities and import bytes before reuse. Local uses
one context spanning build and unit tests and restores its process environment
and removes scratch on completion/failure. No local fetch/init is added: absent
Platform tags produce explicit preparation guidance. Hosted paths may fetch only
identity tags with recursion disabled after required direct dependencies are
initialized. Runner scratch survives until the last consuming job step and is
cleaned through an always-run cleanup or the runner's owned job lifecycle.

Ordering is guard, validated configuration/direct dependencies, SDK, managed
preparation, then the first MSBuild evaluation/restore. Apply this to shared CI,
the local checker, Linux nightly prepare, Windows prepare and release build.
Release preparation happens before `discover_projects`; its version/audit flags
remain authoritative. Hook actions receive prepared outputs and do no checkout,
build, environment provisioning or preparation themselves.

At the inspected producer revision the five import names are
`CustomBeforeDirectoryBuildProps`, `CustomAfterMicrosoftCommonProps`,
`CustomBeforeDirectoryBuildTargets`, `CustomAfterDirectoryBuildTargets`, and
`AfterMicrosoftNETSdkTargets`. Release currently uses distinct
`CustomAfterMicrosoftCommonTargets` and
`CustomAfterMicrosoftCommonCrossTargetingTargets`; there is no direct key
collision in these sources. Still prove both producer final validation and
shared release audit/container targets execute together. Reject conflicting
ambient import overrides rather than silently replacing either chain.

## Required implementation files and qualification

1. New managed context/service and CLI command; narrow resolver/catalog/hash
   integration in `src/libraries/Hexalith.Builds.Tooling/Workspace/` and
   `ModuleCommandApplication.cs`. Preserve frozen legacy `Github/` bytes.
2. Schema/loader optional fields; new Python helper; CI preparation outputs and
   orchestration; local and release integration; Windows input consumption;
   renderer caller outputs and setup documentation. Extend architecture AD-6,
   AD-10 and build-stage descriptions to distinguish active managed catalog from
   truthful Platform provenance.
3. Behavioral .NET tests: old package/source rejection and old serialized hashes
   unchanged; new accepted managed catalog differing from Platform succeeds;
   each wrong/missing/stale authority component fails; changed active catalog,
   Platform pin, imports, conditional package selection or restored assets
   fails; actual producer imports precede evaluation; no resources/run ID or
   dependency mutation. Exercise CLI commands and real Git fixtures.
4. Python loader/schema parity tests for omitted/null/enabled values and unsafe
   paths; meaningful controlled producer failures prove no environment export or
   product command on failure; CI/local/Windows/release reuse one preparation,
   retain default-null behavior and preserve all mandatory flags. Execute actual
   composites rather than workflow-text assertions.
5. Real isolated package-tool restore/invocation and actual .NET solution
   evaluation/build/test classification, native protected Windows execution,
   catalog-bump demonstration without Platform mutation, and audited release
   discovery/build. Retain exact revisions, selected catalog and true Platform
   identity in proof. Source test seams are not production fallback contracts.

No new user choice about knob names or implementation structure is required.
The canonical AD precedence settles active catalog authority; the user approved
necessary generic shared prerequisites. Any finding that this explicit new
authority cannot preserve an existing product assertion must be reported as a
concrete remaining conflict, not worked around with metadata or skipped tests.
