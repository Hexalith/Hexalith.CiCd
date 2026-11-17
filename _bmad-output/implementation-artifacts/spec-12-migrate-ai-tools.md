---
title: '12 — Migrate AI.Tools'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
baseline_commit: '7d32df03405c876df6f098aec4036207bf35af1d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/12/planning.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/12/execution.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** AI.Tools has no managed CI, release workflow or run-history baseline.

**Approach:** Onboard this documentation/skills repository through AD-21 using `solution: none`, preserve its content, and verify real delivery, green CI and its next nightly outcome.

## Boundaries & Constraints

**Always:** Wait for story 11's genuine scheduled-night checkpoint and acceptance before adoption. Preserve concurrent work; establish a clean branch from freshly fetched main. Use module-agent for product writes, CiCd-agent for CiCd, command-local maintainer for administration. Require successful Builds checking before module pushes except for the approved preparation proof below. Use `run-with-temp` and standalone module clones; save evidence outside scratch.

**Never:** Edit owned module portions, initialize nested submodules, weaken checks, invent packages/tests/baselines, obtain the App key, manually dispatch the acceptance night, or revoke legacy access before authenticated adoption. Do not extend the pilots' exception implicitly.

**Human decisions, 2026-11-16 ("do recommended"):** For package-free AI.Tools, retain the main-only release environment and normal GitHub release behavior, omit unused NuGet/Zot publishing credentials and policy, and require them before adding any package/container target. For AI.Tools product preparation before adoption only, replace the unavailable checker with released commitlint/audit checks, exact owned-byte/mode/gitlink preservation, documentation/removal consistency and synchronized entrypoint checks; save exact base/head revisions and results before any push. After delivery, require the normal checker in a standalone clone with Builds as a direct dependency. No owned bootstrap, nested initialization or weakened check is authorized.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| No solution, actions or workflow history | Guard/commitlint CI; empty build/test/CodeQL lists; empty Dependabot updates; baseline metrics unavailable. |
| Missing prerequisite, refused API or concurrent main change | Record exact result; stop the dependent write; refresh and revalidate. |
| Releasable history without packages/containers | Normal GitHub-only release; no fabricated publishing inventory. |
| No releasable history | Record authentic nothing-to-release; never force a version. |

</frozen-after-approval>

## Code Map

- `evidence/12/planning.md` under the main spec folder — exact sources, preflight, concurrency and proposed preparation proof; `planning-preflight.json` contains actual GETs and refusals.
- AI.Tools `package.json`, `package-lock.json` — tool-only package metadata to remove during product preparation; `commitlint.config.mjs` is owned by the perimeter's absent-glob and must be preserved exactly until delivery removes it. Related guidance lives in README, three entrypoints and `hexalith-{git,llm}-instructions.md`.
- `tools/render.py`, `tools/validate.py`, `setup/README.md` — existing no-solution registration and committed-candidate checks; no runtime change needed.
- Builds `check.py`, `Github/lib/{ci_pipeline,guard_commitlint,guard_tools,audit_lint,release_version,release_build}.py` — reuse released checking and empty-inventory behavior.

## Tasks & Acceptance

**Execution:**

- [ ] `evidence/12/` — refresh revisions and pilot acceptance; verify/provision AD-21 in order: App selection, stale state, exact rulesets, main-only release environment, resolved publishing prerequisites, disabled default scans, exact publish switch, retention and grants. Record zero-history baseline.
- [x] `ARCHITECTURE-SPINE.md` under the architecture planning folder — record the approved AI.Tools package-free applicability and preparation-check decisions beside AD-21 without extending either exception to other modules.
- [x] AI.Tools `package.json`, `package-lock.json` and guidance above — retire tool-only npm package metadata, use shared validation and align stale Update branch wording with canonical policy; preserve foreign content and the exact owned `commitlint.config.mjs` blob/mode for delivery-owned deletion. Qualify every edge case through existing checks and actual readbacks; apply the approved preparation proof before any push.
- [x] `setup/Hexalith.AI.Tools.yml`, `rendered/`, `references/Hexalith.AI.Tools` gitlink — register explicit `solution: none`, current prepared main and unchanged acceptable Builds pin; commit cause and render together, fully validate before pushing. Preserve other registrations.
- [ ] `evidence/12/` — authenticate accepted ref, App adoption commit, artifact and complete owned/foreign trees; immediately enable immutable releases and remove only applicable legacy policy/secret/key/Zot access. Record green CI, normal checker and next scheduled release/scan/delivery outcomes.

