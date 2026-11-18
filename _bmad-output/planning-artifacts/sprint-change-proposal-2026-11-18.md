# Sprint Change Proposal: scoped feedback, decoupled delivery, evidence policy

- **Date:** 2026-11-18
- **Baseline:** review of `81e10620` (current `main` and `origin/main`; nothing has landed since)
- **Mode:** batch (one proposal); **scope:** moderate (new stories plus SPEC and spine amendments, implemented by the developer agent)
- **Status:** approved by the maintainer on 2026-11-18 and applied the same day through a `bmad-spec` update. The small differences from §4.1, §4.4 and §4.5 are listed in `specs/spec-cicd/.memlog.md`. Nothing is implemented or published. Story 28-8 still needs its own approval.
- **Planning structure:** `specs/spec-cicd/SPEC.md` plays the PRD's role and `stories.yaml` is the story order of record. There is no `epics.md` (decided 2026-11-08). This file is the only new artifact.

Durations come from the Actions API for 2026-11-13 to 2026-11-18. Byte counts come from `git ls-tree -r -l`. Every "after" figure is an **estimate** until a hosted run verifies it.

## 1. Issue summary

Delivery treats every change as if it touched the shared policy. A prose or receipt push runs all 26 tool suites. It reads Builds and every module, and it runs module delivery. Those runs fail for reasons unrelated to the change, and they hold up the nightly release barrier. Separately, the nightly bump is gated by tests whose inputs a bump cannot change. Raw investigation output also accumulates in Git with no consumer.

### Findings verified on `81e10620`

| # | Finding | Verification on current main | Fix already landed? |
|---|---|---|---|
| F1 | Prose and evidence pushes run full Delivery: 21.4 min (44215968517) and 24.0 min (44211786728). | `deliver.yml` has no change scope. In validate, tool suites take 1,123 of 1,132 s (26 suites, 757 tests, run serially; `tools/check_global.py:401`). The rest of validate, including 5 anonymous module clones, takes about 9 s. Of 109 completed push runs, 57 changed only prose, receipts or gitlinks. Their median was 17.9 min, 938 runner-minutes in total. | No |
| F2 | An evidence push passed validation, then delivery failed for 4 modules on a Builds HTTP 403 (44087897241). | `tools/delivery_runtime.py:443` reads the Builds release, tag, main and compare endpoints **without a token**. `trusted_state` (`tools/deliver.py:123`) runs twice per module, at preflight and at application, so each run makes about 10 anonymous calls per module. The 403 recurred in 6 delivery failures (43892813161, 43912030042, 43951071774, 44044046242, 44068630104, 44087897241). | No |
| F3 | Other red results on prose pushes. | 11 runs failed AI.Tools' AD-21 ruleset precondition. 13 runs failed global validation on suites that were already broken: `'ci' != ['ci']` in `test_render`, a missing Conversations checkout file, and a nightly controller `TypeError`. | Yes: the precondition and the suites were later fixed. Scoping keeps such breakage out of prose pushes. |
| F4 | The v6.3.0 bump failed on three `test_maintenance.py` tests (44264031228). | `test_maintenance.py:11` uses the enclosing checkout as the owner, and `maintenance.py:123` requires its `origin` remote. `bump.py:59` builds its scratch with `git init` and no remotes. The tests landed 2026-11-17 (`3c285357`), and 44264031228 was the first nightly after them. The bump spent 21.7 of 22.4 min in tool suites. | No; this will recur on the next nightly. |
| F5 | The nightly duplicate scan turned the night red. | The 44264031228 scan failed on unsupported discovery constructs in Conversations and McpCli, not on duplicates. `bump` needs `scan` (`nightly.yml:1507`). | No |
| F6 | The release barrier waits on unrelated Delivery runs. | In 44264031228, `dispatch` waited 18.4 min for the 35-min Delivery run of `81e10620`, a gitlink-and-evidence sync. On 17 Nov the barrier timed out at 30 min behind push and hourly runs, and **no release was dispatched** (`evidence/11/scheduled-20261117-diagnosis.json`). | No |
| F7 | The tracked tree grew from 39.8 MiB (`2ecacbaa`, 2026-11-11) to 515.1 MiB, and from 3,415 to 8,196 blobs. | Evidence directories hold 387.7 MiB (spec evidence 249.1, implementation evidence 138.5). One generated patch is 74.2 MiB. The six 44264031228 archives total 9,725 bytes. The working tree is still modifying an evidence file. | No |
| F8 | A global test imports executable code from story evidence. | `tools/tests/test_g6_host_ports.py:12` imports `evidence/18/qualify-owning-g6.py`. `docs/pre-adoption-publication.md` and story 20 also name approved runners in `evidence/17`, `/18`, `/20` and `/21`. | No |
| F9 | New observation: scheduled "hourly" delivery is sparse. | Only 17 scheduled Delivery runs exist since 2026-11-13, 4–10 h apart. Pushes currently provide most drift repair. | Not addressed here; see §5 risks. |

