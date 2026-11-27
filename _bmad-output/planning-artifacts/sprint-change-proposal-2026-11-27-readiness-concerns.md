# Sprint Change Proposal: Readiness Concerns (Shared-Runtime Prerequisites, CAP-13/CAP-16 Verification Alignment, Nightly Barrier Sync)

- **Date:** 2026-11-27
- **Trigger:** Sprint planning readiness paused at **CONCERNS** after re-checking the 27 November readiness-blocker fixes (`sprint-change-proposal-2026-11-27-readiness-blockers.md`), identifying three remaining alignment gaps before tracker generation: two excluded shared-runtime prerequisites missing from `stories.yaml` (before Parties `21` and Memories `22`), four non-frozen `## Verification` bullets still requiring scheduled-only nightly outcomes (`spec-19`, `spec-21`, `spec-22`, `spec-26`), and a stale 30-minute dispatch barrier duration in `pipeline-stages.md:70`.
- **Mode:** Batch
- **Scope classification:** Moderate — schedules two prefix-free prerequisite stories (`31-1` before `21`, `31-2` before `22`) in `stories.yaml`, syncs one spec-companion sentence (`pipeline-stages.md:70`) to AD-18, and aligns four non-frozen `## Verification` bullets plus non-frozen cross-references and Spec Change Log entries. Zero `<frozen-after-approval>` blocks are modified.
- **Status:** Approved by the maintainer on 2026-11-27; §4.1–§4.3 edits applied in the working tree and verified.
- **Planning structure:** `specs/spec-cicd/SPEC.md` serves as the PRD and `specs/spec-cicd/stories.yaml` is the backlog and execution order of record (no `sprint-status.yaml`).

## 1. Issue Summary

Sprint planning readiness re-evaluation found zero FAIL blockers after the earlier 27 November corrections, but paused at **CONCERNS** on three concrete planning inconsistencies:

| # | Finding | Issue Type | Concrete Evidence (baseline `553d22bc2421585b3c4f2c8a86348e7235249dd0`) |
|---|---|---|---|
| **C1** | **Two excluded shared-runtime prerequisites unscheduled in `stories.yaml`** | Missing backlog scheduling for approved technical prerequisites | (a) `prerequisite-21-native-build-reuse.md:29-46` and `spec-21-migrate-parties.md:45,88` block Parties (`21`) adoption on shared `Hexalith.Builds.Module.Cli` native build reuse without hook-side compilation (`spec-21-frozen-release-timestamp.md` is already `done`). (b) `spec-22-migrate-memories.md:30-31,54` and `evidence/22/prerequisite-handoff.md:22-32` explicitly exclude shared rollout tools, prepared OCI inputs and Debug/source composition support from Story `22` and require them to ship separately before Memories registration/adoption. Neither prerequisite has a backlog entry in `stories.yaml` (59 IDs). |
| **C2** | **Four non-frozen `## Verification` bullets require scheduled-only nightly runs** | Artifact conflict missed in the 18 November on-demand nightly pass | `spec-19-migrate-chatbot.md:101` ("next scheduled release outcome"), `spec-21-migrate-parties.md:106` ("scheduled-night outcomes"), `spec-22-migrate-memories.md:96` ("next scheduled release outcome"), and `spec-26-migrate-platform.md:169` ("actual next scheduled nightly outcome") still require a scheduled nightly run, conflicting with `SPEC.md` CAP-13/CAP-16, `ARCHITECTURE-SPINE.md` AD-18, and AD-21 step 4 (lines 620–625), which accept either a scheduled `nightly.yml` run or an authorized `workflow_dispatch` with `qualify-bump: false`. All four lines sit outside `<frozen-after-approval>`. |
| **C3** | **Stale dispatch barrier duration in `pipeline-stages.md:70`** | Spec companion drift vs. Architecture Spine (AD-18) | `pipeline-stages.md:70` states `It first waits, for at most 30 minutes, until no delivery run on main is in progress`, contradicting `ARCHITECTURE-SPINE.md:458` (AD-18), which specifies `It first waits up to two hours for two consecutive complete scans with no active deliver.yml run on main`. |

