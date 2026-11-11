---
title: 'The publish composite'
type: 'feature'
created: '2026-11-11'
status: 'blocked'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 0d29ed715475567155cee2d6f078b7a4bc5faa6a
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: a0b95ba2b8e0a94cdcd090c1d4ec44eabb9184e6
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
  - '{project-root}/references/Hexalith.Builds/Tools/ci/README.md'
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** The reusable release can create an authenticated marked draft and original build artifact, but has no production publisher. CAP-12/13 require publication that finishes safely on retry and never publishes a version from different build content.

**Approach:** Add the AD-17 remote `Github/publish` composite, consuming the eight-field draft handoff. Authenticate original bytes, publish NuGet packages and complete OCI graphs, then publish the draft with tag creation last, or emit `ready` for the nightly App when workflow trees differ.

## Boundaries & Constraints

**Always:** Work in `references/Hexalith.Builds`; runtime Python >=3.12 uses stdlib. Caller owns the `hexalith-release` environment and grants `contents: write`, `actions: read`, `id-token: write`. Accept `publish`, `version`, `sha`, `last-tag`, `draft-id`, `artifact-id`, `artifact-digest`, `artifact-run`, NuGet user and the registry push pair. Execute trusted action-path code; keep payload and empty execution directory outside `GITHUB_WORKSPACE`. Preserve original artifact SHA-256 and five draft trailers. Reject a conflicting Git version tag and every conflicting container version root before any NuGet/registry publication write. Use 3-1's pinned nested login and official Skopeo, verify complete remote OCI bytes. Every executed publisher path uploads one schema-valid outcome, including login/push failures.

**Never:** Checkout/execute module source, load its configuration, restore/build/repack, recompute the captured last reachable tag, move/delete a tag, have release runtime commit to main, add signed provenance/attestations or a public NuGet API-key fallback. Preserve AD-20 frozen legacy runtime, npm release configuration, `builds-release.yml` and production callers. Complete-mode selection/recovery/deletion, scheduler/App publisher, caller rewrite, guard audit lint (5-2) and prior unrelated deferrals remain downstream. This invocation delivers planning only.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Publish | Authenticated draft/artifact; workflow trees equal; version tag absent or targets built SHA | Push original packages/images; one draft PATCH creates tag last; verify published release and peeled tag; `published` outcome | No error |
| AD-17 tag conflict | Lightweight or annotated `v<version>` peels to another commit or non-commit | Exact diagnostic `tag vX.Y.Z does not point at the built commit`; zero package/image/release writes | Fail; preserve tag/draft |
| Authentication failure | Handoff, producer run, draft marker, digest, package stamp, archive or OCI graph invalid; reads uncertain | Zero publication writes | Fail with useful non-secret diagnostic |
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