The 44264031228 release failures for AI.Tools, Conversations, McpCli and Builds are product or release outcomes owned by their stories. They are not part of this correction.

## 2. Impact analysis

- **Spec:** CAP-4 (delivery), CAP-6 (bump), CAP-9 (scan), CAP-13 (nightly), and the Constraint "Nothing runs twice". The MVP and success signals are unchanged.
- **Architecture spine:** AD-3 (global checks), AD-6 (deliver job and Builds reads), AD-18 (bump inputs, scan placement, keepalive). The AD-18 barrier rule stays.
- **Stories:**
  - Completed stories 4-3, 7, 8-2 and 9 are amended in effect by new stories 28-1 to 28-8.
  - Story 11's nightly checkpoint depends on 28-1.
  - Story 20's text and the approved runners for 17, 18, 20 and 21 move in 28-3.
  - Migration stories keep running in parallel.
- **Other files:** `AGENTS.md`, `docs/pre-adoption-publication.md`, `docs/duplicate-scan.md` and `docs/nightly.md`. UX does not apply.
- **Code:**
  - `.github/workflows/deliver.yml` and `nightly.yml`, plus a new `scan.yml`.
  - `tools/validate.py`, `check_global.py`, `bump.py` and `delivery_runtime.py`/`deliver.py` (the trusted controller, not the immutable bootstrap).
  - A new stdlib `tools/change_scope.py`.
  - Tests: `test_validate.py`, `test_maintenance.py`, `test_g6_host_ports.py`, `test_deliver.py`/`test_delivery_runtime.py` and `test_nightly_workflow.py`.

## 3. Recommended approach: direct adjustment, decisions in priority order

Rollback is not viable: the work is completed infrastructure that is in use. An MVP review is not needed. The recommended path is a direct adjustment through eight new stories.

### D1. Scope validation and delivery to the change

**Change classes.** I inspected consumers before classifying anything; the evidence is in parentheses.

| Class | Paths | Consumer evidence |
|---|---|---|
| **Prose/receipt** | `_bmad-output/**`; top-level `docs/*.md`; `README.md`, `AGENTS.md`, `limits.md`, `LICENSE`, `setup/README.md`; agent tooling (`.claude/`, `.agents/`, `.agent/`, `.codex/`, `.cursor/`, `.github/agents/`, `_bmad/`, `.bmad-loop/`); value changes to an existing `references/*` gitlink when `.gitmodules` is unchanged | No tool, test or workflow reads these. The one exception is F8, which 28-3 fixes. Gitlinks: validate checks only that a registered gitlink exists and its mode. CI fills `references/Hexalith.Builds` from Builds main and tags, never from the gitlink value. `bump_push` never changes gitlinks. AD-3 forbids CI from reading submodule checkouts. |
| **Not documentation** | `docs/proposals/**`, `docs/contracts-prerequisites/**`, `tools/tests/fixtures/**` | These are read by `deliver_g6_catalog.py`, the `*contracts_prerequisite*.py` tools and `check_bootstrap`. They are treated as shared. |
| **Module `<Repo>`** | `setup/<Repo>.yml`, `rendered/<Repo>/**`, `rendered/<Repo>-execution/**`, `rendered/<Repo>.perimeter.json` | Each module renders independently (`render.py:583`). No suite reads the repository root's `setup/` or `rendered/`; suites use fixture roots. |
| **Shared** | Everything else: `tools/`, `templates/`, `policies/`, `.github/workflows|actions/`, `builds-version`, `builds-skip`, `.jscpd.json`, `.gitmodules`, added or removed submodules, and any unknown path | Full validation. |

