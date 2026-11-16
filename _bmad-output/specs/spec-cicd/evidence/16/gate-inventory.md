# Story 16 gate inventory

This is the resolved product-only classification for Conversations at source
`9e24c280efd5e9c13826eab9bc8b8b687a7bee09` (read-only origin/main refresh, 2026-11-16).
The checkout was refreshed by the parent to this exact source. No product files,
workflows, settings, releases, builds or tests were changed/executed for this inventory.
The human subsequently selected generic shared producer preparation/protected
Windows support and a released Builds pin within story 16, plus a Conversations-only
pre-adoption verifier exception. These decisions do not authorize dropping product
assertions, runtime filtering, fake mapping identities, or manual owned-file edits.

## Disposition meanings

- **KEEP**: preserve the complete current product assertion, including data rows and
  negative cases, and run it through the shared classified test stage or an enabled
  product hook/job. Names mentioning a story or evidence do not alone determine fate.
- **DELETE**: remove this test method/file from module product automation because its
  subject is CI, BMAD/agent tooling, historical story proof or workflow text. Every
  workflow-asserting repository test must be physically deleted. For C# tests remove
  the declaration and compilation links rather than hiding it with runtime filters.
  Historical proof documents and `_bmad` authoring tools are retained unchanged.
- **EXTRACT**: keep every specifically listed product assertion in a neutral product
  test/helper while removing its historical planning/CI-evidence wrapper. The detailed
  extraction instructions below are part of the implementation tasks, not an open
  classification decision.

Counts below are method declarations, not expanded xUnit/pytest parameterized cases.
All data rows of kept methods must survive. Source lines identify this frozen input;
implementation may rename neutral tests without changing their product predicates.

## Existing jobs and their replacements

| Current lane | Classification and concrete destination |
|---|---|
| `ci` reusable domain-ci: build + unit/integration/AppHost tests | Keep product compilation and every product assertion. Use evaluated `Hexalith.Conversations.slnx`, SDK11/MTP, package mode, fixed shared stage order and generic producer preparation. No runtime `-class-`/`-method-` filters. |
| `ci` with `run-consumer-validation: true` | Keep package/consumer product lane. Frozen Builds domain-ci currently invokes `scripts/pack-release-packages.py`, `scripts/validate-nuget-packages.py` and `scripts/validate-consumer-package-references.py`. Enable module `.github/actions/after-unit-tests/action.yml` to pack existing workspace outputs with `--no-build --no-restore`, validate exact five payload/symbol pairs, then restore/build/run separate isolated public/testing consumer fixtures. This compiles new consumer inputs and must not rebuild the already-built module workspace. |
| `minimal-module-compatibility` | Keep all six original fixture cases plus `RegisteredCommandTests.RegisteredCommandProducesCreatedEventAndIsIdempotentAfterReplay`. New non-test adapter project under `tests/compatibility/MinimalModule/` joins root .slnx and references the frozen test/AppHost fixture projects with isolated compatibility properties; original fixture stays outside .slnx and all frozen bytes remain. After-unit-tests executes its built DLL and strict existing `verify_results.py`; no hook rebuild. Requalify external successor locks/overlay to the released catalog. |
| `testsupport-windows` | Keep actual descendant/orphan cleanup/cancellation and TestSupport non-pack/non-publish checks. `.github/actions/testsupport-windows/action.yml` runs the built TestSupport.Tests DLL after rendered Windows prepare consumes CI outputs. Keep Linux TestSupport run too: it contains Linux-only path/symlink cases. Delete checkout-policy self-tests; safe protected checkout becomes generic Builds support and qualification. |
| `repository` | Delete root-submodule/index policy and checkout-policy gate. Product build dependencies are declared/checked by shared setup/perimeter and the normal test graph. |
| `admin-web` | Keep all Chromium rendering, responsive and accessibility product assertions. `browsers: true`; `tests.integration` includes `tests/Hexalith.Conversations.Admin.Web.Tests/Hexalith.Conversations.Admin.Web.Tests.csproj`. Shared environment setup replaces module install/rebuild steps. |
| `conformance` | Preserve product methods per the exact inventory below. Remove forbidden methods and Compile links, then shared per-project execution runs both tiers completely, unfiltered. |
| `tooling` / npm | Delete npm/signature/commitlint/release-orchestration self-check lane. Shared guard/release owns commit format, security and publication orchestration. Extract the nine product package/mapping tests listed below to `tests/tooling/test_package_contract.py`; retain three overlay product tests and run those through after-unit-tests. |
| `codeql`, `dependency-review`, legacy `commitlint`, legacy `release` | Owned workflows are replaced only by CiCd rendering/delivery. CodeQL and NuGet high/critical/unavailable-audit release enforcement remain in shared nightly release; shared guard owns commitlint. No module workflow-text assertions survive. |

Package inventory remains exactly `Hexalith.Conversations`, `.Contracts`, `.Client`,
`.Testing`, `.EventStoreExtensions`, through `tools/release-packages.json`.
Keep `scripts/release_contract.py` product inventory/version helpers and the two
product validators while removing their obsolete release-orchestration dependencies.
The old archive validator requires restore assets to record audit enabled/all;
that check is module CI-policy enforcement, incompatible with central audit-off CI.
Remove that redundant CI-policy predicate only. Keep actual restore identity,
package-mode dependency/payload/symbol/license/readme and consumer validations.
The shared nightly audit gate and absence of module audit waivers stay mandatory.

## Exact mixed-method extractions

1. `DerivedKeyLifecycleAdrValidationTest.EventStoreShouldRemainOnlyWriteAuthority`:
   keep the runtime key-builder inventory and every family key/prefix/independent
   encoding/tenant-segment assertion (source lines 125–146), and comparison against
   `ConversationProjectionStoreOptions.ConfigurationKey` at the method end. Express
   the same expected templates/tenant flags in a product test fixture independent of
   the signed decision envelope. Delete ADR file hashes, signed-payload/schema/source
   authority checks and assertions only about the prose decision's ownership, expiry,
   lifecycle/order/rollback declaration fields. Those latter declarations do not
   execute their claimed runtime behavior. Keep actual write/rebuild/failure tests in
   LiveProjectionFreshness, projection-read and IntegrationTests unchanged.
2. `ConformanceOracleTieringValidationTest.TieringShouldNotWidenPublicContracts`:
   extract the final `typeof(ClientAssemblyMarker).Assembly.GetExportedTypes()` exact
   sorted-name comparison against the reviewed client API baseline to neutral
   `ClientPublicApiConformanceTest.cs` in the portable project. Keep the baseline type
   names unchanged. Delete historical tier-disposition hashes, frozen source Git/index
   equality, test inventory/approval checks. All other methods in that old class retire.
   Current Contracts member-level API compatibility remains protected by the complete
   `PublicContractShapeSnapshotGenerationTest` suite.
3. `ReleaseBaselineValidationTest`: delete its first four story/run/test-suite-count
   methods. Keep the public-API baseline payload/header and live exported surface
   predicates in the next three methods. Extract the last method's current exported
   type-count plus captured-types-array-count checks; delete its historical
   `release-baseline-v1.json` report pointer/provenance comparisons. Keep neutral API
   expectations and snapshots rather than replacing them with a newly generated baseline.
4. `ReleaseConformanceArtifactGenerationTest.GenerateAndSaveFixtureArtifactFile`:
   preserve serialization/deserialization plus `ReleaseConformanceArtifactV1.ValidateArtifact`
   assertions in memory or an owned temporary fixture. Remove writes/reads of committed
   `docs/release-evidence/release-conformance-artifact-v1-fixture.json`.
   All its other production DTO/vocabulary/content-safety assertions stay.
5. Portable `ResolvedSurfaceShouldContainNoNonPackableModuleReference`: preserve the
   actual evaluated dependency closure/packability/ReferencePath/package-assets checks.
   Extract `_bmad/scripts/verify_conformance_tiering.py:msbuild` product evaluation and
   `portable_surface` into neutral `tests/compatibility/verify_portable_surface.py`,
   without story authority/report/approval/declaration modes or imports. Keep the
   dependency-free nonshipping TestSupport exception exactly. Use existing outputs,
   `ResolveReferences` with `BuildProjectReferences=false`, no rebuild. Refactor
   `Story92TieringVerification.cs` into a neutral product-only invoker; remove its main
   project link and the two story-tiering declaration/structure tests. No BMAD script
   runs in product CI.
6. The nine kept methods from `tests/tooling/test_release_tooling.py` move verbatim in
   product meaning into `tests/tooling/test_package_contract.py`; import only retained
   product helpers. Delete the old mixed file after extraction. Keep fixture/mapping
   isolation and all rejection cases. The source-edge assertion may be expressed via
   evaluated package-mode dependencies to accommodate the explicit isolated adapter;
   do not replace it with a blanket allowed sibling-source exception.
7. `test_minimal_module_compatibility_overlay.py`: retain three actual evaluated
   package/lock/framework/drift tests; physically delete only
   `test_compatibility_job_initializes_only_the_direct_catalog` because it asserts YAML.
   Preserve the exact seven-case execution verifier during real fixture execution.
   Its separate synthetic XML gate self-test file is retired from module automation.

`ArchitecturePlanningAuthorityValidationTest`'s last three methods check APIs named
in an architecture register by parsing historical root gitlink source, and self-test
that private planning parser. They do not check the packaged dependencies actually
compiled into this product, so the entire planning gate retires. This does not remove
runtime/compiled package API assertions from either product conformance tier.

## Compile-link and helper actions

For `tests/Hexalith.Conversations.Conformance.Portable.Tests/*.csproj`, remove every
`Compile Include` whose source file is DELETE below, keep links to all retained
product suites/fixtures/API tests, and add the extracted neutral Client API test.
For the main conformance .csproj remove matching stale `Compile Remove` entries for
physically deleted sources. Keep Remove entries for retained files linked into the
portable tier so no product test compiles twice. Drop the explicit linked
`Story92TieringVerification.cs` from main when removing its structure/declaration
wrapper; portable gets its neutral product-only invoker.

Delete unused `ConformanceTieringIlReferenceReader.cs`,
`ConformanceTierAssemblyInventory.cs` and `RepositoryEvidencePathResolver.cs` once
these exact callers are removed. Retain `ReleaseEvidenceArtifactCollection.cs`
while any retained test has its Collection attribute; update comments to describe
product fixture isolation, without weakening tests. Retain all product suite/helper
files in the source table, notably `ReleaseConformanceArtifactBuilder.cs`, the suite
fixture classes, `TelemetryValidationTestHelpers.cs` and Live* runtime fixtures.

## AppHost runtime and nested-build requirements

Keep both methods in
`tests/Hexalith.Conversations.AppHost.Tests/ConversationsAppHostRuntimeBoundaryTest.cs`:
`RetainedAppHostShouldRefuseCommandsWithoutCatalogAuthority` and
`GatewayProvenanceShouldUseTheOwningProjectFrameworkAndSdk`.

The first enables automatically under GitHub Actions, builds a separate owner gateway
fixture through `BuildEventStoreGatewayWithProvenanceAsync` before starting Aspire,
requires Dapr and asserts actual fail-closed command admission. The package-mode
fixture is Builds `src/hosts/Hexalith.Builds.Module.EventStoreHost`, not a sibling
EventStore source checkout. Its build stamps the actual owner revision/workspace
identity and selected SDK into SourceRevisionId/InformationalVersion, verifies binary
ProductVersion, then checks `.deps.json` uses the selected published Gateway package.
This is actual runnable fixture/provenance checking; do not drop it as a story gate.
It is a separate previously-unbuilt owner fixture, not permission to rebuild the
module solution from a custom action. The second evaluates its owner framework/path
and governed package SDK view (currently 4.2.0 for the packaged host).

