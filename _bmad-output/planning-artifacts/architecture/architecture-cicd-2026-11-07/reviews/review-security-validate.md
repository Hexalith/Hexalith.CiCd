# Security and supply-chain review: ARCHITECTURE-SPINE.md (validate gate)

**Verdict:** The spine keeps fork-PR code away from secrets, but it is not safe to build as written: the org-wide App key and the publish credentials sit in jobs and refs that a compromised dependency, an org agent App or a newly created Builds tag can reach. Five ADs need tightening before stories 2, 3, 4, 7 and 8 lock them in.

Scope and method:
- Lens: security and supply chain only. Threat model as briefed: public repos on GitHub Free, agents push to `main`, careless agents in model, fork-PR authors and compromised dependencies out of model (anything they can exploit is rated at least high).
- Live read-only checks (`gh api`, 2026-11-08):
  - org and repo `default_workflow_permissions` are `read`;
  - fork-PR approval policy is `first_time_contributors`;
  - `allowed_actions` is `all`;
  - immutable releases are `enabled: false` on Builds, CiCd and Parties;
  - Builds has only a `Protect main` branch ruleset, with no tag ruleset;
  - CiCd has no rulesets;
  - org installations: `claude`, `chatgpt-codex-connector` and `cursor` hold `contents`, `workflows` and `actions` write with `repository_selection: all`, and `semgrep-app` holds `workflows` and `actions` write on all repos.
- Local experiments: .NET SDK 10.0.403 against nuget.org, recorded in X-7.
- Spine line numbers refer to `ARCHITECTURE-SPINE.md` as of `updated: 2026-11-08`.

## Answers to the briefed questions (where each is dealt with)

| Question | Answer | Finding |
| --- | --- | --- |
| Fork PR to a module `ci.yml` or CiCd `deliver.yml`: does any job get the App key, secrets, a write token or the pull pair? | No. Fork `pull_request` runs get no secrets and a read-only `GITHUB_TOKEN`, and restore runs only on push to `main`. The exposure is to same-repo branches and to dependencies, not to forks. | X-2, X-12 |
| `pull_request_target` / `workflow_run` excluded? | Not anywhere in the spine. Only SPEC.md:173 mentions the platform's December 2 default block. | X-12 |
| Workflow-level default `permissions:`? | Not stated. Only the CI build job (l.215), restore (l.212) and publish (l.341) are given permissions, and the org default `read` is the only backstop. | X-5, X-12 |
| Script, template and YAML injection | No rule against `${{ github.event.* }}` / `${{ inputs.* }}` in `run:`. Setup values reach YAML through Jinja2 with no escaping rule. | X-8, X-12 |
| App scope and per-job minting | Asserted (l.192) but not specified. `create-github-app-token` defaults to every installation permission. | X-1, X-2 |
| Restore job | Acceptable if it runs no module code. Not stated. | X-14 |
| Custom actions vs secrets in the same job | Yes, they can read them (Runner.Worker memory, docker config). | X-9 |
| Publish job: artifact poisoning, TOCTOU | Outputs and artifact are not integrity-bound, and the build job that produces them runs module code. | X-5 |
| Trusted Publishing scope | Any job in any `release.yml` run, on any ref, can mint a key for every package of the nuget.org owner. | X-4 |
| CiCd-agent PAT → key exfiltration | Yes, through a branch workflow. The same holds for the three org agent Apps. | X-2 |
| Builds `v*` tags immutable? | No tag ruleset exists yet. The planned one doesn't block creation, and immutable releases are off. | X-3 |
| npm, PyPI, uv, binary downloads | Version-pinned only: no lock or hash rule, no `--ignore-scripts`. | X-1, X-11 |
| Provenance and attestations | Absent, and not recorded as out of scope. | X-15 |
| Control loop: undetectable guard disable | A drifted `release.yml` escapes the release drift check, which lives inside the file it should vouch for. | X-4 |
| `ci-workflow` input | Accepted in any repo, but harmless while `release.yml` is undrifted. | X-4 |
| Audit-gate bypasses | Six bypasses confirmed on SDK 10.0.403. | X-7 |

