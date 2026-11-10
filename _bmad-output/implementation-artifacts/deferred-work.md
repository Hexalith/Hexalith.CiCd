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
