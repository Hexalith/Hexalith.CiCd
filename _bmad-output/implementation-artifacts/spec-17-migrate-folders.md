---
title: '17 — Migrate Folders'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
baseline_commit: '7d32df03405c876df6f098aec4036207bf35af1d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/17/planning.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Folders still uses legacy pipelines and duplicates product checks among CI, drift and policy lanes.

**Approach:** Preserve product coverage as centrally enabled hooks, remove CI/tooling/story-evidence assertions, then adopt through AD-21 delivery and verify the next nightly outcome.

## Boundaries & Constraints

**Always:** Preserve concurrent work in the approved isolated branch. Respect migration order and predecessor checkpoints before adoption. Use module-agent for product writes, CiCd-agent for CiCd/Builds, command-local maintainer for administration. Preserve SDK11 and published targets, product checks and foreign content. Keep waivers only in released Builds Props. Use `run-with-temp`; record full revisions and actual failures.

**Never:** Edit owned module portions, initialize nested submodules, obtain the App key, weaken audits/tests, inherit the pilots' exception, invent live-provider evidence, duplicate test execution, revoke legacy access before adoption, or count a `qualify-bump` run or another module's row as its nightly outcome.

**Human decision, 2026-11-16:** Approved a Folders-only pre-adoption checker substitute: released policy/commit checks, exact owned-tree preservation, package-mode Release build and every retained test/product hook with saved revisions/results. This applies only to exact product-preparation commits before real adoption. The normal checker resumes after adoption; no owned-file edits, nested initialization, credential broadening or audit/test bypasses are authorized.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing prerequisite, denied API or main race | Stop the dependent write; preserve exact evidence and revalidate. |
| Mixed product/workflow test | Remove forbidden assertions; preserve product behavior checks. |
| Project assigned to a hook | Execute its complete retained suite once; shared discovery delegates it. |
| Missing runtime, failed product test or unavailable audit | Fail explicitly; never add a skip or waiver in the module. |
| No releasable change | Record genuine nothing-to-release; do not force a version. |

</frozen-after-approval>

## Code Map

- `evidence/17/planning.md` under the main spec folder: revisions, AD-21 GET/UI readbacks, exact mixed-test map and preparation proposal.
- Folders `Hexalith.Folders.CI.slnx`, `global.json`, `Directory.Build.props`, `src/Hexalith.Folders.Client/` — package build, SDK11, audit waiver and net10 generator/tool-runtime seam.
- Folders `tests/Hexalith.Folders.Contracts.Tests/{Deployment,OpenApi}/`, `scripts/tests/`, `tests/tools/` — classify each assertion; retain contract, generated-client, browser, Dapr-security and provider behavior.
- Builds `Github/lib/{ci_pipeline,ci_environment,local_check,guard_actions,audit_lint}.py` — released shared classification/environment/checking; no module setup action may replace these.
- CiCd `tools/{render,validate,check_global,scan}.py`, `setup/README.md` — existing render, committed-candidate and live-action validation; preserve other registrations.

## Tasks & Acceptance

**Execution:**

