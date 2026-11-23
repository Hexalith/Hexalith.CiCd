# Deferred work

- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Carry story 1's submodule answer into the spine and the CI stories. AD-12 l.323 "Only the Builds submodule is checked out" becomes "Builds plus the `submodules` knob". Spine Deferred l.713/715 close, and stories 2-3/2-4 state that the knob exists and that `ci.yml` checks it out.
  evidence: Story 1 found 8 package-mode builds that read sibling submodules (`pipeline-stages.md`), and SPEC.md:162 now says so. The follow-up is recorded only in the `.memlog.md` event, because story 1 may not edit the adopted spine. A `ci.yml` built to AD-12 as written would check out only Builds, and those 8 modules would fail CI (review BH-6, BH-7, EC-4).
  status: done 2026-11-23
  resolution: AD-12 and the story 2-3/2-4 handoff now specify the direct gitlink list used by shared CI and Windows preparation. Both story 1 probes have recorded outcomes in the spine. Five checkout and workflow-output tests passed against Builds v6.6.2.
- source_spec: `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`
  summary: Resolve the AD-20 versus AD-7 conflict. AD-20 has CiCd agents close Dependabot PRs on frozen files, but AD-7's CiCd-agent token has no Pull requests write. The `module-inventory.md` `dependabot.yml` row restates AD-20.
  evidence: Story 1 created the token to AD-7 (Actions, Contents and Workflows write only) and named the conflict as a spine follow-up in the memlog. A close attempt with that token would fail with 403 (review BH-4, EC-7).
  status: done 2026-11-23
  resolution: AD-20 and the Builds inventory assign reporting to the CiCd agent and closure without merge to a Builds maintainer. The frozen-path exclusions and AD-7 token grants still apply.
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

status: done 2026-11-23
origin: spec-deferred b8b8df1d842a
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
archived: 2026-11-23

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

status: done 2026-11-23
origin: spec-deferred 6b2e087c4a3b
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: low
archived: 2026-11-23

### DW-6: Cross-repository resolution of $/ in the reusable ci.yml has not been exercised by any hosted run.

status: done 2026-11-23
origin: spec-deferred 04af84c349a0
source_spec: `2-4-fail-fast-ci-build-and-unit-tests.md`
severity: medium
archived: 2026-11-23

### DW-7: Shared Linux restore/build passes a config-accepted leading-dash solution path to dotnet as a switch.
origin: spec-deferred f53d0a644380
location: references/Hexalith.Builds/Github/lib/ci_pipeline.py:282
source_spec: `2-6-sample-module-self-test-and-the-windows-job.md`
severity: low
reason: ci_config.validate_config path() accepts a solution such as "-consumer.slnx", and ci_pipeline.restore_and_build passes prepared.document["solution"] unchanged to "dotnet restore"/"dotnet build". dotnet parses it as a switch and fails with MSB1001; the recovery pass reproduced this failure on the Windows path. The function predates story 2-6 and is unchanged by it, and shared CI calls it before any Linux prepare, so prepare exposes no new path. The smallest fix is passing str(prepared.root / solution), as the Windows prepare script now does.
status: done 2026-11-23
resolution: Shared Linux CI resolves the module-contained solution before passing it to SDK restore and build. A real .NET 11.0.100 fixture confirms the raw leading-dash path fails and the shared entry point builds it. [Verification](spec-deferred-builds-invocation-and-attachment.md)

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
status: done 2026-11-23
resolution: Story 5-2 shipped Stage 1 audit lint in Builds v6.6.2. At that tag, all 19 audit-lint tests passed and two real Git-tree probes independently rejected the exact NU1903 waivers in Directory.Build.targets and PackageReference metadata. The release resolver source requires successful CI on the exact proposed source for create-mode publication. [Verification](spec-deferred-release-verification.md)

### DW-12: Repair the incoming upstream routing-snapshot descriptor fixture and its four failing cases.
origin: spec-deferred 1be219f5eebc
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/SelectedRoutingCatalogSnapshotTests.cs:289
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Upstream merge e588605ccf2c6577a2490e1a3fc512f8ffdc3960 introduced required ownerRunId/runId/role fields while SelectedRoutingCatalogSnapshotTests.CreateDescriptor still emits only environmentId. Reviewer executed the focused class: 34 tests, 4 failures, exit 2; negative controls also short-circuit. These C# changes were already on origin/main before resumed publisher changes.
status: done 2026-11-23
resolution: Builds `b74b467ac5ce5d9f9fc440f43e279b7093b539de` binds all three fields in the fixture. The corrected test blob `f07fa2cab376672b3d02c82867f6dd092b47f1ee` is in current Builds main, the pinned v6.6.2 tag and the source whose hosted .NET unit job passed. [Hosted job](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43519435001/job/132209687921)

### DW-13: Strengthen the upstream malformed explicit-port CLI tests so missing manifest errors cannot satisfy them.
origin: spec-deferred 633fd01f9c74
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/StartupReadinessTests.cs:37
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: StartupReadinessTests uses --manifest unused and asserts only UsageOrManifest, the same exit code returned when manifest resolution fails. A valid manifest plus parse diagnostic and no-start observation would distinguish the intended refusal. This test was introduced by the preserved upstream merge, outside this story's changes.
status: done 2026-11-23
resolution: The CLI regression uses a declared verification suite and checks HXC001 plus the absence of a startup workspace and state.

### DW-14: Complete and retain focused .NET verification for the incoming endpoint and attached-routing changes.
origin: spec-deferred 9b8d2c86e776
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/SelectedRoutingCatalogSnapshot.cs:83
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Story 3-4's required Python/workflow/API checks do not execute the unrelated incoming C# changes. A reviewer ran the routing-snapshot class and found four failures; the upstream changes need their own focused verification and repair rather than silently attributing Python success to them.
status: done 2026-11-23
resolution: Builds `b74b467ac5ce5d9f9fc440f43e279b7093b539de` repaired the routing-snapshot descriptor fixture. Exact-source hosted Stage 3 at `2dc16bba3053c1efc871a221a4e782a8c3da72ab` ran the unfiltered Linux Module.Tests assembly containing StartupReadinessTests, NativeTestExecutorTests and SelectedRoutingCatalogSnapshotTests. It passed 3,094 tests with zero failures and four named skips in other classes. The corresponding source identities and log digest are retained in the verification spec. [Hosted job](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43519435001/job/132209687921) · [Verification](spec-deferred-release-verification.md)

