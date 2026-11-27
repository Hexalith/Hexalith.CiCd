---
title: '19: Migrate ChatBot'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '66e3a5a3a0e9bb01dd161c19349953594e01a22f'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ChatBot has bespoke push-triggered releases and story-evidence gates, and lacks the shared security, commit-format and dependency-update baseline.

**Approach:** Follow AD-21: prepare product changes, register/render in CiCd, and let App delivery adopt ChatBot. Preserve topology, browser and recovery validation. Completion requires green adopted CI and the next central nightly outcome.

## Boundaries & Constraints

**Always:** Use module-agent for ChatBot product writes, CiCd-agent for CiCd/Builds, and command-local maintainer access for administration. Preserve SDK 11.0.100, product coverage, weekly recovery cadence and foreign content. Meet maintainer preconditions before product pushes.

**Never:** Directly edit owned content in ChatBot, initialize nested submodules locally, weaken tests/audits, broaden credentials, or revoke legacy publishing access before adoption. After adoption require the standard local checker.

**Human decisions, 2026-11-16:**

- Before adoption only, approve the pilot-style verification exception for ChatBot product pushes: fresh-main package-mode product build/tests, applicable package/consumer checks, policy/commit validation and byte/mode/gitlink comparisons proving owned content unchanged. Preserve successful results for each exact pushed revision. The exception ends at App adoption; subsequent pushes require the standard checker.
- Retain explicitly declared, gitlink-pinned AppHost executable/composition source dependencies, including required composition helpers. Remove direct sibling library projects from the solution and keep ordinary library references in package mode. This is a topology-specific exception, not general permission to build libraries from source.
- Ship long-running nightly-hook support as a separate prerequisite, described in `prerequisite-19-long-running-nightly-hooks.md`. Reuse existing token refresh and handoffs, preserve the 45-minute default, and block ChatBot adoption until the capability is released and available. Preserve weekly recovery scenarios, multi-hour allowances and cleanup.

## I/O & Edge-Case Matrix

| State | Result |
| --- | --- |
| Preconditions and verification pass | Register/render; authenticate App adoption |
| Prerequisite absent/unreadable | Block adoption; distinguish absence from access refusal |
| Product failure | Fix product; retain assertions |
| No releasable change | Accept authenticated nightly “nothing to release” |

</frozen-after-approval>

## Code Map

- `_bmad-output/specs/spec-cicd/evidence/19/{preflight.json,code-investigation.md}`: canonical revisions, current prerequisites, exact deletion/retention inventory and dependency details. Read both for implementation; architecture AD-12–14/21 governs.
- ChatBot `Hexalith.ChatBot.slnx`, `Directory.Build.props`, `Directory.Packages.props`, `src/Hexalith.ChatBot.AppHost/Hexalith.ChatBot.AppHost.csproj`: solution/package/source boundary.
- ChatBot `eng/ChatBot.Composition.{props,Restore.targets}`, `Directory.{Build,Solution}.targets`: shared package-mode Tooling inputs and propagation through the pinned SDK's restore/build graph.
- ChatBot `tests/Hexalith.ChatBot.IntegrationTests/LiveCatalogFixture.cs` and AppHost `Program.cs`: real compiled-owner enrollment, matching published catalog helper, private custody and fresh isolated business backend; default AppHost launch remains unchanged.
- ChatBot `tests/Hexalith.ChatBot.{Live.IntegrationTests,Release.Tests,Recovery.Tests}/`, `tests/required-live.xunit.runner.json` and `.github/actions/{after-unit-tests,nightly}/`: whole-project required CI/release/recovery routing and zero-skip enforcement. The original optional manual observer producer stays in ordinary integration.
- ChatBot `tests/Hexalith.ChatBot.Architecture.Tests/{ReleaseWorkflowSafetyTests,LiveRecoveryValidationArchitectureTests,ScaffoldArchitectureTests}.cs`: obsolete workflow assertions mixed with product assertions.
- ChatBot `tests/Hexalith.ChatBot.IntegrationTests/Recovery/LiveContinuityAspireE2eTests.cs` and Server `Audit/`: genuine recovery behavior; preserve it.
- CiCd `setup/README.md`, `tools/{render,validate}.py`, `templates/`, `rendered/`: existing generation, validation and delivery interfaces.

## Tasks & Acceptance

