---
title: 'Fail-fast CI: build and unit tests'
type: feature
created: '2026-11-09'
status: done
baseline_revision: 4e052874ad70b4edceb1b789439dd45c08d87907
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: b5eb25c630b58322fa13f1c5e384b9909b66099b
review_loop_iteration: 0
followup_review_recommended: false
context:
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/AGENTS.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-llm-instructions.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-git-instructions.md
  - /home/administrator/projects/hexalith/cicd/_bmad-output/specs/spec-cicd/pipeline-stages.md
  - /home/administrator/projects/hexalith/cicd/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md
warnings: [oversized]
deferred:
  - summary: >-
      Existing Module tests intermittently fail temporary Git-workspace and manifest validation in local runs.
    evidence: |-
      Before the review patch, the full shared unit run passed 2915 Module tests with 3 existing skips. A later final run failed 98/2918 tests with Git metadata/manifest fixture errors. AttachAdmissionTests reproduced failures both with the new stop-on-fail override (12/133) and without it (92/133); individual failing tests passed and 100 fresh reflection validation probes passed. Product files are unchanged; precise test-isolation cause remains unresolved.
    location: >-
      test/Hexalith.Builds.Module.Tests/AttachAdmissionTests.cs:1859
    severity: medium
  - summary: >-
      Builds' own CI no longer runs Hexalith.Builds.Tooling.IntegrationTests until stage 4 executes integration projects.
    evidence: |-
      The replaced inline dotnet job ran the project explicitly. AD-13 now classifies it as integration (hosted run 42622137434 lists it under "integration"), and this story's intent forbids stage 4 execution. Its only ungated test, ToolAssembliesHaveIndependentEntryPoints, is unrun meanwhile; live tests skip without LiveGate. Story 2-5 implements integration execution and should confirm this project runs there.
    location: >-
      .github/workflows/builds-ci.yml dotnet job; test/Hexalith.Builds.Tooling.IntegrationTests
    severity: low
  - summary: >-
      The reusable CI job's fixed 30-minute budget may be too short for larger consumers, with no per-project hang protection.
    evidence: |-
      Builds' own hosted build/unit job took about 17 minutes. Whether EventStore, Parties or other large modules exceed 30 minutes for stages 2-3 is unknown; a hung test would consume the budget without a dump. Settle by measuring stage 2-3 durations when those modules adopt the shared CI.
    location: >-
      .github/workflows/ci.yml:28
    severity: medium (unverified)
  - summary: >-
      ChatBot's test projects cannot run under the VSTest runner its global.json implies once it adopts the shared CI on SDK 10.
    evidence: |-
      ChatBot's global.json (SDK 10.0.403) selects no test runner, so the shared pipeline uses positional VSTest as AD-13 requires. Its 14 test projects reference plain xunit.v3 (Builds catalog 4.0.3), xunit.runner.visualstudio and Microsoft.NET.Test.Sdk. A reviewer reproduced that setup: `dotnet test --no-build` fails with "Testing with VSTest target is no longer supported by Microsoft.Testing.Platform on .NET 10 SDK". This is preexisting module configuration, and ChatBot's own CI already fails. At adoption, select Microsoft.Testing.Platform in global.json or use xunit.v3.mtp-off.
    location: >-
      references/Hexalith.ChatBot/global.json
    severity: low
  - summary: >-
      Builds releases also stop exercising Hexalith.Builds.Tooling.IntegrationTests until stage 4 runs integration projects.
    evidence: |-
      builds-release.yml passes HEXALITH_G4_SOURCE_CI_RUN_ID. Get-VerifiedSourceCiRun (Tools/G4PackageQualification.functions.ps1) accepts the exact-SHA push run of builds-ci.yml as the source-test evidence. Since this story, that run classifies Tooling.IntegrationTests as integration and does not execute it. This is the same root cause as the deferred Builds CI coverage item. Story 2-5 should confirm the project runs in stage 4 for both CI and release evidence.
    location: >-
      .github/workflows/builds-release.yml; Tools/G4PackageQualification.functions.ps1
    severity: low
  - summary: >-
      Cross-repository resolution of $/ in the reusable ci.yml has not been exercised by any hosted run.
    evidence: |-
      The hosted probe (run 42615634829) and Builds' own calls are same-repository, so the caller and workflow commits coincide. Whether a module's cross-repository workflow_call resolves $/Github/ci-* to Hexalith.Builds at job.workflow_sha is documented but unverified. If it does not, every consumer's CI fails at preparation. Settle with the first module's hosted call of Hexalith/Hexalith.Builds/.github/workflows/ci.yml; if it fails, apply AD-9's pinned own-code checkout.
    location: >-
      .github/workflows/ci.yml:54
    severity: medium (unverified)
---

<intent-contract>

## Intent

**Problem:** Modules need one CI implementation that builds in package mode and stops at the first failing unit-test project. Builds must exercise that reusable pipeline itself.

**Approach:** Add reusable CI through stages 2–3, with a first slot reserved for story 5-1's guard. Share stdlib Python build flags, evaluated solution-project classification, and project execution with the future local check.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds` on main. Verify `$/` with an actual hosted probe FIRST, before pipeline implementation; if it fails apply AD-9's own-code checkout at `job.workflow_sha`, never execute code from the module's Builds gitlink. Composites resolve scripts from `GITHUB_ACTION_PATH`. Guard's reserved stage is first in the CI job; implementation comes in 5-1. Read configuration through `Github/lib/ci_config.py` with trusted repository/sample context. Use module global.json and rollForward. Restore once and build Release with analyzers, warnings as errors, package mode, no audit, no automatic response files, and the trusted Builds NuGet config on every relevant command. Initialize only Builds plus explicitly listed direct root-declared submodules, without recursion. Classify only solution projects evaluated with `IsTestProject=true`, identified by repo-relative forward-slash csproj paths. Apply AD-13 names and only integration/exclude overrides; exclusions must name enabled actions. Unit projects run in ordinal path order; failure stops between projects, never inside a project. Use MTP `--project` versus positional VSTest according to global.json. `solution: none` runs only stage 1. Preserve prior upstream work.

