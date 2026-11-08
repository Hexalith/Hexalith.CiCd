# Rubric review — ARCHITECTURE-SPINE.md (Hexalith.CiCd)

- Reviewed: `../ARCHITECTURE-SPINE.md` (418 lines, 18 ADs), with `../.memlog.md`, `specs/spec-cicd/` (SPEC + 5 companions + `stories.yaml`), and the brownfield code in `references/` (Builds `.github/workflows`, `Github/`, `Props/`, `Hexalith.Build.props`, `global.json`, `package.json`, `Samples/`, `commitlint.config.mjs`. Also spot checks of the module `release.yml`, `.releaserc*`, `dependabot.yml`, `global.json` and `Directory.Build.props` files).
- Date: 2026-11-07
- Method: I checked the spine against the 7-point rubric and grounded each point in a file. I parsed the Mermaid blocks with mermaid@11.4.1 under jsdom.

## Verdict

The spine is a strong, mostly enforceable contract. The paradigm is clear, almost every AD has a concrete check, and the capability coverage is complete. It is **not ready to bind the 27 stories** yet, for three reasons:
- It never decides what Hexalith.Builds itself is (a managed repo or the runtime, or both).
- It contradicts three pieces of brownfield code that are staying (`Hexalith.Build.props`, `Props/Directory.Packages.props`, the release `environment:`).
- Its nightly ordering does not actually prevent the race it names.

One critical, seven high, 17 medium and 18 low findings.

## Rubric scorecard

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Fixes the real divergence points | Partial: C1, H5, H6, and M3–M12 are open |
| 2 | Rules are enforceable and prevent their divergence | Mostly. AD-18 does not prevent its stated race (H3). AD-2 and AD-12 cannot hold against the brownfield code (H4, H5). AD-6's "never cancelled" is not achievable (L1). |
| 3 | Nothing Deferred lets units diverge | Fails on two items: hook secrets (M8) and the release environment (M7). A third, "Submodules other than Builds", is safe only with M6. |
| 4 | Ratifies the brownfield code | Fails in places: H4, H5, M2, M4, M7, M20 |
| 5 | Covers CAP-1..16 | Yes on the map. CAP-11 propagation (M10) and CAP-15 Samples (M11) are thin. |
| 6 | No silent dimension, operational envelope included | Gaps: Builds self-hosting (C1), module-agent token repo scope (H1), repo settings and out-of-file state (M13, M14), CiCd-agent token permissions (M15), rollback semantics (M12) |
| 7 | Mermaid valid, no placeholders, terse | The sequence diagram does not parse (M1). The dependency diagram is normative but incomplete (M17). The prose is terse and no template residue remains, apart from the `[ADOPTED]` tags (L10). |

---

## Critical

### C1 — Hexalith.Builds' own status is undefined and self-contradictory
**Location:** Design Paradigm table, AD-3, AD-4, AD-6, AD-7, AD-12, AD-16, AD-17, AD-18, the Consistency Conventions "Workflow file names" row, the Structural Seed and the sequence diagram.

**Finding:** The spec counts Builds as one of the 18 managed repos (`module-inventory.md`). That leaves 17 modules plus Builds. The spine says "18 module repos" plus Builds (Structural Seed) and "Module release.yml (x18)". None of the ADs say whether Builds is a spoke. Every option breaks one of them:
- **If Builds has `setup/Hexalith.Builds.yml`:**
  - AD-4's whole-directory ownership of `.github/workflows/` would overwrite the reusable workflows that stories 2, 3 and 27 author directly in Builds.
  - AD-4 would merge `permissions.deny` into Builds' `.claude/settings.json`. SPEC forbids exactly that, because it would block the CiCd agents from editing Builds.
  - The guard would run in Builds against a render of Builds itself.
- **If it has no setup file:**
  - AD-18 dispatches Builds' `release.yml` from a list that, by AD-3, cannot exist.
  - AD-7 installs the App on "the managed modules and CiCd" only, so the App cannot dispatch Builds' release.
