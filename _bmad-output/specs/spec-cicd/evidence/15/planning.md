# Story 15 investigation — 2026-11-16

This is planning evidence, not implementation or adoption evidence. Work is
isolated in `/home/administrator/projects/hexalith/cicd-story-15` on
`story/15-migrate-mcpcli`; the other active checkout is untouched.

## Inputs and revisions

- CiCd worktree base: `d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`.
- Recorded McpCli gitlink/checkout:
  `23072f04f423eea3f30456fe5af13d2d382624fe`.
- Fetched McpCli `origin/main` inspected through Git objects:
  `e2e3db7ba2d45d61feacc39c41b3051310fbc57f`.
- Released Builds `v6.0.6`:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- McpCli's legacy Builds gitlink:
  `99f7c86072ca7b35e3fbbaee4606a559a847805a`.
- Root-declared AI.Tools baseline checkout:
  `7ef8166ef87e1365f86d1a1b3aaf0235545177d4`.

Read canonical `SPEC.md`, story 15 in `stories.yaml`, the architecture spine,
the gate classification, setup documentation, pilot migration evidence,
McpCli guidance and its referenced LLM/Git baseline. Two read-only investigation
agents examined the migration contract and current product/test code. No
nested submodule was initialized. Re-fetch current mains before implementation;
these recorded revisions describe this investigation only.

## Administrative preflight

`preflight.json` records read-only GET requests using the command-local
maintainer profile `/home/administrator/.config/gh`. The default remains
`/home/administrator/.config/gh-cicd-agent`. Both profiles authenticated as
`jpiquot`; no GH_TOKEN/GITHUB_TOKEN override was present. Repository identity
is `Hexalith/Hexalith.McpCli`, ID `1379417482`, default branch `main`.
Account permission metadata is not proof of token permissions. GitHub's
connector does not cover the environment/secret/organization endpoints needed
for this preflight, so those checks used the intended local CLI profile.

Verified current state:

- Ruleset inventory is empty. Both exact AD-21 rulesets must be created.
- The complete environment inventory contains only `production`, with a
  reviewer and custom branch policies. `hexalith-release` does not yet exist;
  its secret-metadata endpoint returns 404. Preserve `production` until the
  new publication path is established.
- There is no repository Actions variable, including no release kill switch.
- Retention is 90 days, default CodeQL setup is not configured, Dependabot
  security updates are disabled, and push protection is enabled.
- Immutable releases are disabled; enable immediately after actual adoption.
- All five current `v*` refs have published releases; the release inventory
  contains no draft. Recheck before any cleanup; no deletion target has been
  identified.
- Actions/Dependabot registry pull-secret grants and the NuGet user-variable
  grant select Builds and the two pilots, excluding McpCli.

Unverified access/configuration:

- The org installation inventory confirms the `hexalith-cicd` installation
  `179966090` uses selected repositories and has the documented permissions.
  Its selected-repository endpoint returns **403**: "You must authenticate
  with an access token authorized to a GitHub App, a personal access token,
  or basic auth in order to list repositories for an installation." This
  leaves McpCli selection unverified; it does not establish exclusion. Use
  an authenticated installation-settings readback, as in the pilot, without
  obtaining the App key or broadening the token.
- Legacy CodeQL analyses return **404**; default setup's successful response
  does not prove that the separate analyses inventory is empty. Resolve
  through intended authorized access before declaring preconditions met.
- GitHub metadata cannot prove the NuGet policy or Zot ACL. Establish the
  additive `release.yml`/`hexalith-release` package-scoped policy and a distinct
  McpCli push identity through authenticated provider readbacks. Do not infer
  them from secret names. Identify legacy credential scopes before adoption.

## Product and gate map

Compilation uses `Hexalith.McpCli.slnx`, the module's `global.json` and net11.0
settings, and package references; only Builds is needed for this solution's
build imports. No active module audit waiver or `Directory.Build.rsp` was
found. Historical evidence containing audit flags is not an active waiver.

Keep the six ordinary Abstractions, Analyzers, Core, Manifest, Cli and Mcp test
projects. Keep package payload/consumer validation, conformance contract and
CLI/MCP loopback checks, enrolled-module artifact/operation coverage, catalog
benchmarking, and every live vector plus independent smoke/boundary case.
Consolidate these into registered product actions; avoid rerunning test classes
already executed by the unit stage merely to produce another receipt.

The proprietary-surface census scans cross-repository migration allowances,
approval receipts, historical evidence and workflow-derived invocation targets.
Its current combined gate is migration governance rather than execution of
McpCli's runtime contract. Remove that combined CI gate under CAP-10; retain
its manual maintenance artifacts. Runtime operation coverage remains enforced
by the C# suites and enrolled-module/conformance checks. Do not migrate approval
or story-evidence assertions into a product hook.

Retire agent-instructions-sync and agent/baseline prerequisites. Remove the
`CiWorkflowTests` class in `tools/live-topology/test_ci.py` while retaining its
runtime/product tests. Legacy release tests in `scripts/tests/` also assert
workflow YAML; separate useful package/consumer tests from retired release
orchestration before removing the latter. The root package.json/lockfile are
tool-only commitlint/semantic-release dependencies. Delivery owns workflows,
release/commitlint configuration, forbidden skill copies, instruction blocks
and deny entries: never edit these directly in the module.

