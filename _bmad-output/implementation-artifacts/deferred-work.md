# Deferred work

- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Carry story 1's submodule answer into the spine and the CI stories. AD-12 l.323 "Only the Builds submodule is checked out" becomes "Builds plus the `submodules` knob". Spine Deferred l.713/715 close, and stories 2-3/2-4 state that the knob exists and that `ci.yml` checks it out.
  evidence: Story 1 found 8 package-mode builds that read sibling submodules (`pipeline-stages.md`), and SPEC.md:162 now says so. The follow-up is recorded only in the `.memlog.md` event, because story 1 may not edit the adopted spine. A `ci.yml` built to AD-12 as written would check out only Builds, and those 8 modules would fail CI (review BH-6, BH-7, EC-4).
- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Resolve the AD-20 versus AD-7 conflict. AD-20 has CiCd agents close Dependabot PRs on frozen files, but AD-7's CiCd-agent token has no Pull requests write. The `module-inventory.md` `dependabot.yml` row restates AD-20.
  evidence: Story 1 created the token to AD-7 (Actions, Contents and Workflows write only) and named the conflict as a spine follow-up in the memlog. A close attempt with that token would fail with 403 (review BH-4, EC-7).
- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Codify the `registry.hexalith.com` Zot configuration (namespace `registry-distribution`: htpasswd Secret, config ConfigMap, Deployment) in a source outside the cluster.
  evidence: No kustomize source exists. Platform story 2-8 found the same (`externalKustomizeSourceLocated: false`). Both `ci-reader` (2-8) and `hexalith-registry-pull` (story 1) exist only as live objects, and their `last-applied-configuration` annotations are stale. Re-applying any older manifest would drop both principals and break CI and Dependabot pulls (review BH-15).
- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Agent sessions in this repo still inherit the maintainer's cluster-admin `kubectl` context (`jpiquot@local`) and SSH keys. `GH_CONFIG_DIR` isolates only `gh`, and git over HTTPS to github.com.
  evidence: Story 1's own Zot change ran through that `kubectl` context from an agent session. AD-7 limits only the `gh` credential, so under the careless-agent model an agent here can still change production cluster objects (review BH-16).
- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Prune the legacy-secret reader lists by liveness, for example the public `_OLD` repos holding `NUGET_API_KEY` or `SONAR_TOKEN`, and the `semantic-kernel` fork holding `AZURE_SUBSCRIPTION_ID` and `AZURE_TENANT_ID`.
  evidence: Step 8 restricted each secret to the repos whose default-branch workflows name it, which narrowed access from `all`. It didn't check whether those readers still run, so dead or third-party repos keep access (review BH-17).
- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Memories' `Hexalith.Memories.Web.csproj:10` and `Hexalith.Memories.Web.Tests.csproj:7` build FrontComposer from source whenever `references/Hexalith.FrontComposer` is populated, even with `UseHexalithProjectReferences=false`. So a local check (story 6) with populated references diverges from CI package mode.
  evidence: The default is `Exists(...)` and doesn't check `UseHexalithProjectReferences`, unlike `Directory.Build.props:50`. CI is unaffected, because the `Hexalith.FrontComposer.*` packages are on nuget.org (4.7.6) and CI checks out no FrontComposer (review EC-3).

### DW-1: Existing Module tests intermittently fail temporary Git-workspace and manifest validation in local runs.
origin: spec-deferred 82da96cbdca1
location: test/Hexalith.Builds.Module.Tests/AttachAdmissionTests.cs:1859
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: medium
reason: Before the review patch, the full shared unit run passed 2915 Module tests with 3 existing skips. A later final run failed 98/2918 tests with Git metadata/manifest fixture errors. AttachAdmissionTests reproduced failures both with the new stop-on-fail override (12/133) and without it (92/133); individual failing tests passed and 100 fresh reflection validation probes passed. Product files are unchanged; precise test-isolation cause remains unresolved.
status: open

### DW-2: Builds' own CI no longer runs Hexalith.Builds.Tooling.IntegrationTests until stage 4 executes integration projects.
origin: spec-deferred b8b8df1d842a
location: .github/workflows/builds-ci.yml dotnet job; test/Hexalith.Builds.Tooling.IntegrationTests
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
reason: The replaced inline dotnet job ran the project explicitly. AD-13 now classifies it as integration (hosted run 42622137434 lists it under "integration"), and this story's intent forbids stage 4 execution. Its only ungated test, ToolAssembliesHaveIndependentEntryPoints, is unrun meanwhile; live tests skip without LiveGate. Story 2-5 implements integration execution and should confirm this project runs there.
status: open

