---
title: Sample module self-test and the Windows job
type: feature
created: '2026-11-09'
status: done
baseline_revision: b3a5823f0db6324c87ee8a2c4f5f29f5fe0b2e7d
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 5ec1779040606be89306129a7d2b245258c9acd2
review_loop_iteration: 0
followup_review_recommended: false
context:
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/AGENTS.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-llm-instructions.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.AI.Tools/hexalith-git-instructions.md
warnings: [oversized]
deferred:
  - summary: >-
      Shared Linux restore/build passes a config-accepted leading-dash solution path to dotnet as a switch.
    evidence: |-
      ci_config.validate_config path() accepts a solution such as "-consumer.slnx", and ci_pipeline.restore_and_build passes prepared.document["solution"] unchanged to "dotnet restore"/"dotnet build". dotnet parses it as a switch and fails with MSB1001; the recovery pass reproduced this failure on the Windows path. The function predates story 2-6 and is unchanged by it, and shared CI calls it before any Linux prepare, so prepare exposes no new path. The smallest fix is passing str(prepared.root / solution), as the Windows prepare script now does.
    location: >-
      references/Hexalith.Builds/Github/lib/ci_pipeline.py:282
    severity: low
---

<intent-contract>

## Intent

**Problem:** Builds tests its own products through shared CI but has no sample consumer proving module MSBuild imports, hooks, or the Windows job contract. Regressions in those surfaces can pass CI.

