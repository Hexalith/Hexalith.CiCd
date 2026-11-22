# Sprint change proposal for the CiCd technical audit

**19 November 2026 · Moderate scope · Product owner and CiCd developer handoff**

The maintainer approved this proposal for implementation on 19 November 2026. Story 28-8 still requires a separate decision before historical evidence is deleted. [Approved revision](https://github.com/Hexalith/Hexalith.CiCd/commit/6b413de903926c52a355472f018d3ebcdbc8e144)

Start with story 28-2. One failed Builds release lookup can interrupt repair for several modules that share the same tag. Next, verify the App key inventory and move the executable qualification inputs before narrowing validation. The existing migration sequence and fleet targets still apply. [Technical audit](https://chatgpt.com/space/page_b524c7bda89c8191b5cda7a8636012f9) · [Previous sprint decision](sprint-change-proposal-2026-11-18.md)

## Evidence at the refreshed baseline

The audit examined CiCd `dda394a`. This review used main at `bb61c03795ba0f4a2b58a42c4c1b141871d16fcc`, which selects Builds `v6.4.2` at `8ad2c2285e2d0cec0a173882b3a3a926d555fe48`. All 18 direct checkouts were refreshed from their respective mains. The refresh advances the parent’s Builds reference to `70ce9cb3` and Tenants to `1806474a`. The renderer selects its runtime independently through `builds-version`. Five modules have registrations. The audit's 15 matching caller and configuration comparisons covered those five at the revisions sampled. The refreshed parent passed the locked render check. [Parent baseline](https://github.com/Hexalith/Hexalith.CiCd/commit/bb61c03795ba0f4a2b58a42c4c1b141871d16fcc) · [Registrations](../../setup)

| Audit finding | What the baseline establishes | Decision |
|---|---|---|
| 1. Builds verification | Six hosted deliveries recorded HTTP 403. In one, validation passed and four module deliveries failed. The cause of the refusal is unknown. | Strengthen 28-2 and measure requests per distinct tag. [Delivery run](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44087897241) |
| 2. Full validation on unrelated changes | In the 13–18 November sample, 57 of 109 completed pushes changed only prose, receipts or gitlinks. They used 938 runner-minutes, with a median of 17.9 minutes. A nightly reached its 30-minute delivery barrier without dispatching. | Gate 28-4 on the consumer migration in 28-3. Repeat the same measurements after rollout. [Timing method and sample](sprint-change-proposal-2026-11-18.md#1-issue-summary) |
| 3. App key review coverage | Seven parent workflow files select the environment. AD-7 previously named two. Hosted restrictions and effective grants require separate evidence. | Correct AD-7 and add 30-1 for source enforcement and hosted reconciliation. |
| 4. Scan and bump coupling | Story 28-1 already fixed the maintenance fixture. The bump still runs unrelated suites and waits for scan. Story 29-1 already implemented a reader for both scan sources. | Keep 28-5 and 28-7. Qualify the producer against the existing reader and distinguish release, scan and module acceptance. [Scan reader](../../tools/nightly_acceptance.py) · [Hosted 28-1 result](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44282863616) |
| 5. Dispatch followed by GET 404 | Main contains the bounded GET retry. All three regression cases passed here, including exhausted retries and insufficient time. Each fixture records a single dispatch POST per target. | Close the checkout finding. Story 11 still needs its hosted acceptance on a qualifying run. Its two pre-fix receipts passed the shared checkpoint and Commons, and failed PolymorphicSerializations. [Fix](https://github.com/Hexalith/Hexalith.CiCd/commit/2696124842e84b00df871195f9bf7cfa3e3e992c) · [Pilot receipt](../specs/spec-cicd/evidence/11/pilot-checkpoint-receipt-44517757466.json) |
| 6. Executables and raw evidence | Summing blob entries with `git ls-tree -r -l` at the refreshed parent gives 495,905,573 bytes under `_bmad-output/` out of 540,781,214 bytes overall. There are 236 entries above 256 KiB under that directory. A current test imports an evidence runner. | Migrate live consumers in 28-3, limit new growth in 28-6 and retain the separate maintainer decision for 28-8. [Live consumer](../../tools/tests/test_g6_host_ports.py) |
| 7. Fresh-checkout validation | The root README describes worktrees. The scan guide calls the registry empty and names a four-language test. The current suite has a six-language detector case. | Add 30-2 with a clean Linux checkout as the acceptance environment. [Scan guide](../../docs/duplicate-scan.md) · [Detector suite](../../tools/tests/test_scan.py) |

## App key inventory

The CiCd maintainer owns the standing delivery and nightly jobs in AD-7. The `projects-g6-catalog` option inside the existing delivery job also requests Projects Contents and Workflows write. Its separate review covers the fixed catalog profile until the Projects owner confirms its consumer has retired. The table identifies the five additional manual workflows and the roles responsible for confirming their continued use. Permissions are requested token scopes observed in source. [Owner routes](../../docs/contracts-prerequisites/owner-routes.md) · [Projects repair](../../docs/projects-ci-gates-repair.md)

| Workflow and job | Owner role and target | Requested App permissions | When to review retirement with the owner |
|---|---|---|---|
| `qualify-package-owner-access.yml / qualify` | CiCd maintainer with EventStore and Projects package owners. One fixed matrix target per token. | Contents read | Both package owners have retained their visibility result and finished using this diagnostic. |
| `propose-eventstore-contracts-prerequisite.yml / propose` | EventStore owner with CiCd maintainer. One fixed EventStore proposal branch and its draft PR. | Branch token requests Contents and Workflows write. A separate optional token requests Contents read and Pull requests write. | The named proposal is resolved and the owner confirms the route is no longer needed. |
| `deliver-contracts-prerequisites.yml / deliver` | EventStore and Projects owners with CiCd maintainer. The publisher profile selects one owner. Pin and policy profiles select Projects. | Publishers request Contents and Workflows write. Projects pin and policy profiles request Contents write. | The owners reconcile the approved publisher, pin and policy results and identify the last live profile. |
| `dispatch-contracts-prerequisites.yml / dispatch` | EventStore and Projects owners. One selected owner's existing release workflow. | Actions write and Contents read | Both owners accept their final prerequisite publication or verification receipts. |
| `deliver-projects-ci-gates.yml / deliver` | Projects owner with CiCd maintainer. The qualified nine-file Projects repair. | Contents write | The owner accepts hosted CI, Commitlint and G-6 for the repaired source and confirms retirement. |

These are review conditions. Owners must confirm retirement before a route is removed. A read of the hosted environment from this workspace stopped at the network tunnel with HTTP 403. The hosted branch restrictions and App installation grants remain open.

## Backlog edits and acceptance

The original 28-series criteria still apply. These edits add the evidence needed to accept each change. [Story order](../specs/spec-cicd/stories.yaml) · [Validation classes](../specs/spec-cicd/enforcement.md#what-a-change-runs)

| Story | Previous coverage | Added acceptance |
|---|---|---|
| 28-2 | One authenticated release proof per distinct tag. | Use private state scoped to the delivery run and attempt across slot processes, preflight and application. Test two modules sharing one tag plus a second tag. Count one metadata proof per tag and compare every acquired object with its verified identity. A refusal or inconsistent identity prevents the affected write. Record bounded request IDs and rate-limit headers, and check that state and reports contain no credentials. Observe one week of hosted deliveries using existing token scopes. |
| 28-3 | Move active evidence runners to `tools/qualification/`. | Inventory imports, runbook invocations and fixtures first. Record old and new blob identities or explain path-only edits. Run the affected test and each active qualification entry point against disposable inputs from a clean checkout. Update consumers before treating evidence as prose. |
| 28-4 | Select scope from the PR base or accepted delivered refs. | Record hosted runs for a prose push, scheduled repair, one module's setup and a shared template. Record jobs, verdicts, refs and durations. Prose starts no writer or token mint. The schedule reapplies accepted renders and preserves freshness and tag checks. Check the existing per-module verdict contract. Ambiguous inputs or unreadable baselines take the full path. Repeat the push sample and nightly barrier measurements. |
| 28-5 | Bump selects suites that read the Builds pin. | A bad pin must fail candidate verification. Confirm render, schema, immutable release, tag identity and pin-dependent suites still run. Demonstrate an unrelated failing suite on the full-validation path and record the next eligible hosted bump's duration. |
| 28-6 / 28-8 | Limit evidence growth and later consider historical cleanup. | Test new or modified raw, executable and oversized files against the existing policy alongside a compact receipt and untouched historical files. Record weekly growth using the same blob-entry sum. Before any 28-8 deletion, inventory consumers and obtain its separate maintainer decision. Preserve Git history. |
| 28-7 | Move scan to its own daily/manual workflow and add keepalive. | Ship schedule, failure signal, artifact contract, operator docs and keepalive together. Exercise the existing reader against both an old nightly attempt and the new producer. The independent report must authenticate to its run and cover the module's exact dispatch commit. Exercise missing, stale and failing scan rows, and a bad bump pin. Show separate hosted scan and release outcomes, including a normal daily scan. |
| 30-1 | AD-7 covered the two standing workflows. | Enumerate every parent workflow referencing the environment **or** the key. Check the job, token step, repository selection and requested permissions, including each manual profile. Test an unknown workflow, a widened target and a widened permission. Reconcile the allowlist with read-only hosted evidence for deployment-branch policy, allowed branches and the App's selected repositories and effective grants. Record owner confirmations, discrepancies or access refusals. |
| 30-2 | Local validation instructions were spread across runbooks. | Add a root quickstart with a reproducible `run-with-temp` setup, Python and pinned uv version, Builds tag acquisition, locked render check, one offline controller suite and prerequisites for online validation. Point the scan guide at `setup/` and `ScanTests.test_all_six_languages_use_actual_pinned_detector`. A fresh Linux checkout must reproduce the render and pass the offline suite using only that guide. Identify the npm registry, signature verification and PowerShell prerequisites for detector integration. |

CAP-13 now says how a module is judged once scanning moves. The reader uses the nightly attempt's own artifact for historical runs with a scan job. After separation it selects the first eligible completed scan on main covering the dispatch commit. A missing or stale row leaves module acceptance unproven. AD-18 and the architecture diagram identify the independent producer. [Capability contract](../specs/spec-cicd/SPEC.md) · [Architecture decisions](architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md)

## Implementation handoff

The product owner can fit these changes into the existing sprint. Reverting the dispatch fix or the maintenance fixture would restore known failures. Reducing the fleet target would leave the observed delivery delays and the key inventory gap unresolved. The affected interface is the maintainer's workflow verdict and receipt. There is no product UI change.

1. **CiCd developer and maintainer.** Begin 28-2 with the refusal and object-identity cases. Capture the current proof count before changing the controller. Start 30-1 and 30-2 independently while collecting hosted observations. Allow roughly 1–2 engineer-days for the proof work, one for the inventory and half a day for the quickstart.
2. **CiCd developer.** Complete 28-3 before 28-4. Run 28-6 independently once the live inputs are identified. The audit estimates 1–3 engineer-days for relocation and 3–4 for scoped validation and evidence checks. The principal risk is a wrongly skipped input. Keep the immutable bootstrap's verdict shape and exercise the full fallback.
3. **Release maintainer and CiCd developer.** Qualify 28-5 and 28-7 over the next eligible bump and daily scan. Allow 3–6 engineer-days for the split and qualification work, plus hosted observation. The existing pilot checkpoint and module adoption prerequisites retain their own receipts and owners.
4. **Maintainer.** Record proof requests per tag, runner-minutes by change class, nightly barrier waits and weekly evidence growth. For adopted modules, use the last-200-run method, reporting the window, sample size, main CI success and standard-module p90 against 95% and 10 minutes. Story 27-2 owns the eventual fleet-wide measurement. [Baseline and targets](../specs/spec-cicd/baseline-and-targets.md)

The planning handoff covers all seven findings. Runtime implementation, the hosted App settings readback, a post-fix pilot receipt, online supply-chain checks and the fleet measurements are follow-up evidence. Story 28-8 retains its own decision point.

## 30-2 clean-checkout qualification — 22 November 2026

**Result:** the [root quickstart](../../README.md#linux-maintainer-quickstart)
passed on Linux x86_64: uv 0.13.7 installed managed Python 3.12.16, the locked
render comparison passed, and all 39 dependency-free controller tests passed
with `uv --offline`. Both executable README blocks ran unchanged with initial
`PATH=/usr/bin:/bin`, exercising the documented fallback `run-with-temp`
function. The fresh public parent clone initialized only Builds at gitlink
`3060b20abfcf4ea804ad31816d435e5c754fc129`; the selected and historical tag
fetches succeeded, and the final assertions confirmed unchanged tracked files
and no initialized product modules. Installer, interpreter, executable links,
caches, checkout and raw log stayed beneath private `TMPDIR` and were removed
when the foreground job finished. Quickstart log SHA-256:
`815c019facb60cfcfcfd27e7cb53ee5bae25772fd8bc805de93a17d775e2c2a7`.

The public clone resolved to commit
`307405aba85e587982b69d6ce5847ab2c06000a3`, tree
`05ff900ff5230ca6c295845005b9f87a20537147`. The focused detector command ran
against the implementation baseline commit
`242e868f1060681f134a13692f38c52619e959f1`, tree
`6fc665759992de34287ded8b9a8c5a15f6aa8fbb`. The relevant source objects below
are identical at both commits; these are distinct qualifications, not a claim
that their complete trees match. The README candidate blob (with the qualified bootstrap blocks unchanged) is
`c29dec547900bd410102fbc52974ae1e508772ac`; the corrected scan-guide blob is
`5865c087dda3e056e0dc320260e6c16e3da17a76`.
Standalone commands gained inherited `UV_NO_CACHE=1` during documentation review
after these runs; the recorded verification digests retain their original executions.

| Relevant input | Full Git object identity (blob unless marked tree) |
|---|---|
| `builds-version` | `ecb8b9a7d5cd90f97c08600ef5730590df82cdc4` |
| `.gitmodules` | `5f4db08e8b4a26baaa3649160a7ddf3f8c5e1b0c` |
| `.github/workflows/deliver.yml` (uv pin) | `a10275be9c3ae186cfa301d598731c484e2ca260` |
| `setup/` (live registry tree) | `bb299f775e8564d7dc873f21a5abe10952e4d15c` |
| `templates/` (tree) | `6a2337c8dee8cc4dbae9c9687bf00b21c96e8075` |
| `rendered/` (accepted output tree) | `d1c499bd45fe6ae9e832e2144d9e4a6360db1d40` |
| `tools/render.py` | `8e0959e358376d141183ef0c7f4fd259abf63a11` |
| `tools/render.py.lock` | `4481492c6c5b7b392723c31912f4767526239e4f` |
| `tools/nightly_runtime.py` | `3e18a8b916e6e029a64f3c891279ccf882cf0537` |
| `tools/tests/test_nightly_runtime.py` | `670b0ab8256006666b7f7ac07326ae39ddd1e3b9` |
| `tools/tests/test_nightly_runtime.py.lock` | `7518fc90bf78b2b347b694f695c6e1ed120d523c` |
| `tools/tests/test_scan.py` | `e1e6f5e42ae343e8589dc6bbf3c75d4e30706d02` |
| `tools/tests/test_scan.py.lock` | `c590b9a3f47f2876468871984ca81de8ff999733` |
| `tools/scan.py` | `6beec52b74fd9b4d720be03a96f1071e5d8de260` |
| `.jscpd.json` | `7f2bed36ea9f4d7620c175656a0a3290df9d7a39` |
| `tools/jscpd/package.json` | `68a2a66e16aae5dc0de236929502b2f3b8d7cd88` |
| `tools/jscpd/package-lock.json` | `a5f8267232aabf308c4b834c5cc8ed03a84ad7fd` |

Builds tag objects are lightweight tags, so the tag object and commit IDs match:

| Acquired tag | Tag/commit ID | Tree ID |
|---|---|---|
| `v6.6.1` (selected) | `27fe4d62ca1f3cce07a9f19e1e30b02cbaa51357` | `e55fefff3fa765e4a7bc9408caf61ea0a59b6dc5` |
| `v6.0.6` (renderer fixture) | `fdda17c0a4538b0f7c99f813c20ca24b49006530` | `81882bd1852cf3c10c7a2b6647b238c8eec22fa8` |
| `v5.1.0` (global-suite fixture) | `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4` | `397a855c1acb779f1631835444c3b750ffd72f72` |

**Observed online detector result:** the exact focused command in the
[scan guide](../../docs/duplicate-scan.md) passed (one test, six formats) using
uv 0.13.7, Python 3.12.16, Node 24.22.1, npm 11.19.1 and PowerShell 7.6.2.
Its normal isolated install, mandatory `npm audit signatures` and pinned jscpd
5.4.3/TypeScript 6.0.3 checks succeeded. Substantial copied examples were
detected at YAML 36 lines/216 tokens, Bash 18/54, PowerShell 18/72, Python
18/144, JavaScript 18/198 and TypeScript 18/198. Detector log SHA-256:
`a406d5ed6e466375bec6c601ef8c702b6b40f1170e13624def53cd917504b322`.
No raw output or executable runner was committed under `_bmad-output/`.

**Online boundary and prerequisites:** full `tools/check_global.py` and
`tools/validate.py` were not executed in this qualification and remain unproven,
as do a production live-source scan and hosted workflow outcomes. Their guide
requires Linux x86_64, the same pinned uv/Python and script locks, local selected
and historical Builds tags, Node 24/npm, compatible PowerShell 7 with the native
`ModuleAnalysis` API, npm registry and signature/provenance access, GitHub Git/API
and release/archive connectivity, and the existing read-only `GITHUB_TOKEN` or
`GH_TOKEN` for release/bootstrap proofs and online auditing as applicable.
The local offline pass and the focused detector pass do not waive any failed,
refused or unexecuted online gate. The earlier dated audit observations above
remain historical; current scope is the live [`setup/` tree](../../setup/).

Independent repetition of the documented commands also passed: clean bootstrap
(39 offline tests), log SHA-256
`64837cfa6eccb7c01c9f27a9c53d67a74ab8faa96d760d563d7bebdcbab855f5`;
real six-language detector, log SHA-256
`487f62372c5f92b48deaf97b7bff5b4628bdbff238d29755ca78a9d6a5e63b6d`.
The repeated public checkout resolved to the same commit and tree above.

Post-review verification passed again against the same public commit/tree:
locked render and all 39 offline controller tests, log SHA-256
`1a15c9ad52a4522172aeb54e04d0413f18e91484a54404cf6c4155696bfba2c7`.
The reviewed focused command with inherited `UV_NO_CACHE=1` also passed all six
formats with the same pinned toolchain and mandatory signatures, log SHA-256
`0682981917d0309b45728f047ebb0d853d7570629b06715753af69dcfa8f89f7`.
