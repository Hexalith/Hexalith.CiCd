---
title: 'Create mode: version, audited build, marked draft'
type: feature
created: '2026-11-10'
status: ready-for-dev
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: f39f45c06b9ded0a473b96221c559e5443e41b1c
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: fa5f48734ca44ce63b55fc645f53c9c6bdccaa1c
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/references/Hexalith.Builds/docs/cicd-3-3-release-create-mode-plan.md'
warnings: [oversized]
deferred: []
---

# Create mode: version, audited build, marked draft

<intent-contract>

## Intent

**Problem:** Story 3-2 freezes release identity and runs the gates, but cannot compute a release, produce its audited artifact or create its marked draft. The enabled path still fails because publication stages are absent.

**Approach:** Extend the reusable release with create-mode version, build and trusted draft stages. Compute versions from the frozen source, upload its original versioned payload before creating a draft, and expose the validated handoff for the later publisher; a nonreleasable range ends successfully with `nothing to release`.

## Boundaries & Constraints

**Always:** Follow CAP-12/14 and AD-10/11/16/17/20. Work in `references/Hexalith.Builds`; use workflow-owned `$/` actions and trusted `GITHUB_ACTION_PATH` helpers, never executable pipeline code from the module's Builds gitlink. Reuse the single reachable-stable-tag function. Create stages use resolve's frozen SHA; CodeQL/nightly-hook retain dispatch `github.sha`. Require successful resolve, switch `true`, and successful or intentionally skipped nightly gates. Version/build get `contents: read`, no secrets, credential-free checkouts, no cache; draft gets `contents: write` and `actions: read`, and runs only trusted stdlib Python/git/API operations. Runtime logic is Python >=3.12; a thin JavaScript adapter may invoke the two pinned npm plugins. Pin actions and tools, use `npm ci --ignore-scripts` plus `npm audit signatures`, and pass expressions through `env` rather than `run` text.

The draft independently accepts exactly one major/minor/patch increment with lower components zeroed, or `1.0.0` without a reachable tag. It carries all five AD-17 trailers. Build outputs only artifact ID/digest; draft derives inventory from the authenticated artifact. Never execute product/npm/build code in the write-token job.

**Never:** Implement complete-mode artifact recovery/deletion, package/container publication, tag creation, scheduler, caller migration or the 5-1 drift check here. Complete mode remains fail-closed without building or mutating its existing draft. Preserve unmarked drafts, signed-provenance exclusion and original OCI bytes. Preserve frozen module-used legacy runtime, root legacy release configuration and the current `builds-release.yml`; new functionality goes in new files. Do not rerun tests, nightly hooks or Windows preparation in the release build.

