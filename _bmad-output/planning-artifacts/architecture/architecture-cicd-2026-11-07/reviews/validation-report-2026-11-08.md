# Hexalith.CiCd spine validation — 2026-11-08

- **Spine:** `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md` (21 ADs, status final, feature altitude)
- **Against:** SPEC-cicd at `4666c3d`, `references/Hexalith.Builds` and the 17 modules, live `gh` (read-only), and the web
- **Gate:** the deterministic lint (0 findings), the configured rubric walker, verification and adversary reviewers, and two ad-hoc lenses: spec reconcile and security/supply chain
- **Mode:** Validate. The spine has not been changed.

## Verdict

**Not ready to build on yet. Two critical holes and ten high ones must be fixed before stories 1–8 lock them in. They sit in the release path (AD-16 to AD-18) and in how credentials are held (AD-7). The structure, the stack and the alignment with the spec all hold.**

Raw findings: 2 critical, 12 high, 34 medium, 44 low (92 in all). Several reviewers found the same holes independently, so the 14 critical and high findings merge into the 12 issues below. Of those, 8 have a clear fix and 4 need your decision.

| Lens | Kind | Verdict | C | H | M | L |
| --- | --- | --- | --- | --- | --- | --- |
| Rubric walker | configured | Buildable once two Rule fixes land. It covers CAP-1 to CAP-16, and the pass-3 defects are closed. | 0 | 2 | 9 | 13 |
| Verification | configured | All 23 Stack pins are current. Three platform behaviours were never checked, and they break as written. | 0 | 1 | 4 | 8 |
| Adversary | configured | Fails. A release that fails after its draft exists can never complete once the delivered render moves. | 1 | 3 | 9 | 9 |
| Spec reconcile | ad hoc | Passes with fixes. The refreshed spec (4666c3d) matches every cited AD, and the story order meets every AD ordering condition. | 0 | 1 | 7 | 9 |
| Security and supply chain | ad hoc | Not safe as written. Fork PRs can't reach secrets, but the App key and the publish credentials are exposed outside their jobs. | 1 | 5 | 5 | 5 |

## Critical and high

### I-1 (critical): A failed publish freezes the module's releases

- **Found by:** A-1 (adversary, critical), R-2 (rubric, high), A-7 (adversary, medium)
- **ADs:** AD-16, AD-17, AD-18
- **What breaks:** If a publish fails after the draft exists, the module is left with a marked draft that every later run must complete first. Completing it re-runs the drift check against the live `delivered/<Repo>`, which that night's bump has already moved, so it fails every night. Even if it passed, the newer loader rejects the draft commit's older `hexalith-ci.json` after any minor release that adds a knob. Deleting the draft by hand republishes the same version from different content, which the spec forbids. Builds released about 40 times in the last month, so a bump follows almost every night.
- **Fix:** Completing a draft must not re-check against the current state. The two candidate rules are compared in D1.
- **Disposition:** **Your call: D1**

### I-2 (critical): The App private key shares jobs with unlocked third-party code

- **Found by:** X-1 (security, critical), X-11 (security, medium), V-11 (verification, low)
- **ADs:** AD-7, AD-11
- **What breaks:** The `validate`, `deliver` and `nightly` jobs hold `HEXALITH_CICD_APP_PRIVATE_KEY`. They also run `uv run` over PEP 723 dependencies whose transitive versions float: the verification run resolved new MarkupSafe and referencing releases at run time. They run jscpd from npm too. Any code in a job can read all of that job's secrets from runner memory, which is how the tj-actions compromise worked. The prize is the key itself: write access to Contents, Workflows and Actions on 19 repos, rotated only after a leak.
- **Fix:** A job that reads the key runs only stdlib Python, git and SHA-pinned actions. Render, schema validation, tool tests and the duplicate scan run in separate jobs with no secrets, and clone the public modules anonymously. CiCd tools are locked with `uv lock --script` and run with `--locked`. Every token mint passes explicit `repositories` and `permission-*` inputs.
- **Disposition:** **Clear fix, applied in an Update**

### I-3 (high): App tokens expire after one hour, but nightly holds one for five