**Baseline.** For a PR, compare the candidate with the PR base. For a push or a scheduled run, compare it with each distinct accepted `delivered/*` commit, using an anonymous `ls-remote` and a blobless depth-1 fetch of CiCd only, and take the narrowest result. Every accepted commit passed the global checks, so a candidate that differs from one only in prose and receipts is equivalent in content to a validated state. This baseline also catches a tools push that was cancelled while pending or went red before a prose push.

**Invariant:** a `delivered/<Repo>` ref advances to a commit only when every input that differs from an accepted commit was covered by that run's checks.

| Option | How | Pros | Cons |
|---|---|---|---|
| A. `paths-ignore` on the push trigger | YAML filter against `before` | No code | A PR check filtered out by path never reports, so a required check waits forever. A cancelled pending run hides its changes. It creates a second list to keep in sync. |
| **B. Classifier against accepted commits (recommended)** | A stdlib classifier at the start of `validate`. `deliver` is skipped on a push whose scope is `none`. | One list, fail-safe default of full, sound against cancellations and red runs, no change to the bootstrap | About 150 lines of code plus tests |
| C. Keep full validation and run suites in parallel | Concurrency inside `run_tool_tests` | Helps shared changes | Prose pushes still contact every repository and still deliver |

**Recommendation: B.** Full validation is unchanged for shared changes. Running suites in parallel is deferred (§5).

**Before and after for the three change types**

| Change type | Checks that run | Repositories contacted | What can block delivery | Duration |
|---|---|---|---|---|
| **Prose/receipt** (PR or push) | **Before:** all global checks, including 26 suites (1,123 s); per-module checks; on push, `deliver`: App preconditions, ref advancement and re-apply for every module.<br>**After:** the classifier; the evidence job (D3a). On push, no `deliver` job. | **Before:** CiCd; Builds (full history and tags, plus API reads); 5 modules through anonymous clones; on push, every registered module through the App, plus about 10 anonymous Builds API calls per module.<br>**After:** CiCd only. | **Before:** suites already broken on `main`, the Builds API 403, or another module's precondition. 12 of the 57 runs failed. The run also holds the nightly barrier.<br>**After:** nothing, because nothing is delivered. Refs stay on an equivalent accepted commit. | 57 runs, median 17.9 min (21.4 and 24.0 cited) → **≤ 1 min (estimate)** |
| **Single-module setup** | **Before:** same as shared.<br>**After:** global checks except suites (render inputs, committed render, bootstrap digest, render reproducibility, schemas and caller interfaces at the pin, acceptable Builds tag, lints), plus per-module checks. `deliver` is unchanged. | **Before:** same as shared.<br>**After:** CiCd; Builds (tags, authenticated API); registered modules for reads. Only modules whose render changed receive a commit. | **Before:** everything listed for prose/receipt.<br>**After:** the affected module's own checks block that module. The shared cheap checks block all modules. Another module's failure blocks only itself, as today. | 2 runs, 24.8 and 44.9 min → **about 3–4 min (estimate)** |
| **Shared template, tool or Builds pin** (or ambiguous) | Unchanged: full. | Unchanged, except that Builds reads are authenticated and made once per tag (D2b). | Unchanged, minus the Builds API 403. | 50 runs, median 18.1 min → unchanged (about 19–21 min) |

**Failures D1 must still catch:**
- A tool, template, policy, workflow or pin change is validated in full before any ref advances, even after a cancelled or red run.
- A setup change cannot advance with an invalid render, schema, caller interface or tag.
- Module drift is repaired by every scheduled run.
- Builds tag acceptability and the online zizmor advisories are rechecked by every scheduled run, which keeps all global checks except the suites.

**Deferred:** narrowing the per-module checks and `deliver` to only the affected module. The immutable bootstrap at `03d130f8` accepts only `{"global","modules"}` (`tools/delivery_bootstrap.py:41`), so omitting a module would report it as failed. Narrowing needs a new bootstrap pin. Those reads cost about 0.3 s per module and write nothing.

### D2. Remove accidental release coupling

