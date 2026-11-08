---
title: "Addendum: Hexalith CI/CD brief — evidence baseline and options"
created: 2026-11-07
updated: 2026-11-07
---

# Addendum: Hexalith CI/CD brief

This addendum gives supporting detail for the PRD and architecture work that follows; the brief only summarizes it. "This repo" means Hexalith.CiCd throughout. Its sections:

- **A–C:** measured evidence (run history, where CI fails, drift audit).
- **D:** platform constraints.
- **E:** comparable models.
- **F:** the options for each decision and a recommendation, ending with a list of items to verify.

## Recommendations at a glance

| Part | Recommendation | Section |
|---|---|---|
| Builds | One new minimal CI workflow, modeled on Commons, and one release workflow. Delete the v1 and v2 CI workflows and the legacy actions. Builds' own CI runs the pipeline against `Samples/`, and Builds releases at most once a night. | F1 |
| Setup and custom actions | Each module's setup file lives in this repo. Custom actions stay in the module and run at fixed hook points. An extra job only when another runner is needed. | F2 |
| Builds version | Exact tag. Submodule and workflow move together, at most once a night, as a `build:` commit. | F3 |
| Blocking | Agent tokens without the Workflows permission, plus a guard job that fails PRs touching CI/CD files and restores those files on `main`. No required-check rulesets and no review. An optional ruleset blocks only force-pushes to `main` and deletion of `main`. | F4 |
| Common code | Deny-list lint plus a nightly duplicate scan. Agents in this repo move shared code into Builds. | F5 |
| Gates | One-time pass that keeps only gates that check the product. Module-specific product checks become custom actions. | F6 |
| Agent rules | Shared instruction text plus deny entries in `.claude/settings.json`. Remove `bmad-testarch-ci` from modules. | F7 |
| Fail fast | One job: guard, then build, then unit tests (stop at the first failure), then integration. One command runs the guard, build, and unit tests locally. | F8 |
| Nothing twice | CodeQL only at night. Clone only the submodules the build needs. The release trusts green CI and builds once. Commitlint moves into the guard. Dependency review is dropped if NuGet audit covers it. | F9 |
| Nightly release | One scheduler in this repo starts each module's own release. Reruns are safe. `HEXALITH_RELEASE_PUBLISH_ENABLED` stays as a per-repo kill switch. | F10 |
| Propagation | Independent releases. Dependency bumps don't release unless committed as `fix(deps)`. | F11 |

## A. Run-history baseline (measured 2026-11-07)

**Source:** `gh run list` for each repo, last 200 runs. For most repos that covers only 2–5 days, which shows how much CI activity there is. Failure rate counts completed runs and excludes skipped and canceled ones.

**Overall:** 2,939 completed runs, 700 failed (**24%**).

Main CI workflow, per repo:

| Repo | CI runs | CI fail % | CI median (min) | CI p90 (min) | Notes |
|---|---|---|---|---|---|
| ChatBot | 88 | 100% | 18.8 | 36.5 | `release` also runs on every push: 88 runs, 100% failed |
| Works | 56 | 100% | 6.7 | 21.5 | |
| Conversations | 46 | 91% | 7.9 | 24.6 | CodeQL median 21 min |
| Parties | 39 | 90% | 14.4 | 25.2 | |
| Folders | 26 | 88% | 15.6 | 29.3 | `contract-spine-gates` fails 74%; CodeQL median 24 min |
| Projects | 66 | 82% | 12.7 | 38.7 | |
| Agents | 57 | 70% | 11.6 | 23.4 | CodeQL median 16 min |
| McpCli | 26 | 65% | 39.3 | 65.0 | |
| Timesheets | 47 | 60% | 36.2 | 48.4 | |
| Tenants | 15 | 27% | 32.4 | 35.5 | |
| Memories | 35 | 26% | 22.2 | 55.4 | `Release` fails 29% |
| FrontComposer | 27 | 19% | 8.5 | 24.8 | `Quality` fails 55%, median 27 min |
| PolymorphicSerializations | 53 | 19% | 1.1 | 1.6 | `Commitlint` fails 91% |
| Builds | 52 | 17% | 21.3 | 30.0 | `Release` fails 30%, median 38 min |
| Commons | 79 | 13% | 1.6 | 1.8 | The fastest; shows that a 2-minute CI is achievable |

