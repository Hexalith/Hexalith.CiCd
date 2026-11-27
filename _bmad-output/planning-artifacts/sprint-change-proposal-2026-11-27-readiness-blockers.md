# Sprint Change Proposal: Remaining Readiness Blockers (ChatBot Prerequisite, EventStore Cleanup, Tenants Nightly Acceptance)

- **Date:** 2026-11-27
- **Trigger:** Sprint planning readiness check returned **FAIL** after validating the earlier 27 November planning corrections (`sprint-change-proposal-2026-11-27.md`), identifying three remaining plan blockers across ChatBot (19), EventStore (20), and Tenants (23).
- **Mode:** Batch
- **Scope classification:** Moderate — adds one prerequisite story (`29-3`) before Story 19, updates companion wait-horizon wording (`ARCHITECTURE-SPINE.md`, `pipeline-stages.md`), aligns Story 20's non-frozen task list, and renegotiates one `<frozen-after-approval>` row plus two non-frozen clauses in Story 23.
- **Status:** Approved by the maintainer on 2026-11-27 (including explicit human renegotiation of Story 23's frozen matrix row at `spec-23-migrate-tenants.md:48`); §4.1–§4.3 edits applied in the working tree and verified.
- **Planning structure:** `specs/spec-cicd/SPEC.md` serves as the PRD and `specs/spec-cicd/stories.yaml` is the backlog and execution order of record (no `sprint-status.yaml`).

## 1. Issue Summary

Although the earlier 27 November corrections resolved the `20 → 24 → 23` cutover order, EventStore's on-premises MVP scope, and EventStore's CAP-16 nightly trigger policy, sprint planning readiness still fails on three concrete contradictions in the active planning and implementation artifacts:

| # | Finding | Issue Type | Concrete Evidence (current working tree on baseline `6803c761d5979b0c7639b3b762f3a0d53fdbff9e`) |
|---|---|---|---|
| **F1** | **ChatBot (19) unscheduled prerequisite** | Missing backlog scheduling for an approved technical prerequisite | `spec-19-migrate-chatbot.md:30,57` explicitly exclude shared timing work from Story 19 and block ChatBot adoption on `prerequisite-19-long-running-nightly-hooks.md`. Items 1–3 shipped in Builds `v6.1.0` and CiCd render, but items 4–5 remain open: `tools/nightly.py:154` hard-codes `started + 300 * 60` (`SECONDS["wait"] = 320 * 60` at line 24) and `.github/workflows/nightly.yml:653` caps `wait` at `timeout-minutes: 330` with no continuation job. `stories.yaml` (58 IDs) schedules Story `19` at lines 711–729 with no preceding prerequisite entry. |
| **F2** | **EventStore (20) conflicting cleanup timing** | Artifact conflict between backlog/AD-21 and implementation spec | `stories.yaml:751-753` and `ARCHITECTURE-SPINE.md:663-664` (AD-21) require preserving legacy publishing and tool-only npm/Husky assets until adoption and retiring them *after* adoption. `spec-20-migrate-eventstore.md:93-97` still lists `root npm files` / `tool-only npm assets` deletion under pre-adoption product preparation instead of the post-adoption task (lines 104–106). |
| **F3** | **Tenants (23) scheduled-only nightly clauses** | Artifact conflict missed in the 18 November on-demand nightly pass | `spec-23-migrate-tenants.md:48` (inside `<frozen-after-approval>`) requires `Accept authenticated scheduled “nothing to release”`, line 79 (Acceptance Criteria) requires `the next scheduled central release`, and line 211 (Verification) mirrors `next scheduled release outcome`. All three conflict with `SPEC.md` CAP-13/CAP-16, `ARCHITECTURE-SPINE.md` AD-18, and AD-21 step 4 (lines 620–625), which permit either a scheduled `nightly.yml` run or an authorized `workflow_dispatch` with `qualify-bump: false`. (`sprint-change-proposal-2026-11-18-on-demand-nightly.md:36` mistakenly assumed Story 23 needed no edit.) |

### Exact Source Revisions Inspected

- Repository `HEAD`: `6803c761d5979b0c7639b3b762f3a0d53fdbff9e` (tree `5db92e398b50280cd9bca60cc8055a96a362b100`), with uncommitted 27 November planning updates in the working tree.
- Working-tree blob IDs:
  - `_bmad-output/specs/spec-cicd/SPEC.md`: `e683bde3039d89d0968e1147d01fcaa1ebda0b93`
  - `_bmad-output/specs/spec-cicd/stories.yaml`: `0a5c82eefb0159ea06abc789e1935eae24822829`
  - `_bmad-output/specs/spec-cicd/pipeline-stages.md`: `be6e7d85c485afdfdd9e40491f73d2dae123fc1a`
  - `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md`: `9d21fa67d63ecf4aa1c307493c9a225d7c1f4fb9`
  - `_bmad-output/implementation-artifacts/prerequisite-19-long-running-nightly-hooks.md`: `32bee4394b33843e3b87f746d2c124a6086857a7`
  - `_bmad-output/implementation-artifacts/spec-19-migrate-chatbot.md`: `47bbe5b2103f04d9c6cc7e504be45d9029e907d6`
  - `_bmad-output/implementation-artifacts/spec-20-migrate-eventstore.md`: `7b8963e58ce76210c76327fb1e73ac0809d9f66`
  - `_bmad-output/implementation-artifacts/spec-23-migrate-tenants.md`: `c8a7d0b5470f43c62a941897a9eb4c4f043185bd`
  - `tools/nightly.py`: `c3f911f18a22db044407b65e465aa20d540668b2`
  - `.github/workflows/nightly.yml`: `e10245d9db72f7a201184215df40aba61dcbdd2d`

## 2. Impact Analysis

### Epic & Backlog Impact

- **Story 19 (ChatBot) & Nightly Controller family (`29-*`):** Adding story `29-3` immediately before `19` in `stories.yaml` makes the previously off-backlog CiCd prerequisite executable in the canonical backlog order (59 unique, prefix-free story IDs; `"19-0"` or `"19-1"` would violate `stories-schema.md` prefix-free validity rule #2 against `"19"`). Story `19` remains parked on the maintainer's ChatBot product-scope decision (`evidence/19/blockers-20261118.json`), so `29-3`'s dispatch note explicitly carries that gate before implementation starts.
- **Story 20 (EventStore):** Moving npm/Husky asset removal from product preparation to post-adoption eliminates contradictory developer instructions without changing EventStore's cutover position (`20 → 24 → 23`) or frozen boundaries.
- **Story 23 (Tenants):** Reconciling the frozen matrix row, acceptance criterion, and verification bullet aligns Story 23 with the already-approved CAP-13/CAP-16/AD-21 contract. Cutover order (`20 → 24 → 23`), MVP target, and product coverage remain unchanged.
- **Remaining migrations (`21`, `22`, `24`, `25`, `26`, `27-1`, `27-2`, `29-2`):** Unaffected. `29-3` preserves the 45-minute hook default and existing 5-hour default wait behavior for all other modules.

### Artifact Conflict Analysis

| Artifact | Impact |
|---|---|
| **Requirements (`SPEC.md`)** | **No change required.** CAP-5 already supports bounded 6-hour hooks; CAP-13 and CAP-16 already allow both scheduled and authorized `workflow_dispatch` (`qualify-bump: false`) nightly runs. MVP scope is unchanged. |
| **Architecture (`ARCHITECTURE-SPINE.md`)** | **Targeted update to AD-18 (lines 462, 465):** Document bounded continuation across wait jobs when a dispatched module configures `nightlyTimeoutMinutes` beyond the 5-hour single-job default, keeping every job under GitHub's 6-hour limit and re-minting fresh scoped tokens under 50 minutes. **AD-7 note:** Adding a new `cicd-app` continuation job in `nightly.yml` during `29-3` implementation will require updating `docs/cicd-app-inventory.md` and `tools/app-workflow-policy.json`. |
| **Spec Companion (`pipeline-stages.md`)** | **Targeted update (lines 80–81):** Align the Nightly run `Wait` and `Publish-ready` descriptions with AD-18's bounded wait-continuation behavior. |
| **Backlog (`stories.yaml` + `.memlog.md`)** | **Insert `29-3` before `19`; update `19`'s `invoke_dev_with`.** Record the change in `_bmad-output/specs/spec-cicd/.memlog.md` per `stories-schema.md` update semantics. |
| **Implementation Specs** | Update `prerequisite-19-long-running-nightly-hooks.md` (link to `29-3` and refresh stale line numbers), `spec-19-migrate-chatbot.md:57` (non-frozen task reference to `29-3`), `spec-20-migrate-eventstore.md:93-97,104-106` (non-frozen cleanup timing + Spec Change Log), and `spec-23-migrate-tenants.md:48,79,211` (1 frozen row + 2 non-frozen clauses + Spec Change Log). |
| **UI/UX Specifications** | **N/A** — no product UI/UX specifications exist in this repository. |
| **Secondary / Code Artifacts (deferred to `29-3` execution)** | `tools/nightly.py`, `tools/nightly_runtime.py`, `.github/workflows/nightly.yml`, `docs/nightly.md`, `setup/README.md`, `docs/cicd-app-inventory.md`, `tools/app-workflow-policy.json`, and nightly controller tests. No code edits occur in this planning correction. |

## 3. Recommended Approach

| Option | Assessment | Verdict |
|---|---|---|
| **Option 1: Direct Adjustment (Recommended)** | Add story `29-3` before `19`, update AD-18 / `pipeline-stages.md` wait-horizon text, move EventStore's npm/Husky cleanup to post-adoption in `spec-20`, and reconcile Tenants' three scheduled-only clauses in `spec-23`. **Effort:** Low (planning edits now; Low–Medium for `29-3` implementation later). **Risk:** Low. | **Viable — Selected** |
| **Option 2: Potential Rollback** | Nothing completed causes these conflicts: Builds `v6.1.0` `nightlyTimeoutMinutes`, EventStore's published preparation, and the 18 November on-demand nightly policy are all valid and wanted. Rolling back would discard sound work without resolving readiness. **Effort:** High. **Risk:** High. | **Not viable** |
| **Option 3: PRD MVP Review** | MVP goals (17 modules adopted, on-premises target, shared CI/release/nightly) remain intact. ChatBot's product-scope decision is already parked separately (`evidence/19/blockers-20261118.json`); no MVP reduction is required to make the plan consistent. **Effort:** Medium. **Risk:** Medium. | **Not viable** |

**Rationale:** Direct adjustment resolves all three readiness blockers cleanly in one coordinated pass, honors every prior maintainer decision (16 November prerequisite split, 18 November ChatBot parking & on-demand nightly acceptance, 27 November cutover/MVP updates), and unblocks sprint planning readiness immediately without modifying runtime code prematurely.

**Key Risks & Mitigations:**
- *Premature `29-3` execution before ChatBot product-scope decision:* Mitigated by marking `spec_checkpoint: true` on `29-3` and stating the `blockers-20261118.json` decision gate directly in `invoke_dev_with`.
- *AD-7 App inventory drift when `29-3` adds a continuation job:* Mitigated by naming `docs/cicd-app-inventory.md` and `tools/app-workflow-policy.json` in `29-3`'s `invoke_dev_with` so `tools/check_app_inventory.py` remains enforced.
- *Accidental alteration of Tenants' scheduled performance workload:* Mitigated by restricting edits to lines 48, 79, and 211 while explicitly preserving `scheduled performance` on lines 28 and 72.

## 4. Detailed Change Proposals

### 4.1 Backlog & Spec Companion Updates (via `bmad-spec`)

#### Proposal 1A — `stories.yaml`: Add story `29-3` immediately before story `19`

- **File:** `_bmad-output/specs/spec-cicd/stories.yaml` (insert between Story `18` at line 710 and Story `19` at line 711)
- **OLD:** *(no entry between `id: "18"` and `id: "19"`)*
- **NEW:**
  ```yaml
  - id: "29-3"
    title: "Long-running nightly wait continuation"
    description: >-
      Extend the central nightly wait controller, workflow and docs to cover a
      module's configured nightlyTimeoutMinutes (up to 360 minutes) plus
      subsequent version, build and publication stages without exceeding
      GitHub's 6-hour job limit or reusing stale tokens, while preserving the
      45-minute default and existing behavior for all other modules (CAP-5,
      CAP-13; AD-7, AD-18).
    spec_checkpoint: true
    invoke_dev_with: >-
      Implement the remaining CiCd items 4-5 of
      _bmad-output/implementation-artifacts/prerequisite-19-long-running-nightly-hooks.md
      (items 1-3 already shipped in Builds v6.1.0 and CiCd render). Per
      _bmad-output/specs/spec-cicd/evidence/19/blockers-20261118.json, begin
      implementation only after the maintainer decides ChatBot's product scope
      (EventStore 5 net11.0 retarget and atomic participation). Work in
      tools/nightly.py, tools/nightly_runtime.py, .github/workflows/nightly.yml,
      docs/nightly.md, setup/README.md, their tests, and if a new cicd-app
      continuation job is added, docs/cicd-app-inventory.md and
      tools/app-workflow-policy.json (AD-7). Preserve fresh scoped App mints
      under 50 minutes, exact run/attempt correlation, cancellation, truthful
      timeouts and final verdicts; test boundaries with simulated clocks
      without multi-hour sleeps.
  ```
- **Rationale:** Schedules the remaining CiCd half of `prerequisite-19-long-running-nightly-hooks.md` in canonical execution order before ChatBot cutover using a prefix-free ID (`29-3`, matching the `29-*` nightly controller series and satisfying `stories-schema.md` rule #2).

#### Proposal 1B — `stories.yaml`: Reference `29-3` in Story `19` `invoke_dev_with`

- **File:** `_bmad-output/specs/spec-cicd/stories.yaml` (Story `19`, `invoke_dev_with`, lines 717–719)
- **OLD:**
  ```yaml
    invoke_dev_with: >-
      Check the AD-21 maintainer preconditions first, including the
  ```
- **NEW:**
  ```yaml
    invoke_dev_with: >-
      Wait for story 29-3 (the CiCd half of
      prerequisite-19-long-running-nightly-hooks.md) and the maintainer's
      ChatBot product-scope decision before registering or adopting ChatBot.
      Check the AD-21 maintainer preconditions first, including the
  ```
- **Rationale:** Makes the backlog dependency between `29-3` and `19` explicit in Story `19`'s dispatch instructions.

#### Proposal 1C — `ARCHITECTURE-SPINE.md`: Update AD-18 wait horizon for bounded continuation

- **File:** `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md` (AD-18, lines 462 and 465)
- **OLD (line 462):**
  ```markdown
      2. **`wait`** (App). Polls every 60 seconds until all runs complete, for at most 5 hours, and outputs each run's conclusion and outcome. It fails only when it can't list the runs.
  ```
- **NEW (line 462):**
  ```markdown
      2. **`wait`** (App). Polls every 60 seconds until all runs complete, for at most 5 hours by default—or across bounded continuation jobs when a dispatched module configures `nightlyTimeoutMinutes` beyond the single-job budget, each job staying under the 6-hour limit and re-minting fresh scoped tokens—and outputs each run's conclusion and outcome. It fails only when it can't list the runs.
  ```
- **OLD (line 465):**
  ```markdown
         - It then writes the summary and the verdict per run: a conclusion other than `success` is failed, whatever the outcome; `success` with `published`, `nothing` or `disabled` passes; `ready` passes only if this job published that draft; no readable outcome, or still running after 5 hours, is failed. It fails if any verdict is failed.
  ```
- **NEW (line 465):**
  ```markdown
         - It then writes the summary and the verdict per run: a conclusion other than `success` is failed, whatever the outcome; `success` with `published`, `nothing` or `disabled` passes; `ready` passes only if this job published that draft; no readable outcome, or still running after the configured wait deadline, is failed. It fails if any verdict is failed.
  ```
- **Rationale:** Ensures AD-18 does not contradict story `29-3`'s bounded continuation beyond 5 hours while preserving GitHub's 6-hour job limit and AD-7's 50-minute token limit.

#### Proposal 1D — `pipeline-stages.md`: Align Nightly run Wait & Publish-ready wording

- **File:** `_bmad-output/specs/spec-cicd/pipeline-stages.md` (Nightly run, lines 80–81)
- **OLD:**
  ```markdown
  3. **Wait.** It waits for every run, for at most 5 hours.
  4. **Publish-ready.** With the App, it publishes each draft whose run ended `ready`, after the same checks. It then writes the pass/fail summary with links. A run passes only when it succeeded with `published`, `nothing`, or `disabled`, or ended `ready` and was published here. A run still going after 5 hours, or one without a readable outcome, counts as failed.
  ```
- **NEW:**
  ```markdown
  3. **Wait.** It waits for every run, for at most 5 hours by default, extending across bounded continuation jobs (each under 6 hours) when a dispatched module configures a longer `nightlyTimeoutMinutes` hook allowance (story 29-3).
  4. **Publish-ready.** With the App, it publishes each draft whose run ended `ready`, after the same checks. It then writes the pass/fail summary with links. A run passes only when it succeeded with `published`, `nothing`, or `disabled`, or ended `ready` and was published here. A run still going after the configured wait deadline, or one without a readable outcome, counts as failed.
  ```
- **Rationale:** Keeps the spec companion consistent with AD-18 and story `29-3`.

#### Proposal 1E — ChatBot prerequisite & story spec cross-references (non-frozen)

- **File:** `_bmad-output/implementation-artifacts/spec-19-migrate-chatbot.md` (Execution task 1, line 57 — non-frozen)
  - **OLD:**
    ```markdown
    - [ ] `prerequisite-19-long-running-nightly-hooks.md` — require its verified shared release before registering ChatBot. The prerequisite is a separate deliverable; story 19 does not implement shared timing support.
    ```
  - **NEW:**
    ```markdown
    - [ ] Story `29-3` (`prerequisite-19-long-running-nightly-hooks.md` items 4–5) — require the scheduled CiCd wait-continuation prerequisite to ship before registering ChatBot (items 1–3 already shipped in Builds `v6.1.0` and CiCd render). The prerequisite is a separate deliverable; story 19 does not implement shared timing support.
    ```
- **File:** `_bmad-output/implementation-artifacts/prerequisite-19-long-running-nightly-hooks.md` (Status section, lines 25–36)
  - Add a brief 2026-11-27 status note recording that items 4–5 are scheduled as backlog story `29-3` immediately before Story `19`, and refresh current line pointers (`tools/nightly.py:154`, `.github/workflows/nightly.yml:653`, `builds-version` `v6.8.5`).
- **Rationale:** Links the prerequisite document and Story 19 task list directly to backlog ID `29-3` without altering Story 19's `<frozen-after-approval>` block.

---

### 4.2 EventStore (20) Post-Adoption Cleanup Alignment (via `bmad-spec`)

#### Proposal 2A — `spec-20-migrate-eventstore.md`: Move tool-only npm & Husky cleanup to post-adoption task

- **File:** `_bmad-output/implementation-artifacts/spec-20-migrate-eventstore.md` (Tasks & Acceptance, lines 93–97 and 104–106 — non-frozen; `<frozen-after-approval>` remains byte-for-byte unchanged)
- **OLD (product preparation task, lines 93–97):**
  ```markdown
  - [ ] EventStore `.github/actions/`, `Hexalith.EventStore.slnx`, `scripts/`,
    `tools/`, `tests/`, root npm files and `docs/ci.md` — retain package, consumer,
    compatibility, browser, payload and broker checks; reuse shared Release
    outputs; route live projects explicitly; delete CI/governance assertions
    and tool-only npm assets. Apply the approved preparation checks before pushes.
  ```
- **NEW (product preparation task, lines 93–97):**
  ```markdown
  - [ ] EventStore `.github/actions/`, `Hexalith.EventStore.slnx`, `scripts/`,
    `tools/`, `tests/` and `docs/ci.md` — retain package, consumer,
    compatibility, browser, payload and broker checks; reuse shared Release
    outputs; route live projects explicitly; delete CI/governance assertions
    while preserving legacy publishing and tool-only npm/Husky assets until
    adoption. Apply the approved preparation checks before pushes.
  ```
- **OLD (post-adoption task, lines 104–106):**
  ```markdown
  - [ ] `evidence/20/` — authenticate adoption, enable immutability, retire legacy
    grants, and record the normal checker, green adoption CI, applicable
    on-premises qualification, offline Azure checks and EventStore's nightly outcome.
  ```
- **NEW (post-adoption task, lines 104–106):**
  ```markdown
  - [ ] `evidence/20/` and EventStore root npm/Husky files — authenticate adoption,
    enable immutability, retire legacy grants and tool-only npm and Husky assets
    after adoption, and record the normal checker, green adoption CI, applicable
    on-premises qualification, offline Azure checks and EventStore's nightly outcome.
  ```
- **Spec Change Log (append under line 153):**
  ```markdown
  - 2026-11-27 — Moved tool-only npm and Husky cleanup from pre-adoption product preparation into the post-adoption task to match `stories.yaml` and AD-21, per [readiness-blockers sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-blockers.md).
  ```
- **Rationale:** Resolves the direct conflict with `stories.yaml:751-753` ("Preserve legacy publishing until delivery adopts the module; retire tool-only npm and Husky assets after adoption") and AD-21 (`ARCHITECTURE-SPINE.md:663-664`), while keeping the frozen block untouched.

---

### 4.3 Tenants (23) Nightly Acceptance Reconciliation (via `bmad-correct-course` approval)

> `F` marks text inside `<frozen-after-approval>`. Explicit maintainer approval of this Sprint Change Proposal serves as the human renegotiation required to amend line 48. Lines 28 and 72 (`scheduled performance`) describe Tenants' performance qualification workload and are **not** modified. Historical Implementation Notes (lines 81–185) are preserved unchanged.

#### Proposal 3A — `spec-23-migrate-tenants.md`: Reconcile frozen matrix row, acceptance criterion, and verification bullet

- **File:** `_bmad-output/implementation-artifacts/spec-23-migrate-tenants.md`
- **Section 1 — I/O & Edge-Case Matrix (line 48) `[F]`:**
  - **OLD:**
    ```markdown
    | No releasable change | Accept authenticated scheduled “nothing to release” |
    ```
  - **NEW:**
    ```markdown
    | No releasable change | Accept authenticated CAP-13/CAP-16 “nothing to release” from a central nightly run started after adoption (scheduled or authorized dispatch with `qualify-bump` false) |
    ```
- **Section 2 — Tasks & Acceptance — Acceptance Criteria (line 79):**
  - **OLD:**
    ```markdown
    - Given adoption, when publication is evaluated, then scoped credentials remain, pushes run CI and the next scheduled central release succeeds or reports nothing to release.
    ```
  - **NEW:**
    ```markdown
    - Given adoption, when publication is evaluated, then scoped credentials remain, pushes run CI, and Tenants' own CAP-13/CAP-16 rows pass in a central `nightly.yml` run started after adoption on `main` (scheduled or authorized `workflow_dispatch` with `qualify-bump` false): eligibility, passing CodeQL, verified publication or valid nothing-to-release, qualifying scan evidence for its dispatch commit and any required post-bump delivery evidence.
    ```
- **Section 3 — Verification (line 211):**
  - **OLD:**
    ```markdown
    - Authenticate hosted CI, actual product-hook execution, adoption cleanup and the next scheduled release outcome.
    ```
  - **NEW:**
    ```markdown
    - Authenticate hosted CI, actual product-hook execution, adoption cleanup and Tenants' own CAP-13/CAP-16 nightly outcome from a central `nightly.yml` run started after adoption on `main` (scheduled or authorized dispatch with `qualify-bump` false).
    ```
- **Section 4 — Spec Change Log (append under line 186):**
  ```markdown
  - 2026-11-27 — Human approved [readiness-blockers sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-blockers.md) renegotiating the frozen I/O matrix row (line 48) and aligning the acceptance criterion (line 79) and verification bullet (line 211) with AD-21 step 4, CAP-13 and CAP-16: a central `nightly.yml` run started after adoption on `main`, scheduled or authorized `workflow_dispatch` with `qualify-bump` false, satisfies Tenants' nightly acceptance. Scheduled performance workload requirements (lines 28, 72) and all other constraints are unchanged.
  ```
- **Rationale:** Reconciles the three remaining scheduled-only clauses missed on 18 November with `AD-21` step 4, `CAP-13`, and `CAP-16`, matching the exact CAP-13/CAP-16 evidence standard applied to Story 20.

## 5. Implementation Handoff

- **Change Scope Classification:** **Moderate** — requires backlog/spec coordination (`bmad-spec`) and implementation-spec updates (Developer agent) after maintainer approval.

| Step | Owner / Skill | Responsibility | Effort |
|---|---|---|---|
| **1** | **Maintainer** | Review and explicitly approve this Sprint Change Proposal (including renegotiation of Story 23's frozen matrix row at line 48). | — |
| **2** | **`bmad-spec` update** | Apply §4.1 (`stories.yaml` insert `29-3` before `19` + update `19` `invoke_dev_with`; `ARCHITECTURE-SPINE.md` AD-18; `pipeline-stages.md`; append `.memlog.md`) and §4.2 (`spec-20-migrate-eventstore.md` non-frozen tasks + Spec Change Log). | Low |
| **3** | **Developer agent** | Apply §4.1E (`spec-19-migrate-chatbot.md:57`, `prerequisite-19-long-running-nightly-hooks.md`) and §4.3 (`spec-23-migrate-tenants.md:48,79,211` + Spec Change Log) once maintainer approval is recorded. | Low |
| **4** | **Sprint planning readiness recheck (`bmad-sprint-planning`)** | Re-validate `stories.yaml` (59 unique, prefix-free story IDs; CAP-1..CAP-16 coverage; `29-3` preceding `19`; `20 → 24 → 23`), confirm EventStore cleanup alignment and Tenants CAP-16 alignment, and re-run readiness gate. | Low |
| **5** | **`bmad-build` (Story `29-3`, deferred until ChatBot scope decision)** | Execute `29-3` after the maintainer resolves ChatBot's product scope (`evidence/19/blockers-20261118.json`) and reviews `29-3`'s story spec (`spec_checkpoint: true`). | Low–Medium |

### Success Criteria

1. `stories.yaml` parses cleanly with 59 unique, prefix-free story IDs, covers CAP-1 through CAP-16, schedules `29-3` immediately before `19`, and preserves `20 → 24 → 23`.
2. `ARCHITECTURE-SPINE.md` (AD-18), `pipeline-stages.md`, `prerequisite-19-long-running-nightly-hooks.md`, and `spec-19-migrate-chatbot.md` all agree on bounded wait continuation tracked by `29-3`.
3. `spec-20-migrate-eventstore.md`, `stories.yaml`, and AD-21 all place EventStore's tool-only npm and Husky cleanup in the post-adoption task, with Story 20's frozen block unchanged.
4. `spec-23-migrate-tenants.md` lines 48, 79, and 211 accept either eligible post-adoption central `nightly.yml` trigger (scheduled or authorized `workflow_dispatch` with `qualify-bump: false`) while preserving `scheduled performance` on lines 28 and 72 and recording the human renegotiation in its Spec Change Log.
5. Sprint planning readiness passes with zero open blockers.

### Change Navigation Checklist Status

| Checklist Section | Status | Summary |
|---|---|---|
| **1.1–1.3** Trigger, core problem, evidence | `[x]` Done | All three readiness blockers traced to exact files, line numbers, and working-tree blob IDs. |
| **2.1–2.5** Epic / backlog impact & sequencing | `[x]` Done | Assessed Stories 19, 20, 23, `29-*` controller series, and remaining migrations; scheduled `29-3` before `19`. |
| **3.1–3.2, 3.4** PRD / Architecture / Secondary artifacts | `[x]` Done | Verified `SPEC.md` needs no edit; identified AD-18, `pipeline-stages.md`, and `29-3` AD-7 inventory follow-up. |
| **3.3** UI/UX specifications | `[N/A]` Skip | No product UI/UX specifications exist in this repository. |
| **4.1–4.4** Path forward evaluation | `[x]` Done | Selected Option 1 (Direct Adjustment); Rollback and MVP Review ruled out. |
| **5.1–5.5** Proposal components & handoff | `[x]` Done | Compiled complete proposal with exact before/after edits and Moderate-scope handoff. |
| **6.1–6.2** Checklist & proposal verification | `[x]` Done | Verified schema prefix-freedom (`29-3`), frozen-block boundary (`spec-23:48`), and preserved clauses (`spec-23:28,72`). |
| **6.3** Explicit user approval | `[x]` Done | Approved by the maintainer on 2026-11-27, including human renegotiation of Story 23's frozen matrix row (`spec-23-migrate-tenants.md:48`). |
| **6.4** Update `sprint-status.yaml` | `[N/A]` Skip | No `sprint-status.yaml` in this repo; `stories.yaml` updated directly with `29-3` before `19`. |
| **6.5** Confirm next steps and handoff | `[x]` Done | §4.1–§4.3 edits applied and verified; `bmad-sprint-planning` readiness recheck and deferred `29-3` execution handed off. |