- **Found by:** R-1 (rubric, high), V-1 (verification, high), A-13 (adversary, medium)
- **ADs:** AD-7, AD-18
- **What breaks:** An installation token lives for one hour and is revoked when its job ends. Nightly dispatches the releases, waits up to 5 h, then pushes the bump with the App. On any long night the polling, the outcome download and the bump push get 401, so `builds-version` never moves. The 5 h wait also nearly fills the 6 h job limit.
- **Fix:** No App token is used more than 50 minutes after it is minted. `nightly.yml` becomes separate jobs: dispatch, wait and summary, scan, bump and delivery wait, and keepalive. Each job mints its own token, the wait re-mints on every cycle, and every job stays under 6 h.
- **Disposition:** **Clear fix, applied in an Update**

### I-4 (high): `outcome.json` has no single writer, and nightly can't read `ready`

- **Found by:** A-2 (adversary, high), R-7 (rubric, medium), S-8 (spec reconcile, medium)
- **ADs:** AD-17, AD-18
- **What breaks:** AD-17 has the reusable release write the outcome. That workflow finishes before the caller's `publish` job starts, so the outcome can only ever say `ready`. Nightly has no rule for `ready` outside the Deferred fallback. If it reads `ready` as success, a failed publish goes unreported. If it reads it as failure, nightly is red every night. A second upload from `publish` collides on the artifact name. When `codeql` fails, no job writes `failed`.
- **Fix:** The last job that runs writes the outcome, once. `publish` writes `published` or `failed`. Otherwise a final `if: always()` job in the reusable release writes `nothing`, `disabled`, `ready` (fallback only) or `failed`, always with `overwrite: true`. Nightly fails any run whose conclusion isn't `success`, whatever the outcome says.
- **Disposition:** **Clear fix, applied in an Update**

### I-5 (high): A skipped module never gets its workflow drift repaired

- **Found by:** A-4 (adversary, high), S-4 (spec reconcile, medium)
- **ADs:** AD-6, AD-8
- **What breaks:** Delivery applies the perimeter only to modules that pass their checks. Restore skips `.github/workflows/**` and leaves it to the next delivery. A module agent can cause the skip, for example by renaming an enabled hook's action directory. An org agent App's edit to that module's workflows then persists for as long as the skip lasts. CAP-8's one-hour bound fails for exactly the modules that are in trouble.
- **Fix:** Every delivering run applies every module that has a `delivered/<Repo>` ref. A module that passes gets the new commit. A module that fails gets its last accepted render re-applied, using the perimeter library at that ref's `builds-version`. Both reviewers prefer this to weakening the spec's bound.
- **Disposition:** **Clear fix, applied in an Update**

### I-6 (high): The draft's tag can land on a different commit from the one built

- **Found by:** A-3 (adversary, high)
- **ADs:** AD-16, AD-17
- **What breaks:** Nothing fixes the draft's `target_commitish`, so it defaults to the default branch. The tag is then created at the head of `main` when the draft is published, which can be an hour or more after the build. The next version is computed from a tag that covers commits that never shipped. Setting the target to `main` would also make the story-3 spike pass for the wrong reason.
- **Fix:** `target_commitish` is the full release SHA, the same value as the `hexalith-release:` trailer. `publish` and the nightly fallback check that the two agree before publishing. The spike publishes a draft whose target is a SHA behind `main`.
- **Disposition:** **Clear fix, applied in an Update**

### I-7 (high): The App key is reachable from any CiCd branch

- **Found by:** X-2 (security, high)
- **ADs:** AD-7, AD-21
- **What breaks:** A repo secret is available to runs on every branch, and `deliver.yml` mints App tokens while it validates non-`main` pushes. Anyone with Workflows write on CiCd can push a branch whose workflow prints the key. That includes the CiCd-agent token and the `claude`, `chatgpt-codex-connector` and `cursor` Apps, which hold write access on all repos (checked live). AD-7's controls for those Apps are the guard, the drift check and delivery, and none of them covers CiCd or Builds, where all trust starts.
- **Fix:** The options are compared in D2 (where the key lives) and D3 (which repos the agent Apps can reach).
- **Disposition:** **Your call: D2 · D3**

### I-8 (high): The auto-bump trusts any new Builds tag

