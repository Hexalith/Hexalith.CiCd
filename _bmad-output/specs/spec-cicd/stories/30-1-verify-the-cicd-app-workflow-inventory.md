---
title: 'Verify the CiCd App workflow inventory'
type: 'feature'
created: '2026-11-22'
status: 'done'
baseline_revision: 307405aba85e587982b69d6ce5847ab2c06000a3
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred:
  - summary: >-
      Complete current App selected-repository membership remains unverified.
    evidence: |-
      Read-only maintainer GET user/installations/179966090/repositories returned HTTP 403 with request identity and response digest retained in evidence/30-1/hosted-readback-20261122.json. Installation grants and the environment client-ID binding were readable; neither proves the full selected-repository set. A reader authorized for installation repository enumeration is needed. Preserve story 11's accepted open Hexalith.Docs exception.
    location: >-
      docs/cicd-app-inventory.md
    severity: medium
  - summary: >-
      Current route-specific owner continuation or retirement confirmations remain pending.
    evidence: |-
      All thirteen migration route/profile records preserve historical authority and read-only hosted results but have retirement_confirmation_observed false. No route was removed. The corresponding EventStore or Projects owner must provide an attributable decision before retirement; historical success cannot supply consent.
    location: >-
      docs/cicd-app-inventory.md#migration-owner-dispositions
    severity: medium
  - summary: >-
      Workflow discovery skips case-variant extensions such as .YML.
    evidence: |-
      tools/check_app_inventory.py and check_global.workflow_paths compare path.suffix case-sensitively, so a .github/workflows file ending .YML that selects cicd-app is not inspected. GitHub documents only .yml and .yaml and does not state whether matching is case-sensitive. A hosted probe of an uppercase-extension workflow, or an authoritative GitHub statement, settles it; if GitHub runs such files, casefold the suffix in both discovery paths.
    location: >-
      tools/check_app_inventory.py:184
    severity: medium (unverified)
---

<intent-contract>

## Intent

**Problem:** AD-7 names seven App-consuming workflows, but source validation does not enforce that inventory. Hosted settings and migration-owner retirement decisions require separate evidence.

**Approach:** Enforce a reviewed job and token allowlist during CiCd validation, qualify discovery and scope refusals, and reconcile it with read-only hosted observations and explicit owner dispositions under the approved 2026-11-19 proposal.

## Boundaries & Constraints

**Always:** Discover every parent workflow selecting `cicd-app` or referencing `HEXALITH_CICD_APP_PRIVATE_KEY`. Bind job identity, environment, conditions, token step identity, owner, repository selection and every requested permission, including manual profiles and dynamic selectors. Preserve fixed controller bounds and existing product gates. Keep only compact identities, digests and links as evidence. Use `run-with-temp` for disposable verification. Record authorization failures as unverified configuration.

**Never:** Read or mint the App key, dispatch publication or delivery, change hosted grants/settings, edit module-owned perimeters, or retire a route without that route's owner's explicit confirmation. Historical preparation approvals and successful runs do not imply retirement consent.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Reviewed source | Current seven workflows and closed profiles | Ten privileged jobs and their token scopes accepted | Read-only check succeeds |
| Discovery drift | Unknown workflow/job uses environment or key, independently | Inventory check rejects the new consumer | Contextual nonzero verdict |
| Scope drift | Target, owner, permission, matrix or profile selection widened | Source check refuses the changed boundary | Identify workflow/job/step |
| Hosted access | Readable environment/grants, inaccessible selected-repository API | Preserve verified observations and exact refusal separately | Never infer missing configuration |
| Owner decision | Historical scoped authority without retirement confirmation | Keep route; record pending owner confirmation and retirement condition | No removal |

</intent-contract>

## Code Map