---

## Findings

### X-1 — critical — App private key shares jobs with unlocked third-party code (AD-7, AD-11)

- **Location:** AD-7 (ARCHITECTURE-SPINE.md:192), AD-11 (l.261, l.264), AD-6 (l.176), AD-18 (l.369, l.372).
- **Scenario (compromised dependency):**
  - The CiCd tools run `uv run` over PEP 723 inline dependencies: Jinja2, PyYAML and jsonschema. jsonschema pulls in `attrs`, `referencing`, `rpds-py` and `jsonschema-specifications`, and Jinja2 pulls in `MarkupSafe`.
  - The nightly scan runs jscpd from npm.
  - Without a lockfile, `uv` resolves the newest compatible transitive versions on every run. A malicious release of any of them executes at import, inside `validate` (per-module checks need the App), `deliver` or `nightly`, which are exactly the jobs that hold `HEXALITH_CICD_APP_PRIVATE_KEY`.
  - Step-level scoping doesn't help. The runner holds the job's secrets in the `Runner.Worker` process, and hosted runners have passwordless `sudo`. The tj-actions/changed-files payload (CVE-2025-30066) read that process's memory to dump every secret in the job.
  - The prize is the private key itself, not a one-hour token. It carries Contents, Workflows and Actions write on 19 repos and "is rotated only on leak" (l.530).
  - With it, an attacker can rewrite any module's `release.yml` and mint nuget.org keys for all Hexalith packages (X-4).
- **Evidence:**
  - l.261 "CiCd tools declare PEP 723 inline dependencies and run with `uv run`".
  - l.264 "Third-party tools are called from scripts and pinned in Builds or CiCd". These are version pins on direct dependencies only.
  - l.192 "Each job mints a token … The key never enters … an agent session".
  - uv can lock scripts (`uv lock --script` writes `<script>.py.lock`, which later `uv run --script` calls reuse) and supports `exclude-newer` in `[tool.uv]`: https://docs.astral.sh/uv/guides/scripts/
  - Memory-dump technique: https://www.sysdig.com/blog/detecting-and-mitigating-the-tj-actions-changed-files-supply-chain-attack-cve-2025-30066 and https://www.stepsecurity.io/blog/harden-runner-detection-tj-actions-changed-files-action-is-compromised
  - "The Linux and macOS virtual machines both run using passwordless `sudo`": https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- **Fix (AD-7 Rule tightening, plus one AD-11 line):**
  - "A job that reads `HEXALITH_CICD_APP_PRIVATE_KEY` runs only stdlib Python, git and SHA-pinned actions.
  - Render, schema validation, tool tests and the duplicate scan run in separate jobs with no secrets. Module repos are public, so those jobs clone them anonymously.
  - Each mint passes explicit `repositories` and `permission-*` inputs."
  - AD-11: "CiCd tools are locked with `uv lock --script`. The `.lock` files are committed and run with `uv run --locked`." (See X-11 for the other tool kinds.)

### X-2 — high — The key is reachable from any CiCd branch, and org agent Apps hold write on the hub repos (AD-7, AD-21)

- **Location:** AD-7 (l.192, l.194, l.195), AD-21 CiCd needs (l.456), AD-6 triggers (l.177).
- **Scenario (org agent App, prompt-injected or careless; CiCd-agent session):**
  - A repo secret is available to every push and `workflow_dispatch` run on every branch. `deliver.yml` also validates on non-`main` pushes and same-repo PRs, and its per-module checks need the App, so it mints from branch code.
  - Anyone with Workflows write on CiCd can therefore push a branch whose workflow prints the key base64-encoded, or posts it out. That includes the CiCd-agent PAT (l.194) and the `claude`, `chatgpt-codex-connector` and `cursor` installations, which are verified at `repository_selection: all` with workflows, contents and actions write.
  - The same Apps can write CiCd `main` and create Builds tags (X-3). AD-7's control for them is "the guard, the release drift check and hourly delivery" (l.195), and none of these covers CiCd or Builds. CiCd `main` and Builds tags are the root of trust for all 17 modules.
