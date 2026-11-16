# Story 19: ChatBot code investigation

Read-only investigation of `Hexalith.ChatBot` at freshly fetched `origin/main`
`6a4ca07b18e9b58500dc79dfede1f308da36c828`, 2026-11-16. The CiCd investigation
worktree started at `d04c9ab7a8fa43dc6dac1f15d34135aba8e79551`.

These are planning findings and proposed decisions. No implementation, product
build, test execution, remote write, or migration ran during this investigation.
Paths below are relative to `references/Hexalith.ChatBot/` unless identified as
Builds paths.

## Build and dependency boundary

- `global.json` pins SDK `11.0.100`, with `rollForward: latestPatch`; preserve it.
- `Hexalith.ChatBot.slnx` explicitly includes projects under Commons, EventStore,
  FrontComposer, Parties, Projects and Tenants. Those projects are built directly
  even with `UseHexalithProjectReferences=false`.
- `Directory.Build.props` already selects package mode outside local Debug and
  detects sibling locations through `Hexalith*Root` properties. Most external
  library references in `src/*/*.csproj` and `tests/*/*.csproj` have source-mode
  conditions and package-mode counterparts.
- `src/Hexalith.ChatBot.AppHost/Hexalith.ChatBot.AppHost.csproj` is different: it
  unconditionally references external EventStore, Platform, Tenants, Parties,
  Projects and Memories executable/resource projects. Its composition also
  imports external Aspire libraries. Package-mode flags do not remove these
  source dependencies.
- `tests/Hexalith.ChatBot.Architecture.Tests/ScaffoldArchitectureTests.cs`, method
  `ReleaseDependencyGraphShouldUsePackagesOutsideAppHostCompositionResources`,
  explicitly protects that AppHost composition exception. Do not delete this
  product boundary test merely to hide a changed dependency graph.
- The source-only Folders owner fixture in
  `tests/Hexalith.ChatBot.Server.Tests/Hexalith.ChatBot.Server.Tests.csproj` is
  already conditional, and its source-dependent test is excluded in package
  mode. Ordinary library package counterparts remain required.

Suggested resolution for human decision: remove external library entries from
the solution and use published packages for library dependencies, while retaining
an explicit source-composition exception for AppHost resources and declared
direct submodules. If the strict package-only requirement also covers test
topology executable/resources, adoption must instead wait for a design using
published executable/container assets. Investigation found no existing compatible
replacement that can be selected without changing product behavior.

Hosted module-root CI can initialize explicitly registered direct submodules
through the existing `submodules` setup field. Local umbrella work must use its
root-declared sibling checkouts and explicit root mappings; this is not approval
to initialize ChatBot's nested submodules inside CiCd.

## Product checks to retain

- `tests/Hexalith.ChatBot.IntegrationTests/OwnerServiceTopologyTests.cs`,
  `AssociationIngressAppChannelTokenTopologyTests.cs`, and
  `Recovery/RecoveryValidationTopologyContractTests.cs` instantiate
  `DistributedApplicationTestingBuilder<Projects.Hexalith_ChatBot_AppHost>` even
  without the live Tier3 opt-in. The integration project cannot simply lose its
  AppHost reference.
- `tests/Hexalith.ChatBot.IntegrationTests/TrivialGovernedCommandAspireE2eTests.cs`
  and `Story132ProductionBrowserAspireE2ETests.cs` start the real topology under
  `HEXALITH_CHATBOT_TIER3=1`; `HEXALITH_CHATBOT_TIER3_REQUIRED=1` makes missing
  runtime prerequisites fail. Docker and initialized Dapr are required. The
  browser matrix also requires real Chrome/Chromium.
- `tests/Hexalith.ChatBot.UI.E2E.Tests/`, including
  `RealRenderCrossSurfaceE2ETests.cs` and `RealRenderFixture.cs`, exercises real
  browser/UI behavior. Browser absence currently causes visible skips in some
  tests; migration must provide browsers instead of treating those skips as
  equivalent coverage.
