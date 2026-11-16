# Story 16 module investigation

Read-only source investigation on 2026-11-16. No builds, tests, product edits,
pushes, dispatches or external configuration writes were performed.

## Source identities

- Conversations current `origin/main`: `9e24c280efd5e9c13826eab9bc8b8b687a7bee09`.
- CiCd's pinned Conversations checkout: `c34dc3c1e0469765c75ea608f2960381f649579c`.
- Current Conversations main records Builds `39973bfccb26ae98a3d25856a8f85950fecdf02a`.
- CiCd `builds-version` is `v6.0.6`, peeled to `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- Read module `AGENTS.md` and the initialized direct root AI.Tools baseline/Git
  guidance. No nested submodules were initialized.

## Current build contract

`global.json` selects SDK `11.0.100`, `latestPatch`, Microsoft.Testing.Platform.
`Directory.Build.props` selects `net11.0`. Preserve those product selections.
`Hexalith.Conversations.slnx` contains eight product projects, ten test projects,
two TestSupport helpers and the deletion-conformance tool. It contains no sibling
repository projects. Source-mode sibling references in AppHost/tests are gated;
the package graph should not need sibling source checkouts after forbidden
planning/evidence tests are retired.

However, this is not presently a plain-build module. Root
`Directory.Build.props:ValidateConversationsEnrollmentMapping` requires
`HexalithSourceMappingHash`, `HexalithSourceMappingApplies=true`, explicit
`UseHexalithProjectReferences`, and invokes producer validation targets.
The current legacy workflow invokes Builds `Github/prepare-module-build`.
Its `prepare_module_build.py` restores exact `.config/dotnet-tools.json` tool
`hexalith.builds.module.cli` 6.0.3 and invokes its package `prepare-build` command.
It validates and exports five generated MSBuild imports plus
`HEXALITH_SOURCE_MAPPING_HASH` and `Configuration=Release`.

At v6.0.6, `Github/lib/ci_pipeline.py:build_flags/restore_and_build` supplies
Release, warning/analyzer policy, package mode, audit-off CI and restore config.
It does not invoke module-tool preparation. `Github/prepare/prepare_windows.ps1`
has the same plain-build shape. Neither provides the current required producer
imports. SDK setup uses the module's global.json and has no explicit SDK 10 cap;
actual SDK 11 restore/build/test compatibility remains untested.

A possible product-side adaptation is to provide the standard central build
imports for ordinary package mode while retaining explicit producer mapping in
source mode. That is not proven safe by static inspection: AppHost test metadata
and runtime helpers also require that mapping. Do not just set a fake hash,
remove validation to claim success, or add a late hook that prepares imports
after the shared build has already failed. Alternative: extend Builds' shared
build/local-check preparation interface, then release and adopt the new tag.
That changes shared architecture and requires an explicit scope decision.

## Product lanes that must survive

- Standard unit, integration and AppHost projects: classify from evaluated
  solution membership. Keep TestSupport.Tests on Linux because its tests have
  Linux-only symlink/path cases. Run it additionally on Windows for actual
  descendant/orphan cleanup and cancellation behavior (`GitFactsTests.cs`).
- `tests/Hexalith.Conversations.Admin.Web.Tests`: real Chromium rendering,
  accessibility and responsive assertions. `Fixtures/PlaywrightFixture.cs`
  launches Chromium. Set `browsers: true` and move this project to
  `tests.integration`; shared stage 4 can run it after shared browser setup,
  eliminating its old install/build job. Do not call `tests/install-playwright.ps1`
  from a custom action because it can rebuild/setup.
- `tests/Hexalith.Conversations.AppHost.Tests`: real runtime test enables itself
  automatically in GitHub Actions and runs Dapr-backed hosts. `dapr: true` is
  needed for that lane. `ConversationsAppHostRuntimeBoundaryTest.cs` reads
  producer-selected enrollment metadata/environment, evaluates and builds the
  Builds-owned packaged EventStore gateway host, checks its revision and SDK
  provenance, then starts the real boundary test. Keep actual command-admission
  behavior; do not misclassify it as an evidence-only gate. Shared preparation
  compatibility must address its current mapping/build assumptions explicitly.
- Both conformance projects contain actual product suites mixed with planning,
  story, evidence and repository-authority checks. Classify by assertions, remove
  forbidden tests and their linked Compile entries rather than preserving the
  old workflow's dozens of `-class-`/`-method-` runtime exclusions.
- `tests/fixtures/Hexalith.Conversations.MinimalModule`: seven genuine public
  package compatibility assertions, including registered-command behavior.
  Current `minimal-module-compatibility` job builds that fixture independently
  using `tests/compatibility/MinimalModule/Framework.props` and
  `RegisteredCommand.targets`, successor locks and `verify_results.py`.
  Its README explicitly requires the frozen fixture remain outside the root
  solution with isolated package/xUnit configuration. At this source the overlay
  selects EventStore 5.1.0 and checks it against direct Builds; v6.0.6 selects
  5.1.1. Successor overlay/locks require deliberate product qualification.

The minimal fixture cannot simply become a build-free hook: it is not built by
the root solution. A product-specific dependency/build target could potentially
build it once from shared build while leaving its files outside the root .slnx,
but feasibility, isolation, test discovery and contract compatibility are not
established. Alternatives require either carefully adapting its product build
contract or extending shared support for independently configured fixtures.
Preserve all seven assertions and frozen historical fixture bytes either way.

**More concrete adapter option:** add a new non-test adapter project under
`tests/compatibility/MinimalModule/`, and include only that adapter in the root
solution. Its `ProjectReference` edges can select both the frozen fixture test
and AppHost projects with `ReferenceOutputAssembly=false`, forwarding the
existing compatibility overlay, framework and successor-lock properties via
`AdditionalProperties`, while removing the producer mapping import globals via
`GlobalPropertiesToRemove`. The original fixture has its own self-contained
Directory.Build.props, disables central package props and uses explicit version
properties; its original files need not change. A build-free
`.github/actions/after-unit-tests/action.yml` can execute its seven-test DLL and
the existing strict XML verifier. This is a structurally plausible normal
product build adapter, not yet a need to change shared architecture. Acceptance
must prove one root restore/build covers all four fixture projects, isolated
mapping/package/lock selection survives restore graph propagation, and all seven
assertions pass. Deliberate successor lock/overlay requalification remains
required for the selected Builds catalog. Do not claim this proof from static
inspection alone.

**Producer preparation differs:** a module-side target that calls the CLI during
build is too late to supply evaluation-time imports and independent classifier
project evaluation; a recursive outer build would duplicate framework/build
orchestration. No existing product-side static import was found that produces
the verified mapping without invoking the tool. A new legitimate package-mode
import path might be designed, but merely bypassing the root guard or inventing
producer metadata would not preserve its validation. Shared pre-build enrollment
support is currently the concrete architecture-changing alternative.

## Windows action proposal and checkout conflict

After resolving build and checkout prerequisites, add module-owned
`.github/actions/testsupport-windows/action.yml`, composite with `pwsh` steps to
evaluate TestSupport/TestSupport.Tests pack/publish properties and run the built
Release/net11.0 TestSupport.Tests DLL with `-automated sync -failSkips`.
It must not checkout, build, call Builds or setup an environment. Enable
`jobs.testsupport-windows.runner: windows-latest`; keep this project in Linux's
ordinary unit set rather than excluding Linux coverage. The rendered job must
consume shared CI solution/global-json/submodules outputs.

Current Windows workflow does protected sparse checkout before any source is
expanded. `tools/checkout-windows.py` identifies exactly eighteen historical
HTTP-cache files with `$ps:` in their names, validates other current paths with
native protected Windows Git, and excludes those exact immutable archives.
Shared `Github/prepare/action.yml` instead begins with ordinary full
actions/checkout and validates Windows paths only afterward. A custom action
cannot repair a failure that happens before it runs. This is a concrete
compatibility risk requiring Windows execution or an authorized product archive
layout change/shared checkout enhancement; do not disable `core.protectNTFS` or
claim full checkout is qualified. Retire the module's checkout-policy test gate
under CAP-10 while preserving product files and safe checkout behavior.

## Retirement and waiver inventory

- Root `package.json` dependencies are only commitlint/semantic-release; its
  Python test wrapper does not justify retaining Node release tooling. Retire
  package.json/package-lock and obsolete release scripts/tests with delivery's
  owned config deletion. Actual hooks are `.githooks/commit-msg` (commitlint)
  and `.githooks/pre-commit` (whitespace), not `.husky/`; preserve unrelated hook
  content. No tracked Directory.Build.rsp is present at current main.
- Root `Directory.Build.props` and frozen minimal fixture Directory.Build.props
  waive NU1901–NU1904 through WarningsNotAsErrors. Remove module-owned waivers;
  any justified waiver belongs only in Builds Props and a released selected pin.
- Obvious forbidden checks include repository submodule/Windows checkout policy,
  release-tooling/workflow-text tests, and named planning/evidence authority
  classes. Known YAML assertions are in
  `tests/tooling/test_minimal_module_compatibility_overlay.py`,
  `tests/tooling/test_release_tooling.py`, and conformance
  `PackageEnvironmentAuthorityV18ValidationTest.cs` (historical workflow blobs).
  Inspect mixed files at method level to preserve real product assertions.

## Pre-push prerequisite

The current Builds pin DOES contain `check.py` (tree blob
`ca57bf26f0a7b327854aa6219e404dc98b34a810`). Current Conversations main does NOT
contain `.github/hexalith-ci.json`. Builds `Github/lib/local_check.py` verifies
the exact committed gitlink and separate checkout, then loads that missing
configuration before product commands. Therefore normal pre-adoption check
cannot pass as-is. No normal checker was executed and no exception is assumed;
the earlier story 11 human decision was pilot-specific. Do not create or edit
owned module configuration to bootstrap a product push. Resolve this ordering
conflict explicitly before any preparation push.
