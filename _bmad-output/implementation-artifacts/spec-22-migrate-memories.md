---
title: '22: Migrate Memories'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'c74b5c8f5787fb33bfd85c1c4430b6de39674198'
context:
  - '/home/administrator/projects/hexalith/cicd-story-22/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Memories has legacy pipelines and CI/story gates alongside genuine source, browser, rollout and telemetry checks. Adopting the shared pipelines must preserve product coverage.

**Approach:** Follow AD-21: establish prerequisites, prepare product changes with module-agent, register/render in CiCd, and let App delivery adopt Memories. Finish only after green adopted CI and the next scheduled nightly succeeds or reports nothing to release.

## Boundaries & Constraints

**Always:** Preserve SDK 11.0.100, product assertions, output coverage and foreign content. Use CiCd-agent for CiCd/Builds and command-local maintainer access for administration. Require approved verification before preparation pushes and the standard checker after adoption. Declare exact direct dependencies; preserve package mode for ordinary libraries.

**Never:** Edit module-owned perimeter content directly, weaken audits/tests, add plain skips or skip trailers, broaden credentials, revoke legacy access before adoption, or use hooks for generic setup/rebuilds. Shared capability changes ship separately; adoption waits for acceptable released support.

**Human decisions, 2026-11-16:**

- Approve the Memories-only pre-adoption verification exception: exact committed inputs in a disposable standalone checkout; Release/package compilation, complete applicable product tests, package/consumer checks, pinned commit validation and byte/mode/gitlink proof of unchanged owned content. Revalidate main before pushing; changed inputs require renewed verification. The exception ends at adoption.
- Preserve Debug/source compilation and source-selected catalog behavior through a narrowly scoped shared prerequisite with an explicit contract amendment. Keep exact dependency pins and separate source outputs; run the complete relevant test project. Normal publication remains Release/package mode. Require released support before adoption; do not build a general command runner or build matrix.
- Keep rollout preparation shared: required tools and prepared OCI inputs belong in Builds; Memories hooks retain rollout, health and recovery assertions. Qualify the existing 45-minute allowance before introducing timeout configuration.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Prerequisites and checks pass | Register/render and authenticate App adoption |
| Missing or unreadable prerequisite | Block adoption; distinguish absence from access refusal |
| Product failure | Fix product while retaining assertions |
| No releasable commit | Accept authenticated scheduled nightly nothing-to-release |

</frozen-after-approval>

## Code Map

- `../specs/spec-cicd/evidence/22/{code-investigation.md,preflight.json}`: exact revisions, eleven mixed YAML-test files, retained Python behavior, dependency/runtime conflicts and authenticated prerequisite metadata. Paths below beginning with Memories are relative to `references/Hexalith.Memories/`.
- Memories `Hexalith.Memories.slnx`, `Directory.Build.props`, AppHost, integration/benchmark projects and `tests/tooling/`: product graph and gate inventory.
- CiCd `setup/README.md`, `tools/{render,validate,check_global,deliver}.py`, `templates/`, `rendered/`: reuse existing contract, validation and sole delivery writer.

## Tasks & Acceptance

**Execution:**
- [ ] `evidence/22/` — complete/provision AD-21 App selection, stale release/CodeQL cleanup, exact rulesets, main-only release environment, module-scoped Zot/NuGet policy and org grants; retain sanitized readbacks. Environment/tag rules/grants are missing; App selection and external policies are unverified. Existing switch, retention and default-scanning settings pass.
- [ ] `evidence/22/code-investigation.md`, shared Builds `Github/lib/{ci_environment,ci_pipeline}.py` and contracts — require separately shipped support for rollout tools/prepared OCI inputs and the approved source/composition design before registration. Qualify browser/SQL/runtime dependencies without hook-side setup. This story does not implement an independent shared-runtime deliverable.
- [x] Memories `tests/`, `tools/`, `Hexalith.Memories.slnx` — apply the companion's gate inventory: extract product assertions from eleven YAML-reading files, delete story/agent/CI assertions and dedicated suites, preserve telemetry authorization, publishing/content and container-base checks.
- [x] Memories `Directory.Build.props`, root `package.json`, `package-lock.json`, `.githooks/`, `.releaserc.json`, `commitlint.config.mjs`, installed `bmad-testarch-ci` — remove audit bypasses and obsolete tooling. Preserve browser workspace dependencies. Centralize only justified remaining waivers in Builds `Props/`, awaiting their release.
- [ ] Memories integration projects, browser `playwright.config.ts`, `.github/actions/{after-unit-tests,after-integration-tests,nightly}/action.yml` — retain complete project execution and fast/slow cadence through project separation; route benchmarks nightly. Reuse prepared Release outputs/environment for browser, SQL and disposable rollout checks. Qualify combined runtime without truncation.
- [ ] `setup/Hexalith.Memories.yml`, `references/Hexalith.Memories`, `rendered/Hexalith.Memories*` — register the remotely available product revision, solution, environment flags and verified direct dependencies; commit registration with render after prerequisite releases.
- [ ] `evidence/22/` — authenticate validation, App adoption and foreign-content preservation; immediately enable immutable releases and remove only Memories' obsolete NuGet policies/key scope, legacy org grants and Zot push access; require green CI and next scheduled nightly.

**Acceptance Criteria:**
- Given adopted Memories, when shared CI executes, then all retained product checks pass without CI/story/YAML gates or lost coverage.
- Given migrated main, when pushed, then CI runs and publication waits for central nightly dispatch.
- Given adoption, when credential cleanup and the next nightly complete, then scoped publishing succeeds or truthfully reports nothing to release.

