# Review (update gate): verification of the revised Hexalith.CiCd spine

- **Spine:** `../ARCHITECTURE-SPINE.md` (draft, updated 2026-11-08, AD-1..AD-21), revised from the validate findings I-1..I-12 and validate-D1..D4.
- **Memlog:** `../.memlog.md`, entries from line 111 ("Update run 2026-11-08") to line 137.
- **Earlier review:** `review-verification-validate.md` (V-1..V-13). Its closure status is in the section "Earlier V-* findings" below.
- **Lens:** was every committed decision checked against the web, the existing project or the live platform, rather than asserted from training data? This covers current versions, whether each named technology still exists and fits, and the platform behaviour the ADs rely on.
- **Date:** 2026-11-08
- **Method:**
  - **GitHub docs from source** (`gh api repos/github/docs/contents/...`):
    - `deployments-and-environments.md`, `control-deployments.md`, `review-deployments.md` and the environments reusable;
    - `workflow-syntax.md`, `dependency-caching.md`, `contexts.md`, `reuse-workflows.md` and `events-that-trigger-workflows.md`;
    - `limits.md`, the REST rate-limit reusables and the concurrency reusable;
    - `immutable-releases.md`, `prevent-release-changes.md`, the artifact-retention reusable and `skip-workflow-runs.md`;
    - the feature flags `actions-cache-mode`, `actions-environments-without-deployments` and `actions-nga`;
    - the App permission data (`server-to-server-permissions.json`).
  - **GitHub's OpenAPI description** (`github/rest-api-description`): release, artifact and workflow-run schemas; release create and update; workflow dispatch; fork-approval and ruleset schemas.
  - **Changelogs:** cache-mode GA (2026-09-10); retention extended to runs, checks and statuses (2026-07-17).
  - **Source at the pinned tags:**
    - `actions/create-github-app-token@v3.3.0`: `action.yml`, `README.md`;
    - `actions/download-artifact@v8.0.2`: `action.yml`, `src/download-artifact.ts`;
    - `actions/upload-artifact@v7.0.2`: `action.yml`;
    - `actions/toolkit`: `packages/artifact/src/internal/upload/retention.ts`;
    - `actions/setup-node@v7.1.0`, `astral-sh/setup-uv@v10.3.3`, `actions/setup-python@v7.1.0`, `actions/setup-dotnet@v6.1.0`;
    - `github/codeql-action@v4.39.3`: `init`, `analyze`;
    - zizmor v1.32.0 docs (`usage.md`, `audits.md`);
    - uv 0.13.7 `docs/guides/scripts.md`;
    - NuGetGallery `GitHubTokenPolicyValidator.cs`, `CredentialBuilder.cs` and migration `202608031928454_AddFederatedCredentialPolicyScopes`;
    - NuGet docs `trusted-publishing.md` and its history;
    - `semantic-release/github` `lib/publish.js`.
  - **Experiments,** all in the scratchpad `verification-update/`:
    - `actionlint` 1.7.12 with and without the three ignores, plus canary errors;
    - `uvx zizmor@1.32.0`, offline and online, with the spine's config, on sample callers, reusable workflows, a composite and a CiCd-like tree with `rendered/`;
    - `uvx --from uv==0.13.7 uv lock --script`, then `uv run --locked`, then a dependency change;
    - `npm ci --ignore-scripts`, then `npm audit signatures`, with the five npm Stack pins;
    - SDK 10.0.403: `dotnet build` and `dotnet pack` with `-noAutoResponse`, `-p:RestoreConfigFile` and `-warnaserror:NU1900;NU1903;NU1904;NU1905` against a vulnerable package, a `Directory.Build.rsp` and a bogus `auditSources`; `dotnet test` in VSTest and MTP mode.
  - **Live `gh`, read-only:**
    - releases and latest tags for every GitHub-hosted Stack row; the npm and PyPI registries; .NET `releases-index.json`; the Node.js `schedule.json`; runner-images READMEs; python-versions manifest;
    - org and repo artifact retention; environments and branch policies (Commons); immutable-releases status; release objects (`immutable`); artifacts (`digest`, `expires_at`);
    - workflow runs (`head_sha`, `event`, `referenced_workflows`, runs older than 30 days); a draft without a tag;
    - nuget.org search for packages owned by Hexalith.
  - **Brownfield:** `references/*`. Only 13 of 18 checkouts equal live `main` today: Builds, EventStore, McpCli, Parties and Platform moved during the day (Builds by one commit, a manifest validator). Where it mattered, the evidence below was taken live.

## Verdict

The revision's platform bets mostly hold, and every Stack pin is still the latest on 2026-11-08. The checks that hold are:

- environments on Free public repos, with branch policy `main`, secrets scoped to the job, and use from `schedule`, `workflow_dispatch` and `push`;
- the caller-job environment with nuget.org environment matching;
- `cache-mode` GA;
- immutable releases and the REST `immutable` flag;
- the inputs of the App-token, artifact and setup actions;
- `uv lock --script` with `--locked`, `npm ci --ignore-scripts` with `npm audit signatures`, and the dotnet audit flags;
- actionlint's three ignores.

One behaviour the revision now depends on was treated as an open spike, although GitHub documents it. `GITHUB_TOKEN` can't publish a draft whose commit differs from `main` in `.github/workflows/`, and every Builds bump rewrites the module callers. So the Deferred App fallback is certain for every draft completed after a bump. Two live facts also contradict the text:

- the org's artifact retention is 30 days, not 90;
- nuget.org policies can now be scoped to package IDs, which settles a Deferred check.

**Counts:** 0 critical, 1 high, 3 medium, 7 low.

---

## Claims checked

### Platform behaviour the revision relies on

| # | Claim | Spine location | Status | Evidence |
| --- | --- | --- | --- | --- |
| P1 | Environments on GitHub Free public repos: deployment branch policy limited to `main` | AD-7; AD-21; Seed | **holds.** "Deployment branches and tags are available for all public repositories." The rule is matched against `GITHUB_REF`. It is live in Commons: environment `production` with branch policy `main`, used by successful `release.yml` dispatches on `main`. All 18 repos and CiCd are public; the plan is `free`. | `deployments-and-environments.md` "Deployment branches and tags"; `gh api repos/Hexalith/Hexalith.Commons/environments/production/deployment-branch-policies`; `gh api repos/Hexalith/Hexalith.CiCd --jq .visibility` |
| P2 | Environment secrets and variables reach only the jobs that reference the environment | AD-7; Conventions "Secrets and variables" | **holds.** Docs: "Secrets stored in an environment are only available to workflow jobs that reference the environment." Variables are read through `vars` only. On Free, environment secrets are available in public repos only, which all of these repos are. | `deployments-and-environments.md` "Environment secrets", "Environment variables" |
| P3 | `cicd-app` used from `schedule`, `workflow_dispatch` and `push` runs on `main` | AD-6; AD-18 | **holds.** `GITHUB_REF` is the default branch for `schedule`, the dispatched branch for `workflow_dispatch`, and `refs/heads/main` for a push to main. All three match a `main` branch rule. A `pull_request` ref (`refs/pull/N/merge`) does not, and the `deliver` job is `main`-only anyway. | `events-that-trigger-workflows.md` (`schedule`, `workflow_dispatch` tables) |
| P4 | Environment on the caller's `publish` job, which runs a composite step, not on a reusable call | AD-17; AD-19 | **holds, and the spine avoids the trap.** The job that calls a reusable workflow "can't use the `environment` keyword". Environment secrets inside a reusable workflow must be passed by the caller, and zizmor documents that they "do not interact correctly with reusable workflows unless the caller workflow uses `secrets: inherit`". The spine puts `hexalith-release` on a top-level job, and Builds' `builds-release.yml` does the same, so neither case arises. Commons already runs this shape: `environment: production`, `id-token: write`, `NuGet/login@v1.2.0`. | `reuse-workflows.md:75-82`; zizmor `audits.md` `secrets-outside-env` note; `references/Hexalith.Commons/.github/workflows/release.yml:73-107` |
| P5 | Jobs referencing an environment create deployments | AD-6 (hourly `deliver`), AD-18 (5 App jobs a night) | **info.** Each run adds deployment records to `cicd-app`, about 30 a day. `environment: {name: cicd-app, deployment: false}` (fpt, documented 2026-03-19) keeps the secrets and the reviewers and skips the record. Whether it keeps the OIDC `environment` claim is undocumented, so don't use it on `hexalith-release`. actionlint 1.7.12 accepts the key (experiment). | `control-deployments.md` "Using environments without deployments"; `data/features/actions-environments-without-deployments.yml` |
| P6 | nuget.org policy names an environment, matched against the OIDC `environment` claim | AD-7; AD-21 | **holds.** The validator checks the environment only if the policy sets it, case-insensitively against the `environment` claim, after requiring `job_workflow_ref` to start with `{owner}/{repo}/.github/workflows/`. The file has been unchanged since `63b66c9828` (2026-10-01). | https://github.com/NuGet/NuGetGallery/blob/main/src/NuGetGallery.Services/Authentication/Federated/GitHubTokenPolicyValidator.cs (lines 264-301) |
| P7 | Whether nuget.org policies can scope package IDs | Deferred "Story 1 checks"; memlog l.124, l.136 | **answered: yes, since August 2026** (U-V3). The docs gained "Select Scopes … glob pattern … define which packages the policy applies to" on 2026-08-24. In the Gallery, `CreateShortLivedApiKey` copies the policy's scopes, or grants the all-inclusive pattern for the owner when none are set. | NuGet docs commit `529631d4e` (https://github.com/NuGet/docs.microsoft.com-nuget/commit/529631d4e); NuGetGallery `CredentialBuilder.cs:55-62`, migration `202608031928454_AddFederatedCredentialPolicyScopes.cs` |
| P8 | Immutable releases enabled per repo | AD-19; AD-21 step 3 | **holds.** It is a repo setting, and an org policy for all or selected repos also exists. It "will only apply to future releases". `GET /repos/{o}/{r}/immutable-releases` needs Administration read, which the App has. Builds today: `{"enabled":false}`. | `prevent-release-changes.md`; `server-to-server-permissions.json`; `gh api repos/Hexalith/Hexalith.Builds/immutable-releases` |
| P9 | A draft release is still editable | AD-17 (drafts created, completed, deleted) | **holds.** Only published releases are locked. GitHub's recommended flow is draft, attach assets, publish. | `immutable-releases.md` "Best practices" |
| P10 | Publishing the draft creates `v<version>` last | AD-17 step 5 | **holds only if no such tag exists** (U-V4). The OpenAPI says `target_commitish` is "Unused if the Git tag already exists". Live: the Security_OLD draft `v1.0.0` has no tag ref. | OpenAPI `repos/update-release` body; `gh api repos/Hexalith/Hexalith.Security_OLD/git/ref/tags/v1.0.0` → 404 |
| P11 | What becomes immutable | AD-10 | **holds.** The tag can't be moved or deleted while the release exists, and assets can't change. Title and notes stay editable. A deleted immutable release's tag name can't be reused. | `immutable-releases.md` |
| P12 | The REST release object exposes an immutable flag the bump can check | AD-10 "published and immutable" | **holds.** `release.immutable` (boolean) is in the OpenAPI. Live: Builds `v4.44.13` has `immutable:false`; zizmor `v1.32.0` has `immutable:true`. | OpenAPI `components.schemas.release`; `gh api repos/Hexalith/Hexalith.Builds/releases/latest --jq .immutable` |
| P13 | Effect on legacy `@semantic-release/github` asset uploads | memlog l.125 (reason for enabling immutability only after adoption) | **the rationale is out of date; the rule is harmless.** 12.0.10 (used by 15 repos) creates a draft, uploads assets, then publishes whenever assets are set, which works under immutability. No other legacy step edits releases after publishing (grep of workflows and `Github/`). | https://github.com/semantic-release/github/blob/master/lib/publish.js (lines 61-170); `references/*/package.json`, `.releaserc.json` |
| P14 | `cache-mode: none` at workflow and job level, GA on github.com | AD-17; Conventions | **holds. GA on all plans** (changelog 2026-09-10), dotcom only (not GHES). It is enforced "with scoped cache tokens", and a skipped restore or save logs and continues. A called workflow can't exceed an explicit caller limit (`none` ≤ `none`). zizmor added support in 1.31+ (#2380, closed 2026-10-02). | https://github.blog/changelog/2026-09-10-control-github-actions-cache-access-with-cache-mode/ ; `data/features/actions-cache-mode.yml`; `dependency-caching.md:285-323` |
| P15 | `create-github-app-token` v3.3.0: inputs `client-id`, `owner`, `repositories`, `permission-administration`, `-contents`, `-workflows`, `-actions`, `-security-events` | AD-7 | **holds.** All present in `action.yml@v3.3.0`; `app-id` is deprecated. | https://github.com/actions/create-github-app-token/blob/v3.3.0/action.yml |
| P16 | 1-hour token life; revocation at job end; re-minting within a job | AD-7; AD-18 | **holds,** with a mechanics gap (U-V6). README:16: "expires after 1 hour". README:436: revoked in the `post` step unless `skip-token-revoke`. Re-minting means another action step; stdlib Python can't sign the App JWT (RS256). | `README.md@v3.3.0` |
| P17 | `download-artifact` v8.0.2 by `artifact-ids` from another run (`run-id`, `github-token`) | AD-17 `publish` step 1; complete mode | **holds.** With a token, it lists the artifacts of `run-id` in `repository` and keeps only the listed IDs, so the ID is bound to the run. It passes the server digest as `expectedHash`, and `digest-mismatch` defaults to `error`. `name` and `artifact-ids` are mutually exclusive. A cross-run download needs `actions: read`, which `publish` has. | `action.yml@v8.0.2`; `src/download-artifact.ts@v8.0.2:103-190` |
| P18 | Artifact `digest` in REST and in upload-artifact v7 outputs | AD-17 `build` outputs, `publish` check | **holds.** OpenAPI `artifact.digest` ("SHA256 … upload-artifact v4 or newer"); live `digest: "sha256:…"`. upload-artifact v7.0.2 outputs `artifact-id` and `artifact-digest`, and has `overwrite`. | OpenAPI `components.schemas.artifact`; `gh api repos/Hexalith/Hexalith.Builds/actions/artifacts`; `action.yml@v7.0.2` |
| P19 | Artifact retention of 90 days; is 90 the public-repo maximum? | AD-17 `build`; Conventions "Release markers"; Seed "Quotas" | **90 is the public maximum, but the org is set to 30** (U-V2). The org has `{"days":30}` and every repo `{"days":30,"maximum_allowed_days":30}`. Live Builds artifacts expire 30 days after creation. The toolkit clamps `retention-days` to the repo maximum with a warning. From 2026-10-01 the same setting also governs runs, checks and statuses (announced). Runs from 2026-08-31 are still listed, so it is not yet observed. | `about-artifact-log-retention.md`; https://github.blog/changelog/2026-07-17-actions-retention-will-cover-checks-workflow-runs-and-statuses/ ; `gh api orgs/Hexalith/actions/permissions/artifact-and-log-retention`; toolkit `retention.ts` |
| P20 | `GITHUB_TOKEN` pushes a commit to CiCd `main` that changes only `builds-version` and `rendered/`, including `rendered/<X>/.github/workflows/*.yml` | AD-18 `bump-push`; AD-18 `keepalive` | **unverified** (U-V5). The docs and OpenAPI state the workflow restriction only for files "under `.github/workflows/`" from the repo root. The git-push check is undocumented for nested paths. No public example was found either way, and a test would need a push. | OpenAPI `repos/create-release` note; web searches (none conclusive) |
| P21 | `GITHUB_TOKEN` `workflow_dispatch` of another workflow in the same repo creates a run | AD-8 restore; AD-18 `bump-push` | **holds.** "`workflow_dispatch` and `repository_dispatch` events always create workflow runs." The dispatch API now also takes `return_run_details` (info: it returns the run ID, which `wait` can use). | `data/reusables/actions/actions-do-not-trigger-workflows.md`; OpenAPI `actions/create-workflow-dispatch` |
| P22 | `GITHUB_TOKEN` calls the enable-workflow API on its own repo | AD-18 `keepalive` | **holds.** `PUT …/workflows/{id}/enable` needs Actions write (`actions: write`). Whether it resets the 60-day timer is still unknowable (Deferred, unchanged). | `server-to-server-permissions.json` (`enable-a-workflow`); `events-that-trigger-workflows.md:967` |
| P23 | `GITHUB_TOKEN` can't create or publish a release whose target differs from `main` under `.github/workflows/` | AD-17 steps 3-5; Deferred bullet 1 | **holds, and it applies to every completion after a bump** (U-V1). This is documented for both create and update. A community report shows that a `GITHUB_TOKEN` tag on an older, unmodified commit is refused for the same reason. | OpenAPI `repos/update-release`; https://github.com/orgs/community/discussions/26164 |
| P24 | `uv lock --script` plus `uv run --locked` for a PEP 723 script at uv 0.13.7 | AD-11 | **holds** (experiment, uv 0.13.7). It writes `render.py.lock` with hashes and upload times for 9 packages; `uv run --locked --script` runs; after a pin change, `--locked` exits 1 ("needs to be updated, but `--locked` was provided"). | uv `docs/guides/scripts.md@0.13.7:274-290`; scratch `uvexp/` |
| P25 | `npm ci --ignore-scripts`, then `npm audit signatures` | AD-11 | **holds** (experiment, npm 11.18). Five pins, 495 packages; "495 packages have verified registry signatures, 134 … verified attestations"; exit 0. | scratch `npmexp/` |
| P26 | `-noAutoResponse` and `-p:RestoreConfigFile=<file>` accepted by `dotnet build` and by `dotnet pack`'s implicit restore; `-warnaserror:NU1900;NU1903;NU1904;NU1905` | AD-12; AD-17 `build`; Conventions "SDK and build" | **holds** (experiment, SDK 10.0.403). `build` and `pack` both accept them. `RestoreConfigFile` replaces the local `nuget.config`, including a bogus `auditSources`. A high-severity package fails with `error NU1903` despite `WarningsNotAsErrors`. A broken audit source fails with `NU1900`/`NU1905`. `dotnet test` accepts both flags in VSTest and MTP mode (see U-V8). All 8 module `nuget.config` files list only nuget.org; Agents and Memories also set `signatureValidationMode=require`, which Builds' config replaces. | scratch `dn/`; `references/*/nuget.config` |
| P27 | setup-node v7.1.0 `package-manager-cache`; setup-uv v10.3.3 `enable-cache` | AD-17 | **holds.** setup-node `package-manager-cache` defaults to `true`. setup-uv `enable-cache` defaults to `auto`, which caches on `workflow_dispatch`. Both `false` values are valid. setup-dotnet `cache` defaults to `false`. | `action.yml` at each tag |
| P28 | actionlint 1.7.12 ignores for `$/`, `job.workflow_*` and `cache-mode` | Conventions "Action references" | **holds** (experiment). Without ignores it reports 7 errors. The patterns `unexpected key "cache-mode" for "(workflow\|job)" section`, `specifying action "\$/` and `property "workflow_(ref\|sha\|repository\|file_path)" is not defined in object type` clear exactly those 7. Canary errors (`timeout-minute`, `job.workflow_refx`) are still reported. actionlint also skips `rendered/**` unless the files are passed explicitly (U-V7). | scratch `lint/`; `/home/administrator/.local/bin/actionlint` |
| P29 | zizmor v1.32.0 online audits (`impostor-commit`, `known-vulnerable-actions`, `ref-confusion`, `stale-action-refs`): which token? | Conventions; AD-3 global checks "no secrets" | **holds.** Online mode starts when `GH_TOKEN`, `GITHUB_TOKEN` or `ZIZMOR_GITHUB_TOKEN` is set. The token is used "primarily … for rate-limited API requests", so `github.token` in a job with no secrets suffices for public actions. With the spine's config: offline, no findings on callers, a reusable `release.yml` with `cache-mode`, `$/` and `job.workflow_*`, or an App-token job; online, it ran and flagged only a canary. zizmor skips `rendered/**` when given `.` (U-V7). | zizmor `usage.md@v1.32.0:166-245`; `audits.md`; scratch `lint/`, `cicdsim/` |
| P30 | codeql-action v4.39.3 per-language matrix, `build-mode: none` | AD-18 | **holds.** `build-mode` is "only available when analyzing a single CodeQL language per job, for example using a matrix". `none` covers C#, and `wait-for-processing` defaults to `true`. An empty matrix (`codeql: []`) fails rather than skips (U-V9, community-reported). | `init/action.yml@v4.39.3:32-41`; `analyze/action.yml` |
| P31 | Workflow-runs API by `head_sha` and `event`; `referenced_workflows` | AD-16; AD-17 complete mode; AD-18 `delivery-wait` | **holds.** The filters work; `event` takes one value, so two queries. `referenced_workflows[]` gives `path@ref`, `sha` and `ref` (live). Commons' `main` head `chore(release): 2.30.10 [skip ci]` has only `schedule` and `dynamic` runs and no `push` run (U-V10). | `gh api repos/Hexalith/Hexalith.Commons/actions/runs?head_sha=…&event=push`; OpenAPI `workflow-run.referenced_workflows` |
| P32 | Draft listing | AD-16 `resolve`; AD-17 `publish` "still marked" | **info.** "Only users with push access will receive listings for draft releases." `resolve` needs `contents: write` to find a marked draft; the spine gives it no stated permissions. | OpenAPI `repos/list-releases` |
| P33 | Quotas: Free 20 concurrent jobs; 6 h a job; App at least 5,000 req/h; `GITHUB_TOKEN` 1,000 req/h per repo | Seed "Quotas" | **holds.** The App limit scales by 50 per repo over 20, up to 12,500. Pending runs: the default `queue: single` cancels an older pending run in a group, and `queue: max` (fpt) would queue up to 100. The spine's "a pending run may be superseded" matches the default. | `limits.md:29-70`; `primary-rate-limit-*.md`; concurrency reusable |
| P34 | What the App can read for AD-21 | AD-3 per-module App checks | **holds.** Environment and branch policies need Actions read. Retention, fork approval and immutable releases need Administration read. Environment secret names need "Environments" read, which the App doesn't hold, so they stay on the manual checklist. | `server-to-server-permissions.json` |
| P35 | Fork-PR approval for "all external contributors"; ruleset `update` rule with an App bypass | AD-21 | **holds.** `approval_policy` enum includes `all_external_contributors`. `repository-rule-update` ("Only allow users with bypass permission to update matching refs") exists, and so does bypass `actor_type: Integration` (see U-V11). | OpenAPI schemas |

