---
title: '15 — Migrate McpCli'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
baseline_commit: 'd3f3ef864c08cd89e390246d1a5d1dedffc4a92b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/15/planning.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/15/execution.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** McpCli still uses bespoke release/CI workflows and lacks the delivered baseline. Its native Aspire and cross-platform package checks exceed the existing shared runtime's capabilities.

**Approach:** Satisfy AD-21, preserve product checks through registered actions, replace legacy orchestration with shared CI/nightly release, and adopt exclusively through App delivery. Retain exactly the Abstractions/tool package pair.

## Boundaries & Constraints

**Always:** Follow the canonical gate rule and AD-21 ordering. Use module-agent for product pushes, CiCd-agent for CiCd/Builds and command-local maintainer access for administration. Preserve SDK pins, product behavior, foreign instructions/settings, isolation, audits and failure propagation. Use private disposable workspaces and retain exact evidence.

**Never:** Edit owned module files/gitlinks directly, initialize nested submodules, obtain the App key, fabricate delivered/nightly evidence, skip product tests, waive audits or change unrelated modules. Release packs once and trusts green CI for the same SHA. Retire agent/story/workflow-policy gates; delivery removes owned legacy configuration.

**Human decisions, 2026-11-16:** Extend shared configuration/runtime to preserve macOS product jobs and the complete native Aspire lane, with reusable environment setup and a feasible bounded total CI budget. Retain all product checks.

For McpCli product-preparation pushes before actual App adoption only, authorize package-mode builds/tests, applicable package/consumer checks, policy/commit validation and exact byte/mode/gitlink comparisons proving owned content unchanged from freshly fetched main. Record input revisions and passing results before each push. After adoption, require the normal `python3 references/Hexalith.Builds/check.py`. This grants no owned-file edits, nested initialization, audit/test bypass or alternate credentials.

## I/O & Edge-Case Matrix

| State | Required behavior |
| --- | --- |
| Missing permission, publication policy or runtime prerequisite | Stop the dependent operation; report exact failure and leave unverified state unverified. |
| Live-case failure, skip, timeout or isolation loss | Fail CI, preserve diagnostics and clean private processes/workspaces. |
| Unexpected package or mismatched consumer bytes | Fail before adoption/publication; publish only the approved pair. |

</frozen-after-approval>

## Code Map

- `evidence/15/planning.md` under the main spec: exact revisions, live preflight, gate classification and runtime/publication findings. `preflight.json` retains API outcomes; `pre-adoption-check.log` records the checker failure.
- McpCli `tools/live-topology/{ci.py,native_cohort.py,test_ci.py}`: isolated launcher, audited source fixtures and mixed product/workflow tests. `tools/conformance-vectors/v1/` contains product replay checks with duplicate-build/cache hazards.
- McpCli `scripts/{validate-release-packages.py,smoke-bootstrap-consumer.sh,smoke-paired-tool.py,run-paired-platform-tests.py}`: retain product assertions while removing bespoke release orchestration dependencies.
- Builds `schemas/hexalith.ci.v1.json`, `Github/lib/{ci_config.py,ci_environment.py,ci_pipeline.py}` and `Github/prepare/action.yml`: shared configuration, environment, classification and platform preparation.
- CiCd `tools/render.py`, `templates/.github/workflows/ci.yml.j2`, `tools/{check_global.py,validate.py}`: materialization and committed-candidate qualification.

## Tasks & Acceptance

**Execution:**

- [x] `_bmad-output/specs/spec-cicd/evidence/15/preflight.json` — complete ordered AD-21 provisioning/readbacks, assess actual stale state and identify immediate legacy-access cleanup targets. Current readbacks are recorded in `evidence/15/provisioning-status.json`; initial preflight observations are historical.
- [x] `_bmad-output/specs/spec-cicd/SPEC.md`, `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md`, Builds `schemas/hexalith.ci.v1.json`, `Github/lib/{ci_config.py,ci_environment.py}`, `Github/prepare/action.yml`; CiCd `tools/render.py`, `templates/.github/workflows/ci.yml.j2`, `setup/README.md` — implement the approved runtime/platform contract with compatible defaults and focused qualification. Ship an acceptable Builds release before adoption.
- [x] McpCli `tools/live-topology/{ci.py,test_ci.py}` and conformance scripts — reuse built module outputs, isolate distinct fixtures/caches and preserve every live case, audit/provenance assertion and bounded cleanup; remove YAML assertions.
- [x] McpCli `.github/actions/{after-unit-tests,windows-product,macos-product}/action.yml` and the mapped product scripts — preserve payload, consumer, conformance and platform checks. Delegate Integration.Tests to its real isolated launcher. Remove retired release/agent gate tests and tool-only npm manifests; preserve manual historical evidence.
- [x] McpCli `src/Hexalith.McpCli.Core/Hexalith.McpCli.Core.csproj` — correct packability and verify the complete evaluated release set remains exactly the approved pair.
- [x] `builds-version`, `setup/Hexalith.McpCli.yml`, `rendered/`, `references/Hexalith.McpCli` — after qualified product preparation and shared publication, commit registration/render/pins, validate the committed candidate and publish through normal delivery. Add required direct test-source submodules to setup, never nested initialization.
- [ ] `_bmad-output/specs/spec-cicd/evidence/15/acceptance.json` — authenticate App delivery, immediately enable immutable releases and retire legacy publication grants/policies; record green CI, real platform/live results and its nightly outcome (CAP-13) before accepting done.

