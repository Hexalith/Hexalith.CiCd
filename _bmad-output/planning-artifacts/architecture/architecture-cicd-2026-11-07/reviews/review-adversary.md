---
reviewer: adversary
lens: construct two units one level down (stories in spec-cicd/stories.yaml) that each obey every AD to the letter yet build incompatibly
target: ../ARCHITECTURE-SPINE.md (draft, 2026-11-07)
date: 2026-11-07
---

# Adversarial review: Hexalith.CiCd architecture spine

## Verdict

The paradigm is sound, but the spine is not yet build-safe for independent agents. Two holes make day-one migrations fail permanently. First, Builds' own status, spoke or hub, is undefined. Second, nobody owns *deleting* what whole-directory ownership forbids. Nine more holes give each pair of stories a different reading of one contract, most often the Builds `workflow_call` interface, "head of main", the delivery trigger, and the owned-perimeter shape.

Grounding checks I ran against the checkouts in `references/`:
- Builds already has its own push/PR CI at `.github/workflows/ci.yml`, the name the spine reserves for the reusable workflow.
- Unmigrated modules call Builds at `@main` (`initialize-build@main` ×21, `initialize-dotnet@main` ×18, `dependency-review.yml@main` ×12, `codeql.yml@main` ×11, `commitlint.yml@main` ×11, `domain-ci.yml@main` ×4).
- FrontComposer's `.gitattributes` is `* text=auto eol=crlf`, and Memories' is `* text=auto eol=crlf`.
- AI.Tools has no solution, no Builds submodule, and a tool-only `package.json`.
- 11 modules carry `.releaserc.json` or `release.config.cjs`.

| Tier | Count |
| --- | --- |
| Critical | 2 |
| High | 9 |
| Medium | 12 |
| Low | 8 |

---

## Critical

### C1. Builds is both a managed spoke and the hub runtime

