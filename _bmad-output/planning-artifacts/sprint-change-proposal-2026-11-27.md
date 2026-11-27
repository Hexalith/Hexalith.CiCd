# Sprint change proposal for migration readiness

**27 November 2026 · Moderate scope · Three requested planning corrections applied**

## 1. Issue summary

Implementation readiness failed before tracker generation. The canonical backlog had 58 unique story IDs and references to CAP-1 through CAP-16. Three conflicting instructions gave the remaining migrations an incorrect cutover order, an obsolete Azure provisioning requirement, and inconsistent EventStore nightly acceptance. CiCd uses `SPEC.md` as its requirements contract and `stories.yaml` as its implementation backlog and sprint order. [Backlog](../specs/spec-cicd/stories.yaml) · [Requirements](../specs/spec-cicd/SPEC.md) · [Tracking decision](sprint-change-proposal-2026-11-18.md)

| Readiness finding | Evidence and governing decision |
| --- | --- |
| **Cutover order** | The backlog put Tenants (23) before FrontComposer (24), and the module inventory repeated that order. The adoption contract requires EventStore → FrontComposer → Tenants. [Backlog](../specs/spec-cicd/stories.yaml#L730) · [Module inventory](../specs/spec-cicd/module-inventory.md#managed-repositories) · [Adoption contract](../specs/spec-cicd/adoption-execution.md) |
| **EventStore Azure scope** | Story 20 directed the developer to provision the private runner and approval environment. On 17 November the maintainer confirmed on-premises Kubernetes as the MVP target and deferred Azure live qualification and its provisioning beyond MVP. Applicable on-premises Kubernetes/kind qualification and offline Azure checks remain required. [Story 20 backlog](../specs/spec-cicd/stories.yaml#L730) · [MVP decision](../specs/spec-cicd/evidence/23/mvp-onprem-target-decision.json) · [Ordered adoption runbook](../../docs/ordered-module-adoption.md#adoption-blockers-and-evidence-boundaries) |
| **EventStore nightly acceptance** | AD-21's EventStore note required an actual scheduled-night outcome. CAP-16 allows a scheduled or authorized dispatched nightly started after adoption, and AD-18 already defines both triggers. Story 20's change log records that the maintainer approved both triggers on 18 November. [AD-21](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-21--onboarding-sequence) · [CAP-16](../specs/spec-cicd/SPEC.md#L133) · [AD-18](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#ad-18--nightly-orchestration) · [Story 20 decision](../implementation-artifacts/spec-20-migrate-eventstore.md#spec-change-log) |

Source baseline is CiCd commit `6803c761d5979b0c7639b3b762f3a0d53fdbff9e`, tree `5db92e398b50280cd9bca60cc8055a96a362b100`. The backlog blob is `02ac7637aa817e09813e3a83945c193a1da904e8`, the requirements blob is `e683bde3039d89d0968e1147d01fcaa1ebda0b93`, and the spine blob is `3c0be2ca5c30d70e39e6ee2d5303a1bdfb4f2d3b`.

## 2. Impact analysis

| Area | Impact |
| --- | --- |
| Migration backlog | Story 20 now defines its MVP scope and nightly evidence. Stories 24 and 23 state their cutover dependencies in their dispatch notes. AD-20 cleanup still waits for fleet adoption. Existing product preparation is subject to its evidence and freshness rules. |
| Requirements | CAP-5 retains the reusable private qualification contract. CAP-13 and CAP-16 already define the permitted nightly triggers and acceptance evidence. The approved EventStore MVP decision applies to the provisioning and evidence scope of its adoption. |
| Architecture and operations | AD-21 follows CAP-16 for nightly acceptance and the ordered adoption runbook for EventStore qualification. The shared Builds interface handles qualification and the existing acceptance reader authenticates the nightly evidence. |
| Interfaces and UX | The affected interfaces are the existing Actions workflows and operator runbook. There are no product screens, UX specifications, API or configuration schema edits required for this correction. |

Shared infrastructure release qualification, candidate validation, product checks, the approved exact-input bootstrap before EventStore adoption, and the normal module checker afterward still govern execution. The approved adoption process requires one CiCd-owned delivery commit, exact green adoption CI, and AD-21 post-adoption cleanup. Required hosted qualification and post-adoption nightly acceptance need their own run evidence. [Story 20 implementation spec](../implementation-artifacts/spec-20-migrate-eventstore.md) · [Adoption blockers](../../docs/ordered-module-adoption.md#adoption-blockers-and-evidence-boundaries) · [Publication policy](../../docs/pre-adoption-publication.md)

## 3. Recommended approach

The direct planning correction updates the backlog order, records the previously approved MVP scope in Story 20 and aligns AD-21 with the nightly policy. The implementation timeline still depends on qualification and delivery evidence. An eligible dispatched nightly can remove the wait for the next scheduled start.

The main risks are a premature cutover, treating offline Azure evidence as live qualification, or counting a disabled release as nothing to release. Use each predecessor's adoption receipt, record the on-premises and offline Azure checks with their actual outcomes, and authenticate the EventStore row of the qualifying nightly. A successful `publishing disabled` release remains a valid controller outcome and leaves CAP-16 acceptance pending. Keep publication disabled during cutover and follow the existing separate authorization for any later product release. [Ordered adoption](../../docs/ordered-module-adoption.md) · [Nightly outcomes](../../docs/nightly.md#L47) · [Acceptance reader](../../tools/nightly_acceptance.py#L450)

Rollback would discard completed preparation without resolving the document conflicts. A new MVP review would reopen the maintainer's recorded target decision.

## 4. Detailed changes

### 4.1 Cutover sequence

| Artifact and section | Before | Applied change |
| --- | --- | --- |
| [Backlog, stories 20–26](../specs/spec-cicd/stories.yaml#L730) | `20 → 21 → 22 → 23 → 24 → 25 → 26` | Story 24 moved immediately before Story 23. The block reads `20 → 21 → 22 → 24 → 23 → 25 → 26`. |
| [Story 24, `invoke_dev_with`](../specs/spec-cicd/stories.yaml#L799) | The note went from standard AD-21 preparation to delivery without naming a predecessor. | FrontComposer cutover requires EventStore's accepted delivery and green adoption CI. |
| [Story 23, `invoke_dev_with`](../specs/spec-cicd/stories.yaml#L823) | The note went from standard AD-21 preparation to delivery without naming a predecessor. | Tenants cutover requires FrontComposer's accepted delivery and green adoption CI. |
| [Module inventory, Managed repositories, migration order item 6](../specs/spec-cicd/module-inventory.md#managed-repositories) | “Then by local workflow YAML size: Projects, ChatBot, EventStore, Parties, Memories, Tenants, FrontComposer.” | The inventory follows the corrected order and links to the ordered adoption contract. |

This placement satisfies the mandated relative order and keeps Parties and Memories in their existing positions. Story 24's product acceptance and Story 23's package graph, worker isolation and coverage checks still apply. [Ordered adoption contract](../specs/spec-cicd/adoption-execution.md) · [Module qualification requirements](../../docs/ordered-module-adoption.md#required-product-preparation)

### 4.2 EventStore MVP qualification

| Artifact and section | Before | Applied change |
| --- | --- | --- |
| [Story 20, `description`](../specs/spec-cicd/stories.yaml#L732) | The private manual Azure contract appeared alongside current migration work, with offline schema coverage mentioned separately. | Qualify applicable on-premises Kubernetes/kind routes, run offline Azure schema, payload, invariant and security checks without Azure secrets, and preserve the compatible manual Azure contract (CAP-5). |
| [Story 20, `invoke_dev_with`](../specs/spec-cicd/stories.yaml#L740) | “Provision the private runner and approval environment without manufacturing Azure authority or running faults.” | Require on-premises qualification and offline Azure checks for MVP. Defer dedicated Azure runner, approval environment, authority and secret custody provisioning and live Azure qualification until post-MVP. |
| [Adoption execution contract, final paragraph](../specs/spec-cicd/adoption-execution.md#L49) | The live runner, environment and credential requirements applied without distinguishing routes. | Verify the live requirements for enabled routes before cutover and use hosted evidence to establish live outcomes. Record EventStore's required MVP checks and deferred Azure work explicitly. |

The approved Story 20 boundaries already contain the maintainer's scope decision. Its evidence task now explicitly names applicable on-premises qualification and offline Azure checks. The added acceptance criterion gives each its own evidence. [Story 20 Tasks & Acceptance](../implementation-artifacts/spec-20-migrate-eventstore.md#tasks--acceptance) · [Story 20 MVP clarification](../implementation-artifacts/spec-20-migrate-eventstore.md#L45)

> Given the approved MVP routes, record successful applicable on-premises Kubernetes/kind qualification and passing offline Azure schema, payload, invariant and security checks in ordinary CI without Azure secrets. Record Azure live qualification and its runner, environment, authority and secret custody provisioning as deferred until post-MVP.

### 4.3 EventStore nightly acceptance

| Artifact and section | Before | Applied change |
| --- | --- | --- |
| [AD-21, step 4](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#L620) | “Done when the module's CI is green and its next nightly release succeeds, or reports nothing to release.” | Require green CI and the module's own passing CAP-16 outcome from a central `nightly.yml` run started after adoption on `main`. Both scheduled and CAP-13-authorized dispatched runs qualify, with `qualify-bump` false for dispatch. |
| [AD-21, EventStore-only bootstrap](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#L654) | “Legacy publishing/tool assets remain until adoption; release/provisioning and an actual scheduled-night outcome remain prerequisites for story completion.” | Keep legacy assets until adoption and require the compatible Builds release, applicable provisioning and MVP qualification in the ordered adoption runbook. Close Story 20 with the normal checker, green adopted CI and EventStore's authenticated outcome under step 4. |
| [AD-21, AI.Tools applicability](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md#L644) | AI.Tools waited for Story 11's “genuine scheduled-night checkpoint.” | The dependency cites Story 11's CAP-13 nightly checkpoint, which already accepts both triggers. |
| [Story 20 backlog, `invoke_dev_with`](../specs/spec-cicd/stories.yaml#L740) | The note called for a CAP-13 publication or valid no-release result without specifying timing or trigger. | Record the normal checker, green adoption CI, applicable MVP qualification and EventStore's own passing CAP-13/CAP-16 nightly evidence from either eligible post-adoption trigger. |
| [Story 20 implementation spec, final acceptance criterion](../implementation-artifacts/spec-20-migrate-eventstore.md#tasks--acceptance) | The criterion required successful publication or a valid no-release result from a nightly after adoption. The dispatch conditions appeared in the Spec Change Log. | Authenticate EventStore's eligibility, CodeQL, verified publication or valid nothing-to-release, qualifying scan evidence for the dispatch commit and any required post-bump delivery evidence. |

CAP-13 and CAP-16 already express the approved requirement. AD-18 already defines the central schedule and authorized dispatch behavior. The same evidence checks apply to both triggers. Preserve the standalone acceptance reader's requirements and record the adoption commit and time, nightly run and attempt, EventStore release run and dispatch SHA, and relevant scan and delivery identities. A fixture or an isolated release job cannot supply that evidence. [Nightly policy](../specs/spec-cicd/SPEC.md#L109) · [On-demand decision](sprint-change-proposal-2026-11-18-on-demand-nightly.md) · [Acceptance reader](../../tools/nightly_acceptance.py)

## 5. Implementation handoff

The maintainer requested the three corrections on 27 November. The planning edits are recorded in the specification and architecture decision logs and Story 20's Spec Change Log. The CiCd developer uses `stories.yaml` for sprint order and follows the ordered adoption runbook for the later module work. The maintainer handles the applicable AD-21 provisioning and any separate publication authorization. [Story Breakdown rules](../../.agents/skills/bmad-spec/assets/stories-schema.md) · [Ordered adoption runbook](../../docs/ordered-module-adoption.md)

**Readiness recheck for the three findings passed.**

1. The backlog parses with 58 unique IDs, all 16 capability references and the original checkpoints. Only Story 24 moved, giving the cutover order `20 → 24 → 23`.
2. The backlog, Story 20 acceptance and the adoption and architecture companions agree on on-premises and offline Azure MVP checks. Azure-specific live qualification and provisioning are recorded as post-MVP. Story 20's frozen block is byte-for-byte identical to the baseline.
3. AD-21 and Story 20 accept both CAP-16 trigger paths and require the same module evidence. All 64 existing nightly acceptance reader tests passed. Hosted qualification, adoption and the qualifying nightly are required operational evidence for Story 20.

### Checklist and approval record

| Checklist | Status |
| --- | --- |
| 1.1–1.3, trigger and evidence | `[x]` Readiness findings traced to the current sources and the maintainer decisions. |
| 2.1–2.5, story and migration impact | `[x]` Assessed the affected migration block, existing story order and fleet cleanup dependency. |
| 3.1, 3.2, 3.4, planning and technical artifacts | `[x]` Checked the requirements, architecture, companions, runbook and evidence path. |
| 3.3, UX | `[N/A]` Product UX is outside this correction. |
| 4.1–4.4, response options | `[x]` Direct correction selected within the approved MVP. |
| 5.1–5.5 and 6.1–6.2, proposal and verification | `[x]` Applied and verified the three corrections. |
| 6.3–6.5, approval, tracking and handoff | `[x]` Recorded the maintainer's direction, updated `stories.yaml` and documented the operational handoff. |
