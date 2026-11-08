# Security and supply-chain review: ARCHITECTURE-SPINE.md (update gate, 2026-11-08)

**Verdict:** The revision closes the key-theft paths. The App key now sits only in `main`-only, stdlib-only jobs, and the publish credentials sit behind a `main`-only environment. No critical issue remains. Four high issues are left, and each has a small rule-text fix:
- The unattended bump can push third-party render output, and a tag choice, that no trusted job re-checks (U-X1).
- Stuck-draft completion picks its artifact by name (U-X2).
- Org agent Apps on modules can still publish straight from `main` (U-X3).
- The legacy org credentials undercut `hexalith-release` until the last module adopts (U-X4).

## Scope and method

- **Lens:** security and supply chain only, against the threat model as briefed:
  - public repos on GitHub Free;
  - agents push straight to `main`;
  - careless agents are in model;
  - fork-PR authors and compromised dependencies are out of model, but anything they can exploit is rated at least high.
- **Target:** `ARCHITECTURE-SPINE.md` as of `updated: 2026-11-08`. Line numbers refer to that file. The decisions come from `.memlog.md` after "Update run 2026-11-08" (D1 A, D2 A, D3 A, D4 A, I-2..I-12).
- **Live read-only checks** (`gh api`, 2026-11-08):
  - Org: plan `free`; `default_repository_permission: read`; 2FA required; `allowed_actions: all`; `sha_pinning_required: false`; default workflow permission `read`; fork approval `first_time_contributors`.
  - Org owners: `jpiquot` and `tinouit`. Both are admins on CiCd, Builds and EventStore.
  - CiCd and Builds: no teams, no deploy keys, no outside collaborators.
  - Installations:
    - `claude`, `chatgpt-codex-connector` and `cursor` have `repository_selection: all`, with contents, workflows and actions write. D3 is not applied yet.
    - `semgrep-app` (all repos) has workflows, actions and **secrets** write, plus single-file write on `.github/workflows/semgrep.yml` and `.semgrepignore`.
    - No other installation has contents, workflows or single-file write.
  - CiCd: no environments, no rulesets; immutable releases off; secret scanning and push protection off.
  - Builds:
    - one `Protect main` ruleset; immutable releases off;
    - environment `production`: required reviewer `jpiquot`, branch `main`;
    - releases: the last 100 are all by `github-actions[bot]`, `immutable: false`, target `main`, latest `v4.44.13`.
  - Org secrets: `NUGET_API_KEY`, `HEXALITH_ZOT_*`, `AZURE_*` and `SONAR_TOKEN` are all `visibility: all`. `NUGET_API_KEY` is read by 15 legacy module `release.yml` files and 2 recovery workflows. `HEXALITH_ZOT_*` is read by 4 modules.
  - Agent-App use, from PR heads:
    - `codex/*`: 42 PRs on 9 repos, most recent on EventStore (2026-10-09); also Commons, Folders, FrontComposer, Memories, Parties and AI.Tools;
    - `claude/*`: last 2026-01-10 (Commons) and 2026-01-04 (Builds);
    - `cursor/*`: one PR, 2026-02-26 (EventStore);
    - Semgrep: none.
    - The PRs are authored by `jpiquot`, so the Apps act with the maintainer's identity.
- **Local experiments** (SDK 10.0.403, scratch only): the spine's release command line, run against each module change in the U-X8 table.
- **Docs checked:**
  - GitHub environments: the deployment branch rule is matched against `GITHUB_REF`.
  - GitHub immutable releases: notes stay editable; tags are locked; deleted tags can't be reused.
  - GitHub workflow lockfiles.
  - nuget.org Trusted Publishing: a policy applies to all packages of its owner; "Select Scopes … glob pattern" is now documented.
  - nuget.org scoped API keys.
  - Unit 42 ArtiPACKED: `ACTIONS_RUNTIME_TOKEN` is valid for about 6 h and has been used to replace a run's artifacts.

## Answers to the briefed starting points