## Aspire and stage 4

`tools/live-topology/ci.py:478` and the runtime profile require more than Docker:

- Linux amd64, Python venv/ensurepip and pinned jsonschema.
- Aspire CLI 13.6.5 with verified CLI/DCP/dashboard bytes.
- Dapr CLI/runtime 1.19.1 and exact Core/ASP.NET runtime 11.0.0 selection.
- OpenSSL 3, zlib/zstd, timeout, unshare, ip, curl and private
  user/PID/network/mount namespaces. The existing launcher permits a bounded
  sysctl adjustment only on disposable GitHub-hosted runners.
- Source-backed hosts from direct EventStore, Tenants, Parties and Platform
  checkouts at the runtime manifest's recorded revisions; no nested checkout.
- Digest-bound binaries extracted from Docker images and private runtime state.

`AspireTopologyFixture` refuses ordinary execution without the isolation
environment. Each live vector requires its own selected operation/bindings.
The current launcher treats skips as failures and validates the executed set;
plain shared `dotnet test` is not equivalent. Map Integration.Tests through
`tests.exclude` to an enabled product hook that executes the complete launcher.
The exclusion delegates execution; it does not skip tests.

Existing preparation/runner/job bounds are 40/300/360 minutes. The shared CI
default is 30 minutes, although its reusable API already has
`job-timeout-minutes`. The renderer does not expose it. A migrated total budget
must include shared stages, preparation, all cases and cleanup within six hours.
Do not silently shorten coverage to fit a timeout.

`ci.py:695` rebuilds the already built Integration.Tests with a fresh cache and
online all-dependency audits. Conformance loopback also rebuilds sample-mode
heads and can leave assets pointing at a deleted cache. Refactor to reuse the
shared module build while preserving package-byte/audit provenance; build
distinct source fixtures in isolated outputs. Do not wrap the old scripts and
claim one-build semantics. Generic environment support belongs in Builds;
module-specific topology assertions and launcher behavior belong in McpCli.

## Platform and publication contract

`release.yml:smoke-pair` tests identical staged package bytes on Linux, Windows
and macOS. Windows executes Core/Cli suites and requires seven named security
and mutation-safety tests to pass; macOS executes Cli. Preserve these product
behaviors when moving checks to CI. The shared schema/loader currently permits
only `windows-latest` extra jobs, and AD-12/rendering describes Windows only.
Retaining macOS needs an explicitly approved contract expansion, schema/loader,
prepare, renderer and qualification changes, released before module adoption.

The bespoke operator acceptance and evidence matching are replaced by the
central nightly contract; its release trusts green CI for the same source SHA,
packs once with audit and verifies publication. Preserve pair payload integrity,
offline CLI/MCP smoke and isolated analyzer-consumer behavior in CI actions.
Versioned publication remains the shared release's responsibility.

`tools/release-packages.json` declares exactly `Hexalith.McpCli.Abstractions`
and `Hexalith.McpCli`. Root props default `IsPackable=true`, and Core has no
override. Fix product project packability so generic release discovery does
not accidentally publish a third package. Confirm the complete evaluated pack
set and packaged tool dependencies rather than trusting the old manifest alone.

## Pre-adoption checker conflict

`pre-adoption-check.log` records the required literal command exiting 2 in the
module root because its nested Builds checkout is uninitialized. Unlike the
early pilots, the legacy pinned Builds commit contains a checker. Its
`Github/lib/local_check.py` still requires a matching initialized checkout,
committed `.github/hexalith-ci.json` and genuine delivered state. McpCli lacks
the latter two. Initializing a nested checkout is forbidden and would not
resolve the adoption-state requirement.

The pilot exception in `evidence/11/pre-adoption-check-resolution.md` explicitly
excludes every other module. A McpCli-specific human decision is needed before
any product-preparation push. Proposed bounded substitute: exact package-mode
builds/tests, applicable product package/consumer checks, policy/commit
validation and byte/mode/gitlink comparisons proving owned content unchanged
from freshly fetched main, with recorded inputs/results before each push.
After actual adoption, require the ordinary checker. No owned-file overlay,
symlink, fabricated delivered ref, audit/test bypass or alternate credential
is an equivalent substitute.

## Impact and verification plan

One user goal spans McpCli product preparation, shared runtime support,
CiCd's setup/render contract and authenticated adoption. Generic changes need
Builds fixtures/regressions on Python 3.12 and runner Python, its normal CI and
an acceptable release. Module tests need real Linux isolation and Windows/macOS
execution; fixtures cannot establish live acceptance. CiCd needs renderer tests,
repeat-render equality and full committed-candidate global/per-module checks.
Use `run-with-temp` for disposable jobs and preserve useful logs here.

No implementation, remote administration, product push or module adoption has
occurred. Planned external effects include reviewed stale-state cleanup if
actually needed, additive provisioning, product pushes, a shared Builds
release, CiCd registration, App delivery and immediate legacy-access cleanup.
Do not mark done before green adopted-main CI and the next genuine nightly
success or nothing-to-release result.
