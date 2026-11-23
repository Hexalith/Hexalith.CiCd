---
title: 'Close five nightly and shared CI findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
baseline_commit: '7bdd093399ded4ff2bb407af0b4f1f4ab3a44892'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="requested five-item batch">

## Intent

Close the five deferred entries for nightly delivery readiness, tagged schema defaults, Builds integration test execution, release-source CI coverage, and cross-repository shared action resolution. The nightly controller must wait for a stable observation of idle delivery. The bump writer must recognize defaults introduced in an actual Builds release. Operators need an attributable record for the three CI questions that earlier hosted runs have answered.

## Boundaries & Constraints

Use the existing dispatch budget, retry cadence, repository registry and artifact formats. Keep the writer's independent, data-only verification of candidate additions. Preserve other deferred entries, production setup files and module revision pins. Validate each historical claim against its own source revision.

## I/O & Edge-Case Matrix

| Scenario | Expected behavior |
|---|---|
| A delivery moves from queued or in progress to waiting after the waiting query | A single apparently idle pass cannot clear the barrier. |
| A busy run or changing inventory interrupts two idle passes | Start the consecutive idle count over. Enforce the existing deadline throughout. |
| The v6.1.0 CI schema adds top-level and nested defaults | For the three previously registered modules, the writer independently produces the same typed configuration as the renderer. |
| A candidate supplies arbitrary values or uses an unsupported default predicate | The writer refuses it. |
| A source coverage entry already has a successful hosted run | Record the exact source, run or job and what it demonstrated. |

</frozen-after-approval>

## Code Map

- `tools/nightly.py` implements the delivery barrier. `tools/tests/test_nightly.py` exercises it with a controlled clock and paginated GitHub responses. `docs/nightly.md` describes dispatch timing.
- `tools/bump_runtime.py` evaluates a bounded subset of JSON Schema for the writer. Builds v6.1.0 introduced both defaults and a `minItems` predicate. `tools/tests/test_render.py` can run the actual renderer at both tagged releases in its existing disposable repository. `tools/tests/test_bump_push.py` covers writer refusals.
- `_bmad-output/implementation-artifacts/deferred-work.md` contains the five entries. Story 2-5 records Builds integration coverage. Story 11 retains adopted-main CI receipts. Historical caller, reusable workflow and release-verifier blobs are available in the corresponding repositories.
- At Builds `5ec1779040606be89306129a7d2b245258c9acd2`, hosted run 42661065183 includes integration job 129312688454. Inspect `builds-release.yml` and `Tools/G4PackageQualification.functions.ps1` at that revision. Commons run 43864267698, job 133288671894, used caller `5169f6b6165482d4b1499ccc5958eb897101be4f` and Builds `v6.0.6`.
- The three setup files at CiCd `87de2b565d5896d7a24d31d065e02f033e5a4adf` cover AI.Tools, Commons and PolymorphicSerializations. Use these historical inputs independently of future registry changes. Both Builds schemas are in the existing tag checkout.

## Tasks & Acceptance

- [x] Given a status transition or an incomplete inventory, when the barrier polls delivery, then dispatch requires two consecutive complete idle scans within its time limit. Cover recovery, timeout and the reset between scans.
- [x] Given the three configurations registered at the v6.0.6 to v6.1.0 transition, when the renderer and writer apply the released schemas, then the actual configuration additions and their JSON types agree. Qualify the relevant condition and preserve fail-closed behavior for unsupported predicates.
- [x] Given the recorded exact-SHA Builds push, when reviewing DW-2 and DW-5, then identify the integration job and establish how release-source verification selected that CI result.
- [x] Given the recorded Commons adoption push, when reviewing DW-6, then tie the successful job to its caller, the called Builds revision and the actions resolved from it.
- [x] Mark all five entries done with their verified scope and the results of the relevant tests.

## Implementation Notes

The controller counts consecutive complete idle scans. Either an active run or an incomplete page resets the count. Each scan and the 60-second wait share the existing barrier deadline and dispatch reserve.

