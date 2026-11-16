---
title: '19: Migrate ChatBot'
type: 'chore'
created: '2026-11-16'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context: []
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
- ChatBot `tests/Hexalith.ChatBot.Architecture.Tests/{ReleaseWorkflowSafetyTests,LiveRecoveryValidationArchitectureTests,ScaffoldArchitectureTests}.cs`: obsolete workflow assertions mixed with product assertions.
- ChatBot `tests/Hexalith.ChatBot.IntegrationTests/Recovery/LiveContinuityAspireE2eTests.cs` and Server `Audit/`: genuine recovery behavior; preserve it.
- CiCd `setup/README.md`, `tools/{render,validate}.py`, `templates/`, `rendered/`: existing generation, validation and delivery interfaces.

## Tasks & Acceptance

**Execution:**
- [ ] `prerequisite-19-long-running-nightly-hooks.md` — require its verified shared release before registering ChatBot. The prerequisite is a separate deliverable; story 19 does not implement shared timing support.
- [ ] `evidence/19/` — verify/provision AD-21 App selection, exact rulesets, stale release/CodeQL cleanup, release environment with module-only Zot identity, scoped NuGet policy, publish switch and shared org access. Record sanitized before/after metadata. Rulesets/environment/switch/access are missing; App selection/NuGet policy are unverified; retention/push protection pass.
- [ ] ChatBot `tools/Hexalith.ChatBot.StoryEvidenceGate/`, `tests/Hexalith.ChatBot.StoryEvidenceGate.Tests/`, `story-evidence-policy.json`, `.github/scripts/`, mixed architecture tests and `Hexalith.ChatBot.slnx` — remove obsolete gates and workflow assertions using the investigation inventory; preserve product assertions and recovery code.
- [ ] ChatBot `package.json`, `package-lock.json` — remove tool-only release/commitlint dependencies. No `.husky/` or audit waiver was found.
- [ ] ChatBot solution/AppHost, a dedicated recovery test project and `.github/actions/{after-unit-tests,nightly}/action.yml` — implement approved dependency/test routing, reuse shared build/environment and require live topology/browser prerequisites. Assign the recovery project to the enabled nightly hook through `tests.exclude`; ordinary integration stays in CI. Resolve the recorded DW-4 runner concern with the current SDK without changing its pin or dropping tests.
- [ ] `setup/Hexalith.ChatBot.yml`, `references/Hexalith.ChatBot`, `rendered/Hexalith.ChatBot/`, `rendered/Hexalith.ChatBot.perimeter.json` — register the remotely available product revision with solution `Hexalith.ChatBot.slnx`, Dapr/browsers enabled and required direct dependencies. Await prerequisite Builds releases; commit registration and render together.
- [ ] `evidence/19/` — authenticate candidate validation, App delivery/perimeter/foreign-content preservation, immediate immutable-release/legacy-credential cleanup, green CI and next nightly.

**Acceptance Criteria:**
- Given adopted ChatBot, when shared CI runs, then product checks pass without CI/story/YAML gates or lost product coverage.
- Given migrated main, when pushed, then CI runs and publication waits for central nightly dispatch.
- Given adoption, when legacy cleanup completes, then only scoped publishing remains and the next nightly succeeds or reports nothing to release.

## Implementation Notes

- 2026-11-16: The human approved the spec and requested stopping before implementation, then publishing the planning changes to main. The separate nightly prerequisite remains required before adoption.

## Spec Change Log

## Review Triage Log

## Design Notes

External effects include product pushes, delivery, settings, credential revocation and public publication. This story changes ChatBot solution/tests/actions and CiCd registration/render/evidence. Shared timing support ships separately. No implementation or remote mutation has run.

## Verification

- Use `run-with-temp` for disposable jobs; preserve logs under `evidence/19/`.
- Before product pushes run the approved procedure and pinned commitlint; after adoption run `python3 references/Hexalith.Builds/check.py` from a suitable standalone module checkout.
- Run `uv run --locked --script tools/render.py --check`, then committed-candidate `tools/validate.py` with the intended read credential. Require global and ChatBot verdicts, including lint/schema/perimeter/live-action checks.
- Authenticate hosted CI, actual recovery execution and the next scheduled release outcome.