For this invocation, deliver planning only: commit/push the Builds companion, stage the canonical CiCd story and updated Builds gitlink together, do not commit/push CiCd, and halt at `ready-for-dev` with runtime tasks unchecked.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Module rules | Reachable `v2.3.4`, range ending at frozen SHA | `feat` -> `2.4.0`; `fix`/`perf`/`fix(deps)` -> `2.3.5`; breaking releasable change -> `3.0.0` | `build`, `ci`, `build(deps)` alone yield no version |
| Builds rules | Actual Builds repository, same range | Every type except `docs`/`test`/`style` releases; ordinary changes patch, feat minor, breaking changes major | Modules cannot select Builds rules |
| No version | No releasable commit, including tagless history | Log `nothing to release`, skip build/draft, outcome `nothing`, `publish=false` | Gate failure/cancellation still wins |
| Tagless release | Releasable history with no reachable stable tag | Plugins analyze full history; first version exactly `1.0.0` | Other initial versions rejected |
| Independent draft gate | Highest reachable tag `v2.3.4` | Accept only `2.3.5`, `2.4.0`, `3.0.0` | Reject jumps (`2.3.6`), bad resets (`2.4.1`, `3.1.0`), equal/lower, prerelease, metadata, leading zeros |
| Audit | NU1900, NU1903, NU1904 or NU1905 during restore/build | Fail `vX.Y.Z blocked by a vulnerable package`; no release artifact or draft | NU1901/2 alone do not cross the vulnerability threshold; retain normal compiler/analyzer policy |
| Payload | Evaluated packable/container projects | One real-version package per selected package project and one preserved OCI archive per selected container | Discovery, duplicate identity, build/pack/graph failure blocks upload/draft |
| GitHub-only/empty payload | `solution: none`, or no publishable projects | Upload `release-manifest.json` with empty inventories inside `release`; both list trailers are empty | `none` executes no SDK/submodule commands |
| Artifact identity | This run's unexpired artifact named `release`, matching ID/API SHA-256 digest | Verify downloaded bytes and consume inventory as data | Missing, foreign, expired, wrong-name/digest or malformed artifact blocks draft |
| Retry/competition | Relisted drafts after build | Reuse same-run marked draft only when all release/artifact/inventory identities match | Any other marked draft, invalid bot marker or conflicting same-run metadata fails; unmarked drafts untouched |
| Workflow race | Frozen source workflow tree differs from freshly read `main` | Create nothing; `workflows changed on main during the release, nothing released` | API/Git uncertainty fails closed |
| Success | All gates pass; artifact and version independently verified | Create bot-authored draft for `v<version>` at full SHA with notes and five trailers; expose publisher handoff | No publication/tag/main commit; reporter relinquishes outcome to future publisher only on validated handoff |

</intent-contract>

## Code Map

Paths below are Builds-relative unless prefixed with CiCd. Three investigation agents examined runtime, build/test reuse and every SPEC companion/prior story continuity section. All nine earlier stories are `done`; no unfinished prerequisite was found.

- CiCd `ARCHITECTURE-SPINE.md:365,384` (AD-16/17), `pipeline-stages.md`, `enforcement.md` and SPEC CAP-12/14 govern version, audit, artifact/draft identity and permission separation. Prior 3-2 CodeQL/Kotlin and alert-instance uncertainties, 3-1 spike credential retirement and 2-6's unrelated Linux leading-dash issue stay outside scope. Use absolute SDK paths in this story.
- `.github/workflows/release.yml:1,133` currently has resolve/CodeQL/nightly-hook/outcome and hardcoded `publish=false`. Extend its interface and dependencies; production callers stay unchanged.
- `Github/lib/release_state.py:160,197,207,307` provides safe bare Git, `highest_reachable_stable_tag`, marked-draft validation and frozen resolve. Its AD-16 existing-draft selector accepts versions above the base; add a distinct stricter AD-17 creation check without changing selection semantics.
- `Github/lib/release_state.py:45` provides bounded authenticated GET/pagination with sanitized errors and no credential redirects. Add equivalent restricted write/download handling in the new draft helper; never import spike identity constants.
- `Github/lib/release_outcome.py:68,130` already handles `no-version`, create/complete intentional skips, failed/cancelled precedence and identity-bound publisher ownership. Wire its existing `RELEASE_NOOP_REASON` and draft outputs rather than manufacturing a new outcome state.
- `Github/lib/ci_pipeline.py:61,115,152,192,219` supplies config/preparation, direct submodules and SDK solution membership. `build_flags()` forces audit off and evaluated properties are test-specific: parameterize shared low-level discovery where necessary, preserving CI defaults. `Github/prepare/action.yml:19,55` checks out dispatch SHA and builds without audit; do not reuse its entire sequence for release build.
- `Hexalith.Build.props:15,16,33` disables pack-on-build, defaults `IsPackable=false` and exempts NU1903/4 in `WarningsNotAsErrors`. `NuGet.ci.Config` provides the trusted signed nuget.org-only source. Override audit exemptions in the new release path; do not edit these shared legacy files.
- `Tools/spikes/publish_spike.py:21,59` and `Github/lib/publish_spike.py:43,105` prove single-RID archive assembly, complete graph/digest checks and authenticated artifact handling. Preserve this evidence; generalize into new production code. `Props/ContainerProvenance.targets:4` uses legacy `EnableContainer`; the new path must honor `HexalithPublishContainer=true` independently.
- `package-lock.json:560,745` currently pins commit-analyzer `13.0.1` and release-notes-generator `14.1.1` transitively. Add an isolated trusted npm tool package rather than invoking root semantic-release core/config or reading module npm/release configuration.
- `Samples/Hexalith.Sample/src/Hexalith.Sample/Hexalith.Sample.csproj` is packable; sample tests disable packing. Add a dedicated disposable release fixture for container/audit cases rather than changing normal sample behavior.
- `Github/lib/tests/test_release_{state,outcome,adapters}.py`, `test_ci_pipeline.py:721` and `test_publish_spike.py:28` offer real Git/HTTP/composite, SDK and OCI fixtures. `Tools/ci/run_python_tests.py:20` discovers new lib tests; `Tools/ci/README.md` documents locked dual-Python, lint and committed-source API checks. Preserve behavioral testing; do not assert workflow source text.
- `docs/cicd-3-3-release-create-mode-plan.md` is this run's committed Builds execution companion. The id-keyed CiCd story remains canonical workflow state. Full baseline revisions above came directly from the two repositories; later review must include both deltas.