The writer evaluates `minItems` as a nonnegative integer constraint on arrays. The renderer test uses the three setup files as they stood at CiCd `87de2b565d5896d7a24d31d065e02f033e5a4adf` (setup tree `ae4bdababe37a04e033edae413b9e6a6ad778927`). It renders both tags, verifies each peeled tag identity, and compares the complete JSON values and types with the writer's independent traversal. The historical fixture manifest and the maintainer bootstrap both acquire the two tags.

## Review Triage Log

| Finding | Verdict | Disposition |
|---|---|---|
| Blind 1. A pin-only bump bypasses default evaluation | False as a change to the writer contract | Story 8-2 explicitly permits an exact pin substitution. The writer independently checks the tagged schema whenever a candidate adds configuration fields. The producer's full render validation covers omitted output. |
| Blind 2. The dispatch guide promises a terminal state for every run | Low | Describe the two idle observations and the race after the final status read. |
| Blind 3. The deadline test stops before the confirming scan | Low | Cover a last response that arrives at the deadline on the second scan. |
| Blind 4. Historical two-entry manifests lost positive test coverage | Medium | Run successful fixture acquisition with both historical and current manifests. |
| Blind 5. Editing a copied setup could invalidate the historical replay | Low | Bind each embedded input to its historical Git blob. |
| Blind 6. Release metadata alone cannot identify the selected run attempt | Medium | The published v4.47.0 package inventory identifies CI run 42661065183, attempt 1. The release job log independently names the same CI run. |
| Edge 1. Unsupported predicates can be unevaluated for pin-only candidates | False as a violation of the addition check | A pin-only candidate makes no claim about an added default. The test supplies an actual addition to exercise the refusal path. |
| Edge 2. Multiple eligible push runs could share the release SHA | Medium | Use the selected run and attempt in the published qualification inventory to identify the source. |
| Verification gap. Array lengths above the minimum lacked coverage | Low | Exercise two projects against a minimum of one so equality alone cannot pass. |

## Verification

Run the suites below with `run-with-temp uv run --locked --script --python 3.12`. The renderer also passed `tools/render.py --check`.

- The locked local suites passed with 48 nightly controller, 30 nightly workflow, 40 nightly runtime, 52 renderer, 19 bump-writer, 15 bump-producer and 26 Conversations qualification tests. The checked historical setup file bytes matched all three original Git blobs. The parent index retained its module pins.
- All 77 validation compatibility tests and 19 App inventory mutation tests passed. The locked inventory checker covered seven workflows, ten jobs and 76 token steps. All eleven policy digests match the reviewed source revision `145ccf2c89d026748712c310871f8c9d1abfdeaa`.
- The v6.0.6 and v6.1.0 CI schema blobs are `c4f62ea85c6b5992dc0aefcffaba509db2a5563f` and `a1c02759c9d73190b36be217aa6baf9e3b9c8c84`. Both renders and the writer agreed on seven top-level and two nested additions for each module.
- The Builds push and release used source `5ec1779040606be89306129a7d2b245258c9acd2`, tree `1b925620f2d32d1e6a87a4be1d7d3a11b2dc2d22`. The release workflow, shell CI selector and PowerShell verifier blobs are `b76ad5e3128edd4474d71c4574389bca6bf85f69`, `bd25c6153dfea785aa4f8867cc99368d5b182a05` and `51ec7407b900fb3310974108ac64957e9460c3cc`. [Integration report](../specs/spec-cicd/stories/2-5-stage-4-environment-setup-and-hook-points.md) · [Release observation](../specs/spec-cicd/evidence/3-7/settings.json)
- The Commons caller at `5169f6b6165482d4b1499ccc5958eb897101be4f` has tree `e1bfdb71421d68e5fd9e706afc5dd255f5bc8a40` and workflow blob `d6fa984a959daf82a517bde0f1658f2c4158152d`. The called Builds v6.0.6 tree is `81882bd1852cf3c10c7a2b6647b238c8eec22fa8` and its workflow blob is `cd88b194920953524beb2b1329e8ff9ccf0502b7`. The retained log digest for the successful build and tests job is `d039550e30388d3cc74c3f0c53d8a856b4590770f1f45b409cb4818398330b1a`. [Run and job](../specs/spec-cicd/evidence/11/adopted-main-ci-observation.json) · [Log receipt](../specs/spec-cicd/evidence/11/adopted-main-ci-proof.json)