### Exact Source Revisions Inspected

- Repository `HEAD`: `553d22bc2421585b3c4f2c8a86348e7235249dd0` (tree `62514427d217b495a8fa7263835fa144486238d3`), clean working tree, `builds-version` = `v6.8.5`.
- Inspected blob IDs:
  - `_bmad-output/specs/spec-cicd/stories.yaml`: `e59bea69e1361dda19fef4fd932789004d54f588`
  - `_bmad-output/specs/spec-cicd/pipeline-stages.md`: `8f4944aa415837a2741e8487c95a551af97e358d`
  - `_bmad-output/implementation-artifacts/prerequisite-21-native-build-reuse.md`: `4f482388a4d3224141b8206a90ef2ed04307fd1f`
  - `_bmad-output/implementation-artifacts/spec-19-migrate-chatbot.md`: `6d3472a5c4fd1051a52e459b0517b05d97ae01d4`
  - `_bmad-output/implementation-artifacts/spec-21-migrate-parties.md`: `54afac938c18ee8465611fb46f2e3d28929c7439`
  - `_bmad-output/implementation-artifacts/spec-22-migrate-memories.md`: `cc17bca350890bd3e628bf3189e7d3357cf28ea9`
  - `_bmad-output/implementation-artifacts/spec-26-migrate-platform.md`: `906a723e827a98ba9da286c6d4113dc7b511390c`
  - `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md`: `b0d09ea975dbc887af2ea39c8c8c256a5741ef18`

## 2. Impact Analysis

### Epic & Backlog Impact

- **New shared-runtime prerequisite family (`31-*`):** Inserting `"31-1"` immediately before `"21"` (Parties) and `"31-2"` immediately before `"22"` (Memories) expands `stories.yaml` from 59 to 61 unique, prefix-free story IDs. Using the `31-*` family follows the repository's existing `28-*` / `29-*` / `30-*` convention and respects `stories-schema.md` validity rule #2 (prefix-free under `<id>-`; `"21-*"` and `"22-*"` are invalid because `"21"` and `"22"` already exist). Neither ID collides with any existing `stories/<id>-*.md` file.
- **Stories `21` (Parties) and `22` (Memories):** Their `invoke_dev_with` notes and non-frozen spec references explicitly point to `31-1` and `31-2` respectively. Neither story's `<frozen-after-approval>` block or relative cutover position changes (`20 → 31-1 → 21 → 31-2 → 22 → 24 → 23 → 25 → 26`).
- **Stories `19` (ChatBot), `21` (Parties), `22` (Memories), and `26` (Platform):** Aligning their four non-frozen `## Verification` bullets removes internal contradictions with their own Spec Change Logs (18 November on-demand nightly decision) and AD-21 step 4.
- **Other migrations (`11`–`18`, `20`, `23`, `24`, `25`, `27-1`, `27-2`, `29-2`):** Unaffected. `31-1` preserves default `Hexalith.Builds.Module.Cli` behavior for existing consumers, and `31-2` keeps normal builds and releases in Release/package mode.

### Artifact Conflict Analysis