**Acceptance Criteria:**

- Given accepted pilots and verified prerequisites, when delivery adopts AI.Tools, then one authenticated adoption commit establishes the expected perimeter and preserves product/foreign content.
- Given adopted main, when CI and the normal local checker run, then both succeed without requiring .NET work or module workflow assertions.
- Given adopted green main, when its next genuine nightly finishes, then an authenticated successful release or nothing-to-release outcome and central scan/delivery results establish CAP-16 completion; disabled publishing alone does not.

## Implementation Notes

- Local phase only, following `evidence/12/execution.md`: no push, provisioning,
  App selection, dispatch, credential changes or other remote operations.
- Standalone AI.Tools preparation is committed locally on
  `docs/cicd-adoption-12` at `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6`, from
  base `736687b79c1e4fa8beabdab75c4675bb76c466b9`. It retires the tool-only npm
  package/lock files and preserves the exact owned legacy commitlint config for
  delivery to remove. It documents runnable shared message validation, synchronizes the three
  entrypoints and aligns Update branch guidance. Its exact approved local
  preparation proof passes; remote freshness must be checked again before push.
- `setup/Hexalith.AI.Tools.yml` and five generated artifacts are prepared with
  explicit `solution: none` and unchanged `v6.0.6`. The two pilot registrations
  and renders are unchanged. The module gitlink remains the existing published
  base; it does not record the unpushed preparation commit. Commit/integration
  with prepared current module main remains pending.
- At handoff the shared local `origin/main` was
  `d3f3ef864c08cd89e390246d1a5d1dedffc4a92b`, one documentation-only commit
  after the starting base; it changes this spec/execution handoff only. The
  dedicated branch is preserved and fresh-main integration remains pending.
- Story 11's genuine scheduled night at `2026-11-17T02:17:00Z` and its acceptance
  remain prerequisites. AD-21 live preconditions, authenticated adoption,
  post-adoption checker/green CI and the subsequent genuine nightly outcome
  remain incomplete. See `evidence/12/implementation.md` for the exact handoff.

- Subsequent human request, 2026-11-16: "push all changes to main" authorizes
  remote publication beyond the historical local-only phase. The renewed-proof
  product preparation is published on AI.Tools main at
  `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6`; the owned legacy config remains
  intact. Central policy/evidence, the published gitlink and the root snapshot
  are being qualified for main. Adoption registration remains excluded pending
  clarification of the approved pilot gate. See `evidence/12/publication.md`.
- Current-main local resume, 2026-11-17: registration is already on shared
  `main` `522d011e69f1cca91fe118808f9849c5fa076568` with explicit
  `solution: none` and current `v6.2.0` render. Delivery later applied and
  then bumped the module to `3a4a78d91b36849c4700e8bc9aae74a1b91f2fba`. The
  committed gitlink still names `180ca5692637a018c3f5547daf657e2a90bd5288`
  (`v6.1.0`); that snapshot fails the normal checker with authentic pin drift.
  A standalone clone of the sibling-local `3a4a78d` object passes
  `python3 references/Hexalith.Builds/check.py`. The gitlink was not updated
  without an authenticated fetch. Story 11 acceptance and ordered AD-21 live
  work remain incomplete. See
  [`../specs/spec-cicd/evidence/12/resume-20261117.md`](../specs/spec-cicd/evidence/12/resume-20261117.md).
