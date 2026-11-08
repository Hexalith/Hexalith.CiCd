---
reviewer: adversary
pass: 2
lens: construct two units one level down (stories in spec-cicd/stories.yaml, built by agents that read only the spine and their story) that each obey every AD to the letter yet build incompatibly
target: ../ARCHITECTURE-SPINE.md (revised draft, updated 2026-11-07)
previous: review-adversary.md
date: 2026-11-07
---

# Adversarial review, pass 2: Hexalith.CiCd architecture spine

## Verdict

The revision closes most first-pass holes. It also adds two new cross-repo contracts and gives neither an owner:
- `perimeter.json` has no schema, no closed set of entry kinds and no version, yet pinned Builds code reads it from CiCd `main` at run time.
- The first Builds release under the new pipeline has no owned path.

Most of the new High holes come from one cause. Validate-gated delivery, the bump and the guard each read "CiCd state" at a different moment, and nothing ties those moments together.

## Pass-1 status

| Item | Status | Residual |
| --- | --- | --- |
| C1 Builds spoke or hub | Closed (AD-19) | Builds' release has no config source (H6), and the bootstrap is unowned (C2) |
| C2 Nobody deletes | Closed (AD-6 step 2, AD-8 restore) | Delivery and the guard judge "unrendered" with different code and different wording (M9) |
| H1 Interface contract | Mostly closed (`hexalith-ci.json`, AD-10 public API, validate against the pinned tag) | Release outputs and the `publish` hand-off are unnamed (M4) |
| H2 Concurrency | Closed for module CI and release | Open for `deliver.yml`, which is both top-level and reusable (H2) |
| H3 "Head of main" | Closed (AD-16 pinned SHA, bump after releases) | When a draft is completed, the gates and the build cover different SHAs (M3) |
| H4 Rollback undone | Closed (`builds-skip`) | Rollback against newer knobs, and the bump racing a rollback (M6) |
| H5 Delivery unowned and invoked three ways | Partly open | Delivery is now invoked four ways. The nightly `workflow_call` delivers the pre-bump commit (H2). |
| H6 Migration credential | Closed (AD-21, precedence row) | Sequencing holes: H4, H5 |
| H7 Rewriting Builds `main` | Partly open | The freeze covers only files that `domain-*` reference, while modules call other files at `@main` directly (H7) |
| H8 Perimeter shape | Partly open | `perimeter.json` exists but has no schema, owner or version (C1) |
| H9 Local check inputs | Closed (`hexalith-ci.json`, repo-relative `.csproj` path) | — |

## Grounding checks (run against `references/` and the GitHub API)

- **Builds `main` ruleset `Protect main` is active.** Its rules are `deletion`, `non_fast_forward`, `pull_request` (squash only) and `required_status_checks`. The required checks are Codacy, SonarCloud and `commitlint / commitlint`, which comes from `commitlint-caller.yml`.
- **Builds' repo variables.** The only one is `NUGET_USER`. There is no `HEXALITH_RELEASE_PUBLISH_ENABLED`.
- **Builds' environment `production`** has required reviewers and a branch policy.
- **Builds' current release is `build-release.yml`, not `builds-release.yml`.**
  - Its green check, `Tools/verify-g4-release-source.sh`, hard-codes `actions/workflows/ci.yml/runs` and `.path == ".github/workflows/ci.yml"`. `Tools/G4PackageQualification.functions.ps1` does the same.
  - It runs under `environment: production`.
- **Module `@main` references to Builds files that no `domain-*` workflow references:**
  - `Github/initialize-dotnet@main` ×18
  - `dependency-review.yml@main` ×11
  - `codeql.yml@main` ×10
  - `commitlint.yml@main` ×10
  - `Github/verify@main` ×1
- **Every legacy module `release.yml` has `workflow_dispatch`, and every one uses `@semantic-release/git`.** That plugin commits to `main` and pushes the tag before publishing.
- **AI.Tools** contains only Markdown, JSON and one `.mjs` file. It has no C#.
- **Builds' current `ci.yml`** sets `cancel-in-progress: true` for every ref.

## Tier counts

