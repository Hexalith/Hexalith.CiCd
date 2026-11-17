---
title: 'Verify EventStore producer readiness for Projects query contracts'
type: 'bugfix'
created: '2026-11-17'
status: 'in-progress'
route: 'dispatch'
baseline_commit: '92e4e0b0acf0a256078c330419734eafa69b84ed'
context:
  - '/home/administrator/projects/hexalith/cicd/AGENTS.md'
  - '/home/administrator/projects/hexalith/cicd/docs/pre-adoption-publication.md'
  - '/home/administrator/projects/hexalith/cicd/docs/ordered-module-adoption.md'
review_loop_iteration: 2
---

<frozen-after-approval reason="user answered yes to extending the repair to EventStore release readiness while retaining normal nightly publication">

## Intent

Prepare EventStore release readiness for the query-contract API required by Projects. Verify the current producer source and repair a demonstrated product defect if necessary. Keep normal nightly publication and all current audit, compiler, test and security enforcement. No manual release, adoption, synthetic published version, compatibility shim or attribute deletion is authorized. Do not weaken product checks or edit owned module workflows/configuration. Preserve every concurrent change and job.

## Tasks & Acceptance

- [x] Create a reproducible source-bound verification helper and result report under `_bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/`. Given the frozen producer `3b2350e7c1fff640131f8101596c78a59e31a03f` and its Builds pin `16cf0db6f843eb4defdc87105804d42eded634d6`, when creating disposable standalone copies, then use those exact committed inputs, record their identities and initialize no nested submodules.
- [x] Run ordinary Release/package restore/build with auditing, analyzers and warnings-as-errors for whole Contracts and RestApi.Generators test projects plus Gateway compilation. Given the existing query generator's functional compilation tests, when running both whole test projects with their supported runner, then retain exact totals, native exits and every skip/unrun/failure without changing filters or assertions.
- [x] If a demonstrated product failure occurs, make its smallest correction from freshly fetched main in an isolated persistent worktree and rerun relevant checks. Given no failure, when the checks pass, then leave product source unchanged and do not manufacture a correction. Preserve the original failure if a later source or attempt changes.
- [x] Write a concise readiness report with API/source/package boundaries and the central release route. Given passing focused producer checks but unavailable adoption/publication prerequisites, when reporting readiness, then distinguish the verified API from complete release acceptance and identify concrete remaining gates. No release, adoption, module push or parent-gitlink change occurs during implementation.

</frozen-after-approval>

## Code Map

- Producer objects: `/home/administrator/projects/hexalith/cicd/references/Hexalith.EventStore`; its shared checkout remains old and clean. Freeze the stated fetched commit without checking it out there.
- Producer `Directory.Build.props`, `Directory.Packages.props`, `.editorconfig`, `.gitattributes`, `global.json`, `AGENTS.md` and normal CI show package-mode properties and build guidance; inspect committed bytes.
- `src/Hexalith.EventStore.Contracts/Queries/QueryResultContractAttribute.cs`: new public API, absent from published 5.1.1/5.2.0.
- `tests/Hexalith.EventStore.RestApi.Generators.Tests/TypedGatewayQueryGenerationTests.cs`: two tests actually compile generated typed bindings and retain existing REST route behavior. Run the entire project, not these two alone.
- `tests/Hexalith.EventStore.Contracts.Tests/` and `src/Hexalith.EventStore.Gateway/`: whole contract regression and actual Gateway compilation.
- `scripts/verify-release-source.sh`, `tools/release-packages.json`: exact-main green CI/commitlint and fourteen-package release inventory.
- Build dependency objects are in root-declared `references/Hexalith.Builds`. Disposable standalone dependency copies beneath `TMPDIR` are permitted; do not initialize any nested submodule. If another dependency is needed, use its actual producer gitlink and root-declared object store; record it.
- Root setup currently selects three other modules. EventStore has no delivered ref or adoption config and no approved pre-adoption push substitute. These are publication blockers, not permission to invent configuration or claim adoption.

