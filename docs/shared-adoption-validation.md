# Shared adoption validation — 2026-11-16

The shared implementation is present in the owning Builds/CiCd repositories.
It is **not yet qualified for delivery**. No EventStore, FrontComposer or Tenants
release, package/image publication, registration or cutover was performed by this
work. The selected production Builds contract remains `v6.0.6`.

Supported fields, examples and execution boundaries are in
[setup/README.md](../setup/README.md) and Builds'
[module adoption guide](../../builds/docs/module-adoption-execution.md).
[Ordered adoption](ordered-module-adoption.md) records the remaining product work.

## Evidence and source boundaries

Disposable verification ran under `run-with-temp`; clones, package feeds, reports
and build outputs were beneath its private `TMPDIR`. Useful logs remain in
`builds/artifacts/adoption-shared-2026-11-16/`. This is ignored local evidence;
the table below summarizes it without adding generated bulk to either repository.

Concurrent work advanced Builds during implementation. The complete Python
suite snapshot is synthetic commit `41b99f017ef83d2c36091942f6ec09b35e614566`
based on `05bda4e01d70afacb5048d5c336f383a301c0974`. Final additive deltas
(public schema compatibility, TLS trust export, explicit historical Dapr setup)
have separate focused checks. Final API candidate
`d9bba4bfe55d7cff6f70eff5134d704d2403aedf` is based on
`42625e511967a65cec8df045352fdfe027f0ac5f`;
[candidate-api.json](../../builds/artifacts/adoption-shared-2026-11-16/candidate-api.json)
binds those changed bytes. Synthetic commits exist only in disposable verification
clones and are not releases. Their exact commit messages passed the owning pinned
commitlint CLI. No owning-workspace commit or push was performed during
implementation; later source publication does not qualify infrastructure delivery.
Other concurrent work subsequently changed `module_preparation.py` and its tests;
those bytes differ from the renderer snapshot. This report binds the stated
snapshots and focused deltas, and cannot qualify a later combined repository HEAD.

## Passed checks

Commands are run from the owning repository unless an evidence helper is named.
Helpers are retained beside the logs and snapshot the actual candidate bytes.

| Check | Command / result | Evidence |
| --- | --- | --- |
| Complete Builds Python suites | In an isolated candidate: `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py`, then Python `3.14`; both **16/16 groups passed**, including 726 shared-library tests each. | [3.12](../../builds/artifacts/adoption-shared-2026-11-16/final-python312.log), [3.14](../../builds/artifacts/adoption-shared-2026-11-16/final-python314.log) |
| Final environment/tool deltas | `run-with-temp env PYTHONPATH=Github/lib/tests uv run --no-cache --with PyYAML==6.0.3 --with jsonschema==4.26.0 --python 3.12 python -m unittest test_ci_prerequisites test_ci_environment test_qualification_tools -v`; same suites on 3.14. **74 passed each**. | [3.12](../../builds/artifacts/adoption-shared-2026-11-16/final-delta312.log), [3.14](../../builds/artifacts/adoption-shared-2026-11-16/final-delta314.log) |
| Native report/coverage execution | `run-with-temp python3 artifacts/adoption-shared-2026-11-16/qualify_native_reports.py --multi`, then `--multi --vstest`: real .NET 10/11 fixtures, all four tests per mode, fresh TRX/Cobertura, three source lines and two branches validated. | [MTP](../../builds/artifacts/adoption-shared-2026-11-16/final-native-mtp.log), [VSTest](../../builds/artifacts/adoption-shared-2026-11-16/final-native-vstest.log) |
| Candidate package mechanics | Existing shared product-validation tests passed in the complete Python suites, including isolated restore/build/run failures and candidate signature/metadata checks. No consumer mechanics were copied into module actions. | [Full suite](../../builds/artifacts/adoption-shared-2026-11-16/final-python312.log) |
| Dependency/signature checks | Isolated `npm ci --ignore-scripts` and `npm audit signatures`: exit 0. | [Install](../../builds/artifacts/adoption-shared-2026-11-16/npm-install.log), [Signatures](../../builds/artifacts/adoption-shared-2026-11-16/npm-signatures.log) |
| Public API compatibility | `run-with-temp python3 artifacts/adoption-shared-2026-11-16/qualify_candidate_api.py`: exact Git-object checker against `v6.0.6`, **2,741 entries, no removals**. The earlier combined wrapper's API failure preceded restoration of the common runner schema property; this final rerun passes. | [Final API](../../builds/artifacts/adoption-shared-2026-11-16/final-public-api.log) |
| Builds workflow/security audits | `run-with-temp python3 artifacts/adoption-shared-2026-11-16/run_authenticated_check.py python3 Tools/ci/lint_workflows.py`: pinned actionlint/zizmor pass; **0 new findings**, 10 exact previously frozen composite findings. No new waiver added. | [Final lint](../../builds/artifacts/adoption-shared-2026-11-16/final-workflow-lints-delta.log) |
| Exact candidate rendering | `run-with-temp python3 artifacts/adoption-shared-2026-11-16/qualify_render_contract.py`: actual tagged schema/strict reader/runtime interfaces, deterministic render, four isolated routes, 360-minute mutation, private authority and platform additional-project cases pass. | [Bound bytes/results](../../builds/artifacts/adoption-shared-2026-11-16/candidate-render.json) |
| CiCd renderer/validator | Locked `tools/tests/test_render.py`: **43 passed**; `tools/tests/test_validate.py`: **52 passed**. Generated qualification fixtures: **nine** workflows pass pinned online audits, including private and matrix callers. | [Renderer](../../builds/artifacts/adoption-shared-2026-11-16/renderer-final.log), [Validator](../../builds/artifacts/adoption-shared-2026-11-16/cicd-validate-tests.log), [Qualification lint](../../builds/artifacts/adoption-shared-2026-11-16/qualification-lint-final.log) |
| Existing production rendering | `run-with-temp uv run --locked --script --python 3.12 tools/render.py --check`: exit 0 against existing selected `v6.0.6`; existing registrations/callers unchanged. | [Render](../../builds/artifacts/adoption-shared-2026-11-16/cicd-render-final.log) |
| Real official tool installation | `run-with-temp python3 artifacts/adoption-shared-2026-11-16/qualify_real_tool.py`: official pinned Dapr CLI archive/executable verified and `--version` succeeds. No runtime initialization or product qualification claimed. | [Tool smoke](../../builds/artifacts/adoption-shared-2026-11-16/official-tool-install.log) |
| Release compilation and .NET diagnostics | Shared `restore_and_build` passes with Release/package-only properties and auditing/analyzers. Evidence project: **191 passed**. Diagnostic four-processor rerun of four failed classes: **148 passed**. Whole tooling integration project: **1 passed, 12 existing opt-in live skips**; these skips establish no live qualification. | [Focused details](../../builds/artifacts/adoption-shared-2026-11-16/focused-dotnet.log), [Result](../../builds/artifacts/adoption-shared-2026-11-16/focused-dotnet-result.json) |