Shared preparation must preserve validated `EnrolledReferenceMode`,
`EnrolledBuildsRoot`, `EnrolledEventStoreRoot`, `EnrolledEventStoreVersion`,
`EnrolledRepositoryRoot` assembly metadata and inherited `Configuration` plus
`HEXALITH_SOURCE_MAPPING_HASH`. `ReadProducerConfiguration` refuses a missing hash
or a mode/configuration mismatch; no fabricated hash/default is acceptable.
Keep all real projection/Dapr state end-state and six-seam tests in IntegrationTests,
Server.Tests and DeletionConformance.Tests; historical evidence checks listed DELETE
are not a substitute for their execution. `dapr: true` is required; browser setup is
Linux-only and Windows custom action has no environment setup.

## Retired tooling files and settings

- Root package.json/package-lock dependencies are only semantic-release/commitlint.
  Their Python npm-test wrapper does not justify retaining npm. Delete both after
  product Python invocations are wired through the enabled hook.
- Actual hooks are `.githooks/commit-msg` (retire obsolete module commitlint hook) and
  `.githooks/pre-commit` (keep independent whitespace check). No `.husky/` exists.
- Owned semantic-release/commitlint config and legacy workflows are deleted by
  renderer/delivery, never by module product preparation. Retire now-unused
  `scripts/release_state.py`, `scripts/verify-release-source.py`,
  `scripts/verify-release-state.py`, `scripts/validate-publication-preflight.sh`,
  `scripts/validate-release-secrets.sh`, `scripts/verify-semantic-release-plan.mjs`
  only after confirming retained product helpers no longer import them. They have no
  surviving product role in this inventory.
- `tools/tests/test_checkout_windows.py` and root-submodule script gate are CI policy
  tooling; retire their module gate. Generic protected-checkout qualification belongs
  in Builds/CiCd, with the accepted archive bytes preserved and no protectNTFS bypass.
- Root Directory.Build.props and frozen fixture Directory.Build.props contain audit
  warning waivers. Remove active module waivers; fixture-original-byte preservation
  requires explicit empty global WarningsNotAsErrors in its external adapter, so
  the old literal cannot demote warnings in the current graph. Only justified centrally released Builds Props waivers may
  remain. Do not suppress high/critical or unavailable-audit release results.

## Complete C# source and test-method disposition

### `tests/Hexalith.Conversations.Conformance.Portable.Tests/PortableCompileSurfaceValidationTest.cs`
**EXTRACT** — Keep actual compiled portable package/dependency boundary; replace BMAD verifier wrapper as specified above.
| Source line | Method | Disposition |
|---:|---|---|
| 15 | `ResolvedSurfaceShouldContainNoNonPackableModuleReference` | EXTRACT |

