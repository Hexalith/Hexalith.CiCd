---
title: 'The publish composite'
type: 'feature'
created: '2026-11-11'
status: done
review_loop_iteration: 0
followup_review_recommended: true
baseline_revision: 1803c3418cd200fe8544164b25b8f5b522ba56f8
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 967d3d058df27397da39011c95da0a7e45ebc24e
implementation_revision: 5050f01a74cd6ba22954030c852a097cffb2b5b8
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/references/Hexalith.Builds/Tools/ci/README.md'
warnings: [oversized]
deferred:
  - summary: >-
      Repair the incoming upstream routing-snapshot descriptor fixture and its four failing cases.
    evidence: |-
      Upstream merge e588605ccf2c6577a2490e1a3fc512f8ffdc3960 introduced required ownerRunId/runId/role fields while SelectedRoutingCatalogSnapshotTests.CreateDescriptor still emits only environmentId. Reviewer executed the focused class: 34 tests, 4 failures, exit 2; negative controls also short-circuit. These C# changes were already on origin/main before resumed publisher changes.
    location: >-
      references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/SelectedRoutingCatalogSnapshotTests.cs:289
    severity: medium
  - summary: >-
      Strengthen the upstream malformed explicit-port CLI tests so missing manifest errors cannot satisfy them.
    evidence: |-
      StartupReadinessTests uses --manifest unused and asserts only UsageOrManifest, the same exit code returned when manifest resolution fails. A valid manifest plus parse diagnostic and no-start observation would distinguish the intended refusal. This test was introduced by the preserved upstream merge, outside this story's changes.
    location: >-
      references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/StartupReadinessTests.cs:37
    severity: medium
  - summary: >-
      Complete and retain focused .NET verification for the incoming endpoint and attached-routing changes.
    evidence: |-
      Story 3-4's required Python/workflow/API checks do not execute the unrelated incoming C# changes. A reviewer ran the routing-snapshot class and found four failures; the upstream changes need their own focused verification and repair rather than silently attributing Python success to them.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/SelectedRoutingCatalogSnapshot.cs:83
    severity: medium
  - summary: >-
      Add independent attached-routing identity refusal cases for attached run, environment, role and hold bindings.
    evidence: |-
      The incoming NativeTestExecutorTests attached-routing test varies ownerRunId only while SelectedRoutingCatalogSnapshot validates several independent identity fields. Exact owner/environment/role/hold substitutions would establish refusal for each newly introduced boundary.
    location: >-
      references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/NativeTestExecutorTests.cs:762
    severity: medium
  - summary: >-
      Verify attached candidate-policy refusal independently of TestObservation.
    evidence: |-
      Incoming NativeTestExecutor code refuses attachments when CandidatePolicy is populated, but no test supplies CandidatePolicy with absent TestObservation. Existing access-observation refusal does not isolate that branch.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/NativeTestExecutor.cs:400
    severity: medium
  - summary: >-
      Preserve the requested explicit endpoint in unmanaged occupied-port diagnostics.
    evidence: |-
      Incoming AllocateOwned throws SocketException for an unmanaged occupied explicit port and CompositionEngine maps this to generic HXR020 text without the requested endpoint. The request remains available to the caller, so this is a diagnostic usability issue.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionPortAllocator.cs:184
    severity: low
---

<intent-contract>

## Intent

**Problem:** The reusable release can create an authenticated marked draft and original build artifact, but has no production publisher. CAP-12/13 require publication that finishes safely on retry and never publishes a version from different build content.