| Starting point | Answer | Finding |
| --- | --- | --- |
| `bump` → `bump-push` | Who shapes the commit: CiCd `main` writers, Builds acceptable-tag creators, every locked Python dependency and hash-pinned binary in `bump`, and, if the handoff is by artifact name, any job sharing the nightly run's artifacts. `bump-push` checks only *which paths* change. A poisoned render reaches 17 modules' workflows, the `.claude` deny list and the agent instruction blocks within the hour. The `builds-version` it writes also chooses which Builds code runs inside the key job. | U-X1 |
| `deliver` runs after `validate` whatever its result | A malicious `main` could already do anything: it controls `deliver.yml` itself (accepted). What's new is that a *broken* `main`, whose own tool tests fail, runs its `tools/deliver.py` with the App on every module, every hour. | U-X5 |
| Who else can push CiCd `main` | Today: two org owners (`jpiquot`, `tinouit`), the three agent Apps, and `semgrep-app` through single-file write on a workflow path. After the design: also the `bump-push` and `keepalive` `GITHUB_TOKEN`s (contents but not workflows), and the CiCd App token inside key jobs. Contents write alone reaches the key: the `cicd-app` jobs run `tools/*.py` from `main`. Builds tag creators reach it too, through the perimeter library in `deliver`. | U-X6 |
| `publish`, `artifact-run`, `artifact-id`, `version`, `sha` | Module code in `build` controls only its own build, which is inherent. A careless module agent editing a marked draft is bounded by the run-identity check and the version and commit checks, so it can only point at gated artifacts. The gap is complete mode: it takes "the `release` artifact" of the named run by name. Any code in that run that leaks the runtime token can swap it. `version` is also unbounded. | U-X2, U-X13 |
| Restore | Closed as specified. Hardening is still needed for git over an untrusted checkout. | U-X11 |
| Audit lint, `-noAutoResponse`, `RestoreConfigFile` | Verified effective. `MSBuildWarningsNotAsErrors` and `MSBuildTreatWarningsAsErrors=false` don't get past the gate. An `<Import>` of a file with an unlisted extension does, and so does `NoWarn` under `ItemDefinitionGroup`. Accepting the obfuscated `NoWarn` case is reasonable. | U-X8 |
| Acceptable tag; `v*` creation deferred | The rule is sound. It is evaluated only in jobs that run third-party code (`validate`, `bump`), never in a trusted job. Deferring the `v*` creation restriction is reasonable once D3 is live: only the owners and CiCd agents can create Builds tags. | U-X1, U-X6 |
| Immutable releases timing | Builds: correct, and re-checked before the bootstrap. Modules: switched on by hand after adoption, and nothing checks it. | U-X14 |
| `cache-mode`, `persist-credentials`, `permissions: {}`, triggers, `run:` | Closed for the release. CiCd's own workflows have no cache rule. The trigger rule is a denylist. | U-X10, U-X12 |
| Secrets placement | Pull pair as an Actions and Dependabot secret: accepted (pull-only). Push pair in `hexalith-release`: correct, but nothing says it's a different Zot identity from the legacy `HEXALITH_ZOT_*`. Kill switch as a repo variable: only admins can write it (no App holds `variables`), accepted. Legacy secrets: being restricted doesn't stop them publishing adopted modules' packages. | U-X3, U-X4 |

---

## X-1..X-16 closure