**Never:** Change frozen module-executed files (AD-20), including existing non-test files under `Github/`, the legacy workflows, and specifically `initialize-dotnet`, `initialize-build`, `create-release`, `verify`. Tests are exempt. No workflow-text assertions, source globs for test discovery, arbitrary skips, stage 4/environment/hook execution, local check implementation, sample implementation, legacy job deletion, or removal of `commitlint-caller.yml`. Builds runs no delivered-ref guard. Do not commit or push the superproject.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Build | Complete config with solution | One restore then Release package-mode build, analyzers and mandatory flags; trusted signed nuget.org source | Nonzero restore/build stops before tests |
| No solution | Valid solution none | No SDK, restore, build, discovery or tests | Invalid config fails clearly |
| Classify | Solution lists test and non-test projects, including nested/space paths | Only evaluated test projects; AD-13 defaults, ordinal ordering, integration overrides, enabled-action exclusions | Unknown project overrides and invalid metadata fail without silent test loss |
| Unit failure | First unit project has failing and passing tests; later project exists | All tests in failing project run; later project never starts; nonzero exit | Preserve product failure status |
| Runner | MTP or ordinary global.json | MTP uses --project; VSTest positional; no rebuild/restore in test loop | Unsupported/broken discovery fails closed |
| Trust | Module gitlink differs from workflow code | Pipeline runs own workflow code; submodules are data and explicit dependencies only | Unsupported $/ uses pinned AD-9 fallback |

</intent-contract>

## Code Map

- Implementation root: `references/Hexalith.Builds`; current main is `b5eb25c630b58322fa13f1c5e384b9909b66099b`. It was fast-forwarded from story 2-3's `8a3a11d3614f8549100ed9758bb96bf26ab885ff` before implementation; four external legacy/runtime/test changes are baseline, not this story.
- `Github/lib/ci_config.py`: `load_config`/`validate_config` are the single strict stdlib reader; repository context is mandatory, module_root optional. Builds alone can omit buildsTag. Required submodules knob already shipped in 2-3.
- `.github/hexalith-ci.json`: Builds solution and explicit knobs. `schemas/hexalith.ci.v1.json` and `Github/lib/tests/fixtures/contract.json`: completed contract and corpus, reuse unchanged.
- `.github/workflows/builds-ci.yml`: preserve legacy jobs/steps and aggregator (AD-20); replace its old dotnet job's inline build/test work with reusable CI call, preserving job identity/aggregate dependency, and add workflow_dispatch for verification. No need to duplicate that dotnet job.
- `Hexalith.Builds.slnx`: own projects plus fixtures; test projects Evidence.Tests, Module.Tests, Tooling.IntegrationTests. `global.json` selects SDK 10.0.403 and Microsoft.Testing.Platform.
- `Hexalith.Build.props`, `Directory.Build.props`, `Props/Directory.Packages.props`: existing analyzer/catalog imports; do not rewrite product files to make new lane green.
- `Tools/ci/run_python_tests.py`: discovers `Github/*/tests`, including new lib tests, under Python 3.12 and runner Python. `Tools/ci/lint_workflows.py`, `check_public_api.py`, locks, `.github/actionlint.yaml`, `.github/zizmor.yml`: existing pinned real lint/API checks; $/ and job.workflow_* schema-gap exceptions already present.
- `package.json`, `package-lock.json`, `commitlint.config.mjs`: pinned commitlint 21.2.4. Validate exact full message from a temporary file with owning repository's pinned CLI before every commit; keep successful evidence.
- Hosted runner 2.338.2 (job 129150187225) exceeds required 2.336.0, official workflow syntax documents $/, but rollout flag requires an actual execution probe.

## Tasks & Acceptance

**Execution:**
- [x] New temporary `.github/workflows/ci-runtime-probe.yml` and `Github/ci-runtime-probe/action.yml` — smallest hosted workflow_dispatch probe using $/ and GITHUB_ACTION_PATH; validate commit message, commit/push in Builds and run via gh; retain exact SHAs/run link/result in this spec, then remove both files in final implementation diff. If actual $/ fails, record failure and implement AD-9 fallback. No edits to frozen files for the spike.
- [x] New `Github/lib/ci_pipeline.py` and focused helper files as useful — expose reusable build flags, configuration preparation, solution/MSBuild discovery, classification and unit execution as importable functions plus stdlib CLI; select project membership from the actual solution, evaluate properties with package-mode/Release flags, handle cross-targeting safely, reject unknown overrides. Trusted config outside module checkout.
- [x] New Builds NuGet config — clear inherited sources/mappings; map every package to nuget.org, require signatures and trust nuget.org's repository signature with current verified fingerprints.
- [x] New `.github/workflows/ci.yml` and new composites — one contents-read CI job, reserved first guard slot, checkout without credentials or recursive submodules, own-code resolution, validated module setup, pinned setup-dotnet, build, unit tests; expose solution and submodules outputs for later Windows prepare and test-only module-root/expected-source inputs without implementing sample yet.
- [x] `.github/workflows/builds-ci.yml` — invoke reusable CI against Builds in existing dotnet job, keep aggregate verdict and all remaining legacy lanes. Add dispatch trigger to test current SHA.
- [x] `Github/lib/tests/test_ci_pipeline.py` (and supporting behavioral fixtures) — cover matrix with actual subprocess behavior and at least one real SDK solution/MSBuild/test-project test. No workflow-source assertions. Show two tests inside a failing project complete and later project does not start.
- [x] `Tools/ci/README.md` — document scripts, execution and $/ result/fallback, future local-check reuse. Run relevant checks; leave final implementation uncommitted for parent review. Parent then validates commit message, commits/pushes Builds and verifies hosted CI; stages story and gitlink in CiCd.

**Acceptance Criteria:**
- Given Builds main with this change, when builds-ci.yml runs, then its dotnet job executes reusable ci.yml and the Release build and unit projects succeed (hosted job evidence).
- Given first failing unit project, when shared execution runs, then every test in that project completes and no later project/hook/integration work starts.
- Given module solution and knobs, when CI executes, then the matrix behavior holds and future check.py can import the same flags/classifier without interpreting workflow text.
- Given the implementation baseline, when final diff is inspected, then frozen runtime blobs match and stage 1 remains first, with legacy lanes retained.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass

- Review layers: edge-case hunter, verification-gap reviewer, intent alignment. Blind hunter skipped for the three-reviewer concurrency limit.
- verdicts: 8 findings — high 0, medium 4, low 0, false 4, maybe-false 0
- findings:
  - `[false]` `[reject]` Intent: workflow wiring is not exercised by Python tests — the hosted final reusable job is an explicit verification step; a helper test is not being substituted for that surface. Its exact-SHA result is recorded below before completion.
  - `[medium]` `[patch]` Intent: consuming-module initialization only has mocked coverage — same root cause as the CLI preparation gap below; added disposable HTTP-served Git repositories and actual CLI initialization at recorded gitlink commits, leaving unused/nested dependencies uninitialized.
  - `[false]` `[reject]` Intent: script poisoning does not prove native self-reference — the separate hosted no-checkout probe executed the actual $/ action at f2f0a08d8c38d34b390dc937659d2067c8a09cce successfully; the Python poisoning test covers the distinct import boundary.
  - `[false]` `[reject]` Intent: modifying builds-ci.yml could violate the freeze — AD-20 freezes module-executed runtime, explicitly permits Builds' own workflow replacement, and the baseline byte comparison confirms the named composites and legacy shared workflows are unchanged.
  - `[false]` `[reject]` Intent: the diff alone cannot demonstrate chronology or final delivery — actual Git history/Actions evidence proves the probe precedes implementation; final commit/push and hosted acceptance are performed before completion, rather than inferred from patch text.
  - `[medium]` `[patch]` Verification: removing CLI submodule initialization leaves tests green — added actual consumer CLI/Git regression, including recorded older commits, ambient recursive/update-none settings, and unused/nested non-initialization.
  - `[medium]` `[patch]` Verification: flag expectations mirror build_flags/test_flags — replaced the expected oracle with literal required arguments and real SDK conditional source/package controls; missing package mode now fails restore/build and alters evaluated test membership.
  - `[medium]` `[patch]` Edge: xUnit stopOnFail=true stops within a project — confirmed by the reviewer on SDK 10.0.403/xunit.v3 4.0.2 (1/3 tests ran). Added evaluated xUnit detection and supported MTP/VSTest overrides; real fixtures now run all three tests, preserve culture and restore exact source/output config bytes. Multi-target/output-boundary tests cover the VSTest adapter workaround.

### 2026-11-09 — Review pass (follow-up)

