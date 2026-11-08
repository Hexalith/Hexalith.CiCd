---
title: "Product Brief: Hexalith.CiCd"
status: final
created: 2026-11-07
updated: 2026-11-07
---

# Product Brief: Hexalith.CiCd

## Executive Summary

Hexalith is an ecosystem of 18 interdependent .NET repositories built by one maintainer working with AI coding agents. Each repository runs its own CI/CD, and those pipelines have drifted apart. When an agent hits a red build, it tends to "fix" the build by editing the workflow, adding a gate, or pinning a different version of the shared code. The result is CI that fails most of the time and takes too long. The main CI workflow fails on 60–100% of runs in nine repositories, and some runs take more than an hour.

Hexalith.CiCd makes this repository the only place where CI/CD is changed. `Hexalith.Builds` holds one CI pipeline and one release pipeline, both configurable per module. Each module keeps a generated thin caller and the custom actions that are truly specific to it. This repository generates, enforces, and audits everything else.

The target is CI/CD that is fully automated, fast, and simple:

- The checks most likely to fail run first.
- Nothing runs twice.
- Every night, each module with releasable changes is released without anyone touching it.

## The Problem

These figures were measured on 2026-11-07 from the last 200 runs of each repository. Details are in addendum sections A–C.

- **It breaks.** Overall, 24% of workflow runs fail. The main CI workflow fails on 60–100% of runs in 9 of the 15 repositories that have one. ChatBot and Works had no successful CI run in the sample.
- **It's slow.** Median CI time per repository ranges from 7 to 39 minutes, and the 90th percentile reaches 65 minutes. Commons runs CI in less than 2 minutes, so the toolchain isn't the bottleneck. Real test failures are reported at the end of the run instead of stopping it.
- **Most failures come from CI checking itself.** Few sampled failures are compile or test failures. Most come from setup steps, or from repo-local policy and "evidence" gates that agents added while working on stories.
- **Work is repeated.**
  - CodeQL reanalyzes the whole codebase on every push and every PR, taking up to 24 minutes per run.
  - Every CI job clones all of a module's submodules, which can be up to 17 other Hexalith repositories.
  - One repository runs its full release on every push.
  - Every run loads two versions of Builds that never match: the submodule and the workflow pin.
- **The shared layer exists but doesn't hold.** Builds already hosts reusable workflows and a standards document. Yet repositories pin Builds anywhere from 7 to 946 commits behind, use two CI flavors and four release patterns, and carry up to 13 workflow files and 3,116 lines of local YAML. The agent instruction files never say not to edit workflows, and they contradict the release standard.

Human review can't fix this. There is only one human contributor, and agents can bypass review. GitHub Free also offers no org-wide required workflows and no path-protection rules for public repositories, so enforcement has to be built.

## The Solution

Three layers, each with one job:

| Layer | Owns | Changed by |
|---|---|---|
| `Hexalith.Builds` | All CI/CD code: one reusable CI workflow, one reusable release workflow, shared actions, and build props | This repository only |
| Each module | Custom actions for module-specific operations, in `.github/actions/**`. The module runs its CI/CD through a generated thin caller. | The module changes its custom actions; this repository changes everything else |
| `Hexalith.CiCd` (this repository) | A setup file for each module, the CI/CD files generated from it, enforcement, the cross-module audit, and the nightly release scheduler | The maintainer and agents working here |

In each module, this repository owns `.github/workflows/**`, `dependabot.yml`, the commitlint and semantic-release config, the Builds submodule pointer, and the deny entries in `.claude/settings.json`. Custom actions in `.github/actions/**` stay module-owned.

Addendum section F gives the options behind each choice below, with their pros and cons.

### Pipeline rules

- **Fail fast (F8).** CI runs as one job, in this order:
  1. The guard and the commit-format check
  2. A build with warnings as errors
  3. Unit tests, stopping at the first failing project
  4. Custom hooks and integration tests

  The order follows the rule "cheapest and most likely to fail first." Before they push, agents run the first three stages locally with one command.
- **Nothing twice (F9).** CodeQL runs only at night. CI clones only the submodules the build needs. The release trusts the green CI run for the same commit and builds packages once, with the real version.
- **Fully automated nightly release (F10).** Every night, a scheduler in this repository starts each module's own release. A module is released only if its `main` branch is green and the module has releasable changes. A failed release is fixed by running it again. This replaces releases dispatched by hand.
- **No release cascade (F11).** Each module releases only for its own changes. Dependency bumps are `build(deps)` commits that ship with the module's next releasable change. To force a release (for example, for a security fix), an agent commits the bump as `fix(deps)`.