Three referenced repos have no row:
- **AI.Tools:** no workflow runs.
- **EventStore:** its 200-run sample covers only 2 days, and its CI is not among its five most frequent workflows. Its overall failure rate is 8%.
- **Platform:** no workflow named CI. Its "Platform tuple CI preflight" fails 22% of the time, with a median run time of 11.4 minutes.

## B. Where CI fails

**Source:** the last ~6 failed CI, Quality and Release runs per repo.

Failures fall into three groups. Most of the time CI fails on checks of the CI itself, not because the product fails to compile.

1. **Bespoke policy, evidence and governance gates.** These are the most common, and they are local to each repo.
   - Agents: "Require the pinned Builds workflow source", "Enforce package test floors"
   - Projects: "Validate workflow policy / production-authority scheduling guard" (6 of 6 sampled failures)
   - Works: "Lint release tooling", "Preserve source identity checks", "Platform R1–R11 parity and rollback" (6 of 6 each)
   - Parties: "Finalize exact CI owner", "Require the owning integration job to pass"
   - ChatBot: "story-evidence-integrity", "release evidence gate"
   - FrontComposer: "Gate 2b: Infrastructure governance", "Coverage Summary", "Quarantine Summary"
   - Builds: "Require every validation job to pass"
2. **Setup and import preparation.**
   - "Prepare package build imports" (Conversations, 4 jobs)
   - "Prepare package dependencies" (Works)
   - "Initialize root-declared submodules" (Parties)
   - "Prepare Aspire tier" / "Run Aspire hook" (McpCli)
   - "Prepare verified published Builds artifacts" (Works)
3. **Real test failures**, reported late. "Fail on blocking test failures" appears in Agents, Conversations, Folders, McpCli, Parties, Tenants, Timesheets, and Works. Every test runs to completion and a final aggregate step fails, which is the opposite of fail-fast.

## C. Drift audit of the `references/` checkouts (2026-11-07)

### Current standard (`ci-cd-standards.md`)

This is the baseline the drift is measured against. It says:
- Shared logic lives in Builds.
- Routine Builds refs use `@main`; release is pinned to a reviewed SHA.
- SDK comes from `global.json`; Release builds use `-warnaserror`.
- Tests run per project.
- Releases are `workflow_dispatch` only, behind a publish-gate variable.
- Secrets are explicit, never `secrets: inherit`.
- Every module has CodeQL, dependency review, commitlint, and Dependabot.

### Hexalith.Builds

- **Reusable workflows:**
  - `domain-ci.yml` (v1): 1,507 lines, legacy, many caller hooks.
  - `domain-ci-v2.yml` (v2): 762 lines, strict, manifest-driven. Only EventStore and Parties use it.
  - `domain-release.yml`: 2,058 lines.
  - Thin gates: `codeql`, `dependency-review`, `commitlint`.
- **Composite actions** under `Github/`: `initialize-build`, `initialize-dotnet`, `dapr-init`, `prepare-domain-release`, `prepare-module-build`, `create-release`, `publish-containers`, `governed-provenance`, plus legacy ones.
- **Leftover one-off in the central repo:** `eventstore-maintenance-publisher.yml` triggers on branch `fix/eventstore-maintenance-publication`.
- **Release cadence:** semantic-release, exact tags only. Latest is v4.44.11. There were 44 tags in the last month, and there is no floating major tag. No consumer references a tag; they use `@main` or raw SHAs.

### Consumers

#### Versioning (see F3)

