---
title: '4-2 Setup files and the render'
type: feature
created: '2026-11-13'
status: done
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 8cd22fb6452295ad14d71f1caa872ff2cf780951
builds_contract_tag: v5.1.0
builds_contract_revision: 9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** CiCd has the released Builds CI, release and perimeter APIs but no setup handling, templates or renderer. CAP-4 needs reproducible owned files and perimeters before any module can be onboarded.

**Approach:** Build a local renderer in this superproject that materializes setup files against Builds at `builds-version`, validates the rendered documents, and emits complete module callers/configuration plus `rendered/<Repo>.perimeter.json`. Establish the Dependabot policy and qualify everything with synthetic setup files; halt this invocation after planning.

## Boundaries & Constraints

**Always:** Implementation belongs to `setup/`, `templates/`, `rendered/`, and `tools/`. Treat exactly `setup/*.yml` as the registry, with each stem the repository name; reject `Hexalith.Builds.yml`. Inputs are setup files, templates, `builds-version`, and Git objects from Builds at that exact stable tag. Python is at least 3.12. `tools/render.py` declares PEP 723 dependencies pinned to Jinja2 3.1.6, PyYAML 6.0.3 and jsonschema 4.26.0, with its committed `uv lock --script` lock and `uv run --locked` execution (AD-11). Render through Jinja `StrictUndefined`, emitting every substituted value/key through `tojson`; preserve GitHub expressions literally. Validate final serialized CI JSON and perimeter against both pinned schemas and pinned strict loaders. All Builds references and the perimeter gitlink tag agree with `builds-version`. Write UTF-8 without BOM, LF and one final newline, in stable order. Fixtures live under `tools/tests/fixtures/`; production `setup/*.yml` stays empty until onboarding.

**Never:** Read module checkouts, infer settings from module contents, fetch remote state during rendering, modify Builds, or add an independent registry/schema/default policy. Do not implement delivery, acceptable-release API checks, global-check orchestration, guard/restore, scheduler, or onboarding here. Do not change the pin or submodule pointers. Render only whole owned files; partial ownership belongs inline in the perimeter. Do not enable Dependabot Actions/submodule updates, add automerge workflows, widen credentials, or dispatch/publish anything. Story 10-2 supplies the real instruction-block and deny-entry policy: this story's exact interim outputs below are intentional, bounded behavior.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Empty registry | `setup/` exists with README only | No module directory/perimeter; preserve `rendered/.gitkeep` | Success; no inferred registrations |
| Defaults | `Hexalith.Fixture.yml` contains `{}` | Complete CI document with `solution: none`, false environment flags, empty tests/hooks/jobs/submodules and default empty CodeQL | Success through both validators |
| Partial setup | Solution supplied; some knobs or nested `tests` keys omitted | Schema defaults fill only missing fields; absent CodeQL becomes `[csharp]`; explicit `[]`, false and empty collections survive | Missing required values without defaults fail |
| Full configuration | All hooks, registry, integration/exclusion targets, Windows jobs, sibling submodules | Complete configuration plus same-tag callers; every Windows job uses the CI outputs | Success; no module-content lookup |
| Invalid setup | Duplicate/non-string YAML keys, non-object root, supplied `schema`/`buildsTag`, unknown keys, invalid types/null, reserved jobs, missing exclusion targets or invalid solution-none combination | No output mutation | Nonzero, filename/key diagnostic; no dropped/coerced keys |
| Unsafe interpolation | Unsafe paths/names/control characters or expression injection; valid paths containing quotes/spaces/Unicode | Invalid values fail; valid values remain data after rendering and parsing | No YAML/JSON structure or expression injection |
| Pinned source | Builds worktree/HEAD differs from the release tag | Output and validation use the tag's schemas/loaders/interfaces only | Missing tag or missing/ambiguous CI/perimeter schema fails before writes |
| Template error | Missing template/value or malformed rendered document | Existing output remains byte-for-byte unchanged | Nonzero contextual diagnostic, including StrictUndefined errors |
| Determinism | Same inputs, different cwd/time/module checkout state | Identical output bytes; repeat render causes no diff | Success |
| Stale output | Setup removed/renamed, Windows job removed, obsolete generated artifact present | Entire desired generated tree replaces obsolete output; no files outside `rendered/` touched | Preflight names/path collisions/symlink escapes before writes |
| Check mode | Missing, changed or extra generated artifact | Sorted mismatch paths and nonzero; clean tree returns zero | `--check` never writes/removes output |
| Policy placeholders | Any fixture setup | Three perimeter block bodies use the fixed interim text; deny values are `[]` | Valid v1 partial entries; no claim of final CAP-11 enforcement |

</intent-contract>

## Code Map

All Builds paths below are **read-only at the pinned tag**, accessed with `git show` or a temporary trusted export retaining their relative layout. `builds-version` currently contains `v5.1.0`, which peels to `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`; the submodule checkout is a later documentation revision. Do not load its mutable worktree as the renderer contract. This story implements only in the superproject, whose full planning baseline is in frontmatter.

