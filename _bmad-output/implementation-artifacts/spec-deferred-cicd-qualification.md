---
title: 'Resolve five deferred CiCd qualification findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="requested five-item batch">

## Intent

Close DW-45 and DW-46 by running the committed evidence check independently of
Delivery. Close DW-35 by using the existing read-only Nightly job token for
trusted Builds REST verification. Close DW-42 by relocating the live Tenants
qualification entry points and clarifying the historical EventStore replay
record. Verify the Git capability required by the perimeter repair and document
the minimum for the deferred story 4-1 finding.

</frozen-after-approval>

## Implementation Notes

- Baseline CiCd commit `97538b46caec91945d25b496ff1135bab475f2b0`, tree
  `dd6f0531a915405f403dad9854b966975b1de95d`. Reference checkouts keep their
  committed gitlinks while their local main branches track current upstream.
- Main advanced to `8609f8c09d0fbe16ea4c7b7755dd3d28b030aa87` during
  implementation. Reviewed source `848b5c2d3497bdeae1aebc94e77b2cd1f20872d7`,
  tree `ae641be1eeb2daa5db4c424bf45fc66b440b661a`, includes the new upstream
  Nightly dispatch budgets. The App policy binds this source and the existing
  delivery and Nightly token scopes.
- Evidence runs on PRs and main pushes without the Delivery concurrency group.
  The read-only job still checks the exact event range. Both Nightly observers
  retain their existing Delivery workflow identity.
- The three Nightly initialization steps use the job token already used for
  handoffs. It is used only for the fixed Builds REST reads and handoffs.
  Git transport and App permissions are unchanged.
- Tenants' preflight and test now run from `tools/`. The EventStore prerequisite
  verifier reads the relocated configuration fixture with identical blob
  `450e1e9ec4e7a9d217f885817dc2bdd50d554856`. Prior replay sources remain
  retrievable from the recorded historical revision.
- The Builds qualification ran `PerimeterTests.test_attributes_come_from_selected_index_not_head_or_dirty_worktree`
  from `Github/lib/tests/test_perimeter.py` with each built Git executable
  first on `PATH`. Git v2.40.4 at `54a3711a9dd968a04249beef157393d64b579d64`
  failed at the dirty-worktree clean filter (log SHA-256
  `0580128bb7b595ddf185c914dbd4592690021a2df39d3f2bfc967cfdf3bb6b0f`).
  Git v2.41.0 at `fe86abd7511a9a6862d5706c6fa1d9b57a63ba09` passed the same
  test (log SHA-256
  `741e0352e79b557723f02184f46f50f9b745e519748700e73a17a13b77de3b6b`).
  Both used Builds v6.6.2 commit `2d9ef8b454ff897daca0149f3549844f584b634a`,
  perimeter blob `6049279065c27a36ff16f09184375a7fbe480e64`, and test blob
  `82d4ac9e72d628fd87a76c919b9ac954606fac6c`. Git v2.41.0's release notes
  blob `8a9e17016e45ee0ec6a579b231c0184043eee0e7` documents the feature,
  and its attribute reader blob `d45d34058df639c9a6c3fc80f51fa864611e5b21`
  reads `GIT_ATTR_SOURCE`.

## Review Triage Log

- Medium, fixed. The relocated EventStore verifier identifies the original
  source by a repository path, commit, and matching SHA-256.
- Low, fixed. The Nightly guide limits Evidence coverage to eligible push
  events and explains the files and commits allowed for job-token pushes.
- Medium, unverified in this workflow. The cross-repository Builds read
  authorization is modeled in the Nightly fixtures. Hosted initialization
  with the revised step and its job-token permissions remains to be observed.
  The existing Nightly bump path already uses a job token for public Builds
  REST reads. [Successful bump job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44715684274/job/136229755721)
- Low, fixed. The historical EventStore audit reference uses the pinned packet
  revision. The Tenants procedure uses the relocated test entry point.
- Low, fixed. The Git compatibility receipt names the focused Builds test and
  how each compiled Git executable was selected.

## Verification

- Evidence workflow blob `1954f294085987e714149e959a845c9d92534ff7`
  and checker blob `2fa676160473f52156dee73419104a569be21ad7` passed the
  26 Delivery workflow and eight evidence checker tests. The source diff
  passed the checker with the exact main push baseline.
- The App inventory check reviewed seven workflows, ten jobs and 76 token
  requests. All 21 inventory tests passed. Pinned actionlint 1.7.12 accepted
  all eight parent workflows. The locked renderer found no drift.
- All 41 Nightly runtime tests passed, covering the four authenticated Builds
  GETs, credential-free Git calls and authorization refusal.
- The rebased source passed 51 Nightly controller, 30 Nightly workflow and 21
  Delivery observer tests. The 18-target workflow fixture verified that each of
  the three initialization phases made one authenticated Builds proof.
- The 15 Tenants preflight tests, the relocated fixture check and the 17
  EventStore fixture tests passed. The moved EventStore snapshot verifier's
  help and malformed-identity refusal
  passed. The refusal made zero subprocess calls. This was local verification
  of the relocation.
- Pinned Builds v6.6.2 commitlint 21.2.4 accepted both commit messages.