- **Builds pins** range from 7 to 946 commits behind HEAD. Ten repos pin `domain-ci` to a SHA, although the standard says `@main`.
- **Two Builds versions in every run.** Every `Directory.Packages.props` imports from the `references/Hexalith.Builds` submodule, and in every repo that submodule's commit differs from the workflow pin.
- **Stale submodule pointers.** Timesheets and Platform run workflows on GitHub, but their checkouts in this repo have none.

#### Release and baseline (see F1, F9, F10)

- **Four different release patterns:**
  - reusable `domain-release` (2 repos)
  - the `prepare-domain-release` composite (6 repos)
  - a bespoke `.hexalith/builds-execution` checkout (4 repos)
  - fully bespoke (ChatBot, McpCli)
- **Missing baseline:**
  - ChatBot has no CodeQL, dependency review, commitlint, or Dependabot, and releases on every push.
  - McpCli has no CodeQL, dependency review, or Dependabot.
  - Projects has no Dependabot.
- **Workflow linting:** only Works runs `actionlint`.

#### Setup and toolchain (see F1, F8)

- **Workflow volume:** 2 to 13 workflow files per repo, 218 to 3,116 lines in total.
- **.NET setup drift:**
  - FrontComposer hard-codes the SDK version in 10 places.
  - `global.json` SDK pins are split between 10.0.401, .402, and .403.
- **Other drift:**
  - Dapr runtime pins vary from 1.18.2 to 1.18.7, even within one repo.
  - NuGet authentication is split between an API key and OIDC.
  - Variable names differ from repo to repo.

#### Governance and agents (see F6, F7)

- **Bespoke governance workflows and jobs.** Many trace back to BMAD stories:
  - FrontComposer: flaky-test governance (901 lines of Python), quarantine nightly run, IDE parity ("Story 9-3")
  - Parties: `rc-gate`, startup diagnostics
  - Tenants: `story-guards`, which tests BMAD tooling in CI
  - Folders: drift and policy lanes
  - McpCli: `agent-instructions-sync`
  - Story-named jobs inside `ci.yml` in Memories, Parties, Projects, and ChatBot
- **Agent churn:**
  - Agent-written "fix CI" specs: FrontComposer 26, EventStore 25, Memories 8, Parties 7, Projects 4.
  - Workflow commits since 2026-10-01: Tenants 84, EventStore 76, Parties 60.
- **Lock-in to the current YAML.** Repo tests assert the content of workflow YAML: Folders 27 files, EventStore 13, FrontComposer 13, Tenants 12, Parties 11, Memories 11. Any central change will break them.
- **Agent instructions:**
  - In each repo, `AGENTS.md`, `CLAUDE.md`, and `copilot-instructions.md` are identical, and all derive from `Hexalith.AI.Tools/hexalith-llm-instructions.md`.
  - None of them says "don't edit workflows" or "use Builds".
  - They contradict the standard: they say releases happen on merge to `main`, but the standard says manual dispatch only.
  - The `bmad-testarch-ci` skill ("Scaffold CI/CD quality pipeline") is installed in 14 repos.

#### Technical surface (see F2)

- **Non-.NET code:**
  - Python: Memories 122 files, Tenants 71.
  - PowerShell, plus Node for commitlint and semantic-release.
- **Infrastructure dependencies:**
  - Dapr 1.18 and Aspire.
  - A Postgres image pinned by digest.
  - The Zot registry (`registry.hexalith.com`).
  - Azure secrets (EventStore).
  - A Windows runner (Conversations).

## D. Platform constraints

- The Hexalith org is on **GitHub Free**, with 2 members and 61 public plus 6 private non-archived repos. Only 18 are referenced here.
- **Not available on Free:**
  - org rulesets
  - "Require workflows to pass" (needs Team or above)
  - push rulesets that restrict `.github/workflows/**` (Team plan and private repos only, so never on public repos)
