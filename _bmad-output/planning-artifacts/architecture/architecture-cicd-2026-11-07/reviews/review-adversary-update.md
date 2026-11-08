---
reviewer: adversary
pass: update (re-review after the 2026-11-08 Update run, decisions validate-D1..D4 = A)
lens: "Attack the spine as an adversary: construct two units one level down that each obey every AD to the letter yet still build incompatibly — clashing shared-data shapes, two owners of one entity, conflicting state-mutation paths. Every pair you find is a hole to close with a new or tightened AD."
target: ../ARCHITECTURE-SPINE.md (status draft, updated 2026-11-08, 21 ADs; working-tree revision, uncommitted)
units: ../../../../specs/spec-cicd/stories.yaml (27 stories, text not yet updated for this revision)
previous: review-adversary-validate.md (A-1..A-22)
date: 2026-11-08
---

# Adversarial review, update gate: Hexalith.CiCd architecture spine

## Verdict

**Does not pass yet.** The revision closes 20 of the 22 validate findings. However, D1's new completion path ends in a draft publication that GitHub documents as refused in exactly the case D1 exists for (U-A1). The `resolve` job may also be unable to see drafts at all (U-A2). Either one brings back A-1's stuck release or its mixed-content version. The delivery, nightly and perimeter revisions mostly hold. Their remaining holes are medium or low.

| Severity | Count | IDs |
| --- | --- | --- |
| Critical | 1 | U-A1 |
| High | 1 | U-A2 |
| Medium | 7 | U-A3 to U-A9 |
| Low | 9 | U-A10 to U-A18 |

Line references (`L<n>`) are to `ARCHITECTURE-SPINE.md` as it stands in the working tree, unless another file is named.

## Closure of the validate findings (A-1 to A-22)

| ID | Status | Evidence in the revised spine | Residual |
| --- | --- | --- | --- |
| A-1 (critical) stuck draft deadlocks after a bump | **Partly closed** | The draft is created after the artifact, completed from the creating run's artifact with no drift, CI, loader or build step (L388–392), and `delivered-sha` is pinned (L381) | The completion's publication is refused after the bump that strands the draft (U-A1). `resolve` may not see the draft (U-A2). |
| A-2 (high) outcome has no single writer | Closed | One writer per run, with `overwrite: true` (L403–407), and the verdict table (L421–425) | The draft-deletion path has no listed outcome (folded into U-A3) |
| A-3 (high) tag target unfixed | Closed | `target_commitish` = the trailer (L360, L388), checked again by `publish` (L395) | — |
| A-4 (high) skipped module gets no repair | Closed | Step 3 re-applies every ref, passing or not (L193) | — |
| A-5 (medium) one concurrency group | Closed | `deliver` / `deliver-validate-<ref>` (L189), and "a cancelled run is not a result" (L430) | — |
| A-6 (medium) re-run writes an older render | Closed | The ref advances only to a descendant, otherwise "superseded" (L192); the run applies the render *at the ref* (L193) | — |
| A-7 (medium) drift check reads the live ref | Closed | `delivered-sha` input (L381, L419) | — |
| A-8 (medium) "adopted" undefined | Closed | L418; AD-20 cites AD-18 (L501) | — |
| A-9 (medium) unvalidated bump | Closed | The bump runs the global checks first (L427) | The two global-check runs may differ (U-A13) |
| A-10 (medium) working-tree reads, glob dialect | **Partly closed** | Reads come from git and globs use wildmatch (L147–148) | *Writes* still go through `git add` (L166), which skips paths outside the sparse cone (U-A8) |
| A-11 (medium) nightly hook has no environment or secret | Closed | `prepare` sets up the environment on Linux (L316, L438); the caller passes the pull pair (L376) | — |
| A-12 (medium) hooks under `module-root` | Closed | L472–473; inputs are test-only (L261) | — |
| A-13 (medium) one token for 5 h | Closed | The 50-minute rule (L208) and the job split (L416–434) | — |
| A-14 (low) restore writes `hexalith-ci.json` without the caller | Closed | L232 | — |
| A-15 (low) first tag precedes the perimeter schema | Closed | L263 | — |
| A-16 (low) `gitmodules-section` identity | Closed | L155 | — |
| A-17 (low) line endings | Closed | L163–166 | — |
| A-18 (low) who moves waivers | Closed | L539 | — |
| A-19 (low) Builds Dependabot touches frozen files | Closed | L499 | — |
| A-20 (low) Windows `prepare` and the loader | Closed | D4: the `solution` output (L315) | The output carries only `solution` (U-A9) |
| A-21 (low) non-`main` pushes | Closed | CI push trigger on `main` only (L313) | — |
| A-22 (low) tool-only `package.json` | Closed | L537 | The new "missing file creates it" rule could re-create it (U-A12) |