- Review layers: blind hunter, edge-case hunter, verification-gap reviewer, intent alignment. None skipped. Diff: Builds `b5eb25c630b58322fa13f1c5e384b9909b66099b..d058a5035f2af09ab3045557ac0b22d6f1040561` plus the CiCd gitlink.
- verdicts: 38 findings — high 0, medium 12, low 21, false 4, maybe-false 1
- findings:
  - `[medium]` `[patch]` Blind: the added `workflow_dispatch` trigger makes every manual builds-ci run fail — confirmed: `Tools/archive-g4-qualification-evidence.py:73` rejects events other than push/pull_request, so `contracts` and the aggregate fail. Release verification filters `event=push`, so only dispatch runs are affected. Gated the archive step on `github.event_name != 'workflow_dispatch'`; the attempt record and evidence upload still run.
  - `[low]` `[defer]` Blind: Builds' own Tooling.IntegrationTests no longer runs in CI — confirmed by hosted run 42622137434's classification; its only ungated test is `ToolAssembliesHaveIndependentEntryPoints` (live tests skip without LiveGate). The intent forbids stage 4 execution here and AD-13 names it integration; story 2-5 implements integration execution. Deferred.
  - `[low]` `[patch]` Blind: module-root fixtures require an undeclared `<root>/references/Hexalith.Builds` gitlink — confirmed in `prepare_config`; Builds' root `.gitmodules` declares only AI.Tools, and a self-gitlink would test a stale Builds. Builds' repository now never initializes a Builds gitlink, including under module-root; listed submodules stay prefixed. Test shared with the module-root gap below.
  - `[medium]` `[patch]` Blind: the path-safety boundary has no direct tests — same root cause as the verification guard gap; added unsafe-form, symlink-escape, solution-project escape and non-gitlink tests. Mutants removing each guard now fail.
  - `[medium]` `[patch]` Blind: TargetFrameworks parsing rejects SDK-valid lists — reproduced on SDK 10.0.403: a multiline list evaluates as `"\n    net10.0;\n    net9.0;\n  "` and discovery failed with "invalid TargetFrameworks". Added `target_frameworks` (trim, drop empty entries) for discovery and the VSTest config override; the regression covers both formats.
  - `[low]` `[reject]` Blind: projects are evaluated by MSBuild several times — real but negligible: a warm `-getProperty` evaluation took 0.36 s. Carrying properties through discovery would restructure the importable API for no meaningful gain.
  - `[low]` `[patch]` Blind: failure messages name only `arguments[0] arguments[1]` — confirmed ("git -c failed"). `run_command` now reports `shlex.join` of the full command; the restore/build failure test asserts it.
  - `[low]` `[reject]` Blind: global.json and xunit.runner.json are parsed more strictly than the SDK (no comments/BOM) — no current consumer uses either form; a lenient JSON parser is more than a direct correction for an unobserved input.
  - `[low]` `[patch]` Blind: the poisoning test cannot detect its named PYTHONPATH regression — confirmed: `-I` ignores PYTHONPATH. The test now also runs under `-P` (PYTHONPATH honored, script directory omitted); a mutant that appends instead of prepending the trusted path now fails.
  - `[low]` `[patch]` Blind: the real-SDK test checks less than documented — exact status preservation is already asserted by the subprocess failure test (exit 23); the README said "both tests" for a three-test fixture, and set comparison hid repeated executions. README corrected; the assertion now compares the sorted list.
  - `[low]` `[reject]` Blind: SIGTERM/SIGKILL can leave overridden build-output xunit.runner.json — SIGINT runs `finally` and CI outputs are disposable; only hard kills of local VSTest runs with PreserveNewest copies are affected, and signal handling adds complexity for that rare case.
  - `[maybe-false]` `[defer]` Blind: fixed 30-minute job budget and no hang protection — Builds' own hosted job needed about 17 minutes; whether larger consumers (EventStore, Parties) exceed 30 minutes is unknown. Medium if true; settle by measuring stage 2–3 duration at adoption. Deferred as unverified.
  - `[low]` `[patch]` Blind: configured paths are interpreted as Git pathspecs — confirmed: config paths permit glob characters. `ls-files` and `submodule update` now run with `--literal-pathspecs`; mocked and real-Git tests cover both commands.
  - `[medium]` `[patch]` Edge: multi-targeted xUnit projects get no stop-on-fail override — reproduced on SDK 10.0.403/xunit.v3 4.0.2: outer `XunitTestProject` is empty, inner is `true`. Execution now reads xUnit identity from every inner build; the fake SDK mirrors the empty outer value, and the cross-targeting test asserts the override (the outer-only mutant fails).
  - `[medium]` `[patch]` Edge: a trailing `;` or whitespace in TargetFrameworks fails discovery — same root cause and fix as the blind TargetFrameworks finding.
  - `[low]` `[patch]` Edge: a Builds run with module-root requires an undeclared Builds gitlink — same root cause and fix as the blind module-root finding.
  - `[false]` `[reject]` Edge: a test project excluded from the solution's Release build fails `dotnet test --no-build` — that is a loud nonzero failure for an evaluated test project that was not built: the required fail-closed result, not silent test loss.
  - `[low]` `[reject]` Edge: NUnit/MSTest stop-on-first-failure settings are not overridden — no Hexalith repository references NUnit or MSTest and the stack mandates xUnit v3; per-framework override branches add complexity for unused frameworks.
  - `[low]` `[reject]` Edge: nuget.org repository-certificate rotation breaks restore under require mode — inherent to the intent's trusted-signer policy. Rotation is an announced, infrequent event that fails loudly and needs one fingerprint addition (now documented in the README); automated tracking is more than a direct correction.
  - `[low]` `[reject]` Edge: `,` or `;` in the trusted Builds path splits `-p:RestoreConfigFile` — hosted paths are `_actions/Hexalith/Hexalith.Builds/<sha>`; only an unusual local path triggers it, it fails loudly, and escaping adds code for an unlikely input.
  - `[low]` `[reject]` Edge: no per-command subprocess timeout — CI is bounded by the job timeout and the local check is story 6; timeouts add parameters and policy.
  - `[low]` `[reject]` Edge: a valueless `.gitmodules` path key raises IndexError — requires a malformed `.gitmodules` that Git rejects for submodule work; it still exits nonzero; guarding it adds a branch for a rare state.
  - `[low]` `[defer]` Edge: the explicit Tooling.IntegrationTests step was removed — same root cause as the blind integration-coverage finding; deferred to stage 4 (story 2-5).
  - `[medium]` `[patch]` Edge: the claim of safe cross-targeting completion is unmet — same root cause and fix as the multi-targeted xUnit finding.
  - `[medium]` `[patch]` Verification: classification and execution tests cannot detect case-insensitive matching or non-ordinal ordering — added lowercase markers and an ordinal-versus-casefold pair to classification, plus an execution-order subprocess test; lower-casing and casefold-sorting mutants now fail.
  - `[medium]` `[patch]` Verification: the GITHUB_OUTPUT contract is never verified — added a CLI `--phase prepare` test asserting the exact `solution`, `global-json` and `submodules` lines for a solution and for `none`; the disabled-output mutant fails.
  - `[medium]` `[patch]` Verification: module-root prefixing is never exercised in a passing case — added a prepare test asserting workspace-relative solution, global.json and submodules, plus expected-source preconditions; shares the module-root gitlink fix.
  - `[medium]` `[patch]` Verification: outer/inner IsTestProject disagreement is untested — added a fake-SDK `outer_only` toggle and a fail-closed test; the disabled-check mutant fails.
  - `[medium]` `[patch]` Verification: path-escape and direct-gitlink guards are untested — shares the blind path-safety fix; real Git rejects a declared path tracked as a regular file before any update.
  - `[medium]` `[patch]` Verification: NuGet.ci.Config's trust policy is not behaviorally verified — added a real-SDK test that packs an unsigned package and restores through one-control variants of the real config: NU3004 under its signature policy, NU1101 under its source mapping, success for the relaxed control. Removing `signatureValidationMode` or widening the mapping now fails it.
  - `[low]` `[defer]` Verification (other): Builds CI no longer runs Tooling.IntegrationTests — same root cause as the blind integration-coverage finding; deferred.
  - `[low]` `[patch]` Verification (other): the poisoning test's PYTHONPATH clause is vacuous under `-I -S` — same root cause and fix as the blind poisoning finding.
  - `[false]` `[reject]` Intent: expectations live at the hosted cross-repository surface while tests exercise Python — carried: same claim as the logged "workflow wiring is not exercised by Python tests" row; the hosted exact-SHA run remains the verification surface.
  - `[low]` `[defer]` Intent: rewiring the dotnet job drops Tooling.IntegrationTests coverage — same root cause as the blind integration-coverage finding; deferred.
  - `[low]` `[reject]` Intent: the within-project completion guarantee covers xUnit only — same evidence as the NUnit/MSTest finding; no non-xUnit framework is in use.
  - `[false]` `[reject]` Intent: MTP test commands drop the literal `-noAutoResponse`/`-warnaserror` switches — the requirement is that no automatic response file is read and warnings fail. SDK 10 MTP forwards those switches to the test application (handshake exit 5), its in-process MSBuild reads no response files, and real-SDK tests with poisoned rsp files at workspace and project roots prove both properties.
  - `[false]` `[reject]` Intent: rollForward, solution-none gating and signature trust live only at hosted/workflow surfaces — carried for the workflow-wiring part (same claim as the logged workflow-wiring row); signature trust is now behaviorally covered by the NuGet policy test.
  - `[low]` `[patch]` Intent: the module-root/expected-source acceptance path is untested and its Builds gitlink prefix unexercised — same root cause and fix as the module-root findings.

### 2026-11-09 — Review pass (follow-up, resumed)