### `tests/Hexalith.Conversations.Conformance.Portable.Tests/Story92TieringVerification.cs`
**EXTRACT** — Replace broad BMAD modes with neutral product-only compiled dependency invoker; remove main-tier compilation link.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/AdopterConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/AdopterConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 31 | `SuiteShouldCoverEveryCoreConformanceCheck` | KEEP |
| 40 | `SuiteShouldPassEveryCheckAgainstTheSyntheticFixture` | KEEP |
| 49 | `SuiteShouldExerciseTheAc4ScenarioMatrix` | KEEP |
| 66 | `TenantBindingCheckShouldExerciseCrossTenantHiddenSideChannelShape` | KEEP |
| 83 | `EveryCheckShouldCarryTraceableRequirementPreconditionAndReleaseGateMappings` | KEEP |
| 96 | `IdempotencyCheckShouldSurfaceNonRetryableConflictAsBlocked` | KEEP |
| 108 | `ProjectionFreshnessCheckShouldSurfaceStaleAsDegradedNonTrustBearing` | KEEP |
| 119 | `CompatibilityDiscoveryCheckShouldSurfaceUnsupportedAsBlockedTypedError` | KEEP |
| 131 | `ErrorEnvelopeCheckShouldReuseSharedTypedErrorCatalog` | KEEP |
| 143 | `RunResultShouldSerializeToDeterministicWebJsonForCi` | KEEP |
| 159 | `RunResultShouldRoundTripAndRemainAdditiveTolerantForCi` | KEEP |
| 172 | `RunResultShouldRoundTripLosslesslyPreservingEveryCheckFieldForCi` | KEEP |
| 206 | `RunShouldExerciseTheReadyDegradedAndBlockedOutcomesAcrossChecks` | KEEP |
| 226 | `NonReadyChecksMustCarryTypedErrorsAndReadyChecksMustNot` | KEEP |
| 244 | `RunAggregationShouldBeDeterministicAndDegradedWhenAllChecksConformWithAStaleScenario` | KEEP |
| 261 | `EveryEmittedFailureClassificationMustBelongToTheClosedVocabulary` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ArchitecturePlanningAuthorityValidationTest.cs`
**DELETE** — Planning authority/register and historical dependency-source validation, including its parser self-tests; no executing current packaged module behavior.
| Source line | Method | Disposition |
|---:|---|---|
| 195 | `ArchitectureFrontmatterShouldBindCanonicalCurrentAuthority` | DELETE |
| 228 | `InitiativeAuthoritySourcesShouldRemainPinned` | DELETE |
| 242 | `ArchitectureShouldStateScopeAndPreservationDenominators` | DELETE |
| 263 | `ArchitectureRegistersExactInitiativeLandingZonesAndDeferredFrSixteen` | DELETE |
| 293 | `ArchitectureShouldResolveEveryOpenQuestionExactlyOnce` | DELETE |
| 330 | `SmCTwoShouldFreezeNonemptyInventoryAndOneToOneComparablePostResults` | DELETE |
| 368 | `TargetTreeAndReadinessShouldBeCorrectiveAndPlatformOwned` | DELETE |
| 461 | `CanonicalDomainHostPairShouldBeTaughtInCurrentAuthority` | DELETE |
| 481 | `NoTargetStateOwnershipOrUnqualifiedReadinessShouldSurviveAnywhereInTheDocument` | DELETE |
| 529 | `StillBindingReplayProjectionParticipantIdempotencyAndLegalRulesShouldRemain` | DELETE |
| 554 | `EpicPlanShouldPreserveHistoricalPrefixAndContainExactDispositionRows` | DELETE |
| 774 | `EpicOverlayShouldPreserveFullDenominatorAndCorrectiveFrCoverage` | DELETE |
| 831 | `EpicOverlayShouldBindTheDependencyOrderItAuthorizes` | DELETE |
| 999 | `EpicOverlayAndGeneratedContextShouldBeVersionAndStoryEquivalent` | DELETE |
| 1101 | `PromotionCompletionInvariantShouldBeScopedToDeclaredRootGitlinks` | DELETE |
| 1117 | `NamedPlatformLandingZonesShouldExposeSignatureCompatiblePublicApis` | DELETE |
| 1174 | `NamedPlatformTypesShouldBePublic` | DELETE |
| 1187 | `ConsumerReachabilityShouldBindEachMemberToItsDeclaringType` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/AtRiskTestRegisterGenerationTest.cs`
**DELETE** — Story disposition/at-risk inventory and generated evidence, not product execution.
| Source line | Method | Disposition |
|---:|---|---|
| 52 | `RegisterShouldEnumerateEveryAtRiskTestDeterministically` | DELETE |
| 65 | `EveryRetireOrRetargetEntryShouldNameItsOwningStory` | DELETE |
| 88 | `EveryReExpressionShouldBeGreenAndAnchored` | DELETE |
| 110 | `EveryStory21StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 127 | `EveryStory22StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 144 | `EveryStory23StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 161 | `EveryStory24StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 178 | `EveryStory25StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 195 | `EveryStory26StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 212 | `EveryStory27StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 229 | `EveryStory33StructuralDispositionShouldBeAnchoredAndGreen` | DELETE |
| 246 | `RegisterShouldBeContentSafe` | DELETE |
| 272 | `GenerateAndSaveAtRiskTestRegisterFile` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/BuyerAcceptanceConformanceFixtures.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/BuyerAcceptanceConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/BuyerAcceptanceConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 32 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 39 | `AllChecksShouldUseGovernancePreconditionCheckId` | KEEP |
| 46 | `AllPassScenariosShouldProduceReadyOutcome` | KEEP |
| 70 | `AllFailScenariosShouldProduceBlockedOutcomeWhenValidatorFails` | KEEP |
| 80 | `AllChecksShouldBeClassifiedAsConformant` | KEEP |
| 88 | `AllChecksShouldCarryFR102RequirementAndBuyerAcceptanceMappings` | KEEP |
| 101 | `PassScenariosShouldHaveNullTypedError` | KEEP |
| 113 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 121 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 152 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 187 | `NullScenariosListShouldThrow` | KEEP |
| 195 | `EmptyScenariosListShouldThrow` | KEEP |
| 203 | `NullCorrelationIdShouldThrow` | KEEP |
| 211 | `ExpiredItemShouldProduceConformantResult` | KEEP |
| 223 | `MissingAckShouldProduceConformantResult` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ClassificationChangeProcedureValidationTest.cs`
**DELETE** — Governance of the historical source-classification procedure and inventory.
| Source line | Method | Disposition |
|---:|---|---|
| 68 | `CommittedProcedureShouldBeAcceptedAndDeclareGovernance` | DELETE |
| 82 | `BothProcedureArtifactsAndTheGovernedInventoryShouldBeCommitted` | DELETE |
| 99 | `ChangeLogEntrySchemaShouldDefineBothEntryTypes` | DELETE |
| 128 | `WorkedExamplesShouldIncludeAnUpheldChallengeAndAReclassification` | DELETE |
| 140 | `EveryWorkedExampleShouldConformToItsTypeSchema` | DELETE |
| 160 | `EveryEntryShouldTargetARealInventoryAreaId` | DELETE |
| 182 | `FoldingEachReclassificationExampleShouldPreserveFr2InvariantAndRecomputePlumbing` | DELETE |
| 248 | `InventoryChangeLogShouldBeAnArrayAndEveryRealEntryShouldConform` | DELETE |
| 268 | `CommittedProcedureShouldPassScopedContentSafetyScan` | DELETE |
| 294 | `WorkedExampleEntriesShouldNotLeakIntoTheRealInventoryChangeLog` | DELETE |
| 315 | `ProcedureRecordedBaselineShouldMatchTheGovernedInventory` | DELETE |
| 335 | `ReclassificationEntriesShouldNotOverrideApproxLocOrPaths` | DELETE |
| 353 | `EveryReclassifiedChallengeShouldHaveAMatchingReclassificationEntry` | DELETE |
| 376 | `EveryRealReclassificationEntryShouldBeAppliedToTheLiveClassification` | DELETE |
| 400 | `GovernedInventoryShouldBackReferenceStoryOneFiveForBidirectionalDiscoverability` | DELETE |
| 410 | `EntryTemplateShouldProvideCopyPasteableShapesForBothTypes` | DELETE |
| 430 | `ProcedureMarkdownShouldDocumentTheFiveStepProcedureAndCanonicalLog` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceManifestValidationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 31 | `FixtureManifestShouldPassValidateManifestWithZeroErrors` | KEEP |
| 39 | `ManifestWithDuplicateTestIdShouldReturnDuplicateTestIdError` | KEEP |
| 57 | `ManifestWithWaivedEntryMissingWaiverReferenceShouldReturnMissingWaiverReferenceError` | KEEP |
| 88 | `AllFixtureEntriesShouldPassContentSafetyScan` | KEEP |
| 110 | `ManifestShouldSerializeToStableCamelCaseJsonAndRoundTripDeterministically` | KEEP |
| 131 | `LifecycleStageAllShouldReturnExactlySixStagesMatchingNfr1` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceOracleTieringValidationTest.cs`
**DELETE** — Historical test-tier approval/inventory/source-strength evidence; one live Client API assertion is extracted below.
| Source line | Method | Disposition |
|---:|---|---|
| 70 | `AssertionInventoryShouldMatchPreSplitResultAndSource` | DELETE |
| 183 | `ServerBoundAssertionsShouldHaveExactDisposition` | DELETE |
| 250 | `StrengthDigestsShouldRemainEqual` | DELETE |
| 306 | `DenominatorSuitesShouldRemainUnchanged` | DELETE |
| 371 | `ReclassificationsShouldBindApprovals` | DELETE |
| 483 | `TieringShouldNotWidenPublicContracts` | EXTRACT exact built Client exported-type comparison; DELETE frozen tier/source evidence wrapper |
| 529 | `V2ShouldSupersedeWithoutEditingV1` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceStatusConformanceFixtures.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceStatusConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceStatusConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 32 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 39 | `AllChecksShouldUseGovernancePreconditionCheckId` | KEEP |
| 46 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR99RequirementAndConformanceStatusMappings` | KEEP |
| 81 | `PreconditionMappingsShouldNotBeEmpty` | KEEP |
| 88 | `PassScenariosShouldHaveNullTypedError` | KEEP |
| 100 | `FailScenariosShouldHaveNonNullTypedError` | KEEP |
| 114 | `OnlyProductInvariantFailScenarioShouldHaveBlockingTrue` | KEEP |
| 124 | `WaivedGateScenarioShouldProduceReadyOutcome` | KEEP |
| 135 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 143 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 174 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 209 | `NullScenariosListShouldThrow` | KEEP |
| 217 | `NullCorrelationIdShouldThrow` | KEEP |
| 225 | `EmptyScenariosListShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceTierAssemblyInventory.cs`
**DELETE** — Only the retired baseline test-suite-count gate consumes the cross-tier test inventory.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ConformanceTieringIlReferenceReader.cs`
**DELETE** — Only the retired tiering-ledger verifier consumes this test-IL analyzer.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ConsumePromoteKeepInventoryValidationTest.cs`
**DELETE** — Historical migration/LOC/disposition inventory and its narrative artifacts.
| Source line | Method | Disposition |
|---:|---|---|
| 60 | `CommittedInventoryShouldBeAcceptedAndDeclareFr2Governance` | DELETE |
| 78 | `EveryAreaShouldAppearExactlyOnceWithASingleValidClassification` | DELETE |
| 98 | `EveryConsumeOrPromoteEntryShouldNameItsCapabilityFrAndOwningStory` | DELETE |
| 127 | `PromoteLaterCandidatesShouldBeKeptNowNotPromoted` | DELETE |
| 143 | `PerAreaLocShouldReconcileToTheRecordedSourceTotal` | DELETE |
| 161 | `PlumbingBaselineShouldEqualConsumePlusPromoteLoc` | DELETE |
| 181 | `CommittedInventoryShouldPassScopedContentSafetyScan` | DELETE |
| 200 | `BothJsonAndMarkdownSiblingArtifactsShouldBeCommitted` | DELETE |
| 213 | `Story62DispositionShouldPreserveSignedV1AndReproduceTheConsumedPath` | DELETE |
| 226 | `NoSourceFileShouldBeDoubleCountedAcrossAreas` | DELETE |
| 276 | `ReconciliationPerClassificationSubtotalsShouldBeConsistent` | DELETE |
| 302 | `RecordedPlumbingPercentageShouldMatchTheComputedRatio` | DELETE |
| 318 | `PlumbingDerivationRowsShouldEnumerateExactlyTheConsumeAndPromoteAreas` | DELETE |
| 332 | `AddendumFirstPassShouldBeExplicitlyConfirmedOrCorrected` | DELETE |
| 350 | `InventoryShouldRecordVersioningConventionAndLeaveOpenQuestionsOpen` | DELETE |
| 371 | `ConsumePromoteCrossReferencesShouldUseWellFormedFrAndStoryIdentifiers` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/ContractValidationConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ContractValidationConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 33 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 40 | `AllChecksShouldUseCompatibilityDiscoveryCheckId` | KEEP |
| 47 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR92RequirementAndContractCompatibilityGateMappings` | KEEP |
| 81 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 93 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 106 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 122 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 132 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 140 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 171 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 210 | `NullScenariosListShouldThrow` | KEEP |
| 218 | `EmptyScenariosListShouldThrow` | KEEP |
| 226 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ConversationProjectionReadSurfaceConformanceTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 58 | `RedactedMessageShouldStaySuppressedThroughPublicReadSurface` | KEEP |
| 79 | `GovernanceEvidenceShouldBeAnchoredThroughPublicReadSurface` | KEEP |
| 108 | `DegradedProjectionShouldNotExposeTrustBearingDetail` | KEEP |
| 136 | `PoisonProjectionShouldNotExposeDetailThroughPublicReadSurface` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/CoreFixtureContentSafetyTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 46 | `ConformanceRunResultShouldNotLeakPoisonSentinels` | KEEP |
| 58 | `ConformanceRunResultShouldNotLeakProtectedIdentifiersOrInfrastructureTerms` | KEEP |
| 75 | `TypedFailureCasesShouldRemainContentSafeOnTheWire` | KEEP |
| 101 | `CrossTenantDenialShouldUseHiddenShapeAndNotRevealExistence` | KEEP |
| 116 | `FixtureShouldBeMarkedSyntheticAndDeterministic` | KEEP |
| 130 | `PoisonProjectionShouldCarrySentinelsThatNeverAppearInAuthorizedSurfaces` | KEEP |
| 149 | `ConformanceRunResultShouldPreserveClosedTraceabilityTokensContainingTenantAndPartySegments` | KEEP |
| 163 | `CrossTenantDenialShouldNotCarryClientActionThatDistinguishesExistence` | KEEP |
| 175 | `EveryTypedFailureFixtureScenarioShouldExposeOnlySafeStructuredFields` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/DerivedKeyLifecycleAdrValidationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 97 | `EventStoreShouldRemainOnlyWriteAuthority` | EXTRACT runtime key/configuration assertions; DELETE signed ADR/declaration-only evidence wrapper |

### `tests/Hexalith.Conversations.Conformance.Tests/EventSchemaEvolutionConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/EventSchemaEvolutionConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 33 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 40 | `AllChecksShouldUseEventPublicationCheckId` | KEEP |
| 47 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR91RequirementAndSchemaEvolutionGateMappings` | KEEP |
| 81 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 93 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 106 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 122 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 132 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 140 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 171 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 210 | `NullScenariosListShouldThrow` | KEEP |
| 218 | `EmptyScenariosListShouldThrow` | KEEP |
| 226 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/EvidenceBoundaryAdoptionValidationTest.cs`
**DELETE** — BMAD evidence-reader adoption inventory and runbook/skill controls.
| Source line | Method | Disposition |
|---:|---|---|
| 19 | `ReaderInventoryShouldMatchFrozenSet` | DELETE |
| 23 | `MigrationsShouldUseHelperAtEqualStrength` | DELETE |
| 27 | `DayOneExemptionInventoryShouldBeEmpty` | DELETE |
| 31 | `KnownGitDefectsShouldBeClosedWithoutChangingProjectionProof` | DELETE |
| 49 | `RunbookShouldDocumentTheExactContract` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/FinalConformanceContractDiffEvidenceValidationTest.cs`
**DELETE** — Historical story diff/count/approval record validation; live API protection stays in PublicContractShapeSnapshotGenerationTest.
| Source line | Method | Disposition |
|---:|---|---|
| 34 | `JsonAndMarkdownArtifactsShouldExistAndBeInternallyConsistent` | DELETE |
| 54 | `JsonShouldReferenceStoryOneOneBaselinesAndExactFinalConformanceCounts` | DELETE |
| 93 | `ContractShapeDiffShouldBeEmptyOrCarryApprovalReferences` | DELETE |
| 117 | `EvidenceShouldNotUseBuildArtifactsGeneratedOutputOrLocalPathsAsSourceOfTruth` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/GovernanceAuditPairingSafetyNetConformanceTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 62 | `EveryGovernanceMutationShouldPairItsEventWithAuditEvidence` | KEEP |
| 98 | `GovernanceMutationWithMissingAuditEvidenceShouldFailClosed` | KEEP |
| 127 | `GovernanceMutationWithMismatchedAuditEvidenceShouldFailClosed` | KEEP |
| 149 | `NonGovernanceCommandsShouldEmitEventsWithoutAuditEvidenceDependency` | KEEP |
| 180 | `AggregateGovernanceCommandSurfaceShouldMatchTheAuditPairedInventory` | KEEP |
| 219 | `FutureGovernanceVocabularyShouldNotAppearAsImplementedMutationPaths` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/GovernanceAuditSinkFailClosedConformanceTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 65 | `GovernedMutationShouldFailClosedWhenAuditSinkThrows` | KEEP |
| 91 | `GovernedMutationShouldEmitEventWhenAuditSinkHealthy` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/IdempotencyConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/IdempotencyConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 33 | `RunResultShouldHaveExactly8Checks` | KEEP |
| 40 | `AllChecksShouldUseIdempotencyCheckId` | KEEP |
| 47 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR88RequirementAndIdempotencyMappings` | KEEP |
| 81 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 93 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 106 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 122 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 132 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 140 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 171 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 210 | `NullScenariosListShouldThrow` | KEEP |
| 218 | `EmptyScenariosListShouldThrow` | KEEP |
| 226 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/LiveIdempotencyConflictOracleCharacterizationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 53 | `LiveExecutorShouldRejectConflictingKeyReuseWithoutMutation` | KEEP |
| 89 | `LiveExecutorShouldReturnRetryableUncertaintyForPendingKeyWithoutMutation` | KEEP |
| 123 | `LiveExecutorShouldPreserveOriginalReasonCodeOnDuplicateRejectionReplay` | KEEP |
| 162 | `LiveExecutorReplayPayloadShouldExcludeCallerSuppliedSecrets` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/LiveIdempotencyOracleCharacterizationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 46 | `LiveExecutorShouldReplayDuplicateWithoutReinvokingMutation` | KEEP |
| 82 | `LiveExecutorShouldInvokeMutationOnceForFirstSubmission` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/LiveProjectionFreshnessOracleCharacterizationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 49 | `LiveMaterializerShouldReportCurrentProjectionAsTrustBearing` | KEEP |
| 66 | `LiveMaterializerShouldSurfaceStaleProjectionAsNonTrustBearing` | KEEP |
| 85 | `LiveMaterializerShouldSurfaceGapAsRebuildingNonTrustBearing` | KEEP |
| 103 | `LiveMaterializerShouldSurfaceActiveRebuildAsNonTrustBearing` | KEEP |
| 121 | `LiveMaterializerShouldSurfaceMetadataWriteFailureAsUnavailable` | KEEP |
| 141 | `LiveMaterializerShouldSuppressRedactedContentWhenMessageReplaysAfterRedaction` | KEEP |
| 165 | `LiveMaterializerShouldPairEveryGovernanceMutationWithAuditEvidence` | KEEP |
| 193 | `LiveFreshnessClassifierShouldNeverPromoteDegradedStatesToCurrent` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/LiveTenantFailClosedOracleCharacterizationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 98 | `LiveServiceShouldFailClosedOnEveryReleaseGateTriggerState` | KEEP |
| 122 | `LiveServiceShouldFailClosedWhenTenantBindingIsMissing` | KEEP |
| 143 | `LiveServiceShouldFailClosedWhenTenantIdIsMalformed` | KEEP |
| 166 | `LiveServiceShouldFailClosedWhenCallerPrincipalIsMalformed` | KEEP |
| 187 | `LiveServiceShouldDenyCrossTenantMemberLeakage` | KEEP |
| 216 | `LiveServiceShouldDenyContradictoryTenantBindings` | KEEP |
| 238 | `LiveGuardShouldNotRunProtectedOperationWhenLiveServiceDenies` | KEEP |
| 268 | `LiveServiceShouldAllowAuthorizedOwner` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/NoInModuleSharedFakeDuplicateConformanceTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 61 | `NoInModuleActorStateManagerDuplicateShouldExist` | KEEP |
| 72 | `NoInModuleEventStoreGatewayClientDuplicateShouldExist` | KEEP |
| 82 | `NoInModuleDomainResultAssertionsDuplicateShouldExist` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/OqTwoTargetInterpretationDecisionValidationTest.cs`
**DELETE** — Historical open-question approval and success-metric evidence.
| Source line | Method | Disposition |
|---:|---|---|
| 29 | `DecisionArtifactsShouldExistAndRecordApprovedResolution` | DELETE |
| 56 | `SmOneTargetShouldRecomputeAndBeMetInclusively` | DELETE |
| 79 | `SmTwoTargetShouldRecomputeAndRemainEstimateQualified` | DELETE |
| 119 | `HistoricalEvidenceBindingsShouldMatchAndRemainPointInTimeEvidence` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/OracleBlindSpotAnalysisArtifactGenerationTest.cs`
**DELETE** — Generates/validates retrospective blind-spot analysis evidence rather than exercising the listed production paths.
| Source line | Method | Disposition |
|---:|---|---|
| 55 | `BuiltArtifactShouldBeStructurallyComplete` | DELETE |
| 91 | `BuiltArtifactShouldBeDeterministic` | DELETE |
| 99 | `ArtifactShouldPassContentSafetyScan` | DELETE |
| 109 | `GenerateAndSaveArtifactFile` | DELETE |
| 130 | `CommittedHeaderShouldDescribeTheArtifact` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/PackageEnvironmentAuthorityV18ValidationTest.cs`
**DELETE** — Planning tooling/package environment authority and historical workflow blob assertions.
| Source line | Method | Disposition |
|---:|---|---|
| 84 | `V18AuthorityShouldBindExactPackageEnvironmentAtAnyDescendant` | DELETE |
| 121 | `V18AuthorityNamedClosedContractFaultShouldBeRejected` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/PlanningAuthorityV8ValidationTest.cs`
**DELETE** — Planning bundle/story/status/UX authority checks.
| Source line | Method | Disposition |
|---:|---|---|
| 39 | `V8ShouldPublishOneCompleteCurrentStorySetWithoutAuthorizingImplementation` | DELETE |
| 89 | `CurrentViewShouldBeHashBoundAndStoryEquivalentToV8` | DELETE |
| 140 | `V8DependencyGraphShouldBeClosedAndAcyclic` | DELETE |
| 183 | `MetricAndReadinessAuthorityShouldBeConsistentAndOutcomeNeutral` | DELETE |
| 209 | `UxPlanningShouldHaveCanonicalProvenanceAndZeroGapPreservationMapping` | DELETE |
| 263 | `SprintAndActiveGuidanceShouldPreserveStatusesAndEnforceTheHold` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/PlanningAuthorityV9ValidationTest.cs`
**DELETE** — Planning workflow/customization/source authority inventories.
| Source line | Method | Disposition |
|---:|---|---|
| 54 | `V14AuthorityShouldPreservePriorBlocksAndPublishEpic16` | DELETE |
| 159 | `AuthorityBundleShouldBindEveryCompanionWithoutSelfReference` | DELETE |
| 259 | `StoryContractsAndExecutionGraphShouldBeCompleteAndAcyclic` | DELETE |
| 351 | `StorySliceAuthorityShouldBindBaseContractAndCanonicalAmendment` | DELETE |
| 411 | `RemediationAuthorityShouldBindExactActionsRoutesGitlinksAndCompletionEffect` | DELETE |
| 451 | `WorkflowAndGuidanceInventoriesShouldMatchRoutesAndResolvedCustomization` | DELETE |
| 490 | `SupersessionUxAndSprintProjectionsShouldPreserveEveryFrozenBoundary` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/PlanningToolingEnvironmentAuthorityV15ValidationTest.cs`
**DELETE** — BMAD tooling environment authority/fault-control checks.
| Source line | Method | Disposition |
|---:|---|---|
| 77 | `V15AuthorityShouldBindExactEnvironmentAndOriginalPublication` | DELETE |
| 120 | `V15AuthorityNamedClosedContractFaultShouldBeRejected` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/PlanningToolingLifecycleAuthorityV16ValidationTest.cs`
**DELETE** — BMAD lifecycle environment authority/fault-control checks.
| Source line | Method | Disposition |
|---:|---|---|
| 89 | `V16AuthorityShouldBindExactLifecycleAtAnyDescendant` | DELETE |
| 128 | `V16AuthorityNamedClosedContractFaultShouldBeRejected` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/PlatformEvidenceSeparationConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/PlatformEvidenceSeparationConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 33 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 40 | `AllChecksShouldUseGovernancePreconditionCheckId` | KEEP |
| 47 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR94RequirementAndPlatformEvidenceGateMappings` | KEEP |
| 81 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 93 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 106 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 122 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 132 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 140 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 171 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 210 | `NullScenariosListShouldThrow` | KEEP |
| 218 | `EmptyScenariosListShouldThrow` | KEEP |
| 226 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/PreservationTraceabilityManifestValidationTest.cs`
**DELETE** — Story/UX/requirement inventories, approval bindings and historical source hashes.
| Source line | Method | Disposition |
|---:|---|---|
| 119 | `V2SchemaShouldBeSeparateClosedAndGoverned` | DELETE |
| 148 | `RequirementAndUxDenominatorsShouldMatchIndependentExtraction` | DELETE |
| 171 | `PublicSurfacesAndConformanceAssertionsShouldHaveZeroGap` | DELETE |
| 192 | `BindingsClosuresAndFrozenV1BytesShouldValidateIndependently` | DELETE |
| 288 | `CurrentControlsAndTierPrerequisiteShouldStayTruthful` | DELETE |
| 381 | `MarkdownProjectionShouldBeByteExact` | DELETE |
| 389 | `FaultInjectedCandidatesShouldFailWithStableDiagnostics` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/ProjectionReadStorePopulationProofValidationTest.cs`
**DELETE** — Validates historical proof JSON, source/Git bindings, retained runs and story-completion claims; live runtime/projection tests remain elsewhere.
| Source line | Method | Disposition |
|---:|---|---|
| 71 | `ProofShouldBindExactProductionRouteKeysAndBoundedOutcomes` | DELETE |
| 300 | `RecordedPromotionCandidateShouldStillDescribeTheCurrentGitlinks` | DELETE |
| 331 | `AFailingProofResultMustBlockStoryCompletion` | DELETE |
| 360 | `GatewayBoundaryEvidenceShouldCrossTheCoordinatorAndTheDaprStateStore` | DELETE |
| 411 | `Ac5AndAc6ClaimsShouldBeBoundToPassingMachineReadableRuns` | DELETE |
| 467 | `ProofSourceAndSignedV1BindingsShouldRemainByteIdentical` | DELETE |
| 532 | `SmC2PostShouldUseIdenticalEnvelopeAndRecordEveryMechanicalP95Result` | DELETE |
| 668 | `MarkdownShouldPresentTheAuthoritativeJsonBoundary` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/ProviderPortabilityConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ProviderPortabilityConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 33 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 40 | `AllChecksShouldUseEventPublicationCheckId` | KEEP |
| 47 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR90RequirementAndPortabilityGateMappings` | KEEP |
| 81 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 93 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 106 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 122 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 132 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 140 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 171 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 210 | `NullScenariosListShouldThrow` | KEEP |
| 218 | `EmptyScenariosListShouldThrow` | KEEP |
| 226 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/PublicContractShapeSnapshotGenerationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 89 | `SnapshotShouldCaptureExportedPublicTypesDeterministically` | KEEP |
| 100 | `CurrentSnapshotShouldMatchCommittedBaselineWithoutWriting` | KEEP |
| 117 | `CurrentSuccessorShouldPreserveEveryPriorTypeAndMemberOutsideTheApprovedAdditions` | KEEP |
| 152 | `ByReferenceTypeNamesShouldPreserveTheirSemanticElementShape` | KEEP |
| 160 | `LegacyCoreLibraryVersionsShouldCompareAsTheSameParameterShape` | KEEP |
| 169 | `LiveByReferenceTypesShouldPreserveForeignArgumentAssemblyIdentity` | KEEP |
| 192 | `LegacyByReferenceArraysShouldMatchLiveShapesWithoutLosingRank` | KEEP |
| 202 | `NestedGenericByReferenceTypesShouldRetainDeclaringAndNestedNames` | KEEP |
| 217 | `MalformedLegacyAssemblyMetadataShouldRemainUnequal` | KEEP |
| 231 | `LegacyParameterComparisonShouldStillDetectContractDrift` | KEEP |
| 254 | `LegacyParameterNormalizationShouldRefuseOtherAssemblyIdentities` | KEEP |
| 264 | `LegacyContractAssemblyIdentityShouldRemainExact` | KEEP |
| 286 | `LegacyNormalizationShouldTouchOnlyParameterTypeSlots` | KEEP |
| 306 | `SnapshotShouldCoverAllSixReleaseGateBehaviorAreas` | KEEP |
| 324 | `SnapshotShouldBeContentSafe` | KEEP |
| 353 | `GenerateAndSaveContractShapeSnapshotFile` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/RedactionConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/RedactionConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 33 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 40 | `AllChecksShouldUseGovernancePreconditionCheckId` | KEEP |
| 47 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 60 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 68 | `AllChecksShouldCarryFR89RequirementAndRedactionGateMappings` | KEEP |
| 81 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 93 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 106 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 122 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 132 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 140 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 171 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 210 | `NullScenariosListShouldThrow` | KEEP |
| 218 | `EmptyScenariosListShouldThrow` | KEEP |
| 226 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseBaselineValidationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 87 | `CommittedBaselineRecordShouldExistAndDescribeAGreenAllPassOracle` | DELETE historical result/test-inventory evidence |
| 106 | `BaselineCommitShouldBeAFullFortyCharacterHexShaOnMain` | DELETE historical result/test-inventory evidence |
| 122 | `BaselineEnumeratedSuiteClassesShouldMatchTheActualSuiteClassesInTheAssembly` | DELETE historical result/test-inventory evidence |
| 146 | `BaselineSurvivabilityClassificationShouldAccountForAllFourteenSuites` | DELETE historical result/test-inventory evidence |
| 163 | `CommittedSnapshotShouldExistAndDeclareItsAssemblyAndTypeCount` | KEEP public API snapshot fixture/live-surface integrity |
| 178 | `CommittedSnapshotTypeCountShouldMatchTheLiveExportedContractSurface` | KEEP public API snapshot fixture/live-surface integrity |
| 193 | `CommittedSnapshotCapturedSurfaceShouldPassContentSafetyScan` | KEEP public API snapshot fixture/live-surface integrity |
| 209 | `BaselineReportedTypeCountShouldAgreeWithTheCommittedSnapshotAndLiveSurface` | EXTRACT current live exported/captured type counts; DELETE historical report pointer checks |

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseConformanceArtifactBuilder.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseConformanceArtifactGenerationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 49 | `BuilderShouldProduceValidArtifactFromCoreFixture` | KEEP |
| 58 | `ArtifactShouldContainAllSevenRequiredGateEntries` | KEEP |
| 71 | `OverallStatusShouldBeDeterministicAcrossRuns` | KEEP |
| 80 | `AuditIntegrityGateShouldBePassWhenGovernancePreconditionIsReady` | KEEP |
| 93 | `TenantIsolationGateShouldBeUnknownAcceptedBecauseTenantBindingUsesUnknownOutcome` | KEEP |
| 106 | `ProviderPortabilityGateShouldAlwaysBeUnknownAcceptedWithNoAdopterMapping` | KEEP |
| 118 | `AllGateStatusesShouldBelongToTheClosedVocabulary` | KEEP |
| 126 | `ArtifactContentSafetyScanShouldPass` | KEEP |
| 148 | `BuilderShouldRejectNullConformanceRunResult` | KEEP |
| 161 | `BuilderShouldRejectNullSignerOrRunnerId` | KEEP |
| 174 | `BuilderShouldBeFullyDeterministicWithSameInputs` | KEEP |
| 186 | `GenerateAndSaveFixtureArtifactFile` | EXTRACT product DTO round-trip/validation; DELETE committed evidence output |

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseEvidenceArtifactCollection.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseScopeConformanceFixtures.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseScopeConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseScopeConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 32 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 39 | `AllChecksShouldUseGovernancePreconditionCheckId` | KEEP |
| 46 | `AllPassScenariosShouldProduceReadyOutcome` | KEEP |
| 72 | `AllFailScenariosShouldProduceBlockedOutcomeWhenValidatorFails` | KEEP |
| 83 | `AllChecksShouldBeClassifiedAsConformant` | KEEP |
| 91 | `AllChecksShouldCarryFR100RequirementAndReleaseScopeMappings` | KEEP |
| 104 | `PassScenariosShouldHaveNullTypedError` | KEEP |
| 116 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 124 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 155 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 190 | `NullScenariosListShouldThrow` | KEEP |
| 198 | `EmptyScenariosListShouldThrow` | KEEP |
| 206 | `NullCorrelationIdShouldThrow` | KEEP |
| 214 | `DeferredNoAreasShouldProduceConformantResult` | KEEP |
| 226 | `WaivedNoRefShouldProduceConformantResult` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/ReleaseWaiverValidationTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 36 | `FixtureWaiverShouldPassValidateWaiverWithZeroErrors` | KEEP |
| 44 | `BlockerWithNullApproverShouldReturnBlockerRequiresApproverError` | KEEP |
| 52 | `WaiverWithPastExpiryDateShouldReturnExpiredWaiverError` | KEEP |
| 60 | `WaiverWithPastReviewDateShouldReturnStaleReviewDateError` | KEEP |
| 68 | `FixtureWaiverShouldPassContentSafetyScan` | KEEP |
| 90 | `WaiverShouldSerializeToStableCamelCaseJsonAndRoundTripDeterministically` | KEEP |
| 108 | `WaiverLifecycleStatusAllShouldReturnExactlyFourValues` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/RemovedTestJustificationLedgerReconciliationValidationTest.cs`
**DELETE** — Historical removed-test ledger/disposition/story evidence.
| Source line | Method | Disposition |
|---:|---|---|
| 63 | `JsonAndMarkdownArtifactsShouldExistAndExposeStoryFiveThreeFields` | DELETE |
| 87 | `SourceArtifactsShouldReferenceDurableRepositoryFiles` | DELETE |
| 115 | `EveryAtRiskRegisterEntryShouldBeAccountedFor` | DELETE |
| 158 | `EveryStructuralDispositionSectionShouldBeAccountedFor` | DELETE |
| 182 | `ActualRemovalsShouldBeDeadPlumbingAndNeverDeleteRowsShouldStillExist` | DELETE |
| 224 | `ConformanceSuiteContinuityShouldMatchCurrentTreeAndStoryFiveOneEvidence` | DELETE |
| 259 | `ProjectReferenceDispositionShouldMatchCurrentProjectAndServerUsingInventory` | DELETE |
| 316 | `InventoryChangeLogAndContractShapeImpactShouldBePreserved` | DELETE |
| 341 | `EvidenceShouldNotUseBuildArtifactsGeneratedOutputOrLocalPathsAsSourceOfTruth` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/RepositoryEvidencePathResolver.cs`
**DELETE** — Only retired historical-source/evidence gates consume this nested evidence resolver.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/SecondAdopterConformanceFixtures.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/SecondAdopterConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/SecondAdopterConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 32 | `RunResultShouldHaveExactly10Checks` | KEEP |
| 39 | `AllChecksShouldUseGovernancePreconditionCheckId` | KEEP |
| 46 | `AllPassScenariosShouldProduceReadyOutcome` | KEEP |
| 69 | `AllFailScenariosShouldProduceBlockedOutcomeWhenValidatorFails` | KEEP |
| 79 | `AllChecksShouldBeClassifiedAsConformant` | KEEP |
| 87 | `AllChecksShouldCarryFR103RequirementAndSecondAdopterMappings` | KEEP |
| 100 | `PassScenariosShouldHaveNullTypedError` | KEEP |
| 112 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 120 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 151 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 186 | `NullScenariosListShouldThrow` | KEEP |
| 194 | `EmptyScenariosListShouldThrow` | KEEP |
| 202 | `NullCorrelationIdShouldThrow` | KEEP |
| 210 | `MilestoneOverdueShouldProduceConformantResult` | KEEP |
| 219 | `RevertedNoRationaleShouldProduceConformantResult` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/SmC2BaselineReconstructionValidationTest.cs`
**DELETE** — Historical benchmark reconstruction/provenance and recorded workload manifest, not the current product benchmark.
| Source line | Method | Disposition |
|---:|---|---|
| 47 | `BaselineShouldRecordAnAuditableReconstructionMethod` | DELETE |
| 86 | `EvaluatedProjectGraphShouldMatchTheRecordedWorkloadManifest` | DELETE |
| 143 | `GitShouldConfirmTheFixtureIsAbsentAndTheBaselineSubmoduleIsPinned` | DELETE |
| 175 | `MarkdownShouldPresentTheReconstructionProvenance` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/Story92/ConformanceOracleTieringValidationTest.cs`
**DELETE** — Story-specific assertion inventory/solution/workflow declaration wrappers; keep the separate product portability test.
| Source line | Method | Disposition |
|---:|---|---|
| 15 | `PostSplitAssertionInventoryShouldEqualApprovedDisposition` | DELETE |
| 20 | `BothTiersShouldBeDeclaredEverywhere` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/StoryFinalRecordGenerationValidationTest.cs`
**DELETE** — BMAD skills/final-record generation and completion-gate self-tests.
| Source line | Method | Disposition |
|---:|---|---|
| 131 | `GeneratorMustExistAndExposeTheContractedInvocationSurface` | DELETE |
| 149 | `EveryCompletionSurfaceMustInvokeTheGeneratorAndEnforceItsBlockers` | DELETE |
| 178 | `CodeReviewMustRequireExplicitCommitAuthorizationBeforeGating` | DELETE |
| 212 | `RemovingTheGateHeadingMustBeDetected` | DELETE |
| 228 | `GuttingTheGateBodyWhileKeepingTheHeadingMustBeDetected` | DELETE |
| 250 | `AnEnforcementClauseDisplacedOutsideTheGateSpanMustNotSatisfyTheContract` | DELETE |
| 276 | `ReorderingEnforcementClausesMustBeDetected` | DELETE |
| 321 | `RemovingFinalRecordDependencyFromCompletionMustBeDetected` | DELETE |
| 338 | `BothSkillTreesMustStayByteIdenticalForEverySkillFileThisStoryChanged` | DELETE |
| 352 | `TheStoryRecordMustCarryExactlyOneFileListAndNoSubmoduleInternalPath` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/SuccessMetricReportAndAttestationValidationTest.cs`
**DELETE** — Signed historical metric/attestation/source evidence checks.
| Source line | Method | Disposition |
|---:|---|---|
| 115 | `JsonAndMarkdownArtifactsShouldExistAndExposeRequiredFields` | DELETE |
| 142 | `SourceArtifactsShouldBeRepositoryRelativeExistingFilesWithHashes` | DELETE |
| 175 | `SignedReleaseOwnerDecisionShouldStillBindTheImmutableV1ReportAndSourceIdentity` | DELETE |
| 210 | `SourceArtifactsShouldBindToSignedV1ContentAtItsDeclaredSourceIdentity` | DELETE |
| 278 | `SupersessionAllowlistShouldStayNarrowAndExcludeSignedEvidence` | DELETE |
| 294 | `ArchivedLegacyPrdRelocationShouldStayNarrowAndContentIdentical` | DELETE |
| 308 | `SmOneFactsShouldMatchAcceptedInventoryAndRowDispositionMath` | DELETE |
| 373 | `SmOneRowEvidenceShouldBePartOfSignedSourceManifest` | DELETE |
| 401 | `SignablePayloadHashShouldMatchSourceArtifactManifest` | DELETE |
| 422 | `SmTwoFactsShouldMatchStoryFourTwoEvidenceWithoutClosingOqTwo` | DELETE |
| 441 | `BehaviorPreservationAndRemovedTestFactsShouldMatchSourceArtifacts` | DELETE |
| 474 | `ResidualRisksAndAttestationShouldBeSignableButUnsigned` | DELETE |
| 523 | `FinalDiffShouldMatchIntendedEvidenceBoundaryAndExcludeSubmoduleGitlinks` | DELETE |
| 570 | `EvidenceShouldNotUseBuildArtifactsGeneratedOutputOrLocalPathsAsSourceOfTruth` | DELETE |

### `tests/Hexalith.Conversations.Conformance.Tests/TelemetryCardinalityConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/TelemetryCardinalityConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 30 | `CommandRejectionClassShouldHaveFixedCardinalityBudget` | KEEP |
| 34 | `TenantDenialClassShouldHaveFixedCardinalityBudget` | KEEP |
| 38 | `PrivilegedAccessClassShouldHaveFixedCardinalityBudget` | KEEP |
| 42 | `ProjectionFreshnessClassShouldHaveFixedCardinalityBudget` | KEEP |
| 46 | `ProjectionLagClassShouldHaveFixedCardinalityBudget` | KEEP |
| 50 | `PublicationFailureClassShouldHaveFixedCardinalityBudget` | KEEP |
| 54 | `ConformanceStatusClassShouldHaveFixedCardinalityBudget` | KEEP |
| 58 | `TenantAccessRequirementShouldHaveFixedCardinalityBudget` | KEEP |
| 62 | `EveryClosedVocabularyEnumShouldStayWithinASmallBudgetCeiling` | KEEP |
| 79 | `ApprovedGateIdVocabularyShouldBeBoundedAndSmall` | KEEP |
| 89 | `EachCounterShouldOnlyEverEmitItsApprovedDimensionKeySet` | KEEP |
| 112 | `EveryApprovedCounterShouldBeExercisedUnderLoad` | KEEP |
| 128 | `DistinctDimensionValuesUnderLoadShouldStayWithinTheApprovedClosedVocabulary` | KEEP |
| 151 | `DistinctDimensionValueCountPerKeyShouldNotExceedItsCardinalityBudget` | KEEP |
| 174 | `HighCardinalityLoadShouldProduceManyMeasurementsButFewDistinctTagValues` | KEEP |
| 192 | `GateIdShouldBeTheOnlyDimensionCarryingValuesOutsideClassAndBooleanVocabularies` | KEEP |
| 219 | `EveryEmittedGateIdUnderLoadShouldBeWithinTheBoundedApprovedSet` | KEEP |
| 235 | `CardinalityGateShouldRejectUnboundedOrRawGateIdValues` | KEEP |
| 257 | `CardinalityGateShouldAcceptEveryApprovedGateId` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/TelemetryDisclosureConformanceFixtures.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/TelemetryRedactionConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/TelemetryRedactionConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 25 | `RunShouldEmitAtLeastOneMeasurementPerCounter` | KEEP |
| 46 | `EveryMeasurementShouldCarryOnlyApprovedDimensionKeys` | KEEP |
| 63 | `NoMeasurementDimensionShouldEverCarryAForbiddenValue` | KEEP |
| 83 | `NoMeasurementDimensionShouldCarryRawIdentifierShapes` | KEEP |
| 119 | `ClassDimensionsShouldOnlyCarryClosedVocabularyTokens` | KEEP |
| 142 | `BooleanDimensionsShouldOnlyCarryBoundedTrueOrFalseTokens` | KEEP |
| 164 | `GateIdDimensionShouldOnlyCarryApprovedBoundedGateIds` | KEEP |
| 182 | `GateIdShouldBeTheOnlyStringDimensionOutsideTheClassAndBooleanVocabularies` | KEEP |
| 203 | `NoStructuredLogMessageShouldEverCarryAForbiddenValue` | KEEP |
| 220 | `StructuredLogMessagesShouldNotCarryTenantOrPartyOrConversationIdShapes` | KEEP |
| 246 | `EveryTelemetrySurfaceShouldRejectTheSentinelNoneValue` | KEEP |
| 263 | `NoneSentinelGuardShouldPreventEmissionOfANoneDimensionValue` | KEEP |
| 279 | `FixtureForbiddenValuesShouldCoverEveryRequiredDisclosureClass` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/TelemetryValidationTestHelpers.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/TenantIsolationConformanceSuite.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
No Fact/Theory method declarations; apply this disposition to the helper/fixture source and its compilation links.