| Change | Failure it must still catch |
|---|---|
| **2a. Self-contained maintenance fixture (28-1).** The test builds its own owner repository (committed `tools/maintenance.py`, policy and templates, with an explicit `origin`) and its own target clone. The tests have three inputs: `tools/maintenance.py`, `policies/maintenance/**`, and Builds history at the frozen 4.44.x base `3c809618`. `bump_push` accepts only changes to `builds-version` and `rendered/**`, so **a bump can never change these inputs, and these tests should never block a bump.** They block, through full validation, any PR or push that changes their inputs. | A maintenance render from a foreign owner or target origin, a changed executing tool, or a changed policy hash still refuses before writing. |
| **2b. One authenticated Builds lookup per delivery run (28-2).** Each distinct tag is verified once per run, and the result is kept in the run's delivery state. Each slot runs as a separate child process, so an in-memory cache would not survive between slots. The reads use an App token the controller already holds: CiCd-scoped, or else module-scoped. The bootstrap forwards only `CICD_TOKEN` and `MODULE_TOKEN`, so the job's `GITHUB_TOKEN` is unavailable without a new bootstrap. | A draft, mutable, non-`github-actions[bot]` or non-ancestral tag still stops advancement and application for every module on it. An API refusal still stops writes. |
| **2c. Pin-scoped bump checks (28-5).** The bump runs every global check that reads the pin, plus only the suites that read `builds-version`: today `test_render`, `test_render_legacy` and `test_conversations_qualification`, about 87 s. The bump commit's delivery still runs full validation. | A Builds release that breaks rendered callers or the render. This is the `test_render` `'ci' != ['ci']` failure seen after a pin change in runs 44050937825, 44063032613 and 44064902576. It also catches an unacceptable tag. |
| **2d. Duplicate scan in its own scheduled workflow (28-7).** See the options below. | A fragment in two modules' custom actions or called scripts, and an unsupported discovery construct. Both still fail and name the code, in their own run. |
| **2e. Barrier: keep the rule and shorten what it waits on.** See the options below. | A delivery that pushes module commits or advances refs between dispatch and the release's resolve step. |

Scan placement:

| Option | How | Pros | Cons |
|---|---|---|---|
| Keep in nightly | Status quo | No work | Discovery limits turn the release night red. The bump waits for the scan. |
| **Own `scan.yml` (recommended)** | Same job, daily schedule plus manual dispatch; keepalive enables it; the bump needs only `publish-ready` | The night's verdict reflects only releases and the bump. The scan can be rerun alone. | CAP-9, AD-18 and the docs need edits. One more workflow to keep enabled. |
| Run in hourly delivery | Inside `deliver.yml` | Runs often | Reads every module every hour for no added protection |

Barrier:

| Option | How | Pros | Cons |
|---|---|---|---|
| **B1. Keep the rule (recommended)** | D1 shortens prose runs to about 1 min and scheduled runs to about 3 min (estimates). | No change to code that is designed to fail closed | A full-scope push at dispatch time still costs up to about 21 min. |
| B2. Wait only while a run's `deliver` job can still start | Inspect each run's jobs | Small gain | A run still in validate may write later, so it must still be waited on. |
| B3. Wait only for runs whose render changes an adopted module | Read run scopes | Narrowest wait | Scope isn't readable from a running job; adds complexity. |

Revisit B3 only if a hosted night still loses dispatch to the barrier after 28-4.

### D3. Evidence policy

Recurring outputs at `81e10620`. The categories overlap and their sizes are heuristic.

