---
title: '23: Migrate Tenants'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '771cfd0f01416d9adb2bdb3ff8cf8d1437d385e1'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Tenants still runs bespoke pipelines, story guards and workflow assertions alongside substantial product qualification.

**Approach:** Follow AD-21: prepare the product, register/render in CiCd, and let App delivery adopt Tenants. Preserve product coverage; require green adopted CI and the next central nightly outcome.

## Boundaries & Constraints

**Always:** Preserve SDK 11.0.100, product assertions, coverage thresholds, scheduled performance checks and foreign content. Use module-agent for Tenants product writes, CiCd-agent for CiCd/Builds and command-local maintainer for administration. Meet AD-21 before product preparation. Share one Release package-mode solution build and environment; retain necessary project-specific product variants.

**Never:** Edit owned Tenants content directly, initialize nested submodules, weaken security/tests, copy generic setup into module hooks, fabricate delivered state, or revoke legacy publication before adoption. Require the standard local checker for module pushes unless the human explicitly approves a limited bootstrap exception.

**Human decisions, 2026-11-16:**

- Before adoption only, approve Tenants-specific verification for every exact product revision: released package-mode build/unit routines, applicable product checks, audit/action policy, pinned commitlint and preservation of owned bytes/modes/gitlinks. This does not certify an absent delivered baseline. The exception ends immediately at adoption; subsequent product pushes require the standard checker.
- Retain the named, gitlink-pinned upstream executables, Platform identity helpers, nonpackable Builds.Tooling and indispensable composition dependencies documented in the investigation. Ordinary Tenants library dependencies use published packages. Keep package-consumer checks and preserve live product assertions. Package/container topology redesign is separate work.

## I/O & Edge-Case Matrix

| State | Behavior |
| --- | --- |
| Preconditions or released prerequisites unavailable | Block adoption; distinguish absence from access refusal |
| Backend receipt retained, malformed or mismatched | Refuse private material provisioning |
| Product failure | Fix product while preserving assertions |
| No releasable change | Accept authenticated scheduled “nothing to release” |

</frozen-after-approval>

## Code Map

- `_bmad-output/specs/spec-cicd/evidence/23/investigation.md`: required gate, dependency and shared-capability inventory; `preflight.json` and `maintainer-preflight.json`: current settings and exact access limits.
- Tenants `Hexalith.Tenants.slnx`, AppHost project, `Directory.Build.props`, `tests/`, `scripts/`: product graph, mixed assertions, live bootstrap and tooling.
- Builds `Github/lib/{ci_environment,ci_config,guard_actions}.py`, schema and corresponding tests: shared environment, strict configuration and hook constraints.
- CiCd `setup/README.md`, `templates/.github/workflows/ci.yml.j2`, `tools/{render,validate,check_global}.py`: generation and adoption interfaces.

## Tasks & Acceptance

**Execution:**
- [ ] `evidence/23/` — complete ordered AD-21 provisioning: App selection, release cleanup, exact rulesets, main-only release environment, scoped Zot/NuGet policy, publish switch and org grants. Preserve existing policies until adoption and record sanitized readbacks.
- [x] Builds `Github/lib/ci_environment.py`, `Github/ci-environment/action.yml`, schema/loader and corresponding tests — implement and locally qualify generic pre-Dapr initialization receipts and bounded `ciTimeoutMinutes`, default 30.
- [ ] Builds shared prerequisite release and CiCd `builds-version` — publish and adopt the compatible shared contract before Tenants registration.
- [ ] Tenants solution/AppHost and test projects — implement the selected source boundary, explicit integration/hook ownership and package-backed catalog coverage; retain every current product scenario without duplicate full-solution builds.
- [ ] Tenants mixed tests and Python tooling — remove CI/story/agent/YAML assertions per investigation, preserving package/consumer/coverage and UI assertions. Remove tool-only root package manifest/lock/Husky and audit demotions; fix audited product dependencies or centralize permitted exceptions in Builds before adoption.
- [ ] Tenants `.github/actions/{after-unit-tests,after-integration-tests,nightly}/action.yml`, bootstrap script/tests — preserve browser focus, authenticated routes, profiles, Dapr retry, catalog consumers, coverage thresholds and scheduled performance. Consume shared freshness receipts; preserve refusal cases and private cleanup.
- [x] CiCd timeout template/render tests and contract documentation — expose the existing timeout input while preserving old-tag behavior, and qualify default/custom/invalid allowances and callable input typing.
- [ ] `setup/Hexalith.Tenants.yml`, module gitlink and `rendered/Hexalith.Tenants*` — register verified direct dependencies/environment/test routing and commit render with its cause after product actions reach main and required shared releases are pinned.
- [ ] `evidence/23/` — authenticate full candidate validation, App adoption, perimeter/foreign preservation, immediate immutable-release and legacy-access cleanup, green CI and next nightly.