## Implementation Notes

- The user's original push-all authorization remains, but publication stays gated. Implementation performs no Git commits, pushes, dispatches, credential changes, releases, tags or live configuration writes. Do not edit another session's evidence or shared worktree files.
- Run ad hoc jobs with `run-with-temp`; all clones/build outputs remain under its private `TMPDIR`. Save useful logs/results to the new evidence packet. Wait for children and wrapper cleanup before returning.
- Projects preparation is already published at `3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b`; never reapply old patches or retest it with unreleased-package/source fallback. Current published SDK remains 5.2.0. The current source's missing package API blocks consumer acceptance.
- A concurrent guarded-write job in `/home/administrator/projects/hexalith/eventstore` must remain untouched. Other sessions keep advancing producer main; report the frozen tested source and any later observed head rather than silently changing subjects or claiming latest-main acceptance.
- Completed evidence: all three Release builds pass; generator 203/203 passes. Whole Contracts retains native exit 2 with 1,805 passed, two failed and two skipped. Supplemental fourteen-package consumers and reminder probes pass; direct package authority passes 73 projects in 365 seconds within the unchanged 480-second bound. No product logic defect was demonstrated. All four attempt helpers, inputs, native results and cleanup are source-bound in the packet.
- CiCd records the governance-gate disposition and a checked, unapplied migration patch for agent-tooling assertions, preserving actual commitlint enforcement. Original whole-suite failures remain visible; complete release acceptance is false and normal nightly eligibility still awaits ordered adoption.

## Review Triage Log

- BH1 — medium, bad_spec: inherited package/repository selectors can redirect verification inputs. Quarantine documented selectors, including EVENTSTORE_PACKAGE_CONTRACT_DIR and GIT_INDEX_FILE, before any Git/build job; retain intended credential profile and ordinary platform settings.
- BH2 — medium, bad_spec: ordinary subprocess calls lack the authority command's cancellation/descendant custody. Use one owned-job lifecycle for all jobs, preserving their native exits and original time budgets.
- BH3 — medium, bad_spec: a reproduced child escaping its process group survived a false fully-waited report. Track owned descendants across session changes and prove foreign processes survive cleanup.
- BH4 — medium, bad_spec: positive internally consistent counts do not prove the frozen suites or both required typed-query compilation cases ran. Bind qualification to their captured inventories and required case names.
- BH5 — medium, patch after re-derivation: final clean diff is against current HEAD rather than the frozen commit. Recheck every final HEAD and compare against its recorded revision.
- BH6 — medium, bad_spec: external resolved dependency graphs were discarded. Capture compact libraries/content hashes and sanitized effective sources in future attempts; explicitly label the original unavailable graphs rather than inventing historical provenance.
- BH7 — medium, bad_spec: general package consumers do not reference the new attribute or generated binding. Add a synthetic consumer of real candidate Contracts/Client/generator archives; keep Projects and published pins untouched.
- BH8 — medium, patch after re-derivation: integrity/control receipts lack runnable audit commands. Retain a small executable evidence/negative-control verifier and its exact invocation.
- BH9 — low, patch after re-derivation: earlier API-absence evidence lacks exact tool/version and a known-present control. Add a read-only reproducible inspection with pinned tool identity and positive control, preserving original logs.
- BH10 — low, patch after re-derivation: account proof retains unnecessary profile/contact fields. Keep only identity and relevant permission context; remove unrelated personal fields without rewriting history.
- EC1 — medium, bad_spec, grouped with BH2/BH3: SIGINT during process.wait reproduced an orphaned child. Cleanup must run in finally and reap the owned tree before scratch removal.
- EC2 — medium, bad_spec, grouped with BH1: inherited package-contract directory supplies unrecorded archives. Baseline must clear it and local-package mode must provide only its own generated inventory.
- Verification-gap review — no findings.
- B2.1 — high, bad_spec: three independent isolated controls proved that a foreign child can orphan a new descendant between scans and have it killed as owned. Shared-supervisor adoption is ambiguous; isolate each job beneath its own dedicated custodian.
- B2.2 — medium, bad_spec: six of eleven captured assets are committed Windows history, not fresh Linux restores. Capture evaluated active assets explicitly; preserve the flawed capture and correct current aggregation.
- B2.3 — medium, patch after re-derivation: GIT_CONFIG_GLOBAL, GIT_CONFIG_SYSTEM and GIT_TEMPLATE_DIR can redirect temporary Git configuration/templates. Quarantine overrides while preserving intended credential-profile selection.
- B2.4 — medium, bad_spec: evaluated policy accepts added NU1903/NU1904 suppressions. Bind permitted security-warning exceptions to the frozen baseline and reject additional suppression.
- B2.5 — medium, bad_spec: query-package mode bypasses evaluated analyzer/audit policy. Evaluate and validate the actual producer and synthetic projects used by that mode.
- B2.6 — medium, bad_spec: clean tracked diffs do not reject extra source/build inputs. Reject unexpected untracked input files outside explicitly designated disposable build outputs.
- B2.7 — medium, patch after re-derivation: graph-capture failure can replace the original error and omit final result metadata. Save the primary failure first and attach capture errors separately.
- B2.8 — medium, patch after re-derivation: interrupted API inspections omit the command/cleanup receipt because registration follows execution. Register first and preserve lifecycle errors before propagation.
- B2.9 — medium, patch after re-derivation: the audit omits query-probe input/project/nuspec integrity. Hash all new retained inputs before execution and replay them; label historical missing provenance honestly.
- B2.10 — medium, patch after re-derivation: readiness aggregation can drift independently of audited receipts. Cross-check acceptance fields, counters, identities and source references against those receipts.
- B2.11 — low, patch after re-derivation: downloaded inspector hash is not tied to the separately installed payload. Install the captured archive from an isolated local feed and verify the executed payload identity.
- E2.1 — high, bad_spec, grouped with B2.1: a foreign parent double-forked after the baseline; cleanup killed/reaped its unrelated descendant while reporting custody success.
- E2.2 — medium, patch, grouped with B2.8: an actual JobInterrupted control left the inspection's commands list empty.
- G2.1 — high, bad_spec, grouped with B2.1: the verification-gap review independently reproduced the foreign-orphan kill; current foreign controls keep their parents alive and miss the race.

