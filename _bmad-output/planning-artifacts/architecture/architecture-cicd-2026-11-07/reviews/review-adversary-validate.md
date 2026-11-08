---
reviewer: adversary
pass: validate
lens: construct two units one level down (stories in spec-cicd/stories.yaml, or a story against existing code) that each obey every AD to the letter yet build incompatibly — clashing shared-data shapes, two owners of one entity, conflicting state-mutation paths
target: ../ARCHITECTURE-SPINE.md (status final, updated 2026-11-08, 21 ADs)
spec: ../../../../specs/spec-cicd/ (HEAD 4666c3d)
previous: review-adversary.md, review-adversary-pass2.md, review-adversary-pass3.md
date: 2026-11-08
---

# Adversarial review, validation gate: Hexalith.CiCd architecture spine

## Verdict

**Fails the gate.** A release that fails after creating its draft can never be completed once its module's delivered render changes, and a bump changes it nearly every night (A-1). Four high holes sit in shared release and delivery state (A-2 to A-4), so tightened ADs must land before stories 3, 5, 7 and 8 are built.

| Severity | Count | IDs |
| --- | --- | --- |
| Critical | 1 | A-1 |
| High | 3 | A-2, A-3, A-4 |
| Medium | 9 | A-5 to A-13 |
| Low | 9 | A-14 to A-22 |

All pass-3 adversary items (H1–H3, M1–M6, L1–L7) are closed by the current text. Three older items remain open and are marked below: pass-2 H2 (in part, A-5), pass-2 M8 (A-12) and pass-2 L2/L10 (A-21, A-22).

Line references are to `ARCHITECTURE-SPINE.md` unless another file is named.

---

## Critical

### A-1 (critical): A partly published release deadlocks its module once the delivered render moves

- **Location:** AD-16 (line 328), AD-17 steps 1, 5 and 6 (lines 344, 348–350), AD-18 Bump (line 370), AD-4 loader (line 134).
- **Units:**
  - **Story 3:** the draft state machine. The release SHA is the marked draft's SHA, and every gate and the build use it.
  - **Story 5:** the release drift check against `delivered/<Repo>`.
  - **Story 8:** the bump "whatever their results".
  - **Story 7:** delivery advances `delivered/<Repo>`.
- **Each obeys:**
  - AD-16: "the SHA of the marked draft if one exists … Every gate and the build use it, and it is never re-resolved." (line 328)
  - AD-17 step 1: "re-run the guard check on it against the module's `delivered/<Repo>`. Drift fails red." (line 344)
  - AD-18: "whatever their results, it bumps `builds-version` (AD-10), re-renders, and pushes" (line 370).
  - AD-4: the loader "rejects unknown and missing keys" (line 134).
- **Scenario:**
  1. **Night N.** Module X's release resolves S0, creates the marked draft vX.Y.Z and builds. Then the caller's `publish` job fails partway (a Zot outage, a transient NuGet push or OIDC error), after some packages were pushed. The draft remains.
  2. **Same night.** Nightly bumps T1 to T2, as it must "whatever their results". Delivery advances `delivered/X` to the T2 render and pushes the bump commit to X.
  3. **Night N+1.** The release SHA is S0, because the draft takes precedence. The drift check compares S0 with `delivered/X`. S0 carries the T1 callers, `buildsTag` and gitlink, and the delivered render is T2, so it fails red.
  4. **Every later night:** the same. S0 never matches again.
  5. **Second break on the same path.** Even if the drift check passed, the running T2 loader reads S0's T1-rendered `hexalith-ci.json`. If T2 added an optional knob (a minor, per AD-3), the loader rejects the missing key and the rebuild never starts.
  6. **Manual "Re-run" of night N's run.** It reuses `github.sha` S0 and the T1 workflow, but the drift check reads the live ref, which is now T2. It fails too.
- **Evidence:**
  - Builds published about 40 releases in the last 31 days (`gh api repos/Hexalith/Hexalith.Builds/releases`), and `pipeline-stages.md:84` says it "released 44 times last month". So a bump follows almost every night.
  - Any setup or template change for X between two nights has the same effect, even without a bump.
- **Failure:**
  - X never releases again, and nightly is red every night.
  - The only way out is a human deleting the draft. The next run then recomputes the same vX.Y.Z (no tag was created) from the new head, and `dotnet nuget push --skip-duplicate` (line 354) keeps S0's already-pushed packages beside the new ones. That is a mixed-content version, which `SPEC.md:102` forbids: "A version is never republished from different content."
  - CAP-12's "Rerunning a failed release finishes it" fails exactly in the case it exists for.
