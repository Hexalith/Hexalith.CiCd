# Story 18 implementation design

This design applies the human's two accepted recommendations. It records
implementation choices, not successful qualification. Preserve the frozen
intent in the story spec. Current source revisions and authentication observations
are in `planning.md` and its adjacent evidence.

## Shared configuration and preparation

Add two optional schema fields at the new Builds release:

```yaml
npmWorkspaces: []
dotnetTools: false
```

`npmWorkspaces` is a unique list of contained repository-relative directories
with committed package.json/package-lock.json pairs. `dotnetTools` enables a
module-owned `.config/dotnet-tools.json` containing exact tool versions. Both
are disabled/empty with `solution: none`. The renderer writes both defaults;
upgraded strict readers still require a complete document and do not silently
insert defaults. Update Builds `schemas/hexalith.ci.v1.json`,
`Github/lib/ci_config.py`, hand-authored Builds/sample configurations and
contract fixtures. Existing released consumers continue using their own
unchanged tagged readers. Explicit adoption enables nondefault fields; the
nightly bump's default-only new-key rule stays intact.

Extend `Github/lib/ci_environment.py` and carry validated settings through
`ci_pipeline.write_stage_outputs`, the `ci-unit-tests`/`ci-environment`
composites, shared `ci.yml` and `Github/prepare/action.yml`/its Linux preparation
script. Generic preparation happens once, after successful units in CI and in
the separate nightly-hook preparation. CI's guard already installs pinned Node
24; nightly preparation must establish the same version without caching or
repeating setup already performed in that job. Perform locked npm installation
without lifecycle scripts, verify signatures, and restore pinned .NET tools
through Builds' trusted `NuGet.ci.Config`. Reject missing locks/manifests,
unsafe paths, floating tool versions and failed installation. Browser setup
uses the workspace's locked Playwright executable, alongside existing built
.NET Playwright support. Absence of any supported browser tooling remains an
error. Hooks contain no package restoration, browser/tool installation, shared
building blocks or solution builds.

Projects' local tool manifest pins `Hexalith.FrontComposer.Cli` `6.0.0` with
command `frontcomposer`. Its official NuGet version index is retained in
`inspector-tool-versions.json`. A disposable installation through the released
trusted NuGet config and real `--help` both passed (exit 0);
`inspector-tool-verification.json` retains the exact commands and output.
The installed command supports project-based Release inspection without
`--build`. The temporary tool/packages/cache/CLI home were removed at job exit.
Consequently the hook needs no FrontComposer source checkout or source build.
Only add Aspire.Cli to the manifest if the final test runner actually needs
CLI operation; the programmatic test harness described below does not require
a redundant CLI installation.

## Product hooks and build outputs

Use `.github/actions/after-unit-tests/action.yml` for Projects-specific generated
artifact and package-consumer checks. Set Release/package generator-output
retention in `src/Hexalith.Projects.UI.Contracts/Hexalith.Projects.UI.Contracts.csproj`
so the single shared compile produces the inspector input. Adapt
`tests/tools/run-frontcomposer-inspect-gate.ps1` to invoke the restored tool
against that existing output with `--fail-on-warning`, never `--build`.
Keep the positive and negative ClientGenerationTests in the ordinary full
Client.Tests run; remove the duplicate focused OpenAPI invocation.

Adapt `tests/tools/run-package-dependency-gate.ps1` and
`scripts/pack-release-packages.py` to pack exact existing Release outputs using
the shared package/audit/no-response-file/trusted-config flags with no rebuild
or restore. Keep actual package inventory, dependency isolation, provenance and
payload assertions in `validate-nuget-packages.py` and all five real API
consumer checks in `validate-consumer-package-references.py`. A newly generated
consumer is the distinct product check, not a repeat solution build. Keep its
feed, packages and outputs in the wrapper's scratch directory. Replace legacy
publication/evidence machinery with the shared release contract.

Keep every ordinary C# suite. Retire workflow-YAML assertions, agent-tooling and
historical artifact/run/tag replay gates; preserve unrelated local tools and
historical evidence. Trace the real EventStore PostgreSQL restart/support
assertions invoked by G-6 to owning product tests; removing Projects' wrapper
must not remove those assertions. Do not move source identity/compilation
governance into product hooks.

## Separate package fixture and driver

Add nonpackable test-only projects:

- `tests/Hexalith.Projects.PackageFixtures.AppHost/` — Aspire SDK matching the
  existing `13.6.5` family; own Program, explicit fixture composition and
  prebuilt project metadata, one C# type per file.
- `tests/Hexalith.Projects.PackageFixtures/` — console test driver that owns
  fixture startup, bounded readiness, private credentials, browser execution,
  durable-state observations and teardown. It is invoked by the nightly hook,
  not silently discovered as an extra ordinary unit test.

Add both projects to `Hexalith.Projects.CI.slnx`. They and the existing actual
server/UI/workers/owner executable dependencies compile once through the normal
shared Release/package solution build. Leave `src/Hexalith.Projects.AppHost`,
its existing source-only fixture profiles and their DEBUG/SOURCE refusal intact.
The new path never changes defines to pretend source support exists in Release.

Use published Aspire.Hosting.Testing lifecycle APIs in the automated driver:
`DistributedApplicationFactory`, ResourceNotifications health waits, resource
endpoint APIs and awaited StopAsync/DisposeAsync. This is an automated fixture,
not an agent-operated substitute lifecycle command. Manual AppHost operation
still uses the Aspire skill's exact-target isolated CLI start/wait/stop rules.