### DW-15: Add independent attached-routing identity refusal cases for attached run, environment, role and hold bindings.
origin: spec-deferred b0bd6a702108
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/NativeTestExecutorTests.cs:762
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: The incoming NativeTestExecutorTests attached-routing test varies ownerRunId only while SelectedRoutingCatalogSnapshot validates several independent identity fields. Exact owner/environment/role/hold substitutions would establish refusal for each newly introduced boundary.
status: done 2026-11-23
resolution: The attached-routing theory now substitutes the descriptor environment independently of the hold environment. It checks the identity diagnostic for every invalid run, environment, role and hold case. Both valid captures still verify the exact retained bytes. [Verification](spec-deferred-builds-invocation-and-attachment.md)

### DW-16: Verify attached candidate-policy refusal independently of TestObservation.
origin: spec-deferred 1499f0465ace
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/NativeTestExecutor.cs:400
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: Incoming NativeTestExecutor code refuses attachments when CandidatePolicy is populated, but no test supplies CandidatePolicy with absent TestObservation. Existing access-observation refusal does not isolate that branch.
status: done 2026-11-23
resolution: Builds `565b9e63bce9d3b5b43483d01da81ef7ceb33a20` adds an attachment with a valid hold, an owner candidate policy and no access observation. The test checks HXT009 and confirms the child and attachment workspace are never created. [Verification](spec-deferred-builds-invocation-and-attachment.md)

### DW-17: Preserve the requested explicit endpoint in unmanaged occupied-port diagnostics.
origin: spec-deferred fc4e7db0f6d6
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionPortAllocator.cs:184
source_spec: `3-4-the-publish-composite.md`
severity: low
reason: Incoming AllocateOwned throws SocketException for an unmanaged occupied explicit port and CompositionEngine maps this to generic HXR020 text without the requested endpoint. The request remains available to the caller, so this is a diagnostic usability issue.
status: done 2026-11-23
resolution: HXR020 names the requested loopback endpoint when its pre-launch bind probe fails. The regression verifies that teardown removes the workspace and releases the claims.

### DW-18: Move the upstream explicit-endpoint README section out of License and update the stale attached-routing and claim-retry text.
origin: spec-deferred f697010b556c
location: references/Hexalith.Builds/README.md:1399
source_spec: `3-4-the-publish-composite.md`
severity: low
reason: Upstream commit bfda07ee appends "### Explicit endpoints and attached routing snapshots" (README.md:1399) after "## License" (README.md:1394), so it renders as a License subsection. README.md:641-643 still says owners requiring routing-catalog observations fail attached runs as startup-failure. README.md:752-754 still says every claim conflict retries up to 64 times, with no exception for explicit ports. Not changed by publisher work.
status: done 2026-11-23
resolution: Builds `565b9e63bce9d3b5b43483d01da81ef7ceb33a20` moves explicit endpoints into the runtime documentation and describes attached routing snapshots and the one-attempt explicit claim. The guidance is present on current Builds main. [Verification](spec-deferred-builds-invocation-and-attachment.md)

### DW-19: Test and explain the upstream refusal of explicit EventStore ports on attached suites.
origin: spec-deferred b3ca79539e5e
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Module.Cli/ModuleCommandApplication.cs:450
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: ModuleCommandApplication refuses --attach-to combined with --eventstore-port through generic HXC001 "The command line is invalid." ModuleCommandExecutionService:119-122 throws for Down, runId or out-of-range ports. Searching test/ for eventstore-port/EventStorePort finds only StartupReadinessTests, none with --attach-to, and the guard message appears in no test. Removing either guard fails no test, although the README promises "Attachments cannot request owner ports". Arrived with upstream merge e588605c.
status: done 2026-11-23
resolution: HXC001 names both incompatible flags. The live-owner test verifies that the request creates no attachment or child. The direct service guard is covered separately.