## Spec Change Log

- Iteration 1: review exposed missing lifecycle, input and feature-package provenance details in the non-frozen implementation plan. Re-derive the active helper from the preserved attempt-04 helper, adding the constraints below. Avoid false frozen-input/fully-waited/feature-package claims. KEEP every immutable original attempt, failure/skip, source identity, guard, audit, timeout, native exit, successful source/package proof, owner classification and unapplied proposal. No producer source, test assertion, public pin, release route or live configuration changes.
- Iteration 2: shared-supervisor orphan adoption cannot prove ownership when a foreign tree forks between observations; broad asset discovery and incomplete policy/input/audit bindings also overstate provenance. Re-derive only active verification code in the isolated publication worktree, using the saved pre-review-2 helpers as scaffolding. KEEP all original attempts, failures, successful source/API/package proofs, precise custody limitations, minimal account metadata, owner proposal, CLI compatibility and frozen identities. New proof is limited to the changed helper controls, actual query-package boundary and public API inspection; do not repeat the large producer suites or unrelated consumers.

## Iteration 2 Working Root and Implementation Constraints

- All further edits and outputs belong to `/home/administrator/projects/hexalith/cicd-eventstore-readiness-20261117T004913Z`, on the already prepared isolated CiCd branch. Do not edit the shared original `/home/administrator/projects/hexalith/cicd` checkout. The packet and this spec are copied into that worktree; its top-level EventStore, Tenants, Builds and AI.Tools dependency objects supply the frozen source. No nested submodule initialization.
- Implement per-job custodian process isolation. The main helper must never adopt/classify unrelated child trees; a dedicated child supervisor becomes subreaper for only one job and owns its descendants across forks/sessions/cleared environments. Preserve parent foreign jobs, native exits and cancellation receipts; private IPC is internal and must contain no credential values in saved evidence. Test the exact foreign-orphan race, early/active cancellation and escaped descendants. Keep original limits, especially authority 480 seconds; fail explicitly on incomplete custody.
- Capture only explicitly evaluated active ProjectAssetsFile paths, never arbitrary rglob results. Distinguish current graphs from tracked history and correct the old eleven-project claim with a superseding record. Preserve original captures. Validate actual producer/consumer Release, package, audit and analyzer settings, including the exact frozen permitted vulnerability-warning exceptions. Quarantine ambient policy and Git overrides without switching credential profiles.
- Verify no unexpected source/build inputs exist beyond the frozen tracked tree and explicitly designated generated outputs. Preserve primary exceptions, failed commands, native exits and cleanup receipts before best-effort graph/error capture.
- Bind retained query inputs, project files, nuspecs, graphs and generated output through manifests; replay aggregation against original receipts. A new narrow query-package run may establish fresh complete provenance; prior missing data cannot be invented. No whole producer suite or unrelated consumer rerun.
- Install pinned public inspector from the exact downloaded local archive and verify its actual executed payload. Retain known-present and missing-type controls, tool/version/commands, and interrupted-command receipts. Run only this narrow inspection and relevant utility controls.

