---
title: 'Document and reproduce validation from a fresh checkout'
type: chore
created: '2026-11-22'
status: done
baseline_revision: 242e868f1060681f134a13692f38c52619e959f1
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** A new CiCd maintainer lacks a tested Linux bootstrap from a clean parent checkout to reproducible rendering and offline controller verification. The scan guide describes an empty production registry and names a superseded four-language test.

**Approach:** Add a self-contained root quickstart, correct the scan guide using current registrations and the actual six-language detector case, and record the clean-checkout result and online prerequisites against 30-2 in the 2026-11-19 sprint change proposal.

## Boundaries & Constraints

**Always:** Use Linux, Python 3.12+, the workflow's pinned uv 0.13.7, adjacent script locks, and disposable workspaces beneath `run-with-temp`'s private `TMPDIR`. Initialize only Builds, acquire the selected and historical tag objects, and retain exact source identities and concise verification digests. Treat `setup/*.yml` as live scope. Keep detector signature verification mandatory and distinguish offline success from online results.

**Never:** Change runtime code, workflows, registrations, module checkouts, ownership policy, detector thresholds, credentials, locks or accepted renders. Store raw logs or executable runners under `_bmad-output/`, or claim unexecuted online checks passed.

</intent-contract>

## Code Map

- `README.md` — minimal existing project/worktree guidance; add the Linux quickstart and online entry points.
- `docs/duplicate-scan.md` — sources/scope and local prerequisites; obsolete empty registry claim and four-language test name near calibration. Preserve dated historical observations.
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md` — 30-2 acceptance row; append compact qualification evidence and prerequisite/result boundaries.
- `setup/*.yml` — seven current registrations; link the directory rather than hard-code a permanent list.
- `.github/workflows/deliver.yml:45` — uv 0.13.7 pin. `builds-version` selects v6.6.1.
- `tools/render.py:pinned_contract` — offline local tagged-object reader; `--check` compares committed output without writing.
- `tools/tests/test_nightly_runtime.py` — dependency-free controller suite using injected transport and local Git, suitable for `uv --offline` after interpreter bootstrap.
- `tools/tests/test_render.py:LEGACY_TAG` — renderer fixtures require v6.0.6; full global suites additionally consume v5.1.0. Fetch Builds tags before qualifying.
- `tools/tests/test_scan.py:ScanTests.test_all_six_languages_use_actual_pinned_detector` — actual pinned detector case for YAML, Bash, PowerShell, Python, JavaScript and TypeScript.
- `tools/scan.py:Detector` — jscpd 5.4.3/TypeScript 6.0.3 integrity locks, isolated installation, mandatory npm signature audit. `tools/check_global.py`/`tools/validate.py` define broader online validation.

## Tasks & Acceptance

**Execution:**
- [x] `README.md` — document reproducible scratch-wrapper setup, pinned uv/Python bootstrap, fresh parent checkout, Builds/tag acquisition, locked render comparison and offline controller suite; link registry and scan guide, and document online validation commands and prerequisites.
- [x] `docs/duplicate-scan.md` — replace stale registry/test claims, reflect six configured formats and give the exact focused integration command with npm/signature/PowerShell requirements.
- [x] `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md` — record the guide's clean-checkout execution, full source commit/tree/relevant blob identifiers, result/log digest, and online prerequisites plus any attempted online outcome.

**Acceptance Criteria:**
- [x] Given a Linux machine with Bash, Git and curl, when the maintainer follows the quickstart in a fresh disposable checkout, then pinned uv prepares Python 3.12, the locked render check passes, the offline controller suite passes, and tracked checkout files remain unchanged without initializing product modules.
- [x] Given the live registration tree and scanner policy, when a maintainer reads the scan guide, then scope points to `setup/`, all six formats are identified, and the named test exists and runs the actual pinned detector.
- [x] Given an offline quickstart result, when the maintainer starts online validation using the documented commands, then prerequisites explicitly include Node 24/npm, npm registry and signature access, compatible PowerShell 7, GitHub/API/archive connectivity and the read-only audit credential as applicable; failed or unexecuted checks remain unproven.
- [x] Given completed qualification, when the sprint proposal is read, then its 30-2 evidence identifies exact inputs, observed outcomes and online prerequisites without committed raw output.

## Spec Change Log

## Review Triage Log

### 2026-11-22 — Review pass

- verdicts: 10 findings — high 0, medium 1, low 5, false 4, maybe-false 0
- The verification-gap and edge-case layers returned no findings. The intent auditor's four surface distinctions are evaluated individually below.
- findings:
  - `[false]` `[reject]` Separate fresh-checkout and detector qualifications violate an integrated-validation reading — the resolved story asks for an offline suite and prerequisites for starting online checks. The proposal identifies both source commits and matching relevant objects, and claims no integrated full-validation pass.
  - `[false]` `[reject]` Synthetic detector fixtures fail a live-source reading — the request names the live registration directory and the six-language detector test. The guide links committed `setup/` scope and runs the actual named test; production scanning is explicitly unexecuted.
  - `[false]` `[reject]` Focused integration leaves complete online validation unfulfilled — the request asks to record online prerequisites. Both online entry points and their requirements are documented; the receipt explicitly leaves their execution unproven.
  - `[false]` `[reject]` Story bookkeeping exceeds the named editing surfaces — the explicitly invoked build-auto workflow requires the id-keyed story record. All product edits remain in the two requested docs and the requested sprint proposal.
  - `[medium]` `[patch]` The focused scan command followed a bootstrap that deletes its checkout/toolchain — added explicit placement inside `BOOTSTRAP` before assertions/cleanup and existing-checkout requirements for standalone use.
  - `[low]` `[patch]` Standalone uv environments could persist in the default cache — standalone commands now use inherited `UV_NO_CACHE=1`, including nested tool-suite uv invocations; the main bootstrap retains its private cache.
  - `[low]` `[patch]` Moving main lacked instructions for replaying the receipt's revision — added optional exact-commit fetch/checkout instructions before submodule initialization, linked to the archived receipt.
  - `[low]` `[patch]` PowerShell compatibility had no named working version — both guides now identify tested PowerShell 7.6.2 alongside the required native `ModuleAnalysis` API.
  - `[low]` `[patch]` Audit credential scope omitted its repository targets — README now names CiCd contents/bootstrap objects and Builds release/tag objects, matching `check_bootstrap` and `check_release` in `tools/check_global.py`.
  - `[low]` `[reject]` The quickstart does not automatically capture/hash its output — the advice asks for manual evidence retention, not automatic receipt generation. Adding another logging/exit-status shell procedure for an occasional receipt would add complexity beyond a direct correction; this run already records actual log digests in the proposal.

## Verification

- Execute the README bootstrap from a clean parent checkout under `run-with-temp`; retain only the one-line outcome, canonical input identities and SHA-256 log digest.
- Run the focused `ScanTests.test_all_six_languages_use_actual_pinned_detector` command with its real prerequisites; report failure accurately if a prerequisite refuses access.
- Check document links, live test name, pin values, and `git diff --check`; inspect that only requested documentation and this workflow record changed.

### Observed qualification — 22 November 2026

- Passed the README's executable blocks unchanged from a minimal Linux shell
  (`PATH=/usr/bin:/bin`), including its fallback scratch wrapper: uv 0.13.7,
  managed Python 3.12.16, fresh public parent clone, Builds-only initialization,
  selected/historical tag acquisition, locked render comparison, all 39 offline
  controller tests and unchanged tracked files. Log SHA-256:
  `815c019facb60cfcfcfd27e7cb53ee5bae25772fd8bc805de93a17d775e2c2a7`.
- Passed the documented real-detector case with Node 24.22.1/npm 11.19.1 and
  PowerShell 7.6.2: all six formats detected, with normal locked installation
  and mandatory signature verification. Log SHA-256:
  `a406d5ed6e466375bec6c601ef8c702b6b40f1170e13624def53cd917504b322`.
- Verified local documentation link targets, all recorded input identities,
  the actual test name, live pins and registry, and `git diff --check`.
  Only the three requested documents and this story record changed.
- Full source commit/tree/blob identities, the public-clone versus local-baseline
  distinction and online prerequisites are retained in the
  [30-2 sprint evidence](../../../planning-artifacts/sprint-change-proposal-2026-11-19.md#30-2-clean-checkout-qualification--22-november-2026).
  Full global validation, live-module validation, production scanning and hosted
  outcomes were not executed and remain unproven. Raw logs and ad hoc harnesses
  stayed under disposable scratch; no runtime, policy, locks or renders changed.

## Auto Run Result

Status: done

Implemented the Linux maintainer bootstrap and corrected current scan scope and
six-language reproduction guidance. Recorded exact qualification inputs,
clean-checkout outcomes and online prerequisites against 30-2.

Files changed:

- `README.md` — scratch-wrapper setup, pinned uv/Python, Builds/tag acquisition,
  render/offline verification, archived-commit replay and online entry points.
- `docs/duplicate-scan.md` — live registry link, six configured formats and the
  actual detector case, npm/signature/PowerShell prerequisites and scratch usage.
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md` — 30-2
  exact-source receipt, verified outcomes, log digests and online boundaries.
- This story — plan, acceptance state, review triage and terminal result.

Review: five patch entries applied (medium 1, low 4); no deferrals. Four intent
surface concerns were rejected because the resolved request requires offline
qualification plus online prerequisites, the named synthetic integration case,
and skill bookkeeping. One low finding requesting automatic log capture was
rejected because a new shell logging procedure would add unnecessary complexity;
manual evidence guidance and this run's actual digests satisfy the request.
Every individual finding and its evidence appears in the triage log above.

Follow-up review recommended: false. No high findings and only one medium patch
entry; no specific unverified risk in these documentation corrections remains.

Verification: the final README bootstrap passed from `PATH=/usr/bin:/bin`, with
uv 0.13.7/Python 3.12.16, matching render, all 39 offline controller tests,
unchanged tracked files and Builds-only initialization. Post-review log SHA-256:
`1a15c9ad52a4522172aeb54e04d0413f18e91484a54404cf6c4155696bfba2c7`.
The reviewed detector command passed all six formats with Node 24.22.1,
npm 11.19.1, PowerShell 7.6.2, normal locked installation and signature checks;
log SHA-256:
`0682981917d0309b45728f047ebb0d853d7570629b06715753af69dcfa8f89f7`.
Documentation links, shell syntax, current pins/test name, source identities and
`git diff --check` passed. All disposable jobs finished and removed their scratch.

Residual limits: full global/live-module validation, production scanning and
hosted outcomes were not run. Public-clone and detector-baseline commits are
separately identified in the sprint receipt. No push is part of this run.
