---
title: 'Rewrite builds-release.yml onto the shared release'
type: refactor
created: '2026-11-11'
status: in-review
baseline_revision: 142690a268cec17275cccadc1132bb1f77eff7cd
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: aca0183fdeb4a7fcd02546ff8f082acbf73a0585
implementation_integration_revision: 6ad5854aa14a9950e1fbfc32d7e27953a1c4b82b
implementation_latest_upstream_revision: 1ecbcd6c6f61629086d019c37557d10d4247b0c3
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
---

# Rewrite builds-release.yml onto the shared release

**Current execution scope (2026-11-12):** the user re-dispatched this ready-for-dev story for implementation, commit and push in Builds, with the maintainer coordinating the AD-19 policy switch. The read-only intent contract below retains the prior planning invocation's wording; its planning-only delivery/halt instructions are historical and superseded by this dispatch as recorded in the Spec Change Log. Implement and verify the execution checklist. Production bootstrap, publication and retained-resource/settings mutation remain outside this invocation.

<intent-contract>

## Intent

**Problem:** Builds still releases through its legacy G-4 publisher and runs qualification/evidence gates alongside the shared pipeline. It must exercise the same release runtime as modules before nightly can dispatch it.

**Approach:** Replace Builds' handwritten release caller with the shared release plus caller-owned publisher. In the same implementation change, remove its legacy qualification jobs/tests, aggregator and push/PR CodeQL call, and retain the individually classified Props product checks. This invocation delivers planning only.

## Boundaries & Constraints

**Always:** Follow CAP-10/12/14/15 and AD-7/9/10/11/16/17/19/20. Work in `references/Hexalith.Builds`. Call local reusable workflows and `$/Github/publish` from the caller's revision; preserve all eight existing publisher outputs, original-artifact authentication, package-bearing stale-draft refusal, exact switch, audited single build, duplicate-safe publication, tag-last behavior and exclusive outcome ownership. Release is manual dispatch on `main` only, serialized without cancellation, with `cache-mode: none`, empty top-level permissions and explicit job grants/secrets. Builds has no setup/delivered state or `buildsTag`; no drift check is introduced for it.

Keep shared Builds/sample CI, the dependent Windows sample, quality/API checks and both Python interpreters. Keep all fifteen current catalog invocations in their current languages and preserve their SDK prerequisites. Retire qualification regression suites, while preserving executable helpers still reached by the deferred legacy release configuration. Keep frozen module-executed workflows/composites byte-for-byte unchanged, including `codeql.yml` itself. Story 5-1 owns guard commitlint and `commitlint-caller.yml` retirement. Preserve current SDK/catalog versions and root legacy npm release configuration until final AD-20 cleanup.

The maintainer coordinates the nuget.org policy change from `production` to `hexalith-release` in the rewrite window (AD-19): caller `builds-release.yml`, package scope `Hexalith.Builds*`. Before a later bootstrap, verify all AD-19 preconditions again, including the exact boolean switch and restricted environment. A retained probe draft is an explicit bootstrap stop until the maintainer records its disposition and reconciles probe-only policies/tags. Authorization failures leave settings unverified. Never infer readiness from account `admin: true`.

**Never:** Rewrite the shared release state machine, weaken caller/producer identity checks, add fallback API keys or signed provenance, grant `attestations: write`, expose push credentials/OIDC to the reusable release job, or checkout/build source in the publisher. Do not edit module repositories, introduce a Builds setup file, delete the frozen CodeQL runtime, delete runtime-coupled helpers by wildcard, or add workflow-source assertion tests. Do not mutate retained probe resources, settings, policies or credentials under this planning instruction.