- [ ] `Github/lib/release_publish.py`; minimal factoring in `release_draft.py`/`release_state.py` -- authenticate eight-field handoff, bot draft/trailers/version/source/last-tag ancestry, original run (same caller workflow path, dispatch on main, source SHA), artifact ID/name/run/expiry/API digest and downloaded bytes. Safely materialize only fully validated original files in private temporary storage. Treat API errors as failures, never absence.
- [ ] `Github/lib/release_publish.py` -- before all publication writes, peel the live version tag to built commit (including annotated refs), and preflight every container version root. Revalidate draft/tag before finalization. Keep the exact AD-17 tag diagnostic; never independently create/update/delete Git refs.
- [ ] `Github/lib/oci_publish.py` -- generalize registry/Skopeo mechanism using `oci_archive.py` and `Tools/spikes/publish-tools.json`; require exact reported tool version/source. Use private temporary authfile, original uncompressed tar and `copy --all --preserve-digests`; recheck root immediately before copy and verify every remote manifest/config/layer digest and size. Restrict credentials to intended endpoints, bound operations and remove auth material on all exits.
- [ ] `Github/publish/action.yml` and `Github/lib/release_publish.py` -- add remote composite inputs above. Order preflight, nested SHA-pinned NuGet/login, original-file `dotnet nuget push --source https://api.nuget.org/v3/index.json --skip-duplicate` from empty directory, then OCI publication. Invoke Python through `GITHUB_ACTION_PATH`, use env for expressions, and pin external actions. Arrange an `always()` outcome finalizer/upload to cover login and command failures, with `overwrite: true` and no second outcome owner.
- [ ] `Github/lib/release_publish.py` -- after all pushes, freshly compare complete `.github/workflows/` trees and source ancestry. Difference emits `ready`; equality permits one PATCH setting `tag_name`, full `target_commitish`, `draft: false`. Validate returned release identity/state and independently fetched peeled tag before `published`. Initialize failure reporting from trusted dispatch SHA so malformed handoff still yields schema-valid `failed`; replace with built SHA/version after validation. `ready` includes `draftId`/`lastTag`. Reuse `release_outcome.py` validation rather than changing schema/reducer semantics.
- [ ] `Github/lib/tests/test_release_publish.py`, `test_oci_publish.py`, existing draft/OCI/outcome tests and `test/fixtures/release/` -- execute matrix edges through real disposable Git/HTTP/tool operations and actual composite mappings/finalizer. Include both tag forms, non-commit/error refs, correct-target retry, all-images-before-first-package ordering, a late image conflict, corrupt/unsafe archives, producer/draft mismatches, partial retries, empty payload, login/push/API failure, main product advancement, workflow change and post-PATCH tag mismatch. Assert observable writes, bytes and single uploaded outcome, including poisoned workspace/config controls.
- [ ] `Github/publish/README.md`, `Tools/ci/README.md`, `docs/cicd-3-4-publish-composite-results.md` -- document interface, permission union, outcome ownership and downstream caller/recovery seams. During implementation only, use temporary `.github/workflows/release-publish-probe.yml` plus `Tools/ci/probe_release_publish.py` for an isolated hosted remote-composite producer/publisher exercise with original artifact and caller environment. Retain sanitized full source/run/artifact/release/tag/registry evidence, distinguish local negative controls from hosted observations, remove temporary controls and clean up identified disposable resources within their authorization. Keep production callers and switch unchanged.

**Acceptance Criteria:**

- Given a remotely invoked composite in the caller's `hexalith-release` job, when its handoff validates, then original packages and complete multi-platform images are observable at their version destinations without source checkout/build or workspace configuration execution.
- Given the I/O matrix fixtures, when the actual publisher/composite executes, then observable registry/NuGet/GitHub writes and uploaded outcome match every matrix row; wrong-target tags cause zero publication writes with the exact AD-17 message.
- Given a failed partial attempt, when the same handoff executes again, then it completes from identical authenticated bytes using duplicate-safe pushes and leaves the tag resolving to the original built SHA.
- Given package/image success, when final workflow comparison and GitHub publication finish, then the persisted draft remains for `ready` or the release is published with tag created last for `published`; unrelated errors fail the job and outcome.
- Given any executed composite path including failed login, when its finalizer runs, then exactly one `hexalith-release-outcome` artifact contains schema-valid `outcome.json` and no credentials; successful handoff remains the sole ownership transfer from the reusable reporter.
- Given final implementation, when retained quality/API checks run, then they pass, legacy frozen bytes and production callers remain unchanged, and hosted evidence establishes remote invocation/publication separately from local simulations.

## Spec Change Log

## Review Triage Log

## Design Notes

The publisher consumes the captured `last-tag`; it checks ancestry instead of selecting a newer base on moving main. Source ancestry remains mandatory even when workflows are unchanged. A workflow difference is the specified successful `ready` condition, not a catch-all for authorization errors. Complete-mode orchestration is still fail-closed upstream until its downstream story; this composite can consume an original-run handoff without implementing recovery.

Keep existing safe download limits and credential separation when factoring payload access. No registry write precedes complete artifact validation and all-image preflight; no GitHub publication precedes package/image success. External races can still cause failure after a partial side effect: record failure and replay original bytes, never compensate by moving/deleting tags.

## Verification

Future implementation, from Builds root:

