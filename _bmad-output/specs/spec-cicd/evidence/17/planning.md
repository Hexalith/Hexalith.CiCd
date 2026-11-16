# Story 17 planning evidence

Planning only, 2026-11-16. No product file, remote setting, publication policy,
credential, delivery registration or owned module portion has been changed.

## Isolation and revisions

The human approved an isolated checkout after the initial dirty-worktree gate.
The original workspace is preserved. The branch is `story/17-migrate-folders`
at `/home/administrator/projects/hexalith/cicd-story-17`.

- Initially fetched CiCd main: `d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`.
- Concurrent changes were inspected and fast-forwarded before drafting:
  `7d32df03405c876df6f098aec4036207bf35af1d`.
- Freshly fetched Folders main and product branch base:
  `a448d20873dc9e809623f85da206e8d8a13bb9ab`.
- Selected Builds `v6.0.6` and Folders' existing Builds gitlink:
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.

Only direct CiCd submodules Builds, Folders and AI.Tools were initialized.
No nested submodules were initialized. Other migration sessions have isolated
branches; refresh shared main and inspect changes before eventual publication.

## AD-21 read-only preflight

`planning-preflight.py` saves authenticated GET results and relevant permission
headers to `planning-preflight.json`. The default profile remains
`/home/administrator/.config/gh-cicd-agent`. Command-local maintainer reads use
`/home/administrator/.config/gh`; both identify `jpiquot`, ID `6775094`.
Neither `GH_TOKEN` nor `GITHUB_TOKEN` overrides was present. Account `admin:true`
is not treated as token API permission. No secret values were retrieved.

Observed through successful reads:

- No repository rulesets; create exact main deletion/force-push protection and
  v-tag update/deletion protection before adoption.
- Only the legacy `production` environment exists. `hexalith-release` is
  absent according to the successful environment inventory as well as 404
  detail reads. Provision its main-only policy and own scoped Zot push pair.
- Publish switch is exactly `true`; artifact/log retention is 90 days;
  code-scanning default setup is `not-configured`; Dependabot security updates
  are disabled; secret-scanning push protection is enabled.
- The first 100 CodeQL analyses use `.github/workflows/codeql.yml:analyze`.
  This is a page, not a complete analysis count. Assess and retire stale
  configurations with bounded pagination; preserve other scanning tools.
- Release inventory has 10 entries, no drafts. `v1.1.0` has no corresponding
  release; assess its exact target and incomplete-release history before any
  authorized legacy cleanup. Do not delete published releases or valid tags.
- Folders is not selected for either Actions or Dependabot registry-pull
  secret pair, or the `HEXALITH_NUGET_USER` org variable. Grants are additive
  before adoption; legacy grants remain until real adoption.

The intended maintainer API GET
`user/installations/179966090/repositories` returns HTTP 403:
"You must authenticate with an access token authorized to a GitHub App, a
personal access token, or basic auth in order to list repositories for an
installation." Its diagnostic requests `read:user`. This does not prove the
installation's selection. The existing attended Windows browser provides the
read-only fallback: `browser-preconditions.json` records the visible installed
App page, selected Builds/CiCd/Commons/PolymorphicSerializations, no pending
Save and no Confirm-access prompt. Folders is absent from that observed list.

No connected document-control sessions exist. The visible UI scan found no
Trusted Publishing page. Folders' additive `Hexalith.Folders*` NuGet policy and
its distinct Zot principal are unverified, not inferred absent. Use existing
authenticated access during implementation; stop at any real sign-in barrier.

The approved migration order and predecessor done checkpoints remain in force.
The pilot spec still awaits its genuine scheduled-night checkpoint. Planning
can proceed in parallel; do not claim or perform out-of-order adoption.

## Product map and gate classification

All following paths are relative to Folders unless explicitly prefixed.

- Preserve `global.json` SDK `11.0.100`, MTP selection and published `net11.0`
  targets. Use `Hexalith.Folders.CI.slnx`; the full solution hard-includes
  foreign source projects.
- Enable `dapr`, `browsers` and the three Linux hooks. Register direct source
  prerequisites `references/Hexalith.{McpCli,Memories,Platform,Tenants}`.
  AppHost compiles Platform source; tests consume McpCli inventory/serializer
  and Memories/Tenants metadata/runtime. Shared initialization explicitly
  handles their `update=none`; do not reuse the old standalone-workspace and
  private-Dapr preparation script.