**Approach:** Add a real sample module, call reusable CI against it, and run a Windows job using validated outputs through a new prepare composite. Provide the delivered-tree fixture for the later guard and reuse existing Linux setup.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds`. Follow CAP-5/15 and AD-2/9/11/12/13/14/19/20. Preserve all frozen runtime bytes, including initialize-dotnet, initialize-build, create-release, verify, legacy workflows and existing Samples templates; tests are not frozen. New runtime logic goes in new files. Preserve legacy CI lanes and stage-1 slot. Runtime Python is stdlib only, >=3.12. Windows prepare performs checkout, SDK setup, direct submodule initialization, restore and Release package build without Python, module JSON reading, tests/hooks or environment setup. Linux prepare uses the sole loader and existing environment composite after one build. Scripts resolve from GITHUB_ACTION_PATH, never the module gitlink. Checkouts have no persisted credentials or recursive initialization. Root sample composites run existing built product tests, never rebuild/setup/call Builds or write evidence. Only sample config enables them. Parent reviews, commits/pushes Builds and verifies exact-SHA hosted CI; stages story plus gitlink in CiCd without superproject commit.

**Never:** Change frozen runtime, dispatch a release, initialize nested submodules, add module conditions to shared runtime, assert workflow text, duplicate a config reader, implement the later guard/perimeter library, or claim its reserved slot exercises enforcement.

**Hosted CI recovery:** A confirmed GitHub Actions outage that fails a run before any jobs are created leaves hosted acceptance pending. Preserve the delivered implementation and completed review/local verification evidence. After service recovery, resume with verification of the delivered revision: rerun existing CI run `42672353669` at Builds commit `93c9db2e2892be80ab8595052b91cbda5b7d158f`. All required CI jobs, including sample Linux, dependent `windows-latest`, quality and both Python jobs, must execute and pass before completion. The outage alone requires no implementation change or new delivery commit. Actual review or job failures follow normal repair and exact-SHA verification requirements.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Sample | Complete config, central imports, real projects | Build once, units then enabled root hook and integration; Windows-only project runs in its job | Any product failure fails CI |
| Windows prepare | Validated solution, SDK file, direct submodules | Checkout, selective init, exact SDK setup, one restore/build with shared mandatory flags; no environment or Python/JSON | Preserve failure status; no successors |
| Nested paths | Sample prefix, nested solution, spaces | SDK/cwd remain global.json directory; argument arrays preserve paths | Invalid/escaping/non-gitlink inputs fail before product commands |
| Linux prepare | Complete config, optional environment knobs | Same loader/build flags/classifier; one existing environment setup; no tests/hooks | Invalid config/build fails before setup |
| No solution | solution none | No SDK/build/environment/tests/hooks | Linux configuration still validates |
| Regression controls | Failing sample product/hook or prepare command | Failure reaches execution boundary; no successors | Retain nonzero |
| Hosted CI outage | Confirmed service incident; run fails before creating jobs | Preserve delivered work; after recovery retry the existing run at the same SHA and require all hosted acceptance checks | No-job failures supply no passing evidence; hosted acceptance stays pending |

</intent-contract>

## Code Map

Paths are Builds-relative. Read-only exploration completed by subagent and parent.

- `.github/workflows/ci.yml:19,42`, `Github/ci-prepare/action.yml`, `Github/lib/ci_pipeline.py:115,416`: validated prefixed solution/submodules/global-json already exist internally. Add workflow global-json output for exact SDK/cwd; preserve existing solution/submodules outputs. prepare_config rejects test-only inputs outside Builds; expected-source currently validates directory existence only.
- `.github/workflows/builds-ci.yml:24,43`: dotnet reusable call and retained aggregator. Add sample call and dependent two-step Windows job; include both verdicts. Own config enables no sample hooks/jobs.
- New `Samples/Hexalith.Sample/`: own global.json, slnx, root build/package wrappers, README, small product and central-versioned xUnit projects for unit/integration/hook/Windows. Import `../../Hexalith.Build.props`, `../../Props/Directory.Packages.props`, and central package props from product; set ProjectRoot after import. Modules import these same files. Do not import existing Samples templates directly (wrong MSBuildThisFileDirectory) or Builds root repository props. No nested Builds checkout.
- New sample expected-source directory laid out as delivered tree: `rendered/Hexalith.Sample/...` and `rendered/Hexalith.Sample.perimeter.json`; supply owned sample config now, reserve perimeter schema integration for owning story. Config requires exact buildsTag and every knob including submodules. tests.exclude delegates hook/Windows projects to enabled actions rather than running twice.
- New `.github/actions/{after-unit-tests,sample-windows}/action.yml`: execute built sample tests with proper MTP semantics, without generic setup or evidence artifacts.
- New `Github/prepare/action.yml` and scripts: Windows solution/submodules/global-json inputs, Linux test-only module-root input as needed; expressions only through env. Actions expressions decode submodule JSON to LF-delimited paths; Windows splits LF and reads no JSON. Valid config paths forbid LF. global-json defaults to global.json; workflow passes validated SDK path instead of guessing from solution directory.
- `Github/lib/ci_pipeline.py` build_flags/prepare_config/restore_and_build/classified_projects; `Github/ci-environment/action.yml` and ci_environment.py provide Linux reuse. Browser inference includes classified E2E.
- `Github/lib/tests/test_ci_environment.py:33` executable CompositeHarness and test_ci_pipeline.py real SDK fixtures; extend/add prepare tests using actual PowerShell execution and command effects. Harness currently assumes bash/skips external actions; supply controls and distinguish them from hosted evidence.
- `Tools/ci/{run_python_tests,lint_workflows,check_public_api}.py`: locked suite discovers Github/*/tests; extend lint to root sample composites. `Tools/ci/README.md` documents interfaces. package.json/lock pin commitlint 21.2.4.

## Tasks & Acceptance

**Execution:**
- [x] `Samples/Hexalith.Sample/**` — runnable consumer, complete config and expected-tree fixture, central imports and product tests.
- [x] `.github/actions/{after-unit-tests,sample-windows}/action.yml` — run built delegated tests under custom-action contract.
- [x] `Github/prepare/**` and relevant new Linux helper — both OS contracts, shared flags/trust, exact SDK/cwd, selective submodules and failure handling.
- [x] `.github/workflows/{ci,builds-ci}.yml` — SDK output, second call, two-step Windows job on sample outputs and aggregate verdicts; preserve legacy lanes.
- [x] `Github/*/tests`, `Tools/ci/lint_workflows.py`, `Tools/ci/README.md` — behavioral matrix coverage, root-action lint coverage and interfaces.
- [x] `Tools/package-version-audit.json` — refresh only xUnit consumer evidence for all four sample test projects through the existing generator; preserve package selections and other families.
- [x] Parent Git/spec — independent verification/review, frozen comparison, pinned commitlint, commit/push Builds, exact-SHA hosted sample/Windows evidence; stage CiCd story/gitlink.

**Acceptance Criteria:**
- Given Builds main, when builds-ci.yml runs, then shared CI runs against both Builds and sample, and sample Linux plus dependent Windows jobs pass.
- Given a Builds change breaking sample imports, product tests or hooks, when Builds CI runs, then the run fails at that consumer surface.
- Given a module Windows job, when prepare receives shared CI outputs, then its local action observes restored Release outputs from the same SDK/flags without JSON parsing or environment setup.
- Given the implementation baseline, when final delta is inspected, then every frozen runtime blob remains unchanged, including four named composites.
- Given a confirmed hosted outage before job creation, when service recovers, then the existing CI run is retried at the delivered SHA and all required jobs execute and pass; local verification or an empty failed run cannot satisfy hosted acceptance.

## Spec Change Log

- 2026-11-09 — Human chose exact-SHA hosted retry and normal re-arm after GitHub Actions incident `tp8cghg7tlc4` recovered. Preserve delivered work and all hosted acceptance requirements; resume with verification of CI run `42672353669` at Builds commit `93c9db2e2892be80ab8595052b91cbda5b7d158f`.

## Review Triage Log

### 2026-11-09 — Review pass

- verdicts: 17 findings — high 0, medium 2, low 9, false 6, maybe-false 0.
- Four context-free layers ran at parent capability. Three launched first; intent launched immediately when a slot freed, before any triage. Review source diff excluded this narrative; only edge received claims.
- findings, in reporting order:
  - `[medium]` `[patch]` Gap G1: Linux prepare's dependency-initialization call has no nonempty-graph coverage — accepted as pre-verified. Reused HTTP Git fixture through the real prepare_linux.py prepare/build entrypoints; every SDK command asserts recorded direct checkout contents and absence of nested/unrequested content.
  - `[low]` `[reject]` Edge E1: macOS prepare returns success after checkout — true, but the caller contract allows Linux and schema-closed Windows jobs only. Unsupported-runner misuse is unlikely in normal use; adding a platform guard introduces an extra branch without an affected supported caller.
  - `[false]` `[reject]` Intent I1: sample imports differ from a managed module's pinned checkout/templates — the requested consumer surface is the same central MSBuild files, which the sample imports from current Builds to detect regressions. Frozen templates and initialization composites must remain unchanged; this story does not require executing the legacy path.
  - `[false]` `[reject]` Intent I2: Windows job is handwritten rather than rendered — AD-19 expressly calls for one job shaped like a rendered one in Builds' handwritten own workflow. Its two-step shape is implemented; renderer production belongs to its separate story.
  - `[false]` `[reject]` Intent I3: local PowerShell doubles do not prove Windows hosting — the tests explicitly identify this evidence boundary and the real windows-latest job asserts OperatingSystem.IsWindows. Parent verifies that actual job after the authorized commit/push; no local-host equivalence is claimed.
  - `[false]` `[reject]` Intent I4: local tests do not execute GitHub workflow output propagation/scheduling — this correctly describes their layer, not a code discrepancy. The real sample-to-Windows dependency uses validated workflow outputs; exact-SHA hosted execution supplies that final evidence.
  - `[false]` `[reject]` Intent I5: delegated command doubles alone do not demonstrate every product regression — no such exhaustive claim is made. Parent additionally executed real sample normal/failing-product controls through the actual shared job/composites, proving failure propagation at the outer sample surface.
  - `[low]` `[reject]` Intent I6: expected-source has an empty reserved perimeter — true and explicitly documented; current preparation validates only the directory. The later guard/perimeter contract must populate it when enforcement lands. No present enforcement is claimed, and inventing a schema here would be more than a direct correction.
  - `[false]` `[reject]` Intent I7: source diff does not prove commit/push/hosted completion — delivery follows review under explicit user authorization and is recorded with Git/run evidence in Auto Run Result. A unified source diff cannot itself contain that subsequent evidence; this identifies no implementation defect.
  - `[low]` `[reject]` Blind B1: LF joining splits a forged submodule entry into two requests — direct invalid input can do so, but every supported caller consumes the sole loader's validated output; ci_config.py rejects all controls, including LF, before publishing. No validated path can trigger it. An additional pre-join validator would duplicate that input contract for an unlikely manual misuse.
  - `[low]` `[patch]` Blind B2: requested submodules can collide case-insensitively on Windows — parent confirmed Select-Object -Unique accepts A/a. Added its direct CaseInsensitive option for requested destinations; regressions reject collisions and retain case-sensitive exact gitlink-name checks.
  - `[medium]` `[patch]` Blind B3: omitted Windows solution silently skips preparation — changed default from none to empty so existing path validation fails; explicit none still skips. Actual composite regression verifies omission fails before SDK or product work; Linux still loads its own config without a solution input.
  - `[low]` `[reject]` Blind B4: unsupported OS silently succeeds — same verified state as E1. Only Linux/Windows are supported, and no macOS caller exists; a new unsupported-platform branch is unnecessary for everyday use.
  - `[low]` `[reject]` Blind B5: no real Windows submodule checkout is exercised — true evidence limit; the sample's Windows graph is empty. Existing real HTTP Git recorded-revision tests plus actual PowerShell command/argument tests cover the implementation locally, and hosted sample verifies Windows build/action execution. No native-Git defect was demonstrated; another hosted dependency graph would require additional workflow/fixture complexity. Retain this coverage limit rather than claiming it was proven.
  - `[low]` `[patch]` Blind B6: duplicated Windows/Python flags can drift — retained independent mandatory-flag assertions and added comparison of captured Windows restore/build arguments with live ci_pipeline.build_flags, so either direction of drift fails.
  - `[low]` `[patch]` Blind B7: action.yaml escapes expanded action lint coverage — scan both metadata filenames under Github and root .github/actions; executable scanner-input test covers all four root/filename combinations.
  - `[low]` `[patch]` Blind B8: checked-overflow product behavior is untested — sample unit project now asserts integer overflow throws, with two real unit tests passing under shared Release/package flags.
- Grouped surviving repairs: six entries, medium 2 and low 4. Six rows patched, eleven rejected, zero deferred; no intent gap or bad-spec loopback. Each low rejection retains its specific evidence/complexity rationale above.

### 2026-11-10 — Recovery review pass

- verdicts: 14 findings — high 0, medium 2, low 9, false 3, maybe-false 0.
- Four context-free review layers ran at parent capability. Three launched together; intent launched when a slot freed, before any triage. Edge returned no findings. The review diff contained source only; only edge received the story claims.
- findings, in reporting order:
  - `[medium]` `[patch]` Gap G1: Windows initialization lacks a real checkout assertion — accepted as pre-verified. An isolated removal of `--init` survived all five command-double submodule tests. Reuse the actual HTTP Git fixture through PowerShell and assert recorded dependency contents before each product command. This adds executable regression evidence beyond the earlier native-host coverage observation.
  - `[false]` `[reject]` Intent I1: scoped-story reading — the auditor confirms that the sample, current central imports, shared Linux call, and two-step Windows job implement the scoped story; no discrepancy was claimed.
  - `[false]` `[reject]` Intent I2: broader consumer-equivalence reading — carried from prior Intent I1/I2/I6. The story requests current central imports and a job shaped like a rendered one; legacy runtime is frozen, while rendered delivery and perimeter enforcement belong to later stories. The source does not claim broader equivalence.
  - `[false]` `[reject]` Intent I3: source patch cannot establish completed delivery — carried from prior Intent I7. Delivery is verified separately with Git and actual hosted jobs; inability of a source diff to contain future delivery evidence is no implementation defect.
  - `[low]` `[reject]` Intent I4: hosted sample has an empty Windows dependency graph — carried from prior Blind B5. This is an explicit evidence boundary. The actual Windows sample build passes; local real Git coverage is strengthened by G1. Adding a hosted dependency graph would add workflow/fixture complexity without a demonstrated native-host defect.
  - `[low]` `[reject]` Blind B1: case-folded ancestor destinations can overlap on Windows — exact destination collisions are rejected; this additional unusual graph can remain problematic. No managed module uses it, and an additional normalized-ancestry guard adds a branch for an unlikely manual graph. It does not justify expanding this repair.
  - `[medium]` `[patch]` Blind B2: leading-dash solution is parsed as a switch — parent reproduced `dotnet restore -consumer.slnx` failing MSB1001 while its absolute-path control succeeds. Pass the already resolved absolute solution to product commands and add the regression.
  - `[low]` `[reject]` Blind B3: prefixed caller omitting global-json selects root SDK — supported prefixed callers pass the validated workflow output; root default is explicitly documented for root modules. Inferring an alternative module root from a nested solution would conflict with valid root-owned nested solutions, and adding a required-input branch expands the public contract for unsupported misuse.
  - `[low]` `[patch]` Blind B4: delegated harness skips external checkout/setup — reject every unexpected external action in the delegated-action tests so an added setup cannot pass unnoticed.
  - `[low]` `[patch]` Blind B5: Windows no-Python contract lacks an executable sentinel — install failing python/python3 commands in that case; existing script uses neither.
  - `[low]` `[patch]` Blind B6: Linux prefixed-module forwarding lacks coverage — execute actual prepare metadata with conflicting root config, nested module solution, and environment setup, observing SDK/cwd and one restore/build.
  - `[low]` `[patch]` Blind B7: Linux setup failure propagation lacks prepare-level coverage — inject a tool failure and assert original status plus suppressed successor.
  - `[low]` `[patch]` Blind B8: local prerequisites omit PowerShell — document PowerShell 7.6+ on PATH, matching the repository README and tested interpreter.
  - `[low]` `[reject]` Blind B9: native Windows nonempty graph is unobserved — carried from prior Blind B5, with the same explicit coverage boundary and complexity rationale as Intent I4. G1 supplies actual Git checkout evidence through PowerShell locally, without claiming native-host equivalence.
- Grouped repairs: seven entries, medium 2 and low 5. Seven rejected, zero deferred; no intent gap or bad-spec loopback. Patch completion and verification are recorded in Auto Run Result.

### 2026-11-10 — Review pass

- verdicts: 34 findings — high 0, medium 0, low 20, false 12, maybe-false 2
- Follow-up pass on the `done` spec. All four context-free layers ran at parent capability and launched together, before any triage. The review diff covers Builds `5ec1779040606be89306129a7d2b245258c9acd2..73469a690222b804a8676a7e14c6a80f8ab71213`. It excludes the five concurrent DEVELOPMENT.md/Workspace changes and adds the CiCd gitlink. Only edge received the story claims.
- findings, in reporting order:
  - `[false]` `[reject]` Blind B1: the catch block's `exit 1` after `Write-Error` never runs — disproved. Parent ran pwsh 7.6.2 under the runner's `-Command` wrapper: the original message ("Unsafe solution path: x") is printed and the step exits 1. The unreachable `exit 1` changes no observable outcome.
  - `[low]` `[reject]` Blind B2: Windows native-command failures carry no command name, and a missing or path-less `.gitmodules` exits 1 silently — the silent case needs submodules that are not declared in `.gitmodules`. That is unreachable from validated callers, because shared Linux CI already checked those declarations at the same SHA. dotnet and git failures print their own diagnostics. Handling git's "no match" exit code needs a new branch for an unlikely manual misuse.
  - `[maybe-false]` `[reject]` Blind B3: Windows PowerShell may decode UTF-8 `git -z` output for non-ASCII submodule paths with the console code page — unverified locally, because Linux pwsh decodes UTF-8. Settle it by running windows-latest with a non-ASCII direct gitlink. If true, the failure is loud (the path reads as undeclared) and affects only non-ASCII submodule names, which no Hexalith module uses, so it would only be `low`.
  - `[low]` `[reject]` Blind B4: the PowerShell version is not enforced, and the harness passes `shutil.which("pwsh") == None` to subprocess — without pwsh, the suite still fails loudly at that call. The README documents PowerShell 7.6+, and hosted `shell: pwsh` is always 7.4+. Adding `#Requires` or harness guards adds checks for an unlikely setup.
  - `[false]` `[reject]` Blind B5: the sample actions run `dotnet test` without the shared test flags, which could change the evaluated graph — disproved for the only consumer. `UseHexalithProjectReferences` affects only Hexalith package conditions (Props/Directory.Packages.props), and the sample has no Hexalith references. `--no-build`/`--no-restore` use the built Release outputs. Hosted HookTests (1) and WindowsTests (1) passed against those outputs.
  - `[low]` `[reject]` Blind B6: the HookTests and IntegrationTests lanes do not assert their lane, so a classifier or exclude regression would run them twice and stay green — the hosted sample alone would not notice. The pre-existing executed-workflow tests (test_ci_environment.py:552-568) run the real ci.yml with hook excludes, so the same CI run fails. Lane plumbing through environment variables adds complexity for an unlikely regression.
  - `[low]` `[reject]` Blind B7: an omitted `global-json` is undetectable because the sample's pin equals the root pin — carried from the recovery pass, Blind B3. Supported prefixed callers pass the validated output, and the root default is documented. A divergent SDK pin or nearest-global.json inference would add another hosted SDK or a new resolution rule.
  - `[low]` `[reject]` Blind B8: every aggregate job must be wired in three places, and `WINDOWS_RESULT` naming — the pre-existing aggregator pattern is kept, and the two new jobs are wired correctly in all three places. Hosted run 42726180218's aggregate consumed both. Switching to a generic `needs.*` check refactors the retained aggregator. The naming has no named harm.
  - `[low]` `[reject]` Blind B9: the expected-source config copy can drift, the rendered tree omits root actions, and after-unit-tests is hard-wired to the sample — the fixture is explicitly reserved, and story 5-1 owns the delivered-tree comparison that will detect drift. Only sample config may enable root composites (intent), so the hard-wired path matches the contract. A sync test now would pre-empt 5-1's contract.
  - `[low]` `[patch]` Blind B10: Linux prepare had no checkout or SDK-setup failure case — the existing failure test now runs on both Windows and Linux and asserts status 47, the external-action count and no product command. Parent mutation: adding `always()` to the Linux build step survives, because the harness stops at the first failed step and does not evaluate step conditions after a failure. The Windows case has the same limit; residual risk recorded.
  - `[low]` `[reject]` Blind B11: the Windows gitlink test's echoed `submodules` output assertion is tautological — true but harmless. The shared fixture independently asserts the exact registered URL set, the recorded revisions and the absence of nested and unrequested checkouts. Dropping the assertion only for Windows needs a new fixture parameter.
  - `[low]` `[patch]` Blind B12: the README sentence "checks out with persisted credentials and recursive submodules disabled" can be misread — reworded to "without persisting credentials and without recursive submodules". The zizmor paragraph's short soft-wrapped lines render correctly in Markdown, so they are left unchanged.
  - `[low]` `[reject]` Blind B13: the review diff doubles the `references/Hexalith.Builds/` prefix on `+++` headers — true for the parent's staging artifact, not the change under review. The diff was regenerated with git src/dst prefixes. Its base is correctly `implementation_baseline_revision`.
  - `[maybe-false]` `[reject]` Edge E1: Windows console decoding of non-ASCII git output — same claim as Blind B3, with the same settle condition and the same if-true `low` grade.
  - `[low]` `[reject]` Edge E2: a macOS runner succeeds after checkout only — carried from the first pass, Edge E1/Blind B4. No macOS caller exists, and only Linux and schema-closed Windows jobs are supported.
  - `[low]` `[defer]` Edge E3: Linux prepare passes a leading-dash solution to dotnet as a switch — confirmed. ci_config accepts it, and the pre-existing shared `ci_pipeline.restore_and_build` passes the relative path. That function is unchanged by this diff, and shared CI fails first with the same call, so prepare exposes no new path. Deferred as a pre-existing shared-runtime issue.
  - `[low]` `[reject]` Edge E4: pwsh missing produces a TypeError — same claim and rationale as Blind B4.
  - `[low]` `[reject]` Edge E5: the lint guard no longer requires inputs under `Github/` specifically — deleting every Github composite while root actions exist is implausible, and shared CI would fail on the missing composites anyway. A separate guard adds a branch.
  - `[low]` `[reject]` Edge E6: a hook-gate regression leaves the sample job green, because nothing asserts that HookTests ran — the pre-existing harness tests execute the real ci.yml hook gate (test_ci_environment.py:447-568) in the same Builds CI run, so the run fails. A cross-step "ran" signal adds plumbing for an unlikely regression.
  - `[low]` `[patch]` Verification G1: removing the Windows control-character check failed no test — accepted as pre-verified. Added a test asserting `Unsafe solution path` for LF and DEL solutions and `Unsafe submodule path` for a CR submodule, before any SDK, update or product work. Parent deletion mutant: all three subtests fail.
  - `[low]` `[patch]` Verification G2: the Windows duplicate `.gitmodules` path rejection was untested — accepted as pre-verified. Added a test with a second declaration of `references/B`, asserting the message, no update, no product command and one external action. Parent removal mutant fails.
  - `[low]` `[reject]` Verification O1: an LF-containing submodule item is split into two valid paths on Windows — carried from the first pass, Blind B1. Every supported caller uses the sole loader's output, which rejects LF.
  - `[false]` `[reject]` Intent I1: the implemented reading is R1a/R2a/R3a/R4a/R5a/R6b — carried from the recovery pass, Intent I1. The auditor reports this scoped reading and claims no discrepancy.
  - `[false]` `[reject]` Intent I2: the workflow hand-off and global-json output are exercised only by the hosted run and actionlint — carried from the first pass, Intent I4. This is the correct layer under "never assert workflow text", and the hosted run exercised it.
  - `[false]` `[reject]` Intent I3: there is no hosted failure evidence, and no test breaks central imports — carried from the first pass, Intent I5. A broken import fails the sample's required restore/build job. Real failing-product controls were executed.
  - `[low]` `[reject]` Intent I4: native Windows coverage of spaces, leading dashes, junctions and case collisions exists only under Linux pwsh — carried from the recovery pass, Intent I4 and Blind B9. This evidence boundary is explicitly disclosed.
  - `[false]` `[reject]` Intent I5: the sample skips module probing templates, and `$/` prepare and `module-root` exist only in Builds — carried from the first pass, Intent I1/I2, and the recovery pass, Intent I2. The intent asks for current central imports, and rendered delivery is a later story.
  - `[false]` `[reject]` Intent I6: Linux prepare has no hosted caller — the intent requires the Linux prepare contract, not a hosted Linux custom job. Real prepare_linux entrypoint tests execute the loader, the single build and the existing environment composite. The sample config declares only a Windows job.
  - `[false]` `[reject]` Intent I7: the composite runs SDK setup before initialization, unlike the matrix order — the Always clause orders checkout, SDK setup, initialization, then restore/build, which matches the composite. SDK setup reads only the module-owned global.json, which does not depend on submodules.
  - `[false]` `[reject]` Intent I8: acceptance came from a different run and SHA than the named rerun — the recovery clause routes actual job failures to normal repair and exact-SHA verification. The rerun's catalog job really failed, and repair commit `73469a690222b804a8676a7e14c6a80f8ab71213` passed all ten jobs in run 42726180218.
  - `[false]` `[reject]` Intent I9: the audit records revision `93c9db2e2892be80ab8595052b91cbda5b7d158f` but was committed in `73469a690222b804a8676a7e14c6a80f8ab71213` — `git diff` of Samples between the two SHAs is empty, so the bound blobs are exact. The hosted catalog job at the later SHA validated the file.
  - `[false]` `[reject]` Intent I10: the PowerShell validator and hard-coded flags conflict with "never duplicate a config reader" — the script reads no configuration file and only revalidates path inputs. Its flags are drift-guarded against live `build_flags()` (first pass, Blind B6).
  - `[false]` `[reject]` Intent I11: "Release package build" without `dotnet pack` — the shared Linux build is the same Release build in package-reference mode (`UseHexalithProjectReferences=false`). Shared CI has no pack step either.
  - `[low]` `[reject]` Intent I12: the reserved perimeter fixture is a placeholder with no sync check — carried from the first pass, Intent I6. Story 5-1 owns the perimeter schema and enforcement, and no enforcement is claimed.
