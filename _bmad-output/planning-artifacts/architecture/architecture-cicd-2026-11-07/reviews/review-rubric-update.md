# Rubric review (Update gate): ARCHITECTURE-SPINE.md, Hexalith.CiCd

**Verdict:** The Update closes all 12 critical and high issues except two (I-8 and I-9, each partly closed), and 68 of the 90 validate findings in full. The release path (I-1, I-4, I-6, I-10, I-11) and key custody (I-2, I-3, I-7) now hold. One edit is a regression and must be reverted before story 1 sets the CiCd rulesets: the `delivered/**` ruleset no longer limits updates to the App (U-R1). Five medium gaps sit where two stories meet, or where a Rule doesn't fully prevent what its `Prevents` line names.

- **Target:** `ARCHITECTURE-SPINE.md` (700 lines, 21 ADs, status draft, updated 2026-11-08). Diffed against `HEAD` (`4666c3d`), the validated version.
- **Read against:**
  - the validation report and the five `*-validate.md` reviews;
  - `.memlog.md` from "Update run 2026-11-08" onward;
  - the spec package at `4666c3d` (not yet updated for this revision);
  - brownfield `references/*`;
  - read-only `gh api` calls (environments, releases, latest Stack releases);
  - the nuget.org Trusted Publishing docs;
  - a scratch test of `uv lock --script` / `uv run --locked --script`.
- **Line numbers** refer to the current spine.

**Counts: 0 critical, 1 high, 5 medium, 14 low.**

## Checklist

| # | Item | Result | Findings |
| --- | --- | --- | --- |
| 1 | Fixes the real divergence points for the 27 stories | **Partial** | The validate interfaces are closed: Windows `solution` (D4), the hook contract, MSBuild entry points, the outcome writer, delivery and nightly ownership. New or remaining seams: story 2's CI job vs story 20's hook secrets (U-R4); story 4's `validate` output vs story 7's `deliver` (U-R10); story 1's environments and policies vs onboarding stories 11–26 (U-R2, U-R8); story 5's custom-action check vs stories 13–24 (U-R3). |
| 2 | Every Rule is enforceable and prevents its `Prevents` divergence | **Partial** | AD-21's `delivered/**` ruleset no longer stops unvalidated refs (U-R1). AD-8's custom-action check has a path-scope escape (U-R3). AD-10's "is a major" has no check (U-R6). The AD-7/AD-18 bump has a stale-tree failure mode (U-R5). |
| 3 | Nothing under Deferred lets two units diverge | **Partial** | The pass-2 catch-all is gone and every entry has an owner. But "Hook and job secrets … to a separate job" pre-decides a shape that AD-12 and the spec forbid (U-R4). The `NuGet/login`-in-composite spike has no bound fallback (U-R19). |
| 4 | Named technology is verified-current (light) | **Pass** | Checked live today: setup-python v7.1.0, create-github-app-token v3.3.0, zizmor v1.32.0, uv 0.13.7, Dapr runtime and CLI v1.19.1, upload-artifact v7.0.2, @commitlint/config-conventional 21.2.4. `uv run --locked --script` works and rejects a stale lock. The releases API exposes `immutable`, so the acceptable-tag test can be implemented. |
| 5 | Ratifies the brownfield | **Partial** | It now ratifies the commitlint limits, the Dapr pins, the existing `Samples/`, the two `.gitmodules` section names, line endings and Dependabot. New contradictions: the forced `RestoreConfigFile` silently drops the signature-validation hardening in Agents and Memories (U-R9). The 14 existing legacy nuget.org policies and `production` environments are not accounted for (U-R2, U-R8). |
| 6 | Covers CAP-1..CAP-16 | **Pass, with notes** | 16/16 are bound. U-R5 weakens CAP-6 ("within one night"), U-R4 contradicts CAP-5 ("without repeating … build"), and U-R1 reopens CAP-8's "rejected render never reaches the guard". |
| 7 | Every owned dimension is decided, deferred or open | **Pass, with a note** | Environments (two GitHub environments, no runtime ones), providers, operations and quotas are all stated now (R-12 closed). The protection settings of the two new environments are not (U-R8). |
| F1 | Decisions, not rationale | Mostly | One "because" and four "so …" clauses remain (U-R20). |
| F2 | Invariants separated from the seed | Pass | The seed's Operations bullets restate the AD bounds; the quotas bullet is new. |
| F3 | Every AD has Binds, Prevents and Rule | Pass | 21/21 (script). |
| F4 | Diagrams agree with the ADs | Partial | The sequence diagram now matches AD-18's seven jobs, keepalive included. The flowchart, which calls itself "the allowed dependencies", lacks four edges (U-R15). |
| F5 | Cross-references resolve | Pass | Every `AD-n` is in 1–21. |
| F6 | The map's "Governed by" matches the Binds lines | **Pass** | 16/16 rows match exactly (script). R-16's map half is closed. |

