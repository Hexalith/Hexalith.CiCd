# Rubric review, pass 2: ARCHITECTURE-SPINE.md (Hexalith.CiCd)

- **Reviewed:** `../ARCHITECTURE-SPINE.md` (543 lines, AD-1..AD-21), against:
  - `../.memlog.md` and the pass-1 `review-rubric.md`;
  - `specs/spec-cicd/` (SPEC, its 5 companions, `stories.yaml`);
  - the brownfield code in `references/`. In Builds: `.github/workflows/*`, `Github/*`, `Props/`, `Hexalith.Build.props`, `package.json`, `commitlint.config.mjs`, `.github/dependabot.yml`, `Hexalith.Builds.slnx`, `Samples/`. In the modules: `.gitmodules`, instruction and release-config files, and their `uses: Hexalith/Hexalith.Builds/...` references;
  - live GitHub settings, read-only: Builds' rulesets and environments.
- **Date:** 2026-11-07
- **Method:** I checked the spine against the 7-point rubric. Every finding is tied to a file or an API result. I did not re-parse the Mermaid blocks; read by eye, they are valid, and the memlog records a clean parse with mermaid 11.4.1.

## Verdict

The revision closes most of pass 1. The spine is now a credible consistency contract:
- Builds' status is decided (AD-19).
- Credentials are scoped (AD-7).
- Delivery is gated (AD-6).
- The nightly order is safe (AD-16, AD-18).
- The brownfield NuGet-audit and Props code is ratified.
- A Precedence table exists.

It still has **four high-severity gaps** before it can bind the 27 stories:
1. Builds' own release has no config source and no decided payload.
2. The guard and restore consume an unvalidated CiCd `main`.
3. One module's live state can halt delivery for all modules.
4. The release can trust a green run from a drifted CI caller.

**Counts: 0 critical, 4 high, 16 medium, 18 low.**

## Pass-1 closure

| Pass-1 item | Status | Note |
| --- | --- | --- |
| C1 Builds status undefined | **Partly closed** | AD-19 settles the spoke question, the App installation and the file names. Builds' own .NET product, its release config and its release payload are still open (see H1 below). |
| H1 module-agent token repo scope | Closed | AD-7: module repos only |
| H2 delivery not gated on CiCd CI | **Partly closed** | Delivery is now gated (AD-6). The guard and restore still read ungated CiCd `main` (see H2 below). |
| H3 nightly ordering | Closed | The bump runs after all releases complete. The release SHA is `github.sha`. |
| H4 NuGet audit vs `Hexalith.Build.props` | Mostly closed | CI policy ratified. The release-build gate is unproven (M13). |
| H5 AD-2 vs `Props/` | Closed | AD-2 now scopes `Props/` out |
| H6 non-.NET surface | Closed | Python is tooling, removed by the gate rule. Aspire goes to story 15, with the knob path in AD-3. |
| H7 no spec-amendment list | Closed | The Precedence table exists. Some rows are missing (M1). |

Pass-1 mediums and lows that are still open, carried below:
- M4 Dapr part, now M11;
- M7 hook secrets, now M9;
- M9 `bmad-testarch-ci`, now M14;
- M10 `Samples/` shape, now L11;
- M15 props import paths, now L17;
- M17 arrows, now L7;
- L6, L10, L11, L12 and L14, now L6, L1, L12, L13 and M4.