| Tier | Count |
| --- | --- |
| Critical | 2 |
| High | 7 |
| Medium | 10 |
| Low | 10 |

---

## Critical

### C1. `perimeter.json` is an unowned, unversioned cross-repo format that pinned code reads at run time

- **Units:**
  - Story 4 (`render.py` emits `rendered/<Repo>.perimeter.json`, and `deliver.py` applies it, in CiCd).
  - Story 5 (the guard and restore parse it, in Builds).
  - Story 2 is a third producer: the hand-written fixture perimeter behind `expected-source` (AD-19).
- **Each obeys:**
  - AD-4 says the render emits "whole files, partial entries, absent globs rooted at the repo root, and the gitlink as `{path, tag}`", and that all three consumers read it.
  - AD-10's public API lists `schemas/hexalith-ci.v1.json` and not the perimeter format.
  - Each agent therefore invents a shape. Story 4 writes `{"whole": [...], "absent": [...], "gitlink": {...}}`. Story 5 parses `{"entries": [{"kind": ..., "path": ...}]}`.
- **Clash:**
  - **Day one.** Every module's guard fails to parse CiCd's perimeter. No module can be adopted until one repo is reworked.
  - **Partial entries have no defined home for their expected content.** The AD-4 table needs at least nine distinct operations:
    - the whole `.github/workflows/` directory;
    - whole files;
    - the gitlink;
    - the `.gitmodules` section;
    - the JSON superset in `.claude/settings.json`;
    - three marker blocks;
    - absent globs;
    - absent JSON keys and dependency-name globs in `package.json`;
    - an absent line in `.husky/commit-msg`.

    Two agents will not partition these the same way. Nothing says where the block text and deny entries live. `rendered/<Repo>/AGENTS.md` would read as a whole file.
  - **Ongoing.** The guard runs at the module's pinned tag but reads the perimeter from CiCd `main` at run time (AD-8). Any later `render.py` change to the format breaks the guard in all 17 modules at once:
    - no Builds release is involved;
    - `builds-skip` cannot roll it back;
    - validate does not catch it, because validate checks the render, not what pinned guards can parse.

    This is exactly what AD-1 prevents ("a SHA's CI result depending on CiCd's state at run time"), entering through the one door AD-1 leaves open.
- **Fix (tighten AD-4, add to the AD-10 public API):**
  - The perimeter format is Builds' `schemas/hexalith-perimeter.v1.json`, public API under AD-10.
  - The entry kinds are closed:
    - `whole` (path);
    - `whole-dir` (path; every file at any depth);
    - `gitlink` (path, tag);
    - `gitmodules-section` (name, path, url);
    - `json-superset` (file, JSON pointer, values);
    - `marker-block` (file, begin, end, text);
    - `absent-glob` (git wildmatch, rooted);
    - `absent-json` (file, keys, dependency globs);
    - `absent-line` (file, regex).
  - Partial-entry text is inline in the perimeter. Whole-file content is `rendered/<Repo>/<path>`.
  - `render.py` writes `"format": 1`.
  - Validate checks every perimeter, and Builds' fixture perimeter, against the schema at `builds-version`.
  - The guard fails with a fixed message on an unknown `format` or kind. A format change is a Builds major, adopted per AD-10.

### C2. No owned path to a Builds release, so no tag exists for anything to pin

- **Units:**
  - Story 2 (renames `ci.yml` to `builds-ci.yml`, per AD-20).
  - Builds' legacy `build-release.yml` (unowned; not frozen by AD-20).
  - `builds-release.yml` (AD-19 names the file, but no story owns it; story 3 is the reusable release and story 8 is the scheduler).
  - Story 4 (validates setup files "against Builds' `schemas/hexalith-ci.v1.json` at the pinned tag").
  - AD-21 maintainer preconditions (scoped to modules; Builds is never onboarded).
- **Each obeys:**
  - Story 2 renames as AD-20 orders.
  - Story 3 makes "unset kill switch fails red" the first step, as AD-17 orders.
  - Story 4 validates at the pinned tag.
  - No AD gives Builds any preconditions.