**Acceptance Criteria:**

- Given provisioned prerequisites and qualified preparation, when delivery adopts McpCli, then its owned tree matches the accepted perimeter and only rendered workflows remain.
- Given a green adopted SHA, when central nightly releases it, then only the approved package pair is published or a valid nothing-to-release outcome is recorded.
- Given unchanged existing setup files, when shared support is upgraded, then existing modules retain their default behavior and deterministic renders.

## Implementation Notes

- 2026-11-26 — Reconciled the committed migration against the retained evidence. Ordered AD-21 provisioning passed. Builds `v6.2.0` at `0ccd12af6576a3aac601340dec7dba53e86768c3` qualified at registration. The approved package-mode gate passed against the candidate from `97511d77aeb8fd7759bc5f14a32d2550ec5c0cb5`, including six ordinary test projects, the evaluated Abstractions/tool package pair, commitlint, audit lint and the owned-content comparison. McpCli product preparation `aad8894e24b28b254d1ffa69c16b7353a70452fa` was pushed after that qualification. Delivery validated CiCd registration `060ab6e0812e2279e2c2ed0ebdd4c4c7bc3f1778` and adopted McpCli at `c4046ab713f45c8619669adfef793aba7138279a` with the matching perimeter. Immediate cleanup enabled immutable releases and removed legacy NuGet policy 20113. See [product qualification](../specs/spec-cicd/evidence/15/qualify-current-product.json), [authenticated delivery](../specs/spec-cicd/evidence/15/authenticated-adoption.json) and [acceptance](../specs/spec-cicd/evidence/15/acceptance.json).