- Authorized live resume, 2026-11-17: story 11 remains unaccepted (next genuine
  night `2026-11-18T02:17:00Z`). Authenticated AI.Tools main is
  `3a4a78d91b36849c4700e8bc9aae74a1b91f2fba`. App installation already includes
  Hexalith.AI.Tools with selected-only scope. AD-21 package-free preconditions
  were verified or created: exact rulesets, empty stale inventory, main-only
  `hexalith-release` without Zot secrets, `HEXALITH_RELEASE_PUBLISH_ENABLED=true`,
  disabled default scans, 90-day retention, and normal pull-secret/`HEXALITH_NUGET_USER`
  grants. Digest-matched delivery `44040325762` pushed initial adoption
  `180ca56`; run `44068630104` pushed `3a4a78d`. Owned/foreign trees match
  accepted perimeter `2a5fd36`. Immutable releases are enabled; legacy org-secret
  membership, repo secrets and deploy keys are no-ops. Local CiCd
  `709a9b6ca40cf200271396a47522f710f612a4c1` records the gitlink on published
  `main` (current tip `93eb23114d4ca41b92c3dccf21c8e1baa9c5870e`). Render
  `--check` and authenticated `tools/validate.py` passed
  (`global: true`, AI.Tools/Commons/Conversations/PolymorphicSerializations).
  Hosted CI `44071290863` succeeded on adopted main. Authenticated standalone
  `check.py` exits 0. The next genuine AI.Tools night is still pending. See
  [`../specs/spec-cicd/evidence/12/live-refresh-20261117.json`](../specs/spec-cicd/evidence/12/live-refresh-20261117.json).

## Spec Change Log

- Isolated resume, 2026-11-16: the same six held registration additions pass
  offline committed-input/render, reproducibility, schema, caller and direct
  gitlink checks on the authorized isolated base
  `0f25d19ba712eee9aae59d118251b854bbffd120`. Its updated existing
  renderer and validator suites pass 35 and 52 tests. Historical source evidence
  is preserved; exact revisions, digests, logs, local ref drift and pending live
  sequence are in `evidence/12/isolated-resume.md` and
  `isolated-resume-check.json`. No remote operations, integration, adoption or
  acceptance are claimed, and the frozen intent and task status remain unchanged.
- Local resume, 2026-11-16: the six held registration additions pass existing
  committed render/input, schema, caller and direct-submodule checks on a
  disposable candidate from current local main
  `771cfd0f01416d9adb2bdb3ff8cf8d1437d385e1`, whose AI.Tools gitlink already
  records published preparation `cfd1ebea92587cdea41b9aa2cff47358bf2f32f6`.
  Existing registrations and all other committed files are preserved. This
  local observation does not refresh remote state, integrate the held branch,
  satisfy the future pilot-night gate or claim adoption. Exact results and the
  remaining live sequence are in `evidence/12/resume-local.md` and
  `resume-local-check.json`; status and acceptance tasks remain unchanged.
- Current-main resume, 2026-11-17: committed registration/render pass offline
  committed-input/render, reproducibility, schema, caller and direct-submodule
  checks on local `main` `522d011e69f1cca91fe118808f9849c5fa076568` at
  `v6.2.0`. Existing renderer and validator suites pass 49 and 54 tests; four
  released Builds tests cover empty inventory, first-release analysis,
  nothing-to-release and `solution: none` guard enforcement. The committed
  gitlink `180ca56` fails the standalone checker (v6.1.0 versus expected
  v6.2.0); sibling-local `3a4a78d` passes. No remote operations, gitlink
  update, adoption claim or checkbox change. Exact results are in
  [`../specs/spec-cicd/evidence/12/resume-20261117.md`](../specs/spec-cicd/evidence/12/resume-20261117.md)
  and `resume-20261117-check.json`.