**Tally:** 20 closed, 2 partly closed (A-1, A-10), 0 open.

---

## Critical

### U-A1 (critical): Completing a draft publishes it with `GITHUB_TOKEN`, which GitHub refuses once `main`'s workflows moved, and every bump moves them

- **Location:**
  - AD-17: the module `publish` job (L377), complete mode (L390–391), `publish` step 5 (L399);
  - AD-18: `bump` (L427);
  - Deferred, first spike (L679–681);
  - `SPEC.md:199`.
- **Units:**
  - **Story 3:** complete mode, the `publish` composite, and the spike "publishing a draft behind main".
  - **Story 8:** the bump, and the optional fallback.
  - **Story 7:** delivers the bump's `build(cicd)` commit, which rewrites `.github/workflows/ci.yml` and `release.yml`.
- **Each obeys:**
  - AD-17 (L377): "`publish`: … in environment `hexalith-release`, with `id-token: write`, `contents: write` and `actions: read`. Its one step is `uses: Hexalith/Hexalith.Builds/Github/publish@<tag>`."
  - AD-17 (L399): "Publish the draft, which creates `v<version>` last."
  - AD-17 (L391): "Nothing is drift-checked, CI-checked, loaded from `hexalith-ci.json` at the draft's SHA, or built."
  - AD-18 (L427): "`bump` (no secrets), after `wait` and `scan` whatever their results: moves `builds-version`."
  - Deferred (L679): "Story 3 spike: creating or publishing a draft whose SHA is behind `main` with `GITHUB_TOKEN`, which is refused when that commit's workflows differ from the default branch's. If the spike confirms it: …"
  - Story 3: "Run the two Deferred spikes (publishing a draft behind main; …)". `SPEC.md:199` likewise "assumes that story 3's spike shows `GITHUB_TOKEN` can publish a draft behind `main`".
- **Evidence:**
  - GitHub REST, *Update a release* (and *Create a release*): "If the resolved target commit … adds or modifies any file under .github/workflows/ relative to the repository's default branch … the authenticating token must be authorized to modify workflows. … GitHub App installation tokens also need the "Workflows" repository permission (write)." `GITHUB_TOKEN` can never hold Workflows write. The memlog records the same platform constraint as verified on 2026-11-08.
  - Every bump changes the `@vX.Y.Z` strings in each module's `ci.yml` and `release.yml`.
  - Builds' own `.github/workflows/` changed in 82 of its 643 commits over the last 31 days, on 19 distinct days (`git log --since=2026-10-08 -- .github/workflows`).
- **Scenario:**
  1. **Night N.** Module X creates the marked draft v1.4.0 at S0. `publish` pushes 2 of 5 packages, then fails on a transient error.
  2. **Same night.** The bump moves T1 to T2, and delivery pushes X's `build(cicd)` commit, which rewrites both workflows.
  3. **Night N+1.** `resolve` finds the draft and selects complete mode. `draft` takes night N's artifact. `publish` pushes with `--skip-duplicate`, then PATCHes `draft: false` on target S0. S0's `.github/workflows/` differ from `main`'s, so GitHub refuses. The outcome is `failed`.
  4. **Every later night:** the same, because each bump moves `main` further from S0.
  5. **How the fallback goes missing.** A story-3 spike that publishes a draft behind `main` after an ordinary commit (identical workflows) succeeds. It "does not confirm" the refusal, so story 8 builds no fallback. The spine's own text frames the fallback as optional.
- **Failure:**
  - A-1's deadlock returns: X never releases again without a human, and nightly is red every night.
  - The same happens to Builds whenever its workflows changed after the draft, which is most days. Builds then stops tagging, so central package changes stop reaching modules.
  - Even with the fallback, AD-18's job list (L416–434) has no job that publishes `ready` drafts before `bump`, although the verdict lets `ready` pass (L424).