- `src/Hexalith.ChatBot.Server/Audit/LiveRecoveryValidationEvidenceGate.cs` and
  related recovery policies, manifests and behavioral tests enforce product
  recovery behavior. Their word "Evidence" does not make them story evidence.
- `tests/Hexalith.ChatBot.AppHost.Tests/AppHostTopologyTests.cs` checks topology
  and security configuration. Its
  `MemoriesOwnerTopologyShouldPreserveOneConfiguredSidecarAndSecretServiceAuthentication`
  test additionally reads
  `references/Hexalith.Platform/src/Hexalith.Platform.Composition/PlatformOwnerServices.cs`.
- `tests/Hexalith.ChatBot.Architecture.Tests/PackageCatalogAuthorityTests.cs`
  evaluates `references/Hexalith.Timesheets/Directory.Packages.props`.
  `ScaffoldArchitectureTests.RootDeclaredSiblingPackageWrappersShouldDelegateVersionsToSharedBuildsCatalog`
  inspects declared sibling package wrappers. Account for their source-read
  requirements instead of silently dropping coverage.
- Product conformance, cross-tenant isolation, contracts, server, client,
  workers, UI and recovery tests stay. Story/epic prefixes alone do not classify
  a product test for deletion.

## Gates and assertions to remove or narrow

The CiCd delivery owns replacement of `.github/workflows/ci.yml` and
`.github/workflows/release.yml`. Product preparation must not edit those files.

- Delete `tools/Hexalith.ChatBot.StoryEvidenceGate/`,
  `tests/Hexalith.ChatBot.StoryEvidenceGate.Tests/`, their solution entries, and
  `story-evidence-policy.json`: these implement story-completion evidence gates.
- Delete `.github/scripts/tests/test_story_evidence_guards.py` and obsolete
  story-only scripts such as `check-story-evidence-reserve.sh`,
  `resolve-story-evidence-bounds.sh`, and `collect-story-evidence-artifacts.sh`.
- Remove
  `tests/Hexalith.ChatBot.Architecture.Tests/ReleaseWorkflowSafetyTests.cs`:
  it tests superseded CI/release boundaries, runners and workflow YAML.
- Narrow
  `tests/Hexalith.ChatBot.Architecture.Tests/LiveRecoveryValidationArchitectureTests.cs`.
  Delete `RequiredGateResidualsRemainBoundToOpenLedgerLimits` (reads the BMAD
  deferred ledger), and methods reading workflow YAML:
  `ProducerAttemptEnvelope_ShouldSurviveCheckout`,
  `RecoveryProducers_ShouldBoundInProcessDeadlineStrictlyInsideTheExternalInterrupt`,
  `CompletionJob_ShouldProduceItsInJobCurrentRunLaneAfterTheRecoveryProducer`,
  `CompletionJob_ShouldBuildTheGateToolBeforeItsFirstNoBuildInvocation`,
  `RecoveryLaneCeiling_ShouldCoverTheWorkflowProducerBudget`,
  `RequiredWorkflows_ShouldInvokeAndAlwaysRetainTheLiveEvidenceGate`,
  `ReleasePublication_ShouldRequireFreshMainHeadImmediatelyBeforeSemanticRelease`,
  `ReleasePublication_ShouldBypassStopShipGatesOnlyThroughAnExplicitManualDispatch`,
  and `RunnerBudgetAndCadence_ShouldMatchTheWorkflowValuesTheyDescribe`.
  Preserve runtime fault vocabulary, sandbox boundary, recovery policy and
  compiled dependency checks in the same file.
- Narrow `tests/Hexalith.ChatBot.Architecture.Tests/ScaffoldArchitectureTests.cs`:
  remove `CiShouldInitializeOnlyReferencesSubmodulesNonRecursively`,
  `PullRequestMergeRefValidationShouldRemainIsolatedFromExactHeadEvidence`,
  `StoryEvidenceIntegrityGateShouldRemainFailClosedAndMachineBound`, and
  `WorkflowsAndToolsShouldNotUseRecursiveSubmoduleCommands`, with unused helpers.
  Update solution expectations after gate deletion.
  Split `ReleaseMetadataShouldBindExactInventoryAndRemainBlockedOnOpenEvidenceGates`:
  keep actual package/container inventory assertions, remove story readiness
  blockers and evidence bookkeeping assertions.
