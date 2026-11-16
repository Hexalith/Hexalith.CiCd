# Story 14 planning

Planning only, 2026-11-16. No product files, production registration, remote
configuration, releases or credentials were changed. The original workspace is
preserved. Work continues in the clean worktree
`/home/administrator/projects/hexalith/cicd-story-14`, branch
`story/14-migrate-agents`, created from freshly fetched CiCd main
`d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`. Other migration sessions have separate
worktrees; refresh and preserve their changes before a later push.

## Sources and exact identities

- `stories.yaml`, story `14`: Migrate Agents, CAP-10 and CAP-16, AD-21 ordering.
- `SPEC.md`, `gate-classification.md`, `pipeline-stages.md`, `enforcement.md`
  and architecture `ARCHITECTURE-SPINE.md`, especially AD-1/4/7/13/14/15/20/21.
- Fresh Agents main: `895039d8513363424882b3b7d64bca574fddc43b`; fetched with the
  protected module-agent credential. Product branch `story/14-prepare-agents`.
- Agents' committed Builds gitlink:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`. Its legacy CI still references
  `264e17d3185c87b72b0757dd66a13040793756bb`; delivery must replace that policy.
- Agents' AI.Tools gitlink:
  `736687b79c1e4fa8beabdab75c4675bb76c466b9`. Read its LLM and Git instructions
  from that exact Git object. Its pre-push guidance is conditional on adoption,
  but the human-supplied CiCd workspace rule unconditionally requires the
  checker. Resolve this before a preparation push; do not silently transfer the
  pilots' explicitly limited exception.
- Current central pin: `v6.0.6`. It must be refreshed from current remote main
  before implementation; no version number for the required new release is
  fabricated here.
- SDK `11.0.100`, `net11.0`, C# 15. The local SDK is installed. Preserve all
  three and Microsoft.Testing.Platform.

Story 11 is still in progress awaiting its genuine scheduled-night checkpoint.
Preparation can proceed after approval, but Agents adoption must wait for that
checkpoint's acceptance. Other migration stories are not implicitly accepted.

## Read-only maintainer preflight

`planning-preflight.py` records exact GETs, statuses, permission metadata and
sanitized identities in `planning-preflight.json`. Default profile remains
`/home/administrator/.config/gh-cicd-agent`; no inherited GH_TOKEN/GITHUB_TOKEN
override was present. Administrative reads used command-local
`/home/administrator/.config/gh`, identifying `jpiquot`, ID `6775094`.
Account `admin: true` is not evidence of token API permission.

Observed state:

| Check | Result |
| --- | --- |
| Public repo/main identity | Correct |
| Rulesets including parents | Empty inventory; create exact AD-21 main and v* rulesets after stale-state assessment |
| Environments | Only `production`; `hexalith-release` absent from successful inventory |
| Publish switch | Exactly `true` |
| Retention | 90 days |
| CodeQL default setup | `not-configured` |
| Dependabot security updates | `enabled: false` |
| Push protection | Enabled |
| Immutable releases | Off; enable immediately after actual adoption |
| New org variable and pull-secret grants | Agents absent from successful Actions/Dependabot selection inventories |
| App repository selection | Unverified: installation inventory request refused, not evidence of absence |
| NuGet policy / Zot principal | Not verified by these GitHub reads; inspect existing authenticated NuGet/registry access before provisioning |

Under the intended maintainer profile,
`GET user/installations/179966090/repositories?per_page=100` returned HTTP 403:
“You must authenticate with an access token authorized to a GitHub App, a
personal access token, or basic auth in order to list repositories for an
installation.” The CLI also reports a `read:user` scope requirement. Preserve
this refusal; use existing permitted settings readback or maintainer attestation
and delivery's own scoped checks, without broadening credentials or reading the
App key. No automatic token refresh was performed.

There are three draft releases: `v2.0.0` (ID `446267591`), `v1.2.2`
(`426297010`) and `v1.2.1` (`426274664`). Tags `v1.2.0` and `v1.1.0` have no
published release. Before removing stale drafts/tags, inspect original artifacts,
publication inventory and source identities. Preserve published packages and
published releases, including `v2.0.2`. Keep legacy publication access until
authenticated adoption, then perform AD-21 cleanup immediately.