### `tests/Hexalith.Conversations.Conformance.Tests/TenantIsolationConformanceSuiteTest.cs`
**KEEP** — Product conformance/contract/runtime behavior, required fixture or supporting product helper. Preserve complete assertions and data rows.
| Source line | Method | Disposition |
|---:|---|---|
| 32 | `RunResultShouldHaveExactly12Checks` | KEEP |
| 39 | `AllChecksShouldUseTenantBindingCheckId` | KEEP |
| 46 | `EachScenarioShouldProduceExpectedConformanceOutcome` | KEEP |
| 59 | `EachScenarioCheckShouldBeClassifiedAsConformant` | KEEP |
| 67 | `AllChecksShouldCarryFR87RequirementAndTenantIsolationGateMappings` | KEEP |
| 80 | `ReadyScenariosShouldHaveNullTypedError` | KEEP |
| 92 | `BlockedScenariosShouldHaveNonNullTypedError` | KEEP |
| 105 | `UnknownScenariosShouldCarryAggregateNotFoundTypedError` | KEEP |
| 121 | `AllConformantScenariosProduceOverallReadyOutcome` | KEEP |
| 131 | `SuiteIdAndRunnerIdShouldMatchSpecifiedValues` | KEEP |
| 139 | `RunResultShouldNotLeakPoisonSentinelsOrForbiddenFragments` | KEEP |
| 170 | `RunResultShouldSerializeToStableCamelCaseJsonAndRoundTrip` | KEEP |
| 209 | `NullScenariosListShouldThrow` | KEEP |
| 217 | `EmptyScenariosListShouldThrow` | KEEP |
| 225 | `NullCorrelationIdShouldThrow` | KEEP |

