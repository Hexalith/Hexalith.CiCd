---
title: CI config contract
type: feature
created: '2026-11-09'
status: done
baseline_revision: '91ac82ca14439206ae1da1e1d5c24f5179fcc6e2'
implementation_baseline_revision: '459c1f2fe347ebcdf125c514dd3e08439d3324a5'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
implementation_repository: references/Hexalith.Builds
---

<intent-contract>

## Intent

**Problem:** The new shared pipelines and future CiCd renderer need one complete, validated CI configuration contract. Story 1 found package-mode builds/tests reading sibling submodules, so the contract must include `submodules`.

**Approach:** Add the versioned JSON Schema, a single stdlib loader, Builds' hand-written config, and shared positive/negative fixtures exercised by both schema validation and the loader in Builds CI.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds` on `main` with the CiCd-agent credential. Follow CAP-1 and spine AD-1/3/4/19 plus Deferred. Require every knob explicitly; schema defaults are renderer metadata and never runtime fallback. `buildsTag` is schema-optional but required by every loader call outside Builds' own repository, including samples. Unknown schema uses the spine's fixed unsupported-schema message. Use draft 2020-12, the existing schema filename/$id convention, camelCase contract keys and closed objects. Runtime Python is stdlib only, >=3.12. CI-only dependencies are pinned with committed PEP723 locks. Validate exact commit messages with pinned commitlint; fetch/check divergence before pushing; preserve full revisions from Git.

**Never:** Change any frozen module-executed file except tests, including existing non-test `Github/` files and six legacy reusable workflows; specifically preserve initialize-dotnet, initialize-build, create-release and verify. No nested submodule initialization, release dispatch, module names/branches in new pipeline code, workflow-text assertions, or unrelated later-story implementation. New runtime code goes in new files. Preserve legacy release and CI jobs until their replacement story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected behavior | Error handling |
| --- | --- | --- | --- |
| Complete document | All knobs with valid paths/names/types | Same values returned, no defaults applied | None |
| Invalid structure | Unknown/missing keys, wrong types, invalid nested entries | Both validators reject | Nonzero CLI and useful location |
| Schema identity | Unknown schema value | Loader rejects | Exact fixed ownership diagnostic |
| Repository context | Missing buildsTag | Allowed only for Builds itself | Module and sample calls fail |
| Unsafe inputs | Absolute/traversal/control/expression paths, malformed tags or names | Both validators reject | No commands executed |
| No solution | solution=none | Tests/hooks/jobs empty, dapr/browsers false | Inconsistent documents fail |

</intent-contract>

## Code Map

Paths are Builds-relative unless noted.

- New `schemas/hexalith.ci.v1.json`: AD-1/3 knobs plus Deferred `submodules`; no prior CI schema exists. Schema defaults support future renderer.
- New `Github/lib/ci_config.py`: one importable stdlib loader/validator and CLI; trusted repository context grants AD-19 exception; resolves its own schema identity from the schema at its commit.
- New `Github/lib/tests/` and fixtures: discovered automatically by `Tools/ci/run_python_tests.py:35`; test both engines on identical cases and test repository-context/CLI failures separately.
- `.github/workflows/builds-ci.yml`: quality job invokes locked API checker; Python job runs identical suite on Python 3.12 and captured runner Python. Wire config validation into these existing lanes without workflow-source tests.
- `Tools/ci/run_python_tests.py` and `.lock`: pinned PyYAML environment; add jsonschema 4.26.0 only to CI tests, lock transitively. `Tools/ci/README.md`: document commands.
- `.github/hexalith-ci.json`: new hand-written Builds config naming `Hexalith.Builds.slnx`, without buildsTag, every knob explicit.
- Existing `schemas/`, `.editorconfig`, `.gitattributes`, package.json/lock and commitlint.config.mjs govern schema style, formatting and commit validation. Existing Tools/ci lint/API helpers are reusable verification commands.
- CiCd story 1 Code Map and `pipeline-stages.md:29`: 8 modules read siblings in package mode; include explicit extra-submodule paths with empty default. Freeze comprises all existing non-test Github files plus domain-ci, domain-ci-v2, domain-release, codeql, commitlint and dependency-review workflows.

