---
title: "Rename Builds' own workflows"
type: chore
created: '2026-11-09'
status: done
baseline_revision: '8897a7ceae20498fa40d6c1ea50642cef93afb9c'
implementation_baseline_revision: '25de7a74d14d099faf7baea5da0cbb0b40264592'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
implementation_repository: references/Hexalith.Builds
existing_delivery_commit: '25de7a74d14d099faf7baea5da0cbb0b40264592'
existing_delivery_parent: 'c32bd2a14b97c617b220505b498d2effe627a03d'
---

<intent-contract>

## Intent

**Problem:** Builds' own workflow names must leave `ci.yml` and `release.yml` available for the shared pipeline without breaking existing publication or module callers. Story 2-1 has already shipped; folder/id dispatch needs a verified result in this story directory.

**Approach:** Verify the existing rename and its hosted results against AD-19/20, correct any demonstrated story defect within the authorized boundary, and record closure. Reuse the existing pushed commit when no runtime correction is needed.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds`, on `main`, with the CiCd-agent credential. Preserve every module-executed file, directly or transitively, except tests. This includes `Github/initialize-dotnet`, `initialize-build`, `create-release`, `verify`, all legacy composites/scripts and the six frozen reusable workflows. Preserve legacy `production`, `NUGET_USER`, publishing, qualification, CodeQL, commitlint and aggregator behavior at this stage. Validate exact commit messages with pinned commitlint before any new Builds commit; fetch/check divergence before pushing.

**Never:** Rewrite the release pipeline, remove later-story gates, change module-specific workflow identities, rewrite historical evidence, initialize nested submodules, or dispatch publication as a test. Do not create an empty or unrelated Builds commit when this story is already pushed.

</intent-contract>

## Code Map

Paths below are relative to Builds unless prefixed by the spec folder.

- `.github/workflows/builds-ci.yml`, `builds-release.yml`: existing renamed workflows. The release is byte-identical to its former name in the delivery parent; CI drops only dependency review and the deleted self-CI test invocation. The unused maintenance publisher and `Tools/test-self-ci.py` are absent.
- `Tools/verify-g4-release-source.sh:29,45`, `Tools/G4PackageQualification.functions.ps1:45,57,100`, `Tools/archive-g4-qualification-evidence.py:61`: Builds-only workflow identity checks and retained behavioral tests.
- `.github/dependabot.yml`: root-only Actions scan; six frozen workflow exclusions; no `/Github/*` scanning. Keep npm/NuGet schedules.
- `Github/{commitlint,prepare-module-build,publish-containers}/tests` and affected `Tools/test-*` suites: own-workflow text assertions removed; behavioral tests and domain-workflow fixtures retained.
- `Hexalith.Builds.slnx`, `README.md`, three current dispatch references in `docs/`: already repointed. Historical packets and module/Projects identities remain unchanged.
- `_bmad-output/implementation-artifacts/spec-2-1-rename-builds-own-workflows.md` in CiCd: historical implementation, review and local-test evidence; not the write-back target. Story 1 in this spec folder records satisfied preconditions and the new nuget.org policy.
- Hosted push CI `42586447275` and release `42589089105`: both successful at the existing delivery commit, with renamed workflow paths confirmed through the run API. Local HEAD equals fetched `origin/main`.

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/builds-{ci,release}.yml`, removed predecessors, solution/docs and three Builds-only identity tools — verify the rename, removals and identities against the delivery parent; repair only a demonstrated authorized gap.
- [x] `.github/dependabot.yml` and frozen runtime paths — verify exclusion coverage and byte preservation against the delivery parent, including the four expressly named composites.
- [x] Retained identity tests and affected composite test suites — run focused behavioral checks and actionlint; inspect removal of assertions about the renamed workflows.
- [x] Builds Git history and hosted workflow runs — verify the exact commit is pushed, CI is green and publishing still succeeds. Commit/push a concrete correction if needed; otherwise retain the existing delivery commit.
- [x] This story file — record commands, hosted evidence, review and final status for folder/id dispatch.

**Acceptance Criteria:**
- Given the renamed workflow files, when Builds push CI executes, then its retained validation jobs pass without dependency review or references to removed own-workflow files.
- Given successful exact-source CI, when release source/producer verification runs, then the renamed identities pass and mismatched source, branch or attempt is rejected by retained behavioral tests.
- Given story 1's NuGet policy, when the renamed release runs, then legacy production publication succeeds without changing frozen composites.
- Given the AD-20 freeze, when the delivery diff and Dependabot discovery scope are inspected, then frozen runtime bytes are unchanged and frozen workflows/composites receive no dependency updates.
- Given the renamed/deleted workflows, when retained tests are inspected and executed, then own-workflow text assertions are gone and the remaining behavioral cases pass.

## Implementation Notes

- 2026-11-09: Reverified the existing delivery on Builds `main` with `GH_CONFIG_DIR=/home/administrator/.config/gh-cicd-agent`. The frontmatter has no context files. Read the current story, AD-19/20, story 1's precondition evidence and the historical implementation record; the latter was left unchanged.
- Compared delivery `25de7a74d14d099faf7baea5da0cbb0b40264592` with its parent `c32bd2a14b97c617b220505b498d2effe627a03d`. The release is byte-identical under its new filename; CI differs only by removal of the dependency-review job and self-CI test step. Both old filenames, the unused maintenance publisher and `Tools/test-self-ci.py` are absent. Solution, README, all three current dispatch references and the three Builds-only identity tools point to the renamed workflows. Module/Projects identities and historical evidence remain unchanged.
- A Python byte comparison using `git ls-tree -r --name-only`, `git show <revision>:<path>` and working-tree bytes verified all 58 frozen files: every non-test file under `Github/` plus the six frozen reusable workflows. This explicitly includes `Github/{initialize-dotnet,initialize-build,create-release,verify}`. Parsed both Dependabot configurations with PyYAML: the only Actions scan is `/`, the exact six frozen workflow paths are excluded, composite discovery is absent, and npm/NuGet entries and all schedules are unchanged. The comparison manifest is `/tmp/hexalith-story-2-1-closure/freeze-verification.json`.
- Inspected the affected Python/PowerShell test diffs and searched `Tools`, `Github` and `test` with `rg`. Own-workflow text assertions are deleted; remaining renamed-workflow strings are behavioral producer fixtures. Generic module and Projects workflow identities retain their original names.
- All specified local commands exited 0: Bash release-source guard **28 scenarios**; Python evidence archive **12 tests**; PowerShell source-CI verification **79 scenarios**; Python composite suites **5 commitlint**, **15 preparation** and **164 container** tests (**196 Python tests total**); actionlint and delivery-diff whitespace checks. Retained source/branch/run/attempt refusals passed. The container suite emitted Python 3.14 `ResourceWarning` messages for mocked HTTP errors while passing all tests.
- `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' fetch origin main`, followed by `git rev-parse HEAD refs/remotes/origin/main` and `git rev-list --left-right --count HEAD...origin/main`, confirmed both full identifiers equal the existing delivery SHA and divergence is `0 0`. Builds is clean on `main`. No runtime correction, new Builds commit, push or publication dispatch was needed.
- Hosted evidence was read through `gh api repos/Hexalith/Hexalith.Builds/actions/runs/{42586447275,42589089105}` and each run's `/jobs` endpoint. [Push CI 42586447275](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42586447275) is `completed/success`, attempt 1, event `push`, branch `main`, path `.github/workflows/builds-ci.yml`, at the delivery SHA. All six retained jobs passed: .NET tests, build/package contracts, Python contracts, CodeQL, package catalog and aggregate Build and test.
- [Release 42589089105](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42589089105) is `completed/success`, attempt 1, event `workflow_dispatch`, branch `main`, path `.github/workflows/builds-release.yml`, at the same SHA. Both source verification and release jobs passed, including approved-source recheck, NuGet Trusted Publishing, Create Release and evidence retention. `gh run view 42589089105 --repo Hexalith/Hexalith.Builds --log` confirms successful OIDC exchange, source CI run `42586447275`, and HTTP `Created` publication of both `Hexalith.Builds.{Evidence,Module}.Cli` 4.45.1 packages and their symbols. The log is saved at `/tmp/hexalith-story-2-1-closure/release-42589089105.log`.
- `gh api repos/Hexalith/Hexalith.Builds/releases/tags/v4.45.1` confirms [v4.45.1](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v4.45.1) was published by `github-actions[bot]` at `2026-11-09T09:09:57Z`, is neither draft nor prerelease, and includes the package inventory and qualification evidence archive. `gh api repos/Hexalith/Hexalith.Builds/git/ref/tags/v4.45.1` resolves the tag directly to the delivery SHA. Its current `immutable: false` matches this story's legacy stage; enabling immutable releases is a later-story precondition.
- Implementation verification found no demonstrated defect or deferred runtime work. Independent review and final story status remain with the dispatch parent.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass

- verdicts: 2 diagnostic findings — high 0, medium 0, low 2, false 0, maybe-false 0
- All four context-free layers completed. The blind and verification-gap reviewers reported an empty diff. The edge reviewer returned one skipped-analysis diagnostic; the intent auditor described one limitation of the empty review surface. Neither reported a runtime defect.
- findings:
  - `[low]` `[reject]` Edge review skipped because the current-run diff is empty — confirmed: the owning Builds repository has no changes since `implementation_baseline_revision`. There is no new runtime implementation to trace. The existing delivery was independently investigated, its complete 867-line historical diff was read by the parent, and focused tests, hosted runs and frozen blobs were verified. Editing this build's spec or fabricating a Builds change to populate a review diff would not correct a runtime defect.
  - `[low]` `[reject]` Intent alignment cannot establish prior implementation or delivery from an empty diff — true of that review input alone. The auditor explicitly recognizes idempotent completion as a defensible reading. Existing implementation, fetched remote equality, green exact-SHA CI and successful NuGet publication are recorded above and were checked independently. This limitation does not justify a duplicate implementation or empty commit; the account of verification belongs in this build's spec.
- Patches applied: 0. Deferred entries: 0. No intent gap or bad-spec loopback.

## Verification

Run from Builds:

- `bash Tools/test-g4-release-source.sh`
- `python3 Tools/test-archive-g4-qualification-evidence.py`
- `pwsh -NoProfile -File Tools/test-g4-source-ci.ps1`
- `python3 -m unittest discover -s Github/<commitlint|prepare-module-build|publish-containers>/tests -v` (three invocations)
- `actionlint .github/workflows/builds-ci.yml .github/workflows/builds-release.yml`
- `git diff --check`; compare frozen runtime blobs and original release bytes with the delivery parent.
- Read exact-SHA push CI and release paths/conclusions through `gh api`; inspect published `v4.45.1` and release publication evidence.
- Fetch `origin main`, then compare full canonical HEAD and remote identifiers. No new release dispatch is required.

## Auto Run Result

Status: done.

- Story 2-1 was already implemented and pushed in Builds commit `25de7a74d14d099faf7baea5da0cbb0b40264592`. This invocation verified it and recorded the required folder/id result. No Builds source file needed another change or commit.
- Existing delivered files: own CI/release renamed; obsolete publisher and own-workflow text assertions deleted; Builds-only identity tools, behavioral fixtures, solution and current docs repointed; Dependabot restricted to unfrozen discovery. All 58 frozen runtime files, including the four explicitly named composites, remain byte-identical to the delivery parent. Legacy release bytes are unchanged under the new filename.
- File changed in this invocation: this story spec, with verification evidence, task completion and review results. It resides in CiCd, outside the Builds working copy. Historical story records and caller orchestration fields were left unchanged.
- Parent verification repeated every specified focused command: 196 Python tests, 28 Bash scenarios, 79 PowerShell scenarios, actionlint and whitespace checks passed. Parent independently compared frozen blobs, parsed Dependabot and confirmed exact release bytes. The full existing delivery diff was read; the current-run diff is empty.
- Final delivery check: `git push origin main` returned `Everything up-to-date`; full HEAD and `origin/main` are the delivery SHA above. Builds' working copy is clean. No new commit or publication dispatch was created.
- [Push CI](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42586447275) and [release](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42589089105) succeeded at the delivery SHA. Published [v4.45.1](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v4.45.1) resolves to that SHA; retained logs confirm both NuGet packages and symbols were published.
- Review: no patches, no deferred work; two diagnostic limitations rejected for the reasons in the triage log. The four automated review layers saw an empty current-run diff, so they provide no fresh code review of the historical delivery. The two investigation agents and parent inspected that delivery separately.
- Patched entry counts: high 0, medium 0, low 0. Follow-up review recommended: false.
- Residual observations: passing container tests emit Python 3.14 mocked-HTTP cleanup warnings. Immutable releases remain a later-story precondition; this run did not dispatch publication.
