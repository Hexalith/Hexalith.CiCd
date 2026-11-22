---
title: One authenticated Builds lookup per delivery run
type: bugfix
baseline_revision: 7dc3a2ef50b06ed0b3e6cad93736a8d07741b830
created: '2026-11-22'
status: done
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** Each isolated delivery slot repeats anonymous Builds metadata verification during preflight and application. Refusals can block several modules sharing a tag.

**Approach:** Reuse one authenticated acceptable-release proof per distinct tag in private delivery state bound to the run and attempt. Compare every acquired raw tag and peeled commit with that proof before exporting or executing release code.

## Boundaries & Constraints

**Always:** Follow approved 2026-11-18 proposal §4.1 story 28-2 and 2026-11-19 added acceptance. Preserve published, immutable, bot-author, timestamp, annotated-tag and live-main ancestry checks; fail closed before affected ref/module writes. Prefer the existing CiCd App token, else module App token. Keep private bounded state, budgets, accepted-ref repair, races, and sequential child-slot behavior. Persist refusals without retrying metadata under another credential. Reports and state must exclude credentials and response bodies.

**Never:** Change production files beyond `tools/deliver.py` and `tools/delivery_runtime.py`; change bootstrap, its pin, workflows, token scopes, audits, test fixtures or tests except the single request-assertion correction authorized below. Story record and story-dispatch updates and disposable qualification jobs are workflow bookkeeping. Do not claim the week of hosted acceptance before observation exists.

**Current resolution dispatch (2026-11-22, run `20261122-125939-b817`):** Production changes remain limited to `tools/deliver.py` and `tools/delivery_runtime.py`. The human authorized one test exception: correct only the request-assertion block in `tools/tests/test_deliver.py::test_failed_global_with_passing_names_keeps_refs_and_repairs_accepted_render` to require nonempty Builds-only requests, the exact existing CiCd fixture token on every request, and exactly one release-tag read. Preserve every existing accepted-ref, skipped-advancement and rendered-repair assertion. All other tests and fixtures remain unchanged. This resolution supersedes the earlier two-file-only/test-freeze dispatch, including the proposal handoff restriction, solely for this correction. The corrected controller suite and all other required verification suites must pass; disposable qualification does not waive a failing tracked suite.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Shared tag | 17 modules, separate processes, preflight/application | One release metadata proof, every acquisition identity checked | None |
| Multiple tags | Two modules share tag A, another uses B | One proof per tag | Isolate affected tag |
| Scope | Different run, attempt, or private workspace | No reuse of foreign proof | Refuse mismatched state |
| Refusal | HTTP 401/403/404/429/5xx | No affected write; cached refusal | `Builds release unverified (HTTP n)` plus bounded allowlisted request/rate headers |
| Unacceptable | Draft/mutable/foreign author/nonancestor or malformed object | No advancement/application for that tag | Preserve existing checks |
| Acquisition differs | Raw tag or peeled commit differs after verified proof | No export, execution or affected write | Identity diagnostic |
| Credentials | CiCd token, module-only token, neither | Prefer CiCd; fallback module; anonymous only with no write possible | No credentials in state/reports |
| Accepted repair after global failure | Existing accepted refs, rejected candidate, shared tag, both fixture tokens available | Advancement skipped; accepted refs retained and accepted render repaired; nonempty Builds-only requests use the exact existing CiCd token, with one release-tag read | No module administrative API requests; preserve all existing repair assertions; correct only the named test's request assertions and require its controller suite to pass |

</intent-contract>

## Code Map

- `tools/deliver.py:trusted_state`, `apply_module`, `operate`: all release acquisitions pass through the transport; operation reads private bootstrap state/report and receives only the two existing App tokens.
- `tools/delivery_runtime.py:Transport.builds/_builds`: currently repeats metadata then fetches Git, compares raw/peeled identities and validates capability before export. Split proof from acquisition while preserving direct-call compatibility.
- `tools/delivery_runtime.py:API.get`, `clean`, `atomic`, `read_state`: bounded HTTP/state and secret scrubbing reuse points.
- Read-only `tools/delivery_bootstrap.py:select/invoke`: root is private, state is fresh per selection, report carries run_id/run_attempt; children receive no GitHub context except tokens. Do not modify bootstrap or pin.
- Read-only `tools/tests/delivery_support.py:Workspace/fixture_transport`: real Git, exact released perimeter and subprocess qualification seam. Existing runtime/controller/bootstrap/workflow tests preserve safety contracts.
- `tools/tests/test_deliver.py::test_failed_global_with_passing_names_keeps_refs_and_repairs_accepted_render`: the fixture records paths/authorization and supplies the inert CiCd token. Only its request-assertion block may change, replacing the anonymous-request expectation with the authenticated Builds-only, nonempty and single-release-read requirements above. Preserve all existing repair assertions and fixture inputs; all other tests remain read-only.
- AD-6/AD-10 and story 7 preserve accepted-ref repair, tag object plus commit comparison, bounded private state and child isolation. All predecessor story records are done; no open continuity decision.