## Rubric scorecard

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Fixes the real divergence points | Mostly. Open: H1, H3, M2, M3, M4, M7, M8, M16. |
| 2 | Every Rule is enforceable and prevents its divergence; no contradictions; cross-references correct | All AD-n cross-references resolve to the right AD. Two Rules do not prevent what they state: AD-6 "broken renders shipping" (H2) and AD-16 "releasing an untested commit" (H4). Two pairs contradict each other: AD-11 vs AD-12 (M7) and AD-12 vs AD-14 (M6). |
| 3 | Nothing Deferred lets units diverge | Fails on hook secrets (M9) and the Dapr pin site (M11). The "bot commits" item rests on false reasoning (M10). |
| 4 | Ratifies the brownfield code that is staying | Mostly. Open: the legacy freeze scope (M8), the Dapr pins (M11), the `.gitmodules` section names (L4), the commitlint lengths (L5), Builds' `build-release.yml` and its `production` environment (M15). |
| 5 | Covers CAP-1..16; Precedence table complete | All 16 CAPs are mapped. The Precedence table misses 3 deviations (M1). The map's "Governed by" column disagrees with the AD Binds (L2). |
| 6 | No silent dimension | Gaps: Builds and CiCd repo preconditions (M15), the registry credential reaching hooks (M6), the 60-day schedule disable (M10), the kill switch vs nightly security (M5) |
| 7 | Terse, no placeholders | The `[ADOPTED]` tags remain (L1). Story-level numbers and flags sit in AD-6, AD-16, AD-17 and AD-18 (L14). The spine grew from 418 to 543 lines. |

---

## Critical

None.

---

## High

### H1: Builds' own release has no config source, and Builds' .NET product has no decided fate (residual of pass-1 C1)
**Location:** AD-1 (line 105: "Builds' CI, Builds' release and `check.py` read it from the checkout"), AD-17 "What is published", AD-19, AD-20, Structural Seed.

**Finding:**
- **No config for Builds' release.** `builds-release.yml` calls the reusable `release.yml`. Per AD-1, that workflow reads `solution` and `codeql` from `.github/hexalith-ci.json`. Builds has no setup file and no render (AD-19), so it has no `hexalith-ci.json`. The `module-root`/`expected-source` inputs exist only for CI. The reusable release therefore has nothing to read for Builds.
- **Builds is a .NET product.** Per `Hexalith.Builds.slnx`, it has:
  - packable tools `Hexalith.Builds.Evidence.Cli` and `Hexalith.Builds.Module.Cli`;
  - 3 host projects and 3 test projects;
  - G-4 tool packages, published through `@semantic-release/exec` hooks in the root `package.json` (`Tools/publish-g4-tool-packages.ps1`).
- **Builds' CI drops those tests.** Builds' current CI runs those .NET tests plus 8 PowerShell catalog validators over `Props/Directory.Packages.props`. AD-19's `builds-ci.yml` runs only actionlint, zizmor, the Python tests and the `Samples/` CI.

The outcome depends on what `solution` resolves to for Builds:
- **The slnx:** AD-17 would pack and publish the CLIs untested.
- **`none`:** the G-4 packages and CLIs silently stop shipping.

Stories 2, 3, 8 and 27 each have to guess.

**Fix:** In AD-19, add:
- **Config.** "Builds carries a hand-written `.github/hexalith-ci.json`, validated by `builds-ci.yml` against `schemas/hexalith-ci.v1.json`, which `builds-release.yml` uses."
- **Payload.** Decide it. Recommended:
  - `solution: none`, and `codeql: [python]`, so Builds publishes a GitHub release only;
  - `src/`, `test/` and the G-4 packaging, with the root `package.json` `release` block and `Tools/*g4*`, are legacy tied to `domain-ci-v2`, and story 27 deletes them;
  - the `Props/` catalog validators become Python tests in `builds-ci.yml`, or are dropped under the gate rule. State which.
- **Old release workflow.** Say whether `build-release.yml` is deleted when `builds-release.yml` lands.

### H2: The guard and restore read ungated CiCd `main`, which bypasses AD-6's validation
**Location:** AD-8 (line 199: "shallow sparse git clone of CiCd `main`"), AD-6 Prevents ("broken renders shipping"), AD-5.

**Finding:** AD-6 now delivers only after `validate` passes, but AD-8's guard and restore consume CiCd `main` directly. Suppose a CiCd commit lands with a bad render: a schema-invalid `hexalith-ci.json`, a wrong `builds_tag`, or a template bug. Validation goes red and delivery stops, but two things still happen:
- Every module CI run compares against the broken render and goes red. That is a non-product red, against the spine's success signal.
- On every push to a module's `main`, the restore job writes the broken non-workflow files into that module: `hexalith-ci.json`, `dependabot.yml`, the gitlink, `.gitmodules`, the instruction blocks and the deny entries.

