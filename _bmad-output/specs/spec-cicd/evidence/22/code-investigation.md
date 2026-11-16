# Story 22: Memories migration investigation

This is planning evidence, not adoption or verification of migrated behavior.
All remote operations in this investigation were reads. Existing module and
primary CiCd working trees were preserved.

## Canonical revisions

- Clean CiCd planning worktree: `/home/administrator/projects/hexalith/cicd-story-22`,
  branch `story/22-migrate-memories`, based on freshly fetched main
  `66e3a5a3a0e9bb01dd161c19349953594e01a22f`.
  During investigation, other sessions advanced main. The planning branch was
  fast-forwarded to `c74b5c8f5787fb33bfd85c1c4430b6de39674198`; the incoming
  changes add migration handoffs and a G-6 catalog-acquisition proposal, without
  changing the selected Builds runtime or implementing this story's prerequisites.
- CiCd's current Memories gitlink:
  `898f451111740ccf489d56f7c20cd47edc2fcdf6`.
- Freshly fetched Memories main:
  `c64e292a46858058f6764095c8e01c2faa0ff3e0`. The difference from the gitlink is
  four BMAD documentation files; code/runtime classification applies to this main.
- Selected Builds `v6.0.6`:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- Memories' pre-adoption Builds gitlink:
  `e2bbbd0893f586e4d447ef8358ff747ea3d34435`.

## Maintainer preflight

`preflight.py` records sanitized GET responses in `preflight.json`, using a
command-local maintainer profile. The default profile stays CiCd-agent. Neither
GH_TOKEN nor GITHUB_TOKEN overrides were present. The authenticated account was
`jpiquot`; account admin permissions are not evidence of token API permissions.

| Requirement | Observed state |
| --- | --- |
| CiCd App installation | App exists with selected repositories; Memories membership unverified |
| Membership read refusal | HTTP 403 from `user/installations/179966090/repositories`; API reports missing `read:user` scope |
| Main protection | Active deletion/non-fast-forward rules; current bypass actors require AD-21 reconciliation |
| `v*` tag protection | Missing from successful ruleset inventory |
| Release environment | `hexalith-release` absent from successful environment inventory |
| NuGet policy / dedicated Zot identity | Unverified; establish scoped policy beside legacy policy and module-only push permissions before preparation pushes |
| Publish switch | Exactly `true` |
| Default CodeQL / security updates | Not configured / disabled |
| Retention / push protection | 90 days / enabled |
| Shared org grants | Memories absent from NuGet username and both Actions/Dependabot registry pull grants |
| Immutable releases | Off; enable immediately after authenticated adoption |
| Legacy org access | Selected for `HEXALITH_ZOT_USERNAME` and `HEXALITH_ZOT_API_KEY`; absent from Actions NUGET_API_KEY, Azure and Sonar selections |

Absence from the Actions secret selection does not establish removal from the
legacy nuget.org API key's package scope. Inventory stale CodeQL analyses,
unmarked drafts and orphan/incomplete legacy tags completely, with pagination,
before provisioning. The saved first page alone does not certify cleanup.
The new Builds release is published and immutable; full bot/tag/ancestry checks
remain the existing validator's responsibility at candidate time.

## Gate classification and code map

The authoritative rule is CiCd `AGENTS.md` and spec-cicd
`gate-classification.md`. Keep product compilation, tests, security/dependency,
commit-format and publishing checks. Remove CI/agent/story/YAML checks. Python
under `tests/tooling` is not automatically tooling-only: inspect its behavior.

### Preserve product behavior

- `Hexalith.Memories.slnx`, `global.json`, `Directory.Build.props`,
  `Directory.Packages.props`: preserve SDK 11.0.100 and Release/package defaults.
  Ordinary cross-repository references are package-gated. AppHost runtime
  composition still needs assessment: `AddHexalithEventStoreGatewayProject()`
  resolves source metadata. Retained descriptor-reader tests also use Platform
  and Builds tooling. Do not finalize an empty `submodules` list from the
  package-build inventory alone.
