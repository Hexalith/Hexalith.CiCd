---
title: 'Create mode: version, audited build, marked draft'
type: feature
created: '2026-11-10'
status: done
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 98d1f96a2b9c7dc1badf6e0e9b6e37f493216591
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 4dbf9b80ea6875c8f66a9f6cb5861f4fbba2d0a1
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/references/Hexalith.Builds/docs/cicd-3-3-release-create-mode-plan.md'
warnings: [oversized]
deferred:
  - summary: >-
      Module-owned NuGet audit waivers (Directory.Build.targets NoWarn and PackageReference NoWarn metadata) let NU1903 pass the create-mode release build.
    evidence: |-
      Real SDK 10.0.403 reproduction through release_build.build_release with the release flags and Newtonsoft.Json 9.0.1 (GHSA-5crp-9r3c-p9vr):
      `<NoWarn>$(NoWarn);NU1903</NoWarn>` in a module Directory.Build.targets, or `<PackageReference Include="Newtonsoft.Json" NoWarn="NU1903" />`, builds and packs with no "blocked by a vulnerable package" diagnostic.
      release.targets is imported through CustomAfterMicrosoftCommonTargets, before Directory.Build.targets, and rewrites only the NoWarn/WarningsNotAsErrors properties, not item metadata.
      Inherited Builds props exemptions (Hexalith.Build.props WarningsNotAsErrors NU1903;NU1904) and props-level module NoWarn are still blocked, for single-target and multi-target projects with TreatWarningsAsErrors true or unset.
      SPEC.md:120, enforcement.md and AD-8 assign rejection of module-file audit waivers (NoWarn under any parent or attribute, NuGetAuditSuppress, MSBuildWarningsAsMessages) to the guard audit lint, story 5-2 "Guard lints and commitlint", which is not yet implemented.
      NuGetAuditSuppress in Builds Props/ is the sanctioned waiver mechanism (AD-10) and must keep working.
      No production caller uses the reusable release yet. Until 5-2 lands, or module migration deletes module waivers, create mode alone does not reject these module-file channels.
      Settle by verifying that the 5-2 lint rejects both forms before any caller migration.
    location: >-
      references/Hexalith.Builds/Github/release-build/release.targets:5-8
    severity: high
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