- **Found by:** X-3 (security, high), A-9 (adversary, medium), S-5 (spec reconcile, medium), R-20 (rubric, low), X-16 (security, low)
- **ADs:** AD-10, AD-18, AD-19, AD-21
- **What breaks:** Rulesets block updating and deleting `v*` tags, but not creating them. Builds has no tag ruleset today, and immutable releases are off. Anyone with Contents write on Builds can push `v<major>.99.0` on a commit CI never ran. At 02:17 the bump adopts that tag for all 17 modules, and its `publish` composite then runs with every module's publish credentials. Separately, the bump pushes a `builds-version` that nothing validated, so one bad minor halts all delivery.
- **Fix:** The bump accepts a tag only if its release was published by `github-actions[bot]`, its commit is on Builds `main`, and it matches that night's Builds outcome. The bump also runs the global checks before it pushes. AD-21 says to set the rulesets to exactly the listed ones, creating any that are missing, and to restrict creation of `v*` tags and `delivered/**` branches. Immutable releases are turned on for Builds and every module.
- **Disposition:** **Clear fix, applied in an Update**

### I-9 (high): Publish credentials aren't bound to the publish job

- **Found by:** X-4 (security, high)
- **ADs:** AD-16, AD-17, AD-21
- **What breaks:** The nuget.org policy names only the owner, the repo and `release.yml`, with no environment. So any run of a file named `release.yml`, on any branch, can mint a key, and that key can push any package the owner holds. The registry push pair is an org secret that any branch can read. The drift check lives inside the reusable workflow, so a drifted caller can simply not call it.
- **Fix:** The options are compared in D2. Either way, nightly compares the live `ci.yml` and `release.yml` blobs with `delivered/<Repo>` before it dispatches, and a `ci-workflow` input other than `ci.yml` is rejected outside Builds.
- **Disposition:** **Your call: D2**

### I-10 (high): Release jobs mix module code with write tokens and trusted outputs

- **Found by:** X-5 (security, high), X-10 (security, medium)
- **ADs:** AD-16, AD-17
- **What breaks:** Build and pack run the module's MSBuild and every package's `build/*.targets`. They do it in the same job that deletes drafts, which holds `contents: write`. Code there can push to `main`, create tags, edit drafts, and steer the `version`, `sha` and `artifact` outputs that `publish` trusts. The artifact is handed to `publish` by name, with no digest. A draft is trusted on its body trailer alone.
- **Fix:** Every job in Builds' reusable workflows declares `permissions:`. Jobs that run module or third-party code get `contents: read`, no secrets, and `persist-credentials: false`. Draft creation, completion and deletion run in a job that runs only stdlib Python. `publish` downloads the artifact by ID, checks its digest, and checks each package's version and commit. A draft counts as marked only if `github-actions[bot]` authored it and its SHA is on `main`.
- **Disposition:** **Clear fix, applied in an Update**

### I-11 (high): The release can restore caches that module code can poison

- **Found by:** X-6 (security, high)
- **ADs:** AD-12, AD-17
- **What breaks:** CI on `main` runs module tests and hooks, and can write cache entries scoped to `main`. The release is a `workflow_dispatch` on `main`, so it reads that scope. setup-node and setup-uv cache by default, and the current Builds release path already caches `~/.nuget/packages`. A poisoned entry would be packed into the published package.
- **Fix:** Both `release.yml` files declare `cache-mode: none`. Builds sets `package-manager-cache: false` on setup-node and `enable-cache: false` on setup-uv, and uses no NuGet cache.
- **Disposition:** **Clear fix, applied in an Update**

### I-12 (high): Nothing removes the Builds tests that assert workflow text, as CAP-15 requires

- **Found by:** S-1 (spec reconcile, high)
- **ADs:** AD-20
- **What breaks:** AD-20 lets the rename repoint or delete tests that read a workflow by name, and story 2 is told to repoint them. `Tools/test-self-ci.py` asserts the text of `ci.yml` and `build-release.yml`, and Builds' CI runs it. Once repointed it is still "used", so it survives the final deletion. CAP-15's "no Builds test asserts workflow text" never becomes true.
- **Fix:** AD-20: the rename change also deletes every test that asserts that workflow's text, including tests in frozen directories, and repoints any other test that reads it by name. Story 2's text follows through bmad-spec.
- **Disposition:** **Clear fix, applied in an Update**

## Decisions for you

### D1: How a stuck draft gets completed (I-1)