**Approach:** Add the AD-17 remote `Github/publish` composite, consuming the eight-field draft handoff. Authenticate original bytes, publish NuGet packages and complete OCI graphs, then publish the draft with tag creation last, or emit `ready` for the nightly App when workflow trees differ.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds`; runtime Python >=3.12 uses stdlib. Caller owns the `hexalith-release` environment and grants `contents: write`, `actions: read`, `id-token: write`. Accept `publish`, `version`, `sha`, `last-tag`, `draft-id`, `artifact-id`, `artifact-digest`, `artifact-run`, NuGet user and the registry push pair. Execute trusted action-path code; keep payload and empty execution directory outside `GITHUB_WORKSPACE`. Preserve original artifact SHA-256 and five draft trailers. Reject a conflicting Git version tag and every conflicting container version root before any NuGet/registry publication write. Use 3-1's pinned nested login and official Skopeo, verify complete remote OCI bytes. Every executed publisher path uploads one schema-valid outcome, including login/push failures.

**Never:** Checkout/execute module source, load its configuration, restore/build/repack, recompute the captured last reachable tag, move/delete a tag, have release runtime commit to main, add signed provenance/attestations or a public NuGet API-key fallback. Preserve AD-20 frozen legacy runtime, npm release configuration, `builds-release.yml` and production callers. Complete-mode selection/recovery/deletion, scheduler/App publisher, caller rewrite, guard audit lint (5-2) and prior unrelated deferrals remain downstream.

**Implementation scope:** The planning checkpoint is complete. Subsequent implementation dispatches must implement and verify the existing Execution tasks, including the isolated hosted NuGet/OCI/GitHub publication probe, and commit/push the reviewed changes in `references/Hexalith.Builds`. Planning-only statements in the companion plan and historical Auto Run Result describe the completed planning delivery; this canonical contract governs subsequent implementation dispatches.

**Hosted NuGet prerequisite:** Before the isolated hosted probe is dispatched, an operator must provision and confirm an active nuget.org Trusted Publishing policy matching repository `Hexalith/Hexalith.Builds`, workflow filename `release-publish-probe.yml`, environment `hexalith-release`, policy creator/NuGet user `jpiquot`, and exact package-ID scope `Hexalith.Builds.PublishProbe.20261111`, permitting the isolated package's publication. Keep the specified temporary caller; do not substitute an existing production policy/caller or an API-key fallback. Because the earlier draft and temporary controls were removed, restore the retained temporary controls for a fresh producer run that builds once. Successful hosted NuGet publication and a hosted duplicate-safe retry must consume that same new original handoff: producer run, artifact ID/digest, source SHA and version. Local simulations, container-only publication and a rejected OIDC exchange do not satisfy hosted package acceptance. The operator has confirmed policy creation; the resumed hosted probe must verify its token exchange and publication. Reuse this isolated package ID if the qualification runs on a later date; its dated suffix does not require a new daily package or policy.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Publish | Authenticated draft/artifact; workflow trees equal; version tag absent or targets built SHA | Push original packages/images; one draft PATCH creates tag last; verify published release and peeled tag; `published` outcome | No error |
| AD-17 tag conflict | Lightweight or annotated `v<version>` peels to another commit or non-commit | Exact diagnostic `tag vX.Y.Z does not point at the built commit`; zero package/image/release writes | Fail; preserve tag/draft |
| Authentication failure | Handoff, producer run, draft marker, digest, package stamp, archive or OCI graph invalid; reads uncertain | Zero publication writes | Fail with useful non-secret diagnostic |
| NuGet login rejected | Trusted Publishing token exchange fails | Skip package/image/release publication; upload one schema-valid `failed` outcome | Fail verification; retain non-secret diagnostic; do not waive hosted package acceptance |
| Container conflict | Any destination version root already differs | Check all roots before first NuGet/registry write; recheck each immediately before its copy | Fail; preserve conflicting content |
| Partial retry | Earlier package/image publication succeeded | Replay same original artifact; NuGet skips duplicates; matching complete OCI graph accepted | Remaining errors fail; no new build/version |
| GitHub token restriction | Fresh main's workflow tree differs from built commit | Leave marked draft; no publish PATCH/new tag; successful `ready` outcome with `draftId` and captured `lastTag` | Arbitrary 403/network failures remain failures |
| Finalization race | Ref/draft changes, incorrect API response or post-publication tag target | Reject before PATCH where detectable; independently verify response and peeled tag afterward | `failed`, never false `published`; no rollback |
| Empty payload | Valid manifest with empty package/container lists | Authenticate and finalize GitHub-only release without package/image operations | Same draft/tag/outcome rules |

</intent-contract>

## Code Map

Paths below are relative to `references/Hexalith.Builds` unless specified.

- `.github/workflows/release.yml:29,221,243` exports eight draft outputs and hands outcome ownership to publisher only after successful identity validation. `Github/lib/release_outcome.py:68,156,171` provides `reduce_results`, `validate_outcome`, `write_document`; preserve reducer handoff and failure precedence. `schemas/hexalith.release-outcome.v1.json` already supports required states.
- `Github/lib/release_draft.py:109,180,237,303,318` supplies bounded repository-bound `DraftApi`, credential-free signed storage download, `artifact_metadata`, `artifact_inventory`, `release_body`, `validate_draft`. Inventory validates original ZIP/manifest/package stamps/OCI but returns identities only: factor safe access to original validated files rather than trusting another manifest or extracting unchecked members.
- `Github/lib/release_state.py:45,160,197` supplies restricted `Api`, bare `Git`, stable-tag/ancestry logic. `release_draft.py:339` compares fresh main/source workflow trees but currently raises on difference; publisher needs a reusable comparison without changing create-stage failure behavior.
- `Github/lib/oci_archive.py:143,214` validates generalized full OCI index/platform/child/config/layer graphs. `Github/lib/publish_spike.py:195,217,235` proves registry checks, copy and private authfile cleanup; spike-specific destination/tag/platform constants must not enter production.
- `Tools/spikes/publish-tools.json` pins Skopeo 1.22.3 image digest/source; `docs/cicd-3-1-publish-composite-spike-results.md` settles nested `NuGet/login@8d196754b4036150537f80ac539e15c2f1028841` v1.2.0 and provenance exclusion. Preserve both as evidence.
- `Github/lib/tests/test_release_draft.py:546` executes actual composite input/env/output mappings using `actions_expressions.run_composite`, disposable histories and HTTP/tool controls. Existing `test_release_{draft,oci,outcome}.py` and `test_publish_spike.py` provide regressions; no workflow-text assertions.
- `Tools/ci/{run_python_tests,lint_workflows,check_public_api}.py` and README define retained checks; API checker reads committed Git objects. `commitlint.config.mjs`, locked root CLI/config 21.2.4 govern commits.
- CiCd `stories/3-1-*.md`, `3-2-*.md`, `3-3-*.md` are done: all-image preflight precedes NuGet, wrong-target tag refusal belongs to publisher, `publish=true` is authorization rather than publication. All prior execution checklists are complete. Builds `docs/cicd-3-4-publish-composite-plan.md` is the planning companion.

## Tasks & Acceptance

**Execution:**

- [x] `Github/lib/release_publish.py`; minimal factoring in `release_draft.py`/`release_state.py` -- authenticate eight-field handoff, bot draft/trailers/version/source/last-tag ancestry, original run (same caller workflow path, dispatch on main, source SHA), artifact ID/name/run/expiry/API digest and downloaded bytes. Safely materialize only fully validated original files in private temporary storage. Treat API errors as failures, never absence.
- [x] `Github/lib/release_publish.py` -- before all publication writes, peel the live version tag to built commit (including annotated refs), and preflight every container version root. Revalidate draft/tag before finalization. Keep the exact AD-17 tag diagnostic; never independently create/update/delete Git refs.
- [x] `Github/lib/oci_publish.py` -- generalize registry/Skopeo mechanism using `oci_archive.py` and `Tools/spikes/publish-tools.json`; require exact reported tool version/source. Use private temporary authfile, original uncompressed tar and `copy --all --preserve-digests`; recheck root immediately before copy and verify every remote manifest/config/layer digest and size. Restrict credentials to intended endpoints, bound operations and remove auth material on all exits.
- [x] `Github/publish/action.yml` and `Github/lib/release_publish.py` -- add remote composite inputs above. Order preflight, nested SHA-pinned NuGet/login, original-file `dotnet nuget push --source https://api.nuget.org/v3/index.json --skip-duplicate` from empty directory, then OCI publication. Invoke Python through `GITHUB_ACTION_PATH`, use env for expressions, and pin external actions. Arrange an `always()` outcome finalizer/upload to cover login and command failures, with `overwrite: true` and no second outcome owner.
- [x] `Github/lib/release_publish.py` -- after all pushes, freshly compare complete `.github/workflows/` trees and source ancestry. Difference emits `ready`; equality permits one PATCH setting `tag_name`, full `target_commitish`, `draft: false`. Validate returned release identity/state and independently fetched peeled tag before `published`. Initialize failure reporting from trusted dispatch SHA so malformed handoff still yields schema-valid `failed`; replace with built SHA/version after validation. `ready` includes `draftId`/`lastTag`. Reuse `release_outcome.py` validation rather than changing schema/reducer semantics.
- [x] `Github/lib/tests/test_release_publish.py`, `test_oci_publish.py`, existing draft/OCI/outcome tests and `test/fixtures/release/` -- execute matrix edges through real disposable Git/HTTP/tool operations and actual composite mappings/finalizer. Include both tag forms, non-commit/error refs, correct-target retry, all-images-before-first-package ordering, a late image conflict, corrupt/unsafe archives, producer/draft mismatches, partial retries, empty payload, login/push/API failure, main product advancement, workflow change and post-PATCH tag mismatch. Assert observable writes, bytes and single uploaded outcome, including poisoned workspace/config controls.
- [x] `Github/publish/README.md`, `Tools/ci/README.md`, `docs/cicd-3-4-publish-composite-results.md` -- document interface, permission union, outcome ownership and downstream caller/recovery seams. During implementation only, use temporary `.github/workflows/release-publish-probe.yml` plus `Tools/ci/probe_release_publish.py` for an isolated hosted remote-composite producer/publisher exercise with original artifact and caller environment. Confirm the operator-provisioned Hosted NuGet prerequisite first; retain successful hosted package publication and duplicate-safe retry evidence from the same fresh original handoff without rebuilding or changing its source/version. Retain sanitized full source/run/artifact/release/tag/registry evidence, distinguish local negative controls from hosted observations, remove temporary controls and clean up identified disposable resources within their authorization. Keep production callers and switch unchanged.