Scoped `git diff --check` passes in both owning repositories. Final schema checks
also pass (31 cases). Coverage tests retain Tenants' exact strict `>80` line gate
and named `>=100` branch gate, FrontComposer reporting without a new threshold,
missing/modified report failures, and product-exit precedence. Local checker
regressions exercise the same shared stage 2/3 functions and unit coverage gates;
no real product's standalone local-check success is claimed before adoption.

## Failed or incomplete required checks

`run-with-temp python3 ../builds/artifacts/adoption-shared-2026-11-16/run_authenticated_check.py uv run --locked --script --python 3.12 tools/check_global.py`
from CiCd exited **1**. Its production render, bootstrap, schema/interface,
acceptable existing publication and workflow audit checks pass. It reports:

- Uncommitted render inputs: `ci.yml.j2`, `release.yml.j2`, `qualification.yml.j2`.
  This work intentionally leaves changes reviewable without staging/committing.
- `tools/tests/test_deliver.py` and `test_delivery_workflow.py` each exceeded the
  checker's 600-second bound.
- Five failing subcases in
  `test_builtin_process_imports_preserve_ordinary_environment_and_argument_reads`
  in `test_scan.py`. The scanner and its tests have concurrent changes outside
  this implementation; no unchanged-baseline attribution is claimed.

See [the complete global log](../../builds/artifacts/adoption-shared-2026-11-16/cicd-global.log).

The complete Builds .NET project runs found module failures on this host.
`run-with-temp python3 artifacts/adoption-shared-2026-11-16/qualify_candidate_api.py --dotnet`
completed Release restore/build and the 191-test evidence project. The complete
module project finished **3,118 passed, 5 failed, 4 existing conditional skips**
in 25m24s, native exit 2. The shared runner correctly fails the unit stage before
integration. Failing assertions are:

- `McpCliBuildIsBoundedByTheStartupDeadlineAsync`;
- `PlatformPreparationUsesRemainingDeadlineAsync` (`preflight`, `model`);
- `DeadlineAtFinalReadyCommitRefusesSuccessAsync`;
- `NativeOutcomeControlsLocalCleanupAsync` (source mode, cleanup failure case).

See [the broad log](../../builds/artifacts/adoption-shared-2026-11-16/final-dotnet.log)
and [snapshot/result](../../builds/artifacts/adoption-shared-2026-11-16/final-dotnet-result.json).
The same command with `DOTNET_PROCESSOR_COUNT=4` finished **3,121 passed, 2 failed,
4 existing conditional skips** in 25m21s, native exit 2. Its failures are
`PublicCommandWritesResolvedMappingIntoEnginePlanAsync` (`run`, `package`) and
`McpCliBuildIsBoundedByTheStartupDeadlineAsync`.
See [four-processor log](../../builds/artifacts/adoption-shared-2026-11-16/final-dotnet-4cpu.log)
and [snapshot/result](../../builds/artifacts/adoption-shared-2026-11-16/final-dotnet-result-4cpu.json).
Focused reruns of four classes pass, but do not replace complete-project evidence.
No assertion, coverage threshold, audit or test selection was relaxed. Both broad
process trees finished and their private temporary directories were removed.

## Before adoption

1. Resolve the required-check failures and qualify a separate immutable **Builds
   infrastructure release**. Then select that exact acceptable tag in CiCd,
   regenerate callers and pass global validation. New checkout files do not
   extend `v6.0.6`'s released contract.
2. Prepare enabled product actions and package-only evaluated graphs in
   EventStore → FrontComposer → Tenants order. Verify complete delegated
   execution, exact coverage and preserved Platform deferral limits.
3. Establish fresh hosted browser/TLS/APT, Dapr/Aspire/backend, mutation resource
   and matrix-isolation evidence; measure budgets. Verify live protected Azure
   runner/environment/secrets/authority boundaries separately.
4. Deliver each adoption perimeter with publication disabled and record green
   adoption CI. Product publication requires a later separate authorization.