- **Fix (AD-17, AD-18, Deferred):**

  > - `GITHUB_TOKEN` never creates or publishes a draft whose target's `.github/workflows/` differs from `main`'s; GitHub requires Workflows write for that. `draft` and `publish` compare the two trees first.
  >   - When they differ, `draft` creates nothing and the run ends `ready` before `publish`.
  >   - `publish` pushes, then ends `ready` without publishing. In complete mode after a bump this is the normal path.
  > - `nightly.yml` gains `publish-ready` (App, `cicd-app`), after `wait` and before `bump`. For each run that ended `ready`, it creates or publishes the marked draft with the App, after the same marked-draft, digest and version checks as `publish`.
  > - Nightly's verdict: `ready` passes only once `publish-ready` has published it.
  > - The first Deferred spike is retired: the refusal is documented. CAP-13's "made by a run in its own Actions tab" is amended for these cases (spec update).

---

## High

### U-A2 (high): `resolve` has no stated permissions, and with `contents: read` it cannot see drafts, so a stuck draft is silently re-released from a newer SHA

- **Location:** AD-16 (L357); AD-17 `resolve` (L379), the permissions rule (L378), and `draft` (L388).
- **Units:**
  - **Story 3:** `resolve` (mode selection) and `draft` (create mode).
  - **Story 4:** the caller permissions it renders from story 3's API.
- **Each obeys:**
  - AD-16 (L357): "resolves the release SHA once: the SHA of the marked draft if one exists (complete mode), otherwise `github.sha` … It is never re-resolved."
  - AD-17 (L378): "Every job declares `permissions:`."
    - The rule grants `contents: write` only to `draft` (L388) and to the caller's `publish` (L377).
    - `resolve` "(stdlib only)" only reads, so a least-privilege author gives it `contents: read` and `actions: read`.
- **Evidence:**
  - The REST *List releases* reference: "Only users with push access will receive listings for draft releases."
  - astral-sh/setup-uv had to raise a release job to `contents: write` because `gh release view` could not find its draft under `contents: read`.
- **Scenario:**
  1. A draft v1.2.0 at S0 is stuck after 2 of 5 packages were pushed.
  2. `resolve` (`contents: read`) sees no draft, so it selects create mode at S1.
  3. `version` again computes v1.2.0, because no tag exists yet.
  4. `draft` creates a **second** marked draft v1.2.0 at S1. Nothing tells it to look first.
  5. `publish` pushes with `--skip-duplicate`. S0's two packages stay and S1's three are added. The tag v1.2.0 is created at S1.
  6. S0's draft stays marked forever, because v1.2.0 at S1 isn't reachable from S0.
- **Failure:**
  - `SPEC.md:102` ("A version is never republished from different content") is broken silently, on exactly the path D1 was chosen to fix.
  - A permanently marked orphan is left. Any later run that can see drafts then picks it and fails, because tag v1.2.0 already exists.
- **Fix (AD-17):**

  > - `resolve` has `contents: write` (draft listings need push access) and `actions: read`, and runs no module or third-party code.
  > - In create mode, `draft` lists drafts again before creating one, and fails if a marked draft exists.
  > - The caller's `release` job grants the union these jobs need; it is part of the AD-10 caller permissions.

---

## Medium

### U-A3 (medium): The missing-artifact path checks "a package of its version" with no package identity, and never checks containers

- **Location:** AD-17 complete mode (L391–392); `publish` step 4 (L398); AD-3 `solution: none` (L118); Outcome (L403–407).
- **Units:**
  - **Story 3:** `draft` in complete mode, and `publish`.
  - **Story 8:** reads the outcome of the deletion run.
- **Each obeys:**
  - L392: "If that run has no `release` artifact, the draft is deleted when no package of its version exists on nuget.org."
  - L391: nothing is "loaded from `hexalith-ci.json` at the draft's SHA, or built".
  - L398: `publish` pushes "the containers by version tag".
- **Clash:**
  - The package IDs were in the artifact that is gone, and the job may load nothing at the draft's SHA. Story 3 must invent an identity.
  - **Owner-wide search** ("any Hexalith package at X.Y.Z"): versions overlap across the 17 repos (Agents v1.2.2, Projects v1.2.3, Folders v1.3.3, Works v1.0.2, all checked). The search finds a false "exists", and the draft can never be completed. That is A-1's deadlock again.
  - **Repo-prefix search** (`Hexalith.<Name>.*`): mostly correct today, but nothing in the ADs makes package IDs follow the repo name.
  - **Containers:** they are pushed to Zot after NuGet and never checked. A module that ships only containers passes the check vacuously, so the draft is deleted. The next run rebuilds the same version at a newer SHA and overwrites `:vX.Y.Z`.
  - **No outcome for the deletion:** the outcome list (L405) has no value for the deletion run, so `nothing` or `failed` is story 3's guess.
