# Prerequisite for story 19: long-running nightly hooks

The human approved this as a separate prerequisite on 2026-11-16 by asking to
apply the recommendations. ChatBot adoption remains blocked until the capability
is implemented, verified, released and available to CiCd. This file records the
work; it does not claim that the prerequisite has shipped.

## Goal and boundaries

Allow a registered module's genuine product-recovery hook to retain its approved
execution and cleanup allowance within central nightly releases. Preserve the
45-minute hook default and current behavior for existing modules. ChatBot needs
its weekly recovery sweep, with a 330-minute outer job allowance and shorter
in-process/interrupt deadlines. That is configured capacity, not measured runtime.

Reuse the current controller, authenticated artifact handoffs and fresh tokens
for bounded polling slices. Add only the timeout configuration and bounded wait
continuation needed for the complete release. Do not add another scheduler,
retain tokens past their limits, raise every module's hook timeout, reduce
product scenarios or silently skip failed/due recovery runs.

## Current evidence

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
   to 45 minutes and permitting ChatBot's 330-minute allowance.
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
- Given ChatBot's 330-minute allowance, when its weekly recovery is due, then
  the supported path can complete recovery and subsequent release work without
  expiring the central wait or reusing a stale token.
- Given a recovery failure, cancellation or exceeded deadline, when the run
  finishes, then cleanup gets its reserved window, publication is blocked and
  the nightly report preserves the failure.
- Given a new accepted Builds release containing this capability, when story
  19 resumes, then it can register the dedicated recovery test project and hook;
  acceptance still requires a real successful recovery execution.
