# Review: verification of the Hexalith.CiCd architecture spine

- **Spine:** `../ARCHITECTURE-SPINE.md` (draft, 2026-11-07)
- **Decision log:** `../.memlog.md`
- **Lens:** was each committed decision checked against the web or the existing project, or only asserted from memory? This covers current versions, whether each named technology still exists and fits, and the platform behaviour each AD depends on.
- **Date:** 2026-11-07
- **Method:**
  - `gh api` against release, rules, installation, code-scanning and immutable-release endpoints.
  - The npm and PyPI registries, and the dotnet release index.
  - docs.github.com, learn.microsoft.com, and the GitHub changelog.
  - The NuGetGallery source code.
  - The runner-images READMEs.
  - The existing repos under `references/`.
  - Local experiments in the scratchpad: actionlint 1.7.12 and zizmor 1.32.0 run against sample workflows that use the spine's constructs, and `dotnet restore` (SDK 10.0.403) run against a project that references a vulnerable package.

## Verdict

The version pins are current. However, two decisions rest on platform behaviour that is wrong for this project:

- **NuGet Trusted Publishing from Builds' reusable workflow.** nuget.org's validator rejects it.
- **The `-warnaserror` restore gate.** It does not fail on NU1901–1904, because Builds' own props downgrade those codes.

Two named tools, actionlint and zizmor in its default policy, reject constructs the spine requires. "Never cancelled" concurrency is also wrong as written. These must be fixed before story 2.

---

## Critical

### C1 — AD-17: Trusted Publishing cannot work from Builds' reusable `release.yml` (WRONG)

- **Spine claim:** "NuGet publishing uses Trusted Publishing … The module caller and Builds' reusable workflow are both named `release.yml`." The Deferred section adds: "Which claim nuget.org matches for reusable workflows … neutralized by naming both files `release.yml`".
- **Evidence:** nuget.org's validator is `NuGet/NuGetGallery` `src/NuGetGallery.Services/Authentication/Federated/GitHubTokenPolicyValidator.cs`, last changed 2026-10-01 in "[OIDC] Validate all claims (#11009)". `EvaluatePolicyAsync` requires two things:
  1. The `repository` claim must exactly equal the policy's `{owner}/{repo}`, which is the caller, i.e. the module.
  2. The `job_workflow_ref` claim must **start with** `{policyOwner}/{policyRepo}/.github/workflows/`, and only then is the file name compared.

  In a job defined inside Builds' reusable workflow, `job_workflow_ref` is `Hexalith/Hexalith.Builds/.github/workflows/release.yml@refs/tags/vX`. It never starts with `Hexalith/Hexalith.Folders/.github/workflows/`, so the request is refused with "Claim 'job_workflow_ref' … does not start with …". The file name never gets compared, so naming both files `release.yml` does not help.
- **Reality check:** the existing project already works around this.
  - The only `NuGet/login` use in Builds is in `build-release.yml`, a non-reusable `workflow_dispatch` workflow in Builds itself.
  - The reusable `domain-release.yml` takes a `NUGET_API_KEY` secret.
  - `Github/prepare-domain-release/README.md` tells the *caller* to run `NuGet/login`.
- **Fix:**
  - Put the NuGet publish job (`id-token: write`, `NuGet/login@<sha> # v1.2.0`, `dotnet nuget push --skip-duplicate`) in the **rendered module `release.yml` as a caller-owned job**. It downloads the packed `.nupkg` artifact from the Builds reusable job. Its steps may still be Builds composites (`uses: Hexalith/Hexalith.Builds/Github/<nuget-push>@<tag>`), because composite steps do not change `job_workflow_ref`.
  - Restate the "Completing a draft" order across the two workflows: reusable pack, then caller push, then reusable or caller container push and draft publish. Keep "tag last".
  - Delete the Deferred bullet about which claim nuget.org matches. It is now answered: the caller file, and the job must be defined in it.

### C2 — AD-12: `-warnaserror` restore does not fail NU1901–NU1904 in these repos (WRONG)