- **The `ci.yml` file name is already taken.** It is Builds' own push/PR CI (`references/Hexalith.Builds/.github/workflows/ci.yml`). The spine assigns the same name to the reusable CI and also mentions "its own CI". It does not say whether this is one file with both `workflow_call` and `push` triggers. AD-16's green check for Builds' release depends on that answer.
- **Builds' release rules differ.** AD-10 gives Builds its own release rules. AD-4 says semantic-release config exists only inside the shared composites. AD-2 forbids repo-specific conditions. The composite therefore has no sanctioned way to know it is releasing Builds.
- **Builds is also a .NET product.** It has `src/libraries/*` packable projects and a `test/` solution, and it publishes G-4 tool packages through PowerShell `exec` hooks in the root `package.json`. The spine does not say whether Builds' own CI runs the reusable CI on `Hexalith.Builds.slnx`, on `Samples/` only, or on both. With `Samples/` only, Builds releases untested product code.
- **Builds' `dependabot.yml`** enables `github-actions` with a `ci(deps)` prefix. AD-10 forbids that ecosystem "in modules" only.

Stories 2, 3, 4, 5, 8 and 10 each have to pick an answer, so they will diverge.

**Fix:** Add an AD, "Builds is the runtime, not a spoke". Its Rule:
- Builds has no setup file and is outside the AD-4 perimeter, delivery, the guard and deny-rule rendering.
- CiCd names Builds once, as a constant (`builds-version` already names it), and that constant is the only repo name outside `setup/`.
- The App installation includes Builds (Actions write only).
- Builds' `ci.yml` declares `workflow_call`, `push` and `pull_request`. On push and PR it runs `actionlint`, `zizmor` and the reusable job locally against both `Samples/` and `Hexalith.Builds.slnx`.
- Builds' `release.yml` declares `workflow_call` and `workflow_dispatch`. Its release rules are a composite input (`release-rules: builds|module`, default `module`), so no repo name appears in the code.
- Builds' `dependabot.yml` is Builds-owned and may enable `github-actions` with `build(deps)`.
- The root `package.json` `release` block and `Tools/*-g4-*.ps1` are deleted in story 3.

Then fix the counts: "17 modules + Builds" in the scope, Structural Seed and sequence diagram.

---

## High

### H1 — The module-agent token's repository scope is not fixed, which opens a full bypass through CiCd and Builds
**Location:** AD-7, Structural Seed.

**Finding:** AD-7 fixes the module-agent token's *permissions* (no Workflows, no Administration) but not *which repos* it covers. `enforcement.md` relies on "module agents can't change [CiCd]". If story 10 issues an "All repositories" fine-grained token, the easy choice for 17 repos, a module agent can:
- Push to CiCd `rendered/<Repo>/.github/workflows/*`. These are plain files in CiCd and need no Workflows permission. Within an hour, AD-6's delivery pushes them into the module with the App's Workflows permission.
- Push to Builds `Github/<composite>/`, which is not under `.github/workflows/`. The change ships to every module at the next nightly Builds release and bump.

Both defeat Layers 1 and 2.

**Fix:** In AD-7, add: "The module-agent token covers only the 17 managed modules, never Builds or CiCd. Its permissions are Contents RW, Pull requests RW and Metadata R, with no Workflows, Administration, Secrets, Variables or Actions write." Make it checkable: story 10 records the token's repo list and permissions in CiCd (`docs/tokens.md` or a setup field), and CiCd CI asserts that the list equals `setup/*.yml`.

### H2 — Delivery is not gated on CiCd CI, so one bad template or hand-edited render reaches every module within the hour
**Location:** AD-5, AD-6 triggers, AD-8.

**Finding:** AD-5 says CiCd CI fails on a render diff. AD-6, however, triggers delivery on every push to CiCd `main` touching `setup/`, `templates/` or `rendered/`, and hourly, with no dependency on CiCd CI passing. The guard reads CiCd `main` `rendered/` unconditionally. A broken template, an un-rendered setup change, or a direct edit to `rendered/` therefore becomes the desired state everywhere. The hub then has the same flaw AD-16 removes for modules: shipping an untested commit.

**Fix:** In AD-6, add: "Delivery writes only a CiCd SHA whose CiCd `ci.yml` push run succeeded. The push trigger becomes `workflow_run` of CiCd `ci.yml` on `main` with `conclusion == success`. Hourly and manual runs deliver the newest green CiCd SHA." Optionally, the guard can also read the newest green SHA. At minimum, record "guard reads `main`; a red CiCd `main` is a known window".

### H3 — The nightly ordering does not prevent "releases waiting on bump CI"
**Location:** AD-18 Rule and sequence diagram, AD-5, AD-6 triggers, AD-16, AD-17.