- The independently downloaded artifact release-evidence lane in legacy
  workflows is superseded. The mixed
  `tests/Hexalith.ChatBot.IntegrationTests/Recovery/LiveRecoveryEvidenceGateReplayTests.cs`
  contains both its artifact-driven entry point and product loader/retention
  tests; classify individual methods, preserving behavioral tests.
- `.github/scripts/tests/test_recovery_result_projection.py` and
  `test_release_package_paths.py` test legacy script boundaries. Reassess their
  remaining callers during deletion; do not confuse their existence with a
  need to retain the legacy release pipeline.

## Recovery scheduling conflict

`tests/Hexalith.ChatBot.IntegrationTests/Recovery/LiveContinuityAspireE2eTests.cs`
performs real destructive recovery validation. The legacy CI job has a
330-minute timeout and uses a 250-minute in-process budget. The test has its own
workflow deadline and fault-restoration obligations.

At the selected Builds release, `.github/workflows/release.yml` gives
`nightly-hook` only 45 minutes. Turning on Tier3 for the whole ordinary
IntegrationTests project also turns on this long sweep. Moving its current
command unchanged into the nightly hook cannot preserve its execution budget.

Suggested resolution for human decision: isolate the long recovery sweep from
ordinary integration execution, preserve all its product scenarios and cleanup,
and extend the shared, centrally owned nightly-hook budget before adoption.
Decide whether its weekly cadence must remain or may become nightly. A package
or project split must account for the existing shared integration helpers and
internals; an unreported filter/skip is not a substitute. Alternatively, defer
adoption until a product-owned equivalent fits the existing budget. Deleting the
sweep merely because its name mentions evidence would remove product coverage.

## Proposed setup and cleanup facts

- Baseline setup: `solution: Hexalith.ChatBot.slnx`, `dapr: true`,
  `browsers: true`; specify direct submodules after resolving composition.
  Registry pull need was not established by this investigation.
- Builds `Github/lib/ci_pipeline.py` automatically classifies
  `IntegrationTests`, names containing `E2E`, and names ending `AppHost.Tests`
  into stage 4. ChatBot's `global.json` has no test runner override, so the
  shared VSTest/xUnit adapter path applies; no classifier incompatibility was
  identified from source.
- No module `NuGetAuditSuppress`, `WarningsNotAsErrors` audit waiver or NU190x
  `NoWarn` was found. `Directory.Build.props` sets `NuGetAudit=true` and
  `NuGetAuditMode=all`. AppHost's `ASPIRE010` suppression is unrelated.
- Root `package.json` and `package-lock.json` contain only commitlint and
  semantic-release tooling and qualify for removal. `.husky/` is absent.

## Accepted disposition, 2026-11-16

The human instructed “apply recommandation” after the three options were
explained. The story spec now records the ChatBot-only pre-adoption verification
exception, a gitlink-pinned AppHost executable/composition-helper source
exception, and separate shared nightly timing work as an adoption prerequisite.
Weekly cadence, full recovery budgets and cleanup remain required. The shared
controller already refreshes tokens; the prerequisite reuses that machinery.

The existing deferred ledger entry DW-4 reports a previously reproduced
VSTest/Microsoft.Testing.Platform incompatibility. That report used SDK 10, while
ChatBot now pins SDK 11.0.100. Source inspection alone does not establish current
runner compatibility. Implementation must verify execution and, if needed,
select the supported runner without changing the SDK pin or dropping tests.

The isolated CiCd branch was fast-forwarded to current remote main
`d3f3ef864c08cd89e390246d1a5d1dedffc4a92b` before applying these decisions.
The earlier read-only preflight retains its original revision and timestamp.
No module implementation, remote write, or adoption has occurred.