- Grouped: four patch entries (low 4: B10, B12, G1, G2), one defer entry (low: E3) and 29 rejected. No intent gap or bad-spec loopback. All patches are test or documentation only; no runtime file changed.

## Design Notes

Story 5-1 owns guard/commitlint and commitlint-caller deletion. The fixture enables that later integration. Preserve solution/submodules API; add SDK-path output/input to avoid guessing module root from solution parent. Actions may decode the validated array; Windows scripts parse no JSON. Sample checks current Builds through central imports, avoiding nested submodules and old released props.

## Verification

Implementer runs focused behavioral tests on Python 3.12 and runner Python, real sample shared stages/delegated tests, prepare PowerShell command-effect/failure controls, pinned actionlint/online zizmor, relevant catalog checks. Leave implementation uncommitted for parent review.

Parent repeats focused tests and full locked `Tools/ci/run_python_tests.py` on both interpreters with tool/token prerequisites; runs `python3 Tools/ci/lint_workflows.py` and locked `Tools/ci/check_public_api.py` (Git-object checker repeated after commit). Run real sample restore/build/classified units/integration and built delegated tests, including failing-product mutation control. Inspect complete staged delta/frozen paths against implementation_baseline_revision, whitespace, exact-message pinned commitlint, fetch/divergence, commit/push and hosted exact-SHA CI. Confirm Windows on windows-latest, not inferred from local pwsh.