**Finding:** The Rule says that when Builds' release completes, the nightly runs delivery, which bumps the modules. The diagram shows `N->>D` while `M` is still running. The setup makes this worse:
- On the GitHub Free tier, 18+ release runs (each codeql + nightly-hook + release) exceed the 20-job limit, so many module releases are still queued when Builds finishes.
- The bump pushes `build(cicd)` commits, which move each module's head.
- A queued release then reads a head whose CI is running on the *new* Builds version. It waits up to 30 minutes (AD-16), and a bad Builds release now blocks module releases. The memlog explicitly rejected that outcome (decision 4.2).
- Separately, AD-5 makes the bump a CiCd commit. Per the memlog, App pushes trigger push workflows, so AD-6's push trigger delivers the bump immediately, whatever order nightly.yml intends.
- The hourly delivery at :17 also fires at 02:17, the same minute as the nightly.
- AD-16 and AD-17 never pin the SHA. The green check reads "the head SHA of main", and semantic-release later computes "from the head", which can be a different commit.

**Fix:** Rewrite AD-18:
1. The nightly dispatches every release and waits until **all** of them complete.
2. Only then does it commit `builds-version` and the render to CiCd, and deliver. The push-trigger delivery of that commit is then a no-op.
3. Hourly delivery skips while `nightly.yml` is running (check via the API, or share a concurrency group).

In AD-16, add: "The release resolves the head SHA of `main` once at start. The green check, semantic-release and the draft all use that SHA."

### H4 — AD-12's NuGet-audit gate contradicts `Hexalith.Build.props`, which is staying
**Location:** AD-12 stage 2, the Consistency Conventions "SDK and build" row, and the memlog's "Spec conditional applied" entry. Code: `references/Hexalith.Builds/Hexalith.Build.props`.

**Finding:** `Hexalith.Build.props`, imported by every module through the submodule, sets:
- `<WarningsNotAsErrors>$(WarningsNotAsErrors);NU1901;NU1902;NU1903;NU1904</WarningsNotAsErrors>`
- a comment saying advisories must *not* block pipelines.

The memlog's verification ("NU1901–1904 fail restore under -warnaserror") was generic .NET 10 behaviour. It did not account for this override. Whether `-warnaserror` beats the project-level `WarningsNotAsErrors` depends on the MSBuild and NuGet version. Either way, the brownfield code encodes the opposite policy. If the override wins, dependency review is dropped *and* vulnerable packages pass, which silently loses a product gate (CAP-10 and the spec's condition for dropping dependency review).

**Fix:** In AD-12, add:
- "`Hexalith.Build.props` removes NU1901–NU1904 from `WarningsNotAsErrors`."
- "Builds' CI proves the gate with a `Samples/` project that references a known-vulnerable package version and must fail restore."

Name the owning story (2). Optionally, add to the AD-4 guard a check that no module `Directory.Build.props` re-adds NU190x to `NoWarn` or `WarningsNotAsErrors` (see L18).

### H5 — AD-2 ("no module names or module-specific conditions") contradicts `Props/Directory.Packages.props`, which is staying
**Location:** AD-2. Code: `references/Hexalith.Builds/Props/Directory.Packages.props`.

**Finding:** The central catalog the spine keeps (Structural Seed `Props/`, SPEC "Release propagation") names every module:
- `HexalithCommonsVersion`, `HexalithPartiesVersion`, and so on;
- `Exists('…/Hexalith.Works.slnx')`;
- `'$(MSBuildProjectName)' == 'Hexalith.Folders.Aspire'`;
- `StartsWith('Hexalith.Works')`.

The legacy `domain-*.yml` and `eventstore-maintenance-publisher.yml` also name modules until story 27. As written, AD-2 fails a review on day 1 and stays unenforceable. Worse, a story-2 developer may strip the Works and Folders conditions and break those builds.

**Fix:** Scope AD-2's Rule: "Builds CI/CD code (`.github/workflows/`, `Github/**`, `check.py`, scripts) contains no module names, lists or conditions. The package catalog under `Props/` is data and may name packages and modules. Legacy files are exempt until story 27 deletes them." Make it checkable: a Builds CI grep over those paths for `Hexalith\.(Commons|…)` taken from a fixture list in `Samples/`, so Builds itself stays agnostic.

### H6 — The non-.NET and runtime technical surface has no shared-stage or custom-action decision
**Location:** AD-3 knob list, AD-12, AD-14, Deferred. Spec: `module-inventory.md` "Technical surface", stories 15, 20, 22, 23.