- Shared `ci_pipeline.classify_projects` already places `*AppHost.Tests`,
  `*IntegrationTests` and E2E projects in stage 4. Include sample and
  `LoadTests.Tests` test projects. `tests/load` is an NBomber executable.
- `tests/tools/run-contract-spine-gates.ps1` selects tests already in
  Contracts.Tests and Client.Tests. Delegate those **complete** projects to
  `after-unit-tests` and execute each once there, retaining contract/generated
  artifact and deployment-security coverage. An exclusion names an enabled
  owner; it never skips the project.
- `run-e2e-ci-gates.ps1` executes the complete UI.E2E.Tests assembly, including
  accessibility. Delegate that project to `after-integration-tests`; reuse
  the shared build and browser install. Avoid calling the overlapping
  accessibility subset a second time. Existing switches are
  `-SkipRestoreBuild -SkipBrowserInstall`.
- Retain real Forgejo provider smoke in the `nightly` hook through
  `tests/tools/run-forgejo-smart-http-alpine-smoke.ps1`. It currently combines
  net11 output with `aspnet:10.0-alpine`; align its runtime and preserve all
  actual Docker/TLS assertions and cleanup.
- `run-nightly-drift-gates.ps1` largely repeats Forgejo/GitHub project tests.
  Retain provider classification/redaction and its distinct sanitized-report
  operation (`forgejo-drift/Write-SanitizedForgejoDriftReport.ps1`) without
  duplicate project execution or CI-status self-tests. Its live-provider
  success is explicitly `not_run`; do not report it as performed.
- Scheduled policy orchestration repeats `DaprPolicyConformanceTests` and
  checks report/scheduling text; its live-kind operation is merely
  `reference_pending_story_7_8`. Delete the orchestration machinery while
  preserving actual access-control, mTLS, sidecar, secret-store and pub/sub
  product-security tests in the complete Contracts project.
- Remove `scripts/tests/test_ci_cd_tooling.py`, preparation-script assertion
  tests, and other CI/tooling/story-evidence tests after per-method review.
  Keep genuine product checks even inside similarly named files.
- Root `package.json` is exclusively semantic-release/commitlint; retire it
  with `package-lock.json`. `.husky/` is absent. Delivery removes owned legacy
  commitlint/semantic-release configuration and workflows.
- No current `NuGetAuditSuppress` was found. Remove the module's NU1901–1904
  `WarningsNotAsErrors` waiver in `Directory.Build.props`. Do not invent a
  central suppression. Any actual newly discovered required waiver belongs
  only in Builds Props and must ship in an acceptable tag before adoption.

### Workflow-reference inventory

The original 27-file estimate is stale: current inspection found 24 C# files
referencing workflow paths, of which 22 read/scan workflow contents, one
enumerates YAML names and one refers to a workflow only in a story manifest.
This count is not a deletion quota.

Under `tests/Hexalith.Folders.Contracts.Tests/`, retire these wholly CI/tooling
files:

```
Deployment/AccessibilityCiWorkflowConformanceTests.cs
Deployment/BaselineCiWorkflowConformanceTests.cs
Deployment/ContractParityCiWorkflowConformanceTests.cs
Deployment/E2eCiWorkflowConformanceTests.cs
Deployment/HonestGreenGateBaselineConformanceTests.cs
Deployment/PinnedDomainCiWorkflow.cs
Deployment/ScheduledDriftAndPolicyWorkflowConformanceTests.cs
Deployment/SecurityRedactionCiWorkflowConformanceTests.cs
Deployment/NfrTraceabilityConformanceTests.cs
```

Remove workflow/script-wiring/story-evidence assertions from mixed files,
preserving product assertions:

| File | Direct workflow assertion |
| --- | --- |
| `Deployment/AdrRunbookDocsConformanceTests.cs` | `ContractSpineWorkflowAndBaselineCiWireAdrRunbookGateOnlyInAllowedLanes` |
| `Deployment/CapacityCalibrationConformanceTests.cs` | `CapacityCalibrationShouldRemainARepositoryGateWithoutCouplingPackagePublication` |
| `Deployment/CapacitySmokeCiWorkflowConformanceTests.cs` | `CapacitySmokeWorkflowShouldExposeStableBlockingJobWithBaselineSetupPosture` |
| `Deployment/ConsumerDocsConformanceTests.cs` | `ContractSpineWorkflowAndBaselineCiWireConsumerDocsGate` |
| `Deployment/OperationsAuditDocsConformanceTests.cs` | `ContractSpineWorkflowAndBaselineCiWireOperationsAuditDocsGate` |
| `Deployment/ProductionObservabilityConformanceTests.cs` | `ContractSpineWorkflowAndBaselineCiShouldWireObservabilityGate` |
| `Deployment/ProviderErrorDocsConformanceTests.cs` | `ContractSpineWorkflowAndBaselineCiWireProviderErrorDocsGate` |
| `Deployment/ReleasePackageConformanceTests.cs` | `CiWorkflowShouldUseSharedReleaseMtpValidationAndRetainFoldersGates`; `ReleaseWorkflowShouldBeManualExactSourceProtectedAndImmutable` |
| `Deployment/RetentionAndTenantDeletionConformanceTests.cs` | `RetentionDeletionEvidenceShouldRemainIndependentFromSealedPackagePublication` |
| `OpenApi/ContractSpineCiGateTests.cs` | `WorkflowWiresFocusedContractGeneratedArtifactGatesOnly` |
| `OpenApi/DaprPolicyConformanceTests.cs` | `WorkflowAndScriptShouldWireOfflineDaprPolicyConformanceGate` |
| `OpenApi/GovernanceCompletenessGateTests.cs` | `WorkflowAndScriptExposeOneOfflineGovernanceCompletenessCommand`; workflow cache-key scanner near line 2860 |
| `OpenApi/SafetyInvariantGateTests.cs` | `WorkflowAndDocumentationExposeSameOfflineSafetyGate` |
| `OpenApi/TenantFolderProviderContractGroupTests.cs` | CI YAML inventory within `ContractGroupOperations_PreserveNegativeScope` |

`OpenApi/Pd10ConformanceSetTests.cs` verifies story evidence/source
requalification; classify separately from actual OpenAPI product conformance.
The table identifies direct workflow assertions, not every prohibited method.
Complete the gate-rule audit before writing the final deletion manifest.

### Runtime and verification considerations

Client generation uses `NSwagExe_Net100` and a `net10.0` executable in
`src/Hexalith.Folders.Client/Generation/`. Legacy CI installed .NET10 alongside
SDK11. The shared CI exposes an `additional-sdk-version` input but setup and
release/nightly do not share it. Custom actions forbid `actions/setup-dotnet`.
Do not rely silently on an incidental hosted runtime or introduce module setup
actions. Align the nonpublished generator executable with SDK11 and explicitly
scope NSwag major-runtime roll-forward to its process, retaining byte-stable
generated artifact checks. Preserve published target frameworks. Propagate
shared configuration/package/audit properties into nested generator builds;
the current hard-coded audit-on `dotnet run` bypasses CI's audit-off intent.
Local discovery confirms installed SDK11 and .NET10/11 runtimes, so the local
host alone cannot prove a missing-.NET10 hosted scenario.

Legacy CI has a 17-case not-runnable list. Do not carry it into shared setup or
add a new skip: run actual retained tests with their product prerequisites and
report any product failure. Frozen workload/proprietary-interface policy is
not permission to weaken these tests.

## Scoped preparation proposal requiring a human decision

From the isolated Folders root,
`run-with-temp python3 references/Hexalith.Builds/check.py` exits 2 because the
nested checkout is absent; exact stderr is in `pre-adoption-check.log`.
Initializing it is forbidden by the root-submodule rule and would not resolve
the adopted-config/delivered-state requirements in `Github/lib/local_check.py`.
The source checker exists at the current gitlink, but Folders has neither
`.github/hexalith-ci.json` nor an accepted delivered perimeter.

Story 11's approved replacement was explicitly pilot-only. Proposed Folders
exception, only before real adoption and only for exact product-preparation
commits:

1. Export exact Folders, released Builds and the four direct source
   dependencies into standalone disposable verification workspaces under
   `run-with-temp`; initialize no nested submodules and author no owned module
   files. Record immutable input IDs and in-memory CI settings.
2. Run released audit/action/commit lint and package-mode Release compilation,
   every retained test project with its real prerequisites, browser checks and
   applicable provider/generated-artifact checks. Preserve failure statuses.
3. Prove byte/mode/gitlink identity of all owned portions against freshly
   fetched main. Save exact changed-path inventory, commands and outcomes.
4. Re-fetch at the actual protected-token push; refuse a changed base/head.
   Require the normal successful checker again immediately after adoption.

Keeping the existing checker requirement unchanged means preparation cannot
be pushed, so adoption remains blocked. Neither choice authorizes owned edits,
credential changes, audit/test bypasses or fabricated delivery evidence.