- [x] `Github/lib/release_version.py`, `Github/release-version/{action.yml,invoke_plugins.mjs,package.json,package-lock.json}` -- add trusted history/rule orchestration and direct calls to pinned analyzer `13.0.1`/notes generator `14.1.1`; no core lifecycle or module configuration. Use the shared tag helper, peeled annotated tags, frozen range, full tagless history, explicit module/Builds rules and stable increments. Produce version/notes/last-tag plus explicit `no-version`; isolate npm installation and disable caches.
- [x] `Github/lib/ci_pipeline.py`, `Github/lib/release_build.py`, `Github/release-build/action.yml` -- reuse config/submodule/membership helpers while adding release-specific evaluated properties and flags. Checkout frozen source, choose its `global.json`, and evaluate `IsPackable`, `PackageId`, `IsTestProject`, `HexalithPublishContainer`, container name and platform/RID metadata in the same Release/package/version context. Build once, pack selected projects without restore/build repetition, stamp `PackageVersion`/repository commit, exclude test containers and reject conflicting identities.
- [x] `Github/lib/release_build.py` -- audited restore/build uses `-noAutoResponse`, trusted `NuGet.ci.Config`, `UseHexalithProjectReferences=false`, `-warnaserror:NU1900;NU1903;NU1904;NU1905`, `NuGetAudit=true`, `NuGetAuditMode=all`, `NuGetAuditLevel=low`. Override inherited audit-warning exemptions so those four cannot be demoted. Preserve analyzers and ordinary warning policy, allowing low/moderate audit findings. Emit the required versioned diagnostic only for audit failures and preserve original failing status.
- [x] `Github/lib/oci_archive.py`, `Github/lib/release_build.py` -- publish each selected container platform once through the SDK, then assemble its uncompressed `containers/*.tar` without rewriting child manifests/configs/layers or truncating colon-containing labels. Infer platforms from evaluated project metadata, never spike constants. Validate complete graph, platform and identity consistency before upload.
- [x] `Github/lib/release_build.py`, `Github/release-build/action.yml` -- write internal `release-manifest.json` holding frozen SHA/version and package/container identity-to-relative-path lists, including empty arrays. Upload exactly one `release` artifact for 90 days containing that manifest, `packages/*.nupkg` and `containers/*.tar`; expose only upload action artifact ID/digest. Fail on unexpected/missing payloads. `solution: none` creates only the manifest without SDK work.
- [x] `Github/lib/release_draft.py`, `Github/release-draft/action.yml` -- add the stdlib-only writer. Independently recompute reachable base and strict successor, authenticate this run's artifact ID/name/digest/expiry through GitHub, safely download/hash/read its manifest and payload identities, then relist drafts through existing marked-draft validation. Reuse an identical same-run draft; fail on competing/conflicting markers. Compare complete workflow trees at frozen SHA and freshly fetched main immediately before POST. Send notes plus exactly the five trailers below with full SHA target, stable tag and `draft=true`; validate the returned draft. Do not create a Git ref or publish.
- [x] `.github/workflows/release.yml`, `Github/lib/release_outcome.py`, `Github/release-outcome/action.yml` -- wire guarded rules selection (`module` default; `builds` only for actual Builds, not sample context), create-only version/build and draft creation, named artifact/version handoff and all eight draft outputs. Add every job result to final reporting, route no-version to `nothing`, block publication after failures/cancellation, and retain sole-writer ownership. Complete mode skips version/build and explicitly retains the incomplete-stage failure without old-source config/build or draft mutation. Keep legacy callers unchanged.
- [x] `Github/lib/tests/test_release_{version,build,draft,oci}.py`, existing release outcome/adapter tests and `test/fixtures/release/` -- cover every matrix edge through executed Git/HTTP/composite and real SDK fixtures; include annotated/unreachable/prerelease tags, commit-type precedence, exact successor negatives, audit codes independently, low/moderate controls, imported/multitarget properties, empty payloads, tampered inventories, byte-preserved OCI graphs and draft retry/race/error requests. Assert commands and resulting files/API effects, not YAML text.
- [x] `.github/workflows/release-create-probe.yml`, `Tools/ci/probe_release_create.py`, `test/fixtures/release/`, `docs/cicd-3-3-release-create-mode-results.md` -- during implementation only, run a temporary manual caller through the real reusable job graph with disposable product fixtures, no publisher. Prove artifact upload precedes draft, no-version skips, audit failure suppresses draft, five persisted trailers and exact handoff outputs. Keep production callers/switch unchanged. Clean up only identified probe drafts, remove temporary caller/helper and retain sanitized run/attempt/full-revision/artifact evidence. Label deterministic API controls separately from hosted observations.
- [x] `Tools/ci/README.md`, `docs/cicd-3-3-release-create-mode-results.md` -- document the additive public interfaces, permission union, manifest/handoff format, focused/full verification and frozen-file evidence. Commit/push runtime work only on a later implementation dispatch; stage canonical story plus pushed gitlink in CiCd.

**Acceptance Criteria:**

- Given an enabled green create run with a releasable range, when the reusable workflow finishes its create stages, then its real uploaded archive contains real-version packages/original OCI bytes and the persisted GitHub draft names the same SHA/run/artifact with all five trailers and the eight validated outputs; no tag, published release or main commit exists.
- Given no releasable commits and successful required gates, when the caller runs, then Actions skips build/draft, logs `nothing to release` and downloads one schema-valid `hexalith-release-outcome` with `outcome=nothing` and `publish=false`.
- Given a vulnerable dependency or unavailable audit, when the actual SDK restore/build encounters NU1900/3/4/5, then the run fails with the versioned diagnostic and neither `release` artifact nor draft is created; inherited NU1903/4 exemptions do not bypass it.
- Given tampered version/artifact metadata, a competing draft or a workflow-tree change on main, when the write-token stage executes, then the observed API writes create no draft; the workflow race emits the exact contract message. An identical same-run retry returns the existing draft without a duplicate.
- Given disabled publishing, failed/cancelled gates, complete mode or dispatch/main movement, when Actions evaluates dependencies, then permissions/source identities and outcomes follow the boundaries above; no forbidden build or draft creation runs, and failures never authorize the publisher.