**Execution:**
- [ ] Story `29-3` (`prerequisite-19-long-running-nightly-hooks.md` items 4–5) — require the scheduled CiCd wait-continuation prerequisite to ship before registering ChatBot (items 1–3 already shipped in Builds `v6.1.0` and CiCd render). The prerequisite is a separate deliverable; story 19 does not implement shared timing support.
- [ ] `evidence/19/` — verify/provision AD-21 App selection, exact rulesets, stale release/CodeQL cleanup, release environment with module-only Zot identity, scoped NuGet policy, publish switch and shared org access. Record sanitized before/after metadata. Rulesets/environment/switch/access are missing; App selection/NuGet policy are unverified; retention/push protection pass.
- [x] ChatBot `tools/Hexalith.ChatBot.StoryEvidenceGate/`, `tests/Hexalith.ChatBot.StoryEvidenceGate.Tests/`, `story-evidence-policy.json`, `.github/scripts/`, mixed architecture tests and `Hexalith.ChatBot.slnx` — remove obsolete gates and workflow assertions using the investigation inventory; preserve product assertions and recovery code.
- [x] ChatBot `package.json`, `package-lock.json` — remove tool-only release/commitlint dependencies. No `.husky/` or audit waiver was found.
- [ ] ChatBot solution/AppHost, `Live.IntegrationTests`, a dedicated recovery test project and `.github/actions/{after-unit-tests,nightly}/action.yml` — implement approved dependency/test routing, reuse shared build/environment and require live topology/browser prerequisites. Run the whole required-live project in CI with runner-enforced `failSkips`; preserve the ordinary integration project's unchanged optional manual observer producer and report it unexecuted when its prerequisites are absent, rejecting all other unexpected skips. Assign the recovery project to the enabled nightly hook through `tests.exclude`; ordinary integration stays in CI. Resolve the recorded DW-4 runner concern with the current SDK without changing its pin or dropping tests.
- [ ] ChatBot `tests/Hexalith.ChatBot.Release.Tests/`, the M2/origin-parity harnesses in `TrivialGovernedCommandAspireE2eTests.cs`, and the nightly composite — retain the positive canonical-commit/durable-state checks in a whole nightly project assigned through `tests.exclude`; preserve their full scenario/assertion bodies and run them every release, separately from Sunday recovery. A failed release step must remain failed while a due recovery still runs when runtime preparation succeeded and the run was not canceled. Keep ordinary refusal/topology/browser checks in CI, with no test filters or plain exclusions. See the ChatBot refinement in `gate-classification.md`.
- [ ] `setup/Hexalith.ChatBot.yml`, `references/Hexalith.ChatBot`, `rendered/Hexalith.ChatBot/`, `rendered/Hexalith.ChatBot.perimeter.json` — register the remotely available product revision with solution `Hexalith.ChatBot.slnx`, Dapr/browsers enabled and required direct dependencies. Await prerequisite Builds releases; commit registration and render together.
- [ ] `evidence/19/` — authenticate candidate validation, App delivery/perimeter/foreign-content preservation, immediate immutable-release/legacy-credential cleanup, green CI and next nightly.

**Acceptance Criteria:**
- Given adopted ChatBot, when shared CI runs, then product checks pass without CI/story/YAML gates or lost product coverage.
- Given migrated main, when pushed, then CI runs and publication waits for central nightly dispatch.
- Given adoption, when legacy cleanup completes, then only scoped publishing remains and the next nightly succeeds or reports nothing to release.

## Implementation Notes