| ID | Was | Status | Rule that closes it (quoted) | Residual |
| --- | --- | --- | --- | --- |
| X-1 | critical | **Closed** | AD-7 l.207 "A job in `cicd-app` runs only stdlib Python (`python3 -I`), git and SHA-pinned actions, and parses only JSON. Render, validation, tests, linting and the scan run in jobs with no secrets." AD-11 l.285 "locked with `uv lock --script` … run with `uv run --locked`". AD-7 l.208 "passing `owner`, `repositories` and `permission-*` for each use". | The key can't be read by third-party code any more. Third-party *output* still reaches key jobs as data (U-X1), and so does Builds code at an unchecked tag (U-X6). |
| X-2 | high | **Closed** (by design; live preconditions pending) | AD-7 l.206 "only a secret of the CiCd environment `cicd-app`, whose only deployment branch is `main`"; AD-6 l.186 "`validate`, with no secrets"; AD-7 l.213 Apps "installed on selected repos that exclude CiCd and Builds"; AD-7 l.209 accepts the CiCd-agent path; AD-21 l.544, l.547. GitHub matches the branch rule against `GITHUB_REF`, so `refs/pull/*/merge` and branch pushes can't deploy. Fork runs get no secrets at all. | Live: the Apps are still `all`, and CiCd has no environment yet. The key-reach statement leaves out a second owner and Contents-only writers (U-X6). |
| X-3 | high | **Partly closed** | AD-10 l.268 "acceptable only if its GitHub release is published and immutable, authored by `github-actions[bot]` … and its commit is an ancestor of Builds `main`"; AD-3 l.123 global checks; AD-18 l.427 "runs the AD-3 global checks on the bumped tree"; AD-19 l.488 immutable before the first rewritten release. | Acceptability is checked only in no-secret jobs that run third-party code. `bump-push` and `deliver` take it on trust (U-X1, U-X6). Restricting `v*` creation is deferred (l.686), which is reasonable after D3. |
| X-4 | high | **Partly closed** | AD-7 l.210 "`hexalith-release`, whose only deployment branch is `main` … each nuget.org Trusted Publishing policy names it"; AD-18 l.419 pre-dispatch blob check; AD-16 l.365 "any other value fails". | 1. Agent Apps on modules can still push an edited `release.yml` to `main` (U-X3). 2. Legacy `NUGET_API_KEY` and `HEXALITH_ZOT_*` (U-X4). 3. Builds' interim policy has no environment (U-X7). 4. Package scoping is deferred (l.686). |
| X-5 | high | **Closed** (create mode) | AD-17 l.378 "Every job declares `permissions:` … `contents: read`, no secret except `nightly-hook`'s pull pair, and `persist-credentials: false`"; l.387 "outputs only its artifact ID and digest"; l.388 `draft` is stdlib; l.395 "Download the artifact by ID … Check its digest, each `.nupkg`'s version and repository commit". | D1's complete mode reopens a variant: lookup by name (U-X2). |
| X-6 | high | **Closed** (release) | AD-17 l.375 and l.378 `cache-mode: none`; l.408 "`package-manager-cache: false` … `enable-cache: false` … restores no NuGet cache". | CiCd's `nightly.yml` and `deliver.yml` have no cache rule (U-X10, low). |
| X-7 | medium | **Partly closed** | AD-17 l.387 "`-warnaserror:NU1900;NU1903;NU1904;NU1905`"; conventions l.566 "`-noAutoResponse` and `-p:RestoreConfigFile=<Builds' nuget.org-only NuGet config>` everywhere"; AD-8 l.226 lint list; AD-4 l.158 `**/Directory.Build.rsp` absent. The independent-verdict script was rejected and the obfuscated `NoWarn` case accepted (memlog). | Verified: an imported `.inc` file and an `ItemDefinitionGroup` `NoWarn` still get past the gate (U-X8, low). |
| X-8 | medium | **Closed** | AD-3 l.116 "The schema constrains every string a template writes into YAML …"; AD-5 l.174 "every value through a `tojson` filter, with `StrictUndefined`"; AD-3 l.123 "actionlint and zizmor over … `rendered/**`". | none |
| X-9 | medium | **Closed** | AD-14 l.338 "Every secret its job references is readable by all of that job's steps, so the CI job and `nightly-hook` hold only the pull-only registry pair. Hook secrets … to a separate job"; AD-8 l.225 "every `uses:` in it is `./…` or a third-party action at a full commit SHA, never `Hexalith/Hexalith.Builds`"; conventions l.561 `persist-credentials: false`. | The guard's SHA check is lexical: an impostor (fork-only) SHA passes it. Accepted under the threat model; GitHub's `actions.lock` (which rejects fork-only commits) is the later upgrade. |
| X-10 | medium | **Closed** (creation) | AD-16 l.358–363: author `github-actions[bot]`, `target_commitish` = trailer and an ancestor of `main`, `tag_name` above the last reachable `v*`. "Every other draft is unmarked and never touched." | Drafts stay editable by any Contents writer until publish. That is bounded in U-X2 and U-X13. |
| X-11 | medium | **Closed** | AD-11 l.286–288 "pinned by version and integrity … `npm ci --ignore-scripts`, then `npm audit signatures`; downloaded binaries through a SHA-256"; l.285 uv lock; conventions l.565 "its online audits". | none |
| X-12 | low | **Closed** (by design; live pending) | Conventions l.561 "top-level `permissions: {}` … no `pull_request_target` or `workflow_run` … no expression inside `run:`"; AD-21 l.523 "keep the org's default workflow permission at `read`, and require approval for fork PRs from all external contributors". | Live: fork approval is still `first_time_contributors`. The trigger rule is a denylist (U-X12, low). |
| X-13 | low | **Partly closed** | AD-8 l.227 "run with `--config` from the guard's own action path"; AD-4 l.158 `.commitlintrc*` absent. | The jscpd explicit-config rule is in the memlog but not in the spine (U-X15). |
| X-14 | low | **Closed** | AD-8 l.232 "It runs only Builds code at the workflow's own commit, with `python3 -I`. It recomputes the expected state from `delivered/<Repo>` and takes nothing from the CI job except its drift flag. It never runs when `module-root` is set." | git over the untrusted checkout (U-X11, low). |
| X-15 | low | **Closed** (deferred) | Deferred l.685 "Story 3: provenance …". | none |
| X-16 | low | **Closed** (by design; live pending) | AD-21 l.546 "a ruleset on `delivered/**` that blocks creation, deletion and force-push, with the App as its only bypass". | Live: CiCd has no rulesets yet. |

**Tally:** 12 closed (X-1, X-2, X-5, X-6, X-8, X-9, X-10, X-11, X-12, X-14, X-15, X-16), 4 partly closed (X-3, X-4, X-7, X-13), 0 open. X-2, X-12 and X-16 depend on maintainer preconditions that aren't applied yet. That is expected for a design, but story 1 has to check each one.

---

## Findings

### U-X1 — high — `bump-push` pushes third-party render output and a tag choice that no trusted job re-checks (AD-18, AD-10, AD-6)