- **Failure:** either a permanent deadlock or a version republished from different content. Both are rare, because they need a draft stuck for 90 days (for example a long kill-switch-`false` period), but neither can be undone.
- **Fix (AD-17):**

  > - In create mode, `draft` records the package IDs and container names from the `release` artifact's file list in the draft body, as trailers `hexalith-release-packages:` and `hexalith-release-containers:`.
  > - Without an artifact, the draft is deleted only when none of those packages exists at that version on nuget.org and none of those container tags exists in the registry. The run then ends `nothing`.
  > - Otherwise it fails with the fixed message. The recovery is the maintainer publishing the draft as it is; the next version ships what is missing.

### U-A4 (medium): The completion check names `release.yml`, but Builds' releases run from `builds-release.yml`

- **Location:** AD-17 complete mode (L390); AD-19 own release (L478–480); AD-16 (L365).
- **Units:**
  - **Story 3:** writes the run check and rewrites `builds-release.yml` onto the reusable release.
  - **Story 8:** dispatches `builds-release.yml`.
- **Each obeys:**
  - L390: "after checking that that run is this repo's `release.yml` `workflow_dispatch` run on `main` at the draft's SHA".
  - L480: `builds-release.yml` "passes `ci-workflow: builds-ci.yml` and `release-rules: builds`". There is no release-workflow input, unlike green CI's `ci-workflow` (L365).
- **Clash:**
  - In Builds, the creating run's workflow path is `.github/workflows/builds-release.yml`. The literal check rejects every Builds draft.
  - The spine also doesn't say what a failed run check does. If story 3 fails the run, Builds is stuck for good. If it treats the failure as a missing artifact, Builds' partly pushed packages make it fail anyway.
- **Failure:** Builds stops tagging after its first stuck draft. The bump then keeps the old tag, and `Props/` changes stop reaching modules (SPEC Constraints, "always reaches the modules").
- **Fix (AD-17):**

  > - The named run's workflow path must equal the running caller's, from `github.workflow_ref` (`release.yml` in modules, `builds-release.yml` in Builds).
  > - A named run that fails this check counts as having no `release` artifact.

### U-A5 (medium): CI on `main` shares one concurrency group, so a pending run for the release SHA can be cancelled, and green CI then fails the release

- **Location:** Concurrency convention (L562); AD-16 Green CI (L365–368); L357 "never re-resolved".
- **Units:**
  - **Story 4:** renders the module `ci.yml` concurrency as the convention says.
  - **Story 3:** the green-CI check.
- **Each obeys:**
  - L562: "CI group per workflow and ref, cancelling in progress only for `pull_request` … a pending run may be superseded by a newer one".
  - L365–367: "the latest run of `ci.yml` for the release SHA with event `push` or `workflow_dispatch` … Anything else, or no run: fail with 'main is red, nothing released'".
- **Scenario:**
  1. S0's CI is still running at 02:16. Runners are saturated by the nightly flood of about 55 jobs on 20 slots, so it runs long.
  2. An agent pushes S1 at 02:16. S1's run is pending, waiting for the group.
  3. Nightly dispatches at 02:17, with `github.sha` = S1.
  4. The agent pushes S2 at 02:25. GitHub cancels S1's pending run.
  5. The release finds only a cancelled run for S1 and fails red.
- **Failure:** a red night and a false "main is red" with nothing broken. The window is widest at night, which is exactly when the releases run and unattended agent loops push.
- **Fix (Conventions):**

  > The rendered `ci.yml` uses a cancelling concurrency group only for `pull_request` (`ci-<ref>`). Push and dispatch runs on `main` use `ci-<sha>`, so none is superseded.

### U-A6 (medium): The `delivered/**` ruleset doesn't restrict updates, so a non-App push can move a ref onto an unvalidated render, and delivery then reports "superseded" without failing

- **Location:** AD-21 CiCd needs (L546); AD-6 step 2 (L192), failure reporting (L196); AD-8 (L221); `enforcement.md:20`.
- **Units:**
  - **Story 1:** sets the ruleset as listed.
  - **Story 7:** the advance and the "superseded" rule.
  - **Story 5:** the guard trusts the ref.
  - **Against:** CiCd-agent sessions, whose token has Contents write on CiCd (L212).
