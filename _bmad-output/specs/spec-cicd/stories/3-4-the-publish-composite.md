---
title: 'The publish composite'
type: 'feature'
created: '2026-11-11'
status: in-review
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
  - summary: >-
      Move the upstream explicit-endpoint README section out of License and update the stale attached-routing and claim-retry text.
    evidence: |-
      Upstream commit bfda07ee appends "### Explicit endpoints and attached routing snapshots" (README.md:1399) after "## License" (README.md:1394), so it renders as a License subsection. README.md:641-643 still says owners requiring routing-catalog observations fail attached runs as startup-failure. README.md:752-754 still says every claim conflict retries up to 64 times, with no exception for explicit ports. Not changed by publisher work.
    location: >-
      references/Hexalith.Builds/README.md:1399
    severity: low
  - summary: >-
      Test and explain the upstream refusal of explicit EventStore ports on attached suites.
    evidence: |-
      ModuleCommandApplication refuses --attach-to combined with --eventstore-port through generic HXC001 "The command line is invalid." ModuleCommandExecutionService:119-122 throws for Down, runId or out-of-range ports. Searching test/ for eventstore-port/EventStorePort finds only StartupReadinessTests, none with --attach-to, and the guard message appears in no test. Removing either guard fails no test, although the README promises "Attachments cannot request owner ports". Arrived with upstream merge e588605c.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Module.Cli/ModuleCommandApplication.cs:450
    severity: medium
  - summary: >-
      Make the explicit-port exclusion from independent allocation observable in a test.
    evidence: |-
      CompositionPortAllocator adds the requested port to the excluded set before Allocate, then overwrites EventStoreHttp. The existing distinctness test requests a port already handed out in-process, which _handedOut skips anyway. The other tests take OS-ephemeral ports outside the Linux candidate range. Deleting excluded.Add(requested) fails no test, even though an in-range request (such as the README's 18080) could then be given to a second endpoint. A deterministic test likely needs an injectable candidate source. Upstream change.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/CompositionPortAllocator.cs:174
    severity: medium
  - summary: >-
      Remove the ephemeral-port reuse race from the upstream explicit-port tests.
    evidence: |-
      StartupReadinessTests:66-69 binds an OS-assigned loopback port, stops the listener and then requests that port for the owner. CompositionResourceClaimStoreTests:67 reallocates the same way. Any parallel test or outbound connection can take the released port in between, which makes failures intermittent. Upstream test code.
    location: >-
      references/Hexalith.Builds/test/Hexalith.Builds.Module.Tests/StartupReadinessTests.cs:66
    severity: low
  - summary: >-
      Confirm whether attached children can rewrite the owner's routing-catalog proofs that later attachments capture.
    evidence: |-
      Upstream removed the attached refusal for owners requiring routing-catalog observations (NativeTestExecutor.cs:400 now refuses only on TestObservation/CandidatePolicy/hold mismatch). Unverified: settle it by checking whether attached children get write access to the owner's platform-components/<env>-catalog proofs, and whether SelectedRoutingCatalogSnapshot re-verifies those bytes against the owner capture after each attached child exits.
    location: >-
      references/Hexalith.Builds/src/libraries/Hexalith.Builds.Tooling/Runtime/NativeTestExecutor.cs:400
    severity: medium (unverified)
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

### 2026-11-11 — Review pass
Follow-up pass over the superproject since `1803c3418cd200fe8544164b25b8f5b522ba56f8` plus Builds `967d3d058df27397da39011c95da0a7e45ebc24e..5050f01a74cd6ba22954030c852a097cffb2b5b8`. The story spec (claims file) and the orchestrator-owned deferred-work ledger were left out of the diff. Intent-auditor divergence (b) contained two separate claims, so it is logged as two findings.
- verdicts: 41 findings — high 0, medium 10, low 16, false 14, maybe-false 1
- findings:
  - `[low]` `[patch]` Blind: the publisher README says authenticated handoffs report the built SHA/version, but the state-loss fallback reports the dispatch SHA with no version — fixed: `Github/publish/README.md` now documents the fallback (dispatch SHA, no version, `failed`).
  - `[low]` `[reject]` Blind: the state-loss fallback keeps no copy of the authenticated release identity (grouped with Edge "fallback drops built SHA/version" and Intent (b1)) — confirmed: the fallback outcome carries `GITHUB_SHA` with no version. State loss inside the job's private `/tmp` directory is an abnormal fault, and the outcome is still `failed` and schema-valid. Carrying identity through additional step outputs would add plumbing to a rarely reached degraded path.
  - `[low]` `[patch]` Blind: the fallback diagnostic hides whether state was missing, truncated or invalid, and no test asserts it — fixed: the diagnostic now names the exception class, and the actual composite asserts `FileNotFoundError`/`ReleaseError`/`OutcomeError` for the missing/truncated/invalid state cases.
  - `[false]` `[reject]` Blind: `finally` deletes an unchecked `RELEASE_STATE` path — `RELEASE_STATE` comes only from the prepare step's own `outputs({"state": ...})`, which is the `mkdtemp` directory created outside the workspace. Deleting it is the intended private-payload cleanup, which the composite test asserts.
  - `[medium]` `[patch]` Blind: the composite test discards `run_composite`'s result, so nothing proves failures still fail the job — confirmed: `run_composite` returns `None` when any step fails, and the result was ignored. Fixed: every scenario now asserts `(result is None) == (expected == "failed")`, which covers success, ready and failure paths.
  - `[false]` `[reject]` Blind: state-fault coverage depends on the login hook, and the CI README overclaims "every failure/finalizer boundary" — the outcome phase reads state with the same code whenever the loss happened. The empty-inventory/login-skipped result combination is already covered by the `empty` scenario. No outcome-phase branch is left unexercised.
  - `[low]` `[reject]` Blind: NuGet status classification depends on English CLI text — status lines are cosmetic, and the exit code alone controls publication. Hosted Ubuntu runners emit English. Pinning `DOTNET_CLI_UI_LANGUAGE` adds environment surface for a logging nuance (compare the prior pass's status-text rejection).
  - `[low]` `[reject]` Blind: status lines do not name the package — carried: package identity in status lines was rejected earlier as cosmetic; the constant credential-free statuses are unchanged.
  - `[low]` `[patch]` Blind: the results doc frontmatter `implementation_revision: e9741b56…` and its `hosted-publication-qualified` status overstate what the shipped controller qualified (grouped with Edge "status read as covering shipped finalizer") — fixed: the frontmatter now records `hosted_qualified_revision` `e9741b56…`, `finalizer_repair_revision` `3699c6d6…` and `finalizer_repair_verification: local-actual-composite-only`.
  - `[medium]` `[patch]` Blind: the retained probe tag is the public-API baseline — carried: the prior pass added the comparison against genuine `v4.47.0`, and that is still retained.
  - `[low]` `[patch]` Blind: the dedicated nuget.org Trusted Publishing policy stays live, and nothing records its cleanup (grouped with Blind "retained draft looks pending" and Intent (f)) — fixed: the results cleanup section now records the active policy (kept for reuse, as the story allows) and that the maintainer should remove it once re-qualification is no longer needed.
  - `[low]` `[patch]` Blind: retained draft `441591623` still carries all five handoff trailers — confirmed. Publisher authentication binds to the producer's caller workflow path (`producer()`), so replay needs `release-publish-probe.yml` re-added on `main` before artifact expiry at 2027-02-09T11:16:45Z. Fixed with the grouped results-doc record: that replay path, and that cleanup should delete the draft together with `v4.47.1`.
  - `[false]` `[reject]` Blind: hosted OCI publication leaves no trace and has no independent readback — `publish_oci` raises on any remote manifest/config/layer digest or size mismatch, so step success is the verification. `registry-verification.json` states exactly that evidence kind and claims no independent download.
  - `[low]` `[defer]` Blind: upstream README explicit-endpoint section sits under License, and nearby text is stale (grouped with Verification-gap other finding) — confirmed at README.md:1394/1399, 641-643 and 752-754, all from upstream `bfda07ee`. Deferred.
  - `[medium]` `[defer]` Blind: attachment requesting a port gets an opaque HXC001 refusal, with no test (grouped with Verification-gap "attached explicit port refusal untested") — confirmed at ModuleCommandApplication.cs:450 and ModuleCommandExecutionService.cs:119-122. No test combines `--attach-to` with a port. Upstream merge; deferred.
  - `[false]` `[reject]` Blind: frozen-file and lint evidence cannot be reconciled — the two records state different scopes: all 215 baseline files, versus the 135 GitHub/workflow/pin files at `3699c6d6`. `Tools/ci/README.md` is a permitted story change outside the second scope. Identical lint-log hashes are expected when workflow inputs are unchanged. Durable excerpts were retained by the prior patch.
  - `[false]` `[reject]` Blind: tag-ruleset cleanup reasoning conflicts with the earlier `v4.48.0` deletion — the results doc explicitly says that earlier deletion "overstepped resource-only authorization", that later guidance prohibited protection administration, and that it restored the exact policy. The two records are reconciled.
  - `[medium]` `[defer]` Edge: routing descriptor fixture lacks the required owner fields — carried: already deferred, and still reads as described at the reviewed revision.
  - `[false]` `[reject]` Edge: a state-write failure after a successful PATCH reports `failed` for a published release — reaching it needs a write failure in the job's own private `/tmp` directory, which was never shown to happen. The matrix explicitly accepts `failed` (never a false `published`) after partial side effects.
  - `[low]` `[defer]` Edge: unmanaged occupied explicit port gives generic HXR020 — carried: already deferred upstream diagnostic.
  - `[low]` `[defer]` Edge: explicit-port tests release an OS ephemeral port before reuse, so the test can race — confirmed at StartupReadinessTests.cs:66-69 and CompositionResourceClaimStoreTests.cs:67, in upstream test code. Deferred.
  - `[low]` `[reject]` Edge: the state-loss fallback drops the validated SHA/version, contrary to the "replace with built SHA/version" task — grouped with Blind "fallback keeps no identity", same rejection.
  - `[low]` `[patch]` Edge: `hosted-publication-qualified` is read as covering the never-hosted finalizer repair — grouped with Blind "frontmatter overstates", same frontmatter fix.
  - `[maybe-false]` `[defer]` Edge: attached children may rewrite owner routing proofs that later attachments capture — upstream removal of the refusal at NativeTestExecutor.cs:400. To settle it, check attached children's write access to the owner's catalog proofs and whether those bytes are re-verified. Deferred as medium (unverified).
  - `[medium]` `[defer]` Verification gap: the stale descriptor fixture makes the routing negative scenarios vacuous — carried: the existing deferral already records that the negative controls short-circuit.
  - `[medium]` `[defer]` Verification gap: explicit-port parsing test cannot tell the port refusal from a missing manifest — carried: already deferred.
  - `[medium]` `[defer]` Verification gap: no test of an attached suite requesting an explicit port — grouped with Blind "opaque HXC001 refusal", upstream; deferred.
  - `[medium]` `[defer]` Verification gap: no test observes the explicit-port exclusion from independent allocation — trusted as filed: no current test can fail if `excluded.Add(requested)` is deleted. Upstream code; deferred as filed.
  - `[medium]` `[defer]` Verification gap: attached routing identity checks are tested only with a foreign `ownerRunId` — carried: already deferred.
  - `[medium]` `[defer]` Verification gap: attached HXT009 candidate-policy branch is never exercised — carried: already deferred.
  - `[low]` `[defer]` Verification gap (other): README section rendered under License — grouped with Blind README finding; deferred.
  - `[false]` `[reject]` Intent (a): the shipped controller `3699c6d6` was never hosted. The intent's hosted gates name remote invocation, NuGet publication and duplicate-safe retry. `action.yml`, `push_packages`, authentication and finalization are byte-identical to the hosted-qualified `e9741b56`. The repair changes only stdlib file persistence/fallback in the private directory, and that runs through real action mappings in the actual composite that AC-5 assigns to the finalizer. The residual risk stays recorded.
  - `[low]` `[reject]` Intent (b1): a state-loss outcome identifies the dispatch commit, not the built one — grouped with Blind "fallback keeps no identity", same rejection.
  - `[false]` `[reject]` Intent (b2): the repair does not cover a failure while writing the outcome itself — such a failure needs a `/tmp` write failure that was never shown to occur. It would fail loudly through `if-no-files-found: error`, never as a false success.
  - `[false]` `[reject]` Intent (c): matrix rows are split between hosted and local surfaces — carried: the story requires those surfaces separately.
  - `[false]` `[reject]` Intent (d): remote OCI verification is the controller's own check — the intent puts that verification on the publisher ("verify complete remote OCI bytes"), and the evidence states its kind exactly.
  - `[false]` `[reject]` Intent (e): `ready` was forced by a workflow edit, and the retry did not use the App path — the matrix row's condition is exactly a workflow-tree difference. The App publisher is explicitly downstream.
  - `[low]` `[patch]` Intent (f): the probe's effects last on the real repository's release line — grouped with Blind "Trusted Publishing policy" and "retained draft", same results-doc record.
  - `[false]` `[reject]` Intent (g): the public nupkg SHA differs from the original — the intent preserves the original artifact SHA-256, which is verified. nuget.org always adds its repository signature, and all six original entries are proven unchanged.
  - `[false]` `[reject]` Intent (h): the restored temporary caller was restructured — the intent requires the specified filename, environment and policy match, and those are kept. The composite independently authenticates all eight handoff fields, so the caller's plumbing does not weaken the evidence.
  - `[false]` `[reject]` Intent (i): the pushed range includes the upstream merge and the 20 suite groups were assembled from separate runs — carried: the upstream C# scope was already established as outside publisher work, and the split run was disclosed.

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

