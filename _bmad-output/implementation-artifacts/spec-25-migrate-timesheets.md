---
title: '25: Migrate Timesheets'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'eba7514e02904c741f6a0a80930d85eb358d385c'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Timesheets uses legacy pipelines with unavailable dependency revisions, failing package compilation and gates checking release tooling and story evidence. Its product checks must survive adoption.

**Approach:** Follow AD-21: establish maintainer preconditions, prepare product changes, register/render here, and adopt through App delivery. Completion requires green adopted CI and the next successful central nightly outcome.

## Boundaries & Constraints

**Always:** Preserve SDK 11.0.100, net10 product compatibility, all six test suites, six package/consumer contracts, AppHost configuration and fixture/privacy checks. Keep existing live-Dapr/performance opt-ins without claiming runtime acceptance from default skips. Use CiCd-agent for CiCd/Builds, module-agent for product writes, command-local maintainer for administration. Preserve foreign instructions/settings.

**Approved decision (2026-11-16):** Before Timesheets adoption only, require the exact preparation commit's Release/package-mode build, all six suites and retained product/consumer checks, pinned commitlint, and proof that owned bytes/modes/gitlinks/partial content are unchanged from freshly fetched main. Record results before every preparation push. Require normal successful `python3 references/Hexalith.Builds/check.py` after actual App adoption. This exception applies only to Timesheets; all other ownership, credential and validation requirements remain. See `evidence/25/pre-adoption-decision.md`.

**Never:** Edit owned module portions manually; weaken audits/tests/scanner coverage; add skips or broad credential access; duplicate generic build/feed/process plumbing in module actions. Registration waits for compatible published Builds support and complete action discovery.

## I/O & Edge-Case Matrix

| State | Required behavior | Failure handling |
|---|---|---|
| Product compilation/check failure | Fail before adoption/publication | Fix product; retain gate |
| Unresolved action call graph | Block registration | Refactor or complete shared prerequisite |
| Missing onboarding access/configuration | Leave adoption incomplete | Record exact failure; preserve existing settings |
| Successful adoption | Preserve foreign content; retire legacy publishing access immediately | Authenticate cleanup and next nightly |

</frozen-after-approval>

## Code Map

- `_bmad-output/specs/spec-cicd/evidence/25/{investigation.md,preflight.json,pre-adoption-check.json,discovery-probe.json,hosted-diagnostics.json}` — revisions, administrative state, exact policy blocker, gate inventory and failed hook probes.
- `prerequisite-25-product-validation.md` — required shared package-consumer/discovery and catalog support; implementation/release precedes registration.
- Timesheets `Hexalith.Timesheets.slnx`, `Directory.{Build,Packages}.props`, `tools/release-packages.json`, `scripts/`, architecture fitness tests — package graph, product contracts and removable gates.
- CiCd `setup/README.md`, `tools/{render,validate,scan_discovery}.py`, `templates/`; Builds `Github/lib/{ci_pipeline,local_check}.py` — reuse existing generation/delivery/runtime interfaces.

## Tasks & Acceptance

**Execution:**
- [ ] `evidence/25/` — refresh canonical refs and AD-21 checks; provision App selection, exact rulesets, module-specific release environment/Zot identity, scoped NuGet policy and org access in order. Preserve current publish switch; recheck existing security/retention settings.
- [ ] `prerequisite-25-product-validation.md`, `builds-version` — require verified shared support and a published compatible catalog before registration; do not substitute local unreleased Builds files.
- [x] Timesheets `scripts/tests/`, architecture `FitnessTests/`, `package.json`, `package-lock.json` — remove the classified agent/CI/story/YAML gates and tool-only manifests, retaining mixed-file product assertions and package validators. Delivery handles owned configuration removals.
- [ ] Timesheets `scripts/`, `.github/actions/after-unit-tests/action.yml` — integrate the qualified shared runner, reuse the existing Release build and its actual version, and retain all six archive/symbol/dependency/isolated-consumer contracts plus compiled AppHost, selected-index and fixture/privacy checks. Prove full discovery and fail-fast behavior.
- [ ] `setup/Hexalith.Timesheets.yml`, `references/Hexalith.Timesheets`, `rendered/Hexalith.Timesheets/`, `rendered/Hexalith.Timesheets.perimeter.json` — register remotely available product revision, solution `Hexalith.Timesheets.slnx`, hook `after-unit-tests`, direct EventStore/Works dependencies, false Dapr/browser/registry flags and default test routing. Commit registration/render/gitlink together, then validate that candidate before delivery.
- [ ] `evidence/25/` — authenticate delivery, preserved foreign content, immediate immutable-release/legacy-credential cleanup, green CI and next nightly; leave incomplete acceptance open.