- **Evidence:**
  - l.192 "The key never enters a module, Builds or an agent session". This is asserted, not enforced.
  - `gh api orgs/Hexalith/installations` (2026-11-08).
  - "Secrets stored in an environment are only available to workflow jobs that reference the environment". Deployment branches and environment secrets are available to public repos on Free: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- **Fix (AD-7 Rule tightening, plus AD-21 CiCd preconditions):**
  - Move the key into a CiCd environment `cicd-app` with deployment branches limited to `main`. Only the `deliver`, `nightly` and per-module-check jobs reference it.
  - On PRs and non-`main` pushes, per-module checks use only anonymous reads.
  - The maintainer sets the three agent Apps and `semgrep-app` to "Only select repositories", excluding CiCd and Builds. The org can't remove their Workflows permission, but it can remove repos from an installation.
  - Restate the rule as "a CiCd-agent session can obtain the key; accepted under the careless-agent model".

### X-3 — high — Any new Builds tag is trusted by the auto-bump and runs with every module's publish credentials (AD-10, AD-18, AD-19, AD-21)

- **Location:** AD-10 auto-bump (l.246), AD-21 rulesets (l.446), AD-19 preconditions (l.413), Action references convention (l.473).
- **Scenario (org agent App, careless CiCd agent, or a compromised Builds workflow with `contents: write`):**
  - Rulesets block update and deletion of `v*` tags, not creation, and immutable releases are off.
  - Anyone with Contents write on Builds can push `v<major>.99.0` at any commit, including one off `main` that `builds-ci.yml` never ran on.
  - At 02:17 the bump adopts "the newest tag in the current major" for all 17 modules, unattended. From then on that tag's `publish` composite runs in every module's publish job (`id-token: write`, `contents: write`, the push pair), its restore code runs with `contents: write`, and its perimeter library runs inside CiCd `deliver` with the App token.
  - The AD-19 check that "every Builds `v*` tag has a published release" (l.413) is a one-time precondition, not a check at bump time.
- **Evidence:**
  - l.246, l.446.
  - Live: `immutable-releases` is `{"enabled":false}` on Builds, and Builds has no tag ruleset.
  - Immutable releases: "Git tags cannot be moved" and the tag "cannot be deleted while the release exists", and publishing generates a release attestation: https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases
  - Rulesets support "Restrict creations": https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- **Fix (AD-10 Rule tightening, plus AD-21 precondition):**
  - "The bump and the global checks accept a Builds tag only if:
    - its GitHub release is published (not a draft) and authored by `github-actions[bot]`;
    - its commit is an ancestor of Builds `main`;
    - it equals the `version` in that night's `builds-release.yml` `outcome.json` (`published`), or the current `builds-version`."
  - Precondition: enable immutable releases on Builds and on every module.

### X-4 — high — Publish credentials aren't bound to the publish job, and the release drift check can't vouch for its own file (AD-17, AD-16, AD-21)

- **Location:** AD-17 (l.341, l.342, l.344), AD-21 (l.445), AD-19 (l.412), Secrets convention (l.469), AD-16 (l.329).
- **Scenario (org agent App with Workflows write, or a compromised Builds tag via X-3):**
  - **Any ref can mint.** The nuget.org policy names only owner, repo and `release.yml`, with no environment. Any job in any run of a file called `release.yml`, on any branch and any event, can mint a key. An App can push a branch with an edited `release.yml` (`on: push`, `id-token: write`) and publish.
  - **Any package can be pushed.** The policy "will apply to all packages owned by the selected owner", so a key minted from Parties can push new versions of Hexalith.Commons. The same goes for the push pair: org secrets are readable by any workflow, on any branch, in all 18 repos.
  - **The drift check can be skipped.** It runs inside the reusable workflow that the (possibly drifted) caller chooses to call (l.344). A drifted `release.yml` simply doesn't call it.
  - **The nightly dispatch runs whatever is on `main`.** It dispatches the module's live `main`, and hourly delivery repairs at :47, so an edit made between 01:47 and 02:17 is what runs.
  - `ci-workflow` is accepted in every repo, unlike `module-root` (l.407).