## Tasks & Acceptance

**Execution:**
- [x] `tools/delivery_runtime.py` -- persist per-tag verification outcomes in run/attempt-bound private state; authenticate metadata and retain all acceptability/identity checks; provide bounded, sanitized HTTP refusal diagnostics.
- [x] `tools/deliver.py` -- bind transport to existing private state/report and available tokens for each operation without changing bootstrap interfaces.
- [x] Both files -- qualify matrix via disposable real-Git/subprocess fixtures; inspect complete diff and bootstrap/pin identities.
- [x] Previous attempt -- ran every relevant suite unchanged and reported the incompatible anonymous-request assertion; the controller suite failed 1/20 and remains a gate.
- [x] `tools/tests/test_deliver.py` -- make only the authorized request-assertion correction in the named test, preserving every existing repair assertion and fixture input.
- [x] Run the corrected controller suite and every other required suite; all must pass, with no other test changes, skips or gate waivers.
- [x] Story record -- record exact baseline, verification digests and hosted observation limits.

**Acceptance Criteria:**
- Given 17 modules sharing a tag and separate slot processes, when delivery preflights and applies them, then one authenticated release read occurs and all acquired objects match the verified raw/peeled identities.
- Given two modules sharing one tag and a second tag, when delivery runs, then each distinct tag has one proof across preflight and application.
- Given a refusal or unacceptable release, when any affected module reaches either write, then it is blocked, with bounded credential-free diagnostics and no fallback credential retry.
- Given proof state from another run or attempt, when consumed, then it cannot authorize a write.
- Given global validation failure with existing accepted refs and both fixture tokens, when the named controller test repairs the shared-tag modules, then advancement stays skipped, accepted refs and rendered content remain correct, and nonempty recorded requests are all Builds-only with the exact existing CiCd token and exactly one release-tag read. Correct only that test's request-assertion block to enforce these requirements, preserve every existing repair assertion and fixture input, and require the controller suite and all other required suites to pass. Never weaken authentication or waive a tracked suite failure.
- Given the deployed change, when one week of push and scheduled deliveries has elapsed, then no Builds 403 is observed, or the existing-scope refusal is reported without widening access. This remains pending until hosted evidence exists.

## Spec Change Log

- 2026-11-22 resolution for run `20261122-125939-b817` -- Human authorized the narrow request-assertion correction specified in the current resolution dispatch, superseding the earlier two-file-only/test-freeze dispatch solely for that correction. The story manifest dispatch is aligned with this exception. Every existing repair assertion, fixture input and full verification gate remains required. This resolution changes only the spec and story dispatch; the next development session corrects the test and reruns verification. Implementation evidence and the blocked Auto Run Result below predate this resolution and do not establish a passing corrected suite.

- 2026-11-22 earlier dispatch (superseded by the resolution above) -- The user renewed the two-file implementation boundary. This superseded the earlier test-edit exception. Production files were at the recorded baseline; previous implementation evidence below was historical and had to be reproduced against the new changes.

- 2026-11-22 -- Human authorized the narrow request-assertion correction in the single named controller test to reconcile authenticated metadata acceptance with the test freeze. All existing repair checks and the full verification gate remain required. This resolution changes spec content only; the next development session performs the test correction and verification.

## Review Triage Log