| Artifact | Impact |
|---|---|
| **Requirements (`SPEC.md`)** | **No change required.** CAP-5, CAP-10, CAP-13, and CAP-16 already govern shared runtime capabilities, product-only hooks, and on-demand/scheduled nightly acceptance. MVP scope is unchanged. |
| **Architecture (`ARCHITECTURE-SPINE.md`)** | **No change required now.** AD-18 (line 458) is already the authoritative source for the two-hour / two-consecutive-complete-scans dispatch barrier, and AD-21 step 4 (lines 620–625) already defines CAP-13/CAP-16 nightly acceptance. Any additive schema/contract knobs introduced during `31-1` or `31-2` will be reviewed at their `spec_checkpoint: true` gates under AD-2, AD-10, AD-12, and AD-14. |
| **Spec Companion (`pipeline-stages.md`)** | **Targeted update (line 70):** Sync the Nightly run `Dispatch` barrier sentence to match AD-18 (`up to two hours, for two consecutive complete scans with no active deliver.yml run on main`). |
| **Backlog (`stories.yaml` + `.memlog.md`)** | **Insert `31-1` before `21` and `31-2` before `22`; update `21` and `22` `invoke_dev_with`.** Append the decision entry to `_bmad-output/specs/spec-cicd/.memlog.md` per `stories-schema.md`. |
| **Implementation Specs** | Update non-frozen lines only: `spec-19-migrate-chatbot.md:101` (+ Spec Change Log), `spec-21-migrate-parties.md:45,106` (+ Spec Change Log), `prerequisite-21-native-build-reuse.md` (status pointer to `31-1`), `spec-22-migrate-memories.md:54,96` (+ Spec Change Log), and `spec-26-migrate-platform.md:169` (+ Spec Change Log). Historical evidence (`evidence/22/prerequisite-handoff.md`) is preserved unchanged. |
| **UI/UX Specifications** | **N/A** — no product UI/UX specifications exist in this repository. |
| **Secondary / Code Artifacts (deferred to `31-1` and `31-2` execution)** | `references/Hexalith.Builds` (`Hexalith.Builds.Module.Cli`, `Github/lib/{ci_environment,ci_pipeline}.py`, `schemas/`) and CiCd `templates/` / `tools/render.py` if additive contract fields are approved at `spec_checkpoint`. No code edits occur in this planning correction. |

## 3. Recommended Approach

| Option | Assessment | Verdict |
|---|---|---|
| **Option 1: Direct Adjustment (Recommended)** | Schedule `31-1` before `21` and `31-2` before `22` in `stories.yaml` (both with `spec_checkpoint: true`), align the four non-frozen `## Verification` bullets with CAP-13/CAP-16, and sync `pipeline-stages.md:70` to AD-18. **Effort:** Low (planning edits now; Medium when executing `31-1` and `31-2` later). **Risk:** Low. | **Viable — Selected** |
| **Option 2: Potential Rollback** | Nothing completed causes these concerns: frozen-created timestamp (`spec-21-frozen-release-timestamp.md`), AD-18's two-hour dispatch barrier, and CAP-13/CAP-16 on-demand nightly acceptance are all valid and wanted. Rolling back would discard sound work without fixing readiness. **Effort:** High. **Risk:** High. | **Not viable** |
| **Option 3: PRD MVP Review** | MVP goals (17 modules adopted under shared CI/release/nightly with preserved product coverage) remain intact and explicitly ratified in the 16 November human decisions for Stories 21 and 22. Reducing MVP scope is unnecessary. **Effort:** Medium. **Risk:** Medium. | **Not viable** |

**Rationale:** Direct adjustment eliminates all three readiness `CONCERNS` cleanly in one pass without modifying any `<frozen-after-approval>` block or runtime code. Putting `spec_checkpoint: true` on `31-1` and `31-2` guarantees human architectural review of any additive Builds contract changes (AD-2, AD-10, AD-12, AD-14) and lets `31-2` audit already-shipped capabilities (such as `npmWorkspaces` in `v6.8.5`) before writing new Builds code.

**Key Risks & Mitigations:**
- *Scope creep or module-specific logic in `31-1` / `31-2`:* Mitigated by `spec_checkpoint: true`, explicit AD-2 module-agnosticity requirements in `invoke_dev_with`, and prohibiting general command runners or build matrices in `31-2`.
- *Duplicating capabilities already shipped since `v6.0.6` (`31-2`):* Mitigated by instructing `31-2` to audit current `builds-version` (`v6.8.5`+) before adding only demonstrated remaining gaps.
- *Accidental edits to `<frozen-after-approval>` blocks:* Mitigated by restricting all four spec edits strictly to non-frozen `Code Map`, `Tasks & Acceptance`, `Spec Change Log`, and `Verification` sections.

## 4. Detailed Change Proposals

### 4.1 Backlog Scheduling for Excluded Shared-Runtime Prerequisites (`stories.yaml` + non-frozen cross-references)

#### Proposal 1A — `stories.yaml`: Insert `31-1` before `21` and update `21` `invoke_dev_with`