### `tests/Hexalith.Conversations.Conformance.Tests/UxPreservationDispositionValidationTest.cs`
**DELETE** — Historical UX approval and frozen planning/evidence boundaries.
| Source line | Method | Disposition |
|---:|---|---|
| 27 | `PreservedBundleShouldPassZeroGapVerification` | DELETE |
| 95 | `SourcesShouldBindCanonicalPathsVersionsAndHashes` | DELETE |
| 128 | `DecisionsShouldProjectTheFrozenInventory` | DELETE |
| 150 | `AcceptanceCriteriaShouldProjectTheFrozenInventory` | DELETE |
| 186 | `DispositionsShouldRemainPreservedAndHistorical` | DELETE |
| 213 | `CandidateShouldContainNoProductionUiChange` | DELETE |

## Complete Python test/helper disposition

### `tests/tooling/check_adoption_hardlink_mutation.py`

Agent evidence mutation/qualification helper; no product runtime assertion.

**DELETE module automation helper**; keep historical proof records unchanged. No test_* method declarations.

### `tests/tooling/check_authority_chain_mutation.py`

Agent evidence mutation/qualification helper; no product runtime assertion.

**DELETE module automation helper**; keep historical proof records unchanged. No test_* method declarations.

### `tests/tooling/test_ad4_acceptance_readiness.py`