- **Available on Free:**
  - repo-level rulesets on public repos
  - CODEOWNERS with required code-owner review
  - the required-reviewer rule (GA since 2026-02; *verify* plan limits)
  - token scoping (agent tokens without the Workflows permission)
  - Claude Code `permissions.deny` on `Edit(/.github/workflows/**)`, which managed settings can enforce
  - Copilot coding agent's default "Approve and run workflows" gate
- **Actions platform facts:**
  - **Reusable workflow limits:** 10 levels of nesting, 50 called workflows per run.
  - **Immutable releases:** GA, so `Builds@vX.Y.Z` tags can be trusted.
  - **Workflow lockfiles:** preview, Enterprise only.
  - **`pull_request_target`:** blocked by default on public repos from 2026-12-02.

## E. Comparable models (landscape research)

- **Grafana `shared-workflows` (see F3):** a tag per workflow, and tags are immutable. Publishing a release doesn't move consumers to it, so bots bump their pins. Org-wide checks live in a separate repo.
- **Apache `infrastructure-actions` (see F4, F5):**
  - an allowlist of approved actions kept as code;
  - an allowlist-check job in every repo;
  - an audit script that scans all repos for baseline tooling and opens PRs where it is missing.

  This is the closest model to "enforce on top of Builds".
- **Octopus (2026-10, see F3):** consolidated 20 copied workflows and chose `@main`, accepting a large blast radius. Its lesson is to decide early how callers reference the shared workflows, how changes are tested, and how versions are tracked.
- **Tooling:**
  - `zizmor`: pinning and forbidden-uses audits.
  - `actionlint`.
  - OpenSSF Scorecard and Allstar.
  - `github/safe-settings`: rulesets and settings as code.
  - `actions-template-sync`.
  - Renovate's `workflow` dependency type.

## F. Solution analysis and recommendations

This section takes each part of the solution in turn. For each it gives how it works, the options, their pros and cons, and a recommendation. Each choice is tested against your principles: fully automated, fast, simple, pragmatic, and nothing done twice.

Items marked *verify* rest on GitHub behavior recalled from the docs, or on code not yet read in full. Check them before building on them. The section ends with a list of all of them.

### F1. One simple Builds

**How it works.** Builds keeps:
- one reusable CI workflow;
- one reusable release workflow;
- the CodeQL workflow;
- a few composite actions.

Everything else goes:
- `domain-ci.yml` (1,507 lines) and `domain-ci-v2.yml` (762 lines) are replaced by the one CI workflow.
- `domain-release.yml` (2,058 lines), the `prepare-domain-release` composite, and the four release patterns are replaced by the one release workflow.
- The legacy actions are deleted: `verify`, `unit-tests`, `package-release`, `publish-azure-container-app`, and `publish-container-to-registry`.
- The one-off `eventstore-maintenance-publisher.yml` is deleted.

**Options for the new CI workflow:**

| Option | Pros | Cons |
|---|---|---|
| Keep v2 and extend it | Already strict; used by 2 repos | Rejects caller hooks by design; needs the module CLI tool pin and registry secrets everywhere |
| Keep v1 and trim it | Covers every current case | 1,507 lines of hooks; trimming a big file rarely ends small |
| Write a new minimal workflow, modeled on Commons' 1.6-minute CI | Small enough to read in one sitting; contains only what the 18 repos need | Edge cases (Dapr, Aspire, Windows) have to be solved again, as shared optional stages or custom actions |

**Recommendation:** write the new minimal workflow. Migrate the simplest repos first (Commons, PolymorphicSerializations). Delete v1 and v2 once their last caller has moved.

**Builds' own CI.** For Builds, the pipeline *is* the product, so testing it counts as a product check. The way to test it is to run it:
- lint the workflows with `actionlint` and `zizmor`;
- run the reusable CI against the sample module in `Samples/`.

Tests that assert workflow text are dropped. Builds releases through the same nightly pipeline as the modules, so it releases at most once a night; by contrast, it released 44 times last month.