- `setup/`, `templates/`, `rendered/`, `tools/` — absent at investigation; introduce them. No existing CiCd runtime/test harness or applicable root/ancestor `AGENTS.md` was found.
- `ARCHITECTURE-SPINE.md:112` (path in `context`) — AD-3 registry, materialization, schema validation and separate global/per-module checks; `:176` AD-5 deterministic inputs; `:259` AD-10 API/versioning; `:290` AD-11 script locks. AD-4 defines ownership, AD-12 Windows shape, AD-17 release isolation.
- `references/Hexalith.Builds/schemas/hexalith.ci.v1.json` — discover the sole `hexalith.ci.v<N>.json` at the tag, derive schema identity/defaults. `submodules` is a required current knob with default `[]`; `buildsTag` is loader-required outside Builds. `tests` needs nested defaults. The solution-none CodeQL rule is conditional.
- `references/Hexalith.Builds/Github/lib/ci_config.py:63` — `schema_identity`; `:71` `validate_config`; `:178` `load_config`. Reuse for semantic constraints with trusted `repository="Hexalith/<setup stem>"`, no sample/Builds exemption. It supplies no defaults.
- `references/Hexalith.Builds/schemas/hexalith.perimeter.v1.json`, `Github/lib/perimeter_config.py:90` and `:174` — closed nine-kind contract, `validate_config`/`load_bytes`; `Github/lib/tests/fixtures/perimeter-contract.json` first valid fixture records all owned entries.
- `references/Hexalith.Builds/Github/lib/perimeter.py:57`, `:99`, `:685`, `:721` — `Git`, `Snapshot`, `compare`, `apply`; reuse in temporary Git integration fixtures, never copy its comparison/application logic.
- `references/Hexalith.Builds/.github/workflows/ci.yml:5`, `Github/prepare/action.yml:3`, `.github/workflows/builds-ci.yml:45` — current callable signatures and working two-step Windows example. Outputs are `solution`, `submodules`, **and `global-json`**.
- `references/Hexalith.Builds/.github/workflows/release.yml:5`, `.github/workflows/builds-release.yml`, `Github/publish/action.yml:3` — concrete dispatch caller, permission union, isolated publisher and authenticated eight-field handoff. Publish already contains NuGet/login.
- `references/Hexalith.Builds/Tools/ci/check_public_api.py:29` — reuse the strict duplicate-key/GitHub-compatible YAML loading pattern; do not import the API-check orchestration. `Tools/ci/run_python_tests.py:1` demonstrates locked scripts and same-interpreter unittest subprocesses.
- `references/Hexalith.Builds/Tools/ci/lint_workflows.py:30`, `Tools/ci/tools.json`, `.github/actionlint.yaml`, `.github/zizmor.yml` — integrity-checked installer and pinned linter versions/configuration conventions. Its `run_linters` hard-codes Builds directories; it cannot directly lint arbitrary rendered paths. Reuse installation/pins, not that enumeration or legacy finding exceptions.
- `../module-inventory.md:133`, `../pipeline-stages.md`, `../enforcement.md` — central Builds package catalog, test/submodule contracts and precise forbidden ownership. All 15 earlier story specs are `done`, with complete execution checklists. Stories 2-3/2-6 settle defaults and Windows outputs; 3-1 through 3-6 settle publisher isolation and artifact recovery; 4-1 released/adopted the schema/library in v5.1.0. Earlier bootstrap blockers are closed.
- `../../../implementation-artifacts/deferred-work.md:220` — older-Git attribute-source qualification is an existing perimeter-library follow-up. Other prior runtime/adoption follow-ups (cross-repository `$/`, runner/CodeQL and timing qualification) remain with those stories; do not change their implementations here.

## Tasks & Acceptance

**Execution:**

- [x] `setup/README.md`, `rendered/.gitkeep` — document registry/setup syntax, CLI, fixture-only onboarding boundary, render-with-cause rule, Dependabot/merge decision and 10-2 transition; establish an empty real registry/output root — prevent synthetic adoption and extra configuration sources.
- [x] `tools/render.py`, `tools/render.py.lock` — implement locked CLI `--project-root PATH` (default from script location) and `--check`; enumerate/validate registry names, resolve/export pinned Builds, discover schemas, materialize missing defaults recursively and validate serialized JSON through both schema/loader APIs; strictly parse generated YAML — make the rendered document the contract. Use an explicit template map and validate the complete desired tree before output mutation; remove stale generated files in write mode, detect them without writes in check mode, preserving only the reserved `.gitkeep`.
- [x] `templates/.github/hexalith-ci.json.j2`, `templates/.github/workflows/ci.yml.j2` — render full CI configuration and thin CI caller, with sorted Windows jobs and validated CI-output inputs — keep data in the JSON and execution structure in the caller.
- [x] `templates/.github/workflows/release.yml.j2` — render dispatch-only reusable release plus environment-bound publisher at the same tag, with exact named inputs/secrets and permissions below — retain the released artifact protocol.
- [x] `templates/.github/dependabot.yml.j2` — render the fixed NuGet/no-solution policy below — give module-owned dependency changes a clear update/merge path without touching centrally owned pins.
- [x] `templates/perimeter.json.j2`, `templates/partials/ownership-block.txt.j2`, `templates/partials/deny-entries.json.j2` — emit the complete AD-4 nine-kind perimeter, whole-file references and inline partial values including the exact interim policy — allow later delivery to use the sole Builds engine without whole-file replacement of module-owned instructions/settings.
- [x] `tools/tests/test_render.py`, `tools/tests/test_render.py.lock`, `tools/tests/fixtures/render/` — add a locked PEP 723 unittest entry point and temporary fixture workspaces covering the I/O matrix through the real renderer CLI; qualify a generated render/perimeter through the tagged Git/index library — prove determinism, complete defaults, rejection and consumer compatibility. Pin the same dependency versions as the renderer; subprocesses use this interpreter. Include local Git tag/schema fixtures for failures and default evolution; do not run against live module repositories.
- [x] `tools/tests/test_render.py`, `tools/actionlint.yaml`, `tools/zizmor.yml` — add `--lint` mode that renders representative temporary fixtures and invokes pinned, integrity-checked actionlint/zizmor on their explicit workflow paths with online audits and no legacy exceptions — qualify generated callers despite an empty production registry. Keep the default test mode offline after dependency installation; a later global validator may reuse these configs/pins. Finish with render and check mode on the empty real registry and record verification in this story.

**Acceptance Criteria:**

- Given minimal and fully populated synthetic registries, when the real CLI renders each, then its generated tree contains exactly two callers, complete CI JSON and Dependabot YAML per module plus a sibling perimeter; both pinned schemas and strict loaders accept the emitted JSON, and every Builds reference uses the pin.
- Given a Windows job fixture, when the rendered caller is parsed and linted against the pinned public API, then it runs only after `ci` succeeds and has exactly tagged `prepare` with all three CI outputs followed by the literal module action, with contents read permission.
- Given a release fixture, when the rendered workflow is parsed and linted, then it has only manual dispatch and the two specified jobs, with pull credentials confined to reusable release and publish credentials/OIDC confined to `hexalith-release`; all eight handoff fields reach the sole tagged publisher step.
- Given generated expected files/perimeter and a temporary module Git repository containing owned drift and foreign instruction/settings/package content, when the tagged library applies and compares them, then the index matches the generated owned state, foreign content survives, forbidden content disappears, and a second apply changes nothing; module working-tree bytes remain untouched.
- Given solution and no-solution fixtures, when their Dependabot YAML is parsed, then the documented policy is exact, no forbidden ecosystem appears, and generated workflows contain no dependency automerge job.
- Given a clean checkout with no production registrations, when implementation validation runs, then fixture tests and explicit-path lints exercise nonempty representative renders, real render/check succeed with no module output, and no module/submodule state, live settings or release is changed.