- **File:** `_bmad-output/specs/spec-cicd/stories.yaml` (insert between Story `20` at line 787 and Story `21` at line 788; update Story `21` lines 794–795)
- **OLD (between `id: "20"` and `id: "21"`):** *(no entry)*
- **NEW (insert before `id: "21"`):**
  ```yaml
  - id: "31-1"
    title: "Shared native build reuse in Builds.Module.Cli"
    description: >-
      Add an explicit, validated way for Hexalith.Builds.Module.Cli to reuse
      original audited Release test and composition artifacts in module hooks
      without restoring or compiling them, while keeping default behavior for
      existing consumers (CAP-5, CAP-10; AD-2, AD-10, AD-14). Ship and qualify
      the capability through an authorized Builds release before enabling
      package-mode native hooks in story 21.
    spec_checkpoint: true
    invoke_dev_with: >-
      Implement the required shared capability in
      _bmad-output/implementation-artifacts/prerequisite-21-native-build-reuse.md
      (inspected interfaces in
      _bmad-output/specs/spec-cicd/evidence/21/runner-build-reuse.json). Work in
      references/Hexalith.Builds with CiCd-agent (module-agnostic per AD-2). Bind
      reused artifacts to source, package cohort, target framework, configuration
      and composition model; reject missing, stale, foreign or changed bytes;
      preserve private credential issuance, descriptor ownership, authenticated
      endpoints, persisted-state observation, cancellation, expiry, cleanup and
      native TRX validation. Prove reuse across profiles without compiler
      invocations and mismatch rejection through the same production boundary,
      then ship through an authorized Builds release. Separate from frozen-created
      support (done) and grants no Parties adoption or publication authority.
  ```
- **OLD (Story `21`, `invoke_dev_with`, lines 794–795):**
  ```yaml
    invoke_dev_with: >-
      Check the AD-21 maintainer preconditions first, including the
  ```
- **NEW (Story `21`, `invoke_dev_with`):**
  ```yaml
    invoke_dev_with: >-
      Wait for story 31-1 (prerequisite-21-native-build-reuse.md) to ship in an
      acceptable Builds release before enabling package-mode native hooks,
      registering or adopting Parties. Check the AD-21 maintainer preconditions
      first, including the
  ```
- **Rationale:** Schedules the excluded Parties shared-runtime prerequisite directly ahead of Story `21` using a prefix-free ID (`31-1`), with `spec_checkpoint: true` for Builds public-API review.

#### Proposal 1B — `stories.yaml`: Insert `31-2` before `22` and update `22` `invoke_dev_with`

- **File:** `_bmad-output/specs/spec-cicd/stories.yaml` (insert between Story `21` at line 806 and Story `22` at line 807; update Story `22` lines 813–814)
- **OLD (between `id: "21"` and `id: "22"`):** *(no entry)*
- **NEW (insert before `id: "22"`):**
  ```yaml
  - id: "31-2"
    title: "Shared rollout tools, prepared OCI inputs and Debug/source composition support"
    description: >-
      Extend Builds' module-agnostic CI preparation, pipeline and schema contract
      with narrowly scoped Debug/source catalog composition, shared rollout tool
      preparation and hash-bound prepared OCI inputs, while keeping normal builds
      and releases in Release/package mode (CAP-5, CAP-10; AD-2, AD-10, AD-12,
      AD-14). Ship and qualify the compatible Builds release and CiCd render
      support before registering or adopting Memories in story 22.
    spec_checkpoint: true
    invoke_dev_with: >-
      Implement the shared Builds and CiCd prerequisites required by
      _bmad-output/implementation-artifacts/spec-22-migrate-memories.md (lines
      30-31, 54) and
      _bmad-output/specs/spec-cicd/evidence/22/prerequisite-handoff.md (contract
      table). Audit what already shipped through current builds-version (e.g.
      npmWorkspaces) and add only demonstrated remaining gaps: narrowly scoped
      Debug/source compilation and source-selected catalog behavior with exact
      direct dependency pins and separate outputs (no general command runner or
      build matrix), packaged Aspire runtime composition, shared Coverlet/MTP
      coverage collection, SQL/rollout tool preparation (kind/kubectl/pinned
      runtime deps) and hash-bound immutable prepared OCI inputs. Work in
      references/Hexalith.Builds (Github/lib/{ci_environment,ci_pipeline}.py and
      schemas) and CiCd templates/render as needed with CiCd-agent, keep Builds
      module-agnostic (AD-2), amend AD-12/AD-14 at spec_checkpoint if contract
      knobs change, qualify the existing 45-minute hook allowance before adding
      timeout settings, and ship an acceptable Builds release before story 22.
  ```