- 2026-11-26 — Adopted CI run [44175925587](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/44175925587) failed while preparing the isolated Tenants source fixture. MSBuild reported `MSB4019` for its missing Builds `ContainerProvenance.targets` import. Later McpCli commit `70014769c58593d738e979a65c3e71d093fcea0b` binds that import to the prepared catalog. Scheduled nightly [44282863616](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44282863616) also failed for McpCli at the original adopted SHA, with a failed release outcome from [44282959436](https://github.com/Hexalith/Hexalith.McpCli/actions/runs/44282959436) and module scan discovery errors. The latest local source and its rendered workflow pins were inspected offline. Acceptance still needs a green hosted Linux native lane and Windows/macOS product jobs, plus a qualifying CAP-13 nightly outcome for that exact green SHA. The receipt records the archived failures and leaves later hosted outcomes unverified. See [acceptance](../specs/spec-cicd/evidence/15/acceptance.json).

### Historical handoffs

- Push checkpoint, 2026-11-16: the product draft is now committed locally as `d4341dba735a4347793235b60dfa7a89c269b334` on `story/15-product-preparation`, based on fetched main `119a4b59e5e1391ff8ddb4587e1608ad1d1e5145`. The module push remains held by the required package-mode gate; the actual commit is backed up in the [verified source bundle](../specs/spec-cicd/evidence/15/mcpcli-product-current-checkpoint.bundle) and the [push record](../specs/spec-cicd/evidence/15/push-request.json). Older uncommitted-draft descriptions below are historical. No registration, adoption or acceptance is claimed.

- Current continuation, 2026-11-16: authenticated ordered provisioning and metadata-only NuGet inventory are complete; expired key 954800 remains preserved. Read the [execution continuation](../specs/spec-cicd/evidence/15/execution.md), [current qualification](../specs/spec-cicd/evidence/15/continuation-qualification.json), [acceptance state](../specs/spec-cicd/evidence/15/acceptance.json) and [Projects prerequisite](../specs/spec-cicd/evidence/15/projects-publication-prerequisite.md) before dependent work. Current Builds source `6db97d4e9da392ef691ed3f367e73f1b7d2ef318` preserves independent main changes and the proven canonical catalog correction; exact CI [43935156026](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43935156026) is running. Its acceptable release must come through central nightly. Local product/native draft qualification passed 109 controlled launcher, 70 script and 188 conformance tests; the draft remains uncommitted/unpushed on `e2e3db7ba2d45d61feacc39c41b3051310fbc57f`. Full production qualification remains held for genuinely unpublished `Hexalith.Projects.Contracts` `2.0.0-story66.3`. Registration, App adoption, immediate cleanup and real module/platform/live/workflow-timing/nightly acceptance remain incomplete. Earlier notes describe historical handoffs.

- Human authentication resumed: McpCli was additively selected for the App and verified after an actual browser reload; all prior selections and selected-only scope remain intact. [Current provisioning state](../specs/spec-cicd/evidence/15/provisioning-status.json) supersedes the earlier authentication blocker. Continue ordered AD-21 provisioning before dependent product changes.

- Approved and started on 2026-11-16; the independent shared Aspire/macOS/timeout candidate is implemented locally, with compatible renderer behavior. [Execution handoff](../specs/spec-cicd/evidence/15/execution.md) and [qualification](../specs/spec-cicd/evidence/15/local-qualification.json) distinguish passing local checks from unexecuted platform/live acceptance.
- A genuine installation-settings refresh exposed GitHub's **Confirm access** prompt. Human authentication was requested; ordered module provisioning and dependent product preparation/adoption remain pending. No App Save, settings mutation, commit, push, release or adoption occurred. The frozen scope and all task/acceptance obligations are preserved.

- 2026-11-16: Prepared and locally qualified the independent shared-runtime and
  platform contract candidate. No remote mutation, Builds publication, McpCli
  product preparation or App adoption occurred in the implementation handoff.
  See `../specs/spec-cicd/evidence/15/execution.md` for exact revisions, edits,
  passing checks, corrected API diagnoses and incomplete acceptance. The parent
  session is continuing ordered provisioning; all task checkboxes remain open.

## Spec Change Log

- 2026-11-18 — Human approved the [on-demand nightly sprint change](../planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md) (section 4.5): a nightly run on `main`, scheduled or dispatched with `qualify-bump` false, satisfies this story's nightly criterion, judged on this module's own rows (CAP-13, CAP-16). Reworded the scheduled-night lines; no other constraint changed.

## Review Triage Log

## Verification

- 2026-11-26 — Locked offline render check passed at CiCd `3ff573241a6c0d6968be4b12273a1b90f05fc3b9`, with 52 renderer tests passing on both Python 3.12 and 3.14. The local global checks passed for App workflow inventory, committed render inputs and outputs, repeated renders, the selected schema and caller interfaces. The local `validate.py` direct gitlink check passed for McpCli. The authenticated registration run recorded a passing global verdict and successful McpCli delivery. Full current validation also requires remote reads.
- 2026-11-26 — 32 Builds tests passed on each Python version at `80928033b28e7a9726e93c8850389a081d3a2cb6`, covering the schema and loader, native Aspire environment, and macOS prepare handling of validated outputs and restore failures. The [acceptance record](../specs/spec-cicd/evidence/15/acceptance.json) records the test-output digests.
- 2026-11-26 — Nine controlled McpCli tests passed on Python 3.12 at `7e3f3a77661288bbedf083adbe11a5e698294cbc`. They exercised prerequisite refusal, live failure, skips, timeouts, process cleanup, extra packages and mutated package bytes. The shared comparator reported zero perimeter drift both at adoption and when comparing this local McpCli snapshot to the locally recorded delivered CiCd revision `0279c0fb4fbb8d4ef2ad8c5b72e84815cd8e0c31`. See the [verification digests](../specs/spec-cicd/evidence/15/acceptance.json).
- 2026-11-26 — The local nightly scanner's discovery pass against that McpCli snapshot found 30 files and reported 89 errors. It rejected shell wrapper options in the Linux product action and could not resolve several Python subprocess and import expressions in the reached scripts. The scan needs complete source discovery before it can support CAP-13 acceptance. See the [discovery result](../specs/spec-cicd/evidence/15/acceptance.json).

- Run meaningful shared schema/environment/prepare regressions on Python 3.12 and runner Python; qualify actual Windows/macOS product jobs and Linux namespace/live execution.
- Run renderer regressions, `uv run --locked --script tools/render.py --check`, committed-candidate `tools/check_global.py` and `tools/validate.py` under `run-with-temp`.
- Before every module push, apply the approved pre-adoption resolution or normal `python3 references/Hexalith.Builds/check.py` after adoption; retain exact revisions and outcomes.