### 2026-11-22 — Review pass
- verdicts: 10 findings — high 0, medium 3, low 2, false 5, maybe-false 0
- findings:
  - `[false]` `[reject]` Intent audit: local fixtures do not establish one week of hosted acceptance — the approved criteria and this story explicitly leave that observation pending; the diff makes no hosted-success claim and this session performs no deployment.
  - `[false]` `[reject]` Intent audit: broad qualification is outside the tracked repair-test diff — the named test intentionally exercises accepted repair, while the parent read and independently executed the permitted disposable matrix and targeted controls. The user expressly freezes every other tracked test and fixture.
  - `[medium]` `[patch]` Blind hunter: malformed annotated-tag and comparison identities enter cached refusal state — parent reproductions confirmed both paths. Delivery-bound diagnostics now preserve canonical Git identities and substitute a fixed label for other values; unbound direct-call diagnostics preserve their frozen compatibility contract. Disposable state/report controls cover both malformed paths and both canonical paths.
  - `[false]` `[reject]` Blind hunter: every unexpected exception becomes a permanent refusal without its class — permanent fail-closed refusal is required after interrupted or failed verification. The production API wraps transport/JSON failures and validates object fields; tracing found no additional reachable arbitrary-message path beyond the malformed identities patched above. No programming-error retry or exception-class diagnostic is required by the intent.
  - `[low]` `[reject]` Blind hunter: HTTP refusal diagnostics omit the failed operation — status and seven bounded request/rate headers meet the specified diagnostic contract. Operation ambiguity is unlikely to impede ordinary diagnosis using the request ID; adding operation classifications introduces branches beyond a direct correction.
  - `[false]` `[reject]` Blind hunter: the 85-entry bound lacks a named explanation — current callers permit one candidate preflight and four accepted application attempts per module, so 17 times five covers every reachable distinct-tag acquisition. No current caller exceeds the bound; a naming preference establishes no present defect.
  - `[medium]` `[reject]` Blind hunter: machine-local qualification cannot be reproduced from a clean checkout — this limitation is real, but adding versioned tests/fixtures exceeds the user's explicit test freeze and two-production-file boundary. The permitted disposable runners, identities and results are recorded; durable regression migration needs separately scoped work.
  - `[false]` `[reject]` Blind hunter: hosted observation lacks a deployment identity and start — no deployment exists in this session, so inventing those fields would be incorrect. The approved proposals assign rollout and observation to the CiCd developer/maintainer; hosted acceptance remains explicitly pending.
  - `[low]` `[reject]` Blind hunter: the inherited story repeats superseded evidence — the text contains compact decisions, source identities and digests, not raw logs or executable snapshots. Its proposed consolidation edits this build's spec, which the review workflow rejects as a finding remedy; no evidence-cleanup scope is introduced here.
  - `[medium]` `[patch]` Verification gap: existing two-tag controls share one release identity and accept a first-proof mutation — added an independent disposable control with two annotated tags whose raw and peeled identities differ. Both accepted versions apply successfully, and the exact first-proof mutation blocks the second tag with the expected identity mismatch. Existing tracked tests, fixtures and retained runners remain unchanged.

The edge-case layer returned no findings. All four layers ran; the fourth
started when one of the three available child-agent slots became free.
There are two patched entries, both medium, and no deferred entries. A follow-up
review is not recommended: targeted controls cover each patch and no specific
unverified patch risk remains. Hosted observation is a separate pending criterion.

## Design Notes

Bind proof state to private root, start time, source/candidate and report run/attempt, since the immutable caller strips GitHub environment variables. Cache only bounded identities or sanitized failure text, never tokens, HTTP bodies or exported code. Retain identity checking on every acquisition, including cache hits and retries.

## Verification

- `run-with-temp python3 tools/tests/test_deliver.py`
- `run-with-temp python3 tools/tests/test_delivery_runtime.py`
- `run-with-temp python3 tools/tests/test_delivery_bootstrap.py`
- `run-with-temp python3 tools/tests/test_delivery_workflow.py`
- `run-with-temp python3 tools/tests/test_nightly_runtime.py`
- Disposable qualification: baseline and final proof counts, two tags, token fallback, refusals, malformed acceptability, annotated/raw/peeled mismatch, scope mismatch and credential absence.
- `git diff --check`; unchanged bootstrap/pin diff.

## Historical Implementation Evidence (2026-11-22, previous attempt; not current verification)

The controller binds the transport to the private selection, source/candidate,
start time, and report run/attempt. Metadata uses the available CiCd token first,
otherwise the module token. A selection-specific private JSON file retains at
most 85 tag outcomes: raw/peeled identities or a sanitized refusal. Every Git
acquisition still compares both identities before capability checks and export.
HTTP refusals retain only status and seven allowlisted request/rate headers,
each limited to 128 sanitized characters; tokens, their Git Basic encoding,
response bodies and other headers are excluded. Refusals survive child exits
and a later change of available token without another metadata request.

- Baseline commit: `7dc3a2ef50b06ed0b3e6cad93736a8d07741b830`; tree:
  `bcd456f3cbd66e52ede55266ac8cb9cf52a3877b`. Baseline controller/runtime blobs:
  `e8567c561dcd73d3002a42ab4e53a5f470027532` /
  `c98cfcffdd7eb4c4f52e9629f6fadf57b790c554`.
- Measured baseline: 17 modules, one tag, full subprocess delivery passed;
  34 release metadata reads, all anonymous, in 15.46 seconds.
- Final disposable qualification: 26 cases passed. The 17-module case used
  17 distinct child processes, one CiCd-authenticated release read and 34
  identity-checked acquisitions across preflight/application (16.78 seconds).
  Two tags required two proofs; module-token-only repair required one proof;
  neither token produced zero metadata reads and zero writes.
- Negative controls passed: cached 401/403/404/429/500/503 despite a later
  different available credential; draft, mutable, foreign-author, unpublished
  and malformed releases; malformed Git objects and nonancestry; foreign run,
  attempt and workspace proof state; changed annotated raw identity and changed
  peeled commit on cache hits; annotated-object identity mismatch and cycle.
  Affected writes were blocked, with bounded diagnostics and no credential,
  response-body or unknown-header leakage into state/reports.