## Spec Change Log

## Review Triage Log

### 2026-11-13 — Review pass

- verdicts: 18 findings and descriptive observations — high 0, medium 9, low 4, false 5, maybe-false 0
- findings:
  - `[medium]` `[patch]` Verification gap: publication rollback is untested — The verification reviewer removed backup restoration in an isolated copy and all 22 tests still passed. Add a staged-installation OSError regression that proves the previous tree survives. Applied: a staged-installation OSError regression verifies complete previous-file and directory restoration.
  - `[medium]` `[patch]` Edge case: numeric-leading Windows job IDs are invalid — A schema-valid 123-job setup rendered successfully; pinned actionlint rejected its generated job ID. Use a fixed alphabetic workflow-ID prefix and preserve the module action name. Applied: every Windows job ID uses the literal windows- prefix; original configuration/action paths survive. Numeric and prefix-looking names pass parsed API checks and pinned lints.
  - `[medium]` `[patch]` Edge case: interruption deletes the previous render — Injecting KeyboardInterrupt on staged-tree installation left rendered/ absent after temporary-directory cleanup. Restore the backup across the demonstrated interruption boundary. Applied: rollback now encloses both renames and restores on BaseException, with before/after backup/install interruption regressions.
  - `[false]` `[reject]` Intent audit: representative artifacts exist only in temporary fixtures — The user explicitly directs fixture setup files and postpones real registrations until onboarding; committed setup/README.md and rendered/.gitkeep match that boundary.
  - `[false]` `[reject]` Intent audit: structural compatibility does not execute hosted workflows — This invocation implements the local story component with fixture validation; live onboarding, credential execution and publication are not requested. Exact API checks, parsed callers and eight linted workflows cover the intended local consumer surface.
  - `[false]` `[reject]` Intent audit: perimeter integration uses a temporary index — Fixture tests are explicitly requested. The tagged consumer applies and compares a real temporary module Git index, verifies foreign-content preservation and leaves working-tree bytes intact.
  - `[false]` `[reject]` Intent audit: final agent policy is deferred — The user explicitly assigns the instruction and deny texts to 10-2. Exact placeholder bodies and empty deny values therefore implement the requested interim policy.
  - `[false]` `[reject]` Intent audit: renderer subprocesses use the locked test interpreter — The test entry point itself runs through its committed PEP 723 lock; subprocesses deliberately reuse that interpreter. Parent verification also directly ran the renderer through uv run --locked, as documented.
  - `[medium]` `[patch]` Blind hunter: numeric-leading Windows action names produce invalid job IDs — Independently reproduced CLI success followed by actionlint invalid-ID failure for 123-job. Same root cause and correction as the edge-case job-ID finding. Applied: every Windows job ID uses the literal windows- prefix; original configuration/action paths survive. Numeric and prefix-looking names pass parsed API checks and pinned lints.
  - `[low]` `[reject]` Blind hunter: a YAML-mapping template can omit workflow structure — Replacing the trusted CI template with {} does publish an unusable mapping. Exact parsed-caller tests and actionlint reject that source change; the committed templates pass both. A second runtime workflow validator adds policy and complexity for an unlikely everyday input, beyond a direct correction.
  - `[medium]` `[patch]` Blind hunter: nonlocal dynamic schema references escape offline validation — A temporary pinned schema with a file URI dynamicRef accepted external bytes; changing that external file changed validation, and removing it produced a traceback. Reject nonlocal dynamic references and disable external retrieval. Applied: both reference keywords reject nonlocal references; the validator registry explicitly denies external retrieval and reports contextual resolution failures.
  - `[medium]` `[patch]` Blind hunter: promisor Git reads can fetch — A local temporary promisor repository with a missing object invoked a fake remote helper through renderer.git. Disable lazy fetching and qualify the offline failure. Applied: renderer Git reads force GIT_NO_LAZY_FETCH=1; the missing-promisor-blob test verifies no helper invocation and includes a positive fetch control.
  - `[medium]` `[patch]` Blind hunter: interrupted publication removes prior output — The parent reproduced loss of rendered/ when the second rename raises KeyboardInterrupt. Same root cause as the edge-case interruption finding. Applied: rollback now encloses both renames and restores on BaseException, with before/after backup/install interruption regressions.
  - `[low]` `[reject]` Blind hunter: deeply nested shared YAML aliases expand exponentially — The parent reproduced 0.0013 seconds at 10 levels versus 0.1859 seconds at 18 levels. The harm requires a deliberately pathological local setup graph; adding alias bans or resource-budget policy is more than a direct correction and is not warranted for ordinary authoring.
  - `[medium]` `[patch]` Blind hunter: local-reference defaults are missed — The parent reproduced defaults({}) returning {} when a missing property points to a local definition containing its default. Resolve referenced defaults, preserving explicit values, and exercise an existing strict-loader knob through a synthetic tagged schema. Applied: local-reference default lookup materializes absent values and preserves explicit empty/nonempty/null values, verified through a tagged-schema fixture.
  - `[medium]` `[patch]` Blind hunter: required callable declarations are not checked in reverse — The CI/release/prepare assertions only establish supplied keys are declared; they do not require every declared required input or secret to be supplied. Add reverse required-set assertions and a negative declaration case. Applied: reverse required-input/secret assertions cover CI, release, prepare and publish, with negative newly required declaration cases.
  - `[low]` `[patch]` Blind hunter: repository names exceed GitHub limits — The parent verified registry acceptance at 101 characters. GitHub documents a maximum of 100 characters at [GitHub repository-name documentation](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository). Apply the direct length bound and boundary fixtures. Applied: repository names now have the direct 1..100 bound; both boundaries pass their expected CLI behavior and the README cites GitHub documentation.
  - `[low]` `[patch]` Blind hunter: relative examples contradict any-cwd claim — The displayed commands use tools/render.py relative to the shell cwd, so they cannot locate that script outside the repository. Label root-relative examples accurately and add an absolute-path example. Applied: relative examples are labeled repository-root commands and an absolute script-path example covers other working directories.

Nine grouped patch entries were applied: medium 7, low 2, high 0. Duplicate job-ID and interruption findings share their respective correction; the missing rollback regression remains a separate verification entry. Nothing was deferred. All four review lenses ran; the fourth launched after an agent slot became available.