### What this repository does

1. **Keeps every module on one Builds version (F3).** Modules reference Builds by an exact release tag. This repository moves the workflow reference and the Builds submodule together, at most once a night, as a `build:` commit that doesn't trigger a release.
2. **Undoes CI/CD changes made anywhere else (F4).** Agents still push directly to `main`. Agent tokens get no `workflow` permission, so GitHub rejects their workflow edits. A guard job, owned by Builds, runs first in every CI run:
   - On a PR that changes owned files, it fails.
   - On `main`, it restores the owned files and fails the run, telling the agent to fix the product rather than the pipeline.

   The design assumes careless agents, not malicious ones.
3. **Runs module-specific work through setup files (F2).** A module's setup file lives in this repository. It turns on shared stages and enables the module's custom actions. Custom actions run at fixed hook points inside the shared CI job and reuse its build. A separate job is used only when an action needs a different runner, such as a Windows runner or one with a browser.
4. **Keeps custom actions module-specific (F5).** The guard rejects custom actions that use generic building blocks, such as checkout or SDK setup. A nightly scan here flags code found in two or more modules, and an agent working here then moves that code into Builds.
5. **Removes gates that don't check the product (F6).** A gate stays only if it checks the product: compilation, tests, security and dependency scans, commit format, or package publishing.
   - **Kept:** product checks specific to one module, such as Folders' end-to-end and accessibility gates or EventStore's payload-protection tests. They become custom actions.
   - **Deleted:** gates that check the CI itself, agent tooling, story evidence, or workflow YAML, plus the module tests that assert workflow YAML.
6. **Tells agents the rules (F7).**
   - The shared instructions from `Hexalith.AI.Tools` say that CI/CD is owned here, and no longer contradict the release standard.
   - Each module's `.claude/settings.json` carries deny rules for the owned paths.
   - The `bmad-testarch-ci` skill is removed from the modules.

## Who This Serves

- **The maintainer**, the only human contributor. Success means CI/CD stops being something to watch: a red build means the product is broken, and new releases are there every morning.
- **AI coding agents working in modules**, the main source of drift today. Success means a short, fast pipeline whose failures point at the product, and a clear message that CI/CD changes belong in this repository.
- **Agents working in this repository**, the only ones allowed to change CI/CD. Success means they see every module at once, so a CI/CD change, or a move of shared code into Builds, reaches every module in one pass.

## Success Criteria

| Measure | Today (2026-11-07) | Target |
|---|---|---|
| Main CI success rate | 0–40% in 9 repos | ≥ 95% in every repo |
| Main CI duration, 90th percentile, standard module | up to 65 min | ≤ 10 min |
| CI and release patterns in use | 2 CI flavors, 4 release patterns | 1 of each |
| Builds version spread across modules | 7–946 commits behind | all on the same version within one night |
| Local workflow YAML in modules | 218–3,116 lines | only the generated caller |
| Custom-action code common to two or more modules | not measured | none |
| CI/CD changes from outside this repository that persist | frequent: 84 workflow commits in Tenants since 2026-10-01 | none; the next CI run undoes each one |
| Releases | dispatched by hand | every module with releasable changes is released overnight by its own run; a failure shows as a failed run in that repository |

## Scope

**In the first version:**

- The 18 repositories referenced in `references/`. A repository comes under management when it is added here as a submodule.
- A simpler Builds (F1):
  - A new minimal CI workflow, modeled on Commons' 2-minute CI, replaces `domain-ci` v1 and v2.
  - One release workflow replaces the four release patterns.
  - The legacy actions are deleted.
- In this repository: per-module setup files, caller generation, the guard, the nightly duplicate scan, the nightly release scheduler, and the agent guardrails.
- Migration of all 18 repositories, simplest first, including removal of gates with no value and of tests that assert workflow YAML.

**Out:**

- The other public Hexalith repositories (about 43).
- Upgrading the GitHub plan to get org-wide rulesets.
- Changes to product test suites, beyond how CI runs them.
- Deployment to runtime environments.

## Open Questions

1. **What counts as a releasable change in Builds itself?** Hexalith package versions are pinned centrally in Builds' props, and modules receive a change there only after Builds releases it. Architecture has to define which Builds changes are releasable.
2. **Which facts need verifying before architecture?** Addendum section F lists them:
   - Who receives failure notifications for scheduled runs and for dispatched runs
   - The Free plan's limit on concurrent jobs
   - Which submodules a package-mode build actually reads
   - Whether NuGet audit already fails the build on vulnerable packages