- Disposable runner SHA-256:
  `2a129ab686dfd521d872418f0822059f8d3232cd018e4b346209e92b071ab1ca`.
  Generated fixture adapter SHA-256:
  `ecfac4c29c6766aa3361d9dbac51b83ef714296ed5c79a353cd7da693ab70a52`.
  Canonical JSON result-summary SHA-256:
  `7145213344ad85e4e226513adfdd4dcbbb4b36a689e35b3318de49c8398c75f4`.
  Raw fixtures/logs remained under `run-with-temp` and were removed when the
  job finished; no tracked tests were added or changed. A requested runnable
  copy remains outside the repository at
  `/home/administrator/.cache/codex/qualifications/story-28-2/tools/qualify.py`;
  invoke it with `run-with-temp python3` and that path.
- Two additional controls passed on those same final source fingerprints.
  The peeled-only control holds the verified and acquired annotated raw tag
  identity equal while their peeled sources differ; it reports both source
  identities, performs zero Builds exports and blocks both affected writes.
  This supplements the matrix's raw-only annotated-tag change, whose peeled
  commit stays equal. The multiple-tag control exercises two tag A preflights,
  two tag A applications and one accepted tag B repair with exactly two release
  metadata reads. Retained runnable control:
  `/home/administrator/.cache/codex/qualifications/story-28-2/tools/targeted.py`;
  invoke with `run-with-temp python3` and that path. Control/result SHA-256:
  `e1241cea9ccbfb6532201523779e1d66b9209b954112368e862e55b46ef57911` /
  `fb6b50e144eec4f3ad00ad46f0adf216077c826605930ffdbb9e93f5443bb955`.
- Interruption control found and closed a gap: before the final fix, exiting
  `77` immediately after the first release API response left no proof, and the
  next isolated slot repeated metadata (two reads total), advanced and pushed.
  The final implementation atomically records an incomplete refusal before
  requesting metadata, replacing it only on verification completion. Repeating
  that interruption left a private incomplete proof: the next slot made no
  additional metadata request and no affected write (one read total).
  Pre-fix adapter/result SHA-256:
  `d4f1d03787d4a453f5070ad3b1c2bb871670f0db6150767092f110f89522abf4` /
  `fd4fe7c47ddf3d57782470ee6993906bf138665f955205cd8bd1d7b7b93bc92f`.
- Compatibility control reproduced an `AttributeError` when a nightly
  transport subclass did not call the delivery superclass constructor.
  Optional scope/token attributes now use `getattr` defaults. The final
  disposable control passes with two anonymous direct proof calls and no
  initialized delivery cache attributes; parent verification additionally
  reports the unchanged nightly runtime suite passing 39/39.
- Existing suites during implementation: runtime 21/21, bootstrap 9/9 and
  workflow 17/17 passed unchanged. The first controller run passed 18/20:
  its same-directory re-selection failure was fixed and its unchanged
  idempotence test then passed 1/1. The remaining assertion at
  `tools/tests/test_deliver.py:80` requires anonymous Builds requests and
  conflicts with this story's authenticated-read acceptance; it was left
  unchanged. Independent final verification is recorded below.
- Final qualified controller/runtime Git blobs:
  `5df04dae6f79c0afd43aad39a41e2b012827ecb1` /
  `a28670792433c7d63e8ad2f76541ce49dd849375`. Their SHA-256 fingerprints,
  unchanged from the start through completion of final qualification, are
  `f313fcc85524b851fbaa99595a77a1813c13046379bc18ccbc1b5a81e3c0e901` /
  `6661866f8e62d66b70d3633b22d6e633f15113b1f34b94f485992c8cc6473746`.
  Production diff SHA-256:
  `96e202b70805a30157c1f42386b860f3950522e1dd787406e93ad633f5ae039b`.
- Complete production diff inspected; `git diff --check` passed. Bootstrap,
  delivery workflow/pin and tests have no diff. Bootstrap/workflow SHA-256:
  `4432b135997e953c18d86e5ae249fb3fbe28514fcc75ca543847e4b1773b3beb` /
  `3643794dbe66ebf4651821909066b7ec28f3ab4c2f9440bc55bc01628f8ae9b1`.

Hosted acceptance remains pending: no deployment or week of push/scheduled
observations was performed here. Existing-scope access refusals must still be
reported as refusals; these fixtures establish no broader token permission.

## Pre-resolution Implementation Evidence (2026-11-22)

Implementation is restricted to `tools/deliver.py` and `tools/delivery_runtime.py`.
The controller binds transport state to the canonical private root, selection
start, source/candidate, run and attempt. At most 85 tag outcomes are retained.
An incomplete refusal is written before metadata is requested; a verified result
stores only raw tag and peeled commit identities. All metadata uses the existing
CiCd token, or otherwise the module token. Every acquisition compares both
identities before capability reads and export. HTTP refusals retain status and
seven allowlisted headers, each sanitized and limited to 128 characters.
Credentials, Git Basic encodings, response bodies and unrelated headers are
excluded. Bootstrap, workflow pin, tests and fixtures have no diff.