Even with a good commit, there is a window between the push to CiCd and the end of delivery:
- The guard already expects the new render.
- Restore writes the new `builds_tag` while the callers still carry the old one.
- The module goes red until delivery catches up.

The memlog recorded this "~1 min window" as a known effect, but the spine dropped it.

**Fix:** In AD-8, write: "The guard clones CiCd at the ref `delivered`. `deliver.yml` fast-forwards that ref to the validated SHA, with the App, immediately before pushing to modules. CiCd `main` is never read by the guard." Add `delivered` to the Consistency Conventions. This keeps "expected state = last validated state" for all three consumers (AD-4).

### H3: One module's live state can halt delivery for all 17 modules
**Location:** AD-3 "The validate job (AD-6) fails when…" (lines 128–133), AD-6 ("`deliver` runs only … after `validate` succeeds"), AD-7 (App-based agents: "The guard and hourly delivery are their control").

**Finding:** The validate job mixes two kinds of check:
- **Static checks:** render with no diff, schema, tool tests, lint.
- **Per-module live checks:** the action exists on the module's live `main`, the AD-21 preconditions, the App installation.

A module agent can legitimately rename or delete a directory under the module-owned `.github/actions/**`. A maintainer can also leave one precondition unset while onboarding a new module. Either way, `validate` fails, and every delivery stops in every module, the hourly runs included. Hourly delivery is the only repair for workflow drift by the org agent Apps (AD-7), so one module's state switches off enforcement everywhere.

**Fix:** Split the job in AD-3 and AD-6:
- Static checks gate the whole run.
- Per-module live checks gate only that module's delivery. That module is skipped, listed in the job summary, and the run ends red.

The module's own CI already goes red through the guard's "every enabled hook and job action exists" check (AD-8).

### H4: The release trusts a green CI run even when the CI caller itself has drifted
**Location:** AD-16 (lines 310–313), AD-7 (App-based agents hold Workflows write), AD-8 ("Workflow drift is left to the next delivery").

**Finding:** AD-16 accepts any successful run of `ci.yml` for the release SHA. The org agent Apps (`claude`, `chatgpt-codex-connector`, `cursor`) can rewrite `.github/workflows/ci.yml`, and the spine accepts this (AD-7). An agent might replace the `uses: Hexalith/Hexalith.Builds/...` call with its own steps, which is the exact behaviour this project exists to stop. The guard then never runs, CI can be green, and drift is repaired only at the next delivery, up to an hour later.

A nightly run dispatched in that window pins the drifted SHA and publishes it to nuget.org. That cannot be undone. AD-16's "Prevents: releasing an untested commit" does not hold.

**Fix:** In AD-16, add: "Before the green check, the release runs the guard's perimeter comparison (read-only) on the release SHA. Any owned-file drift fails with 'main is red, nothing released'." This takes seconds and needs no new credential. A lighter alternative is to require the green run to contain the reusable workflow's guard job (a job name prefix fixed in Conventions).

---

## Medium

### M1: The Precedence table misses three spec deviations
**Location:** Precedence table (lines 30–47).

**Finding:** These deviations are in force but not listed:
- **Builds is not managed.** CAP-1 says "all 18 modules call the same Builds CI workflow… only generated files". CAP-16 says "All 18 repositories are managed from here", and `module-inventory.md` lists 18 managed repos. AD-19 makes Builds unmanaged, hand-written and unguarded. Only the CAP-4 row mentions AD-19.
- **Browsers and Dapr run in the main job.** CAP-5 says "an action needing a … browser runner runs in its own job", and `pipeline-stages.md` names "a browser, a Dapr topology" as extra-job cases. AD-12 sets up browsers and Dapr inside the main job. Stories 17 (Folders) and 24 (FrontComposer) can each choose differently.
- **Majors and skipped tags are not auto-adopted.** CAP-6 says "Within one night of a Builds release, all modules reference it". AD-10 excludes majors and `builds-skip` tags from the auto-bump.