**Acceptance Criteria:**
- Given migrated Timesheets, when shared CI runs, then five suites run in stage 3, IntegrationTests in stage 4, and all retained product checks pass without CI/story/YAML gates.
- Given missing shared support or incomplete discovery, when registration is evaluated, then adoption remains blocked without bypasses.
- Given adoption, when cleanup and the next nightly finish, then only scoped publishing remains and the release succeeds or reports nothing to release.

## Implementation Notes

- 2026-11-16: The human approved the full migration spec and requested stopping before implementation, then pushing the planning changes. The Timesheets-only pre-adoption verification decision remains in force. Shared-support, compatibility, onboarding and adoption tasks remain unexecuted.
- 2026-11-16: Local product cleanup is implemented; retained tests pass (30 package, 30 selected-index, 95 architecture). Added the isolated shared-runner prerequisite and six module-owned consumer inputs; its 25 behavioral tests pass. Full package build is blocked by recorded net10/net11 catalog incompatibilities. Real SDK packing reuses existing outputs; strict NuGet policy correctly refuses unsigned candidates (NU3004), leaving a signed-candidate path unqualified. No remote operations, production hook, registry/render/gitlink update or adoption was performed. Evidence: `../specs/spec-cicd/evidence/25/local-preparation.md`.
- 2026-11-16: Final local qualification passes all six retained .NET suites (Architecture 95, Contracts 108, Projections 792, Server 746, Works 76, Integration 1,057 plus five existing skips), AppHost configuration/construction, 270 fixture/privacy, 27 runner and six catalog metadata cases. Fixed repeated streamed-bootstrap metadata reads with reservation revalidation and transient `/proc` cleanup races; no deadlines/assertions/skips were weakened. Fresh build at `b325a0b47d642f1711f49e589509ca89ac585bca` packs six validated package/symbol pairs at `2.1.1-preview.0.3`, then correctly stops on unsigned-consumer NU3004. External commits were preserved and were not performed by this agent. Signing/discovery/publication, exact pre-push verification, registration and all adoption acceptance remain open. Final identities and receipts: `../specs/spec-cicd/evidence/25/verification-summary.json`.

- 2026-11-16: The human requested fixing the push-blocking verification failures.
  Applied the finite net10 catalog correction in central Builds, preserving SDK
  11.0.100 and the module's net10 contract. Added evaluated catalog regressions
  for selected, unrelated and future project identities; six tests and six
  source/package/override metadata cases pass. Replaced the 80 ms wall-clock
  polling test with controlled time while retaining poll-count, deadline,
  single-submit and no-readback assertions. The existing public constructor
  still uses System time; the explicit clock is internal to the test seam.
  All 42 polling tests and all 746 Server tests pass without skips; see
  `../specs/spec-cicd/evidence/25/polling-deadline-fix.json`. Candidate-package
  signing trust remains a separate pending human decision in
  `prerequisite-25-candidate-signing.md`; no signature/audit bypass was applied.

## Spec Change Log

## Review Triage Log

## Design Notes

External effects include preparation pushes, App delivery, settings changes, credential revocation and publication. Investigation made no remote changes. The original stale-checkout assumption is obsolete: fetched main already equals the CiCd gitlink. No waiver was found; no waiver release is needed unless subsequent investigation finds one.

## Verification

- Use `run-with-temp` for disposable jobs and keep useful results under `evidence/25/`.
- Run all six package-mode test projects and retained package/AppHost/Python checks on exact committed inputs; follow the resolved pre-push policy and require normal `check.py` after adoption.
- Run `uv run --locked --script tools/render.py --check`, then authenticated `uv run --locked --script tools/validate.py` on the committed candidate. Require global and Timesheets verdicts, complete discovery and a real cross-module duplicate scan.
- Verify hosted adopted CI and the next central nightly outcome; configuration-only AppHost checks grant no live/deployed runtime acceptance.