## Tasks & Acceptance

**Execution:**

- [ ] `Github/lib/release_version.py`, `Github/release-version/{action.yml,invoke_plugins.mjs,package.json,package-lock.json}` -- add trusted history/rule orchestration and direct calls to pinned analyzer `13.0.1`/notes generator `14.1.1`; no core lifecycle or module configuration. Use the shared tag helper, peeled annotated tags, frozen range, full tagless history, explicit module/Builds rules and stable increments. Produce version/notes/last-tag plus explicit `no-version`; isolate npm installation and disable caches.
- [ ] `Github/lib/ci_pipeline.py`, `Github/lib/release_build.py`, `Github/release-build/action.yml` -- reuse config/submodule/membership helpers while adding release-specific evaluated properties and flags. Checkout frozen source, choose its `global.json`, and evaluate `IsPackable`, `PackageId`, `IsTestProject`, `HexalithPublishContainer`, container name and platform/RID metadata in the same Release/package/version context. Build once, pack selected projects without restore/build repetition, stamp `PackageVersion`/repository commit, exclude test containers and reject conflicting identities.
- [ ] `Github/lib/release_build.py` -- audited restore/build uses `-noAutoResponse`, trusted `NuGet.ci.Config`, `UseHexalithProjectReferences=false`, `-warnaserror:NU1900;NU1903;NU1904;NU1905`, `NuGetAudit=true`, `NuGetAuditMode=all`, `NuGetAuditLevel=low`. Override inherited audit-warning exemptions so those four cannot be demoted. Preserve analyzers and ordinary warning policy, allowing low/moderate audit findings. Emit the required versioned diagnostic only for audit failures and preserve original failing status.
- [ ] `Github/lib/oci_archive.py`, `Github/lib/release_build.py` -- publish each selected container platform once through the SDK, then assemble its uncompressed `containers/*.tar` without rewriting child manifests/configs/layers or truncating colon-containing labels. Infer platforms from evaluated project metadata, never spike constants. Validate complete graph, platform and identity consistency before upload.
- [ ] `Github/lib/release_build.py`, `Github/release-build/action.yml` -- write internal `release-manifest.json` holding frozen SHA/version and package/container identity-to-relative-path lists, including empty arrays. Upload exactly one `release` artifact for 90 days containing that manifest, `packages/*.nupkg` and `containers/*.tar`; expose only upload action artifact ID/digest. Fail on unexpected/missing payloads. `solution: none` creates only the manifest without SDK work.
- [ ] `Github/lib/release_draft.py`, `Github/release-draft/action.yml` -- add the stdlib-only writer. Independently recompute reachable base and strict successor, authenticate this run's artifact ID/name/digest/expiry through GitHub, safely download/hash/read its manifest and payload identities, then relist drafts through existing marked-draft validation. Reuse an identical same-run draft; fail on competing/conflicting markers. Compare complete workflow trees at frozen SHA and freshly fetched main immediately before POST. Send notes plus exactly the five trailers below with full SHA target, stable tag and `draft=true`; validate the returned draft. Do not create a Git ref or publish.
- [ ] `.github/workflows/release.yml`, `Github/lib/release_outcome.py`, `Github/release-outcome/action.yml` -- wire guarded rules selection (`module` default; `builds` only for actual Builds, not sample context), create-only version/build and draft creation, named artifact/version handoff and all eight draft outputs. Add every job result to final reporting, route no-version to `nothing`, block publication after failures/cancellation, and retain sole-writer ownership. Complete mode skips version/build and explicitly retains the incomplete-stage failure without old-source config/build or draft mutation. Keep legacy callers unchanged.
- [ ] `Github/lib/tests/test_release_{version,build,draft,oci}.py`, existing release outcome/adapter tests and `test/fixtures/release/` -- cover every matrix edge through executed Git/HTTP/composite and real SDK fixtures; include annotated/unreachable/prerelease tags, commit-type precedence, exact successor negatives, audit codes independently, low/moderate controls, imported/multitarget properties, empty payloads, tampered inventories, byte-preserved OCI graphs and draft retry/race/error requests. Assert commands and resulting files/API effects, not YAML text.
- [ ] `.github/workflows/release-create-probe.yml`, `Tools/ci/probe_release_create.py`, `test/fixtures/release/`, `docs/cicd-3-3-release-create-mode-results.md` -- during implementation only, run a temporary manual caller through the real reusable job graph with disposable product fixtures, no publisher. Prove artifact upload precedes draft, no-version skips, audit failure suppresses draft, five persisted trailers and exact handoff outputs. Keep production callers/switch unchanged. Clean up only identified probe drafts, remove temporary caller/helper and retain sanitized run/attempt/full-revision/artifact evidence. Label deterministic API controls separately from hosted observations.
- [ ] `Tools/ci/README.md`, `docs/cicd-3-3-release-create-mode-results.md` -- document the additive public interfaces, permission union, manifest/handoff format, focused/full verification and frozen-file evidence. Commit/push runtime work only on a later implementation dispatch; stage canonical story plus pushed gitlink in CiCd.