- This resumes the follow-up pass. The previous session committed and pushed its patches as Builds `fe02e57c291d28ea4298e7429850cf26208f5fbc` and wrote its triage log, but it ended before finalization.
- Review layers: blind hunter, edge-case hunter, verification-gap reviewer, intent alignment. None skipped.
- Diff: this story's Builds files `b5eb25c630b58322fa13f1c5e384b9909b66099b..fe02e57c291d28ea4298e7429850cf26208f5fbc`, plus the CiCd gitlink. It excludes the interleaved upstream catalog and dependency commits, which touch none of those files.
- verdicts: 36 findings — high 0, medium 8, low 17, false 10, maybe-false 1
- findings:
  - `[medium]` `[patch]` Blind: a manual dispatch shares the push run's concurrency group and can cancel the push CI that release consumes — confirmed.
    - The group was `builds-ci-${{ github.ref }}` with `cancel-in-progress`. Dispatch run 42636349353 at `fe02e57c` was cancelled when push run 42638222177 started on main.
    - `Get-VerifiedSourceCiRun` requires a successful push run.
    - Fix: added `github.event_name` to the group key, which leaves push and PR grouping unchanged, and documented this in the README.
  - `[low]` `[patch]` Blind: `.gitmodules` parsing splits submodule names that contain spaces — reproduced on Git 2.53.0: `submodule.references/Extra dependency.path` parsed as `dependency.path references/Extra dependency`.
    - Fix: read `git config -z` records and split each at its first newline.
    - The real-Git consumer test now names its spaced dependency after its path, as `git submodule add` does. The old-parsing mutant fails.
    - A missing `.gitmodules` still fails loudly through the named git command.
  - `[low]` `[defer]` Blind: ChatBot selects VSTest with plain xunit.v3 4.x, which fails under SDK 10 — real but preexisting module configuration.
    - ChatBot's `global.json` selects no runner, its 14 test projects use xunit.v3 with runner.visualstudio, and its own CI already fails.
    - The pipeline follows `global.json` as the intent requires, and the SDK error is actionable.
  - `[false]` `[reject]` Blind: dropping `-p:GeneratePackageOnBuild=false` makes Commons pack in stage 2 — no new packing is introduced.
    - The module CI Commons runs today (`domain-ci.yml:433`) builds with the same `-warnaserror` and no such override.
    - Builds' `Hexalith.Build.props:15` sets it to false, and AD-12's stage-2 flags do not include it.
  - `[low]` `[reject]` Blind: the NuGet policy applies only when packages are first extracted, so a warm cache skips it — hosted runners restore into an empty global packages folder, so every package is verified. Builds' hosted restore is the positive real-config case. Warm-cache isolation belongs to the future local check, which the intent excludes from this story.
  - `[medium]` `[patch]` Blind: the composite phase split is untested — same root cause as the verification phase-split gap. Added a prepare→build→unit subprocess sequence test.
  - `[low]` `[patch]` Blind: the README command detaches a developer's listed submodules — confirmed: `--phase all` runs `git submodule update --init --checkout` for them. The README now says so and directs the command to disposable or CI-like checkouts.
  - `[false]` `[reject]` Blind: module response files are ignored without a message — this is the intent's "no automatic response files" rule, and the README states that every MSBuild CLI invocation uses `-noAutoResponse`.
  - `[low]` `[reject]` Blind: classified but unrun integration or excluded projects get no warning or summary — the job log's classification JSON names them.
    - No consumer adopts before stage 4 (story 2-5), and Builds' own loss is already deferred.
    - An annotation or summary would add surface beyond a direct correction.
  - `[false]` `[reject]` Blind: the reserved stage-1 slot comes before a depth-1 checkout — the intent requires the guard slot first. Story 5-1 owns the guard's checkout and history needs, and this story runs no guard.
  - `[low]` `[reject]` Blind: multi-targeted test projects need runtimes CI does not install — no module multi-targets its tests, and a missing runtime fails loudly. Installing extra runtimes would add parsing and setup for an unused case.
  - `[medium]` `[patch]` Edge: a dispatch on main while push CI runs cancels the push run release consumes — same root cause and fix as the blind concurrency finding.
  - `[low]` `[reject]` Edge: Builds CI in a fork is treated as a consumer — fork pull requests run with the base repository identity, and only pushes inside a fork fail, loudly. Identifying Builds by workspace content would weaken the trusted repository context the intent requires; that identity rule is story 2-3's loader.
  - `[low]` `[reject]` Edge: a `.gitmodules` path key with no value raises IndexError — carried: same claim as the logged row. Incidentally, the `-z` parsing patch now yields an empty path instead of a traceback.
  - `[low]` `[patch]` Edge: a declared directory holding exactly one gitlink passes the direct-gitlink guard — reproduced on Git 2.53.0.
    - `ls-files --stage -- references/Holder` returns only `references/Holder/Inner`, and the update would initialize that unlisted child.
    - Fix: the guard now reads `-z` entries and requires the exact path. A real-Git test covers it, and the no-exact-path mutant fails.
  - `[low]` `[reject]` Edge: a BOM in a build-output `xunit.runner.json` raises ConfigError — carried: same claim as the logged strict-JSON row; the code is unchanged.
  - `[false]` `[reject]` Edge: an MTP project with zero tests exits 8 — no module is shown with a zero-test unit project. MTP's loud zero-test failure matches "no silent test loss", and ignoring exit 8 would hide a lost project.
  - `[low]` `[patch]` Edge: the README local command detaches local submodules — same root cause and fix as the blind README finding.
  - `[low]` `[defer]` Edge: the explicit Tooling.IntegrationTests step was removed — carried: same claim as the logged integration-coverage rows; already deferred, not deferred again.
  - `[medium]` `[patch]` Verification: the workflow phase split is never tested — added `test_composite_phase_sequence_restores_once_and_tests_only_in_unit`. Both the restore-in-unit and tests-in-build mutants fail.
  - `[medium]` `[patch]` Verification: the `CI_REPOSITORY`, `CI_MODULE_ROOT` and `CI_EXPECTED_SOURCE` environment context is never exercised — added an environment-only prepare test. It asserts module-root-relative outputs and that a non-Builds repository is rejected as test-only. The environment-default mutant fails.
  - `[medium]` `[patch]` Verification: the excluded classification output is never checked — the override test now asserts the exact classification JSON. A classifier case proves that an exclusion takes precedence over an integration name. The excluded-as-integration mutant fails.
  - `[medium]` `[patch]` Verification: the duplicate-path `.gitmodules` guard is untested — added a duplicate path case that asserts the error and that no update runs. The guard-removal mutant fails.
  - `[medium]` `[patch]` Verification: rejecting escaping runner configurations is untested — added symlinks to a repository source config and to an outside file, plus an outside output directory. Dropping the escape clauses, or only the repository clause, now fails, and the target bytes stay unchanged.
  - `[low]` `[patch]` Verification: captured output from failed discovery commands is never checked — the fake SDK now prints stdout and stderr markers when it fails. New `sln` and `msbuild` failure cases assert exit 17, both markers, and that no tests run. The print-removal mutant fails.
  - `[low]` `[reject]` Verification (other): a hard-linked output config bypasses the source and tracked-file guard — no Hexalith module sets `CreateHardLinksForCopyFilesToOutputDirectoryIfPossible` (repository search). The original bytes are restored in `finally`, and a link-count guard would add complexity for an unused build option.
  - `[low]` `[defer]` Verification (other): the integration deferral also removes Tooling.IntegrationTests from release checks — confirmed: builds-release takes the exact-SHA push CI verdict (`Get-VerifiedSourceCiRun`) as its source-test evidence. Same root cause as the coverage loss deferred under the intent's no-stage-4 boundary; recorded as an extra deferred impact for story 2-5.
  - `[low]` `[defer]` Intent: Builds no longer runs Tooling.IntegrationTests in its own CI ("replace" versus "add and keep" reading) — carried: same claim as the logged intent row; already deferred.
  - `[maybe-false]` `[defer]` Intent: `$/` was proven only by a same-repository top-level probe, and no cross-repository `workflow_call` exercises it — true as stated.
    - Unverified: whether a module's cross-repository call resolves `$/` to Builds at `job.workflow_sha`. GitHub's documented semantics say it does.
    - Medium if wrong. Settle at the first module's hosted call of `ci.yml`. Deferred as unverified.
  - `[false]` `[reject]` Intent: workflow-level stage order, `solution: none` gating and composite wiring have no tests — carried: same claim as the logged workflow-wiring rows. Workflow-text assertions are forbidden; hosted exact-SHA runs are the surface.
  - `[false]` `[reject]` Intent: MTP test commands omit the literal `-noAutoResponse` and `-warnaserror` switches — carried: same claim as the logged row.
  - `[low]` `[reject]` Intent: within-project completion is enforced only for xUnit, and the VSTest override adds refusals for tracked, source and escaping configs that the matrix does not list — the xUnit-only part is carried from the logged row. The refusals are loud, fail-closed outcomes for states no module shows, since build outputs are untracked.
  - `[false]` `[reject]` Intent: a non-csproj solution member fails stage 3 after a successful build — no module solution under `references/` lists a non-csproj project (repository search). AD-13 identifies test projects by `.csproj` path, and the loud failure applies only to that unshown state.
  - `[false]` `[reject]` Intent: classification is case-sensitive — AD-13 names literal suffixes and requires ordinal ordering. No module project uses lower-case markers, so no project changes stage.
  - `[false]` `[reject]` Intent: the dispatch path and its archive gate have no completed hosted run — by reading the code, the gate skips only the archiver, which rejects dispatch; `--record-attempt` and the upload ignore the event. The patched SHA's dispatch run is recorded under Verification.
  - `[false]` `[reject]` Intent: unknown overrides are reported only after restore and build — the auditor itself rates this neutral. Both paths fail without silent test loss, and test identity needs MSBuild evaluation after restore.