- **OLD (Story `22`, `invoke_dev_with`, lines 813–814):**
  ```yaml
    invoke_dev_with: >-
      Check the AD-21 maintainer preconditions first, including the
  ```
- **NEW (Story `22`, `invoke_dev_with`):**
  ```yaml
    invoke_dev_with: >-
      Wait for story 31-2 (shared rollout tools, prepared OCI inputs and
      Debug/source composition support) to ship in an acceptable Builds release
      before registering or adopting Memories. Check the AD-21 maintainer
      preconditions first, including the
  ```
- **Rationale:** Schedules the excluded Memories shared-runtime prerequisite directly ahead of Story `22` using a prefix-free ID (`31-2`), with `spec_checkpoint: true` and an explicit audit of capabilities already released since `v6.0.6`.

#### Proposal 1C — Non-frozen prerequisite cross-references (`prerequisite-21`, `spec-21`, `spec-22`)

- **File:** `_bmad-output/implementation-artifacts/prerequisite-21-native-build-reuse.md` (append status note after line 46)
  - **NEW (append):**
    ```markdown

    ## Status

    - 2026-11-27: Scheduled in `_bmad-output/specs/spec-cicd/stories.yaml` as backlog story `31-1` (`spec_checkpoint: true`) immediately before story `21` (Parties).
    ```
- **File:** `_bmad-output/implementation-artifacts/spec-21-migrate-parties.md` (Code Map, line 45 — non-frozen)
  - **OLD:**
    ```markdown
    - Current preparation and exact-input verification: [implementation handoff](../specs/spec-cicd/evidence/21/implementation-handoff.md), [accepted local verification](../specs/spec-cicd/evidence/21/accepted-local-verification.json), and [dispositions](../specs/spec-cicd/evidence/21/preparation-dispositions.md). Consult these before the earlier planning investigation. [Native build reuse prerequisite](prerequisite-21-native-build-reuse.md) and the owner-emission boundary evidence record the remaining shared interfaces.
    ```
  - **NEW:**
    ```markdown
    - Current preparation and exact-input verification: [implementation handoff](../specs/spec-cicd/evidence/21/implementation-handoff.md), [accepted local verification](../specs/spec-cicd/evidence/21/accepted-local-verification.json), and [dispositions](../specs/spec-cicd/evidence/21/preparation-dispositions.md). Consult these before the earlier planning investigation. Story `31-1` ([native build reuse prerequisite](prerequisite-21-native-build-reuse.md)) and the owner-emission boundary evidence record the remaining shared interfaces.
    ```
- **File:** `_bmad-output/implementation-artifacts/spec-22-migrate-memories.md` (Execution task 2, line 54 — non-frozen)
  - **OLD:**
    ```markdown
    - [ ] `evidence/22/code-investigation.md`, shared Builds `Github/lib/{ci_environment,ci_pipeline}.py` and contracts — require separately shipped support for rollout tools/prepared OCI inputs and the approved source/composition design before registration. Qualify browser/SQL/runtime dependencies without hook-side setup. This story does not implement an independent shared-runtime deliverable.
    ```
  - **NEW:**
    ```markdown
    - [ ] Story `31-2` (`evidence/22/code-investigation.md`, shared Builds `Github/lib/{ci_environment,ci_pipeline}.py` and contracts) — require the scheduled shared prerequisite for rollout tools/prepared OCI inputs and the approved source/composition design to ship before registration. Qualify browser/SQL/runtime dependencies without hook-side setup. This story does not implement an independent shared-runtime deliverable.
    ```