- Baseline commit: `7dc3a2ef50b06ed0b3e6cad93736a8d07741b830`; tree:
  `bcd456f3cbd66e52ede55266ac8cb9cf52a3877b`. Controller/runtime baseline
  blobs: `e8567c561dcd73d3002a42ab4e53a5f470027532` /
  `c98cfcffdd7eb4c4f52e9629f6fadf57b790c554`.
- Fresh disposable baseline: 17 modules, 34 anonymous release reads, 18.42 s.
  Canonical result SHA-256:
  `48629de56d8b30556859befb3abbeeb4a6ee2c300b9dc812564bbc49c0fe74e0`.
- Current disposable matrix: 26/26 passed. Seventeen child processes made one
  CiCd-authenticated release read and 34 identity-checked acquisitions (17.89 s).
  Shared/distinct tags, module-token fallback, absent tokens, cached HTTP
  401/403/404/429/500/503 after a credential change, malformed/unacceptable
  releases, nonancestry, foreign run/attempt/workspace, raw/peeled changes,
  annotated identity/cycle errors, interrupted verification and a legacy
  subclass without superclass initialization all passed. State/report privacy,
  bounds and credential absence were checked. Runner / adapter / canonical
  result SHA-256: `2a129ab686dfd521d872418f0822059f8d3232cd018e4b346209e92b071ab1ca` /
  `ecfac4c29c6766aa3361d9dbac51b83ef714296ed5c79a353cd7da693ab70a52` /
  `6f34f5430ff6a78628aba9f4fa4c6ef3f4a314f96b5b67d1364009027c4992fc`.
- Two additional controls passed: identical raw annotated identity with a
  different peeled commit produced zero exports/writes; two tags across
  preflight/application required two release reads. Runner / result SHA-256:
  `e1241cea9ccbfb6532201523779e1d66b9209b954112368e862e55b46ef57911` /
  `e840af15e391cd0923131df00dafdcbf77b373aa757f167772cf747f54b696b6`.
- The named accepted-render repair passed in a disposable assertion adaptation
  preserving every original repair check and requiring nonempty Builds-only
  requests, exact CiCd authorization and one release read. Tracked tests remain
  unchanged; this adaptation does not waive their failure. Runner / adapted
  source SHA-256: `d1a78bfc71eb4cce18944fb241e1762c95f971e93fe17dff651babb589de6d1f` /
  `f51c561830c75d4c89723d899950ad46c3d2edf079fc1ec3c9f34a083f68002b`.
- Runnable controls remain outside the repository under
  `/home/administrator/.cache/codex/qualifications/story-28-2/tools/` as
  `qualify.py`, `targeted.py` and `authenticated_repair.py`. Invoke with
  `run-with-temp python3 PATH`. Raw logs/workspaces were confined to the private
  temporary workspace and removed after the jobs finished.
- Qualified controller/runtime blobs:
  `26c8c62fff988a7da8719661f69f9c75ec074a02` /
  `3839fb6eaa39ee7b3119904ed9f448daf40e2b1a`; SHA-256:
  `94fbe91d4ce5b18a43b52c945cd36b3b4a7090fb87127192f7e4c455e91c7df7` /
  `1e4c752c8a776f395fc9a55dc288cb3e85a14bd159827dcf809c353683d69994`.
  Production diff SHA-256:
  `d601daed04928e0ccbbe2531df05486b6001bef7f7a033558ec2f4569ba23403`.
- Bootstrap/workflow SHA-256 remain
  `4432b135997e953c18d86e5ae249fb3fbe28514fcc75ca543847e4b1773b3beb` /
  `3643794dbe66ebf4651821909066b7ec28f3ab4c2f9440bc55bc01628f8ae9b1`.

Hosted acceptance remains pending. No commit, push or deployment was performed;
no week of hosted push/scheduled observations has been collected.

## Pre-resolution Independent Parent Verification

The parent inspected the complete staged diff and independently reran every
required suite under `run-with-temp`, with raw logs inside its private `TMPDIR`.
No test was changed, disabled, skipped or waived. All child jobs finished before
returning. Log SHA-256 values identify raw output removed at job completion.