- **Each obeys:**
  - L546: "a ruleset on `delivered/**` that blocks creation, deletion and force-push, with the App as its only bypass".
  - L192: "provided that commit equals or descends from the ref. Otherwise report 'superseded by `<sha>`'".
  - L196 makes failed checks, failed global checks and failed pushes fail the run, but not "superseded".
- **Clash:**
  - A fast-forward update is neither a creation, a deletion nor a force-push, so the ruleset allows it. `enforcement.md:20` promises the stricter rule ("lets only the App update these branches"), and GitHub rulesets have one ("Restrict updates").
  - A careless CiCd agent fixing a red guard runs `git push origin HEAD:delivered/Hexalith.X` from a work branch that descends from the ref.
  - From then on:
    - the guard and restore enforce that unvalidated render;
    - every delivery re-applies it (L193);
    - nightly passes it as `delivered-sha`;
    - no `main` commit descends from the side-branch commit, so every run reports X "superseded" and stays green.
- **Failure:** AD-8's Prevents, "the guard enforcing an unvalidated render", is defeated, and X is frozen silently.
- **Fix (AD-21, AD-6):**

  > - The `delivered/**` ruleset also restricts updates, with the App as its only bypass.
  > - A ref whose commit is not an ancestor of CiCd `main` fails the run, naming it. "Superseded" applies only to refs on `main`.

### U-A7 (medium): "The AD-21 preconditions the App can read" is an open set, checked every hour forever, and some members can never pass

- **Location:** AD-3 per-module checks (L126); AD-21 step 1 (L524–532) and step 3 (L540); the App permissions (L205).
- **Units:**
  - **Story 7:** enumerates and runs the App checks in every `main` deliver run.
  - **Story 3:** creates CodeQL analyses under `hexalith-release/<language>` and leaves drafts.
  - **Stories 11–26:** onboarding.
- **Each obeys:**
  - L126: "with the App, in `main` runs only … the AD-21 preconditions the App can read are met".
  - The App has Administration and Code scanning read and Contents write (L205). It can therefore read rulesets, drafts, CodeQL configurations and the immutable-releases setting.
- **Clash:** story 7 picks the set itself, and each plausible member breaks something:
  - **"No unmarked drafts" (L526):** the first stray draft freezes X's ref.
  - **"Stale CodeQL configurations deleted" read as "no CodeQL configurations":** after the first nightly analysis, every module fails, every ref freezes, and the bump reaches no one.
  - **"Immutable releases on":** no module can ever be adopted, because AD-21 turns immutability on only *after* the adoption commit (L540).
- **Failure:** depending on the reading, an adoption deadlock or all refs frozen, through a check meant to run once.
- **Fix (AD-3):**

  > - The App per-module checks are exactly these:
  >   - the repo is in the App installation;
  >   - its rulesets are exactly the AD-21 ones;
  >   - code-scanning default setup and Dependabot security updates are off.
  > - Drafts, tags, CodeQL configurations and immutable releases are checked by hand at onboarding, never by delivery.

### U-A8 (medium): The library reads from git but writes through `git add`, and in delivery's sparse clone git refuses every path outside the cone

- **Location:** AD-4 (L147, L165–166); AD-6 step 3 (L193); AD-21 step 3 (L540); `enforcement.md:96`.
- **Units:**
  - **Story 4:** the perimeter library. Builds CI tests it only on full checkouts: the guard, restore and the `Samples/` call.
  - **Story 7:** applies it in "a shallow sparse clone".
- **Each obeys:**
  - L147: reads "from git (the `HEAD` tree or the index), never from the working tree, so a sparse clone judges exactly like a full checkout".
  - L166: "Writes go through `git add` under the module's attributes".
  - L193: "take a shallow sparse clone of the module's live `main` and apply the render".
- **Evidence (scratch test, git 2.53, cone-mode sparse clone):**
  - `git rm deep/x/Directory.Build.rsp` and `git add .claude/settings.json` (both outside the cone) print "matched paths that exist outside of your sparse-checkout definition, so will not be updated in the index", and change nothing.
  - `git rm --sparse` works.
- **Clash:**
  - Story 7's cone holds the fixed owned paths. The absent-glob matches fall outside it: `.agents/skills/bmad-testarch-ci/**` in 14 modules, and `**/Directory.Build.rsp`.
  - A partial file created in a new directory (`.claude/settings.json` in a module without `.claude/`) falls outside it too.
  - **The result:**
    - the library *judges* drift but the write is silently dropped;
    - the adoption commit is incomplete ("Delivery deletes it" is false);
    - the first CI fails the guard, and restore cleans up;
    - every hourly run in between re-detects drift it can't write.