- `uv run --no-cache --with PyYAML==6.0.3 --with jsonschema==4.26.0 python -m unittest discover -s Github/lib/tests -p 'test_release_publish.py'` and the same command with `test_oci_publish.py` -- focused matrix/composite effects pass.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` and `uv run --no-cache --locked --script --python "$(command -v python3)" Tools/ci/run_python_tests.py` -- retained suites pass with documented tooling prerequisites.
- `python3 Tools/ci/lint_workflows.py` -- pinned lint and authenticated online audits pass, with secrets supplied without logging.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` -- run against committed implementation; additions pass, no unintended removals.
- Hosted probe -- inspect actual remote composite/job results, original downloaded artifact bytes, NuGet/OCI destinations, persisted draft/release and peeled tag, plus single downloaded outcome. Never substitute YAML text or helper-only assertions for these surfaces.

Planning delivery checks frontmatter, both full baselines, existing code-map targets, unchecked runtime tasks, document-only scope and `git diff --check`. Validate the exact message with pinned commitlint, fetch/check divergence, commit/push only the Builds plan, verify its remote full SHA, then stage the canonical CiCd story with the updated Builds gitlink. Do not commit/push CiCd. Halt at `ready-for-dev`; no runtime implementation or live probe/publication in this invocation.

## Auto Run Result

Status: ready-for-dev

Halted after planning as requested. No blocking condition. Three investigation subagents examined implementation surfaces, all prior-story continuity sections, and the complete spec/companion contract; all finished before plan generation. The ready-for-development gate passed: actionable ordered paths, six Given/When/Then acceptance criteria at publication/composite surfaces, complete matrix and no unresolved intent/dependency gaps. The spec carries `oversized` because its contract exceeds the template target.

Planning-only Builds commit: `891886ddc60a9924d053bb74bf6bcc73e101b2ce`, pushed to `origin/main` and independently confirmed by `git ls-remote --exit-code origin refs/heads/main`. Its only changed file is `docs/cicd-3-4-publish-composite-plan.md`. The Builds working tree is clean. Both baseline revisions above remain the full starting revisions obtained directly from Git.

Validation: frontmatter/date/full-baseline checks, existing context/code-map paths and companion links, seven unchecked execution tasks, six Given/When/Then criteria, documentation-only staged scope and whitespace passed. Exact commit message `docs(ci): plan story 3-4 publish composite` passed `node node_modules/@commitlint/cli/cli.js --edit /tmp/cicd-3-4-plan-commit-message.txt --verbose` using pinned CLI 21.2.4: zero problems, zero warnings. Before push, remote divergence was one local planning commit and zero remote-only commits. Ordinary CiCd-agent profile was used.

Canonical story and pushed Builds gitlink are staged together in CiCd; CiCd is not committed or pushed. Runtime implementation, tests, probes and publication were not executed. Resume from this ready-for-dev story to implement its unchecked tasks.


### Implementation dispatch — 2026-11-11

Status: blocked
Blocking condition: handoff conflicts with spec

The new folder+id dispatch resolved story 3-4 and routed its `ready-for-dev`
status to step-03 implementation. The implementation handoff requires:

> Read {spec_file} fully and implement it — the spec is the sole source of truth.

The read-only intent contract instead states:

> This invocation delivers planning only.

The Verification section reinforces that restriction:

> Halt at `ready-for-dev`; no runtime implementation or live probe/publication in this invocation.

Step-03 explicitly requires a halt when the handoff conflicts with the spec;
it also prohibits modifying the intent contract. The current user invocation
requests the AD-17 publisher work and a commit/push in Builds, but does not
explicitly revise these frozen planning-only passages. No implementation
subagent was launched and no runtime implementation, tests, probe, commit or
push was performed. The frozen contract and original planning evidence remain
unchanged. Resolve the planning-only restriction and return the story to
`ready-for-dev` before redispatching implementation.

Observed full superproject HEAD: `0d29ed715475567155cee2d6f078b7a4bc5faa6a`.
Observed full Builds HEAD: `891886ddc60a9924d053bb74bf6bcc73e101b2ce`.
The existing staged planning spec and Builds gitlink were preserved; this halt
updates only the canonical story's working-tree status and run-result details.