- Authorized live resume, 2026-11-17: AD-21 package-free provisioning, App
  selection UI readback, delivery artifacts, tree comparison, immutable-release
  enablement, legacy no-ops, hosted CI, and the authenticated standalone checker
  are recorded under `evidence/12/`. Product-preparation and registration/gitlink
  tasks are complete. Story 11 acceptance and the next genuine night remain open.

## Review Triage Log

## Verification

- Isolated current-base results: `isolated-resume-check.json` records passing
  offline committed candidate checks and 87 existing tests (35 renderer,
  52 validator), using exact released v6.0.6 Builds objects. Only the six held
  registration files enter the temporary candidate; all existing committed
  files are preserved. Full live validation and adoption remain pending.
- Local results: renderer generation and `--check` pass; the existing renderer
  suite passes 32 tests and validator suite 51. A disposable committed CiCd
  candidate passes existing committed-input/render, schema and caller-interface
  checks. This is an offline preparation result, not the full live verdict.
- `preparation-proof.json` records exact base/head, shared and prior owning
  message lint, audit lint, unchanged blobs/modes/gitlinks, entrypoint and
  removal consistency. The normal checker remains unavailable before adoption
  (exit 2); no owned bootstrap or nested dependency was created.
- The earlier unpushed preparation incorrectly removed the owned legacy
  commitlint config; its proof is explicitly superseded. The corrected head
  preserves that exact base blob/mode for delivery-owned deletion and passes
  the narrowed approved proof. The 83 existing tests cover registry/render/schema
  cases; actual empty-package release behavior and the full live matrix/acceptance
  audit remain pending with the live gates.
- `readme-recipe-verification.json` authenticates the exact documented shared
  message-validation recipe against the full saved candidate. It runs against
  CiCd's existing direct released Builds dependency; AI.Tools is not adopted.
- Full `tools/validate.py`, online audits, fresh live release/settings readbacks
  and acceptance checks below are deferred by the no-remote-operations phase.
- 2026-11-17 current-main results: `resume-20261117-check.json` records passing
  committed registration checks on `522d011e69f1cca91fe118808f9849c5fa076568`
  with released `v6.2.0` (`0ccd12af6576a3aac601340dec7dba53e86768c3`). Renderer
  49, validator 54, and four Builds empty-inventory/no-release/guard tests
  passed. The committed gitlink checker exits 1 on `180ca56`/`v6.1.0`; the
  sibling-local `3a4a78d`/`v6.2.0` checker exits 0. Concurrent story 11 files
  were excluded. Matrix machinery coverage from those passing suites: no-solution
  empty inventory (`test_minimal_complete_defaults_and_exact_output_tree`,
  `test_dependabot_exact_solution_policy`,
  `test_solution_none_has_the_same_guard_enforcement`); refused/missing API
  (`test_http_reader_bounds_get_and_rejects_auth_errors_malformed_and_oversized_json`,
  `test_unavailable_missing_and_malformed_api_never_certify_release`);
  empty-package first release (`test_none_payload_does_not_execute_sdk_or_submodules`,
  `test_first_release_analyzes_full_history_and_is_exactly_one`); authentic
  nothing-to-release (`test_no_version_tagless_or_at_base_has_explicit_noop`).
  Live AD-21, full validate, authenticated adoption trees, hosted CI and the
  next genuine AI.Tools night remain pending.

- `run-with-temp uv run --locked --script tools/render.py --check` — reproducible output after generation.
- `run-with-temp uv run --locked --script tools/validate.py` — complete committed/global/live-module verdict; supply intended read-only authentication privately.
- `run-with-temp python3 references/Hexalith.Builds/check.py` — successful post-adoption standalone-module guard/checker.
- Inspect authenticated App settings, delivery report/tree, immutable release setting and actual next scheduled run. Preserve exact failures; fixtures cannot establish live acceptance.
