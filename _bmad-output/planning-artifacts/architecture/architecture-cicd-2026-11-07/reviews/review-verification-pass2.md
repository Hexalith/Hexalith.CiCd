# Review (pass 2): verification of the revised Hexalith.CiCd spine

- **Spine:** `../ARCHITECTURE-SPINE.md` (revised, AD-1..AD-21, 2026-11-07)
- **Decision log:** `../.memlog.md` (through line 75)
- **Pass 1:** `review-verification.md` (2C/5H/9M/9L). Items it CONFIRMED are not re-checked here.
- **Lens:** were the decisions that are new or changed in the revision checked against the web or the existing repos, or only asserted? This covers versions, whether each named technology exists and fits, and the platform behaviour each AD relies on.
- **Date:** 2026-11-07
- **Method:**
  - Local experiments in the scratchpad:
    - `dotnet build`, `pack` and `restore` on SDK 10.0.403 against a `net10.0` project referencing `System.Text.Json 8.0.0` (NU1903 high).
    - actionlint 1.7.12 and `uvx zizmor@1.32.0 --offline` on sample workflows shaped like the spine's callers and reusables.
  - Source code read:
    - semantic-release 25.0.9 (`npm pack`);
    - github/codeql-action v4.39.3 (`src/`, `analyze/action.yml`);
    - NuGetGallery `GitHubTokenPolicyValidator.cs`;
    - create-github-app-token v3.3.0 `action.yml`.
  - docs.github.com article bodies: releases REST, App permissions reference, reusing workflows, variables, concurrency, events, workflow and metadata syntax, code scanning REST, rulesets REST.
  - `gh api`: release tags, workflow runs and job steps, code-scanning analyses and alerts, CiCd rulesets, Builds immutable-releases.
  - The brownfield under `references/`.

## Verdict

Both pass-1 criticals are now placed correctly:
- **NuGet login.** It runs in a caller-defined job, which is what nuget.org's validator requires.
- **Audit gate.** The `-warnaserror:NU1903;NU1904` CLI switch does override `WarningsNotAsErrors`, on `build` and `pack` as well as `restore`.

All Stack rows are current. But the revised release path rests on two platform behaviours that are wrong for this design:
- **semantic-release.** It refuses to compute a version once `main` has moved past the pinned SHA.
- **Releases API.** The docs say the `GITHUB_TOKEN` cannot create or publish a release whose target commit changes workflow files relative to the default branch. That case is exactly the draft-completion and race path.

Two audit-gate claims are also contradicted by measurement:
- "overriding module props" is false for three module-owned levers;
- "NU1901–NU1904 stay warnings in CI" is false in 5 modules.

**Counts:** 0 critical, 4 high, 7 medium, 11 low.

---

## Pass-1 items: how the revision handled them