For this invocation, commit and push only the Builds planning companion. Stage this canonical story with the pushed Builds gitlink in CiCd; do not commit/push CiCd. Keep implementation tasks unchecked and halt at `ready-for-dev`. No runtime edit, live probe, release dispatch or publication occurs now. The first production bootstrap is a separate operational step after the prerequisites below pass; implementation does not bypass a failed preflight to obtain a green release.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Releasable Builds main | Exact-SHA `builds-ci.yml` green; valid switch `true`; no interfering draft; security/audit pass | Shared Builds rules select version; build once; forward eight outputs to caller publisher; publish original bytes and tag last | Existing shared failures and outcomes remain authoritative |
| Commit classes | Builds `build`, `ci`, `refactor`, `revert`, `fix`, `perf`, `feat`, or breaking change | Existing Builds rules release; `docs`, `test`, `style` alone do not; no prerelease | No new caller-side version algorithm |
| Red or missing exact-source CI | No successful latest eligible push/dispatch run for the selected SHA | No publisher; `main is red, nothing released` and failed outcome | Do not substitute another SHA or an aggregator check |
| Disabled / invalid switch | Exactly `false`, or any other value including unset | False suppresses publication while current-dispatch analysis/hooks still run; invalid value fails | Preserve existing failure-first outcome reduction |
| No releasable commit | Green source, enabled switch, only excluded changes | `nothing to release`; no publisher; one `nothing` outcome | No artificial release to prove the caller |
| Interrupted product release | Valid marked draft produced by `builds-release.yml`; original artifact usable | Complete from that producer's original bytes without version/build or historical CI/config checks | Workflow change may end `ready` for AD-18 publication |
| Original artifact gone | Existing complete-mode draft has any listed package | Retain draft and fail; no rebuilt/reused version | Preserve story 3-5 conservative refusal |
| Existing probe draft | Marked draft 441591623 from `release-publish-probe.yml` still present | Stop bootstrap preflight; obtain separately authorized maintainer disposition | No deletion, second marked draft, caller-identity bypass or production dispatch |
| Settings inaccessible | Intended scoped API returns 403 | Record setting unverified and exact permission needed; stop bootstrap until verified | Do not infer absent/false or expand session credentials |
| CI simplification | Push/PR/manual Builds CI after rewrite | Retained product/shared/sample/Windows/quality/Python checks determine workflow conclusion directly | A failed retained job fails the run without an aggregator |

</intent-contract>

## Code Map

All implementation paths below are Builds-relative. Three investigation subagents read the release/runtime, CI/tests/catalog, and every prior story's Code Map, Design Notes, Spec Change Log, checklist and Auto Run Result. All twelve existing stories are `done`. Prior 3-5 findings supersede the older epic prose that permitted anonymous NuGet absence to authorize draft deletion.