| Suite | Result | Log SHA-256 |
|---|---|---|
| `test_delivery_runtime.py` | 21/21 passed | `a56acb910b9ad45af164727c646d264d41bc0aa11e498d5ac742b1a3d719103f` |
| `test_delivery_bootstrap.py` | 9/9 passed | `df29852c5bee21a212be03c71b6d5381fd3e920da41d46813384970f5dc17d8e` |
| `test_delivery_workflow.py` | 17/17 passed | `de951655aa78c67e994af76dbed2c6a894f4ddb17e6577c80d4f2e0d4b3346bb` |
| `test_nightly_runtime.py` | 39/39 passed | `6f4e7ff1e97707666bab55e73fae96742481097a75051bb948e509f23699f60e` |
| `test_deliver.py` | 19/20 passed, one incompatible request assertion | `9d17dc2ace6dda00ef93313fe94d5cf546b0ef2b074367b80d81ce3b73ddf816` |

Matrix audit: the 26-case runner covers shared tags, run/attempt/workspace scope,
HTTP refusals, unacceptable releases/objects, identity mismatches and all three
credential cases. The targeted runner covers both tags across preflight and
application and peeled-only mismatch before export. The disposable authenticated
repair case preserves all original accepted-ref/render assertions and verifies
Builds-only requests, exact existing CiCd authorization and one release read.
These controls passed against the exact qualified source identities above.
They establish the requested behavior and do not waive the tracked suite failure.

## Resolution Implementation Evidence (2026-11-22)

The production implementation is confined to `tools/deliver.py` and
`tools/delivery_runtime.py`. The only test change is the authorized request
assertion block in the named accepted-render repair test. It now requires
nonempty Builds-only requests, exact `Bearer inert-cicd-token` authorization
on every request, and exactly one release-tag read. Fixture inputs and every
accepted-ref, skipped-advancement and rendered-repair assertion are preserved.
No other test or fixture changed; no test was skipped or waived.

All required suites passed under `run-with-temp`. Raw logs and disposable
workspaces stayed beneath the private `TMPDIR` and were removed after each
job completed; all child jobs finished before returning.

| Suite | Result | Log SHA-256 |
|---|---|---|
| `test_deliver.py` | 20/20 passed | `34235e4077b7e072b97bdeb3f1e50b2c55064b22a724fa9eae110343a8cac8c4` |
| `test_delivery_runtime.py` | 21/21 passed | `4c2c113143cc62b674400487aa80c53c629578f2e9065533ecdc23a194dd8d95` |
| `test_delivery_bootstrap.py` | 9/9 passed | `25a0954ffecbff6d8280c6587324c8e30e631b00446a128889e28b31935e29a3` |
| `test_delivery_workflow.py` | 17/17 passed | `e2221c7e63ff86be097620aea004a19200b7e61b8256b076726080cd7eee4fe8` |
| `test_nightly_runtime.py` | 39/39 passed | `17dcaa02ab1589ce173c31cef6426ff7ebb41159a37517d3810e738dedb69f83` |

- Baseline commit/tree remain `7dc3a2ef50b06ed0b3e6cad93736a8d07741b830` /
  `bcd456f3cbd66e52ede55266ac8cb9cf52a3877b`. A fresh disposable baseline
  using its exact controller/runtime blobs reproduced 34 anonymous release
  reads for 17 modules (16.97 s). Canonical result SHA-256:
  `c89bc876262bcd67c948eebced91f74d8e330945c33f0db9df05d4681d5639ae`.
- The retained 26-case qualification passed against the final production
  source: 17 isolated slot processes, one CiCd-authenticated release read,
  and 34 checked acquisitions (16.52 s). Two tags, module-token fallback,
  absent tokens, cached HTTP 401/403/404/429/500/503 after a credential change,
  unacceptable releases, malformed/annotated objects, nonancestry, foreign
  run/attempt/workspace state, raw/peeled mismatch, interrupted verification,
  privacy/bounds and legacy subclass compatibility all passed. Runner /
  generated adapter / canonical result / log SHA-256:
  `2a129ab686dfd521d872418f0822059f8d3232cd018e4b346209e92b071ab1ca` /
  `ecfac4c29c6766aa3361d9dbac51b83ef714296ed5c79a353cd7da693ab70a52` /
  `fc971a9f5eaf44f2607b9a9eb553d6e5d9e9e0409e5e67540da86a708d4e69d5` /
  `7490a203e3dd73e503cf043e3414e1be7116718fc9e68c0cea321d98d45318b0`.
- Both retained targeted controls passed: a peeled-only mismatch with identical
  raw annotated identity exported nothing and blocked affected writes; two
  tags across preflight/application needed exactly two release reads. Runner /
  canonical result / log SHA-256:
  `e1241cea9ccbfb6532201523779e1d66b9209b954112368e862e55b46ef57911` /
  `c7e2454ef4ff6683b0a2fa9b50aec9cf5d28305d5eedb1303ee8ea717bfda5dd` /
  `eb7fe9794e1a3e91262c3c0ee2d8a9123d56bd44c480cc4f7f6bb376d813576d`.