| Output (bytes now) | Consumer | Decision it supports | Home |
|---|---|---|---|
| Story records and checkpoint verdicts (Markdown, about 5.4 MiB) | Maintainer; the next agent session | Accepting a story, AC or checkpoint | Git |
| Source identity: base/head SHAs, tree/blob ids, gitlinks, Builds tag and commit, digests | Pre-adoption publication binding; audits | "This exact source was qualified or published" | Git, as small receipts |
| Hosted run results | Checkpoints such as story 11's real night; verdict review | Accepting a release or a night | Git keeps the run URL plus the artifact name, id and digest. The content stays in Actions for 90 days. |
| Copies of Actions receipts (`scheduled-*-hexalith-nightly-*.json`, `delivery.json`) | Same as above | Nothing beyond the link | Actions only; stop copying them |
| Receipts read by later jobs (`dispatch.json` → `wait`/`publish-ready`, `delivery.json` → `delivery-wait`, bump artifact → `bump-push`); about 9.5 KiB per night | Nightly jobs | Dispatch, publication, bump push | Actions; unchanged |
| Delivery inputs that look like docs (`docs/proposals/**`, fixtures) | Delivery tools | Narrow corrections | Git; classed as shared |
| Raw logs and agent transcripts (27.5 MiB, 1,025 files; `*.log` is gitignored but was force-added) | Debugging | None that lasts | Actions logs; locally under `$TMPDIR`, with a one-line result in the record |
| Tree and inventory dumps (184.6 MiB) | Proving an owned tree unchanged or a cleanup complete | "Unchanged", "complete" | Git keeps tree/blob ids, the result and counts. The dump goes only to an Actions artifact. |
| Generated patches and diffs (120.0 MiB, including the 74.2 MiB `cicd-merged-candidate.patch`, which nothing references except its own generator) | Reviewing what was pushed | "What was published" | Git keeps the base/head SHAs; `git diff` reproduces the patch. |
| Repeated attempt snapshots (`fix`…`fix10-eventstore-pre-adoption.json` at 2.8 MiB each; `attempt-*/`, `iteration-*/` at about 102.6 MiB) | Debugging | Only the final attempt is a decision | Git keeps the final receipt, the attempt count and the failure class. |
| Packages and test results (11.9 MiB) | None in Git | Package identity | Git keeps the id, version and SHA-256. |
| Executable fixtures and runners (8.1 MiB, mostly historical copies) | `test_g6_host_ports`; the approved pre-adoption runners | Pre-adoption publication | Live ones move to `tools/qualification/` (28-3). |

**D3a. Stop new growth (28-6).**

| Option | How | Pros | Cons |
|---|---|---|---|
| Rule plus `.gitignore` only | Written policy | Trivial | Has already failed: 1,025 ignored-kind files were force-added. |
| **Rule plus a non-verdict `evidence` job (recommended)** | A job in `deliver.yml` on PRs and pushes rejects new or modified `_bmad-output/` files over 256 KiB, raw kinds and executables. It is outside `needs` and outside the verdict. | Catches force-adds. Costs seconds. Never blocks delivery. The largest legitimate record today is 138 KiB. | Red after the fact on direct pushes to `main`. |
| Pre-commit hook | Local hook | Catches files before they are committed | A non-goal in the spec, and easy to bypass |

**D3b. Remove existing files (28-8). This is a separate approval, and history is not rewritten.**

| Option | How | Pros | Cons |
|---|---|---|---|
| R0. Keep | Nothing | No effort | Every depth-1 checkout keeps carrying 515 MiB; searches keep returning noise. |
| **R1. Remove raw kinds that nothing references (recommended)** | Delete from HEAD the logs, dumps, patches, binaries and superseded attempts that no tracked file outside evidence references | About 280 MiB smaller (estimate). Records, receipts and referenced files stay. | Links inside evidence records to removed files resolve only through history. |
| R2. Remove the evidence trees of closed stories | Delete whole directories | About 388 MiB smaller | Deletes decision records and breaks `docs/` links. |

**Prerequisite:** 28-3 moves the executable fixtures out first.

## 4. Detailed change proposals

### 4.1 `stories.yaml`: insert after story `11`, through a `bmad-spec` update

Acceptance criteria are copied into `stories/<id>-<slug>.md` at plan time.