- **Failure:** the AD-21 "one adopt commit" is broken, and A-10's guard/delivery split is back on the write side.
- **Fix (AD-4):**

  > - The library writes only to the index:
  >   - blobs with `git hash-object -w --path=<path>`, so the module's attributes apply;
  >   - entries with `git update-index --add --cacheinfo` (mode `160000` for the gitlink);
  >   - deletions with `git rm --cached --sparse`.
  > - It never needs a path in the working tree. The guard, restore and delivery use the same calls.

### U-A9 (medium): Only `solution` reaches Windows `prepare`, so the Deferred `submodules` knob can't reach it, and AD-14 promises an environment it doesn't set up

- **Location:**
  - AD-12 (L311, L315–316);
  - AD-11 (L289);
  - AD-14 (L337);
  - Deferred "Submodules beyond Builds" (L687);
  - the deny list (`enforcement.md`, `actions/checkout`).
- **Units:**
  - **Story 1:** checks whether a package-mode build reads other submodules.
  - **Story 2:** `prepare`, the `solution` output, and any `submodules` knob.
  - **Story 16:** Conversations, the first Windows job.
- **Each obeys:**
  - L315: Windows jobs get "`prepare@<tag>` with `solution: ${{ needs.ci.outputs.solution }}`, then a literal `uses: ./.github/actions/<job-name>`".
  - L289: Windows `prepare` "contain[s] no Python and read[s] no JSON".
  - L687: "story 2 adds a `submodules` knob". The loader reads it on Linux only.
  - L337: the action "assumes a … workspace with the Builds environment set up, and never … sets up an environment".
- **Evidence:** Conversations' `testsupport-windows` job runs `git submodule update --init -- references/Hexalith.Builds references/Hexalith.Platform` before building `tests/Hexalith.Conversations.TestSupport.Tests`.
- **Clash:**
  - Story 1 finds Platform is read, so story 2 adds `submodules`.
  - Windows `prepare` can't see the knob, and the action may not check out (deny list). Story 16 therefore cannot move this job.
  - Separately, Windows `prepare` sets up no Dapr, browsers or registry login. Yet AD-14's environment guarantee is public API (L256) and covers every action.
- **Failure:** story 16 is blocked, or story 2 adds a second JSON reader on Windows, which is exactly what D4 rejected.
- **Fix (AD-12, AD-14):**

  > - The reusable `ci.yml` outputs every knob that Windows `prepare` uses, as the loader validated it: `solution` and, when added, `submodules`. Each output is public API, and the rendered Windows job passes all of them.
  > - On Windows, `prepare` sets up no environment. AD-14's environment guarantee covers Linux hooks. A Windows job's action assumes only a restored, Release-built workspace.

---

## Low

### U-A10 (low): "The last `v*` tag reachable from that SHA" has three implementers and no definition

- **Location:** AD-16 (L361); AD-17 `version` (L386) and `publish` step 1 (L395); Deferred fallback (L680–681).
- **Units:**
  - **Story 3:** `version` and `resolve`, with a full clone (`git describe`).
  - **Story 3:** `publish`, which "never checks out the repo" and so must use the API.
  - **Story 8:** nightly's fallback check, in CiCd.
- **Clash:**
  - "Last" can mean nearest by topology, highest reachable semver, or newest by date, and with or without prereleases.
  - After any out-of-order or manual tag, `publish` judges the draft "not marked" while `resolve` keeps choosing it. The run then fails every night.
- **Evidence:** today nearest = highest = newest in all 16 tagged repos, and there are no prerelease `v*` tags (checked). The hole is latent.
- **Fix (AD-16):**

  > The last `v*` tag reachable from a SHA is the highest `v<semver>` without a prerelease among tags whose commit is an ancestor of that SHA. One Builds stdlib function computes it. `publish` and nightly take it from `draft`'s outputs and re-check only ancestry.

### U-A11 (low): Create-mode draft creation is not idempotent on "Re-run failed jobs"

- **Location:** AD-17 `draft` (L388); `SPEC.md:164` ("Every release step is safe to rerun").
- **Units:**
  - **Story 3:** `draft`.
  - **Against:** maintainer re-runs.
- **Clash:**
  - `draft` creates the draft and then fails, for example when writing its outputs. A re-run repeats `draft` with `resolve`'s create-mode output.
  - Drafts create no tag, so nothing stops a second marked draft with the same `tag_name` and trailers.
  - "The SHA of the marked draft" (L357) is then ambiguous.