## Tasks & Acceptance

**Execution:**
- [x] `schemas/hexalith.ci.v1.json` — define every knob/default, nested shape and path/name restrictions, optional exact stable buildsTag, no-solution conditions and submodules list.
- [x] `Github/lib/ci_config.py` — implement strict stdlib JSON loading and validation with matching schema semantics and fixed unsupported-schema diagnostic; require tag by repository context.
- [x] `.github/hexalith-ci.json` — write Builds' complete configuration without tag.
- [x] `Github/lib/tests/` and fixtures — cover matrix and schema/loader agreement, explicit defaults, nested unknown keys, exclusions targeting enabled actions, and CLI/import behavior.
- [x] `Tools/ci/run_python_tests.py`, `.lock`, `.github/workflows/builds-ci.yml`, `Tools/ci/README.md` — run shared fixtures and Builds config through both validators in existing dual-Python lanes; document schema defaults and loader API.
- [x] Builds Git and this spec — verify frozen blobs, lint/API/tests; commit/push implementation; record result and stage superproject pointer with this spec.

**Acceptance Criteria:**
- Given a Builds push, when its CI Python matrix runs, then the same fixture corpus passes/fails under both independent validators on Python 3.12 and runner Python, and either validator disagreement fails CI.
- Given Builds' hand-written config, when the CI contract checks run, then it validates without buildsTag and contains every knob including submodules.
- Given the final delivery diff, when frozen runtime blobs are compared with the implementation baseline, then they remain byte-identical, including the four explicitly named composites.

## Implementation Notes

- Added the CI schema, one stdlib loader/CLI, complete hand-written Builds config and 178 shared structural fixtures (9 valid, 169 invalid). The existing Python runner discovers the new lib test group automatically; its pinned jsonschema 4.26.0 dependency and transitive hashes are locked. CI invokes both engines through that group on both interpreters.
- Loader-only supplemental tests enforce trusted repository/sample context and dynamic exclusion-target membership, which standard document-only JSON Schema cannot express. Runtime readers never materialize defaults. CodeQL defaults and the additional-direct-submodules knob are documented for the future renderer and pipeline.
- Parent inspected all nine changed files and the staged unified diff. Corrected the new schema $id from the existing schemas' hexalith.dev convention to the spine-required https://hexalith.com/schemas/hexalith.ci.v1.json. Parent focused suite passed 14 tests after this correction; a deterministic 4,500-case path parity probe also passed.
- Parent ran `python3 -I Github/lib/ci_config.py .github/hexalith-ci.json --repository Hexalith/Hexalith.Builds`, repeated online lint (24 inputs, 12 exact frozen findings, zero new), and compared all 58 frozen runtime files with the implementation baseline: all byte-identical. Exact commit candidate passed pinned commitlint 21.2.4 with zero problems/warnings, recorded in /tmp/story-2-3-commitlint.log. No commit/push or release dispatch yet.
- Full locked suites run with `/tmp/hexalith-builds-ci-tools/uv run --no-cache --locked --script --python <3.12-or-/usr/bin/python3> Tools/ci/run_python_tests.py`; both logs end with 19/19 groups passed, including the original 14 contract tests and 46 existing helper/policy tests, on Python 3.12.13 and 3.14.4 respectively. Logs: /tmp/story-2-3-python312.log and /tmp/story-2-3-runner.log. Committed-revision API validation and hosted checks remain delivery steps.

- Matrix audit: complete documents, structural invalids, exact schema diagnostic, repository/sample context, unsafe paths/tags/names and no-solution constraints each have passing coverage in the 14 contract tests and shared fixture corpus.

## Spec Change Log

## Review Triage Log

### 2026-11-09 — Review pass