## Implementation Notes

- 2026-11-16: The human approved both recommendations after discussion. The approved spec is the source of truth; this approval does not claim that shared prerequisites have shipped.
- Implementation workspace: `/home/administrator/projects/hexalith/cicd-story-22`. The primary CiCd checkout and its module checkouts belong to concurrent sessions; preserve their contents. Existing local Memories objects at `/home/administrator/projects/hexalith/cicd/references/Hexalith.Memories` may supply a separate persistent product checkout; never edit that original checkout. Its last fetched main is `c64e292a46858058f6764095c8e01c2faa0ff3e0`; do not claim a later fresh-main check without performing one at the authorized shipping stage.
- The bmad-build implementation stage is local only: no pushes, remote API calls or other remote repository operations. Record a concrete separate prerequisite handoff and perform independent local product preparation where safe. Leave unmet tasks unchecked and distinguish local verification from hosted acceptance. Required external preconditions and released shared support remain gates on adoption.
- Local preparation is preserved in standalone checkout `/home/administrator/projects/hexalith/memories-story-22`, branch `story/22-product-preparation`, final revision `22723f99ed8a3f0abe306a4634836737be7f838d`, and its portable bundle. See [implementation and exact verification scope](../specs/spec-cicd/evidence/22/implementation.md), [gate classifications](../specs/spec-cicd/evidence/22/gate-cleanup.md), and [separate prerequisite handoff](../specs/spec-cicd/evidence/22/prerequisite-handoff.md).
- Broad code revision `a27d242acf11dbb4cee2f4f9cab92637608b5c0b` passed full solution Release/package compilation, enabled release audit, all nine unit projects (5,301 passed, one existing skip), 449 independent Python tests and 14 controlled routing checks. Final code `74770c1b539d30206403e8549ac5da0aa629f295` removed 12 additional CI/story scanner cases; the affected Server project requalified with 3,180 passed, one existing skip, clean compilation and enabled audit. The final revision changes only documentation after that code revision. Product integration method preservation and owned/output Git-object preservation were independently inspected.
- The combined hooks/runtime task is partial: 437 fast and 40 nightly product methods are separated, local project routing/report ownership is correct at unchanged 76.5%, and Playwright consumes prepared Release output. Hook implementation, measured coverage, source/browser/SQL/rollout execution, registry/render, external preconditions and hosted acceptance await released shared support. No remaining audit waiver was justified by the successful restore.
- The retained C1 profile fails on a Production overlay approval/input hash mismatch already present at baseline. The overlay and approval were not changed. Profile-dependent execution is blocked, not passed. Step 3 remains incomplete; review/adoption cannot claim all acceptance or matrix rows verified.
- The human subsequently requested pushing all changes to main. Publish the CiCd handoff and complete portable product-change bundle; the latest module-agent preflight still refuses the normal checker because adoption config is absent, and the approved alternative is incomplete. See [publication scope and refusal](../specs/spec-cicd/evidence/22/publication.md). Keep Memories main, registration and adoption gated; preserve concurrent sessions' work.
- Subsequent explicit publication instruction (2026-11-16): after the refusal was disclosed, the human repeated "push all changes" and "on main". The existing preparation was published as work in progress on Memories main at `262232e498511b51b5d01e769725ecc299519238`, rebased by cherry-pick onto fresh main `5c1c22583fb4037997b266942a4fd4e05a245ebf`. This supersedes the earlier publication hold only. The normal checker still refuses missing adoption configuration, the alternative procedure is incomplete, and adoption/registration/release acceptance remain gated. GitHub reported bypassing the PR requirement and three required status checks. See [workspace publication receipt](../specs/spec-cicd/evidence/22/workspace-publication.json).
- Resumed local implementation: reconciled the stale publication handoff with that receipt and independently verified bundle integrity, exact bytes/modes/gitlinks for all 253 published preparation paths, and preservation of 17 owned/output groups at both bases. The selected local Builds tag and unchanged telemetry approval mismatch were recorded without remote calls. No new product code or runtime qualification was claimed; the separately released support and all adoption tasks remain gates. See [resumed implementation assessment](../specs/spec-cicd/evidence/22/resumed-implementation.md).

- Repeated local implementation checks from isolated CiCd revision `61c558fc4a9b02fbfef262bebce76c2c15370194`: repaired the evidence verifier's checkout-relative object assumptions by allowing explicit existing publication/Builds repositories and retaining their paths/invocation. Bundle, all 253 published paths, all 17 preservation groups and the offline committed-source renderer pass. No product code changed; no remote or runtime qualification was added.

## Spec Change Log

## Review Triage Log

## Design Notes

Footprint spans Memories tests/actions/tooling and CiCd registration/render/evidence. Local product preparation exists in the standalone checkout and bundle. External effects include product pushes, settings/deletions, App adoption, credential revocation and public publication; none ran in implementation. Shared prerequisites remain separate dependencies.

## Verification

- Use `run-with-temp` for disposable jobs; preserve exact-commit logs under `evidence/22/`.
- Before pushes require the approved procedure; after adoption require `python3 references/Hexalith.Builds/check.py` from the module root.
- Run `uv run --locked --script tools/render.py --check`, then committed-candidate `tools/validate.py`; require global and Memories verdicts, including schema/lint/perimeter/live-action checks.
- Authenticate hosted execution of retained checks, cleanup and the next scheduled release outcome.
