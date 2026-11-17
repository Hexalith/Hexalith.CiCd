# Shared adoption validation — 2026-11-16–17

**Source qualification passed for the integrated fixes below. Operational delivery remains blocked by the AI.Tools AD-21 ruleset precondition. Builds main subsequently advanced beyond the qualified source, so its newer combined source also requires qualification. Infrastructure release and product cutover remain held.** This report supersedes the provisional synthetic-source qualification in the [previous report](https://github.com/Hexalith/Hexalith.CiCd/blob/5da249288476d21095c3c677563974bf90dccbbe/docs/shared-adoption-validation.md).

The selected production contract remains `v6.0.6` at `fdda17c0a4538b0f7c99f813c20ca24b49006530`. This work creates no infrastructure release or product adoption. EventStore, FrontComposer and Tenants publication switches were found enabled and changed to `false`, with successful readbacks at 2026-11-16 21:30 and 23:19 UTC. No product package/image publication or product source changes were performed.

## Source and evidence boundaries

- Initial Builds main: `cbd13a1e93015182439112918cae4216b953f9bf`.
- Reviewed Builds local source: `24184ca0940ab5e2be7550cc270a59492e764143`, based on `95a4a9adf52637cc1d26d7c07ef62536ea36be04`.
- Concurrent Builds `0a1d2e028c554798969643485631eab245ef020d` independently fixed ordinary catalog-default selection. Integration preserves that implementation, its nullable package-lookup contract, tests and README, and adds the reviewed lifecycle and literal-default checks.
- Integrated Builds fix: `2ee32885ae96805c7745c519275e351ebb229720`, based on `07fdb22578ba55e092b2db1b4ff43f253b53fbbf`. The final eight-file delta preserves the concurrent upstream fixes.
- Initial CiCd main: `5da249288476d21095c3c677563974bf90dccbbe`; later reproduction baseline: `4d5a41c69b1c57e049a3d3a5c084259d896c6e5b`.
- Reviewed CiCd local source: `6cb83f8519b316b17b5e918ab0c941c67975b6e4`.
- Integrated CiCd fix: `195d03e2d0a4ef43da623c2542faa9079c80c811`, based on `f76fe248bbaf5b12448f0acb959f762142567439`.

Every disposable clone, feed, report and build output was beneath a live `run-with-temp` private directory. Useful evidence is retained in `builds/artifacts/adoption-qualification-20261116/`, outside scratch storage and excluded from commits. Complete checks and focused diagnostics have separate logs and source identities. Original working trees were not edited by this work. Interrupted superseded-source runs grant no complete-suite credit.

## Reproduction

| Source / check | Result |
| --- | --- |
| Builds initial main, complete shared Release build and unit projects | Evidence project 191 passed. Module project 3,121 passed, 2 failed, 4 existing conditional skips, 41m24.889s; native exit 2. Unit failure correctly prevented integration. |
| Builds hosted initial main, run [43958809607](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43958809607) | Module project 3,122 passed, 1 failed, 4 existing conditional skips, 25m24.248s. Catalog fallback read retained `7.0.7` where current `8.0.1` was required. |
| Builds native lifecycle reproduction | `ReviewFailedLaunchPreservesActualBatchHistoryAsync(true)` recorded `failed` instead of `terminated`; a deterministic uncertainty regression failed on the old scanner because no retry occurred after an unverified empty scan. |
| Builds startup/deadline diagnostics | The initial complete-project run passed the previously named deadline cases. An overlapping seven-class diagnostic had 286 passed / 5 failed, including four five-second mapping cases and one pre-task path case. These remain failed diagnostic evidence, not a passing gate. Original assertions and deadlines were retained; four fixture classes now use the existing exclusive collection. |
| CiCd initial main, `test_deliver.py` | Timed out at the unchanged 600-second bound after six completed methods. Repeated Git subprocesses and per-blob lazy fetches were measured. |
| CiCd initial main, `test_delivery_workflow.py` | 17 passed in 503.044s; the prior timeout did not reproduce. |
| CiCd initial main, `test_scan.py` | 114 passed in 428.335s. The five reported probes were then uncommitted. |
| CiCd later main `4d5a41c…`, original five positive probes | All five failed in 9.904s. Their one-line fixtures could not satisfy the unchanged duplication threshold; bare `process` also incorrectly required a package lock. The original source strings and assertions are preserved, with substantial copied bodies appended. |

## Fixes and review

Builds retries uncertain native-process scans within the original stopping allowance and continues to refuse persistent uncertainty. Catalog fallback uses explicit top-level literal defaults, excludes conditional/Target/Otherwise scopes, and preserves pinned consumer snapshots. No startup deadline, count assertion, test selection, coverage threshold or audit policy was relaxed.

CiCd batches exact-object source acquisition and validates modes, paths, object identities, per-blob size, aggregate size and bounded command output. The 600-second suite limits remain unchanged. Scanner handling preserves ordinary local `process` reads while rejecting reflective execution/loaders, environment resolution changes, computed invocation and unsupported re-exports. All prior scanner methods except the repaired positive fixture body remain unchanged; its assertions are identical. Extra positive and negative controls cover the new boundaries.

Three independent review lenses were triaged. The verified default-scope and process-execution gaps were fixed. Progressive writes to disposable export storage before a later size refusal remain pre-existing behavior: callers abort before import/ready, so partial output earns no execution or qualification credit.

## Required checks

| Exact source / check | Observed result |
| --- | --- |
| Builds `2ee32885…`, [CI 43974880506](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43974880506) | Both Python lanes passed 16/16 groups, including 748 shared-library tests each; workflow/API and Linux, Windows and macOS sample jobs passed. The package catalog and complete .NET job also passed; the entire workflow concluded success. |
| Builds `2ee32885…`, standalone complete shared stages | Exit 0 in 26m1.214s. Stage 1 and Release build passed; evidence 191 passed; complete module project 3,139 passed, 0 failed, 4 existing conditional skips (25m30.050s); complete integration project 1 passed, 0 failed, 12 existing opt-in live skips. No processor-count override. |
| Builds `2ee32885…`, native report/coverage smoke | Real .NET 10/11, four tests per mode, both MTP and VSTest passed with fresh TRX/Cobertura. Each scoped fixture reported 3/3 lines and 2/2 named branches; strict `>80` line and `>=100` named-branch gates preserved. |
| Builds `2ee32885…`, dependency and API checks | Locked npm install/signatures passed. Public API: 2,758 entries, no removals against `v6.0.6`. Pinned online workflow/composite audits passed. |
| CiCd `195d03e2…`, [hosted validation job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43973386699/job/133671851472) | Passed: `global=true`; AI.Tools, Commons and PolymorphicSerializations independently validated. Delivery 20 tests/130.070s; workflow 17/101.336s; scanner 119/245.648s; runtime 19/8.053s. All tool suites passed. |
| CiCd `195d03e2…`, complete local locked `tools/validate.py` | Exit 0 in 1,030.100s; global and all three module checks passed, including scanner 119/268.228s. Original 600-second suite and 1,800-second global bounds unchanged. |
| Exact integrated Builds/CiCd candidate contract | Actual schema/strict-reader bytes, deterministic caller/interfaces, four isolated routes, long mutation workers, private authority and additional-project cases passed. Local test tag only; no acceptable publication is claimed. |

The exact Builds hosted .NET job independently reports the same 191 / 3,139 / 1 passing counts and 0 / 4 / 12 existing skips. Its results and the local complete-project results are separate receipts.

The earlier frozen reviewed Builds source `24184ca0…` separately passed both complete Python interpreters and all 16 catalog commands. These results are retained as snapshot evidence; fresh integration CI is authoritative for the resulting commits. Focused diagnostics never replace complete projects or complete global checks.

CI stages 1–3 deliberately retain their existing shared `NuGetAudit=false` restore policy. Their flags and local checker alignment are unchanged; the separate infrastructure release's authoritative all-package audit remains required. Dependency signature checks and audit regressions were retained. Existing conditional/live skips certify no Platform/live/private product execution.

## Concurrent main advancement

At 2026-11-16 23:51 UTC, Builds main had advanced from the qualified `2ee32885ae96805c7745c519275e351ebb229720` to `66fc4855a6d3746fbfc8ad02db27d4ecd44dd8c9`. The intervening work changes producer preparation, package metadata acquisition, schema/workflow contracts and catalog assignment ordering, including replacing the ambiguous-default rejection with SDK-evaluated ordered assignments. These are substantive changes outside this qualification's frozen eight-file fix. Their [CI run 43981872199](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43981872199) was queued when inspected.

The green results above qualify `2ee32885…` only. They cannot authorize releasing the newer main. Freeze and qualify the intended combined source, including its complete projects, catalog/Python suites, audits and candidate contract, before an infrastructure release. No later-main passing result is inferred from the earlier snapshot or from focused checks.

## Operational delivery blocker

The [separate delivery job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43973386699/job/133679596704) failed after successful validation: `Hexalith.AI.Tools` reported `App precondition check failed: AD-21 main/v* rulesets check failed`. Its accepted ref remained absent and no application occurred. A read-only API query returned zero rulesets. The guard remains unchanged; provisioning this repository's live policy is a separate maintainer operation.

The overall CiCd Delivery workflow therefore concluded failure, despite its successful validation job. Commons and PolymorphicSerializations advanced their existing accepted references and reported `application=unchanged`, without content pushes. EventStore, FrontComposer and Tenants are not registered or adopted by this work. Artifact `14280044050` binds this receipt to source `195d03e2…`, with SHA-256 `6bc9f1dc5165d7624c3c9103b125e4e20b6bf3a6854c4c1e39aa9b28173016ab`.

## Reproducibility and publication boundaries

The required full entry points were `uv run --locked --script --python 3.12 tools/validate.py` in CiCd and `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` (also Python 3.14) in Builds. The native helper invokes the existing shared guard, prepare, Release restore/build, complete unit and complete integration stages; it does not substitute selected classes. Helpers, exact commands, timestamps, commit/tree identities and full stdout/stderr are retained with the evidence. Checks used pinned Node 24 and uv 0.13.7. No product's standalone local-check success is claimed before adoption.

The three repositories' product publication variables remain disabled. No infrastructure release, product release, product registration, package or image publication was dispatched. Both scoped source commits were pushed normally to main; their exact full messages passed the owning pinned commitlint 21.2.4 policy before use. The report is a separate documentation-only commit and makes no qualification claim for later source changes.

## Separate operations after qualification

1. Resolve the separate AD-21 operational blocker and qualify the frozen intended Builds release source, including the concurrent main changes described above, then perform its separately authorized `builds-release.yml` infrastructure release. Preserve authoritative release audits and original-artifact provenance, and verify an acceptable immutable bot-authored stable tag. No such release is dispatched or published by this work.
2. In a separate CiCd infrastructure change, select that exact acceptable tag in `builds-version`, regenerate callers, commit the render with its cause, and run full locked global/module validation against the published tag. Checkout files cannot substitute for released contract bytes.
3. Product preparation and hosted browser/TLS/APT, Dapr/backend, matrix isolation, mutation budgets and private authority evidence remain separate. EventStore → FrontComposer → Tenants adoption and product publication require later authorization; keep their publication switches disabled.