- [ ] `evidence/17/` — verify predecessors; provision AD-21 in order: App selection, assessed stale CodeQL/legacy remnants, exact rulesets, main-only release environment, isolated Zot push pair, additive `Hexalith.Folders*` NuGet policy, disabled default scans, exact switch, retention and org grants. Capture baseline and preserve legacy access.
- [x] Folders `tests/Hexalith.Folders.Contracts.Tests/{Deployment,OpenApi}/`, `scripts/tests/`, `tests/tools/` — apply the recorded per-method gate map; remove workflow/tooling/story assertions and redundant scheduled wrappers, retain all product and deployment-security tests. Update gate classification evidence; 27 is an old estimate, not a deletion quota.
- [x] Folders `package.json`, `package-lock.json`, `Directory.Build.props` — retire tool-only npm files and module audit waiver; remove `.husky/` only if present. Record actual central-waiver needs; any required Builds `Props/` change must ship before adoption.
- [x] Folders `src/Hexalith.Folders.Client/{Hexalith.Folders.Client.csproj,Generation/}`, `tests/tools/run-forgejo-smart-http-alpine-smoke.ps1` — align nonpublished generator/runtime execution with SDK11, scope NSwag runtime roll-forward, propagate shared build/audit settings and fix Alpine runtime mismatch. Preserve generated-byte and real provider assertions.
- [ ] Folders `.github/actions/{after-unit-tests,after-integration-tests,nightly}/action.yml`, `tests/tools/` — create composite hooks reusing shared outputs/environment. Run complete Contracts/Client projects once in the first hook; complete UI.E2E including accessibility once in the second; distinct provider smoke/classification/redaction checks nightly. Verify nonvacuous execution and failure propagation.
- [ ] `setup/Hexalith.Folders.yml`, `rendered/`, `references/Hexalith.Folders` — after approved preparation proof and protected-token publication, register CI solution, Dapr/browsers, three hooks and four required direct submodules. Delegate complete hook-owned projects with `tests.exclude`; preserve automatic AppHost/integration classification. Commit prepared remote gitlink, setup and render together; validate before central publication.
- [ ] `evidence/17/` — authenticate delivered ref, report, sole adoption parent and full tree preservation; immediately enable immutable releases and retire only this module's legacy NuGet/secret/key/Zot access. Record normal checker, green CI and next scheduled release outcome before story-17 acceptance.

**Acceptance Criteria:**

- Given verified prerequisites and predecessor checkpoints, when delivery adopts Folders, then one authenticated commit establishes its perimeter and preserves product/foreign content.
- Given a retained suite failure, when its shared stage or hook executes, then CI fails without lost coverage, duplicate runs or an allow-not-runnable exemption.
- Given generated artifacts and provider checks, when the SDK11 package build and nightly hook execute, then artifact identity and actual provider behavior pass with compatible runtimes.
- Given adopted green main, when a nightly run (CAP-13) after adoption completes, then successful publication or nothing-to-release and immediate credential retirement establish CAP-16 completion.

## Implementation Notes

- The 2026-11-18 resume used CiCd `dc931eafa9f50c68f847650ea0d7aa60c8bfce0e`
  and two locally available Folders snapshots. An explicit, versionless
  `Aspire.Hosting.AppHost` reference fixes `NU1009`. Audited Release restore
  and build plus the complete Contracts, Client, UI.E2E and prepared Server
  suites passed against the umbrella dependency pins. The later cached main
  restore fails with `NU1506` because Tenants and Builds both declare
  `Aspire.Hosting.Dotnet`. The exact AppHost edit is available in the detached
  worktree `/home/administrator/projects/hexalith/folders-story-17-candidate`
  based on `a53fcb940fa1114fe3ead0af2775af388e39432c`. Publication requires a
  fresh fetch and [exact-input qualification](../../docs/pre-adoption-publication.md).
- The [2026-11-18 qualification](../specs/spec-cicd/evidence/17/local-resume-20261118.md)
  supersedes earlier results where it retested the same gate. Released audit,
  action and candidate commit checks passed, and local script discovery still
  failed. The complete core run rejected two provider skips and AppHost timed
  out. The Server hook needs shared preparation of its Keycloak fixture, and
  the selected delivery release still needs a compatible Aspire catalog.
  Predecessor checkpoints, publication, AD-21 adoption and the nightly outcome
  remain open.

- Resume, 2026-11-16: implementation checkout is `/home/administrator/projects/hexalith/cicd-story-17-resume`, branch `story/17-migrate-folders-resume`, created from freshly fetched CiCd main `b836159cea272e5211333296936106cf82833a27`. Resolve `{project-root}` context paths to this checkout. Preserve the original baseline and frozen intent. The prior published Folders candidate and source evidence are available in the clean sibling checkout `/home/administrator/projects/hexalith/cicd-story-17`; use its Git objects read-only to populate local direct checkouts if needed. Continue local implementation and verification sequentially; no pushes, remote Git operations, provisioning, adoption, or credential changes in step 03. Preserve both earlier workspaces.