- verdicts: 14 findings — high 0, medium 2, low 10, false 2, maybe-false 0.
- All four context-free layers completed. Three ran concurrently; the fourth initially hit the three-reviewer capacity limit and was launched immediately when the first slot freed, before triage. The claims file was withheld from the blind, gap and intent layers. Review content contains the implementation diff and other superproject changes; the story's narrative is supplied only as the edge layer's claims file.
- findings, in layer-report order:
  - `[medium]` `[patch]` Verification gap: stdlib runtime tests retain third-party site packages — pre-verified by mutation: adding import jsonschema leaves all original tests green. Add a CLI test using -I -S, preserving the existing PYTHONPATH isolation case.
  - `[low]` `[patch]` Edge: deep JSON escapes ConfigError — parent reproduced RecursionError on Python 3.12.13 with 10,000 nested arrays; Python 3.14 already returns a caught ValueError. Extend the existing exception normalization and cover both import and CLI. Shares the blind recursion repair.
  - `[false]` `[reject]` Intent: config validation does not exercise submodule initialization or hook execution — the auditor confirms this matches the referenced story's contract scope. The user requests the knob conditionally, and story 1 supplies the affirmative evidence; the knob is included. Pipeline consumption and filesystem existence checks belong to later stories, not an omitted behavior of this loader change.
  - `[false]` `[reject]` Intent: a diff cannot prove commits, pushes or frozen-blob comparisons — correct as an evidence limitation, not a defect. Parent independently compared all 58 frozen files; reviewed commit/push and exact-revision hosted checks are final delivery steps recorded in Auto Run Result.
  - `[low]` `[patch]` Blind: Unicode separators differ between Python and ECMAScript regex engines — parent reproduced foo\u2028bar.slnx accepted by the loader and rejected by Node's RegExp. Replace dot-based any-character matching with portable character classes and add cross-engine cases.
  - `[low]` `[patch]` Blind: deeply nested JSON leaks RecursionError — same demonstrated Python 3.12 root cause as the edge finding; shares its normalization and regression tests.
  - `[low]` `[reject]` Blind: malformed shipped schema identity structure raises KeyError/TypeError — true for an altered or corrupt loader installation, but the schema is trusted versioned runtime data and the contract tests fail before such a schema can ship. Everyday callers cannot supply it. Structural fallback guards add branches for this unlikely installation state, so no repair is warranted.
  - `[low]` `[reject]` Blind: escaped lone surrogates pass path checks and cannot encode as filesystem paths — parent reproduced UnicodeEncodeError on such a synthetic path. These invalid Unicode scalar strings are unlikely in ordinary checked-in module paths; adding scalar/UTF-16 compatibility guards to both engines adds complexity for that rare state. Retain as a documented limitation of lexical validation, with real path existence checked by later consumers.
  - `[medium]` `[patch]` Blind: untrusted diagnostic text can create separate workflow-command lines — parent reproduced an unsupported schema yielding a newline followed by ::error::. Escape diagnostic controls across schema values, unknown keys and rejected path-key locations, preserving normal fixed-message bytes.
  - `[low]` `[reject]` Blind: array uniqueness has quadratic cost — the slice/scan behavior is real, but a 20,000-entry submodule list is far outside the 17-module workspace's ordinary configs. Reordering typed validation and maintaining hash sets adds special handling for negligible everyday cost.
  - `[low]` `[reject]` Blind: JSON files have no size budget — whole-file loading is real, but a new arbitrary size limit is not required by this contract and would add a configuration restriction and guards for oversized committed files. Ordinary configs are small; no demonstrated normal input exhausts memory.
  - `[low]` `[patch]` Blind: solution=none has two applicable CodeQL default annotations — parent confirmed both csharp and empty defaults apply, and JSON Schema defines no override precedence. Move them to mutually exclusive branches while keeping explicit required values and renderer semantics.
  - `[low]` `[patch]` Blind: additive language/hook enums can escape the fixed corpus — all current values are covered, but a schema-only addition can remain green. Add an independent assertion that positive shared fixtures cover the complete schema language/hook enums, so the documented parity check detects such drift.
  - `[low]` `[reject]` Blind: duplicate-key errors omit containing-object/line information — true; current errors still identify source file and duplicate key. Preserving decoder positions would require more parsing machinery for a negligible improvement in small config files, and is not warranted.