- **Rationale:** Links the prerequisite note and non-frozen story references directly to backlog IDs `31-1` and `31-2` without touching any `<frozen-after-approval>` block.

---

### 4.2 Align Four Non-Frozen `## Verification` Bullets with CAP-13/CAP-16

#### Proposal 2A — `spec-19-migrate-chatbot.md` (line 101 + Spec Change Log)

- **File:** `_bmad-output/implementation-artifacts/spec-19-migrate-chatbot.md` (Verification, line 101 — non-frozen)
- **OLD:**
  ```markdown
  - Authenticate hosted CI, actual recovery execution and the next scheduled release outcome.
  ```
- **NEW:**
  ```markdown
  - Authenticate hosted CI, actual recovery execution and ChatBot's own CAP-13/CAP-16 nightly outcome from a central `nightly.yml` run started after adoption on `main` (scheduled or authorized `workflow_dispatch` with `qualify-bump` false).
  ```
- **Spec Change Log (under line 88):**
  ```markdown
  - 2026-11-27 — Aligned the non-frozen `## Verification` bullet (line 101) with CAP-13, CAP-16 and AD-21 step 4 (accepting either a scheduled `nightly.yml` run or an authorized `workflow_dispatch` with `qualify-bump` false), per [readiness-concerns sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-concerns.md). Frozen intent unchanged.
  ```

#### Proposal 2B — `spec-21-migrate-parties.md` (line 106 + Spec Change Log)

- **File:** `_bmad-output/implementation-artifacts/spec-21-migrate-parties.md` (Verification, line 106 — non-frozen)
- **OLD:**
  ```markdown
  - Verify actual native/browser execution, container provenance/OCI identity, hosted CI, App delivery and scheduled-night outcomes; no mock or unavailable permission proves acceptance.
  ```
- **NEW:**
  ```markdown
  - Verify actual native/browser execution, container provenance/OCI identity, hosted CI, App delivery and Parties' own CAP-13/CAP-16 nightly outcome from a central `nightly.yml` run started after adoption on `main` (scheduled or authorized `workflow_dispatch` with `qualify-bump` false); no mock or unavailable permission proves acceptance.
  ```
- **Spec Change Log (append under line 93):**
  ```markdown
  - 2026-11-27 — Linked Code Map line 45 to newly scheduled prerequisite story `31-1` and aligned the non-frozen `## Verification` bullet (line 106) with CAP-13, CAP-16 and AD-21 step 4 (scheduled `nightly.yml` or authorized `workflow_dispatch` with `qualify-bump` false), per [readiness-concerns sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-concerns.md). Frozen intent unchanged.
  ```

#### Proposal 2C — `spec-22-migrate-memories.md` (line 96 + Spec Change Log)

- **File:** `_bmad-output/implementation-artifacts/spec-22-migrate-memories.md` (Verification, line 96 — non-frozen)
- **OLD:**
  ```markdown
  - Authenticate hosted execution of retained checks, cleanup and the next scheduled release outcome.
  ```
- **NEW:**
  ```markdown
  - Authenticate hosted execution of retained checks, cleanup and Memories' own CAP-13/CAP-16 nightly outcome from a central `nightly.yml` run started after adoption on `main` (scheduled or authorized `workflow_dispatch` with `qualify-bump` false).
  ```
- **Spec Change Log (append under line 83):**
  ```markdown
  - 2026-11-27 — Linked Execution task 2 (line 54) to newly scheduled prerequisite story `31-2` and aligned the non-frozen `## Verification` bullet (line 96) with CAP-13, CAP-16 and AD-21 step 4 (scheduled `nightly.yml` or authorized `workflow_dispatch` with `qualify-bump` false), per [readiness-concerns sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-concerns.md). Frozen intent unchanged.
  ```

#### Proposal 2D — `spec-26-migrate-platform.md` (line 169 + Spec Change Log)

- **File:** `_bmad-output/implementation-artifacts/spec-26-migrate-platform.md` (Verification, lines 168–169 — non-frozen)
- **OLD:**
  ```markdown
  - Inspect authenticated delivery report, accepted/pushed full revisions,
    perimeter/preservation, adopted CI and actual next scheduled nightly outcome.
  ```
- **NEW:**
  ```markdown
  - Inspect authenticated delivery report, accepted/pushed full revisions,
    perimeter/preservation, adopted CI and Platform's own CAP-13/CAP-16 nightly
    outcome from a central `nightly.yml` run started after adoption on `main`
    (scheduled or authorized `workflow_dispatch` with `qualify-bump` false).
  ```
- **Spec Change Log (append under line 149):**
  ```markdown
  - 2026-11-27 — Aligned the non-frozen `## Verification` bullet (lines 168–169) with CAP-13, CAP-16 and AD-21 step 4 (scheduled `nightly.yml` or authorized `workflow_dispatch` with `qualify-bump` false), per [readiness-concerns sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-concerns.md). Frozen intent unchanged.
  ```

- **Rationale (2A–2D):** Completes the 18 November on-demand nightly pass across all four non-frozen verification sections so none contradicts CAP-13, CAP-16, AD-18, or AD-21 step 4.

---

### 4.3 Sync Nightly Dispatch Barrier Duration (`pipeline-stages.md` + `.memlog.md`)

#### Proposal 3A — `pipeline-stages.md` (line 70)

- **File:** `_bmad-output/specs/spec-cicd/pipeline-stages.md` (Nightly run, item 1 `Dispatch`, line 70)
- **OLD:**
  ```markdown
  1. **Dispatch.** It first waits, for at most 30 minutes, until no delivery run on `main` is in progress. A module is adopted when its `delivered/<Repo>` branch exists and its live `main` has `.github/hexalith-ci.json`. Each adopted module whose live `ci.yml` and `release.yml` equal those on its branch gets its `release.yml` dispatched, along with the branch's commit. A drifted module is not dispatched, and fails the night. So do a branch without the file (a failed adoption push) and an adopted module with immutable releases off. Builds' `builds-release.yml` is dispatched too. Anything beyond the Free plan's 20 concurrent jobs waits in GitHub's queue.
  ```
- **NEW:**
  ```markdown
  1. **Dispatch.** It first waits, up to two hours, for two consecutive complete scans with no active `deliver.yml` run on `main`. A module is adopted when its `delivered/<Repo>` branch exists and its live `main` has `.github/hexalith-ci.json`. Each adopted module whose live `ci.yml` and `release.yml` equal those on its branch gets its `release.yml` dispatched, along with the branch's commit. A drifted module is not dispatched, and fails the night. So do a branch without the file (a failed adoption push) and an adopted module with immutable releases off. Builds' `builds-release.yml` is dispatched too. Anything beyond the Free plan's 20 concurrent jobs waits in GitHub's queue.
  ```
- **Rationale:** Brings `pipeline-stages.md` into exact agreement with AD-18 in `ARCHITECTURE-SPINE.md:458`.

#### Proposal 3B — `.memlog.md` (append update record)

- **File:** `_bmad-output/specs/spec-cicd/.memlog.md` (append after line 274)
- **NEW:** Record approval and application of `sprint-change-proposal-2026-11-27-readiness-concerns.md` (61 unique, prefix-free story IDs with `31-1` before `21` and `31-2` before `22`, `pipeline-stages.md:70` synced to AD-18, and four non-frozen `## Verification` bullets aligned with CAP-13/CAP-16).

