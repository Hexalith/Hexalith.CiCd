# Memories adoption prerequisite handoff

This is a separate dependency handoff, not a shared-runtime implementation or
an adoption approval. Story 22's implementation stage is local only. It made no
GitHub API calls, remote repository operations, pushes, settings changes,
credential changes or delivery.
All prerequisite metadata in `preflight.json` remains a historical readback;
absence and authorization refusal retain their different meanings.

## Shared Builds and CiCd contract release

The selected release is Builds `v6.0.6`,
`fdda17c0a4538b0f7c99f813c20ca24b49006530`. It does not supply the approved
source/composition and rollout prerequisites. Memories' existing Builds gitlink
remains `e2bbbd0893f586e4d447ef8358ff747ea3d34435`; story 22 has not edited it,
the Builds `.gitmodules` section, workflow files or delivered content.

The owning Builds change must amend AD-12/AD-14 and the schema/readers as needed,
ship separately, and pass qualification before a CiCd registration can enable
the dependent hooks. Do not invent setup fields in this story.

| Required capability | Concrete contract and qualification |
| --- | --- |
| Debug/source qualification | Preserve the real SDK `11.0.100` source graph and source-selected catalog behavior at exact direct dependency commits. Use separate Debug/source outputs, leaving normal compilation and publication in Release/package mode. Run the complete source-selected catalog test project, without a method filter or hook-side build. The approved exception is narrowly scoped, not a command runner or build matrix. |
| Runtime composition | Qualify `AddHexalithEventStoreGatewayProject()` with the packaged Aspire dependency while supplying its exact direct source metadata. Ordinary libraries must remain package references. Do not select unpinned sibling/ancestor or nested checkouts. |
| npm Playwright preparation | Current `ci_environment.playwright_tools()` requires built .NET Playwright tooling. Memories has the separate npm workspace `tests/Hexalith.Memories.Web.E2E/` with its own lock. Provide supported shared Node/dependency/browser preparation for that workspace. Run typecheck, every browser specimen/accessibility case, and artifact validation against the already prepared Release specimen host. The local Playwright change uses `Release --no-build --no-restore`. |
| Product coverage | Current `ci_pipeline.execute_test_projects()` does not collect the module's existing Coverlet/MTP outputs. Preserve the `76.5%` gate and required assemblies/files in `tests/tooling/coverage_gate/line-coverage-gate.json`. Require all nine project reports: the original eight plus DerivedStores' newly explicit sole execution/coverage ownership. Its MTP collector already comes from `tests/Directory.Build.props`; no extra package is needed. Collect during shared test execution, validate in the product hook, and preserve useful artifacts. Do not rerun or rebuild whole projects in a hook simply to obtain coverage. |
| SQL tools and image | Prepare Docker, PowerShell >=7.5, OpenSSL and local image `docker.io/library/postgres@sha256:0377e72c5289ed2f98cf61b1a9c2db9eb9d300317fe14244492fbc94343b3d04` before the SQL contract runner. Missing image/tool is a failed prerequisite, never skip credit. |
| Rollout tools | Prepare kind/kubectl and the pinned Dapr/runtime dependencies centrally. Memories retains the real rollout, health, persistence, backup/recovery and cleanup assertions in its existing tools. A hook may exercise those assertions but may not install a generic environment. |
| Prepared OCI inputs | Shared preparation must produce hash-bound immutable OCI inputs for the five declared images and provide the four archives consumed by `verify-production-deployment.ps1`: Server, MCP, telemetry lifecycle and clock. Preserve dual-architecture publication and module content assertions. Do not copy `publish-containers.ps1`/`dotnet publish` preparation into a hook. |
| Combined runtime | Run the complete nightly project, complete benchmark project and retained product checks with required preparation and cleanup; measure the combined duration against the existing 45-minute allowance. Historical parallel run times do not establish a combined duration. No new timeout setting is justified yet. |

Any remaining justified vulnerability waiver must be authored in Builds `Props/`
with rationale and released support. The local product change removes the four
NU1901-NU1904 `WarningsNotAsErrors` bypasses without adding a waiver. A CI build
using the shared `NuGetAudit=false` contract is distinct from the required
audit-enabled release restore; the latter must retain its independent verdict.

The parked telemetry profile also has a separate Memories-owned prerequisite:
`telemetry-prerequisite.log` records `FAIL: current-input:` for the Production
disabled overlay. Its approval expects SHA-256 `0c2b4b836d14be457ab8ccc79a534cd9997193f9c7b10f3d11b8b100a8b40ab2`;
both baseline and migration input bytes instead hash to
`c2e002c81951672e13a2776d0b12eb514f4ecbcb7d7fd917bc51d82b1b734cc9`.
Neither file nor approval changed in this migration. Retain that refusal and
resolve it through the owning profile/requalification process before claiming
the dependent suite passes. Do not refresh approval hashes or Production
overlays merely to make migration verification green. The partially executed
C1 diagnostic is explicitly blocked, not a complete suite verdict.

## Exact local direct dependency inputs

These are the candidate's existing gitlinks read from Git, not freshly fetched
or newly approved dependencies. Registration must verify its final dependency
set against the released source/composition design and remotely available
product revision.