**Fix:**
- Add three rows that point at AD-19, AD-12 and AD-10.
- Add to AD-12: "A custom action that needs browsers or Dapr is a hook with `browsers`/`dapr` enabled. A `jobs` entry is only for another OS."

### M2: The bump and the rollback do not re-render, so validate fails and delivery halts
**Location:** AD-5 ("Whoever changes `setup/` or `templates/`…"), AD-18 Bump (line 349), AD-10 rollback.

**Finding:** The Builds tag appears in the render: in the callers, in `hexalith-ci.json` `builds_tag`, and in the perimeter gitlink. AD-18's bump changes `builds-version` and commits, but nothing says it re-renders. AD-5's rule covers only `setup/` and `templates/`. A literal implementation of story 8 commits a stale `rendered/`. `validate` then fails on every run, so all delivery stops, the hourly runs included. A manual rollback has the same problem. The memlog decision ("change version, re-render, commit") was lost in distillation.

**Fix:**
- AD-5: "Whoever changes `setup/`, `templates/` or `builds-version` re-renders and commits `rendered/` in the same commit."
- AD-18: "…bump `builds-version`, re-render, and commit both."

### M3: `deliver.yml` is both a top-level and a reusable workflow, and its concurrency rule cannot be applied
**Location:** AD-6 triggers (`workflow_call` from `nightly.yml`), AD-18 Bump, Conventions "Concurrency" ("only in top-level workflows, never in reusable ones").

**Finding:**
- **The rule does not decide.** `deliver.yml` is both kinds of workflow, so the rule says nothing for it. Story 4 owns it and story 8 calls it.
- **Delivery runs twice.** App pushes trigger push workflows (memlog), so the bump commit fires the push-triggered delivery as well as the `workflow_call`.
- **The nightly can fail falsely.** With a shared group, nightly's called delivery can sit pending and be replaced by a newer run, as the convention allows. That cancels nightly's job, turns `nightly.yml` red, and sends a false failure email.

**Fix:**
- Drop the `workflow_call` trigger. The bump commit's push triggers delivery, and nightly does not wait for it.
- Alternatively, declare `concurrency: deliver` at job level on the `deliver` job and record that exception in Conventions.

### M4: Nightly failure semantics and the duplicate-scan host are not fixed
**Location:** AD-18 "Wait and report" and "Bump" (lines 348–349), Capability map CAP-9 (`tools/scan.py`), Deferred (duplicate scan).

**Finding:**
- **Does a failed release block the bump?** AD-18 says "It fails if any run failed… Only then does it bump". It is ambiguous whether one failed module release blocks the bump. If it does, one permanently red module, or one with the kill switch unset (red under AD-17), stops the Builds bump for every module. That breaks CAP-6.
- **Where does the scan run?** `enforcement.md` says it "fails this repository's nightly run". No AD says which workflow runs `tools/scan.py`, whether it runs before or after the bump, or whether it blocks the bump. Stories 8 and 9 both edit `nightly.yml`. This is pass-1 L14, still open.

**Fix:** In AD-18, write:
- "The bump runs once every dispatched run has completed, whatever its conclusion. It requires only that Builds' own run was not a failure."
- "`nightly.yml` runs `tools/scan.py` as a separate job that does not gate the bump."
- "The workflow ends red if any release or the scan failed."

### M5: With the kill switch at `false`, the release may skip CodeQL and the nightly hook
**Location:** AD-17 steps 1–2 (line 326: "`false` succeeds … and creates or completes nothing"), CAP-14, AD-18 `nightly-hook`.

**Finding:** The kill switch is step 1, and the `codeql` and `nightly-hook` jobs are step 2. Read as a sequence, a module with publishing disabled never gets CodeQL. Its nightly hook also never runs, which matters for Folders' provider smoke test. CAP-14 says "each module's nightly run includes CodeQL".

**Fix:** In AD-17, write: "`codeql` and `nightly-hook` always run. The kill switch gates only draft creation and completion, and the `publish` job."