- **Fix (AD-17):**

  > - In create mode, `draft` reuses a marked draft whose `hexalith-release-run:` names this run.
  > - `resolve` fails if more than one marked draft exists.

### U-A12 (low): "A partial entry whose file is missing creates it" also covers `absent-json` and `absent-line`

- **Location:** AD-4 (L159–160, L165); AD-21 step 2 (L537).
- **Units:**
  - **Story 4:** the library.
  - **Stories 11–26:** module agents delete `package.json` and `.husky/`.
- **Clash:**
  - A literal library creates `package.json` as `{}` and an empty `.husky/commit-msg` in every module that lacks them.
  - That re-creates the files step 2 deletes.
- **Fix (AD-4):**

  > Only `json-superset`, `marker-block` and `gitmodules-section` entries create a missing file. An `absent-*` entry on a missing file is met.

### U-A13 (low): "Global checks … with no secrets" leaves zizmor's online audits and the acceptable-tag lookups without a token, and the two runs of the checks may differ

- **Location:** AD-3 (L123); Action references convention (L565, "its online audits"); AD-18 `bump` (L427).
- **Units:**
  - **Story 4:** the `validate` job.
  - **Story 8:** `bump`.
- **Clash:**
  - Online zizmor audits and the release, immutability, author and ancestry lookups need a token. Anonymous REST is 60 calls an hour per runner IP.
  - Story 4 gives `validate` its `GITHUB_TOKEN`. Story 8 reads "no secrets" strictly, so it runs zizmor offline and makes anonymous calls.
  - A bumped tree can then pass `bump` and fail `validate`, which brings back A-9's halt of every ref advance.
- **Fix (AD-3):**

  > The global checks are one CiCd script. `validate` and `bump` run it identically with the job's `GITHUB_TOKEN` (`contents: read`), which this rule does not count as a secret.

### U-A14 (low): Nightly's pre-dispatch drift check races a delivery in flight around 02:17

- **Location:** AD-18 `dispatch` (L418–419); AD-6 steps 2–4 (L192–194).
- **Units:**
  - **Story 8:** `dispatch`.
  - **Story 7:** a deliver run triggered by a CiCd commit at about 02:10.
- **Clash:**
  - The ref advances at 02:16 and the module push lands at 02:19. A dispatch at 02:17 sees the new ref and the old live `main`, so the module counts as "drifted" and the night fails.
  - Alternatively, the dispatch reads the old ref and `github.sha` picks up the new commit, so the drift check fails red.
  - An adoption in flight reads as "ref and no file" (L418).
- **Fix (AD-18):**

  > `dispatch` waits, for at most 30 minutes, until no `deliver.yml` run on `main` is in progress or pending, then reads the refs and the live files.

### U-A15 (low): `delivery-wait` needs each module's delivered commit, and no AD says where `deliver` records it

- **Location:** AD-18 `delivery-wait` (L429–431); AD-6 step 4 (L194); Commit types convention (L557).
- **Units:**
  - **Story 7:** `deliver`, built first.
  - **Story 8:** `delivery-wait`.
- **Clash:**
  - Story 8 must find "each delivered module's CI run on its `build(cicd)` commit".
  - Restore commits also use `build(cicd): …`. Searching module history by message can therefore match a restore commit, or a later delivery.
- **Fix (AD-6):**

  > The `deliver` job uploads `delivery.json` (artifact `hexalith-delivery`). For each module it holds the ref commit and the pushed module commit, or `unchanged`, `superseded` or `failed`. `delivery-wait` reads only that.

### U-A16 (low): The schema lets a job be named `ci`, and lets `jobs` and `hooks` coexist with `solution: none`

- **Location:** AD-3 name pattern (L116) and `solution: none` (L118); AD-12 (L310, L315).
- **Units:**
  - **Story 2:** the schema.
  - **Story 4:** the render.
- **Clash:**
  - A job named `ci` duplicates the caller's `ci` job, which every Windows job `needs:`. The rendered caller is invalid, and the *global* actionlint check fails, which blocks every ref advance.
  - With `solution: none`, a rendered Windows job passes `none` to `prepare`.
- **Fix (AD-3):**

  > Job names exclude `ci`. With `solution: none`, `jobs`, `hooks` and `tests` are empty, and `dapr` and `browsers` are false.

### U-A17 (low): Nothing requires a release run to be on `main`