| Direct checkout | Existing exact commit | Role to qualify |
| --- | --- | --- |
| `Hexalith.Builds` | `e2bbbd0893f586e4d447ef8358ff747ea3d34435` | Existing catalog/tool descriptors; implicit Builds pin will be delivered centrally. |
| `Hexalith.Commons` | `fbf4e94233821f6ca336af91a06feaaeb7a16855` | Declared Debug/source graph. |
| `Hexalith.EventStore` | `cbb3a867c773a0857001468062c1779ad9755b8d` | Debug/source graph and Aspire runtime composition metadata. |
| `Hexalith.Tenants` | `7c1747f93fbe988ca8aaa87d636bb6a39563e6b8` | Declared Debug/source graph. |
| `Hexalith.FrontComposer` | `b22be84bdbb23d9263a8835496ad0c95adf1843f` | Declared Debug/source graph. |
| `Hexalith.McpCli` | `55f8a02435c7faa7c4073bf22c78a5d04c466929` | Declared source and gateway/tool graph. |
| `Hexalith.Platform` | `0c3f55d1c4345f4952cbecbff92014251f484ef2` | Retained read-only descriptor and functional-retention boundary tests. |
| `Hexalith.AI.Tools` | `17a37d83db193f0b7494c1b931fd1e82a67c1424` | Existing baseline guidance and legacy `RequiredRootSubmodule` entry; not evidence of a product library dependency. Remove agent-only source prerequisites in the owning preparation design rather than declaring every legacy checkout blindly. |

## Local product candidate and remaining hook work

Persistent standalone checkout:
`/home/administrator/projects/hexalith/memories-story-22`,
branch `story/22-product-preparation`, based on the previously fetched main
`c64e292a46858058f6764095c8e01c2faa0ff3e0`. This stage never claims a current
remote-main check. The primary Memories checkout and its module objects were
read only; all direct dependency checkouts were separate local clones, with no
nested submodule initialization.
This preparation clone's `origin` is the local seeding repository. Shipping uses
a fresh, authorized GitHub checkout at freshly fetched `main`, reapplying the
reviewed product changes under module-agent authentication.

The local candidate extracts the two C# product packaging/container guards,
removes obsolete root release/commitlint/story/agent tooling and YAML assertions,
keeps mixed publisher/recovery/authorization assertions, separates slow cases
into `Hexalith.Memories.Integration.NightlyTests`, and leaves DerivedStores test
ownership in its dedicated complete project. All real OpenBao scenarios remain.

`OpenBaoTopologyTraits_FastSlowAndPerformanceLanesRemainSeparated` is explicitly
classified as a CI inventory/trait-selection assertion under CAP-10. It checks
test registration and categories, not OpenBao behavior. It is removed along with
the old CI inventory. Therefore the integration baseline has 478 source test
methods and the prepared candidate has 477, including all 477 product methods;
the method-preservation evidence must disclose this single permitted removal.
The inert subprocess worker is linked into both executables because slow
restart cases invoke it as an explicit subprocess entry point.

Hook authoring/registration is intentionally incomplete until the shared
environment/output contract is released. The final ownership mapping is:

- Shared stage 3: complete discovered unit/contract projects, including the
  dedicated DerivedStores project, and the preserved product coverage output.
- Shared stage 4: complete `Hexalith.Memories.IntegrationTests` project,
  including previously untagged product cases; after-integration runs browser,
  SQL and disposable rollout assertions against prepared outputs/environment.
- Enabled nightly action: complete `Hexalith.Memories.Integration.NightlyTests`
  and complete `Hexalith.Memories.Benchmarks` projects, through the supported
  project-to-hook exclusion mapping. Preserve all 17 benchmark source cases.
- Product tooling: retain the six telemetry/authorization/SQL/retention suite
  trees, package topology and publishing/content behavior, coverage validator,
  container base/content assertions, and deployment/recovery tools. The six
  telemetry trees include mixed story/fixture setup coupling; the local change
  removes only story-ledger assertions and root commitlint fixture setup from
  those two mixed files, preserving their product assertions.

## Authorized later shipping sequence

1. Revalidate current `main` at the authorized shipping stage. If it advanced,
   reapply only product changes on that main and rerun verification against the
   exact new committed inputs. Do not use PR Update branch to import owned CI.
2. Under command-local maintainer administration, verify App selection first;
   distinguish the existing membership HTTP 403 (`read:user` refusal) from
   absence. Inventory stale CodeQL analyses, drafts and incomplete/orphan tags
   completely with pagination before targeted cleanup.
3. Provision/read back exactly main deletion/non-fast-forward and `v*`
   update/deletion rules, main-only `hexalith-release` without reviewers/timer,
   module-scoped NuGet trusted publishing and Zot push identity, NuGet username
   and Actions/Dependabot pull grants, retaining legacy access until adoption.
   Existing publish-switch, retention and scanning readbacks do not certify
   these outstanding preconditions.
4. Obtain acceptable released shared support, retain authenticated release/tag
   checks, and complete the Memories-only approved pre-adoption verification
   exception on exact committed inputs in a disposable standalone checkout:
   Release/package compilation, every applicable complete product suite,
   package/consumer checks, pinned commit validation, and owned-content
   byte/mode/gitlink proof. Partial local evidence is not push approval.
5. Use module-agent for the product preparation push. Commit CiCd setup,
   remotely available Memories gitlink and render together with CiCd-agent.
   Run renderer check and committed-candidate validation, requiring global and
   Memories schema/lint/perimeter/live-action verdicts. Authenticate the App's
   sole delivery adoption and foreign-content preservation.
6. Immediately after authenticated adoption enable immutable releases, remove
   only Memories' obsolete NuGet policy/key scope, legacy org grants and Zot
   push access, and retain sanitized exact readbacks. The standard checker
   replaces the temporary exception immediately.
7. Require green adopted CI and the next scheduled central nightly success or
   authenticated nothing-to-release. Disabled publishing, a manual dispatch,
   local test success, or an unexecuted environment does not satisfy acceptance.