### 2026-11-13 — Review pass

Follow-up pass on the done spec. All four lenses ran in parallel.

- verdicts: 44 findings — high 0, medium 2, low 31, false 11, maybe-false 0
- findings:
  - `[low]` `[patch]` Blind hunter: an uninitialized Builds directory resolves to the superproject — Reproduced: an empty `references/Hexalith.Builds` inside a Git repository reports the superproject as top level, so a fresh non-recursive clone gives `Needed a single revision` or, with a matching superproject tag, a misleading schema-count error. Applied: `git()` sets `GIT_CEILING_DIRECTORIES` to the Builds parent. A new regression test (an empty Builds directory under a tagged fixture superproject) requires `not a git repository` and unchanged output.
  - `[low]` `[reject]` Blind hunter: the local tag ref is not anchored to a recorded commit — A moved tag only matters after a deliberate local force-move of an immutable Builds release tag. Anchoring it would add a new trust policy (a commit-ancestry gate), which is more than a direct correction for that rare case.
  - `[low]` `[reject]` Blind hunter: the root `.gitignore` hides some rendered names and staging leftovers — Verified for repositories literally named `Release`, `Packages`, `Log` or `*.env`. Every current Hexalith module name renders unignored. Such names are unlikely, and the fix needs the root `.gitignore`, which is outside the intent's four authorized directories, or a second reserved generated file. Staging leftovers need a hard kill between two renames and stay visible as untracked files.
  - `[low]` `[reject]` Blind hunter: `--check` compares bytes, not file modes or HEAD — True for a manual `chmod +x` on generated files. Render writes default modes, and committing the render is the documented render-with-cause rule; the HEAD comparison belongs to the excluded global check. Mode capture adds a new comparison dimension for an unlikely edit.
  - `[low]` `[reject]` Blind hunter: callers set no `timeout-minutes` — Real but bounded: GitHub's 360-minute ceiling applies and runs can be cancelled manually, and hangs are rare. A value is new policy: Windows job duration is module-specific and the pinned schema has no timeout knob. Reusable-workflow jobs cannot set it at the caller.
  - `[low]` `[reject]` Blind hunter: generated YAML has no "generated" header — No delivery exists in this story to revert module edits. Ownership is documented in the README and enforced through the perimeter. Header wording is new owned-content policy, not a direct correction.
  - `[false]` `[reject]` Blind hunter: `dependabot.yml` is not linted and has no cooldown — `test_dependabot_exact_solution_policy` pins the exact emitted policy, and the spec cites the Dependabot options reference for every option used. No invalid configuration can pass. The lint scope is explicit workflow paths by design, and omitting cooldown is the documented policy, not a defect.
  - `[low]` `[patch]` Blind hunter: the `--lint` cache is a predictable shared `/tmp` path — The tagged installer re-verifies the archive but writes and runs the binaries inside a directory another local user could pre-create, and the audit token is in that process's environment. Applied: `lint_fixtures` uses a private `TemporaryDirectory` cache for each run. Online `--lint` passed.
  - `[low]` `[patch]` Blind hunter: the README omits Windows job IDs and where `nightly` runs — Verified: the README's own `windows-tests` example renders as `windows-windows-tests`. The tagged `release.yml` alone runs `./.github/actions/nightly`; CI runs only the two test hooks. Applied: the README states both rules.
  - `[low]` `[patch]` Blind hunter: the README omits prerequisites — No mention of an initialized Builds submodule holding the pinned tag, of `uv`, or of the Linux x86_64 and network requirements of `--lint`. Applied: a concise prerequisites paragraph (the cache location is now private and temporary).
  - `[low]` `[reject]` Blind hunter: the defaults walker handles only part of 2020-12 (boolean subschemas, missing `$defs`, non-object `properties.schema`) — The pinned v1 schema's booleans appear only as `additionalProperties`, which the walker guards with `isinstance`, and every `$ref` is a `#/` pointer. The cited failures need a different future Builds schema, and they fail loudly; a pin bump is requalified by this suite. Guarding each form adds complexity.
  - `[low]` `[reject]` Blind hunter: tag agreement is checked only for CI JSON — Every `uses` value and the gitlink tag derive from `contract.tag` in the render context. Templates are trusted committed source; the exact caller and perimeter tests reject a hard-coded tag. A second runtime reference validator has the same cost/benefit as the earlier rejected template-shape finding.
  - `[false]` `[reject]` Blind hunter: `--check` output does not classify mismatches — The README promises sorted missing, changed and extra *paths*, not labels, and the intent requires sorted mismatch paths. The CLI prints exactly those.
  - `[low]` `[reject]` Blind hunter: near-miss `*.yaml`/`*.YML` registrations are silently ignored — The intent fixes the registry as exactly `setup/*.yml`, and the test pins that. Onboarding is rare and documented, and diagnosing near-misses adds a new branch and policy.
  - `[low]` `[reject]` Blind hunter: duplicated PEP 723 dependency blocks are unguarded — `uv run --locked` already fails when a header and its own lock disagree. Drift needs a deliberate partial bump of one script only. A cross-file consistency test adds a new guard for an occasional maintenance edit.
  - `[low]` `[patch]` Blind hunter: the full CI JSON and quoted values are not asserted exactly — Verified: no test compared the full fixture's CI JSON, and the quoted fixture asserted only `solution`/`submodules`. Applied: the full CI JSON must equal the setup plus the two renderer-supplied fields. The quoted fixture adds a hook and a quoted Unicode exclusion key, and `codeql`, `hooks` and `tests` are asserted exactly.
  - `[low]` `[patch]` Blind hunter: template-error diagnostics are unchecked for partials and the perimeter — Verified `contains=None` for those subtests. Same root cause as the verification-gap diagnostic entry. Applied: the partial and perimeter cases require `Hexalith.Fixture.yml -> perimeter.json`. That diagnostic also carries the JSON pointer of the owned entry, so naming the partial file separately was not added.
  - `[low]` `[reject]` Edge case: a boolean subschema raises a contextless `TypeError` — Same root cause as the 2020-12 walker entry. The pinned schema has no boolean subschema at a walked position, and `main` reports `TypeError` without a traceback.
  - `[low]` `[reject]` Edge case: a non-object `properties.schema` raises `AttributeError` — Same root cause as the 2020-12 walker entry. It needs a Builds schema without an identity constant, which fails loudly either way.
  - `[low]` `[reject]` Edge case: array-index, percent-encoded, anchor or nested-`$id` local references — Same root cause as the 2020-12 walker entry. Every pinned reference is a plain `#/$defs/...` pointer.
  - `[low]` `[reject]` Edge case: defaults under `anyOf`/`oneOf`/`patternProperties` are skipped — The pinned schema's only `anyOf` (`solution`) declares its default at the property level, which is honored. A future schema must be requalified at its pin bump, and an unsupported-keyword guard is more than a direct correction. Same root cause as the 2020-12 walker entry.
  - `[low]` `[reject]` Edge case: nested YAML aliases expand exponentially — carried: same location and claim as the logged shared-alias row, and `json_values` still reads as described. Kept the low reject.
  - `[low]` `[reject]` Edge case: a failing rollback rename (second interrupt or concurrent render) loses the backup — Needs a second interrupt inside the rollback window, or two concurrent renders. `rendered/` is committed and deterministically regenerable. Retained-backup handling and locking add complexity for a rare case.
  - `[low]` `[reject]` Edge case: SIGTERM/SIGKILL between the two renames — The window is two adjacent renames. Recovery is a re-render or a checkout, and the stranded staging directory shows as untracked. Signal handlers plus a startup sweep are more than a direct correction.
  - `[low]` `[reject]` Edge case: file-mode drift passes `--check` — Same root cause and reasoning as the blind-hunter mode/HEAD entry.
  - `[low]` `[reject]` Edge case: Git older than 2.44 ignores `GIT_NO_LAZY_FETCH` — Needs both a partial-clone Builds checkout (this checkout has no `extensions.partialClone`) and Git older than 2.44 (2.53 here). On such Git, the existing promisor regression and its positive control would fail. A version gate adds a guard.
  - `[low]` `[patch]` Edge case: shared `/tmp` linter cache — Same root cause as the blind-hunter cache entry. Applied the same private per-run cache.
  - `[low]` `[patch]` Verification gap: replace refs are untested — Pre-verified mutation: dropping `GIT_NO_REPLACE_OBJECTS` passed all 29 tests. Applied: the tag-objects test replaces the tagged schema blob with invalid bytes and still requires a clean check and unchanged render. The mutant is now killed.
  - `[medium]` `[patch]` Verification gap: Git environment scrubbing is masked by the test runner — Pre-verified: dropping the scrub passed every test, yet `--check` broke whenever `GIT_DIR` was inherited, as under a superproject hook. Applied: the determinism test runs `--check` with `GIT_DIR`/`GIT_WORK_TREE` pointing at an unrelated repository. The mutant is now killed.
  - `[low]` `[patch]` Verification gap: `--check` output escaping is untested — Pre-verified raw-print mutation. Applied: a stale `stale\n::error::injected` output must print escaped on one line, with no line starting with `::`. The mutant is now killed.
  - `[low]` `[patch]` Verification gap: rollback of an interrupted first publish is untested — Pre-verified deletion of the no-previous-output rollback branch. Applied: `test_interrupted_first_publication_leaves_no_output` interrupts before and after install and requires no output or staging residue. The mutant is now killed.
  - `[low]` `[patch]` Verification gap: template-error tests do not check diagnostic content — Pre-verified for the `Undefined` branch and the perimeter source label. Applied: per-case expectations, including `.github/hexalith-ci.json.j2: 'missing_value' is undefined` and `Hexalith.Fixture.yml -> perimeter.json`. Both mutants are now killed.
  - `[medium]` `[reject]` Intent audit: interface conformance is checked only by tests, not at render time — After an API-changing pin bump, render and check would still pass until the suite runs. The intent excludes acceptable-release API checks and global-check orchestration, and the suite compares the callers with the tagged declarations in both directions.
  - `[false]` `[reject]` Intent audit: workflows and Dependabot are only strictly parsed at render time — The intent's explicit render-time validation is the schemas and strict loaders for CI JSON and the perimeter, which runs. Generated YAML is strictly parsed; workflow linting is fixture qualification, and global checks are excluded.
  - `[low]` `[reject]` Intent audit: invalid-setup tests assert the filename, not the key — `Contract.validate` emits `$/<pointer>: <schema message>`, and strict-YAML errors name the key, so the diagnostics do carry keys. Per-row key expectations across the 40-plus-row matrix is test policy beyond a direct correction for an unlikely regression.
  - `[false]` `[reject]` Intent audit: "missing required values without defaults" is unreachable with v1 — This is correct behavior. The tagged-schema evolution fixture exercises the failure path, as the intent's default-evolution coverage requires.
  - `[false]` `[reject]` Intent audit: the determinism test plants only an unregistered module checkout — The renderer has no read path to any module checkout: it reads only `setup/`, `templates/`, `builds-version` and Builds Git objects, whatever path is planted.
  - `[low]` `[patch]` Intent audit: the quoted `tests.integration` value is not asserted — Same root cause and correction as the blind-hunter full/quoted assertion entry.
  - `[false]` `[reject]` Intent audit: publication stages a temporary sibling directory — The temporary directory is removed on success and failure. The rollback tests require that only `rendered/` remains, which satisfies the no-lasting-change reading, and atomic replacement needs a same-filesystem sibling.
  - `[false]` `[reject]` Intent audit: the locked renderer path is not exercised by the suite — carried: same claim as the logged locked-test-interpreter row. This pass's verification also ran `uv run --locked --script tools/render.py` and `--check` directly.
  - `[false]` `[reject]` Intent audit: repository-name rules are the renderer's own policy — They implement the intent's unsafe-name and output-collision rows and GitHub's documented length limit. They add no registry source or allowlist.
  - `[false]` `[reject]` Intent audit: perimeter contents exceed the intent — The 17 entries are the AD-4 nine-kind ownership recorded in the design notes. Only the placeholder text, deny values and gitlink tag are interim by intent.
  - `[false]` `[reject]` Intent audit: pull secrets are always passed and publish permissions are fixed in the template — The tagged CI declares both pull secrets optional and uses them only when the registry is enabled. Publish credentials stay confined to `hexalith-release`, exactly as AC3 requires, so no credential is widened.
  - `[false]` `[reject]` Intent audit: a full implementation versus "halt after planning" — The phrase bounds the original planning invocation. The ready spec was later implemented under its Tasks section; this diff is that implementation.