- `.github/workflows/builds-release.yml:1` — renamed legacy dispatcher: source checks, `production`, `NUGET_USER`, `Github/create-release`, G-4 publication. Replace the entire caller; do not migrate those steps into shared code.
- `.github/workflows/release.yml:3,10,14,23,30,58` — existing inputs, named pull secrets, eight outputs, cache policy and union permissions. `Github/lib/release_state.py:245,251,307` restricts the Builds CI identity, admits only exact-source green CI and enforces main/switch. `Github/lib/release_version.py:29` already implements Builds rules. `release_build.py:45,114,184` supplies audited project discovery/build/pack; no new release API is needed.
- `Github/publish/action.yml:3`, `Github/lib/release_publish.py:137,146,158` — eight-field handoff, nested pinned NuGet/login, no checkout, original producer/caller authentication and sole terminal outcome. `release_complete.py:52` treats mismatching producer identity as unavailable; a package-bearing draft is retained/fails. Preserve existing release/security/outcome/OCI behavior and tests.
- `.github/workflows/builds-ci.yml:24,44,56,65,83,165,301,327,377` — aggregator; shared Builds; sample; Windows; catalog; legacy contracts; quality; Python matrix; CodeQL call respectively. Delete aggregator/contracts/CodeQL call together; no separately named G-6 job exists. Main/prerelease triggers and cancelling ref-based concurrency still carry legacy behavior: align own CI with AD-19/conventions during cleanup.
- `Tools/ci/run_python_tests.py:20,26`, `Tools/ci/tests/test_python_runner.py:26,45,55,75` — all `Tools/test-*.py` and `test_*.py` are executed; `test/qualification` is mandatory today. Removing YAML alone leaves G-6 running. Remove retired files and the empty mandatory group; preserve runner interpreter/discovery/failure-propagation controls.
- `Tools/test-archive-g4-qualification-evidence.py`, `test-prepare-g4-synthetic-acceptance.py`, `test-g6-cli-paths.py`, `test_g6_current.py`, `test-runtime-toolchain-disposition.py`, `test-runtime-toolchain-evidence-validator.py`, `test_runtime_toolchain_v2.py` and `test/qualification/test_stage3_live_qualification.py` — obsolete qualification/evidence regression suites to retire. The first seven paths are under `Tools/`.
- `Tools/test-g4-release-contract.ps1`, `test-g4-release-source.sh`, `test-g4-source-ci.ps1`, `test-g4-tool-package-contract-gate.ps1`, `test-g4-tool-package-artifact-validator.ps1`, `test-publish-g4-tool-packages.ps1` — six standalone regressions with no non-test executable caller; retire with their CI job. All paths are under `Tools/`.
- `Tools/verify-g4-tool-release.ps1:35` still invokes `test-g4-tool-package-contracts.ps1`; `build-g4-tool-packages.ps1:123` invokes `test-g4-packaged-platform-loader.ps1`; the contracts executable `:724` invokes `test-g4-packaged-seed-subscriptions.ps1`. Preserve this dormant executable dependency chain with the deferred root npm configuration. These are not claimed to be module-frozen files.
- `Hexalith.Builds.slnx:8` and `test/Hexalith.Builds.{Evidence.Tests,Module.Tests,Tooling.IntegrationTests}/` — all three .NET projects test shipped CLI/tooling products and remain under shared CI. G-4/G-6 terminology inside `RuntimePrerequisiteGateTests.cs`, `ModuleCommandApplicationTests.cs`, `QualificationOwnerBindingTests.cs` and `Live/LiveGate.cs` describes product behavior; it does not authorize deleting those tests or projects.
- `Tools/` catalog files in the classification below — each checks shipped Props/package graphs or validator behavior, rather than workflow text/story evidence. `global.json` currently selects SDK 11; Builds/sample offline fixtures also use SDK 10.0.404. Keep those pins. The shared release restores online through signed nuget.org and does not execute offline test fixtures; no source evidence establishes a release SDK blocker.
- `.github/zizmor.yml:15,16` — obsolete `builds-release.yml` hash-pinning exceptions disappear with its replacement; preserve frozen workflow exemptions and `Tools/ci/frozen-composite-findings.json`. `Tools/ci/{lint_workflows,check_public_api,run_python_tests}.py`, `package*.json`, `commitlint.config.mjs` — retained real lint, committed-Git API checking, dual-Python and commitlint 21.2.4.
- `Github/lib/tests/actions_expressions.py`, `test_release_outcome.py`, `test_release_{state,version,adapters,publish,complete}.py` — executed graph, reporter, Git/API and composite controls. Current references to caller filenames in these controls are behavioral data, not workflow text assertions. No remaining actual Builds-caller source assertion was found; audit and remove any discovered while implementing, even in frozen test directories, without deleting executed shell/adapters merely for mentioning workflows.
- `Tools/ci/README.md` — update legacy-jobs/aggregate/G-4 documentation and current caller contract. `Github/publish/README.md` remains the publishing interface reference. New `docs/cicd-3-6-builds-shared-release-results.md` records later implementation evidence; [Builds planning companion](../../../../references/Hexalith.Builds/docs/cicd-3-6-builds-shared-release-plan.md) is this invocation's Builds delivery.

## Tasks & Acceptance

**Execution:**