## Design Notes

Runtime Python is stdlib only, at least 3.12; no new third-party runtime dependency. Source selection is workflow-owned; module Builds checkout is data. The submodules knob supersedes AD-12's stale single-submodule sentence (pipeline-stages and spine Deferred). Stage 4, guard and sample remain future stories. For the probe only, a short-lived main workflow is authorized by this story's explicit commit/push and runtime-verification requirement; remove its files afterward. Preserve canonical full Git identifiers from Git directly.

SDK 10 MTP evidence: passing `-noAutoResponse` or `-warnaserror` to `dotnet test --project` forwards them to the test application and produces handshake exit 5, before tests run. The shared adapter retains every mandatory MSBuild property and expresses warnings-as-errors with `TreatWarningsAsErrors`/`MSBuildTreatWarningsAsErrors`; it omits those two engine switches only for MTP's in-process MSBuild API. Real SDK tests restore/build and run two tests in the failing project with poisoned `MSBuild.rsp` and `Directory.Build.rsp` at both module and project roots. Both tests complete (one fails, one passes), exit 2 is preserved, and no later project starts. Every actual MSBuild CLI invocation keeps `-noAutoResponse` and `-warnaserror`. This is the executable interpretation of “every relevant command,” not a product-file workaround. See [SDK MTP option semantics](https://learn.microsoft.com/dotnet/core/tools/dotnet-test-mtp) and the [SDK in-process MSBuild implementation](https://github.com/dotnet/sdk/blob/main/src/Cli/dotnet/Commands/Test/MTP/MSBuildUtility.cs).

## Verification

Commands run in `references/Hexalith.Builds` unless stated:
- `python3 -m unittest discover -s Github/lib/tests -v` — complete loader/classifier/executor suite passes, including all matrix behaviors.
- `python3 Tools/ci/lint_workflows.py` — pinned actionlint and zizmor with online audits pass (use current gh read token through environment without printing it).
- `python3 -I Github/lib/ci_pipeline.py --workspace . --repository Hexalith/Hexalith.Builds` — real package-mode restore, build, evaluated classification and unit execution succeed.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and corresponding runner python interpreter invocation — retained Python groups pass.
- Public API checker against staged/final source tree and full frozen-path diff inspection — no removals or frozen runtime changes.
- Hosted probe and final builds-ci.yml reusable job at exact submitted SHAs — real self-reference support and own build/unit execution; record external failures separately if unrelated legacy lanes fail.

### Hosted self-reference probe (before implementation)

- Baseline: `b5eb25c630b58322fa13f1c5e384b9909b66099b`.
- Validated the exact probe message with pinned `@commitlint/cli@21.2.4`: 0 problems, 0 warnings.
- Probe commit: `f2f0a08d8c38d34b390dc937659d2067c8a09cce`, pushed to Builds main.
- [Hosted probe run 42615634829](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42615634829), job `129154686542`, runner `2.338.2`, Ubuntu `26.04.1`: **success** on 2026-11-09.
- With no workspace checkout, `$/Github/ci-runtime-probe` downloaded Builds at the exact probe SHA and printed `SELF_REFERENCE_OK /home/runner/work/_actions/Hexalith/Hexalith.Builds/f2f0a08d8c38d34b390dc937659d2067c8a09cce/Github/ci-runtime-probe` from `GITHUB_ACTION_PATH`. Native self-reference works; the AD-9 fallback is unnecessary. The temporary files are removed by the implementation.

### Local implementation verification