## Checker bootstrap decision

### Approved resolution, 2026-11-16

The human approved the proposed Agents-only preparation proof and this spec
with **"approve and stop"**. Before actual adoption only, require full
package-mode builds/tests at original floors, actual package/consumer checks,
released audit/commit validation and exact owned-byte/mode/gitlink preservation
against freshly fetched main. Save exact base/head revisions and passing
results before each preparation push. After delivery, require the normal
`python3 references/Hexalith.Builds/check.py` in a standalone module clone.
This approval grants no owned-file edits, nested initialization, weaker checks
or credential substitution. The spec is ready-for-dev; implementation has not
started. The diagnosis and original proposal below remain historical evidence.

### Diagnosis and original proposal

`checker-bootstrap.json` records an actual read-only invocation in a standalone
disposable clone, with a separate direct Builds checkout at the committed
gitlink. Both checkouts were clean. The required command exits 1 before guard,
build or tests because `.github/hexalith-ci.json` does not exist. Scratch was
created beneath `run-with-temp`'s TMPDIR and removed by the wrapper.

The existing checker also requires matching tagged configuration and genuine
accepted delivered state. Product preparation precedes delivery, and no direct
edit of owned config/gitlink or fake delivered state is allowed. The proposed
Agents-only preparation proof is: full package-mode Release build and five
test suites at their original floors, actual package/isolated-consumer checks,
applicable product regressions, released audit/commit validation, and an exact
byte/mode/gitlink comparison against freshly fetched main proving every owned
portion unchanged. Record exact base/head/results before each preparation
push. After actual adoption the ordinary checker is mandatory, in a standalone
module clone. This proposal was subsequently approved as recorded above;
approval is not completed product verification.

## Gate inventory and implementation design

Current `ci.yml` has legacy shared CI plus `agents-policy`. Keep compilation,
all real product suites, package authority, stable EventStore capability floor,
dependency-mode rejection behavior, actual package inventory/static assets and
isolated consumer checks. Delete the pinned-source gate, tool-only npm gate,
workflow-text assertions, story receipts/anchors and redundant full/focused
reruns. Never delete runtime tests just because a class has a story name.

1. **Shared test floors:** Extend Builds `schemas/hexalith.ci.v1.json`,
   `Github/lib/ci_config.py` and `ci_pipeline.py` with
   `tests.minimumExpectedTests` (project-to-positive-integer map; renderer
   default `{}`) and `tests.failSkips` (renderer default `false`). New tagged
   documents explicitly contain both fields; loaders stay strict and never
   insert runtime defaults. Update public fixtures, samples and
   `Github/lib/tests/test_{ci_config,ci_pipeline,local_check}.py` accordingly.
   All five Agents projects stay in shared stage 3, `tests.exclude: {}`.
   Original Release floors are Contracts 529, Client 6, Agents 787, Server 549,
   UI 1073. Apply the same executor options to CI and local checking, finish a
   failing project's tests, then stop before its successor. Keep
   `--stop-on-fail off`. Unsupported runner/framework combinations, unknown or
   excluded projects, booleans and nonpositive minima must fail explicitly.
   There is no demonstrated need to lower any floor.

2. **Product authority and dependency rejection:** Existing
   `PackageVersionCentralizationTests.cs` has synthetic validator tests but
   lacks actual whole-repository coverage. Add a product test calling the
   existing full Builds validator with its exact
   `eng/package-authority-exclusions.txt`. This runs in stage 3, outside the
   custom action. Add evaluation-only probes in
   `BuildContractConformanceTests.cs` for
   `FailReleaseWithHexalithProjectReferences`,
   `FailPackWithHexalithProjectReferences`, and `CheckSourceDependencies`,
   retaining the original failure properties/diagnostics without restore,
   compile or pack. Extract stable EventStore >=3.128.3 capability validation
   from `eng/verify-story-5.2.ps1` into a neutral product script and update its
   executable behavioral tests.

