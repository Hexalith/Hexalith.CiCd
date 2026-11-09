---
title: "Story 2-1: Rename Builds' own workflows"
type: 'chore'
created: '2026-11-09'
status: 'done'
route: 'dispatch'
baseline_commit: '27145e52ffab5623198ba5efdab5cdb71aa42d28'
baseline_repository: 'references/Hexalith.Builds'
superproject_baseline_commit: 'f46c04c9af26bbd91e082bee5daded285fd684e2'
integration_base_commit: 'c32bd2a14b97c617b220505b498d2effe627a03d'
delivery_commit: '25de7a74d14d099faf7baea5da0cbb0b40264592'
ci_run_id: '42586447275'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Builds' own workflow names occupy the names needed by the shared pipeline. Renaming them without updating release identities would block publishing.

**Approach:** Implement stories.yaml 2-1 under AD-19/20: rename the workflows, repoint Builds-only consumers, remove their YAML-asserting tests, and exclude frozen files from Dependabot.

## Boundaries & Constraints

**Always:** Preserve legacy publishing, `NUGET_USER`, `production`, triggers, permissions and qualification behavior. Use only the CiCd-agent credential. Commit and push in Builds, then inspect its CI. Preserve the user's existing `module-inventory.md` edit. Story 1 records the required settings and the maintainer-attested new NuGet policy.

**Never:** Change module-executed files, including `Github/create-release`, `initialize-dotnet`, `initialize-build`, `verify` and frozen reusable workflows. Remove CodeQL, commitlint-caller, G-4/G-6 qualification or the aggregator early. Rewrite historical evidence or module/Projects workflow identities. Dispatch a publishing release as a test.

</frozen-after-approval>

## Code Map

Paths below are relative to `references/Hexalith.Builds/`, clean on `main` at `27145e52ffab5623198ba5efdab5cdb71aa42d28` during investigation.