- `.github/workflows/` — seven consumers: `deliver.yml`, `nightly.yml`, `qualify-package-owner-access.yml`, `propose-eventstore-contracts-prerequisite.yml`, `deliver-contracts-prerequisites.yml`, `dispatch-contracts-prerequisites.yml`, `deliver-projects-ci-gates.yml`; ten jobs, 76 mint steps at the baseline. Delivery includes `projects-g6-catalog`.
- `tools/check_global.py:481` — global validation entry point; `run_tool_tests` discovers locked parent tool suites. `tools/render.py:75` supplies strict duplicate-rejecting YAML parsing.
- `tools/delivery_bootstrap.py`, `tools/nightly.py`, `tools/nightly_runtime.py` — trusted dynamic selectors, accepted registrations and bounded token use; preserve existing qualification.
- `docs/contracts-prerequisites/owner-routes.md`, `docs/projects-ci-gates-repair.md`, `docs/contracts-prerequisites/approver.json` — closed owner authorizations; no retirement authority.
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md` — authoritative 30-1 acceptance and per-route retirement conditions.
- Architecture spine AD-7 includes all seven consumers; `SPEC.md` and `enforcement.md` retain stale two-workflow wording and need reconciliation.
- Story 11 records an accepted open `Hexalith.Docs` installation exception. Story 1's historical environment observations are not current proof. All 31 existing story specs were consulted for continuity; preserve their completed outcomes.

## Tasks & Acceptance

**Execution:**
- [x] `tools/check_app_inventory.py` and `tools/app-workflow-policy.json` — implement an offline, strict, readable job/token boundary check covering both discovery signals and closed manual profiles.
- [x] `tools/check_global.py` — invoke the inventory check as a secret-free global check without changing delivery verdict semantics.
- [x] `tools/tests/test_app_inventory.py` and its lock — exercise real parent source and mutated disposable fixtures for unknown workflows/jobs, independently missing environment/key, widened repository/owner/permission/matrix/profile and malformed input.
- [x] `docs/cicd-app-inventory.md`, `SPEC.md`, `enforcement.md` and AD-7 — document the reviewed inventory, dynamic selection bounds, source discrepancies and owner conditions; reconcile stale descriptions without implying hosted compliance.
- [x] `_bmad-output/specs/spec-cicd/evidence/30-1/` — record baseline commit/tree/workflow blob IDs, read-only hosted request identities/digests, settings/grants/refusals, and an explicit disposition for each migration route/profile. Preserve pending owner decisions and the Docs exception.

**Acceptance Criteria:**
- Given all parent workflows, when CiCd validation runs, then every environment or key consumer must match the reviewed workflow/job/token allowlist, including manual profile repository and permission bounds.
- Given an unknown consumer, widened target or widened permission, when the actual checker runs against changed source, then it fails with the responsible boundary identified.
- Given hosted readback, when reconciled with source, then deployment-branch policy, allowed branch, selected-repository evidence and effective installation grants have verified results or precise access refusals; account administration alone is not permission proof.
- Given each migration route, when disposition is recorded, then it names the owner, retained evidence, discrepancies or pending confirmation, and the exact retirement condition. Removal requires the corresponding owner's explicit confirmation.
- Given the existing controller and renderer checks, when the new check is integrated, then the parent verdict contract and generated module files remain valid.

## Spec Change Log

## Review Triage Log

### 2026-11-22 — Review pass
- verdicts: 16 findings — high 1, medium 6, low 7, false 2, maybe-false 0
- findings:
  - `[medium]` `[patch]` Verification-gap: an unrelated selected-contract failure masks whether inventory errors affect the global verdict — reviewer demonstrated that swallowing inventory errors still passed all 13 tests; fixed the integration test with otherwise successful checks, baseline success and inventory-only failure; all 17 inventory methods now pass.
  - `[false]` `[reject]` Intent alignment: source mutation checks do not themselves mint and probe every token — the approved 30-1 acceptance selects source-boundary mutation tests plus read-only hosted reconciliation; live token minting is not required. Existing controller qualification remains in use and is rerun where relevant.
  - `[medium]` `[defer]` Intent alignment: complete hosted membership is unverified — pre-existing read refusal is retained precisely with request identity; no configuration absence or unconditional compliance is claimed. A permitted installation-membership read settles this.
  - `[medium]` `[defer]` Intent alignment: owner-authored current dispositions have not been obtained — all thirteen rows explicitly retain pending confirmation. This is a pre-existing missing decision; successful runs do not substitute for it and no retirement is performed.
  - `[false]` `[reject]` Intent alignment: retirement was not executed — retirement was conditional on corresponding owner confirmation and no route was removed; the conditional requirement is preserved.
  - `[high]` `[patch]` Edge-case: an unreviewed reusable-workflow job can select the caller's environment in its callee without a literal signal — actual checker accepted the fixture; GitHub reusable-workflow documentation confirms environment secrets are selected at callee job level. Reject unreviewed job-level reusable calls, including calls without inherited secrets, and cover both paths.
  - `[medium]` `[patch]` Blind hunter: computed secret indexing bypasses literal key discovery — actual checker accepted the computed-key fixture; reject unresolved computed secret indices independently, retaining harmless unrelated literal references.
  - `[low]` `[patch]` Blind hunter: substring search confuses unrelated environment names and URL text with the actual environment name — match the literal name exactly and preserve conservative expression handling; cover suffix and URL-only fixtures.
  - `[medium]` `[patch]` Blind hunter: live App grants lacked a current binding to the workflow variable — read-only environment-variable and installation GETs now verify the explicit nonsecret client-ID match. The repository-variable 404 is retained without an absence inference.
  - `[medium]` `[patch]` Blind hunter: artifact metadata lacked authenticated list-request and workflow-run bindings — fresh GETs now retain request IDs and response/body digests; each artifact's unchanged identity/digest and returned workflow_run.id are verified against its claimed run.
  - `[low]` `[patch]` Blind hunter: several retained suite results lack log digests — repeat the relevant suites with disposable raw logs and retain one-line outcomes, output sizes and SHA256 digests.
  - `[low]` `[patch]` Blind hunter: parent verification includes unittest dots and separator output — replace result arrays with concise outcome strings while preserving existing digests and byte counts.
  - `[low]` `[patch]` Blind hunter: older unconditional credential wording conflicts with authorized interactive maintainer reads — reconcile documentation with the command-local repository-administration exception; retain CiCd-agent for ordinary/unattended work and preserve the default profile.
  - `[low]` `[patch]` Blind hunter: inherited proxy bypass and gh configuration weaken the claimed offline proof — isolate credential configuration, clear proxy bypass and exercise direct checker calls under denied sockets without host networking changes.
  - `[low]` `[patch]` Blind hunter: mutation fixture copying fails on harmless workflow subdirectories — filter the fixture copy to the workflow YAML file set used by production discovery.
  - `[low]` `[patch]` Blind hunter: conservative source hashes lack a renewal procedure — document manual scope review, canonical digests, full revision identities and qualification; add no auto-approval or regeneration mode.

### 2026-11-22 — Review pass
- verdicts: 36 findings — high 0, medium 8, low 18, false 9, maybe-false 1
- findings:
  - `[false]` `[reject]` Intent alignment: enforcement is a validation verdict that skips `projects-g6-catalog` and does not block other workflows — the intent places enforcement "during CiCd validation" and the spec preserves delivery verdict semantics; a blocking hosted barrier would change hosted settings, which the intent forbids. The real-path verification part is the global-path row below.
  - `[false]` `[reject]` Intent alignment: dynamic bounds are frozen by controller hashes, not evaluated, and a controller failure names the file — the Design Notes bind selector context rather than treating expressions as runtime evidence; a controller change is refused at its responsible boundary, the controller path.
  - `[false]` `[reject]` Intent alignment: "owner" binds only the token input — the intent lists owner among token-binding fields; route owner roles are recorded in every disposition, so no required binding is missing.
  - `[medium]` `[defer]` Intent alignment: the Hosted access row is a recorded fact and the selected-repository comparison stays unverified — carried: same claim as the earlier membership row. Still HTTP 403 for both profiles at 16:55 UTC, later superseded by story 30-3's all-mode readback. Not re-deferred.
  - `[false]` `[reject]` Intent alignment: "no removal" is not enforced and nothing reads `retirement_confirmation_observed` — removing a consumer fails the checker until a reviewed policy edit; the intent's Never clause constrains implementers and nothing was removed.
  - `[medium]` `[patch]` Intent alignment: the credential policy changed beyond the intent — grouped with the credential rows below; narrowed per the user's decision.
  - `[false]` `[reject]` Intent alignment: discovery also fails unrelated reusable calls, dynamic environment names and computed secret indices — this over-breadth is the fail-closed consequence of confirmed callee environment selection and runtime secret selection; current source has no unrelated uses and the guide documents renewal.
  - `[false]` `[reject]` Intent alignment: narrowing is refused and diagnostics say "differs" — exact match is the reviewed fail-closed boundary, and every refusal names its workflow/job/step/field path.
  - `[false]` `[reject]` Intent alignment: evidence is not compact — every added `_bmad-output` file is below 256 KiB; request headers and the account login/ID are the compact identities AGENTS.md asks for; the policy is executable input under `tools/`.
  - `[medium]` `[patch]` Blind hunter: SPEC, enforcement and AD-7 approved unattended BMAD Loop use of the CiCd-agent token and dropped the no-personal-login rules — memlog line 27 records the approved decision that this token is for interactive sessions only. Per the user's decision this pass, restored the approved rules with one exception: read-only GETs the user explicitly authorizes interactively, run with the command-local maintainer profile. The guide records unattended BMAD Loop use as a deviation awaiting a decision.
  - `[medium]` `[patch]` Blind hunter: the maintainer exception covered "repository administration", including writes, and was unenforced — same group; the exception now covers only read-only GETs, run command-local with `GH_TOKEN`/`GITHUB_TOKEN` unset, and never becomes the session default.
  - `[low]` `[patch]` Blind hunter: AD-7's CiCd-agent bullet lost its scope statement to a workstation path — same group; restored the fine-grained Builds/CiCd Contents, Workflows and Actions write scope, interactive only.
  - `[low]` `[patch]` Blind hunter: delivery controller hashes bind working-tree files that the select/permit/module steps do not run — confirmed: the deliver job runs the bootstrap and its sibling runtime from commit `03d130f82366dec8ed70a21a14177ae55ea09ca1`, bound by the checkout step digest. Corrected the guide and both policy `bound` statements; no hash changed.
  - `[medium]` `[patch]` Blind hunter: nothing checks that `context_jobs` covers each consumer's transitive `needs` — the checker accepted a policy without `bump-push` or `scan`. Added a needs-closure guard and `test_unbound_transitive_dependency_job_fails`; a mutation removing the guard fails it.
  - `[low]` `[reject]` Blind hunter: `selector_sources` completeness is unchecked — hashed selectors validate producer outputs against the committed registry, capacity and fixed identities, so unhashed producers cannot widen targets past those bounds. Deriving every invoked script and import is new analysis, not a direct correction.
  - `[low]` `[patch]` Blind hunter: the discrepancy audit omits inline Python against AD-7's "from CiCd's `tools/`" — confirmed two `python3 -I -c` steps in each nightly App job and a `python3 -I -` heredoc in the prerequisite dispatch job. The guide records them as a literal deviation bound by step digests.
  - `[low]` `[patch]` Blind hunter: admin bypass is recorded but not classified — the guide now says `can_admins_bypass: true` is not main-only proof for administrators, does not establish branch-policy coverage, falls within the accepted org-owner residual, and that no setting changed.
  - `[false]` `[reject]` Blind hunter: DW-38 and the guide omit remediation for the HTTP 403 — superseded: story 30-3 (`c311d1f3`) verified `repository_selection: all`, closed DW-38 and rewrote the guide's hosted section.
  - `[low]` `[reject]` Blind hunter: owner dispositions do not define who confirms or how — role-level owners match the approved 19 November proposal, `approver.json` excludes retirement authority and DW-39 tracks the decisions. A new attestation protocol is not a direct correction.
  - `[low]` `[patch]` Blind hunter: retirement conditions refer to other rows and dispatch owners conflict with "both owners" — every "Same …" condition is now explicit. Contracts and dispatch rows name both owners and the confirming owner, matching the proposal and receipt; the visibility rows note that one matrix job serves both owners.
  - `[low]` `[reject]` Blind hunter: retained run evidence has no `expires_at` — AGENTS.md keeps raw artifacts in Actions under retention and digests in Git; the receipts' digests outlive the archives, and expiry metadata needs new hosted reads.
  - `[low]` `[patch]` Blind hunter: no recorded run covers the real global path — ran the real `tools/check_global.py`. The App workflow inventory, all offline checks and the tool suites passed; three online checks refused locally without a read-only GitHub token, a pre-existing precondition. Recorded below.
  - `[low]` `[reject]` Blind hunter: reusable-call approval is untested and needs no pinned ref — no reusable call exists, any approval is a reviewed policy edit whose renewal requires callee review, and pin enforcement would guard an absent state.
  - `[low]` `[reject]` Blind hunter: `reviewed_revision` is never verified — it is review metadata; ancestry checks need history that shallow CI checkouts lack and would add a failure mode.
  - `[low]` `[patch]` Verification gap: the workflow-level computed secret index refusal is untested — added an unreviewed workflow with a computed top-level `env` index to `test_top_level_key_reference_and_removed_consumer_fail`; deleting that check now fails it.
  - `[medium]` `[patch]` Verification gap: the policy token-entry rules are untested — added `test_policy_token_entries_require_explicit_owner_key_action_and_permissions`, which changes source and policy identically. Deleting the owner, key, action, permission or `cicd-app` boundary rule each fails it.
  - `[low]` `[reject]` Edge-case: YAML 1.1 parses `050` as 40 — this requires a deliberately non-canonical literal, and the fix is a new scalar guard in the shared renderer loader.
  - `[low]` `[reject]` Edge-case: `toJSON(secrets)` escapes computed-index detection — the key exists only in `cicd-app`, whose literal or dynamic selection is discovered independently, so a dump without it cannot reach the key; the form is rare and the fix adds a branch.
  - `[maybe-false]` `[defer]` Edge-case: case-variant extensions such as `.YML` skip discovery — GitHub documents `.yml`/`.yaml` without stating case sensitivity; a hosted probe or authoritative statement settles it. Deferred as medium (unverified).
  - `[low]` `[reject]` Edge-case: a policy could list a mint step under `context_steps` — its digest still binds the step exactly; only renewal readability suffers, and the fix adds a guard.
  - `[medium]` `[patch]` Edge-case: the transitive needs closure is unchecked — same root cause as the blind-hunter needs row; guard and test added.
  - `[low]` `[reject]` Edge-case: producer scripts `validate.py` and `bump_push.py` are unhashed — same root cause and reason as the `selector_sources` row.
  - `[low]` `[patch]` Edge-case: deliver runs `delivery_runtime.py` from the pinned checkout — same root cause as the controller-hash row; corrected.
  - `[low]` `[patch]` Edge-case: the integration test compares an unresolved root with `run()`'s resolved path — confirmed at `tools/check_global.py:490`; the assertion now uses `root.resolve()`.
  - `[false]` `[reject]` Edge-case: unhashed `setup/*.yml` lets a registry addition widen deliver and nightly targets — the committed setup registry is the designed dynamic target source, named by the reviewed policy bound and by approved AD-7. CAP-4/CAP-16 govern adoption, and the hashed controllers enforce its bounds.
  - `[medium]` `[patch]` Edge-case: the interactive-only CiCd-agent limit and unattended personal-token ban were deleted — same group as the blind-hunter credential row; restored.

## Design Notes

Source enforcement and hosted observations establish different facts. Bind dynamic expressions and their selector context; do not treat an expression string as evidence of its runtime repository set. The current package-visibility diagnostic uses inline non-isolated Python; the optional proposal token requests an ungranted Pull requests scope. Record these discrepancies explicitly. A denied read or missing retirement confirmation must remain visible, without granting access or deleting a live route.

## Verification

**Commands:**
- `run-with-temp uv run --locked --script tools/tests/test_app_inventory.py` — positive source and negative boundary cases pass.
- `run-with-temp uv run --locked --script tools/tests/test_validate.py` — validation behavior remains compatible.
- `run-with-temp uv run --locked --script tools/render.py --check` — committed render remains unchanged.
- Read-only maintainer-profile GitHub GETs — environment policy and installation permissions reconciled; failures retained with request IDs and digests. Never output credentials.

## Auto Run Result

Status: done (follow-up review pass).

Story 30-1 enforces the reviewed App workflow inventory as a secret-free global
check: seven workflows, ten privileged jobs and 76 mint steps. This pass reviewed
the complete change since `307405aba85e587982b69d6ce5847ab2c06000a3` with four
reviewers and triaged 36 findings above. At the user's direction, story 30-3's
uncommitted work in the same tree was committed unchanged first as
`c311d1f3`, and these patches were applied on top.

Changed files in this pass:
- `tools/check_app_inventory.py` — rejects a consumer whose transitive `needs` job is not bound.
- `tools/tests/test_app_inventory.py` — closure, policy token-entry and top-level computed-index tests, plus a resolved-path assertion (19 tests).
- `tools/app-workflow-policy.json` — corrected the `bound` statements for the delivery bootstrap and runtime; no digest changed.
- `docs/cicd-app-inventory.md` — pinned delivery selector, narrowed credential exception, admin bypass, inline-Python deviation, explicit retirement conditions.
- AD-7, `SPEC.md` and `enforcement.md` — restored the approved CiCd-agent and personal-login rules, with one read-only GET exception.

Review: 10 entries patched (high 0, medium 3, low 7). Deferred: `.YML`
discovery (medium, unverified). Carried: selected-repository membership, already
deferred and since superseded by 30-3. Rejected:
- low, not direct corrections: `selector_sources`/producer completeness, owner attestation protocol, artifact expiry, reusable-call pin, `reviewed_revision` ancestry, YAML 1.1 octal, `toJSON(secrets)`, mint step in `context_steps`;
- false: the enforcement surface, frozen bounds, owner binding, no-removal enforcement, discovery breadth, exact match, evidence size, superseded 403 remediation, unhashed setup registry.

Follow-up review recommended: **false**. This follow-up pass patched no high
finding (medium 3, low 7).

Verification (raw logs discarded; SHA-256 of each log):
- `run-with-temp uv run --locked --script tools/tests/test_app_inventory.py` — 19 tests OK, `9ea8bf0740d466675529bd0534d15f601a00836a28dfc2f46a5d60a0fdd232f2`.
- `run-with-temp uv run --locked --script tools/tests/test_validate.py` — 54 tests OK, `ca3176c0a78b1ae53af56b7264afc954cddbe450f354bc492f79313b6466a2fe`.
- `run-with-temp uv run --locked --script tools/render.py --check` — exit 0, no output.
- `run-with-temp uv run --locked --script tools/check_global.py` — exit 1, `6e72cdb0d788bae679bb74d0eaeaf319fce0b9d37b023b403aa6bad60edae2e6`. Passed: App workflow inventory, render inputs, render, reproducibility, schemas and all tool suites. Refused locally without a read-only GitHub token: immutable delivery bootstrap, acceptable Builds publication, workflow lints. CI supplies that token.
- Mutation runs on a disposable copy — 7 of 7 guard deletions fail the new tests; the unmutated copy passes, `d5918a6d2138b32cf9601fc5b803217883cd18d428cbcb4f102ce30f6eca80f6`.
- Read-only hosted retry, 16:55 UTC. It ran after the user said the 403 was fixed and before 30-3 was found in the tree. `user/installations/179966090/repositories` still returned HTTP 403 with both profiles: maintainer `D261:2D801A:133624E5:1CF4BA6A:6B031E70`, CiCd-agent `D297:35FB30:1345C96D:1D16611A:6B031E85`. The maintainer org membership read returned `admin` (`D257:2D1CF5:134765B4:1D1AB8FA:6B031E70`). Story 30-3's all-mode readback supersedes the listing.

Residual risks: unattended BMAD Loop sessions still run with the CiCd-agent
profile, now recorded as an AD-7 deviation awaiting a decision. `.YML`
discovery is unverified. Online global checks were not exercised locally. DW-39
owner confirmations remain pending. No hosted setting, grant, key or live route
changed.
