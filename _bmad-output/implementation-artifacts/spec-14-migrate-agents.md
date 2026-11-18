---
title: '14 — Migrate Agents'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
baseline_commit: 'd04c9ab7a8fa43dc6dac1f15d34135aba8e79551'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/14/planning.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Agents still uses legacy pipelines, redundant story gates and a mismatched pinned-source check.

**Approach:** Follow AD-21 to adopt Agents through delivery, preserving product checks, original test floors and package behavior. Extend shared test policy so count/skip enforcement also runs locally without duplicate suites.

## Boundaries & Constraints

**Always:** Preserve SDK11/net11/C#15, all product behavior, original floors, foreign content and concurrent migrations. Use module-agent for module writes, CiCd-agent for CiCd/Builds and command-local maintainer for approved administration. Await pilot acceptance before adoption and an acceptable Builds release containing required policy. Save verification outside disposable `run-with-temp` workspaces.

**Never:** Edit owned module portions, initialize nested submodules, weaken audits/tests/scan, use skip markers, obtain the App key, fabricate nightly success or remove legacy access before authenticated adoption. The pilots' checker exception does not apply implicitly.

**Human decision, 2026-11-16 ("approve and stop"):** Approve this spec and an Agents-only preparation proof before actual adoption: full package-mode builds/tests at original floors, actual package/consumer checks, released audit/commit validation and exact owned-byte/mode/gitlink preservation against freshly fetched main. Save exact base/head revisions and passing results before each preparation push. After delivery, require normal `python3 references/Hexalith.Builds/check.py` in a standalone module clone. This grants no owned-file edits, nested initialization, weaker checks or credential substitution. Leave the spec ready for development and stop before implementation.

## I/O & Edge-Case Matrix

**Human decision, 2026-11-16 ("approve"):** Add only the six exact historical Platform project paths listed in the approved `historical-authority-decision.md` proposal to Agents' `eng/package-authority-exclusions.txt`. Preserve all existing exclusions, historical source bytes, live product projects, validator assertions and original test floors. Rerun the full ordered product checks. This approval does not authorize broader exclusions or change the pending adoption prerequisites.

| State | Expected behavior |
| --- | --- |
| Missing prerequisite, refused API or changed main | Record exact evidence; stop dependent writes and revalidate. |
| Too few tests or skipped tests | Fail the project; finish its tests, then stop before its successor. |
| Invalid/unsupported test policy | Reject before execution; never ignore requirements. |
| Default test settings | Preserve existing shared behavior. |
| Package/consumer failure or unresolved scan source | Block adoption; retain diagnostics and fix the cause. |

</frozen-after-approval>

## Code Map

- `evidence/14/planning.md` under the spec folder: exact revisions, gate inventory, file paths, preflight/refusal and verification design; adjacent JSON records actual reads and checker failure.
- Builds `schemas/hexalith.ci.v1.json`, `Github/lib/{ci_config,ci_pipeline}.py`, `Props/Directory.Packages.props`: shared test and audit policy; preserve strict tagged readers and default compatibility.
- Agents `eng/verify-story*.ps1`, `scripts/`, `test/Hexalith.Agents.Server.Tests/{PackageInventoryTests,PackageVersionCentralizationTests,BuildContractConformanceTests,TraceabilityManifestTests}.cs`: split product behavior from pipeline/evidence assertions as detailed in planning.
- `tools/{render,check_global,validate}.py`: reuse existing committed-candidate and live-module qualification.

## Tasks & Acceptance

**Execution:**

- [ ] `evidence/14/` — refresh/provision AD-21: App scope, assessed stale drafts/tags, exact rulesets, main-only release environment, own Zot identity, additive package-scoped NuGet policy, scans/retention/switch and org grants. Apply the approved preparation proof before pushing.
- [x] Builds schema, readers/executor, samples/fixtures and `Github/lib/tests/test_{ci_config,ci_pipeline,local_check}.py` — add explicit `tests.minimumExpectedTests` and `tests.failSkips`, renderer defaults `{}`/`false`, strict validation and identical CI/local execution. Keep all five projects in stage 3.
- [x] Builds `Props/`, Agents `Directory.Build.props` and conformance tests — centralize NU1901/NU1902 treatment, preserve higher-severity failures; release shared changes and select an acceptable tag before adoption.
- [x] Agents server product tests and neutral EventStore-floor script — preserve whole-repository package authority and dependency rejection without rebuilding; retire YAML/story/tooling assertions, redundant runners and tool-only npm files. Keep original floors 529/6/787/549/1073.
- [x] Agents `.github/actions/after-unit-tests/action.yml`, package/consumer scripts and product regressions — reuse built output with no-build packing; preserve six-package/UI/consumer checks, clean scratch and satisfy unchanged discovery/duplication policy. Never call Builds from the hook.
- [ ] `gate-classification.md`, architecture spine AD-13/21, `builds-version`, `setup/Hexalith.Agents.yml`, `rendered/` and Agents gitlink — record decisions, configure both C#/JavaScript CodeQL and the hook/floors, commit cause/output, validate and allow App delivery after pilot acceptance.
- [ ] `evidence/14/` — authenticate adoption and immediately enable immutable releases/remove other NuGet policies and legacy grants; verify green CI and its nightly outcome (CAP-13) before completion.

