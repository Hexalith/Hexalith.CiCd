# Local preparation dispositions

This is an implementation inventory, not adoption or push acceptance. No spec
execution checkbox is complete. Product preparation remains uncommitted. The
first focused logs predate later product-cohort and test changes; immutable
`runs/` records identify the exact subsequent diff and new-file bytes.

| Removed or narrowed surface | Disposition and retained product coverage |
| --- | --- |
| `CiGitHistoryPreparationTests`, `GitlinkGateWorkflowTests`, their Python cases, `prepare-ci-git-history.sh`, `gitlink-rc-gate.sh` | Retired CI source-history/gitlink-controller gates. No product test was supplied by these files. Root gitlink declarations and historical signoff records remain unchanged. |
| `AssistantCommitMessageInstructionsTests`, `GeneratedBuildsCheckoutTests` | Retired assistant-policy and generated CI checkout tests. Agent instructions and effective commitlint policy remain unchanged. |
| `ReleaseSourcePreflightTests`, `ReleaseRegistryFloorTests`, `ReleasePublicationVerificationTests` | Retired tests that extract source admission, tag-floor and run/tag lookup shell from legacy workflow YAML. `ReleaseArtifactVerificationTests` retains the package/archive/OCI byte, source identity, created-time and propagation/transport controls. `scripts/verify-release-publication.py` and its archive cases remain. |
| `AccessibilityWorkflowTests` | Removed workflow shape, step order and artifact-upload assertions. `BrowserProductTests` retains the complete accessibility/portal/picker script inventory, nonoptional browser scenarios and prebuilt UI Test fixture. The real `tests/e2e` manifest, lock, configuration and all specs are unchanged. |
| `PartiesContainerPublishWorkflowTests` | Removed reusable-workflow pins, release job/environment wiring, workflow ownership, docs and tool-only npm assertions. `ContainerProductTests` retains browser lock/engine checks, ICU image requirements, test concurrency configuration, OCI validator compatibility, strict created/calendar labels and exact eleven-package inventory. New source/version adapter controls reject conflicting identities. `PackagePublicationProductTests` retains exact package/image argument forwarding and package-count refusal from the legacy publisher boundary. |
| `tests/ci-lifecycle/*.py`, `qualify-disposable-ci.py`, `observe-current-owner-startup.py` | Retired CI campaign/controller/startup observer orchestration and their mocked job/process controls. The actual `.Platform.IntegrationTests`, `.Platform.LifecycleTests`, `.Platform.AttachedLifecycleTests`, `AspireMtlsBootstrapTests`, `AspireMtlsCleanupFailureTests`, native image observations, authentication, state persistence and cleanup tests remain. Their real hosted/runtime execution is still pending. |
| `EpicEightClosureFitnessTests`, `G8OwnerDeliveryReceiptTests`, `MatrixRow`, `ClosureDeferral` | Retired story status, closure evidence, deferred-work bookkeeping and historical owner-delivery receipt gates. These did not perform fresh domain runtime qualification. Historical records remain. |
| `PlatformApiPrerequisitesTests` | Removed story matrices, dated Git identities, scope policing and receipt checks. Extracted executable runtime inventory, package/source boundary, explicit source mapping, MSBuild property/version and malformed-graph checks into `ExternalRuntimeGraphTests` and its `EvaluatedProjectGraph` value type. |
| `RetainedCatalogViewTests` | Removed the obsolete shared-producer 40-name cohort and unknown-project default gates. The retained product check evaluates every actual project with package mode, asserts the qualified 5.1.1 default and preserves explicit 4.2.0 selection. Existing caller-catalog/default/family precedence tests remain unchanged; the product default now defers to alternate caller catalogs. |
| `RetiredLeafProjectFitnessTests` | Removed only the story-matrix status requirement. Retained absent retired projects, actual host dependency/wiring checks, and the authentication project/solution assertion. |
| Five live Memories/backfill classes in `Hexalith.Parties.Tests` | Compile only in the new `Hexalith.Parties.Runtime.IntegrationTests` assembly. Their namespaces, opt-in requirements, workload methods and deterministic teardown cases remain. The topology wrapper and preparation select that child; shared non-test helpers are linked without duplicating recovery tests. The dependency subprocess selects the actual executing assembly name. `RuntimeTestRoutingTests` reads real compiled metadata to prove the boundary. |
| `verify-current-owner-integration.py`, `verify-public-package-integration.py` and their mixed receipt tests | Replaced by `runtime_observation_contract.py`, `public_runtime_observation_contract.py` and three product regression modules. Removed old CI invocation/execution/per-attempt cleanup layouts, fixed job/source admission, old Builds schema/gitlink gates and historical 28-name workflow inventory. Retained bounded no-link readers, duplicate JSON refusal, native case/interval binding, issued tenant and full persisted identities/sequences/timestamps, authentication/persistence cases, source/body/SDK/package/image role provenance and verified empty inventories of every cleanup resource role. Context and native output roots are explicit caller inputs. Historical measured SDK 4.2/public image bytes remain exact compatibility expectations; they grant no new runtime acceptance. |
| Completed-build reuse gate | Production preparation now requires a bounded, structurally exact completion marker bound to its matching positive start timestamp, selected configuration and an ordered nonfuture completion. `test_runtime_build_reuse.py` exercises the real Bash entry point across 17 missing/malformed/mismatched/linked-marker subcases; a `dotnet` sentinel proves refusal precedes any SDK call, and stale prepared manifests are removed. Actual positive reuse is separately exercised after the full solution build. |
| Root `package.json` and `package-lock.json` | Retired tool-only commitlint/semantic-release manifests. Effective `commitlint.config.mjs`, legacy publisher scripts/configuration and browser tooling remain. Legacy credential grants have not been revoked. |
| Active CI/release docs | Replaced obsolete module-owned CI update/manual release instructions with pending central-adoption requirements. Prior descriptions are preserved verbatim in `docs/ci-legacy-reference.md` and `docs/legacy-release-checklist.md`. |