- **Location:** AD-18 l.427 (`bump`), l.428 (`bump-push`); AD-10 l.268–269; AD-6 l.192–193; AD-5 l.177.
- **Scenario (compromised dependency, out of model, so at least high):**
  - `bump` runs Jinja2, PyYAML, jsonschema and their transitive dependencies (locked, but a careless lock refresh can pull in a freshly compromised release), plus actionlint and zizmor. It hands a commit to `bump-push`, whose only content check is that the commit "changes only `builds-version` and `rendered/`".
  - So the bump job writes `rendered/<Repo>/.github/workflows/*.yml`, `.claude/settings.json` `permissions.deny`, the `AGENTS.md`/`CLAUDE.md` marker blocks and every perimeter. `bump-push` pushes them to CiCd `main` unattended and dispatches `deliver.yml`.
  - `validate` re-renders with the same locked dependencies, so a compromised one reproduces its own output and "render with no diff" passes. `deliver` then writes the result into all 17 modules with the App, which holds Workflows write.
  - The rendered `release.yml` runs on `main` and so reaches `hexalith-release`: the push pair, and a nuget.org key for every package of the owner. The instruction blocks become a prompt-injection channel into every agent session, in every module.
  - `bump-push` also never re-derives `builds-version`. A poisoned bump can point it at a tag in `builds-skip` (a known-bad rollback) or at any other existing tag. `deliver` step 3 then *runs Builds' perimeter library at that tag inside the `cicd-app` job* (l.193). Third-party code thereby chooses which code runs with the key.
- **Scenario (careless CiCd agent, in model; medium on its own):**
  - An agent pushes a `templates/` or `setup/` change without re-rendering, which breaks AD-5 l.175. The global checks go red, so no ref advances.
  - At 02:17 the bump re-renders the whole tree, folds the unreviewed change into a `build(cicd): bump Builds to …` commit that touches only `rendered/` and `builds-version`, and pushes it. Delivery ships it to 17 modules. Nobody ever saw that render diff.
- **Evidence:**
  - l.428 "checks that the bump commit changes only `builds-version` and `rendered/`".
  - l.193 "with Builds' perimeter library, from a shallow clone of Builds at that ref's `builds-version`".
  - l.123 acceptability is a global check, which runs in `validate` (no secrets, third-party code).
  - Memlog I-3: "bump-push … checks the commit touches only builds-version and rendered/".
- **Fix (AD-18 `bump-push`, stdlib only):**
  > "`bump-push` takes the bump commit by the artifact ID the `bump` job outputs, and pushes it only if:
  > - its parent is the run's `github.sha`;
  > - `bump-push`'s own API reads confirm that the new `builds-version` is the newest acceptable tag (AD-10) in the current major and not in `builds-skip`;
  > - every changed file under `rendered/` equals its parent copy with the old tag replaced by the new one, and the old gitlink commit by the new tag's commit. The one exception: a `hexalith-ci.json` may also gain keys whose values equal the `default` in the new tag's `schemas/hexalith.ci.v<N>.json`.
  >
  > Any other difference fails the night and names the file."

  A within-major bump changes nothing else, because templates are CiCd's and perimeter shape changes need a major (AD-10 l.265). So this check costs nothing in normal operation. It also turns the careless case into a red night instead of a silent delivery.

### U-X2 — high — Completing a stuck draft picks "the `release` artifact" by name, so a leaked runtime token can swap what gets published; `version` is unbounded (AD-17, AD-16)

- **Location:** AD-17 l.387 (`build`), l.388 (`draft`, create), l.390 (`draft`, complete), l.393, l.395; AD-16 l.361; Release markers l.558.
- **Scenario (compromised dependency or module custom action in a read-only job of the creating run; out of model, so at least high):**
  1. In run R, `nightly-hook` (module custom action code), `version` (npm tools) or `codeql` runs with `contents: read`. With passwordless `sudo` it reads `ACTIONS_RUNTIME_TOKEN` from Runner.Worker memory and sends it out. The token is valid for about 6 hours.
  2. After `build` uploads `release`, the attacker replaces it with the token: delete and re-upload under the same name, which issues a new ID.
  3. Create mode is safe: `publish` downloads the original ID, which is gone, so it fails.
  4. That failure leaves a marked draft. The next night's complete mode "takes the `release` artifact of the run named by `hexalith-release-run:`", which is the replacement. Its digest, read from the API, matches it. The `.nupkg` version and repository-commit checks pass, because the attacker wrote the nuspec.
  5. The honest `publish` job then pushes the attacker's packages and containers through Trusted Publishing and the push pair.