- **Fix (AD-17: new bullet after step 5; amend AD-16):**

  > **Completing a draft.**
  > - The run that creates a marked draft also writes the trailer `hexalith-release-run: <run-id>` into its body.
  > - A run that finds a marked draft completes it from that run's `release` artifact:
  >   - it runs no drift check and no green-CI check;
  >   - it loads no `hexalith-ci.json` at the draft's SHA, and builds nothing.
  > - `codeql` and `nightly-hook` still run on `github.sha` and gate the completion as in step 2. The kill switch applies.
  > - If the artifact has expired, the draft is deleted when no package of its version exists on nuget.org. Otherwise the run fails with "draft vX.Y.Z cannot be completed: its build artifact expired".
  > - `release` artifacts are kept 90 days.
  >
  > AD-16: "When a marked draft exists, its SHA identifies what is published. The gates ran in the run that created the draft."

  - **Rejected alternative:** record the delivered commit in the draft and compare against it. That still leaves the loader rejecting S0's older `hexalith-ci.json`, and it still rebuilds.

---

## High

### A-2 (high): `outcome.json` has no single writer, and AD-17 puts `published` in a job that cannot know it

- **Location:** AD-17 module `release.yml` (lines 339–342), outputs (line 351), `publish` composite (lines 352–356), Outcome (line 360); AD-18 Wait and report (lines 369, 371); Deferred (line 582).
- **Units:**
  - **Story 3:** the reusable release and the `publish` composite.
  - **Story 4:** the rendered caller `release.yml`, with jobs `release` and `publish`.
  - **Story 8:** nightly reads the outcome.
- **Each obeys:**
  - AD-17 places "**Outcome.** Every run uploads the artifact `hexalith-release-outcome` … `published`, `ready` (draft complete except publication), `nothing`, `disabled` or `failed`" under the reusable `release.yml` (line 360).
  - The `publish` composite "takes those outputs plus the NuGet user and the registry push pair" and has no outcome duty (line 352).
  - AD-18: "without a readable outcome, counts as `failed`. It reads each run's outcome" (line 369).
- **Clash:**
  - **The success path can only say `ready`.** The reusable workflow finishes before the caller's `publish` job starts, so it never knows whether publication worked.
  - **Story 8 has no rule for `ready` outside the fallback.** It can read it three ways, and each is wrong:
    - as the Deferred fallback signal (line 582): it tries to publish drafts that the `publish` job already published;
    - as success: a failed `publish` job (outcome `ready`, conclusion `failure`) reads as released, and the CAP-13 failure signal is lost;
    - as failure: nightly is red every night.
  - **A second writer breaks the run.** If story 3 also makes the `publish` composite upload `hexalith-release-outcome`, upload-artifact v4+ rejects a second artifact with the same name unless `overwrite: true`. The `publish` job then fails after the release has shipped.
  - **Some paths have no writer at all.**
    - When `codeql` fails, step 2 skips the release steps, and nothing says who writes `failed`. That needs an `if: always()` job.
    - Kill switch `false` together with a failed `codeql` is either `disabled` or `failed`.
- **Fix (AD-17 Outcome, AD-18 Wait and report):**

  > - The outcome is written once per run, by the last job that runs:
  >   - the caller's `publish` job writes `published` or `failed`, through the `publish` composite;
  >   - when `publish` does not run, a final reusable job (`if: always()`) writes `nothing`, `disabled`, `ready` (Deferred fallback only) or `failed`.
  >
  >   Each upload uses `overwrite: true`.
  > - The outcome is `failed` whenever any job of the run failed. It is `disabled` only when the kill switch is `false` and `codeql` and `nightly-hook` succeeded or were skipped.
  > - Nightly's verdict:
  >   - a conclusion other than `success` is failed, whatever the outcome;
  >   - `success` with `published`, `nothing` or `disabled` passes;
  >   - `ready` passes only under the Deferred fallback, where nightly then publishes the draft;
  >   - anything else is failed.

### A-3 (high): The draft's tag target is unfixed, so the tag can land on a different commit than the one built

- **Location:** AD-16 (line 328); AD-17 step 5 (line 348) and `publish` step 4 (line 356); Release markers convention (line 467); Deferred spike (line 582).
- **Units:**
  - **Story 3:** creates the draft, publishes it, and runs the spike "publishing a draft whose SHA is behind `main` with `GITHUB_TOKEN`".
  - **Story 8:** the fallback publication with the App.
  - **The next night's version computation** (story 3).