**Acceptance Criteria:**

- Given a remotely invoked composite in the caller's `hexalith-release` job, when its handoff validates, then original packages and complete multi-platform images are observable at their version destinations without source checkout/build or workspace configuration execution.
- Given the I/O matrix fixtures, when the actual publisher/composite executes, then observable registry/NuGet/GitHub writes and uploaded outcome match every matrix row; wrong-target tags cause zero publication writes with the exact AD-17 message.
- Given a failed partial attempt, when the same handoff executes again, then it completes from identical authenticated bytes using duplicate-safe pushes and leaves the tag resolving to the original built SHA.
- Given package/image success, when final workflow comparison and GitHub publication finish, then the persisted draft remains for `ready` or the release is published with tag created last for `published`; unrelated errors fail the job and outcome.
- Given any executed composite path including failed login, when its finalizer runs, then exactly one `hexalith-release-outcome` artifact contains schema-valid `outcome.json` and no credentials; successful handoff remains the sole ownership transfer from the reusable reporter.
- Given final implementation, when retained quality/API checks run, then they pass, legacy frozen bytes and production callers remain unchanged, and hosted evidence establishes remote invocation/publication separately from local simulations, including successful NuGet publication and a hosted duplicate-safe retry consuming the same fresh original producer run, artifact ID/digest, source SHA and version.