```yaml
- id: "28-1"
  title: "Self-contained maintenance test fixture"
  description: >-
    test_maintenance.py builds its owner repository and target clone in its
    own temporary directory, so it passes from actions/checkout and from the
    bump's remote-less scratch checkout (CAP-6; AD-18).
  invoke_dev_with: >-
    Work in this repo. Keep every refusal in tools/maintenance.py unchanged.
- id: "28-2"
  title: "One authenticated Builds lookup per delivery run"
  description: >-
    The deliver controller verifies each distinct Builds tag once per run with
    an App token it already holds, and reuses the result for preflight and
    application of every module (CAP-4; AD-6, AD-10).
  invoke_dev_with: >-
    Work in this repo: tools/deliver.py and tools/delivery_runtime.py only;
    the immutable bootstrap and its pin stay unchanged.
- id: "28-3"
  title: "Executable fixtures out of evidence"
  description: >-
    Move every executable with a live consumer out of evidence directories
    into tools/qualification/, and add a test that no tracked file outside the
    prose/receipt set references _bmad-output/ (CAP-4; AGENTS.md).
  invoke_dev_with: >-
    Work in this repo. Keep runner logic unchanged apart from paths; update
    docs/pre-adoption-publication.md and story 20's text.
- id: "28-4"
  title: "Change-scoped validation and delivery"
  description: >-
    Classify each candidate against the PR base or the accepted delivered
    commits as none, module or full; run only the checks a class can affect;
    start no delivery for a prose/receipt push (CAP-4; AD-3, AD-6).
  invoke_dev_with: >-
    Work in this repo: tools/change_scope.py (stdlib), validate.py,
    check_global.py, deliver.yml, test_validate.py. A missing or unknown scope
    is full. Record hosted run links in the story file, not in a new bundle.
- id: "28-5"
  title: "Pin-scoped bump checks"
  description: >-
    The nightly bump runs the global checks and suites that read the Builds
    pin; validation of the bump commit stays full (CAP-6; AD-3, AD-18).
  invoke_dev_with: >-
    Work in this repo: check_global.py suite selection, bump.py.
- id: "28-6"
  title: "Evidence policy and growth stop"
  description: >-
    Write the evidence rule in AGENTS.md and add a non-verdict evidence job to
    deliver.yml that rejects new raw, executable or over-256-KiB files under
    _bmad-output/ (CAP-4; AGENTS.md).
  invoke_dev_with: >-
    Work in this repo. The job holds no secret and is not a need of deliver.
- id: "28-7"
  title: "Independent duplicate scan"
  description: >-
    Move the nightly scan job into scan.yml on its own daily schedule and
    manual dispatch; the bump needs only publish-ready (CAP-9; AD-18).
  invoke_dev_with: >-
    Work in this repo. Same tool, config and report schema; keepalive enables
    scan.yml.
- id: "28-8"
  title: "Remove raw evidence from the tree"
  description: >-
    After 28-3 and 28-6, delete from HEAD the raw evidence kinds that no
    tracked file outside evidence references; no history rewrite.
  done_checkpoint: true
  invoke_dev_with: >-
    Requires its own maintainer approval before starting.
```

**Acceptance criteria**

- **28-1**
  1. The suite creates an owner repository from the candidate's committed `tools/maintenance.py`, `policies/maintenance/story-2-8.json` and the templates that policy names, with `origin` set to `https://github.com/Hexalith/Hexalith.CiCd.git`. It reads no remote, branch or config of the enclosing checkout.
  2. It passes under `actions/checkout` and in a reproduced bump scratch (`git init`, no remotes).
  3. The foreign-origin, tool-digest and policy-hash refusals still fail before any write.
  4. Hosted: the next nightly bump does not fail in `test_maintenance.py`.
- **28-2**
  1. Each distinct tag is read once per run. A 17-module fixture issues one release read per tag.
  2. The reads carry the CiCd-scoped App token, or else the module-scoped one. They are anonymous only when neither was minted, and then no write is possible anyway.
  3. All existing acceptability checks and fail-closed outcomes stay. A refusal reports "Builds release unverified (HTTP n)".
  4. Hosted: no Builds 403 across a week of push and scheduled deliveries. If GitHub refuses the CiCd-scoped token for Builds reads, report it and do not widen the token.
- **28-3**
  1. `evidence/18/qualify-owning-g6.py` moves to `tools/qualification/`, and `test_g6_host_ports.py` imports it from there.
  2. The approved runners still in force move to `tools/qualification/pre-adoption/<module>/`, with their default output outside `_bmad-output/`:
     - Folders: `evidence/17/verify-product-candidate.py`, `verify-final-candidate.py`
     - Projects: `evidence/18/local-package-build.py`
     - EventStore: `evidence/20/pre-adoption-verify.py` and its test
     - Parties: `evidence/21/publication/qualify-push.py`
  3. `docs/pre-adoption-publication.md` and story 20 point to the new paths.
  4. A tool test fails if a tracked file outside the prose/receipt set references `_bmad-output/`, or if a suite reads `setup/` or `rendered/` from the repository root.