**Recommendation:** Option A. Combine it with A-7's `delivered-sha` input, which nightly passes at dispatch to the run that creates the draft, and with I-10's digest check.

- **A. Complete it from the run that created it**
  - *How:* The creating run writes `hexalith-release-run: <run-id>` into the draft. A later run completes the draft from that run's `release` artifact, with no drift check, no green-CI check and no build. `codeql`, `nightly-hook` and the kill switch still gate it. Artifacts are kept 90 days. If the artifact has expired, the draft is deleted when no package of its version is on nuget.org; otherwise the run fails with a fixed message.
  - *Pros:* What ships is exactly what was gated and built. Bumps and schema changes can't break it, and no version ever mixes content from two builds.
  - *Cons:* It depends on artifact retention. The conventions gain a trailer, a fixed message and a retention rule. The completing run trusts an earlier run's artifact, so it needs I-10's digest check.
- **B. Pin the drift baseline in the draft**
  - *How:* The draft records `hexalith-delivered: <cicd-sha>`. Completion re-checks against that commit, never the live ref.
  - *Pros:* The smallest text change. Every gate still runs again.
  - *Cons:* It still rebuilds at the old SHA with the newer loader, which rejects that commit's older `hexalith-ci.json` after any minor that adds a knob. The rebuild can also differ from packages that were already pushed.

### D2: Environments for the App key and the publish credentials (I-7, I-9)

**Recommendation:** Option A. It reverses the earlier "No GitHub environment" call. That call was made so nuget.org would accept the interim Builds release, and A keeps that working by leaving Builds' policy on `production` until the rewrite.

- **A. Two environments, deployable from `main` only**
  - *How:* A CiCd environment `cicd-app` holds the App key. Only the `deliver`, `nightly` and per-module-check jobs reference it, and PR and branch validation read the modules anonymously. Each module's publish job runs in `hexalith-release`, which holds the registry push pair. Each nuget.org policy names that environment and, where nuget.org allows it, scopes package IDs to the module's prefix. AD-7, AD-17, AD-21 and the Secrets convention change.
  - *Pros:* A workflow pushed on a branch can no longer read the key or mint a nuget.org key. Environments are available for public repos on GitHub Free. It closes the paths that fall outside the threat model.
  - *Cons:* It reverses an approved decision. There are 18 environments and nuget.org policies to change, in story 1 and at each onboarding. Builds' policy must stay on `production` until its release is rewritten.
- **B. Keep repo and org secrets, and accept the exposure in writing**
  - *How:* AD-7 states that any CiCd branch run and any `release.yml` run can reach these credentials, and that this is accepted under the careless-agent model.
  - *Pros:* No change to onboarding or to the nuget.org policies.
  - *Cons:* A prompt-injected agent App, or any CiCd-agent session, can take the org-wide key. Any branch can mint a key that pushes every Hexalith package.

### D3: Which repos the org agent Apps can reach (I-7)

**Recommendation:** Option A if you don't run those Apps' agents in CiCd or Builds. Otherwise option B, together with D2 option A.

- **A. Remove CiCd and Builds from their installations**
  - *How:* The maintainer sets `claude`, `chatgpt-codex-connector`, `cursor` and `semgrep-app` to "Only select repositories", leaving out CiCd and Builds. AD-21 lists this as a precondition, and AD-7 records it.
  - *Pros:* It removes the only writers to CiCd and Builds that no control covers.
  - *Cons:* Those Apps can no longer work in CiCd or Builds, and the setting has to be checked again whenever an installation changes.
- **B. Keep them, and rely on D2 and I-8**
  - *How:* AD-7 states that the agent Apps can push to CiCd `main` and Builds, and names the environments (D2) and tag acceptance (I-8) as the controls.
  - *Pros:* No change to how agents work.
  - *Cons:* An agent App can still push to CiCd `main`, which delivery trusts and ships to 17 modules within the hour.

### D4: How the Windows `prepare` step gets `solution` (R-3, A-20)

**Recommendation:** Option A.

- **A. CI passes it**
  - *How:* The reusable `ci.yml` outputs `solution`, as the loader validated it. Rendered jobs for other operating systems pass it to `prepare`, which reads no JSON on Windows. The output joins the AD-10 public API.
  - *Pros:* Keeps one loader and no Python on Windows.
  - *Cons:* Adds an output to the public API. Jobs for other operating systems depend on the `ci` job's output.