- **Evidence:**
  - l.342 "No GitHub environment"; l.445 "with no environment".
  - Policy fields, the optional environment and "all packages owned by the selected owner", plus "Select Scopes … glob pattern": https://learn.microsoft.com/en-us/nuget/nuget-org/trusted-publishing
  - Environment secrets are restricted to jobs that reference the environment (URL in X-2).
- **Fix (AD-17 Rule tightening, plus AD-21 precondition):**
  - "The publish job runs in environment `hexalith-release`, with deployment branches limited to `main`.
  - Each nuget.org policy names that environment and scopes package IDs to the module's own prefix.
  - The registry push pair is an environment secret of `hexalith-release`, ideally a per-module Zot identity limited to that module's repositories."
  - AD-18: "Before dispatch, nightly compares the live `main` blobs of `ci.yml` and `release.yml` with `delivered/<Repo>` and skips a drifted module. After each run it checks that the run's `referenced_workflows` names Builds `release.yml` at `buildsTag`."
  - AD-16: "`ci-workflow` other than `ci.yml` is rejected outside Builds."

### X-5 — high — Release jobs mix module and dependency code with write tokens and authoritative outputs (AD-17)

- **Location:** AD-17 steps 5–7 and publish (l.348–l.356). The rule gives no job split and no per-job `permissions`. Only `nightly-hook` is covered, via AD-14 l.309.
- **Scenario (compromised NuGet or npm dependency):**
  - **Step 6.** Build and pack run module MSBuild and every package's `build/*.targets`. The same step also deletes drafts, so it needs `contents: write`.
  - **Step 5.** It installs semantic-release plugins and creates the draft, possibly in one job.
  - Code in either job can, with `contents: write`, push to `main` (rulesets block only deletion and force-push), create new `v*` tags and edit drafts. It can also append to `$GITHUB_OUTPUT` and `$GITHUB_ENV` to steer later steps and the `version`, `sha` and `artifact` outputs that the publish job trusts.
  - Inside a reusable workflow, a job without `permissions:` inherits the caller job's grant.
  - The artifact is handed to `publish` by name, with no digest or content check against `sha` and `version`.
  - Brownfield already uses `npm ci --ignore-scripts`, `npm audit signatures` and `persist-credentials: false` (references/Hexalith.Builds/Github/prepare-domain-release/action.yml:125–128, Github/create-release/action.yml:25). The spine doesn't carry these forward, and AD-20 makes all new code new files.
- **Evidence:**
  - l.349 "Build and pack once at the release SHA"; l.350 "it is deleted when no package of its version exists"; l.351 "Output `publish`, `version`, `sha`, `draft-id` and `artifact`".
  - zizmor `github-env` and `excessive-permissions` audits: https://docs.zizmor.sh/audits/
- **Fix (AD-17 Rule tightening):**
  - "Every job in Builds' reusable workflows declares `permissions:`. Jobs that run module or third-party code (`build`, `codeql`, `nightly-hook`, the version computation) get `contents: read`, no secrets, and `persist-credentials: false`.
  - Draft create, complete and delete run in a separate job that runs only stdlib Python.
  - `sha` comes from the resolve job, and `version` from a job that runs no module code.
  - The build job outputs only the artifact ID and `artifact-digest`. `publish` downloads by ID, verifies the digest, and checks each `.nupkg` version and its nuspec repository commit against `version` and `sha`."

### X-6 — high — Nothing stops the release from restoring Actions caches that module code can poison (AD-12, AD-17)

- **Location:** AD-12 (l.273–l.287) and AD-17. The spine says nothing about caches, apart from the custom-action deny list.
- **Scenario (compromised dependency, or careless module code):**
  - CI on push to `main` runs unit and integration tests and hooks, all module and dependency code, and can write `main`-scope cache entries (the Cacheract technique).
  - The release is a `workflow_dispatch` on `main`, so it reads that scope.
  - If any release job restores a cache, the poisoned content is packed into the published package. Extracted `~/.nuget/packages` folders are not re-verified on restore. setup-node v5+ caches npm automatically when `packageManager` is declared, and setup-uv's `auto` caches on every event except release, tag push, `pull_request_target` and `workflow_run`.
  - The brownfield release path already caches `~/.nuget/packages` with `restore-keys: nuget-` (prepare-domain-release/action.yml:120–122).