- `.github/workflows/ci.yml`, `build-release.yml`: own CI and manual release. Release calls `Tools/verify-g4-release-source.sh` twice and delegates publication through unchanged composites.
- `Tools/G4PackageQualification.functions.ps1`: `Get-VerifiedSourceCiRun` and `Assert-CurrentReleaseSource` enforce workflow identity. `Tools/archive-g4-qualification-evidence.py` validates producer identities by kind.
- `Tools/g6_current.py`, G-6 policies and runtime baselines concern Projects workspaces; retain their `ci.yml` references. Generic provenance, split-publication and module fixtures also retain theirs.
- `.github/dependabot.yml`: root workflows plus `/Github/*` composite scanning; all current composites are frozen. Story 1 evidence is in the superproject's `_bmad-output/specs/spec-cicd/stories/1-maintainer-preconditions-and-remaining-checks.md`.

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/ci.yml` → `builds-ci.yml`; `build-release.yml` → `builds-release.yml`. Remove CI's `dependency-review` job and self-CI test step; delete `.github/workflows/eventstore-maintenance-publisher.yml` and `Tools/test-self-ci.py`.
- [x] `Tools/verify-g4-release-source.sh`, `Tools/G4PackageQualification.functions.ps1`, `Tools/archive-g4-qualification-evidence.py` — replace only Builds' old workflow identities with the new names, retaining all source/run/attempt checks.
- [x] `Hexalith.Builds.slnx`, `README.md` — repoint own workflow entries and release-policy documentation.
- [x] `.github/dependabot.yml` — scan GitHub Actions at `/` only; exclude `.github/workflows/{domain-ci,domain-ci-v2,domain-release,codeql,commitlint,dependency-review}.yml`. Remove `/Github/*` scanning; explain the temporary freeze. Keep npm/NuGet and scheduling unchanged.
- [x] `Github/commitlint/tests/test_commitlint_workflow.py`, `Github/prepare-module-build/tests/test_prepare_module_build.py`, `Github/publish-containers/tests/test_publish_script_contract.py` — delete methods asserting the renamed workflows, removing unused path constants. Preserve behavioral and frozen-workflow tests.
- [x] `Tools/test-archive-g4-qualification-evidence.py` — delete `test_workflows_retain_carriers_and_release_publishes_it`; repoint retained producer fixtures.
- [x] `Tools/test-central-package-version-validator.ps1`, `Tools/test-dapr-package-version-validator.ps1`, `Tools/test-package-version-audit-generator.ps1`, `Tools/test-package-version-audit-validator.ps1`, `Tools/test-domain-workflow-test-platforms.ps1`, `Tools/test-g4-release-contract.ps1` — remove self-workflow reads/assertions and unused variables; retain behavioral tests and domain-workflow assertions.
- [x] `Tools/test-g4-release-source.sh`, `Tools/test-g4-source-ci.ps1`, `Tools/test-g4-tool-package-contract-gate.ps1`, `Tools/test-publish-g4-tool-packages.ps1`, `Tools/test-g4-release-contract.ps1` — repoint Builds-specific behavioral fixtures.

**Acceptance Criteria:**
- Given the renamed workflows, when push CI runs, then retained validation jobs succeed without missing-file failures or the dependency-review call.
- Given successful exact-SHA push CI from `builds-ci.yml`, when release source and producer identity validation run, then the new names pass; mismatched SHA, branch or attempt still fails.
- Given the new release filename, when its publishing configuration is inspected, then the existing NuGet login and production publishing contract remain compatible with story 1's policy.
- Given the migration freeze, when the diff and Dependabot configuration are inspected, then module-executed bytes are unchanged and frozen workflows/composites cannot receive version updates.
- Given renamed/deleted own workflows, when retained tests run, then none asserts their YAML text and all behavioral fixtures use the correct identities.

## Implementation Notes

- 2026-11-09: Approved for implementation. Loaded the latest saved spec, including its trailing separators. The inventory edit was committed externally in the superproject and is preserved. The implementation baseline is Builds' HEAD; the superproject revision is recorded separately.
- Execution order: implement and verify locally first. Workflow step 3 prohibits remote operations; the required commit, push and remote CI verification follow review. The implementation handoff must leave those delivery actions for the parent session.
- Local implementation complete: two renames, 13 CI lines removed, unused maintenance publisher and self-CI test deleted, Builds-only identities and fixtures repointed, and specified YAML assertions removed. The release workflow and 58 frozen runtime/workflow files remain byte-identical to the baseline.
- All required local checks exited 0: 196 Python tests, 28 Bash scenarios, and 11 PowerShell invocations (including audit validator 101, audit generator 113, source CI 79, artifact validator 71, Dapr 35, central validator 16, and domain contracts 410/253 assertions). Actionlint, parsed YAML inspection, diff whitespace and pinned commitlint also passed. Full commands/results are saved in `/tmp/hexalith-story-2-1-validation/summary.json`.
- Parent audit: staged the complete Builds diff against `baseline_commit`, including new workflow files, saved it to `/tmp/hexalith-story-2-1-3a234pz2.diff`, and read all 828 lines. Every implementation task is complete. Remote push-CI acceptance remains a delivery check after review; live package publication is intentionally outside this story's verification.
- Review patch: corrected three current/pending dispatch references in `docs/module-cli-configuration-key-compatibility.md`, `docs/module-cli-configuration-key-release-plan.md`, and `docs/producer-qualification-evidence-4383-handoff.md`. Read the final three-line diff and checked its links and whitespace. No executable code changed after full local verification, so no broad test repetition was needed.
- Delivery integration: remote main had advanced by 11 independent commits to `c32bd2a14b97c617b220505b498d2effe627a03d`. Rebased the local change without conflicts; `git range-diff` confirmed an identical patch. Frozen files are unchanged relative to that integration parent. Re-ran the overlapping domain-contract suites (legacy 410, v2 301 assertions), actionlint and diff checks; all passed.
- The exact candidate commit message passed pinned commitlint. Pushed `25de7a74d14d099faf7baea5da0cbb0b40264592` to Builds `main` using only the CiCd-agent credential. Hosted CI run `42586447275` is pending; its result is required before closure. No release was dispatched.
- Closure: [hosted push CI](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42586447275) completed successfully for `25de7a74d14d099faf7baea5da0cbb0b40264592`, with `.github/workflows/builds-ci.yml` confirmed by the run API. All six jobs passed: .NET tests, build/package contracts, Python contracts, CodeQL, package catalog and aggregate Build and test. Separate [commitlint](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42586447204) also passed. Every acceptance criterion is satisfied; BH-8's pending hosted evidence is fulfilled. No work was deferred.

## Spec Change Log

## Review Triage Log

Review pass 1: all three context-free layers completed; edge-case hunter returned no findings. Each finding is assessed separately below before grouping.

| Finding | Verdict | Evidence and disposition |
| --- | --- | --- |
| BH-1: stale release dispatch instructions in three docs | medium | Verified current/future dispatch instructions in `docs/module-cli-configuration-key-compatibility.md:135`, `docs/module-cli-configuration-key-release-plan.md:9`, and `docs/producer-qualification-evidence-4383-handoff.md:114` still name the deleted file. Patch their current references, preserving historical observations. |
| BH-2: removed create-release composite text checks | low | The deleted mixed test checked the frozen composite's Node/install/audit source text. That composite is byte-identical to baseline; this story intentionally removes own-workflow YAML tests. Reject: introducing separate source-inspection tests adds machinery for an unchanged frozen implementation, with no present behavioral defect. |
| BH-3: removed release evidence asset configuration assertion | low | The mixed test's static `package.json` asset assertion is removed. Package configuration and actual asset paths are unchanged, and retained archive/publisher tests pass. Reject: restoring a test that mirrors static configuration adds coverage for a hypothetical future edit rather than correcting this change. |
| BH-4: removed aggregator execution matrix | low | The deleted self-CI suite also executed 625 status combinations. The aggregator itself is unchanged; its deletion is scheduled later under AD-20. Reject: recreating workflow-extraction test machinery checks CI itself and adds complexity without a current aggregate defect. |
| BH-5: removed NuGet wiring source assertions | low | The removed opening assertion inspected workflow text. The renamed release is byte-identical, including OIDC/login/key wiring, and the new NuGet policy is story-1-attested. Reject: a replacement source-shape test conflicts with the intended test cleanup and addresses only future wiring edits. |
| BH-6: no explicit old-filename negative fixture | low | Existing source-CI tests reject mutated run paths, forged workflow proofs and foreign release refs; production comparisons require the new exact names and the carrier regex requires the selected new filename. Reject redundant cases for a specific alternative string: no old-name acceptance was demonstrated. |
| BH-7: no Dependabot boundary verification | false | Executed parsed-YAML inspection checked exactly the six exclusions, root-only Actions discovery, and unchanged npm/NuGet schedules; summary.json records these checks. Inspection was semantic, beyond YAML syntax. A new config-mirroring regression test is unnecessary. |
| BH-8: no hosted producer acceptance evidence | low | True at pre-delivery review: changes are not committed/pushed yet. The approved verification explicitly schedules exact-SHA hosted CI after review. This is a pending delivery task, not missing implementation; record its result before closing. |
| VG-1: executable status-aggregation coverage removed | low | Trusting the review's verified whole-tree search: the deleted matrix has no surviving equivalent, and it would detect a hypothetical omitted Python condition. Current Bash still requires all four results, with no changed condition. Reject for the same unchanged-CI/test-machinery rationale as BH-4; no product failure is introduced. |

Survivor: BH-1 only, routed to a trivial documentation patch. No intent gap, bad spec or deferred issue remains from this pass.

## Verification

Run from Builds. Install pinned Node dependencies with `npm ci --ignore-scripts` if needed.

- `bash Tools/test-g4-release-source.sh` and `python3 Tools/test-archive-g4-qualification-evidence.py` — retained identity/error cases pass.
- Run every touched PowerShell suite above with `pwsh -NoProfile -File`, plus `Tools/test-g4-tool-package-artifact-validator.ps1`; run domain contracts once normally and once with `-Contract v2` — all pass.
- Run `python3 -m unittest discover -s` on each of `Github/{commitlint,prepare-module-build,publish-containers}/tests`, with `-v` — all pass.
- `actionlint .github/workflows/builds-ci.yml .github/workflows/builds-release.yml`; `git diff --check` — clean.
- Review YAML with a parser and the diff for expected jobs, publishing settings and freeze exclusions; use GitHub's [documented exclude-paths semantics](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#exclude-paths). Compare frozen paths against the implementation baseline.
- Validate the exact commit message with pinned commitlint before committing. Fetch and inspect divergence before pushing; use the CiCd-agent credential. Monitor the pushed SHA's CI and record results and any independent failures.