### F2. Module setup and custom actions

**Constraint.** In GitHub Actions, `uses:` cannot be an expression. So a reusable workflow in Builds can't call a module action whose name is known only at run time.

**Options for running custom actions:**

| Option | How | Pros | Cons |
|---|---|---|---|
| Fixed hook points | When the module's setup file enables a hook, Builds' CI job calls `./.github/actions/<hook>` at a named point, such as after the build or after unit tests | Runs in the same job and reuses the build, so nothing is done twice | Only at predefined points; same runner as the main job |
| Extra job in the generated caller workflow | This repo renders an extra job into the module's caller, which calls the local action | Any runner or OS (Windows, browsers, Dapr topology) | Repeats checkout, restore and build in a separate job |
| Script hooks through `run:` | Builds runs a script whose path comes from the setup file | Fully dynamic | Not actions; little structure; easily grows into a second pipeline |

**Recommendation:** use fixed hook points by default. Use an extra job only when the action needs a different runner.

**Where the setup files live:**

| Option | Pros | Cons |
|---|---|---|
| In each module | Sits next to the code | It counts as CI/CD, so module agents can't change it and it would still be edited from here; 18 separate places to look |
| In this repo, one file per module | One place; the generator reads it directly; with every module side by side, common code is easy to spot | Enabling a new custom action needs a change here |

**Recommendation:** keep the setup files in this repo. Requiring a change here to enable a custom action is useful: that change is where the common-code check (F5) and the gate rule (F6) get applied.

**Change to what this repo owns.** Module agents must still be able to edit their custom actions, so `.github/actions/**` stays module-owned. The guard never restores that folder but does lint it (F4), and the duplicate scan audits it (F5). The CI/CD files this repo owns in each module become:
- `.github/workflows/**`, which holds the generated caller;
- `dependabot.yml`;
- the commitlint and semantic-release config;
- the Builds submodule pointer;
- the deny entries in `.claude/settings.json` (see F7).

### F3. One Builds version per run

Today every run mixes two Builds versions that never match: the submodule that `Directory.Packages.props` imports, and the workflow pin.

| Option | Pros | Cons |
|---|---|---|
| `@main` everywhere | No bump work | One bad Builds commit breaks all 18 repos at once. Runs can't be reproduced. The submodule still sits at a fixed commit, so the mismatch stays. |
| Exact release tag, with the submodule at the same tag | One version per run. Readable and reproducible. Tags can be made immutable now that GitHub's immutable releases are GA. | One bump commit per module each time Builds releases |
| Full commit SHA | Same as tags | Unreadable. For Builds references, the current standard says `@main` for routine use and a reviewed SHA for releases (section C). The recommendation below replaces both. |

**Recommendation:** use the exact tag. This repo moves the workflow reference and the submodule together:
- in one commit per module;
- at most once a night;
- as a `build:` commit, a commit type that semantic-release doesn't treat as releasable, so a Builds bump never triggers a module release.

Rolling back is the same bump in the other direction.

### F4. Blocking CI/CD changes made elsewhere

Already decided: agents keep pushing directly to `main`, and human review is not an enforcement layer.

**Layer 1: token scoping.**

*How it works.* Agents use a fine-grained token for the module repos as their git and `gh` credential. The token has neither the Workflows nor the Administration permission, so GitHub rejects any push that touches `.github/workflows/**`. Agents working in this repo do need to change Builds' workflows. They use a second token, scoped to Builds and this repo only.

- **Pros:** a hard block enforced by GitHub itself, with no code to maintain.
- **Cons:**
  - It takes discipline: agent sessions must not run with your personal `gh` login, which has the `workflow` scope.
  - It doesn't cover CI/CD files outside `.github/workflows/`.

**Layer 2: the guard job.** Builds owns this job. It runs first in every CI run and takes seconds.