### DW-3: The reusable CI job's fixed 30-minute budget may be too short for larger consumers, with no per-project hang protection.
origin: spec-deferred 0b604b83db2d
location: .github/workflows/ci.yml:28
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: medium
reason: Builds' own hosted build/unit job took about 17 minutes. Whether EventStore, Parties or other large modules exceed 30 minutes for stages 2-3 is unknown; a hung test would consume the budget without a dump. Settle by measuring stage 2-3 durations when those modules adopt the shared CI. (declared severity: medium (unverified))
status: open

### DW-4: ChatBot's test projects cannot run under the VSTest runner its global.json implies once it adopts the shared CI on SDK 10.
origin: spec-deferred 77ba729371b3
location: references/Hexalith.ChatBot/global.json
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
reason: ChatBot's global.json (SDK 10.0.403) selects no test runner, so the shared pipeline uses positional VSTest as AD-13 requires. Its 14 test projects reference plain xunit.v3 (Builds catalog 4.0.3), xunit.runner.visualstudio and Microsoft.NET.Test.Sdk. A reviewer reproduced that setup: `dotnet test --no-build` fails with "Testing with VSTest target is no longer supported by Microsoft.Testing.Platform on .NET 10 SDK". This is preexisting module configuration, and ChatBot's own CI already fails. At adoption, select Microsoft.Testing.Platform in global.json or use xunit.v3.mtp-off.
status: open

### DW-5: Builds releases also stop exercising Hexalith.Builds.Tooling.IntegrationTests until stage 4 runs integration projects.
origin: spec-deferred 6b2e087c4a3b
location: .github/workflows/builds-release.yml; Tools/G4PackageQualification.functions.ps1
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
reason: builds-release.yml passes HEXALITH_G4_SOURCE_CI_RUN_ID. Get-VerifiedSourceCiRun (Tools/G4PackageQualification.functions.ps1) accepts the exact-SHA push run of builds-ci.yml as the source-test evidence. Since this story, that run classifies Tooling.IntegrationTests as integration and does not execute it. This is the same root cause as the deferred Builds CI coverage item. Story 2-5 should confirm the project runs in stage 4 for both CI and release evidence.
status: open

### DW-6: Cross-repository resolution of $/ in the reusable ci.yml has not been exercised by any hosted run.
origin: spec-deferred 04af84c349a0
location: .github/workflows/ci.yml:54
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: medium
reason: The hosted probe (run 42615634829) and Builds' own calls are same-repository, so the caller and workflow commits coincide. Whether a module's cross-repository workflow_call resolves $/Github/ci-* to Hexalith.Builds at job.workflow_sha is documented but unverified. If it does not, every consumer's CI fails at preparation. Settle with the first module's hosted call of Hexalith/Hexalith.Builds/.github/workflows/ci.yml; if it fails, apply AD-9's pinned own-code checkout. (declared severity: medium (unverified))
status: open

### DW-7: Shared Linux restore/build passes a config-accepted leading-dash solution path to dotnet as a switch.
origin: spec-deferred f53d0a644380
location: references/Hexalith.Builds/Github/lib/ci_pipeline.py:282
source_spec: `2-6-sample-module-self-test-and-the-windows-job.md`
severity: low
reason: ci_config.validate_config path() accepts a solution such as "-consumer.slnx", and ci_pipeline.restore_and_build passes prepared.document["solution"] unchanged to "dotnet restore"/"dotnet build". dotnet parses it as a switch and fails with MSB1001; the recovery pass reproduced this failure on the Windows path. The function predates story 2-6 and is unchanged by it, and shared CI calls it before any Linux prepare, so prepare exposes no new path. The smallest fix is passing str(prepared.root / solution), as the Windows prepare script now does.
status: open