- Final controller/runtime blobs are `26c8c62fff988a7da8719661f69f9c75ec074a02` /
  `3839fb6eaa39ee7b3119904ed9f448daf40e2b1a`; their SHA-256 values are
  `94fbe91d4ce5b18a43b52c945cd36b3b4a7090fb87127192f7e4c455e91c7df7` /
  `1e4c752c8a776f395fc9a55dc288cb3e85a14bd159827dcf809c353683d69994`.
  Corrected controller test blob/SHA-256:
  `0424b7c51e65c2bf25035570813c0192659b9d41` /
  `9ea5e87bd30d69b6e8cb5c92551d3b5c23ea2f67664211635cdec7752d816a05`.
  Production diff SHA-256 remains
  `d601daed04928e0ccbbe2531df05486b6001bef7f7a033558ec2f4569ba23403`.
- The complete production/test diff was inspected and `git diff --check`
  passed. Bootstrap and workflow/pin have no diff. Bootstrap/workflow
  SHA-256 remain `4432b135997e953c18d86e5ae249fb3fbe28514fcc75ca543847e4b1773b3beb` /
  `3643794dbe66ebf4651821909066b7ec28f3ab4c2f9440bc55bc01628f8ae9b1`.

Hosted acceptance remains pending. No commit, push or deployment was performed
by this implementation session; no week of hosted push/scheduled observations
has been collected.

## Resolution Independent Parent Verification (2026-11-22)

The parent read the complete staged diff and independently reran every required
suite and both retained qualification runners under `run-with-temp`. All passed;
no tests were skipped or waived. All verification jobs finished. Raw logs and
disposable workspaces were removed by their wrappers; only digests remain here.

| Suite/control | Result | Log SHA-256 |
|---|---|---|
| `test_delivery_runtime.py` | 21/21 passed | `3e51a6904396d377f9e40150f8ecff375c4345084e6fd627b2e8f7241ced7a6a` |
| `test_delivery_bootstrap.py` | 9/9 passed | `b2197e98800dbdad35896260a878eb42c664605ed631997f452c1d2a787d2622` |
| `test_nightly_runtime.py` | 39/39 passed | `bfcd987c5d15c7ec7c582eedc2a45cdf82d76c89a4db0a92878659ecae64be2f` |
| `targeted.py` | 2/2 passed | `8d2b39dacfec7134342ec63ec94f6491ccb316290034eeb4009a42ba0990a212` |
| `test_delivery_workflow.py` | 17/17 passed | `32027730df9ff6eb46f874f5b63dced5d5008638461dc4c917be1050eb33c179` |
| `qualify.py` | 26/26 passed | `a0812824c5ac99081c6640bd0304efc6ed52e7bd28a7fb38c242a641c19dec00` |
| `test_deliver.py` | 20/20 passed | `cb67919b0fe70981161537bea8985563d9de20f7e64bf5a4c0ba73e2a36f8c65` |

The matrix audit passed: the 26-case runner covers shared tags across 17 slot
processes, distinct tags, run/attempt/workspace scope, cached HTTP refusals,
unacceptable releases, object identities, all credential cases, interruption,
and credential-free bounded state/reports. The targeted runner covers two tags
across both phases and a peeled-only mismatch before any export. The corrected
controller case covers accepted-ref retention, skipped advancement and accepted
render repair with nonempty Builds-only requests, exact existing CiCd
authorization and one release read. Every covering control ran and passed.

An AST comparison against the baseline confirmed that all fixture inputs and
assertions outside the authorized request block are identical. The staged
file inventory confirms no other test or fixture changes. `git diff --check`
and `git diff --cached --check` passed. Bootstrap and workflow/pin have no diff.
Source identities match the Resolution Implementation Evidence above.

Independent canonical qualification result SHA-256:
`15d7e528d428bf0e15af005acb580a1461565302004546168ed9f1fb82f97cdd`;
targeted result SHA-256:
`fe1e4600f4904a3520c00832a0e218e79a00afe71677b430d98d887bf0121f3b`.
Hosted one-week acceptance remains pending; no deployment was performed.

## Final Verification After Review Patches (2026-11-22)

The parent inspected the complete patched production/test diff and reran every
required verification command and disposable qualification entry point. All
106 tests and 34 qualification controls passed. No test was skipped or waived;
all child jobs finished and their private workspaces/logs were removed.