- **Each obeys:**
  - AD-17: "create the marked draft" and "Publish the draft, which creates `v<version>` last".
  - The convention fixes only the body trailer `hexalith-release: <sha>`.
  - Nothing fixes the draft's `target_commitish`. GitHub's create-release API defaults it to the default branch and uses it when the tag is created, which for a draft happens at publication.
- **Clash:**
  - **How the wrong target gets in.** Story 3 leaves `target_commitish` at its default, or sets it to `main`. Setting `main` is exactly what makes the spike's `GITHUB_TOKEN` refusal disappear (line 582), so the spike "confirms" the main path for the wrong reason.
  - **Where the tag lands.** Publication can happen an hour or more after dispatch, behind the 20-job queue. `v<version>` is then created at `main`'s head S1, while the packages were built from S0.
  - **What the next night computes.**
    - "the last `v*` tag reachable from the SHA" (line 348) is S1.
    - A `feat` or `fix(deps)` that landed in (S0, S1] is treated as released but was never shipped.
    - The tag no longer names the shipped source.
- **Failure:** a silent CAP-13 miss (`SPEC.md:108`), and a wrong basis for the CAP-13 fallback decision taken at story 8.
- **Fix (AD-17 step 5):**

  > - The marked draft's `tag_name` is `v<version>`. Its `target_commitish` is the full 40-character release SHA, equal to its `hexalith-release:` trailer.
  > - `publish`, and nightly's fallback, check that the two agree before publishing, and fail otherwise.
  > - Nothing sets `target_commitish` to a branch.
  > - The story-3 spike publishes a draft whose `target_commitish` is a SHA behind `main`.

### A-4 (high): A module skipped by its per-module checks gets no workflow-drift repair, although AD-8 promises one within the hour

- **Location:** AD-6 (lines 178–183), AD-8 (line 214), AD-3 per-module checks (lines 117–122), AD-7 (line 195).
- **Units:**
  - **Story 7:** the `deliver` job.
  - **Story 5:** restore, which defers to "the next delivery".
  - **Story 4:** the per-module checks.
  - **Against:** module agents and App-based agents.
- **Each obeys:**
  - AD-6: "**On a passing run, for each module that passes its own checks:** 1. Advance … 2. … apply the perimeter … 3. … push" (lines 178–181), and "A module that fails its checks is skipped" (line 183).
  - AD-8: restore skips `.github/workflows/**` and "What restore skips waits for the next delivery, at most one hour later" (line 214).
  - SPEC CAP-8: "What restore skips doesn't persist beyond the next delivery, within 1 h" (`SPEC.md:75`).
  - AD-7: for App-based agents, "The guard, the release drift check (AD-17) and hourly delivery are their control" (line 195).
- **Clash:**
  - **Things that get a module skipped:**
    - An agent deletes or renames `.github/actions/after-unit-tests`. That directory is module-owned and its token allows the change, but line 119 then fails.
    - The maintainer sets the kill switch to `False` or clears it, which fails line 122.
    - A transient API error.
  - **What story 7 then does.** It runs steps 1–4 only for passing modules, so X gets no apply at all.
  - **Why X stays red.** An App-based agent's edit to X's `.github/workflows/ci.yml` (Tenants: 84 workflow commits since 2026-10-01, per `module-inventory.md`) is skipped by restore and never redelivered. X stays red for as long as the skip lasts. The skip itself is reachable by a module agent.
- **Failure:** the workflow-drift control that AD-7 relies on is switched off for exactly the modules in trouble. CAP-8's 1-hour bound is false.
- **Fix (AD-6):**

  > - Every delivering run applies every module that has a `delivered/<Repo>` ref.
  > - A module that passes its per-module checks gets the validated commit (steps 1–4).
  > - A module that fails them keeps its ref. Its last accepted render (the perimeter and files at `delivered/<Repo>`) is re-applied with the perimeter library at that ref's `builds-version`, so the 1-hour repair bound holds while it is skipped.
  > - Only a module with no `delivered/<Repo>` yet is skipped entirely.

---

## Medium

### A-5 (medium): One `deliver` concurrency group for validate-only and delivering runs, and nightly waits on a run GitHub may cancel