- **28-4**
  1. The classifier follows D1's classes and baseline. It is full on `workflow_dispatch`, with no accepted commit, with an unreadable baseline, or when `.gitmodules` changes.
  2. `none` on a PR or push: no Builds checkout, no module clone and no suites, and the `validate` check completes green. `none` on a push also starts no `deliver` job, mints no App token and leaves the refs unchanged.
  3. `module`: global checks except suites, plus per-module checks. `deliver` is unchanged.
  4. A scheduled `none` run skips only the suites. Re-apply, the 26-hour freshness check, the tag-acceptability check and the lints remain.
  5. A missing or malformed scope is full.
  6. Tests cover each of these cases:
     - prose after a red tools push → full
     - prose after a cancelled pending tools push → full
     - one module's setup plus render → module
     - `builds-version` → full
     - `templates/` → full
     - `docs/proposals/` → full
     - gitlink only → none
     - `.gitmodules` → full
  7. Hosted: one run each of a prose PR, a prose push, a single-module setup push and a tools push. Record durations and contacted repositories against §3.
- **28-5**
  1. `check_global.py` takes a suite selection (`all` or `pin`). `bump.py` uses `pin`.
  2. The `pin` suite list is explicit. A tool test fails if an unlisted suite reads `builds-version` from the repository root.
  3. `bump_push`'s substitution and newest-tag checks are unchanged.
  4. Hosted: the bump job runs in ≤ 6 min (estimate) and does not run the maintenance tests.
- **28-6**
  1. `AGENTS.md` carries the text in §4.4.
  2. The `evidence` job rejects new or modified files under `_bmad-output/` that are over 256 KiB, a raw kind (`.log`, `.jsonl`, `.patch`, `.diff`, `.nupkg`, `.snupkg`, `.trx`, `.binlog`, `.zip`, `.gz`, `.tar`), or executable (`.py`, `.js`, `.mjs`, `.ps1`, `.sh`). Unmodified existing files are not flagged.
  3. `docs/pre-adoption-publication.md`'s "write fresh results to a new evidence directory" becomes "write one receipt (revisions, tree ids, digests, results); keep raw output under `$TMPDIR`."
  4. Target: tracked `_bmad-output/` bytes grow by ≤ 5 MiB per week. The baseline is about 59 MiB per day.
- **28-7**
  1. `scan.yml` runs the existing job.
  2. `nightly.yml` no longer has a `scan` job.
  3. `bump` needs `[publish-ready]`.
  4. `keepalive` enables `scan.yml`.
  5. Duplicates and unsupported discovery fail `scan.yml` and name the code.
- **28-8**
  1. Delete only unreferenced raw kinds.
  2. Use one commit per evidence root, naming the last commit that contains the files.
  3. Measure the tracked-tree reduction with `git ls-tree`; the estimate is about 280 MiB.

### 4.2 SPEC edits

- **CAP-4, new success bullet.** "Validation covers what changed. A prose or receipt change completes without reading Builds or any module. A change to one module's setup checks that module and the shared checks it reads. Any other or ambiguous change runs every check. A push whose changes against an accepted commit are only prose and receipts starts no delivery. Scheduled delivery still re-applies every accepted render."
- **CAP-9.**
  - OLD: "The nightly scan fails, and names the code, when a fragment appears in the custom actions of two or more modules."
  - NEW: "The daily scan, which runs in its own workflow, fails and names the code when a fragment appears in the custom actions of two or more modules."
- **Constraints, "Nothing runs twice", new bullet.** "Tool suites run when their inputs change; the nightly bump runs only the checks that read the Builds pin."

### 4.3 Architecture spine edits

- **AD-3, Global checks.**
  - OLD: "They are one CiCd script, which `validate` and the nightly `bump` run identically, …"
  - NEW: "They are one CiCd script with no secret other than the job's read-only `GITHUB_TOKEN`. Tool tests run only when the candidate differs from every accepted commit outside the prose/receipt and module-input sets. The nightly `bump` runs the checks and suites that read `builds-version`. A ref advances only to a commit whose every differing input was covered by its run's checks."
- **AD-6.**
  - OLD: "`deliver`, on `main` only, after `validate` whatever its result"
  - NEW: "… whatever its result, except on a push whose validation scope is `none`"
  - In step 3, OLD: "confirm with stdlib API reads that it is an acceptable tag"
  - NEW: "confirm once per tag per run, with authenticated stdlib API reads, that it is an acceptable tag"