- **Spine claim:** "Restore with `-warnaserror`, so NU1901–NU1904 fail the run and no dependency-review job exists." The memlog adds: "Spec conditional applied after verification".
- **Reality:**
  - `references/Hexalith.Builds/Hexalith.Build.props:33`, the props the module submodule exists to supply (AD-9), deliberately sets `<WarningsNotAsErrors>$(WarningsNotAsErrors);NU1901;NU1902;NU1903;NU1904</WarningsNotAsErrors>`.
  - Nine module `Directory.Build.props` files do the same: Works, Memories, Folders, EventStore, Agents, Tenants, Conversations, and others.
  - `Hexalith.Timesheets/Directory.Build.props:22` sets `<NuGetAudit>false</NuGetAudit>`.
  - Two EventStore test projects set `NuGetAuditMode=direct`.
- **Experiment:** SDK 10.0.403, `net10.0`, `System.Text.Json 8.0.0`, which triggers NU1903 (high):

  | Project settings | `dotnet restore` arguments | NU1903 | Exit |
  | --- | --- | --- | --- |
  | none | `-warnaserror` | error | 1 |
  | `WarningsNotAsErrors` NU1901–4 (as in Builds props) | `-warnaserror` | **warning** | **0** |
  | same | `-warnaserror:NU1901;NU1902;NU1903;NU1904` | error | 1 |
  | same | `-warnaserror -p:WarningsNotAsErrors=` | error | 1 |
  | `NuGetAudit=false` | `-warnaserror` | not reported | **0** |
  | `NuGetAudit=false` | `-warnaserror -p:NuGetAudit=true -p:WarningsNotAsErrors=` | error | 1 |

  The blanket `-warnaserror` also promoted the unrelated NU1510 (pruning) to an error. So the gate fails on any restore warning, not only on NU1900 as the memlog notes.
- **Consequence:** dependency-review was removed on the strength of a gate that is a no-op in at least 10 of the 18 repos. Module-owned MSBuild files can switch it off at any time.
- **Fix:**
  - The Builds restore script runs `dotnet restore -warnaserror:NU1900;NU1901;NU1902;NU1903;NU1904 -p:NuGetAudit=true -p:NuGetAuditMode=all -p:NuGetAuditLevel=low`. Global properties override module props, and the explicit code list promotes only audit codes.
  - Remove the `WarningsNotAsErrors` line from `Hexalith.Build.props`, or document that CI overrides it.
  - Add `NuGetAuditSuppress` items and `NoWarn` containing `NU190x` in module MSBuild files to the guard's deny checks. Neither can be overridden from the command line.
  - Record the experiment in the memlog as the verification.

---

## High

### H1 — actionlint (Stack v1.7.12, Conventions "pass `actionlint`") rejects `$/` and `queue:` (DOESN'T FIT)

- v1.7.12 (2026-03-30) is the latest release, but upstream's last commit was 2026-04-19. Issue rhysd/actionlint#719, "author inactive", points to forks.
- I ran v1.7.12 on sample workflows:
  - `uses: $/.github/actions/prepare` fails with: specifying action "$/.github/actions/prepare" in invalid format because ref is missing [action].
  - `jobs.x.uses: $/.github/workflows/ci.yml` fails with: reusable workflow call … is not following the format … [workflow-call].
  - `concurrency: {queue: max}` fails with: unexpected key "queue" for "concurrency" section [syntax-check].