For the resolved hosted-service pause, retain the recorded implementation/review/local evidence and start by retrying existing CI run `42672353669` at its delivered Builds SHA `93c9db2e2892be80ab8595052b91cbda5b7d158f`. Inspect the actual jobs and require every hosted acceptance check to pass before completing the story. A further infrastructure-only failure leaves hosted verification pending; an actual review or job defect requires the normal repair and verification cycle.

## Implementation Notes

- Implementer delivered 30 Builds-relative files, uncommitted for parent review. New sample has five projects and four classified/delegated test lanes; nested solution and current central imports exercise consumer setup. Linux prepare shares existing loader/build/environment APIs; Windows uses PowerShell and validated solution/submodules/SDK inputs.
- Implementer focused evidence: 15 prepare tests on Python 3.12 and 3.14.4, 20 environment tests, 12 linter-helper tests, real sample shared sequence, real local PowerShell prepare, five-project sample authority check, pinned online lint with zero new findings. Local pwsh is not claimed as Windows-runner evidence.
- Parent inspected the complete staged implementation delta and compared all 59 frozen starting blobs: zero changed. Parent pinned online lint passes with 12 exact frozen findings and zero new findings. Precommit Git-object API check passes 2488 entries against v4.46.0; final committed revision will be checked separately.
- Parent disposable real-sample workflow/composite execution passed normal product through units, root hook and integration. Mutating checked addition to subtraction returned unit exit 2 and suppressed hook/integration. The workspace implementation was never mutated. Evidence log: `/tmp/story-2-6-parent-sample.log`.
- The expected-source directory contains sample config and an explicitly reserved perimeter filename. Story 5-1 owns perimeter schema and guard execution; no enforcement claim is made here.