- **B. A PowerShell exception**
  - *How:* On Windows, `prepare` reads only `solution` with `ConvertFrom-Json`, after the Linux job has loaded the document.
  - *Pros:* No change to the API.
  - *Cons:* It adds a second reader of `hexalith-ci.json`, which is exactly the divergence AD-4's one-loader rule prevents.

## Medium and low (78)

A row that points to I-n or D-n belongs to that issue or decision. "Same as" marks a duplicate found by another lens.

| ID | Sev | Lens | Where | Finding | Fix | Link |
| --- | --- | --- | --- | --- | --- | --- |
| A-5 | medium | Adversary | AD-6 · AD-18 | A single `deliver` concurrency group lets validate-only runs cancel the bump's delivery | Main-branch runs use group `deliver` and are never cancelled. Other runs use `deliver-validate-<ref>` with cancel-in-progress. | previously raised |
| A-6 | medium | Adversary | AD-6 | A re-run or late deliver run writes an older render back into modules | Deliver only when the validated commit descends from the module's ref. A ref never moves backwards. | same as R-19 |
| A-7 | medium | Adversary | AD-16 · AD-17 · AD-18 | The drift check reads `delivered/<Repo>` live, hours after the release SHA was fixed | Nightly passes the ref's commit at dispatch as the `delivered-sha` input. | → I-1 |
| A-8 | medium | Adversary | AD-18 · AD-20 · AD-21 | "Adopted" has three readers and no fixed test | Adopted means `delivered/<Repo>` exists and live `main` has `hexalith-ci.json`. |  |
| A-9 | medium | Adversary | AD-18 · AD-3 | The bump pushes a `builds-version` that nothing validated | Run the global checks on the bumped tree first. On failure, push nothing and fail the night. | → I-8 |
| A-10 | medium | Adversary | AD-4 · AD-6 | Perimeter entries are judged on the working tree, but delivery's clone is sparse | The perimeter library reads paths from git (the HEAD tree or the index). Globs use git wildmatch. |  |
| A-11 | medium | Adversary | AD-12 · AD-14 · AD-18 | The `nightly` hook gets no environment setup and no registry secret | `prepare` runs the AD-12 environment setup on Linux, and the release caller passes the pull pair. |  |
| A-12 | medium | Adversary | AD-12 · AD-14 · AD-19 | Builds' self-test can't put hook actions under `module-root` | Hook actions always resolve at the workspace root. Only paths, config and the perimeter are re-rooted. | previously raised |
| A-13 | medium | Adversary | AD-7 · AD-18 | One App token per job can't cover a 5-hour wait | See I-3. | → I-3 |
| R-3 | medium | Rubric | AD-4 · AD-11 · AD-12 | Windows `prepare` must read `solution`, but every way of doing it breaks an AD | See D4. | → D4 |
| R-4 | medium | Rubric | AD-8 · AD-14 | "Custom actions never call Builds" has no Rule, and the deny list misses it | The guard checks that each custom action is composite and names no `Hexalith/Hexalith.Builds` ref. |  |
| R-5 | medium | Rubric | AD-10 · AD-14 | The hook and job contract isn't part of Builds' public API | Add the hook names, action path, inputs, environment and workspace guarantees to the AD-10 API. |  |
| R-6 | medium | Rubric | AD-10 · AD-19 | The MSBuild entry points and the `PackageVersion` set aren't public API | Add the imported props files and the `PackageVersion` set. Removing either is a major. | previously raised |
| R-7 | medium | Rubric | AD-17 · AD-18 | Who writes `outcome.json`, and how nightly judges a run, is undecided | See I-4. | → I-4 |
| R-8 | medium | Rubric | AD-10 · AD-12 | CI runs triggered by Dependabot get no Actions secrets | Mirror the pull pair as Dependabot org secrets. Open question for story 4: who merges Dependabot PRs? |  |
| R-9 | medium | Rubric | AD-18 | Nobody watches module CI on delivered commits, so a bad minor surfaces about 24 h later | Nightly waits, with a bound, for each module's CI on its `build(cicd)` commit. |  |
| R-10 | medium | Rubric | AD-7 · AD-21 | Legacy org credentials are never retired, and nobody creates the new `HEXALITH_*` secrets | The maintainer creates `HEXALITH_*` before the first adoption, then restricts and deletes the legacy secrets. |  |
| R-11 | medium | Rubric | AD-10 · AD-20 | Builds' Dependabot changes frozen files every week | Exclude the frozen paths from Builds' Dependabot until the final deletion. | same as A-19 |
| S-2 | medium | Spec reconcile | AD-20 | Builds' "Require every validation job to pass" deletion is scheduled nowhere | Widen AD-20's legacy-job list: the G-4/G-6 jobs, the aggregator and the `codeql.yml` call. |  |
| S-3 | medium | Spec reconcile | AD-4 | "Never parse the module's copy" contradicts partial entries and CAP-11's allow list | Limit it to whole-file entries. An unparseable partial file is drift, rewritten from the owned part. |  |
| S-4 | medium | Spec reconcile | AD-6 · AD-8 | The 1 h repair bound fails for a skipped module and while the global checks fail | See I-5. | → I-5 |
| S-5 | medium | Spec reconcile | AD-19 · AD-21 | Nothing creates the `v*` tag ruleset that the spec now relies on, and Builds has none | "Set rulesets to exactly these, creating missing ones." | → I-8 |
| S-6 | medium | Spec reconcile | AD-19 | The no-orphan-tag precondition is checked in story 1 but can lapse before story 3 | Story 3 re-checks AD-19's release preconditions before the hand-dispatched bootstrap release. |  |
| S-7 | medium | Spec reconcile | AD-10 | The bootstrap tag ships without the perimeter schema that story 4's validation needs | AD-10 says "at most one version of each schema". Story 4 releases the schema and moves `builds-version` first. | same as A-15 |
| S-8 | medium | Spec reconcile | AD-17 | Story 3 doesn't carry the release side of the Deferred fallback | If the spike confirms the refusal, the release stops before publishing and reports `ready`. | → I-4 |
| V-2 | medium | Verification | AD-3 · AD-7 | `create-github-app-token` can't scope a token to Variables | Move the kill-switch check to the AD-21 manual checklist, or read it in a separate step. |  |
| V-3 | medium | Verification | AD-8 · AD-9 | actionlint 1.7.12 rejects `job.workflow_ref` and `job.workflow_sha`, and the spine ignores only `$/` | Extend the actionlint ignore to `job.workflow_*`, and log the verification. |  |
| V-4 | medium | Verification | Deferred | The `GITHUB_TOKEN` restriction also blocks creating the draft, not only publishing it | The spike tests both. In the fallback, nightly creates and publishes the draft with the App. | previously raised |
| V-5 | medium | Verification | AD-7 | A module-agent token without Workflows may be unable to push a branch once delivered workflows change | Branch from current `main`. Story 10 tests a branch push and "Update branch" with that token. |  |
| X-7 | medium | Security | AD-8 · AD-17 | Six confirmed audit-gate bypasses fall outside the `NoWarn`/`NuGetAuditSuppress` lint | The release build ignores response files and the module's `nuget.config`. A Builds script judges `project.assets.json`. |  |
| X-8 | medium | Security | AD-3 · AD-5 | Setup values reach YAML with no escaping or shape rule | The schema constrains strings. Templates emit through `tojson` with `StrictUndefined`, and zizmor checks `rendered/`. |  |
| X-9 | medium | Security | AD-12 · AD-14 | Custom actions can read every secret their job holds, and can call unpinned actions | State that job secrets are visible to every step. Use `persist-credentials: false` and deny unpinned `uses:`. |  |
| X-10 | medium | Security | AD-16 · AD-17 | A marked draft is trusted on its body trailer alone | Marked only if authored by `github-actions[bot]`, with its SHA on `main`. | → I-10 |
| X-11 | medium | Security | AD-11 | Tools are pinned by version, not by hash | npm: a lockfile, `--ignore-scripts` and `audit signatures`. Python: `uv lock --script`. Binaries: a SHA-256. | → I-2 |
| A-14 | low | Adversary | AD-1 · AD-8 | Restore writes `hexalith-ci.json` without the caller that carries the same `jobs` | Write it only when `.github/workflows/` already matches the delivered render. |  |
| A-15 | low | Adversary | AD-4 · AD-10 | The first Builds tag comes before the perimeter schema | "At most one version" per tag. A new schema is a minor. | same as S-7 |
| A-16 | low | Adversary | AD-4 | The `gitmodules-section` entry has no fixed identity, and modules use two section names | Identify the section by `path`, keep its name, and remove duplicates. |  |
| A-17 | low | Adversary | AD-4 · AD-15 | Line endings are fixed for whole files only | Judge every entry on git blob content, normalizing CRLF for partial entries. |  |
| A-18 | low | Adversary | AD-7 · AD-21 | Nothing says who moves the NuGet audit waivers, or when | A CiCd agent adds them to `Props/`, and adoption waits for a tag that contains them. | same as S-15 |
| A-19 | low | Adversary | AD-19 · AD-20 | Builds' own Dependabot updates frozen files | See R-11. | same as R-11 |
| A-20 | low | Adversary | AD-1 · AD-4 · AD-11 | Windows `prepare` can't use the one loader | See D4. | → D4 |
| A-21 | low | Adversary | AD-8 | Non-`main` pushes are judged against the current delivered ref | Fail only for owned paths changed since the merge base. | same as R-14 |
| A-22 | low | Adversary | AD-4 · AD-21 | `package.json` and lockfiles kept only for the removed tools outlive delivery | Module agents delete them when they exist only for semantic-release or commitlint. | previously raised |
| R-12 | low | Rubric | Seed · Operations | Quotas and rate limits are never stated (a gap in the operations dimension) | Add a quotas bullet: 20 concurrent jobs, the 6 h job limit, the App's 5,000 calls/h, artifact retention. |  |
| R-13 | low | Rubric | AD-3 · AD-5 | The render's inputs are not closed | `render.py` reads only `setup/`, `templates/`, `builds-version` and Builds at that version. | previously raised |
| R-14 | low | Rubric | AD-8 · AD-12 | Branch pushes run CI twice and fail on stale branches | `push` triggers on `main` only. | same as A-21 |
| R-15 | low | Rubric | Conventions | The commitlint conventions contradict Builds' config (200/200, footer 100) | Ratify today's limits, or name the change under story 5. | same as V-9 |
| R-16 | low | Rubric | Diagrams · map | The diagrams and the capability map lag the ADs | Add the missing edges, reword line 82, and regenerate the map from the Binds lines. | previously raised |
| R-17 | low | Rubric | AD-10 · Deferred | Deferred has an unowned catch-all, and its composite names clash with AD-10 | Replace the pass-2 catch-all with explicit entries, and drop "as public API". |  |
| R-18 | low | Rubric | AD-11 · Stack | Currency notes: `client-id` replaces `app-id`, nothing provisions Python 3.12, a config-conventional row is missing | Rename the secret, add the rows, and provision 3.12 for the floor test. | same as V-8 |
| R-19 | low | Rubric | AD-6 | AD-6 doesn't stop a re-run of an old deliver run | See A-6. | same as A-6 |
| R-20 | low | Rubric | AD-7 · AD-17 · AD-21 | Module agents can create `v*` tags and releases | Restrict `v*` creation, or compute versions only from marked releases. | → I-8 |
| R-21 | low | Rubric | AD-2 · AD-11 | AD-2's literal scope covers frozen files and the kept validators | Limit it to new pipeline code. |  |
| R-22 | low | Rubric | AD-19 | Builds' `prerelease` channel is dropped without saying so | Add one line to AD-19: no prerelease channel. | previously raised |
| R-23 | low | Rubric | CAP-10 | "No module test asserts workflow YAML" is a one-time deletion with no lasting control | Add a Deferred entry, an instruction-block line, or accept it in writing. |  |
| R-24 | low | Rubric | Form | Stray `[ADOPTED]` tags, and rationale clauses left in Rules | Drop the tags and the clauses. | previously raised |
| S-9 | low | Spec reconcile | CAP-6 | CAP-6's "within one night" leaves out the skipped-module exception | Spec edit. |  |
| S-10 | low | Spec reconcile | Spec | module-inventory still says Builds releases "at most once a night" | Spec edit. |  |
| S-11 | low | Spec reconcile | AD-20 | "Final deletion removes it" could mean the whole root `package.json` | Spec edit: "removes that configuration". |  |
| S-12 | low | Spec reconcile | AD-1 · AD-8 | "Everything CI depends on is committed" ignores the guard's run-time read | Spec edit: add the `delivered/<Repo>` exception. |  |
| S-13 | low | Spec reconcile | AD-4 | Nothing says what a partial entry does when its file is absent | "Creates it holding only the owned part." |  |
| S-14 | low | Spec reconcile | Deferred | The CAP-13 assumption is broader than the spine's refusal condition | Align both on "draft publication refused". |  |
| S-15 | low | Spec reconcile | AD-21 | Module agents are given a Builds change they can't make | A CiCd agent adds the waivers to `Props/` before adoption. | same as A-18 |
| S-16 | low | Spec reconcile | Deferred | Stories 1 and 2 don't name their Deferred follow-ups | Story 2: verify `$/`, name the Dapr pin, and add the `submodules` knob if needed. |  |
| S-17 | low | Spec reconcile | Spec | Stories 17 and 24 leave out some gates that are not yet classified | Story text edit. |  |
| V-6 | low | Verification | AD-19 · Seed | `Samples/` already exists, as consumer templates | Seed: existing templates plus a new sample module in a subfolder. |  |
| V-7 | low | Verification | Stack · Deferred | The Dapr pin already exists in `Props/` (1.18.7), and there is no CLI row | Name the existing properties, bump both to 1.19.1, and add a CLI row. | previously raised |
| V-8 | low | Verification | AD-7 · Conventions | `HEXALITH_CICD_APP_ID` names a deprecated input | Rename it `HEXALITH_CICD_APP_CLIENT_ID`. | same as R-18 |
| V-9 | low | Verification | Conventions | The commit conventions describe a target as if it were the current state | See R-15. | same as R-15 |
| V-10 | low | Verification | AD-18 · Deferred | The 60-day keepalive can't be verified in story 8 | Make the enable-API call the primary keepalive and the commit secondary. |  |
| V-11 | low | Verification | Stack · AD-11 | Stack rows are missing, and PEP 723 transitive dependencies float | Add the rows, and lock the scripts. | → I-2 |
| V-12 | low | Verification | AD-18 | CodeQL's `build-mode` needs one language per job | Run `codeql` as a matrix over the languages. | previously raised |
| V-13 | low | Verification | Stack | The CI SDK floats with `latestPatch`, and the inventory is stale | State the roll-forward rule, and fix the inventory line upstream. | previously raised |
| X-12 | low | Security | AD-6 · AD-12 · AD-19 | Untrusted triggers and permission defaults are left implicit | No `pull_request_target` or `workflow_run`. Top-level `permissions: {}`. zizmor runs over every workflow. |  |
| X-13 | low | Security | AD-8 · AD-18 | commitlint and jscpd may load configuration from the scanned module | Run both with explicit configs from Builds. |  |
| X-14 | low | Security | AD-8 | Restore's isolation from module code is implied, not stated | Restore runs only Builds code with `python3 -I`, and consumes nothing from the CI job. |  |
| X-15 | low | Security | AD-17 · Deferred | Release provenance is absent, and not recorded as out of scope | Deferred: attestations and immutable releases, decided in story 3. |  |
| X-16 | low | Security | AD-21 | The `delivered/**` ruleset doesn't restrict branch creation | Block creation too. Only the App creates or updates. | → I-8 |

## What held

- The deterministic lint is clean: 21 ADs, each with Binds, Prevents and Rule, no placeholders, and every Stack version pinned.
- All 23 Stack pins are current on 2026-11-08. The platform mechanics the design leans on were confirmed: `$/` on runner 2.338.2, the `job.workflow_*` contexts, Trusted Publishing from the caller job, CodeQL categories, and per-repo rulesets on GitHub Free.
- Fork PRs can't reach secrets. The org's default workflow permission is `read`, and first-time contributors need approval.
- Every pass-3 adversary hole is closed. The story order meets every AD ordering condition. Every upstream item the spine handed to the spec landed in the refresh (4666c3d).
- CAP-1 to CAP-16 are all mapped to ADs.

## Full reviews

- Rubric walker: `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/reviews/review-rubric-validate.md`
- Verification: `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/reviews/review-verification-validate.md`
- Adversary: `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/reviews/review-adversary-validate.md`
- Spec reconcile: `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/reviews/review-reconcile-validate.md`
- Security and supply chain: `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/reviews/review-security-validate.md`