- Six grouped repairs were sent to the original implementation agent: stdlib isolation (medium), diagnostic escaping (medium), recursion normalization (low), portable regex (low), default metadata (low) and enum coverage (low). No intent gap, bad-spec loopback or deferred entry. The original agent applied all six repairs. Parent read the repair diff; focused verification passed 18 tests and 179 shared fixtures on both interpreters. Final full locked verification passed 19/19 groups with exit 0 on Python 3.12.13 and 3.14.4; both include all 18 contract tests and 46 helper/policy tests.

## Design Notes

Represent hooks as a unique list of the three fixed hook names; jobs as a map of kebab-case names to closed `{runner: windows-latest}` objects; tests as `{integration: [project paths], exclude: {project path: enabled action name}}`. Defaults: solution `none`, false boolean knobs, empty lists/maps; codeql `[csharp]` for a solution and `[]` for none, documented for renderer materialization. Submodules lists additional direct repo-relative submodule paths; Builds checkout remains implicit. Schema cannot know repository identity, so missing-tag contextual negatives supplement the shared schema fixture corpus.

## Verification

Run locked full Python suites under 3.12 and runner python3, pinned actionlint/online zizmor, public API comparison, direct isolated stdlib loader CLI positive/negative cases, frozen-blob comparison and `git diff --check`. Validate pinned commitlint candidate, fetch/check divergence, push Builds main, inspect exact-SHA hosted checks without release dispatch. Record precise commands/results and any unrelated blocker.

## Auto Run Result

Status: done. Reviewed implementation and final local verification are complete; delivery identifiers and hosted results are appended below.

- Implemented the complete CI config contract, versioned schema, one stdlib loader/CLI, Builds' hand-written config without buildsTag, and explicit additional-direct-submodules knob required by story 1. Runtime readers never apply defaults. The schema and loader exercise the same 179 structural fixtures (10 valid, 169 invalid); contextual repository/exclusion checks have supplemental loader coverage.
- Files changed in Builds:
  - `schemas/hexalith.ci.v1.json` — closed draft-2020-12 contract, explicit requirements, names/paths, conditional defaults and submodules.
  - `Github/lib/ci_config.py` — strict stdlib loader/CLI, trusted repository/sample context, source diagnostics and controlled malformed-input failures.
  - `Github/lib/tests/fixtures/contract.json` — shared complete valid/invalid documents.
  - `Github/lib/tests/test_ci_config.py` — independent schema/loader agreement, context, CLI, stdlib-only, diagnostic, recursion and cross-engine regex tests.
  - `.github/hexalith-ci.json` — complete Builds-owned configuration, no buildsTag.
  - `Tools/ci/run_python_tests.py` — pinned CI-only jsonschema dependency; existing discovery runs the contract group.
  - `Tools/ci/run_python_tests.py.lock` — transitive versions and artifact integrity.
  - `.github/workflows/builds-ci.yml` — identifies both validators in the existing dual-Python suite lane.
  - `Tools/ci/README.md` — contract defaults, loader API/CLI and contextual validation boundaries.