## 5. Implementation Handoff

- **Change Scope Classification:** **Moderate** — requires backlog/spec coordination (`bmad-spec` update semantics for `stories.yaml`, `pipeline-stages.md`, `.memlog.md`) and non-frozen implementation-spec updates (Developer agent) after explicit maintainer approval.

| Step | Owner / Skill | Responsibility | Effort |
|---|---|---|---|
| **1** | **Maintainer** | Review and explicitly approve this Sprint Change Proposal. | — |
| **2** | **`bmad-spec` update** | Apply §4.1A–B (`stories.yaml`: insert `31-1` before `21` and `31-2` before `22`, update `21`/`22` `invoke_dev_with`), §4.3A (`pipeline-stages.md:70`), and §4.3B (`.memlog.md`), and validate `stories.yaml` schema rules (61 unique, prefix-free string IDs, no `status`, CAP-1..16 coverage). | Low |
| **3** | **Developer agent** | Apply §4.1C (`prerequisite-21-native-build-reuse.md`, `spec-21:45`, `spec-22:54`) and §4.2A–D (four non-frozen `## Verification` bullets + Spec Change Log entries in `spec-19`, `spec-21`, `spec-22`, `spec-26`) while verifying zero bytes changed inside any `<frozen-after-approval>` block. | Low |
| **4** | **Sprint planning readiness recheck (`bmad-sprint-planning`)** | Re-run implementation readiness to confirm PASS with zero `CONCERNS` and generate/proceed with sprint planning. | Low |
| **5** | **`bmad-build` (Stories `31-1` and `31-2`, when reached in order)** | Plan and review each prerequisite at its `spec_checkpoint: true`, implement in `references/Hexalith.Builds` (and CiCd render/templates if needed), qualify, and ship acceptable Builds releases prior to Stories `21` and `22`. | Medium |

