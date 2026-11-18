# Sprint Change Proposal: on-demand nightly runs and module-scoped nightly acceptance

- **Date:** 2026-11-18
- **Trigger:** "we should be able to test nightly CI/CD without waiting the night" (maintainer, during story 11's last task).
- **Baseline:** `81e10620` (`main`). The approved [scoped feedback proposal](sprint-change-proposal-2026-11-18.md) is being applied in the working tree (stories 28-1 to 28-8, SPEC, spine and `AGENTS.md` edits, uncommitted). This proposal builds on it and edits none of its decisions.
- **Mode:** batch. **Scope chosen by the maintainer:** "dispatch counts" — no new pipeline mode. A module subset input and a no-publish rehearsal were considered and deferred (§3).
- **Scope classification:** moderate — one new story and wording changes to the nightly criterion of 15 stories, through a `bmad-spec` update and the developer agent.
- **Status:** approved by the maintainer on 2026-11-18 ("yes"), with D2's default kept: Builds' own release row is recorded and does not decide story 11's pilot checkpoint. Handoff progress: steps 2 and 3 of §5 are applied in the working tree, not committed.
  - The CAP-14 intent also now reads "once per nightly run" (maintainer, "apply recommended").
  - The `docs/nightly.md` section in §4.4 is left to story 29-1 (its AC 9), so the doc never names a tool that does not exist yet.
  - Steps 4 and 5 are pending.
- **Planning structure:** `specs/spec-cicd/SPEC.md` plays the PRD's role and `stories.yaml` is the order of record; there is no `epics.md`.

## 1. Issue summary

Story 11's pilot checkpoint and the last criterion of every migration story wait for a `schedule` event of `nightly.yml`, and three stories forbid a manual dispatch. GitHub's scheduler, not the pipeline, sets the pace: one attempt per calendar day, 7–9 hours late, and any other module's red result spoils the attempt.

| # | Finding | Evidence (read-only API and repository reads, 2026-11-18) |
|---|---|---|
| N1 | Scheduled runs arrive 7–9 h late, or not at all. | Only 3 scheduled nightly runs exist for the `17 2 * * *` cron: 43699255217 (15 Nov 09:26), 43842471669 (16 Nov 09:44), 44067556763 (17 Nov 10:44). None for 18 Nov by 09:49 UTC. Scheduled `deliver.yml` (`47 * * * *`) ran 17 times in 5 days. |
| N2 | A dispatched run is the same nightly. | No `nightly.yml` job reads the event; only the opt-in `qualify-bump` input changes job selection (`if:` at lines 24, 595, 886, 1448, 1508, 1592, 1659, 1825). `tools/nightly.py:40`, `nightly_delivery_wait.py:49`, `nightly_keepalive.py:26` and `bump_runtime.py:78` accept both events. Module releases are always started by `workflow_dispatch`. Delivery freshness (`tools/deliver.py:82`) counts the latest run of either event. `docs/nightly.md:3` and CAP-15 already allow a dispatch on `main` from an interactive CiCd session. `test_nightly_workflow.py:284` already covers schedule and manual selection. |
| N3 | The "scheduled" requirement exists only in story text. | Story 11: AC at `spec-11…md:72` and `evidence/11/planning.md:205` ("manual dispatch or fixtures cannot substitute"). Frozen prohibitions: `spec-12…md:26`, `spec-13…md:26`, `spec-17…md:25`. "Scheduled"/"genuine" wording in 12 more story specs, `stories.yaml` (11, 20) and `docs/pre-adoption-publication.md:89`. No SPEC or spine rule requires a schedule event. |
| N4 | A dispatched run already shows the pilots green. | 44264031228 (`workflow_dispatch`, 08:05–09:10 UTC, source `81e10620`): Commons release 44266704721 — Release CodeQL (csharp) success, published `3.0.1`, scan row pass (4 files). Poly release 44266726524 — CodeQL success, nothing to release, scan row pass (0 files). Duplicates: 0. |
| N5 | A night-wide red verdict hides module results. | The same run is red on the AI.Tools, Conversations, McpCli and Builds releases, on Conversations/McpCli local-script discovery in the scan, and on the `v6.3.0` bump (F4 of the approved proposal, story 28-1). Story 11's authenticator requires the whole scan to pass, so no module can be accepted while any other is red. 16 and 17 Nov were lost the same way (Builds 403; delivery barrier). |
| N6 | Each night needs new executable evidence. | `evidence/11/authenticate-scheduled-20261117.py` (601 lines) and `-20261118.py` (582 lines), plus an observer, a systemd unit and a timer per night. The approved evidence policy keeps executed code under `tools/`. |

Issue type: failed approach (acceptance bound to an external timer), compounded by a platform limitation (GitHub schedule latency).

## 2. Impact analysis

- **Spec:** CAP-13 gains two success bullets (on-demand run; module row). CAP-16's done criterion and the bump Constraint are reworded. The success signal is unchanged: in steady state releases are still started by the scheduler with nobody touching them. MVP unchanged.
- **Architecture spine:** AD-18's first rule line only. No component, contract or token changes.
- **Stories:**
  - Story 11: checkpoint wording, AC and task. Story 11 still also needs 28-1, because the bump fails until then.
  - Stories 12 and 13: dependency on story 11 and their prohibitions.
  - Stories 14–18, 20–22 and 26: nightly-criterion wording only. Stories 19, 23 and 25 already say "next nightly" and need no edit.
  - New story 29-1. Stories 28-1 to 28-8 are unchanged. After 28-7 the scan row comes from `scan.yml`, which 29-1 handles.
- **Docs:** `docs/nightly.md` (new section) and `docs/pre-adoption-publication.md:89`.
- **Code:** a new read-only `tools/nightly_acceptance.py` with tests, plus one assertion added to `tools/tests/test_nightly_workflow.py`. No change to `nightly.yml`, the controllers, Builds or module templates.
- **Operations:** the 18 Nov story 11 observer and its systemd timer (`hexalith-cicd-story11-20261118`) become optional. Keep it until story 11 is accepted, then disable it. No new per-night observers.
- **UX:** not applicable.

## 3. Recommended approach: direct adjustment

| Path | Verdict |
|---|---|
| **Direct adjustment (recommended)** | Viable. Wording changes plus one small read-only tool. Effort low–medium, risk low. |
| Rollback | Not viable: the pipeline already supports dispatch, so there is nothing to undo. |
| MVP review | Not needed: the goals and success signal are unchanged. |

### D1. A dispatched nightly counts as a nightly

**How it works:** a `workflow_dispatch` of `nightly.yml` on `main` with `qualify-bump` false is a nightly run, wherever a story or check needs one.
- **Who starts it:** the maintainer, or an interactive CiCd session whose CiCd-agent token holds Actions write on CiCd (otherwise the session asks the maintainer). Never a module agent: GitHub refuses it (CAP-7).
- **Before dispatching:** check that no `nightly.yml` run is queued or in progress, because the `nightly` group replaces an older pending run. Plan no CiCd push for 30 minutes: dispatch waits up to 30 minutes for `deliver.yml` and lost 17 Nov to that wait.
- **Duration:** about 65 minutes end to end (44264031228).

**Pros:**
- Testable any time of day.
- No pipeline change.
- The same jobs, tokens and fail-closed checks run as at 02:17.

**Cons:**
- A test run is real. It releases, publishes and may bump, exactly as the 02:17 run would. Dispatching again without a fix only produces "nothing to release".
- Per-story acceptance no longer proves that the cron fires (see D4).

### D2. A module's nightly outcome is its own row

**How it works:** module M's outcome in a nightly run is decided by M's own rows only:
- M is eligible and dispatched.
- Its release run concluded `success` with outcome `published` or `nothing`. `ready` counts only if `publish-ready` published it; `disabled` fails.
- Every Release CodeQL job in that run succeeded, unless M declares no CodeQL languages.
- M's scan row passes for the dispatched head.
- When the run pushed a bump, M's `delivery-wait` result is green.

Other modules' rows, Builds' release row and the run's overall verdict are recorded and never change M's outcome. The night's own verdict is unchanged: it still fails when any row fails.

**Story 11's pilot checkpoint also requires the shared machinery:**
- The bump reports either no change, or a pushed candidate whose `delivery-wait` is green.
- `keepalive` passes.

Builds' own release row is recorded but does not decide the pilot checkpoint, because it belongs to Builds' stories. **Decision point:** say so if you want it to decide.

**Pros:**
- One module's red row no longer blocks another module's story.
- The verdict follows the rows `nightly.json` already reports.

**Cons:**
- The checks that apply only to story 11 must be stated explicitly.

### D3. One read-only acceptance tool (story 29-1)

**How it works:** `tools/nightly_acceptance.py` authenticates one run, its artifacts and the linked release runs, then prints D2's per-module verdict. It replaces the per-night observers, authenticators and systemd units.

**Pros:**
- One tested implementation for 15 stories.
- Story evidence becomes a small receipt.

**Cons:**
- About 300 lines plus fixture tests. It generalizes the checks in `authenticate-scheduled-20261118.py`.

### D4. Scheduler health: no change

Dispatched runs keep delivery's 26-hour freshness check fresh, so a cron that stopped firing is masked only while people dispatch. Keepalive still enables both schedules every night. Requiring a `schedule` event in the freshness check would turn delivery red whenever GitHub runs late: 17 Nov's run started 25 h after 16 Nov's. The approved proposal's F9 already flags scheduler sparsity for its own decision.

**Deferred (maintainer decision, 2026-11-18):**
- A module subset input. It would change the dispatch, wait and publish controllers.
- A no-publish rehearsal mode. It would need a Builds release and redelivery to every module.

## 4. Detailed change proposals

### 4.1 `stories.yaml` (through a `bmad-spec` update)

**Insert after `28-8`:**

```yaml
- id: "29-1"
  title: "On-demand nightly acceptance"
  description: >-
    A read-only tool judges one nightly.yml run on main, scheduled or
    dispatched, and reports each module's own verdict, so stories accept a
    nightly outcome without waiting for 02:17 UTC (CAP-13, CAP-16; AD-18).
  invoke_dev_with: >-
    Work in this repo: tools/nightly_acceptance.py (stdlib plus the caller's
    gh), its tests, test_nightly_workflow.py and docs/nightly.md. Generalize
    the checks of evidence/11/authenticate-scheduled-20261118.py without
    importing it. Read-only: no dispatch, rerun, mint or credential switch.
    Acceptance criteria: story 29-1 in section 4.1 of
    _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md.
```

**Acceptance criteria for 29-1:**
1. `python3 tools/nightly_acceptance.py --run <id> --module <Repo> [--module …] [--checkpoint pilot] [--receipt <path>]` reads only through the caller's `gh` profile and writes nothing remote.
2. It accepts only a completed `nightly.yml` run on `main` whose event is `schedule` or `workflow_dispatch` and whose `dispatch` job ran, which proves `qualify-bump` was false. It rejects:
   - qualify-bump runs;
   - other workflows or branches;
   - unfinished runs;
   - any artifact whose downloaded bytes do not match its API digest.
3. Each module's verdict follows D2.
   - The scan row comes from the run's `scan` job, or, after 28-7, from the first completed `scan.yml` run on `main` whose row for that module covers the dispatched head.
   - A module with CodeQL languages in its committed setup fails when no Release CodeQL job succeeded.
4. Other modules' rows, Builds' row and the run's overall conclusion are reported and never change a module's verdict.
5. `--checkpoint pilot` also requires the bump report to be `no-change`, or a pushed candidate with a green `delivery-wait`, and `keepalive` to pass.
6. The JSON verdict goes to stdout. `--receipt` writes at most 16 KiB of identities only: run id, attempt, event and head; artifact ids and digests; per-module verdicts and reasons. It writes no logs.
7. Fixture tests cover:
   - schedule and dispatch both accepted;
   - qualify-bump, non-main, other-workflow, in-progress and digest-mismatch runs rejected;
   - `published` and `nothing` pass;
   - `disabled`, failed, and `ready` not published by this run fail;
   - a failed or skipped CodeQL job fails;
   - a module's own scan error fails it, while another module's scan error or release failure leaves it passing;
   - the pilot checkpoint fails on a failed bump (the 44264031228 shape).
8. `test_nightly_workflow.py` asserts that every job's selection is identical for `schedule` and for `workflow_dispatch` with `qualify-bump` false.
9. `docs/nightly.md` carries §4.4.
10. Hosted: on 44264031228 the tool reports Commons and Poly pass and the four other targets fail. `--checkpoint pilot` fails, naming the `v6.3.0` bump.

**Story 11 description:**
- OLD: "The pause after this story is for watching one real night: CodeQL, release, Builds bump, and delivery."
- NEW: "The pause after this story is for watching one real nightly run, scheduled or dispatched (CAP-13): the pilots' CodeQL and releases, the Builds bump, and delivery."

**Story 20 `invoke_dev_with`:**
- OLD: "scheduled-night publication or valid no-release result"
- NEW: "nightly-run (CAP-13) publication or valid no-release result"

### 4.2 SPEC edits

**CAP-13, new success bullets** (after "`HEXALITH_RELEASE_PUBLISH_ENABLED` set to `false` …"):
- "A `workflow_dispatch` of `nightly.yml` on `main` with `qualify-bump` false runs the same jobs as the 02:17 UTC schedule. Anything that needs a nightly outcome may start one instead of waiting for the night. The maintainer or an interactive CiCd session starts it, never a module agent."
- "A module's nightly outcome is its own row: its eligibility, its release run's CodeQL and release-or-nothing result, its scan row and, after a bump, its delivery. Other rows don't change it. The night still fails when any row fails."

**CAP-16 success:**
- OLD: "It is done when its CI is green and its next nightly release succeeds or reports nothing to release."
- NEW: "It is done when its CI is green and its own outcome in a nightly run started after its adoption (CAP-13), scheduled or dispatched, passes: CodeQL passes and the release succeeds or reports nothing to release."

**Constraints, Builds pin:**
- OLD: "The automatic bump runs at most once a night."
- NEW: "The scheduled bump runs once a night; a dispatched nightly (CAP-13) may bump again the same day."

### 4.3 Architecture spine, AD-18

**Rule, first line:**
- OLD: "`nightly.yml` runs at 02:17 UTC as the jobs below."
- NEW: "`nightly.yml` runs at 02:17 UTC, or when dispatched on `main`, as the jobs below. No job reads the triggering event; only the `qualify-bump` input changes which jobs run."

### 4.4 Docs

**`docs/nightly.md`, new section after the opening section, "Testing on demand":**

> Dispatch `nightly.yml` on `main` to test the nightly without waiting for 02:17 UTC; it runs the same jobs and really releases, publishes and bumps. First confirm that no `nightly.yml` run is queued or in progress, and plan no CiCd push for 30 minutes, which is the dispatch barrier. Only the maintainer or an interactive CiCd session dispatches; a module agent cannot. A run takes about an hour. Judge it with `python3 tools/nightly_acceptance.py --run <id> --module <Repo>`: each module's verdict depends only on its own rows. Story 11 adds `--checkpoint pilot`. Record the receipt, not logs. Dispatching again without a fix only reports nothing to release.

**`docs/pre-adoption-publication.md:89`:**
- OLD: "the scheduled nightly acceptance outcome"
- NEW: "the nightly acceptance outcome (CAP-13)"

### 4.5 Story specs (`_bmad-output/implementation-artifacts/`)

`F` marks text inside `<frozen-after-approval>`. Approving this proposal is the human renegotiation those blocks require. Each edited spec gets a Spec Change Log line citing this proposal. Implementation Notes and review logs are history and stay unchanged.

| File:line | F | OLD | NEW |
|---|---|---|---|
| `spec-11…:65` | | "the scheduled night" | "one nightly run (CAP-13)" |
| `spec-11…:72` | | "when one real scheduled nightly finishes, then CodeQL, releases or valid no-release outcomes, scan, Builds bump/no-bump and delivery are evidenced before checkpoint acceptance" | "when one real nightly run finishes, scheduled or dispatched on `main` (CAP-13), then the pilots' CodeQL, releases or valid no-release outcomes and scan rows pass, and the bump's no-change or pushed-and-delivered result and `keepalive` are evidenced before checkpoint acceptance; other modules' rows are recorded, not decisive" |
| `spec-12…:24` | F | "Wait for story 11's genuine scheduled-night checkpoint and acceptance before adoption." | "Wait for story 11's nightly checkpoint acceptance before adoption." |
| `spec-12…:26` | F | "manually dispatch the acceptance night," | "count a `qualify-bump` run or another module's row as its nightly outcome," |
| `spec-12…:62` | | "its next genuine nightly finishes" | "a nightly run (CAP-13) after adoption finishes" |
| `spec-13…:26` | F | "Dispatch or rerun the story 11 night. Register or deliver Works before story 11's genuine scheduled-night checkpoint is accepted." | "Count a `qualify-bump` run or another module's row as a nightly outcome. Register or deliver Works before story 11's nightly checkpoint is accepted." |
| `spec-13…:28` | F | "after story 11's genuine scheduled night is accepted" | "after story 11's nightly checkpoint is accepted (amended 2026-11-18, on-demand nightly)" |
| `spec-13…:64` | | "the next genuine scheduled night" | "a nightly run (CAP-13) after adoption" |
| `spec-13…:69` | | "story 11's genuine scheduled night is accepted" | "story 11's nightly checkpoint is accepted" |
| `spec-13…:71` | | "the next genuine nightly finishes" | "a nightly run (CAP-13) after adoption finishes" |
| `spec-14…:60` | | "the next genuine scheduled nightly outcome" | "its nightly outcome (CAP-13)" |
| `spec-14…:67` | | "its next scheduled nightly runs" | "a nightly run (CAP-13) after adoption finishes" |
| `spec-15…:60` | | "the next genuine nightly outcome" | "its nightly outcome (CAP-13)" |
| `spec-16…:26` | F | "the next genuine scheduled nightly outcome" | "its nightly outcome (CAP-13)" |
| `spec-16…:119` | | "scheduled night" | "nightly run" |
| `spec-16…:133` | | "its next scheduled nightly completes" | "a nightly run (CAP-13) after adoption completes" |
| `spec-17…:25` | F | "or substitute manual dispatch for the acceptance night" | "or count a `qualify-bump` run or another module's row as its nightly outcome" |
| `spec-17…:66` | | "the next genuine nightly completes" | "a nightly run (CAP-13) after adoption completes" |
| `spec-18…:20` | F | "a successful next scheduled nightly" | "a successful nightly run (CAP-13) after adoption" |
| `spec-18…:65` | | "its next scheduled nightly finishes" | "a nightly run (CAP-13) after adoption finishes" |
| `spec-20…:114` | | "the next scheduled night completes" | "a nightly run (CAP-13) after adoption completes" |
| `spec-21…:66` | | "the next scheduled night finish" | "a nightly run (CAP-13) after adoption finish" |
| `spec-22…:19` | F | "the next scheduled nightly succeeds" | "a nightly run (CAP-13) after adoption succeeds" |
| `spec-22…:40` | F | "Accept authenticated scheduled nightly nothing-to-release" | "Accept an authenticated nightly-run nothing-to-release" |
| `spec-22…:59` | | "next scheduled nightly" | "a nightly run (CAP-13)" |
| `spec-26…:119` | | "the next scheduled nightly" | "a nightly run (CAP-13) after adoption" |

Line numbers are as of `81e10620`; the edit is by phrase.

### 4.6 Story 11 planning

**`specs/spec-cicd/evidence/11/planning.md:204-206`:**
- OLD: "Wait for a real scheduled nightly and its CodeQL, release, Builds bump/no-bump and delivery outcomes; manual dispatch or fixtures cannot substitute for the story's real-night checkpoint."
- NEW: "Use one real nightly run, scheduled or dispatched on `main` (CAP-13), judged with `tools/nightly_acceptance.py --checkpoint pilot`; fixtures cannot substitute for it."

## 5. Implementation sequence and handoff

| Step | Who | What | Effort | Risk |
|---|---|---|---|---|
| 1 | Maintainer | Approve this proposal; answer D2's decision point if the default is wrong. | — | — |
| 2 | `bmad-spec` update | Apply §4.1–4.3 once the morning update in the working tree is committed, so SPEC, `stories.yaml` and spine are not edited concurrently. | Low | Low |
| 3 | Developer agent | Apply §4.4–4.6 in one commit. A story spec that another session has modified but not committed is left to that story's next resume. | Low | Low |
| 4 | `bmad-build 29-1` | Build the tool; it can run in parallel with 28-1. | Low–medium | Low: read-only, no pipeline change |
| 5 | Story 11 resume | After 28-1 and 29-1 land: dispatch one nightly per D1 and run `--checkpoint pilot`. Record the receipt, then disable the 18 Nov observer timer. | Low | Low |

If today's scheduled run arrives and the existing authenticator accepts it before step 5, story 11 may close on that result; both satisfy the new wording.

**Success criteria:**
- A nightly outcome is available within about 70 minutes of deciding to test, at any time of day.
- Story 11 accepts from one nightly run after 28-1 lands, with no new per-night script, observer or timer.
- Stories 12–26 judge their nightly criterion with `tools/nightly_acceptance.py` on any nightly run after adoption, and another module's failure never blocks them.
- Job selection for `schedule` and dispatch is identical and tested.
- The 02:17 UTC schedule, keepalive and the night's overall verdict are unchanged.

**Checklist status:**
- Done: 1.1–1.3, 2.1–2.5, 3.1, 3.2, 3.4, 4.1–4.4, 5.1–5.5, 6.1–6.3 (approved 2026-11-18).
- Not applicable: 3.3 (UX); 6.4 (no `sprint-status.yaml`; `stories.yaml` is the order of record).
- Needs action: 6.5 (handoff steps 2–5 of §5, run by the `bmad-spec` update, the developer agent and `bmad-build`).