### DW-8: Retire or narrow the story 3-1 spike publishing credentials that remain live after the spike: the nuget.org policy `Hexalith.Builds CiCd`, the Zot principal `cicd-publish-spike-3-1`, and the spike
origin: spec-deferred d1a742edfcfa
location: nuget.org Trusted Publishing policy `Hexalith.Builds CiCd`; Hexalith/Hexalith.Builds environment `hexalith-release`; Zot principal `cicd-publish-spike-3-1`
source_spec: `3-1-spike-oci-containers-and-nuget-login-in-the-publish-composite.md`
severity: medium
reason: The temporary workflow and action were removed in Builds 82eebdbff0074f62abe5a6b9a14a6ae9bd62b469, but the confirmed nuget.org policy is still active (owner Hexalith, workflow publish-spike.yml, environment hexalith-release, glob *, push new packages/versions plus unlist/relist). Any future publish-spike.yml merged to Builds main could therefore push any Hexalith-owned package. That contradicts spine line 220: after adoption, a repository's only Trusted Publishing policy is for release.yml, scoped to its package-ID prefix (Builds from its rewrite, AD-19). Builds hexalith-release also stores the spike-only Zot pair under the production secret names, while enforcement.md expects the module's own push identity there. The intent required preserving these configured inputs, and removing them needs maintainer nuget.org, GitHub and Zot administration, so this follow-up review records the work rather than performing it.
status: open

### DW-9: Verify Kotlin coverage with the pinned CodeQL no-build analyzer before adopting java-kotlin in a managed module.
origin: spec-deferred fb8938c5c76e
location: references/Hexalith.Builds/.github/workflows/release.yml:94
source_spec: `3-2-release-gate-jobs-and-the-outcome.md`
severity: medium
reason: Current GitHub documentation says no-build java-kotlin analyzes Java and omits Kotlin with a warning. The review did not execute a mixed Kotlin/Java fixture with pinned v4.39.3, so that pinned behavior remains unverified. A pinned mixed-language analysis and an architecture decision on the mandated no-build policy would settle it; current hosted evidence covers csharp only. Primary reference: https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/manage-your-configuration/codeql-for-compiled-languages (declared severity: medium (unverified))
status: open

### DW-10: Confirm the release alert gate cannot miss a release-category alert whose most recent instance on main moves to a non-release analysis.
origin: spec-deferred cb3b97a24b26
location: references/Hexalith.Builds/Github/lib/release_security.py:64
source_spec: `3-2-release-gate-jobs-and-the-outcome.md`
severity: medium
reason: The gate implements AD-18's predicate exactly: open high/critical alerts whose most_recent_instance carries a hexalith-release/ category. An alert shared with another analysis configuration on main (for example the frozen codeql.yml default /language:<lang> category) could carry that other category, and pass unblocked, if that analysis finishes processing between this run's SARIF processing and the alert read. Whether GitHub orders most_recent_instance by processing time across categories was not verified. The scoped agent token cannot read code scanning (HTTP 403), and no concurrent two-category experiment ran. A controlled two-category experiment on main, or authoritative GitHub documentation, would settle it. A fix would judge the release-category instance from /code-scanning/alerts/{number}/instances and needs an AD-18 predicate decision. (declared severity: medium (unverified))
status: open

### DW-11: Module-owned NuGet audit waivers (Directory.Build.targets NoWarn and PackageReference NoWarn metadata) let NU1903 pass the create-mode release build.
origin: spec-deferred b5fffd2156c7
location: references/Hexalith.Builds/Github/release-build/release.targets:5-8
source_spec: `3-3-create-mode-version-audited-build-marked-draft.md`
severity: high
reason: Real SDK 10.0.403 reproduction through release_build.build_release with the release flags and Newtonsoft.Json 9.0.1 (GHSA-5crp-9r3c-p9vr): `<NoWarn>$(NoWarn);NU1903</NoWarn>` in a module Directory.Build.targets, or `<PackageReference Include="Newtonsoft.Json" NoWarn="NU1903" />`, builds and packs with no "blocked by a vulnerable package" diagnostic. release.targets is imported through CustomAfterMicrosoftCommonTargets, before Directory.Build.targets, and rewrites only the NoWarn/WarningsNotAsErrors properties, not item metadata. Inherited Builds props exemptions (Hexalith.Build.props WarningsNotAsErrors NU1903;NU1904) and props-level module NoWarn are still blocked, for single-target and multi-target projects with TreatWarningsAsErrors true or unset. SPEC.md:120, enforcement.md and AD-8 assign rejection of module-file audit waivers (NoWarn under any parent or attribute, NuGetAuditSuppress, MSBuildWarningsAsMessages) to the guard audit lint, story 5-2 "Guard lints and commitlint", which
status: open

