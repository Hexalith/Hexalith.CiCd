---
id: SPEC-cicd
companions:
  - ../../planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md
  - pipeline-stages.md
  - enforcement.md
  - gate-classification.md
  - module-inventory.md
  - baseline-and-targets.md
sources:
  - ../../planning-artifacts/briefs/brief-cicd-2026-11-07/brief.md
  - ../../planning-artifacts/briefs/brief-cicd-2026-11-07/addendum.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Hexalith.CiCd

## Why

**Pain to solve.** Hexalith has 18 interdependent .NET repositories, built by one maintainer working with AI coding agents. Each repository runs its own CI/CD, and agents "fix" red builds by editing workflows, adding gates, or re-pinning Builds. As of 2026-11-07, the main CI workflow fails on 60–100% of runs in 9 of the 15 repositories that have one, and the 90th-percentile run time reaches 65 minutes. Most failures come from CI checking itself, not from the product. Human review can't fix this: there is one human, agents can bypass review, and GitHub Free offers no org-wide enforcement. So this repository (Hexalith.CiCd) becomes the only place CI/CD changes. Hexalith.Builds is the shared runtime, with one CI pipeline and one release pipeline. This repository renders, delivers, enforces, and audits the CI/CD of the other 17 repositories, the modules. Every decision is measured against the same principles: fully automated, fast, simple, pragmatic, and nothing done twice. Three groups are served:
- The maintainer: a red build means the product is broken, and releases are there every morning.
- Module agents: a short pipeline whose failures point at the product.
- Agents in this repository: one view across every module.

The architecture spine (first companion) decides how each capability is built, in AD-1 to AD-21.

## Capabilities

- **CAP-1** Shared CI pipeline
  - **intent:** Every module runs CI through one reusable Builds CI workflow, called from a rendered thin caller.
  - **success:**
    - All 17 modules call the same Builds CI workflow through a rendered `ci.yml` and `.github/hexalith-ci.json`.
    - `domain-ci.yml` (v1) and `domain-ci-v2.yml` (v2) are deleted.
    - Each module's `.github/workflows/` holds only rendered files.
    - Builds runs the same workflow from its own `builds-ci.yml` (CAP-15).
- **CAP-2** Fail-fast CI
  - **intent:** A CI run reports the cheapest, most-likely failure first and stops there.
  - **success:** On a commit with a failing unit-test project, the run fails at that project. No later test project, hook, or integration test runs. Every test inside the failing project still runs. Main CI p90 is ≤ 10 min for a standard module.
- **CAP-3** Local pre-push check
  - **intent:** Agents run the guard, build, and unit-test stages locally with one command before they push.
  - **success:** A single Builds-provided command, run on a commit, gives the same pass or fail as CI stages 1–3 on that commit.
- **CAP-4** Module setup, rendering, and delivery
  - **intent:** A setup file per module in this repository turns on shared stages and enables custom actions. This repository renders every owned file from it and delivers them, so one CI/CD change reaches every module in one pass.
  - **success:**
    - Re-rendering from unchanged setup files produces no diff.
    - Enabling a custom action needs only a setup-file change here.
    - Owned files reach a module only through delivery, as one `build(cicd): …` commit, and only when there is a diff. The restore job (CAP-8) is the one exception.
    - A module that fails its own checks is skipped and reported, and the other modules are still delivered.
    - A repository is onboarded when the maintainer preconditions are met (AD-21) and it is added here as a submodule with its setup file. It then comes under delivery, the guard, the scheduler, and the duplicate scan.
- **CAP-5** Custom actions at hook points
  - **intent:** A module's custom actions in `.github/actions/**` run at named hook points inside the shared CI job and reuse its build and environment. An action that needs another operating system gets its own rendered job.
  - **success:**
    - The only hook points are `after-unit-tests`, `after-integration-tests`, and `nightly`.
    - An enabled hook runs without repeating checkout, restore, build, or environment setup.
    - An action that needs browsers or Dapr runs as a hook in the main job, with that knob turned on.
    - An action declared for Windows runs in its own job on that runner, only after the main job passes.
- **CAP-6** One Builds version
  - **intent:** Every module references one exact Builds release tag, through the callers, `hexalith-ci.json`, and the submodule, moved together by delivery.
  - **success:**
    - No CI run uses two Builds versions.
    - Within one night of a Builds release, all modules reference it, unless it is a new major or is listed in `builds-skip`.
    - A rollback to an older tag is not undone by the next night's bump.
    - A Builds bump commit never triggers a module release.
- **CAP-7** Token-level block
  - **intent:** GitHub rejects module-agent token pushes that touch `.github/workflows/**`, and refuses module-agent workflow dispatches.
  - **success:**
    - A push made with a module-agent token that changes a workflow file is refused.
    - A `workflow_dispatch` made with a module-agent token is refused.