### DW-20: Make the explicit-port exclusion from independent allocation observable in a test.
origin: spec-deferred fc5d41ad69ba
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionPortAllocator.cs:174
source_spec: `3-4-the-publish-composite.md`
severity: medium
reason: CompositionPortAllocator adds the requested port to the excluded set before Allocate, then overwrites EventStoreHttp. The existing distinctness test requests a port already handed out in-process, which _handedOut skips anyway. The other tests take OS-ephemeral ports outside the Linux candidate range. Deleting excluded.Add(requested) fails no test, even though an in-range request (such as the README's 18080) could then be given to a second endpoint. A deterministic test likely needs an injectable candidate source. Upstream change.
status: done 2026-11-23
resolution: The regression observes the explicit port in the exclusion set passed to the independent allocator and verifies it occurs once in the claimed result.

### DW-21: Remove the ephemeral-port reuse race from the upstream explicit-port tests.
origin: spec-deferred 873dc1ab4adc
location: references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/StartupReadinessTests.cs:66
source_spec: `3-4-the-publish-composite.md`
severity: low
reason: StartupReadinessTests:66-69 binds an OS-assigned loopback port, stops the listener and then requests that port for the owner. CompositionResourceClaimStoreTests:67 reallocates the same way. Any parallel test or outbound connection can take the released port in between, which makes failures intermittent. Upstream test code.
status: done 2026-11-23
resolution: The successful CLI fixture selects a port from the normal allocator. The occupied-port fixtures keep their listeners bound through refusal and verify claim rollback.

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
  status: done 2026-11-23
  resolution: The pinned Builds repair test used the dirty worktree filter on Git 2.40.4 and passed with snapshot attributes on Git 2.41.0. The maintainer quickstart documents the minimum. [Verification](spec-deferred-cicd-qualification.md)

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
status: done 2026-11-23
resolution: Release resolve names the committed configuration path for validation and JSON syntax failures. Composite tests verify repeat stability, a sample module path and refusal before configuration outputs are emitted. [Verification](spec-deferred-builds-invocation-and-attachment.md)

### DW-26: Builds main stays red on two baseline failures with no follow-up owner: the package-catalog validator's 14 EventStore 4.2.0-versus-5.0.0 assertions (exit 1) and the 44 failing Evidence.Tests
origin: spec-deferred 25bd20338ca7
location: references/Hexalith.Builds package catalog contracts job; test/Hexalith.Builds.Evidence.Tests
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Follow-up review BH14. Both failures reproduce on integration revision 05a75b626fb73c6e386d16c41e885f193d3cff16 (run 43387068103), before this story's source. They come from upstream dependency/catalog changes: Props/Directory.Packages.props moved HexalithEventStoreVersion to 5.0.0 while the catalog assertions still require 4.2.0. The story-5-1 verification exception tolerates them for story verification only. The deferred-work ledger has no entry for either failure. While they persist, Builds' own release green-CI gate cannot pass. Settle by reconciling the catalog validator with the EventStore 5.0.0 pin, and by triaging the 44 Evidence.Tests failures in their owning upstream change.
status: done 2026-11-23
resolution: The story 5-1 follow-up at Builds `185e3a4e695f392e114eacffbdecd2a23da32c9b` passed catalog validation and all 191 Evidence.Tests without the historical exception. The later exact-source run 43519435001 independently passed both lanes. [Catalog job](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467144/job/131936449710) · [.NET job](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467144/job/131936450342)

### DW-27: Exact-name catalog snapshots accept case-varied consumer names.
origin: spec-deferred a3d95c73af72
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Workspace/CatalogVersionMaterializer.cs:175; Runtime/CompositionDeclarationOptions.cs:183
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review EC1/BH2: MSBuildProjectName.Equals selectors are case-sensitive, but CatalogVersionMaterializer stores project views with OrdinalIgnoreCase and CompositionDeclarationOptions.ReadRecordedPackageVersion uses OrdinalIgnoreCase. A clean Hexalith.Parties.Tests view selects SDK4.2/OpenAPI2; hexalith.Parties.Tests selects SDK5/OpenAPI3 but can reuse the recorded retained view. Both paths were traced and disposable MSBuild evaluations confirmed the selection difference. This is present in upstream integration cae351e20093634483afad16aca3bfd90845eda8, before the story follow-up commit; fix exact-name materialization/lookup and add a case-varied consumer test in the catalog workstream.
status: done 2026-11-23
resolution: Builds records exact project names in materialized and on-demand views and resolves them by exact name. A real MSBuild regression keeps three case variants distinct through materialization, composition lookup and validation. Package IDs remain case-insensitive. [Verification](spec-deferred-catalog-authority.md)

### DW-28: The no-snapshot catalog package reader selects conditional EventStore4.2 instead of the default SDK5 view.
origin: spec-deferred db73a849f2fd
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionDeclarationOptions.cs:147
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review BH1: CompositionDeclarationOptions.ReadCatalogPackageVersion resolves $(HexalithEventStoreVersion) using the first XML descendant without evaluating its condition. The integrated catalog now declares the retained conditional 4.2.0 before the default 5.0.0, while the first OpenAPI declarations remain 11.0.0/3.11.0. This yields a crossed default tuple through the public no-snapshot overload. The implementation and declaration order are present unchanged in integration cae351e20093634483afad16aca3bfd90845eda8; this story changes neither file. Use an evaluated default view or require the materialized snapshot in that owning catalog change.
status: done 2026-11-23
resolution: Builds selects default properties in source order, skipping consumer-conditioned assignments. The existing regression cases verify the no-snapshot owner and package lookup against MSBuild's default view. Conditional package inclusion is tracked separately. [Verification](spec-deferred-catalog-authority.md)

### DW-29: The Python catalog selector reader omits the new Equals-based consumer views from runtime inventory.
origin: spec-deferred 499534893948
location: references/Hexalith.Builds/Tools/evaluated_catalog.py:96; Tools/runtime_toolchain_v2.py:186
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review BH3: Tools/evaluated_catalog.py.conditioned_catalog_project_names recognizes quoted == expressions only. Tools/runtime_toolchain_v2.py.inventory evaluates a consumer-specific catalog only when the project stem is in that returned set. The integrated MSBuildProjectName.Equals selectors are therefore omitted and affected projects receive the default SDK5 inventory. The C# selector reader was updated upstream but this Python reader was not; both the new selectors and this omission already exist in integration cae351e20093634483afad16aca3bfd90845eda8. Extend the Python selector extraction and behavioral inventory tests in that catalog workstream.
status: done 2026-11-23
resolution: Python inventory discovers literal Equals selectors in preprocessed package-mode imports and passes the actual project name to MSBuild. The inventory regression verifies exact Equals selection, case-insensitive quoted equality and default selection. [Verification](spec-deferred-catalog-authority.md)

### DW-30: Current toolchain defaults and some tests remain coupled to newly frozen v1 runtime pins.
origin: spec-deferred 4a73d8a5fd2b
location: references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionToolchainPins.cs:34; test/Hexalith.Builds.Module.Tests/SupportedPlatformPinsCatalogTests.cs:29
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: low
reason: Review BH4/BH9: SupportedPlatformPins now returns immutable v1 literals, but CompositionToolchainPins.DaprRuntimeVersion still delegates to that facade and CompositionPrerequisiteProbe uses it for its documented catalog default. SupportedPlatformPinsCatalogTests also retains current-versus-frozen equality for FrontComposer and Dapr. Values currently agree, so no current hosted failure exists; a future approved current-catalog update would leave the default probe on the frozen runtime and reject the otherwise independent catalog update in tests. This authority split was introduced by the preserved upstream frozen-pin work and is present at integration cae351e20093634483afad16aca3bfd90845eda8. Reconcile the intended current/frozen facade and test authorities in that workstream.
status: done 2026-11-23
resolution: Builds already reads the current Dapr runtime pin for composition prerequisites. The follow-up checks the frozen v1 Dapr SDK against its own literal, alongside independent current catalog assertions. [Verification](spec-deferred-catalog-authority.md)

### DW-31: Active retained compatibility package selections have no current conditional-selection audit records.
origin: spec-deferred a5740c625d89
location: references/Hexalith.Builds/Tools/package-version-audit.json; Props/Directory.Packages.props
source_spec: `5-1-guard-drift-detection-and-the-release-drift-check.md`
severity: medium
reason: Review BH5: The current package audit rows bind EventStore.Gateway5.0.0, ASP.NET OpenAPI11.0.0, OpenAPI3.11.0 and OpenIdConnect11.0.0. The active named views select 4.2.0, 10.0.15, 2.13.0 and 10.0.15, respectively, but any old observations are labeled historical and do not bind the current conditional selections. This leaves current listing/retention provenance incomplete for those consumers. The audit and selectors are unchanged from upstream integration cae351e20093634483afad16aca3bfd90845eda8; extend current view-bound audit evidence in the owning package-audit workstream.
status: done 2026-11-23
resolution: The remaining SDK 4.2 selectors were retired by Builds 286ed438367e9dbb9a0a0ab65a1538f8806bf191. The four current default selections have matching listed audit rows. The verification record identifies the exact catalog and audit inputs. [Verification](spec-deferred-catalog-authority.md)

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

### DW-33: A rerun release run may still list its earlier attempt's same-name outcome artifact, which would make a valid current-attempt outcome non-unique.
origin: spec-deferred 124d582e1b7d
location: tools/nightly.py:338
source_spec: `8-1-nightly-releases.md`
severity: medium
reason: `outcome()` requires exactly one `hexalith-release-outcome` artifact before it rejects artifacts created before `run_started_at`. If GitHub's list-run-artifacts endpoint returns earlier attempts' artifacts for a rerun, every rerun target fails closed as an unreadable outcome (medium if true). To settle it, list the artifacts of a hosted rerun release run. If earlier attempts appear, filter by `created_at >= run_started_at` before the uniqueness check. (declared severity: medium (unverified))
status: done 2026-11-23
resolution: A hosted Timesheets rerun listed same-name publication artifacts from both attempts under its legacy uploader. Nightly now defensively excludes earlier-attempt outcome artifacts before requiring one current match. The regression covers distinct attempt starts, both listing orders, duplicate current artifacts and missing timestamps. [Hosted rerun](https://github.com/Hexalith/Hexalith.Timesheets/actions/runs/44421310299)

### DW-34: The delivery barrier's sequential per-status scans can miss a `deliver.yml` run that moves into `waiting` between two status queries.

status: done 2026-11-23
origin: spec-deferred fda010c8a0b1
source_spec: `8-1-nightly-releases.md`
severity: medium
archived: 2026-11-23

### DW-35: Anonymous trusted-Builds REST acquisition in each nightly job may exhaust the shared unauthenticated rate limit on hosted runners.
origin: spec-deferred 30d6c9d78f3f
location: tools/delivery_runtime.py:365 (Transport.builds), reused by tools/nightly_runtime.py Transport
source_spec: `8-1-nightly-releases.md`
severity: medium
reason: Each nightly job acquires the trusted Builds release through delivery's existing anonymous `Transport.builds` reads: about four per job, twelve per night. If hosted runners share egress IPs, the 60/hour unauthenticated quota may already be spent, failing initialization and with it the whole night (medium if true). The same anonymous pattern already runs hourly in delivery and passed story 7's hosted requalification. To settle it, record the X-RateLimit headers from hosted nightly runs. If they show exhaustion, authenticate these public reads with the job token. (declared severity: medium (unverified))
status: done 2026-11-23
resolution: Dispatch, wait and publish-ready use the existing read-only job token for fixed Builds REST reads, with credential-free Git object acquisition and no anonymous fallback. Hosted rate-limit headers remain unobserved. [Verification](spec-deferred-cicd-qualification.md)
- source_spec: `_bmad-output/specs/spec-cicd/stories/8-2-nightly-builds-bump.md`
  summary: Confirm that the bump-push and keepalive GITHUB_TOKEN fast-forward pushes to CiCd `main` are not blocked by classic branch protection; the hosted probe only pushed a disposable ref.
  evidence: Story 8-2 review B1 (maybe-false; medium if true). Ruleset 26812262 has only `deletion` and `non_fast_forward`, so fast-forwards pass it, but classic protection on `main` (`protected: true`) was unreadable with the agent token (HTTP 403). To settle it, read `branches/main/protection` with an admin token, or watch the first production bump or keepalive push. A GH006 rejection would fail every bump night loudly.
  status: done 2026-11-23
  resolution: Scheduled run 44715684274 used the repository job token and confirmed the exact validated fast-forward `634fe40ef3f0f1e8aba55251ed8ca574db41fc1d` on CiCd main. This exercised the same repository, job-token Contents write and fast-forward branch policy used by keepalive. An idle-branch keepalive write remains unobserved. [Hosted bump-push job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44715684274/job/136236963286)
- source_spec: `_bmad-output/specs/spec-cicd/stories/8-2-nightly-builds-bump.md`
  summary: Add a parity test showing that the writer's `bump_runtime.add_defaults` gives the same additions as `render.defaults` on a real tagged Builds CI schema that introduces new defaults.
  evidence: Story 8-2 review B9 (maybe-false; medium if true). The v5.1.0 and v5.2.2 `hexalith.ci.v1.json` schemas are byte-identical, so the writer's default-addition path is not reached yet, and every test uses a synthetic schema. If the two traversals drift, the writer either blocks valid bumps or accepts additions the renderer would not produce. The first Builds release that adds a CI default settles it: run both functions on that schema with the registered setups.
  status: done 2026-11-23
  resolution: The released v6.0.6 to v6.1.0 render and independent writer agree for AI.Tools, Commons and PolymorphicSerializations using the setup registry from `87de2b565d5896d7a24d31d065e02f033e5a4adf`. Each gained `ciTimeoutMinutes=30`, empty arrays for `npmWorkspaces` and `buildProjects`, `dotnetTools=false`, nulls for `moduleManifest`, `windowsCheckout` and `publishedBuilds`, and nested defaults `tests.minimumExpectedTests={}` and `tests.failSkips=false`. The 52 renderer tests passed, including this comparison of the complete typed documents. All 19 writer tests passed, including the tagged-schema predicate `minItems`, a forged numeric value for a boolean default and an unsupported predicate.

### DW-36: Verify eligible-source accounting can distinguish legitimate token-floor filtering from unexpectedly missing substantial detector inputs.
origin: spec-deferred c8c02347814a
location: tools/scan.py:findings
source_spec: `9-nightly-cross-module-duplicate-scan.md`
severity: high
reason: The report validator accepts coherent all-zero counters. Actual pinned jscpd 5.4.3 reports zero sources for two comment-heavy 100-line files below the token floor, while substantial 100-line copies report two sources and one clone. No engine failure on an eligible substantive corpus was reproduced. Establish the pinned engine's eligible-source counting contract and reproduce an unexpectedly omitted eligible input before introducing a coverage invariant. Evidence: _bmad-output/implementation-artifacts/story-9-parent-counter-check.log. This is review finding B10, unverified, rather than an observed production defect. (declared severity: high (unverified))
status: open

- source_spec: `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md`
  summary: Scope the shared guide's mandatory Builds pre-push command for standalone tooling repositories.
  evidence: Review B1 (medium): AI.Tools entry points require hexalith-llm-instructions.md, whose new CI/CD section requires references/Hexalith.Builds/check.py before every push, but AI.Tools has no Builds checkout or .gitmodules. Clarify tooling versus product-module scope; the workflow defers agent-context changes found in review.
  status: done 2026-11-23
  resolution: AI.Tools `736687b79c1e4fa8beabdab75c4675bb76c466b9` scoped the checker prerequisite to adopted modules and specified standalone clones with Builds as a direct submodule. The wording is present in the checked-out main guide blob `2cda6714f426cb5c419d3b15d28a20e57dd7b039`.

- source_spec: `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md`
  summary: Make the restricted module-credential refusal rule explicitly override the shared Git guide's interactive maintainer fallback.
  evidence: Review B2 (medium): hexalith-llm-instructions.md both prohibits switching credentials after module refusals and calls hexalith-git-instructions.md the Git source of truth; the latter permits a maintainer-profile fallback for an explicitly requested interactive push to an uncovered repository. Resolve precedence without broadening module credentials; this instruction-file correction is deferred by the build review workflow.

- source_spec: `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md`
  summary: Describe package publishing under the shared guide's release flow rather than as a push/PR CI action.
  evidence: Review B3 (low): the new shared-guide CI bullet includes package publishing, while generated CI is read-only and the release caller owns publication; the adjacent nightly release paragraph is correct. This wording correction edits agent-context instructions and is deferred by the build review workflow.

- source_spec: `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md`
  summary: Document forbidden release/commitlint configuration and agent-tooling portions alongside the positive ownership list.
  evidence: Review B4 (low): templates/perimeter.json.j2 also owns absent release/commitlint config, selected package entries, commitlint hook lines, Directory.Build.rsp and bmad-testarch-ci paths, while the final ownership body lists the positive ownership portions. Guard enforcement remains unchanged; the generated agent-context clarification is deferred by the build review workflow.
  status: done 2026-11-23
  resolution: The canonical ownership block and rendered module manifests now describe the guard's release and commitlint settings, package entries, hook lines, response files and agent-tooling paths.

- source_spec: `_bmad-output/specs/spec-cicd/stories/10-2-agent-instructions-and-deny-entries.md`
  summary: Preserve foreign instructions or fail safely when repairing malformed or duplicated perimeter markers before pilot adoption.
  evidence: Review B7 (high, pre-existing): unchanged Builds v5.2.2 Github/lib/perimeter.py _marker() replaces the whole instruction file for unbalanced, duplicated or reversed markers. The parent reproduced foreign prefix/suffix loss for unbalanced and duplicated markers; tagged tests explicitly assert recreation. Evidence is _bmad-output/specs/spec-cicd/evidence/10-2/review-dependency-probe.json. Resolve in Builds and qualify the accepted tag before relying on preservation for malformed pilot input; this story adopted no production module.


- source_spec: `_bmad-output/implementation-artifacts/spec-10-1-module-agent-token.md`
  summary: Describe 10-2's canonical policy template without calling it already delivered in the 10-1 closeout.
  evidence: Closeout review B1 (low): the current-disposition paragraph says "its delivered policy" while all qualification is pre-adoption and no module delivery is proved. The verification record, reproduction recipe and triage explicitly state the canonical-template scope; the review workflow defers corrections to specifications.
  status: done 2026-11-23
  resolution: Story 10-1's dated disposition identifies the canonical template and places module delivery at the pilot. This matches `delivery_limit` in the [closeout receipt](../specs/spec-cicd/evidence/10-1/closeout-verification.json).

- source_spec: `_bmad-output/implementation-artifacts/spec-10-1-module-agent-token.md`
  summary: Describe observed credential-source continuity without implying verified token-byte or grant continuity in the 10-1 closeout.
  evidence: Closeout review B6 (low): the current-disposition paragraph says "same protected module credential" but source path, account and expiration alone do not establish unchanged bytes or grants since the historical probes. Verification/recipe evidence and triage record this limit, and fresh read-only checks do not requalify write restrictions. The review workflow defers the spec wording correction.
  status: done 2026-11-23
  resolution: Story 10-1 lists the observed source path, account and expiration and attributes the write outcomes to the historical probes. All 41 retained evidence files matched the hashes in the closeout receipt.


- source_spec: `_bmad-output/implementation-artifacts/spec-19-migrate-chatbot.md`
  summary: Ship bounded long-running nightly-hook support as a separate prerequisite before ChatBot adoption; see `_bmad-output/implementation-artifacts/prerequisite-19-long-running-nightly-hooks.md`.
  evidence: On 2026-11-16 the human approved the recommendations. ChatBot preserves a real weekly recovery sweep with a 330-minute job allowance and ten serial 20-minute scenarios plus 30 minutes of topology margin. Builds v6.0.6 limits the hook to 45 minutes, while CiCd currently waits 300 minutes. Reuse the existing fresh-token polling slices and handoffs, retain the 45-minute default, and extend bounded waiting through subsequent release stages. Story 19 must not adopt before the prerequisite ships.

- source_spec: `prerequisite-25-candidate-signing.md`
  summary: Unverified medium: determine whether exact SDK timestamp/chain command transports need a separate per-command deadline.
  evidence: The wrapper has no independent deadline, but no indefinitely waiting SDK transport was demonstrated; inspect the installed transport cancellation/timeouts or reproduce a real stalled command. Hosted-job deadlines and explicit cancellation already bound ordinary CI use.
- source_spec: `prerequisite-25-candidate-signing.md`
  summary: Unverified medium: determine whether exact SDK timestamp/chain command transports need a separate per-command deadline.
  evidence: The wrapper has no independent deadline, but no indefinitely waiting SDK transport was demonstrated; inspect the installed transport cancellation/timeouts or reproduce a real stalled command. Hosted-job deadlines and explicit cancellation already bound ordinary CI use.

- source_spec: `spec-fix-projects-publication-checks.md`
  summary: Verify native-library resolution if a selected Projects catalog adapter factory requires an unmanaged dependency.
  evidence: Blind review identified a possible gap in the fixture-only managed owner loader, but no current selected factory requiring this path was demonstrated. Medium severity remains unverified; reproduce a real factory with a selected native dependency and conflicting ambient resolution before expanding the loader.

- source_spec: `_bmad-output/implementation-artifacts/spec-20-migrate-eventstore.md`
  summary: Resolve the existing CiCd source-discovery capability gap before activating EventStore.
  evidence: Latest candidate discovery selects 22 files but reports 58 unresolved source-coverage diagnostics; see evidence/20/scan-source-coverage-review.json. This remains a blocking activation prerequisite, with no exclusions or audit bypass.

- source_spec: `_bmad-output/implementation-artifacts/spec-fix-folders-component-fixtures.md`
  summary: Harden the existing component verifier against outer SIGTERM cancellation so private files, containers and child processes are observed and cleaned.
  evidence: BH2 verified the default SIGTERM path bypasses context cleanup; the baseline verifier already had no signal handlers around its temporary fixture and child launch.

- source_spec: `_bmad-output/implementation-artifacts/spec-fix-folders-component-fixtures.md`
  summary: Bound component-child output capture during execution to prevent disk or memory exhaustion before diagnostic truncation.
  evidence: BH3 and EC1 identify the same pre-existing capture limit gap: baseline capture_output=True accumulated without a cap; the refactor spools to disk and then reads the full output.

- source_spec: `_bmad-output/specs/spec-cicd/stories/28-1-self-contained-maintenance-test-fixture.md`
  summary: Make test_maintenance.py independent of a developer's global Git config, such as a `url.<ssh>.insteadOf https://github.com/` rule or `core.autocrlf=true`.
  evidence: Blind Hunter reproduced this with GIT_CONFIG_GLOBAL: `git remote get-url` in tools/maintenance.py:51 expands insteadOf, so both origins look foreign, and autocrlf rewrites the checked-out workflow. The behavior predates 28-1, which used the same tool call and checkout. It does not occur in Actions or the bump scratch. A fix must keep tools/maintenance.py unchanged and must not drop the safe.directory entries that runners may rely on.
  status: done 2026-11-23
  resolution: The fixture keeps caller Git trust settings when reading the committed CiCd and Builds inputs, then isolates configuration for its disposable repositories. The 28 maintenance tests passed, including a subprocess render with a global GitHub URL rewrite, core.autocrlf=true and explicit safe.directory trust for both real sources.

- source_spec: `_bmad-output/specs/spec-cicd/stories/28-1-self-contained-maintenance-test-fixture.md`
  summary: Add refusal tests for the maintenance render guards that still have none.
  evidence: The guards without tests are abbreviated revisions, a target HEAD other than the selected revision, a registration render not at origin/main, a changed incoming owned workflow (baseSha256), an uncommitted target workflow, an unrelated preparation output or receipt, and a policy path outside .github/workflows/*.yml. Each is a refusal in tools/maintenance.py:118-186. 28-1's fixture now reaches them for their own reasons, but the gap predates this story and is outside its acceptance criteria.
  status: done 2026-11-23
  resolution: The 28-test maintenance suite exercises abbreviated owner and target revisions, a mismatched HEAD, stale registration main, unexpected committed and uncommitted workflow bytes, occupied proposal and receipt files, an out-of-scope directory and an invalid workflow extension. Each refusal checks the reason and preserves the workflows, index entries and flags, and outputs.

- source_spec: `_bmad-output/implementation-artifacts/spec-19-migrate-chatbot.md`
  summary: Human scope decision needed: a ChatBot product story to make the required live/release cases passable (EventStore 5 with a `net11.0` retarget, and atomic participation in `ChatBotAdmissionEvidenceValidator`) before story 19 resumes.
  evidence: On 2026-11-18 the human parked story 19. ChatBot `ddd385ec6b37a7bb6362cdc66cb3a1a0def935d3` still pins EventStore `77a2dafdf2e6aab7382afab7ab50e22144361d42`, whose owner loader refuses the System.Text.Json snapshot. EventStore v5.0.0 changed that loader but requires `net11.0`; whether it fixes ChatBot is unverified. Separately, `ValidateAtomicParticipationAsync` always returns `CanonicalExecutionUnavailable`, so every ChatBot nightly release would fail. The CiCd half of `prerequisite-19-long-running-nightly-hooks.md` waits for this decision. See `_bmad-output/specs/spec-cicd/evidence/19/blockers-20261118.json`.

- source_spec: `_bmad-output/implementation-artifacts/spec-19-chatbot-latest-dependencies.md`
  summary: Two sibling fixes are needed before the ChatBot latest-dependencies story can resume. Story 21 must push the Parties EventStore 5.3.x qualification as an early preparation push. Story 18 must push the Projects product fix once Conversations releases the query APIs.
  evidence: On 2026-11-19 the human pinned every ChatBot gitlink to its submodule's latest `main` and waited for both sibling fixes.
    - Parties: main `e88937fb6bc6d6ceaf66996abcf1f753102abf71` and v4.0.0 have `Directory.Build.targets` blob `3b8f26b17d9f0d14b34c8b03978b957e246de3aa`, which enables compiled owner declarations only through EventStore 5.1.1. Tenants main requires 5.3.0 or 5.3.1.
    - Projects: main `69697a088f1e407a59a2cbf2b21c0a2206aa72c8` does not compile against Conversations v2.0.0.
    - Decision: the human then approved two changes. Story 21 qualifies 5.3.x early, and story 18 pushes Projects without waiting for story 11.
    - Conversations: main CI is green on `734b92d1585d467ea7d8b686392c76135c036d5f`, but release run 44517857028 failed on Builds v6.3.4 with HXW006 on a retained fixture ProjectReference. The human then chose Builds v6.4.2 (`8ad2c2285e2d0cec0a173882b3a3a926d555fe48`) for ChatBot's Builds gitlink and tool.
    - See `_bmad-output/specs/spec-cicd/evidence/19/latest-dependencies/main-readback-20261119.json`.

- source_spec: `_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md`
  summary: Update the Commons and PolymorphicSerializations references that story 11 left behind when it deleted the tool-only npm toolchain. The foreign AGENTS.md, CLAUDE.md and copilot-instructions text still requires the repository-pinned commitlint CLI, `commitlint.config.*` and the commit hook. Poly's `.slnx` (line 5, `package.json`) and README (lines 145-146, semantic-release override) are also stale.
  evidence: Retirement commits Commons `a83959832ebdad9fe5a5ea268fb0224c49cfa8ea` and Poly `c547c763a20e1fbf6b7a5c9d3b4791260fb61149` removed `package.json`, its lockfile and `.husky/`, and the perimeter forbids `commitlint.config.*`. On current mains the stale text remains at Commons `77b534ebbceebe58a4582ad8840b8cc78f6c10a7` (AGENTS.md, CLAUDE.md and `.github/copilot-instructions.md`, lines 51-69) and Poly `ed8a6d3149b0675f18b5ff17b4b948192ec354e3` (AGENTS.md and CLAUDE.md, lines 52-56). An agent following that text looks for a validator and a hook that no longer exist. The fix edits foreign, non-owned instruction text, so it needs a module-token product push qualified by `check.py` (review BH3, EC7, EC8).

- source_spec: `_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md`
  summary: Give the shared release an expected package set per module, so a project that stops being packable fails the release instead of publishing fewer packages.
  evidence: Before adoption, Poly called the legacy Builds release with `expected-package-count: '2'` and `package-manifest: tools/release-packages.json` (Poly `c547c763^:.github/workflows/release.yml:67-68`). The shared release (`release_build.py`, `release_publish.py:verify_packages`) verifies only the packages it actually built, and `hexalith-ci.json` has no package-set field. Commons still checks its 12 packages in its `after-unit-tests` CI hook. Poly and every later adopter have no such check. The gap is in the shared release design (stories 3-x), so it predates story 11 (review BH4).

- source_spec: `_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md`
  summary: Name the method and path in the nightly runtime's retry-budget and invalid-retry-delay errors.
  evidence: `tools/nightly_runtime.py:399` and `:403` raise `<delay error>: HTTP <status>; {...}` and `GitHub API retry budget exhausted: HTTP <status>; {...}` with no method or path, while terminal errors say `GitHub API <method> <path> failed`. The message had no path before story 11's diagnostics commit `a968a421` either, so this predates the story. A caller that doesn't add its own context therefore can't name the endpoint (review BH12).
  status: done 2026-11-23
  resolution: The nightly runtime retains the validated method and query-free path on retry-delay and budget refusals. All 40 runtime tests passed, including checks for bounded HTTP evidence, credential redaction, transport errors and a single request with no retry sleep.

- source_spec: `_bmad-output/implementation-artifacts/spec-14-migrate-agents.md`
  summary: Agents' isolated package-consumer restore uses TreatWarningsAsErrors with default NuGet audit, so a new low or moderate advisory could fail the after-unit-tests hook despite the central NU1901/NU1902 treatment.
  evidence: Pre-existing at 805b35da (validate_consumer already set TreatWarningsAsErrors). Unverified; settle it by restoring the consumer against a package with a known low-severity advisory and checking whether NU1901 becomes an error.
- source_spec: `_bmad-output/implementation-artifacts/spec-14-migrate-agents.md`
  summary: Agents' tests/tooling suite (hook-script failure paths, UI consumer assets, built-package hook) no longer runs in any CI after adoption; decide whether these hook-tooling tests stay local-only (with an owner) or move into a product gate.
  evidence: The delivered after-unit-tests action runs only scripts/check-built-packages.py, and the shared CI and check.py run only .NET projects (verification-gap review, story 14).
- source_spec: `_bmad-output/implementation-artifacts/spec-14-migrate-agents.md`
  summary: Confirm, by human readback on nuget.org, that the legacy API key behind NUGET_API_KEY is expired or no longer covers Hexalith.Agents* (story 14 review finding BH7).
  evidence: Two attended probes of nuget.org/account/apikeys opened Trusted Publishing instead; only story 11's 2026-11-16 "expired" record supports the disposition. Agents' NUGET_API_KEY grant and legacy policy 26964 are already removed.
- source_spec: `_bmad-output/implementation-artifacts/spec-14-migrate-agents.md`
  summary: RESOLVED — the BH7 legacy nuget.org API key readback for Hexalith.Agents is closed.
  evidence: On 2026-11-22 the human ruled "NUGET API KEYS are obsolete, use trusted publishing", so no readback will be done. Agents publishes only through scoped trusted publishing policy 28307; its NUGET_API_KEY grant and legacy policy 26964 are removed. This resolution supersedes the open entry above without rewriting its evidence.

### DW-37: Unreadable `deferred:` items in 11-pilot-migration-commons-and-polymorphicserializations.md
origin: spec-deferred-malformed 1d1be2e49bcd
location: n/a
source_spec: `11-pilot-migration-commons-and-polymorphicserializations.md`
severity: low
reason: The dev session recorded deferred findings the orchestrator could not parse, so they were NOT filed as entries: item 1: not a mapping (got str); item 2: not a mapping (got str). Read `11-pilot-migration-commons-and-polymorphicserializations.md`'s frontmatter and re-file them by hand.
status: done 2026-11-23
resolution: Reconciled both original findings. Story 30-3's approved organization-wide App installation covers the historical Hexalith.Docs grant, as recorded in archived DW-38. The nine overlapping NuGet policies have their own open item, DW-44. [Story 30-3](../specs/spec-cicd/stories/30-3-reconcile-organization-wide-cicd-app-access.md) · [DW-38](deferred-work-archive.md#dw-38-complete-current-app-selected-repository-membership-remains-unverified)

### DW-38: Complete current App selected-repository membership remains unverified.

status: done 2026-11-22
origin: spec-deferred 4ec62ad298c1
source_spec: `30-1-verify-the-cicd-app-workflow-inventory.md`
severity: medium
archived: 2026-11-23

### DW-39: Current route-specific owner continuation or retirement confirmations remain pending.
origin: spec-deferred 10b7fe32491e
location: docs/cicd-app-inventory.md#migration-owner-dispositions
source_spec: `30-1-verify-the-cicd-app-workflow-inventory.md`
severity: medium
reason: All thirteen migration route/profile records preserve historical authority and read-only hosted results but have retirement_confirmation_observed false. No route was removed. The corresponding EventStore or Projects owner must provide an attributable decision before retirement; historical success cannot supply consent.
status: open

### DW-40: Workflow discovery skips case-variant extensions such as .YML.
origin: spec-deferred 5a4d3459c21e
location: tools/check_app_inventory.py:184
source_spec: `30-1-verify-the-cicd-app-workflow-inventory.md`
severity: medium
reason: tools/check_app_inventory.py and check_global.workflow_paths compare path.suffix case-sensitively, so a .github/workflows file ending .YML that selects cicd-app is not inspected. GitHub documents only .yml and .yaml and does not state whether matching is case-sensitive. A hosted probe of an uppercase-extension workflow, or an authoritative GitHub statement, settles it; if GitHub runs such files, casefold the suffix in both discovery paths. (declared severity: medium (unverified))
status: done 2026-11-23
resolution: CiCd conservatively inspects case variants of both YAML extensions. The App inventory refuses unreviewed privileged parent workflows. Global lint reports case variants in parent and rendered paths with the lowercase extension required by pinned zizmor. This is a local discovery guarantee.

### DW-41: The relocated EventStore verifier suite is not discovered by the CiCd tool-suite gate.

status: done 2026-11-23
origin: spec-deferred 20f3d4904c68
source_spec: `28-3-executable-fixtures-out-of-evidence.md`
severity: medium
archived: 2026-11-23

### DW-42: Live in-progress procedures still name executables under evidence, which AGENTS.md now forbids without exception.
origin: spec-deferred eaab043bb34f
location: _bmad-output/implementation-artifacts/spec-23-migrate-tenants.md:64
source_spec: `28-3-executable-fixtures-out-of-evidence.md`
severity: medium
reason: spec-23-migrate-tenants.md (in-progress) names evidence/23/read-preflight.py for the next read-only AD-21 refresh and evidence/23/qualify-eventstore-snapshot-candidate.py; eventstore-release-readiness-20261117 READMEs invoke evidence-resident verify and audit scripts. Pre-existing: the removed AGENTS.md sentence exempted only the runbook-named pre-adoption runners for stories 17, 18, 20 and 21, which this story relocated. Resolution needs AGENTS.md wording or relocating story 23 tooling, both outside this story.
status: done 2026-11-23
resolution: The live Tenants preflight, its test and the prerequisite verifier now run from tools/. The completed EventStore packet points to current procedures and its pinned replay record. [Verification](spec-deferred-cicd-qualification.md)

### DW-43: The Parties publication runner's exact-input checks are bare asserts that python3 -O removes.

status: done 2026-11-23
origin: spec-deferred ef40bb6bea8b
source_spec: `28-3-executable-fixtures-out-of-evidence.md`
severity: medium
archived: 2026-11-23

### DW-44: Resolve NuGet trusted publishing scopes that overlap the pilot package IDs

origin: manual recovery of story 11 deferred item 2 from DW-37, 2026-11-23
location: nuget.org Trusted Publishing policies for the Hexalith package owner
source_spec: `11-pilot-migration-commons-and-polymorphicserializations.md`
severity: high
reason: The November 22 readback identified nine other repository policies whose wildcard push scopes covered Commons and PolymorphicSerializations package IDs. The maintainer accepted the pilot with this exception open. Recheck the nine policy IDs and record the owner-approved disposition of each overlap. [Pilot repair receipt](../specs/spec-cicd/evidence/11/ad-7-ad-21-maintainer-repair-20261122.json) · [Maintainer acceptance](../specs/spec-cicd/stories/11-pilot-migration-commons-and-polymorphicserializations.md#maintainer-acceptance--2026-11-22)
status: open

- source_spec: `_bmad-output/implementation-artifacts/spec-deferred-validation-findings.md`
  summary: Recheck the release run attempt before recording a terminal outcome error if the artifact read fails.
  evidence: Nightly already rechecks attempt identity after a successful artifact download. The baseline error path stores a terminal outcome error immediately, so a rerun that changes the artifact listing before the status recheck can be missed. Add a controlled attempt change during the listing and verify that the next attempt remains pollable.
  status: done 2026-11-23
  resolution: Wait revalidates the correlated attempt after either result of an artifact read. A newer or temporarily unconfirmed attempt remains pollable. The regression covers running and completed replacements and a transient confirmation failure after missing and readable previous-attempt artifacts. [Verification](spec-deferred-release-verification.md)

### DW-45: Delivery's shared concurrency group can replace a pending main push before its evidence check runs.
origin: spec-deferred 85628a2803d3
location: .github/workflows/deliver.yml:20
source_spec: `28-6-evidence-policy-and-growth-stop.md`
severity: medium
reason: The existing workflow-level group uses GitHub's single pending slot. If a later run replaces the pending push, that next push compares against its own previous SHA. A replay or concurrency redesign affects Delivery scheduling.
status: done 2026-11-23
resolution: Evidence has its own PR and main push workflow without concurrency. The checker still uses each event's exact baseline. [Verification](spec-deferred-cicd-qualification.md)

### DW-46: Nightly's observers consume the aggregate Delivery run status and conclusion.
origin: spec-deferred e9bd5aa3af46
location: tools/nightly_delivery_wait.py:331 and tools/nightly.py:205
source_spec: `28-6-evidence-policy-and-growth-stop.md`
severity: medium
reason: An evidence-only failure can make an otherwise qualifying post-bump Delivery run red to the propagation observer. The pre-dispatch barrier also waits for the aggregate run to finish.
status: done 2026-11-23
resolution: Both Nightly observers continue to query Delivery. Evidence runs in a separate workflow and has its own status and conclusion. [Verification](spec-deferred-cicd-qualification.md)

- source_spec: `_bmad-output/implementation-artifacts/spec-deferred-catalog-authority.md`
  summary: Account for catalog imports whose inclusion depends on MSBuildProjectName when discovering Python inventory views.
  evidence: In a real .NET 11.0.100 probe, a StartsWith condition on an import hid Nested.Legacy from default preprocessing. Evaluating Nested.Legacy directly selected 4.2.0 from the imported Equals selector, while inventory used 5.0.0. Discover the relevant views without dropping package-mode evaluation or replacing actual MSBuild selection.

- source_spec: `_bmad-output/implementation-artifacts/spec-deferred-catalog-authority.md`
  summary: Honor conditional package inclusion in the C# default catalog lookup when there is no materialized snapshot.
  evidence: The current catalog makes Hexalith.Platform.TestExtension 2.2.5 available only to Hexalith.Platform.EventStoreHost. MSBuild excludes the package in the default view. CompositionDeclarationOptions can still return the item by reading the raw XML without evaluating its enclosing ItemGroup condition.

- source_spec: `_bmad-output/implementation-artifacts/spec-deferred-builds-invocation-and-attachment.md`
  summary: Use option-safe SDK paths when restoring and building explicitly listed additional test projects.
  evidence: Builds `Github/lib/ci_pipeline.py` passes `tests.additional` project paths directly to restore and build. A root filename starting with a dash is accepted by the path validation and can be interpreted as an SDK option. The solution-path repair in DW-7 uses a contained absolute path for both commands.
