# Shared adoption validation — 2026-11-16–17

**Frozen-source checks passed for Builds `b1c34d0…` and CiCd `6b45861f…`. Operational delivery and cutover remain held by AI.Tools AD-21 and later unqualified Builds source.** Both frozen targets passed complete local and hosted validation. Later Builds main is outside these results. This report supersedes the [provisional report](https://github.com/Hexalith/Hexalith.CiCd/blob/5da249288476d21095c3c677563974bf90dccbbe/docs/shared-adoption-validation.md).

A separate workflow outside this task already published [Builds `v6.1.0`](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.1.0) from a different source at 2026-11-17 01:14:39 UTC. This task did not dispatch, publish or adopt it. **CiCd remains pinned to `v6.0.6`**; EventStore, FrontComposer and Tenants publication remains disabled. No product registration, adoption, cutover or package/image publication was performed by this task.

## Source identities and boundaries

| Purpose | Immutable identity |
| --- | --- |
| Initial Builds main | `cbd13a1e93015182439112918cae4216b953f9bf` |
| Initial CiCd main / published scanner reproduction baseline | `5da249288476d21095c3c677563974bf90dccbbe` / `4d5a41c69b1c57e049a3d3a5c084259d896c6e5b` |
| Initial integrated fixes, pushed normally | Builds `2ee32885ae96805c7745c519275e351ebb229720`; CiCd `195d03e2d0a4ef43da623c2542faa9079c80c811` |
| Final frozen Builds target | `b1c34d0cae03d8d6e0a37d67ac62cdd7dcd9e5bc`, parent `717e5ab29569fc57b0f43415f1aee2fc93441859` |
| CiCd bounded byte-packing fix | `5c358596f8636b31cc6b5b8aca309814997cb1d9`, parent `95d181721d55535c0e7c57d2f12f6537d754341c` |
| Final frozen CiCd target | `6b45861fefc87c645f368801c63d2308f0c4eb23`, parent `166350673f5eb57555ed4a1aaf501f8828cfa32d` |
| Unchanged selected production contract | `v6.0.6` at `fdda17c0a4538b0f7c99f813c20ca24b49006530` |

All disposable clones, package feeds and build outputs stayed beneath live `run-with-temp` private directories. Useful logs, helpers, raw reports, command/timestamp/commit/tree receipts and `qualification-index.json` are retained outside scratch storage in `builds/artifacts/adoption-qualification-20261116/` and excluded from commits. Original tracked working-tree files were untouched. Only direct root-declared dependencies were initialized; no nested submodules were initialized. Superseded or interrupted checks earn no complete-suite credit.

Both scoped source deltas preserve concurrent upstream work. The final Builds target includes producer preparation, SDK-evaluated ordered catalog assignments and fresh TLS work. The final CiCd target preserves the independent deterministic ZIP fix `5790a657d1ef63c58908b6682a56f40f500e88fe` and concurrent private-qualification checks. Its own final two-file delta retains prior ZIP attributes and adds an end-to-end fixture regression. Exact full messages passed the owning pinned commitlint 21.2.4 policy before use; pushes used normal main ancestry without force or bypass warnings.

## Reproduction and failed evidence

| Source / scope | Observed result |
| --- | --- |
| Builds initial main, complete shared Release/unit pipeline | Evidence 191 passed. Module 3,121 passed, 2 failed, 4 existing conditional skips; 41m24.889s, native exit 2. Unit failure correctly prevented integration. Catalog fallback selected historical `7.0.7` instead of `8.0.1`; failed-launch lifecycle recorded `failed` instead of `terminated`. |
| Builds initial main, [hosted complete project](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43958809607) | Module 3,122 passed, 1 failed, 4 existing skips; catalog failure. Previously named startup/deadline cases passed on this main. |
| Builds focused diagnostics, separately retained | An overlapping seven-class diagnostic had 286 passed / 5 failed, including four five-second mapping cases and a pre-task path case. Deterministic native-uncertainty and catalog-default regressions failed on old code and passed after fixes. These selected runs never substitute for complete-project results. |
| CiCd initial main, original suites | `test_deliver.py` exceeded the unchanged 600-second bound after six methods. `test_delivery_workflow.py` passed 17 tests in 503.044s, so its timeout did not reproduce. Scanner passed 114/428.335s; the five reported probes were then uncommitted. |
| CiCd `4d5a41c…`, original five scanner probes | All five failed in 9.904s. Their one-line bodies could not meet the unchanged duplication threshold; bare `process` also incorrectly required a package lock. Original source strings/assertions remain, with substantial copied bodies appended. |
| Documentation-only `4db3776…`, complete validation | Hosted validation passed, including scanner 119/326.450s. Local validation failed at the unchanged 1,800-second global bound during scanner; all three independent module checks passed. No complete local passing credit. |
| CiCd `5c358596…`, complete validation | Local full validator passed in 1,312.376s, including scanner 125/334.416s. [Hosted validation](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43987869330/job/133729496844) failed one nightly readiness precondition; all other suites, including scanner 125/245.217s, passed. The complete hosted result remains failure. |

The nightly failure is reproducible on unchanged `5c358596…` by crossing a two-second ZIP clock boundary. The fixture separately regenerated listing/download ZIPs with equal documents but different timestamps and SHA-256 values. Captured state reports `artifact ZIP size or digest mismatch`; production correctly refuses the outcome, reproducing the same `TypeError` in the test precondition. The actual hosted internal state was not retained, so the controlled reproduction proves this fixture failure mechanism without claiming an unavailable hosted diagnostic.

## Fixes and review

Builds retries uncertain native-process scans within the existing stopping allowance, still refusing persistent uncertainty. Catalog fallback retains literal top-level defaults, excludes conditioned/Target/Otherwise assignments and preserves verified consumer snapshots and the upstream SDK-ordering contract. Four finite startup fixture classes use the existing exclusive collection; every original deadline and count assertion remains.

The changed legacy workflow exposed seven security findings. Two consumer checkouts now disable credential persistence; five nonexistent release labels now truthfully describe their unchanged untagged action commits. Canonical tag inventories were checked. No dependency/action pin, audit rule, frozen baseline or waiver changed. Online audits report 10 existing frozen composite findings and zero new findings.

CiCd acquires validated exact Git objects in bounded groups and packs complete body/framing bytes within the existing 16 MiB command cap. The 2 MiB blob, 64 MiB total and 128-entry acquisition limits remain. All 69 prior runtime assertions remain; real partial-Git tests cover exact capacity and a one-byte-over split. Profiles preserve identical bytes and reduce tools Git calls 16→5 and historical Builds calls 17→10. Final tools wall timing showed no gain; historical Builds median improved 0.410→0.288s. These are diagnostic observations, not complete-suite credit.

Scanner bindings admit ordinary local Node `process` reads while refusing reflective loaders/execution, environment resolution changes, computed invocation and unsupported re-exports. Existing negative cases and duplication thresholds remain. Nightly fixture serialization is deterministic with original compression/member metadata; existing test methods, strict digest rejection and publication-slot withholding remain unchanged. The new fixture-API regression fails before the fix and passes after; the original failing controller case passes controlled clock-boundary repeats.

Three independent review lenses were applied to the original changes and each follow-up; verified findings were repaired. An optional pre-existing global-preflight enhancement for progressive export writes is deferred: callers abort before import/ready on refusal, and partial exports receive no execution or qualification credit.

## Complete required checks on frozen targets

| Target / check | Result |
| --- | --- |
| Builds `b1c34d0…`, [CI 43985758751](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43985758751), attempt 2 | **Success**, all required jobs. Both Python 3.12.16 and 3.14.4 lanes passed 16/16 groups, including 755 shared-library tests each. All 16 catalog commands, workflow/API and Linux/Windows/macOS sample jobs passed. Attempt 1 was cancelled before execution and earns no credit. |
| Builds `b1c34d0…`, complete hosted .NET | Evidence 191 passed; module 3,146 passed / 0 failed / 4 existing conditional skips (31m44.778s); integration 1 passed / 0 failed / 12 existing live opt-in skips. |
| Builds `b1c34d0…`, complete local shared stages | Exit 0 in 35m20.223s: guard, prepare, Release restore/build, complete unit projects and complete integration project. Same 191 / 3,146 / 1 passing counts and 0 / 4 / 12 existing skips; module 34m44.879s. No processor-count override. |
| Builds `b1c34d0…`, native report/coverage smoke | MTP and VSTest passed on real .NET 10/11: four tests each, fresh TRX/Cobertura, exact 3/3 scoped lines and 2/2 named branches. Strict `>80` line and `>=100` named-branch gates retained. |
| Builds `b1c34d0…`, dependencies/API/audits | Locked npm install and signatures passed; 2,760 API entries, no removals against `v6.0.6`; pinned online workflow/composite audits passed. |
| CiCd `6b45861f…`, full locked validator | **Passed**, exit 0 in 853.395s. All 19 tool suites and all three independent module checks passed; original 600-second suite and 1,800-second global bounds unchanged. Complete counts/timings are retained in `qualified-cicd-suite-summary.json`. |
| CiCd `6b45861f…`, [hosted validation](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43997702423) | **Passed**: global and all three module checks. Delivery 20/135.829s; workflow 17/109.124s; runtime 21/9.122s; nightly 42/111.670s; nightly runtime 39/11.512s; scanner 125/254.732s; renderer 46 and validator 54 also passed. The separate delivery job failed as described below. |
| CiCd `6b45861f…`, renderer audits | 46 tests and nine fixture workflows passed pinned online actionlint/zizmor audits. |
| Exact `b1c34d0…` / `6b45861f…` contract | Actual schema/strict reader and caller interfaces, deterministic render, four isolated routes, long mutation workers, mapped/legacy private authority and additional-project cases passed. Unpublished local test tag only. |

The full entry points were Builds `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` (also 3.14) and CiCd `uv run --locked --script --python 3.12 tools/validate.py`. The native helper invokes actual shared guard/prepare/Release/complete-unit/complete-integration functions. Pinned uv 0.13.7 and Node 24 were used. Earlier frozen local snapshots and the initially qualified `2ee32885…` / `195d03e2…` retain separate complete receipts; current rows are authoritative for these final targets.

CI stages 1–3 retain their existing shared `NuGetAudit=false` restore policy and local-checker alignment. The separate infrastructure release performs authoritative all-package auditing; this task did not replace that boundary. Existing conditional/live skips establish no Platform/private/backend/product qualification.

## Remaining blockers and concurrent publication

The [separate delivery job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43997702423/job/133765849487) failed after successful validation: AI.Tools reports `App precondition check failed: AD-21 main/v* rulesets check failed`. Its accepted ref remains absent and no application occurred. A read-only query at 2026-11-17 02:05 UTC returned zero rulesets. The live guard is unchanged; maintaining this repository policy and rerunning delivery is a separate maintainer operation. Commons and PolymorphicSerializations advanced existing accepted refs with `application=unchanged` and no content push. Artifact `14291978033` binds this receipt to exact `6b45861f…`, digest `85d5a387fa6574c81f986506fc57fb486cd5028d2c12b881f9719c76a8d54835`. The overall workflow is therefore failure despite passing source validation.

Later Builds main `af3752ddcbe94c007630703ab3803df5654f9933` changes dependencies, guard tools, workflows and catalog tests beyond `b1c34d0…`. This report does not qualify those bytes.

A separate [release run 43991667652](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43991667652), dispatched at 00:56:29 UTC, published [v6.1.0](https://github.com/Hexalith/Hexalith.Builds/releases/tag/v6.1.0) at 01:14:39 UTC from `a1e0c310b1f1a50d78e6132890fae6bcba769f6d`. Its SHA-256-verified outcome artifact `14287814810` says `published`; the author is `github-actions[bot]`. Original release artifact `14288218275` has digest `31fe4c5d1eb53bc6f2d94179635a280071ed58761a0b65a5d3c6387b2939611e`. This occurred outside this task and differs from our qualified source. No dispatch, publication, rollback, republication or adoption was performed here; the published source/artifact needs separate assessment before use.

EventStore, FrontComposer and Tenants publication flags were found enabled and set to `false` at 2026-11-16 21:30 UTC as required. Readback at 2026-11-17 01:54 UTC confirms all three remain false. No product registration was added; the registry still names only AI.Tools, Commons and PolymorphicSerializations.

## Separate operations, not executed here

1. Keep infrastructure release separate. Freeze and qualify the intended exact source, including later main changes and the concurrent `v6.1.0` publication, before deciding any `builds-release.yml` operation. Preserve authoritative all-package audits, original-artifact provenance and acceptable immutable bot-authored stable-tag requirements. Do not publish another release as part of this task.
2. Once an exact published source/tag is qualified and separately authorized, change CiCd `builds-version`, run locked `tools/render.py`, `tools/render.py --check`, renderer fixture audits and full `tools/validate.py`; commit the pin with its caused render. Checkout bytes cannot replace the released contract. This task leaves `v6.0.6` selected.
3. Product adoption/cutover and fresh hosted browser/TLS/APT, Dapr/backend, mutation-budget, matrix-isolation and private-authority evidence remain separate. Keep product publication disabled. No EventStore, FrontComposer or Tenants adoption, release or package/image publication is authorized by this report.