BMAD owner-acceptance evidence/protection/candidate-boundary tooling.

| Source line | Function/method | Disposition |
|---:|---|---|
| 122 | `test_absences_pairs_and_committed_bindings` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 141 | `test_fake_complete_accepted_inputs_never_authorize` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 151 | `test_invalid_json_is_fail_with_exact_binding` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 162 | `test_operational_md_is_json_under_the_existing_contract` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 166 | `test_wrong_modes_never_follow_symlinks_or_execute_files` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 173 | `test_record_tamper_and_missing_pair_are_visible` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 184 | `test_structurally_invalid_record_and_duplicate_keys_fail` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 191 | `test_lone_surrogate_record_fails_and_second_pair_is_still_verified` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 200 | `test_internally_consistent_synthetic_pair_still_fails_preserved_hashes` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 216 | `test_changed_gitlink_reports_the_committed_tuple_without_inventing_acceptance` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 226 | `test_gitlink_inventory_and_unsafe_declared_paths_fail` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 232 | `test_unsafe_raw_tree_path_fails_without_reading_its_target` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 236 | `test_shallow_partial_missing_commit_and_missing_blob_block` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 252 | `test_missing_parent_does_not_use_available_tree_as_complete_history` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 257 | `test_bad_cli_and_candidate_object_type_are_json_failures` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 270 | `test_worktree_and_environment_decoys_cannot_change_result` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 284 | `test_candidate_tools_schemas_and_hooks_are_never_executed` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 298 | `test_unexpected_and_environment_failures_have_closed_nonempty_diagnostics` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 310 | `test_host_helper_executes_bound_source_even_with_matching_stale_bytecode` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 332 | `test_host_helper_symlink_components_and_nonregular_leaves_rejected_before_execution` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 358 | `test_ordered_merge_parents_are_observations_only` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 367 | `test_schema_closes_controls_failures_and_ledgers` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 383 | `test_schema_pins_each_preserved_pair_path_and_expected_and_verified_hashes` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |
| 398 | `test_actual_revision_preserves_all_existing_evidence_bytes_and_mtimes` | DELETE: BMAD owner-acceptance evidence/protection/candidate-boundary tooling. |

### `tests/tooling/test_check_root_submodules.py`

Repository Git/index declaration policy; CI checks itself.

| Source line | Function/method | Disposition |
|---:|---|---|
| 19 | `test_current_repository_matches_its_declarations` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 22 | `test_missing_and_unexpected_gitlinks_are_reported` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 48 | `test_regular_file_cannot_stand_in_for_a_gitlink` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 78 | `test_separate_names_cannot_declare_the_same_path` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 91 | `test_repeated_path_setting_is_rejected` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 100 | `test_worktree_cannot_hide_invalid_staged_declarations` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 115 | `test_unstaged_declaration_edits_do_not_change_staged_result` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 122 | `test_staged_declarations_need_no_worktree_copy` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 129 | `test_unstaged_declarations_cannot_replace_missing_index_entry` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 139 | `test_conflicted_index_declarations_are_rejected` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 155 | `test_multistage_declaration_conflict_is_rejected` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 173 | `test_indexed_configuration_without_declarations_has_specific_diagnostic` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 192 | `test_no_declarations_still_reports_undeclared_gitlinks` | DELETE: Repository Git/index declaration policy; CI checks itself. |
| 204 | `test_malformed_indexed_configuration_retains_git_error` | DELETE: Repository Git/index declaration policy; CI checks itself. |

### `tests/tooling/test_epic16_published_artifact_qualification.py`

Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence.

| Source line | Function/method | Disposition |
|---:|---|---|
| 69 | `test_inventory_positive_and_exact_identity_substitutions` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 86 | `test_producer_controls_cannot_be_vacuous` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 101 | `test_configuration_fields_relocate_semantically_and_preserve_input` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 126 | `test_exact_36_control_inventory_rejects_substitutions` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 145 | `test_negative_requires_exact_field_source_and_one_diagnostic` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 161 | `test_adoption_exact_identity_delta_and_owner_disposition` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 181 | `test_output_ownership_rejects_existing_source_and_aliases` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 198 | `test_native_capture_positive_timeout_and_descendant_cleanup` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 217 | `test_stream_limit_and_caller_cancellation_are_bounded` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 232 | `test_archive_hash_substitution_and_expansion_bound` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 243 | `test_unsigned_archive_requires_exact_ci_hash_size_and_payload` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 257 | `test_embedded_catalog_matches_actual_source_props_and_detects_substitution` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 279 | `test_missing_package_preparation_retains_native_failure_and_no_source_credit` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 295 | `test_verdict_preserves_failure_blocker_and_non_vacuity` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 304 | `test_restoration_fault_is_fail_with_a_nonempty_ledger` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 321 | `test_missing_artifact_and_pending_owner_evidence_stay_blocked` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 333 | `test_cli_invalid_roots_and_output_alias_return_nonempty_preflight_ledger` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 356 | `test_available_platform_catalog_disagreement_is_not_hidden_by_missing_release_tag` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 404 | `test_network_worker_positive_transfer_and_archive_byte_cap` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 421 | `test_real_trickle_response_obeys_parent_network_and_remaining_deadlines` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 438 | `test_network_worker_caller_cancellation_reaps_the_owned_worker` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 458 | `test_real_http_truncation_is_incomplete_blocked_with_positive_control` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 476 | `test_native_signature_result_distinguishes_invalid_and_unavailable` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 486 | `test_successful_leader_cleanup_stops_descendant_with_closed_streams` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 502 | `test_zero_size_watched_entries_obey_inner_bounds` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 535 | `test_collect_finalization_checks_captured_inputs_after_interruptions` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 556 | `test_human_negative_rejects_other_diagnostic_families` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 567 | `test_actual_inspector_resource_path_guard_cannot_create_escaped_file` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 580 | `test_collect_failed_prerequisites_execute_no_candidate_commands` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 609 | `test_candidate_version_runs_only_after_complete_independent_prerequisites` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 619 | `test_pending_native_qualification_does_not_bar_byte_verified_diagnostic_controls` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 633 | `test_restore_installs_without_running_the_candidate` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 649 | `test_unsigned_helper_owned_temporary_directory_is_always_removed` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 694 | `test_producer_payload_native_and_declared_evidence_are_independent` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 720 | `test_adoption_caller_retains_failures_and_cannot_accept_matching_failed_reports` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 736 | `test_platform_pair_caller_keeps_mismatch_fail_and_missing_tag_blocked` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 754 | `test_artifact_path_rejects_each_schema_identity_substitution` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 788 | `test_candidate_only_separates_root_pin_and_retains_planning_and_selected_inputs` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 826 | `test_prepared_platform_tuple_and_readme_never_supply_acceptance` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 844 | `test_exact_ci_evidence_carriers_preserve_missing_substituted_and_duplicate_states` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |
| 868 | `test_duplicate_adoption_rows_retain_every_native_row_and_owner_disposition` | DELETE: Tests _bmad/scripts/qualify_epic16_published_artifact.py and retained tool-qualification evidence. |