**Finding:** The spec says shared stages or custom actions "must cover" Python (122 files in Memories, 71 in Tenants), PowerShell, Node, Aspire, a Postgres image pinned by digest, Azure secrets and Windows. The spine decides Dapr and Playwright (Builds-owned) and Windows (`jobs`). It is silent on:
- Python test suites (not `IsTestProject`, so AD-13 never sees them);
- Aspire and Docker preparation (McpCli's "Prepare Aspire tier" is the story-15 hook);
- PowerShell and Node product code.

Stories 22 and 23 will each write a pytest custom action. CAP-9's duplicate scan then fails, which forces a hoist into Builds and a new knob. That is two stories diverging and a third cleaning up. AD-3's closed knob list makes the hoist a schema change that no story owns.

**Fix:** Decide now, in AD-12 and AD-3:
- "Python tests are a Builds-owned stage-3 step, enabled by a `python` knob that names the test root(s), run with `python3 -m pytest` or `unittest`. Projects run in ordinal path order after .NET unit tests."
- "Aspire AppHost tests need only Docker on `ubuntu-latest`. No preparation step exists."
- "PowerShell and Node product checks are custom actions."

Alternatively, defer explicitly: "the first story to need X adds a Builds stage and a knob, and later stories reuse it". Name story 22 as the owner for Python.

### H7 — The spine silently overrides spec and story text in at least seven places, with no amendment list
**Location:** whole document. There is no "Spec amendments" or "Supersedes" section.

**Finding:** The spine governs the 27 stories, but story text still says the opposite in places. A developer agent handed `stories.yaml` will follow the story:

| Item | Spec or story text | Spine |
| --- | --- | --- |
| Story 4 | "render … commitlint and semantic-release config" | AD-4: that config must be **absent** from modules |
| Story 8 | "with staggered start times" | AD-18: all dispatched at once |
| CAP-8 | "No such change persists beyond the next CI run" | AD-8: up to one hour for `.github/workflows/**` |
| Non-goal | "Central failure reporting" | AD-18: the nightly aggregates and fails |
| CAP-4 | "submodule + setup file" onboards a repo | AD-3: also App installation (plus a nuget.org policy, per the memlog) |
| Stories 5 and 11–26 | "credential decided in story 1" | AD-7 and AD-8 already decide it, which shrinks story 1 |
| `enforcement.md` | the guard restores "the expected files" | AD-8: only agent-reachable files |

The story-4 conflict alone produces a permanent fight between the generator and the guard.

**Fix:** Add a short "Spec and story amendments" section listing each override with its AD. Reduce story 1's scope to the facts that are still unverified (see L16). Alternatively, push the amendments into SPEC.md and `stories.yaml` before story 2 starts.

---

## Medium

### M1 — The sequence diagram is invalid Mermaid
**Location:** AD-18 sequence diagram, last line: `N->>N: summary; fail if any run failed`.

**Finding:** In sequence diagrams, `;` is a statement separator. mermaid@11.4.1 reports `Parse error on line 14 … got 'NEWLINE'`. Replacing `;` with `,` makes it parse, which I checked. The other two diagrams parse.

**Fix:** Write `N->>N: summary, fail if any run failed`.

### M2 — Wrong repository slug in action references
**Location:** AD-12 (`uses: Hexalith/Builds/Github/prepare@<same tag>`), AD-18 ("Builds `prepare`").

**Finding:** The repo is `Hexalith/Hexalith.Builds`, per every module's `.gitmodules` and Commons' `uses: Hexalith/Hexalith.Builds/.github/workflows/domain-ci.yml@…`. Templates copied from AD-12 will not resolve.

**Fix:** Write `uses: Hexalith/Hexalith.Builds/Github/prepare@<tag>`. Add a Consistency Conventions row: "Builds reference: `Hexalith/Hexalith.Builds/<path>@vX.Y.Z`".

### M3 — The split of concurrency and permissions between caller and reusable workflow is not fixed
**Location:** Consistency Conventions "Concurrency groups", AD-8, AD-12, AD-17.

**Finding:** Two problems:
- **Concurrency.** If story 2 or 3 declares `concurrency` in Builds' reusable workflow and story 4 declares the same group in the rendered caller, GitHub detects a deadlock and cancels the run.
- **Permissions.** A called workflow can only narrow the caller's permissions (memlog). The restore job needs `contents: write` and `actions: write`, and the release needs `contents: write`, `id-token: write`, `security-events: write` and `actions: read`. The rendered caller must therefore grant these maximums, and no rule says so.

**Fix:** Add a row: "`concurrency` is declared only in rendered callers and CiCd workflows, never in Builds' reusable workflows. Rendered callers grant, per job: `ci` gets `contents: write, actions: write`; `release` gets `contents: write, id-token: write, security-events: write, actions: read`. Builds narrows per job, and the build job keeps `contents: read`."

### M4 — Toolchain unification has no owning artifact (SDK, Dapr)
**Location:** Stack (".NET SDK 10.0.403 (from each `global.json`)", "Dapr runtime (one pin in Builds) 1.19.1"), Consistency Conventions "SDK and build".

**Finding:**
- **SDK.** Module `global.json` files pin 10.0.401, .402 or .403 (Agents, McpCli, Platform, Timesheets and Works on .401; ChatBot, Folders and Projects on .402). `global.json` is module-owned, so the Stack row is a wish, not a rule. Migration stories will each choose differently.
- **Dapr.** The brownfield has two pin sites: `Props/Directory.Packages.props` (`HexalithDaprRuntimeVersion` 1.18.7, `HexalithDaprCliVersion` 1.18.2) and the default in `Github/dapr-init/action.yml` (1.18.0). The spine does not say which one is "the one pin", and Aspire's Dapr hosting reads the Props value at test time.

**Fix:**
- SDK: add `global.json` `sdk.version` to the AD-4 perimeter as a partial-key row (like `settings.json`), equal to the rendered value. Alternatively, state that `global.json` is module-owned and drop the version from the Stack row.
- Dapr: name the pin, for example "Dapr runtime and CLI versions live only in `Props/Directory.Packages.props` (`HexalithDaprRuntimeVersion`, `HexalithDaprCliVersion`). The Dapr setup composite reads them and has no default."

### M5 — The package-mode build switch is not fixed, so CI and the local check can build differently
**Location:** AD-12 ("checks out only the Builds submodule"), AD-15, Deferred "Submodules other than Builds".

**Finding:** Modules pick project or package references with per-module MSBuild logic: `UseHexalithProjectReferences` and `UseNuGetDeps`, defaulted by `GITHUB_ACTIONS` and `Configuration` (see `Hexalith.Agents/Directory.Build.props` lines 29–32 and Commons lines 17–20). Locally, with sibling submodules present, the same Release build can resolve differently from CI. That breaks CAP-3, and it is the real cause behind the deferred submodule question.

**Fix:** In the "SDK and build" row, add: "CI and `check.py` always build with `-p:UseHexalithProjectReferences=false`." Then the deferral is safe: a module that still needs another submodule is a migration-story bug, not a knob.

### M6 — Deferring the release `environment` contradicts the brownfield code and can break publishing at the pilot
**Location:** Deferred "GitHub environment on the release job", AD-17, Consistency Conventions "Secrets and variables".

**Finding:**
- 14 module release workflows and Builds' `build-release.yml` use `environment: production`, and the existing nuget.org Trusted Publishing policies may be bound to it. If they are, an environment-less `release.yml` fails `NuGet/login`. If the environment is kept and has protection rules, nightly releases wait for approval (CAP-13).
- The brownfield variables are `vars.NUGET_USER` and `vars.NUGET_TRUSTED_PUBLISHING_USER`. The spine requires a `HEXALITH_` prefix but names no variables, so stories 3 and 11 will choose differently.
- The policies are also keyed to the workflow file name, currently `build-release.yml` (Builds, PolymorphicSerializations).

**Fix:**
- Decide "no environment".
- Add to the onboarding checklist: "recreate the nuget.org policy for `release.yml`, no environment".
- Fix the names in Consistency Conventions: `HEXALITH_NUGET_USER` (org variable), `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD` (org secrets), `HEXALITH_RELEASE_PUBLISH_ENABLED` (repo variable).

### M7 — The deferred hook-secrets mechanism contradicts AD-14 and changes Builds' public API at story 20
**Location:** Deferred "Hook and job secrets", AD-14 ("no secrets"), AD-10 (inputs and secrets are semver API).

**Finding:** Composite actions cannot read `secrets`. Giving an in-job hook a secret therefore needs a new `workflow_call` `secrets:` entry on Builds' `ci.yml`. That changes Builds' public API, breaks AD-14, and risks a module-specific secret name (AD-2). Deferring the mechanism to story 20 lets that story reshape Builds.

**Fix:** Decide the mechanism now: "Actions that need secrets run only as rendered extra-runner jobs (AD-12). The rendered caller passes named `HEXALITH_*` secrets to that step as `env`. In-job hooks never get secrets, and Builds' `ci.yml` declares no secrets." Defer only *which* EventStore secrets.

### M8 — No rule says at which revision CiCd reads module content
**Location:** AD-3 (CiCd CI checks "names an action the module lacks"), CiCd `tools/scan.py` (CAP-9).

**Finding:** CiCd's `references/` submodule pointers are stale. The inventory says so for Timesheets and Platform, and nothing in the spine updates them. The AD-3 check and the duplicate scan will give wrong answers if they read the pinned submodule commit. Migration stories push a custom action to a module and then enable it in `setup/`, so they will either bump CiCd pointers by hand or see false failures.

**Fix:** Add to AD-3: "CiCd tools read module content from a shallow clone of the module's `main` at run time, never from the `references/` submodule pointer. The pointers are a convenience for agents and are not checked."

### M9 — CAP-11 has no propagation path and no recurrence check
**Location:** Capability map CAP-11, AD-4, AD-6.

**Finding:** Two gaps:
- **Instruction files.** How does the AI.Tools instruction section reach the `AGENTS.md`, `CLAUDE.md` and `copilot-instructions.md` of 17 modules? If AI.Tools' own sync pushes them, it is a second unattended writer into modules (AD-6) with an undecided credential (AD-7). If it is a one-time push, later edits drift.
- **`bmad-testarch-ci`.** It lives in `.claude/skills/`, `.agents/skills/` and `.agent/skills/` (Works, Memories, Platform, Timesheets, Parties). The next BMAD reinstall, which happens routinely, puts it back, and nothing checks for it.

**Fix:**
- Decide the writer. Recommended: the instruction section is rendered and delivered as a marker-delimited partial row in AD-4, superset-checked like `settings.json`. The rest of each file stays module-owned.
- Add `**/skills/bmad-testarch-ci/` to the AD-4 "must be absent" row.

### M10 — The shape of `Samples/` is undefined, and the guard cannot be exercised in Builds' CI
**Location:** Structural Seed (`Samples/`), CAP-15, AD-8.

**Finding:** Today `Samples/` holds only two `.props` files. CAP-15 needs a sample module rich enough that "a Builds change that breaks the sample module's CI fails Builds' CI". It needs:
- unit and integration projects;
- every hook point and an extra-runner job;
- `dapr: true`;
- a packable project and a container project.

Stories 2, 3, 5 and 6 each extend it ad hoc. AD-8 also hard-wires the guard's expected tree to CiCd `main` `rendered/<Repo>/`, and no such tree exists for `Samples/`, so the guard and restore are never run by Builds' CI.

**Fix:**
- Add to the Structural Seed: "`Samples/Module/` is a minimal module that exercises every AD-12 stage, each hook, one `jobs` entry, `dapr: true`, `tests.integration` and `tests.exclude`, and one packable and one container project."
- In AD-8, add: "The guard takes the expected-tree location as an input (default CiCd `main`). Builds' CI points it at `Samples/expected/`."

### M11 — A rollback is undone by the next nightly auto-bump
**Location:** Structural Seed Operations ("Rollback: the reverse Builds bump"), AD-10, AD-18.

**Finding:** The bump target is not defined: "the tag tonight's Builds release created" or "the latest tag in the major". If it is the latest tag, a manual rollback to v4.44.11 is re-bumped to the bad v4.44.12 the next night. Story 7 and story 8 can implement different semantics.

**Fix:** In AD-18, add: "The nightly bumps only to the tag created by tonight's Builds release run. No new tag means no bump. A rollback is a CiCd commit that sets `builds-version` back, and it holds until Builds publishes a newer tag."

### M12 — Desired state outside files is a silent dimension (repo settings, the other module lists)
**Location:** AD-3 ("no other module list exists"), AD-7, AD-12 ("No CodeQL runs on a push or PR"), AD-10.

**Finding:** Several module lists and settings exist outside the repo files, and none is checked:
- Org-secret and org-variable "selected repositories" access lists (Zot credentials, `HEXALITH_NUGET_USER`).
- The per-repo nuget.org policies.
- The per-repo `HEXALITH_RELEASE_PUBLISH_ENABLED` variable.
- Repo settings that would bypass the ADs:
  - code scanning *default setup*, which runs CodeQL on push and PR outside any workflow (breaks CAP-14);
  - Dependabot *security updates*, which open PRs editing workflow files even when `dependabot.yml` omits `github-actions` (a layer-1 bypass AD-10 misses);
  - the default `GITHUB_TOKEN` workflow permissions and allowed-actions policy.

AD-3 checks only the App installation.

**Fix:** Extend AD-3's CiCd CI check:
- "For each setup file, CiCd CI verifies through the API: App installation, org-secret and org-variable access, `HEXALITH_RELEASE_PUBLISH_ENABLED` set, code-scanning default setup off, Dependabot security updates off."
- "A missing nuget.org policy is accepted as a red first release."

### M13 — The CiCd-agent token's permission set is unspecified
**Location:** AD-7 ("a fine-grained token on Builds and CiCd, for interactive sessions only").

**Finding:** Stories 2, 3, 8 and 27 require editing `.github/workflows/` in Builds and CiCd, which needs the Workflows permission. A least-privilege token made in story 10 without Workflows blocks them.

The memlog also routes nightly failure emails to the "last cron editor". That works only if the cron lines are committed with a maintainer-owned credential, which is an unstated invariant.

**Fix:** In AD-7, add:
- "CiCd-agent token: Builds and CiCd only. Contents, Workflows, Actions and Pull requests RW."
- "The `schedule:` lines in CiCd workflows are committed only from an interactive session, so failure email reaches the maintainer."

### M14 — CodeQL languages are undecided
**Location:** AD-18 `codeql` job, AD-3 closed knob list.

**Finding:** Brownfield `codeql.yml` takes `languages` with default `csharp`. Python in Builds `Github/`, CiCd `tools/`, Memories and Tenants would never be analysed. No knob exists, and AD-3 forbids ad hoc knobs.

**Fix:** In AD-18, add: "CodeQL languages are detected by Builds from the checkout (`csharp` always, plus `python` when `*.py` exists outside `references/`). There is no knob." Alternatively, add a `codeql.languages` knob to the schema.

### M15 — Builds' public API omits the MSBuild props and `check.py`
**Location:** AD-10 ("`workflow_call` inputs and secrets, and its composite interfaces, are its semver public API").

**Finding:** Modules also consume, through the submodule:
- `Hexalith.Build.props`, `Hexalith.Package.props` and `Props/Directory.Packages.props` (import paths and property names);
- `check.py`'s CLI.

A within-major auto-bump that renames a property or removes a `PackageVersion` turns every module red for a non-product reason, against the spec's success signal.

**Fix:** In AD-10, add: "The public API also includes the import paths and documented properties of `Hexalith.*.props` and `Props/*`, and the `check.py` invocation. Removing or renaming one is a major."

### M16 — The commit-type vocabulary conflicts with the brownfield commitlint config
**Location:** Consistency Conventions "Commit types" (`chore(cicd): keepalive`), AD-10. Code: `references/Hexalith.Builds/commitlint.config.mjs`.

**Finding:**
- Builds' `type-enum` is build, ci, docs, feat, fix, perf, refactor, revert, style and test, with no `chore`. AD-4 says that config becomes the only commitlint config. The keepalive therefore fails commitlint wherever it is linted, and AD-10's "except … chore" refers to a type the config forbids.
- The rendered `dependabot.yml` prefix is never stated. Brownfield modules use `chore(deps)` (Commons, which fails commitlint) or `build(deps)` (Works).
- The spine does not say whether CiCd's own commits are linted.

**Fix:** In Consistency Conventions:
- Fix the type-enum (ratify the brownfield list).
- Change the keepalive to `build(cicd): keepalive`.
- Add "rendered `dependabot.yml` uses `build(deps)` for every ecosystem".
- State whether CiCd CI runs Builds' commitlint.

### M17 — The dependency diagram is declared normative ("nothing else") but omits arrows the ADs require
**Location:** Invariants & Rules flowchart and the sentence after it.

**Finding:** These arrows are missing:
- `NIGHTLY → BREL`: AD-18 dispatches Builds' `release.yml`.
- `NIGHTLY → DELIVER`.
- `CALLER → COMP`: AD-12's extra-runner job uses `prepare@tag`.
- `CALLER → ACT`: the nightly-hook and extra-runner jobs.
- `BCI → module` for the restore write (AD-8).
- `BREL → GitHub Actions API` for the module's own runs (AD-16).
- CiCd CI → module `main` (AD-3, M8).

Read literally, AD-8, AD-12 and AD-18 violate the diagram.

**Fix:** Add the arrows, or change the sentence to "Allowed *cross-repo code and config* dependencies are the arrows above."

---

## Low

- **L1 — "never cancelled" concurrency (AD-6, AD-17, Conventions).** GitHub replaces a *pending* run whenever a newer run queues in the same group. Only in-progress runs can be protected, with `cancel-in-progress: false`. Reword to that, and note that replacing a pending run is harmless for delivery because the latest render wins.
- **L2 — zizmor's default `unpinned-uses` policy versus exact tags (Conventions "Action references", AD-10).** zizmor's default policy is believed to require hash pins for non-`actions/*` owners. That would flag `Hexalith/Hexalith.Builds/…@vX.Y.Z`, `NuGet/login@v1.2.0` and `astral-sh/setup-uv@v10.3.3`. The brownfield already hash-pins NuGet/login and dapr/setup-dapr. Verify this in story 2, and commit a `zizmor.yml` that allows ref-pins for `Hexalith/*` (immutable releases) and requires hash pins for other third-party actions.
- **L3 — `python3` on `windows-latest` (AD-11, AD-12 extra-runner `prepare`).** `python3` is not guaranteed on Windows images. Use `shell: python` in composites, or state "Linux: `python3`; Windows: `python`".
- **L4 — Restore loop and races (AD-8).** Add "no diff means no commit and no dispatch". Specify what happens on a non-fast-forward push: re-read and retry once, then fail.
- **L5 — AD-1 Prevents overclaims.** The guard verdict *does* depend on CiCd state at run time (AD-8). Reword to "a SHA's build, test and release behaviour depending on CiCd state; only the guard verdict may".
- **L6 — Deny-list source (AD-8 "from `enforcement.md`").** At run time the list must live in the Builds guard (AD-1). State "a constant in the Builds guard, seeded from `enforcement.md`".
- **L7 — CodeQL blocking criterion (AD-18).** Name the field and tool: `tool=CodeQL`, `state=open`, `security_severity_level in {high, critical}`. Wait for analysis processing before querying.
- **L8 — Which CI run counts (AD-16).** Several runs can share one SHA (rerun attempts, push plus dispatch). State "the most recently created completed run, latest attempt".
- **L9 — The Stack table is incomplete and has duplicate pin sites.** It is missing `actions/setup-node` (v7.1.0 in the brownfield), `dapr/setup-dapr`, Playwright, the container-push tooling and `nick-fields/retry`, if kept. `actionlint` and `zizmor` are pinned "in Builds or CiCd", which is two sites. Name one.
- **L10 — `[ADOPTED]` tags appear on AD-1 and AD-2 only.** They are unexplained status markers. Remove them, or define them and apply them to every AD.
- **L11 — The AD-13 name table misroutes known names.** `LoadTests`, `LiveTests` (EventStore, Azure-backed), `Benchmarks`, `LifecycleTests` and `NativeTests` all exist today and default to stage 3. Add them to the table (LiveTests and LoadTests to stage 4, Benchmarks excluded unless `IsTestProject`), or have each migration story record its overrides.
- **L12 — Prerelease channels are dropped silently.** Builds' `prerelease` branch and channel, and some modules' `alpha`/`beta` branches, disappear under AD-17's main-only state machine. State it.
- **L13 — Guard behaviour on non-`main` pushes is unspecified (AD-8).** The CI caller triggers on every `push`. State "on other branches: fail like a PR, never restore".
- **L14 — The duplicate scan's host workflow is unfixed.** `enforcement.md` says the CiCd nightly. AD-18 does not list it. Add "`nightly.yml` runs `tools/scan.py` and fails on a finding".
- **L15 — "publishing disabled" timing (AD-17).** Say whether a draft is created when the kill switch is off. Recommended: no draft, and the check runs before step 1.
- **L16 — There is no Open Questions section.** Three Deferred items are unverified facts, not deferrals: bot commits counting as activity, the nuget.org claim, and `$/`. Move them to an Open Questions list with their owning story. Story 1 can absorb them, given H7.
- **L17 — Operations omit the expiry of module-agent tokens (≤ 366 days) and the failure signal for hourly delivery.** Add both: renewal at expiry is noticed interactively, and `deliver.yml` failure email goes to the last cron editor.
- **L18 — Module-owned warning suppression.** A module's `Directory.Build.props` can add `NoWarn` or `WarningsNotAsErrors` for NU190x or analyzers, making CI green: gate erosion that AD-13 blocks for tests but nothing blocks here. Optionally, add a guard check, or accept it explicitly as product-code territory.

---

## What is solid and should be kept

- The paradigm and AD-1 materialisation remove the main source of non-reproducible CI.
- AD-4's perimeter table: whole directory, whole file, gitlink, partial superset and must-be-absent, each with a concrete check.
- AD-7's App-only unattended path, which closes the token-expiry risk for releases.
- AD-13's classifier, with no plain skip and one shared implementation for CI and the local check.
- AD-17's draft-release state machine, which removes the recovery workflows.
- AD-9's `$/` self-reference, with a named fallback.