- **Location:** AD-16 (L357, L360); AD-17 (L377).
- **Units:**
  - **Story 3:** `resolve`.
  - **Against:** an interactive CiCd dispatch on a branch.
- **Clash:**
  - Create mode uses `github.sha` from any dispatched ref. It builds and creates a draft at a SHA that is not on `main`. That draft is unmarked at once.
  - The `hexalith-release` environment then refuses `publish`.
  - The orphan draft is "never touched" (L409) and may trip U-A7.
- **Fix (AD-17):**

  > `resolve` fails unless `github.ref` is `refs/heads/main`.

### U-A18 (low): Builds' CI never runs Windows `prepare` or the new `solution` output, and the output's base under `module-root` is unstated

- **Location:** AD-19 own CI (L469–475); AD-12 (L315); AD-10 public API (L254).
- **Units:**
  - **Story 2:** `prepare`, the output, and `builds-ci.yml`.
  - **Story 16:** the first real consumer.
- **Clash:**
  - Windows jobs exist only in rendered callers, so CAP-15 never exercises this public API before Conversations does.
  - If story 2 adds a Windows job to `builds-ci.yml`, it has to guess the output's base. A path relative to `module-root` makes `prepare` build the wrong path. A workspace-relative path differs from what the loader validated.
- **Fix (AD-12, AD-19):**

  > The `solution` output is workspace-relative, and includes `module-root` when set. `builds-ci.yml` runs one Windows job on the `Samples/` call's output, shaped like a rendered job.

---

## Pairs tried that held

- **Single-writer outcome (stories 3 and 8):** the success, `nothing`, `disabled`, CodeQL-failed and kill-switch-`false` paths each have exactly one final writer. `overwrite: true` also defeats a hook that uploads `hexalith-release-outcome` first.
- **Draft-after-artifact against an audit failure:** no draft exists yet, so nothing needs deleting, and the next run starts clean.
- **A re-run of an old deliver run (story 7):** the ref doesn't move backwards, and step 3 applies the render *at the ref*, not the old run's own render.
- **Skipped module and global-failure mode (stories 4, 5, 7):** both re-apply existing refs and advance none, so the 1-hour bound holds.
- **`bump-push` against the deliver concurrency group (stories 7 and 8):**
  - a dispatched run that is superseded while pending is replaced by a run on a descendant, which counts;
  - `GITHUB_TOKEN`'s `workflow_dispatch` creates a run (the documented exception).
- **`bump-push` writing `rendered/**/.github/workflows/`:** GitHub's workflow-file check covers only CiCd's own `.github/workflows/`, and `bump-push` refuses anything outside `builds-version` and `rendered/`.
- **Restore against Windows `jobs` (A-14) and a module-forged `hexalith-ci.json`:** restore takes its tag from `job.workflow_ref` and recomputes from the ref.
- **`gitmodules-section` by path against live `.gitmodules`:** all 16 modules that carry Builds use path `references/Hexalith.Builds` with the same URL, under section names `Hexalith.Builds` or `references/Hexalith.Builds` (checked). Keeping the existing name handles both.
- **CRLF:** FrontComposer and Memories use `* text=auto eol=crlf`, and blob judging agrees with `git add` normalization. No module sets a filter or `working-tree-encoding` on an owned path (checked `.gitattributes`).
- **Immutable releases on Builds before stories 2–3:** the legacy `@semantic-release/github` creates a draft, uploads its assets, then publishes (checked `lib/publish.js`). Turning immutability on early therefore doesn't break the interim release, and legacy `build-release.yml` is dispatch-only.
- **Module immutable releases after adoption:** nothing reads a module release's immutability, so a first nightly release before the maintainer acts is harmless.
- **Acceptable tag against rollback:** the bootstrap tag is the floor. Only pre-bootstrap legacy tags are unacceptable.
- **Complete mode against a drifted caller:** the caller at `github.sha` is covered by nightly's pre-dispatch blob check (L419). Interactive dispatches are CiCd sessions.
- **The 50-minute rule in stdlib jobs:** stdlib Python can't sign the App JWT, so long jobs unroll mint and poll step pairs through `create-github-app-token`. That is buildable, and no two units clash on it.
- **Nightly verdict with kill switch `false` and a failed CodeQL:** the conclusion is failure and the outcome `failed`, which is consistent with L407 and L422.
- **First advance for a new module:** an absent ref passes "equals or descends" trivially, and the App bypasses the creation block.