**Acceptance Criteria:**

- Given satisfied prerequisites, when App delivery adopts Agents, then its owned perimeter matches the accepted render and product/foreign content is preserved.
- Given the five product suites, when CI or local checking runs, then original floors and fail-skips apply once per suite with existing failure ordering.
- Given built Release output, when the enabled product hook runs, then all six package/consumer checks pass without rebuilding Agents or writing retained evidence.
- Given adopted green main, when a nightly run (CAP-13) after adoption finishes, then both CodeQL languages and release success or authentic nothing-to-release are evidenced, with immediate credential cleanup verified.

## Implementation Notes

- 2026-11-17 — The human asked to publish the Agents product files and rerun the floors. The approved preparation proof passed on current main after a concurrent `.gitmodules` move: ordinary `check.py` refused missing config; released v6.2.0 audit/commitlint passed; ordered floors 2005/7/1084/2063/1362 with fail-skips and zero skips; six packages and seven consumers; owned perimeter unchanged. Module-agent fast-forwarded `2d7a4cf96d67ba27458c49fdbaca9ff23d1c0c9a` to Agents main. Evidence is in [`../specs/spec-cicd/evidence/14/prepare-push-20261117/README.md`](../specs/spec-cicd/evidence/14/prepare-push-20261117/README.md). This is not adoption. Story 11 night, Conversations discovery errors, AD-21 refresh, registration, delivery and nightly remain open.
- 2026-11-17 — Sequential local resume in the primary CiCd workspace. Restored Agents `OrdinaryReleaseShouldEvaluateTheHighAndCriticalAuditPolicy` after later product work inverted the published central NU1901/NU1902 assertion, and reviewed/updated `eng/consumer-executable-assets.json` for current catalog EventStore 5.2.0 and Fluent UI 5.1.0. `run-with-temp` qualification of Builds `e8b86ba3` and Agents `e98dab8` plus those two files passes schema/executor/local-check (23/51/40) on Python 3.12 and 3.14, 78 package regressions, the two audit facts, and the real six-package/seven-consumer hook with cleaned scratch. Current `builds-version` `v6.2.0` contains the shared count/skip and central audit policy; it was not used to register or adopt Agents. The prospective scan finds six Agents sources and a complete local Commons snapshot, then fails on seven Conversations discovery expressions, so hook enablement stays blocked. AD-21 refresh, story 11 night acceptance, production `setup/Hexalith.Agents.yml`/render/gitlink, App delivery, credential cleanup and a genuine scheduled nightly remain pending. No owned perimeter, nested initialization, remote operations, commits or pushes. Exact snapshots and logs are in [`../specs/spec-cicd/evidence/14/local-resume-20261117/README.md`](../specs/spec-cicd/evidence/14/local-resume-20261117/README.md).
- 2026-11-16 — Resumed the implementation dispatch with sequential local qualification only. Current committed Builds passes the schema/executor/local-check groups (18/38/38) on Python 3.12 and 3.14; current published Agents passes 67 package regressions and preserves its recorded owned perimeter. The unchanged scanner and real locked/signed detector run offline against a disposable three-module registry: Agents discovers all six sources, but the scan fails on four unresolved discovery expressions in the local Commons snapshot, so no clean cross-module qualification or hook enablement is claimed. The local selected v6.0.6 lacks the required shared test/audit policy; remote release state and AD-21 provisioning were not refreshed. Exact snapshots, logs and remaining prerequisites are in `evidence/14/local-readiness-20261116/README.md`. Pilot acceptance, acceptable release, fresh full-product proof, registration, delivery, credential cleanup and actual scheduled-nightly acceptance remain pending. No module source, owned perimeter, real index, remote state or concurrent changes were modified.
- 2026-11-16 — Resumed bmad-build in the primary CiCd workspace. The rendered implementation step requires sequential local execution with no pushes or remote operations. Verify and finish available local preparation while preserving concurrent workspace changes; keep release, provisioning, delivery and scheduled-nightly acceptance pending until their prerequisites can be fulfilled.
- 2026-11-16 — Published the qualified Builds and Agents preparation commits to their main branches with intended scoped credentials and confirmed remote readbacks. Fresh-main integration passes 565 shared library tests on each Python version and all 6325 Agents tests, six packages/seven consumers, owned-perimeter preservation and released audit/message validation. Exact bases, heads and proof limitations are in `evidence/14/publication/README.md`. CiCd publication records only remotely available submodule commits. No adoption or package release is claimed.
- 2026-11-16 — The human requested "push all changes to main", authorizing publication of the prepared work and overriding the earlier local-stage restriction on repository operations. Prepared isolated publication branches from freshly fetched CiCd, Builds and Agents main, preserving concurrent migrations and newer product changes. Shared conflict resolution combines upstream Aspire/macOS support with count/skip policy. Publication proof and exact commit-message validation are recorded under `evidence/14/publication/`. Adoption, package release and credential cleanup remain separate acceptance requirements.
- 2026-11-16 — Applied the human-approved six exact historical exclusions, preserving all original entries and historical source bytes. The full ordered Release proof passes: Contracts 2005, Client 7, domain 1041, Server 1883 and UI 1352; 6288 total, zero failures/skips, unchanged floors. The first rerun exposed the hosting guard's old validator filename; its exact policy-data exception now follows the extracted validator. Removed its registered agent/workflow automation scan under the existing product-only gate rule, retaining all hosting product checks. The precise six-path exclusion regression, six real packages/seven consumers, released audit lint, owned-byte/mode/gitlink checks and unchanged source discovery pass. Current source trees and approval evidence are in `evidence/14/local-implementation/approved-exclusions.json` and `final-candidates.json`. Shared release, fresh-main/provisioning, cross-module duplication, registration, delivery and nightly acceptance remain pending; no remote operations, commits or pushes were performed.
- 2026-11-16 — Parent task verification corrected three additional shared fixture builders and qualified all five affected library groups with CI's locked Node installation and signatures. The 556-test broad run's initial failures are retained alongside passing reruns. Removed only formatting churn from the Agents candidate; normalized-source equivalence and updated staged trees are recorded in `evidence/14/local-implementation/parent-verification/README.md`. The six-path exclusion proposal is pending a human decision. No frozen intent, exclusions, historical source, floors, audits or scanner policy changed. Full product/adoption acceptance remains unmet, so the workflow has not advanced to review.
- 2026-11-16 — Local implementation prepared shared strict count/skip policy, centralized low/moderate audit treatment, Agents product-check cleanup and a fixed-command package/consumer hook. The unchanged source-discovery engine passes. Whole-repository authority validation with the exact approved exclusions reports 81 errors across six historical foreign Platform projects; no exclusions or historical evidence were changed. See `evidence/14/local-implementation/historical-authority-decision.md` for a proposed exact-path amendment requiring human decision. Shared tests (18/38/38 on each Python), 66 package regressions, six actual packages/seven consumers and independent UI (1352) pass; the ordered Server result remains failed (1883/1884, zero skips). Canonical final source trees and all results are saved in `evidence/14/local-implementation/`. No remote operations, commits, pushes, shared release, production registration, delivery or nightly acceptance occurred.
- 2026-11-16 — Resumed in `/home/administrator/projects/hexalith/cicd-story-14` at the human's direction. This bmad-build implementation stage permits sequential local work only, with no pushes or remote operations. Prepare and verify the local changes; record all dependent provisioning, release, delivery and nightly acceptance work as pending. Preserve the existing baseline and frozen approval.
- 2026-11-16 — Human approved the spec and Agents-only preparation proof with "approve and stop". Re-read and preserved the expanded on-disk task list. Status is ready-for-dev; no implementation, product push or adoption was performed.

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines; no other constraint changed.

## Review Triage Log

## Verification

- Builds targeted schema/executor/local-check regressions on Python 3.12 and runner Python; native SDK11 floor/skip/failure-order qualification.
- `run-with-temp` product builds, full suites, real package/consumer and applicable regression checks; required checker before module pushes subject only to an explicitly approved preparation decision.
- `run-with-temp uv run --locked --script tools/render.py --check`, then committed/global/live validation through `tools/check_global.py` and `tools/validate.py`; common-code scan and authenticated delivery/CI/nightly readbacks.