*How it works:*
1. It downloads the module's expected CI/CD files (listed in F2) from this repo, where they are rendered and committed. This repo is public, so no token is needed. The source of truth sits outside the module, where module agents can't change it.
2. It compares them with the module's files, and lints the module's custom actions (F5).
3. On a PR, it fails with the diff and the message "CI/CD is owned by Hexalith.CiCd. Fix the product code, not the pipeline."
4. On a push to `main`, it restores the expected files in one commit, then fails the run with the same message.

It restores the files rather than running `git revert`, because the agent's commit usually mixes product changes with the CI/CD edit.

- **Pros:** it repairs itself, and the agent gets a clear and immediate signal.
- **Cons:**
  - The restore commit can race the agent's next push. The agent then has to pull and rebase as usual.
  - Commits pushed with `GITHUB_TOKEN` don't start a new CI run, so the restored files are only tested on the next push.

**Recommendation:** layers 1 and 2, nothing else.

**Not used:**
- Rulesets with required status checks, because they block direct pushes.
- CODEOWNERS and required review, because agents can bypass them.

An optional ruleset can block force-pushes to `main` and deletion of `main`. It costs nothing and does no harm.

### F5. Keeping custom actions module-specific

| Option | How | Pros | Cons |
|---|---|---|---|
| Deny-list lint in the guard | Custom actions must not contain generic building blocks: `actions/checkout`, `actions/setup-dotnet`, `actions/cache`, `dapr init`, a solution-wide `dotnet build` or `dotnet test`, `nuget push`, registry login, semantic-release | Deterministic and instant. Catches the most common duplication, which is setup. | A list to maintain; occasional false positives |
| Cross-module duplicate scan, run nightly in this repo | A copy-paste detector such as `jscpd` (YAML, shell, PowerShell, Python) scans every module's custom actions and the scripts they call. A fragment found in two or more modules fails this repo's nightly run and names the code to move. | Deterministic and cheap. Covers all modules at once, which only this repo can do. | Misses the same logic written differently; the threshold needs tuning |
| Agent review in this repo | An agent reads all custom actions and proposes what to move | Catches the same logic written differently | Not deterministic, costs tokens, and is no guarantee |

**Recommendation:** the guarantee comes from the deny-list lint plus the nightly duplicate scan. Use agent review only when a new custom action is enabled, or when the scan flags something.

**Moving shared code ("hoisting")** is an ordinary change made by an agent in this repo:
1. Move the code into Builds as a shared stage or action.
2. Switch the modules over to it.
3. Delete the copies.

### F6. Removing gates that don't check the product

**How it works.** A one-time pass goes through the inventory in section C and classifies each job and step with one rule:
- **Keep** it if it checks the product.
- **Delete** it if it checks the CI itself, agent tooling, story evidence, or workflow YAML text.

Product checks specific to one module are kept and become custom actions. Repo tests that assert workflow YAML are deleted.

- **Pros:** removes most of the failures sampled in section B, and a large share of run time.
- **Cons:** a deleted gate may once have caught something real. All product tests stay, so the risk is small.

**Recommendation:** run the one-time pass with this rule, and turn module-specific product checks into custom actions.

Gates can't come back:
- module agents can't add workflows (F4);
- custom actions can only be enabled from this repo (F2);
- the rule is written into this repo's `AGENTS.md`.

**First classification** (*verify* during migration):

*Keep, as custom actions:*
- Folders' accessibility and end-to-end gates, and FrontComposer's browser regression tests.
- Folders' contract-spine gates, which check API contracts and generated artifacts.
- Folders' provider smoke test (`nightly-drift`), moved into the nightly run.
- EventStore's payload-protection tests and Dapr broker tests.