## Spec Change Log

- 2026-11-11: Human chose a dedicated nuget.org Trusted Publishing policy for the existing `release-publish-probe.yml` caller, environment `hexalith-release`, creator `jpiquot`, and exact isolated package ID `Hexalith.Builds.PublishProbe.20261111` in `Hexalith/Hexalith.Builds`, then confirmed policy creation. Retained successful hosted NuGet publication and same-original hosted retry as acceptance gates; those hosted results remain unverified. Clarified that the dated package ID can be reused across dates without daily policy creation.
- 2026-11-11: Human authorized implementation of the existing Execution tasks, tests and isolated hosted publication probe, followed by reviewed Builds commit/push. Clarified that planning-only scope belongs to the completed planning checkpoint, including companion plan and historical run-result statements. Existing publication requirements and downstream exclusions continue to apply.

## Review Triage Log

### 2026-11-11 — Review pass
- verdicts: 19 findings — high 1, medium 7, low 3, false 7, maybe-false 1
- findings:
  - `[medium]` `[defer]` Verification gap: invalid-port CLI tests can pass on missing manifest — the filed test evidence shows `--manifest unused` and exit-code-only assertions. This test originates in incoming upstream merge `e588605ccf2c6577a2490e1a3fc512f8ffdc3960`; record its independent repair.
  - `[medium]` `[defer]` Verification reviewer: descriptor fixture breaks routing-proof controls — focused .NET class ran 34 tests with four failures; the upstream fixture lacks newly required owner identity. Group with the blind reviewer fixture finding.
  - `[medium]` `[defer]` Blind reviewer: update the routing descriptor fixture — confirmed `CreateDescriptor` omits ownerRunId/runId/role required by `ValidateDescriptor`; this upstream regression is unchanged by resumed publisher work.
  - `[false]` `[reject]` Blind reviewer: cancellation behavior needs a runtime change — the reported failure supplies an invalid descriptor; strict identity validation correctly rejects it before reading files. With a valid descriptor, the token still reaches cancellable reads. The fixture failure is recorded separately, and does not establish a valid-input cancellation regression.
  - `[medium]` `[defer]` Blind reviewer: verify affected C# changes — Python suites do not claim to cover C#; review nevertheless exposed a genuine incoming test regression. Record the incoming changes' separate .NET verification debt, without changing those unrelated runtime files.
  - `[false]` `[reject]` Blind reviewer: retained probe tag contradicts completed cleanup — results explicitly list retained release/tag/package/image, explain protection prevents deletion and warn about version-base selection. The spec requires cleanup within authorization; no complete deletion is claimed and no policy mutation is authorized. Retention remains a disclosed operational risk.
  - `[medium]` `[patch]` Blind reviewer: probe tag weakens API baseline — additionally compare the final public API with genuine product release `v4.47.0` (`5ec1779040606be89306129a7d2b245258c9acd2`), retaining 2488 baseline entries, 2554 current entries, 66 additions and zero removals. Keep the normal committed-source check too.
  - `[low]` `[patch]` Blind reviewer: verification output needs durable retention — retain sanitized focused output and full-suite/lint/API result excerpts alongside commands and hashes, so `/tmp` lifetime does not limit later review.
  - `[medium]` `[defer]` Blind reviewer: attached-routing negative identity cases are incomplete — inspected test varies only ownerRunId while the incoming validator checks attached run/environment/role/hold independently. Record separate upstream coverage work.
  - `[medium]` `[defer]` Blind reviewer: candidate policy needs an isolated attached refusal test — incoming candidate-policy guard is not independently exercised with TestObservation absent. Record upstream coverage work.
  - `[low]` `[defer]` Blind reviewer: unmanaged occupied-port diagnostic omits the endpoint — incoming allocator throws SocketException and engine emits generic HXR020. Preserve the upstream behavior and record this diagnostic improvement.
  - `[low]` `[reject]` Blind reviewer: include package identity in every fixed status line — authenticated artifact inventory already identifies package paths/version and publication behavior is unchanged. Dynamic metadata plus escaping would add complexity for a cosmetic logging improvement; keep credential-free constant status lines.
  - `[maybe-false]` `[reject]` Blind reviewer: stderr/missing stdout/misleading status text lacks controls — missing stdout already runs through successful existing tool controls. A misleading recognized phrase would need an actual pinned dotnet response to establish the claimed logging error; it would affect cosmetic status only, since exit codes control publication. Additional parsing branches/tests are unwarranted without such evidence.
  - `[high]` `[patch]` Edge reviewer: unreadable state prevents the always-run outcome — demonstrated missing/truncated state previously exited before producing an upload path and retained payload. Repair `3699c6d6c72ca2a02940cdf73656ae7ebf53a6a8` writes state atomically and falls back to schema-valid failed dispatch identity with cleanup. Actual composite missing/truncated/invalid state cases and interrupted-write preservation pass.
  - `[false]` `[reject]` Intent auditor: newly changed test is not the AD-17 boundary — AD-17 already exists in live implementation and parent reran actual-composite conflict cases for lightweight/annotated/non-commit refs; each asserts exact diagnostic, no writes and one failed outcome. Resumed delivery need not replace that guard to preserve and verify it.
  - `[false]` `[reject]` Intent auditor: hosted publication does not demonstrate hosted conflicting-tag refusal — hosted success/retry and local actual-composite negative controls are explicitly distinguished. The story requires these surfaces separately, not hosted dispatch for every negative matrix row.
  - `[false]` `[reject]` Intent auditor: production callers are not integrated — downstream caller integration is explicitly excluded by the story invoked through folder/id. This delivery qualifies the remote composite and preserves existing production callers as required.
  - `[false]` `[reject]` Intent auditor: unrelated C# changes exceed publisher intent — `git diff 967d3d058df27397da39011c95da0a7e45ebc24e e588605ccf2c6577a2490e1a3fc512f8ffdc3960` proves every listed C# change arrived on origin/main before resumed work; they were preserved by fast-forward. No publisher commit changes those C# files. Their genuine review issues are deferred above.
  - `[false]` `[reject]` Intent auditor: diff cannot prove commit/push — independent Git readback verifies the complete owning-repository HEAD on origin/main; canonical CiCd story/gitlink remain staged per the explicit delivery instruction.