- **Clash:**
  - **Builds `main` refuses every push from stories 2, 3, 5, 6 and 27.** It requires a PR plus the Codacy, SonarCloud and `commitlint / commitlint` checks. The CiCd-agent token has no Pull requests write (AD-7). If story 5 retires `commitlint-caller.yml` because "commitlint moves into the guard", the required `commitlint / commitlint` check never reports again, and Builds PRs can never merge.
  - **The rename kills Builds' only working release path.** `verify-g4-release-source.sh` looks for push runs of `.github/workflows/ci.yml`. Once the reusable, `workflow_call`-only `ci.yml` takes that name, it has no push runs.
  - **The new path cannot succeed either:**
    - `builds-release.yml` fails with "HEXALITH_RELEASE_PUBLISH_ENABLED is not set" because Builds has only `NUGET_USER`.
    - The nuget.org policy names `build-release.yml` under environment `production`, so `NuGet/login` fails from `builds-release.yml`, which has no environment.
    - `HEXALITH_NUGET_USER` is "restricted to the managed repos", which may exclude Builds.
  - **The dependency loop.** Story 4's validate needs a tag that contains `schemas/hexalith-ci.v1.json`. That tag can only come from the path above, and nothing seeds `builds-version`. Every migration story (11–26) waits on it.
- **Fix (add an AD-19 bullet and amend AD-20):**
  - **Builds preconditions (maintainer, before story 2):**
    - cut `Protect main` to deletion and non-fast-forward;
    - set `HEXALITH_RELEASE_PUBLISH_ENABLED=true` on Builds;
    - give Builds access to `HEXALITH_NUGET_USER`;
    - add a nuget.org policy for `builds-release.yml` with no environment.
  - **Ownership.** Story 3 owns `builds-release.yml` and lands it with the reusable `release.yml` and `publish`.
  - **The rename commit** (story 2) also points `build-release.yml` and its `Tools/` checks at `builds-ci.yml`. Story 3 deletes `build-release.yml` once `builds-release.yml` has produced a tag.
  - **Until story 8,** a CiCd agent dispatches `builds-release.yml` by hand.
  - **Seeding.** Story 4 sets `builds-version` to the first tag that contains `schemas/hexalith-ci.v1.json`.

---

## High

### H1. Validate gates delivery but not the guard: CiCd `main` is every module's expected state before validation

- **Units:** Story 5 (the guard and restore read "by shallow sparse git clone of CiCd `main`", AD-8) against Story 4 (`deliver` runs "only after `validate` succeeds", AD-6) and Story 8 (the bump commit lands on `main` before its delivery validates it).
- **Each obeys:** AD-8 and AD-6 as written.
- **Clash:**
  - CiCd agents push straight to `main` (AD-5), and validate runs after the commit has landed.
  - A template commit that fails actionlint or zizmor, or a bump to a tag whose interface does not match the templates, becomes the guard's expected state in all 17 modules at once:
    - every module push fails the guard with workflow drift;
    - restore writes the unvalidated non-workflow parts into modules (`hexalith-ci.json`, deny entries, instruction blocks).

    Delivery, the only validated writer, is meanwhile refused.
  - "A red build means the product is broken" fails org-wide until a human repairs CiCd. Restore has become an unvalidated write path that bypasses AD-6.
- **Fix (amend AD-6 and AD-8):**
  - After `validate` passes, the `deliver` job fast-forwards the CiCd branch `delivered` to the validated commit with the App token, before pushing any module. A ruleset lets only the App move it.
  - The guard, restore and `check.py` read the perimeter and expected files from `delivered`, never from `main`.

### H2. The nightly `workflow_call` delivery delivers the pre-bump commit and races the bump's own delivery

- **Units:** Story 8 / Story 7 (nightly commits the bump, then calls `deliver.yml`, per AD-18) against Story 4 (`deliver.yml` with push, hourly, `workflow_call` and dispatch triggers, AD-6).
- **Each obeys:**
  - **Story 8.** It runs `uses: ./.github/workflows/deliver.yml` after the bump job pushes commit B.
  - **Story 4.** It checks out `github.sha`, the default.