| Suite/control | Result | Log SHA-256 |
|---|---|---|
| `test_deliver.py` | 20/20 passed | `63b42160b725bb64eb3eba26e44e23397760532d46a7ee1cc13407d1916eff23` |
| `test_delivery_runtime.py` | 21/21 passed | `74d643b47c171b0957412388d1ad4cf23fa43c24eb49a4c496941e384c35b28b` |
| `test_delivery_bootstrap.py` | 9/9 passed | `6f852aa67121dd544261538f04d1ab8d12d7cfc20015423aba4336e3f3268131` |
| `test_delivery_workflow.py` | 17/17 passed | `a84c2104e9c5cb34ae319826059dec2d38fddec0da09beebfbc7422dc25434b6` |
| `test_nightly_runtime.py` | 39/39 passed | `b9a4e249455d88eda416392925542a0d806e8ade8b3ecccbf62d2224753c9583` |
| `qualify.py` | 26/26 passed | `e27594efaf7db4ab9e1a514ba2c2f4248d9b8c6932ea92622863c2d425d3ea8f` |
| `targeted.py` | 2/2 passed | `d4240b392229e9f39e78ea0beefe4a665519da1086f1c66024604084acd82f9b` |
| `distinct_tags.py` | 6/6 passed | `00a92876be081a8f6f08b0db59a7f153a08ff2257bca756022cd1a27cd586a95` |

Final source identities (superseding the pre-review runtime fingerprint):

- Controller blob: `26c8c62fff988a7da8719661f69f9c75ec074a02`;
  SHA-256: `94fbe91d4ce5b18a43b52c945cd36b3b4a7090fb87127192f7e4c455e91c7df7`.
- Runtime blob: `e53d73c39a1d0ae87ef85ff34991a3405fc14977`;
  SHA-256: `287a3a38b270899342f5f9557df882c1cfbc878872e73ae4f4128f22a4fa1dec`.
- Corrected test blob: `0424b7c51e65c2bf25035570813c0192659b9d41`;
  SHA-256: `9ea5e87bd30d69b6e8cb5c92551d3b5c23ea2f67664211635cdec7752d816a05`.
- Production diff SHA-256:
  `8e8a11f499c0c786af8abee82164a71bf248be8ff8577e5be0765434f7fc070f`.
- Bootstrap and workflow/pin remain unchanged at blobs
  `ea0a9a34021466e6a48099845ebe0fa40ad7d002` /
  `a10275be9c3ae186cfa301d598731c484e2ca260`.

Final canonical result SHA-256 values:

- `qualify.py`: `bed8e36b96f32b351dcffa90592f3d01375455fe543821b2083e1d9c15a43236`.
- `targeted.py`: `4499b778d7c52a3decb3995a164c1422a3833b7ebaea283bb8125326fc20067c`.
- `distinct_tags.py`: `74a94cf278212afbaba97bfa1d2df4a5cc984400329ce110227f455b3bcfa053`.

The new independent runner remains outside the repository beside the retained
controls as `distinct_tags.py` under the qualification tools directory named
above. Runner SHA-256:
`9ee3076a38f7c0f41f771d88288d159a10ec89aee698d59f7af9ea70252e71c2`;
generated adapter SHA-256:
`c1a545c0d59d85995201a62bef089f2a621f23a67a18acc6b8aa96ede3c7f9f7`.
It verifies two successful distinct annotated-release repairs, detects the
first-proof mutation, and checks both malformed and canonical annotation and
ancestry diagnostics. Tracked tests/fixtures and prior runners are unchanged.

## Auto Run Result

Status: done (local implementation, review and verification).

Implemented one authenticated acceptable-release proof per distinct Builds tag
in private state scoped to selection, delivery run and attempt. Refusals,
including incomplete verification, are retained without credential retries.
Every acquisition still compares raw tag and peeled commit before exporting
or executing release code. Delivery diagnostics are bounded and omit credentials
and arbitrary response content.

Files changed:

- `tools/deliver.py`: bind each isolated operation to delivery proof state and existing tokens.
- `tools/delivery_runtime.py`: authenticate and persist per-tag proofs/refusals; retain all acquisition and acceptability checks; sanitize bounded diagnostics.
- `tools/tests/test_deliver.py`: only the authorized request-assertion correction; every existing repair assertion and fixture input is preserved.
- This story: decisions, source identities, review triage, verification digests and hosted-observation limits.
- `../stories.yaml`: preserve the human-approved resolution dispatch supplied at invocation.

Four review lenses completed. Ten observations were individually triaged:
two medium entries patched, none deferred, and eight rejected with their
specific reasons recorded in Review Triage Log. Patched counts: high 0,
medium 2, low 0. `followup_review_recommended: false`: both patches have
passing targeted controls and no specific unverified patch risk remains.

Verification: all five required `run-with-temp python3 tools/tests/...`
commands passed (20 + 21 + 9 + 17 + 39 = 106 tests). The retained 26-case
matrix, two targeted controls and six new review controls passed. The matrix
audit covers every row, including shared run state, refusal persistence,
credential absence, raw/peeled identities, and accepted repair. Diff whitespace
checks passed; bootstrap, workflow/pin, every other test and all fixtures are
unchanged. The only added qualification code is outside the repository.

Residual limits: the qualification runners are machine-local under the explicit
test freeze. Hosted GitHub token acceptance and the required week of push and
scheduled observations remain pending; fixtures establish no broader token
permissions. No push or deployment was performed. The workflow's local `done`
status does not assert hosted acceptance.