### Stack (spot check, 2026-11-08)

All rows are the latest stable releases today. The three new rows are marked.

| Row | Spine | Latest today | Evidence |
| --- | --- | --- | --- |
| .NET SDK | 10.0.403 (global.json, `latestPatch`) | 10.0.403 (2026-10-25). 16 of 17 .NET repos plus Builds pin it. .NET 11 is at RC3 "go-live"; `latestPatch` keeps 10.0.4xx. | `releases-index.json`; `references/*/global.json` |
| Python | ≥ 3.12 (26.04: 3.14.4) | Ubuntu 26.04 image 20261101 ships Python 3.14.4 and Node 24.22.2. The `ubuntu-latest` move is still in progress (runner-images #14748 open). python-versions has 3.12.16 for 26.04. | runner-images READMEs; python-versions manifest |
| `actions/setup-python` (**new**) | v7.1.0 | v7.1.0 (2026-10-22) | `releases/latest` |
| uv / `setup-uv` | 0.13.7 / v10.3.3 | 0.13.7 / v10.3.3 | `releases/latest` |
| Jinja2 / PyYAML / jsonschema | 3.1.6 / 6.0.3 / 4.26.0 | same | PyPI |
| Node.js / setup-node | 24 / v7.1.0 | 24 has been Maintenance LTS since 2026-10-20 (26 is Active LTS); setup-node is v7.1.0 | `schedule.json`; `releases/latest` |
| commit-analyzer / release-notes-generator | 13.0.1 / 14.1.1 | same | npm |
| `@commitlint/cli` / `@commitlint/config-conventional` (**new**) | 21.2.4 / 21.2.4 | same (2026-10-18). Body, footer and header limits are 100; Builds overrides body and header to 200. | npm; `node_modules/@commitlint/config-conventional/lib/index.js`; live `commitlint.config.mjs` |
| jscpd | 5.4.3 | 5.4.3 (2026-11-08) | npm |
| actionlint / zizmor | v1.7.12 / v1.32.0 | same (zizmor-action v0.8.1) | `releases/latest` |
| checkout / setup-dotnet / upload-artifact / download-artifact | v7.0.1 / v6.1.0 / v7.0.2 / v8.0.2 | same | `releases/latest` |
| create-github-app-token / codeql-action / NuGet/login | v3.3.0 / v4.39.3 / v1.2.0 | same (codeql bundle 2.27.4) | `releases` |
| Dapr runtime / CLI (**CLI new**) | 1.19.1 / 1.19.1 | same. The Builds pins are still 1.18.7 and 1.18.2 (`Props/Directory.Packages.props:30-31`), as the Deferred item says. Dapr .NET SDK 1.19.0 is the latest. | `releases/latest`; nuget.org |
| Runner | ≥ 2.336.0 | v2.338.2 | `releases/latest` |

---

## Findings

### High

#### U-V1 (high): AD-17 complete mode publishes with `GITHUB_TOKEN` a draft that is behind `main` in `.github/workflows/` after every bump, so the "spike" fallback is certain

- **Location:** AD-17, "Complete mode" and `publish` step 5 ("Publish the draft"). Deferred bullet 1 ("If the spike confirms it: … a run whose publication is refused ends `ready` after pushing, and `nightly.yml` publishes the draft with the App before the bump"). AD-18 `bump` and `bump-push`.
- **Issue:** validate-D1 A makes a later run complete a stuck draft from the run that built it (memlog l.112). That draft's `target_commitish` is an older release SHA. Every Builds bump changes the module's rendered `ci.yml` and `release.yml` (`uses: …@vX.Y.Z`), and the last three Builds releases were on 2026-11-06, 11-07 and 11-08. So whenever a completion happens, `main`'s workflows almost always differ from the draft commit's.
- **Evidence:**
  - OpenAPI `repos/update-release`: "If the resolved target commit … adds or modifies any file under `.github/workflows/` relative to the repository's default branch, the authenticating token must be authorized to modify workflows … The `GITHUB_TOKEN` available to GitHub Actions cannot be authorized for this."
  - Community report https://github.com/orgs/community/discussions/26164: `GITHUB_TOKEN` tags on older commits were refused with "refusing to allow a bot to create or update workflow", although the poster had not touched the workflow. The check compares content with the default branch head.
  - Builds release cadence: `gh api repos/Hexalith/Hexalith.Builds/releases`.
- **Failure it allows:**
  - The question the story-3 spike is meant to answer is already documented.
  - If the implementer treats the fallback as optional ("if the spike confirms it"), every completion fails at step 5 after the packages are pushed. The outcome is `failed`, the draft stays marked, and the next night repeats. That is the I-1 freeze, the critical issue D1 was chosen to fix.
  - The fallback also changes CAP-13, and that spec update hasn't been raised.
- **Smallest fix (AD-17, replacing the conditional in Deferred bullet 1):**
  > "`publish` step 5 publishes with `GITHUB_TOKEN` only when the draft's SHA has the same `.github/workflows/` tree as `main`. Otherwise, which is always the case for a completion after a bump, the run ends `ready` after pushing, and `nightly.yml`'s `wait` job publishes that draft with the App (Contents and Workflows write on that repo) before `bump`. The same applies when draft creation is refused."

  Keep only the composite and `NuGet/login` items as story-3 spikes, and raise the CAP-13 change as a spec update now.

### Medium

#### U-V2 (medium): The org's artifact retention is 30 days, not 90, and GitHub is extending retention to workflow runs

- **Location:** AD-17 `build` ("kept 90 days") and complete mode ("the run named by `hexalith-release-run:`"); Conventions "Release markers" ("kept 90 days"); Seed "Quotas" ("artifacts kept at most 90 days"); AD-16 (green CI reads the run for the release SHA).
- **Evidence:**
  - `gh api orgs/Hexalith/actions/permissions/artifact-and-log-retention` returns `{"days":30,"maximum_allowed_days":400}`.
  - Builds, CiCd, Commons, EventStore and Parties each return `{"days":30,"maximum_allowed_days":30}`.
  - Live Builds artifacts created 2026-11-08 have `expires_at` 2026-12-08.
  - The toolkit's `retention.ts` clamps any `retention-days` above `GITHUB_RETENTION_DAYS`, logging "Using 30 instead".
  - The docs allow 1 to 90 days on public repos.
  - Changelog 2026-07-17: from 2026-10-01, "checks, workflow runs, and statuses" are removed once they pass the same retention period. Live, runs from 2026-08-31 are still listed in Builds and Parties, so deletion isn't observed yet.
- **Failure it allows:**
  - A stuck draft can be completed for 30 days, not 90.
  - Once run deletion is enforced, the run that complete mode must verify can vanish, and AD-17 has no rule for a missing run, so the run could fail red every night.
  - AD-16 would also see "no run" for a quiet module whose last CI run aged out, for example a month without a Builds release or a module kept out by `builds-skip`. It would fail "main is red" every night.
- **Smallest fix:**
  - **AD-21, "Once, before the first adoption":** "set the org's Actions artifact and log retention to 90 days, the public-repo maximum".
  - **AD-3, per-module checks with the App:** add "the repo's artifact and log retention is 90 days". `GET …/actions/permissions/artifact-and-log-retention` needs Administration read, which the App holds.
  - **AD-17, complete mode:** "A `hexalith-release-run:` run that no longer exists counts as a run with no `release` artifact."
  - **Conventions:** "kept 90 days (the org retention)".

#### U-V3 (medium): nuget.org policies can now be scoped to package IDs, so the Deferred story-1 check is already answered

- **Location:** Deferred, "Story 1 checks" ("If a nuget.org Trusted Publishing policy can scope package IDs, each policy is scoped to its module's prefix"); AD-7 "Publish credentials"; AD-21 step 1 (nuget.org policy).
- **Evidence:**
  - NuGet docs commit `529631d4e` (2026-08-24, "Add Scope Support to OIDC") adds "Select Scopes … The associated glob pattern can be used to target specific packages and define which packages the policy applies to".
  - The Gallery stores the scopes on the policy (migration `202608031928454_AddFederatedCredentialPolicyScopes`). `CreateShortLivedApiKey` copies them, or grants `NuGetPackagePattern.AllInclusivePattern` with `NuGetScopes.All` for the owner when none are set.
  - The Hexalith owner holds 200+ packages, many from repos outside the 17 (Infrastructure 53, Application 16, Documents 14, …): nuget.org search `owner:Hexalith`.
- **Failure it allows:** without scopes, any module's `hexalith-release` job can push new versions of every Hexalith package, including other modules' packages and the unmanaged repos' packages. The spine leaves the check to story 1, so story 1 may skip it.
- **Smallest fix:**
  - **AD-21 step 1:** "… and the nuget.org policy for `release.yml` naming it, scoped to the module's package-ID glob (for example `Hexalith.Commons*`), for pushing new versions of existing packages only."
  - **AD-19:** the same scoping for Builds' `Hexalith.Builds*` packages.
  - **Deferred:** delete the nuget half of "Story 1 checks".
  - A module that adds an ID outside its glob fails its first push, which is red and visible.

#### U-V4 (medium): Publishing binds the release to any existing `v<version>` tag, so "creates `v<version>` last" can attach to a commit that was not built

- **Location:** AD-17 `publish` steps 1 and 5; AD-16 "Marked draft" (`tag_name` above the last `v*` tag reachable from the SHA).
- **Evidence:**
  - OpenAPI, `repos/create-release` and `repos/update-release`: `target_commitish` is "Unused if the Git tag already exists."
  - Tag creation isn't restricted: the Deferred "Story 1 checks" item covers it, and AD-21 rulesets block only update and deletion of `v*`.
  - Module-agent tokens hold Contents write (AD-7), so they can push tags.
  - The marked-draft rule only looks at tags reachable from the SHA. A stray tag on another commit is invisible to it.
- **Failure it allows:**
  - A stray `v1.4.0` tag on any commit is enough. Publishing draft `v1.4.0` (target = release SHA) attaches the release to the stray commit. Immutability then locks that wrong tag, which can't be deleted while the release exists.
  - The packages on nuget.org were built from a different commit.
  - The next night computes `v1.4.0` again, because the stray tag isn't reachable from `main`. Draft creation then collides with the existing tag, and the module is red until someone repairs it by hand.
- **Smallest fix:**
  - **AD-17 `publish` step 1:** add "and that no tag `v<version>` exists, or that it points at `sha`".
  - **AD-17 step 5:** add "then check that `v<version>` resolves to `sha`; otherwise fail with 'tag vX.Y.Z does not point at the built commit'".
  - **Conventions "Fixed messages":** add the message.

### Low

- **U-V5 (low): the `GITHUB_TOKEN` push of `rendered/<X>/.github/workflows/*.yml` is unverified.**
  - **Location:** AD-18 `bump-push` (memlog l.120 assumes only top-level `.github/workflows/` is protected).
  - **Evidence:** the docs and OpenAPI describe the restriction only for files "under `.github/workflows/`" from the root. The git-side check for nested paths is undocumented. Web searches found nothing either way, and testing needs a push, which this review may not do.
  - **Failure it allows:** if GitHub matches the nested path, every bump push is refused and `builds-version` never moves.
  - **Fix:** in Deferred, add "Story 8 check: a `GITHUB_TOKEN` push changing only `rendered/<X>/.github/workflows/*.yml` is accepted. If not, `bump-push` runs in `cicd-app` with an App token scoped to CiCd `contents: write` (stdlib and git, as AD-7 allows). Its push then triggers `deliver.yml` and the explicit dispatch is dropped."
- **U-V6 (low): re-minting mechanics are left implicit.**
  - **Location:** AD-7 ("a longer job mints again"); AD-18 `wait` (≤ 5 h) and `delivery-wait` (≤ 90 min).
  - **Evidence:** `create-github-app-token` is a step with a `post` revocation. A `cicd-app` job runs only stdlib Python, which has no RS256 signing to mint a token itself.
  - **Fix:** in AD-7, add "A longer job is a fixed sequence of steps, each a `create-github-app-token` mint followed by a script step that ends within 50 minutes. Later pairs are skipped once the work is done."
- **U-V7 (low): actionlint and zizmor don't pick up `rendered/**` by default.**
  - **Location:** AD-3 global checks ("actionlint and zizmor over CiCd's workflows and `rendered/**`").
  - **Evidence:**
    - actionlint with no arguments lints only the root `.github/workflows/`.
    - `zizmor .` (also with `--collect=all`) audits the root workflows and every `action.yml`, but skips `rendered/<X>/.github/workflows/ci.yml`.
    - `zizmor rendered/` and an explicit actionlint file list both lint them, and the spine's config passes on a rendered caller (scratch `cicdsim/`).
  - **Fix:** in AD-3, "… actionlint and zizmor over CiCd's workflows and, passed by path, `rendered/*/.github/workflows/*.yml`".
- **U-V8 (low): `dotnet test` runs in Microsoft.Testing.Platform mode in 16 of 17 .NET repos and Builds.**
  - **Location:** AD-13 (projects run one by one); AD-8 audit lint; AD-15.
  - **Evidence:**
    - `"test": {"runner": "Microsoft.Testing.Platform"}` is in `references/*/global.json` (Tenants, Commons, Agents, Timesheets, Folders, FrontComposer, Conversations, Builds, EventStore, PolymorphicSerializations, Works, McpCli, Projects, Platform, Memories, Parties).
    - In that mode a project is passed as `--project <csproj>`; the positional form is VSTest syntax (Learn, "Migrate to MTP mode").
    - The MSBuild property `TestingPlatformCommandLineArguments` injects test-app arguments, including filters. No module uses it today.
    - `-noAutoResponse` and `-p:` are accepted in MTP mode (experiment).
  - **Failure it allows:** a classifier written for `dotnet test <path>` breaks, or a module prop silently filters tests, which is the module-owned skip AD-13 forbids.
  - **Fix:**
    - AD-13: "The classifier runs each project with `dotnet test --project <path>` in MTP mode, or positionally in VSTest mode."
    - AD-8 audit lint: add "no `TestingPlatformCommandLineArguments` or `VSTestTestCaseFilter`".
- **U-V9 (low): `codeql: []` is an empty matrix, and an empty matrix fails the run.**
  - **Location:** AD-3 ("`[]` skips analysis"); AD-18 `codeql` matrix.
  - **Evidence:** GitHub rejects a matrix with no values. This is community-reported (for example the rust-lang CI workaround), not in GitHub's docs. The usual fix is a job-level `if:` on the list.
  - **Fix:** in AD-18, "`codeql` runs only when the language list is non-empty; otherwise it is skipped."
- **U-V10 (low): `[skip ci]`-family markers suppress push CI.**
  - **Location:** AD-8 (the guard is stage 1 of every CI run); AD-16 ("no run: fail").
  - **Evidence:**
    - `skip-workflow-runs.md`: `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, `[actions skip]` and the trailer `skip-checks: true` stop `push` and `pull_request` runs.
    - Live: Commons' `main` head (`chore(release): 2.30.10 [skip ci]`) has no `push` run.
  - **Failure it allows:** a module-agent push carrying a marker skips the guard for that push, and its release stays red ("main is red") until the next commit.
  - **Fix:**
    - Conventions "Commit types": add "Builds' commitlint config rejects skip markers and `skip-checks` trailers."
    - The instruction block forbids them on direct pushes.
- **U-V11 (low): the `delivered/**` ruleset dropped "update".**
  - **Location:** AD-21 ("a ruleset on `delivered/**` that blocks creation, deletion and force-push, with the App as its only bypass"). Memlog l.104 (validate-pass D1 A) says it "lets only the App update".
  - **Evidence:** the ruleset rule type `update` ("Only allow users with bypass permission to update matching refs") exists, and so does bypass `actor_type: Integration` (OpenAPI).
  - **Failure it allows:** any CiCd writer, including a `GITHUB_TOKEN` with `contents: write` in `bump-push` or `keepalive`, can fast-forward `delivered/<Repo>` to an unvalidated commit. The guard and restore then enforce it.
  - **Fix:** in AD-21, "blocks creation, update, deletion and force-push".

---

## Earlier V-* findings

| Finding | Status now | Where |
| --- | --- | --- |
| V-1 (1-hour App token) | **closed.** The 50-minute rule and the nightly job split are in. The mechanics are under U-V6. | AD-7; AD-18 |
| V-2 (no Variables scope) | **closed.** The App no longer lists Variables, and the kill switch is on the manual checklist. | AD-7; AD-21 step 1; AD-19 |
| V-3 (actionlint `job.workflow_*`) | **closed.** The three ignores were verified by experiment (P28). | Conventions |
| V-4 (create or publish) | **closed** in wording. The case is certain, not a spike (U-V1). | Deferred bullet 1 |
| V-5 (module-agent branch sync) | **closed.** Module agents start from `main`, with a story-10 check. | AD-7; Deferred |
| V-6 (`Samples/` exists) | **closed** | AD-19; Seed |
| V-7 (Dapr pin) | **closed.** The pin is named and the CLI row added. Live pins are still 1.18.7 and 1.18.2, as Deferred says. | Deferred; Stack |
| V-8 (`client-id`) | **closed** | Conventions |
| V-9 (commitlint limits) | **closed.** Matches live `commitlint.config.mjs` and config-conventional 21.2.4. | Conventions |
| V-10 (60-day keepalive) | **closed** | Deferred |
| V-11 (Stack gaps; floating PEP 723 transitives) | **partly closed.** `@commitlint/config-conventional` and the Dapr CLI are added, and PEP 723 transitives are locked (P24). Microsoft.Playwright (where browsers come from), the container push tool (Deferred) and `gh` still have no row. | Stack; AD-11 |
| V-12 (CodeQL one language per job) | **closed.** The empty-list case is under U-V9. | AD-18 |
| V-13 (SDK floats) | **closed.** The Stack and Conventions now say `global.json` with `rollForward`. | Stack; Conventions |

## Memlog cross-check (entries after line 111)

| Entry | Claim | Today |
| --- | --- | --- |
| l.112 | release artifacts kept 90 days | **wrong in the live org: 30 days** (U-V2) |
| l.112 (D1 A), l.123 | completion publishes the draft at its SHA | the publication is refused after any bump (U-V1) |
| l.113 | environments `cicd-app` and `hexalith-release`, deployable from `main` only; Builds' policy has no environment until the rewrite | **holds** (P1-P6). The validator is unchanged since 2026-10-01. |
| l.116 | `cache-mode` exists and limits the reusable workflow; actionlint ignore | **holds; GA on all plans** (P14, P28) |
| l.117 | token life 1 h and revocation; `client-id`; `permission-*`; 6 h; `overwrite`; release restriction; `build-mode`; single-valued `event` | **holds** (P15-P18, P23, P30, P31) |
| l.118 | setup-python v7.1.0; Builds commitlint limits | **still latest; matches live** |
| l.119 | `uv lock --script` with `uv run --locked`; `npm ci --ignore-scripts` with `npm audit signatures` | **verified by experiment** (P24, P25) |
| l.120 | `bump-push` with `GITHUB_TOKEN` "not `.github/workflows`" | **unverified for nested paths** (U-V5) |
| l.124, l.136 | package-ID scoping is a story-1 check | **answered: yes** (U-V3) |
| l.125 | immutability only once legacy releases are gone, "because legacy semantic-release may add assets after publishing" | **rationale out of date** (P13). The rule is harmless. |
| l.125 | `delivered/**` ruleset "App-only bypass"; l.104 "lets only the App update" | **AD-21 lost "update"** (U-V11) |
| l.127 | `package-manager-cache: false`, `enable-cache: false` | **holds** (P27) |
| l.131 | `-noAutoResponse`, `-p:RestoreConfigFile`, `-warnaserror:NU1900;NU1903;NU1904;NU1905` | **holds** (P26); see U-V8 for MTP |

**Counts:** 0 critical, 1 high, 3 medium, 7 low.