- **Clash:**
  - **The called run delivers the wrong commit.** A called workflow runs at the caller's `github.sha`, which is commit A, the CiCd `main` at 02:17, before the bump.
  - **Two deliveries race.** The App push of B also triggers a `push` run of `deliver.yml` (App pushes trigger workflows, per the memlog).
    1. The push run delivers T2.
    2. The nightly-called run (A) then validates A cleanly, finds a diff in every module, and pushes T1 back.
    3. The next hourly run restores T2.

    On every bump night each module flips T1 → T2 → T1 → T2, with three module CI runs. In between, the guard (reading B) and restore fight the T1 state. AD-6's "prevents stale renders written back after a race" fails.
  - **Concurrency cannot be placed.** The conventions say concurrency is "declared only in top-level workflows, never in reusable ones", but `deliver.yml` is both.
    - If it declares `deliver`, the nightly-called run can be the pending run that a newer hourly run supersedes. Nightly then goes red with nothing broken.
    - If it does not, push, hourly and dispatch deliveries overlap.
- **Fix (AD-6, AD-18):**
  - `deliver.yml` has no `workflow_call` trigger. It is top-level only, with `concurrency: {group: deliver, cancel-in-progress: false}`.
  - The bump commit's App push triggers delivery.
  - Nightly waits for the first `deliver.yml` run on `main` whose `head_sha` is the bump commit or a descendant, and reports that run's conclusion in its summary.

### H3. The Builds bump is gated on every module release (and the duplicate scan) succeeding

- **Units:**
  - Story 8 ("It fails if any run failed. … Only then does it bump", AD-18).
  - Story 7 (the bump).
  - Story 9 (the duplicate scan, which "fails this repository's nightly run", enforcement.md; AD-18 does not place it).
- **Each obeys:**
  - Story 8 exits non-zero after the summary, and the next step (the bump) is skipped by default.
  - Story 9 adds the scan as a step before the bump.
- **Clash:**
  - 9 of 15 repos fail CI 60–100% of the time today, and any red `main` gives "main is red, nothing released", which is a failed run.
  - One red module, or one duplicate fragment, therefore blocks the bump for all 17 modules, night after night. CAP-6 ("within one night of a Builds release, all modules reference it") fails as the normal case.
  - Modules released on the old tag, so their failures say nothing about the new tag.
- **Fix (AD-18):**
  - The bump runs after the wait, whatever the release conclusions. It is a no-op when no newer tag exists.
  - The duplicate scan is its own job, which the bump never `needs`.
  - Release and scan failures set the run's conclusion only at the end.

### H4. One module's live state blocks delivery to all modules

- **Units:** Story 4 (validate fails "when an action named by `hooks`, `jobs` or `tests.exclude` is missing on the module's live `main`" or "an AD-21 precondition … is unmet", AD-3; delivery runs only after validate succeeds, AD-6) against module agents (`.github/actions/**` is module-owned and never restored, AD-4 and AD-14) and Story 8 (the bump delivery).
- **Each obeys:** A module agent renames `.github/actions/after-unit-tests` in Folders, which its token allows. Validate correctly fails.
- **Clash:**
  - Validate is one gate for all 17 modules, so delivery stops everywhere:
    - no workflow-drift repair, which is the only control for the org-wide agent Apps (AD-7);
    - no bump;
    - no onboarding.
  - The same happens when a maintainer toggles one precondition in one repo, and on every onboarding whose preconditions are not done yet (AD-21 step 3).
- **Fix (AD-3 and AD-6):**
  - Validate has two parts:
    - **Global checks** (render with no diff, schemas, tool tests, actionlint, zizmor) block every delivery.
    - **Per-module checks** (submodule, installation, actions on live `main`, preconditions) block only that module. Delivery skips it, delivers the others, and the run fails naming it.
  - Nightly does not dispatch a module that fails its per-module checks.

### H5. Nightly dispatches the legacy `release.yml` of modules that are listed but not yet adopted