## Spec Change Log

- 2026-11-10 implementation redispatch: the current user request authorizes runtime implementation, verification, and commit/push in Builds. References to "this invocation" and planning-only delivery describe the completed earlier planning invocation recorded below; that invocation has ended. Execute the unchecked runtime tasks on this dispatch. Preserve the intent-contract text, keep the canonical CiCd story and updated Builds pointer staged together, and do not commit/push CiCd. Baselines refreshed directly from current full repository HEADs before implementation.


- Concurrent delivery observed during implementation: an external `/pushall` merged lifecycle work at `9f238f42fdb4fe0da40945663b92d9561a8acfd7` (other parent `4ce510b2b263f8e4ea469638a130f08776ba27a3`) and committed/pushed the then-present partial story implementation at `79eeccfd2f9482bb1f17729f880f03c25a1da2b3`. The original baselines remain recorded above. Preserve this history and unrelated lifecycle changes; frozen-file comparisons distinguish those external changes from this story.

- Concurrent implementation commit: a separate Cursor session committed/pushed the remaining source at `4dd100c62ee8d5dd2952cfaa5c2516245d5e1c1c` while parent verification ran. No source was discarded. Parent verification observes that full implementation.

## Review Triage Log

### 2026-11-11 — Review pass
- verdicts: 15 findings — high 2, medium 11, low 2, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` Verification-gap: fresh-main ancestry lacks force-push coverage — the existing race fixtures retain ancestry, and deleting the guard leaves all 24 draft tests green. Add a real final-fetch rewrite to unrelated history with identical workflows; patch applied.
  - `[medium]` `[patch]` Verification-gap: generated notes lack downstream body coverage — creation/HTTP/composite tests validate markers and outputs but deleting the notes prefix leaves all 24 draft tests green. Add HTTP read-back of multiline notes and trailer boundary; patch applied.
  - `[high]` `[patch]` Edge: comma audit exemptions bypass the required threshold — the filter recognizes semicolons only; actual Newtonsoft.Json 9.0.1 restore with comma NoWarn returns zero without NU1903. Handle both NuGet separators; patch applied. Shared root cause with blind finding 1.
  - `[medium]` `[patch]` Edge: inferred/container-specific RID assets are not restored — discovery selects them, solution restore omits them, and no-restore publication requires them. Include selected RIDs in the single audited restore; patch applied. Shared root cause with blind finding 2.
  - `[medium]` `[patch]` Edge: effective SDK container repository is not computed — discovery validates raw AssemblyName while ComputeContainerConfig normalizes Release.Container to release-container. Evaluate effective SDK metadata; patch applied. Shared root cause with blind finding 3.
  - `[high]` `[patch]` Blind 1: comma audit exemptions permit vulnerable payloads — independently reproduced successful signed restore of Newtonsoft.Json 9.0.1 with NoWarn=NU1903,NU1904. Correct the existing exemption filter and add comma controls; patch applied.
  - `[medium]` `[patch]` Blind 2: default/container-only RIDs fail NETSDK1047 — the current restore lacks inferred assets while publication explicitly uses each selected RID with no restore. Correct restore inputs and cover default publication; patch applied.
  - `[medium]` `[patch]` Blind 3: omitted ContainerRepository fails normal SDK defaults — actual SDK ComputeContainerConfig returns a valid normalized repository that current raw validation rejects. Query the SDK's effective identity; patch applied.
  - `[medium]` `[patch]` Blind 4: plural RIDs override explicit singular selections — the installed SDK's ComputeContainerBaseImage/_ContainerEstablishRIDNess select singular when present, while runtime_ids chooses plural first. Match SDK precedence; patch applied.
  - `[low]` `[patch]` Blind 5: internal archive filenames collide — distinct allowed a/b_c and a_b/c both become a_b_c.tar. A direct filename-encoding correction preserves the existing manifest interface; patch applied.
  - `[medium]` `[patch]` Blind 6: descriptor platform metadata is discarded — a real combine call with an os.features-bearing descriptor drops that field. Preserve validated platform metadata with original child bytes; patch applied.
  - `[medium]` `[patch]` Blind 7: UTF-16 XML bypasses declaration rejection — independently accepted a UTF-16 nuspec with a DOCTYPE/internal entity through package_identity. Use encoding-aware declaration rejection; patch applied.
  - `[low]` `[patch]` Blind 8: one-property evaluation fails the new helper option — a real properties=(PackageId,) SDK call returns a scalar and raises invalid discovery metadata. A direct scalar-result correction preserves existing multi-property callers; patch applied.
  - `[medium]` `[patch]` Blind 9: mandatory descriptor types are not validated — independently rehashed a valid graph with missing config/layer mediaType fields and inspection still succeeded. Validate supported mandatory descriptor types; patch applied.
  - `[medium]` `[patch]` Blind 10: tar extended metadata precedes member limits — stdlib TarInfo._proc_pax reads the extended payload before a yielded member reaches the current checks. Bound PAX/GNU metadata before allocation and cumulatively; patch applied.

The intent-alignment layer reported no semantic divergence for the story-scoped reading. Its four descriptive contrasts are retained as context, not defect findings: AD-17 creation remains distinct from AD-16 selection; production activation belongs to caller migration; hosted switch/no-version inputs are labelled controls with local real computation; hosted source predates restored cleanup. None requires changing the captured intent or this build's spec.

All findings were individually verified before grouping. The 15 rows form 12 patch entries: one high, nine medium and two low; the three edge findings duplicate the corresponding blind root causes. No intent gap, bad-spec loopback, deferral, or rejected defect finding was found. All patches remain within existing interfaces and demonstrated states. The same implementation agent applied all 12 fixes and narrow regressions. Parent re-verification passes all 137 focused release tests; the full two-interpreter suite and hardened hosted probe are in progress.

### 2026-11-11 — Review pass
- verdicts: 33 findings — high 3, medium 3, low 20, false 6, maybe-false 1
- findings:
  - `[false]` `[reject]` Blind 1: release.targets runs after NoWarn is copied into MSBuildWarningsAsMessages, so inherited NoWarn NU1903 still hides the warning — refuted at the release surface. A real-SDK `build_release` with a single-target project, TreatWarningsAsErrors unset and props-level NoWarn/WarningsNotAsErrors NU1903 still fails the solution restore with NU1903 and the versioned diagnostic. A module setting MSBuildWarningsAsMessages directly is a module-file waiver; see the deferred Blind 3 group.
  - `[false]` `[reject]` Blind 2: tests and hosted runs cover only the multi-target TreatWarningsAsErrors=true setup where the bypass is hidden — the premised bypass does not occur. Real-SDK single-target controls, with TreatWarningsAsErrors true and unset and with NoWarn and WarningsNotAsErrors-only exemptions, all block NU1903.
  - `[high]` `[defer]` Blind 3: NuGetAuditSuppress items and PackageReference NoWarn metadata bypass the audit — PackageReference `NoWarn="NU1903"` reproduced: Newtonsoft.Json 9.0.1 builds with no diagnostic. NuGetAuditSuppress is the sanctioned waiver, kept only in Builds `Props/` (AD-10). SPEC.md:120, enforcement.md and story 5-2 assign rejection of module-file waivers to the guard audit lint, not to this story. Deferred with Edge 14 and Verification 5.
  - `[low]` `[reject]` Blind 4: a commit whose notes start a line with a reserved marker blocks create mode — real, but it needs a deliberately reserved-marker commit line. Failing closed is the designed "notes cannot inject trailers" protection. Escaping notes adds sanitization logic.
  - `[low]` `[reject]` Blind 5: unbounded release notes block a large first release — every released module and Builds already carry reachable stable tags (3–224 each), so full-history notes are not reached. Nightly ranges stay far below 120,000 characters. Truncation or a file handoff adds new logic. Grouped with Edge 2 and Edge 3.
  - `[low]` `[reject]` Blind 6: no check that tag v<version> does not already exist — AD-17's publish composite checks "no tag v<version> exists or it points at sha" before any write and verifies the tag after publication. A stray unreachable next-version tag can strand a draft but cannot publish it. The guard is unlikely to matter and adds a check. Grouped with Edge 1.
  - `[low]` `[reject]` Blind 7: module rules drop breaking changes on non-releasing types — matches AD-10's closed module list (feat/fix/perf release) and the intent's "breaking releasable change". Changing it changes the specified policy.
  - `[low]` `[reject]` Blind 8: Builds-rule releases triggered only by ci/refactor/chore get header-only notes — the pinned notes generator's default writer behaves this way. No current caller uses builds rules (Builds still releases through legacy builds-release.yml). Listing those types needs a new preset dependency or writer configuration.
  - `[low]` `[reject]` Blind 9: malformed OCI root/annotations raise AttributeError instead of a clean error — the archive is this run's own SDK output with a verified digest, the job still fails closed, and the fix adds guards. Grouped with Edge 12.
  - `[low]` `[patch]` Blind 10: results document is stale (122 tests, "recorded below after those checks finish", non-retained /tmp logs) — patch applied: the 122 count is labelled pre-hardening, the forward-looking sentence is corrected, and the local logs are stated as not retained.
  - `[low]` `[patch]` Blind 11: README manifest example shows `containers/image-name.tar` — the collision fix writes `containers/container-<n>.tar`. Patch applied: the example and naming rule are corrected.
  - `[low]` `[reject]` Blind 12: Node runtime pinned only to major 24 — matches the existing Builds actions and `engines: >=24`; plugin code is lockfile-pinned and signature-audited. An exact Node release cannot be verified locally (local Node 26) without a hosted run.
  - `[false]` `[reject]` Blind 13: concurrent same-SHA runs can both create a draft — AD conventions declare concurrency only in top-level callers, with `release` per repository, so two create runs never overlap. Duplicates would still fail closed at the next resolve. Grouped with Edge 8.
  - `[low]` `[reject]` Edge 1: an existing unreachable v<version> tag binds the draft to a foreign commit — same root cause and disposition as Blind 6.
  - `[low]` `[reject]` Edge 2: tagless first release notes above 120,000 characters — same root cause and disposition as Blind 5.
  - `[low]` `[reject]` Edge 3: notes above ~128 KiB in RELEASE_NEEDS/RELEASE_NOTES cause E2BIG and no outcome document — same unbounded-notes root cause as Blind 5. The trigger already exceeds the draft body limit and is not reached by any current module.
  - `[low]` `[patch]` Edge 4: a non-UTF-8 commit message aborts version computation — reproduced with a raw-byte commit object; current Git re-encodes, but older tooling did not. Patch applied: commit text decodes with replacement, and a regression writes a raw legacy commit and fails without the fix.
  - `[low]` `[reject]` Edge 5: a 100-release page above MAX_JSON 4 MiB fails draft but not resolve — Hexalith release bodies are small, so 100 average bodies stay far under 4 MiB. The bound is a deliberate memory limit that fails loudly.
  - `[low]` `[patch]` Edge 6: a nested `.nuspec` content file passes build but fails draft — confirmed: build selects root nuspec only, draft counted every `.nuspec`. Patch applied: draft uses the same root-only selection; a regression accepts nested content and rejects a second root nuspec.
  - `[low]` `[reject]` Edge 7: outer and inner cross-targeting IsPackable/PackageId may differ — requires TFM-conditional package identity. Comparing the outer evaluation is not a direct correction, because test metadata legitimately differs between outer and inner evaluations.
  - `[false]` `[reject]` Edge 8: concurrent create runs race between relist and POST — same refutation as Blind 13.
  - `[maybe-false]` `[reject]` Edge 9: "re-run all jobs" after an upload may conflict on the `release` artifact name — not verifiable locally. If true it is low: "re-run failed jobs" reuses the uploaded artifact, and a new dispatch always works. Settled by a hosted re-run-all after a failed draft.
  - `[low]` `[reject]` Edge 10: RestoreLockedMode plus added RIDs fails NU1004 — no Hexalith module uses lock files (RestorePackagesWithLockFile/RestoreLockedMode or packages.lock.json). The failure is loud, and the fix adds branching.
  - `[low]` `[patch]` Edge 11: limited_read reports an oversized Content-Length as an invalid length — confirmed: ReleaseError subclasses ValueError and was caught by the parse handler. Patch applied: size checks run outside the parse handler; a regression covers oversized, negative and unparsable lengths.
  - `[low]` `[reject]` Edge 12: AttributeError on a non-object OCI root or annotations — same root cause and disposition as Blind 9.
  - `[false]` `[reject]` Edge 13: MSBuildWarningsAsMessages copy defeats release.targets for single-target inherited NoWarn — same refutation as Blind 1.
  - `[high]` `[defer]` Edge 14: Directory.Build.targets NoWarn, PackageReference NoWarn and NuGetAuditSuppress bypass the audit — reproduced for Directory.Build.targets (imported after release.targets) and per-package NoWarn. These are module-file waivers assigned to the 5-2 guard audit lint; same group as Blind 3.
  - `[false]` `[reject]` Edge 15: "re-run all jobs" after a draft exists selects complete mode and fails — the intent requires complete mode to stay fail-closed in this story. The same-run reuse contract is met by "re-run failed jobs" of the draft job.
  - `[medium]` `[patch]` Verification 1: the build payload format is never checked by the draft parser — patch applied: real SDK package and dual-platform container payloads are stored-zipped like the upload and read through `release_draft.artifact_inventory`.
  - `[medium]` `[patch]` Verification 2: release.yml job wiring and reporter inputs are not executed by any test — patch applied. A shared test-only expression evaluator runs the real workflow `if:`, `with:`, job-output, reporter `env:`, upload and workflow-output expressions for no-version, handoff, build failure, disabled, complete-mode and CodeQL-failure states, then runs the real reporter. Mutations of the release-rules, version, no-op and notes mappings each fail it.
  - `[medium]` `[patch]` Verification 3: composite tests preset RELEASE_* and never check the input-to-env mapping — patch applied: version, build and draft composites now run through their declared inputs, step env, `if:`, external-action `with:` and output expressions (default and builds rules, multiline notes, upload name/path/retention).
  - `[low]` `[patch]` Verification 4: no test rejects a multi-target container project — patch applied: a real-SDK subtest asserts "container requires one evaluated target framework".
  - `[high]` `[defer]` Verification 5: Directory.Build.targets and PackageReference NoWarn exemptions pass the release audit — independently reproduced; same group as Blind 3.

The intent-alignment layer found the diff implements the story-scoped reading. The planning-only paragraph described the completed planning dispatch (Spec Change Log). Its one substantive contrast is the audit-waiver channel reading. It is deferred above because SPEC.md:120 assigns module-file waivers to the guard. Its other contrasts are retained as context: the job graph previously lacked local execution evidence, now covered by Verification 2's patch; NU1900/4/5 use deterministic SDK warning controls; the final restored release.yml has not itself run hosted. None changes the captured intent or this build's spec.

Grouping: Blind 3, Edge 14 and Verification 5 form one deferred high entry (module-file audit waivers). Blind 5/Edge 2/Edge 3, Blind 6/Edge 1 and Blind 9/Edge 12 are rejected low groups. Blind 13/Edge 8 and Blind 1/Edge 13 are false pairs. Nine patch entries were applied directly by the review parent; no step-03 implementation agent existed in this follow-up dispatch. They comprise three medium (Verification 1–3) and six low (Verification 4, Edge 4, Edge 6, Edge 11, Blind 10, Blind 11) entries. None is high, no intent gap or bad-spec loopback was found, and every patch stays within existing interfaces.

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

### Follow-up review pass — 2026-11-11

Status: done.

Summary: story 3-3 delivers the create-mode version, audited build, original release artifact and marked draft with all five trailers, plus the failure-first publisher handoff. This follow-up pass ran a fresh four-lens review of the story-scoped delta:

- Builds `4dbf9b80ea6875c8f66a9f6cb5861f4fbba2d0a1..9b34565cb746d6a9c978d8dcf436830a31ceaefc`, excluding the merged 2-11 lifecycle files;
- the superproject Builds pointer change since `baseline_revision`.

It applied nine patches and committed them as Builds `a0b95ba2b8e0a94cdcd090c1d4ec44eabb9184e6` (`fix(ci): close release follow-up review gaps`). That commit is pushed to `origin/main` and verified with `git ls-remote`. Earlier pass results remain in this story's Git history (superproject `1c3ce8d625c4dba602e3906fcb121b45df960f5a` and the triage log above).

Files changed in this pass (Builds-relative):

- `Github/lib/tests/actions_expressions.py` — new test-only GitHub expression evaluator and composite runner (inputs, env, `if:`, external `with:`, outputs, GITHUB_OUTPUT heredocs).
- `Github/lib/tests/test_release_outcome.py` — executes the real `release.yml` gates, handoffs, reporter env, upload condition and workflow outputs across six graph states with the real reporter.
- `Github/lib/tests/test_release_version.py`, `test_release_draft.py`, `test_release_build.py` — composites run through their declared mappings. Adds the build-to-draft inventory round trip, multi-target container rejection, raw non-UTF-8 commit, nested nuspec and Content-Length regressions.
- `Github/lib/release_version.py` — decodes frozen commit text with replacement instead of aborting.
- `Github/lib/release_draft.py` — root-only nuspec selection and correct size-limit classification.
- `Tools/ci/README.md`, `docs/cicd-3-3-release-create-mode-results.md` — corrected container archive example and stale result wording, plus a follow-up review evidence section.

Review findings (33 rows):

- Patched (nine entries): Verification 1, 2 and 3 (medium), and Verification 4, Edge 4, Edge 6, Edge 11, Blind 10 and Blind 11 (low).
- Deferred (one high entry, three rows: Blind 3, Edge 14, Verification 5): module-file audit waivers, recorded in frontmatter `deferred` for the story 5-2 guard audit lint.
- Rejected false, each refuted by the evidence recorded in the triage log:
  - Blind 1, Blind 2 and Edge 13: real-SDK single-target and TreatWarningsAsErrors-unset controls still block NU1903.
  - Blind 13 and Edge 8: the per-repository caller `release` concurrency group.
  - Edge 15: complete mode stays fail-closed by intent.
- Rejected maybe-false: Edge 9. If true it is low, because re-running failed jobs or a new dispatch works.
- Rejected low, each with its reason in the triage log:
  - Blind 4: reserved-marker notes fail closed by design.
  - Blind 5, Edge 2 and Edge 3: every released module has stable tags.
  - Blind 6 and Edge 1: the AD-17 publisher owns the stray-tag refusal.
  - Blind 7: AD-10's closed module rules.
  - Blind 8: no current builds-rules caller; listing more types needs a new preset.
  - Blind 9 and Edge 12: this run's own digest-verified SDK output, still fail-closed.
  - Blind 12: the major-pinned Node matches Builds convention and cannot be verified locally.
  - Edge 5: a deliberate memory bound.
  - Edge 7: not a direct correction.
  - Edge 10: no module uses lock files.

Follow-up review recommended: false. This is a follow-up pass, and it patched no high-verdict entry (patched counts: high 0, medium 3, low 6), so the work has converged. The only high finding is deferred to the guard lint story.

Verification:

- `python3 -m unittest discover -s Github/lib/tests -p 'test_release_*.py' -v`: 143 tests passed.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and `... --python python3 ...`: 20/20 groups passed on Python 3.12.13 and 3.13.13, with 252 library tests each. The online zizmor policy group used the scoped CiCd-agent read token, which was not logged.
- `python3 Tools/ci/lint_workflows.py`: 12 exact frozen findings, 0 new.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` at committed `a0b95ba2b8e0a94cdcd090c1d4ec44eabb9184e6`: compatible, 2542 entries, no removals against `v4.47.0`.
- Frozen legacy files are byte-identical to `implementation_baseline_revision`: builds-release.yml, root package.json and lock, Hexalith.Build.props, NuGet.ci.Config, ContainerProvenance.targets and the publish spike sources.
- Mutating the release.yml release-rules, version fallback, no-op reason and notes mappings each fails the new graph tests.
- The non-UTF-8 regression fails without its fix.
- Pinned commitlint 21.2.4 passed the exact Builds message with 0 problems and 0 warnings. Local logs are under the session scratchpad and are not retained.

Residual risks:

- Until story 5-2's guard audit lint lands, create mode alone does not reject module-file `NoWarn` NU190x waivers (Directory.Build.targets or PackageReference metadata). No production caller uses the reusable release yet.
- The restored final `release.yml` has not itself run hosted. Its wiring is now exercised locally by the graph tests, while hosted evidence predates cleanup.
- Re-running all jobs after an upload may conflict on the `release` artifact name; this is unverified.
