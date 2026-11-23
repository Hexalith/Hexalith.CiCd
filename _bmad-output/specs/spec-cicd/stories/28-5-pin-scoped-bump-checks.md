---
title: 'Pin-scoped bump checks'
type: feature
created: '2026-11-23'
status: done
baseline_revision: aaa9388bc5a6f13522f285771aa264f5c697590c
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** The nightly Builds candidate runs all tool suites even when its only changed inputs are the Builds pin and the generated render.

**Approach:** Have the bump producer request the suites that consume the live pin. Run the same global checks and keep full validation for delivery of the bump commit.

## Boundaries & Constraints

- The approved contracts are [November 18 §4.1](../../../planning-artifacts/sprint-change-proposal-2026-11-18.md#41-stories) and the [November 19 acceptance](../../../planning-artifacts/sprint-change-proposal-2026-11-19.md#acceptance-additions), story 28-5.
- Preserve all global checks, locked suite invocations, delivery scope behavior, and the bump writer's substitution and newest-tag checks.
- Record the next eligible hosted bump's duration and suite coverage from its actual job. The proposal estimates at most six minutes. Treat hosted acceptance as pending until the implementation runs with a newer eligible tag.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected behavior |
|---|---|---|
| Full validation | Default or explicit `all` | Run every discovered suite and the relocated EventStore suite. A failing independent suite turns validation red. |
| Bump candidate | Explicit `pin` | Run the fixed list, with named suite diagnostics, in addition to all non-suite checks. Maintenance and other independent suites are outside this list. |
| Narrow delivery | Existing `none` or `module` change scope | Preserve the existing non-suite behavior. Unknown change scopes retain full validation. |
| Wrong selector or missing listed suite | Invalid selection, or an incomplete pin suite set | Fail closed. |
| Unlisted live-pin reader | Direct or helper-mediated read of the root pin | Repository tool test fails with the consuming suite and the read location. Disposable fixture pins remain valid. |

</intent-contract>

## Code Map

- `tools/check_global.py` — `run` evaluates the same globals in both modes. `run_tool_tests` owns sorted locked suite execution, its timeout, failure aggregation, and the special EventStore invocation. `main` already accepts delivery's separate `--scope`.
- `tools/bump.py` — `run_script` invokes the committed tool with an isolated interpreter after the producer creates the candidate. Pass `--suites pin` only to the candidate's global gate.
- `tools/repository_inputs.py` — reuse `PathReads` for suite dependency checks. `test_render`, `test_render_legacy` and `test_conversations_qualification` read the pin. At this baseline `test_validate` also reads the pin and shares the renderer workspace, and `test_delivery_workflow` uses that workspace from its CLI boundary driver. Keep those two suites eligible for the pin gate.
- `tools/validate.py`, `tools/change_scope.py`, `tools/bump_push.py` — existing delivery entry, shared-input classification and writer constraints. Verify behavior through their existing tests and leave them untouched.

## Tasks & Acceptance

**Execution**

- [x] `tools/check_global.py` — add an explicit `all` / `pin` selector with `all` as the default. Keep delivery scope independent and retain the relocated qualification suite on the full path.
- [x] `tools/bump.py` — request pin suites on the committed candidate and retain exit-code propagation and candidate cleanup.
- [x] `tools/repository_inputs.py` and existing tool tests — enforce the dependency boundary and cover selection, producer invocation and separate failure controls.
- [x] This story — record local verification, immutable source identities and the hosted timing outcome or pending condition.

**Acceptance Criteria**

- Given a candidate that reaches the shared gate with a rejected Builds pin, when the producer runs the pin selection, then candidate verification fails and emits no publishable artifact. Exercise the real render, schema, bootstrap and release proof checks, including tag identity, with controlled external responses and real pinned suites.
- Given a valid pin and a separately injected pin-independent suite failure, when the full validation entry runs, then it fails on that suite. The pin selection on those same inputs passes and omits that suite.
- Given a posted bump commit with a changed `builds-version`, when delivery classifies and validates its commit, then full validation still covers every suite.
- Given the completed rollout and an eligible hosted bump, when its Actions job finishes, then record the job's timestamps, duration against the six-minute estimate and suite coverage, including maintenance exclusion.

## Spec Change Log

## Review Triage Log

### 2026-11-23 — Review pass

- Verdicts: 22 findings. High 1, medium 14, low 5, false 2, maybe-false 0.
- Blind Hunter
  - `[medium] [patch]` Pin validation indirectly ran the relocated EventStore suite. Moved the missing-release case intact to the full-only App inventory suite.
  - `[low] [reject]` Nightly still sets up Node for detector integration. The approved production change names the shared selector and producer. The next hosted job measurement will include setup time.
  - `[medium] [patch]` Git object syntax hid reads of the root pin. The guard now checks those operands against the Git working directory.
  - `[medium] [patch]` Relative child paths hid reads of the root pin. The guard now resolves those operands against the child working directory.
  - `[medium] [patch]` Imported test classes could contain unflagged pin reads. The guard now follows imported test classes.
  - `[medium] [patch]` Imports could execute unscanned local package initializers. The guard now analyzes them.
  - `[medium] [patch]` Local `runpy.run_path` reads escaped dependency analysis. The guard now analyzes the identified module.
  - `[low] [reject]` The static guard assumes the suite's configured working directory for relative reads. No current suite changes the Python process cwd before opening a fixture pin. Modeling arbitrary process state would add substantial complexity.
  - `[medium] [patch]` An unknown delivery scope combined with explicit pin selection took the pin path. Unknown scopes now take the full path.
- Edge Case Hunter
  - `[medium] [patch]` A helper executed by `runpy.run_path` could read the pin. The guard follows the helper and attributes the read to the suite.
  - `[medium] [patch]` Relative subprocess arguments could reach the pin. Resolved against the child's working directory.
  - `[low] [patch]` Suffix or stem transformations could change whether the path names the root pin. The guard now applies concrete transformations.
  - `[low] [patch]` A known glob could select the pin without a finding. The guard matches repository-root patterns against the pin.
  - `[low] [reject]` An in-process cwd change could make a relative fixture file look like the live pin. The current suites use explicit fixture paths and subprocess working directories, both covered by fixtures.
  - `[medium] [patch]` The required dependency test missed a real unlisted suite using `cat`. Added a positive root case and a disposable fixture case.
- Verification Gap Reviewer
  - `[medium] [patch]` A mutation forcing full selection at the actual CLI survived the tests. The new CLI control observes a passing pin run and a failing full run on the same independent failure.
  - `[medium] [patch]` A mutation bypassing publication verification on the pin path survived the tests. The new CLI control fails on a substituted tag-object identity with its selected suites passing. The producer regression and disposable candidate exercise cover exit propagation and removal of candidate artifacts.
  - `[high] [patch]` Full validation broke the App inventory suite's assertion about the full runner call. Restored the default all-suites call and reran App inventory.
  - `[medium] [patch]` Both Git and relative child reads were missed by the dependency test. Added both forms and fixture negatives.
- Intent Alignment Auditor
  - `[false] [reject]` The expanded list could be read as a discrepancy with the proposal's inventory. Two more current suites demonstrably read the live pin, and the approved criterion selects by dependency.
  - `[false] [reject]` The disposable push is a different event from hosted explicit dispatch. The hosted dispatch uses unconditional full classification, exercised in `test_delivery_workflow.py`. Hosted timing is a separate pending acceptance item.
  - `[medium] [patch]` The subprocess example showed a real pin read missed by the guard. The child-cwd regression now covers that exact path.

## Verification

- Run the affected locked suites under `run-with-temp` and separately verify the bad-pin and independent-suite controls. Record exact relevant commit, tree and blob IDs and log digests.
- Inspect the local diff and compare writer trust-boundary blobs with the baseline. Record any live checks that could not be exercised.
- Acceptance sources are [November 18 §4.1](../../../planning-artifacts/sprint-change-proposal-2026-11-18.md#41-storiesyaml-insert-after-story-11-through-a-bmad-spec-update) and [November 19 backlog edits and acceptance](../../../planning-artifacts/sprint-change-proposal-2026-11-19.md#backlog-edits-and-acceptance).

### Local source identities

The story baseline is `aaa9388bc5a6f13522f285771aa264f5c697590c`, tree `e63ec3d8e11e110a4309f215f5ed3632f64d496d`. The synchronized local base is `9e452b04505780d5483c25461340159560ccdb7d`, tree `9d41763780dd405bd66c8c399c4c8d37c2231da8`. The two bases differ in 15 non-Builds module gitlinks. The disposable verification source is `eaf4107a3bdf84c7103748ca0fafaf0097d326f4`, tree `d2ca3063fca98d1128786282384f3334d5438601`.

| File | Verified Git blob |
|---|---|
| `tools/check_global.py` | `268249523bcb5d11ca0f2ae560e5dc3eb773f867` |
| `tools/bump.py` | `3a511e93e73478072e23718c33b011630d2f8fdd` |
| `tools/repository_inputs.py` | `7dc7866ba684d2ef9e143982be688f5cba345bc8` |
| `tools/tests/test_bump.py` | `b6cac6ad73286302f61d48f4ee51b24b1d5ec48e` |
| `tools/tests/test_repository_inputs.py` | `a201c9b0c716a7f3fd32a5c25c5c42c46295f558` |
| `tools/tests/test_validate.py` | `d852a96bdf8548affa430d8e67aabc4dd671b3ae` |

The producer and global gate lock files share blob `4481492c6c5b7b392723c31912f4767526239e4f`. The bootstrap manifest blob is `a4ce329ccd8fe3d874a040ea8cd6c95d01e34eee` and its immutable source is `03d130f82366dec8ed70a21a14177ae55ea09ca1`.

Git comparison against the story baseline and synchronized base found identical writer and delivery trust-boundary blobs.

| File | Baseline and verified Git blob |
|---|---|
| `tools/bump_push.py` | `70ed2e25cbfbcbac9f62d0d2cdb17519e13e8670` |
| `tools/bump_runtime.py` | `ae98ec297551319e772d49ededa0594670a59f23` |
| `tools/nightly_runtime.py` | `d511ef58ca843e290e33a5eb91c07fe9f7f0a1b9` |
| `.github/workflows/nightly.yml` | `03e4599a0409d86ea10733cbd2bb17ea02a68391` |
| `.github/workflows/deliver.yml` | `b6dabfb1dedf3e3c53c163d40d1f358cf5a0aa9b` |
| `tools/change_scope.py` | `5404369d5f2710fb1956528500e668a22f23cbed` |
| `tools/validate.py` | `f69476ee4b6c1f9b566bec17bdee8fd1689b1579` |

### Local verification

| Locked suite under `run-with-temp` | Result | Combined output SHA-256 |
|---|---|---|
| `test_bump.py` | 15 passed. The isolated child received `--suites pin` and failure removed the previous candidate. | `dc602e71c4d01b4d19e3c2845286e2829655490d84cd917b12f7842845444503` |
| `test_bump_push.py` | 19 passed. | `00afae57c723e8cab005e6bed9fc459c4c4d950fec3574ef05cccb2e78aba5fb` |
| `test_repository_inputs.py` | 36 passed. Direct, imported and shared helper reads identify the consuming suite and read line. Disposable fixture pins pass. | `503d6a36d5cf23b5e2c8fd834c843fd63e29c91e2359dfc6fe47ccab3d7d8359` |
| `test_validate.py -k global_suite_selection` | Passed. Pin and full selection use the locked commands. Full includes the relocated suite and rejects the injected independent failure. A missing pin suite fails closed. | `cecde7426376965b2160f8ee7f916c2635362cad4169e95bd12160ead135a636` |
| `test_validate.py -k global_cli_exit_status` | Passed. Invalid selectors exit with a parser error. Explicit and default suite modes preserve the delivery scope behavior. | `83c6ad04327d39ede8798f895c1eca505b0ca265afa2b64c660570fb5f72aad9` |
| `test_maintenance.py` | 28 passed with the original suite source. | `3ca8c03a70d4082d9d2cf25b11e5efe5cb20e08d26fe1580f6c32cdbf5db1526` |
| Relocated EventStore suite | 17 passed with the global gate's locked dependencies. | `0935cdd6341ce0a664bf7c01e5511c008ea4aa1f45abb077583b8e056220d825` |

### Rejected pin control

The fixture bumped from Builds `v6.6.1` (commit and lightweight tag object `27fe4d62ca1f3cce07a9f19e1e30b02cbaa51357`, tree `e55fefff3fa765e4a7bc9408caf61ea0a59b6dc5`) to `v6.6.2` (commit and lightweight tag object `2d9ef8b454ff897daca0149f3549844f584b634a`, tree `d610c1dd857908d8eda420c92cf8efcd5bf4b614`). The fixture's parent `703c1e51f60e7626427e863dd2b568f12ec944ce` has tree `a8ba0496c45e17557101d65a2b8008374e0a889f`, pin blob `ecb8b9a7d5cd90f97c08600ef5730590df82cdc4` and render tree `1fd6513c6e9304b1559199fd4569d85b6277a80c`. The candidate `5d45ad02afc5339767a431932fa12fc4f8bc8187` has tree `93fcb03b0c6e01006187dcb7675fffe34c8ab60f`, pin blob `6fdce8f909b5307d0159bc0fc76748328ebe5f18` and render tree `40d0d62a63313350c1903ccf0e9a555141596be1`.

The real producer's initial selection accepted the fixture metadata. The candidate's independent global proof received a substituted remote tag object and reported `remote/local tag-object mismatch`. App inventory, committed inputs and render, immutable bootstrap digests, reproducibility, schemas and caller interfaces, and all five real locked pin suites passed. The producer exited 1 and recorded a failed report. Global log SHA-256 `ec35a206deab6fc383b207f20728cc3986072ad57a96c09a9ba341c143bda8e6`. Render log SHA-256 `b4ef9b8613e6c3d2cfc8f685925910abc63499cc4a701c29478e122fc7fe4b78`.

A separate producer run with controlled suite subprocesses verified exit 1 and the absence of `candidate.json` after the same rejected tag proof. Its candidate commit `8427ec0c46c05f1bd212f527485674766acd7003` has the same tree, pin blob and render tree as the first run. Global log SHA-256 `fdf115003fda1cb45859e79a473dcd26e862d7ccd4b98b8e4ec5205932c267cd`.

### Valid pin and independent failure

The second verification source commit `0b1f1eae82b7d630af8e092d3e6472f3c8ac5b85` used the same source tree `d2ca3063fca98d1128786282384f3334d5438601`. Its disposable parent `5a15b3ed145140380071673fe7668429121f84d5` used the same parent tree and old pin as the rejected run. The fixture's maintenance failure blob is `ae57e227ee2d139e561b8706f533a57fa83e4867`. The producer emitted candidate `1e0203594012088890fb57a20dfdc71f368af27c` with the same candidate tree, pin blob and render tree as the rejected run.

The real global proof accepted the release metadata, raw tag identity, peeled commit and live-main ancestry. Rendering, bootstrap and schema checks passed. The top-level pin selection ran only the suites below and produced the candidate despite the maintenance fixture. The validator suite also emits diagnostics from its internal fixture runs. Global log SHA-256 `4c5aba885daf01012978310a91df645da29904f965f6f0f307a4f28da45e03c5`. Render log SHA-256 `b4ef9b8613e6c3d2cfc8f685925910abc63499cc4a701c29478e122fc7fe4b78`.

| Pin suite | Passed |
|---|---:|
| `test_conversations_qualification.py` | 26 |
| `test_delivery_workflow.py` | 24 |
| `test_render.py` | 52 |
| `test_render_legacy.py` | 16 |
| `test_validate.py` | 78 |

The writer fast-forwarded the disposable main to that exact candidate. The push classifier compared it with accepted baseline `5a15b3ed145140380071673fe7668429121f84d5` and returned `full`. The delivery entry invoked the global gate with its default selector. The gate dispatched all 31 discovered suites and relocated EventStore using the existing commands. The actual maintenance subprocess exited 1 and the delivery validator returned exit 1 with `global: false`. Other suite subprocess outcomes and module reads were controlled for this check. The full log assertion counted the maintenance subprocess separately from the enclosing gate's exit. Full-delivery log SHA-256 `d3f60bd7d216000ce8ea03a9a40cade6622602fbfba347598b4ee81f8dec63d9`.

### Verification after review

The tested payload tree `c50770ab1de6f815922f745b2d2e839c050910b9` includes the reviewed code and tests over `9e452b04505780d5483c25461340159560ccdb7d` before the story receipt. The producer and its regression test retain the verified blobs above.

| File updated during review | Verified Git blob |
|---|---|
| `tools/check_global.py` | `ec544117d21c59a7fc2e745f50f5583c9c92bcc2` |
| `tools/repository_inputs.py` | `bdc1b1b369f58aa28648f75c154f8577930a2024` |
| `tools/tests/test_app_inventory.py` | `c4bbad282acaf3347b5fe271c3afff3bd1fef4fe` |
| `tools/tests/test_repository_inputs.py` | `2f20760317b915c1aac075d112ac55c2973ef2e4` |
| `tools/tests/test_validate.py` | `3ae7b9e1d7f93701990f97fc471ec8504410ed90` |

The maintained CLI control verifies the three outcomes separately. An accepted pin passed in pin mode with the maintenance failure present. The same fixture failed on the real maintenance subprocess under both default full validation and an unknown change scope. A substituted tag-object identity failed the pin route while its suites passed. The relocated EventStore negative control passed in the full-only App inventory suite.

| Locked check under `run-with-temp` | Result | Combined output SHA-256 |
|---|---:|---|
| `test_bump.py` | 15 passed | `722008ea4fb654533f360014d2be8e1388cec9696114b8543563b07c25cf557a` |
| `test_bump_push.py` | 19 passed | `38655952f0edb95d74828c4d113afbd404f26fa18817842ff104351a66a8c586` |
| `test_repository_inputs.py -v` | 39 passed | `f202c7ad3459103d7725ec34536ede61cd3d1e58b9f6fc9fdeda81a92c93a503` |
| `test_validate.py -v` | 78 passed | `61c3f79982dd0d2a731aa2d5993d7eb71a02782c872ab6037199010d176a5b5c` |
| `test_app_inventory.py -v` | 20 passed | `70354b39815426b6f4c02d5135555ec051e0d974972a2d9eca4c0cdfe21fa047` |
| `test_conversations_qualification.py` | 26 passed | `ae3ea18cc338fe44b6515417781044194b2138b8a59b403ae660b5a8634e938c` |
| `test_delivery_workflow.py` | 24 passed | `3cb9a136676c652cff23e7d896924635d26ba599acb80c28e9b9ec2bc03dc16a` |
| `test_render.py` | 52 passed | `3459e88cb491ba6f93056368f6f82e49b4351113b7f621aeba9c9983a134d23f` |
| `test_render_legacy.py` | 16 passed | `bf8f1fd9a3a0567fa588ca7895ca39e302e13fc14fc556162cec7534b608289a` |
| `render.py --check` | Passed | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

### Hosted acceptance

Pending rollout and the first hosted Nightly bump with a newer eligible Builds tag. Record the run, job and attempt, UTC start and finish times, duration against the six-minute estimate, and each named suite from the job log. Confirm maintenance is absent. The local fixture uses controlled GitHub API and linter responses. Hosted online audits and timing require the actual Actions job.

## Auto Run Result

Status: done for local implementation, review, and qualification. Hosted acceptance is pending.

- `tools/check_global.py` accepts `--suites all` or `--suites pin`, logs the exact selection, and applies the shared checks. Full delivery still uses all suites.
- `tools/bump.py` requests pin mode against the committed candidate. A failed gate leaves no candidate artifact.
- `tools/repository_inputs.py` defines the five-suite allowlist and analyzes unlisted suites for repository-root pin reads. `tools/tests/test_repository_inputs.py` covers direct and helper-mediated reads plus disposable fixture paths.
- `tools/tests/test_validate.py` tests CLI selection, independent suite failure, and release proof rejection. `tools/tests/test_bump.py` tests the producer invocation and cleanup. `tools/tests/test_app_inventory.py` retains the real EventStore isolation case under full validation.

The four review layers produced 22 findings. Twelve distinct entries were patched at high 1, medium 9, and low 2. No findings were deferred. The triage log records each of the five rejections and its reason. The targeted assertions and affected suites cover each patch, so no additional source review is recommended. Actual job timing and hosted coverage require the next eligible bump.

All 289 tests in the nine post-review locked suites passed, as did `render.py --check`. The separate disposable producer and delivery runs established tag mismatch refusal and full-path failure on the independent maintenance subprocess. The maintained CLI controls repeated both failure verdicts after review.