- **Units:** Story 4 (setup format and generator, "adding a submodule plus a setup file onboards a repo") and Story 8 (scheduler) against Stories 2/3 (Builds' reusable `ci.yml`/`release.yml`, authored directly in Builds).
- **Each obeys:**
  - Story 4 writes `setup/Hexalith.Builds.yml`. Builds is a submodule of CiCd, SPEC CAP-16 says all 18 repos are managed, and every AD-3 CiCd CI check passes.
  - Story 8 enumerates `setup/*.yml` (AD-3: "no other module list exists"), so it can only dispatch Builds if Builds has a setup file.
  - Stories 2/3 author `.github/workflows/ci.yml` and `release.yml` in Builds, as the conventions table names them.
- **Clash:**
  - With a setup file, AD-4 whole-directory ownership makes delivery overwrite Builds' reusable workflows with a rendered caller that calls itself.
  - Without one, AD-18's "dispatch Builds" has no source, and AD-7's App installation ("managed modules and CiCd") doesn't include Builds, so the dispatch has no token.
  - AD-16 reads "`ci.yml` runs (push or workflow_dispatch)". In Builds, `ci.yml` is the reusable workflow, which is `workflow_call` only. The existing self-test CI already holds that name and must be renamed. Builds' release therefore always gets "no run" and reports "main is red, nothing released". No Builds tag is ever produced, so there is never a bump (CAP-6, CAP-15).
  - AD-10 needs two releaseRules sets in one Builds composite. AD-2 forbids `if repo == Builds`, and AD-3 offers no knob, so Story 3 must invent a selector, and either choice breaks one AD.
- **Fix: new AD-19 "Builds is the hub runtime, not a spoke":**
  - There is no `setup/Hexalith.Builds.yml`, and the schema or CiCd CI rejects one. Builds is never rendered, delivered, guarded, bumped or duplicate-scanned. The managed modules are the 17 setup files. `nightly.yml` names Builds as its one fixed extra dispatch.
  - The App installation includes Builds. Jobs that touch Builds mint `actions: write`-only tokens.
  - Builds' self-test CI is `.github/workflows/builds-ci.yml` (push, pull_request, workflow_dispatch). The reusable `ci.yml` is `workflow_call` only.
  - Builds' `release.yml` declares both `workflow_call` and `workflow_dispatch`. Both declare inputs `ci-workflow` and `release-rules` (`module` | `builds`).
    - Under `workflow_call` the defaults are `ci.yml` and `module`, and module callers never set them.
    - Under `workflow_dispatch` the defaults are `builds-ci.yml` and `builds`.
    - AD-16 reads the workflow named by `ci-workflow`.

### C2. Nobody deletes what the perimeter says must not exist

- **Units:** Delivery (`deliver.yml`/`deliver.py`, which no story owns; see H5) against Story 5 (guard and restore). Migration Stories 11–26 are a third candidate deleter.
- **Each obeys:**
  - Delivery takes "a sparse clone of the owned paths and writes the render. No diff means no push" (AD-6).
  - The guard treats any unrendered file under `.github/workflows/` as drift, and any present must-be-absent path as drift (AD-4).
  - Restore handles only agent-reachable files, and "drift under `.github/workflows/**` is left to the next delivery" (AD-8).
- **Clash:**
  - The first delivery to Commons overwrites `ci.yml` and `release.yml` but leaves `codeql.yml`, `commitlint.yml` and `dependency-review.yml` in place.
  - The guard goes red. Restore may not touch workflows. The next delivery writes the same render, finds no diff and pushes nothing. The module is red forever.
  - Meanwhile legacy `codeql.yml` keeps running CodeQL on every push (breaks AD-12). Folders' `nightly-drift.yml` and FrontComposer's three nightly schedules keep firing (breaks AD-18 "modules have no `schedule:`").
  - `.releaserc.json` (11 modules), `commitlint.config.*` and `.husky/commit-msg` are not in delivery's sparse clone. Restore may or may not delete them, since AD-8 only says "restores". A module agent may delete them too. Three possible deleters is the same as none.
- **Fix: tighten AD-6.**
  - "Delivery makes every AD-4 path equal to the desired state:
    - it writes rendered files;
    - it deletes every file under `.github/workflows/` that is not rendered;
    - it deletes every must-be-absent path and removes the `release`/`commitlint` keys from `package.json`;
    - it merges the `permissions.deny` entries;
    - it sets the gitlink.
  - Restore performs the same operations for every AD-4 path except `.github/workflows/`."
  - Assign `deliver.yml` to Story 4 explicitly (see H5).

---

## High

### H1. The Builds `workflow_call` interface has no owner, no names and no encoding

- **Units:** Stories 2/3/5 (Builds `ci.yml`, `release.yml`, restore job) against Story 4 (caller templates).
- **Each obeys:**
  - AD-3 names the knobs (`solution`, `dapr`, `tests.integration`, `tests.exclude`, `hooks`, `jobs`).
  - AD-10 makes Builds' inputs and secrets its semver API.
  - AD-1 says the values are rendered into the caller.
  - Each agent then picks names itself.
- **Clash:**
  - `workflow_call` inputs are only `string`, `number` or `boolean`. `tests.integration` (a list), `tests.exclude` (a map) and `hooks` (a list) need a serialization.
    - Story 2 parses `hooks: "after-unit-tests,nightly"`. Story 4 renders `'["after-unit-tests"]'`.
    - `contains()` still matches on the hooks, but the `tests.exclude` map fails to parse, so an excluded project runs in stage 3 or the run aborts.
  - Required secrets (Zot, and EventStore's Azure secrets later) have no agreed names on either side.
  - Required **caller permissions** are unstated. A called workflow can only narrow what the caller grants. A caller rendered "least privilege" (`contents: read`, which zizmor rewards) makes every run fail at startup: "nested job 'restore' is requesting 'contents: write, actions: write', but is only allowed 'contents: read'". Release needs `id-token`, `contents: write`, `security-events: write` and `actions: read`.
  - Nothing catches a minor Builds release that renames an input: the nightly auto-bump (AD-10) delivers it to every module.
- **Fix: new AD "Builds interface contract".**
  - A table in the spine lists, for each reusable workflow and for `prepare`, every input (name, type, default), every secret name, and the exact per-job `permissions:` block the caller must grant.
  - Lists and maps are passed as compact JSON strings.
  - CiCd CI validates every rendered caller against `on.workflow_call` of Builds at the `builds-version` tag. It checks names, types, required inputs, secrets and permissions. The nightly bump commit gets the same check before delivery (H5).

### H2. Concurrency: deadlock by placement, and cancelled runs that AD-16 cannot classify

- **Units:** Story 2 (Builds `ci.yml`) and Story 3 (Builds `release.yml`) against Story 4 (callers). Story 5 (restore dispatch) and Story 3 (green check) are the second pair.
- **Each obeys:** The conventions table says "CI per ref, cancel superseded; `release` per repo, never cancel" without saying where the group is declared. Both sides declare it.
- **Clash:**
  - When a caller and its called workflow use the same group, GitHub cancels with "deadlock for concurrency group detected between 'top level workflow' and '<job>'". That happens in every module, for both CI and release.
  - "Cancel superseded" on `main` cancels the run for SHA S while the release waits up to 30 minutes on S. AD-16 lists success, failure, none and running, but not `cancelled`.
  - With `cancel-in-progress: false`, GitHub still replaces an older *pending* run, so "never cancelled" cannot be implemented for any group.
  - Restore dispatches `ci.yml` on `main` while its own run is still in progress. The new run supersedes and cancels its parent, so the offending SHA ends `cancelled` instead of "failed with the ownership message" (CAP-8).
- **Fix: tighten the conventions and AD-16.**
  - "Concurrency is declared only at workflow level in rendered callers and in CiCd workflows. Builds reusable workflows declare none."
  - "CI uses the group `ci-<ref>` and cancels in progress only for `pull_request`. `push` and `workflow_dispatch` runs on `main` get a per-run group, so every main SHA gets a conclusive run."
  - AD-16: "Only `conclusion == success` on the latest attempt is green. Every other conclusion is red."
  - Replace "never cancelled" with "a replaced pending run loses nothing because every run is idempotent from current state" (see H5).

### H3. "Head of main" is read three times, and the bump can land between the reads

- **Units:** Story 3 (release) against Stories 7/8 (bump and scheduler), plus agents and hourly delivery.
- **Each obeys:**
  - The release checks the "head SHA of `main`" (AD-16), and semantic-release computes "from the head" (AD-17).
  - Nightly dispatches everything at once and lets GitHub queue it (AD-18). "When Builds' release completes", delivery bumps the modules.
- **Clash:**
  - 18 modules × up to three jobs (`codeql`, `nightly-hook`, `release`), plus Builds, is roughly 40–55 jobs against a limit of 20. Many module releases start after the bump commit has landed.
  - A release that re-reads head through the API waits 30 minutes on bump CI and then releases on the new Builds. That is the "bump-first" order the memlog rejected.
  - A release that pins `github.sha` hands semantic-release a local branch that is behind `origin/main`. semantic-release logs "local branch is behind the remote one, therefore a new version won't be published" and exits 0. The night reads as "nothing to release", which is a silent CAP-13 miss.
  - Any agent push after dispatch has the same effect.
- **Fix:**
  - AD-16/17: "The release SHA is `github.sha` of the dispatch. The green check, CodeQL, the semantic-release analysis and the draft all use it. semantic-release runs on a local `main` at that SHA, with no remote ahead of it."
  - AD-18: "The bump delivery starts only after every dispatched release run has completed."

### H4. A rollback is undone by the next night's auto-bump

- **Units:** Story 7 (bumper and rollback, "a rollback is the same bump in reverse") against Story 8 (nightly auto-bump within the major).
- **Each obeys:** Story 7 writes the older tag to `builds-version` (AD-10). Story 8 bumps to the latest tag within the current major (AD-10/18).
- **Clash:** At 02:17 the next night the bad tag is the newest within the major, so it comes back. Releases are immutable, so there is no way to retract it. The documented rollback lasts less than 24 hours.
- **Fix:** In AD-10, `builds-version` carries `version` plus a `skip: [tags]` list. "The auto-bump moves only forward, to the highest tag within the major that is not in `skip`. A rollback is one CiCd commit that sets `version` and adds the bad tag to `skip`."

### H5. Delivery is unowned, ungated, and invoked three ways

- **Units:**
  - Story 4 (generator; CiCd CI re-render check) against Story 7 (bumper, which pushes into modules).
  - Story 8 (nightly "runs delivery") against the push trigger of `deliver.yml`.
- **Each obeys:**
  - AD-6 lists four triggers, including "a push to CiCd `main` touching … `rendered/`".
  - AD-5 says CiCd CI re-renders and fails on any diff.
  - AD-18 says nightly "runs delivery".
  - No story is titled delivery, so Story 7 can build its own pusher for the bump while still calling it "a delivery of a changed version value".
- **Clash:**
  - Delivery starts on the same push as CiCd CI and ships to 17 modules a render (or a bump) that CiCd CI is about to reject. Hourly delivery ships CiCd `main` even when it is red.
  - The bump commit fires the push trigger *and* nightly's own delivery. A third, hourly run then replaces whichever is pending (see H2). If the replaced run is nightly's in-workflow delivery job, nightly goes red.
  - On a non-fast-forward, the bump's textual rebase of `rendered/` over a concurrent setup commit can produce a render that `render.py` would never emit.
- **Fix: tighten AD-6.**
  - "`deliver.yml` is built in Story 4. Story 7 adds only the `builds-version` bump step to `nightly.yml`."
  - "Delivery runs on `workflow_run` success of CiCd CI on `main`, hourly and on dispatch. It always delivers the newest CiCd `main` commit whose CI is green."
  - "Nightly bumps by committing `builds-version` plus the re-render with the App token, nothing else. It then waits for a delivery run whose `head_sha` contains its bump commit."
  - "Every automated writer (delivery, bump, restore) recomputes from the new head on a non-fast-forward and never runs `git rebase`."

### H6. The migration stories are told to use a credential no agent may hold

- **Units:** Stories 11–26 ("push with the delivery credential decided in story 1") against AD-7 and Story 10 (agent tokens).
- **Each obeys:**
  - Story 1 decides the App credential, and the migration story pushes with it.
  - AD-7 says the key "never enters a module or an agent session". The CiCd-agent token covers only Builds and CiCd. The module-agent token has no Workflows permission.
- **Clash:**
  - The migration agent either leaks the App key into its session or cannot push at all.
  - The half-migrated ordering is undefined:
    - YAML-asserting tests fail the moment delivery replaces the workflows.
    - AD-3's "names an action the module lacks" check fails if hooks are enabled before the custom actions exist.
    - Kill-switch variables, nuget.org policies, org-secret access, CodeQL default setup and stale CodeQL configurations (M8), and leftover drafts (M6) are nobody's step.
- **Fix: new AD "Onboarding sequence":**
  1. A module-agent-token commit adds the custom actions, deletes the YAML-asserting tests and legacy gates in product code, and removes the must-be-absent files.
  2. A CiCd commit adds the setup file and the render. CiCd CI checks the preconditions: submodule, App installation, actions, the `HEXALITH_RELEASE_PUBLISH_ENABLED` variable, org-secret access, and CodeQL default setup off.
  3. The first delivery replaces `.github/workflows/` wholesale.
  - "Agents never push owned paths."
  - Replace the stories' "delivery credential" wording to match.

### H7. Rewriting Builds `main` breaks every module that has not migrated yet

- **Units:** Stories 2/3/5 (rewrite Builds; inventory: composites "reviewed against the new workflows"; "commitlint moves into the guard") against unmigrated modules waiting on Stories 13–26.
- **Each obeys:** AD-10 governs exact-tag consumption by *migrated* modules only. Nothing protects `@main` consumers.
- **Clash:**
  - Unmigrated modules call `initialize-build@main`, `initialize-dotnet@main`, `codeql.yml@main`, `commitlint.yml@main`, `dependency-review.yml@main` and `domain-ci.yml@main`.
  - Story 3 folds CodeQL into release, Story 5 absorbs commitlint, and Story 2 reworks `initialize-build`. Each change breaks up to 16 repos the moment it lands.
- **Fix: new AD "Legacy freeze":** "Until Story 27, Builds never modifies or removes a file that an unmigrated module references. New pipeline code uses new paths and names only. Story 27 deletes the legacy files."

### H8. The perimeter is implemented twice, and its data shape is undefined

- **Units:** Story 4 (render and delivery in CiCd) against Story 5 (guard and restore in Builds).
- **Each obeys:** Both implement the AD-4 table faithfully.
- **Clash:**
  - **Gitlink shape.** `rendered/<Repo>/references/Hexalith.Builds` cannot be a gitlink inside CiCd's tree. One side renders a tag file, the other expects a gitlink or nothing.
  - **`.claude/settings.json`.** Is the rendered file the deny fragment or the full file? If it is the full file, the render reads module content and breaks AD-5 determinism. Delivery re-serializes with `indent=2` and restore with `indent=4`, so each rewrites the other and races agents editing their allow list.
  - **Absent paths.** Is it `.releaserc*` at the root only or recursively? Is it `.husky/commit-msg` the whole file or only the commitlint line?
  - **Line endings.** FrontComposer's `* text=auto eol=crlf` puts CRLF in the working tree on Linux. A guard comparing working-tree bytes with the LF render sees drift on every run. Restore writes LF, git normalizes it, and nothing is committed: a permanent red, or a loop.
- **Fix: tighten AD-4.**
  - "The render emits `rendered/<Repo>/.hexalith/perimeter.json`, which lists:
    - whole files and the whole directory;
    - partial JSON keys;
    - absent globs, rooted at the repo root;
    - the gitlink as `{path, tag}`.
  - The guard, restore and delivery all consume it, so there is no hard-coded path list in Builds.
  - Whole files are compared as git blobs (`git show <sha>:<path>`), and the render writes LF, UTF-8, no BOM, with a final newline.
  - Partially owned files are judged by the guard's semantic check and written only when that check fails, so the existing formatting is kept."

### H9. The local check cannot read what CI receives as inputs

- **Units:** Story 6 (`check.py`, standard library only per AD-11) against Story 4 (overrides rendered "as caller inputs") and Story 2 (classifier fed by those inputs).
- **Each obeys:**
  - AD-13 provides one classifier.
  - AD-15 says the local check first compares the pointer with "the caller tag".
  - AD-11 allows no PyYAML in Builds runtime.
- **Clash:**
  - `check.py` must parse the caller YAML with regular expressions to get `tests.exclude`, `tests.integration` and the tag, and it breaks on the first template reformat. Or it skips them, and the local check runs excluded projects and moves integration overrides to stage 3, against CAP-3.
  - The **project identifier** is unspecified (name, `.csproj` name, or solution-relative path). Story 4's schema validates names, Story 2 matches paths, and the overrides silently never apply.
- **Fix:**
  - "The render writes `.github/hexalith-ci.json`, owned as a whole file, holding `builds_tag`, `solution`, `dapr`, `tests`, `hooks` and `jobs`. Builds CI and `check.py` both read it from the checkout (AD-1 holds, since it is in the commit). The caller passes no per-module inputs beyond what `uses:`/`if:` need."
  - "A project is identified by its solution-relative path with forward slashes."

---

## Medium

### M1. Builds environment setup runs after the first hook and keys off the classifier
- **Units:** Story 2 (setup order) against Stories 17/20/24 (custom actions for Folders' E2E and accessibility checks, EventStore's Dapr broker tests, FrontComposer's browser tests), with Story 9 (duplicate scan) downstream.
- **Clash:**
  - AD-12 runs hook `after-unit-tests` *before* the Dapr and Playwright setup.
  - Playwright is installed only for E2E projects classified into stage 4. A project in `tests.exclude` that is run by an action is never in stage 4, so no browsers are installed.
  - Each action then installs browsers itself. That duplicates environment setup, and `dapr init` is deny-listed while `playwright install` is not. The copies in Folders and FrontComposer trip the duplicate scan.
- **Fix:** "Builds environment setup runs once, before any stage-4 hook. It is driven by the setup knobs `dapr` and `browsers` (new), never by the classifier. Dapr stays up until the job ends."

### M2. Guard behaviour on `workflow_dispatch` runs is undefined
- **Units:** Story 2 (the restore job's `if:` in `ci.yml`) against Story 5 (guard modes and commitlint range).
- **Clash:**
  - AD-8 defines a PR mode and a push mode only.
  - A run dispatched by restore has no pushed range. Commitlint then checks either everything (red forever on legacy history) or nothing.
  - If the dispatched run is treated as a push, it restores again. With only workflow drift it has nothing to commit, dispatches again anyway, and loops until delivery arrives.
- **Fix:** "On `workflow_dispatch` the guard only checks, and commitlint checks `HEAD` only. Restore dispatches only after pushing a commit, and a dispatched run never restores."

### M3. Restore against delivery and agent pushes on a non-fast-forward
- **Units:** Story 5 (restore) against delivery (rebase and retry).
- **Clash:**
  - A restore computed from an earlier CiCd clone can be rebased over a newer delivery commit and write back the older render, which AD-8 claims to prevent.
  - Delivery's `git rebase` conflicts when restore already wrote overlapping lines.
- **Fix:** "Restore never retries. On a non-fast-forward it stops, because the newer commit's own CI handles it." H5's recompute rule covers delivery.

### M4. CiCd tools read module content from stale CiCd submodule pointers
- **Units:**
  - Story 4 (the AD-3 "names an action the module lacks" check, project names, and dependabot ecosystems).
  - Story 9 (the duplicate scan "every module's custom actions").
  - Stories 25/26, which bump pointers by hand.
- **Clash:**
  - Nothing moves CiCd's `references/*` pointers, since AD-5 allows no automated commits.
  - The checks pass against month-old code. The scan misses fresh duplicates and flags deleted ones.
- **Fix:** "CiCd tools that read module content shallow-clone the module's live `main`. They never read CiCd's submodule checkouts, which exist only as agent context."

### M5. An enabled action deleted in the module fails late and obscurely
- **Units:** Story 4 (existence checked only when the setup changes) against Story 2 (literal `uses: ./.github/actions/<hook>`), with AD-4 making actions module-owned.
- **Clash:**
  - An agent removes or renames an enabled action. CI then fails at stage 4 with "can't find action.yml", not at stage 1.
  - The agent likely restores a stub, which quietly erodes the gate.
  - `tests.exclude` can name a *dormant* hook, which is a plain skip in disguise.
- **Fix:**
  - "The guard checks that every enabled hook, job and `tests.exclude` target exists."
  - "The schema requires each `tests.exclude` target to be an enabled hook or job."

### M6. The draft state machine reads stale tags and adopts foreign drafts
- **Units:** Story 3 step 1 (complete a draft) against Story 3 step 2 (semantic-release), and Story 3 against migration Stories 11–26.
- **Clash:**
  - The tags were fetched before step 1 published v1.3.0, so step 2 computes v1.3.0 again from the head.
    - `--skip-duplicate` silently keeps the old package.
    - The container tag `v1.3.0` is overwritten with new content.
    - Both break AD-17 "never republished from different content".
  - Step 1 "completes" any draft, including drafts left by legacy flows or created by hand.
- **Fix:**
  - "A run that completes a draft stops there."
  - "Only drafts carrying the pipeline marker (body trailer `hexalith-release: <sha>`) are completed."
  - "Onboarding deletes other drafts."

### M7. Kill switch against draft state, and an unset kill switch
- **Units:** Story 3 against onboarding (Stories 11–26) and Story 8 (summary).
- **Clash:**
  - The check is "before any push", but before or after draft creation is unstated. If it comes after, a draft computed weeks ago is published the night the switch flips back on.
  - An unset variable means "publishing disabled", which succeeds. A newly onboarded module never releases, and nightly stays green.
- **Fix:**
  - "The kill switch is the release's first step. When it is off, no draft is created or completed."
  - "The nightly summary reports 'publishing disabled' as its own non-green status."
  - The H6 precondition check confirms the variable exists.

### M8. Legacy CodeQL state blocks the new gate
- **Units:** Story 3 (gate on "open high/critical alerts") against migration Stories 11–26, since 12 repos run CodeQL today.
- **Clash:**
  - Alerts from the deleted `codeql.yml` configuration stay open as a stale configuration, so the gate blocks on findings the new analysis no longer reports.
  - With CodeQL *default setup* enabled, the release's advanced upload is rejected.
- **Fix:**
  - "The gate counts only alerts from the `release.yml` CodeQL configuration, using a fixed category."
  - "Onboarding disables default setup and deletes stale configurations."

### M9. Repos without a solution or a Builds submodule
- **Units:** Story 12 (AI.Tools: no `.sln*`, no `.gitmodules`, a commitlint-only `package.json`) against Story 2 (stage 2 is mandatory) and delivery (sets only the gitlink).
- **Clash:**
  - Stage 2 fails with "MSB1003" on every run.
  - A gitlink without a `.gitmodules` entry fails `git submodule update`, and `check.py` cannot exist.
  - FrontComposer's `.gitmodules` sets `branch = main` for Builds, which invites `git submodule update --remote` drift, and `.gitmodules` sits outside the perimeter.
- **Fix:**
  - AD-3: "`solution: none` runs only stage 1, and release publishes only the GitHub release."
  - AD-4: "The `[submodule "references/Hexalith.Builds"]` section of `.gitmodules` is owned: `path` and `url` only, with no `branch` or `update`."

### M10. No unit writes the agent instructions into modules
- **Units:** Story 10 (edits `hexalith-llm-instructions.md` in AI.Tools) against Story 15 (deletes McpCli's sync, which "belongs in AI.Tools' own sync") and AD-4/AD-7.
- **Clash:**
  - AI.Tools cannot host a sync workflow, because its `.github/workflows/` is rendered and an unrendered file is drift.
  - A cross-repo sync needs the App key in a module.
  - CAP-11's "every module's AGENTS.md, CLAUDE.md and copilot-instructions.md carry the rule" has no write path.
- **Fix:** Name the writer. The recommended writer is delivery, which owns a marker-delimited block in those three files, rendered from AI.Tools at a pinned commit. The alternative is an explicit interactive step using module-agent tokens.

### M11. Builds' self-test cannot exercise the guard modules run
- **Units:** Story 2 (reusable CI run against `Samples/`) against Story 5 (guard clones `rendered/<github.repository>/`).
- **Clash:**
  - In Builds the guard finds no `rendered/Hexalith.Builds/`, which is correct under C1. Story 2 then either skips the guard, leaving the path modules depend on untested (CAP-15), or adds an ad hoc module-root or "test mode" input that no setup knob produces (AD-2/AD-3).
- **Fix:** "Builds' public API includes the test-only inputs `module-root` and `expected-source` (a local fixture path). Modules never set them. `builds-ci.yml` drives `Samples/` with a fixture perimeter."

### M12. Dependabot commits against Builds' commitlint
- **Units:** Story 5 (commitlint config inside Builds) against Story 4 (rendered `dependabot.yml`).
- **Clash:**
  - Dependabot commit bodies (URLs and `updated-dependencies` YAML) exceed `body-max-line-length: 100`. Every Dependabot PR, and every squash-merge to `main`, turns the guard red.
  - The commit-message prefix decides releasability (`build(deps)` against `fix(deps)`), and only Story 4 sets it.
- **Fix:**
  - "Builds' commitlint config disables the body and footer line-length rules."
  - "The rendered `dependabot.yml` sets `commit-message.prefix: build`, `include: scope`."

---

## Low

- **L1.** The Windows extra-runner job runs `prepare`. AD-11 says scripts "run with `python3`", which is not guaranteed on `windows-latest`. Story 16 against Story 2. **Fix:** composites invoke scripts with `shell: python` (verify).
- **L2.** A `jobs` name may equal a hook name, so both map to `.github/actions/<name>`. **Fix:** the schema forbids job names `after-unit-tests`, `after-integration-tests` and `nightly`.
- **L3.** AD-15's "Builds pointer" can mean the gitlink in `HEAD` or the checked-out submodule commit. An agent who skipped `git submodule update` runs a different `check.py` than CI. **Fix:** check that both equal the caller tag.
- **L4.** AD-4 bans only the `release`/`commitlint` *keys* in `package.json`. The memlog also bans tool-only `package.json` files: AI.Tools has commitlint only in `devDependencies`, which Story 5's guard passes and Story 12 keeps. **Fix:** "and no `semantic-release`/`@commitlint/*` dependencies."
- **L5.** The value shape of `builds-version` (`v4.45.0` or `4.45.0`) and the annotated-tag dereference are read by render, bump, guard and `check.py`. **Fix:** "exact tag name, including `v`; resolved with `^{}`."
- **L6.** If module-agent tokens carry Actions or Variables write, agents can dispatch `release.yml` outside the night or flip the kill switch. This breaks the SPEC rule that a release starts only from the scheduler's dispatch. **Fix:** AD-7 states that module-agent tokens have no Actions, Variables or Secrets write.
- **L7.** If the CodeQL language set includes `actions`, a high alert in a *rendered* caller blocks all 17 releases, and the fix lives in CiCd. **Fix:** the gate excludes the `actions` language, or CiCd CI runs that analysis on the templates.
- **L8.** Stories 2, 3 and 27 push `.github/workflows/**` in Builds, but AD-7 never says the CiCd-agent token has Workflows write on Builds. **Fix:** state it.