### DW-12: Repair the incoming upstream routing-snapshot descriptor fixture and its four failing cases.
origin: spec-deferred 1be219f5eebc
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/SelectedRoutingCatalogSnapshotTests.cs:289
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Upstream merge e588605ccf2c6577a2490e1a3fc512f8ffdc3960 introduced required ownerRunId/runId/role fields while SelectedRoutingCatalogSnapshotTests.CreateDescriptor still emits only environmentId. Reviewer executed the focused class: 34 tests, 4 failures, exit 2; negative controls also short-circuit. These C# changes were already on origin/main before resumed publisher changes.
status: open

### DW-13: Strengthen the upstream malformed explicit-port CLI tests so missing manifest errors cannot satisfy them.
origin: spec-deferred 633fd01f9c74
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/StartupReadinessTests.cs:37
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: StartupReadinessTests uses --manifest unused and asserts only UsageOrManifest, the same exit code returned when manifest resolution fails. A valid manifest plus parse diagnostic and no-start observation would distinguish the intended refusal. This test was introduced by the preserved upstream merge, outside this story's changes.
status: open

### DW-14: Complete and retain focused .NET verification for the incoming endpoint and attached-routing changes.
origin: spec-deferred 9b8d2c86e776
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/SelectedRoutingCatalogSnapshot.cs:83
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Story 3-4's required Python/workflow/API checks do not execute the unrelated incoming C# changes. A reviewer ran the routing-snapshot class and found four failures; the upstream changes need their own focused verification and repair rather than silently attributing Python success to them.
status: open

### DW-15: Add independent attached-routing identity refusal cases for attached run, environment, role and hold bindings.
origin: spec-deferred b0bd6a702108
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/NativeTestExecutorTests.cs:762
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: The incoming NativeTestExecutorTests attached-routing test varies ownerRunId only while SelectedRoutingCatalogSnapshot validates several independent identity fields. Exact owner/environment/role/hold substitutions would establish refusal for each newly introduced boundary.
status: open

### DW-16: Verify attached candidate-policy refusal independently of TestObservation.
origin: spec-deferred 1499f0465ace
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/NativeTestExecutor.cs:400
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Incoming NativeTestExecutor code refuses attachments when CandidatePolicy is populated, but no test supplies CandidatePolicy with absent TestObservation. Existing access-observation refusal does not isolate that branch.
status: open

### DW-17: Preserve the requested explicit endpoint in unmanaged occupied-port diagnostics.
origin: spec-deferred fc4e7db0f6d6
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionPortAllocator.cs:184
source_spec: `3-4-the-publish-composite.md`
severity: low
reason: Incoming AllocateOwned throws SocketException for an unmanaged occupied explicit port and CompositionEngine maps this to generic HXR020 text without the requested endpoint. The request remains available to the caller, so this is a diagnostic usability issue.
status: open

### DW-18: Move the upstream explicit-endpoint README section out of License and update the stale attached-routing and claim-retry text.
origin: spec-deferred f697010b556c
location: references/Hexalith.Builds/README.md:1399
source_spec: `3-4-the-publish-composite.md`
severity: low
reason: Upstream commit bfda07ee appends "### Explicit endpoints and attached routing snapshots" (README.md:1399) after "## License" (README.md:1394), so it renders as a License subsection. README.md:641-643 still says owners requiring routing-catalog observations fail attached runs as startup-failure. README.md:752-754 still says every claim conflict retries up to 64 times, with no exception for explicit ports. Not changed by publisher work.
status: open

### DW-19: Test and explain the upstream refusal of explicit EventStore ports on attached suites.
origin: spec-deferred b3ca79539e5e
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Module.Cli/ModuleCommandApplication.cs:450
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: ModuleCommandApplication refuses --attach-to combined with --eventstore-port through generic HXC001 "The command line is invalid." ModuleCommandExecutionService:119-122 throws for Down, runId or out-of-range ports. Searching test/ for eventstore-port/EventStorePort finds only StartupReadinessTests, none with --attach-to, and the guard message appears in no test. Removing either guard fails no test, although the README promises "Attachments cannot request owner ports". Arrived with upstream merge e588605c.
status: open