- **CAP-8** Guard
  - **intent:** CI/CD changes made outside this repository fail on PRs and are undone on `main`.
  - **success:**
    - A PR that changes an owned file fails with the diff and the ownership message.
    - A push to `main` that changes an owned file fails with the same message. A restore commit repairs everything except `.github/workflows/**` and starts a new CI run.
    - No such change persists beyond the next CI run. Changes to `.github/workflows/**` don't persist beyond the next delivery, within 1 h.
    - A release run on a commit whose owned files differ from the delivered state fails.
- **CAP-9** Module-specific custom actions
  - **intent:** Custom actions contain no generic building blocks and no code shared with another module. Shared code moves to Builds.
  - **success:**
    - The guard rejects a custom action that uses any deny-listed building block.
    - The nightly scan fails, and names the code, when a fragment appears in the custom actions of two or more modules.
    - Zero such fragments remain.
- **CAP-10** Product-only gates
  - **intent:** Every gate that remains checks the product.
  - **success:**
    - After migration, no job or step checks the CI itself, agent tooling, story evidence, or workflow YAML.
    - No module test asserts workflow YAML.
    - Kept module-specific product checks run as custom actions.
- **CAP-11** Agent rules
  - **intent:** Module agents are told that CI/CD is owned here, and Claude Code agents are denied edits to owned paths.
  - **success:**
    - Every module's `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` carry the delivered CI/CD-ownership block, which the guard checks.
    - AI.Tools' shared guide links to that block and no longer says releases happen on merge.
    - Every `.claude/settings.json` has the deny entries, checked by the guard, and keeps its own allow list.
    - `bmad-testarch-ci` is absent from all modules.
- **CAP-12** Shared release pipeline
  - **intent:** Every module releases through one reusable Builds release workflow. It publishes only a commit whose CI passed and whose owned files match the delivered state, builds packages once with the real version, and completes when rerun.
  - **success:**
    - On a red `main`, the release fails with "main is red, nothing released".
    - With no releasable commit, it succeeds with "nothing to release".
    - With `HEXALITH_RELEASE_PUBLISH_ENABLED` set to `false`, it succeeds with "publishing disabled". Any value other than `true` or `false` fails it.
    - Rerunning a failed release finishes it without duplicates. A version is never republished from different content.
    - The tag is created last, and the release never commits to `main`.
    - The four release patterns and the three `recover-partial-release.yml` copies are gone.
- **CAP-13** Nightly release scheduler
  - **intent:** Each night, this repository starts the release workflow of Builds and of every adopted module, all at once, and reports whether they all succeeded.
  - **success:**
    - Each morning, every module with a green `main`, releasable commits, and no blocking finding (CAP-14) has a new release, made by a run in its own Actions tab.
    - A failure shows as a failed run in that repository and turns this repository's nightly run red.
    - `HEXALITH_RELEASE_PUBLISH_ENABLED` set to `false` stops that module from publishing.
- **CAP-14** Nightly security analysis
  - **intent:** CodeQL analyzes each module once a night, inside its release run, and never on a push or PR. High and critical findings block that night's release.
  - **success:**
    - No module runs CodeQL on a push or PR.
    - An open high or critical CodeQL alert from the release analysis blocks that module's release.
    - A package with a high or critical vulnerability (NU1903, NU1904) blocks the release.
    - The guard rejects module MSBuild files that waive NU1903 or NU1904.
- **CAP-15** Builds tests its pipeline by running it
  - **intent:** Builds' own CI lints its workflows and runs the reusable CI against Builds itself and its sample module. Builds releases through the same nightly run as the modules.
  - **success:**
    - A Builds change that breaks the sample module's CI fails Builds' CI.
    - No Builds test asserts workflow text.
    - After the first release, which is dispatched by hand, Builds releases at most once a night.
- **CAP-16** Migration
  - **intent:** All 17 modules move onto the shared pipelines, simplest first, and the legacy CI/CD in Builds is deleted.
  - **success:**
    - Each module is adopted by one delivery commit. It is done when its CI is green and its next nightly release succeeds or reports nothing to release.
    - All 17 modules are managed from here.
    - The following are deleted:
      - `domain-ci.yml`, `domain-ci-v2.yml`, and `domain-release.yml`
      - the `prepare-domain-release` composite
      - the legacy actions
      - `eventstore-maintenance-publisher.yml`

## Constraints

- Builds holds all shared CI/CD code and is changed only by agents in this repository. Builds is the runtime, not a managed module: it has no setup file and is never rendered, delivered to, guarded, bumped, or duplicate-scanned (AD-19).
- Everything a module's CI and release depend on is committed in the module. Builds contains no module names or module-specific conditions (AD-1, AD-2).
- Delivery is the only writer of owned files into modules. The guard's restore job is the one exception (AD-6, AD-8).
- In each module, this repository owns (AD-4):
  - `.github/workflows/`, as a whole directory: an unrendered file is drift
  - `.github/hexalith-ci.json` and `.github/dependabot.yml`
  - the Builds submodule pointer and its `.gitmodules` section
  - the deny entries in `.claude/settings.json`
  - the marked CI/CD block in `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`

  The following must be absent from modules: semantic-release and commitlint config and dependencies, the commitlint `.husky` hook line, and `bmad-testarch-ci`. That tooling exists only in Builds. `.github/actions/**` is module-owned: it is linted and scanned, but never restored.