- Parent full locked Python suites passed **20/20 groups on Python 3.12 and 3.14.4**, including all new prepare cases. Logs: `/tmp/story-2-6-parent-python312.log`, `/tmp/story-2-6-parent-runner.log`. Parent root package-authority validation passed 28 projects. Matrix audit: each row has executed passing behavioral coverage; actual Windows-runner confirmation remains the authorized post-push delivery check.


## Recovery Implementation Notes

- A second concurrent remote change, `da4e896b164f35c0b830a32b975203bb922280f9`, touched only WorkspaceAppHostTests.cs. Parent inspected and fast-forwarded it before the repair commit; all five unrelated concurrent documentation/test changes remain preserved.

- Review repairs completed: all 23 prepare cases pass on Python 3.12.13 and 3.14.4. The parent independently removed Windows `--init` in a disposable action copy; the new real-checkout test failed at the missing dependency contents, killing the mutation. Logs: `/tmp/story-2-6-review-fixes-final-prepare312.log`, `/tmp/story-2-6-review-fixes-final-prepare314.log`, `/tmp/story-2-6-recovery-windows-mutation.log`.

- Retried existing CI run `42672353669`, attempt 3, at delivered Builds commit `93c9db2e2892be80ab8595052b91cbda5b7d158f`. Actual sample Linux and `windows-latest` jobs passed; workflow lint/API and CodeQL passed. Catalog failed on four missing sample xUnit consumer relations. Other unfinished jobs were cancelled by a subsequent push, so this run is not a passing aggregate acceptance claim.
- Normal hosted-job repair: generated `Tools/package-version-audit.json` using `Tools/audit-central-package-versions.ps1 -ChangedFamily xunit -PriorAuditPath Tools/package-version-audit.json`. Its four sample declarations bind committed blobs at `93c9db2e2892be80ab8595052b91cbda5b7d158f`; all package selections and live metadata stayed unchanged, and 155 family decisions were preserved. This Builds-owned audit data is not module runtime.
- Concurrent remote main advanced to `cbdeee4af6307d5f7fb694bc91fddb1a4c1cfaf7`. Parent inspected its tree delta against the delivered story SHA: only DEVELOPMENT.md and three Workspace test files changed. Fast-forwarded without overwriting those changes or altering the audit repair. Exact-SHA hosted verification will target the new delivery commit after repairs.