Ten grouped patch entries were applied: medium 1, low 9, high 0. The cache, assertion and diagnostic duplicates share their entries' corrections. Nothing was deferred, and no finding routed to intent_gap or bad_spec.


## Design Notes

Generated Windows workflow job IDs use `windows-<action-name>` for every configured job. This keeps numeric-leading action names valid, prevents ID collisions, and leaves module action paths and test-exclusion targets unchanged.

Use Jinja variable delimiters such as `[[` / `]]` so literal GitHub `${{ ... }}` expressions survive; require `tojson` for every substitution, including dynamic keys and complete constructed `uses` values. Parse emitted JSON and YAML bytes strictly before publishing them, keeping the GitHub `on` key a string. Treat YAML booleans consistently with JSON/GitHub, reject duplicate/non-string keys and unsupported YAML values, and preserve explicit null for validation failure. Registry stems must be nonempty safe GitHub repository components (letters, digits, dots, underscores and hyphens, excluding `.`/`..`); reject symlinks and output-name collisions, with no fixed module allowlist. A missing setup field gets a schema default; an explicit value never gets replaced. Supply `schema` from the discovered constant, `buildsTag` from the pin, and the documented solution-sensitive CodeQL default. Do not make the schema require module-side action existence; anonymous per-module checks belong to delivery. Validate all modules before replacing output so one malformed input leaves the prior render intact. Diagnostics identify repo/path without interpreting control characters as log commands.

