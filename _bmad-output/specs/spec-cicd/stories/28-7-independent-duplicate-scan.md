---
title: 'Independent duplicate scan'
type: feature
created: '2026-11-23'
status: done
baseline_revision: 97538b46caec91945d25b496ff1135bab475f2b0
review_loop_iteration: 0
followup_review_recommended: true
context: []
warnings: []
deferred:
  - summary: >-
      Large duplicate-scan summaries can exceed the Actions step summary limit.
    evidence: |-
      The existing scanner allows a summary of up to 16 MiB and the moved step writes the full text to the Actions job summary. GitHub limits a step summary to 1 MiB. The retained summary.md artifact carries the complete report.
    location: >-
      .github/workflows/scan.yml
    severity: low
---

<intent-contract>

## Intent

**Problem.** A duplicate scan waits for publication and holds up the Builds bump. Its coverage verdict also makes the release run red.

**Approach.** Move the existing job to a daily and manually dispatchable `scan.yml`, add it to keepalive, and qualify the existing acceptance reader against both producers.

## Boundaries & Constraints

Build to [November 18 §4.1](../../../planning-artifacts/sprint-change-proposal-2026-11-18.md#41-stories) and [November 19 story 28-7](../../../planning-artifacts/sprint-change-proposal-2026-11-19.md#backlog-edits-and-acceptance), CAP-9, CAP-13 and AD-18. Keep the tool, detector, policy, report schema, artifact name and members. Retain the nightly release, bump verification and post-bump delivery behavior. The scan reads registered public modules' live main and uses a Contents-read job with no App credentials. Store run links, Git identities, log digests and results in this story.

</intent-contract>

## Code Map

- `.github/workflows/nightly.yml` — move the entire `scan` job, including its before-checkout seed, pinned toolchain, summary verdict and 90-day upload. Remove its nightly prerequisite and probe input check. Set `bump.needs` to `[publish-ready]`.
- `tools/nightly_keepalive.py` and `tools/nightly_runtime.py` — extend the sequence and exact CiCd-only enable routes. Keep enable failures independent and visible and retain idle-main handling.
- `tools/app-workflow-policy.json` — bind the new bump graph and exact runtime. `scan.yml` uses no App and is outside the dependency closure of App jobs.
- `tools/scan.py` — `scan` resolves controller HEAD and each module commit, persists `report.json` and `summary.md`, and reports findings and discovery failures. Treat it and its configuration as fixed.
- `tools/nightly_acceptance.py` — `ARTIFACTS`, `Artifacts` and `ScanSource` authenticate the artifact and use the first eligible scan with an exact dispatch row. Use the reader unchanged. `test_nightly_acceptance.py` provides simulated GitHub responses for both producer paths.
- `tools/tests/test_nightly_workflow.py` — reuse the executable job harness. Exercise scan independently, keep release and cancellation coverage, and enforce the real upload name and members. `test_scan.py` provides real Git and pinned detector fixtures for producer-to-reader qualification.
- `docs/duplicate-scan.md` and `docs/nightly.md` — describe independent scan operation, its artifacts and the acceptance check.

## Tasks & Acceptance

**Execution**

- [x] `.github/workflows/{scan,nightly}.yml` — schedule scan daily at 03:07 UTC and by hand on main. Preserve the job steps and remove scan from the nightly graph.
- [x] `tools/nightly_{runtime,keepalive}.py` and their existing tests — enable the three fixed workflows and cover allowed and refused requests.
- [x] `tools/app-workflow-policy.json` and `tools/tests/test_app_inventory.py` — renew the runtime and bump bindings. Retain transitive dependency coverage.
- [x] `tools/tests/test_nightly_workflow.py` — exercise both graphs and the scan artifact.
- [x] `tools/tests/{test_scan,test_nightly_acceptance}.py` — pass real scanner artifacts through the existing reader's Actions boundary with distinct controller revisions and real dispatch commits. Use existing fixtures to exercise rejected identity and bad pin cases through the reader and bump gate.
- [x] `docs/{duplicate-scan,nightly}.md` — update operator procedures and verdict meanings.
- [x] This story — record local qualification and read the retained hosted Nightly artifact.
- [ ] This story — record a normal daily scan and separate release observations after rollout.

**Acceptance Criteria**

- Given either scan trigger on main, when the job runs, then it executes the existing locked scan and retains the two-member attempt artifact. Given a duplicate or unsupported discovery construct, when scanned, then the independent run fails and its report names the affected source.
- Given a nightly with failed publication or an unrelated failing scan, when the nightly finishes, then the bump depends only on publication completing and keepalive attempts all three enables. Given a bad Builds pin, when the bump verifies it, then it fails without a publishable candidate.
- Given a historical attempt with a scan job or a new nightly with an independent producer, when the reader evaluates it, then it authenticates the producing run and artifact and assesses the exact module dispatch commit. Given missing coverage, a stale or failed row, or a duplicate involving the module, when evaluated, then the reader withholds acceptance. A later clean row cannot replace the first exact failing row.
- Given rollout to hosted main, when Nightly and scans complete, then record separate release and scan outcomes, including a normal scheduled scan. Record the scan run, attempt and artifact and exact-head module coverage. Keep this criterion open until observed.

## Spec Change Log

## Review Triage Log

### 2026-11-23 — Review pass

- Verdicts 17 findings. High 0, medium 9, low 8, false 0, maybe-false 0.
- Findings
  - `[medium]` `[patch]` Blind 1. The reader selects the current attempt for each run ID. The runbooks now distinguish attempt selection from ordering across independent runs.
  - `[medium]` `[patch]` Blind 2. Detector runtime setup could fail the bump. Removed it from the bump and checked every pin suite with Node and npm commands intercepted.
  - `[medium]` `[patch]` Blind 3. An on-demand scan started after module main advances can miss the dispatch commit. Documented the exact-head timing and the separate scan dispatch.
  - `[low]` `[patch]` Blind 4. The existing reader accepts one complete page of results. Documented the 100-run limit.
  - `[low]` `[patch]` Blind 5. A compact receipt can list artifacts from multiple scan runs. The procedure now records the deciding run, attempt, artifact and dispatch SHA alongside it.
  - `[medium]` `[patch]` Blind 6. The scan could consume the finalization budget. A 42-minute step limit reserves time in the existing 55-minute job, and the docs describe cancellation and runner loss.
  - `[low]` `[defer]` Blind 7. The inherited full-text job summary can exceed 1 MiB. The complete Markdown remains in the artifact. A UI excerpt is separate work.
  - `[medium]` `[patch]` Blind 8. The earlier bad-pin case stopped at selection. The revised fixture runs the isolated producer gate on the committed pin, then gives the resulting report to the reader. A separate validator test rejects a remote tag-object mismatch.
  - `[low]` `[patch]` Blind 9. The setup guide described the old scan placement. It now identifies the independent workflow and links to the scan runbook.
  - `[low]` `[reject]` Blind 10. The hosted observation is open as recorded. It requires the new default-branch workflow and a normal scheduled event. This local review cannot substitute for that observation.
  - `[medium]` `[patch]` Edge 1. Retrying a run can change the current artifact that the reader evaluates. The runbooks now identify the eligible run's current attempt.
  - `[low]` `[patch]` Edge 2. The single-page limit can be reached within artifact retention. The operator documentation states the lookup bound.
  - `[medium]` `[patch]` Edge 3. Slow discovery could exhaust the job deadline before finalization. The scan step leaves a separate finalization budget.
  - `[medium]` `[patch]` Edge 4. A partially written temporary file could enter a directory upload. The action now receives exactly the two public members. Its pinned implementation uses their common parent as the ZIP root. The fixture stages an extra file and checks the named paths. [Pinned upload path handling](https://github.com/actions/upload-artifact/blob/cf430e030ddbb5b0abf93d22962f4752f3646cd9/src/shared/search.ts#L128-L139)
  - `[low]` `[reject]` Edge 5. Existing fixture cases use one producer source or the other and have unique run IDs. A duplicate-ID guard would only protect future fixture construction.
  - `[medium]` `[patch]` Verification gap. A checkout of a moving main ref was invisible to both old fixtures. The scan explicitly checks out the triggering SHA, the workflow fixture advances main before checkout, and the real-report test independently derives the run SHA and rejects a mismatched controller.
  - `[low]` `[reject]` Intent alignment. The local workflow and producer-to-reader checks compose through fixture Actions responses. A hosted acceptance result remains an explicit, separate observation.

## Verification

- Run the changed workflow, runtime, keepalive, scan and reader suites in disposable scratch with locked uv. Exercise the bad pin with the bump and validator tests.
- Lint CiCd workflow YAML with the configured actionlint. Check the source delta and record its identities.
- Read hosted Nightly `44264031228` with the read-only acceptance tool and record post-rollout outcomes from Actions metadata and authenticated artifacts.

## Hosted historical qualification

The read-only acceptance CLI authenticated the original scan artifact on
[Nightly 44264031228](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44264031228),
attempt 1. CiCd commit `81e10620d4b4442b741d5c4a7420d1c8eb33ff4c`, tree
`57804d63ad97613962e28c2392603cad9d8bf88f`, nightly workflow blob
`03e4599a0409d86ea10733cbd2bb17ea02a68391`, scanner blob
`6beec52b74fd9b4d720be03a96f1071e5d8de260`, reader blob
`afa017ecb81c78fd3bb6437c72c69fdcb0be57f7`.

| Module | Dispatch and scan revision | Release run | Module acceptance |
| --- | --- | --- | --- |
| Commons | `d551e5f3b67653b8793f86afedab355c8a3821da` | [44266704721](https://github.com/Hexalith/Hexalith.Commons/actions/runs/44266704721) | Pass |
| PolymorphicSerializations | `f1e2b45b161627bc2d204e128ffeda086eb413b8` | [44266726524](https://github.com/Hexalith/Hexalith.PolymorphicSerializations/actions/runs/44266726524) | Pass |

| Authenticated artifact | ID | SHA-256 |
| --- | --- | --- |
| Nightly | 14410984147 | `b832abea6746c9dd7c832bd4f8c62075e43376ac83d3be36d3306a40ede35c81` |
| Scan | 14411942153 | `b0111428a63b05f2d1f9cb6a4885d345589015a480a8743ebd69b47803248573` |
| Bump report | 14414051248 | `083cbee75dc29037eeb68f3c36e64713364ca612b5d6f7f1824deeb2d9b503ab` |
| Keepalive | 14413692096 | `e2781a9d04cf7fbcaaa7ea951810b3d0847da9c3ade1dc9002677711d85b7476` |

The historical scan job failed overall. Both module rows passed. The CLI
returned 1 with the pilot checkpoint selected because the Builds v6.3.0 bump
candidate `efb17b0a7d00f8d7945932fa4e919bed3de5aa02` failed. CLI output SHA-256
`410f67c9d228be1939f8fce84443758922b8843aa11b038d756f7a483b5d13f3`, compact
receipt SHA-256 `ce8ab158e53994ce0ba773b83f5b568fd51185dcadc7bba0a9592bbd0618c4b9`.

## Verification baseline

Implementation began on superproject commit
`f36bbb648fada62c866c2d910017bdba7f9ca32d` (tree
`7ad054f31cc860826703720c9a0485299927c5f6`). During implementation the checkout's
main moved to `97538b46caec91945d25b496ff1135bab475f2b0` (tree
`dd6f0531a915405f403dad9854b966975b1de95d`). The story delta and final
verification are based on that current main. The intervening nightly runbook
edit remains present.

### Local qualification before review

The tested staged source tree before this receipt is
`454f1750812a64d509c75c2612977f7b08419aa1`. The standalone Actions job has
the same parsed steps, pins, timeout, report directory and upload settings
as the former Nightly job. Nightly's parsed graph changes the bump need and
the keepalive step label. The App gate binds the new bump dependency and
runtime bytes. Its inventory still reports seven workflows with ten App jobs
and 76 mints.

| Qualified input | Git blob or tree |
| --- | --- |
| `.github/workflows/nightly.yml` | `dfb42e9b535176b4022b0b28a48b853bb7422b99` |
| `.github/workflows/scan.yml` | `b9888477644522638245f64fafd661d74e2d6a10` |
| `tools/nightly_keepalive.py` | `1dfccac92e7958bb0f07af967b46ffd0417a2631` |
| `tools/nightly_runtime.py` | `9151595826dc98a7cb357dc81a66bc2d602329e8` |
| `tools/app-workflow-policy.json` | `55a75944cae7e6b696a681f6df8e42d89c0519bd` |
| `tools/scan.py` | `6beec52b74fd9b4d720be03a96f1071e5d8de260` |
| `tools/scan.py.lock` | `c590b9a3f47f2876468871984ca81de8ff999733` |
| `.jscpd.json` | `7f2bed36ea9f4d7620c175656a0a3290df9d7a39` |
| `tools/jscpd/` | `6e831bac0b40be1b35b58fec6f4d86d42bdf83c5` (tree) |
| `tools/nightly_acceptance.py` | `afa017ecb81c78fd3bb6437c72c69fdcb0be57f7` |
| `tools/tests/test_scan.py` | `82c12b588ecf95b58d2f023c4c885597198adb2d` |
| `tools/tests/test_nightly_acceptance.py` | `f4196cc32d761d03172862e358ea3efe0d5dfc9c` |
| `tools/tests/test_nightly_workflow.py` | `31e4d8235e40c9d959661f72c301ebfe4d360da3` |
| `tools/tests/test_app_inventory.py` | `67a6119ecdf123a10c0b2a3c322ccbf34e5192b8` |

| Local check | Result | Output SHA-256 |
| --- | --- | --- |
| Full scanner suite | 132 passed with pinned jscpd, Node 24.22.1 and PowerShell 7.6.2 | `0d59b36ce620e7183c23b79ce14293250f9aeb07cf4bf9c4e4e9150a9f3dab0f` |
| Real producer-to-reader and six-language detector replay | 2 passed | `5af7fa51a6637081ff279bda59d428f43bb80d33dd182d1ea46345204dc30f00` |
| Nightly and independent scan workflow fixtures | 31 passed | `0cc17466ba6b721bd60b18f02194606ef19e6661ce718003e25d48a47cf25bb9` |
| Acceptance CLI fixtures | 42 passed | `94c5180e761d6c8b1128fe74ef4f25cd0698754c76749942c120130252159911` |
| Nightly runtime | 40 passed | `50190c4c185336016307d83731826ade9fb8e19b95b378f54adce1dbfa16f8b7` |
| Keepalive | 9 passed | `b53bda28a5d7d5fd6d4e4451533e789cc9fbdf07a322647a2a3ee599082c6789` |
| Builds bump producer | 15 passed | `f24d1316440bbbd25be573448167d7b53d26c27b5dacd06a32fd621f55845b22` |
| Validator, including rejected pin | 78 passed | `e51dbb06d17db80427541b6582e609ec2379b3305e329805ac214f8fda04ed06` |
| Repository inputs | 39 passed | `b93ef69eef3ea8e11c0dcf88031d492dfe701b30f78e6c3ee9249a9221233e96` |
| App inventory mutation suite | 21 passed | `37f7691471bec872aab8ab04907307cb6c629c23c7bdcac5208703c0be2a4cd9` |
| App inventory gate | Passed | `6847eabe4b1b062442f1fffb6a90c005692e5f35fdf33b3953eeab139d78235c` |
| Locked render | Passed | `ca59a9019627c8eba6af526c036af2eb054bb5b32522dbd5903168c9d70efcff` |
| Configured actionlint 1.7.12 | All eight parent workflows passed | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The scanner fixture used real temporary Git commits and the pinned detector.
It gave the acceptance CLI the emitted report and summary through fixture
Actions metadata and ZIP responses. It covered historical and independent
success, a missing module row, stale revisions, a scheduled scan's exact
failing rows, duplicate paths and unsupported discovery, and tampered
artifact attribution. A later passing scan could not replace the first
qualifying failure. A separate real bump producer received mismatched
tag-object proof and emitted no candidate. Its reader fixture kept the
module acceptance green and returned a failed pilot checkpoint, independently
of the scan.

### Read-only live scan

The scanner inspected the seven registered modules at their anonymous live
`main` revisions using the controller at `97538b46caec91945d25b496ff1135bab475f2b0`
and its `setup/` tree `e808b9bec9d5aaf0b84f0b41667fd2ebe1986b9a`.
It returned exit 1 with five rows reporting unsupported discovery, zero
duplicate findings and zero run-level errors. For example, Commons reported
unresolved computed subprocess working directories in
`scripts/validate-consumer-package-references.py`. This was a local CLI run.

| Registered module | Scanned commit | Result |
| --- | --- | --- |
| AI.Tools | `91fd549794c72e99d22b69d33ff24e403aede938` | Pass |
| Agents | `54bc11514d7dbf1175a062c224e49272b7a1e5fd` | Pass |
| Commons | `d010dc2b661a74169a39246767710e10c82c9eb8` | Fail |
| Conversations | `7c35922c34cc787b6874c5ba46c091fa2c8ae6b5` | Fail |
| McpCli | `050328500a88406934088ddd2dacc0c7a6165ce7` | Fail |
| PolymorphicSerializations | `8948299a703ee206ff5ea3c1a326673fb49bb2a8` | Fail |
| Works | `d8de7e65f8f20ce16ce395d5d6cc90bd465b3df2` | Fail |

Report SHA-256 `4b32feabb32b5bf6ab83f163a173dd78f6a87bd7f7e956973d8f09e5ae2bc9aa`.
Summary SHA-256 `d2c02e362be48556dbe5b4b2e6d4aaf68a26e9741418d8654179a9b4ed537872`.

### Hosted rollout acceptance

Open. A read-only Actions workflow listing for Hexalith/Hexalith.CiCd at
default-branch commit `8609f8c09d0fbe16ea4c7b7755dd3d28b030aa87` did not
include `scan.yml` and a direct workflow lookup returned HTTP 404. The
CiCd-agent profile was used without environment token overrides. Rollout,
a scheduled scan, and a separate Nightly release verdict remain required to
observe actual Actions artifact metadata, keepalive and exact dispatch coverage.

### Verification after review

| Updated input | Git blob |
| --- | --- |
| `.github/workflows/nightly.yml` | `03af6f126d95d3f1b1be5d67eb70e6e8cadf67b8` |
| `.github/workflows/scan.yml` | `f21efe0012a64ae1bfd245b5705c624ff6ca7747` |
| `tools/app-workflow-policy.json` | `ddde07075e03688a3e8b63c6875a63acead9f408` |
| `tools/tests/test_nightly_acceptance.py` | `304504fcdbe9f08631a76f6222c832da85ccfaca` |
| `tools/tests/test_nightly_workflow.py` | `a88964cad049585b2a068ceb8cadf9c3562b2f7a` |
| `tools/tests/test_scan.py` | `e0f9cdb13c469ed20d44beef879c6ca69dc104d6` |

| Final replay | Result | Output SHA-256 |
| --- | --- | --- |
| Workflow fixtures | 32 passed | `e4859faa10ea8704cdcd19d2b027d838ee438b3df88586144acaf39e6343375b` |
| Acceptance CLI | 42 passed | `33644955d3793e5c1ea4ee54fe8ce81430d3609578265c734947091ed5611ee2` |
| Producer-to-reader and six-language detector | 2 passed | `40c0d8aed934c6243df9f34b22829d2d7868b96c17ebf0b96887ee126bf62b54` |
| Repository inputs | 39 passed | `225657fb7b657c1309a38845b89f99a047974693c633861da4a0674a2d734bb5` |
| App inventory mutation suite | 21 passed | `eac3a4f09dd3203b377da44a1eeecea31078ba36842390bc1d431c6fc3442d60` |
| App inventory gate | Passed | `416343d9f705e2b2b8a15ff70717c5277f81f6ac27ba7fc3264f5555f1c31ff1` |
| Locked render | Passed | `54d515b7b2ab8e70f73a100b4c13cff8e0b62d8e72fb04c9d6818671c73a26d1` |
| Configured actionlint | Eight parent workflows passed | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

All five pin-scoped suites passed with sentinel executables on `PATH` for
`node`, `nodejs`, `npm` and `npx`. No sentinel was invoked. The real
validator fixture rejected substituted remote tag-object proof in pin mode.
The integrated producer negative control rejected the committed pin through
a controlled gate subprocess, emitted no candidate and failed the pilot
checkpoint while the selected module passed.

| Pin suite | Tests passed | Output SHA-256 |
| --- | --- | --- |
| Conversations qualification | 26 | `46132092914279afc0551e89f63504fdb38906b81b1c1080943283ed7be19f4c` |
| Delivery workflow | 26 | `ee9361627d186efce11ef2b7015be596b7110d11220dd405d00324fbd0f24527` |
| Renderer | 52 | `07f3cc5c3537caf78654ffc8a7cfc24361b3d9eba945a550de4f101a4c691052` |
| Legacy renderer | 16 | `e2e4cf7ebd1759a3ce11b091ff4e354c895b6ad988ca0b1b24fb1187ff87ae74` |
| Validator | 78 | `f4c2a372e465723b8a1da833e0f4262912f3a897905869d56b0f77cc55a3f9d1` |

## Auto Run Result

Status: done for implementation and local review. Hosted rollout acceptance
is open. The workflows and story are committed locally.

- `.github/workflows/scan.yml` moves the locked scan to an independent
  daily and manually dispatched workflow with the two-member attempt artifact.
- `.github/workflows/nightly.yml` makes bump depend only on publication and
  leaves the detector runtime in scan. The existing publish, candidate-check
  and propagation gates continue to run.
- `tools/nightly_keepalive.py`, `tools/nightly_runtime.py` and
  `tools/app-workflow-policy.json` add the exact CiCd scan enable route and
  bind the revised dependency and runtime.
- The runbooks document scan operation, retention and exact dispatch
  coverage. The fixtures exercise workflow conditions, the unchanged reader,
  real detector output, failed pin verification and App policy drift.

Review applied seven medium and three low distinct patches, deferred one
low Actions summary issue and rejected three observations as patch requests.
The triage log records the reason for each finding. The follow-up is
recommended for the hosted workflow-to-reader handoff. The pinned upload
source and local fixtures cover the archive layout, while a scheduled Actions
run must still establish the actual artifact attribution and exact module
coverage. The local base is `97538b46caec91945d25b496ff1135bab475f2b0`.
Hosted main moved to `8609f8c09d0fbe16ea4c7b7755dd3d28b030aa87`, with
independent release-dispatch timing changes, during this work.