## Auto Run Result

Status: **done**. Follow-up review pass complete. Four low-severity test/documentation patches are committed and pushed, and exact-SHA hosted acceptance passed. No runtime file changed in this pass.

**Implemented change (story-wide):** a real sample consumer (`Samples/Hexalith.Sample`), root delegated sample actions, a second reusable-CI call, a validated `global-json` workflow output, and a dependent two-step `windows-latest` job. A new `Github/prepare` composite reuses the Linux loader, build and environment APIs, and prepares Windows without Python, module JSON parsing or environment setup. A generated xUnit audit refresh binds the four sample consumers. Delivery commits: `93c9db2e2892be80ab8595052b91cbda5b7d158f` (original), `73469a690222b804a8676a7e14c6a80f8ab71213` (recovery repair), `b99c0d9a5b9b2eeebacc19ea1aebf1b0f656afba` (this follow-up).

**This pass's patches** (all `low`; Builds commit `b99c0d9a5b9b2eeebacc19ea1aebf1b0f656afba`, `test(ci): cover Windows prepare rejection paths`):

- G1 — new `test_windows_control_characters_fail_as_unsafe_before_sdk_or_update` asserts `Unsafe solution path` (LF, DEL) and `Unsafe submodule path` (CR) before any SDK, update or product work.
- G2 — new `test_windows_duplicate_declared_paths_fail_before_sdk_or_update` asserts the `Duplicate paths in root .gitmodules` rejection.
- B10 — `test_external_checkout_and_sdk_failure_prevent_all_product_commands` now runs on both Windows and Linux.
- B12 — the README checkout sentence is reworded to "without persisting credentials and without recursive submodules".