- **Units:** Story 8 (dispatches "every module's `release.yml`" from `setup/*.yml`, per AD-3 and AD-18) against AD-21 step 3 and stories 11–26 (the setup file lands first, then delivery adopts).
- **Each obeys:** The CiCd agent commits the setup file and the render. Validate fails on an unmet precondition, which is the case AD-21 step 3 expects (and H4 makes it block delivery). Nightly enumerates `setup/*.yml` at 02:17.
- **Clash:**
  - Every legacy module `release.yml` has `workflow_dispatch` and uses `@semantic-release/git`.
  - Nightly therefore runs the legacy release under the scheduler. It commits a CHANGELOG to `main` and pushes the tag before publishing. That is the partial-release pattern that `recover-partial-release.yml` exists for.
  - Adoption then deletes the recovery workflow. The new state machine (AD-17) treats the orphan tag as released and computes the next version past it, so that version's packages are never published.
  - AD-21's preconditions cover drafts and CodeQL but not orphan tags.
- **Fix (AD-18 and AD-21):**
  - Nightly dispatches a module's `release.yml` only when the module's live `main` has `.github/workflows/release.yml` and `.github/hexalith-ci.json` equal to the render at `delivered`. Otherwise it reports the module as "not adopted" (failed) and dispatches nothing.
  - AD-21 step 1 adds: no legacy release is in progress or partial. Every `v*` tag has a published GitHub release and its packages; the maintainer completes it by hand or deletes the tag.

### H6. Builds' release has no configuration source

- **Units:** Story 3 (the reusable `release.yml` reads `solution`, `codeql`, `hooks` and `registry` from `.github/hexalith-ci.json` in the checkout, AD-1) against `builds-release.yml` and AD-19 (Builds is "never rendered"; callers carry only `uses:` and job structure).
- **Each obeys:**
  - Story 3 reads the file AD-1 names.
  - `builds-release.yml` passes only `ci-workflow` and `release-rules`, as AD-19 says.
