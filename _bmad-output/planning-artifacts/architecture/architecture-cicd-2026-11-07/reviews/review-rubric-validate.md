# Rubric review (validation gate): ARCHITECTURE-SPINE.md, Hexalith.CiCd

**Verdict:** The spine can be built on once two Rule fixes land. Its structure is sound, it covers CAP-1 to CAP-16, and the pass-3 defects are closed. But two Rules fail the very `Prevents` line they claim:
- AD-7: App tokens expire one hour into a nightly run that can wait five hours.
- AD-17: a stale draft fails its drift check forever after any delivery.

Separately, nine medium gaps sit at story interfaces and in the operational envelope.

- **Target:** `ARCHITECTURE-SPINE.md` (596 lines, 21 ADs, status final, updated 2026-11-08).
- **Read against:**
  - `.memlog.md`;
  - the spec package at commit `4666c3d` ("fix: spec", 2026-11-08 13:07; the refresh is committed, not uncommitted, and the working tree is clean);
  - brownfield `references/Hexalith.Builds` at `3c809618`, which equals live `main`;
  - module workflows in `references/*`;
  - read-only `gh` checks of org secrets, Builds pull requests and rulesets, and Stack releases;
  - the earlier reviews (pass 1, pass 2, pass 3).
- **Labels:** findings that an earlier pass raised and the current text still leaves open are marked *previously raised, still open*.

**Counts: 0 critical, 2 high, 9 medium, 13 low.**

## Checklist

| # | Item | Result | Findings |
| --- | --- | --- | --- |
| 1 | Fixes the real divergence points for the 27 stories | **Partial** | Story mapping and ordering conditions now match `stories.yaml` (rename → story 2, rewrite → story 3, perimeter → story 4, guard → story 5, deliver → story 7, ready-draft fallback → story 8). Open interfaces: Windows `prepare` vs the loader (R-3: stories 2, 4, 16), the hook contract (R-5: story 2 vs 13–24), outcome semantics (R-7: story 3 vs 8), MSBuild entry points (R-6: Builds vs every module). |
| 2 | Every Rule is enforceable and prevents its `Prevents` divergence | **Partial** | AD-7 does not prevent "dying on token expiry" (R-1). AD-17 breaks "partial releases needing recovery" (R-2). The line-82 invariant "custom actions never call Builds" has no Rule (R-4). AD-6's stale-render guard has a re-run hole (R-19). |
| 3 | Nothing under Deferred lets two units diverge | **Partial** | Entries are owned and bounded, except the catch-all pointing at `reviews/*-pass2.md`, which hides an open cross-version contract (R-6, R-17). The composite-names entry contradicts AD-10 (R-17). |
| 4 | Named technology is verified-current (light) | **Pass** | Every Stack row matches the latest release on 2026-11-08 (`gh` releases, PyPI, npm, .NET release metadata). Notes in R-18. |
| 5 | Ratifies the brownfield | **Partial** | Schemas, workflow names, `Props/` and `Tools/` are ratified. Contradicted or unaddressed: Builds' active Dependabot updates of frozen composites (R-11), the commitlint lengths (R-15), MSBuild import paths (R-6), the `prerelease` channel (R-22), and AD-2 vs the kept validators (R-21). |
| 6 | Covers CAP-1..CAP-16 | **Pass, with notes** | All 16 are mapped. R-2 breaks CAP-12's "rerunning a failed release finishes it", R-7 weakens CAP-13's failure signal, and CAP-10's "no module test asserts workflow YAML" has no lasting control (R-23). |
| 7 | Parent spine | N/A | None. |
| 8 | Every owned dimension is decided, deferred or open | **Partial** | Deployment (none, a non-goal), environments (none) and the provider set (GitHub Free, hosted runners, nuget.org, Zot, Azure deferred) are decided. Gaps: token lifetime and the 6 h job limit (R-1), module CI health after delivery (R-9), the legacy credential lifecycle (R-10), Dependabot runs (R-8), and quotas and rate limits left unstated (R-12). |
| F1 | Decisions, not rationale | Mostly | A few explanatory clauses remain (R-24). |
| F2 | Invariants separated from seed; seed minimal | Pass | The seed's "Operations" bullets carry decisions that no AD binds. This is acceptable, but R-9 and R-10 extend them. |
| F3 | Every AD has Binds, Prevents and Rule | Pass | 21/21, checked by script. |
| F4 | Diagrams valid and agree with ADs | Partial | Syntax inspected, no errors (memlog: they parse with mermaid 11.4.1). The sequence diagram matches AD-18, apart from the omitted keepalive. The flowchart misses edges that the ADs allow (R-16). |
| F5 | Cross-references resolve | Pass, with a lag | All `AD-n` references are 1–21, and the companion files exist. The capability map disagrees with the Binds lines in 13 of 16 rows (R-16). |