Output templates mirror module paths. The perimeter is the sibling `rendered/<Repo>.perimeter.json`, not an extra file delivered into the module. Normalized rendered ownership is:

- `whole-dir` `.github/workflows`; `whole` `.github/hexalith-ci.json` and `.github/dependabot.yml`.
- `gitlink` `references/Hexalith.Builds` with the exact `buildsTag`; `gitmodules-section` `.gitmodules`, `submodulePath: references/Hexalith.Builds`, canonical `https://github.com/Hexalith/Hexalith.Builds.git` URL.
- `json-superset` `.claude/settings.json`, pointer `/permissions/deny`, values from the partial template; three `marker-block` entries for `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, whose text excludes the fixed begin/end delimiters added by the library.
- `absent-glob` `.releaserc*`, `release.config.*`, `commitlint.config.*`, `.commitlintrc*`, `**/Directory.Build.rsp`, `**/bmad-testarch-ci/**`.
- `absent-json` `package.json`: root `release` and `commitlint`; `semantic-release`, `@semantic-release/*`, `@commitlint/*` in dependencies, devDependencies, optionalDependencies and peerDependencies, using component-array selectors.
- `absent-line` `.husky/commit-msg`, regex `\bcommitlint\b`. Module actions are not owned entries.

Interim policy is fully specified: `ownership-block.txt.j2` renders `CI/CD ownership instruction placeholder; replaced by story 10-2.` plus LF; each perimeter marker body uses that same text. `deny-entries.json.j2` renders `[]` plus LF; the perimeter contains an empty `values` array. Both are valid under v1. Story 10-2 replaces these two partials and re-renders with its policy change; this story neither fabricates final deny rules nor claims CAP-11 completion. Do not emit whole `AGENTS.md`/settings files or copy the old fixture's illustrative policy.

CI caller: name `CI`; push to main, pull requests to main, manual dispatch; top-level permissions `{}`. Preserve exact-source push/manual runs and allow PR cancellation using the event/ref-or-SHA concurrency pattern from tagged `builds-ci.yml`. Job `ci` calls the exact-tag reusable workflow with contents read, no test-only inputs, and explicit `registry-pull-username` / `registry-pull-password` mapped from `HEXALITH_REGISTRY_PULL_USERNAME` / `_PASSWORD`. For each Windows job use `needs: ci`, `windows-latest`, contents read, then exactly tagged `Github/prepare` with `needs.ci.outputs.solution`, `.submodules`, `.global-json`, followed by `./.github/actions/<job>`. Do not independently render a solution path into preparation.

Release caller: name `Release`; dispatch has optional string `delivered-sha` default `''`, forwarded to reusable release. Top permissions `{}`, `cache-mode: none`, concurrency group `release` with cancellation false. Job `release` uses exact-tag reusable release with contents write, actions read, security-events write and only the named pull-secret pair. Do not set Builds-only `ci-workflow` or `release-rules`. Job `publish` needs `release`, condition `needs.release.outputs.publish == 'true'`, Ubuntu, environment `hexalith-release`, contents write/actions read/id-token write. Its single tagged `Github/publish` step receives `publish`, `version`, `sha`, `last-tag`, `draft-id`, `artifact-id`, `artifact-digest`, `artifact-run`, `vars.HEXALITH_NUGET_USER`, and environment secrets `HEXALITH_REGISTRY_USERNAME` / `_PASSWORD`. No checkout, login fallback, rebuilding, cache, App key or provenance grant is added.

Dependabot decision: for `solution != none`, emit version 2 with one `nuget` update entry at directory `/`, `exclude-paths: ["references/**"]`, weekly Monday `06:00`, timezone `Etc/UTC`, open PR limit 5, and `commit-message.prefix: "build(deps)"` without an additional scope option. For `solution: none`, emit version 2 with `updates: []`. No npm, pip, Docker, Actions or git-submodule entries are enabled. Module-local NuGet versions are maintained here; the imported Builds catalog changes through Builds releases. Variable npm/Python manifests and legacy cleanup cannot be detected from the allowed inputs and do not justify a new setup knob. A module agent or the maintainer reviews and merges dependency PRs after green CI, preserving the `build(deps)` commit prefix; a deliberately releasable security fix uses `fix(deps)` under the existing release policy. No automerge mechanism or extra agent permission is introduced.

The [GitHub options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference) supports these schedule, path-exclusion and prefix options. The [Dependabot configuration parser](https://github.com/dependabot/dependabot-core/blob/main/common/lib/dependabot/config/file.rb) accepts an empty update array; hosted update execution is an onboarding qualification, not exercised by fixture rendering. The [uv script guide](https://docs.astral.sh/uv/guides/scripts/#locking-dependencies) documents adjacent script locks. These sources support syntax; the architecture/user direction determine policy.

Tests compare parsed generated workflow inputs, secrets, permissions and output references with the pinned `workflow_call`/composite declarations; actionlint alone does not establish remote API compatibility. Linter configs under `tools/` allow only documented tool-schema gaps (notably `cache-mode`), the Hexalith ref-pin/third-party hash-pin policy, and the architecture's self-repository audit setting; no frozen legacy ignore list is transferred. In `--lint` mode, install binaries using trusted tagged pins/installer, provide fixture workflow paths explicitly and a read-only GitHub token through the environment for online audits. Fail on failed/incomplete scans. Rendering/default fixture tests themselves require no network or token. Do not invoke Builds' entire repository linter or add a CiCd workflow/global-check runner in this story.

## Verification

The implementation commands below were executed on 2026-11-13; recorded results follow the original planning result.

**Commands:**

- `uv lock --script tools/render.py` and `uv lock --script tools/tests/test_render.py` — create/update both committed script locks alongside deliberate dependency changes.
- `uv run --locked --script --python 3.12 tools/tests/test_render.py` — all CLI/matrix/schema/loader/Git fixture tests pass at the Python floor.
- `uv run --locked --script --python 3.14 tools/tests/test_render.py --lint` — current-interpreter fixture tests plus pinned actionlint and online zizmor pass over all representative rendered callers; use the available runner Python if its version differs and record it.
- `uv run --locked --script tools/render.py` and `uv run --locked --script tools/render.py --check` — empty production registry succeeds; repeating leaves identical generated bytes.
- `git diff --check` and `git status --short` — no whitespace errors, implementation stays inside the four authorized directories plus this canonical story; no fixture registration, Builds change, pin change, or submodule pointer change.

## Initial Implementation Evidence

Initial implementation completed on 2026-11-13, before independent review. The real registry
remains empty, with only `setup/README.md` and `rendered/.gitkeep` at those roots.

- Added the locked renderer, seven explicit templates, setup documentation, four
  synthetic setup fixtures, locked unittest entry point and narrow linter configs.
- The renderer exports exact blobs from the locally pinned tag using Git
  `ls-tree`/`cat-file`, independently of HEAD, worktree or archive attributes. It
  materializes schema defaults, validates final CI/perimeter JSON through both
  schemas and their tagged strict readers, strictly parses YAML, and publishes
  the complete desired output only after every module validates.
- `uv lock --script tools/render.py` and
  `uv lock --script tools/tests/test_render.py` succeeded; both locks are present.
- `uv run --locked --script --python 3.12 tools/tests/test_render.py` passed all
  22 test methods on Python 3.12.13 (final sequential run: 20.035 seconds).
  The methods include invalid-input matrices, defaults and schema evolution,
  pinned source isolation, deterministic/check/stale output handling, exact
  caller/API and policy assertions, and real tagged perimeter index integration.
- `uv run --locked --script --python 3.14 tools/tests/test_render.py --lint`
  passed all 22 methods on Python 3.14.4 and all eight explicit fixture workflow
  paths with integrity-checked actionlint 1.7.12 and online zizmor 1.32.0, with no
  findings or legacy exceptions. Authentication came privately from the configured
  CiCd-agent profile; credentials were not printed or persisted.
- `uv run --locked --script tools/render.py` and
  `uv run --locked --script tools/render.py --check` succeeded on the empty real
  registry, with zero changed paths. Repeated rendering produced no output diff.
- `git diff --check` passed. `git status --short` showed only this canonical
  story and the four authorized implementation directories. No module registration,
  Builds change, `builds-version` change, submodule pointer change, live settings,
  workflow dispatch, publication, commit or push occurred.

An initial StrictUndefined diagnostic gap found by the tests was fixed before the
passing runs. A concurrent cross-version rerun recreated uv's shared script
environment; both required interpreter runs were therefore qualified sequentially.
The instruction and deny partials remain the exact authorized interim policy for
story 10-2. No implementation task remains incomplete.


## Implementation Verification Audit

Final parent verification passed on Python 3.12.13 (29 tests, 22.018 seconds) and
Python 3.14.4 (29 tests, 23.902 seconds, verbose evidence), with actionlint 1.7.12
and online zizmor 1.32.0 passing all eight representative caller paths. Both
script locks resolved unchanged. Empty production render/check and both staged
and unstaged whitespace checks passed.

Every matrix row is covered by executed, passing tests:

| Matrix row | Covering test methods (`test_` prefix) |
| --- | --- |
| Empty registry | `empty_registry_and_exact_yml_enumeration` |
| Defaults | `minimal_complete_defaults_and_exact_output_tree` |
| Partial setup | `nested_defaults_and_explicit_values_survive`, `defaults_come_from_pinned_schema_and_missing_required_fails`, `referenced_defaults_follow_tagged_schema_and_preserve_explicit_values` |
| Full configuration | `callers_match_pinned_workflow_and_composite_interfaces`, `tagged_perimeter_applies_only_index_and_preserves_foreign_content` |
| Invalid setup | `invalid_setup_matrix_does_not_mutate_output`, `strict_yaml_keys_and_values`, `bad_module_keeps_all_previous_modules_unchanged` |
| Unsafe interpolation | `invalid_setup_matrix_does_not_mutate_output`, `names_collisions_and_symlinks_fail_before_writes`, `valid_quotes_spaces_unicode_are_data` |
| Pinned source | `tag_objects_win_over_head_and_worktree`, `missing_tag_and_schemas_fail_without_writes`, `schema_validation_and_strict_loader_both_run`, `missing_promisor_blob_does_not_invoke_remote_helper`, `remote_schema_refs_are_rejected_offline`, `validator_itself_prohibits_external_retrieval` |
| Template error | `template_errors_are_atomic_and_contextual` |
| Determinism | `determinism_cwd_time_and_module_state` |
| Stale output | `check_mode_sorted_paths_and_stale_tree_replacement`, `output_and_template_symlinks_cannot_escape`, `publication_install_oserror_restores_complete_previous_tree`, `publication_interrupts_at_rename_boundaries_restore_previous_tree` |
| Check mode | `check_mode_sorted_paths_and_stale_tree_replacement`, `missing_root_and_keep_check_do_not_write` |
| Policy placeholders | `perimeter_all_nine_kinds_and_exact_interim_policy` |

## Auto Run Result

Status: done

Follow-up review pass on the completed story. The change is a fixture-qualified
setup renderer in this superproject. It reads only the registry, explicit
templates, the pin and local Git objects from the exact Builds tag. It
materializes the schema defaults and validates the final JSON through the tagged
schemas and strict readers. YAML is parsed strictly. It publishes a
deterministic, complete owned tree, with stale cleanup and a read-only check mode.

This pass independently reviewed the first pass's job-ID, referenced-default and
publication-rollback amendments together with the rest of the diff. It found no
high-severity defect. Ten grouped patch entries were applied: one code fix,
README clarifications, a private lint cache and regression tests.

Files changed in this pass:

- `tools/render.py` — Git discovery for Builds stops at its parent directory, so an uninitialized submodule fails clearly instead of resolving to the superproject.
- `tools/tests/test_render.py`
  - Private per-run linter cache.
  - New tests for an uninitialized Builds directory and for an interrupted first publication.
  - New coverage for replace refs, an inherited `GIT_DIR`, escaped check-mode paths, exact diagnostics, and the exact full and quoted CI JSON.
- `tools/tests/fixtures/render/quoted.yml` — adds a hook and a quoted Unicode exclusion key.
- `setup/README.md` — prerequisites, the `windows-<name>` job-ID rule and where `nightly` runs.
- This canonical story — the follow-up triage log and this result.

Earlier files are unchanged: the templates, both locks, linter configs, the other
fixtures, `rendered/.gitkeep`.

Review findings: 44 findings — high 0, medium 2, low 31, false 11.

Patches applied (10 entries; patched counts medium 1, low 9, high 0):

- Superproject fallthrough for an uninitialized Builds directory.
- Shared `/tmp` linter cache (blind and edge-case duplicates).
- README Windows job IDs and `nightly` placement.
- README prerequisites.
- Exact full and quoted CI JSON assertions (blind and intent duplicates).
- Replace-ref regression test.
- Inherited `GIT_DIR` regression test (medium).
- Check-mode escaping test.
- Interrupted first-publication rollback test.
- Template and perimeter diagnostic content (verification and blind duplicates).

Deferred: none. Nothing was routed to intent_gap or bad_spec.

Rejected findings and their reasons:

- Unanchored local tag: needs a deliberate force-move, and anchoring is new trust policy.
- `.gitignore` rendered names and staging leftovers: unlikely names, and the fix lies outside the authorized directories.
- `--check` ignores file modes and HEAD; the edge-case duplicate is file-mode drift: unlikely manual chmod, and HEAD comparison is the excluded global check.
- No `timeout-minutes`: bounded by GitHub's ceiling, and a value would be new module policy.
- No generated header: no delivery exists in this story, and header wording is new policy.
- Dependabot lint and cooldown (false): the exact documented policy is asserted.
- Defaults walker and 2020-12 forms, plus four edge-case duplicates: the forms do not occur in the pinned schema, fail loudly, and are requalified on a pin bump.
- Runtime tag agreement: refs come from `contract.tag`, and exact tests reject template edits.
- Unclassified `--check` output (false): the documented contract is sorted paths.
- Near-miss registry names: the intent fixes the registry as exactly `setup/*.yml`.
- Duplicated PEP 723 blocks: `--locked` already guards each script, and drift needs a partial bump.
- YAML alias expansion: carried low reject.
- Rollback-rename failure and SIGTERM/SIGKILL windows: rare, regenerable, and fixing them adds complexity.
- Git older than 2.44 with lazy fetch: needs a partial clone and old Git, and the existing promisor test would detect it.
- Render-time interface checks (medium): the intent excludes acceptable-release API checks and global-check orchestration.
- Render-time workflow/Dependabot validation (false): the intent's validation surface is met.
- Diagnostic key assertions: keys are already emitted, and per-row expectations are extra test policy.
- Unreachable required-without-default (false): correct behavior.
- Determinism planted path (false): the renderer never reads module checkouts.
- Temporary staging sibling (false): removed, and nothing lasting outside `rendered/`.
- Locked-path exercise (false): carried row, and the locked CLI was run directly.
- Repository-name rules (false): they implement the intent rows.
- Perimeter contents (false): AD-4 ownership.
- Credentials (false): optional, gated pull secrets; publish confined to `hexalith-release`.
- Invocation scope (false): the planning halt was the earlier invocation.

Every reason is also recorded in the triage log.

Follow-up review recommended: false. This is a follow-up pass and it patched no
high entry, so the work has converged. Patched counts by verdict: high 0,
medium 1, low 9.

Verification performed on 2026-11-13:

- Both `uv lock --script` commands resolved 9 packages, leaving both committed locks byte-identical.
- `uv run --locked --script --python 3.12 tools/tests/test_render.py -v` passed 31 tests on Python 3.12.13 (22.504 seconds).
- `GH_TOKEN=<private CiCd-agent gh profile token> uv run --locked --script --python 3.14 tools/tests/test_render.py --lint -v` passed 31 tests on Python 3.14.4 (24.390 seconds). Integrity-checked actionlint 1.7.12 and online zizmor 1.32.0 passed all eight explicit fixture workflow paths without findings, using the new private per-run cache. The token was not printed or persisted.
- Mutation checks ran in an isolated copy, one targeted test each. Removing the ceiling, `GIT_NO_REPLACE_OBJECTS`, the `GIT_DIR` scrub, check-mode escaping, the first-publication rollback branch, the `Undefined` diagnostic branch or the perimeter source label each made its new test fail. The copy was deleted.
- `uv run --locked --script tools/render.py` and `--check` ran twice each on the empty real registry: 0 changed paths and exit 0. The only entries are `setup/README.md` and `rendered/.gitkeep`.
- `git diff --check` passed.
- `git status --short` showed only `setup/`, `tools/` and this story.
- `builds-version` is still `v5.1.0`, and the Builds submodule pointer (`7917c50e21ec5bae15677c9ac3559623e432756e`) is unchanged.
- No module registration, live settings, dispatch, publication or push occurred.

Residual risks:

- Several rejected low-severity hardening items remain accepted trade-offs and are not tracked as deferred work:
  - process kill or a double interrupt during the rename window;
  - file-mode drift under `--check`;
  - 2020-12 schema forms absent from the v1 pin;
  - lazy fetch on Git older than 2.44 with a partial clone;
  - missing caller timeouts.
- A Builds pin bump must rerun this suite. Render-time interface checks are excluded by intent.
- The Dependabot policy has not run on GitHub. Hosted runs remain an onboarding qualification.
- Story 10-2 still owns the final instruction and deny policy, and production onboarding remains with its later story.