### M6: The CI registry login reaches custom actions, against AD-14's "no secrets"
**Location:** AD-12 stage 4 ("registry login if `registry`. Then hook `after-unit-tests`"), AD-14 ("read-only token and no secrets"), Conventions "Secrets and variables" (one `HEXALITH_REGISTRY_*` pair).

**Finding:**
- **The credential leaks.** `docker login` writes the credential to the runner's Docker config. Every later step in the job can read it, and that includes the hooks.
- **It can push.** The same credential pair pushes release containers, so module-owned actions hold write access to the registry.
- **The deny list does not help.** It bans "a registry login", but the action is already logged in.

**Fix:**
- In Conventions, write: "CI uses a pull-only pair, `HEXALITH_REGISTRY_PULL_USERNAME` and `HEXALITH_REGISTRY_PULL_PASSWORD`. The push pair is passed only to the release `publish` job."
- Alternatively, log out before the first hook, and state that in AD-12.

### M7: AD-11 and AD-12 conflict on Windows-capable composites, which risks two implementations of environment setup
**Location:** AD-11 ("All logic is Python"; "Composites that can run on Windows (`prepare`) contain no Python"), AD-12 (`prepare` gives the "same environment setup").

**Finding:**
- **No language is named.** `prepare` has to read `hexalith-ci.json`, decide on Dapr, browsers and registry, and build in package mode. AD-11 forbids Python there and names no other language.
- **The setup may be written twice.** AD-12's main-job environment setup is presumably Python. Story 2 would then write the "same environment setup" in two languages.

**Fix:** In AD-11, write:
- "Windows-capable composites use only `fromJSON()` expressions and one-line `pwsh` or `bash` steps."
- "The main CI job calls `prepare`'s environment-setup sub-composite, so one implementation exists."

Alternatively, allow `shell: python` on Windows images.

### M8: AD-20's freeze misses Builds files that modules call directly, and story 27's deletion list leaves orphans
**Location:** AD-20 (lines 389–392), CAP-16.

**Finding:** I grepped `references/*/.github/workflows`. These are called directly, not through `domain-*.yml`, which puts them outside AD-20's scope:
- `.github/workflows/codeql.yml`: 10 callers at `@main`;
- `commitlint.yml`: 10 callers at `@main`;
- `dependency-review.yml`: 11 callers at `@main`;
- `Github/initialize-build` and `Github/initialize-dotnet` at `@main`.

Two consequences:
- If story 3 reworks `codeql.yml`, or story 5 changes the commitlint workflow, every unmigrated module breaks.
- Story 27 does not delete `codeql.yml`, `commitlint.yml`, `commitlint-caller.yml`, `dependency-review.yml`, `candidate-policy.yml` or `build-release.yml`, so they stay as orphans.

**Fix:**
- AD-20: "Every workflow, composite, script and root config that any module references today (at `@main` or a SHA), directly or through `domain-*`, is frozen."
- Add the files above to story 27's deletion list.

### M9: Hook secrets are still deferred to story 20, which can reshape Builds' API (pass-1 M7)
**Location:** AD-14 (line 291), Deferred "Hook and job secrets".

**Finding:**
- **Builds' API changes.** A secret for an in-job hook needs a new `workflow_call.secrets` entry on Builds' `ci.yml`, which is public API (AD-10).
- **AD-2 is at risk.** An EventStore-specific secret name inside Builds would break AD-2.
- **The mechanism is still open.** Story 20 decides it alone.

**Fix:** Decide the mechanism now:
- "Actions that need cloud credentials run as rendered extra-runner jobs. They use OIDC (`id-token: write` plus the provider login in the rendered job), or named secrets that the caller passes as `env`."
- "In-job hooks never get secrets, and Builds' `ci.yml` declares only `HEXALITH_REGISTRY_*`."

Defer only EventStore's concrete identities.

### M10: The 60-day schedule disable hits both CiCd schedules, so the Deferred reasoning is false
**Location:** Deferred, "Whether bot commits count as activity" ("The 26-hour freshness check catches a stopped nightly either way"), Operations "Failure signal".