## Design Notes

Resumed implementation from Builds `967d3d058df27397da39011c95da0a7e45ebc24e`; the previously implemented publisher originated after story baseline `891886ddc60a9924d053bb74bf6bcc73e101b2ce`. The resumed diff retains that original implementation as context and completes the hosted NuGet gate.

The publisher consumes the captured `last-tag`; it checks ancestry instead of selecting a newer base on moving main. Source ancestry remains mandatory even when workflows are unchanged. A workflow difference is the specified successful `ready` condition, not a catch-all for authorization errors. Complete-mode orchestration is still fail-closed upstream until its downstream story; this composite can consume an original-run handoff without implementing recovery.

Keep existing safe download limits and credential separation when factoring payload access. No registry write precedes complete artifact validation and all-image preflight; no GitHub publication precedes package/image success. External races can still cause failure after a partial side effect: record failure and replay original bytes, never compensate by moving/deleting tags.

## Verification

Implementation verification, from Builds root:

- `uv run --no-cache --with PyYAML==6.0.3 --with jsonschema==4.26.0 python -m unittest discover -s Github/lib/tests -p 'test_release_publish.py'` and the same command with `test_oci_publish.py` -- focused matrix/composite effects pass.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and `uv run --no-cache --locked --script --python "$(command -v python3)" Tools/ci/run_python_tests.py` -- retained suites pass with documented tooling prerequisites.
- `python3 Tools/ci/lint_workflows.py` -- pinned lint and authenticated online audits pass, with secrets supplied without logging.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` -- run against committed implementation; additions pass, no unintended removals.
- Hosted probe -- confirm the dedicated Trusted Publishing policy before dispatching a fresh producer; inspect actual remote composite/job results, original downloaded artifact bytes, NuGet/OCI destinations, persisted draft/release and peeled tag, plus single downloaded outcome. Retain successful hosted NuGet publication and duplicate-safe retry from that same original handoff without another build or a changed source/version. Never substitute YAML text, helper-only assertions, local simulations or container-only success for these package surfaces.

Resumed execution completed the dedicated-policy hosted gate: producer `43010609603` built original artifact `13850760915` with digest `sha256:18db4ed7b07ffa3c5fd4496afce65dd50888705687d42695260e7573a7456d30`, source `75e1d4a3809b30684e67c7e9b2c8043720b49c53` and version `4.47.1`. Publisher `43010882516` successfully exchanged OIDC and published the isolated package/complete OCI graph, ending `ready`; publisher `43011306951` consumed the same handoff, skipped the duplicate package and ended `published`, with independently verified release/tag targeting that original source. Both downloaded outcomes validate independently against the schema. Python 3.12 and runner 3.14 full suites pass 20/20 groups each; focused publisher/OCI controls, authenticated workflow lint, committed-source API and frozen-byte checks pass. Full sources, observable effects, identities, commands and log hashes are retained in Builds `evidence/cicd-3-4/trusted-publishing/` and [results](../../../../references/Hexalith.Builds/docs/cicd-3-4-publish-composite-results.md).

Temporary controls are removed. No protection policy changed in resumed execution. Protected disposable release `441591623` (returned to draft after qualification) and `v4.47.1` remain together, as do the isolated NuGet/registry version; the reachable probe tag can affect future version-base selection until authorized maintainer cleanup. Public NuGet page, version index and package retrieval now return HTTP 200. Independent public nupkg inspection confirms all six original ZIP entries are unchanged and only nuget.org's repository signature was added; `dotnet nuget verify --all` passes. Exact original/public/signature hashes and observations are retained in Builds `evidence/cicd-3-4/trusted-publishing/nuget-public-package.json`.

Implementation delivery completes the existing Execution tasks and acceptance criteria, runs the implementation verification above, and checks `git diff --check`. Validate the exact commit message with pinned commitlint, fetch/check divergence, commit/push the reviewed Builds implementation, verify its remote full SHA, then stage the canonical CiCd story with the updated Builds gitlink. Do not commit/push CiCd. The planning-only halt at `ready-for-dev` applied to the completed planning delivery and does not apply to subsequent implementation dispatches.

## Auto Run Result

Status: done

Delivered the original-artifact publish composite and verified AD-17 through actual composite conflict controls. Resumed work completed dedicated-policy hosted NuGet/OCI publication, a duplicate-safe replay from the same original handoff, public package-byte/signature readback, and review hardening of the always-run outcome finalizer. The user-staged intent contract is preserved byte-for-byte.

Files changed:
- [Publisher](../../../../references/Hexalith.Builds/Github/lib/release_publish.py): credential-free package status messages, atomic state writes, failed-outcome recovery and private-payload cleanup when state is missing or invalid.
- [Publisher tests](../../../../references/Hexalith.Builds/Github/lib/tests/test_release_publish.py): status redaction, interrupted-state preservation, and actual-composite missing/truncated/invalid state cases; existing live tag conflict controls retained.
- [Publisher interface](../../../../references/Hexalith.Builds/Github/publish/README.md) and [CI guidance](../../../../references/Hexalith.Builds/Tools/ci/README.md): publication, retry, permissions, ownership and qualification evidence.
- [Results](../../../../references/Hexalith.Builds/docs/cicd-3-4-publish-composite-results.md) and [verification records](../../../../references/Hexalith.Builds/evidence/cicd-3-4/trusted-publishing/verification.json): exact hosted source/run/artifact/release/tag identities, original bytes, public NuGet package/signature observations, durable verification excerpts, cleanup and upstream regression evidence.
- Temporary caller/helper restored for qualification and removed; canonical CiCd story and Builds pointer staged only.

Review: all four lenses completed, with 19 raw findings. Three patch entries were addressed (high 1, medium 1, low 1): recoverable finalizer state, genuine-product API comparison and durable verification output. Six grouped upstream items are recorded in the single frontmatter deferred list, including the incoming .NET fixture regression. Every raw finding has its own verdict/evidence row above.

Rejected findings and reasons:
- Cancellation runtime change: the failing fixture lacks required descriptor identity; valid descriptors still reach cancellable reads.
- Incomplete cleanup claim: retained protected resources and their operational effect are explicitly disclosed; no deletion outside authorization is claimed.
- Dynamic package log identity: cosmetic benefit does not justify dynamic output/escaping beyond constant credential-free statuses.
- Misleading status classification: no pinned-tool response demonstrates the alleged error; missing stdout is already exercised, and status text does not control publication.
- AD-17 test surface mismatch: the existing actual-composite conflict tests ran and passed; the tag guard already exists in live production code.
- Missing hosted conflict invocation: local actual-composite negative controls and hosted publication/retry evidence satisfy their separate required surfaces.
- Missing production caller integration: the invoked story explicitly leaves that integration downstream.
- Additional C# scope: every listed C# change arrived in the preserved origin/main merge before resumed publisher work; publisher commits do not edit them.
- Unproven push: independent origin/main readback matches the final full owning-repository revision below.

Verification:
- All nine I/O matrix rows have executed passing controls. Focused publisher 12/12 and OCI 3/3 pass, including actual composite AD-17 refusal with exact diagnostic, zero publication writes and one schema-valid failed outcome.
- Initial authenticated complete suites passed 20/20 groups on Python 3.12.13 and runner 3.14.4. After the repair, complete reruns passed 19/20 groups each; the sole failure was the omitted authentication prerequisite of the online policy group. That entire group was rerun with privately supplied authentication and passed all 46 tests on each interpreter, verifying all 20 groups after repair without code changes between runs. Exact failure/recovery and durable excerpts are retained.
- Authenticated workflow lint passes: 12 exact frozen findings, zero new. Final committed-source public API check passes: 2554 entries, no removals. Independent comparison with genuine product v4.47.0 confirms 2488 baseline entries, 66 additions, zero removals. Frozen GitHub/workflow/pin bytes and temporary-control removal are independently verified; whitespace checks pass.
- Hosted producer 43010609603 built artifact 13850760915 once. Publisher 43010882516 ended ready; publisher 43011306951 reused its exact producer/artifact/digest/source/version, observed NuGet duplicate skipping, reverified OCI and ended published. Both outcome ZIPs validate independently. The public NuGet package preserves all six original entries and adds only a valid NuGet repository signature.

Residual risks and recommendation:
- Follow-up review recommended: true. The high finalizer repair has actual local composite fault coverage; hosted publication evidence pins the earlier controller, so abrupt interruption of the repaired controller on a hosted runner remains unverified.
- Incoming upstream .NET routing class has four failures out of 34 tests, caused by missing owner fields in its fixture. Exact command/log and six upstream follow-ups are retained; the story does not claim a passing .NET suite.
- Protected v4.47.1 remains reachable and can affect future version-base selection until authorized cleanup. Its identified release is retained as a draft after qualification; genuine product v4.47.0 is again latest. Original release body/source and tag target are preserved. No protection policy changed. Isolated package/image and evidence artifacts remain.

Delivery:
- Builds main committed and pushed: `5050f01a74cd6ba22954030c852a097cffb2b5b8`. Independent remote readback matches and the Builds working tree is clean.
- The canonical CiCd story and updated Builds gitlink are staged, with no CiCd commit/push, following the explicit delivery instruction. This scope-specific instruction takes precedence over the workflow's generic all-working-copies commit/clean step.