---

## Critical

None.

## High

### R-1 (high): App tokens expire after 1 hour, but nightly waits up to 5 hours before it pushes with the App
- **Location:**
  - AD-7, line 192;
  - AD-18, lines 369–372;
  - AD-7 `Prevents`, line 189.
- **Issue:** AD-7's only token rule is "Each job mints a token with `actions/create-github-app-token`". AD-18 puts the dispatch, a wait of up to 5 hours, the bump push, the wait for the delivery run, and the enable-API and keepalive calls in one run, with no rule about token age. Read naturally, that is one job and one token, and the token is dead after 60 minutes.
- **Evidence:**
  - Spine line 189: AD-7 "**Prevents:** unattended paths dying on token expiry".
  - Spine line 370: "it bumps `builds-version` … and pushes … with the App".
  - The `actions/create-github-app-token` v3.3.0 README, line 16: "An installation access token expires after 1 hour."
  - The same README, line 436: the token "is revoked in the `post` step … it cannot be passed to another job".
  - GitHub-hosted jobs stop at 6 hours. The 5 h wait leaves under 1 h for the scan, the bump, the delivery wait and the keepalive.
- **Failure it allows:**
  - On any night whose releases take more than about 1 h (17 CodeQL runs of 16–24 min each, queued under the Free plan's 20-job limit, `pipeline-stages.md:49`), the bump push, the enable API and the keepalive fail with 401.
  - Builds never reaches the modules, and nightly is red every long night.
  - Or the job hits the 6 h limit.
  - Story 8 discovers this in production.
- **Fix (AD Rule tightening, AD-7 + AD-18):**
  - "No App token is used more than 50 minutes after it is minted. `nightly.yml` runs as separate jobs (dispatch; wait and summary; scan; bump and delivery wait; keepalive). Each job mints its own token, and the wait re-mints at least every 50 minutes."
  - "Each nightly job stays under the 6 h job limit."

### R-2 (high): Completing a stale marked draft always fails the drift check after any delivery, so the module never releases again
- **Location:**
  - AD-16, line 328 (release SHA = the marked draft's SHA);
  - AD-17 step 1, line 344;
  - AD-17 step 5, line 348;
  - AD-18 bump, line 370.
- **Issue:** The drift check compares the release SHA with the module's *current* `delivered/<Repo>`. When the release completes a draft, the release SHA is the draft's SHA, which was created before the bump, or before any template change, that delivery has since pushed.
- **Evidence:**
  - Line 344: "re-run the guard check on it against the module's `delivered/<Repo>`. Drift fails red."
  - Line 348: "If a draft … exists, use its version, and the run stops after completing it."
  - Line 370: the bump runs "whatever their results".
  - Example:
    1. Night N: the draft is created at SHA S under `vOld`, and the publish job fails, for example because Zot is down.
    2. The bump delivers `vNew` (callers, `hexalith-ci.json`, gitlink), and `delivered/<Repo>` moves.
    3. Night N+1: the release SHA is S, whose owned files still name `vOld`. The drift check fails red, before the audit-deletion rule at line 350 can run.
    4. Every night repeats step 3.
- **Failure it allows:**
  - A single transient publish failure, followed by any Builds release (44 last month), freezes that module's releases until a human acts.
  - If NuGet push had already succeeded, the packages sit on nuget.org with no tag or release.
  - This is the "recovery workflow" outcome that AD-17's `Prevents` rules out, and it breaks CAP-12 ("Rerunning a failed release finishes it").
- **Fix (AD Rule tightening, AD-17):**
  - "The marked draft records the CiCd commit its drift check passed against (trailer `hexalith-delivered: <cicd-sha>`). Completing a draft re-checks against that commit, never the current `delivered/<Repo>`."
  - Add the trailer to the "Release markers" convention.

## Medium

### R-3 (medium): `prepare` on Windows must read `solution`, but every way to do that breaks an AD
*Previously raised in part (pass-2 M7). The language half is closed; the loader half is still open.*
- **Location:**
  - AD-4, line 133 ("Every reader uses it");
  - AD-11, line 262;
  - AD-12, line 287;
  - AD-1, line 92.
- **Issue:** On Windows, `prepare` restores and builds `solution`, which lives only in `hexalith-ci.json` (AD-1). AD-4 says every reader uses the stdlib Python loader. AD-11 forbids Python in the Windows part of `prepare`. AD-12 renders the job as two steps that pass no inputs, and AD-1 keeps knobs out of callers. Story 2 (`prepare`) and story 16 (Conversations, the first Windows job) must break one of these rules, and each could pick a different one:
  - pwsh JSON parsing, a second loader;
  - Python on Windows;
  - a rendered `with: solution:`, a second copy of a knob.
- **Evidence:** the four lines above. JSON files cannot be read with expressions in composites.
- **Failure it allows:** two loaders or two copies of the knob, which drift apart; or a Windows `prepare` that builds the wrong solution in a repo with two solutions.
- **Fix (AD Rule tightening, AD-12 + AD-10):**
  - "The reusable `ci.yml` outputs `solution`, as validated by the loader. Rendered `jobs` pass `solution: ${{ needs.ci.outputs.solution }}` to `prepare`, which on Windows reads no JSON."
  - The output becomes public API.

### R-4 (medium): "Custom actions never call Builds" has no Rule, and the lexical deny list misses exactly that bypass
- **Location:**
  - line 82;
  - AD-14, lines 306–309;
  - AD-8, line 207;
  - `enforcement.md:59-69`.
- **Issue:**
  - The invariant sits under the diagram only.
  - AD-14 forbids rebuilding and environment setup, but not `uses: Hexalith/Hexalith.Builds/...`.
  - "Composite only" is in the Rule, but the guard does not check it.
  - The deny list matches text (`actions/checkout`, `actions/setup-dotnet`, `dapr init`, …), and a call to a legacy Builds composite contains none of those strings.
- **Evidence:**
  - Modules call `initialize-build@main` 21 times and `initialize-dotnet@main` 18 times today (`module-inventory.md:39`).
  - These are the steps agents will copy when they turn kept gates into custom actions (stories 13–24).
- **Failure it allows:**
  - A hook runs `Hexalith/Hexalith.Builds/Github/initialize-build@main`, which does a checkout, a .NET setup and a rebuild.
  - Its Builds `@main` code runs beside the pinned tag, two Builds versions in one run, which AD-9's `Prevents` rules out.
  - The guard passes it, and the module turns red at the final deletion (story 27).
  - A JavaScript or Docker action escapes the deny list entirely.
- **Fix (AD Rule tightening, AD-14 + AD-8):**
  - "Every `.github/actions/**/action.yml` has `runs.using: composite`, and no `uses:` names `Hexalith/Hexalith.Builds` at any ref. The guard checks both."
  - Add both to the deny list.

### R-5 (medium): The hook and job contract is not in Builds' public API, so a minor can break every module's custom actions overnight
- **Location:** AD-10, lines 232–237; AD-14, lines 307–309.
- **Issue:**
  - AD-14 promises hooks a workspace: restored, Release-built, environment set up, a pull-only registry session and a read-only token.
  - It calls hook secrets "a minor Builds API change".
  - But AD-10's enumerated public API does not include the hook-invocation contract: the hook names and the action path, the inputs and environment Builds passes, the workspace guarantees, and the `jobs` shape (`prepare`, then the action).
- **Evidence:**
  - Line 309: "Hook secrets arrive as a minor Builds API change."
  - AD-10's list (lines 233–237) names only `workflow_call` I/O, `prepare`/`publish`, three schemas, the `check.py` CLI and two MSBuild properties.
- **Failure it allows:**
  - Story 2's hook call and stories 13–24's actions can disagree on inputs, the working directory or build outputs.
  - A later Builds change to any of these is not classified as a major, so the auto-bump (AD-10) ships it to Folders, EventStore and FrontComposer the same night, and their hooks fail.
- **Fix (AD Rule tightening, AD-10):** Add to the public API: "the AD-14 hook and job contract: hook names, action path, inputs and environment passed, workspace guarantees".

### R-6 (medium): MSBuild entry points and `PackageVersion` removals are not public API
*Previously raised in pass-1 M15 and pass-2 L17, still open; the Deferred catch-all hides it.*
- **Location:** AD-10, line 237; Deferred, line 596.
- **Issue:** Modules import Builds through fixed file paths, and Builds' catalog removals reach every module through the auto-bump. AD-10 covers property names only.
- **Evidence:**
  - Module imports, grepped over `references/*`:
    - `references/Hexalith.Builds/Props/Directory.Packages.props` 62 times, for example `Hexalith.Commons/Directory.Packages.props:6`;
    - `Hexalith.Build.props` 7 times;
    - `Hexalith.Package.props` 6 times.
  - Line 237 lists only `UseHexalithProjectReferences` and `HexalithPublishContainer`.
  - Separately, today's `Samples/` holds only starter props files. A sample module placed under Builds' root inherits Builds' own `Directory.*.props`, so CAP-15's self-test would not exercise these import paths.
- **Failure it allows:**
  - A Builds minor moves a props file or drops a `PackageVersion`.
  - The nightly bump moves every gitlink, and modules fail with MSB4019 or NU1010 the next morning.
  - The Samples test stays green.
- **Fix (AD Rule tightening, AD-10 + AD-19):**
  - Add to the public API: "the MSBuild files modules import (`Hexalith.Build.props`, `Hexalith.Package.props`, `Props/Directory.Packages.props`) and the `PackageVersion` set; removing or renaming one is a major".
  - AD-19: "The sample module imports Builds through the same paths a module uses."

### R-7 (medium): Who writes `outcome.json` and how nightly judges a run are undecided
- **Location:**
  - AD-17 "Outcome", line 360;
  - AD-17 publish composite, lines 352–356;
  - AD-18, lines 369 and 371;
  - Deferred, line 582.
- **Issue:**
  - The reusable release ends before the caller's `publish` job runs, so it cannot write `published`.
  - Artifacts made with `upload-artifact` v4 and later are immutable unless `overwrite: true` (README v7.0.2, lines 299 and 404).
  - AD-18 says nightly "reads each run's outcome" and fails "when any release … failed". It does not say whether a run counts as failed by its conclusion or by its outcome.
  - Under the Deferred fallback, `ready` is a *successful* end state.
- **Failure it allows:**
  - The publish job fails after the release wrote `ready`.
  - Story 8, which reads outcomes, counts it as success, and nightly stays green while a module did not release. That breaks CAP-13 ("A failure … turns this repository's nightly run red").
  - Or story 3's second upload fails on the immutable artifact name.
- **Fix (AD Rule tightening, AD-17 + AD-18):**
  - "The reusable release writes `outcome.json`. The `publish` composite overwrites it with `published`, using `overwrite: true`."
  - "Nightly counts a run as failed when its conclusion is not `success`, whatever `outcome.json` says. The outcome only labels the summary."

### R-8 (medium): Dependabot-triggered module CI gets no Actions secrets, and the Dependabot workflow is otherwise undecided
- **Location:** Conventions "Secrets and variables", line 469; AD-12, lines 280 and 286; AD-10, line 253.
- **Issue:**
  - Modules keep Dependabot (`build(deps)`), and CI runs on its `push` and `pull_request` events.
  - Those runs get only Dependabot secrets. The pull pair exists only as an Actions org secret.
  - The spine also does not say who merges Dependabot PRs, given that agents push straight to `main`.
- **Evidence:**
  - GitHub docs: "the only secrets available to the workflow are Dependabot secrets. GitHub Actions secrets are **not available**." (https://docs.github.com/en/code-security/dependabot/troubleshooting-dependabot/troubleshooting-dependabot-on-github-actions)
  - EventStore and Parties log in to the registry in CI today (`Hexalith.EventStore/.github/workflows/ci.yml:94-95`, `Hexalith.Parties/.github/workflows/ci.yml:49-50`).
  - 13 modules have a `dependabot.yml`.
- **Failure it allows:** every Dependabot PR in a `registry: true` module goes red at login, which breaks "a red build means the product is broken". Agents then "fix" it, which is the pain this repository exists to stop.
- **Fix (Conventions + AD-21 precondition):**
  - "`HEXALITH_REGISTRY_PULL_USERNAME`/`_PASSWORD` also exist as Dependabot org secrets with the same names, restricted to the managed repos."
  - Add an open question for story 4: who merges Dependabot PRs.

### R-9 (medium): Nobody watches module CI on the commits delivery pushes, so a bad Builds minor is first seen about 24 h later
- **Location:**
  - AD-18, lines 370–371;
  - sequence diagram, lines 393–394;
  - seed "Failure signal", line 527.
- **Issue:**
  - Nightly waits for the `deliver.yml` run, not for the module CI runs that the `build(cicd)` commits trigger.
  - Those runs are App-triggered, so GitHub notifies nobody (memlog line 13). The same goes for the CI runs that restore dispatches.
  - Nothing else in the spine watches module CI.
- **Evidence:**
  - Line 371: "Fails when any release, the scan or that delivery failed."
  - Line 394: "D-->>N: delivery result".
- **Failure it allows:**
  - A Builds minor passes `Samples/` but breaks module CI.
  - All 17 modules go red at about 04:00, and the only signal is the next night's 17 "main is red" releases, a full day without releases.
  - Meanwhile, module agents see red CI and try to fix the pipeline.
- **Fix (AD Rule tightening, AD-18):** "After the bump's delivery, nightly waits (bounded) for each delivered module's CI run on its `build(cicd)` commit and fails if any is not green." This is one more job under R-1's split.

### R-10 (medium): Legacy org-wide credentials have no retirement or restriction, and the new HEXALITH_* secrets have no creator
- **Location:**
  - AD-7, lines 191–196;
  - AD-21 step 1, lines 443–451;
  - Conventions, line 469;
  - seed "Credentials", line 530.
- **Issue:** Today's org secrets are visible to **all** repos. AD-7 concedes that org agent Apps keep Workflows write. Neither AD-7 nor AD-21 nor AD-20 restricts or deletes these secrets. Also, no AD or story creates the new `HEXALITH_NUGET_USER`, `HEXALITH_REGISTRY_*` and `HEXALITH_REGISTRY_PULL_*`, or the pull-only Zot account that the pull pair requires. AD-21 only says "grant access".
- **Evidence:**
  - `gh api orgs/Hexalith/actions/secrets` returns these, each with visibility `all`:
    - `NUGET_API_KEY`;
    - `HEXALITH_ZOT_USERNAME`/`HEXALITH_ZOT_API_KEY`;
    - `AZURE_*`;
    - `SONAR_TOKEN`.
  - Legacy workflows read `secrets.NUGET_API_KEY`, for example `Hexalith.Agents/.github/workflows/recover-release.yml:46`.
- **Failure it allows:**
  - A careless App-based agent copies a legacy release workflow into a module.
  - It runs on that push and publishes to nuget.org with the org API key before the guard or the next delivery deletes it.
  - The release then hits a version that is already taken.
  - Separately, the first `registry: true` adoption stalls on a secret that nobody created.
- **Fix (AD Rule tightening, AD-21 + seed Operations):**
  - "Before the first adoption, the maintainer creates the HEXALITH_* org secrets and variables. The pull pair is a pull-only Zot account."
  - "Legacy org secrets are restricted to the unmanaged repos that still use them at that point, and deleted at the final deletion."

### R-11 (medium): Builds' Dependabot changes frozen files every week, and the spine does not decide its fate
- **Location:** AD-20 "Freeze", line 422; AD-10 "Dependabot", line 253, which covers modules only; AD-19, line 402 ("only CiCd agents change it").
- **Issue:**
  - Builds' own `.github/dependabot.yml` runs the `github-actions` ecosystem over `/` and `/Github/*`, which includes the frozen `domain-*.yml` and the composites that modules call at `@main`.
  - These PRs are routinely merged.
  - AD-20 says those files "stay unchanged" and says nothing about Builds' Dependabot.
- **Evidence:**
  - `references/Hexalith.Builds/.github/dependabot.yml:13-21`.
  - `gh api repos/Hexalith/Hexalith.Builds/pulls`: 65 of the last 100 PRs are Dependabot's. "bump actions/setup-dotnet … in /Github/initialize-dotnet" was merged on 2026-11-05, and modules call that composite at `@main` 18 times.
- **Failure it allows:** stories 2, 3 and 5 (CiCd agents in Builds) each choose differently: merge, which breaks the freeze and changes code that `@main` callers run; ignore, so PRs pile up; or close.
- **Fix (AD Rule tightening, AD-20):** "Until the final deletion, Builds' Dependabot `github-actions` ecosystem excludes the frozen files (`exclude-paths`), or is limited to the new pipeline's directories."

## Low

- **R-12 (low): Quotas and rate limits are left silent (dimension gap).**
  - The spine never states the Free plan's 20-job concurrency, the 6 h job limit, the App rate limit (5,000/h, shared by nightly polling, delivery checks and dispatch), the `GITHUB_TOKEN` limit of 1,000/h per repo, or artifact retention.
  - The spec records the queue decision (`pipeline-stages.md:49`), and today's numbers fit: about 1,100 polling calls an hour.
  - **Fix:** add a seed "Operations: quotas" bullet that restates these limits and points to R-1.
- **R-13 (low): The render's inputs are not closed.** *Previously raised (adversary pass-2 L8), still open.*
  - AD-5 (line 166) lists what triggers a re-render, not what the render may read.
  - AD-3 (line 123) lets CiCd tools read module live `main`.
  - Deferred line 591 leaves Dependabot ecosystems to the render, with no knob.
  - If `render.py` reads module content, "render with no diff", a global check that gates all delivery, flaps on every module push.
  - **Fix (AD-5 tightening):** "`render.py` reads only `setup/`, `templates/`, `builds-version` and Builds at `builds-version`."
- **R-14 (low): Branch pushes run CI twice and fail on stale branches.** *Previously raised in part (adversary pass-2 L2), still open.*
  - AD-12 (line 286) triggers CI on `push` and `pull_request` with no branch filter, so every PR-branch commit runs twice, against "nothing runs twice".
  - On non-`main` pushes, AD-8 (line 211) compares the branch with the current `delivered/<Repo>`. A branch cut before a delivery fails without touching an owned file.
  - **Fix (AD-12 tightening):** "`push` triggers on `main` only."
- **R-15 (low): The commitlint conventions contradict Builds' config.** *Previously raised (rubric pass-2 L5), still open.*
  - Line 466 says "body and footer line length unlimited".
  - `references/Hexalith.Builds/commitlint.config.mjs:5-6` sets body and header to 200. The footer stays at config-conventional's default of 100, and `defaultIgnores: false` makes merge commits fail.
  - No story owns the change.
  - **Fix:** ratify 200/200 and state the footer rule, or name the change under story 5.
- **R-16 (low): The diagrams and the capability map lag the ADs.** *Previously raised (rubric pass-2 L2 and L7), still open.*
  - The flowchart, which line 82 calls "the allowed dependencies", lacks these edges:
    - `CALLER → ACT`, the extra-OS job (AD-12, line 287);
    - CiCd tools → module live `main` (AD-3, line 123);
    - module → Builds props through the gitlink (AD-9);
    - the restore job's write into the module (AD-6, AD-8).
  - The structural seed lacks `BUILDS → nuget.org`.
  - Line 82's "modules never reference CiCd" reads wrong while the guard clones CiCd from inside module CI.
  - The map's "Governed by" column disagrees with the Binds lines in 13 of 16 rows (script). Examples: CAP-16 lists AD-4 and AD-6, which do not bind it, and omits AD-3, AD-10, AD-17 and AD-19, which do.
  - **Fix:** add the edges, reword line 82 as "module files never name CiCd", and regenerate the map from the Binds lines.
- **R-17 (low): Deferred hygiene.**
  - Line 596 ("Low-severity reviewer notes in `reviews/*-pass2.md`") is unowned and unbounded. Story agents do not read reviews. It covers R-6 and R-13, which are not low.
  - Line 592 makes composite names beyond `prepare` and `publish` "public API under AD-10". AD-10's list names only `prepare` and `publish`, and the other composites are internal `$/` references.
  - **Fix:** replace line 596 with explicit entries or delete it, and drop "as public API" from line 592.
- **R-18 (low): Currency notes.** *The `client-id` part was previously raised (verification pass-2 L3), still open.*
  - `actions/create-github-app-token` v3.3.0 deprecates `app-id` (`action.yml`: "Use 'client-id' instead."), but line 469 and story 1 name `HEXALITH_CICD_APP_ID`.
  - AD-11 requires tests on Python 3.12 while `ubuntu-latest` ships 3.14.4, yet no Stack row provides 3.12 (`setup-python`, or `uv python`).
  - `@commitlint/config-conventional`, which Builds' config extends, has no Stack row.
  - jscpd 5.4.3 was published at 06:54 UTC today.
  - All other rows are current.
- **R-19 (low): AD-6 does not stop a re-run of an old `deliver.yml` run.**
  - "Re-run jobs" uses the original SHA. Step 1's ref advance would then not be a fast-forward, and the Rule (lines 179–182) does not say the run stops before step 2's module push. It writes a stale render, which AD-6's `Prevents` rules out. Self-heals within 1 h.
  - **Fix (AD-6 tightening):** "The deliver job pushes to no module unless its commit is the tip of CiCd `main` and its ref advance succeeded."
- **R-20 (low): Module agents can create `v*` tags and releases.**
  - The module-agent token has Contents write (AD-7, line 193). AD-21's tag ruleset (line 446) blocks only update and deletion, and AD-17 step 5 (line 348) trusts any reachable `v*` tag.
  - A stray agent tag shifts every later version.
  - **Fix (open question for story 3):** restrict `v*` creation to the release actor, or compute versions only from releases that carry the trailer.
- **R-21 (low): AD-2's scope.** "Builds' workflows, composites and scripts contain no module names" (line 99) is literal.
  - Frozen legacy files name modules: `Github/publish-containers/publish-containers.sh`, `Github/prepare-module-build/prepare_module_build.py`.
  - So do the `Tools/` catalog validators that AD-11 keeps: `Tools/test-platform-version-catalog.ps1`, `Tools/package-version-exceptions.json`.
  - **Fix:** "New pipeline code. Frozen files and the `Props/` catalog validators are outside this rule."
- **R-22 (low): Builds' `prerelease` channel is dropped without saying so.** *Previously raised (rubric pass-2 L13), still open.*
  - `references/Hexalith.Builds/package.json:17-18` and `.github/workflows/build-release.yml:36` show the channel.
  - **Fix:** one line in AD-19: "No prerelease channel."
- **R-23 (low): CAP-10's "No module test asserts workflow YAML" (`SPEC.md:87`) is a one-time deletion with no lasting control.**
  - A module agent can add such a test after migration; the guard does not look.
  - **Fix:** a Deferred entry for story 10, a gate-rule line in the delivered instruction block, or accept and say so.
- **R-24 (low): Form polish.**
  - `[ADOPTED]` remains on AD-1 and AD-2 only (lines 84 and 95). *Previously raised (pass-1 L10, pass-2 L1), still open.*
  - A few Rules carry rationale:
    - line 179, "It is always a fast-forward, because …";
    - line 275, "That means package mode …";
    - line 582, "The REST docs say …".
  - **Fix:** drop the tag and the clauses.

## Checked and holding (no finding)

- **Pass-3 closures that hold:**
  - the AD-3 setup-file validation (the rendered document is validated);
  - Builds' `hexalith-ci.json` without `buildsTag`;
  - the rename-before-freeze test carve-out (line 423);
  - the end state for `Github/`, `Tools/` and `package.json` (lines 431–434);
  - preconditions with timing (AD-19, lines 411–413);
  - the outcome schema in the public API;
  - the per-module `delivered/<Repo>` (D1).
- **Sequence diagram vs AD-18:** dispatch of adopted modules only, release order (kill switch, green CI, draft, pack, publish, tag last), summary, then scan, then bump, then delivery. It matches, apart from the omitted keepalive.
- **`stories.yaml` vs the spine's ordering conditions:** satisfied:
  - ruleset cut and nuget.org policy (story 1) before the rename (story 2);
  - the rewrite (story 3) before nightly (story 8);
  - the perimeter library in a Builds release (story 4) before deliver (story 7);
  - the `commitlint-caller.yml` deletion (story 5) after the cut.
