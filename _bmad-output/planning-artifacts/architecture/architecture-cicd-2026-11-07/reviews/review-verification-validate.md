# Review (validate gate): verification of the final Hexalith.CiCd spine

- **Spine:** `../ARCHITECTURE-SPINE.md` (status final, updated 2026-11-08, AD-1..AD-21)
- **Memlog:** `../.memlog.md` (through line 109)
- **Earlier passes:** `review-verification.md`, `review-verification-pass2.md`, `review-verification-pass3.md`. Items they raised that still hold in the current text are marked **previously raised, still open**.
- **Lens:** was every committed decision checked against the web, the existing project or the live platform, rather than asserted from training data? This covers versions, whether each named technology still exists and fits, and the platform behaviour the ADs depend on.
- **Date:** 2026-11-08
- **Method:**
  - `gh api` releases for every GitHub-hosted Stack row; the npm and PyPI registries (versions, `engines`, `requires_python`, yanked flags); .NET `releases-index.json`; the Node.js `schedule.json`; runner-images READMEs and issue #14748; a live Builds job log (runner and image version).
  - GitHub docs from their source (`github/docs`): `workflow-syntax.md`, `contexts.md`, `events-that-trigger-workflows.md`, the App and fine-grained PAT permission data (`src/github-apps/data/fpt-2022-11-28/*.json`), the PAT policy page, the Releases REST note. GitHub's OpenAPI description (`app-permissions` schema). The `$/` changelog.
  - Source code at the pinned tags: `actions/create-github-app-token@v3.3.0` (`action.yml`, `README.md`, `lib/get-permissions-from-inputs.js`), `github/codeql-action@v4.39.3` (`init/action.yml`, `analyze/action.yml`), `astral-sh/setup-uv@v10.3.3`, `NuGet/login@v1.2.0`, `actions/setup-dotnet@v6.1.0` README, NuGetGallery `GitHubTokenPolicyValidator.cs` (history).
  - Experiments in the scratchpad: actionlint 1.7.12 and `uvx zizmor@1.32.0 --offline` (spine's committed config) on a sample reusable workflow using `$/`, `job.workflow_ref` and `job.workflow_sha`; `uv run` of a PEP 723 script with the three Stack pins.
  - Live `gh`: repo visibility and heads of all 18 repos, rulesets, org installations, org rulesets, code-scanning alerts, workflow-runs filters, draft releases and tag refs, org code search for `package-release@main`.
  - Brownfield: all 18 `references/` checkouts equal their live `main` today (`git rev-parse HEAD` = `gh api …/commits/main`), so local evidence is live.

## Verdict

Every Stack pin is current, exists and fits as of 2026-11-08, and the core platform mechanics hold (`$/`, `job.workflow_*`, caller-job Trusted Publishing, CodeQL categories, per-repo rulesets on Free). But three behaviours the ADs rely on were never checked, and they break as written: App installation tokens expire after one hour while AD-18 holds one for up to five hours; `create-github-app-token` cannot scope a token to Variables, which AD-7 and AD-3 need; and actionlint 1.7.12 rejects the `job.workflow_ref` that AD-8 depends on.

**Counts:** 0 critical, 1 high, 4 medium, 8 low.

---

## Claims checked

### Stack

| # | Claim | Spine location | Status | Evidence |
| --- | --- | --- | --- | --- |
| S1 | .NET SDK from each `global.json` (10.0.4xx); Builds 10.0.403 | Stack; Conventions "SDK and build" | **verified** (latest SDK 10.0.403, from 10.0.14, 2026-10-25). All 16 .NET repos now pin 10.0.403, 15 with `latestPatch` and Memories with `latestFeature`. AI.Tools has no .NET at all. The SDK floats on 2026-11-10 (V-13). | https://builds.dotnet.microsoft.com/dotnet/release-metadata/releases-index.json ; `references/*/global.json` |
| S2 | Python ≥ 3.12; `ubuntu-latest` moving to 26.04 with 3.14.4 | Stack; AD-11 | **verified.** A live Builds CI job on 2026-11-08 02:02Z ran `ubuntu-latest` on image `ubuntu-26.04` 20261028.624. The 26.04 image ships Python 3.14.4 and Node 24.22.2. During the rollout (until 2026-11-19), 24.04 still serves some jobs with Python 3.12.3 and Node 22.23.4. windows-2025 has 3.12.10. | runner-images `Ubuntu2604-Readme.md`, `Ubuntu2404-Readme.md`, `Windows2025-Readme.md`; https://github.com/actions/runner-images/issues/14748 ; job log of run 42436815567 |
| S3 | uv 0.13.7 | Stack | **verified, latest** (2026-11-03) | https://github.com/astral-sh/uv/releases ; PyPI |
| S4 | `astral-sh/setup-uv` v10.3.3 (`version` input) | Stack | **verified, latest** (2026-10-28); `version` input present | `setup-uv@v10.3.3/action.yml` |
| S5 | Jinja2 3.1.6 | Stack | **verified, latest**, not yanked | https://pypi.org/project/Jinja2/ |
| S6 | PyYAML 6.0.3 | Stack | **verified, latest**; has cp314 wheels, so it fits 3.14 | https://pypi.org/project/PyYAML/6.0.3/ |
| S7 | jsonschema 4.26.0 | Stack | **verified, latest**, requires Python ≥ 3.10 | https://pypi.org/project/jsonschema/ |
| S8 | Node.js 24 (Maintenance LTS) / `actions/setup-node` v7.1.0 | Stack | **verified.** Maintenance since 2026-10-20, EOL 2028-04-30. Node 26 is Active LTS. setup-node v7.1.0 is the latest. | https://raw.githubusercontent.com/nodejs/Release/main/schedule.json ; https://github.com/actions/setup-node/releases |
| S9 | `@semantic-release/commit-analyzer` 13.0.1 | Stack; AD-17 | **verified, latest stable** (beta 14.0.0-beta.4); `engines` node ≥ 20.8.1; resolves in Builds' lockfile today | npm registry; `references/Hexalith.Builds/package-lock.json` |
| S10 | `@semantic-release/release-notes-generator` 14.1.1 | Stack; AD-17 | **verified, latest stable** (beta 15.0.0-beta.3); node ≥ 20.8.1 | npm registry |
| S11 | `@commitlint/cli` 21.2.4 | Stack; AD-8 | **verified, latest**; `engines` node ≥ 22.12, which fits Node 24 | npm registry |
| S12 | jscpd 5.4.3 | Stack | **verified, latest** (published 2026-11-08 06:53Z, the same day); node ≥ 18 | npm registry; https://github.com/kucherenko/jscpd/releases |
| S13 | actionlint v1.7.12, with an ignore for `$/` | Stack; Conventions "Action references" | **verified latest, but incomplete.** Upstream is inactive (last commit 2026-04-19; #711 `$/` and #719 still open). It also rejects `job.workflow_ref` and `job.workflow_sha` (V-3). | experiment; https://github.com/rhysd/actionlint/issues/711 |
| S14 | zizmor v1.32.0 with the committed config | Stack; Conventions | **verified.** Latest release. "No findings" on `$/`, `job.workflow_*`, local reusable call and `$/Github/publish`. | experiment `uvx zizmor@1.32.0 --offline --config` |
| S15 | `actions/checkout` v7.0.1 | Stack | **verified, latest** | GitHub releases |
| S16 | `actions/setup-dotnet` v6.1.0 | Stack | **verified, latest** (2026-11-03) | GitHub releases |
| S17 | `actions/upload-artifact` v7.0.2 | Stack | **verified, latest** | GitHub releases |
| S18 | `actions/download-artifact` v8.0.2 | Stack | **verified, latest** | GitHub releases |
| S19 | `actions/create-github-app-token` v3.3.0 | Stack; AD-7 | **verified latest.** `app-id` is deprecated (V-8), and there is no input that scopes Variables (V-2). | `create-github-app-token@v3.3.0/action.yml` |
| S20 | `github/codeql-action` v4.39.3 | Stack; AD-18 | **verified, latest** (2026-11-04) | GitHub releases |
| S21 | `NuGet/login` v1.2.0 | Stack; AD-17 | **verified, latest**; node24; `user` required | `NuGet/login@v1.2.0/action.yml` |
| S22 | Dapr runtime 1.19.1, one pin in Builds | Stack; AD-12; Deferred | **verified latest** (runtime 1.19.1, CLI 1.19.1). But a pin already exists in Builds `Props/` at 1.18.7, with the CLI at 1.18.2 (V-7). | https://github.com/dapr/dapr/releases ; `Props/Directory.Packages.props:30-31` |
| S23 | Runner ≥ 2.336.0 for `$/` | Stack; AD-9 | **verified.** Changelog: "requires … runner … 2.336.0 or newer". The live hosted runner is 2.338.2. | https://github.blog/changelog/2026-07-30-reference-same-repository-actions-with-self-repository-syntax/ ; job log |

### Platform behaviour

| # | Claim | Spine location | Status | Evidence |
| --- | --- | --- | --- | --- |
| P1 | `$/` resolves to the repo of the file it appears in, at the running commit, including in composite steps; no `@ref`; not on GHES | AD-9; Conventions | **verified** | `github/docs` `workflow-syntax.md:741-749` (https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) |
| P2 | `job.workflow_ref` gives the running Builds tag; `job.workflow_sha` gives the reusable workflow's commit | AD-8; AD-9 | **verified to exist** ("For jobs defined in a reusable workflow, this refers to the reusable workflow file"). Never recorded in the memlog. actionlint rejects it (V-3). | `github/docs` `contexts.md:385-388, 447-465` (https://docs.github.com/en/actions/reference/workflows-and-actions/contexts) |
| P3 | `GITHUB_TOKEN` is refused when publishing a draft whose target differs from `main` in workflow files | Deferred 1 | **verified for both Create and Update**; the Deferred item names only publish (V-4) | https://docs.github.com/en/rest/releases/releases |
| P4 | A draft creates no tag until it is published | AD-17 "creates `v<version>` last" | **partly supported live, undocumented.** The Hexalith.Security_OLD draft `v1.0.0` (target `main`) has no tag ref. The Agents drafts v1.2.1 and v1.2.2 do have tags, but legacy semantic-release pushed those first. | `gh api repos/Hexalith/Hexalith.Security_OLD/git/ref/tags/v1.0.0` → 404 |
| P5 | App permission names: Contents, Workflows, Actions, Administration, Variables, Code scanning alerts | AD-7 | **verified.** "Code scanning alerts" is the `security_events` key; "Variables" is `actions_variables`. | `github/docs` `src/github-apps/data/fpt-2022-11-28/server-to-server-permissions.json` |
| P6 | The AD-21 checks the App can read | AD-3; AD-21 | **verified.** `code-scanning/default-setup` and `automated-security-fixes` need repo Administration read. A repo variable needs Variables read. Rulesets need only Metadata. Org secrets shared with a repo need **Secrets** read, and `/orgs/{org}/installations` needs **org** Administration; both are on the manual checklist. | same file |
| P7 | 60-day schedule auto-disable on public repos; enable API | AD-18; Deferred | **verified** (docs; enable needs Actions write). Whether bot commits or the enable call reset the timer: **unverifiable** (V-10). | `events-that-trigger-workflows.md:967`; permission data |
| P8 | `create-github-app-token` scoping inputs `owner`, `repositories`, `permission-*` | AD-7 | **verified**, except that no `permission-*` input exists for Variables (V-2) | `action.yml@v3.3.0`; https://github.com/actions/create-github-app-token/issues/231 |
| P9 | One minted App token serves a job's whole run | AD-7 "each job mints a token"; AD-18 | **wrong for jobs over 1 hour.** "An installation access token expires after 1 hour", and it is revoked at job end (V-1). | `create-github-app-token@v3.3.0/README.md:16, 436` |
| P10 | An App token can push `.github/workflows/**` and dispatch workflows in other repos; its pushes trigger runs | AD-6; AD-18 | **verified.** `git/refs` writes need Contents write plus Workflows write as an additional permission. Dispatch and enable need Actions write. App tokens create runs. | permission data; `trigger-a-workflow.md:26-28`; `data/reusables/actions/actions-do-not-trigger-workflows.md` |
| P11 | `GITHUB_TOKEN` pushes create no runs, but `workflow_dispatch` does | AD-8 restore | **verified** | same reusable |
| P12 | Fine-grained PAT permissions (Contents, Pull requests, Workflows, Actions, Administration, Variables, Secrets); ≤ 366-day lifetime | AD-7; Seed | **verified.** The org's default maximum is 366 days. Non-expiring tokens are allowed unless a policy blocks them. | `fine-grained-pat-permissions.json`; `setting-a-personal-access-token-policy-for-your-organization.md:34` |
| P13 | A module-agent token without Workflows can keep working on branches across nightly workflow rewrites | AD-7 (implicit) | **unverified, plausibly wrong** (V-5) | https://github.com/orgs/community/discussions/35410 ; https://github.com/web-platform-tests/wpt/issues/31939 |
| P14 | `NuGet/login` in a caller-defined job, even inside a remote composite; the policy matches the workflow file name | AD-17; AD-19; Deferred 2 | **verified by source.** The validator requires `job_workflow_ref` to start with `{owner}/{repo}/.github/workflows/`, then matches the file name case-insensitively; it checks environment only if the policy sets one. The file is unchanged since `63b66c9828` (2026-10-01). The composite case remains a Deferred spike. | https://github.com/NuGet/NuGetGallery/blob/main/src/NuGetGallery.Services/Authentication/Federated/GitHubTokenPolicyValidator.cs |
| P15 | CodeQL `build-mode: none` for C# | AD-18 | **verified.** The C# default setup uses `none`. The action's input is "only available when analyzing a single CodeQL language per job" (V-12). | `build-options-for-compiled-languages.md:88-90`; `codeql-action@v4.39.3/init/action.yml:32-40` |
| P16 | Category `hexalith-release/<language>`; filter on the most recent instance's category | AD-18; Conventions | **verified live.** Alerts carry `most_recent_instance.category`. The list API silently ignores an unknown `category` query parameter, so the filter must be client-side, as the spine says. | `gh api repos/Hexalith/Hexalith.EventStore/code-scanning/alerts` |
| P17 | Latest run of a workflow per SHA, with event `push` or `workflow_dispatch` | AD-16 | **verified live.** `head_sha` + `event` work, but `event` is single-valued: a comma list returns 0, so two queries are needed. | `gh api …/actions/workflows/ci.yml/runs?head_sha=…&event=…` |
| P18 | actionlint and zizmor handle `$/` | Conventions | actionlint: **rejects** `$/` (the ignore works) **and** `job.workflow_*` (no ignore; V-3). zizmor: **accepts**. `self-repository` fixes are marked unsafe upstream (zizmor #2373). | experiment |
| P19 | `uv run` with PEP 723 inline dependencies | AD-11 | **verified.** It resolves the three pins, but transitive dependencies float: MarkupSafe 3.0.4 and referencing 0.37.0 were resolved at run time (V-11). | experiment |
| P20 | GitHub Free: per-repo rulesets on public repos; no org rulesets, push rulesets or required workflows needed | AD-21 | **verified.** Active repo rulesets exist on Builds, EventStore and Platform under plan `free`. `GET /orgs/Hexalith/rulesets` returns 403 "Upgrade to GitHub Team". Push rulesets and required workflows aren't used, so the spine fits. | `gh api orgs/Hexalith`, `…/rulesets` |
| P21 | Org agent Apps (`claude`, `chatgpt-codex-connector`, `cursor`) hold Workflows write | AD-7 | **verified.** All three have `repository_selection=all` with Workflows, Contents and Actions write. `semgrep-app` also has Workflows and Actions write. | `gh api orgs/Hexalith/installations` |

### Brownfield

| # | Claim | Spine location | Status | Evidence |
| --- | --- | --- | --- | --- |
| B1 | Builds workflow inventory and AD-20 lists | AD-20 | **verified.** There are 15 entries, all accounted for, including `eventstore-maintenance-publisher.yml`. Module `@main` uses are exactly `codeql.yml`, `commitlint.yml`, `dependency-review.yml`, `initialize-build`, `initialize-dotnet` and `verify`. `domain-*` and the other composites are used at SHAs. | `references/Hexalith.Builds/.github/workflows/`; `grep` over `references/*/.github` |
| B2 | Builds commitlint `type-enum` | Conventions "Commit types" | **verified.** "Unlimited" body and footer length is not current state (V-9). | `commitlint.config.mjs` |
| B3 | Today's Builds ruleset requires the commitlint check | AD-20 | **verified.** Ruleset 19196298 requires `commitlint / commitlint`, Codacy and SonarCloud. | `gh api repos/Hexalith/Hexalith.Builds/rulesets/19196298` |
| B4 | `schemas/` convention | Conventions "Schemas" | **verified.** Draft 2020-12 in 16/16. `schema` const = file stem and required in 14/16. Top level closed in 15/16. `$id` host split 8/7/1. | `references/Hexalith.Builds/schemas/*.json` |
| B5 | Audit waivers live only in Builds `Props/` | AD-10 | **target state, consistent.** No `NuGetAuditSuppress` items exist anywhere today, only comments in Works and EventStore. No module `NoWarn` NU1903/NU1904. | `grep` over `references/` |
| B6 | `Samples/`, `check.py`, `Github/lib/` | AD-19; Seed | `check.py` and `Github/lib/` are **new**. `Samples/` **already exists**, holding two consumer-template props files that the README documents (V-6). | `ls`; `README.md:37-39,146` |
| B7 | All 18 repos public, default branch `main` | memlog line 9; Seed | **verified today** | `gh api repos/Hexalith/<r>` |
| B8 | 14 unmanaged repos run `Github/package-release@main` | AD-20 known effect | **verified.** Code search: 14 repos, the same list as memlog line 105. No other unmanaged `@main` use of Builds. | `gh api search/code` |
| B9 | The CiCd App exists | AD-7 | **not yet**: no such installation in the org. It is a story-1 precondition, so this is expected. | `gh api orgs/Hexalith/installations` |

---

## Findings

### High

#### V-1 (high) — AD-7 / AD-18: an App installation token expires after one hour, but the nightly holds the App for up to five

- **Location:** AD-7 ("Each job mints a token with `actions/create-github-app-token`"); AD-18 (dispatch, then "polls … for at most 5 hours … reads each run's outcome … pushes `build(cicd): bump …` with the App … then waits for the push-triggered `deliver.yml` run").
- **Issue:** the spine never states the token lifetime. Read together, the two ADs describe one App token serving dispatch, a wait of up to 5 hours, outcome download, the bump push, and the wait for delivery.
- **Evidence:**
  - `actions/create-github-app-token@v3.3.0` `README.md:16`: "An installation access token expires after 1 hour."
  - The same file, `:436`: the token "is revoked in the `post` step of the action, which means it cannot be passed to another job."
  - No memlog entry or earlier review mentions the lifetime (grep of `reviews/` and `.memlog.md`).
- **Failure it allows:** on any night when the releases take more than about an hour, the 60-second poll and the outcome-artifact download start returning 401. The bump push, the step that moves the whole lockstep set, is refused. `nightly.yml` goes red and `builds-version` never advances. A story-8 implementer who writes `nightly.py` as one job, which is the natural reading, hits this on the first real night.
- **Smallest fix:** add one sentence to AD-7: "An installation token lives at most 1 hour. A job that needs the App later mints a new token right before that use." In AD-18, split `nightly.yml` into jobs `dispatch` → `wait` → `report-and-bump`, each with its own `create-github-app-token` step. Keep every App use inside the job's first hour; for the wait, poll in steps of ≤ 50 minutes, each preceded by a mint step.

### Medium

#### V-2 (medium) — AD-7 / AD-3: `create-github-app-token` cannot scope a token to Variables, which the per-module checks need

- **Location:** AD-7 (App permissions include "Variables … read"; "scoped to the repos and permissions it needs"); AD-3 (per-module checks include "the AD-21 preconditions readable with the App's permissions", e.g. `HEXALITH_RELEASE_PUBLISH_ENABLED` exactly `true`/`false`).
- **Issue:** the scoping claim was verified for `owner`, `repositories` and `permission-*` in general (pass 1 #5), but never per permission.
- **Evidence:**
  - `action.yml@v3.3.0` has generated inputs for `permission-administration`, `-contents`, `-workflows`, `-actions` and `-security-events`, but **none for Variables**.
  - The list is generated from octokit's copy of GitHub's `app-permissions` schema. GitHub's own OpenAPI `components.schemas.app-permissions` also has no Variables property.
  - Issue #231, "Permission to manage GitHub Repository Variables", has been open since 2025-04-04. The last comment (2026-10-14) says it is still missing.
  - The permission itself exists as `actions_variables` ("Variables") in GitHub's App permission data.
  - `lib/get-permissions-from-inputs.js`: as soon as any `permission-*` input is set, the token gets only the listed permissions.
- **Failure it allows:** a validate job that scopes its token (`permission-administration: read`, `permission-security-events: read`, …) gets 403 on `GET …/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED`. Every module then fails its per-module checks and is never delivered. The workaround of omitting all `permission-*` inputs hands the validate job, which also runs on `pull_request`, the App's full Contents, Workflows and Actions write on 19 repos. That contradicts AD-7.
- **Smallest fix:** in AD-7, after "scoped to the repos and permissions it needs", add: "`create-github-app-token` v3.3.0 cannot request Variables. The kill-switch value is read by a separate read-only step [chosen in story 4], or moved to the AD-21 manual checklist." Pick one; moving it to the manual checklist is the smallest. Then record the check in the memlog.

#### V-3 (medium) — Conventions "Action references": actionlint 1.7.12 also rejects `job.workflow_ref` and `job.workflow_sha`, and the spine ignores only `$/`

- **Location:** Conventions ("actionlint runs with an ignore for `$/` references"); AD-8 ("The running tag comes from the workflow's own ref (`job.workflow_ref`)"); AD-9 fallback (`job.workflow_sha`); AD-19 (`builds-ci.yml` runs actionlint).
- **Issue:** `job.workflow_*` entered the spine in the pass-3 autofixes (memlog line 102). It was not verified against the docs, and it was not linted.
- **Evidence:**
  - The properties exist (`contexts.md:385-388`), so the platform side is fine.
  - Running actionlint 1.7.12 on a reusable workflow with `env: JOB_REF: ${{ job.workflow_ref }}` gives: `property "workflow_ref" is not defined in object type {check_run_id: number; container: …; services: …; status: string} [expression]`, and the same for `workflow_sha`. This persists with `-ignore '"\$/'`; exit 1.
  - Upstream has made no commit since 2026-04-19 (#719 "author inactive").
  - zizmor 1.32.0 accepts both.
- **Failure it allows:** the first story that reads the running tag in a Builds workflow (restore, AD-8) turns `builds-ci.yml` red. The implementer then improvises: a broad ignore, dropping actionlint, or reading the tag from the module's `hexalith-ci.json`, which AD-8 explicitly forbids.
- **Smallest fix:** in the Conventions row, change to: "actionlint runs with ignores for `$/` references and for `property "workflow_(ref|sha|repository|file_path)" is not defined` (`job.workflow_*`, documented in the contexts reference)". Add a memlog `Verified` entry for `job.workflow_*` citing `contexts.md`.

#### V-4 (medium) — Deferred 1: the `GITHUB_TOKEN` restriction covers creating the draft too, not only publishing it (previously raised, still open in part)

- **Location:** Deferred ("Story 3 spike: publishing a draft whose SHA is behind `main` with `GITHUB_TOKEN` … the run ends `ready`, and `nightly.yml` publishes ready drafts with the App"); AD-17 step 5 ("create the marked draft").
- **Issue:** pass-2 H2 said "cannot create **or** publish". The spine kept only the publish half.
- **Evidence:** the REST docs carry the same note for **Create a release** and **Update a release**: "If the commit identified by target_commitish … adds or modifies any file under .github/workflows/ relative to the repository's default branch, the authenticating token must be authorized to modify workflows … The GITHUB_TOKEN available to GitHub Actions cannot be authorized for this." (https://docs.github.com/en/rest/releases/releases)
- **Failure it allows:** the release SHA is `github.sha` at dispatch. If any App delivery changes module workflows before step 5, the create call returns 404 or 403. Step 5 can run up to 30 minutes plus CodeQL time later, and the `:47` hourly run falls inside the 02:17 night. The run then fails, not `ready`, so the planned fallback (nightly publishes ready drafts) has nothing to publish. The spike as worded would not test this path.
- **Smallest fix:** rewrite Deferred 1 as "creating or publishing a draft whose SHA is behind `main`", and extend the fallback: "if creation is refused, the run ends `ready` without a draft and `nightly.yml` creates and publishes it with the App."

#### V-5 (medium) — AD-7: a module-agent token without Workflows may be unable to sync a branch across the nightly workflow rewrites (never verified)

- **Location:** AD-7 ("Module agents. A fine-grained token … with Contents and Pull requests write. It has no Workflows …"). AD-6 and AD-18 rewrite module `.github/workflows/*.yml` on every Builds bump, i.e. nearly every night.
- **Issue:** the memlog verified that a token without Workflows cannot *write* workflow files (line 10). Nobody checked whether it can *push a branch that merges or rebases a `main` that changed them*.
- **Evidence:**
  - Community reports describe exactly this refusal when a branch is synced with upstream workflow changes ("refusing to allow a Personal Access Token to create or update workflow … without `workflow` scope"), for example https://github.com/orgs/community/discussions/35410 and https://github.com/web-platform-tests/wpt/issues/31939.
  - The fix reported there is a token with Workflows.
  - The GitHub docs don't state the rule precisely. The permission data marks `POST /git/refs` as needing Workflows write as an additional permission.
- **Failure it allows:** any module-agent branch that lives across a nightly bump can't be updated with `main` and pushed. Agents stall, or ask for a token with Workflows, which is exactly what CAP-7 forbids.
- **Smallest fix:** add to AD-7: "Module agents start each branch from current `main` and never merge or rebase across a `build(cicd)` commit. Story 10 verifies with a module-agent token that a branch created after a delivery, and a PR 'Update branch', both push." If the test fails, record the restriction in the instruction block.

### Low

- **V-6 (low) — `Samples/` is not new (never reality-checked).**
  - **Location:** AD-19 ("against `Samples/`"); Seed (`Samples/  # sample module + fixture perimeter`).
  - **Evidence:** Builds already has `Samples/Module.Directory.Build.props` and `Samples/Module.Directory.Packages.props` (last changed `7061ce5c`, 2026-07-26). `README.md:37-39,146` documents them as "the starting point for consuming" Builds. `check.py` and `Github/lib/` don't exist yet.
  - **Failure:** a story-2 or story-5 implementer places a sample module there, or rewrites the README templates as fixtures. Either way, public consumer guidance and the CI fixture get tangled.
  - **Fix:** in the Seed, write `Samples/` as "existing consumer templates + new sample module and fixture perimeter" (or use a subfolder such as `Samples/module/`), and add a memlog reality-check line.

- **V-7 (low) — The Dapr pin already exists and is behind (previously raised as pass-1 L6 and pass-2 L10, still open in part).**
  - **Location:** Stack "Dapr runtime (one pin in Builds) 1.19.1"; Deferred ("seeded at 1.19.1 … story 2 names its file").
  - **Evidence:** `Props/Directory.Packages.props:30-31` already defines `HexalithDaprRuntimeVersion` 1.18.7 and `HexalithDaprCliVersion` 1.18.2. They are read by `domain-ci-v2.yml` and the catalog tools. The latest runtime and CLI are both 1.19.1. The Stack has no CLI row.
  - **Failure:** story 2 creates a second pin file, breaking "one pin", or the runtime moves to 1.19.1 while the CLI stays at 1.18.2.
  - **Fix:** in Deferred, write "the pin is `HexalithDaprRuntimeVersion` and `HexalithDaprCliVersion` in `Props/Directory.Packages.props`, bumped to 1.19.1", and add a Dapr CLI 1.19.1 row.

- **V-8 (low) — `HEXALITH_CICD_APP_ID` names a deprecated input (previously raised as pass-1 L1, pass-2 L3 and pass-3, still open).**
  - **Evidence:** `action.yml@v3.3.0:11-14`: `app-id` has `deprecationMessage: "Use 'client-id' instead."`
  - **Fix:** in Conventions, rename it `HEXALITH_CICD_APP_CLIENT_ID`.

- **V-9 (low) — Commit conventions describe a target as if it were current state (previously raised as pass-2 L9, still open).**
  - **Location:** Conventions "Commit types": "body and footer line length unlimited".
  - **Evidence:** Builds `commitlint.config.mjs` today sets `body-max-line-length` 200 and `header-max-length` 200, and inherits footer 100 from config-conventional 21.2.4.
  - **Fix:** write "set to unlimited by the guard's config" (owned by story 5), or keep today's 200.

- **V-10 (low) — The 60-day deferral can't be "verified in story 8", and its fallback rests on an undocumented warning.**
  - **Location:** Deferred ("Whether bot commits count as activity … Verified in story 8 … the maintainer re-enables the workflows on GitHub's warning"); memlog line 45 cites "keepalive-workflow makes a commit after 50 days".
  - **Evidence:**
    - The docs define only "no repository activity … in 60 days" (`events-that-trigger-workflows.md:967`). The disable/enable page says nothing about what resets the timer.
    - The cited project moved to an enable-API keepalive in v2, and its repo is now "disabled by GitHub Staff due to a violation of GitHub's terms of service" (https://github.com/gautamkrishnar/keepalive-workflow). Its author warned that automated commits may breach the ToS.
    - The maintained alternative https://github.com/liskin/gh-workflow-keepalive "uses GitHub API to preemptively re-enable the workflow … will not create any dummy commits".
    - The advance-warning email is only community-reported, and https://lists.w3.org/Archives/Public/public-swicg/2025Apr/0036.html reports a disable without warning.
    - A test in story 8 would need 60 idle days.
  - **Failure:** both CiCd schedules stop together, and the 26 h check (itself a schedule) stops with them.
  - **Fix:** in Deferred, write "not testable in a story. The nightly enable-API call is the primary keepalive (current community practice); the commit keepalive is secondary." Re-cite memlog line 45.

- **V-11 (low) — Stack gaps (previously raised as pass-2 L10, still open).**
  - **Missing rows:** `@commitlint/config-conventional` 21.2.4; Microsoft.Playwright; the Dapr CLI (V-7); the tool that pushes the OCI archives from `publish` (Deferred 2); `gh`.
  - **PEP 723:** transitive dependencies still float. My run resolved MarkupSafe 3.0.4 and referencing 0.37.0 at run time.
  - **Fix:** add the rows, or state that they are pinned in Builds' `package.json`/lockfile and in `uv lock --script`.

- **V-12 (low) — The CodeQL job must be one language per job (previously raised as pass-2 M2, partly fixed).**
  - **Evidence:** `codeql-action@v4.39.3/init/action.yml:32-35`: `build-mode` "is only available when analyzing a single CodeQL language per job, for example using a matrix". The per-language category is already in the spine.
  - **Fix:** in AD-18, write "`codeql`: a matrix over the `codeql` languages, `build-mode: none` …".

- **V-13 (low) — The CI SDK floats with no commit (previously raised as pass-1 M4, still open). The spec's inventory is stale.**
  - **Evidence:**
    - All 16 .NET repos pin 10.0.403 with `latestPatch`, and Memories uses `latestFeature`.
    - setup-dotnet v6.1.0 "take[s] the highest SDK the policy allows" (README:358). So CI moves to 10.0.404 on Patch Tuesday, 2026-11-10, with no commit.
    - `specs/spec-cicd/module-inventory.md:93` still says the pins are "split between 10.0.401, .402, and .403".
  - **Fix:** in the Stack, change to "`global.json` resolves the SDK (`rollForward` `latestPatch`: highest 10.0.4xx patch)". Raise the inventory line upstream.

---

## Memlog cross-check

| Memlog entry | Claim | Today |
| --- | --- | --- |
| l.9 (2026-11-07) | 18 repos public, `main` default | **still true** (B7) |
| l.10–11 | `GITHUB_TOKEN` limits; App pushes and dispatches | **still true** (P10, P11) |
| l.12 | fine-grained PAT, 366-day default | **still true** (P12) |
| l.14, l.45 | 60-day disable; bot commits unconfirmed; keepalive-workflow makes commits | Disable confirmed. **The cited source is stale:** the project moved to API mode and is now disabled by GitHub Staff (V-10). |
| l.17, l.37 | `$/`, runner ≥ 2.336.0 | **still true**; live runner 2.338.2 (P1, S23) |
| l.19, l.59, l.66, l.101 | Stack versions | **all still latest** on 2026-11-08 (S1–S23) |
| l.27 | App token "scoped to the repos and permissions it needs" | **never verified per permission**; Variables cannot be scoped (V-2) |
| l.27, l.46 | the App serves nightly dispatch, poll and bump | **never checked against the 1-hour token lifetime** (V-1) |
| l.44, l.65, l.99 | nuget.org validator | **still true**; source unchanged since 2026-10-01 (P14) |
| l.63 | `Hexalith.Build.props:33` WNAE | **still true** |
| l.64, l.68 | rulesets; org agent Apps | **still true** (B3, P21) |
| l.66 | actionlint rejects `$/` | **true but incomplete**: it also rejects `job.workflow_*` (V-3) |
| l.77 | GITHUB_TOKEN can't create/update a release whose target modifies workflows | **true**, but the spine kept only the publish half (V-4) |
| l.86–89, l.98 | Builds workflows and schemas | **still true** (B1, B4) |
| l.102 | AD-8 `job.workflow_ref`, AD-9 `job.workflow_sha` | **no verification entry.** The properties exist (P2), but were never linted (V-3). |
| l.105 | 14 unmanaged `package-release@main` callers | **still true** (B8) |
| none | `Samples/` exists; Dapr pin in `Props/`; module-agent branch sync | **never reality-checked** (V-6, V-7, V-5) |

**Counts:** 0 critical, 1 high, 4 medium, 8 low.