*Delete:*
- FrontComposer's flaky-test governance, quarantine nightly run, and IDE parity check.
- Parties' `rc-gate` and startup diagnostics.
- Tenants' `story-guards`, and the story- and BMAD-named jobs in `ci.yml` (Memories, Parties, Projects, ChatBot).
- McpCli's `agent-instructions-sync`. It is agent tooling and belongs in AI.Tools' own sync.
- The three `recover-partial-release.yml` copies, replaced by a release that is safe to rerun (F10).
- The workflow-policy, pinned-source and "evidence" gates (Agents, Projects, Works, ChatBot, Builds).
- The repo tests that assert workflow YAML (counts in section C).

### F7. Telling agents the rules

**Layer 1: instructions.** One short section goes into `Hexalith.AI.Tools/hexalith-llm-instructions.md`, which feeds every module's `AGENTS.md`, `CLAUDE.md`, and Copilot file. It says:
- CI/CD is owned by Hexalith.CiCd.
- Don't edit workflows, CI config, or the Builds pointer.
- When CI fails, fix the product.
- When CI itself is wrong, report it rather than work around it.

The same change:
- fixes the line that says releases happen on merge;
- removes the `bmad-testarch-ci` skill ("Scaffold CI/CD quality pipeline") from the 14 modules that have it.

**Layer 2: Claude Code deny rules.** This repo makes sure each module's `.claude/settings.json` includes `permissions.deny` entries for the CI/CD paths this repo owns, and the guard checks that they are there. The file exists in 15 modules, in 12 different versions. So the entries are merged in, and each module keeps its own allow list.

Don't put these rules in machine-wide managed settings. A deny rule there would also stop agents in this repo from editing Builds' workflows, and no allow rule can override a deny.

- **Pros:** cheap. Most agents comply, so the guard rarely has to step in.
- **Cons:** for agents other than Claude Code, these are only instructions. Real enforcement still comes from F4's two layers.

**Recommendation:** both layers.

### F8. Fail fast

**How it works.** By default the Builds CI is one job, run in this order:
1. Guard and commit-format check, which take seconds.
2. Restore and a Release build with `-warnaserror`, including analyzers, which take minutes.
3. Unit tests, project by project, stopping at the first failing project. All tests within that project still run, so you see all of its failures.
4. Hooks and integration tests (Dapr, Aspire), once unit tests pass.