**Acceptance Criteria:**

- Given an enabled green create run with a releasable range, when the reusable workflow finishes its create stages, then its real uploaded archive contains real-version packages/original OCI bytes and the persisted GitHub draft names the same SHA/run/artifact with all five trailers and the eight validated outputs; no tag, published release or main commit exists.
- Given no releasable commits and successful required gates, when the caller runs, then Actions skips build/draft, logs `nothing to release` and downloads one schema-valid `hexalith-release-outcome` with `outcome=nothing` and `publish=false`.
- Given a vulnerable dependency or unavailable audit, when the actual SDK restore/build encounters NU1900/3/4/5, then the run fails with the versioned diagnostic and neither `release` artifact nor draft is created; inherited NU1903/4 exemptions do not bypass it.
- Given tampered version/artifact metadata, a competing draft or a workflow-tree change on main, when the write-token stage executes, then the observed API writes create no draft; the workflow race emits the exact contract message. An identical same-run retry returns the existing draft without a duplicate.
- Given disabled publishing, failed/cancelled gates, complete mode or dispatch/main movement, when Actions evaluates dependencies, then permissions/source identities and outcomes follow the boundaries above; no forbidden build or draft creation runs, and failures never authorize the publisher.

## Spec Change Log

## Review Triage Log

## Design Notes