- Implementation follows the rendered step-03 local-only boundary: no pushes, remote Git operations or external provisioning in this handoff. Prepare the concrete local candidate and verification; leave live rollout tasks unchecked until that boundary is explicitly resolved. This does not narrow final story acceptance. Read source dependencies from existing local Git objects rather than changing the original workspace.

- Resume qualification, 2026-11-16: [current evidence](../specs/spec-cicd/evidence/17/resume.md)
  revalidates the exact published local candidate against CiCd
  `b836159cea272e5211333296936106cf82833a27`. Production and candidate render,
  local validator boundaries, classification and all nine strict-runner
  boundaries pass. The eight unchanged historical audit declarations and
  940 unchanged discovery diagnostics still fail. Reconstructed prior source
  proves that the retained failing tests and sprint controls are unchanged;
  the evidence distinguishes required real component/owner/provider setup
  from the frozen FR58 product prerequisites. No additional product edit,
  production registration, remote operation or acceptance completion is claimed.

- Publication authorization, 2026-11-16: after the local qualification handoff, the human requested `push all changes to main`. Publish this resume's spec update and verification evidence on current CiCd main, preserving the recorded failed gates and incomplete acceptance. The earlier local-only statements describe implementation; this subsequent request authorizes publication of the handoff.

- Current local readiness, 2026-11-16: [limited requalification](../specs/spec-cicd/evidence/17/local-readiness-20261116/README.md)
  pins committed CiCd `0f25d19ba712eee9aae59d118251b854bbffd120` and the
  unchanged committed Folders candidate. Changed rendering and discovery sources were checked:
  production/candidate render and local validator boundaries pass, all five
  proposal output hashes remain identical, and discovery retains the exact
  940 diagnostics. Unchanged product, audit, classification and strict-runner
  outcomes were preserved by source identity without duplicate execution.
  No additional safe product edit was established. Frozen prerequisites,
  shared policy failures and live acceptance remain incomplete; production
  registration, owned module content and gitlinks were not changed.

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines, including frozen ones; no other constraint changed. The manual-dispatch prohibition became a ban on counting `qualify-bump` runs or another module's row.

## Review Triage Log

## Verification

- `run-with-temp uv run --locked --script tools/render.py --check` — reproducible cause/render.
- `run-with-temp uv run --locked --script tools/validate.py` — full committed/global/live-action verdict, using intended read-only authentication privately.
- `run-with-temp python3 references/Hexalith.Builds/check.py` — successful post-adoption standalone-module check.
- Execute complete delegated projects, built browser checks, provider smoke and deterministic generation under disposable product workspaces; retain exact inputs, outputs and nonzero failures. Inspect authenticated settings/delivery trees and the real scheduled-night outcome.

## Local handoff status, 2026-11-16

The local product candidate and proposed six-project hook ownership are recorded
in `evidence/17/implementation.md` and `evidence/17/final-candidate.json`. The
registration/render are review artifacts under `evidence/17/registration-candidate/`;
production setup, rendered delivery, and the superproject gitlink are unchanged.
No remote Git, provisioning, adoption, credential retirement, or manual release
dispatch was performed.

The full audited Release build, fresh .NET11-only generators, product source
quality checks, complete Contracts suite, browser suite, capacity operations, and
real Forgejo smoke have saved source-bound outcomes. The final Client fixture
alignment is checked separately. Retained explicit security controls and the
frozen FR58 proof fail on genuine prerequisites; incomplete suites remain red
under the strict runner. Eight unchanged historical `auditSources` declarations
and the current PowerShell discovery limitation block policy proof.

All acceptance criteria remain in progress. Passing local component checks does
not establish protected publication, authenticated adoption, green delivered CI,
or the next genuine scheduled release outcome.

## Publication instruction, 2026-11-16

The human requested `push all changes` after the blocked handoff. The existing
work is published on `story/17-migrate-folders` branches, preserving the failed
verification status and all adoption prerequisites. The Folders branch is
verified at `d27487f405cb52dabdc6ce8dc16af543b2ddd625`; its tree is the exact
previously qualified local candidate. This CiCd commit records that remotely
available gitlink and the handoff. It adds no production setup or rendered
Folders registration and does not establish story acceptance. See
[publication details](../specs/spec-cicd/evidence/17/publication.md).