- GitHub Free has no org rulesets, no required workflows, and no push rulesets that restrict workflow paths on public repos. Enforcement is token scoping, the guard, and hourly delivery, nothing else (`enforcement.md`). Org-wide agent Apps (`claude`, `chatgpt-codex-connector`, `cursor`) keep Workflows write access that the org can't remove. Only the guard and delivery cover them.
- Agents push directly to `main`. Human review, CODEOWNERS, and required-status-check rulesets are not enforcement layers. The design assumes careless agents, not malicious ones.
- `uses:` can't be an expression, so Builds calls custom actions only at fixed, named hook points.
- CI is one job, run in a fixed order: cheapest and most likely to fail first (`pipeline-stages.md`). A separate job is allowed only for one of these (AD-8, AD-12):
  - an action that needs another operating system, run after the main job
  - the restore job, which isolates write permission from custom actions
- Nothing runs twice:
  - CodeQL runs only in the nightly release.
  - CI checks out only the Builds submodule.
  - Commitlint runs inside the guard.
  - The release trusts green CI for the same SHA, skips the tests, and packs once.
  - Dependency review is dropped. NuGet audit runs only in the release build.
  - Known exception: a module with a `nightly` hook compiles twice a night.
- A gate exists only if it checks the product: compilation, tests, security and dependency scans, commit format, or package publishing (`gate-classification.md`).
- Builds is referenced by exact release tag, and its releases are immutable. The callers, `hexalith-ci.json`, and the submodule move together. The automatic bump runs at most once a night, within the current major, and skips the tags in `builds-skip`. Adopting a new major or rolling back is a commit in this repository, at any time (AD-10).
- Builds releases on every commit type except `docs`, `test`, and `style`, so a central package change in `Props/Directory.Packages.props` always reaches the modules through the next bump.
- Each module releases independently. Dependency bumps are non-releasable `build(deps)` commits that ship with the module's next releasable change. A `fix(deps)` commit forces a release. There is no release cascade.
- A release starts only from `workflow_dispatch`, never on a push. The scheduler dispatches it nightly, and module agents can't. Every release step is safe to rerun. `HEXALITH_RELEASE_PUBLISH_ENABLED` stays as a per-repository kill switch, and its value must be exactly `true` or `false`.
- Every Builds file that modules call today stays unchanged until the last caller has moved. New pipeline code goes in new files (AD-20).
- Claude Code deny rules go in each module's `.claude/settings.json`, never in machine-wide managed settings: a deny there would also block agents here from editing Builds.
- Credentials (AD-7):
  - One org GitHub App delivers and dispatches. Its private key exists only as a secret in this repository. Each job mints a short-lived token scoped to what it needs.
  - Nothing unattended uses a personal token.
  - Module agents use a token that has no Workflows, Administration, Actions, Variables, or Secrets write access.
  - Agents in this repository use a second token, scoped to Builds and this repository, in interactive sessions only.
  - Agent sessions never run with the maintainer's personal `gh` login, which has the `workflow` scope.
- Actions limits: reusable workflows nest at most 10 levels deep, with at most 50 called workflows per run. From 2026-12-02, `pull_request_target` is blocked by default on public repos.

## Non-goals

- The other public Hexalith repositories (about 43); only the 18 in `references/` are managed.
- Upgrading the GitHub plan to get org-wide rulesets or required workflows.
- Changes to product test suites, beyond how CI runs them.
- Unifying .NET SDK versions: each module's `global.json` stays module-owned, and CI/CD never rewrites it.
- Deployment to runtime environments.
- Defending against malicious agents.
- Enforcement through human review, CODEOWNERS, or required-status-check rulesets.
- Reordering stages automatically from run history; a pre-push hook.
- A same-night release cascade in dependency order.
- Repacking CI-built packages for the release.
- Central failure detail: the nightly run reports only pass or fail with run links, and the details stay in each module's own run.

## Success signal

- Each morning, every module with releasable changes and no blocking finding has a new release, started by the scheduler with nobody touching it. A red CI run in any module means the product is broken. Any CI/CD edit made outside this repository has already been undone, and an edit to a workflow file is undone within an hour.
- The numeric targets, such as main CI success ≥ 95% in every repository and p90 ≤ 10 min, are in `baseline-and-targets.md`, measured the same way as the 2026-11-07 baseline.

## Assumptions

- The rules of the current `ci-cd-standards.md` that this spec doesn't override carry over: SDK from `global.json`, explicit secrets (never `secrets: inherit`), and tests per project. The standard is rewritten to match this spec, with exact tags, nightly dispatch, and one CI and one release pattern.
- For the p90 target, a "standard module" is one whose CI runs only shared stages and fixed-point hooks, with no job on another runner.
- Success rates are re-measured with the baseline method (`baseline-and-targets.md`).
- Builds' thin `codeql.yml`, `commitlint.yml`, and `dependency-review.yml` are legacy files, deleted with the rest in the final cleanup. The spine freezes them as legacy, CodeQL moves into the release, and commitlint moves into the guard.
