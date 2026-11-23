---
title: 'Wait for backlogged Delivery runs before dispatching releases'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="requested nightly release repair">

## Intent

Nightly run [45185339361](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45185339361) dispatched zero releases after waiting nearly 45 minutes for a Delivery queue that remained active for more than 75 minutes. Give Nightly up to two hours to observe two complete idle scans, using fresh Actions-read tokens scoped to CiCd and reserving time for all 18 release targets. Persistent activity or unreadable inventory must still block dispatch.

Delivery run [45191312240](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45191312240) failed the active-input audit on a historical path in the EventStore qualification reporter. Record the historical Git blob identity alongside the existing source revision and SHA-256 so Delivery can validate the candidate with the same audit.

</frozen-after-approval>

## Implementation Notes

- The two-hour limit starts when the dispatch controller initializes. The first two slices can yield around 45 minutes when they have yet to confirm clearance. Each slice requires two complete idle scans one minute apart. The dispatch controller and job allow 170 and 180 minutes respectively to cover the wait and all target operations.
- The App policy binds all three mints to CiCd with Actions read. Dispatch and publication mints retain their existing repository and permission scopes.
- The EventStore qualification report now records the historical source Git blob `2b10ee3bdcd3495665e64cbef82f3e4720cfc5ae`. Its recorded SHA-256 matches the blob bytes, and repository-input validation accepts the active script.

## Evidence

- Nightly ran source `2a8f5254881c93703eb252384f5c3d0d680bdd98`, tree `26c9960c15ef832bbd3237d4980193d9d2fde51b`, workflow blob `c134a44a86b10cc2c284fe0d6489dea7f8675426` and controller blob `8acceca41fc4e0cd2a834df9007f964d18ca2def`. Dispatch logged 44 minutes and 15 seconds at the barrier. Delivery runs [45183960433](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45183960433), [45191312240](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45191312240) and [45192481439](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45192481439) overlapped its wait and extended beyond it. [Dispatch artifact](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45185339361/artifacts/14825544696)
- Delivery validation on `646f6d137f4b40c8e4743b5c6836f43444c4601b` rejected the historical path in the EventStore qualifier. The same validation test failed locally before the source identity change and passed afterward. [Validation job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/45191312240/job/137752861811)
- Reviewed source `f0d19e1054c9f25da4e0fe0e27a227a2b1d5e48e`, tree `42f7f8a20b586bb1411545bda72a51cc229b2864`, workflow blob `e10245d9db72f7a201184215df40aba61dcbdd2d`, controller blob `c3f911f18a22db044407b65e465aa20d540668b2` and runtime blob `5490af8890e96cf5ca60cc48901304f0af135237`.

## Review Triage Log

| Finding | Verdict and disposition |
| --- | --- |
| Slow scan at the token boundary | Medium. Check for the renewal boundary before each inventory page. A partial inventory cannot count toward clearance. |
| Interrupted observation could permit renewal | Medium. Each renewal requires the preceding observation step to succeed. |
| Initialization uses part of the two-hour window | Low. The documented ceiling starts at controller initialization, so setup and renewal overhead count against it. A separate timer would add state for the small initialization interval. |
| Expired barrier could mint another token | Medium. Check the aggregate deadline before authorizing a new mint. |
| No rollover case with one idle scan before renewal | Medium. The workflow replay now verifies that the new token must observe two idle scans. |
| No failure case for a missing renewal token | Medium. The replay now fails closed on the second mint and checks that no request uses an older token. |
| Reviewed source identity predates the change | Medium. The policy records the commit containing the reviewed workflow and controllers. |
| Polling interval wording spans renewals | Low. The runbook now defines the interval within each slice. |
| Evidence and result were incomplete | Medium. The record includes run links, exact Git identities and verification results. |

## Verification

- The workflow replay held Delivery active for 116 simulated minutes and dispatched and verified all 18 release targets. The cutoff and renewal cases refused persistent work, unreadable inventory and a missing fresh mint. The slow scan test discarded a partial observation and required two complete scans on renewal.
- Local suites passed with 53 controller tests, 34 workflow tests, 41 runtime tests, 39 repository-input tests, 21 App inventory tests and 78 validation tests. The reviewed inventory accepted seven workflows, ten jobs and 78 mint steps. The locked renderer and pinned actionlint 1.7.12 also passed.
