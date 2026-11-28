---
title: '31-1 Shared native build reuse in Builds.Module.Cli'
type: 'feature'
created: '2026-11-27'
status: 'in-progress'
route: 'dispatch'
baseline_commit: 'b6842869c8d034e39313a63528ad77cfc96839c2'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Package-mode native runs compile the selected test project and Platform model in private workspaces. Add an opt-in CLI handoff that reuses the original audited Release outputs across native profiles, including the composition dependencies needed to run without compilation or restore.

## Boundaries & Constraints

Keep the shared contract module-agnostic and additive. Preserve existing source and package behavior when the handoff is omitted. Bind reuse to the same prepared checkout, declared source and package boundary, and an independently supplied producer receipt digest. Keep credentials and run state private to the current execution. Include a bounded local Platform companion for the prepared composition path. Story 21 resumes after a compatible release is selected through CiCd's normal process.

| Scenario | Input | Expected behavior |
| --- | --- | --- |
| Reuse | Audited Release outputs matching the current selection | Launch verified bytes from private run paths. Batch entries and admitted attachments use the owner's verified inventory. |
| Refusal | Missing, stale, foreign, incomplete or modified input, including an attachment override | Fail through the production CLI before launching the affected executable. Never fall back to compilation. Preserve normal failure reporting and cleanup. |

</frozen-after-approval>

## Code Map

- Builds `ModuleCommandApplication.cs` and `Workspace/{BuildPreparationService,ManagedBuildPreparationService}.cs` parse commands and resolve the catalog. `Github/lib/ci_pipeline.py::restore_and_build` precedes hooks in the same CI workspace. The regular build flags alone do not establish an audited producer.
- Builds `Runtime/{ModuleCommandExecutionService,CompositionEngine,CompositionRunPlan,AttachedSuiteSupervisor}.cs` carry owner and attached execution. `NativeTestExecutor.ExecuteSelectedAsync` handles launch, handoff, supervision and reports. `PlatformManifestCommand.BuildModelAsync` compiles against the pinned catalog and executing Tooling assembly.
- Platform `src/Hexalith.Platform.Composition/{PlatformAppModel,PlatformRoutingCatalog,PlatformCurrentOwnerProof}.cs` launches owners, builds the reader and prepares current-owner proof. The Parties pin `a670a4c51d76f63f3142e38f02542a246e1926fb` still compiles on this path. The prebuilt owner switch serves Development/source.
- Parties `module/hexalith.module-manifest.v2.json` declares `platform-package`, `lifecycle-package`, `attached-lifecycle-package` and the separate `platform-source` profile. `Hexalith.Parties.Standalone.slnx` builds the native tests. The Platform model requires explicit preparation.

## Tasks & Acceptance

- [x] Builds `src/libraries/Hexalith.Builds.Tooling/Workspace/` and `Github/lib/ci_pipeline.py` — prepare and seal outputs once before hooks. Bind source commit/tree and executable gitlinks, manifest and project identities, resolved package versions and content hashes, SDK/TFM/RID, Release configuration, Platform model/catalog identity, and Tooling bytes. Inventory the full runnable output, including dependency and configuration files.
- [x] Builds `src/libraries/Hexalith.Builds.Module.Cli/ModuleCommandApplication.cs` and `src/libraries/Hexalith.Builds.Tooling/Runtime/` — validate the receipt and exact file inventory at the production boundary. Reject escaped or linked paths and copy verified bytes into private run paths. Launch the selected prebuilt MTP or VSTest entry through the existing executor, with per-run TRX. Carry the validated selection through attachment admission.
- [ ] Builds `src/hosts/Hexalith.Builds.Module.AppHost/RunTopology.cs` and Platform `src/Hexalith.Platform.Composition/` — route the verified model, catalog reader, owner proof and runtime owners. Preserve catalog trust and ordinary package references. Validate a compliant prebuilt EventStore owner closure. Treat any additional upstream package-routing change or publication as its own prerequisite.
- [ ] Builds `test/Hexalith.Builds.Module.Tests/` — extend CLI, native executor, model and attachment tests. Exercise mismatch, absent/changed files, valid reports, authentication, cancellation, expiry and cleanup through production entry points.
- [ ] CiCd `_bmad-output/specs/spec-cicd/evidence/21/` — record exact source, package and output identities and qualification results. Qualify the published CLI through the central Builds release process before selecting its tag.

**Acceptance Criteria**

- Given one audited Release preparation, when all three declared Parties package profiles run with EventStore 5.6.0 and Tenants 8.1.1, then process traces show no compiler or restore invocations and the runs retain authenticated endpoints, persisted-state checks, native TRX and verified cleanup. Exercise cancellation and attachment expiry. Run the existing source profile as a separate compatibility check.
- Given any mismatched source, cohort, framework, configuration, model, or artifact byte, when reuse is requested, then a nonzero verdict identifies the mismatch without exposing credentials or attempting a fallback build.
- Given an immutable bot-published Builds release from green main, when its NuGet tool and tag pass qualification and CiCd pin validation, then select it and resume the approved story 21 sequence.

## Implementation Notes

- The user approved the spec on 2026-11-27. Implement locally in the isolated worktrees at `/home/administrator/projects/hexalith/cicd-31-1/builds` and `/home/administrator/projects/hexalith/cicd-31-1/platform`. Their baselines are `a0c8b64ec1a9492220a4caa5487574296263f8e1` and `e51cf194ac1caac65feb233c8c42491a7895518f`. Use the owning repository guidance and the Hexalith baseline in the CiCd workspace's `references/Hexalith.AI.Tools/`. Use `run-with-temp` for build and qualification jobs. The implementation step permits local work. Publication follows the authorized release process after qualification.
- The local Builds and Platform implementation and targeted verification are retained in those worktrees. The acceptance audit connected CI to the default-disabled `nativeBuildReuse` setup field. The packaged candidate passed the live source profile and cleanup on repeat. The pinned Parties Platform commit lacks the prepared runtime entry point, and Platform checks the exact committed gitlinks and release source. The three live package profiles and release selection remain open. See the [qualification record](../specs/spec-cicd/evidence/21/native-build-reuse-31-1.md).

## Spec Change Log

## Review Triage Log

## Verification

- Use `run-with-temp` for the Builds regression suite and the Parties build from `8daf30af7e413278f03f1ea744477e976a78fe16`. Verify the package cohort from actual restore assets and runtime dependencies. Trace the child process tree and record digests and outcomes.
- Builds main inspected at `a0c8b64ec1a9492220a4caa5487574296263f8e1` includes attached bearer fixes. Published `v6.9.1` at `91cb7cba990ffdf82930f9bf8cb68aef41baba76` still builds on execution.