**Acceptance Criteria:**
- Given adopted Tenants, when shared CI runs, then preserved product tests and thresholds pass without CI/story/YAML gates or omitted live classes.
- Given adoption, when publication is evaluated, then scoped credentials remain, pushes run CI and the next scheduled central release succeeds or reports nothing to release.

## Implementation Notes

- 2026-11-16: The human approved both recommended decisions after the detailed tradeoff discussion. The isolated CiCd branch was fast-forwarded to current origin/main before capturing the implementation baseline. Existing user work in the original CiCd and Builds checkouts remains untouched. Shared local prerequisites can proceed while AD-21 completion gates Tenants product preparation and adoption. No external provisioning, product push or delivery is claimed by this approval record.
- The current Build implementation stage permits local work only: no pushes or other remote operations. Implement the shared local prerequisites in isolated owning-repository worktrees, verify them, and report live-gated tasks as incomplete. AD-21 is not yet satisfied, so Tenants product preparation and registration remain gated. Do not use that gate as a reason to leave independent shared local implementation unfinished.
- 2026-11-16 local implementation: shared Dapr initialization receipts and required bounded `ciTimeoutMinutes` are implemented in the isolated Builds worktree `/home/administrator/projects/hexalith/builds-story-23`; CiCd's tagged-contract timeout forwarding is implemented here. Defaults remain 30; Builds' own complete document retains its existing 60-minute allowance. The tracked sample expected document was updated with its actual configuration, and the intact whole-file guard was qualified against those checked-in artifacts. Source baselines, final file hashes, verification outcomes and remaining gates are recorded in [`implementation-local.md`](../specs/spec-cicd/evidence/23/implementation-local.md) and `evidence/23/shared-local-changes.json`.
- 2026-11-16 qualification: Python 3.12 and 3.14 each passed 34 locked renderer tests plus render `--check`, 18 final config tests, 31 final environment tests and 17 final expected-state tests. The retained 148-case combined runs each passed all 117 non-environment consumer cases and failed the earlier Docker-inspection exit-code assertion; the full final environment reruns passed after correcting that diagnostic. Both owning-worktree `git diff --check` commands passed. No publication, product push, registration, provisioning, delivery, adoption or scheduled-nightly outcome is claimed; all live gates and Tenants product work remain incomplete, and the story remains in progress.
- Parent inspection checked the shared code and tests, confirmed all 179 existing contract fixtures preserve their prior values except the added timeout default, and documented the future released contract in AD-3 and pipeline stages. Local source changes are staged in their isolated owning worktrees. The full-story acceptance and matrix audit remain incomplete because Tenants provisioning, product migration and real delivery have not run; the workflow has not advanced to final story review.
- The human subsequently explicitly requested pushing all current changes to main. That authorizes publishing this work to the two owning repositories despite the earlier local-only implementation phase. Migration, release and adoption completion still require their recorded gates; this publication does not claim them.

## Spec Change Log

## Review Triage Log

## Design Notes

Footprint spans Tenants tests/actions/graph, shared Builds contracts and CiCd registration/rendering. External effects include settings, product pushes, delivery, credential revocation and public publication. Both human choices are approved; actual preconditions and acceptance evidence remain required.

## Verification

- Use `run-with-temp` for disposable jobs; retain logs in `evidence/23/`.
- Qualify shared receipt/config behavior, valid/invalid fixtures and callable contracts on supported Python versions. Preserve receipt refusal and product coverage tests.
- Before module pushes use the standard checker or the explicitly approved bootstrap procedure, with pinned commitlint and exact owned-state comparisons.
- Run locked renderer `--check`, then committed-candidate `tools/validate.py`; require global and Tenants verdicts, including schema/lint/perimeter/live-action checks.
- Authenticate hosted CI, actual product-hook execution, adoption cleanup and the next scheduled release outcome.