- [ ] `.github/workflows/builds-release.yml` — replace legacy jobs with `release` using `./.github/workflows/release.yml`, `ci-workflow: builds-ci.yml`, `release-rules: builds`, and named pull secrets. Grant `contents: write`, `actions: read`, `security-events: write` to that call. Add dependent `publish`, conditioned on `needs.release.outputs.publish == 'true'`, in `hexalith-release`, with only `contents: write`, `actions: read`, `id-token: write`. Its sole step uses `$/Github/publish`, forwards all eight outputs unchanged and passes `vars.HEXALITH_NUGET_USER` plus environment `HEXALITH_REGISTRY_USERNAME`/`PASSWORD`. Keep top-level dispatch-only trigger, `permissions: {}`, `cache-mode: none`, serialized `release` concurrency without cancellation; shared resolve enforces main. No checkout/login/build in publish.
- [ ] `.github/workflows/builds-ci.yml` — delete `build-and-test`, entire `contracts` job and `codeql.yml` call. Retain catalog, dotnet, sample, sample-windows, quality and Python matrix with their existing inputs/secrets/SDK preparation. Use push-to-main, PR-to-main and manual triggers. PR concurrency is keyed by ref and cancels; push/manual use SHA and are never cancelled, preserving exact-source CI evidence.
- [ ] `Tools/test-archive-g4-qualification-evidence.py`, `Tools/test-prepare-g4-synthetic-acceptance.py`, `Tools/test-g6-cli-paths.py`, `Tools/test_g6_current.py`, `Tools/test-runtime-toolchain-disposition.py`, `Tools/test-runtime-toolchain-evidence-validator.py`, `Tools/test_runtime_toolchain_v2.py`, `test/qualification/test_stage3_live_qualification.py`, `Tools/test-g4-release-contract.ps1`, `Tools/test-g4-release-source.sh`, `Tools/test-g4-source-ci.ps1`, `Tools/test-g4-tool-package-contract-gate.ps1`, `Tools/test-g4-tool-package-artifact-validator.ps1`, `Tools/test-publish-g4-tool-packages.ps1` — delete these fourteen standalone regressions. Preserve the three runtime-coupled `test-g4-*` helpers and their legacy callers until final deletion. Inspect affected call sites/test names; remove only obsolete references, never a frozen module-executed dependency.
- [ ] `Tools/ci/run_python_tests.py`, `Tools/ci/tests/test_python_runner.py` — remove the now-empty mandatory `test/qualification` group and its fixture expectations. Keep automatic discovery of every retained suite, selected-interpreter execution and nonzero failure propagation. Do not replace deletion with an exclusion or allow-missing switch.
- [ ] `.github/zizmor.yml` — remove only exceptions for the rewritten Builds release caller; keep unrelated frozen-runtime allowances unchanged.
- [ ] `Github/lib/tests/test_release_outcome.py` and `Tools/ci/tests/test_python_runner.py` — reuse existing expression/adapter execution and real process fixtures to verify affected handoff/reporting and runner behavior. Cover the matrix through retained behavioral controls and hosted observations; extend a test only for an uncovered changed behavior, never to assert YAML strings. Preserve all release identity/audit/security/partial-retry tests.
- [ ] `Tools/ci/README.md`, `docs/cicd-3-6-builds-shared-release-results.md`, `docs/cicd-3-6-builds-shared-release-plan.md` — document caller permissions/secrets/outputs, the complete catalog classification, retired checks, retained legacy dependency chain, and sanitized exact-source CI evidence. Record AD-19 preflight results and any inaccessible setting as unverified. Run the verification below, then commit/push Builds; stage its pushed gitlink and this canonical story in CiCd without a CiCd commit/push.

**Catalog classification:** every row is **KEEP**, in `builds-ci.yml`'s `catalog` job with its existing command/options and language. No validator implementation or catalog version change is required.

| `Tools/` file | Product checked |
| --- | --- |
| `validate-central-package-versions.ps1` | Evaluated NuGet identities/versions |
| `test-central-package-version-validator.ps1` | Catalog validator acceptance/rejection |
| `test-authoritative-package-catalog.ps1` | Required packages/authoritative family selections |
| `test-logging-generator-selection.py` | Real MSBuild logging generator selection without duplicates |
| `validate-package-version-audit.ps1` | Catalog/source/dependency-disposition agreement |
| `test-package-version-audit-generator.ps1` | Audit generator behavior |
| `test-package-version-audit-validator.ps1` | Audit validator rejection controls |
| `validate-consumer-package-authority.ps1` | Effective consumer graph obeys central catalog |
| `test-consumer-package-authority-validator.ps1` | Consumer authority validator behavior |
| `validate-package-version-exceptions.ps1` | Exceptions match catalog and evaluated SDK requirements |
| `test-package-version-exception-validator.ps1` | Exception validator behavior |
| `validate-platform-version-catalog.ps1` | Catalog/EventStore metadata hosting compatibility |
| `test-platform-version-catalog.ps1` | Platform compatibility validator behavior |
| `validate-dapr-package-versions.ps1` | Evaluated Dapr family compatibility |
| `test-dapr-package-version-validator.ps1` | Dapr identity/timeout/rejection controls |

**Acceptance Criteria:**

- Given the rewritten caller on Builds main and a permitted later dispatch, when Actions executes it, then the actual shared release uses `builds-ci.yml` and Builds rules; only its successful `publish=true` handoff admits the caller's environment-bound publisher, with original run/artifact/digest identity preserved and one terminal outcome.
- Given a failing retained product/sample/Windows/quality/Python job, when Builds CI completes, then its workflow fails directly; given all retained jobs succeed, then the exact-source push run succeeds without G-4/G-6 qualification, aggregator or push/PR CodeQL jobs/tests. PR runs may cancel by ref; push/manual source evidence is not superseded by later commits.
- Given the fifteen current catalog invocations, when migrated CI runs, then every classified product check still executes unchanged in its current language; given final tree comparison with the starting revision, then frozen module runtime, SDK/catalog data and deferred legacy release dependencies are unchanged.
- Given the current retained probe draft or an unverified AD-19 precondition, when bootstrap readiness is assessed, then the report identifies the exact stop and no production dispatch/resource mutation occurs. Given all preconditions later pass, when the first bootstrap is explicitly performed, then its exact source, original artifact, outcome and final tag are verified under AD-19; a `ready` draft follows AD-18 checks and separate maintainer publication.