**Deferred (1):** Edge E3. Shared `ci_pipeline.restore_and_build` passes a config-accepted leading-dash solution to dotnet as a switch. The function is pre-existing and unchanged by this story; it is recorded in frontmatter `deferred` as `low`.

**Rejected (29), with recorded reasons** (full evidence in the 2026-11-10 Review pass of the Review Triage Log):

- `false`:
  - B1: verified that pwsh exits 1 and prints the original message.
  - B5: the sample has no Hexalith references, and the hosted delegated tests passed.
  - Intent I1, I2, I3, I5, I6, I7, I8, I9, I10, I11: the descriptive readings match the intent's scope, ordering and recovery clause.
- `maybe-false`, if-true `low`:
  - B3/E1: non-ASCII Windows console decoding. Settle it on windows-latest with a non-ASCII gitlink.
- `low`, carried:
  - B7, E2, O1, I4, I12 keep their earlier rationales.
- `low`, unlikely in everyday use with a fix that adds guards, branches or plumbing:
  - B2: silent exit for undeclared submodules, unreachable from validated callers.
  - B4/E4: missing-pwsh diagnostics.
  - B6/E6: lane and "ran" assertions; the executed-workflow harness already fails CI.
  - B8: the aggregator refactor.
  - B9: fixture drift, owned by story 5-1.
  - B11: a redundant assertion that would need a fixture parameter to drop.
  - E5: the lint guard.
  - B13: a defect in the parent's staging diff, not the change; regenerated.