The stricter create-time successor test is separate from AD-16's selection of an existing draft. From `v2.3.4`, a larger version alone is insufficient: `2.3.5`, `2.4.0`, `3.0.0` are the complete accepted set. No base permits only `1.0.0`.

The internal manifest makes a GitHub-only release uploadable and binds inventory to artifact bytes rather than additional build outputs. It is data, not executable configuration or a fourth public schema. Reject unsafe paths, duplicate identities/JSON keys, mismatched SHA/version and inventory/payload disagreement. Notes cannot inject extra reserved trailer lines. Emit each reserved trailer once, with package/container identities serialized deterministically as comma-separated lists (empty suffix for an empty list):

```text
hexalith-release: <full-sha>
hexalith-release-run: <run-id>
hexalith-release-artifact: <artifact-id> <sha256-digest>
hexalith-release-packages: <package-ids>
hexalith-release-containers: <container-names>
```

Draft outputs are `publish`, `version`, `sha`, `last-tag`, `draft-id`, `artifact-id`, `artifact-digest`, `artifact-run`. Expose `publish=true` only after validated draft success and failure-first outcome reduction. This is authorization for the later caller-owned publisher; it does not report `published` or `ready`. Until the publisher/caller rewrite arrives, production remains on its existing path. Complete-mode recovery and the delivered-state check remain downstream seams, not claims of this story.

## Verification

Planning delivery: parse both documents' frontmatter, verify baselines with Git, resolve existing context links, check all runtime tasks remain unchecked and validate documentation-only diff/whitespace. Validate the exact planning commit message with pinned commitlint 21.2.4, fetch/inspect divergence, push only the Builds plan, then stage the canonical story and updated gitlink in CiCd.

Later implementation commands, from Builds:

- `python3 -m unittest discover -s Github/lib/tests -p 'test_release_*.py' -v` -- all release controls, with real SDK/plugin/HTTP effects; include production OCI helper coverage in the release test names.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and `uv run --no-cache --locked --script --python python3 Tools/ci/run_python_tests.py` -- retained suites pass on both supported interpreters.
- `python3 Tools/ci/lint_workflows.py` -- real pinned actionlint/online zizmor pass with existing read-only authentication supplied without logging credentials.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` -- additive API remains compatible; run against committed source.
- Compare frozen legacy tracked bytes against `implementation_baseline_revision`; retain hosted probe job conclusions, downloaded artifact digest/inventory and persisted draft API response. A local adapter harness does not prove Actions dependency/skip scheduling.

## Auto Run Result

Status: ready-for-dev

Halt reason: requested halt after planning. No runtime implementation or release dispatch was performed; all 10 implementation tasks remain unchecked.

Planning passed the actionable, dependency-ordered, Given/When/Then, outer-surface, completeness and coherence checks. Three investigation agents supplied code/build/contract context; all prior story continuity was incorporated. The plan explicitly includes the five release trailers and independent AD-17 one-step successor validation. The `oversized` warning records the expanded contract and code map.

Builds planning commit: `4dbf9b80ea6875c8f66a9f6cb5861f4fbba2d0a1`, pushed to `origin/main` and verified by `git ls-remote --exit-code origin refs/heads/main`. Only `docs/cicd-3-3-release-create-mode-plan.md` changed in that commit; Builds is clean and synchronized with its remote.

Validation: both frontmatters, full Git baselines, existing context/local links, unchecked tasks, all five Given/When/Then criteria, five trailers, strict successor examples, documentation-only scope and whitespace passed. The exact planning message passed pinned commitlint 21.2.4 with zero problems and zero warnings. Local verification evidence is retained at `/tmp/hexalith-cicd-3-3-planning-20261110/planning-validation.json` and `/tmp/hexalith-cicd-3-3-planning-20261110/commitlint.log`.

The canonical story and updated pushed Builds gitlink are staged together in CiCd. CiCd was not committed or pushed; its pre-existing local/remote divergence was left in place. Review on implementation must combine both repository deltas using the full baselines in frontmatter.