- **Evidence:**
  - Cache poisoning into release workflows (Angular, Clinejection): https://adnanthekhan.com/posts/angular-compromise-through-dev-infra/ and https://adnanthekhan.com/posts/clinejection
  - `cache-mode` `none` / `read` / `write` / `write-only` at workflow or job level, which carries through reusable workflows: https://github.blog/changelog/2026-09-10-control-github-actions-cache-access-with-cache-mode
  - setup-node default caching: https://github.com/actions/setup-node; setup-uv `enable-cache: auto`: https://github.com/astral-sh/setup-uv
  - zizmor `cache-poisoning`: https://docs.zizmor.sh/audits/
- **Fix (AD-17 Rule tightening; one row in the Consistency Conventions):**
  - "Builds' reusable `release.yml` and the rendered `release.yml` declare `cache-mode: none`.
  - Builds workflows set `package-manager-cache: false` on setup-node and `enable-cache: false` on setup-uv, and use no NuGet cache."

### X-7 — medium — The audit gate has six confirmed bypasses outside the guard's `NoWarn` / `NuGetAuditSuppress` lint (AD-8, AD-17)

- **Location:** AD-8 (l.208), AD-17 step 6 (l.349), AD-10 waivers (l.252).
- **Scenario (careless module agent "fixing" a red nightly release):** each change below makes the release gate exit 0 with a known high-severity advisory present.
- **Evidence:** local experiment, SDK 10.0.403.
  - Setup: a project with `Newtonsoft.Json 12.0.1` (GHSA-5crp-9r3c-p9vr, high), `TreatWarningsAsErrors=true`, and `WarningsNotAsErrors` NU1901–NU1904, as in Tenants, Conversations and Folders.
  - Command: `dotnet build -c Release -warnaserror:NU1903;NU1904 -p:NuGetAudit=true -p:NuGetAuditMode=all -p:NuGetAuditLevel=low`. Baseline: `error NU1903`, exit 1.

  | Module change | Result |
  | --- | --- |
  | `<MSBuildWarningsAsMessages>NU1903</MSBuildWarningsAsMessages>` in Directory.Build.props | **exit 0**, no NU1903 |
  | `<Project TreatAsLocalProperty="NuGetAudit">` + `<NuGetAudit>false</NuGetAudit>` | **exit 0**: beats the global `-p:` |
  | `<PackageReference … NoWarn="NU1903" />` (attribute, not element) | **exit 0** |
  | `Directory.Build.rsp` containing `-nowarn:NU1903` | **exit 0** |
  | `nuget.config` `<auditSources><clear/><add … value="./feed"/></auditSources>` (module without TWAE) | **exit 0**: only `warning NU1905`, NU1903 never raised |
  | `<NoWarn>$(NoWarn);$(_C)03</NoWarn>` with `_C=NU19` (no literal code) | **exit 0**: evades a text lint |
  | `NuGetAuditSuppress` in an imported `build.xml` | **exit 0**: evades a lint keyed on `.props`/`.targets` |
  | `Directory.Build.rsp` with `-p:NuGetAudit=false` | exit 1 (the CLI wins) |
  | `<WarningsAsMessages>NU1903</WarningsAsMessages>` | exit 1 (no bypass) |
  | rsp case rerun with `-noAutoResponse`; auditSources case rerun with `-p:RestoreConfigFile=<nuget.org-only config>` | exit 1 (gate restored) |

  - `dotnet list package --vulnerable --source nuget.org` also honours the module's `auditSources` and reports nothing, so it is not an independent check.
  - Today no module carries a bypass, and every `nuget.config` is nuget.org-only.