- Shared stages 2–3 run all discovered unit/contract projects. The separate
  `DerivedStores.Tests` project is discovered even though old unit inventories
  omit it; some sources are linked into Server.Tests. Preserve coverage and
  avoid redundant execution by an explicit project ownership change if needed.
- `tests/Hexalith.Memories.IntegrationTests/`: fast, slow, performance and
  untagged cases are product checks. The shared runner runs complete projects.
  Preserving current fast-CI/slow-nightly cadence requires separating nightly
  cases into a complete project and registering its ownership; no plain skips.
- `tests/Hexalith.Memories.Benchmarks/`: retain the entire NDCG project in the
  enabled nightly hook using the supported project-to-hook exclusion mapping.
- `tests/Hexalith.Memories.Web.E2E/`: retain Playwright specimens, accessibility,
  type checks and browser artifact assertions. Keep its own Node manifest/lock.
  Change `playwright.config.ts` to use the prepared Release specimen host; its
  current Debug `dotnet run` recompiles. Use the shared browser environment.
- Preserve 44 Python files across `tests/tooling/access_telemetry_c1/`,
  `access_telemetry_c1_interchange/`, `access_telemetry_c1_sql_contract/`,
  `access_telemetry_functional_retention/`, `access_telemetry_lifecycle/` and
  `access_telemetry_owner_discovery/`: actual domain/operator authorization,
  SQL and safety behavior, not merely story evidence. Required tools and source
  descriptors must be available without hook-side generic setup.
- `tools/verify-production-deployment.ps1`,
  `tools/validate-production-deployment-evidence.ps1` and
  `tests/tooling/production_deployment_evidence/`: retain real disposable rollout,
  health, persistence and recovery checks. Existing workflow first rebuilds OCI
  through `tools/publish-containers.ps1`; copying that step into a hook violates
  AD-14. Shared prepared images and kind/kubectl provisioning are prerequisites.
- SQL contract runner:
  `tests/tooling/access_telemetry_c1_sql_contract/linkage_sql_contract_test.py`.
  Dependencies include Docker, PowerShell >=7.5, OpenSSL and pinned PostgreSQL
  `docker.io/library/postgres@sha256:0377e72c5289ed2f98cf61b1a9c2db9eb9d300317fe14244492fbc94343b3d04`.
- Keep meaningful product package/container-content and publication behavior
  assertions while removing workflow coupling. Existing release inventories
  `tools/release-packages.json` and `tools/release-containers.json` describe ten
  NuGet packages and five dual-architecture images. Shared discovery must cover
  those product outputs; compare inventories before deleting any legacy tooling.

### Eleven YAML-asserting files: split mixed coverage

Paths below are relative to Memories `tests/`:

1. `Hexalith.Memories.Cli.Tests/Ci/CiTestInventoryTests.cs`
2. `tooling/builds_publication_qualification/builds_publication_qualification_test.py`
3. `tooling/ci_alignment/ci_alignment_test.py`
4. `tooling/commitlint/commitlint_entrypoints_test.py`
5. `tooling/coverage_gate/coverage_contract_test.py`
6. `tooling/publish_containers/partial_release_completion_test.py`
7. `tooling/publish_containers/partial_release_recovery_test.py`
8. `tooling/publish_containers/publication_contract_test.py`
9. `tooling/release_dispatch/release_dispatch_test.py`
10. `tooling/release_preflight/release_preflight_test.py`
11. `tooling/story_review_readiness/readiness_entrypoints_test.py`

Do not delete mixed files wholesale. Extract the C# product assertions
`BackendProjects_ShouldNotUseRedisCompatibilityPackageAsDependencyFacade`
(line 141) and `ContainerBaseImage_IsDigestPinnedAndInheritedByEveryProject`
(line 1379) before removing the CI inventory class. Python split points include
completion line 295, recovery lines 1015 onward, preflight line 84, qualification
`assert_capture` around line 399, and module-level workflow dependencies in
coverage/publication contract suites. Earlier publisher behavior tests remain
subject to product ownership, not a blanket filename verdict.