## Spec Change Log

- 2026-11-12 implementation dispatch: the user explicitly invoked `bmad-build-auto` for story 3-6 and instructed: "Work in references/Hexalith.Builds; commit and push there. The maintainer switches Builds' nuget.org policy from environment production to hexalith-release in the same window (AD-19)." This latest instruction supersedes the previous invocation's planning-only scope, unchecked-task requirement and ready-for-dev halt recorded in the historical intent contract. Implement the seven execution tasks and verify them now; commit and push the implementation in Builds. The maintainer owns the policy switch. Production bootstrap remains separate; no release dispatch, publication or retained-resource/settings mutation is authorized here. Stage the resulting story and pushed Builds gitlink in CiCd without committing/pushing CiCd. The intent contract is otherwise unchanged. The implementation baseline advances from the previous planning baseline `d4f75283221fc11779416c5f2b531ea09f22582c` to the clean starting Builds HEAD `aca0183fdeb4a7fcd02546ff8f082acbf73a0585`; the superproject baseline remains its current HEAD `142690a268cec17275cccadc1132bb1f77eff7cd`.

- 2026-11-12 upstream integration: fetched eight concurrent Builds commits through `6ad5854aa14a9950e1fbfc32d7e27953a1c4b82b`, fast-forwarded the clean base, and reapplied this story. The sole modify/delete conflict was `Tools/test_g6_current.py`; the story's explicit regression retirement wins while upstream G-6 runtime/policy and all product/catalog updates remain intact. Verification restarts on this combined tree. Compare frozen/pinned preservation against the integration revision, and separately identify upstream changes since the starting baseline.

- 2026-11-12 integration repair: concurrent upstream `c48c20d0fb2e39ef53888e5061ee27c7b8410344` selected Commons `2.30.11` and PolymorphicSerializations `1.19.9` without refreshing its revision-bound audit, causing 15 deterministic audit errors at `42cfc1413927b5c55d27835a40bc07c9079f50d9`. Preserve those catalog versions. Refresh only the `hexalith-commons` and `hexalith-polymorphicserializations` audit families with the existing generator against committed declarations and real NuGet metadata, preserving all 156 other family/package rows. This derived audit repair adds `Tools/package-version-audit.json` to integration scope; no validator, SDK/catalog version, accepted-compatibility claim or legacy runtime is changed. Validate with the unchanged audit validator.

- 2026-11-12 final upstream integration: fetched and preserved `cac8bf5ca50741f9ece4f75d9633292c78f58d6c`, which already repaired those same two audit families from committed source `c48c20d0fb2e39ef53888e5061ee27c7b8410344`. Retained the valid upstream audit bytes after independently reproducing and validating the targeted refresh. Also preserved upstream consumer-validator fixes `25a6b5a613aca2ee37ebec582f69ad01a3b99e36` and `1ecbcd6c6f61629086d019c37557d10d4247b0c3`. Only affected audit/consumer validation is repeated; this story's final own diff does not modify catalog versions, audit data or validator implementation.

## Review Triage Log

## Design Notes

The caller change needs no new release controller or API: stories 3-1 through 3-5 already provide the eight-field handoff, Builds version rules, real audited pack, authenticated publisher and conservative recovery. The permission union on the calling job allows nested jobs to request their own narrower permissions; it does not give those jobs registry push credentials or OIDC. Only the separate caller publisher receives those.

Read-only preflight during planning confirmed bot draft `441591623`, `v4.47.1`, source `75e1d4a3809b30684e67c7e9b2c8043720b49c53`, producer `43010609603` (`.github/workflows/release-publish-probe.yml`, dispatch/main, success), and unexpired original artifact `13850760915`, digest `sha256:18db4ed7b07ffa3c5fd4496afce65dd50888705687d42695260e7573a7456d30`, expiry `2027-02-09T11:16:45Z`. Its listed `Hexalith.Builds.PublishProbe.20261111` package makes mismatching-caller completion fail conservatively. Do not weaken that behavior or silently delete this resource.

