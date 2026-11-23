---
title: 'Allow Nightly to wait for a busy Delivery queue'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="requested nightly release repair">

## Intent

Scheduled Nightly run [45159188381](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45159188381) timed out before dispatching any releases. Its Delivery barrier started at 10:53:12 UTC. The last blocking Delivery run [45163448014](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45163448014) completed at 11:29:43 UTC, 36 minutes and 31 seconds later.

Give the barrier time to cover that queue while still requiring two complete idle scans, honoring the Actions-read token limit and reserving time for selection and dispatch of every target. Verify recovery after the observed queue duration and refusal when the barrier expires. Preserve the existing release eligibility, CI, security and publication checks.

</frozen-after-approval>

## Implementation Notes

- The barrier can wait 45 minutes. The dispatch controller and job allow 95 and 105 minutes respectively. The barrier respects the existing token budget and reserves time for 18 selections, serial one-minute mints, per-target dispatch operations, and finalization.
- The workflow fixture holds Delivery active for 43 polls, then requires two idle scans before dispatching the 17 modules and Builds with slow serial mints and dispatch requests. Controller tests cover a persistently busy queue, incomplete inventories, late responses and a token too old to complete both scans.

## Review Triage Log

| Finding | Verdict and disposition |
| --- | --- |
| Serial token mints can consume the time reserved for later slots | High. Reserve each mint and each target operation. Include later mints in the per-slot budget and exercise all slots with 59-second mints and 50-second dispatch responses. |
| The workflow test compares against a literal job timeout | Medium. Read the dispatch timeout from the workflow under test and check controller headroom. |
| The original replay could pass with a 40-minute cutoff | Medium. Confirm idle at 44 minutes in the workflow replay and check a response arriving at the deadline in the controller suite. |
| The timeout message omits the limiting budget | Low. Record the limiting budget in barrier failures. Actions records the step's elapsed time. |
| The record lacks exact source identities and results | Medium. Record the affected commits, objects and verification results below. |

## Evidence

- Failed source `9e6109595c795b7ac6f86066af4b787a09e310dc`, tree `7bc1c300677593ef3f86abfd83a9885dae0f601a`, workflow blob `03e4599a0409d86ea10733cbd2bb17ea02a68391` and controller blob `4472e31330d9f996ab091a2c8033f5af5fd6428e`. Dispatch state recorded eight failed target rows and zero release run IDs. The Actions archive digest was `sha256:05cbea4ac978ccda5e51ead27241164c61c8210be4ea03a4aade67ac02b9f576`. [Dispatch artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45159188381/artifacts/14812663416)
- Reviewed source `3d097433140c3f885e33a7cb3d413005e560d70c`, tree `dd3f6c277896e28b33427a332fb7515625e1b002`, workflow blob `a720fad3e854298fed57e544215c26a5d6b2ef1a` and controller blob `4cae6862d651a75219e709c44d7fb1268d7c185a`. The App policy records the dispatch job timeout and controller SHA-256 `f07921b472c856fe09c481f33e2ce9ec557ee253e08251fe952bc5db6afdc93e`.
- Policy blob `438912fb3128e09d4b4b1a2cc33287feab7c6532`. Controller and workflow test blobs `8a939fab34c5da1228335fc50546fdb499c51020` and `8015c42627df281e8b589b3cbeef4a859dbf3741`.

## Verification

- The all-target replay confirmed idle at minute 44 and dispatched 18 targets with near-limit mints and slow API responses. All four focused workflow and job-timeout checks passed.
- All 51 Nightly controller tests and all 30 Nightly workflow tests passed. Log SHA-256 digests are `d4e4021f9345a82ef0f946c4b8af72c74da13cfbd5929ce6179f02f2eca66e1d` and `40433a139cb51fb9c80497b24404e35aab901fe28836ec1eebce916134234259`, respectively.
- The App inventory accepted seven workflows, ten jobs and 76 token steps. All 21 mutation tests passed (log SHA-256 `0e5fcb8c83542353041903914f9aeb8fb1de299ab141f426d79afdeea52d7629`). The rendered output check, 78 validation tests, 40 Nightly runtime tests and pinned `actionlint` 1.7.12 also passed.