3. **Package hook:** New `.github/actions/after-unit-tests/action.yml` invokes
   module-specific validation against the existing Release output. Adapt
   `scripts/pack-release-packages.py` with explicit no-build/no-restore mode;
   preserve exact six-package inventory, caller-owned unrelated archive
   protection, `validate-nuget-packages.py`, `release_package_integrity.py`,
   `validate-consumer-package-references.py`, `eng/consumer-executable-assets.json`
   and `eng/ui-static-assets/**`. An isolated consumer's own compile remains
   a product check; never rebuild Agents in the hook. Use cleaned temporary
   package feeds/consumer outputs and omit retained receipts. Normal static
   Python imports and explicit supported subprocess entrypoints must make the
   hook's complete reachable source discoverable by the existing scan. Do not
   call Builds from the hook, evade discovery or weaken the scan. If genuine
   shared fragments are detected, hoist them through a shared stage before
   enabling the action.

4. **Delete CI/tooling/evidence gates:** In `PackageInventoryTests.cs`, retain
   actual package inventory but delete the four workflow-reading methods and
   final script-text meta-test. Delete `TraceabilityManifestTests.cs`,
   `tests/tooling/release_authentication_test.py` and
   `dependency_commit_contract_test.py`. Split blanket tooling discovery by
   the gate rule; retain real product archive/import behavior and useful local
   regression qualification, removing pipeline/story-evidence assertions from
   hosted gates. Historical source-mapping story runners 5.3/5.4/5.9/6.1 are
   not current CI gates and must not be enabled in the new hook. Do not add
   previously dormant Node test gates; retain the JS product and its analysis.
   Remove tool-only root `package.json`/lockfile; `.husky/` is absent. Delivery,
   not module preparation, removes owned release/commitlint configuration and
   legacy workflows.

5. **Audit policy and release prerequisite:** Remove module-local
   NU1901/NU1902 `WarningsNotAsErrors` from `Directory.Build.props`, relocate
   the intended low/moderate treatment into released Builds `Props/`, and
   update `BuildContractConformanceTests.cs` to assert effective central
   behavior. Retain NuGetAudit=true/all, high/critical/audit-unavailable
   failures, SDK pin, all product code and the unrelated UI NU5104 setting.
   Qualify and publish one acceptable Builds release containing both shared
   test policy and centralized audit policy before pinning/adoption.

6. **Registration:** `setup/Hexalith.Agents.yml` uses
   `solution: Hexalith.Agents.slnx`, the five exact `.csproj` floor entries,
   `failSkips: true`, `hooks: [after-unit-tests]` and
   `codeql: [csharp, javascript-typescript]`. The JS target is real product:
   `src/Hexalith.Agents.UI/wwwroot/pendingProviderCommands.js`. No extra
   submodules, Dapr, browser environment or Windows jobs are required for the
   package lane. Render through the released schemas, commit cause/output and
   prepared Agents gitlink together, then run full committed/global/live
   validation before pushing. Preserve all other modules and concurrent pin
   changes. Record the resolved classification centrally.

## Verification and acceptance

Use `run-with-temp` for every disposable job, with outputs/feeds below TMPDIR
and useful logs outside it. Qualify strict schema/default behavior, count
boundaries, fail-skips, unsupported-policy rejection, test completion and
project stop ordering, default-module compatibility and CI/local parity.
Run shared Python tests on Python 3.12 and runner Python, native SDK11 product
build/tests, actual six-package/consumer checks, package-hook regressions and
the common-code scan. No unit assertion of workflow YAML is added to modules.

Re-use `tools/render.py`, `tools/check_global.py` and `tools/validate.py` with
their adjacent locked environments. Global validation requires cause/render
committed at candidate HEAD. Per-module validation fetches live actions, so
the qualified product hook must be on actual Agents main before registration.

After pilot acceptance and the required shared release/preconditions, observe
App delivery. Authenticate report/run/artifact/accepted refs and exact delivered
perimeter before revoking any legacy access. Then verify immutable releases,
sole scoped NuGet policy, removal from legacy org secrets/API-key scope/Zot
push identity and green module CI. Completion requires Agents' next genuine
scheduled nightly release success or authenticated nothing-to-release,
including both CodeQL languages. A planned or manually dispatched run is not
acceptance evidence.