- **AD-18.**
  - Remove item 4 (`scan`) and add "The duplicate scan runs in `scan.yml` on its own schedule."
  - Item 5: OLD "after `publish-ready` and `scan` whatever their results … runs the AD-3 global checks"; NEW "after `publish-ready` whatever its result … runs the AD-3 pin checks".
  - Item 8: the enable API covers `scan.yml`.
  - The barrier text is unchanged.

### 4.4 `AGENTS.md` (CiCd's own file), new section

> **Evidence.** Git keeps decisions and identities, not raw output. A story record keeps the decision, exact source revisions (commit, tree and blob ids), digests, and run and artifact links. Raw logs, tree dumps, generated patches, packages, test results and earlier attempts stay in the producing Actions run or under `$TMPDIR`; record their digest and a one-line result instead. Code that tests or procedures execute lives under `tools/`, never under `_bmad-output/`. Files added under `_bmad-output/` stay under 256 KiB.

### 4.5 Story 20 text

- OLD: "Use the EventStore-only evidence/20 pre-adoption verifier"
- NEW: "Use the EventStore-only pre-adoption verifier in tools/qualification/pre-adoption/eventstore/ (moved by 28-3)"

## 5. Implementation sequence and handoff

| Step | Story | Why it goes here | Effort | Risk |
|---|---|---|---|---|
| 1 | 28-1 | Unblocks the next nightly bump; the smallest change | Low | Low |
| 2 | 28-2 | Removes the most frequent cross-module delivery blocker | Low | Low: trusted controller only |
| 3 | 28-3 | Makes D1's prose class sound and makes cleanup possible | Low–medium | Low |
| 4 | 28-4 | Priority 1. Depends on step 3. | Medium | Medium; mitigated by the default to full |
| 5 | 28-5 | Shortens the bump once its suites are deterministic | Low | Low |
| 6 | 28-6 | Stops growth. Can run in parallel with steps 4–5. | Low | Low |
| 7 | 28-7 | Separates the scan's verdict from the night's | Low | Low |
| 8 | 28-8 | Cleanup, under its own approval | Low–medium | Low |

**Work that can be retired:**
- Full suite runs and `deliver` jobs for prose and receipt pushes (about 940 runner-minutes over the 5-day window; estimate).
- Duplicate Builds lookups per module.
- The nightly `scan` job and the bump's dependency on it.
- Pin-independent suites in the bump.
- The evidence import in `test_g6_host_ports`.
- The habit of committing logs, dumps, patches, packages, test results, attempt snapshots and copies of Actions receipts.
- The instruction "write fresh results to a new evidence directory".

**Deferred, outside this correction:**
- Per-module `deliver` narrowing (needs a new bootstrap).
- Parallel tool suites (would cut full-scope validation to about 5 min; estimate).
- Barrier option B3.

**Risks:**
- F9: scheduled delivery ran 17 times in 5 days. After 28-4, prose pushes no longer repair drift as a side effect, and AD-8's one-hour bound is already unmet by GitHub's scheduler. This needs its own decision.
- 28-2 depends on GitHub accepting a CiCd-scoped installation token for public Builds reads. Its acceptance criteria require reporting a refusal, not widening the token.

**Handoff (moderate scope):**
1. The maintainer approves this proposal.
2. A `bmad-spec` update applies §4.1–4.5.
3. `bmad-build` runs the stories in the order above.
4. The maintainer separately approves 28-8 before it starts.

**Success criteria** (hosted; targets are estimates):
- A prose PR completes `validate` in ≤ 1 min with no Builds or module fetch, and merging it creates no `deliver` job.
- A single-module setup push finishes in ≤ 5 min, and only that module receives a commit.
- Shared changes keep full validation.
- The next bump finishes in ≤ 6 min and never runs the maintenance tests.
- The nightly verdict excludes the scan.
- No Builds 403 occurs for a week.
- Tracked `_bmad-output/` growth stays ≤ 5 MiB per week.

**Checklist status:**
- Done: 1.1–1.3, 2.1–2.5, 3.1, 3.2, 3.4, 4.1–4.4, 5.1–5.5, 6.1, 6.2.
- Not applicable: 3.3 (UX); 6.4 (no `sprint-status.yaml`; `stories.yaml` is the order of record).
- Done after approval: 6.3 (approved 2026-11-18); 6.5 (handoff below).
- Next: a `bmad-spec` update applies §4.1–4.5; then `bmad-build` runs 28-1.