- Parked, 2026-11-18: The human approved parking story 19 and opening a ChatBot product scope decision; the CiCd half of the timing prerequisite follows that decision. A local read-only inspection found four open blockers. (1) Builds v6.1.0 and later and the CiCd render carry `nightlyTimeoutMinutes`, but the central nightly still has one 300-minute wait in one 330-minute job, so the prerequisite is not shipped. (2) ChatBot `ddd385ec6b37a7bb6362cdc66cb3a1a0def935d3` still pins EventStore `77a2dafdf2e6aab7382afab7ab50e22144361d42` and targets `net10.0`. The owner-loader refusal is unchanged. EventStore v5.0.0 changed that loader but requires `net11.0`, and nobody has verified that it fixes ChatBot. (3) `ValidateAtomicParticipationAsync` still always refuses, so the retained positive M2/origin release cases cannot pass. (4) The AD-21 administration recorded on 2026-11-16 is still unprovisioned, and App selection needs an Organization Owner. No push, remote operation, registration or adoption occurred. See [blockers](../specs/spec-cicd/evidence/19/blockers-20261118.json).
- Authorized publication, 2026-11-16: The user explicitly instructed “override for this push”. Product commit `e2727327bf495764fd8c31edd46a81c8048cbbac` is now verified on ChatBot main using module-agent. This one-time exception covers the five known failed required checks and incomplete/unverified AD-21 push preconditions; test enforcement, future push requirements, the separate timing prerequisite and adoption/release acceptance remain unchanged. No registration, adoption or successful hosted acceptance is claimed. See `evidence/19/publication-exception.json` and `product-main-publication.json`.
- Renewed push request, 2026-11-16: The parent created local product commit `e2727327bf495764fd8c31edd46a81c8048cbbac`, exactly matching reviewed tree `5fe3abbc9327c0aaf102c1ac4e74ca136bedece0`, after fresh-main and pinned commitlint checks. The worktree is clean. Five required live/release checks still fail and AD-21 setup is incomplete/unverified. An explicit exception to those publication preconditions has been requested; no product push, root commit, registration or adoption has occurred in this follow-up. Preserve unrelated active work in the shared checkout.
- Final local follow-up, 2026-11-16: Package-mode solution compilation passes with zero warnings/errors. Ten complete unit suites pass 5,388 tests, AppHost passes 18, ordinary integration passes 548 and UI E2E passes 289: 6,243 unique passing tests, plus exactly the unchanged optional manual observer case unexecuted. All three required live cases and both whole-project release cases execute and fail during public compiled-owner preparation: the test host selects app-local `System.Text.Json/11.0.0`, while the normal `net10.0` owner uses framework 10 and has no package/output Json DLL. The pinned SDK's immutable-output loader refuses that host-local fallback. Final source differs from the runtime snapshot only in the existing Architecture test, corrected to check the helper's exact source/package split and required non-resource metadata; its own fresh build has zero warnings/errors and all 119 tests pass. The evidence preserves this sole-file lineage instead of relabeling earlier hashes. This actual loader refusal blocks product-push certification; no framework DLL substitution, runtime/pin change or weakened guard was made. Positive release scenarios cannot reach atomic acceptance while owner preparation fails; their independent unconditional production refusal is established from source. All verification children/resources have exited. See `evidence/19/product-fix-verification.md` and `parent-fix-audit.json`; no story 19 push, successful administration, registration or adoption occurred.
- Verification correction, 2026-11-16: The initial MSB3277 conclusion below is superseded. A canonical, acyclic snapshot of the exact pinned sources removes those conflicts; they were verification-layout defects, not evidence that the unchanged products were broken. The earlier unauthenticated-module verdict is also superseded: the existing module-agent credential is configured in its intended profile, repository reads and a main-push dry run pass, and no remote ref has changed. Current live-fixture/routing fixes still require fresh exact-source verification. See `evidence/19/fix-progress.json` and the final follow-up proofs when available.
- Active follow-up refinement, 2026-11-16: Legacy release workflow lines 89–101 select the positive committed-state M2 gate only for releases; the CI topology job selects only independent refusal/browser cases. Preserve that distinction with a dedicated Release.Tests project and a complete-project nightly invocation. The existing 330-minute recovery/preparation/cleanup allowance remains intact; add the legacy M2 30-minute allowance for a 360-minute total shared hook capacity, without changing the 45-minute default or recovery's 250/280/300-minute timers. This is a timing-prerequisite requirement, not permission to register against the current 45-minute Builds contract. The current unconditional atomic-participation refusal is preserved and truthfully blocks M2 release acceptance until an accepted owner implementation exists.
- Active live-fixture refinement, 2026-11-16: The pinned EventStore development-catalog contract supports explicit owner-private custody only together with a genuinely new, owner-isolated business backend. Repair live fixture composition using those public options and real compiled-owner observations, fresh owned backend identities and private key custody retained for the backend lifetime. Do not reuse default `dapr init` Redis as proof of freshness, copy model-only keys, manufacture observations or change authentication/admission guards. No new human credential is required for a genuinely disposable owner-created fixture.
- Active follow-up, 2026-11-16: The human requested fixing the publication blockers, continuing the authorized push to main. The existing module-agent credential has now been configured in its intended profile and successfully authenticated against ChatBot. In this implementation handoff, fix and verify the remaining composed-graph product failures from local product commit `bf0f44ff395d89c5565a423b424e389d2f80d0f6`, including complete package-mode solution/integration/recovery compilation. Preserve warning/audit/test enforcement, the SDK pin, exact dependency gitlinks and owned files; do not edit sibling products. Save reusable reproduction commands and useful logs under the story evidence directory, and distinguish genuine product fixes from verification-layout defects. The parent handles repository administration and publication; this implementation handoff performs product work and local verification only. Do not invoke bmad-build again inside the handoff.
- 2026-11-16: The human approved the spec and requested stopping before implementation, then publishing the planning changes to main. The separate nightly prerequisite remains required before adoption.
- 2026-11-16: Implementation resumed in the existing clean `story/19-migrate-chatbot` worktree at `../cicd-story-19`, preserving unrelated work in the main checkout. This bmad-build implementation phase permits local preparation only (no pushes or remote operations); external prerequisites and acceptance remain pending until independently verified. Prepare independent product changes without registering or adopting ChatBot before the separate nightly prerequisite is released.