Remove dedicated story/agent/CI gates and suites in `story_scope`,
`story_slice_scope`, `story_review_readiness`, `tenant_isolation_evidence`,
`bmad_customization`, `ci_alignment`, and workflow/action-pin/agent-ledger checks.
Inspect mixed line-ending, coverage and package tests by the same rule. Keep
actual product assertions; new hooks must not reintroduce CI qualification.
Delivery removes old workflow files, including story-named jobs; preparation
does not edit those owned files.

### Audit and legacy root tooling

- Remove the module audit bypass in `Directory.Build.props:12–21`, including
  `WarningsNotAsErrors` for NU1901–NU1904. Builds v6.0.6 already pins AngleSharp
  1.10.3 with security-fix rationale. Run a real release audit; do not create an
  unnecessary central waiver. Any justified remaining waiver belongs only in
  Builds `Props/` and requires an acceptable release before adoption.
- Root `package.json` and `package-lock.json` contain semantic-release/commitlint
  tooling only. Remove them, `.releaserc.json`, `commitlint.config.mjs`, and
  installed `bmad-testarch-ci` copies. `.husky/` is absent.
- Actual legacy hooks are `.githooks/pre-commit` and `.githooks/commit-msg`.
  Remove obsolete story/evidence/root-node dependencies with the tooling;
  retain commit-format enforcement through the shared guard.

## Hard planning boundaries

The source-debug workflow compiles the actual Debug/source dependency graph and
runs source-selected catalog tests. It is genuine product coverage. AD-12/14
requires Release/package-only shared preparation and prohibits hook rebuilds.
The human must resolve that conflict explicitly. Package catalog checks alone
do not establish source-build compatibility.

AD-14 also forbids generic environment setup and Builds calls from custom hooks.
Current `Github/lib/ci_environment.py`, `ci_pipeline.py`, reusable workflows,
schemas and CiCd renderer are the shared extension points for rollout tools,
prepared OCI inputs and any approved source qualification. Such shared work
must ship separately; story 22 must not invent unsupported setup keys, add a
bespoke workflow, or enable incompatible actions before the runtime is released.
Read-only descriptors/composition dependencies must be pinned and declared,
with ordinary libraries remaining in package mode.

The existing checker is present at Memories' pinned Builds revision.
`Github/lib/local_check.py:152` loads `.github/hexalith-ci.json`, which does not
exist before adoption; the guard subsequently requires delivered expected state.
This proves a sequencing gap, not a reason to fabricate config, edit the pin,
disable the guard or inherit another module's approved exception.

## Timing evidence

Read-only investigation found successful nightly run
`https://github.com/Hexalith/Hexalith.Memories/actions/runs/43846941740`:
slow integration 10m22s, benchmark 2m31s, whole run 10m26s with parallel jobs.
The last five successful nightlies took roughly 9–15 minutes. Old 60/30-minute
job limits are allowances, not observed runtime. Qualify the combined prepared
hook, including setup and cleanup, against the shared 45-minute default; do not
claim a measured >45-minute blocker or silently truncate coverage.
Sanitized run/job metadata is retained in `nightly-timing.json`.

## Execution and acceptance interfaces

- Reuse CiCd `tools/render.py`, `tools/validate.py`, `tools/check_global.py`,
  `setup/README.md` and `tools/deliver.py:app_checks` rather than a second writer.
- Maintainer-only state extends beyond App checks: those do not certify the
  NuGet policy, scoped Zot permissions, every environment property or cleanup.
- Product writes use module-agent; CiCd/Builds writes use CiCd-agent. Maintainer
  administration uses a command-local profile. Do not broaden or switch around
  credential refusals; App private key never enters an interactive session.
- Initialize only necessary direct submodules at exact pins in isolated jobs;
  use `run-with-temp` for disposable work and preserve useful logs here.
- Register `setup/Hexalith.Memories.yml`, remotely available product gitlink,
  and `rendered/Hexalith.Memories*` together after dependencies are available.
- Recheck current main immediately before all writes. Authenticate App adoption,
  foreign-content preservation, immediate scoped credential cleanup, green
  adopted CI, and the next scheduled nightly success or nothing-to-release.
  Publishing disabled or a manual dispatch does not establish story completion.