- Review: 14 rows; high 0, medium 2, low 10, false 2. Seven rows share six applied repair entries: medium 2, low 4. No deferred entries or spec loopbacks. Rejected findings: runtime checkout/hook execution is outside this contract story; delivery evidence is supplied by Git and hosted checks; corrupt trusted schema installations are rare and already fail CI; lone-surrogate path guards add complexity for invalid Unicode; quadratic scans are negligible for ordinary small configs; an arbitrary input-size restriction adds unnecessary policy; duplicate-key source/key diagnostics are adequate without a custom position-preserving parser. Each rejection and its evidence is recorded separately in Review Triage Log.
- Verification: final locked full suites passed **19/19 groups** on both Python **3.12.13** and runner **3.14.4**, exit 0. Each runs all **18 contract tests**, **179 shared fixtures**, and **46 existing helper/policy tests**. Logs: `/tmp/story-2-3-final-python312.log`, `/tmp/story-2-3-final-runner.log`. The original full runs also passed before repairs. Parent read every changed file and the repair diff; the matrix audit has no missing/skipped row.
- Final pinned actionlint/online zizmor passed: 24 inputs, 12 exact frozen findings, zero new findings (`/tmp/story-2-3-final-lint.log`). Parent direct isolated CLI and a 4,500-case parity probe passed. Whitespace and exact-message pinned commitlint 21.2.4 passed. All 58 frozen runtime files, including initialize-dotnet, initialize-build, create-release and verify, are unchanged against the implementation baseline.
- Follow-up recommendation: false. The two medium repair entries would ordinarily warrant another pass, but no specific unverified implementation risk remains after focused regressions and complete dual-interpreter verification. Patched entry counts: high 0, medium 2, low 4.
- Residual limits: JSON Schema alone cannot know trusted repository context or correlate arbitrary exclusion targets, so the loader supplies these checks. Validation is lexical; later delivery checks real action/submodule existence. Rare malformed trusted installations and lone-surrogate paths retain the limitations described in rejected findings. No release was dispatched.

- Delivery commit: `8a3a11d3614f8549100ed9758bb96bf26ab885ff`, exact subject validated with pinned commitlint. Fetch before push showed one local commit and zero remote-only commits. Push fast-forwarded Builds main; full HEAD and origin/main match this revision and the owning working copy is clean.
- Committed-revision API comparison passed against v4.45.1 (`25de7a74d14d099faf7baea5da0cbb0b40264592`), **2,473 entries**, no removals. Log: `/tmp/story-2-3-final-api.log`. All 58 committed frozen blobs match the implementation baseline, and the committed message equals the validated candidate.
- CiCd stages this story and the updated Builds gitlink together, following the submodule-story rule. No superproject commit/push was requested; the implementation is committed and pushed in Builds. Hosted evidence and concurrent-push result follow.

- Hosted [Commitlint 42613326681](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42613326681) completed successfully at the delivery revision. In [CI 42613326664](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42613326664), CodeQL and the Workflow lint and public API job passed; the quality log confirms 2,473 compatible entries and 12 exact frozen findings/zero new findings. Log: `/tmp/story-2-3-hosted-quality.log`.
- CI was then **cancelled by a concurrent push**, not a contract-test failure. At 2026-11-09T12:06:22Z another writer pushed merge `b5eb25c630b58322fa13f1c5e384b9909b66099b`, whose first parent is the delivery revision. The existing builds-ci concurrency group cancels superseded main runs. All unfinished jobs were cancelled and the aggregate job failed because its dependencies were cancelled. The run ended cancelled at 12:06:47Z. Run JSON is saved in `/tmp/story-2-3-hosted-ci-result.json`; Commitlint JSON is `/tmp/story-2-3-hosted-commitlint-result.json`.
- The concurrent merge changes four unrelated legacy/runtime/test files; it changes none of this story's nine reviewed files. Parent fetched and verified the delivery commit remains an ancestor of origin/main (zero local-only, two remote-only commits). The local Builds checkout and staged CiCd gitlink intentionally remain at the reviewed delivery revision, whose 58 frozen blobs are unchanged. The owning checkout is clean. No rerun was started because it would cancel the other writer's active main run. The successor [CI 42614232566](https://github.com/Hexalith/Hexalith.Builds/actions/runs/42614232566) belongs to that concurrent merge; it is not claimed as exact-revision verification for this story.
- Final result: implemented, reviewed, locally verified on both interpreters, committed and pushed. Hosted lint/API/CodeQL and Commitlint passed; full exact-revision hosted CI remains unverified after external supersession. All authorized story changes are committed; only this story record and the reviewed Builds pointer are staged in CiCd. No implementation or deferred task remains.