- **Fix (AD-17 Rule tightening):**
  - "Step 6 adds `-noAutoResponse`, `-p:RestoreConfigFile=<Builds' nuget.org-only config>` and `-warnaserror:NU1900;NU1903;NU1904;NU1905`.
  - The verdict comes from a Builds stdlib script. It reads each project's `project.assets.json` (located via `-getProperty:ProjectAssetsFile`), matches the resolved packages against `https://api.nuget.org/v3/vulnerabilities/index.json`, and subtracts Builds' Props waivers. Module MSBuild and NuGet settings can't change it."
  - AD-8 lint, kept as an early signal: deny NU1900/NU1903/NU1904/NU1905, `TreatAsLocalProperty`, `MSBuildWarningsAsMessages` and `auditSources` in any module file, and add `Directory.Build.rsp` to the `absent-glob` row.

### X-8 — medium — Setup values reach YAML without an escaping or shape rule (AD-3, AD-5)

- **Location:** AD-3 knobs (l.110–l.114), AD-12 `jobs` rendering (l.287), Identifiers convention (l.464), global checks (l.116).
- **Scenario (fork-PR author to CiCd whose PR a careless agent merges, or a careless CiCd agent):**
  - `jobs` names and runner values are written by Jinja2 into the rendered caller's YAML.
  - A runner value carrying a newline and `permissions: write-all`, or a `${{ … }}` expression, changes the workflow GitHub executes.
  - Jinja2 autoescape targets HTML and does nothing for YAML.
  - The schema validates the rendered `hexalith-ci.json`, not the YAML. Kebab-case is a convention, not a schema pattern, and the "linting" in the global checks is unspecified.
- **Evidence:** l.109 "Validation checks that rendered `hexalith-ci.json`…"; l.464 "hooks, jobs and actions in kebab-case".
- **Fix (AD-3 Rule tightening):**
  - "The schema constrains every string a template writes into YAML: names `^[a-z0-9]+(-[a-z0-9]+)*$`, runner enum `windows-latest`, paths without control characters or `${{`.
  - Templates emit values only through a `tojson` filter, with `StrictUndefined`.
  - The global checks run actionlint and zizmor over `rendered/**/.github/workflows/*.yml` and CiCd's own workflows."

### X-9 — medium — "Read-only token and no secrets" is not what a custom action actually gets, and custom actions may call unpinned actions (AD-14, AD-8, AD-12)

- **Location:** AD-14 (l.309), AD-12 registry login (l.280), Deferred hook secrets (l.585), enforcement.md deny list.
- **Scenario (compromised third-party action or dependency used in a hook):**
  - **Same-job secrets are readable.** Hooks and tests run in the same job as the registry login. The pull pair is readable from `~/.docker/config.json` and from Runner.Worker memory (X-1). With default checkout, the job token is also readable from the persisted credentials file under `$RUNNER_TEMP`.
  - **Deferred hook secrets would leak the same way.** If they are added to that job, every test and every dependency reads them.
  - **Custom actions can pull in unpinned code.** The deny list doesn't stop a composite from calling `someone/action@main`, so a careless agent can bring mutable third-party code into CI and into the `nightly-hook` job of the release run.
  - Org `allowed_actions` is `all`.
- **Evidence:**
  - l.309 "It gets a read-only token and no secrets".
  - Checkout v6+ "stores credentials in a separate file under `$RUNNER_TEMP`": https://github.com/actions/checkout
  - zizmor `unpinned-uses` and `ref-confusion` cover actions: https://docs.zizmor.sh/audits/
- **Fix (AD-14 Rule tightening, plus one deny-list line):**
  - "Every secret a job references is readable by all of its steps. The pull pair is accepted on that basis, as a pull-only account limited to test images. Hook secrets, when added, go to a separate job, never the CI job.
  - Builds checkouts use `persist-credentials: false`."
  - Deny list: "a `uses:` that is not `./…` or a 40-hex SHA".

### X-10 — medium — A marked draft is trusted on its body trailer alone (AD-16, AD-17)