Both owner-gate dispositions are explicit: “Finalize exact CI owner” was already
absent at the baseline; “Require the owning integration job to pass” belongs to
legacy `ci.yml` and is removed by eventual CiCd delivery. Preparation does not
edit that owned workflow. Its following native product verification must be
routed through an enabled hook before adoption.

The first standalone build exposed the catalog's finite retained Parties SDK4.2
view: all three native project names selected EventStore 4.2.0 by default, and the
attached suite failed on nine missing descriptor members. Current product
selection now explicitly requests EventStore 5.1.1 before importing the catalog,
while explicit compatibility/mapped-source selections retain authority. This
requires product-suite and historical-cohort qualification, not only compilation.

The package-mode runtime artifact graph and published Aspire tools are now
declared. Solution builds bind the native Admin UI through ProjectReference;
metadata-only runtime preparation and the catalog driver accept `--reuse-build`.
The complete standalone build, all thirteen prebuilt preparation records and the
declared Aspire asset check pass in `runs/20261116T185507Z-ecd36aa4/`. The derived
`runtime-graph-verdict.json` proves exactly the eight declared external projects
compiled, all in Release, with no ordinary source library added. Legacy
direct qualification paths remain distinct. The proposed Tenants source gitlink
advances locally from `2ec938397c5b330cf1e694e8cc442cb4ad022f2b` to CiCd's already
selected `292dbf164f26bcf376ef86d749b149b075f8b502`: the old owner guard refuses
SDK 5.1.1, while the latter contains its owner-qualified support. No nested
checkout, remote ref or publishing grant was changed.

Outstanding work: activate complete suite/cohort routing and finish retained-suite/native/browser execution and OCI archive verification. The package-mode native hooks are blocked on the actual
shared runner's build-reuse interface, recorded in
`../../../../implementation-artifacts/prerequisite-21-native-build-reuse.md`.
Hook execution cannot substitute an unissued descriptor, change to source mode,
or rebuild the native test/model closure.

Owner-emission verification has an independently measured package boundary gap:
`owner-emission-boundary.json` evaluates the exact pinned EventStore AppHost,
Aspire helper and executable with package mode plus the published-host selector.
AppHost still references the packable Aspire source project; that project still
references Contracts/Client/ServiceDefaults source, and the executable references
Gateway source. The executable/composition exception is not capped at eight
projects. Its ordinary libraries must nevertheless stay packaged. A supported
owner package-routing/prebuilt composition interface is still required; no
ordinary source build or weakened manifest check was used to claim emission.

Outstanding dependent work: released generic frozen-created support and selected
Builds pin; maintainer prerequisites and migration-order acceptance; verified
remote product revision, registration/render, App adoption, scoped cleanup,
normal local checker, green hosted shared CI and scheduled-night acceptance.


Final accepted local results are recorded in `accepted-local-verification.json`:
421 complete retained Ci.Tests pass serially, and 2,800 complete environment-free
general tests pass after the two Memories documentation rows are corrected.
Runtime child identity (10) and relocated deterministic cleanup controls (22)
also pass. `verification-history.json` preserves failed and canceled scopes;
the final source-state proof matches the final unit-run snapshot. The two doc
rows are the only tracked difference from the complete solution/Ci.Tests input;
compiled sources, untracked hashes/modes and dependency pins are identical.
There is no new native/browser/OCI/hosted/adoption/nightly qualification claim.