- Open issues: #711 (`$/`) and #657 (`queue`). The Stack recorded the version as current but never checked that it accepts the spine's own AD-9 syntax.
- **Fix:** record an explicit choice. Either:
  - pin a maintained fork (kjanat/actionlint or jdx/jactionlint) after evaluation; or
  - keep rhysd 1.7.12 with two narrowly scoped `-ignore` regexes (the workaround documented in #711 and #657), written into the spine; or
  - replace actionlint with schema validation (schemastore `github-workflow.json` already defines `concurrency.queue`) plus zizmor.

### H2 — zizmor "default policy" fails every tag pin, and its auto-fix would break hook points (DOESN'T FIT)

zizmor ≥ 1.20 defaults `unpinned-uses` to a blanket hash-pin rule (docs.zizmor.sh/audits/#unpinned-uses). I ran zizmor 1.32.0 offline:

- `actions/checkout@v7.0.1`, `actions/create-github-app-token@v3.3.0`, `astral-sh/setup-uv@v10.3.3`, and the caller `uses: Hexalith/Hexalith.Builds/.github/workflows/ci.yml@v4.45.0` are each reported as `error[unpinned-uses]` (high). The exit code is 14.

This conflicts with the Stack (all tag refs), AD-10 ("exact release tag") and AD-12 (`prepare@<same tag>`).

The new `self-repository` audit (zizmor PR #2271) flags Builds' intentional `uses: ./.github/actions/<hook>`, and **offers an auto-fix to `$/`**. Applying it would make hooks resolve into Builds instead of the module, silently disabling every module hook.

**Fix:**
- Change the convention from "default policy" to "committed `zizmor.yml`".
- Hash-pin third-party and `actions/*` refs with `# vX.Y.Z` comments. The Stack versions then become those comments.
- Set the `unpinned-uses` policy `Hexalith/*: ref-pin` for Builds refs. Enable immutable releases on Builds so that a tag can't move; today `GET /repos/Hexalith/Hexalith.Builds/immutable-releases` returns `enabled: false`.
- Put inline `# zizmor: ignore[self-repository]` on each hook step, with the reason.
- Forbid `zizmor --fix` on Builds `ci.yml`.

### H3 — "Never cancelled" concurrency is wrong without `queue: max` (WRONG)

This affects AD-6, AD-17, AD-18 and the Concurrency conventions row.

- **Docs:** by default "any existing `pending` job or workflow in the same concurrency group will be canceled". `queue: single` is the default (https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
- **Effect:** with only `cancel-in-progress: false`, two failure modes follow:
  - A pending nightly bump or delivery is cancelled by the next hourly run, a push-triggered run, or a manual run.
  - A nightly-dispatched module release is cancelled by a manual dispatch.

  The nightly poller then sees `cancelled`.
- **What exists:** `queue: max` holds up to 100 pending runs, became available on 2026-05-07 (https://github.blog/changelog/2026-05-07-github-actions-concurrency-groups-now-allow-larger-queues/), is valid at workflow and job level, and is invalid together with `cancel-in-progress: true`.
- **Fix:**
  - Specify `queue: max` for the `deliver` and `release` groups.
  - Give the nightly poller a hard timeout. Community discussion #206259 reports stuck `queue: max` jobs.
  - Note the actionlint dependency (H1).

### H4 — Branch rulesets block the "one write path" on three repos (UNVERIFIED against reality)

AD-6 and AD-8 push directly to `main`: delivery with the App token, restore with `GITHUB_TOKEN`. The repos' actual rules (`gh api repos/Hexalith/<r>/rulesets/<id>`) are:

| Repo | Rules on `main` | Bypass actors |
| --- | --- | --- |
| Hexalith.Builds | `pull_request` + strict `required_status_checks` | user 6775094 |
| Hexalith.EventStore | the same | users 6775094 and 148322258 |
| Hexalith.Platform | `pull_request`, 1 approval + code owner | user 6775094 |
| Hexalith.Conversations | classic protection: linear history, enforce admins | (compatible with rebase-and-push) |

App and `GITHUB_TOKEN` pushes to Builds, EventStore and Platform will be rejected (GH013).

**Fix:**
- Add the CiCd App as an `Integration` bypass actor on those rulesets, or replace them with one org ruleset that has the bypass.
- Decide how restore works where `GITHUB_TOKEN` can't bypass. Whether the GitHub Actions integration can be a bypass actor is UNCONFIRMED; the alternative is that restore defers to delivery on those repos.
- Add an onboarding/CiCd CI check on `GET /repos/{o}/{r}/rules/branches/main` (AD-3).

### H5 — AD-7's token-level block is contradicted by org-wide agent Apps (UNVERIFIED against reality)

AD-7 and CAP-7 rest on "module agents use a fine-grained token without Workflows". `gh api orgs/Hexalith/installations` shows these Apps installed on **all** repositories:

- `claude`, `chatgpt-codex-connector` and `cursor`, each with `contents: write` + `workflows: write`;
- `semgrep-app`, with `workflows: write` + `actions: write`.

Agent sessions driven through these Apps can write `.github/workflows/**` in every module.

**Fix:**
- Restrict those installations to non-managed repos, or remove their Workflows permission.
- Add an "only the CiCd App has Workflows on managed repos" check to onboarding. The nightly run can't do it, because the installations endpoint needs org-admin.

---

## Medium

- **M1 — Stack "Python ≥ 3.12 (runner system 3.12.3)" is stale.**
  - `ubuntu-latest` is moving to Ubuntu 26.04 between 2026-10-19 and 2026-11-19 (https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/).
  - The 26.04 image's system `python3` is **3.14.4**; 24.04 has 3.12.3 and windows-2025 has 3.12.10 (runner-images READMEs).
  - The floor still holds. But CI will exercise 3.14 while the local check may run 3.12, so nothing tests the floor.
  - **Fix:** update the row. Have Builds' own CI run its script tests on 3.12 (via `uv python` or setup-python) as well as on the runner's `python3`.
- **M2 — `python3` on `windows-latest` is UNCONFIRMED** (see `jobs` knob → runner, AD-12 extra-runner job → Builds `prepare`).
  - Windows toolcache Pythons ship `python.exe`, and actions/setup-python#1079 reports that versioned executables are missing.
  - **Fix:** Builds composites call `python` when `runner.os == 'Windows'`, or story 2 verifies `python3` on windows-2025.
- **M3 — uv itself is not pinned.**
  - `astral-sh/setup-uv@v10.3.3` installs the latest uv (0.13.7 today) unless `version` or `version-file` is set (setup-uv action.yml).
  - PEP 723 `uv run` also re-resolves transitive dependencies (MarkupSafe, referencing, rpds-py) at run time. That undermines AD-11 ("pinned") and AD-5's "re-render and fail on any diff" determinism.
  - **Fix:** set setup-uv `version: 0.13.7`, or `required-version` in a CiCd `uv.toml`. Use `uv lock --script` per tool, or set `exclude-newer` in the script metadata.
- **M4 — Stack ".NET SDK 10.0.403 (from each `global.json`)" does not match reality.**
  - Module pins range from 10.0.401 to 10.0.403.
  - All use `rollForward: latestPatch`, except Memories, which uses `latestFeature`. setup-dotnet v6.1.0 installs the **highest** SDK the policy allows (README), so the SDK changes with no commit (10.0.404 is expected on Patch Tuesday, 2026-11-10). That cuts against AD-1.
  - `Hexalith.AI.Tools` has no `global.json` and no .NET solution, so `setup-dotnet global-json-file` "will fail" and AD-12's restore/build/test shape doesn't apply.
  - ChatBot, Platform and Timesheets lack the MTP `test.runner`, so `dotnet test` runs in VSTest mode there.
  - **Fix:**
    - Decide the rollForward policy (render it, or guard it).
    - Rename the row to "whatever each `global.json` resolves to".
    - Add a setup knob or an exclusion for AI.Tools.
    - Make the test script handle both `dotnet test` modes.
- **M5 — AD-17 "containers = projects with SDK container publishing enabled" sweeps in test hosts.**
  - Web and Worker SDK projects have container support on by default; only console apps need `EnableSdkContainerSupport` (https://learn.microsoft.com/dotnet/core/containers/overview).
  - The repos have 58 Web/Worker projects but only 30 explicit opt-ins. Test hosts and samples would be pushed to Zot, for example `EventStore.Sharding.TestHost`, `EventStore.Sample`, `Memories.Web.SpecimenHost` and `PublishedCompatibility…/Host`.
  - **Fix:** select on an explicit opt-in property (e.g. `HexalithPublishContainer=true`), excluding `IsTestProject=true`.
- **M6 — The schedule can be dropped silently.**
  - The docs say "The `schedule` event can be delayed … some queued jobs may be dropped" (https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
  - A dropped 02:17 run creates no red run and no email, which is the outcome AD-18 says it prevents.
  - **Fix:** the hourly `deliver.yml`, or a second cron, fails when the last `nightly.yml` run is more than 26 hours old.
- **M7 — Nightly polling: the enabling platform feature was never recorded, and the rate budget was never set.**
  - The dispatch API now returns `workflow_run_id`, `run_url` and `html_url` (https://github.blog/changelog/2026-02-19-workflow-dispatch-api-now-returns-run-ids, https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event). AD-18 should rely on this explicitly rather than searching runs.
  - Installation tokens share 5,000 requests per hour across the App installation, for delivery, polling and keepalive alike (https://docs.github.com/en/actions/reference/limits).
  - **Fix:** specify the poll interval, use conditional (ETag) requests, and add an overall timeout.
- **M8 — Stack omissions for tools the ADs run.**
  - `actions/setup-node` (v7.1.0, used by Builds today). The ubuntu-24.04 and windows-2025 default Node is 22.23.4, below the Stack's ≥ 24.10 floor.
  - Dapr CLI 1.19.1 and `dapr/setup-dapr`.
  - Microsoft.Playwright 1.64.1. Its browser install uses `playwright.ps1`, i.e. the image's pwsh 7.6.9, contrary to the memlog 5.4 rule "don't depend on image specifics".
  - `@commitlint/config-conventional` 21.2.4, `@semantic-release/commit-analyzer` 13.0.1 and release-notes-generator.
  - gh CLI: 2.103.3 on the images; ≥ 2.87 is needed for the run URL from `gh workflow run`.
  - uv 0.13.7.
  - **Fix:** add these rows, or state that they are pinned in Builds `package.json` and its lockfile.
- **M9 — AD-12 names a non-existent repo.**
  - `uses: Hexalith/Builds/Github/prepare@<same tag>` points at `Hexalith/Builds`, which does not resolve (`gh repo view Hexalith/Builds`: "Could not resolve to a Repository"). The repo is `Hexalith/Hexalith.Builds`.
  - **Fix:** correct the reference in AD-12 and in the templates.

## Low

- **L1 — create-github-app-token v3.**
  - In v3.3.0, `app-id` is deprecated in favour of `client-id`.
  - The spine names only the private-key secret. **Fix:** add a `HEXALITH_CICD_APP_CLIENT_ID` variable.
  - The scoping inputs `owner`, `repositories` and `permission-*` are CONFIRMED (action.yml@v3.3.0).
- **L2 — semantic-release dry-run.** It computes the version and notes without tagging: CONFIRMED (v25.0.9 `index.js`; `normalize.js` skips prepare/publish/success/fail in dry-run). Three caveats:
  - It still runs `verifyAuth` (`git push --dry-run`), so it needs push credentials.
  - It exits early on PR events.
  - **Fix:** capture `nextRelease` through the JS API rather than by parsing logs, and declare only commit-analyzer and release-notes-generator as plugins.
- **L3 — Draft releases and tags.**
  - That a draft creates no tag until it is published is only community-confirmed. The REST docs say only that `target_commitish` "determines where the Git tag is created from".
  - `gh release create --draft --target <full SHA>` is CONFIRMED (https://cli.github.com/manual/gh_release_create).
  - Drafts are listed only for tokens with push access, and "get by tag" returns only published releases. **Fix:** find drafts through the list API, and add a story-level test.
  - `GITHUB_TOKEN` can create tags on commits that change workflow files: CONFIRMED by Builds' own history. `github-actions[bot]` published v4.37.0–v4.44.0, whose ranges touched `.github/workflows/`.
- **L4 — Dependabot.**
  - The `github-actions` and `gitsubmodule` ecosystems exist (CONFIRMED). Dependabot *security updates* for Actions are a repository setting that doesn't depend on `dependabot.yml` (https://github.blog/changelog/2022-11-23-dependabot-security-updates-now-supports-github-actions).
  - It is disabled on all 18 repos today, but nothing keeps it disabled. **Fix:** add it to the onboarding check.
  - Builds' own `dependabot.yml` enables `github-actions` with directories `/` and `/Github/*`. **Fix:** say whether AD-10's ban applies to Builds. If it does, nothing refreshes the Stack pins.
- **L5 — Node.** Node 24 is now Maintenance LTS; 26.x is the active LTS. The ≥ 24.10 floor matches the semantic-release 25 engines (`^22.14.0 || >=24.10.0`) and is fine.
- **L6 — Dapr 1.19.1 is a planned bump, not current state.** Builds props pin `HexalithDaprRuntimeVersion` 1.18.7 and `HexalithDaprCliVersion` 1.18.2, with the .NET SDK packages at 1.19.0. **Fix:** list the bump as a migration step.
- **L7 — .NET 11.** .NET 11 is at rc.3 (go-live, 2026-10-25), with GA imminent. That has no impact; .NET 10 is LTS. The 10.0.403 pin will be superseded on 2026-11-10 (see M4).
- **L8 — `IsTestProject` is a module-owned csproj property.** Five projects already set it to `false`, legitimately. Classification can be dodged by the same kind of csproj marker that memlog 2.x rejected. **Fix:** the guard compares the classified set against projects referencing a test SDK (Microsoft.NET.Test.Sdk or xunit.v3).
- **L9 — The code-scanning `severity` filter takes a single value** (https://docs.github.com/en/rest/code-scanning/code-scanning#list-code-scanning-alerts-for-a-repository). **Fix:** query `critical` and `high` separately, with `state=open`, `ref=refs/heads/main` and `tool_name=CodeQL`, and a `security-events: read` token. The Actions runs `event` filter is also single-valued (`push` and `workflow_dispatch` need two queries) and capped at 1,000 results.

---

## Platform behaviour checklist

| # | Behaviour an AD relies on | Status | Source |
| --- | --- | --- | --- |
| 1 | `$/` self-repository refs (AD-9). In a reusable workflow called from another repo it resolves to the **called** workflow's repo at the running commit; no `@ref`; runner ≥ 2.336.0; not on GHES | CONFIRMED | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax ("`$/` always resolves against the repository of the file it appears in"); https://github.blog/changelog/2026-07-30-reference-same-repository-actions-with-self-repository-syntax/ |
| 2 | `GITHUB_TOKEN` cannot write `.github/workflows/**` (no `workflows` permission key) | CONFIRMED | workflow-syntax `permissions` key list (no `workflows`); https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps (Workflows is an additional permission on contents and ref writes) |
| 3 | `GITHUB_TOKEN` pushes create no runs; `workflow_dispatch` and `repository_dispatch` do | CONFIRMED | https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow |
| 4 | App with Workflows can push workflow files; Actions:write can dispatch; App-token pushes trigger runs | CONFIRMED | permissions-required-for-github-apps (dispatches = Actions write); trigger-a-workflow ("use a GitHub App installation access token") |
| 5 | `create-github-app-token` scoping (`owner`, `repositories`, `permission-*`) | CONFIRMED (L1: `client-id`) | https://github.com/actions/create-github-app-token/blob/v3.3.0/action.yml |
| 6 | Draft release creates the tag only on publish | UNCONFIRMED (community only) | REST "Create a release" is silent; L3 |
| 7 | `gh release create --draft --target <full SHA>` | CONFIRMED | https://cli.github.com/manual/gh_release_create |
| 8 | semantic-release computes the next version without tagging (dry-run) | CONFIRMED | semantic-release v25.0.9 `index.js`, `lib/plugins/normalize.js` |
| 9 | `releaseRules` for custom types; falls back to the defaults; `build`/`ci` don't release; `fix(deps)` releases | CONFIRMED | semantic-release/commit-analyzer `index.js`, `lib/default-release-rules.js` |
| 10 | `NuGetAuditMode=all` by default for net10.0 | CONFIRMED | https://learn.microsoft.com/dotnet/core/compatibility/sdk/10.0/nugetaudit-transitive-packages |
| 11 | NU1901–1904 fail restore under `-warnaserror` | **WRONG in these repos** (C2) | local experiment; `Hexalith.Build.props:33` |
| 12 | nuget.org Trusted Publishing from a reusable workflow | **WRONG** (C1) | NuGetGallery `GitHubTokenPolicyValidator.cs`; https://learn.microsoft.com/nuget/nuget-org/trusted-publishing |
| 13 | Actions API filters runs by `head_sha` | CONFIRMED (single `event`, 1k cap) | https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-workflow |
| 14 | Dispatch returns the run ID | CONFIRMED, not in the memlog (M7) | https://github.blog/changelog/2026-02-19-workflow-dispatch-api-now-returns-run-ids |
| 15 | Code-scanning alerts API `severity` filter | CONFIRMED (single value) | https://docs.github.com/en/rest/code-scanning/code-scanning |
| 16 | CodeQL `build-mode: none` for C# | CONFIRMED (accuracy "Good", generated code not analyzed); no repo has default setup enabled, so advanced uploads won't conflict (`code-scanning/default-setup` = not-configured ×18) | https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages |
| 17 | Dependabot `github-actions` and `gitsubmodule` ecosystems | CONFIRMED (L4: security updates are separate) | Dependabot options reference; 2022-11-23 changelog |
| 18 | Public-repo schedules disable after 60 days without activity | CONFIRMED; whether bot commits count as "activity" is UNCONFIRMED (correctly deferred) | events-that-trigger-workflows |
| 19 | Schedule failure email goes to the last cron editor | CONFIRMED | events-that-trigger-workflows |
| 20 | Free plan: 20 concurrent jobs (5 macOS); jobs beyond that queue | CONFIRMED; org plan = `free` (`gh api orgs/Hexalith`) | https://docs.github.com/en/actions/reference/limits |
| 21 | Concurrency "never cancelled" | **WRONG without `queue: max`** (H3) | control-workflow-concurrency docs |
| 22 | jscpd covers YAML, bash, PowerShell, Python | CONFIRMED (v5 Rust engine, 224 formats, also on PyPI) | https://github.com/kucherenko/jscpd/blob/master/FORMATS.md |
| 23 | Python 3.12 on `ubuntu-latest` | **STALE**: moving to 26.04, which has Python 3.14.4; the floor still holds (M1) | 2026-09-17 changelog; runner-images `Ubuntu2604-Readme.md` |
| 24 | `raw.githubusercontent.com` CDN cache (reason for the AD-8 git clone) | CONFIRMED (`cache-control: max-age=300`) | curl |
| 25 | Anonymous shallow sparse clone of CiCd | CONFIRMED (CiCd is public; anonymous `git ls-remote` works) | gh / git |
| 26 | `GITHUB_TOKEN` can tag and publish releases on commits that change workflow files | CONFIRMED by Builds history | `gh api repos/Hexalith/Hexalith.Builds/releases` |
| 27 | Direct pushes to module `main` allowed | **WRONG for Builds, EventStore, Platform** (H4) | rulesets API |
| 28 | Only the CiCd App holds Workflows on managed repos | **WRONG** (H5) | `gh api orgs/Hexalith/installations` |
| 29 | Web SDK projects are container-publishable by default | CONFIRMED (M5) | https://learn.microsoft.com/dotnet/core/containers/overview |
| 30 | setup-dotnet `global-json-file` with `latestPatch` installs the highest SDK | CONFIRMED (M4) | setup-dotnet v6.1.0 README |
| 31 | `NuGet/login` v1.2.0 (`user` required, node24) | CONFIRMED | https://github.com/NuGet/login/blob/v1.2.0/action.yml |

## Stack row check

| Row | Spine | Latest found (date) | Status |
| --- | --- | --- | --- |
| .NET SDK | 10.0.403 | 10.0.403 (2026-10-25, releases-index) | current; see M4 |
| Python | ≥ 3.12 (system 3.12.3) | 24.04: 3.12.3; 26.04 (`ubuntu-latest` from Nov): 3.14.4 | stale note (M1) |
| uv / setup-uv | v10.3.3 | setup-uv v10.3.3 (2026-10-28); uv 0.13.7 (2026-11-03) | uv itself unpinned (M3) |
| Jinja2 / PyYAML / jsonschema | 3.1.6 / 6.0.3 / 4.26.0 | the same (PyPI) | current |
| Node.js | ≥ 24.10 | 24.22.2 (Maintenance LTS), 26.13.0 | floor OK; setup-node missing (M8) |
| semantic-release | 25.0.9 | 25.0.9 latest (26.0.0-beta.6 exists) | current; a major is coming |
| @commitlint/cli | 21.2.4 | 21.2.4 | current |
| jscpd | 5.4.2 | 5.4.2 (2026-10-20) | current, fits |
| actionlint | v1.7.12 | v1.7.12 (2026-03-30); upstream inactive | **doesn't fit** (H1) |
| zizmor | v1.32.0 | v1.32.0 (2026-11-02) | current; default policy conflicts (H2) |
| actions/checkout | v7.0.1 | v7.0.1 | current |
| actions/setup-dotnet | v6.1.0 | v6.1.0 (2026-11-03) | current |
| actions/create-github-app-token | v3.3.0 | v3.3.0 (2026-10-12) | current (L1) |
| github/codeql-action | v4.39.3 | v4.39.3 (2026-11-04) | current (Builds uses v4.39.1 today) |
| NuGet/login | v1.2.0 | v1.2.0 (2026-04-24) | current; placement wrong (C1) |
| Dapr runtime | 1.19.1 | runtime 1.19.1 (2026-10-31), CLI 1.19.1 | current; Builds pins 1.18.7 today (L6) |
| Runner (`$/`) | ≥ 2.336.0 | 2.338.2 (2026-10-26) | satisfied on hosted runners |

**Counts:** 2 critical, 5 high, 9 medium, 9 low.
