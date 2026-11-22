---
title: '5.11 — Agents nonpublishing release rehearsal'
type: 'chore'
created: '2026-11-22'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-18-on-demand-nightly.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Hexalith.Agents Story 5.11 still needs a hosted nonpublishing rehearsal receipt. CiCd has no supported path that runs the audited release build without creating a GitHub draft or publishing packages, and dispatching today's `release.yml` would be a real release.

**Approach:** Record the green CI at Agents `0d98305f91899a088ddad0b0a23a596453913274`, confirm rehearsal remains deferred through Builds `v6.6.0`, write the smallest Builds and CiCd change plus the maintainer decision into the Story 5.11 spec, and leave that story in progress. Do not dispatch `release.yml` or flip `HEXALITH_RELEASE_PUBLISH_ENABLED`.

</frozen-after-approval>

## Implementation Notes

- Confirmed Agents `HEAD` = `0d98305f91899a088ddad0b0a23a596453913274`. Hosted CI run 45004296055 / job 137152331716 (`ci / Build and tests`) succeeded: https://github.com/Hexalith/Hexalith.Agents/actions/runs/45004296055/job/137152331716
- Exact-SHA inventory (`gh api repos/Hexalith/Hexalith.Agents/actions/runs?head_sha=0d98305f91899a088ddad0b0a23a596453913274`) has that CI run only; no `release.yml` run.
- CiCd HEAD `b72e695cc9bfb98a226c4c5c6cafe17825ad0d2e`. Delivered Agents workflows pin Builds `v6.4.4`. CiCd `builds-version` is `v6.6.0` (tag object `d532b1e9b1f595e2c9867bfa9780dccd78c9a2d9`). Shared `release.yml` at `v6.6.0` still has no rehearsal input.
- Kill switch `false` skips version/build/draft (Builds `v6.6.0` `Github/lib/release_state.py` 387–389; delivered Agents `v6.4.4` 380–382). Job `if:` requires `enabled == 'true'`. Dispatch with `true` is a real create-mode release.
- Did not dispatch Agents `release.yml` and did not change `HEXALITH_RELEASE_PUBLISH_ENABLED`. Live variable API is 403; last known `true` from the 2026-11-21 `v2.0.3` publish.
- Recorded the deferred receipt, smallest change, and maintainer decision in Agents `_bmad-output/implementation-artifacts/spec-5-11-restore-reproducible-build-and-host-verification.md`. Left that spec `status: in-progress` and sprint-status key `5-11-restore-reproducible-build-and-host-verification` in progress.
- Blind Hunter review: N=4 from 10.649 kB. Patched the named current SHA, smallest-change files, stale `2b21256` handoff, kill-switch 403 note, and line-number tags. Did not requalify Debug/source at `0d98305` (remaining gate is rehearsal). Did not add artifact id/digest to the four-field receipt the story asked for.

## Review Triage Log

- BH1 three open rehearsal SHAs — medium — patched: `2b21256`/`412528e` rows are historical; current candidate is `0d98305`.
- BH2 missing empty-cache/Debug requalification at `0d98305` — false — user nominated that SHA plus green CI job 137152331716; remaining gate is rehearsal, and `412528e` already holds the source receipt.
- BH3 smallest change omitted outcome reducer/D2 — medium — patched: named `release_outcome.py`, schema, `intentional_skips`, and D2 reject of `rehearsed`.
- BH4 receipt missing artifact id/digest — false — Story 5.11 asked for SHA, Builds version, run URL, and result; the run URL is the durable hosted evidence.
- BH5 live `HEXALITH_RELEASE_PUBLISH_ENABLED` unread — medium — patched: API 403; last known `true` from the 2026-11-21 `v2.0.3` publish.
- BH6 `release_state.py` lines vs tag — low — patched: `v6.6.0` 387–389 and `v6.4.4` 380–382.
- BH7 CiCd spec missing pointers — medium — patched: job URL, inventory command, CiCd HEAD, Builds `v6.6.0` object, Agents spec path.
- BH8 template input/`with` and pre-delivery dispatch — medium — patched with BH3: current `v6.4.4` caller drops extra inputs.
- BH9 stale Debug/source handoff — medium — patched: November 21 fetch failures stay on `2b21256`; `412528e` already passed.
- BH10 "compute a patch" and Agents-only exception — medium — patched: create-mode can publish a new stable version; fleet redelivery remains the 2026-11-18 requirement.