- **Location:** AD-16 (l.328), AD-17 step 5 (l.348), Release markers (l.467).
- **Scenario (careless module agent; a fork-PR commit as the payload):**
  - Module agents have Contents write, so they can create a draft whose body carries `hexalith-release: <sha>` and any `tag_name`.
  - The release then takes that SHA and that version. The SHA can be any commit in the fork network, including an unmerged branch or a fork-PR commit fetchable by SHA from the parent repo.
  - The drift check passes if the owned files are unchanged. Green-CI passes once anyone pushes a branch at that commit.
- **Evidence:** l.348 "If a draft carrying the trailer `hexalith-release: <sha>` exists, use its version". zizmor `impostor-commit`: "commits within a repository Git's network that are not present on the repository itself": https://docs.zizmor.sh/audits/
- **Fix (AD-16 Rule tightening):**
  - "A draft counts as marked only if its author is `github-actions[bot]`, its SHA is an ancestor of `main`, and its `tag_name` is `v<semver>` above the last tag reachable from that SHA.
  - Any other draft is unmarked and ignored."

### X-11 — medium — Tool integrity is version-pinned, not hash-pinned (AD-11, Stack, Action references)

- **Location:** AD-11 (l.264), AD-4 (l.159), AD-12 Dapr and browsers (l.278–l.279), Action references convention (l.473).
- **Scenario (compromised dependency or registry):**
  - npm installs of commitlint, commit-analyzer, release-notes-generator and jscpd run install scripts, resolve transitives, and have no signature check.
  - Dapr CLI and runtime, Playwright browsers, and actionlint and zizmor binaries are fetched by version without a checksum.
  - The SHA-pinned third-party actions aren't checked for impostor commits.
  - Their CI-side impact is limited (read-only token plus the pull pair), but a tampered commitlint or commit-analyzer silently changes the gate or the version.
- **Evidence:** l.264; Builds `package.json` uses caret ranges for `@semantic-release/*` today, with a `package-lock.json` in the repo.
- **Fix (AD-11 Rule tightening):**
  - "Third-party tools are pinned by version and integrity:
    - npm: a committed lockfile, `npm ci --ignore-scripts`, then `npm audit signatures`;
    - Python: `uv lock --script` (X-1);
    - downloaded binaries: a SHA-256 in Builds, checked by the script before use.
  - zizmor runs its online audits, including `impostor-commit` and `known-vulnerable-actions`."

### X-12 — low — Untrusted triggers and permission defaults are left implicit (AD-6, AD-12, AD-19, conventions)

- **Location:**
  - AD-12 triggers (l.286), AD-6 triggers (l.177), AD-19 `builds-ci.yml` (l.404).
  - Action references convention (l.473): the zizmor scope is unstated for Builds `Github/**/action.yml`, CiCd workflows and rendered callers.
- **Scenario (fork-PR author, later edit by a careless agent):**
  - Fork `pull_request` runs are safe today: no secrets and a read-only token (verified).
  - On CiCd, though, per-module checks can't run on fork PRs, so `validate` goes red. The natural "fix" is `pull_request_target` or `workflow_run`, which run with secrets and write tokens. Nothing in the spine forbids them.
  - Workflow-level `permissions:` isn't required. Only the org default `read` (verified) protects an unrendered workflow added by an App before delivery deletes it.
  - Fork approval is `first_time_contributors`.
- **Evidence:**
  - "`workflow_run` … is able to access secrets and write tokens, even if the previous workflow was not": https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
  - GitHub's default event policy blocks `pull_request_target` on public repos from 2026-12-02: https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2 and https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- **Fix (AD-12 and AD-6 Rule tightening, plus AD-21 precondition):**
  - "No workflow in Builds, CiCd or `rendered/` uses `pull_request_target` or `workflow_run`.
  - Every workflow declares top-level `permissions: {}` and grants per job.
  - zizmor covers Builds workflows and `Github/**/action.yml`, CiCd workflows and `rendered/**`."
  - Precondition: keep the org default `read`, and set fork approval to "all external contributors".

### X-13 — low — commitlint and jscpd may load configuration from the scanned module (AD-4, AD-8, AD-18)