---

## High

### U-R1 (high, regression): the `delivered/**` ruleset no longer limits updates to the App

- **Location:** AD-21 "CiCd itself needs", line 546. Depends on AD-6 step 2 (line 192), AD-8 (line 221) and AD-6 step 3 (line 193).
- **Issue:**
  - The old text read: "a ruleset on `delivered/**` that blocks deletion and force-push and lets only the App update those branches".
  - The new text reads: "blocks creation, deletion and force-push, with the App as its only bypass".
  - Adding creation (X-16) dropped the update restriction. Rulesets treat "Restrict creations", "Restrict updates", "Restrict deletions" and "Block force pushes" as separate rules. With only creation, deletion and force-push restricted, anyone with Contents write on CiCd can fast-forward `delivered/<Repo>` to any commit.
- **Evidence:**
  - Old spine line 456 (`git show HEAD:…`).
  - `enforcement.md:20` still says "lets only the App update these branches", so the spine now contradicts the spec.
  - The agent Apps are now excluded from CiCd, but the CiCd-agent token keeps Contents write on CiCd (AD-7, line 212).
- **Failure it allows:**
  - A CiCd agent "fixes" a red module by pushing an edited render straight to `delivered/Hexalith.X`.
  - The guard and restore enforce it (AD-8), and each hourly run's step 3 applies it into the module with the App, workflows included. That is an unvalidated render reaching the module and the guard, which is exactly what AD-6 and AD-8 prevent.
  - Delivery can't repair it. Step 2 advances only to a commit that "equals or descends from the ref", and `main` never descends from the hand-pushed commit. So the module reports "superseded" and stays on the foreign render until a human resets the ref, which only the App can do.
- **Fix (AD-21, line 546):**
  > a ruleset on `delivered/**` that restricts creation, updates and deletion and blocks force-push, with the App as its only bypass actor;

---

## Medium

### U-R2 (medium): onboarding adds a `hexalith-release` nuget.org policy but says nothing about the policy that already exists