Aspire 13.6.5 API inspection verified `IProjectMetadata.SuppressBuild`,
`BuildEnvironment`, `BuildWorkingDirectory` and `ProjectPath`.
Inject resource-specific metadata with `AddProject<TMetadata>(name, options)`.
Its project executable launch recipe emits `dotnet run --project ... --no-build
--configuration <AppHost configuration> --no-launch-profile` when build
suppression is set and DOTNET_WATCH is false. Supply prebuilt metadata for
every child, require Release outputs before startup and disable watch. Retain
ProjectResource shapes needed by published DevelopmentRouteCatalog and workload
binding APIs; do not undertake a Project v2 migration or invent ExecutableResource
overloads. Missing output must fail rather than rebuilding.

Run two distinct product phases, preserving the existing comparisons:

1. Compatibility fixtures: actual Projects server/UI/workers, EventStore and
   Tenants plus the existing role-specific sibling fixture host. Use a private
   Keycloak/Redis/Dapr runtime and fresh per-run credentials; run the existing
   startup/auth smoke and complete Chromium suite with the zero-skip reporter.
2. Actual-owner journey: actual owners including Folders server/workers,
   published route-catalog/workload-binding APIs and private fixture authority;
   preserve supported browser/read/write/recovery assertions and verify durable
   bootstrap/domain/audit/projection contents with a test-driver observer against
   the fixture-owned store. Seed via normal authenticated product commands and
   reads, not source-only diagnostics or direct domain-state writes.

The existing source qualifier's missing Release methods are private diagnostic
clients (`OwnerSourceReadClient` and `CatalogInvocationClient`). No new
EventStore API/package/release dependency has been established: the browser
product assertions use normal HTTP and fixture-owned persisted-state observation.
Use published WorkloadBindingAuthority and DevelopmentRouteCatalog APIs in the
new test-only authority host. Preserve the existing source diagnostic qualifier
unchanged; retire source-manifest/fleet-identity evidence from shared CI. If a
genuinely missing public product capability emerges, report its exact symbol
and required owner change; never extend the Projects preparation exception to
another module or substitute unpublished source for packages.

Add a literal `test:package` recipe in `tests/e2e/package.json` and invoke it
from `.github/actions/nightly/action.yml`; it runs the prepared driver and full
browser assertions. Retain the existing npm manifest/lock and local source
launcher. The scanner selects the complete npm test workspace even though the
driver itself is compiled C#. Runtime endpoint/control files and credentials
exist only in private scratch and are deleted after every outcome. Hook execution
reports failures to stdout/stderr; disable persisted browser reports/artifacts
for this hook while preserving zero-test/skip failure checks. No long-lived
password secret or early shared hook-secret API is needed.

The setup uses `Hexalith.Projects.CI.slnx`, Dapr, browsers, npm workspace
`tests/e2e`, the restored tool manifest, `after-unit-tests` and `nightly`, with
the default integration-test classification. Direct additional submodules are
EventStore, Tenants and Folders for actual executable hosts, and Platform for
package-mode linked helpers. Do not list FrontComposer after switching to the
released inspector. Set `registry: false`: use public Keycloak/Redis/Dapr
fixture images and the already-built owner executables, with no private image
dependency. Verify that resource inventory during qualification.
These dependency assumptions require a real package-mode build and full hook
run before adoption, with no checkout of nested dependencies.

## Duplicate-scan reachability

Extend `tools/scan_discovery.py` to understand literal npm workspace/script
execution and fixed installed Playwright invocation. Conservatively include
all tracked JS/TS in the referenced workspace, its configuration/global setup
and reporters; resolve relative imports and literal tsconfig aliases, including
Projects' `@support`, `@factories` and `@helpers`. Continue following supported
cross-language script literals. Use trusted TypeScript `6.0.3` (the version in
Projects' lock) as a locked static parser; never evaluate module configs or execute module scripts
to discover scope. Unresolved computed import/process/config execution fails
with a source diagnostic; conservative inclusion cannot waive unsafe paths.

Update `tools/scan.py`'s fixed policy/staging formats, `.jscpd.json`,
`tools/jscpd/package.json`/lock and scan documentation to include JavaScript and
TypeScript. Keep current thresholds, bounds, suppression rejection and
cross-module-only failure semantics. Exercise duplicate fragments reached only
through npm and aliased imports, plus unsupported/unsafe cases; opaque wrappers
are not an alternative to coverage.

## Contract, qualification and delivery

Record the additive configuration/scanner evolution in SPEC companions and
the architecture spine's AD-3/12/14 and scan contract, preserving unchanged
constraints. Include schema/default-loader agreement, default-disabled behavior,
path/manifest/lock/installation failures, one preparation per job, no rebuild,
fixture readiness and teardown failures, no production activation, real credential
isolation, complete browser/persisted-state assertions and scanner closure in
meaningful existing/new product or shared-runtime tests. Do not add module
workflow-text tests. Builds' own existing qualification verifies its produced
policy, at Python 3.12 and runner Python as appropriate.

Before any product preparation push use the approved Projects-only proof.
Shared runtime changes require the normal Builds qualification and an acceptable
released version before Projects' adoption. Commit setup/cause and render
together and run full CiCd candidate validation. No unpushed product commit may
be recorded as a delivered CiCd gitlink. Rebase/reapply only owned local changes
if other migrations advance main; never overwrite their registry entries.

Verify/provision AD-21 in order, authenticate App-only delivery and immediate
legacy scope cleanup, run normal post-adoption checking and wait for the genuine
next scheduled-night outcome. Story 11 acceptance and the new acceptable Builds
release are external prerequisites; local fixtures or a manual acceptance dispatch
do not replace either one.