- **The second half (create mode):** `version` comes from third-party npm code. The only bound is "above the last `v*` tag" (l.361), checked at publish. A compromised commit-analyzer can therefore ship the honest build as `v99.0.0`. That version can't be taken back on nuget.org, and floating ranges pick it up.
- **Evidence:**
  - l.390 takes the artifact by run, not by ID.
  - l.393: the complete-mode `artifact-digest` can only come from the API, so it is self-consistent.
  - Unit 42, ArtiPACKED (August 2024): the runtime token "with an expiration of about six hours" was used to "replace the original artifact with a new one". https://origin-unit42.paloaltonetworks.com/?p=136260 and https://thehackernews.com/2024/08/github-vulnerability-artipacked-exposes.html
  - Upload-artifact v4+ names are immutable unless `overwrite: true`, which deletes and re-creates the artifact under a new ID (memlog constraint).
- **Fix (AD-17 `draft`, plus one Release-markers entry):**
  > "Create mode: `draft` checks through the API that the artifact ID from `build` belongs to this run, is named `release`, and has the digest `build` output. It writes `hexalith-release-artifact: <id> <sha256>` into the draft body. It accepts `version` only if it is the last `v*` tag reachable from the SHA with exactly one of major, minor or patch incremented (lower parts zeroed).
  >
  > Complete mode: `draft` uses exactly the artifact named by that trailer, and fails if it is missing from the named run or its API digest differs."

  `publish` then checks against that digest. A trailer edit needs Contents write. Only module agents and agent Apps hold it, and an App that can edit drafts can already publish (U-X3), so this adds no new path.

### U-X3 — high (residual; accept only with the scope cuts below) — Org agent Apps on modules can publish from `main`; the `main`-only environment doesn't stop a `main` push (AD-7, AD-21)

- **Location:** AD-7 l.210, l.213; AD-21 l.532; Deferred l.686; Structural Seed l.606.
- **Scenario (prompt-injected agent App, out of model; or a careless one "fixing" a release):**
  - `claude`, `chatgpt-codex-connector` and `cursor` hold contents, workflows and actions write on every module. `semgrep-app` can write `.github/workflows/semgrep.yml` on every repo through single-file permission.
  - One of them pushes to module `main` an edited `release.yml` (adding `on: push`) or any workflow with a job in `environment: hexalith-release`.
  - The job runs at once on `main`. The environment admits it, the nuget.org policy matches (same file name, same environment), and the push pair is readable. The temporary nuget.org key covers every package of the owner, because package scoping is deferred.
  - The guard, the pre-dispatch check, the release drift check and hourly delivery all act *after* the push. They repair the file, not the publish.
  - The Apps act with the maintainer's identity: their PRs are authored by `jpiquot`. So a ruleset with a role-based bypass can't tell them apart from the module-agent token, and "Restrict updates" on modules is no cheap fix.
- **Evidence:**
  - Live installation permissions and `repository_selection: all`.
  - `codex/*` PRs on EventStore until 2026-10-09, and on six other modules; `claude/*` last 2026-01-10; `cursor/*` one PR, 2026-02-26; no Semgrep use found.
  - Trusted Publishing: "The policy will apply to all packages owned by the selected owner"; the Learn page now also documents "Select Scopes … The associated glob pattern can be used to target specific packages". https://learn.microsoft.com/nuget/nuget-org/trusted-publishing
- **Fix (AD-21 maintainer preconditions plus AD-7 wording; pragmatic):**
  > "Before the first adoption, `claude`, `cursor` and `semgrep-app` exclude all 18 managed repos. `chatgpt-codex-connector` is installed only on the modules where it is used.
  >
  > Each module's nuget.org policy is scoped to that module's package-ID prefix (story-1 check; the Learn page documents policy glob scopes). Each `hexalith-release` push pair is a Zot identity that can push only that module's repositories.
  >
  > AD-7: 'An agent App on a module can publish that module's packages and containers through an edited workflow on `main`. Accepted.'"

  With those cuts, the residual is one module's packages, from one App, and it is reasonable to accept.

  **Preventive upgrade, if wanted later:** a module branch `release` that only the CiCd App can update (ruleset, App-only bypass, no role bypass). `nightly` fast-forwards it to the SHA it just blob-checked and dispatches there, and `hexalith-release` is deployable from `release` only.

### U-X4 — high — Legacy credentials undercut `hexalith-release` until the last module adopts (AD-21, Secrets convention)