**Status:** previously raised in part (pass-2 H2's "first run … whose `head_sha` is the bump commit or a descendant" was not adopted); still open.

- **Location:** Concurrency convention (line 470); AD-6 triggers (lines 176–177); AD-18 Bump (lines 370–371).
- **Units:**
  - **Story 4:** `deliver.yml` and its `validate` job.
  - **Story 7:** the `deliver` job.
  - **Story 8:** waits for "the push-triggered `deliver.yml` run of that commit".
- **Each obeys:**
  - The convention: "`deliver` and `nightly` in CiCd; a pending run may be superseded by a newer one".
  - AD-6: triggers are "push (validate only off `main`), `pull_request`, hourly at minute 47, manual dispatch".
- **Clash:**
  - **Where the group goes.** Story 4 declares `concurrency: deliver` at workflow level, as the convention reads.
  - **What it causes.**
    - PR and branch-push validate runs share the group with `main` deliveries.
    - While one run is in progress, only one pending run survives. An agent iterating on a CiCd PR during the bump cancels the bump commit's pending push run.
    - Nightly sees `cancelled`, so "that delivery failed" (line 371), and the night turns red with nothing broken.
    - The bump reaches modules only at the next `main` run.
  - **The reverse.** A delivering run can be superseded by a validate-only run.
- **Fix (Conventions, AD-18):**

  > - `deliver.yml` runs on `main` (push, schedule, dispatch) use the group `deliver`, never cancelled. All other runs use `deliver-validate-<ref>` with `cancel-in-progress: true`.
  > - Nightly waits for the first `deliver.yml` run on `main` that ran the `deliver` job on the bump commit or a descendant, and reports its conclusion. A cancelled run is not a delivery result, and the wait continues.

### A-6 (medium): A re-run, or a late, deliver run writes an older render back into every module

- **Location:** AD-6 Prevents (line 174) and step 1 (line 179).
- **Units:**
  - **Story 7:** the `deliver` job.
  - **Against:** maintainer re-runs.
  - **Story 5:** the guard, which reads `delivered/<Repo>`.
- **Each obeys:**
  - AD-6 asserts rather than requires: "It is always a fast-forward, because every ref is a commit on CiCd `main`."
  - A GitHub re-run reuses the original `GITHUB_SHA` and workflow file.
- **Clash:**
  - **Setup.** The hourly run at C2 fails, for example on one skipped module. C3 and C4 are delivered later. The maintainer then clicks "Re-run failed jobs" on the C2 run.
  - **Step 1.** The ref move from C4 back to C2 is refused, because the ruleset blocks force-push. Story 7, trusting "always", logs it and goes on.
  - **Steps 2–3.** They apply C2's perimeter and push. Module-side pushes are fast-forwards, so they succeed.
  - **Result.**
    - Every module regresses to the C2 render while `delivered/<Repo>` says C4.
    - Every guard fails, and restore reverts the non-workflow files.
    - The workflows stay at C2 until the next hourly run.
- **Fix (AD-6 step 1):**

  > - Before touching a module, `deliver` checks that its validated commit equals or descends from that module's `delivered/<Repo>`.
  > - If it doesn't, it delivers nothing to that module and reports "superseded by `<sha>`". A ref never moves backwards.

### A-7 (medium): The release's drift check reads `delivered/<Repo>` live, hours after the release SHA was fixed

- **Location:** AD-16 (line 328), AD-17 step 1 (line 344), AD-18 Dispatch and Wait (lines 368–369).
- **Units:**
  - **Story 5:** the drift check.
  - **Story 8:** dispatch and the 5-hour wait.
  - **Story 7 and CiCd agents:** CiCd commits and deliveries at any hour. Unattended agent loops run at night too.
- **Each obeys:**
  - The SHA is `github.sha` of the 02:17 dispatch, never re-resolved.
  - Nightly lets GitHub queue about 55 jobs on 20 slots (memlog 5.6), so a module's first job may start around 04:00.
  - The drift check reads the ref when it runs.
- **Clash:**
  - **What happens in the window.** Any CiCd commit between dispatch and a module's first job that changes the module's render advances `delivered/<Repo>`. A template edit changes all 17 renders.
  - **The result.** The 02:17 SHA "drifts", and every affected release fails red. A whole night is lost with nothing broken. A-1 is the permanent form of the same root cause.
- **Fix (AD-17 step 1, AD-18 Dispatch):**

  > - Nightly reads each module's `delivered/<Repo>` commit when it dispatches, and passes it as the `release.yml` input `delivered-sha`.
  > - The drift check compares the release SHA with that commit.
  > - A dispatch without the input uses the live ref.

  Both inputs are a minor Builds API addition.

### A-8 (medium): "Adopted" has three readers and no fixed test

- **Location:** AD-18 (line 368); AD-20 (line 424); AD-21 steps 3–4 (lines 453–454).
- **Units:**
  - **Story 8:** nightly dispatches adopted modules only.
  - **Story 27:** the freeze ends "when all 17 managed modules are adopted".
  - **Story 7:** the adopt commit.
- **Each obeys:** "Adopted means the module's live `main` holds the rendered `hexalith-ci.json`" (line 368).
- **Clash:**
  - **The spine doesn't say which render.** It could be the render at CiCd `main`, the one at `delivered/<Repo>`, or any render.
  - **Story 8 compares byte-for-byte with CiCd `main`'s render.** Then these modules read as "not adopted" and are silently not dispatched:
    - a module skipped by its per-module checks;
    - a module whose delivery push failed after a setup change;
    - every module, if a CiCd change landed at 02:10 and its delivery hasn't finished.

    Nightly can't fail for them, because "not adopted" is the normal state of the legacy modules during migration.
  - **Story 27 checks existence.** The freeze can then end while nightly still treats a module as legacy, or the other way round.
- **Fix (AD-18, AD-20):**

  > - A module is adopted when `delivered/<Repo>` exists and its live `main` has `.github/hexalith-ci.json`. Only delivery creates that file in a module.
  > - Nightly dispatches every adopted module; its drift check decides.
  > - A module with a `delivered/<Repo>` ref but no file has a failed adoption push, and fails the night.

### A-9 (medium): The bump pushes an unvalidated `builds-version`, so one bad Builds minor halts every delivery

- **Location:** AD-18 Bump (line 370); AD-3 global checks (line 116); AD-6 (line 176); AD-10 (line 239).
- **Units:**
  - **Story 8:** the bump.
  - **Stories 4 and 7:** the global checks gate all delivery.
  - **Story 3:** Builds releases on almost every commit type.
- **Each obeys:**
  - AD-18: "bumps `builds-version` …, re-renders, and pushes".
  - AD-6: "`deliver` runs only … after `validate`'s global checks pass".
- **Clash:**
  - **The trigger.** T2 ships an accidental interface change in a minor, such as a renamed input or a knob missing its `default`. The bump is blind, so validate fails the global checks on the push.
  - **The effect.** From then on no run delivers anything to any module until a human writes a rollback. That means:
    - no workflow-drift repair, which is the App-based-agent control of AD-7;
    - no onboarding;
    - no setup change.

    The automation has switched off the AD-6/AD-8 repair loop for all 17 modules on its own.
- **Fix (AD-18 Bump):**

  > - The bump runs the AD-3 global checks on the bumped tree before it pushes.
  > - If they fail, it pushes nothing, leaves `builds-version` unchanged, and fails the night naming the tag. The next night retries.

### A-10 (medium): Perimeter entries are judged on the working tree, and delivery's clone is sparse

- **Location:** AD-6 step 2 (line 180); AD-4 (lines 142, 152); `enforcement.md:96`.
- **Units:**
  - **Story 4:** the perimeter library and the render's glob strings.
  - **Story 7:** delivery's "shallow sparse clone".
  - **Story 5:** the guard, which runs in a full checkout.
  - **Story 6:** `check.py`, in a developer checkout.
- **Each obeys:**
  - AD-4 has one library for compare and apply.
  - AD-6 has delivery apply it in a sparse clone.
  - The table mixes root names (`.releaserc*`, `commitlint.config.*`) with `**/bmad-testarch-ci/**`, and fixes no glob dialect and no tree source.
- **Evidence (checked):**
  - `bmad-testarch-ci` is tracked under `.agents/skills/`, `.agent/skills/` and `.claude/skills/` in 14 modules.
  - Conversations tracks 27 `commitlint.config.*` files nested under `module/validation/…`.
  - FrontComposer, Memories, Parties, Projects and Tenants have nested `package.json` files.
- **Clash:**
  - **Different trees.** A library that globs the filesystem (natural Python) finds nothing outside delivery's sparse cone, but finds `.agents/skills/bmad-testarch-ci/**` in the guard's checkout.
    - The adoption commit leaves those files.
    - The first CI run fails, and restore deletes them.
    - `enforcement.md:96`'s "Delivery deletes it" is false.
    - Delivery and the guard disagree on "no diff" for every `**` glob. That is the pass-2 M9 split, now through the input rather than the code.
  - **Different dialects.** Gitignore-style matching of `commitlint.config.*` deletes Conversations' 27 nested files. Path-anchored matching does not. The render author and the library author choose independently.
- **Fix (AD-4):**

  > - The perimeter library enumerates and judges paths from git (the tree of `HEAD`, or the index), never from the working tree. A sparse or partial clone therefore judges exactly like a full checkout.
  > - Globs use git wildmatch on paths relative to the repo root: `*` stops at `/`, and only `**/` crosses directories. So `commitlint.config.*` means the root file only.

### A-11 (medium): The `nightly` hook gets no environment, and the release caller passes no registry secret

- **Location:** AD-18 `nightly-hook` (line 375); AD-14 (lines 308–309); AD-12 (lines 277–282); AD-11 (line 262); AD-17 caller (lines 339–342); Secrets convention (line 469).
- **Units:**
  - **Story 2:** the `prepare` composite.
  - **Story 3:** the `nightly-hook` job.
  - **Story 4:** the rendered `release.yml`.
  - **Stories 17 and 20:** the first nightly hooks.
- **Each obeys:**
  - Story 2 writes `prepare` as AD-11 lists it: "checkout, .NET setup, restore, build". Environment setup stays at stage 4 of the CI job (AD-12).
  - Story 3 writes AD-18 literally: "`nightly-hook`: when enabled, Builds `prepare`, then `./.github/actions/nightly`."
  - AD-14: the action "assumes a restored, Release-built workspace with the Builds environment set up".
  - The pull pair is labelled "(CI)" (line 469), and AD-17 has the caller pass nothing to `release`.
- **Clash:**
  - **No environment.** The nightly action runs without the Dapr, browsers or registry login that its knobs promise.
  - **No secret path.** With `registry: true`, the reusable release needs the pull pair, and nothing tells story 4 to pass it.
    - If story 3 declares the pair `required`, every module's release call fails.
    - If story 3 makes it optional, the hook's pulls fail.
- **Fix (AD-18, AD-12, AD-17):**

  > - `prepare` reads the knobs from `hexalith-ci.json` and, on Linux, runs the AD-12 environment setup after the build. The `nightly-hook` job therefore gets the stage-4 environment.
  > - The rendered `release.yml` passes `HEXALITH_REGISTRY_PULL_USERNAME` and `_PASSWORD` to the reusable release, which hands them only to `nightly-hook`.

### A-12 (medium): Builds' self-test can't put hook actions under `module-root`, and its test-only inputs are frozen before their consumer exists

**Status:** the first half was previously raised (pass-2 M8) and is still open; the current AD-19 text now asserts the variant that can't work. The second half is new.

- **Location:** AD-19 (line 406); AD-12 (line 287); AD-14 (line 306); AD-10 (line 233); story order 2 → 3 (first tag) → 4 (perimeter schema) → 5 (guard).
- **Units:**
  - **Story 2:** the hook steps and the `Samples/` call. It adds `module-root` and `expected-source`.
  - **Story 5:** the guard's "enabled actions exist" check, and the consumer of `expected-source`.
  - **Story 3:** the first tag, which publishes the inputs.
  - **Story 4:** the perimeter schema.
- **Each obeys:**
  - AD-19: "Under `module-root`, every module path resolves (perimeter, `hexalith-ci.json`, `.github/actions/`)."
  - Hooks are a literal `uses: ./.github/actions/<name>`, and `uses:` can't be an expression (SPEC Constraints).
  - AD-10: `workflow_call` inputs are public API.
- **Clash:**
  - **Hook location.** `./` resolves against the workspace root. The sample's hook at `Samples/x/.github/actions/after-unit-tests` is where the guard looks, but the step can't find it there.
    - If story 2 moves the actions to Builds' root, the guard reports them missing.
    - Either way, CAP-15 never exercises a hook or `tests.exclude` routing.
  - **Input shape.** Story 2 shapes `expected-source` before the perimeter schema and the guard exist, and story 3's hand-dispatched tag publishes it.
    - Story 5 may need a different shape: a directory laid out like `delivered/<Repo>`, rather than one JSON file.
    - Under AD-10, that change is a Builds major.
- **Fix (AD-19):**

  > - Hook and job actions always resolve at the workspace root (`./.github/actions/<name>`), and the guard checks them there.
  > - Under `module-root`, only `solution`, project paths, `hexalith-ci.json`, the perimeter and the owned paths are re-rooted.
  > - Builds keeps the sample's actions in its root `.github/actions/`. Only the `Samples/` call enables them.
  > - `expected-source` names a directory laid out like a `delivered/<Repo>` tree for the repo name `Hexalith.Sample`.
  > - `module-root` and `expected-source` are test-only and outside the semver public API.

### A-13 (medium): One App token per job cannot cover a 5-hour wait

- **Location:** AD-7 (line 192); AD-18 (lines 369–370).
- **Units:**
  - **Story 8:** dispatch, wait, bump and delivery wait.
  - **Against:** AD-7's minting rule.
- **Each obeys:**
  - "Each job mints a token with `actions/create-github-app-token`".
  - Nightly polls "for at most 5 hours", then pushes the bump with the App.
  - GitHub App installation tokens expire after 1 hour.
- **Clash:**
  - **The token.** Story 8 mints once at job start. Any night longer than an hour (likely: about 55 jobs, CodeQL at 6–24 minutes each, 30-minute green-CI waits) turns every poll into a 401 from about 03:17.
  - **The consequences.**
    - Every run has "no readable outcome", so all count as failed.
    - The bump push fails.
  - **The job limit.** One job that waits 5 hours, then scans, bumps and waits for delivery, can also exceed the 6-hour job limit.
- **Fix (AD-7, AD-18):**

  > - A token is never used more than 50 minutes after it was minted. Long-running jobs mint again before each App call or poll cycle.
  > - `nightly.yml` runs dispatch, wait, scan, bump and delivery-wait as separate jobs, each minting its own token.

---

## Low

### A-14 (low): Restore writes `hexalith-ci.json` without the caller that carries the same `jobs`

- **Location:** AD-8 (line 212); AD-1 (lines 89, 92); AD-13 (line 297).
- **Units:**
  - **Story 5:** restore.
  - **Story 4:** the render. `jobs` lives in both `hexalith-ci.json` and the caller.
- **Scenario:**
  1. A setup change adds Windows job J and hands project P to it through `tests.exclude`.
  2. `delivered/X` advances, but the delivery push to X does not land: the retries are exhausted, or the App push fails.
  3. An agent pushes to X. Restore writes the new `hexalith-ci.json`, because the tags are equal, but not the caller.
  4. CI excludes P, no job runs it, and CI is green.
- **Failure:** silent test loss, which AD-13 exists to prevent, until the next delivery.
- **Fix (AD-8):**

  > Restore writes `hexalith-ci.json` only when the module's `.github/workflows/` already equals the delivered render. Otherwise it waits for delivery, like the workflows.

### A-15 (low): The first Builds tag precedes the perimeter schema

- **Location:** AD-10 (lines 241, 243) against AD-4 (line 130); stories 3 → 4.
- **Units:**
  - **Story 3:** seeds `builds-version` with the first tag.
  - **Story 4:** writes the perimeter schema.
- **Clash:**
  - AD-10 says "Each Builds tag ships exactly one version of each of those three schemas", so story 3 ships a stub `hexalith.perimeter.v1.json`.
  - Story 4's real v1 is then "a change of meaning". By AD-10 that is v2 and a major, while AD-4 names v1.
- **Fix (AD-10):**

  > A tag ships at most one version of each schema. Adding a schema that no earlier tag shipped is a minor.

### A-16 (low): The `gitmodules-section` entry has no fixed identity, and modules use two section names

- **Location:** AD-4 (line 149).
- **Evidence (checked):**
  - The Builds section is named `Hexalith.Builds` in 13 modules, and `references/Hexalith.Builds` in Conversations, McpCli and Platform.
  - FrontComposer adds `branch = main`.
  - Git accepts two sections with the same path, and the last one wins. Reproduced locally.
- **Units:**
  - **Story 4:** the render and the library.
  - **Against:** the existing module `.gitmodules` files.
- **Clash:**
  - If the entry is keyed by section name, delivery appends a second section with the same path in 13 (or 3) modules.
  - A module-owned duplicate placed after the owned section silently overrides its `url` and `branch`.
- **Fix (AD-4):**

  > The entry is identified by `path`. The library keeps the existing section name (default `references/Hexalith.Builds`), removes any other section with that path, and owns only `path` and `url`.

### A-17 (low): Line endings are fixed for whole files, not for partial entries or local checkouts

- **Location:** AD-4 Prevents (line 129) and rules (lines 157–158); AD-15.
- **Evidence (checked):**
  - FrontComposer and Memories set `* text=auto eol=crlf`. CI's Linux checkout therefore writes `AGENTS.md`, `CLAUDE.md` (and in Memories, `.claude/settings.json`) as CRLF.
  - A Windows checkout with `core.autocrlf` is CRLF everywhere.
- **Units:**
  - **Story 4:** the library's partial-entry comparison.
  - **Story 6:** `check.py`.
- **Clash:**
  - A library that compares working-tree bytes reports drift that restore can't fix, because git normalizes the write back to the same blob.
  - The result is a module that is red on every push, or `check.py` disagreeing with CI (CAP-3).
- **Fix (AD-4):**

  > Every entry is judged on blob content read from git, with CRLF normalized to LF for partial entries. Writes go through `git add` under the module's attributes.

### A-18 (low): Who moves NuGet audit waivers, and in what order, is unstated

- **Location:** AD-21 step 2 (line 452) against AD-7 (line 193) and AD-10 (line 252).
- **Units:**
  - **Stories 11–26:** module agents.
  - **A CiCd agent:** Builds `Props/`.
- **Clash:**
  - **A literal contradiction.**
    - Step 2 has module agents "moving module NuGet audit waivers to Builds" with module-agent tokens.
    - That token reaches module repos only, and only CiCd agents may change Builds' waivers.
  - **No ordering.** CI runs with audit off, so if the Builds waiver isn't in the tag that the adoption delivers, nothing shows until the first release fails the audit.
- **Fix (AD-21 step 2):**

  > - A CiCd agent adds the module's waivers to Builds `Props/`.
  > - Adoption (step 3) waits until `builds-version` names a tag that contains them.
  > - Module agents only delete the module copies.

### A-19 (low): Builds' own Dependabot updates frozen files

- **Location:** AD-20 freeze (line 422); AD-19 (line 402).
- **Evidence (checked):** Builds' `.github/dependabot.yml` updates `github-actions` in `/` and `/Github/*` weekly.
- **Units:**
  - **Story 2:** owns Builds' interim tooling.
  - **Against:** the AD-20 freeze.
- **Clash:** merging a routine `ci(deps)` PR changes frozen files, such as `Github/initialize-build` and `codeql.yml`, that legacy modules run at `@main`.
- **Fix (AD-20):**

  > Until the final deletion, Builds' `dependabot.yml` excludes the frozen paths. CiCd agents close Dependabot PRs that touch frozen files.

### A-20 (low): `prepare` on Windows cannot use the one loader

- **Location:** AD-4 (line 133) against AD-11 (line 262) and AD-1 (line 92).
- **Units:**
  - **Story 2:** `prepare`.
  - **Story 4:** the rendered extra job.
  - **Story 16:** Conversations, the first Windows job.
- **Clash:**
  - **The conflicting rules.**
    - `prepare` needs `solution`.
    - The loader is Python, and the Windows part of `prepare` "contain[s] no Python".
    - Callers carry no knobs.
  - **Each way out breaks an AD.** Story 2 writes a second parser (AD-4), or story 4 passes `solution` as an input (AD-1).
- **Fix (AD-4):**

  > On Windows, `prepare` reads only `solution` with PowerShell's `ConvertFrom-Json`, after the Linux job has loaded the same document through the AD-4 loader (`needs: ci`). This is the one exception to the single loader.

### A-21 (low): Non-`main` pushes are judged against the current delivered ref

**Status:** previously raised (pass-2 L2), still open.

- **Location:** AD-8 (line 211).
- **Clash:** any branch cut before the last delivery fails the guard, even though it touched no owned file.
- **Fix (AD-8):**

  > On a non-`main` push, the guard fails only for owned paths changed in `merge-base(origin/main, HEAD)..HEAD`.

### A-22 (low): Tool-only `package.json` and lockfiles outlive delivery

**Status:** previously raised (pass-2 L10, pass-1 L4), still open.

- **Location:** AD-4 (lines 152–154).
- **Evidence:** Commons' root `package.json` holds only semantic-release and commitlint `devDependencies`.
- **Clash:**
  - After `absent-json`, the module keeps a `package.json` with no dependencies and a stale `package-lock.json`.
  - `npm ci` then fails, out of sync.
  - A rendered `npm` Dependabot ecosystem keeps proposing updates.
- **Fix (AD-21 step 2):**

  > Module agents delete a root `package.json`, its `package-lock.json` and `.husky/` when they exist only for semantic-release or commitlint.

---

## Pairs tried that held

- **Rollback across a minor knob (stories 4, 5, 7 and 8).** It holds: the restore tag rule (line 212) and the single-commit delivery keep callers, `hexalith-ci.json` and gitlink together. Only the draft path breaks (A-1).
- **Restore against delivery against an agent push.** It holds: restore stops on a non-fast-forward, and delivery re-applies.
- **`check.py` on a stale submodule against CI.** It holds: the gitlink is compared before any JSON is read (line 318).
- **Stories 4 and 7 sharing `deliver.yml`; stories 8 and 9 sharing `nightly.yml`.** They hold: the stories run in sequence and edit disjoint jobs.
- **Commitlint ownership between stories 2 and 5.** It holds: the guard composite is the only commitlint (line 209).
- **The Builds bootstrap release against the new CodeQL gate.** It holds: Builds has 0 open code-scanning alerts (checked), so the first rewritten release isn't blocked.
- **"Last `v*` tag reachable" against legacy history.** It holds: every managed repo's tags are `v`-prefixed (checked).