### Success Criteria

1. `stories.yaml` parses cleanly with **61 unique, prefix-free quoted string IDs**, no `status` field, CAP-1..CAP-16 coverage preserved, `31-1` immediately before `21`, `31-2` immediately before `22`, and `20 → 31-1 → 21 → 31-2 → 22 → 24 → 23` order intact.
2. `spec-19:101`, `spec-21:106`, `spec-22:96`, and `spec-26:169` all accept a central `nightly.yml` run started after adoption on `main`, whether scheduled or authorized `workflow_dispatch` with `qualify-bump` false, with every `<frozen-after-approval>` block byte-for-byte unchanged.
3. `pipeline-stages.md:70` matches AD-18 (`ARCHITECTURE-SPINE.md:458`): up to two hours for two consecutive complete scans with no active `deliver.yml` run on `main`.
4. Sprint planning readiness re-run passes cleanly with zero remaining `CONCERNS`.

### Change Navigation Checklist Status

| Checklist Section | Status | Summary |
|---|---|---|
| **1.1–1.3** Trigger, core problem, evidence | `[x]` Done | All three readiness `CONCERNS` traced to exact files, line numbers, and `HEAD` blob IDs (`553d22bc`). |
| **2.1–2.5** Epic / backlog impact & sequencing | `[x]` Done | Assessed `21`, `22`, `19`, `26`, new `31-*` shared-runtime prerequisite family, and unaffected migrations; verified prefix-free IDs and relative cutover order. |
| **3.1–3.2, 3.4** PRD / Architecture / Secondary artifacts | `[x]` Done | Verified `SPEC.md` and `ARCHITECTURE-SPINE.md` need no edits now; scoped `pipeline-stages.md:70` and deferred Builds/CiCd code to `31-1`/`31-2`. |
| **3.3** UI/UX specifications | `[N/A]` Skip | No product UI/UX specifications exist in this repository. |
| **4.1–4.4** Path forward evaluation | `[x]` Done | Selected Option 1 (Direct Adjustment); Rollback and PRD MVP Review ruled out. |
| **5.1–5.5** Proposal components & handoff | `[x]` Done | Compiled complete Sprint Change Proposal with exact before/after diffs and Moderate-scope handoff. |
| **6.1–6.2** Checklist & proposal verification | `[x]` Done | Verified schema prefix-freedom (`31-1`, `31-2`), frozen-block preservation, and exact AD-18 wording alignment. |
| **6.3** Explicit user approval | `[x]` Done | Approved by the maintainer on 2026-11-27. |
| **6.4** Update `sprint-status.yaml` | `[N/A]` Skip | No `sprint-status.yaml` exists in this repo (`stories.yaml` is the backlog of record). |
| **6.5** Confirm next steps and handoff | `[x]` Done | §4.1–§4.3 edits applied and verified; `bmad-sprint-planning` readiness recheck and deferred `31-1`/`31-2` execution handed off. |