- 2026-11-16: Local product preparation removed obsolete story/CI gates and npm release tooling, retained product assertions and AppHost composition sources, split the weekly recovery entry point into `Hexalith.ChatBot.Recovery.Tests`, added dormant live-prerequisite/nightly actions and selected Microsoft.Testing.Platform while preserving SDK 11.0.100. The unchanged baseline reproduces the composed Parties/Memories MSB3277 conflicts. Nine full unit suites passed; the Client lane exposed a baseline stale hash fixture, corrected with byte-identical NSwag generation and a passing focused assertion. Final cold tool-path/Platform reference checks pass for four package-cache cases; full graph execution remains unverified after that correction. See [local preparation](../specs/spec-cicd/evidence/19/local-preparation.md) and its logs. No pushes, remote operations, nested initialization, registration or adoption occurred; external prerequisites and all hosted acceptance remain pending.
- 2026-11-16: Parent inspection independently verified the final implementation hashes, seven protected files, all 16 gitlinks, the unchanged recovery scenario body, the solution boundary and frozen intent. Only the two fully completed removal tasks above are checked. Product verification used ChatBot's existing Builds gitlink, not the future adoption release; compatibility with that release remains unverified. Step 3 acceptance is incomplete, so formal review and completion were not entered. See [parent audit](../specs/spec-cicd/evidence/19/parent-local-audit.json).
- 2026-11-16: The human subsequently authorized pushing all story 19 changes to main. After freshly fetching ChatBot main, created local product commit `bf0f44ff395d89c5565a423b424e389d2f80d0f6` on `story/19-chatbot-product-preparation`; its patch exactly matches the inspected preparation and its message passed locked, signature-verified commitlint. Publishing is blocked: the required module-agent profile is unauthenticated, successful maintainer reads confirm missing AD-21 rulesets/release environment/publish switch, and the approved pre-adoption verification is not fully green. No product push or CiCd commit was attempted, and the unpublished gitlink was not staged. See [push preflight](../specs/spec-cicd/evidence/19/push-preflight.json). The earlier implementation phase's local-only restriction is superseded by this explicit authorization; the repository gates remain required.

## Spec Change Log

- 2026-11-27 — Aligned the non-frozen `## Verification` bullet (line 101) with CAP-13, CAP-16 and AD-21 step 4 (accepting either a scheduled `nightly.yml` run or an authorized `workflow_dispatch` with `qualify-bump` false), per [readiness-concerns sprint change proposal](../planning-artifacts/sprint-change-proposal-2026-11-27-readiness-concerns.md). Frozen intent unchanged.

## Review Triage Log

## Design Notes

External effects include product pushes, delivery, settings, credential revocation and public publication. This story changes ChatBot solution/tests/actions and CiCd registration/render/evidence. Shared timing support ships separately. Local product preparation and verification are recorded in [local preparation](../specs/spec-cicd/evidence/19/local-preparation.md); no successful remote state change, registration or adoption has run.

## Verification

- Use `run-with-temp` for disposable jobs; preserve logs under `evidence/19/`.
- Before product pushes run the approved procedure and pinned commitlint; after adoption run `python3 references/Hexalith.Builds/check.py` from a suitable standalone module checkout.
- Run `uv run --locked --script tools/render.py --check`, then committed-candidate `tools/validate.py` with the intended read credential. Require global and ChatBot verdicts, including lint/schema/perimeter/live-action checks.
- Authenticate hosted CI, actual recovery execution and ChatBot's own CAP-13/CAP-16 nightly outcome from a central `nightly.yml` run started after adoption on `main` (scheduled or authorized `workflow_dispatch` with `qualify-bump` false).