### `tests/tooling/test_evidence_boundary_adoption.py`

Tests _bmad evidence adoption/skill/render/approval boundaries.

| Source line | Function/method | Disposition |
|---:|---|---|
| 76 | `test_fault_receipt_rejects_unavailable_history_as_fail` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 84 | `test_fault_receipt_retains_original_result_and_verifier_exit` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 93 | `test_fault_receipt_rejects_wrong_verifier_exit` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 106 | `test_fault_receipt_rejects_invalid_original_observation` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 117 | `test_fault_receipt_composed_guidance_uses_unique_ids` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 131 | `test_complete_fault_matrix_integrity` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 163 | `test_complete_fault_matrix_chain` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 213 | `test_fault_receipt_chain_mutation_rejects_unrelated_outcomes` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 224 | `test_complete_fault_matrix_workflow` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 243 | `test_complete_fault_matrix_guidance` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 278 | `test_complete_fault_matrix_readers` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 294 | `test_adoption_output_hardlink_cannot_overwrite_a_source` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 315 | `test_fault_receipt_hardlink_mutation_rejects_unrelated_outcomes` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 326 | `test_approved_assertion_correction_preserves_every_other_entry_byte` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 355 | `test_neutral_helper_portable_surface_stays_closed` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 395 | `test_approved_gitlink_amendment_cannot_redefine_compiled_trust_roots` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 417 | `test_approved_gitlink_amendment_checks_real_raw_git_diffs` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 438 | `test_approved_gitlink_amendment_binding_and_candidate_stay_independent` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 465 | `test_approved_gitlink_amendment_retains_valid_non_applicable_state` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 480 | `test_approved_gitlink_amendment_complete_verifier_preserves_result_schema` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 529 | `test_approved_gitlink_amendment_unavailable_history_stays_blocked` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 548 | `test_approved_gitlink_amendment_output_requires_available_ownership` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 566 | `test_approved_gitlink_amendment_output_requires_evaluated_candidate_tree` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 581 | `test_approved_gitlink_amendment_output_missing_git_preserves_real_tracked_receipt` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 600 | `test_approved_gitlink_amendment_output_can_publish_fail_with_proven_ownership` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 615 | `test_approved_gitlink_amendment_output_checks_resolved_candidate_ownership` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 633 | `test_runbook_acceptance_sequence_matches_effective_contract` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 646 | `test_frozen_authority_chain_requires_the_final_document_boundary` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 661 | `test_frozen_authority_chain_adoption_seam_uses_the_compiled_guard` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 691 | `test_adoption_output_ownership_failure_preserves_receipt` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |
| 711 | `test_adoption_output_git_admin_hardlink_cannot_overwrite` | DELETE: Tests _bmad evidence adoption/skill/render/approval boundaries. |

### `tests/tooling/test_evidence_boundary_current.py`

Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions.

| Source line | Function/method | Disposition |
|---:|---|---|
| 52 | `test_stable_code_contract_registry_is_unique` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 83 | `test_stable_code_contract_bridge_faults` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 117 | `test_stable_code_contract_raw_gitlink_is_never_filtered` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 138 | `test_workflow_tree_and_render_parity` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 151 | `test_not_applicable_is_not_pass` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 158 | `test_not_applicable_is_not_pass_missing_history` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 169 | `test_lifecycle_transition_semantics` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 206 | `test_invocation_removal_and_displacement` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 242 | `test_current_cli_preserves_historical_verify_callable` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 252 | `test_current_missing_workflow_is_gate_failure` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 258 | `test_current_helper_integrity_fault_is_fail` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 271 | `test_stable_code_contract_changed_reader_requires_real_helpers` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 298 | `test_current_cli_output_preserves_helper_failure_json` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 310 | `test_stable_code_contract_output_write_failure_is_schema_valid_blocked` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 327 | `test_lifecycle_transition_semantics_rejects_forged_not_applicable` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 343 | `test_current_binding_inventory_and_source_scope_faults_fail_closed` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 388 | `test_current_reader_only_candidate_is_inspected_before_applicability` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 410 | `test_current_cli_baseline_override_cannot_erase_scope` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 426 | `test_current_historical_provenance_cannot_be_rebound_to_mutated_bytes` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 449 | `test_current_historical_provenance_unavailable_is_blocked` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 478 | `test_current_reader_literal_forms_are_inspected` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 488 | `test_current_shared_reader_construction_and_meaningful_predicate_pass` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 497 | `test_current_reader_assertion_identity_and_predicate_strength` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 514 | `test_current_bridge_preserves_helper_failure_classification` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 529 | `test_current_output_collision_preserves_protected_bytes` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 550 | `test_current_public_cli_dispatch_emits_closed_scoped_failure` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 560 | `test_current_result_schema_failure_keeps_raw_filename_and_blocks_transition` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 570 | `test_stable_code_contract_unavailable_history_cannot_pass` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 577 | `test_current_approved_roots_are_derived_from_verified_baseline` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 583 | `test_current_roots_rebinding_is_rejected_independently` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 606 | `test_current_verifier_carries_canonical_candidate_into_dependent_requests` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 637 | `test_current_public_cli_invalid_filename_is_schema_valid_fail` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 663 | `test_current_existing_reader_blob_failure_is_skipped_and_blocked` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 674 | `test_current_reader_reads_pin_the_first_resolved_head` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 686 | `test_current_runner_reports_registered_invalid_request` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 691 | `test_current_cli_argument_failure_is_closed_blocked` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 700 | `test_current_source_inventory_is_pinned_to_entry_independently_of_diff` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 720 | `test_current_provenance_and_source_inventory_use_independent_approved_commits` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 742 | `test_current_withdrawal_requires_nine_exact_deletions` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 786 | `test_current_refreshed_source_accepts_exact_withdrawal_and_writes_receipt` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 804 | `test_current_withdrawal_output_exception_preserves_other_inputs` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 821 | `test_stable_code_contract_current_ownership_preserves_receipt` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 839 | `test_stable_code_contract_committed_edited_xml_withdrawal_fails` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 852 | `test_stable_code_contract_receipt_is_canonical_utf8_bytes` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |
| 869 | `test_stable_code_contract_current_ownership_unavailable_cannot_write` | DELETE: Tests _bmad evidence transition/skill/render/receipt boundaries, including workflow assertions. |

### `tests/tooling/test_ext_conv_ai_1_installed_delivery_packet.py`

Owner qualification/delivery-packet claims, not actual Conversations code execution.

| Source line | Function/method | Disposition |
|---:|---|---|
| 63 | `test_missing_inputs_stay_null_and_packet_is_not_submitted` | DELETE: Owner qualification/delivery-packet claims, not actual Conversations code execution. |
| 89 | `test_absent_receiver_blocks_separation_claim` | DELETE: Owner qualification/delivery-packet claims, not actual Conversations code execution. |
| 100 | `test_qualification_gate_reserves_nothing` | DELETE: Owner qualification/delivery-packet claims, not actual Conversations code execution. |

### `tests/tooling/test_ext_conv_ai_1_live_runner.py`

Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests.

| Source line | Function/method | Disposition |
|---:|---|---|
| 182 | `test_synthetic_pipeline_covers_authentication_scope_and_all_lanes` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 190 | `test_equivalent_utc_count_serializations_match` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 197 | `test_invalid_window_refuses_before_requests_or_reservation` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 205 | `test_wrong_count_window_cannot_pass_c1` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 211 | `test_unmet_prerequisite_makes_zero_requests_and_consumes_no_attempt` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 220 | `test_repeat_attempt_makes_zero_additional_requests` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 230 | `test_receiver_scope_failure_precedes_membership` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 238 | `test_receiver_bare_response_is_not_a_qualified_sdk_result` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 245 | `test_unqualified_rollover_prevents_retry` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 254 | `test_http_failure_cannot_report_an_available_outcome` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |
| 260 | `test_interruption_retains_pending_operation_and_original_attempt` | DELETE: Synthetic HTTP/process tests of an owner-gated proof runner; real six-seam product behavior remains in Server.Tests and DeletionConformance.Tests. |

### `tests/tooling/test_ext_conv_ai_1_local_runner.py`

Tests agent proof-runner process/mapping forwarding and synthetic result generation; product mapping/runtime tests remain.

| Source line | Function/method | Disposition |
|---:|---|---|
| 91 | `test_complete_mapping_reaches_all_projects_without_selecting_roots_or_versions` | DELETE: Tests agent proof-runner process/mapping forwarding and synthetic result generation; product mapping/runtime tests remain. |
| 105 | `test_each_missing_environment_value_refuses_before_any_child` | DELETE: Tests agent proof-runner process/mapping forwarding and synthetic result generation; product mapping/runtime tests remain. |
| 112 | `test_invalid_mapping_inputs_refuse_before_any_child` | DELETE: Tests agent proof-runner process/mapping forwarding and synthetic result generation; product mapping/runtime tests remain. |
| 120 | `test_evaluated_mapping_mismatch_refuses_before_builds` | DELETE: Tests agent proof-runner process/mapping forwarding and synthetic result generation; product mapping/runtime tests remain. |

### `tests/tooling/test_ext_conv_ai_1_qualification.py`

Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product.