**Finding:** `nightly.yml` and `deliver.yml`'s hourly schedule both live in CiCd. Inactivity disables both at once, and the push trigger needs a push. The freshness check then never runs, and the failure is silent, which is the exact case the item claims is covered.

**Fix:**
- Delete "either way".
- State the backstop: "If story 8 finds that bot commits do not count, `nightly.yml` calls the workflow-enable API for both workflows on every run, and the maintainer re-enables them on any 60-day warning email."
- Alternatively, put a second freshness check in Builds' `builds-ci.yml`, which runs on every Builds push.

### M11: The Dapr pin site is not named, and the brownfield has three different values (pass-1 M4)
**Location:** Deferred "Dapr runtime value" ("One pin in Builds; seeded at 1.19.1"), Stack.

**Finding:** The brownfield pins Dapr in three places:
- `Props/Directory.Packages.props`: `HexalithDaprRuntimeVersion` 1.18.7 and `HexalithDaprCliVersion` 1.18.2;
- `Github/dapr-init/action.yml`: default 1.18.0;
- the Stack table: 1.19.1.

Module tooling reads the Props values (Parties' workflows, Conversations' tooling). Story 2 may pin the new composite to 1.19.1 while Aspire and test tooling keep 1.18.7.

**Fix:** In Conventions, write: "Dapr runtime and CLI versions live only in `Props/Directory.Packages.props` (`HexalithDaprRuntimeVersion`, `HexalithDaprCliVersion`). The Builds Dapr setup reads them and has no default." Story 2 bumps them to 1.19.1.

### M12: The local check's commitlint range is not fixed, so CAP-3 can diverge
**Location:** AD-15 ("the same guard"), AD-8 (commitlint: PR base..head, push before..after, dispatch `HEAD`).

**Finding:** Story 6 has no event, so it will pick a range: `HEAD`, or `origin/main..HEAD`. Suppose a push of three commits has a bad message in the first one. The local check passes on `HEAD` only, and CI fails on before..after. Stories 5 and 6 diverge.

**Fix:** In AD-15, write: "Commitlint checks `@{upstream}..HEAD`, falling back to `origin/main..HEAD`, which matches the push range CI will see."

### M13: The release's vulnerability gate is unproven against `Hexalith.Build.props` (residual of pass-1 H4)
**Location:** AD-17 step 6 (`-warnaserror:NU1903;NU1904 -p:NuGetAudit=true -p:NuGetAuditMode=all`), Precedence row "Dependency review…".

**Finding:**
- **The override may win.** `Hexalith.Build.props:33` adds NU1901–NU1904 to `WarningsNotAsErrors`. MSBuild also derives `MSBuildWarningsNotAsErrors` from that property. Whether a command-line `-warnaserror:<codes>` beats a project-level not-as-error is version-dependent.
- **Nothing tests it.** The memlog records the flags but no test. The item is also not in Deferred.
- **The failure would be silent.** This gate is the stated reason for dropping dependency review. If it is inert, vulnerable packages ship.

**Fix:**
- In AD-17, add: "`builds-ci.yml` proves the gate. A `Samples/` fixture that references a known NU1903 package must fail the release build step."
- Story 3 picks the mechanism that passes, for example adding `-p:WarningsNotAsErrors=` (a global override).
- Alternatively, list the item under Deferred with story 3 as its owner.

### M14: Nothing keeps `bmad-testarch-ci` absent (CAP-11, pass-1 M9)
**Location:** AD-4 "must be absent" row, CAP-11 map.

**Finding:** CAP-11 success says "`bmad-testarch-ci` is absent from all modules". Story 10 removes it once. The next BMAD reinstall, which is routine, restores it, and the guard does not check for it.

**Fix:** Add `.claude/skills/bmad-testarch-ci/`, `.agents/skills/bmad-testarch-ci/` and `.agent/skills/bmad-testarch-ci/` to the AD-4 "must be absent" row.