**Follow-up review recommendation: false.** This is a follow-up pass, and no `high` entry was patched. Patched counts by verdict: high 0, medium 0, low 4. The work has converged.

**Verification performed:**

- Focused `test_ci_prepare`: 25/25 on Python 3.12 and 3.14.
- Mutation controls on disposable copies:
  - Deleting the control-character check fails all three G1 subtests.
  - Removing the duplicate-declaration throw fails G2.
  - Adding `always()` to the Linux build step **survives** B10 (see residual risks).
- Full locked `Tools/ci/run_python_tests.py`: **20/20 groups** on Python 3.12.13 and runner 3.14.4. The only `FAILED` line in the logs is the runner's own expected failing-fixture self-test.
- `python3 Tools/ci/lint_workflows.py` (online zizmor): **12 exact frozen findings, 0 new**.
- Public API: compatible before commit (`73469a690222b804a8676a7e14c6a80f8ab71213`) and after commit (`b99c0d9a5b9b2eeebacc19ea1aebf1b0f656afba`), **2494 entries, no removals** against v4.47.0.
- Commit message:
  - Pinned commitlint **21.2.4** accepts the exact message, and the stored message is byte-identical.
  - `git diff --check` is clean.
  - Fetch before push showed one local commit and zero remote-only commits; the push was a fast-forward.
- Hosted runs at `b99c0d9a5b9b2eeebacc19ea1aebf1b0f656afba`:
  - [CI 42732973691](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42732973691) **success**. All ten jobs passed: sample Linux, native Windows, both Python matrices, workflow lint/public API, package catalog, .NET tests, build/package contracts, CodeQL, and the aggregate Build and test.
  - [Commitlint 42732973739](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42732973739) **success**.
  - Hosted Python logs show 25 prepare cases passing, including both new tests, in each matrix.
- Frozen runtime: this pass changed only `Github/lib/tests/test_ci_prepare.py` and `Tools/ci/README.md`. No runtime, template or workflow file changed.

**Files changed** (Builds-relative, story-wide; excludes the five preserved concurrent DEVELOPMENT.md/Workspace changes):

- `.github/actions/after-unit-tests/action.yml`, `.github/actions/sample-windows/action.yml` — run the already-built delegated sample test projects.
- `.github/workflows/builds-ci.yml` — sample call plus the dependent two-step Windows job; the aggregate includes both verdicts.
- `.github/workflows/ci.yml` — exposes the validated SDK file alongside the solution/submodules outputs.
- `Github/prepare/{action.yml,prepare_linux.py,prepare_windows.ps1}` — cross-platform prepare interface and OS-specific execution.
- `Github/lib/tests/test_ci_environment.py`, `test_ci_pipeline.py`, `test_ci_prepare.py` — executable harness, shared real-Git fixture, and **25** prepare/delegation cases (2 added in this pass, 1 extended).
- `Samples/Hexalith.Sample/**` — config, central imports, SDK pin, nested solution, product, four test projects, README, and the reserved expected-source fixture.
- `Tools/ci/README.md` — interfaces and evidence limits; checkout wording clarified in this pass.
- `Tools/ci/lint_workflows.py`, `Tools/ci/tests/test_lint_workflows.py` — scan both action roots and both metadata filenames.
- `Tools/package-version-audit.json` — generated xUnit refresh for the four sample consumers.

**Residual risks:**

- The composite harness stops at the first failed step and does not evaluate step conditions after a failure. Neither the Windows nor the Linux checkout/SDK failure case can catch an `always()`-style condition regression. Hosted runs exercise only success paths.
- A nonempty native-Windows submodule graph and non-ASCII paths are unobserved on a real Windows host. The hosted sample graph is empty.
- The Linux leading-dash solution issue is deferred, as above.
- CiCd: this record and the updated Builds gitlink (`b99c0d9a5b9b2eeebacc19ea1aebf1b0f656afba`) are staged only. Per the intent, there is no CiCd commit or push and no release dispatch.

Local evidence logs (scratchpad `/tmp/claude-1000/-home-administrator-projects-hexalith-cicd/158d4a46-5a04-45d5-9bbf-c091a5057e15/scratchpad/`): `followup-prepare-3.12.log`, `followup-prepare-3.14.log`, `followup-mutation-ctl.log`, `followup-mutation-dup.log`, `followup-mutation-linux.log`, `followup-suite312.log`, `followup-suiterunner.log`, `followup-lint.log`, `followup-api.log`, `followup-committed-api.log`, `followup-commitlint.log`, `followup-hosted-jobs.json`, `followup-hosted-python-*.log`.