- **Clash:**
  - Builds has no `.github/hexalith-ci.json`.
  - The reusable release has three options, each of which breaks an AD:
    - fail;
    - guess `solution` (Builds has `Hexalith.Builds.slnx`);
    - read `Samples/`'s config, which would publish the sample.
  - CodeQL languages for Builds (C# and Python) are undefined.
  - If the schema requires `builds_tag`, any hand-written file needs a meaningless tag.
- **Fix (AD-19):**
  - Builds commits a hand-written `.github/hexalith-ci.json`: `solution: Hexalith.Builds.slnx`, `codeql: [csharp, python]`, no `hooks`, no `builds_tag`.
  - The schema makes `builds_tag` optional. Only the guard and `check.py` require it.
  - `builds-ci.yml` validates this file against the schema at the same commit.

### H7. The legacy freeze still leaves the files modules call at `@main` unprotected (pass-1 H7 residual)

- **Units:** Stories 2, 3 and 5 against unmigrated modules waiting on stories 13–26.
- **Each obeys:** AD-20 freezes `domain-ci*.yml`, `domain-release.yml` "and every composite, action and script they reference".
  - Story 2 reworks `Github/initialize-dotnet`. Builds' own CI already uses it, and the inventory says composites are "reviewed against the new workflows".
  - Story 3 folds `codeql.yml` into the nightly job.
  - Story 5 retires `commitlint.yml` and `commitlint-caller.yml`.
  - Some story drops `dependency-review.yml`.
- **Clash:**
  - None of those files is referenced from `domain-*`, but modules call them directly at `@main`:
    - `initialize-dotnet` ×18;
    - `dependency-review.yml` ×11;
    - `codeql.yml` ×10;
    - `commitlint.yml` ×10;
    - `verify` ×1.
  - Each change breaks up to 16 repos the moment it lands, which is exactly the failure H7 described.
- **Fix (AD-20):**
  - Until story 27, no file that exists today under Builds' `.github/workflows/` or `Github/` is modified or deleted.
  - The exceptions are the `ci.yml` rename and the `build-release.yml` hand-over (C2).
  - The test is "exists today", not "referenced from `domain-*`".

---

## Medium

### M1. Restore moves part of the lockstep set
- **Units:** Story 5 (restore "applies the perimeter to everything except `.github/workflows/**`", AD-8) against AD-10 lockstep (callers, `hexalith-ci.json` and the gitlink "all moved together by delivery"), Story 4 (delivery) and Story 6 (`check.py`).
- **Clash:**
  - In the bump window, or for as long as delivery is blocked (H1, H4), any module push to `main` makes restore write `builds_tag: T2`, the gitlink and the `.gitmodules` section, while the callers stay at `@T1`.
  - `check.py` then passes its own consistency check (gitlink equals `builds_tag`) and runs T2's guard, while CI runs T1's guard. That is two Builds versions, which AD-9 prevents, and CAP-3 diverges.
  - The AD-9 fallback would check out T2 inside a T1 run.
- **Fix (AD-8):** Restore never writes the gitlink, the `.gitmodules` section or `.github/hexalith-ci.json` when the perimeter's tag differs from the tag the running workflow was called at. Like `.github/workflows/**`, those wait for delivery.

### M2. The release outcome cannot be read by the nightly summary
- **Units:** Story 3 (the reusable release ends `success` for released, nothing to release and publishing disabled) against Story 8 (the summary must tell success, nothing to release, publishing disabled and failed apart, AD-18).
- **Clash:**
  - All three non-failure outcomes have conclusion `success`.
  - Story 3 prints the fixed messages to the log or the step summary. The REST API exposes neither, so Story 8 cannot classify the outcome.
  - The alternative is inferring it from job or step names, which breaks on the next Builds minor.
- **Fix (AD-17 and AD-18):**
  - The `release` job ends with exactly one annotation, `hexalith-release: released v<version> | nothing to release | publishing disabled`.
  - `nightly.py` reads it through the check-run annotations API.
  - A successful run without that annotation counts as failed.
  - The annotation is public API (AD-10).

### M3. Completing a draft: the gates cover `github.sha`, the build covers the draft's SHA
- **Units:** Story 3's `codeql`, `nightly-hook` and green-check jobs (AD-16: "the release SHA is `github.sha` … never re-resolved") against Story 3's draft step (AD-17 step 4: "use its version and SHA") and Story 17 (Folders' `nightly` custom action, which assumes the workspace is what ships).
- **Clash:**
  - When last night's draft (SHA S0) is completed, CodeQL, the nightly hook and the green check vouch for tonight's head, while S0 is built and shipped.
  - A draft whose S0 now fails the NU1903/NU1904 audit fails every night, forever, and blocks all later releases. Only a hand-run recovery can clear it, which CAP-12 forbids.
- **Fix (AD-16 and AD-17):**
  - The kill-switch job also resolves the release SHA: the marked draft's SHA if one exists, otherwise `github.sha`. It outputs that SHA.
  - `codeql`, `nightly-hook`, the green check and the build all use it.
  - A draft whose build fails the audit is deleted when no package of its version is on nuget.org. Otherwise the run fails with a fixed message.

### M4. The release-to-publish hand-off is undefined beyond `publish`
- **Units:** Story 3 (reusable release outputs; the `publish` composite) against Story 4 (the caller template wires `needs.release.outputs.*` into `publish` with `with:`).
- **Clash:**
  - AD-17 names only the `publish` output. The version, the draft id, the release SHA and the artifact name are left to each side.
  - The publish job is "one step", so the composite cannot read `hexalith-ci.json` without its own checkout.
  - Containers built in the `release` job cannot reach the publish job's VM unless they are exported. Story 3 may expect a Docker daemon image while Story 4 renders no registry secrets into `publish`.
- **Fix (AD-17, public API under AD-10):**
  - The reusable release outputs `publish`, `version`, `sha`, `draft-id` and `artifact`.
  - The artifact holds `packages/*.nupkg` and `containers/*.tar` (OCI archives written by the `release` job).
  - The `publish` composite takes those outputs plus `nuget-user`, `registry-username` and `registry-password`, and never checks out the repo.

### M5. The bump commit is not covered by the render-with-commit rule
- **Units:** Story 7 / Story 8 (`nightly.py` "bump `builds-version` … commit", AD-18) against Story 4 (validate "re-renders and fails on any diff", AD-5 and AD-6).
- **Clash:**
  - AD-5's rule binds whoever changes `setup/` or `templates/`, and `builds-version` is neither.
  - A bump that commits only `builds-version` fails validate, and the bump is never delivered.
- **Fix (AD-5):** The rule also covers `builds-version`. The bump commit holds `builds-version` and the full re-render from `tools/render.py`.

### M6. Rollback against newer knobs, and the bump racing a rollback
- **Units:** Story 7 (a rollback sets the older tag and adds the bad tag to `builds-skip`, AD-10) against Story 4 (validate against the schema "at the pinned tag", AD-3) and against Story 8 (the nightly bump commits to CiCd `main`).
- **Clash:**
  - **Knobs.** Setup files adopted a knob added in T2, so the rollback commit to T1 fails validate (unknown keys fail). The rollback cannot be delivered.
  - **Race.** Nightly's bump push is not a fast-forward because an agent's rollback commit landed first. AD-6's re-fetch rule covers module pushes only. Nightly rebases or re-applies its precomputed tag, and bumps straight to the tag the rollback just skipped.
- **Fix (AD-10 and AD-18):**
  - A rollback commit also removes the setup keys that the older tag's schema lacks. Validate names them.
  - On a non-fast-forward, the nightly bump and the keepalive re-fetch CiCd `main` and recompute from its `builds-version` and `builds-skip`, at most 3 times. They never rebase.

### M7. `solution: none` with the default `codeql: [csharp]` turns AI.Tools' release red every night
- **Units:** Story 3 (the `codeql` job takes "languages from `codeql`", default `[csharp]`, AD-3 and AD-18) against Story 12 (AI.Tools: Markdown only, `solution: none`).
- **Clash:**
  - A C# analysis of a repo with no C# fails, so AI.Tools' release fails red every night.
  - AD-3 does not say whether an empty `codeql` is valid. A schema with `minItems: 1` makes the AI.Tools release impossible.
  - If the empty case skips the job, `needs: [codeql, nightly-hook]` with a skipped job skips the release job by default.
- **Fix (AD-3 and AD-18):**
  - `codeql: []` is valid and skips the job. With `solution: none` the default is `[]`.
  - The release steps run when `codeql` and `nightly-hook` each either succeeded or were skipped.

### M8. In Builds' self-test, the guard and the hook steps look for actions in different places
- **Units:** Story 2 (`module-root` re-roots the sample, and hooks are literal `uses: ./.github/actions/<hook>`, which always resolve at the workspace root) against Story 5 (the guard checks "every enabled hook and job action exists", naturally under `<module-root>/.github/actions/`).
- **Clash:**
  - If the sample's actions live under `Samples/<m>/.github/actions/`, the hook step fails with "can't find action.yml".
  - If they live at Builds' root `.github/actions/`, the guard reports them missing.
  - Either way the self-test skips or bends the hook path. CAP-15 loses exactly what AD-19 claims to protect.
- **Fix (AD-19):**
  - `module-root` re-roots only `solution`, `hexalith-ci.json`, the perimeter and the gitlink.
  - Hook and job actions always resolve at the workspace root, and the guard checks them there.
  - Builds keeps the sample's actions in its own root `.github/actions/`.

### M9. Delivery and the guard judge "drift" with different code and different wording
- **Units:** Story 4 (`deliver.py`: "delete unrendered workflow files", AD-6 step 2) against Story 5 (the guard: under `.github/workflows/`, "an unrendered file is drift", AD-4).
- **Clash:**
  - `deliver.py` deletes only `*.yml` and `*.yaml`, while the guard flags `.github/workflows/README.md` or a subdirectory. The same split applies to absent-glob dialects: fnmatch, pathlib and git wildmatch differ on `**` and dotfiles.
  - Delivery sees no diff and pushes nothing. Restore never touches workflows. The module stays red with no repair path, which is C2 of pass 1 entering again through the side.
- **Fix (AD-6):**
  - Delivery decides "no diff" by running the Builds guard at `builds-version` on its applied clone, with the guard in perimeter-only mode against the local render.
  - AD-4's "file" (any file at any depth) governs.

### M10. The kill-switch values change meaning at adoption
- **Units:** Story 3 (unset fails red, `false` disables, AD-17) against the legacy state that AD-21 step 1 inherits.
- **Clash:**
  - Legacy releases treat anything other than exactly `true` as frozen.
  - The new rule enables every value except `false`. A module the maintainer froze with `0`, `no` or `frozen` starts publishing the night it is adopted.
- **Fix (AD-17 and AD-21):**
  - Exactly `true` enables and exactly `false` disables.
  - Any other value, including unset, fails red with the fixed message.
  - The maintainer sets exactly one of the two.

---

## Low

- **L1. Hourly delivery at :17 collides with nightly at 02:17.**
  - Units: Story 4 against Story 8.
  - A drift-repair commit pushed at 02:17 becomes the pinned release SHA. Its CI queues behind about 90 release jobs under the 20-job limit, the 30-minute wait expires, and the release reports "main is red" with nothing broken.
  - Fix: nightly runs at 02:47.
- **L2. Non-`main` branch pushes are compared against the current CiCd state.**
  - Units: Story 5 against Story 4.
  - Any branch cut before the last delivery fails the guard without touching an owned file. PRs are safe, because their merge commit carries the new files.
  - Fix: on non-`main` pushes, the guard fails only for owned paths changed in `merge-base(main)..HEAD`.
- **L3. `check.py` has no commitlint range.**
  - Units: Story 6 against Story 5.
  - If it lints only `HEAD` while CI lints `before..after`, a local pass can be followed by a CI fail (CAP-3).
  - Fix: `check.py` lints `@{upstream}..HEAD`, or `origin/main..HEAD` when there is no upstream.
- **L4. The renamed `builds-ci.yml` keeps `cancel-in-progress: true` on `main`.**
  - Units: Story 2 against Story 3 / AD-16.
  - Rapid Builds commits end `cancelled`, which is never green.
  - Fix: AD-20's rename also applies the conventions' CI concurrency.
- **L5. The registry login before hooks hands hook actions the Zot credential.**
  - Units: AD-12 (Story 2) against AD-14 ("no secrets"; the deny list in Story 5).
  - The login is in `~/.docker/config.json`, which the hook can read.
  - Fix: AD-14 says "no secrets except the registry login when `registry` is set", or the login comes after the hooks.
- **L6. `builds_tag` and the setup-file validation.**
  - Units: Story 2 (schema) against Story 4 (setup "validated against" the same schema).
  - If `builds_tag` is required, every setup file fails validation.
  - Fix: covered by H6's "optional in the schema", and validate checks the setup file with `builds_tag` injected.
- **L7. Story 7 has no deliverable left, and Stories 7 and 8 both edit `nightly.yml`.**
  - After the precedence row, the two stories can each build a bump step.
  - Fix: Story 7 owns `tools/bump.py` and the `builds-skip` handling. Story 8 owns `nightly.yml` and calls it.
- **L8. Render determinism.**
  - Units: Story 4 (Dependabot ecosystems are "owned by the generator story", with no knob) against AD-5.
  - If `render.py` derives ecosystems from the module's live `main` (AD-3 allows reading it), validate flaps whenever a module changes, and H4 turns that into a global block.
  - Fix: the render reads only `setup/`, `templates/` and `builds-version`.
- **L9. The AD-9 fallback inside Builds' self-test.**
  - Units: Story 2's fallback against AD-19.
  - The fallback checks out `builds_tag`, an old release, so the self-test tests old code.
  - Fix: the fallback uses `github.workflow_sha` whenever `module-root` is set.
- **L10. Leftover npm files after delivery.**
  - Units: Story 4 (removes the keys and dependencies from `package.json`) against the rendered `dependabot.yml`.
  - Every module's `package.json` is tool-only today. Delivery leaves an empty `package.json`, a stale `package-lock.json` and a `.husky/` directory, and an `npm` Dependabot ecosystem would keep updating them.
  - Fix: AD-4 restores the memlog rule. A tool-only `package.json`, its lockfile and `.husky/` must be absent.