## Re-derivation Code Map

- [x] Restore and harden the active helper's input, lifecycle, identity, inventory and graph boundaries with executable controls.
- [x] Prove the requested API through a real synthetic package consumer and preserve runnable public-package API/evidence inspection.
- [x] Refresh truthful reports, minimize authentication metadata and retain all original evidence unchanged.

- Active helper: `_bmad-output/implementation-artifacts/evidence/eventstore-release-readiness-20261117/verify.py`. Its preserved scaffold is `attempt-04-authority/verify.py` in that packet. Restore it with the existing CLI and frozen identities; retain all historical versions and receipts unchanged.
- Quarantine Git repository selectors and the documented package-contract selector. Preserve configured credential-profile selection. Record effective verification inputs without secrets. Validate using isolated sentinel indexes/package selectors, never a real user index.
- Apply exception-safe owned-descendant cleanup to ordinary and bounded jobs, including SIGINT and descendants starting new sessions. Preserve pre-existing unrelated children; record cleanup failures as failures. Keep the authority limit 480 seconds. Test native success/failure, timeout, cancellation, session escape and unrelated-process survival under optimization.
- Bind frozen suite qualification to the recorded 203/1809 inventories and both actual typed-query test names. Recheck final repository HEADs and diffs against recorded commits. Replay retained reports and synthetic incomplete cases without rerunning the large producer suites.
- Save compact resolved package libraries/content hashes and sanitized source configuration for new attempts. Historical graphs are unavailable; annotate that limitation without relabeling past evidence.
- Add one isolated query-API package probe using real locally packed Contracts, Client and RestApi.Generators archives from the same frozen producer. Compile an attributed synthetic owner Contracts assembly and a consumer with the packaged analyzer, requiring the generated typed binding. Record the actual resolved graph and package hashes. Reuse existing package helpers where appropriate; no Projects fallback or producer source change. Run only the package work needed for this new boundary, not the whole producer suites or unrelated consumers.
- Persist runnable evidence/control validation and exact command/version/known-present control for public package API inspection. Keep credential/profile metadata minimal. These are internal verification artifacts; add no public SDK API or production workflow.
- Parent/original adoption and publication gates remain blocked. Re-derivation validates the helper and new package boundary only; supplemental success never makes the original Contracts run green.
- Re-derivation verification: the real three-package query consumer compiles the new attribute and generated typed binding; pinned inspector 0.28.0 reproduces public absence with known-present controls. Executable evidence controls pass, followed by 18 focused cancellation/adoption/foreign-child/layout controls after removal of process-environment scanning. Historical graph/custody limitations remain explicit; no producer or broad package rerun was used to mask old results.