- `python3 -m unittest discover -s Github/lib/tests -v`: **33 tests passed**, including 15 new subprocess/real-SDK pipeline tests (Python 3.14.4).
- The real SDK fixture restores and builds with **0 warnings, 0 errors**, correctly discovers the nested/space-path solution projects, and proves the two-test failing-project boundary with poisoned automatic response files.
- Real Builds package-mode restore and Release analyzer build: **passed**, 0 warnings, 0 errors. With the MTP adapter, Evidence.Tests: **191 passed**; the complete Module.Tests results are recorded in final acceptance below.
- `GH_TOKEN=<current read token> python3 Tools/ci/lint_workflows.py`: **passed** actionlint and online zizmor; 12 exact frozen composite findings, 0 new findings.
- Public API checker `surface`/`baseline_tag` over a temporary-index final source tree `143059724ba4ff318827e29349a3ac519510324c` against `v4.45.1` (`25de7a74d14d099faf7baea5da0cbb0b40264592`): **2479 entries, 0 removals**. The real index and final implementation remain uncommitted.
- `git diff --check`: **passed**. Byte comparison of all 66 baseline non-test `Github/` and workflow paths (exempting tests and Builds' own caller) found **no frozen-runtime changes**.

### Parent verification and matrix audit

- Independent library test run: 33 tests passed, no new skipped tests; independent actionlint and online zizmor passed, 0 new findings.
- Completed real shared unit execution: Evidence 191 passed; Module 2915 passed, 3 preexisting platform/qualification skips, 0 failures. Final process exit 0.
- Completed Python 3.12.13 and 3.14.4 suites: both 19/19 groups passed with exit 0.
- Matrix coverage ran successfully: build/no-solution/classification/runner/trust subprocess cases, restore/build failure cases, cross-target evaluation, and actual SDK failing-project completion. No matrix row lacks executed coverage.
- Parent baseline-byte comparison confirms all existing non-test Github and legacy workflow blobs are unchanged (own builds-ci.yml exempt).
- Concurrent external CiCd/submodule changes are preserved and remain outside this story staging.

### Reviewed delivery and post-review verification

- Applied three medium review patch groups (four medium finding rows, including the duplicate consumer-surface observation); no deferred review-layer findings.
- Final independent library suite: **37 passed**, including 19 pipeline tests and real MTP/VSTest failures with complete project execution.
- Both final Python versions: **19/19 groups passed**; online actionlint/zizmor: **passed**, 0 new findings.
- Final baseline comparison: **66 frozen non-test Github/workflow blobs unchanged**, excluding Builds' own caller; whitespace checks passed.
- Exact delivery message passed pinned commitlint 21.2.4, 0 problems/warnings. All three fixture-commit candidate messages were also validated.
- Implementation commit pushed to Builds main: `d058a5035f2af09ab3045557ac0b22d6f1040561`. Probe files are removed. Committed API checker against `v4.45.1` (`25de7a74d14d099faf7baea5da0cbb0b40264592`): **2479 entries, no removals**.
- [Hosted final source run 42622137434](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42622137434) checks the exact implementation SHA.
- One final local shared-pipeline invocation exited 2: Module 2817 passed, 98 failed, 3 preexisting skips; the failures concern existing temporary Git-workspace/manifest fixtures. A read-only diagnosis reproduced the AttachAdmissionTests class failure both with the new override (12/133 failed) and without it (92/133 failed); exact failing tests passed alone and 100 fresh validation probes passed. No product files were changed. A sequential repeat and clean hosted execution settle the final acceptance separately.

### Post-review verification finding

- verdicts: 1 finding — high 0, medium 1, low 0, false 0, maybe-false 0
- `[medium]` `[defer]` Existing local Module fixture isolation is intermittent — full run and class controls fail without the new override as well; exact tests and fresh validator probes pass. Keep frozen/product files unchanged and record the clean rerun/hosted outcome independently.

### Resumed follow-up review verification

- Hosted push run [42632747702](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42632747702) at the previous follow-up patch `fe02e57c291d28ea4298e7429850cf26208f5fbc`: **success**. It classified Tooling.IntegrationTests as integration and ran Evidence.Tests and Module.Tests.
- Mutation controls on a scratch copy, all against the fast subprocess, classifier and submodule classes. The unmutated control passes, and **10/10 mutants are killed**:
  - unit phase restores again;
  - build phase runs tests;
  - `CI_MODULE_ROOT` default ignored;
  - excluded projects reported as integration;
  - duplicate-path guard removed;
  - escape clauses dropped;
  - repository clause dropped;
  - captured output not printed;
  - old space-splitting parser;
  - exact gitlink path check removed.
- `python3 -m unittest discover -s Github/lib/tests -v`: **47 tests passed**, 0 skipped, including the real SDK, NuGet trust-policy and real-Git classes. The suite passed again after rebasing onto upstream `829e55a1b685908efbdc2756500b148007aae68f`.
- `GH_TOKEN=<current read token> python3 Tools/ci/lint_workflows.py`: **passed**; actionlint and online zizmor, 12 exact frozen composite findings, 0 new findings.
- `uv run --no-cache --locked --script` `Tools/ci/run_python_tests.py` under Python 3.12 and runner Python 3.14.4: both **19/19 groups passed**, exit 0.
- `python3 -I Github/lib/ci_pipeline.py --workspace . --repository Hexalith/Hexalith.Builds`: **exit 0** in 601 s.
  - Release build: 0 warnings, 0 errors.
  - Evidence.Tests: **191 passed**.
  - Module.Tests: **2932 passed, 3 existing skips, 0 failed**.
  - Tooling.IntegrationTests was classified for stage 4 and not executed.
- `git diff --check`: passed. Since `b5eb25c630b58322fa13f1c5e384b9909b66099b`, only this story's files and Builds' own exempt `builds-ci.yml` differ under `Github/` and `.github/workflows`, so the frozen runtime is unchanged.
- The exact commit message passed pinned `@commitlint/cli@21.2.4` with 0 problems and 0 warnings, both before the commit and on the committed message.
- Public API checker on the committed patch against `v4.46.0` (`a8a87160f2708322d5520742b9a0c3f93d23db78`): **2479 entries, no removals**.
- The patch commit was rebased without conflicts onto upstream main `829e55a1b685908efbdc2756500b148007aae68f`, which touches none of this story's files: `9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4`.
- I let upstream's in-progress push CI for `829e55a1` complete ([run 42646725912](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42646725912), success) rather than supersede it. Then I pushed `9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4` to Builds main.
- [Hosted push run 42650358536](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42650358536) at that exact SHA: **success** in every lane and in the aggregate verdict.
  - [Reusable job 129274751930](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42650358536/job/129274751930) ran the reserved stage 1, then checkout, own-code preparation, SDK setup, stage 2 and stage 3, all successful.
  - Release build: 0 warnings, 0 errors.
  - Evidence.Tests: **191 passed**.
  - Module.Tests: **2933 passed, 5 existing environment skips, 0 failed**.
  - Archive and Record CI qualification steps: success.
- [Hosted dispatch run 42650442938](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42650442938) at the same SHA ran **concurrently** with that push run and neither was cancelled, which confirms the event-scoped concurrency group.
  - Result: **success** in every lane, including the reusable build/unit job.
  - "Archive CI qualification evidence" was **skipped**; "Record CI qualification attempt" succeeded.


## Auto Run Result

Status: **done**.

Implemented shared CI through stage 3. Builds now runs it itself.

- **Reusable `ci.yml`:** one job, in this order:
  - a reserved first slot for story 5-1's guard;
  - a non-recursive checkout without credentials;
  - workflow-owned `$/` composites that locate scripts through `GITHUB_ACTION_PATH`;
  - strict configuration preparation and explicit direct submodule initialization;
  - SDK setup from the module's `global.json`;
  - one restore, then a Release package-mode build with analyzers;
  - evaluated AD-13 classification;
  - ordinal unit execution that finishes the failing project and starts no later project.
- **Shared library:** stdlib `Github/lib/ci_pipeline.py` exposes the same flags, preparation, classifier and executor for the future local check.
- **Restore trust:** `NuGet.ci.Config` restricts restore to signed nuget.org packages.
- **Builds' own CI:** its `dotnet` job calls the reusable workflow.
- **Self-reference:** native `$/` was proven by a hosted probe before implementation, so the AD-9 fallback was unnecessary.

Builds commits on main:
- `f2f0a08d8c38d34b390dc937659d2067c8a09cce`: probe.
- `d058a5035f2af09ab3045557ac0b22d6f1040561`: implementation.
- `fe02e57c291d28ea4298e7429850cf26208f5fbc`: first follow-up review patches.
- `9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4`: this pass's review patches.

The CiCd gitlink is staged at `9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4`.

Files changed (Builds-relative, net since `b5eb25c630b58322fa13f1c5e384b9909b66099b`):
- `.github/workflows/ci.yml`: one reusable CI job with validated `solution`/`submodules` outputs and test-only fixture inputs.
- `.github/workflows/builds-ci.yml`: calls the reusable job and adds a dispatch trigger. Dispatch skips G-4 archiving and uses an event-scoped concurrency group.
- `Github/ci-prepare/action.yml`, `Github/ci-build/action.yml`, `Github/ci-unit-tests/action.yml`: workflow-owned entry points for each phase.
- `Github/lib/ci_pipeline.py`: shared flags; direct, NUL-safe submodule preparation; discovery and classification; fail-fast execution with xUnit completion overrides.
- `Github/lib/tests/test_ci_pipeline.py`: 29 behavioral tests: fake SDK subprocess, real Git, real SDK for MTP/VSTest, and NuGet trust policy.
- `NuGet.ci.Config`: nuget.org-only restore with signature verification required.
- `Tools/ci/README.md`: runtime, reuse, trust, submodule-checkout and hosted self-reference guidance.
- A temporary probe workflow and action were created for verification, then deleted.
- CiCd: this story spec and the Builds gitlink.

Review findings, this pass: this resumes the follow-up pass, with 36 findings.

**Patched** (10 entries, 13 rows; high 0, medium 6, low 4):
- (medium) Event-scoped CI concurrency, so a dispatch cannot cancel the push run that release consumes.
- (medium) Phase-sequence test.
- (medium) Workflow environment context test.
- (medium) Excluded-classification test.
- (medium) Duplicate-path guard test.
- (medium) Escaping runner-config tests.
- (low) Discovery-failure output test.
- (low) Spaced submodule names parsed via `git config -z`.
- (low) Exact direct-gitlink path check.
- (low) README note that preparation detaches listed submodules.

**Deferred** (3 new frontmatter items; 2 carried rows not deferred again):
- ChatBot's VSTest/xunit.v3 runner mismatch (low).
- Release evidence also lacks Tooling.IntegrationTests until stage 4 (low).
- Cross-repository `$/` resolution unverified (medium, unverified).

**Rejected** (18):
- `GeneratePackageOnBuild` (false): Commons' current CI builds the same way, and AD-12 omits the flag.
- Warm-cache NuGet policy (low): hosted caches start empty; this concerns the future local check, which is out of scope.
- Response files ignored (false): required by the intent and documented.
- Unrun projects get no warning (low): the classification is logged, no consumer adopts before stage 4, and the Builds case is deferred.
- Stage-1 slot before checkout (false): the intent mandates it, and 5-1 owns the guard's checkout.
- Multi-target runtimes (low): unused case that fails loudly.
- Fork identity (low): fork PRs use the base identity, and a content-based identity would weaken trust.
- Valueless `.gitmodules` key (low, carried).
- BOM in JSON (low, carried).
- MTP zero tests (false): the loud failure matches "no silent test loss".
- Hard-linked configs (low): no module uses hard links; bytes are restored and a guard adds complexity.
- Workflow wiring without tests (false, carried).
- Literal MTP switches (false, carried).
- xUnit-only completion and refusals (low): partly carried; the refusals are loud fail-closed outcomes for unshown states.
- Non-csproj solution members (false): none exist, and AD-13 identifies projects by `.csproj`.
- Case-sensitive names (false): AD-13 uses literal names and ordinal order; no affected project.
- Dispatch path unproven (false): static reading, plus the successful hosted dispatch run 42650442938.
- Late override errors (false): neutral, with no silent loss.

Follow-up review recommendation: **false**. This run resumes the follow-up review of a spec that had reached `done`. The orchestrator re-dispatched it, and the interrupted follow-up session left it `in-review` after committing its patches. The follow-up rule therefore applies, and this pass patched no `high` entry (high 0, medium 6, low 4). Under a literal first-pass reading, the 6 medium patches would recommend another pass. All patched behavior is covered by mutation-checked tests and exact-SHA hosted runs, so no specific unverified risk remains to name.

Verification:
- Library suite: 47 tests passed.
- Mutation controls: 10/10 killed.
- Python 3.12 and 3.14.4: 19/19 groups passed in each.
- Online actionlint and zizmor: 0 new findings.
- Real local Builds pipeline: exit 0; Module 2932 passed, 3 skipped, 0 failed.
- API checker: 2479 entries, no removals.
- Frozen-runtime comparison and whitespace checks: clean.
- Commitlint on the exact message: 0 problems.
- Hosted push and concurrent dispatch runs at `9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4`: success in every lane.

Residual risks, all recorded in frontmatter `deferred`:
- Existing local Module fixtures are intermittent. They passed locally and hosted in this pass.
- Builds' Tooling.IntegrationTests waits for stage 4 (story 2-5), in both CI and release evidence.
- The 30-minute job budget for larger consumers is unmeasured.
- Cross-repository `$/` is unverified until the first module adopts the shared CI.
- ChatBot must select MTP, or use xunit.v3.mtp-off, when it adopts the shared CI.

Delivery: the Builds working tree is clean, and remote main equals `9b9e03f69b77e4a8e64e4185a1df1cb4bc315ba4`. In CiCd, only the story spec and Builds gitlink are staged; the intent forbids superproject commits. The user's concurrent unstaged EventStore and Parties pointer changes are preserved and unstaged.