### DW-20: Make the explicit-port exclusion from independent allocation observable in a test.
origin: spec-deferred fc5d41ad69ba
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionPortAllocator.cs:174
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: CompositionPortAllocator adds the requested port to the excluded set before Allocate, then overwrites EventStoreHttp. The existing distinctness test requests a port already handed out in-process, which _handedOut skips anyway. The other tests take OS-ephemeral ports outside the Linux candidate range. Deleting excluded.Add(requested) fails no test, even though an in-range request (such as the README's 18080) could then be given to a second endpoint. A deterministic test likely needs an injectable candidate source. Upstream change.
status: open

### DW-21: Remove the ephemeral-port reuse race from the upstream explicit-port tests.
origin: spec-deferred 873dc1ab4adc
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/StartupReadinessTests.cs:66
source_spec: `3-4-the-publish-composite.md`
severity: low
reason: StartupReadinessTests:66-69 binds an OS-assigned loopback port, stops the listener and then requests that port for the owner. CompositionResourceClaimStoreTests:67 reallocates the same way. Any parallel test or outbound connection can take the released port in between, which makes failures intermittent. Upstream test code.
status: open

### DW-22: Confirm whether attached children can rewrite the owner's routing-catalog proofs that later attachments capture.
origin: spec-deferred d10c03683eda
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/NativeTestExecutor.cs:400
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Upstream removed the attached refusal for owners requiring routing-catalog observations (NativeTestExecutor.cs:400 now refuses only on TestObservation/CandidatePolicy/hold mismatch). Unverified: settle it by checking whether attached children get write access to the owner's platform-components/<env>-catalog proofs, and whether SelectedRoutingCatalogSnapshot re-verifies those bytes against the owner capture after each attached child exits. (declared severity: medium (unverified))
status: open

### DW-23: Qualify out-of-band release mutation after final authenticated GET and before DELETE.
origin: spec-deferred 18e5300409ca
location: references/Hexalith.Builds/Github/lib/release_complete.py:192
source_spec: `3-5-complete-mode-reruns-finish-from-the-original-artifact.md`
severity: medium
reason: The required immediate live revalidation and standard release concurrency are implemented. Actual GitHub behavior for an external editor/publisher in this remaining interval was not destructively qualified because retained story 3-4 resources must remain untouched. Settle with an authorized disposable two-actor experiment and a supported serialization or atomicity decision. Potential medium impact is unverified. (declared severity: medium (unverified))
status: open

- source_spec: `_bmad-output/specs/spec-cicd/stories/3-6-rewrite-builds-release-yml-onto-the-shared-release.md`
  summary: Add focused normally executed product verification of the real packaged CLI child-AppHost extension closure without restoring retired G-4 qualification execution.
  evidence: Review BH-4/VG-1 confirms upstream 12472357225b78ae3a2647a832504261cc078266 added current-catalog assembly retention, while its real loader assertion is reached only through the intentionally dormant legacy builder. Package unit fixtures use dummy binaries and the installed-package live lane is opt-in. A controlled missing-extension package should fail an ordinary product test. Severity medium; no actual broken package was demonstrated.
- source_spec: `_bmad-output/specs/spec-cicd/stories/3-6-rewrite-builds-release-yml-onto-the-shared-release.md`
  summary: Bound upstream consumer evaluator execution, stream draining and output storage, including cleanup of owned processes.
  evidence: Review BH-6/BH-7/EC-1 verifies Tools/validate-consumer-package-authority.ps1 Invoke-JsonEvaluation uses parameterless WaitForExit, unbounded ReadToEndAsync/GetResult and complete diagnostic output. A hung or noisy evaluator can exhaust the catalog lane's deadline or memory. This is independent upstream validator behavior; add process/drain deadlines, bounded stdout/diagnostic tails and behavioral failure fixtures. Severity medium.
- source_spec: `_bmad-output/specs/spec-cicd/stories/3-6-rewrite-builds-release-yml-onto-the-shared-release.md`
  summary: Ensure upstream central-catalog evaluator cleanup terminates owned descendants even after the direct evaluator process exits.
  evidence: Review BH-8/EC-2 verifies ProcessRunner in Tools/validate-central-package-versions.ps1 throws on its five-second stream-drain deadline but its finally guard skips Kill(true) when HasExited is true. Reproduce with an exited evaluator whose descendant retains redirected streams, then track and clean up that owned group independently. Introduced by upstream 00681381c5c81069623478fd75f8650333542d82; severity medium.
- source_spec: `_bmad-output/specs/spec-cicd/stories/3-6-rewrite-builds-release-yml-onto-the-shared-release.md`
  summary: Diagnose the intermittent native descendant cleanup observation rather than treating a successful retry as proof of reliability.
  evidence: Review BH-10: hosted push run 43174705780 attempt 1, job 131036024414, failed ReviewDetachedNativeDescendantsAreVerifiedAsync(discoveryVerified: True) at NativeTestExecutorTests.cs:64 because StopObserved was false. Retry, focused 2/2 and full-class 62/62 passed without a code change. The sanitized failure excerpt is retained in Builds evidence/cicd-3-6/cleanup-first-attempt.log; causal attribution remains unverified, potential severity medium.

- source_spec: `_bmad-output/specs/spec-cicd/stories/4-1-perimeter-contract-and-library-in-builds.md`
  summary: Verify and document the minimum Git capability required for snapshot-pinned perimeter attributes (medium, unverified).
  evidence: Resumed review RB9 notes that old Git versions may ignore GIT_ATTR_SOURCE; no older binary was available to reproduce its exact behavior. Current hosted/local Git passes selected-index and dirty-worktree attribute controls. Settle this with a cross-version real-Git repair demonstrating whether an unsupported attribute source can affect hashing, then document or enforce the proven minimum without weakening index atomicity.

### DW-24: On create-mode drift, release resolve still emits CodeQL and nightly-hook settings parsed from the drifted dispatch-SHA configuration, so the owned edit can steer the release security jobs.
origin: spec-deferred 5638b7c7b782
location: references/Hexalith.Builds/Github/lib/release_state.py resolve (dispatch_settings emission before require_clean); references/Hexalith.Builds/.github/workflows/release.yml codeql/nightly-hook if
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Follow-up review BH1/IA-D1. release_state.resolve emits dispatch_settings(git, sha, ...) after the completed comparison but before Comparison.require_clean() raises. release.yml gates codeql and nightly-hook only on !cancelled() && config-valid == 'true' (plus codeql != '[]' / nightly-hook == 'true'), not on the resolve result. So an owned edit setting "codeql": [] skips release CodeQL, and adding "nightly" to hooks starts nightly-hook, which runs $/Github/prepare with the registry pull secrets and then ./.github/actions/nightly. test_module_create_matches_accepted_state_and_blocks_drift_before_false_switch asserts codeql == ["ruby"] from the drifted file. This is pre-existing: the baseline emitted dispatch settings unconditionally, before any check. The story's AC and Design Notes explicitly keep these settings available to the existing security jobs, and no publication handoff occurs. Settling it needs a design decision: emit the accepted (expected) configuration's settings on drift,
status: open

### DW-25: Release resolve configuration diagnostics still name a random, already-deleted temporary path instead of the committed logical configuration path.
origin: spec-deferred bcf2d39cf4a1
location: references/Hexalith.Builds/Github/lib/release_state.py dispatch_settings
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: low
reason: Follow-up review BH3/VG3. release_state.dispatch_settings materializes the dispatch blob into tempfile.TemporaryDirectory(prefix="hexalith-release-config-") and passes it to load_config. Two calls on an invalid configuration printed /tmp/hexalith-release-config-e4hcdqgv/hexalith-ci.json: ... and then /tmp/hexalith-release-config-m4ev6d9i/hexalith-ci.json: .... The guard's expected_state.load_ci maps loader errors to the committed path. dispatch_settings already has this behavior at implementation baseline f01c3ab70f7e7401b3b73217983955f7771a1465, and this story did not change it. Fix: apply the same str(error).replace(str(path), relative) mapping, and assert the logical path and repeat stability in test_release_adapters.
status: open

### DW-26: Builds main stays red on two baseline failures with no follow-up owner: the package-catalog validator's 14 EventStore 4.2.0-versus-5.0.0 assertions (exit 1) and the 44 failing Evidence.Tests
origin: spec-deferred 25bd20338ca7
location: references/Hexalith.Builds package catalog contracts job; test/Hexalith.Builds.Evidence.Tests
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Follow-up review BH14. Both failures reproduce on integration revision 05a75b626fb73c6e386d16c41e885f193d3cff16 (run 43387068103), before this story's source. They come from upstream dependency/catalog changes: Props/Directory.Packages.props moved HexalithEventStoreVersion to 5.0.0 while the catalog assertions still require 4.2.0. The story-5-1 verification exception tolerates them for story verification only. The deferred-work ledger has no entry for either failure. While they persist, Builds' own release green-CI gate cannot pass. Settle by reconciling the catalog validator with the EventStore 5.0.0 pin, and by triaging the 44 Evidence.Tests failures in their owning upstream change.
status: open

### DW-27: Exact-name catalog snapshots accept case-varied consumer names.
origin: spec-deferred a3d95c73af72
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Workspace/CatalogVersionMaterializer.cs:175; Runtime/CompositionDeclarationOptions.cs:183
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review EC1/BH2: MSBuildProjectName.Equals selectors are case-sensitive, but CatalogVersionMaterializer stores project views with OrdinalIgnoreCase and CompositionDeclarationOptions.ReadRecordedPackageVersion uses OrdinalIgnoreCase. A clean Hexalith.Parties.Tests view selects SDK4.2/OpenAPI2; hexalith.Parties.Tests selects SDK5/OpenAPI3 but can reuse the recorded retained view. Both paths were traced and disposable MSBuild evaluations confirmed the selection difference. This is present in upstream integration cae351e20093634483afad16aca3bfd90845eda8, before the story follow-up commit; fix exact-name materialization/lookup and add a case-varied consumer test in the catalog workstream.
status: open

### DW-28: The no-snapshot catalog package reader selects conditional EventStore4.2 instead of the default SDK5 view.
origin: spec-deferred db73a849f2fd
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionDeclarationOptions.cs:147
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review BH1: CompositionDeclarationOptions.ReadCatalogPackageVersion resolves $(HexalithEventStoreVersion) using the first XML descendant without evaluating its condition. The integrated catalog now declares the retained conditional 4.2.0 before the default 5.0.0, while the first OpenAPI declarations remain 11.0.0/3.11.0. This yields a crossed default tuple through the public no-snapshot overload. The implementation and declaration order are present unchanged in integration cae351e20093634483afad16aca3bfd90845eda8; this story changes neither file. Use an evaluated default view or require the materialized snapshot in that owning catalog change.
status: open

### DW-29: The Python catalog selector reader omits the new Equals-based consumer views from runtime inventory.
origin: spec-deferred 499534893948
location: references/Hexalith.Builds/Tools/evaluated_catalog.py:96; Tools/runtime_toolchain_v2.py:186
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review BH3: Tools/evaluated_catalog.py.conditioned_catalog_project_names recognizes quoted == expressions only. Tools/runtime_toolchain_v2.py.inventory evaluates a consumer-specific catalog only when the project stem is in that returned set. The integrated MSBuildProjectName.Equals selectors are therefore omitted and affected projects receive the default SDK5 inventory. The C# selector reader was updated upstream but this Python reader was not; both the new selectors and this omission already exist in integration cae351e20093634483afad16aca3bfd90845eda8. Extend the Python selector extraction and behavioral inventory tests in that catalog workstream.
status: open

### DW-30: Current toolchain defaults and some tests remain coupled to newly frozen v1 runtime pins.
origin: spec-deferred 4a73d8a5fd2b
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionToolchainPins.cs:34; test/Hexalith.Builds.Module.Tests/SupportedPlatformPinsCatalogTests.cs:29
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: low
reason: Review BH4/BH9: SupportedPlatformPins now returns immutable v1 literals, but CompositionToolchainPins.DaprRuntimeVersion still delegates to that facade and CompositionPrerequisiteProbe uses it for its documented catalog default. SupportedPlatformPinsCatalogTests also retains current-versus-frozen equality for FrontComposer and Dapr. Values currently agree, so no current hosted failure exists; a future approved current-catalog update would leave the default probe on the frozen runtime and reject the otherwise independent catalog update in tests. This authority split was introduced by the preserved upstream frozen-pin work and is present at integration cae351e20093634483afad16aca3bfd90845eda8. Reconcile the intended current/frozen facade and test authorities in that workstream.
status: open

### DW-31: Active retained compatibility package selections have no current conditional-selection audit records.
origin: spec-deferred a5740c625d89
location: references/Hexalith.Builds/Tools/package-version-audit.json; Props/Directory.Packages.props
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review BH5: The current package audit rows bind EventStore.Gateway5.0.0, ASP.NET OpenAPI11.0.0, OpenAPI3.11.0 and OpenIdConnect11.0.0. The active named views select 4.2.0, 10.0.15, 2.13.0 and 10.0.15, respectively, but any old observations are labeled historical and do not bind the current conditional selections. This leaves current listing/retention provenance incomplete for those consumers. The audit and selectors are unchanged from upstream integration cae351e20093634483afad16aca3bfd90845eda8; extend current view-bound audit evidence in the owning package-audit workstream.
status: open

### DW-32: Automatic response-file isolation lacks a real consumer-authority regression test.
origin: spec-deferred ac138a90e03b
location: references/Hexalith.Builds/Tools/validate-central-package-versions.ps1:218; Tools/test-consumer-package-authority-validator.ps1
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review VG1, pre-verified: Removing only -noAutoResponse from validate-central-package-versions.ps1 still passed all 23 central-validator scenarios. A disposable ancestor Directory.Build.rsp setting FixtureVersion=9.9.9 under TMPDIR made both actual and expected consumer evaluations use 9.9.9 and validation exit successfully after that mutation; current code correctly rejects 9.9.9 instead of 1.2.3. The consumer-authority suite covers local XML overrides but not this response-file path. The isolation fix and test gap already exist in upstream integration cae351e20093634483afad16aca3bfd90845eda8 and are outside this story-authored patch. Add the demonstrated real-process poisoned-response-file case to the owning consumer-authority suite.
status: open

- source_spec: `_bmad-output/specs/spec-cicd/stories/5-2-guard-lints-and-commitlint.md`
  summary: Repair the pre-existing package-catalog and .NET contract failures introduced by the independent Builds catalog update before closing story 5.2's all-jobs qualification gate.
  evidence: Upstream Builds 4c1bf138368968cb4565a3aaef894353ffcf6038 failed normal CI run 43506256176 before these review corrections. Package catalog job 132164596242 fails Test authoritative package catalog with EventStore family/SDK owner-tuple mismatches; .NET job 132164596764 fails Stage 3 unit tests with stale catalog version expectations (expected 4.2.0, actual 5.0.1). Both Python lanes, workflow/API checks, sample and Windows pass at that upstream source. Story 5.2 explicitly excludes SDK/catalog pins outside the guard tool package; correcting that independent update needs separate scope authorization.

- source_spec: `_bmad-output/specs/spec-cicd/stories/5-2-guard-lints-and-commitlint.md`
  summary: RESOLVED — the upstream catalog/.NET qualification blocker recorded for story 5.2 is closed.
  evidence: The user explicitly authorized the catalog repair. Existing production pins were preserved; current/historical consumer contracts and the two-family audit snapshot were synchronized, and the historical closure fixture now selects the retained producer view while current Platform selection still refuses older release authority. Final Builds source 2dc16bba3053c1efc871a221a4e782a8c3da72ab passed all seven jobs in normal exact-source run 43519435001, including both 892-test Python lanes, all catalog checks, full .NET, sample and Windows. This resolution supersedes the earlier open blocker entry without rewriting its historical evidence.

- source_spec: `_bmad-output/specs/spec-cicd/stories/7-delivery-the-single-write-path-into-modules.md`
  summary: Confirm whether GitHub's Dependabot security-updates endpoint returns HTTP 200 `{"enabled": false}` for a compliant module; if it does, `app_checks` must accept that body as well as 404 (unverified; high if true).
  evidence: Review-1 E4. The docs say 200 means enabled and 404 means not enabled, but the 200 schema carries an `enabled` boolean. `tools/deliver.py:77-78` treats any 200 as enabled, which would block every module from advancing. The CiCd-agent token gets 403 on this endpoint, so the live shape is unverified. Settle it by reading `GET /repos/Hexalith/<module>/automated-security-fixes` with an Administration-read token on a repository with Dependabot alerts on and security updates off.

- source_spec: `_bmad-output/specs/spec-cicd/stories/7-delivery-the-single-write-path-into-modules.md`
  summary: Measure whether per-slot Builds re-acquisition and partial-clone lazy fetches keep a full 17-module delivery inside the 36-minute soft deadline (unverified; medium if true).
  evidence: Review-1 E13. A real anonymous `Transport.builds("v5.1.0")` took 26–27 s from the dev host: 57 blobs, each lazily fetched. `trusted_state` runs it once per attempt, plus a preflight for each eligible module, so 17 modules take an estimated 15–20 min, not shown to exceed 36 min. Settle it by timing the first hosted multi-module run. If it is too slow, cache the verified acquisition per tag or fetch the tag without `blob:none`.