Before the first rewritten release, re-inventory marked drafts and every stable `v*` tag/published release. The maintainer must record authorized disposition of the probe draft/tag and probe-only policies, including the earlier `publish-spike.yml` wildcard policy and dedicated `release-publish-probe.yml` policy, and the deferred spike Zot identity/secrets. Recheck no interfering marked draft/unpublished stable tag remains. Coordinate the Builds policy/environment switch in that same window; a policy edit alone does not establish cleanup of the other identities.

Recheck App installation, exact `HEXALITH_RELEASE_PUBLISH_ENABLED` boolean, org variable/pull-secret access, `hexalith-release` main-only protection without reviewers/timer and Builds-owned push pair, Builds-scoped nuget.org policy, immutable releases, 90-day retention and AD-21 rulesets. Planning used `/home/administrator/.config/gh-cicd-agent`, no `GH_TOKEN`/`GITHUB_TOKEN` override, account `jpiquot`, target `Hexalith/Hexalith.Builds`. `gh api repos/Hexalith/Hexalith.Builds/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED` returned HTTP 403, `Resource not accessible by personal access token`; advertised permission: `actions_variables=read`. This setting is **unverified**, not absent. Maintainer confirmation or a properly authorized read is required before bootstrap; no new token or administrative change is requested by this plan.

## Verification

Planning verification: both repositories began clean on `main`; writable Git metadata refresh passed; Builds `HEAD` equalled fetched `origin/main`. Validate this document's frontmatter/unchecked tasks, exact message with pinned commitlint, whitespace and docs-only diff; commit/push the Builds companion and verify remote reachability. No runtime tests are required for the planning-only artifact.

Later implementation, from Builds root with the prerequisites in `Tools/ci/README.md`:

- `python3 Tools/ci/lint_workflows.py` — real actionlint/zizmor with authenticated online audits; no new exceptions for rewritten callers.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and the same command with `--python "$RUNNER_PYTHON"` captured before interpreter setup — every retained group passes on both interpreters; obsolete qualification suites are absent.
- `python3 -m unittest discover -s Tools/ci/tests -p test_python_runner.py -v` under Python >=3.12 — discovery/interpreter/failure controls pass.
- Execute each retained catalog command exactly as in `builds-ci.yml`, including its arguments — all fifteen pass; no substitute XML/text-only check.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` after committing implementation — current committed Git surface passes against the last reachable stable tag. Inspect both repository deltas from their full recorded baselines; frozen runtime remains byte-identical.
- Observe the exact-source hosted **push** `builds-ci.yml` conclusion/jobs, sample Linux/Windows outputs and no push/PR CodeQL; record full source/run identities in results. Exercise caller graph/handoff through the existing executable expression/adapter controls. Do not dispatch production solely for verification while the documented bootstrap stop is active, change the live switch to manufacture a branch, or claim prior invalid-switch probes proved a positive handoff. A later authorized bootstrap must record actual package/artifact/tag/outcome observations; local controls alone do not establish live publication.

## Auto Run Result

Status: ready-for-dev

Halted after planning as requested. Three investigation subagents completed; the parent re-read the rendered workflow and this story and verified the Ready for Development criteria. Seven implementation tasks remain unchecked. The plan includes AD-19 policy coordination, all fifteen KEEP catalog verdicts, fourteen retired standalone regressions, preserved product tests/runtime dependencies, and the retained-draft/settings bootstrap stops. No runtime implementation, live probe, release dispatch, settings change or publication was performed.

Builds planning companion committed and pushed to `origin/main` at `aca0183fdeb4a7fcd02546ff8f082acbf73a0585`. `git ls-remote` confirmed that full revision on `refs/heads/main`; Builds is clean and synchronized. The committed Builds diff contains only `docs/cicd-3-6-builds-shared-release-plan.md`. This canonical story and the pushed gitlink are staged together in CiCd without a CiCd commit/push.

Planning checks passed: parseable frontmatter, correct full repository baselines, unique story path, unchecked tasks, no placeholders, local links, UTF-8/LF and staged whitespace checks. Exact message `docs(cicd): plan Builds shared release caller migration` passed the owning repository's pinned commitlint 21.2.4 with zero problems/warnings; successful output is retained at `/tmp/cicd-3-6-commitlint.log`. Runtime tests and hosted publication verification remain for implementation/rollout; no CI-green claim is made for this planning-only delivery.