- **Location:** AD-21 step 1, line 528; AD-7 "Publish credentials", line 210; AD-19 preconditions, lines 482 and 487.
- **Issue:**
  - 14 modules publish today from a legacy `release.yml` that runs `NuGet/login` under `environment: production`, so each already has a nuget.org policy for `release.yml` (FrontComposer's is for `release-publish.yml`).
  - AD-21 says to "create … the nuget.org policy for `release.yml` naming it". AD-7 says "each nuget.org Trusted Publishing policy names it". Neither rule says when the existing policy goes.
  - Builds has an explicit interim rule (AD-19). The modules have none.
- **Evidence:**
  - `grep` of `references/*/.github/workflows`: `NuGet/login` sits in `release.yml` under `environment: production` in Commons, Conversations, EventStore, Folders, McpCli, Memories, Parties, PolymorphicSerializations, Projects, Tenants, Timesheets, Works and ChatBot (ChatBot without an environment).
  - `gh api repos/Hexalith/Hexalith.Commons/environments` shows `production` with `required_reviewers` and `branch_policy`.
  - nuget.org issues a key when the token matches "a trusted publishing policy you've configured", and the environment is "validated only if set in the policy" (learn.microsoft.com/nuget/nuget-org/trusted-publishing; memlog l.99, NuGetGallery validator).
- **Failure it allows:** each reading breaks something.
  - **Add a policy beside the old one.** An old policy with no environment keeps I-9's hole open (any `release.yml` run on any branch can mint a key) for as long as it exists, and no rule deletes it.
  - **Edit the old policy to name `hexalith-release`.** The legacy release keeps running under `production` from step 1 until the adoption commit, and fails `NuGet/login` for that whole window, which can be days.
- **Options:**
  - **A (recommended).**
    - *How:* step 1 adds the `hexalith-release` policy beside the existing one. Right after the adoption commit, together with immutable releases, the maintainer deletes every other nuget.org policy for that repo.
    - *Pros:* legacy releases work until adoption, and the hole closes at adoption.
    - *Cons:* the old exposure lasts for the onboarding window.
  - **B.**
    - *How:* step 1 replaces the policy.
    - *Pros:* the hole closes earliest.
    - *Cons:* the module has no releases between step 1 and adoption.
- **Fix (option A, AD-21):**
  - Step 1: "… and add a nuget.org policy for `release.yml` naming it, beside any existing policy;"
  - Step 3: "The maintainer then turns on immutable releases and deletes every other nuget.org policy for the repo."
  - AD-7: "After adoption, a module's only nuget.org policy is for `release.yml` and names `hexalith-release`."

### U-R3 (medium): the custom-action check covers only `.github/actions/**/action.yml`, so a local sub-action elsewhere escapes it

- **Location:** AD-8, line 225; AD-14, lines 335–336. Partly closes R-4.
- **Issue:**
  - The guard checks that each `.github/actions/**/action.yml` is composite, and that its `uses:` are `./…` or SHA-pinned third-party actions.
  - But `./…` may point anywhere in the workspace, AD-14 allows "local sub-actions", and GitHub also accepts `action.yaml`.
- **Evidence:**
  - GitHub resolves `uses: ./path` to `path/action.yml` or `path/action.yaml`.
  - Nothing confines local paths to `.github/actions/`. The deny list (`enforcement.md:59-69`) and the scan cover "custom actions" by the same path convention.
- **Failure it allows:**
  - A hook at `.github/actions/after-unit-tests/action.yml` calls `uses: ./tools/ci-helper`. That file may be a JavaScript or Docker action, or may call `Hexalith/Hexalith.Builds/Github/initialize-build@main`.
  - The result is two Builds versions in one run (AD-9), plus a rebuild and environment setup outside the contract (AD-14).
  - The guard passes it, and stories 13–24 copy the pattern.
- **Fix (AD-8 and AD-14):**
  > Every local `uses:` in a custom action names a directory under `.github/actions/`. The guard checks every `action.yml` and `action.yaml` under `.github/actions/**` (composite, `uses:` rule, deny list), and fails on any other local action path.

### U-R4 (medium): "hook secrets go to a separate job" contradicts SPEC's "CI is one job", CAP-5 and AD-12

- **Location:** AD-14, line 338; AD-12, line 315 ("`jobs` exist only for Windows"); Deferred, line 688 (story 20).
- **Issue:** AD-14 now sends hook secrets "to a separate job, never to the CI job". That job is undefined:
  - It isn't a hook, because hooks run inside the CI job (AD-12).
  - It isn't a `jobs` entry, because those are Windows-only (AD-12).
  - It has to repeat checkout, restore and build to get the workspace the hook contract promises (AD-14, line 337).
- **Evidence:**
  - `SPEC.md:150-152`: "A separate job is allowed only for one of these": the other-OS job and restore.
  - CAP-5 (`SPEC.md:55`): "An enabled hook runs without repeating checkout, restore, build, or environment setup."
  - The memlog's upstream list does not include this delta.
- **Failure it allows:**
  - Story 20 (EventStore's Azure-backed tests) has to invent a third job type. It might be a Linux `jobs` entry, against AD-12, or a hook that receives secrets in the CI job, against AD-14.
  - Story 2's reusable `ci.yml` has no slot for either.
  - Whichever story 20 picks, it breaks a spec constraint without raising it.
- **Options:**
  - **A (recommended).**
    - *How:* make the job a defined variant of `jobs`, and raise the spec delta now.
    - *Pros:* secrets stay out of the CI job (X-9's intent), and story 20 gets a ready slot.
    - *Cons:* one more compile for that module, and a spec change.
  - **B.**
    - *How:* AD-14: "hook secrets are passed by name to the CI job and readable by all its steps, accepted under the careless-agent model".
    - *Pros:* no spec change, no extra compile.
    - *Cons:* every test and dependency in the CI job can read the Azure secret.
- **Fix (option A, AD-12 line 315 and AD-14 line 338):**
  > `jobs` exist only for Windows, or for an action that needs a secret (AD-14). A secret job is rendered with `needs: ci`, `runs-on: ubuntu-latest`, `prepare` and then the action, and receives only the secrets named for it. This third separate-job exception, and the repeated build it implies, are raised as a spec update (SPEC Constraints, CAP-5).

### U-R5 (medium, robustness regression): the bump can render on the 02:17 tree, so any CiCd commit during the night fails it

- **Location:** AD-18 `bump` and `bump-push`, lines 427–428; CAP-6 (`SPEC.md:62`).
- **Issue:**
  - The old rule re-fetched and recomputed on a non-fast-forward (up to 3 times). The new rule says "A non-fast-forward fails the night; the next night retries". That choice is sound, because it keeps Jinja2 out of a write job.
  - But nothing says which tree `bump` renders. A scheduled run's `github.sha`, the default for `actions/checkout`, is the default-branch head when the run starts. `bump` runs after a wait of up to 5 hours.
- **Evidence:**
  - Every job of a `schedule` run shares the trigger-time `GITHUB_SHA`.
  - Unattended agent loops commit to CiCd at night (adversary A-7).
- **Failure it allows:**
  - Any CiCd commit between 02:17 and the bump makes `bump-push` non-fast-forward, so the night fails and Builds doesn't move.
  - A nightly agent loop can keep that happening night after night, which breaks CAP-6's "within one night of a Builds release, all modules reference it".
- **Fix (AD-18 `bump`):**
  > `bump` fetches the current tip of CiCd `main` when it starts, never the run's `github.sha`, and renders on it. `bump-push` pushes that commit onto the same tip.

### U-R6 (medium): AD-10 classifies a public-API removal as "a major", but nothing checks the classification

- **Location:** AD-10, lines 253–259 (public API; "Removing or renaming any of them is a major") and lines 269–274 (auto-bump, release rules). Prevents line 251: "a minor breaking custom actions or module imports".
- **Issue:**
  - The version bump comes from commit types: `@semantic-release/commit-analyzer` makes a major only from `!` or `BREAKING CHANGE`.
  - A CiCd agent who removes a `PackageVersion`, a composite input or a `workflow_call` output under `build:` or `fix:` ships a minor. The auto-bump then delivers it to all 17 modules that night.
  - The bump's global checks (line 427) validate only the render.
- **Evidence:** no Rule compares the public API with the previous tag. `builds-ci.yml`'s `Samples/` call only catches what the sample uses.
- **Failure it allows:** modules fail with NU1010 or MSB4019, or their callers fail on a missing input, around 04:00. `delivery-wait` turns the night red, all 17 modules are red until a human writes a rollback, and module agents meanwhile try to "fix" the pipeline.
- **Fix (AD-10, Public API):**
  > `builds-ci.yml` compares the public API with the last release tag: `workflow_call` inputs, secrets and outputs; composite inputs; schema files; imported MSBuild files; the `PackageVersion` set. It fails a change that removes or renames any of them unless its commits carry a breaking-change marker.

---

## Low

- **U-R7 (low): re-minting has one valid mechanism, and the Rule doesn't name it** (AD-7, line 208; AD-18 `wait`, line 421).
  - **Issue:** "A longer job mints again." The App JWT is RS256-signed, and stdlib Python can't sign RSA. A `cicd-app` job may run only stdlib Python, git and SHA-pinned actions. So the only valid way to re-mint is another `create-github-app-token` step.
  - **Failure:** story 8 writes the 5-hour wait as one Python loop. It then adds PyJWT or `cryptography` to the key-holding job (the I-2 risk), or hand-rolls RSA.
  - **Fix (AD-7):** "A job re-mints by running `create-github-app-token` again as its own step. No CiCd script signs the App JWT, and a step that uses a token runs at most 50 minutes. `wait` alternates mint and poll steps."
- **U-R8 (low): the protection settings of the new environments are unstated, and today's `production` environments require reviewers** (AD-7, lines 206 and 210; AD-21, lines 528 and 544).
  - **Evidence:** `gh api …/environments` on Commons, Parties and Builds shows `production` with `required_reviewers` and `branch_policy`.
  - **Failure:** a maintainer copies `production`'s settings into `hexalith-release` or `cicd-app`. Every unattended publish or delivery then waits for an approval: nightly counts the run as failed at 5 hours, and hourly delivery stalls.
  - **Fix (AD-7):** "`cicd-app` and `hexalith-release` have one protection rule, deployment branch `main`, with no required reviewers and no wait timer."
- **U-R9 (low): the forced Builds NuGet config drops the module hardening it replaces, and the audit lint misses `NuGet.config`** (Conventions "SDK and build", line 566; AD-8, line 226).
  - **Evidence:**
    - `Hexalith.Agents/NuGet.config` and `Hexalith.Memories/NuGet.config` set `signatureValidationMode` to `require`, define `trustedSigners` and `packageSourceMapping`, and say they are the "supply-chain hardening baseline for new Hexalith modules".
    - `RestoreConfigFile` replaces the config hierarchy.
    - Both files are named `NuGet.config`, and the lint names `nuget.config` (case-sensitive on Linux).
  - **Fix:** in the Convention: "Builds' nuget.org-only config sets `signatureValidationMode` `require`, the nuget.org `trustedSigners`, and maps `*` to nuget.org." In AD-8: "… and NuGet config files (matched case-insensitively)".
- **U-R10 (low): the `validate`-to-`deliver` interface isn't fixed** (AD-6, lines 186–192).
  - **Issue:** `deliver` runs "after `validate` whatever its result", yet must know whether the global checks passed and which modules passed the anonymous checks. Story 4 writes `validate` and story 7 writes `deliver`.
  - **Fix (AD-6):** "`validate` outputs one JSON object: the global-check verdict and the names of the modules that passed the anonymous checks. `deliver` treats a missing output as a failed global check, and accepts only names in `setup/*.yml`."
- **U-R11 (low): `delivery-wait` reads a superseded module CI run as a failure** (AD-18, lines 429–433; Concurrency convention, line 562).
  - **Issue:** a module's pending CI run on the `build(cicd)` commit is cancelled when an agent push lands first ("a pending run may be superseded"). The night then fails with nothing broken.
  - **Fix:** "… then, for each delivered module, the first completed, non-cancelled `ci.yml` run on `main` whose head is its `build(cicd)` commit or a descendant."
- **U-R12 (low): the nightly pre-dispatch check reads an in-flight delivery as drift** (AD-18 `dispatch`, line 419).
  - **Issue:** a CiCd commit shortly before 02:17 advances `delivered/<Repo>` before the module push lands. The module counts as "drifted", isn't dispatched, and loses that night's release.
  - **Fix:** "`dispatch` first waits, for at most 30 minutes, for any in-progress or pending `deliver.yml` run on `main` to finish."
- **U-R13 (low): the legacy org secrets are restricted once, and adopted modules keep access** (AD-21 "Once, before the first adoption", line 522). This partly closes R-10.
  - **Issue:** at the first adoption all 17 modules still read the legacy secrets, so the one-time restriction includes them. "An adopted module reads none of them" is a statement, not an action. R-10's scenario (a copied legacy workflow publishing with `NUGET_API_KEY`) stays open for adopted modules.
  - **Fix (AD-21 step 3):** "The maintainer then removes the module from every legacy org secret's repository list."
- **U-R14 (low): orphan `v*` tags must be deleted after the `v*` ruleset exists, and that ruleset has no bypass** (AD-19, lines 482 and 489; AD-21, lines 526–527). This partly closes S-5.
  - **Issue:** for Builds, the tag ruleset comes before any change (story 1), while orphan-tag deletion is re-checked right before the bootstrap (story 3). The interim legacy release fails about 30% of the time. For modules, the legacy release keeps running between step 1 and adoption. Each case can leave a tag that only a ruleset bypass can delete.
  - **Fix (AD-21):** "The `v*` ruleset's only bypass actor is the repository admin role, used only to delete orphan `v*` tags."
- **U-R15 (low): the flowchart lacks edges the ADs allow** (lines 44–88). This partly closes R-16.
  - **Missing edges:**
    - `NIGHTLY → DELIVER` (`bump-push` dispatches `deliver.yml`, AD-18);
    - `NIGHTLY -.-> DELIVERED` (the pre-dispatch comparison and `delivered-sha`);
    - `NIGHTLY -.-> ACT` (the scan reads module live `main`);
    - `RENDER → Builds` at `builds-version` (schemas, AD-5).
  - Line 88 calls the arrows "the allowed dependencies".
  - **Fix:** add the four edges.
- **U-R16 (low): jscpd's explicit config is in the memlog but not in the spine** (AD-18 `scan`, line 426). This partly closes X-13.
  - **Fix (AD-18):** "`scan`: jscpd with Builds' or CiCd's committed config, never a config from the scanned module."
- **U-R17 (low): `resolve` "runs the guard check" in a stdlib-only job** (AD-17, line 381).
  - **Issue:** the guard includes commitlint (Node) and the lints, but CAP-8 needs only the owned-file comparison. Story 3 or 5 may run the whole guard composite in `resolve`, or decide stdlib-only is impossible.
  - **Fix:** "run the AD-4 perimeter comparison (the drift check only) on the release SHA …".
- **U-R18 (low): the SHA-256 rule doesn't fit tool-managed downloads, and some Stack rows are still missing** (AD-11, lines 286–288). This partly closes V-11.
  - **Issue:** Playwright browser installs and `dapr init` download binaries themselves, so no Builds script can check a SHA-256 for them. Microsoft.Playwright and `gh` still have no row; the container push tool is deferred.
  - **Fix (AD-11):** "… downloaded binaries that a Builds or CiCd script fetches itself, through a SHA-256 checked before use. Tool-managed downloads (Playwright browsers, the Dapr runtime) are pinned by the tool's version."
- **U-R19 (low): the `NuGet/login`-in-composite spike has no bound fallback** (Deferred, line 684; AD-17, line 377).
  - **Issue:** if `NuGet/login` fails inside the remote `publish` composite, AD-17's "Its one step is `uses: …publish@<tag>`" is wrong, and story 4's render differs from story 3's composite.
  - **Fix (Deferred):** "If it fails, the caller's `publish` job runs `NuGet/login` as its first step and passes the key to `publish` as an input. That input is part of the composite interface (AD-10)."
- **U-R20 (low): form and scope polish.** This partly closes R-24.
  - Rationale clauses remain at line 505 ("because today's ruleset requires its check") and as "so …" consequences at lines 147, 338, 472 and 683.
  - The Workflow-security convention (line 561) says "every workflow declares top-level `permissions: {}`", but the frozen legacy workflows (AD-20) can't change.
  - **Fix:** drop the clauses, and write "every workflow outside the AD-20 freeze declares …".

---

## Regressions and new contradictions

| Kind | Where | What |
| --- | --- | --- |
| Regression (was correct, now wrong) | AD-21, line 546 | The `delivered/**` ruleset lost "lets only the App update" (U-R1). |
| Behavioural weakening | AD-18, lines 427–428 | The bump's 3× re-fetch was replaced by "fail the night", with no rule on which tree it renders (U-R5). Defensible as a trade-off, but not complete. |
| New AD-vs-AD contradiction | AD-14, line 338 vs AD-12, line 315 | A separate hook-secret job vs "`jobs` exist only for Windows" (U-R4). |
| New spine-vs-spec contradictions | AD-14 vs SPEC Constraints and CAP-5; AD-21 vs `enforcement.md:20` | U-R4 and U-R1. Both are absent from the memlog's upstream list. |

No other rule that was correct before is now wrong. Checked case by case:
- the skipped-module re-apply vs "superseded": step 3 applies the ref's render, never the run's own commit, so a re-run can't regress a module;
- complete mode vs the CodeQL gate: the draft exists only after `codeql` and `nightly-hook` passed, and completion re-gates on `github.sha`;
- the outcome writers: exactly one per path;
- the App permissions without Variables: nothing else reads Variables with the App;
- `cicd-app` vs `pull_request` runs: `validate` holds no secret;
- `cache-mode: none` vs `nightly-hook`: it blocks both reading and writing.

---

## Closure of the validate findings

Status values:
- **C:** closed by the new text.
- **P:** partly closed.
- **D:** deferred explicitly.
- **H:** spec-side, handed to bmad-spec (the spine needs no change).
- **O:** left open.

### Critical and high (I-1..I-12, D1–D4)

| ID | Status | Where it closes / what remains |
| --- | --- | --- |
| I-1 | C | AD-16 complete mode, AD-17 step 4 (artifact from the run in `hexalith-release-run:`; no drift check, CI check, loader or build; 90 days; fixed message), `delivered-sha` input (A-7). |
| I-2 | C | AD-7, line 207 (`cicd-app` jobs: stdlib, git, SHA-pinned actions, JSON only; render, lint and scan without secrets; scoped mints); AD-11 (uv lock, npm `--ignore-scripts` + `audit signatures`, SHA-256). See U-R7. |
| I-3 | C | AD-7 (50-minute rule); AD-18 (seven jobs, each minting, each under 6 h). See U-R7. |
| I-4 | C | AD-17 Outcome (one writer per path, `overwrite: true`, `failed`/`disabled` rules); AD-18 `wait` verdict. |
| I-5 | C | AD-6 step 3 (every module with a ref, passing or not, even when the global checks fail). |
| I-6 | C | AD-17 `draft` (`target_commitish` = full SHA); AD-16 marked test; `publish` re-checks; Deferred spike "behind `main`". |
| I-7 | C | AD-7 (`cicd-app`, `main` only; only `deliver` and the nightly App jobs); D3: agent Apps exclude CiCd and Builds (AD-7, AD-19, AD-21). |
| I-8 | P | Acceptable tag (AD-10), global check, bump runs the global checks, "set rulesets … creating missing ones", immutable releases, `delivered/**` creation blocked. Remaining: `v*` creation restriction deferred to the story-1 check, and the update restriction lost (U-R1). |
| I-9 | P | `hexalith-release` (`main` only), policy names it, nightly pre-dispatch comparison, `ci-workflow` restricted. Remaining: existing policies not retired (U-R2); package-ID scoping deferred to story 1. |
| I-10 | C | AD-17 job split, `permissions:` everywhere, `persist-credentials: false`, stdlib `resolve` and `draft`, artifact by ID + digest + nupkg checks, marked-draft test. |
| I-11 | C | AD-17 and Conventions (`cache-mode: none`, `package-manager-cache: false`, `enable-cache: false`, no NuGet cache). |
| I-12 | C | AD-20, line 500 (deletes text-asserting tests, frozen directories included); AD-19, line 476. |
| D1–D4 | C | Applied as chosen: A, A, A, A (memlog). |

### Medium (34)

| ID | St. | Note | ID | St. | Note |
| --- | --- | --- | --- | --- | --- |
| A-5 | C | AD-6 groups; AD-18 "a cancelled run is not a result" | R-11 | C | AD-20 Dependabot exclusion + closing PRs |
| A-6 | C | AD-6 step 2 "never moves backwards" + step 3 | S-2 | C | AD-20 legacy list widened |
| A-7 | C | `delivered-sha` (AD-17, AD-18) | S-3 | C | AD-4, line 145 (whole-file only) |
| A-8 | C | AD-18 "adopted"; AD-20 cites it | S-4 | C | → I-5 |
| A-9 | C | AD-18 `bump` runs the global checks | S-5 | P | Created where missing, deletion before the ruleset for modules; Builds' ordering trap and the missing bypass remain (U-R14) |
| A-10 | C | AD-4 (git tree or index, wildmatch) | S-6 | C | AD-19 "checked again right before the bootstrap"; story-3 text → H |
| A-11 | C | AD-12 `prepare` on Linux; AD-17 pull pair to `nightly-hook` | S-7 | P | AD-10 "at most one"; AD-6 delivery waits for the schema tag. Story 4's `validate` ordering is neither stated nor in the upstream list |
| A-12 | C | AD-19 (workspace-root actions, test-only inputs, `expected-source` layout) | S-8 | C | Deferred (`ready` before/after publish); story-3 text → H |
| A-13 | C | → I-3 | V-2 | C | Variables dropped; kill switch on the AD-21 checklist |
| R-3 | C | D4 (AD-12, AD-10, AD-11) | V-3 | C | Conventions: actionlint ignores `job.workflow_*` and `cache-mode` |
| R-4 | P | Composite and `uses:` checks added; the path-scope escape remains (U-R3) | V-4 | C | Deferred "creating or publishing" + creation fallback |
| R-5 | C | AD-10 hook and job contract | V-5 | D | AD-7 "start each branch from current `main`"; Deferred story-10 check |
| R-6 | C | AD-10 MSBuild files + `PackageVersion`; AD-19 sample imports. Enforcement gap: U-R6 | X-7 | P | `-noAutoResponse`, `RestoreConfigFile`, NU1900/NU1905, wider lint; the assets-file verdict was rejected (memlog); new side effects in U-R9 |
| R-7 | C | → I-4 | X-8 | C | AD-3 string constraints; AD-5 `tojson` + `StrictUndefined`; lint over `rendered/**` |
| R-8 | C | Dependabot org secret (AD-21, Conventions); "who merges" deferred to story 4 | X-9 | C | AD-14 secret visibility; AD-8 `uses:` rule; `persist-credentials: false`. New conflict: U-R4 |
| R-9 | C | AD-18 `delivery-wait` waits for module CI. See U-R11 | X-10 | C | → I-10 |
| R-10 | P | `HEXALITH_*` + pull-only Zot account created; the legacy-secret restriction is one-time (U-R13) | X-11 | C | → I-2; zizmor online audits in Conventions |

Medium tally: 28 C, 5 P, 1 D.

### Low (44)

| ID | St. | ID | St. | ID | St. | ID | St. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-14 | C (AD-8, line 232) | R-13 | C (AD-5, line 174) | S-9 | H | V-6 | C (Seed, AD-19) |
| A-15 | C (AD-10) | R-14 | C (AD-12, line 313) | S-10 | H | V-7 | C (Deferred Dapr pins, Stack CLI row) |
| A-16 | C (AD-4 table) | R-15 | C (Conventions, today's limits) | S-11 | H | V-8 | C (`HEXALITH_CICD_APP_CLIENT_ID`) |
| A-17 | C (AD-4, lines 163–166) | R-16 | P (map and line 88 fixed; edges: U-R15) | S-12 | H (AD-1 now names both run-time reads) | V-9 | C |
| A-18 | C (AD-21 step 2) | R-17 | C | S-13 | C (AD-4, line 165) | V-10 | C (Deferred; story-8 text still says "verify", → handoff) |
| A-19 | C | R-18 | C | S-14 | C (Deferred split; spec text → H) | V-11 | P (rows added; Playwright and `gh` missing: U-R18) |
| A-20 | C (D4) | R-19 | C | S-15 | C (AD-21 step 2) | V-12 | C (matrix) |
| A-21 | C (via R-14; PRs judge the merge ref) | R-20 | D (story-1 check) | S-16 | H (spine Deferred updated) | V-13 | C (Stack and Conventions `rollForward`) |
| A-22 | C (AD-21 step 2) | R-21 | C (AD-2) | S-17 | H | X-12 | C (Conventions, AD-21) |
| R-12 | C (seed quotas) | R-22 | C (AD-10) | | | X-13 | P (commitlint `--config`, `.commitlintrc*` added; jscpd config missing: U-R16) |
| | | R-23 | D (Deferred story 10: instruction-block control) | | | X-14 | C (AD-8, line 231) |
| | | R-24 | P (`[ADOPTED]` gone; clauses remain: U-R20) | | | X-15 | D (story-3 provenance) |
| | | | | | | X-16 | P (creation blocked; update restriction lost: U-R1) |

Low tally: 30 C, 5 P, 3 D, 6 H.

**Overall (90 findings): 68 closed, 12 partial, 4 deferred explicitly, 6 spec-side handoff, 0 left open.**

---

## Spec handoff items (not rated as spine defects)

The memlog's upstream list covers environments, agent-App exclusion, draft-after-artifact, the outcome writer, the nightly split, re-apply and concurrency, Windows `solution`, the acceptable tag, CAP-15 test deletion, the Dependabot exclusion, the `Samples/` layout and the commitlint limits. Items not on that list:

- **story 4:** move `builds-version` to a tag that ships the perimeter schema before `validate` checks perimeters (S-7);
- **story 4 / story 7:** the per-module checks split into anonymous (`validate`) and App (`deliver`), plus the `validate` output (U-R10);
- **story 5:** the composite and `uses:` checks, the extended audit lint and commitlint `--config` (R-4, X-7, X-9, X-13);
- **story 8:** its description still says "verify whether bot commits count as activity", while the Deferred entry says this "can't be tested within a story" (V-10);
- **story 20:** the hook-secret job shape (U-R4);
- **`enforcement.md` Layer 2 step 3:** "On a PR or a push to another branch". CI now runs on push to `main` only (R-14);
- **`pipeline-stages.md` Nightly run steps 2.1–2.7:** the build runs before the draft; complete mode skips the drift check, the CI check and the build; `codeql` and `nightly-hook` run at `github.sha`;
- **`pipeline-stages.md:67`:** the bump is pushed by `GITHUB_TOKEN`, then dispatched;
- **SPEC Constraints "Credentials" (l.168) and the agent-Apps bullet (l.147):** an environment secret; agent Apps excluded from CiCd and Builds; the nightly pre-dispatch check as an extra control;
- **SPEC CAP-8 success 4:** in complete mode, the shipped SHA was drift-checked when its draft was created.

## Checked and holding

- Script check: 21/21 ADs have Binds, Prevents and Rule; every `AD-n` reference resolves; the capability map equals the Binds lines in all 16 rows.
- The sequence diagram matches AD-18's seven jobs (dispatch with `delivered-sha`, wait verdicts, scan, bump with the global checks, `bump-push` dispatch, `delivery-wait` with module CI, keepalive).
- **I-1 walk:**
  1. Night N: publish fails after the draft exists.
  2. The bump moves `delivered/<Repo>` and adds an optional knob.
  3. Night N+1: completion reads only the creating run's artifact, with no drift check, CI check, loader or build at the draft SHA.
  4. It publishes the same bytes.
  5. "Re-run failed jobs" also converges.
- **Supporting checks:**
  - **Container base images:** every module's base image is on `mcr.microsoft.com`, so the `build` job needs no pull pair.
  - **Immutability flag:** the releases API carries `immutable` (Builds v4.44.13: `false`, author `github-actions[bot]`), so the AD-10 acceptable-tag test can be implemented.
  - **uv lock:** `uv lock --script` plus `uv run --locked --script` works and fails on a stale lock (scratch test).
- **Ordering conditions still met by `stories.yaml`:**
  - agent-App exclusion, rulesets and immutable releases come before the first CiCd-agent change and the first rewritten release (story 1 before 2 and 3);
  - the perimeter tag comes before delivery (4 before 7);
  - the `builds-release.yml` rewrite comes before nightly (3 before 8).
