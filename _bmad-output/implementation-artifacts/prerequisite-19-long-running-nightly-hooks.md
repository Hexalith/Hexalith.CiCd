# Prerequisite for story 19: long-running nightly hooks

The human approved this as a separate prerequisite on 2026-11-16 by asking to
apply the recommendations. ChatBot adoption remains blocked until the capability
is implemented, verified, released and available to CiCd. This file records the
work; it does not claim that the prerequisite has shipped.

## Goal and boundaries

Allow a registered module's genuine product-recovery hook to retain its approved
execution and cleanup allowance within central nightly releases. Preserve the
45-minute hook default and current behavior for existing modules. ChatBot needs
its weekly recovery sweep, retaining its 330-minute outer allowance and shorter
in-process/interrupt deadlines. The legacy release-only M2 committed-state gate
also needs its own unchanged 30-minute allowance on every release. Sequentially
preserving both requires a 360-minute shared hook allowance: the original recovery,
preparation and cleanup capacity plus M2. That is configured capacity, not measured runtime.

Reuse the current controller, authenticated artifact handoffs and fresh tokens
for bounded polling slices. Add only the timeout configuration and bounded wait
continuation needed for the complete release. Do not add another scheduler,
retain tokens past their limits, raise every module's hook timeout, reduce
product scenarios or silently skip failed/due recovery runs.

## Status, 2026-11-18

Items 1–3 below have shipped. Builds commit
`42625e511967a65cec8df045352fdfe027f0ac5f`, first released in `v6.1.0`, adds
`nightlyTimeoutMinutes` (1–360, default 45) and carries it into the hook job.
CiCd renders it at `tools/render.py:619-620` and pins Builds `v6.3.1`. Items 4–5
remain. `tools/nightly.py:140` still sets one 300-minute wait deadline, and
`.github/workflows/nightly.yml:597` still limits the wait job to 330 minutes, with
no continuation. The prerequisite is therefore not shipped. The human chose
to build items 4–5 only after deciding ChatBot's product scope, because
ChatBot's required release cases cannot pass yet. See
[story 19 blockers](../specs/spec-cicd/evidence/19/blockers-20261118.json).

## Current evidence (2026-11-16)

- Builds `v6.0.6` resolves to `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
  Its `.github/workflows/release.yml:nightly-hook` has a fixed 45-minute job.
- CiCd `tools/nightly.py` sets a 300-minute wait horizon and refreshes polling
  authorization through separate slices, each bounded to 40 minutes.
  `.github/workflows/nightly.yml` already supplies those token-mint boundaries.
- ChatBot `tests/Hexalith.ChatBot.IntegrationTests/Recovery/LiveContinuityAspireE2eTests.cs`
  reserves ten serial 20-minute scenarios plus 30 minutes of topology margin.
  `src/Hexalith.ChatBot.Server/Audit/LiveRecoveryValidationOptions.cs` validates
  that complete scenario and restoration budgets fit inside the runner budget.

## Work to implement separately

1. Builds `schemas/hexalith.ci.v1.json`, `Github/lib/ci_config.py` and their
   tests: add one validated, bounded per-module hook-timeout setting, defaulting
   to 45 minutes and permitting ChatBot's 360-minute combined allowance.
2. Builds `.github/workflows/release.yml` and its caller contract: carry the
   validated timeout into the hook job. Preparation, build and cleanup share the
   outer budget; the product deadline must expire early enough for cleanup.
3. CiCd `templates/.github/workflows/release.yml.j2`, `tools/render.py`,
   `tools/check_global.py` and their existing tests: render the selected
   allowance and preserve explicit credentials and permissions.
4. CiCd `tools/nightly.py`, `.github/workflows/nightly.yml`, shared runtime
   and existing tests: allow bounded waiting for the entire configured release,
   including remaining version/build/publication stages after the hook.
   Extend existing handoffs across wait jobs if the required horizon exceeds a
   job budget. Preserve fresh scoped mints, exact run/attempt correlation,
   cancellation, truthful timeouts and final reports for every module.
5. CiCd `docs/nightly.md` and `setup/README.md`:
   explain the allowance and the relationship between hook and total release
   deadlines. Test default/invalid values and simulated slice, deadline,
   cancellation and continuation boundaries without real multi-hour sleeps.
6. Publish Builds through the authorized central release process, then move
   CiCd `builds-version` and render together to the acceptable release containing
   the capability. Validate the committed candidate before delivery. The new
   setting must not be consumed against an older Builds contract.

## Acceptance

- Given an existing module without a timeout override, when rendered and run,
  then its hook retains the 45-minute default and existing release behavior.
- Given ChatBot's 360-minute combined allowance, when its weekly recovery is due,
  then the supported path retains the original 330-minute recovery/preparation/
  cleanup capacity plus the independent 30-minute release-only M2 gate, and can
  complete subsequent release work without expiring the central wait or reusing
  a stale token. A failed M2 gate still permits due recovery after successful
  runtime preparation unless the run was canceled; either failure blocks publication.
- Given a recovery failure, cancellation or exceeded deadline, when the run
  finishes, then cleanup gets its reserved window, publication is blocked and
  the nightly report preserves the failure.
- Given a new accepted Builds release containing this capability, when story
  19 resumes, then it can register the dedicated recovery test project and hook;
  acceptance still requires a real successful recovery execution.