| Pass 1 | Revision | Status |
| --- | --- | --- |
| C1 Trusted Publishing from a reusable workflow | AD-17: `publish` job defined in the module caller, its one step a remote Builds composite | **CONFIRMED.** See #1 in the checklist. |
| C2 `-warnaserror` restore is a no-op | AD-12 keeps advisories as warnings in CI; AD-17 release build uses `-warnaserror:NU1903;NU1904 -p:NuGetAudit=true -p:NuGetAuditMode=all` | **Partly.** The switch works (#2). The pass-1 fix items `-p:NuGetAuditLevel=low` and a guard deny for `NoWarn`/`NuGetAuditSuppress` were dropped (H3). The CI half is wrong in 5 repos (H4). |
| H1 actionlint rejects `$/` | Convention: "actionlint runs with an ignore for `$/` references" | **CONFIRMED** by experiment (#9). One caveat in L1. |
| H2 zizmor default policy | Convention: committed config, ref-pin `Hexalith/*`, hash-pin others, `self-repository` off, never `--fix` | **CONFIRMED** by experiment (#10). Caveat in L2. |
| H3 "never cancelled" concurrency | Convention: "a pending run may be superseded by a newer one" (default queue accepted) | **Correct as stated** (#5). Two knock-on effects remain open: M3 and L11. |
| H4 rulesets block direct pushes | AD-21: maintainer cuts rulesets; validate checks what the API exposes | **CONFIRMED** readable: rulesets GET needs only Metadata (#13). |
| H5 org-wide agent Apps | AD-7: accepted; the guard and hourly delivery are the control | Accepted decision; nothing to verify. |
| M1, M2, M5, M6, M9 | Stack Python row; no Python in Windows composites; `HexalithPublishContainer`; 26 h freshness check; slug fixed | Handled. M5 has a follow-up (M7). |
| M3 uv unpinned | Stack uv 0.13.7 (memlog: setup-uv `version`) | Handled for uv itself. Transitive PEP 723 deps still float (L10). |
| M7 dispatch returns run IDs | Not adopted | Still open (L8). |
| M8 Stack omissions | setup-node, uv and the artifact actions added | Partly. Dapr CLI / `dapr/setup-dapr`, Playwright and `gh` are still missing (L10). |
| L1 `app-id` deprecated | Convention still `HEXALITH_CICD_APP_ID` | Still open (L3). |

---

## Critical

None.

---

## High

### H1 — AD-17 step 5: semantic-release won't compute a version for a pinned SHA once `main` has moved (WRONG)

- **Spine claim:**
  - AD-16: "The release SHA is `github.sha` … never re-resolved."
  - AD-17 step 5: "compute the next version for the pinned SHA, independent of later pushes."
  - The memlog (4.4, line 42) names semantic-release as the version engine. AD-4 keeps it only in Builds.
- **Evidence:** semantic-release 25.0.9 `index.js:86-98`, `lib/git.js:209-216` and `lib/git.js:296-303`.
  1. Before any dry-run branching, `run()` calls `verifyAuth`, which is `git push --dry-run --no-verify -- <repositoryUrl> HEAD:<branch>`.
  2. If that fails, it calls `isBranchUpToDate`. That function requires local `HEAD` to equal the remote branch head (`git ls-remote --heads`).
  3. If the two differ, it logs "The local branch main is behind the remote one, therefore a new version won't be published." and returns `false`.
  4. `--dry-run` does not skip this, because the `dryRun` checks come later, at `index.js:123/204/224`.
- **Why it applies here:** `actions/checkout` on a `workflow_dispatch` puts local `main` at `github.sha`. Any push to the module's `main` between dispatch and step 5 makes the run decline. The window covers the kill switch, the `codeql` and `nightly-hook` jobs, and up to 30 minutes of green-CI wait. Pushes that can land in it:
  - hourly delivery (it fires at 02:17, the same minute as the nightly; see M6);
  - restore commits;
  - agent pushes.

  The JS API returns `false`, which is indistinguishable from "no release". The night silently becomes "nothing to release".
- **Fix (pick one, and record it in AD-17):**
  - **Option A.** Builds' version script does not run semantic-release core. It calls `@semantic-release/commit-analyzer` and `@semantic-release/release-notes-generator` directly on `git log <last v* tag reachable from SHA>..<SHA>`. This needs no push credentials, which also resolves L5.
  - **Option B.** Keep semantic-release but point `repositoryUrl` at a local bare mirror in which `refs/heads/main` is set to the pinned SHA and the tags are copied.
  - Either way, add a story-3 test: push to `main` after dispatch, and the pinned SHA must still release.

### H2 — AD-17: `GITHUB_TOKEN` cannot create or publish a release whose target changes workflow files relative to `main` (docs say WRONG for the rerun and race paths)

- **Spine claim:**
  - AD-17 creates a marked draft at the pinned SHA. The caller `publish` job "publish[es] the draft, which creates `v<version>` last".
  - Step 4 completes an existing draft at its stored SHA on a later run.
  - Only `GITHUB_TOKEN` exists in module runs (AD-7).
- **Evidence:**
  - docs.github.com REST "Create a release" and "Update a release", in the note above the parameters (https://docs.github.com/en/rest/releases/releases): "If the commit identified by target_commitish … adds or modifies any file under .github/workflows/ relative to the repository's default branch, the authenticating token must be authorized to modify workflows. Otherwise, this endpoint returns 404 Not Found … The GITHUB_TOKEN available to GitHub Actions cannot be authorized for this."
  - For Update, the resolved target is "the existing target" when `target_commitish` is not changed.
  - The earlier rule (https://github.blog/changelog/2023-11-02-github-actions-enforcing-workflow-scope-when-creating-a-release) exempted SHAs that have a branch head or tag.
- **Brownfield doesn't cover it:**
  - Builds v4.44.9 (`0577f0c2` touches 2 workflow files) was published by `github-actions[bot]`.
  - That went through semantic-release, which `git push`es the tag while the commit is the `main` head and then creates the release on an existing tag.
  - The draft-then-publish path that AD-17 uses has not been exercised.
- **Where it bites:**
  - **Draft completion.** On a later night, the draft's SHA is behind `main`, and usually behind a `build(cicd)` bump delivery that rewrote `.github/workflows/*.yml`. Publishing returns 404. Step 4 retries the same draft every night and stops there, so the module never releases again until a human publishes it. That is the recovery workflow AD-17 claims to prevent.
  - **Same-night race.** Any workflow-changing commit (delivery) between draft creation and the publish job has the same effect.
  - **Builds.** It is hit more often, because Builds' own commits routinely change `.github/workflows/`.
- **Fix:**
  - Add a story-3 spike that measures both cases with `GITHUB_TOKEN`:
    - (a) the target SHA itself modifies workflows and is no longer the head;
    - (b) the target SHA doesn't modify workflows, but `main` changed workflows after it.
  - If either fails, move only the final "publish draft" call to CiCd `nightly.yml`. It already holds an App token with Contents and Workflows write on every module. The module run ends in a "ready" state with packages and containers pushed, and nightly publishes the draft after the run succeeds. Tag-last holds, and no key enters a module.
  - Alternatively, step 5 creates the draft only while the pinned SHA is still `main`'s head (`git ls-remote`). This narrows the race but does not fix completion.

### H3 — AD-17: the release audit gate is not "overriding module props"; three module-owned levers defeat it (WRONG, measured)

- **Spine claim:** AD-17 step 6 says `-warnaserror:NU1903;NU1904 -p:NuGetAudit=true -p:NuGetAuditMode=all`. The memlog D1 (line 67) adds "overriding module props".
- **Experiment:** SDK 10.0.403, project with `TreatWarningsAsErrors=true` plus `WarningsNotAsErrors` NU1901–1904, which mirrors `Hexalith.Build.props:33`.

  | Module-side setting | Release command | Result |
  | --- | --- | --- |
  | none (only WNAE) | `pack -c Release "-warnaserror:NU1903;NU1904" -p:NuGetAudit=true -p:NuGetAuditMode=all` | **error NU1903, exit 1** (the gate works) |
  | `<NoWarn>…;NU1903</NoWarn>` | same | no diagnostic, **exit 0** |
  | `<NuGetAuditLevel>critical</NuGetAuditLevel>` | same | no diagnostic, **exit 0** |
  | `NuGetAuditLevel=critical` | same + `-p:NuGetAuditLevel=low` | error NU1903, exit 1 |
  | `<NuGetAuditSuppress Include="…GHSA…"/>` (in `Directory.Build.targets`) | same | no diagnostic, **exit 0** |
  | `NoWarn` NU1903 | same + `-p:NoWarn=NU1510` | error, exit 1. **Don't use this:** a global `NoWarn` discards every module analyzer suppression. |

- **Reality:**
  - `Hexalith.Works/Directory.Build.props:42-44` and `Hexalith.EventStore/Directory.Build.props:74` already tell authors and agents to "Waive an individual advisory with NuGetAuditSuppress".
  - EventStore sets `NuGetAuditLevel` (`:77`, currently `low`).
- **Fix:**
  - Add `-p:NuGetAuditLevel=low` to the release build.
  - Add to the guard's deny checks (`enforcement.md`): `NoWarn` containing `NU1903`/`NU1904` in any module MSBuild file.
  - Decide `NuGetAuditSuppress` explicitly. Either:
    - deny it in the guard; or
    - make it the sanctioned waiver (the analogue of a CodeQL dismissal) and list it as such in AD-17, accepting that module agents can add it.
  - Record the experiment in the memlog.

### H4 — AD-12: "NU1901–NU1904 stay warnings in CI" is false in 5 modules (WRONG, measured)

- **Spine claim:** AD-12 step 2 says "Release build with `-warnaserror` … NU1901–NU1904 stay warnings in CI". This is the premise of D1, which rejected option A: "overnight advisory turns all CI red".
- **Reality:** these modules set `TreatWarningsAsErrors=true`, do not import `Hexalith.Build.props`, and have no `WarningsNotAsErrors` for NU190x:
  - ChatBot (`Directory.Build.props:25`, audit on `:29-30`);
  - Platform (`:6`);
  - Parties (`:12`; its targets only exempt CS codes);
  - FrontComposer (`:37`);
  - McpCli (`:15`).

  NuGet's audit is on by default for net10.0 (pass 1 #10).
- **Experiment** (same shape, no WNAE):

  | Command | Result |
  | --- | --- |
  | `build -warnaserror` | **error NU1903, exit 1** |
  | `build -warnaserror "-warnnotaserror:NU1901;…;NU1904"` | still **error**. NuGet promotes the code itself under `TreatWarningsAsErrors`, so MSBuild's switch can't demote it. |
  | `build -warnaserror -p:WarningsNotAsErrors=NU1901;…;NU1904` | warning, exit 0. This clobbers module lists (e.g. Projects `NU5104`, Parties `CS9113;CS0162;CS1591;CS1574`). |

  The consequence: any advisory, even a low one, turns these modules' CI red. Their releases are then blocked through AD-16.
- **Fix (choose one):**
  - **Option A.** The Builds CI and local-check build passes `-p:NuGetAudit=false`. The release build stays the only audit gate. Pass 1 measured that this suppresses reporting.
  - **Option B.** AD-21 step 2 adds the NU1901–1904 `WarningsNotAsErrors` line to those 5 modules' props.

---

## Medium

### M1 — AD-7/AD-21: the App permission list doesn't cover every precondition check, and one name is off

Checked against https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps:

| AD-21 check | Endpoint | Required permission | In AD-7? |
| --- | --- | --- | --- |
| Ruleset shape | `GET /repos/{o}/{r}/rulesets[/{id}]`, `GET …/rules/branches/{b}` | **Metadata** read (implicit) | yes. Administration is not needed. |
| Code-scanning default setup off | `GET …/code-scanning/default-setup` | Administration (repo) read | yes |
| Dependabot security updates off | `GET …/automated-security-fixes` | Administration (repo) read | yes |
| Kill-switch variable set | `GET …/actions/variables/{name}` | Variables read | yes |
| Org variable shared with repo | `GET …/actions/organization-variables` | Variables (repo) read | yes |
| Org **secrets** shared with repo | `GET …/actions/organization-secrets` | **Secrets (repo) read** | **no** |
| `semgrep-app` removed | `GET /orgs/{org}/installations` | **Administration (organization) read** | ambiguous. AD-7 doesn't say repo or org. |
| Stale CodeQL configurations | `GET …/code-scanning/analyses` | "**Code scanning alerts**" read | yes. The permission's real name is "Code scanning alerts". |
| Unmarked drafts | `GET …/releases` (drafts need push access) | Contents write | yes |
| Repo in installation | `GET /installation/repositories` | none | yes |

**Fix:**
- AD-7: list "Code scanning alerts: read" and "Secrets: read (repository; names only)".
- Either add "Administration: read (organization)" or move the `semgrep-app` check to the manual list.
- AD-3: name which AD-21 preconditions validate enforces.

### M2 — AD-18: the CodeQL `category hexalith-release` only works for one language, and the alerts API can't filter by category

- **One language only.** codeql-action v4.39.3 passes the `category` input unchanged to every language's `--sarif-category` (`src/analyze.ts:603-627`). It refuses an upload whose runs share tool and `automationDetails.id`:
  - `src/sarif/index.ts:109-118` (`createRunKey`);
  - `src/upload-lib.ts:59-102`: "does not support uploading multiple SARIF runs with the same category".

  The CLI manual says the category "should differ between each of the analyses" for different languages (https://docs.github.com/en/code-security/reference/code-scanning/codeql/codeql-cli-manual/database-interpret-results). The `codeql` knob is a language list, so `[csharp, javascript-typescript]` breaks.
- **No server-side category filter.** The list-alerts parameters are `tool_name`, `tool_guid`, `ref`, `pr`, `state`, `severity`, `sort`, `direction`, `before`, `after`, `page`, `per_page` and `assignees`. There is no `category`. The category is only on `most_recent_instance.category`. Live check: EventStore alerts carry `.github/workflows/codeql.yml:analyze`.
- **What is CONFIRMED:** `wait-for-processing` defaults to `true` (`analyze/action.yml:75-78`), so alerts are current right after analyze.
- **Fix:**
  - Use one analyze step per language (a matrix) with `category: hexalith-release/language:<lang>`.
  - The gate filters client-side on `most_recent_instance.category` starting with `hexalith-release`, with `state=open`, `ref=refs/heads/main` and `tool_name=CodeQL`. It queries `severity=critical` and `severity=high` separately (pass 1 L9).
  - Update the Conventions "Release markers" row.

### M3 — Concurrency: `deliver.yml` is both top-level and reusable, and calling it from nightly is redundant and racy (CONFIRMED mechanism; the spine has not decided how to handle it)

- **Reusable-workflow concurrency.**
  - The reuse docs (https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations) say "A called workflow uses the name of its caller workflow in `${{ github.workflow }}`" and that "the `github` context is always associated with the caller workflow".
  - Community reports show a workflow-level `concurrency` in a called workflow is evaluated, and that a group equal to the caller's is cancelled as a deadlock (z-shell/.github#507, github/gh-aw#35161).
  - So "never in reusable ones" is right for Builds `ci.yml`/`release.yml`.
- **The conflict.** Conventions put a `deliver` group in `deliver.yml`, which AD-6 also triggers via `workflow_call` from nightly. The two rules contradict each other for that file.
- **The race.**
  - The nightly bump commit is pushed with the App, and App pushes trigger `push` workflows (pass 1 #4). So `deliver.yml` already runs from that push.
  - The extra `workflow_call` then waits as the single pending entry in `deliver`.
  - An hourly or push run supersedes it. The nightly job ends `cancelled`, and nightly goes red or cancelled for no product reason.
- **Fix:**
  - AD-18: after the bump commit, nightly does not call `deliver.yml`. It lets the push trigger deliver, or dispatches it. Drop the `workflow_call` trigger from AD-6.
  - Or keep the call and state that `deliver.yml` declares a literal group `deliver`, never `${{ github.workflow }}`. In that case accept the supersede risk explicitly.

### M4 — AD-17: how containers reach the `publish` job is unspecified, and "build and pack once" is UNCONFIRMED for them

- Step 6 packs and uploads **packages** only. The caller `publish` job then "push[es] containers by version tag".
- SDK container publishing (`PublishContainer`) pushes straight to a registry from the build.
- Pushing in a later job needs one of:
  - `ContainerArchiveOutputPath` (a tarball artifact) plus an external pusher (`docker load`/`push`, or similar);
  - or a rebuild in `publish`, which breaks "build once" and AD-14's "no rebuild" spirit.
- **Fix:** name the mechanism in AD-17. Archive in step 6, upload it with the packages, push in `publish` using a pinned tool. Verify in story 3 against Zot.

### M5 — The nightly 02:17 and hourly delivery at minute 17 coincide

- AD-6 runs hourly delivery at minute 17. AD-18 runs the nightly at 02:17. The 02:17 delivery pushes into the modules exactly while their releases start.
- That is the trigger for H1 and H2, and for avoidable `ci.yml` concurrency churn on the release SHA.
- **Fix:** skip the hourly run while a nightly run is in progress (check `nightly.yml` runs), or move the nightly to a different minute.

### M6 — AD-10 lists `UseHexalithProjectReferences` and `HexalithPublishContainer` as Builds public API, but Builds owns neither (reality check)

- **`UseHexalithProjectReferences`:**
  - It is defined in 12 modules' `Directory.Build.props`, with module-specific defaults: `Debug` gives `true` in Works:26, Folders:24 and Agents:30.
  - It is unused in AI.Tools, McpCli, PolymorphicSerializations and Timesheets.
  - Builds only reads it, once, at `Props/Directory.Packages.props:72`.
  - The global `-p:UseHexalithProjectReferences=false` still wins everywhere, because every definition is conditioned on `== ''`.
- **`HexalithPublishContainer`:** it exists nowhere in the 18 repos. Pass 1 counted about 30 explicit container opt-ins today. Until each one is converted, adoption silently publishes no containers.
- **Fix:**
  - AD-10: "Builds defines and documents …" (move the default into `Hexalith.Build.props`), or call them module conventions that Builds reads.
  - AD-21 step 2: module agents set `HexalithPublishContainer=true` on every project that is published as a container today.

### M7 — AD-17: the `publish` job's permissions as written can't publish the draft

- The spine says the job is "defined in the caller with `id-token: write`".
- Job-level `permissions` sets every unlisted scope to `none`, so publishing the release would fail.
- The job needs `contents: write` plus `id-token: write`.
- Downloading a same-run artifact needs no token (download-artifact README: `github-token` only for another repo or run).
- **Fix:** state `contents: write, id-token: write` in AD-17. Combined with H2, the job may need only `id-token: write` if nightly publishes the draft.

---

## Low

- **L1 — actionlint `-ignore` (CONFIRMED, with a caveat).**
  - With `-ignore 'specifying action "\$/'`, v1.7.12 exits 0 on step-level `uses: $/Github/prepare`.
  - A job-level `uses: $/.github/workflows/…` raises a different `[workflow-call]` message, and that one still fails.
  - Missing local `./.github/actions/<hook>` dirs are skipped silently, which is good for dormant hooks.
  - `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` lints clean.
  - **Fix:** write the exact regex into Builds, e.g. `-ignore '"\$/'`. Note that upstream is inactive (pass 1).
- **L2 — zizmor config (CONFIRMED, with a caveat).**
  - `rules.unpinned-uses.config.policies: {"Hexalith/*": ref-pin, "*": hash-pin}` plus `rules.self-repository.disable: true` gives "No findings" on zizmor 1.32.0. Subpaths such as `Hexalith/Hexalith.Builds/Github/publish@vX` and the reusable `…/.github/workflows/release.yml@vX` both match `Hexalith/*`.
  - `actions/setup-node@v7.1.0` is still flagged, as intended.
  - But `ref-pin` also accepts `Hexalith/Hexalith.Builds/…@main`, so exact-tag enforcement rests only on validate (AD-10).
  - Builds immutable releases are still `enabled: false`, so tags remain movable.
  - **Fix:** state that validate rejects any non-`builds_tag` ref, and consider enabling immutable releases on Builds.
- **L3 — create-github-app-token v3.3.0** (`action.yml:11-14`). `app-id` carries `deprecationMessage: "Use 'client-id' instead."`, but Conventions still names `HEXALITH_CICD_APP_ID`. **Fix:** use `HEXALITH_CICD_APP_CLIENT_ID`.
- **L4 — `-warnaserror:NU1903;NU1904` quoting.** In a shell the `;` ends the command. **Fix:** pass it as one argv element from the script, or write it with a comma; the experiment shows `NU1903,NU1904` works the same.
- **L5 — zizmor `artipacked` vs semantic-release.**
  - A release-shaped job (`actions/checkout` without `persist-credentials: false`, plus `upload-artifact`) gets `warning[artipacked]` from zizmor 1.32.0.
  - semantic-release's `verifyAuth` needs persisted push credentials.
  - H1 option A removes the conflict. Otherwise add a scoped inline ignore.
- **L6 — Draft tag only on publish: still UNCONFIRMED.** The REST docs say only that `target_commitish` "determines where the Git tag is created from" and is "Unused if the Git tag already exists". The only other source is community (goreleaser discussion #3604). **CONFIRMED:** draft listing needs push access ("Only users with push access will receive listings for draft releases"). Keep the story-3 test.
- **L7 — nuget.org policies today.**
  - The validator checks `environment` only when the policy has one (`GitHubTokenPolicyValidator.cs`).
  - 14 module releases use `environment: production` today, and FrontComposer publishes from `release-publish.yml`.
  - Any existing policy keeps rejecting the new no-environment `release.yml` job.
  - **Fix:** AD-21 says "create or replace". Name the file and leave the environment empty.
- **L8 — Dispatch run IDs (pass 1 M7, still open).** The response schema now marks `workflow_run_id` and `run_url` as required. AD-18 should poll those rather than search runs.
- **L9 — Commit conventions vs Builds today.**
  - `commitlint.config.mjs` currently sets `body-max-line-length` 200 and `header-max-length` 200, and inherits footer 100 from config-conventional. The "unlimited" in Conventions is a planned change, so list it in story 2/3.
  - Explicit `commit-message.prefix` yields a lowercase subject (Builds PRs: "ci(deps): bump actions/setup-dotnet …"). Auto-detected prefixes can capitalize (EventStore: "build(deps): Bump …"), which would fail config-conventional `subject-case`. The rendered explicit prefix is therefore correct.
- **L10 — Stack gaps (pass 1 M3/M8 remainder).**
  - No rows for the Dapr CLI / `dapr/setup-dapr`, Microsoft.Playwright, `@commitlint/config-conventional` 21.2.4, the commit-analyzer and release-notes-generator plugins, or `gh`.
  - PEP 723 transitive deps (MarkupSafe etc.) are still resolved at run time. **Fix:** `exclude-newer` or `uv lock --script`.
- **L11 — The nightly summary has no "cancelled" bucket.** Superseded pending release runs are now accepted, so the summary needs one. **Fix:** classify `cancelled` as "superseded" and decide whether it fails the night.

---

## Platform-behaviour checklist (new or changed claims)

| # | Behaviour an AD relies on | Status | Source |
| --- | --- | --- | --- |
| 1 | NuGet/login in a caller-defined job, even inside a remote Builds composite, passes nuget.org's validator | **CONFIRMED.** The validator needs `job_workflow_ref` to start with `{owner}/{repo}/.github/workflows/` and compares the file name case-insensitively. `workflow_ref`, `ref` and `sha` are not checked; `environment` only if the policy sets one. A top-level job works live: Commons `release.yml:72-105`, step "Authenticate to NuGet with trusted publishing" = success; Builds `build-release.yml` runs success 2026-11-07. A composite wrapper has not been exercised; the claims are job-scoped, so smoke-test it in story 3. | `NuGetGallery/src/NuGetGallery.Services/Authentication/Federated/GitHubTokenPolicyValidator.cs`; `gh api …/runs/{id}/jobs` |
| 2 | `-warnaserror:NU1903;NU1904` overrides `WarningsNotAsErrors`; placement on restore not required | **CONFIRMED.** Errors on `build`, `pack` and `restore`, and on `build`/`pack --no-restore` after a plain restore, because diagnostics are re-emitted from the assets file. Comma separator equivalent. | experiment (SDK 10.0.403) |
| 3 | The CLI gate overrides all module props | **WRONG** (H3) | experiment |
| 4 | NU1901–1904 stay warnings in CI | **WRONG for 5 modules** (H4) | experiment; module props lines cited |
| 5 | Reusables declare no concurrency, callers do; pending runs superseded by default; `cancel-in-progress` as an expression | **CONFIRMED** | https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations ; https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency (example `cancel-in-progress: ${{ !contains(github.ref, 'release/')}}`) |
| 6 | `vars` in Builds' reusable `release.yml` reads the module's `HEXALITH_RELEASE_PUBLISH_ENABLED` | **CONFIRMED** ("For reusable workflows, the variables from the caller workflow's repository are used") | https://docs.github.com/en/actions/reference/workflows-and-actions/variables |
| 7 | Draft creates no tag until published; `target_commitish` respected | **UNCONFIRMED** (L6); `target_commitish` "unused if the Git tag already exists" CONFIRMED | REST releases |
| 8 | `GITHUB_TOKEN` can create or publish the draft at the pinned SHA | **WRONG when the target changes workflows relative to `main`** (H2) | REST releases note |
| 9 | actionlint `-ignore` suppresses the `$/` uses error | **CONFIRMED** (step level; L1) | experiment, actionlint 1.7.12 |
| 10 | zizmor 1.32.0 keys: `rules.unpinned-uses.config.policies`, `rules.self-repository.disable` | **CONFIRMED** (L2) | experiment, `uvx zizmor@1.32.0 --offline` |
| 11 | `$/` usable inside composite `action.yml` (prepare/publish calling Builds siblings) | **CONFIRMED** | https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax (`runs.steps[*].uses`) |
| 12 | Artifact handoff from a reusable-workflow job to a caller job in the same run | **CONFIRMED live.** Builds `domain-ci-v2.yml:687-692` uploads `module-integration-diagnostics` (upload v7.0.2). Parties `ci.yml:52-71` downloads it (download v8.0.1). Run 42353187283: step success. Upload v7 and download v8 share `@actions/artifact` 6.3.1; v8 defaults hash mismatch to `error`. | `gh api`; release notes |
| 13 | App permission names and AD-21 check endpoints | **Partly** (M1) | permissions-required-for-github-apps |
| 14 | `workflow_dispatch` `github.sha` = branch head at dispatch | **CONFIRMED.** `GITHUB_SHA` is "Last commit on the GITHUB_REF branch or tag", and the dispatch API returns the created run synchronously (`workflow_run_id` required). | events-that-trigger-workflows; REST workflows |
| 15 | semantic-release computes a version for a SHA behind `main` | **WRONG** (H1) | semantic-release 25.0.9 source |
| 16 | CodeQL `category` and filtering alerts by category | **Partly** (M2) | codeql-action v4.39.3 source; code-scanning REST |
| 17 | `UseHexalithProjectReferences` exists in Builds props; its default | **WRONG premise.** Defined per module (12 repos), Builds only reads it (`Props/Directory.Packages.props:72`); the global `=false` override works (M6) | `references/` grep |
| 18 | `HexalithPublishContainer` | New; set nowhere today (M6) | `references/` grep |
| 19 | Ruleset rule types `deletion`, `non_fast_forward`, `update` | **CONFIRMED** | https://docs.github.com/en/rest/repos/rules |
| 20 | CiCd `main` accepts App pushes (bump, keepalive) | **CONFIRMED.** No rulesets, no branch protection. | `gh api repos/Hexalith/Hexalith.CiCd/rulesets`, `…/branches/main/protection` (404) |
| 21 | NuGet audit has a vulnerability source in every module | **CONFIRMED.** All 8 `nuget.config` files `<clear/>` then add nuget.org; the others use the default. | `references/*/nuget.config` |

## Stack spot-check (2026-11-07)

| Row | Spine | Latest found | Status |
| --- | --- | --- | --- |
| uv | 0.13.7 | 0.13.7 (2026-11-03) | current |
| `actions/setup-node` | v7.1.0 | v7.1.0 (2026-10-08) | current |
| `actions/upload-artifact` | v7.0.2 | v7.0.2 (2026-10-07) | current |
| `actions/download-artifact` | v8.0.2 | v8.0.2 (2026-10-07) | current; v8 = no unzip of non-zipped, hash mismatch → `error` |
| `astral-sh/setup-uv` | v10.3.3 | v10.3.3 (2026-10-28) | current |
| `actions/checkout` / `setup-dotnet` | v7.0.1 / v6.1.0 | same | current |
| `actions/create-github-app-token` | v3.3.0 | v3.3.0 | current (L3) |
| `github/codeql-action` | v4.39.3 | v4.39.3 (latest tag; the bundle release is 2.27.4) | current |
| `NuGet/login` | v1.2.0 | v1.2.0 | current |
| actionlint / zizmor | v1.7.12 / v1.32.0 | same | current |
| semantic-release / @commitlint/cli / jscpd | 25.0.9 / 21.2.4 / 5.4.2 | same (npm) | current |
| Jinja2 / PyYAML / jsonschema | 3.1.6 / 6.0.3 / 4.26.0 | same (PyPI) | current |
| .NET SDK | per `global.json` (10.0.4xx); Builds 10.0.403 | 10.0.403 latest (2026-10-25); modules: 5× 401, 3× 402, 9× 403 | current |
| Dapr runtime | 1.19.1 | v1.19.1 (2026-10-31) | current |
| Runner (`$/`) | ≥ 2.336.0 | v2.338.2 | satisfied |

**Counts:** 0 critical, 4 high, 7 medium, 11 low.