| Choice | Recommendation | Why |
|---|---|---|
| Fixed order, or reordered automatically from history | Fixed order, by the rule "cheapest and most likely to fail first". Review it with the run-history script from section A whenever a stage is added. | Automatic reordering is over-engineering |
| Stop at the first failure, or collect every failure | Stop | Agents fix and push again. The cost is extra rounds when several projects fail. |
| One job, or many parallel jobs | One job. Split off a job only for a slow, independent suite, and only when that measurably shortens the run. | Each extra job repeats checkout, restore and build, and counts against the org-wide limit on concurrent jobs (*verify* the Free plan's limit) |
| How agents check locally | One command from Builds runs stages 1–3, and agents are told to run it before they push. No mandatory pre-push hook. | Hooks slow every push and can be skipped with `--no-verify` |

**Recommendation:** one job in the fixed order above, stop at the first failing project, and give agents one command to run stages 1–3 locally.

### F9. Nothing done twice

**CodeQL.**
- *Today:* it runs on every push, every PR, and once a week, in 12 of the checked-out repos, and takes 6–24 minutes per run. It already uses `build-mode: none`, so the waste is repeated analysis, not a second build.
- *Recommendation:* run it only in the nightly run, before the release.
- *Trade-off:* this removes a quarter to a third of the runs in most repos. A security finding can take up to 24 hours to show up, but it still appears before the release.

**Submodule cloning.**
- *Today:* `initialize-build` runs `git -c submodule.recurse=false submodule update --init --depth 1`, which initializes every submodule the module declares. Modules declare 2–17 Hexalith submodules, so each CI job clones up to 17 repositories.
- *Recommendation:* clone only what the build reads. If CI builds in package mode, only Builds is needed (*verify* which submodules a package-mode build reads).

**Repeated setup.**
- *Today:* several jobs each repeat setup and the build.
- *Recommendation:* use one job (see F8).

**Release.**
- *Today:* the release builds and tests everything again.
- *Recommendation:* the release checks that CI on `main` passed for that exact SHA, and skips the tests. It builds the packages once, with the real version.
- *Trade-off:* the version is set when a package is packed, so reusing the packages CI built would mean repacking them. That isn't worth it. The only work still repeated is one compile per released module per night.

**Commitlint.**
- *Today:* it runs as a separate workflow.
- *Recommendation:* make it a step inside the guard (F4).

**Dependency review.**
- *Today:* it runs only on PRs, so with direct pushes it rarely runs at all.
- *Recommendation:* drop it, provided NuGet audit with `-warnaserror` already fails the build on vulnerable packages (*verify*).
- *Trade-off:* this loses the license check and the npm coverage.

### F10. Nightly release

| Option | How | Pros | Cons |
|---|---|---|---|
| A cron in each module's caller | Each repo schedules its own release | Each repo is fully independent | Failure emails go to whoever last changed the cron, which would be the sync bot, so you'd never hear (*verify*). In public repos, schedules switch off after 60 days without activity (*verify*). |
| One scheduler in this repo | Each night it starts each module's release workflow through `workflow_dispatch`, which the standard already requires. Each repo still runs its own release in its own Actions tab. | Only one schedule to keep alive, in the most active repo. Failure notifications go to you, as the token owner (*verify*). Start times can be staggered. | Needs a token with Actions write access to the modules, stored here as a secret. If the scheduler breaks, no releases happen, but that shows up in one place. |

**Recommendation:** one scheduler in this repo.

**The release job runs in this order:**
1. If CI on the head of `main` isn't green, the job fails red: "main is red, nothing released".
2. If semantic-release finds no releasable commit since the last tag, the job succeeds: "nothing to release".
3. Otherwise it sets the version, packs and publishes the NuGet packages and containers, tags the commit, and creates the GitHub release.

Every step is safe to rerun (NuGet pushes use `--skip-duplicate`, and container images are pushed by tag), so rerunning a failed release completes it. That replaces the three recovery workflows. The variable `HEXALITH_RELEASE_PUBLISH_ENABLED` stays, as a per-repo kill switch.

### F11. How releases propagate

| Option | Pros | Cons |
|---|---|---|
| Same-night cascade in dependency order | New versions reach every module in one night | Cycles in the submodule graph (EventStore with Tenants, Memories with EventStore) have to be broken. A deep chain is slow, and one failure stalls everything after it. |
| Independent: dependency bumps are `build(deps)` commits that don't release, and ship with the module's next real change | Simple; no ripple; quiet modules stay quiet | A module's published package keeps referencing an older Hexalith version until that module changes |
| Every bump triggers a patch release (`fix(deps)`) | Every module is always current | Each Commons change ripples one hop per night across the mesh, causing days of releases everywhere |

**Recommendation:** independent releases. When a dependency fix matters, such as a security fix, an agent commits the bump as `fix(deps): …` to force a release.

Hexalith package versions are pinned centrally in Builds' `Props/Directory.Packages.props`. So a change there must itself produce a Builds release, as `fix(deps)` in Builds, before modules receive it through their next Builds bump (*verify* in architecture).

### Open items to verify

| Item | Section |
|---|---|
| Plan limits of the required-reviewer rule (not used by the recommendations) | D |
| Keep/delete classification of each gate, confirmed during migration | F6 |
| The Free plan's limit on concurrent jobs | F8 |
| Which submodules a package-mode build actually reads | F9 |
| Whether NuGet audit with `-warnaserror` already fails the build on vulnerable packages | F9 |
| Who receives failure notifications for scheduled runs (whoever last changed the cron) and for dispatched runs (the token owner) | F10 |
| Whether schedules in public repos switch off after 60 days without activity | F10 |
| Which Builds changes count as releasable, so that a central version bump reaches modules | F11 |