- **Location:** AD-21 l.522; Secrets convention l.560; AD-7 l.210.
- **Scenario (compromised dependency in a not-yet-adopted module's legacy release job, out of model; or a careless agent with any branch workflow there):**
  - `NUGET_API_KEY` is a long-lived nuget.org key (updated 2025-09-20). It is an org secret with `visibility: all`, read by 15 legacy module release workflows. "Restrict … to the repos that still read them" still leaves it readable by any workflow, on any branch, in up to 16 repos, for the whole migration (stories 11–26).
  - Unless its nuget.org glob is narrower than the owner's packages, it pushes new versions of *adopted* modules' packages. That defeats D2 for those packages.
  - The same holds for containers if `HEXALITH_REGISTRY_USERNAME/_PASSWORD` reuse the identity behind `HEXALITH_ZOT_*` (`visibility: all`, read by 4 modules).
  - Today CiCd and Builds can read both secrets as well.
- **Evidence:**
  - `gh api orgs/Hexalith/actions/secrets` (visibilities).
  - `grep` over `references/*/.github/workflows/`.
  - Scoped API keys: "you can scope the key to specific packages or glob patterns" and "Edit existing API keys to change package applicability". https://learn.microsoft.com/nuget/nuget-org/scoped-api-keys
- **Fix (AD-21, once and per repo):**
  > "Once, before the first adoption: CiCd and Builds are removed from every legacy org secret. `HEXALITH_REGISTRY_*` is a Zot identity distinct from `HEXALITH_ZOT_*`.
  >
  > At each adoption, in the same maintainer step that creates `hexalith-release`: remove the module's package IDs from the legacy `NUGET_API_KEY` scope (edit, or regenerate with the remaining IDs and an expiry no later than the planned last adoption), remove the repo from the legacy secrets' selected repos, and revoke the legacy Zot identity's push on the module's repositories."

### U-X5 — medium — A red CiCd `main` runs its own failing tools with the App key, hourly (AD-6, AD-7)

- **Location:** AD-6 l.187 "after `validate` whatever its result, in environment `cicd-app`"; l.192–196; AD-7 l.207; memlog I-5.
- **Scenario (careless CiCd agent, in model):**
  - An agent pushes a `tools/deliver.py` change whose tool tests fail in `validate`.
  - Before I-5 that kept the key job from running. Now `deliver` still runs step 3 with the broken `deliver.py`, from the run's commit, for every module that has a ref, every hour until `main` is fixed.
  - A bug in path handling or perimeter application pushes bad `build(cicd)` commits into 17 modules. If it touches owned files, each module's restore fights it (restore → `ci.yml` → next delivery), which is exactly the restore loop AD-8 is meant to prevent. Product files deleted by the bug need a manual revert in each module.
  - A *malicious* `main` is out of scope here: it controls `deliver.yml` itself, and that is accepted.
- **Fix (AD-6, one sentence):**
  > "When this run's global checks failed, the `deliver` job runs steps 1 and 3 with `tools/` checked out from the newest commit that a `delivered/*` ref points to, never from the run's commit."

  That code passed the global checks, tool tests included, when its ref advanced, and the CAP-8 one-hour bound is kept.

### U-X6 — medium — AD-7 understates who can reach the key, and the key job runs Builds code at a tag no trusted job checked (AD-7, AD-6, AD-21)

- **Location:** AD-7 l.206–209, l.214; AD-6 l.193; AD-21 l.543–547; Structural Seed l.603.
- **What the spine says:** "A CiCd-agent session can still reach it through a push to CiCd `main`."
- **What is actually true:**
  1. **A second org owner, `tinouit`,** is admin on CiCd and Builds. The spine names only "the maintainer", and its rules on agent sessions and personal tokens (l.214) bind only that one person.
  2. **Contents write is enough; Workflows write is not needed.** The `cicd-app` jobs run `tools/deliver.py` and `tools/nightly.py` from `main`. Any CiCd Contents writer gets the key that way: owners, the CiCd-agent token, any App user-to-server token on CiCd, and `bump-push`'s `GITHUB_TOKEN`, which is bounded only by `bump-push`'s own check (U-X1).
  3. **Builds tag creators.** `deliver` runs Builds' perimeter library from the tag in each ref's `builds-version`. That tag's acceptability was last checked in `validate`, which runs third-party code (U-X1).
  4. **The App token for CiCd.** To advance `delivered/*`, `deliver` mints a CiCd token with Contents write. That token can also push CiCd `main`, and it may be live while Builds code runs in the same job.
  5. **`semgrep-app`** can add `.github/workflows/semgrep.yml` to CiCd `main` without Contents permission. D3 removes it, but nothing re-checks D3.
- **Fix (AD-7 wording plus AD-21 "CiCd itself needs"; AD-6 step 3):**
  > "AD-7: 'The key is reachable by every CiCd Contents writer and every creator of an acceptable Builds tag: the org owners (named), CiCd-agent sessions, and the CiCd App. Accepted under the careless-agent model.'
  >
  > AD-21: 'CiCd and Builds have exactly the org owners as collaborators, no deploy keys, and no installation with contents, workflows or single-file write except the CiCd App. `deliver` and `nightly`'s App checks read the installations, and fail the run if one appears.'
  >
  > AD-6 step 3: 'Before cloning Builds at a ref's `builds-version`, `deliver` confirms with stdlib API reads that it is an acceptable tag, and checks the clone's commit against the tag. The CiCd token for advancing `delivered/*` is minted only after Builds code has finished.'"

### U-X7 — medium — Builds' interim nuget.org policy has no environment, so any Builds branch run of `builds-release.yml` can mint (AD-19)

- **Location:** AD-19 l.479, l.482 "the nuget.org policy names `builds-release.yml` with no environment"; memlog D2 "Builds' policy keeps no environment while the interim legacy release runs under `production`".
- **Scenario (careless CiCd agent, in model):**
  - From the rename (story 2) to the rewrite (story 3), any run of a file named `builds-release.yml` in Builds can trade its OIDC token for a key to every Hexalith package. That holds on any branch and for any event.
  - A CiCd agent iterating on the story-3 rewrite on a branch, with `on: push` for testing, publishes real packages, and they can't be unpublished.
- **Evidence:**
  - Live: Builds' `production` environment is `main`-only, with required reviewer `jpiquot`.
  - The legacy job uses `environment: production` on every ref except `prerelease`, and runs `NuGet/login` in that same job (references/Hexalith.Builds/.github/workflows/build-release.yml:36, :74).
  - A policy that names `production` therefore accepts the interim file as it is.
- **Fix (AD-19 precondition):**
  > "Until the rewrite, Builds' nuget.org policy names `builds-release.yml` with environment `production`. The rewrite switches it to `hexalith-release`."

### U-X8 — low — The audit lint misses imported files with other extensions, case variants, and `ItemDefinitionGroup` `NoWarn` (AD-8)

- **Location:** AD-8 l.226.
- **Evidence:** local experiment, SDK 10.0.403, with the spine's release flags:

  `dotnet build -c Release -noAutoResponse -p:RestoreConfigFile=<nuget.org-only> -warnaserror:NU1900;NU1903;NU1904;NU1905 -p:NuGetAudit=true -p:NuGetAuditMode=all -p:NuGetAuditLevel=low`

  The test project references `Newtonsoft.Json 12.0.1`, uses TWAE and has `WarningsNotAsErrors` NU1901–NU1904.

  | Module change | Exit | Caught by the AD-8 lint as written? |
  | --- | --- | --- |
  | baseline | 1 (`error NU1903`) | n/a |
  | `MSBuildWarningsNotAsErrors=NU1903` | 1 | n/a (no bypass) |
  | `MSBuildTreatWarningsAsErrors=false` | 1 | n/a (no bypass) |
  | `<Import Project="build/audit.inc"/>` holding `MSBuildWarningsAsMessages` | **0** | no: `.inc` is not a listed extension |
  | `<Import Project="build/waivers.inc"/>` holding `NuGetAuditSuppress` | **0** | no |
  | `<ItemDefinitionGroup><PackageReference><NoWarn>NU1903` | **0** | only if "a `NoWarn` element" matches under any parent |

- **Notes:**
  - Module imports use computed paths (`$(Hexalith2BuildPackageProps)`), so a lint can't resolve them statically.
  - Two modules ship `NuGet.config` rather than `nuget.config`. With `RestoreConfigFile` this matters less, but the lint should still match the name case-insensitively.
  - Accepting the obfuscated `NoWarn` case remains reasonable.
- **Fix (AD-8 lint scope):**
  > "…over every tracked file whose root element is an MSBuild `<Project>`, whatever its extension, plus `*.rsp` and `nuget.config` matched case-insensitively. A `NoWarn` element or attribute matches under any parent."

### U-X9 — low — `delivered-sha` is taken on trust and can be fetched by bare SHA (AD-17, AD-18)

- **Location:** AD-17 l.381 "against the `delivered-sha` input"; AD-18 l.419.
- **Scenario:**
  - Anyone with Actions write on a module can dispatch `release.yml` with any `delivered-sha`: owners, the agent Apps and the CiCd App.
  - If the drift check fetches that commit by SHA from the public CiCd repo, it can get any fork-network commit, including one whose `rendered/<Repo>` matches a drifted module.
  - The green-CI gate still reads the live ref through the guard, which blocks the obvious use. So this is defense in depth.
- **Fix (AD-17 resolve):**
  > "`delivered-sha` is accepted only if it is the live `delivered/<Repo>` commit or one of its ancestors. The check fetches the branch, never a bare SHA."

### U-X10 — low — CiCd's own workflows have no cache rule (Workflow security convention, AD-17)

- **Location:** conventions l.561; AD-17 l.408 covers Builds only.
- **Scenario:**
  - A compromised dependency in `validate` on `main` writes a poisoned uv cache entry scoped to `main`.
  - `bump` (and the next `validate`) restore it, so the compromise survives the fix of the dependency or lock.
- **Fix (conventions):**
  > "CiCd's `deliver.yml` and `nightly.yml` declare `cache-mode: none`, and set `enable-cache: false` on setup-uv."

### U-X11 — low — Untrusted module content and artifacts in key and write jobs need explicit handling (AD-6, AD-8, AD-17, AD-18)

- **Location:** AD-6 l.193 (sparse clones of module `main` in `cicd-app`); AD-8 l.230–233 (restore over the module checkout); AD-18 l.421 (`wait` reads 18 outcome artifacts); AD-17 l.394–399 (`publish` handles the build's files).
- **Scenario:**
  - Module trees are untrusted in jobs that hold the App or a write token. Risks:
    - submodule recursion;
    - Git LFS smudge to an `.lfsconfig` URL;
    - an unscoped `http.extraheader`, which LFS forwards to any host.
  - Outcome zips and module JSON are untrusted input to stdlib parsers. One module's malformed file can abort the whole loop, which breaks AD-3's "one module's state blocking all others".
  - The build artifact becomes files on the `publish` runner. A crafted `nuget.config` or `global.json` in its working directory is read by `dotnet`.
- **Fix (one AD-7 bullet, one AD-17 bullet):**
  > "AD-7: in `cicd-app` and restore jobs, git runs with no submodule recursion, `GIT_LFS_SKIP_SMUDGE=1` and `core.hooksPath=/dev/null`, and receives tokens only as a header scoped to `https://github.com/`. Artifacts are read in memory with a size cap, never extracted. Each module is processed in isolation, and one module's failure is reported without stopping the others.
  >
  > AD-17: `publish` extracts the artifact outside its working directory, runs `dotnet nuget push` and the container push tool from an empty directory, and names the source by its full URL."

### U-X12 — low — The trigger rule is a denylist (Workflow security convention)

- **Location:** conventions l.561.
- **Scenario:**
  - `issue_comment`, `issues`, `repository_dispatch`, `check_run` and similar triggers run `main`'s workflow with `GITHUB_REF=refs/heads/main`. So they can deploy to the `main`-only `cicd-app` and `hexalith-release` environments, and they carry attacker-controlled event text.
  - Banning only `pull_request_target` and `workflow_run` leaves them open to a careless edit.
- **Fix (conventions):**
  > "Workflows trigger only on `push`, `pull_request`, `schedule`, `workflow_dispatch` and `workflow_call`. A job in an environment also tests `github.event_name` against an allowlist."

### U-X13 — low — The publish step re-reads the draft, then publishes it: a time-of-check gap (AD-17)

- **Location:** AD-17 l.395 "that the draft is still marked", l.399 "Publish the draft".
- **Scenario:** a Contents writer (module agent or agent App) edits `tag_name` or `target_commitish` between the check and the publish call. The tag then lands on a different commit.
- **Fix (AD-17 publish step 5):**
  > "The publishing request sets `tag_name`, `target_commitish` and `draft: false` together, and the step checks the returned release before reporting `published`."

### U-X14 — low — Module immutable releases and push protection are manual and unchecked (AD-21)

- **Location:** AD-21 l.540 "The maintainer then turns on immutable releases".
- **Scenario:**
  - A forgotten toggle leaves module release assets and tags editable.
  - Secret scanning push protection is off on CiCd (live). It's free for public repos, and it is the cheapest guard against an agent committing the key or a PAT.
- **Fix (AD-21 step 3, and once):**
  > "The org enforces immutable releases for the managed repos as each one adopts (`enforced_by_owner`). `nightly`'s App checks read `immutable-releases` for adopted modules and fail the night when it is off. Secret scanning push protection is on for all 19 repos."

### U-X15 — low — The jscpd explicit-config rule never reached the spine (AD-18; X-13 residual)

- **Location:** AD-18 l.426; the memlog's X-13 decision says "jscpd with an explicit config".
- **Scenario:** a module's `.jscpd.json` steers the duplicate scan, which is CAP-9's signal, in the no-secret `scan` job.
- **Fix (AD-18 `scan`):**
  > "`scan` runs jscpd with its config from CiCd, and never reads configuration from a module."

---

## Counts

- critical 0
- high 4 (U-X1, U-X2, U-X3, U-X4)
- medium 3 (U-X5, U-X6, U-X7)
- low 8 (U-X8 to U-X15)

## Residuals reasonable to accept under the threat model

- **CiCd-agent sessions and the org owners can reach the key.** The spine accepts this; U-X6 only asks that it name the whole set.
- **Builds `v*` tag creation is unrestricted** until the story-1 check. Once D3 is live, the only creators are the owners and CiCd agents.
- **The obfuscated `NoWarn` case** stays accepted.
- **Complete mode doesn't re-run the audit** on a draft completed after a new advisory. It's D1 A's trade-off, and the artifact was gated when built.
- **The pull pair is readable by every step of CI and `nightly-hook`, and by Dependabot runs.** It's pull-only and limited to test images.
- **SHA pins in module custom actions are checked lexically only.** GitHub's `actions.lock` (which rejects fork-only commits) is the later upgrade. The org-wide `sha_pinning_required` policy would block the exact-tag Builds reusable-workflow calls, so it isn't recommended.
- **An agent App on a module can publish that module's packages** (U-X3), once its scope is cut to one module.