| Source line | Function/method | Disposition |
|---:|---|---|
| 114 | `test_complete_accepted_inputs_pass_without_runtime_effects` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 119 | `test_uncommitted_protection_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 123 | `test_no_owner_accepted_binding_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 127 | `test_unexpected_accepted_file_is_not_ignored` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 131 | `test_changed_cohort_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 135 | `test_unpinned_host_target_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 139 | `test_different_platform_targets_refuse` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 143 | `test_manifest_change_voids_acceptance` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 147 | `test_hash_is_bound_to_the_consumed_manifest_bytes` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 155 | `test_post_body_snapshot_survives_a_later_file_change` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 164 | `test_anchor_change_voids_acceptance` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 168 | `test_missing_anchor_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 172 | `test_configuration_substitution_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 176 | `test_shared_receiver_lookup_identity_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 183 | `test_component_only_host_evidence_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 188 | `test_no_host_pass_path_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 193 | `test_changed_post_body_voids_acceptance` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 197 | `test_missing_or_unexpected_plan_body_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 201 | `test_absolute_file_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 205 | `test_contained_symlink_is_not_an_accepted_file` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 211 | `test_parent_directory_symlink_is_not_containment` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 216 | `test_symlink_above_manifest_root_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 227 | `test_noncanonical_post_cannot_evade_body_inventory` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 235 | `test_copied_manifest_cannot_reserve_another_attempt` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 251 | `test_one_attempt_survives_changed_evidence_destination` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 265 | `test_property_order_cannot_reset_attempt_identity` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 278 | `test_sdk_query_payload_decodes` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 284 | `test_direct_query_payload_remains_supported` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 288 | `test_failed_query_cannot_carry_available_payload` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 293 | `test_nonboolean_query_success_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 297 | `test_invalid_sdk_payloads_refuse` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 304 | `test_ambiguous_query_payload_refuses` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 308 | `test_receiver_requires_the_sdk_encoded_envelope` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |
| 316 | `test_enrolled_provider_assertion_is_reread_after_rotation` | DELETE: Tests owner-accepted input/attempt-journal/evidence qualification helpers; does not execute the built Conversations product. |

### `tests/tooling/test_minimal_module_compatibility_overlay.py`

Keep actual evaluated package/lock/framework/drift assertions; delete the workflow-text method.

| Source line | Function/method | Disposition |
|---:|---|---|
| 34 | `test_actual_overlay_selects_packages_and_external_successor_locks` | KEEP: actual fixture package/lock/framework boundary and negative drift behavior. |
| 72 | `test_compatibility_job_initializes_only_the_direct_catalog` | DELETE: asserts workflow YAML. |
| 86 | `test_reference_framework_discovery_uses_active_framework` | KEEP: actual fixture package/lock/framework boundary and negative drift behavior. |
| 101 | `test_catalog_drift_refuses_before_using_successor_locks` | KEEP: actual fixture package/lock/framework boundary and negative drift behavior. |

### `tests/tooling/test_minimal_module_compatibility_results.py`

Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled.

| Source line | Function/method | Disposition |
|---:|---|---|
| 42 | `test_accepts_complete_passing_suite` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 45 | `test_rejects_missing_registered_test_even_with_green_counters` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 50 | `test_rejects_duplicate_test_replacing_a_required_test` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 55 | `test_rejects_failed_skipped_or_unknown_outcomes_with_green_counters` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 62 | `test_rejects_bad_counters_even_with_passing_results` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 70 | `test_rejects_multiple_assemblies` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 75 | `test_rejects_wrong_document_shape` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |
| 80 | `test_rejects_malformed_and_missing_results` | DELETE: Self-tests the CI test-result XML gate with synthetic XML; real seven-case product execution and strict result verification stay enabled. |

### `tests/tooling/test_release_tooling.py`

Mixed legacy pipeline file: extract listed package/mapping product methods, delete remainder and the original file.

| Source line | Function/method | Disposition |
|---:|---|---|
| 112 | `test_package_output_must_stay_below_repository_root` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 116 | `test_exact_manifest_loads_and_unknown_inventory_is_rejected` | KEEP: exact five-package product inventory and unknown-package rejection. |
| 137 | `test_invalid_archive_boundary_rejects_foreign_assembly` | KEEP: package payload boundary must reject foreign assemblies. |
| 160 | `test_internal_dependencies_follow_candidate_version` | KEEP: internal dependency versions follow the package candidate; external versions remain intact. |
| 173 | `test_symbol_archive_requires_canonical_portable_pdb` | KEEP: canonical product symbol archive identity and Portable PDB format. |
| 181 | `test_frozen_dispatch_skips_without_network` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 199 | `test_stale_dispatch_is_rejected` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 214 | `test_exact_main_and_successful_push_ci_are_required` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 279 | `test_newest_exact_source_ci_attempt_must_succeed` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 321 | `test_partial_publication_is_not_treated_as_absent` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 329 | `test_occupied_release_is_rejected_before_republication` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 336 | `test_publish_boundary_accepts_only_semantic_releases_exact_tag` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 354 | `test_first_release_present_state_accepts_exact_pairs_and_sha` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 374 | `test_publication_rejects_missing_or_corrupt_asset_downloads` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 392 | `test_publication_rejects_different_nuget_package_contents` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 410 | `test_configured_release_plugins_load_without_resolving_npm_publisher` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 477 | `test_semantic_release_planning_in_ci_preserves_repository_refs` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 532 | `test_release_assets_reject_missing_and_unexpected_names` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 559 | `test_nuget_publication_poll_retries_transient_responses` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 583 | `test_public_consumer_execution_failure_is_blocking` | KEEP: a real consumer failure propagates; extraction preserves failure semantics. |
| 603 | `test_local_package_source_is_xml_attribute_escaped` | KEEP: isolated package-consumer feed paths retain their exact safe XML value. |
| 613 | `test_publication_preflight_routes_verify_and_publish_phases` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 650 | `test_unmapped_build_refuses_every_ambient_configuration` | KEEP: real product MSBuild source-mapping refusal; adapt only the approved generic preparation integration, never invent producer identity. |
| 675 | `test_pack_inherits_producer_mapping_without_overriding_selection` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 690 | `test_standalone_consumers_remove_parent_mapping_imports` | KEEP: isolated package consumers cannot inherit the producer mapping/configuration. |
| 709 | `test_workflows_pin_bypass_and_freeze_contract` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 744 | `test_release_solution_and_projects_exclude_external_release_source_edges` | KEEP: actual product solution/package graph remains independent of sibling source edges; preserve equivalent evaluated checks for the new adapter. |
| 760 | `test_windows_checkout_excludes_only_historical_http_cache` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |
| 783 | `test_ci_and_security_automation_cover_release_boundary` | DELETE: legacy pipeline/tooling/publisher-state or workflow-text self-check; shared runtime owns the replacement. |

## Exact portable compile links

### `tests/Hexalith.Conversations.Conformance.Portable.Tests/Hexalith.Conversations.Conformance.Portable.Tests.csproj`

| Operation | Source | Action |
|---|---|---|
| Include | `../Hexalith.Conversations.Conformance.Tests/ConformanceTierAssemblyInventory.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseEvidenceArtifactCollection.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/AdopterConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/AdopterConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ArchitecturePlanningAuthorityValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/AtRiskTestRegisterGenerationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/BuyerAcceptanceConformanceFixtures.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/BuyerAcceptanceConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/BuyerAcceptanceConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ClassificationChangeProcedureValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ConformanceManifestValidationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ConformanceOracleTieringValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ConformanceTieringIlReferenceReader.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ConsumePromoteKeepInventoryValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ContractValidationConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ContractValidationConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/CoreFixtureContentSafetyTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/EventSchemaEvolutionConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/EventSchemaEvolutionConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/FinalConformanceContractDiffEvidenceValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/GovernanceAuditPairingSafetyNetConformanceTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/IdempotencyConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/IdempotencyConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/NoInModuleSharedFakeDuplicateConformanceTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/OqTwoTargetInterpretationDecisionValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/OracleBlindSpotAnalysisArtifactGenerationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PackageEnvironmentAuthorityV18ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PlanningAuthorityV8ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PlanningAuthorityV9ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PlanningToolingEnvironmentAuthorityV15ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PlanningToolingLifecycleAuthorityV16ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PlatformEvidenceSeparationConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PlatformEvidenceSeparationConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PreservationTraceabilityManifestValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ProjectionReadStorePopulationProofValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ProviderPortabilityConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ProviderPortabilityConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/PublicContractShapeSnapshotGenerationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/RedactionConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/RedactionConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseBaselineValidationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseConformanceArtifactBuilder.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseConformanceArtifactGenerationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseScopeConformanceFixtures.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseScopeConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseScopeConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/ReleaseWaiverValidationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/RemovedTestJustificationLedgerReconciliationValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/RepositoryEvidencePathResolver.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/SecondAdopterConformanceFixtures.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/SecondAdopterConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/SecondAdopterConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/SmC2BaselineReconstructionValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/StoryFinalRecordGenerationValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/SuccessMetricReportAndAttestationValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Include | `../Hexalith.Conversations.Conformance.Tests/TenantIsolationConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/TenantIsolationConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Include | `../Hexalith.Conversations.Conformance.Tests/UxPreservationDispositionValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |

### `tests/Hexalith.Conversations.Conformance.Tests/Hexalith.Conversations.Conformance.Tests.csproj`

| Operation | Source | Action |
|---|---|---|
| Include | `../Hexalith.Conversations.Conformance.Portable.Tests/Story92TieringVerification.cs` | Remove main-tier link; retain neutral product-only helper in portable tier. |
| Remove | `AdopterConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `AdopterConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ArchitecturePlanningAuthorityValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `AtRiskTestRegisterGenerationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `BuyerAcceptanceConformanceFixtures.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `BuyerAcceptanceConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `BuyerAcceptanceConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ClassificationChangeProcedureValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `ConformanceManifestValidationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ConformanceOracleTieringValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `ConformanceTieringIlReferenceReader.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `ConsumePromoteKeepInventoryValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `ContractValidationConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ContractValidationConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `CoreFixtureContentSafetyTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `EventSchemaEvolutionConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `EventSchemaEvolutionConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `FinalConformanceContractDiffEvidenceValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `GovernanceAuditPairingSafetyNetConformanceTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `IdempotencyConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `IdempotencyConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `NoInModuleSharedFakeDuplicateConformanceTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `OqTwoTargetInterpretationDecisionValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `OracleBlindSpotAnalysisArtifactGenerationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `PackageEnvironmentAuthorityV18ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `PlanningAuthorityV8ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `PlanningAuthorityV9ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `PlanningToolingEnvironmentAuthorityV15ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `PlanningToolingLifecycleAuthorityV16ValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `PlatformEvidenceSeparationConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `PlatformEvidenceSeparationConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `PreservationTraceabilityManifestValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `ProjectionReadStorePopulationProofValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `ProviderPortabilityConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ProviderPortabilityConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `PublicContractShapeSnapshotGenerationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `RedactionConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `RedactionConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseBaselineValidationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseConformanceArtifactBuilder.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseConformanceArtifactGenerationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseScopeConformanceFixtures.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseScopeConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseScopeConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `ReleaseWaiverValidationTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `RemovedTestJustificationLedgerReconciliationValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `RepositoryEvidencePathResolver.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `SecondAdopterConformanceFixtures.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `SecondAdopterConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `SecondAdopterConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `SmC2BaselineReconstructionValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `StoryFinalRecordGenerationValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `SuccessMetricReportAndAttestationValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |
| Remove | `TenantIsolationConformanceSuite.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `TenantIsolationConformanceSuiteTest.cs` | Keep product compilation partition; apply mixed-method extraction above where named. |
| Remove | `UxPreservationDispositionValidationTest.cs` | Remove this stale compilation entry when source is deleted/extracted. |

## Inventory totals

- DELETE: 171
- EXTRACT: 5
- KEEP: 303
- helper DELETE: 3
- helper EXTRACT: 1
- helper KEEP: 22
- python DELETE: 236
- python KEEP: 12

This inventory enumerates every C# source and Python test/helper file under the two conformance project directories and tests/tooling at the stated source, including each declared Fact/Theory and test_* method. It is a planning classification, not evidence that any revised suite, adapter, hook, archive checkout or shared preparation has passed.