### M15: AD-21 covers modules only; Builds' and CiCd's preconditions are not listed
**Location:** AD-21 step 1, AD-19 ("The nuget.org policy names `builds-release.yml`"), AD-7.

**Finding:** Builds is released nightly from story 8, before any module migrates, and needs its own one-time settings. I checked live (`gh api`):
- Builds' ruleset "Protect main" requires a PR and the status checks `commitlint / commitlint`, Codacy and SonarCloud. The maintainer user can bypass it. The commitlint check name disappears with AD-20's rename.
- Builds' `production` environment has a required reviewer, a human gate that AD-17/AD-19 drop without saying so.
- Builds has no `v*` tag ruleset. The lockstep relies on immutable tags.
- Nothing says who sets these before Builds' first nightly release, or when:
  - the nuget.org policy for `builds-release.yml`;
  - `HEXALITH_RELEASE_PUBLISH_ENABLED` on Builds (unset means red under AD-17);
  - `HEXALITH_NUGET_USER` access for Builds;
  - code-scanning default setup off.
- CiCd has no rulesets at all.

**Fix:** Add an AD-21 step 0, "Builds and CiCd preconditions, before story 3 ships", covering:
- Builds' rulesets: cut to deletion and force-push on `main`, plus `v*` update and deletion;
- deleting the `production` environment;
- the nuget.org policy, if Builds still publishes packages (see H1);
- the kill-switch variable;
- org variable and secret access;
- code-scanning default setup off;
- deletion and force-push protection on CiCd `main`.

### M16: The container publishing contract is new and incomplete
**Location:** AD-17 "What is published" (`HexalithPublishContainer=true`), AD-10 public API, AD-21 step 2.

**Finding:**
- **The property is new.** `HexalithPublishContainer` does not exist in the brownfield. No AD says where it defaults to `false`, for example in `Hexalith.Build.props`.
- **Image names may change.** Today, image names come from the `container-projects` input (`path|repository-name`, in `Github/publish-containers`), or from `ContainerRepository` in some projects. The spine does not say where the image name and registry come from, so a migration can silently rename published images.
- **Nobody is told to set it.** Setting the property is not in AD-21 step 2's module-agent work.

**Fix:**
- AD-17: "Image = `registry.hexalith.com/$(ContainerRepository):<version>`. `HexalithPublishContainer` defaults to `false` in `Hexalith.Build.props`."
- AD-21 step 2: "Module agents set `HexalithPublishContainer` and keep today's `ContainerRepository` names."

---

## Low

- **L1. Template residue: `[ADOPTED]` remains on AD-1 and AD-2** (lines 99, 109). Delete it, or define it and apply it to every AD. This is pass-1 L10, still open.
- **L2. The Capability map's "Governed by" disagrees with the AD Binds in about 20 places.** Some examples:
  - AD-12 binds CAP-14, but the CAP-14 row omits it.
  - AD-6 binds CAP-8, but the CAP-8 row omits it.
  - AD-18 binds CAP-15, AD-19 binds CAP-6 and CAP-16, and AD-3 binds CAP-13 and CAP-16, and the rows omit them.
  - The CAP-16 row lists AD-4, which does not bind CAP-16.

  Generate the column from the Binds, or drop it.