- **Location:** AD-4 `absent-glob` row (l.152), AD-8 commitlint (l.209), AD-18 scan.
- **Scenario (careless module agent):**
  - commitlint's config search (via cosmiconfig) also finds `.commitlintrc`, `.commitlintrc.{json,yaml,yml,js,cjs,mjs,ts,cts,mts}` and a `package.yaml` `commitlint` key. None of these is in the perimeter, which lists only `commitlint.config.*` and `package.json` keys.
  - Run with the module as its working directory, the guard would load (and for `.js`, execute) a module config that relaxes the rules.
  - jscpd likewise reads `.jscpd.json` from its working directory.
- **Evidence:** the config file list: https://commitlint.js.org/reference/configuration.html
- **Fix (AD-8 Rule tightening):**
  - "The guard runs commitlint with `--config` pointing into its own action path, and the scan runs jscpd with an explicit config. Neither reads configuration from the module."
  - Optionally widen the `absent-glob` row to `.commitlintrc*`.

### X-14 — low — Restore's isolation from module code is implied, not stated (AD-8)

- **Location:** AD-8 restore (l.212), AD-19 Samples call (l.405–l.407).
- **Scenario (careless agent or compromised dependency in the CI job):**
  - Restore holds `contents: write` and `actions: write`. With `actions: write` it can also disable workflows and delete runs or artifacts.
  - It is safe only if:
    - it runs no module code: no build, no hooks, no module scripts;
    - it takes no data from the CI job except a boolean;
    - its Python can't import a module-planted file from the working directory.
  - Nothing says restore is off for the `Samples/` call in Builds. A drifted fixture could make it push to Builds `main`.
- **Fix (AD-8 Rule tightening):**
  - "Restore runs only Builds code at the workflow's own commit, with `python3 -I`. It recomputes the expected state from `delivered/<Repo>` and consumes no artifact, cache or output from the CI job except its drift flag.
  - It never runs when `module-root` is set."

### X-15 — low — Release provenance is absent, and not recorded as out of scope (AD-17, Deferred)

- **Location:** AD-17 publish (l.352–l.356); Deferred (l.580–l.596) has no entry.
- **Scenario (downstream consumer of a compromised publish):** there is no signed statement linking a `.nupkg` or container to its release SHA and run.
  - Brownfield had opt-in `actions/attest-build-provenance` (ci-cd-standards.md:188–196), but managed modules ran with `governed-release: false` (e.g. Agents `release.yml:123`), so dropping it is no regression in practice.
  - The publish job already holds `id-token: write`.
  - Immutable releases add a release attestation for free (X-3 URL).
- **Fix (Deferred entry):**
  - "Provenance: `actions/attest-build-provenance` for packages and containers in `publish` (`attestations: write`), plus immutable releases on modules. Decided by story 3."

### X-16 — low — The `delivered/**` ruleset doesn't restrict creation (AD-21)

- **Location:** AD-21 (l.456).
- **Scenario (careless CiCd agent or org agent App):**
  - The ruleset "blocks deletion and force-push and lets only the App update". Branch creation stays open.
  - Before a module's first delivery, anyone with CiCd Contents write can create `delivered/<Repo>` pointing at a crafted perimeter. That module's guard and restore would then enforce it.
- **Evidence:** "Restrict creations: only users with bypass permissions can create branches or tags…" (rulesets URL in X-3).
- **Fix (AD-21 Rule tightening):** "…blocks creation, deletion and force-push, and lets only the App create or update those branches."

---

## Counts

- critical 1 (X-1)
- high 5 (X-2, X-3, X-4, X-5, X-6)
- medium 5 (X-7, X-8, X-9, X-10, X-11)
- low 5 (X-12 to X-16)

Two fixes clear most of the high tier: X-1 (keep key-holding jobs free of third-party code, and lock the tools) and X-4 (a `main`-only environment that the nuget.org policy and the push pair are bound to). X-3 and X-5 are rule text that stories 3 and 8 can absorb without changing any decision the user approved.