- **L3. The "Story 1 spike scope" row conflicts with Deferred.** The row (line 47) says story 1 verifies everything still under Deferred. But Deferred names stories 2, 8 and 15 as verifiers, and it mixes decisions into the list (SDK unification, Dependabot ownership, composite names). Mark the verify-items and their owners, and move the decisions into Conventions.
- **L4. `.gitmodules` section names differ across modules.** Conversations, McpCli and Platform use `references/Hexalith.Builds`, and the other modules use `Hexalith.Builds`. AD-4 says "section for `references/Hexalith.Builds`". Fix: "the section whose `path` is `references/Hexalith.Builds`; its name is kept as found".
- **L5. The commitlint lengths change the brownfield config.** The brownfield `commitlint.config.mjs` sets header and body to 200. The spine says "body and footer unlimited" and does not mention the header (config-conventional's default is 100). Ratify `header-max-length: 200`, or state the change.
- **L6. The deny-list source.** AD-8 says "(`enforcement.md`)". At run time the list must be a constant in Builds' guard, seeded from `enforcement.md`. This is pass-1 L6, still open.
- **L7. The dependency diagram is normative but misses two arrows.** It lacks:
  - `CALLER → ACT`: the extra-runner job's `./.github/actions/<job-name>`, from AD-12;
  - `CiCd tools → module live main`, a read-only clone, from AD-3.

  Add both arrows.
- **L8. The App's permissions do not cover the precondition checks.** AD-3 and AD-21 need organization-level reads: org secret and variable access, and the org App installations for `semgrep-app`. AD-7 lists repo-level reads only. Add those reads to AD-7, or state that those checks are manual. AD-7 should also say whether `HEXALITH_CICD_APP_ID` is a secret or a variable.
- **L9. CI concurrency on `main` drops intermediate SHAs.** With the group "per workflow and ref", a pending `main` run is replaced by a newer one. A release pinned to a replaced SHA then reads "main is red". Use a per-SHA group for `push` on `main`, or accept and document this.
- **L10. AD-6 lints "actionlint and zizmor on templates and render".** Jinja2 templates are not YAML. Lint the render only.
- **L11. The shape of `Samples/` and the self-test hook location are unstated.** Hook `uses:` are literal, so in Builds' self-test `./.github/actions/<hook>` resolves at Builds' root, not at `Samples/`. Define what `Samples/` must exercise, and state that sample hooks live in Builds' root `.github/actions/`. This is pass-1 M10, partly open.
- **L12. The AD-13 name table misses known names.** EventStore's Azure-backed `LiveTests` and the `LoadTests` projects default to stage 3. Have each migration story record its `tests.integration` overrides, or extend the table. This is pass-1 L11.
- **L13. Prerelease channels are dropped without saying so.** Builds' `prerelease` branch (`package.json`, `build-release.yml`) and its environment disappear under main-only AD-17. State it. This is pass-1 L12.
- **L14. Some ADs hold story-level detail.** Examples: "at most 3 times" (AD-6), 30 minutes (AD-16), the `dotnet nuget push --skip-duplicate` and audit flags (AD-17), 60-second polling and 50 days (AD-18). Story 3 alone owns AD-17's six-step state machine. Keep the invariants: tag last, the draft marker, the SHA pin, and the publish job in the caller. Move the numbers and flags to Deferred, naming the owning story.
- **L15. A CodeQL or audit block has no fixed outcome.** Fixed messages and AD-18's summary categories do not cover a release blocked by CodeQL or by audit. Add "blocked by security findings" to both.
- **L16. The App key is available to every CiCd workflow.** Same-repo PR runs and any workflow a CiCd agent adds can read `HEXALITH_CICD_APP_PRIVATE_KEY`. Put the key in an environment whose deployment-branch policy allows only `main`.
- **L17. AD-10's public API omits the import paths.** It lists two MSBuild properties, but not the import paths (`Hexalith.Build.props`, `Hexalith.Package.props`, `Props/Directory.Packages.props`) or the removal of a `PackageVersion`. A minor release that removes one breaks modules. This is pass-1 M15, partly open.
- **L18. The `publish` job permissions are incomplete.** AD-17 gives the job `id-token: write`. Publishing the draft also needs `contents: write`. State the full set, since it is caller-side public API (AD-10).

---

## What is solid and should be kept

- The Precedence table: a story developer can now see where the spine overrides `stories.yaml`.
- AD-19: Builds as the runtime, with test-only inputs that module callers never set.
- AD-4's perimeter file, consumed by guard, restore and delivery alike, with blob comparison and minimal partial edits.
- AD-16 and AD-17: the SHA pinned at dispatch, the draft marker, tag last, and NuGet/login in the caller job, which matches nuget.org's `job_workflow_ref` check.
- AD-7: the residual risk of the org agent Apps is stated honestly, with a named control.
- AD-21: onboarding as preconditions, then the product side, then one adopt commit, with the validate job checking what the API exposes.
